"""Guards added after the validation round (findings #47, #59, #60, #61, #67, #77, #43, #53)."""
import sqlite3, unittest, os
SCHEMA = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')).read()
P = '"aprovo ideia#{}" chat 26/10'
FICHA = dict(trilha='W', hook='h', twist='É X, mas Y, de modo que Z', modo='solo', plataforma='web',
             horas_estimadas=25, score_json='{"demanda":7,"twist":7,"canal":7,"execucao":7,"economia":4}', advogado_em='2026-10-26 10:00:00', ai_arte_visivel=0, loot_box=0, chat_livre=0, ai_runtime=0, loop_idle=0)


def fechar_hipotese(c, hid, resultado, fechada_em="datetime('now')"):
    """Decides an open hypothesis the legal way (7.4): a metrics row for its experiment and observed values coherent with
    the result (confirmada at the pass line; refutada below it, or above it for teto). Inconclusive results need no data."""
    t, lp, lm, nmin, x = c.execute('SELECT tipo_criterio, limiar_passa, limiar_mata, n_min, experimento_id FROM hipoteses WHERE id=?', (hid,)).fetchone()
    if resultado in ('confirmada', 'refutada'):
        c.execute("INSERT OR IGNORE INTO metricas(experimento_id,data,metrica,valor,fonte) VALUES(?,date('now'),'jogadas',?,'portal_dashboard')", (x, nmin))
        v = lp if resultado == 'confirmada' else (max(lm, lp) + 1 if t == 'teto' else min(lm, lp) - 1)
        c.execute(f"UPDATE hipoteses SET resultado=?, fechada_em={fechada_em}, n_observado=?, eventos_observados=0, valor_observado=? WHERE id=?",
                  (resultado, nmin, v, hid))
    else:
        c.execute(f"UPDATE hipoteses SET resultado=?, fechada_em={fechada_em} WHERE id=?", (resultado, hid))


def _segmento(c, i, etapa):
    """The limiares segment of this stage on the idea's own platform/path (None when the stage has no limiares rows)."""
    plat, excl = c.execute('SELECT plataforma, exclusividade FROM ideias WHERE id=?', (i,)).fetchone()
    for (seg,) in c.execute('SELECT DISTINCT segmento FROM limiares WHERE etapa=? ORDER BY segmento', (etapa,)).fetchall():
        if seg in ('roblox', 'uefn') and seg != plat: continue
        if seg.startswith('poki') and excl == 'crazygames_agregadores': continue
        if seg == 'crazygames_basic' and excl != 'crazygames_agregadores': continue
        if seg == 'publisher': continue
        return seg
    return None


def passar_etapas(c, i, etapas=('W1', 'W2')):
    """Records each stage as passed the legal way: experiment, confirmed hypotheses (a copy of every limiares row of the
    stage's segment when the database has them), then decisao='passa'."""
    for etapa in etapas:
        x = c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,fim) VALUES(?,?,'portal_teste','encerrado',date('now'))", (i, etapa)).lastrowid
        seg = _segmento(c, i, etapa)
        if seg is None:
            c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,"
                      "eventos_min,limiar_versao,previsao,prazo_dias) VALUES(?,?,?,'e','m','media',3,1.5,500,0,1,3,7)",
                      (i, x, etapa))
        else:
            c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,segmento,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,"
                      "eventos_min,limiar_versao,previsao,prazo_dias) "
                      "SELECT ?,?,etapa,segmento,'e',metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,versao,limiar_passa,prazo_dias"
                      " FROM limiares l WHERE etapa=? AND segmento=? "
                      "AND versao=(SELECT MAX(versao) FROM limiares x WHERE x.etapa=l.etapa AND x.metrica=l.metrica AND x.segmento=l.segmento)",
                      (i, x, etapa, seg))
        for (hid,) in c.execute('SELECT id FROM hipoteses WHERE experimento_id=?', (x,)).fetchall():
            fechar_hipotese(c, hid, 'confirmada')
        c.execute("UPDATE experimentos SET decisao='passa' WHERE id=?", (x,))


