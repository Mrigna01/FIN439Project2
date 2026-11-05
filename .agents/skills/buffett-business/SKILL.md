---
name: buffett-business
description: Analyze a company's business for FIN439 Lab 18 using Buffett's three checks, SEC EDGAR annual facts, and a memo limited to script-printed numbers. Use for a ticker's Buffett business screen, not stock pricing or trade advice.
---

# Buffett business screen

Use this skill's bundled `scripts/buffett.py`. From the repository root:

```sh
.venv/bin/python .agents/skills/buffett-business/scripts/buffett.py COST
```

Replace COST with the requested ticker. Live requests read `SEC_USER_AGENT`, or the
ignored `.sec-user-agent` file in the repository root. It must contain the caller's
real name and email; do not invent either or publish the contact file.
Use `--offline` only to recompute from the saved, explicitly labelled SEC snapshot.
Use `--refresh` to deliberately replace the snapshot with newly downloaded facts.
Network errors are errors, not evidence of missing financial values.

Read the printed report and `data/lab18/TICKER_report.json` before writing a memo.
The script uses only USD facts from 10-K filings, annual flow periods of 350–380
elapsed days (including retail 52/53-week years), and the latest filing for each
period. Tags follow the lab's ordered fallbacks. Missing raw values stay
`not found`; undefined ratios and checks with missing inputs stay `not known`.
Never paste the course's known-answer table into the data pipeline.

Write a short Buffett-inspired educational memo to
`docs/lab18/TICKER_buffett.md`, with a clear **own the business**, **watch it**, or
**pass** judgment. This is a simulated perspective, not an actual Buffett opinion.
Judge business quality from the computed checks; do not invent a moat, management
record, forecast, stock price, valuation, or margin of safety. Use only numeric
tokens printed in the script's report, with the same units and rounding. State
that missing owner earnings prevent judging owner earnings. Discuss weaknesses
of the screen: year-end equity, simplified cash-flow-minus-capex owner earnings,
and the difference between first-to-last growth and uninterrupted growth.

The course overrides FAskills' broader valuation instructions: no installation of
FAskills, paid data, API keys, price targets, or projected estimates. Read its
[Buffett page](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/warren_buffett.md)
as philosophy only. The lab definition is operating cash flow minus capital
spending, not a maintenance-capex estimate.

Bind the memo to the exact calculated data and verify its numbers:

```sh
.venv/bin/python .agents/skills/buffett-business/scripts/buffett.py COST --offline --bind-memo
```

This fails if the memo contains an unprinted number. It writes a fingerprint
sidecar so the app can identify a memo written for different facts. The number
flag checks provenance of numbers, not whether a sentence assigns them to the
right metric or makes a sound claim; review those yourself.

Run the app with `.venv/bin/python -m streamlit run buffett_app.py`.
Follow the same process on JPM, preserving its gaps. Do not claim partner work,
an AI-off explanation, a separate browser-AI probe, or a submission occurred
unless there is actual evidence.

Source: [Lab 18](https://github.com/CinderZhang/FIN43900-Fall2026/blob/main/lessons/week-11/lab-18-legend-investor-as-skill.md).
