"""End to end on the seeded database: an idea walks the funnel of SKILL.md sections 6-10 with the real thresholds."""
import os, sqlite3, subprocess, sys, tempfile, unittest
from lib import decidir
from test_schema import PAYLOAD, FICHA
from test_queries import queries

D = os.path.dirname(os.path.abspath(__file__))


class Funil(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        db = os.path.join(self.tmp, 'rotina.db')
        subprocess.run([sys.executable, 'seed.py', db], cwd=D, check=True, capture_output=True)
        self.c = sqlite3.connect(db); self.c.execute('PRAGMA foreign_keys=ON')
        # the suite pins the profile values its fixtures use: adapting seed_config.csv never breaks it
        for k, v in (('horas_mvp_max', '20'), ('carga_max_h_semana', '3'), ('categoria_hit_min', '0.0015'), ('slots_construcao', '1')):
            self.c.execute('UPDATE config SET valor=? WHERE chave=?', (v, k))
        # and the seeds' measurement date (a fresh bootstrap re-measures stale ones; the suite must not expire)
        self.c.execute("UPDATE benchmarks SET verificado_em=date('now')")

    def mover(self, i, para, ator='rotina', prova=None, motivo='t', **cols):
        de = self.c.execute('SELECT estado FROM ideias WHERE id=?', (i,)).fetchone()[0]
        try:
            self.c.execute('SAVEPOINT s')
            self.c.execute('INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,?,?,?,?,?)', (i, de, para, motivo, ator, prova))
            sets = ', '.join([f'{k}=?' for k in cols] + ['estado=?'])
            self.c.execute(f'UPDATE ideias SET {sets} WHERE id=?', list(cols.values()) + [para, i])
            self.c.execute('RELEASE s'); return None
        except sqlite3.IntegrityError as e:
            self.c.execute('ROLLBACK TO s'); self.c.execute('RELEASE s'); return str(e)

    def limiar(self, etapa):
        return self.c.execute("SELECT etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,versao,prazo_dias FROM limiares "
                              "WHERE etapa=? ORDER BY versao DESC LIMIT 1", (etapa,)).fetchone()

    def preregistrar(self, i, etapa):
        e, m, t, lp, lm, n, ev, v, p = self.limiar(etapa)
        return self.c.execute("INSERT INTO hipoteses(ideia_id,etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,prazo_dias) "
                              "VALUES(?,?,?,?,?,?,?,?,?,?)", (i, e, m, t, lp, lm, n, ev, v, p)).lastrowid

    def nova_ate_lancada(self):
        fonte = self.c.execute("SELECT id FROM fontes WHERE nome='gh_issues_reacoes'").fetchone()[0]
        i = self.c.execute("INSERT INTO ideias(titulo) VALUES('portwho')").lastrowid
        s = self.c.execute("INSERT INTO sinais(fonte_id,hash,url,url_status,trecho_literal,tipo,reacoes,payload_json) VALUES(?,?,?,200,?,'issue_reacoes',340,?)",
                           (fonte, 'h1', 'https://github.com/x/y/issues/1', 'x' * 40, PAYLOAD)).lastrowid
        self.c.execute('INSERT INTO evidencias(ideia_id,sinal_id,polaridade) VALUES(?,?,1)', (i, s))
        self.assertIsNone(self.mover(i, 'candidata'))
        cols = dict(FICHA); cols.pop('advogado_em')
        b, v = self.c.execute("SELECT id, valor FROM benchmarks WHERE metrica='hit_rate_gt1000_cli_rust_12m'").fetchone()
        cols.update(hit_rate_benchmark_id=b, hit_rate_categoria=v, linguagem='Rust')
        r = self.c.execute("INSERT INTO repos(full_name,criado_em) VALUES('old/lsof-wrapper','2019-01-01')").lastrowid
        self.c.execute("INSERT INTO repo_snapshots(repo_id,data,estrelas,forks,pushed_at,fonte) VALUES(?,date('now'),700,40,date('now','-20 days'),'gh_star_count')", (r,))
        self.c.execute("INSERT INTO ideia_repos(ideia_id,repo_id,papel) VALUES(?,?,'rival')", (i, r))
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in cols) + ", advogado_em=datetime('now') WHERE id=?", list(cols.values()) + [i])
        self.assertIsNone(self.mover(i, 'em_construcao', 'dono', f'"aprovo a construção da ideia#{i}" chat 2026-10-27 10:00'))
        self.c.execute("INSERT INTO horas(ideia_id,data,horas,tipo,prova_dono) VALUES(?,date('now'),10,'construcao','\"10h\" chat')", (i,))
        for (cod,) in self.c.execute('SELECT codigo FROM checklist_itens WHERE obrigatorio=1').fetchall():
            self.c.execute("INSERT INTO checklist(ideia_id,item,ok,prova) VALUES(?,?,1,'readme ok')", (i, cod))
        self.assertIsNone(self.mover(i, 'pronta'))
        self.c.execute("INSERT INTO lancamentos(ideia_id,canal,url,titulo,postado_em,prova_dono) VALUES(?,'show_hn','https://news.ycombinator.com/item?id=1',"
                       "'Show HN: portwho - which process holds a port, 3x faster than lsof',datetime('now','-30 days'),?)", (i, f'"lancei a ideia#{i} no show_hn" chat'))
        self.assertIsNone(self.mover(i, 'lancada', 'dono', f'"lancei a ideia#{i} no show_hn" chat 2026-10-27 12:00'))
        return i

    def test_caminhoAteTracao(self):
        i = self.nova_ate_lancada()
        h1 = self.preregistrar(i, 'S1'); h2 = self.preregistrar(i, 'S2')
        for d in range(0, 31):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(?,date('now',?),5,'stargazers_history')", (i, f'-{d} days'))
        jan = dict(zip([x[0] for x in self.c.execute(queries()['q_janela'], {'ideia_id': i}).description],
                       self.c.execute(queries()['q_janela'], {'ideia_id': i}).fetchone()))
        e, m, t, lp, lm, n, ev, v, p = self.limiar('S1')
        self.assertEqual(decidir(t, jan['e14'], 14, lp, lm, n, ev, 0), 'passa')
        self.c.execute("UPDATE hipoteses SET resultado='confirmada', fechada_em=datetime('now'), n_observado=14, valor_observado=? WHERE id=?", (jan['e14'], h1))
        e, m, t, lp, lm, n, ev, v, p = self.limiar('S2')
        self.assertEqual(decidir(t, jan['e30'], 30, lp, lm, n, ev, 0), 'passa')
        self.c.execute("UPDATE hipoteses SET resultado='confirmada', fechada_em=datetime('now'), n_observado=30, valor_observado=? WHERE id=?", (jan['e30'], h2))
        self.assertIsNone(self.mover(i, 'tracao'))

    def test_umCanalFracoSoArquivaDoisMatam(self):
        i = self.nova_ate_lancada()
        self.assertIn('matar_exige_dois_canais', self.mover(i, 'morta', motivo_morte='teste_reprovado'))
        self.assertIsNone(self.mover(i, 'arquivada', reabrir_se='2º canal com E7 >= 30'))

    def test_preRegistroDivergenteRecusado(self):
        i = self.nova_ate_lancada()
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'pre_registro_diverge_do_limiar'):
            self.c.execute("INSERT INTO hipoteses(ideia_id,etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,prazo_dias) "
                           "VALUES(?,'S2','e30','contagem',50,10,30,0,1,30)", (i,))

    def test_calibracaoNaoAfrouxa(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'limiar_nao_afrouxa'):
            self.c.execute("INSERT INTO limiares(etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,prazo_dias,mata_destino,versao,vigente_desde,origem) "
                           "VALUES('S2','e30','contagem',60,29,30,0,30,'morta',2,date('now'),'calibrado')")

    def test_checklistDoBancoSemeadoZerado(self):
        cur = self.c.execute(queries()['q_checklist']); cols = [d[0] for d in cur.description]
        r = dict(zip(cols, cur.fetchone()))
        self.assertTrue(all(v == 0 for v in r.values()), r)


if __name__ == '__main__':
    unittest.main()
