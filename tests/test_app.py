import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'


class AppTests(unittest.TestCase):
    def test_default_page(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([m.value for m in app.metric], ['$1,200.00', '$1,220.00', '$1,270.00'])
        self.assertEqual(len(app.dataframe[0].value), 101)
        self.assertEqual(len(app.get('plotly_chart')), 1)
        self.assertEqual(len(app.get('download_button')), 1)

    def test_quantity_change_updates_outputs(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        original = app.dataframe[0].value.copy()
        app.number_input(key='quantity').set_value(2000.0).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([m.value for m in app.metric], ['$2,400.00', '$2,440.00', '$2,540.00'])
        self.assertAlmostEqual(app.dataframe[0].value.iloc[-1]['call_hedged_cost_usd'], 2640)
        for field in ('unhedged_cost_usd', 'futures_hedged_cost_usd', 'call_hedged_cost_usd'):
            for before, after in zip(original[field], app.dataframe[0].value[field]):
                self.assertAlmostEqual(after, 2 * before)

    def test_reference_price_does_not_change_scenario_costs(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        original = app.dataframe[0].value.copy()
        app.number_input(key='spot').set_value(1.5).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([m.value for m in app.metric], ['$1,500.00', '$1,220.00', '$1,320.00'])
        updated = app.dataframe[0].value
        for field in original.columns:
            if field != 'current_spot_usd_per_lb':
                self.assertEqual(original[field].tolist(), updated[field].tolist())
        self.assertTrue((updated['current_spot_usd_per_lb'] == 1.5).all())

    def test_invalid_range_removes_stale_outputs(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        app.number_input(key='price_min').set_value(2.0).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 1)
        self.assertEqual(len(app.metric), 0)
        self.assertEqual(len(app.dataframe), 0)
        self.assertEqual(len(app.get('download_button')), 0)
        self.assertEqual(len(app.get('plotly_chart')), 0)

    def test_zero_premium(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        app.number_input(key='premium').set_value(0.0).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[2].value, '$1,200.00')

    def test_premium_increase_shifts_only_call_costs(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        original = app.dataframe[0].value.copy()
        app.number_input(key='premium').set_value(0.10).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([m.value for m in app.metric], ['$1,200.00', '$1,220.00', '$1,300.00'])
        updated = app.dataframe[0].value
        self.assertEqual(len(updated), 101)
        for field in ('unhedged_cost_usd', 'futures_hedged_cost_usd',
                      'terminal_price_usd_per_lb', 'call_payoff_usd'):
            self.assertEqual(original[field].tolist(), updated[field].tolist())
        for before, after in zip(original['call_hedged_cost_usd'], updated['call_hedged_cost_usd']):
            self.assertAlmostEqual(after - before, 30)

    def test_strike_change_has_piecewise_effect(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        original = app.dataframe[0].value.copy()
        app.number_input(key='strike').set_value(1.35).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[2].value, '$1,270.00')
        updated = app.dataframe[0].value
        for field in ('unhedged_cost_usd', 'futures_hedged_cost_usd'):
            self.assertEqual(original[field].tolist(), updated[field].tolist())
        for old, new in zip(original.to_dict('records'), updated.to_dict('records')):
            price = new['terminal_price_usd_per_lb']
            expected_change = 1000 * (min(price, 1.35) - min(price, 1.25))
            self.assertAlmostEqual(new['call_hedged_cost_usd'] - old['call_hedged_cost_usd'], expected_change)
        from calculations import call_hedged_cost
        self.assertAlmostEqual(call_hedged_cost(1000, 1.00, 1.35, .07), 1070)
        self.assertAlmostEqual(call_hedged_cost(1000, 1.80, 1.35, .07), 1420)


    def test_ratio_and_budget_controls_update_all_outputs(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        self.assertEqual(app.slider(key='hedge_ratio').value, 1.0)
        self.assertEqual(app.number_input(key='budget').value, 1300)
        app.slider(key='hedge_ratio').set_value(.5).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([m.value for m in app.metric], ['$1,200.00', '$1,210.00', '$1,235.00'])
        text = ' '.join(item.value for item in app.markdown)
        self.assertNotIn('Full hedge cost bounds:', text)
        summary = app.dataframe[1].value
        self.assertEqual(summary['Scenarios over budget'].tolist(), [42, 35, 44])
        app.number_input(key='budget').set_value(2000.0).run()
        self.assertTrue((app.dataframe[0].value['budget_usd'] == 2000).all())
        self.assertEqual(app.dataframe[1].value['Scenarios over budget'].tolist(), [0, 0, 0])
        import json
        spec = json.loads(app.get('plotly_chart')[0].proto.spec)
        self.assertEqual(spec['layout']['shapes'][0]['y0'], 2000)

    def test_zero_hedge_and_zero_premium_explanations(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        app.slider(key='hedge_ratio').set_value(0.0).run()
        self.assertEqual([m.value for m in app.metric], ['$1,200.00'] * 3)
        self.assertIn('All nonnegative terminal prices',
                      ' '.join(item.value for item in app.markdown))
        app.slider(key='hedge_ratio').set_value(.5).run()
        app.number_input(key='premium').set_value(0.0).run()
        text = ' '.join(item.value for item in app.markdown)
        self.assertIn('0 ≤ S ≤ 1.2500', text)


if __name__ == '__main__':
    unittest.main()
