# CHANGELOG

The routine proposes changes here (1st Sunday of the month). The owner approves and applies them.

## v6 — 2026-10-27 (review round 5, the last of the 5 the owner set: 17 findings, ~16 distinct, none high; all fixed or documented)

- The desk view puts a forbidden category first (it can only die); every queue sends a forbidden category to morta.
- Only re-measurable counts expire (`hit_rate_*`, `repos_*`, `p_ge*`, `showhn_github_pct_*`); samples and fixed
  windows do not, so `checklist_ok` no longer goes red for good after 35 days.
- `mcp_server` is forbidden for saturation, not for its rate (the corrected seeds put its rate above CLIs).
- The baseline covers any repo public before launch day; a missing `publico_em` falls back to the creation date.
- An extended window kills only when the first window was at or below the kill line (`janela1_abaixo`; trigger and
  `lib.decidir`); the category rate must be the current benchmark row; `dono_desistiu` is reopened only by the owner;
  `outro` never counts as a second channel and `canal` comes from the URL host; S1–S3 are all checked per cycle.
- The launch polish of an already public repo has no hour floor; AI hooks in Portuguese; the queue weighs rate ×
  demand; the sheet has `como_chega` (given to the advocate); the niche search has no creation filter and the
  benchmarked incumbent of a `lib_benchmark` is a `rival`; the fake-star audit no longer claims X/Bluesky searches.
- Known limits (14) now list the guards that stay heuristic.

## v5 — 2026-10-27 (review round 4: 12 findings, ~10 distinct, all fixed; 2 high)

- **High:** the seeded CLI hit rate was inflated ~3× by an incomplete Search API count; re-measured live (Rust
  37/10,425, Go 18/10,821, all CLIs 169/88,406) and the owner lowered `categoria_hit_min` from 0.5% to 0.15%. A test
  now checks every hit-rate row against its k/n note.
- **High:** the pre-launch baseline follows `repos.publico_em` (when the repo went public), not its creation: a repo
  built private is public from launch day and no longer blocks every decision.
- The build queues apply every build cut of the database through one view (`mesa_cortes`); `q_mesa_reprovada` returns
  the failed cut and its destination.
- A `pronta` idea holds the build slot; exempt categories never use a rate; real build hours have an owner phrase, a
  Friday ask and their own refusal (`horas_reais_insuficientes`); the fake-star audit checks Trending, X and Bluesky
  first and asks the owner before archiving; benchmarks re-measured at 28+ days; Reddit scores need the owner's OAuth
  app (else `termometro`); `carga_itens_por_1k_cli` is a premise.

## v4 — 2026-10-27 (review round 3: 22 findings, ~19 distinct, all fixed; 1 high)

- **High:** the incentivized-stars cut is no longer claimed as a database guard: it is the advocate's fifth question,
  the L0 item and the post-launch audit.
- Cycle guards: `lancada`, `tracao` and `hit` need a post or a confirmed stage of the current cycle; a relaunch
  without its S1 shows in `q_checklist`.
- The extended window kills only at the kill line; between the lines it is `inconclusiva` → arquivada.
- Repos public before launch: a 28-day pre-launch baseline is required and windows are judged net of it.
- Suspect star days block any decision, with a numeric spike rule and a third-party-post search; the portfolio goal
  and conversion leave them out; a hit is a confirmed S3.
- The advocate closes every complete desk (no queue/advocate deadlock); checklist proofs have one written procedure
  (upsert, every item re-proved on each build); NULL rate/load/category goes to `q_mesa_reprovada`.
- Niche taken by an active successor of any age; exempt category labels only when literal and without a measured
  rate; queue demand normalized by type threshold; real build hours at `pronta`; AI hooks after an article;
  owner phrases in capitals; trusted publishing only with a registry; personal-account fake-star rule.
- Seeds: the Show HN endpoint was split by an unquoted comma; `seed.py` removes a half-seeded database; backups
  carry the time; `decidir` documented with named arguments.

## v3 — 2026-10-27 (review round 2: 19 findings, ~14 distinct, all fixed; 2 high)

- **High:** launch cycles: a reopened idea starts a new cycle; launches and hypotheses carry it, windows run from the
  cycle's first launch, a relaunch re-proves the checklist and the two-channel kill counts only this cycle's channels.
- **High:** desk failures have a destination (`q_mesa_reprovada` → arquivada/morta) and `q_fila_construcao` lists only
  buildable ideas.
- The extension needs a channel not used in the window, posted after it ended; the load ceiling stays with the
  low-maintenance mode (doubled) and uses the CLI rate for `cli`; pre-registration fails closed; suspect star days are
  left out of windows and block confirmation; hooks that sell AI and one-offs below `horas_mvp_min` are refused; hits
  counted from effective states; snapshots only for alive ideas; transitions inside one SAVEPOINT.

## v2 — 2026-10-27 (review round 1: 16 findings, all fixed; 3 high)

- **High:** the extension measures a new window from the second channel (`estendida_em`, checked against a
  `lancamentos` row of another channel); an `estender` without a second channel expires to `inconclusiva`.
- **High:** open sibling hypotheses are closed (`inconclusiva`) before an idea leaves for arquivada/morta/tracao/hit;
  stages are decided only while measured, over a window with one star row per day.
- **High:** benchmarks no longer expire as a time bomb: only own measurements are re-measured (35 days), and the suite
  pins the seeds' date.
- Category rate tied to a benchmark row (measure a missing segment on the spot); sheet changes void the advocate;
  niche check fails closed; demand thresholds in the database on every entry in candidata; owner-only transitions as
  explicit pairs; `gh_issues_reacoes` filters issues older than a year; the queue no longer flags finished desks;
  own repo registered at build time; traffic only required with a push-access token; category definitions.

## v1 — 2026-10-27

- First version, built from the research synthesis of 2026-10-27 (7 research fronts, 137 findings, 55 re-verified by
  a red-team): demand-first funnel (D0–D2), launch gate L0, stages S1/S2/S3 on organic stars after the first launch
  channel, two-channel kill rule, low-maintenance mode, fake-star filter.
- Seeds: 61 sourced benchmarks, 31 data sources (status from the live test), 3 stage thresholds, 29 config keys.

### Assumptions without a source (premissa)

- `horas_mvp_max` 20, `carga_min_por_item` 10 min, `carga_semanas` 13, `carga_max_h_semana` 3, `categoria_hit_min`
  0.5%, the S1/S2/S3 kill lines (2, 29, 299), `conv_visita_estrela_min` 3%, `m1_issues_por_1k_pausa` 10,
  `m2_dias_sem_push` 42, `pausa_max_semanas` 4, `leitura_carencia_dias` 3.

### Open points

- Reddit, X, Bluesky and Product Hunt are unmeasured; Trending thresholds come from one snapshot.
