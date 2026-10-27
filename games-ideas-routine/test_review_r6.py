"""Review round 6 (findings #2, #4, #6, #9, #10)."""
import sqlite3, unittest
from test_queries import queries
from test_queries_v2 import db_sem_travas


def col(c, nome, coluna, params=None):
    cur = c.execute(queries()[nome], params or {})
    cols = [d[0] for d in cur.description]
    return cur.fetchone()[cols.index(coluna)]


class QueriesR6(unittest.TestCase):
    def test_emTesteSemExperimentoAbertoApareceNoChecklist(self):
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('em_teste_sem_experimento_dias','7','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo,estado,atualizada_em) VALUES(1,'a','em_teste',datetime('now','-10 days'))")
        self.assertEqual([r[0] for r in c.execute(queries()['q_em_teste_sem_experimento'])], [1])
        self.assertEqual(col(c, 'q_checklist', 'em_teste_sem_experimento'), 1)

    def test_topTrendingRobloxDe300DiasEhTendencia(self):   # round 12: Roblox age counts from the first popularity (< 365 days old)
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','candidata')")
        c.execute("INSERT INTO concorrentes(id,loja,id_loja,lancado_em) VALUES(1,'roblox','5',date('now','-300 days'))")
        c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,ccu) VALUES(1,date('now','-30 days'),'global',200)")   # round 14: observed rise
        c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista,rank_pos) VALUES(1,date('now'),'global','top-trending',1)")
        self.assertEqual(col(c, 'q_checklist', 'tendencias_nao_registradas'), 1)

    def test_rivalCadastradoNaoContaPlataforma(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'i')")
        c.execute("INSERT INTO fontes(id,nome,plataforma,tipo,mercado,frequencia,cota_min) VALUES(1,'a','roblox','t','todos','diaria',0),(2,'b','crazygames','t','todos','diaria',0)")
        for i, (f, t) in enumerate([(1, 'hit_plataforma'), (1, 'hit_plataforma'), (2, 'concorrente')], start=1):
            c.execute("INSERT INTO sinais(id,fonte_id,hash,url,url_status,trecho_literal,tipo,payload_json) VALUES(?,?,?,'u',200,?,?,'{\"sha256\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"date\":\"d\"}')", (i, f, f'h{i}', 'x' * 40, t))
            c.execute("INSERT INTO evidencias VALUES(1,?,1,1,NULL)", (i,))
        self.assertEqual(c.execute(queries()['q_fontes_distintas_por_ideia']).fetchone()[1], 1)

    def test_escadaE5UsaUltimoMesFechado(self):
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('e5_d60_min_usd','5','seed',datetime('now')),('e5_d120_min_usd','10','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','lancada')")
        c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono,em) VALUES(1,'em_construcao','lancada','t','dono','x',datetime('now','-70 days'))")
        c.execute("INSERT INTO receita_snapshots(ideia_id,data,receita_liquida_usd,fonte) VALUES(1,date('now','start of month','-1 month'),3,'poki')")
        self.assertEqual(c.execute(queries()['q_e5_escada']).fetchall()[0][-1], 'congelar')

    def test_graduacaoDoisMesesSeguidos(self):
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('graduacao_receita_min_usd','100','seed',datetime('now')),('graduacao_meses','2','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','lancada')")
        for m, v in ((-1, 120), (-2, 130)):
            c.execute("INSERT INTO receita_snapshots(ideia_id,data,receita_liquida_usd,fonte) VALUES(1,date('now','start of month',?),?,'poki')", (f'{m} month', v))
        self.assertEqual([r[0] for r in c.execute(queries()['q_graduacao'])], [1])

    def test_receitaDeDuasPlataformasNoMesmoMes(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'a')")
        c.execute("INSERT INTO receita_snapshots(ideia_id,data,receita_liquida_usd,fonte) VALUES(1,'2026-12-01',36,'crazygames')")
        c.execute("INSERT INTO receita_snapshots(ideia_id,data,receita_liquida_usd,fonte) VALUES(1,'2026-12-01',20,'gamedistribution')")



class ValidadaParada(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()
        self.c.execute("INSERT INTO config VALUES('validada_max_dias','21','seed',datetime('now')),('validada_max_dias_arquivar','180','seed',datetime('now'))")

    def com(self, dias):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','validada')")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,em) VALUES(1,'em_teste','validada','t','rotina',datetime('now',?))", (f'-{dias} days',))
        return self.c.execute(queries()['q_validada_parada']).fetchall()

    def test_validadaParadaVira_pendencia_aos21dias(self):
        self.assertEqual(self.com(30), [(1, 'pendencia')])

    def test_validadaParadaSoArquivaAos180dias(self):
        self.assertEqual(self.com(200), [(1, 'arquivar')])


if __name__ == '__main__':
    unittest.main()
