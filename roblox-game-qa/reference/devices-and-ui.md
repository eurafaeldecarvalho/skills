# Devices & UI (dimension 2)

Goal: every screen is readable and usable on every target device, and nothing ever blocks play.

## Device matrix (minimum)
| Class | Emulator preset (examples) | What usually breaks |
|---|---|---|
| Small phone, landscape | iPhone SE / small Android | text too small, buttons under thumbstick/jump, panels overflow |
| Large phone, landscape | iPhone Pro Max / notch phones | notch/Dynamic Island covers HUD, rounded corners clip |
| Tablet | iPad | UI floats tiny in the middle or stretches absurdly |
| Desktop | 1080p, 1440p, ultrawide | Offset UI tiny on 1440p, stretched on ultrawide |
| Console / TV | Xbox / 10-foot | text too small at distance, no gamepad selection, overscan edges |
Studio's Device Emulator checks layout; it does **not** prove touch feel, performance or real safe areas.
Confirm on hardware (see release gate).

## The matrix (every iteration, never shrunk)
Rows = every reachable screen/state from FEATURES.md (loading, lobby, waiting, countdown, round, results,
settings, shop, disconnected…). Columns = viewport preset × input × language (localization.md) × player count
where it changes the UI. Three ways to fill a cell, cheapest first:
1. **Pure layout math (headless).** If UI positions/scale come from a pure module (one `UIScale` from the viewport,
   computed rects), a Lune test can sweep every screen × every viewport and assert: inside the safe area, no overlap,
   text ≥ floor in real px, targets ≥ 44 px, nothing in the thumbstick/jump zones. Seconds, no Studio.
2. **ui-audit probe in a play session** ([`scripts/ui-audit.client.luau`](../scripts/ui-audit.client.luau) via
   `studio-mcp.py run-pair`, inside a booked slot): measures the real GUI tree at the current viewport and input,
   per screen. It reports real px after scale, so a 9.9 px label can't hide behind "looks fine".
3. **Operator screenshots.** The Device Emulator preset switch is a Studio UI action the agent may not be able to
   drive; give the operator a numbered script (preset → screen → screenshot name) and audit the screenshots.
A cell is ✅ only with its evidence source in the report; a cell nobody could check is **Blocked**, not ✅.
A ui-audit hit is evidence, not proof: confirm on the screenshot before fixing, and fix the detector (with a test)
when it is wrong.

## Layout rules
- Size with **Scale**, keep shape with `UIAspectRatioConstraint`, cap with `UISizeConstraint`; or design at
  one reference resolution and drive a single `UIScale` from `workspace.CurrentCamera.ViewportSize`.
- Offset is fine for small padding/strokes, not for panels. A 900-px-wide Offset panel is a phone bug.
- Use `UIListLayout`/`UIGridLayout`/`UIPadding` so content reflows; test longest strings (and translations, if any).
- `ScreenGui.ScreenInsets`: `CoreUISafeInsets` for HUD and buttons (avoids Roblox top bar + notch);
  `DeviceSafeInsets` or none only for full-bleed backgrounds. Re-check after any top-bar change.
- Keep the mobile control zones clear: default thumbstick bottom-left, jump bottom-right (read real
  positions from `PlayerGui.TouchGui` at runtime if custom buttons need to sit near them).
- `StarterGui.ScreenOrientation` set deliberately; test rotation if sensor-based.

## Readability
- Touch targets ≥ 44×44 px on the smallest phone, with spacing so a thumb doesn't hit two.
- Body text ≥ ~14 px after scaling on phones (12 px is an absolute floor; set the number in GAME-QA.md); use `UITextSizeConstraint` (`MinTextSize`) when using `TextScaled`.
- Contrast: light text gets a `UIStroke` or a backing panel over 3D scenes.
- Emoji and rare glyphs may render differently or as boxes per platform/font: use ImageLabels for
  anything that carries meaning; test the rest on a real device.
- Console/TV: larger text and spacing; keep important UI ~5% away from edges.

## Overlays and states
- Every transient overlay (countdown, "round starting", results, toasts, tutorial bubbles) has an
  **automatic exit** tied to time or game state, plus an optional skip. Tap-only dismissal is a P0/P1.
- One modal at a time; opening a modal disables conflicting HUD buttons; every modal closes with a
  visible button, Back/B on gamepad and Esc where it makes sense.
- Overlays must not keep `Active`/`Modal` input capture after hiding (invisible blockers eat taps).
- Check every state screen: loading, waiting for players, empty inventory, round over, disconnected.

## Anti-patterns
- Testing only in the default Studio window size.
- `IgnoreGuiInset`/full-screen frames that hide behind the top bar or notch.
- Text that `TextScaled` shrinks to 6 px on phones.
- A HUD button parked exactly where the jump button is.
- Hidden frames that still swallow input.
