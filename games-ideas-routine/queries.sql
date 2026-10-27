-- Ready-made queries. Use these instead of writing new SQL for the recurring decisions.

-- name: q_portfolio_vagas
SELECT 4 - COALESCE(SUM(estado='pre_teste'),0)     AS vagas_pre_teste,
       2 - COALESCE(SUM(estado='em_teste'),0)      AS vagas_teste,
       1 - COALESCE(SUM(estado='em_construcao'),0) AS vagas_construcao,
       1 - COALESCE(SUM(trilha='S' AND estado IN ('em_teste','validada','em_construcao')),0) AS vagas_aposta_steam,
       COALESCE(SUM(estado='lancada'),0)           AS lancadas
FROM ideias;

-- name: q_gasto_ideia   (:ideia_id)
SELECT COALESCE(SUM(valor_brl),0) AS gasto_brl FROM gastos WHERE ideia_id = :ideia_id AND categoria <> 'plataforma';

-- name: q_gasto_mes   (monthly test cap; platform fees have a separate budget)
SELECT COALESCE(SUM(valor_brl),0) AS gasto_mes_brl FROM gastos
WHERE strftime('%Y-%m', data) = strftime('%Y-%m', 'now') AND categoria <> 'plataforma';

-- name: q_fontes_distintas_por_ideia   (candidate rule, section 3.2 item 4; 'tendencia' and 'outro' never count)
SELECT e.ideia_id,
  -- platforms with measured traction; an 'arbitragem' signal documents the gap on a target platform and is counted apart
  COUNT(DISTINCT CASE WHEN s.tipo IN ('hit_plataforma','tag_coorte','jam_mecanica') THEN f.plataforma END) AS plataformas,
  COUNT(DISTINCT CASE WHEN s.tipo IN ('hit_plataforma','arbitragem','tag_coorte','jam_mecanica','concorrente') THEN s.id END) AS sinais_prova,
  SUM(s.tipo = 'reclamacao') AS sinais_reclamacao,
  SUM(f.plataforma = 'dono_campo') AS sinais_dono_campo,
  COUNT(*) AS sinais,
  -- the gap counts only on a platform without measured traction for the idea
  COUNT(DISTINCT CASE WHEN s.tipo = 'arbitragem' AND f.plataforma NOT IN (
        SELECT f2.plataforma FROM evidencias e2 JOIN sinais s2 ON s2.id = e2.sinal_id JOIN fontes f2 ON f2.id = s2.fonte_id
        WHERE e2.ideia_id = e.ideia_id AND e2.polaridade = 1 AND s2.tipo IN ('hit_plataforma','tag_coorte','jam_mecanica'))
      THEN f.plataforma END) AS plataformas_arbitragem
FROM evidencias e JOIN sinais s ON s.id = e.sinal_id JOIN fontes f ON f.id = s.fonte_id
WHERE e.polaridade = 1
  AND (s.url_status = 200 OR (s.url_status = 0 AND f.plataforma = 'dono_campo'))
  AND s.tipo NOT IN ('tendencia','outro')
GROUP BY e.ideia_id;

