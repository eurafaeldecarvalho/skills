"""Review round 27 (decisive columns locked against rewriting, rival name with a subtitle, trend idea on the web path,
calibration of the S1 extension, prototype hours overrun)."""
import sqlite3, unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


def col(c, nome, coluna):
    cur = c.execute(queries()[nome]); cols = [d[0] for d in cur.description]
    return cur.fetchone()[cols.index(coluna)]


class TravasR27(Base):
    def test_arquivamentoNaoSeReclassifica(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste'); self.mover(i, 'arquivada', reabrir_se='x')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'arquivamento_imutavel'):
            self.c.execute("UPDATE ideias SET arquivamento='operacional' WHERE id=?", (i,))

    def test_sinalNaoSeReescreve(self):
        self.nova(**FICHA_OK)   # links one signal
        sid = self.c.execute('SELECT MIN(id) FROM sinais').fetchone()[0]
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'sinal_imutavel'):
            self.c.execute("UPDATE sinais SET tipo='jam_mecanica' WHERE id=?", (sid,))

    def test_exploracaoEmNaoMuda(self):
        i = self.nova(**FICHA_OK)
        self.c.execute("UPDATE ideias SET exploracao_em=date('now'), exploracao=1, fonte_ideia='exploracao' WHERE id=?", (i,))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'exploracao_em_imutavel'):
            self.c.execute("UPDATE ideias SET exploracao_em=date('now','-40 days') WHERE id=?", (i,))

    def test_cotaDeExploracaoLeAConfig(self):
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('exploracao_por_mes','2','seed')")
        a = self.nova(genero='a', **FICHA_OK); b = self.nova(genero='b', **FICHA_OK)
        self.c.execute("UPDATE ideias SET exploracao_em=date('now'), exploracao=1, fonte_ideia='exploracao' WHERE id=?", (a,))
        self.mover(a, 'arquivada', reabrir_se='x', arquivamento='operacional')
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(?,'candidata','em_teste','x','rotina')", (a,))
        self.c.execute("UPDATE ideias SET exploracao_em=date('now'), exploracao=1, fonte_ideia='exploracao' WHERE id=?", (b,))

    def test_aiRuntimeSoVoltaAZeroComFixFirst(self):
        i = self.nova(**dict(FICHA_OK, ai_runtime=1))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'flag_proibida_so_com_fix_first'):
            self.c.execute('UPDATE ideias SET ai_runtime=0 WHERE id=?', (i,))

    def test_planoDeModeracaoDeVerdade(self):
        i = self.nova(**dict(FICHA_OK, ai_runtime=1, plano_moderacao='x'))
        self.assertIn('excluida_por_regra', self.mover(i, 'em_teste'))

    def test_rivalComSubtituloNoTwistRecusa(self):
        i = self.nova(**dict(FICHA_OK, twist='É Hype Game, mas com arte nova, de modo que Z'))
        rid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','hy','Hype Game: Deluxe Edition','2026-01-01')").lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'rival')", (i, rid))
        self.assertIn('referencia_no_twist', self.mover(i, 'em_teste'))

    def test_ideiaDeTendenciaWebSoPelaCrazyGames(self):
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('horas_semana_dono_min','8','seed'),('tendencia_mvp_dias_max','14','seed')")
        i = self.nova(**dict(FICHA_OK, fonte_ideia='tendencia', horas_estimadas=12))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('poki','h','Hype',date('now','-20 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,plays) VALUES(?,date('now'),'global',200000)", (cid,))
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja) VALUES('h','poki','h')")
        self.assertIn('tendencia_fora_do_escopo', self.mover(i, 'em_teste'))


class QueriesR27(unittest.TestCase):
    def test_erroDePrevisaoDoS1EstendidoNaMesmaUnidade(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'s')")
        c.execute("INSERT INTO experimentos(id,ideia_id,etapa,tipo,estado) VALUES(1,1,'S1','pagina_steam','encerrado')")
        c.execute("INSERT INTO hipoteses(id,ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,"
                  "limiar_versao,previsao,prazo_dias,estendida,resultado,fechada_em,valor_observado) VALUES(1,1,1,'S1','e','wishlists_14d','contagem',201,20,14,0,1,250,14,1,'confirmada',datetime('now'),450)")
        self.assertEqual(c.execute(queries()['q_erro_previsao']).fetchall(), [('S1', 'wishlists_14d', 1, -25.0)])

    def test_horasDoPrototipoEstouradasAparecemNoChecklist(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado,horas_estimadas) VALUES(1,'a','em_teste',10)")
        c.execute("INSERT INTO horas(ideia_id,data,horas,tipo,prova_dono) VALUES(1,date('now'),60,'validacao','x')")
        self.assertEqual(col(c, 'q_checklist', 'horas_estouradas'), 1)


if __name__ == '__main__':
    unittest.main()
