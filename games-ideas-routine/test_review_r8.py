"""Review round 8: single trend definition (new AND in a top list, not itch, expires at lancado_em + 120) and #1, #2, #7-#10."""
import sqlite3, unittest
from test_guards_v2 import Base, passar_etapas
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas
from test_review_r6 import col


def lider(c, loja, id_loja, dias, top=True):
    cid = c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES(?,?,date('now',?))", (loja, id_loja, f'-{dias} days')).lastrowid
    if top:
        c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista,rank_pos) VALUES(?,date('now','-3 days'),'global','most-played',4)", (cid,))
    else:   # round 29: a recent game needs one popularity number; this one is below every trend floor
        c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,reviews_total) VALUES(?,date('now','-3 days'),'global',10)", (cid,))
    return cid


class TendenciaR8(Base):
    def ligar(self, i, cid, papel='rival'):
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,?)", (i, cid, papel))

    def test_novoEPopularPrecisaDeRegistro(self):   # round 10: only the reference counts
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem')); self.ligar(i, lider(self.c, 'steam', 'h', 40), 'referencia')
        self.assertIn('tendencia_nao_registrada', self.mover(i, 'em_teste'))

    def test_liderRegistradoComoReferenciaExigeFonteTendencia(self):   # round 10: only the reference counts
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem')); self.ligar(i, lider(self.c, 'steam', 'h', 40), 'referencia')
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja) VALUES('h','steam','h')")
        self.assertIn('fonte_ideia_tendencia', self.mover(i, 'em_teste'))

    def test_novoSemListaNaoEhTendencia(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem')); self.ligar(i, lider(self.c, 'steam', 'r', 40, top=False), 'referencia')
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_jogoDeJamNaoEhTendencia(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem')); self.ligar(i, lider(self.c, 'itch', 'j', 10), 'referencia')
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_tendenciaExpiraNoLancamentoMais120(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem')); self.ligar(i, lider(self.c, 'steam', 'h', 130), 'referencia')
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja,status,detectada_em) VALUES('h','steam','h','fechada',date('now','-20 days'))")
        self.assertIsNone(self.mover(i, 'em_teste'))


class ChecklistTendencia(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','candidata')")

    def test_perenePromocaoNaoEhTendencia(self):
        cid = lider(self.c, 'steam', 'vs', 1500, top=False)
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,?,'referencia')", (cid,))
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,ccu) VALUES(?,date('now','-20 days'),'global',18000),(?,date('now'),'global',41000)", (cid, cid))
        self.assertEqual(col(self.c, 'q_checklist', 'tendencias_nao_registradas'), 0)

    def test_novoEPopularApareceNoChecklist(self):
        cid = lider(self.c, 'steam', 'h', 30)
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,?,'referencia')", (cid,))
        self.assertEqual(col(self.c, 'q_checklist', 'tendencias_nao_registradas'), 1)


class OutrosR8(Base):
    def test_morteDeIrmaMaisNovaNaoBloqueiaAMaisVelha(self):
        a = self.nova(genero='deck', **FICHA_OK)
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('gacha','deck')").lastrowid
        self.mover(b, 'candidata')
        self.c.execute('DROP TRIGGER trg_familia_escolha'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, b))
        self.mover(b, 'morta', motivo_morte='excluida_por_regra')
        self.assertIsNone(self.mover(a, 'em_teste'))

    def test_trilhaRAceitaModoSolo(self):
        i = self.nova(**dict(FICHA_OK, trilha='R', plataforma='roblox', modo='solo', horas_estimadas=15))
        self.assertIsNone(self.mover(i, 'em_teste'))


class QueriesR8(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def test_candidataPontuadaParadaEntraNaFila(self):
        self.c.execute("INSERT INTO config VALUES('candidata_pendente_dias','14','seed',datetime('now')),('candidata_fila_dias','60','seed',datetime('now'))")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,atualizada_em) VALUES(1,'a','candidata',31,datetime('now','-70 days')),(2,'b','candidata',31,datetime('now','-20 days'))")
        # round 14: 'sem_vaga' only when the pre_teste queue is full (4)
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(11,'p1','pre_teste'),(12,'p2','pre_teste'),(13,'p3','pre_teste'),(14,'p4','pre_teste')")
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_candidatas_paradas'])], [1])

    def test_fichaNaoCobraCongeladaDoGate(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','congelada')")
        self.assertEqual(col(self.c, 'q_checklist', 'ideias_sem_ficha'), 0)

    def test_jogoNoArCongeladoNaoExpira(self):
        self.c.execute("INSERT INTO config VALUES('congelada_max_meses','6','seed',datetime('now'))")
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','congelada')")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,em) VALUES(1,'lancada','congelada','E5','rotina',datetime('now','-300 days'))")
        self.assertEqual(self.c.execute(queries()['q_congeladas_vencidas']).fetchall(), [])

    def test_metaPortfolioEmReaisPorHora(self):
        self.c.execute("INSERT INTO config VALUES('cambio_usd_brl','5','medido',datetime('now'))")
        self.c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'a')")
        self.c.execute("INSERT INTO receita_snapshots(ideia_id,data,receita_liquida_usd,fonte) VALUES(1,date('now','start of month','-1 month'),100,'poki')")
        self.c.execute("INSERT INTO horas(ideia_id,data,horas,tipo,prova_dono) VALUES(1,date('now','start of month','-1 month'),25,'validacao','x')")
        self.assertEqual(col(self.c, 'q_meta_portfolio', 'rs_por_hora_12m'), 20.0)


if __name__ == '__main__':
    unittest.main()
