# Devices & layout (dimension 6)

## Device matrix (Android first; pick by your users, not your desk)
| Class | Example | Why |
|---|---|---|
| Low/mid Motorola (near-stock + Moto skin) | Moto G series (G73/G54/G35…) — huge in Brazil/LatAm | slower CPU, 6.5" FHD+, Moto dark/"Display" settings, gesture nav default |
| Samsung mid (One UI) | Galaxy A1x/A3x/A5x | most common Android in BR; Samsung keyboard (decimal-pad quirks), font size + style settings, One UI dark mode |
| Xiaomi/Redmi/POCO (HyperOS/MIUI) | Redmi Note | aggressive battery killing (background sync/notifications), forced dark for apps, autostart permission |
| Small screen / low density | 720×1280 @ 320dpi emulator (or `wm size`) | overflow, cramped forms, keyboard covering inputs |
| Large phone + max font | Pixel/any at font 2.0 + display size largest | text overflow, broken rows |
| Foldable/tablet (if supported) | Pixel Fold / tablet emulator | resizing, two-pane, rotation |
| Oldest supported Android | minSdk device/emulator | API gaps, Hermes Intl differences, permission models |
| Newest Android | latest stable API | edge-to-edge enforced (Android 15+), predictive back, new permission rules |
Free reach: Play pre-launch report runs on several real devices; Firebase Test Lab Spark quota
(see [release-and-store.md](release-and-store.md)). Real hardware is still required for the gate.

## Edge-to-edge and insets (SDK 54+/Android 15+ = always edge-to-edge)
- Use `react-native-safe-area-context` (`SafeAreaView edges` / `useSafeAreaInsets`) on every screen root,
  headers, bottom bars, FABs, sheets, toasts/banners, modals.
- **Every screen in 3-button nav AND gesture nav is a P1 gate item** (`adb shell cmd overlay enable
  com.android.internal.systemui.navbar.threebutton` / `...gestural`, or `scripts/adb-env.sh nav
  threebutton|gestural`; the sweep's `NAVS` does both). Nothing interactive or meaningful may sit under
  the navigation bar or the gesture handle: bottom tab bar, bottom buttons/footers, FABs, snackbars,
  bottom sheets, modals, the keyboard's accessory/submit row. Also display cutouts and status bar icon
  contrast in both themes.
- Detector: `scripts/adb-env.sh bars` prints the system bar frames (`dumpsys window` → `navigationBars`,
  `statusBars`); the sweep stores them in `env.txt` and `sweep-check.py` flags **`nav-overlap` /
  `status-overlap` (P1)** when a clickable or text node's bounds intersect a bar by ≥ 6 dp. It cannot see
  overlaps drawn inside one big view (e.g. a canvas) — the contact sheet review still applies.
- Android 15+ (targetSdk 35+) forces edge-to-edge and Android 16 removes the opt-out; Expo SDK 54+ is
  always edge-to-edge. Bars over app content are therefore the default, not an edge case.
- Common RN causes: fixed `paddingBottom` on tab bars, `position: 'absolute', bottom: 0` without
  `insets.bottom`, `SafeAreaView` from `react-native` (iOS-only) instead of
  `react-native-safe-area-context`, modals/sheets rendered outside the `SafeAreaProvider` tree.
- Banners/toasts at the top must sit below the status bar and not cover the header actions.

## Keyboard
- Every input reachable and visible above the keyboard on the small screen (use
  `react-native-keyboard-controller` `KeyboardAwareScrollView`/`KeyboardAvoidingView` correctly; Android
  `softwareKeyboardLayoutMode`).
- `returnKeyType`/`onSubmitEditing` moves focus; the last one submits; tap outside dismisses.
- Correct `keyboardType`, `autoComplete`, `textContentType`, `autoCapitalize` (emails never capitalized).

## Font scale and display size
- `settings put system font_scale 1.3` and `2.0`; display size via `wm density` (bigger = fewer dp).
  Don't disable font scaling globally (`allowFontScaling={false}` is an accessibility failure); cap only
  where layout truly can't grow (`maxFontSizeMultiplier` ~1.5 on tab labels) and make rows wrap.

## Orientation, back, multi-window
- Locked orientation declared on purpose; if rotation is allowed, state survives it.
- Android back (button and predictive gesture) does the expected thing on every screen, closes sheets/modals
  first, never exits a half-filled form silently.

## Visual precision
Label centering in buttons/chips/pills (Android font padding), image aspect ratio, spacing grid, icon sizes
and pixel-level alignment, with the `label-offcenter` and `image-distortion` detectors →
[launch-and-visual-precision.md](launch-and-visual-precision.md) §B. The splash is checked on small,
1080×2400 and tablet profiles (aspect ratio changes expose stretched bitmaps).

## Anti-patterns
Fixed heights for text containers · absolute positioning near screen edges without insets · testing only
on a Pixel emulator at font 1.0 · `allowFontScaling={false}` everywhere.
