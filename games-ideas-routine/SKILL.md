---
name: games-ideas-routine
description: >-
  A daily autonomous routine that finds, validates and only then proposes building small games
  (web portals like Poki/CrazyGames, Steam, mobile, Roblox/UEFN) for a solo developer who builds with AI.
  Use it when setting up or running a recurring "find me a game idea worth building" agent (any agent
  with a persistent folder, terminal and web access), when the
  owner asks why a game idea was killed/archived, or when calibrating the funnel. It starts from loops
  that are already proven (platform arbitrage, genre cohorts, jams) plus a structural twist, keeps all
  state in SQLite with database-enforced guards, validates by measuring player behavior (free portal
  playtests → Steam page/demo → paid tests only when they buy a real sample), picks the engine per idea,
  and every number carries a source. Goal is a portfolio with net R$/hour, not MRR. For a one-off
  go/no-go on a single concept, validate it directly with a quick playtest; once building, use `game-feel`, `game-taste-2d`,
  `game-taste-3d` and `game-polish`.
---

# Game ideas routine (search → behavior test → build proposal)

A daily routine for an autonomous agent. It looks for game ideas whose **core loop is already proven**
somewhere, adds a **structural twist**, and tests each one by **measuring what players do** in free or cheap
tests before the owner invests real hours. Everything it decides is stored in SQLite and guarded by triggers,
so an agent that follows this text cannot "talk an idea through" the funnel by mistake, by a convenient label or by
skipping a step.

**Threat model.** The guards stop errors, rationalization and shortcuts that this text allows; they cannot stop an
agent that deliberately rewrites rows against it (the agent owns the database file). Therefore: never `UPDATE` or
`DELETE` a row of `hipoteses`, `ideia_eventos`, `metricas`, `evidencias`, `ideia_concorrentes`, `limiares`, or the
past rows and the `lancado_em`/`proprio_ideia_id` of `concorrentes`, `concorrente_snapshots` and `tendencias`, except
through the procedures written here — and the same for every other column: write a column only where this text
says to write it (the database also locks the ones that decide a destiny: an archive's class, a signal's identity,
the exploration month, the sheet flags, the source label) —, never touch `schema.sql` objects (no `DROP`/`ALTER`), and never type an owner phrase that is
not literally in `inbox/`.

## How to use this skill

1. **Copy the folder** to the agent's persistent workspace. The text below assumes `/workspace/rotina-jogos/`
   (the Grok Bot persistent folder); change `dir_base` in `seed_config.csv` if yours differs.
2. **Schedule two runs** in the owner's timezone: (A) daily at 08:00 and (B) Friday at 18:00 (section 3).
3. **First run = bootstrap** (section 3.1): it runs `seed.py`, tests every data source live and sends the owner a
   list of prerequisites (portal accounts, tax rate, optional API keys).
4. **Adapt the owner profile** in `seed_config.csv` before the first run: goal (`meta_*`), budget (`teto_gasto_*`),
   hours per week, hour caps per track. The defaults are those of the original owner (a Brazilian solo dev with
   8–10 h/week, R$500 per idea).
5. **Run the tests** whenever the folder changes (the suite pins the profile values its fixtures use, so adapting
   `seed_config.csv` never breaks it): `python3 -m unittest test_lib test_schema test_queries test_e2e test_guards_v2 test_queries_v2 test_review_r1 test_review_r2 test_review_r3 test_review_r4 test_review_r5 test_review_r6 test_review_r7 test_review_r8 test_review_r9 test_review_r10 test_review_r11 test_review_r12 test_review_r13 test_review_r14 test_review_r15 test_review_r16 test_review_r17 test_review_r18 test_review_r19 test_review_r20 test_review_r21 test_review_r22 test_review_r23 test_review_r24 test_review_r25 test_review_r26 test_review_r27 test_review_r28 test_review_r29 test_review_r30 test_review_r31 test_review_r32 test_review_r33`.

**Language.** Rules, tables and code are in English; **identifiers stay in Portuguese** (tables, columns, state
values such as `candidata`, `morta`, `em_teste`) because the database, queries and tests depend on them.
Owner-facing messages and the literal phrases the agent matches (e.g. "aprovo a construção da ideia#12") are in
Brazilian Portuguese; translate both together if your owner speaks another language.

**Files in this folder**

| File | What it is |
|---|---|
| `SKILL.md` | The routine (this file): mission, gate, funnel, thresholds, modes, engine, state machine, outputs |
| `schema.sql` | SQLite schema with the guards (portfolio, one Steam bet, family/graveyard, reopening, owner proof, engine before build, no loot box, no free chat, public room list) |
| `queries.sql` | Ready-made queries for every recurring decision |
| `lib.py` / `test_lib.py` | Deterministic math (Wilson interval, decision for rate/count/mean/ceiling, Steam projection, net from abroad, Roblox, portal revenue, sample size, owner proof) + tests |
| `test_schema.py` / `test_guards_v2.py` / `test_review_r1.py` / `test_review_r2.py` / `test_review_r3.py` / `test_review_r4.py` / `test_review_r5.py` / `test_review_r6.py` / `test_review_r7.py` / `test_review_r8.py` / `test_review_r9.py` / `test_review_r10.py` / `test_review_r11.py` / `test_review_r12.py` / `test_review_r13.py` / `test_review_r14.py` / `test_review_r15.py` / `test_review_r16.py` / `test_review_r17.py` / `test_review_r18.py` / `test_review_r19.py` / `test_review_r20.py` / `test_review_r21.py` / `test_review_r22.py` / `test_review_r23.py` / `test_review_r24.py` / `test_review_r25.py` / `test_review_r26.py` / `test_review_r27.py` / `test_review_r28.py` / `test_review_r29.py` / `test_review_r30.py` / `test_review_r31.py` / `test_review_r32.py` / `test_review_r33.py` / `test_queries.py` / `test_queries_v2.py` / `test_e2e.py` | Tests of the guards, of every query, and of the funnel end to end on the seeded database |
| `seed.py` + `seed_*.csv` | Bootstrap and seeds: config/assumptions, sourced benchmarks, thresholds, data sources |
| `CHANGELOG.md` | Version history, assumptions without a source, known open points |

**Honest limits.** Games are a hit-driven market: the 2025 Steam median was US$318 gross `[bench:receita_bruta_mediana/steam_2025]` and about half the
launches ended with fewer than 10 reviews `[bench:pct_menos_10_reviews/steam_2025]`. No funnel removes that.
What this one does is stop the owner from spending 100+ hours before players have shown, in a measured test,
that they keep playing. Benchmarks were verified on 2026-10-26 and are re-checked every ~55 days.

---

## 0. Files, persistence and owner input (before anything else)

- **Base folder:** `/workspace/rotina-jogos/`. Only `/workspace` is persistent. Installed packages may disappear in an update.
- **Start of every run, in this order:**
  1. `cd /workspace/rotina-jogos`.
  2. Check that `python3` and the `sqlite3` module exist. Reinstall whatever is missing.
  3. Run `python3 -m unittest test_lib test_schema test_queries test_e2e test_guards_v2 test_queries_v2 test_review_r1 test_review_r2 test_review_r3 test_review_r4 test_review_r5 test_review_r6 test_review_r7 test_review_r8 test_review_r9 test_review_r10 test_review_r11 test_review_r12 test_review_r13 test_review_r14 test_review_r15 test_review_r16 test_review_r17 test_review_r18 test_review_r19 test_review_r20 test_review_r21 test_review_r22 test_review_r23 test_review_r24 test_review_r25 test_review_r26 test_review_r27 test_review_r28 test_review_r29 test_review_r30 test_review_r31 test_review_r32 test_review_r33`. If it fails, **stop** and warn in the chat.
  4. **If `.bootstrap_feito` does not exist:** run the bootstrap (3.1) and create `.bootstrap_feito` when done. If `rotina.db` already exists without `.bootstrap_feito` (interrupted bootstrap): with `PRAGMA user_version`=1 and `config` not empty, skip `seed.py` and resume from step 2 of 3.1; otherwise create `backups/` if missing, rename the file to `backups/rotina-bootstrap-falho-AAAAMMDDHHMM.db` and run `seed.py`.
  5. **If `.bootstrap_feito` exists:** open `rotina.db` and run `PRAGMA foreign_keys=ON` (applies **per connection**, repeat it on every new connection). `PRAGMA integrity_check` must return `ok` and `PRAGMA user_version` must return 1.
     - Database missing or corrupted: restore the most recent backup from `backups/`.
     - No backup: **abort** and send "BANCO INACESSÍVEL" ("DATABASE INACCESSIBLE"). Never recreate the database on your own.
  6. **Read the owner input** (section 0.1).
- **End of every run:** `python3 -c "import sqlite3;sqlite3.connect('rotina.db').execute(\"VACUUM INTO 'backups/rotina-AAAA-MM-DD-HHMMSS.db'\")"` (seconds in the name: there are two backups per run, 3.2 item 6). Keep the 28 most recent (14 runs).
- **Seeds:** the initial rows only via `seed.py`. After the bootstrap, `limiares` and `benchmarks` change only through the INSERTs of section 15 (new version / new row with `source_url`), and `config` only with `origem='medido'` (PTAX rates, or the measured portal US$/1,000 plays of section 15) or through the owner. Typing any other benchmark, threshold, source or config by hand is forbidden. Config with `origem='dono'` only changes through a message from the owner.
- **Reading config:** `valor` is text. Convert it with `float()` or `int()` before calculating.
- **Secrets:** they live in `secrets/`, never go into messages and stay out of backups.

### 0.1 Owner input

The owner writes in two ways: replying in the bot chat or in a file in `inbox/`.

1. **Save before processing.** At the start of the run, save **literally** every owner message later than the last one already saved in `inbox/` (or `inbox/lido/`) to `inbox/AAAA-MM-DD-HHMM-chat.md`: one header line per message with its date and time (`## AAAA-MM-DD HH:MM`), then the message on the next line exactly as written — no prefix, quote mark or markdown before it (`lib.prova_existe` reads a line start as a sentence start).
2. **Record each item** with `ator='dono'` and `prova_dono` = literal quote in quotation marks, then the date and time:
   `'"<phrase…>" chat AAAA-MM-DD HH:MM'` — the opening quote is the first character (the database checks the phrase
   right after it).
3. **Move** the processed files to `inbox/lido/`.
4. **Check in the checklist:** every `prova_dono` recorded in the run must exist literally in a file of `inbox/lido/` **moved in this run**, and the **quote** must contain `ideia#<id>` (or the topic, for expenses and hours). A short answer ("sim", "aprovo") does not count: ask again for a full sentence citing the idea. Check with `lib.prova_existe(prova, textos_desta_rodada, ideia_id, frase)` (`frase` = the 0.1 phrase with the id filled in, for owner transitions — for the launch only the fixed prefix "ideia#N lançada em"; without `ideia_id` only for expenses and hours)
   **before** the COMMIT of the owner event; if it fails, `ROLLBACK`. The database also refuses an owner event whose
   proof does not contain `ideia#<id>`.

**Input types:**
- build approval: "aprovo a construção da ideia#N";
- resuming a frozen build or a frozen live game, back to the state it froze from: "descongelo a ideia#N" (an idea
  frozen before its build comes back only by reactivation, `congelada → candidata`); if the database refuses it
  because the slot was taken meanwhile (`portfolio_cheio`, `familia_ocupada`, `uma_aposta_steam`), keep the idea
  `congelada` and open a pending item naming the idea that holds the slot (the owner chooses which one goes on);
- Steam bet release (section 7.1): "libero a aposta Steam da ideia#N";
- building without a behavior test: "construo sem teste de comportamento a ideia#N";
- launch: "ideia#N lançada em <plataforma> em <data>";
- test cancellation: "cancelo o teste da ideia#N";
- **dashboard readings** (portals, Steamworks, Roblox, publisher), in the template below;
- **milestones and test ends:** "ideia#N <etapa>: teste iniciado em <data>" (or Basic Launch / página / demo no ar)
  sets `experimentos.inicio`; "ideia#N <etapa>: plataforma encerrou o teste em <data>" makes `prazo_esgotado` true;
- **build measurements:** "ideia#N build: build_mb=…; tempo_gameplay_s=…" (`ideias.build_mb`, `ideias.tempo_gameplay_s`,
  written only from that quoted message: they route the portal path);
