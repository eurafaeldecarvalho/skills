"""Review round 10 (findings #1/#7, #2/#8, #3, #4, #6)."""
import sqlite3, unittest
from test_guards_v2 import Base, ligar_referencia_e_evidencia
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas
from lib import decidir, prova_existe


class LibR10(unittest.TestCase):
    def test_contagemNaoPassaComAmostraAbaixoDoMinimo(self):
        self.assertEqual(decidir('contagem', 240, 7, 201, 20, 14, 0, False), 'aguardar')

    def test_s1EstendidoNaoExtrapolaNoDia15(self):
        self.assertEqual(decidir('contagem', 161, 15, 201, 20, 14, 0, True, False, 300), 'aguardar')

    def test_aceiteDePlataformaAindaPassaComUmaDecisao(self):
        self.assertEqual(decidir('contagem', 1, 1, 1, -1, 1, 1, True, True, 1), 'passa')

    def test_fraseDepoisDeQuebraDeLinhaOuMarcador(self):
        self.assertTrue(prova_existe('"aprovo a construção da ideia#5" chat', ['Beleza\naprovo a construção da ideia#5'], 5))
        self.assertTrue(prova_existe('"aprovo a construção da ideia#5" chat', ['- aprovo a construção da ideia#5'], 5))


class QueriesR10(unittest.TestCase):
    def test_tendenciaFechadaExpiradaNaoArquivaPlanejado(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','em_teste')")
        c.execute("INSERT INTO concorrentes(id,loja,id_loja,lancado_em) VALUES(1,'steam','99',date('now','-200 days'))")
        c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        c.execute("INSERT INTO tendencias(nome,loja,id_loja,status) VALUES('hit','steam','99','fechada')")
        c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(1,'W1','portal_teste','planejado')")
        self.assertEqual(c.execute(queries()['q_tendencia_fechada_planejados']).fetchall(), [])


class GuardsR10(Base):
    def test_arquivamentoOperacionalNaoEhCemiterio(self):
        a = self.nova(genero='deck', **FICHA_OK)
        self.mover(a, 'arquivada', reabrir_se='vaga de teste livre', arquivamento='operacional')
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('b','deck')").lastrowid
        ligar_referencia_e_evidencia(self.c, b)
        self.mover(b, 'candidata')
        self.c.execute('DROP TRIGGER trg_familia_escolha'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, b))
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in FICHA_OK) + ' WHERE id=?', list(FICHA_OK.values()) + [b])
        self.assertIsNone(self.mover(b, 'em_teste'))

    def test_rivalHypeNaoTravaAIdeia(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem'))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('play','h','HypeGame',date('now','-40 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista) VALUES(?,date('now'),'global','top-trending')", (cid,))
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja) VALUES('h','play','h')")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'rival')", (i, cid))
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_jogoCitadoNoTwistPrecisaSerReferencia(self):
        i = self.nova(**dict(FICHA_OK, twist='É HypeGame, mas no celular, de modo que pct_3min >= 35%'))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('play','h','HypeGame','2020-01-01')").lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'rival')", (i, cid))
        self.assertIn('referencia_no_twist', self.mover(i, 'em_teste'))


if __name__ == '__main__':
    unittest.main()
