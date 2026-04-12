"""Bubble score calculation.

Computes a speculative-bubble risk indicator from market signals.
Positive = potential bubble (price inflated beyond fundamentals).
Negative = potentially undervalued.
Range: clamped to [-1.0, 1.0].
"""


def compute_bubble(
    price: int,
    fair_value: int,
    price_12mo: int,
    social_score: int,
    psa10_pop: int,
) -> float:
    """Derive bubble score from market data.

    Components (weighted sum):
      35%  Price premium   — (price - fair_value) / fair_value
      25%  12-mo momentum  — (price - price_12mo) / price_12mo
      20%  Social hype     — social_score / 100, centered at 0.5
      20%  Supply pressure — psa10_pop / 1000, capped at 1; scarce cards
                             (low pop) dampen the bubble signal
    """
    if not fair_value or not price_12mo:
        return 0.0

    premium = (price - fair_value) / fair_value
    momentum = (price - price_12mo) / price_12mo
    hype = (social_score / 100.0) - 0.5
    supply = min(psa10_pop / 1000.0, 1.0) - 0.3

    raw = 0.35 * premium + 0.25 * momentum + 0.20 * hype + 0.20 * supply
    return round(max(-1.0, min(1.0, raw)), 2)
