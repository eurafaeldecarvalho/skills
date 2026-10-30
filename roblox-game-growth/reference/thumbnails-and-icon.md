# Thumbnails, video and icon

Roblox rules change often; accurate at writing time (late 2026). Sources: [Thumbnails](https://create.roblox.com/docs/production/publishing/thumbnails),
[Icons](https://create.roblox.com/docs/production/publishing/experience-icons), staff tips (DevForum 3471689).

## Specs and rules [ROBLOX]
- Up to **10 images or videos** on the details page; all are moderated.
- Images **16:9**, ideally **1920×1080**; anything else gets stretched. Keep personalization uploads **< 3 MB**.
  Formats: jpg, png, gif, tga, bmp. Add **alt text**.
- Keep essential elements away from the **bottom** (player count/metadata overlays cover it).
- A **custom** thumbnail is required to be eligible for Home recommendation impressions.
- **Video**: free, **3 uploads per month** (rejected ones still count). Must be authentic in-game footage.
  In-game UI text is fine; music only from Roblox's audio catalog; **no voice-over, narration, voice chat,
  or music with lyrics**; overlay text only to describe gameplay ("Collect coins to boost jumps"); no ads,
  promos or subjective claims ("best game ever"), no misleading footage.
- **Icon**: square, **512×512**, often shown at 150×150 or smaller; one icon per locale; must pass moderation.
  It should express the theme and be unique and relevant (ambiguous art confuses players).

## Personalization (built-in A/B) [ROBLOX]
- Activate **2-5 thumbnails**; Roblox shows each to random users, then gives more impressions to the
  winner *per user group* (multi-armed bandit, rebalanced regularly). Docs: average **+8.5% qualified PTR**
  in testing, some games +50%. Staff tips post: average +12%, up to +56%.
- Keep several active (tastes shift) instead of locking one winner; give a set ≥ 7 days or until the next
  update before judging; make thumbnails **visually different** from each other (different promise,
  character, colour, moment) so the system has something to learn; every one must reflect real gameplay.
- Read *Impressions by thumbnail* and *qualified PTR by thumbnail*; retire losers, add one new challenger per update.

## What converts [HEURISTIC — DevForum/community consensus, test it]
- **One focal subject** (character, monster, item) large in frame; a readable emotion (fear, surprise, glee).
- **High contrast and value separation**: bright subject on a dark/simple background, rim light; it must
  read at phone size in a grid full of saturated tiles.
- **Show the real hook**: the moment from your "clip" (the monster at the window, the rare drop, the chaos).
- **Little or no text** (≤ 3 big words if any); text in images is not auto-translated.
- **Use Roblox avatars** in the art so players see "people like me" doing it; two characters for co-op games.
- Rendered in-engine or painted is fine, but don't show places, items or modes that don't exist.
- Refresh with each major update (new content → new thumbnail challenger; event art during events).
- Test small: put the tile next to the top 10 of your genre at 150 px width. If you can't tell what it is in 1 second, redo it.

## Icon heuristics [HEURISTIC]
- One silhouette or face, no scene; no thin text; consistent with the thumbnail's main character/colour so
  players recognise it in "Continue" rows; avoid Roblox logos and other creators' characters.

## Brief workflow
1. Write the brief (template in `templates.md`): hook, subject, emotion, palette, framing, what must be true in-game.
2. Stage the shot in Studio (lighting, camera FOV 30-50 for a "poster" look), capture at 1920×1080+.
3. Paint-over/composite allowed; keep it honest. Export < 3 MB.
4. Upload 3 distinct variants + video; activate personalization; log the date; don't touch for ≥ 7 days.

## Common rejections / reach cuts [ROBLOX]
Giveaway or Robux imagery, misleading content, copyrighted characters/logos, near-copies of another game's
thumbnail, lyrics/voice in video, off-platform URLs.
