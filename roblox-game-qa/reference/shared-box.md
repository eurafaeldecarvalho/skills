# Shared machine: book it, check it, leave it clean (pass 0, mandatory)

Many agents may share one machine (same CPU, RAM, disk, Studio install). A Roblox QA run is heavy: Studio
under Wine without a GPU, extra Play clients, emulators of other agents, builds. Without coordination one agent
eats the RAM (there is often **no swap**: the kernel kills something at random) or closes another agent's window.
This reference makes the coordination a step of the pass, not a courtesy.

**Single source of truth:** the shared schedule + locks of `box-reserve.sh` (canonical copy:
[`mobile-app-qa/scripts/box-reserve.sh`](../../mobile-app-qa/scripts/box-reserve.sh); installed for all agents in
the shared folder, by default `/home/box/shared/` with `box-schedule.md` and `locks/`). Do **not** fork it or keep a
second schedule. This skill only adds [`scripts/box-preflight.sh`](../scripts/box-preflight.sh) (RAM/process
pre-flight + watchdog), installed next to it.

## What counts as heavy (book it)
Roblox Studio (any session, edit or play) · Clients-and-Servers / extra clients · Studio MCP play runs · Android
emulators · Gradle/large builds · long Lune soak tests (> 10 min or > 1 GB). Cheap and unbooked: static checks,
`rojo build`, short Lune suites, reading files.

## Roblox numbers to plan with (measure your own and write them in GAME-QA.md)
| Item | RAM (approx.) | Rule |
|---|---|---|
| Studio process (edit session) | ~2.5 GB | one Studio window per agent |
| Each Play / Server / Client window | ~2.5 GB more | on a ~8 GB-free box: edit + 1 client at most |
| Android emulator (other agents) | ~4 GB | never start Studio + clients beside a running emulator unless pre-flight says GO |
| Headroom that must stay free | 2 GB | no swap → below this, stop your own job |
| Studio MCP bridge | one per box | one port (e.g. 44755); if it is already listening, someone else's Studio is driven by it — coordinate, don't take it over |

## Before (every heavy job)
1. **Read the schedule:** `box-reserve.sh status` (live locks, upcoming slots, recurring `daily` rows).
   Respect every booking and recurring window of other agents on the same resource or `all`.
2. **Pre-flight:** `box-preflight.sh check -r studio,studio-client` (RAM available vs estimate + headroom,
   heavy processes of everyone, Studio/emulator counts, MCP port). `NO-GO` = do not start.
3. **Book a slot** with your project name and the resources (`studio`, `emulator`, `build`, or `all` for exclusive use):
   `box-reserve.sh reserve -p "<project>" -o "<agent>" -r studio -s "YYYY-MM-DD HH:MM" -e "YYYY-MM-DD HH:MM" -n "roblox QA iter 2"`.
   Exit 3 = overlap: **message the agent(s) that own the overlapping slot** (agent-to-agent message, or ask the
   owner to relay) and agree a time; book with `--force` only with their explicit OK, and say so in `-n`.
   If you are unsure whether your job disturbs someone (RAM close to the limit, their recurring window soon), message
   them anyway before starting.
4. **Take the lock** inside your slot: `box-reserve.sh acquire -p "<project>" -r studio` and release it on exit
   (`trap 'box-reserve.sh release -p "<project>" -r studio' EXIT`). A lock whose pid is dead or whose end time
   passed is stale and is ignored by the script; do not delete other agents' lock files by hand.
5. **Urgent override** (a release is blocked): message the affected agents first, wait for an answer or a
   reasonable timeout stated in the message, book with `--force` and a note, never stop their processes.

## During
- Run the watchdog on your own job: `box-preflight.sh watch --pid <your studio/job pid> --log qa/<date>/memlog.txt --kill`.
  Below the headroom it stops **only your pid**; then shrink the job (fewer clients) or rebook.
- Kill only processes you started (record their pids). Never close or kill another agent's Studio, emulator,
  Gradle daemon or browser window, even if it looks idle. Prefix your files and places with your project name.
- One Studio window per agent; close extra Play windows as soon as the check ends.
- `box-reserve.sh left -p "<project>" -r studio` tells the minutes left; stop and save before the slot ends.

## After
- Stop your Studio/Play windows and MCP bridge, release the lock (`box-reserve.sh release ...`, which also marks the
  slot `done`), and note the slot and RAM peak in the report.

## When you can't get a slot
Items that need the heavy resource become **Blocked** (reason: "no machine slot until <time>"), never passed and never
removed from the matrix; book the next free slot, keep doing headless work (Lune, fake server, static checks), and
list them under **Untested**. Real 2-client sessions on a small box and real phones need people: hand them an operator
script (see final-pass.md) instead of squeezing a second client into RAM that isn't there.
