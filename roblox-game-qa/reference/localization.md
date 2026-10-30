# Localization (dimension 12, part B)

Matters when GAME-QA.md lists more than one language, and even with one: Roblox auto-translates strings it can see,
which can break layout or meaning.

| Check | How |
|---|---|
| Every player-visible string is in one place (strings table / LocalizationTable), not scattered literals | `rg -n 'Text\s*=\s*"' src` and review; literals in UI code are findings (P3, P2 if shipped languages miss them) |
| Every key exists in every shipped language | a Lune test that loads the table and diffs keys per locale (missing = P2) |
| Longest translation fits | **locale × viewport sweep**: render or compute each screen with the longest string per key (German/Portuguese are ~30% longer than English) on the smallest viewport; ui-audit `off-screen`/`overlap`/`small-text` must stay clean. A pure-math layout test (case-turno.md, `escala.spec`) does this headless. |
| No string concatenation of sentences | `"You have " .. n .. " coins"` can't be translated; use format strings with named slots (P3) |
| Numbers, plurals, time | `1 coin / 2 coins`; decimal separator per locale if shown; timers not locale-formatted by hand |
| Auto-translation | decide per string: auto-translate on/off; check names/brand words aren't translated; check the store page text in each language |
| Glyphs | fonts used render accents and the shipped scripts; emoji may render as boxes on some devices (ui-audit `emoji-glyph`) |
| Store page | title/description per language within limits; thumbnails without baked-in text, or one set per language |

Pseudo-locale trick: a test locale that wraps each string as `[!! Ţéxţ ~~~ !!]` (+40% length, accents) finds
hard-coded text and clipping in one pass. Run it in the sweep, never ship it.
