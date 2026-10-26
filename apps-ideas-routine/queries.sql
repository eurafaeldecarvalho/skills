-- Ready-made queries. Use these instead of writing new SQL for the frequent decisions.

-- name: q_portfolio_vagas
SELECT 4 - COALESCE(SUM(estado='pre_teste'),0)     AS vagas_pre_teste,
       2 - COALESCE(SUM(estado='em_teste'),0)      AS vagas_teste,
       1 - COALESCE(SUM(estado='em_construcao'),0) AS vagas_construcao,
       COALESCE(SUM(estado='lancada'),0)           AS lancadas
FROM ideias;

-- name: q_gasto_ideia   (:ideia_id)
SELECT COALESCE(SUM(valor_brl),0) AS gasto_brl FROM gastos WHERE ideia_id = :ideia_id AND categoria <> 'plataforma';

-- name: q_gasto_mes   (monthly test budget; platform costs have a separate budget)
SELECT COALESCE(SUM(valor_brl),0) AS gasto_mes_brl FROM gastos
WHERE strftime('%Y-%m', data) = strftime('%Y-%m', 'now') AND categoria <> 'plataforma';

-- name: q_fontes_distintas_por_ideia   (candidate rule; trustmrr and keyword_fraca never count)
SELECT e.ideia_id,
  COUNT(DISTINCT f.plataforma) AS plataformas,
  COUNT(DISTINCT CASE WHEN s.tipo IN ('dor','pedido','orfao','regulacao') THEN f.plataforma END) AS plataformas_de_dor,
  SUM(s.tipo IN ('preco','concorrente')) AS sinais_pagador,
  SUM(f.plataforma = 'dono_campo') AS sinais_dono_campo,
  COUNT(*) AS sinais
FROM evidencias e JOIN sinais s ON s.id = e.sinal_id JOIN fontes f ON f.id = s.fonte_id
WHERE e.polaridade = 1
  AND (s.url_status = 200 OR (s.url_status = 0 AND f.plataforma = 'dono_campo'))
  AND f.plataforma <> 'trustmrr' AND s.tipo NOT IN ('keyword_fraca','outro')
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
  SELECT concorrente_id, pais, data, 'ratings_count' AS medida, ratings_count AS v FROM concorrente_snapshots WHERE rank_lista = '' AND ratings_count IS NOT NULL
  UNION ALL SELECT concorrente_id, pais, data, 'users', users FROM concorrente_snapshots WHERE rank_lista = '' AND users IS NOT NULL
  UNION ALL SELECT concorrente_id, pais, data, 'installs_min', installs_min FROM concorrente_snapshots WHERE rank_lista = '' AND installs_min IS NOT NULL
)
SELECT a.concorrente_id, a.pais, a.medida, a.data AS data_atual, b.data AS data_base, a.v - b.v AS delta,
       ROUND((a.v - b.v) * 30.0 / (julianday(a.data) - julianday(b.data))) AS delta_30d
FROM s a JOIN s b ON b.concorrente_id = a.concorrente_id AND b.pais = a.pais AND b.medida = a.medida
WHERE a.data = (SELECT MAX(data) FROM s x WHERE x.concorrente_id = a.concorrente_id AND x.pais = a.pais AND x.medida = a.medida)
  AND b.data = (SELECT MIN(data) FROM s y WHERE y.concorrente_id = a.concorrente_id AND y.pais = a.pais AND y.medida = a.medida
                AND y.data >= date(a.data, '-30 days'))
  AND julianday(a.data) - julianday(b.data) >= 7;

-- name: q_hipoteses_abertas   (deadline counts from the milestone = experimentos.inicio; 'planejado' never expires)
SELECT h.*, x.estado AS exp_estado, x.inicio,
       CASE WHEN x.inicio IS NULL THEN 0
            ELSE date('now') > date(x.inicio, '+' || (h.prazo_dias * (1 + h.estendida)) || ' days') END AS prazo_esgotado
FROM hipoteses h JOIN experimentos x ON x.id = h.experimento_id
WHERE h.resultado IS NULL AND x.estado IN ('planejado','rodando');

-- name: q_metricas_experimento   (:experimento_id) — cumulative totals (each row is 1 day)
SELECT metrica, SUM(valor) AS total FROM metricas WHERE experimento_id = :experimento_id GROUP BY metrica;

-- name: q_installs_ultimos_7d   (:experimento_id) — for M1
SELECT COALESCE(SUM(valor),0) AS installs_7d FROM metricas
WHERE experimento_id = :experimento_id AND metrica = 'install' AND data > date('now','-8 days');

