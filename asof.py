"""Lab 16 provenance gate. Run: python asof.py (standard library only)."""

import argparse
from datetime import date
from math import isfinite

# Editable, fictional course inputs. Row identifiers stay attached to every record.
DECISION_DATE = '2026-03-31'
ROWS = [
    {'row': 1, 'ticker': 'AAA', 'month': '2026-01', 'published': '2026-02-10', 'price': 101.0},
    {'row': 2, 'ticker': 'AAA', 'month': '2026-02', 'published': '2026-03-10', 'price': 104.0},
    {'row': 3, 'ticker': 'AAA', 'month': '2026-03', 'published': '2026-04-10', 'price': 109.0},
    {'row': 4, 'ticker': 'AAA', 'month': '2026-02', 'published': '2026-03-25', 'price': 103.0},
    {'row': 5, 'ticker': 'BBB', 'month': '2026-01', 'published': '2026-02-10', 'price': 98.0},
    {'row': 6, 'ticker': 'BBB', 'month': '2026-02', 'published': '2026-03-10', 'price': 97.0},
    {'row': 7, 'ticker': 'BBB', 'month': '2026-02', 'published': '2026-03-10', 'price': 97.0},
    {'row': 8, 'ticker': 'BBB', 'month': '2026-03', 'published': '2026-04-10', 'price': 92.0},
    {'row': 9, 'ticker': 'CCC', 'month': '2026-01', 'published': '2026-02-10', 'price': 110.0},
    {'row': 10, 'ticker': 'CCC', 'month': '2026-02', 'published': '2026-04-05', 'price': 112.0},
    {'row': 11, 'ticker': '', 'month': '2026-02', 'published': '2026-03-10', 'price': 99.0},
    {'row': 12, 'ticker': 'CCC', 'month': '2026-02', 'published': '2026-03-10', 'price': 111.0},
]


def latest_publications(rows):
    """Keep the most recent publication for each ticker/month, independent of row order."""
    latest = {}
    for row in sorted(rows, key=lambda item: (item['published'], item['row'])):
        key = (row['ticker'], row['month'])
        previous = latest.get(key)
        if previous is not None and previous['published'] == row['published']:
            raise ValueError(f"Conflicting values on the same publication date: rows "
                             f"{previous['row']} and {row['row']}.")
        latest[key] = row
    panel = sorted(latest.values(), key=lambda item: (item['ticker'], item['month']))
    kept = {row['row'] for row in panel}
    replaced = sorted(row['row'] for row in rows if row['row'] not in kept)
    return panel, replaced


def provenance_gate(rows, decision_date=DECISION_DATE):
    """Apply the four rules in order. None means no date cutoff (naive comparison).

    The original input records are not modified. Duplicate identity excludes the
    row identifier; the smallest original row number is retained.
    """
    cutoff = date.fromisoformat(decision_date) if decision_date is not None else None
    if len({row['row'] for row in rows}) != len(rows):
        raise ValueError('Original row identifiers must be unique.')
    active = [dict(row) for row in sorted(rows, key=lambda item: item['row'])]
    funnel = []

    def record(rule, status, removed):
        funnel.append({'rule': rule, 'status': status, 'count': len(removed),
                       'rows': sorted(removed), 'remaining': len(active)})

    missing = [row['row'] for row in active if not row['ticker'].strip()]
    active = [row for row in active if row['row'] not in missing]
    record('No ticker', 'quarantined', missing)

    # Structural validation prevents silently interpreting malformed input.
    for row in active:
        try:
            date.fromisoformat(row['published'])
            measured = date.fromisoformat(row['month'] + '-01')
            if measured.strftime('%Y-%m') != row['month'] or not isfinite(row['price']):
                raise ValueError('Invalid month or price')
        except (ValueError, TypeError) as error:
            raise ValueError(f"Malformed date or nonnumeric/nonfinite price in row {row['row']}.") from error

    seen, unique, duplicates = set(), [], []
    for row in active:
        signature = (row['ticker'], row['month'], row['published'], row['price'])
        if signature in seen:
            duplicates.append(row['row'])
        else:
            seen.add(signature)
            unique.append(row)
    active = unique
    record('Exact duplicate', 'removed', duplicates)

    future = [row['row'] for row in active
              if cutoff is not None and date.fromisoformat(row['published']) > cutoff]
    active = [row for row in active if row['row'] not in future]
    record('Published after decision date', 'removed', future)

    active, replaced = latest_publications(active)
    record('Older vintage replaced by a revision', 'removed', replaced)
    return {'decision_date': decision_date, 'input_count': len(rows), 'funnel': funnel, 'panel': active}


