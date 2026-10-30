# Red-team pass (pass 6b — mandatory in EVERY loop iteration)

Mindset: you are **not** the tester who confirms the app works; you are a hostile user, a careless
user, a co-parent with a grudge, an attacker holding a valid account and the APK, and a phone that
misbehaves. Your job is to **make the app fail**. Every attempt that succeeds (crash, wrong data, data
of another space, stuck UI, leaked PII, bypassed rule) is a finding and feeds the convergence loop
([convergence-loop.md](convergence-loop.md)). Every attempt that fails is logged too (it becomes the
regression suite of the next iteration).

## Rules of engagement (non-negotiable)
- Only against **your own** app, on the **staging/production-like** backend, with **tagged QA accounts**
  (`qa+<run>-a@…`, `-b`, `-c`). Never real users' data; never someone else's service.
- Bounded load: rate-limit probes use small bursts (e.g. 20–50 requests) — this is a check, not a DoS.
- Secrets (service-role key, DB URL, test passwords, JWTs) come from env / secret store, are never
  echoed, never committed, never pasted into reports; tokens in evidence are truncated (`eyJ…last6`).
- Chaos runs (monkey) only on an emulator or a dedicated test phone signed into QA accounts — monkey taps
  anything, including system toggles.
- Each iteration uses a **new seed** and a **new adversarial corpus slice**; record seeds so any failure
  replays exactly.

## A. Chaos & robustness (the app must survive)
| # | Attack | How | Pass condition |
|---|---|---|---|
| C1 | Monkey | `scripts/red-team-chaos.sh monkey` → `adb shell monkey -p <pkg> -s <seed> --throttle 80 --pct-syskeys 0 -v 20000` ×3 seeds | no `// CRASH`, no ANR, `logcat -b crash` empty; app still usable after |
| C2 | Random input fuzz | Maestro [`red-team-inputs.yaml`](../templates/maestro/flows/red-team-inputs.yaml) (`inputRandomText`, corpus strings) on every text/money/date field | validation message or correct save; never crash, never raw error, never silently corrupted value |
| C3 | Adversarial corpus | emoji/ZWJ (`👨‍👩‍👧`), RTL (`مرحبا`) + bidi override (`\u202E`), combining accents, 10 000 chars, only spaces, leading/trailing spaces, newline, `<b>x</b>`, `<script>alert(1)</script>`, `'); drop table x;--`, `%s %n {0} {{x}}`, `../../etc`, null-ish (`null`, `undefined`, `NaN`) | stored and rendered literally (escaped), length limits enforced server-side too, layout intact |
| C4 | Money abuse | `0`, `-1`, `-0`, `0,001`, `1,999`, `1.234,56` and `1,234.56` in both locales, `999999999999`, `1e9`, `∞`, paste with `R$`, Arabic-Indic digits, split 0 %/100 %/101 %/33,33 %×3 | rejected or normalized; integer cents; splits sum exactly to total; DB `check` constraints reject what the UI misses |
| C5 | Dates | 1900-01-01, 2100-12-31, 29 Feb (2028 and 2027), DST gap/overlap days in the user's zone, year boundary, device clock set ±2 years, timezone change while open (`red-team-chaos.sh clock`) | correct day shown everywhere; schedules not shifted; no negative durations |
| C6 | Rapid / double input | double/triple tap submit, tap two buttons at once, back spam (`input keyevent 4` ×20), swipe during transition | exactly one write, no duplicate navigation, no crash |
| C7 | Lifecycle mid-action | kill mid-write (`am kill` / `am force-stop` right after submit), airplane mode mid-request, `pm clear` and relaunch, Don't-keep-activities, rotate, split/freeform window, theme/language/font change while a form is dirty | no lost or double write; state restored or explicit discard; outbox resumes |
| C8 | Resource pressure | `am send-trim-memory <pkg> RUNNING_CRITICAL` (foreground) / `COMPLETE` (background); low storage (`cmd devicestoragemonitor force-low`, or fill `/sdcard` on the emulator); battery saver | graceful messages; no corrupted local DB; cache trimmed not data |
| C9 | Permissions mid-flow | `pm revoke <pkg> android.permission.CAMERA` (Android kills the process) during upload; deny forever; notifications off | app restores, explains, offers Settings |
| C10 | Extremes of display | font scale 2.0 + display size max (`wm density` largest) + small screen + RTL pseudo-locale (`ar-XB`) + long-text pseudo-locale (`en-XA`) | no clipped/overlapping/unreachable control |
| C11 | Concurrency | A and B edit the **same** record at the same time (two devices, Maestro `--device`), both offline then online, delete vs edit race | documented conflict rule applied, no silent loss, no duplicate, both converge to same state |
| C12 | Session | access token expired (staging JWT expiry set low, or wait it out), refresh token revoked (sign out other sessions), password changed on device B | silent refresh or clean re-login, queued writes not lost, no infinite loop |

