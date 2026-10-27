"""queries.sql: every named query parses on the schema and answers its decision."""
import os, re, sqlite3, unittest

D = os.path.dirname(os.path.abspath(__file__))


def queries():
    txt = open(os.path.join(D, 'queries.sql'), encoding='utf-8').read()
    out = {}
    for bloco in re.split(r'(?m)^-- name: ', txt)[1:]:
        nome = bloco.split()[0]
        corpo = '\n'.join(l for l in bloco.split('\n')[1:] if not l.lstrip().startswith('--')).strip()
        out[nome] = corpo
    return out


def db_sem_travas():
    """The schema without triggers (fixtures write any state directly) plus the seeded config."""
    sql = open(os.path.join(D, 'schema.sql'), encoding='utf-8').read()
    # keep only the triggers that fill derived columns (the launch/hypothesis cycle)
    sql = re.sub(r'CREATE TRIGGER (?!trg_lancamento_ciclo|trg_hipotese_ciclo).*?END;', '', sql, flags=re.S)
    c = sqlite3.connect(':memory:'); c.executescript(sql)
    import csv
    for r in csv.DictReader(open(os.path.join(D, 'seed_config.csv'), encoding='utf-8')):
        c.execute('INSERT INTO config(chave,valor,origem) VALUES(?,?,?)', (r['chave'], r['valor'], r['origem']))
    return c


def candidata(c, i, **cols):
    """A finished desk (complete sheet + advocate) with an old, active rival: buildable unless cols say otherwise."""
    f = dict(titulo=f't{i}', estado='candidata', categoria='cli', gancho='finds which process holds a port', prova_numero='3x',
             linguagem='Go', horas_estimadas=12, estrelas_alvo=1000, carga_h_semana=0.3, hit_rate_categoria=0.0113,
             licenca='MIT', modo_baixa_manutencao=0, como_chega='Show HN + the issue thread')
    f.update(cols)
    c.execute("INSERT OR IGNORE INTO benchmarks(id,metrica,segmento,valor,unidade,source_url,data_fonte,tipo_fonte,confianca,verificado_em) "
              "VALUES(1,'m','s',0.0113,'fracao','u','2026','medicao_propria','alta',date('now'))")
    if f.get('hit_rate_categoria') is not None and 'hit_rate_benchmark_id' not in cols:
        b = c.execute("INSERT INTO benchmarks(metrica,segmento,valor,unidade,source_url,data_fonte,tipo_fonte,confianca,verificado_em) "
                      "VALUES('m',?,?,'fracao','u','2026','medicao_propria','alta',date('now'))", (f'seg{i}', f['hit_rate_categoria'])).lastrowid
        f['hit_rate_benchmark_id'] = b
    ks = ['id'] + list(f) + ['advogado_em']
    c.execute(f"INSERT INTO ideias({','.join(ks)}) VALUES({','.join('?' * (len(ks) - 1))},datetime('now'))", [i] + list(f.values()))
    r = c.execute("INSERT INTO repos(full_name,criado_em) VALUES(?,date('now','-5 years'))", (f'old/rival{i}',)).lastrowid
    c.execute("INSERT INTO repo_snapshots(repo_id,data,estrelas,pushed_at,fonte) VALUES(?,date('now'),900,date('now','-3 days'),'gh_star_count')", (r,))
    c.execute("INSERT INTO ideia_repos VALUES(?,?,'rival')", (i, r))


def linha(c, nome, params=None):
    cur = c.execute(queries()[nome], params or {}); cols = [d[0] for d in cur.description]
    r = cur.fetchone()
    return dict(zip(cols, r)) if r else None


def lancar(c, i, canal='show_hn', dias=20):
    c.execute("INSERT INTO lancamentos(ideia_id,canal,url,titulo,postado_em,prova_dono) VALUES(?,?,?,?,datetime('now',?),'\"lancei\" chat x')",
              (i, canal, f'u{i}{canal}', 't', f'-{dias} days'))


class Todas(unittest.TestCase):
    def test_todasAsQueriesExecutam(self):
        c = db_sem_travas()
        for nome, sql in queries().items():
            with self.subTest(nome=nome):
                c.execute(sql, {'ideia_id': 1}).fetchall()

    def test_checklistVazioZerado(self):
        c = db_sem_travas()
        r = linha(c, 'q_checklist')
        self.assertTrue(r and all(v == 0 for v in r.values()), r)


