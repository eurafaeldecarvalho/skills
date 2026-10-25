---
name: game-feel
description: >-
  Make a game (or game-like interaction) FEEL good — the "juice" / game feel layer that separates a
  cheap-feeling prototype from a satisfying, shareable game. Use this whenever building, polishing, or
  reviewing a game, especially 2D/web (HTML5, Canvas, PixiJS, Phaser): when adding juice, feedback, or
  "game feel"; when a game, click, hit, pickup, score, or progress bar feels flat, stiff, cheap, dead,
  or unsatisfying; when adding screenshake, hit-stop/freeze-frame, particles, easing/tweening,
  number-pop / floating combat text, satisfying sound feedback, or impact animation; when deciding how
  to make a minimalist game look premium and read cleanly; and for incremental / idle / clicker feel
  specifically. Reach for it even when the user says "make it feel better" or "it feels off" without
  naming juice.
---

# Game feel (juice)

The gap between a prototype that feels dead and a game people compulsively play (and clip) is almost
never the mechanics — it's the **feedback**. "Juice" is the layer of exaggerated, immediate response
the game gives to every input: the screen shakes, numbers pop, things squash and ease, sounds fire.
It is the game-dev equivalent of a polished UI. This skill is the checklist and the reasoning for
adding it well.

Core references worth knowing: Martin Jonasson & Petri Purho, *"Juice it or lose it"*; Jan Willem
Nijman (Vlambeer), *"The Art of Screenshake"*; Steve Swink, *Game Feel*.

## The one rule that governs everything

**Feel is a deliberate pass you make AFTER the loop works, one effect at a time, with every value
exposed as an editable constant.** Don't scatter magic numbers through the code. Put
`SHAKE_TRAUMA_PER_HIT`, `POP_RISE_PX`, `HITSTOP_MS`, `TICK_PITCH_JITTER` in one tunable config, add
effects one by one, and feel the difference each makes. The final values come from **playtesting**,
not from theory — so make them trivially cheap to change.

Why this matters: juice is easy to overdo. Added all at once with hardcoded numbers, you can't tell
what helped and you end up with a noisy, laggy mess. Added one layer at a time, you keep only what
improves the feel.

## The layers, in the order you should add them

Add them roughly top to bottom. Each assumes the previous ones exist.

### 1. Easing on everything (the foundation)
Nothing teleports or snaps. Every bar, counter, panel, camera move, and value change interpolates
with an ease. If one thing is instant and everything else eases, the instant thing feels broken.
- Use a tween lib (GSAP on web is excellent and free) or a tiny `lerp`/easing helper.
- The **ease curve is personality**: `ease-out` for things arriving, `back`/`elastic` for playful
  pop (they give you squash & stretch for free), `ease-in-out` for camera.
- Typical UI durations: 120–300ms. Longer feels sluggish; instant feels cheap.

### 2. Number-pop / floating text (highest ROI, especially for incrementals)
A game that is "numbers going up" lives or dies on how the numbers appear. Every gain spawns a
floating number that scales up fast, drifts/arcs upward, and fades out. Crits/milestones get a bigger
scale and an accent color.
- **Object-pool these** — recycle a fixed set of text objects, never create/destroy per number, or
  you get GC stutter. This is a requirement, not an optimization.
- If the screen floods (rapid gains), switch to a **combine mode**: merge fast hits into one number
  that keeps growing, instead of 50 overlapping labels.

### 3. Screenshake by decaying "trauma" (never fixed random shake)
Keep a `trauma` float (0–1). Strong events ADD to it (`trauma += 0.4`). Each frame, offset the camera
by `maxOffset * trauma²` (squaring makes small trauma subtle, big trauma violent) in a random/`noise`
direction, then decay `trauma -= decay * dt`. Shake² feels far better than linear.
- Vlambeer starting point: camera kicks back ~6px on a hit, add ~4 "units" of shake with fast decay.
- **Reserve shake for impact and milestones**, not every frame/click — constant shake reads as a bug
  and causes motion sickness. Respect `prefers-reduced-motion` with a scale multiplier the player can lower.

