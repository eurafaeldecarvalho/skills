---
name: game-taste-2d
description: >-
  Make a 2D game LOOK beautiful and intentional instead of cheap, generic, "asset-flip", or AI-made —
  the visual art-direction layer ("taste-skill, but for games"). Use whenever designing, generating,
  choosing, or reviewing a game's visuals: palette and color, readability and silhouette, composition,
  mascot/character design, camera framing and parallax, HUD and typography/fonts; when a game looks
  flat, off, generic, templated, "Unity-default", asset-flippy, or AI-made; when deciding art direction
  or how to make a minimalist game look premium and read cleanly; and when setting up an AI asset
  pipeline for a consistent style. Reach for it even when the user just says "it looks cheap" or "make
  it look good". Pairs with the `game-feel` skill (motion/juice); this one is how the game LOOKS,
  game-feel is how it FEELS.
---

# Game taste (art direction for 2D games)

A game looks cheap not because it uses simple art or asset packs — it looks cheap because it's
**inconsistent**: mixed art styles, engine-default materials and fonts, AI outputs left untouched, a
UI that doesn't match the sprites. Taste is **intentional constraint applied consistently**. This
skill is the protocol for that, for 2D/flat/low-poly games (web, PixiJS, Phaser, Godot 2D).

Companion skill: **`game-feel`** owns motion/juice (easing, number-pop, screenshake, hit-stop, SFX).
This skill owns the still frame: color, shape, readability, layout, type. Use both together — they're
the "impeccable for games" when combined.

## The one rule: lock the palette and font BEFORE making any art
Most slop is created in the first hour, by generating or coding art before the constraints exist.
Build a **one-screen moodboard** first (the main gameplay view + the HUD + the shareable moment, side
by side), lock the master palette and the font, then produce. Retrofitting a palette is agony.

