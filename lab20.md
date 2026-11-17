# Lab 20 — Project 2 Readiness

## Partner cold run

My partner cloned the repository and followed the README. The first command, `source .venv/bin/activate`, failed immediately because the clone had no virtual environment. I updated the README to put the Python version check and environment creation before activation, then pushed the fix.

On the rerun, my partner created the environment, installed the dependencies, and started the app with `python -m streamlit run app.py`. Setup and verification took about 31 seconds. Under **Campus Scholarship Reserve → Current scenario**, the app showed 75% SGOV and 25% VT, with a 5.76% estimated annual return, 3.82% annual volatility, and 75% eligible reserves. Running `python lab20.py` reproduced those figures.

[README fix](https://github.com/Mrigna01/FIN439Project2/commit/947645a) · [Saved decision output](data/lab20-output.txt)

## Locked changed-input record

** prediction,** I would raise the minimum reserve share from 4% to 80% of portfolio value while holding the full-sample return estimates and the 5.50% annual objective fixed. I expect the starting mix to fail the new floor. The higher floor leaves room for at most 20% in VT, so I expect even the highest-return mix at that floor to miss the 5.50% objective. I would stop the pilot if no allocation passes both rules.

The [actual pre-run commit](https://github.com/Mrigna01/FIN439Project2/commit/af9bd3b5117bb19c18b0dd6ea792ea439ebc6e88) 

**Result.** At the 4% floor, 408 of 1,771 mixes passed both rules. At the 80% floor, none passed. The highest-return mix at that floor was 80% SGOV and 20% VT, with a 5.35% estimated annual return. That matched the prediction and stopped the pilot under the tighter rule.

[Before-and-after output](data/lab20-output.txt) · [Reproduction script](lab20.py)

## Code walkthrough and reflection

We walked through `search_portfolio`. My partner asked why the app didn’t select 80% SGOV and 20% VT. The search checks the return and reserve thresholds before comparing volatility. That mix meets the reserve floor and misses the return target, so it appears in the diagnostic report and the app returns no feasible allocation.

The clone exposed a setup issue I’d missed because my usual project folder already had a virtual environment. Before the deadline, I’d keep the checked-in prices and the starting mandate fixed so the app, report, and memo agree.

[Portfolio code](portfolio.py) · [Decision memo](docs/decision-memo.md)

## Decision

**Pilot 75% SGOV and 25% VT. Stop if the mix falls below the 5.50% estimated annual net return objective or breaches the applicable reserve floor.**
