"""The lab must compare procurement cashflows on a terminal-value basis."""

import math
import csv
import io
import unittest

from lab_scenarios import build_lab_scenarios, lab_scenarios_to_csv, LAB_SCENARIO_FIELDS
from scenarios import SCENARIO_FIELDS
from analysis import break_even_vs_unhedged
from calculations import partial_call_hedged_cost, unhedged_cost


class LabScenarioTests(unittest.TestCase):
    def build(self, **overrides):
        args = dict(quantity=1000, current_spot=1.2, futures_price=1.5,
                    strike=1.25, volatility=0, time_to_expiry=1,
                    rate=math.log(2), price_min=1, price_max=1.5,
                    hedge_ratio=.5, budget_usd=1300)
        args.update(overrides)
        return build_lab_scenarios(**args)

    def test_deterministic_partial_hedge_and_cashflow_reconciliation(self):
        rows = self.build()
        self.assertEqual(len(rows), 101)
        last = rows[-1]
        self.assertAlmostEqual(last['model_premium_today_usd_per_lb'], .125)
        self.assertEqual(last['model_premium_terminal_usd_per_lb'], .25)
        self.assertAlmostEqual(last['total_premium_today_usd'], 62.5)
        self.assertEqual(last['total_premium_terminal_usd'], 125)
        for prefix in ('unhedged', 'futures_hedged', 'call_hedged'):
            self.assertEqual(last[f'{prefix}_cost_usd'], 1500)
        for row in rows:
            self.assertEqual(row['premium_usd_per_lb'], .25)
            self.assertEqual(row['option_premium_usd'], row['total_premium_terminal_usd'])
            self.assertEqual(tuple(row)[:24], SCENARIO_FIELDS)
            self.assertEqual(len(row), 32)

    def test_zero_hedge_keeps_quote_but_has_no_premium_cashflow(self):
        for row in self.build(hedge_ratio=0):
            self.assertEqual(row['model_premium_terminal_usd_per_lb'], .25)
            self.assertEqual(row['total_premium_today_usd'], 0)
            self.assertEqual(row['total_premium_terminal_usd'], 0)
            self.assertEqual(row['call_hedged_cost_usd'], row['unhedged_cost_usd'])

    def test_full_hedge_and_exact_budget_equality(self):
        rows = self.build(hedge_ratio=1, budget_usd=1500)
        self.assertEqual(rows[-1]['call_hedged_cost_usd'], 1500)
        self.assertEqual(rows[-1]['call_hedged_budget_gap_usd'], 0)
        self.assertEqual(rows[-1]['call_hedged_overspend_usd'], 0)
        self.assertTrue(all(row['futures_hedged_cost_usd'] == 1500 for row in rows))

    def test_rate_changes_today_metadata_not_terminal_cashflows(self):
        low = self.build(volatility=.3, rate=-.05)
        high = self.build(volatility=.3, rate=.1)
        changing = {'risk_free_rate_annual', 'model_premium_today_usd_per_lb',
                    'total_premium_today_usd', 'discount_factor'}
        for a, b in zip(low, high):
            self.assertGreater(a['model_premium_today_usd_per_lb'], b['model_premium_today_usd_per_lb'])
            for key in a.keys() - changing:
                self.assertEqual(a[key], b[key], key)

    def test_invalid_pricing_inputs_still_rejected_at_zero_hedge(self):
        with self.assertRaises(ValueError):
            self.build(volatility=-1, hedge_ratio=0)
        with self.assertRaises(TypeError):
            self.build(rate=True, hedge_ratio=0)

    def test_terminal_premium_break_even_not_today_premium(self):
        result = break_even_vs_unhedged(1.22, 1.25, .063, .5)['call']
        self.assertAlmostEqual(result['lower_usd_per_lb'], 1.313)
        self.assertAlmostEqual(partial_call_hedged_cost(1000, 1.313, 1.25, .063, .5), unhedged_cost(1000, 1.313))
        row = self.build(volatility=.3)[0]
        point = break_even_vs_unhedged(1.5, 1.25, row['model_premium_terminal_usd_per_lb'], .5)['call']['lower_usd_per_lb']
        self.assertAlmostEqual(partial_call_hedged_cost(1000, point, 1.25, row['model_premium_terminal_usd_per_lb'], .5), 1000*point)
        self.assertNotAlmostEqual(point, 1.25+row['model_premium_today_usd_per_lb'])

    def test_csv_round_trip_all_3232_cells(self):
        rows = self.build(volatility=.3)
        text = lab_scenarios_to_csv(rows)
        reader = csv.DictReader(io.StringIO(text))
        self.assertEqual(tuple(reader.fieldnames), LAB_SCENARIO_FIELDS)
        self.assertEqual(LAB_SCENARIO_FIELDS[:24], SCENARIO_FIELDS)
        decoded = list(reader)
        self.assertEqual(len(decoded), 101)
        for original, restored in zip(rows, decoded):
            for key in LAB_SCENARIO_FIELDS:
                self.assertEqual(float(restored[key]), original[key])

    def test_csv_empty_is_header_only(self):
        self.assertEqual(lab_scenarios_to_csv([]).splitlines(), [','.join(LAB_SCENARIO_FIELDS)])

    def test_csv_rejects_wrong_schema(self):
        row = self.build()[0]
        missing = dict(row)
        del missing['discount_factor']
        for bad in (missing, dict(row, extra=1)):
            with self.assertRaises(ValueError):
                lab_scenarios_to_csv([bad])

    def test_csv_rejects_bad_cells(self):
        for bad, error in (('1', TypeError), (True, TypeError),
                           (float('nan'), ValueError), (float('inf'), ValueError),
                           (10**400, ValueError)):
            row = self.build()[0]
            row['discount_factor'] = bad
            with self.subTest(error=error), self.assertRaises(error):
                lab_scenarios_to_csv([row])


if __name__ == '__main__':
    unittest.main()