-- name: q_checklist   (every column must be 0)
SELECT
 (SELECT COUNT(DISTINCT c.id) FROM concorrentes c
   JOIN ideia_concorrentes ic ON ic.concorrente_id = c.id
   JOIN ideias i ON i.id = ic.ideia_id AND i.estado NOT IN ('morta','arquivada')
   WHERE NOT EXISTS (SELECT 1 FROM concorrente_snapshots cs WHERE cs.concorrente_id = c.id AND cs.rank_lista = ''
     AND cs.data >= CASE WHEN c.loja IN ('appstore','play','wordpress')
                          AND EXISTS (SELECT 1 FROM ideia_concorrentes ic2 JOIN ideias i2 ON i2.id = ic2.ideia_id
                                      WHERE ic2.concorrente_id = c.id AND i2.estado IN ('pre_teste','em_teste','validada','em_construcao','lancada'))
                         THEN date('now') ELSE date('now','-6 days') END)) AS concorrentes_sem_foto,
 (SELECT COUNT(*) FROM experimentos x WHERE x.estado = 'rodando' AND x.inicio < date('now')
   AND NOT EXISTS (SELECT 1 FROM metricas m WHERE m.experimento_id = x.id AND m.data = date('now','-1 day'))) AS experimentos_sem_metrica,
 (SELECT COUNT(*) FROM ideias WHERE estado = 'morta' AND motivo_morte IS NULL) AS mortas_sem_motivo,
 (SELECT COUNT(*) FROM ideias i WHERE i.reabrir_se IS NULL
   AND ( (i.estado = 'morta' AND i.motivo_morte IN ('sem_pagador','incumbente_gratis','concorrencia_saturada','sem_canal','mercado_pequeno','prazo'))
      OR i.estado = 'arquivada' )) AS mortas_sem_reabrir_se,
 (SELECT COUNT(*) FROM ideias WHERE estado NOT IN ('sinal','candidata') AND familia_id IS NULL) AS ideias_sem_familia,
 (SELECT COUNT(*) FROM (SELECT ideia_id FROM gastos WHERE ideia_id IS NOT NULL AND categoria <> 'plataforma'
   GROUP BY ideia_id HAVING SUM(valor_brl) > (SELECT CAST(valor AS REAL) FROM config WHERE chave='teto_gasto_ideia_brl'))) AS ideias_acima_teto,
 (SELECT CASE WHEN COALESCE(SUM(valor_brl),0) > (SELECT CAST(valor AS REAL) FROM config WHERE chave='teto_gasto_mes_brl') THEN 1 ELSE 0 END
   FROM gastos WHERE strftime('%Y-%m', data) = strftime('%Y-%m','now') AND categoria <> 'plataforma') AS mes_acima_teto,
 (SELECT COUNT(*) FROM benchmarks_vigentes WHERE usar_em_calculo = 1 AND date(verificado_em) < date('now','-90 days')) AS benchmarks_vencidos,
 (SELECT COUNT(*) FROM sinais s JOIN evidencias e ON e.sinal_id = s.id JOIN fontes f ON f.id = s.fonte_id
   WHERE NOT (s.url_status = 200 OR (s.url_status = 0 AND f.plataforma = 'dono_campo'))) AS evidencias_sem_url_ok,
 (SELECT COUNT(*) FROM ideias WHERE estado = 'candidata' AND score IS NULL
   AND atualizada_em < datetime('now', '-' || (SELECT valor FROM config WHERE chave='candidata_pendente_dias') || ' days')) AS candidatas_paradas;

-- name: q_lancamentos_vs_meta   (goal: >= 3 launches by month 4–5)
SELECT COUNT(DISTINCT ideia_id) AS lancamentos FROM ideia_eventos WHERE para = 'lancada';

-- name: q_runs_trava   (suggest an adjustment if > 3 in the last 7)
SELECT SUM(motivo_parada IN ('teto_tempo','teto_buscas')) AS paradas_por_trava
FROM (SELECT motivo_parada FROM runs WHERE tipo = 'diaria' ORDER BY id DESC LIMIT 7);

-- name: q_erro_previsao   (calibration)
SELECT etapa, metrica, COUNT(*) AS n, AVG(valor_observado - previsao) AS erro_medio
FROM hipoteses WHERE resultado IN ('confirmada','refutada') AND valor_observado IS NOT NULL
GROUP BY etapa, metrica;

-- name: q_reabrir_candidatas   (evaluate reabrir_se; 1st Sunday of the month or when an orfao/plataforma/regulacao signal cites the competitor)
SELECT i.id, i.titulo, i.estado, i.motivo_morte, i.reabrir_se, i.familia_id
FROM ideias i
WHERE i.estado IN ('morta','arquivada') AND i.reabrir_se IS NOT NULL
  AND (i.motivo_morte IS NULL OR i.motivo_morte NOT IN ('teste_reprovado','advogado_do_diabo','risco_banimento','excluida_por_regra'))
  AND NOT EXISTS (SELECT 1 FROM ideia_eventos ev WHERE ev.ideia_id = i.id AND ev.motivo LIKE 'REABERTA:%' AND ev.ator = 'rotina'
                  AND ev.de IN ('morta','arquivada'));

