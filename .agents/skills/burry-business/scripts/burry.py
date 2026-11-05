"""Michael Burry's Lab 19 cash-conversion and leverage rules."""

LIABILITIES_EQUITY_MAXIMUM = 2.0


def evaluate(rows):
    complete = len(rows) == 5 and all(
        r['operating_cash_flow'] is not None and r['net_income'] is not None for r in rows)
    cash = 'not known' if not complete else (
        'pass' if all(r['operating_cash_flow'] >= r['net_income'] for r in rows) else 'fail')
    ratio = rows[-1]['liabilities_equity']
    leverage = 'not known' if ratio is None else (
        'pass' if ratio <= LIABILITIES_EQUITY_MAXIMUM else 'fail')
    return [
        {'investor': 'Burry', 'check': 'Operating cash flow at least net income every year', 'status': cash},
        {'investor': 'Burry', 'check': f'Liabilities/equity no greater than {LIABILITIES_EQUITY_MAXIMUM:.2f}, latest year',
         'status': leverage},
    ]


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    from legend_panel import run_cli
    run_cli(investor='Burry')
