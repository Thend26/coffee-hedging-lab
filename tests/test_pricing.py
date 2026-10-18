"""Numerical building blocks for the European Black–76 laboratory."""

import math
import unittest

from pricing import normal_cdf, discount_factor, black76_call_values


class NormalCdfTests(unittest.TestCase):
    def test_reference_probabilities(self):
        for x, expected in ((0, .5), (1, .8413447460685429),
                            (-1, .15865525393145707)):
            with self.subTest(x=x):
                self.assertAlmostEqual(normal_cdf(x), expected, places=14)

    def test_monotone_probabilities_stay_between_zero_and_one(self):
        values = [normal_cdf(x) for x in (-10, -3, -1, 0, 1, 3, 10)]
        self.assertTrue(all(0 <= value <= 1 for value in values))
        self.assertTrue(all(a <= b for a, b in zip(values, values[1:])))

    def test_symmetry(self):
        for x in (.1, 1, 3, 5):
            with self.subTest(x=x):
                self.assertAlmostEqual(normal_cdf(-x) + normal_cdf(x), 1, places=14)

    def test_preserves_small_left_tail_instead_of_cancelling_to_zero(self):
        value = normal_cdf(-10)
        self.assertGreater(value, 0)
        self.assertTrue(math.isclose(value, 7.61985302416047e-24, rel_tol=1e-12))

    def test_large_finite_inputs_saturate_without_overflow(self):
        self.assertEqual(normal_cdf(-1e308), 0)
        self.assertEqual(normal_cdf(1e308), 1)

    def test_rejects_nonnumeric_inputs_and_booleans(self):
        for value in ('1', True, False, None, [], 1+2j):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    normal_cdf(value)

    def test_rejects_nonfinite_or_unrepresentable_inputs(self):
        for value in (float('nan'), float('inf'), float('-inf'), 10**400):
            with self.subTest(value_type=type(value)):
                with self.assertRaises(ValueError):
                    normal_cdf(value)


class DiscountFactorTests(unittest.TestCase):
    def test_zero_rate_and_zero_expiry(self):
        self.assertEqual(discount_factor(0, 5), 1)
        self.assertEqual(discount_factor(.05, 0), 1)

    def test_positive_rate_discounts(self):
        self.assertAlmostEqual(discount_factor(math.log(2), 1), .5)
        self.assertAlmostEqual(discount_factor(.05, 1), .951229424500714)

    def test_negative_rate_is_allowed(self):
        self.assertAlmostEqual(discount_factor(-math.log(2), 1), 2)

    def test_negative_expiry_is_rejected(self):
        with self.assertRaises(ValueError):
            discount_factor(.05, -1)

    def test_rejects_invalid_types_in_either_argument(self):
        for value in ('1', True, False, None, [], 1+2j):
            for args in ((value, 1), (.05, value)):
                with self.subTest(args=args), self.assertRaises(TypeError):
                    discount_factor(*args)

    def test_rejects_nonfinite_or_unrepresentable_inputs_even_at_zero(self):
        for value in (float('nan'), float('inf'), float('-inf'), 10**400):
            for args in ((value, 0), (0, value)):
                with self.subTest(types=tuple(map(type, args))), self.assertRaises(ValueError):
                    discount_factor(*args)

    def test_overflow_is_a_value_error(self):
        with self.assertRaises(ValueError):
            discount_factor(-1000, 1)

    def test_extreme_positive_discount_underflows_to_zero(self):
        self.assertEqual(discount_factor(1000, 1), 0)


