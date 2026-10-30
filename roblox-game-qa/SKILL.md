---
name: roblox-game-qa
description: >-
  A step-by-step QA and refinement pass for Roblox experiences built with Rojo/Luau and Roblox Studio
  (optionally driven through Studio's built-in MCP server). Use it BEFORE publishing or updating a Roblox
  experience, AFTER a playtest or a batch of tester reports, and whenever the user wants to refine, polish,
  harden or "cover every possible problem" in a Roblox game. It runs ordered passes (context, audit,
  play critique, harden, adapt, polish, publish, feedback loop) over build reproducibility, every device
  and input type (phone, tablet, desktop, console/TV; touch, keyboard/mouse, gamepad), world interaction
  (ProximityPrompts, camera, movement), game flow, multiplayer/server authority, visuals/audio,
  performance, safety/compliance and publishing, scores each dimension 0-4, ranks findings P0-P3 and ends
  with a release gate that requires real-device and real-player verification. Composes `game-polish`,
  `game-feel` and `game-taste-3d` for the look-and-feel layer.
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
players, and why every tester report becomes a regression test. Always say what produced the evidence
(static check, unit test, Studio play-test, Device Emulator, real device, real players) and what stayed
untested.

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

## How to run the pass (order matters)

| # | Pass | Goal | Output |
|---|------|------|--------|
| 0 | **Context** | Write/refresh `GAME.md` at the repo root: genre, core loop, target devices, solo/multiplayer, server size, session length, audience/age, place & universe *names* (no secrets), known-unfinished areas. | `GAME.md` |
| 1 | **Audit** (code + build) | Everything measurable without playing: build, static checks, tests, debug flags, remotes, data, assets, performance budgets. | scored findings |
| 2 | **Critique** (play) | Play the real build like a first-time player on each device class; judge clarity, flow, pacing, fun, feel. | scored findings |
| 3 | **Harden** | Attack edge cases: join/leave mid-round, 1 vs N players, lag, spam, exploits, empty/long text, streaming, teleports, data loss. | findings + fixes |
| 4 | **Adapt** | Make every screen and action work on every device and input type. | findings + fixes |
| 5 | **Polish** | Refinement, not redesign: visuals, audio, juice, copy, consistency (→ `game-polish`, `game-feel`, `game-taste-3d`). | fixes |
| 6 | **Gate + publish** | Run the release gate, publish to the existing place, verify on a real device after publish. | gate report |
| 7 | **Feedback loop** | Turn every tester report into a reproducible bug → fix → regression test → re-verify on the failing device. | bug log |

Rules for running it:
- **Run Audit and Critique independently.** If you can spawn sub-agents, give each one a separate
  context so the code audit does not bias the play critique (and vice versa); merge only afterwards.
- **See it running.** Static reading cannot judge touch targets, prompt overlap, darkness or pacing.
- **Fix in severity order, one change at a time**, re-test after each; never one giant "QA fixes" commit.
- **Narrow targets beat whole-game glances.** "Critique the shift-end screen on a small phone" finds more than "review the game".
- **Polish preserves.** If the core loop is not fun, say so and stop polishing; send it back to concept validation / redesign.
- Read [reference/anti-patterns.md](reference/anti-patterns.md) before the first fix; it lists the Roblox mistakes no linter catches.

## Severity (blocker → polish)
- **P0 Blocker** — cannot play, progress, or ship: crash/error loop, stuck screen, lost data, exploit that
  breaks the economy, action impossible on a device class, safety/compliance violation. Fix now; blocks publish.
- **P1 Major** — a large share of players will struggle or quit: unclear goal, unreachable/overlapped
  prompt on touch, unreadable text on phone, broken mid-round join, frame drops on mobile. Fix before publish.
- **P2 Minor** — annoyance with a workaround: wrong hint glyph, small layout clipping, a loud sound. Next pass.
- **P3 Polish** — small finish details: extra juice, transition timing, copy tone. If time permits; keep the list short.

Not everything is P0. A list of 40 P1s is a failed triage.

## Dimension scores (0-4)
Score each dimension at the end of passes 1-4: **0** broken · **1** major gaps · **2** works with rough
edges · **3** good, minor issues · **4** excellent, verified on real devices. The release gate needs
**≥3 everywhere and 4 on "Devices & UI" and "Input parity" for every target device class**.

Dimensions: 1 Build & reproducibility · 2 Devices & UI · 3 Input parity · 4 World interaction ·
5 Game flow & onboarding · 6 Multiplayer & server · 7 Visual & audio · 8 Performance · 9 Safety &
compliance · 10 Publishing · 11 Feedback loop.

---

## The checklist (condensed; details and how-tos in `reference/`)

### 1. Build & reproducibility → [reference/build-and-tests.md](reference/build-and-tests.md)
- [ ] Clean checkout builds: `rojo build default.project.json -o build.rbxl` succeeds, no unmapped/duplicate paths.
- [ ] `luau-lsp analyze` (or Script Analysis), `selene`, `stylua --check` are clean; new modules use `--!strict` where feasible.
- [ ] Lune unit tests pass for every pure module (rules, scoring, economy, timers, difficulty).
- [ ] Studio Output is clean on server **and** client start: no errors, no warnings spam, no "asset not found / failed to load".
- [ ] **Debug flags reset:** every `DEBUG`, `SKIP_TUTORIAL`, `FAST_TIMERS`, `GOD_MODE`, test currency, admin allow-list, `print` spam is off/removed in the publish build (grep for them; ideally one `Config` module with a test that asserts release values).
- [ ] The place in Studio matches git (no Studio-only edits that Rojo will overwrite, or that never reached git).

### 2. Devices & UI → [reference/devices-and-ui.md](reference/devices-and-ui.md)
- [ ] Device Emulator pass on: small phone landscape, large phone landscape, tablet, 1080p desktop, ultrawide, console/TV (10-foot). Portrait too if `ScreenOrientation` allows it.
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
- [ ] Join mid-round, leave mid-round, rejoin, last player leaves, the player who pressed start leaves — all tested in *Clients and Servers* with 1, 2 and max players.
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

---

## Release gate (definition of done)
Ship only when all are true; otherwise report what is missing.
- [ ] Zero open P0; every P1 fixed or explicitly accepted by the owner in writing.
- [ ] All dimension scores ≥3; Devices & UI and Input parity = 4 for every target device class.
- [ ] Build from clean checkout + static checks + Lune tests green; debug flags in release state.
- [ ] Full loop played 3× in *Clients and Servers* with 1 and N players, Output clean.
- [ ] Played on at least one **real phone** (and every other target device class you can get), not just the emulator.
- [ ] At least 2 **real players** who did not build it completed the loop without help; their reports logged.
- [ ] Safety checks (filtering, no unapproved spending) pass; publish target confirmed as the existing place.
- [ ] Post-publish smoke test on a real device done.

## Report formats

**Finding (passes 1-5):**
```
P1 — [Devices & UI] Countdown overlay never dismisses on touch
  Evidence: Device Emulator iPhone SE landscape + real Android phone; Studio play, 1 player.
  Repro: start shift → countdown 3-2-1 → overlay stays until tapped.
  Why it matters: blocks the first seconds of every round on mobile.
  Fix: hide on countdown end (server state change), keep tap-to-skip as an extra.
  Verify: regression check in tests/ + replay on real phone.
```

**Tester report → bug (pass 7):**
```
ID: BUG-012          Severity: P0/P1/P2/P3        Status: new / repro / fixed / verified
Reporter + date:     Device + OS + input:  (e.g. Android phone, touch, landscape)
Build/place version: Players in server:
Steps:  1. … 2. … 3. …
Expected:            Actual:
Frequency: always / sometimes (x of y) / once     Output/F9 errors: (paste)
Screenshot/video:    Regression test: (file or manual check name)
```

**End of pass:** dimension scores table, counts by severity, the top 3 fixes, the gate checklist with
✅/❌, and an explicit **"Untested:"** line (devices, inputs, player counts or flows you could not check).

## Anti-patterns of the QA itself
- Declaring "works on mobile" from the Device Emulator alone.
- Testing only solo in Play mode; never with *Clients and Servers*, never with a late joiner.
- Reviewing code without playing; or playing without reading Output/F9.
- Fixing a reported bug without reproducing it first, or without a regression check.
- Polishing visuals while a P0/P1 remains.
- Publishing with debug flags on, or to a new duplicate place.
- Claiming the game is "100% bug-free". Report scores, evidence and what stayed untested instead.
