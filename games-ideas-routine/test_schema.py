import sqlite3, unittest, os
from test_guards_v2 import passar_etapas, ligar_referencia_e_evidencia
SCHEMA = open(os.path.join(os.path.dirname(__file__), 'schema.sql')).read()
P = '"aprovo a construção da ideia#1" chat 26/10 21:00'
SJ = '{"demanda":7,"twist":7,"canal":7,"execucao":7,"economia":4}'

class Engine(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(':memory:'); self.c.executescript(SCHEMA)
        self.c.execute("INSERT INTO config(chave,valor,origem) VALUES('prototipo_horas_max_w','30','seed'),('prototipo_horas_max_s','50','seed'),('prototipo_horas_max_m','30','seed'),('prototipo_horas_max_r','20','seed')")
        self.c.execute("INSERT INTO ideias(titulo,genero_central,trilha) VALUES('i1','bullet_heaven','W')")
        ligar_referencia_e_evidencia(self.c, 1)
        self.c.execute("UPDATE ideias SET hook='h', twist='É X, mas Y, de modo que Z', modo='solo', plataforma='web', horas_estimadas=25, score_json=?, ai_arte_visivel=0, loot_box=0, chat_livre=0, ai_runtime=0, loop_idle=0, advogado_em='2026-10-26 10:00:00' WHERE id=1", (SJ,))
        self.mover('candidata'); self.c.execute("UPDATE ideias SET familia_id=1 WHERE id=1")
        self.mover('pre_teste'); self.mover('em_teste')
        self.c.execute("UPDATE ideias SET advogado_em=datetime('now','+1 second') WHERE id=1")
        passar_etapas(self.c, 1); self.mover('validada')

    def mover(self, para, ator='rotina', prova=None):
        de = self.c.execute('SELECT estado FROM ideias WHERE id=1').fetchone()[0]
        self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(1,?,?,'t',?,?)", (de, para, ator, prova))
        self.c.execute('UPDATE ideias SET estado=? WHERE id=1', (para,))

    def test_deveBarrarConstrucaoSemEngine(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'engine_obrigatoria'):
            self.mover('em_construcao', 'dono', P)

    def test_deveBarrarConstrucaoComEngineSemJustificativa(self):
        self.c.execute("UPDATE ideias SET engine='godot' WHERE id=1")
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'engine_obrigatoria'):
            self.mover('em_construcao', 'dono', P)

    def test_devePermitirConstrucaoComEngineJustificada(self):
        self.c.execute("UPDATE ideias SET engine='godot', engine_justificativa='2D, export web+Steam, GodotSteam' WHERE id=1")
        self.mover('em_construcao', 'dono', P)
        self.assertEqual(self.c.execute('SELECT estado FROM ideias').fetchone()[0], 'em_construcao')

class Criterio(unittest.TestCase):
    def test_limiarAceitaCriterioMedia(self):
        c = sqlite3.connect(':memory:'); c.executescript(SCHEMA)
        c.execute("""INSERT INTO limiares(etapa,metrica,segmento,tipo_criterio,limiar_passa,limiar_mata,n_min,eventos_min,prazo_dias,
          unidade_n,marco_inicio,sem_amostra_destino,mata_destino,versao,vigente_desde,origem)
          VALUES('W1','minutos_por_jogador','crazygames','media',10,5,500,0,21,'jogadores_novos','publicacao','arquivada','morta',1,'2026-10-26','benchmark')""")

    def test_hipoteseAceitaCriterioTeto(self):
        c = sqlite3.connect(':memory:'); c.executescript(SCHEMA)
        c.execute("INSERT INTO ideias(titulo) VALUES('i')")
        c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(1,'M1','cpi_teste','planejado')")
        c.execute("""INSERT INTO hipoteses(ideia_id,experimento_id,etapa,enunciado,metrica,tipo_criterio,limiar_passa,limiar_mata,
          n_min,eventos_min,limiar_versao,previsao,prazo_dias) VALUES(1,1,'M1','cpi','cpi_usd','teto',0.4,0.6,300,0,1,0.35,6)""")


