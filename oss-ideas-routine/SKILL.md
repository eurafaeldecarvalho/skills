---
name: oss-ideas-routine
description: >-
  A daily autonomous routine that finds, validates and only then proposes building open-source repositories meant
  to spread and earn GitHub stars, for a solo developer who builds with AI. Use it when setting up or running a
  recurring "find me a repo idea that can go viral" agent (any agent with a persistent folder, terminal and web
  access), when the owner asks why a repo idea was killed or archived, or when planning a launch. It starts from
  measured unmet demand (heavily upvoted issues the maintainers declined, popular abandoned repos, "is there a
  tool" threads), filters by category hit rate and maintenance load, keeps all state in SQLite with
  database-enforced guards, gates the launch with a checkable README/security list, and judges each idea by the
  organic stars after the owner's own launch posts. No fake or incentivized stars, no AI-written posts. For game or
  app ideas use `games-ideas-routine` or `apps-ideas-routine`.
---

# Open-source ideas routine (demand → build → launch → stars)

A daily routine for an autonomous agent. It looks for repository ideas with **measured demand that nobody serves
well**, keeps only the categories where a solo developer has a real chance, has the owner build a small,
demonstrable first version, checks the repo against a launch gate, and then **measures the organic stars** that
follow the owner's launch posts. Everything it decides is stored in SQLite and guarded by triggers, so an agent
that follows this text cannot push an idea through the funnel by mistake, by a convenient label or by skipping a step.

**Threat model.** The guards stop errors, rationalization and shortcuts that this text allows; they cannot stop an
agent that deliberately rewrites rows against it (the agent owns the database file). Therefore: write a column only
where this text says to write it; never `UPDATE` or `DELETE` a row of `hipoteses`, `ideia_eventos`, `evidencias`,
`sinais`, `lancamentos`, `estrelas_diarias`, `traffic`, `checklist` or `limiares` except through the procedures
written here (e.g. 7.2 for proving and re-proving checklist items); never touch `schema.sql` objects (no `DROP`/`ALTER`); never type an owner phrase that is not
literally in `inbox/`.

**What success looks like, honestly.** Of the 58.2 M repositories created in 2025, 0.0455% passed 100 stars and
3,219 passed 1,000 `[bench:repos_ge_100_estrelas/github_2025]` `[bench:repos_ge_1000_estrelas/github_2025]`. A Show HN
of a GitHub repo has a median of 2 points and reaches 100 points 1.8% of the time
`[bench:showhn_github_pontos_mediana/hn_12m]` `[bench:showhn_github_pct_ge100/hn_12m]`. No funnel removes that. What
this one does is stop the owner from spending weeks on ideas without demand, in crowded categories, or that will
drown 8–10 h/week in issues if they succeed — and make every launch count.

## How to use this skill

1. **Copy the folder** to the agent's persistent workspace. The text assumes `/workspace/rotina-oss/`; change
   `dir_base` in `seed_config.csv` if yours differs.
2. **Schedule two runs** in the owner's timezone: (A) daily at 08:00 and (B) Friday at 18:00 (section 3).
3. **First run = bootstrap** (3.1): it runs `seed.py`, tests every data source live and sends the owner the
   prerequisites (GitHub token, Hacker News account, Lobsters invite, Reddit history).
4. **Adapt the owner profile** in `seed_config.csv` before the first run: hours per week, the MVP hour cap, the
   maintenance cap, the 12-month goal. Defaults are a Brazilian solo dev with 8–10 h/week.
5. **Run the tests** whenever the folder changes: `python3 -m unittest discover -p 'test_*.py'` (the suite pins the
   profile values its fixtures use, so adapting `seed_config.csv` never breaks it).

**Language.** Rules and code are in English; **identifiers stay in Portuguese** (tables, columns, state values such
as `candidata`, `lancada`, `morta`) because the database, queries and tests depend on them. Owner-facing messages and
the literal owner phrases (e.g. "aprovo a construção da ideia#12") are in Brazilian Portuguese.

| File | What it is |
|---|---|
| `SKILL.md` | The routine: mission, demand gate, cuts, desk, build, launch gate, measurement, after launch, outputs |
| `schema.sql` | SQLite schema with the guards (demand before candidacy, forbidden categories, free niche, maintenance cap, one build at a time, owner phrases, launch checklist, two-channel kill, pre-registered hypotheses decided only from data) |
| `queries.sql` | Named queries for every recurring decision |
| `lib.py` / `test_lib.py` | Deterministic math (stage decision, Wilson interval, owner proof, maintenance load, fake-star signature, conversion, expected stars per Show HN band) |
| `test_schema.py` / `test_queries.py` / `test_e2e.py` / `test_review_r*.py` | Tests of the guards, the queries and the funnel end to end |
| `seed.py` + `seed_*.csv` | Bootstrap and seeds: config, sourced benchmarks (verified 2026-10-27), thresholds, data sources |
| `CHANGELOG.md` | Version history and open points |

---

## 0. Files, persistence and owner input

- **Base folder:** `/workspace/rotina-oss/` (persistent). The GitHub token lives in `secrets/github_token` (never
  printed, logged or committed; refer to it by file name only).
- **Start of every run, in this order:**
  1. `cd /workspace/rotina-oss`; check `python3` and `sqlite3`.
  2. Run the tests. If they fail, **stop** and warn the owner in the chat.
  3. Without `.bootstrap_feito`, run the bootstrap (3.1) and create the file at the end.
  4. Open `rotina.db`, run `PRAGMA foreign_keys=ON` (per connection), check `PRAGMA integrity_check` = `ok` and
     `PRAGMA user_version` = 1. A broken database is restored from the newest file in `backups/`.
  5. Open a `runs` row (`status='rodando'`); a `rodando` row older than 3 h becomes `falhou`.

### 0.1 Owner input

1. **Save before processing.** Save every new owner message to `inbox/AAAA-MM-DD-HHMM-chat.md`: one header line
   `## AAAA-MM-DD HH:MM`, then the message on the next line exactly as written (no prefix or markdown before it).
2. **Record each item** with `ator='dono'` and `prova_dono` = the literal quote in quotation marks, then the date:
   `'"<phrase…>" chat AAAA-MM-DD HH:MM'` — the opening quote is the first character.
3. **Move** processed files to `inbox/lido/`.
4. **Check:** every `prova_dono` written in the run passes `lib.prova_existe(prova, texts_of_this_run, ideia_id,
   frase)` before the COMMIT (`frase` = the phrase below with the id filled in; for a launch, the prefix
   "lancei a ideia#N"); if it fails, `ROLLBACK`. Every transition goes as its event + the UPDATE inside one
   `SAVEPOINT`, rolled back as a whole on any error (a refused UPDATE otherwise leaves an orphan event).

**Owner phrases** (the database checks them at the START of the quote, straight or curly quotes, any letter case):
- build approval: "aprovo a construção da ideia#N" (`candidata → em_construcao`);
- launch: "lancei a ideia#N no <canal>" with the post URL in the same message (`pronta → lancada`, and every later
  channel as a `lancamentos` row);
- reopening of a serious death: "reabro a ideia#N";
- giving up: "desisto da ideia#N" (→ `morta`, `motivo_morte='dono_desistiu'`);
- hours by idea and type: "horas ideia#N construcao: X" (or `lancamento`/`manutencao`) → one `horas` row with
  that quote as `prova_dono` (frase = "horas ideia#N"). The daily message asks for them every Friday while an idea
  is `em_construcao`; `pronta` needs ≥ `horas_mvp_min` real build hours (`horas_reais_insuficientes`).

A phrase literally in the inbox that the database still refuses is a malformed quote (fix it, never ask again) or an
order that does not fit the idea's state: then open a pending item quoting it and explaining the valid path.

---

## 1. Goal

| | Year 1 | Then |
|---|---|---|
| Mother metric | `E30` = organic stars in the 30 days after the first launch channel ≥ 100 on at least one repo (`q_janela`) | the same, on 1 repo per quarter |
| Portfolio | `q_meta.estrelas_12m` ≥ `meta_estrelas_organicas_12m`; `hits_12m` ≥ `meta_hits_12m` (a repo past 1,000 stars in 90 days) | set by the owner |
| Process | ≥ 4 launches with two channels each; no build without a demand signal | — |

**Why E30.** Stars concentrate at launch: 59–74% of a launched repo's current stars arrived in its first 30 days
`[bench:pct_estrelas_em_30d_pos_hn/hn_posts_2025-11_2026-07]`, and the median peak is week 3
`[bench:semanas_ate_pico_mediana/repos_gt2000_abr-jul26]`. A repo that did not move in 30 days rarely moves later.

---

## 2. Principles

1. **Demand before code.** An idea enters the funnel only with a behavioral demand signal (4.2): people already
   asked for it with reactions, or abandoned a popular tool that did it.
2. **Category beats execution.** The share of a topic's 12-month repos that passed 1,000 stars ranges from 0.07%
   `[bench:hit_rate_gt1000_build_your_own_name_12m/name_build_your_own]` to 0.93%
   `[bench:hit_rate_gt1000_awesome_12m/topic_awesome]`; CLIs sit at 0.17–0.36%
   `[bench:hit_rate_gt1000_cli_rust_12m/topic_cli_rust]`. The routine only builds at or above
   `[config:categoria_hit_min]` (0.15%, a premise set by the owner).
3. **Mechanical provenance.** Every number in a sheet, digest or message carries a mark: `[sinal#id]`,
   `[bench:metrica/segmento]`, `[config:chave]`, `[limiar:etapa/metrica]` or `[metrica q_<query> AAAA-MM-DD]`. Counts,
   ids and dates read from the routine's own database need no mark. Without a mark, `checklist_ok=0`.
4. **The launch is the event.** The repo goes public on launch day with README, demo and release ready; a repo
   opened "in progress" spends its novelty.
5. **One post is noise.** The first weak channel only archives an idea; killing needs two different channels (8.3).
6. **Stars are the behavior; never manufacture them.** Buying, trading or rewarding stars, alternate accounts,
   star-for-star, asking friends or AI assistants to star, asking for upvotes: forbidden — GitHub's Acceptable Use
   forbids rank abuse and incentivized engagement, and fake stars help for under 2 months and then hurt
   `[bench:starscout_efeito_promocional_dias/github]` (90% of the fake-starred repos were deleted
   `[bench:starscout_pct_repos_deletados/github_2019_2024]`).
7. **The owner writes and posts.** Hacker News forbids AI-generated or AI-edited text and automated posting; the
   routine suggests angles, the owner writes every title, post and first comment and posts by hand.
8. **Built with AI, sold for what it does.** Titles sold as "AI/agent/LLM/MCP" reach 100 points in 1.31% of Show HN
   posts against 2.14% for the rest `[bench:showhn_titulo_ia_pct_ge100/hn_12m]`; declaring AI use in the README does
   not hurt. The README says in one line how AI was used and what the owner tested.
9. **Calculations only through `lib.py`.** Never do the math in your head.

---

## 3. Runs

### 3.1 Bootstrap (only without `.bootstrap_feito`)

Resuming a broken bootstrap: `seed.py` removes the database when a seed fails (fix the seed and run it again); if
`rotina.db` exists with `PRAGMA user_version=1` and a non-empty `config`, skip step 1 and resume at step 2
(`seed.py` refuses an existing database).

1. `python3 seed.py rotina.db` (it also creates `backups/`, `inbox/lido/`, `digests/`, `posts/`, `adv/`, `secrets/`).
2. **Sources:** test each source of `fontes` with 1 request; record `ok`/`degradada`; a source that needs the
   owner's key and has none in `secrets/` → `desligada` (no alert).
3. **Measurements:** re-measure every `medicao_propria` benchmark older than `[config:benchmarks_reverificar_dias]`
   before the first desk (`q_checklist.benchmarks_vencidos` lists them).
4. **Prerequisites to the owner** (one message): a GitHub token in `secrets/github_token` with push access to the
   owner's repos, private ones included (search limits are 10/min without a token; the Traffic API and the private
   repo of a build need push access — without it `gh_traffic` stays `desligada` and traffic is not required); a Hacker News account; a Lobsters invite **now** (self-promotion only
   after 70 days of account and under 1/4 of its activity); a Reddit account with history in the target subs and,
   for scores, a Reddit OAuth app (client id/secret in `secrets/reddit`; without it `reddit_rss` signals are
   `termometro` only, never demand);
   whether to register the owner's existing public repos (13).
