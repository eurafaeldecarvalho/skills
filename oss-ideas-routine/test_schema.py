"""schema.sql guards: the funnel cannot be skipped by mistake, label or shortcut."""
import os, sqlite3, unittest

D = os.path.dirname(os.path.abspath(__file__))
SCHEMA = open(os.path.join(D, 'schema.sql'), encoding='utf-8').read()
PAYLOAD = '{"sha256":"' + 'a' * 64 + '","date":"Mon, 27 Oct 2026 10:00:00 GMT"}'
FICHA = dict(categoria='cli', gancho='finds which process holds a port, in one command', prova_numero='3x faster than lsof',
             linguagem='Go', horas_estimadas=12, estrelas_alvo=1000, carga_h_semana=0.3, hit_rate_categoria=0.0113, hit_rate_benchmark_id=1,
             licenca='MIT', advogado_em='agora', modo_baixa_manutencao=0, como_chega='Show HN + the issue thread that asked for it')
CONFIG = (('horas_mvp_max', '20'), ('carga_max_h_semana', '3'), ('categoria_hit_min', '0.005'),
          ('slots_construcao', '1'), ('slots_lancadas', '2'), ('demanda_reacoes_min', '100'), ('demanda_pontos_min', '20'),
          ('demanda_estrelas_abandonado_min', '5000'), ('horas_mvp_min', '6'))


class Base(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(':memory:'); self.c.executescript(SCHEMA)
        self.c.executemany("INSERT INTO config(chave,valor,origem) VALUES(?,?,'seed')", CONFIG)
        self.c.execute("INSERT INTO fontes(id,nome,plataforma,tipo,frequencia) VALUES(1,'gh_issues_reacoes','github','necessidade','diaria'),"
                       "(2,'gh_trending_html','github','ranking','diaria')")
        self.c.executemany("INSERT INTO limiares(etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,prazo_dias,mata_destino,versao,vigente_desde,origem) "
                           "VALUES(?,?,'contagem',?,?,?,0,?,?,1,date('now'),'heuristica')",
                           [('S1', 'e14', 10, 2, 14, 14, 'arquivada'), ('S2', 'e30', 100, 29, 30, 30, 'morta'), ('S3', 'e90', 1000, 299, 90, 90, 'arquivada')])
        self.c.execute("INSERT INTO benchmarks(id,metrica,segmento,valor,unidade,source_url,data_fonte,tipo_fonte,confianca,verificado_em) "
                       "VALUES(1,'hit_rate_gt1000_cli_go_12m','topic_cli_go',0.0113,'fracao','https://api.github.com/search/repositories','2026-10-27','medicao_propria','alta',date('now'))")

    def sinal(self, tipo='issue_reacoes', fonte=1, reacoes=None):
        n = self.c.execute('SELECT COUNT(*) FROM sinais').fetchone()[0] + 1
        if reacoes is None:   # above every demand threshold of the config
            reacoes = 6000 if tipo == 'repo_abandonado' else 340
        return self.c.execute("INSERT INTO sinais(fonte_id,hash,url,url_status,trecho_literal,tipo,reacoes,payload_json) VALUES(?,?,?,200,?,?,?,?)",
                              (fonte, f'h{n}', f'https://github.com/x/y/issues/{n}', 'x' * 40, tipo, reacoes, PAYLOAD)).lastrowid

    def nova(self, demanda=True, sem_repos=False, **cols):
        i = self.c.execute("INSERT INTO ideias(titulo) VALUES('t')").lastrowid
        if demanda:
            self.c.execute('INSERT INTO evidencias(ideia_id,sinal_id,polaridade) VALUES(?,?,1)', (i, self.sinal()))
        if not sem_repos:   # the niche search left a trace: an old, active rival with a complete snapshot
            r = self.c.execute("INSERT INTO repos(full_name,criado_em) VALUES(?,date('now','-5 years'))", (f'old/rival{i}',)).lastrowid
            self.c.execute("INSERT INTO repo_snapshots(repo_id,data,estrelas,forks,pushed_at,fonte) VALUES(?,date('now'),900,90,date('now','-3 days'),'gh_star_count')", (r,))
            self.c.execute("INSERT INTO ideia_repos(ideia_id,repo_id,papel) VALUES(?,?,'rival')", (i, r))
        self.mover(i, 'candidata')
        if cols:
            self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in cols) + ' WHERE id=?', list(cols.values()) + [i])
            if cols.get('advogado_em') == 'agora':   # the advocate ran after the entry in candidata
                self.c.execute("UPDATE ideias SET advogado_em=datetime('now') WHERE id=?", (i,))
        return i

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

    def aprovar(self, i):
        return self.mover(i, 'em_construcao', 'dono', f'"aprovo a construção da ideia#{i}" chat 2026-10-27 10:00')

    def checklist_ok(self, i, horas=8):
        if horas:   # the build's real hours (pronta refuses a one-off below horas_mvp_min)
            self.c.execute("INSERT INTO horas(ideia_id,data,horas,tipo,prova_dono) VALUES(?,date('now'),?,'construcao','\"horas\" chat')", (i, horas))
        for (cod,) in self.c.execute('SELECT codigo FROM checklist_itens WHERE obrigatorio=1').fetchall():
            self.c.execute("INSERT INTO checklist(ideia_id,item,ok,prova) VALUES(?,?,1,'readme linha 3') "
                           "ON CONFLICT(ideia_id,item) DO UPDATE SET ok=1, prova=excluded.prova, verificado_em=datetime('now')", (i, cod))

    def lancar(self, i, canal='show_hn'):
        self.c.execute("INSERT INTO lancamentos(ideia_id,canal,url,titulo,postado_em,prova_dono) VALUES(?,?,?,?,datetime('now'),?)",
                       (i, canal, f'https://news.ycombinator.com/item?id={i}{canal}', 'Show HN: portwho', f'"lancei a ideia#{i} no {canal}" chat'))

    def ate_lancada(self, i):
        self.aprovar(i); self.checklist_ok(i); self.mover(i, 'pronta'); self.lancar(i)
        return self.mover(i, 'lancada', 'dono', f'"lancei a ideia#{i} no show_hn" chat 2026-10-27 12:00')


