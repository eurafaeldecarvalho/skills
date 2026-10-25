# skills

A collection of Claude skills. Each skill lives in its own folder with a `SKILL.md`.

## Skills

**Before you build** — the go / no-go gate that decides if a concept can spread at all:

| Skill | What it does | Scope |
|-------|--------------|-------|
| [`concept-gate/`](concept-gate/) | Run **before a single line of product code**: scores a game/app concept against a fixed virality + buildability rubric, hard-fails ideas with no engine to spread (solo/idle loops, "it'll sell" with no reach answer, ideas the market already killed), checks it against the owner's real goal, and returns **GO / FIX-FIRST / SKIP**. Stops you polishing something nobody will share. | Game & app concepts |

**Once you're building** — together these are the "impeccable + taste-skill, but for games":

| Skill | What it does | Scope |
|-------|--------------|-------|
| [`game-feel/`](game-feel/) | How the action **FEELS** — the feedback/juice layer (easing, number-pop, trauma-based screenshake, hit-stop, particles, sound). | Shared (2D & 3D) |
| [`game-taste-2d/`](game-taste-2d/) | How a 2D game **LOOKS** — art direction (palette, value-based legibility, composition, mascot, camera/parallax, HUD/typography, anti-slop). The "taste-skill for 2D games". | 2D |
| [`game-taste-3d/`](game-taste-3d/) | How a stylized/low-poly 3D game **LOOKS** — art direction (palette, lighting & post, materials/shaders, silhouette & modeling, 3D camera, web/Steam pipeline, anti-slop). The "taste-skill for 3D games". | 3D |
| [`game-polish/`](game-polish/) | The whole-build **audit/polish pass** (feel, art, readability, onboarding, performance, mobile, accessibility, audio, the shareable moment) → a prioritized fix list. The "impeccable for games". | Shared (2D & 3D) |

> `game-taste` is split by dimension because 2D and 3D art direction differ a lot (`-2d` = palette,
> silhouette, flat/parallax; `-3d` = lighting, materials/shaders, low-poly modeling, 3D camera).
> `game-feel` and `game-polish` are dimension-agnostic, so they have no suffix.

## Install a skill (Claude Code)

Copy the skill folder into your skills directory:

```bash
# user-level skill
cp -r game-taste-2d ~/.claude/skills/game-taste-2d
```

Or drop the folder into a project's `.claude/skills/`. Claude then consults it automatically whenever
the context matches the skill's `description`.

## License
MIT — see [LICENSE](LICENSE).
