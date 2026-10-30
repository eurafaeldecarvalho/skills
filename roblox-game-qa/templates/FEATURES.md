# FEATURES.md — inventory of everything the player can do or see
<!-- Pass 1. Build it from the CODE (remotes, ProximityPrompts, buttons, states, screens), not from memory:
  rg -n 'OnServerEvent|OnServerInvoke' src      # every remote handler
  rg -n 'ProximityPrompt|ClickDetector' src     # world interactions
  rg -n 'Activated|MouseButton1Click' src       # UI actions
  rg -n 'Estado|State|Phase' src/shared         # game states / screens
Every row needs an oracle (how we know it worked). Status ⏳ = not yet verified. The gate needs ⏳ = 0
(or the row marked Blocked with the reason — Blocked never counts as passed). -->

| ID | Feature / action / screen | Oracle (expected result) | Inputs (touch/KBM/pad) | Edge cases | Failure cases | Red-team row | Test (file / manual check) | Evidence source | Status |
|---|---|---|---|---|---|---|---|---|---|
| F01 | Join → lobby | Lobby UI visible ≤ 5 s, no Output errors | — | late joiner, full server | DataStore down | R07 | tests/flow.spec | Lune fake server | ⏳ |
| F02 | Pick role | Server assigns, both clients see it | ✅/✅/⏳ | both pick same role | spam 60/s | R02 | tests/limit.spec | MCP play | ⏳ |

## Cross-cutting rows (always present)
| ID | Concern | Oracle | Status |
|---|---|---|---|
| X01 | Full loop 3× without leak or stuck state | instances back to baseline; no overlay without auto-exit | ⏳ |
| X02 | Every overlay has an automatic exit | timer/state change hides it without input | ⏳ |
| X03 | Every remote validates type/range/state + rate limit | red-team R01–R05 green | ⏳ |
| X04 | Data saves on leave, shutdown (BindToClose) and teleport | fake-server + Studio check | ⏳ |
| X05 | Release flags in release state | verify.sh flag grep + Config test | ⏳ |
| X06 | Every text in every shipped language fits | locale × viewport sweep | ⏳ |
| X07 | Accessibility: no meaning by color/sound alone; reduced motion respected | accessibility.md checklist | ⏳ |
