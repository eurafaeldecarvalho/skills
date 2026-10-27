import unittest
from lib import wilson, decidir, liquido_usd, n_atingivel, steam_projecao, liquido_steam, roblox_usd, web_receita_mes

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
        self.assertEqual(decidir('contagem', 2, 200, 3, 0, 150, 3, estendida=True, passa_estendido=5), 'aguardar')
    def test_estendida_passa_com_5(self):
        self.assertEqual(decidir('contagem', 5, 300, 3, 0, 150, 3, estendida=True, passa_estendido=5), 'passa')
    def test_estendida_com_4_em_2x_mata(self):
        self.assertEqual(decidir('contagem', 4, 300, 3, 0, 150, 3, estendida=True, passa_estendido=5), 'mata')
    def test_sem_amostra_com_prazo_esgotado(self):
        self.assertEqual(decidir('contagem', 0, 50, 3, 0, 300, 3, estendida=False, prazo_esgotado=True), 'sem_amostra')

class Economia(unittest.TestCase):
    def test_appstore_uk_com_vat(self):
        self.assertAlmostEqual(liquido_usd(4.99, 'appstore', aliquota_ir=0, vat=0.20), 3.535, places=3)
    def test_retencao_na_fonte(self):
        # Play BR com IRRF+CIDE hipotético de 25%
        self.assertAlmostEqual(liquido_usd(10, 'play', aliquota_ir=0, retencao=0.25), 6.375, places=3)
    def test_n_atingivel_meta_br(self):
        self.assertEqual(n_atingivel(300, 5.04, 0.20), 297)


class V4(unittest.TestCase):
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
    def test_extensao_por_falta_de_amostra_mantem_limiar(self):
        self.assertEqual(decidir('contagem', 3, 300, 3, 0, 300, 3, estendida=True, passa_estendido=3), 'passa')   # round 10: n >= n_min


class V8(unittest.TestCase):
    def test_piso_nao_cumprido_aguarda(self):
        self.assertEqual(decidir('contagem', 3, 60, 3, 0, 300, 3, False, piso_ok=False), 'aguardar')
    def test_piso_nao_cumprido_com_prazo_esgotado_vira_sem_amostra(self):
        self.assertEqual(decidir('contagem', 3, 60, 3, 0, 300, 3, True, True, 3, piso_ok=False), 'sem_amostra')
    def test_piso_cumprido_passa(self):
        self.assertEqual(decidir('contagem', 3, 300, 3, 0, 300, 3, False, piso_ok=True), 'passa')   # round 10: n >= n_min


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


class Games(unittest.TestCase):
    def test_steam_semana1_preco_baixo_usa_015(self):
        p = steam_projecao(5000, 9.99)
        self.assertEqual(p['copias_semana1'], 750)
    def test_steam_semana1_preco_alto_usa_010(self):
        self.assertEqual(steam_projecao(5000, 14.99)['copias_semana1'], 500)
    def test_steam_ano1_faixa(self):
        p = steam_projecao(5000, 9.99)
        self.assertEqual((p['copias_ano1_baixo'], p['copias_ano1_centro'], p['copias_ano1_alto']), (1250, 2000, 3500))
    def test_liquido_steam_sem_credito_ir_incide_sobre_o_recebido_bruto(self):
        # 1000 gross -> 700 after Valve; US withholding 0.30*0.40*700 = 84; BR IR 27.5% on the 700 = 192.5
        self.assertAlmostEqual(liquido_steam(1000, us_share=0.40, aliquota_ir=0.275), 423.5, places=1)
    def test_liquido_steam_com_credito_paga_o_maior_dos_dois_impostos(self):
        # reciprocity: the 84 withheld are credited against the 192.5 -> total tax = 192.5
        self.assertAlmostEqual(liquido_steam(1000, us_share=0.40, aliquota_ir=0.275, compensa_eua=True), 507.5, places=1)
    def test_liquido_steam_credito_limitado_ao_ir_brasileiro(self):
        # IR 7.5% (52.5) < withholding 84: the excess withholding is lost -> net 700 - 84
        self.assertAlmostEqual(liquido_steam(1000, us_share=0.40, aliquota_ir=0.075, compensa_eua=True), 616.0, places=1)
    def test_liquido_steam_com_reembolso(self):
        self.assertAlmostEqual(liquido_steam(1000, us_share=0, aliquota_ir=0, reembolso=0.10), 630.0, places=1)
    def test_roblox_devex(self):
        self.assertAlmostEqual(roblox_usd(30000), 114.0, places=2)
    def test_web_receita_por_mil_plays(self):
        self.assertAlmostEqual(web_receita_mes(200000, usd_por_mil=2.0), 400.0, places=2)



