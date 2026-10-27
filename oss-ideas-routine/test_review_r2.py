"""Review round 2: launch cycles (a relaunch is measured from its own launch, re-proves the checklist and counts its own
channels), a real second chance on extension, a buildable queue and a destination for desk failures, a load ceiling,
fail-closed pre-registration, suspect star days, AI-hook and one-off guards, hits counted from effective states."""
import sqlite3, unittest
from lib import prova_existe
from test_schema import Base, FICHA
from test_queries import queries, db_sem_travas, linha, candidata


def hip(c, i, etapa='S1'):
    v = {'S1': ('e14', 10, 2, 14, 14), 'S2': ('e30', 100, 29, 30, 30), 'S3': ('e90', 1000, 299, 90, 90)}[etapa]
    return c.execute("INSERT INTO hipoteses(ideia_id,etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,prazo_dias) "
                     "VALUES(?,?,?,'contagem',?,?,?,0,1,?)", (i, etapa) + v).lastrowid


class CicloR2(Base):
    def lancamento(self, i, canal, dias):
        self.c.execute("INSERT INTO lancamentos(ideia_id,canal,url,titulo,postado_em,prova_dono) VALUES(?,?,?,'t',datetime('now',?),?)",
                       (i, canal, f'u{i}{canal}{dias}', f'-{dias} days', f'"lancei a ideia#{i} no {canal}" chat'))

    def test_relancamentoMedeDoNovoLancamentoERefazOChecklist(self):
        i = self.nova(**FICHA); self.aprovar(i); self.checklist_ok(i); self.mover(i, 'pronta')
        self.c.execute("UPDATE checklist SET verificado_em=datetime('now','-61 days') WHERE ideia_id=?", (i,))   # proved in the old cycle
        self.lancamento(i, 'show_hn', 60)
        self.mover(i, 'lancada', 'dono', f'"lancei a ideia#{i} no show_hn" chat')
        h = hip(self.c, i)
        self.c.execute("UPDATE hipoteses SET resultado='inconclusiva', fechada_em=datetime('now') WHERE id=?", (h,))
        self.mover(i, 'arquivada', reabrir_se='relançamento')
        self.assertIsNone(self.mover(i, 'candidata', motivo='REABERTA: relançamento [sinal#1]'))
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now') WHERE id=?", (i,))
        self.assertIsNone(self.aprovar(i))
        self.assertIn('checklist_incompleto', self.mover(i, 'pronta'))   # the old proofs are from the previous cycle
        self.checklist_ok(i); self.assertIsNone(self.mover(i, 'pronta'))
        self.lancamento(i, 'reddit', 0)
        self.assertIsNone(self.mover(i, 'lancada', 'dono', f'"lancei a ideia#{i} no reddit" chat'))
        hip(self.c, i)
        cur = self.c.execute(queries()['q_hipoteses_abertas']); cols = [d[0] for d in cur.description]
        r = dict(zip(cols, cur.fetchone()))
        self.assertEqual((r['dias_cobertos'], r['prazo_esgotado']), (0, 0))
        # two channels across two cycles are not two channels of this launch
        self.c.execute("UPDATE hipoteses SET resultado='inconclusiva', fechada_em=datetime('now') WHERE resultado IS NULL")
        self.assertIn('matar_exige_dois_canais', self.mover(i, 'morta', motivo_morte='teste_reprovado'))

    def test_extensaoExigeCanalNovoDepoisDaJanela(self):
        i = self.nova(**FICHA); self.aprovar(i); self.checklist_ok(i); self.mover(i, 'pronta')
        self.lancamento(i, 'show_hn', 40); self.lancamento(i, 'reddit', 39)
        self.mover(i, 'lancada', 'dono', f'"lancei a ideia#{i} no show_hn" chat')
        h = hip(self.c, i, 'S2')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'extensao_sem_segundo_canal'):
            self.c.execute("UPDATE hipoteses SET estendida=1, passa_estendido=100, estendida_em=date('now','-39 days') WHERE id=?", (h,))
        self.lancamento(i, 'lobsters', 0)
        self.c.execute("UPDATE hipoteses SET estendida=1, passa_estendido=100, estendida_em=date('now') WHERE id=?", (h,))


class GuardsR2(Base):
    def test_cargaComModoBaixaManutencaoTemTeto(self):
        i = self.nova(**dict(FICHA, carga_h_semana=7, modo_baixa_manutencao=1))
        self.assertIn('carga_acima_do_teto', self.aprovar(i))

    def test_preRegistroComMetricaDesconhecidaRecusado(self):
        i = self.nova(**FICHA); self.ate_lancada(i)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'pre_registro_diverge_do_limiar'):
            self.c.execute("INSERT INTO hipoteses(ideia_id,etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,prazo_dias) "
                           "VALUES(?,'S2','E30','contagem',5,1,30,0,1,30)", (i,))

    def test_diaSuspeitoBloqueiaConfirmacao(self):
        i = self.nova(**FICHA); self.ate_lancada(i)
        h = hip(self.c, i)
        for d in range(14):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte,suspeito) VALUES(?,date('now',?),?,'stargazers_history',?)",
                           (i, f'+{d} days', 200 if d == 3 else 0, 1 if d == 3 else 0))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'estrelas_suspeitas'):
            self.c.execute("UPDATE hipoteses SET resultado='confirmada', fechada_em=datetime('now'), n_observado=14, valor_observado=200 WHERE id=?", (h,))

    def test_ganchoQueVendeIaRecusado(self):
        i = self.nova(**dict(FICHA, gancho='AI agent that renames your files'))
        self.assertIn('gancho_vende_ia', self.aprovar(i))

    def test_oneOffDeUmaTardeRecusado(self):
        i = self.nova(**dict(FICHA, horas_estimadas=4))
        self.assertIn('one_off', self.aprovar(i))


class QueriesR2(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def test_filaSoComIdeiasConstruiveis(self):
        # round 4: complete desks; 'fraca' sits below the seeded floor (0.0015)
        candidata(self.c, 1, hit_rate_categoria=0.001, horas_estimadas=10)
        candidata(self.c, 2, categoria='lib_benchmark', hit_rate_categoria=None, horas_estimadas=10)
        candidata(self.c, 3, horas_estimadas=10); self.c.execute("UPDATE ideias SET advogado_em=NULL WHERE id=3")
        candidata(self.c, 4, horas_estimadas=12)
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_fila_construcao'])], [4, 2])
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_mesa_reprovada'])], [1])

    def test_repoDeIdeiaMortaNaoCobraSnapshot(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','morta')")
        self.c.execute("INSERT INTO repos(id,full_name,proprio_ideia_id) VALUES(1,'me/a',1)")
        self.assertEqual(linha(self.c, 'q_checklist')['repos_sem_snapshot_7d'], 0)

    def test_hitOrfaoNaoContaNaMeta(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','tracao')")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(1,'tracao','hit','x','rotina')")   # refused transition
        self.assertEqual(linha(self.c, 'q_meta')['hits_12m'], 0)


class LibR2(unittest.TestCase):
    def test_fraseDeLancamentoPeloPrefixo(self):
        self.assertTrue(prova_existe('"lancei a ideia#3 no show_hn https://news.ycombinator.com/item?id=1" chat 2026-10-27 12:00',
                                     ['lancei a ideia#3 no show_hn https://news.ycombinator.com/item?id=1'], 3, 'lancei a ideia#3'))


if __name__ == '__main__':
    unittest.main()
