"""Review round 4 (findings #1-#8, #14)."""
import sqlite3, unittest
from test_guards_v2 import Base, fechar_hipotese
from test_review_r1 import FICHA_OK
from test_review_r2 import hipotese


def jogo_lancado(c):
    """An own launched game: an idea with the owner's launch event."""
    j = c.execute("INSERT INTO ideias(titulo) VALUES('meu jogo')").lastrowid
    c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,'em_construcao','lancada','x','dono',?)", (j, f'"ideia#{j} lançada em poki em 26/10" chat'))
    return j


class GuardsR4(Base):
    def fresh_adv(self, i):
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now','+1 second') WHERE id=?", (i,))

    def exp(self, i, etapa, decisao, metrica='m'):
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,fim) VALUES(?,?,'portal_teste','encerrado',date('now'))", (i, etapa)).lastrowid
        h = self.c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,"
                           "eventos_min,limiar_versao,previsao,prazo_dias) VALUES(?,?,?,'e',?,'media',3,1.5,500,0,1,3,7)",
                           (i, x, etapa, metrica)).lastrowid
        fechar_hipotese(self.c, h, 'confirmada')
        self.c.execute("UPDATE experimentos SET decisao=? WHERE id=?", (decisao, x))

    def test_validadaExigeEtapasDaTrilhaPassadas(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste'); self.fresh_adv(i)
        self.assertIn('etapas_nao_passaram', self.mover(i, 'validada'))
        self.exp(i, 'W1', 'passa')
        self.assertIn('etapas_nao_passaram', self.mover(i, 'validada'))      # Poki path also needs W2
        self.exp(i, 'W2', 'passa')
        self.assertIsNone(self.mover(i, 'validada'))

    def test_caminhoCrazyGamesValidaSoComW1(self):
        i = self.nova(genero='idle', **dict(FICHA_OK, exclusividade='crazygames_agregadores')); self.mover(i, 'em_teste'); self.fresh_adv(i)   # round 15: direct CrazyGames needs a reason
        self.exp(i, 'W1', 'passa', metrica='aceite_plataforma')
        self.assertIsNone(self.mover(i, 'validada'))

    def test_refutadaNaoEscapaPorCongelada(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        hipotese(self.c, i, 'W1', 'refutada', estendida=1)
        self.assertIn('refutada_exige_morte', self.mover(i, 'congelada', data_reativacao='2027-01-01'))

    def test_experimentoFantasmaNaoDesligaAGuarda(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        hipotese(self.c, i, 'W1', 'refutada', estendida=1)
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,))
        self.assertIn('refutada_exige_morte', self.mover(i, 'arquivada', reabrir_se='x'))

    def test_tendenciaAntigaNaoBloqueiaParaSempre(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem'))
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('steam','7','2025-07-01')")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (i,))
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja,status,detectada_em) VALUES('hit','steam','7','fechada','2025-09-01')")
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_vinculoNaoPodeSerApagadoDepoisDoGate(self):
        i = self.nova(**FICHA_OK)
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('steam','8','2024-01-01')")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (i,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'vinculo_imutavel'):
            self.c.execute('DELETE FROM ideia_concorrentes WHERE ideia_id=?', (i,))

    def test_proprioJogoNaoContaComoTendencia(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem'))
        own = jogo_lancado(self.c)   # round 15: proprio_ideia_id points to a launched idea
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em,proprio_ideia_id) VALUES('crazygames','own',date('now','-75 days'),?)", (own,))
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (i,))
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja) VALUES('own','crazygames','own')")
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_lootBoxNaoPodeSerArquivada(self):
        i = self.nova(**dict(FICHA_OK, loot_box=1))
        self.assertIn('excluida_por_regra', self.mover(i, 'arquivada', reabrir_se='x'))

    def test_construcaoExigeAFraseExataDoDono(self):
        i = self.nova(**FICHA_OK)
        e = self.mover(i, 'em_construcao', 'dono', f'"ideia#{i} build: build_mb=3" chat', engine='p', engine_justificativa='j')
        self.assertIn('frase_do_dono', e)
        self.assertIsNone(self.mover(i, 'em_construcao', 'dono', f'"construo sem teste de comportamento a ideia#{i}" chat', engine='p', engine_justificativa='j'))

    def test_lootBoxEChatPrecisamSerDeclarados(self):
        i = self.nova(**dict(FICHA_OK, loot_box=None))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))

    def test_plataformaSocialSoNaTrilhaR(self):
        i = self.nova(**dict(FICHA_OK, modo='plataforma_social'))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))

    def test_segundoFallbackCrazyGamesRecusado(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        for _ in range(2):
            x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,)).lastrowid
            self.c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,previsao,prazo_dias) VALUES(?,?,'W1','e','aceite_plataforma','contagem',1,-1,1,1,1,1,21)", (i, x))
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,)).lastrowid
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'crazygames_uma_vez'):
            self.c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,previsao,prazo_dias) VALUES(?,?,'W1','e','aceite_plataforma','contagem',1,-1,1,1,1,1,21)", (i, x))

    def test_tabelaDePendencias(self):
        self.c.execute("INSERT INTO pendencias(texto) VALUES('pagar a taxa Steam da ideia#1')")
        self.assertEqual(self.c.execute("SELECT resolvida_em FROM pendencias").fetchone(), (None,))


if __name__ == '__main__':
    unittest.main()
