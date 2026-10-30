---
name: mobile-app-qa
description: >-
  Find → fix → re-verify QA that leaves a mobile app (Expo/React Native, Android first) working and
  looking right. Use BEFORE a store or test-track release, AFTER tester or Play
  pre-launch reports, when it "works on my phone" but breaks elsewhere (dark mode, other language, big
  font, 3-button nav, another brand), or when asked to test, QA, harden or break a mobile app. Builds a
  feature inventory, runs functional E2E, a LIVE pass (real accounts, email, DB, push, two devices), an
  adb + Maestro matrix sweep (theme × locale × font × size × nav mode) with detectors (incl. controls
  under the system bars), locale/translation research, a mandatory RED-TEAM pass every iteration (chaos,
  fuzz, RLS/IDOR, role escalation, invite abuse, injection, tampering, PII leaks), scores 12 dimensions
  0-4, ranks P0-P3, loops until two consecutive full iterations find zero findings, then runs a FINAL
  PASS on the signed release APK installed on clean emulators (fresh + update) and gates the release. Adapted from Impeccable.
---

# Mobile app QA (the "impeccable" pass for phones — looks AND works)

A structured pass that takes an existing mobile app and leaves it **working and looking right on every
front we know how to check**: it inventories every feature, finds problems, fixes them in priority
order, proves each fix with a regression test, and only then lets the build ship. Appearance and
functionality get **equal rigor**: a beautiful screen that saves the wrong number is a P0, and so is a
correct screen that renders black in dark mode.

It is the mobile counterpart of [`roblox-game-qa`](../roblox-game-qa/) and complements
[`play-store-aso-growth`](../play-store-aso-growth/) (which starts once the app is good).

**Honest scope.** This maximizes coverage; it cannot guarantee a bug-free app. Emulators lie about
OEM skins, GPU, memory, keyboards and real networks; testers find what no checklist predicts. That is
why the pass ends with a **release gate** that needs a real low/mid-range Android phone and real people,
and why every tester report becomes a regression test. Always state what produced the evidence
(static check, unit test, E2E on emulator, matrix sweep, real device, real testers) and what stayed
**untested**.

Method credit: the pass structure (separate audit / critique / harden / adapt / polish passes, 0-4
dimension scores, P0-P3 severity, anti-pattern catalogs, "a detector result is evidence, not proof",
screenshots from the emulator/device and never a browser, `cmd uimode night` + `font_scale` in the
verification pass, saying which evidence came from hardware) is adapted from Paul Bakaus's
[Impeccable](https://github.com/pbakaus/impeccable) (Apache-2.0), especially its `audit.native`,
`adapt.native`, `harden`, `polish` and `android` references. No text is copied; the mobile QA content,
functional-testing method and scripts are original. More sources in
[reference/sources.md](reference/sources.md).

## Tools this skill assumes (all free)
- **Repo:** Expo/RN + TypeScript; unit tests (Vitest or Jest); `tsc --noEmit`; ESLint.
- **Android SDK + JDK 17** (emulator, `adb`, `avdmanager`, `bundletool` for `.aab` → universal APK).
  KVM on Linux for a usable emulator. On the owner's box: SDK `/home/box/android-sdk`, JDK `/home/box/jdk17`.
  **No KVM** (VM without nested virtualization: `-accel off`, ~15 min boot)? Run the emulator passes on
  **GitHub Actions** with [`templates/ci/android-emulator-maestro.yml`](templates/ci/android-emulator-maestro.yml)
  (KVM on free runners, 35-58 s boot, ~10-13 min/API level; API 30 = 3-button + 34 = gesture nav) →
  [reference/device-clouds.md](reference/device-clouds.md).
- **Maestro** (`curl -fsSL https://get.maestro.mobile.dev | bash`) for E2E flows on the **release** build.
- **This skill's scripts:** [`scripts/matrix-sweep.sh`](scripts/matrix-sweep.sh) (config matrix ×
  screens → screenshots + UI dumps), [`scripts/sweep-check.py`](scripts/sweep-check.py) (detectors:
  black/blank screens, wrong money/number format per locale, raw i18n keys, `undefined`/`NaN`,
  untranslated English, invisible/low-contrast text, small touch targets, stuck banners, controls under
  the system navigation/status bar, off-center button labels, stretched images; `--splash` splash-frame
  checks; `--launch-audit` static splash/icon config audit),
  [`scripts/splash-capture.sh`](scripts/splash-capture.sh) (screenrecord every cold/warm/hot launch per
  profile × theme → frames), [`scripts/adb-env.sh`](scripts/adb-env.sh) (one-line device
  state toggles + reset).
- **Red-team:** [`scripts/red-team-chaos.sh`](scripts/red-team-chaos.sh) (seeded monkey, trim-memory, low
  storage, clock/timezone, rotation, back spam, kill mid-write, clear data, permission revoke) and
  [`scripts/rls-probe.sh`](scripts/rls-probe.sh) (RLS/IDOR probe with an attacker's token; prints status
  and counts only).
- **Shared machine:** [`scripts/box-reserve.sh`](scripts/box-reserve.sh) (`status` load + locks + slots,
  `reserve` with overlap check, `acquire`/`check`/`left`/`release` lock; trap-friendly). Schedule:
  `/home/box/shared/box-schedule.md`. `final-pass.sh` and `matrix-sweep.sh` refuse to run without a lock.
  RAM GO/NO-GO and watchdog: `/home/box/shared/box-preflight.sh` (from `roblox-game-qa/scripts/`) when present.