- expenses (including platform fees) and hours of the week (by idea and `tipo`);
- monthly revenue per game and platform (statement), and tax withheld abroad;
- income tax (IR) rate and the accountant's answer about crediting US withholding (`compensa_eua`);
- excerpts from closed groups (source `dono_campo`);
- reopening by the owner (a serious death, a second reopening, or a sibling's entry in a family with a serious death):
  "reabro a ideia#N" (the database refuses any owner `REABERTA:` event without it).

**Dashboard template** (send it to the owner whenever a reading is due):
```
ideia#N <etapa> <data da leitura>: views=…; cliques=…; jogadas=…; jogadores_novos=…; minutos_media=… (por jogada|por jogador);
pct_3min=…%; d1=…%; c2p=…%; sessoes=…; pct_sessoes_10min=…%; wishlists=…; visitas_pagina=…; demo_jogadores=…;
demo_wishlists=…; installs=…; custo_brl=…; ccu_pico=…; salas_abertas_pico=…;
notas_webfit=CTR x/5, tempo y/5, C2P z/5; decisao_plataforma=aceitou|recusou|pendente
```
Only the fields of the stage are needed. Dashboards report **totals**: for additive metrics record in `metricas` the
**increment** since the last reading (total now − sum already recorded) on the reading date, with
`INSERT ... ON CONFLICT(experimento_id,data,metrica) DO UPDATE SET valor = valor + excluded.valor` (two readings on
the same day add up). **Daily peaks**
(`ccu_pico`, `salas_abertas_pico`) are not additive: record each day's value as read, on the day it refers to
(`ON CONFLICT … DO UPDATE SET valor = MAX(valor, excluded.valor)`), never as an increment. Sources: `fonte` = `portal_dashboard`,
`steamworks`, `roblox_dashboard`, `fortnite_api`, `publisher`, `telemetria` or `dono_extrato`. Means and percentages
become sums and counts before recording, always with the **same denominator** the dashboard used for the mean:
- `playtime_total_s = minutos_media × 60 × D`, where D = `jogadas` if the mean is per play (Poki) or
  `jogadores_novos` if per player; the hypothesis then uses that same D as `n` (7.4);
- `jogadores_d1 = round(d1 × jogadores_novos)` (M1: `round(d1 × installs)`); `jogadas_3min = round(pct_3min × jogadas)`;
  `sessoes_10min = round(pct_sessoes_10min × sessoes)`;
- `decisao_plataforma`: `aceitou` → `aceite_plataforma=1` and `decisao_plataforma=1`; `recusou` →
  `aceite_plataforma=0` and `decisao_plataforma=1`; `pendente` → record nothing;
- `notas_webfit` → `webfit_notas_ok` = how many of the 3 scores are ≥ 3.
- **State metrics** (`webfit_notas_ok`, `aceite_plataforma`, `decisao_plataforma`) are recorded **once**, on the date of
  the result; a later reading that repeats them adds no row.

The phrase must **start a sentence** of the owner's message — after the start, a `.`/`!`/`?`/`;`/`:`, a line break or
a list bullet, and the quote in `prova_dono` must **start with the phrase** — quote the phrase, not the clause
before it ("não aprovo a construção da ideia#N" or "ainda não aprovo…" is no approval: `lib.prova_existe` with
`frase` and the database both refuse a quote that does not begin with the phrase). The database matches the owner phrases case-insensitively (accented capitals
Ç, Ã, Õ, É included); a phrase with other words in the middle is refused
(`frase_do_dono`): ask the owner again with the exact phrase. Straight (") and curly (“ ”) quotes both work. If
the phrase **is** literally in the inbox and the database still refuses, the `prova_dono` is malformed (quote not
starting with the phrase, missing `ideia#N`): fix the quote, never ask the owner again for a phrase already given. If the database refuses an owner phrase
because a slot is taken (`portfolio_cheio`, `familia_ocupada`, `uma_aposta_steam`), keep the idea where it is and open
a pending item that quotes the phrase and names its `inbox/lido/` file; while that item is open, that file counts as a
text of the run for `lib.prova_existe` (apply the phrase when the slot frees, then resolve the item). Any other
refusal of a literal owner phrase (`transicao_fora_da_tabela`, `descongelo_fora_da_origem`, `etapas_nao_passaram`, …)
means the order does not fit the idea's state: open a pending item quoting the phrase and explaining the valid path
(e.g. "a ideia#N já está em teste: responda 'aprovo a construção da ideia#N' quando ela for validada").

Never invent, summarize or paraphrase an owner input.

---

## 1. Mission, goal and limits

You find and **validate** game ideas for a solo Brazilian dev who builds with AI. You only propose building after
players have shown, in a measured test, that the loop holds them.

- **Platforms:** web portals (Poki, CrazyGames), Steam (PC), mobile (Android/iOS), Roblox and UEFN (Fortnite).
- **Owner's time:** `horas_semana_dono_min`–`horas_semana_dono_max` (8 to 10 h/week × 45 working weeks ≈ 360–450 h/year, ~270–350 h of development).
- **Why not MRR.** A game rarely gives recurring revenue: Steam sales concentrate at launch and a portal game's tail
  decays well below its launch peak. The goal is therefore a **portfolio** measured by **net R$ per hour**.

**Goal (config `meta_*`):**

| | Year 1 (from the bootstrap) | Year 2 |
|---|---|---|
| Process | ≥ `testes_meta_ano` behavior tests concluded (W1/S1/S2/M1/R1; W2 is the second half of a Poki test and does not count twice), ≥ 1 game live with monetization by month 6 | at most 1 Steam or mobile bet, gated (7.1) |
| Revenue | the summed portfolio reaches `meta_mensal_usd` net/month (≈ the €100 CrazyGames payout floor) by month 12; `meta_mensal_stretch_usd` is a stretch, not a plan | R$/h ≥ `meta_rs_hora_ano2` |
| Mother metric | net R$/h of the last 12 closed months ≥ `meta_rs_hora_ano1` (`q_meta_portfolio.rs_por_hora_12m`, converted at `cambio_usd_brl`) | ≥ `meta_rs_hora_ano2` |
| Kill | `meta_prazo_meses` months with no game live with monetization **and** no month ≥ `meta_mensal_usd` → send the owner a "pausar jogos?" pending item | idem |

If by month 6 no idea has passed W1, change the **kind of idea** (source, genre, platform), not the volume.

- **Test budget:** R$0 for portal tests; `teto_gasto_ideia_brl` per idea and `teto_gasto_mes_brl` per month for paid
  stages. **Platform fees** (Steam Direct US$100 per app `[bench:steam_direct_taxa/steam]`, Google Play US$25 `[bench:custo_conta/google_play]`,
  Apple US$99/year `[bench:custo_conta/apple_developer]`) stay outside this cap,
  each one approved by the owner.
- **Portfolio (the database enforces it):** up to 4 `pre_teste`, 2 `em_teste` and 1 `em_construcao`, at most 1 slot
  per family and at most **1 Steam bet** (track S in `em_teste`, `validada` or `em_construcao`).

**You do on your own:** collection, analysis, filtering, scoring, the prototype brief, the test plan, reading public
APIs, writing to the database and sending messages.

**Only the owner does:** building the prototype (with AI), uploading builds, requesting portal tests, posting clips,
spending, paying platform fees, publishing, reading private dashboards, approving a build and changing this prompt.
You prepare everything and record it as a **pending item** in `pendencias` (its `id` is the number shown to the owner;
`resolvida_em` + `prova_dono` when the owner reports it done; list with `q_pendencias_abertas`). A `reabrir_se` that
waits for the owner is written `pendencia#N resolvida`.

---

## 2. Principles

1. **Proven loop first, then a structural twist.** Novelty without a reference is the exception quota (5.1).
2. **Start from the median.** Every success case is shown next to its segment's median. Project above the P75 only
   with data measured in your own tests.
3. **Mechanical provenance.**
   - Every number in a sheet, digest or message carries a mark: `[sinal#id]`, `[bench:metrica/segmento]`,
     `[config:chave]`, `[coorte:tag/ano]` or `[metrica exp#id data]`; the routine's own numbers carry
     `[limiar:etapa/metrica/segmento]`, `[gasto:ideia#N]`, `[horas:ideia#N]` or `[score:ideia#N]`. Counts, ids and dates read
     from the routine's own database (runs, pending items, deadlines) need no mark. Without a mark, `checklist_ok=0`.
   - A signal only counts with HTTP 200 **in this run** and a `trecho_literal` of at least 40 characters (the
     exception to the HTTP 200 is `dono_campo`, which still needs the 40-character excerpt).
   - Recording a signal, URL or number from prior knowledge is forbidden.
4. **Behavior, not opinion.** Likes, comments, upvotes and "looks fun" are worth zero. Playtime, retention,
   conversion to play, wishlists and platform decisions are the evidence.
5. **Building is cheap, so copying is too.** AI-labeled games were ~31% of 2026 Steam launches and took 10–27% of the
   revenue `[bench:pct_lancamentos_ia/steam_2026]`. Speed is not an advantage; the twist and the test are.
6. **Synthetic evidence is worth zero.** An LLM saying a game is fun is not a playtest.
7. **A source without data is not zero demand.**
8. **Calculations only through `lib.py`.** Call with positional arguments, in the signature's order.
9. **Also record what is against.** Every signal read about the idea goes to `evidencias` with polarity +1 or −1.
10. **The owner's preferences are hypotheses.** When the owner prefers a design (e.g. public rooms), weigh it
    against the evidence and recommend the better path even if it disagrees (section 6.4).

---

## 3. Schedules and order of runs

Configure two routines in the bot (timezone `America/Sao_Paulo`):

- **(A) daily, 08:00:** section 3.2. On **Sunday** it then also runs 12.1; on the **1st Sunday of the month**, also
  15. Always record `runs.tipo='diaria'`; the Sunday work goes in `resumo_json`.
- **(B) Friday, 18:00:** section 12.2, with `runs.tipo='sexta'`.

**`runs` rules:** open with `status='rodando'`, close with `ok`, `parcial` (a fixed task failed) or `falhou`. A run
`rodando` for more than 3 h becomes `falhou`. The bootstrap records `tipo='bootstrap'`. If the last `sexta` run with
status `ok` or `parcial` (or a `diaria` whose `resumo_json` has `semanal_atrasado=true`) is more than 7 days old, the
next (A) generates the overdue weekly summary and records `semanal_atrasado=true` in its `resumo_json`. Grok Bot keeps only 20 executions and does not
retry failed ones: if yesterday's failed, say so today.

### 3.1 Bootstrap (only without `.bootstrap_feito`)

1. `python3 seed.py rotina.db` (it also creates `backups/`, `inbox/lido/`, `digests/`, `briefs/`, `adv/` and `secrets/`).
2. **Exchange rate:** PTAX selling rate of the last business day before today (source `ptax_bcb`). Record
   `cambio_usd_brl` and `cambio_data` in `config` with `origem='medido'`; the same for `cambio_eur_brl` (source
   `ptax_bcb_eur`, CrazyGames pays in EUR). Refresh both on the 1st run of each month.
3. **Sources:** test each source with 1 request and record the status; a source that failed stays `degradada`; a
   source that needs the owner's key and has none in `secrets/` → `desligada` (no alert), back to `ok` when the key
   arrives.
4. **Cohorts:** start the rotation of 4.5 (the first runs fill `tags_iniciais` within the page cap).
5. The bootstrap does **not** create ideas.
6. Send "bootstrap: N fontes ok, N sinais, N coortes" and the prerequisites list (11.3).

### 3.2 Daily run

1. **Context:** `q_portfolio_vagas`, `q_hipoteses_abertas`, the last 7 `runs`, the last note of `CHANGELOG.md`, the
   owner input (0.1).
2. **Fixed tasks (100%), in this order:**
   - **Milestones of `planejado` experiments** (table in 7.3). On the 1st occurrence: `estado='rodando'`,
     `inicio` = its date.
   - **Orphans:** `q_experimentos_orfaos` → close the open hypotheses as `inconclusiva_amostra_parcial`
     (aprendizado='ideia saiu da etapa') and `estado='encerrado'`, **without** applying a destination.
   - **Readings due:** for every `rodando` experiment whose platform has no public API, ask the owner for the
     reading (template 0.1) when the test ends and at least every 7 days. Record what arrived.
   - **Public metrics of own games:** Fortnite Data API (D-1 of own islands, daily; it keeps only 7 days), Steam
     CCU and reviews of own apps, Roblox `games` endpoint of own universes.
   - **Competitor snapshots** (`rank_lista=''`) for every competitor linked to an idea that is neither `morta` nor
     `arquivada`: **daily** for `roblox`/`uefn` when the idea is in `pre_teste` or beyond (trends move in days),
     **weekly** (Sunday) for the others. A competitor registered today is snapshotted right away. Stores with a
     per-game source in `fontes`: Steam, Roblox, UEFN, App Store; Poki, CrazyGames, Google Play and web pages have
     none, so their competitors get a snapshot only when they show up in a ranking source (the checklist does not
     count them). Write every snapshot with `INSERT … ON CONFLICT(concorrente_id,data,pais,rank_lista) DO UPDATE`.
     A snapshot counts only with a popularity number (reviews, CCU, plays, ratings, installs or favorites): on Steam,
     combine `steam_appdetails` (price) with the CCU and review sources in the same row; a game released in the last
     120 days on Steam, Roblox, UEFN or the App Store with no popularity number blocks the test of any idea linked to it
     (`popularidade_indeterminada`). A weekly snapshot missed (a failed Sunday) is taken in today's run.
   - **Trends:** for each `tendencias` with `status='aberta'`, snapshot the leader (reuse the day's competitor
     snapshot when it exists); close it (4.4) when its rule is met.
   - **`q_sinais_parados`:** an idea in `sinal` beyond `sinal_max_dias` without meeting the candidacy rule →
     `arquivada` (`arquivamento='operacional'`, `reabrir_se` = the missing criterion, e.g. 'sinal em 2ª plataforma').
   - **`q_planejados_vencidos`:** → close the hypotheses as `inconclusiva_amostra_parcial`, set the experiment
     `estado='encerrado'`, `decisao='planejado_vencido'` **without** applying a destination, and move the idea to
     `arquivada` (`arquivamento='operacional'`) with `reabrir_se`='pendencia#N resolvida' — unless it was the
     CrazyGames fallback of a Poki refusal: then the refusal stands and the idea goes to `morta` (`teste_reprovado`)
     (the database refuses archiving it).
   - **`q_experimentos_a_fechar`:** close (7.4, "When deciding"); a refuted stage applies its `mata_destino` in the same
     run (7.4 `mata`), never waits for `q_em_teste_sem_experimento`.
   - **`q_pre_teste_parado`:** → `arquivada` with `reabrir_se`='vaga de teste livre e ideia ainda no topo do score'.
   - **`q_validada_parada`:** `pendencia` → open (once) a pending item asking for "aprovo a construção da ideia#N"; the idea
     stays `validada`. `arquivar` (after `validada_max_dias_arquivar`) → `arquivada` with `reabrir_se`='pendencia#N
     resolvida' (a reopened idea redoes its tests). `pendencia_vaga` (validada waiting behind a build in progress) →
     open (once) a pending item comparing both ideas' projected R$/h and offering to freeze the build
     (`em_construcao → congelada`) or keep waiting; never archive for this reason.
   - **`q_em_teste_sem_experimento`:** an `em_teste` idea with no open experiment → open the next stage of its track
     (W1 → W2 on the Poki path, S1 → S2, CrazyGames fallback) or, if none is due, decide it: the latest decided stage refuted → its `mata_destino` (7.4 `mata`); `validada` when
     all stages passed; otherwise `arquivada` with `reabrir_se`='pendencia#N resolvida'.
   - **`q_irmas_bloqueadas`:** a scored candidata (or `pre_teste` idea, whose sibling died while it waited) blocked by an older sibling in the family's graveyard. `grave=1` or
     `cota_rotina_usada=1` → open ONE pending item asking for "reabro a ideia#N" (on the owner's no, archive it,
     `arquivamento='operacional'`); otherwise reopen it with the routine's REABERTA once the sibling's `reabrir_se` is
     met (10.2). `q_candidatas_paradas` `bloqueada_cemiterio` archives one still blocked after `candidata_fila_dias`
     (`arquivamento='operacional'`, `reabrir_se` = the blocking sibling's, or 'pendencia#N resolvida' with the
     "reabro a ideia#N" item when the sibling has none, e.g. a serious death).
   - **`q_candidatas_paradas`:** `sem_mesa` → `arquivada` with `reabrir_se` = the desk criterion that was missing;
     `sem_vaga` (scored, no slot for `candidata_fila_dias`) → `arquivada` with `reabrir_se`='vaga de teste livre e
     ideia ainda no topo do score' (a reopened idea redoes the desk with fresh snapshots).
   - **`q_checklist.horas_estouradas`:** prototype hours (validacao + marketing) above 1.5× `horas_estimadas` → open
     ONE pending item 'horas estouradas ideia#N' with `pendencias.ideia_id` = N (every pending item about an idea
     records its `ideia_id`) (cut scope, freeze or continue); a trend idea past its trend hour cap
     is archived when its window cannot hold the rest (`arquivamento='operacional'`, `reabrir_se`='nova tendência aberta
     no mesmo gênero').
   - **`q_construcao_longa`:** → a pending item to the owner (cut scope, continue or freeze), opened **once** per cap crossed
     (hours, then weeks); "continue" closes it and the same cap is not raised again.
   - **`q_congeladas_vencidas`:** `reativar` → `congelada→candidata` with `data_reativacao=NULL` in the same UPDATE;
     `arquivar` → `congelada→arquivada` with `reabrir_se` (a live game frozen by E5 never expires this way: it stays
     under `q_e5_escada`).
   - **`q_tendencia_fechada_fila`:** a clone in `candidata`/`pre_teste` whose trend closed before it got a test →
     `arquivada` (`arquivamento='operacional'`, `reabrir_se`='nova tendência aberta no mesmo gênero'); run it before
     any entry of the day.
   - **`q_tendencia_fechada_planejados`:** a planned experiment of an idea whose trend closed → close its hypotheses as
     `inconclusiva_amostra_parcial`, `estado='encerrado'`, `decisao='orfao'`, and archive the idea (`pre_teste`/`em_teste`
     only; a build follows the 4.4 pending item, and S3/S4/E5 are not listed) with
     `reabrir_se`='nova tendência aberta no mesmo gênero'; cancel the prototype pending item. A trend idea never
  reopens (`q_reabrir_candidatas` leaves out `fonte_ideia='tendencia'`): a new trend in the genre becomes a **new**
  idea linked to the new leader, with `reaberta_de` = the old one. If the planned experiment
     was the CrazyGames fallback of a Poki refusal, the refusal stands: `morta` (`teste_reprovado`).
   - `receita_snapshots` of the `lancada` ideas and of the `congelada` ones frozen by E5 (the game stays live) (from the owner's statement; one row per idea, month and platform; a
     statement in EUR is converted with `valor_eur × cambio_eur_brl ÷ cambio_usd_brl` before `lib.liquido_exterior`), then
     `q_e5_escada`: `congelar`/`arquivar` as in 7.2 (`arquivar` → `arquivamento='resultado'`, `reabrir_se`='receita
     mensal >= e5_d120_min_usd'; a launched game is never a family graveyard); `aguardar_extrato` → ask the owner for the missing statement (a
     month without data, or missing a platform that reported in an earlier month, is never zero).
   - Decision of each open hypothesis (7.4).
   - PTAX of the last previous business day.
3. **Signal collection** (4).
4. **Triage:**
   - group signals into ideas and record `evidencias`;
   - when creating the idea, record `hook`, `twist`, `referencia`, `genero_central`, `fonte_ideia`, `plataforma`,
     `modo`, `mercado`, `ai_arte_visivel`; the track and the family are assigned at the start of the gate (section 5);
   - `genero_central` = the Steam tag of the core loop (from `steam_tag_map`), in lowercase snake_case
     (`bullet_heaven`, `roguelike_deckbuilder`); never invent a spelling — reuse the one already in `ideias` for the
     same tag (the database accepts only `[a-z0-9_]`);
   - **sinal → candidata** when `q_fontes_distintas_por_ideia` gives `plataformas` ≥ 2 (counted only over signals of
     measured traction: a complaint, a platform/regulation signal or an `arbitragem` signal does not add a platform),
     or — for an arbitrage idea — `plataformas` = 1 plus `plataformas_arbitragem` ≥ 1 on another platform (the
     documented gap) and `sinais_prova` ≥ 2, and
     `referencia` names a game with measured traction (a `concorrentes` row with a snapshot). `dono_campo` counts as
     at most 1 platform; a registered rival (`concorrente` signal) counts as none. Track R: the reference in a
     Roblox/Fortnite top sort (snapshot of the last 30 days) replaces the 2-platform rule (those games live on one
     platform). Exploration (5.1) and graduation/ports (7.1) have their own rule.
   - **Competitors:** every game cited as reference or rival goes to `concorrentes` (once per `loja`+`id_loja`) with
     `lancado_em` (its release date on the store/portal; the database refuses a test while a linked competitor lacks
     it; when the page shows no date — Poki, CrazyGames — use the date of the oldest collected signal or snapshot that
     cites the game with `lancado_em_incerto=1`: an upper bound that never makes the game a trend, `v_tendencia_viva`
     ignores it. Use `incerto=1` only when there is no date at all: CrazyGames pages show a release date (a month →
     the 1st of that month, `incerto=0`), and a game first seen in a `new` list (`poki_new`, `crazygames_new`) takes
     that date with `incerto=0`; note that the portal sources in `fontes` give only `new` lists, so a portal hype is not
     detected as a trend unless the owner pastes its plays/favorites — see 14), is linked in `ideia_concorrentes` with `papel='referencia'` (the X of the twist, exactly the game the idea
     derives from) or `papel='rival'`, and gets its 1st snapshot right away. A linked live hype (4.4) must be registered in
     `tendencias` before any test (the database refuses `tendencia_nao_registrada`).
5. **Gate (5) and desk (6)** on the new candidates. At most **2 complete sheets per day**.
6. In this order: draft the summary and the digest (11.1, not sent yet), backup (`VACUUM INTO`, section 0), checklist
   (11.2, which checks that file and the provenance marks of the drafted summary and digest), record `checklist_ok`
   and close the run, a second `VACUUM INTO` (so the latest backup holds the closed run), then send the summary.

---

## 4. Signal collection

### 4.1 Sources

Use only the `fontes` table (from `seed_fontes.csv`, endpoints tested on 2026-10-26). Different endpoints of the
same `plataforma` count as one.

**Forbidden for automation:** scraping SteamDB (its FAQ forbids it), fortnite.gg (blocked), Reddit without OAuth,
the TikTok Research API (commercial use not eligible), `pytrends`. A one-off manual look is fine; a crawler is not.

**How to collect:**
- **Language:** English for global, Portuguese for BR. Record the `idioma`.
- **Throttle:** store.steampowered.com ≤ 1 request/2 s with exponential backoff on 429; SteamSpy ≤ 1/s (and 1/min
  for `request=all`), never the same appid twice in 24 h; YouTube ≤ 100 `search.list`/day (separate quota) plus
  10,000 units for the rest; Twitch reads `Ratelimit-Remaining` and stops below 50. Cache everything for 24 h.
- **Validate the content type** of every API response: HTML where JSON was expected = the source broke silently
  (it happened with the old Steam `appreviews`) → `quebrada` and warn.
- **Undocumented endpoints** (Roblox explore-api, portal `/new` pages): read them behind a timeout and treat an
  unexpected shape as "no data", never as zero.
- **`dono_campo`:** up to 10 excerpts per week pasted by the owner, `url_status=0`, literal excerpt ≥ 40 characters.
- **Recording:** `INSERT ... ON CONFLICT(hash) DO NOTHING` (never `INSERT OR IGNORE`, which also swallows CHECK
  violations). The signal is **new** if the insert recorded 1 row; any other `IntegrityError` is a collection error. For `url_status=200`,
  `payload_json` holds `{"sha256": <hash of the response body>, "date": <the response Date header>}` and the
  `trecho_literal` must be a substring of that body (the database refuses a 200 signal without `payload_json`). Hash =
  `sha256(fonte|id_externo)`; without an external id, `sha256(fonte|url normalizada|200 primeiros caracteres)`.

**Failures:**

| Situation | What to do |
|---|---|
| 5xx or timeout | 3 attempts, waiting 2 s, 8 s and 30 s |
| 429 or 403 | stop the source until the next run |
| 1st run that still fails after the attempts | `degradada` (`falhas_seguidas` + 1) |
| 3 consecutive failures or key field missing | `quebrada`, warn the owner |
| `degradada` source responds 200 | back to `ok`, `falhas_seguidas` = 0 |
| `quebrada` by transient failures (5xx, timeout, 429, 403) | retested once a week (Sunday); 200 with the key field → `ok` |
| `quebrada` by a missing key field | back only through a CHANGELOG fix approved by the owner |
| Fortnite Data API returns `null` | fewer than 5 unique players in the interval: insert no `metricas` row (absence = no data); in `concorrente_snapshots` record NULL, never 0 |

### 4.2 Signal types (value of `sinais.tipo`)

| Finding | `tipo` |
|---|---|
| A game with measured traction in a platform list (Steam most played/top sellers, Roblox top-trending, Fortnite top islands, portal "new & hot") | `hit_plataforma` |
| A loop proven on one platform and **absent or weak** on another (mobile → PC/web, PC → web, Roblox → Steam) | `arbitragem` |
| A genre tag whose cohort is healthy (4.5) | `tag_coorte` |
| A jam game in the top 10% of its jam by **Enjoyment** rank (rank ≤ 0.1 × entries) on the jam's results page, in a jam with ≥ 200 entries (`itch_jams_past` → `itch_jam_results`) | `jam_mecanica` |
| A repeated complaint in reviews of a hit (used to **formulate** the twist, never to choose the market) | `reclamacao` |
| A rising trend (only amplifies; see 4.4) | `tendencia` |
| A rival game registered for an idea | `concorrente` |
| Platform rule or feature change (payout, SDK, discovery, new program) | `plataforma` |
| New regulation that changes design or monetization | `regulacao` |
| Third-party revenue estimate or anecdote (hypothesis only; **never counts**) | `outro` |

**Where ideas come from, in priority order** (record `fonte_ideia`):
1. `arbitragem` + structural twist (Vampire Survivors took the loop of a mobile game, Magic Survival, to PC; Suika
   spread from a Chinese browser game to Switch and then everywhere);
2. `tag_genero`: a proven mid-size genre by cohort statistics + twist;
3. `jam_itch`: a jam or itch mechanic with engagement (Buckshot Roulette, Peak);
4. `tendencia`: only for a web or Roblox micro-game whose MVP fits `tendencia_mvp_dias_max` days at the owner's pace (4.4);
5. `reclamacao`: a hit's weakness as the twist (combined with 1–3, never alone);
6. `exploracao`: quota (5.1).

### 4.3 Choosing the day's sources and stopping

- **Choice:** 70% of the day's sources by yield (`q_rendimento_fontes`), 30% by rotation; in the first 4 weeks,
  equal rotation. Σ `cota_min` ≤ `trava_buscas` − searches of the fixed tasks.
- **Search:** each HTTP request counts 1.
- **Stop:** when the chosen sources meet the quota **and** `saturacao_consultas_sem_novidade` consecutive queries
  bring no new signal → `motivo_parada='saturou'`. Caps: `trava_minutos` → `teto_tempo`; `trava_buscas` →
  `teto_buscas`; error → `erro`. If `q_runs_trava` > 3, propose an adjustment in the CHANGELOG.

### 4.4 Trends (trend-jacking is a trap for 8–10 h/week)

Viral hits have a half-life of months: Grow a Garden went from 21.3M peak CCU to ~15k
`[bench:meia_vida_tendencia/roblox_grow_a_garden]`, and Steam games named after a hype (suika, brainrot, backrooms) had a median
of 200–700 copies, 60–70% under 1,000 and only 4–20% over 10,000 `[bench:clones_hype_mediana/steam_titulo_suika]`.

- **What is a trend (one definition, in the database as `v_tendencia_detectada`):** a game released **less than 120
  days ago** (`concorrentes.lancado_em`, normalized to ISO `AAAA-MM-DD` before recording — Steam returns "Oct 20, 2022";
  the database refuses other formats) **and popular** in a snapshot of the last 30 days: in a popularity list
  (`rank_lista` = `most-played`, `top-sellers`, `top-trending`, `hot` or `featured` — **not** `new`, which lists every
  recent game) or with `reviews_total` ≥ `tendencia_reviews_min`, `ccu` ≥ `tendencia_ccu_min`, `plays` ≥
  `tendencia_plays_min`, `ratings_count` ≥ `tendencia_ratings_min`, `installs_min` ≥ `tendencia_installs_min` or
  `favoritos` ≥ `tendencia_favoritos_min` (so a new mobile hit counts too; a portal hit only with an owner-pasted number, see 14). On Roblox/UEFN `plays`
  and `favoritos` are lifetime totals and never count: there only `ccu`, a popularity list or `top-trending` do. Every linked competitor that shows up in a ranking source gets a snapshot with that
  `rank_lista` in the same collection. Excluded: itch jam entries (`loja='itch'`, they feed `jam_mecanica`) and the owner's own
  games (`concorrentes.proprio_ideia_id`, set for ports and graduations). An evergreen game whose CCU jumps with a sale
  is **not** a trend. Only the **reference** link counts (the X of the twist; the database refuses a rival whose name
  appears in the twist: `referencia_no_twist`, except a rival whose name is part of the reference's name, e.g. the
  predecessor "Hades" of "Hades II"). A rival that is a live hype is a scored risk (−2 Channel on `score` only, 9.2; it never counts toward the Channel
  minimum), not a lock — so listing the strongest close rival is never punished.
  Register the leader in `tendencias` (the database refuses a test while a linked detected leader has no row:
  `tendencia_nao_registrada`; `q_checklist.tendencias_nao_registradas` shows the same); snapshot it daily.
- **One expiry date:** every trend guard stops 120 days after the trend's start: the release (`lancado_em`) or, on
  Roblox/UEFN — where hits often peak months after release —
  the first popular snapshot, for games released in the last 365 days, and only when the rise was observed (a non-popular snapshot of that game
  before its first popular one, or a `top-trending` snapshot — that list itself ranks the week's relative DAU rise;
  `v_tendencia_viva`). A Roblox/UEFN game first seen already popular by another list or
  floor, and released more than 120 days ago, is an ordinary reference: no trend rules, no `janela_fechada` death. After the 120 days every
  leader is an ordinary reference.
- **Close the trend** (`status='fechada'` and `fechada_em`=today, in the same UPDATE; the database already treats an
  open trend past its window as closed, and `q_checklist.tendencias_abertas_vencidas` flags it) when `q_tendencia_meia_vida` shows `atual` < 50% of `pico`, or
  `tendencia_janela_semanas` weeks after `detectada_em` (`clones_8sem` is informative only).
- An idea with `fonte_ideia='tendencia'` is only valid (checked at test entry; a stage that already passed is not undone
  when the trend later closes or expires) with an open trend, `plataforma='web'` (on the CrazyGames path, `exclusividade='crazygames_agregadores'`: W1 + W2 +
  Poki's Final Review do not fit the trend window) or `roblox`, and
  `horas_estimadas` ≤ `horas_semana_dono_min` × `tendencia_mvp_dias_max` ÷ 7 (the database refuses a test without an
  open trend on the reference, `tendencia_sem_janela_aberta`, or outside those limits).
  If the refusal is only because the reference is not a live trend for the database (outside `v_tendencia_viva`: older
  than its window, first seen popular off `top-trending`, or `lancado_em_incerto=1`), it is an ordinary reference: while
  the idea is still `candidata`, `pre_teste` or `congelada` (a frozen port that comes back after the guards stopped), set `fonte_ideia` to its real source (the database allows it only while no reference is a live trend) (`arbitragem`, `tag_genero`, …) and go on — no
  death. The mirror case: a reference that becomes a registered live trend after the idea entered the queue
  (`candidata`, `pre_teste`, `congelada`) — e.g. a portal hype the owner's numbers revealed — turns `fonte_ideia` into
  'tendencia' (the database allows it while that trend is registered), and the trend limits apply from there.
  Otherwise (a registered trend that closed, or hours/platform outside the limits), by platform (not by opinion): on the hype's own platform (Steam→steam, portals/web→web,
  App Store/Play→mobile, Roblox, UEFN) it is a trend clone: if its trend closed before it ever had a test →
  `arquivada` (`arquivamento='operacional'`, the same as `q_tendencia_fechada_fila`, which runs daily before any
  entry); otherwise, on web or Roblox → `morta` (`janela_fechada`), `reabrir_se`='nova tendência aberta no mesmo
  gênero' (the database refuses freezing such a clone: `clone_de_hype_morre`); on Steam, mobile or UEFN, where a trend
  idea is not allowed, the only block is the leader's age → `congelada` until the trend's start + 121 days; a port of the hit to **another**
  platform (arbitrage) → `congelada` with `data_reativacao` = the trend's start + 121 days (release, or the first popular snapshot
  on Roblox/UEFN), when the guards stop (10.1 freeze row).
- A trend clone also needs a measurable difference (twist with Z, 6.3). Name, art or theme of the hype is not one.
- **By data, not by label:** an idea whose reference is a registered leader that is still < 120 days old is a trend
  idea, whatever `fonte_ideia` says. The database refuses it in a test unless
  `fonte_ideia='tendencia'`, and refuses any test while that trend is `fechada`.
- **Trend closing during a test:** the running experiment ends normally and its result stands, but an `estender`
  becomes `resultado='inconclusiva_amostra_parcial'` and the idea goes to `arquivada` (`arquivamento='operacional'`) with `reabrir_se`='nova
  tendência aberta no mesmo gênero' (no iteration on a closed window, and no serious death for a test that never fell
  below its kill line). "During" means `tendencias.fechada_em` falls between the experiment's `inicio` and `fim`. A `validada` or
  `em_construcao` idea goes on. A stage that **passed** after the trend closed is still a passed test (players
  approved it, measured with paid or portal traffic, not the wave): the idea stays `validada`, its `fonte_ideia` goes
  back to the real source once no reference is a live trend, and the owner gets a pending item (build or archive) —
  never an automatic archive; an `em_construcao` idea → a pending item to the owner (freeze with `congelada` or continue).

### 4.5 Genre cohorts (`tag_coortes`)

Source `gamalytic_list` (free list endpoint; the per-game endpoint is paid and forbidden here). **Read every page**
(`page=0…pages−1`): the list is sorted by estimated revenue, so a partial read is a biased sample and counts as no
data. Year = `firstReleaseDate` (first release, Early Access included). For a tag and a year: launches, median of
estimated copies, share ≥ 10k and share ≥ 100k. Estimates are models, not sales: label them as such. Copies of the
current year are not comparable with past years (young games have not sold yet); only its launch count is.

- Refresh the tags of active ideas and `tags_iniciais` so that none is older than 35 days, a few tags per run in
  rotation (`fontes.cursor` of `gamalytic_list` = last tag done). Cohort pages have their own cap,
  `trava_paginas_coorte` per run, outside `trava_buscas`; a tag that does not fit waits for the next run (large tags span
  many pages). A new idea's tag without a fresh cohort goes first.
- **Healthy cohort:** the latest full year has median ≥ 1,000 copies **or** share ≥ 10k ≥ 10%, **and** the launches
  of the current year, annualized when ≥ 6 months have passed, are not more than 3× those of two years earlier.
  Measured on 2026-10-26 (all 705 rows): Bullet Heaven 2025 = 120 launches, median 2,318 copies — healthy by copies —
  but 2026 already had 388 launches by October (~466 annualized vs 72 in 2024, 6.5×), whose median so far is 100
  `[bench:coorte_bullet_heaven/steam_2026_parcial]`. That is what saturation looks like: the launch count moves first.
- Co-op tags sell more per game (VGI: median 38k vs 5k lifetime units in a filtered sample `[bench:coop_mediana_unidades/steam_coop]`) but most co-op games
  have no players at all (6.4): use it as a relative bonus, never as an absolute target.

### 4.6 Control columns

| Column | How to fill |
|---|---|
| `fontes.cursor` | highest id, date or page already collected; update in the same transaction as the inserts |
| `fontes.falhas_seguidas` / `ultimo_ok_em` | +1 on each failure; reset and `datetime('now')` on each 200 |
| `runs.taxa_novidade` | `sinais_novos / buscas` (NULL if searches = 0) |
| `concorrente_snapshots.pais` | `global` unless the source is per country |
| `concorrente_snapshots` columns | whatever the source returns (`ccu`, `ccu_pico_14d`, `reviews_total`, `reviews_positivas_pct`, `copias_estimadas`, `plays`, `minutos_por_jogador`, `favoritos`, `ratings_count`, `rating_avg`, `installs_min`, `preco`, `versao_data`, `rank_pos`); NULL only when there is no data |
| `concorrente_snapshots.rank_lista` | `''` for the competitor snapshot; `top-trending`, `most-played`, `new` etc. for a list position |
| `ideias.atualizada_em` | only changes in the state-transition UPDATE (10.1) |
| `horas.tipo` | `validacao` (prototype and iterations), `marketing` (clips, posts, pages), `construcao` (`em_construcao`), `manutencao` (`lancada`) |
| `gastos.categoria` | `anuncio` (with `experimento_id` and `ideia_id`), `plataforma` (fees, no `ideia_id` required), `ferramenta`, `outro` |
| `receita_snapshots` | one row per idea, month and platform (`data`=`AAAA-MM-01`; queries sum the platforms): `receita_bruta_usd`, `receita_liquida_usd` (via `lib.liquido_exterior` / `lib.liquido_steam`), `plays`, `copias`; `fonte` = `poki`, `crazygames`, `steam`, `roblox`, `epic`, `itch`, `appstore`, `play`, `publisher` |

Fixed numbers written in this text are design assumptions: they only change through the CHANGELOG.

---

## 5. Elimination gate

**Track and family first.** With `evidencias` and **all** `ideia_concorrentes` recorded — the reference and the 2–4
rivals of 6.2 are linked now, before the family, because links added later re-check the family at test entry:
1. **Track** (`trilha`), by the core loop and the channel (not a free choice):

   | The loop… | Track |
   |---|---|
   | fits a session-based web game, runs well on a phone, and the prototype fits `prototipo_horas_max_w` | **W** (default) |
   | needs PC depth (long runs, mouse/keyboard, content > 2 h, Steam tags with demand) | **S** |
   | is a port of an own validated game, or a hybrid-casual prototype for a publisher | **M** |
   | is platform-native social play (Roblox/UEFN genres), or the reference lives there | **R** |

   The track locks once the idea leaves `candidata` (the database enforces it).
2. **Family:** link the reference and the 2–4 rivals of 6.2 first (`ideia_concorrentes.papel`; the game named in the
   twist is the `referencia`), then run `q_familia_sugerida`; if any row has 2 or more columns = 1, inherit the `familia_id` of the one
   with the most columns (tie → lowest `familia_id`; the database requires exactly that one); otherwise
   `familia_id` = the idea's own `id`. Record the chosen row in the `evidencia_ids` of the next event. Family and
   `genero_central` do not change afterwards. A newer idea never changes the family of an older one that already has a family; an older idea that waited in
   `sinal` while a newer sibling got its family joins that family (`q_familia_sugerida` lists older ideas and newer
   live ones; at test entry the family must still be the best one among older ideas or among all of them). If a test entry is refused with `familia_errada` (a link added after the
   family), archive the idea (`reabrir_se`='recriada como ideia#<nova>') and create a new idea with `reaberta_de` that
   inherits the right family (the archived one never reopens). The family is re-checked only at test entry: links
   added after that (e.g. rivals re-read for the build proposal) never block a validated idea's build approval.

**Death:** whoever hits a cut goes to `morta`, with the cut's `motivo_morte` and `reabrir_se` (10.2). A stage refuted
with `mata_destino='morta'` always uses `motivo_morte='teste_reprovado'` (a serious death, 10.2).

**FIX-FIRST:** 1 time per family (`q_fix_first_familia` = 0). The idea stays `candidata`: record only one event
`de='candidata', para='candidata', motivo='FIX-FIRST: <smallest fix>'`, without UPDATE. If the cut persists in the
next run, `morta`.

1. **Forbidden by law or platform** → `excluida_por_regra`:
   - loot box, gacha or any paid random reward in a game that minors can likely access — Brazil's ECA Digital
     (Lei 15.211/2025, art. 20, in force since 2026-03-17) applies to foreign portals accessible from Brazil;
     treat every game on every platform (Steam, Epic and itch included) as accessible by minors;
   - free text, voice or video chat between players that the game implements or extends — the platform's own
     Roblox/UEFN chat, left at its defaults, is not `chat_livre` (it is cut 11's risk); record `chat_livre=1` only for
     chat or voice the game adds or opens beyond the platform defaults (art. 21 requires parental consent by default and the 8
     safeguards of Lei 14.852 art. 16; Poki forbids chat). Emotes/emoji are fine (Poki names an emoji system as the
     alternative; predefined phrases are not covered by its docs — confirm with Poki before relying on them);
   - real-money gambling, adult content, content generated live by an LLM without a moderation plan (the sheet
     records `ai_runtime`; with `ai_runtime=1` the database treats the idea like `loot_box` until `plano_moderacao` is
     filled; gambling and adult content are judged by the agent, see 14).

   `loot_box`, `chat_livre`, `ai_runtime` and `loop_idle` have no default: the sheet must declare 0 or 1 (the database
   refuses a test with NULL).
   Record the idea truthfully (`loot_box=1` or `chat_livre=1`): the database then lets it go only to `morta` with
   `excluida_por_regra` (or stay `candidata` for a FIX-FIRST that removes the feature and sets the flag back to 0).
2. **Clone or IP** → `clone_legal`: name, art, music, characters or the "look and feel" of an existing title, or a
   brand as the advantage (Tetris v. Xio; Roblox removes infringing games in bulk; Poki and CrazyGames reject clones
   and asset flips — Poki: "AI art doesn't make a clone original"; CrazyGames QA lists "Unoriginal content (e.g.
   clones or asset flips)"). Before proposing, compare mechanic + art + name with the idea's own `referencia` and linked rivals (any platform) and with
   the top 50 of the genre on the target platform; copying a **mechanic** is allowed, copying the **expression** is not.
3. **Depends on a queue** → `depende_fila`: the fun needs strangers online at the same time (matchmaking, public
   lobbies as the only way to play). The only exception is `modo='plataforma_social'` on track R, where the platform
   supplies the players — and only if the reference is in a Roblox/Fortnite top sort in a snapshot of the last 30 days
   (its genre has live players now). Measured on 2026-10-26: of 3,720 Steam games tagged Online Co-Op, the median
   has 0 concurrent players and 87% have fewer than 100 `[bench:ccu_coop_mediana/steam_online_coop]`.
4. **Not playable alone** → `nao_jogavel_solo` (tracks W, S, M): it must be fun with one player. Exception:
   `modo='party_host'` (6.4), allowed with −2 Channel.
5. **Cosmetic twist** → `twist_cosmetico`: the twist only changes art, theme or name (6.3).
6. **No channel** → `sem_canal`: the track has no testable channel for this loop (e.g. desktop-only game on track
   W — Poki's audience is mostly mobile; a Steam genre with no cohort data; a Roblox genre absent from the sorts).
   Portal content rules also belong here: CrazyGames requires PEGI 12 (audience 13+), English localization and no
   kids-targeted content on its main site; Poki wants content safe for all ages.
7. **Scope** → `escopo_grande`: prototype estimate above the track cap (`prototipo_horas_max_*`) or full game above
   `escopo_total_horas_max`.
8. **Saturated** → `mercado_saturado`: the genre cohort fails the health rule (4.5) **and** the twist is not
   structural, or there are ≥ 3 close equivalents released in the last 12 months with the same twist.
9. **Window** → `janela_fechada` (or a freeze until the trend's start + 121 days, as defined in 4.4): trend rule (4.4).
10. **Cost** → `custo_alto`: server cost estimate above `servidor_usd_mes_max` at 1,000 CCU, or paid assets above the
    idea budget.
11. **Platform risk** → `risco_plataforma`: the core depends on an undocumented API, on a managed multiplayer backend
    without an exit path (Hathora closed its hosting on 2026-05-05; Unity Multiplay on 2026-03-31), on Roblox chat
    across ages (age checks restrict chat to similar ages), or on consoles from day 1.
12. **Empty loop** → `loop_vazio`: the payoff comes only at the end of filler (the "Cava até o Japão" pattern), i.e. the
    brief cannot show a meaningful decision or reward in the first 30 s and something new at least every 2 min.
    A payoff only at the end is always `loop_vazio` (the idea dies), whatever else it is: the payoff is the game's
    declared goal (what ends a match or a session), and it must be reachable, or partly rewarded, within 2 min —
    upgrades that only speed the way to it do not count (a "dig to X" idle clicker with an upgrade shop is still
    `loop_vazio`). `loop_idle` is a different
    thing: progress that runs without input while the brief still shows a decision or reward in the first 30 s and
    something new every 2 min. Idle/incremental/clicker loops on track W go through the CrazyGames path (the sheet
    declares `loop_idle=1` for them, whatever the genre tag, and it cannot go back to 0 once the idea left candidata; the database refuses a
    Poki W1 for `loop_idle=1` or a `genero_central` with idle, incremental or clicker: `idle_vai_para_crazygames`), because Poki's Player Fit "only measures
    playtime" (an open idle tab counts as play), while CrazyGames decides the Full Launch on its Basic Launch metrics,
    retention included. On track R the full R1 set always includes D1 (a return, which an idle tab does not inflate),
    so an idle loop there cannot pass on session length alone.

### 5.1 Exploration quota (new mechanic without a reference)

- **Limit:** `exploracao_por_mes` per month and 1 active at a time (`q_exploracao_mes`; the database enforces it).
- **Conditions:** ≥ 1 `jam_mecanica` signal (4.2) + cuts 1–12 clean (except that `referencia` may be NULL).
- **sinal → candidata:** the `jam_mecanica` signal alone is enough.
- **Desk:** (c), (d), (e), (f) without (a)/(b).
- **Path:** set `exploracao=1` and `exploracao_em=date('now')` in the same UPDATE. Track W only (the cheapest test);
  the database refuses a test for an exploration outside track W or without a linked `jam_mecanica` signal.
  Demand score = 4 with a minimum of 4. The month's quota is used only by an exploration that is still active or that
  reached `em_teste` (an exploration archived at the desk does not burn the month; the database enforces it).

---

## 6. Desk (R$0, up to 3 days, routine only)

### 6.1 Criteria

- **(a) Proven loop:** the reference has traction measured in a snapshot in the last 30 days, on any platform:
  Steam ≥ 1,000 reviews in the last 24 months, or a Roblox experience in a top sort, or a Fortnite island in the top
  of its genre, or a portal game in the category's top 50 — or an **own game** whose W1/W2/S2 hypotheses were
  `confirmada` (ports and graduation, 7.1).
- **Fields written at the desk** (before scoring): track S → `preco_alvo` (USD, between `s_preco_min_usd` and
  `s_preco_max_usd`) and `moeda_preco='USD'`; `modo` `coop_convite`/`party_host` → `tamanho_sala`; any online mode →
  `servidor_usd_mes_1000ccu`.
- **(b) Cohort:** the genre tag passes the health rule (4.5) `[coorte:tag/ano]`.
- **(c) Twist:** written as **"É X, mas Y, de modo que Z"** (6.3), with Z measurable in telemetry.
- **(d) Hook:** one sentence, visual, understandable in 3 seconds without sound, with a clipable moment, and a
  meaningful decision or reward in the first 30 s (cut 12).
- **(e) Scope and engine:** `horas_estimadas` ≤ the track cap; engine picked with the matrix (8) and justified.
- **(f) Mode:** the mode rules (6.4) hold.

**Result:** passes with (c), (d), (e), (f) **and** at least one of (a) or (b), plus the score minimums (9). Any axis
below its minimum → `arquivada` right away, with `reabrir_se` = the axis and what would raise it.
Failed with ≥ 4 evaluable criteria → `arquivada`, `reabrir_se` = the missing criterion. Fewer evaluable → stays
`candidata` with a pending item; after `candidata_pendente_dias` → `arquivada`.

### 6.2 Competitors

Bring 2 to 4 close games with link and traction (`q_tracao_concorrente.delta_30d`) and their median next to the
leader. Without a concrete, testable difference, the idea dies (`twist_cosmetico` or `mercado_saturado`).

### 6.3 Twist template

"**É X, mas Y, de modo que Z**": X = the proven loop (with `referencia`), Y = the structural change, Z = the
observable consequence. Z must name a metric that has a `limiares` row for the idea's track (otherwise the prediction
goes in the `aprendizado` as a diagnostic, not as a hypothesis) — a metric the test can read (playtime, % of plays over 3 min, D1, demo→wishlist,
or an own-telemetry metric that has a `limiares` row) **and** a number compared with the reference (e.g. "% de jogadas acima de 3 min ≥ 35%, contra ~25%
do gate"), recorded as the `previsao` of that hypothesis. Examples of structural Y: change of dimension (Megabonk = Vampire Survivors in 3D), change of platform/input, merging two proven loops (BALL x PIT, Backpack Battles), inverting the player's
role. A change of platform counts as structural only when the loop is adapted (session length, input or duration,
measurable in the Z); a straight port with new art is not. Y that is only art, theme, setting or name → cut 5.

### 6.4 Game mode and rooms (evaluated, not assumed)

The owner likes rooms (create a room; friends join by code; strangers find it in a public list; playable any time,
no queue). Evaluated against the data:

| Mode (`modo`) | When | Rule |
|---|---|---|
| `solo` / `solo_async` | **default** — best cost/risk | async layer (daily seed, ghost, leaderboard, shareable result card) is a +1 bonus |
| `coop_convite` | co-op is the twist and the solo mode is still fun | room by code/invite link; host-only or per-player purchase at US$5–10; co-op is a high-variance bet (bimodal: friendslop hits sold millions while 73% of Online Co-Op games have < 10 CCU `[bench:ccu_coop_mediana/steam_online_coop]`) |
| `party_host` | party with friends only: one host owns the game and the others join on the same screen or their own (phones, Remote Play) | −2 Channel (party games: 88% have < 10 CCU `[bench:pct_party_menos_10ccu/steam_party_game]`) |
| `plataforma_social` | only on Roblox/UEFN, where the platform supplies the players | track R only (the database refuses it on any other track); track R may also use `solo`, `solo_async` or `coop_convite` |

- **Public room list:** `lista_publica` starts at 0 (the database enforces it) and can only be switched on for a
  launched game (`lancada`) when `q_lista_publica` shows, over 14 days, `ccu_ok=1` (on more than 7 of the 14 days
  the daily peak CCU ≥ `lista_publica_ccu_mult` × `tamanho_sala` — one launch-day spike is not density) **or** `dias_salas_ok` > 7 (days whose `salas_abertas_pico` ≥
  `lista_publica_min_salas`); when `salas_abertas_pico` is measured at all, only `dias_salas_ok` decides (`ccu_ok`
  is the fallback for games without room telemetry). An empty list is worse than none.
- **Networking:** prefer P2P with a free relay — Steam Lobbies (up to 250 members `[bench:lobby_membros_max/steam]`) + Steam Networking Sockets/SDR on
  Steam (relay cost is not stated in the docs; treat "free" as practice, not contract), Poki netlib (WebRTC P2P,
  beta: pin the version and contact Poki before going live), WebRTC in the engine. Photon's free tier is 20 CCU for
  development only `[bench:ccu_gratis/photon_realtime]`. Server estimate (`servidor_usd_mes_1000ccu`): > `servidor_usd_mes_penalidade` → −2 Execution;
  > `servidor_usd_mes_max` → cut 10.
- **CrazyGames multiplayer** (requirements only to be eligible for its Multiplayer landing page): room/join via SDK
  (invite link), Instant Multiplayer (the first player lands in a new private room), CrazyGames usernames shown, chat
  that respects DisableChat and is moderated (at least a profanity filter — and here chat is cut 1 anyway).
  Multiplayer that needs a large audience may skip Basic Launch (QA decides); with a single-player part, Basic Launch
  is required.
- Real-time competitive play sensitive to latency between Brazil and the US/EU → −2 Execution.

---

## 7. Tracks and test funnel

### 7.1 Order and gates per track

| Track | Path (states and stages) | Entry condition |
|---|---|---|
| **W** web portal | `candidata` → (`pre_teste` = queue) → `em_teste` [W1, W2] → `validada` → `em_construcao` (Full Launch polish ≤ `construcao_horas_max_w`) → `lancada` [E5] | default. The CrazyGames path (`exclusividade='crazygames_agregadores'`) is chosen at the desk only for an idle/incremental loop (cut 12; `genero_central` says idle or incremental), a game whose measured `build_mb` or `tempo_gameplay_s` exceeds Poki's targets, or a trend idea (4.4); otherwise only after a Poki refusal (the database refuses the first W1 otherwise: `crazygames_direto_sem_motivo`). A build is only measured after the
prototype exists: when the owner's "ideia#N build: …" exceeds Poki's targets while the Poki W1 is still `planejado`,
close that experiment (`estado='abortado'`, `decisao='orfao'`, open hypotheses `inconclusiva_amostra_parcial`), switch
`exclusividade` to CrazyGames (the database allows it until a test has started) and pre-register the CrazyGames W1. `exclusividade` locks at the first experiment and then only switches to CrazyGames after a Poki refusal (the database enforces it) |
| **S** Steam | `candidata` → `pre_teste` [G1] → `em_teste` [S1, S2] → `validada` → `em_construcao` [S3, S4] → `lancada` [E5] | ≥ 1 own game `lancada` on track W **or** "libero a aposta Steam da ideia#N" — when an S idea passes the desk, open a pending item asking for that phrase (its queue clock is paused meanwhile); at most 1 Steam bet (database) |
| **M** mobile | `candidata` → `em_teste` [M1] → `validada` → `em_construcao` → `lancada` [E5] | `referencia` = an own game that passed W1/W2/S2 **and is `lancada`** — this alone makes the port a candidate (graduation below is for track S and other genres) (port; while the original is `validada`/`em_construcao` it holds the family slot), or a hybrid prototype for a publisher. **Never** a self-published F2P counting on organic traffic |
| **R** Roblox/UEFN | `candidata` → `em_teste` [R1] → `validada` → `em_construcao` (monetization without randomness) → `lancada` [E5] | UEFN needs the owner to be 18+ and in the Fortnite Developer Program: any real-money purchase through Epic Payments in the last 365 days, **or** spending and redeeming US$20 in Fortnite in the last 365 days |

**Portal order on track W.** Poki first: its tests are free, repeatable and fast, and publishing the game on any
other web portal first turns a Poki exclusive deal into, at most, a one-time flat fee
(developers.poki.com/guide/revenue-deal-types). The CrazyGames path (non-exclusive, Basic Launch) is used only under
the condition of the table above or after a Poki refusal. Steam and mobile stay free in both cases. That aggregators
(GameDistribution etc.) are non-exclusive is a hypothesis until their agreement is read.

**Graduation.** A `lancada` web game that holds ≥ `graduacao_receita_min_usd`/month for `graduacao_meses` consecutive
months, or whose W1 mean playtime was ≥ 10 min, may spawn a **new** idea on track S or M (`fonte_ideia='arbitragem'`,
`referencia`='ideia#<id>'). Register the own game in `concorrentes` (its portal/store id) with
`proprio_ideia_id` = the id of the own game's idea and a first snapshot, and link the new idea to it in
`ideia_concorrentes`; the new idea goes `sinal → candidata` by this rule alone (the 2-platform rule does not apply) and meets desk criterion (a); it needs no collected signal in `evidencias` (the own game's measured data is the evidence; the database exempts an idea whose reference is an own game). Portal
plays do **not** become wishlists: the new idea goes through G1/S1 or M1 like any other.

### 7.2 Stages

| Stage | Track / state | `tipo` | How | Criterion (thresholds in `limiares`) |
|---|---|---|---|---|
| **G1 Hook clip** | S; `pre_teste` | `clip_hook` | A 15–30 s vertical clip of the mock or prototype (≤ 5 h of work) posted **by the owner** on 1–2 channels (Shorts/TikTok + 1 genre community, respecting its rules) with a UTM link to the prototype's itch.io page. | `clique_por_view` (taxa). `mata` → `arquivada` (one post is noisy evidence, not a death) |
| **W1 Portal playtest** | W; `em_teste` | `portal_teste` | Prototype ≤ `prototipo_horas_max_w` h, build ≤ `poki_build_mb_max` MB initial / `poki_total_mb_max` MB total and ≤ `tempo_gameplay_s_max` s to gameplay (CrazyGames: ≤ `cg_build_mb_max_mobile` MB for the mobile home). **Poki path:** watch 10 playtest recordings, then the Player Fit test (500 plays, ~5 h, up to 2 per day). **CrazyGames path:** Basic Launch (ends at 7 days + 500 plays, or at 21 days; no ads). | Poki (`poki_player_fit`): `minutos_por_jogador` (media) and `pct_jogadas_3min` (taxa) — Poki's own gate to advance is a mean over 3 min **and** ≥ 25% of plays over 3 min. CrazyGames (`crazygames_basic`): `aceite_plataforma` (the Full Launch invitation; its published figures — 10+ min, D1 10–15%, 80%+ conversion — describe successful titles, not a cut, so they are recorded as diagnostics only) |
| **W2 Poki Web Fit + review** | W (Poki path); `em_teste` | `portal_webfit` | Web Fit (~10,000 players on real category pages, 3–7 days — Poki's docs say 3–5 on one page and ~7 on another; CTR, time on page and C2P each scored 0–5 against the category, 3 = at or above average), then Final Review. | `webfit_notas_ok` (contagem of the 3 scores ≥ 3) and `aceite_plataforma` |
| **S1 Coming Soon page** | S; `em_teste` | `pagina_steam` | Steam page with capsule, 30 s trailer showing the hook, and the prototype shown in it. **Organic only**, no paid traffic. Steam Direct fee US$100 `[bench:steam_direct_taxa/steam]` = platform budget. The search JSON gives only name and logo: take the appid from the logo URL and drop demos/soundtracks before counting launches. | `wishlists_14d` (contagem; Zukowski bands from 278 games, updated 2026-09-14: 0–20 / 21–200 / 201–1,000 / 1,000+) |
| **S2 Demo / Playtest** | S; `em_teste` | `demo_playtest` | Free demo (separate page) or Steam Playtest (free; a separate child app with no reviews of its own; sign-ups live on the main page, where players can still wishlist; the docs describe no built-in playtime metrics, so ship own telemetry). | `demo_conversao` (taxa = demo wishlists ÷ demo players; `[bench:demo_conversao_mediana/steam_nextfest_2026_02]` and `…/steam_nextfest_2026_06`; self-selected). The source says the ratio "isn't a predictor of success", so a refusal only **archives** |
| **M1 Mobile test** | M; `em_teste` | `publisher_teste` or `cpi_teste` | **Publisher first:** submit to a publisher that pays the test (a refusal → one more publisher; a 2nd refusal kills) (Azur Games says so on its official page; re-check before submitting — publishers change, e.g. Supersonic was sold to Tripledot on 2026-08-04). **Own test (Android only):** one Meta ad set, 3–6 video creatives of 15–30 s, ≤ `orc_m1_brl`; daily budget ≥ 7.2 × expected CPI (Meta: 50 events in 7 days `[bench:meta_eventos_aprendizado/meta_ads]`). iOS paid tests are forbidden at this budget. A new personal Play account needs 12 testers for 14 days first `[bench:google_play_testers/conta_pessoal_pos_2023_11_13]`. | publisher: `aceite_plataforma`; own: `cpi_usd` (teto) and `d1` (taxa). The own test has **no iteration** (its budget buys one sample): an `estender` closes as `inconclusiva_amostra_parcial` and the idea goes to `arquivada` (`arquivamento='resultado'`, `reabrir_se`='publisher test') |
| **R1 Platform MVP** | R; `em_teste` | `roblox_mvp` | Roblox: 1 core loop in ≤ `prototipo_horas_max_r` h (Luau via Rojo), Maturity & Compliance questionnaire filled, then Ads Manager with the **New Players** audience up to `orc_r1_brl` (card payments need 18+). UEFN: publish the island; Discover tests new islands for up to 2 weeks; read `retention` (d1), `average-minutes-per-player` and `unique-players` (n) from the Fortnite Data API. | Roblox: `d1` (taxa) and `pct_sessoes_10min` (taxa; Creator Rewards pay per Active Spender who plays 10+ min). UEFN: `d1` (taxa) and `minutos_por_jogador` (media; Discover's bounce line is often 5 min) |
| **S3 Next Fest** | S; `em_construcao` | `next_fest` | Once per game, demo required, page public, game not released. Enter only with ≥ `s_wl_next_fest_min` wishlists. Next window: register by 2027-01-10; demo build and page submitted for review by 2027-01-18 (Press Preview) or at the latest by 2027-02-01; fest 2027-02-22 to 03-01. | **No `decidir`.** Record wishlists gained vs. the bracket median `[bench:nextfest_ganho_mediana/pre_0_999]` (322), `…/pre_1000_9999` (1,006), `…/pre_10000_99999` (5,215), `…/pre_100000_mais` (12,882) in `decisao` |
| **S4 Launch** | S; `em_construcao` → `lancada` | `lancamento_steam` | Launch with ≥ `s_wl_lancar` wishlists; if the page is 6 months old with fewer, launch at the minimum price and move on (`s_wl_lancar` 5,000 is below the ~8k P30 that the Personal Calendar seems to need `[bench:personal_calendar_p30/steam_2026_06]`). Price `s_preco_min_usd`–`s_preco_max_usd`; content ≥ `s_conteudo_min_h` h (refunds: 14 days and < 2 h played). | **No `decidir`.** Record week-1 copies vs. `lib.steam_projecao` in `decisao` |
| **E5 Post-launch** | all; `lancada` | `pos_lancamento` | Reads `receita_snapshots`. | **No `decidir`.** `q_e5_escada` (last closed month, all platforms summed): `congelar` → `congelada` (no more hours; the game stays live); `arquivar` (D120 below `e5_d120_min_usd` and not above the month before) → `arquivada`. Graduation: `q_graduacao` |

### 7.3 Milestones (`limiares.marco_inicio`)

Before the milestone the experiment stays `planejado` and the deadline does not run.

| `marco_inicio` | Signal that it occurred |
|---|---|
| `clipe_publicado` | owner reading with `views` > 0 |
| `teste_iniciado` | the owner informs that the portal/publisher test started (Poki Player Fit, Web Fit, publisher test) |
| `basic_launch_no_ar` | the owner informs the CrazyGames Basic Launch is live |
| `pagina_publica` | the owner informs the Coming Soon page is public |
| `demo_publica` | the owner informs the demo or Playtest is public |
| `anuncio_aprovado` | 1st `custo_brl` > 0 |
| `ilha_publicada` | 1st non-null Fortnite Data API value for the island |
| `fest_inicio` / `lancamento` | the fest's first day / owner event `em_construcao→lancada` |

### 7.4 Metrics, pre-registration and decision

**One hypothesis per criterion metric**, all linked to the same experiment. The stage (`q_etapa_status`):
**passes** when all hypotheses pass; **is refuted** when any is refuted → `limiares.mata_destino`; **inconclusive**
when any is inconclusive and none refuted → `sem_amostra_destino`; **continues** while one is open.

**Criterion metric → calculation** (totals from `q_metricas_experimento`):

| Criterion | `tipo_criterio` | events | n |
|---|---|---|---|
| `clique_por_view` | taxa | cliques | views |
| `minutos_por_jogador` | media | playtime_total_s ÷ 60 | the same D used to rebuild playtime (0.1): jogadas (Poki, mean per play) or jogadores_novos; UEFN: the Data API only returns daily series (`day|hour|minute`), so `jogadores_novos` = Σ daily `unique-players` over the 7-day window (**player-days**, not unique players; `n_min` 500 is in player-days) |
| `pct_jogadas_3min` | taxa | jogadas_3min | jogadas |
| `aceite_plataforma` | contagem | aceite_plataforma | decisao_plataforma (n_min 1: no decision yet = wait) |
| `webfit_notas_ok` | contagem | webfit_notas_ok (0–3) | 1 once the Web Fit review is recorded, 0 before (Poki's review gives scores, not a player count) |
| `wishlists_14d` | contagem | wishlists × 14 ÷ n (normalized to 14 days; the 9.2 projection uses this 14-day velocity) | days covered by the latest reading (reading date − `inicio`), not calendar days: decide only on a reading dated ≥ `inicio` + 14. **Extension:** events = cumulative wishlists × 28 ÷ days covered (the same velocity normalization, over 28 days), against `s1_passa_estendido`, decided only on a reading dated ≥ `inicio` + 28 (`n_min` stays 14 in the extension, so the lib does not check the 28 days: call `decidir` only from that reading on) |
| `demo_conversao` | taxa | demo_wishlists | demo_jogadores |
| `cpi_usd` | teto | custo_brl ÷ `cambio_usd_brl` | installs |
| `d1` | taxa | jogadores_d1 | jogadores_novos (M1: installs; UEFN: the same player-day total, with `jogadores_d1 = round(Σ(retention.d1_dia × unique_dia))`, a weighted mean; minutes likewise Σ(avg_min_dia × unique_dia) ÷ Σ unique_dia) |
| `pct_sessoes_10min` | taxa | sessoes_10min | sessoes |

**Reachable sample (paid stages M1 own test and R1):** before the idea enters `em_teste` (it waits in `pre_teste`), `n = lib.n_atingivel(orcamento,
cambio_usd_brl, custo_por_unidade_usd)` with the cost per install/new player measured in the first 48 h (or the
owner's estimate before that). If n < `n_min`, do not start: open a pending item with the budget that would buy
`n_min`. Measured in the first 48 h below it → stop spending and record `sem_amostra`.

**Pre-registration:** before the test, **copy** from the current version of `limiares` (exact segment; otherwise
`*`) to `hipoteses`: `segmento`, metrica, tipo_criterio, thresholds, n_min, eventos_min, prazo_dias and `limiar_versao`
(the database refuses a copy that differs from the latest version of that row: `pre_registro_diverge_do_limiar`).
Copy **every** row of the segment that matches the idea's platform and path (W1 Poki: both metrics; R1 Roblox: both;
M1 own test: CPI and D1); a stage only passes with that full set, on its own platform (`hipoteses_incompletas`). Record
the `previsao` in the metric's unit, `orcamento_max_brl` and the experiment's `utm_sources`. Changing a threshold
after seeing data is forbidden: the database refuses a hypothesis on an experiment that already has metrics
(`hipotese_depois_dos_dados`). `preco_alvo` locks once a test starts (database).

**Decision:** `lib.decidir(tipo, eventos, n, limiar_passa, limiar_mata, n_min, eventos_min, estendida, prazo_esgotado,
passa_estendido)`. Record `n_observado`, `eventos_observados` and `valor_observado` in the same UPDATE as `resultado` (the
database checks: a hypothesis is born open — inserting one already decided is refused, `decisao_so_por_update`;
`confirmada`/`refutada` need all three values and `metricas` rows, `decisao_sem_dado`; `confirmada` needs the value at
or beyond the pass line and a first-round `refutada` a value short of it, `decisao_incoerente`; a hypothesis belongs to
its experiment's stage, `hipotese_de_outra_etapa`). Stages read from an API over a fixed window (UEFN R1: the 7 days
of the Fortnite Data API) decide only on a reading that covers `inicio` + `prazo_dias`; before that every result other
than `aguardar` is treated as `aguardar`. `prazo_esgotado` comes from `q_hipoteses_abertas`, **or** is true when the platform reports the
test as finished (Poki Player Fit/Web Fit, CrazyGames Basic Launch end, publisher verdict). For
`aceite_plataforma`, a recorded `decisao_plataforma` (accepted or refused) always means `prazo_esgotado=True`. For
stages read by the owner, decide only on a reading dated ≥ `inicio` + `prazo_dias` (or the platform's end); while it is
missing, wait and ask for it, and treat the deadline as over only `leitura_carencia_dias` later.

| Result | What to do |
|---|---|
| `aguardar` | keep collecting |
| `estender` | On a closed trend, see 4.4 (inconclusive + archived). **Portal/platform tests (W1, W2, R1, M1 publisher; the M1 own test never iterates: an `estender` there closes as `inconclusiva_amostra_parcial` → `arquivada`, `resultado`, `reabrir_se`='teste de publisher'):** one iteration of ≤ `iteracao_horas_max` h changing **one** variable (thumbnail, onboarding, first 30 s, build size), then a **new experiment** of the same stage with hypotheses copied with `estendida=1`; close the old experiment's hypotheses as `inconclusiva_amostra_parcial` (aprendizado='iterado → exp#<novo>'), `estado='encerrado'`, `decisao='iterado'`, **without** applying a destination. For R1 (paid) the new experiment's `orcamento_max_brl` = `teto_gasto_ideia_brl` − `q_gasto_ideia`; if `lib.n_atingivel(that budget, cambio_usd_brl, cost per player measured in the 1st test)` < `n_min`, record `sem_amostra` instead of iterating (a test known to end short is not run). Every extended count passes `passa_estendido` explicitly to `decidir` (`limiar_passa` for fixed-scale counts, `s1_passa_estendido` for S1); the lib refuses to guess. **G1, S1, S2:** keep the same experiment, `estendida=1`, `extensao_motivo='meio'` (S1 with one page/capsule change; S1 then requires `passa_estendido=[config:s1_passa_estendido]` cumulative). Fixed-scale counts (`aceite_plataforma`, `webfit_notas_ok`) always use `passa_estendido=limiar_passa`. Do not change `n_min` or `prazo_dias`: the lib and `q_hipoteses_abertas` already double them. |
| `passa` | `resultado='confirmada'`; when the stage passes, open the experiment of the next stage of the track right away; if it was the last stage, run the advocate and the desk with fresh snapshots and move `em_teste → validada` in the same run (the idea's own confirmed stages now meet criterion (a) and Demand keeps its grade — the database checks the Demand minimum only at test entry; a refreshed desk that hits a cut of section 5 other than Demand → `arquivada`, `arquivamento='resultado'`) — except G1: its S1 is pre-registered when the idea moves `pre_teste → em_teste` (Sunday) |
| `mata` | `resultado='refutada'`; apply `mata_destino` (`morta` → `motivo_morte='teste_reprovado'`; `arquivada` → with `reabrir_se`). **W1 Poki:** `mata_destino='arquivada'` when refuted without an iteration (`estendida=0`; a first onboarding failure is not a verdict on the genre); refuted again after the iteration → the CrazyGames fallback below (once); only then `morta` (`teste_reprovado`). **W2 on the Poki path**: and W1 Poki after its iteration: if the idea has never run W1 `crazygames_basic`, set `exclusividade='crazygames_agregadores'` and open that W1 experiment (idea stays `em_teste`); only a CrazyGames refusal kills it (the database refuses archiving a refuted stage whose destination is death) |
| `sem_amostra` | `resultado='inconclusiva_sem_trafego'` (n < `n_min` at the deadline), then `sem_amostra_destino` (`arquivada` with `reabrir_se` and `arquivamento='operacional'`, or `congelada`). An experiment with only inconclusive hypotheses never hides an earlier refutation: a CrazyGames fallback that ends without a reading keeps the Poki refusal → `morta` (`teste_reprovado`). `extensao_motivo='sem_amostra'` is not used in this routine |

**When deciding:** record `n_observado`, `eventos_observados`, `valor_observado`, `ic_inf`/`ic_sup` (rates:
`lib.wilson`; others NULL), `fechada_em=datetime('now')` (the database requires it in that format) and the
`aprendizado`. `valor_observado` is in the threshold's unit: `eventos ÷ n` for `taxa`, the mean for `media`/`teto`,
the events themselves for `contagem` (`wishlists_14d`: the 14-day velocity, or the 28-day cumulative on the
extension). When `q_etapa_status.abertas=0`: `UPDATE experimentos
SET estado='encerrado', fim=date('now'), decisao=<stage result>` — `passa`, `mata` or `sem_amostra` (the other values
are `iterado`, `orfao`, `planejado_vencido` and `abortado`; only the first three count as a concluded test). A stage decided by one hypothesis closes the others
as `inconclusiva_amostra_parcial` (aprendizado='etapa decidida por outra hipótese'). **Cancelling a test** only through
an owner message. First process every reading of the run and decide (7.4) each open hypothesis that has data — a
refutation applies its `mata_destino` and the cancel stops there. Then close the rest as `inconclusiva_amostra_parcial`,
set the experiment's `decisao='abortado'` (an aborted experiment never hides an earlier refutation), idea →
`arquivada` with `reabrir_se` and `arquivamento='operacional'` — or `'resultado'` when the experiment already had
metrics (the database enforces both: `decidir_antes_de_sair_do_teste`, `cancelamento_com_dados`), then `estado='abortado'` (the database refuses aborting with an open
hypothesis). If the cancelled experiment was the CrazyGames fallback of a Poki refusal, the refusal stands: `morta`
(`teste_reprovado`), as in `q_planejados_vencidos` (the database refuses the archive).

**Diagnostics** (record in `aprendizado`, never decide with them): Poki C2P (target 65%+; Unity builds typically
60–65%) and Web Fit diagnosis (low CTR → thumbnail; good CTR with low C2P → build size/load; converts but leaves
early → thumbnail promises too much or early difficulty wall); CrazyGames playtime, D1 and conversion vs. their
"successful titles" figures; Steam page visit→wishlist; demo median playtime.

**Signal weights:** platform acceptance 10; wishlist 3; play over 3 min 2; click 1; like, comment or upvote 0.

---

## 8. Engine and language, per idea

The engine is chosen **per idea** from what the idea needs, in any language; record `engine` and
`engine_justificativa` (the database refuses `em_construcao` without them) and the measured `build_mb` and
`tempo_gameplay_s` of the test build.

| The idea needs… | Engine |
|---|---|
| web portal test, 2D, short sessions, phone support (**default for W**) | **Phaser 4 + TypeScript** (Poki measured an empty "Phaser" project at ~290 KB `[bench:engine_vazio_phaser_kb/web]`, version not stated; all code is text). Pin the version and give the coding agent the v4 docs: most public code and model training is Phaser 3, whose API differs. Poki's official plugin is for Phaser 3: with Phaser 4 integrate the HTML5 SDK by hand (`gameLoadingFinished`, `gameplayStart` on the first input, `gameplayStop` on every interruption) and validate it with the Poki Inspector in the first 4 h of the prototype |
| light 3D in the browser | Three.js (~151 KB) or PlayCanvas (~300 KB), same Poki measurement (`nota` of `[bench:engine_vazio_phaser_kb/web]`) |
| Steam, 2D or 3D, with content, Steam lobbies/P2P or Workshop (**default for S**) | **Godot 4.7 + GDScript** (MIT; text `.tscn` scenes an agent can edit; GodotSteam active, v4.23.2 on 2026-10-20). Web export: GDScript only (C# does not export to web), single-thread by default (threads need COOP/COEP headers, which portals rarely allow); ~10 MB compressed base, so it fails Poki's 5 MB target but fits CrazyGames |
| one codebase for web + native mobile | Defold (free, no royalties; empty web ~1 MB) |
| Roblox | Luau via Rojo (text + Git) |
| UEFN | Verse (no alternative) |

**Avoid:** Unity for web builds (~11 MB empty, disabled on iOS at CrazyGames, C2P 60–65% at Poki); engines whose
logic or scenes are not text the agent can edit (Construct event sheets) or with a pre-1.0 API (Bevy 0.x);
GameMaker (US$99.99 to sell, little public code); LÖVE for web (no official web export); Electron + steamworks.js as
a default (last npm release 0.4.0 on 2024-08-06, last commit 2025-09-07: plan B only, after a 4 h spike). **Consoles are out of scope** until a
game has traction: Defold and Unity export to them, but platform approval, devkits and NDAs are months of work.

**Switching engines** happens only for a hard, binary requirement the current engine cannot meet (closed platform,
build size, Steam lobbies/Workshop, console) — never by preference, and never during a test. Prove the gap with a
spike of at most 4 h; estimate the rewrite as ~100% of the hours already in the base **plus a new validation cycle**
(a new build invalidates the playtime and retention already measured). Record each critical library's last release
date; more than 12 months without a release is a risk that requires a spike.

---

## 9. Devil's advocate and score

### 9.1 Devil's advocate (before `em_teste`, `validada` and the build proposal)

- Run in a new subtask that receives only the sheet and the links (no subtask → `adv/<ideia>.md`, answered in a
  separate section, ignoring the run's reasoning).
- Ask: "3 motivos verificáveis para matar esta ideia, cada um com URL". Each answer needs a signal that
  **contradicts the objection's premise**.
- Give the advocate every linked rival in `v_tendencia_detectada` as a mandatory objection: "is this hype the loop
  the idea copies?" If the answer is yes, the idea named the wrong reference: archive it (`arquivamento='operacional'`,
  `reabrir_se`='recriada como ideia#<nova>', as in a `familia_errada` recreation) and recreate it with the hype as `referencia`, where the trend
  rules (4.4) apply. Also mandatory: "does the expression (art, name, look) differ from the reference beyond an
  AI-art swap?" — a no is cut 2.
- Record the literal output. **Kills** (`advogado_do_diabo`) only an objection that meets a section 5 cut with
  evidence and has no answer with a `[sinal#…]` or `[bench:…]` collected after the sheet. The others become listed risks.
- Record `ideias.advogado_em = datetime('now')` after each run of the advocate: the database refuses `em_teste`
  without it and `validada` without a run **after** the idea entered `em_teste`.

### 9.2 Score

**Scale:** only 0, 4, 7 and 10. Record in `score_json` the anchor text and the evidence of each axis; `score` = the
sum of the 5 axes after adjustments (max 50). Format: scalar keys at the root for the grades plus
`<eixo>_ancora` / `<eixo>_evidencia` text keys, e.g. `{"demanda":7,"demanda_ancora":"(a) …","demanda_evidencia":"[sinal#12]",…}`.
`score_json` must have the keys `demanda`, `twist`, `canal`,
`execucao`, `economia` (the database checks them). A **negative** adjustment rounds **down** to the nearest of
0/4/7/10 (10 − 2 = 8 → 7; 7 − 2 = 5 → 4); a **positive** one moves the axis **one step up** (4 → 7, 7 → 10).

| Axis | 10 | 7 | 4 | 0 | Minimum |
|---|---|---|---|---|---|
| **Demand** | (a) and (b) of 6.1 | (a) or (b) | jam/itch signal only (exploration) | none | 7 (exploration: 4) |
| **Twist** | structural Y + measurable Z + clipable moment | structural Y + measurable Z | Y partly cosmetic | cosmetic (cut 5) | 7 |
| **Channel** | ideal fit for the track (W: phone-first, ≤ 5 MB, fun in the first 30 s; S: tag with active creators; R: genre in a top sort) | fits | fits with a penalty | none | 7 |
| **Execution** | ≤ 2/3 of the track cap, systemic/numeric core (puzzle, deckbuilder, sim, roguelite of decisions — where AI speeds code most) | ≤ track cap | above the cap after FIX-FIRST, or core built on game feel / fine control (precision platformer, fighting) | unfeasible | 7 |
| **Economics** | projected net R$/h ≥ 2 × `meta_rs_hora_ano2` | ≥ `meta_rs_hora_ano1` | ≥ half of `meta_rs_hora_ano1` | below | 4 |

**Economics projection** (always `lib`, always with the premise marked):
All projections are in USD: multiply the net by `[config:cambio_usd_brl]` before dividing by hours, to compare with
the R$/h goals.
- W: `lib.web_receita_mes([config:plays_cauda_mes_premissa], [config:usd_por_mil_plays_premissa])` × 12 → net via
  `lib.liquido_exterior` → × câmbio → ÷ (`horas_estimadas` + `construcao_horas_max_w`). Poki pays 50/50 on its own
  traffic (100% on traffic the dev brings), CrazyGames does not publish its share: the premise already embeds it.
  Because the premise is a constant, W Economics only varies with hours and does **not** discriminate between ideas
  until 15 replaces the premise with measured revenue; say so in the sheet.
- S: wishlists = min(`s_wl_lancar`, 14-day velocity of S1 × `[config:s1_fator_anual]`) once S1 exists, else `s_wl_lancar`,
  where the velocity is always wishlists × 14 ÷ days covered (also for an extended S1);
  `lib.steam_projecao(wishlists, preco_alvo)` year-1 center × price × (1 − `[config:steam_desconto_medio_premissa]`) →
  `lib.liquido_steam(bruto, [config:steam_us_share_premissa], aliquota_ir, [config:steam_reembolso_premissa],
  compensa_eua)` → × câmbio; × `fator_arte_ia_steam` if `ai_arte_visivel=1` (72% of failed AI-labeled games used AI
  visuals `[bench:pct_fracassos_ia_arte_visivel/steam_2025]`, and Steam requires disclosing them — this factor is the only AI-art penalty);
  ÷ (`horas_estimadas` + `construcao_horas_max_s`). The US-share premise is 1.0 because Valve's tax FAQ says that, without a
  treaty, it withholds 30% "of your revenue share payment", while another answer says the withholding is the "US
  Share" × the rate; replace it with the measured US Share of the first own report.
- R: Economics = 4 until an own Roblox/UEFN game has revenue. The only public figure,
  `[bench:devex_mediana/roblox]`, is the median **among those who cash out** (survivors) and would give every R idea
  a 10.
- M: with a publisher's terms, the net per player through `lib.liquido_usd` (price, store cut, withholding); the own
  test's CPI and D1 alone have no LTV formula, so Economics = 4 until an own statement exists. Roblox statements in
  Robux go through `lib.roblox_usd` and then `lib.liquido_exterior`.

**Adjustments** (result limited to 0–10; `score_json` keeps the axis grades before adjustments and `score` sums the
adjusted axes; a positive adjustment does not count toward a minimum, a negative one does — except the live-hype rival
−2, which only lowers `score`, so naming the strongest close rival never blocks an idea; the database applies the
`party_host` and server −2 to the minimum by itself, while the latency −2 is the agent's: an Execution grade of 7 with
that penalty fails the minimum, so archive the idea before the test):

| Adjustment | Axis |
|---|---|
| +1 async layer or shareable result card (the "Wordle square") | Twist |
| +1 co-op by invite that stays fun solo | Channel |
| −2 `party_host` | Channel |
| −2 a rival that is a live hype (`v_tendencia_detectada`) | Channel |
| −2 server above `servidor_usd_mes_penalidade` (co-op by invite over P2P/Steam Lobbies is not penalized here) | Execution |
| −2 latency-sensitive competitive play across BR↔US/EU | Execution |
| −1 paid game finished in < 2 h (refund rule) | Economics |

**Tie-break:** 1) track W; 2) higher Twist; 3) fewer hours; 4) genre with an own game already `lancada` (reuse code
and learning).

**Gates on measured play, not virality:** this routine gates for measured play and money rather than for
shareability alone. Here a solo game with a shareable artifact is fine (it gets +1), because the test, not the rubric,
decides.

---

## 10. States, transitions, family and reopening

### 10.1 Transitions (the database accepts only these; any state can go to `morta`)

| From → To | Condition | Actor |
|---|---|---|
| sinal → candidata | 3.2 item 4 | routine |
| sinal → arquivada | `q_sinais_parados` (operational) | routine |
| candidata → pre_teste | desk + score + slot (W/M/R: queue for an `em_teste` slot; S: to run G1, with the entry condition of 7.1) | routine |
| candidata → em_teste | desk + score + advocate + slot (W, M, R) | routine (Sunday) |
| candidata / pre_teste → em_construcao | "construo sem teste de comportamento a ideia#N" + approval + slot + engine + the sheet fields (`trilha`, `plataforma`, `modo`, `hook`, `twist`, `horas_estimadas`, and the declared flags `loot_box`/`chat_livre`/`ai_runtime`/`loop_idle` (0 or 1, no default) with cut 1 applied; the database checks them) | **owner** |
| candidata → arquivada | desk failed or pending beyond the deadline | routine |
| pre_teste → em_teste | queue (W/M/R) or G1 passed (S) + advocate + slot | routine (Sunday) |
| candidata / pre_teste / em_teste → congelada | trend or seasonal window outside its time, with `data_reativacao` | routine |
| pre_teste / em_teste → arquivada | `sem_amostra`/archiving `mata_destino`, `q_planejados_vencidos`, `q_pre_teste_parado` or cancel | routine |
| em_teste → validada | the track's stages passed (W: W1 CrazyGames, or W1+W2 Poki; S: S1+S2; M: M1; R: R1) + advocate + desk redone with fresh snapshots | routine |
| validada → em_construcao | the owner approves the proposal (12.3) + slot + engine | **owner** |
| validada → arquivada | the owner rejects (`resultado`, `reabrir_se`='dono pede: reabro a ideia#N' — never a pending item already resolved, which the routine would read as met), the reference changed (a close equivalent shipped; `resultado`), or `q_validada_parada` (`operacional`) | routine |
| em_construcao → lancada | the owner informs the launch (the database opens the E5 experiment that holds the live game's metrics) | **owner** |
| em_construcao → congelada | build stopped by the owner | routine, quoting the owner |
| lancada → congelada / arquivada | E5 | routine |
| congelada → lancada | "descongelo a ideia#N" (a frozen live game) | **owner** |
| congelada → em_construcao | "descongelo a ideia#N" (a build frozen by the owner resumes) | **owner** |
| congelada → candidata | `data_reativacao` reached (once per idea) | routine |
| congelada → arquivada | `congelada_max_meses` without reactivation | routine |
| morta / arquivada → candidata | reopening (10.2) | routine or **owner** |
| any → morta | gate, test, advocate | routine |

**How to record (one transaction):**
```sql
BEGIN;
INSERT INTO ideia_eventos(ideia_id, de, para, motivo, evidencia_ids, ator, prova_dono, run_id) VALUES (...);
UPDATE ideias SET estado=?, motivo_morte=?, reabrir_se=?, arquivamento=?, atualizada_em=datetime('now') WHERE id=?;
COMMIT;
```
If it fails, `ROLLBACK`. `arquivamento` is required when entering `arquivada` (`resultado` or `operacional`, 10.2). On
reopening, `motivo_morte=NULL` (the database clears `score`, `score_json`, `advogado_em` and `arquivamento` on every
return to `candidata`, so the desk is redone). Do not fill `em`. The event must be the idea's **last** one.

**The database refuses:** a transition outside the table; a missing event or one that is not the last; full
portfolio, occupied family or a 2nd Steam bet; `em_construcao`/`lancada` without `ator='dono'` with `prova_dono`;
`em_construcao` without `engine` and `engine_justificativa`; `pre_teste`/`em_teste`/`validada` without the sheet
(`trilha`, `plataforma`, `modo`, `hook`, `twist`, `horas_estimadas`, `score_json`), and `em_teste`/`validada` without
`advogado_em`; a sheet with an axis that is not a number on the 0/4/7/10 scale (JSON `null` included) or below its minimum, hours above the track's prototype
cap, a track whose platform does not match (W web, S steam, M mobile, R roblox/uefn), or `fonte_ideia='exploracao'`
without `exploracao=1` (and vice versa); a test while a linked competitor has no `lancado_em`, without a linked `referencia` (except exploration), without a
positive evidence row, or with an unnamed rival; a track-S test without an
own launched web game or "libero a aposta Steam da ideia#N" (recorded as an event `de=para=<current state>`,
`motivo='LIBERACAO_STEAM: …'`, `ator='dono'`, `prova_dono`, and its pending item closed); any change to a decided hypothesis and any UPDATE or
DELETE in `ideia_eventos`; deleting an `ideia_concorrentes`/`evidencias` link after `sinal`; `validada` without the track's
stages passed in the current cycle (W: W1, plus W2 on the Poki path; S: S1 and S2; M: M1; R: R1); a refuted
stage whose destination is death leaving `em_teste` for `arquivada` or `congelada` (the latest experiment with decided
hypotheses counts); a 3rd CrazyGames W1 experiment; an owner transition without the exact phrase of 0.1
("construo sem teste de comportamento a ideia#N", "aprovo a construção da ideia#N", "ideia#N lançada em …",
"descongelo a ideia#N"); a stage result `passa` without hypotheses or with one not `confirmada`; any change to the
pre-registered fields of a hypothesis; a 2nd FIX-FIRST in a family; an exploration outside track W or without a
`jam_mecanica` signal; a trend idea outside web/roblox or above the trend hour cap; an `advogado_em` in the future; an idea born outside `sinal` or with a family; a track or `fonte_ideia` change once the idea has ever left `candidata`; a `reabrir_se` 'recriada como ideia#' outside an operational archive
(even after a reopening), or a `genero_central` change after the gate; reopening without `REABERTA:`, to a state other
than `candidata`, of a serious death without the owner, or a 2nd reopening by the routine; family entries without the
`REABERTA:` of 10.2; a family other than the one with the most columns in `q_familia_sugerida` (≥ 2; tie → lowest
`familia_id`); an idea with `loot_box=1` or `chat_livre=1` going anywhere but `morta` (`excluida_por_regra`); a test for
an idea linked to a trend unless `fonte_ideia='tendencia'`, or while that trend is `fechada`; a `loot_box`/`chat_livre`
flag going back to 0 without a FIX-FIRST event; an owner event whose proof lacks `ideia#<id>`; a death with a mild
motive after a refuted hypothesis (must be `teste_reprovado`); a second `congelada → candidata`; `lista_publica=1` at
creation or before `lancada`; `preco_alvo` change after a test; a signal with `url_status=200` without `payload_json`.

### 10.2 Family and reopening

- **Family:** `q_familia_sugerida` measures same `genero_central`, a competitor/reference in common and ≥ 50% shared
  signals. With 2 of the 3, the idea inherits the family. Renaming or re-theming does not reset the graveyard.
- **`reabrir_se`:** ONE verifiable condition when killing for `sem_canal`, `mercado_saturado`, `depende_fila`,
  `escopo_grande`, `custo_alto`, `risco_plataforma`, `janela_fechada` or `loop_vazio`, and on every `arquivada`.
- **Evaluation:** `q_reabrir_candidatas` on the 1st Sunday of the month and when a `plataforma` or `regulacao` signal
  cites the reference.
- **Condition true:** event `motivo='REABERTA: <condition> [sinal#]'` → `candidata`. The routine reopens at most once
  per idea (all cuts run from scratch on reopening). When the condition is true again for an idea the routine
  already reopened (`q_reabrir_candidatas.ja_reaberta_pela_rotina=1`), open a pending item asking for "reabro a
  ideia#N" instead (the database refuses a 2nd routine reopening). A reopened idea starts a new cycle: the CrazyGames
  test and its iteration, and the portal choice (`exclusividade`), count again from the reopening. An exploration (`exploracao=1`) that died or was archived reopens
  only through the owner (`q_reabrir_candidatas` leaves it out; the database refuses the routine).
- **Serious deaths** (`teste_reprovado`, `advogado_do_diabo`, `clone_legal`, `excluida_por_regra`): only the owner
  reopens, with `ator='dono'` and `prova_dono`. A sibling in the same family enters a test only after an owner event `ator='dono', motivo='REABERTA: ...'`,
  `prova_dono` with "reabro a ideia#N", recorded **in the run the phrase arrives** (as the next entry event, or, when the
  entry happens later — e.g. Sunday — as an event `de=para=<current state>` of that run) after the sibling died; that one event covers the next entry too (`pre_teste` → `em_teste`), in a serious or a light
  graveyard alike. The owner's build override
  ("construo sem teste de comportamento a ideia#N", `candidata`/`pre_teste` → `em_construcao`) in such a family is the
  same event with `motivo='REABERTA: …'` and the override phrase as its proof.
  An idea already `validada` when the sibling died is not blocked from its build approval, and only **older**
  siblings count: a newer idea that dies never blocks an older one (the database enforces both).
- **Operational archives are not a graveyard:** archiving by a queue or deadline query (`q_candidatas_paradas`
  `sem_vaga`, `sem_mesa` — missing data is not a failure — and `bloqueada_cemiterio`, `q_sinais_parados`, `q_pre_teste_parado`, `q_planejados_vencidos`, `q_validada_parada`, `q_em_teste_sem_experimento`,
  `familia_errada` or wrong-reference recreation (9.1), `q_tendencia_fechada_planejados`, `q_congeladas_vencidas` `arquivar`, a test cancelled by
  the owner, a `sem_amostra` stage with no refuted hypothesis — no traffic is not a verdict) sets
  `arquivamento='operacional'`; a refuted stage, a desk failure, the owner's rejection of a build or a changed
  reference sets `arquivamento='resultado'`. The database requires one of the two on every archive. The database ignores operational archives in the family rule.
- **Sibling of a non-serious dead or archived idea** (any other `motivo_morte`, or `arquivada` by a result): the entry event of
  `candidata`/`pre_teste` → `pre_teste`/`em_teste`/`em_construcao` must carry `motivo='REABERTA: <the sibling's
  reabrir_se, now met> [sinal#]'`. The routine may do this for at most 1 idea per family; after that, only the owner.
  The database enforces both rules (`familia_no_cemiterio`).
- On reopening, record `reaberta_de` when the new idea replaces a dead one.

---

## 11. Outputs, checklist and prerequisites

### 11.1 Daily chat message (only if something changed)

```
[rotina-jogos] AAAA-MM-DD · <N> mudanças · <N> pendências
1) Mudanças (≤ 10 linhas):  ideia#id: de→para — motivo [evidências]
2) Pendências do dono (numeradas, com R$, horas e prazo)
3) Checklist: OK | itens que falharam
4) Run: buscas · sinais_novos · taxa_novidade · motivo_parada
```
Attach `digests/AAAA-MM-DD.md`, generated from the database. **Immediate alerts** (separate message): a decided
hypothesis; `q_orcamento_experimentos.alerta_80`; a `quebrada` source; a platform acceptance; a launch; an E5 step;
a reopening; a trend closing on an idea in test.

### 11.2 End-of-run checklist

Passes if `q_checklist` returns 0 in all columns, every provenance mark resolves, no contrary signal is omitted, every
`prova_dono` passes `lib.prova_existe`, `integrity_check` = ok and the backup was written. Record `runs.checklist_ok`
and `checklist_json`; **never** type this value.

### 11.3 Owner prerequisites (sent in the bootstrap)

1. **Files and routines:** copy the folder to `/workspace/rotina-jogos/` and create routines (A) and (B).
2. **Portal accounts:** Poki developer account; CrazyGames developer account (payouts via Tipalti,
   `[bench:crazygames_payout_minimo/crazygames]`, NET 60 in the contract and ~10 days in practice
   `[bench:crazygames_payout_prazo_dias/crazygames]`); itch.io account. Ask Poki, before the first deal, whether it pays a
   Brazilian individual (its payouts page only says wire or PayPal).
3. **Marginal income tax (IR) rate** (`aliquota_ir_marginal`; the seed value 27.5% is a conservative premise) and,
   when there is revenue, the accountant's answer about crediting US withholding (`compensa_eua`).
4. **Optional keys** (in `secrets/`): YouTube Data API key, Twitch app (client credentials).
5. **Telemetry for Steam demos/Playtests** (optional, free tier of any product analytics): events `sessao_inicio`,
   `sessao_fim` (with duration) and a day-1 return flag.
6. **Platform fees** (separate budget, one by one, each approved): Steam Direct US$100 per app (only when S1 is
   approved, `[bench:steam_direct_taxa/steam]`); Google Play `[bench:custo_conta/google_play]`; Apple
   `[bench:custo_conta/apple_developer]` (only for a validated port); Roblox Ads card (18+).

Without what it needs, the experiment stays `planejado` and becomes a pending item.

---

## 12. Sunday, Friday and build proposal

### 12.1 Sunday (after the daily)

1. Shortlist of the 5 best; devil's advocate on the best one.
2. **Portfolio:** fill `em_teste` from the queue (write the prototype brief, 12.4, and pre-register) — the 2nd `em_teste`
   slot is filled only when the other test's experiment is already `rodando` (one prototype at a time) — except a
   trend idea, which may take the 2nd slot at once (its window is 6 weeks; it goes first in the queue) and `q_tendencia_fechada_fila` archives a **clone** (the hype's own
   platform) whose trend closed before it got a test (`arquivamento='operacional'`); a port to another platform
   follows 4.4 instead (`congelada` until the guards stop); propose
   building for `validada` ideas; apply deaths, freezes and archivings.
3. **Expenses:** with 2 ideas in paid stages and the month's cap tight (`q_gasto_mes`), ask whether the 2nd waits.
4. **Maintenance:** if `manutencao` hours in the week > 3 h or there are > 3 `lancada` with hours, propose freezing
   the one with the lowest R$/h (`q_rs_por_hora_ideia`) before opening a new build.
5. **"O que aprendemos":** closed hypotheses; `q_erro_previsao` (if you always err upward, reduce the next
   predictions in the same proportion); yield per source; `q_meta_portfolio` against the goal (1).

### 12.2 Friday 18:00

For each idea that changed during the week: gate, scores with anchor, economics, competitors with their median,
stage with confidence interval, spend (`q_gasto_ideia`), hours (`q_horas_prototipo`) and next step. Also: the
portfolio with cutoff dates, the request for the real hours of the week, the pending items, `q_meta_portfolio`, and
the warning that the bot may pause the routine if the owner goes too long without answering.

### 12.3 Build proposal

Only for a `validada` idea with a slot.
- **Evidence:** the stage results with confidence interval and links, re-read on the day of the proposal.
- **Scope:** ≤ `construcao_horas_max_<trilha>` h; only what the test proved plus what the platform requires (W: portal
  SDK with ads/rewarded, Poki `gameplayStart()` on the player's first input (not on load) and `gameplayStop()` on
  every interruption; S: demo → full game, Steam Content Survey
  including player-visible AI content; R: game passes and direct, non-random products).
- **Engine** (8) with justification; **mode** and networking (6.4); **legal checklist**: no loot box, no free chat,
  **classificação indicativa for every game, browser games included**: Portaria MJSP 1.048/2025 revoked Portaria
  502/2021 (art. 94, I; in force since 2025-11-17) and did not keep the old exemption for browser games (old art. 43
  §3). Self-rate through IARC or an authorized system (arts. 44 §3 and 45); in stores, the IARC questionnaire (art. 48).
  Before the first portal launch, ask the portal whether it already self-rates the game; otherwise the owner does.
- **E5 ladder** pre-registered.
- **Fiscal note:** revenue from abroad goes to the monthly carnê-leão in the month the money arrives, converted at
  the BCB **buying** rate of the last business day of the first half of the previous month (RIR/2018 art. 119; the
  US tax withheld uses the same rate) — the PTAX selling rate in `cambio_usd_brl` is only for projections and CPI; ask
  the bank to classify the exchange as export of services (IOF zero by Decreto 6.306 art. 15-B); US withholding (Steam, itch,
  Roblox, Epic) is credited only if the accountant confirms; above `receita_alerta_cnpj_brl`/month sustained, open a
  "consultar contador sobre PJ" pending item (whether MEI covers game development is unverified).
- **Build skills:** if available, use `game-feel`, `game-taste-2d`/`game-taste-3d` and finish with `game-polish`.
- **"O motivo mais forte pra não fazer"**.

### 12.4 Prototype brief (when the idea enters `em_teste`)

Write `briefs/ideia-<id>.md` for the owner: hook; twist "É X, mas Y, de modo que Z" and the metric that reads Z; the
30–60 s core loop; what to cut to fit `prototipo_horas_max_<trilha>` h; engine + pinned version; build budget (MB and
seconds); 3 thumbnail variants to test; the clipable moment; the pre-registered thresholds and the reading template
(0.1). On track W: phone support, no text dependence (or English), `gameplayStart()` at the first input.

---

## 13. Anchor examples

**Rejection (real owner cases): "Cava até o Japão" and "Arquibancada".** Solo click-to-descend with the payoff only at
the end, and a concept already free elsewhere: cut 12 (`loop_vazio`) and cut 5 (the "twist" is the theme).

**Sheet that passes (illustrative):**
- **Idea:** "É [roguelite de dados de um hit Steam com 20k reviews], mas no celular e em partidas de 4 minutos, de
  modo que a % de jogadas acima de 3 min chegue a ≥ 35% (contra os ~25% do gate)" — reference with snapshot, tag
  cohort healthy `[coorte:…]`.
- **Track:** W (Poki path). **Mode:** `solo_async` (daily seed + result card). **Engine:** Phaser 4 (2D, phone-first,
  ~2 MB build).
- **Test:** W1 Poki Player Fit: `minutos_por_jogador` and `pct_jogadas_3min` pre-registered.
- **Economics:** premise tail 30k plays/month × US$1.5/1,000 → US$45/month → `lib.liquido_exterior(45*12, 0.275)` =
  US$391.5/year × `cambio_usd_brl` ÷ 45 h (≈ R$45/h at R$5.2/US$ → Economics 7; non-discriminating premise, 9.2).
- **Strongest reason not to do it:** the hit's own dev may ship a mobile version.

---

## 14. Known limits

- Portal dashboards have no public API: every portal reading depends on the owner pasting it.
- CrazyGames' revenue share is not public; GameDistribution's terms could not be read; Poki's deal numbers are
  "indicative" until the contract.
- The thresholds outside the platforms' own gates are heuristics (`origem='heuristica'`); calibration is mandatory.
- Steam coefficients come from devs who share data (survivor-biased upward), and the year-1 center mixes a mean
  (Zukowski) with a median multiplier (GameDiscoverCo); the 2025 Steam median was US$318 (Gamalytic estimate)
  `[bench:receita_bruta_mediana/steam_2025]`.
- Success through polish or editorial featuring is not detectable before building.
- The co-op part of a `coop_convite` idea is not a pre-registered hypothesis (portals expose no invite metric): on
  track W the tests measure the solo game, which must stand on its own; invites and group sessions are diagnostics.
  On track S, S1/S2 measure interest (wishlists, demo conversion), not whether one player keeps playing alone: a
  queue-dependent multiplayer labeled `coop_convite` rests on cut 3 (judgment) and the demo playtime diagnostic.
- Steam-native ideas: every Steam signal source has `plataforma='steam'`, so a Steam-only genre (no itch, portal,
  mobile, Roblox, Twitch or YouTube signal) never meets the 2-platform candidacy rule and ages out of `sinal`; the
  `tag_genero` source (4.2) works only for genres seen on more than one platform.
- Portal trends: the sources in `fontes` only list `new` games for Poki and CrazyGames, so a portal hype becomes a
  detected trend only when the owner pastes its plays or favorites; otherwise its clones meet only the cosmetic-twist
  judgment and the portals' own QA.
- G1 cannot kill on its first round: the Wilson upper bound of 0 clicks in 2,000 views is 0.0019 > `limiar_mata`
  0.001, so a dead hook is extended once and dies on the extension.
- A **cosmetic twist** (a skin, an AI-art restyle of a hype) is a judgment the database cannot check: it rests on the
  6.3 template, the devil's advocate and the portals' own rejection of clones. The same holds for the reference/rival
  label: an agent that names an old game as the reference of a hype clone (the hype only as a rival) escapes the trend
  rules; the advocate's mandatory hype objection (9.1) is the only check, and the test itself still decides.
- Real-money gambling and adult content (cut 1) have no flag: they rest on the agent's judgment.
- `lib` constants (Valve cut, US withholding, DevEx rate, store cuts) are fixed in code: if reverification changes
  one, propose editing `lib.py` + `test_lib.py` in the CHANGELOG.

---

## 15. Calibration and evolution (1st Sunday of the month)

- **Thresholds:** every 5 closed hypotheses of the same stage and metric, recalculate; record a new version in
  `limiares` (`origem='calibrado'`) without deleting the previous one. A calibration only tightens (higher pass/kill
  lines; lower for `teto`), and a platform gate (`origem='benchmark'`) is never recalibrated (the database refuses
  both: `limiar_recalibracao_proibida`); loosening goes to the owner as a CHANGELOG proposal.
- **Benchmarks:** reverify the `benchmarks_vigentes` older than `benchmarks_reverificar_dias`. Same value:
  `UPDATE benchmarks SET verificado_em=date('now') WHERE id=?`. Different value: new row.
- **Cohorts:** refresh `tag_coortes` (4.5). **Reopening:** run `q_reabrir_candidatas`.
- **Portal revenue premise:** replace `usd_por_mil_plays_premissa` with the measured US$ per 1,000 plays once 2 games
  have 2 months of revenue.
- **Prompt:** propose changes in `CHANGELOG.md` (yield per source, prediction error, cap stops, calibrated thresholds,
  reopenings). **Do not apply.**
