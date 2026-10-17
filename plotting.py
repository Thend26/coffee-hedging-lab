"""Static scientific plots built from the scenario records, not new formulas."""

import matplotlib.pyplot as plt


def plot_costs(rows):
    """Return a Matplotlib figure showing the three procurement costs."""
    if not rows:
        raise ValueError('At least one scenario is required.')
    prices = [row['terminal_price_usd_per_lb'] for row in rows]
    fig, ax = plt.subplots(figsize=(10, 6), layout='constrained')
    series = (
        ('Unhedged', 'unhedged_cost_usd', '#2864a3', '-'),
        ('Futures hedge', 'futures_hedged_cost_usd', '#bd6426', '--'),
        ('Call option hedge', 'call_hedged_cost_usd', '#218362', '-.'),
    )
    for label, field, color, style in series:
        costs = [row[field] for row in rows]
        ax.plot(prices, costs, label=label, color=color, linestyle=style, linewidth=2.5)
    ax.set_xlabel('Terminal coffee price (USD/lb)')
    ax.set_ylabel('Total procurement cost (USD)')
    ax.set_title('Coffee procurement costs under three hedging strategies',
                 loc='left', fontsize=14, fontweight='bold', pad=35)
    first = rows[0]
    ax.text(0, 1.035,
            f"Quantity: {first['quantity_lb']:g} lb | Futures: ${first['futures_price_usd_per_lb']:g}/lb | "
            f"Strike: ${first['strike_usd_per_lb']:g}/lb | Premium: ${first['premium_usd_per_lb']:g}/lb",
            transform=ax.transAxes, fontsize=10, color='#444444')
    ax.grid(True, alpha=.18)
    ax.legend(loc='upper left', frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    fig.supxlabel('Teaching scenarios: perfect matching; no basis, funding, fees or taxes.\n'
                  'Option premium included as an undiscounted cash expenditure; not a price forecast.',
                  fontsize=9, color='#555555')
    return fig
