# Case study: EvenKeel (Expo SDK 54, Supabase) — tester on a Moto G73 5G

A friend installed a test build and in minutes found three bugs no one saw on the developer's setup.
They are the reason this skill exists. File:line refs are from the code read on 2026-10-30; the causes
are **hypotheses to verify in the same config**, not conclusions.

## 1. "Dark mode: the whole screen is black and weird" (P0)
Evidence: `src/theme/theme.ts` dark ground `#000000`, surface `#111111`, text `#ffffff` (≈ no visible
elevation between ground and cards); `app.json:9` `"userInterfaceStyle": "automatic"` but
`expo-system-ui` not in `package.json` (on Android the field is then ignored — verify with
`npx expo config` / the build warning). Native surfaces (splash, root background, Modal, Alert, pickers)
and Motorola's own dark handling may not match the JS theme.
Hypotheses: (a) palette with no tonal elevation → "all black"; (b) system/native parts in the other
scheme or forced dark by the OEM → "weird"; (c) hardcoded colors on some components.
Tests to add: sweep every screen in dark (system and in-app override) on the release APK; live toggle
`cmd uimode night yes`; theme token contrast unit test; real Moto in dark.

## 2. "Chose Brazilian Portuguese; money shows US format with a dot for cents" (P1)
Evidence: `src/domain/present.ts:213-219` `money()`/`localeOf()` format with `uiLocale()`
(`src/i18n/index.ts:44-46` maps pt* → `pt-BR`, es* → `es-419`); `src/screens/details.tsx:545` formats a
price with hardcoded `"USD"`; the amount field (`details.tsx:270`) uses `keyboardType="decimal-pad"` and
shows the raw text the user typed; `src/domain/money.ts` `parseMoneyToCents` accepts `,` or `.`.
Hypotheses: (a) **input**: React Native's Android `decimal-pad` uses a digits key listener that only
accepts `.` on many keyboards → a Brazilian is forced to type `10.50`, and the field shows it raw;
(b) a code path formats with a locale other than the chosen language (device locale/`Intl` default) or
before i18n resolved; (c) Hermes `Intl` output on the device differs from Node; (d) es-419 format = dot
decimals for Spanish-speaking countries that use commas.
Tests to add: parse/format table + round-trip property tests; Maestro `money-input-ptbr` flow typing
`1234,56` with the device in pt-BR and asserting `R$ 1.234,56` (NBSP) everywhere it appears; keyboard
check on Gboard/Samsung/Moto; language-switch test; on-device Intl diff (locale-conventions.md).

## 3. "An alert at the top never goes away" (P1)
Evidence: `src/nav/Root.tsx:162-166` shows `offline.banner` when `!app.online`, else `offline.sending`
when `pendingIds.length > 0`; neither has `onDismiss` (only `app.banner` does, line 167).
`src/state/AppState.tsx:206-208` any network-classified flush error sets `online=false`; the 20 s timer
(`:259-261`) flushes **only if already online**, so recovery depends solely on an expo-network state
*change* event (`:245-256`). If the network never "changes" (it was fine all along, e.g. a timeout or a
backend hiccup was classified as network) the app stays "offline" forever; a write that keeps failing
keeps "sending" forever.
Fix direction: probe/retry with backoff while offline-latched, re-check on foreground, distinguish
server/timeout errors from offline, add a retry/dismiss action and a "failed to send" state.
Tests: unit tests for the latch with a fake clock; Maestro airplane-mode on/off flow asserting the
banner disappears ≤ retry interval; sweep `stuck-banner` detector.

## 4. "The translations aren't good"
Catalogs were written without locale research; pt-PT users get the pt-BR catalog
(`src/i18n/index.ts:21-24`). → [translation-quality.md](translation-quality.md) and
[locale-conventions.md](locale-conventions.md).

## 5. "The Android navigation bar covers the app's buttons" (second tester report)
Symptom: the system navigation bar (3-button bar or gesture handle) sits on top of the bottom tab bar /
bottom buttons, so taps hit Home/Back instead of the app.
Evidence (code reading, to confirm on device): Expo SDK 58 → the app is edge-to-edge on every Android
version (and Android 15+/16 force it anyway), so it draws under the system bars and must pad itself. `src/nav/Root.tsx:273-275` — the
`TabBar` uses a fixed `paddingBottom: 10` (`const bottom = 10`) instead of `useSafeAreaInsets().bottom`;
`src/ui/kit.tsx` `Screen` pads the top and the scrolling/footer variants, but the non-scroll body
(`scroll=false`, no footer) gets no bottom inset.
Fix direction: tab bar `paddingBottom: Math.max(insets.bottom, 10)` (height grows with it); audit every
absolutely positioned bottom element, FAB, sheet, toast and modal for `insets.bottom`; keyboard-avoiding
views add the inset only when the keyboard is closed.
Tests: matrix sweep with `NAVS="gestural threebutton"` → `nav-overlap` detector (interactive node bounds vs.
the `navigationBars` frame from `dumpsys window`); Maestro tap on each tab by `testID` in 3-button mode
(fails if Home is hit instead); visual check of the contact sheet; real Moto in both nav modes.