class Media(unittest.TestCase):
    """Mean criterion (e.g. average playtime in minutes): eventos = sum of the values, n = players."""
    def test_deveAguardarQuandoAmostraAbaixoDoMinimo(self):
        self.assertEqual(decidir('media', 4000, 300, 10, 5, 500, 0, 0), 'aguardar')

    def test_deveSerSemAmostraQuandoPrazoEsgotadoSemAmostra(self):
        self.assertEqual(decidir('media', 4000, 300, 10, 5, 500, 0, 0, prazo_esgotado=True), 'sem_amostra')

    def test_devePassarQuandoMediaAtingeLimiar(self):
        self.assertEqual(decidir('media', 5500, 500, 10, 5, 500, 0, 0), 'passa')

    def test_deveMatarQuandoMediaAbaixoDoLimiarDeMorte(self):
        self.assertEqual(decidir('media', 2000, 500, 10, 5, 500, 0, 0), 'mata')

    def test_deveEstenderQuandoMediaNoMeio(self):
        self.assertEqual(decidir('media', 3500, 500, 10, 5, 500, 0, 0), 'estender')

    def test_estendidaNoMeioComAmostraDobradaMata(self):
        self.assertEqual(decidir('media', 7000, 1000, 10, 5, 500, 0, 1), 'mata')

    def test_estendidaNoMeioSemAmostraDobradaAguarda(self):
        self.assertEqual(decidir('media', 4200, 600, 10, 5, 500, 0, 1), 'aguardar')

    def test_mediaAceitaSomaMaiorQueN(self):
        self.assertEqual(decidir('media', 6000, 500, 10, 5, 500, 0, 0), 'passa')


class Teto(unittest.TestCase):
    """Ceiling mean (lower is better, e.g. CPI in USD): eventos = total cost, n = installs."""
    def test_devePassarQuandoCpiAbaixoDoTeto(self):
        self.assertEqual(decidir('teto', 105.0, 350, 0.40, 0.60, 300, 0, 0), 'passa')   # 0.30/install

    def test_deveMatarQuandoCpiAcimaDoLimiarDeMorte(self):
        self.assertEqual(decidir('teto', 245.0, 350, 0.40, 0.60, 300, 0, 0), 'mata')    # 0.70

    def test_deveEstenderQuandoCpiNoMeio(self):
        self.assertEqual(decidir('teto', 175.0, 350, 0.40, 0.60, 300, 0, 0), 'estender')  # 0.50

    def test_estendidaNoMeioComAmostraDobradaMata(self):
        self.assertEqual(decidir('teto', 300.0, 600, 0.40, 0.60, 300, 0, 1), 'mata')

    def test_deveAguardarSemAmostra(self):
        self.assertEqual(decidir('teto', 30.0, 100, 0.40, 0.60, 300, 0, 0), 'aguardar')

    def test_tetoComLimiaresInvertidosRejeita(self):
        with self.assertRaises(ValueError):
            decidir('teto', 105.0, 350, 0.60, 0.40, 300, 0, 0)

class Exterior(unittest.TestCase):
    def test_portalSemRetencaoPagaSoIrBrasileiro(self):
        from lib import liquido_exterior
        self.assertAlmostEqual(liquido_exterior(200, 0.275), 145.0, places=2)

    def test_retencaoSemCreditoSomaOsDoisImpostos(self):
        from lib import liquido_exterior
        self.assertAlmostEqual(liquido_exterior(200, 0.275, retido_usd=60), 85.0, places=2)

    def test_retencaoComCreditoPagaOMaior(self):
        from lib import liquido_exterior
        self.assertAlmostEqual(liquido_exterior(200, 0.275, retido_usd=60, compensa_eua=True), 140.0, places=2)

if __name__ == '__main__':
    unittest.main()