def ligar_referencia_e_evidencia(c, i):
    """Every idea in a test needs a linked reference and an evidence row (3.2 item 4): a neutral old game + one signal."""
    c.execute("INSERT OR IGNORE INTO fontes(id,nome,plataforma,tipo,mercado,frequencia,cota_min) VALUES(900,'fixture','steam','t','todos','diaria',0)")
    cid = c.execute("INSERT INTO concorrentes(id,loja,id_loja,nome,lancado_em) VALUES(?,'steam',?,?,'2015-01-01')", (10_000_000 + i * 1000, f'ref{i}', f'Referencia{i}')).lastrowid
    c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
    sid = c.execute("INSERT INTO sinais(id,fonte_id,hash,url,url_status,trecho_literal,tipo,payload_json) VALUES(?,900,?,'u',200,?,'hit_plataforma','{\"sha256\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"date\":\"d\"}')", (10_000_000 + i * 1000, f'fx{i}', 'x' * 40)).lastrowid
    c.execute("INSERT INTO evidencias VALUES(?,?,1,1,NULL)", (i, sid))


class Base(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(':memory:'); self.c.executescript(SCHEMA)
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('prototipo_horas_max_w','30','seed'),('prototipo_horas_max_s','50','seed'),('prototipo_horas_max_m','30','seed'),('prototipo_horas_max_r','20','seed'),('tendencia_reviews_min','1000','seed'),('tendencia_ccu_min','1000','seed'),('tendencia_plays_min','100000','seed')")

    def nova(self, genero='g', sem_vinculos=False, **cols):
        i = self.c.execute('INSERT INTO ideias(titulo,genero_central) VALUES(?,?)', ('t', genero)).lastrowid
        if not sem_vinculos:
            ligar_referencia_e_evidencia(self.c, i)
        self.mover(i, 'candidata'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (i, i))
        if cols:
            self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in cols) + ' WHERE id=?', list(cols.values()) + [i])
        return i

    def passar(self, i):
        passar_etapas(self.c, i)

    def mover(self, i, para, ator='rotina', prova=None, motivo='t', **cols):
        de = self.c.execute('SELECT estado FROM ideias WHERE id=?', (i,)).fetchone()[0]
        try:
            self.c.execute('SAVEPOINT s')
            self.c.execute('INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,?,?,?,?,?)', (i, de, para, motivo, ator, prova))
            if para == 'arquivada': cols.setdefault('arquivamento', 'resultado')
            sets = ', '.join([f'{k}=?' for k in cols] + ['estado=?'])
            self.c.execute(f'UPDATE ideias SET {sets} WHERE id=?', list(cols.values()) + [para, i])
            self.c.execute('RELEASE s'); return None
        except sqlite3.IntegrityError as e:
            self.c.execute('ROLLBACK TO s'); self.c.execute('RELEASE s'); return str(e)