## 1. Palette protocol
- **<15 colors in the whole game**, organized in 5 groups: **shadow / mid / light / accent / white.**
  A tight palette is what creates unity and directs the eye. (Alto's Adventure, Monument Valley.)
- If the game has **zones** (levels, biomes, depth layers), give each zone ~3 colors that shift by
  **value and temperature** to carry meaning — but keep the total under ~12 + 2 reserved.
- **Reserve 1–2 colors as a FIXED ACCENT** for the player/mascot and critical UI — it never changes
  from zone to zone. This is what anchors identity *and* legibility at once.
- **Reserve a rare, high-contrast color for reward/danger only** (the Downwell lesson): don't let the
  whole palette be saturated. A color used only for the jackpot/threat reads instantly as special.
- Define the palette as **tokens** (CSS `:root` vars / a constants file), never as scattered literals.

## 2. Legibility comes from VALUE, not hue
- Build contrast with luminosity (light/dark), not color. Gameplay clarity depends on it.
- **The 32px silhouette test (do this before detailing anything):** paint the character/key object
  100% black over each background it appears on. If you can't tell what it is from the shape alone, or
  it disappears against a background, fix it — usually with a constant thin light/dark **outline** that
  holds its value against *every* background.
- Never communicate information by color alone (accessibility) — also use shape, icon, or position.

## 3. Composition: detail in the action zone, everything else breathes
- Concentrate detail, particles, and animation in the **player's active zone**. Over-detailed
  backgrounds that compete with the action are noise.
- Everything else is **flat, large shapes, negative space** (Monument Valley / Alto's). A clean,
  uncluttered frame is what reads as premium.
- **Transitions between zones are gradients, not hard cuts** — let the new palette bleed into the old
  over ~one screen; it feels intentional and continuous.

## 4. Cohesion is everything (the real anti-slop lever)
Pick ONE of each and apply it to every element — button, number, card, character, icon:
- one font, one shadow (at most one soft shadow), one corner radius, one line weight, an 8px grid.
- one unified light/color treatment layered over everything so nothing looks "out of the box".
- Implement what repeats (icons, bands, the share card, the mascot) in **SVG/canvas recolored by
  token** — coherence becomes trivial, it loads instantly, and it suits a flat/low-poly look.

## 5. Mascot / character (optional but high-ROI for virality)
A mascot is usually a **marketing/share-card asset, not a gameplay one** — it amplifies the shareable
moment at near-zero cost. Putting it in the way of the core loop is low ROI.
- **One dominant shape** (round = friendly), **monochrome in the fixed accent color** (so you can make
  viral variants by swapping an *accessory/color*, not the model).
- **Emotion by posture + contrast, not by an animated face.** Budget: one 2-frame idle (bounce with
  squash & stretch preserving volume) + ~4 **static** expressions mapped to states (e.g. happy / scared
  / celebrating / deflated). No rig, no walk cycle.
- Run the 32px silhouette test on it before detailing.
- Keep it **simple enough that a 6-year-old could draw it** — that's what makes it meme-able and cheap
  (crewmate, Fall Guys bean, Suika's fruit).

## 6. Camera & framing (the still-frame part; shake lives in game-feel)
- Frame for what matters: if the interesting thing is *ahead/below*, keep the player off-center (e.g.
  upper third, 60–70% of the screen showing what's coming — Downwell).
- **Follow with time-based smoothing**, never a fixed per-frame lerp (it breaks across refresh rates —
  critical on web): `cam += (target - cam) * (1 - exp(-k * dt))` or SmoothDamp (~0.12–0.20s). Update the
  camera *after* movement, or it lags a frame.
- Use a **deadzone + lookahead** toward the direction of travel.
- **Depth via 3-layer parallax** of gradient/bands (factors ~0.2 / 0.5 / 0.8), drawn back-to-front. Not
  5–6 detailed layers (expensive, pollutes the flat look, slows load).
- (Screenshake, hit-stop, punch-in → see `game-feel`. Reserve them for milestones, never the common loop.)

## 7. HUD & typography
- Make the **hero metric diegetic** when you can (a progress element the player reads as part of the
  world, not a floating label). Everything else is secondary — clarity over immersion in the HUD.
- Numbers: `font-variant-numeric: tabular-nums` so digits don't jitter width; animated count-up with
  easing; **one notation per range** (K/M/B/T then scientific), always the same decimal places.
- **Typography carries the same personality as the art.** One font with character used in *everything*
  (numbers, buttons, card). Good free/OFL choices for flat/rounded games: Fredoka, Baloo 2, Nunito for
  UI; Audiowide/Orbitron for a display logo. **Never** Arial/Times/system-default. No pixel fonts if the
  art is flat (they fight). Load one display weight + two UI weights to stay light.
- Touch targets ~44px, text contrast ~4.5:1.

## 8. AI asset pipeline (consistent + cheap + light)
- **Prefer code over bitmaps for anything that repeats** (icons, bands, globe, mascote): SVG/canvas
  recolored by token. Bonus: instant load and trivial coherence.
- When you do need coherent bitmaps: (1) write the **rules first** (small palette, line weight, flat
  shading *no gradients*, view angle, mood); (2) generate ONE style sheet and pick the best as the
  reference; (3) use img2img/style-reference with a **fixed seed** for the rest; (4) extract swatches and
  **recolor every off-palette output by hand**; (5) expect a manual cleanup pass — nothing comes out
  "game-ready". Be skeptical of tools promising "guaranteed" consistency.
- **Steam AI disclosure:** AI in *code* is exempt; AI-generated art/music/SFX/store text that *ships*
  must be declared in "About This Game". Keep your generation logs.

## Anti-slop checklist (the ways games look cheap)
- Default font (Arial/Times/system/engine) → instant loss of identity.
- Inconsistency (mixed styles, default materials, untouched AI/marketplace assets). Fix the style guide
  *before* generating; edit every output by hand.
- Contrast by hue instead of value → the character disappears when the background changes.
- Over-detailed backgrounds competing with the action.
- Multicolor/gradient/over-detailed mascot → fails the 32px silhouette test, blocks color-swap variants.
- Raw number going up as a generic scoreboard → give magnitudes meaning (color/sound/text shift).
- "AI look": purple-blue gradients, drop-shadow on everything, card-inside-card, generic emoji. Use flat
  fills, one soft shadow, one radius, tabular digits.
- Centering the player when the interesting thing is off-screen; fixed per-frame lerp.
- Cultural/theme clichés (lazy stereotypes) instead of the specific and real.

## How to apply (build or review)
1. Build the one-screen moodboard; lock master palette (tokens) + font. Day one.
2. Run the 32px silhouette test on the player/mascot against every background.
3. Decide the reserved reward/danger color and the fixed accent.
4. Produce the repeating art as tokenized SVG/canvas; reserve bitmaps/AI for hero/reference art.
5. Check cohesion: one font/shadow/radius/line-weight across button, number, card, character.
6. Give the shareable moment the same palette/font as gameplay, and make it read on its own.

## Reference games
Alto's Adventure, Monument Valley (palette/shape/mood) · PEAK (flat low-poly) · Downwell (vertical
framing, reserved reward color) · SteamWorld Dig / Motherload / Mr. Mine (depth, cross-section) ·
Among Us / Fall Guys (blob mascot, emotion by posture, color-swap virality) · Suika (no hero mascot,
"cute that frustrates" meme).
