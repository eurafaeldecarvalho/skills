# Translation quality (pass 1b + part of dimension 5)

Goal: every string reads like it was **written** by someone from that market for an app in that
category — not translated. Bad translation is a P1 (P0 when it changes meaning: money, dates, legal,
consent, destructive actions).

Rule zero: **research first, translate second, review in context third.** Never translate a catalog
string by string from English with no glossary, and never ship a locale nobody looked at on screenshots.

## Step 1 — Research the locale (before writing a single string)
Write the answers into `qa/l10n/<locale>-glossary.md` (template: [../templates/glossary-template.md](../templates/glossary-template.md)).

| Question | Why it matters | Example |
|---|---|---|
| Which **variant** exactly? | Vocabulary, spelling and grammar differ a lot. | pt-BR vs pt-PT; es-419 (LatAm neutral) vs es-ES vs es-MX/es-AR |
| **Register / form of address** used by apps in this market? | Wrong register sounds foreign or rude. | pt-BR: *você*, friendly, imperative (*Toque em…*). pt-PT: *tu* is common in consumer apps, or impersonal infinitive (*Iniciar sessão*); avoid Brazilian *você* forms. es-419: most consumer apps use *tú*; finance/legal/government often *usted* — pick one, never mix. |
| **Everyday words** vs dictionary words? | The dictionary word is often not the one people use. | pt-BR *celular*, *tela*, *app/aplicativo*, *baixar*; pt-PT *telemóvel*, *ecrã*, *aplicação/app*, *transferir*; es-419 *celular*, *pantalla*, *descargar* (es-ES *móvil*) |
| **OS standard terms** in that language? | Users learned these from their phone; deviating feels off. | see table below — always confirm on a device/emulator in that language |
| **Category jargon** in that market? | Legal/finance/health words are country-specific. | co-parenting: pt-BR *guarda compartilhada*, *convivência*, *pensão alimentícia*; pt-PT *responsabilidades parentais*, *residência alternada*, *pensão de alimentos*; es-419 *custodia compartida*, *régimen de convivencia/visitas*, *cuota/pensión alimentaria/alimenticia* (varies by country) — verify each in research |
| Gender, plural, formality rules | Plurals and agreement break naive interpolation. | ICU plurals (`one/other`; pt-PT/es also `many` in some CLDR versions), gendered adjectives after a name |
| Typography & punctuation | Small tells of machine translation. | pt/es: no Title Case In Buttons; es ¿…? ¡…!; pt-BR *e-mail*; quotes “ ” / « » (pt-PT) |
| Units, formats | Handled in [i18n-and-formatting.md](i18n-and-formatting.md) | R$ 1.234,56 · 1234,56 € · 30/10/2026 |

### OS / Material standard terms (starting point — verify on a device set to that language)
| English | pt-BR | pt-PT | es-419 |
|---|---|---|---|
| Settings | Configurações | Definições | Configuración |
| Sign in / Log in | Entrar / Fazer login | Iniciar sessão | Acceder / Iniciar sesión |
| Sign out | Sair | Terminar sessão | Salir / Cerrar sesión |
| Sign up / Create account | Criar conta / Cadastrar-se | Criar conta / Registar-se | Crear cuenta / Registrarse |
| Save | Salvar | Guardar | Guardar |
| Delete | Excluir | Eliminar | Eliminar / Borrar |
| Share | Compartilhar | Partilhar | Compartir |
| Download | Baixar / Fazer download | Transferir | Descargar |
| Cancel / OK / Done | Cancelar / OK / Concluído | Cancelar / OK / Concluído | Cancelar / Aceptar / Listo |
| Notifications | Notificações | Notificações | Notificaciones |
| Password / Forgot password? | Senha / Esqueceu a senha? | Palavra-passe / Esqueceu-se da palavra-passe? | Contraseña / ¿Olvidaste tu contraseña? |
| Screen / Phone | Tela / Celular | Ecrã / Telemóvel | Pantalla / Celular (teléfono) |
| Expense / Balance / Settle up | Despesa / Saldo / Acertar (as contas) | Despesa / Saldo / Acertar contas | Gasto / Saldo / Saldar (cuentas) |
How to verify: emulator `adb shell cmd locale set-app-locales com.android.settings --locales pt-PT`
(or system locale), screenshot Settings, Accounts, Share sheet, Google sign-in; and read Google's own
apps (Gmail, Calendar, Drive) in that language — they follow Google's localization style guides.

