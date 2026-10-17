"""Scenario comparison helpers; not yet the complete public input interface."""

from calculations import (
    unhedged_cost, futures_hedged_cost, call_hedged_cost, futures_pnl, call_payoff,
    partial_futures_hedged_cost, partial_call_hedged_cost,
)
from analysis import budget_metrics
import csv
import io
import math


SCENARIO_FIELDS = (
    'quantity_lb', 'current_spot_usd_per_lb', 'futures_price_usd_per_lb',
    'strike_usd_per_lb', 'premium_usd_per_lb', 'terminal_price_usd_per_lb',
    'physical_cost_usd', 'futures_pnl_usd', 'call_payoff_usd',
    'option_premium_usd', 'unhedged_cost_usd', 'futures_hedged_cost_usd',
    'call_hedged_cost_usd',
    'hedge_ratio', 'budget_usd',
    'unhedged_savings_vs_unhedged_usd', 'unhedged_budget_gap_usd', 'unhedged_overspend_usd',
    'futures_hedged_savings_vs_unhedged_usd', 'futures_hedged_budget_gap_usd',
    'futures_hedged_overspend_usd', 'call_hedged_savings_vs_unhedged_usd',
    'call_hedged_budget_gap_usd', 'call_hedged_overspend_usd',
)


def build_scenarios(quantity, current_spot, futures_price, strike, premium,
                    price_min, price_max, hedge_ratio=1.0, budget_usd=1300.0):
    """Build 101 fully specified educational procurement scenarios.

    Current spot is a reference only. Cash costs ignore funding, basis,
    fees and taxes; option premium is an undiscounted cash expenditure on
    hedged quantity only. V2 exports add ratio, budget, savings and stress fields.
    """
    # Validate the reference even though it does not enter scenario costs.
    unhedged_cost(quantity, current_spot)
    if current_spot <= 0:
        raise ValueError('current_spot must be greater than zero.')
    prices = generate_prices(price_min, price_max)
    if any(a >= b for a, b in zip(prices, prices[1:])):
        raise ValueError('Price range is too narrow for 101 distinct float values.')
    # Validate all contract inputs before constructing records.
    partial_futures_hedged_cost(quantity, prices[0], futures_price, hedge_ratio)
    partial_call_hedged_cost(quantity, prices[0], strike, premium, hedge_ratio)
    budget_metrics(0, budget_usd)
    hedged_quantity = quantity * hedge_ratio
    premium_total = float(hedged_quantity * premium)
    rows = []
    for price in prices:
        physical = unhedged_cost(quantity, price)
        row = {
            'quantity_lb': quantity,
            'current_spot_usd_per_lb': current_spot,
            'futures_price_usd_per_lb': futures_price,
            'strike_usd_per_lb': strike,
            'premium_usd_per_lb': premium,
            'terminal_price_usd_per_lb': price,
            'physical_cost_usd': physical,
            'futures_pnl_usd': (futures_pnl(hedged_quantity, price, futures_price)
                                if hedged_quantity else 0.0),
            'call_payoff_usd': (call_payoff(hedged_quantity, price, strike)
                                if hedged_quantity else 0.0),
            'option_premium_usd': premium_total,
            'unhedged_cost_usd': physical,
            'futures_hedged_cost_usd': partial_futures_hedged_cost(
                quantity, price, futures_price, hedge_ratio),
            'call_hedged_cost_usd': partial_call_hedged_cost(
                quantity, price, strike, premium, hedge_ratio),
            'hedge_ratio': hedge_ratio,
            'budget_usd': budget_usd,
        }
        for prefix in ('unhedged', 'futures_hedged', 'call_hedged'):
            cost = row[f'{prefix}_cost_usd']
            metrics = budget_metrics(cost, budget_usd)
            row[f'{prefix}_savings_vs_unhedged_usd'] = physical - cost
            row[f'{prefix}_budget_gap_usd'] = metrics['budget_gap_usd']
            row[f'{prefix}_overspend_usd'] = metrics['overspend_usd']
        rows.append(row)
    return rows


def scenarios_to_csv(rows):
    """Serialize scenario records without rounding or adding formulas.

    Return text for UTF-8 encoding at the file/download boundary.
    An empty list returns a header-only CSV. Only finite numeric cells and
    exactly the specified keys are accepted; this is not a pricing validator.
    """
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=SCENARIO_FIELDS, lineterminator='\n')
    writer.writeheader()
    for row in rows:
        if set(row) != set(SCENARIO_FIELDS):
            raise ValueError('CSV records must have exactly the scenario fields.')
        for value in row.values():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError('CSV cells must be finite numeric values.')
            try:
                finite = math.isfinite(value)
            except OverflowError:
                raise ValueError('CSV value is too large to represent.') from None
            if not finite:
                raise ValueError('CSV cells must be finite.')
        writer.writerow(row)
    return output.getvalue()


def generate_prices(price_min, price_max, count=101):
    """Generate an inclusive, evenly spaced teaching price grid."""
    for name, value in (("price_min", price_min), ("price_max", price_max)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be an int or float.")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            raise ValueError(f"{name} is too large to represent.") from None
        if not finite:
            raise ValueError(f"{name} must be finite.")
    if price_min < 0:
        raise ValueError("price_min must be zero or greater.")
    if price_max <= price_min:
        raise ValueError("price_max must be greater than price_min.")
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError("count must be an integer, not a boolean.")
    if count < 2:
        raise ValueError("count must be at least two.")

    step = (price_max - price_min) / (count - 1)
    prices = []
    for i in range(count):
        price = price_min + i * step
        prices.append(price)
    # Avoid an accumulated rounding difference at the inclusive endpoints.
    prices[0] = price_min
    prices[-1] = price_max
    return prices


def compare_prices(prices, quantity, futures_price, strike, premium):
    """Return one independent cost record per supplied terminal price.

    Scalar validation comes from the calculation functions. This teaching
    helper expects an iterable of prices; the future build_scenarios public
    interface will validate bounds and generate its own nonempty price grid.
    """
    rows = []

    for price in prices:
        row = {
            "terminal_price": price,
            "unhedged_cost": unhedged_cost(quantity, price),
            "futures_hedged_cost": futures_hedged_cost(
                quantity, price, futures_price
            ),
            "call_hedged_cost": call_hedged_cost(
                quantity, price, strike, premium
            ),
        }
        rows.append(row)

    return rows
