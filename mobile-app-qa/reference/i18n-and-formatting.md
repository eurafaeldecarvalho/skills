# Localization & formatting (dimension 5, mechanics)

Words are covered in [translation-quality.md](translation-quality.md). This file covers locale
resolution, numbers, money, dates, plurals and layout under translation.

## 1. One source of truth for the active locale
Three different "locales" exist in an Expo/RN app, and bugs live in the gaps:
| Source | What it is | Gotcha |
|---|---|---|
| In-app language choice (i18next/i18n-js state, persisted) | what the user picked | formatters that don't read it keep the old/device locale |
| Device / per-app locale (`expo-localization` `getLocales()`) | Android system or per-app language (Android 13+) | On Android it can change while the app runs: re-read on foreground (`AppState`) or use `useLocales()` |
| `Intl` default (`'default'` / no locale arg / `toLocaleString()` with no args) | engine default | Not your app language. Never call `Intl`/`toLocaleString` without an explicit locale |
Rules:
- A single `formatLocale()` derived from the **active app language + the user's region**, passed to
  every formatter. Formatters are created per call or memoized **keyed by locale**.
- Language ≠ region ≠ currency. `es-419` is a *language* tag: as a *format* locale it uses `.` decimals
  (`1,234.56`), which is wrong for Argentina, Chile, Colombia, Uruguay, Paraguay (comma decimals) and
  right for Mexico. Format with `es-AR`, `es-MX`, … built from language + `regionCode` when you know it.
- Currency comes from the account/family/country data, **not** from the language; format it with the
  user's format locale. Same amount, same currency, different reader → different string. All of these
  are correct (ICU/Node 24; verify Hermes on device):

| locale | currency | 1234.56 | -5 |
|---|---|---|---|
| pt-BR | BRL | `R$ 1.234,56` (U+00A0 after `R$`) | `-R$ 5,00` |
| pt-BR | USD | `US$ 1.234,56` | |
| pt-PT | EUR | `1234,56 €` (no grouping for 4 digits; `12 345,60 €` with U+00A0) | `-5,00 €` |
| es-419 | MXN | `MXN 1,234.56` | |
| en-US | USD | `$1,234.56` | `-$5.00` |
| en-US | BRL | `R$1,234.56` ← **the "US-format money in pt-BR" bug looks exactly like this** | |

- Tests compare with the NBSP normalized or, better, assert the exact string including `\u00a0`.
- `currencyDisplay: "narrowSymbol"` turns `US$`/`R$` into `$`/`R$` — ambiguous for USD vs other dollars;
  decide on purpose.

## 2. Hermes `Intl` on Android
- Hermes implements `Intl` on Android via the platform's ICU (Java `android.icu`/`java.text`), so output
  can differ by Android version and from Node. Some options are rough on old versions (`notation:
  'compact'`, `signDisplay`, `style: 'unit'` on Android 11; see Hermes `doc/IntlAPIs.md`).
- Therefore: golden tests in Node (fast, CI) **and** a device check — the matrix sweep detector reads the
  real rendered strings on the emulator for every locale.

## 3. Money and number INPUT
- Accept both `,` and `.` as the decimal separator; treat the **last** separator followed by 1-2 digits
  as decimal; strip grouping. Reject >2 decimals for 2-decimal currencies; handle 0-decimal currencies
  (JPY, CLP, PYG) explicitly.
- Display while typing in the locale format (or at least show a formatted preview next to the field).
- `keyboardType="decimal-pad"`: Android keyboards differ — some Samsung keyboards historically hid the
  comma (facebook/react-native#22005/#21733). Test on Gboard + Samsung + Moto default keyboards with the
  device in pt-BR; never rely on the keyboard to enforce format.
- Store integers in minor units (cents); never floats; never round-trip money through `toFixed` + `Number`.
- Property tests (fast-check): for random cents and every locale, `parse(format(c, l), l) === c`;
  `parse` is idempotent on already-normalized input; sums of splits equal the total (rounding rule documented).

## 4. Dates, times, plurals
- Always `Intl.DateTimeFormat(locale, options)`; never manual `MM/DD`. pt/es are `dd/mm/aaaa`; 24h clock;
  week starts Monday in PT/most of LatAm vs Sunday in BR/US (read `getCalendars()[0].firstWeekday`).
- Timezone: store UTC instants for events, plain dates (YYYY-MM-DD) for all-day items; test DST changes,
  devices in different timezones for the two parents, and midnight boundaries.
- Plurals via ICU/i18next plural forms (`_one`, `_other`, and `_many` where CLDR defines it); test 0, 1,
  2, 5, 21, 1000000.
- Relative times ("há 2 dias", "hace 2 días") via `Intl.RelativeTimeFormat` with the app locale.

## 5. Layout under translation
- Budget +30% length; buttons/tabs/chips wrap or shrink gracefully; no fixed widths on text.
- Test the longest locale at font scale 1.3 and 2.0 on the small screen (the sweep does this).
- Names, emails and amounts from users may be long; truncate with ellipsis + full value accessible.

## 6. Tests to add (minimum)
- `i18n catalog parity` (keys, placeholders, plural keys) — already common; extend with variant-word lists.
- `formatMoney` golden table: every shipped locale × {BRL, EUR, USD, MXN} × {0, 0.5, 1234.56, -5, 1e6}.
- `parseMoney` table: `"1234,56"`, `"1.234,56"`, `"1,234.56"`, `"1234.5"`, `"R$ 10"`, `" 7 "`, `""`, `","`,
  `"1,2,3"`, `"12,345"` (ambiguous — define the rule!), negative, >max.
- Language switch test: change language in-app → every formatted value on screen changes (Maestro flow
  by `testID` asserting the formatted text, or a component test rendering with each locale).
