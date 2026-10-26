-- Schema of the app-ideas routine. Dates in UTC: 'YYYY-MM-DD HH:MM:SS' (datetime('now')) or 'YYYY-MM-DD' (date('now')).
-- Identifiers (tables, columns, state values) are in Portuguese on purpose; SKILL.md explains each one.
PRAGMA foreign_keys=ON;
PRAGMA user_version=11;
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
  tipo TEXT NOT NULL CHECK(tipo IN('dor','pedido','concorrente','orfao','plataforma','regulacao','keyword_fraca','preco','outro')),
  autor_tipo TEXT, mercado TEXT CHECK(mercado IN('BR','EN','global_outros') OR mercado IS NULL),
  idioma TEXT, publicado_em TEXT, coletado_em TEXT NOT NULL DEFAULT (datetime('now')), payload_json TEXT);

CREATE TABLE ideias(id INTEGER PRIMARY KEY, titulo TEXT NOT NULL, problema TEXT, publico TEXT,
  familia_id INTEGER, reaberta_de INTEGER REFERENCES ideias(id), reabrir_se TEXT,
  exploracao INTEGER NOT NULL DEFAULT 0 CHECK(exploracao IN(0,1)), exploracao_em TEXT,
  pagador TEXT CHECK(pagador IN('consumidor','profissional','empresa') OR pagador IS NULL),
  formato TEXT CHECK(formato IN('saas','pwa','extensao','addon','ios','android') OR formato IS NULL),
  mercado TEXT CHECK(mercado IN('BR','EN','global_outros') OR mercado IS NULL), paises_alvo TEXT,
  trilha TEXT CHECK(trilha IN('W','WSEO','M','L') OR trilha IS NULL),
  canal TEXT, canal_cobranca TEXT CHECK(canal_cobranca IN('appstore','play','shopify','atlassian_forge','creem','dodo','paddle','stripe_br') OR canal_cobranca IS NULL),
  preco_alvo REAL, moeda_preco TEXT CHECK(moeda_preco IN('USD','BRL') OR moeda_preco IS NULL),
  liquido_cliente_usd REAL, n300 INTEGER, n1000 INTEGER, visitas_mes INTEGER,
  volume_status TEXT CHECK(volume_status IN('medido','proxy','nao_medido') OR volume_status IS NULL),
  universo INTEGER, universo_fonte TEXT,
  risco_absorcao TEXT CHECK(risco_absorcao IN('baixo','medio','alto') OR risco_absorcao IS NULL),
  risco_dependencia TEXT CHECK(risco_dependencia IN('baixo','alto') OR risco_dependencia IS NULL),
  cobertura_llm REAL, fosso TEXT, janela_inicio TEXT, janela_fim TEXT, data_reativacao TEXT,
  estado TEXT NOT NULL DEFAULT 'sinal' CHECK(estado IN
    ('sinal','candidata','pre_teste','em_teste','validada','em_construcao','lancada','congelada','arquivada','morta')),
  motivo_morte TEXT CHECK(motivo_morte IN('sem_pagador','sem_canal','mercado_pequeno','concorrencia_saturada',
    'incumbente_gratis','commodity_ia','teste_reprovado','custo_alto','risco_banimento','excluida_por_regra',
    'advogado_do_diabo','prazo') OR motivo_morte IS NULL),
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
  loja TEXT NOT NULL CHECK(loja IN('appstore','play','cws','shopify','wordpress','workspace','notion','figma',
    'slack','atlassian','web','trustmrr')),
  id_loja TEXT NOT NULL, nome TEXT, vendedor TEXT, url TEXT, modelo_preco TEXT, preco_texto TEXT,
  ultimo_sinal_de_vida TEXT,   -- date of the last review reply, changelog, commit or price change
  primeira_vez_em TEXT NOT NULL DEFAULT (date('now')), UNIQUE(loja,id_loja));

CREATE TABLE ideia_concorrentes(ideia_id INTEGER NOT NULL REFERENCES ideias(id),
  concorrente_id INTEGER NOT NULL REFERENCES concorrentes(id), PRIMARY KEY(ideia_id,concorrente_id));

