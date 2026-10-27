"""Review round 4: the baseline follows when the repo went public (not its creation), pronta holds the build slot,
the queues apply every build cut of the database (one view, mesa_cortes), exempt categories ignore any rate,
real build hours have their own refusal, and the seeded CLI rate is the complete measurement."""
import csv, os, re, sqlite3, unittest
from test_schema import Base, FICHA, D
from test_queries import queries, db_sem_travas, candidata
from test_review_r2 import hip


class BaselineR4(Base):
    def test_repoPrivadoCriadoHaMuitoTempoDecideSemBaseline(self):
        i = self.nova(**FICHA)
        self.c.execute("INSERT INTO repos(full_name,criado_em,proprio_ideia_id) VALUES('me/novo',date('now','-70 days'),?)", (i,))
        self.ate_lancada(i)
        self.c.execute("UPDATE repos SET publico_em=date('now') WHERE proprio_ideia_id=?", (i,))   # made public at launch (7.4)
        h = hip(self.c, i)
        for d in range(14):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(?,date('now',?),5,'stargazers_history')", (i, f'+{d} days'))
        self.c.execute("UPDATE hipoteses SET resultado='confirmada', fechada_em=datetime('now'), n_observado=14, valor_observado=70 WHERE id=?", (h,))


class SlotR4(Base):
    def test_prontaOcupaOSlotDeConstrucao(self):
        a = self.nova(**FICHA); b = self.nova(**FICHA)
        self.aprovar(a); self.checklist_ok(a); self.assertIsNone(self.mover(a, 'pronta'))
        self.assertIn('slot_ocupado', self.aprovar(b))


class GuardsR4(Base):
    def test_categoriaIsentaIgnoraTaxaMedida(self):
        b = self.c.execute("INSERT INTO benchmarks(metrica,segmento,valor,unidade,source_url,data_fonte,tipo_fonte,confianca,verificado_em) "
                           "VALUES('hit_rate_gt1000_library_ts_12m','topic_library_ts',0.0016,'fracao','u','2026-10-27','medicao_propria','alta',date('now'))").lastrowid
        i = self.nova(**dict(FICHA, categoria='lib_benchmark', hit_rate_categoria=0.0016, hit_rate_benchmark_id=b))
        self.assertIsNone(self.aprovar(i))

    def test_horasReaisFaltandoTemRecusaPropria(self):
        i = self.nova(**FICHA); self.aprovar(i); self.checklist_ok(i, horas=0)
        self.assertIn('horas_reais_insuficientes', self.mover(i, 'pronta'))


class FilasR4(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def fila(self):
        return [r[0] for r in self.c.execute(queries()['q_fila_construcao'])]

    def mesa(self):
        return [(r[0], r[-1]) for r in self.c.execute(queries()['q_mesa_reprovada'])]

    def test_nichoTomadoSaiDaFilaEVaiPraMesaReprovada(self):
        candidata(self.c, 1)
        r = self.c.execute("INSERT INTO repos(full_name,criado_em) VALUES('b/succ',date('now','-3 years'))").lastrowid
        self.c.execute("INSERT INTO repo_snapshots(repo_id,data,estrelas,pushed_at,fonte) VALUES(?,date('now'),5000,date('now','-10 days'),'gh_star_count')", (r,))
        self.c.execute("INSERT INTO ideia_repos VALUES(1,?,'sucessor')", (r,))
        self.assertEqual((self.fila(), self.mesa()), ([], [(1, 'nicho_tomado')]))

    def test_horasAcimaDoTetoSaiDaFila(self):
        candidata(self.c, 1, horas_estimadas=30)
        self.assertEqual((self.fila(), self.mesa()), ([], [(1, 'ficha_incompleta')]))

    def test_ganchoQueVendeIaSaiDaFila(self):
        candidata(self.c, 1, gancho='The AI agent that renames files')
        self.assertEqual((self.fila(), self.mesa()), ([], [(1, 'gancho_vende_ia')]))

    def test_candidataConstruivelSoNaFila(self):
        candidata(self.c, 1)
        self.assertEqual((self.fila(), self.mesa()), ([1], []))


class SeedR4(unittest.TestCase):
    def rows(self, t):
        return list(csv.DictReader(open(os.path.join(D, f'seed_{t}.csv'), encoding='utf-8')))

    def test_taxaDeCliRustComDenominadorCompleto(self):
        r = next(r for r in self.rows('benchmarks') if r['metrica'] == 'hit_rate_gt1000_cli_rust_12m')
        self.assertIn('37/10425', r['nota'])
        self.assertAlmostEqual(float(r['valor']), 37 / 10425, places=4)

    def test_taxaBateComANotaKN(self):
        for r in self.rows('benchmarks'):
            m = re.search(r'(\d+)/(\d+)', r['nota'] or '')
            if r['metrica'].startswith('hit_rate_') and m:
                with self.subTest(r['metrica']):
                    self.assertAlmostEqual(float(r['valor']), int(m[1]) / int(m[2]), delta=0.00006)

    def test_pisoDeCategoriaEPremissaDeCargaCli(self):
        cfg = {r['chave']: r for r in self.rows('config')}
        self.assertEqual(cfg['categoria_hit_min']['valor'], '0.0015')
        self.assertEqual(cfg['carga_itens_por_1k_cli']['origem'], 'premissa')


if __name__ == '__main__':
    unittest.main()
