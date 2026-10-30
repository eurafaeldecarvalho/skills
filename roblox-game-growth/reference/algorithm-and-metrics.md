# Algorithm and metrics (how Home recommendations decide, and what to measure)

Roblox rules change often; this is accurate at writing time (late 2026). Re-read
[Discovery](https://create.roblox.com/docs/discovery) and the [Discovery FAQ](https://create.roblox.com/docs/discovery-faq)
before acting on a specific number.

## How Recommended for You (RFY) works [ROBLOX]
Two stages:
1. **Retrieval (consideration).** Any traffic helps the system notice a game: sponsored ads, curation,
   search, charts, friends, teleports, notifications, social-media sharing. "Even a small number of people
   playing" can make a game worth testing.
2. **Ranking (how far it goes).** Depends **entirely** on engagement/retention of users who came
   **organically from RFY**. Users first acquired by ads, curation, friends, search or social media are
   not counted at this stage.

Explore → expand: after an update you may see a spike of RFY users (explore). If that cohort engages and
monetizes, the system keeps showing the game to more similar cohorts (expand). After a jump in
distribution, expect your signals to fluctuate and settle at a new baseline (wider audience = fewer
superfans per impression).

Impressions depend on 4 factors: (1) what you change in the game, (2) what Roblox changes in the
algorithm, (3) how many people visit Home (weekly peak usually **Saturday**, summer/back-to-school and
holiday seasonality), (4) how well *other* games engage. Your traffic can fall while your signals stay flat.

## Signals (all per-user averages, RFY users only) [ROBLOX]
| Priority | Signal | Window |
|---|---|---|
| Most important | **Play-through rate (PTR)**: plays ÷ RFY impressions (qualified PTR filters accidental clicks) | first session |
| Most important | **First-play bounce rate** (negative): leaving after a short first session | < 60 s and 61-180 s |
| Most important | **Play days per user** | D1, D2-7 (avg days out of 6), D8-28 |
| Most important | **Playtime per user** (capped at 60 min per user per game per day) | D1, D2-7, D8-28 |
| Important | **Intentional co-play days**: days returning to play with friends (join, invites, private servers) | same |
| Important | **Qualified play sessions per user** | same |
| Important | **Spend days per user**, **Robux spent per user** | same |

What the FAQ adds [ROBLOX]:
- No single signal decides ranking. Fix retention first, then monetization; being strong in only one still earns impressions.
- New games get signals right away (no 28-day wait); weak early performance is not a permanent penalty
  (moving windows, daily testing), and old games can grow again.
- Finite/story games are not penalized for ending. Genre is not a ranking factor, but an accurate genre
  and a video reduce bounces from mismatched expectations.
- Benchmarks are for comparison only; they don't affect ranking.
- After ads, RFY impressions can dip because ad-acquired users are "already acquired": not a penalty.
- Reduced exposure (giveaway-led metadata, mismatched metadata, near-copies) shows a **banner** on the
  Creator Dashboard, updated daily. Among near-identical games, the original is favored.
- Capping playtime at 60 min/day means **getting players back on more days** is worth more than ever-longer sessions.

## What to read in Creator Analytics [ROBLOX]
- **Acquisition ▸ Home Recommendations**: impressions, plays, PTR, bounce, play days, playtime vs your benchmark.
  Pick the benchmark set (similar experiences or genre) — [DevForum 4010157](https://devforum.roblox.com/t/4010157).
- **Acquisition sources**: Home recs, Continue, Today's Picks, Home other, Friends, Search (incl. the
  details-page "Recommended"), Charts, Sponsored/Search/Portal ads, Teleport, Other (external links).
- **Retention**: cohorts by first-play date, D1/D7/D30, view **by acquisition source**. A dip after a big
  influx is normal. D1 is moved by core loop, FTUE and performance; D7 by progression and content depth.
- **Funnels** ([funnel events](https://create.roblox.com/docs/production/analytics/funnel-events)):
  `AnalyticsService:LogOnboardingFunnelStepEvent(player, step, stepName)` for the one-time first session;
  `LogFunnelStepEvent(player, funnelName, funnelSessionId, step, stepName)` for recurring loops (a round,
  a shop visit). Server-only, published games only, limited number of funnels. Plus custom and economy events.
- **Experiments and Configs** (onboarding doc): A/B-test values and matchmaking, tune live without a republish.

## Target metrics (how to set them without inventing numbers)
1. **Primary target: at or above your similar-experience benchmark** in the Home Recommendations tab, for
   PTR, < 60 s bounce, D1 play days and playtime. This is the only benchmark Roblox computes for you. [ROBLOX]
2. **Context ranges** from the GameAnalytics *2025 Roblox Benchmark Report* (games with > 1M MAU, Jan
   2023-Jul 2025; skews to large games; its D7/D30 definitions are stricter than Roblox's play-days) [DATA]:

| Avg session length | Median D1 | Top-decile D1 |
|---|---|---|
| 0-3 min | ~4% | < 10% |
| 4-6 min | ~6% | ~11-13% |
| 7-12 min | ~8% | low teens |
| 13-18 min | ~10% | ~15-20% |
| 25+ min | — | top games keep nearly 1 in 4 |

   Same report: the median player opens a game ≥ 2 sessions/day (top decile ~6); ~48% of players use both
   PC and mobile; advice is to design for 3-7 min bursts, staged timers and co-play as the optimal path.
   Use these as sanity checks, not goals.
3. **Your own trend**: the next iteration should move the worst funnel step. Write down the expected
   direction before shipping.

## Diagnosis table [HEURISTIC, built on ROBLOX signal definitions]
| Symptom | Likely cause | First fix |
|---|---|---|
| Low PTR, normal bounce | Thumbnail/icon/title don't sell | New distinct thumbnails + personalization; clearer genre word in title |
| High PTR, high < 60 s bounce | Store page over-promises, or slow/confusing spawn | Make the first 30 s match the thumbnail; cut loading/menus; fix mobile |
| Bounce 61-180 s | Fun arrives too late, or first failure feels unfair | Earlier first win; shorter first round; better teaching |
| Good D1, weak D2-7 | No mid-term goals | Progression, collections, daily/weekly content, notifications opt-in |
| Good solo metrics, low co-play | Inviting isn't rewarded | Invite prompt at a high point, referral rewards, duo roles |
| Impressions fall, signals flat | Seasonality or competitors | Ship an update/event; wait; check the banner |
| Banner "reduced exposure" | Metadata issue | Remove giveaway wording, align thumbnails with gameplay, de-duplicate |
