# <locale> glossary + tone guide (qa/l10n/<locale>-glossary.md)

Variant: e.g. pt-BR (Brazil) — not pt-PT · Format locale: pt-BR · Currency default: BRL
Reviewer(s): name, native? y/n · Last reviewed: date, build

## Research log
| Source | What we took from it |
|---|---|
| Android system UI in <locale> (emulator screenshots) | Configurações, Entrar, Sair… |
| Top app 1 (Play listing + in-app, country store) | … |
| Top app 2 … 5 | … |
| Style guide (Microsoft <locale>, Material) | … |

## Conventions (from CLDR/Intl, verified on device — see reference/locale-conventions.md)
| Convention | Value | Verified on device (Hermes)? |
|---|---|---|
| Decimal / grouping | `,` / `.` | |
| Currency format | `R$ 1.234,56` (NBSP) | |
| Negative / percent | `-R$ 5,00` / `12,5%` | |
| Date / time | `30/10/2026` / `18:05` | |
| First weekday | Sunday (product decision: …) | |
| Plurals | one (0,1) / many / other | |
| Phone / postal code | `(11) 91234-5678` / `01310-100` | |
| Quotes, sorting | “ ” / `Intl.Collator('pt-BR')` | |

## Tone guide
- Form of address: você · voice: warm, calm, neutral (sensitive topic) · buttons: infinitive or imperative? (pick one)
- Sentence case; no exclamation marks in errors; errors = what happened + what to do
- Max lengths: button ≤ 18 chars, tab ≤ 12
- Avoid: calques, other-variant words (list), legalese outside legal screens

## Terms
| English (source) | Chosen | Rejected (why) | Seen in (source) | Notes (gender, plural, context) |
|---|---|---|---|---|
| Settings | Configurações | Definições (pt-PT), Ajustes (iOS) | Android pt-BR | |
| Sign in | Entrar | Logar (slang), Iniciar sessão (pt-PT) | Android, Gmail | |
| Expense | Despesa | Gasto (ok in speech) | top apps … | fem. |
| Co-parent | … | … | … | |