CREATE TABLE concorrente_snapshots(concorrente_id INTEGER NOT NULL REFERENCES concorrentes(id),
  data TEXT NOT NULL, pais TEXT NOT NULL, rank_lista TEXT NOT NULL DEFAULT '',
  ratings_count INTEGER, rating_avg REAL, installs_min INTEGER, installs_max INTEGER, users INTEGER,
  preco REAL, tem_iap INTEGER, versao_data TEXT, rank_pos INTEGER, run_id INTEGER REFERENCES runs(id),
  PRIMARY KEY(concorrente_id,data,pais,rank_lista));

CREATE TABLE keywords(id INTEGER PRIMARY KEY, termo TEXT NOT NULL, loja TEXT NOT NULL, pais TEXT NOT NULL,
  ideia_id INTEGER REFERENCES ideias(id), principal INTEGER NOT NULL DEFAULT 0 CHECK(principal IN(0,1)),
  intencao TEXT CHECK(intencao IN('transacional','ferramenta','informacional') OR intencao IS NULL),
  tem_ai_overview INTEGER, registrada_em TEXT NOT NULL DEFAULT (datetime('now')));
CREATE UNIQUE INDEX ux_keywords ON keywords(termo, loja, pais, IFNULL(ideia_id, 0));

CREATE TABLE keyword_snapshots(keyword_id INTEGER NOT NULL REFERENCES keywords(id), data TEXT NOT NULL,
  popularidade INTEGER, fonte_popularidade TEXT CHECK(fonte_popularidade IN('apple_ads_popularidade','keyword_planner') OR fonte_popularidade IS NULL),
  n_resultados INTEGER, top10_ratings_mediana INTEGER, top10_pagos INTEGER, top10_abandonados INTEGER,
  cumpre_criterio INTEGER, top10_json TEXT, PRIMARY KEY(keyword_id,data));

CREATE TABLE experimentos(id INTEGER PRIMARY KEY, ideia_id INTEGER NOT NULL REFERENCES ideias(id),
  etapa TEXT NOT NULL CHECK(etapa IN('E1','E2E3','E3','E4','WSEO','M1','L1')),
  tipo TEXT NOT NULL CHECK(tipo IN('landing','anuncio','checkout','listing','paywall','seo')),
  url TEXT, utm_sources TEXT, paises_trafego TEXT, preco_testado REAL, moeda_preco_testado TEXT,
  estado TEXT NOT NULL CHECK(estado IN('planejado','rodando','encerrado','abortado')),
  inicio TEXT,   -- stage milestone (see limiares.marco_inicio); NULL while 'planejado'
  fim TEXT, decisao TEXT);

CREATE TABLE hipoteses(id INTEGER PRIMARY KEY, ideia_id INTEGER NOT NULL REFERENCES ideias(id),
  experimento_id INTEGER NOT NULL REFERENCES experimentos(id),
  etapa TEXT NOT NULL CHECK(etapa IN('E1','E2E3','E3','E4','WSEO','M1','L1')),
  enunciado TEXT NOT NULL, metrica TEXT NOT NULL,
  tipo_criterio TEXT NOT NULL CHECK(tipo_criterio IN('taxa','contagem')),
  limiar_passa REAL NOT NULL, limiar_mata REAL NOT NULL, n_min INTEGER NOT NULL, eventos_min INTEGER NOT NULL,
  limiar_versao INTEGER NOT NULL, previsao REAL NOT NULL,
  extensao_motivo TEXT CHECK(extensao_motivo IN('meio','sem_amostra') OR extensao_motivo IS NULL),
  orcamento_max_brl REAL NOT NULL DEFAULT 0, prazo_dias INTEGER NOT NULL, estendida INTEGER NOT NULL DEFAULT 0,
  resultado TEXT CHECK(resultado IN('confirmada','refutada','inconclusiva_sem_trafego','inconclusiva_amostra_parcial') OR resultado IS NULL),
  n_observado INTEGER, eventos_observados INTEGER, valor_observado REAL, ic_inf REAL, ic_sup REAL,
  aprendizado TEXT, criada_em TEXT NOT NULL DEFAULT (datetime('now')), fechada_em TEXT);

