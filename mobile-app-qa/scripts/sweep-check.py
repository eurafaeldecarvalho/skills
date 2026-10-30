#!/usr/bin/env python3
"""Detectors over a matrix-sweep run. Output: findings.md, findings.json, contact-<config>.png, crops/.

Usage:
  sweep-check.py <run-dir> [--no-contact] [--assets qa/assets.tsv]   matrix sweep (+ label-offcenter, image-distortion)
  sweep-check.py --splash <splash-run> [--logo logo.png]             splash frames from splash-capture.sh
  sweep-check.py --launch-audit <project-dir> [--android-res <res>]  static splash/icon config audit
Env FIRST_SCREENS (comma list of screen names) raises label-offcenter to P1 there.
Detector output is evidence, not proof: a human still reviews the contact sheets.
Needs Pillow (pip install pillow).
"""
import csv, json, re, sys, xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
try:
    from PIL import Image, ImageChops, ImageDraw, ImageStat
except ImportError:
    sys.exit("pip install pillow")

US_MONEY = re.compile(r"(?:US\$|R\$|\$|€|USD|BRL|EUR|MXN)\s?\d{1,3}(?:,\d{3})*\.\d{2}\b|\b\d{1,3}(?:,\d{3})+\.\d{2}\b|\b\d+\.\d{2}\s?(?:€|R\$)")
COMMA_MONEY = re.compile(r"(?:R\$|\$|€)\s?\d{1,3}(?:\.\d{3})*,\d{2}\b")
RAW_KEY = re.compile(r"^[a-z][a-zA-Z0-9]*(?:\.[a-zA-Z0-9_]+)+$")
BAD_VALUE = re.compile(r"\b(?:undefined|NaN|null|\[object Object\]|Invalid Date)\b")
EN_WORDS = {"settings", "save", "cancel", "delete", "sign in", "log in", "sign out", "loading", "error",
            "retry", "done", "next", "back", "add", "edit", "share", "search", "today", "yesterday"}
COMMA_DECIMAL = {"pt-BR", "pt-PT", "es-AR", "es-CL", "es-CO", "es-UY", "es-PY", "es-ES", "fr-FR", "de-DE", "it-IT"}
BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")

def lum(rgb):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * c(r) + 0.7152 * c(g) + 0.0722 * c(b)

def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def nodes(xml_path):
    try:
        root = ET.parse(xml_path).getroot()
    except Exception:
        return []
    out = []
    for n in root.iter("node"):
        m = BOUNDS.match(n.get("bounds", ""))
        if not m:
            continue
        out.append({"text": (n.get("text") or "").strip(), "desc": (n.get("content-desc") or "").strip(),
                    "clickable": n.get("clickable") == "true", "rid": n.get("resource-id", ""),
                    "pkg": n.get("package", ""), "cls": n.get("class", ""),
                    "b": tuple(map(int, m.groups()))})
    return out

def parse_env(envf):
    env = {}
    if envf.exists():
        for line in envf.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def rect(v):
    try:
        r = tuple(int(x) for x in v.split(","))
        return r if len(r) == 4 and r[2] > r[0] and r[3] > r[1] else None
    except (ValueError, AttributeError):
        return None

def overlap(a, b):
    """Overlap in px (width, height) of two [x1,y1,x2,y2] rects."""
    return max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))

def resolve(run, p):
    """Manifest paths may be cwd-relative (as written by matrix-sweep.sh) or relative to the run dir."""
    p = Path(p)
    return p if p.is_absolute() or p.exists() else Path(run) / p


