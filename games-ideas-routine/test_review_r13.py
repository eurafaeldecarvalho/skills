"""Review round 13 (findings #1, #2, #3, #4, #8, #9)."""
import sqlite3, unittest
from test_guards_v2 import Base, passar_etapas
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


class GuardsR13(Base):
    def ref(self, i, nome='Antigo', dias=900, papel='referencia'):
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam',?,?,date('now',?))", (nome, nome, f'-{dias} days')).lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,?)", (i, cid, papel))
        return cid

    def evid(self, i):
        self.c.execute("INSERT OR IGNORE INTO fontes(id,nome,plataforma,tipo,mercado,frequencia,cota_min) VALUES(99,'f','steam','t','todos','diaria',0)")
        sid = self.c.execute("INSERT INTO sinais(fonte_id,hash,url,url_status,trecho_literal,tipo,payload_json) VALUES(99,?,'u',200,?,'hit_plataforma','{\"sha256\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"date\":\"d\"}')", (f'h{i}', 'x' * 40)).lastrowid
        self.c.execute("INSERT INTO evidencias VALUES(?,?,1,1,NULL)", (i, sid))

    def test_eixoNullNaoBurlaEscala(self):
        i = self.nova(**dict(FICHA_OK, score_json='{"demanda":7,"twist":7,"canal":7,"execucao":7,"economia":null}'))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))

    def test_testeExigeReferenciaLigadaEEvidencia(self):
        i = self.nova(sem_vinculos=True, **FICHA_OK)
        self.assertIn('referencia_nao_ligada', self.mover(i, 'em_teste'))
        self.ref(i)
        self.assertIn('sem_evidencia', self.mover(i, 'em_teste'))
        self.evid(i)
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_rivalSemNomeRecusado(self):
        i = self.nova(**FICHA_OK)
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('steam','semnome','2020-01-01')").lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'rival')", (i, cid))
        self.assertIn('concorrente_sem_nome', self.mover(i, 'em_teste'))

    def test_construcaoSemTesteExigeFlagsLegais(self):
        i = self.nova(**dict(FICHA_OK, loot_box=None))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_construcao', 'dono', f'"construo sem teste de comportamento a ideia#{i}" chat', engine='p', engine_justificativa='j'))

    def test_reabertaDeNaoApagaMorteGraveDaFamilia(self):
        x = self.nova(genero='deck', **FICHA_OK)
        k = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','c','Comum','2020-01-01')").lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'rival')", (x, k))
        self.mover(x, 'em_teste'); self.mover(x, 'morta', motivo_morte='teste_reprovado')
        n = self.c.execute("INSERT INTO ideias(titulo,genero_central,reaberta_de) VALUES('n','deck',?)", (x,)).lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'rival')", (n, k))
        self.mover(n, 'candidata')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'familia_errada'):
            self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (n, n))

    def test_tendenciaVencidaNaoBloqueiaValidada(self):
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('horas_semana_dono_min','8','seed'),('tendencia_mvp_dias_max','14','seed')")
        # round 27: a web trend idea runs the CrazyGames path
        i = self.nova(**dict(FICHA_OK, fonte_ideia='tendencia', horas_estimadas=10, exclusividade='crazygames_agregadores'))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','t','TrendGame',date('now','-100 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,reviews_total) VALUES(?,date('now'),'global',5000)", (cid,))   # round 29
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja) VALUES('t','steam','t')")
        self.assertIsNone(self.mover(i, 'em_teste'))
        self.c.execute("UPDATE concorrentes SET lancado_em=date('now','-130 days') WHERE id=?", (cid,))
        from test_review_r15 import hipotese
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,fim) VALUES(?,'W1','portal_teste','encerrado',date('now'))", (i,)).lastrowid
        hipotese(self.c, i, x, 'W1', 'aceite_plataforma', 'confirmada')
        self.c.execute("UPDATE experimentos SET decisao='passa' WHERE id=?", (x,))
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now','+1 second') WHERE id=?", (i,))
        self.assertIsNone(self.mover(i, 'validada'))


class QueriesR13(unittest.TestCase):
    def test_listaPublicaExigeCcuSustentado(self):
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('lista_publica_min_salas','5','seed',datetime('now')),('lista_publica_ccu_mult','10','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo,tamanho_sala) VALUES(1,'a',4)")
        c.execute("INSERT INTO experimentos(id,ideia_id,etapa,tipo,estado) VALUES(1,1,'E5','pos_lancamento','rodando')")
        for d in range(14):
            c.execute("INSERT INTO metricas VALUES(1,date('now',?),'ccu_pico',?, 'telemetria',NULL)", (f'-{d} days', 45 if d == 0 else 3))
        self.assertEqual(c.execute(queries()['q_lista_publica'], {'ideia_id': 1}).fetchone()[-1], 0)


if __name__ == '__main__':
    unittest.main()
