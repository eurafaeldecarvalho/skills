# Build & reproducibility (dimension 1)

Goal: anyone (or any agent) can rebuild the exact published place from git and get the same result, and
the cheap checks catch bugs before a human has to play.

## Build
- `rojo build default.project.json -o build.rbxl` from a clean clone. Fail the pass on any warning about
  unknown files, duplicate names or paths that map nowhere.
- During development use `rojo serve` + the Studio plugin. Before publishing, either publish from a
  freshly built file or confirm Studio is synced and has no unsaved Studio-only edits.
- Things that live only in Studio (terrain, lighting tweaks, hand-placed models) must be exported back
  (`.rbxm`/`.rbxmx` in the repo, or a documented "Studio-owned" list in `GAME.md` / `qa/GAME-QA.md`). Unknown drift = P1.

## Static checks
- `luau-lsp analyze --definitions=<roblox defs> src/` (or Studio ▸ Script Analysis): zero errors.
- `selene src/` with the `roblox` std; `stylua --check src/`.
- Prefer `--!strict` in new modules; at minimum `--!nonstrict` with typed public functions.
- Look for: shadowed globals, deprecated APIs (`wait`, `spawn`, `delay` → `task.*`), `:connect` lowercase,
  missing `:Disconnect()` on per-round connections.

## Unit tests and simulations (Lune)
- Keep game rules in **pure ModuleScripts** that don't touch `game`/services (scoring, recipe/order
  generation, economy, difficulty tables, timers math). Inject services where needed.
- Run them with Lune (`lune run tests`) in CI or before every publish. Typical tests: score never
  negative; economy can't go infinite; each level is winnable; timers end; random seeds reproducible.
- **Difficulty simulation:** run N thousand simulated sessions with bot policies (weak / average /
  strong, solo and N players) and print win rate, average score and time per level. Flag levels where
  weak bots win <20% early on or strong bots never fail late (tune numbers to the game's intent).
- A bug that a tester found gets a test here whenever the logic is pure (see feedback-loop.md).

## Fake server in Lune (multiplayer without Studio)
Pure-module tests can't see the server scripts that wire everything together, and a small shared box can't run
2+ Studio clients. The fix is a **fake server**: a Lune module that loads the REAL server scripts
(`src/server/**`) with `@lune/luau`, on a fake DataModel with:
- a **virtual clock** (`advance(seconds)` steps `task.wait`/`task.delay`/Heartbeat in fixed ticks);
- **fake Players** (`join(userId)`, `leave(p)`, `Kick`), fake `RemoteEvent`s that record what each client
  received (`last(p, "State")`) and let the test fire remotes as a client (`remote(p, "Ready", ...)`);
- payloads deep-copied on every remote (Roblox serializes them; shared tables would hide bugs);
- stubs only for visual/platform services (tweens, NPC rigs, analytics, badges), each stub listed at the top.
Then a spec drives scenarios: 2 players play a round; partner leaves mid-round; late joiner; last player leaves;
spam; DataStore failure; seeded join/leave storm (red-team.md). **Mutation check** once: break one server line
on purpose and see the spec fail — proof it runs the real code. See case-turno.md for a real one (~300 lines).

## Scripts in this skill
| Script | What it does |
|---|---|
| [`scripts/verify.sh`](../scripts/verify.sh) | Headless chain: luau-compile every file → `rojo build` (warnings are findings) → `luau-lsp analyze` (sourcemap + Roblox defs) → `selene` → `stylua --check` → debug-flag grep + print/warn count → Lune suite × `FLAKE` (flake = finding). `STATIC=required` fails when a tool is missing. Logs to `$OUT`. |
| [`scripts/output-scan.py`](../scripts/output-scan.py) | Classifies an Output / F9 / studio-mcp log: script errors P0; infinite yield, asset/DataStore/HTTP/remote failures P1; deprecations/warnings P2. `--allow REGEX` for documented noise, `--json` for the report; exit 1 on P0/P1. |
| [`scripts/studio-mcp.py`](../scripts/studio-mcp.py) | Small stdio client for Studio's MCP server: list tools, run Luau in edit mode, run a server script in play mode, inject/remove a temporary client probe (`run-pair` always removes it). Saves the raw result to `--out`. Never saves the place. |
| [`scripts/qa-collect.server.luau`](../scripts/qa-collect.server.luau) | Server half of a play probe: creates `ReplicatedStorage.QA_Channel`, prints every client report as `[qa] TAG json`, waits for the expected reports. |
| [`scripts/ui-audit.client.luau`](../scripts/ui-audit.client.luau) | Client probe: walks visible GUI and reports safe-area, off-screen, small text (real px), small targets, thumbstick/jump zone, overlaps, hidden modals, invisible blockers, emoji glyphs, keyboard hints on touch. |
| [`scripts/box-preflight.sh`](../scripts/box-preflight.sh) | Shared-machine RAM/process pre-flight and watchdog (shared-box.md). |

Typical play check (inside a booked slot):
```
python3 scripts/studio-mcp.py run-pair scripts/ui-audit.client.luau scripts/qa-collect.server.luau --out qa/<date>/ui-<preset>.json
python3 scripts/output-scan.py qa/<date>/ui-<preset>.json --json qa/<date>/scan-<preset>.json
```
The MCP tool names differ between Studio's built-in server and community servers; run `studio-mcp.py tools` first
and pass `--run-tool/--play-tool` if needed. The probes were validated against a stub MCP server and the Luau
compiler; validate them once on your Studio before trusting a clean result (a probe that reports nothing is not "clean").

## Studio checks
- Start Play and *Test ▸ Clients and Servers* (2-3 clients); read Output for server and each client.
  Any red error on start = P0 until explained.
- With Studio's MCP server connected you can script these checks: start a play session, run Luau that
  asserts invariants (e.g., all stations have exactly one prompt; all `ScreenGui`s use safe insets;
  no `TextLabel` below the minimum size), read Output, stop. Keep such checks as files in the repo.

## Debug flags reset (before every publish)
- One `Config`/`Flags` module holds every debug toggle. A Lune test asserts release values
  (`DEBUG=false`, real timers, no free currency, empty admin list unless intended).
- `grep -rn "DEBUG\|TODO\|FIXME\|print(\|warn(" src/` and review each hit; remove noisy prints.
- Remove test-only remotes, cheat commands and "skip" buttons, or gate them by owner UserId on the server.

## Anti-patterns
- "It works in my Studio" while git has an older version.
- Tests that need Studio for logic that could be pure.
- Leaving `FAST_TIMERS = true` from the last playtest.