def nova_ideia(c, i, trilha, genero):
    if not c.execute("SELECT 1 FROM config WHERE chave='prototipo_horas_max_w'").fetchone():
        c.execute("INSERT INTO config(chave,valor,origem) VALUES('prototipo_horas_max_w','30','seed'),('prototipo_horas_max_s','50','seed'),('prototipo_horas_max_m','30','seed'),('prototipo_horas_max_r','20','seed')")
    c.execute("INSERT INTO ideias(titulo,genero_central,trilha) VALUES(?,?,?)", (f'i{i}', genero, trilha))
    ligar_referencia_e_evidencia(c, i)
    c.execute("UPDATE ideias SET hook='h', twist='É X, mas Y, de modo que Z', modo='solo', plataforma='web', horas_estimadas=25, score_json=?, ai_arte_visivel=0, loot_box=0, chat_livre=0, ai_runtime=0, loop_idle=0, advogado_em='2026-10-26 10:00:00' WHERE id=?", (SJ, i))

def mover(c, i, para, ator='rotina', prova=None):
    de = c.execute('SELECT estado FROM ideias WHERE id=?', (i,)).fetchone()[0]
    c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,?,?,'t',?,?)", (i, de, para, ator, prova))
    c.execute('UPDATE ideias SET estado=?, arquivamento=COALESCE(arquivamento, CASE WHEN ?=\'arquivada\' THEN \'resultado\' END) WHERE id=?', (para, para, i))


class UmaApostaSteam(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(':memory:'); self.c.executescript(SCHEMA)
        for i, (trilha, genero) in enumerate([('S', 'roguelite'), ('S', 'colony_sim'), ('W', 'merge')], start=1):
            nova_ideia(self.c, i, trilha, genero); mover(self.c, i, 'candidata')
            self.c.execute('UPDATE ideias SET familia_id=? WHERE id=?', (i, i))
            if trilha == 'S':
                self.c.execute("UPDATE ideias SET plataforma='steam' WHERE id=?", (i,))
                self.c.execute("INSERT INTO ideia_eventos(ideia_id,de,para,motivo,ator,prova_dono) VALUES(?,'candidata','candidata','liberação','dono',?)",
                               (i, f'"libero a aposta Steam da ideia#{i}" chat'))
        mover(self.c, 1, 'pre_teste'); mover(self.c, 1, 'em_teste')

    def test_deveBarrarSegundaApostaSteamEmTeste(self):
        mover(self.c, 2, 'pre_teste')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'uma_aposta_steam'):
            mover(self.c, 2, 'em_teste')

    def test_devePermitirWebEmTesteComApostaSteamAtiva(self):
        mover(self.c, 3, 'pre_teste'); mover(self.c, 3, 'em_teste')
        self.assertEqual(self.c.execute('SELECT estado FROM ideias WHERE id=3').fetchone()[0], 'em_teste')

    def test_devePermitirSegundaApostaSteamDepoisQueAPrimeiraSai(self):
        mover(self.c, 1, 'arquivada'); mover(self.c, 2, 'pre_teste'); mover(self.c, 2, 'em_teste')
        self.assertEqual(self.c.execute('SELECT estado FROM ideias WHERE id=2').fetchone()[0], 'em_teste')

    def test_deveBarrarTrocaDeTrilhaDepoisDeSairDeCandidata(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'trilha_imutavel'):
            self.c.execute("UPDATE ideias SET trilha='W' WHERE id=1")

    def test_devePermitirDefinirTrilhaEmCandidata(self):
        self.c.execute("UPDATE ideias SET trilha='W' WHERE id=2")


class Vocabulario(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(':memory:'); self.c.executescript(SCHEMA)
        self.c.execute("INSERT INTO ideias(titulo,build_mb,tempo_gameplay_s) VALUES('i',3.2,6)")

    def test_aceitaEtapaW2WebFitEPublisher(self):
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(1,'W2','portal_webfit','planejado')")
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(1,'M1','publisher_teste','planejado')")

    def test_aceitaMetricasNovasDosPortaisERoblox(self):
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(1,'W1','portal_teste','rodando')")
        for i, m in enumerate(['jogadas_3min', 'webfit_notas_ok', 'aceite_plataforma', 'sessoes_10min', 'decisao_plataforma']):
            self.c.execute("INSERT INTO metricas(experimento_id,data,metrica,valor,fonte) VALUES(1,?,?,1,'portal_dashboard')", (f'2026-10-2{i}', m))

    def test_aceitaFontePublisher(self):
        self.c.execute("INSERT INTO experimentos(ideia_id,etapa,tipo,estado) VALUES(1,'M1','publisher_teste','rodando')")
        self.c.execute("INSERT INTO metricas(experimento_id,data,metrica,valor,fonte) VALUES(1,'2026-10-26','aceite_plataforma',1,'publisher')")

if __name__ == '__main__': unittest.main()
