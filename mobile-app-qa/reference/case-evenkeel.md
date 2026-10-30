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

## Lesson
All of this was invisible on the developer's emulator in light mode, English, font 1.0. The gate now
requires the tester's config (mid-range Moto, dark, pt-BR, font 1.3, gesture nav) on real hardware.