## 6. "The launch logo is distorted/stretched" (P1, third tester report)
Symptom: the logo shown while the app opens looks squashed/stretched (and is not the EvenKeel logo).
Evidence (static, `sweep-check.py --launch-audit` on the vc8 build tree; to confirm with
`splash-capture.sh` frames in the tester's config): `app.json` has `"splash": null` and **no
`expo-splash-screen`** in `plugins` or `package.json`; `assets/splash-icon.png` is still the **Expo template
placeholder** (grey grid + concentric circles). The prebuilt `res/values/styles.xml` gives
`Theme.App.SplashScreen` (the `MainActivity` launch theme) `android:windowBackground =
@drawable/splashscreen_logo` — a **square bitmap** (the placeholder composited on white, 288–1152 px per
density). Android stretches a bitmap window background to the whole window, so on the Moto G73
(1080×2400, 20:9) the circles become tall ovals until React draws; on a tablet it is a different oval.
`values-night/colors.xml` has no `splashscreen_background` → the splash is **white in dark mode** too.
`MainActivity` calls `setTheme(R.style.AppTheme)` "for expo-splash-screen", which isn't installed.
Hypotheses to verify (frames, same config): H1 stretched bitmap window background (expected: logo ink
aspect ≈ window aspect, `splash-stretch`); H2 placeholder instead of the real logo; H3 white splash →
dark first screen (`splash-theme`, `splash-handoff-color`).
Fix direction: `npx expo install expo-splash-screen`; plugin with the real logo on a **transparent**
background (`image`, `imageWidth: 200`, `resizeMode: "contain"`, `backgroundColor` = light ground,
`dark: {image, backgroundColor}` = dark ground); `preventAutoHideAsync()` at module scope and `hide()`
after fonts/theme/locale are ready; `npx expo prebuild --clean` and check that no splash theme has a bitmap
`windowBackground`; delete the placeholder asset; check the adaptive icon (safe zone, monochrome).
Tests: `--launch-audit` clean; `splash-capture.sh` cold + warm + hot × light + dark × small/1080×2400/tablet
→ `--splash --logo` clean (`splash-stretch`, `-fullbleed`, `-offcenter`, `-theme`, `-flash`, `-jump`);
strips reviewed; the tester's phone recorded with `screenrecord` in dark and light.

## 7. "The text isn't centered in the 'Criar uma conta' and 'Entrar' buttons" (P2 → P1 on the welcome screen)
Symptom: on the welcome screen the labels of the two primary buttons sit visibly off-center in the box.
Evidence (code reading, to measure on device): `src/ui/kit.tsx` `Button` — `Pressable` style
`{minHeight: 48, paddingHorizontal: 16, alignItems: "center", justifyContent: "center",
flexDirection: "row", flexWrap: "wrap", gap: 8}`; label `<T role="section" style={{fontSize: 16,
flexShrink: 1, textAlign: "center"}}>` in **Geist-Medium** with the role's `lineHeight` (role size × 1.4,
not the 16 override); **no `includeFontPadding: false`** anywhere in `src`, no `textAlignVertical` on the
label. Welcome: `src/screens/gates.tsx:32-33` (`welcome.create` "Criar uma conta", `welcome.signIn` "Entrar").
Hypotheses: H1 Android font padding + Geist's asymmetric ascent/descent → label ink sits high/low (vertical
offset of 1–3 dp, invisible in layout bounds); H2 `lineHeight` from the role ≠ the 16 px font → extra
leading on one side; H3 `flexWrap: "wrap"` + `gap` with a hidden icon slot → label pushed sideways or
wrapped left-aligned in long locales/font 1.3.
Fix direction: label style `includeFontPadding: false`, `textAlignVertical: "center"`, explicit
`lineHeight` ≈ 20 for 16 px; `flexWrap: "nowrap"` with the label `flexShrink: 1` + `textAlign: "center"`;
render the icon slot only when there is an icon; give the buttons `accessibilityRole="button"` (already) and
a `testID`.
Tests: matrix sweep with `FIRST_SCREENS=welcome,sign-in,sign-up` → `label-offcenter` (ink + node bounds,
> 2 dp) clean in light/dark × pt-BR/en/es/pt-PT × font 1.0/1.3/2.0 × small/default; crops of both buttons
reviewed at 200 %; real Moto screenshot.

## Lesson
All of this was invisible on the developer's emulator in light mode, English, font 1.0. The gate now
requires the tester's config (mid-range Moto, dark, pt-BR, font 1.3) in **both** gesture and 3-button
navigation on real hardware. Reports 6–7 add the launch itself (recorded frames, several aspect ratios,
both themes) and measured, not assumed, centering of the first screen's buttons.
