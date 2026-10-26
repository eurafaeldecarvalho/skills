import unittest
from lib import wilson, decidir, liquido_usd, n_clientes, n_atingivel

class Wilson(unittest.TestCase):
    def test_0_de_200_superior_abaixo_de_2pct(self):
        lo, hi = wilson(0, 200); self.assertEqual(lo, 0.0); self.assertAlmostEqual(hi, 0.0188, places=3)
    def test_10_de_200_inferior(self):
        self.assertAlmostEqual(wilson(10, 200)[0], 0.0274, places=3)

class DecidirTaxa(unittest.TestCase):
    def test_passa_com_10_de_200(self):
        self.assertEqual(decidir('taxa', 10, 200, 0.05, 0.02, 200, 10, estendida=False), 'passa')
    def test_mata_com_0_de_200(self):
        self.assertEqual(decidir('taxa', 0, 200, 0.05, 0.02, 200, 10, estendida=False), 'mata')
    def test_no_meio_estende(self):
        self.assertEqual(decidir('taxa', 6, 200, 0.05, 0.02, 200, 10, estendida=False), 'estender')
    def test_estendida_aguarda_ate_2x_n_min(self):
        self.assertEqual(decidir('taxa', 6, 210, 0.05, 0.02, 200, 10, estendida=True), 'aguardar')
    def test_estendida_em_2x_n_min_no_meio_mata(self):
        self.assertEqual(decidir('taxa', 12, 400, 0.05, 0.02, 200, 10, estendida=True), 'mata')
    def test_estendida_com_prazo_esgotado_decide(self):
        self.assertEqual(decidir('taxa', 8, 240, 0.05, 0.02, 200, 10, estendida=True, prazo_esgotado=True), 'mata')
    def test_amostra_insuficiente_aguarda(self):
        self.assertEqual(decidir('taxa', 5, 100, 0.05, 0.02, 200, 10, estendida=False), 'aguardar')
    def test_sem_trafego_com_prazo_esgotado_e_sem_amostra(self):
        self.assertEqual(decidir('taxa', 1, 40, 0.05, 0.02, 200, 10, estendida=False, prazo_esgotado=True), 'sem_amostra')
    def test_eventos_maior_que_n_rejeita(self):
        with self.assertRaises(ValueError): decidir('taxa', 12, 10, 0.4, 0.15, 10, 4, False)
    def test_n_min_zero_rejeita(self):
        with self.assertRaises(ValueError): decidir('taxa', 0, 0, 0.05, 0.02, 0, 10, False)

class DecidirContagem(unittest.TestCase):
    def test_3_pagamentos_passa(self):
        self.assertEqual(decidir('contagem', 3, 300, 3, 0, 300, 3, estendida=False), 'passa')
    def test_0_pagamentos_com_amostra_mata(self):
        self.assertEqual(decidir('contagem', 0, 300, 3, 0, 300, 3, estendida=False), 'mata')
    def test_1_a_2_pagamentos_estende(self):
        self.assertEqual(decidir('contagem', 2, 150, 3, 0, 150, 3, estendida=False), 'estender')
    def test_estendida_precisa_dobrar_n(self):
        self.assertEqual(decidir('contagem', 2, 200, 3, 0, 150, 3, estendida=True), 'aguardar')
    def test_estendida_passa_com_5(self):
        self.assertEqual(decidir('contagem', 5, 300, 3, 0, 150, 3, estendida=True), 'passa')
    def test_estendida_com_4_em_2x_mata(self):
        self.assertEqual(decidir('contagem', 4, 300, 3, 0, 150, 3, estendida=True), 'mata')
    def test_sem_amostra_com_prazo_esgotado(self):
        self.assertEqual(decidir('contagem', 0, 50, 3, 0, 300, 3, estendida=False, prazo_esgotado=True), 'sem_amostra')

