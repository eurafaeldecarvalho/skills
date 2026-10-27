"""Review round 7 (findings #1/#6, #2, #3, #4/#8)."""
import sqlite3, unittest
from test_guards_v2 import Base, passar_etapas
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas
from test_review_r6 import col


class E5SemExtrato(unittest.TestCase):
    def test_semExtratoDoMesNaoCongelaNemArquiva(self):
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('e5_d60_min_usd','5','seed',datetime('now')),('e5_d120_min_usd','10','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','lancada')")
        c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono,em) VALUES(1,'em_construcao','lancada','t','dono','x',datetime('now','-130 days'))")
        self.assertEqual(c.execute(queries()['q_e5_escada']).fetchall()[0][-1], 'aguardar_extrato')
        self.assertEqual(col(c, 'q_checklist', 'lancadas_sem_extrato'), 1)


class GuardsR7(Base):
    def test_ideiaMaisNovaNaoMudaAFamiliaDaValidada(self):
        a = self.nova(genero='deck', **FICHA_OK); self.mover(a, 'em_teste'); passar_etapas(self.c, a)
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now','+1 second') WHERE id=?", (a,)); self.mover(a, 'validada')
        b = self.nova(genero='deck', **FICHA_OK)
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('steam','r','2020-01-01')")
        for x in (a, b): self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'))", (x,))
        self.assertIsNone(self.mover(a, 'em_construcao', 'dono', f'"aprovo a construção da ideia#{a}" chat', engine='p', engine_justificativa='j'))

    def test_rivalRecenteNaoTornaAIdeiaTendencia(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem'))
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','r','RivalRecente',date('now','-40 days'))")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'rival')", (i,))   # recent, not in a top list
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,reviews_total) VALUES((SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),date('now'),'global',10)")   # round 29: one popularity number
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_referenciaRecenteSemTendenciaRegistradaBarra(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem'))
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('steam','h',date('now','-40 days'))")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (i,))
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista,rank_pos) VALUES((SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),date('now'),'global','most-played',3)")
        self.assertIn('tendencia_nao_registrada', self.mover(i, 'em_teste'))

    def test_fraseEmCaixaAltaComAcento(self):
        i = self.nova(**FICHA_OK)
        self.mover(i, 'em_teste'); passar_etapas(self.c, i)
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now','+1 second') WHERE id=?", (i,)); self.mover(i, 'validada')
        self.assertIsNone(self.mover(i, 'em_construcao', 'dono', f'"APROVO A CONSTRUÇÃO DA IDEIA#{i}" chat', engine='p', engine_justificativa='j'))


if __name__ == '__main__':
    unittest.main()
