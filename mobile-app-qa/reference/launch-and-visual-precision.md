# Launch/splash pass and visual precision (dimension 4 + 6)

Two tester complaints that no other check here catches: **"the launch logo is distorted/stretched"** and
**"the button text isn't centered in the button"**. Both are first-impression bugs: the splash is the first
thing every user sees, and an off-center label on the welcome screen's "Criar uma conta" makes the whole app
look unfinished. Detectors flag; a human still looks at the frames and crops at 100–200 % zoom.

Severity: **splash/logo/app-icon defects = P1** (first impression; gate item). Other visual-precision
defects (label off-center, squashed image, misaligned grid, wrong icon size) = **P2** (visual polish), P1
if they touch a primary action on the first screens (welcome, sign-in, sign-up, empty home).

---

## A. Launch/splash pass (mandatory in every iteration and in the FINAL PASS)

### What Android actually shows at launch
1. **Android 12+ system splash** (cold and warm start only, never on a hot start): a window with a
   **single opaque background color** and the **icon centered**. Icon rules (adaptive-icon spec):
   app icon *with* an icon background = 240×240 dp, content within a **160 dp circle**; *without* icon
   background = 288×288 dp, content within a **192 dp circle**; everything outside the circle is masked
   (one third of the foreground is cut). Branding image 200×80 dp (discouraged). Light and night variants.
   If `windowSplashScreenBackground` is unset, the theme's `windowBackground` is used **only if it is a
   plain color**.
2. **The activity's window background** until the first React frame is drawn (and behind every screen,
   keyboard resize and transition afterwards). A bitmap PNG set as `android:windowBackground` is
   **stretched to fill the whole window** → a square logo becomes an oval on a 20:9 phone and changes
   shape again on a tablet. This is the classic "distorted splash".
3. **The JS side**: `expo-splash-screen` keeps the native splash until `SplashScreen.hide()`; then the first
   screen. Anything between (a white/black flash, a logo that jumps size/position, a blank frame, a spinner
   on a different color) is a transition defect.
4. Android ≤ 11 (if minSdk allows): no system splash; only the starting window = theme `windowBackground`.

### Expo / config audit (static, before any emulator)
```bash
python3 mobile-app-qa/scripts/sweep-check.py --launch-audit . --out qa/launch-audit.md   # app.json + assets (+ android/ if prebuilt)
#   EAS/CI build tree instead of android/:  --android-res <build>/android/app/src/main/res
npx expo config --type introspect | grep -iE -A3 'splash|adaptiveIcon|userInterfaceStyle'
```
Checks (the audit automates the ones marked ⚙):
- ⚙ `expo-splash-screen` **installed and in `plugins`** with `image`, `imageWidth` (≈ 200, the logo's
  display width in dp), `resizeMode: "contain"`, `backgroundColor`, and a **`dark: {image, backgroundColor}`**
  block. Without it, prebuild may still emit `Theme.App.SplashScreen` with a **bitmap
  `windowBackground`** (stretched) and a white background in dark mode.
- ⚙ Splash image is a **logo on a transparent background** with padding, not a full-bleed opaque square
  and **not the Expo template placeholder** (`splash-icon.png` grid with circles); its opaque content fits
  the 160/192 dp circle at `imageWidth`.
- ⚙ Adaptive icon: `foregroundImage` content inside the **safe zone** (inner 66/108 ≈ 61 % circle of the
  1024 px canvas), `backgroundColor`/`backgroundImage` set, **`monochromeImage`** present (Android 13
  themed icons), all 1024×1024 (432 dp at 4×) with no stretched aspect.
- ⚙ Prebuilt `android/` (or the EAS build dir): no `<item name="android:windowBackground">@drawable/…png`
  in any splash theme; `values-night/colors.xml` defines the dark splash background; `MainActivity`
  calls the splash install path the plugin expects.
