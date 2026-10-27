"""Review round 9 (findings #1, #2, #3, #5, #6, #7, #8, #9, #12)."""
import sqlite3, unittest
from test_guards_v2 import Base, passar_etapas
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas
from lib import prova_existe


class TendenciaR9(Base):
    def concorrente(self, loja, dias, **snap):
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES(?,?,?,date('now',?))", (loja, f'{loja}{dias}', f'Jogo {loja}{dias}', f'-{dias} days')).lastrowid
        cols = ','.join(['concorrente_id', 'data', 'pais'] + list(snap)); ph = ','.join(['?', "date('now','-2 days')", "'global'"] + ['?'] * len(snap))
        self.c.execute(f'INSERT INTO concorrente_snapshots({cols}) VALUES({ph})', [cid] + list(snap.values()))
        return cid

    def test_hypeSteamComMuitasReviewsEhTendenciaSemLista(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem'))
        cid = self.concorrente('steam', 40, reviews_total=5000)
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.assertIn('tendencia_nao_registrada', self.mover(i, 'em_teste'))

    def test_listaNewNaoEhPopularidade(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem'))
        cid = self.concorrente('poki', 30, rank_lista='new', rank_pos=3)
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'rival')", (i, cid))
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_lancadoEmExigeFormatoIso(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'CHECK'):
            self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('steam','x','Oct 20, 2022')")

    def test_buildDeValidadaNaoReconfereFamilia(self):
        a = self.nova(genero='deck', **FICHA_OK)
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('steam','r','2020-01-01')")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'rival')", (a,))
        b = self.nova(genero='deck', **FICHA_OK); self.mover(b, 'em_teste'); passar_etapas(self.c, b)
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now','+1 second') WHERE id=?", (b,)); self.mover(b, 'validada')
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'rival')", (b,))
        self.assertIsNone(self.mover(b, 'em_construcao', 'dono', f'"aprovo a construção da ideia#{b}" chat', engine='p', engine_justificativa='j'))

    def test_lancamentoCriaExperimentoE5(self):
        i = self.nova(**FICHA_OK)
        self.mover(i, 'em_construcao', 'dono', f'"construo sem teste de comportamento a ideia#{i}" chat', engine='p', engine_justificativa='j')
        self.mover(i, 'lancada', 'dono', f'"ideia#{i} lançada em poki em 27/10" chat')
        self.assertEqual(self.c.execute("SELECT etapa,tipo,estado FROM experimentos WHERE ideia_id=?", (i,)).fetchall(), [('E5', 'pos_lancamento', 'rodando')])

    def test_construcaoSemTesteExigeFicha(self):
        i = self.nova(**dict(FICHA_OK, horas_estimadas=None))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_construcao', 'dono', f'"construo sem teste de comportamento a ideia#{i}" chat', engine='p', engine_justificativa='j'))


class ProvaR9(unittest.TestCase):
    def test_fraseNegadaNaoEhProva(self):
        self.assertFalse(prova_existe('"aprovo a construção da ideia#1" chat', ['ainda não aprovo a construção da ideia#1, falta polir'], 1))

    def test_fraseNoInicioDaFraseEhProva(self):
        self.assertTrue(prova_existe('"aprovo a construção da ideia#1" chat', ['Ok. Aprovo a construção da ideia#1, pode seguir'], 1))


class QueriesR9(unittest.TestCase):
    def test_recriadaNaoReabre(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado,reabrir_se) VALUES(1,'b','arquivada','recriada como ideia#3')")
        self.assertEqual(c.execute(queries()['q_reabrir_candidatas']).fetchall(), [])

    def test_planejadoDeTendenciaFechada(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado,fonte_ideia) VALUES(1,'t','em_teste','tendencia')")
        c.execute("INSERT INTO concorrentes(id,loja,id_loja,lancado_em) VALUES(1,'roblox','9',date('now','-40 days'))")
        c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        c.execute("INSERT INTO tendencias(nome,loja,id_loja,status) VALUES('t','roblox','9','fechada')")
        c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(1,'R1','roblox_mvp','planejado')")
        self.assertEqual([r[0] for r in c.execute(queries()['q_tendencia_fechada_planejados'])], [1])


if __name__ == '__main__':
    unittest.main()
