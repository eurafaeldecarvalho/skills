"""Review round 17 (negated owner phrase, incomplete hypothesis set, build switch order, port evidence, idle on Poki)."""
import sqlite3, unittest
from lib import prova_existe
from test_guards_v2 import Base, passar_etapas, fechar_hipotese
from test_review_r1 import FICHA_OK
from test_review_r4 import jogo_lancado

LIMIAR = ("INSERT INTO limiares(etapa,metrica,segmento,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,prazo_dias,unidade_n,"
          "marco_inicio,sem_amostra_destino,mata_destino,versao,vigente_desde,origem) VALUES(?,?,?,'taxa',0.25,0.12,500,0,7,'jogadas','m','arquivada','arquivada',1,date('now'),'benchmark')")
HIP = ("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,segmento,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,"
       "eventos_min,limiar_versao,previsao,prazo_dias) VALUES(?,?,?,?,'e',?,'taxa',0.25,0.12,500,0,1,0.3,7)")


class FraseNegadaR17(Base):
    def test_negacaoDaFraseNaoAprovaConstrucao(self):
        i = self.nova(**FICHA_OK)
        self.assertIn('frase_do_dono', self.mover(i, 'em_construcao', 'dono',
                      f'"Não construo sem teste de comportamento a ideia#{i}, quero o playtest antes." chat', engine='p', engine_justificativa='j'))

    def test_negacaoNaoReabre(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'morta', motivo_morte='clone_legal')
        self.assertIn('frase_do_dono', self.mover(i, 'candidata', 'dono', f'"Não reabro a ideia#{i}." chat', motivo='REABERTA: dono'))

    def test_libExigeAFraseNoInicioDaCitacao(self):
        msg = 'Não aprovo a construção da ideia#1'
        self.assertFalse(prova_existe(f'"{msg}" chat', [msg], 1, frase='aprovo a construção da ideia#1'))
        self.assertTrue(prova_existe('"aprovo a construção da ideia#1" chat', ['ok. aprovo a construção da ideia#1'], 1, frase='aprovo a construção da ideia#1'))


class ConjuntoR17(Base):
    def setUp(self):
        super().setUp()
        for m in ('minutos_por_jogador', 'pct_jogadas_3min'):
            self.c.execute(LIMIAR, ('W1', m, 'poki_player_fit'))
        self.c.execute(LIMIAR, ('R1', 'd1', 'roblox')); self.c.execute(LIMIAR, ('R1', 'd1', 'uefn'))

    def exp(self, i, etapa):
        return self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,fim) VALUES(?,?,'portal_teste','encerrado',date('now'))", (i, etapa)).lastrowid

    def hips(self, i, x, *linhas):
        """Pre-registers every hypothesis first, then decides them (round 23: decided only by UPDATE, from data)."""
        ids = [self.c.execute(HIP, (i, x) + l).lastrowid for l in linhas]
        for h in ids:
            fechar_hipotese(self.c, h, 'confirmada')

    def test_passaExigeTodasAsMetricasDoSegmento(self):
        i = self.nova(**FICHA_OK); x = self.exp(i, 'W1')
        self.hips(i, x, ('W1', 'poki_player_fit', 'pct_jogadas_3min'))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'hipoteses_incompletas'):
            self.c.execute("UPDATE experimentos SET decisao='passa' WHERE id=?", (x,))
        x2 = self.exp(i, 'W1')   # the full set, pre-registered together
        self.hips(i, x2, ('W1', 'poki_player_fit', 'pct_jogadas_3min'), ('W1', 'poki_player_fit', 'minutos_por_jogador'))
        self.c.execute("UPDATE experimentos SET decisao='passa' WHERE id=?", (x2,))

    def test_passaNaoValeSoComMetricaInventada(self):
        i = self.nova(**FICHA_OK); x = self.exp(i, 'W1')
        self.hips(i, x, ('W1', None, 'cliques_totais'))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'hipoteses_incompletas'):
            self.c.execute("UPDATE experimentos SET decisao='passa' WHERE id=?", (x,))

    def test_segmentoDeOutraPlataformaNaoVale(self):
        i = self.nova(**dict(FICHA_OK, trilha='R', plataforma='roblox', horas_estimadas=15)); x = self.exp(i, 'R1')
        self.hips(i, x, ('R1', 'uefn', 'd1'))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'hipoteses_incompletas'):
            self.c.execute("UPDATE experimentos SET decisao='passa' WHERE id=?", (x,))


class OutrosR17(Base):
    def test_trocaPorBuildNaOrdemDoTexto(self):   # abort the planned Poki W1 first, then switch
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('poki_build_mb_max','5','seed'),('tempo_gameplay_s_max','10','seed')")
        i = self.nova(**dict(FICHA_OK, exclusividade='poki')); self.mover(i, 'em_teste')
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,)).lastrowid
        self.c.execute("UPDATE experimentos SET estado='abortado', decisao='orfao' WHERE id=?", (x,))
        self.c.execute('UPDATE ideias SET build_mb=11 WHERE id=?', (i,))
        self.c.execute("UPDATE ideias SET exclusividade='crazygames_agregadores' WHERE id=?", (i,))

    def test_portDeJogoProprioNaoPedeSinalColetado(self):
        own = jogo_lancado(self.c)
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em,proprio_ideia_id) VALUES('poki','meu','Meu','2026-01-01',?)", (own,)).lastrowid
        i = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('port','deck')").lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.mover(i, 'candidata'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (i, i))
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in FICHA_OK) + ' WHERE id=?', list(FICHA_OK.values()) + [i])
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_idleNaoVaiPeloPoki(self):
        i = self.nova(genero='clicker', **dict(FICHA_OK, exclusividade='poki'))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'idle_vai_para_crazygames'):
            self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,))
        j = self.nova(genero='clicker', **dict(FICHA_OK, exclusividade='crazygames_agregadores'))
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (j,))


if __name__ == '__main__':
    unittest.main()