class Black76CallTests(unittest.TestCase):
    def test_atm_simplification_across_volatility_and_expiry(self):
        # Independent simplified identity: F * (2*N(sigma*sqrt(T)/2)-1).
        # Catches wrong d1/d2 signs or missing sqrt(T), using ordinary inputs
        # where subtracting probabilities is numerically safe.
        for sigma, expiry in ((.1, .25), (.2, 1), (.6, 2)):
            with self.subTest(sigma=sigma, expiry=expiry):
                d1 = sigma * math.sqrt(expiry) / 2
                d2 = -d1
                self.assertAlmostEqual(normal_cdf(d2), 1-normal_cdf(d1))
                expected_terminal = 100 * (2 * normal_cdf(d1) - 1)
                values = black76_call_values(100, 100, sigma, expiry, .05)
                self.assertAlmostEqual(values['premium_terminal_usd_per_lb'], expected_terminal, delta=1e-12)
                self.assertAlmostEqual(values['premium_today_usd_per_lb'], expected_terminal * math.exp(-.05*expiry), delta=1e-12)

    def test_independent_atm_fixture(self):
        values = black76_call_values(100, 100, .2, 1, .05)
        self.assertAlmostEqual(values['premium_today_usd_per_lb'], 7.57708214642728, delta=1e-10)
        self.assertAlmostEqual(values['premium_terminal_usd_per_lb'], 7.965567455405804, delta=1e-10)
        self.assertEqual(set(values), {'premium_today_usd_per_lb', 'premium_terminal_usd_per_lb', 'discount_factor'})

    def test_zero_volatility(self):
        for f, terminal in ((110, 10), (100, 0), (90, 0)):
            values = black76_call_values(f, 100, 0, 1, math.log(2))
            self.assertAlmostEqual(values['premium_today_usd_per_lb'], terminal / 2)
            self.assertEqual(values['premium_terminal_usd_per_lb'], terminal)

    def test_zero_expiry(self):
        values = black76_call_values(110, 100, .2, 0, .05)
        self.assertEqual(values['premium_today_usd_per_lb'], 10)
        self.assertEqual(values['premium_terminal_usd_per_lb'], 10)
        self.assertEqual(values['discount_factor'], 1)

    def test_bounds_and_financing_identity(self):
        for f in (50, 100, 150):
            for rate in (-.05, 0, .05):
                values = black76_call_values(f, 100, .3, .5, rate)
                today = values['premium_today_usd_per_lb']
                terminal = values['premium_terminal_usd_per_lb']
                self.assertGreaterEqual(terminal, max(f-100, 0))
                self.assertLessEqual(terminal, f)
                self.assertAlmostEqual(today * math.exp(rate*.5), terminal)

    def test_terminal_value_does_not_depend_on_rate(self):
        a = black76_call_values(100, 100, .2, 1, -.05)
        b = black76_call_values(100, 100, .2, 1, .05)
        self.assertEqual(a['premium_terminal_usd_per_lb'], b['premium_terminal_usd_per_lb'])
        self.assertGreater(a['premium_today_usd_per_lb'], b['premium_today_usd_per_lb'])

    def test_volatility_increases_value(self):
        values = [black76_call_values(100, 100, sigma, 1, .05)['premium_today_usd_per_lb'] for sigma in (0, .1, .2, .5)]
        self.assertEqual(values, sorted(values))

    def test_discounted_value_need_not_increase_with_expiry(self):
        short = black76_call_values(200, 100, .01, .5, .2)
        long = black76_call_values(200, 100, .01, 1, .2)
        self.assertLess(long['premium_today_usd_per_lb'], short['premium_today_usd_per_lb'])

    def test_extreme_moneyness_and_tiny_atm_volatility(self):
        self.assertEqual(black76_call_values(1e200, 1e-200, .2, 1, 0)['premium_terminal_usd_per_lb'], 1e200)
        tiny = black76_call_values(100, 100, 1e-16, 1, 0)['premium_terminal_usd_per_lb']
        self.assertTrue(math.isclose(tiny, 3.989422804014327e-15, rel_tol=1e-12))
        for f in (1, 10000):
            self.assertGreaterEqual(black76_call_values(f, 100, .001, 1, 0)['premium_terminal_usd_per_lb'], 0)

    def test_underflowed_today_value_does_not_destroy_terminal_value(self):
        values = black76_call_values(110, 100, 0, 1, 1000)
        self.assertEqual(values['premium_today_usd_per_lb'], 0)
        self.assertEqual(values['premium_terminal_usd_per_lb'], 10)

    def test_invalid_types_are_checked_before_boundary_returns(self):
        for index in range(5):
            for bad in ('1', True, None):
                args = [100, 100, 0, 0, .05]
                args[index] = bad
                with self.subTest(index=index, bad=bad), self.assertRaises(TypeError):
                    black76_call_values(*args)

    def test_invalid_domains_and_nonfinite_values(self):
        for index in range(5):
            invalid = [float('nan'), float('inf'), 10**400]
            if index < 2:
                invalid += [0, -1]
            elif index < 4:
                invalid += [-1]
            for bad in invalid:
                args = [100, 100, 0, 0, .05]
                args[index] = bad
                with self.subTest(index=index), self.assertRaises(ValueError):
                    black76_call_values(*args)

    def test_price_overflow_is_rejected(self):
        with self.assertRaises(ValueError):
            black76_call_values(1e308, 1, 0, 1, -10)


if __name__ == '__main__':
    unittest.main()
