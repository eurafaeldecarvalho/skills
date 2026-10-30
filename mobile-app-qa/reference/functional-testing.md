# Functional correctness (dimensions 2 and 3)

Goal: **every feature works**, for every role, in every state, with correct data — proven by tests,
not by a glance. Appearance bugs make people uninstall; functional bugs make them distrust (and, in a
money/custody app, fight). Equal rigor.

## 1. Build the feature inventory from the code (pass 1)
You cannot test what you didn't list. Read the code, not the README. Recipes for an Expo/RN repo:
```bash
rg -n "name=\"|name: \"|createStackNavigator|Stack.Screen|Tabs.Screen" src app   # screens/routes
ls app/ 2>/dev/null                                                             # expo-router file routes
rg -n "onPress=|onLongPress=|onSubmitEditing=|onValueChange=" src | wc -l         # every interaction
rg -n "<TextInput|<Field|keyboardType=" src                                       # every input
rg -n "\.from\(\"|\.rpc\(|functions\.invoke|storage\.from" src                    # backend tables/RPC/storage
rg -n "requestPermissionsAsync|PermissionsAndroid|ImagePicker|Camera|Notifications" src
rg -n "Linking|getInitialURL|scheme|intentFilters" src app.json                  # deep links
rg -n "setInterval|AppState|BackgroundFetch|TaskManager|addNetworkStateListener" src  # background/timers
rg -n "export function .*Cents|reduce\(|Math\.round|toFixed" src/domain           # calculations
ls supabase/migrations supabase/functions 2>/dev/null                             # server logic, RLS
rg -n "t\(\"" src | wc -l                                                         # strings (for l10n)
```
Fill [../templates/FEATURES.md](../templates/FEATURES.md): one row per feature with ID, entry point,
roles, preconditions, happy path, edge cases, failure cases, oracle (expected result), test type
(unit / integration / Maestro / manual), test name, status, evidence. A feature = something a user can
start and finish (e.g. "Add expense with photo receipt", "Invite co-parent by link", "Export court PDF").
Also list **cross-cutting** behaviors: sync/outbox, offline banner, session refresh, notifications,
language/appearance settings, account deletion.

## 2. Design the cases (don't improvise)
For each row use the techniques that fit:
- **Equivalence partitions + boundary values:** amounts 0, 0.01, 0.99, 1, max, max+1, negative; split
  0/1/49/50/51/99/100 %; dates on month end, Feb 29, DST change, year end; text 0/1/max/max+1 chars, emoji,
  RTL char, leading/trailing spaces, HTML/SQL-looking text.
- **State transitions:** draw the states (e.g. expense requested → paid / disputed → resolved) and test
  every allowed transition **and** that forbidden ones are blocked (UI + server/RLS).
- **Decision tables** for rules with several conditions (who can edit what, when).
- **Pairwise** for configuration combinations you can't fully cross (OS version × theme × locale × font).
- **Error guessing** from the anti-pattern catalog and from past bugs.
- **Oracle first:** write the expected result (hand-computed numbers, exact strings per locale) before
  running. A test without an oracle is a demo.

