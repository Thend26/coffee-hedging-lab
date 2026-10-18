import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from pricing import black76_call_values

APP = Path(__file__).resolve().parents[1] / 'app.py'


class LabAppTests(unittest.TestCase):
    def lab(self):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        return app.selectbox(key='analysis_mode').select('Black–76 laboratory').run(timeout=20)

    def test_lab_defaults_and_mode_isolation(self):
        app = self.lab()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.get('plotly_chart')), 4)
        frame = app.dataframe[0].value
        self.assertEqual(frame.shape, (101, 32))
        quote = black76_call_values(1.22, 1.25, .3, .5, .03)
        self.assertAlmostEqual(frame.iloc[0]['premium_usd_per_lb'], quote['premium_terminal_usd_per_lb'])
        self.assertEqual(len(app.get('download_button')), 1)
        app.selectbox(key='analysis_mode').select('V2 simplified').run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([m.value for m in app.metric], ['$1,200.00', '$1,220.00', '$1,270.00'])
        self.assertEqual(app.dataframe[0].value.shape, (101, 24))

    def test_interest_changes_today_premium_not_terminal_costs(self):
        app = self.lab()
        before = app.dataframe[0].value.copy()
        app.number_input(key='lab_rate').set_value(10.0).run()
        after = app.dataframe[0].value
        self.assertLess(after.iloc[0]['model_premium_today_usd_per_lb'], before.iloc[0]['model_premium_today_usd_per_lb'])
        for field in ('call_hedged_cost_usd', 'model_premium_terminal_usd_per_lb'):
            self.assertEqual(before[field].tolist(), after[field].tolist())

    def test_volatility_and_maturity_update_model(self):
        app = self.lab()
        before = app.dataframe[0].value.iloc[0]['premium_usd_per_lb']
        app.number_input(key='lab_volatility').set_value(60.0).run()
        self.assertGreater(app.dataframe[0].value.iloc[0]['premium_usd_per_lb'], before)
        app.number_input(key='lab_expiry').set_value(1.0).run()
        expected = black76_call_values(1.22, 1.25, .6, 1, .03)
        self.assertAlmostEqual(app.dataframe[0].value.iloc[0]['premium_usd_per_lb'], expected['premium_terminal_usd_per_lb'])

    def test_zero_boundaries_negative_rate_and_zero_hedge(self):
        app = self.lab()
        for key, value in (('lab_volatility', 0.0), ('lab_expiry', 0.0), ('lab_rate', -5.0)):
            app.number_input(key=key).set_value(value).run()
            self.assertEqual(len(app.exception), 0)
        app.slider(key='lab_hedge_ratio').set_value(0.0).run()
        frame = app.dataframe[0].value
        self.assertEqual(frame['call_hedged_cost_usd'].tolist(), frame['unhedged_cost_usd'].tolist())
        self.assertTrue((frame['total_premium_today_usd'] == 0).all())

    def test_invalid_range_or_contract_removes_stale_results(self):
        for key, value in (('lab_price_min', 2.0), ('lab_futures', 0.0), ('lab_strike', 0.0)):
            app = self.lab()
            app.number_input(key=key).set_value(value).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.error), 1)
            for kind in ('metric', 'dataframe', 'plotly_chart', 'download_button'):
                self.assertEqual(len(app.get(kind)), 0)


if __name__ == '__main__':
    unittest.main()
