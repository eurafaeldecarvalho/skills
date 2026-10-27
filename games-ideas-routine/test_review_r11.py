"""Review round 11 (findings #1, #2/#8, #3, #4, #6, #11, #12)."""
import sqlite3, unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_review_r2 import hipotese
from test_queries import queries
from test_queries_v2 import db_sem_travas


class GuardsR11(Base):
    def setUp(self):
        super().setUp()
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('tendencia_ratings_min','10000','seed'),('tendencia_installs_min','1000000','seed'),('tendencia_favoritos_min','100000','seed')")

    def test_planejadoVencidoNaoApagaRefutacao(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        hipotese(self.c, i, 'W1', 'refutada', estendida=1)
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,decisao) VALUES(?,'W1','portal_teste','encerrado','planejado_vencido')", (i,)).lastrowid
        self.c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,previsao,prazo_dias,resultado,fechada_em) "
                       "VALUES(?,?,'W1','e','aceite_plataforma','contagem',1,-1,1,1,1,1,21,'inconclusiva_amostra_parcial',datetime('now'))", (i, x))
        self.assertIn('refutada_exige_morte', self.mover(i, 'arquivada', reabrir_se='x', arquivamento='operacional'))

    def test_arquivamentoZeraNaReaberturaEExigeValor(self):
        i = self.nova(**FICHA_OK)
        self.assertIn('arquivamento_obrigatorio', self.mover(i, 'arquivada', reabrir_se='x', arquivamento=None))
        self.mover(i, 'arquivada', reabrir_se='x', arquivamento='operacional')
        self.mover(i, 'candidata', motivo='REABERTA: x')
        self.assertEqual(self.c.execute('SELECT arquivamento FROM ideias WHERE id=?', (i,)).fetchone()[0], None)

    def test_hitMobileComMuitasAvaliacoesEhTendencia(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem'))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('appstore','m',date('now','-60 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,ratings_count) VALUES(?,date('now'),'global',2000000)", (cid,))
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.assertIn('tendencia_nao_registrada', self.mover(i, 'em_teste'))

    def test_exclusividadeTravaDepoisDoPrimeiroExperimento(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'exclusividade_travada'):
            self.c.execute("UPDATE ideias SET exclusividade='crazygames_agregadores' WHERE id=?", (i,))
        hipotese(self.c, i, 'W1', 'refutada', estendida=1)        # a Poki refusal after the iteration opens the fallback
        self.c.execute("UPDATE ideias SET exclusividade='crazygames_agregadores' WHERE id=?", (i,))

    def test_fonteTendenciaExigeTendenciaAberta(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='tendencia', horas_estimadas=10))
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('horas_semana_dono_min','8','seed'),('tendencia_mvp_dias_max','14','seed')")
        self.assertIn('tendencia_sem_janela_aberta', self.mover(i, 'em_teste'))

    def test_liderExpiraNoDia120(self):
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('roblox','z',date('now','-120 days'))")
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM v_tendencia_viva').fetchone()[0], 0)


class QueriesR11(unittest.TestCase):
    def test_ideiaSteamSemLiberacaoNaoSaiPorFila(self):
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('candidata_pendente_dias','14','seed',datetime('now')),('candidata_fila_dias','60','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo,estado,score,trilha,atualizada_em) VALUES(1,'s','candidata',31,'S',datetime('now','-70 days'))")
        self.assertEqual(c.execute(queries()['q_candidatas_paradas']).fetchall(), [])


if __name__ == '__main__':
    unittest.main()
