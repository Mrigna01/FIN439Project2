"""SEC-only Buffett business screen. No third-party dependencies or API keys."""

import argparse
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / 'data' / 'lab18'
MEMOS = ROOT / 'docs' / 'lab18'
TICKERS_URL = 'https://www.sec.gov/files/company_tickers.json'
TAGS = {
    'revenue': ('RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues'),
    'net_income': ('NetIncomeLoss',),
    'operating_cash_flow': ('NetCashProvidedByUsedInOperatingActivities',),
    'capital_spending': ('PaymentsToAcquirePropertyPlantAndEquipment',
                         'PaymentsToAcquireProductiveAssets'),
    'equity': ('StockholdersEquity',),
}
LABELS = {
    'revenue': 'Revenue', 'net_income': 'Net income',
    'operating_cash_flow': 'Operating cash flow',
    'capital_spending': 'Capital spending', 'equity': 'Equity',
    'roe': 'ROE', 'owner_earnings': 'Owner earnings',
}
NUMBER = re.compile(
    r'\b\d{4}-\d{2}-\d{2}\b|(?<=FY)\d{4}\b|(?<![\w.])[-+−]?(?:\d{1,3}(?:,\d{3})+|\d+)'
    r'(?:\.\d+)?(?:[eE][-+]?\d+)?%?(?![\w]|\.\d)'
)


def validate_ticker(ticker):
    ticker = ticker.strip().upper()
    if not re.fullmatch(r'[A-Z][A-Z0-9.-]{0,14}', ticker):
        raise ValueError('Use a ticker such as COST or JPM.')
    return ticker


def user_agent():
    contact = ROOT / '.sec-user-agent'
    value = os.environ.get('SEC_USER_AGENT') or (
        contact.read_text().strip() if contact.exists() else '')
    if not re.search(r'\S+@\S+\.\S+', value) or len(value.split()) < 2:
        raise ValueError('Set SEC_USER_AGENT or .sec-user-agent to your name and email.')
    return value


def fetch_json(url):
    request = Request(url, headers={'User-Agent': user_agent(),
                                   'Accept': 'application/json'})
    # Sequential downloads, with a pause between requests; no bulk harvesting.
    time.sleep(0.2)
    try:
        with urlopen(request, timeout=45) as response:
            raw = response.read()
    except (HTTPError, URLError, TimeoutError) as error:
        raise ValueError(f'SEC download failed for {url}: {error}. '
                         'No financial values have been inferred.') from error
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def annual_fact(fact):
    if fact.get('form') != '10-K' or fact.get('fp') != 'FY':
        return False
    if not isinstance(fact.get('val'), (int, float)) or not math.isfinite(fact['val']):
        return False
    try:
        duration = (date.fromisoformat(fact['end']) - date.fromisoformat(fact['start'])).days
    except (KeyError, ValueError):
        return False
    return 350 <= duration <= 380


def fiscal_ends(company):
    facts = company.get('facts', {}).get('us-gaap', {})
    # The fiscal year printed on a comparative fact is often the filing's FY,
    # so use the annual period's end instead of grouping on the `fy` field.
    entries = facts.get('NetIncomeLoss', {}).get('units', {}).get('USD', [])
    ends = sorted({f['end'] for f in entries if annual_fact(f)})[-5:]
    if not ends:
        raise ValueError('No annual USD NetIncomeLoss facts from 10-K filings found.')
    return ends


def pick_fact(company, metric, end, tag_map=None, instant_metrics=('equity',)):
    facts = company.get('facts', {}).get('us-gaap', {})
    for tag in (TAGS if tag_map is None else tag_map)[metric]:
        eligible = []
        for f in facts.get(tag, {}).get('units', {}).get('USD', []):
            if f.get('end') != end or f.get('form') != '10-K' or f.get('fp') != 'FY':
                continue
            if not isinstance(f.get('val'), (int, float)) or not math.isfinite(f['val']):
                continue
            if metric in instant_metrics:
                if 'start' in f:  # Equity is a point-in-time stock, not a flow.
                    continue
            elif not annual_fact(f):
                continue
            eligible.append(f)
        if not eligible:
            continue
        latest = max((f.get('filed', ''), f.get('accn', '')) for f in eligible)
        newest = [f for f in eligible if (f.get('filed', ''), f.get('accn', '')) == latest]
        if len({f['val'] for f in newest}) != 1:
            raise ValueError(f'Conflicting latest-filing values for {tag} ending {end}.')
        selected = max(newest, key=lambda f: f.get('start', ''))
        return {'value': selected['val'], 'tag': 'us-gaap:' + tag,
                'source': {k: selected[k] for k in
                           ('start', 'end', 'filed', 'accn', 'form', 'fy', 'fp') if k in selected}}
    return {'value': None, 'tag': None, 'source': None}


