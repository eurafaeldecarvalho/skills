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
- Body text ≥ ~14 px after scaling; use `UITextSizeConstraint` (`MinTextSize`) when using `TextScaled`.
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
