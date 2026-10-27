"""Review round 5 (last): forbidden category wins in the desk view, only recalibrable benchmarks expire, the baseline
covers any repo public before launch, every stage pre-registered, the owner's giving up needs the owner to reopen,
an extension kills only when the first window was below the kill line, the category rate must be the current row,
polishing an existing public repo skips the hour floor, Portuguese AI hooks, demand-weighted queue, 'outro' is not a
second channel, and the sheet says how the tool reaches users."""
import sqlite3, unittest
from lib import decidir
from test_schema import Base, FICHA
from test_queries import queries, db_sem_travas, linha, candidata
from test_review_r2 import hip


class MesaR5(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def mesa(self):
        return [(r[0], r[-1]) for r in self.c.execute(queries()['q_mesa_reprovada'])]

    def test_categoriaProibidaVenceOutroCorte(self):
        candidata(self.c, 1, categoria='mcp_server', horas_estimadas=30)
        self.assertEqual(self.mesa(), [(1, 'categoria_proibida')])

    def test_semComoChegaEhFichaIncompleta(self):
        candidata(self.c, 1, como_chega=None)
        self.assertEqual(self.mesa(), [(1, 'ficha_incompleta')])

    def test_taxaDeLinhaSuperadaNaoValeNaFila(self):
        candidata(self.c, 1, hit_rate_categoria=0.00166)
        b = self.c.execute('SELECT hit_rate_benchmark_id FROM ideias WHERE id=1').fetchone()[0]
        self.c.execute("INSERT INTO benchmarks(metrica,segmento,valor,unidade,source_url,data_fonte,tipo_fonte,confianca,verificado_em) "
                       "SELECT metrica,segmento,0.0005,unidade,source_url,data_fonte,tipo_fonte,confianca,date('now','+1 day') FROM benchmarks WHERE id=?", (b,))
        self.assertEqual(self.mesa(), [(1, 'hit_rate_sem_benchmark')])

    def test_filaPesaDemandaPelaTaxa(self):
        from test_schema import PAYLOAD
        self.c.execute("INSERT INTO fontes(id,nome,plataforma,tipo,frequencia) VALUES(1,'f','github','x','diaria')")
        candidata(self.c, 1, hit_rate_categoria=0.00166)
        candidata(self.c, 2, categoria='sucessor_abandonado', hit_rate_categoria=None)
        self.c.execute("INSERT INTO sinais(id,fonte_id,hash,url,url_status,trecho_literal,tipo,reacoes,payload_json) VALUES"
                       "(1,1,'a','u1',200,?,'issue_reacoes',100,?),(2,1,'b','u2',200,?,'repo_abandonado',20000,?)", ('x' * 40, PAYLOAD) * 2)
        self.c.execute("INSERT INTO evidencias VALUES(1,1,1,NULL),(2,2,1,NULL)")
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_fila_construcao'])], [2, 1])   # 1.0 x 4.0 beats 1.1 x 1.0


class ChecklistR5(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def test_soBenchmarksRecalibraveisVencem(self):
        self.c.execute("INSERT INTO benchmarks(metrica,segmento,valor,unidade,source_url,data_fonte,tipo_fonte,confianca,verificado_em) VALUES"
                       "('fork_star_mediana','repos_gt2000_12m',0.097,'r','u','2026','medicao_propria','alta',date('now','-200 days')),"
                       "('hit_rate_gt1000_cli_12m','topic_cli',0.0019,'f','u','2026','medicao_propria','alta',date('now','-200 days'))")
        self.assertEqual(linha(self.c, 'q_checklist')['benchmarks_vencidos'], 1)

    def test_lancadaSemS2DoCicloAcusa(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','tracao')")
        self.c.execute("INSERT INTO hipoteses(ideia_id,etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,prazo_dias) "
                       "VALUES(1,'S1','e14','contagem',10,2,14,0,1,14),(1,'S2','e30','contagem',100,29,30,0,1,30)")
        self.assertEqual(linha(self.c, 'q_checklist')['lancadas_sem_hipotese'], 1)


class GuardsR5(Base):
    def test_baselineParaRepoPublicoPoucoAntesDoLancamento(self):
        i = self.nova(**FICHA)
        self.c.execute("INSERT INTO repos(full_name,criado_em,publico_em,proprio_ideia_id) VALUES('me/r',date('now','-10 days'),date('now','-10 days'),?)", (i,))
        self.ate_lancada(i)
        h = hip(self.c, i)
        for d in range(14):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(?,date('now',?),1,'stargazers_history')", (i, f'+{d} days'))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_sem_dado'):
            self.c.execute("UPDATE hipoteses SET resultado='confirmada', fechada_em=datetime('now'), n_observado=14, valor_observado=14 WHERE id=?", (h,))

    def test_desistenciaDoDonoSoODonoReabre(self):
        i = self.nova(**FICHA)
        self.assertIsNone(self.mover(i, 'morta', 'dono', f'"desisto da ideia#{i}" chat', motivo_morte='dono_desistiu'))
        self.assertIn('reabertura_proibida', self.mover(i, 'candidata', motivo='REABERTA: novo sinal'))

    def test_extensaoSoMataSeAPrimeiraJanelaEstavaAbaixo(self):
        i = self.nova(**FICHA); self.ate_lancada(i)
        self.c.execute("UPDATE lancamentos SET postado_em=datetime('now','-20 days') WHERE ideia_id=?", (i,))
        h = hip(self.c, i); self.lancar(i, 'reddit')
        self.c.execute("UPDATE hipoteses SET estendida=1, passa_estendido=10, estendida_em=date('now') WHERE id=?", (h,))
        for d in range(14):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(?,date('now',?),0,'stargazers_history')", (i, f'+{d} days'))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_incoerente'):
            self.c.execute("UPDATE hipoteses SET resultado='refutada', fechada_em=datetime('now'), n_observado=14, valor_observado=0 WHERE id=?", (h,))

    def test_canalOutroNaoEhSegundoCanal(self):
        i = self.nova(**FICHA); self.ate_lancada(i); self.lancar(i, 'outro')
        self.c.execute("UPDATE hipoteses SET resultado='inconclusiva', fechada_em=datetime('now') WHERE resultado IS NULL")
        self.assertIn('matar_exige_dois_canais', self.mover(i, 'morta', motivo_morte='teste_reprovado'))

    def test_polimentoDeRepoPublicoDispensaPisoDeHoras(self):
        i = self.nova(**dict(FICHA, horas_estimadas=3))
        self.c.execute("INSERT INTO repos(full_name,criado_em,publico_em,proprio_ideia_id) VALUES('me/velho',date('now','-2 years'),date('now','-2 years'),?)", (i,))
        self.assertIsNone(self.aprovar(i))
        self.checklist_ok(i, horas=3)
        self.assertIsNone(self.mover(i, 'pronta'))

    def test_ganchoEmPortuguesQueVendeIa(self):
        i = self.nova(**dict(FICHA, gancho='Agente de IA que corrige o CI'))
        self.assertIn('gancho_vende_ia', self.aprovar(i))


class LibR5(unittest.TestCase):
    def test_estendidaEntreAsLinhasNaPrimeiraNaoMata(self):
        self.assertEqual(decidir('contagem', 0, 30, 100, 29, 30, 0, 1, passa_estendido=100), 'inconclusiva')
        self.assertEqual(decidir('contagem', 0, 30, 100, 29, 30, 0, 1, passa_estendido=100, janela1_abaixo=True), 'mata')


if __name__ == '__main__':
    unittest.main()
