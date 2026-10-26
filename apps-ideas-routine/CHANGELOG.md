# CHANGELOG

The routine proposes changes here (1st Sunday of the month). The owner approves and applies them.

## v11 — 2026-10-26 (final; review rounds 1–9)

Built from market research (Oct 2026) and then hardened by 9 rounds of independent review. Each round ran a
red-team that pushed 5 good and 3 bad ideas through the funnel, plus a correctness/executability reviewer
that simulated every state transition in SQLite. Findings per round: 39 → 21 → 17 → 17 → 20 → 17 → 15 → 5 → 7.
None of the round-9 findings was blocking, and all of them were fixed in v11. v11 itself was not re-reviewed
by an independent round. Its fixes are covered by the unit tests and the end-to-end checks.

Key decisions taken by the owner along the way:
- an exploration quota for brand-new categories (no paying competitor);
- the free landing test (E1) does not use a test slot;
- the store track (L) requires E1 or an explicit "build without demand test" from the owner;
- platform fees (Apple, Play, Chrome Web Store, Shopify) come from a separate budget;
- the paid BR test (E2E3) passes with 2 payments.

### Assumptions without a source (`origem='premissa'` in config; calibrate with your own data)
- Churn per ticket band.
- MVP ≤ 40 h.
- Run caps, saturation and deadlines.
- `pv_por_clique` 0.7.
- `conv_visita_paga_web` 1%.
- `fator_conversao_br` 0.5.
- `pct_max_penetracao` 3%.
- Per-stage budgets and minimum prices.
- Every threshold outside E4.

### Not verifiable (kept out of calculations)
- "~72% of annual plans cancel in year 1".
- The ~US$150 micro-SaaS MRR median.
- Reddit CPC by country.
- Dodo's fee base (treated as charged on the total, which is the conservative choice).
- The maximum duration of a Grok Bot routine run.

### Known open points (low severity)
- The reopening text for a store-track idea parked because volume was not measured is imprecise.
- The M1 threshold (15 installs/week) and the E3 sample for marketplace extensions are not aligned. An
  extension that barely passes M1 tends to be archived for lack of sample in E3. The monthly calibration
  should fix this.