class Funil(Base):
    def test_ideiaNasceEmSinal(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'ideia_nasce_em_sinal'):
            self.c.execute("INSERT INTO ideias(titulo,estado) VALUES('x','candidata')")

    def test_candidataExigeSinalDeDemanda(self):
        i = self.c.execute("INSERT INTO ideias(titulo) VALUES('t')").lastrowid
        self.assertIn('sem_sinal_de_demanda', self.mover(i, 'candidata'))
        self.c.execute('INSERT INTO evidencias(ideia_id,sinal_id,polaridade) VALUES(?,?,1)', (i, self.sinal('ranking', 2)))
        self.assertIn('sem_sinal_de_demanda', self.mover(i, 'candidata'))   # a ranking hit is not demand
        self.c.execute('INSERT INTO evidencias(ideia_id,sinal_id,polaridade) VALUES(?,?,1)', (i, self.sinal('repo_abandonado')))
        self.assertIsNone(self.mover(i, 'candidata'))

    def test_transicaoForaDaTabela(self):
        i = self.nova(**FICHA)
        self.assertIn('transicao_fora_da_tabela', self.mover(i, 'lancada', 'dono', f'"lancei a ideia#{i}" chat'))

    def test_estadoSemEvento(self):
        i = self.nova(**FICHA)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'sem_ideia_evento'):
            self.c.execute("UPDATE ideias SET estado='arquivada', reabrir_se='x' WHERE id=?", (i,))

    def test_construcaoSoComAFraseDoDono(self):
        i = self.nova(**FICHA)
        self.assertIn('transicao_exige_dono', self.mover(i, 'em_construcao'))
        self.assertIn('frase_do_dono', self.mover(i, 'em_construcao', 'dono', f'"não aprovo a construção da ideia#{i}" chat'))
        self.assertIsNone(self.aprovar(i))

    def test_construcaoExigeFichaCompleta(self):
        i = self.nova(**dict(FICHA, prova_numero=None))
        self.assertIn('ficha_incompleta', self.aprovar(i))

    def test_construcaoExigeAdvogado(self):
        i = self.nova(**dict(FICHA, advogado_em=None))
        self.assertIn('advogado_obrigatorio', self.aprovar(i))

    def test_umaConstrucaoPorVez(self):
        a = self.nova(**FICHA); b = self.nova(**FICHA)
        self.aprovar(a)
        self.assertIn('slot_ocupado', self.aprovar(b))

    def test_horasAcimaDoTeto(self):
        i = self.nova(**dict(FICHA, horas_estimadas=30))
        self.assertIn('ficha_incompleta', self.aprovar(i))

    def test_cargaAcimaDoTetoSoComModoBaixaManutencao(self):
        i = self.nova(**dict(FICHA, carga_h_semana=4))
        self.assertIn('carga_acima_do_teto', self.aprovar(i))
        self.c.execute('UPDATE ideias SET modo_baixa_manutencao=1 WHERE id=?', (i,))
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now') WHERE id=?", (i,))   # a sheet change voids the advocate (round 1)
        self.assertIsNone(self.aprovar(i))

    def test_categoriaComTaxaBaixaRecusa(self):
        b = self.c.execute("INSERT INTO benchmarks(metrica,segmento,valor,unidade,source_url,data_fonte,tipo_fonte,confianca,verificado_em) "
                           "VALUES('hit_rate_gt1000_skills_12m','topic_skills',0.003,'fracao','s','2026-10-27','medicao_propria','alta',date('now'))").lastrowid
        i = self.nova(**dict(FICHA, categoria='skill_harness', hit_rate_categoria=0.003, hit_rate_benchmark_id=b))
        self.assertIn('categoria_fraca', self.aprovar(i))

    def test_categoriaProibidaSoMorre(self):
        i = self.nova(**dict(FICHA, categoria='prompts_vazados'))
        self.assertIn('categoria_proibida', self.aprovar(i))
        self.assertIn('categoria_proibida', self.mover(i, 'arquivada', reabrir_se='x'))
        self.assertIsNone(self.mover(i, 'morta', motivo_morte='categoria_proibida'))

    def test_nichoTomadoSoMorre(self):
        i = self.nova(**FICHA)
        r = self.c.execute("INSERT INTO repos(full_name,criado_em) VALUES('a/sucessor',date('now','-200 days'))").lastrowid
        self.c.execute("INSERT INTO repo_snapshots(repo_id,data,estrelas,forks,pushed_at,fonte) VALUES(?,date('now'),5000,400,date('now','-10 days'),'gh_star_count')", (r,))
        self.c.execute("INSERT INTO ideia_repos(ideia_id,repo_id,papel) VALUES(?,?,'sucessor')", (i, r))
        self.assertIn('nicho_tomado', self.aprovar(i))

    def test_licencaValida(self):
        i = self.nova(**dict(FICHA, licenca='GPL-3.0'))
        self.assertIn('ficha_incompleta', self.aprovar(i))

    def test_prontaExigeChecklistObrigatorio(self):
        i = self.nova(**FICHA); self.aprovar(i)
        self.assertIn('checklist_incompleto', self.mover(i, 'pronta'))
        self.checklist_ok(i)
        self.assertIsNone(self.mover(i, 'pronta'))

    def test_lancadaExigeFraseEUrlDoPost(self):
        i = self.nova(**FICHA); self.aprovar(i); self.checklist_ok(i); self.mover(i, 'pronta')
        self.assertIn('sem_lancamento', self.mover(i, 'lancada', 'dono', f'"lancei a ideia#{i} no show_hn" chat'))
        self.lancar(i)
        self.assertIsNone(self.mover(i, 'lancada', 'dono', f'"lancei a ideia#{i} no show_hn" chat'))

    def test_matarPorTesteExigeDoisCanais(self):
        i = self.nova(**FICHA); self.assertIsNone(self.ate_lancada(i))
        self.assertIn('matar_exige_dois_canais', self.mover(i, 'morta', motivo_morte='teste_reprovado'))
        self.lancar(i, 'reddit')
        self.assertIsNone(self.mover(i, 'morta', motivo_morte='teste_reprovado'))

    def test_tracaoExigeS2Confirmado(self):
        i = self.nova(**FICHA); self.ate_lancada(i)
        self.assertIn('etapa_nao_passou', self.mover(i, 'tracao'))

    def test_reaberturaDeMorteGraveSoPeloDono(self):
        i = self.nova(**FICHA); self.ate_lancada(i); self.lancar(i, 'reddit'); self.mover(i, 'morta', motivo_morte='teste_reprovado')
        self.assertIn('reabertura_proibida', self.mover(i, 'candidata', motivo='REABERTA: x'))
        self.assertIsNone(self.mover(i, 'candidata', 'dono', f'"reabro a ideia#{i}" chat', motivo='REABERTA: dono'))

    def test_arquivadaExigeReabrirSe(self):
        i = self.nova(**FICHA)
        self.assertIn('arquivada_sem_reabrir_se', self.mover(i, 'arquivada'))