- **FINAL PASS:** [`scripts/final-pass.sh`](scripts/final-pass.sh) (`setup` SDK images + AVDs, `boot` a clean
  headless emulator, `install` fresh, `update-prev` + `update` over the previous version, `evidence`/`record`
  screenshots and video, `logscan` crash/ANR/error/PII scan, `perf` gfxinfo/meminfo).
- **Templates:** [`templates/`](templates/) — `APP-QA.md` context file, `FEATURES.md` inventory,
  `glossary-template.md` (per-locale conventions + glossary + tone guide), Maestro config/flows/subflows
  (smoke, pt-BR money input, offline banner recovery, screen sweep, two-account invite, red-team inputs), report with iteration ledger + tester
  bug template, `ci/android-emulator-maestro.yml` (GitHub Actions emulator + Maestro job).
- **Cloud (free tiers, tested and ranked → [reference/device-clouds.md](reference/device-clouds.md)):**
  1. GitHub Actions emulator (best; 2,000 free min/month private, unlimited public); 2. Firebase Test Lab
  Spark (10 virtual + 5 physical runs/day, no card; shuts down 2027-09-30); 3. Play internal track +
  pre-launch report (report seems to need a closed-track upload — confirm); 4. Samsung Remote Test Lab
  (real Galaxy devices, manual from a desktop browser only). Anything paid needs the owner's approval.
- **Real hardware:** at least one low/mid Android (Moto G / Galaxy A / Redmi class) + ≥2 real testers.

## How to run the pass (order matters)

| # | Pass | Goal | Output |
|---|------|------|--------|
| 0 | **Reserve the machine** (mandatory on a shared box) | Before any build, emulator, Maestro, sweep, red-team chaos or FINAL PASS: check load (`free -h`, `nproc`, `uptime`, heavy processes, `adb devices`), read the shared schedule, book a slot with `scripts/box-reserve.sh` (overlap → message the other agents and wait for an OK), hold the lock while running, release on exit even on failure. Caps: one emulator per agent (`-memory 4096 -cores 4`), Gradle `-Xmx3g --max-workers=2`, `nice`/`ionice`; shared SDK add-only; never kill others' processes; pause and resume in the next slot. → [reference/shared-machine.md](reference/shared-machine.md) | booked slot + lock |
| 0 | **Context** | Write/refresh `APP-QA.md` (stack, locales, currencies, themes, min/target SDK, device targets, test accounts *names only*, backend envs, known-unfinished areas). | `APP-QA.md` |
| 1 | **Inventory** | Read the code and list **every** screen, flow, form, button, permission, notification, deep link, backend call, background job and calculation, with roles and states. | `FEATURES.md` |
| 1b | **Language research + copy** | Before translating or reviewing copy: research each target locale's format conventions (CLDR table, verified on device) and language (variant, register, everyday words), harvest the wording of top apps in the same category/market and the OS's own terms, write a per-locale glossary + tone guide, then translate/rewrite. | `qa/l10n/<locale>-glossary.md` + catalog changes |
| 2 | **Audit** (code + build) | Everything measurable without a person: types, lint, unit/integration tests, release config, theming tokens, i18n catalog, formatting helpers, RLS/security, dead flags. | scored findings |
| 3 | **Functional E2E** | Every inventory row: happy path + edge + failure, automated with Maestro where possible; two-account flows; data correctness checked against an oracle. | findings + flows |
| 3b | **Live E2E** (mandatory) | Real backend, real tagged accounts (`qa+<run>@…`), real emails in a real inbox (arrival, spam, SPF/DKIM, links), real DB rows checked with SQL, RLS between real accounts, real FCM push on devices (fg/bg/killed), two devices for multi-user, uploads, test-mode billing, account deletion, then verified cleanup. Never touches real users' data; never prints secrets. | live evidence + cleanup log |
| 4 | **Matrix sweep** | Every screen × light/dark × every locale × font scale × screen size × 3-button/gesture nav on the release build (emulator locally with KVM, else GitHub Actions API 30 + 34 → [reference/device-clouds.md](reference/device-clouds.md)); detectors (incl. `label-offcenter`, `image-distortion`) + human review of the contact sheet and crops. | findings + screenshots |
| 4b | **Launch/splash pass** (mandatory) | `--launch-audit` of the splash/icon config, then screenrecord **cold + warm (+ hot)** launches in **light + dark** on small, 1080×2400 and tablet profiles: Android 12+ SplashScreen rules (icon inside the 160/192 dp circle, no stretching, background color per theme), adaptive + monochrome launcher icon, native splash → first screen with no flash/jump/blank; frame detectors + human review of the strips. → [reference/launch-and-visual-precision.md](reference/launch-and-visual-precision.md) | `qa/splash/<run>/` frames + strips |
| 5 | **Harden** | Offline/slow/flaky network, process death, permissions denied, background/foreground, push, deep links, extreme data, clock/timezone, upgrades. | findings |
| 6 | **Critique** (look & UX) | Use the app like a first-time user on a real phone; judge hierarchy, clarity, feedback, consistency, platform conformance (Material 3 on Android). | findings |
| 6b | **RED-TEAM** (mandatory, every iteration) | Act as attacker and hostile user: chaos (monkey with seeds, fuzz/adversarial inputs, double taps, kill/airplane mid-write, trim-memory, low storage, clock/DST, rotation, permission revoke, two users editing the same record, expired session) **and** security abuse (RLS/IDOR across spaces, privilege escalation between co-parents, invite abuse, RPC/storage/realtime access, tampered requests, injection, auth abuse, deep-link injection, APK secrets, PII in logs, consent). Every successful attack is a finding. → [reference/red-team.md](reference/red-team.md) | `qa/red-team/<iter>/` |
| 7 | **Convergence loop** | Fix in severity order (failing regression test first, one commit per finding), then re-run the **FULL** pass 2–6b plus all regression tests; repeat until **two consecutive full iterations have zero findings of any severity** (the second with fresh seeds/inputs). Iteration ledger, anti-cheating rules, safety cap → [reference/convergence-loop.md](reference/convergence-loop.md) | ledger + commits |
| 7b | **FINAL PASS** (mandatory) | After the loop exits: build the signed release artifact (AAB → `bundletool build-apks --mode=universal` with the upload key, or a release APK), `adb install` it on **clean emulators** (headless Linux; Android 14 and 15/16, Play Store image, mid-range 1080×2400 and a small-screen profile) as a **fresh install AND an update over the previous version**, then run the real app end to end (no local KVM → same on GitHub Actions, API 30 + 34, see [reference/device-clouds.md](reference/device-clouds.md)): full feature walkthrough, live backend flows, whole Maestro suite, matrix sweep, red-team quick pass, logcat `*:E`/crash/ANR scan, `dumpsys gfxinfo`, screenshots + `screenrecord` video. Preferably also install from the Play closed-test track on a real phone. **Any finding restarts the loop.** → [reference/final-pass.md](reference/final-pass.md) | `qa/final/` evidence |
| 8 | **Gate + release** | Only after the loop exits and the FINAL PASS is clean: run the release gate; upload to the test track; read the pre-launch report; smoke-test the store-installed build on a real phone. | gate report |
| 9 | **Feedback loop** | Every tester report → reproduce → finding → back into the convergence loop (full pass, two clean iterations) → new bug classes go into the anti-pattern catalog and the red-team corpus. | bug log |

