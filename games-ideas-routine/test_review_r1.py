"""Guards and queries from review round 1 (findings #1-#4, #7, #8, #11, #12, #16-#18)."""
import os, sqlite3, subprocess, sys, tempfile, unittest
from test_guards_v2 import Base, FICHA, fechar_hipotese
from test_queries import queries
from test_queries_v2 import db_sem_travas

D = os.path.dirname(os.path.abspath(__file__))
FICHA_OK = dict(FICHA, twist='É X, mas Y, de modo que Z', ai_arte_visivel=0,
                score_json='{"demanda":7,"twist":7,"canal":7,"execucao":7,"economia":4}')


class GuardsR1(Base):
    def test_flagLootBoxNaoVoltaAZeroForaDeFixFirst(self):
        i = self.nova(**dict(FICHA_OK, loot_box=1))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'flag_proibida_so_com_fix_first'):
            self.c.execute('UPDATE ideias SET loot_box=0 WHERE id=?', (i,))
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(?,'candidata','candidata','FIX-FIRST: compra direta no lugar da caixa','rotina')", (i,))
        self.c.execute('UPDATE ideias SET loot_box=0 WHERE id=?', (i,))

    def test_provaDoDonoPrecisaCitarAIdeia(self):
        i = self.nova(**FICHA_OK)
        self.mover(i, 'em_teste'); self.passar(i)
        self.assertIsNone(self.mover(i, 'validada', advogado_em=self.c.execute("SELECT datetime('now','+1 second')").fetchone()[0]))
        e = self.mover(i, 'em_construcao', 'dono', '"aprovo a construção" chat', engine='phaser', engine_justificativa='j')
        self.assertRegex(e, 'prova_sem_ideia|frase_do_dono')
        e = self.mover(i, 'em_construcao', 'dono', f'"aprovo a construção da ideia#{i}2" chat', engine='phaser', engine_justificativa='j')
        self.assertRegex(e, 'prova_sem_ideia|frase_do_dono')
        self.assertIsNone(self.mover(i, 'em_construcao', 'dono', f'"aprovo a construção da ideia#{i}" chat', engine='phaser', engine_justificativa='j'))

    def test_generoCentralEmSnakeCase(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'CHECK'):
            self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('x','Merge-Physics')")

    def test_morteDepoisDeTesteRefutadoExigeTesteReprovado(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','encerrado')", (i,)).lastrowid
        h = self.c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,previsao,prazo_dias) "
                           "VALUES(?,?,'W1','e','m','media',3,1.5,500,0,1,3,7)", (i, x)).lastrowid
        fechar_hipotese(self.c, h, 'refutada')
        self.assertIn('morte_por_teste', self.mover(i, 'morta', motivo_morte='escopo_grande', reabrir_se='x'))
        self.assertIsNone(self.mover(i, 'morta', motivo_morte='teste_reprovado'))

    def test_fichaComTwistForaDoModeloOuScoreSemEixosRecusa(self):
        i = self.nova(**dict(FICHA_OK, twist='x'))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))
        j = self.nova(genero='h', **dict(FICHA_OK, score_json='{}'))
        self.assertIn('ficha_incompleta', self.mover(j, 'em_teste'))
        k = self.nova(genero='k', **dict(FICHA_OK, ai_arte_visivel=None))
        self.assertIn('ficha_incompleta', self.mover(k, 'em_teste'))

    def test_validadaExigeAdvogadoDepoisDaEntradaEmTeste(self):
        i = self.nova(**dict(FICHA_OK, advogado_em='2000-01-01 00:00:00'))
        self.assertIsNone(self.mover(i, 'em_teste')); self.passar(i)
        self.assertIn('advogado_obrigatorio', self.mover(i, 'validada'))
        self.assertIsNone(self.mover(i, 'validada', advogado_em=self.c.execute("SELECT datetime('now','+1 second')").fetchone()[0]))

    def test_reativacaoDeCongeladaSoUmaVez(self):
        i = self.nova(**FICHA_OK)
        self.mover(i, 'congelada', data_reativacao='2026-10-26'); self.assertIsNone(self.mover(i, 'candidata'))
        self.mover(i, 'congelada', data_reativacao='2026-10-26')
        self.assertIn('reativacao_unica', self.mover(i, 'candidata'))


class QueriesR1(unittest.TestCase):
    def test_w2EmTesteNaoEOrfao(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','em_teste')")
        c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(1,'W2','portal_webfit','rodando')")
        self.assertEqual(c.execute(queries()['q_experimentos_orfaos']).fetchall(), [])

    def test_filaSteamContaDaLiberacaoDaVaga(self):
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('pre_teste_espera_dias','90','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo,trilha,estado,atualizada_em) VALUES(1,'s1','S','pre_teste',datetime('now','-200 days')),(2,'s2','S','arquivada',datetime('now'))")
        c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(2,'em_teste','arquivada','t','rotina')")
        self.assertEqual(c.execute(queries()['q_pre_teste_parado']).fetchall(), [])

    def test_checklistCobraReabrirSeDeLoopVazio(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(titulo,estado,motivo_morte) VALUES('a','morta','loop_vazio')")
        cols = [d[0] for d in c.execute(queries()['q_checklist']).description]
        row = c.execute(queries()['q_checklist']).fetchone()
        self.assertEqual(row[cols.index('mortas_sem_reabrir_se')], 1)

    def test_cotaExploracaoDoMesIgnoraArquivadaNaMesa(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(titulo,estado,exploracao,exploracao_em) VALUES('a','arquivada',1,date('now'))")
        self.assertEqual(c.execute(queries()['q_exploracao_mes']).fetchone(), (0, 0))

    def test_ccuDobrandoDeJogoAntigoNaoEhTendencia(self):   # round 8: doubling is no longer a criterion
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','candidata')")
        c.execute("INSERT INTO concorrentes(id,loja,id_loja) VALUES(1,'roblox','9')")
        c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,ccu) VALUES(1,date('now','-20 days'),'global',100),(1,date('now'),'global',250)")
        cols = [d[0] for d in c.execute(queries()['q_checklist']).description]
        row = c.execute(queries()['q_checklist']).fetchone()
        self.assertEqual(row[cols.index('tendencias_nao_registradas')], 0)


class Bootstrap(unittest.TestCase):
    def test_seedCriaAsPastasDeTrabalho(self):
        tmp = tempfile.mkdtemp()
        for f in os.listdir(D):
            if f.endswith(('.sql', '.csv', '.py')):
                with open(os.path.join(D, f), 'rb') as a, open(os.path.join(tmp, f), 'wb') as b: b.write(a.read())
        subprocess.run([sys.executable, 'seed.py', 'rotina.db'], cwd=tmp, check=True, capture_output=True)
        for p in ('backups', 'inbox/lido', 'digests', 'briefs', 'adv', 'secrets'):
            self.assertTrue(os.path.isdir(os.path.join(tmp, p)), p)


if __name__ == '__main__':
    unittest.main()
