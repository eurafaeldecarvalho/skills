---
name: apps-ideas-routine
description: >-
  A daily autonomous routine that finds, validates and only then proposes building small paid apps
  (web SaaS, browser extensions, marketplace add-ons, iOS/Android) for a solo developer who builds with AI.
  Use it when setting up or running a recurring "find me an app idea worth building" agent (Grok Bot,
  Claude scheduled tasks or any agent with a persistent filesystem, terminal and web access), when the
  owner asks why an idea was killed/archived, or when calibrating the funnel. It starts from who already
  pays (not from viral trends), keeps all state in SQLite with database-enforced guards, validates without
  talking to users (public data → fake-door landing → paid test → real checkout → paywalled MVP), and every
  number carries a source. It replaces ad-hoc idea brainstorming; for a one-off go/no-go on a single game or
  app concept use `concept-gate` instead.
---

# App ideas routine (search → validation → build proposal)

A daily routine for an autonomous agent. It looks for app ideas where **someone already pays and complains**,
validates each one with real, cheap tests, and only proposes construction after real payments. Everything
it decides is stored in SQLite and guarded by triggers, so the agent cannot "talk an idea through" the funnel.

## How to use this skill

1. **Copy the folder** to the agent's persistent workspace. The text below assumes `/workspace/rotina-apps/`
   (the Grok Bot persistent folder); change `dir_base` in `seed_config.csv` if yours differs.
2. **Schedule two runs** in the owner's timezone: (A) daily at 08:00 and (B) Friday at 18:00 (section 3).
3. **First run = bootstrap** (section 3.1): it runs `seed.py`, tests every data source live and sends the owner a
   list of prerequisites (Cloudflare Pages token, PostHog key, Search Console service account, tax rate,
   `contatos_dono`, platform fees).
4. **Adapt the owner profile** in `seed_config.csv` before the first run: goal (`meta_mrr_*`), budget
   (`teto_gasto_*`), hours per week, forbidden domains (`dominios_proibidos`), markets. The defaults are those of the
   original owner (a Brazilian solo dev, BR + English markets, US$300–1,000/month in 6 months, R$500 per idea).
5. **Run the tests** whenever the folder changes: `python3 -m unittest test_lib`.

**Language.** Rules, tables and code are in English; **identifiers stay in Portuguese** (tables, columns, state
values such as `candidata`, `morta`, `pre_teste`) because the database, queries and tests depend on them. Owner-facing
messages and the literal phrases the agent matches (e.g. "construo sem teste de demanda") are in Brazilian
Portuguese; translate both the messages and those phrases together if your owner speaks another language.

**Files in this folder**

| File | What it is |
|---|---|
| `SKILL.md` | The routine (this file): mission, gate, funnel, thresholds, state machine, outputs |
| `schema.sql` | SQLite schema with the guards (portfolio, family/graveyard, reopening, owner proof, price lock) |
| `queries.sql` | Ready-made queries for every recurring decision |
| `lib.py` / `test_lib.py` | Deterministic math (Wilson interval, decision, net revenue, sample size, owner proof) + tests |
| `seed.py` + `seed_*.csv` | Bootstrap and seeds: config/assumptions, 66 sourced benchmarks, thresholds, 27 data sources |
| `CHANGELOG.md` | Version history, assumptions without a source, known open points |

**Honest limits.** No funnel is free of errors in both directions. Ideas that win on craft, design or editorial
featuring are not detectable without talking to users and will die here (section 14). Benchmarks were verified
on 2026-10-26 and are re-checked by the routine every ~55 days.

---

## 0. Files, persistence and owner input (before anything else)

- **Base folder:** `/workspace/rotina-apps/`. The owner copies the files there once. Only `/workspace` is persistent. Installed packages may disappear in an update.
- **Start of every run, in this order:**
  1. `cd /workspace/rotina-apps`.
  2. Check that `python3`, the `sqlite3` module, `node` and `google-play-scraper` exist. Reinstall whatever is missing.
  3. Run `python3 -m unittest test_lib`. If it fails, **stop** and warn in the chat.
  4. **If `.bootstrap_feito` does not exist:** run the bootstrap (3.1) and create `.bootstrap_feito` when done. If `rotina.db` already exists without `.bootstrap_feito` (interrupted bootstrap): with `PRAGMA user_version`=11 and `config` not empty, skip `seed.py` and resume from step 2 of 3.1; otherwise, create `backups/` if missing and rename it to `backups/rotina-bootstrap-falho-AAAAMMDDHHMM.db` and run `seed.py`.
  5. **If `.bootstrap_feito` exists:** open `rotina.db` and run `PRAGMA foreign_keys=ON` (applies **per connection**, repeat it on every new connection). `PRAGMA integrity_check` must return `ok` and `PRAGMA user_version` must return 11.
     - Database missing or corrupted: restore the most recent backup from `backups/`.
     - No backup: **abort** and send "BANCO INACESSÍVEL" ("DATABASE INACCESSIBLE"). Never recreate the database on your own.
  6. **Read the owner input** (section 0.1).
- **End of every run:** `python3 -c "import sqlite3;sqlite3.connect('rotina.db').execute(\"VACUUM INTO 'backups/rotina-AAAA-MM-DD-HHMM.db'\")"` (with the time, because Friday has 2 runs). Keep the 14 most recent.
- **Seeds:** only via `seed.py`. Typing a benchmark, threshold, source or config by hand is forbidden. Config with `origem='dono'` only changes through a message from the owner.
- **Reading config:** `valor` is text. Convert it with `float()` or `int()` before calculating.
- **Secrets:** they live in `secrets/`, never go into messages and stay out of backups.

### 0.1 Owner input

The owner writes in two ways: replying in the Grok Bot chat or in a file in `inbox/`.

1. **Save before processing.** At the start of the run, save **literally** every owner message later than the last message already saved in `inbox/` (or in `inbox/lido/`) to `inbox/AAAA-MM-DD-HHMM-chat.md`, with date and time.
2. **Record each item** with `ator='dono'` and `prova_dono` = literal quote in quotation marks, with date and time.
3. **Move** the processed files to `inbox/lido/`.
4. **Check in the checklist:** every `prova_dono` recorded in the run must exist literally in a file of `inbox/lido/` **moved in this run** and the **quote** must contain `ideia#<id>` (or the topic, for expenses and hours). Every pending item asks the owner for an answer in a full sentence citing the idea (e.g.: "aprovo a construção da ideia#12" ("I approve building ideia#12")); a short answer ("sim" ("yes"), "aprovo" ("I approve")) does not count as proof: ask again. Check with `lib.prova_existe(prova, textos_desta_rodada, ideia_id)` (without `ideia_id` only for expenses and hours).

**Input types:**
- build approval;
- publication and active billing of an app (including a native paid plan active on the M1 listing);
- expenses (including platform ones);
- hours of the week;
- keyword popularity or volume;
- income tax (IR) rate and Play withholding;
- payments and refunds statement of E3;
- installs, trials and paid read in the store console (when PostHog does not cover it);
- excerpts from closed groups (source `dono_campo`);
- `contatos_dono`: emails and domains of the owner and acquaintances (to exclude from `pay_count`), recorded as a JSON list in `config.contatos_dono` with `origem='dono'` (the seed brings `[]` with `origem='seed'`, which means **not informed**);
- "construo sem teste de demanda" ("I'll build without a demand test");
- reopening of a dead idea.

Never invent, summarize or paraphrase an owner input.

---

## 1. Mission and limits

You find and **validate** app ideas for a solo Brazilian dev who builds with AI. You only propose building after real tests.

- **App:** web (SaaS, PWA, extension, marketplace add-on) or mobile (iOS/Android).
- **Goal:** US$300 to 1,000/month of net revenue in `meta_meses` months, summing the portfolio.
- **Owner's time:** 8 to 10 h/week.
- **Markets:** `BR`; `EN` (US, GB, CA, AU, IE, NZ, billing in USD); `global_outros`. Decided per idea.
- **Validation without talking to users.**
- **Test budget:** R$0 until E0; afterwards, `teto_gasto_ideia_brl` per idea and `teto_gasto_mes_brl` per month. **Platform costs** stay outside this cap, each one approved by the owner.
- **Forbidden domains:** real estate, vehicles and classifieds.
- **Portfolio (the database enforces it):** up to 4 `pre_teste`, 2 `em_teste` and 1 `em_construcao`, with at most 1 slot per family. These limits are fixed in the database; `max_*` in config only documents.

**You do on your own:** collection, analysis, filtering, scoring, copy, publishing landing pages on Cloudflare Pages, reading metrics, writing to the database and sending messages.

**Only the owner does:** spending and charging, publishing in a store, posting in a community, providing keyword volume, approving a build and changing this prompt. You prepare everything and list it as a **numbered pending item**.

---

## 2. Principles