class Guards(Base):
    def test_ideiaComLootBoxPodeSerGravadaEMortaMasNaoTestada(self):
        i = self.nova(**dict(FICHA, loot_box=1))
        self.assertIn('excluida_por_regra', self.mover(i, 'em_teste'))
        self.assertIn('excluida_por_regra', self.mover(i, 'morta', motivo_morte='twist_cosmetico'))
        self.assertIsNone(self.mover(i, 'morta', motivo_morte='excluida_por_regra'))

    def test_semFichaNaoEntraEmTeste(self):
        i = self.nova(trilha='W')
        self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))
        j = self.nova(**FICHA)
        self.assertIsNone(self.mover(j, 'em_teste'))

    def test_semAdvogadoNaoEntraEmTeste(self):
        f = dict(FICHA); f.pop('advogado_em')
        i = self.nova(**f)
        self.assertIn('advogado_obrigatorio', self.mover(i, 'em_teste'))

    def test_trilhaTravadaMesmoDepoisDeReaberta(self):
        i = self.nova(**dict(FICHA, trilha='S', plataforma='steam'))
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,'candidata','candidata','liberação','dono',?)", (i, f'"libero a aposta Steam da ideia#{i}" chat'))
        self.mover(i, 'pre_teste'); self.mover(i, 'arquivada', reabrir_se='x')
        self.mover(i, 'candidata', motivo='REABERTA: x')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'trilha_imutavel'):
            self.c.execute("UPDATE ideias SET trilha='W' WHERE id=?", (i,))

    def test_ideiaLigadaATendenciaFechadaNaoEntraEmTeste(self):
        i = self.nova(**dict(FICHA, fonte_ideia='tendencia'))
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('roblox','42',date('now','-30 days'))")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (i,))
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja,status) VALUES('hype','roblox','42','fechada')")
        self.assertIn('janela_fechada', self.mover(i, 'em_teste'))

    def test_ideiaLigadaATendenciaPrecisaSerRotuladaTendencia(self):
        i = self.nova(**dict(FICHA, fonte_ideia='arbitragem'))
        self.c.execute("INSERT INTO concorrentes(loja,id_loja,lancado_em) VALUES('roblox','42',date('now','-30 days'))")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (i,))
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja) VALUES('hype','roblox','42')")
        self.assertIn('fonte_ideia_tendencia', self.mover(i, 'em_teste'))

    def test_exploracaoArquivadaSemTesteNaoQueimaACotaDoMes(self):
        a = self.nova(genero='a', **FICHA)
        self.c.execute("UPDATE ideias SET exploracao=1, exploracao_em=date('now'), fonte_ideia='exploracao' WHERE id=?", (a,))
        self.mover(a, 'arquivada', reabrir_se='x')
        b = self.nova(genero='b', **FICHA)
        self.c.execute("UPDATE ideias SET exploracao=1, exploracao_em=date('now'), fonte_ideia='exploracao' WHERE id=?", (b,))

    def test_exploracaoQueChegouATesteQueimaACota(self):
        a = self.nova(genero='a', **FICHA)
        fid = self.c.execute("INSERT INTO fontes(nome,plataforma,tipo,mercado,frequencia,cota_min) VALUES('itch','itch','t','todos','diaria',0)").lastrowid
        sid = self.c.execute("INSERT INTO sinais(fonte_id,hash,url,url_status,trecho_literal,tipo,payload_json) VALUES(?,'j','u',200,?,'jam_mecanica','{\"sha256\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"date\":\"d\"}')", (fid, 'x' * 40)).lastrowid
        self.c.execute('INSERT INTO evidencias VALUES(?,?,1,1,NULL)', (a, sid))
        self.c.execute("UPDATE ideias SET exploracao=1, exploracao_em=date('now'), fonte_ideia='exploracao' WHERE id=?", (a,))
        self.mover(a, 'em_teste'); self.mover(a, 'arquivada', reabrir_se='x')
        b = self.nova(genero='b', **FICHA)
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'cota_exploracao'):
            self.c.execute("UPDATE ideias SET exploracao=1, exploracao_em=date('now'), fonte_ideia='exploracao' WHERE id=?", (b,))

    def test_sinalComHttp200ExigePayload(self):
        self.c.execute("INSERT INTO fontes(nome,plataforma,tipo,mercado,frequencia,cota_min) VALUES('f','p','t','todos','diaria',0)")
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'CHECK'):
            self.c.execute("INSERT INTO sinais(fonte_id,hash,url,url_status,trecho_literal,tipo) VALUES(1,'h','u',200,?, 'hit_plataforma')", ('x' * 40,))

    def test_motivoLoopVazioExisteEPrazoNao(self):
        i = self.nova(**FICHA)
        self.assertIsNone(self.mover(i, 'morta', motivo_morte='loop_vazio'))
        j = self.nova(genero='z', **FICHA)
        self.assertIn('CHECK', self.mover(j, 'morta', motivo_morte='prazo'))

    def test_metricaSalasAbertasETamanhoSala(self):
        self.c.execute("INSERT INTO ideias(titulo,tamanho_sala) VALUES('x',4)")
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(1,'E5','pos_lancamento','rodando')")
        self.c.execute("INSERT INTO metricas(experimento_id,data,metrica,valor,fonte) VALUES(1,'2026-10-26','salas_abertas_pico',6,'telemetria')")


if __name__ == '__main__':
    unittest.main()
