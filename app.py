"""Lab 15. Run: python -m streamlit run app.py"""

from copy import deepcopy
from hashlib import sha256
import importlib
from pathlib import Path

import streamlit as st
import portfolio as engine

# Reload the single engine so saved input changes appear on a browser refresh.
engine = importlib.reload(engine)
ROOT = Path(__file__).resolve().parent

st.set_page_config(page_title="Portfolio stability", page_icon="📊", layout="wide")
st.title("Portfolio stability")
st.caption("Built with AI help, a learning demonstration, not investment advice.")

with st.sidebar:
    st.header("Mandate and data")
    universe = st.radio("Portfolio universe", ["Meridian training", "Campus Scholarship Reserve"], key="universe")
    uploaded = st.file_uploader("Upload monthly adjusted prices", type=["csv"], key="upload")
    st.caption("An upload replaces the selected data. Date first, oldest month first, 3–6 funds.")

try:
    data = uploaded.getvalue() if uploaded is not None else (
        (ROOT / "prices.csv").read_bytes() if universe == "Campus Scholarship Reserve" else None)
    source_key = sha256(data).hexdigest()[:12] if data is not None else "meridian"
    loaded = engine.estimate_from_csv(data) if data is not None else {
        "sleeves": deepcopy(engine.SLEEVES), "correlations": deepcopy(engine.CORRELATIONS)}
    campus = {s["name"] for s in loaded["sleeves"]} == {"SGOV", "SCHR", "USIG", "VT"}
except (ValueError, UnicodeError, OSError) as error:
    st.error(f"Cannot load prices: {error}")
    st.stop()

with st.sidebar:
    objective = st.number_input("Objective return (%)", value=5.5 if campus else 6.5,
                                step=0.1, format="%.2f", key=f"objective_{source_key}") / 100
    minimum = st.number_input("Reserve minimum (%)", min_value=0.0, max_value=100.0,
                              value=4.0 if campus else 3.0, step=1.0, format="%.2f",
                              key=f"minimum_{source_key}") / 100
    last_36 = st.toggle("Use last 36 months", value=False, disabled=data is None, key="last36")
    if campus:
        st.caption("Campus: CPI estimate 2.5% + 3% = 5.5%; reserve minimum 4%.")
    else:
        st.caption("Meridian starts at 6.5% return and 3% reserves. Set your own rules for other uploads.")

try:
    active = engine.estimate_from_csv(data, last_36=True) if data is not None and last_36 else deepcopy(loaded)
except (ValueError, UnicodeError) as error:
    st.error(str(error))
    st.stop()

st.subheader("Return estimates and reserve eligibility")
if data is not None:
    st.caption(f"{active['observations']} monthly returns: {active['return_start']} to {active['end']}. "
               "Annual arithmetic mean × 12; sample standard deviation × √12. History is an estimate, not a forecast.")
else:
    st.caption("Meridian uses the course's training assumptions.")

# Switching sample windows resets return edits to the selected window's estimates.
signature = (source_key, bool(last_36 and data is not None))
reset = st.button("Reset return estimates", key="reset_returns")
if st.session_state.get("estimate_signature") != signature or reset:
    for i, sleeve in enumerate(active["sleeves"]):
        st.session_state[f"return_{source_key}_{i}"] = sleeve["return"] * 100
    st.session_state["estimate_signature"] = signature

edited = deepcopy(active["sleeves"])
baseline_sleeves = deepcopy(loaded["sleeves"])
for i, (sleeve, column) in enumerate(zip(edited, st.columns(len(edited)))):
    with column:
        sleeve["return"] = st.number_input(f"{sleeve['name']} return estimate (%)",
                                            step=0.1, format="%.4f",
                                            key=f"return_{source_key}_{i}") / 100
        sleeve["reserve_eligible"] = st.checkbox(f"{sleeve['name']} reserve-eligible",
                                                  value=sleeve["reserve_eligible"],
                                                  key=f"reserve_{source_key}_{i}")
        baseline_sleeves[i]["reserve_eligible"] = sleeve["reserve_eligible"]

try:
    baseline = engine.search_portfolio(baseline_sleeves, loaded["correlations"], objective, minimum)
    current = engine.search_portfolio(edited, active["correlations"], objective, minimum)
except ValueError as error:
    st.error(f"Input error: {error}")
    st.stop()


def show_result(title, result, sleeves):
    st.subheader(title)
    if result is None:
        st.warning("no mix meets the objective")
        st.caption("No 5-point grid allocation meets both the current return and reserve rules.")
        return
    st.table({"Asset": [s["name"] for s in sleeves],
              "Weight": [f"{weight:.2%}" for weight in result["weights"]]})
    a, b = st.columns(2)
    a.metric("Expected return (estimate)", f"{result['return']:.2%}")
    b.metric("Annual volatility", f"{result['volatility']:.2%}")
    st.metric("Reserve-eligible weight", f"{result['reserve']:.2%}")
    st.caption(f"{result['feasible']:,} feasible mixes from {result['evaluated']:,} grid allocations.")


st.divider()
st.caption("Both results use the current objective and reserve rules. The loaded comparison keeps "
           "the original return estimates and, for CSV data, the full sample's volatility and correlations.")
left, right = st.columns(2)
with left:
    show_result("As loaded · all months" if data is not None else "As loaded · Meridian", baseline, baseline_sleeves)
with right:
    show_result("Current scenario · last 36 months" if data is not None and last_36 else "Current scenario", current, edited)
change = engine.largest_weight_change(baseline, current)
if change is None:
    st.info("Largest weight change: unavailable because at least one scenario has no feasible mix.")
else:
    st.metric("Largest weight change", f"{change:.2f} points")
st.caption("Lowest estimated risk on a 5-percentage-point grid. The app checks long-only weights, "
           "the return objective and the reserve minimum; it does not establish full mandate compliance.")

with st.expander("See the estimated risk inputs"):
    st.table({"Asset": [s["name"] for s in edited],
              "Annual volatility": [f"{s['volatility']:.2%}" for s in edited]})
    st.write("Correlation matrix (same asset order)")
    st.table({s["name"]: [round(row[i], 4) for row in active["correlations"]]
              for i, s in enumerate(edited)})
