# GAME-QA.md — QA context for <experience name>
<!-- Pass 0. Copy to qa/GAME-QA.md (or merge into GAME.md). Facts only, no secrets. Re-read every iteration. -->

## The game
- Genre / core loop (one sentence):
- Solo / co-op / PvP; server size (Max Players): 
- Session length target:              Audience / age guideline:
- Languages shipped: (e.g. pt-BR source, en)
- Place / universe *names* (no IDs that grant access, no keys):
- Known-unfinished areas (not findings, but list them):

## Targets (what "every device" means here)
| Class | Must support? | Emulator preset | Real device available (who/when) |
|---|---|---|---|
| Small phone landscape | yes/no | iPhone SE | |
| Large phone / notch | | iPhone 14 Pro Max | |
| Tablet | | iPad | |
| Desktop 1080p / 1440p / ultrawide | | — | |
| Console / TV (10-foot, gamepad) | | Xbox | |
Inputs: touch · keyboard/mouse · gamepad (each: yes/no)

## Budgets (numbers, not adjectives)
- Text floor: __ px real on the smallest phone (≥ 12; phones ~14) · touch target ≥ 44 px
- Client memory on the weakest phone: < __ MB · server memory: < __ MB
- Frame rate on the weakest phone at the busiest moment: ≥ __ fps (real device only)
- Instances after N rounds: back to baseline ± __ (leak check)
- Join → first core action: ≤ 30 s · round/shift length: __ (drift ≤ 1 s)

## Machine constraints (shared box)
- Schedule: `box-reserve.sh status` (shared schedule file + locks). My project name in the schedule: ____
- RAM: total __ GB, no swap; headroom to keep: 2 GB. Studio ≈ 2.5 GB per process (edit + each Play window/client).
- Max Studio clients that fit while others run: __ (typically 1 extra). Real 2-client tests and real phones → people.
- Studio MCP bridge: one per box (port __); one Studio window per agent.
- Recurring windows of other agents I must not touch: (copy from the schedule, don't guess)

## Evidence sources available
Lune (pure + fake server) · Studio MCP play (server + 1 client) · Clients and Servers (N=__) ·
Device Emulator (operator) · real phone (who) · real players (who)
