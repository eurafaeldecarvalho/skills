# Social loops and virality (every player brings the next)

Roblox rules change often; accurate at writing time (late 2026). Docs: [Invite prompts](https://create.roblox.com/docs/production/promotion/invite-prompts),
[Referral system](https://create.roblox.com/docs/production/promotion/referral-system), [Share links](https://create.roblox.com/docs/production/promotion/share-links),
[Experience notifications](https://create.roblox.com/docs/production/promotion/experience-notifications), [Events](https://create.roblox.com/docs/production/promotion/experience-events),
[Social links](https://create.roblox.com/docs/production/promotion/social-media-links), [Moments](https://about.roblox.com/newsroom/2025/09/roblox-moments-user-generated-discovery).

## Why social matters more on Roblox
- **Intentional co-play days** is an "important" ranking signal (joins, invites, private servers) [ROBLOX].
- Roblox describes its users as hopping between many experiences per session, with friend invites and
  YouTube driving organic traffic [ROBLOX, roblox-user-base doc].
- Recent hits are built for friends: 99 Nights in the Forest is co-op survival ("friendslop") and peaks on
  weekends; Grow a Garden added trading; DOORS is better in a group [CASE].

## Design for co-play [HEURISTIC]
- Make playing **with** a friend the best path: shared goals, roles that need two people (one watches the
  cameras, one serves), revive/rescue, shared rewards, "duo" bonuses. Don't punish solo players: give them
  an NPC partner, a solo mode, or fast matchmaking.
- Small fixed party sizes (2-4) are easy to fill from a friend list; big servers need strangers.
- Keep friends together: party-aware teleports (`TeleportService` with the party), reserved servers for
  groups, "join friend" works mid-round.

## Invite prompts [ROBLOX]
- `SocialService:CanSendGameInviteAsync(player)` → `SocialService:PromptGameInvite(player, options)`.
- `ExperienceInviteOptions`: `PromptMessage`, `InviteUser` (a specific friend), `InviteMessageId`
  (localized invite text set in Creator Hub), `LaunchData` (≤ 200 chars: room code, place, inviter id).
- Read launch data on join via `player:GetJoinData().LaunchData` and put the friend **next to the inviter**.
- [HEURISTIC] Prompt at an emotional high point (after the first scare survived, after a rare drop, at
  "round lost — bring help?"), not at spawn. Offer it from a persistent "Invite" button too.

## Referral rewards [ROBLOX]
- Creator Hub **Referral rewards** shows a banner to invited players; use `player:GetJoinData().ReferredByPlayerId`
  in-game to reward **both** inviter and invitee.
- Anti-abuse: reward once per new user, require some playtime before the reward, cap per day. Encouraging
  alt accounts to farm referrals is prohibited (Creator Rewards terms).

## Share links [ROBLOX]
- Create share links in Creator Hub (Promotion) with custom launch data per channel (TikTok bio, YouTube
  description, Discord, a creator's own link). They replace deprecated deep links; launch data is visible
  and user-editable, so never put secrets or trust it for rewards.
- Use them to measure which channel brings retained players (Share Link analytics; Acquisition "Other").

## Notifications and events [ROBLOX]
- **Experience notifications** go only to opted-in users 13+. Ask with
  `ExperienceNotificationService:PromptOptIn()` (system text, not customizable) at a moment when the player
  wants to come back ("your crops are ready tomorrow"); send via Open Cloud with localized string templates
  and launch data. Don't spam: tie each notification to something real.
- **Events & Updates** (Creator Dashboard ▸ Engagement): up to 10 ongoing/upcoming events, each with its
  own thumbnail, category, page and **Notify me** RSVP (stream + push notifications). The Charts sort
  **Trending events** needs an event active < 7 days with **≥ 1,000 RSVPs** and public visibility.
  **Update announcements** notify followers.

## Clips and Moments [ROBLOX + HEURISTIC]
- **Roblox Moments** (beta since RDC 2025, 13+): players share ≤ 30 s clips with a **Join** button inside
  Roblox; Captures API can auto-trigger a capture at peak moments. If your game has a "clip" moment, hook it.
- Design screenshot/clip moments: the jump scare, the rare spawn, the funny fail, a visible reaction
  (big text, sound sting). Shareable = surprising + readable without context in 3 seconds.

## Community [ROBLOX + HEURISTIC]
- A Roblox **group/community** named after your studio: branded icon, social links, events featured, a
  place for update posts and feedback.
- **Social links** on the details page: up to 3, only for creators age-verified 16+, shown only to
  age-checked 16+ users. In-game you may say "Check out our social media links on our game's page" but
  never show URLs or handles that point off-platform.
- Discord/X/TikTok accounts are fine off-platform; contests with Robux or real-value prizes are not allowed
  without Roblox involvement (Community Standards).