## 3. The test pyramid for an Expo + Supabase app
| Layer | Tool | What goes here |
|---|---|---|
| Unit | Vitest/Jest (+ fast-check) | domain logic: money, splits, balances, schedules, permissions, parsers, formatters per locale, i18n parity |
| Component | @testing-library/react-native | a screen renders each state (loading/empty/error/data), validation messages, theme tokens, a11y labels |
| Integration | Vitest + Supabase (local `supabase start` or a disposable test project) | repository/outbox against real Postgres + **RLS** (two users' JWTs), edge functions, migrations |
| DB policy | `supabase test db` (pgTAP) | RLS: owner can, partner can within family, stranger cannot; storage policies |
| E2E | Maestro on the **release** APK | each inventory row's happy path + key failure paths, by `testID` |
| Exploratory | human/agent on a real phone | charters: "break expense entry in pt-BR with a Samsung keyboard", "two parents edit the same day offline" |

## 4. Maestro E2E rules (Android emulator or device)
- Install Maestro; flows live in the app repo under `.maestro/` (templates in
  [../templates/maestro/](../templates/maestro/)). Run: `maestro test .maestro/ --format junit --output qa/maestro.xml`.
- **Select by `id:` (RN `testID`)**; add `testID`s as part of the fix loop. Text selectors break in other
  locales — and this skill runs every flow in every locale.
- Deterministic state: `launchApp: { clearState: true }`, seeded test accounts per run (unique emails
  via `${RANDOM}`-style env or timestamp), never production data. Credentials via `-e` env, not committed.
- Waits, not sleeps: `extendedWaitUntil`, `assertVisible` with timeouts.
- Each flow asserts **outcomes** (the saved value and its formatted text, the balance after, the item in
  the list after app restart), not only that buttons were tappable.
- Network failure cases: run the write step with `adb shell cmd connectivity airplane-mode enable`
  (from a wrapper script) and assert the offline UI, then disable and assert sync + banner cleared.
- Flake check: whole suite 3× in a row green before the gate.

### Two-account (multi-user) flows
Shared-space features need two sessions:
1. Two emulators (`-port 5554/5556`) or emulator + phone; Maestro picks with `--device <serial>`.
2. Script: A creates family → A invites (capture link/code from the UI via `copyTextFrom`, or from the DB
   in a test env) → B signs up and accepts → B sees A's data → B edits → A sees it (pull-to-refresh or
   realtime) → permissions: B cannot do A-only actions → A removes B → B loses access (server-enforced).
3. Repeat the edit step with B offline, then both editing the same item → conflict rule observed.

## 5. Auth matrix (every app with accounts)
Sign-up (valid, existing email, weak password, typo'd email) · email confirmation link (opens app, cold
and warm; expired) · login (right, wrong password, unknown email, rate limit) · password reset round
trip · logout (local data cleared as designed) · session expiry/refresh after 1 h+ in background ·
reinstall → login → data back · delete account (in-app **and** web URL, data really deleted/anonymized) ·
OAuth providers if any (cancel mid-way).

## Data, sync and security
- Offline-first/outbox: create/edit/delete offline → kill → reopen → pending shown → online → synced
  exactly once → server state equals local. Repeat with server error 500 and with a validation error.
- Every degraded state (offline, sending, conflict, read-only) has: an entry condition, a visible UI, an
  **exit condition that is actually re-checked** (timer/backoff retry, foreground, network event), and a
  manual escape (retry/dismiss). Test: enter the state, remove the cause, wait ≤ the retry interval → UI clears.
- Never classify every exception as "offline": a 4xx/5xx or timeout is not a network loss.
- Supabase RLS: for each table, tests for owner / family member / other family / anonymous × select /
  insert / update / delete. Storage: private buckets, path includes family id, signed URL expiry.
- Local storage migrations across versions: install the previous release AAB, create data, install the
  new one over it (`adb install -r`), data intact and migrated.
- Calculations: unit tests with hand-computed oracle tables **and** invariants (property tests): balances
  sum to zero across parents, split rounding never loses/creates a cent, recurring schedules produce the
  same days in every timezone.

## 7. Paywalls / purchases (if present)
License testers on the test track (no real charge) · purchase, cancel, restore, upgrade/downgrade,
grace period, refund/revoke → entitlement removed · reinstall/new device restore · offline at launch with
an active entitlement. Any real purchase needs the owner's approval.

## 8. Notifications
Permission prompt on Android 13+ at a sensible moment · denied → in-app explanation + link to settings ·
token registered per device/user, removed on logout · each notification type: content localized in the
**recipient's** language, tap opens the right screen (cold, warm, logged out) · no duplicates on reinstall.

## 9. Status per feature
`✅ verified` (evidence: test names / run id / device) · `⚠️ known issue` (bug id) · `❌ failing` ·
`⏳ not tested` (must be zero at the gate). Scoring dimension 2: 4 = every row ✅ with automated
coverage of every happy path and every money/permission rule; 3 = all ✅ but some manual-only; 2 = gaps.
