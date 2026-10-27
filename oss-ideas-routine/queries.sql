-- Named queries of the open-source ideas routine. Parameters: :ideia_id. Every number they return is quoted with a
-- [metrica q_<name> AAAA-MM-DD] mark (SKILL.md section 2, principle 3).

-- name: q_checklist   (every column must be 0 before checklist_ok=1; section 11.2)
SELECT
 (SELECT COUNT(*) FROM ideias i WHERE i.estado <> 'sinal'
   AND NOT EXISTS (SELECT 1 FROM ideia_eventos e WHERE e.ideia_id = i.id)) AS ideias_sem_evento,
 -- own launched repos need yesterday's stars (stargazers/history) and traffic (it keeps only 14 days)
 (SELECT COUNT(*) FROM ideias i WHERE i.estado IN ('lancada','tracao','hit')
   AND NOT EXISTS (SELECT 1 FROM estrelas_diarias s WHERE s.ideia_id = i.id AND s.data >= date('now','-1 day'))) AS lancadas_sem_estrelas_ontem,
 -- traffic needs a token with push access; while the source is not 'ok' the column is not required
 (SELECT COUNT(*) FROM ideias i WHERE i.estado IN ('lancada','tracao','hit')
   AND EXISTS (SELECT 1 FROM fontes f WHERE f.nome = 'gh_traffic' AND f.status = 'ok')
   AND NOT EXISTS (SELECT 1 FROM traffic t WHERE t.ideia_id = i.id AND t.data >= date('now','-1 day'))) AS lancadas_sem_traffic_ontem,
 (SELECT COUNT(*) FROM ideias i WHERE i.estado IN ('pronta','lancada','tracao','hit')
   AND NOT EXISTS (SELECT 1 FROM repos r WHERE r.proprio_ideia_id = i.id)) AS lancadas_sem_repo,
 -- measured ideas need S1, S2 and S3 pre-registered in the current cycle (8.1)
 (SELECT COUNT(*) FROM ideias i WHERE i.estado IN ('lancada','tracao','hit')
   AND (SELECT COUNT(DISTINCT h.etapa) FROM hipoteses h WHERE h.ideia_id = i.id AND h.ciclo = i.ciclo) < 3) AS lancadas_sem_hipotese,
 -- open hypotheses past their deadline (window x (1 + extended) + reading grace) must be decided today
 -- an undecided window must be decided; an 'estender' waits segundo_canal_max_dias for the owner's 2nd channel
 (SELECT COUNT(*) FROM hipoteses h WHERE h.resultado IS NULL
   AND date('now') > date(COALESCE(h.estendida_em, (SELECT date(MIN(postado_em)) FROM lancamentos l WHERE l.ideia_id = h.ideia_id AND l.ciclo = h.ciclo)),
        '+' || (h.prazo_dias
                + COALESCE((SELECT CAST(valor AS INTEGER) FROM config WHERE chave='leitura_carencia_dias'),0)
                + CASE WHEN h.estendida = 0 THEN COALESCE((SELECT CAST(valor AS INTEGER) FROM config WHERE chave='segundo_canal_max_dias'),0) ELSE 0 END)
        || ' days')) AS hipoteses_vencidas,
 -- watched repos: own repos and competitors of ideas still alive (not morta/arquivada)
 (SELECT COUNT(*) FROM repos r
   WHERE (EXISTS (SELECT 1 FROM ideias i WHERE i.id = r.proprio_ideia_id AND i.estado IN ('em_construcao','pronta','lancada','tracao','hit'))
       OR EXISTS (SELECT 1 FROM ideia_repos ir JOIN ideias i ON i.id = ir.ideia_id
          WHERE ir.repo_id = r.id AND i.estado IN ('candidata','em_construcao','pronta','lancada','tracao','hit')))
   AND NOT EXISTS (SELECT 1 FROM repo_snapshots s WHERE s.repo_id = r.id AND s.data >= date('now','-7 days'))) AS repos_sem_snapshot_7d,
 -- only the routine's re-measurable counts expire (section 12: Search API counts, Show HN shares, category rates);
 -- samples, fixed windows, papers and case posts do not
 (SELECT COUNT(*) FROM benchmarks_vigentes WHERE tipo_fonte = 'medicao_propria'
   AND (metrica LIKE 'hit_rate_%' OR metrica LIKE 'repos_%' OR metrica LIKE 'p_ge%' OR metrica LIKE 'showhn_github_pct_%')
   AND verificado_em < date('now','-' || (SELECT valor FROM config WHERE chave='benchmarks_reverificar_dias') || ' days')) AS benchmarks_vencidos;

