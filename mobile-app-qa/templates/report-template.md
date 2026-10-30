# QA report — <app> <version/build> — <date>

**Gate: PASS / FAIL** · Evidence source: real device(s) <models> / emulator <AVD> · Build: release <hash>

## Scores (0–4)
| # | Dimension | Score | Notes |
|---|---|---|---|
| 1 | Build & release config | | |
| 2 | Functional correctness (must be 4) | | |
| 3 | Data, sync & security (must be 4) | | |
| 4 | Appearance & theming (must be 4) | | |
| 5 | Localization & formatting incl. conventions + translation quality (must be 4) | | |
| 6 | Layout & adaptivity | | |
| 7 | Accessibility | | |
| 8 | Resilience & lifecycle | | |
| 9 | Performance & stability | | |
| 10 | Store & compliance | | |
| 11 | Feedback loop | | |

## Findings
| ID | Sev | Dimension | Where (screen, config) | What happened / expected | Root cause | Fix (commit) | Regression test | Re-verified in |
|---|---|---|---|---|---|---|---|---|

## Coverage
FEATURES.md: __ ✅ / __ ⚠️ / __ ❌ / __ ⏳ · Maestro: __ flows, 3× green? · Sweep: __ configs × __ screens,
flags triaged? · Locales reviewed in context by: …

**Untested:** (be explicit — e.g. "iOS", "native pt-PT review", "Xiaomi battery killer")

---

# Tester bug template (send to testers)
- Phone model + Android version: (Settings → About phone)
- Theme: light / dark · App language: · Phone language/region:
- Font size / display size changed? · Navigation: gestures / 3 buttons
- App version (Settings → About in the app):
- What I did (steps):
- What I expected:
- What happened (screenshot or screen recording please):
- Happens always / sometimes / once:
