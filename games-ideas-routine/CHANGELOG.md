# CHANGELOG

The routine proposes changes here (1st Sunday of the month). The owner approves and applies them.

## v35 — 2026-10-27 (review round 33: 5 findings, all fixed)

- A reference that becomes a registered live trend after the queue entry turns the label into 'tendencia' (no stuck
  idea in pre_teste); a trend idea may take the 2nd test slot at once.
- Measured open rooms outrank CCU for the public list (CCU is only the fallback).
- A sibling the routine already reopened is not listed as blocked (own reopening not counted as the family quota);
  `trg_validada_exige_etapas` anchors its cycle on a real reopening; overrun items match by `ideia_id` or text.

## v34 — 2026-10-27 (review round 32: 8 findings, all fixed)

- An owner same-state event (REABERTA, LIBERACAO_STEAM) is not a new entry in candidata nor a new cycle: the entry
  anchor needs a state change and the cycle anchor a reopening from morta/arquivada.
- A same-platform clone on Steam/mobile/UEFN (no trend ideas there) freezes until the leader's 121st day instead of
  dying; the arbitrage gap counts only off the proof platforms.
- Text: cut 2 compares with the idea's own reference and rivals; a platform change is structural only with an adapted
  loop; mandatory advocate objection on AI-art swaps; trend-extension archives are operational; Roblox plays are not
  popularity. Sources: iTunes genre filter does not work (filter by `primaryGenreName`), SteamSpy unknown tags return
  a default list (both checked live).

## v33 — 2026-10-27 (review round 31: 9 findings, all fixed)

- Roblox/UEFN lifetime visits and favorites are no popularity floor (a modest game is no longer a trend leader).
- An `arbitragem` signal documents a gap, not traction: counted apart (`plataformas_arbitragem`), with an explicit
  arbitrage candidacy rule.
- A validated/building/launched trend idea gets its real source back once no reference is a live trend.
- Public list counts exactly 14 dates; `sem_amostra` is not a concluded test (`testes_sem_amostra`); UEFN null days
  do not fail the reading checklist.
- Text: E5-frozen games keep their statements; the overdue weekly summary has a marker (no duplicates); the
  measured portal premise may be written to config.

## v32 — 2026-10-27 (review round 30: 10 findings, all fixed)

- A trend idea whose stage passed after the trend closed stays `validada` (pending item to the owner), never an
  automatic archive; the owner's "reabro" is recorded in the run it arrives and covers a later Sunday entry.
- The reading grace period is in `q_hipoteses_abertas` (no early `sem_amostra`); an all-null UEFN reading counts as
  "not popular" (no false block, no checklist failure).
- Text: refused owner phrases that do not fit the state become a pending item; cut 9 uses the trend's start;
  `loop_vazio` has a checkable payoff rule; `valor_observado` unit per criterion; M economics and Robux go through
  `lib`; keyless optional sources are `desligada`.

## v31 — 2026-10-27 (review round 29: 10 findings, all fixed; 1 high)

- **High:** a price-only snapshot hid a hype: a snapshot counts only with a popularity number, and a recent game on a
  store with a numeric source and no such number blocks the test (`popularidade_indeterminada`).
- The trend window is enforced by the database (an open trend past `tendencia_janela_semanas` is closed in effect;
  checklist `tendencias_abertas_vencidas`); a refuted test archives as `resultado` (no `recriada` relabel).
- A sibling blocked while in `pre_teste` reaches the owner; the owner's rejection is not reopened by the routine;
  the rival check matches whole words.
- Text: every platform is accessible by minors (cut 1); own-database counts need no mark; missed weekly snapshots
  are caught up; closed-window archives are operational.

## v30 — 2026-10-27 (review round 28: 7 findings, all fixed)

- The behavior test outranks a re-graded proxy: the Demand minimum applies only at test entry, so a refreshed desk at
  `validada` no longer archives an idea players approved.
