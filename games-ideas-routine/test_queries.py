import re, sqlite3, unittest, os
D = os.path.dirname(os.path.abspath(__file__))
SCHEMA = open(os.path.join(D, 'schema.sql')).read()
QUERIES = open(os.path.join(D, 'queries.sql')).read()

def queries():
    partes = re.split(r'^-- name: (\w+).*$', QUERIES, flags=re.M)
    return {partes[i]: partes[i + 1].strip() for i in range(1, len(partes), 2)}

class Queries(unittest.TestCase):
    def test_todasAsQueriesExecutamNoSchema(self):
        c = sqlite3.connect(':memory:'); c.executescript(SCHEMA)
        params = {'ideia_id': 1, 'experimento_id': 1, 'familia_id': 1, 'tag': 'Roguelike', 'concorrente_id': 1, 'cambio': 5.4}
        for nome, sql in queries().items():
            with self.subTest(nome=nome):
                c.execute(sql, {k: v for k, v in params.items() if ':' + k in sql}).fetchall()

    def test_horasAceitaTipoMarketing(self):
        c = sqlite3.connect(':memory:'); c.executescript(SCHEMA)
        c.execute("INSERT INTO ideias(titulo) VALUES('i')")
        c.execute("INSERT INTO horas(ideia_id,data,horas,tipo,prova_dono) VALUES(1,'2026-10-26',2,'marketing','\"2h clipe ideia#1\" 26/10')")

    def test_metaPortfolioContaMesesComSomaDoPortfolio(self):
        c = sqlite3.connect(':memory:'); c.executescript(SCHEMA)
        c.execute("INSERT INTO config(chave,valor,origem) VALUES('meta_mensal_usd','110','seed')")
        for t in ('a', 'b'): c.execute("INSERT INTO ideias(titulo) VALUES(?)", (t,))
        c.execute("INSERT INTO receita_snapshots(ideia_id,data,receita_liquida_usd,fonte) VALUES(1,date('now','start of month'),60,'crazygames')")
        c.execute("INSERT INTO receita_snapshots(ideia_id,data,receita_liquida_usd,fonte) VALUES(2,date('now','start of month'),55,'poki')")
        self.assertEqual(c.execute(queries()['q_meta_portfolio']).fetchone()[2], 1)

    def test_construcaoLongaUsaLimiteDeSemanasDaTrilha(self):
        c = sqlite3.connect(':memory:'); c.executescript(SCHEMA)
        for k, v in [('construcao_horas_max_w', '15'), ('construcao_max_semanas_w', '4'), ('construcao_horas_max_s', '250'), ('construcao_max_semanas_s', '36')]:
            c.execute("INSERT INTO config(chave,valor,origem) VALUES(?,?,'seed')", (k, v))
        for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            c.execute(f'DROP TRIGGER {t}')   # this test is about the query, not the guards
        for i, t in [(1, 'W'), (2, 'S')]:
            c.execute("INSERT INTO ideias(titulo,trilha,estado) VALUES(?,?,'em_construcao')", (f'i{i}', t))
            c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono,em) VALUES(?,'validada','em_construcao','t','dono','x ideia#1 26/10',datetime('now','-50 days'))", (i,))
        ids = [r[0] for r in c.execute(queries()['q_construcao_longa'])]
        self.assertEqual(ids, [1])

if __name__ == '__main__': unittest.main()