class Janela(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','lancada')")
        lancar(self.c, 1, dias=20)
        for d in range(0, 21):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(1,date('now',?),2,'stargazers_history')", (f'-{d} days',))

    def test_janelasContamDoPrimeiroLancamento(self):
        r = linha(self.c, 'q_janela', {'ideia_id': 1})
        self.assertEqual((r['e7'], r['e14'], r['canais']), (14, 28, 1))
        self.assertEqual(r['dias_desde_lancamento'], 20)

    def test_estrelasAntesDoLancamentoNaoContam(self):
        self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(1,date('now','-40 days'),500,'stargazers_history')")
        self.assertEqual(linha(self.c, 'q_janela', {'ideia_id': 1})['e30'], 42)


class Hipoteses(unittest.TestCase):
    def test_prazoComCarenciaContaDoPrimeiroLancamento(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','lancada')")
        lancar(c, 1, dias=16)
        c.execute("INSERT INTO hipoteses(ideia_id,etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,prazo_dias) "
                  "VALUES(1,'S1','e14','contagem',10,2,14,0,1,14)")
        r = linha(c, 'q_hipoteses_abertas')
        self.assertEqual((r['dias_cobertos'], r['prazo_esgotado']), (14, 0))   # capped at the window; 14 + 3 grace days
        c.execute("UPDATE lancamentos SET postado_em=datetime('now','-18 days')")
        self.assertEqual(linha(c, 'q_hipoteses_abertas')['prazo_esgotado'], 1)


class Fila(unittest.TestCase):
    def test_filaDeConstrucaoOrdenaPorTaxaDaCategoria(self):
        c = db_sem_travas()
        # round 4: complete desks (the queue applies every build cut of the database)
        candidata(c, 1, hit_rate_categoria=0.006, horas_estimadas=10)
        candidata(c, 2, hit_rate_categoria=0.0113, horas_estimadas=15)
        candidata(c, 3, hit_rate_categoria=0.0113, horas_estimadas=8)
        self.assertEqual([r[0] for r in c.execute(queries()['q_fila_construcao'])], [3, 2, 1])

    def test_sinaisECandidatasParados(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado,criada_em,atualizada_em) VALUES(1,'a','sinal',datetime('now','-40 days'),datetime('now','-40 days')),"
                  "(2,'b','candidata',datetime('now','-20 days'),datetime('now','-20 days')),(3,'c','candidata',datetime('now','-2 days'),datetime('now','-2 days'))")
        self.assertEqual([r[0] for r in c.execute(queries()['q_sinais_parados'])], [1])
        self.assertEqual([r[0] for r in c.execute(queries()['q_candidatas_paradas'])], [2])


class PosLancamento(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()
        self.c.execute("INSERT INTO ideias(id,titulo,estado,repo_full_name) VALUES(1,'a','tracao','me/a')")
        self.c.execute("INSERT INTO repos(id,full_name,proprio_ideia_id) VALUES(1,'me/a',1)")

    def test_m1SaudeIssuesPorMilEstrelas(self):
        self.c.execute("INSERT INTO repo_snapshots VALUES(1,date('now'),2000,50,30,date('now'),'gh_star_count')")
        self.assertEqual([(r[0], r[1]) for r in self.c.execute(queries()['q_m1_saude'])], [(1, 'pausa')])

    def test_m2CongeladoSemPush(self):
        self.c.execute("INSERT INTO repo_snapshots VALUES(1,date('now'),200,5,1,date('now','-50 days'),'gh_star_count')")
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_m2_congelado'])], [1])

    def test_conversaoDosUltimos14Dias(self):
        for d in range(14):
            self.c.execute("INSERT INTO traffic VALUES(1,date('now',?),100,100)", (f'-{d} days',))
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(1,date('now',?),1,'stargazers_history')", (f'-{d} days',))
        r = linha(self.c, 'q_conversao', {'ideia_id': 1})
        self.assertAlmostEqual(r['conversao'], 14 / 1400)


class Checklist(unittest.TestCase):
    def test_lancadaSemEstrelasDeOntemAcusa(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','lancada')")
        c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(1,'pronta','lancada','x','rotina')")
        self.assertEqual(linha(c, 'q_checklist')['lancadas_sem_estrelas_ontem'], 1)

    def test_lancadaSemHipoteseS1Acusa(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','lancada')")
        c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(1,'pronta','lancada','x','rotina')")
        self.assertEqual(linha(c, 'q_checklist')['lancadas_sem_hipotese'], 1)


if __name__ == '__main__':
    unittest.main()