5. Send "bootstrap: N fontes ok, N degradadas" and the prerequisites.

### 3.2 Daily run (A), in this order

1. Owner input (0.1).
2. **Own repos** (states `lancada`, `tracao`, `hit`): the stars per day from `gh_star_history` into `estrelas_diarias`,
   **one row per day since the first launch, zeros included** (`INSERT … ON CONFLICT(ideia_id,data) DO UPDATE`; after a
   failed or skipped run, backfill the missing days first — the database refuses a decision over a window with a
   missing day), traffic of the last days into `traffic` (GitHub keeps 14 days),
   a `repo_snapshots` row (stars, forks, open issues, `pushed_at`); weekly, a snapshot of the owner's repos in
   `em_construcao`/`pronta` and of the competitors linked to every alive idea.
3. **Decisions:** `q_hipoteses_abertas` → decide each open hypothesis (8.2); `q_m1_saude`, `q_m2_congelado` (9).
4. **Queues:** `q_mesa_reprovada` (every finished desk the database would refuse, with its `corte`) →
   `categoria_proibida` and `nicho_tomado` → `morta` with that reason; any other `corte` → `arquivada` with it as
   `reabrir_se`; `q_sinais_parados` → `arquivada` (`reabrir_se`='novo sinal de demanda'); `q_candidatas_paradas` →
   run the desk today or archive with the missing criterion as `reabrir_se` (in every queue, an idea whose
   `categoria` is forbidden goes to `morta`/`categoria_proibida`, never `arquivada`); `q_construcao_longa` and
   `q_pronta_parada` → one pending item each (cut scope, launch date or archive).
