# Game flow, onboarding & multiplayer (dimensions 5-6)

## Flow walk-through (do it 3× in a row, solo and with N clients)
1. Join → loading → lobby: what does a new player see in the first 10 s? Is the next step obvious?
2. Start: who can start, what if they leave, what if nobody presses start (auto-start/timeout)?
3. Rounds/shifts: timer visible, warnings near the end, the goal always on screen.
4. End screen: results readable, auto-advances, offers replay/back to lobby.
5. Replay: state fully reset (scores, inventories, spawned items, connections, UI). Leaks show up on
   the 3rd loop, not the 1st.

## Timers and state
- One server-side state machine (`Lobby → Countdown → Playing → Results → Lobby`), replicated via
  attributes or a single remote; clients render, never decide.
- Use `os.clock`/`workspace:GetServerTimeNow()` deltas, not counting `task.wait(1)` ticks.
- What happens on: all players leave, a player AFKs, the server is shutting down (`BindToClose`)?

## First-time player clarity
- Watch someone who has never played (no explaining). Note the second they first get stuck.
- Teach by doing: highlight the first station, arrow or beam to the target, one instruction at a time.
- Tutorial can't soft-lock (what if they walk away or leave mid-step?), persists completion, skippable.
- Pacing: the first round is easier and shorter; rewards early; new mechanics introduced one at a time.

## Difficulty curve
- Simulate with Lune using the real rule modules (see build-and-tests.md), then confirm with real
  players. Record target bands in `GAME.md` / `qa/GAME-QA.md` (e.g., level 1 win rate 90%+, level 5 ~60%).
- Tune separately for solo and full servers (more players = more hands; scale orders/enemies by player count).

## Server authority & remotes
- Client sends intent ("I want to pick up item X"), server checks and applies. Never accept score,
  currency, damage, positions of other things or timer values from the client.
- Validate every remote argument: type (`typeof`), range, NaN/inf, instance belongs to the expected
  folder, player is close enough, game state allows it, cooldown elapsed.
- Rate-limit per player (token bucket); drop and log spam instead of erroring.
- Don't `InvokeClient` and wait on the server; avoid RemoteFunctions where an event will do.
- Physics: decide network ownership for carried/pushed objects; the server validates results.

## Join / leave / reconnect
- Handle players already in the game when a script starts (`for _, p in Players:GetPlayers()` + `PlayerAdded`).
- Join mid-round: spectator or drop-in? UI must reflect the current state, not the lobby.
- Leave mid-round: their station/items/score cleaned or reassigned; the round still ends.
- Rejoin: data reloads; no duplicate characters or items.
- Test with 1, 2, and max players in *Clients and Servers*; set the server size (max players) deliberately in Game Settings.

## Data
- `DataStoreService` with retries/backoff, `UpdateAsync` for read-modify-write, session lock or
  ProfileStore-style pattern, save on leave + periodic + `BindToClose`. Never lose progress on shutdown.
- Version your data schema; migrate old saves.

## Streaming & teleports
- With `StreamingEnabled`, client code must not assume distant parts exist: `WaitForChild` with
  timeouts, `Model.ModelStreamingMode = Persistent` for things the client always needs (stations, UI anchors).
- Teleports: handle `TeleportInitFailed` with retry/message; treat `TeleportData` as untrusted; reserved
  servers for parties if needed.

## Anti-patterns
- Client-side scoring "because it's just a casual game".
- Timers that pause when the host's client lags.
- Only ever testing as the first player in an empty server.
- Round reset that forgets to disconnect last round's connections.
