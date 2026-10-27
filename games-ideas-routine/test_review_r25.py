"""Review round 25 (queue queries anchored on the current cycle, closed-trend queue only for clones, build override
checks loop_idle)."""
import sqlite3, unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


class QueriesR25(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()
        self.c.execute("INSERT INTO config VALUES('candidata_pendente_dias','14','seed',datetime('now')),('candidata_fila_dias','60','seed',datetime('now'))")

    def antiga_reabertura(self, ator):
        # an old REABERTA, then a later re-entry in candidata: the old one no longer covers the family entry
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono,em) VALUES(2,'arquivada','candidata','REABERTA: x',?,?,datetime('now','-200 days'))",
                       (ator, '"reabro a ideia#2" chat' if ator == 'dono' else None))
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,em) VALUES(2,'arquivada','candidata','reativada','rotina',datetime('now','-100 days'))")

    def test_reaberturaAntigaNaoEscondeIrmaBloqueada(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,motivo_morte,familia_id) VALUES(1,'a','morta','teste_reprovado',1)")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,familia_id,trilha,atualizada_em) VALUES(2,'b','candidata',28,1,'W',datetime('now','-70 days'))")
        self.antiga_reabertura('dono')
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_irmas_bloqueadas'])], [2])
        self.assertEqual([(r[0], r[-1]) for r in self.c.execute(queries()['q_candidatas_paradas'])], [(2, 'bloqueada_cemiterio')])

    def test_portDeHypeComTendenciaFechadaNaoSaiDaFila(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,fonte_ideia,plataforma) VALUES(1,'port','candidata','arbitragem','mobile')")
        self.c.execute("INSERT INTO concorrentes(id,loja,id_loja,lancado_em) VALUES(1,'steam','h',date('now','-40 days'))")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja,status,fechada_em) VALUES('t','steam','h','fechada',date('now'))")
        self.assertEqual(self.c.execute(queries()['q_tendencia_fechada_fila']).fetchall(), [])
        self.c.execute("UPDATE ideias SET plataforma='steam' WHERE id=1")   # a clone on the hype's own platform leaves the queue
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_tendencia_fechada_fila'])], [1])


class GuardsR25(Base):
    def test_overrideDeConstrucaoExigeLoopIdle(self):
        i = self.nova(**dict(FICHA_OK, loop_idle=None))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_construcao', 'dono', f'"construo sem teste de comportamento a ideia#{i}" chat',
                                                     engine='p', engine_justificativa='j'))


if __name__ == '__main__':
    unittest.main()
