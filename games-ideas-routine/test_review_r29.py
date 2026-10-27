"""Review round 29 (undetermined popularity of a recent game, trend window enforced, refuted test archived as a result,
blocked sibling already in pre_teste, owner rejection not reopened by the routine, word-boundary rival check)."""
import sqlite3, unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_review_r15 import hipotese
from test_queries import queries
from test_queries_v2 import db_sem_travas


def col(c, nome, coluna):
    cur = c.execute(queries()[nome]); cols = [d[0] for d in cur.description]
    return cur.fetchone()[cols.index(coluna)]


class GuardsR29(Base):
    def test_jogoRecenteSemDadoDePopularidadeNaoEntra(self):
        i = self.nova(**FICHA_OK)
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','hy','Hype',date('now','-20 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,preco) VALUES(?,date('now'),'global',4.99)", (cid,))
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'rival')", (i, cid))
        self.assertIn('popularidade_indeterminada', self.mover(i, 'em_teste'))
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista,reviews_total) VALUES(?,date('now'),'global','x',40)", (cid,))
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_tendenciaAbertaAlemDaJanelaNaoValeComoAberta(self):
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('horas_semana_dono_min','8','seed'),('tendencia_mvp_dias_max','14','seed'),('tendencia_janela_semanas','6','seed')")
        i = self.nova(**dict(FICHA_OK, fonte_ideia='tendencia', horas_estimadas=12, exclusividade='crazygames_agregadores'))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('poki','h','Hype',date('now','-70 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,plays) VALUES(?,date('now'),'global',200000)", (cid,))
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja,detectada_em) VALUES('h','poki','h',date('now','-60 days'))")
        self.assertIn('tendencia_sem_janela_aberta', self.mover(i, 'em_teste'))

    def test_testeRefutadoArquivaComoResultado(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,fim) VALUES(?,'W1','portal_teste','encerrado',date('now'))", (i,)).lastrowid
        hipotese(self.c, i, x, 'W1', 'pct_jogadas_3min', 'refutada')
        self.assertIn('refutada_arquiva_como_resultado', self.mover(i, 'arquivada', reabrir_se=f'recriada como ideia#{i + 1}', arquivamento='operacional'))
        self.assertIsNone(self.mover(i, 'arquivada', reabrir_se='x', arquivamento='resultado'))

    def test_rivalCurtoSoCasaPalavraInteira(self):
        i = self.nova(**dict(FICHA_OK, twist='É Valheim, mas com crafting automatizado, de modo que Z'))
        rid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','raft','Raft','2018-01-01')").lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'rival')", (i, rid))
        self.assertIsNone(self.mover(i, 'em_teste'))


class QueriesR29(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def test_irmaBloqueadaJaEmPreTesteApareceParaODono(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,motivo_morte,familia_id) VALUES(1,'a','morta','advogado_do_diabo',1)")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,familia_id) VALUES(2,'b','pre_teste',28,1)")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(2,'sinal','candidata','x','rotina')")
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_irmas_bloqueadas'])], [2])

    def test_recusaDoDonoNaoReabrePelaRotina(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,reabrir_se) VALUES(1,'a','arquivada','dono pede: reabro a ideia#1')")
        self.assertEqual(self.c.execute(queries()['q_reabrir_candidatas']).fetchall(), [])

    def test_snapshotSoComPrecoNaoContaComoFoto(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','candidata')")
        self.c.execute("INSERT INTO concorrentes(id,loja,id_loja,lancado_em) VALUES(1,'steam','s','2020-01-01')")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista,preco) VALUES(1,date('now'),'global','',4.99)")
        self.assertEqual(col(self.c, 'q_checklist', 'concorrentes_sem_foto'), 1)

    def test_tendenciaAbertaVencidaNoChecklist(self):
        self.c.execute("INSERT INTO config VALUES('tendencia_janela_semanas','6','seed',datetime('now'))")
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja,detectada_em) VALUES('t','steam','x',date('now','-60 days'))")
        self.assertEqual(col(self.c, 'q_checklist', 'tendencias_abertas_vencidas'), 1)


if __name__ == '__main__':
    unittest.main()