Rules for running it:
- **Run Audit, Functional E2E and Critique independently.** With sub-agents, give each its own context
  so code reading doesn't bias the critique; merge afterwards.
- **Test the release build.** Dev builds hide bugs (LogBox, Metro, dev-only flags, no minification,
  different JS engine settings). E2E, sweep and gate always run on a release APK/AAB.
- **See it running.** Code reading cannot judge contrast, clipping, banners, keyboards or real formats.
- **Locale-proof selectors.** Maestro flows select by `testID` (`id:`), never by visible text, so the
  same flow runs in every language. Missing `testID`s are findings.
- **Fix in severity order, one change at a time**; never one giant "QA fixes" commit; never polish
  visuals while a P0/P1 is open.
- **This skill drives fixing, not just reporting, and loops.** It ends only when the convergence loop exits
  (two consecutive clean full iterations, gate ✅) or the safety cap escalates with an explicit list of
  what blocks it and why. "Zero" means zero P0–P3 — nothing lowered, skipped or accepted without the owner.
- **Be a good neighbour on a shared machine.** No heavy step without a booked slot and a live lock
  (`box-reserve.sh`); stay inside the caps; stop your own emulators/daemons; never touch other agents'
  processes or shared SDK components; when the slot ends, save state and resume in the next one.
- **Finish on the real artifact.** Nothing ships on the strength of dev builds or code reading: the FINAL
  PASS installs the exact signed APK users will get and runs the real app; its findings send you back into
  the loop.
- **Test AND try to break.** Confirming the happy path is half the job; the red-team phase runs in every
  iteration with new seeds and its own findings count toward zero.
- Read [reference/anti-patterns.md](reference/anti-patterns.md) before the first fix.

## Severity (blocker → polish)
- **P0 Blocker** — crash/ANR, data loss or **wrong data** (wrong total, wrong split, value saved in the
  wrong unit/scale), a feature that cannot be completed, a screen unreadable in a supported config
  (e.g. black screen in dark mode), privacy/security leak (other family's data, RLS/IDOR, privilege
  escalation, secret in the APK, PII in logs/analytics), any successful red-team attack on data or auth, store-policy violation,
  sign-in/sign-up impossible. Fix now; blocks release.
- **P1 Major** — a large share of users will struggle or distrust the app: wrong number/date/currency
  format for the chosen language, untranslated strings, banner/toast that never goes away, text clipped
  at font scale 1.3, keyboard covering the submit button, **system navigation/status bar covering app
  controls (3-button or gesture nav)**, **distorted/stretched/placeholder splash or logo, splash in the
  wrong theme, white/black flash or logo jump at launch** (first impression), TalkBack can't reach a primary action,
  offline edits silently lost on restart, broken back gesture. Fix before release.
- **P2 Minor** — annoyance with a workaround: inconsistent spacing, **button/chip label off-center (> 2 dp;
  P1 on the welcome/sign-in/sign-up primary actions), squashed/stretched image, off-grid alignment,
  inconsistent icon sizes**, a missing empty state illustration,
  slow-but-working screen, minor contrast miss on secondary text. Next pass.
