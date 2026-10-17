import unittest

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from plotting import plot_costs
from scenarios import build_scenarios


class PlotCostsTests(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_lines_use_exact_scenario_data_and_units(self):
        rows = build_scenarios(1000, 1.2, 1.22, 1.25, .07, .6, 1.8)
        fig = plot_costs(rows)
        ax = fig.axes[0]
        self.assertEqual(ax.get_xlabel(), 'Terminal coffee price (USD/lb)')
        self.assertEqual(ax.get_ylabel(), 'Total procurement cost (USD)')
        lines = {line.get_label(): line for line in ax.lines}
        fields = {'Unhedged': 'unhedged_cost_usd',
                  'Futures hedge': 'futures_hedged_cost_usd',
                  'Call option hedge': 'call_hedged_cost_usd'}
        for label, field in fields.items():
            self.assertEqual(list(lines[label].get_xdata()),
                             [row['terminal_price_usd_per_lb'] for row in rows])
            self.assertEqual(list(lines[label].get_ydata()), [row[field] for row in rows])

    def test_rejects_empty_data(self):
        with self.assertRaises(ValueError):
            plot_costs([])


if __name__ == '__main__':
    unittest.main()
