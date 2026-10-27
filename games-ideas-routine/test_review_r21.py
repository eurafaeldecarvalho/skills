"""Review round 21 (silent default in decidir, hypothesis decided without data, uncertain portal release dates,
live LLM content, family entry consistency, family-occupied queue, blocked siblings)."""
import sqlite3, unittest
from lib import decidir, prova_existe
from test_guards_v2 import Base, ligar_referencia_e_evidencia
from test_review_r1 import FICHA_OK
from test_review_r15 import hipotese
from test_queries import queries
from test_queries_v2 import db_sem_travas


class LibR21(unittest.TestCase):
    def test_contagemEstendidaExigePassaEstendidoExplicito(self):
        with self.assertRaises(ValueError):
            decidir('contagem', 1, 1, 1, -1, 1, 1, 1, True)

    def test_inboxComCabecalhoDeDataEMensagemNaLinhaSeguinte(self):
        texto = '## 2026-10-27 10:00\naprovo a construção da ideia#12'
        self.assertTrue(prova_existe('"aprovo a construção da ideia#12" chat 2026-10-27 10:00', [texto], 12, 'aprovo a construção da ideia#12'))


class GuardsR21(Base):
    def test_hipoteseNaoSeDecideSemDado(self):
        i = self.nova(**FICHA_OK)
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','rodando')", (i,)).lastrowid
        hipotese(self.c, i, x, 'W1', 'pct_jogadas_3min', None)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_sem_dado'):
            self.c.execute("UPDATE hipoteses SET resultado='confirmada', fechada_em=datetime('now') WHERE experimento_id=?", (x,))
        self.c.execute("UPDATE hipoteses SET resultado='inconclusiva_sem_trafego', fechada_em=datetime('now') WHERE experimento_id=?", (x,))

    def test_dataIncertaDePortalNaoViraTendencia(self):
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em,lancado_em_incerto) VALUES('poki','bb','Block Blast',date('now'),1)").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista,rank_pos) VALUES(?,date('now'),'global','hot',1)", (cid,))
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM v_tendencia_viva').fetchone()[0], 0)

    def test_llmAoVivoSemPlanoDeModeracaoSoMorre(self):
        i = self.nova(**dict(FICHA_OK, ai_runtime=None))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))
        self.c.execute('UPDATE ideias SET ai_runtime=1 WHERE id=?', (i,))
        self.assertIn('excluida_por_regra', self.mover(i, 'em_teste'))
        self.c.execute("UPDATE ideias SET plano_moderacao='filtro de saída por lista fechada de temas, bloqueio de nomes e chat, revisão diária do dono e botão de denúncia' WHERE id=?", (i,))
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_familiaHerdadaDaIrmaMaisNovaEntraEmTeste(self):
        """older O (2 columns) vs newer live X (3 columns): the family chosen at the gate (X's) also passes the entry check."""
        o = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('O','deck')").lastrowid
        ligar_referencia_e_evidencia(self.c, o); self.mover(o, 'candidata'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (o, o))
        n = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('n','deck')").lastrowid   # waits in sinal
        x = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('X','deck')").lastrowid
        ligar_referencia_e_evidencia(self.c, x)
        ref_o = self.c.execute('SELECT concorrente_id FROM ideia_concorrentes WHERE ideia_id=?', (o,)).fetchone()[0]
        ref_x = self.c.execute('SELECT concorrente_id FROM ideia_concorrentes WHERE ideia_id=?', (x,)).fetchone()[0]
        sig_x = self.c.execute('SELECT sinal_id FROM evidencias WHERE ideia_id=?', (x,)).fetchone()[0]
        self.mover(x, 'candidata'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (x, x))
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia'),(?,?,'rival')", (n, ref_x, n, ref_o))
        self.c.execute('INSERT INTO evidencias VALUES(?,?,1,1,NULL)', (n, sig_x))
        self.mover(n, 'candidata'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (x, n))
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in FICHA_OK) + ' WHERE id=?', list(FICHA_OK.values()) + [n])
        self.assertIsNone(self.mover(n, 'em_teste'))


class QueriesR21(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()
        self.c.execute("INSERT INTO config VALUES('candidata_pendente_dias','14','seed',datetime('now')),('candidata_fila_dias','60','seed',datetime('now'))")

    def test_familiaOcupadaTambemEhSemVaga(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,familia_id) VALUES(1,'a','em_teste',1)")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,familia_id,trilha,atualizada_em) VALUES(2,'b','candidata',28,1,'W',datetime('now','-70 days'))")
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_candidatas_paradas'])], [2])

    def test_irmaBloqueadaPeloCemiterioApareceParaODono(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,motivo_morte,familia_id) VALUES(1,'a','morta','clone_legal',1)")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,familia_id) VALUES(2,'b','candidata',28,1)")
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_irmas_bloqueadas'])], [2])


if __name__ == '__main__':
    unittest.main()
