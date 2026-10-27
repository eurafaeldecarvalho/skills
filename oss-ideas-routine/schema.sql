-- Schema of the open-source ideas routine. Dates in UTC: 'YYYY-MM-DD HH:MM:SS' (datetime('now')) or 'YYYY-MM-DD'.
-- Identifiers (tables, columns, state values) are in Portuguese on purpose; SKILL.md explains each one.
PRAGMA foreign_keys=ON;
PRAGMA user_version=1;
-- PRAGMA foreign_keys does NOT persist: run 'PRAGMA foreign_keys=ON' on every new connection.

CREATE TABLE config(chave TEXT PRIMARY KEY, valor TEXT NOT NULL,
  origem TEXT NOT NULL CHECK(origem IN('dono','premissa','medido','seed')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now')));

CREATE TABLE fontes(id INTEGER PRIMARY KEY, nome TEXT UNIQUE NOT NULL, plataforma TEXT NOT NULL, tipo TEXT NOT NULL,
  endpoint TEXT, frequencia TEXT NOT NULL CHECK(frequencia IN('diaria','semanal','mensal','manual')),
  limite TEXT, termos_nota TEXT, cursor TEXT,
  status TEXT NOT NULL DEFAULT 'ok' CHECK(status IN('ok','degradada','quebrada','desligada')),
  falhas_seguidas INTEGER NOT NULL DEFAULT 0, ultimo_ok_em TEXT);

CREATE TABLE runs(id INTEGER PRIMARY KEY,
  tipo TEXT NOT NULL CHECK(tipo IN('bootstrap','diaria','sexta')),
  iniciado_em TEXT NOT NULL DEFAULT (datetime('now')), terminado_em TEXT,
  status TEXT NOT NULL CHECK(status IN('rodando','ok','parcial','falhou')),
  buscas INTEGER NOT NULL DEFAULT 0, sinais_novos INTEGER NOT NULL DEFAULT 0,
  checklist_ok INTEGER, checklist_json TEXT, resumo_json TEXT, erro TEXT);

-- A signal is a fetched page (HTTP 200 in this run) with a literal excerpt; 'dono_campo' is an owner-attested note.
CREATE TABLE sinais(id INTEGER PRIMARY KEY, fonte_id INTEGER NOT NULL REFERENCES fontes(id),
  run_id INTEGER REFERENCES runs(id), hash TEXT NOT NULL UNIQUE, url TEXT NOT NULL,
  url_status INTEGER NOT NULL CHECK(url_status IN(200,0)),
  trecho_literal TEXT NOT NULL CHECK(length(trecho_literal) >= 40),
  -- demand types (section 4.2): issue_reacoes, issue_not_planned, repo_abandonado, pedido_ferramenta
  tipo TEXT NOT NULL CHECK(tipo IN('issue_reacoes','issue_not_planned','repo_abandonado','pedido_ferramenta',
                                   'ranking','lancamento_concorrente','termometro','dono_campo','outro')),
  reacoes INTEGER, coletado_em TEXT NOT NULL DEFAULT (datetime('now')), payload_json TEXT,
  CHECK(url_status = 0 OR (json_valid(payload_json) AND length(json_extract(payload_json,'$.sha256')) = 64
                          AND json_extract(payload_json,'$.date') IS NOT NULL)),
  CHECK(url_status = 200 OR tipo = 'dono_campo'));
CREATE TRIGGER trg_sinal_fixo BEFORE UPDATE OF fonte_id, hash, url, url_status, trecho_literal, tipo, reacoes ON sinais
BEGIN SELECT RAISE(ABORT,'sinal_imutavel'); END;

CREATE TABLE ideias(id INTEGER PRIMARY KEY, titulo TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'sinal' CHECK(estado IN('sinal','candidata','em_construcao','pronta','lancada',
                                                        'tracao','hit','arquivada','morta')),
  categoria TEXT CHECK(categoria IN('cli','lib_benchmark','skill_harness','sucessor_abandonado','alternativa_open',
      'lista_curadoria','mcp_server','self_hosted_completo','framework_agentes','prompts_vazados','build_your_own','outro')
      OR categoria IS NULL),
  gancho TEXT,                   -- what it does, one line, no AI buzzword as the hook (section 5, cut 6)
  prova_numero TEXT,             -- the proof number planned for the README top and the post title (e.g. "53% -> 99%")
  linguagem TEXT, horas_estimadas REAL, estrelas_alvo INTEGER,
  carga_h_semana REAL,           -- lib.carga_h_semana(estrelas_alvo, ...) with the config premises
  hit_rate_categoria REAL,       -- share of the category's repos created in 12 months that passed 1k stars [bench:hit_rate_*]
  hit_rate_benchmark_id INTEGER REFERENCES benchmarks(id),   -- the benchmark row the rate was copied from (same value)
  modo_baixa_manutencao INTEGER NOT NULL DEFAULT 0 CHECK(modo_baixa_manutencao IN(0,1)),
  licenca TEXT, licenca_justificativa TEXT,
  como_chega TEXT,               -- how users will find it (channels and mechanism, never a reward for stars; section 6.2)
  repo_full_name TEXT UNIQUE,    -- owner/repo once created (private while em_construcao)
  advogado_em TEXT,              -- last devil's advocate run (section 6.3)
  motivo_morte TEXT CHECK(motivo_morte IN('teste_reprovado','categoria_proibida','nicho_tomado','sem_demanda','carga',
      'advogado_do_diabo','estrelas_incentivadas','dono_desistiu','outro') OR motivo_morte IS NULL),
  reabrir_se TEXT, reaberta_de INTEGER REFERENCES ideias(id), nota TEXT,
  ciclo INTEGER NOT NULL DEFAULT 1,   -- +1 on every reopening: launches and hypotheses belong to one cycle
  criada_em TEXT NOT NULL DEFAULT (datetime('now')), atualizada_em TEXT NOT NULL DEFAULT (datetime('now')));

CREATE TABLE ideia_eventos(id INTEGER PRIMARY KEY, ideia_id INTEGER NOT NULL REFERENCES ideias(id),
  run_id INTEGER REFERENCES runs(id), de TEXT, para TEXT NOT NULL, motivo TEXT NOT NULL,
  ator TEXT NOT NULL CHECK(ator IN('rotina','dono')),
  prova_dono TEXT,   -- literal quote of the owner's message ('"<phrase>" chat AAAA-MM-DD HH:MM')
  em TEXT NOT NULL DEFAULT (datetime('now')),
  CHECK(ator = 'rotina' OR length(prova_dono) >= 10));
CREATE TRIGGER trg_evento_sem_update BEFORE UPDATE ON ideia_eventos BEGIN SELECT RAISE(ABORT,'evento_imutavel'); END;
CREATE TRIGGER trg_evento_sem_delete BEFORE DELETE ON ideia_eventos BEGIN SELECT RAISE(ABORT,'evento_imutavel'); END;

CREATE TABLE evidencias(ideia_id INTEGER NOT NULL REFERENCES ideias(id), sinal_id INTEGER NOT NULL REFERENCES sinais(id),
  polaridade INTEGER NOT NULL CHECK(polaridade IN(-1,1)), nota TEXT, PRIMARY KEY(ideia_id,sinal_id));
CREATE TRIGGER trg_evidencia_fixa BEFORE DELETE ON evidencias
WHEN (SELECT estado FROM ideias WHERE id=OLD.ideia_id) <> 'sinal'
BEGIN SELECT RAISE(ABORT,'vinculo_imutavel'); END;

-- Repos watched: competitors, successors, references and the owner's own launched repos.
CREATE TABLE repos(id INTEGER PRIMARY KEY, full_name TEXT NOT NULL UNIQUE, criado_em TEXT,
  proprio_ideia_id INTEGER REFERENCES ideias(id),
  suspeito_fake INTEGER NOT NULL DEFAULT 0 CHECK(suspeito_fake IN(0,1)),   -- lib.suspeito_fake (section 4.3)
  publico_em TEXT,   -- own repos: the day it became public (launch day for a repo built private; section 7.4, 13)
  nota TEXT);
CREATE TABLE repo_snapshots(repo_id INTEGER NOT NULL REFERENCES repos(id), data TEXT NOT NULL,
  estrelas INTEGER NOT NULL, forks INTEGER, issues_abertas INTEGER, pushed_at TEXT,
  fonte TEXT NOT NULL CHECK(fonte IN('gh_star_count','gh_search_repos','gh_trending_html')),
  PRIMARY KEY(repo_id,data));
CREATE TABLE ideia_repos(ideia_id INTEGER NOT NULL REFERENCES ideias(id), repo_id INTEGER NOT NULL REFERENCES repos(id),
  papel TEXT NOT NULL CHECK(papel IN('referencia','sucessor','rival','abandonado')),
  PRIMARY KEY(ideia_id,repo_id));

-- Launch posts: written and posted by the owner by hand (section 7.3); the routine only records them.
CREATE TABLE lancamentos(id INTEGER PRIMARY KEY, ideia_id INTEGER NOT NULL REFERENCES ideias(id),
  canal TEXT NOT NULL CHECK(canal IN('show_hn','reddit','lobsters','x','bluesky','devto','changelog_news','console_dev',
                                     'product_hunt','awesome_list','outro')),
  url TEXT NOT NULL UNIQUE, titulo TEXT NOT NULL, postado_em TEXT NOT NULL,
  pontos_72h INTEGER, comentarios_72h INTEGER, e7 INTEGER,
  prova_dono TEXT NOT NULL CHECK(length(prova_dono) >= 10),
  ciclo INTEGER);   -- set by the database: the idea's cycle when the post was recorded
CREATE TRIGGER trg_lancamento_ciclo AFTER INSERT ON lancamentos
BEGIN UPDATE lancamentos SET ciclo=(SELECT ciclo FROM ideias WHERE id=NEW.ideia_id) WHERE id=NEW.id; END;

-- Own-repo stars per day, from the official /stargazers/history (section 4.1). Never typed by hand.
CREATE TABLE estrelas_diarias(ideia_id INTEGER NOT NULL REFERENCES ideias(id), data TEXT NOT NULL,
  estrelas INTEGER NOT NULL CHECK(estrelas >= 0),
  fonte TEXT NOT NULL CHECK(fonte IN('stargazers_history')),
  suspeito INTEGER NOT NULL DEFAULT 0 CHECK(suspeito IN(0,1)),   -- a spike without a post (section 9.2); excluded from windows
  PRIMARY KEY(ideia_id,data));
CREATE TABLE traffic(ideia_id INTEGER NOT NULL REFERENCES ideias(id), data TEXT NOT NULL,
  views INTEGER NOT NULL, uniques INTEGER NOT NULL, PRIMARY KEY(ideia_id,data));

-- Launch gate L0 (section 7.2): the items and their per-idea proof.
CREATE TABLE checklist_itens(codigo TEXT PRIMARY KEY, descricao TEXT NOT NULL, obrigatorio INTEGER NOT NULL CHECK(obrigatorio IN(0,1)));
INSERT INTO checklist_itens VALUES
 ('demo_topo','image, GIF or video showing the RESULT in the first ~3,000 characters of the README',1),
 ('o_que_por_que_como','what it does, why, how to start, where to ask, who maintains it',1),
 ('licenca','SPDX license detected by the API (MIT or Apache-2.0; AGPL only with the owner''s reason)',1),
 ('topics','3 to 20 valid topics',1),
 ('descricao','repo description filled (homepage when there is a demo or docs site)',1),
 ('social_preview','custom social preview 1280x640 under 1 MB',1),
 ('quickstart','quickstart in <= 3 copy-paste commands, no sign-up',1),
 ('vs_alternativas','"vs alternatives / why not X" section',0),
 ('release','>= 1 tagged release on launch day',1),
 ('ia_e_testes','one line on how AI was used and what the owner tested; tests and CI visible',1),
 ('numero_prova','the proof number at the top (benchmark, before -> after)',1),
 ('baixa_manutencao','SECURITY.md, SUPPORT.md ("no guaranteed support"), issue templates, Discussions, open-PR limit per user',1),
 ('supply_chain','Actions pinned by full SHA, minimal permissions, no pull_request_target checkout, push protection on, trusted publishing when publishing to a package registry',1),
 ('sem_pedido_estrela','no request, reward or instruction to star (people or AI assistants) anywhere in the repo',1);
CREATE TABLE checklist(ideia_id INTEGER NOT NULL REFERENCES ideias(id), item TEXT NOT NULL REFERENCES checklist_itens(codigo),
  ok INTEGER NOT NULL CHECK(ok IN(0,1)), prova TEXT NOT NULL CHECK(length(prova) >= 5),
  verificado_em TEXT NOT NULL DEFAULT (datetime('now')), PRIMARY KEY(ideia_id,item));

CREATE TABLE benchmarks(id INTEGER PRIMARY KEY, metrica TEXT NOT NULL, segmento TEXT NOT NULL, valor REAL NOT NULL,
  unidade TEXT NOT NULL, source_url TEXT NOT NULL, data_fonte TEXT NOT NULL,
  tipo_fonte TEXT NOT NULL CHECK(tipo_fonte IN('primaria','secundaria','medicao_propria')),
  confianca TEXT NOT NULL CHECK(confianca IN('alta','media','baixa')), nota TEXT, verificado_em TEXT NOT NULL,
  UNIQUE(metrica,segmento,verificado_em));
CREATE VIEW benchmarks_vigentes AS SELECT b.* FROM benchmarks b
  WHERE b.verificado_em = (SELECT MAX(verificado_em) FROM benchmarks x WHERE x.metrica=b.metrica AND x.segmento=b.segmento);

-- Stage thresholds, versioned (section 8.1). A new version never loosens the previous one (section 12).
CREATE TABLE limiares(id INTEGER PRIMARY KEY, etapa TEXT NOT NULL CHECK(etapa IN('S1','S2','S3')), metrica TEXT NOT NULL,
  tipo_criterio TEXT NOT NULL CHECK(tipo_criterio IN('contagem','taxa')),
  limiar_passa REAL NOT NULL, limiar_mata REAL NOT NULL, n_min INTEGER NOT NULL, eventos_min INTEGER NOT NULL,
  prazo_dias INTEGER NOT NULL, mata_destino TEXT NOT NULL CHECK(mata_destino IN('morta','arquivada')),
  versao INTEGER NOT NULL, vigente_desde TEXT NOT NULL, origem TEXT NOT NULL CHECK(origem IN('benchmark','heuristica','calibrado')),
  ancora TEXT, UNIQUE(etapa,metrica,versao));
CREATE TRIGGER trg_limiar_nao_afrouxa BEFORE INSERT ON limiares
WHEN EXISTS(SELECT 1 FROM limiares l WHERE l.etapa=NEW.etapa AND l.metrica=NEW.metrica
            AND l.versao=(SELECT MAX(versao) FROM limiares x WHERE x.etapa=NEW.etapa AND x.metrica=NEW.metrica)
            AND (NEW.limiar_passa < l.limiar_passa OR NEW.limiar_mata < l.limiar_mata))
BEGIN SELECT RAISE(ABORT,'limiar_nao_afrouxa'); END;

-- Pre-registered hypotheses per stage: born open, decided only by UPDATE with data, never rewritten.
CREATE TABLE hipoteses(id INTEGER PRIMARY KEY, ideia_id INTEGER NOT NULL REFERENCES ideias(id),
  etapa TEXT NOT NULL CHECK(etapa IN('S1','S2','S3')), metrica TEXT NOT NULL,
  tipo_criterio TEXT NOT NULL CHECK(tipo_criterio IN('contagem','taxa')),
  limiar_passa REAL NOT NULL, limiar_mata REAL NOT NULL, n_min INTEGER NOT NULL, eventos_min INTEGER NOT NULL,
  limiar_versao INTEGER NOT NULL, prazo_dias INTEGER NOT NULL,
  estendida INTEGER NOT NULL DEFAULT 0 CHECK(estendida IN(0,1)), passa_estendido REAL,
  estendida_em TEXT,             -- date of the second channel: the extended window starts here (section 8.2)
  janela1_abaixo INTEGER NOT NULL DEFAULT 0 CHECK(janela1_abaixo IN(0,1)),   -- 1 = the first window ended at or below the kill line
  resultado TEXT CHECK(resultado IN('confirmada','refutada','inconclusiva') OR resultado IS NULL),
  n_observado INTEGER, valor_observado REAL, aprendizado TEXT,
  criada_em TEXT NOT NULL DEFAULT (datetime('now')), fechada_em TEXT,
  ciclo INTEGER,   -- set by the database: the idea's cycle at pre-registration
  CHECK(resultado IS NULL OR fechada_em IS NOT NULL),
  CHECK(estendida = 0 OR (passa_estendido IS NOT NULL AND estendida_em IS NOT NULL)));
CREATE TRIGGER trg_hipotese_nasce_aberta BEFORE INSERT ON hipoteses
WHEN NEW.resultado IS NOT NULL
BEGIN SELECT RAISE(ABORT,'decisao_so_por_update'); END;
CREATE TRIGGER trg_hipotese_ciclo AFTER INSERT ON hipoteses
BEGIN UPDATE hipoteses SET ciclo=(SELECT ciclo FROM ideias WHERE id=NEW.ideia_id) WHERE id=NEW.id; END;
-- fail closed: a metric or segment with no limiares row (a typo such as 'E30') is refused too
CREATE TRIGGER trg_hipotese_copia_limiar BEFORE INSERT ON hipoteses
WHEN NOT EXISTS(SELECT 1 FROM limiares l WHERE l.etapa=NEW.etapa AND l.metrica=NEW.metrica AND l.versao=NEW.limiar_versao
                AND l.versao=(SELECT MAX(versao) FROM limiares x WHERE x.etapa=l.etapa AND x.metrica=l.metrica)
                AND l.tipo_criterio=NEW.tipo_criterio AND l.limiar_passa=NEW.limiar_passa AND l.limiar_mata=NEW.limiar_mata
                AND l.n_min=NEW.n_min AND l.eventos_min=NEW.eventos_min AND l.prazo_dias=NEW.prazo_dias)
BEGIN SELECT RAISE(ABORT,'pre_registro_diverge_do_limiar'); END;
CREATE TRIGGER trg_hipotese_imutavel BEFORE UPDATE OF etapa, metrica, tipo_criterio, limiar_passa, limiar_mata, n_min,
  eventos_min, limiar_versao, prazo_dias, ideia_id ON hipoteses
BEGIN SELECT RAISE(ABORT,'hipotese_imutavel'); END;
CREATE TRIGGER trg_hipotese_decidida_fixa BEFORE UPDATE OF resultado, n_observado, valor_observado, estendida, passa_estendido, janela1_abaixo ON hipoteses
WHEN OLD.resultado IS NOT NULL
BEGIN SELECT RAISE(ABORT,'hipotese_imutavel'); END;
-- An extension is a real second chance: a channel NOT used in this cycle's window, posted after that window ended,
-- on the date the extended window starts.
CREATE TRIGGER trg_extensao BEFORE UPDATE OF estendida ON hipoteses
WHEN NEW.estendida=1 AND OLD.estendida=0
 AND NOT EXISTS(SELECT 1 FROM lancamentos l WHERE l.ideia_id=NEW.ideia_id AND l.ciclo=NEW.ciclo AND l.canal<>'outro' AND date(l.postado_em)=NEW.estendida_em
                AND date(l.postado_em) >= date((SELECT MIN(postado_em) FROM lancamentos WHERE ideia_id=NEW.ideia_id AND ciclo=NEW.ciclo),
                                               '+' || NEW.prazo_dias || ' days')
                AND l.canal NOT IN (SELECT canal FROM lancamentos x WHERE x.ideia_id=NEW.ideia_id AND x.ciclo=NEW.ciclo
                                    AND date(x.postado_em) < date((SELECT MIN(postado_em) FROM lancamentos WHERE ideia_id=NEW.ideia_id AND ciclo=NEW.ciclo),
                                                                  '+' || NEW.prazo_dias || ' days')))
BEGIN SELECT RAISE(ABORT,'extensao_sem_segundo_canal'); END;
-- A decision (either way) waits while a suspect star day (a spike without a post) sits in the window unresolved:
-- leaving it out could kill an idea whose spike was organic. Closing as 'inconclusiva' is always allowed.
CREATE TRIGGER trg_estrelas_suspeitas BEFORE UPDATE OF resultado ON hipoteses
WHEN NEW.resultado IN ('confirmada','refutada') AND OLD.resultado IS NULL
 AND EXISTS(SELECT 1 FROM estrelas_diarias s WHERE s.ideia_id=NEW.ideia_id AND s.suspeito=1
            AND s.data >= COALESCE(NEW.estendida_em, (SELECT date(MIN(postado_em)) FROM lancamentos WHERE ideia_id=NEW.ideia_id AND ciclo=NEW.ciclo))
            AND s.data < date(COALESCE(NEW.estendida_em, (SELECT date(MIN(postado_em)) FROM lancamentos WHERE ideia_id=NEW.ideia_id AND ciclo=NEW.ciclo)),
                              '+' || NEW.prazo_dias || ' days'))
BEGIN SELECT RAISE(ABORT,'estrelas_suspeitas'); END;
-- A decision needs the observed values and one star row for EVERY day of the decided window (zeros included).
CREATE TRIGGER trg_decisao_com_dado BEFORE UPDATE OF resultado ON hipoteses
WHEN NEW.resultado IN ('confirmada','refutada') AND OLD.resultado IS NULL
 AND (NEW.n_observado IS NULL OR NEW.valor_observado IS NULL
      OR (SELECT COUNT(DISTINCT s.data) FROM estrelas_diarias s WHERE s.ideia_id=NEW.ideia_id
          AND s.data >= COALESCE(NEW.estendida_em, (SELECT date(MIN(postado_em)) FROM lancamentos WHERE ideia_id=NEW.ideia_id AND ciclo=NEW.ciclo))
          AND s.data < date(COALESCE(NEW.estendida_em, (SELECT date(MIN(postado_em)) FROM lancamentos WHERE ideia_id=NEW.ideia_id AND ciclo=NEW.ciclo)),
                            '+' || MIN(NEW.n_observado, NEW.prazo_dias) || ' days'))
         < MIN(NEW.n_observado, NEW.prazo_dias))
BEGIN SELECT RAISE(ABORT,'decisao_sem_dado'); END;
-- A repo that was PUBLIC before its launch day (publico_em; a repo built private is public from the launch day; with
-- publico_em missing, its creation date: fail closed) needs the 28 days before the cycle's first launch (zeros included): the window is judged net of that
-- pace (q_hipoteses_abertas.baseline_janela).
CREATE TRIGGER trg_decisao_baseline BEFORE UPDATE OF resultado ON hipoteses
WHEN NEW.resultado IN ('confirmada','refutada') AND OLD.resultado IS NULL
 AND EXISTS(SELECT 1 FROM repos r WHERE r.proprio_ideia_id=NEW.ideia_id AND COALESCE(r.publico_em, r.criado_em)
            < date((SELECT MIN(postado_em) FROM lancamentos WHERE ideia_id=NEW.ideia_id AND ciclo=NEW.ciclo)))
 AND (SELECT COUNT(DISTINCT s.data) FROM estrelas_diarias s WHERE s.ideia_id=NEW.ideia_id
      AND s.data >= date((SELECT MIN(postado_em) FROM lancamentos WHERE ideia_id=NEW.ideia_id AND ciclo=NEW.ciclo),'-28 days')
      AND s.data < date((SELECT MIN(postado_em) FROM lancamentos WHERE ideia_id=NEW.ideia_id AND ciclo=NEW.ciclo))) < 28
BEGIN SELECT RAISE(ABORT,'decisao_sem_dado'); END;
-- Stages are decided only while the idea is being measured (closing as 'inconclusiva' is always allowed).
CREATE TRIGGER trg_decisao_em_medicao BEFORE UPDATE OF resultado ON hipoteses
WHEN NEW.resultado IN ('confirmada','refutada') AND OLD.resultado IS NULL
 AND (SELECT estado FROM ideias WHERE id=NEW.ideia_id) NOT IN ('lancada','tracao','hit')
BEGIN SELECT RAISE(ABORT,'ideia_fora_de_medicao'); END;
CREATE TRIGGER trg_decisao_coerente BEFORE UPDATE OF resultado ON hipoteses
WHEN OLD.resultado IS NULL AND NEW.valor_observado IS NOT NULL AND (
     (NEW.resultado='confirmada' AND NEW.valor_observado < (CASE WHEN NEW.estendida=1 THEN NEW.passa_estendido ELSE NEW.limiar_passa END))
  OR (NEW.resultado='refutada' AND NEW.valor_observado >= (CASE WHEN NEW.estendida=1 THEN NEW.passa_estendido ELSE NEW.limiar_passa END)))
BEGIN SELECT RAISE(ABORT,'decisao_incoerente'); END;
-- An extension kills only when the first window was already at or below the kill line: between the lines it was a
-- second chance, and a weak tail after the launch peak is no proof of failure (section 8.2).
CREATE TRIGGER trg_extensao_mata BEFORE UPDATE OF resultado ON hipoteses
WHEN NEW.resultado='refutada' AND OLD.resultado IS NULL AND NEW.estendida=1 AND NEW.janela1_abaixo=0
BEGIN SELECT RAISE(ABORT,'decisao_incoerente'); END;

CREATE TABLE pendencias(id INTEGER PRIMARY KEY, ideia_id INTEGER REFERENCES ideias(id), texto TEXT NOT NULL,
  criada_em TEXT NOT NULL DEFAULT (datetime('now')), resolvida_em TEXT, prova_dono TEXT,
  cancelada_em TEXT, motivo_cancelamento TEXT,
  CHECK(resolvida_em IS NULL OR prova_dono IS NOT NULL),
  CHECK(cancelada_em IS NULL OR motivo_cancelamento IS NOT NULL));

CREATE TABLE horas(id INTEGER PRIMARY KEY, ideia_id INTEGER NOT NULL REFERENCES ideias(id), data TEXT NOT NULL,
  horas REAL NOT NULL CHECK(horas > 0), tipo TEXT NOT NULL CHECK(tipo IN('construcao','lancamento','manutencao')),
  prova_dono TEXT NOT NULL);

-- ===== State machine guards (section 10) =====

CREATE TRIGGER trg_nasce_em_sinal BEFORE INSERT ON ideias
WHEN NEW.estado <> 'sinal'
BEGIN SELECT RAISE(ABORT,'ideia_nasce_em_sinal'); END;

-- Every state change carries a matching event written just before it.
CREATE TRIGGER trg_evento BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado <> OLD.estado AND NOT EXISTS(SELECT 1 FROM ideia_eventos e
  WHERE e.id = (SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)
    AND e.de=OLD.estado AND e.para=NEW.estado AND e.em >= datetime('now','-10 minutes'))
BEGIN SELECT RAISE(ABORT,'sem_ideia_evento'); END;

CREATE TRIGGER trg_transicao_valida BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado <> OLD.estado AND NEW.estado <> 'morta' AND NOT (
 (OLD.estado='sinal' AND NEW.estado IN ('candidata','arquivada')) OR
 (OLD.estado='candidata' AND NEW.estado IN ('em_construcao','arquivada')) OR
 (OLD.estado='em_construcao' AND NEW.estado IN ('pronta','arquivada')) OR
 (OLD.estado='pronta' AND NEW.estado IN ('lancada','em_construcao','arquivada')) OR
 (OLD.estado='lancada' AND NEW.estado IN ('tracao','arquivada')) OR
 (OLD.estado='tracao' AND NEW.estado IN ('hit','arquivada')) OR
 (OLD.estado='hit' AND NEW.estado='arquivada') OR
 (OLD.estado IN ('morta','arquivada') AND NEW.estado='candidata'))
BEGIN SELECT RAISE(ABORT,'transicao_fora_da_tabela'); END;

CREATE TRIGGER trg_transicao_do_dono BEFORE INSERT ON ideia_eventos
WHEN ((NEW.de='candidata' AND NEW.para='em_construcao') OR (NEW.de='pronta' AND NEW.para='lancada')) AND NEW.ator <> 'dono'
BEGIN SELECT RAISE(ABORT,'transicao_exige_dono'); END;

-- Owner phrases (section 0.1) at the START of the quote: "não aprovo..." is no approval. Curly quotes count as straight;
-- SQLite's lower() is ASCII-only, so the phrase's accented capitals are folded by hand.
CREATE TRIGGER trg_frase_do_dono BEFORE INSERT ON ideia_eventos
WHEN NEW.ator='dono' AND (
     (NEW.para='em_construcao' AND NEW.de='candidata'
      AND lower(replace(replace(replace(NEW.prova_dono,'“','"'),'Ç','ç'),'Ã','ã') || ' ') NOT GLOB ('"aprovo a construção da ideia#' || NEW.ideia_id || '[^0-9]*'))
  OR (NEW.para='lancada' AND NEW.de='pronta'
      AND lower(replace(replace(replace(NEW.prova_dono,'“','"'),'Ç','ç'),'Ã','ã') || ' ') NOT GLOB ('"lancei a ideia#' || NEW.ideia_id || '[^0-9]*'))
  OR (NEW.motivo LIKE 'REABERTA:%'
      AND lower(replace(replace(replace(NEW.prova_dono,'“','"'),'Ç','ç'),'Ã','ã') || ' ') NOT GLOB ('"reabro a ideia#' || NEW.ideia_id || '[^0-9]*')))
BEGIN SELECT RAISE(ABORT,'frase_do_dono'); END;

-- Any entry in candidata (also a reopening): at least one behavioral demand signal above its threshold (4.2, D0).
-- sinais.reacoes = the issue's 👍, the post's points, or the abandoned repo's stars.
CREATE TRIGGER trg_candidata_demanda BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='candidata' AND OLD.estado<>'candidata'
 AND NOT EXISTS(SELECT 1 FROM evidencias e JOIN sinais s ON s.id=e.sinal_id WHERE e.ideia_id=NEW.id AND e.polaridade=1
                AND ((s.tipo IN ('issue_reacoes','issue_not_planned')
                      AND s.reacoes >= (SELECT CAST(valor AS INTEGER) FROM config WHERE chave='demanda_reacoes_min'))
                  OR (s.tipo='pedido_ferramenta'
                      AND s.reacoes >= (SELECT CAST(valor AS INTEGER) FROM config WHERE chave='demanda_pontos_min'))
                  OR (s.tipo='repo_abandonado'
                      AND s.reacoes >= (SELECT CAST(valor AS INTEGER) FROM config WHERE chave='demanda_estrelas_abandonado_min'))))
BEGIN SELECT RAISE(ABORT,'sem_sinal_de_demanda'); END;

-- Forbidden categories (section 5) can only die, with that reason.
CREATE TRIGGER trg_categoria_proibida BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado <> OLD.estado AND NEW.categoria IN ('self_hosted_completo','framework_agentes','prompts_vazados','build_your_own','mcp_server')
 AND NOT (NEW.estado='candidata' OR (NEW.estado='morta' AND NEW.motivo_morte IS 'categoria_proibida'))
BEGIN SELECT RAISE(ABORT,'categoria_proibida'); END;

-- The build approval: complete sheet, advocate after the last entry in candidata, one build slot, category hit rate,
-- free niche, maintenance load (section 6).
CREATE TRIGGER trg_construcao BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='em_construcao' AND OLD.estado='candidata'
BEGIN
  SELECT RAISE(ABORT,'ficha_incompleta') WHERE NEW.categoria IS NULL OR COALESCE(TRIM(NEW.gancho),'')=''
    OR COALESCE(TRIM(NEW.prova_numero),'')='' OR NEW.linguagem IS NULL OR NEW.estrelas_alvo IS NULL OR NEW.carga_h_semana IS NULL
    OR COALESCE(TRIM(NEW.como_chega),'')=''
    OR NEW.horas_estimadas IS NULL OR NEW.horas_estimadas <= 0
    OR NEW.horas_estimadas > (SELECT CAST(valor AS REAL) FROM config WHERE chave='horas_mvp_max')
    OR NEW.licenca IS NULL OR NEW.licenca NOT IN ('MIT','Apache-2.0','AGPL-3.0')
    OR (NEW.licenca='AGPL-3.0' AND COALESCE(TRIM(NEW.licenca_justificativa),'')='');
  SELECT RAISE(ABORT,'advogado_obrigatorio') WHERE NEW.advogado_em IS NULL
    OR NEW.advogado_em < (SELECT MAX(em) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de<>'candidata');
  -- a ready idea still holds the slot: it may go back to em_construcao when an L0 item breaks (section 7.2)
  SELECT RAISE(ABORT,'slot_ocupado') WHERE (SELECT COUNT(*) FROM ideias WHERE estado IN ('em_construcao','pronta') AND id<>NEW.id)
    >= (SELECT CAST(valor AS INTEGER) FROM config WHERE chave='slots_construcao');
  SELECT RAISE(ABORT,'hit_rate_sem_benchmark') WHERE NEW.hit_rate_categoria IS NOT NULL
    AND NOT EXISTS(SELECT 1 FROM benchmarks_vigentes b WHERE b.id=NEW.hit_rate_benchmark_id AND b.valor=NEW.hit_rate_categoria);
  -- the exempt categories have no topic rate: any rate recorded for them is ignored (no incentive to skip measuring)
  SELECT RAISE(ABORT,'categoria_fraca') WHERE NEW.categoria NOT IN ('lib_benchmark','sucessor_abandonado','alternativa_open')
    AND (NEW.hit_rate_categoria IS NULL
         OR NEW.hit_rate_categoria < (SELECT CAST(valor AS REAL) FROM config WHERE chave='categoria_hit_min'));
  -- the low-maintenance mode doubles the ceiling, never removes it
  SELECT RAISE(ABORT,'carga_acima_do_teto') WHERE
    NEW.carga_h_semana > (SELECT CAST(valor AS REAL) FROM config WHERE chave='carga_max_h_semana') * (1 + NEW.modo_baixa_manutencao);
  -- the hook says what the tool does; it does not lead with an AI buzzword (section 5, cut 6)
  -- (an optional leading article: "The AI agent that..." leads with AI too)
  SELECT RAISE(ABORT,'gancho_vende_ia') WHERE EXISTS(
    SELECT 1 FROM (SELECT '' AS a UNION ALL SELECT 'a ' UNION ALL SELECT 'an ' UNION ALL SELECT 'the ' UNION ALL SELECT 'your '
                   UNION ALL SELECT 'o ' UNION ALL SELECT 'um ' UNION ALL SELECT 'uma ' UNION ALL SELECT 'seu ' UNION ALL SELECT 'sua ') art,
                  (SELECT 'ai' AS w UNION ALL SELECT 'agent' UNION ALL SELECT 'agents' UNION ALL SELECT 'agentic' UNION ALL SELECT 'llm'
                   UNION ALL SELECT 'llms' UNION ALL SELECT 'gpt' UNION ALL SELECT 'mcp'
                   UNION ALL SELECT 'ia' UNION ALL SELECT 'agente' UNION ALL SELECT 'agentes' UNION ALL SELECT 'assistente'
                   UNION ALL SELECT 'copilot' UNION ALL SELECT 'chatbot') wd
    WHERE lower(trim(NEW.gancho)) = art.a || wd.w OR lower(trim(NEW.gancho)) GLOB art.a || wd.w || '[^a-z0-9]*'
       OR lower(trim(NEW.gancho)) GLOB art.a || 'gpt[0-9-]*');
  -- an afternoon's work is a quick one-off (Hacker News: "Don't post quickly-generated one-offs")
  -- (the launch polish of a repo that is already public (section 13) has no hour floor)
  SELECT RAISE(ABORT,'one_off') WHERE NEW.horas_estimadas < (SELECT CAST(valor AS REAL) FROM config WHERE chave='horas_mvp_min')
    AND NOT EXISTS(SELECT 1 FROM repos r WHERE r.proprio_ideia_id=NEW.id AND r.publico_em IS NOT NULL);
  -- the niche search left a trace: at least one linked repo with a complete snapshot; a successor with missing
  -- dates cannot be judged (fail closed)
  SELECT RAISE(ABORT,'concorrente_incompleto') WHERE EXISTS(SELECT 1 FROM ideia_repos ir JOIN repos r ON r.id=ir.repo_id
    WHERE ir.ideia_id=NEW.id AND ir.papel='sucessor' AND (r.criado_em IS NULL
      OR NOT EXISTS(SELECT 1 FROM repo_snapshots s WHERE s.repo_id=r.id AND s.pushed_at IS NOT NULL)));
  SELECT RAISE(ABORT,'sem_concorrente_verificado') WHERE NOT EXISTS(SELECT 1 FROM ideia_repos ir JOIN repos r ON r.id=ir.repo_id
    JOIN repo_snapshots s ON s.repo_id=r.id WHERE ir.ideia_id=NEW.id AND r.criado_em IS NOT NULL AND s.pushed_at IS NOT NULL);
  -- an active successor (any age) with > 1,000 stars and a push in the last 90 days, not fake-starred
  SELECT RAISE(ABORT,'nicho_tomado') WHERE EXISTS(SELECT 1 FROM ideia_repos ir JOIN repos r ON r.id=ir.repo_id
    JOIN repo_snapshots s ON s.repo_id=r.id AND s.data=(SELECT MAX(data) FROM repo_snapshots WHERE repo_id=r.id)
    WHERE ir.ideia_id=NEW.id AND ir.papel='sucessor' AND r.suspeito_fake=0
      AND s.estrelas > 1000 AND s.pushed_at >= date('now','-90 days'));
END;

-- The build cuts of trg_construcao as one row per finished desk (candidata with an advocate): corte = the first cut
-- that fails, NULL when buildable. q_fila_construcao lists corte IS NULL, q_mesa_reprovada the rest, so the queue
-- never proposes an idea the database will refuse. Keep it in step with trg_construcao (same names); a forbidden
-- category comes first: it can only die (trg_categoria_proibida), whatever else fails.
CREATE VIEW mesa_cortes AS
SELECT i.id, CASE
  WHEN i.categoria IN ('self_hosted_completo','framework_agentes','prompts_vazados','build_your_own','mcp_server') THEN 'categoria_proibida'
  WHEN i.categoria IS NULL OR COALESCE(TRIM(i.gancho),'')='' OR COALESCE(TRIM(i.prova_numero),'')='' OR i.linguagem IS NULL
    OR i.estrelas_alvo IS NULL OR i.carga_h_semana IS NULL OR i.horas_estimadas IS NULL OR i.horas_estimadas <= 0
    OR COALESCE(TRIM(i.como_chega),'')=''
    OR i.horas_estimadas > (SELECT CAST(valor AS REAL) FROM config WHERE chave='horas_mvp_max')
    OR i.licenca IS NULL OR i.licenca NOT IN ('MIT','Apache-2.0','AGPL-3.0')
    OR (i.licenca='AGPL-3.0' AND COALESCE(TRIM(i.licenca_justificativa),'')='') THEN 'ficha_incompleta'
  WHEN i.hit_rate_categoria IS NOT NULL
    AND NOT EXISTS(SELECT 1 FROM benchmarks_vigentes b WHERE b.id=i.hit_rate_benchmark_id AND b.valor=i.hit_rate_categoria) THEN 'hit_rate_sem_benchmark'
  WHEN i.categoria NOT IN ('lib_benchmark','sucessor_abandonado','alternativa_open') AND (i.hit_rate_categoria IS NULL
    OR i.hit_rate_categoria < (SELECT CAST(valor AS REAL) FROM config WHERE chave='categoria_hit_min')) THEN 'categoria_fraca'
  WHEN i.carga_h_semana > (SELECT CAST(valor AS REAL) FROM config WHERE chave='carga_max_h_semana') * (1 + i.modo_baixa_manutencao) THEN 'carga_acima_do_teto'
  WHEN EXISTS(
    SELECT 1 FROM (SELECT '' AS a UNION ALL SELECT 'a ' UNION ALL SELECT 'an ' UNION ALL SELECT 'the ' UNION ALL SELECT 'your '
                   UNION ALL SELECT 'o ' UNION ALL SELECT 'um ' UNION ALL SELECT 'uma ' UNION ALL SELECT 'seu ' UNION ALL SELECT 'sua ') art,
                  (SELECT 'ai' AS w UNION ALL SELECT 'agent' UNION ALL SELECT 'agents' UNION ALL SELECT 'agentic' UNION ALL SELECT 'llm'
                   UNION ALL SELECT 'llms' UNION ALL SELECT 'gpt' UNION ALL SELECT 'mcp'
                   UNION ALL SELECT 'ia' UNION ALL SELECT 'agente' UNION ALL SELECT 'agentes' UNION ALL SELECT 'assistente'
                   UNION ALL SELECT 'copilot' UNION ALL SELECT 'chatbot') wd
    WHERE lower(trim(i.gancho)) = art.a || wd.w OR lower(trim(i.gancho)) GLOB art.a || wd.w || '[^a-z0-9]*'
       OR lower(trim(i.gancho)) GLOB art.a || 'gpt[0-9-]*') THEN 'gancho_vende_ia'
  WHEN i.horas_estimadas < (SELECT CAST(valor AS REAL) FROM config WHERE chave='horas_mvp_min')
    AND NOT EXISTS(SELECT 1 FROM repos r WHERE r.proprio_ideia_id=i.id AND r.publico_em IS NOT NULL) THEN 'one_off'
  WHEN EXISTS(SELECT 1 FROM ideia_repos ir JOIN repos r ON r.id=ir.repo_id
    WHERE ir.ideia_id=i.id AND ir.papel='sucessor' AND (r.criado_em IS NULL
      OR NOT EXISTS(SELECT 1 FROM repo_snapshots s WHERE s.repo_id=r.id AND s.pushed_at IS NOT NULL))) THEN 'concorrente_incompleto'
  WHEN NOT EXISTS(SELECT 1 FROM ideia_repos ir JOIN repos r ON r.id=ir.repo_id
    JOIN repo_snapshots s ON s.repo_id=r.id WHERE ir.ideia_id=i.id AND r.criado_em IS NOT NULL AND s.pushed_at IS NOT NULL) THEN 'sem_concorrente_verificado'
  WHEN EXISTS(SELECT 1 FROM ideia_repos ir JOIN repos r ON r.id=ir.repo_id
    JOIN repo_snapshots s ON s.repo_id=r.id AND s.data=(SELECT MAX(data) FROM repo_snapshots WHERE repo_id=r.id)
    WHERE ir.ideia_id=i.id AND ir.papel='sucessor' AND r.suspeito_fake=0
      AND s.estrelas > 1000 AND s.pushed_at >= date('now','-90 days')) THEN 'nicho_tomado'
  END AS corte
FROM ideias i WHERE i.estado='candidata' AND i.advogado_em IS NOT NULL;

-- (created before trg_pronta: SQLite fires the later trigger first, so a missing checklist is reported first)
-- pronta also needs the real build hours to reach horas_mvp_min: the estimate alone does not prove it is not a one-off.
CREATE TRIGGER trg_pronta_horas BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='pronta' AND OLD.estado='em_construcao'
 AND (SELECT COALESCE(SUM(horas),0) FROM horas WHERE ideia_id=NEW.id AND tipo='construcao')
     < (SELECT CAST(valor AS REAL) FROM config WHERE chave='horas_mvp_min')
 AND NOT EXISTS(SELECT 1 FROM repos r WHERE r.proprio_ideia_id=NEW.id AND r.publico_em IS NOT NULL)
BEGIN SELECT RAISE(ABORT,'horas_reais_insuficientes'); END;

-- pronta: every mandatory launch-gate item proved ok for this idea (section 7.2).
CREATE TRIGGER trg_pronta BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='pronta' AND OLD.estado='em_construcao'
 AND EXISTS(SELECT 1 FROM checklist_itens ci WHERE ci.obrigatorio=1
            AND NOT EXISTS(SELECT 1 FROM checklist c WHERE c.ideia_id=NEW.id AND c.item=ci.codigo AND c.ok=1
                           -- proved in this build (a reopened idea re-proves every item)
                           AND c.verificado_em >= (SELECT MAX(em) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='em_construcao')))
BEGIN SELECT RAISE(ABORT,'checklist_incompleto'); END;

-- lancada: the owner's post of THIS cycle is recorded (section 7.3).
CREATE TRIGGER trg_lancada BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='lancada' AND OLD.estado='pronta'
 AND NOT EXISTS(SELECT 1 FROM lancamentos WHERE ideia_id=NEW.id AND ciclo=NEW.ciclo)
BEGIN SELECT RAISE(ABORT,'sem_lancamento'); END;

-- tracao / hit only after the stage hypothesis of THIS cycle was confirmed.
CREATE TRIGGER trg_etapas BEFORE UPDATE OF estado ON ideias
WHEN (NEW.estado='tracao' AND OLD.estado='lancada'
      AND NOT EXISTS(SELECT 1 FROM hipoteses WHERE ideia_id=NEW.id AND ciclo=NEW.ciclo AND etapa='S2' AND resultado='confirmada'))
  OR (NEW.estado='hit' AND OLD.estado='tracao'
      AND NOT EXISTS(SELECT 1 FROM hipoteses WHERE ideia_id=NEW.id AND ciclo=NEW.ciclo AND etapa='S3' AND resultado='confirmada'))
BEGIN SELECT RAISE(ABORT,'etapa_nao_passou'); END;

-- One post is a noisy sample: killing by test needs two different launch channels (section 8.3).
CREATE TRIGGER trg_matar_dois_canais BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='morta' AND OLD.estado<>'morta' AND NEW.motivo_morte IS 'teste_reprovado'
 AND (SELECT COUNT(DISTINCT canal) FROM lancamentos WHERE ideia_id=NEW.id AND ciclo=NEW.ciclo AND canal<>'outro') < 2
BEGIN SELECT RAISE(ABORT,'matar_exige_dois_canais'); END;

CREATE TRIGGER trg_morta_motivo BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='morta' AND OLD.estado<>'morta' AND NEW.motivo_morte IS NULL
BEGIN SELECT RAISE(ABORT,'morta_sem_motivo'); END;

CREATE TRIGGER trg_arquivada_reabrir_se BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='arquivada' AND OLD.estado<>'arquivada' AND COALESCE(TRIM(NEW.reabrir_se),'')=''
BEGIN SELECT RAISE(ABORT,'arquivada_sem_reabrir_se'); END;

-- Reopening: a REABERTA event; serious deaths only by the owner; the routine reopens an idea once.
CREATE TRIGGER trg_reabertura BEFORE UPDATE OF estado ON ideias
WHEN OLD.estado IN ('morta','arquivada') AND NEW.estado='candidata' AND (
     NOT EXISTS(SELECT 1 FROM ideia_eventos e WHERE e.id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)
                AND e.motivo LIKE 'REABERTA:%')
  OR (OLD.motivo_morte IN ('teste_reprovado','categoria_proibida','advogado_do_diabo','estrelas_incentivadas','dono_desistiu')
      AND (SELECT ator FROM ideia_eventos WHERE id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)) <> 'dono')
  OR ((SELECT ator FROM ideia_eventos WHERE id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)) = 'rotina'
      AND (SELECT COUNT(*) FROM ideia_eventos WHERE ideia_id=NEW.id AND motivo LIKE 'REABERTA:%' AND ator='rotina') > 1))
