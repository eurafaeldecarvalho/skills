# FEATURES.md — feature inventory (built from the code; one row per user-completable feature)

Status: ✅ verified · ⚠️ known issue · ❌ failing · ⏳ not tested (must be zero at the gate)

| ID | Feature | Entry point (screen/route) | Roles | Preconditions | Happy path → oracle | Edge cases | Failure cases | Red-team / abuse cases | Tests (unit / integ / Maestro / probe / manual) | Live | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AUTH-1 | Sign up with email | `/signup` | anon | none | account created, confirm mail, lands on onboarding | existing email, weak pw, uppercase email | offline, server 500, rate limit | signup spam, enumeration, open redirect | `auth.test.ts`, `.maestro/flows/signup.yaml` | L1 | ⏳ | |
| MONEY-1 | Add expense | Expenses → + | parent | in a family | `1234,56` in pt-BR → saved 123456 cents, shows `R$ 1.234,56` everywhere | 0, 0,01, max, comma/dot, 0 % / 100 % split | offline (queued), validation | -1, 1e9, tampered amount/split via API, double submit | `money.test.ts`, `money-input-ptbr.yaml`, `red-team-inputs.yaml` | L5 | ⏳ | |
| SHARE-1 | Invite co-parent | Settings → Family | owner | family exists | B accepts, both see same data | expired code, already member | B offline, revoked | code reuse/brute force, forged space id, B escalates role | `two-account-invite.yaml` (2 devices), RLS tests, `rls-probe.sh` | L6–L7 | ⏳ | |

## Cross-cutting
| ID | Behavior | Oracle | Tests | Status | Evidence |
|---|---|---|---|---|---|
| X-SYNC | Outbox/offline sync | exactly-once, banner clears ≤ retry interval | | ⏳ | |
| X-L10N | Language switch | every string + format changes live | | ⏳ | |
| X-THEME | Theme switch | all screens correct, live | | ⏳ | |
| X-NOTIF | Push notifications | localized for recipient, opens right screen | | ⏳ | |
| X-DELETE | Account deletion | data gone, web URL works | | ⏳ | |
| X-INSETS | System bars | nothing under nav bar (3-button + gesture) or status bar, every screen | sweep `nav-overlap` | ⏳ | |
| X-UPGRADE | Update over previous release | data + session kept, migrations once, outbox flushed | | ⏳ | |
| X-SEC | RLS / roles / storage / realtime / RPC | stranger and co-parent can't exceed their rights | `rls-probe.sh`, red-team S1–S16 | ⏳ | |
| X-PII | Logs, analytics, consent | no PII/tokens; no tracking before consent | red-team S13–S14 | ⏳ | |
| X-TIME | Clock / timezone / DST | same day for every user, schedules intact | | ⏳ | |
