-- Schema of the game-ideas routine. Dates in UTC: 'YYYY-MM-DD HH:MM:SS' (datetime('now')) or 'YYYY-MM-DD' (date('now')).
-- Identifiers (tables, columns, state values) are in Portuguese on purpose; SKILL.md explains each one.
PRAGMA foreign_keys=ON;
PRAGMA user_version=1;
-- PRAGMA foreign_keys does NOT persist: run 'PRAGMA foreign_keys=ON' on every new connection.

CREATE TABLE config(chave TEXT PRIMARY KEY, valor TEXT NOT NULL,
  origem TEXT NOT NULL CHECK(origem IN('dono','premissa','medido','seed')),
  atualizado_em TEXT NOT NULL DEFAULT (datetime('now')));

CREATE TABLE fontes(id INTEGER PRIMARY KEY, nome TEXT UNIQUE NOT NULL, plataforma TEXT NOT NULL, tipo TEXT NOT NULL,
  endpoint TEXT, mercado TEXT NOT NULL CHECK(mercado IN('BR','EN','todos')),
  frequencia TEXT NOT NULL CHECK(frequencia IN('diaria','semanal','manual')),
  cota_min INTEGER NOT NULL, limite TEXT, cursor TEXT,
  status TEXT NOT NULL DEFAULT 'ok' CHECK(status IN('ok','degradada','quebrada','desligada')),
  falhas_seguidas INTEGER NOT NULL DEFAULT 0, ultimo_ok_em TEXT, termos_nota TEXT);

CREATE TABLE runs(id INTEGER PRIMARY KEY,
  tipo TEXT NOT NULL CHECK(tipo IN('bootstrap','diaria','sexta')),
  iniciado_em TEXT NOT NULL DEFAULT (datetime('now')), terminado_em TEXT,
  status TEXT NOT NULL CHECK(status IN('rodando','ok','parcial','falhou')),
  motivo_parada TEXT CHECK(motivo_parada IN('saturou','teto_tempo','teto_buscas','erro') OR motivo_parada IS NULL),
  buscas INTEGER NOT NULL DEFAULT 0, sinais_novos INTEGER NOT NULL DEFAULT 0, taxa_novidade REAL,
  checklist_ok INTEGER, checklist_json TEXT, resumo_json TEXT, erro TEXT);

CREATE TABLE sinais(id INTEGER PRIMARY KEY, fonte_id INTEGER NOT NULL REFERENCES fontes(id),
  run_id INTEGER REFERENCES runs(id), hash TEXT NOT NULL UNIQUE, id_externo TEXT, url TEXT NOT NULL,
  url_status INTEGER NOT NULL CHECK(url_status IN(200,0)),   -- 0 only for source dono_campo (attested by the owner)
  trecho_literal TEXT NOT NULL CHECK(length(trecho_literal) >= 40),
  -- payload_json holds sha256 of the body + the response Date header for every url_status=200 (section 4.1)
  tipo TEXT NOT NULL CHECK(tipo IN('hit_plataforma','arbitragem','tag_coorte','jam_mecanica','reclamacao','tendencia','concorrente','plataforma','regulacao','outro')),
  autor_tipo TEXT, mercado TEXT CHECK(mercado IN('BR','EN','global_outros') OR mercado IS NULL),
  idioma TEXT, publicado_em TEXT, coletado_em TEXT NOT NULL DEFAULT (datetime('now')), payload_json TEXT,
  CHECK(url_status = 0 OR (json_valid(payload_json) AND length(json_extract(payload_json,'$.sha256')) = 64
                          AND json_extract(payload_json,'$.date') IS NOT NULL)));

CREATE TABLE ideias(id INTEGER PRIMARY KEY, titulo TEXT NOT NULL,
  hook TEXT,                     -- 1 sentence, visual, understandable in 3 s without sound
  twist TEXT,                    -- "It's X, but Y, so that Z" (Z measurable in telemetry)
  referencia TEXT,               -- the proven game/loop this idea derives from (if any)
  familia_id INTEGER, reaberta_de INTEGER REFERENCES ideias(id), reabrir_se TEXT,
  exploracao INTEGER NOT NULL DEFAULT 0 CHECK(exploracao IN(0,1)), exploracao_em TEXT,
  genero_central TEXT CHECK(genero_central IS NULL OR (genero_central <> '' AND genero_central NOT GLOB '*[^a-z0-9_]*')),
                                 -- core loop/genre for families: the Steam tag in lowercase snake_case (e.g. 'bullet_heaven')
  fonte_ideia TEXT CHECK(fonte_ideia IN('arbitragem','tag_genero','jam_itch','tendencia','reclamacao','exploracao') OR fonte_ideia IS NULL),
  plataforma TEXT CHECK(plataforma IN('web','steam','mobile','roblox','uefn') OR plataforma IS NULL),
  trilha TEXT CHECK(trilha IN('W','S','M','R') OR trilha IS NULL),
  modo TEXT CHECK(modo IN('solo','solo_async','coop_convite','party_host','plataforma_social') OR modo IS NULL),
  lista_publica INTEGER NOT NULL DEFAULT 0 CHECK(lista_publica IN(0,1)),
  servidor_usd_mes_1000ccu REAL,
  mercado TEXT CHECK(mercado IN('global','BR') OR mercado IS NULL),
  canal TEXT, canal_cobranca TEXT CHECK(canal_cobranca IN('steam','crazygames','poki','agregador','itch','appstore','play','roblox','uefn') OR canal_cobranca IS NULL),
  preco_alvo REAL, moeda_preco TEXT CHECK(moeda_preco IN('USD','BRL') OR moeda_preco IS NULL),
  exclusividade TEXT CHECK(exclusividade IN('poki','crazygames_agregadores','nenhuma') OR exclusividade IS NULL),
  horas_estimadas INTEGER,
  engine TEXT,                   -- chosen per idea from the engine matrix (e.g. godot, phaser, defold, unity, roblox_studio, uefn)
  engine_justificativa TEXT,     -- why this engine for this idea; required to enter em_construcao (trg_engine_antes_construcao)
  build_mb REAL,                 -- measured initial download of the test build, in MB (portal limits, section 7.2)
  tempo_gameplay_s REAL,         -- measured seconds until gameplay starts on simulated 4G
  tamanho_sala INTEGER,          -- players per room (coop/party modes), for the public-list density rule (6.4)
  advogado_em TEXT,              -- datetime of the last devil's advocate run (9.1); required to enter em_teste and validada
  ai_arte_visivel INTEGER CHECK(ai_arte_visivel IN(0,1) OR ai_arte_visivel IS NULL),
  ai_audio INTEGER CHECK(ai_audio IN(0,1) OR ai_audio IS NULL),
  ai_runtime INTEGER CHECK(ai_runtime IN(0,1) OR ai_runtime IS NULL),   -- content generated live by an LLM (cut 1)
  plano_moderacao TEXT,          -- required (>= 80 chars) to test an ai_runtime=1 idea (cut 1: no live LLM content without a moderation plan)
  loop_idle INTEGER CHECK(loop_idle IN(0,1) OR loop_idle IS NULL),   -- declared: progress that runs without input (cut 12); a payoff only at the end is loop_vazio and the idea dies
  loot_box INTEGER CHECK(loot_box IN(0,1)),                     -- declared explicitly (sheet);   -- ECA Digital art. 20: 1 = the idea has one -> can only die (trg_proibido)
  chat_livre INTEGER CHECK(chat_livre IN(0,1)),                 -- declared explicitly (sheet); -- art. 21: 1 = free chat -> can only die; emotes/pings are 0
  classificacao TEXT,            -- IARC / ClassInd self-rating
  janela_inicio TEXT, janela_fim TEXT, data_reativacao TEXT,
  arquivamento TEXT CHECK(arquivamento IN('resultado','operacional') OR arquivamento IS NULL),  -- why it was archived (10.2); NULL = resultado
  estado TEXT NOT NULL DEFAULT 'sinal' CHECK(estado IN
    ('sinal','candidata','pre_teste','em_teste','validada','em_construcao','lancada','congelada','arquivada','morta')),
  motivo_morte TEXT CHECK(motivo_morte IN('sem_canal','mercado_saturado','depende_fila','nao_jogavel_solo','twist_cosmetico',
    'clone_legal','escopo_grande','teste_reprovado','custo_alto','risco_plataforma','excluida_por_regra',
    'advogado_do_diabo','janela_fechada','loop_vazio') OR motivo_morte IS NULL),
  score REAL, score_json TEXT,
  criada_em TEXT NOT NULL DEFAULT (datetime('now')), atualizada_em TEXT NOT NULL DEFAULT (datetime('now')),
  CHECK(estado <> 'morta' OR motivo_morte IS NOT NULL));