1. **Whoever pays comes first.** A free and good competitor kills the idea. The exception is the exploration quota (5.1).
2. **Start from the median.** Project above P75 only with data measured in your own tests.
3. **Mechanical provenance.**
   - Every number in a sheet, digest or message carries a mark: `[sinal#id]`, `[bench:metrica/segmento]`, `[config:chave]` or `[metrica exp#id data]`. Without a mark, `checklist_ok=0`.
   - A signal only counts with HTTP 200 **in this run** and a `trecho_literal` of at least 40 characters. The exception is `dono_campo`.
   - Recording a signal, URL or number from prior knowledge is forbidden.
4. **Number, not adjective.** Every sheet ends with **"O motivo mais forte pra não fazer"** ("The strongest reason not to do it").
5. **Building is cheap, so copying is too.**
6. **Synthetic evidence is worth zero.**
7. **A source without data is not zero demand.**
8. **Calculations only through `lib.py`.** Call with positional arguments, in the signature's order.
9. **Also record what is against.** Every signal read about the idea goes to `evidencias` with polarity +1 or −1.

---

## 3. Schedules and order of runs

Configure in Grok Bot (Settings → Bot → Timezone = `America/Sao_Paulo`) two routines:

- **(A) daily, 08:00:** runs section 3.2. On **Sunday**, it then also runs 12.1; on the **1st Sunday of the month**, also 15. Always record `runs.tipo='diaria'`. The Sunday work goes in `resumo_json`.
- **(B) Friday, 18:00:** section 12.2, with `runs.tipo='sexta'`.

**`runs` rules:**
- Open each run with `status='rodando'` and close with `ok`, `parcial` (some fixed task failed) or `falhou`.
- A run that has been `rodando` for more than 3 h becomes `falhou`.
- The bootstrap records `tipo='bootstrap'`.
- If the bootstrap was more than 7 days ago and the last `sexta` too, the next (A) generates the overdue weekly summary.
- Grok Bot keeps only 20 executions and **does not retry** the ones that failed. If yesterday's failed, say so today.

### 3.1 Bootstrap (only without `.bootstrap_feito`)

