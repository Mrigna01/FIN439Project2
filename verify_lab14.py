"""Run the Lab 14 known-answer and correlation checks: python verify_lab14.py."""

from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

import mandate
import portfolio as p


class Lab14Checks(unittest.TestCase):
    def test_known_answers(self):
        covariance = p.covariance_matrix(p.SLEEVES, p.CORRELATIONS)
        cases = [
            (p.benchmark_weights(p.SLEEVES, p.BENCHMARK_ALLOCATIONS),
             ['0.0%', '0.0%', '40.0%', '60.0%'], '6.80%', '10.46%', '0.0%', True),
            (p.equal_weights(p.SLEEVES),
             ['25.0%'] * 4, '5.20%', '5.21%', '50.0%', False),
            (p.inverse_volatility_weights(p.SLEEVES),
             ['84.3%', '6.0%', '7.0%', '2.6%'], '3.77%', '1.05%', '90.3%', False),
        ]
        for weights, displayed, ret, vol, reserve, meets in cases:
            with self.subTest(weights=displayed):
                self.assertAlmostEqual(sum(weights), 1.0)
                self.assertEqual([f'{w:.1%}' for w in weights], displayed)
                result = p.expected_return(weights, p.SLEEVES)
                self.assertEqual(f'{result:.2%}', ret)
                self.assertEqual(f'{p.portfolio_volatility(weights, covariance):.2%}', vol)
                self.assertEqual(f'{p.reserve_weight(weights, p.SLEEVES):.1%}', reserve)
                self.assertEqual(p.meets_objective(result, p.OBJECTIVE_RETURN), meets)

    def test_correlation_change(self):
        changed = deepcopy(p.CORRELATIONS)
        changed[2][3] = changed[3][2] = 0.50
        output = StringIO()
        with patch.object(p, 'CORRELATIONS', changed), redirect_stdout(output):
            p.main()
        self.assertIn('Volatility: 11.00%', output.getvalue())
        self.assertEqual(p.CORRELATIONS[2][3], 0.25)
        self.assertEqual(p.CORRELATIONS[3][2], 0.25)

    def test_out_of_range_correlations(self):
        for invalid in (1.3, -1.3):
            with self.subTest(correlation=invalid):
                changed = deepcopy(p.CORRELATIONS)
                changed[2][3] = changed[3][2] = invalid
                with patch.object(p, 'CORRELATIONS', changed):
                    with self.assertRaisesRegex(ValueError, 'between -1 and 1'):
                        p.main()

    def test_asymmetric_correlations(self):
        changed = deepcopy(p.CORRELATIONS)
        changed[2][3] = 0.50  # Leave the other cell at 0.25.
        with patch.object(p, 'CORRELATIONS', changed):
            with self.assertRaisesRegex(ValueError, 'symmetric'):
                p.main()

    def test_candidate_e(self):
        checks = mandate.check_candidate(mandate.CANDIDATES['E'])
        failures = [(label, value) for label, value, passed in checks if not passed]
        self.assertEqual(failures, [('Reserve >= 3.0%', 0)])


if __name__ == '__main__':
    unittest.main(verbosity=2)
