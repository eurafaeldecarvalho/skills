# Anti-pattern catalog (things this skill hunts)

| Anti-pattern | Symptom | Check |
|---|---|---|
| `Intl`/`toLocaleString` without explicit app locale | money in US format although pt-BR chosen | grep `toLocaleString()` / `NumberFormat(undefined`; sweep `us-money` detector |
| Currency inferred from language (or hardcoded `"USD"`) | wrong symbol | grep `currency:\s*["']` |
| Formatters memoized without locale key | old format after language switch | language-switch test |
| Parser accepts only `.` | can't type cents with comma keyboard | parse table tests |
| `es-419` used as format locale for AR/CL/CO | dot decimals in Argentina | conventions table |
| Translating before research / word-by-word MT | unnatural, wrong variant/register | translation-quality pass |
| One "pt" catalog for BR and PT | "ecrã" for Brazilians or "tela" for Portuguese | variant-word lists |
| String concatenation for sentences | broken grammar/plurals | grep `t\(.*\) \+` |
| Pure `#000` everywhere in dark, no elevation | "all black and weird" | theme review, sweep dark |
| `userInterfaceStyle` without `expo-system-ui` | app ignores system dark mode | config check |
| Hardcoded colors outside theme | white boxes/invisible text in dark | grep raw colors |
| Banner with no exit condition | alert never disappears | state-exit tests, `stuck-banner` detector |
| Every exception → "offline" | false offline latch | error classification tests |
| `isInternetReachable === null` treated as offline | offline banner at launch | unit test |
| No safe-area insets | content under status/nav bar | sweep gesture + 3-button |
| `allowFontScaling={false}` | inaccessible, still breaks on display size | grep |
| Text selectors in E2E | flows fail in pt-BR | Maestro uses `id:` |
| Testing dev build only | release-only crashes | build-and-release |
| Fixed sleeps in E2E | flaky suite | grep `sleep`/`waitForAnimationToEnd` misuse |
| Client-only permission checks | partner can edit A-only data via API | RLS tests |
| Floats for money | 0.1+0.2 cents drift | grep `parseFloat` in money paths |
## QA anti-patterns
Declaring done from code reading · screenshots only in light/en-US · "can't reproduce" without matching
the tester's config · fixing many things at once without re-verifying · trusting detectors without looking.
