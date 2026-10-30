# FEATURES.md — feature inventory (built from the code; one row per user-completable feature)

Status: ✅ verified · ⚠️ known issue · ❌ failing · ⏳ not tested (must be zero at the gate)

| ID | Feature | Entry point (screen/route) | Roles | Preconditions | Happy path → oracle | Edge cases | Failure cases | Tests (unit / integ / Maestro / manual) | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| AUTH-1 | Sign up with email | `/signup` | anon | none | account created, confirm mail, lands on onboarding | existing email, weak pw, uppercase email | offline, server 500, rate limit | `auth.test.ts`, `.maestro/flows/signup.yaml` | ⏳ | |
| MONEY-1 | Add expense | Expenses → + | parent | in a family | `1234,56` in pt-BR → saved 123456 cents, shows `R$ 1.234,56` everywhere | 0, 0,01, max, comma/dot, 0 % / 100 % split | offline (queued), validation | `money.test.ts`, `money-input-ptbr.yaml` | ⏳ | |
| SHARE-1 | Invite co-parent | Settings → Family | owner | family exists | B accepts, both see same data | expired code, already member | B offline, revoked | `two-account-invite.yaml` (2 devices), RLS tests | ⏳ | |

## Cross-cutting
| ID | Behavior | Oracle | Tests | Status | Evidence |
|---|---|---|---|---|---|
| X-SYNC | Outbox/offline sync | exactly-once, banner clears ≤ retry interval | | ⏳ | |
| X-L10N | Language switch | every string + format changes live | | ⏳ | |
| X-THEME | Theme switch | all screens correct, live | | ⏳ | |
| X-NOTIF | Push notifications | localized for recipient, opens right screen | | ⏳ | |
| X-DELETE | Account deletion | data gone, web URL works | | ⏳ | |
