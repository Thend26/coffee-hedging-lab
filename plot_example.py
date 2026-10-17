"""Save the independent example's three-strategy cost chart."""

from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plotting import plot_costs
from scenarios import build_scenarios


def main():
    rows = build_scenarios(1000, 1.2, 1.22, 1.25, .07, .6, 1.8)
    fig = plot_costs(rows)
    output = Path(__file__).parent / 'output' / 'coffee_hedging_costs.png'
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(output)


if __name__ == '__main__':
    main()
