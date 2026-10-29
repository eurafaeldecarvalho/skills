# Input parity & world interaction (dimensions 3-4)

## Action inventory (fill one row per action)
| Action | Keyboard/mouse | Touch | Gamepad | Hold? | Hint shown | Verified on |
|---|---|---|---|---|---|---|
| e.g. Pick up dough | E (prompt) | tap prompt / station bar | ButtonX | 0.5 s | "E" / hand icon / X | emulator + real phone |
Any empty cell is a finding (P0 if the action is required to progress).

## Binding
- Use `ContextActionService:BindAction(name, fn, createTouchButton, Enum.KeyCode.E, Enum.KeyCode.ButtonX)`
  for gameplay actions; position created touch buttons with `SetPosition` away from thumbstick/jump.
- Respect `gameProcessedEvent` in `UserInputService` handlers so typing in chat doesn't trigger actions.
- Unbind/rebind on state changes (lobby vs round) so stale bindings don't fire.

## Gamepad UI
- Every interactive `GuiObject` reachable: `Selectable = true`, set `GuiService.SelectedObject` when a
  menu opens and clear it on close; use `NextSelectionUp/Down/Left/Right` where auto-navigation guesses wrong.
- B/Back closes the top modal; Start/Menu doesn't conflict with Roblox's menu.

## Dynamic hints
- Track the current input via `UserInputService.PreferredInput` (or `LastInputTypeChanged` /
  `GamepadEnabled` / `TouchEnabled` as fallbacks) and swap glyphs/text live. A touch player must never
  see "Press E".

## Hold actions
- `ProximityPrompt.HoldDuration` works for all inputs. Custom holds need touch: start on
  `InputBegan` (Touch), show progress, cancel on `InputEnded`, finger leaving the button, or the
  character moving away. Clean up state on cancel.

## ProximityPrompts & ClickDetectors
- Walk/stand at every real interaction spot on phone and desktop camera angles and check which prompt
  shows. Roblox picks visible prompts by distance and where the camera points, so two close stations
  can make one prompt always win (the fryer-over-dough bug).
- Per prompt, decide: `Exclusivity` (`OnePerButton` default, `OneGlobally`, `AlwaysShow`),
  `MaxActivationDistance` (short for dense stations), `RequiresLineOfSight`, `UIOffset` (separate
  stacked prompts), `KeyboardKeyCode`/`GamepadKeyCode`, `ObjectText`/`ActionText` that say what happens.
- Parent prompts to a part at the interaction point, not to the center of a big model.
- Dense layouts: add a **station bar** (context buttons for nearby stations) as the touch path, or a
  custom prompt UI via `Style = Custom` with larger tap areas.
- ClickDetectors don't work well with gamepad; pair them with a prompt or a CAS action.
- Server re-checks distance and state on `Triggered` (clients can fire prompts from anywhere they exist).

## Movement & camera
- Decide per state: free movement, locked at a station (anchor/WalkSpeed 0 + restore), or cutscene.
  Make sure movement returns after the state ends, including on death/reset.
- Occlusion: `StarterPlayer.DevCameraOcclusionMode` (Zoom vs Invisicam), low ceilings, transparent
  roofs over play areas, `CameraMinZoomDistance`/`CameraMaxZoomDistance`, first-person lock only if intended.
- After cutscenes/`Scriptable` camera, return `CameraType` to `Custom` and the subject to the humanoid.
- Spawns not inside parts; kill planes and respawn behave; no ledge where players get stuck.

## Anti-patterns
- Keyboard-only `InputBegan` checks for gameplay.
- "Press E" text on mobile.
- Two prompts 2 studs apart with default settings.
- Relying on ClickDetector for console players.
- Trusting the client that a prompt was triggered from a valid spot.
