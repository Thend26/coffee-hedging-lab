"""Deterministic analytical results for the simplified coffee hedging model."""

import math


def budget_metrics(cost: float, budget: float) -> dict:
    """Return signed gap and nonnegative overspend in USD; equality is not excess."""
    for name, value in (("cost", cost), ("budget", budget)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be an int or float, not a boolean.")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            raise ValueError(f"{name} is too large to represent.") from None
        if not finite or value < 0:
            raise ValueError(f"{name} must be finite and nonnegative.")
    gap = float(cost - budget)
    return {'budget_gap_usd': gap, 'overspend_usd': max(gap, 0.0)}


def budget_summary(rows: list[dict]) -> dict:
    """Summarize only supplied scenarios, not probabilities or global cost caps.

    Consume costs and a common budget; recompute gaps rather than trusting
    potentially stale derived fields. Require at least one scenario.
    """
    if not rows:
        raise ValueError('At least one scenario is required.')
    budget = rows[0]['budget_usd']
    result = {}
    for prefix in ('unhedged', 'futures_hedged', 'call_hedged'):
        costs, overspends = [], []
        for row in rows:
            cost = row[f'{prefix}_cost_usd']
            metrics = budget_metrics(cost, row['budget_usd'])
            if row['budget_usd'] != budget:
                raise ValueError('All scenarios must use the same budget.')
            costs.append(cost)
            overspends.append(metrics['overspend_usd'])
        result[prefix] = {
            'exceedance_count': sum(value > 0 for value in overspends),
            'max_cost_usd': max(costs),
            'max_overspend_usd': max(overspends),
        }
    return result


def break_even_vs_unhedged(futures_price: float, strike: float,
                           premium: float, hedge_ratio: float) -> dict:
    """Classify nonnegative terminal prices where costs equal unhedged cost.

    Bounds are inclusive, in USD/lb. A point repeats its price in both bounds;
    an interval contains every price between the bounds. all_prices represents
    [0, infinity), with None as its unbounded upper endpoint. No grid or price
    probabilities are used. Quantity cancels under the assumption Q > 0.
    """
    for name, value in (("futures_price", futures_price), ("strike", strike),
                        ("premium", premium), ("hedge_ratio", hedge_ratio)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be an int or float, not a boolean.")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            raise ValueError(f"{name} is too large to represent.") from None
        if not finite:
            raise ValueError(f"{name} must be finite.")

    if futures_price <= 0:
        raise ValueError("futures_price must be greater than zero.")
    if strike <= 0:
        raise ValueError("strike must be greater than zero.")
    if premium < 0:
        raise ValueError("premium must be zero or greater.")
    if not 0 <= hedge_ratio <= 1:
        raise ValueError("hedge_ratio must be between zero and one inclusive.")

    if hedge_ratio == 0:
        return {
            'futures': {'kind': 'all_prices', 'lower_usd_per_lb': 0.0,
                        'upper_usd_per_lb': None},
            'call': {'kind': 'all_prices', 'lower_usd_per_lb': 0.0,
                     'upper_usd_per_lb': None},
        }

    futures_result = {'kind': 'point', 'lower_usd_per_lb': float(futures_price),
                      'upper_usd_per_lb': float(futures_price)}
    if premium == 0:
        call_result = {'kind': 'interval', 'lower_usd_per_lb': 0.0,
                       'upper_usd_per_lb': float(strike)}
    else:
        try:
            point = float(strike + premium)
        except OverflowError:
            raise ValueError("Call break-even price is too large to represent.") from None
        if not math.isfinite(point):
            raise ValueError("Call break-even price must be finite.")
        call_result = {'kind': 'point', 'lower_usd_per_lb': point,
                       'upper_usd_per_lb': point}
    return {'futures': futures_result, 'call': call_result}