def signals(panel):
    """Return latest month-over-previous-calendar-month changes, with source rows."""
    grouped = {}
    for row in panel:
        grouped.setdefault(row['ticker'], []).append(row)
    result = {}
    for ticker, records in sorted(grouped.items()):
        records = sorted(records, key=lambda row: row['month'])
        latest = records[-1]
        item = {'month': latest['month'], 'latest_row': latest['row'], 'return': None}
        if len(records) < 2:
            item['reason'] = 'Previous month unavailable'
        else:
            previous = records[-2]
            a = date.fromisoformat(previous['month'] + '-01')
            b = date.fromisoformat(latest['month'] + '-01')
            if (b.year - a.year) * 12 + b.month - a.month != 1:
                item['reason'] = 'Previous calendar month unavailable'
            elif previous['price'] == 0:
                item['reason'] = 'Previous price is zero; percentage change undefined'
            else:
                item.update(previous_month=previous['month'], previous_row=previous['row'],
                            **{'return': latest['price'] / previous['price'] - 1})
        result[ticker] = item
    return result


def sanity_check(panel):
    """Separate classroom check, not a fifth step silently changing the provenance panel.

    Assumptions: one-year zeros, face value 100, nonnegative yields expected,
    and price(AAA) > price(BBB) > price(CCC) for comparable bonds.
    """
    rank = {'AAA': 0, 'BBB': 1, 'CCC': 2}
    results = []
    for row in panel:
        flags = []
        yield_value = None
        if row['price'] <= 0:
            flags.append('nonpositive price')
        else:
            yield_value = 100 / row['price'] - 1
            if yield_value < 0:
                flags.append('negative yield')
        for better in panel:
            if (row['month'] == better['month'] and row['ticker'] in rank
                    and better['ticker'] in rank and rank[row['ticker']] > rank[better['ticker']]
                    and row['price'] >= better['price']):
                flags.append(f"not priced below {better['ticker']}")
        results.append({**row, 'yield': yield_value, 'flags': flags})
    return results


def analyze(rows=ROWS, decision_date=DECISION_DATE):
    asof = provenance_gate(rows, decision_date)
    naive = provenance_gate(rows, None)
    return {'asof': asof, 'naive': naive, 'asof_signals': signals(asof['panel']),
            'naive_signals': signals(naive['panel']), 'sanity': sanity_check(asof['panel'])}


def format_signal(signal):
    if signal is None:
        return 'unavailable: no admitted rows'
    month = date.fromisoformat(signal['month'] + '-01').strftime('%B %Y')
    if signal['return'] is None:
        return f"unavailable ({month}; {signal['reason']})"
    return f"{signal['return']:+.2%} ({month}; rows {signal['previous_row']} -> {signal['latest_row']})"


def main(decision_date=DECISION_DATE):
    result = analyze(ROWS, decision_date)
    print(f'Lab 16 - Provenance gate | Decision date: {decision_date}')
    print(f"Input: {result['asof']['input_count']} rows")
    for i, step in enumerate(result['asof']['funnel'], 1):
        row_numbers = ', '.join(map(str, step['rows'])) or 'none'
        print(f"{i}. {step['rule']}: {step['count']} {step['status']}; "
              f"rows {row_numbers}; {step['remaining']} remain")
    print('\nAs-of panel')
    print('Row  Ticker  Month    Published   Price')
    for row in result['asof']['panel']:
        print(f"{row['row']:>3}  {row['ticker']:<6}  {row['month']}  {row['published']}  {row['price']:.1f}")
    print('\nSignals: as-of versus naive (latest publication, no date cutoff)')
    for ticker in sorted(set(result['asof_signals']) | set(result['naive_signals'])):
        print(f"{ticker}: as-of {format_signal(result['asof_signals'].get(ticker))}")
        print(f"     naive {format_signal(result['naive_signals'].get(ticker))}")
    print('\nSeparate sanity check: one-year zero-coupon bonds, face value 100')
    for row in result['sanity']:
        yield_text = f"{row['yield']:+.2%}" if row['yield'] is not None else 'undefined'
        print(f"Row {row['row']}: {row['ticker']} {row['month']}, yield {yield_text}; "
              f"{'; '.join(row['flags']) or 'no stated sanity rule broken'}")
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decision-date', default=DECISION_DATE, help='YYYY-MM-DD, inclusive cutoff')
    args = parser.parse_args()
    try:
        main(args.decision_date)
    except ValueError as error:
        raise SystemExit(f'Input error: {error}') from None
