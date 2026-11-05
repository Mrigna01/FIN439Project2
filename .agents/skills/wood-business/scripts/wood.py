"""Cathie Wood's Lab 19 rules, computed on the shared annual SEC rows."""

GROWTH_MINIMUM = 0.15
RD_MINIMUM = 0.05


def evaluate(rows, revenue_cagr, growth_minimum=None):
    threshold = GROWTH_MINIMUM if growth_minimum is None else growth_minimum
    latest = rows[-1]
    growth = 'not known' if revenue_cagr is None else (
        'pass' if revenue_cagr >= threshold else 'fail')
    rd = latest['rd_ratio']
    innovation = 'not known' if rd is None else ('pass' if rd >= RD_MINIMUM else 'fail')
    return [
        {'investor': 'Cathie Wood', 'check': f'Revenue CAGR at least {threshold:.1%}, first year to last',
         'status': growth},
        {'investor': 'Cathie Wood', 'check': f'R&D at least {RD_MINIMUM:.1%} of revenue, latest year',
         'status': innovation},
    ]


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    from legend_panel import run_cli
    run_cli(investor='Cathie Wood')
