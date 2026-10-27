"""Deterministic calculations for the games routine. Use these functions; never do this math in your head."""
import math
import re

Z = 1.96  # 95%

# Store cut on in-app purchases / paid apps (verified on 2026-10-26; see seed_benchmarks.csv).
# Steam, portals and Roblox have their own functions below.
TAXAS = {
    'appstore': 0.15,   # Small Business Program, on the tax-exclusive price [bench:taxa_appstore/sbp]
    'play':     0.15,   # service fee page [bench:taxa_play/primeiro_1M_ano]; confirm the games in-app rate before a port
}


def wilson(k, n, z=Z):
    """95% Wilson interval for k successes in n trials."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    margem = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centro - margem), min(1.0, centro + margem)


def decidir(tipo, eventos, n, limiar_passa, limiar_mata, n_min, eventos_min, estendida,
            prazo_esgotado=False, passa_estendido=None, piso_ok=True):
    """Returns 'passa' (pass), 'mata' (kill), 'estender' (extend), 'aguardar' (wait) or 'sem_amostra' (no sample) — SKILL.md section 7.4.

    tipo: 'taxa' (rate, Wilson interval), 'contagem' (count), 'media' (mean, higher is better: eventos = sum of the values, n = players)
    or 'teto' (mean, lower is better, e.g. CPI: eventos = total cost in USD, n = installs).

    prazo_esgotado: today > experimentos.inicio (milestone) + prazo_dias (x2 if extended).
    Do not change n_min or prazo_dias in the table when extending: this function and q_hipoteses_abertas already double them.
    passa_estendido (count): events required after extension — REQUIRED when estendida (fixed-scale counts such as
    aceite_plataforma/webfit_notas_ok pass limiar_passa; S1 passes s1_passa_estendido): a silent default once killed
    a game the platform had accepted.
    piso_ok (count): False when a sample floor beyond n_min was not met; then 'passa' becomes
    'aguardar' (or 'sem_amostra' once the deadline is over). No stage of this routine uses it today.
    """
    # a rate above 100% on a short early reading (e.g. page wishlists before demo players) waits; on a full sample it is an input error
    if n_min < 1 or n < 0 or eventos < 0 or (tipo == 'taxa' and eventos > n and n >= n_min):
        raise ValueError(f'invalid input: eventos={eventos} n={n} n_min={n_min}')
    if tipo == 'teto' and limiar_passa > limiar_mata:
        raise ValueError('teto: limiar_passa must be <= limiar_mata (lower is better)')
    alvo = 2 * n_min if estendida else n_min
    if tipo == 'contagem' and estendida and passa_estendido is None:
        raise ValueError('contagem estendida: pass passa_estendido explicitly (section 7.4)')

    if tipo == 'contagem':
        exigido = (passa_estendido if passa_estendido is not None else limiar_passa + 2) if estendida else limiar_passa
        if n < n_min:   # n_min also protects passing (a 7-day reading cannot pass a 14-day stage)
            return 'sem_amostra' if prazo_esgotado else 'aguardar'
        if eventos >= exigido:
            if piso_ok:
                return 'passa'
            return 'sem_amostra' if prazo_esgotado else 'aguardar'
        if eventos <= limiar_mata:
            return 'mata'
        if not estendida:
            return 'estender'
        return 'mata' if (n >= alvo or prazo_esgotado) else 'aguardar'

    if n < n_min:
        return 'sem_amostra' if prazo_esgotado else 'aguardar'
    p = eventos / n

    if tipo in ('media', 'teto'):
        # Point estimate of a mean (dashboards give no variance); n_min is the only protection.
        # 'teto' = lower is better (e.g. CPI): passes at or below limiar_passa, dies above limiar_mata.
        bom = p <= limiar_passa if tipo == 'teto' else p >= limiar_passa
        ruim = p > limiar_mata if tipo == 'teto' else p < limiar_mata
        if bom:
            return 'passa'
        if ruim:
            return 'mata'
        if not estendida:
            return 'estender'
        return 'mata' if (n >= alvo or prazo_esgotado) else 'aguardar'

    lo, hi = wilson(eventos, n)
    if p >= limiar_passa and lo >= limiar_mata and eventos >= eventos_min:
        return 'passa'
    if hi < limiar_mata:
        return 'mata'
    if not estendida:
        return 'estender'
    if n < alvo and not prazo_esgotado:
        return 'aguardar'
    return 'passa' if (p >= limiar_passa and eventos >= eventos_min) else 'mata'


def liquido_usd(preco, canal, aliquota_ir, vat=0.0, moeda='USD', cambio=1.0, retencao=0.0):
    """Net USD per purchase on a mobile store (IAP or paid app).

    preco: what the player pays, tax INCLUDED when there is tax; vat: tax rate contained in preco;
    retencao: withholding tax (e.g. Play BR IRRF+CIDE).
    """
    sem_imposto = preco / (1 + vat)
    liquido = sem_imposto * (1 - TAXAS[canal]) * (1 - retencao)
    if moeda == 'BRL':
        liquido = liquido / cambio
    return liquido * (1 - aliquota_ir)


def n_atingivel(orcamento_brl, cambio_usd_brl, cpc_usd, pv_por_clique=1.0):
    """Sample the budget buys. With pv_por_clique < 1, returns pageviews instead of clicks."""
    # a tiny epsilon keeps an exact quotient (300 / (6.0 x 0.05) = 1000) from flooring to 999 in floating point
    return math.floor(math.floor(orcamento_brl / (cambio_usd_brl * cpc_usd) + 1e-9) * pv_por_clique + 1e-9)


def _normaliza(t):
    return ' '.join(t.lower().split())


def prova_existe(prova_dono, textos_inbox, ideia_id=None, frase=None):
    """True if the excerpt quoted in prova_dono (between quotes, if any) appears literally in an inbox text.
    With ideia_id, the quote must also contain 'ideia#<id>' (no digit right after it).
    With frase (an owner phrase of section 0.1, with the id filled in), the quote must START with it: a negation
    ("não aprovo a construção da ideia#N") quoted whole is no proof."""
    m = re.search(r'["“](.+?)["”]', prova_dono, re.DOTALL)
    # same line-break treatment as the inbox text below, so a multi-line quote matches
    trecho = _normaliza(re.sub(r'\s*\n\s*', '. ', m.group(1) if m else prova_dono))
    if ideia_id is not None and not re.search(rf'ideia#{ideia_id}(?!\d)', trecho):
        return False
    if frase is not None and not re.match(re.escape(_normaliza(frase)) + r'(?!\d)', trecho):
        return False
    # the phrase must start a sentence (start of text, after . ! ? ; : or a line break, optionally after a list bullet):
    # "ainda não aprovo..." is no proof
    padrao = r'(?:^|[.!?;:]\s*)(?:[-*•]\s*)?' + re.escape(trecho) + (r'(?!\d)' if trecho[-1:].isdigit() else '')
    # a line break also starts a sentence: turn it into '. ' before collapsing whitespace
    return len(trecho) >= 10 and any(re.search(padrao, _normaliza(re.sub(r'\s*\n\s*', '. ', t))) for t in textos_inbox)


# ===== Games =====
# Steam coefficients (2023-25 cohorts; see seed_benchmarks.csv): week-1 copies per wishlist
# 0.15 (price <= US$10) / 0.10 (price > US$10); year-1 copies per wishlist center 0.40, band 0.25-0.70.
STEAM_W1_BAIXO_PRECO = 0.15   # median of all prices (>25k wishlists): proxy for <= US$10, a lower bound
STEAM_W1_ALTO_PRECO = 0.10
STEAM_ANO1 = (0.25, 0.40, 0.70)
STEAM_VALVE = 0.30           # Valve cut under US$10M
STEAM_RETENCAO_EUA = 0.30    # US withholding on the US share (no BR-US treaty)
ROBLOX_DEVEX_USD = 0.0038    # USD per earned Robux


def steam_projecao(wishlists, preco_usd):
    """Copies projection from launch-day wishlists. Returns ints (floor), computed in exact integer hundredths."""
    w1 = STEAM_W1_BAIXO_PRECO if preco_usd <= 10 else STEAM_W1_ALTO_PRECO
    b, c, a = STEAM_ANO1
    f = lambda k: (wishlists * round(k * 100)) // 100
    return {
        'copias_semana1': f(w1),
        'copias_ano1_baixo': f(b),
        'copias_ano1_centro': f(c),
        'copias_ano1_alto': f(a),
    }


def liquido_exterior(bruto_usd, aliquota_ir, retido_usd=0.0, compensa_eua=False):
    """Net of a payment from abroad (portal, Roblox DevEx, Epic, itch, Steam) for a Brazilian individual.

    bruto_usd: what the platform credited, before any withholding; retido_usd: US tax withheld from it.
    BR income tax (carne-leao) = aliquota_ir on bruto_usd. compensa_eua=True credits the US withholding against it
    (reciprocity, ADE SRF 28/2000), limited to the BR tax due. Confirm with an accountant before using True.
    """
    ir_br = bruto_usd * aliquota_ir
    imposto = max(retido_usd, ir_br) if compensa_eua else retido_usd + ir_br
    return bruto_usd - imposto


def liquido_steam(bruto_usd, us_share, aliquota_ir, reembolso=0.0, compensa_eua=False):
    """Personal net from Steam gross: refunds and the Valve cut, then 30% US withholding on the US share
    (no BR-US treaty) and BR income tax via liquido_exterior."""
    recebido = bruto_usd * (1 - reembolso) * (1 - STEAM_VALVE)
    return liquido_exterior(recebido, aliquota_ir, recebido * STEAM_RETENCAO_EUA * us_share, compensa_eua)


def roblox_usd(robux):
    return robux * ROBLOX_DEVEX_USD


def web_receita_mes(plays_mes, usd_por_mil):
    """Portal revenue estimate: plays per month x net USD per 1,000 plays (calibrate usd_por_mil with real data)."""
    return plays_mes * usd_por_mil / 1000