5. **Discovery** (4), within `trava_buscas_dia` and `teto_minutos_run`: demand sources first, then rankings.
6. **Desk** (6) for up to 2 new candidates; the devil's advocate (6.3) closes each desk whose sheet is complete, and
   runs again for any candidate whose sheet changed (`advogado_em` back to NULL). `q_fila_construcao` lists only
   candidates that already have it and pass every build cut of the database (view `mesa_cortes`).
7. **Build proposal** when the build slot is free: the top of `q_fila_construcao` with its sheet, as a pending item
   asking for "aprovo a construção da ideia#N".
8. In this order: draft the summary and the digest (11, not sent yet); backup (`VACUUM INTO
   backups/rotina-AAAAMMDD-HHMM.db`: `VACUUM INTO` fails on an existing file, and a resumed run makes a second one the
   same day; keep the last 14 days); `q_checklist` (11.2) including the marks of the drafts; record
   `checklist_ok` and close the run; send the summary.

### 3.3 Friday run (B)

The weekly digest (11.3), the Trending snapshots of the week, and the launch plan of the next week for any `pronta`
idea (channel, day, the 3 angles for the owner to write about).

---

## 4. Sources and signals

### 4.1 Collection rules

- Use only `fontes` (seeded and tested live on 2026-10-27; read `termos_nota` of each before use). Respect `limite`;
  read `x-ratelimit-remaining` and stop the source below 5; stop it at the first secondary-limit 403.
- **GitHub search:** repeat a query while `incomplete_results=true` (counts can come back 25% short); after 3
  incomplete tries record nothing. Slice date ranges to ≤ 15 days for lists.
- **Stars:** only `/repos/{o}/{r}/stargazers/history` (official since 2026-09; its sum matches `stargazers_count`).
  The stargazers *list* is closed to third parties; GH Archive, the ClickHouse dataset and OSS Insight trends are
  stale or dead (`status` in `fontes`).
- **Reddit:** only the RSS (`.json` returns 403 without OAuth); scores need the owner's OAuth app (3.1 step 4).
  Without it a Reddit post cannot prove `demanda_pontos_min` and is recorded as `termometro`.
- **A signal counts** only with HTTP 200 **in this run**, a `trecho_literal` ≥ 40 characters and `payload_json`
  `{sha256 of the body, Date header}` (the database refuses less). Record with `INSERT … ON CONFLICT(hash) DO NOTHING`.
  Recording a signal, URL or number from memory is forbidden.

### 4.2 Signal types (`sinais.tipo`)

**Demand** (the only types that make an idea `candidata`):

| Type | What qualifies | Source |
|---|---|---|
| `issue_reacoes` | an open `enhancement` issue with ≥ `demanda_reacoes_min` (100) 👍, created more than 1 year ago (`created:<{D365}`; the date and label filters are mandatory: without them the search returns memes) | `gh_issues_reacoes` |
| `issue_not_planned` | an `enhancement` issue closed as "not planned" with ≥ `demanda_reacoes_min` 👍; read the closing comment (votes and crashes do not count) | `gh_issues_not_planned` |
| `repo_abandonado` | a repo with ≥ `demanda_estrelas_abandonado_min` (5,000) stars, no push for > 12 months, ≥ 200 open issues and recent requests in them | `gh_repos_abandonados` |
| `pedido_ferramenta` | an "Ask HN" or subreddit post with ≥ `demanda_pontos_min` (20) points asking for a tool (validate the "Ask HN:" prefix; the tag leaks) | `hn_algolia_ask`, `reddit_rss` |

