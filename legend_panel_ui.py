"""Streamlit display shared by the Lab 18 extension and the Lab 19 entry point."""

import hashlib
import json
import re

import streamlit as st

import legend_panel as engine


def render_panel(ticker, refresh=False, growth_minimum=None):
    try:
        with st.spinner('Reading the shared SEC facts…'):
            report = engine.load_report(ticker, refresh=refresh, growth_minimum=growth_minimum)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        st.error(str(error))
        return
    st.subheader(f"{report['company']} ({report['ticker']})")
    st.caption(f"Saved SEC download: {report['provenance']['downloaded_at_utc']}. "
               'Annual filings only; monetary figures in USD millions.')
    st.link_button('SEC company facts source', report['provenance']['source_url'])
    for warning in report['warnings']:
        st.warning(warning)

    st.subheader('Owner earnings and net income')
    chart = {'Fiscal year end': [r['fiscal_end'] for r in report['rows']],
             'Owner earnings': [None if r['owner_earnings'] is None else r['owner_earnings'] / 1e6
                                for r in report['rows']],
             'Net income': [None if r['net_income'] is None else r['net_income'] / 1e6
                            for r in report['rows']]}
    st.line_chart(chart, x='Fiscal year end', y=['Owner earnings', 'Net income'], y_label='USD millions')
    st.subheader('Shared annual facts')
    st.table(engine.display_rows(report))
    st.metric('Revenue CAGR, first year to last',
              'not known' if report['revenue_cagr'] is None else f"{report['revenue_cagr']:.2%}")
    st.caption('ROE uses year-end equity; owner earnings subtract reported capital spending from '
               'operating cash flow. Revenue CAGR uses four intervals over five annual observations. '
               'R&D not found is not zero; an affected check is not known.')

    st.subheader('Investor × check')
    st.table([{'Investor': c['investor'], 'Check': c['check'], 'Result': c['status']}
              for c in report['checks']])
    st.caption('Screen summaries report the checks. The memos give separate AI judgments; '
               'neither is a recommendation to trade.')
    st.subheader('Three perspectives on the same facts')
    all_flags = {}
    for investor, column in zip(engine.INVESTORS, st.columns(3)):
        with column:
            st.markdown(f'### {investor}')
            st.write('Screen: ' + engine.screen_summary(report, investor))
            path = engine.memo_path(report['ticker'], investor)
            saved = path.read_text() if path.exists() else ''
            if path.with_suffix('.json').exists():
                binding = json.loads(path.with_suffix('.json').read_text())
                if binding['analysis_sha256'] != report['analysis_sha256']:
                    st.warning('This memo was written for different facts or thresholds. Review its verdict.')
                elif binding['memo_sha256'] != hashlib.sha256(saved.encode()).hexdigest():
                    st.warning('The saved memo changed since verification. Review its claims.')
            if not saved:
                st.info('No saved memo for this company. Run the investor skill on the printed report '
                        'and save its memo, or enter a memo below.')
            key = f"panel_memo_{engine.INVESTORS[investor]}_{report['ticker']}_{report['analysis_sha256']}"
            memo = st.text_area(f'{investor} memo — editable number probe', value=saved, height=320, key=key)
            if memo.strip():
                verdict = re.search(r'\*\*Verdict:\s*(.*?)\*\*', memo)
                if verdict:
                    st.write('Memo verdict: ' + verdict[1])
                bad = engine.unprinted_numbers(memo, report)
                if bad:
                    all_flags[investor] = bad
                    st.error('Unprinted number(s): ' + ', '.join(bad))
                else:
                    st.success('Memo numbers match the printed facts and thresholds.')
                st.markdown(memo)
                st.download_button('Download this memo', memo, file_name=path.name,
                                   key=f'download_{engine.INVESTORS[investor]}')
    if all_flags:
        st.error('Panel number flag: ' + '; '.join(f"{k}: {', '.join(v)}" for k, v in all_flags.items()))
    else:
        st.info('Panel number check complete. Each available memo is checked against the same printed inputs.')
    st.caption('A printed number can still be assigned to the wrong metric or year. The flag checks '
               'numeric provenance, not every claim. Edits here do not overwrite the saved memos.')
    with st.expander('XBRL tags, filing dates and calculation evidence'):
        st.markdown(engine.render_report(report))
    st.download_button('Download panel report', engine.render_report(report),
                       file_name=f"{report['ticker']}_panel.md")
