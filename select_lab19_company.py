"""Record VT's largest disclosed equity holding from Vanguard's public holdings data."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

URL = 'https://investor.vanguard.com/irr/funds/profile/3141-AdditionalFundData'
ROOT = Path(__file__).resolve().parent


def select(raw):
    details = json.loads(raw)['holdingDetails']
    # Small positions may have an unreported percentage. Rank by reported
    # dollar value instead; do not invent a zero weight for those positions.
    holdings = sorted(details['equityHoldings'],
                      key=lambda h: float(h['marketValueBaseCurrency'].replace('$', '').replace(',', '')),
                      reverse=True)
    if not holdings:
        raise ValueError('Vanguard returned no equity holdings.')
    return {
        'fund': 'VT', 'issuer': 'Vanguard',
        'issuer_page': 'https://advisors.vanguard.com/investments/products/vt/vanguard-total-world-stock-etf',
        'data_url': URL, 'downloaded_at_utc': datetime.now(timezone.utc).isoformat(),
        'raw_response_sha256': hashlib.sha256(raw).hexdigest(),
        'holdings_as_of': details['asOfDate'], 'equity_records_compared': len(holdings),
        'selection_method': 'Sort all disclosed equity holdings by reported USD market value; select the largest. Missing percentages are not estimated.',
        'selected_ticker': holdings[0]['ticker'],
        'top_equity_holdings': holdings[:10],
    }


if __name__ == '__main__':
    request = Request(URL, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    with urlopen(request, timeout=30) as response:
        raw = response.read()
    result = select(raw)
    path = ROOT / 'data/lab19/fund_selection.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(f"{result['fund']}: {result['selected_ticker']}, "
          f"{result['top_equity_holdings'][0]['marketValuePercentage']}, "
          f"holdings as of {result['holdings_as_of']}.")
