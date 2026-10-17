import unittest

from scenarios import compare_prices, generate_prices


class ComparePricesTests(unittest.TestCase):
    def test_returns_all_three_scenarios(self):
        rows = compare_prices([1, 1.25, 1.5], 1000, 1.22, 1.25, .07)
        self.assertEqual(len(rows), 3)
        expected = [(1, 1000, 1220, 1070), (1.25, 1250, 1220, 1320),
                    (1.5, 1500, 1220, 1320)]
        keys = ('terminal_price', 'unhedged_cost',
                'futures_hedged_cost', 'call_hedged_cost')
        for row, values in zip(rows, expected):
            self.assertEqual(set(row), set(keys))
            for key, value in zip(keys, values):
                self.assertAlmostEqual(row[key], value)

    def test_preserves_order_and_duplicate_prices(self):
        rows = compare_prices([1.5, 1, 1.5], 1000, 1.22, 1.25, .07)
        self.assertEqual([row['terminal_price'] for row in rows], [1.5, 1, 1.5])

    def test_uses_supplied_parameters(self):
        row = compare_prices([3], 2.5, 2.2, 2.5, .1)[0]
        self.assertAlmostEqual(row['unhedged_cost'], 7.5)
        self.assertAlmostEqual(row['futures_hedged_cost'], 5.5)
        self.assertAlmostEqual(row['call_hedged_cost'], 6.5)

    def test_returns_independent_records(self):
        rows = compare_prices([1, 1.5], 1000, 1.22, 1.25, .07)
        rows[0]['call_hedged_cost'] = -999
        self.assertAlmostEqual(rows[1]['call_hedged_cost'], 1320)

    def test_invalid_price_does_not_return_partial_results(self):
        with self.assertRaises(ValueError):
            compare_prices([1, -1, 1.5], 1000, 1.22, 1.25, .07)


class GeneratePricesTests(unittest.TestCase):
    def test_five_points(self):
        actual = generate_prices(.6, 1.8, 5)
        self.assertEqual(len(actual), 5)
        for value, expected in zip(actual, [.6, .9, 1.2, 1.5, 1.8]):
            self.assertAlmostEqual(value, expected)

    def test_default_grid_has_101_points_and_exact_endpoints(self):
        prices = generate_prices(.6, 1.8)
        self.assertEqual(len(prices), 101)
        self.assertEqual(prices[0], .6)
        self.assertEqual(prices[-1], 1.8)
        self.assertAlmostEqual(prices[1] - prices[0], .012)
        self.assertAlmostEqual(prices[50], 1.2)
        self.assertTrue(all(a < b for a, b in zip(prices, prices[1:])))

    def test_two_points_with_zero_lower_bound(self):
        self.assertEqual(generate_prices(0, 1, 2), [0, 1])

    def test_rejects_invalid_bounds(self):
        for bounds in ((1, 1), (2, 1), (-1, 1),
                       (float('nan'), 1), (0, float('inf')),
                       (0, 10**400)):
            with self.subTest(bounds=bounds):
                with self.assertRaises(ValueError):
                    generate_prices(*bounds)

    def test_rejects_invalid_types(self):
        for args in (('0', 1, 5), (0, True, 5), (0, 1, True),
                     (0, 1, 5.0), (0, 1, '5')):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    generate_prices(*args)

    def test_rejects_too_few_points(self):
        for count in (-1, 0, 1):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    generate_prices(0, 1, count)

    def test_generated_grid_can_feed_comparison(self):
        rows = compare_prices(generate_prices(.6, 1.8), 1000, 1.22, 1.25, .07)
        self.assertEqual(len(rows), 101)
        self.assertAlmostEqual(rows[0]['call_hedged_cost'], 670)
        self.assertAlmostEqual(rows[-1]['call_hedged_cost'], 1320)
        for row in rows:
            self.assertAlmostEqual(row['futures_hedged_cost'], 1220)


if __name__ == '__main__':
    unittest.main()
