# Locale conventions (mandatory research step before translating — pass 1b, dimension 5)

Words are only half of localization. Before translating, **research and write down the format
conventions of every target locale** in `qa/l10n/<locale>-glossary.md` (section "Conventions"), with
the source for each line. Source of truth: **Unicode CLDR** (what `Intl` implements) — check the CLDR
charts / `Intl` output, then confirm on the device, because **Hermes `Intl` on Android uses the
platform ICU and can differ from Node/CLDR by Android version** (and some APIs, e.g. `Intl.Locale`
week info, `Intl.Segmenter`, `DurationFormat`, may be missing). Every row below must have a test.

Values: Node 24 (ICU/CLDR) output. `⍽` = U+00A0 no-break space. Verify on the device before trusting.

| Convention | en-US | pt-BR | pt-PT | es-MX | es-AR | Source / API |
|---|---|---|---|---|---|---|
| Decimal / thousands separator | `1,234,567.891` | `1.234.567,891` | `1⍽234⍽567,891`, but `1234` (no grouping for 4 digits) | `1,234,567.891` | `1.234.567,891` | `Intl.NumberFormat(l)` |
| Currency, placement, spacing | `$1,234.56` | `R$⍽1.234,56`; USD → `US$⍽1.234,56` | `1234,56⍽€` (after, with space) | `$1,234.56` (MXN; ambiguous with USD → show code when mixed) | `$⍽1.234,56` (ARS) | `{style:'currency', currency}` |
| Negative amount | `-$5.00` | `-R$⍽5,00` | `-5,00⍽€` | `-$5.00` | `-$⍽5,00` | `signDisplay`, `currencySign:'accounting'` |
| Percent | `12.5%` | `12,5%` | `12,5%` | `12.5%` | `12,5%` | `{style:'percent'}` |
| Short date | `10/30/2026` (M/D) | `30/10/2026` | `30/10/2026` | `30/10/2026` | `30/10/2026` | `DateTimeFormat` |
| Long date, capitalization | `Friday, October 30, 2026` | `sexta-feira, 30 de outubro de 2026` (lower-case days/months) | same as pt-BR | `viernes, 30 de octubre de 2026` | same | `dateStyle:'full'`; capitalize only at sentence start |
| Time | `6:05 PM` (12 h) | `18:05` (24 h) | `18:05` | `6:05 p.m.` | `6:05 p. m.` (CLDR) — many AR users/apps use 24 h; respect device 24 h setting | `timeStyle`, `hourCycle`; Android 24-hour setting |
| First day of week | Sunday | Sunday | Sunday (CLDR) — many PT calendars start Monday; decide and test | Sunday | Monday | `expo-localization getCalendars()[0].firstWeekday` (device), `Intl.Locale#getWeekInfo` (may be missing in Hermes) |
| Relative dates | `yesterday`, `3 days ago` | `ontem`, `há 3 dias` | `ontem`, `há 3 dias` | `ayer`, `hace 3 días` | same | `RelativeTimeFormat(l,{numeric:'auto'})` |
| Plural categories for 0/1/2/1e6 | other/one/other/other | **one**/one/other/many (pt-BR treats 0 as singular: "0 item") | other/one/other/many ("0 itens") | other/one/other/many | same | `Intl.PluralRules`, i18next `_one/_many/_other` |
| Lists | `A, B, and C` | `A, B e C` | `A, B e C` | `A, B y C` | same | `Intl.ListFormat` |
| Units | imperial (lb, mi, °F, fl oz) | metric (kg, km, °C) | metric | metric | metric | `{style:'unit'}` (`2,5 kg`); `getLocales()[0].measurementSystem`, `temperatureUnit` |
| Phone numbers | `(555) 123-4567`, +1 | `(11) 91234-5678`, +55, mobile 9 digits | `912 345 678`, +351 | `55 1234 5678`, +52 | `11 1234-5678` / `+54 9 11 …` | libphonenumber (`libphonenumber-js`), never a hand regex |
| Address / postal code | street no. + street, city, ST 12345 | Rua X, 123 — bairro — cidade-UF — CEP `01310-100` | Rua X, 123, `1000-001` Lisboa | Calle X 123, Col. Y, `06600` CDMX | Calle X 123, `C1425` CABA (CPA) | Google libaddressinput data; free-form fields beat rigid US forms |
| Name order / fields | given + family | given + family; often 2+ family names | same | given + paternal + maternal | given + family | one "full name" field or given/family without length/charset limits |
| Sorting / search with accents | locale collation | `ábaco Ágata avó éter Eva Zé` (accent-insensitive order); naive `sort()` gives `Eva Zé avó Ágata ábaco éter` | same | same; `ñ` after `n` | same | `Intl.Collator(l)` / `localeCompare(b, l)`; search: `sensitivity:'base'` |
| Quotes | “ ” | “ ” | « » (also “ ”) | « » / “ ” | “ ” | tone guide |
| Number **input** | `.` decimal | **`,` decimal** — must also accept `.` | `,` | `.` | `,` | own parser + `keyboardType="decimal-pad"`; test Gboard/Samsung/OEM keyboards |
| Timezone | multiple | multiple (BRT UTC-3, AMT, ACT, Noronha), no DST since 2019 | WET/WEST (DST), Azores | multiple, no DST since 2022 (except border) | ART UTC-3 | `getCalendars()[0].timeZone`; store UTC instants, plain dates for all-day |
| Week/month names in UI | — | `seg ter qua…`, `jan fev…` | same | `lun mar mié…` | same | `DateTimeFormat({weekday:'short'})` — never hardcode arrays |

