"""Review round 18 (curly quotes, guards anchored on the current cycle, second reopening reaches the owner)."""
import sqlite3, unittest
from test_guards_v2 import Base
from test_review_r1 import FICHA_OK
from test_review_r15 import hipotese
from test_queries import queries
from test_queries_v2 import db_sem_travas


class AspasR18(Base):
    def test_aspasCurvasValemComoRetas(self):
        i = self.nova(**FICHA_OK)
        self.assertIsNone(self.mover(i, 'em_construcao', 'dono', f'“Construo sem teste de comportamento a ideia#{i}” chat 27/10',
                                     engine='p', engine_justificativa='j'))

    def test_liberacaoSteamComAspasCurvas(self):
        i = self.nova(**dict(FICHA_OK, trilha='S', plataforma='steam', horas_estimadas=40))
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,'candidata','candidata','LIBERACAO_STEAM: x','dono',?)",
                       (i, f'“libero a aposta Steam da ideia#{i}” chat'))
        self.assertIsNone(self.mover(i, 'pre_teste'))


class CicloR18(Base):
    def reabrir(self, i):
        self.mover(i, 'arquivada', reabrir_se='x', arquivamento='operacional')
        self.mover(i, 'candidata', motivo='REABERTA: x [sinal#1]')
        self.c.execute('UPDATE ideias SET ' + ','.join(f'{k}=?' for k in FICHA_OK) + ' WHERE id=?', list(FICHA_OK.values()) + [i])

    def test_reabertaRecuperaAIteracaoDoCrazyGames(self):
        i = self.nova(genero='idle', **dict(FICHA_OK, exclusividade='crazygames_agregadores')); self.mover(i, 'em_teste')
        for _ in range(2):   # previous cycle: the test and its iteration, both expired unrun
            x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,decisao,criado_em) VALUES(?,'W1','portal_teste','encerrado','planejado_vencido',datetime('now','-80 days'))", (i,)).lastrowid
            self.c.execute("INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,n_min,"
                           "eventos_min,limiar_versao,previsao,prazo_dias,resultado,criada_em,fechada_em) VALUES(?,?,'W1','e','aceite_plataforma','contagem',1,-1,1,1,1,1,21,"
                           "'inconclusiva_amostra_parcial',datetime('now','-80 days'),datetime('now','-10 days'))", (i, x))   # created before the reopening
        self.reabrir(i); self.mover(i, 'em_teste')
        x = self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(?,'W1','portal_teste','planejado')", (i,)).lastrowid
        hipotese(self.c, i, x, 'W1', 'aceite_plataforma', None)

    def test_reabertaPodeTrocarPortalPeloBuild(self):
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('poki_build_mb_max','5','seed'),('tempo_gameplay_s_max','10','seed')")
        i = self.nova(**dict(FICHA_OK, exclusividade='poki')); self.mover(i, 'em_teste')
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado,inicio,fim,decisao,criado_em) VALUES(?,'W1','portal_teste','encerrado',date('now','-30 days'),date('now','-20 days'),'mata',datetime('now','-31 days'))", (i,))
        self.reabrir(i); self.mover(i, 'em_teste')
        self.c.execute('UPDATE ideias SET build_mb=11 WHERE id=?', (i,))
        self.c.execute("UPDATE ideias SET exclusividade='crazygames_agregadores' WHERE id=?", (i,))


class QueriesR18(unittest.TestCase):
    def test_segundaReaberturaApareceParaPedirAoDono(self):
        c = db_sem_travas()
        c.execute("INSERT INTO ideias(id,titulo,estado,reabrir_se) VALUES(1,'a','arquivada','cond2')")
        c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator) VALUES(1,'arquivada','candidata','REABERTA: cond','rotina')")
        cur = c.execute(queries()['q_reabrir_candidatas'])
        cols = [d[0] for d in cur.description]; rows = cur.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][cols.index('ja_reaberta_pela_rotina')], 1)


if __name__ == '__main__':
    unittest.main()
