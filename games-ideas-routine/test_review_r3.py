"""Review round 3 (findings #1-#6, #11-#14, #16, #17)."""
import json, sqlite3, unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_review_r2 import hipotese
from test_queries import queries
from test_queries_v2 import db_sem_travas

CFG = [('prototipo_horas_max_w', '30'), ('prototipo_horas_max_s', '50'), ('prototipo_horas_max_m', '30'), ('prototipo_horas_max_r', '20')]


class GuardsR3(Base):
    def sinal(self, tipo, fonte='f'):
        self.c.execute("INSERT OR IGNORE INTO fontes(nome,plataforma,tipo,mercado,frequencia,cota_min) VALUES(?,?,'t','todos','diaria',0)", (fonte, fonte))
        fid = self.c.execute('SELECT id FROM fontes WHERE nome=?', (fonte,)).fetchone()[0]
        return self.c.execute("INSERT INTO sinais(fonte_id,hash,url,url_status,trecho_literal,tipo,payload_json) VALUES(?,?,'u',200,?,?,'{\"sha256\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"date\":\"d\"}')",
                              (fid, f'h{tipo}{fonte}{id(self)}', 'x' * 40, tipo)).lastrowid

    def test_sinalDeCoorteCompartilhadoNaoFazFamilia(self):
        coorte = self.sinal('tag_coorte')
        a = self.nova(genero='deck', **FICHA_OK); b_hit = self.sinal('hit_plataforma', 'g')
        self.c.execute('INSERT INTO evidencias VALUES(?,?,1,1,NULL)', (a, coorte))
        self.c.execute('INSERT INTO evidencias VALUES(?,?,1,1,NULL)', (a, self.sinal('hit_plataforma', 'h')))
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('b','deck')").lastrowid
        for s in (coorte, b_hit): self.c.execute('INSERT INTO evidencias VALUES(?,?,1,1,NULL)', (b, s))
        self.mover(b, 'candidata')
        self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (b, b))   # own family must be allowed

    def test_fallbackCrazyGamesSemAmostraMantemARecusa(self):   # round 20: spec changed (was 'PodeArquivar')
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        hipotese(self.c, i, 'W1', 'refutada', estendida=1)
        hipotese(self.c, i, 'W1', 'inconclusiva_sem_trafego')    # the CrazyGames fallback ended without a reading
        self.assertIn('refutada_exige_morte', self.mover(i, 'arquivada', reabrir_se='x'))
        self.assertIsNone(self.mover(i, 'morta', motivo_morte='teste_reprovado'))

    def test_trilhaEPlataformaCoerentes(self):
        i = self.nova(**dict(FICHA_OK, trilha='W', plataforma='steam'))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))

    def test_trilhaSExigeLancadaWOuLiberacaoDoDono(self):
        i = self.nova(**dict(FICHA_OK, trilha='S', plataforma='steam'))
        self.assertIn('aposta_steam_nao_liberada', self.mover(i, 'pre_teste'))
        self.assertIsNone(self.mover(i, 'pre_teste', 'dono', f'"libero a aposta Steam da ideia#{i}" chat'))

    def test_concorrenteLigadoSemLancadoEmBarraTeste(self):
        i = self.nova(**FICHA_OK)
        self.c.execute("INSERT INTO concorrentes(loja,id_loja) VALUES('steam','1')")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,(SELECT MIN(id) FROM concorrentes WHERE id_loja NOT LIKE 'ref%'),'referencia')", (i,))
        self.assertIn('concorrente_sem_lancado_em', self.mover(i, 'em_teste'))

    def test_eixoForaDaEscalaOuAbaixoDoMinimoBarra(self):
        for sj in ('{"demanda":5,"twist":7,"canal":7,"execucao":7,"economia":4}', '{"demanda":4,"twist":7,"canal":7,"execucao":7,"economia":4}'):
            i = self.nova(genero=f'g{len(sj)}{sj[11]}', **dict(FICHA_OK, score_json=sj))
            self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))

    def test_horasAcimaDoTetoDaTrilhaBarra(self):
        i = self.nova(**dict(FICHA_OK, horas_estimadas=900))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))

    def test_fonteExploracaoExigeFlagExploracao(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='exploracao'))
        self.assertIn('ficha_incompleta', self.mover(i, 'em_teste'))

    def test_hipoteseDecididaEImutavelEEventoNaoApaga(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste')
        hipotese(self.c, i, 'R1', 'refutada')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'hipotese_decidida_imutavel'):
            self.c.execute("UPDATE hipoteses SET resultado='inconclusiva_amostra_parcial'")
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'eventos_imutaveis'):
            self.c.execute('DELETE FROM ideia_eventos')

    def test_aprovacaoDeConstrucaoNaoExigeReaberturaPorMorteDeIrmaPosterior(self):
        a = self.nova(genero='merge', **FICHA_OK); self.mover(a, 'em_teste')
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now','+1 second') WHERE id=?", (a,)); self.passar(a); self.mover(a, 'validada')
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central,familia_id) VALUES('b','merge',NULL)").lastrowid
        self.mover(b, 'candidata'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (b, b))
        self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, a))
        # force b into a's family through the graveyard path: b dies seriously in a's family
        self.c.execute('DROP TRIGGER trg_familia_fixa'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, b))
        self.mover(b, 'morta', motivo_morte='advogado_do_diabo')
        self.assertIsNone(self.mover(a, 'em_construcao', 'dono', f'"aprovo a construção da ideia#{a}" chat', engine='p', engine_justificativa='j'))

    def test_reaberturaZeraScoreEAdvogado(self):
        i = self.nova(**dict(FICHA_OK, score=30)); self.mover(i, 'arquivada', reabrir_se='x')
        self.mover(i, 'candidata', motivo='REABERTA: x')
        self.assertEqual(self.c.execute('SELECT score, score_json, advogado_em FROM ideias WHERE id=?', (i,)).fetchone(), (None, None, None))


