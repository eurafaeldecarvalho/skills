---
name: mobile-app-qa
description: >-
  A rigorous find → fix → re-verify QA pass that leaves a mobile app (Expo / React Native + TypeScript,
  Android first, iOS later; also useful for any Android app) working impeccably in BOTH appearance and
  every feature. Use it BEFORE any store release or closed/open test build, AFTER tester reports or a
  Play pre-launch report, when the app "works on my phone" but breaks on someone else's (dark mode,
  another language, big font, another Android brand), and whenever the user asks to test, QA, harden,
  polish or "make everything work perfectly" in a mobile app. It builds a feature inventory from the
  code, tests every feature end to end (happy path, edge cases, failures; two-account flows; offline and
  sync), runs a mandatory LIVE pass (real accounts, emails, DB checks, FCM push, two devices, cleanup), runs an automated adb + Maestro matrix sweep (light/dark × every locale × font scale × screen
  size) with screenshot and UI-text detectors, researches each locale's format conventions (CLDR,
  verified on device) and real everyday/app vocabulary before translating, audits theming, localization
  and money/date formatting,
  layout/insets, accessibility, resilience, performance and release-build config, scores 11 dimensions
  0-4, ranks findings P0-P3, drives the fix loop and ends with a release gate (no P0/P1, real device,
  real testers). Method adapted from Impeccable (pbakaus/impeccable).
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
- **Maestro** (`curl -fsSL https://get.maestro.mobile.dev | bash`) for E2E flows on the **release** build.
- **This skill's scripts:** [`scripts/matrix-sweep.sh`](scripts/matrix-sweep.sh) (config matrix ×
  screens → screenshots + UI dumps), [`scripts/sweep-check.py`](scripts/sweep-check.py) (detectors:
  black/blank screens, wrong money/number format per locale, raw i18n keys, `undefined`/`NaN`,
  untranslated English, invisible/low-contrast text, small touch targets, stuck banners),
  [`scripts/adb-env.sh`](scripts/adb-env.sh) (one-line device
  state toggles + reset).
- **Templates:** [`templates/`](templates/) — `APP-QA.md` context file, `FEATURES.md` inventory,
  `glossary-template.md` (per-locale conventions + glossary + tone guide), Maestro config/flows/subflows
  (smoke, pt-BR money input, offline banner recovery, screen sweep, two-account invite), report + tester
  bug template.
- **Cloud (free tiers, optional):** Google Play **pre-launch report** (runs automatically on
  closed/open test uploads), Firebase Test Lab Spark (10 virtual + 5 physical runs/day; service is
  deprecated, shuts down 2027-09-30). Anything paid needs the owner's approval.
- **Real hardware:** at least one low/mid Android (Moto G / Galaxy A / Redmi class) + ≥2 real testers.

## How to run the pass (order matters)

| # | Pass | Goal | Output |
|---|------|------|--------|
| 0 | **Context** | Write/refresh `APP-QA.md` (stack, locales, currencies, themes, min/target SDK, device targets, test accounts *names only*, backend envs, known-unfinished areas). | `APP-QA.md` |
| 1 | **Inventory** | Read the code and list **every** screen, flow, form, button, permission, notification, deep link, backend call, background job and calculation, with roles and states. | `FEATURES.md` |
| 1b | **Language research + copy** | Before translating or reviewing copy: research each target locale's format conventions (CLDR table, verified on device) and language (variant, register, everyday words), harvest the wording of top apps in the same category/market and the OS's own terms, write a per-locale glossary + tone guide, then translate/rewrite. | `qa/l10n/<locale>-glossary.md` + catalog changes |
| 2 | **Audit** (code + build) | Everything measurable without a person: types, lint, unit/integration tests, release config, theming tokens, i18n catalog, formatting helpers, RLS/security, dead flags. | scored findings |
| 3 | **Functional E2E** | Every inventory row: happy path + edge + failure, automated with Maestro where possible; two-account flows; data correctness checked against an oracle. | findings + flows |
| 3b | **Live E2E** (mandatory) | Real backend, real tagged accounts (`qa+<run>@…`), real emails in a real inbox (arrival, spam, SPF/DKIM, links), real DB rows checked with SQL, RLS between real accounts, real FCM push on devices (fg/bg/killed), two devices for multi-user, uploads, test-mode billing, account deletion, then verified cleanup. Never touches real users' data; never prints secrets. | live evidence + cleanup log |
| 4 | **Matrix sweep** | Every screen × light/dark × every locale × font scale × screen size on the release build; detectors + human review of the contact sheet. | findings + screenshots |
| 5 | **Harden** | Offline/slow/flaky network, process death, permissions denied, background/foreground, push, deep links, extreme data, clock/timezone, upgrades. | findings |
| 6 | **Critique** (look & UX) | Use the app like a first-time user on a real phone; judge hierarchy, clarity, feedback, consistency, platform conformance (Material 3 on Android). | findings |
| 7 | **Fix loop** | Fix in severity order, one change at a time; each fix gets a regression test and is re-verified in the exact config that failed. Repeat 2-6 on the touched areas until the gate passes. | commits + bug log |
| 8 | **Gate + release** | Run the release gate on a clean release build; upload to the test track; read the pre-launch report; smoke-test the store-installed build on a real phone. | gate report |
| 9 | **Feedback loop** | Every tester report → reproduce → bug → fix → regression test → re-verify on the failing device class; new bug classes go into the anti-pattern catalog. | bug log |

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
- **This skill drives fixing, not just reporting.** The pass ends only at a passing gate or with an
  explicit list of what blocks it and why.