class Dados(Base):
    def test_sinalSemPayloadValido(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute("INSERT INTO sinais(fonte_id,hash,url,url_status,trecho_literal,tipo,payload_json) VALUES(1,'z','u',200,?,'issue_reacoes','{}')", ('x' * 40,))

    def test_sinalImutavel(self):
        s = self.sinal()
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'sinal_imutavel'):
            self.c.execute("UPDATE sinais SET tipo='repo_abandonado' WHERE id=?", (s,))

    def test_lancamentoExigeProvaDoDono(self):
        i = self.nova(**FICHA)
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute("INSERT INTO lancamentos(ideia_id,canal,url,titulo,postado_em) VALUES(?,'show_hn','u','t',datetime('now'))", (i,))

    def test_estrelasDiariasSoDaFonteOficial(self):
        i = self.nova(**FICHA)
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(?,date('now'),5,'chute')", (i,))

    def test_hipoteseNasceAbertaEDecideComDadoCoerente(self):
        i = self.nova(**FICHA); self.ate_lancada(i)
        ins = ("INSERT INTO hipoteses(ideia_id,etapa,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,limiar_versao,prazo_dias{c}) "
               "VALUES(?,'S1','e14','contagem',10,2,14,0,1,14{v})")
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_so_por_update'):
            self.c.execute(ins.format(c=',resultado,fechada_em', v=",'confirmada',datetime('now')"), (i,))
        h = self.c.execute(ins.format(c='', v=''), (i,)).lastrowid
        upd = "UPDATE hipoteses SET resultado=?, fechada_em=datetime('now'), n_observado=14, valor_observado=? WHERE id=?"
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_sem_dado'):
            self.c.execute(upd, ('confirmada', 12, h))
        for d in range(14):   # one row per day of the window (round 1: complete data)
            self.c.execute("INSERT INTO estrelas_diarias(ideia_id,data,estrelas,fonte) VALUES(?,date('now',?),?,'stargazers_history')", (i, f'+{d} days', 12 if d == 0 else 0))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'decisao_incoerente'):
            self.c.execute(upd, ('confirmada', 4, h))
        self.c.execute(upd, ('confirmada', 12, h))
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'hipotese_imutavel'):
            self.c.execute("UPDATE hipoteses SET limiar_passa=1 WHERE id=?", (h,))

    def test_eventosNaoSeApagam(self):
        i = self.nova(**FICHA)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'evento_imutavel'):
            self.c.execute('DELETE FROM ideia_eventos WHERE ideia_id=?', (i,))


if __name__ == '__main__':
    unittest.main()