- **P3 Polish** — finish details: motion timing, copy tone, icon alignment. If time permits; keep short.

Not everything is P0. A list of 40 P1s is a failed triage. When unsure between two levels, ask: "would
a tester stop using the app or tell a friend it's broken?" → the higher one.

## Dimension scores (0-4)
**0** broken · **1** major gaps · **2** works with rough edges · **3** good, minor issues · **4**
excellent, verified on a real device in every supported config.

| # | Dimension | Must be 4 for release? |
|---|-----------|------------------------|
| 1 | Build & release config | — (≥3) |
| 2 | **Functional correctness** (inventory coverage, data correctness) | **yes** |
| 3 | Data, sync & security (offline queue, conflicts, multi-user, RLS) | **yes** |
| 4 | **Appearance & theming** (light + dark, contrast, system bars) | **yes** |
| 5 | **Localization & formatting** (every shipped locale) | **yes** |
| 6 | Layout & adaptivity (sizes, font scale, insets, keyboard) | — (≥3) |
| 7 | Accessibility (TalkBack, targets, contrast, labels) | — (≥3) |
| 8 | Resilience & lifecycle (network, process death, permissions, push, links) | — (≥3) |
| 9 | Performance & stability (startup, jank, memory, ANR) | — (≥3) |
| 10 | Store & compliance (Play policies, data safety, account deletion) | — (≥3) |
| 11 | Feedback loop (bug log, regression tests, iteration ledger) | — (≥3) |
| 12 | **Security & abuse resistance** (red-team: RLS/IDOR, roles, invites, injection, tampering, PII, chaos) | **yes** |

---

## The checklist (condensed; details and how-tos in `reference/`)

### 1. Build & release config → [reference/build-and-release.md](reference/build-and-release.md)
- [ ] Clean checkout: `npm ci && npx tsc --noEmit && npx eslint . && npm test` green; `npx expo-doctor` clean.
- [ ] Release build reproducible (`eas build --local` or `npx expo prebuild && ./gradlew bundleRelease`); the AAB installs on the emulator via `bundletool` universal APK.
- [ ] No dev-only behavior in release: dev menus, sample/seed data, `__DEV__` branches that change logic, test accounts, verbose logs, `console.log` of PII, debug feature flags (grep; one config module with a test asserting release values).
- [ ] Config plugins present for every app.json field that needs one (e.g. `expo-system-ui` for Android `userInterfaceStyle`; without it the field is silently ignored).
- [ ] `versionCode` bumped; `targetSdk` meets the Play requirement; R8/ProGuard rules don't strip reflection-based libs; Hermes on.
- [ ] No secrets in the bundle (only public anon keys); service-role keys never in the app.

### 2. Functional correctness → [reference/functional-testing.md](reference/functional-testing.md)
- [ ] `FEATURES.md` covers **every** screen, button, form, flow, permission, notification, deep link, backend call, background job and calculation found in the code (grep recipes in the reference). Unlisted = untested.
- [ ] Each feature has: happy path, ≥2 edge cases (boundaries, empty, max), ≥1 failure case (network/server/validation/permission), the expected result **written before** running it.
- [ ] Auth: sign-up, email confirmation, login, wrong password, password reset (link opens the app), logout, session expiry/refresh, delete account, re-login after reinstall.
- [ ] Multi-user/shared flows run with **two real accounts on two devices/emulators** (invite → accept → both see the same data → edit on A → appears on B → permissions enforced on B).
- [ ] Every calculation (splits, balances, totals, schedules, dates) has unit tests with an independent oracle (hand-computed table) plus property tests for invariants (sums conserve, round-trips hold).
- [ ] Forms: required/invalid/boundary values, paste, emoji, very long text, leading/trailing spaces, double-tap submit (no duplicates), back mid-edit (draft kept or discard confirmed).
- [ ] Every list/screen has loading, empty, error, partial and "many items" states, each reachable and tested.
- [ ] Paywall/purchases (if any): test track license testers, purchase/restore/cancel/refund, entitlements after reinstall; no real charges.
- [ ] Maestro suite (by `testID`) green on the release build **3 runs in a row** (flake check).

### 3. Data, sync & security → [reference/functional-testing.md](reference/functional-testing.md#data-sync-and-security)
- [ ] Offline create/edit/delete → kill app → reopen → still there → reconnect → synced once (no dupes), conflict rule visible and correct.
- [ ] Supabase RLS: user B cannot read/write family A's rows (tests with two JWTs or pgTAP); storage buckets private where needed; signed URLs expire.
- [ ] Every "syncing/offline" state has a **recovery path** (retry timer or user action) and clears itself when the condition ends.
- [ ] **Upgrade path:** install the previous production build (from Play or its APK) → create data in every feature, including queued offline writes → update over it (`adb install -r` and via the Play test track) → data intact, migrations ran once, still signed in, outbox flushed.
- [ ] **Old client vs new backend:** the previous app version keeps working (or is force-updated cleanly) after this release's DB migrations/Edge Functions deploy — run its smoke flow against staging after migrating.
- [ ] Multi-device concurrency: same record edited on A and B at the same time (online and both offline) → documented conflict rule, no silent loss, both converge.
- [ ] Token lifecycle: access-token expiry, refresh-token revoked, password changed elsewhere, removed from the space → handled without data loss or loops; server cuts access immediately.
- [ ] No PII/tokens in logcat, crash reports or analytics events (grep with distinctive QA values); analytics/crash SDKs respect consent; tokens in SecureStore, not AsyncStorage; logout wipes local user data.

