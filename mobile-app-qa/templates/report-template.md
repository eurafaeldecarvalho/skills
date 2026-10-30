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
| 12 | Security & abuse resistance — red-team (must be 4) | | |

## Convergence loop — iteration ledger
| Iter | Build | Seeds (monkey / fuzz) | P0 | P1 | P2 | P3 | Total | Fixed since last | New | Regressions | Blocked | Clean streak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | — | | — | | 0 |

Exit: two consecutive full iterations with Total = 0 (second with fresh seeds) · Escalated? (reason) ·
Owner-accepted items (listed, not counted as zero):

## FINAL PASS (signed release APK on clean emulators)
| Profile | Android | Fresh install | Update over prev | Walkthrough | Live | Maestro | Sweep | Red-team quick | logscan (crash/ANR/err) | gfxinfo janky % | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mid-range 1080×2400 | 14 | | | | | | | | | | `qa/final/…` |
| mid-range 1080×2400 | 15/16 | | | | | | | | | | |
| small screen | 14 | | | | | | | | | | |
| Real phone (Play closed track) | | | | | | | | | | | |
APK SHA-256 (new / previous): · versionCode: · signing cert SHA-256:

## Red-team (last iteration)
| Attack | Attempts | Succeeded (→ finding ID) | Evidence |
|---|---|---|---|
| Chaos C1–C12 | | | `qa/red-team/<iter>/` |
| Security S1–S16 (accounts A/B/C) | | | probe logs (tokens truncated) |

## Findings
| ID | Sev (original→current) | Found in iter | Dimension | Where (screen, config incl. nav mode) | What happened / expected | Root cause | Fix (commit) | Regression test | Re-verified in |
|---|---|---|---|---|---|---|---|---|---|

## Coverage
FEATURES.md: __ ✅ / __ ⚠️ / __ ❌ / __ ⏳ · Maestro: __ flows, 3× green? · Sweep: __ configs × __ screens,
flags triaged? · Locales reviewed in context by: …

**Untested:** (be explicit — e.g. "iOS", "native pt-PT review", "Xiaomi battery killer")

---

# Tester bug template (send to testers)
- Phone model + Android version: (Settings → About phone)
- Theme: light / dark · App language: · Phone language/region:
- Font size / display size changed? · Navigation: gestures / 3 buttons (Settings → System → Gestures/Navigation)
- Anything covered by the phone's bottom bar or notch? (screenshot please)
- App version (Settings → About in the app):
- What I did (steps):
- What I expected:
- What happened (screenshot or screen recording please):
- Happens always / sometimes / once:
