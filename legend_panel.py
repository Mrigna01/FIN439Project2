"""Lab 19: shared SEC facts for Buffett, Cathie Wood, and Burry. Standard library only."""

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/lab19'
MEMOS = ROOT / 'docs/lab19'
INVESTORS = {'Buffett': 'buffett', 'Cathie Wood': 'wood', 'Burry': 'burry'}


def skill_module(name, script):
    path = ROOT / '.agents/skills' / name / 'scripts' / script
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


b = skill_module('buffett-business', 'buffett.py')
wood = skill_module('wood-business', 'wood.py')
burry = skill_module('burry-business', 'burry.py')
TAGS = {**b.TAGS, 'liabilities': ('Liabilities',),
        'research_development': ('ResearchAndDevelopmentExpense',)}
LABELS = {**b.LABELS, 'liabilities': 'Liabilities',
          'research_development': 'R&D', 'rd_ratio': 'R&D / revenue',
          'liabilities_equity': 'Liabilities / equity'}


def analyze(company, ticker, provenance=None, growth_minimum=None):
    base = b.analyze(company, ticker, provenance)
    rows = base['rows']
    for row in rows:
        for metric in ('liabilities', 'research_development'):
            fact = b.pick_fact(company, metric, row['fiscal_end'], tag_map=TAGS,
                               instant_metrics=('equity', 'liabilities'))
            row['facts'][metric] = fact
            row[metric] = fact['value']
        equity, liabilities = row['equity'], row['liabilities']
        row['liabilities_equity'] = liabilities / equity if (
            liabilities is not None and equity is not None and equity > 0) else None
        rd, revenue = row['research_development'], row['revenue']
        row['rd_ratio'] = rd / revenue if rd is not None and revenue is not None and revenue > 0 else None
    first, last = rows[0]['revenue'], rows[-1]['revenue']
    cagr = None
    if len(rows) == 5 and first is not None and last is not None and first > 0 and last >= 0:
        cagr = (last / first) ** (1 / 4) - 1
    minimum = wood.GROWTH_MINIMUM if growth_minimum is None else growth_minimum
    if not math.isfinite(minimum) or minimum < 0:
        raise ValueError('The growth threshold must be a finite nonnegative rate.')
    checks = [{'investor': 'Buffett', **c} for c in base['checks']]
    checks += wood.evaluate(rows, cagr, growth_minimum=minimum)
    checks += burry.evaluate(rows)
    base.update(rows=rows, checks=checks, revenue_cagr=cagr, growth_minimum=minimum)
    base['facts_sha256'] = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    base['analysis_sha256'] = hashlib.sha256(json.dumps(
        {'rows': rows, 'checks': checks, 'growth_minimum': minimum}, sort_keys=True).encode()).hexdigest()
    return base


def load_report(ticker, refresh=False, offline=False, growth_minimum=None):
    ticker = b.validate_ticker(ticker)
    if refresh and offline:
        raise ValueError('Choose refresh or offline, not both.')
    path = DATA / f'{ticker}_facts.json'
    if offline and not path.exists():
        raise ValueError(f'No saved Lab 19 SEC snapshot for {ticker}. Download it first.')
    if path.exists() and not refresh:
        snapshot = json.loads(path.read_text())
    else:
        snapshot = b.download_snapshot(ticker, data_dir=DATA, tag_map=TAGS)
    return analyze(snapshot['companyfacts'], ticker, snapshot['provenance'], growth_minimum)


def display_value(row, metric):
    if metric in b.LABELS:
        return b.display_value(row, metric)
    value = row[metric]
    if value is None:
        if metric == 'liabilities_equity':
            return 'not known'
        if metric == 'rd_ratio' and row['research_development'] is not None:
            return 'not known'
        return 'not found'
    if metric == 'rd_ratio':
        return f'{value:.2%}'
    if metric == 'liabilities_equity':
        return f'{value:.2f}'
    return f'{value / 1e6:,.6f}'.rstrip('0').rstrip('.')


def display_rows(report):
    return [{'Fiscal year end': row['fiscal_end'],
             **{label: display_value(row, metric) for metric, label in LABELS.items()}}
            for row in report['rows']]


def screen_summary(report, investor):
    statuses = [c['status'] for c in report['checks'] if c['investor'] == investor]
    if 'fail' in statuses:
        return 'fails screen'
    if 'not known' in statuses:
        return 'incomplete'
    return 'passes screen'