`es-419` as a *format* locale formats like es-MX (`.` decimal) and with `USD` code for USD — wrong for
AR/CL/CO/UY/PY. Use language `es-419` for words but a region-specific format locale.

## Mandatory research step (do this per locale before translating)
1. Generate the table for the locale with Node (`Intl`) and check doubtful rows in the CLDR charts.
2. Run the same snippet **inside the app on the release build on Android** (a hidden debug screen or a
   Jest/Maestro check reading rendered text) and diff with Node. Differences = Hermes/ICU gaps → polyfill
   (`@formatjs/intl-*`) or avoid the API.
3. Note product decisions (week start, 24 h, currency display, address form) in the glossary.

## Test cases (each row becomes at least one automated test)
| Area | Cases |
|---|---|
| Separators | format 0, 0.5, 1234, 1234567.891 per locale; pt-PT 4-digit no-grouping |
| Currency | each currency × each locale; NBSP exact; currency ≠ language (BRL in en-US, USD in pt-BR) |
| Negative / percent | -5, -0 (no "-0,00"), 12.5 %, 100 % |
| Dates | 30/10/2026 vs 10/30/2026; 01/02 ambiguity; Feb 29; year end; long-date lower case |
| Time | 18:05 vs 6:05 PM; device 24 h toggle on/off (`settings put system time_12_24 24`) |
| Week start | calendar grid starts on the configured day per locale |
| Relative | ontem / há 3 dias / amanhã; boundaries at midnight in the user's TZ |
| Plurals | 0, 1, 2, 5, 21, 1 000 000 in each locale (pt-BR 0 → singular) |
| Units | kg vs lb display if the app shows any measurement |
| Phone | parse/format/validate BR mobile, PT, MX, AR, US; paste with spaces/`+` |
| Address/CEP | CEP `01310-100` and `01310100`; PT `1000-001`; long street names |
| Names | `Maria da Conceição dos Santos Oliveira`, `José Ñúñez`, one-word name, apostrophe `D'Ávila` |
| Collation/search | sorted lists use `Intl.Collator`; search "jose" finds "José" |
| Quotes/punctuation | ¿…? ¡…! present in es; no ASCII-quote tells where tone guide says otherwise |
| Number input | `1234,56`, `1.234,56`, `1,234.56`, `0,5`, `,5`, `R$ 10`, spaces, empty, `1,2,3`; with each keyboard |
| Timezone | two parents in different TZs see the same event at the right local time; DST in PT |
| Hermes | every row above re-checked on device (release build) — Node green is not enough |

## Sources
CLDR charts <https://www.unicode.org/cldr/charts/latest/> · CLDR plural rules
<https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html> · MDN `Intl` ·
Hermes Intl on Android <https://github.com/facebook/hermes/blob/main/doc/IntlAPIs.md> · expo-localization
<https://docs.expo.dev/versions/latest/sdk/localization/> · libphonenumber · Google libaddressinput.
