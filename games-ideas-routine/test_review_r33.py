"""Review round 33 (a trend detected after the queue entry, measured rooms outrank CCU, a sibling already reopened by
the routine is not blocked, overrun item matched by its text)."""
import unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


def col(c, nome, coluna, params=None):
    cur = c.execute(queries()[nome], params or {}); cols = [d[0] for d in cur.description]
    return cur.fetchone()[cols.index(coluna)]


class GuardsR33(Base):
    def test_tendenciaDetectadaDepoisDaFilaTrocaORotulo(self):
        i = self.nova(sem_vinculos=True, **dict(FICHA_OK, fonte_ideia='arbitragem', horas_estimadas=12))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','h','Hit',date('now','-30 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,reviews_total) VALUES(?,date('now','-10 days'),'global',100)", (cid,))
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(?,'candidata','pre_teste','x','rotina')", (i,))
        self.c.execute("DROP TRIGGER trg_ficha_antes_do_teste"); self.c.execute("UPDATE ideias SET estado='pre_teste' WHERE id=?", (i,))
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,reviews_total) VALUES(?,date('now'),'global',5000)", (cid,))
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja) VALUES('h','steam','h')")
        self.c.execute("UPDATE ideias SET fonte_ideia='tendencia' WHERE id=?", (i,))


class QueriesR33(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def test_salasMedidasVencemOCcu(self):
        self.c.execute("INSERT INTO config VALUES('lista_publica_ccu_mult','2','seed',datetime('now')),('lista_publica_min_salas','5','seed',datetime('now'))")
        self.c.execute("INSERT INTO ideias(id,titulo,tamanho_sala) VALUES(1,'a',2)")
        self.c.execute("INSERT INTO experimentos(id,ideia_id,etapa,tipo,estado) VALUES(1,1,'E5','pos_lancamento','rodando')")
        for d in range(0, 9):
            for m, v in (('ccu_pico', 25), ('salas_abertas_pico', 0)):
                self.c.execute("INSERT INTO metricas(experimento_id,data,metrica,valor,fonte) VALUES(1,date('now',?),?,?,'telemetria')", (f'-{d} days', m, v))
        self.assertEqual(col(self.c, 'q_lista_publica', 'ccu_ok', {'ideia_id': 1}), 0)

    def test_irmaReabertaPelaRotinaNaoEhBloqueada(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,arquivamento,reabrir_se,familia_id) VALUES(1,'a','arquivada','resultado','x',1)")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,familia_id) VALUES(2,'b','pre_teste',28,1)")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(2,'sinal','candidata','x','rotina')")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(2,'candidata','pre_teste','REABERTA: x [sinal#1]','rotina')")
        self.assertEqual(self.c.execute(queries()['q_irmas_bloqueadas']).fetchall(), [])

    def test_pendenciaDeHorasCasaPeloTexto(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,horas_estimadas) VALUES(5,'a','em_teste',20)")
        self.c.execute("INSERT INTO horas(ideia_id,data,horas,tipo,prova_dono) VALUES(5,date('now'),31,'validacao','x')")
        self.c.execute("INSERT INTO pendencias(texto) VALUES('horas estouradas ideia#5: cortar escopo, congelar ou continuar?')")
        self.assertEqual(col(self.c, 'q_checklist', 'horas_estouradas'), 0)


if __name__ == '__main__':
    unittest.main()