Record `reacoes` on the signal — the issue's 👍, the post's points, or the abandoned repo's stars; the database
accepts a demand signal only at or above its threshold, on every entry in `candidata` (reopenings included). **Other types** (`ranking`, `lancamento_concorrente`, `termometro`)
inform the desk and the competitor list but never qualify an idea; `dono_campo` is an owner note (`url_status=0`).

### 4.3 Competitors and the fake-star filter

Every repo the desk cites (reference, successor, rival, abandoned origin) goes to `repos` with `criado_em` and a
`repo_snapshots` row, and is linked in `ideia_repos`. Before a competitor counts as "niche taken" or a repo enters a
benchmark, run `lib.suspeito_fake(weekly stars, fork_star)` on its `stargazers/history`: one week with > 70% of all
stars and every later week under 1% of that peak, or forks/stars < 0.01 (median 0.097
`[bench:fork_star_mediana/repos_gt2000_12m]`) → `suspeito_fake=1`. Also flag a personal account (not an organization) with > 5 repos above
2,000 stars in 12 months, or near-identical weekly series across one owner's repos. A suspect repo never takes a
niche and never enters `seed_benchmarks`.

---

## 5. Cuts (the database enforces the starred ones; the others are the advocate's, 6.3)

1. **Forbidden category*** → `morta` (`categoria_proibida`), the only exit the database allows:
   `prompts_vazados` (ToS/DMCA risk), `framework_agentes` and `self_hosted_completo` (maintenance beyond 8–10 h/week;
   dominated by organizations), `mcp_server` (saturated: 34,399 new repos in 12 months, 3× the CLI-Rust topic, and the top dominated by known
   names and organizations `[bench:hit_rate_gt1000_mcp_server_12m/topic_mcp_server]`; its rate is not the reason),
   `build_your_own` (1 in 1,373 passed 1k `[bench:hit_rate_gt1000_build_your_own_name_12m/name_build_your_own]`).
2. **Niche taken*** → `morta` (`nicho_tomado`): a non-suspect successor of any age with > 1,000 stars and a push in
   the last 90 days, linked as `papel='sucessor'`. `sucessor` = any repo that solves the same problem for the same
   user (it says it replaces, forks or continues the reference, or the reference's issues point to it); the label is
   by that definition, never by the repo's age or size, and the advocate checks it.
3. **Weak category*** → no build: `hit_rate_categoria` below `[config:categoria_hit_min]`. `lib_benchmark`,
   `sucessor_abandonado` and `alternativa_open` never use a rate (no topic rate exists; their cases carry the desk):
   leave it NULL; the database ignores one if recorded. Cuts 3 and 4 send the idea to `arquivada` with the failed cut as `reabrir_se`
   (`q_mesa_reprovada`).
4. **Maintenance load*** → no build: `lib.carga_h_semana(estrelas_alvo, itens, [config:carga_min_por_item],
   [config:carga_semanas])` above `carga_max_h_semana`, with `itens` = `[config:carga_itens_por_1k_cli]` for `cli`
   and `[config:carga_itens_por_1k]` otherwise; `modo_baixa_manutencao=1` (9.1) doubles the ceiling, never removes
   it. At the defaults (1,000 stars) the cut rarely fires; it bites on large `estrelas_alvo`.
   Lifetime load is ~22 issues+PRs per 1,000 stars `[bench:issues_prs_por_1k_estrelas_vida/github_virais]` (7.7 to
   66 in that sample, the top for daily-use CLIs); `carga_itens_por_1k_cli` = 60 is a premise from that top end.
5. **Incentivized stars** → `morta` (`estrelas_incentivadas`, owner-only reopening): any plan whose traction
   depends on principle 6's forbidden practices. The advocate asks it every time (6.3); the L0 item
   `sem_pedido_estrela` checks the repo (its proof is the grep command over the repo and its empty result), and 9.2
   audits the stars after launch.
6. **Quick one-off** → `morta` (`advogado_do_diabo`): nothing a reader could not build in an afternoon, no number to
   prove value, or not runnable without sign-up (Hacker News: "Don't post quickly-generated one-offs"). The
   database refuses `horas_estimadas` below `[config:horas_mvp_min]` at the build (`one_off`), fewer real build
   hours (`horas`, `tipo='construcao'`, 0.1) at `pronta` (`horas_reais_insuficientes`) — neither applies to the launch
   polish of a repo that is already public (13) —, and a `gancho` that opens with "AI", "agent(s)", "agentic", "LLM",
   "GPT", "MCP", "IA", "agente(s)", "assistente", "copilot" or "chatbot", after an optional article (`gancho_vende_ia`): sell the result, not the technology. Both
   are heuristics; the advocate judges the rest.
7. **License*** : MIT or Apache-2.0; AGPL-3.0 only with the owner's reason (Google forbids it internally; 5.6% of the
   repos above 1k stars since 2025 `[bench:share_licenca_mit/repos_gt1000_desde_2025]`).

---

## 6. Desk, sheet and build proposal

### 6.1 Desk criteria (D0–D2)

