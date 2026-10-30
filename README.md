# skills

A collection of Claude skills. Each skill lives in its own folder with a `SKILL.md`.

## Skills

**Finding what to build** — recurring agents that hunt and validate ideas before you build:

| Skill | What it does | Scope |
|-------|--------------|-------|
| [`apps-ideas-routine/`](apps-ideas-routine/) | A **daily autonomous routine** (Grok Bot, Claude scheduled tasks or any agent with a persistent workspace) that starts from **who already pays and complains**, keeps all state in **SQLite with database-enforced guards**, validates without talking to users (public data → fake-door landing → paid test → real checkout → paywalled MVP) and only then proposes building. Ships with schema, queries, a tested calc lib and 66 sourced benchmarks. | Web & mobile apps |
| [`games-ideas-routine/`](games-ideas-routine/) | A **daily autonomous routine** for small games (web portals like Poki/CrazyGames, Steam, mobile, Roblox/UEFN) that starts from **loops already proven** (platform arbitrage, genre cohorts, jams) plus a structural twist, keeps all state in **SQLite with database-enforced guards**, validates by **measured player behavior** (portal playtests → Steam page/demo → paid tests only when they buy a real sample), picks the engine per idea and aims at a portfolio in net R$/hour, not MRR. Ships with schema, queries, a tested calc lib, 65 sourced benchmarks and a 352-test suite. | Games |
| [`oss-ideas-routine/`](oss-ideas-routine/) | A **daily autonomous routine** for open-source repos meant to **earn GitHub stars**, not money. It starts from **measured demand** (issues with hundreds of 👍 the maintainer refused, abandoned popular tools, tool requests on HN), cuts by category hit rate and maintenance load, keeps all state in **SQLite with database-enforced guards**, runs a launch-readiness gate, and judges each launch on **organic stars after the owner's own posts** (E14/E30/E90, two channels before a kill, net of any pre-launch pace). Ships with schema, queries, a tested calc lib, 63 sourced benchmarks and a 128-test suite. | Open source |

**Once you're building** — together these are the "impeccable + taste-skill, but for games":

| Skill | What it does | Scope |
|-------|--------------|-------|
| [`game-feel/`](game-feel/) | How the action **FEELS** — the feedback/juice layer (easing, number-pop, trauma-based screenshake, hit-stop, particles, sound). | Shared (2D & 3D) |
| [`game-taste-2d/`](game-taste-2d/) | How a 2D game **LOOKS** — art direction (palette, value-based legibility, composition, mascot, camera/parallax, HUD/typography, anti-slop). The "taste-skill for 2D games". | 2D |
| [`game-taste-3d/`](game-taste-3d/) | How a stylized/low-poly 3D game **LOOKS** — art direction (palette, lighting & post, materials/shaders, silhouette & modeling, 3D camera, web/Steam pipeline, anti-slop). The "taste-skill for 3D games". | 3D |
| [`game-polish/`](game-polish/) | The whole-build **audit/polish pass** (feel, art, readability, onboarding, performance, mobile, accessibility, audio, the shareable moment) → a prioritized fix list. The "impeccable for games". | Shared (2D & 3D) |
| [`roblox-game-qa/`](roblox-game-qa/) | The **Roblox QA + refinement pass** to run before publishing/updating an experience or after a playtest: ordered passes (audit, play critique, harden, adapt, polish, publish, feedback loop) over build/tests (Rojo, Luau checks, Lune), every device and input (phone, tablet, desktop, console; touch, mouse/keyboard, gamepad), ProximityPrompts and camera, game flow, server authority and remotes, visuals/audio, performance, text filtering/compliance and publishing. 0-4 scores, P0-P3 severity, an anti-pattern catalog and a release gate with real-device and real-player checks. Method adapted from [Impeccable](https://github.com/pbakaus/impeccable). | Roblox |
| [`mobile-app-qa/`](mobile-app-qa/) | The **find → fix → re-verify QA pass for mobile apps** that leaves both the looks and every feature working: feature inventory from the code, functional E2E (Maestro, two accounts, offline/sync, calculations), a mandatory **live pass** (real sign-ups, emails in real inboxes, DB rows checked by SQL, RLS, FCM push on devices, deletion, cleanup), an adb + Maestro **matrix sweep** (light/dark × locales × font scale × screen size) with screenshot/UI-text detectors, locale-convention research (CLDR, verified on device) and translation-quality review before shipping a language, theming, insets, accessibility, resilience, performance and release config. 0-4 scores, P0-P3 severity, an anti-pattern catalog and a release gate on a real mid-range phone and the Play test-track build. Ships with sweep scripts, Maestro flows and templates. Method adapted from [Impeccable](https://github.com/pbakaus/impeccable). | Mobile apps (Expo/RN, Android first) |

> `game-taste` is split by dimension because 2D and 3D art direction differ a lot (`-2d` = palette,
> silhouette, flat/parallax; `-3d` = lighting, materials/shaders, low-poly modeling, 3D camera).
> `game-feel` and `game-polish` are dimension-agnostic, so they have no suffix.

**Once it's built** — getting it found and spreading:

| Skill | What it does | Scope |
|-------|--------------|-------|
| [`play-store-aso-growth/`](play-store-aso-growth/) | The **Google Play ASO + growth playbook**: how Play search and ranking work (what gets indexed, keyword density, relevance vs. quality signals), a listing checklist (title/short/full description, icon, screenshots), custom store listings and A/B experiments, ratings via the In-App Review API, the Android vitals and core-value thresholds that cut visibility, the 12-tester/14-day closed test → production launch plan, invite/share loops with Install Referrer, cross-channel and paid (Google Ads) options, and the policy traps that get apps removed. Every rule tagged as Google-sourced fact or industry heuristic; costs flagged. Ships with a fill-in listing template. | Android apps (Google Play) |
| [`roblox-game-growth/`](roblox-game-growth/) | The **Roblox discovery + growth playbook** ("how do I make my Roblox game go viral"): how Home's Recommended-for-You ranks games (play-through rate, first-play bounce, play days, playtime, co-play, spend — only organic RFY users count), the store page that converts (16:9 thumbnails + video, thumbnail personalization A/B, 512×512 icon, title, hook-first description, genre, auto-translation, maturity label and Kids/Select reach), the launch → measure → iterate loop on Creator Analytics, growth channels (invite prompts, referral rewards, share links, events, notifications, Moments, YouTube/TikTok creators, Today's Picks/Standout, Ads Manager), live-ops cadence, 2025-2026 case studies and the policy traps (clickbait, giveaways, botting, off-platform links). 0-4 readiness scores, a growth gate, every claim tagged [ROBLOX]/[DATA]/[CASE]/[HEURISTIC], spending flagged 💲. Ships with fill-in templates. | Roblox |

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
