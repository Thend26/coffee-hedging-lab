"""Fixed-input Black–76 experiments, not forecasts or outcome probabilities."""

from pricing import black76_call_values


def build_pricing_sensitivities(futures_price, strike, volatility,
                                time_to_expiry, rate) -> dict:
    """Return volatility/maturity curves and their joint parameter grid.

    Volatility runs from 0 to 1 in 21 steps; maturity from 0 to 2 years
    in 21 steps. Each curve fixes the other selected parameter. All
    experiments hold the futures price, strike and annual rate fixed.
    """
    # Validate selected values even if a scan would replace them.
    black76_call_values(futures_price, strike, volatility, time_to_expiry, rate)

    def record(sigma, expiry):
        quote = black76_call_values(futures_price, strike, sigma, expiry, rate)
        return {
            'volatility_annual': sigma,
            'time_to_expiry_years': expiry,
            'premium_today_usd_per_lb': quote['premium_today_usd_per_lb'],
            'premium_terminal_usd_per_lb': quote['premium_terminal_usd_per_lb'],
        }

    sigmas = [i / 20 for i in range(21)]
    expiries = [i / 10 for i in range(21)]
    volatility_curve = []
    for sigma in sigmas:
        volatility_curve.append(record(sigma, time_to_expiry))

    maturity_curve = []
    for expiry in expiries:
        maturity_curve.append(record(volatility, expiry))

    heatmap = []
    for sigma in sigmas:
        for expiry in expiries:
            heatmap.append(record(sigma, expiry))

    return {
        'volatility_curve': volatility_curve,
        'maturity_curve': maturity_curve,
        'heatmap': heatmap,
    }