**Live (pass 3b) → [reference/live-e2e.md](reference/live-e2e.md):**
- [ ] Every live flow L1–L14 that applies passes against the production-like backend with tagged QA accounts: sign-up/login/reset with emails really delivered (inbox not spam, localized, links/App Links open the app, SPF/DKIM/DMARC pass), DB rows verified by SQL, RLS isolation with a third account, invites + realtime between two devices, uploads, FCM push in foreground/background/killed opening the right screen, test-mode billing, account/data deletion.
- [ ] Cleanup verified (zero QA rows/objects left); no secrets or real users' data in logs, screenshots or reports.

### 4. Appearance & theming → [reference/appearance-and-theming.md](reference/appearance-and-theming.md)
- [ ] Every screen captured in **light and dark** (system setting **and** in-app override, if any) on the release build; contact sheet reviewed by a human.
- [ ] All colors come from theme tokens; grep finds no raw hex/`"white"`/`"black"` in components; images/icons/SVGs have dark variants or use `currentColor`/tint.
- [ ] Dark theme is designed, not inverted: surfaces have visible elevation steps (not pure `#000` everywhere), text ≥ 4.5:1, borders/dividers visible, disabled states distinguishable.
- [ ] Native surfaces follow the theme: splash (dark variant), root view background, status/nav bar icon contrast, keyboard appearance, `Modal`, `Alert`, date pickers, WebViews.
- [ ] Theme switches live (no restart) and survives process death; no white/black flash at launch.
- [ ] **Launch/splash (P1) → [reference/launch-and-visual-precision.md](reference/launch-and-visual-precision.md):** `sweep-check.py --launch-audit` clean (expo-splash-screen with transparent logo, `imageWidth`, `resizeMode: contain`, `dark` block; no bitmap `windowBackground`; no Expo placeholder); `splash-capture.sh` frames for cold + warm + hot × light + dark × small/1080×2400/tablet: logo round/undistorted and centered, background matches the theme and the first screen, no flash, jump or blank frame; `--splash` detectors clean and every strip reviewed.
- [ ] Launcher icon: adaptive foreground inside the 66/108 safe zone (circle, squircle, rounded-square masks), monochrome layer for Android 13+ themed icons, light and dark launchers.
- [ ] OEM "force dark"/"dark mode for apps" toggles don't double-invert the app (test on a real Motorola/Samsung/Xiaomi when possible).

### 5. Localization & formatting → [reference/i18n-and-formatting.md](reference/i18n-and-formatting.md) + [reference/translation-quality.md](reference/translation-quality.md)
**Translation quality (research before translating; never translate word by word):**
- [ ] Per-locale research done **before** any translation: variant (pt-BR ≠ pt-PT; es-419 ≠ es-ES), register (pt-BR *você*; pt-PT *tu*/impersonal; es-419 *tú* vs *usted*), everyday words people really use, and the category's jargon in that market.
- [ ] Wording harvested from ≥5 top apps of the same category **in that market** (store listings + in-app strings/screenshots) and from the OS's own UI in that language (Android/Material terms: pt-BR *Configurações, Entrar, Sair, Salvar, Cancelar, Excluir, Compartilhar*; pt-PT *Definições, Iniciar sessão, Terminar sessão, Guardar, Eliminar, Partilhar*).
- [ ] `qa/l10n/<locale>-glossary.md` exists (term → chosen translation → rejected alternatives → source) plus a tone guide; every string obeys it (glossary-consistency check).
- [ ] No calques/false friends or machine-translation tells; gender/plural correct (ICU plural forms); natural length (no truncation).
- [ ] **Every string reviewed in context on sweep screenshots** by a native-level reviewer (or the agent with the glossary + a second independent agent pass), and ideally one native tester per locale.
**Locale conventions (research before translating):**
- [ ] Per-locale conventions table written from CLDR/`Intl` and **re-checked on the device (Hermes Intl uses platform ICU)**: decimal/thousands separators, currency symbol/code/placement/spacing, negatives, percent, dates, 12/24 h, first weekday, day/month names & capitalization, relative dates, units, phone, address/postal code, name order, plurals, collation with accents, quotes, number input, timezone → [reference/locale-conventions.md](reference/locale-conventions.md). Each row has a test case.
**Formatting:**
- [ ] Catalog parity test: every key exists in every shipped locale; no placeholders mismatched; no raw keys on screen.
- [ ] **Format with the user's locale, not the currency's country nor the device default**: one `formatMoney/formatNumber/formatDate` module that takes the active app locale; golden tests per locale (pt-BR `R$ 1.234,56` with U+00A0 after `R$`).
- [ ] Money **input** accepts the locale's decimal separator (`,` for pt-BR/pt-PT/es-AR) and also `.`; parse ↔ format round-trip property test; the keyboard actually offers the separator on Samsung/Gboard/Moto keyboards.
- [ ] Changing language in-app updates every visible format immediately (no memoized formatter with the old locale); system-language change while the app runs is handled.
- [ ] Dates/times: locale order, 24h vs 12h, first weekday, timezone/DST boundaries; pluralization rules per locale.
- [ ] Text expansion: pt/es are ~20-35% longer than en; buttons/tabs/chips wrap or truncate gracefully.

