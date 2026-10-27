"""Review round 1 (16 findings): extension window from the 2nd channel, sibling hypotheses closed before a terminal
state, complete star data, category rate tied to a benchmark, sheet changes void the advocate, fail-closed niche,
demand thresholds, owner-only transitions as explicit pairs, queue and checklist fixes."""
import sqlite3, unittest
from lib import decidir
from test_schema import Base, FICHA
from test_queries import queries, db_sem_travas, linha


class LibR1(unittest.TestCase):
    def test_estendidaMedeANovaJanelaSemDobrarNMin(self):
        # the extended window starts at the 2nd channel and lasts the stage window again
        self.assertEqual(decidir('contagem', 12, 14, 10, 2, 14, 0, 1, passa_estendido=10), 'passa')


class GuardsR1(Base):
    def lancada_com_s1(self):
        i = self.nova(**FICHA); self.ate_lancada(i)
        h = self.c.execute("INSERT INTO hipoteses(ideia_id,etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,prazo_dias) "
                           "VALUES(?,'S1','e14','contagem',10,2,14,0,1,14)", (i,)).lastrowid
        return i, h

    def test_extensaoExigeSegundoCanal(self):
        i, h = self.lancada_com_s1()
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'extensao_sem_segundo_canal'):
            self.c.execute("UPDATE hipoteses SET estendida=1, passa_estendido=10, estendida_em=date('now') WHERE id=?", (h,))
        # round 2: the extension channel is new and posted after the first window ended
        self.c.execute("UPDATE lancamentos SET postado_em=datetime('now','-20 days') WHERE ideia_id=?", (i,))
        self.lancar(i, 'reddit')
        self.c.execute("UPDATE hipoteses SET estendida=1, passa_estendido=10, estendida_em=date('now') WHERE id=?", (h,))

    def test_naoArquivaComHipoteseAberta(self):
        i, h = self.lancada_com_s1()
        self.assertIn('hipoteses_abertas', self.mover(i, 'arquivada', reabrir_se='x'))
        self.c.execute("UPDATE hipoteses SET resultado='inconclusiva', fechada_em=datetime('now'), aprendizado='encerrada pelo arquivamento' WHERE id=?", (h,))
        self.assertIsNone(self.mover(i, 'arquivada', reabrir_se='x'))

    def test_decisaoSoComIdeiaEmMedicao(self):
        i, h = self.lancada_com_s1()
        self.c.execute("UPDATE hipoteses SET resultado='inconclusiva', fechada_em=datetime('now') WHERE id=?", (h,))
        self.mover(i, 'arquivada', reabrir_se='x')
        h2 = self.c.execute("INSERT INTO hipoteses(ideia_id,etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,prazo_dias) "
                            "VALUES(?,'S2','e30','contagem',100,29,30,0,1,30)", (i,)).lastrowid
        for d in range(30):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(?,date('now',?),0,'stargazers_history')", (i, f'-{d} days'))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'ideia_fora_de_medicao'):
            self.c.execute("UPDATE hipoteses SET resultado='refutada', fechada_em=datetime('now'), n_observado=30, valor_observado=0 WHERE id=?", (h2,))

    def test_decisaoExigeTodosOsDiasDaJanela(self):
        i, h = self.lancada_com_s1()
        self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(?,date('now'),1,'stargazers_history')", (i,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_sem_dado'):
            self.c.execute("UPDATE hipoteses SET resultado='refutada', fechada_em=datetime('now'), n_observado=14, valor_observado=1 WHERE id=?", (h,))

    def test_hitRateLigadoAUmBenchmark(self):
        b = self.c.execute("INSERT INTO benchmarks(metrica,segmento,valor,unidade,source_url,data_fonte,tipo_fonte,confianca,verificado_em) "
                           "VALUES('hit_rate_gt1000_cli_go_12m','topic_cli_go_r1',0.009,'fracao','https://api.github.com/search/repositories?q=topic:cli+language:go','2026-10-27','medicao_propria','alta',date('now'))").lastrowid
        i = self.nova(**dict(FICHA, hit_rate_categoria=0.0113, hit_rate_benchmark_id=b))
        self.assertIn('hit_rate_sem_benchmark', self.aprovar(i))
        self.c.execute('UPDATE ideias SET hit_rate_categoria=0.009 WHERE id=?', (i,))
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now') WHERE id=?", (i,))
        self.assertIsNone(self.aprovar(i))

    def test_mudarFichaDepoisDoAdvogadoAnulaOAdvogado(self):
        i = self.nova(**FICHA)
        self.c.execute("UPDATE ideias SET categoria='outro' WHERE id=?", (i,))
        self.assertIn('advogado_obrigatorio', self.aprovar(i))

    def test_nichoFalhaFechado(self):
        i = self.nova(**dict(FICHA, sem_repos=True))
        self.assertIn('sem_concorrente_verificado', self.aprovar(i))
        r = self.c.execute("INSERT INTO repos(full_name,criado_em) VALUES('a/suc',NULL)").lastrowid
        self.c.execute("INSERT INTO repo_snapshots(repo_id,data,estrelas,pushed_at,fonte) VALUES(?,date('now'),5000,NULL,'gh_star_count')", (r,))
        self.c.execute("INSERT INTO ideia_repos VALUES(?,?,'sucessor')", (i, r))
        self.assertIn('concorrente_incompleto', self.aprovar(i))

    def test_sinalFracoNaoQualifica(self):
        i = self.c.execute("INSERT INTO ideias(titulo) VALUES('t')").lastrowid
        self.c.execute('INSERT INTO evidencias(ideia_id,sinal_id,polaridade) VALUES(?,?,1)', (i, self.sinal(reacoes=3)))
        self.assertIn('sem_sinal_de_demanda', self.mover(i, 'candidata'))

    def test_reaberturaTambemExigeDemanda(self):
        i = self.c.execute("INSERT INTO ideias(titulo) VALUES('t')").lastrowid
        self.mover(i, 'arquivada', reabrir_se='x')
        self.assertIn('sem_sinal_de_demanda', self.mover(i, 'candidata', motivo='REABERTA: x'))

    def test_voltarDeProntaParaConstrucaoEhDaRotina(self):
        i = self.nova(**FICHA); self.aprovar(i); self.checklist_ok(i); self.mover(i, 'pronta')
        self.c.execute("UPDATE checklist SET ok=0, prova='release apagada' WHERE ideia_id=? AND item='release'", (i,))
        self.assertIsNone(self.mover(i, 'em_construcao'))


