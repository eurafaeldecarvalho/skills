# Accessibility (dimension 12, part A)

Roblox gives few platform switches, so most of this is design + UI checks. Score it like any dimension; a
blocker for a whole group of players (unreadable on the target phone, a mechanic that needs sound) is P1.

| Check | How to verify | Typical severity |
|---|---|---|
| Text readable on the smallest target | ui-audit `small-text` (real px after scale) ≥ the floor in GAME-QA.md; dark scenes: contrast ≥ 4.5:1 for body text, 3:1 for large/HUD | P2 (P1 if core info) |
| Meaning not by color alone | grep the UI code for state shown only by `BackgroundColor3`/`TextColor3`; add icon/text/shape | P2 |
| Meaning not by sound alone | every gameplay-relevant sound (alarm, anomaly, timer) has a visual cue too | P1 if needed to win/survive |
| Flashing / strobing | no full-screen flashes > 3 per second; jump scares have a setting or warning when the audience is young | P1 |
| Reduced motion | camera shake, screen bob, big tweens can be turned off or are mild; respect `GuiService.ReducedMotionEnabled` where available | P2 |
| Hold / timing actions | holds and quick-time events have generous windows or a tap alternative; no action needs two simultaneous touches unless core | P2 |
| Touch targets | ui-audit `small-target` (≥ 44 px) and `touch-zone` (no buttons under the thumbstick/jump) | P2 / P1 |
| Gamepad | every action reachable with `SelectedObject` navigation; focus visible | P1 if console targeted |
| Subtitles | voice lines / story audio have on-screen text | P2 |
| Reading load | onboarding text short (≤ ~12 words per prompt), icons + words, not walls of text | P3 |
| Preferred text size | where `GuiService.PreferredTextSize` is honored, UI still fits at the largest setting (sweep it like a locale) | P2 |

Evidence: ui-audit JSON per screen × viewport, screenshots of the darkest scene on the weakest phone (operator),
and a short list of design checks with file:line. Mark device-only checks Blocked until a person runs them.
