"""Lab 18: python -m streamlit run buffett_app.py."""

import hashlib
import importlib.util
import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / '.agents/skills/buffett-business/scripts/buffett.py'
spec = importlib.util.spec_from_file_location('buffett_engine', SCRIPT)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

st.set_page_config(page_title='Buffett business screen', page_icon='📖', layout='wide')

with st.sidebar:
    st.header('Company')
    ticker_input = st.text_input('Ticker', 'COST', key='ticker')
    refresh = st.button('Download latest SEC facts', key='refresh')
    show_panel = st.checkbox('Show Lab 19 investor panel', key='show_panel')
    st.caption('Saved SEC snapshots load first. Download only when you want to refresh the facts.')

st.title('Legend investor panel' if show_panel else 'Buffett business screen')
st.caption('Data from SEC EDGAR; built with AI help, a learning demonstration, not investment advice.')
if show_panel:
    from legend_panel_ui import render_panel
    render_panel(ticker_input, refresh)
    st.stop()

try:
    ticker = engine.validate_ticker(ticker_input)
    with st.spinner('Reading SEC facts…'):
        report = engine.load_report(ticker, refresh=refresh)
except (ValueError, OSError, json.JSONDecodeError) as error:
    st.error(str(error))
    st.stop()

st.subheader(f"{report['company']} ({ticker})")
provenance = report['provenance']
st.caption(f"Saved SEC download: {provenance.get('downloaded_at_utc', 'unknown')}. "
           'Annual filings only; figures below in USD millions except ROE.')
st.link_button('SEC company facts source', provenance['source_url'])
for warning in report['warnings']:
    st.warning(warning)

st.subheader('Owner earnings and net income')
chart = {
    'Fiscal year end': [r['fiscal_end'] for r in report['rows']],
    'Owner earnings': [None if r['owner_earnings'] is None else r['owner_earnings'] / 1e6
                       for r in report['rows']],
    'Net income': [None if r['net_income'] is None else r['net_income'] / 1e6
                   for r in report['rows']],
}
st.line_chart(chart, x='Fiscal year end', y=['Owner earnings', 'Net income'],
              y_label='USD millions')
if any(r['owner_earnings'] is None for r in report['rows']):
    st.info('Missing owner earnings are not plotted or replaced with zero. The net-income series remains available.')

st.subheader('Annual facts and computed measures')
st.table(engine.display_rows(report))
st.caption('ROE uses year-end equity. Owner earnings use operating cash flow minus total reported '
           'capital spending, the lab proxy; this is not an estimate of maintenance capital spending.')

st.subheader('Buffett checks')
st.table([{'Check': c['check'], 'Result': c['status']} for c in report['checks']])
st.caption('First-to-last growth does not require growth in every intervening year. '
           'A missing required input makes the affected check not known.')

with st.expander('Inspect the XBRL tags and filing evidence'):
    ledger = []
    for row in report['rows']:
        for metric, fact in row['facts'].items():
            source = fact['source'] or {}
            ledger.append({'Fiscal end': row['fiscal_end'], 'Metric': engine.LABELS[metric],
                           'XBRL tag': fact['tag'] or 'not found',
                           'Period start': source.get('start', 'instant' if fact['source'] else 'not found'),
                           'Filed': source.get('filed', 'not found'),
                           'Accession': source.get('accn', 'not found')})
    st.table(ledger)
    st.code('ROE = NetIncomeLoss / StockholdersEquity\n'
            'Owner earnings = NetCashProvidedByUsedInOperatingActivities − selected capex tag')

st.subheader('Buffett-inspired memo')
memo_path = engine.MEMOS / f'{ticker}_buffett.md'
binding_path = memo_path.with_suffix('.json')
saved = memo_path.read_text() if memo_path.exists() else ''
if binding_path.exists():
    binding = json.loads(binding_path.read_text())
    if binding['facts_sha256'] != report['facts_sha256']:
        st.warning('This saved memo uses different SEC facts. Review it against the current table.')
    elif binding['memo_sha256'] != hashlib.sha256(saved.encode()).hexdigest():
        st.warning('The saved memo changed since its last verification. Review its claims and numbers.')
if not saved:
    st.info('No saved AI memo for this ticker yet. Use the buffett-business skill to write one '
            'from the report, then rerun the app, or paste a draft below.')
memo = st.text_area('Memo text — edit here to test an unsupported number', value=saved,
                    height=260, key=f'memo_{ticker}_{report["facts_sha256"]}')
if memo.strip():
    bad = engine.unprinted_numbers(memo, report)
    if bad:
        st.error('Unprinted number(s): ' + ', '.join(bad))
    else:
        st.success('Every numeric value in this memo appears in the displayed facts or check threshold.')
    st.markdown(memo)
    st.download_button('Download memo as Markdown', memo, file_name=f'{ticker}_buffett.md')
st.caption('The number flag checks whether a value was printed, not whether it is attached to '
           'the correct year or metric. Memo edits here do not overwrite the saved file.')
st.download_button('Download computed report', engine.render_report(report),
                   file_name=f'{ticker}_report.md')