-- Each row = count for ONE full UTC day (yesterday). Never cumulative.
CREATE TABLE metricas(experimento_id INTEGER NOT NULL REFERENCES experimentos(id), data TEXT NOT NULL,
  metrica TEXT NOT NULL CHECK(metrica IN('pageview','pageview_preco','cta_click','email_submit','checkout_start',
    'pagamento','reembolso','install','install_pago','trial_start','paid','upgrade_click','ativos','impressoes','cliques_busca','custo_brl')),
  valor REAL NOT NULL, fonte TEXT NOT NULL CHECK(fonte IN('posthog','search_console','loja','gateway_api','dono_extrato','anuncio_dono')),
  run_id INTEGER REFERENCES runs(id), PRIMARY KEY(experimento_id,data,metrica));

CREATE TABLE receita_snapshots(ideia_id INTEGER NOT NULL REFERENCES ideias(id), data TEXT NOT NULL,
  mrr_liquido_usd REAL, pagantes INTEGER, trials INTEGER, installs INTEGER, fonte TEXT NOT NULL,
  PRIMARY KEY(ideia_id,data));

CREATE TABLE gastos(id INTEGER PRIMARY KEY, data TEXT NOT NULL, valor_brl REAL NOT NULL,
  categoria TEXT NOT NULL CHECK(categoria IN('anuncio','plataforma','dominio','ferramenta','outro')),
  ideia_id INTEGER REFERENCES ideias(id), experimento_id INTEGER REFERENCES experimentos(id),
  prova_dono TEXT NOT NULL CHECK(length(prova_dono) >= 10), nota TEXT);

CREATE TABLE horas(id INTEGER PRIMARY KEY, ideia_id INTEGER NOT NULL REFERENCES ideias(id), data TEXT NOT NULL,
  horas REAL NOT NULL, tipo TEXT NOT NULL CHECK(tipo IN('validacao','construcao','manutencao')),
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
  tipo_criterio TEXT NOT NULL CHECK(tipo_criterio IN('taxa','contagem')),
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
    OR (OLD.motivo_morte IN ('teste_reprovado','advogado_do_diabo','risco_banimento','excluida_por_regra')
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
WHEN NEW.estado IN ('pre_teste','em_teste','em_construcao') AND OLD.estado IN ('candidata','pre_teste','validada')
 AND (
  ( EXISTS(SELECT 1 FROM ideias m WHERE m.familia_id=NEW.familia_id AND m.id<>NEW.id AND m.estado='morta'
           AND m.motivo_morte IN ('teste_reprovado','advogado_do_diabo','risco_banimento','excluida_por_regra'))
    AND NOT EXISTS(SELECT 1 FROM ideia_eventos e WHERE e.id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)
           AND e.ator='dono' AND e.motivo LIKE 'REABERTA:%') )
  OR
  ( EXISTS(SELECT 1 FROM ideias m WHERE m.familia_id=NEW.familia_id AND m.id<>NEW.id AND m.estado IN ('morta','arquivada')
           AND (m.motivo_morte IS NULL OR m.motivo_morte NOT IN ('teste_reprovado','advogado_do_diabo','risco_banimento','excluida_por_regra')))
    AND OLD.estado IN ('candidata','pre_teste')
    AND ( NOT EXISTS(SELECT 1 FROM ideia_eventos e WHERE e.id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)
                     AND e.motivo LIKE 'REABERTA:%')
       OR ( (SELECT ator FROM ideia_eventos WHERE id=(SELECT MAX(id) FROM ideia_eventos WHERE ideia_id=NEW.id)) = 'rotina'
            AND (SELECT COUNT(DISTINCT e.ideia_id) FROM ideia_eventos e JOIN ideias i2 ON i2.id=e.ideia_id
                 WHERE i2.familia_id=NEW.familia_id AND e.motivo LIKE 'REABERTA:%' AND e.ator='rotina'
                   AND e.de IN ('candidata','pre_teste') AND e.para IN ('pre_teste','em_teste','em_construcao')) > 1 ) ) )
 )
BEGIN SELECT RAISE(ABORT,'familia_no_cemiterio'); END;

-- When the family is first written: requires payer; must be the best eligible family
-- (most matching columns, tie -> lowest familia_id) whenever any family matches 2 of 3.
CREATE VIEW v_familia_match AS
SELECT n.id AS nova, o.id AS outra, o.familia_id AS familia,
 ( COALESCE(o.pagador = n.pagador, 0)
 + ((SELECT COUNT(*) FROM ideia_concorrentes a JOIN ideia_concorrentes b ON b.concorrente_id=a.concorrente_id
     WHERE a.ideia_id=n.id AND b.ideia_id=o.id) >= 1)
 + COALESCE(1.0*(SELECT COUNT(*) FROM evidencias a JOIN evidencias b ON b.sinal_id=a.sinal_id
     WHERE a.ideia_id=n.id AND b.ideia_id=o.id)
     / NULLIF(MIN((SELECT COUNT(*) FROM evidencias WHERE ideia_id=n.id),(SELECT COUNT(*) FROM evidencias WHERE ideia_id=o.id)),0) >= 0.5, 0)
 ) AS colunas
FROM ideias n JOIN ideias o ON o.id <> n.id AND o.familia_id IS NOT NULL;

CREATE TRIGGER trg_familia_escolha BEFORE UPDATE OF familia_id ON ideias
WHEN OLD.familia_id IS NULL AND NEW.familia_id IS NOT NULL AND (
  NEW.pagador IS NULL
  OR ( EXISTS(SELECT 1 FROM v_familia_match WHERE nova=NEW.id AND colunas >= 2)
       AND NEW.familia_id <> (SELECT familia FROM v_familia_match WHERE nova=NEW.id AND colunas >= 2
                              ORDER BY colunas DESC, familia ASC LIMIT 1) ))
BEGIN SELECT RAISE(ABORT,'familia_errada'); END;

-- After the family is set, the payer cannot change (prevents escaping the graveyard by switching payer).
CREATE TRIGGER trg_pagador_fixo BEFORE UPDATE OF pagador ON ideias
WHEN OLD.familia_id IS NOT NULL AND NEW.pagador IS NOT OLD.pagador
BEGIN SELECT RAISE(ABORT,'pagador_imutavel_apos_familia'); END;

-- A serious death motive cannot be changed (prevents "laundering" the death).
CREATE TRIGGER trg_morte_imutavel BEFORE UPDATE OF motivo_morte ON ideias
WHEN OLD.estado IN ('morta','arquivada') AND NEW.estado=OLD.estado AND NEW.motivo_morte IS NOT OLD.motivo_morte
 AND OLD.motivo_morte IN ('teste_reprovado','advogado_do_diabo','risco_banimento','excluida_por_regra')
BEGIN SELECT RAISE(ABORT,'motivo_morte_grave_imutavel'); END;

-- Exploration quota: 1 active and 1 per month.
CREATE TRIGGER trg_exploracao BEFORE UPDATE OF exploracao ON ideias
WHEN NEW.exploracao=1 AND OLD.exploracao=0 AND (
  NEW.exploracao_em IS NULL OR NEW.exploracao_em <> date('now')
  OR EXISTS(SELECT 1 FROM ideias WHERE exploracao=1 AND id<>NEW.id
            AND estado IN ('candidata','pre_teste','em_teste','validada','em_construcao'))
  OR EXISTS(SELECT 1 FROM ideias WHERE exploracao=1 AND id<>NEW.id
            AND strftime('%Y-%m',exploracao_em)=strftime('%Y-%m',NEW.exploracao_em)))
BEGIN SELECT RAISE(ABORT,'cota_exploracao'); END;

-- Only the transitions of SKILL.md section 10.1 (any state may go to 'morta').
CREATE TRIGGER trg_transicao_valida BEFORE UPDATE OF estado ON ideias
WHEN NEW.estado<>OLD.estado AND NEW.estado<>'morta' AND NOT (
 (OLD.estado='sinal' AND NEW.estado='candidata') OR
 (OLD.estado='candidata' AND NEW.estado IN ('pre_teste','em_teste','em_construcao','arquivada','congelada')) OR
 (OLD.estado='pre_teste' AND NEW.estado IN ('em_teste','em_construcao','arquivada','congelada')) OR
 (OLD.estado='em_teste' AND NEW.estado IN ('validada','arquivada','congelada')) OR
 (OLD.estado='validada' AND NEW.estado IN ('em_construcao','arquivada')) OR
 (OLD.estado='em_construcao' AND NEW.estado IN ('lancada','congelada')) OR
 (OLD.estado='lancada' AND NEW.estado IN ('congelada','arquivada')) OR
 (OLD.estado='congelada' AND NEW.estado IN ('lancada','candidata','arquivada')) OR
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
