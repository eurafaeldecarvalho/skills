"""End-to-end: seeded database + lib, walking the funnel of SKILL.md sections 7 and 10."""
import os, sqlite3, subprocess, sys, tempfile, unittest
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
from lib import decidir
from test_guards_v2 import passar_etapas, ligar_referencia_e_evidencia

P = '"aprovo a construção da ideia#{}" chat 26/10 21:00'


class Funil(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        db = os.path.join(self.tmp, 'rotina.db')
        subprocess.run([sys.executable, 'seed.py', db], cwd=D, check=True, capture_output=True)
        self.c = sqlite3.connect(db); self.c.execute('PRAGMA foreign_keys=ON')
        # the suite pins the profile values its fixtures depend on: adapting seed_config.csv (How to use, 4) never breaks it
        for chave, valor in (('prototipo_horas_max_w', '30'), ('prototipo_horas_max_s', '50'), ('prototipo_horas_max_m', '30'),
                             ('prototipo_horas_max_r', '20'), ('s1_passa_estendido', '402')):
            self.c.execute('UPDATE config SET valor=? WHERE chave=?', (valor, chave))

    def nova(self, titulo, genero, trilha):
        cur = self.c.execute("INSERT INTO ideias(titulo,genero_central,trilha,hook,twist,modo,plataforma,horas_estimadas,score_json,advogado_em,ai_arte_visivel,loot_box,chat_livre,ai_runtime,loop_idle) "
                             "VALUES(?,?,?,'h','É X, mas Y, de modo que Z','solo','web',25,'{\"demanda\":7,\"twist\":7,\"canal\":7,\"execucao\":7,\"economia\":4}','2026-10-26 10:00:00',0,0,0,0,0)", (titulo, genero, trilha))
        i = cur.lastrowid
        ligar_referencia_e_evidencia(self.c, i)
        self.mover(i, 'candidata')
        self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (i, i))
        return i

    def mover(self, i, para, ator='rotina', prova=None, motivo='t', **cols):
        de = self.c.execute('SELECT estado FROM ideias WHERE id=?', (i,)).fetchone()[0]
        try:
            self.c.execute('SAVEPOINT s')
            self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,?,?,?,?,?)",
                           (i, de, para, motivo, ator, prova))
            if para == 'arquivada': cols.setdefault('arquivamento', 'resultado')
            sets = ', '.join([f'{k}=?' for k in cols] + ['estado=?'])
            self.c.execute(f'UPDATE ideias SET {sets} WHERE id=?', list(cols.values()) + [para, i])
            self.c.execute('RELEASE s'); return None
        except sqlite3.IntegrityError as e:
            self.c.execute('ROLLBACK TO s'); self.c.execute('RELEASE s'); return str(e)

    def limiar(self, etapa, metrica, segmento):
        return self.c.execute("SELECT tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min FROM limiares "
                              "WHERE etapa=? AND metrica=? AND segmento=?", (etapa, metrica, segmento)).fetchone()

    def decide(self, etapa, metrica, segmento, eventos, n, estendida=0, prazo=False, passa_estendido=None):
        t, lp, lm, nmin, emin = self.limiar(etapa, metrica, segmento)
        return decidir(t, eventos, n, lp, lm, nmin, emin, estendida, prazo, passa_estendido)

    # --- W, Poki path ---
    def test_pokiPlayerFitAcimaDe3MinPassa(self):
        self.assertEqual(self.decide('W1', 'minutos_por_jogador', 'poki_player_fit', 3.4 * 500, 500), 'passa')
        self.assertEqual(self.decide('W1', 'pct_jogadas_3min', 'poki_player_fit', 140, 500), 'passa')

    def test_pokiPlayerFitNoMeioItera_eDepoisMataQuandoOTesteAcaba(self):
        self.assertEqual(self.decide('W1', 'minutos_por_jogador', 'poki_player_fit', 2.4 * 500, 500), 'estender')
        # new experiment after the iteration, estendida=1, platform reports the test finished
        self.assertEqual(self.decide('W1', 'minutos_por_jogador', 'poki_player_fit', 2.6 * 500, 500, 1, True), 'mata')

    def test_webfitComDuasNotasIteraEComTresPassa(self):
        self.assertEqual(self.decide('W2', 'webfit_notas_ok', 'poki_webfit', 2, 9800), 'estender')
        self.assertEqual(self.decide('W2', 'webfit_notas_ok', 'poki_webfit', 3, 9800, 1, True, passa_estendido=3), 'passa')

    def test_recusaPokiMataW2(self):
        self.assertEqual(self.decide('W2', 'aceite_plataforma', 'poki_webfit', 0, 1), 'mata')

    def test_crazygamesPrimeiraRecusaIteraSegundaMata(self):
        self.assertEqual(self.decide('W1', 'aceite_plataforma', 'crazygames_basic', 0, 1), 'estender')
        self.assertEqual(self.decide('W1', 'aceite_plataforma', 'crazygames_basic', 0, 1, 1, True, passa_estendido=1), 'mata')
        self.assertEqual(self.decide('W1', 'aceite_plataforma', 'crazygames_basic', 1, 1), 'passa')

    def test_semDecisaoDoPortalAguarda(self):
        self.assertEqual(self.decide('W1', 'aceite_plataforma', 'crazygames_basic', 0, 0), 'aguardar')

    # --- S ---
    def test_paginaSteamFaixasZukowski(self):
        self.assertEqual(self.decide('S1', 'wishlists_14d', '*', 250, 14), 'passa')
        self.assertEqual(self.decide('S1', 'wishlists_14d', '*', 15, 14), 'mata')
        self.assertEqual(self.decide('S1', 'wishlists_14d', '*', 120, 14), 'estender')
        self.assertEqual(self.decide('S1', 'wishlists_14d', '*', 120, 10), 'aguardar')
        ext = int(self.c.execute("SELECT valor FROM config WHERE chave='s1_passa_estendido'").fetchone()[0])
        # round 17: the extension keeps the first-round velocity (2 x 201 in 28 days), it does not loosen it
        self.assertEqual(self.decide('S1', 'wishlists_14d', '*', 410, 28, 1, False, ext), 'passa')
        self.assertEqual(self.decide('S1', 'wishlists_14d', '*', 310, 28, 1, False, ext), 'mata')

    def test_demoConversao(self):
        self.assertEqual(self.decide('S2', 'demo_conversao', '*', 75, 300), 'passa')   # 25%
        self.assertEqual(self.decide('S2', 'demo_conversao', '*', 18, 300), 'mata')    # 6%
        self.assertEqual(self.decide('S2', 'demo_conversao', '*', 50, 200), 'aguardar')

    # --- M ---
    def test_cpiProprioTeto(self):
        self.assertEqual(self.decide('M1', 'cpi_usd', 'proprio', 0.33 * 200, 200), 'passa')
        self.assertEqual(self.decide('M1', 'cpi_usd', 'proprio', 0.95 * 90, 90), 'mata')

    # --- state machine with the seeded database ---
    def test_caminhoWebCompletoAteLancada(self):
        i = self.nova('merge roguelite', 'merge', 'W')
        self.assertIsNone(self.mover(i, 'em_teste'))
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now','+1 second') WHERE id=?", (i,))
        passar_etapas(self.c, i)
        self.assertIsNone(self.mover(i, 'validada'))
        self.assertIn('engine_obrigatoria', self.mover(i, 'em_construcao', 'dono', P.format(i)))
        self.assertIsNone(self.mover(i, 'em_construcao', 'dono', P.format(i), engine='phaser@4.2.1',
                                     engine_justificativa='2D, phone-first, ~2 MB build'))
        self.assertIn('lista_publica_so_com_jogo_lancado', self.erro("UPDATE ideias SET lista_publica=1 WHERE id=?", i))
        self.assertIsNone(self.mover(i, 'lancada', 'dono', f'"ideia#{i} lançada em poki em 26/10" chat'))
        self.assertIsNone(self.erro("UPDATE ideias SET lista_publica=1 WHERE id=?", i))

    def test_segundaApostaSteamBarradaEPassaQuandoAPrimeiraArquiva(self):
        a = self.nova('roguelite deck', 'deckbuilder', 'S'); b = self.nova('colony', 'colony_sim', 'S')
        for x in (a, b):
            self.c.execute("UPDATE ideias SET plataforma='steam' WHERE id=?", (x,))
            self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,'candidata','candidata','liberação','dono',?)",
                           (x, f'"libero a aposta Steam da ideia#{x}" chat'))
        self.mover(a, 'pre_teste'); self.assertIsNone(self.mover(a, 'em_teste'))
        self.mover(b, 'pre_teste'); self.assertIn('uma_aposta_steam', self.mover(b, 'em_teste'))
        self.assertIn('trilha_imutavel', self.erro("UPDATE ideias SET trilha='W' WHERE id=?", b))
        self.mover(a, 'arquivada', reabrir_se='x')
        self.assertIsNone(self.mover(b, 'em_teste'))

    def test_familiaComMorteGraveExigeReaberturaDoDono(self):
        a = self.nova('suika twist', 'merge_physics', 'W')
        self.mover(a, 'em_teste'); self.mover(a, 'morta', motivo_morte='teste_reprovado')
        # same genre + shared competitor = 2 of 3 columns -> must inherit the dead idea's family
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('steam','1','2023-01-01')")
        c2 = self.c.execute("INSERT INTO ideias(titulo,genero_central,trilha,hook,twist,modo,plataforma,horas_estimadas,score_json,advogado_em,ai_arte_visivel,loot_box,chat_livre,ai_runtime,loop_idle) "
                            "VALUES('suika 3','merge_physics','W','h','É X, mas Y, de modo que Z','solo','web',25,'{\"demanda\":7,\"twist\":7,\"canal\":7,\"execucao\":7,\"economia\":4}','2026-10-26 10:00:00',0,0,0,0,0)").lastrowid
        ligar_referencia_e_evidencia(self.c, c2)
        self.mover(c2, 'candidata')
        for x in (a, c2): self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (x,))
        self.assertIn('familia_errada', self.erro('UPDATE ideias SET familia_id=? WHERE id=?', c2, c2))
        self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, c2))
        self.assertIn('familia_no_cemiterio', self.mover(c2, 'em_teste'))
        # section 10.2: the entry event itself is the owner's REABERTA
        self.assertIsNone(self.mover(c2, 'em_teste', 'dono', f'"reabro a ideia#{c2}" chat', motivo='REABERTA: dono aprovou'))   # round 15: exact phrase

    def test_lootBoxEChatLivreSoPodemMorrer(self):
        i = self.nova('gacha jovem', 'gacha', 'W')
        self.c.execute('UPDATE ideias SET loot_box=1 WHERE id=?', (i,))
        self.assertIn('excluida_por_regra', self.mover(i, 'em_teste'))
        self.assertIsNone(self.mover(i, 'morta', motivo_morte='excluida_por_regra'))
        j = self.nova('chat aberto', 'social', 'W')
        self.c.execute('UPDATE ideias SET chat_livre=1 WHERE id=?', (j,))
        self.assertIn('excluida_por_regra', self.mover(j, 'pre_teste'))

    def erro(self, sql, *args):
        try:
            self.c.execute(sql, args); return None
        except sqlite3.IntegrityError as e:
            return str(e)


if __name__ == '__main__':
    unittest.main()