-- name: q_rendimento_fontes   (last 4 weeks; NULL = no history)
SELECT f.id, f.nome, f.plataforma, f.status, COUNT(s.id) AS sinais,
       SUM(CASE WHEN e.sinal_id IS NOT NULL THEN 1 ELSE 0 END) AS viraram_evidencia,
       CASE WHEN COUNT(s.id) = 0 THEN NULL
            ELSE 1.0 * SUM(CASE WHEN e.sinal_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(s.id) END AS rendimento
FROM fontes f
LEFT JOIN sinais s ON s.fonte_id = f.id AND s.coletado_em >= datetime('now','-28 days')
LEFT JOIN (SELECT DISTINCT sinal_id FROM evidencias) e ON e.sinal_id = s.id
WHERE f.status IN ('ok','degradada') AND f.frequencia <> 'manual'
GROUP BY f.id ORDER BY rendimento DESC;

-- name: q_tracao_concorrente   (growth normalized to 30 days, same measure; only with >= 2 snapshots >= 7 days apart)
WITH s AS (
  SELECT concorrente_id, pais, data, 'reviews_total' AS medida, reviews_total AS v FROM concorrente_snapshots WHERE rank_lista = '' AND reviews_total IS NOT NULL
  UNION ALL SELECT concorrente_id, pais, data, 'ccu_pico_14d', ccu_pico_14d FROM concorrente_snapshots WHERE rank_lista = '' AND ccu_pico_14d IS NOT NULL
  UNION ALL SELECT concorrente_id, pais, data, 'favoritos', favoritos FROM concorrente_snapshots WHERE rank_lista = '' AND favoritos IS NOT NULL
  UNION ALL SELECT concorrente_id, pais, data, 'ratings_count', ratings_count FROM concorrente_snapshots WHERE rank_lista = '' AND ratings_count IS NOT NULL
  UNION ALL SELECT concorrente_id, pais, data, 'installs_min', installs_min FROM concorrente_snapshots WHERE rank_lista = '' AND installs_min IS NOT NULL
)
SELECT a.concorrente_id, a.pais, a.medida, a.data AS data_atual, b.data AS data_base, a.v - b.v AS delta,
       ROUND((a.v - b.v) * 30.0 / (julianday(a.data) - julianday(b.data))) AS delta_30d
FROM s a JOIN s b ON b.concorrente_id = a.concorrente_id AND b.pais = a.pais AND b.medida = a.medida
WHERE a.data = (SELECT MAX(data) FROM s x WHERE x.concorrente_id = a.concorrente_id AND x.pais = a.pais AND x.medida = a.medida)
  AND b.data = (SELECT MIN(data) FROM s y WHERE y.concorrente_id = a.concorrente_id AND y.pais = a.pais AND y.medida = a.medida
                AND y.data >= date(a.data, '-30 days'))
  AND julianday(a.data) - julianday(b.data) >= 7;

-- name: q_coorte_tag   (:tag) — cohort health of a genre tag: last 3 cohort years, latest snapshot of each
SELECT t.tag, t.ano, t.lancamentos, t.mediana_copias, t.p_10k, t.p_100k, t.data, t.fonte
FROM tag_coortes t
WHERE t.tag = :tag AND t.data = (SELECT MAX(data) FROM tag_coortes x WHERE x.tag = t.tag AND x.ano = t.ano)
ORDER BY t.ano DESC LIMIT 3;

-- name: q_tendencia_meia_vida   (:concorrente_id) — leader of a trend: peak and latest CCU (or plays) in the last 120 days
SELECT MAX(COALESCE(ccu, plays)) AS pico,
       (SELECT COALESCE(ccu, plays) FROM concorrente_snapshots WHERE concorrente_id = :concorrente_id AND rank_lista = ''
        ORDER BY data DESC LIMIT 1) AS atual,
       (SELECT data FROM concorrente_snapshots WHERE concorrente_id = :concorrente_id AND rank_lista = ''
        ORDER BY COALESCE(ccu, plays) DESC, data ASC LIMIT 1) AS data_pico
FROM concorrente_snapshots WHERE concorrente_id = :concorrente_id AND rank_lista = '' AND data >= date('now','-120 days');

-- name: q_hipoteses_abertas   (the deadline counts from the milestone = experimentos.inicio; 'planejado' never expires)
SELECT h.*, x.estado AS exp_estado, x.inicio,
       CASE WHEN x.inicio IS NULL THEN 0
            -- the deadline plus the reading grace period (7.4: a reading may arrive after the deadline)
            ELSE date('now') > date(x.inicio, '+' || (h.prazo_dias * (1 + h.estendida)
                                     + COALESCE((SELECT CAST(valor AS INTEGER) FROM config WHERE chave='leitura_carencia_dias'), 0)) || ' days') END AS prazo_esgotado
FROM hipoteses h JOIN experimentos x ON x.id = h.experimento_id
WHERE h.resultado IS NULL AND x.estado IN ('planejado','rodando');

-- name: q_metricas_experimento   (:experimento_id) — accumulated totals (each row is 1 day or 1 reading increment)
SELECT metrica, SUM(valor) AS total FROM metricas WHERE experimento_id = :experimento_id GROUP BY metrica;

-- name: q_checklist   (every column must be 0)
SELECT
 (SELECT COUNT(DISTINCT c.id) FROM concorrentes c
   JOIN ideia_concorrentes ic ON ic.concorrente_id = c.id
   JOIN ideias i ON i.id = ic.ideia_id AND i.estado NOT IN ('morta','arquivada')
   -- only stores with a per-game source in fontes (portal and Google Play pages have none: 4.1)
   WHERE c.loja IN ('steam','roblox','uefn','appstore')
     AND NOT EXISTS (SELECT 1 FROM concorrente_snapshots cs WHERE cs.concorrente_id = c.id AND cs.rank_lista = ''
     -- a snapshot counts only with a popularity number (a price-only reading is not a photo)
     AND (COALESCE(cs.reviews_total, cs.ccu, cs.plays, cs.ratings_count, cs.installs_min, cs.favoritos) IS NOT NULL
          OR c.loja = 'uefn')   -- an all-null UEFN reading means < 5 unique players (4.1)
     AND cs.data >= CASE WHEN c.loja IN ('uefn','roblox')
                          AND EXISTS (SELECT 1 FROM ideia_concorrentes ic2 JOIN ideias i2 ON i2.id = ic2.ideia_id
                                      WHERE ic2.concorrente_id = c.id AND i2.estado IN ('pre_teste','em_teste','validada','em_construcao','lancada'))
                         THEN date('now') ELSE date('now','-6 days') END)) AS concorrentes_sem_foto,
 (SELECT COUNT(*) FROM experimentos x WHERE x.estado = 'rodando' AND x.inicio <= date('now','-7 days')
   AND x.tipo IN ('pagina_steam','demo_playtest','cpi_teste','roblox_mvp')
   AND NOT EXISTS (SELECT 1 FROM metricas m WHERE m.experimento_id = x.id AND m.data >= date('now','-7 days'))
   -- UEFN is read from the API: a null day (< 5 players) has no row by rule (4.1)
   AND COALESCE((SELECT plataforma FROM ideias WHERE id = x.ideia_id),'') <> 'uefn') AS experimentos_sem_leitura_7d,
 (SELECT COUNT(*) FROM ideias WHERE estado = 'morta' AND motivo_morte IS NULL) AS mortas_sem_motivo,
 (SELECT COUNT(*) FROM tendencias WHERE status = 'aberta'
   AND detectada_em < date('now','-' || (COALESCE((SELECT CAST(valor AS INTEGER) FROM config WHERE chave='tendencia_janela_semanas'),6) * 7) || ' days')) AS tendencias_abertas_vencidas,
 -- prototype hours beyond 1.5x the estimate: a pending item to the owner (cut scope, freeze or continue)
 (SELECT COUNT(*) FROM ideias i WHERE i.estado IN ('pre_teste','em_teste') AND i.horas_estimadas IS NOT NULL
   AND (SELECT COALESCE(SUM(h.horas),0) FROM horas h WHERE h.ideia_id = i.id AND h.tipo IN ('validacao','marketing'))
       > 1.5 * i.horas_estimadas
   -- one item per idea: once the owner answered (continue) it does not re-arm
   AND NOT EXISTS (SELECT 1 FROM pendencias p WHERE (p.ideia_id = i.id OR (' ' || p.texto || ' ') GLOB ('*ideia#' || i.id || '[^0-9]*'))
                   AND p.texto LIKE 'horas estouradas%' AND p.cancelada_em IS NULL)) AS horas_estouradas,
 (SELECT COUNT(*) FROM ideias i WHERE i.reabrir_se IS NULL
   AND ( (i.estado = 'morta' AND i.motivo_morte IN ('sem_canal','mercado_saturado','depende_fila','escopo_grande','custo_alto','risco_plataforma','janela_fechada','loop_vazio'))
      OR i.estado = 'arquivada' )) AS mortas_sem_reabrir_se,
 (SELECT COUNT(*) FROM ideias i WHERE i.estado NOT IN ('sinal','candidata') AND i.familia_id IS NULL
   -- an idea archived before the gate (q_sinais_parados, sem_mesa) never got a family
   AND NOT (i.estado = 'arquivada' AND NOT EXISTS (SELECT 1 FROM ideia_eventos e WHERE e.ideia_id = i.id
            AND e.para IN ('pre_teste','em_teste','validada','em_construcao','lancada')))) AS ideias_sem_familia,
 (SELECT COUNT(*) FROM ideias WHERE estado IN ('pre_teste','em_teste','validada','em_construcao','lancada')
   AND (trilha IS NULL OR plataforma IS NULL OR modo IS NULL OR hook IS NULL OR twist IS NULL OR horas_estimadas IS NULL)) AS ideias_sem_ficha,
 (SELECT COUNT(*) FROM (SELECT ideia_id FROM gastos WHERE ideia_id IS NOT NULL AND categoria <> 'plataforma'
   GROUP BY ideia_id HAVING SUM(valor_brl) > (SELECT CAST(valor AS REAL) FROM config WHERE chave='teto_gasto_ideia_brl'))) AS ideias_acima_teto,
 (SELECT CASE WHEN COALESCE(SUM(valor_brl),0) > (SELECT CAST(valor AS REAL) FROM config WHERE chave='teto_gasto_mes_brl') THEN 1 ELSE 0 END
   FROM gastos WHERE strftime('%Y-%m', data) = strftime('%Y-%m','now') AND categoria <> 'plataforma') AS mes_acima_teto,
 (SELECT COUNT(*) FROM benchmarks_vigentes WHERE usar_em_calculo = 1 AND date(verificado_em) < date('now','-90 days')) AS benchmarks_vencidos,
 (SELECT COUNT(*) FROM sinais s JOIN evidencias e ON e.sinal_id = s.id JOIN fontes f ON f.id = s.fonte_id
   WHERE NOT (s.url_status = 200 OR (s.url_status = 0 AND f.plataforma = 'dono_campo'))) AS evidencias_sem_url_ok,
 (SELECT COUNT(*) FROM ideias WHERE estado = 'candidata' AND score IS NULL
   AND atualizada_em < datetime('now', '-' || (SELECT valor FROM config WHERE chave='candidata_pendente_dias') || ' days')) AS candidatas_paradas,
 (SELECT COUNT(DISTINCT v.concorrente_id) FROM v_tendencia_detectada v
   JOIN ideia_concorrentes ic ON ic.concorrente_id = v.concorrente_id AND ic.papel = 'referencia'
   JOIN ideias i ON i.id = ic.ideia_id AND i.estado NOT IN ('morta','arquivada')
   WHERE NOT EXISTS (SELECT 1 FROM tendencias t WHERE t.loja = v.loja AND t.id_loja = v.id_loja)) AS tendencias_nao_registradas,
 (SELECT COUNT(*) FROM ideias i WHERE i.estado IN ('lancada','congelada')
   AND (SELECT MAX(em) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'lancada') < datetime('now','-45 days')
   AND NOT EXISTS (SELECT 1 FROM receita_snapshots r WHERE r.ideia_id = i.id AND r.data = date('now','start of month','-1 month'))) AS lancadas_sem_extrato,
 (SELECT COUNT(*) FROM ideias i WHERE i.estado = 'em_teste'
   AND NOT EXISTS (SELECT 1 FROM experimentos x WHERE x.ideia_id = i.id AND x.estado IN ('planejado','rodando'))
   AND MAX(i.atualizada_em, COALESCE((SELECT MAX(fim) FROM experimentos z WHERE z.ideia_id = i.id), '0'))
       < datetime('now', '-' || (SELECT valor FROM config WHERE chave='em_teste_sem_experimento_dias') || ' days')) AS em_teste_sem_experimento;

-- name: q_meta_portfolio   (goal, section 1: net revenue and hours of the last 12 CLOSED months, in USD and in R$/h at
--                       config cambio_usd_brl; months whose summed portfolio net >= meta_mensal_usd)
SELECT
 (SELECT COALESCE(SUM(receita_liquida_usd),0) FROM receita_snapshots
   WHERE data >= date('now','start of month','-12 months') AND data < date('now','start of month')) AS liquido_12m_usd,
 (SELECT COALESCE(SUM(horas),0) FROM horas
   WHERE data >= date('now','start of month','-12 months') AND data < date('now','start of month')) AS horas_12m,
 (SELECT COUNT(*) FROM (SELECT strftime('%Y-%m', data) AS mes FROM receita_snapshots GROUP BY mes
   HAVING SUM(receita_liquida_usd) >= (SELECT CAST(valor AS REAL) FROM config WHERE chave='meta_mensal_usd'))) AS meses_meta_ok,
 (SELECT COUNT(DISTINCT ideia_id) FROM ideia_eventos WHERE para = 'lancada') AS lancamentos,
 (SELECT COUNT(*) FROM experimentos WHERE estado = 'encerrado' AND etapa IN ('W1','S1','S2','M1','R1')
   AND decisao IN ('passa','mata')) AS testes_concluidos,   -- a test without a sample measured no behavior
 (SELECT COUNT(*) FROM experimentos WHERE estado = 'encerrado' AND etapa IN ('W1','S1','S2','M1','R1')
   AND decisao = 'sem_amostra') AS testes_sem_amostra,
 (SELECT MIN(iniciado_em) FROM runs WHERE tipo = 'bootstrap') AS inicio_rotina,
 ROUND((SELECT COALESCE(SUM(receita_liquida_usd),0) FROM receita_snapshots
         WHERE data >= date('now','start of month','-12 months') AND data < date('now','start of month'))
       * (SELECT CAST(valor AS REAL) FROM config WHERE chave='cambio_usd_brl')
       / NULLIF((SELECT SUM(horas) FROM horas
         WHERE data >= date('now','start of month','-12 months') AND data < date('now','start of month')), 0), 2) AS rs_por_hora_12m;

-- name: q_rs_por_hora_ideia   (net R$/h per idea; cambio = :cambio)
SELECT i.id, i.titulo, i.genero_central, i.trilha,
  COALESCE((SELECT SUM(receita_liquida_usd) FROM receita_snapshots r WHERE r.ideia_id = i.id),0) * :cambio AS liquido_brl,
  COALESCE((SELECT SUM(horas) FROM horas h WHERE h.ideia_id = i.id),0) AS horas,
  ROUND(COALESCE((SELECT SUM(receita_liquida_usd) FROM receita_snapshots r WHERE r.ideia_id = i.id),0) * :cambio
        / NULLIF((SELECT SUM(horas) FROM horas h WHERE h.ideia_id = i.id),0), 2) AS brl_por_hora
FROM ideias i WHERE EXISTS (SELECT 1 FROM horas h WHERE h.ideia_id = i.id)
ORDER BY brl_por_hora DESC;

-- name: q_runs_trava   (suggest an adjustment if > 3 in the last 7)
SELECT SUM(motivo_parada IN ('teto_tempo','teto_buscas')) AS paradas_por_trava
FROM (SELECT motivo_parada FROM runs WHERE tipo = 'diaria' ORDER BY id DESC LIMIT 7);

-- name: q_erro_previsao   (calibration)
-- the S1 extension records 28-day cumulative wishlists: halve it to the 14-day unit of the previsao
SELECT etapa, metrica, COUNT(*) AS n,
  AVG(CASE WHEN etapa = 'S1' AND estendida = 1 THEN valor_observado / 2.0 ELSE valor_observado END - previsao) AS erro_medio
FROM hipoteses WHERE resultado IN ('confirmada','refutada') AND valor_observado IS NOT NULL
GROUP BY etapa, metrica;

-- name: q_reabrir_candidatas   (evaluate reabrir_se; 1st Sunday of the month or when a 'plataforma'/'regulacao' signal cites the reference)
SELECT i.id, i.titulo, i.estado, i.motivo_morte, i.reabrir_se, i.familia_id,
  -- 1 = the routine already reopened it once: when the condition is true, open a pending item asking for
  --     "reabro a ideia#N" instead of reopening (10.2)
  EXISTS (SELECT 1 FROM ideia_eventos ev WHERE ev.ideia_id = i.id AND ev.motivo LIKE 'REABERTA:%' AND ev.ator = 'rotina'
          AND ev.de IN ('morta','arquivada')) AS ja_reaberta_pela_rotina
FROM ideias i
WHERE i.estado IN ('morta','arquivada') AND i.reabrir_se IS NOT NULL
  AND i.reabrir_se NOT LIKE 'recriada como ideia#%'   -- replaced ideas never reopen
  AND i.reabrir_se NOT LIKE 'dono pede%'   -- the owner's rejection reopens only through the owner
  AND i.exploracao = 0   -- an exploration reopens only through the owner (trg_exploracao_reaberta)
  AND COALESCE(i.fonte_ideia,'') <> 'tendencia'   -- a new trend means a NEW idea linked to the new leader (4.4), not a reopening
  AND (i.motivo_morte IS NULL OR i.motivo_morte NOT IN ('teste_reprovado','advogado_do_diabo','clone_legal','excluida_por_regra'));

-- name: q_exploracao_mes   (quota: 1 per month, 1 active)
SELECT
 (SELECT COUNT(*) FROM ideias WHERE exploracao = 1 AND estado IN ('candidata','pre_teste','em_teste','validada','em_construcao')) AS ativas,
 (SELECT COUNT(*) FROM ideias x WHERE x.exploracao = 1 AND strftime('%Y-%m', x.exploracao_em) = strftime('%Y-%m','now')
   AND (x.estado IN ('candidata','pre_teste','em_teste','validada','em_construcao','lancada')
        OR EXISTS (SELECT 1 FROM ideia_eventos e WHERE e.ideia_id = x.id AND e.para = 'em_teste'))) AS no_mes;

-- name: q_familia_sugerida   (:ideia_id) — first row = the family to inherit when colunas >= 2 (most columns, tie -> lowest familia_id)
WITH m AS (
SELECT o.id, o.familia_id, o.estado, o.motivo_morte,
 COALESCE(o.genero_central = n.genero_central, 0) AS mesmo_genero,
 (SELECT COUNT(*) FROM ideia_concorrentes a JOIN ideia_concorrentes b ON b.concorrente_id = a.concorrente_id
   JOIN concorrentes k ON k.id = a.concorrente_id
   WHERE a.ideia_id = n.id AND b.ideia_id = o.id AND k.proprio_ideia_id IS NULL) >= 1 AS concorrente_comum,
 COALESCE(1.0 * (SELECT COUNT(*) FROM evidencias a JOIN evidencias b ON b.sinal_id = a.sinal_id JOIN sinais s ON s.id = a.sinal_id
     WHERE a.ideia_id = n.id AND b.ideia_id = o.id AND s.tipo IN ('hit_plataforma','arbitragem','jam_mecanica','concorrente','reclamacao'))
   / NULLIF(MIN((SELECT COUNT(*) FROM evidencias e JOIN sinais s ON s.id = e.sinal_id WHERE e.ideia_id = n.id
                 AND s.tipo IN ('hit_plataforma','arbitragem','jam_mecanica','concorrente','reclamacao')),
                (SELECT COUNT(*) FROM evidencias e JOIN sinais s ON s.id = e.sinal_id WHERE e.ideia_id = o.id
                 AND s.tipo IN ('hit_plataforma','arbitragem','jam_mecanica','concorrente','reclamacao'))), 0) >= 0.5, 0) AS metade_sinais
FROM ideias o, ideias n WHERE n.id = :ideia_id AND o.id <> n.id AND o.familia_id IS NOT NULL
  -- older ideas, plus newer ones still alive (an older idea that waited in 'sinal')
  AND (o.id < n.id OR o.estado NOT IN ('morta','arquivada'))
  AND NOT (o.estado = 'arquivada' AND o.arquivamento IS 'operacional' AND COALESCE(o.reabrir_se,'') LIKE 'recriada como ideia#%'))
SELECT *, mesmo_genero + concorrente_comum + metade_sinais AS colunas FROM m
ORDER BY colunas DESC, familia_id ASC;

-- name: q_orcamento_experimentos   (alert at 80%)
SELECT x.id AS experimento_id, x.ideia_id, MAX(h.orcamento_max_brl) AS orcamento,
       COALESCE((SELECT SUM(valor_brl) FROM gastos g WHERE g.experimento_id = x.id), 0) AS gasto,
       COALESCE((SELECT SUM(valor_brl) FROM gastos g WHERE g.experimento_id = x.id), 0) >= 0.8 * MAX(h.orcamento_max_brl) AS alerta_80
FROM experimentos x JOIN hipoteses h ON h.experimento_id = x.id
WHERE x.estado = 'rodando' AND h.orcamento_max_brl > 0 GROUP BY x.id;

-- name: q_etapa_status   (:experimento_id) — the stage passes if ALL hypotheses passed; dies if ANY was refuted
SELECT COALESCE(SUM(resultado = 'confirmada'),0) AS confirmadas, COALESCE(SUM(resultado = 'refutada'),0) AS refutadas,
       COALESCE(SUM(resultado IS NULL),0) AS abertas, COALESCE(SUM(resultado LIKE 'inconclusiva%'),0) AS inconclusivas, COUNT(*) AS total
FROM hipoteses WHERE experimento_id = :experimento_id;

-- name: q_planejados_vencidos   (experiment stuck in 'planejado' beyond the stage limit -> idea archived; S3/S4/E5 excluded)
SELECT x.id AS experimento_id, x.ideia_id, x.etapa, MIN(h.criada_em) AS criada_em
FROM experimentos x LEFT JOIN hipoteses h ON h.experimento_id = x.id
WHERE x.estado = 'planejado' AND x.etapa NOT IN ('S3','S4','E5')
GROUP BY x.id
HAVING COALESCE(MIN(h.criada_em), (SELECT atualizada_em FROM ideias WHERE id = x.ideia_id)) < datetime('now', '-' || (SELECT valor FROM config WHERE chave =
   CASE x.etapa WHEN 'G1' THEN 'planejado_max_dias_g1' WHEN 'S1' THEN 'planejado_max_dias_s1' WHEN 'S2' THEN 'planejado_max_dias_s2'
                ELSE 'planejado_max_dias_prototipo' END) || ' days');

-- name: q_experimentos_a_fechar   (every hypothesis decided, experiment still open)
SELECT x.id AS experimento_id, x.ideia_id, x.etapa, x.estado
FROM experimentos x
WHERE x.estado IN ('planejado','rodando')
  AND NOT EXISTS (SELECT 1 FROM hipoteses h WHERE h.experimento_id = x.id AND h.resultado IS NULL)
  AND EXISTS (SELECT 1 FROM hipoteses h WHERE h.experimento_id = x.id);

-- name: q_fix_first_familia   (:familia_id) — FIX-FIRST holds once per family
SELECT COUNT(*) AS usados FROM ideia_eventos e JOIN ideias i ON i.id = e.ideia_id
WHERE i.familia_id = :familia_id AND e.motivo LIKE 'FIX-FIRST:%';

-- name: q_experimentos_orfaos   (open experiment whose idea already left the stage's state -> close without applying a destination)
SELECT x.id AS experimento_id, x.ideia_id, x.etapa, i.estado
FROM experimentos x JOIN ideias i ON i.id = x.ideia_id
WHERE x.estado IN ('planejado','rodando')
  AND NOT ( (x.etapa = 'G1' AND i.estado = 'pre_teste')
         OR (x.etapa IN ('W1','W2','S1','S2','M1','R1') AND i.estado = 'em_teste')
         OR (x.etapa IN ('S3','S4') AND i.estado IN ('em_construcao','lancada'))
         OR (x.etapa = 'E5' AND i.estado IN ('lancada','congelada')) );

-- name: q_pre_teste_parado   (queue: pre_teste with no open experiment for more than pre_teste_espera_dias -> archive with reabrir_se;
--                         paused for S while the Steam bet is taken)
SELECT i.id, i.trilha, MAX(i.atualizada_em) AS desde
FROM ideias i
WHERE i.estado = 'pre_teste'
  AND NOT EXISTS (SELECT 1 FROM experimentos y WHERE y.ideia_id = i.id AND y.estado IN ('planejado','rodando'))
  -- the clock of an S idea is paused while the single Steam bet is taken
  AND NOT (i.trilha = 'S' AND EXISTS (SELECT 1 FROM ideias b WHERE b.trilha = 'S' AND b.id <> i.id
                                      AND b.estado IN ('em_teste','validada','em_construcao')))
  AND MAX(i.atualizada_em, COALESCE((SELECT MAX(fim) FROM experimentos z WHERE z.ideia_id = i.id), '0'),
          -- S: the wait counts from the last release of the Steam bet
          CASE WHEN i.trilha = 'S' THEN COALESCE((SELECT MAX(e.em) FROM ideia_eventos e JOIN ideias b ON b.id = e.ideia_id
               WHERE b.trilha = 'S' AND b.id <> i.id AND e.de IN ('em_teste','validada','em_construcao')
                 AND e.para NOT IN ('em_teste','validada','em_construcao')), '0') ELSE '0' END)
      < date('now', '-' || (SELECT valor FROM config WHERE chave = 'pre_teste_espera_dias') || ' days')
GROUP BY i.id;

-- name: q_congeladas_vencidas   (seasonal/window with data_reativacao reached -> candidata; other frozen for more than congelada_max_meses -> arquivada)
WITH ult AS (
  SELECT i.id, i.data_reativacao,
    (SELECT de FROM ideia_eventos WHERE id = (SELECT MAX(id) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'congelada')) AS veio_de,
    (SELECT MAX(em) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'congelada') AS congelada_em,
    (SELECT COUNT(*) FROM ideia_eventos WHERE ideia_id = i.id AND de = 'congelada' AND para = 'candidata') AS reativacoes
  FROM ideias i WHERE i.estado = 'congelada')
SELECT id, veio_de, data_reativacao,
  CASE WHEN data_reativacao IS NOT NULL AND data_reativacao <= date('now')
            AND veio_de IN ('candidata','pre_teste','em_teste') AND reativacoes = 0 THEN 'reativar'
       WHEN congelada_em < datetime('now', '-' || (SELECT valor FROM config WHERE chave='congelada_max_meses') || ' months')
            AND veio_de <> 'lancada'   -- a live game frozen by E5 stays monitored
            AND NOT (data_reativacao IS NOT NULL AND veio_de IN ('candidata','pre_teste','em_teste') AND reativacoes = 0) THEN 'arquivar'
  END AS acao
FROM ult WHERE acao IS NOT NULL;

-- name: q_validada_parada   (validada with a free build slot and no owner decision: after validada_max_dias -> pending item
--                         (idea stays validada); after validada_max_dias_arquivar -> archive)
WITH v AS (
  SELECT i.id, MAX((SELECT MAX(em) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'validada'),
                   COALESCE((SELECT MAX(em) FROM ideia_eventos WHERE de = 'em_construcao'), '0')) AS desde
  FROM ideias i WHERE i.estado = 'validada'
    AND NOT EXISTS (SELECT 1 FROM ideias c WHERE c.estado = 'em_construcao'))
SELECT id, CASE WHEN desde < datetime('now', '-' || (SELECT valor FROM config WHERE chave='validada_max_dias_arquivar') || ' days')
                THEN 'arquivar' ELSE 'pendencia' END AS acao
FROM v WHERE desde < datetime('now', '-' || (SELECT valor FROM config WHERE chave='validada_max_dias') || ' days')
UNION ALL
-- validada waiting behind a build in progress: ask the owner (freeze the build or keep waiting); never archive
SELECT i.id, 'pendencia_vaga' FROM ideias i WHERE i.estado = 'validada'
  AND EXISTS (SELECT 1 FROM ideias c WHERE c.estado = 'em_construcao')
  AND (SELECT MAX(em) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'validada')
      < datetime('now', '-' || (SELECT valor FROM config WHERE chave='validada_max_dias') || ' days');

-- name: q_horas_prototipo   (:ideia_id) — validation hours spent on the idea vs. the track cap (section 7.2)
SELECT COALESCE(SUM(horas),0) AS horas_validacao FROM horas WHERE ideia_id = :ideia_id AND tipo IN ('validacao','marketing');

-- name: q_construcao_longa   (em_construcao above the track's build cap in hours or weeks -> pending item to the owner)
SELECT i.id, i.trilha,
  (SELECT COALESCE(SUM(horas),0) FROM horas WHERE ideia_id = i.id AND tipo = 'construcao') AS horas_construcao,
  (SELECT MAX(em) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'em_construcao') AS desde
FROM ideias i WHERE i.estado = 'em_construcao'
  AND ( (SELECT COALESCE(SUM(horas),0) FROM horas WHERE ideia_id = i.id AND tipo = 'construcao')
        > (SELECT CAST(valor AS REAL) FROM config WHERE chave = 'construcao_horas_max_' || lower(i.trilha))
     OR (SELECT MAX(em) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'em_construcao')
        < datetime('now', '-' || ((SELECT CAST(valor AS INTEGER) FROM config WHERE chave = 'construcao_max_semanas_' || lower(i.trilha)) * 7) || ' days') );

-- name: q_lista_publica   (:ideia_id) — density rule to switch on the public room list (section 6.4), last 14 days of own telemetry.
-- Switch on only if dias_salas_ok > 7 OR ccu_ok = 1.
SELECT COALESCE(MAX(CASE WHEN m.metrica = 'ccu_pico' THEN m.valor END),0) AS ccu_pico_14d,
       (SELECT tamanho_sala FROM ideias WHERE id = :ideia_id) AS tamanho_sala,
       COUNT(DISTINCT CASE WHEN m.metrica = 'salas_abertas_pico'
             AND m.valor >= (SELECT CAST(valor AS REAL) FROM config WHERE chave='lista_publica_min_salas') THEN m.data END) AS dias_salas_ok,
       COUNT(DISTINCT CASE WHEN m.metrica = 'ccu_pico'
             AND m.valor >= (SELECT CAST(valor AS REAL) FROM config WHERE chave='lista_publica_ccu_mult') * (SELECT tamanho_sala FROM ideias WHERE id = :ideia_id)
             THEN m.data END) > 7   -- sustained: more than 7 of the 14 days
       -- CCU is only a fallback: measured open rooms (salas_abertas_pico) always decide
       AND COUNT(CASE WHEN m.metrica = 'salas_abertas_pico' THEN 1 END) = 0 AS ccu_ok
FROM metricas m JOIN experimentos x ON x.id = m.experimento_id
WHERE x.ideia_id = :ideia_id AND m.data > date('now','-14 days');   -- exactly the last 14 dates

-- name: q_candidatas_paradas   (candidata without score for more than candidata_pendente_dias -> arquivada, reabrir_se = the missing
--                           criterion; scored but without a slot for more than candidata_fila_dias -> arquivada, reabrir_se =
--                           'vaga de teste livre e ideia ainda no topo do score')
--                           a scored idea blocked by its family's graveyard (familia_no_cemiterio) for candidata_fila_dias
--                           -> 'bloqueada_cemiterio': arquivada (operacional), reabrir_se = the blocking sibling's reabrir_se
SELECT id, titulo, atualizada_em,
  CASE WHEN score IS NULL THEN 'sem_mesa'
       WHEN EXISTS (SELECT 1 FROM ideias m WHERE m.familia_id = ideias.familia_id AND m.id < ideias.id
              AND (m.estado = 'morta' OR (m.estado = 'arquivada' AND m.arquivamento IS NOT 'operacional'))
              AND NOT EXISTS (SELECT 1 FROM ideia_eventos l WHERE l.ideia_id = m.id AND l.para = 'lancada')) 
            AND NOT EXISTS (SELECT 1 FROM ideia_eventos e WHERE e.ideia_id = ideias.id AND e.ator = 'dono' AND e.motivo LIKE 'REABERTA:%'
                                -- mirrors trg_familia_cemiterio: an owner REABERTA since the last entry in candidata and after the sibling's death
                                AND e.id >= (SELECT MAX(id) FROM ideia_eventos WHERE ideia_id = ideias.id AND para = 'candidata' AND de <> 'candidata')
                                AND e.id > COALESCE((SELECT MAX(d.id) FROM ideia_eventos d JOIN ideias m ON m.id = d.ideia_id
                                                     WHERE m.familia_id = ideias.familia_id AND m.id < ideias.id AND d.para = 'morta'), 0)) THEN 'bloqueada_cemiterio'
       ELSE 'sem_vaga' END AS motivo FROM ideias
WHERE estado = 'candidata'
  AND ( (score IS NULL AND atualizada_em < datetime('now', '-' || (SELECT valor FROM config WHERE chave='candidata_pendente_dias') || ' days'))
     OR (score IS NOT NULL
         -- no slot: the pre_teste queue is full (4), the family already holds its slot (trg_familia), or the family's
         -- graveyard blocks the entry (no REABERTA since the idea's last entry in candidata)
         AND ( (SELECT COUNT(*) FROM ideias p WHERE p.estado = 'pre_teste') >= 4
            OR (EXISTS (SELECT 1 FROM ideias m WHERE m.familia_id = ideias.familia_id AND m.id < ideias.id
              AND (m.estado = 'morta' OR (m.estado = 'arquivada' AND m.arquivamento IS NOT 'operacional'))
              AND NOT EXISTS (SELECT 1 FROM ideia_eventos l WHERE l.ideia_id = m.id AND l.para = 'lancada'))
                AND NOT EXISTS (SELECT 1 FROM ideia_eventos e WHERE e.ideia_id = ideias.id AND e.ator = 'dono' AND e.motivo LIKE 'REABERTA:%'
                                -- mirrors trg_familia_cemiterio: an owner REABERTA since the last entry in candidata and after the sibling's death
                                AND e.id >= (SELECT MAX(id) FROM ideia_eventos WHERE ideia_id = ideias.id AND para = 'candidata' AND de <> 'candidata')
                                AND e.id > COALESCE((SELECT MAX(d.id) FROM ideia_eventos d JOIN ideias m ON m.id = d.ideia_id
                                                     WHERE m.familia_id = ideias.familia_id AND m.id < ideias.id AND d.para = 'morta'), 0)))
            OR EXISTS (SELECT 1 FROM ideias f WHERE f.familia_id = ideias.familia_id AND f.id <> ideias.id
                       AND f.estado IN ('pre_teste','em_teste','validada','em_construcao')) )
         -- the wait counts from the entry in candidata or, for S, from the owner's Steam release
         AND MAX(atualizada_em, COALESCE((SELECT MAX(e.em) FROM ideia_eventos e WHERE e.ideia_id = ideias.id
                                          AND e.motivo LIKE 'LIBERACAO_STEAM:%'), '0'))
             < datetime('now', '-' || (SELECT valor FROM config WHERE chave='candidata_fila_dias') || ' days')
         -- an S idea waiting for the owner's Steam release (or for a launched web game) does not age out of the queue
         AND NOT (COALESCE(trilha,'') = 'S'
                  AND NOT EXISTS (SELECT 1 FROM ideias w JOIN ideia_eventos e ON e.ideia_id = w.id WHERE w.trilha = 'W' AND e.para = 'lancada')
                  AND NOT EXISTS (SELECT 1 FROM ideia_eventos e WHERE e.ideia_id = ideias.id AND e.ator = 'dono'
                                  AND lower(replace(e.prova_dono,'“','"') || ' ') GLOB ('"libero a aposta steam da ideia#' || ideias.id || '[^0-9]*')))) );

-- name: q_em_teste_sem_experimento   (em_teste with no open experiment: open the next stage of the track, or archive)
SELECT i.id, i.trilha FROM ideias i WHERE i.estado = 'em_teste'
  AND NOT EXISTS (SELECT 1 FROM experimentos x WHERE x.ideia_id = i.id AND x.estado IN ('planejado','rodando'))
  AND MAX(i.atualizada_em, COALESCE((SELECT MAX(fim) FROM experimentos z WHERE z.ideia_id = i.id), '0'))
      < datetime('now', '-' || (SELECT valor FROM config WHERE chave='em_teste_sem_experimento_dias') || ' days');

-- name: q_e5_escada   (E5: last CLOSED month net, all platforms summed; "no growth" = that month <= the month before;
--                   a month without any statement row, or missing a platform that reported before, is 'aguardar_extrato', never zero)
WITH b AS (
  SELECT i.id, i.estado,
    julianday('now') - julianday((SELECT MAX(em) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'lancada')) AS dias,
    (SELECT SUM(receita_liquida_usd) FROM receita_snapshots r WHERE r.ideia_id = i.id
     AND r.data = date('now','start of month','-1 month')) AS mes,
    (SELECT SUM(receita_liquida_usd) FROM receita_snapshots r WHERE r.ideia_id = i.id
     AND r.data = date('now','start of month','-2 months')) AS mes_anterior,
    -- a platform that already had a statement row is missing from the month (statements arrive on different schedules)
    EXISTS(SELECT 1 FROM receita_snapshots r WHERE r.ideia_id = i.id AND r.data < date('now','start of month','-1 month')
           AND r.fonte NOT IN (SELECT fonte FROM receita_snapshots WHERE ideia_id = i.id AND data = date('now','start of month','-1 month'))) AS falta_mes,
    EXISTS(SELECT 1 FROM receita_snapshots r WHERE r.ideia_id = i.id AND r.data < date('now','start of month','-2 months')
           AND r.fonte NOT IN (SELECT fonte FROM receita_snapshots WHERE ideia_id = i.id AND data = date('now','start of month','-2 months'))) AS falta_mes_anterior
  FROM ideias i WHERE i.estado IN ('lancada','congelada')
    AND EXISTS (SELECT 1 FROM ideia_eventos WHERE ideia_id = i.id AND para = 'lancada'))
SELECT id, estado, dias, mes, mes_anterior,
  CASE WHEN dias >= 60 AND (mes IS NULL OR (dias >= 120 AND mes_anterior IS NULL) OR falta_mes
                            OR (dias >= 120 AND falta_mes_anterior)) THEN 'aguardar_extrato'
       WHEN dias >= 120 AND mes < (SELECT CAST(valor AS REAL) FROM config WHERE chave='e5_d120_min_usd') AND mes <= mes_anterior THEN 'arquivar'
       WHEN estado = 'lancada' AND dias >= 60 AND mes < (SELECT CAST(valor AS REAL) FROM config WHERE chave='e5_d60_min_usd') THEN 'congelar'
  END AS acao
FROM b WHERE acao IS NOT NULL;

-- name: q_graduacao   (lancada game whose summed net was >= graduacao_receita_min_usd in each of the last graduacao_meses closed months)
SELECT i.id FROM ideias i WHERE i.estado = 'lancada'
  AND (SELECT COUNT(*) FROM (SELECT r.data, SUM(r.receita_liquida_usd) AS v FROM receita_snapshots r
         WHERE r.ideia_id = i.id AND r.data >= date('now','start of month', '-' || (SELECT valor FROM config WHERE chave='graduacao_meses') || ' months')
           AND r.data < date('now','start of month') GROUP BY r.data
         HAVING v >= (SELECT CAST(valor AS REAL) FROM config WHERE chave='graduacao_receita_min_usd')))
      = (SELECT CAST(valor AS INTEGER) FROM config WHERE chave='graduacao_meses');

-- name: q_pendencias_abertas   (owner pending items still open and not cancelled, oldest first)
SELECT id, ideia_id, texto, criada_em FROM pendencias WHERE resolvida_em IS NULL AND cancelada_em IS NULL ORDER BY criada_em;

-- name: q_tendencia_fechada_planejados   (planned experiments of ideas whose reference's trend closed while the leader is still
--                                     < 120 days old -> close as inconclusive and archive)
SELECT DISTINCT x.id AS experimento_id, x.ideia_id FROM experimentos x
JOIN ideia_concorrentes ic ON ic.ideia_id = x.ideia_id AND ic.papel = 'referencia'
JOIN v_tendencia_viva v ON v.concorrente_id = ic.concorrente_id
JOIN tendencias t ON t.loja = v.loja AND t.id_loja = v.id_loja AND t.status = 'fechada'
JOIN ideias i ON i.id = x.ideia_id AND i.estado IN ('pre_teste','em_teste')   -- a build follows 4.4 (pending item)
WHERE x.estado = 'planejado' AND x.etapa NOT IN ('S3','S4','E5');

-- name: q_sinais_parados   (idea stuck in 'sinal' for more than sinal_max_dias -> arquivada, arquivamento='operacional',
--                         reabrir_se = the missing candidacy criterion)
SELECT id, titulo, criada_em FROM ideias
WHERE estado = 'sinal' AND criada_em < datetime('now', '-' || (SELECT valor FROM config WHERE chave='sinal_max_dias') || ' days');

-- name: q_irmas_bloqueadas   (scored candidata blocked by an older sibling in the family's graveyard and not yet reopened.
--                           grave=1 (serious death) or the routine's one REABERTA per family already used -> open ONE pending
--                           item asking for "reabro a ideia#N"; otherwise the routine may reopen it once the sibling's
--                           reabrir_se is met (10.2))
SELECT i.id, i.titulo, i.familia_id,
  EXISTS (SELECT 1 FROM ideias m WHERE m.familia_id = i.familia_id AND m.id < i.id AND m.estado = 'morta'
          AND m.motivo_morte IN ('teste_reprovado','advogado_do_diabo','clone_legal','excluida_por_regra')) AS grave,
  EXISTS (SELECT 1 FROM ideia_eventos e JOIN ideias i2 ON i2.id = e.ideia_id WHERE i2.familia_id = i.familia_id AND i2.id <> i.id
          AND e.motivo LIKE 'REABERTA:%' AND e.ator = 'rotina' AND e.de IN ('candidata','pre_teste')) AS cota_rotina_usada
FROM ideias i
WHERE i.estado IN ('candidata','pre_teste') AND i.score IS NOT NULL AND i.familia_id IS NOT NULL   -- pre_teste: the sibling died while it waited
  AND EXISTS (SELECT 1 FROM ideias m WHERE m.familia_id = i.familia_id AND m.id < i.id
              AND (m.estado = 'morta' OR (m.estado = 'arquivada' AND m.arquivamento IS NOT 'operacional'))
              AND NOT EXISTS (SELECT 1 FROM ideia_eventos l WHERE l.ideia_id = m.id AND l.para = 'lancada'))
  AND NOT EXISTS (SELECT 1 FROM ideia_eventos e WHERE e.ideia_id = i.id AND e.ator = 'dono' AND e.motivo LIKE 'REABERTA:%'
                                -- mirrors trg_familia_cemiterio: an owner REABERTA since the last entry in candidata and after the sibling's death
                                AND e.id >= (SELECT MAX(id) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'candidata' AND de <> 'candidata')
                                AND e.id > COALESCE((SELECT MAX(d.id) FROM ideia_eventos d JOIN ideias m ON m.id = d.ideia_id
                                                     WHERE m.familia_id = i.familia_id AND m.id < i.id AND d.para = 'morta'), 0))
  -- a sibling the routine already reopened since its last entry is not blocked (trg_familia_cemiterio, light branch)
  AND NOT EXISTS (SELECT 1 FROM ideia_eventos e WHERE e.ideia_id = i.id AND e.ator = 'rotina' AND e.motivo LIKE 'REABERTA:%'
                  AND e.de IN ('candidata','pre_teste')
                  AND e.id >= (SELECT MAX(id) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'candidata' AND de <> 'candidata'));

-- name: q_tendencia_fechada_fila   (candidata/pre_teste idea whose reference's trend closed before it got a test: it can
--                                 never enter (janela_fechada) -> arquivada, arquivamento='operacional')
SELECT DISTINCT i.id, i.titulo FROM ideias i
JOIN ideia_concorrentes ic ON ic.ideia_id = i.id AND ic.papel = 'referencia'
JOIN v_tendencia_viva v ON v.concorrente_id = ic.concorrente_id   -- only a leader still < 120 days old blocks the entry
JOIN tendencias t ON t.loja = v.loja AND t.id_loja = v.id_loja AND t.status = 'fechada'
WHERE i.estado IN ('candidata','pre_teste')
  -- clones only (the hype's own platform); a port to another platform follows 4.4 (frozen until the guards stop)
  AND CASE WHEN v.loja IN ('poki','crazygames','web','itch') THEN 'web' WHEN v.loja IN ('appstore','play') THEN 'mobile'
           ELSE v.loja END = i.plataforma
  AND NOT EXISTS (SELECT 1 FROM experimentos x WHERE x.ideia_id = i.id AND x.estado IN ('planejado','rodando'));
