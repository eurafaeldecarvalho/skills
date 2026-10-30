# Red-team pass (every iteration, with recorded seeds)

Assume a hostile client: any LocalScript can fire any remote with any arguments, at any rate, in any state.
The red-team runs **every iteration** (not once), with new seeds each time, and every success is P0 by default
(P1 only if it affects nobody but the attacker and nothing persists). Prefer the headless **fake server**
(build-and-tests.md) so it costs no Studio slot; confirm the worst rows once in a real play session.

| Row | Attack | How (fake server / MCP client probe) | Pass when |
|---|---|---|---|
| R01 | Wrong types | every remote × {nil, number, string, table, Instance, Vector3, NaN, ±inf, -0} per argument | no error in server Output, state unchanged |
| R02 | Rate | 60/s for 2 s per remote, per player | ≤ the documented rate gets through; other players unaffected |
| R03 | Out-of-state | fire each remote in every game state (lobby, countdown, round, end) | ignored outside the states that allow it |
| R04 | Ownership | act on another player's object/slot/station/team id | rejected |
| R05 | Distance / LOS | trigger world actions from far away or through walls | rejected (server checks distance) |
| R06 | Size | 100 kB strings, deep/huge tables, 10k-element arrays | rejected cheaply, no lag spike |
| R07 | Join/leave storm | join/leave/rejoin N players in random order at random moments (seeded) | no stuck state, no orphaned data, no error |
| R08 | Leave at the worst time | the host / last player / the one holding an item leaves mid-action | game continues or resets cleanly |
| R09 | Data | DataStore errors/throttle injected; two servers writing the same key; shutdown during save | no data loss; retries; session lock |
| R10 | Teleport / LaunchData | forged TeleportData / join data, failed teleports | treated as untrusted; failures handled |
| R11 | Economy | buy/sell/claim twice concurrently, negative/huge quantities, reward farming loop | balance never wrong, no infinite source |
| R12 | Monkey | seeded random sequence of legal + illegal actions for N minutes per player | no error, invariants hold (score ≥ 0, one role per player, timers end) |

Rules:
- Record seeds in the ledger and in `qa/<date>/red-team/seeds.txt`; a failing seed becomes a permanent regression test.
- Remotes list comes from code (`rg -n 'OnServerEvent|OnServerInvoke' src`), not memory; a new remote adds rows.
- Never run attacks against a public live server or other people's games; use the fake server, Studio, or a
  private place. Exploit tooling from the internet is out of scope.
