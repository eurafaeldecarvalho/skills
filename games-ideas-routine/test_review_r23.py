"""Review round 23 (decision oracle, hypothesis of another stage, light-graveyard owner reopening, trend idea stuck in
the queue, declared idle lock)."""
import sqlite3, unittest
from test_guards_v2 import Base, ligar_referencia_e_evidencia
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas

ABERTA = ("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,"
          "eventos_min,limiar_versao,previsao,prazo_dias) VALUES(?,?,?,'e','m','media',3,1.5,500,0,1,3,7)")


class OraculoR23(Base):
    def setUp(self):
        super().setUp()
        self.i = self.nova(**FICHA_OK)
        self.x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,inicio) VALUES(?,'W1','portal_teste','rodando',date('now'))", (self.i,)).lastrowid

    def test_hipoteseNaoNasceDecidida(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_so_por_update'):
            self.c.execute(ABERTA.replace("prazo_dias)", "prazo_dias,resultado,fechada_em)").replace("3,7)", "3,7,'confirmada',datetime('now'))"),
                           (self.i, self.x, 'W1'))

    def test_confirmadaAbaixoDoLimiarRecusa(self):
        h = self.c.execute(ABERTA, (self.i, self.x, 'W1')).lastrowid
        self.c.execute("INSERT INTO metricas(experimento_id,data,metrica,valor,fonte) VALUES(?,date('now'),'jogadas',500,'portal_dashboard')", (self.x,))
        upd = "UPDATE hipoteses SET resultado=?, fechada_em=datetime('now'), n_observado=500, eventos_observados=?, valor_observado=? WHERE id=?"
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_incoerente'):
            self.c.execute(upd, ('confirmada', 200, 0.4, h))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_sem_dado'):
            self.c.execute(upd, ('confirmada', None, 3.2, h))
        self.c.execute(upd, ('confirmada', 1600, 3.2, h))

    def test_refutadaAcimaDoLimiarRecusa(self):
        h = self.c.execute(ABERTA, (self.i, self.x, 'W1')).lastrowid
        self.c.execute("INSERT INTO metricas(experimento_id,data,metrica,valor,fonte) VALUES(?,date('now'),'jogadas',500,'portal_dashboard')", (self.x,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_incoerente'):
            self.c.execute("UPDATE hipoteses SET resultado='refutada', fechada_em=datetime('now'), n_observado=500, eventos_observados=1600, valor_observado=3.2 WHERE id=?", (h,))

    def test_hipoteseDeOutraEtapaRecusa(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'hipotese_de_outra_etapa'):
            self.c.execute(ABERTA, (self.i, self.x, 'G1'))


class FamiliaR23(Base):
    def test_reabertaDoDonoNoCemiterioLeveCobreAsDuasEntradas(self):
        a = self.nova(genero='deck', **FICHA_OK); self.mover(a, 'em_teste'); self.mover(a, 'arquivada', reabrir_se='x')
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('b','deck')").lastrowid
        ligar_referencia_e_evidencia(self.c, b); self.mover(b, 'candidata')
        self.c.execute('DROP TRIGGER trg_familia_escolha'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, b))
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in FICHA_OK) + ' WHERE id=?', list(FICHA_OK.values()) + [b])
        self.assertIsNone(self.mover(b, 'pre_teste', 'dono', f'"reabro a ideia#{b}" chat', motivo='REABERTA: dono'))
        self.assertIsNone(self.mover(b, 'em_teste'))

    def test_loopIdleDeclaradoNaoVoltaAZero(self):
        i = self.nova(**dict(FICHA_OK, loop_idle=1, exclusividade='crazygames_agregadores')); self.mover(i, 'em_teste')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'loop_idle_imutavel'):
            self.c.execute('UPDATE ideias SET loop_idle=0 WHERE id=?', (i,))


class QueriesR23(unittest.TestCase):
    def test_ideiaDeTendenciaNaFilaComTendenciaFechadaSai(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado,fonte_ideia,plataforma) VALUES(1,'t','pre_teste','tendencia','web')")
        c.execute("INSERT INTO concorrentes(id,loja,id_loja,lancado_em) VALUES(1,'poki','h',date('now','-50 days'))")
        c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        c.execute("INSERT INTO tendencias(nome,loja,id_loja,status,fechada_em) VALUES('t','poki','h','fechada',date('now'))")
        self.assertEqual([r[0] for r in c.execute(queries()['q_tendencia_fechada_fila'])], [1])


if __name__ == '__main__':
    unittest.main()