def year_row(company, end):
    """Turn one fiscal period into facts, preserving missing and undefined values."""
    selected = {metric: pick_fact(company, metric, end) for metric in TAGS}
    values = {metric: fact['value'] for metric, fact in selected.items()}
    income, equity = values['net_income'], values['equity']
    values['roe'] = income / equity if income is not None and equity is not None and equity > 0 else None
    cash, capex = values['operating_cash_flow'], values['capital_spending']
    values['owner_earnings'] = cash - capex if cash is not None and capex is not None else None
    return {'fiscal_end': end, **values, 'facts': selected}


def all_years(values, predicate, count):
    if count != 5 or any(v is None for v in values):
        return 'not known'
    return 'pass' if all(predicate(v) for v in values) else 'fail'


def analyze(company, ticker, provenance=None):
    rows = [year_row(company, end) for end in fiscal_ends(company)]
    roe = [r['roe'] for r in rows]
    earnings = [r['owner_earnings'] for r in rows]
    growth = 'not known'
    if len(rows) == 5 and earnings[0] is not None and earnings[-1] is not None:
        growth = 'pass' if earnings[-1] > earnings[0] else 'fail'
    checks = [
        {'check': 'ROE of 15.0% or more every year',
         'status': all_years(roe, lambda v: v >= .15, len(rows))},
        {'check': 'Owner earnings positive every year',
         'status': all_years(earnings, lambda v: v > 0, len(rows))},
        {'check': 'Owner earnings grew, first year to last', 'status': growth},
    ]
    fingerprint = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    return {'ticker': validate_ticker(ticker), 'company': company.get('entityName', ticker),
            'cik': company.get('cik'), 'rows': rows, 'checks': checks,
            'facts_sha256': fingerprint, 'provenance': provenance or {},
            'warnings': [] if len(rows) == 5 else ['Fewer than five fiscal years; checks are not known.']}


def download_snapshot(ticker, data_dir=None, tag_map=None):
    destination = DATA if data_dir is None else Path(data_dir)
    tags = TAGS if tag_map is None else tag_map
    destination.mkdir(parents=True, exist_ok=True)
    cache = ROOT / '.cache' / 'lab18'
    cache.mkdir(parents=True, exist_ok=True)
    mapping_path = cache / 'company_tickers.json'
    if mapping_path.exists():
        mapping = json.loads(mapping_path.read_text())
    else:
        mapping, _ = fetch_json(TICKERS_URL)
        mapping_path.write_text(json.dumps(mapping))
    match = next((v for v in mapping.values() if v['ticker'].upper() == ticker), None)
    if match is None:
        raise ValueError(f'{ticker} was not found in the SEC ticker map.')
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(match['cik_str']):010d}.json"
    company, digest = fetch_json(url)
    ends = set(fiscal_ends(company))
    # Retain the original SEC fact records relevant to this assignment, not a
    # manually entered table. Derived values are always recomputed from them.
    subset = {}
    for tag in {tag for candidates in tags.values() for tag in candidates}:
        original = company.get('facts', {}).get('us-gaap', {}).get(tag)
        if original is not None:
            entries = [f for f in original.get('units', {}).get('USD', [])
                       if f.get('end') in ends and f.get('form') == '10-K']
            subset[tag] = {'label': original.get('label'), 'units': {'USD': entries}}
    snapshot = {'companyfacts': {'cik': company['cik'], 'entityName': company['entityName'],
                                'facts': {'us-gaap': subset}},
                'provenance': {'source_url': url, 'ticker_map_url': TICKERS_URL,
                               'downloaded_at_utc': datetime.now(timezone.utc).isoformat(),
                               'raw_response_sha256': digest,
                               'snapshot_scope': 'Unmodified relevant USD 10-K fact records for the last five annual net-income period ends; other tags omitted.'}}
    (destination / f'{ticker}_facts.json').write_text(json.dumps(snapshot, indent=2) + '\n')
    return snapshot


def load_report(ticker, refresh=False, offline=False):
    ticker = validate_ticker(ticker)
    if refresh and offline:
        raise ValueError('Choose refresh or offline, not both.')
    path = DATA / f'{ticker}_facts.json'
    if offline and not path.exists():
        raise ValueError(f'No saved SEC snapshot for {ticker}; download it first.')
    snapshot = json.loads(path.read_text()) if path.exists() and not refresh else download_snapshot(ticker)
    return analyze(snapshot['companyfacts'], ticker, snapshot['provenance'])