- A trend clone whose trend closed before any test is an operational archive (same as `q_tendencia_fechada_fila`,
  now run daily before entries); only a tested clone dies `janela_fechada`.
- Overrun hours open one item per idea (an answered "continue" does not re-arm); the `bloqueada_cemiterio` label
  mirrors its filter.
- Text: source status machine (degradada → quebrada → weekly retest), default `reabrir_se`/`arquivamento` for every
  archive path, desk-written fields (`preco_alvo`, `tamanho_sala`, `servidor_usd_mes_1000ccu`).

## v29 — 2026-10-27 (review round 27: 12 findings, all fixed or recorded)

- Threat model generalized: every column is written only where the text says; the database locks the decisive ones
  (archive class, signal identity, exploration month, `ai_runtime` via FIX-FIRST, real moderation plan ≥ 80 chars).
- `referencia_no_twist` compares the rival's base name (store subtitle cut); a web trend idea must run the CrazyGames
  path; the exploration quota reads `exploracao_por_mes`.
- EUR statements (CrazyGames) convert through `cambio_eur_brl` from the new `ptax_bcb_eur` source (verified live);
  the S1 extension's forecast error is measured in its 14-day unit; prototype hours beyond 1.5× the estimate reach
  the checklist; the summary/digest are drafted before the checklist so their marks are checked.
- Known limit: Steam-native genres cannot meet the 2-platform rule. Schema comment of `loop_idle` corrected.

## v28 — 2026-10-27 (review round 26: 9 findings, all fixed or recorded; 1 high)

- **High:** a frozen arbitrage port no longer gets stuck: a `tendencia` label goes back to the real source (candidata,
  pre_teste or congelada) once no reference is a live trend.