-- name: q_exploracao_mes   (quota: 1 per month, 1 active)
SELECT
 (SELECT COUNT(*) FROM ideias WHERE exploracao = 1 AND estado IN ('candidata','pre_teste','em_teste','validada','em_construcao')) AS ativas,
 (SELECT COUNT(*) FROM ideias WHERE exploracao = 1 AND strftime('%Y-%m', exploracao_em) = strftime('%Y-%m','now')) AS no_mes;

-- name: q_familia_sugerida   (:ideia_id) — inherit the family of the row with most columns = 1 (minimum 2); tie -> lowest familia_id
SELECT o.id, o.familia_id, o.estado, o.motivo_morte,
 COALESCE(o.pagador = n.pagador, 0) AS mesmo_pagador,
 (SELECT COUNT(*) FROM ideia_concorrentes a JOIN ideia_concorrentes b ON b.concorrente_id = a.concorrente_id
   WHERE a.ideia_id = n.id AND b.ideia_id = o.id) >= 1 AS concorrente_comum,
 COALESCE(1.0 * (SELECT COUNT(*) FROM evidencias a JOIN evidencias b ON b.sinal_id = a.sinal_id WHERE a.ideia_id = n.id AND b.ideia_id = o.id)
   / NULLIF(MIN((SELECT COUNT(*) FROM evidencias WHERE ideia_id = n.id), (SELECT COUNT(*) FROM evidencias WHERE ideia_id = o.id)), 0) >= 0.5, 0) AS metade_sinais
FROM ideias o, ideias n WHERE n.id = :ideia_id AND o.id <> n.id AND o.familia_id IS NOT NULL;

-- name: q_orcamento_experimentos   (alert at 80%)
SELECT x.id AS experimento_id, x.ideia_id, MAX(h.orcamento_max_brl) AS orcamento,
       COALESCE((SELECT SUM(valor_brl) FROM gastos g WHERE g.experimento_id = x.id), 0) AS gasto,
       COALESCE((SELECT SUM(valor_brl) FROM gastos g WHERE g.experimento_id = x.id), 0) >= 0.8 * MAX(h.orcamento_max_brl) AS alerta_80
FROM experimentos x JOIN hipoteses h ON h.experimento_id = x.id
WHERE x.estado = 'rodando' AND h.orcamento_max_brl > 0 GROUP BY x.id;

-- name: q_etapa_status   (:experimento_id) — stage passes if ALL hypotheses passed; dies if ANY was refuted
SELECT COALESCE(SUM(resultado = 'confirmada'),0) AS confirmadas, COALESCE(SUM(resultado = 'refutada'),0) AS refutadas,
       COALESCE(SUM(resultado IS NULL),0) AS abertas, COALESCE(SUM(resultado LIKE 'inconclusiva%'),0) AS inconclusivas, COUNT(*) AS total
FROM hipoteses WHERE experimento_id = :experimento_id;

-- name: q_planejados_vencidos   (experiment stuck in 'planejado' beyond the stage limit -> idea archived; L1/E4 excluded)
SELECT x.id AS experimento_id, x.ideia_id, x.etapa, MIN(h.criada_em) AS criada_em
FROM experimentos x LEFT JOIN hipoteses h ON h.experimento_id = x.id
WHERE x.estado = 'planejado' AND x.etapa NOT IN ('L1','E4')
GROUP BY x.id
HAVING COALESCE(MIN(h.criada_em), (SELECT atualizada_em FROM ideias WHERE id = x.ideia_id)) < datetime('now', '-' || (SELECT valor FROM config WHERE chave =
   CASE x.etapa WHEN 'M1' THEN 'planejado_max_dias_m1' WHEN 'WSEO' THEN 'planejado_max_dias_wseo' ELSE 'planejado_max_dias' END) || ' days');

-- name: q_experimentos_a_fechar   (all hypotheses decided, experiment still open)
SELECT x.id AS experimento_id, x.ideia_id, x.etapa, x.estado
FROM experimentos x
WHERE x.estado IN ('planejado','rodando')
  AND NOT EXISTS (SELECT 1 FROM hipoteses h WHERE h.experimento_id = x.id AND h.resultado IS NULL)
  AND EXISTS (SELECT 1 FROM hipoteses h WHERE h.experimento_id = x.id);

-- name: q_fix_first_familia   (:familia_id) — FIX-FIRST allowed once per family
SELECT COUNT(*) AS usados FROM ideia_eventos e JOIN ideias i ON i.id = e.ideia_id
WHERE i.familia_id = :familia_id AND e.motivo LIKE 'FIX-FIRST:%';

