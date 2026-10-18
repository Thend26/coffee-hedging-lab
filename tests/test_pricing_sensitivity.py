"""Controlled experiments must vary only their named inputs."""

import math
import unittest

from pricing import black76_call_values
from pricing_sensitivity import build_pricing_sensitivities


class PricingSensitivityTests(unittest.TestCase):
    def setUp(self):
        self.result = build_pricing_sensitivities(100, 100, .3, .5, .05)

    def test_grid_sizes_endpoints_and_fixed_inputs(self):
        self.assertEqual(set(self.result), {'volatility_curve', 'maturity_curve', 'heatmap'})
        vol = self.result['volatility_curve']
        maturity = self.result['maturity_curve']
        self.assertEqual(len(vol), 21)
        self.assertEqual(len(maturity), 21)
        self.assertEqual([row['volatility_annual'] for row in vol], [i/20 for i in range(21)])
        self.assertEqual([row['time_to_expiry_years'] for row in maturity], [i/10 for i in range(21)])
        self.assertTrue(all(row['time_to_expiry_years'] == .5 for row in vol))
        self.assertTrue(all(row['volatility_annual'] == .3 for row in maturity))
        pairs = {(row['volatility_annual'], row['time_to_expiry_years']) for row in self.result['heatmap']}
        self.assertEqual(len(self.result['heatmap']), 441)
        self.assertEqual(pairs, {(i/20, j/10) for i in range(21) for j in range(21)})

    def test_records_match_pricer_with_fixed_futures_strike_and_rate(self):
        for records in self.result.values():
            for row in records:
                self.assertEqual(set(row), {'volatility_annual', 'time_to_expiry_years', 'premium_today_usd_per_lb', 'premium_terminal_usd_per_lb'})
                self.assertTrue(all(math.isfinite(value) for value in row.values()))
                quote = black76_call_values(100, 100, row['volatility_annual'], row['time_to_expiry_years'], .05)
                for key in ('premium_today_usd_per_lb', 'premium_terminal_usd_per_lb'):
                    self.assertEqual(row[key], quote[key])

    def test_selected_point_agrees_in_all_three_experiments(self):
        selected = []
        for records in self.result.values():
            selected.append(next(row for row in records if row['volatility_annual'] == .3 and row['time_to_expiry_years'] == .5))
        self.assertEqual(selected[0], selected[1])
        self.assertEqual(selected[1], selected[2])

    def test_atm_zero_corners_and_volatility_monotonicity(self):
        for row in self.result['heatmap']:
            if row['volatility_annual'] == 0 or row['time_to_expiry_years'] == 0:
                self.assertEqual(row['premium_today_usd_per_lb'], 0)
                self.assertEqual(row['premium_terminal_usd_per_lb'], 0)
        prices = [row['premium_today_usd_per_lb'] for row in self.result['volatility_curve']]
        self.assertEqual(prices, sorted(prices))

    def test_invalid_selected_inputs_are_not_hidden_by_scans(self):
        for index, bad, error in ((0, 0, ValueError), (1, -1, ValueError),
                                  (2, -1, ValueError), (3, -1, ValueError),
                                  (2, True, TypeError), (3, '1', TypeError),
                                  (4, float('nan'), ValueError)):
            args = [100, 100, .3, .5, .05]
            args[index] = bad
            with self.subTest(index=index), self.assertRaises(error):
                build_pricing_sensitivities(*args)

    def test_zero_selected_inputs_and_negative_rates_are_valid(self):
        result = build_pricing_sensitivities(110, 100, 0, 0, -.05)
        self.assertTrue(all(row['premium_today_usd_per_lb'] == 10 for row in result['volatility_curve']))
        self.assertAlmostEqual(result['maturity_curve'][-1]['premium_today_usd_per_lb'], 11.051709180756477)


if __name__ == '__main__':
    unittest.main()