CREATE TABLE ideia_eventos(id INTEGER PRIMARY KEY, ideia_id INTEGER NOT NULL REFERENCES ideias(id),
  run_id INTEGER REFERENCES runs(id), de TEXT, para TEXT NOT NULL, motivo TEXT NOT NULL,
  evidencia_ids TEXT, ator TEXT NOT NULL CHECK(ator IN('rotina','dono')),
  prova_dono TEXT,   -- literal quote of the owner's message, with date and time
  em TEXT NOT NULL DEFAULT (datetime('now'))
    CHECK(em GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]'));

CREATE TABLE evidencias(ideia_id INTEGER NOT NULL REFERENCES ideias(id), sinal_id INTEGER NOT NULL REFERENCES sinais(id),
  polaridade INTEGER NOT NULL CHECK(polaridade IN(-1,1)), peso REAL NOT NULL DEFAULT 1, nota TEXT,
  PRIMARY KEY(ideia_id,sinal_id));

CREATE TABLE concorrentes(id INTEGER PRIMARY KEY,
  loja TEXT NOT NULL CHECK(loja IN('steam','crazygames','poki','itch','roblox','uefn','appstore','play','web')),
  id_loja TEXT NOT NULL, nome TEXT, vendedor TEXT, url TEXT, modelo_preco TEXT, preco_texto TEXT,
  ultimo_sinal_de_vida TEXT,   -- date of the last review reply, changelog, commit or price change
  proprio_ideia_id INTEGER REFERENCES ideias(id),   -- set when this row is one of the owner's own games (ports, graduation)
  lancado_em TEXT CHECK(lancado_em IS NULL OR lancado_em GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),  -- ISO release date of the game (store/portal); < 120 days = trend candidate (section 4.4)
  lancado_em_incerto INTEGER NOT NULL DEFAULT 0 CHECK(lancado_em_incerto IN(0,1)),   -- 1 = the page shows no date (Poki, CrazyGames): an upper bound, never a trend
  primeira_vez_em TEXT NOT NULL DEFAULT (date('now')), UNIQUE(loja,id_loja));

CREATE TABLE ideia_concorrentes(ideia_id INTEGER NOT NULL REFERENCES ideias(id),
  concorrente_id INTEGER NOT NULL REFERENCES concorrentes(id),
  papel TEXT NOT NULL DEFAULT 'rival' CHECK(papel IN('referencia','rival')),  -- referencia = the X of the twist (trend rule)
  PRIMARY KEY(ideia_id,concorrente_id));

CREATE TABLE concorrente_snapshots(concorrente_id INTEGER NOT NULL REFERENCES concorrentes(id),
  data TEXT NOT NULL, pais TEXT NOT NULL, rank_lista TEXT NOT NULL DEFAULT '',
  ccu INTEGER, ccu_pico_14d INTEGER, reviews_total INTEGER, reviews_positivas_pct REAL, copias_estimadas INTEGER,
  plays INTEGER, minutos_por_jogador REAL, favoritos INTEGER, ratings_count INTEGER, rating_avg REAL,
  installs_min INTEGER, preco REAL, versao_data TEXT, rank_pos INTEGER, run_id INTEGER REFERENCES runs(id),
  PRIMARY KEY(concorrente_id,data,pais,rank_lista));

-- Cohort statistics per Steam tag/genre (Gamalytic free list endpoint), snapshot by date.
CREATE TABLE tag_coortes(tag TEXT NOT NULL, ano INTEGER NOT NULL, data TEXT NOT NULL,
  lancamentos INTEGER NOT NULL, mediana_copias REAL, p_10k REAL, p_100k REAL, fonte TEXT NOT NULL,
  PRIMARY KEY(tag, ano, data));

-- Trend tracking for the leader of a trend (daily CCU/plays), used by the trend window rule.
CREATE TABLE tendencias(id INTEGER PRIMARY KEY, nome TEXT NOT NULL, loja TEXT NOT NULL, id_loja TEXT NOT NULL,
  detectada_em TEXT NOT NULL DEFAULT (date('now')), fechada_em TEXT, clones_8sem INTEGER, status TEXT NOT NULL DEFAULT 'aberta'
  CHECK(status IN('aberta','fechada')), UNIQUE(loja,id_loja));

CREATE TABLE experimentos(id INTEGER PRIMARY KEY, ideia_id INTEGER NOT NULL REFERENCES ideias(id),
  etapa TEXT NOT NULL CHECK(etapa IN('G1','W1','W2','S1','S2','S3','S4','M1','R1','E5')),
  tipo TEXT NOT NULL CHECK(tipo IN('clip_hook','portal_teste','portal_webfit','pagina_steam','demo_playtest','next_fest','lancamento_steam','cpi_teste','publisher_teste','roblox_mvp','pos_lancamento')),
  url TEXT, utm_sources TEXT, paises_trafego TEXT, preco_testado REAL, moeda_preco_testado TEXT,
  estado TEXT NOT NULL CHECK(estado IN('planejado','rodando','encerrado','abortado')),
  inicio TEXT,   -- stage milestone (see limiares.marco_inicio); NULL while 'planejado'
  fim TEXT, decisao TEXT,
  criado_em TEXT NOT NULL DEFAULT (datetime('now')));   -- anchors the per-cycle guards (a reopened idea starts a new cycle)

CREATE TABLE hipoteses(id INTEGER PRIMARY KEY, ideia_id INTEGER NOT NULL REFERENCES ideias(id),
  experimento_id INTEGER NOT NULL REFERENCES experimentos(id),
  etapa TEXT NOT NULL CHECK(etapa IN('G1','W1','W2','S1','S2','S3','S4','M1','R1','E5')),
  enunciado TEXT NOT NULL, metrica TEXT NOT NULL,
  tipo_criterio TEXT NOT NULL CHECK(tipo_criterio IN('taxa','contagem','media','teto')),
  limiar_passa REAL NOT NULL, limiar_mata REAL NOT NULL, n_min INTEGER NOT NULL, eventos_min INTEGER NOT NULL,
  limiar_versao INTEGER NOT NULL, previsao REAL NOT NULL,
  segmento TEXT,   -- the limiares segment copied (exact, otherwise '*'); checked by trg_pre_registro_copia
  extensao_motivo TEXT CHECK(extensao_motivo IN('meio','sem_amostra') OR extensao_motivo IS NULL),
  orcamento_max_brl REAL NOT NULL DEFAULT 0, prazo_dias INTEGER NOT NULL, estendida INTEGER NOT NULL DEFAULT 0,
  resultado TEXT CHECK(resultado IN('confirmada','refutada','inconclusiva_sem_trafego','inconclusiva_amostra_parcial') OR resultado IS NULL),
  n_observado INTEGER, eventos_observados INTEGER, valor_observado REAL, ic_inf REAL, ic_sup REAL,
  aprendizado TEXT, criada_em TEXT NOT NULL DEFAULT (datetime('now')), fechada_em TEXT,
  CHECK(resultado IS NULL OR (fechada_em IS NOT NULL AND fechada_em GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]')));

-- Additive metrics: each row = the increment for one day or one reading (never cumulative). Daily peaks
-- (ccu_pico, salas_abertas_pico): each row = that day's value, on the day it refers to (SKILL.md 0.1).
CREATE TABLE metricas(experimento_id INTEGER NOT NULL REFERENCES experimentos(id), data TEXT NOT NULL,
  metrica TEXT NOT NULL CHECK(metrica IN('views','cliques','visitas_pagina','wishlists','plays','jogadores_novos','jogadores_d1',
    'jogadores_iniciaram','playtime_total_s','demo_jogadores','demo_wishlists','ccu_pico','installs','custo_brl','compartilhamentos',
    'sessoes','sessoes_grupo','sessoes_10min','convites_enviados','convites_aceitos','pagantes','receita_usd','reembolsos',
    'jogadas','jogadas_3min','webfit_notas_ok','aceite_plataforma','decisao_plataforma','salas_abertas_pico')),
  valor REAL NOT NULL, fonte TEXT NOT NULL CHECK(fonte IN('steamworks','portal_dashboard','roblox_dashboard','fortnite_api','publisher','loja','telemetria','anuncio_dono','dono_extrato')),
  run_id INTEGER REFERENCES runs(id), PRIMARY KEY(experimento_id,data,metrica));

CREATE TABLE receita_snapshots(ideia_id INTEGER NOT NULL REFERENCES ideias(id), data TEXT NOT NULL,
  receita_bruta_usd REAL, receita_liquida_usd REAL, plays INTEGER, copias INTEGER, fonte TEXT NOT NULL,
  PRIMARY KEY(ideia_id,data,fonte));   -- one row per idea, month and platform

CREATE TABLE gastos(id INTEGER PRIMARY KEY, data TEXT NOT NULL, valor_brl REAL NOT NULL,
  categoria TEXT NOT NULL CHECK(categoria IN('anuncio','plataforma','dominio','ferramenta','outro')),
  ideia_id INTEGER REFERENCES ideias(id), experimento_id INTEGER REFERENCES experimentos(id),
  prova_dono TEXT NOT NULL CHECK(length(prova_dono) >= 10), nota TEXT);

CREATE TABLE horas(id INTEGER PRIMARY KEY, ideia_id INTEGER NOT NULL REFERENCES ideias(id), data TEXT NOT NULL,
  horas REAL NOT NULL, tipo TEXT NOT NULL CHECK(tipo IN('validacao','construcao','manutencao','marketing')),
  prova_dono TEXT NOT NULL, nota TEXT);

CREATE TABLE benchmarks(id INTEGER PRIMARY KEY, metrica TEXT NOT NULL, segmento TEXT NOT NULL, valor REAL NOT NULL,
  unidade TEXT NOT NULL, source_url TEXT NOT NULL, data_fonte TEXT NOT NULL,
  tipo_fonte TEXT NOT NULL CHECK(tipo_fonte IN('primaria','secundaria')),
  confianca TEXT NOT NULL CHECK(confianca IN('alta','media','baixa')),
  usar_em_calculo INTEGER NOT NULL CHECK(usar_em_calculo IN(0,1)), nota TEXT, verificado_em TEXT NOT NULL,
  UNIQUE(metrica,segmento,verificado_em));
CREATE VIEW benchmarks_vigentes AS SELECT b.* FROM benchmarks b
  WHERE b.verificado_em = (SELECT MAX(verificado_em) FROM benchmarks x WHERE x.metrica=b.metrica AND x.segmento=b.segmento);

CREATE TABLE limiares(id INTEGER PRIMARY KEY, etapa TEXT NOT NULL, metrica TEXT NOT NULL, segmento TEXT NOT NULL,
  tipo_criterio TEXT NOT NULL CHECK(tipo_criterio IN('taxa','contagem','media','teto')),
  limiar_passa REAL NOT NULL, limiar_mata REAL NOT NULL, n_min INTEGER NOT NULL, eventos_min INTEGER NOT NULL,
  prazo_dias INTEGER NOT NULL, unidade_n TEXT NOT NULL, marco_inicio TEXT NOT NULL,
  sem_amostra_destino TEXT NOT NULL, mata_destino TEXT NOT NULL CHECK(mata_destino IN('morta','arquivada','congelada')),
  versao INTEGER NOT NULL, vigente_desde TEXT NOT NULL,
  origem TEXT NOT NULL CHECK(origem IN('heuristica','benchmark','calibrado')), ancora TEXT,
  UNIQUE(etapa,metrica,segmento,versao));

CREATE INDEX ix_sinais_coletado ON sinais(coletado_em);
CREATE INDEX ix_ideias_estado ON ideias(estado);

-- ===== Guards =====
-- Every idea is born in 'sinal'.
CREATE TRIGGER trg_ideia_nasce_sinal BEFORE INSERT ON ideias WHEN NEW.estado <> 'sinal'
BEGIN SELECT RAISE(ABORT,'ideia_nasce_em_sinal'); END;

-- Portfolio: up to 4 pre_teste, 2 em_teste, 1 em_construcao (limits fixed here; config only documents them).
CREATE TRIGGER trg_portfolio BEFORE UPDATE OF estado ON ideias
WHEN (NEW.estado='pre_teste' AND OLD.estado<>'pre_teste'
      AND (SELECT COUNT(*) FROM ideias WHERE estado='pre_teste' AND id<>NEW.id) >= 4)
  OR (NEW.estado='em_teste' AND OLD.estado<>'em_teste'
      AND (SELECT COUNT(*) FROM ideias WHERE estado='em_teste' AND id<>NEW.id) >= 2)
  OR (NEW.estado='em_construcao' AND OLD.estado<>'em_construcao'
      AND (SELECT COUNT(*) FROM ideias WHERE estado='em_construcao' AND id<>NEW.id) >= 1)
BEGIN SELECT RAISE(ABORT,'portfolio_cheio'); END;

-- A family takes at most 1 test/build slot.
CREATE TRIGGER trg_familia BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado IN ('pre_teste','em_teste','em_construcao') AND NEW.familia_id IS NOT NULL
 AND EXISTS(SELECT 1 FROM ideias WHERE familia_id=NEW.familia_id AND id<>NEW.id
            AND estado IN ('pre_teste','em_teste','validada','em_construcao'))
BEGIN SELECT RAISE(ABORT,'familia_ocupada'); END;

-- A state change requires a recent event with the right from/to.
CREATE TRIGGER trg_evento BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado<>OLD.estado AND NOT EXISTS(SELECT 1 FROM ideia_eventos e
  WHERE e.id = (SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)
    AND e.de=OLD.estado AND e.para=NEW.estado AND e.em>=datetime('now','-10 minutes'))
BEGIN SELECT RAISE(ABORT,'sem_ideia_evento'); END;

-- Dead/archived only returns to 'candidata', with a 'REABERTA:' event; serious deaths only by the owner; the routine reopens once per idea.
CREATE TRIGGER trg_reabertura BEFORE UPDATE OF estado ON ideias
WHEN OLD.estado IN ('morta','arquivada') AND NEW.estado NOT IN ('morta','arquivada')
 AND ( NEW.estado <> 'candidata'
    OR NOT EXISTS(SELECT 1 FROM ideia_eventos e WHERE e.id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)
                  AND e.motivo LIKE 'REABERTA:%')
    OR (OLD.motivo_morte IN ('teste_reprovado','advogado_do_diabo','clone_legal','excluida_por_regra')
        AND (SELECT ator FROM ideia_eventos WHERE id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)) <> 'dono')
    OR ( (SELECT ator FROM ideia_eventos WHERE id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)) = 'rotina'
         AND (SELECT COUNT(*) FROM ideia_eventos WHERE ideia_id=NEW.id AND motivo LIKE 'REABERTA:%' AND ator='rotina'
              AND de IN ('morta','arquivada')) > 1 ) )
