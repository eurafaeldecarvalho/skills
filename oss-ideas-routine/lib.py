"""Deterministic calculations for the open-source ideas routine. Use these functions; never do this math in your head."""
import math
import re

Z = 1.96  # 95%

# Median stars gained in the 7 days after a Show HN, by points band (n~40 per band, posts 2025-11..2026-07)
# [bench:estrelas_7d_mediana_hn_10_49pts/...], [bench:estrelas_7d_mediana_hn_50_99pts/...], etc.
E7_POR_FAIXA = ((10, 49, 32), (50, 99, 127), (100, 199, 303), (200, None, 755))


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
            prazo_esgotado=False, passa_estendido=None, janela1_abaixo=False):
    """Returns 'passa', 'mata', 'estender', 'inconclusiva', 'aguardar' or 'sem_amostra' (SKILL.md section 8.2).

    tipo: 'contagem' (stars in a window: eventos = stars, n = days covered since the first launch channel) or
    'taxa' (rate with Wilson interval: eventos = successes, n = trials).
    estendida: 1 after the second launch channel; eventos and n then cover a NEW window that starts on the second
    channel's date (same length, n_min not doubled), and passa_estendido is REQUIRED (a silent default once killed an
    idea that had passed). On the extended window: >= passa_estendido 'passa', <= limiar_mata 'mata', between the
    lines 'inconclusiva' (archive; the kill line is the same on both windows). It kills only with janela1_abaixo
    (the first window also ended at or below the kill line): a weak tail after a near-pass is 'inconclusiva'.
    prazo_esgotado: today > first launch + prazo_dias x (1 + estendida) + the reading grace period.
    """
    if n_min < 1 or n < 0 or eventos < 0 or (tipo == 'taxa' and eventos > n and n >= n_min):
        raise ValueError(f'invalid input: eventos={eventos} n={n} n_min={n_min}')
    if tipo == 'contagem' and estendida and passa_estendido is None:
        raise ValueError('contagem estendida: pass passa_estendido explicitly')
    alvo = 2 * n_min if estendida else n_min

    if tipo == 'contagem':
        exigido = passa_estendido if estendida else limiar_passa
        if n < n_min:   # a short reading cannot pass nor kill a window
            return 'sem_amostra' if prazo_esgotado else 'aguardar'
        if eventos >= exigido:
            return 'passa'
        if eventos <= limiar_mata and (janela1_abaixo or not estendida):
            return 'mata'
        return 'inconclusiva' if estendida else 'estender'

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


def _normaliza(t):
    return ' '.join(t.lower().split())


def prova_existe(prova_dono, textos_inbox, ideia_id=None, frase=None):
    """True if the excerpt quoted in prova_dono (between quotes, if any) appears literally in an inbox text, at the start
    of a sentence. With ideia_id, the quote must contain 'ideia#<id>' (no digit right after it). With frase (an owner
    phrase of section 0.1 with the id filled in), the quote must START with it: a negation quoted whole is no proof."""
    m = re.search(r'["“](.+?)["”]', prova_dono, re.DOTALL)
    trecho = _normaliza(re.sub(r'\s*\n\s*', '. ', m.group(1) if m else prova_dono))
    if ideia_id is not None and not re.search(rf'ideia#{ideia_id}(?!\d)', trecho):
        return False
    if frase is not None and not re.match(re.escape(_normaliza(frase)) + r'(?!\d)', trecho):
        return False
    padrao = r'(?:^|[.!?;:]\s*)(?:[-*•]\s*)?' + re.escape(trecho) + (r'(?!\d)' if trecho[-1:].isdigit() else '')
    return len(trecho) >= 10 and any(re.search(padrao, _normaliza(re.sub(r'\s*\n\s*', '. ', t))) for t in textos_inbox)


def carga_h_semana(estrelas_alvo, itens_por_1k, min_por_item, semanas):
    """Projected maintenance (issues + PRs) in hours per week if the repo reaches estrelas_alvo, assuming the whole
    lifetime load lands in the first `semanas` (worst case: stars and issues concentrate at launch)."""
    itens = estrelas_alvo / 1000 * itens_por_1k
    return itens * min_por_item / 60 / semanas


def suspeito_fake(estrelas_semanais, fork_star=None, pico_frac=0.70, resto_frac=0.01, fork_star_min=0.01):
    """Fake-star signature of a competitor or benchmark repo (SKILL.md section 4.3): one week with more than 70% of all
    stars and every later week below 1% of that peak, or forks/stars below 0.01."""
    if fork_star is not None and fork_star < fork_star_min:
        return True
    total = sum(estrelas_semanais)
    if total <= 0:
        return False
    i = max(range(len(estrelas_semanais)), key=lambda k: estrelas_semanais[k])
    pico = estrelas_semanais[i]
    depois = estrelas_semanais[i + 1:]
    return pico / total > pico_frac and len(depois) > 0 and all(x < resto_frac * pico for x in depois)


def conversao(estrelas, visitantes_unicos):
    """Visit-to-star conversion of the own repo (GitHub Traffic); None without visitors."""
    if not visitantes_unicos:
        return None
    return estrelas / visitantes_unicos


def e7_esperado(pontos_hn):
    """Median 7-day stars for a Show HN in that points band; None below 10 points (no reference band)."""
    for lo, hi, med in E7_POR_FAIXA:
        if pontos_hn >= lo and (hi is None or pontos_hn <= hi):
            return med
    return None