-- name: q_janela   (:ideia_id) — organic stars in the windows after the FIRST launch channel (E7, E14, E30, E90)
WITH l AS (SELECT MIN(postado_em) AS ini, COUNT(DISTINCT canal) AS canais FROM lancamentos
           WHERE ideia_id = :ideia_id AND ciclo = (SELECT ciclo FROM ideias WHERE id = :ideia_id))
SELECT l.ini AS primeiro_lancamento, l.canais,
  CAST(julianday(date('now')) - julianday(date(l.ini)) AS INTEGER) AS dias_desde_lancamento,
  (SELECT COALESCE(SUM(estrelas),0) FROM estrelas_diarias WHERE ideia_id = :ideia_id AND suspeito = 0 AND data >= date(l.ini) AND data < date(l.ini,'+7 days')) AS e7,
  (SELECT COALESCE(SUM(estrelas),0) FROM estrelas_diarias WHERE ideia_id = :ideia_id AND suspeito = 0 AND data >= date(l.ini) AND data < date(l.ini,'+14 days')) AS e14,
  (SELECT COALESCE(SUM(estrelas),0) FROM estrelas_diarias WHERE ideia_id = :ideia_id AND suspeito = 0 AND data >= date(l.ini) AND data < date(l.ini,'+30 days')) AS e30,
  (SELECT COALESCE(SUM(estrelas),0) FROM estrelas_diarias WHERE ideia_id = :ideia_id AND suspeito = 0 AND data >= date(l.ini) AND data < date(l.ini,'+90 days')) AS e90
FROM l WHERE l.ini IS NOT NULL;

