"""Run engine and Streamlit checks, then save reproducible Lab 15 results.

Run: python verify_lab15.py
"""

from contextlib import redirect_stdout
from copy import deepcopy
from io import BytesIO, StringIO
import json
from math import comb, sqrt
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
import portfolio as p

ROOT = Path(__file__).resolve().parent


def scenarios():
    full = p.estimate_from_csv(ROOT / 'prices.csv')
    recent = p.estimate_from_csv(ROOT / 'prices.csv', last_36=True)
    equity = deepcopy(p.SLEEVES)
    equity[3]['return'] = 0.07
    corr = deepcopy(p.CORRELATIONS)
    corr[2][3] = corr[3][2] = 0.50
    stress = deepcopy(full['sleeves'])
    stress[3]['return'] -= 0.01
    extra = deepcopy(full['sleeves'])
    extra[3]['return'] -= 0.011
    results = {
        'meridian': p.search_portfolio(p.SLEEVES, p.CORRELATIONS, .065, .03),
        'meridian_equity_minus_one_point': p.search_portfolio(equity, p.CORRELATIONS, .065, .03),
        'meridian_correlation_050': p.search_portfolio(p.SLEEVES, corr, .065, .03),
        'campus_all_months': p.search_portfolio(full['sleeves'], full['correlations'], .055, .04),
        'campus_last_36': p.search_portfolio(recent['sleeves'], recent['correlations'], .055, .04),
        'campus_vt_minus_one_point': p.search_portfolio(stress, full['correlations'], .055, .04),
        'campus_vt_minus_1_1_points': p.search_portfolio(extra, full['correlations'], .055, .04),
    }
    return {'full_estimates': full, 'recent_estimates': recent, 'results': results,
            'meridian_change_points': p.largest_weight_change(results['meridian'], results['meridian_equity_minus_one_point']),
            'campus_window_change_points': p.largest_weight_change(results['campus_all_months'], results['campus_last_36']),
            'campus_stress_change_points': p.largest_weight_change(results['campus_all_months'], results['campus_vt_minus_one_point']),
            'campus_extra_stress_change_points': p.largest_weight_change(results['campus_all_months'], results['campus_vt_minus_1_1_points'])}


class EngineChecks(unittest.TestCase):
    def test_grid_complete_unique_and_fully_invested(self):
        for count in (3, 4, 6):
            grid = list(p.weight_grid(count))
            self.assertEqual(len(grid), comb(20 + count - 1, count - 1))
            self.assertEqual(len({tuple(w) for w in grid}), len(grid))
            for weights in grid:
                self.assertAlmostEqual(sum(weights), 1)
                self.assertTrue(all(w >= 0 and abs(w * 20 - round(w * 20)) < 1e-10 for w in weights))

    def test_meridian_known_answers(self):
        results = scenarios()['results']
        for name, weights, ret, vol in [
            ('meridian', [0, .2, .25, .55], '6.51%', '9.44%'),
            ('meridian_equity_minus_one_point', [0, .1, .1, .8], '6.53%', '12.94%'),
            ('meridian_correlation_050', [0, .4, 0, .6], '6.52%', '9.73%'),
        ]:
            with self.subTest(name=name):
                result = results[name]
                self.assertEqual(result['weights'], weights)
                self.assertEqual(f"{result['return']:.2%}", ret)
                self.assertEqual(f"{result['volatility']:.2%}", vol)

    def test_infeasible_and_boundary(self):
        self.assertIsNone(p.search_portfolio(p.SLEEVES, p.CORRELATIONS, .20, .03))
        sleeves = deepcopy(p.SLEEVES)
        for s in sleeves:
            s['reserve_eligible'] = False
        self.assertIsNone(p.search_portfolio(sleeves, p.CORRELATIONS, .065, .03))
        self.assertIsNotNone(p.search_portfolio(sleeves, p.CORRELATIONS, .065, 0))
        result = p.search_portfolio(p.SLEEVES, p.CORRELATIONS, .035, 1)
        self.assertEqual(result['weights'], [1, 0, 0, 0])
        self.assertIsNone(p.largest_weight_change(result, None))

    def test_estimator_against_small_hand_calculation(self):
        # Monthly returns A=[.10,-.10], B=[.20,-.20], C=[-.10,.10].
        source = b'Date,A,B,C\n2024-01-31,100,100,100\n2024-02-29,110,120,90\n2024-03-28,99,96,99\n'
        estimate = p.estimate_from_csv(source)
        self.assertAlmostEqual(estimate['sleeves'][0]['return'], 0)
        self.assertAlmostEqual(estimate['sleeves'][0]['volatility'], sqrt(.02) * sqrt(12))
        self.assertAlmostEqual(estimate['correlations'][0][1], 1)
        self.assertAlmostEqual(estimate['correlations'][0][2], -1)

    def test_real_data_windows(self):
        full = p.estimate_from_csv(ROOT / 'prices.csv')
        recent = p.estimate_from_csv(ROOT / 'prices.csv', True)
        self.assertEqual(full['observations'], 60)
        self.assertEqual(recent['observations'], 36)
        self.assertEqual(recent['price_start'], '2023-09-29')
        self.assertEqual(recent['return_start'], '2023-10-31')
        # A separately selected 37-price CSV must give identical recent estimates.
        lines = (ROOT / 'prices.csv').read_text().splitlines()
        subset = ('\n'.join([lines[0], *lines[-37:]]) + '\n').encode()
        self.assertEqual(p.estimate_from_csv(subset), recent)

    def test_bad_csv_rejected(self):
        source = 'Date,A,B,C\n2024-01-31,100,100,100\n2024-02-29,110,120,90\n2024-03-28,99,96,99\n'
        for bad in [source.replace('A,B,C', 'A,A,C'), source.replace('2024-02-29', '2024-01-31'),
                    source.replace('2024-02-29', '2024-04-30'), source.replace('110', 'nan'),
                    source.replace('110', '0'), source.replace('110', ''), source.replace('110', '-1')]:
            with self.subTest(csv=bad), self.assertRaises(ValueError):
                p.estimate_from_csv(bad.encode())
        with self.assertRaisesRegex(ValueError, '37 monthly prices'):
            p.estimate_from_csv(source.encode(), True)
        constant = source.replace('110,120,90', '100,100,100').replace('99,96,99', '100,100,100')
        with self.assertRaisesRegex(ValueError, 'zero or invalid'):
            p.estimate_from_csv(constant.encode())


