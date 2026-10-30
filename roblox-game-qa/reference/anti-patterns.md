# Roblox anti-pattern catalog

Things that pass linters and look fine in Studio but hurt real players. Check each one; add new lines
as you find new bug classes.

## UI & devices
- Offset-sized panels that overflow small phones or look tiny on 1440p.
- HUD under the notch or Roblox top bar (no `CoreUISafeInsets`).
- Buttons inside the thumbstick or jump zones.
- `TextScaled` without a minimum size; text unreadable on phones/TV.
- Overlays that only close on tap (countdowns, results, tutorial bubbles).
- Invisible frames that still capture input.
- Emoji carrying critical meaning (may render as boxes on some platforms).

## Input
- Keyboard-only actions; "Press E" shown to touch/gamepad players.
- Hold actions that only work with a key.
- Menus a gamepad can't navigate (no `SelectedObject`).
- ClickDetector-only interactions on console.

## World
- Adjacent ProximityPrompts with default settings, so one always wins on touch.
- Prompts parented to the center of big models.
- Character free to walk off mid-interaction (or stuck after it).
- Roofs/walls occluding the camera over the play area.

## Flow
- Rounds that never end when players leave; lobby waiting forever for "start".
- State not reset on replay (leaks appear on loop 3).
- Tutorial soft-lock when a step is skipped or a player leaves.
- First round as hard as later rounds.

## Server
- Client-authoritative score/currency/timers.
- Remotes without type/range/distance/state checks or rate limits.
- No handling for players who joined before the script connected `PlayerAdded`.
- Saves only on `PlayerRemoving` (lost on shutdown); `SetAsync` read-modify-write races.
- Client code assuming streamed-out parts exist.

## Visual, audio, performance
- Night scenes judged on a bright monitor.
- Assets not permitted for the experience (fine in Studio, missing for players).
- Unbounded loops, per-frame instancing, leaked connections.

## Safety & publishing
- Unfiltered user text shown to others.
- Debug flags/cheats left on; test currency in the live economy.
- Publishing a duplicate place instead of updating the existing one.
- Spending Robux or buying assets without the owner's approval.

## Accessibility & localization
- Game state shown by color alone, or a danger cue that is only a sound.
- Sentences built by concatenation; UI tested only with the source language's short strings.

## The QA process itself (shared machine, loop)
- Opening Studio + extra clients without booking the machine or checking free RAM; closing another agent's window.
- Treating a check that couldn't run (no slot, no device, no people) as passed instead of Blocked.
- Ending after one pass because the fixes "obviously" work; re-running only the fixed items.
- Smoke-testing a cloud place that doesn't contain the latest commits.
- Reporting frame rate measured on a box without a GPU.
