# Live end-to-end pass (pass 3b — mandatory before the gate)

Mocks and local Supabase prove the code; only a **live** run proves the product: real accounts, real
emails in real inboxes, real push on a device, real rows in the real (production-like) database, real
store build. "Saiu dos testes 100% pronto" means this pass is green.

## Ground rules
- **Environment:** a production-like project (same Supabase plan/config, same auth email provider, same
  FCM project, same storage policies and edge functions) or production itself **only** with tagged QA
  accounts. Write down which one in `qa/APP-QA.md`.
- **Tagged accounts only:** `qa+<run-id>-a@<your-domain>` / `qa+<run-id>-b@…` (plus-addressing on an inbox
  the team controls — e.g. the bot's own agent inbox or a dedicated QA mailbox), display names prefixed
  `QA <run-id>`, families/spaces named `QA <run-id>`. `run-id` = `YYYYMMDD-HHMM`.
- **Never touch real users' data:** every SQL query filters by the run's tagged user ids; no updates or
  deletes without `where email like 'qa+<run-id>%'` (or ids gathered from them); read-only checks on
  everything else.
- **Secrets never printed or committed:** service-role key, DB URL, FCM server credentials and test
  passwords come from env/secret store; scripts don't `echo` them; logs and screenshots are checked for
  tokens before attaching to reports. Prefer the least-privileged credential that can do the check.
- **Release build from the Play test track** (internal/closed) for the gating run; the same flows may run
  earlier on a local release APK.
- **Cleanup step is part of the pass** (below) and is verified, not assumed.
- Billing only in **test mode** (Play license testers / test cards) — any real charge needs the owner.

## Flows (each: steps → what to verify where → evidence)
| # | Flow | Verify in the app | Verify outside the app |
|---|---|---|---|
| L1 | Sign-up A with a real address | onboarding reached | confirmation email **arrives** in the inbox within N min (not spam: check spam/promotions), sender name/subject/body localized for the user's language, link opens the app (cold + warm, App Links verified: `adb shell pm get-app-links <pkg>`) and confirms; `auth.users` row exists, `email_confirmed_at` set; SPF/DKIM/DMARC pass in the message headers (`Authentication-Results`) |
| L2 | Login / wrong password / logout | right messages | auth logs show attempts; no session left after logout |
| L3 | Password reset round trip | new password works, old doesn't | reset email arrives, link expires after use/time, localized |
| L4 | Email change (if offered) | | both old/new addresses notified as designed |
| L5 | Core data writes (every FEATURES row that writes) | values displayed, formatted per locale | **the row in the DB** has the exact values (cents, timestamps in UTC, foreign keys, `created_by`), via Supabase SQL editor/`psql` read-only query filtered by QA ids |
| L6 | Two accounts, two devices: invite + join | B sees A's space | membership row; invite consumed; email/SMS/link invite actually delivered if the app sends one |
| L7 | RLS isolation | B cannot see A's other spaces; a third account C sees nothing | as C's JWT, `select` on each table returns 0 rows of A/B; writes rejected (try with the REST API using C's access token) |
| L8 | Realtime / sync between devices | A edits → B updates within N s (foreground), after resume (background) | single row, no duplicates; conflict rule observed when both edit offline |
| L9 | File upload/download (receipts, photos, exports) | thumbnail, open, share | object exists at the right private path; signed URL expires; other family cannot fetch it |
| L10 | Push notifications via FCM on a real device **and** an emulator with Google Play services | delivered in **foreground** (in-app UI), **background** and **killed**; tap opens the right screen; text in the recipient's language; channel/importance right; no duplicates | token row per device/user; token removed on logout; delivery logged by the sender (edge function/FCM response) |
| L11 | Scheduled/transactional emails & notifications (reminders, digests) | | arrive at the right local time for each user's timezone |
| L12 | Billing (if any) with license testers | entitlement granted, restored after reinstall, revoked after refund/cancel | Play Console order (test), server entitlement row |
| L13 | Account & data deletion (Play requirement) | in-app path works; signed out | user row + personal data deleted/anonymized in DB and storage; web deletion URL from the listing works; shared-space data handled as documented for the other parent |
| L14 | Upgrade path | previous production version → update via Play | data intact, migrations applied once |

## Tools
- Inbox: the bot's own email inbox (search by `qa+<run-id>`) or a QA mailbox via API; read raw headers
  for SPF/DKIM/DMARC; record arrival latency.
- DB: Supabase SQL editor or `psql "$QA_DB_URL"` with read-only role for checks; RLS checks with real user
  JWTs through the REST API (`apikey` = anon key, `Authorization: Bearer <user access token>`), or
  pgTAP in a staging copy.
- Push: two devices (real phone + emulator image with Google Play), app in fg/bg/killed
  (`adb shell am force-stop` for killed — note force-stopped apps on Android don't receive FCM until
  opened again; use swipe-away from recents for the "killed" case), screenshots of the shade
  (`adb shell cmd statusbar expand-notifications`), `adb shell dumpsys notification --noredact | grep <pkg>`.
- Maestro for the in-app parts (`two-account-invite.yaml` on `--device` A and B), screenshots as evidence.

## Cleanup (mandatory, verified)
1. Delete QA accounts through the **app's own deletion flow** (this also tests L13).
2. Remove leftovers with a reviewed script restricted to the run's ids (spaces, storage objects, push
   tokens, invites) — dry-run first, print counts only.
3. Verify zero rows/objects left for `qa+<run-id>`; archive QA emails.
4. Note in the report what was created and removed.

## Gate
Every L-flow that applies passes on the **release build installed from the Play test track**, on a real
phone + a second device for multi-user flows, with evidence (screenshots, email headers, query results
without secrets/PII), and cleanup verified. Any failure is P0 (auth, data, deletion, isolation, billing)
or P1 (delivery delays, localization of emails/push, deep link fallbacks).