## B. Security & abuse (a valid user tries to go where they shouldn't)
Use [`scripts/rls-probe.sh`](../scripts/rls-probe.sh) with three accounts: A (owner of space S_A), B (co-parent
in S_A, owner of S_B), C (stranger). Tokens obtained by signing in the QA accounts; never service role.

| # | Attack | How | Pass condition (P0 if it fails) |
|---|---|---|---|
| S1 | IDOR / RLS read | C (and B for S_B-only data) `GET /rest/v1/<table>?select=*` and `?<space_col>=eq.<S_A>`; embedded selects (`select=*,other(*)`); `Prefer: count=exact` HEAD; views | zero rows of spaces you don't belong to, counts too |
| S2 | RLS write | C inserts with `<space_col>=S_A`; updates/deletes A's row ids; upsert with a foreign id | rejected (401/403/RLS error) or 0 rows affected; verify by SQL that nothing changed |
| S3 | Privilege escalation between co-parents | B PATCHes own membership `role`→owner, removes A, edits A-only fields, changes `created_by`, re-assigns ownership | rejected; roles only changed through audited server function |
| S4 | Invite abuse | reuse a consumed/revoked/expired code; accept an invite addressed to another email; brute-force short codes (bounded); invite yourself into a space; invite link with forged `space_id` | rejected; codes long/random/single-use/expiring; attempts rate-limited |
| S5 | Functions & RPC | list `SECURITY DEFINER` functions (`select proname from pg_proc where prosecdef and pronamespace='public'::regnamespace`) and call each as C with A's ids; Edge Functions without/with wrong JWT | every function checks `auth.uid()` membership; `search_path` pinned |
| S6 | Storage | C downloads/lists/overwrites A's objects (`/storage/v1/object/<bucket>/<path>`, `/object/list`); guessable paths; signed URL after expiry | denied; private buckets; paths not guessable |
| S7 | Realtime | C subscribes to S_A channel/table changes | receives nothing |
| S8 | Tampered requests | replay the app's own request with altered amounts, split, `user_id`, `created_at`, `is_paid`, extra columns | server/DB constraints and RLS `with check` reject; server recomputes derived values |
| S9 | Injection | PostgREST filter injection where user text reaches `.or()`/`.filter()` strings (grep template literals in queries); HTML in display names → invite emails/push; markdown/links in notes | parameterized; escaped in email/push; no clickable injected links |
| S10 | Auth flows | sign-up spam/reset spam for one address (bounded), email enumeration (different message for existing email), weak password accepted, open redirect in `redirect_to`, magic-link reuse, login after account deletion | rate-limited; generic messages; allow-listed redirects; deleted = gone |
| S11 | Deep-link injection | `adb shell am start -W -a android.intent.action.VIEW -d '<scheme>://invite?code=x&space=<S_A>'`, `…?next=https://evil.example`, path traversal, huge params, logged-out | validated server-side; no open redirect; no action without confirmation |
| S12 | APK inspection | `unzip -p app.apk assets/index.android.bundle \| grep -aoE 'service_role|sk_live|-----BEGIN|AIza[0-9A-Za-z_-]{35}'` (report names only); manifest: exported components, `allowBackup`, `usesCleartextTraffic`, debuggable | only public keys; nothing exported unintentionally; no cleartext; not debuggable |
| S13 | PII & logs | run the full flow with distinctive QA values, then `adb logcat -d \| grep -iE '<qa email>|<qa name>|eyJ'`, crash-reporter breadcrumbs, analytics events, URLs/query strings | no emails, names, amounts tied to people or tokens in logs/analytics |
| S14 | Consent & privacy | fresh install, decline analytics/crash consent (if offered) → observe network (`adb logcat`, proxy on a debug build with user CA, or SDK debug logs) | no analytics/ads/crash SDK traffic before consent where consent is required; Data safety matches |
| S15 | Local data at rest | `adb backup`/`run-as` (debug) to inspect AsyncStorage/SQLite; logout then inspect | tokens in SecureStore/Keystore, not AsyncStorage; logout wipes user data; other user on the same phone sees nothing |
| S16 | Deleted / removed member | remove B from S_A, then B's cached app and B's token try to read/write S_A; deleted account token | access lost immediately server-side; client clears cache |

## Output
`qa/red-team/<iteration>/` with `seeds.txt`, `attempts.md` (attack → result → evidence), monkey logs, probe
results (tokens truncated). Successful attacks → findings (security ones default **P0**; chaos crashes
**P0**; wrong/duplicated data **P0**; stuck/ugly-but-recoverable **P1–P2**). Unsuccessful attacks stay in
the suite and are re-run every iteration.

Sources: OWASP MASVS/MASTG (https://mas.owasp.org/), Supabase RLS docs
(https://supabase.com/docs/guides/database/postgres/row-level-security), Android UI/Application Exerciser
Monkey (https://developer.android.com/studio/test/other-testing-tools/monkey), Maestro random input
commands (https://docs.maestro.dev/).