BEGIN SELECT RAISE(ABORT,'reabertura_proibida'); END;

-- Family is assigned at the gate and never changes; no family, no test.
CREATE TRIGGER trg_familia_fixa BEFORE UPDATE OF familia_id ON ideias
WHEN OLD.familia_id IS NOT NULL AND NEW.familia_id IS NOT OLD.familia_id
BEGIN SELECT RAISE(ABORT,'familia_id_imutavel'); END;

CREATE TRIGGER trg_familia_obrigatoria BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado IN ('pre_teste','em_teste','em_construcao') AND NEW.familia_id IS NULL
BEGIN SELECT RAISE(ABORT,'sem_familia'); END;

-- Family with a dead/archived idea: entering test/build requires a REABERTA: event on entry.
-- Serious death -> owner's REABERTA. Non-serious -> REABERTA (routine at most 1 per family).
CREATE TRIGGER trg_familia_cemiterio BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado IN ('pre_teste','em_teste','em_construcao') AND OLD.estado IN ('candidata','pre_teste')
 AND (
  ( EXISTS(SELECT 1 FROM ideias m WHERE m.familia_id=NEW.familia_id AND m.id<NEW.id AND m.estado='morta'
           AND m.motivo_morte IN ('teste_reprovado','advogado_do_diabo','clone_legal','excluida_por_regra'))
    -- one owner REABERTA per entry: it covers candidata->pre_teste->em_teste (since the last entry in candidata and
    -- after the sibling's death)
    AND NOT EXISTS(SELECT 1 FROM ideia_eventos e WHERE e.ideia_id=NEW.id AND e.ator='dono' AND e.motivo LIKE 'REABERTA:%'
           AND e.id >= (SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de<>'candidata')
           AND e.id > (SELECT MAX(d.id) FROM ideia_eventos d JOIN ideias m ON m.id=d.ideia_id
                       WHERE m.familia_id=NEW.familia_id AND m.id<NEW.id AND d.para='morta')) )
  OR
  ( EXISTS(SELECT 1 FROM ideias m WHERE m.familia_id=NEW.familia_id AND m.id<NEW.id AND m.estado IN ('morta','arquivada')
           AND (m.motivo_morte IS NULL OR m.motivo_morte NOT IN ('teste_reprovado','advogado_do_diabo','clone_legal','excluida_por_regra'))
           -- a game that was launched and later archived by E5 is not a graveyard entry, nor is an operational archive
           AND NOT EXISTS(SELECT 1 FROM ideia_eventos l WHERE l.ideia_id=m.id AND l.para='lancada')
           AND NOT (m.estado='arquivada' AND m.arquivamento IS 'operacional'))
    AND OLD.estado IN ('candidata','pre_teste')
    -- an owner REABERTA since the idea's last entry in candidata covers its whole entry (as in the serious branch)
    AND NOT EXISTS(SELECT 1 FROM ideia_eventos e WHERE e.ideia_id=NEW.id AND e.ator='dono' AND e.motivo LIKE 'REABERTA:%'
                   AND e.id >= (SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de<>'candidata'))
    AND ( NOT EXISTS(SELECT 1 FROM ideia_eventos e WHERE e.id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)
                     AND e.motivo LIKE 'REABERTA:%')
       OR ( (SELECT ator FROM ideia_eventos WHERE id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)) = 'rotina'
            AND (SELECT COUNT(DISTINCT e.ideia_id) FROM ideia_eventos e JOIN ideias i2 ON i2.id=e.ideia_id
                 WHERE i2.familia_id=NEW.familia_id AND e.motivo LIKE 'REABERTA:%' AND e.ator='rotina'
                   AND e.de IN ('candidata','pre_teste') AND e.para IN ('pre_teste','em_teste','em_construcao')) > 1 ) ) )
 )
BEGIN SELECT RAISE(ABORT,'familia_no_cemiterio'); END;

-- When the family is first written: requires genero_central; must be the best eligible family
-- (most matching columns, tie -> lowest familia_id) whenever any family matches 2 of 3.
CREATE VIEW v_familia_match AS
SELECT n.id AS nova, o.id AS outra, o.familia_id AS familia,
 ( COALESCE(o.genero_central = n.genero_central, 0)
 + ((SELECT COUNT(*) FROM ideia_concorrentes a JOIN ideia_concorrentes b ON b.concorrente_id=a.concorrente_id
     JOIN concorrentes k ON k.id=a.concorrente_id
     WHERE a.ideia_id=n.id AND b.ideia_id=o.id AND k.proprio_ideia_id IS NULL) >= 1)   -- an own game is not a shared rival
 + COALESCE(1.0*(SELECT COUNT(*) FROM evidencias a JOIN evidencias b ON b.sinal_id=a.sinal_id JOIN sinais s ON s.id=a.sinal_id
     WHERE a.ideia_id=n.id AND b.ideia_id=o.id AND s.tipo IN ('hit_plataforma','arbitragem','jam_mecanica','concorrente','reclamacao'))
     / NULLIF(MIN((SELECT COUNT(*) FROM evidencias e JOIN sinais s ON s.id=e.sinal_id WHERE e.ideia_id=n.id
                   AND s.tipo IN ('hit_plataforma','arbitragem','jam_mecanica','concorrente','reclamacao')),
                  (SELECT COUNT(*) FROM evidencias e JOIN sinais s ON s.id=e.sinal_id WHERE e.ideia_id=o.id
                   AND s.tipo IN ('hit_plataforma','arbitragem','jam_mecanica','concorrente','reclamacao'))),0) >= 0.5, 0)
 ) AS colunas
FROM ideias n JOIN ideias o ON o.id <> n.id AND o.familia_id IS NOT NULL
  AND NOT (o.estado='arquivada' AND o.arquivamento IS 'operacional' AND COALESCE(o.reabrir_se,'') LIKE 'recriada como ideia#%')
  -- older ideas, plus newer ones still alive (an older idea that waited in 'sinal' joins its newer sibling's family);
  -- entry checks use only older ideas (trg_familia_na_entrada)
  AND (o.id < n.id OR o.estado NOT IN ('morta','arquivada'));

CREATE TRIGGER trg_familia_escolha BEFORE UPDATE OF familia_id ON ideias
WHEN OLD.familia_id IS NULL AND NEW.familia_id IS NOT NULL AND (
  NEW.genero_central IS NULL
  OR ( EXISTS(SELECT 1 FROM v_familia_match WHERE nova=NEW.id AND colunas >= 2)
       AND NEW.familia_id <> (SELECT familia FROM v_familia_match WHERE nova=NEW.id AND colunas >= 2
                              ORDER BY colunas DESC, familia ASC LIMIT 1) ))
BEGIN SELECT RAISE(ABORT,'familia_errada'); END;

-- After the family is set, the core genre cannot change (prevents escaping the graveyard by relabeling).
CREATE TRIGGER trg_genero_fixo BEFORE UPDATE OF genero_central ON ideias
WHEN OLD.familia_id IS NOT NULL AND NEW.genero_central IS NOT OLD.genero_central
BEGIN SELECT RAISE(ABORT,'genero_imutavel_apos_familia'); END;

-- Multiplayer that depends on a queue is forbidden; a public room list starts off.
CREATE TRIGGER trg_lista_publica_padrao BEFORE INSERT ON ideias WHEN NEW.lista_publica <> 0
BEGIN SELECT RAISE(ABORT,'lista_publica_comeca_desligada'); END;

-- A serious death motive cannot be changed (prevents "laundering" the death).
CREATE TRIGGER trg_morte_imutavel BEFORE UPDATE OF motivo_morte ON ideias
WHEN OLD.estado IN ('morta','arquivada') AND NEW.estado=OLD.estado AND NEW.motivo_morte IS NOT OLD.motivo_morte
 AND OLD.motivo_morte IN ('teste_reprovado','advogado_do_diabo','clone_legal','excluida_por_regra')
BEGIN SELECT RAISE(ABORT,'motivo_morte_grave_imutavel'); END;

-- Exploration quota: 1 active and 1 per month.
CREATE TRIGGER trg_exploracao BEFORE UPDATE OF exploracao ON ideias
WHEN NEW.exploracao=1 AND OLD.exploracao=0 AND (
  NEW.exploracao_em IS NULL OR NEW.exploracao_em <> date('now')
  OR EXISTS(SELECT 1 FROM ideias WHERE exploracao=1 AND id<>NEW.id
            AND estado IN ('candidata','pre_teste','em_teste','validada','em_construcao'))
  OR (SELECT COUNT(*) FROM ideias x WHERE x.exploracao=1 AND x.id<>NEW.id
            AND strftime('%Y-%m',x.exploracao_em)=strftime('%Y-%m',NEW.exploracao_em)
            AND (x.estado IN ('candidata','pre_teste','em_teste','validada','em_construcao','lancada')
                 OR EXISTS(SELECT 1 FROM ideia_eventos e WHERE e.ideia_id=x.id AND e.para='em_teste')))
     >= COALESCE((SELECT CAST(valor AS INTEGER) FROM config WHERE chave='exploracao_por_mes'), 1))
BEGIN SELECT RAISE(ABORT,'cota_exploracao'); END;

-- Only the transitions of SKILL.md section 10.1 (any state may go to 'morta').
CREATE TRIGGER trg_transicao_valida BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado<>OLD.estado AND NEW.estado<>'morta' AND NOT (
 (OLD.estado='sinal' AND NEW.estado IN ('candidata','arquivada')) OR
 (OLD.estado='candidata' AND NEW.estado IN ('pre_teste','em_teste','em_construcao','arquivada','congelada')) OR
 (OLD.estado='pre_teste' AND NEW.estado IN ('em_teste','em_construcao','arquivada','congelada')) OR
 (OLD.estado='em_teste' AND NEW.estado IN ('validada','arquivada','congelada')) OR
 (OLD.estado='validada' AND NEW.estado IN ('em_construcao','arquivada')) OR
 (OLD.estado='em_construcao' AND NEW.estado IN ('lancada','congelada')) OR
 (OLD.estado='lancada' AND NEW.estado IN ('congelada','arquivada')) OR
 (OLD.estado='congelada' AND NEW.estado IN ('lancada','candidata','arquivada','em_construcao')) OR
 (OLD.estado IN ('morta','arquivada') AND NEW.estado='candidata'))
BEGIN SELECT RAISE(ABORT,'transicao_fora_da_tabela'); END;

-- Owner transitions require proof (literal quote of the message).
CREATE TRIGGER trg_ator_dono BEFORE INSERT ON ideia_eventos
WHEN NEW.ator='dono' AND (NEW.prova_dono IS NULL OR length(NEW.prova_dono) < 10)
BEGIN SELECT RAISE(ABORT,'dono_sem_prova'); END;

CREATE TRIGGER trg_transicao_do_dono BEFORE INSERT ON ideia_eventos
WHEN NEW.para IN ('em_construcao','lancada') AND NEW.ator <> 'dono'
BEGIN SELECT RAISE(ABORT,'transicao_exige_dono'); END;

-- Target price locks once a test has started.
CREATE TRIGGER trg_preco_fixo BEFORE UPDATE OF preco_alvo ON ideias
WHEN NEW.preco_alvo IS NOT OLD.preco_alvo
 AND EXISTS(SELECT 1 FROM experimentos WHERE ideia_id=NEW.id AND estado IN ('rodando','encerrado','abortado'))
BEGIN SELECT RAISE(ABORT,'preco_alvo_travado_apos_teste'); END;

-- An experiment can only be aborted after its hypotheses are closed (prevents erasing a defeat).
CREATE TRIGGER trg_abortar_com_hipotese_aberta BEFORE UPDATE OF estado ON experimentos
WHEN NEW.estado='abortado' AND OLD.estado IN ('planejado','rodando')
 AND EXISTS(SELECT 1 FROM hipoteses WHERE experimento_id=NEW.id AND resultado IS NULL)
BEGIN SELECT RAISE(ABORT,'feche_as_hipoteses_antes_de_abortar'); END;

-- Exploration: born 0, never back to 0; reopening an exploration requires the owner and no other active one.
CREATE TRIGGER trg_exploracao_nasce_zero BEFORE INSERT ON ideias WHEN NEW.exploracao<>0
BEGIN SELECT RAISE(ABORT,'exploracao_so_por_update'); END;

CREATE TRIGGER trg_exploracao_irreversivel BEFORE UPDATE OF exploracao ON ideias
WHEN OLD.exploracao=1 AND NEW.exploracao=0
BEGIN SELECT RAISE(ABORT,'exploracao_irreversivel'); END;

CREATE TRIGGER trg_exploracao_reaberta BEFORE UPDATE OF estado ON ideias
WHEN NEW.exploracao=1 AND OLD.estado IN ('morta','arquivada','congelada') AND NEW.estado='candidata'
 AND ( EXISTS(SELECT 1 FROM ideias WHERE exploracao=1 AND id<>NEW.id AND estado IN ('candidata','pre_teste','em_teste','validada','em_construcao'))
    OR (OLD.estado IN ('morta','arquivada')
        AND (SELECT ator FROM ideia_eventos WHERE id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id))<>'dono') )