def render_report(report):
    lines = [f"# {report['ticker']} — {report['company']}",
             'SEC EDGAR; 10-K only; monetary figures in USD millions.',
             f"Source: {report['provenance'].get('source_url', 'synthetic test fixture')}",
             f"Downloaded UTC: {report['provenance'].get('downloaded_at_utc', 'synthetic test fixture')}",
             '', '| ' + ' | '.join(['Fiscal year end', *LABELS.values()]) + ' |',
             '| ' + ' | '.join(['---'] * (len(LABELS) + 1)) + ' |']
    lines += ['| ' + ' | '.join(row.values()) + ' |' for row in display_rows(report)]
    cagr = report['revenue_cagr']
    lines += ['', 'Revenue CAGR, first year to last: ' + ('not known' if cagr is None else f'{cagr:.2%}'),
              '', '| Investor | Check | Result |', '| --- | --- | --- |']
    lines += [f"| {c['investor']} | {c['check']} | {c['status']} |" for c in report['checks']]
    lines += ['', '| Investor | Screen summary |', '| --- | --- |']
    lines += [f'| {investor} | {screen_summary(report, investor)} |' for investor in INVESTORS]
    lines += ['', '## Source ledger',
              '| Fiscal end | Metric | USD value | XBRL tag | Start | Filed | Accession |',
              '| --- | --- | --- | --- | --- | --- | --- |']
    for row in report['rows']:
        for metric, fact in row['facts'].items():
            source = fact['source'] or {}
            value = 'not found' if fact['value'] is None else f"{fact['value']:,}"
            lines.append('| ' + ' | '.join([row['fiscal_end'], LABELS[metric], value,
                         fact['tag'] or 'not found', source.get('start', 'instant' if source else 'not found'),
                         source.get('filed', 'not found'), source.get('accn', 'not found')]) + ' |')
    lines += ['', 'ROE = NetIncomeLoss / StockholdersEquity (year-end).',
              'Owner earnings = NetCashProvidedByUsedInOperatingActivities minus selected capital spending.',
              'R&D / revenue = ResearchAndDevelopmentExpense / selected revenue.',
              'Liabilities / equity = Liabilities / StockholdersEquity; nonpositive equity is not known.',
              'Revenue CAGR = (last revenue / first revenue) ** (1 / 4) - 1.',
              'The derived metrics have formulas, not direct XBRL tags.', *report['warnings']]
    return '\n'.join(lines) + '\n'


def unprinted_numbers(memo, report):
    financial = '\n'.join(' '.join(row.values()) for row in display_rows(report))
    financial += '\n' + ' '.join(row['fiscal_end'][:4] for row in report['rows'])
    financial += '\n' + '\n'.join(c['check'] for c in report['checks'])
    if report['revenue_cagr'] is not None:
        financial += f"\n{report['revenue_cagr']:.2%}"
    allowed = {b.numeric_key(m.group()) for m in b.NUMBER.finditer(financial)}
    return list(dict.fromkeys(m.group() for m in b.NUMBER.finditer(memo)
                              if b.numeric_key(m.group()) not in allowed))


def memo_path(ticker, investor):
    return MEMOS / f'{b.validate_ticker(ticker)}_{INVESTORS[investor]}.md'


def bind_memos(report):
    bindings = []
    for investor in INVESTORS:
        path = memo_path(report['ticker'], investor)
        memo = path.read_text()
        bad = unprinted_numbers(memo, report)
        if bad:
            raise ValueError(f'{investor} memo has unprinted numbers: {bad}')
        bindings.append((path, memo))
    for path, memo in bindings:
        path.with_suffix('.json').write_text(json.dumps({
            'facts_sha256': report['facts_sha256'], 'analysis_sha256': report['analysis_sha256'],
            'memo_sha256': hashlib.sha256(memo.encode()).hexdigest()}, indent=2) + '\n')


def save_report(report, suffix=''):
    DATA.mkdir(parents=True, exist_ok=True)
    stem = f"{report['ticker']}{suffix}"
    (DATA / f'{stem}_report.json').write_text(json.dumps(report, indent=2) + '\n')
    (DATA / f'{stem}_output.md').write_text(render_report(report))


def run_cli(investor=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ticker')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--growth-minimum', type=float, default=None)
    parser.add_argument('--bind-memos', action='store_true')
    args = parser.parse_args()
    try:
        report = load_report(args.ticker, args.refresh, args.offline, args.growth_minimum)
        suffix = '' if args.growth_minimum is None else '_growth_probe'
        save_report(report, suffix)
        print(render_report(report))
        if investor:
            print(f'Invoked skill: {investor}; {screen_summary(report, investor)}.')
        if args.bind_memos:
            bind_memos(report)
            print('All panel memos match printed numbers and are bound to these facts and checks.')
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from None


if __name__ == '__main__':
    run_cli()
