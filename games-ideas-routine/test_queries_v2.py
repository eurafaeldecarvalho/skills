"""Queries changed after the validation round (findings #51, #52, #53/#76, #54, #55, #75)."""
import sqlite3, unittest
from test_queries import SCHEMA, queries


def db_sem_travas():
    c = sqlite3.connect(':memory:'); c.executescript(SCHEMA)
    for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
        c.execute(f'DROP TRIGGER {t}')   # these tests are about the queries, not the guards
    return c


class QueriesV2(unittest.TestCase):
    def test_familiaSugeridaOrdenaPorColunasEMenorFamilia(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,genero_central,familia_id) VALUES(1,'a','x',1),(2,'b','x',2),(3,'n','x',NULL)")
        c.execute("INSERT INTO concorrentes(id,loja,id_loja) VALUES(1,'steam','1')")
        c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(2,1,'referencia'),(3,1,'referencia')")
        rows = c.execute(queries()['q_familia_sugerida'], {'ideia_id': 3}).fetchall()
        self.assertEqual(rows[0][1], 2)            # 2 columns beats 1
        self.assertEqual(rows[0][-1], 2)           # 'colunas' is the last column

    def test_e5ContinuaQuandoIdeiaCongela(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','congelada')")
        c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(1,'E5','pos_lancamento','rodando')")
        self.assertEqual(c.execute(queries()['q_experimentos_orfaos']).fetchall(), [])

    def test_testesConcluidosNaoContaIteradoNemOrfao(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'a')")
        for d in ('passa', 'iterado', 'orfao', 'mata', 'sem_amostra'):
            c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,decisao) VALUES(1,'W1','portal_teste','encerrado',?)", (d,))
        r = c.execute(queries()['q_meta_portfolio']).fetchone()
        self.assertEqual(r[4], 2)   # round 31: sem_amostra measured no behavior (counted apart)

    def test_preTesteSteamNaoVenceEnquantoApostaSteamOcupada(self):
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('pre_teste_espera_dias','90','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo,trilha,estado,atualizada_em) VALUES(1,'s1','S','pre_teste',datetime('now','-200 days')),"
                  "(2,'s2','S','em_construcao',datetime('now')),(3,'w','W','pre_teste',datetime('now','-200 days'))")
        ids = [r[0] for r in c.execute(queries()['q_pre_teste_parado'])]
        self.assertEqual(ids, [3])

    def test_listaPublicaContaDiasComSalasEMultiploDoTamanho(self):
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('lista_publica_min_salas','5','seed',datetime('now')),('lista_publica_ccu_mult','10','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo,tamanho_sala) VALUES(1,'a',4)")
        c.execute("INSERT INTO experimentos(id,ideia_id,etapa,tipo,estado) VALUES(1,1,'E5','pos_lancamento','rodando')")
        for d in range(10):
            c.execute("INSERT INTO metricas VALUES(1,date('now',?),'salas_abertas_pico',?, 'telemetria',NULL)", (f'-{d} days', 6 if d < 8 else 2))
        for d in range(8):   # round 13: the CCU rule needs a sustained peak (> 7 of 14 days)
            c.execute("INSERT INTO metricas VALUES(1,date('now',?),'ccu_pico',45,'telemetria',NULL)", (f'-{d} days',))
        dias_ok, ccu_ok = c.execute(queries()['q_lista_publica'], {'ideia_id': 1}).fetchone()[-2:]
        self.assertEqual((dias_ok, ccu_ok), (8, 0))   # round 33: with measured rooms, CCU is not consulted (dias_ok decides)

    def test_candidatasParadasTemQueryDeAcao(self):
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('candidata_pendente_dias','14','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo,estado,atualizada_em) VALUES(1,'a','candidata',datetime('now','-20 days')),(2,'b','candidata',datetime('now'))")
        self.assertEqual([r[0] for r in c.execute(queries()['q_candidatas_paradas'])], [1])


if __name__ == '__main__':
    unittest.main()
