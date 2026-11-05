"""Lab 19 known answers, threshold probe, shared-fact invariants, and app interactions."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import legend_panel as p
from select_lab19_company import select


def company_snapshot(ticker='COST'):
    return json.loads((p.DATA / f'{ticker}_facts.json').read_text())['companyfacts']


class KnownAnswers(unittest.TestCase):
    def test_current_course_revision(self):
        revision = json.loads((p.DATA / 'source_revision.json').read_text())
        self.assertEqual(revision['investors'], list(p.INVESTORS))
        self.assertIn('Cathie Wood', revision['commit_message'])

    def test_cost_all_new_numbers_and_checks(self):
        report = p.load_report('COST', offline=True)
        self.assertEqual([f"{r['liabilities_equity']:.2f}" for r in report['rows']],
                         ['2.11', '1.75', '1.96', '1.64', '1.49'])
        self.assertEqual(f"{report['revenue_cagr']:.2%}", '7.51%')
        self.assertTrue(all(r['research_development'] is None and r['rd_ratio'] is None
                            for r in report['rows']))
        self.assertEqual([c['status'] for c in report['checks']],
                         ['pass', 'pass', 'pass', 'fail', 'not known', 'pass', 'pass'])

    def test_lab18_values_preserved(self):
        old = p.b.load_report('COST', offline=True)
        new = p.load_report('COST', offline=True)
        for a, b in zip(old['rows'], new['rows']):
            for key in ('fiscal_end', *p.b.LABELS):
                self.assertEqual(a[key], b[key])

    def test_nvda_split_and_cash_failures(self):
        report = p.load_report('NVDA', offline=True)
        self.assertEqual([c['status'] for c in report['checks']],
                         ['pass', 'pass', 'pass', 'pass', 'pass', 'fail', 'pass'])
        self.assertEqual(f"{report['revenue_cagr']:.2%}", '68.30%')
        self.assertEqual(p.display_value(report['rows'][-1], 'rd_ratio'), '8.57%')
        self.assertEqual(p.display_value(report['rows'][-1], 'liabilities_equity'), '0.31')
        failures = [r['fiscal_end'] for r in report['rows'] if r['operating_cash_flow'] < r['net_income']]
        self.assertEqual(failures, ['2022-01-30', '2024-01-28', '2025-01-26', '2026-01-25'])

    def test_actual_skill_threshold_probe_restores_rule(self):
        retained = p.load_report('COST', offline=True)
        with patch.object(p.wood, 'GROWTH_MINIMUM', .05):
            probe = p.load_report('COST', offline=True)
        self.assertEqual([c['status'] for c in probe['checks'][3:5]], ['pass', 'not known'])
        self.assertEqual(probe['facts_sha256'], retained['facts_sha256'])
        self.assertNotEqual(probe['analysis_sha256'], retained['analysis_sha256'])
        self.assertEqual(p.wood.GROWTH_MINIMUM, .15)
        self.assertEqual(p.load_report('COST', offline=True)['checks'][3]['status'], 'fail')

    def test_six_memos_bound_to_exact_analysis(self):
        for ticker in ('COST', 'NVDA'):
            report = p.load_report(ticker, offline=True)
            for investor in p.INVESTORS:
                with self.subTest(ticker=ticker, investor=investor):
                    path = p.memo_path(ticker, investor)
                    memo = path.read_text()
                    self.assertRegex(memo, r'\*\*Verdict: (own the business|watch it|pass)\.\*\*')
                    self.assertEqual(p.unprinted_numbers(memo, report), [])
                    binding = json.loads(path.with_suffix('.json').read_text())
                    self.assertEqual(binding['facts_sha256'], report['facts_sha256'])
                    self.assertEqual(binding['analysis_sha256'], report['analysis_sha256'])
                    self.assertEqual(binding['memo_sha256'], hashlib.sha256(memo.encode()).hexdigest())

    def test_all_memos_reject_unsupported_percentage(self):
        report = p.load_report('COST', offline=True)
        for investor in p.INVESTORS:
            memo = p.memo_path('COST', investor).read_text() + '\nROE is 40.0%.'
            self.assertEqual(p.unprinted_numbers(memo, report), ['40.0%'])

    def test_vanguard_fund_selection(self):
        choice = json.loads((p.DATA / 'fund_selection.json').read_text())
        self.assertEqual(choice['selected_ticker'], 'NVDA')
        self.assertEqual(choice['holdings_as_of'], '09/30/2026')
        self.assertEqual(choice['top_equity_holdings'][0]['marketValuePercentage'], '4.52%')
        self.assertGreater(choice['equity_records_compared'], 1000)
        # Deliberately unordered weights: select numerically, not lexically or by first row.
        raw = json.dumps({'holdingDetails': {'asOfDate': 'test date', 'equityHoldings': [
            {'ticker': 'SMALL', 'marketValuePercentage': '9.00%', 'marketValueBaseCurrency': '$900'},
            {'ticker': 'LARGE', 'marketValuePercentage': '12.00%', 'marketValueBaseCurrency': '$1,200'},
            {'ticker': 'TINY', 'marketValueBaseCurrency': '$1'}]}}).encode()
        self.assertEqual(select(raw)['selected_ticker'], 'LARGE')

    def test_skills_have_frontmatter_and_executable_scripts(self):
        for folder, script in [('wood-business', 'wood.py'), ('burry-business', 'burry.py')]:
            path = p.ROOT / '.agents/skills' / folder
            text = (path / 'SKILL.md').read_text()
            self.assertRegex(text, r'\A---\nname: '+folder+r'\ndescription: [^\n]+\n---\n')
            self.assertTrue((path / 'scripts' / script).exists())
            self.assertNotIn('[TODO:', text)


class MissingInputsAndThresholds(unittest.TestCase):
    def test_nonpositive_equity_is_unknown_for_burry(self):
        for value in (0, -1):
            company = company_snapshot()
            for f in company['facts']['us-gaap']['StockholdersEquity']['units']['USD']:
                if f['end'] == '2026-08-30':
                    f['val'] = value
            report = p.analyze(company, 'COST')
            self.assertIsNone(report['rows'][-1]['liabilities_equity'])
            self.assertEqual(report['checks'][-1]['status'], 'not known')

    def test_missing_liabilities_stays_unknown(self):
        company = company_snapshot()
        del company['facts']['us-gaap']['Liabilities']
        report = p.analyze(company, 'COST')
        self.assertEqual(report['checks'][-1]['status'], 'not known')

    def test_bad_revenue_denominator_preserves_unknown(self):
        for value in (0, -1):
            company = company_snapshot('NVDA')
            for tag in p.TAGS['revenue']:
                for f in company['facts']['us-gaap'].get(tag, {}).get('units', {}).get('USD', []):
                    if f['end'] in ('2022-01-30', '2026-01-25'):
                        f['val'] = value
            report = p.analyze(company, 'NVDA')
            self.assertIsNone(report['revenue_cagr'])
            self.assertIsNone(report['rows'][-1]['rd_ratio'])
            self.assertEqual([c['status'] for c in report['checks'][3:5]], ['not known', 'not known'])

    def test_cash_input_missing_is_not_known(self):
        company = company_snapshot('NVDA')
        del company['facts']['us-gaap']['NetCashProvidedByUsedInOperatingActivities']
        report = p.analyze(company, 'NVDA')
        self.assertEqual(report['checks'][-2]['status'], 'not known')
        self.assertTrue(all(r['owner_earnings'] is None for r in report['rows']))

    def test_burry_checks_threshold_boundary_and_five_year_requirement(self):
        rows = [{'operating_cash_flow': 50, 'net_income': 50, 'liabilities_equity': 2.0}] * 5
        self.assertEqual([c['status'] for c in p.burry.evaluate(rows)], ['pass', 'pass'])
        self.assertEqual(p.burry.evaluate(rows[:4])[0]['status'], 'not known')
        changed = deepcopy(rows)
        changed[-1] = {**changed[-1], 'liabilities_equity': 2.00001}
        self.assertEqual(p.burry.evaluate(changed)[-1]['status'], 'fail')

    def test_wood_boundaries(self):
        rows = [{'rd_ratio': .05}]
        self.assertEqual([c['status'] for c in p.wood.evaluate(rows, .15)], ['pass', 'pass'])
        self.assertEqual(p.wood.evaluate(rows, .149999)[0]['status'], 'fail')
        self.assertEqual([c['status'] for c in p.wood.evaluate([{'rd_ratio': None}], None)],
                         ['not known', 'not known'])


class AppChecks(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(p.ROOT / 'legend_panel_app.py'), default_timeout=25).run()

    def test_costco_chart_panel_and_three_memos(self):
        app = self.app()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get('vega_lite_chart')), 1)
        self.assertEqual(len(app.text_area), 3)
        self.assertEqual(app.table[1].value['Result'].tolist(),
                         ['pass', 'pass', 'pass', 'fail', 'not known', 'pass', 'pass'])
        self.assertEqual(app.metric[0].value, '7.51%')
        self.assertEqual(len(app.success), 3)
        self.assertFalse(app.error)

    def test_flag_each_investor_memo_and_restore(self):
        app = self.app()
        for i in range(3):
            original = app.text_area[i].value
            app.text_area[i].set_value(original + '\nInvented ROE 40.0%.').run()
            self.assertFalse(app.exception)
            self.assertTrue(any('40.0%' in error.value and 'Panel number flag:' in error.value
                                for error in app.error))
            app.text_area[i].set_value(original).run()
            self.assertFalse(app.error)

    def test_probe_changes_one_check_keeps_gap_and_warns_memos(self):
        app = self.app()
        app.radio(key='growth_threshold').set_value('5% — lab probe').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.table[1].value['Result'].tolist(),
                         ['pass', 'pass', 'pass', 'pass', 'not known', 'pass', 'pass'])
        self.assertEqual(len(app.warning), 3)
        app.radio(key='growth_threshold').set_value('15% — retained rule').run()
        self.assertEqual(app.table[1].value['Result'].tolist()[3], 'fail')
        self.assertFalse(app.warning)

    def test_nvda_run_and_memo_switch(self):
        app = self.app()
        app.text_input(key='ticker').set_value('NVDA').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, '68.30%')
        self.assertEqual(app.table[1].value['Result'].tolist(),
                         ['pass', 'pass', 'pass', 'pass', 'pass', 'fail', 'pass'])
        self.assertEqual(len(app.text_area), 3)
        self.assertTrue(all('NVDA' in area.value for area in app.text_area))
        self.assertFalse(app.error)

    def test_lab18_app_panel_extension(self):
        app = AppTest.from_file(str(p.ROOT / 'buffett_app.py'), default_timeout=25).run()
        app.checkbox(key='show_panel').set_value(True).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.text_area), 3)
        self.assertEqual(app.table[1].value['Investor'].tolist(),
                         ['Buffett', 'Buffett', 'Buffett', 'Cathie Wood', 'Cathie Wood', 'Burry', 'Burry'])

    def test_invalid_ticker_no_crash(self):
        app = self.app()
        app.text_input(key='ticker').set_value('../COST').run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    retained = p.load_report('COST', offline=True)
    with patch.object(p.wood, 'GROWTH_MINIMUM', .05):
        probe = p.load_report('COST', offline=True)
    p.save_report(probe, '_growth_probe')
    evidence = {
        'tests_run': result.testsRun, 'passed': result.wasSuccessful(),
        'failures': len(result.failures), 'errors': len(result.errors),
        'cost_checks': retained['checks'],
        'nvda_checks': p.load_report('NVDA', offline=True)['checks'],
        'threshold_probe': {'method': 'Temporarily override GROWTH_MINIMUM in the Wood skill module; restore afterwards.',
                            'retained': retained['growth_minimum'], 'probe': probe['growth_minimum'],
                            'retained_wood_checks': retained['checks'][3:5],
                            'probe_wood_checks': probe['checks'][3:5],
                            'rule_restored': p.wood.GROWTH_MINIMUM == .15,
                            'same_facts': retained['facts_sha256'] == probe['facts_sha256']},
        'memo_number_probe': {investor: p.unprinted_numbers('ROE 40.0%.', retained)
                              for investor in p.INVESTORS},
        'activity_record': 'AI-assisted implementation and written analysis; no partner exchange or AI-off activity claimed.',
    }
    (p.DATA / 'verification.json').write_text(json.dumps(evidence, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
