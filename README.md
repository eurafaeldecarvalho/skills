# skills

A collection of Claude skills. Each skill lives in its own folder with a `SKILL.md`.

## Skills

**Before you build** — the go / no-go gate that decides if a concept can spread at all:

| Skill | What it does | Scope |
|-------|--------------|-------|
| [`concept-gate/`](concept-gate/) | Run **before a single line of product code**: scores a game/app concept against a fixed virality + buildability rubric, hard-fails ideas with no engine to spread (solo/idle loops, "it'll sell" with no reach answer, ideas the market already killed), checks it against the owner's real goal, and returns **GO / FIX-FIRST / SKIP**. Stops you polishing something nobody will share. | Game & app concepts |

**Finding what to build** — a recurring agent that hunts and validates paid app ideas before you build:

| Skill | What it does | Scope |
|-------|--------------|-------|
| [`apps-ideas-routine/`](apps-ideas-routine/) | A **daily autonomous routine** (Grok Bot, Claude scheduled tasks or any agent with a persistent workspace) that starts from **who already pays and complains**, keeps all state in **SQLite with database-enforced guards**, validates without talking to users (public data → fake-door landing → paid test → real checkout → paywalled MVP) and only then proposes building. Ships with schema, queries, a tested calc lib and 66 sourced benchmarks. | Web & mobile apps |

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