Audit detectors: `splash-config` (plugin missing, no image, `resizeMode` ≠ contain, no `dark.backgroundColor`
with `userInterfaceStyle` automatic/dark, odd `imageWidth`), `splash-placeholder` (Expo template image as
the splash or as the generated `splashscreen_logo` — perceptual hash + no color), `splash-opaque`,
`splash-bitmap-windowbackground`, `splash-night-color`, `icon-aspect`, `icon-safe-zone`, `icon-monochrome`,
`icon-adaptive`. All P1 except monochrome/adaptive/odd width (P2/P3).
- Splash background color = the first screen's background in **each theme** (no color jump at handoff).
- `SplashScreen.preventAutoHideAsync()` at module scope; `hide()` only after fonts, theme, locale and the
  first screen's data are ready (no flash of default font, wrong theme or English).

### Runtime capture (screenrecord frames)
Run inside your emulator slot (`box-reserve.sh`), on the **release** APK, after `adb install`:
```bash
APP_ID=app.example OUT=qa/splash/$(date +%F-%H%M) BOX_PROJECT=<proj> \
PROFILES="small:720x1280:320 phone:1080x2400:420 tablet:1600x2560:320" THEMES="light dark" STARTS="cold warm hot" \
  mobile-app-qa/scripts/splash-capture.sh
python3 mobile-app-qa/scripts/sweep-check.py --splash qa/splash/<run> --logo assets/splash-icon-logo.png
```
For each profile × theme × start kind the script: sets size/density/theme, makes the start **cold**
(`am force-stop`), **warm** (process alive, activity finished with BACK) or **hot** (HOME), starts
`screenrecord`, launches with `am start -W` (records `TotalTime`/`WaitTime`), stops recording ~4 s later,
extracts **every frame at 30 fps** with `ffmpeg`, and keeps the last frame as `first-screen.png`.

Profiles cover several densities and aspect ratios: small (720×1280 @ 320, 16:9), mid-range
**1080×2400 @ 420 (20:9, Moto G73 class)**, tablet (1600×2560 @ 320, 16:10); add a foldable/landscape
profile if the app supports it. Also the real phone the tester used (cold + warm, light + dark),
recorded with `adb shell screenrecord`.

### Splash-frame detectors (`sweep-check.py --splash`)
| Detector | Sev | Flags |
|---|---|---|
| `splash-stretch` | P1 | logo's rendered ink box aspect ≠ source logo's opaque-box aspect by > 4 % (`--logo`); without `--logo`: logo aspect ≈ window aspect (scaled with the window) or differs > 4 % across configs |
| `splash-fullbleed` | P1 | logo/background ink fills ≥ 90 % of the window in both axes → bitmap stretched as window background |
| `splash-offcenter` | P1 | logo ink center > 8 dp from the window center |
| `splash-theme` | P1 | dark-theme run whose splash background is light (or light run with a dark one) |
| `splash-flash` | P1 | a frame whose mean luminance jumps away from both the splash and the first screen (white/black flash) |
| `splash-jump` | P1 | the logo moves or resizes > 4 dp between consecutive splash frames before the first screen |
| `splash-handoff-color` | P2 | splash background ≠ first-screen background (color jump at handoff) |
| `splash-none` | P3 | no stable splash frame found on a cold/warm start (fast device or no splash) — check the strip |
| `splash-blank` | P2 | > 300 ms of a uniform blank frame after the splash and before the first screen |
| `splash-slow` | P2 | `TotalTime` > 2000 ms on a cold start (release, mid-range profile) |

How it reads frames: launcher frames before `am start` are skipped (`pre_secs` in `env.txt`); the first
screen is the final settled run of frames; splash frames are stable frames with a dominant uniform background
and a logo that differ from the first screen; the status/nav bar bands are ignored; dp come from `density`
and `size` in `env.txt`. Tested on synthetic frames (stretched placeholder, squashed logo, black flash,
20 dp jump, good dark splash = clean); calibrate thresholds on your first real run.

Human review: open the frame strip (`strip-<cfg>.png`) for every config; check the logo shape, crisp edges
(no upscaled blur), the handoff frame, and that the app icon on the launcher (normal, themed/monochrome on
Android 13+, round/squircle masks) looks right in light and dark.

---

## B. Visual precision checks (every screen, both themes, every locale, in the matrix sweep)

### What to check
- **Label centering** in buttons, chips, pills, tabs, badges, segmented controls, FABs: the label's ink
  is centered **horizontally and vertically** within the control (≤ 2 dp off), with and without an icon
  (icon + text centered as a group), in every locale (longer pt/es labels wrap centered), at font 1.3/2.0.
