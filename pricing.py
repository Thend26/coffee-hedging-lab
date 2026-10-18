"""Numerical primitives for the educational European Black–76 laboratory."""

import math


def normal_cdf(x: float) -> float:
    """Return P(Z <= x) for a standard normal random variable Z.

    Accept finite Python ints/floats, excluding booleans. Using erfc avoids
    subtractive cancellation in the small left tail.
    """
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise TypeError("x must be a number, not a boolean")
    try:
        finite = math.isfinite(x)
    except OverflowError as exc:
        raise ValueError("x must be representable as a finite float") from exc
    if not finite:
        raise ValueError("x must be finite")
    return 0.5 * math.erfc(-x / math.sqrt(2))


def discount_factor(rate: float, time_to_expiry: float) -> float:
    """Continuous discount factor exp(-rT), with T in years.

    Negative rates are allowed, but expiry must be nonnegative. Extremely
    small factors may round to zero; an overflowing factor is rejected.
    """
    for name, value in (("rate", rate), ("time_to_expiry", time_to_expiry)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a number, not a boolean")
        try:
            finite = math.isfinite(value)
        except OverflowError as exc:
            raise ValueError(f"{name} must be representable as a finite float") from exc
        if not finite:
            raise ValueError(f"{name} must be finite")
    if time_to_expiry < 0:
        raise ValueError("time_to_expiry must be nonnegative")
    try:
        factor = math.exp(-float(rate) * float(time_to_expiry))
    except OverflowError as exc:
        raise ValueError("discount factor exceeds the supported numeric range") from exc
    if not math.isfinite(factor):
        raise ValueError("discount factor exceeds the supported numeric range")
    return factor


def black76_call_values(futures_price: float, strike: float, volatility: float,
                        time_to_expiry: float, rate: float) -> dict:
    """European futures-call values per lb under the Black–76 assumptions.

    The terminal premium is the risk-neutral expected payoff, equivalently
    today's premium financed at the same deterministic rate to expiry. It is
    not the realised payoff in a particular terminal-price scenario.
    """
    inputs = (("futures_price", futures_price), ("strike", strike),
              ("volatility", volatility), ("time_to_expiry", time_to_expiry),
              ("rate", rate))
    for name, value in inputs:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a number, not a boolean")
        try:
            finite = math.isfinite(value)
        except OverflowError as exc:
            raise ValueError(f"{name} must be representable as a finite float") from exc
        if not finite:
            raise ValueError(f"{name} must be finite")
    f, k, sigma, t, r = (float(value) for _, value in inputs)
    if f <= 0 or k <= 0:
        raise ValueError("futures_price and strike must be positive")
    if sigma < 0 or t < 0:
        raise ValueError("volatility and time_to_expiry must be nonnegative")
    discount = discount_factor(r, t)
    total_volatility = sigma * math.sqrt(t)
    if not math.isfinite(total_volatility):
        raise ValueError("total volatility exceeds the supported numeric range")
    if total_volatility == 0:
        terminal = max(f - k, 0.0)
    elif f == k:
        # N(s/2)-N(-s/2) without cancellation for tiny s.
        terminal = f * math.erf(total_volatility / (2 * math.sqrt(2)))
    else:
        log_moneyness = math.log(f) - math.log(k)
        d1 = log_moneyness / total_volatility + total_volatility / 2
        d2 = log_moneyness / total_volatility - total_volatility / 2

        def cdf_limit(x):
            # Extreme finite inputs can produce infinite standardised scores.
            if math.isinf(x):
                return 1.0 if x > 0 else 0.0
            return normal_cdf(x)

        if f > k:
            # Intrinsic value + OTM put, by put-call parity.
            put = k * cdf_limit(-d2) - f * cdf_limit(-d1)
            terminal = (f - k) + put
        else:
            terminal = f * cdf_limit(d1) - k * cdf_limit(d2)
    today = discount * terminal
    if not math.isfinite(today) or not math.isfinite(terminal) or terminal < 0:
        raise ValueError("option value exceeds the supported numeric range")
    return {
        "premium_today_usd_per_lb": today,
        "premium_terminal_usd_per_lb": terminal,
        "discount_factor": discount,
    }
