"""Review round 3: cycle guards on launch and stage moves, the build queue and the desk-failure queue see NULLs, the
extended window kills only below the kill line, suspect days block any decision, a pre-launch baseline for repos that
were public before, real build hours, Unicode owner phrases, hook articles, the seed file and the seed's atomicity."""
import csv, os, shutil, sqlite3, subprocess, sys, tempfile, unittest
from lib import decidir
from test_schema import Base, FICHA, D
from test_queries import queries, db_sem_travas, linha, candidata
from test_review_r2 import hip


class CicloR3(Base):
    def reaberta_pronta(self):
        """An idea that reached tracao in cycle 1 (S2 confirmed), archived, reopened and rebuilt: pronta in cycle 2."""
        i = self.nova(**FICHA); self.ate_lancada(i)
        self.c.execute("UPDATE lancamentos SET postado_em=datetime('now','-40 days') WHERE ideia_id=?", (i,))
        h1 = hip(self.c, i); h2 = hip(self.c, i, 'S2')
        for d in range(41):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(?,date('now',?),5,'stargazers_history')", (i, f'-{d} days'))
        self.c.execute("UPDATE hipoteses SET resultado='inconclusiva', fechada_em=datetime('now') WHERE id=?", (h1,))
        self.c.execute("UPDATE hipoteses SET resultado='confirmada', fechada_em=datetime('now'), n_observado=30, valor_observado=150 WHERE id=?", (h2,))
        self.assertIsNone(self.mover(i, 'tracao'))
        self.assertIsNone(self.mover(i, 'arquivada', reabrir_se='relançamento'))
        self.assertIsNone(self.mover(i, 'candidata', motivo='REABERTA: relançamento [sinal#1]'))
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now') WHERE id=?", (i,))
        self.assertIsNone(self.aprovar(i)); self.checklist_ok(i)
        self.assertIsNone(self.mover(i, 'pronta'))
        return i

    def test_lancadaExigePostDoCicloAtual(self):
        i = self.reaberta_pronta()
        self.assertIn('sem_lancamento', self.mover(i, 'lancada', 'dono', f'"lancei a ideia#{i} no reddit" chat'))

    def test_tracaoExigeS2DoCicloAtual(self):
        i = self.reaberta_pronta()
        self.lancar(i, 'reddit')
        self.assertIsNone(self.mover(i, 'lancada', 'dono', f'"lancei a ideia#{i} no reddit" chat'))
        self.assertIn('etapa_nao_passou', self.mover(i, 'tracao'))

    def test_lancadaSemHipoteseDoCicloAcusa(self):
        i = self.reaberta_pronta()
        self.lancar(i, 'reddit')
        self.mover(i, 'lancada', 'dono', f'"lancei a ideia#{i} no reddit" chat')
        self.assertEqual(linha(self.c, 'q_checklist')['lancadas_sem_hipotese'], 1)


class GuardsR3(Base):
    def test_diaSuspeitoBloqueiaRefutacao(self):
        i = self.nova(**FICHA); self.ate_lancada(i)
        h = hip(self.c, i)
        for d in range(14):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte,suspeito) VALUES(?,date('now',?),?,'stargazers_history',?)",
                           (i, f'+{d} days', 300 if d == 2 else 0, 1 if d == 2 else 0))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'estrelas_suspeitas'):
            self.c.execute("UPDATE hipoteses SET resultado='refutada', fechada_em=datetime('now'), n_observado=14, valor_observado=0 WHERE id=?", (h,))

    def test_prontaExigeHorasReaisDeConstrucao(self):
        i = self.nova(**FICHA); self.aprovar(i); self.checklist_ok(i, horas=0)
        self.assertIn('horas_reais_insuficientes', self.mover(i, 'pronta'))   # renamed in round 4
        self.c.execute("INSERT INTO horas(ideia_id,data,horas,tipo,prova_dono) VALUES(?,date('now'),7,'construcao','\"7h\" chat')", (i,))
        self.assertIsNone(self.mover(i, 'pronta'))

    def test_ganchoComArtigoQueVendeIaRecusado(self):
        i = self.nova(**dict(FICHA, gancho='The AI agent that renames your files'))
        self.assertIn('gancho_vende_ia', self.aprovar(i))

    def test_ganchoQueCitaIaNoMeioPassa(self):
        i = self.nova(**dict(FICHA, gancho='renames 10k files in 2 s, no LLM needed'))
        self.assertIsNone(self.aprovar(i))

    def test_fraseDoDonoEmCaixaAlta(self):
        i = self.nova(**FICHA)
        self.assertIsNone(self.mover(i, 'em_construcao', 'dono', f'"APROVO A CONSTRUÇÃO DA IDEIA#{i}" chat 2026-10-27 10:00'))

    def test_sucessorAtivoAntigoTomaONicho(self):
        i = self.nova(**FICHA)
        r = self.c.execute("INSERT INTO repos(full_name,criado_em) VALUES('b/succ',date('now','-30 months'))").lastrowid
        self.c.execute("INSERT INTO repo_snapshots(repo_id,data,estrelas,pushed_at,fonte) VALUES(?,date('now'),4000,date('now','-5 days'),'gh_star_count')", (r,))
        self.c.execute("INSERT INTO ideia_repos VALUES(?,?,'sucessor')", (i, r))
        self.assertIn('nicho_tomado', self.aprovar(i))


