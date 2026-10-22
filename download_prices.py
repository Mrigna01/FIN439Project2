"""Download Yahoo adjusted closes, keeping the last trading day of each month.

Run: python download_prices.py
Writes prices.csv and data/prices_source.json. Uses the standard library only.
"""

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

TICKERS = ('BIL', 'IEF', 'LQD', 'VT')
START = '2021-09-01'  # Extra starting price allows 60 monthly returns.
END = '2026-10-01'  # Exclusive; October is incomplete at download time.
ROOT = Path(__file__).resolve().parent


def download():
    params = {
        'period1': int(datetime.fromisoformat(START).replace(tzinfo=timezone.utc).timestamp()),
        'period2': int(datetime.fromisoformat(END).replace(tzinfo=timezone.utc).timestamp()),
        'interval': '1d', 'events': 'div,splits', 'includeAdjustedClose': 'true',
    }
    series, sources = {}, {}
    for ticker in TICKERS:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?{urlencode(params)}'
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(request, timeout=45) as response:
            chart = json.load(response)['chart']
        if chart.get('error') or not chart.get('result'):
            raise ValueError(f'{ticker}: Yahoo returned no usable data: {chart.get("error")}')
        result = chart['result'][0]
        if result['meta']['currency'] != 'USD':
            raise ValueError(f'{ticker}: expected USD prices')
        timestamps = result['timestamp']
        adjusted = result['indicators']['adjclose'][0]['adjclose']
        closes = result['indicators']['quote'][0]['close']
        monthly = {}
        for stamp, price, close in zip(timestamps, adjusted, closes):
            day = datetime.fromtimestamp(stamp, ZoneInfo('America/New_York')).date().isoformat()
            if not START <= day < END:
                continue
            if price is None or not math.isfinite(price) or price <= 0:
                raise ValueError(f'{ticker}: invalid adjusted close on {day}')
            month = day[:7]
            if month not in monthly or day > monthly[month]['date']:
                monthly[month] = {'date': day, 'adj_close': price, 'close': close}
        expected = [f'{year:04d}-{month:02d}' for year in range(2021, 2027)
                    for month in range(1, 13) if '2021-09' <= f'{year:04d}-{month:02d}' <= '2026-09']
        if sorted(monthly) != expected:
            raise ValueError(f'{ticker}: missing or extra months; got {len(monthly)}')
        series[ticker] = monthly
        sources[ticker] = {'url': url, 'history_page': f'https://finance.yahoo.com/quote/{ticker}/history/',
                           'currency': 'USD', 'monthly_observations': monthly}
        print(f'{ticker}: {len(monthly)} complete month-end prices')
    rows = []
    for month in sorted(series[TICKERS[0]]):
        dates = {series[ticker][month]['date'] for ticker in TICKERS}
        if len(dates) != 1:
            raise ValueError(f'Month-end trading dates do not align in {month}')
        rows.append([dates.pop()] + [series[ticker][month]['adj_close'] for ticker in TICKERS])
    provenance = {'downloaded_at_utc': datetime.now(timezone.utc).isoformat(),
                  'start_inclusive': START, 'end_exclusive': END,
                  'method': 'Last daily adjusted close in each completed month; no filling or interpolation.',
                  'columns': ['Date', *TICKERS], 'rows': rows, 'sources': sources}
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data' / 'prices_source.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    return rows


def main():
    rows = download()
    with (ROOT / 'prices.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['Date', *TICKERS])
        writer.writerows(rows)
    print(f'Saved {len(rows)} prices per fund: {rows[0][0]} to {rows[-1][0]}.')


if __name__ == '__main__':
    main()