1. `python3 seed.py rotina.db`. Every connection opened afterwards runs `PRAGMA foreign_keys=ON`.
2. **Exchange rate:** PTAX selling rate of the **last business day before today** (source `ptax_bcb`; today's only comes out after 13 h). Record:
   ```sql
   INSERT OR REPLACE INTO config(chave,valor,origem) VALUES('cambio_usd_brl',?,'medido');
   INSERT OR REPLACE INTO config(chave,valor,origem) VALUES('cambio_data',?,'medido');
   ```
3. **Sources:**
   - test each source with 1 request and record the status;
   - read the terms of `github_issues` and record them in `termos_nota` (if they forbid collection, `desligada`);
   - a source that failed stays `degradada`.
4. **Keywords:** seed only with collected data. Use the categories of the top-paid/top-grossing US and BR and the titles with "alternative to", "looking for a tool" or "ferramenta para" ("tool for") from the last 30 days (HN and Stack Exchange). Popularity stays NULL.
5. The bootstrap does **not** do E0 or a sheet.
6. Send in the chat "bootstrap: N fontes ok, N sinais, N keywords" ("bootstrap: N sources ok, N signals, N keywords") and the list of prerequisites (11.3).

### 3.2 Daily run

1. **Context:** `q_portfolio_vagas`, `q_hipoteses_abertas`, the last 7 `runs`, the last note of `CHANGELOG.md` and the owner input (0.1).
2. **Fixed tasks (100%), in this order:**
   - **`planejado` experiments already published first** (milestone, table below). When it becomes `rodando`, record the metrics of each day since `inicio`.
   - **Orphans:** `q_experimentos_orfaos` → close the open hypotheses as `inconclusiva_amostra_parcial` (aprendizado='ideia saiu da etapa' ("idea left the stage")) and `estado='encerrado'`, **without** applying a destination (closing is not aborting).
   - **Competitor snapshot** (`rank_lista=''`), for every competitor linked to an idea that is neither `morta` nor `arquivada`. Frequency: **daily** for `appstore`, `play` and `wordpress` when the idea is at `pre_teste` or beyond (in EN, daily only US and GB; other countries on Sunday); **weekly** (Sunday) for candidates and for the other stores. **A competitor registered today is snapshotted right away.** Late snapshot (Sunday run failed) → take it today.
   - **Yesterday's metrics** (full UTC day) of every `rodando` experiment. A day without events records `valor=0`. Search Console may lag: reread the last `search_console_releitura_dias` days with `INSERT OR REPLACE`.
  - **Milestone of the `planejado` ones:** read only the milestone metric. On the 1st occurrence: `estado='rodando'`, `inicio` = its date.

    | `marco_inicio` | Signal that it occurred |
    |---|---|
    | `landing_no_ar` | 1st `pageview` |
    | `anuncio_aprovado` | 1st `custo_brl` > 0 |
    | `primeiro_pageview_preco` | 1st `pageview_preco` |
    | `listing_aprovado` | approval informed by the owner or 1st `install` |
    | `paginas_publicadas` | 1st `impressoes` > 0 |
    | `publicado_na_loja` | owner event `em_construcao→lancada` |
    | `mvp_lancado` | owner event `em_construcao→lancada` (tracks W, WSEO, M) |
    | `cobranca_ativa` | the owner informs that the native paid plan (Shopify/Atlassian) is active on the listing |
    | E4 of track L | `fim` of the passed L1 experiment (E4 starts when L1 ends) |
  - **`q_planejados_vencidos`** (except L1 and E4; limit `planejado_max_dias`, M1 `planejado_max_dias_m1`, WSEO `planejado_max_dias_wseo`): → close the hypotheses as `inconclusiva_amostra_parcial` and move the idea to `arquivada` with `reabrir_se`='dono executou a pendência N' ("owner carried out pending item N").
  - **`q_experimentos_a_fechar`:** close (7.3, "When deciding").
  - **`q_pre_teste_parado`:** track L with no open experiment for more than `pre_teste_l_espera_dias` **with the build slot free**, counted from the last release of the slot (or from the end of E1, whichever is more recent) → `arquivada` (`reabrir_se`='vaga de construção livre e aprovação do dono' ("build slot free and owner approval")); W waiting for universe ((f) NULL) or WSEO waiting for universe or volume (`nao_medido`) for more than `pre_teste_dado_espera_dias` → `arquivada` (`reabrir_se`='dono informou universo/volume' ("owner informed universe/volume")). With `q_l_aguardando_dono` ≥ `max_l_aguardando_dono`, no L candidate enters `pre_teste`. Approved W and WSEO ideas wait for an `em_teste` slot in `pre_teste` (queue by score), with no deadline.
  - **`q_validada_parada`:** `validada` **with build slot free** and without an owner decision for more than `validada_max_dias`, counted from entry into `validada` or from the last release of the slot (whichever is more recent) → `arquivada` with `reabrir_se`='dono aprovou a proposta' ("owner approved the proposal").
  - **`q_construcao_longa`:** build above `mvp_horas_max` hours or 8 weeks → pending item to the owner (cut scope, continue or freeze).
  - **`q_congeladas_vencidas`:** `reativar` (only seasonal frozen before building, 1 time per idea) → `congelada→candidata` with `data_reativacao=NULL` in the same UPDATE (and `exploracao_em` of today, if it is exploration); `arquivar` → `congelada→arquivada` with `reabrir_se`.
   - `receita_snapshots` of the `lancada` ideas.
   - Decision of each open hypothesis (7.3).
   - PTAX of the last previous business day.
3. **Signal collection** (4).
4. **Triage:**
   - group the signals into ideas and record `evidencias`;
   - when creating the idea, record `pagador`, `formato`, `mercado` and `paises_alvo` (EN = `paises_en`); the family is assigned at the start of the gate (section 5);
   - **sinal → candidata** when `q_fontes_distintas_por_ideia` gives `plataformas` ≥ 3, `plataformas_de_dor` ≥ 2 and `sinais_pagador` ≥ 1. `dono_campo` and `web` count as at most 1 platform each. **Exception:** BR market, format `saas`/`pwa` and no competitor with an app in the stores → `plataformas` ≥ 2 and `plataformas_de_dor` ≥ 2 suffice, and `web` can count up to 2 platforms if they are 2 distinct domains.
   - **Competitors:** every paid product cited in a signal goes to `concorrentes` (once per `loja`+`id_loja`), is linked to the idea in `ideia_concorrentes` and gets its 1st snapshot in `concorrente_snapshots` right away. An idea in a family with a severe death does not enter testing without a reopening by the owner (the database enforces it).
5. **Gate (5) and E0 (6)** on the new candidates. At most **2 complete sheets per day**.
6. **Checklist** (11.2), backup and summary (11.1).

---

## 4. Signal collection

### 4.1 Sources

Use only the `fontes` table (from `seed_fontes.csv`, endpoints tested on 10/26/2026). Different endpoints of the same `plataforma` count as one.

**Forbidden:**
- X API;
- Reddit without OAuth (the Data API terms forbid automated collection);
- Product Hunt for commercial use;
- scraping G2 and Capterra;
- `pytrends`.

**How to collect:**
- **Language:** queries in English for EN and in Portuguese for BR. Record the `idioma`.
- **`dono_campo`:** up to 10 excerpts per week pasted by the owner. It carries `url_status=0` and a literal excerpt of at least 40 characters. It never replaces E3.
- **Recording:** use `INSERT OR IGNORE`. The signal is **new** if the insert recorded 1 row.

**Failures:**

| Situation | What to do |
|---|---|
| 5xx or timeout | 3 attempts, waiting 2 s, 8 s and 30 s |
| 429 or 403 | stop the source until the next run |
| 3 consecutive failures or key field missing | `quebrada`, warn the owner |
| `degradada` source responds 200 | back to `ok` |
| App Store reviews return 400 on page 11 | end of feed, not a failure |
| Chrome Web Store | use `curl -L` |

### 4.2 Signal types (value of `sinais.tipo`)

| Finding | `tipo` |
|---|---|
| 1-to-3-star review, unresolved support topic, "is there a tool", "alternative to", "ferramenta para" | `dor` |
| Unanswered feature request | `pedido` |
| Paid product with traction (competitor registration) | `concorrente` |
| Public price, paid plan, price increase | `preco` |
| Shutdown, price increase above 30%, end of free plan (60-day window; also triggers `q_reabrir_candidatas`) | `orfao` |
| Platform feature that became stable, or monetization release | `plataforma` |
| New regulation with a deadline and a small audience | `regulacao` |
| Keyword with weak supply: top 10 with median below 1,000 reviews, ≥ 2 abandoned apps and ≥ 1 paid. **Never counts toward candidate.** | `keyword_fraca` |
| TrustMRR and any third-party revenue. **Hypothesis only; never counts toward candidate.** | `outro` |

Trends and headlines only amplify.

### 4.3 Choosing the day's sources and stopping

- **Choice:** before collecting, choose the day's sources. 70% come by yield (`q_rendimento_fontes`) and 30% by rotation; in the first 4 weeks, equal rotation. The condition is Σ `cota_min` ≤ `trava_buscas` − searches of the fixed tasks.
- **Search:** each HTTP request counts 1.
- **Signal hash:** `sha256(fonte|id_externo)`. Without an external id: `sha256(fonte|url normalizada|200 primeiros caracteres normalizados)`.
- **Stop:** when the chosen sources meet the quota **and** `saturacao_consultas_sem_novidade` consecutive queries bring no new signal → `motivo_parada='saturou'`.
- **Caps:** when hitting `trava_minutos` or `trava_buscas`, stop with `motivo_parada='teto_tempo'` or `'teto_buscas'`. If the stop is due to an error, use `'erro'`.
- **Adjustment:** if `q_runs_trava` > 3, propose an adjustment in the CHANGELOG.

### 4.4 Control columns

| Column | How to fill |
|---|---|
| `fontes.cursor` | highest `created_at_i`, review id or date already collected; update it in the same transaction as the inserts |
| `fontes.falhas_seguidas` / `ultimo_ok_em` | +1 on each failure, resets and records `datetime('now')` on each 200 |
| `runs.taxa_novidade` | `sinais_novos / buscas` (NULL if searches=0) |
| `keywords.intencao` | `transacional` (buy, price), `ferramenta` (generator, converter, calculator, template) or `informacional` |
| `keywords.tem_ai_overview` | 1 if the target country's results page shows an AI summary |
| `concorrente_snapshots.pais` | country code; `global` for a store without a country (web, Notion, Figma, Slack, Workspace, TrustMRR) |
| `ideias.n1000` / `universo_fonte` | `lib.n_clientes([config:meta_mrr_max_usd], liquido)` / URL of the universe source |
| `experimentos.paises_trafego` | allowed countries of origin (= `paises_alvo`) |
| `horas.tipo` | `validacao` (E0 to E3), `construcao` (`em_construcao`), `manutencao` (`lancada`) |
| `ideias.atualizada_em` | only changes in the state-transition UPDATE (10.1); never in other UPDATEs (the deadlines depend on it) |
| competitor removed from the store | record the day's snapshot with NULL values and an `orfao` signal |
| the idea's position on the keyword (L1, top 30) | `concorrente_snapshots` of the app itself with `rank_lista='kw:<keyword_id>'` and `rank_pos` |
| `concorrente_snapshots.rank_lista` | `''` for the competitor snapshot; `top-free`, `top-paid` or `top-grossing-<genero>` for ranking position |
| `gastos.categoria` | `anuncio` (with `experimento_id` and `ideia_id`), `plataforma` (without `ideia_id`), `dominio`, `ferramenta`, `outro` |
| `keyword_snapshots.fonte_popularidade` | `apple_ads_popularidade` or `keyword_planner` (always informed by the owner) |
| `receita_snapshots.fonte` | `gateway_api`, `loja` or `dono_extrato` |
| `concorrente_snapshots.ratings_count` / `users` / `installs_min` / `installs_max` / `rating_avg` / `preco` / `tem_iap` / `versao_data` | whatever the store returns |
| `receita_snapshots.mrr_liquido_usd` / `pagantes` / `trials` / `installs` | from the gateway, the store or the owner's statement |
| other columns | fill them whenever the source returns the data; NULL only when there is no data |

Fixed rule numbers written in the text (e.g.: rating 4.2, 1,000 reviews, 24 months) are design assumptions: they only change through the CHANGELOG.

---

## 5. Elimination gate

**Family first:** before applying the cuts, with `pagador`, `evidencias` and `ideia_concorrentes` already recorded, assign the family (one idea at a time): run `q_familia_sugerida`; if any row has 2 or more columns = 1, inherit the `familia_id` of the one with the most columns (tie → lowest `familia_id`; the database requires exactly that one); otherwise, `familia_id` = the idea's own `id`. Record the chosen row in the `evidencia_ids` of the next event. Once recorded, family and payer do not change (the database enforces it).

**Death:** whoever hits a cut goes to `morta`, with `motivo_morte` and `reabrir_se` (10.2).

**FIX-FIRST:** exception, 1 time per family (`q_fix_first_familia` = 0). The idea stays `candidata`: record only one event `de='candidata', para='candidata', motivo='FIX-FIRST: <smallest fix>'`, without UPDATE. If the cut persists in the next run, `morta`.

1. **Forbidden domain** → `excluida_por_regra`.
2. **No payer:** no competitor charges (price > 0, IAP or paid plan) → `sem_pagador`. The exception is the exploration quota (5.1).
3. **Free and good incumbent** → `incumbente_gratis`.
   - "Good" = rating ≥ 4.2 with ≥ 1,000 reviews, or ≥ 100,000 users.
   - **Exception:** ≥ 3 signals, from ≥ 2 platforms, showing that a **named segment** rejects the free one. In that case, the audience becomes only that segment.
4. **AI commodity:**
   - The 5 core tasks come from ≥ 3 `dor` signals (cite the `sinal#`).
   - Execute each task in a subtask without tools, with 1 prompt.
   - A **second subtask** receives only the tasks and the outputs and scores which ones were usable without editing. If there is no subtask, do each step in a separate file in `adv/`.
   - `cobertura_llm` = usable ÷ 5. With ≥ 0.7: `risco_absorcao='alto'` → `commodity_ia`.
   - A generic LLM wrapper is rejected outright.
5. **No channel** → `sem_canal`. Valid:
   - marketplace with internal search (Shopify, Chrome Web Store, Google Workspace, WordPress, Atlassian, Notion, Figma, Slack);
   - app store keyword that meets E0 (a) **and** has ≥ 3 of the top 10 with fewer than 1,000 reviews or without an update for 12 months or more;
   - Google search with transactional or tool intent (track WSEO);
   - **(track W) testable channel:** named community (name, URL, public size, self-promotion rule read) or Meta BR with `n_atingivel` ≥ `n_min` of E2E3.

   **Keywords:** before looking at the top 10, record the main term (`principal=1`) and up to 3 synonyms. Every term tested stays recorded with `cumpre_criterio`. The criterion holds if the main term **and** at least 2 synonyms meet it.

   **AI summary:** if the target country's results page has an AI summary, multiply the expected volume by `[bench:ctr_link_com_ai_overview/google_eua]` ÷ `[bench:ctr_link_sem_ai_overview/google_eua]`.
6. **Free or ad-only consumer** → `excluida_por_regra`. Every MVP is born with a paywall or trial. In the exploration quota a free plan may exist, but E3 tests the paid plan.
7. **The math doesn't close:**
   - `n300_bruto = ceil(n300 × (1 + churn_mensal × churn_meses_reposicao))`;
   - `visitas_mes = n300_bruto / (conv × fator × meta_meses)`, where:
     - `conv` on web = `conv_visita_paga_web`;
     - `conv` on mobile = `[bench:download_to_paid/ios]` or `[bench:download_to_paid/android]`, according to the idea's platform;
     - `fator` = `fator_conversao_br` if the market is BR; otherwise, 1.
   - Using `conversao_landing_mediana` is forbidden (it measures clicks, not payment).
   - **Channel volume**, recorded in `volume_status`:

     | Channel | Comparison with `visitas_mes` | `volume_status` |
     |---|---|---|
     | Keyword with volume in searches/month **informed by the owner** | compare: if the volume does not deliver `visitas_mes` → `mercado_pequeno` | `medido` |
     | E0 (a) proxy, Apple popularity, marketplace, track W (budget or community) | **do not compare** (it is not visits/month); the test is what proves it, and E0 (f) applies | `proxy` |
     | No measurement | — | `nao_medido` |

     With `nao_medido`, the idea does not die, but paid stage, `em_teste` and `em_construcao` are blocked on tracks WSEO and L until the owner informs the volume.
8. **Graveyard:** search for who tried and shut down, and why. If the reason applies and there is no concrete difference → `concorrencia_saturada` or `custo_alto`.
9. **Revenue via apps inside ChatGPT** → reject. There only physical goods sell well.
10. **Ban risk:** a core that depends on scraping or automating a service whose terms forbid it, or on a vendor that, in the last 24 months, **raised the price ≥ 30%, removed the endpoint/permission used or started forbidding that use** → `risco_banimento`, quoting the excerpt.
11. **Third-party dependency:** without 2 dated versions showing price and terms stable for ≥ 24 months **and** without an alternative: `risco_dependencia='alto'` and −3 on the Execution score.

### 5.1 Exploration quota (new category, no competitor that charges)

- **Limit:** `exploracao_por_mes` per month and 1 active at a time (`q_exploracao_mes`).
- **Conditions:**
  - ≥ 3 pain or request signals, from ≥ 2 platforms, showing that the user **already spends** on a substitute (spreadsheet, script, freelancer, hourly service, adapted product);
  - cuts 1, 3, 4, 5, 7, 8, 9, 10 and 11 clean (only 2 and 6 have an exception).
- **Exploration E0:**
  - (b) becomes (b'): ≥ 3 distinct paid substitutes with a cited public price;
  - (c) becomes (c'): ≥ 1 substitute with the weakness of (c);
  - in the proxy of (a), replace "≥ 3 paid" with "≥ 3 results containing the keyword".
  - Passes with ≥ 3 of (a), (b'), (c') and (d), plus (f), economics and score.
- **Path:** set `exploracao=1` and `exploracao_em=date('now')` in the same UPDATE (the database refuses if there is already 1 active or 1 in the month). Goes straight to E3 (EN and `global_outros`) or to E2E3 (BR), with the same thresholds. Payer score = 4, with a minimum of 4. Never goes to `em_construcao` without E3 (or E2E3, in BR) passed.

---

## 6. E0 — Desk (R$0, up to 3 days, routine only)

Evaluate in the target country (EN = sum of US, GB, CA and AU).

- **(a) Measurable channel:** volume ≥ 1,000/month or Apple popularity ≥ 20 **informed by the owner**; or proxy (search top 10 with ≥ 3 results containing the keyword, `top10_ratings_mediana` < 5,000 and ≥ 3 paid; in the Chrome Web Store, "paid" = public paid plan on the listing or the site). On **track W**, (a) also holds with the testable channel of cut 5. Never estimate volume.
- **(b)** ≥ 3 competitors charging.
- **(c) Incumbent with traction and weakness.**
  - **Weakness:** rating ≤ 3.8; or no update for ≥ 12 months **and** no sign of life in the last 90 days (review reply, changelog, post, commit, price change; record in `concorrentes.ultimo_sinal_de_vida`); or price increase ≥ 30%.
  - **The weakness does not count** if, in the last 90 days, the incumbent published a post, changelog, roadmap or commit that addresses pain (d). In that case the idea goes to `arquivada` (`reabrir_se`='2 sinais de dor posteriores à entrega do incumbente' ("2 pain signals later than the incumbent's delivery")).
  - **Traction:** iOS/Play ≥ 500 reviews; Chrome Web Store ≥ 1,000 users; Shopify/WordPress ≥ 50 reviews or ≥ 1,000 installs; web SaaS ≥ 3 competitors with public price.
- **(d) Repeated pain:**
  - iOS/Play: ≥ 30 reviews of 1 to 3 stars, same pain ≥ 5 times;
  - Chrome/Shopify/WordPress: ≥ 10 reviews, same pain ≥ 3 times;
  - web SaaS: ≥ 5 independent mentions.
- **(e) Trend:** Google Trends read manually. Does not count.
- **(f) Universe:** potential payers with a cited public source. If `n300 > pct_max_penetracao × universo` → `mercado_pequeno`. Without a source: NULL and pending item. **(f) NULL does not block E1, but blocks `em_teste`, `validada` and `em_construcao`.**

**E0 result:**
- **Passes:** ≥ 3 of (a)–(d), (f) did not fail, economics (9) closes and the score (8) reaches the minimums.
- **Failed, with ≥ 3 evaluable criteria:** `arquivada`, with `reabrir_se` = the criterion that was missing.
- **Fewer than 3 evaluable:** stays `candidata` with a pending item. After `candidata_pendente_dias` since `atualizada_em` → `arquivada`, with `reabrir_se`.

Competitor traction: use `q_tracao_concorrente.delta_30d`.

---

## 7. Tracks and test funnel

**Track by format and channel** (not a free choice):

| Format and channel | Track |
|---|---|
| iOS/Android | **L** |
| Extension or add-on with marketplace channel | **M** |
| Web with transactional search channel in EN | **WSEO** |
| The rest of web | **W** |

### 7.1 Reachable sample (before pre-registering a paid stage)

- `n_atingivel_pv = lib.n_atingivel(orc_e2e3_brl − reserva_criativo_brl, cambio_usd_brl, CPC, pv_por_clique)`.
- **Budget per stage** (`hipoteses.orcamento_max_brl`): E2E3 = `orc_e2e3_brl`; E3 BR = `orc_e3_complemento_brl`; L1 = `orc_apple_ads_l1_brl`; EN creative = `orc_criativo_en_brl`; others = 0. The cap by `n_atingivel_pv` applies **only to E2E3**; E3 (organic + complement) uses the threshold's `n_min`.
- **Before pre-registering E2E3 or E3:**
  - if `config.contatos_dono` still has `origem='seed'`, **pre-register the hypotheses normally** and leave the experiment `planejado` without publishing the billing link; it becomes a pending item ("informe `contatos_dono`, pode ser `[]`" ("provide contatos_dono, it can be []")). `q_planejados_vencidos` archives it on the deadline with `reabrir_se`='dono informou contatos_dono' ("owner provided contatos_dono");
  - in BR, ask the owner which gateway and whether they will open a CNPJ before the 1st charge (the Stripe account under CPF does not become CNPJ).
  - **Unit:** pageviews.
  - **CPC:** `[bench:cpc_meta_mediana/BR]` until measured. In the first 48 h, recalculate with the observed CPC and the observed pageview÷click.
- Pre-registered `n_min` (E2E3 only) = min(threshold's `n_min`, `n_atingivel_pv`). Record the calculation in the sheet with the day's exchange rate.
- **EN:** the Meta US CPC `[bench:cpc_meta_mediana/US]` and the Apple Ads CPI `[bench:apple_ads_cpi_mediana/US]` do not close a sample with this budget. EN validates through tracks M, L, WSEO, or W with organic traffic. Paid in EN only to test creative (up to `orc_criativo_en_brl`), and it **never** counts as evidence.
- Traffic from IN, PH, NG, PK and BD never counts. Filter by `$geoip_country_code`.

### 7.2 Stages

| Stage | Track / state | Experiment (`tipo`) | How | Criterion |
|---|---|---|---|---|
| **E1 Landing + fake door** | W and L; `pre_teste` | `landing` | Landing with the **list price**; the "Assinar" ("Subscribe") button leads to "em breve, deixe seu e-mail" ("coming soon, leave your email"). Traffic from up to 2 named communities, **posted by the owner** with ready-made text and `utm_source`. Friends and the owner's own email do not count. | `cta_click_rate` **and** `email_per_click` |
| **E2E3 Ad → checkout** | W BR (the only paid test in BR); `em_teste` | `checkout` (a single experiment; `custo_brl` recorded on it) | Meta BR straight to the page with real checkout. CTR < `ctr_criativo_min_meta` = creative problem: swap it 1 time (`reserva_criativo_brl`). | `pay_count` BR (2 payments, owner's decision). With `pay_count` confirmed and **CAC_brl > `cac_max_multiplo_liquido` × `liquido_cliente_usd` × `cambio_usd_brl`** → `experimentos.decisao='refutada_cac'` (the hypothesis stays confirmed), idea `morta` (`custo_alto`). `mata` or `sem_amostra` in E2E3 → `arquivada` (the budget does not refute: passing requires ~1.3% conversion with n=150; only 0 payments with n ≥ n_min is `refutada`). |
| **E3 Real checkout / pre-sale** | W EN/global (organic), M after M1, WSEO after WSEO, EN exploration; `em_teste`. Native billing (Shopify/Atlassian): segment `nativo`, `n` = listing installs, milestone `cobranca_ativa` | `checkout` | Billing link created by the owner. Founder price ≥ 80% of the list price; record `preco_testado`. **Estimated** delivery within 75 days (or 30 days after the build approval), with full refund until delivery; state this on the page. Paid complement only in BR (`orc_e3_complemento_brl`). | `pay_count` |
| **M1 Minimal listing** | M; `em_teste` | `listing` | 1 function, upgrade button and pricing page, with PostHog events (11.3). Hours: ≤ `m1_horas_max` (Shopify/Atlassian ≤ `m1_horas_max_shopify_atlassian`). | `installs_7d`. Passed → E3 with native billing (Shopify/Atlassian) or Creem (Chrome Web Store/Workspace). |
| **WSEO** | WSEO; `pre_teste` | `seo` | Landing + 3 to 5 transactional pages, measured in Search Console. | `impressoes_7d` **and** `cta_click_7d`. Passed → E3. |
| **L1 1-function MVP** | L; built in `em_construcao`, measured in `lancada` (the milestone is the owner event `em_construcao→lancada`) | `paywall` | **Pre-register ONE hypothesis:** `trial_start` if the paywall has a trial, otherwise `installs_organicos`. Record the L1 experiment and hypothesis (and those of E4) **after** the owner event `→em_construcao` and before `lancada`; until then, the hypothesis stays only in the proposal sheet. **Before building:** E1 passed **or** "construo sem teste de demanda" from the owner. Value that depends on the device. Price ≥ `preco_min_l1_anual_usd`/year or ≥ `preco_min_l1_semanal_usd`/week. Hard paywall, with a 7–14-day trial. Apple Ads up to `orc_apple_ads_l1_brl`, only to measure impressions and taps (prefer CA, AU and GB). | The chosen hypothesis. Then, E4. Out of the keyword's top 30 in 30 days (position in `rank_lista='kw:<id>'`) → `morta` (`sem_canal`); this rule is separate from the L1 `mata_destino` (which is to freeze for lack of sample). |
| **E4 MVP with paywall** | all; measured in `lancada` | `paywall` | Only the flow the payers bought. | Mobile (L): `install_to_trial` + `trial_to_paid`, segment = the idea's market. Web (W, WSEO): `visit_to_trial` + `trial_to_paid`, segment `web`. Marketplace (M): `install_to_trial` (segment `marketplace`) + `trial_to_paid` (segment `web`). |
| **E5 Post-launch ladder** | all; `lancada` | — | Reads `receita_snapshots`. **Does not use `decidir`.** D30/D60/D120 count from the end of E4. | 0 payers at D30 → `congelada`; < `e5_d60_min_usd`/month at D60 → `congelada`; < `[config:e5_d120_min_usd]` with no trend at D120 → `arquivada` (step per idea; the goal `meta_mrr_min_usd` is for the summed portfolio). Before archiving or killing an idea with active payers, open a pending item for the owner to notify or cancel the subscriptions. |

**`pay_count`, how to count:**
- counts **distinct customers** (distinct email and card; of the card, only the last 4 digits); in B2B, at most `max_pagantes_por_dominio_b2b` per corporate domain;
- only with `utm_source` registered in `experimentos.utm_sources`;
- excludes `contatos_dono` (without this list informed by the owner, E3 and E2E3 do not pass) and payments from cards issued in IN, PH, NG, PK or BD when the market is EN;
- deducts refunds and chargebacks;
- source: `gateway_api` or `dono_extrato`.

**Native billing (Shopify, Atlassian):** payer = distinct store or instance (`myshopify` domain or Atlassian site); `utm_sources` = `listing_<loja>`; excludes `contatos_dono`, test charges and development stores; source `gateway_api` of the platform or `dono_extrato`.

**Sample floor to pass (E3 and E2E3):**
- **E2E3** (one Meta campaign) and **native E3** (listing): `piso_ok` = `n` ≥ `e3_n_min_fracao_para_passar` × `n_min`.
- **Other E3:** `piso_ok` = `n` ≥ `e3_n_piso_abs` **and** payers coming from ≥ 2 **distinct named channels** (name + URL in the sheet; utm variations of the same channel count as 1; a store's listing counts as 1 channel), each with ≥ 1 payer. Payers from a single channel do not validate (channel bias). Pass `piso_ok` to `lib.decidir`: without the floor, `passa` becomes `aguardar` and, with the deadline exhausted, `sem_amostra` (the stage's destination).

**`passa` in a payment count** is only recorded `dias_espera_reembolso` days after the payment that hit the threshold. Until then, the decision is `aguardar`.

**General rules:**
- Paid TikTok/UGC and creators: forbidden.
- **Android in EN:** only after iOS passes E4. On Android, download→paid is `[bench:download_to_paid/android]` versus `[bench:download_to_paid/ios]` on iOS, and a new personal Play account requires `[bench:play_testers_conta_pessoal/teste_fechado]`.
- If you captured emails, notify the list within 30 days after `→em_construcao`.
- SEO on track W is a parallel channel, never a death criterion before 90 days.
- **Seasonality:** if ≥ 60% of the searches or signals fall in one window of the year, record `janela_inicio` and `janela_fim` and schedule the test to end up to 2 weeks before. Outside the window, the idea does not die: it goes to `congelada` (from `candidata`, `pre_teste` or `em_teste`), with `data_reativacao`; it reactivates **1 time** per idea. When recording the window, register an event `de=para=<estado atual>`, `motivo='JANELA: <ini>..<fim>'`. With an experiment running, only freeze if there is a `JANELA:` event prior to the pre-registration (`MIN(hipoteses.criada_em)`); otherwise, decide first (`lib.decidir` with `prazo_esgotado=True`) and apply the destination; if it returns `estender` or `aguardar`, record `inconclusiva_amostra_parcial` and move the idea to `arquivada` with `reabrir_se`='janela sazonal registrada antes do novo teste' ("seasonal window recorded before the new test") (applies to rate and count; it is not a death). Since the state-change event must be the last one, record the `JANELA:` event and then, separately, the transition event.
- **Before `validada` and the proposal:** redo the **entire E0** with the most recent snapshots. If, in the last 90 days before the proposal, the incumbent published a changelog, post, roadmap or commit that addresses the main pain (d) → `arquivada` (`reabrir_se`='sinal# posterior mostrando a dor persistindo' ("later sinal# showing the pain persisting")) or `morta` (`concorrencia_saturada`), unless ≥ 2 `dor` signals **of the same pain (d)** (cite the original `sinal#`), from distinct authors, with `publicado_em` ≥ 14 days after the incumbent's delivery and citing in the `trecho_literal` the new version or a use after it.

### 7.3 Metrics, pre-registration and decision

**One hypothesis per criterion metric**, all linked to the same experiment (`hipoteses.experimento_id`). The stage (`q_etapa_status`):
- **passes** when all hypotheses pass;
- **is refuted** when any is refuted → apply `limiares.mata_destino` (`morta` with `teste_reprovado`, `arquivada` with `reabrir_se`, or `congelada`);
- **inconclusive** when any is inconclusive and none refuted → apply its `sem_amostra_destino`;
- **continues** if there is still an open hypothesis.

**Milestone (`experimentos.inicio`)** = `limiares.marco_inicio`: landing live, ad approved, first `pageview_preco`, listing approved by the store, pages published, app published or MVP launched. Before the milestone, the experiment stays `planejado` and the deadline does not run. The `n` in days or weeks counts from the milestone: days = `julianday(hoje) − julianday(inicio)`; weeks = `floor(dias / 7)`.

**`metricas`:** each row is the count of **one full UTC day (yesterday)**, never cumulative. The possible values:

| `metricas.metrica` | Origin (`metricas.fonte`) |
|---|---|
| `pageview` (human `$pageview`, only from `paises_alvo`), `pageview_preco`, `cta_click`, `email_submit`, `checkout_start` | `posthog` |
| `pagamento`, `reembolso` | `gateway_api` or `dono_extrato` |
| `install`, `install_pago` (with paid `utm_source`), `trial_start`, `paid`, `upgrade_click`, `ativos` | `posthog`; fallback `loja` (via inbox) |
| `impressoes`, `cliques_busca` | `search_console` |
| `custo_brl` | `anuncio_dono` (via inbox) |

**Criterion metric → calculations:**

| Criterion | events | n |
|---|---|---|
| `cta_click_rate` | cta_click | pageview |
| `email_per_click` | email_submit | cta_click |
| `pay_count` | pagamento − reembolso | pageview_preco |
| `installs_7d` | `q_installs_ultimos_7d` | weeks since the milestone |
| `impressoes_7d` | `q_janela_7d` with `metrica='impressoes'` and `fim` = today − `search_console_releitura_dias` | weeks |
| `cta_click_7d` | `q_janela_7d` with `metrica='cta_click'` (PostHog) and `fim` = yesterday | weeks |
| `installs_organicos` | install − install_pago | days |
| `trial_start` (L1) | trial_start | days |
| `install_to_trial` | trial_start | install |
| `visit_to_trial` | trial_start | pageview |
| `trial_to_paid` | paid | trial_start |
| CAC | sum of `custo_brl` ÷ `pay_count` | — |

**Pre-registration:**
- Before the test, **copy** from the current version of `limiares` (exact segment; if there is none, `*`) to `hipoteses`: metrica, tipo_criterio, limiares, n_min (with the 7.1 adjustment), eventos_min, prazo_dias and `limiar_versao`.
- Record the `previsao` **in the metric's unit**: fraction for `taxa`, count for `contagem`.
- Also `orcamento_max_brl` and the experiment with `utm_sources`.
- Changing the threshold after seeing data is forbidden. The `preco_alvo` locks after the test starts.

**If `eventos > n`** (e.g.: `paid` > `trial_start` in a paywall without trial): use `n = eventos` and register it in the `aprendizado`.

**Decision:** `lib.decidir(tipo, eventos, n, limiar_passa, limiar_mata, n_min, eventos_min, estendida, prazo_esgotado)`, with the totals from `q_metricas_experimento` and the `prazo_esgotado` from `q_hipoteses_abertas`.

| Result | What to do |
|---|---|
| `aguardar` | keep collecting |
| `estender` | `estendida=1` and `extensao_motivo='meio'`, one single time. **In E2E3**, the extension goes up to `n_atingivel` (not up to 2 × n_min): pass `prazo_esgotado = prazo_esgotado or n >= n_atingivel` and `passa_estendido=limiar_passa` (owner's decision: 2 payments). `mata` after this extension records `inconclusiva_amostra_parcial` (the budget does not refute) and the idea goes to `arquivada`. **Do not change `n_min` or `prazo_dias`**: the lib and `q_hipoteses_abertas` already double them. In E2E3, if the extension does not fit the budget → `sem_amostra`. |
| `passa` | `resultado='confirmada'` (respecting the refund wait) |
| `mata` | `resultado='refutada'`; the stage follows `limiares.mata_destino`. |
| `sem_amostra` | according to `limiares.sem_amostra_destino` (below) |

**`sem_amostra`, by destination:**

| Destination | Stages | What to do |
|---|---|---|
| `e1_inconclusiva` | E1 | sum of the experiment's `pageview` < `e1_min_visitantes_total` → `inconclusiva_sem_trafego`; otherwise → `inconclusiva_amostra_parcial`. Then: **W in BR** → E2E3; **EN/global and track L** → 1 new E1 (new experiment with another named community, owner pending item). The 2nd inconclusive → `arquivada` with `reabrir_se`='nova comunidade com tamanho público' ("new community with public size"). |
| `estender_depois_arquivada` | E3 | (also applies to `mata` after an extension for lack of sample with 1 or more payments; 0 payments with n ≥ n_min is `refutada`) extend 1 time (+`prazo_dias`), recording `estendida=1` and `extensao_motivo='sem_amostra'`; in the following decisions, if `extensao_motivo='sem_amostra'`, call `decidir(..., passa_estendido=limiar_passa)` (the extension for lack of sample does not raise the requirement); if it persists → `inconclusiva_amostra_parcial` and idea `arquivada` with `reabrir_se`='≥ n_min pageview_preco em prazo_dias' ("≥ n_min pageview_preco within prazo_dias"). Never `refutada`. |
| `arquivada` | E2E3, M1, WSEO | `inconclusiva_amostra_parcial` and idea `arquivada` with `reabrir_se` |
| `congelada` | L1, E4 | `inconclusiva_amostra_parcial`. L1, or E4 with 0 active payers → `lancada→congelada`. **E4 with ≥ 1 active payer:** the idea stays `lancada` and goes straight to E5 (a live product does not freeze for lack of sample). |

**When deciding:**
- Record `n_observado`, `eventos_observados`, `valor_observado` (in the metric's unit), `fechada_em=datetime('now')` and the `aprendizado`.
- When `q_etapa_status.abertas=0`: `UPDATE experimentos SET estado='encerrado', fim=date('now'), decisao=<resultado da etapa>`.
- **Stage decided by one hypothesis** (refuted, or destination applied): record the still-open hypotheses of the same experiment as `inconclusiva_amostra_parcial` (aprendizado='etapa decidida por outra hipótese' ("stage decided by another hypothesis")) and close the experiment. With one inconclusive and another open, the stage continues until the last one closes.
- **Cancelling a test** only through an owner message (`prova_dono`). First, record the open hypotheses as `inconclusiva_amostra_parcial`; the idea goes to `arquivada` with `reabrir_se` (E1, E2E3, E3, M1, WSEO) or to `congelada` (L1, E4), **without** extending or advancing a stage; only then `estado='abortado'` (the database refuses aborting with an open hypothesis). The same stage only runs again after a `REABERTA:` event.
- For `taxa`: `ic_inf, ic_sup = lib.wilson(eventos, n)`. For `contagem`: leave NULL.

**Signal weights:** payment 10; card on trial 5; price click 2; email 1; like or upvote 0.

---

## 8. Devil's advocate and score

### 8.1 Devil's advocate (before `em_teste`, `validada` and the proposal)

- **Where to run:** in a new subtask that receives only the sheet and the links. If there is no subtask, write in `adv/<ideia>.md` and answer in a separate section, ignoring the run's reasoning.
- **Request:** "3 motivos verificáveis para matar esta ideia, cada um com URL" ("3 verifiable reasons to kill this idea, each with a URL"). Each answer needs a signal that **contradicts the objection's premise** (being later than the sheet is not enough).
- **Record:** record the literal output.
- **Kills the idea** (`advogado_do_diabo`) only the objection that **meets a section 5 cut with evidence** and that has no answer with a `sinal#` or `bench#` collected after the sheet.
- **The other objections** become risks listed in the sheet. One of them, for example, is "copiável com IA" ("copyable with AI"), already scored in Moat.

### 8.2 Score

**Scale:** only 0, 4, 7 and 10 are valid. Record in `score_json` the anchor text and the evidence.

| Axis | 10 | 7 | 4 | 0 | Minimum |
|---|---|---|---|---|---|
| **Payer** | ≥ 3 competitors charge ≥ `pagador_ticket_alto_usd`/month, with E0 (c) traction; payment in USD | ≥ 3 charging | 1–2 charging, or paid substitute (exploration) | none | 7 (exploration: 4) |
| **Channel** | marketplace with search and top 3 with ≤ 200 reviews | measured volume proxy | named testable channel (W) | none | 7 (W: 4) |
| **Moat** | 2+ verifiable moats | 1 moat | weak moat | none | 4 |
| **Economics** | n300 ≤ `nota_economia_n300_10` | n300 ≤ `nota_economia_n300_7` | n300 ≤ `nota_economia_n300_4` | doesn't close | 7 |
| **Execution** | MVP ≤ `nota_execucao_h_10` h, no store risk, support ≤ 1 h/week for 30 payers | ≤ `mvp_horas_max` h | > `mvp_horas_max` h or review risk (app that is a website/LLM wrapper, collects sensitive data or falls under Apple guidelines 4.2/4.3/5.1) | unfeasible | 7 |

**Adjustments** (result limited to 0–10):

| Adjustment | Axis |
|---|---|
| +2 built-in channel with a buyer who already has a card (Shopify, Atlassian, App Store, Play; **not** Chrome Web Store or Workspace) | Channel |
| +1 billing done by the platform | Economics |
| −2 `cobertura_llm` ≥ 0.5 | Moat |
| −2 saturated mobile B2C | Channel |
| −2 consumer without channel | Channel |
| −1 synchronous support | Execution |
| −3 `risco_dependencia='alto'` | Execution |

A positive adjustment does not count toward reaching the minimum; a negative one does.

**Tie-break:**
1. add-on with native billing;
2. B2B or professional web in the `preco_b2b_faixa_usd`/month range;
3. iOS with paywall for EN;
4. B2C freemium.

**Competition:** bring 2 to 4 similar ones with link and traction. Without a concrete advantage, the idea dies.

---

## 9. Economics (always via `lib.py`)

**Warning (iOS):** an annual price of US$35–80 usually gives n300 above `nota_economia_n300_7` (Economics below the minimum); in a store app, the math only closes with a high weekly or monthly price.

**Annual or weekly price:** pass `preco_anual / 12` or `preco_semanal × 52 / 12` to `liquido_usd` (the lib works per month); the churn band uses this monthly ticket.

**Net per customer:** `lib.liquido_usd(preco, canal_cobranca_da_ideia, aliquota_ir, vat, moeda, cambio, cartao_internacional, retencao)`, with positional arguments.
- **`preco`:** what the customer pays, **with tax** when there is any. `vat` is the rate contained in the price.
- **Stores (App Store/Play):** in the UK, EU and AU the price includes VAT/GST and the commission applies without tax. In the US and CA, `vat=0`.
- **MoR (Creem/Dodo/Paddle):** the tax is added to the price and the fee applies to the total. The Creem fee was verified `[bench:taxa_creem/transacao]`. The fee base at Dodo is a conservative assumption.
- **Atlassian Forge:** `atlassian_forge` = 0% up to US$1M lifetime `[bench:taxa_atlassian_forge/primeiro_1M_vitalicio]`.
- **Other marketplaces without verified billing** (Chrome Web Store, Workspace, WordPress, Notion, Figma): use `creem`.
- **Currency:** `stripe_br` in BRL; Creem, Dodo and Paddle in USD (the lib refuses mixing); stores and Shopify accept BRL with the exchange rate.

**Income tax (IR) (facts verified on 10/26/2026):**
- An individual with revenue from abroad pays carnê-leão by the 2026 progressive table, from 7.5% to 27.5% (Receita Federal: gov.br/receitafederal → carnê-leão, rendimentos do exterior).
- The reduction up to R$7,350/month comes from Law 15.270/2025 (planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/L15270.htm).
- Use `[config:aliquota_ir_marginal]` (informed by the owner; the seed value is a conservative assumption).
- There is no income tax exemption for individuals for export of services.

**`retencao`:**
- **Play BR:** IRRF + CIDE when the owner receives in a currency other than the real (Play Console help answer/9384608), at the rate informed by the owner.
- **US:** `retencao_eua`. Apple requires the W-8BEN and only withholds "if it deems it due" (Apple Developer Program License Agreement, Schedule 2). Brazil has no treaty with the US (IRS "Tax treaties A to Z").

**Final calculations:**
- **Customers needed:** `lib.n_clientes([config:meta_mrr_min_usd], liquido)` and `lib.n_clientes([config:meta_mrr_max_usd], liquido)`. Net ≤ 0 → the math doesn't close.
- **Churn:** monthly ticket bands in USD: `churn_mensal_ticket_lt25` (< 25), `_25a50` (25 to 50), `_gt50` (> 50). Multiply by `churn_mult_app_ia` if the app uses AI `[bench:churn_ia_vs_nao/app_ia]`. Show the monthly replacement.
- **Price floor:** web B2C ≥ `preco_piso_web_b2c_usd`/month. The economics uses the **list price**.
- **App with LLM:** gross margin ≥ 70% at the p95 user, or a usage limit.
- **Honest probability:** `[bench:pct_chega_1k_em_2anos/app_assinatura]`. `[config:meta_mrr_min_usd]`/month sits near the P70 of monthly revenue at 12 months (log interpolation between `[bench:receita_mensal_12m_mediana/app_assinatura]` and `[bench:receita_mensal_12m_p75/app_assinatura]`). Goal: ≥ 3 launches by month 4–5 (`q_lancamentos_vs_meta`).

---

## 10. States, transitions, family and reopening

### 10.1 Transitions (the database accepts only these; any state can go to `morta`)

| From → To | Condition | Actor |
|---|---|---|
| sinal → candidata | 3.2 item 4 | routine |
| candidata → pre_teste | E0 + slot (W, WSEO; L to do E1) | routine |
| candidata → em_teste | E0 + advocate + slot + (f) not NULL and not failed (M1; exploration straight to E3/E2E3) | routine (Sunday) |
| candidata → em_construcao | track L + E0 + advocate + (f) not NULL and not failed + `volume_status`≠`nao_medido` + "construo sem teste de demanda" + approval + slot | **owner** |
| candidata → arquivada | E0 failed or pending beyond the deadline | routine |
| pre_teste → em_teste | E1 or WSEO passed, or E1 inconclusive in BR (→ E2E3) + advocate + (f) + slot (WSEO: `volume_status`≠`nao_medido`) | routine (Sunday) |
| pre_teste → em_construcao | track L with E1 passed + advocate + (f) not NULL and not failed + `volume_status`≠`nao_medido` + approval + slot | **owner** |
| candidata / pre_teste / em_teste → congelada | seasonal outside the window (7.2), with `data_reativacao` | routine |
| pre_teste / em_teste → arquivada | deadline, archivable `sem_amostra`/`mata_destino`, 2nd inconclusive E1, `q_planejados_vencidos`, `q_pre_teste_parado` or abort | routine |
| em_teste → validada | E2E3 or E3 passed + advocate + E0 (c) redone + (f) | routine |
| validada → em_construcao | the owner approves the proposal (12.3) + slot | **owner** |
| validada → arquivada | the owner rejects the proposal, incumbent updated (7.2), statement reread below the threshold (12.3) or `q_validada_parada` | routine |
| em_construcao → lancada | the owner informs publication and active billing | **owner** |
| em_construcao → congelada | build stopped by owner decision | routine, quoting the owner |
| lancada → congelada | L1 without sample or refuted, E4 without sample with 0 payers, or E5 | routine |
| lancada → arquivada | E5 | routine |
| congelada → lancada | owner decision | **owner** |
| congelada → candidata | `data_reativacao` (seasonal) | routine |
| congelada → arquivada | no reactivation in `congelada_max_meses` months | routine |
| morta / arquivada → candidata | reopening (10.2) | routine or **owner** |
| any → morta | gate, test, advocate or L1 out of the top 30 | routine |

**How to record (one transaction):**
```sql
BEGIN;
INSERT INTO ideia_eventos(ideia_id, de, para, motivo, evidencia_ids, ator, prova_dono, run_id) VALUES (...);
UPDATE ideias SET estado=?, motivo_morte=?, reabrir_se=?, atualizada_em=datetime('now') WHERE id=?;
COMMIT;
```
- If it fails, `ROLLBACK`.
- On reopening, `motivo_morte=NULL`.
- Do not fill `em`: the database fills it.
- The event must be the idea's **last** one.

**The database refuses:**
- a transition outside the table;
- a missing event or one that is not the last;
- full portfolio or occupied family;
- `em_construcao` or `lancada` without `ator='dono'` with `prova_dono`;
- an idea born outside `sinal`;
- reopening without `REABERTA:`, to a state other than `candidata`, reopening of a severe death without the owner, or a 2nd reopening by the routine;
- an idea from a family with a severe death leaving `candidata`, `pre_teste` or `validada` for test or build without an owner `REABERTA:`, or from a family with a non-severe death leaving `candidata` or `pre_teste` without `REABERTA:` (routine at most 1 per family);
- a family different from the 1st row of `q_familia_sugerida` (most columns, tie → lowest `familia_id`), or a family without `pagador`;
- a change of `preco_alvo` after the test.

### 10.2 Family and reopening

- **Family:** assigned at the start of the gate and immutable afterwards. `q_familia_sugerida` measures three things: same payer (format does not count), competitor in common and ≥ 50% of the signals of the smaller of the two ideas. With 2 of the 3, the idea inherits the `familia_id`.
  - Rewording title, niche or format does not reset the graveyard.
  - Splitting an idea into two keeps the family, and each family occupies at most 1 slot.
- **`reabrir_se`:** record ONE verifiable condition when killing for `sem_pagador`, `incumbente_gratis`, `concorrencia_saturada`, `sem_canal`, `mercado_pequeno` or `prazo`, and on every `arquivada` (in E5, the condition is the market one that would change the result, e.g.: 'concorrente principal encerrou' ("main competitor shut down")).
- **Evaluation:** `q_reabrir_candidatas` on the 1st Sunday of the month and when an `orfao`, `plataforma` or `regulacao` signal cites the competitor.
- **Condition true:** event `motivo='REABERTA: <condition> [sinal#]'` → `candidata`. The routine reopens at most 1 time per idea. Afterwards, run all the cuts from scratch.
- **Idea in a family with a non-severe dead/archived one:** entry into testing **or into build** carries an event `REABERTA: <reabrir_se condition met> [sinal#]`. The routine may do this for at most 1 idea per family (the reopened idea itself may repeat the `REABERTA:` on entry).
- **Severe deaths** (`teste_reprovado`, `advogado_do_diabo`, `risco_banimento`, `excluida_por_regra`): only the owner reopens, with `motivo='REABERTA: ...'`, `ator='dono'` and `prova_dono`. The severe death reason cannot be swapped (the database enforces it). An idea from the same family only enters testing if the event of that entry is from the owner: `de=<current state (candidata or pre_teste)>, para=<state>, ator='dono', motivo='REABERTA: ...', prova_dono`. This also applies when the sibling died after the idea entered `pre_teste`.
- An exploration idea reopened from `morta`/`arquivada` needs the owner; seasonal reactivation from `congelada` may be by the routine, only if `q_exploracao_mes.no_mes` = 0 (otherwise it waits for the following month); in both, no other active exploration (the database enforces it). `exploracao_em` = today.
- On reopening, record `reaberta_de` when the new idea replaces a dead one.

---

## 11. Outputs, checklist and prerequisites

### 11.1 Daily chat message (only if something changed)

Send if there was: a new candidate, a new sheet, a state change, a decided hypothesis, a broken source, a checklist failure, a new pending item, a reopening or a failure of the previous run.

```
[rotina] AAAA-MM-DD · <N> mudanças · <N> pendências
1) Mudanças (≤ 10 linhas):  ideia#id: de→para — motivo [evidências]
2) Pendências do dono (numeradas, com R$ e prazo)
3) Checklist: OK | itens que falharam
4) Run: buscas · sinais_novos · taxa_novidade · motivo_parada
```

Attach `digests/AAAA-MM-DD.md`, generated from the database.

**Immediate alerts** (separate message):
- a decided hypothesis;
- `q_orcamento_experimentos.alerta_80`;
- a `quebrada` source;
- 1st payer of a launched idea, or an E5 step;
- a reopening.

### 11.2 End-of-run checklist

The checklist passes if:
- `q_checklist` returns 0 in all columns;
- every provenance mark is resolved;
- no contrary signal is omitted;
- every `prova_dono` of the run passes `lib.prova_existe`;
- `integrity_check` = ok;
- the backup was written.

Record `runs.checklist_ok` and `checklist_json`. **Never** type this value.

### 11.3 Owner prerequisites (sent in the bootstrap)

1. **Files and routines:** copy the folder to `/workspace/rotina-apps/` and create routines (A) and (B) with timezone `America/Sao_Paulo`.
2. **Cloudflare Pages:** project `rotina-lp` + `CF_PAGES_TOKEN` (Pages:Edit) in `secrets/`. Each experiment lives at `rotina-lp.pages.dev/e<id>/`. Never use Vercel Hobby (it forbids commercial use).
3. **PostHog:**
   - project on the free plan (1 million events/month) + read key + host;
   - events `$pageview`, `cta_click`, `email_submit`, `checkout_start`, with `experiment_id`;
   - **every M1 listing and L1 MVP ships with** `install` (Chrome Web Store: `chrome.runtime.onInstalled`; Shopify: install webhook; iOS/Android: 1st open), `trial_start` and `paid` (billing webhook);
   - reading via HogQL, 1 aggregated query per experiment per day (limit of 2,400/h).
4. **Search Console:** service account with read access + JSON in `secrets/`.
5. **Payments (optional):** restricted read key of the gateway. Without it, the statement comes through the inbox.
6. **Gmail (optional):** with send permission, for the Friday summary.
7. **Marginal income tax (IR) rate** and Play withholding.
8. **`contatos_dono`:** list of emails and domains to exclude from payments (can be `[]`, but it must be provided).
9. **Platform costs** (separate budget, one by one):
   - Apple `[bench:custo_conta/apple_developer]`/year;
   - Play `[bench:custo_conta/google_play]`;
   - Chrome Web Store `[bench:custo_conta/chrome_web_store]`;
   - Shopify `[bench:custo_conta/shopify_partner]`.

   They go in `gastos` with `categoria='plataforma'`.

Without the key it needs, the experiment stays `planejado` and becomes a pending item.

**Fake door page:** no secret in the HTML, email via PostHog, notice "produto em desenvolvimento" ("product in development"). Pages with login or payment require tested authorization and an idempotent webhook.

---

## 12. Sunday, Friday and build proposal

### 12.1 Sunday (after the daily)

1. Shortlist of the 5 best; devil's advocate on the best one.
2. **Portfolio:**
   - fill `pre_teste` and `em_teste` (pre-register and publish);
   - propose building for `validada` ideas and for track L;
   - apply deaths, freezes and archivings.
3. **Expenses:** with 2 ideas in the paid phase and the month's cap tight (`q_gasto_mes`), ask the owner whether the 2nd waits.
4. **Maintenance:** if maintenance `horas` in the week > 3 h or there are > 2 `lancada`, propose freezing the one with the lowest MRR before opening a new build.
5. **"O que aprendemos"** ("What we learned"):
   - closed hypotheses;
   - `q_erro_previsao`: if you always err upward, reduce the next predictions in the same proportion;
   - yield per source;
   - `q_lancamentos_vs_meta`.

### 12.2 Friday 18:00

For each idea that changed during the week:
- gate;
- scores with anchor;
- economics;
- competitors;
- stage with confidence interval;
- spend (`q_gasto_ideia`) and next step.

Also include:
- the portfolio, with the cutoff dates;
- the request for the real hours;
- the pending items;
- the warning that Grok Bot may pause the routine if the owner goes too long without answering.

### 12.3 Build proposal

Only for a `validada` idea (or one from track L with the L1 prerequisites) and with a slot.

- **Evidence:** payments from the statement **reread on the day of the proposal** (refunds up to the date; if net payments fell below `limiar_passa` → `validada → arquivada`), metrics with confidence interval and links.
- **Scope:** MVP in ≤ `mvp_horas_max` h, only the paid flow.
- **Format and stack;** hosting on Cloudflare.
- **Billing:**
  - EN and `global_outros`: MoR (Creem; alternatives Dodo and Paddle);
  - BR: Stripe Brasil;
  - Shopify, Atlassian and app stores: native billing.
- **Stripe Brasil:** the CPF account does not become CNPJ later. If revenue may exceed `receita_alerta_cnpj_brl`/month, ask the owner before the 1st charge.
- **MEI does not allow software:**
  - LC 238/2026 only raised the ceiling (planalto.gov.br/ccivil_03/leis/lcp/Lcp238.htm);
  - PLP 25/2026, which includes programmers in MEI, awaits a rapporteur in the Chamber's CFT (dadosabertos.camara.leg.br, bill 2602924).
- **EU with a store app:** declaring yourself a trader exposes address and phone. Use a PO box or exclude the EU until you have a CNPJ.
- **App Store:** count on 1 rejection `[bench:pct_envios_rejeitados/app_store_2025]`; review within 48 h `[bench:pct_revisoes_em_48h/app_store]`.
- **E5 ladder** pre-registered.
- **"O motivo mais forte pra não fazer"**.

---

## 13. Anchor examples

**Rejection (real owner cases): Cava and Arquibancada.** Consumer, free, no channel and no paying competitor: cuts 2, 5 and 6.

**Sheet that passes (illustrative):**
- **Idea:** extension for [profession] that solves [complaint in 34 reviews of 1–3 stars, sinal#…] of incumbent X: 40 thousand users, no update for 16 months and no sign of life in 90 days.
- **Track:** M.
- **Payer:** [profession] who already pays US$12/month to X.
- **Channel:** Chrome Web Store search for "Y" + 2 synonyms.
- **Economics:** US$12 via Creem, customer in the US → `lib.liquido_usd(12,'creem',0.275)` = 8.07 → n300 = 38.
- **Universe:** 40 thousand → 38 ≤ 3%.
- **Strongest reason not to do it:** X may update.

---

## 14. Known limits

- The routine does not see the real keyword volume: only the owner provides it.
- Validation in EN with paid media does not fit the budget.
- The v1 thresholds are heuristic, except those of E4. Calibration is mandatory.
- Success through polish, design or editorial featuring is not detectable without talking to users.
- `lib.TAXAS` is fixed in the code. If a fee changes on reverification, propose editing `lib.py` + `test_lib.py` in the CHANGELOG.
- Atlassian Forge goes to 17% after US$1M lifetime. Review when getting close.

---

## 15. Calibration and evolution (1st Sunday of the month)

- **Thresholds:** every 5 closed hypotheses of the same stage and metric, recalculate. Record a new version in `limiares` (`origem='calibrado'`) without deleting the previous one.
- **Benchmarks:** reverify the `benchmarks_vigentes` older than `benchmarks_reverificar_dias` days (the checklist flags at 90; the interval between 1st Sundays reaches 35). Same value: `UPDATE benchmarks SET verificado_em=date('now') WHERE id=?`. Different value: new row. Different fee: lib edit proposal.
- **Reopening:** run `q_reabrir_candidatas`.
- E5 uses `[config:e5_d60_min_usd]` (D60) and `[config:e5_d120_min_usd]` (D120), per idea; calibrate them here, not the portfolio goal.
- **Prompt:** propose changes in `CHANGELOG.md`, based on yield per source, prediction error, cap stops, calibrated thresholds and reopenings. **Do not apply.**
