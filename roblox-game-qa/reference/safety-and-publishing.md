# Safety, compliance & publishing (dimensions 9-10)

Roblox rules change often. Before publishing, re-read the current Creator Hub pages on publishing,
the Maturity & Compliance questionnaire and Community Standards; the notes below were accurate at
writing time (late 2026) and are a reminder, not the authority.

## Text filtering
- Any text a player writes that another player can see (pet names, signs, team names, custom
  messages) goes through `TextService:FilterStringAsync` on the server, then
  `GetNonChatStringForBroadcastAsync` (or the per-user variant). Wrap in `pcall`; on failure show nothing.
- Don't build custom chat that bypasses `TextChatService`. Review `TextChatService` settings (channels,
  bubble chat) deliberately.
- Numbers and preset choices don't need filtering; free text always does.

## Content, maturity & audience
- Content follows Community Standards. Answer the Maturity & Compliance questionnaire truthfully for
  what is actually in the game; re-answer when content changes.
- Match the audience: what is fine for 16+ may not be for all-ages. Reaching younger audiences has
  extra creator requirements (age/ID verification, 2FA, fee or subscription, evaluation at the time of
  writing).
- No secrets in the DataModel that clients can read; use server-only storage/Secrets.

## Money (needs the owner's approval)
- Never buy assets, spend Robux, create or price developer products/game passes, run ads or sponsor
  the experience without explicit approval from the owner for that specific action.
- If monetization exists: purchases processed with `MarketplaceService.ProcessReceipt` idempotently,
  granted only after the receipt, never lost on failure.

## Publishing
- Confirm the target: the **existing** universe/place (check name and that Studio's
  *File ▸ Game Settings* shows the expected game) before *Publish to Roblox*. *Publish to Roblox As…*
  creates or retargets places; use it only on purpose. Duplicate places split players and history.
- Access, at writing time: a playtest/early-testers mode (editors plus a small number of invited testers,
  e.g. up to 10) lets you gather feedback before going public; public requires an age check, account in
  good standing and the maturity step. Verify the current limits.
- Note the published version; place version history allows rollback (revert to a previous version and
  publish). Decide whether to restart/migrate servers so players get the update.
- Post-publish smoke test: join from a real device of each class that had bugs, play one full loop,
  open F9 and read client errors.

## Anti-patterns
- Displaying unfiltered player-made text "because it's only shown to friends".
- Publishing from a stale Studio file instead of the current build.
- Assuming publishing rules from memory.
