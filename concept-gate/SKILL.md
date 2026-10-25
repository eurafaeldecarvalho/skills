---
name: concept-gate
description: >-
  A go / no-go gate you run BEFORE building any game or app concept — the checkpoint that stops you
  pouring days into something that cannot spread or sell. Use it the moment an idea is picked and before
  a single line of product code: when choosing between ideas, when the user says "let's build X", when a
  build already underway "feels strategically off", or when asked whether something will go viral or
  sell. It scores the concept against a fixed virality + buildability rubric, applies hard fails for the
  patterns that have no distribution engine (solo/idle loops, "it'll sell" with no reach answer, ideas
  the market already killed), checks the concept against the owner's actual goal, and returns GO /
  FIX-FIRST / SKIP with reasons. It is a concept gate, not a polish pass — for finishing a build use
  `game-polish`; for feel use `game-feel`; for art use `game-taste-2d` / `game-taste-3d`.
---

# Concept gate (decide if it spreads *before* you build it)

This is the cheapest skill in the kit and the one that saves the most money. It runs **once, up front**,
on a concept — before design, before code, before art. Its whole job is to answer one question honestly:

> **Does this thing have a reason to spread and a reason to exist — or are we about to make something
> well that nobody asked for and nobody will share?**

## The one rule that would have saved the last project

**Virality is a property of the concept, not a polish you add later.** You cannot juice, animate, or
art-direct distribution into a thing that has no distribution engine in its *core loop*. Decide whether
it spreads first. If the core verb is one person doing something alone, there is nothing to spread no
matter how good it feels.

> **Postmortem baked into this skill — "Cava até o Japão":** a solo click-to-descend game. Scored Tribo
> (the social axis) = 0. The one viral surface (a shareable antipode card) existed but was buried behind
> minutes of filler clicking nobody would sit through. The concept ("dig to the other side of the
> Earth") already existed for free (antipode maps, "Dig to China") and its one paid version was rated
> 1.0/5. The gate would have returned **SKIP, or FIX-FIRST → strip to the social daily challenge.**
> Instead it got built and polished. That is the exact mistake this skill exists to prevent.

## How to run the gate

Work in this order and **stop at the first hard fail** — do not score-polish a concept that already
failed a gate.

### Step 0 — State the owner's real goal, out loud
Write the goal in one sentence (e.g. *"a cheap, multiplayer/social game that spreads organically in
Brazil"*). Then ask: **does this concept actually serve that goal, or did we drift?** Drift is the most
common failure and the hardest to see from inside a build you're enjoying. If the concept is a different
category than the goal (goal = multiplayer; concept = solo clicker), that is a flag on its own — name it.

### Step 1 — Score it with the fixed rubric (so ideas are comparable)
Reuse the house rubric (see `rotina-ideias-virais/PROMPT-PARA-O-BOT.md` for the full version):

- **VIRAL (0–3 each, max 12):**
  - **A — Attention:** is the wave rising *now* and are we early?
  - **B — Tribe:** does it split people into sides / fandoms / rivalries? (solo = 0)
  - **C — Anchor:** is there a place/person/ritual everyone already understands (zero tutorial)?
  - **D — Emotion:** high-activation emotion (laughter, rage, tension, awe, euphoria)?
- **EXECUTION (0–3 each, max 9):** Cost · Organic distribution · Speed to MVP.

Promote only if **VIRAL ≥ 9/12 AND EXECUTION ≥ 7/9**. Below that it is not a GO on score alone.

### Step 2 — Apply the hard fails (any one = not a GO)
These are auto-fails. A concept that trips one goes to FIX-FIRST (if the fix is obvious) or SKIP:

1. **No engine to spread.** Tribe = 0 **and** no standardized shareable artifact in the loop. The thing
   has no way to recruit the next player. (This is what killed the last project.)
2. **"It'll sell" with no reach answer.** Confusing *good* with *discoverable*. If you can't answer "how
   do the first 1,000 users find this without paying?", there is no business yet.
3. **Solo + repetitive core verb with the payoff only at the end** (clicker/idle). The loop is filler;
   the one good moment is gated behind tedium. Clickers that scaled were almost all *free* novelties, or
   rode a pre-existing brand (Cookie Clicker had 10 free years first). New paid ones make ~$5k and vanish.
4. **The market already answered.** The concept already exists and is free, dead, or badly rated. Someone
   ran the experiment for you — read the result before re-running it.
5. **Viral confused with profitable, or vice-versa.** They are two different questions. Answer both
   explicitly; a thing can spread and not earn, or earn quietly and never spread.

### Step 3 — Require the two concrete answers
A concept that passes the gates must still answer these, specifically, not hand-wavily:

- **Organic reach:** how do the first 1,000 users find this *without paid ads*? (which Brazilian
  creators / communities / platforms, what clip, why it spreads). No concrete answer → not a GO.
- **The "Wordle square":** what is the standardized, spoiler-free artifact the user posts after every
  session that works as an ad on its own, readable by someone who never played? If there isn't one,
  that's usually the first thing to design — not an afterthought.

## Output format

Return a short, decisive verdict — never a wishy-washy "it could work":

```
VERDICT: GO | FIX-FIRST | SKIP
Owner goal: <one line> — concept serves it? yes / drifted (how)
Scores: VIRAL x/12 (A/B/C/D) · EXECUTION y/9 (cost/distrib/speed)
Hard fails tripped: <none | which ones>
Reach answer: <the concrete first-1,000 plan, or "missing">
Shareable artifact: <the Wordle square, or "missing">
```

- **GO:** passes the score and all gates, both answers concrete. Say the single biggest risk anyway.
- **FIX-FIRST:** the idea has a live core but trips a gate. State the **smallest change** that would make
  it pass (usually: add the tribe/competitive layer, or cut the filler so the shareable moment is the
  product). Re-run the gate on the fixed version.
- **SKIP:** trips a gate with no cheap fix, or the market already answered. Say why in one line, and point
  to the nearest adjacent idea that *would* pass.

## Anti-patterns (of running the gate, and of ignoring it)

- **Building first and rationalizing later.** The gate is worthless if you run it after the code exists
  and grade on a curve to justify the work. Run it at idea-time, cold.
- **Letting a fun mechanic smuggle in a concept with no distribution.** "But the digging *feels* good" is
  not a reason to ship a thing that can't spread. Feel amplifies reach; it doesn't create it.
- **Agreeing with enthusiasm instead of gating.** When the owner is excited, the gate's job is to confirm
  or push back *with evidence* — not to cheerlead. A gate that always says GO is not a gate.
- **Treating "viral" and "sells" as the same check.** Score and answer both.
- **Vague verdicts.** "Has potential" helps no one. GO / FIX-FIRST / SKIP, with the reason.
- **Skipping Step 0.** Most drift is invisible until you write the goal next to the concept and see they
  are different categories.