### 4. Hit-stop / freeze-frame (50–100ms) on real impacts
On a meaningful impact (a kill, a breakthrough, a big milestone), freeze the involved elements for
50–100ms, scaling duration with force. This sells weight more than any animation.
- **Never set a global timescale to 0** — that freezes UI, audio, and tweens and looks like a crash.
  Freeze only the elements involved, and run the un-freeze timer on **real/unscaled** time.

### 5. Particles — with a hard cap and pooling
Dust, sparks, debris, a burst on pickup. They add life but are the easiest way to tank the frame rate
and muddy a clean look. Enforce a max count, pool them, and keep bursts short. In a minimalist art
style, restraint reads as premium; confetti everywhere reads as cheap.

### 6. Sound: a short, satisfying "tick" with pitch variation
The primary action (click, dig, step, shoot) needs a crisp SFX with slight random pitch jitter so it
doesn't fatigue on repetition. Milestones get a distinct, richer sound.
- Generate SFX procedurally with **bfxr / jsfxr** (free, no AI-disclosure concerns, suits a
  minimalist style). Use Howler.js on web for pooling and audio sprites.
- Low latency matters — preload and reuse buffers; never `new Audio()` per hit.

### 7. Flash, anticipation, and small loving details (sparingly)
A brief white/accent flash on a milestone, a few frames of wind-up before a big action, a tiny camera
punch-in on reveal. "Fill it with love and small details" — but in a flat, minimalist game, **less is
more**. One tasteful detail beats five competing ones.

### 8. Frame budget is a feature, not an afterthought
Everything above must fit in 60fps / ~16ms per frame. "Light and smooth" is part of what makes a game
feel good and is what makes it load and run everywhere (the real driver of reach). Profile; pool;
avoid per-frame allocations; keep the draw calls and particle counts bounded.

## Making a minimalist / "light" game look premium

Clean low-poly/flat games (think the readable, uncluttered look of games like PEAK) feel expensive
because of **art direction, not graphical fidelity** — which also keeps them light.
- **Lock the palette to <15 colors**: roughly shadow / mid / light / one accent / white. Fewer
  colors, used consistently, read as intentional.
- **Contrast by VALUE before hue.** Squint: the important thing should be the lightest or darkest.
- **Max saturation only on the hero element**; everything else desaturated. This directs the eye.
- **Flat shading / simple shapes.** Detail goes into feel and motion, not texture.
- Decide this on day one and hold it — retrofitting a palette is painful.

## The shareable moment deserves its own juice
If the game has a "money shot" (a result card, a win screen, a reveal) that people screenshot and
post, treat that moment as a first-class feature: ease into it, reveal with a pop, let it breathe.
That frame is the game's distribution — it earns extra polish.

## Anti-patterns (the usual ways feel goes wrong)
- Global `timeScale = 0` for hit-stop → freezes UI/audio, looks broken.
- Spawning/destroying number-pop or particles per event → GC stutter.
- Constant or fully-random screenshake → reads as a bug, nauseating.
- Instant snaps mixed with eased motion → the snap feels broken.
- Hardcoded magic numbers everywhere → can't tune, so it never gets good.
- Juice piled on before the core loop is fun → polishing something that isn't working yet.
- Ignoring `prefers-reduced-motion` and accessibility.

## How to apply this in a review or build
1. Confirm the core loop is actually fun first. If it isn't, fix that before juicing.
2. Pull every feel value into one tunable config.
3. Add the layers in order (1→8), one at a time, feeling each before the next.
4. Playtest for the specific question: *does the core action feel good on its own, repeated 50 times?*
5. Give the shareable moment extra love.
6. Check the frame budget and reduced-motion.
