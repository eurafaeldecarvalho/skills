"""Review round 32 (an owner same-state event is not a new entry in candidata, a same-platform clone where trends are
not allowed freezes, arbitrage gap counted only off the proof platforms)."""
import unittest
from test_guards_v2 import Base, ligar_referencia_e_evidencia
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


class GuardsR32(Base):
    def test_liberacaoSteamDepoisDoReabroNaoInvalidaAReabertura(self):
        a = self.nova(genero='coop', **FICHA_OK); self.mover(a, 'em_teste'); self.mover(a, 'morta', motivo_morte='teste_reprovado')
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('b','coop')").lastrowid
        ligar_referencia_e_evidencia(self.c, b); self.mover(b, 'candidata')
        self.c.execute('DROP TRIGGER trg_familia_escolha'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, b))
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in FICHA_OK) + ", trilha='S', plataforma='steam', horas_estimadas=40 WHERE id=?",
                       list(FICHA_OK.values()) + [b])
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,'candidata','candidata','REABERTA: dono','dono',?)", (b, f'"reabro a ideia#{b}" chat'))
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,'candidata','candidata','LIBERACAO_STEAM: x','dono',?)", (b, f'"libero a aposta Steam da ideia#{b}" chat'))
        self.assertIsNone(self.mover(b, 'pre_teste'))

    def test_cloneNaSteamDeHitRecenteCongelaAteATravaCair(self):
        i = self.nova(sem_vinculos=True, **dict(FICHA_OK, trilha='S', plataforma='steam', horas_estimadas=40))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','h','Hit',date('now','-70 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,reviews_total) VALUES(?,date('now'),'global',4000)", (cid,))
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (i, cid))
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja) VALUES('h','steam','h')")
        self.assertIsNone(self.mover(i, 'congelada', data_reativacao='2027-01-01'))


class QueriesR32(unittest.TestCase):
    def test_lacunaDeArbitragemNaMesmaPlataformaNaoConta(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'i')")
        c.execute("INSERT INTO fontes(id,nome,plataforma,tipo,mercado,frequencia,cota_min) VALUES(1,'a','steam','t','todos','diaria',0),(2,'b','steam','t','todos','diaria',0)")
        for k, (f, t) in enumerate([(1, 'hit_plataforma'), (2, 'arbitragem')], start=1):
            c.execute("INSERT INTO sinais(id,fonte_id,hash,url,url_status,trecho_literal,tipo,payload_json) VALUES(?,?,?,'u',200,?,?,?)",
                      (k, f, f'h{k}', 'x' * 40, t, '{"sha256":"' + 'a' * 64 + '","date":"d"}'))
            c.execute("INSERT INTO evidencias VALUES(1,?,1,1,NULL)", (k,))
        cur = c.execute(queries()['q_fontes_distintas_por_ideia']); cols = [d[0] for d in cur.description]
        self.assertEqual(cur.fetchone()[cols.index('plataformas_arbitragem')], 0)


if __name__ == '__main__':
    unittest.main()
