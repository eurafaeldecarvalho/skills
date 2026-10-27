"""Review round 31 (Roblox cumulative visits are not popularity, arbitrage signal is not a proof platform, public list
window, concluded tests, trend label after validada, UEFN null readings)."""
import sqlite3, unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


def col(c, nome, coluna, params=None):
    cur = c.execute(queries()[nome], params or {}); cols = [d[0] for d in cur.description]
    return cur.fetchone()[cols.index(coluna)]


class GuardsR31(Base):
    def test_visitasAcumuladasDoRobloxNaoFazemTendencia(self):
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('roblox','222','Modesto',date('now','-200 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,ccu,plays,favoritos) VALUES(?,date('now','-90 days'),'global',120,50000,900)", (cid,))
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,ccu,plays,favoritos) VALUES(?,date('now','-5 days'),'global',300,150000,2500)", (cid,))
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM v_tendencia_detectada').fetchone()[0], 0)

    def test_rotuloDeTendenciaVoltaDepoisDeValidada(self):
        i = self.nova(sem_vinculos=True, **dict(FICHA_OK, fonte_ideia='tendencia'))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','h','Hype',date('now','-130 days'))").lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(?,'candidata','em_teste','x','rotina')", (i,))
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(?,'em_teste','validada','x','rotina')", (i,))
        self.c.execute('DROP TRIGGER trg_evento'); self.c.execute('DROP TRIGGER trg_transicao_valida'); self.c.execute('DROP TRIGGER trg_ficha_antes_do_teste')
        self.c.execute('DROP TRIGGER trg_validada_exige_etapas')
        self.c.execute("UPDATE ideias SET estado='validada' WHERE id=?", (i,))
        self.c.execute("UPDATE ideias SET fonte_ideia='arbitragem' WHERE id=?", (i,))


class QueriesR31(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def test_sinalDeArbitragemNaoContaComoPlataformaDeProva(self):
        self.c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'i')")
        self.c.execute("INSERT INTO fontes(id,nome,plataforma,tipo,mercado,frequencia,cota_min) VALUES(1,'a','steam','t','todos','diaria',0),(2,'b','poki','t','todos','diaria',0)")
        for k, (f, t) in enumerate([(1, 'hit_plataforma'), (2, 'arbitragem')], start=1):
            self.c.execute("INSERT INTO sinais(id,fonte_id,hash,url,url_status,trecho_literal,tipo,payload_json) VALUES(?,?,?,'u',200,?,?,?)",
                           (k, f, f'h{k}', 'x' * 40, t, '{"sha256":"' + 'a' * 64 + '","date":"d"}'))
            self.c.execute("INSERT INTO evidencias VALUES(1,?,1,1,NULL)", (k,))
        self.assertEqual(col(self.c, 'q_fontes_distintas_por_ideia', 'plataformas'), 1)
        self.assertEqual(col(self.c, 'q_fontes_distintas_por_ideia', 'plataformas_arbitragem'), 1)

    def test_listaPublicaContaSoOs14Dias(self):
        self.c.execute("INSERT INTO config VALUES('lista_publica_ccu_mult','2','seed',datetime('now')),('lista_publica_min_salas','5','seed',datetime('now'))")
        self.c.execute("INSERT INTO ideias(id,titulo,tamanho_sala) VALUES(1,'a',4)")
        self.c.execute("INSERT INTO experimentos(id,ideia_id,etapa,tipo,estado) VALUES(1,1,'E5','pos_lancamento','rodando')")
        for d in range(7, 15):
            self.c.execute("INSERT INTO metricas(experimento_id,data,metrica,valor,fonte) VALUES(1,date('now',?),'salas_abertas_pico',6,'telemetria')", (f'-{d} days',))
        self.assertEqual(col(self.c, 'q_lista_publica', 'dias_salas_ok', {'ideia_id': 1}), 7)

    def test_semAmostraNaoContaComoTesteConcluido(self):
        self.c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'a')")
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,decisao) VALUES(1,'R1','roblox_mvp','encerrado','sem_amostra')")
        self.assertEqual(col(self.c, 'q_meta_portfolio', 'testes_concluidos'), 0)
        self.assertEqual(col(self.c, 'q_meta_portfolio', 'testes_sem_amostra'), 1)

    def test_r1UefnSemLeituraNaoReprovaChecklist(self):
        self.c.execute("INSERT INTO ideias(id,titulo,plataforma) VALUES(1,'a','uefn')")
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,inicio) VALUES(1,'R1','roblox_mvp','rodando',date('now','-8 days'))")
        self.assertEqual(col(self.c, 'q_checklist', 'experimentos_sem_leitura_7d'), 0)


if __name__ == '__main__':
    unittest.main()
