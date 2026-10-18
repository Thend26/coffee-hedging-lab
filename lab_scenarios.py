"""Black–76 premiums adapted to terminal-valued procurement scenarios.

Unlike V2's simplified premium assumption, premium_usd_per_lb and
option_premium_usd here explicitly represent amounts at expiry T.
"""

import math
import csv
import io

from pricing import black76_call_values
from scenarios import build_scenarios, SCENARIO_FIELDS


LAB_SCENARIO_FIELDS = SCENARIO_FIELDS + (
    'volatility_annual', 'time_to_expiry_years', 'risk_free_rate_annual',
    'model_premium_today_usd_per_lb', 'model_premium_terminal_usd_per_lb',
    'total_premium_today_usd', 'total_premium_terminal_usd', 'discount_factor',
)


def lab_scenarios_to_csv(rows) -> str:
    """Serialize lab records unrounded, with an explicit 32-field schema.

    All cost/budget fields are terminal amounts; current premiums are separate
    metadata. Return text for UTF-8 encoding at the eventual download boundary.
    """
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=LAB_SCENARIO_FIELDS,
                            lineterminator='\n')
    writer.writeheader()
    for row in rows:
        if set(row) != set(LAB_SCENARIO_FIELDS):
            raise ValueError('CSV records must have exactly the lab scenario fields.')
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


def build_lab_scenarios(quantity, current_spot, futures_price, strike,
                        volatility, time_to_expiry, rate, price_min, price_max,
                        hedge_ratio=1.0, budget_usd=1300.0) -> list[dict]:
    """Compare terminal costs, financing the premium at the pricing rate.

    Assumes European cash settlement and perfect spot/futures matching at T.
    Budgets are terminal amounts. The current spot is a reference only.
    """
    quote = black76_call_values(futures_price, strike, volatility,
                               time_to_expiry, rate)
    rows = build_scenarios(
        quantity, current_spot, futures_price, strike,
        quote['premium_terminal_usd_per_lb'], price_min, price_max,
        hedge_ratio, budget_usd,
    )
    total_today = quantity * hedge_ratio * quote['premium_today_usd_per_lb']
    if not math.isfinite(total_today):
        raise ValueError('Total current premium exceeds the supported numeric range.')
    for row in rows:
        row.update({
            'volatility_annual': volatility,
            'time_to_expiry_years': time_to_expiry,
            'risk_free_rate_annual': rate,
            'model_premium_today_usd_per_lb': quote['premium_today_usd_per_lb'],
            'model_premium_terminal_usd_per_lb': quote['premium_terminal_usd_per_lb'],
            'total_premium_today_usd': total_today,
            'total_premium_terminal_usd': row['option_premium_usd'],
            'discount_factor': quote['discount_factor'],
        })
    return rows
