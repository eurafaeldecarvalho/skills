# Build & reproducibility (dimension 1)

Goal: anyone (or any agent) can rebuild the exact published place from git and get the same result, and
the cheap checks catch bugs before a human has to play.

## Build
- `rojo build default.project.json -o build.rbxl` from a clean clone. Fail the pass on any warning about
  unknown files, duplicate names or paths that map nowhere.
- During development use `rojo serve` + the Studio plugin. Before publishing, either publish from a
  freshly built file or confirm Studio is synced and has no unsaved Studio-only edits.
- Things that live only in Studio (terrain, lighting tweaks, hand-placed models) must be exported back
  (`.rbxm`/`.rbxmx` in the repo, or a documented "Studio-owned" list in `GAME.md`). Unknown drift = P1.

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
