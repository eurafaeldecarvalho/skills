"""Review round 30 (owner reopening recorded when it arrives, UEFN null reading is determined, reading grace period
in the deadline)."""
import unittest
from test_guards_v2 import Base, ligar_referencia_e_evidencia
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


class GuardsR30(Base):
    def test_reabroDoDonoGravadoNaChegadaCobreAEntradaDeDomingo(self):
        a = self.nova(genero='deck', **FICHA_OK)
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('b','deck')").lastrowid
        ligar_referencia_e_evidencia(self.c, b); self.mover(b, 'candidata')
        self.c.execute('DROP TRIGGER trg_familia_escolha'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, b))
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in FICHA_OK) + ' WHERE id=?', list(FICHA_OK.values()) + [b])
        self.mover(b, 'pre_teste')
        self.mover(a, 'em_teste'); self.mover(a, 'morta', motivo_morte='advogado_do_diabo')   # the sibling dies while b waits
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,'pre_teste','pre_teste','REABERTA: dono','dono',?)",
                       (b, f'"reabro a ideia#{b}" chat terça'))   # recorded the day it arrives
        self.assertIsNone(self.mover(b, 'em_teste'))   # Sunday, by the routine

    def test_ilhaUefnComLeituraNulaEhDeterminada(self):
        i = self.nova(**dict(FICHA_OK, trilha='R', plataforma='uefn', horas_estimadas=15))
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('uefn','1111-2222-3333','Ilha',date('now','-30 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais) VALUES(?,date('now'),'global')", (cid,))
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'rival')", (i, cid))
        self.assertIsNone(self.mover(i, 'em_teste'))


class QueriesR30(unittest.TestCase):
    def test_prazoSoSeEsgotaDepoisDaCarencia(self):
        c = db_sem_travas()
        c.execute("INSERT INTO config VALUES('leitura_carencia_dias','7','seed',datetime('now'))")
        c.execute("INSERT INTO ideias(id,titulo) VALUES(1,'s')")
        c.execute("INSERT INTO experimentos(id,ideia_id,etapa,tipo,estado,inicio) VALUES(1,1,'S1','pagina_steam','rodando',date('now','-15 days'))")
        c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,"
                  "limiar_versao,previsao,prazo_dias) VALUES(1,1,'S1','e','wishlists_14d','contagem',201,20,14,0,1,250,14)")
        cur = c.execute(queries()['q_hipoteses_abertas']); cols = [d[0] for d in cur.description]
        self.assertEqual(cur.fetchone()[cols.index('prazo_esgotado')], 0)
        c.execute("UPDATE experimentos SET inicio=date('now','-22 days') WHERE id=1")
        cur = c.execute(queries()['q_hipoteses_abertas'])
        self.assertEqual(cur.fetchone()[cols.index('prazo_esgotado')], 1)


if __name__ == '__main__':
    unittest.main()