class AppChecks(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20).run()

    def test_meridian_edit_and_reset(self):
        app = self.app()
        self.assertFalse(app.exception)
        self.assertEqual(app.table[0].value['Weight'].tolist(), ['0.00%', '20.00%', '25.00%', '55.00%'])
        box = next(x for x in app.number_input if x.label.startswith('Global equity'))
        box.set_value(7.0).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.table[1].value['Weight'].tolist(), ['0.00%', '10.00%', '10.00%', '80.00%'])
        self.assertEqual(app.metric[-1].value, '25.00 points')
        app.button(key='reset_returns').click().run()
        self.assertEqual(app.metric[-1].value, '0.00 points')

    def test_campus_switch_stress_and_infeasible(self):
        app = self.app()
        app.radio(key='universe').set_value('Campus Scholarship Reserve').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.table[0].value['Weight'].tolist(), ['75.00%', '0.00%', '0.00%', '25.00%'])
        app.toggle(key='last36').set_value(True).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.table[1].value['Weight'].tolist(), ['90.00%', '0.00%', '0.00%', '10.00%'])
        self.assertEqual(app.metric[-1].value, '15.00 points')
        app.toggle(key='last36').set_value(False).run()
        box = next(x for x in app.number_input if x.label.startswith('VT return'))
        box.set_value(box.value - 1).run()
        self.assertEqual(app.metric[-1].value, '0.00 points')
        self.assertEqual(app.metric[3].value, '5.51%')
        next(x for x in app.number_input if x.label == 'Objective return (%)').set_value(50.0).run()
        self.assertEqual(len(app.warning), 2)
        self.assertTrue(all(w.value == 'no mix meets the objective' for w in app.warning))
        self.assertFalse(app.exception)

    def test_reserve_checkboxes(self):
        app = self.app()
        for checkbox in app.checkbox:
            checkbox.set_value(False)
        app.run()
        self.assertEqual(len(app.warning), 2)
        next(x for x in app.number_input if x.label == 'Reserve minimum (%)').set_value(0.0).run()
        self.assertEqual(len(app.warning), 0)

    def test_uploaded_file_and_bad_upload(self):
        # AppTest has no file-uploader interaction API; supply its file-like return.
        with patch('streamlit.file_uploader', return_value=BytesIO((ROOT / 'prices.csv').read_bytes())):
            app = self.app()
            self.assertFalse(app.exception)
            self.assertEqual(app.table[0].value['Asset'].tolist(), ['SGOV', 'SCHR', 'USIG', 'VT'])
        with patch('streamlit.file_uploader', return_value=BytesIO(b'bad,data\n')):
            app = self.app()
            self.assertTrue(app.error)
            self.assertFalse(app.exception)

    def test_saved_engine_change_reaches_app(self):
        path = ROOT / 'portfolio.py'
        original = path.read_bytes()
        try:
            text = original.decode('utf-8')
            changed = text.replace('[0.05, 0.80, 1.00, 0.25]', '[0.05, 0.80, 1.00, 0.50]')
            changed = changed.replace('[0.00, -0.10, 0.25, 1.00]', '[0.00, -0.10, 0.50, 1.00]')
            self.assertNotEqual(text, changed)
            path.write_text(changed + '\n# Temporary verification input.\n', encoding='utf-8')
            app = self.app()
            self.assertFalse(app.exception)
            self.assertEqual(app.table[0].value['Weight'].tolist(), ['0.00%', '40.00%', '0.00%', '60.00%'])
            self.assertEqual(app.metric[0].value, '6.52%')
            self.assertEqual(app.metric[1].value, '9.73%')
        finally:
            path.write_bytes(original)
        app = self.app()
        self.assertEqual(app.metric[1].value, '9.44%')


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    output = scenarios()
    output['verification'] = {'tests_run': result.testsRun, 'passed': True}
    target = ROOT / 'data' / 'lab15_results.json'
    target.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    print(f'Saved results to {target.name}')
