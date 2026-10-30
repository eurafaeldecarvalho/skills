# Appearance & theming (dimension 4)

Goal: every screen is correct and comfortable in **light and dark**, with the system setting and with any
in-app override, on the release build, including native surfaces React doesn't draw.

## How dark mode reaches an Expo app on Android
- `app.json` `userInterfaceStyle` (`automatic`/`light`/`dark`), also `android.userInterfaceStyle`.
  **On Android it only takes effect with the `expo-system-ui` config plugin installed**; otherwise the
  CLI warns "Install expo-system-ui in your project to enable this feature" and the field is ignored.
  Changing it needs a new native build.
- `useColorScheme()` / `Appearance` gives the system scheme; an in-app "System / Light / Dark" setting
  must combine both (`appearance === 'system' ? systemScheme : appearance`) and also drive
  `Appearance.setColorScheme()` (RN ≥0.72) if native components (Alert, DatePicker, keyboard) should follow.
- Native surfaces to check: splash screen (`expo-splash-screen` `dark` config), root background
  (`expo-system-ui` `setBackgroundColorAsync` / `backgroundColor`), status bar style (`expo-status-bar`
  `style="auto"` or explicit per theme), nav bar buttons, `Modal` (own window), `Alert`, date/time
  pickers, keyboard, WebView content, images/SVG/Lottie, map tiles, PDF export (should stay light/paper).
- OEM layers: Android 10+ developer option "Override force-dark" and some OEM "dark mode for all apps"
  features can invert apps that don't declare dark support → double inversion or muddy colors. Test once
  on a real Motorola/Samsung/Xiaomi with those toggles on and off.

## Design rules for a dark theme that doesn't look "all black and weird"
- Not pure `#000` for every layer: use a dark ground (e.g. Material baseline `#121212`-ish or brand-tinted)
  and **visible elevation steps** for surfaces/cards/sheets (tonal lightening per level). Pure black
  ground + `#111` cards = no separation on most screens, and OLED black smear when scrolling.
- Text: high-emphasis ~87% white, medium ~60%; contrast ≥ 4.5:1 (body) / 3:1 (large text, icons, borders,
  focus rings) — check every semantic color (error, success, warning, links, chips) in **both** themes.
- Brand/accent colors usually need a lighter, desaturated dark variant.
- Shadows don't read in dark; use borders/tonal elevation.
- Illustrations/logos with transparent backgrounds and dark strokes disappear — supply dark variants.
- Disabled vs enabled must stay distinguishable.

## Code audit (static)
```bash
# raw colors outside the theme module
rg -n --glob '!**/theme/**' -e '#[0-9a-fA-F]{3,8}\b' -e "'(white|black)'" -e '"(white|black)"' -e 'rgba?\(' src App.tsx
# components that never read the theme (heuristic): files with StyleSheet colors but no useTheme
rg -l 'color:|backgroundColor:' src | xargs rg -L 'useTheme|theme\.' 
# placeholder/selection/underline colors on TextInput, RefreshControl tintColor, ActivityIndicator color
rg -n 'TextInput|RefreshControl|ActivityIndicator|Switch' src
```
Each hit is a candidate; confirm on a screenshot.

## Runtime checks (sweep + manual)
- Sweep every screen in light and dark (system scheme), plus once with the in-app override opposite to
  the system (dark app on light system and vice versa).
- Live switch: toggle `cmd uimode night yes/no` while on a screen → it re-renders correctly, no stale
  colors (memoized styles created outside components are a classic cause).
- Process death in dark → reopen → no light flash, correct theme.
- Detector `blank-screen` flags screenshots with almost no luminance variance (all black/white) and
  `low-contrast` estimates text contrast from the UI dump bounds (heuristic). A human still reviews
  every dark screenshot.

## Scoring
0 dark mode unusable · 1 several screens broken · 2 readable but un-designed (pure black, low contrast,
native surfaces wrong) · 3 good, minor misses · 4 both themes first-class, verified on a real phone.
