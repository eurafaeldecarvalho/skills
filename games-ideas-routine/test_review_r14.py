"""Review round 14 (findings #1, #2, #4, #5, #7)."""
import sqlite3, unittest
from test_guards_v2 import Base
from test_queries import queries
from test_queries_v2 import db_sem_travas


class QueriesR14(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()
        self.c.execute("INSERT INTO config VALUES('candidata_pendente_dias','14','seed',datetime('now')),('candidata_fila_dias','60','seed',datetime('now'))")

    def test_filaSteamContaDaLiberacao(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,trilha,atualizada_em) VALUES(1,'s','candidata',31,'S',datetime('now','-70 days'))")
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(1,'candidata','candidata','LIBERACAO_STEAM: x','dono','\"libero a aposta Steam da ideia#1\" chat')")
        self.assertEqual(self.c.execute(queries()['q_candidatas_paradas']).fetchall(), [])

    def test_semVagaSoComFilaCheia(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado,score,trilha,atualizada_em) VALUES(1,'w','candidata',31,'W',datetime('now','-70 days'))")
        self.assertEqual(self.c.execute(queries()['q_candidatas_paradas']).fetchall(), [])   # 4 pre_teste slots free
        for k in range(2, 6):
            self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(?,'q','pre_teste')", (k,))
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_candidatas_paradas'])], [1])

    def test_pendenciaCanceladaSaiDaLista(self):
        self.c.execute("INSERT INTO pendencias(texto,cancelada_em,motivo_cancelamento) VALUES('prototipo ideia#1',datetime('now'),'ideia arquivada')")
        self.assertEqual(self.c.execute(queries()['q_pendencias_abertas']).fetchall(), [])


class GuardsR14(Base):
    def test_jogoProprioNaoFazFamiliaEntrePortEGraduacao(self):
        own = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em,proprio_ideia_id) VALUES('crazygames','own','Meu Jogo','2026-01-01',NULL)").lastrowid
        a = self.c.execute("INSERT INTO ideias(titulo,genero_central,familia_id) VALUES('port','deck',NULL)").lastrowid
        from test_review_r4 import jogo_lancado
        self.c.execute("UPDATE concorrentes SET proprio_ideia_id=? WHERE id=?", (jogo_lancado(self.c), own))   # round 15: a launched idea
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (a, own))
        self.mover(a, 'candidata'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, a))
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('grad','deck')").lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (b, own))
        self.mover(b, 'candidata')
        self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (b, b))   # own family allowed

    def test_robloxJaPopularNoPrimeiroSnapshotNaoEhTendencia(self):
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('roblox','old','Velho',date('now','-300 days'))").lastrowid
        # round 16: top-trending itself is an observed rise; a game first seen popular by CCU is not
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,ccu) VALUES(?,date('now'),'global',5000)", (cid,))
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM v_tendencia_viva').fetchone()[0], 0)

    def test_robloxQueSubiuDiantedeNosEhTendencia(self):
        cid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('roblox','sab','Brainrot',date('now','-144 days'))").lastrowid
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,ccu) VALUES(?,date('now','-40 days'),'global',200)", (cid,))
        self.c.execute("INSERT INTO concorrente_snapshots(concorrente_id,data,pais,rank_lista,rank_pos) VALUES(?,date('now','-20 days'),'global','top-trending',1)", (cid,))
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM v_tendencia_viva').fetchone()[0], 1)

    def test_tendenciaGuardaDataDeFechamento(self):
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja,status,fechada_em) VALUES('t','roblox','x','fechada',date('now'))")


if __name__ == '__main__':
    unittest.main()