## Step 2 — Harvest wording from top apps in the same category and market
- Pick **≥5 apps** that people in that country actually use for the same job (for co-parenting/shared
  expenses in BR: the leading local co-parenting apps, Splitwise, Nubank/Mercado Pago "dividir" flows,
  Google Calendar; for PT: local banks' MB Way split, Splitwise; for LatAm: Mercado Pago, Splitwise…).
  Choose by Play Store top charts / search results **in that country** (`&gl=BR&hl=pt-BR`,
  `&gl=PT&hl=pt-PT`, `&gl=MX&hl=es-419`).
- From each, collect: store title + short description, screenshot captions, onboarding, sign-in/up,
  settings, empty states, error messages, notifications, the words for the category's core nouns/verbs.
  Store listing pages are public; in-app strings come from screenshots in the listing, the app itself on
  a test device, or public help centers.
- Put the evidence in the glossary: term → candidates seen (app, where) → **chosen** → rejected (+ why).
- Prefer the term the **majority of top local apps + the OS** use; prefer short over long; prefer
  everyday over legal unless the screen is legal (terms, court export) — then use the country's legal term.

## Step 3 — Tone guide (one short page per locale)
Voice (warm/neutral/serious per screen type), form of address, imperative vs infinitive on buttons,
sentence case, how to write errors (what happened + what to do, no blame), numbers/dates, emoji policy,
words to avoid (calques, other-variant words, MT tells), max lengths for buttons/tabs/chips.

## Step 4 — Translate / rewrite
- Rewrite from the **meaning and the screen**, not from the English sentence. Keep the glossary open.
- Keys get **context comments** in the source catalog (where it appears, max length, variables, gender of
  the subject) — translators (human or model) without context produce calques.
- Interpolation: whole sentences with named placeholders and ICU plurals/select; never concatenate
  fragments (`"You owe " + name + " " + amount`). Gender of names unknown → rephrase neutrally.
- pt-PT is **not** pt-BR with spelling changes; es-419 is not es-ES. Write each separately; share only
  what is truly identical.
- Machine translation / LLM drafts are allowed **only** as drafts fed the glossary + tone guide + screen
  context, and must pass Steps 5-6.

## Step 5 — Automated checks (CI)
- Catalog parity: same keys in every locale; same placeholders; ICU syntax valid; no empty strings.
- No English left in non-en catalogs (heuristic: common English words list), no other-variant words
  (pt-BR catalog must not contain *ecrã, telemóvel, definições, guardar (=save), registar*; pt-PT must
  not contain *tela, celular, configurações, salvar, cadastrar, excluir*); glossary-term consistency
  (the same English term always maps to the chosen word).
- Length budget: flag strings > 1.3× the English length on buttons/tabs.
- Sweep detector `raw-key` / `untranslated` (see [matrix-sweep.md](matrix-sweep.md)).

## Step 6 — Review every string in context (the gate)
- Use the matrix sweep contact sheet for that locale (light, font 1.3, small screen): read **every**
  screen, every state (empty, error, success), every notification, every email/SMS template, the store
  listing, and exported files (PDF/CSV).
- Checklist per string: correct variant · correct register · natural everyday wording (would a local say
  it?) · glossary-consistent · no calque/false friend (pt *pretender* ≠ pretend, *assumir*, *aplicar*;
  es *aplicar* ≠ apply for, *actualmente*) · gender/plural right for 0/1/2/many · not truncated/wrapped
  badly · punctuation/typography native · meaning identical for money, dates, consent, destructive actions.
- Two independent reviewers: one native speaker per locale (best: a tester from that country), or —
  when none is available — two independent agent reviews with the glossary, and list "no native
  review" under **Untested**.
- Copy findings use normal severities: wrong meaning in money/consent/destructive = **P0**; wrong variant,
  wrong register, untranslated, truncated, broken plural, obvious calque = **P1**; awkward but clear = P2.

## Gate
Release only with: a glossary + tone guide per shipped locale; automated checks green; every string
reviewed in context on screenshots; zero P0/P1 copy findings; native sign-off per locale or an explicit
"Untested: native review <locale>" line accepted by the owner.

## Sources
- Google Play country/language store pages (`play.google.com/store/apps?hl=pt-BR&gl=BR`), Android
  system UI and Google apps in each language (via emulator).
- Microsoft Language Portal / Microsoft localization style guides (pt-BR, pt-PT, es-MX, es-419 era
  guides are public): <https://learn.microsoft.com/en-us/globalization/reference/microsoft-style-guides>
- Material Design writing guidance: <https://m3.material.io/foundations/content-design/style-guide>
- Unicode CLDR plural rules: <https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html>
