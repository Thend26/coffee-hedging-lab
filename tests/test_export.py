import csv
import io
import math
import unittest

from scenarios import build_scenarios, scenarios_to_csv
from calculations import futures_hedged_cost, call_hedged_cost


FIELDS = [
    'quantity_lb', 'current_spot_usd_per_lb', 'futures_price_usd_per_lb',
    'strike_usd_per_lb', 'premium_usd_per_lb', 'terminal_price_usd_per_lb',
    'physical_cost_usd', 'futures_pnl_usd', 'call_payoff_usd',
    'option_premium_usd', 'unhedged_cost_usd', 'futures_hedged_cost_usd',
    'call_hedged_cost_usd',
    'hedge_ratio', 'budget_usd',
]
for prefix in ('unhedged', 'futures_hedged', 'call_hedged'):
    FIELDS.extend([f'{prefix}_savings_vs_unhedged_usd',
                   f'{prefix}_budget_gap_usd', f'{prefix}_overspend_usd'])


class FormalScenarioTests(unittest.TestCase):
    def build(self, **changes):
        params = dict(quantity=1000, current_spot=1.2, futures_price=1.22,
                      strike=1.25, premium=.07, price_min=.6, price_max=1.8)
        params.update(changes)
        return build_scenarios(**params)

    def test_schema_and_literal_results(self):
        rows = self.build()
        self.assertEqual(len(rows), 101)
        self.assertEqual(list(rows[0]), FIELDS)
        for row, wanted in ((rows[0], [.6, 600, -620, 0, 70, 600, 1220, 670]),
                            (rows[-1], [1.8, 1800, 580, 550, 70, 1800, 1220, 1320])):
            self.assertEqual([row[k] for k in FIELDS[:5]], [1000, 1.2, 1.22, 1.25, .07])
            for key, value in zip(FIELDS[5:13], wanted):
                self.assertAlmostEqual(row[key], value)

    def test_partial_hedge_cashflows_and_budget_fields(self):
        rows = self.build(hedge_ratio=.5, budget_usd=1300)
        last = rows[-1]
        for key, expected in {'futures_pnl_usd': 290, 'call_payoff_usd': 275,
                              'option_premium_usd': 35, 'unhedged_cost_usd': 1800,
                              'futures_hedged_cost_usd': 1510,
                              'call_hedged_cost_usd': 1560,
                              'futures_hedged_savings_vs_unhedged_usd': 290,
                              'call_hedged_budget_gap_usd': 260,
                              'call_hedged_overspend_usd': 260}.items():
            self.assertAlmostEqual(last[key], expected)
        self.assertEqual(len(rows), 101)
        for row in rows:
            self.assertEqual(row['hedge_ratio'], .5)
            self.assertEqual(row['budget_usd'], 1300)
            for prefix in ('unhedged', 'futures_hedged', 'call_hedged'):
                cost = row[f'{prefix}_cost_usd']
                self.assertAlmostEqual(row[f'{prefix}_budget_gap_usd'], cost - 1300)
                self.assertAlmostEqual(row[f'{prefix}_overspend_usd'], max(cost - 1300, 0))
                self.assertAlmostEqual(row[f'{prefix}_savings_vs_unhedged_usd'],
                                       row['unhedged_cost_usd'] - cost)

    def test_zero_hedge_has_no_derivative_cashflows(self):
        for row in self.build(hedge_ratio=0):
            for key in ('futures_pnl_usd', 'call_payoff_usd', 'option_premium_usd'):
                self.assertEqual(row[key], 0)
            self.assertEqual(row['futures_hedged_cost_usd'], row['unhedged_cost_usd'])
            self.assertEqual(row['call_hedged_cost_usd'], row['unhedged_cost_usd'])

    def test_new_inputs_reject_invalid_values(self):
        for name in ('hedge_ratio', 'budget_usd'):
            for value in (-1, float('nan'), float('inf')):
                with self.assertRaises(ValueError):
                    self.build(**{name: value})
            for value in (True, '1'):
                with self.assertRaises(TypeError):
                    self.build(**{name: value})
        with self.assertRaises(ValueError):
            self.build(hedge_ratio=1.1)

    def test_partial_hedge_csv_roundtrip(self):
        rows = self.build(hedge_ratio=.37, budget_usd=1350.123456789)
        saved = list(csv.DictReader(io.StringIO(scenarios_to_csv(rows))))
        for source, restored in zip(rows, saved):
            for key in FIELDS:
                self.assertEqual(float(restored[key]), source[key])

    def test_current_spot_only_changes_reference(self):
        for before, after in zip(self.build(), self.build(current_spot=9)):
            for key in FIELDS:
                if key != 'current_spot_usd_per_lb':
                    self.assertEqual(before[key], after[key])

    def test_rejects_bad_reference_price(self):
        for value in (0, -1, float('inf'), float('nan'), 10**400):
            with self.subTest(value_type=type(value)):
                with self.assertRaises(ValueError):
                    self.build(current_spot=value)
        for value in ('1.2', True, None):
            with self.assertRaises(TypeError):
                self.build(current_spot=value)

    def test_rejects_bad_bounds_and_scalars(self):
        for changes in (dict(price_min=1, price_max=1), dict(price_min=2, price_max=1),
                        dict(price_min=-1), dict(price_max=float('inf')),
                        dict(quantity=0), dict(futures_price=0), dict(strike=0),
                        dict(premium=-1)):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    self.build(**changes)

    def test_rejects_unresolvable_grid(self):
        with self.assertRaises(ValueError):
            self.build(price_min=1.0, price_max=math.nextafter(1, 2))

    def test_rejects_overflowing_output(self):
        with self.assertRaises(ValueError):
            self.build(quantity=1e308, price_min=1, price_max=3)

    def test_csv_roundtrip_all_cells(self):
        rows = self.build()
        reader = csv.DictReader(io.StringIO(scenarios_to_csv(rows)))
        saved = list(reader)
        self.assertEqual(reader.fieldnames, FIELDS)
        self.assertEqual(len(saved), 101)
        for source, recovered in zip(rows, saved):
            for key in FIELDS:
                self.assertEqual(float(recovered[key]), source[key])

    def test_csv_preserves_precision(self):
        rows = self.build(premium=.07123456789)
        saved = list(csv.DictReader(io.StringIO(scenarios_to_csv(rows))))
        self.assertEqual(float(saved[0]['premium_usd_per_lb']), .07123456789)

    def test_csv_rejects_missing_extra_or_invalid_cells(self):
        for change in ('missing', 'extra', 'nan', 'text'):
            row = self.build()[0].copy()
            if change == 'missing':
                del row['quantity_lb']
            elif change == 'extra':
                row['extra'] = 1
            else:
                row['quantity_lb'] = float('nan') if change == 'nan' else '=1+1'
            with self.subTest(change=change):
                with self.assertRaises((TypeError, ValueError)):
                    scenarios_to_csv([row])

    def test_csv_empty_input_is_header_only(self):
        self.assertEqual(scenarios_to_csv([]).strip(), ','.join(FIELDS))

    def test_large_price_does_not_cancel_locked_cost(self):
        self.assertAlmostEqual(futures_hedged_cost(1000, 1e20, 1.22), 1220)
        self.assertAlmostEqual(call_hedged_cost(1000, 1e20, 1.25, .07), 1320)


if __name__ == '__main__':
    unittest.main()