class QueriesR1(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def test_benchmarkDePaperNaoVence(self):
        self.c.execute("INSERT INTO benchmarks(metrica,segmento,valor,unidade,source_url,data_fonte,tipo_fonte,confianca,verificado_em) "
                       "VALUES('x','y',1,'u','s','2018','primaria','alta',date('now','-200 days'))")
        self.assertEqual(linha(self.c, 'q_checklist')['benchmarks_vencidos'], 0)

    def test_candidataComMesaCompletaNaoEhParada(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,atualizada_em,advogado_em) VALUES(1,'a','candidata',datetime('now','-20 days'),datetime('now'))")
        self.assertEqual(self.c.execute(queries()['q_candidatas_paradas']).fetchall(), [])

    def test_extensaoMedeDesdeOSegundoCanal(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','lancada')")
        self.c.execute("INSERT INTO lancamentos(ideia_id,canal,url,titulo,postado_em,prova_dono) VALUES(1,'show_hn','u1','t',datetime('now','-40 days'),'\"lancei\" x'),"
                       "(1,'reddit','u2','t',datetime('now','-14 days'),'\"lancei\" x')")
        for d in range(0, 41):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(1,date('now',?),1,'stargazers_history')", (f'-{d} days',))
        self.c.execute("INSERT INTO hipoteses(ideia_id,etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,prazo_dias,estendida,passa_estendido,estendida_em) "
                       "VALUES(1,'S1','e14','contagem',10,2,14,0,1,14,1,10,date('now','-14 days'))")
        r = linha(self.c, 'q_hipoteses_abertas')
        self.assertEqual((r['dias_cobertos'], r['eventos_janela']), (14, 14))

    def test_lancadaSemRepoProprioAcusa(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','lancada')")
        self.assertEqual(linha(self.c, 'q_checklist')['lancadas_sem_repo'], 1)

    def test_trafficSoCobradoComAFonteLigada(self):
        self.c.execute("INSERT INTO fontes(nome,plataforma,tipo,frequencia,status) VALUES('gh_traffic','github','metrica','diaria','desligada')")
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','lancada')")
        self.assertEqual(linha(self.c, 'q_checklist')['lancadas_sem_traffic_ontem'], 0)


if __name__ == '__main__':
    unittest.main()
