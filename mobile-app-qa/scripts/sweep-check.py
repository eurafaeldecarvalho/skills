#!/usr/bin/env python3
"""Detectors over a matrix-sweep run. Output: findings.md, findings.json, contact-<config>.png.

Usage: sweep-check.py <run-dir> [--no-contact]
Detector output is evidence, not proof: a human still reviews the contact sheets.
Needs Pillow (pip install pillow).
"""
import csv, json, re, sys, xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
try:
    from PIL import Image, ImageDraw, ImageStat
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
                    "b": tuple(map(int, m.groups()))})
    return out

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

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    run = Path(sys.argv[1]); contact = "--no-contact" not in sys.argv
    rows = list(csv.DictReader(open(run / "manifest.tsv"), delimiter="\t"))
    findings = []
    def add(sev, det, row, msg):
        findings.append({"severity": sev, "detector": det, "config": row["config"], "screen": row["screen"], "detail": msg})
    banners = defaultdict(lambda: defaultdict(set))
    for row in rows:
        png = Path(row["png"]); xmlp = Path(row["xml"]) if row.get("xml") else png.with_suffix(".xml")
        if not png.exists() or png.stat().st_size == 0:
            add("P1", "missing-screenshot", row, "no screenshot captured"); continue
        im, mean, sd = check_image(png)
        blank = sd < 6
        if blank:
            add("P0", "blank-screen", row, f"almost uniform screen (mean luminance {mean:.0f}, sd {sd:.1f}) — black/white/blank?")
        envf = png.parent / "env.txt"
        dens = 420
        if envf.exists():
            m = re.search(r"density=(\d+)", envf.read_text())
            dens = int(m.group(1)) if m else dens
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
            if n["text"] and (x2 > W + 2 or y2 > H + 2 or x1 < -2):
                add("P2", "clipped-text", row, f"text outside screen: {n['text']!r}")
            if n["text"] and y1 < H * 0.2 and len(n["text"]) > 12:
                banners[row["config"]][n["text"]].add(row["screen"])
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
            if Path(r["png"]).exists():
                by_cfg[r["config"]].append(r)
        for cfg, rs in by_cfg.items():
            tw, th, cols = 270, 585, 6
            sheet = Image.new("RGB", (tw * min(cols, len(rs)), (th + 22) * ((len(rs) + cols - 1) // cols)), "gray")
            d = ImageDraw.Draw(sheet)
            for i, r in enumerate(rs):
                im = Image.open(r["png"]).convert("RGB"); im.thumbnail((tw, th))
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