### 6. Layout & adaptivity → [reference/devices-and-layout.md](reference/devices-and-layout.md)
- [ ] Sweep at font scale **1.0 / 1.3 / 2.0** and display size small/large; nothing clipped, overlapping or unreachable (scroll exists).
- [ ] **System bars never cover the app (P1 gate item):** every screen swept in **both 3-button and gesture navigation** (`scripts/adb-env.sh nav threebutton|gestural`; sweep `NAVS`), edge-to-edge on Android 15+ (forced on Android 16; always on Expo SDK 54+). Bottom tab bar, bottom buttons/footers, FABs, snackbars, sheets, modals and the keyboard's submit row sit above the nav bar/gesture handle; headers and top banners below the status bar and cutout. `nav-overlap`/`status-overlap` detectors clean; `react-native-safe-area-context` insets everywhere (no fixed bottom padding).
- [ ] Keyboard open in both nav modes: focused input and submit visible, no double inset (keyboard + nav inset) gap.
- [ ] Keyboard never covers the focused input or the submit button (test small screen + font 1.3 + gesture nav).
- [ ] Small phone (≈360×640 dp) and large phone/tablet/landscape (if supported) both usable.
- [ ] **Visual precision (P2; P1 on first screens):** labels centered horizontally **and** vertically in every button/chip/pill/tab (Android `includeFontPadding` + custom font metrics), in every locale and font scale; images/logos keep their aspect ratio (`qa/assets.tsv` → `image-distortion`); 4/8 dp grid, aligned edges and baselines, one icon scale; `label-offcenter`/`image-distortion` clean and crops of the first screens' primary buttons reviewed at 200 %.

### 7. Accessibility → [reference/accessibility.md](reference/accessibility.md)
- [ ] TalkBack: every control has a role + label + state, logical order, no traps, banners announced (`accessibilityLiveRegion`), focus moves on navigation.
- [ ] Touch targets ≥ 48×48 dp with spacing; contrast ≥ 4.5:1 text / 3:1 UI in both themes; no meaning by color alone.
- [ ] Accessibility Scanner (free app) run on key screens; pre-launch report accessibility warnings triaged.
- [ ] TalkBack actually exercised: core flows completed with TalkBack on (enable on a Play image: `adb shell settings put secure enabled_accessibility_services com.google.android.marvin.talkback/com.google.android.marvin.talkback.TalkBackService` + `settings put secure accessibility_enabled 1`; turn off after) in pt-BR and en, light and dark; labels are localized.

### 8. Resilience & lifecycle → [reference/resilience-and-performance.md](reference/resilience-and-performance.md)
- [ ] Airplane mode, slow (EDGE/GPRS) and flaky network on every write action; timeouts show a retry, never an infinite spinner.
- [ ] Background → foreground after 30 min; process death with "Don't keep activities"; rotate; split screen; low memory.
- [ ] Permissions: allow, deny, deny forever, revoke in Settings while running (camera/photos/notifications).
- [ ] Push notifications: permission flow on Android 13+, tap opens the right screen (cold + warm start), no duplicates.
- [ ] Deep links / invite links: cold start, warm start, logged out (resumes after login), invalid/expired link.
- [ ] Device clock/timezone change while the app is open, DST gap/overlap days in the user's zone, leap day, year boundary; two users in different timezones see the same date for the same event.
- [ ] Low storage (`cmd devicestoragemonitor force-low`), low memory (`am send-trim-memory`), battery saver, OEM background-kill: no corrupted local data, clear messages.
- [ ] App update over an installed build while offline writes are pending; reinstall; `pm clear`.

### 9. Performance & stability → [reference/resilience-and-performance.md](reference/resilience-and-performance.md#performance)
- [ ] Cold start to interactive ≤ ~2 s on the mid-range target (release); lists virtualized; no jank in scroll (gfxinfo janky frames < ~5%).
- [ ] Zero crashes/ANRs in sweep + E2E logcat (`adb logcat -b crash`), in the pre-launch report and in Play vitals.
- [ ] Memory stable across 3 loops of the main flow (no growth trend).

### 10. Store & compliance → [reference/release-and-store.md](reference/release-and-store.md)
- [ ] Data safety form matches what the code actually collects/sends; privacy policy URL works; in-app + web account deletion.
- [ ] Permissions declared = permissions used; no unexplained sensitive permissions.
- [ ] Pre-launch report: no crashes, security warnings triaged, screenshots reviewed (they come from many devices — free coverage).

### 11. Feedback loop → [reference/feedback-loop.md](reference/feedback-loop.md)
- [ ] Each tester report logged with the bug template, reproduced in the **same config** (device class, theme, locale, font scale) or marked "cannot reproduce" with what was tried.
- [ ] Fix → regression test (unit, Maestro flow or sweep detector) → re-verified in the failing config → anti-pattern catalog updated if the class is new.

