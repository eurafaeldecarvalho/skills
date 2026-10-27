"""Review round 15 (findings A1, A3, A4, B1, B4, B5, B6/B8, B7, B9, B11)."""
import sqlite3, unittest
from test_guards_v2 import Base, fechar_hipotese
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas

PAYLOAD_OK = '{"sha256":"' + 'a' * 64 + '","date":"Mon, 26 Oct 2026 10:00:00 GMT"}'


def hipotese(c, i, x, etapa, metrica, resultado, estendida=0):
    h = c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,"
                  "eventos_min,limiar_versao,previsao,prazo_dias,estendida) VALUES(?,?,?,'e',?,'taxa',1,0,1,0,1,1,7,?)",
                  (i, x, etapa, metrica, estendida)).lastrowid
    if resultado is not None:
        fechar_hipotese(c, h, resultado)   # round 23: decided only by UPDATE, from data


class GuardsR15(Base):
    def test_recusaPokiSuperadaPeloCrazyGamesNaoObrigaTesteReprovado(self):   # A1
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        x1 = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,fim) VALUES(?,'W2','portal_webfit','encerrado',date('now'))", (i,)).lastrowid
        hipotese(self.c, i, x1, 'W2', 'aceite_plataforma', 'refutada')
        x2 = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,fim) VALUES(?,'W1','portal_teste','encerrado',date('now'))", (i,)).lastrowid
        hipotese(self.c, i, x2, 'W1', 'aceite_plataforma', 'confirmada')
        self.assertIsNone(self.mover(i, 'morta', motivo_morte='mercado_saturado'))

    def test_reabertaDoDonoValeParaAsDuasEntradasDaIrma(self):   # A4
        a = self.nova(genero='deck', **FICHA_OK); self.mover(a, 'em_teste'); self.mover(a, 'morta', motivo_morte='teste_reprovado')
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('b','deck')").lastrowid
        from test_guards_v2 import ligar_referencia_e_evidencia
        ligar_referencia_e_evidencia(self.c, b); self.mover(b, 'candidata')
        self.c.execute('DROP TRIGGER trg_familia_escolha'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, b))
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in FICHA_OK) + ' WHERE id=?', list(FICHA_OK.values()) + [b])
        self.assertIsNone(self.mover(b, 'pre_teste', 'dono', f'"reabro a ideia#{b}" chat', motivo='REABERTA: dono aprovou'))
        self.assertIsNone(self.mover(b, 'em_teste'))

    def test_flagProibidaNaoSomePorNull(self):   # B1
        i = self.nova(**dict(FICHA_OK, loot_box=1))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'flag_proibida_so_com_fix_first'):
            self.c.execute('UPDATE ideias SET loot_box=NULL WHERE id=?', (i,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'flag_proibida_so_com_fix_first'):
            self.c.execute('UPDATE ideias SET chat_livre=1 WHERE id=?', (i,)); self.c.execute('UPDATE ideias SET chat_livre=NULL WHERE id=?', (i,))

    def test_sinal200ExigePayloadComHashEData(self):   # B4
        self.c.execute("INSERT INTO fontes(id,nome,plataforma,tipo,mercado,frequencia,cota_min) VALUES(1,'a','steam','t','todos','diaria',0)")
        for ruim in ('', 'x', '{}', '{"sha256":"abc","date":"d"}'):
            with self.assertRaises(sqlite3.IntegrityError, msg=ruim):
                self.c.execute("INSERT INTO sinais(fonte_id,hash,url,url_status,trecho_literal,tipo,payload_json) VALUES(1,?,'u',200,?,'hit_plataforma',?)", ('h' + ruim, 'x' * 40, ruim))
        self.c.execute("INSERT INTO sinais(fonte_id,hash,url,url_status,trecho_literal,tipo,payload_json) VALUES(1,'ok','u',200,?,'hit_plataforma',?)", ('x' * 40, PAYLOAD_OK))

    def test_jogoProprioSoParaIdeiaLancadaEImutavel(self):   # B5
        i = self.nova(**FICHA_OK)
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('steam','hype',date('now','-30 days'))").lastrowid
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'proprio_so_de_ideia_lancada'):
            self.c.execute('UPDATE concorrentes SET proprio_ideia_id=? WHERE id=?', (i, cid))

    def test_reaberturaPeloDonoExigeFrase(self):   # B8
        i = self.nova(**FICHA_OK); self.mover(i, 'morta', motivo_morte='clone_legal')
        self.assertIn('frase_do_dono', self.mover(i, 'candidata', 'dono', f'"como está a ideia#{i}?" chat', motivo='REABERTA: dono'))
        self.assertIsNone(self.mover(i, 'candidata', 'dono', f'"reabro a ideia#{i}" chat 27/10', motivo='REABERTA: dono'))

    def test_crazygamesDiretoSoComMotivoMedido(self):   # B7
        i = self.nova(**dict(FICHA_OK, exclusividade='crazygames_agregadores', build_mb=1.2, tempo_gameplay_s=4))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'crazygames_direto_sem_motivo'):
            self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,))
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('poki_build_mb_max','5','seed'),('tempo_gameplay_s_max','10','seed')")
        self.c.execute('UPDATE ideias SET build_mb=9 WHERE id=?', (i,))
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,))

    def test_hipoteseNaoNasceDepoisDasMetricas(self):   # B9
        i = self.nova(**FICHA_OK)
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,inicio) VALUES(?,'W1','portal_teste','rodando',date('now'))", (i,)).lastrowid
        self.c.execute("INSERT INTO metricas(experimento_id,data,metrica,valor,fonte) VALUES(?,date('now'),'plays',500,'portal_dashboard')", (x,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'hipotese_depois_dos_dados'):
            hipotese(self.c, i, x, 'W1', 'pct_jogadas_3min', None)

    def test_gateDaPlataformaNaoRecalibraECalibracaoNaoAfrouxa(self):   # B11
        base = ("INSERT INTO limiares(etapa,metrica,segmento,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,prazo_dias,unidade_n,"
                "marco_inicio,sem_amostra_destino,mata_destino,versao,vigente_desde,origem) VALUES(?,?,?,?,?,?,1,0,7,'u','m','arquivada','arquivada',?,date('now'),?)")
        self.c.execute(base, ('W1', 'minutos_por_jogador', 'poki_player_fit', 'media', 3, 2, 1, 'benchmark'))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'limiar_recalibracao_proibida'):
            self.c.execute(base, ('W1', 'minutos_por_jogador', 'poki_player_fit', 'media', 0.5, 0.2, 2, 'calibrado'))
        self.c.execute(base, ('S1', 'wishlists_14d', '*', 'contagem', 200, 30, 1, 'heuristica'))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'limiar_recalibracao_proibida'):
            self.c.execute(base, ('S1', 'wishlists_14d', '*', 'contagem', 150, 30, 2, 'calibrado'))
        self.c.execute(base, ('S1', 'wishlists_14d', '*', 'contagem', 260, 30, 2, 'calibrado'))
        self.c.execute(base, ('M1', 'cpi_usd', 'proprio', 'teto', 0.4, 0.9, 1, 'heuristica'))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'limiar_recalibracao_proibida'):
            self.c.execute(base, ('M1', 'cpi_usd', 'proprio', 'teto', 0.6, 0.9, 2, 'calibrado'))


class QueriesR15(unittest.TestCase):
    def test_extratoDeUmaPlataformaFaltandoAguarda(self):   # A3
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('e5_d60_min_usd','5','seed',datetime('now')),('e5_d120_min_usd','10','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','lancada')")
        c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,em) VALUES(1,'em_construcao','lancada','x','dono',datetime('now','-130 days'))")
        c.execute("INSERT INTO receita_snapshots(ideia_id,data,receita_liquida_usd,fonte) VALUES(1,date('now','start of month','-2 months'),4,'crazygames'),"
                  "(1,date('now','start of month','-2 months'),20,'publisher'),(1,date('now','start of month','-1 month'),4,'crazygames')")
        self.assertEqual([r[-1] for r in c.execute(queries()['q_e5_escada'])], ['aguardar_extrato'])


if __name__ == '__main__':
    unittest.main()
