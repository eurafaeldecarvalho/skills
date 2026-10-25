---
name: game-polish
description: >-
  Audit and polish a game build to a high bar across every dimension that makes a game feel finished —
  the "impeccable, but for games". Use whenever reviewing or improving a game (especially 2D/web) as a
  whole: when the user says "make it feel more polished", "something's off", "it feels unfinished/cheap",
  "get it ready to ship/demo", or asks for a quality/polish pass or review; and before publishing a demo
  or launch. It runs a structured pass over feel, visual art direction, readability, first-time UX,
  performance, mobile/touch, accessibility, audio, the shareable moment, and consistency, and returns a
  prioritized list of concrete fixes. Composes the `game-feel` (motion/juice) and `game-taste`
  (art direction) skills — reach for those directly when the work is only about one of those.
---

# Game polish (the quality pass for games)

This is a **review-and-improve pass**, not a from-scratch builder. Like a good design review, it goes
dimension by dimension over an existing build, finds what makes it feel unfinished, and returns a
**prioritized, concrete fix list** — then applies the fixes if asked. It composes two sibling skills:
**`game-feel`** (how the action feels) and **`game-taste`** (how the game looks). Load those when a
finding is squarely in their domain; this skill is the whole-build sweep that ties them together.

Core idea: "polish" is not one big thing, it's ~40 small things each 1% better. Find them, rank them by
impact-vs-effort, fix the cheap high-impact ones first.

## How to run the pass
1. **See it actually running first.** Play/observe the real build (or watch a capture). You cannot
   polish from the code alone — feel and look only exist in motion.
2. Go through the dimensions below, writing one finding per issue: what's wrong, why it matters, and the
   concrete fix (with values where relevant).
3. **Rank every finding P0/P1/P2** (see priorities) and sort by impact-vs-effort.
4. Report the list. On request, apply fixes **one at a time**, re-checking feel after each — never a big
   undifferentiated polish commit.

## The dimensions (sweep in this order)

### 1. Feel / juice  → defer to `game-feel`
Does every core action have easing, a satisfying response, feedback? Is there number-pop (pooled),
milestone screenshake (trauma-based, reserved for milestones), hit-stop on impact (local, not global
timescale), a crisp SFX with pitch variation? Does the shareable moment have its own juice? Flag
missing or overdone juice.

### 2. Look / art direction  → defer to `game-taste`
Is the palette locked (<15 colors, fixed accent)? Does the player pass the 32px silhouette test against
every background? Is detail concentrated in the action zone, backgrounds flat? One font with character
(no system default)? One shadow/radius/line-weight? Does the UI match the sprites? Any "AI look"
(purple gradients, drop-shadows everywhere, card-in-card)?

### 3. Readability & game clarity
Can a new player tell, at a glance, what to do, what's interactive, what just changed, and what the
current goal is? Is the hero metric obvious? Is anything communicated by color alone? Is text legible at
the real play distance / on a phone?

### 4. First-time experience (onboarding)
From a cold open: how many seconds to the first meaningful action, and to the first "aha"? Is there a
tutorial wall, or does it teach by doing? Does the core loop hook within ~2 minutes? (If not, that's a
design problem, not a polish one — say so.)

### 5. Performance / frame budget
Holds 60fps / ~16ms? Any per-frame allocations, unpooled spawns (number-pop, particles), layout
thrash? Load time (the real driver of reach on web — keep the bundle/assets small, no runtime downloads
of big data)? Particle counts capped?

### 6. Mobile / touch  → see `mobile-native` for web
Touch targets ~44px? No 100vh bug, no pull-to-refresh hijack, no tap-highlight flash, no input zoom, no
long-press selecting button text? Content clear of the notch? Works one-handed? Tested on real hardware,
not just a desktop resize.

### 7. Accessibility
`prefers-reduced-motion` honored (shake/flash scale down)? Contrast ~4.5:1 for text? Info never by color
alone? Remappable/forgiving input? Pause/mute reachable?

### 8. Audio
Is there audio at all (silence reads as unfinished)? Master mute + volume? SFX pooled and pitch-varied
so repetition doesn't fatigue? Milestone sound distinct from the common-action sound? Does music loop
seamlessly?

### 9. The shareable moment
Does the game manufacture a frame people want to screenshot/post? Is it funny/impressive **on its own**
(readable by someone who never played)? Same palette/font as gameplay? Exports cleanly (no CORS taint,
with a download fallback)? This is distribution — it earns extra polish.

### 10. Consistency & finish
Empty states, error/edge states, win/lose screens, settings, pause — all styled to the same bar as the
main screen? Copy in one voice? No placeholder text, no lorem, no default engine splash?

## Priorities
- **P0 — breaks the experience or the first impression:** unreadable core action, no audio, janky
  framerate, broken on mobile, the shareable moment is confusing or ugly, default font/engine look.
- **P1 — noticeably unfinished:** missing juice on the core loop, weak onboarding, inconsistent states,
  no reduced-motion, number-as-raw-scoreboard.
- **P2 — nice-to-have refinements:** extra particles, secondary transitions, flavor polish.

## Output format
Report findings as a ranked list, most impactful first:

```
P0 — [dimension] short title
  Problem: what's wrong (observed, not theorized).
  Why it matters: the effect on the player / on virality.
  Fix: concrete change, with values. (→ game-feel / game-taste if it lives there.)
```

End with a one-line verdict: is this shippable as a demo, and the top 3 things to fix first.

## Anti-patterns of the review itself
- Reviewing from the code without seeing it run.
- A flat dump of 50 findings with no priority — the user can't act on it.
- Vague notes ("make it pop") instead of a concrete fix with values.
- Polishing a core loop that isn't fun yet — fix the fun first; polish amplifies, it doesn't rescue.
- One giant "polish" commit — apply and feel one change at a time.
- Gold-plating P2s while P0s remain.