class QueriesR3(unittest.TestCase):
    def test_tendenciaComBaseZeroNaoDobra(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','candidata')")
        c.execute("INSERT INTO concorrentes(id,loja,id_loja,lancado_em) VALUES(1,'steam','9','2023-01-01')")
        c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,ccu) VALUES(1,date('now','-20 days'),'global',0),(1,date('now'),'global',0)")
        cols = [d[0] for d in c.execute(queries()['q_checklist']).description]
        self.assertEqual(c.execute(queries()['q_checklist']).fetchone()[cols.index('tendencias_nao_registradas')], 0)

    def test_experimentoDeOntemNaoContaComoSemLeitura(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'a')")
        c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,inicio) VALUES(1,'S1','pagina_steam','rodando',date('now','-1 day'))")
        cols = [d[0] for d in c.execute(queries()['q_checklist']).description]
        self.assertEqual(c.execute(queries()['q_checklist']).fetchone()[cols.index('experimentos_sem_leitura_7d')], 0)

    def test_plataformasContaSoSinaisDeProva(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'i')")
        c.execute("INSERT INTO fontes(id,nome,plataforma,tipo,mercado,frequencia,cota_min) VALUES(1,'a','steam','t','todos','diaria',0),(2,'b','youtube','t','todos','diaria',0)")
        for i, (f, t) in enumerate([(1, 'hit_plataforma'), (1, 'hit_plataforma'), (2, 'reclamacao')], start=1):
            c.execute("INSERT INTO sinais(id,fonte_id,hash,url,url_status,trecho_literal,tipo,payload_json) VALUES(?,?,?,'u',200,?,?,'{\"sha256\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"date\":\"d\"}')", (i, f, f'h{i}', 'x' * 40, t))
            c.execute("INSERT INTO evidencias VALUES(1,?,1,1,NULL)", (i,))
        self.assertEqual(c.execute(queries()['q_fontes_distintas_por_ideia']).fetchone()[1], 1)


if __name__ == '__main__':
    unittest.main()