### 12. Security & abuse (RED-TEAM) → [reference/red-team.md](reference/red-team.md)
- [ ] Every attack S1–S16 run with three QA accounts (owner A, co-parent B, stranger C) on staging via [`scripts/rls-probe.sh`](scripts/rls-probe.sh) and manual requests; every table, view, RPC, bucket and realtime channel in the inventory covered.
- [ ] Chaos C1–C12 run with new seeds this iteration ([`scripts/red-team-chaos.sh`](scripts/red-team-chaos.sh), Maestro [`red-team-inputs.yaml`](templates/maestro/flows/red-team-inputs.yaml) pattern on every input); seeds recorded.
- [ ] Every successful attack → finding (security/data = P0) → failing test/probe first → fix → probe added to the permanent suite.

---

## Matrix sweep (pass 4) in one screen
Full recipe and caveats in [reference/matrix-sweep.md](reference/matrix-sweep.md).
```bash
# release APK installed on a booted emulator; screens.txt = name|deeplink or a Maestro sweep flow
APP_ID=com.example.app SCREENS=qa/screens.txt OUT=qa/sweep/$(date +%F-%H%M) \
LOCALES="en-US pt-BR es-419 pt-PT" THEMES="light dark" FONTS="1.0 1.3 2.0" SIZES="default small" \
NAVS="gestural threebutton" \
  mobile-app-qa/scripts/matrix-sweep.sh
FIRST_SCREENS=welcome,sign-in,sign-up python3 mobile-app-qa/scripts/sweep-check.py qa/sweep/<run> --assets qa/assets.tsv
#   → findings.md + contact sheets + crops/ (label-offcenter, image-distortion and the rest)
# launch/splash pass (pass 4b)
python3 mobile-app-qa/scripts/sweep-check.py --launch-audit . [--android-res android/app/src/main/res]
APP_ID=com.example.app BOX_PROJECT=<proj> mobile-app-qa/scripts/splash-capture.sh   # cold/warm/hot × light/dark × 3 profiles
python3 mobile-app-qa/scripts/sweep-check.py --splash qa/splash/<run> --logo assets/logo.png
```
Core toggles it uses (all restorable; `scripts/adb-env.sh reset` puts the device back):
`cmd uimode night yes|no` · `cmd locale set-app-locales <pkg> --locales pt-BR` (Android 13+, no root) ·
`settings put system font_scale 1.3` · `wm size 720x1280` + `wm density 320` · `exec-out screencap -p` ·
`exec-out uiautomator dump /dev/tty`. The detectors flag; a **human (or vision model) still looks at every
dark-mode and pt-BR screenshot** — a detector result is evidence, not proof.

## Release gate (definition of done)
Ship (even to a closed test) only when all are true; otherwise report what's missing:
- [ ] **Convergence loop exited:** two consecutive FULL iterations (all phases incl. live and red-team) with
      **zero findings of any severity**, the second with fresh seeds/inputs; ledger in the report; no Blocked
      items. (Anything the owner explicitly accepted in writing is listed as "accepted, not zero".)
- [ ] Scores ≥3 everywhere and **4** on Functional correctness, Data/sync/security, Appearance & theming,
      Localization & formatting, Security & abuse resistance.
- [ ] **FINAL PASS clean** ([reference/final-pass.md](reference/final-pass.md)): signed release APK (same
      commit/versionCode/key as the upload) installed with `adb install` on clean emulators (Android 14 + 15/16,
      mid-range + small screen) as fresh install **and** update over the previous version; feature walkthrough,
      live flows, Maestro suite, sweep, red-team quick pass all green; `logscan` 0 crashes/ANRs/app errors;
      screenshots + video attached. Real-device install from the Play closed track done, or listed as Blocked.
- [ ] Red-team: every S/C attack attempted in the last iteration on the Play test-track build; none succeeded.
- [ ] Shared machine: every heavy run happened inside a booked slot with a live lock; locks released, own
      emulators/Gradle daemons stopped, no shared SDK component removed or overwritten.
- [ ] Clean checkout: types, lint, unit + integration tests green; release config checks pass.
- [ ] Every `FEATURES.md` row has status ✅ with evidence (test name or run id); none "not tested".
- [ ] Maestro suite green 3× in a row on the **release** build; two-account flows included.
- [ ] Matrix sweep complete (every screen × theme × locale × font × size), detectors clean or every flag
      triaged, contact sheet reviewed, logcat crash buffer empty.
- [ ] Locale conventions: table per shipped locale, every convention test green in Node **and** on the device (Hermes).
- [ ] Translation quality: research + glossary + tone guide per shipped locale; every string reviewed **in context on screenshots**; zero P0/P1 copy findings (wrong variant, wrong register, calque, untranslated, truncated, wrong plural/gender); a native speaker per locale signed off or is listed under "Untested".
- [ ] **Live E2E pass green on the release build installed from the Play test track** (real accounts, emails, DB checks, push, two devices, deletion) with cleanup verified → [reference/live-e2e.md](reference/live-e2e.md).
- [ ] **Insets (P1):** every screen in **3-button and gesture navigation**, edge-to-edge, no control or text
      under the system bars (`nav-overlap`/`status-overlap` clean + contact sheet reviewed), keyboard cases included.
- [ ] **Launch/splash (P1):** `--launch-audit` and `--splash` clean on the release build (cold + warm, light +
      dark, small/1080×2400/tablet); logo undistorted and centered, splash color per theme, no flash/jump; adaptive
      + monochrome icon checked; strips reviewed. **Visual precision (P2):** `label-offcenter`/`image-distortion`
      clean or triaged; first screens' primary buttons crop-reviewed.
