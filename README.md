# FIN439 Project 2

Portfolio mandate checks, baseline portfolios and a Streamlit stability app for the Campus Scholarship Reserve case.

## Run the app

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app starts with Meridian's training inputs. Select **Campus Scholarship Reserve** to use the included prices and the case's 5.5% return objective and 4% reserve minimum. You can also upload a CSV with `Date` first and three to six fund columns. Change return estimates or switch to the last 36 months to compare allocations.

## Lab write-ups

- [Lab 13: mandate](lab13.md)
- [Lab 14: baselines and fund selection](lab14.md)
- [Lab 15: stability decision and computed results](lab15.md)

## Checks

```sh
python mandate.py
python portfolio.py
python verify_lab14.py
python verify_lab15.py
```

`portfolio.py` retains the Lab 14 printed results. The Lab 15 verification script also writes `data/lab15_results.json` with the computed scenarios. The temporary correlation test restores the original engine file after checking it.

The saved `prices.csv` snapshot uses SGOV, SCHR, USIG and VT, with 61 monthly prices per fund and 60 monthly returns. Sources and the October 22, 2026 download date are recorded in the write-ups and `data/prices_source.json`. Running `python download_prices.py` refreshes the same date range; provider revisions may change historical adjusted prices, so rerun the checks and review the write-up if refreshing.

Built with AI help as a learning demonstration, not investment advice.
