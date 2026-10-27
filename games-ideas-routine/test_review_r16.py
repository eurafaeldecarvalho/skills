"""Review round 16 (findings: cancelled fallback, build-based CrazyGames switch, Roblox top-trending, pre-registration
copy, derivable negative adjustments, Web Fit sample, multiline quote, rate above 100%)."""
import sqlite3, unittest
from lib import decidir, prova_existe
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_review_r15 import hipotese


class GuardsR16(Base):
    def test_cancelarOFallbackNaoApagaARecusaPoki(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        x1 = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,fim) VALUES(?,'W2','portal_webfit','encerrado',date('now'))", (i,)).lastrowid
        hipotese(self.c, i, x1, 'W2', 'aceite_plataforma', 'refutada')
        x2 = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,decisao) VALUES(?,'W1','portal_teste','abortado','abortado')", (i,)).lastrowid
        hipotese(self.c, i, x2, 'W1', 'aceite_plataforma', 'inconclusiva_amostra_parcial')
        self.assertIn('refutada_exige_morte', self.mover(i, 'arquivada', reabrir_se='x', arquivamento='operacional'))
        self.assertIsNone(self.mover(i, 'morta', motivo_morte='teste_reprovado'))

    def test_buildMedidoAntesDoTesteTrocaParaCrazyGames(self):
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('poki_build_mb_max','5','seed'),('tempo_gameplay_s_max','10','seed')")
        i = self.nova(**dict(FICHA_OK, exclusividade='poki')); self.mover(i, 'em_teste')
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'exclusividade_travada'):   # nothing measured yet
            self.c.execute("UPDATE ideias SET exclusividade='crazygames_agregadores' WHERE id=?", (i,))
        self.c.execute('UPDATE ideias SET build_mb=11 WHERE id=?', (i,))
        self.c.execute("UPDATE ideias SET exclusividade='crazygames_agregadores' WHERE id=?", (i,))

    def test_trocaPorBuildNaoValeDepoisQueOTesteComecou(self):
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('poki_build_mb_max','5','seed'),('tempo_gameplay_s_max','10','seed')")
        i = self.nova(**dict(FICHA_OK, exclusividade='poki')); self.mover(i, 'em_teste')
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,inicio) VALUES(?,'W1','portal_teste','rodando',date('now'))", (i,))
        self.c.execute('UPDATE ideias SET build_mb=11 WHERE id=?', (i,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'exclusividade_travada'):
            self.c.execute("UPDATE ideias SET exclusividade='crazygames_agregadores' WHERE id=?", (i,))

    def test_topTrendingRobloxJaEhAltaObservada(self):
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('roblox','hype','Hype',date('now','-200 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista,rank_pos) VALUES(?,date('now'),'global','top-trending',1)", (cid,))
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM v_tendencia_viva').fetchone()[0], 1)

    def test_preRegistroCopiaOLimiarVigente(self):
        self.c.execute("INSERT INTO limiares(etapa,metrica,segmento,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,prazo_dias,unidade_n,"
                       "marco_inicio,sem_amostra_destino,mata_destino,versao,vigente_desde,origem) VALUES('W1','pct_jogadas_3min','poki_player_fit','taxa',0.25,0.12,500,0,7,'jogadas','m','arquivada','arquivada',1,date('now'),'benchmark')")
        i = self.nova(**FICHA_OK)
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,)).lastrowid
        ins = ("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,segmento,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,"
               "eventos_min,limiar_versao,previsao,prazo_dias) VALUES(?,?,'W1','poki_player_fit','e','pct_jogadas_3min','taxa',?,0.12,500,0,1,0.3,7)")
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'pre_registro_diverge_do_limiar'):
            self.c.execute(ins, (i, x, 0.12))
        self.c.execute(ins, (i, x, 0.25))

    def test_partyHostComCanal7NaoEntraEmTeste(self):
        i = self.nova(**dict(FICHA_OK, modo='party_host'))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))
        j = self.nova(**dict(FICHA_OK, modo='party_host', score_json='{"demanda":7,"twist":7,"canal":10,"execucao":7,"economia":4}'))
        self.assertIsNone(self.mover(j, 'em_teste'))


class LibR16(unittest.TestCase):
    def test_citacaoMultilinhaBateComOInbox(self):
        msg = 'horas da semana:\nideia#3 validacao 4h\nideia#5 construcao 3h'
        self.assertTrue(prova_existe('"horas da semana:\nideia#3 validacao 4h\nideia#5 construcao 3h" chat 27/10', [msg]))

    def test_taxaAcimaDe100ComAmostraPequenaAguarda(self):
        self.assertEqual(decidir('taxa', 14, 10, 0.16, 0.10, 300, 30, 0), 'aguardar')


if __name__ == '__main__':
    unittest.main()
