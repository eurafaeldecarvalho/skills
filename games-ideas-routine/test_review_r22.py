"""Review round 22 (sibling stuck behind a light graveyard, trend-idea reopening loop, declared idle loop)."""
import sqlite3, unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


class QueriesR22(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()
        self.c.execute("INSERT INTO config VALUES('candidata_pendente_dias','14','seed',datetime('now')),('candidata_fila_dias','60','seed',datetime('now'))")

    def test_irmaAtrasDeArquivoPorResultadoApareceParaODono(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,arquivamento,reabrir_se,familia_id) VALUES(1,'a','arquivada','resultado','x',1)")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,familia_id) VALUES(2,'b','candidata',28,1)")
        cur = self.c.execute(queries()['q_irmas_bloqueadas']); cols = [d[0] for d in cur.description]; rows = cur.fetchall()
        self.assertEqual([r[0] for r in rows], [2])
        self.assertEqual(rows[0][cols.index('grave')], 0)

    def test_irmaBloqueadaEnvelheceNaFila(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,arquivamento,reabrir_se,familia_id) VALUES(1,'a','arquivada','resultado','x',1)")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,familia_id,trilha,atualizada_em) VALUES(2,'b','candidata',28,1,'W',datetime('now','-70 days'))")
        self.assertEqual([(r[0], r[-1]) for r in self.c.execute(queries()['q_candidatas_paradas'])], [(2, 'bloqueada_cemiterio')])

    def test_ideiaDeTendenciaNaoReabrePelaRotina(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,reabrir_se,fonte_ideia) VALUES(1,'t','arquivada','nova tendência aberta no mesmo gênero','tendencia')")
        self.assertEqual(self.c.execute(queries()['q_reabrir_candidatas']).fetchall(), [])


class GuardsR22(Base):
    def test_loopIdleDeclaradoNaoVaiPeloPoki(self):
        i = self.nova(genero='mining', **dict(FICHA_OK, exclusividade='poki', loop_idle=1))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'idle_vai_para_crazygames'):
            self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,))

    def test_fichaExigeLoopIdleDeclarado(self):
        i = self.nova(**dict(FICHA_OK, loop_idle=None))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))


if __name__ == '__main__':
    unittest.main()
