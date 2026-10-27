"""Review round 26 (trend label of a frozen port, blocked-sibling queries mirror the trigger, n_atingivel exact
quotient, launch phrase prefix, and guard tests the mutation run found missing)."""
import sqlite3, unittest
from lib import n_atingivel, prova_existe
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


class TendenciaR26(Base):
    def test_portCongeladoVoltaComORotuloReal(self):
        i = self.nova(sem_vinculos=True, **dict(FICHA_OK, fonte_ideia='tendencia', plataforma='mobile', trilha='M'))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','h','Hype',date('now','-30 days'))").lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.assertIsNone(self.mover(i, 'congelada', data_reativacao='2027-01-01'))
        self.c.execute("UPDATE concorrentes SET lancado_em=date('now','-130 days') WHERE id=?", (cid,))   # the guards stopped
        self.assertIsNone(self.mover(i, 'candidata', motivo='reativada'))
        self.c.execute("UPDATE ideias SET fonte_ideia='arbitragem' WHERE id=?", (i,))

    def test_rotuloDeTendenciaComLiderVivoSegueTravado(self):
        i = self.nova(sem_vinculos=True, **dict(FICHA_OK, fonte_ideia='tendencia', plataforma='mobile', trilha='M'))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','h','Hype',date('now','-30 days'))").lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.mover(i, 'congelada', data_reativacao='2027-01-01'); self.mover(i, 'candidata', motivo='reativada')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'fonte_ideia_imutavel'):
            self.c.execute("UPDATE ideias SET fonte_ideia='arbitragem' WHERE id=?", (i,))


class GuardsBasicosR26(Base):
    def test_quintaIdeiaEmPreTesteRecusa(self):
        ids = [self.nova(genero=f'g{k}', **FICHA_OK) for k in range(5)]
        for i in ids[:4]:
            self.assertIsNone(self.mover(i, 'pre_teste'))
        self.assertIn('portfolio_cheio', self.mover(ids[4], 'pre_teste'))

    def test_irmaNaMesmaFamiliaNaoOcupaSegundaVaga(self):
        a = self.nova(genero='deck', **FICHA_OK); self.mover(a, 'pre_teste')
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('b','deck')").lastrowid
        from test_guards_v2 import ligar_referencia_e_evidencia
        ligar_referencia_e_evidencia(self.c, b); self.mover(b, 'candidata')
        self.c.execute('DROP TRIGGER trg_familia_escolha'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, b))
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in FICHA_OK) + ' WHERE id=?', list(FICHA_OK.values()) + [b])
        self.assertIn('familia_ocupada', self.mover(b, 'pre_teste'))

    def test_transicaoForaDaTabelaRecusa(self):
        i = self.nova(**FICHA_OK)
        self.assertIn('transicao_fora_da_tabela', self.mover(i, 'lancada', 'dono', f'"ideia#{i} lançada em poki em 27/10" chat'))

    def test_mudarEstadoSemEventoRecusa(self):
        i = self.nova(**FICHA_OK)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'sem_ideia_evento'):
            self.c.execute("UPDATE ideias SET estado='pre_teste' WHERE id=?", (i,))

    def test_reabrirSemEventoREABERTARecusa(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'arquivada', reabrir_se='x', arquivamento='operacional')
        self.assertIn('reabertura_proibida', self.mover(i, 'candidata', motivo='voltou'))


class QueriesR26(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()
        self.c.execute("INSERT INTO config VALUES('candidata_pendente_dias','14','seed',datetime('now')),('candidata_fila_dias','60','seed',datetime('now'))")

    def test_reaberturaDaRotinaNaoDesbloqueiaIrmaNaFila(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,motivo_morte,familia_id) VALUES(1,'a','morta','mercado_saturado',1)")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,familia_id,trilha,atualizada_em) VALUES(2,'b','candidata',28,1,'W',datetime('now','-70 days'))")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,em) VALUES(2,'arquivada','candidata','REABERTA: x','rotina',datetime('now','-70 days'))")
        self.assertEqual([(r[0], r[-1]) for r in self.c.execute(queries()['q_candidatas_paradas'])], [(2, 'bloqueada_cemiterio')])

    def test_reaberturaDoDonoAntesDaMorteDaIrmaNaoCobre(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,motivo_morte,familia_id) VALUES(1,'a','morta','teste_reprovado',1)")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,familia_id) VALUES(2,'b','candidata',28,1)")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(2,'arquivada','candidata','REABERTA: x','dono','\"reabro a ideia#2\" chat')")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(1,'em_teste','morta','teste','rotina')")
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_irmas_bloqueadas'])], [2])


class LibR26(unittest.TestCase):
    def test_nAtingivelComQuocienteExato(self):
        self.assertEqual(n_atingivel(300, 6.0, 0.05), 1000)
        self.assertEqual(n_atingivel(275, 5.5, 0.2), 250)

    def test_fraseDeLancamentoEhOPrefixoFixo(self):
        inbox = ['## 2026-10-27 09:00\nIdeia#12 lançada em Poki em 27/10/2026.']
        self.assertTrue(prova_existe('"ideia#12 lançada em Poki em 27/10/2026" chat 2026-10-27 09:00', inbox, 12, 'ideia#12 lançada em'))


if __name__ == '__main__':
    unittest.main()
