# Title, description, genre, languages and maturity label

Roblox rules change often; accurate at writing time (late 2026). Sources: [Publish games](https://create.roblox.com/docs/production/publishing/publish-games-and-places),
[Descriptions](https://create.roblox.com/docs/production/publishing/descriptions), [Genres](https://create.roblox.com/docs/production/publishing/experience-genres),
[Automatic translation](https://create.roblox.com/docs/production/localization/automatic-translations), [Content maturity](https://create.roblox.com/docs/production/promotion/content-maturity),
[Kids and Select](https://create.roblox.com/docs/production/publishing/kids-and-select).

## Title (game name)
[ROBLOX]
- **Keep it consistent.** Renaming often makes the game harder to find by its old name.
- **No spam.** Repeating words ("OBBY OBBY OBBY") can get the game demoted.
- **One or two well-placed emojis** are fine; decorations inside words are not.
- Metadata implying monetary rewards ("Robux!", "FREE UGC") gets less exposure; near-copies of another game's
  title/visuals are not prioritized.

[HEURISTIC]
- The commonly reported limit is **50 characters** (community sources). Verify in Creator Hub. Tiles truncate,
  so the recognisable part must sit in the first ~20-30 characters.
- Structure: `<Brand name> <optional 1 emoji>`, or `<Brand> [<short tag>]` only while the tag stays true
  (e.g. an event). Hits use short brandable names (*DOORS*, *Grow a Garden*, *Dead Rails*, *99 Nights in the Forest*).
- The name should say the **promise or genre** when the brand is unknown ("Escape the…", "Survive…", "…Kiosk", "…Tycoon").
- Riding a trend is allowed by Roblox's own advice ("add your own spin to existing trends in the title, images,
  description and content"), but not copying a name; Roblox favours the original among near-identical games.
- Bracket tags like `[UPDATE]` / `[🎃 EVENT]` are common practice; change them only when it's true and
  remove them after. Constant renaming works against you.

## Description
[ROBLOX] Recommended structure:
1. **Hook (≤ ~160 chars)**: what the game is + core keywords. This becomes search snippets and is all that
   mobile shows before "expand". First sentence = the most accurate summary of genre and content.
2. **Recent updates (optional, short)**: one or two lines. Don't let it push the main content down.
3. **Main content**: features, modes, goals, social hooks, in natural language with relevant keywords.
4. **Extra (optional)**: brief FAQ, credits, group mention.

Rules: around a **1,000-character** budget in the doc's guidance; emojis OK; **no tags/hashtags** (unused by
ranking); **don't list controls** (teach them in-game); no keyword repetition or irrelevant keywords
(demotion); no giveaways; nothing that isn't in the game. Use plain words players search for ("horror",
"co-op", "2 players", "survive", "scary", "kiosk", "night shift").

## Genre and subgenre
[ROBLOX] Genres: Action, Adventure, Education, Entertainment, Obby & platformer, Party & casual, Puzzle, RPG,
Roleplay & avatar sim, Shooter, Shopping, Simulation, Social, Sports & racing, Strategy, Survival, Utility &
other, each with subgenres. **There is no "Horror" genre**: horror games usually fit **Survival** (1 vs All,
Escape) or **Adventure** (Story, Exploration); a job/shop-sim horror can also fit **Simulation** if the work
loop dominates. Genre can change **only once every 3 months**. Genre isn't a ranking factor, but an accurate
one sets expectations and lowers bounce (FAQ).

## Languages and localization
[ROBLOX]
- Turn on **Automatic text capture** (needs `AutoLocalize`) and **Use translated content**, then pick
  languages in Localization settings. **Experience information** translation covers the name and description.
- Automatic translation only fills empty entries and never overrides your manual ones. Text baked into
  images is not captured (so keep UI and thumbnail text minimal, or make per-locale images; the icon is per locale).
- Capture can take minutes in Studio and days via automatic capture in live servers; check the localization table.

[HEURISTIC]
- Hand-write the name/description for your top 2-3 markets; machine translation is the fallback.
- Brazil is Roblox's **second-largest market by DAU** (Roblox VP, Oct 2024 interview, [Mobile Time](https://www.mobiletime.com.br/noticias/04/10/2024/roblox-brasil/)) [CASE];
  Portuguese, Spanish and English cover most of the Americas. Check **Analytics ▸ Demographics** for your real split.
- Keep the brand name the same in every language; translate the hook, not the brand.

## Maturity label and who can see the game 🔞
[ROBLOX]
- Creator needs an account in good standing ≥ 2 days old plus an age check to release to 16+.
- Answering only the first questionnaire question with "No" gives **Content May Vary**, visible **only to age-checked 16+**.
- Account tiers: **Roblox Kids** (5-8) sees Minimal/Mild; **Roblox Select** (9-15, and self-declared 9+ until
  age-checked) sees Minimal, Mild, Moderate (9+); **Roblox** (age-checked 16+) sees all rated content except Restricted 18+.
- Reaching Kids/Select ("all ages") also requires: age verification, 2FA, **Roblox Plus/Premium active for 2
  months or a refundable 1,000 Robux per-game fee** 💲, the full questionnaire, and an evaluation:
  **250 unique plays by highly engaged age-checked players within 60 days** (watch it in Audience ▸ Reach).
  A refundable **50,000 Robux expedited review** 💲 exists for timed launches. Fees are refunded after 90 days
  unless the game is permanently moderated.
- Fear: **Mild** = heavy breathing, screaming, creepy NPCs, **jump scares**, ominous music, suspense.
  **Moderate** = realistic gore (disfigured mouths with realistic blood, visible organs, bleeding eyes).
  Re-answer the questionnaire whenever content changes.

[HEURISTIC] For most growth goals, a Mild label + all-ages eligibility gives the largest audience; a 16+-only
game is choosing a much smaller pool. Decide it deliberately, with the owner, because of the fee/subscription.