- Blocked-sibling queries mirror the family trigger (owner REABERTA only, after the sibling's death);
  `n_atingivel` no longer floors an exact quotient to n−1; the launch phrase passed to the lib is the fixed prefix.
- A `sem_amostra` archive is operational (no traffic is not a verdict).
- Known limits recorded: portal trends need an owner-pasted number; track S does not measure solo play; G1 only kills
  on the extension. Guard tests added for portfolio, family slot, transition table, event and reopening.

## v27 — 2026-10-27 (review round 25: red-team 0; correction 6 findings, all fixed)

- Queue queries anchor REABERTA on the idea's last entry in candidata (as the family trigger): a sibling reopened long
  ago and blocked again ages out and reaches the owner.
- `q_tendencia_fechada_fila` lists clones only; ports follow 4.4 (frozen). The build override checks `loop_idle`.
- An owner phrase refused for lack of a slot is kept in a pending item and stays valid until applied.
- The suite pins every per-track prototype cap (checked with all caps at 10 h); provenance marks added; the unsourced
  Roblox Ads first-charge figure removed.

## v26 — 2026-10-27 (review round 24: 6 findings, 5 distinct, all fixed; 1 high)

- **High:** `q_tendencia_fechada_fila` now joins `v_tendencia_viva` like its sibling query: a leader past its 120 days
  no longer archives an arbitrage port that 4.4 told to wait (no archive/reopen loop).
- 4.4: a trend idea refused only because its reference is not a live trend relabels `fonte_ideia` (still candidata)
  and goes on, never `janela_fechada`.
- Docs: `s1_passa_estendido` premise 402; `dono_campo` still needs 40 characters; `ai_runtime`/`loop_idle` listed
  as required sheet flags.

## v25 — 2026-10-27 (review round 23: 8 findings, all fixed; 1 high)

- **High:** the decision oracle is enforced: a hypothesis is born open (`decisao_so_por_update`), a decision needs
  all observed values and metrics, and agrees with the pass line (`decisao_incoerente`); a hypothesis belongs to its
  experiment's stage. Test fixtures now decide through `fechar_hipotese` (the legal path).
- A payoff only at the end is always `loop_vazio`; `loop_idle` is input-free progress and locks once declared.
- Light graveyard: one owner REABERTA covers the whole entry; a trend idea goes first in the queue and
  `q_tendencia_fechada_fila` archives one whose trend closed first; UEFN decides only on the full window; the M1 own
  test never iterates; build measurements only from the owner's quoted message.

## v24 — 2026-10-27 (review round 22: 6 findings, all fixed; 1 high)

- **High:** a sibling blocked by a light graveyard (result archive, non-serious death) was stuck forever:
  `q_irmas_bloqueadas` now covers it (pending item when serious or the routine's quota is used) and
  `q_candidatas_paradas` ages it out as `bloqueada_cemiterio`.
- A trend idea never reopens: a new trend becomes a new idea linked to the new leader (no reopen/refuse loop).
- Portal dates: `lancado_em_incerto=1` only without any date (CrazyGames shows one; a `new` list sighting dates it),
  so a new portal hit is a trend again; the sheet declares `loop_idle` (idle never on Poki, whatever the tag).
- Skill description under the 1024-character limit.

## v23 — 2026-10-27 (review round 21: 12 findings, 11 fixed, 1 recorded as a known limit)

- `decidir` requires `passa_estendido` on extended counts (a silent +2 default could kill an accepted game); a
  hypothesis is decided only with observed values and metrics rows.
- Portal games without a release date get `lancado_em_incerto=1` and never become a trend; `ai_runtime` is part of the
  sheet and live LLM content needs `plano_moderacao`.
- Family: the gate's choice also passes the entry check; a family-occupied candidata ages as `sem_vaga`; siblings
  blocked by a serious death reach the owner (`q_irmas_bloqueadas`).
- Inbox layout fixed (header line + message line); R1 iterates only if the remaining budget reaches `n_min`; W1 Poki
  anchor corrected; the suite pins its own profile values. Known limit: reference/rival label of a hype clone.

## v22 — 2026-10-27 (review round 20: 9 findings, 8 fixed, 1 answered in the text)

- No light exit for a failed test: an inconclusive-only experiment (CrazyGames fallback without a reading) never hides
  the Poki refusal (spec change: r3 test inverted); open hypotheses with data are decided before freezing or
  archiving; a cancelled test with data is a result archive.
- A hype clone on the hype's own platform dies (`clone_de_hype_morre`); only a port to another platform freezes.
- A validada idea behind a build in progress opens a pending item (`pendencia_vaga`); the owner's build override works
  in a family with a graveyard; ideas archived before the gate no longer fail the family checklist.
- `prova_dono` format fixed (opening quote first); idle on track R: the R1 set already requires D1 (text only).

## v21 — 2026-10-27 (review round 19: 10 findings, all fixed)

- An older idea that waited in `sinal` joins its newer live sibling's family; 'recriada como ideia#' only on an
  operational archive (no laundering a serious death); `fonte_ideia` locks with the track.
- A rival whose name is part of the reference's (predecessor, franchise) no longer trips `referencia_no_twist`.
- `sinal → arquivada` via `q_sinais_parados` (`sinal_max_dias`); `sem_mesa` is an operational archive.
- Portal/Google Play competitors have no per-game source: not counted by the snapshot checklist, `lancado_em` from
  the oldest citing signal; snapshots use ON CONFLICT DO UPDATE.
- UEFN R1 aggregates the daily API series (player-days, weighted D1 and minutes); a closed trend never archives a build.

## v20 — 2026-10-27 (review round 18: 5 findings, all fixed)

- Curly quotes (“ ”) are accepted in `prova_dono` by the database and the queue query, like the lib; a refused phrase
  that is literally in the inbox is a malformed quote, not a reason to ask the owner again.
- CrazyGames test count and the portal lock are per cycle (`experimentos.criado_em`): a reopened idea gets them again.
- `q_reabrir_candidatas` lists ideas the routine already reopened (`ja_reaberta_pela_rotina`) so the owner is asked.
- S1 extension normalizes the cumulative count to 28 days; a refused "descongelo" (slot taken) keeps the idea frozen
  and opens a pending item.

## v19 — 2026-10-27 (review round 17: 8 findings, all fixed; 1 high)

- **High:** an owner phrase must START the quote — a negation quoted whole ("não aprovo a construção da ideia#N")
  passed both the database and `lib.prova_existe`; the database now anchors all five phrases and the lib takes `frase`.
- A stage passes only with the full hypothesis set of its `limiares` segment, on the idea's own platform/path.
- The build-based CrazyGames switch works in the text's order (no test started = no `inicio`); idle/incremental/clicker
  never take the Poki path; a port/graduation needs no collected signal.
- S1 extension keeps the first-round velocity (`s1_passa_estendido` 402); the platform's own Roblox/UEFN chat is not
  `chat_livre`; a wrong-reference recreation is an operational archive.

## v18 — 2026-10-27 (review round 16: 10 findings, 8 distinct, all fixed)

- A cancelled (`abortado`) CrazyGames fallback no longer hides the Poki refusal: the refusal stands (death).
- A build measured over Poki's targets switches to CrazyGames while the Poki W1 is still planned.
- Roblox `top-trending` counts as an observed rise (the list ranks the week's DAU rise).
- Pre-registration is checked against the latest `limiares` row (`hipoteses.segmento` added).
- `party_host` and server −2 count toward the minimum in the database; the latency −2 is applied by the agent.
- Web Fit sample = the recorded review (n_min 1); multi-line owner quotes match; a rate above 100% on a short early
  reading waits instead of raising.

## v17 — 2026-10-27 (review round 15: 17 findings, 16 fixed, 1 handled in the text)

- Owner reopening needs the exact phrase "reabro a ideia#N"; one owner REABERTA covers a sibling's whole entry
  (pre_teste → em_teste); a 2nd reopening becomes a pending item to the owner.
- A Poki refusal overcome by a passed CrazyGames stage no longer forces `teste_reprovado`; E5 waits for a missing
  platform statement instead of reading it as zero.
- New guards: forbidden flags cannot be cleared through NULL; a 200 signal needs a valid `{sha256, date}` payload;
  own games point to a launched idea, once; direct CrazyGames needs a measured reason (build, time to gameplay, idle
  genre or trend); no hypothesis after the data; calibration never loosens nor touches platform gates.
- Text: Roblox trend needs an observed rise (already-popular old games are ordinary references); trend ideas on web
  run the CrazyGames path; archive type stated per path; the advocate checks live-hype rivals (a wrong reference is
  recreated — the guard for this stays in the text); unmarked numbers removed or marked (Photon benchmark added).

## v16 — 2026-10-27 (review round 14: 9 findings, all fixed)

- Queue aging: an S idea's wait counts from the owner's Steam release; `sem_vaga` only when `pre_teste` is full (4).
- The owner's own game is never a common competitor (family rule); a Roblox/UEFN trend needs an observed rise (a
  non-popular snapshot before the first popular one).
- Live-hype rival −2 lowers `score` only (never a minimum); a refuted last stage applies `mata_destino` from both
  closing queries.
- `tendencias.fechada_em` records the closing date and defines "closing during a test"; pending items can be
  cancelled (`cancelada_em` + reason) and leave `q_pendencias_abertas`.
- Owner hours on 45 working weeks (360–450 h/year); provenance marks for the routine's own numbers.

## v15 — 2026-10-27 (review round 13: 11 findings, all fixed)

- `reaberta_de` no longer hides a dead sibling from the family (only the `recriada como ideia#` archive is excluded).
- The sheet needs numeric score axes (JSON `null` was slipping through), a linked `referencia`, a positive evidence row
  and named rivals; "construo sem teste" needs the legal flags; trend-entry checks run only at test entry.
- Public list needs a sustained CCU peak (> 7 of 14 days); state metrics are recorded once; Steam release recorded as
  an owner event; `q_construcao_longa` opens once per cap; closed-trend fallback keeps the Poki refusal; 4.2 aligned.
- Test fixtures now link a reference and an evidence row for every idea (the rule applies to all tests).

## v14 — 2026-10-27 (review round 12: 5 findings, all fixed)

- "descongelo" only returns to the state the idea froze from (`trg_descongelo_origem`).
- Roblox/UEFN trend age counts from the first popular snapshot for games < 365 days old (hits peak after 120 days);
  popularity predicate shared in `v_snapshot_popular`; `clones_8sem` no longer closes a trend.
- M1 own test: D1 `n_min` 120 (fits R$300 at the CPI pass line) and no iteration.
- Explorations reopen only through the owner (now said in the text and left out of `q_reabrir_candidatas`).

## v13 — 2026-10-27 (review round 11: 13 findings, all fixed)

- A refutation is not erased by an administrative closure (`planejado_vencido`/`orfao`/`iterado`): an unrun CrazyGames
  fallback leaves the Poki refusal standing (death); `arquivamento` is required on archive, cleared on reopening, and
  only exempts archived rows from the graveyard.
- Trend popularity also via ratings/installs/favorites (mobile and portal hits); leader expires strictly at 120 days;
  a trend idea needs an open trend on its reference; `exclusividade` locks at the first experiment.
- Steam release requested as a pending item (queue clock paused); one prototype at a time and `planejado` 70 days;
  UEFN window 7 days; owner-read stages wait for the final reading with a grace period; the last passed stage
  validates in the same run; the port rule is the M table's.

## v12 — 2026-10-27 (review round 10: 8 findings, all fixed)

- Trend rule back to the reference only, made mechanical: a game named in the twist must be the reference
  (`referencia_no_twist`), so a hype cannot be relabeled a rival; a rival that is a live hype costs −2 Channel instead
  of locking the idea (listing the strongest rival is no longer punished). `q_tendencia_fechada_planejados` respects the
  120-day expiry.
- `lib.decidir`: for counts, `n_min` now also protects passing (spec change; two inherited tests updated); extended
  S1 uses cumulative wishlists decided at `inicio` + 28.
- Operational archives (`arquivamento='operacional'`) are not a graveyard; owner phrase after a line break or bullet is
  accepted; two backups per run with seconds in the name.

## v11 — 2026-10-27 (review round 9: 14 findings, all fixed)

- Trend "popular" = a popularity list (not `new`) or reviews/CCU/plays above config floors, so a Steam hype is caught
  without a list snapshot; `lancado_em` must be ISO (Steam's "Oct 20, 2022" broke the comparison).
- Family re-checked only at test entry (not at a validated idea's build approval); replaced ideas never reopen.
- Owner phrase must start a sentence ("ainda não aprovo…" is no approval); "construo sem teste" needs the sheet; a
  launch opens the E5 experiment automatically; planned experiments of closed trends are closed
  (`q_tendencia_fechada_planejados`); M1 publisher refusal → one more publisher (limiar_mata −1); `orc_m1_brl` 300 (corrected in v14: the own test has no iteration); S projection always on the 14-day velocity; end-of-run order (backup → checklist → close → backup);
  marks for the Play/Apple fees and the CrazyGames payment term.

## v10 — 2026-10-27 (review round 8: 12 findings, all fixed)

- Trend rule redesigned on one definition (`v_tendencia_viva` / `v_tendencia_detectada`): a game released < 120 days
  ago that is also in a top list in the last 30 days; itch jam entries and own games excluded; CCU doubling dropped
  (it caught evergreen sales); any link counts; one expiry date (`lancado_em` + 120). This replaces four earlier
  patches that each opened a new edge case.
- Graveyard looks only at older siblings; scored candidates without a slot leave after `candidata_fila_dias`; the sheet
  check skips ideas frozen at the gate; a live game frozen by E5 never expires; `rs_por_hora_12m` in R$ on closed
  months; track R may use non-social modes; S1 wishlists normalized to 14 days; the "tail = a tenth" claim removed.

## v9 — 2026-10-27 (review round 7: 9 findings, all fixed)

- E5 never treats a missing statement as zero (`aguardar_extrato` + checklist `lancadas_sem_extrato`).
- Family matching only looks at older ideas (a newer idea cannot block an older validated one).
- Links have a role (`papel` referencia/rival): only the reference triggers the trend rule; a recent reference must be
  registered as a trend before any test (`tendencia_nao_registrada`).
- Owner phrases accept accented capitals; G1 → S1 is pre-registered at the Sunday move; UEFN sample = window total;
  the co-op part is a diagnostic (known limit).

## v8 — 2026-10-27 (review round 6: 10 findings, all fixed)

- An arbitrage of a recent hit that does not fit the trend rules is frozen until the hit is 120 days old (not killed
  with an unreachable reopen condition).
- `q_em_teste_sem_experimento` (+ checklist): an idea in test with no open experiment opens the next stage or is
  decided; the reachable-sample check runs before entering `em_teste`; a passed stage opens the next one.
- `q_validada_parada` opens a pending item and only archives after `validada_max_dias_arquivar` (180 days).
- Trend checklist also catches a Roblox top-trending entry; cut 3 exception only for `plataforma_social` on track R
  with a reference in a live top sort; a registered rival no longer counts as a platform (track R has its own rule).
- `q_e5_escada` and `q_graduacao` (last closed month, platforms summed, "no growth" defined); `receita_snapshots` key
  includes the platform; graduation text completed; Z must have a `limiares` row.

## v7 — 2026-10-27 (review round 5: 14 findings, all fixed)

- Threat model made explicit (top of SKILL.md): guards stop errors, rationalization and shortcuts the text allows;
  deliberate row rewriting against the text is forbidden by the text, not by SQLite.
- Guards: a stage `passa` needs confirmed hypotheses; pre-registered fields are immutable; the CrazyGames path validates
  only with a confirmed `aceite_plataforma`; FIX-FIRST once per family; exploration only on track W with a jam signal;
  trend ideas only on web/roblox within the hour cap; `advogado_em` cannot be in the future; a recreated idea does
  not match the idea it replaces; owner phrases case-insensitive; "descongelo a ideia#N" and congelada → em_construcao.
- Data: `jam_mecanica` is now objective (top 10% Enjoyment in a jam ≥ 200 entries) with two tested sources
  (`itch_jams_past`, `itch_jam_results`).
- Text: a recorded platform decision ends the test; S economics divides by prototype + build hours; idle loops go to
  CrazyGames because its Full Launch decision weighs retention.

## v6 — 2026-10-27 (review round 4: 15 findings, 14 fixed + 1 documented as a known limit)

- Guards: `validada` needs the track's stages passed in the current cycle; a refuted stage cannot escape through
  `congelada` nor through a phantom experiment (the latest experiment with decided hypotheses counts); CrazyGames runs
  at most twice per idea; trend guards look only at trends of the last 120 days and never at own games
  (`concorrentes.proprio_ideia_id`); links cannot be deleted after `sinal`; loot box/chat only die (not archive) and must
  be declared (no default); `plataforma_social` only on track R; owner transitions need the exact phrase.
- New table `pendencias` (+ `q_pendencias_abertas`): `reabrir_se`='pendencia#N resolvida' is checkable.
- Recording: `ON CONFLICT(hash) DO NOTHING` (OR IGNORE swallowed CHECK errors); metric upserts add increments and keep
  the max of daily peaks; rivals linked before the family; `familia_errada` → recreate with `reaberta_de`;
  `score_json` format with `<eixo>_ancora`; marks for the store cuts, the Steam year-1 band and the 72%; ×26 is config.
- Known limit (not fixable in the database): a cosmetic twist is a judgment (section 14).

## v5 — 2026-10-27 (review round 3: 18 findings, all fixed)

- Family: the shared genre-cohort signal no longer makes two ideas of the same genre one family (only idea-specific
  signals count); a sibling's later serious death does not block the build approval of a validated idea.
- Guards: the sheet checks the 0/4/7/10 scale, the axis minimums, the hour cap of the track and track↔platform; the
  exploration label needs the flag; linked competitors need `lancado_em`; the Steam bet needs a launched web game or
  the owner's release; decided hypotheses and the event log are immutable; a reopening clears score and advocate.
- CrazyGames fallback that ends without sample can be archived (only the latest experiment's refutation counts).
- A closed trend turns `estender` into inconclusive + archived (not a serious death); S1 decides on a reading that
  covers 14 days; S1 has its own `planejado` limit (70 days); M port requires the original `lancada`.
- Queries: platforms counted over proof signals only; doubling needs a base > 0; "no reading in 7 days" starts after
  7 days; numbers in the text now carry resolvable marks (Feb 2026 demo benchmarks added).

## v4 — 2026-10-27 (review round 2: 16 findings, all fixed)

- Guards: family re-checked at test entry (links added after the family was written count); decided hypotheses need
  `fechada_em` in datetime format; a refuted stage whose destination is death cannot be archived; a launched game
  archived by E5 is not a graveyard entry for its port.
- Trend: a game released < 120 days ago (`concorrentes.lancado_em`) counts, so a hype found at its peak is caught.
- W1 Poki refused after the iteration gets the CrazyGames fallback once (same as W2).
- R Economics = 4 until own revenue (the DevEx median is of survivors); daily peaks are not recorded as increments;
  cohort pages have their own cap with a rotation; `horas_semana_dono_min/max`; S prototype cap 50 h (50 + 250 ≤ 300);
  W2 does not count as a second concluded test; `steam_projecao` in exact integer arithmetic.

## v3 — 2026-10-27 (review round 1: 21 findings, all fixed)

- Guards: loot box/chat flag back to 0 only through FIX-FIRST; owner proof must cite `ideia#<id>`; `genero_central` in
  snake_case; death after a refuted hypothesis must be `teste_reprovado`; sheet checks the twist template, the 5 score
  keys and `ai_arte_visivel`; `validada` needs an advocate run after entering the test; reactivation once.
- Queries: W2 was treated as an orphan (the Poki path could never validate); Steam queue counts from the release of
  the bet; checklist covers `loop_vazio` and unregistered trends (a linked game that doubled CCU in 30 days).
- Text: score axis below minimum archives; positive adjustments move one step up; AI-art penalty only as the Steam
  ×0.5 factor; R economics per hour; reachable sample before paid stages; `party_host` defined once; seed.py creates the
  working folders; SteamSpy/Gamalytic count as the `steam` platform.

## v2 — 2026-10-27 (validation round 1)

A 6-agent validation (4 fact-checkers at the primary source, 1 executability simulation, 1 funnel red-team)
returned 77 findings (9 high, 34 medium, 34 low); all were confirmed and fixed, except #75 in part (a validated idea is
not archived while a build is running — that would discard proven ideas; only the Steam queue clock pauses).
Main changes:
- **Law:** Portaria MJSP 1.048/2025 revoked 502/2021 (in force since 2025-11-17): browser games now need
  classificação indicativa too (self-rating via IARC).
- **Database guards:** loot box/free chat recorded truthfully and allowed only to die; no test without the sheet and
  the devil's advocate (`advogado_em`); track locked even after a reopening; trend rule by data (linked trend leader);
  exploration quota burned only by an active idea or one that reached a test; HTTP-200 signals need `payload_json`.
- **Funnel:** W1 Poki refusal without an iteration archives (a first onboarding is not a verdict on the genre);
  S2 demo conversion only archives (its source says it does not predict success); the CrazyGames path is chosen only
  for idle/incremental loops, oversized builds or after a Poki refusal; new cut 12 `loop_vazio`; S4 without the
  3,000 floor; Economics converted to R$ and S uses the S1 velocity; score = sum of axes, rounded down to the scale.
- **Data:** Gamalytic read on every page with `firstReleaseDate` (page 0 alone inflated the cohort 100×+); Fortnite
  metric is `average-minutes-per-player` and `unique-players` gives n; dashboard template with the same denominator
  as the mean; Roblox Ads US$300/day removed (not in the docs); UEFN program rule corrected; Next Fest 4th bracket.

## v1 — 2026-10-26

Built from two research rounds (October 2026), each with primary sources and an adversarial verifier:
monetization and goal design, Steam, web portals, mobile, Roblox/UEFN, idea sources and validation data,
promotion, AI/solo risks, game mode and rooms, "already validated" ideas, engine per idea, BR tax and law.

Key decisions taken with the owner:
- goal = portfolio with net R$/hour, not MRR; year 1 = reach the ~€100/month payout floor summed across the
  portfolio; Steam is a gated option, not a promise;
- validation only by measured behavior (portal playtests, wishlists, demo conversion, platform decisions);
- platforms: web portals, Steam, mobile, Roblox/UEFN; same architecture as `apps-ideas-routine`;
- rooms: the owner's preferred model was evaluated, not adopted as-is (section 6.4): invite rooms yes, public
  list only with measured density, solo must stay fun;
- the engine/language is chosen per idea, in any language (section 8).

### Assumptions without a source (`origem='premissa'` or `heuristica`; calibrate with own data)
- Every hour cap (prototype, iteration, build, total scope) and every weekly limit.
- Portal revenue: `plays_cauda_mes_premissa` 30k and `usd_por_mil_plays_premissa` 1.5 (one old portfolio made
  ~€1.20 per 1,000 plays).
- Kill thresholds outside the platforms' own gates: Poki < 1.5 min / < 12%; G1; M1 own test; R1 (Roblox D1 12% is
  an illustrative example in its docs); W2 Web Fit "3 scores ≥ 3".
- `s1_passa_estendido` 402 (= 2 × the S1 pass line of 201, the same velocity over 28 days; v19); `s_wl_lancar` 5,000 (below the ~8k P30 that the Personal Calendar seems to need).
- `steam_desconto_medio_premissa` 0.3 and `steam_reembolso_premissa` 0.1; `receita_alerta_cnpj_brl` (R$7,350 is the
  end of the 2026 IR reducer, used here only as a trigger to talk to an accountant).
- `steam_us_share_premissa` 1.0 and `compensa_eua=0` (conservative until the accountant confirms).
- `fator_arte_ia_steam` 0.5; server penalty/limit; public-list density rule.

### Not verifiable in this round (kept out of calculations or marked)
- CrazyGames revenue-share percentage (developer terms page renders empty); GameDistribution terms.
- Whether Poki and Tipalti pay a Brazilian individual without a company.
- Steam Datagram Relay cost (docs silent); BRL suggested price for US$9.99.
- Whether the Valve no-treaty withholding applies to the whole payment or only to the US Share (the tax FAQ
  says both); whether the carnê-leão reducer of Lei 15.270 applies; whether MEI covers game development.
- Roblox Ads audience minimums and cost per new player (R1 may end `sem_amostra` at R$300).
- Whether Poki's "predefined phrases" are acceptable as chat replacement (docs only name emoji).

### Known open points
- Portal dashboards have no public API: readings depend on the owner.
- Phaser 4 is a recent major version; most public code is Phaser 3 — pin the version and give the coding agent
  the v4 docs.
