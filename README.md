# FIN439 Project 2

Portfolio mandate checks, baseline portfolios and a Streamlit stability app for the Campus Scholarship Reserve case.

## Run the app

Use Python 3.11–3.14. On a fresh clone, check that `python3 --version`
shows a supported version before creating the environment. If `python3` points
to an older version, use the command for your supported interpreter instead,
such as `python3.13`. If you already have a working `.venv`, start at activation.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app starts with Meridian's training inputs. Select **Campus Scholarship Reserve** to use the included prices and the case's 5.5% return objective and 4% reserve minimum. You can also upload a CSV with `Date` first and three to six fund columns. Change return estimates or switch to the last 36 months to compare allocations.

## Reproduce the Campus decision

With a supported Python, run `python3 lab20.py` from the repository root.
If you activated the environment above, `python lab20.py` works too.
The report uses the checked-in prices and requires no third-party packages.

- [Saved decision output](data/lab20-output.txt)
- [Decision memo](docs/decision-memo.md)
- [Validation and AI use](docs/validation-and-ai-use.md)
- [Lab 20 checkout](lab20.md)

## Lab write-ups

- [Lab 13: mandate](lab13.md)
- [Lab 14: baselines and fund selection](lab14.md)
- [Lab 15: stability decision and computed results](lab15.md)
- [Lab 16: provenance gate and point-in-time signals](lab16.md)
- [Lab 18: Buffett investor skill, SEC facts, memos and verification](lab18.md)
- [Lab 19: Buffett, Cathie Wood and Burry panel](lab19.md)

## Lab 19 app

```sh
source .venv/bin/activate
python -m streamlit run legend_panel_app.py
python verify_lab19.py
```

The panel follows the professor's November 5 update replacing Graham with Cathie
Wood. It includes COST's known answer, NVDA from VT's largest disclosed equity
holding, three memos side by side, the growth-threshold probe and number flags.
The [Lab 19 write-up](lab19.md) links the results, source evidence and written analysis.

## Lab 18 app

This separate app uses the same environment and leaves the portfolio app above available:

```sh
source .venv/bin/activate
python -m streamlit run buffett_app.py
python verify_lab18.py
```

It starts from the saved SEC snapshot for COST; enter JPM to see the missing-data
probe. The [Lab 18 write-up](lab18.md) explains live downloads, the ignored SEC
contact configuration, the reusable Codex skill, and the remaining in-person work.

## Checks

```sh
python mandate.py
python portfolio.py
python verify_lab14.py
python verify_lab15.py
python asof.py
python verify_lab16.py
```

`portfolio.py` retains the Lab 14 printed results. The Lab 15 verification script also writes `data/lab15_results.json` with the computed scenarios. The temporary correlation test restores the original engine file after checking it.

The saved `prices.csv` snapshot uses SGOV, SCHR, USIG and VT, with 61 monthly prices per fund and 60 monthly returns. Sources and the October 22, 2026 download date are recorded in the write-ups and `data/prices_source.json`. Running `python download_prices.py` refreshes the same date range; provider revisions may change historical adjusted prices, so rerun the checks and review the write-up if refreshing.

Built with AI help as a learning demonstration, not investment advice.

Lab 16 uses a separate fictional training table. Run `python asof.py --decision-date 2026-04-15` to verify that the later-date signals equal the naive signals. The default cutoff remains March 31, 2026. `verify_lab16.py` saves the computed evidence under `data/`.