def display_value(row, metric):
    value = row[metric]
    if value is None:
        return 'not known' if metric == 'roe' else 'not found'
    if metric == 'roe':
        return f'{value:.1%}'
    # Print in millions, without silently rounding small companies to zero.
    return f'{value / 1_000_000:,.6f}'.rstrip('0').rstrip('.')


def display_rows(report):
    return [{'Fiscal year end': r['fiscal_end'],
             **{LABELS[k]: display_value(r, k) for k in LABELS}} for r in report['rows']]


def render_report(report):
    lines = [f"# {report['ticker']} — {report['company']}",
             'SEC EDGAR; 10-K only; USD millions except ROE.',
             f"Source: {report['provenance'].get('source_url', 'synthetic test fixture')}",
             f"Downloaded UTC: {report['provenance'].get('downloaded_at_utc', 'not available')}",
             '', '| ' + ' | '.join(['Fiscal year end', *LABELS.values()]) + ' |',
             '| ' + ' | '.join(['---'] * (len(LABELS) + 1)) + ' |']
    for row in display_rows(report):
        lines.append('| ' + ' | '.join(row.values()) + ' |')
    lines += ['', '## Computed checks']
    lines.extend(f"- {c['check']}: {c['status']}" for c in report['checks'])
    lines += ['', '## XBRL source ledger',
              '| Fiscal end | Metric | USD value | XBRL tag | Period start | Filed | Accession |',
              '| --- | --- | --- | --- | --- | --- | --- |']
    for row in report['rows']:
        for metric, fact in row['facts'].items():
            source = fact['source'] or {}
            value = 'not found' if fact['value'] is None else f"{fact['value']:,}"
            lines.append('| ' + ' | '.join([row['fiscal_end'], LABELS[metric], value,
                         fact['tag'] or 'not found', source.get('start', 'instant' if source else 'not found'),
                         source.get('filed', 'not found'), source.get('accn', 'not found')]) + ' |')
    lines += ['', 'ROE = us-gaap:NetIncomeLoss / us-gaap:StockholdersEquity (year-end).',
              'Owner earnings = us-gaap:NetCashProvidedByUsedInOperatingActivities minus the selected capital-spending tag above.',
              'No direct XBRL tag exists for either derived measure.',
              'Missing inputs are not estimated; nonpositive equity makes ROE not known.',
              *report['warnings']]
    return '\n'.join(lines) + '\n'


def numeric_key(token):
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', token):
        return ('date', token)
    return ('percent' if token.endswith('%') else 'number',
            Decimal(token.replace(',', '').replace('−', '-').rstrip('%')))


def unprinted_numbers(memo, report):
    # Restrict the numeric allow-list to the displayed financial table and
    # thresholds. Filing IDs/URLs/timestamps must not authorize financial claims.
    printed = '\n'.join(' '.join(row.values()) for row in display_rows(report))
    printed += '\n' + '\n'.join(c['check'] for c in report['checks'])
    printed += '\n' + ' '.join(r['fiscal_end'][:4] for r in report['rows'])
    allowed = {numeric_key(m.group()) for m in NUMBER.finditer(printed)}
    return list(dict.fromkeys(m.group() for m in NUMBER.finditer(memo)
                              if numeric_key(m.group()) not in allowed))


def bind_memo(report):
    path = MEMOS / f"{report['ticker']}_buffett.md"
    memo = path.read_text()
    bad = unprinted_numbers(memo, report)
    if bad:
        raise ValueError(f'Memo contains unprinted numbers: {bad}')
    path.with_suffix('.json').write_text(json.dumps({
        'facts_sha256': report['facts_sha256'],
        'memo_sha256': hashlib.sha256(memo.encode()).hexdigest(),
        'note': 'AI-authored memo checked against the displayed financial numbers.'}, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ticker')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--bind-memo', action='store_true')
    args = parser.parse_args()
    try:
        report = load_report(args.ticker, args.refresh, args.offline)
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / f"{report['ticker']}_report.json").write_text(json.dumps(report, indent=2) + '\n')
        rendered = render_report(report)
        (DATA / f"{report['ticker']}_output.md").write_text(rendered)
        print(rendered)
        if args.bind_memo:
            bind_memo(report)
            print('Memo bound to these facts; no unprinted financial numbers.')
    except (ValueError, OSError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from None


if __name__ == '__main__':
    main()