- Read [reference/anti-patterns.md](reference/anti-patterns.md) before the first fix.

## Severity (blocker → polish)
- **P0 Blocker** — crash/ANR, data loss or **wrong data** (wrong total, wrong split, value saved in the
  wrong unit/scale), a feature that cannot be completed, a screen unreadable in a supported config
  (e.g. black screen in dark mode), privacy/security leak (other family's data), store-policy violation,
  sign-in/sign-up impossible. Fix now; blocks release.
- **P1 Major** — a large share of users will struggle or distrust the app: wrong number/date/currency
  format for the chosen language, untranslated strings, banner/toast that never goes away, text clipped
  at font scale 1.3, keyboard covering the submit button, TalkBack can't reach a primary action,
  offline edits silently lost on restart, broken back gesture. Fix before release.
- **P2 Minor** — annoyance with a workaround: inconsistent spacing, a missing empty state illustration,
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
| 11 | Feedback loop (bug log, regression tests) | — (≥3) |

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
- [ ] Migrations of local storage across app versions (install old build → create data → upgrade → data intact).

**Live (pass 3b) → [reference/live-e2e.md](reference/live-e2e.md):**
- [ ] Every live flow L1–L14 that applies passes against the production-like backend with tagged QA accounts: sign-up/login/reset with emails really delivered (inbox not spam, localized, links/App Links open the app, SPF/DKIM/DMARC pass), DB rows verified by SQL, RLS isolation with a third account, invites + realtime between two devices, uploads, FCM push in foreground/background/killed opening the right screen, test-mode billing, account/data deletion.
- [ ] Cleanup verified (zero QA rows/objects left); no secrets or real users' data in logs, screenshots or reports.

### 4. Appearance & theming → [reference/appearance-and-theming.md](reference/appearance-and-theming.md)
- [ ] Every screen captured in **light and dark** (system setting **and** in-app override, if any) on the release build; contact sheet reviewed by a human.
- [ ] All colors come from theme tokens; grep finds no raw hex/`"white"`/`"black"` in components; images/icons/SVGs have dark variants or use `currentColor`/tint.
- [ ] Dark theme is designed, not inverted: surfaces have visible elevation steps (not pure `#000` everywhere), text ≥ 4.5:1, borders/dividers visible, disabled states distinguishable.
- [ ] Native surfaces follow the theme: splash (dark variant), root view background, status/nav bar icon contrast, keyboard appearance, `Modal`, `Alert`, date pickers, WebViews.
- [ ] Theme switches live (no restart) and survives process death; no white/black flash at launch.
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
- [ ] Edge-to-edge (mandatory on Android 16; default since Expo SDK 54): content not under status bar, camera cutout, gesture bar or 3-button nav; `react-native-safe-area-context` insets used everywhere, including modals/sheets.
- [ ] Keyboard never covers the focused input or the submit button (test small screen + font 1.3 + gesture nav).
- [ ] Small phone (≈360×640 dp) and large phone/tablet/landscape (if supported) both usable.

### 7. Accessibility → [reference/accessibility.md](reference/accessibility.md)
- [ ] TalkBack: every control has a role + label + state, logical order, no traps, banners announced (`accessibilityLiveRegion`), focus moves on navigation.
- [ ] Touch targets ≥ 48×48 dp with spacing; contrast ≥ 4.5:1 text / 3:1 UI in both themes; no meaning by color alone.
- [ ] Accessibility Scanner (free app) run on key screens; pre-launch report accessibility warnings triaged.

### 8. Resilience & lifecycle → [reference/resilience-and-performance.md](reference/resilience-and-performance.md)
- [ ] Airplane mode, slow (EDGE/GPRS) and flaky network on every write action; timeouts show a retry, never an infinite spinner.
- [ ] Background → foreground after 30 min; process death with "Don't keep activities"; rotate; split screen; low memory.
- [ ] Permissions: allow, deny, deny forever, revoke in Settings while running (camera/photos/notifications).
- [ ] Push notifications: permission flow on Android 13+, tap opens the right screen (cold + warm start), no duplicates.
- [ ] Deep links / invite links: cold start, warm start, logged out (resumes after login), invalid/expired link.
- [ ] Device clock/timezone change, DST day, year boundary.

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

---

## Matrix sweep (pass 4) in one screen
Full recipe and caveats in [reference/matrix-sweep.md](reference/matrix-sweep.md).
```bash
# release APK installed on a booted emulator; screens.txt = name|deeplink or a Maestro sweep flow
APP_ID=com.example.app SCREENS=qa/screens.txt OUT=qa/sweep/$(date +%F-%H%M) \
LOCALES="en-US pt-BR es-419 pt-PT" THEMES="light dark" FONTS="1.0 1.3 2.0" SIZES="default small" \
  mobile-app-qa/scripts/matrix-sweep.sh
python3 mobile-app-qa/scripts/sweep-check.py qa/sweep/<run>   # → findings.md + contact sheet
```
Core toggles it uses (all restorable; `scripts/adb-env.sh reset` puts the device back):
`cmd uimode night yes|no` · `cmd locale set-app-locales <pkg> --locales pt-BR` (Android 13+, no root) ·
`settings put system font_scale 1.3` · `wm size 720x1280` + `wm density 320` · `exec-out screencap -p` ·
`exec-out uiautomator dump /dev/tty`. The detectors flag; a **human (or vision model) still looks at every
dark-mode and pt-BR screenshot** — a detector result is evidence, not proof.

## Release gate (definition of done)
Ship (even to a closed test) only when all are true; otherwise report what's missing:
- [ ] **Zero open P0 and P1.** (P1 may be accepted only by the owner, in writing, with a reason.)
- [ ] Scores ≥3 everywhere and **4** on Functional correctness, Data/sync/security, Appearance & theming,
      Localization & formatting.
- [ ] Clean checkout: types, lint, unit + integration tests green; release config checks pass.
- [ ] Every `FEATURES.md` row has status ✅ with evidence (test name or run id); none "not tested".
- [ ] Maestro suite green 3× in a row on the **release** build; two-account flows included.
- [ ] Matrix sweep complete (every screen × theme × locale × font × size), detectors clean or every flag
      triaged, contact sheet reviewed, logcat crash buffer empty.
- [ ] Locale conventions: table per shipped locale, every convention test green in Node **and** on the device (Hermes).
- [ ] Translation quality: research + glossary + tone guide per shipped locale; every string reviewed **in context on screenshots**; zero P0/P1 copy findings (wrong variant, wrong register, calque, untranslated, truncated, wrong plural/gender); a native speaker per locale signed off or is listed under "Untested".
- [ ] **Live E2E pass green on the release build installed from the Play test track** (real accounts, emails, DB checks, push, two devices, deletion) with cleanup verified → [reference/live-e2e.md](reference/live-e2e.md).
- [ ] Real low/mid Android phone: full main flow in **dark + pt-BR + font 1.3 + gesture nav**, and in
      light + en-US.
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
**End of pass:** dimension scores table, counts by severity, top 3 fixes, gate checklist ✅/❌, and an
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
5. Tester found the first three in minutes on one phone — the gate's "real mid-range Android, dark + pt-BR +
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
- Claiming the app is "100% bug-free". Report scores, evidence and what stayed untested instead.
