"""Review round 2 (findings #1, #2, #3, #4, #6, #14, #16)."""
import sqlite3, unittest
from test_guards_v2 import fechar_hipotese, Base, ligar_referencia_e_evidencia
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas
from lib import steam_projecao


def hipotese(c, i, etapa, resultado, estendida=0, fechada_em="datetime('now')"):
    x = c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,?,'portal_teste','encerrado')", (i, etapa)).lastrowid
    h = c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,"
                  "eventos_min,limiar_versao,previsao,prazo_dias,estendida) VALUES(?,?,?,'e','m','media',3,1.5,500,0,1,3,7,?)",
                  (i, x, etapa, estendida)).lastrowid
    if resultado is not None:
        fechar_hipotese(c, h, resultado, fechada_em)   # round 23: decided only by UPDATE, from data


class GuardsR2(Base):
    def test_familiaConferidaNaEntradaDoTeste(self):
        a = self.nova(genero='merge', **FICHA_OK); self.mover(a, 'em_teste')
        self.mover(a, 'morta', motivo_morte='teste_reprovado')
        b = self.nova(genero='merge', **FICHA_OK)          # own family written before the link
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('steam','1','2023-01-01')")
        for x in (a, b): self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (x,))
        self.assertIn('familia_errada', self.mover(b, 'em_teste'))

    def test_hipoteseDecididaExigeFechadaEm(self):
        i = self.nova(**FICHA_OK)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'CHECK'):
            hipotese(self.c, i, 'W1', 'refutada', fechada_em='NULL')

    def test_w1PokiRefutadoDepoisDaIteracaoNaoArquiva(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        hipotese(self.c, i, 'W1', 'refutada', estendida=1)
        self.assertIn('refutada_exige_morte', self.mover(i, 'arquivada', reabrir_se='x'))

    def test_w1PokiRefutadoSemIteracaoPodeArquivar(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        hipotese(self.c, i, 'W1', 'refutada', estendida=0)
        self.assertIsNone(self.mover(i, 'arquivada', reabrir_se='x'))

    def test_jogoLancadoArquivadoNoE5NaoBloqueiaOPort(self):
        a = self.nova(genero='merge', **FICHA_OK); self.mover(a, 'em_teste')
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now','+1 second') WHERE id=?", (a,))
        self.passar(a); self.mover(a, 'validada')
        self.mover(a, 'em_construcao', 'dono', f'"aprovo a construção da ideia#{a}" chat', engine='phaser', engine_justificativa='j')
        self.mover(a, 'lancada', 'dono', f'"ideia#{a} lançada em poki em 26/10" chat'); self.mover(a, 'arquivada', reabrir_se='x')
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('crazygames','own','2023-01-01')")
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('port','merge')").lastrowid
        for x in (a, b): self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (x,))
        ligar_referencia_e_evidencia(self.c, b)
        self.mover(b, 'candidata'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, b))
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in FICHA_OK) + ' WHERE id=?', list(FICHA_OK.values()) + [b])
        self.assertIsNone(self.mover(b, 'em_teste'))


class QueriesR2(unittest.TestCase):
    def test_testesConcluidosNaoContaW2(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'a')")
        for e in ('W1', 'W2'):
            c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,decisao) VALUES(1,?,'portal_teste','encerrado','passa')", (e,))
        self.assertEqual(c.execute(queries()['q_meta_portfolio']).fetchone()[4], 1)

    def test_lancadoRecenteForaDeListaNaoEhTendencia(self):   # round 8: needs a top list too
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','candidata')")
        c.execute("INSERT INTO concorrentes(id,loja,id_loja,lancado_em) VALUES(1,'steam','9',date('now','-40 days'))")
        c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,ccu) VALUES(1,date('now','-20 days'),'global',80000),(1,date('now'),'global',60000)")
        cols = [d[0] for d in c.execute(queries()['q_checklist']).description]
        self.assertEqual(c.execute(queries()['q_checklist']).fetchone()[cols.index('tendencias_nao_registradas')], 0)


class LibR2(unittest.TestCase):
    def test_projecaoSemErroDePontoFlutuante(self):
        self.assertEqual(steam_projecao(90, 9.99)['copias_ano1_alto'], 63)


if __name__ == '__main__':
    unittest.main()