- **D0 Demand:** ≥ 1 demand signal (4.2) linked in `evidencias` (database: `sem_sinal_de_demanda`).
- **D0 Niche:** search for a successor (`gh_search_repos` by the problem's words, any creation date, `pushed:>`
  90 days ago, sorted by stars; record the query URL in the idea's `nota`). Link what you found with `criado_em` and a
  snapshot (`pushed_at` included): `sucessor` = a repo that already delivers this idea's `prova_numero` to the same
  user, or the declared continuation of the abandoned origin; `rival` = an adjacent one, including the incumbent a
  `lib_benchmark`/`alternativa_open` is measured against (beating it is the pitch); `abandonado` = the origin. The database refuses the build without at least one linked repo
  with a complete snapshot (`sem_concorrente_verificado`), with a successor whose dates are missing
  (`concorrente_incompleto`), and applies cut 2.
- **D1 Category:** set `categoria` by its definition below and copy `hit_rate_categoria` from a `benchmarks` row,
  recording that row in `hit_rate_benchmark_id` (the database refuses a rate that differs from it). A category or
  language without a row: measure it now with `gh_search_count` (`topic:<t> language:<l> created:>{D365}` with and
  without `stars:>1000`, repeating while incomplete) and insert a `medicao_propria` row with that `source_url`; never
  borrow another segment's rate. Cut 3. The exempt labels (`lib_benchmark`, `sucessor_abandonado`,
  `alternativa_open`) apply only when their definition fits literally (the advocate checks the label); they are
  never measured.

  | `categoria` | Definition (the advocate checks the label) |
  |---|---|
  | `cli` | a command-line tool the user runs directly |
  | `lib_benchmark` | a library whose pitch is a measured number against alternatives |
  | `skill_harness` | Claude Code / agent skills, CLAUDE.md, harnesses |
  | `sucessor_abandonado` | a maintained successor of a `repo_abandonado` signal |
  | `alternativa_open` | an open-source alternative to a paid product, scoped to one feature |
  | `lista_curadoria` | an awesome list or curated index |
  | `mcp_server` | anything whose main deliverable is an MCP server (forbidden) |
  | `self_hosted_completo` | a full self-hosted product (forbidden) |
  | `framework_agentes` | an agent framework or platform (forbidden) |
  | `prompts_vazados` | leaked, jailbreak or system-prompt collections (forbidden) |
  | `build_your_own` | sold by the "build your own X" label (forbidden) |
  | `outro` | none of the above; requires a measured rate for its topic |

  When an idea fits a forbidden category and an allowed one, the forbidden one wins.
- **D2 Load:** `estrelas_alvo` (default `[config:estrelas_alvo_padrao]`) and `carga_h_semana` via the lib; cut 4.

### 6.2 The sheet (all required before the build; the database checks them)

`categoria`, `gancho` (in English: what it does, in one line, no AI buzzword as the hook), `prova_numero` (the number
the README top and the post title will show: a benchmark, a before → after), `como_chega` (how users will find it:
the channels of 7.3 and the mechanism, never a reward or request for stars), `linguagem`, `horas_estimadas` (≤
`horas_mvp_max`), `estrelas_alvo`, `carga_h_semana`, `hit_rate_categoria`, `licenca`, and a fresh devil's advocate.
Ranking of the queue: `q_fila_construcao` (category rate over the floor — 1 for the exempt categories — times
demand as a multiple of its type's threshold, then fewer hours).

### 6.3 Devil's advocate (before the build proposal)

In a separate subtask that receives only the sheet (with `como_chega`) and the links: "3 motivos verificáveis para matar esta ideia,
cada um com URL" — always including "já existe e funciona?", "é um one-off de uma tarde?", "a carga cabe em
8–10 h/semana?" and "a categoria e a taxa estão certas pela definição de 6.1?". It kills (`advogado_do_diabo`) only with evidence meeting a cut of section 5. Record
`advogado_em = datetime('now')`. A fifth question is always asked too: "a tração depende de troca, recompensa ou
pedido de estrelas?" (cut 5). The database refuses the build without a run after the last entry in `candidata`,
and any later change to the sheet voids it (`advogado_em` back to NULL: run the advocate again).

### 6.4 Build approval

One build at a time (`slots_construcao`): an idea in `pronta` still holds the slot (it may go back to
`em_construcao`), so the next proposal waits for the launch or the archive. The pending item shows the sheet with marks and asks for "aprovo a
construção da ideia#N". The owner may answer "desisto da ideia#N".

---

## 7. Build and launch

### 7.1 The first version (`em_construcao`)

- Private repo (`repo_full_name`), ≤ `horas_mvp_max` hours, scoped to the demand signal and the `prova_numero`.
  Register it in `repos` with `proprio_ideia_id`=N, `criado_em` the day it is created and `publico_em` NULL (M1/M2
  and the checklist read that link: `q_checklist.lancadas_sem_repo`).
- Brief in `posts/ideia-N-brief.md`: the problem in the requester's words (quote the signal), the proof number and
  how to measure it, the 3-command quickstart, what is out of scope.
- The routine may write code with the owner; it never posts, opens issues in other repos or comments in the
  demand thread.

### 7.2 Launch gate L0 (`em_construcao → pronta`)

Every mandatory `checklist_itens` row needs a `checklist` row with `ok=1` and a `prova` (file and line, API field or
setting), verified during the current build (`verificado_em` ≥ the last `em_construcao` event: a relaunch re-proves
every item); the database refuses `pronta` otherwise. Check by script where possible (README regex, the repo API, the
releases feed, the OpenSSF Scorecard). The items: demo near the top, what/why/how/help/who, SPDX license, 3–20
topics, description, social preview 1280×640 under 1 MB, quickstart in ≤ 3 commands without sign-up, a tagged
release, one line on AI use plus visible tests and CI, the proof number at the top, the low-maintenance files
(SECURITY.md, SUPPORT.md, issue templates, Discussions, open-PR limit), supply chain (Actions pinned by full SHA,
minimal `permissions:`, no `pull_request_target` checkout, push protection, and trusted publishing when the project
publishes to a package registry — a Go binary released on GitHub proves "no registry"), and
**no request or reward for stars anywhere** (including notes addressed to AI assistants). "vs alternatives" is
recommended, not mandatory. README evidence is correlational: none of these items is proven causal.
**Proving an item** (the only way to write `checklist`): `INSERT INTO checklist(ideia_id,item,ok,prova) VALUES(…)
ON CONFLICT(ideia_id,item) DO UPDATE SET ok=excluded.ok, prova=excluded.prova, verificado_em=datetime('now')`. Every
entry in `em_construcao` (a first build, a rebuild after reopening, a return from `pronta`) re-proves EVERY mandatory
item this way before `pronta`. Items that need the repo public (social preview rendering, Scorecard) are proved from
the settings and files while private; the launch-day checks of 7.3 confirm them public.
If an item breaks while `pronta` (e.g. the release was deleted): prove it with `ok=0, prova=<what broke>`, move
`pronta → em_construcao` (routine), fix it and re-prove every item.

### 7.3 Launch sequence (the owner writes and posts everything)

| When | Channel | Rules |
|---|---|---|
| D0, 12–17 UTC (9–14 h BRT) `[config:post_utc_inicio]`–`[config:post_utc_fim]` | **Show HN**, repo public the same day | runnable without sign-up; not trivial; no landing page or waitlist; title says what it does plus the proof number; the owner's "why" as the first comment; never ask for votes; one repost only, and only if the first got no attention |
| D0–D1 | the language or niche subreddit | reread the sub's rules that day (they change; the routine cannot read them from this IP) |
| D1–D7 | Changelog News (submit form), Console.dev (pre-1.0 dev tools only), X/Bluesky with the demo, dev.to "how I built it" | — |
| D7+ | Lobsters (`show` tag) | only with an eligible account |
| 30 days to 5 months | awesome lists | each list's criteria (age, stars, downloads); the PR is written by the owner |

Before D0 the routine writes `posts/ideia-N-lancamento.md` with **angles and facts only** (the proof number with its
mark, 3 possible angles, the questions readers will ask, the channel rules) — never a ready-made title or text.
Expectation, written in the plan: median Show HN = 2 points; ≥ 10 points 8.9% `[bench:showhn_github_pct_ge10/hn_12m]`.

### 7.4 Recording a launch

From the owner's "lancei a ideia#N no <canal>" message: a `lancamentos` row (canal, URL, title, `postado_em`,
`prova_dono`), then `pronta → lancada` on the first one. `canal` comes from the URL host (news.ycombinator.com →
`show_hn`, reddit.com → `reddit`, lobste.rs → `lobsters`, x.com → `x`, bsky.app → `bluesky`, dev.to → `devto`,
producthunt.com → `product_hunt`, changelog.com → `changelog_news`, console.dev → `console_dev`, a github.com awesome
list → `awesome_list`); `outro` only for other hosts, and it never counts as a second channel. A repo the routine
built private (7.1) went public that day: set its `repos.publico_em` to it; a repo registered by section 13 already
has `publico_em` (when missing, the database falls back to its creation date and asks for the baseline). At 72 h record `pontos_72h`/`comentarios_72h` (Algolia
item) and at 7 days `e7`. Pre-register S1, S2 and S3 the same day (8.1).

