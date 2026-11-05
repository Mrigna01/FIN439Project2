"""Run Lab 18's source-based known answers, edge cases, and real Streamlit interactions."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent
SKILL = ROOT / '.agents/skills/buffett-business'
spec = importlib.util.spec_from_file_location('buffett', SKILL / 'scripts/buffett.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def synthetic_company():
    """Small independently understandable fixture; not used by the application."""
    facts = {}
    values = {'NetIncomeLoss': 30, 'StockholdersEquity': 100,
              'NetCashProvidedByUsedInOperatingActivities': 50,
              'PaymentsToAcquirePropertyPlantAndEquipment': 10,
              'RevenueFromContractWithCustomerExcludingAssessedTax': 200}
    for tag, value in values.items():
        entries = []
        for year in range(2021, 2026):
            f = {'end': f'{year}-12-31', 'val': value + (year - 2021 if tag != 'StockholdersEquity' else 0),
                 'form': '10-K', 'fp': 'FY', 'filed': f'{year+1}-02-01',
                 'fy': year, 'accn': f'test-{year}'}
            if tag != 'StockholdersEquity':
                f['start'] = f'{year}-01-01'
            entries.append(f)
        facts[tag] = {'units': {'USD': entries}}
    return {'entityName': 'Synthetic test, not SEC data', 'cik': 0, 'facts': {'us-gaap': facts}}


class KnownAnswerChecks(unittest.TestCase):
    def test_skill_metadata_and_bundled_script(self):
        # Validate this simple string-only frontmatter without installing PyYAML.
        text = (SKILL / 'SKILL.md').read_text()
        match = re.match(r'\A---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n', text)
        self.assertIsNotNone(match)
        self.assertEqual(match[1], SKILL.name)
        self.assertLessEqual(len(match[1]), 64)
        self.assertLessEqual(len(match[2]), 1024)
        self.assertNotIn('[TODO:', text)
        self.assertTrue((SKILL / 'scripts/buffett.py').is_file())

    def test_costco_all_known_values(self):
        # Transcribed from the professor's Lab 18 table ONLY as test expectations.
        expected = [
            ('2022-08-28', 226954, 5844, 7392, 3891, 20642, '28.3%', 3501),
            ('2023-09-03', 242290, 6292, 11068, 4323, 25058, '25.1%', 6745),
            ('2024-09-01', 254453, 7367, 11339, 4710, 23622, '31.2%', 6629),
            ('2025-08-31', 275235, 8099, 13335, 5498, 29164, '27.8%', 7837),
            ('2026-08-30', 303154, 9226, 15817, 6435, 35803, '25.8%', 9382),
        ]
        report = b.load_report('COST', offline=True)
        self.assertEqual(len(report['rows']), 5)
        for row, expected_row in zip(report['rows'], expected):
            actual = (row['fiscal_end'], *(row[k] / 1e6 for k in b.TAGS),
                      b.display_value(row, 'roe'), row['owner_earnings'] / 1e6)
            self.assertEqual(actual, expected_row)
        self.assertEqual([c['status'] for c in report['checks']], ['pass'] * 3)

    def test_jpm_gaps_and_fallback(self):
        report = b.load_report('JPM', offline=True)
        self.assertEqual([c['status'] for c in report['checks']], ['fail', 'not known', 'not known'])
        for r in report['rows']:
            self.assertIsNone(r['capital_spending'])
            self.assertIsNone(r['owner_earnings'])
            self.assertEqual(r['facts']['revenue']['tag'], 'us-gaap:Revenues')
        memo = (b.MEMOS / 'JPM_buffett.md').read_text()
        self.assertIn('cannot judge owner earnings', memo)

    def test_saved_memos_numbers_and_fingerprints(self):
        for ticker in ('COST', 'JPM'):
            with self.subTest(ticker=ticker):
                report = b.load_report(ticker, offline=True)
                memo_path = b.MEMOS / f'{ticker}_buffett.md'
                memo = memo_path.read_text()
                self.assertEqual(b.unprinted_numbers(memo, report), [])
                binding = json.loads(memo_path.with_suffix('.json').read_text())
                self.assertEqual(binding['facts_sha256'], report['facts_sha256'])
                self.assertEqual(binding['memo_sha256'], hashlib.sha256(memo.encode()).hexdigest())

    def test_hand_typed_number_probe(self):
        report = b.load_report('COST', offline=True)
        self.assertEqual(b.unprinted_numbers('ROE is 40.0%.', report), ['40.0%'])
        self.assertEqual(b.unprinted_numbers('ROE is 28.3%.', report), [])
        self.assertEqual(b.unprinted_numbers('FY2026 owner earnings $9,382 million.', report), [])
        self.assertEqual(b.unprinted_numbers('I forecast 9.99e15 dollars.', report), ['9.99e15'])
        self.assertEqual(b.unprinted_numbers('2026-08-31 was the year end.', report), ['2026-08-31'])

    def test_snapshot_provenance(self):
        for ticker in ('COST', 'JPM'):
            report = b.load_report(ticker, offline=True)
            self.assertTrue(report['provenance']['source_url'].startswith('https://data.sec.gov/'))
            self.assertRegex(report['provenance']['raw_response_sha256'], r'^[0-9a-f]{64}$')
            for row in report['rows']:
                for metric, fact in row['facts'].items():
                    if fact['value'] is None:
                        self.assertIsNone(fact['source'])
                        continue
                    self.assertEqual(fact['source']['form'], '10-K')
                    self.assertEqual(fact['source']['end'], row['fiscal_end'])
                    self.assertTrue(fact['source']['accn'])
                    if metric != 'equity':
                        self.assertTrue(b.annual_fact({**fact['source'], 'val': fact['value']}))


class SelectionAndGapChecks(unittest.TestCase):
    def test_hand_calculated_ratios_and_growth(self):
        report = b.analyze(synthetic_company(), 'TEST')
        self.assertEqual(report['rows'][0]['roe'], .30)
        self.assertEqual(report['rows'][0]['owner_earnings'], 40)
        self.assertEqual(report['rows'][-1]['owner_earnings'], 40)
        self.assertEqual([c['status'] for c in report['checks']], ['pass', 'pass', 'fail'])

    def test_quarters_and_other_forms_excluded_latest_filing_wins(self):
        company = synthetic_company()
        entries = company['facts']['us-gaap']['NetIncomeLoss']['units']['USD']
        entries += [
            {**entries[-1], 'start': '2025-10-01', 'val': 999, 'filed': '2028-01-01'},
            {**entries[-1], 'form': '10-Q', 'val': 888, 'filed': '2028-01-01'},
            {**entries[-1], 'val': 44, 'filed': '2027-01-01', 'accn': 'restatement'},
            {**entries[0], 'fy': 2025, 'val': 35, 'filed': '2027-01-01', 'accn': 'comparative'},
        ]
        rows = b.analyze(company, 'TEST')['rows']
        self.assertEqual(rows[-1]['net_income'], 44)
        self.assertEqual(rows[0]['net_income'], 35)
        self.assertEqual(rows[0]['fiscal_end'], '2021-12-31')

    def test_nonpositive_equity_and_missing_capex(self):
        for equity in (0, -10):
            company = synthetic_company()
            facts = company['facts']['us-gaap']
            facts['StockholdersEquity']['units']['USD'][0]['val'] = equity
            del facts['PaymentsToAcquirePropertyPlantAndEquipment']
            report = b.analyze(company, 'TEST')
            self.assertIsNone(report['rows'][0]['roe'])
            self.assertTrue(all(r['owner_earnings'] is None for r in report['rows']))
            self.assertEqual([c['status'] for c in report['checks']], ['not known'] * 3)

    def test_capex_tag_fallback(self):
        company = synthetic_company()
        facts = company['facts']['us-gaap']
        facts['PaymentsToAcquireProductiveAssets'] = facts.pop('PaymentsToAcquirePropertyPlantAndEquipment')
        row = b.analyze(company, 'TEST')['rows'][0]
        self.assertEqual(row['owner_earnings'], 40)
        self.assertEqual(row['facts']['capital_spending']['tag'], 'us-gaap:PaymentsToAcquireProductiveAssets')

    def test_latest_filing_conflicts_rejected(self):
        company = synthetic_company()
        entries = company['facts']['us-gaap']['NetIncomeLoss']['units']['USD']
        entries.append({**entries[-1], 'val': 777})
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            b.analyze(company, 'TEST')

    def test_insufficient_years_not_silent_pass(self):
        company = synthetic_company()
        for fact in company['facts']['us-gaap'].values():
            fact['units']['USD'] = fact['units']['USD'][-2:]
        report = b.analyze(company, 'TEST')
        self.assertEqual([c['status'] for c in report['checks']], ['not known'] * 3)
        self.assertTrue(report['warnings'])

    def test_nonfinite_facts_are_missing(self):
        company = synthetic_company()
        company['facts']['us-gaap']['StockholdersEquity']['units']['USD'][0]['val'] = float('nan')
        row = b.analyze(company, 'TEST')['rows'][0]
        self.assertIsNone(row['equity'])
        self.assertIsNone(row['roe'])

    def test_ticker_path_input_rejected(self):
        for bad in ('../COST', '', 'COST/../../', '<script>'):
            with self.assertRaises(ValueError):
                b.validate_ticker(bad)


class AppChecks(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(ROOT / 'buffett_app.py'), default_timeout=25).run()

    def test_costco_table_chart_and_memo(self):
        app = self.app()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get('vega_lite_chart')), 1)
        self.assertEqual(app.table[0].value['ROE'].tolist(), ['28.3%', '25.1%', '31.2%', '27.8%', '25.8%'])
        self.assertEqual(app.table[1].value['Result'].tolist(), ['pass'] * 3)
        self.assertTrue(app.success)
        self.assertFalse(app.error)

    def test_edit_probe_and_restore(self):
        app = self.app()
        original = app.text_area[0].value
        app.text_area[0].set_value(original + '\nAn unsupported ROE is 40.0%.').run()
        self.assertFalse(app.exception)
        self.assertIn('40.0%', app.error[0].value)
        app.text_area[0].set_value(original).run()
        self.assertFalse(app.error)
        self.assertTrue(app.success)

    def test_jpm_switch_preserves_gaps_and_memo(self):
        app = self.app()
        app.text_input(key='ticker').set_value('JPM').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.table[0].value['Owner earnings'].tolist(), ['not found'] * 5)
        self.assertEqual(app.table[1].value['Result'].tolist(), ['fail', 'not known', 'not known'])
        self.assertIn('cannot judge owner earnings', app.text_area[0].value)
        self.assertTrue(app.info)
        self.assertFalse(app.error)

    def test_invalid_ticker_shows_error_without_crashing(self):
        app = self.app()
        app.text_input(key='ticker').set_value('../COST').run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)

    def test_stale_facts_warn(self):
        path = b.MEMOS / 'COST_buffett.json'
        original = path.read_text()
        binding = json.loads(original)
        binding['facts_sha256'] = 'different facts'
        # Patch the read only, rather than changing saved student artifacts.
        read_text = Path.read_text
        def altered_read(p, *args, **kwargs):
            return json.dumps(binding) if p == path else read_text(p, *args, **kwargs)
        with patch.object(Path, 'read_text', altered_read):
            app = self.app()
        self.assertFalse(app.exception)
        self.assertTrue(any('different SEC facts' in w.value for w in app.warning))


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = b.load_report('COST', offline=True)
    evidence = {
        'tests_run': result.testsRun, 'passed': result.wasSuccessful(),
        'failures': len(result.failures), 'errors': len(result.errors),
        'cost_known_answer': 'All annual values and checks matched' if result.wasSuccessful() else 'Review failures',
        'unprinted_number_probe': b.unprinted_numbers('ROE is 40.0%.', report),
        'cost_facts_sha256': report['facts_sha256'],
        'jpm_facts_sha256': b.load_report('JPM', offline=True)['facts_sha256'],
        'partner_work': 'Not performed',
        'fresh_browser_ai_probe': 'Not performed; do not substitute a skill-aware response',
    }
    (b.DATA / 'verification.json').write_text(json.dumps(evidence, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
