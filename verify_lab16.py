"""Check Lab 16 and save actual output. Run: python verify_lab16.py."""

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import random
import unittest

import asof

ROOT = Path(__file__).resolve().parent


class ProvenanceChecks(unittest.TestCase):
    def test_known_funnel_and_complete_accounting(self):
        result = asof.provenance_gate(asof.ROWS)
        self.assertEqual([step['rows'] for step in result['funnel']], [[11], [7], [3, 8, 10], [2]])
        self.assertEqual([step['remaining'] for step in result['funnel']], [11, 10, 7, 6])
        self.assertEqual([row['row'] for row in result['panel']], [1, 4, 5, 6, 9, 12])
        accounted = [number for step in result['funnel'] for number in step['rows']]
        accounted += [row['row'] for row in result['panel']]
        self.assertEqual(sorted(accounted), list(range(1, 13)))

    def test_known_signals(self):
        result = asof.analyze()
        for ticker, actual, naive, month in [('AAA', '+1.98%', '+5.83%', '2026-03'),
                                            ('BBB', '-1.02%', '-5.15%', '2026-03'),
                                            ('CCC', '+0.91%', '+1.82%', '2026-02')]:
            self.assertEqual(f"{result['asof_signals'][ticker]['return']:+.2%}", actual)
            self.assertEqual(result['asof_signals'][ticker]['month'], '2026-02')
            self.assertEqual(f"{result['naive_signals'][ticker]['return']:+.2%}", naive)
            self.assertEqual(result['naive_signals'][ticker]['month'], month)

    def test_later_date_matches_naive_without_mutating_inputs(self):
        before = deepcopy(asof.ROWS)
        result = asof.analyze(decision_date='2026-04-15')
        self.assertEqual(result['asof_signals'], result['naive_signals'])
        self.assertEqual(result['asof']['panel'], result['naive']['panel'])
        self.assertEqual(asof.ROWS, before)
        self.assertEqual(asof.DECISION_DATE, '2026-03-31')

    def test_publication_boundary_inclusive_and_revision_timing(self):
        before = asof.analyze(decision_date='2026-03-24')
        on = asof.analyze(decision_date='2026-03-25')
        self.assertEqual(before['asof_signals']['AAA']['latest_row'], 2)
        self.assertEqual(on['asof_signals']['AAA']['latest_row'], 4)
        self.assertEqual(f"{before['asof_signals']['AAA']['return']:+.2%}", '+2.97%')
        april4 = asof.analyze(decision_date='2026-04-04')
        april5 = asof.analyze(decision_date='2026-04-05')
        self.assertEqual(april4['asof_signals']['CCC']['latest_row'], 12)
        self.assertEqual(april5['asof_signals']['CCC']['latest_row'], 10)

    def test_order_independent(self):
        rows = deepcopy(asof.ROWS)
        random.Random(16).shuffle(rows)
        self.assertEqual(asof.analyze(rows), asof.analyze())

    def test_rules_applied_in_order(self):
        rows = deepcopy(asof.ROWS)
        rows.extend([{**rows[10], 'row': 13}, {**rows[2], 'row': 14}])
        funnel = asof.provenance_gate(rows)['funnel']
        self.assertEqual(funnel[0]['rows'], [11, 13])
        self.assertEqual(funnel[1]['rows'], [7, 14])
        self.assertEqual(funnel[2]['rows'], [3, 8, 10])

    def test_sanity_is_separate(self):
        result = asof.analyze()
        checks = result['sanity']
        self.assertEqual([row['row'] for row in checks if row['flags']], [1, 4, 9, 12])
        self.assertEqual([f"{row['yield']:+.2%}" for row in checks],
                         ['-0.99%', '-2.91%', '+2.04%', '+3.09%', '-9.09%', '-9.91%'])
        self.assertEqual(len(result['asof']['panel']), 6)

    def test_same_date_conflict_rejected(self):
        rows = deepcopy(asof.ROWS)
        rows.append({**rows[3], 'row': 13, 'price': 102.0})
        with self.assertRaisesRegex(ValueError, 'Conflicting values'):
            asof.provenance_gate(rows)

    def test_insufficient_history_and_zero_denominator(self):
        early = asof.analyze(decision_date='2026-02-10')
        self.assertTrue(all(s['return'] is None for s in early['asof_signals'].values()))
        self.assertEqual(asof.analyze(decision_date='2026-01-01')['asof_signals'], {})
        rows = [dict(asof.ROWS[0]), dict(asof.ROWS[2])]
        self.assertIsNone(asof.signals(rows)['AAA']['return'])
        rows = [dict(asof.ROWS[0]), dict(asof.ROWS[3])]
        rows[0]['price'] = 0
        self.assertIsNone(asof.signals(rows)['AAA']['return'])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProvenanceChecks)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    if not outcome.wasSuccessful():
        raise SystemExit(1)
    output = StringIO()
    with redirect_stdout(output):
        baseline = asof.main()
        print('\n--- Later-date verification (local test, not a partner exchange) ---\n')
        later = asof.main('2026-04-15')
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data/lab16_output.txt').write_text(output.getvalue(), encoding='utf-8')
    report = {'assignment_commit': '5e6970110e86ea5487b1e0ec8eb9add94e44f8c6',
              'baseline': baseline, 'later_date': later,
              'verification': {'tests_run': outcome.testsRun, 'passed': True}}
    (ROOT / 'data/lab16_results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Saved data/lab16_output.txt and data/lab16_results.json')