def check_image(png):
    im = Image.open(png).convert("RGB")
    small = im.resize((max(1, im.width // 8), max(1, im.height // 8)))
    st = ImageStat.Stat(small.convert("L"))
    return im, st.mean[0], st.stddev[0]

def text_contrast(im, b):
    x1, y1, x2, y2 = b
    if x2 - x1 < 4 or y2 - y1 < 4:
        return None
    crop = im.crop((x1, y1, x2, y2)).resize((min(64, x2 - x1), min(32, y2 - y1)))
    data = crop.get_flattened_data() if hasattr(crop, "get_flattened_data") else crop.getdata()
    px = sorted(data, key=lum)
    lo, hi = px[len(px) // 20], px[-len(px) // 20 - 1]
    return contrast(lo, hi)

# ---------- visual precision: label centering + image distortion ----------
BUTTON_CLASSES = ("android.widget.Button", "android.widget.ToggleButton", "android.widget.CompoundButton",
                  "android.widget.ImageButton", "android.widget.RadioButton", "android.widget.Switch")
DESCENDERS = set("gjpqyçÇQ,;")
FIRST_SCREENS = {s.strip().lower() for s in
                 (__import__("os").environ.get("FIRST_SCREENS") or "welcome,sign-in,signin,sign-up,signup,login,onboarding,home-empty").split(",") if s.strip()}

def _px(im):
    return im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()

def _median(colors):
    if not colors:
        return (0, 0, 0)
    return tuple(sorted(c[i] for c in colors)[len(colors) // 2] for i in range(3))

def _dist(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))

def _ring(im, b, d):
    """Pixels on the rectangle b grown (d>0) or shrunk (d<0) by |d| px, clipped to the image."""
    x1, y1, x2, y2 = b[0] - d, b[1] - d, b[2] + d - 1, b[3] + d - 1
    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(im.width - 1, x2), min(im.height - 1, y2)
    if x2 <= x1 or y2 <= y1:
        return []
    pts = [(x, y1) for x in range(x1, x2 + 1, 2)] + [(x, y2) for x in range(x1, x2 + 1, 2)]
    pts += [(x1, y) for y in range(y1, y2 + 1, 2)] + [(x2, y) for y in range(y1, y2 + 1, 2)]
    return [im.getpixel(p)[:3] for p in pts]

def _maxdiff(im, color):
    """L image: per-pixel max channel distance to a solid color (C speed via ImageChops)."""
    r, g, b = ImageChops.difference(im, Image.new("RGB", im.size, color)).split()
    return ImageChops.lighter(ImageChops.lighter(r, g), b)

def _mask(im, color, thr):
    return _maxdiff(im, color).point(lambda v: 255 if v > thr else 0)

def ink_box(im, b, inset, thr=48):
    """Bounding box of 'ink' inside rect b: pixels unlike the control's own background (sampled on a ring
    `inset` px inside the edge) AND unlike the surrounding screen (ring just outside: rounded corners)."""
    bg = _median(_ring(im, b, -inset)); out = _median(_ring(im, b, 3))
    x1, y1, x2, y2 = b[0] + inset, b[1] + inset, b[2] - inset, b[3] - inset
    if x2 - x1 < 4 or y2 - y1 < 4:
        return None, bg
    crop = im.crop((x1, y1, x2, y2)).convert("RGB")
    m = _mask(crop, bg, thr)
    if _dist(bg, out) > thr:
        m = ImageChops.multiply(m, _mask(crop, out, thr))
    if m.histogram()[255] < 6:
        return None, bg
    bb = m.getbbox()
    return (x1 + bb[0], y1 + bb[1], x1 + bb[2], y1 + bb[3]), bg

def label_centering(im, n, kids, dens):
    """Returns (dx_dp, dy_dp, how, start_aligned) or None. Positive dx = right, dy = down."""
    x1, y1, x2, y2 = n["b"]; dp = dens / 160
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    inset = max(2, round(3 * dp))
    ib, _ = ink_box(im, n["b"], inset)
    res = []
    if ib:
        res.append(("ink", ((ib[0] + ib[2]) / 2 - cx) / dp, ((ib[1] + ib[3]) / 2 - cy) / dp, ib))
    tk = [k for k in kids if k["text"]]
    if tk:
        bx = (min(k["b"][0] for k in tk), min(k["b"][1] for k in tk), max(k["b"][2] for k in tk), max(k["b"][3] for k in tk))
        res.append(("node", ((bx[0] + bx[2]) / 2 - cx) / dp, ((bx[1] + bx[3]) / 2 - cy) / dp, bx))
    if not res:
        return None
    how, dx, dy, box = max(res, key=lambda r: max(abs(r[1]), abs(r[2])))
    lgap, rgap = (box[0] - x1) / dp, (x2 - box[2]) / dp
    start_aligned = lgap <= 24 and rgap > 3 * max(lgap, 1) and (x2 - x1) / dp > 160
    return dx, dy, how, start_aligned

def load_assets(path):
    out = {}
    if path and Path(path).exists():
        for line in Path(path).read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                out[parts[0].strip()] = (parts[1].strip(), (parts[2].strip() if len(parts) > 2 else "P2"),
                                         Path(path).parent)
    return out

def asset_source(spec, base):
    """(aspect, RGBA image or None) from 'W:H' or an image path (opaque bbox aspect)."""
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*[:x]\s*(\d+(?:\.\d+)?)\s*$", spec)
    if m:
        return float(m.group(1)) / float(m.group(2)), None
    p = Path(spec)
    if not p.exists():
        p = base / spec
        if not p.exists():
            p = base.parent / spec
    if not p.exists():
        return None, None
    src = Image.open(p).convert("RGBA"); bb = src.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox() or (0, 0, src.width, src.height)
    src = src.crop(bb)
    return src.width / src.height, src

def _gray(im, size=(48, 48)):
    return list(_px(im.convert("L").resize(size)))

def _mad(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)

def image_distortion(im, n, spec, base, dens):
    """Returns (ratio_rendered, ratio_source, verdict) or None. verdict: stretched|ok|unknown."""
    aspect, src = asset_source(spec, base)
    if not aspect:
        return None
    b = n["b"]; bw, bh = b[2] - b[0], b[3] - b[1]
    if bw < 8 or bh < 8:
        return None
    crop = im.crop(b).convert("RGB")
    if src is not None:   # compare the render against stretch / contain / cover of the source
        bg = _median(_ring(im, b, -1))
        base_img = Image.new("RGBA", src.size, bg + (255,)); s = Image.alpha_composite(base_img, src).convert("RGB")
        cand = {"stretch": s.resize((bw, bh))}
        k = min(bw / s.width, bh / s.height); c = Image.new("RGB", (bw, bh), bg)
        r = s.resize((max(1, round(s.width * k)), max(1, round(s.height * k)))); c.paste(r, ((bw - r.width) // 2, (bh - r.height) // 2))
        cand["contain"] = c
        k = max(bw / s.width, bh / s.height); r = s.resize((max(1, round(s.width * k)), max(1, round(s.height * k))))
        ox, oy = (r.width - bw) // 2, (r.height - bh) // 2; cand["cover"] = r.crop((ox, oy, ox + bw, oy + bh))
        g = _gray(crop); scores = {k2: _mad(g, _gray(v)) for k2, v in cand.items()}
        best = min(scores, key=scores.get)
        ratio_box = bw / bh
        if abs(ratio_box / aspect - 1) <= 0.04:
            return ratio_box, aspect, "ok"
        if best == "stretch" and scores["stretch"] < 0.8 * min(scores["contain"], scores["cover"]):
            return ratio_box, aspect, "stretched"
        if best in ("contain", "cover") and scores[best] < 40:
            return ratio_box, aspect, "ok"
    ib, _ = ink_box(im, b, 1)
    if not ib:
        return None
    iw, ih = ib[2] - ib[0], ib[3] - ib[1]
    if iw >= bw - 3 and ih >= bh - 3:                       # fills the node: crop vs stretch undecidable
        return iw / ih, aspect, "unknown"
    r = iw / ih
    return r, aspect, ("stretched" if abs(r / aspect - 1) > 0.04 else "ok")

def save_crop(run, row, n, im, tag, label=""):
    d = run / "crops" / row["config"]; d.mkdir(parents=True, exist_ok=True)
    x1, y1, x2, y2 = n["b"]; pad = 12
    c = im.crop((max(0, x1 - pad), max(0, y1 - pad), min(im.width, x2 + pad), min(im.height, y2 + pad)))
    c = c.resize((c.width * 2, c.height * 2), Image.NEAREST)
    name = re.sub(r"[^\w.-]+", "_", (label or n["rid"].split("/")[-1] or n["text"] or n["desc"] or "node"))[:40]
    p = d / f"{row['screen']}-{name}-{tag}.png"; c.save(p)
    return p.relative_to(run)

# ---------- splash frames (--splash) ----------
def _frame_stats(im, dp):
    """Dominant background, its share, the logo ink bbox (ignoring status/nav bar bands) and mean luminance."""
    W, H = im.size; top, bot = int(32 * dp), int(H - 56 * dp)
    sm = im.resize((max(1, W // 8), max(1, H // 8))).convert("RGB"); sw, sh = sm.size
    t4, b4 = top // 8, bot // 8
    px = list(_px(sm))
    border = [px[y * sw + x] for y in range(t4, b4) for x in (0, 1, sw - 2, sw - 1)] + \
             [px[y * sw + x] for y in (t4, t4 + 1, b4 - 2, b4 - 1) for x in range(sw)]
    q = defaultdict(int)
    for c in border:
        q[(c[0] // 16, c[1] // 16, c[2] // 16)] += 1
    key = max(q, key=q.get); bg = _median([c for c in border if (c[0] // 16, c[1] // 16, c[2] // 16) == key])
    reg = im.convert("RGB").crop((0, top, W, bot)); rs = reg.resize((max(1, W // 2), max(1, (bot - top) // 2)))
    share = 1 - _mask(rs, bg, 24).histogram()[255] / (rs.width * rs.height)
    bb = _mask(rs, bg, 40).getbbox()
    box = (bb[0] * 2, top + bb[1] * 2, bb[2] * 2, top + bb[3] * 2) if bb else None
    mean = sum(lum(c) for c in px[:: 7]) / len(px[:: 7])
    return {"bg": bg, "share": share, "box": box, "lum": mean, "g": _gray(im, (27, 60)), "area": (W, (bot - top))}

def splash_check(run, logo, findings):
    run = Path(run); lr = None
    if logo:
        lr, _ = asset_source(str(logo), Path("."))
    cfgs = sorted(p.parent for p in run.glob("*/frames")); aspects = {}
    if not cfgs:
        sys.exit(f"no <cfg>/frames under {run} (run splash-capture.sh first)")
    def add(sev, det, cfg, msg):
        findings.append({"severity": sev, "detector": det, "config": cfg, "screen": "launch", "detail": msg})
    for d in cfgs:
        cfg = d.name; env = parse_env(d / "env.txt")
        frames = sorted((d / "frames").glob("*.png"))
        if len(frames) < 5:
            add("P1", "splash-capture", cfg, f"only {len(frames)} frames captured"); continue
        fps = float(env.get("fps", 30)); dens = int(env["density"]) if env.get("density", "").isdigit() else 420
        first = Image.open(frames[0]); W, H = first.size
        dw = int(env["size"].split("x")[0]) if re.match(r"^\d+x\d+$", env.get("size", "")) else W
        dp = (dens / 160) * (W / dw)                       # px per dp in the recorded frame
        start, theme = env.get("start", "cold"), env.get("theme", "")
        skip = int(float(env.get("pre_secs", 0.6)) * fps)  # launcher frames before am start
        st = [_frame_stats(Image.open(f).convert("RGB"), dp) for f in frames]
        fin = st[-1]
        h = len(st) - 1                                     # handoff = start of the final settled run
        while h > skip and _mad(st[h - 1]["g"], fin["g"]) < 3:
            h -= 1
        win = list(range(skip, h))
        def stable(i):
            return i > 0 and _mad(st[i]["g"], st[i - 1]["g"]) < 2.5
        diff_final = {i: _mad(st[i]["g"], fin["g"]) for i in win}
        splash = [i for i in win if stable(i) and st[i]["share"] >= 0.6 and diff_final[i] > 6 and st[i]["box"]]
        aw, ah = st[0]["area"]
        # full-bleed bitmap: ink spans ≥ 90 % of both axes for ≥ 3 stable frames that aren't the first screen
        fb = [i for i in win if stable(i) and st[i]["box"] and diff_final[i] > 6 and
              (st[i]["box"][2] - st[i]["box"][0]) >= 0.9 * aw and (st[i]["box"][3] - st[i]["box"][1]) >= 0.9 * ah and
              _mad(st[i]["g"], st[max(0, skip - 1)]["g"]) > 6]
        if len(fb) >= 3 and start != "hot":
            add("P1", "splash-fullbleed", cfg, f"{len(fb)} frames ({len(fb)*1000/fps:.0f} ms) where an image fills the whole window "
                f"before the first screen — bitmap stretched as windowBackground? (frame {frames[fb[0]].name})")
        if splash and start != "hot":
            bgs = _median([st[i]["bg"] for i in splash]); L = lum(bgs)
            if theme == "dark" and L > 0.4:
                add("P1", "splash-theme", cfg, f"dark theme but splash background is light {bgs} (lum {L:.2f}) — no night splash color?")
            if theme == "light" and L < 0.05:
                add("P2", "splash-theme", cfg, f"light theme with a near-black splash {bgs} — intended?")
            fl = lum(_median([fin["bg"]])) if fin["share"] > 0.3 else None
            if fl is not None and abs(fl - L) > 0.35:
                add("P2", "splash-handoff-color", cfg, f"splash background {bgs} ≠ first-screen background {fin['bg']}: color jump at handoff")
            boxes = [st[i]["box"] for i in splash]
            for i in splash[:1] + splash[len(splash) // 2: len(splash) // 2 + 1]:
                bx = st[i]["box"]; bw, bh = bx[2] - bx[0], bx[3] - bx[1]
                ox = ((bx[0] + bx[2]) / 2 - W / 2) / dp; oy = ((bx[1] + bx[3]) / 2 - H / 2) / dp
                if max(abs(ox), abs(oy)) > 8:
                    add("P1", "splash-offcenter", cfg, f"logo center off by {ox:+.0f},{oy:+.0f} dp (frame {frames[i].name})"); break
            bx = boxes[len(boxes) // 2]; r = (bx[2] - bx[0]) / max(1, bx[3] - bx[1]); aspects[cfg] = r
            if lr and abs(r / lr - 1) > 0.04:
                add("P1", "splash-stretch", cfg, f"logo rendered aspect {r:.3f} vs source {lr:.3f} ({(r/lr-1)*100:+.0f} %) — stretched/squashed")
            elif not lr and abs(W / H - 1) > 0.1 and abs(r / (W / H) - 1) <= 0.04:
                add("P1", "splash-stretch", cfg, f"logo aspect {r:.3f} = window aspect {W/H:.3f}: the image is scaled with the "
                    "window (bitmap windowBackground?) — pass --logo to confirm")
            for a, b2 in zip(splash, splash[1:]):
                A_, B_ = st[a]["box"], st[b2]["box"]
                mv = max(abs(A_[i] - B_[i]) for i in range(4)) / dp
                if b2 - a <= 2 and mv > 4 and min(st[a]["share"], st[b2]["share"]) > 0.8:
                    add("P1", "splash-jump", cfg, f"logo moves/resizes {mv:.0f} dp between {frames[a].name} and {frames[b2].name}"); break
        ref = [st[i]["lum"] for i in splash] or [st[max(0, skip - 1)]["lum"]]
        refL = sum(ref) / len(ref)
        last_splash = max(splash) if splash else skip
        flash = [i for i in win if st[i]["share"] > 0.9 and abs(st[i]["lum"] - refL) > 0.35 and abs(st[i]["lum"] - fin["lum"]) > 0.35]
        if flash:
            add("P1", "splash-flash", cfg, f"{len(flash)} frame(s) ({len(flash)*1000/fps:.0f} ms) of a uniform "
                f"{'white' if st[flash[0]]['lum'] > 0.5 else 'black'} screen during launch (first {frames[flash[0]].name})")
        blank = [i for i in win if i > last_splash and st[i]["share"] > 0.97 and not st[i]["box"] and i not in flash]
        if splash and len(blank) * 1000 / fps > 300:
            add("P2", "splash-blank", cfg, f"{len(blank)*1000/fps:.0f} ms of blank frames between splash and first screen")
        am = (d / "am-start.txt").read_text() if (d / "am-start.txt").exists() else ""
        m = re.search(r"TotalTime:\s*(\d+)", am)
        if m and start == "cold" and int(m.group(1)) > 2000:
            add("P2", "splash-slow", cfg, f"cold start TotalTime {m.group(1)} ms (> 2000)")
        if start != "hot" and not splash and not fb:
            add("P3", "splash-none", cfg, "no stable splash frame found (fast device, or system splash disabled) — review the strip")
        # strip: pre-launch, splash frames, transition, final
        pick = sorted(set([max(0, skip - 1)] + splash[:: max(1, len(splash) // 4 or 1)][:4] + fb[:2] + flash[:2] +
                          [max(skip, h - 2), h, len(st) - 1]))[:10]
        tw = 180; th = round(tw * H / W); strip = Image.new("RGB", (tw * len(pick), th + 20), "gray"); dr = ImageDraw.Draw(strip)
        for j, i in enumerate(pick):
            t = Image.open(frames[i]).convert("RGB").resize((tw, th)); strip.paste(t, (j * tw, 20))
            dr.text((j * tw + 3, 3), f"{frames[i].stem} {i*1000/fps:.0f}ms", fill="white")
        strip.save(run / f"strip-{cfg}.png")
    if not lr and len(aspects) >= 2:                     # same logo, different shape per profile = stretched
        lo, hi = min(aspects.values()), max(aspects.values())
        if hi / lo > 1.04:
            add("P1", "splash-stretch", "*", "logo aspect differs across configs: " +
                ", ".join(f"{k} {v:.2f}" for k, v in sorted(aspects.items())) + " — scaled with the window?")
    return cfgs

# ---------- static launch audit (--launch-audit) ----------
EXPO_PLACEHOLDER_DHASH = 0x92B0C8C4C4C8B092   # Expo template assets/splash-icon.png (grey grid + circles), on white

def _dhash(path):
    im = Image.open(path).convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(bg, im).convert("L")
    bb = flat.point(lambda v: 255 if v < 250 else 0).getbbox()   # content box: ignore padding
    g = list(_px((flat.crop(bb) if bb else flat).resize((9, 8)))); h = 0
    for r in range(8):
        for c in range(8):
            h = (h << 1) | (g[r * 9 + c] > g[r * 9 + c + 1])
    return h

def is_placeholder(path):
    """Expo template splash (grey grid + circles): dHash close to the template AND nearly colorless."""
    if bin(_dhash(path) ^ EXPO_PLACEHOLDER_DHASH).count("1") > 12:
        return False
    im = Image.open(path).convert("RGBA").resize((64, 64))
    ink = [c for c in _px(im) if c[3] > 128 and min(c[:3]) < 250]
    return bool(ink) and sum(max(c[:3]) - min(c[:3]) for c in ink) / len(ink) < 12

def launch_audit(proj, android_res=None):
    proj = Path(proj); out = []
    def add(sev, det, msg):
        out.append({"severity": sev, "detector": det, "config": "static", "screen": "launch", "detail": msg})
    cfg = {}
    if (proj / "app.json").exists():
        cfg = json.loads((proj / "app.json").read_text()).get("expo", {})
    elif any((proj / f).exists() for f in ("app.config.js", "app.config.ts")):
        add("P3", "launch-audit", "dynamic app.config.* — run `npx expo config --json > /tmp/app.json` and audit that dir")
    plugins = cfg.get("plugins", []) or []
    sp = None
    for p in plugins:
        name, opts = (p, {}) if isinstance(p, str) else (p[0], p[1] if len(p) > 1 else {})
        if name == "expo-splash-screen":
            sp = opts or {}
    pkg = json.loads((proj / "package.json").read_text()) if (proj / "package.json").exists() else {}
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    def asset(rel):
        return (proj / rel) if rel else None
    android = cfg.get("android", {})
    img = None
    if sp is None:
        add("P1", "splash-config", "expo-splash-screen is not in plugins" + ("" if "expo-splash-screen" in deps else " (not installed either)") +
            f"; legacy `splash` = {json.dumps(cfg.get('splash'))} — prebuild falls back to a default/bitmap splash")
        if isinstance(cfg.get("splash"), dict):
            img = asset(cfg["splash"].get("image"))
            if cfg["splash"].get("resizeMode") in ("cover", "stretch"):
                add("P1", "splash-config", f"splash.resizeMode {cfg['splash']['resizeMode']!r} crops/stretches the logo; use contain")
    else:
        img = asset(sp.get("image"))
        if not sp.get("image"):
            add("P1", "splash-config", "expo-splash-screen has no `image`")
        if sp.get("resizeMode", "contain") != "contain":
            add("P1", "splash-config", f"resizeMode {sp.get('resizeMode')!r}: use \"contain\" (cover crops, native ignores imageWidth)")
        if not sp.get("backgroundColor"):
            add("P2", "splash-config", "no backgroundColor (default #ffffff in both themes)")
        if cfg.get("userInterfaceStyle", "light") != "light" and not (sp.get("dark") or {}).get("backgroundColor"):
            add("P1", "splash-config", f"userInterfaceStyle {cfg.get('userInterfaceStyle')!r} but no `dark.backgroundColor` → white splash in dark mode")
        iw = sp.get("imageWidth", 100)
        if not 120 <= iw <= 288:
            add("P3", "splash-config", f"imageWidth {iw} dp (default 100): the logo may look small/large; ≈ 200 for a 192 dp circle")
    for rel, label in ((img, "splash image"),):
        if rel and rel.exists():
            im = Image.open(rel).convert("RGBA"); a = im.getchannel("A")
            if is_placeholder(rel):
                add("P1", "splash-placeholder", f"{rel.relative_to(proj)} looks like the Expo template placeholder (grid + circles)")
            opaque = sum(1 for v in _px(a.resize((64, 64))) if v > 200) / 4096
            if opaque > 0.95:
                add("P1", "splash-opaque", f"{label} {rel.relative_to(proj)} is a full-bleed opaque image ({opaque:.0%} opaque): it gets "
                    "masked/stretched; use the logo on a transparent background")
        elif rel:
            add("P1", "splash-config", f"{label} {rel} not found")
    tpl = proj / "assets" / "splash-icon.png"
    if tpl.exists() and (not img or tpl.resolve() != img.resolve()) and is_placeholder(tpl):
        add("P3", "splash-placeholder", "assets/splash-icon.png is still the Expo template placeholder (unused or leftover)")
    ai = android.get("adaptiveIcon") or {}
    fg = asset(ai.get("foregroundImage"))
    if not ai:
        add("P2", "icon-adaptive", "no android.adaptiveIcon (legacy square icon gets masked unpredictably)")
    if fg and fg.exists():
        im = Image.open(fg).convert("RGBA")
        if im.width != im.height:
            add("P1", "icon-aspect", f"adaptive foreground {im.width}x{im.height} is not square → stretched")
        a = im.getchannel("A").resize((128, 128)); r = 128 * (66 / 108) / 2; far = 0.0
        for i, v in enumerate(_px(a)):
            if v > 40:
                x, y = i % 128 + 0.5, i // 128 + 0.5
                far = max(far, ((x - 64) ** 2 + (y - 64) ** 2) ** 0.5)
        if far > r * 1.02:
            add("P1", "icon-safe-zone", f"adaptive foreground content reaches {far/64:.0%} of the half-canvas; safe zone is 61 % "
                "(66/108) → cropped by circle/squircle masks")
    if ai and not ai.get("monochromeImage"):
        add("P2", "icon-monochrome", "no adaptiveIcon.monochromeImage → no themed icon on Android 13+")
    # prebuilt native res
    roots = [Path(android_res)] if android_res else [p for p in (proj / "android").glob("**/src/main/res") if "node_modules" not in p.parts]
    for res in roots:
        drawables = {p.stem: p.suffix for p in res.glob("drawable*/*.*")}
        logos = sorted(res.glob("drawable*/splashscreen_logo.png"))
        if logos and is_placeholder(logos[-1]):
            add("P1", "splash-placeholder", f"{logos[-1].relative_to(res.parent)} is the Expo template placeholder (grid + circles), "
                "not the app's logo")
        for sx in res.glob("values*/styles.xml"):
            txt = sx.read_text(errors="ignore")
            for m in re.finditer(r'<style name="([^"]*)"[^>]*>(.*?)</style>', txt, re.S):
                for d in re.findall(r'name="android:windowBackground">@drawable/([\w.]+)<', m.group(2)):
                    if drawables.get(d) in (".png", ".webp", ".jpg"):
                        add("P1", "splash-bitmap-windowbackground", f"{sx.relative_to(res.parent)}: {m.group(1)} uses bitmap "
                            f"@drawable/{d} as android:windowBackground → stretched to the whole window at launch")
        day = res / "values" / "colors.xml"; night = res / "values-night" / "colors.xml"
        if day.exists() and "splashscreen_background" in day.read_text() and \
                (not night.exists() or "splashscreen_background" not in night.read_text()):
            add("P1", "splash-night-color", f"{night.relative_to(res.parent)} has no splashscreen_background → light splash in dark mode")
    return out

def write_findings(path_md, title, findings, intro):
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    findings.sort(key=lambda f: (order[f["severity"]], f["detector"], f["config"], f["screen"]))
    path_md.with_suffix(".json").write_text(json.dumps(findings, indent=2, ensure_ascii=False))
    with open(path_md, "w") as f:
        f.write(f"# {title}\n\n{intro}\n\n| Sev | Detector | Config | Screen | Detail |\n|---|---|---|---|---|\n")
        for x in findings:
            f.write(f"| {x['severity']} | {x['detector']} | {x['config']} | {x['screen']} | {x['detail'].replace('|', '/')} |\n")
    counts = defaultdict(int)
    for x in findings:
        counts[x["severity"]] += 1
    print(f"{path_md}: " + ", ".join(f"{k}={counts[k]}" for k in ("P0", "P1", "P2", "P3")))
    return 1 if counts["P0"] or counts["P1"] else 0

def opt(name):
    if name in sys.argv:
        i = sys.argv.index(name)
        return sys.argv[i + 1] if i + 1 < len(sys.argv) else None
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--launch-audit":
        proj = Path(sys.argv[2] if len(sys.argv) > 2 else ".")
        f = launch_audit(proj, opt("--android-res"))
        dest = Path(opt("--out") or "/tmp/launch-audit.md")
        sys.exit(write_findings(dest, f"Launch audit — {proj.resolve().name}", f,
                                "Static splash/icon checks (reference/launch-and-visual-precision.md). Verify on frames."))
    if sys.argv[1] == "--splash":
        run = Path(sys.argv[2]); f = []
        splash_check(run, opt("--logo"), f)
        sys.exit(write_findings(run / "splash-findings.md", f"Splash findings — {run.name}", f,
                                "Frame heuristics: review every strip-<cfg>.png before triage."))
    run = Path(sys.argv[1]); contact = "--no-contact" not in sys.argv
    assets = load_assets(opt("--assets") or ("qa/assets.tsv" if Path("qa/assets.tsv").exists() else None))
    rows = list(csv.DictReader(open(run / "manifest.tsv"), delimiter="\t"))
    findings = []
    def add(sev, det, row, msg):
        findings.append({"severity": sev, "detector": det, "config": row["config"], "screen": row["screen"], "detail": msg})
    banners = defaultdict(lambda: defaultdict(set))
    for row in rows:
        png = resolve(run, row["png"]); xmlp = resolve(run, row["xml"]) if row.get("xml") else png.with_suffix(".xml")
        if not png.exists() or png.stat().st_size == 0:
            add("P1", "missing-screenshot", row, "no screenshot captured"); continue
        im, mean, sd = check_image(png)
        blank = sd < 6
        if blank:
            add("P0", "blank-screen", row, f"almost uniform screen (mean luminance {mean:.0f}, sd {sd:.1f}) — black/white/blank?")
        env = parse_env(png.parent / "env.txt")
        dens = int(env["density"]) if env.get("density", "").isdigit() else 420
        navbar, statusbar, nav = rect(env.get("navbar")), rect(env.get("statusbar")), env.get("nav", "?")
        min_px = 48 * dens / 160
        ns = nodes(xmlp) if xmlp.exists() else []
        loc = row["locale"]; lang = loc.split("-")[0]
        texts = [n["text"] for n in ns if n["text"]] + [n["desc"] for n in ns if n["desc"]]
        for t in texts:
            if loc in COMMA_DECIMAL and US_MONEY.search(t):
                add("P1", "us-money", row, f"US-style amount in {loc}: {t!r}")
            if loc == "en-US" and COMMA_MONEY.search(t):
                add("P1", "comma-money", row, f"comma-decimal amount in en-US: {t!r}")
            if RAW_KEY.match(t) and " " not in t and not re.match(r"^[\w.-]+@", t) and not re.search(r"\.(com|br|pt|app|io)$", t):
                add("P1", "raw-key", row, f"looks like an untranslated key: {t!r}")
            if BAD_VALUE.search(t):
                add("P0", "bad-value", row, f"bad value rendered: {t!r}")
            if lang != "en" and t.lower() in EN_WORDS:
                add("P1", "untranslated", row, f"English word in {loc}: {t!r}")
        W, H = im.size
        for n in ns:
            x1, y1, x2, y2 = n["b"]
            if n["clickable"] and (x2 - x1) > 0 and ((x2 - x1) < min_px - 1 or (y2 - y1) < min_px - 1):
                add("P2", "small-target", row, f"touch target {(x2-x1)*160/dens:.0f}x{(y2-y1)*160/dens:.0f}dp {n['rid'] or n['text'] or n['desc']!r}")
            interactive = n["clickable"] or n["text"] or n["desc"]
            small_node = (y2 - y1) < H * 0.5 and n["pkg"] != "com.android.systemui"
            if interactive and small_node:
                for bar, name in ((navbar, "nav"), (statusbar, "status")):
                    if bar:
                        ow, oh = overlap(n["b"], bar)
                        if ow > 0 and oh >= 6 * dens / 160:
                            what = n["rid"] or n["text"] or n["desc"]
                            add("P1", f"{name}-overlap", row,
                                f"{'control' if n['clickable'] else 'text'} {what!r} overlaps the system {name} bar "
                                f"({nav} nav, {oh * 160 / dens:.0f}dp) — missing safe-area inset?")
                            break
            if n["text"] and (x2 > W + 2 or y2 > H + 2 or x1 < -2):
                add("P2", "clipped-text", row, f"text outside screen: {n['text']!r}")
            if n["text"] and y1 < H * 0.2 and len(n["text"]) > 12:
                banners[row["config"]][n["text"]].add(row["screen"])
            if not blank and n["cls"] in BUTTON_CLASSES and 0 < (y2 - y1) <= 72 * dens / 160 and (x2 - x1) >= 24 * dens / 160 \
                    and x2 <= W and y2 <= H:
                kids = [k for k in ns if k is not n and k["b"][0] >= x1 and k["b"][1] >= y1 and k["b"][2] <= x2 and k["b"][3] <= y2]
                lc = label_centering(im, n, kids, dens)
                label = n["text"] or n["desc"] or " ".join(k["text"] for k in kids if k["text"])
                if lc and not lc[3]:
                    dx, dy, how, _ = lc
                    tol_y = 2 + (1.5 if how == "ink" and DESCENDERS & set(label) else 0)
                    if abs(dx) > 2 or abs(dy) > tol_y:
                        sev = "P1" if row["screen"].lower() in FIRST_SCREENS else "P2"
                        cp = save_crop(run, row, n, im, "label", label)
                        add(sev, "label-offcenter", row, f"label {label[:30]!r} off-center by {dx:+.1f},{dy:+.1f} dp ({how}; "
                            f"{'down' if dy > 0 else 'up'}/{'right' if dx > 0 else 'left'}) — crop {cp}")
            key = next((k for k in assets if k and (n["rid"] == k or n["rid"].endswith("/" + k) or n["desc"] == k)), None)
            if key and not blank:
                spec, sev, base = assets[key]
                r = image_distortion(im, n, spec, base, dens)
                if r and r[2] == "stretched":
                    cp = save_crop(run, row, n, im, "aspect")
                    add(sev, "image-distortion", row, f"{key!r} rendered aspect {r[0]:.3f} vs source {r[1]:.3f} "
                        f"({(r[0]/r[1]-1)*100:+.0f} %) — stretched/squashed — crop {cp}")
            if n["text"] and not blank:
                c = text_contrast(im, n["b"])
                if c is not None and c < 1.15:
                    add("P1", "invisible-text", row, f"no visible ink in text bounds (~{c:.2f}:1): {n['text'][:40]!r} — same color as background? (heuristic)")
                elif c is not None and c < 3.0:
                    add("P2", "low-contrast", row, f"text contrast ~{c:.1f}:1 {n['text'][:40]!r} (heuristic)")
    screens_per_cfg = defaultdict(set)
    for r in rows:
        screens_per_cfg[r["config"]].add(r["screen"])
    for cfg, texts in banners.items():
        total = len(screens_per_cfg[cfg])
        for t, scr in texts.items():
            if total >= 4 and len(scr) >= max(3, int(total * 0.8)):
                findings.append({"severity": "P1", "detector": "stuck-banner", "config": cfg, "screen": "*",
                                 "detail": f"same top text on {len(scr)}/{total} screens: {t!r} — banner that never clears?"})
    crash = run / "logcat-crash.txt"
    if crash.exists() and crash.read_text(errors="ignore").strip():
        findings.append({"severity": "P0", "detector": "crash", "config": "*", "screen": "*", "detail": "logcat crash buffer not empty: see logcat-crash.txt"})
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    findings.sort(key=lambda f: (order[f["severity"]], f["detector"], f["config"], f["screen"]))
    (run / "findings.json").write_text(json.dumps(findings, indent=2, ensure_ascii=False))
    with open(run / "findings.md", "w") as f:
        f.write(f"# Sweep findings — {run.name}\n\n{len(rows)} screenshots, {len(findings)} flags. "
                "Detector output is evidence, not proof: triage each, then review contact sheets.\n\n")
        f.write("| Sev | Detector | Config | Screen | Detail |\n|---|---|---|---|---|\n")
        for x in findings:
            f.write(f"| {x['severity']} | {x['detector']} | {x['config']} | {x['screen']} | {x['detail'].replace('|', '/')} |\n")
    if contact:
        by_cfg = defaultdict(list)
        for r in rows:
            if resolve(run, r["png"]).exists():
                by_cfg[r["config"]].append(r)
        for cfg, rs in by_cfg.items():
            tw, th, cols = 270, 585, 6
            sheet = Image.new("RGB", (tw * min(cols, len(rs)), (th + 22) * ((len(rs) + cols - 1) // cols)), "gray")
            d = ImageDraw.Draw(sheet)
            for i, r in enumerate(rs):
                im = Image.open(resolve(run, r["png"])).convert("RGB"); im.thumbnail((tw, th))
                x, y = (i % cols) * tw, (i // cols) * (th + 22)
                sheet.paste(im, (x, y + 22)); d.text((x + 4, y + 4), r["screen"], fill="white")
            sheet.save(run / f"contact-{cfg}.png")
    counts = defaultdict(int)
    for x in findings:
        counts[x["severity"]] += 1
    print(f"{run}/findings.md: " + ", ".join(f"{k}={counts[k]}" for k in ("P0", "P1", "P2", "P3")))
    sys.exit(1 if counts["P0"] or counts["P1"] else 0)

if __name__ == "__main__":
    main()