class Economia(unittest.TestCase):
    def test_creem_12usd_sem_imposto_com_ir_275(self):
        self.assertAlmostEqual(liquido_usd(12, 'creem', aliquota_ir=0.275), 8.07, places=2)
    def test_mor_taxa_sobre_total_com_vat(self):
        # cliente paga 14,40 (12 + 20% VAT); Creem cobra 3,9% sobre 14,40 + 0,40
        self.assertAlmostEqual(liquido_usd(14.40, 'creem', aliquota_ir=0, vat=0.20), 11.0384, places=4)
    def test_appstore_uk_com_vat(self):
        self.assertAlmostEqual(liquido_usd(4.99, 'appstore', aliquota_ir=0, vat=0.20), 3.535, places=3)
    def test_stripe_br_cartao_nacional(self):
        self.assertAlmostEqual(liquido_usd(49, 'stripe_br', aliquota_ir=0, moeda='BRL', cambio=5.04),
                               (49*(1-0.0399-0.007)-0.39)/5.04, places=4)
    def test_retencao_na_fonte(self):
        # Play BR com IRRF+CIDE hipotético de 25%
        self.assertAlmostEqual(liquido_usd(10, 'play', aliquota_ir=0, retencao=0.25), 6.375, places=3)
    def test_creem_em_brl_rejeita(self):
        with self.assertRaises(ValueError): liquido_usd(49, 'creem', 0, moeda='BRL', cambio=5.04)
    def test_n_clientes(self):
        self.assertEqual(n_clientes(300, 8.07), 38); self.assertEqual(n_clientes(1000, 8.07), 124)
    def test_liquido_negativo_rejeita(self):
        with self.assertRaises(ValueError): n_clientes(300, -1)
    def test_n_atingivel_meta_br(self):
        self.assertEqual(n_atingivel(300, 5.04, 0.20), 297)


class V4(unittest.TestCase):
    def test_atlassian_forge_sem_comissao_ate_1M(self):
        self.assertAlmostEqual(liquido_usd(20, 'atlassian_forge', aliquota_ir=0), 20.0, places=4)
    def test_n_atingivel_em_pageviews(self):
        # R$250 / (5.50 * 0.20) = 227 cliques; x0.7 = 158 pageviews
        self.assertEqual(n_atingivel(250, 5.50, 0.20, pv_por_clique=0.7), 158)
    def test_prova_existe_em_texto_do_inbox(self):
        from lib import prova_existe
        textos = ['26/10 21:10 dono: pode construir a ideia 5, aprovado']
        self.assertTrue(prova_existe('"pode construir a ideia 5, aprovado" — chat 26/10 21:10', textos))
    def test_prova_inventada_nao_existe(self):
        from lib import prova_existe
        self.assertFalse(prova_existe('"construa tudo" 26/10', ['26/10 dono: oi']))

class V5(unittest.TestCase):
    def test_appstore_aceita_preco_em_brl(self):
        # R$ 29,90 na loja BR, 15% -> 25,415 / 5,0 = 5,083 USD
        self.assertAlmostEqual(liquido_usd(29.90, 'appstore', 0, moeda='BRL', cambio=5.0), 5.083, places=3)
    def test_creem_continua_recusando_brl(self):
        with self.assertRaises(ValueError): liquido_usd(49, 'creem', 0, moeda='BRL', cambio=5.0)
    def test_extensao_por_falta_de_amostra_mantem_limiar(self):
        self.assertEqual(decidir('contagem', 3, 280, 3, 0, 300, 3, estendida=True, passa_estendido=3), 'passa')


class V8(unittest.TestCase):
    def test_piso_nao_cumprido_aguarda(self):
        self.assertEqual(decidir('contagem', 3, 60, 3, 0, 300, 3, False, piso_ok=False), 'aguardar')
    def test_piso_nao_cumprido_com_prazo_esgotado_vira_sem_amostra(self):
        self.assertEqual(decidir('contagem', 3, 60, 3, 0, 300, 3, True, True, 3, piso_ok=False), 'sem_amostra')
    def test_piso_cumprido_passa(self):
        self.assertEqual(decidir('contagem', 3, 120, 3, 0, 300, 3, False, piso_ok=True), 'passa')


class V11(unittest.TestCase):
    def test_deve_recusar_ideia1_quando_mensagem_cita_ideia12(self):
        from lib import prova_existe
        inbox = ['aprovo a construção da ideia#12, pode seguir']
        self.assertFalse(prova_existe('"aprovo a construção da ideia#1" 26/10', inbox, ideia_id=1))
    def test_deve_recusar_sem_ideia_quando_id_informado(self):
        from lib import prova_existe
        self.assertFalse(prova_existe('"aprovo a construção" 26/10', ['aprovo a construção'], ideia_id=3))
    def test_deve_aceitar_citacao_com_ideia_certa(self):
        from lib import prova_existe
        self.assertTrue(prova_existe('"aprovo a construção da ideia#12" 26/10', ['aprovo a construção da ideia#12, pode seguir'], ideia_id=12))


if __name__ == '__main__':
    unittest.main()