-- name: q_experimentos_orfaos   (open experiment whose idea already left the stage state -> close without applying a destination)
SELECT x.id AS experimento_id, x.ideia_id, x.etapa, i.estado
FROM experimentos x JOIN ideias i ON i.id = x.ideia_id
WHERE x.estado IN ('planejado','rodando')
  AND NOT ( (x.etapa IN ('E1','WSEO') AND i.estado = 'pre_teste')
         OR (x.etapa IN ('E2E3','E3','M1') AND i.estado = 'em_teste')
         OR (x.etapa IN ('L1','E4') AND i.estado IN ('em_construcao','lancada')) );

-- name: q_pre_teste_parado   (pre_teste without an open experiment for longer than the limit -> archive with reabrir_se)
SELECT i.id, i.trilha, MAX(x.fim) AS ultimo_fim
FROM ideias i LEFT JOIN experimentos x ON x.ideia_id = i.id
WHERE i.estado = 'pre_teste'
  AND NOT EXISTS (SELECT 1 FROM experimentos y WHERE y.ideia_id = i.id AND y.estado IN ('planejado','rodando'))
  AND ( (i.trilha = 'L' AND NOT EXISTS (SELECT 1 FROM ideias c WHERE c.estado = 'em_construcao'))
     OR (i.trilha = 'W' AND i.universo IS NULL)
     OR (i.trilha = 'WSEO' AND (i.universo IS NULL OR i.volume_status = 'nao_medido')) )
GROUP BY i.id
HAVING MAX(COALESCE(MAX(x.fim), '0'), MAX(i.atualizada_em),
           CASE WHEN i.trilha = 'L' THEN COALESCE((SELECT MAX(em) FROM ideia_eventos WHERE de = 'em_construcao'), '0') ELSE '0' END)
       < date('now', '-' || (SELECT valor FROM config WHERE chave =
   CASE WHEN i.trilha = 'L' THEN 'pre_teste_l_espera_dias' ELSE 'pre_teste_dado_espera_dias' END) || ' days');

-- name: q_congeladas_vencidas   (seasonal with data_reativacao reached -> candidata; other frozen ideas older than congelada_max_meses -> archived)
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
            AND NOT (data_reativacao IS NOT NULL AND veio_de IN ('candidata','pre_teste','em_teste') AND reativacoes = 0) THEN 'arquivar'
  END AS acao
FROM ult WHERE acao IS NOT NULL;

-- name: q_l_aguardando_dono   (L ideas in pre_teste without an open experiment; with >= max_l_aguardando_dono, no L candidate enters pre_teste)
SELECT COUNT(*) AS aguardando FROM ideias i
WHERE i.estado = 'pre_teste' AND i.trilha = 'L'
  AND NOT EXISTS (SELECT 1 FROM experimentos x WHERE x.ideia_id = i.id AND x.estado IN ('planejado','rodando'));

-- name: q_janela_7d   (:experimento_id, :metrica, :fim) — 7-day sum ending at :fim (WSEO: fim = today − search_console_releitura_dias)
SELECT COALESCE(SUM(valor),0) AS total_7d FROM metricas
WHERE experimento_id = :experimento_id AND metrica = :metrica AND data > date(:fim, '-7 days') AND data <= :fim;

-- name: q_validada_parada   (validada with the build slot free and no owner decision for longer than validada_max_dias -> archive)
SELECT i.id FROM ideias i
WHERE i.estado = 'validada'
  AND NOT EXISTS (SELECT 1 FROM ideias c WHERE c.estado = 'em_construcao')
  AND MAX((SELECT MAX(em) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'validada'),
          COALESCE((SELECT MAX(em) FROM ideia_eventos WHERE de = 'em_construcao'), '0'))
      < datetime('now', '-' || (SELECT valor FROM config WHERE chave='validada_max_dias') || ' days');

-- name: q_construcao_longa   (em_construcao with hours above mvp_horas_max or older than 8 weeks -> pending item for the owner)
SELECT i.id,
  (SELECT COALESCE(SUM(horas),0) FROM horas WHERE ideia_id = i.id AND tipo = 'construcao') AS horas_construcao,
  (SELECT MAX(em) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'em_construcao') AS desde
FROM ideias i WHERE i.estado = 'em_construcao'
  AND ( (SELECT COALESCE(SUM(horas),0) FROM horas WHERE ideia_id = i.id AND tipo = 'construcao') > (SELECT CAST(valor AS REAL) FROM config WHERE chave='mvp_horas_max')
     OR (SELECT MAX(em) FROM ideia_eventos WHERE ideia_id = i.id AND para = 'em_construcao') < datetime('now','-56 days') );
