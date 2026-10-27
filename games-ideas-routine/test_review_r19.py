"""Review round 19 (family with a newer sibling, 'recriada' laundering, fonte_ideia lock, rival inside the reference
name, idle 'sinal', closed trend on S3/S4, portal stores without a snapshot source)."""
import sqlite3, unittest
from test_guards_v2 import Base, ligar_referencia_e_evidencia
from test_review_r1 import FICHA_OK
from test_queries import queries
from test_queries_v2 import db_sem_travas


class GuardsR19(Base):
    def test_ideiaMaisVelhaHerdaFamiliaDaIrmaMaisNovaViva(self):
        a = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('A','roguelite')").lastrowid   # still in 'sinal'
        b = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('B','roguelite')").lastrowid
        ligar_referencia_e_evidencia(self.c, b); self.mover(b, 'candidata'); self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (b, b))
        ref = self.c.execute("SELECT concorrente_id FROM ideia_concorrentes WHERE ideia_id=?", (b,)).fetchone()[0]
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'referencia')", (a, ref))
        self.mover(a, 'candidata')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'familia_errada'):
            self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (a, a))
        self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (b, a))

    def test_recriadaSoEmArquivamentoOperacional(self):
        i = self.nova(**FICHA_OK); self.mover(i, 'em_teste'); self.mover(i, 'morta', motivo_morte='teste_reprovado')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'recriada_so_operacional'):
            self.c.execute("UPDATE ideias SET reabrir_se='recriada como ideia#99' WHERE id=?", (i,))
        j = self.nova(**FICHA_OK)
        self.assertIsNone(self.mover(j, 'arquivada', reabrir_se=f'recriada como ideia#{j + 1}', arquivamento='operacional'))

    def test_fonteIdeiaTravaDepoisDaCandidata(self):
        i = self.nova(**dict(FICHA_OK, fonte_ideia='arbitragem')); self.mover(i, 'em_teste')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'fonte_ideia_imutavel'):
            self.c.execute("UPDATE ideias SET fonte_ideia='tendencia' WHERE id=?", (i,))

    def test_rivalContidoNoNomeDaReferenciaNaoBloqueia(self):
        i = self.nova(**dict(FICHA_OK, twist='É Referencia{} II, mas Y, de modo que Z'))
        self.c.execute("UPDATE concorrentes SET nome=nome || ' II' WHERE id IN (SELECT concorrente_id FROM ideia_concorrentes WHERE ideia_id=?)", (i,))
        self.c.execute("UPDATE ideias SET twist=? WHERE id=?", (f'É Referencia{i} II, mas Y, de modo que Z', i))
        rid = self.c.execute("INSERT INTO concorrentes(loja,id_loja,nome,lancado_em) VALUES('steam','prev',?,'2018-01-01')", (f'Referencia{i}',)).lastrowid
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(?,?,'rival')", (i, rid))
        self.assertIsNone(self.mover(i, 'em_teste'))

    def test_sinalParadoPodeSerArquivado(self):
        i = self.c.execute("INSERT INTO ideias(titulo,genero_central) VALUES('s','g')").lastrowid
        self.assertIsNone(self.mover(i, 'arquivada', reabrir_se='2ª plataforma com sinal', arquivamento='operacional'))


class QueriesR19(unittest.TestCase):
    def setUp(self):
        self.c = db_sem_travas()

    def test_sinaisParadosEnvelhecem(self):
        self.c.execute("INSERT INTO config VALUES('sinal_max_dias','30','seed',datetime('now'))")
        self.c.execute("INSERT INTO ideias(id,titulo,estado,criada_em) VALUES(1,'a','sinal',datetime('now','-40 days')),(2,'b','sinal',datetime('now','-5 days'))")
        self.assertEqual([r[0] for r in self.c.execute(queries()['q_sinais_parados'])], [1])

    def test_tendenciaFechadaNaoPegaS3DeIdeiaEmConstrucao(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'s','em_construcao')")
        self.c.execute("INSERT INTO concorrentes(id,loja,id_loja,lancado_em) VALUES(1,'steam','h',date('now','-30 days'))")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        self.c.execute("INSERT INTO tendencias(nome,loja,id_loja,status,fechada_em) VALUES('t','steam','h','fechada',date('now'))")
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(1,'S3','next_fest','planejado')")
        self.assertEqual(self.c.execute(queries()['q_tendencia_fechada_planejados']).fetchall(), [])

    def test_lojaSemFonteDeSnapshotNaoTravaChecklist(self):
        self.c.execute("INSERT INTO ideias(id,titulo,estado) VALUES(1,'a','candidata')")
        self.c.execute("INSERT INTO concorrentes(id,loja,id_loja,lancado_em) VALUES(1,'poki','p','2025-01-01')")
        self.c.execute("INSERT INTO ideia_concorrentes(ideia_id,concorrente_id,papel) VALUES(1,1,'referencia')")
        cur = self.c.execute(queries()['q_checklist']); cols = [d[0] for d in cur.description]
        self.assertEqual(cur.fetchone()[cols.index('concorrentes_sem_foto')], 0)


if __name__ == '__main__':
    unittest.main()
