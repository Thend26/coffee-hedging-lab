import unittest

from calculations import (
    unhedged_cost, futures_pnl, futures_hedged_cost, call_payoff, call_hedged_cost,
    partial_futures_hedged_cost, partial_call_hedged_cost,
)


class PartialFuturesCostTests(unittest.TestCase):
    def test_zero_half_and_full_hedge_costs(self):
        for ratio, expected in ((0, 1500), (0.5, 1360), (1, 1220)):
            with self.subTest(ratio=ratio):
                self.assertAlmostEqual(
                    partial_futures_hedged_cost(1000, 1.5, 1.22, ratio), expected)

    def test_full_hedge_matches_legacy(self):
        for price in (0, 1, 1.22, 1.8, 1e20):
            with self.subTest(price=price):
                self.assertEqual(partial_futures_hedged_cost(1000, price, 1.22, 1),
                                 futures_hedged_cost(1000, price, 1.22))

    def test_quantity_scaling(self):
        self.assertAlmostEqual(partial_futures_hedged_cost(2000, 1.5, 1.22, .5), 2720)
        self.assertAlmostEqual(partial_futures_hedged_cost(2.5, 1.5, 1.22, .5), 3.4)

    def test_zero_terminal_price(self):
        self.assertAlmostEqual(partial_futures_hedged_cost(1000, 0, 1.22, .5), 610)

    def test_half_hedge_residual_price_sensitivity(self):
        low = partial_futures_hedged_cost(1000, 1, 1.22, .5)
        high = partial_futures_hedged_cost(1000, 1.1, 1.22, .5)
        self.assertAlmostEqual(high - low, 50)

    def test_rejects_invalid_types_in_every_parameter(self):
        for value in ('0.5', True, False, None, [], 1+2j):
            for index in range(4):
                args = [1000, 1.5, 1.22, .5]
                args[index] = value
                with self.subTest(index=index, value=value):
                    with self.assertRaises(TypeError):
                        partial_futures_hedged_cost(*args)

    def test_rejects_nonfinite_or_unrepresentable_inputs(self):
        for value in (float('nan'), float('inf'), float('-inf'), 10**400):
            for index in range(4):
                args = [1000, 1.5, 1.22, .5]
                args[index] = value
                with self.subTest(index=index, value=value):
                    with self.assertRaises(ValueError):
                        partial_futures_hedged_cost(*args)

    def test_rejects_invalid_domains_even_at_zero_hedge(self):
        for args in ((0, 1, 1, .5), (-1, 1, 1, .5), (1, -1, 1, .5),
                     (1, 1, 0, 0), (1, 1, -1, 0),
                     (1, 1, 1, -.1), (1, 1, 1, 1.1)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    partial_futures_hedged_cost(*args)

    def test_rejects_output_overflow(self):
        with self.assertRaises(ValueError):
            partial_futures_hedged_cost(1e308, 1e308, 1, .5)


class PartialCallCostTests(unittest.TestCase):
    def test_half_hedge_below_and_above_strike(self):
        for price, expected in ((1, 1035), (1.5, 1410)):
            with self.subTest(price=price):
                self.assertAlmostEqual(
                    partial_call_hedged_cost(1000, price, 1.25, .07, .5), expected)

    def test_zero_hedge_matches_unhedged(self):
        for price in (0, 1, 1.25, 1.8):
            with self.subTest(price=price):
                self.assertEqual(partial_call_hedged_cost(1000, price, 1.25, .07, 0),
                                 unhedged_cost(1000, price))

    def test_full_hedge_matches_legacy(self):
        for price in (0, 1, 1.25, 1.8, 1e20):
            with self.subTest(price=price):
                self.assertAlmostEqual(
                    partial_call_hedged_cost(1000, price, 1.25, .07, 1),
                    call_hedged_cost(1000, price, 1.25, .07))

    def test_quantity_scaling(self):
        self.assertAlmostEqual(partial_call_hedged_cost(2000, 1.5, 1.25, .07, .5), 2820)
        self.assertAlmostEqual(partial_call_hedged_cost(2.5, 1.5, 1.25, .07, .5), 3.525)

    def test_continuity_and_slopes_at_strike(self):
        below = partial_call_hedged_cost(1000, 1.24, 1.25, .07, .5)
        at_strike = partial_call_hedged_cost(1000, 1.25, 1.25, .07, .5)
        above = partial_call_hedged_cost(1000, 1.26, 1.25, .07, .5)
        self.assertAlmostEqual(at_strike, 1285)
        self.assertAlmostEqual(at_strike - below, 10)
        self.assertAlmostEqual(above - at_strike, 5)

    def test_premium_increase_scales_with_hedged_quantity(self):
        for price in (0, 1, 1.25, 1.8):
            with self.subTest(price=price):
                low = partial_call_hedged_cost(1000, price, 1.25, .07, .5)
                high = partial_call_hedged_cost(1000, price, 1.25, .10, .5)
                self.assertAlmostEqual(high - low, 15)

    def test_allows_zero_premium(self):
        self.assertAlmostEqual(partial_call_hedged_cost(1000, 1.5, 1.25, 0, .5), 1375)

    def test_zero_terminal_price_only_pays_hedged_premium(self):
        self.assertAlmostEqual(partial_call_hedged_cost(1000, 0, 1.25, .07, .5), 35)

    def test_rejects_invalid_types_in_every_parameter(self):
        for value in ('0.5', True, False, None, [], 1+2j):
            for index in range(5):
                args = [1000, 1.5, 1.25, .07, .5]
                args[index] = value
                with self.subTest(index=index, value=value):
                    with self.assertRaises(TypeError):
                        partial_call_hedged_cost(*args)

    def test_rejects_nonfinite_or_unrepresentable_inputs(self):
        for value in (float('nan'), float('inf'), float('-inf'), 10**400):
            for index in range(5):
                args = [1000, 1.5, 1.25, .07, .5]
                args[index] = value
                with self.subTest(index=index, value=value):
                    with self.assertRaises(ValueError):
                        partial_call_hedged_cost(*args)

    def test_rejects_invalid_domains_even_at_zero_hedge(self):
        for args in ((0, 1, 1, 0, .5), (-1, 1, 1, 0, .5),
                     (1, -1, 1, 0, .5), (1, 1, 0, 0, 0),
                     (1, 1, -1, 0, 0), (1, 1, 1, -.01, 0),
                     (1, 1, 1, 0, -.1), (1, 1, 1, 0, 1.1)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    partial_call_hedged_cost(*args)

    def test_rejects_output_overflow(self):
        for args in ((1e308, 1e308, 1, 0, .5), (1e308, 1, 1, 1e308, .5)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    partial_call_hedged_cost(*args)


class UnhedgedCostTests(unittest.TestCase):
    def test_multiplies_quantity_by_price(self):
        self.assertEqual(unhedged_cost(1000, 1.5), 1500)

    def test_allows_zero_terminal_price(self):
        self.assertEqual(unhedged_cost(1000, 0), 0)

    def test_allows_fractional_quantity(self):
        self.assertAlmostEqual(unhedged_cost(2.5, 1.2), 3)

    def test_rejects_nonpositive_quantity(self):
        for quantity in (0, -1):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    unhedged_cost(quantity, 1.5)

    def test_rejects_negative_price(self):
        with self.assertRaises(ValueError):
            unhedged_cost(1000, -1)

    def test_rejects_nonnumeric_inputs_and_booleans(self):
        for value in ('1000', True, False, None, [], 1 + 2j):
            for args in ((value, 1.5), (1000, value)):
                with self.subTest(args=args):
                    with self.assertRaises(TypeError):
                        unhedged_cost(*args)

    def test_rejects_nonfinite_inputs(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            for args in ((value, 1.5), (1000, value)):
                with self.subTest(args=args):
                    with self.assertRaises(ValueError):
                        unhedged_cost(*args)

    def test_rejects_nonfinite_result(self):
        with self.assertRaises(ValueError):
            unhedged_cost(1e308, 1e308)


class FuturesPnlTests(unittest.TestCase):
    def test_profit_when_price_rises(self):
        self.assertAlmostEqual(futures_pnl(1000, 1.5, 1.22), 280)

    def test_loss_when_price_falls(self):
        self.assertAlmostEqual(futures_pnl(1000, 1.0, 1.22), -220)

    def test_zero_when_prices_equal(self):
        self.assertEqual(futures_pnl(1000, 1.22, 1.22), 0)

    def test_zero_terminal_price_and_fractional_quantity(self):
        self.assertAlmostEqual(futures_pnl(2.5, 0, 1.2), -3)

    def test_quantity_doubling_doubles_pnl(self):
        self.assertAlmostEqual(futures_pnl(2000, 1.5, 1.22), 560)

    def test_rejects_invalid_ranges(self):
        for args in ((0, 1, 1), (-1, 1, 1), (1000, -1, 1),
                     (1000, 1, 0), (1000, 1, -1)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    futures_pnl(*args)

    def test_rejects_invalid_types(self):
        for value in ('1.5', True, False, None, [], 1 + 2j):
            for index in range(3):
                args = [1000, 1.5, 1.22]
                args[index] = value
                with self.subTest(args=args):
                    with self.assertRaises(TypeError):
                        futures_pnl(*args)

    def test_rejects_nonfinite_values(self):
        for value in (float('nan'), float('inf'), float('-inf'), 10**400):
            for index in range(3):
                args = [1000, 1.5, 1.22]
                args[index] = value
                with self.subTest(index=index):
                    with self.assertRaises(ValueError):
                        futures_pnl(*args)

    def test_rejects_result_overflow(self):
        for args in ((1e308, 3, 1), (1e308, 1, 3)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    futures_pnl(*args)


class FuturesHedgedCostTests(unittest.TestCase):
    def test_cost_after_price_rises(self):
        self.assertAlmostEqual(futures_hedged_cost(1000, 1.5, 1.22), 1220)

    def test_cost_after_price_falls(self):
        self.assertAlmostEqual(futures_hedged_cost(1000, 1.0, 1.22), 1220)

    def test_cost_when_prices_equal(self):
        self.assertAlmostEqual(futures_hedged_cost(1000, 1.22, 1.22), 1220)

    def test_zero_terminal_price_and_fractional_quantity(self):
        self.assertAlmostEqual(futures_hedged_cost(2.5, 0, 1.2), 3)

    def test_quantity_doubling_doubles_cost(self):
        self.assertAlmostEqual(futures_hedged_cost(2000, 1.5, 1.22), 2440)

    def test_reuses_type_validation(self):
        for value in ('1.5', True, False, None, [], 1 + 2j):
            for index in range(3):
                args = [1000, 1.5, 1.22]
                args[index] = value
                with self.subTest(args=args):
                    with self.assertRaises(TypeError):
                        futures_hedged_cost(*args)

    def test_reuses_range_validation(self):
        for args in ((0, 1, 1), (-1, 1, 1), (1000, -1, 1),
                     (1000, 1, 0), (1000, 1, -1)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    futures_hedged_cost(*args)

    def test_reuses_finite_input_validation(self):
        for value in (float('nan'), float('inf'), float('-inf'), 10**400):
            for index in range(3):
                args = [1000, 1.5, 1.22]
                args[index] = value
                with self.subTest(index=index):
                    with self.assertRaises(ValueError):
                        futures_hedged_cost(*args)

    def test_rejects_intermediate_overflow(self):
        for args in ((1e308, 3, 1), (1e308, 0, 3)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    futures_hedged_cost(*args)

    def test_rejects_combined_cost_overflow(self):
        with self.assertRaises(ValueError):
            futures_hedged_cost(1e308, 1, 2)


class CallPayoffTests(unittest.TestCase):
    def test_positive_payoff_above_strike(self):
        self.assertAlmostEqual(call_payoff(1000, 1.5, 1.25), 250)

    def test_zero_payoff_below_strike(self):
        self.assertEqual(call_payoff(1000, 1.0, 1.25), 0)

    def test_zero_payoff_at_strike(self):
        self.assertEqual(call_payoff(1000, 1.25, 1.25), 0)

    def test_zero_terminal_price(self):
        self.assertEqual(call_payoff(1000, 0, 1.25), 0)

    def test_fractional_quantity(self):
        self.assertAlmostEqual(call_payoff(2.5, 1.5, 1.25), 0.625)

    def test_quantity_doubling(self):
        self.assertAlmostEqual(call_payoff(2000, 1.5, 1.25), 500)

    def test_rejects_invalid_ranges(self):
        for args in ((0, 1, 1), (-1, 1, 1), (1000, -1, 1),
                     (1000, 1, 0), (1000, 1, -1)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    call_payoff(*args)

    def test_rejects_invalid_types(self):
        for value in ('1.5', True, False, None, [], 1 + 2j):
            for index in range(3):
                args = [1000, 1.5, 1.25]
                args[index] = value
                with self.subTest(args=args):
                    with self.assertRaises(TypeError):
                        call_payoff(*args)

    def test_rejects_nonfinite_inputs(self):
        for value in (float('nan'), float('inf'), float('-inf'), 10**400):
            for index in range(3):
                args = [1000, 1.5, 1.25]
                args[index] = value
                with self.subTest(index=index):
                    with self.assertRaises(ValueError):
                        call_payoff(*args)

    def test_rejects_payoff_overflow(self):
        with self.assertRaises(ValueError):
            call_payoff(1e308, 3, 1)


class CallHedgedCostTests(unittest.TestCase):
    def test_cost_above_strike(self):
        self.assertAlmostEqual(call_hedged_cost(1000, 1.5, 1.25, .07), 1320)

    def test_cost_below_strike(self):
        self.assertAlmostEqual(call_hedged_cost(1000, 1, 1.25, .07), 1070)

    def test_cost_at_strike(self):
        self.assertAlmostEqual(call_hedged_cost(1000, 1.25, 1.25, .07), 1320)

    def test_zero_premium(self):
        self.assertAlmostEqual(call_hedged_cost(1000, 1.5, 1.25, 0), 1250)

    def test_zero_terminal_price(self):
        self.assertAlmostEqual(call_hedged_cost(1000, 0, 1.25, .07), 70)

    def test_fractional_quantity(self):
        self.assertAlmostEqual(call_hedged_cost(2.5, 1.5, 1.25, .07), 3.3)

    def test_quantity_doubling(self):
        self.assertAlmostEqual(call_hedged_cost(2000, 1.5, 1.25, .07), 2640)

    def test_premium_increase(self):
        self.assertAlmostEqual(call_hedged_cost(1000, 1.5, 1.25, .08), 1330)

    def test_rejects_invalid_types(self):
        for value in ('0.07', True, False, None, [], 1 + 2j):
            for index in range(4):
                args = [1000, 1.5, 1.25, .07]
                args[index] = value
                with self.subTest(index=index, value=value):
                    with self.assertRaises(TypeError):
                        call_hedged_cost(*args)

    def test_rejects_invalid_ranges(self):
        for args in ((0, 1, 1, .07), (-1, 1, 1, .07),
                     (1000, -1, 1, .07), (1000, 1, 0, .07),
                     (1000, 1, -1, .07), (1000, 1, 1, -.07)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    call_hedged_cost(*args)

    def test_rejects_nonfinite_values(self):
        for value in (float('nan'), float('inf'), float('-inf'), 10**400):
            for index in range(4):
                args = [1000, 1.5, 1.25, .07]
                args[index] = value
                with self.subTest(index=index):
                    with self.assertRaises(ValueError):
                        call_hedged_cost(*args)

    def test_rejects_premium_overflow(self):
        with self.assertRaises(ValueError):
            call_hedged_cost(1e308, 0, 1, 3)

    def test_rejects_final_sum_overflow(self):
        with self.assertRaises(ValueError):
            call_hedged_cost(1e308, 1, 1, 1)

    def test_rejects_component_overflow(self):
        with self.assertRaises(ValueError):
            call_hedged_cost(1e308, 3, 1, 0)


if __name__ == '__main__':
    unittest.main()
