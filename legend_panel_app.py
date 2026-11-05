"""Run with: python -m streamlit run legend_panel_app.py."""

import streamlit as st

from legend_panel_ui import render_panel

st.set_page_config(page_title='Legend investor panel', page_icon='📚', layout='wide')
st.title('Legend investor panel')
st.caption('Data from SEC EDGAR; built with AI help, a learning demonstration, not investment advice.')
with st.sidebar:
    st.header('Company and screen')
    ticker = st.text_input('Ticker', 'COST', key='ticker')
    refresh = st.button('Download latest SEC facts', key='refresh')
    threshold = st.radio('Cathie Wood revenue-growth threshold', ['15% — retained rule', '5% — lab probe'],
                         key='growth_threshold')
    st.caption('COST is the known answer. NVDA is the company selected from VT. '
               'Saved SEC snapshots load first; refresh deliberately.')
render_panel(ticker, refresh, .05 if threshold.startswith('5%') else .15)
