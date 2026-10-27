"""Review round 20 (failed test laundered into a light archive, hype clone frozen instead of killed, validada behind a
long build, owner override in a family with a graveyard, family checklist)."""
import sqlite3, unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_review_r15 import hipotese
from test_queries import queries
from test_queries_v2 import db_sem_travas


class LavagemR20(Base):
    def test_fallbackSemLeituraNaoApagaARecusa(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        x1 = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,fim) VALUES(?,'W2','portal_webfit','encerrado',date('now'))", (i,)).lastrowid
        hipotese(self.c, i, x1, 'W2', 'aceite_plataforma', 'refutada')
        x2 = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,decisao) VALUES(?,'W1','portal_teste','encerrado','sem_amostra')", (i,)).lastrowid
        hipotese(self.c, i, x2, 'W1', 'aceite_plataforma', 'inconclusiva_sem_trafego')
        self.assertIn('refutada_exige_morte', self.mover(i, 'arquivada', reabrir_se='x'))

    def test_cancelarComDadosNaoViraArquivoOperacional(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,inicio,decisao) VALUES(?,'W1','portal_teste','abortado',date('now'),'abortado')", (i,)).lastrowid
        self.c.execute("INSERT INTO metricas(experimento_id,data,metrica,valor,fonte) VALUES(?,date('now'),'jogadas',500,'portal_dashboard')", (x,))
        self.assertIn('cancelamento_com_dados', self.mover(i, 'arquivada', reabrir_se='x', arquivamento='operacional'))
        self.assertIsNone(self.mover(i, 'arquivada', reabrir_se='x', arquivamento='resultado'))

    def test_congelarComMetricasNaoDecididasRecusa(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,inicio) VALUES(?,'W1','portal_teste','rodando',date('now'))", (i,)).lastrowid
        hipotese(self.c, i, x, 'W1', 'pct_jogadas_3min', None)
        self.c.execute("INSERT INTO metricas(experimento_id,data,metrica,valor,fonte) VALUES(?,date('now'),'jogadas',500,'portal_dashboard')", (x,))
        self.assertIn('decidir_antes_de_sair_do_teste', self.mover(i, 'congelada', data_reativacao='2027-06-01'))

    def test_cloneDeHypeNaMesmaPlataformaMorreNaoCongela(self):
        i = self.nova(sem_vinculos=True, **dict(FICHA_OK, fonte_ideia='arbitragem'))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('poki','hype','Hype',date('now','-30 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista,rank_pos) VALUES(?,date('now'),'global','hot',1)", (cid,))
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja) VALUES('h','poki','hype')")
        self.assertIn('clone_de_hype_morre', self.mover(i, 'congelada', data_reativacao='2027-01-01'))
        self.c.execute("UPDATE ideias SET plataforma='mobile', trilha='M' WHERE id=?", (i,))   # a port to another platform is arbitrage
        self.assertIsNone(self.mover(i, 'congelada', data_reativacao='2027-01-01'))

    def test_overrideDoDonoNaFamiliaComCemiterio(self):
        a = self.nova(genero='deck', **FICHA_OK); self.mover(a, 'em_teste'); self.mover(a, 'arquivada', reabrir_se='x')
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('b','deck')").lastrowid
        from test_guards_v2 import ligar_referencia_e_evidencia
        ligar_referencia_e_evidencia(self.c, b); self.mover(b, 'candidata')
        self.c.execute('DROP TRIGGER trg_familia_escolha'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, b))
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in FICHA_OK) + ' WHERE id=?', list(FICHA_OK.values()) + [b])
        self.assertIsNone(self.mover(b, 'em_construcao', 'dono', f'"construo sem teste de comportamento a ideia#{b}" chat',
                                     motivo='REABERTA: dono construiu sem teste', engine='p', engine_justificativa='j'))


class QueriesR20(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()
        self.c.execute("INSERT INTO config VALUES('validada_max_dias','21','seed',datetime('now')),('validada_max_dias_arquivar','180','seed',datetime('now'))")

    def test_validadaAtrasDeBuildLongoAvisaODono(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'s','em_construcao'),(2,'w','validada')")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,em) VALUES(2,'em_teste','validada','x','rotina',datetime('now','-200 days'))")
        self.assertEqual(self.c.execute(queries()['q_validada_parada']).fetchall(), [(2, 'pendencia_vaga')])

    def test_arquivadaAntesDoGateNaoFalhaChecklistDeFamilia(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,arquivamento,reabrir_se) VALUES(1,'s','arquivada','operacional','x')")
        cur = self.c.execute(queries()['q_checklist']); cols = [d[0] for d in cur.description]
        self.assertEqual(cur.fetchone()[cols.index('ideias_sem_familia')], 0)


if __name__ == '__main__':
    unittest.main()
