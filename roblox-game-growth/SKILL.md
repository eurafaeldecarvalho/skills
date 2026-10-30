---
name: roblox-game-growth
description: >-
  A playbook for getting a Roblox experience discovered, played, kept and shared ("how do I make my Roblox
  game go viral"): how the Recommended-for-You algorithm actually ranks games (play-through rate, first-play
  bounce, play days, playtime, co-play, spend), how to build the store page that converts (16:9 thumbnails
  and video, personalization A/B, 512x512 icon, title, description, genre, maturity label and audience
  reach), the launch sequence, the measure-and-iterate loop on Creator Analytics, the growth channels
  (invite prompts, referral rewards, share links, events, notifications, Moments clips, TikTok/YouTube
  creators, Today's Picks/Standout nominations, Ads Manager) and the live-ops cadence that keeps a hit
  alive. Use it BEFORE publishing a Roblox game publicly or pushing traffic to it, when writing or
  redoing its thumbnails/icon/title/description, when a live game "gets no players" or stopped growing,
  when planning an update, event, creator outreach or ad test, and whenever the user asks how to make a
  Roblox game viral or popular. Scores readiness 0-4, ends with a growth gate (no paid or influencer push
  before the game keeps players), tags every claim [ROBLOX] / [DATA] / [CASE] / [HEURISTIC], and flags
  anything that spends money or needs the owner's approval. Validate the concept before building and run
  `roblox-game-qa` before publishing; this skill starts where those stop.
---

# Roblox game growth (find → click → stay → return → bring a friend)

A field guide for a small team taking a Roblox experience from "published" to "growing". It turns what
Roblox officially documents about discovery, the store page and promotion tools into an ordered
playbook, and adds what recent hits (2024-2026) and third-party data show about how games actually spread.

**The model in one line.** Roblox's Home feed (Recommended for You, "RFY") is the biggest organic source
of new players, and it ranks your game almost only on **what organically recommended players do after
they see it**: do they click and play (play-through rate), do they bounce in the first minutes, do they
come back on later days, how long do they play, do they play *with friends*, do they spend. Everything
else (ads, creators, TikTok, search, events) brings people in, which gets your game *considered*; only
retention keeps it *recommended* ([Discovery][discovery], [Discovery FAQ][faq]).

**So "going viral" on Roblox is three things in order:** (1) a first session that hooks within a minute
and a reason to come back tomorrow, (2) a store page that tells the truth attractively, and (3) social
loops and outside attention that keep feeding new players into (1). Pushing traffic before (1) works
burns your audience and your money.

**Honest scope.** Nobody outside Roblox knows the weights, and nothing here guarantees a hit; most games
never get one. Roblox rules, limits and programs change often (several did in 2025-2026). Facts below
were verified on **2026-10-29**; re-check limits, age rules and program status before relying on them.
Never invent a benchmark: compare against your own **Creator Analytics benchmarks** (similar experiences
or genre), which Roblox computes for your game.

**Evidence tags**
- **[ROBLOX]**: stated in Roblox Creator Hub docs, DevForum staff announcements or Roblox newsroom. Linked in `reference/sources.md`.
- **[DATA]**: third-party aggregate data (e.g. GameAnalytics 2025 benchmark report). Good, but sample-biased.
- **[CASE]**: what a specific hit did, from interviews or press. One game's story is not a law.
- **[HEURISTIC]**: practitioner/community consensus or anecdote. Test it; don't trust it.
- **💲**: costs money or Robux → needs the owner's explicit approval before anyone spends.
- **🔞**: depends on age/verification rules for the creator or the players.

**Files in this folder**

| File | What it is |
|---|---|
| `SKILL.md` | The playbook (this file) |
| `reference/algorithm-and-metrics.md` | How RFY retrieval/ranking works, every signal, what moves impressions, target metrics, analytics setup |
| `reference/thumbnails-and-icon.md` | Thumbnail/video specs and rules, what converts, personalization A/B, icon rules, brief workflow |
| `reference/title-and-description.md` | Name, description structure, keywords, genre, localization/auto-translation, maturity label |
| `reference/social-and-virality.md` | Co-play, invite prompts, referral rewards, share links, Moments/captures, notifications, events, community |
| `reference/content-creators-and-ads.md` | YouTube/TikTok/streamers, curated sorts, Ads Manager products and objectives, Creator Rewards |
| `reference/launch-and-live-ops.md` | Launch sequence, update cadence, seasonal timing, events, update parties, copycats |
| `reference/case-studies.md` | Grow a Garden, Dead Rails, 99 Nights in the Forest, Scary Shawarma Kiosk, DOORS, Dress to Impress |
| `reference/policy-traps.md` | What gets reach cut, games moderated or accounts banned (clickbait, botting, links, giveaways, ages) |
| `reference/templates.md` | Fill-in templates: description, thumbnail/icon brief, update post, creator outreach, growth report |
| `reference/sources.md` | Every source with URL and what it supports |

---

## How to run the playbook (order matters)

| # | Step | Goal | Output |
|---|------|------|--------|
| 0 | **Context** | Read/refresh `GAME.md` (genre, loop, devices, server size, audience/age, languages, what's unfinished). Add: target players, "the clip" (the 10-second moment people would share), comparable Roblox games. | `GAME.md` growth section |
| 1 | **Readiness gate** | Score the 9 dimensions below 0-4. Fix every P0 before anything public. Run `roblox-game-qa` if not done. | scorecard + fix list |
| 2 | **Store page** | Icon, 3-5 distinct thumbnails + 1 gameplay video, title, description (hook first), genre/subgenre, maturity questionnaire, languages, social links. | store-page pack |
| 3 | **Instrument** | Onboarding funnel, core-loop funnel, key custom events, share links per channel, invite + referral wiring. Turn debug analytics off. | analytics plan |
| 4 | **Soft launch** | Public, no push. Let RFY test it; invite friends/testers; read PTR, bounce, D1 by source; fix the first session. | first-week report |
| 5 | **Iterate loop** | Weekly: read metrics → pick the worst funnel step → one change (or an Experiment) → ship → wait ≥ 7 days or until the next update → read again. | iteration log |
| 6 | **Growth gate** | Only when first-session and D1 signals are at/above your similar-experience benchmark: start pushes. | gate report |
| 7 | **Push** | Creators/clips, Today's Picks / Standout nominations, events, notifications, 💲 ads tests (owner approval). | channel log |
| 8 | **Live ops** | Fixed update rhythm, events, seasonal beats, thumbnail refresh per update, community. | update calendar |

Rules for running it:
- **Retention before reach.** RFY only counts players who arrived organically from RFY, so bought or
  borrowed traffic can't buy ranking; it only gives the game a chance to be tested [ROBLOX][faq]. Players
  from ads or outside links also tend to retain differently: Roblox shows D1 by source for this reason [ROBLOX][retention-source].
- **The store page is a promise; the first minute keeps it.** Clickbait raises clicks and then bounce,
  and bounce is a top signal. Mismatched metadata is also an explicit reason for reduced exposure [ROBLOX][discovery].
- **One change at a time, then wait.** Signals use moving windows and update over days. Staff advise
  leaving thumbnail sets alone ≥ 7 days or until the next update [ROBLOX][thumb-tips]. A temporary PTR dip
  when impressions surge is normal [ROBLOX][faq].
- **Per-user averages, not totals.** Small games aren't penalized for being small; a tiny game with
  highly engaged players can grow, and an old game can grow again [ROBLOX][faq].
- **Anything that spends money or Robux** (ads, publishing fee, expedited review, paid creator deals,
  Premium/Plus for publishing eligibility) is 💲: draft it, price it, ask the owner. Never spend on your own.
- **Never fake it.** No bots, alt accounts, paid visits/likes, fake giveaways, "free Robux" bait, or
  external links in-game. See `reference/policy-traps.md`. These end in moderation, not growth.

## Severity (for findings)
- **P0 blocks growth:** something that makes new players leave or makes Roblox cut reach: broken or
  confusing first minute on mobile, crash/soft-lock, no custom thumbnail (not eligible for Home
  recommendations), misleading metadata, policy violation, wrong maturity label for the target audience,
  matchmaking that leaves a 2-player game stuck waiting, debug overlays visible.
- **P1 wastes traffic:** weak hook in thumbnails/title, description that hides the genre, no reason to
  return tomorrow, no invite path, funnels not instrumented, no Portuguese/English (or other key) text.
- **P2 leaves growth on the table:** single thumbnail (no personalization), no video, no events/update
  cadence, no share links, no creator kit.
- **P3 nice to have:** extra locales, Moments capture prompts, group/community polish.

## Readiness scorecard (0-4 each)
0 = absent/broken, 1 = poor, 2 = works but weak, 3 = good, 4 = excellent (beats the similar-experience benchmark or is clearly best-in-genre).

| Dimension | What "4" looks like |
|---|---|
| **1. Spreadable concept** | The game is explainable in one line, has a visible "clip" moment, a familiar base with one fresh twist, and is more fun with a friend (validate the concept before building). |
| **2. First 60 seconds** | Spawn → first meaningful action in ≤ ~30 s, first win/scare/laugh in ≤ ~60 s, controls taught by doing, works on a phone in landscape. Low first-play bounce. |
| **3. Return loop** | Short/mid/long goals visible, something "about to pop" tomorrow (unlocks, collections, daily/weekly content), progress shown on rejoin. Healthy D1/D7 vs benchmark. |
| **4. Social / co-play** | Inviting a friend is the obvious best path: invite prompt at the right moment, join-friend works, party/private-server play, referral reward, roles that need two people. |
| **5. Store page** | Custom 512×512 icon, 3-5 distinct 16:9 thumbnails + authentic video, title ≤ ~30 visible chars with a clear genre word, description hook ≤ 160 chars, accurate genre/subgenre. |
| **6. Audience & compliance** | Maturity questionnaire matches content; the label lets the target ages in (see `title-and-description.md`); no off-platform links in-game; text filtered; copyright-clean audio. |
| **7. Measurement** | Onboarding + core funnels and custom events live; share links per channel; benchmark set chosen; weekly report habit. |
| **8. Live-ops readiness** | Content pipeline for a regular update, events set up in Creator Hub, notification strings, a thumbnail refresh plan per update. |
| **9. Clip-ability / creator fit** | Moments that look good recorded (reactions, chaos, rare drops, jump scares), streamer-friendly pacing, no copyrighted music, a creator kit (key art, short description, codes). |

**Gate thresholds.** Public release with no push: no P0 and dimensions 2, 5, 6 ≥ 3. **Growth gate** (start
creators/ads/outreach): additionally 3 and 4 ≥ 3, 7 ≥ 3, and PTR, first-play bounce and D1 at or above the
similar-experience benchmark for at least a week of RFY traffic. Average ≥ 3.0 with no dimension < 2.

---

## Condensed checklists

### A. Before going public (see `reference/policy-traps.md`, `reference/title-and-description.md`)
- [ ] `roblox-game-qa` release gate passed; debug flags (analytics debug, test overlays) off.
- [ ] Owner account in good standing ≥ 2 days and age-checked; experience published to the right
  **audience** (Playtest / Friends / Public) [ROBLOX][publish].
- [ ] Maturity & compliance questionnaire answered **fully and honestly**. If you only answer the first
  question, the default is "Content May Vary", visible only to age-checked 16+ users [ROBLOX][publish] 🔞.
- [ ] If the game is for under-16s: Roblox Kids (5-8) accepts only **Minimal/Mild**; Roblox Select (9-15)
  also accepts **Moderate (9+)**. Reaching them also needs: age verification + 2-step verification, a Roblox
  Plus/Premium subscription active 2 months **or** a refundable 1,000 Robux fee per game 💲, the full
  questionnaire, and an evaluation (250 unique plays by highly engaged age-checked players within 60 days;
  50,000 Robux refundable expedited review exists 💲). Plan this with the owner [ROBLOX][kids-select] 🔞.
  Horror: jump scares, creepy NPCs, ominous music and suspense are **Mild fear**; realistic gore is Moderate [ROBLOX][maturity].
- [ ] Genre + subgenre chosen (changeable only once every 3 months) [ROBLOX][genres].
- [ ] Custom thumbnail uploaded (required for Home recommendation eligibility) [ROBLOX][discovery].
- [ ] "Exclude from recommendations" is **off** (otherwise Home recommendations are zero) [ROBLOX][acquisition].
- [ ] Automatic translation on for the main markets, plus name/description reviewed by a native speaker for the top 1-2 languages [ROBLOX][autotranslate].

### B. Store page (see `reference/thumbnails-and-icon.md`, `reference/title-and-description.md`, `reference/templates.md`)
- [ ] Icon 512×512, one bold subject, readable at 150×150 and smaller; no tiny text.
- [ ] 3-5 thumbnails at 1920×1080 (16:9), each a **different** promise (character, moment, mode, mood);
  nothing essential at the bottom edge; true to gameplay [ROBLOX][thumbnails].
- [ ] Personalization on with 2-5 active thumbnails [ROBLOX][thumbnails].
- [ ] One 15-30 s gameplay video (in-engine footage, Roblox-catalog music, no voice-over, no ad claims;
  3 uploads/month quota) [ROBLOX][thumbnails].
- [ ] Title: short, unique, genre word or hook early, ≤ 2 emoji, no "[UPDATE]" spam if you can't keep it honest.
- [ ] Description: hook line (title + genre + most unique feature) ≤ 160 chars, then "what's new", then
  features; no keyword stuffing, no hashtags (not used for ranking), no giveaways [ROBLOX][descriptions].
- [ ] Social links (up to 3; visible only to age-checked 16+ users; creator must be age-verified 16+) [ROBLOX][social-links] 🔞.

### C. First session (see `reference/algorithm-and-metrics.md`; feel/onboarding detail in `game-polish`)
- [ ] Instrument `LogOnboardingFunnelStepEvent` for every step from spawn to the first completed loop [ROBLOX][funnels].
- [ ] Teach by doing; get to the fun quickly; end the first loop with a "moment of joy" and a visible next goal [ROBLOX][onboarding].
- [ ] Multiplayer-only games: never strand a lone new player (solo fallback, bots/NPC partner, or fast fill).
- [ ] Test on a low-end phone: load time, first-frame readability, touch controls.

### D. Social loops (see `reference/social-and-virality.md`)
- [ ] Invite prompt (`SocialService:PromptGameInvite`) shown at a natural high point, with `LaunchData` so the friend lands next to the inviter [ROBLOX][invites].
- [ ] Referral Rewards banner configured; reward both sides once; anti-abuse limits [ROBLOX][referral].
- [ ] Private/reserved servers or "play with friends" queue: these sessions count as intentional co-play [ROBLOX][rfy-2025].
- [ ] Share links per channel (TikTok, YouTube, Discord…) with launch data [ROBLOX][share-links].

### E. Growth push (only after the growth gate; see `reference/content-creators-and-ads.md`)
- [ ] Creator kit and a short list of matching creators; clips posted natively on TikTok/Shorts/Reels.
- [ ] Today's Picks nomination after each notable update; Standout Games if genuinely novel [ROBLOX][todays-picks][standout].
- [ ] Events in Creator Hub (RSVP → notifications; Trending Events chart needs ≥ 1,000 RSVPs) [ROBLOX][events].
- [ ] 💲 Ads test drafted (objective, audience, budget, creatives, stop rule) and **approved by the owner** before launch.

### F. Live ops (see `reference/launch-and-live-ops.md`)
- [ ] Fixed update day (hits often ship weekly before the weekend; Saturday is the weekly traffic peak) [ROBLOX][faq][CASE].
- [ ] Each update: changelog line in the description, new thumbnail for the new content, event or announcement, Today's Picks re-nomination.
- [ ] Seasonal calendar (Halloween, school holidays, local holidays such as Brazil's July/December breaks).

---

## Growth gate (fill in before any push)
```
GROWTH GATE — <game> — <date>
Scores (0-4): concept _ | first60s _ | return _ | social _ | store _ | compliance _ | measurement _ | liveops _ | clip _
Open P0: <none | list>
RFY window: <dates>  PTR: _ (bench _)  first-play bounce: _ (bench _)  D1: _ (bench _)  playtime/user: _ (bench _)
Co-play share: _   Top funnel drop: step _ (_ %)
Decision: PUSH | FIX FIRST (<top 3 fixes>) | RETHINK (concept/loop)
Spend requested 💲: <none | channel, amount, duration, stop rule>  → owner approval: <pending|yes|no>
```

## Weekly growth report (format)
```
WEEK <n> — <game>
Traffic by source (new users): Home recs _ | Search _ | Friends _ | Charts _ | Ads _ | Other/external _
Signals vs benchmark: PTR _ | bounce _ | D1 _ | D7 _ | playtime/user _ | co-play days _
What changed this week: <update / thumbnail / event / creator video>
Read: <what moved and why we think so, with confidence>
Next single change: <one thing> — wait until <date> before judging
```

## Anti-patterns (the short list; full list in `reference/policy-traps.md`)
- Buying traffic (ads, creators) to "kick-start the algorithm" before the first session retains.
- Thumbnails showing things that aren't in the game, fake UI, "FREE ROBUX/UGC", giveaways, or Roblox logos.
- Renaming the game every week or stuffing the title with emoji and tags; copying a hit's name/thumbnail.
- Judging a change after a day; changing five things at once; ignoring seasonality (weekends, school terms).
- A 2-player game that strands solo players in a lobby.
- "Join our Discord" text or URLs inside the game (only the store-page social links are allowed).
- Contests with Robux or real-money prizes, alt-account referral farming, bots of any kind.
- Treating one viral TikTok as success: the spike only matters if D1/D7 hold.

[discovery]: https://create.roblox.com/docs/discovery
[faq]: https://create.roblox.com/docs/discovery-faq
[retention-source]: https://devforum.roblox.com/t/analytics-view-retention-by-acquisition-source-and-select-your-benchmark-set/4010157
[thumb-tips]: https://devforum.roblox.com/t/5-tips-from-roblox-staff-to-get-the-most-out-of-thumbnail-personalization/3471689
[publish]: https://create.roblox.com/docs/production/publishing/publish-games-and-places
[kids-select]: https://create.roblox.com/docs/production/publishing/kids-and-select
[maturity]: https://create.roblox.com/docs/production/promotion/content-maturity
[genres]: https://create.roblox.com/docs/production/publishing/experience-genres
[acquisition]: https://create.roblox.com/docs/production/analytics/acquisition
[autotranslate]: https://create.roblox.com/docs/production/localization/automatic-translations
[thumbnails]: https://create.roblox.com/docs/production/publishing/thumbnails
[descriptions]: https://create.roblox.com/docs/production/publishing/descriptions
[social-links]: https://create.roblox.com/docs/production/promotion/social-media-links
[funnels]: https://create.roblox.com/docs/production/analytics/funnel-events
[onboarding]: https://create.roblox.com/docs/production/game-design/onboarding
[invites]: https://create.roblox.com/docs/production/promotion/invite-prompts
[referral]: https://create.roblox.com/docs/production/promotion/referral-system
[rfy-2025]: https://devforum.roblox.com/t/3587441
[share-links]: https://create.roblox.com/docs/production/promotion/share-links
[todays-picks]: https://create.roblox.com/docs/creator-programs/todays-picks-home
[standout]: https://create.roblox.com/docs/creator-programs/standout-games
[events]: https://create.roblox.com/docs/production/promotion/experience-events