---

## 8. Measurement and decisions

### 8.1 Pre-registration

**Cycles.** Each reopening starts a new cycle (`ideias.ciclo`+1); launches and hypotheses belong to the cycle they
were recorded in, and every window runs from the cycle's first launch. Old-cycle channels and stars do not count.

On the first launch of a cycle, copy the latest `limiares` version of S1, S2 and S3 into `hipoteses` (metric, criterion,
thresholds, `n_min`, `prazo_dias`, `limiar_versao`); the database refuses a copy that differs
(`pre_registro_diverge_do_limiar`, also when no `limiares` row matches), a hypothesis born decided (`decisao_so_por_update`) and any change to a decided one.

| Stage | Metric | Pass | Kill line | Window | Destination when it fails |
|---|---|---|---|---|---|
| S1 Signal | E14 | ≥ 10 `[limiar:S1/e14]` | ≤ 2 | 14 d | `arquivada` |
| S2 Traction | E30 (mother metric) | ≥ 100 `[limiar:S2/e30]` | ≤ 29 | 30 d | `morta` (`teste_reprovado`) |
| S3 Hit | E90 | ≥ 1,000 `[limiar:S3/e90]` | ≤ 299 | 90 d | `arquivada` (the repo stays public, no more investment) |

### 8.2 Deciding

