---
name: roblox-game-qa
description: >-
  QA and refinement pass for Roblox experiences built with Rojo/Luau and Roblox Studio (optionally driven via
  Studio's MCP server). Use it BEFORE publishing or updating an experience, AFTER a playtest or tester reports,
  and whenever the user wants to refine, polish, harden or "cover every possible problem" in a Roblox game.
  Step 0 books the shared machine (schedule, RAM pre-flight, coordination with other agents). Then ordered
  passes (audit, play critique, harden, red-team, adapt, polish, feedback loop) over build, every device and
  input, world interaction, flow, multiplayer, visuals/audio, measured performance, safety, publishing,
  accessibility and localization, repeated in a convergence loop until two clean iterations, then a FINAL
  PASS on the published build. Ships scripts (verify chain, Studio MCP harness, UI audit, Output scan, RAM
  pre-flight) and templates; scores 0-4, ranks P0-P3, ends with a release gate needing real devices and players.
---

# Roblox game QA (the "impeccable" pass for Roblox experiences)

A structured pass that takes an existing Roblox experience and leaves it **tested and polished on every
front we know how to check**: it finds problems, fixes them in priority order, proves the fixes, and only
then lets the build ship. It is the Roblox-specific counterpart of [`game-polish`](../game-polish/):
`game-polish` judges feel/look/onboarding for any game; this skill adds everything that is specific to
Roblox (devices, inputs, prompts, replication, publishing rules, safety) and the verification loop.

**Honest scope.** This checklist maximizes coverage; it cannot guarantee a bug-free game. Emulators
lie about touch, notches, memory and frame rate, and testers find things no checklist predicts. That is
why the pass ends with a **release gate** that requires a real device of each failing class and real
players, and why every tester report becomes a regression test. **Evidence-source rule:** every claim, score and
finding names what produced it — static check, Lune unit test, Lune fake server, Studio MCP play, Clients and
Servers, Device Emulator, real device, real players — and the config (build sha, place version, viewport, input,
players, language). A score is capped by its weakest source: nothing reaches 4 on emulator evidence alone.
What could not be checked is listed as **Untested** / **Blocked**, never silently passed.

Method credit: the pass structure (separate audit / critique / harden / adapt / polish passes,
0-4 dimension scores, P0-P3 severity, anti-pattern catalogs, "a detector result is evidence, not proof",
reporting what stayed untested) is adapted from Paul Bakaus's
[Impeccable](https://github.com/pbakaus/impeccable) skill for frontend design (Apache-2.0). No text is
copied; the Roblox content is original.

## Tools this skill assumes
- **Rojo** project (`default.project.json`), Luau source in git. Build with `rojo build`, sync with `rojo serve`.
- **Static checks:** `luau-lsp analyze` (or Studio Script Analysis), `selene`, `stylua --check`.
- **Unit tests / simulations:** **Lune** running pure Luau modules (game rules, economy, difficulty) outside Studio.
- **Roblox Studio** for play-tests: Play / Play Here / Run, *Test ▸ Clients and Servers* (multi-client local
  server), *Device Emulator*, Output, Developer Console (F9), MicroProfiler (View ▸ MicroProfiler in Studio; Ctrl+F6 in the client).
- **Studio's built-in MCP server**, when connected: use it to run Luau in edit/play mode, start/stop
  play-tests, read Output and inspect the DataModel. Without it, hand the owner an exact play-test script.
- A real phone (and ideally a tablet, a console or a TV-size screen) and at least 2 real testers.
- When the machine is shared with other agents: the shared schedule `box-reserve.sh` (+ `box-schedule.md`,
  `locks/`) and this skill's `box-preflight.sh`, both in the shared folder. See
  [reference/shared-box.md](reference/shared-box.md).

## Scripts and templates (copy into the game repo's `qa/`, adjust the config block, keep them in git)
| File | Use |
|---|---|
| [scripts/verify.sh](scripts/verify.sh) | Pass 1 headless chain (compile, rojo, luau-lsp, selene, stylua, flags, Lune × N for flakes) |
| [scripts/studio-mcp.py](scripts/studio-mcp.py) | Drive Studio's MCP server: edit-mode Luau, play-mode server script, inject/remove a client probe |
| [scripts/ui-audit.client.luau](scripts/ui-audit.client.luau) + [scripts/qa-collect.server.luau](scripts/qa-collect.server.luau) | Measure the live GUI (insets, off-screen, real text px, targets, thumb zones, overlaps, blockers, modals) |
| [scripts/windows-pc/](scripts/windows-pc/) | Rafael's Windows PC: Server & Clients harness (mt_ins/multi_srv/multi_cli/mt_poll/mt_rem), probes, batches, win.py ([reference/windows-pc.md](reference/windows-pc.md)) |
| [scripts/output-scan.py](scripts/output-scan.py) | Classify Output/F9/MCP logs into P0-P2 findings; gate on P0/P1 |
| [scripts/box-preflight.sh](scripts/box-preflight.sh) | Shared-machine RAM/process pre-flight + memory watchdog for your own job |
| [templates/GAME-QA.md](templates/GAME-QA.md) | Pass 0 context: targets, numeric budgets, machine constraints, evidence sources |
| [templates/FEATURES.md](templates/FEATURES.md) | Inventory of every action/screen with oracle, edges, failure and red-team rows; ⏳ must reach 0 |
| [templates/report-template.md](templates/report-template.md) | Scores, iteration ledger, findings with config + evidence, red-team, FINAL PASS, gate, Untested/Blocked |
| [templates/bug-template.md](templates/bug-template.md) · [templates/manual-checks.md](templates/manual-checks.md) | Tester reports; regression checks no script covers yet |

The Luau probes and the MCP client were validated against a stub MCP server and the compiler, and on 2026-10-30 against
Studio 0.745's built-in StudioMCP.exe on a Windows PC (solo, Server & Clients with 2–3 clients, Device Simulator); check them once
on your Studio (and its MCP tool names) before trusting a clean result.

## How to run the pass (order matters)

| # | Pass | Goal | Output |
|---|------|------|--------|
| 0 | **Machine + context** | **Mandatory pre-flight** before anything heavy (below). Then write/refresh `qa/GAME-QA.md` (template): genre, core loop, target devices/inputs, players, languages, numeric budgets, machine constraints, place *names* (no secrets). | booked slot, `GAME-QA.md` |
| 1 | **Audit** (code + build) | `scripts/verify.sh`; build `FEATURES.md` from the code (remotes, prompts, buttons, states); debug flags, data, assets, budgets. | scored findings, `FEATURES.md` |
| 2 | **Critique** (play) | Play the real build like a first-time player on each device class; judge clarity, flow, pacing, fun, feel. | scored findings |
| 3 | **Harden** | Edge cases: join/leave mid-round, 1 vs N players, lag, empty/long text, streaming, teleports, data loss — on the Lune fake server first, then in play. | findings + fixes |
| 3b | **Red-team** | Hostile client: wrong types, spam, out-of-state, ownership, distance, size, join/leave storms, data, forged teleport data, economy, seeded monkey ([reference/red-team.md](reference/red-team.md)). New seeds every iteration. | findings + seeds |
| 4 | **Adapt** | Every screen × viewport × input × language: layout math sweep, `ui-audit` probe, operator screenshots; accessibility and localization. | matrix + fixes |
| ↺ | **Converge** | Repeat passes 1–4 (whole, plus every earlier regression check) until **2 consecutive iterations with zero P0–P2**, fresh seeds in the second ([reference/convergence-loop.md](reference/convergence-loop.md)). | iteration ledger |
| 5 | **Polish** | Refinement, not redesign: visuals, audio, juice, copy, consistency (→ `game-polish`, `game-feel`, `game-taste-3d`). | fixes |
| 6 | **FINAL PASS + gate** | Clean-commit build, publish (owner-approved) to the existing place with private/playtest access, real-server Output/F9, update-over-previous-version data check, real phone + 2 real players, rollback noted ([reference/final-pass.md](reference/final-pass.md)). Then the release gate. | FINAL PASS table, gate |
| 7 | **Feedback loop** | Turn every tester report into a reproducible bug → fix → regression test → re-verify on the failing device. | bug log |

### Step 0 — shared-machine pre-flight (mandatory, every session that opens Studio, extra clients, emulators or long soaks)
Several agents may share one box with limited RAM and often no swap. Before any heavy step
([reference/shared-box.md](reference/shared-box.md) has the commands):
1. **Read the schedule** (`box-reserve.sh status`): live locks, booked slots and recurring windows of other agents.
2. **Check the machine** (`box-preflight.sh check -r studio[,studio-client]`): `free -m`, heavy processes of
   everyone (Studio, emulators, Gradle…), RAM estimate for your plan. Budget: Studio ≈ 2.5 GB per process (edit
   session and each Play client), an emulator ≈ 4 GB, and **≥ 2 GB must stay free**. NO-GO → don't start.
3. **Book a slot** in the shared schedule with your project and resource, then take the lock inside it. Respect
   other agents' bookings and recurring windows; on overlap or doubt, **message the affected agents first**
   (agent-to-agent, or via the owner). Urgent overrides: notify first, then book with `--force` and a note.
4. **During:** run the memory watchdog on your own pid; if free RAM drops below the headroom, stop **your**
   job. Kill only your own processes; never close or kill another agent's windows. One Studio window per agent;
   the Studio MCP bridge is a single port per box — if it's taken, coordinate.
5. **After:** close your Studio/clients, release the lock (marks the slot done), log the slot and RAM peak.
6. **No slot / not enough RAM:** the affected items are **Blocked** (never counted as passed); do the headless work,
   rebook, and list them under Untested.

### Running on Rafael's Windows PC (mandatory rules)
When the QA runs on Rafael's Windows PC (DESKTOP-UEOVLLP), follow [reference/windows-pc.md](reference/windows-pc.md):
- **A REAL multiplayer test is MANDATORY:** *Server & Clients* with **2+ clients** (3 when the game has spectators or a
  queue), driven by MCP with the `scripts/windows-pc/` pattern (`mt_ins` → `multi_srv`/`multi_cli` → `mt_poll` → `mt_rem`):
  the core action through the real remotes, state equal on every client, red-team from the unprivileged client, one
  player leaving mid-round. A QA on the PC without it is incomplete.
- Local Rojo-built place only, in your own test Studio under `C:\Users\Rafael\turno-qa\`; never the live place, never
  publish. Leave Rafael's own Studio/Player windows alone; close only your test Studio (check PID + title).
- Use Studio's **built-in StudioMCP.exe** (status-bar "MCP" toggle) with `studio-mcp.py --studio <file>.rbxlx batch`.
- Batch every PC command (each one needs approval); `CopyToBox` only after the producing command finished.

Rules for running it:
- **Run Audit and Critique independently.** If you can spawn sub-agents, give each one a separate
  context so the code audit does not bias the play critique (and vice versa); merge only afterwards.
- **See it running.** Static reading cannot judge touch targets, prompt overlap, darkness or pacing.
- **Fix in severity order, one change at a time**: failing regression check first, then the fix, one finding per
  commit with its ID; never one giant "QA fixes" commit. A fix is verified by the next full iteration, not by itself.
- **Prefer headless evidence, then confirm live.** Lune pure tests and the fake server run anywhere in seconds;
  a Studio slot is scarce on a shared box — spend it on what only Studio can show.
- **Narrow targets beat whole-game glances.** "Critique the shift-end screen on a small phone" finds more than "review the game".
- **Polish preserves.** If the core loop is not fun, say so and stop polishing; send it back to concept validation / redesign.
- Read [reference/anti-patterns.md](reference/anti-patterns.md) before the first fix; it lists the Roblox mistakes no linter catches.

## Severity (blocker → polish)
| Sev | Meaning | Roblox examples |
|---|---|---|
| **P0 Blocker** | cannot play, progress or ship; fix now, blocks publish | server error loop on join; overlay that only leaves on tap and blocks the round; data lost on leave/shutdown; a remote that grants currency/score without validation (any successful red-team attack); action impossible on touch or gamepad; unfiltered user text shown to others; debug flag on in the publish build |
| **P1 Major** | many players struggle or quit; fix before publish (or owner accepts in writing) | prompt hidden behind another on touch; core text < 12 px on a small phone; late joiner stuck in lobby; instance count grows every round; asset not permitted (silent for players); infinite yield in Output; no visual cue for a sound-only danger |
| **P2 Minor** | annoyance with a workaround; fixed inside the loop (the loop exits only at zero P2) | `E` hint shown on touch; label clipped in one language; deprecated `wait()`; a loud sound; button slightly under the jump zone on one preset |
| **P3 Polish** | finish details; tracked, doesn't keep the loop alive | transition timing, extra juice, copy tone, emoji in a title |

Not everything is P0. A list of 40 P1s is a failed triage.

## Dimension scores (0-4)
Score each dimension at the end of passes 1-4: **0** broken · **1** major gaps · **2** works with rough
edges · **3** good, minor issues · **4** excellent, verified on real devices. The release gate needs
**≥3 everywhere and 4 on the mandatory four — Devices & UI, Input parity, Multiplayer & server, Safety &
compliance — for every target device class**. A 4 needs live evidence (real device / real players for Devices,
Input and Multiplayer); headless-only evidence caps at 3.

Dimensions: 1 Build & reproducibility · 2 Devices & UI · 3 Input parity · 4 World interaction ·
5 Game flow & onboarding · 6 Multiplayer & server · 7 Visual & audio · 8 Performance · 9 Safety &
compliance · 10 Publishing · 11 Feedback loop · 12 Accessibility & localization
([reference/accessibility.md](reference/accessibility.md), [reference/localization.md](reference/localization.md)).

---

## The checklist (condensed; details and how-tos in `reference/`)

### 1. Build & reproducibility → [reference/build-and-tests.md](reference/build-and-tests.md)
- [ ] Clean checkout builds: `rojo build default.project.json -o build.rbxl` succeeds, no unmapped/duplicate paths.
- [ ] `luau-lsp analyze` (or Script Analysis), `selene`, `stylua --check` are clean; new modules use `--!strict` where feasible.
- [ ] Lune unit tests pass for every pure module (rules, scoring, economy, timers, difficulty).
- [ ] `scripts/verify.sh` green with `FLAKE=3` (a test red once in 3 runs is a finding).
- [ ] Studio Output is clean on server **and** client start (`output-scan.py` on the log): no errors, no warnings spam, no "asset not found / failed to load".
- [ ] **Debug flags reset:** every `DEBUG`, `SKIP_TUTORIAL`, `FAST_TIMERS`, `GOD_MODE`, test currency, admin allow-list, `print` spam is off/removed in the publish build (grep for them; ideally one `Config` module with a test that asserts release values).
- [ ] The place in Studio matches git (no Studio-only edits that Rojo will overwrite, or that never reached git).

### 2. Devices & UI → [reference/devices-and-ui.md](reference/devices-and-ui.md)
- [ ] Screen × viewport matrix filled (layout-math sweep, `ui-audit` probe, operator screenshots), every cell with its source. Device Emulator pass on: small phone landscape, large phone landscape, tablet, 1080p desktop, ultrawide, console/TV (10-foot). Portrait too if `ScreenOrientation` allows it.
- [ ] Layout uses Scale + `UIAspectRatioConstraint` / `UISizeConstraint`, or one `UIScale` driven by viewport; no giant Offset-only panels.
- [ ] Safe area: `ScreenGui.ScreenInsets` = `CoreUISafeInsets` (or `DeviceSafeInsets` for full-bleed backgrounds only); nothing important under the notch, the Roblox top bar, or rounded corners.
- [ ] Nothing interactive sits on the mobile thumbstick (bottom-left) or jump button (bottom-right) zones.
- [ ] Touch targets ≥ 44×44 px on the smallest phone; text ≥ ~14 px after scaling (`UITextSizeConstraint.MinTextSize`); `TextScaled` never shrinks body text to unreadable.
- [ ] `StarterGui.ScreenOrientation` set intentionally (usually `LandscapeSensor` for action games).
- [ ] Emoji/special glyphs render on every platform (no tofu boxes) — prefer images/icons for critical meaning.
- [ ] **Every overlay dismisses itself** (countdowns, "round starting", toasts, results) on a timer or state change — never only on tap. *(Real bug: a countdown screen that disappeared only when tapped, blocking the game.)*
- [ ] Modal stacking is sane: one modal at a time, a visible close/back on every platform, Back/B closes on gamepad.

### 3. Input parity → [reference/input-and-interaction.md](reference/input-and-interaction.md)
- [ ] Inventory every player action; each has a **keyboard/mouse, touch and gamepad** path (table in the reference).
- [ ] Actions bound with `ContextActionService` (gamepad + optional touch button) rather than keyboard-only `InputBegan`.
- [ ] Gamepad can reach every button: `GuiObject.Selectable`, `GuiService.SelectedObject` set when a menu opens, sensible `NextSelection*`.
- [ ] Button hints switch by input type (`UserInputService.PreferredInput` / `LastInputTypeChanged`): `E` vs tap vs `ButtonX`.
- [ ] Hold actions work by touch (press-and-hold with progress, cancel on finger-up/leave) and on gamepad.
- [ ] No action needs hover, right-click, scroll wheel or two simultaneous keys without an alternative.

### 4. World interaction → [reference/input-and-interaction.md](reference/input-and-interaction.md)
- [ ] ProximityPrompts / ClickDetectors don't overlap or occlude each other from the player's real standing spots and camera angles, **especially on touch**. *(Real bug: on mobile the fryer prompt always won over the dough prompt next to it.)*
- [ ] Prompt `Exclusivity`, `MaxActivationDistance`, `RequiresLineOfSight`, `UIOffset`, `HoldDuration`, key codes set per prompt on purpose; `ProximityPromptService.MaxPromptsVisible` considered.
- [ ] Dense station layouts have a **touch fallback** (a station bar / contextual buttons) instead of relying on prompt picking.
- [ ] Character movement is intended (free, locked at a station, or disabled); no accidental walking off while interacting.
- [ ] Camera: no walls/roofs occluding the play area (`DevCameraOcclusionMode`, collision groups, transparent ceilings), zoom limits set, camera resets after cutscenes.
- [ ] Spawn points safe; no falling through the map; `FallenPartsDestroyHeight` and respawn behave.

### 5. Game flow & onboarding → [reference/flow-and-multiplayer.md](reference/flow-and-multiplayer.md)
- [ ] Full loop works end to end: join → lobby → start → rounds/shifts → end screen → replay/back to lobby, repeated 3+ times without leaks or stuck state.
- [ ] Timers are server-authoritative; clients only display; pausing/AFK/leave doesn't freeze them.
- [ ] A first-time player knows what to do within ~10 s and does the core action within ~30 s (watch someone new; don't explain).
- [ ] Tutorial teaches by doing, can't soft-lock, is skippable for returning players, and is shown once (persisted).
- [ ] Difficulty curve validated with **Lune simulations** of the real rules (win rate / score per level for weak, average, strong bots), then confirmed by real players.
- [ ] Solo and multiplayer modes both tuned (solo isn't impossible, full server isn't trivial).

### 6. Multiplayer & server → [reference/flow-and-multiplayer.md](reference/flow-and-multiplayer.md)
- [ ] Server authority: the client requests, the server decides (score, currency, inventory, damage, timers).
- [ ] Every `RemoteEvent`/`RemoteFunction` validates type, range, ownership, distance and state, and is rate-limited per player; no `InvokeClient` the server waits on.
- [ ] Join mid-round, leave mid-round, rejoin, last player leaves, the player who pressed start leaves — all on the Lune fake server with 1, 2 and max players, and confirmed in *Clients and Servers* as far as the machine allows (Blocked beyond that).
- [ ] Red-team rows R01–R12 pass with this iteration's seeds ([reference/red-team.md](reference/red-team.md)).
- [ ] Data: DataStore with retries, `UpdateAsync`, session locking, `BindToClose` save, no data loss on shutdown or teleport.
- [ ] `StreamingEnabled` behavior: clients use `WaitForChild` / `ModelStreamingMode` for models they need; nothing assumes the whole map is present.
- [ ] Teleports: failures handled (`TeleportInitFailed`), teleport data treated as untrusted.
- [ ] Max players (Game Settings ▸ Places / server size) matches the design; server fill and reserved/private servers behave.

### 7. Visual & audio → [reference/visual-audio-performance.md](reference/visual-audio-performance.md)
- [ ] Lighting readable on a dim phone screen: night/indoor scenes not too dark (check `Brightness`, `Ambient`, `OutdoorAmbient`, `ExposureCompensation`, Atmosphere, local lights).
- [ ] No missing assets: Output has no "failed to load", no grey boxes, no default textures; asset permissions granted to this experience.
- [ ] NPC rigs: correct rig type, `HumanoidRootPart` anchored as intended, animations loaded via `Animator`, owned/permitted animation IDs, no T-pose.
- [ ] Signals readable at a glance (order ready, timer low, danger): shape + color + sound, never color alone.
- [ ] Audio exists, is balanced through `SoundGroup`s, no clipping/loud spikes, music loops cleanly, settings mute works.
- [ ] Look & feel pass → `game-taste-3d` (art direction) and `game-feel` (juice).

### 8. Performance → [reference/visual-audio-performance.md](reference/visual-audio-performance.md)
- [ ] Budgets met on the weakest target phone: stable FPS during the busiest moment, client memory comfortably below the device limit.
- [ ] Part/instance counts reasonable; unions/meshes with sensible `CollisionFidelity`; `CanCollide`/`CanTouch`/`CanQuery` off where unused; anchored statics.
- [ ] Streaming configured for large maps; no per-frame `Instance.new`/destroy churn; no unbounded loops or leaked connections across rounds.
- [ ] Script activity in Developer Console and MicroProfiler checked during peak load, server and client.
- [ ] Numbers recorded: instance count at lobby / after round 1 / after round 3 (flat), memory per side, remotes/s at peak; real fps only from a real device (a no-GPU box gives none).

### 9. Safety & compliance → [reference/safety-and-publishing.md](reference/safety-and-publishing.md)
- [ ] Every user-written text shown to others (names, signs, pets, messages) is filtered with `TextService` before display; filter failures hide the text.
- [ ] `TextChatService` settings deliberate; no custom chat bypassing filtering.
- [ ] Content follows Community Standards; Maturity & Compliance answers are truthful for the actual content; age guidelines match the audience.
- [ ] **No paid assets, Robux spending, developer products, game passes, ads or price changes without the owner's explicit approval.**
- [ ] No secrets in the place (API keys, webhooks) — use Secrets/HttpService config, never in a ModuleScript clients can read.

### 10. Publishing → [reference/safety-and-publishing.md](reference/safety-and-publishing.md)
- [ ] Publish to the **existing** place/universe (never "Publish as new" creating duplicates); confirm the place name before publishing.
- [ ] Audience/access chosen on purpose (playtest/early testers vs public) and its current requirements met.
- [ ] Version noted; rollback path known (place version history); servers restarted/migrated if needed.
- [ ] After publish: join from a **real device** of each class that had bugs, play one full loop, check F9 console.

### 11. Feedback loop → [reference/feedback-loop.md](reference/feedback-loop.md)
- [ ] Each tester report logged with the template below and reproduced (or marked "cannot reproduce" with what was tried).
- [ ] Fix → regression test (Lune unit test, or a scripted Studio/MCP check, or a named manual check) → re-verify on the device type that failed.
- [ ] The anti-pattern catalog gets a new line when a bug class is new.

### 12. Accessibility & localization → [reference/accessibility.md](reference/accessibility.md), [reference/localization.md](reference/localization.md)
- [ ] No meaning by color alone or sound alone; no fast full-screen flashing; reduced-motion respected; generous timing on holds.
- [ ] Every visible string comes from one table; every key exists in every shipped language (test); no concatenated sentences.
- [ ] Locale × viewport sweep (longest strings, pseudo-locale) clean on the smallest phone.

---

## Release gate (definition of done)
Ship only when all are true; otherwise report what is missing.
- [ ] Zero open P0 and zero open P1 (a P1 may stay only if the owner accepts it in writing, with its ID, in the report — the agent never accepts its own).
- [ ] Convergence loop exited: 2 consecutive full iterations with zero P0–P2, the second with fresh red-team seeds; no severity lowered and no check removed to get there.
- [ ] FEATURES.md has no ⏳; every Blocked item is listed with its reason and counts as not passed.
- [ ] All dimension scores ≥3; the mandatory four (Devices & UI, Input parity, Multiplayer, Safety) = 4 for every target device class.
- [ ] Build from clean checkout + static checks + Lune tests green; debug flags in release state.
- [ ] Full loop played 3× in *Clients and Servers* with 1 and N players, Output clean.
- [ ] Played on at least one **real phone** (and every other target device class you can get), not just the emulator.
- [ ] At least 2 **real players** who did not build it completed the loop without help; their reports logged.
- [ ] Safety checks (filtering, no unapproved spending) pass; publish target confirmed as the existing place.
- [ ] FINAL PASS done on the published build (clean commit, place version recorded, real-server Output/F9 clean, previous-version data loads, rollback version noted).
- [ ] Shared-machine slot released; no leftover processes of yours.

## Report formats

Use [templates/report-template.md](templates/report-template.md) for the whole report (scores, iteration ledger,
findings, red-team, FINAL PASS, gate, Untested/Blocked).

**Finding (passes 1-5):**
```
P1 — [Devices & UI] Countdown overlay never dismisses on touch          (F-07, found iter 1)
  Config: build 3f2a1c0 · local place · iPhone SE landscape preset · touch · 1 player · pt-BR
  Evidence source: Device Emulator (operator screenshot) + real Android phone.
  Repro: start shift → countdown 3-2-1 → overlay stays until tapped.
  Why it matters: blocks the first seconds of every round on mobile.
  Fix: hide on countdown end (server state change), keep tap-to-skip as an extra.
  Verify: regression check in tests/ + replay on real phone.
```

**Tester report → bug (pass 7):** [templates/bug-template.md](templates/bug-template.md) (device, OS, input,
graphics quality, language, players, place version, steps, expected/actual, frequency, F9 errors).

**End of each iteration:** a ledger row (P0–P3, fixed, new, regressions, Blocked, clean streak). **End of the
run:** dimension scores, the gate with ✅/❌/Blocked, the top 3 next steps, and an explicit **"Untested:"** line
(devices, inputs, player counts, languages or flows you could not check, and why).

A worked example of this skill on a real game (and the bugs that shaped these rules):
[reference/case-turno.md](reference/case-turno.md).

## Anti-patterns of the QA itself
- Declaring "works on mobile" from the Device Emulator alone.
- Testing only solo in Play mode; never with *Clients and Servers*, never with a late joiner.
- Reviewing code without playing; or playing without reading Output/F9.
- Fixing a reported bug without reproducing it first, or without a regression check.
- Polishing visuals while a P0/P1 remains.
- Publishing with debug flags on, or to a new duplicate place.
- Claiming the game is "100% bug-free". Report scores, evidence and what stayed untested instead.
- Starting Studio or extra clients on a shared machine without the pre-flight and a booked slot, or touching
  another agent's processes or windows.
- Counting Blocked checks as passed; lowering a severity, skipping a test or shrinking the matrix to exit the loop.