- **Android font padding:** `Text` on Android adds font padding above/below by default
  (`includeFontPadding: true`), and custom fonts (Geist, Inter…) have asymmetric ascent/descent → the label
  sits visibly high or low even though the layout is "centered". Fix: `includeFontPadding: false` +
  explicit `lineHeight` (≈ 1.2–1.25 × fontSize) + `textAlignVertical: "center"` on button/chip labels, or
  a font with balanced metrics; verify on the device, not in the code.
- **Common centering bugs:** `flexWrap: "wrap"` on the button row (a long label drops to a new line
  left-aligned), `textAlign` missing on multi-line labels, `lineHeight` from a different role than the
  `fontSize` override, fixed `height` smaller than lineHeight + padding, asymmetric `paddingTop/Bottom`,
  a hidden icon slot that still takes `gap` space.
- **Image aspect ratio preserved:** every logo, avatar, photo, illustration renders with its source
  aspect (no stretch/squash): RN `Image` with both `width` and `height` fixed and `resizeMode` default
  (`cover` crops; `stretch` distorts); explicit `aspectRatio` from the asset; avatars square; receipts
  `contain`. Static grep: `rg -n "resizeMode=\"stretch\"|resizeMode: 'stretch'|<Image" src`.
- **Alignment and spacing grid:** consistent 4/8 dp grid for paddings, margins, gaps; left edges of text
  blocks line up; list rows share the same baseline; card insets equal on both sides; nothing 1–3 px off
  between sibling elements (classic pixel misalignment).
- **Icon sizes:** one scale (e.g. 16/20/24 dp), consistent per context; icons optically centered in their
  hit area; same stroke weight across icon sets.
- **Pixel-level:** crop each primary control at 200 % and compare left/right and top/bottom padding of the
  ink; borders 1 dp on all sides (no half-pixel blur); rounded corners not clipped.

### Detectors (`sweep-check.py`, run on every matrix sweep)
| Detector | Sev | How |
|---|---|---|
| `label-offcenter` | P2 (P1 on welcome/sign-in/sign-up screens: `FIRST_SCREENS`) | for every button-like node (`android.widget.Button`, `ToggleButton`, `CompoundButton`, `ImageButton`, ≤ 72 dp tall): (1) **node**: text child bounds center vs button center, (2) **ink**: non-background pixels inside the button vs its center; flags > 2 dp horizontally or vertically (descender allowance for g/j/p/q/y/ç) |
| `image-distortion` | severity column of `qa/assets.tsv` (P2 default, P1 for the logo) | for nodes listed in `qa/assets.tsv` (`key<TAB>asset path or W:H[<TAB>P1]`; key = testID (= resource-id in RN) or content-desc; paths relative to the tsv): with an image path, the render is compared with the source **stretched / contained / covered** into the node and flagged when "stretched" wins and the aspects differ > 4 %; with only `W:H`, the rendered ink box aspect vs W:H (skipped when the image fills the node: crop vs stretch undecidable) |

`label-offcenter` ignores start-aligned rows (text ≤ 24 dp from the left and > 3× more space on the right in
a control wider than 160 dp: list rows with a button role). The ink check samples the control's own
background on a ring 3 dp inside its edge and ignores pixels of the surrounding screen color (rounded corners).
Example `qa/assets.tsv`:
```
# key	source (path relative to this file, or W:H)	severity
welcome-logo	../assets/logo.png	P1
pet-photo	4:3
avatar	1:1
```

Both are heuristics (gradients, ripples, shadows and icons with asymmetric visual weight can mislead):
every flag is triaged on the crop that the detector saves in `crops/`.
The RN `Pressable` with `accessibilityRole="button"` is exported as `android.widget.Button`, so give every
custom button/chip a role; a control without a role is invisible to the detector **and** to TalkBack.

### Manual crop review
`sweep-check.py` saves `crops/<cfg>/<screen>-<node>.png` for every flagged node; also crop the primary
buttons of the welcome, sign-in, sign-up and home screens in every config even when nothing is flagged and
look at them at 200 %.

## Scoring impact
A distorted/stretched splash or logo, a splash in the wrong theme, or a launch flash keeps **Appearance &
theming below 4** (gate blocker). Repeated off-center labels or squashed images keep it at ≤ 3.
