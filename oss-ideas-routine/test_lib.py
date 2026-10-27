"""lib.py: decisions, owner proof, maintenance load, fake-star signature, conversion."""
import unittest
from lib import decidir, wilson, prova_existe, carga_h_semana, suspeito_fake, conversao, e7_esperado


class Decidir(unittest.TestCase):
    def test_s1PassaCom10EstrelasEm14Dias(self):
        self.assertEqual(decidir('contagem', 10, 14, 10, 2, 14, 0, 0), 'passa')

    def test_s1EntreAsLinhasEstende(self):
        self.assertEqual(decidir('contagem', 6, 14, 10, 2, 14, 0, 0), 'estender')

    def test_s1AbaixoDaLinhaDeMorte(self):
        self.assertEqual(decidir('contagem', 2, 14, 10, 2, 14, 0, 0), 'mata')

    def test_leituraCurtaAguarda(self):
        self.assertEqual(decidir('contagem', 50, 9, 10, 2, 14, 0, 0), 'aguardar')

    def test_estendidaExigePassaEstendidoExplicito(self):
        with self.assertRaises(ValueError):
            decidir('contagem', 10, 28, 10, 2, 14, 0, 1)

    def test_estendidaPassaNaMesmaLinha(self):
        self.assertEqual(decidir('contagem', 12, 28, 10, 2, 14, 0, 1, passa_estendido=10), 'passa')
        self.assertEqual(decidir('contagem', 2, 28, 10, 2, 14, 0, 1, passa_estendido=10, janela1_abaixo=True), 'mata')   # rounds 3/5: kill line, first window below

    def test_wilsonSemAmostra(self):
        self.assertEqual(wilson(0, 0), (0.0, 1.0))


class Prova(unittest.TestCase):
    def test_fraseNoInicioDaCitacao(self):
        inbox = ['## 2026-10-27 10:00\naprovo a construção da ideia#3']
        self.assertTrue(prova_existe('"aprovo a construção da ideia#3" chat 2026-10-27 10:00', inbox, 3, 'aprovo a construção da ideia#3'))

    def test_negacaoNaoVale(self):
        msg = 'não aprovo a construção da ideia#3'
        self.assertFalse(prova_existe(f'"{msg}" chat', [msg], 3, 'aprovo a construção da ideia#3'))

    def test_outraIdeiaNaoVale(self):
        self.assertFalse(prova_existe('"aprovo a construção da ideia#31" chat', ['aprovo a construção da ideia#31'], 3))


class Carga(unittest.TestCase):
    def test_cargaDe1000EstrelasCom22ItensPor1k(self):
        # 1000 stars x 22 items/1k = 22 items x 10 min = 220 min over 13 weeks ~ 0.28 h/week
        self.assertAlmostEqual(carga_h_semana(1000, 22, 10, 13), 22 * 10 / 60 / 13, places=6)

    def test_cargaDeCliDiaria(self):
        self.assertGreater(carga_h_semana(10000, 66, 10, 13), 3)


class Fake(unittest.TestCase):
    def test_semanaUnicaComQuaseTudoEDepoisNada(self):
        self.assertTrue(suspeito_fake([10, 7378, 40, 30, 20], fork_star=0.05))

    def test_forkStarMuitoBaixo(self):
        self.assertTrue(suspeito_fake([100, 200, 150, 120], fork_star=0.005))

    def test_curvaOrganica(self):
        self.assertFalse(suspeito_fake([50, 400, 900, 450, 300, 200], fork_star=0.09))


class Conversao(unittest.TestCase):
    def test_conversaoVisitaEstrela(self):
        self.assertAlmostEqual(conversao(800, 6000), 800 / 6000)
        self.assertIsNone(conversao(5, 0))

    def test_e7EsperadoPorFaixaDePontos(self):
        self.assertEqual(e7_esperado(5), None)
        self.assertEqual(e7_esperado(30), 32)
        self.assertEqual(e7_esperado(80), 127)
        self.assertEqual(e7_esperado(150), 303)
        self.assertEqual(e7_esperado(400), 755)


if __name__ == '__main__':
    unittest.main()
