# QA report — <experience> — <YYYY-MM-DD>
Build: `<git sha>` · Place version: `<n or "not published">` · Skill: roblox-game-qa · Agent: <name>
Machine slot: <schedule row> · RAM at start: <MB available> · Evidence folder: `qa/<date>/`

## Dimension scores (0–4)
| Dimension | Score | Evidence source | Note |
|---|---|---|---|
| 1 Build & reproducibility | | verify.sh | |
| 2 Devices & UI | | ui-audit + Device Emulator / real phone | |
| 3 Input parity | | | |
| 4 World interaction | | | |
| 5 Flow & onboarding | | | |
| 6 Multiplayer & server | | | |
| 7 Visual & audio | | | |
| 8 Performance | | | |
| 9 Safety & compliance | | | |
| 10 Publishing | | | |
| 11 Feedback loop | | | |
| 12 Accessibility & localization | | | |

## Iteration ledger (convergence loop)
| Iter | Build | Seeds | P0 | P1 | P2 | P3 | Weighted (8·P0+4·P1+2·P2+P3) | Fixed | New | Regressions | Blocked | Clean streak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | | | | 0 |

## Findings
| ID | Sev (original → current) | Found in iter | Dimension | Config | Root cause | Fix commit | Regression test | Re-verified in (iter, source) | Status |
|---|---|---|---|---|---|---|---|---|---|
<!-- Config = build sha · place version · viewport/preset · input · players · language · source (Lune / fake server /
     MCP play / Clients&Servers / Device Emulator / real device / real players). Status: open / fixed / verified / Blocked -->

## Red-team
| Row | Attack | Seed(s) | Attempts | Successes | Finding |
|---|---|---|---|---|---|

## FINAL PASS (published build)
| Check | Result | Evidence |
|---|---|---|
| Built from clean commit `<sha>`; verify.sh green | | |
| Published to the existing place (private/playtest access), place version `<n>` | | |
| Join on real server: Output/F9 clean (output-scan) | | |
| Data written by the previous version loads | | |
| Real phone loop | | |
| 2 real players loop | | |
| Rollback version noted | | |

## Release gate
(copy the gate from SKILL.md with ✅ / ❌ / Blocked)

## Coverage
Features ✅ __/__ · ⏳ __ · Blocked __ · viewports __ · locales __ · inputs __ · player counts __
**Untested:** <devices, inputs, player counts, languages, flows — and why (no slot / no device / no people)>

## Top 3 next
1. 