BEGIN SELECT RAISE(ABORT,'cota_exploracao_reabertura'); END;

-- Family is born NULL (assigned at the gate, checked by trg_familia_escolha).
CREATE TRIGGER trg_familia_nasce_nula BEFORE INSERT ON ideias WHEN NEW.familia_id IS NOT NULL
BEGIN SELECT RAISE(ABORT,'familia_so_no_gate'); END;

-- The public room list can only be switched on for a launched game (density is checked by the routine, section 6.4).
CREATE TRIGGER trg_lista_publica_so_lancada BEFORE UPDATE OF lista_publica ON ideias
WHEN NEW.lista_publica = 1 AND OLD.lista_publica = 0 AND NEW.estado <> 'lancada'
BEGIN SELECT RAISE(ABORT,'lista_publica_so_com_jogo_lancado'); END;

-- No build without an engine chosen per idea, with a justification (engine matrix in the prompt).
CREATE TRIGGER trg_engine_antes_construcao BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='em_construcao' AND OLD.estado<>'em_construcao'
BEGIN
  SELECT RAISE(ABORT,'engine_obrigatoria') WHERE COALESCE(TRIM(NEW.engine),'')='' OR COALESCE(TRIM(NEW.engine_justificativa),'')='';
  SELECT RAISE(ABORT,'ficha_incompleta') WHERE NEW.trilha IS NULL OR NEW.plataforma IS NULL OR NEW.modo IS NULL
    OR NEW.hook IS NULL OR NEW.twist IS NULL OR NEW.horas_estimadas IS NULL OR NEW.loot_box IS NULL OR NEW.chat_livre IS NULL
    OR NEW.ai_runtime IS NULL OR NEW.loop_idle IS NULL;
END;

-- At most 1 Steam bet (track S) in test, validated or in build at a time (it is the expensive bet).
CREATE TRIGGER trg_uma_aposta_steam BEFORE UPDATE OF estado ON ideias
WHEN NEW.trilha='S' AND NEW.estado IN ('em_teste','validada','em_construcao')
 AND OLD.estado NOT IN ('em_teste','validada','em_construcao')
 AND EXISTS(SELECT 1 FROM ideias WHERE trilha='S' AND id<>NEW.id AND estado IN ('em_teste','validada','em_construcao'))
BEGIN SELECT RAISE(ABORT,'uma_aposta_steam'); END;

-- The track is chosen at the gate and locks once the idea leaves 'candidata' (prevents relabeling S -> W to dodge limits).
CREATE TRIGGER trg_trilha_fixa BEFORE UPDATE OF trilha ON ideias
WHEN NEW.trilha IS NOT OLD.trilha AND ( OLD.estado NOT IN ('sinal','candidata')
  OR EXISTS(SELECT 1 FROM ideia_eventos WHERE ideia_id=NEW.id AND de='candidata' AND para NOT IN ('candidata','morta','arquivada')) )
BEGIN SELECT RAISE(ABORT,'trilha_imutavel'); END;

-- An idea with loot box or free chat is recorded truthfully and can only die with excluida_por_regra (section 5, cut 1).
CREATE TRIGGER trg_proibido BEFORE UPDATE OF estado ON ideias
WHEN (NEW.loot_box=1 OR NEW.chat_livre=1 OR (NEW.ai_runtime=1 AND length(COALESCE(TRIM(NEW.plano_moderacao),'')) < 80)) AND NEW.estado<>OLD.estado
 AND ( NEW.estado NOT IN ('candidata','morta')
    OR (NEW.estado='morta' AND NEW.motivo_morte IS NOT 'excluida_por_regra') )
BEGIN SELECT RAISE(ABORT,'excluida_por_regra'); END;

-- No test without the sheet (gate, desk and score recorded) and, for em_teste/validada, the devil's advocate (9.1).
CREATE TRIGGER trg_ficha_antes_do_teste BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado IN ('pre_teste','em_teste','validada') AND NEW.estado<>OLD.estado
BEGIN
  SELECT RAISE(ABORT,'ficha_incompleta') WHERE NEW.trilha IS NULL OR NEW.plataforma IS NULL OR NEW.modo IS NULL
    OR NEW.hook IS NULL OR NEW.horas_estimadas IS NULL OR NEW.ai_arte_visivel IS NULL
    OR NEW.twist IS NULL OR NEW.twist NOT LIKE 'É %, mas %, de modo que %'
    OR NEW.score_json IS NULL OR NOT json_valid(NEW.score_json)
    OR json_type(NEW.score_json,'$.demanda') IS NULL OR json_type(NEW.score_json,'$.twist') IS NULL
    OR json_type(NEW.score_json,'$.canal') IS NULL OR json_type(NEW.score_json,'$.execucao') IS NULL
    OR json_type(NEW.score_json,'$.economia') IS NULL
    OR json_type(NEW.score_json,'$.demanda') NOT IN ('integer','real') OR json_type(NEW.score_json,'$.twist') NOT IN ('integer','real')
    OR json_type(NEW.score_json,'$.canal') NOT IN ('integer','real') OR json_type(NEW.score_json,'$.execucao') NOT IN ('integer','real')
    OR json_type(NEW.score_json,'$.economia') NOT IN ('integer','real')
    -- every axis on the 0/4/7/10 scale and at its minimum (9.2)
    OR json_extract(NEW.score_json,'$.demanda') NOT IN (0,4,7,10) OR json_extract(NEW.score_json,'$.twist') NOT IN (0,4,7,10)
    OR json_extract(NEW.score_json,'$.canal') NOT IN (0,4,7,10) OR json_extract(NEW.score_json,'$.execucao') NOT IN (0,4,7,10)
    OR json_extract(NEW.score_json,'$.economia') NOT IN (0,4,7,10)
    -- at validada the idea's own confirmed stages are its demand (6.1 a): a re-graded proxy does not undo them
    OR (NEW.estado IN ('pre_teste','em_teste') AND json_extract(NEW.score_json,'$.demanda') < (CASE WHEN NEW.exploracao=1 THEN 4 ELSE 7 END))
    OR json_extract(NEW.score_json,'$.twist') < 7 OR json_extract(NEW.score_json,'$.canal') < 7
    OR json_extract(NEW.score_json,'$.execucao') < 7 OR json_extract(NEW.score_json,'$.economia') < 4
    -- negative adjustments the database can derive count toward the minimum (9.2): party_host -2 Channel, server -2 Execution
    OR (NEW.modo='party_host' AND json_extract(NEW.score_json,'$.canal') - 2 < 7)
    OR (NEW.servidor_usd_mes_1000ccu > (SELECT CAST(valor AS REAL) FROM config WHERE chave='servidor_usd_mes_penalidade')
        AND json_extract(NEW.score_json,'$.execucao') - 2 < 7)
    -- hours within the track's prototype cap (cut 7)
    OR NEW.horas_estimadas > COALESCE((SELECT CAST(valor AS REAL) FROM config WHERE chave='prototipo_horas_max_' || lower(NEW.trilha)), 0)
    -- track and platform agree; exploration label and flag agree
    OR NOT ((NEW.trilha='W' AND NEW.plataforma='web') OR (NEW.trilha='S' AND NEW.plataforma='steam')
            OR (NEW.trilha='M' AND NEW.plataforma='mobile') OR (NEW.trilha='R' AND NEW.plataforma IN ('roblox','uefn')))
    OR (NEW.fonte_ideia IS 'exploracao') <> (NEW.exploracao=1)
    OR NEW.loot_box IS NULL OR NEW.chat_livre IS NULL OR NEW.ai_runtime IS NULL OR NEW.loop_idle IS NULL
    OR (NEW.modo IS 'plataforma_social' AND NEW.trilha IS NOT 'R');
  -- a detected trend leader linked to the idea (any role) must be registered before any test (4.4)
  SELECT RAISE(ABORT,'tendencia_nao_registrada') WHERE EXISTS(SELECT 1 FROM ideia_concorrentes ic
    JOIN v_tendencia_detectada v ON v.concorrente_id=ic.concorrente_id WHERE ic.ideia_id=NEW.id AND ic.papel='referencia'
    AND NOT EXISTS(SELECT 1 FROM tendencias t WHERE t.loja=v.loja AND t.id_loja=v.id_loja));
  -- a game named in the twist (its X) is the reference, never a rival (prevents relabeling a hype as a rival)
  SELECT RAISE(ABORT,'referencia_no_twist') WHERE EXISTS(SELECT 1 FROM ideia_concorrentes ic
    JOIN concorrentes c ON c.id=ic.concorrente_id WHERE ic.ideia_id=NEW.id AND ic.papel='rival'
    -- the rival's base name (store subtitle or edition after ':' or ' - ' cut) appearing in the twist
    AND length(rtrim(CASE WHEN instr(c.nome,':') > 0 THEN substr(c.nome,1,instr(c.nome,':')-1)
                          WHEN instr(c.nome,' - ') > 0 THEN substr(c.nome,1,instr(c.nome,' - ')-1) ELSE c.nome END)) >= 3
    -- whole words only (a short rival like 'Raft' does not match 'crafting')
    AND instr((' ' || replace(replace(replace(replace(replace(replace(replace(replace(replace(lower(NEW.twist),',',' '),'.',' '),':',' '),';',' '),'!',' '),'?',' '),'(',' '),')',' '),'"',' ') || ' '), (' ' || replace(replace(replace(replace(replace(replace(replace(replace(replace(lower(rtrim(CASE WHEN instr(c.nome,':') > 0 THEN substr(c.nome,1,instr(c.nome,':')-1)
                                                 WHEN instr(c.nome,' - ') > 0 THEN substr(c.nome,1,instr(c.nome,' - ')-1) ELSE c.nome END)),',',' '),'.',' '),':',' '),';',' '),'!',' '),'?',' '),'(',' '),')',' '),'"',' ') || ' ')) > 0
    -- a rival whose name is part of the reference's name (predecessor, franchise) is not the X
    AND NOT EXISTS(SELECT 1 FROM ideia_concorrentes r JOIN concorrentes rc ON rc.id=r.concorrente_id
                   WHERE r.ideia_id=NEW.id AND r.papel='referencia' AND instr(lower(rc.nome), lower(c.nome)) > 0
                   AND instr(lower(NEW.twist), lower(rc.nome)) > 0));
  -- every linked competitor needs its release date (trend rule, 4.4)
  SELECT RAISE(ABORT,'concorrente_sem_lancado_em') WHERE EXISTS(SELECT 1 FROM ideia_concorrentes ic
    JOIN concorrentes c ON c.id=ic.concorrente_id WHERE ic.ideia_id=NEW.id AND c.lancado_em IS NULL);
  -- the Steam bet needs an own launched web game or the owner's release (7.1)
  SELECT RAISE(ABORT,'aposta_steam_nao_liberada') WHERE NEW.trilha='S' AND NEW.estado IN ('pre_teste','em_teste')
    AND NOT EXISTS(SELECT 1 FROM ideias w JOIN ideia_eventos e ON e.ideia_id=w.id WHERE w.trilha='W' AND e.para='lancada')
    AND NOT EXISTS(SELECT 1 FROM ideia_eventos e WHERE e.ideia_id=NEW.id AND e.ator='dono'
                   AND lower(replace(e.prova_dono,'“','"') || ' ') GLOB ('"libero a aposta steam da ideia#' || NEW.id || '[^0-9]*'));
  SELECT RAISE(ABORT,'advogado_obrigatorio') WHERE NEW.estado IN ('em_teste','validada')
    AND (NEW.advogado_em IS NULL OR NEW.advogado_em > datetime('now','+5 seconds'));
  SELECT RAISE(ABORT,'exploracao_sem_jam') WHERE NEW.exploracao=1 AND (NEW.trilha IS NOT 'W'
    OR NOT EXISTS(SELECT 1 FROM evidencias e JOIN sinais s ON s.id=e.sinal_id WHERE e.ideia_id=NEW.id
                  AND e.polaridade=1 AND s.tipo='jam_mecanica'));
  SELECT RAISE(ABORT,'referencia_nao_ligada') WHERE NEW.exploracao IS NOT 1 AND NOT EXISTS(
    SELECT 1 FROM ideia_concorrentes WHERE ideia_id=NEW.id AND papel='referencia');
  SELECT RAISE(ABORT,'sem_evidencia') WHERE NOT EXISTS(SELECT 1 FROM evidencias WHERE ideia_id=NEW.id AND polaridade=1)
    -- a port or graduation of an own launched game carries its own measured data instead of a collected signal
    AND NOT EXISTS(SELECT 1 FROM ideia_concorrentes ic JOIN concorrentes c ON c.id=ic.concorrente_id
                   WHERE ic.ideia_id=NEW.id AND ic.papel='referencia' AND c.proprio_ideia_id IS NOT NULL);
  -- a rival needs a name: it is compared with the twist (referencia_no_twist)
  SELECT RAISE(ABORT,'concorrente_sem_nome') WHERE EXISTS(SELECT 1 FROM ideia_concorrentes ic JOIN concorrentes c
    ON c.id=ic.concorrente_id WHERE ic.ideia_id=NEW.id AND ic.papel='rival' AND length(COALESCE(c.nome,'')) < 3);
  SELECT RAISE(ABORT,'tendencia_sem_janela_aberta') WHERE NEW.estado IN ('pre_teste','em_teste') AND NEW.fonte_ideia IS 'tendencia' AND NOT EXISTS(
    SELECT 1 FROM ideia_concorrentes ic JOIN v_tendencia_viva v ON v.concorrente_id=ic.concorrente_id
    JOIN tendencias t ON t.loja=v.loja AND t.id_loja=v.id_loja AND t.status='aberta'
      AND t.detectada_em >= date('now','-' || (COALESCE((SELECT CAST(valor AS INTEGER) FROM config WHERE chave='tendencia_janela_semanas'),6) * 7) || ' days')   -- open AND inside its window (4.4), even if nobody closed it
    WHERE ic.ideia_id=NEW.id AND ic.papel='referencia');
  -- a recent game on a store with a per-game numeric source must have one popularity number before an idea linked to
  -- it enters a test (a price-only snapshot cannot tell a hype from a flop)
  SELECT RAISE(ABORT,'popularidade_indeterminada') WHERE NEW.estado IN ('pre_teste','em_teste') AND EXISTS(
    SELECT 1 FROM ideia_concorrentes ic JOIN concorrentes c ON c.id=ic.concorrente_id
    WHERE ic.ideia_id=NEW.id AND c.proprio_ideia_id IS NULL AND c.loja IN ('steam','roblox','uefn','appstore')
      AND c.lancado_em > date('now','-120 days')
      AND NOT EXISTS(SELECT 1 FROM concorrente_snapshots s WHERE s.concorrente_id=c.id
                     AND (COALESCE(s.reviews_total, s.ccu, s.plays, s.ratings_count, s.installs_min, s.favoritos) IS NOT NULL
                          OR s.rank_lista IN ('most-played','top-sellers','top-trending','hot','featured')
                          -- the Fortnite Data API returns null below 5 unique players: that reading is 'not popular'
                          OR c.loja = 'uefn')));
  SELECT RAISE(ABORT,'tendencia_fora_do_escopo') WHERE NEW.estado IN ('pre_teste','em_teste') AND NEW.fonte_ideia IS 'tendencia' AND (NEW.plataforma NOT IN ('web','roblox')
    OR (NEW.plataforma='web' AND NEW.exclusividade IS NOT 'crazygames_agregadores')   -- the Poki path does not fit the window (4.4)
    OR NEW.horas_estimadas > (SELECT CAST(valor AS REAL) FROM config WHERE chave='horas_semana_dono_min')
                             * (SELECT CAST(valor AS REAL) FROM config WHERE chave='tendencia_mvp_dias_max') / 7.0);
  -- validada needs an advocate run after the idea entered em_teste
  SELECT RAISE(ABORT,'advogado_obrigatorio') WHERE NEW.estado='validada'
    AND NEW.advogado_em <= (SELECT MAX(em) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='em_teste' AND de<>'em_teste');
