"""Review round 5 (findings #1, #2/#9, #4, #6, #8, #10, #11, #12)."""
import sqlite3, unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_review_r2 import hipotese


class GuardsR5(Base):
    def test_decisaoPassaExigeHipotesesConfirmadas(self):
        i = self.nova(**FICHA_OK)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_sem_hipoteses'):
            self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,fim,decisao) VALUES(?,'W1','portal_teste','encerrado',date('now'),'passa')", (i,))

    def test_limiaresPreRegistradosImutaveis(self):
        i = self.nova(**FICHA_OK)
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','rodando')", (i,)).lastrowid
        self.c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,previsao,prazo_dias) VALUES(?,?,'W1','e','m','media',3,1.5,500,0,1,3,7)", (i, x))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'pre_registro_imutavel'):
            self.c.execute('UPDATE hipoteses SET limiar_passa=0.9')

    def test_caminhoCrazyGamesExigeW1ComAceite(self):
        i = self.nova(genero='idle', **FICHA_OK); self.mover(i, 'em_teste')   # round 15: direct CrazyGames needs a reason
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now','+1 second'), exclusividade='crazygames_agregadores' WHERE id=?", (i,))
        hipotese(self.c, i, 'W1', 'confirmada')                      # a Poki W1 (metric 'm'), not CrazyGames
        self.c.execute("UPDATE experimentos SET decisao='passa', fim=date('now')")
        self.assertIn('etapas_nao_passaram', self.mover(i, 'validada'))

    def test_exploracaoSoNaTrilhaWComSinalDeJam(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='exploracao', score_json='{"demanda":4,"twist":7,"canal":7,"execucao":7,"economia":4}'))
        self.c.execute("UPDATE ideias SET exploracao=1, exploracao_em=date('now') WHERE id=?", (i,))
        self.assertIn('exploracao_sem_jam', self.mover(i, 'em_teste'))

    def test_tendenciaSoWebOuRobloxEDentroDoTeto(self):
        i = self.nova(**dict(FICHA_OK, trilha='S', plataforma='steam', fonte_ideia='tendencia'))
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,'candidata','candidata','l','dono',?)", (i, f'"libero a aposta Steam da ideia#{i}" chat'))
        self.assertRegex(self.mover(i, 'pre_teste'), 'tendencia_fora_do_escopo|tendencia_sem_janela_aberta')

    def test_fixFirstUmaVezPorFamilia(self):
        i = self.nova(**dict(FICHA_OK, loot_box=1))
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(?,'candidata','candidata','FIX-FIRST: a','rotina')", (i,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'fix_first_uma_vez'):
            self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(?,'candidata','candidata','FIX-FIRST: b','rotina')", (i,))

    def test_advogadoNoFuturoRecusado(self):
        i = self.nova(**dict(FICHA_OK, advogado_em='2099-01-01 00:00:00'))
        self.assertIn('advogado_obrigatorio', self.mover(i, 'em_teste'))

    def test_recriadaNaoCasaComAQueSubstitui(self):
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('steam','1','2020-01-01')")
        b = self.nova(genero='g', **FICHA_OK); self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (b,))
        self.assertIsNone(self.mover(b, 'arquivada', reabrir_se=f'recriada como ideia#{b + 1}', arquivamento='operacional'))   # round 19: recreation is operational
        c = self.c.execute("INSERT INTO ideias(titulo,genero_central,reaberta_de) VALUES('c','g',?)", (b,)).lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (c,))
        self.mover(c, 'candidata')
        self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (c, c))   # must not be forced into b's family

    def test_fraseDoDonoComMaiuscula(self):
        i = self.nova(**FICHA_OK)
        self.assertIsNone(self.mover(i, 'em_construcao', 'dono', f'"Construo sem teste de comportamento a ideia#{i}" chat', engine='p', engine_justificativa='j'))

    def test_descongelarEFrase(self):
        i = self.nova(**FICHA_OK)
        self.mover(i, 'em_construcao', 'dono', f'"construo sem teste de comportamento a ideia#{i}" chat', engine='p', engine_justificativa='j')
        self.mover(i, 'congelada')
        self.assertIsNone(self.mover(i, 'em_construcao', 'dono', f'"descongelo a ideia#{i}" chat'))


if __name__ == '__main__':
    unittest.main()
