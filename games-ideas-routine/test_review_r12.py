"""Review round 12 (findings #1, #3, #5)."""
import sqlite3, unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


class GuardsR12(Base):
    def test_descongeloSoVoltaParaOEstadoDeOrigem(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        self.mover(i, 'congelada', data_reativacao='2027-01-01')
        self.assertIn('descongelo_fora_da_origem', self.mover(i, 'lancada', 'dono', f'"descongelo a ideia#{i}" chat'))
        self.assertIn('descongelo_fora_da_origem', self.mover(i, 'em_construcao', 'dono', f'"descongelo a ideia#{i}" chat', engine='p', engine_justificativa='j'))

    def test_hypeRobloxContaDaPrimeiraPopularidade(self):
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('roblox','sab',date('now','-144 days'))").lastrowid
        # round 14: the rise must be observed (a non-popular snapshot before the first popular one)
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,ccu) VALUES(?,date('now','-40 days'),'global',200)", (cid,))
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista,rank_pos) VALUES(?,date('now','-20 days'),'global','top-trending',1)", (cid,))
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM v_tendencia_detectada').fetchone()[0], 1)

    def test_classicoRobloxNaoViraTendencia(self):
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('roblox','adopt','2017-07-14')").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista,rank_pos) VALUES(?,date('now','-2 days'),'global','top-trending',3)", (cid,))
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM v_tendencia_detectada').fetchone()[0], 0)


class QueriesR12(unittest.TestCase):
    def test_exploracaoNaoReabrePelaRotina(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado,reabrir_se,exploracao) VALUES(1,'e','arquivada','x',1)")
        self.assertEqual(c.execute(queries()['q_reabrir_candidatas']).fetchall(), [])


if __name__ == '__main__':
    unittest.main()