END;

-- Trend rule (section 4.4), one definition: a game released < 120 days ago (not the owner's, not an itch jam entry).
-- It becomes a trend leader when it is also popular in a snapshot of the last 30 days: a popularity list (not 'new')
-- or reviews/CCU/plays above the config floors (v_tendencia_detectada);
-- every guard expires when the game turns 120 days old. Only the reference link counts (a game named in the twist
-- must be linked as the reference: trg_ficha 'referencia_no_twist'); a rival that is a live hype is a scored risk.
-- Popularity of a snapshot (shared by both views below).
CREATE VIEW v_snapshot_popular AS
SELECT s.concorrente_id, s.data FROM concorrente_snapshots s
WHERE s.rank_lista IN ('most-played','top-sellers','top-trending','hot','featured')
   OR s.reviews_total >= (SELECT CAST(valor AS REAL) FROM config WHERE chave='tendencia_reviews_min')
   OR s.ccu >= (SELECT CAST(valor AS REAL) FROM config WHERE chave='tendencia_ccu_min')
   -- plays/favorites are lifetime totals on Roblox/UEFN (visits since launch): not a popularity floor there
   OR (s.plays >= (SELECT CAST(valor AS REAL) FROM config WHERE chave='tendencia_plays_min')
       AND (SELECT loja FROM concorrentes WHERE id=s.concorrente_id) NOT IN ('roblox','uefn'))
   OR s.ratings_count >= (SELECT CAST(valor AS REAL) FROM config WHERE chave='tendencia_ratings_min')
   OR s.installs_min >= (SELECT CAST(valor AS REAL) FROM config WHERE chave='tendencia_installs_min')
   OR (s.favoritos >= (SELECT CAST(valor AS REAL) FROM config WHERE chave='tendencia_favoritos_min')
       AND (SELECT loja FROM concorrentes WHERE id=s.concorrente_id) NOT IN ('roblox','uefn'));
-- Age of a trend = from the release; on Roblox/UEFN (hits peak months after release) from the first popular snapshot,
-- for games released in the last 365 days (an old classic seen popular today is not a trend).
CREATE VIEW v_tendencia_viva AS
SELECT c.id AS concorrente_id, c.loja, c.id_loja FROM concorrentes c
WHERE c.proprio_ideia_id IS NULL AND c.loja <> 'itch' AND c.lancado_em_incerto = 0
  AND ( c.lancado_em > date('now','-120 days')
     OR (c.loja IN ('roblox','uefn') AND c.lancado_em > date('now','-365 days')
         AND (SELECT MIN(data) FROM v_snapshot_popular p WHERE p.concorrente_id=c.id) > date('now','-120 days')
         -- the rise was observed: a non-popular snapshot exists before the first popular one
         AND (EXISTS(SELECT 1 FROM concorrente_snapshots s WHERE s.concorrente_id=c.id
                    AND s.data < (SELECT MIN(data) FROM v_snapshot_popular p WHERE p.concorrente_id=c.id))
              -- top-trending itself ranks the week's relative DAU rise
              OR EXISTS(SELECT 1 FROM concorrente_snapshots s WHERE s.concorrente_id=c.id AND s.rank_lista='top-trending'
                        AND s.data > date('now','-120 days')))) );
CREATE VIEW v_tendencia_detectada AS
SELECT v.* FROM v_tendencia_viva v
WHERE EXISTS(SELECT 1 FROM v_snapshot_popular p WHERE p.concorrente_id=v.concorrente_id AND p.data >= date('now','-30 days'));
CREATE TRIGGER trg_tendencia BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado IN ('pre_teste','em_teste') AND NEW.estado<>OLD.estado
 AND EXISTS(SELECT 1 FROM ideia_concorrentes ic JOIN v_tendencia_viva v ON v.concorrente_id=ic.concorrente_id
            JOIN tendencias t ON t.loja=v.loja AND t.id_loja=v.id_loja WHERE ic.ideia_id=NEW.id AND ic.papel='referencia')
 AND NEW.fonte_ideia IS NOT 'tendencia'
BEGIN SELECT RAISE(ABORT,'fonte_ideia_tendencia'); END;
CREATE TRIGGER trg_tendencia_fechada BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado IN ('pre_teste','em_teste') AND NEW.estado<>OLD.estado
 AND EXISTS(SELECT 1 FROM ideia_concorrentes ic JOIN v_tendencia_viva v ON v.concorrente_id=ic.concorrente_id
            JOIN tendencias t ON t.loja=v.loja AND t.id_loja=v.id_loja WHERE ic.ideia_id=NEW.id AND ic.papel='referencia' AND t.status='fechada')
BEGIN SELECT RAISE(ABORT,'janela_fechada'); END;

-- A loot box / free chat flag only goes back to 0 through a FIX-FIRST event that removes the feature (section 5).
CREATE TRIGGER trg_flag_proibida_fix_first BEFORE UPDATE OF loot_box, chat_livre, ai_runtime ON ideias
WHEN ((OLD.loot_box=1 AND NEW.loot_box IS NOT 1) OR (OLD.chat_livre=1 AND NEW.chat_livre IS NOT 1)
      OR (OLD.ai_runtime=1 AND NEW.ai_runtime IS NOT 1))
 AND NOT ( OLD.estado='candidata' AND EXISTS(SELECT 1 FROM ideia_eventos e
           WHERE e.id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id) AND e.motivo LIKE 'FIX-FIRST:%') )
BEGIN SELECT RAISE(ABORT,'flag_proibida_so_com_fix_first'); END;

-- An owner event must quote the idea: 'ideia#<id>' not followed by a digit (lib.prova_existe still runs before COMMIT).
CREATE TRIGGER trg_prova_cita_ideia BEFORE INSERT ON ideia_eventos
WHEN NEW.ator='dono' AND lower(NEW.prova_dono || ' ') NOT GLOB ('*ideia#' || NEW.ideia_id || '[^0-9]*')
BEGIN SELECT RAISE(ABORT,'prova_sem_ideia'); END;

