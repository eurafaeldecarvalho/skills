"""Review round 24 (closed-trend queue query respects the 120-day expiry)."""
import unittest
from test_queries import queries
from test_queries_v2 import db_sem_travas


class QueriesR24(unittest.TestCase):
    def test_liderVencidoComTendenciaFechadaNaoTiraIdeiaDaFila(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado,fonte_ideia) VALUES(1,'port','candidata','arbitragem')")
        c.execute("INSERT INTO concorrentes(id,loja,id_loja,lancado_em) VALUES(1,'steam','h',date('now','-130 days'))")
        c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        c.execute("INSERT INTO tendencias(nome,loja,id_loja,status,fechada_em) VALUES('t','steam','h','fechada',date('now','-70 days'))")
        self.assertEqual(c.execute(queries()['q_tendencia_fechada_fila']).fetchall(), [])


if __name__ == '__main__':
    unittest.main()
