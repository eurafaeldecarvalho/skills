# skills

A collection of Claude skills. Each skill lives in its own folder with a `SKILL.md`.

## Skills

Together these are the "impeccable + taste-skill, but for games":

| Skill | What it does | Scope |
|-------|--------------|-------|
| [`game-feel/`](game-feel/) | How the action **FEELS** — the feedback/juice layer (easing, number-pop, trauma-based screenshake, hit-stop, particles, sound). | Shared (2D & 3D) |
| [`game-taste-2d/`](game-taste-2d/) | How a 2D game **LOOKS** — art direction (palette, value-based legibility, composition, mascot, camera/parallax, HUD/typography, anti-slop). The "taste-skill for games". | 2D |
| [`game-polish/`](game-polish/) | The whole-build **audit/polish pass** (feel, art, readability, onboarding, performance, mobile, accessibility, audio, the shareable moment) → a prioritized fix list. The "impeccable for games". | Shared (2D & 3D) |

> `game-taste` is split by dimension because 2D and 3D art direction differ a lot. A `game-taste-3d`
> counterpart covers 3D (lighting, materials, low-poly, shaders). `game-feel` and `game-polish` are
> dimension-agnostic, so they have no suffix.

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