BEGIN SELECT RAISE(ABORT,'reabertura_proibida'); END;

-- On reopening, the idea redoes the advocate and the sheet's judgment fields.
CREATE TRIGGER trg_reabertura_zera AFTER UPDATE OF estado ON ideias
WHEN OLD.estado IN ('morta','arquivada') AND NEW.estado='candidata'
BEGIN UPDATE ideias SET advogado_em=NULL, motivo_morte=NULL, reabrir_se=NULL, ciclo=ciclo+1 WHERE id=NEW.id; END;

CREATE TRIGGER trg_atualizada AFTER UPDATE OF estado ON ideias
WHEN NEW.estado <> OLD.estado
BEGIN UPDATE ideias SET atualizada_em=datetime('now') WHERE id=NEW.id; END;

-- Changing the sheet after the devil's advocate voids it: the advocate judged other facts (section 6.3).
CREATE TRIGGER trg_ficha_muda_advogado AFTER UPDATE OF categoria, gancho, prova_numero, linguagem, horas_estimadas, estrelas_alvo,
  carga_h_semana, hit_rate_categoria, hit_rate_benchmark_id, modo_baixa_manutencao, licenca, como_chega ON ideias
WHEN NEW.advogado_em IS NOT NULL AND NEW.advogado_em IS OLD.advogado_em AND NEW.estado='candidata'
BEGIN UPDATE ideias SET advogado_em=NULL WHERE id=NEW.id; END;

-- A measured idea leaves for arquivada/morta only after its open hypotheses were closed (as 'inconclusiva' when the
-- stage was not decided); tracao/hit close the earlier stages too.
CREATE TRIGGER trg_hipoteses_fechadas BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado <> OLD.estado AND (
     (NEW.estado IN ('arquivada','morta') AND EXISTS(SELECT 1 FROM hipoteses WHERE ideia_id=NEW.id AND resultado IS NULL))
  OR (NEW.estado='tracao' AND EXISTS(SELECT 1 FROM hipoteses WHERE ideia_id=NEW.id AND resultado IS NULL AND etapa='S1'))
  OR (NEW.estado='hit' AND EXISTS(SELECT 1 FROM hipoteses WHERE ideia_id=NEW.id AND resultado IS NULL AND etapa IN ('S1','S2'))))
BEGIN SELECT RAISE(ABORT,'hipoteses_abertas'); END;