class BaselineR3(Base):
    def test_repoPublicoAntesExigeBaselineEDescontaORitmo(self):
        i = self.nova(**FICHA)
        self.c.execute("INSERT INTO repos(full_name,criado_em,publico_em,proprio_ideia_id) VALUES('me/old',date('now','-2 years'),date('now','-2 years'),?)", (i,))
        self.ate_lancada(i)
        h = hip(self.c, i)
        for d in range(14):   # 1 star a day: the pre-launch pace
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(?,date('now',?),1,'stargazers_history')", (i, f'+{d} days'))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_sem_dado'):   # no baseline days yet
            self.c.execute("UPDATE hipoteses SET resultado='confirmada', fechada_em=datetime('now'), n_observado=14, valor_observado=14 WHERE id=?", (h,))
        for d in range(1, 29):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(?,date('now',?),1,'stargazers_history')", (i, f'-{d} days'))
        cur = self.c.execute(queries()['q_hipoteses_abertas']); cols = [x[0] for x in cur.description]
        r = dict(zip(cols, cur.fetchone()))
        self.assertEqual((r['baseline_janela'], r['eventos_janela']), (14, 0))


class LibR3(unittest.TestCase):
    def test_estendidaEntreAsLinhasEhInconclusiva(self):
        self.assertEqual(decidir('contagem', 60, 30, 100, 29, 30, 0, 1, passa_estendido=100), 'inconclusiva')
        self.assertEqual(decidir('contagem', 20, 30, 100, 29, 30, 0, 1, passa_estendido=100, janela1_abaixo=True), 'mata')   # round 5

    def test_chamadaDocumentadaRodaComTudoNomeado(self):
        self.assertEqual(decidir('contagem', eventos=12, n=14, limiar_passa=10, limiar_mata=2, n_min=14, eventos_min=0,
                                 estendida=0, prazo_esgotado=False, passa_estendido=None), 'passa')


class QueriesR3(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def test_mesaReprovadaPegaNulos(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,categoria,hit_rate_categoria,carga_h_semana,advogado_em) VALUES"
                       "(1,'sem_taxa','candidata','cli',NULL,0.5,datetime('now')),(2,'sem_carga','candidata','cli',0.0113,NULL,datetime('now'))")
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_mesa_reprovada'])], [1, 2])

    def test_metaIgnoraDiasSuspeitosEHitOrfao(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','arquivada')")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(1,'tracao','hit','x','rotina')")
        self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte,suspeito) VALUES(1,date('now'),900,'stargazers_history',1)")
        r = linha(self.c, 'q_meta')
        self.assertEqual((r['estrelas_12m'], r['hits_12m']), (0, 0))

    def test_filaNormalizaDemandaPeloLimiarDoTipo(self):
        from test_schema import PAYLOAD
        self.c.execute("INSERT INTO fontes(id,nome,plataforma,tipo,frequencia) VALUES(1,'f','github','x','diaria')")
        candidata(self.c, 1, categoria='sucessor_abandonado', hit_rate_categoria=None, horas_estimadas=10)
        candidata(self.c, 2, categoria='lib_benchmark', hit_rate_categoria=None, horas_estimadas=10)
        self.c.execute("INSERT INTO sinais(id,fonte_id,hash,url,url_status,trecho_literal,tipo,reacoes,payload_json) VALUES"
                       "(1,1,'a','u1',200,?,'repo_abandonado',20000,?),(2,1,'b','u2',200,?,'issue_reacoes',600,?)", ('x' * 40, PAYLOAD) * 2)
        self.c.execute("INSERT INTO evidencias VALUES(1,1,1,NULL),(2,2,1,NULL)")
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_fila_construcao'])], [2, 1])   # 600/100 = 6x the threshold beats 20000/5000 = 4x


class SeedR3(unittest.TestCase):
    def test_endpointDoShowHnInteiro(self):
        rows = {r['nome']: r for r in csv.DictReader(open(os.path.join(D, 'seed_fontes.csv'), encoding='utf-8'))}
        self.assertTrue(rows['hn_algolia_showhn']['endpoint'].endswith('hitsPerPage=1000'))
        self.assertEqual(rows['hn_algolia_showhn']['status'], 'ok')
        self.assertTrue(all(None not in r and r['status'] in ('ok', 'degradada', 'quebrada', 'desligada') for r in rows.values()))

    def test_seedQueFalhaNaoDeixaBanco(self):
        t = tempfile.mkdtemp()
        try:
            for f in ('schema.sql', 'seed.py', 'seed_benchmarks.csv', 'seed_limiares.csv', 'seed_fontes.csv'):
                shutil.copy(os.path.join(D, f), t)
            open(os.path.join(t, 'seed_config.csv'), 'w').write('chave,valor,origem\nx,1,invalida\n')
            p = subprocess.run([sys.executable, 'seed.py', 'rotina.db'], cwd=t, capture_output=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertFalse(os.path.exists(os.path.join(t, 'rotina.db')))
        finally:
            shutil.rmtree(t)


if __name__ == '__main__':
    unittest.main()
