"""Analytical break-even contracts, independent of a price sampling grid."""

import unittest

from analysis import break_even_vs_unhedged, budget_metrics, budget_summary
from calculations import (
    unhedged_cost, partial_futures_hedged_cost, partial_call_hedged_cost,
)


class BreakEvenTests(unittest.TestCase):
    def test_positive_premium_gives_two_points(self):
        result = break_even_vs_unhedged(1.22, 1.25, .07, .5)
        self.assertEqual(result, {
            'futures': {'kind': 'point', 'lower_usd_per_lb': 1.22,
                        'upper_usd_per_lb': 1.22},
            'call': {'kind': 'point', 'lower_usd_per_lb': 1.32,
                     'upper_usd_per_lb': 1.32},
        })

    def test_zero_hedge_gives_all_prices_even_without_premium(self):
        for premium in (0, .07):
            with self.subTest(premium=premium):
                result = break_even_vs_unhedged(1.22, 1.25, premium, 0)
                for strategy in ('futures', 'call'):
                    self.assertEqual(result[strategy], {
                        'kind': 'all_prices', 'lower_usd_per_lb': 0,
                        'upper_usd_per_lb': None})

    def test_zero_premium_gives_closed_call_interval(self):
        result = break_even_vs_unhedged(1.22, 1.25, 0, .5)
        self.assertEqual(result['call'], {
            'kind': 'interval', 'lower_usd_per_lb': 0,
            'upper_usd_per_lb': 1.25})
        self.assertEqual(result['futures']['kind'], 'point')
        self.assertEqual(result['futures']['lower_usd_per_lb'], 1.22)

    def test_positive_hedge_ratios_do_not_move_points(self):
        for ratio in (.01, .5, 1):
            with self.subTest(ratio=ratio):
                result = break_even_vs_unhedged(1.22, 1.25, .07, ratio)
                self.assertAlmostEqual(result['futures']['lower_usd_per_lb'], 1.22)
                self.assertAlmostEqual(result['call']['lower_usd_per_lb'], 1.32)

    def test_futures_savings_change_sign_at_returned_point(self):
        point = break_even_vs_unhedged(1.22, 1.25, .07, .5)['futures']['lower_usd_per_lb']
        for price, expected_savings in ((1, -110), (point, 0), (1.5, 140)):
            with self.subTest(price=price):
                self.assertAlmostEqual(unhedged_cost(1000, price)
                    - partial_futures_hedged_cost(1000, price, 1.22, .5), expected_savings)

    def test_call_savings_change_sign_at_returned_point(self):
        point = break_even_vs_unhedged(1.22, 1.25, .07, .5)['call']['lower_usd_per_lb']
        for price, expected_savings in ((1.25, -35), (point, 0), (1.5, 90)):
            with self.subTest(price=price):
                self.assertAlmostEqual(unhedged_cost(1000, price)
                    - partial_call_hedged_cost(1000, price, 1.25, .07, .5), expected_savings)

    def test_zero_premium_interval_matches_cost_equality(self):
        for price in (0, .5, 1.25):
            with self.subTest(price=price):
                self.assertAlmostEqual(partial_call_hedged_cost(1000, price, 1.25, 0, .5),
                                       unhedged_cost(1000, price))
        self.assertAlmostEqual(1500 - partial_call_hedged_cost(1000, 1.5, 1.25, 0, .5), 125)

    def test_rejects_invalid_types_in_all_inputs(self):
        for value in ('1', True, False, None, [], 1+2j):
            for index in range(4):
                args = [1.22, 1.25, .07, .5]
                args[index] = value
                with self.subTest(index=index, value=value):
                    with self.assertRaises(TypeError):
                        break_even_vs_unhedged(*args)

    def test_rejects_nonfinite_and_unrepresentable_inputs(self):
        for value in (float('nan'), float('inf'), float('-inf'), 10**400):
            for index in range(4):
                args = [1.22, 1.25, .07, .5]
                args[index] = value
                with self.subTest(index=index, value=value):
                    with self.assertRaises(ValueError):
                        break_even_vs_unhedged(*args)

    def test_validates_domains_even_at_zero_hedge(self):
        for args in ((0, 1, 0, 0), (-1, 1, 0, 0), (1, 0, 0, 0),
                     (1, -1, 0, 0), (1, 1, -.1, 0),
                     (1, 1, 0, -.1), (1, 1, 0, 1.1)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    break_even_vs_unhedged(*args)

    def test_rejects_nonfinite_point_from_finite_inputs(self):
        with self.assertRaises(ValueError):
            break_even_vs_unhedged(1, 1e308, 1e308, .5)


class BudgetTests(unittest.TestCase):
    def test_gap_and_overspend_below_equal_above_budget(self):
        for cost, gap, excess in ((1200, -100, 0), (1300, 0, 0), (1410, 110, 110)):
            with self.subTest(cost=cost):
                self.assertEqual(budget_metrics(cost, 1300),
                                 {'budget_gap_usd': gap, 'overspend_usd': excess})

    def test_zero_budget(self):
        self.assertEqual(budget_metrics(35, 0),
                         {'budget_gap_usd': 35, 'overspend_usd': 35})

    def test_invalid_metric_inputs(self):
        for index in range(2):
            for value in ('1300', True, None):
                args = [1000, 1300]
                args[index] = value
                with self.assertRaises(TypeError):
                    budget_metrics(*args)
            for value in (-1, float('nan'), float('inf'), 10**400):
                args = [1000, 1300]
                args[index] = value
                with self.assertRaises(ValueError):
                    budget_metrics(*args)

    def test_summary_counts_strict_exceedance_and_interval_maxima(self):
        rows = [dict(budget_usd=1300, unhedged_cost_usd=u,
                     futures_hedged_cost_usd=f, call_hedged_cost_usd=c)
                for u, f, c in ((1200, 1210, 1235), (1300, 1260, 1310),
                                (1500, 1360, 1410))]
        result = budget_summary(rows)
        self.assertEqual(result['unhedged'],
                         dict(exceedance_count=1, max_cost_usd=1500, max_overspend_usd=200))
        self.assertEqual(result['futures_hedged'],
                         dict(exceedance_count=1, max_cost_usd=1360, max_overspend_usd=60))
        self.assertEqual(result['call_hedged'],
                         dict(exceedance_count=2, max_cost_usd=1410, max_overspend_usd=110))
        self.assertEqual(budget_summary(rows[:1])['call_hedged']['max_cost_usd'], 1235)

    def test_summary_all_or_no_scenarios_exceed(self):
        for budget, count, overspend in ((0, 2, 200), (200, 0, 0)):
            rows = [dict(budget_usd=budget, unhedged_cost_usd=c,
                         futures_hedged_cost_usd=c, call_hedged_cost_usd=c)
                    for c in (100, 200)]
            for result in budget_summary(rows).values():
                self.assertEqual(result, dict(exceedance_count=count, max_cost_usd=200,
                                              max_overspend_usd=overspend))

    def test_summary_rejects_empty_inconsistent_or_invalid_rows(self):
        with self.assertRaises(ValueError):
            budget_summary([])
        row = dict(budget_usd=1300, unhedged_cost_usd=1000,
                   futures_hedged_cost_usd=1220, call_hedged_cost_usd=1070)
        with self.assertRaises(ValueError):
            budget_summary([row, dict(row, budget_usd=1400)])
        with self.assertRaises(ValueError):
            budget_summary([dict(row, call_hedged_cost_usd=float('nan'))])


if __name__ == '__main__':
    unittest.main()
