"""Educational coffee procurement calculations in USD and pounds."""

import math


def call_hedged_cost(quantity: float, terminal_price: float,
                     strike: float, premium: float) -> float:
    """Return simplified USD cost including undiscounted option premium.

    Component functions validate quantity, terminal price and strike.
    Premium is USD per pound, finite and nonnegative; zero is allowed.
    """
    physical_cost = unhedged_cost(quantity, terminal_price)
    payoff = call_payoff(quantity, terminal_price, strike)

    if isinstance(premium, bool) or not isinstance(premium, (int, float)):
        raise TypeError("premium must be an int or float, not a boolean.")
    try:
        finite = math.isfinite(premium)
    except OverflowError:
        raise ValueError("premium is too large to represent.") from None
    if not finite:
        raise ValueError("premium must be finite.")
    if premium < 0:
        raise ValueError("premium must be zero or greater.")

    try:
        premium_cost = float(quantity * premium)
    except OverflowError:
        raise ValueError("Calculated premium cost is too large to represent.") from None
    if not math.isfinite(premium_cost):
        raise ValueError("Calculated premium cost must be finite.")

    # Equivalent to physical_cost - payoff, without subtracting large,
    # nearly equal amounts. Component calls above still validate cashflows.
    cost = float(quantity * min(terminal_price, strike)) + premium_cost
    if not math.isfinite(cost):
        raise ValueError("Calculated call-hedged cost must be finite.")
    return cost


def call_payoff(quantity: float, terminal_price: float, strike: float) -> float:
    """Return a long call's terminal payoff in USD, excluding premium."""
    for name, value in (("quantity", quantity), ("terminal_price", terminal_price),
                        ("strike", strike)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be an int or float, not a boolean.")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            raise ValueError(f"{name} is too large to represent.") from None
        if not finite:
            raise ValueError(f"{name} must be finite.")

    if quantity <= 0:
        raise ValueError("quantity must be greater than zero.")
    if terminal_price < 0:
        raise ValueError("terminal_price must be zero or greater.")
    if strike <= 0:
        raise ValueError("strike must be greater than zero.")

    try:
        payoff = float(quantity * max(terminal_price - strike, 0))
    except OverflowError:
        raise ValueError("Calculated payoff is too large to represent.") from None
    if not math.isfinite(payoff):
        raise ValueError("Calculated payoff must be finite.")
    return payoff


def futures_hedged_cost(quantity: float, terminal_price: float, futures_price: float) -> float:
    """Return simplified fully matched procurement cost, before funding/fees."""
    unhedged_cost(quantity, terminal_price)
    futures_pnl(quantity, terminal_price, futures_price)
    # Q*S - Q*(S-F) = Q*F; avoid catastrophic floating-point cancellation.
    try:
        cost = float(quantity * futures_price)
    except OverflowError:
        raise ValueError("Calculated hedged cost is too large to represent.") from None
    if not math.isfinite(cost):
        raise ValueError("Calculated hedged cost must be finite.")
    return cost


def futures_pnl(quantity: float, terminal_price: float, futures_price: float) -> float:
    """Return long futures P&L in USD; a finite loss is a valid result."""
    for name, value in (("quantity", quantity), ("terminal_price", terminal_price),
                        ("futures_price", futures_price)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be an int or float, not a boolean.")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            raise ValueError(f"{name} is too large to represent.") from None
        if not finite:
            raise ValueError(f"{name} must be finite.")

    if quantity <= 0:
        raise ValueError("quantity must be greater than zero.")
    if terminal_price < 0:
        raise ValueError("terminal_price must be zero or greater.")
    if futures_price <= 0:
        raise ValueError("futures_price must be greater than zero.")

    try:
        pnl = float(quantity * (terminal_price - futures_price))
    except OverflowError:
        raise ValueError("Calculated P&L is too large to represent.") from None
    if not math.isfinite(pnl):
        raise ValueError("Calculated P&L must be finite.")
    return pnl


def unhedged_cost(quantity: float, terminal_price: float) -> float:
    """Return quantity (lb) times terminal price (USD/lb).

    Accept ordinary int/float values, but not bool or numeric strings.
    Quantity must be positive and price nonnegative. Invalid types raise
    TypeError; invalid or unrepresentable values raise ValueError.
    """
    for name, value in (("quantity", quantity), ("terminal_price", terminal_price)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be an int or float, not a boolean.")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            raise ValueError(f"{name} is too large to represent.") from None
        if not finite:
            raise ValueError(f"{name} must be finite.")

    if quantity <= 0:
        raise ValueError("quantity must be greater than zero.")
    if terminal_price < 0:
        raise ValueError("terminal_price must be zero or greater.")

    try:
        cost = float(quantity * terminal_price)
    except OverflowError:
        raise ValueError("Calculated cost is too large to represent.") from None
    if not math.isfinite(cost):
        raise ValueError("Calculated cost must be finite.")
    return cost