-- Death after a refuted hypothesis of the current test is always teste_reprovado (no laundering into a mild motive).
-- "Current" = the latest decided experiment (a Poki refusal overcome by a passed CrazyGames stage no longer counts).
CREATE TRIGGER trg_morte_por_teste BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='morta' AND OLD.estado<>'morta'
 AND NEW.motivo_morte NOT IN ('teste_reprovado','advogado_do_diabo','clone_legal','excluida_por_regra')
 AND EXISTS(SELECT 1 FROM hipoteses h WHERE h.ideia_id=NEW.id AND h.resultado='refutada'
            AND h.experimento_id = (SELECT MAX(hh.experimento_id) FROM hipoteses hh JOIN experimentos xx ON xx.id=hh.experimento_id
                                    WHERE hh.ideia_id=NEW.id AND hh.resultado IN ('confirmada','refutada')   -- an inconclusive-only experiment (no reading) never hides a refutation
                                    AND COALESCE(xx.decisao,'') NOT IN ('planejado_vencido','orfao','iterado','abortado'))
            AND h.fechada_em >= COALESCE((SELECT MAX(em) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0'))
BEGIN SELECT RAISE(ABORT,'morte_por_teste_exige_teste_reprovado'); END;

-- congelada -> candidata (reactivation) happens once per idea.
CREATE TRIGGER trg_reativacao_unica BEFORE UPDATE OF estado ON ideias
WHEN OLD.estado='congelada' AND NEW.estado='candidata'
 AND (SELECT COUNT(*) FROM ideia_eventos WHERE ideia_id=NEW.id AND de='congelada' AND para='candidata') > 1
BEGIN SELECT RAISE(ABORT,'reativacao_unica'); END;

-- The family is re-checked when the idea enters a test (not at the build approval of a validated idea): links added after the family was written count too.
CREATE TRIGGER trg_familia_na_entrada BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado IN ('pre_teste','em_teste') AND NEW.estado<>OLD.estado
 AND EXISTS(SELECT 1 FROM v_familia_match WHERE nova=NEW.id AND outra < nova AND colunas >= 2)
 AND NEW.familia_id IS NOT (SELECT familia FROM v_familia_match WHERE nova=NEW.id AND outra < nova AND colunas >= 2
                            ORDER BY colunas DESC, familia ASC LIMIT 1)
 -- the family chosen at the gate (best among older and newer live ideas) also passes
 AND NEW.familia_id IS NOT (SELECT familia FROM v_familia_match WHERE nova=NEW.id AND colunas >= 2
                            ORDER BY colunas DESC, familia ASC LIMIT 1)
BEGIN SELECT RAISE(ABORT,'familia_errada'); END;

-- A refuted stage whose destination is death cannot be archived instead (section 7.4): every stage except G1 and S2,
-- and W1 only after its iteration (estendida=1).
CREATE TRIGGER trg_refutada_exige_morte BEFORE UPDATE OF estado ON ideias
WHEN OLD.estado='em_teste' AND NEW.estado IN ('arquivada','congelada')
 AND EXISTS(SELECT 1 FROM hipoteses h WHERE h.ideia_id=NEW.id AND h.resultado='refutada'
            AND h.etapa NOT IN ('G1','S2') AND (h.etapa<>'W1' OR h.estendida=1)
            AND h.experimento_id = (SELECT MAX(hh.experimento_id) FROM hipoteses hh JOIN experimentos xx ON xx.id=hh.experimento_id
                                    WHERE hh.ideia_id=NEW.id AND hh.resultado IN ('confirmada','refutada')   -- an inconclusive-only experiment (no reading) never hides a refutation
                                    AND COALESCE(xx.decisao,'') NOT IN ('planejado_vencido','orfao','iterado','abortado'))
            AND h.fechada_em >= COALESCE((SELECT MAX(em) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0'))
BEGIN SELECT RAISE(ABORT,'refutada_exige_morte'); END;

-- Decided hypotheses and the event log are immutable (no rewriting a defeat).
CREATE TRIGGER trg_hipotese_imutavel BEFORE UPDATE ON hipoteses
WHEN OLD.resultado IS NOT NULL
BEGIN SELECT RAISE(ABORT,'hipotese_decidida_imutavel'); END;
CREATE TRIGGER trg_hipotese_sem_delete BEFORE DELETE ON hipoteses
BEGIN SELECT RAISE(ABORT,'hipotese_decidida_imutavel'); END;
CREATE TRIGGER trg_eventos_sem_update BEFORE UPDATE ON ideia_eventos
BEGIN SELECT RAISE(ABORT,'eventos_imutaveis'); END;
CREATE TRIGGER trg_eventos_sem_delete BEFORE DELETE ON ideia_eventos
BEGIN SELECT RAISE(ABORT,'eventos_imutaveis'); END;

-- A reopened or reactivated idea starts the desk from scratch: score, sheet score and advocate are cleared (10.2).
CREATE TRIGGER trg_reabertura_zera_score AFTER UPDATE OF estado ON ideias
WHEN NEW.estado='candidata' AND OLD.estado IN ('morta','arquivada','congelada')
BEGIN UPDATE ideias SET score=NULL, score_json=NULL, advogado_em=NULL, arquivamento=NULL WHERE id=NEW.id; END;

-- validada only with the track's stages passed in the current cycle (10.1).
CREATE TRIGGER trg_validada_exige_etapas BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='validada' AND OLD.estado='em_teste' AND NOT (
  CASE NEW.trilha
   WHEN 'W' THEN (NEW.exclusividade IS 'crazygames_agregadores'
                  AND EXISTS(SELECT 1 FROM experimentos x JOIN hipoteses h ON h.experimento_id=x.id
                         WHERE x.ideia_id=NEW.id AND x.etapa='W1' AND x.decisao='passa'
                         AND h.metrica='aceite_plataforma' AND h.resultado='confirmada'
                         AND x.fim >= COALESCE((SELECT date(MAX(em)) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0')))
             OR (NEW.exclusividade IS NOT 'crazygames_agregadores'
                  AND EXISTS(SELECT 1 FROM experimentos x WHERE x.ideia_id=NEW.id AND x.etapa='W1' AND x.decisao='passa'
                         AND x.fim >= COALESCE((SELECT date(MAX(em)) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0'))
                  AND EXISTS(SELECT 1 FROM experimentos x WHERE x.ideia_id=NEW.id AND x.etapa='W2' AND x.decisao='passa'
                         AND x.fim >= COALESCE((SELECT date(MAX(em)) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0')))
   WHEN 'S' THEN (SELECT COUNT(DISTINCT x.etapa) FROM experimentos x WHERE x.ideia_id=NEW.id AND x.etapa IN ('S1','S2') AND x.decisao='passa'
                         AND x.fim >= COALESCE((SELECT date(MAX(em)) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0')) = 2
   WHEN 'M' THEN EXISTS(SELECT 1 FROM experimentos x WHERE x.ideia_id=NEW.id AND x.etapa='M1' AND x.decisao='passa'
                         AND x.fim >= COALESCE((SELECT date(MAX(em)) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0'))
   WHEN 'R' THEN EXISTS(SELECT 1 FROM experimentos x WHERE x.ideia_id=NEW.id AND x.etapa='R1' AND x.decisao='passa'
                         AND x.fim >= COALESCE((SELECT date(MAX(em)) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0'))
   ELSE 0 END )
BEGIN SELECT RAISE(ABORT,'etapas_nao_passaram'); END;

-- Owner transitions need the exact phrase of section 0.1, at the START of the quote ("não aprovo ..." is no approval).
CREATE TRIGGER trg_frase_do_dono BEFORE INSERT ON ideia_eventos
WHEN NEW.ator='dono' AND (
     (NEW.para='em_construcao' AND NEW.de IN ('candidata','pre_teste')
      AND replace(replace(replace(replace(lower(replace(NEW.prova_dono,'“','"') || ' '),'Ç','ç'),'Ã','ã'),'Õ','õ'),'É','é') NOT GLOB ('"construo sem teste de comportamento a ideia#' || NEW.ideia_id || '[^0-9]*'))
  OR (NEW.para='em_construcao' AND NEW.de='validada'
      AND replace(replace(replace(replace(lower(replace(NEW.prova_dono,'“','"') || ' '),'Ç','ç'),'Ã','ã'),'Õ','õ'),'É','é') NOT GLOB ('"aprovo a construção da ideia#' || NEW.ideia_id || '[^0-9]*'))
  OR (NEW.de='congelada' AND NEW.para IN ('em_construcao','lancada')
      AND replace(replace(replace(replace(lower(replace(NEW.prova_dono,'“','"') || ' '),'Ç','ç'),'Ã','ã'),'Õ','õ'),'É','é') NOT GLOB ('"descongelo a ideia#' || NEW.ideia_id || '[^0-9]*'))
  OR (NEW.motivo LIKE 'REABERTA:%' AND NOT (NEW.para='em_construcao' AND NEW.de IN ('candidata','pre_teste'))   -- the override carries its own phrase
      AND replace(replace(replace(replace(lower(replace(NEW.prova_dono,'“','"') || ' '),'Ç','ç'),'Ã','ã'),'Õ','õ'),'É','é') NOT GLOB ('"reabro a ideia#' || NEW.ideia_id || '[^0-9]*'))
  OR (NEW.para='lancada' AND NEW.de<>'congelada' AND replace(replace(replace(replace(lower(replace(NEW.prova_dono,'“','"') || ' '),'Ç','ç'),'Ã','ã'),'Õ','õ'),'É','é') NOT GLOB ('"ideia#' || NEW.ideia_id || ' lançada em*')) )
BEGIN SELECT RAISE(ABORT,'frase_do_dono'); END;

-- The CrazyGames path runs at most twice per idea (the test and its one iteration).
CREATE TRIGGER trg_crazygames_uma_vez BEFORE INSERT ON hipoteses
WHEN NEW.etapa='W1' AND NEW.metrica='aceite_plataforma'
 AND (SELECT COUNT(DISTINCT experimento_id) FROM hipoteses WHERE ideia_id=NEW.ideia_id AND etapa='W1'
      AND metrica='aceite_plataforma' AND experimento_id<>NEW.experimento_id
      -- per cycle: a reopened idea gets its test and iteration again
      AND criada_em >= COALESCE((SELECT MAX(em) FROM ideia_eventos WHERE ideia_id=NEW.ideia_id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0')) >= 2
BEGIN SELECT RAISE(ABORT,'crazygames_uma_vez'); END;

-- Links that define family, candidacy and trends cannot be deleted after the idea left 'sinal'.
CREATE TRIGGER trg_vinculo_concorrente_fixo BEFORE DELETE ON ideia_concorrentes
WHEN (SELECT estado FROM ideias WHERE id=OLD.ideia_id) <> 'sinal'
BEGIN SELECT RAISE(ABORT,'vinculo_imutavel'); END;
CREATE TRIGGER trg_vinculo_evidencia_fixo BEFORE DELETE ON evidencias
WHEN (SELECT estado FROM ideias WHERE id=OLD.ideia_id) <> 'sinal'
BEGIN SELECT RAISE(ABORT,'vinculo_imutavel'); END;

-- Owner pending items, so that 'pendencia#N resolvida' is checkable (reabrir_se, 3.2).
CREATE TABLE pendencias(id INTEGER PRIMARY KEY, ideia_id INTEGER REFERENCES ideias(id), texto TEXT NOT NULL,
  criada_em TEXT NOT NULL DEFAULT (datetime('now')), resolvida_em TEXT, prova_dono TEXT,
  cancelada_em TEXT, motivo_cancelamento TEXT,   -- the routine cancels an obsolete item (no owner quote needed)
  CHECK(resolvida_em IS NULL OR prova_dono IS NOT NULL),
  CHECK(cancelada_em IS NULL OR motivo_cancelamento IS NOT NULL));

-- A stage result 'passa' needs hypotheses, all confirmed (no bare label).
CREATE TRIGGER trg_decisao_passa_ins BEFORE INSERT ON experimentos WHEN NEW.decisao='passa'
BEGIN SELECT RAISE(ABORT,'decisao_sem_hipoteses'); END;
CREATE TRIGGER trg_decisao_passa_upd BEFORE UPDATE OF decisao ON experimentos
WHEN NEW.decisao='passa' AND ( NOT EXISTS(SELECT 1 FROM hipoteses WHERE experimento_id=NEW.id)
   OR EXISTS(SELECT 1 FROM hipoteses WHERE experimento_id=NEW.id AND resultado IS NOT 'confirmada') )
BEGIN SELECT RAISE(ABORT,'decisao_sem_hipoteses'); END;

-- Pre-registration: the copied thresholds never change.
CREATE TRIGGER trg_pre_registro_imutavel BEFORE UPDATE OF metrica, tipo_criterio, limiar_passa, limiar_mata, n_min,
  eventos_min, prazo_dias, previsao, limiar_versao ON hipoteses
BEGIN SELECT RAISE(ABORT,'pre_registro_imutavel'); END;

-- FIX-FIRST once per family (section 5).
CREATE TRIGGER trg_fix_first_uma_vez BEFORE INSERT ON ideia_eventos
WHEN NEW.motivo LIKE 'FIX-FIRST:%'
 AND EXISTS(SELECT 1 FROM ideia_eventos e JOIN ideias i ON i.id=e.ideia_id
            WHERE e.motivo LIKE 'FIX-FIRST:%'
              AND (i.id=NEW.ideia_id OR i.familia_id=(SELECT familia_id FROM ideias WHERE id=NEW.ideia_id)))
BEGIN SELECT RAISE(ABORT,'fix_first_uma_vez'); END;

-- A launch opens the E5 experiment that holds the live game's metrics (section 7.2).
CREATE TRIGGER trg_lancamento_abre_e5 AFTER UPDATE OF estado ON ideias
WHEN NEW.estado='lancada' AND OLD.estado='em_construcao'
 AND NOT EXISTS(SELECT 1 FROM experimentos WHERE ideia_id=NEW.id AND etapa='E5' AND estado='rodando')
BEGIN INSERT INTO experimentos(ideia_id,etapa,tipo,estado,inicio) VALUES(NEW.id,'E5','pos_lancamento','rodando',date('now')); END;

-- Every archive states why (10.2): 'resultado' or 'operacional'.
CREATE TRIGGER trg_arquivamento_obrigatorio BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='arquivada' AND OLD.estado<>'arquivada' AND NEW.arquivamento IS NULL
BEGIN SELECT RAISE(ABORT,'arquivamento_obrigatorio'); END;

-- The portal path (exclusividade) is chosen before the first experiment; afterwards it only switches to CrazyGames
-- after a Poki refusal (W1 refuted after its iteration, or W2 refuted) — section 7.1/7.4.
CREATE TRIGGER trg_exclusividade_travada BEFORE UPDATE OF exclusividade ON ideias
WHEN NEW.exclusividade IS NOT OLD.exclusividade
 -- only experiments of the current cycle (since the last reopening) lock the choice
 AND EXISTS(SELECT 1 FROM experimentos WHERE ideia_id=NEW.id AND criado_em >= COALESCE((SELECT MAX(em) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0'))
 AND NOT (NEW.exclusividade='crazygames_agregadores'
          AND EXISTS(SELECT 1 FROM hipoteses h WHERE h.ideia_id=NEW.id AND h.resultado='refutada'
                     AND ((h.etapa='W1' AND h.estendida=1) OR h.etapa='W2')))
 -- a build measured over Poki's targets before any test started also switches to CrazyGames (7.1)
 AND NOT (NEW.exclusividade='crazygames_agregadores'
          AND NOT EXISTS(SELECT 1 FROM experimentos WHERE ideia_id=NEW.id AND inicio IS NOT NULL AND criado_em >= COALESCE((SELECT MAX(em) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0'))
          AND COALESCE(NEW.build_mb > (SELECT CAST(valor AS REAL) FROM config WHERE chave='poki_build_mb_max')
                       OR NEW.tempo_gameplay_s > (SELECT CAST(valor AS REAL) FROM config WHERE chave='tempo_gameplay_s_max'), 0))
BEGIN SELECT RAISE(ABORT,'exclusividade_travada'); END;

-- "descongelo" returns an idea only to the state it froze from (build or live game); an idea frozen before the build
-- comes back only through reactivation (congelada -> candidata).
CREATE TRIGGER trg_descongelo_origem BEFORE UPDATE OF estado ON ideias
WHEN OLD.estado='congelada' AND NEW.estado IN ('em_construcao','lancada')
 AND NEW.estado IS NOT (SELECT de FROM ideia_eventos WHERE id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='congelada'))
BEGIN SELECT RAISE(ABORT,'descongelo_fora_da_origem'); END;

-- An own game (ports, graduations) points to a launched idea, once (it switches off the trend guard for that row).
CREATE TRIGGER trg_proprio_ins BEFORE INSERT ON concorrentes
WHEN NEW.proprio_ideia_id IS NOT NULL
 AND NOT EXISTS(SELECT 1 FROM ideia_eventos WHERE ideia_id=NEW.proprio_ideia_id AND para='lancada')
BEGIN SELECT RAISE(ABORT,'proprio_so_de_ideia_lancada'); END;
CREATE TRIGGER trg_proprio_upd BEFORE UPDATE OF proprio_ideia_id ON concorrentes
WHEN NEW.proprio_ideia_id IS NOT OLD.proprio_ideia_id
 AND (OLD.proprio_ideia_id IS NOT NULL
      OR NOT EXISTS(SELECT 1 FROM ideia_eventos WHERE ideia_id=NEW.proprio_ideia_id AND para='lancada'))
BEGIN SELECT RAISE(ABORT,'proprio_so_de_ideia_lancada'); END;

-- CrazyGames chosen at the desk (no Poki refusal) needs a measured reason: build or time to gameplay over Poki's
-- targets, an idle/incremental genre (cut 12), or a trend idea (the Poki path does not fit the trend window, 4.4).
CREATE TRIGGER trg_crazygames_direto BEFORE INSERT ON experimentos
WHEN NEW.etapa='W1'
 AND (SELECT exclusividade FROM ideias WHERE id=NEW.ideia_id) IS 'crazygames_agregadores'
 AND NOT EXISTS(SELECT 1 FROM hipoteses h WHERE h.ideia_id=NEW.ideia_id AND h.resultado='refutada'
                AND ((h.etapa='W1' AND h.estendida=1) OR h.etapa='W2'))
 AND NOT EXISTS(SELECT 1 FROM ideias i WHERE i.id=NEW.ideia_id AND (
       i.build_mb > (SELECT CAST(valor AS REAL) FROM config WHERE chave='poki_build_mb_max')
    OR i.tempo_gameplay_s > (SELECT CAST(valor AS REAL) FROM config WHERE chave='tempo_gameplay_s_max')
    OR i.loop_idle IS 1 OR lower(i.genero_central) GLOB '*idle*' OR lower(i.genero_central) GLOB '*incremental*' OR lower(i.genero_central) GLOB '*clicker*'
    OR i.fonte_ideia IS 'tendencia'))
BEGIN SELECT RAISE(ABORT,'crazygames_direto_sem_motivo'); END;

-- Pre-registration happens before the data: no hypothesis on an experiment that already has metrics.
CREATE TRIGGER trg_hipotese_antes_dos_dados BEFORE INSERT ON hipoteses
WHEN EXISTS(SELECT 1 FROM metricas WHERE experimento_id=NEW.experimento_id)
BEGIN SELECT RAISE(ABORT,'hipotese_depois_dos_dados'); END;

-- Calibration (section 15): platform gates (origem='benchmark') are never recalibrated, and a new version never
-- loosens the previous one (owner-approved changes go through the CHANGELOG and the seed).
CREATE TRIGGER trg_limiar_calibracao BEFORE INSERT ON limiares
WHEN EXISTS(SELECT 1 FROM limiares l WHERE l.etapa=NEW.etapa AND l.metrica=NEW.metrica AND l.segmento=NEW.segmento
            AND l.origem='benchmark')
  OR EXISTS(SELECT 1 FROM limiares l WHERE l.etapa=NEW.etapa AND l.metrica=NEW.metrica AND l.segmento=NEW.segmento
            AND l.versao=(SELECT MAX(versao) FROM limiares x WHERE x.etapa=NEW.etapa AND x.metrica=NEW.metrica AND x.segmento=NEW.segmento)
            AND CASE WHEN NEW.tipo_criterio='teto' THEN NEW.limiar_passa > l.limiar_passa OR NEW.limiar_mata > l.limiar_mata
                     ELSE NEW.limiar_passa < l.limiar_passa OR NEW.limiar_mata < l.limiar_mata END)
BEGIN SELECT RAISE(ABORT,'limiar_recalibracao_proibida'); END;

-- Pre-registration copies the current limiares row (7.4): when the stage+metric has a limiares row, the hypothesis
-- must match the latest version of its segment field by field.
CREATE TRIGGER trg_pre_registro_copia BEFORE INSERT ON hipoteses
WHEN EXISTS(SELECT 1 FROM limiares WHERE etapa=NEW.etapa AND metrica=NEW.metrica)
 AND NOT EXISTS(SELECT 1 FROM limiares l WHERE l.etapa=NEW.etapa AND l.metrica=NEW.metrica AND l.segmento=COALESCE(NEW.segmento,'*')
                AND l.versao=NEW.limiar_versao
                AND l.versao=(SELECT MAX(versao) FROM limiares x WHERE x.etapa=l.etapa AND x.metrica=l.metrica AND x.segmento=l.segmento)
                AND l.tipo_criterio=NEW.tipo_criterio AND l.limiar_passa=NEW.limiar_passa AND l.limiar_mata=NEW.limiar_mata
                AND l.n_min=NEW.n_min AND l.eventos_min=NEW.eventos_min AND l.prazo_dias=NEW.prazo_dias)
BEGIN SELECT RAISE(ABORT,'pre_registro_diverge_do_limiar'); END;

-- Idle/incremental/clicker loops never take the Poki path: an open idle tab inflates Player Fit (cut 12).
CREATE TRIGGER trg_idle_crazygames BEFORE INSERT ON experimentos
WHEN NEW.etapa='W1'
 AND EXISTS(SELECT 1 FROM ideias i WHERE i.id=NEW.ideia_id AND i.exclusividade IS NOT 'crazygames_agregadores'
            AND (i.loop_idle IS 1 OR lower(i.genero_central) GLOB '*idle*' OR lower(i.genero_central) GLOB '*incremental*' OR lower(i.genero_central) GLOB '*clicker*'))
BEGIN SELECT RAISE(ABORT,'idle_vai_para_crazygames'); END;

-- A stage passes only with the full hypothesis set of its limiares segment, on the idea's own platform/path (7.4).
CREATE TRIGGER trg_passa_conjunto BEFORE UPDATE OF decisao ON experimentos
WHEN NEW.decisao='passa' AND (
  -- the stage has limiares rows but no hypothesis copies one
  ( EXISTS(SELECT 1 FROM limiares WHERE etapa=NEW.etapa)
    AND NOT EXISTS(SELECT 1 FROM hipoteses h JOIN limiares l ON l.etapa=h.etapa AND l.metrica=h.metrica AND l.segmento=COALESCE(h.segmento,'*')
                   WHERE h.experimento_id=NEW.id) )
  -- a segment in use misses one of its metrics
  OR EXISTS(SELECT 1 FROM limiares l WHERE l.etapa=NEW.etapa
            AND l.segmento IN (SELECT COALESCE(segmento,'*') FROM hipoteses WHERE experimento_id=NEW.id)
            AND NOT EXISTS(SELECT 1 FROM hipoteses h WHERE h.experimento_id=NEW.id AND h.metrica=l.metrica
                           AND COALESCE(h.segmento,'*')=l.segmento AND h.resultado='confirmada'))
  -- a segment of another platform or path
  OR EXISTS(SELECT 1 FROM hipoteses h JOIN ideias i ON i.id=h.ideia_id WHERE h.experimento_id=NEW.id AND (
        (h.segmento IN ('roblox','uefn') AND h.segmento IS NOT i.plataforma)
     OR (h.segmento GLOB 'poki*' AND i.exclusividade IS 'crazygames_agregadores')
     OR (h.segmento='crazygames_basic' AND i.exclusividade IS NOT 'crazygames_agregadores'))) )
BEGIN SELECT RAISE(ABORT,'hipoteses_incompletas'); END;

-- 'recriada como ideia#' (excluded from family and reopening) only on an operational archive without a death motive.
CREATE TRIGGER trg_recriada_ins BEFORE UPDATE OF reabrir_se, estado, arquivamento ON ideias
WHEN COALESCE(NEW.reabrir_se,'') LIKE 'recriada como ideia#%'
 AND NOT (NEW.estado='arquivada' AND NEW.arquivamento IS 'operacional' AND NEW.motivo_morte IS NULL)
BEGIN SELECT RAISE(ABORT,'recriada_so_operacional'); END;

-- The idea's source label is fixed once it leaves candidata (it switches trend and CrazyGames rules).
CREATE TRIGGER trg_fonte_ideia_fixa BEFORE UPDATE OF fonte_ideia ON ideias
WHEN NEW.fonte_ideia IS NOT OLD.fonte_ideia AND ( OLD.estado NOT IN ('sinal','candidata')
  OR EXISTS(SELECT 1 FROM ideia_eventos WHERE ideia_id=NEW.id AND de='candidata' AND para NOT IN ('candidata','morta','arquivada')) )
 -- a 'tendencia' label whose reference is no longer a live trend goes back to the idea's real source (4.4)
 AND NOT (OLD.fonte_ideia IS 'tendencia' AND NEW.fonte_ideia IS NOT 'tendencia'
          AND OLD.estado IN ('candidata','pre_teste','congelada','validada','em_construcao','lancada')
          AND NOT EXISTS(SELECT 1 FROM ideia_concorrentes ic JOIN v_tendencia_viva v ON v.concorrente_id=ic.concorrente_id
                         WHERE ic.ideia_id=NEW.id AND ic.papel='referencia'))
 -- and the mirror: a reference that became a registered live trend after the queue entry turns the label into 'tendencia'
 AND NOT (NEW.fonte_ideia IS 'tendencia' AND OLD.fonte_ideia IS NOT 'tendencia' AND OLD.estado IN ('candidata','pre_teste','congelada')
          AND EXISTS(SELECT 1 FROM ideia_concorrentes ic JOIN v_tendencia_viva v ON v.concorrente_id=ic.concorrente_id
                     JOIN tendencias t ON t.loja=v.loja AND t.id_loja=v.id_loja
                     WHERE ic.ideia_id=NEW.id AND ic.papel='referencia'))
BEGIN SELECT RAISE(ABORT,'fonte_ideia_imutavel'); END;

-- A cancelled test that already had data is archived as a result (graveyard), never as an operational archive.
CREATE TRIGGER trg_cancelamento_com_dados BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='arquivada' AND OLD.estado<>'arquivada' AND NEW.arquivamento IS 'operacional'
 AND EXISTS(SELECT 1 FROM experimentos x WHERE x.ideia_id=NEW.id AND x.decisao='abortado' AND x.criado_em >= COALESCE((SELECT MAX(em) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0')
            AND EXISTS(SELECT 1 FROM metricas m WHERE m.experimento_id=x.id))
BEGIN SELECT RAISE(ABORT,'cancelamento_com_dados'); END;

-- Leaving a test (freeze or archive) first decides every open hypothesis that already has data (7.4).
CREATE TRIGGER trg_decidir_antes_de_sair BEFORE UPDATE OF estado ON ideias
WHEN OLD.estado='em_teste' AND NEW.estado IN ('congelada','arquivada')
 AND EXISTS(SELECT 1 FROM hipoteses h WHERE h.ideia_id=NEW.id AND h.resultado IS NULL
            AND EXISTS(SELECT 1 FROM metricas m WHERE m.experimento_id=h.experimento_id))
BEGIN SELECT RAISE(ABORT,'decidir_antes_de_sair_do_teste'); END;

-- A clone of a registered live hype on the hype's own platform dies (janela_fechada); only a port to another platform
-- (arbitrage) may freeze until the guards stop (4.4).
CREATE TRIGGER trg_clone_de_hype_morre BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado='congelada' AND OLD.estado IN ('candidata','pre_teste','em_teste')
 AND EXISTS(SELECT 1 FROM ideia_concorrentes ic JOIN v_tendencia_viva v ON v.concorrente_id=ic.concorrente_id
            JOIN tendencias t ON t.loja=v.loja AND t.id_loja=v.id_loja
            WHERE ic.ideia_id=NEW.id AND ic.papel='referencia'
              -- only where a trend idea is allowed (web, roblox): elsewhere the same-platform clone waits for the 121st day
              AND NEW.plataforma IN ('web','roblox')
              AND CASE WHEN v.loja IN ('poki','crazygames','web','itch') THEN 'web'
                       WHEN v.loja IN ('appstore','play') THEN 'mobile' ELSE v.loja END = NEW.plataforma)
BEGIN SELECT RAISE(ABORT,'clone_de_hype_morre'); END;

-- A hypothesis is decided from data: confirmada/refutada need the observed values and at least one metrics row (7.4).
CREATE TRIGGER trg_decisao_com_dado BEFORE UPDATE OF resultado ON hipoteses
WHEN NEW.resultado IN ('confirmada','refutada') AND OLD.resultado IS NULL
 AND (NEW.n_observado IS NULL OR NEW.valor_observado IS NULL OR NEW.eventos_observados IS NULL
      OR NOT EXISTS(SELECT 1 FROM metricas WHERE experimento_id=NEW.experimento_id))
BEGIN SELECT RAISE(ABORT,'decisao_sem_dado'); END;

-- A hypothesis is born open (pre-registration) and is decided only by UPDATE, from data (7.4).
CREATE TRIGGER trg_hipotese_nasce_aberta BEFORE INSERT ON hipoteses
WHEN NEW.resultado IN ('confirmada','refutada')
BEGIN SELECT RAISE(ABORT,'decisao_so_por_update'); END;

-- The decision agrees with the observed value: confirmada at or beyond the pass line (teto: at or below it); refutada
-- short of it (first round only: an extended count passes against passa_estendido, in its own unit).
CREATE TRIGGER trg_decisao_coerente BEFORE UPDATE OF resultado ON hipoteses
WHEN OLD.resultado IS NULL AND NEW.valor_observado IS NOT NULL AND (
     (NEW.resultado='confirmada' AND CASE WHEN NEW.tipo_criterio='teto' THEN NEW.valor_observado > NEW.limiar_passa
                                          ELSE NEW.valor_observado < NEW.limiar_passa END)
  OR (NEW.resultado='refutada' AND NEW.estendida=0 AND CASE WHEN NEW.tipo_criterio='teto' THEN NEW.valor_observado <= NEW.limiar_passa
                                                            ELSE NEW.valor_observado >= NEW.limiar_passa END))
BEGIN SELECT RAISE(ABORT,'decisao_incoerente'); END;

-- A hypothesis belongs to its experiment's stage and idea.
CREATE TRIGGER trg_hipotese_da_etapa BEFORE INSERT ON hipoteses
WHEN NEW.etapa IS NOT (SELECT etapa FROM experimentos WHERE id=NEW.experimento_id)
  OR NEW.ideia_id IS NOT (SELECT ideia_id FROM experimentos WHERE id=NEW.experimento_id)
BEGIN SELECT RAISE(ABORT,'hipotese_de_outra_etapa'); END;

-- A declared idle loop stays declared once the idea leaves candidata (it routes the portal path).
CREATE TRIGGER trg_loop_idle_fixo BEFORE UPDATE OF loop_idle ON ideias
WHEN OLD.loop_idle=1 AND NEW.loop_idle IS NOT 1 AND ( OLD.estado NOT IN ('sinal','candidata')
  OR EXISTS(SELECT 1 FROM ideia_eventos WHERE ideia_id=NEW.id AND de='candidata' AND para NOT IN ('candidata','morta','arquivada')) )
BEGIN SELECT RAISE(ABORT,'loop_idle_imutavel'); END;

-- Columns that decide a destiny are written once (threat model): an archive's class, a signal's identity, the
-- exploration month.
CREATE TRIGGER trg_arquivamento_fixo BEFORE UPDATE OF arquivamento ON ideias
WHEN OLD.estado IN ('arquivada','morta') AND NEW.estado=OLD.estado AND NEW.arquivamento IS NOT OLD.arquivamento
BEGIN SELECT RAISE(ABORT,'arquivamento_imutavel'); END;
CREATE TRIGGER trg_sinal_fixo BEFORE UPDATE OF tipo, fonte_id, hash, url, url_status, trecho_literal ON sinais
BEGIN SELECT RAISE(ABORT,'sinal_imutavel'); END;
CREATE TRIGGER trg_exploracao_em_fixo BEFORE UPDATE OF exploracao_em ON ideias
WHEN OLD.exploracao_em IS NOT NULL AND NEW.exploracao_em IS NOT OLD.exploracao_em
BEGIN SELECT RAISE(ABORT,'exploracao_em_imutavel'); END;

-- A test whose latest decided stage was refuted is a result archive (graveyard), never an operational one or a
-- 'recriada' relabel (mirror of trg_cancelamento_com_dados).
CREATE TRIGGER trg_refutada_arquiva_resultado BEFORE UPDATE OF estado ON ideias
WHEN OLD.estado='em_teste' AND NEW.estado='arquivada'
 AND (NEW.arquivamento IS NOT 'resultado' OR COALESCE(NEW.reabrir_se,'') LIKE 'recriada como ideia#%')
 AND EXISTS(SELECT 1 FROM hipoteses h WHERE h.ideia_id=NEW.id AND h.resultado='refutada'
            -- only the stages whose refutation may archive (the others must die: trg_refutada_exige_morte)
            AND (h.etapa IN ('G1','S2') OR (h.etapa='W1' AND h.estendida=0))
            AND h.experimento_id = (SELECT MAX(hh.experimento_id) FROM hipoteses hh JOIN experimentos xx ON xx.id=hh.experimento_id
                                    WHERE hh.ideia_id=NEW.id AND hh.resultado IN ('confirmada','refutada')
                                    AND COALESCE(xx.decisao,'') NOT IN ('planejado_vencido','orfao','iterado','abortado'))
            AND h.fechada_em >= COALESCE((SELECT MAX(em) FROM ideia_eventos WHERE ideia_id=NEW.id AND para='candidata' AND de IN ('morta','arquivada') AND motivo LIKE 'REABERTA:%'),'0'))
BEGIN SELECT RAISE(ABORT,'refutada_arquiva_como_resultado'); END;