- [ ] Real low/mid Android phone: full main flow in **dark + pt-BR + font 1.3 + gesture nav** and again in
      **3-button nav**, and in light + en-US.
- [ ] Pre-launch report: no crashes/ANRs; warnings triaged.
- [ ] ≥2 real testers who didn't build it completed the core flows without help; reports logged.
- [ ] Post-upload smoke test of the **store-installed** build on a real phone.

## Report formats
**Finding:**
```
P1 — [Localization] Expense amount shows US format in pt-BR
  Config: release vc7 · Moto G73 (Android 14) · dark · app lang pt-BR · font 1.0 · gesture nav
  Evidence: tester screenshot + sweep run 2026-10-30-1700 (ptBR_dark_f1.0/expense-form.png, detector money-format)
  Repro: Settings → Language → Português (BR) → Expenses → New → type 1234,56 → hint shows "R$1,234.56"
  Expected: "R$ 1.234,56"      Root cause: (file:line)
  Fix: (what changed)          Regression test: money.format.test.ts › pt-BR golden + Maestro expense-pt-br.yaml
  Verified: emulator sweep + real phone, same config
```
**Tester report → bug:** see [templates/report-template.md](templates/report-template.md).
**End of pass:** iteration ledger, FINAL PASS results per emulator profile (install/update, logscan, perf, evidence links), dimension scores table, counts by severity, red-team attempts/successes, top 3 fixes, gate checklist ✅/❌, and an
explicit **"Untested:"** line (devices, locales, flows, OS versions you could not check).

## Lessons from real tester bugs (EvenKeel closed test, Moto G73 5G)
Full analysis and the regression tests they produced: [reference/case-evenkeel.md](reference/case-evenkeel.md).
1. **"Dark mode = black, weird screens."** Dark was never swept on the release build; pure `#000` ground
   with `#111` surfaces erases elevation, and any hard-coded dark text or un-themed native surface
   (splash, modal, picker, icons) disappears. → Sweep every screen in dark; token-only colors; elevation steps.
2. **"pt-BR shows money as $1,234.56."** `Intl` with currency `BRL` but locale `en` gives `R$1,234.56`:
   currency and format locale are different things. Any formatter that reads the device default or a
   stale/memoized locale instead of the **active app language** breaks after an in-app language change.
   → One formatter module, golden tests per locale, sweep detector for US-style money in non-en locales.
3. **"A top alert never goes away."** A status banner driven by a latched flag (e.g. `online=false` set
   after one failed request) with no retry path and no dismiss stays forever even when the network is
   fine. → Every banner has an exit condition, a timeout or dismiss, and a recovery retry; tested by
   toggling the condition off.
4. **"The translations aren't good."** Strings were translated before anyone studied how Brazilians,
   Portuguese and Latin Americans actually talk in apps. → Research + glossary + in-context review is a
   gate item ([reference/translation-quality.md](reference/translation-quality.md)).
5. **"The Android navigation bar covers the app's buttons."** Expo SDK 54+ draws edge-to-edge on every
   Android version, but the bottom tab bar used a fixed bottom padding instead of the safe-area inset. →
   Every screen in 3-button **and** gesture nav, `nav-overlap` detector, insets on every bottom element.
6. **"The launch logo is distorted/stretched."** No `expo-splash-screen` config: prebuild left the Expo
   template placeholder as a **bitmap `android:windowBackground`**, which Android stretches to the whole
   window (a square becomes a 20:9 oval), white even in dark mode. → Launch/splash pass with frame
   capture on several aspect ratios; `--launch-audit` + `--splash` detectors; P1.
7. **"The text isn't centered in 'Criar uma conta' / 'Entrar'."** The layout was "centered" but the label
   ink wasn't: Android font padding + Geist metrics (and a wrapping flex row) shift it. → `label-offcenter`
   detector on uiautomator bounds + ink, crops reviewed at 200 %; P1 on the first screens.
8. Testers found these in minutes on one phone — the gate's "real mid-range Android, dark + pt-BR +
   font 1.3" line exists because of this.

## Anti-patterns of the QA itself
- Testing only the dev build, only light mode, only English, only font 1.0, only a Pixel emulator.
- Maestro flows that select by visible text (break in every other language) or `sleep` instead of waits.
- Declaring a feature tested because one happy path passed; no edge/failure case; no expected result written first.
- Translating string by string with no research, glossary or screenshots; one "Portuguese" for Brazil and Portugal.
- Verifying money/date output by eye in English only; no golden tests per locale.
- Fixing a reported bug without reproducing it in the reporter's config, or without a regression test.
- Testing multi-user features with one account.
- Polishing visuals while a P0/P1 is open; a giant "QA fixes" commit.
- Stopping after one pass, or re-testing only the fixed items instead of the full pass.
- Only confirming things work; never trying to break them (no red-team, no seeds, one account).
- Judging the launch from code or a single dev-build cold start in light mode; never recording the splash frames.
- Calling a layout "centered" from the code (`alignItems: center`) without measuring the rendered ink.
- Making the count reach zero by lowering severity, skipping tests or shrinking the matrix.
- Claiming the app is "100% bug-free". Report scores, evidence and what stayed untested instead.
