"""Review round 28 (the behavior test outranks a re-graded Demand at validada; overrun item answered once; queue
label mirrors its filter)."""
import unittest
from test_guards_v2 import Base, passar_etapas
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


def col(c, nome, coluna):
    cur = c.execute(queries()[nome]); cols = [d[0] for d in cur.description]
    return cur.fetchone()[cols.index(coluna)]


class ValidadaR28(Base):
    def test_testeConfirmadoValeMaisQueDemandaRebaixada(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        passar_etapas(self.c, i)
        self.c.execute("""UPDATE ideias SET score_json='{"demanda":4,"twist":7,"canal":7,"execucao":7,"economia":4}', advogado_em=datetime('now','+1 second') WHERE id=?""", (i,))
        self.assertIsNone(self.mover(i, 'validada'))


class QueriesR28(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def test_continuarDoDonoNaoRearmaHorasEstouradas(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,horas_estimadas) VALUES(1,'a','em_teste',25)")
        self.c.execute("INSERT INTO horas(ideia_id,data,horas,tipo,prova_dono) VALUES(1,date('now'),40,'validacao','x')")
        self.c.execute("INSERT INTO pendencias(ideia_id,texto,resolvida_em,prova_dono) VALUES(1,'horas estouradas ideia#1',datetime('now'),'\"continuar ideia#1\" chat')")
        self.assertEqual(col(self.c, 'q_checklist', 'horas_estouradas'), 0)

    def test_irmaJaLiberadaPeloDonoSaiComoSemVaga(self):
        self.c.execute("INSERT INTO config VALUES('candidata_pendente_dias','14','seed',datetime('now')),('candidata_fila_dias','60','seed',datetime('now'))")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,motivo_morte,reabrir_se,familia_id) VALUES(1,'a','morta','sem_canal','x',1)")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(1,'candidata','morta','x','rotina')")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,familia_id,trilha,atualizada_em) VALUES(2,'b','candidata',28,1,'W',datetime('now','-70 days'))")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(2,'sinal','candidata','x','rotina')")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(2,'candidata','candidata','REABERTA: dono','dono','\"reabro a ideia#2\" chat')")
        for k in range(3, 7):
            self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(?,'q','pre_teste')", (k,))
        self.assertEqual([(r[0], r[-1]) for r in self.c.execute(queries()['q_candidatas_paradas'])], [(2, 'sem_vaga')])


if __name__ == '__main__':
    unittest.main()
