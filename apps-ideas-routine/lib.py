"""Deterministic calculations for the routine. Use these functions; never do this math in your head."""
import math
import re

Z = 1.96  # 95%

# Fees per billing channel (verified on 2026-10-26; see seed_benchmarks.csv)
TAXAS = {
    # pct and fixed fee per transaction; fixed fee in the MOEDA_FIXO currency (default USD)
    'appstore': {'pct': 0.15, 'fixo': 0.0},     # Small Business Program, on the tax-exclusive price
    'play':     {'pct': 0.15, 'fixo': 0.0},     # subscriptions, all markets
    'shopify':  {'pct': 0.029, 'fixo': 0.0},    # 0% rev share up to US$1M lifetime + 2.9% processing
    'creem':    {'pct': 0.039, 'fixo': 0.40},   # MoR, no international surcharge
    'dodo':     {'pct': 0.04 + 0.015 + 0.005, 'fixo': 0.40},  # +1.5% international +0.5% subscription
    'paddle':   {'pct': 0.05, 'fixo': 0.50},
    'stripe_br': {'pct': 0.0399 + 0.007, 'fixo': 0.39},       # domestic card + Billing; fixed fee in BRL
    'atlassian_forge': {'pct': 0.0, 'fixo': 0.0},  # 0% up to US$1M lifetime on Forge; 17% after (revisit when close)
}
MOR = ('creem', 'dodo', 'paddle')   # fee charged on the total paid (tax included); Dodo = conservative assumption
MOEDA_FIXO = {'stripe_br': 'BRL'}


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
    """Returns 'passa' (pass), 'mata' (kill), 'estender' (extend), 'aguardar' (wait) or 'sem_amostra' (no sample) — SKILL.md section 7.3.

    prazo_esgotado: today > experimentos.inicio (milestone) + prazo_dias (x2 if extended).
    Do not change n_min or prazo_dias in the table when extending: this function and q_hipoteses_abertas already double them.
    passa_estendido (count): events required after extension; default limiar_passa + 2.
    piso_ok (count): False when the E3/E2E3 sample floor was not met; then 'passa' becomes
    'aguardar' (or 'sem_amostra' once the deadline is over).
    """
    if n_min < 1 or n < 0 or eventos < 0 or (tipo == 'taxa' and eventos > n):
        raise ValueError(f'invalid input: eventos={eventos} n={n} n_min={n_min}')
    alvo = 2 * n_min if estendida else n_min

    if tipo == 'contagem':
        exigido = (passa_estendido if passa_estendido is not None else limiar_passa + 2) if estendida else limiar_passa
        if eventos >= exigido:
            if piso_ok:
                return 'passa'
            return 'sem_amostra' if prazo_esgotado else 'aguardar'
        if n < n_min:
            return 'sem_amostra' if prazo_esgotado else 'aguardar'
        if eventos <= limiar_mata:
            return 'mata'
        if not estendida:
            return 'estender'
        return 'mata' if (n >= alvo or prazo_esgotado) else 'aguardar'

    if n < n_min:
        return 'sem_amostra' if prazo_esgotado else 'aguardar'
    p = eventos / n
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


def liquido_usd(preco, canal, aliquota_ir, vat=0.0, moeda='USD', cambio=1.0,
                cartao_internacional=False, retencao=0.0):
    """Monthly net revenue per customer in USD.

    preco: what the customer pays, tax INCLUDED when there is tax; vat: tax rate contained in preco;
    retencao: withholding tax (e.g. Play BR IRRF+CIDE, US withholding).
    """
    t = TAXAS[canal]
    if t['fixo'] > 0 and moeda != MOEDA_FIXO.get(canal, 'USD'):
        raise ValueError(f'{canal} charges in {MOEDA_FIXO.get(canal, "USD")}, not {moeda}')
    sem_imposto = preco / (1 + vat)
    pct = t['pct'] + (0.02 if canal == 'stripe_br' and cartao_internacional else 0.0)
    base_taxa = preco if canal in MOR else sem_imposto
    liquido = (sem_imposto - base_taxa * pct - t['fixo']) * (1 - retencao)
    if moeda == 'BRL':
        liquido = liquido / cambio
    return liquido * (1 - aliquota_ir)


def n_clientes(meta_usd, liquido_cliente_usd):
    if liquido_cliente_usd <= 0:
        raise ValueError('net <= 0: the math does not close')
    return math.ceil(meta_usd / liquido_cliente_usd)


def n_atingivel(orcamento_brl, cambio_usd_brl, cpc_usd, pv_por_clique=1.0):
    """Sample the budget buys. With pv_por_clique < 1, returns pageviews instead of clicks."""
    return math.floor(math.floor(orcamento_brl / (cambio_usd_brl * cpc_usd)) * pv_por_clique)


def _normaliza(t):
    return ' '.join(t.lower().split())


def prova_existe(prova_dono, textos_inbox, ideia_id=None):
    """True if the excerpt quoted in prova_dono (between quotes, if any) appears literally in an inbox text.
    With ideia_id, the quote must also contain 'ideia#<id>' (no digit right after it)."""
    m = re.search(r'["“](.+?)["”]', prova_dono)
    trecho = _normaliza(m.group(1) if m else prova_dono)
    if ideia_id is not None and not re.search(rf'ideia#{ideia_id}(?!\d)', trecho):
        return False
    padrao = re.escape(trecho) + (r'(?!\d)' if trecho[-1:].isdigit() else '')
    return len(trecho) >= 10 and any(re.search(padrao, _normaliza(t)) for t in textos_inbox)