`lib.decidir('contagem', eventos=eventos_janela, n=dias_cobertos, limiar_passa=limiar_passa, limiar_mata=limiar_mata,
n_min=n_min, eventos_min=0, estendida=estendida, prazo_esgotado=prazo_esgotado, passa_estendido=passa_estendido)` with
the columns of `q_hipoteses_abertas` (`eventos_janela` is already net of `baseline_janela`, the pre-launch pace of a
repo that was public before; 13): the window starts at the first launch, or at
the second channel's date once extended (`estendida_em`), and lasts `prazo_dias`; `dias_cobertos` is capped at the
window; `prazo_esgotado` = window + `leitura_carencia_dias`. Record `n_observado`, `valor_observado` (`eventos_janela`) and
`resultado` and `fechada_em=datetime('now')` in one UPDATE. The database refuses a decision without one star row per day of the window
(`decisao_sem_dado`; for a repo public before launch, `repos.publico_em`, also the 28 days before the cycle's first launch), over an
unresolved suspect day (`estrelas_suspeitas`, 9.2), against the pass line (`decisao_incoerente`) or while the idea is not `lancada`/`tracao`/`hit`
(`ideia_fora_de_medicao`).

| Result | Action |
|---|---|
| `passa` | confirm; S2 confirmed → `lancada → tracao`; S3 confirmed → `tracao → hit` |
| `estender` | a pending item asking the owner for the **second channel** (7.3). When it is posted (a `lancamentos` row of a channel not used in this cycle's window, posted after the window ended), set `estendida=1`, `passa_estendido=limiar_passa`, `estendida_em=<its date>` in one UPDATE (the database checks the channel): a new window of the same length from that date, decided at the same lines: ≥ the pass line `passa`; ≤ the kill line `mata` only with `janela1_abaixo=1` (pass it to `decidir`; the database refuses it otherwise); anything else `inconclusiva` → `arquivada` (`reabrir_se`='entre as linhas após 2 canais'). Without a second channel within `segundo_canal_max_dias` → `inconclusiva`, `arquivada` (`reabrir_se`='2º canal') |
| `mata` with one channel | it is an `estender` (the second channel first); the extension UPDATE also sets `janela1_abaixo=1`, the only case an extended window can kill |
| `mata` with two channels | `resultado='refutada'`, the stage's destination (S1 → `arquivada` with `reabrir_se`; S2 → `morta`, `teste_reprovado`) |
| `inconclusiva` (extended window between the lines) | `resultado='inconclusiva'`, `arquivada` (`reabrir_se`='entre as linhas após 2 canais'); never `morta` |
| `aguardar` / `sem_amostra` | wait; `sem_amostra` at the deadline → `inconclusiva`, `arquivada` (`reabrir_se`='relançamento') |

**Closing the other stages.** Before moving an idea to `arquivada` or `morta`, close its open hypotheses as
`inconclusiva` (`aprendizado`='encerrada por <etapa/motivo>', `fechada_em=datetime('now')`); on `lancada → tracao` close an open S1, on
`tracao → hit` an open S1/S2 the same way. The database refuses the move otherwise (`hipoteses_abertas`).

### 8.3 Two channels before a death

A single post is a noisy sample: Concat had 5 points on Hacker News and has 11.9k stars today. The database refuses
`motivo_morte='teste_reprovado'` with fewer than two distinct channels in the current cycle (`matar_exige_dois_canais`).

### 8.4 Diagnostics (recorded in `aprendizado`, never decide)

- `e7` against `lib.e7_esperado(pontos_72h)` (32 / 127 / 303 / 755 by band): far below = the README lost the
  visitors; within = the channel was the limit.
- `q_conversao`: with ≥ 1,000 unique visitors and conversion < `conv_visita_estrela_min` (3%), rewrite the top of the
  README; above 10%, the problem is distribution. The only public anchor is one case at 13%
  `[bench:conv_visita_repo_estrela/dotenvx]`.
- Language Trending: stars of the day against the last repo of the daily Trending of the language (Python 41,
  TypeScript 12, Rust 27 on 2026-10-27 `[bench:trending_lang_diario_min_python/github_trending_python]`).

---

## 9. After the launch

### 9.1 Low-maintenance mode (mandatory at launch)

Issue templates, Discussions for questions, SUPPORT.md saying support is not guaranteed, the open-PR limit per user
(2), PRs restricted to collaborators when the load spikes, and a "existing users" interaction limit for a week if
needed. `modo_baixa_manutencao=1` on the sheet commits the owner to these before launch.

### 9.2 Health checks

- **M1** (`q_m1_saude`, repos with ≥ 1,000 stars): open issues per 1,000 stars above 6 → `baixa_manutencao`
  (apply 9.1 now); above 10 → `pausa` (a pending item: pause contributions, or archive the repo read-only).
- **M2** (`q_m2_congelado`): no push for `m2_dias_sem_push` days → a pending item: a small release (a release week
  brings ~1.5× the usual stars `[bench:ganho_semana_pos_major_mediana/top5000_2018]`) or archive the repo.
- A pause over `pausa_max_semanas` → archive the repo (read-only) instead of letting it rot.
- **Own fake-star audit:** a spike = a day with ≥ 50 stars and more than half of the stars since the window
  started. Organic sources are checked first: the repo in that day's or the previous day's `gh_trending_html`
  snapshot, an own post that day or the day before, or a third-party post found by searching Hacker News (Algolia),
  Reddit for the repo URL (the routine cannot search X or Bluesky). None found → `estrelas_diarias.suspeito=1` on those days and tell the owner (someone
  else may be buying stars for the repo), asking where it came from — the owner can check X, Bluesky and
  newsletters logged in. A third-party post found → it is organic (`suspeito=0`, record its URL in
  the summary). Suspect days are left out of every window and block any decision (`estrelas_suspeitas`); the owner's
  explanation of an organic source → `suspeito=0`. A hypothesis overdue with a suspect day still open → a pending
  item asking the owner about that day; after `segundo_canal_max_dias` without an answer → `inconclusiva`,
  `arquivada` (`reabrir_se`='dia suspeito explicado').

---

## 10. State machine

| Transition | Condition | Actor |
|---|---|---|
| sinal → candidata | ≥ 1 demand signal (4.2) | routine |
| sinal → arquivada | `q_sinais_parados` | routine |
| candidata → em_construcao | "aprovo a construção da ideia#N" + sheet + advocate + slot + cuts 2–4, 7 | **owner** |
| em_construcao → pronta | every mandatory L0 item proved | routine |
| pronta → em_construcao | an L0 item broke before launch | routine |
| pronta → lancada | "lancei a ideia#N no <canal>" + a `lancamentos` row | **owner** |
| lancada → tracao / tracao → hit | S2 / S3 confirmed | routine |
| any → arquivada | with `reabrir_se` | routine |
| any → morta | with `motivo_morte`; `teste_reprovado` only after two channels | routine / owner |
| morta/arquivada → candidata | a `REABERTA:` event; serious deaths (`teste_reprovado`, `categoria_proibida`, `advogado_do_diabo`, `estrelas_incentivadas`, `dono_desistiu`) only with "reabro a ideia#N"; the routine reopens an idea once | routine / owner |

**The database refuses:** an idea born outside `sinal`; a state change without a matching event; a transition outside
this table; `candidata` without a demand signal; the owner's transitions without the exact phrase at the start of
the quote; a forbidden category leaving except to `morta`; the build with an incomplete sheet, hours above the cap,
an invalid license, no fresh advocate, the slot taken (a `pronta` idea holds it), a weak category, a taken niche or a load above the cap;
`pronta` with a mandatory item unproved; `lancada` without a post; `tracao`/`hit` without the stage confirmed; a
death by test with one channel; leaving to `arquivada`/`morta`/`tracao`/`hit` with an earlier stage still open;
an extension without a new channel posted after the window; `lancada`, `tracao` or `hit` on a post or a stage of an
earlier cycle; a decision over an unresolved suspect day or, for a repo public before launch, without its 28-day
baseline; `pronta` with fewer real build hours than `horas_mvp_min`; an extended window killing after a first window
between the lines; a category rate from a superseded benchmark row; a sheet without `como_chega`; a hook that sells AI; a one-off below
`horas_mvp_min`; a confirmation over suspect star days; `pronta` with proofs from an earlier build; a pre-registration
with no matching threshold; a stage decided outside `lancada`/`tracao`/`hit`, or without one star row per
day of its window; a category rate that differs from its benchmark row; the build after a sheet change without a new
advocate; a demand signal below its threshold on any entry in `candidata`; `morta` without a reason; `arquivada` without `reabrir_se`; a signal without a valid
payload or rewritten later; a launch without the owner's proof; stars from any source but `stargazers_history`; a
hypothesis born decided, decided without star data or against its pass line, or changed after decided; a threshold
version that loosens the previous one; a deleted or edited event.

---

## 11. Outputs

### 11.1 Daily message (PT-BR, ≤ 15 lines)

```
Rotina OSS — <data>
1) Decisões: <ideia#N> <estado> (<motivo, com marca>)
2) Lançadas: <ideia#N> E7 <x> · E30 <y> [metrica q_janela <data>]
3) Pendências do dono (numeradas): aprovar construção / data de lançamento / M1-M2
4) Novos sinais de demanda: <n> · fila de construção: <top 1 com hit rate>
   (sexta, com ideia em construção: "quantas horas na ideia#N? responda: horas ideia#N construcao: X")
5) Checklist: ok | itens que falharam
```

### 11.2 Checklist (`checklist_ok`)

Passes when every `q_checklist` column is 0, every `prova_dono` of the run passes `lib.prova_existe`, every number
of the drafted summary and digest carries a mark (principle 3), `integrity_check` = ok and the backup was written.

### 11.3 Friday digest (`digests/AAAA-MM-DD.md`)

Week's launches with E7/E14/E30, decisions with the stage table, the build queue with sheets, the next week's launch
plan, and "O que aprendemos" (the `aprendizado` of the closed hypotheses).

---

## 12. Calibration (1st Sunday of the month)

- Re-measure every re-measurable `medicao_propria` count (`hit_rate_*`, `repos_*`, `p_ge*`, `showhn_github_pct_*`)
  measured 28 or more days ago (a row from the previous first Sunday
  is 28–35 days old and would expire before the next one), and, any day, every row `q_checklist.benchmarks_vencidos`
  flags: base rates (Search API counts, repeating while incomplete), Show HN P(≥10)/P(≥100) by
  Algolia, the category hit rates; new `benchmarks` rows with `source_url` (never update old ones). Papers and case
  posts do not expire.
- **Thresholds** change only as a new `limiares` version that does not loosen the previous one (the database
  refuses `limiar_nao_afrouxa`); loosening is a CHANGELOG proposal for the owner.
- After ≥ 5 own launches, replace the conversion premise with the median of `q_conversao`.

---

## 13. The owner's existing repos

At the bootstrap the owner may list existing public repos. Register each in `repos` (`proprio_ideia_id` once it has
an idea) and run the L0 checklist against it; report the gaps. A repo that never had a launch can enter the funnel as
an idea only with a demand signal (4.2) and the owner's "aprovo a construção da ideia#N" (the build is the polish
for launch); otherwise it is only watched (snapshots, no hypotheses). A repo public before its launch carries its
own pace: set `repos.publico_em` to the day it went public (its creation day when it was always public), and
backfill `estrelas_diarias` for the 28 days before the cycle's first launch (the database refuses a
decision without them) and every window is judged net of that pace (`baseline_janela`).

---

## 14. Known limits

- Reddit, X, Bluesky and Product Hunt reach and conversion are unmeasured (blocked or closed APIs); subreddit rules
  must be read by the owner logged in.
- The Trending algorithm is not published; its thresholds come from a single snapshot until the routine accumulates
  2–4 weeks of daily ones.
- The demand rule and the "niche taken" test rest on few cases (yq, snapdom, claude-agent-acp succeeded; thefuck's
  98k stars produced no relevant successor): heuristics, recalibrated with own data.
- README evidence is correlational; the conversion premise has one public anchor.
- Search API counts include fake-starred and malware repos not yet removed; the organic base rates are lower.
- Heuristic guards: the AI-hook word list (English and Portuguese), the niche search (the database checks that a
  competitor was linked, not that the search was done well), `janela1_abaixo` and the advocate's judgment of labels
  are set by the agent; the threat model covers them, the database does not.
- `lib.e7_esperado` keeps the E7-by-points table in code; re-measuring `estrelas_7d_mediana_hn_*` needs a code
  change. Sample medians and fixed-window benchmarks do not expire (only counts are re-measured, 12).