-- name: q_hipoteses_abertas   (the window starts at the first launch, or at the 2nd channel once extended (estendida_em);
--                            n = days covered, capped at the window; baseline_janela = the pace of the 28 days before the
--                            cycle's first launch, scaled to the window (0 for a repo private until launch);
--                            eventos = the window's stars net of that baseline; deadline = window + grace)
WITH b AS (
  SELECT h.*, COALESCE(h.estendida_em, (SELECT date(MIN(postado_em)) FROM lancamentos l WHERE l.ideia_id = h.ideia_id AND l.ciclo = h.ciclo)) AS inicio_janela,
    (SELECT date(MIN(postado_em)) FROM lancamentos l WHERE l.ideia_id = h.ideia_id AND l.ciclo = h.ciclo) AS primeiro_lancamento
  FROM hipoteses h WHERE h.resultado IS NULL),
c AS (
  SELECT b.*,
    CAST(ROUND((SELECT COALESCE(SUM(s.estrelas),0) FROM estrelas_diarias s WHERE s.ideia_id = b.ideia_id AND s.suspeito = 0
       AND s.data >= date(b.primeiro_lancamento,'-28 days') AND s.data < b.primeiro_lancamento) * b.prazo_dias / 28.0) AS INTEGER) AS baseline_janela,
    (SELECT COALESCE(SUM(s.estrelas),0) FROM estrelas_diarias s WHERE s.ideia_id = b.ideia_id AND s.suspeito = 0
       AND s.data >= b.inicio_janela AND s.data < date(b.inicio_janela, '+' || b.prazo_dias || ' days')) AS estrelas_janela
  FROM b WHERE b.inicio_janela IS NOT NULL)
SELECT c.*,
  MIN(CAST(julianday(date('now')) - julianday(c.inicio_janela) AS INTEGER), c.prazo_dias) AS dias_cobertos,
  MAX(c.estrelas_janela - c.baseline_janela, 0) AS eventos_janela,
  date('now') > date(c.inicio_janela, '+' || (c.prazo_dias
       + COALESCE((SELECT CAST(valor AS INTEGER) FROM config WHERE chave='leitura_carencia_dias'),0)) || ' days') AS prazo_esgotado
FROM c;

-- name: q_fila_construcao   (finished desks that pass every build cut of the database (mesa_cortes.corte IS NULL);
--                          ordered by (category rate / floor; the exempt categories count 1) x demand as a multiple of
--                          its type's threshold (👍, points and abandoned-repo stars are different units), then fewer hours)
SELECT i.id, i.titulo, i.categoria, i.hit_rate_categoria, i.horas_estimadas,
  (SELECT COALESCE(MAX(1.0 * s.reacoes / (SELECT CAST(valor AS REAL) FROM config WHERE chave = CASE s.tipo
        WHEN 'repo_abandonado' THEN 'demanda_estrelas_abandonado_min' WHEN 'pedido_ferramenta' THEN 'demanda_pontos_min'
        ELSE 'demanda_reacoes_min' END)),0)
   FROM evidencias e JOIN sinais s ON s.id = e.sinal_id
   WHERE e.ideia_id = i.id AND e.polaridade = 1 AND s.tipo IN ('issue_reacoes','issue_not_planned','pedido_ferramenta','repo_abandonado')) AS demanda_x_limiar
FROM ideias i JOIN mesa_cortes m ON m.id = i.id AND m.corte IS NULL
ORDER BY (CASE WHEN i.categoria IN ('lib_benchmark','sucessor_abandonado','alternativa_open') THEN 1.0
              ELSE i.hit_rate_categoria / (SELECT CAST(valor AS REAL) FROM config WHERE chave='categoria_hit_min') END)
         * MAX(demanda_x_limiar, 1) DESC,
         demanda_x_limiar DESC, COALESCE(i.horas_estimadas,999) ASC, i.id ASC;

-- name: q_mesa_reprovada   (finished desks the database would refuse; corte = the failed cut -> its destination
--                         (SKILL.md 3.2 step 4): categoria_proibida -> morta; nicho_tomado -> morta; the rest -> arquivada
--                         with reabrir_se = corte)
SELECT i.id, i.titulo, i.categoria, i.hit_rate_categoria, i.carga_h_semana, m.corte
FROM ideias i JOIN mesa_cortes m ON m.id = i.id AND m.corte IS NOT NULL
ORDER BY i.id;

-- name: q_sinais_parados   (idea in 'sinal' beyond sinal_max_dias without a demand signal -> arquivada)
SELECT id, titulo, criada_em FROM ideias
WHERE estado = 'sinal' AND criada_em < datetime('now','-' || (SELECT valor FROM config WHERE chave='sinal_max_dias') || ' days');

-- name: q_candidatas_paradas   (candidata whose desk is still unfinished (no advocate) beyond candidata_pendente_dias ->
--                             desk today or arquivada; a finished desk waiting for the build slot is not stuck)
SELECT id, titulo, atualizada_em FROM ideias
WHERE estado = 'candidata' AND advogado_em IS NULL
  AND atualizada_em < datetime('now','-' || (SELECT valor FROM config WHERE chave='candidata_pendente_dias') || ' days');

-- name: q_construcao_longa   (build beyond construcao_max_dias or 1.5x the estimated hours -> pending item to the owner)
SELECT i.id, i.titulo, i.horas_estimadas,
  (SELECT COALESCE(SUM(horas),0) FROM horas h WHERE h.ideia_id = i.id AND h.tipo = 'construcao') AS horas_construcao
FROM ideias i WHERE i.estado = 'em_construcao'
  AND ( i.atualizada_em < datetime('now','-' || (SELECT valor FROM config WHERE chave='construcao_max_dias') || ' days')
     OR (SELECT COALESCE(SUM(horas),0) FROM horas h WHERE h.ideia_id = i.id AND h.tipo = 'construcao') > 1.5 * i.horas_estimadas );

-- name: q_pronta_parada   (ready but not launched beyond pronta_max_dias -> pending item: launch window or archive)
SELECT id, titulo, atualizada_em FROM ideias
WHERE estado = 'pronta' AND atualizada_em < datetime('now','-' || (SELECT valor FROM config WHERE chave='pronta_max_dias') || ' days');

-- name: q_m1_saude   (own repo health after launch: open issues per 1k stars; needs >= 1,000 stars to judge)
SELECT i.id, CASE WHEN 1000.0 * s.issues_abertas / s.estrelas > (SELECT CAST(valor AS REAL) FROM config WHERE chave='m1_issues_por_1k_pausa') THEN 'pausa'
                  ELSE 'baixa_manutencao' END AS acao,
  ROUND(1000.0 * s.issues_abertas / s.estrelas, 1) AS issues_por_1k
FROM ideias i JOIN repos r ON r.proprio_ideia_id = i.id
JOIN repo_snapshots s ON s.repo_id = r.id AND s.data = (SELECT MAX(data) FROM repo_snapshots WHERE repo_id = r.id)
WHERE i.estado IN ('lancada','tracao','hit') AND s.estrelas >= 1000
  AND 1000.0 * s.issues_abertas / s.estrelas > (SELECT CAST(valor AS REAL) FROM config WHERE chave='m1_issues_por_1k_max');

-- name: q_m2_congelado   (own launched repo without a push for m2_dias_sem_push -> a release or archive the repo)
SELECT i.id, s.pushed_at FROM ideias i JOIN repos r ON r.proprio_ideia_id = i.id
JOIN repo_snapshots s ON s.repo_id = r.id AND s.data = (SELECT MAX(data) FROM repo_snapshots WHERE repo_id = r.id)
WHERE i.estado IN ('lancada','tracao','hit')
  AND s.pushed_at < date('now','-' || (SELECT valor FROM config WHERE chave='m2_dias_sem_push') || ' days');

-- name: q_conversao   (:ideia_id) — visit-to-star conversion over the last 14 days (diagnostic only; section 9.2)
SELECT (SELECT COALESCE(SUM(estrelas),0) FROM estrelas_diarias WHERE ideia_id = :ideia_id AND suspeito = 0 AND data > date('now','-14 days')) AS estrelas_14d,
       (SELECT COALESCE(SUM(uniques),0) FROM traffic WHERE ideia_id = :ideia_id AND data > date('now','-14 days')) AS visitantes_14d,
       1.0 * (SELECT COALESCE(SUM(estrelas),0) FROM estrelas_diarias WHERE ideia_id = :ideia_id AND suspeito = 0 AND data > date('now','-14 days'))
           / NULLIF((SELECT SUM(uniques) FROM traffic WHERE ideia_id = :ideia_id AND data > date('now','-14 days')),0) AS conversao;

-- name: q_meta   (portfolio goal of section 1: organic stars and hits in the last 12 months)
SELECT (SELECT COALESCE(SUM(estrelas),0) FROM estrelas_diarias WHERE suspeito = 0 AND data > date('now','-365 days')) AS estrelas_12m,
       -- a hit is a confirmed S3 (an event alone can be the orphan of a refused transition)
       (SELECT COUNT(DISTINCT ideia_id) FROM hipoteses WHERE etapa = 'S3' AND resultado = 'confirmada'
         AND fechada_em > datetime('now','-365 days')) AS hits_12m,
       (SELECT COUNT(DISTINCT ideia_id) FROM lancamentos WHERE postado_em > datetime('now','-365 days')) AS lancamentos_12m;
