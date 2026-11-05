# Lab 19 — Legend Panel

I used Codex to build the investor skills, SEC data pipeline, Streamlit panel,
tests and written analysis. The financial values come from SEC EDGAR and the
checks are computed in Python. This is a learning demonstration, not investment advice.

## The version I followed

I followed the professor's November 5 revision,
[`c4ad923`](https://github.com/CinderZhang/FIN43900-Fall2026/blob/c4ad923d058d5250a237de56db26dfa99dbf87f6/lessons/week-11/lab-19-legend-panel.md),
which replaces Graham with **Cathie Wood**. My panel therefore contains Buffett,
Cathie Wood and Burry. The revision, timestamp and source link are recorded in
[source_revision.json](data/lab19/source_revision.json).

## D — The common question

**When three investors' skills read the same annual facts, where do they agree,
where do they split, and would I trust the panel?**

I trust the panel to apply explicit historical screens consistently, provided
every result keeps its source and missing-data status. I do not treat agreement
as a valuation or as independent confirmation from unrelated analysts. The
personas share the same data and AI assistance, but emphasize different
questions: Buffett tests profitability and owner earnings, Wood tests revenue
growth and research intensity, and Burry tests cash conversion and leverage.

## Opener — How the perspectives approach the sell-off

In the sell-off scenario described in the lab, a Wood-inspired approach would
ask whether long-term innovation and adoption evidence has changed before
reacting to falling prices. A price decline could prompt closer research if
the business thesis survives, but the decline alone does not prove a bargain.

A Burry-inspired approach would scrutinize the financial statements and ask
whether the sell-off exposes weak cash conversion or excessive obligations.
He need not buy simply because prices fell or short simply because sentiment
changed. These are interpretations of the assigned investor pages, not claims
that either investor made a particular trade today.

## Build — My implementation request and rules

I asked for a panel that preserves the Lab 18 calculations, chart, source ledger
and memo-number flag, adds the Wood and Burry skills, and runs every perspective
on the same selected annual SEC facts. I required missing inputs to stay
missing and the written judgments to stay separate from the quantitative checks.

The implementation adds `Liabilities` and `ResearchAndDevelopmentExpense` to
the Lab 18 tags. Liabilities and equity are fiscal-year-end balances; R&D,
revenue, income and cash flows are annual flows. Only USD facts from `10-K`
filings are eligible. The existing annual-period filter includes retail
fifty-two- and fifty-three-week years, and the latest filing wins when the same
period appears more than once. Each selected raw value retains its XBRL tag,
period end, filing date and accession number.

The new formulas are:

```text
Revenue CAGR = (last annual revenue / first annual revenue)^(1/4) - 1
R&D intensity = annual ResearchAndDevelopmentExpense / annual revenue
Liabilities/equity = year-end Liabilities / year-end StockholdersEquity
```

The growth formula uses four intervals between five annual observations.
Missing or invalid inputs do not become estimates. Nonpositive equity makes
the leverage ratio and its check `not known`; a missing R&D disclosure prints
`not found`, and its threshold check is `not known`. A failed check remains a
failure even if another investor prefers the business.

The two new skills are
[wood-business](.agents/skills/wood-business/SKILL.md) and
[burry-business](.agents/skills/burry-business/SKILL.md), with their checks in
their bundled [Wood script](.agents/skills/wood-business/scripts/wood.py) and
[Burry script](.agents/skills/burry-business/scripts/burry.py).
The [shared engine](legend_panel.py) reuses the
[Buffett skill's data-selection functions](.agents/skills/buffett-business/scripts/buffett.py).
I read the FAskills pages as philosophy; I did not install FAskills, add paid
data services, or generate price targets.

## V — Costco known answer

The panel reproduces the revised known answer from downloaded SEC facts:

| Fiscal year end | R&D / revenue | Liabilities / equity |
| --- | --- | ---: |
| 2022-08-28 | not found | 2.11 |
| 2023-09-03 | not found | 1.75 |
| 2024-09-01 | not found | 1.96 |
| 2025-08-31 | not found | 1.64 |
| 2026-08-30 | not found | 1.49 |

Revenue CAGR from the first to last year is **7.51%**.

| Investor | Check | COST result |
| --- | --- | --- |
| Buffett | ROE at least 15% every year | pass |
| Buffett | Owner earnings positive every year | pass |
| Buffett | Owner earnings grew from first to last | pass |
| Cathie Wood | Revenue CAGR at least 15% | fail |
| Cathie Wood | Latest R&D at least 5% of revenue | not known |
| Burry | Operating cash flow at least net income every year | pass |
| Burry | Latest liabilities no greater than twice equity | pass |

Buffett passes all three checks; Wood fails the growth hurdle with R&D unknown;
Burry passes both checks. Costco's missing R&D is not interpreted as zero
spending or evidence that it never innovates. The historical leverage ratio
of 2.11 does not fail a check explicitly defined on the latest year.

The [computed COST report](data/lab19/COST_output.md) contains the complete
financial table, checks and filing ledger. The memos are
[Buffett](docs/lab19/COST_buffett.md), [Wood](docs/lab19/COST_wood.md) and
[Burry](docs/lab19/COST_burry.md).

## Probe — A threshold is a design choice

I tested the assigned change by temporarily overriding `GROWTH_MINIMUM` inside
the Wood skill module from `0.15` to `0.05`. The original rule was restored
after the run; the SEC facts and their fingerprint were identical.

| Wood check on COST | Retained 15% growth rule | Probe at 5% |
| --- | --- | --- |
| First-to-last annual revenue growth | fail | pass |
| Latest R&D intensity | not known | not known |

The [probe report](data/lab19/COST_growth_probe_output.md) and
[verification record](data/lab19/verification.json) preserve the result.
The app also exposes this change through its threshold selector and warns that
the saved memos were written under different thresholds. Returning the selector
to 15% restores the original panel.

**Threshold retained:** I retain 15% annual revenue growth because the purpose
is to apply the stated innovation screen consistently, rather than relax it
after observing a company I want to pass. This line also appears under Wood's
memo. Lowering a threshold changes the judgment rule, not Costco's business.

## My company — NVIDIA inside VT

I selected **VT**, the Vanguard Total World Stock ETF, from my existing Project 2
fund universe. Vanguard's disclosed holdings as of **September 30, 2026** identify
**NVIDIA (NVDA)** as the largest equity holding at **4.52%**. I used the issuer's
public holdings data, ranked the reported equity positions by dollar market
value, and retained the source URL, download timestamp, response digest and
largest positions in [fund_selection.json](data/lab19/fund_selection.json).
The [selection script](select_lab19_company.py) reproduces that choice.

NVIDIA has annual `10-K` facts on EDGAR, so no next-largest-company substitution
was necessary. Its panel uses the fiscal years ending January 30, 2022 through
January 25, 2026. See the [complete NVDA report](data/lab19/NVDA_output.md).

| Investor | Check | NVDA result |
| --- | --- | --- |
| Buffett | ROE at least 15% every year | pass |
| Buffett | Owner earnings positive every year | pass |
| Buffett | Owner earnings grew from first to last | pass |
| Cathie Wood | Revenue CAGR at least 15% | pass — 68.30% |
| Cathie Wood | Latest R&D at least 5% of revenue | pass — 8.57% |
| Burry | Operating cash flow at least net income every year | fail |
| Burry | Latest liabilities no greater than twice equity | pass — 0.31 |

Buffett and Wood give positive business-screen judgments. Burry stays on watch
because cash conversion fails despite the leverage pass. In the latest year,
operating cash flow is $102,718 million versus net income of $120,067 million.
The cash check also fails in fiscal years ending January 30, 2022, January 28,
2024 and January 26, 2025. The shortfalls warrant investigation; they do not
by themselves establish accounting manipulation.

The company memos are [Buffett](docs/lab19/NVDA_buffett.md),
[Wood](docs/lab19/NVDA_wood.md), and [Burry](docs/lab19/NVDA_burry.md).
Every memo uses only printed numerical values, and each is bound to both the
facts fingerprint and the threshold-dependent analysis fingerprint.

## Explain the code — Written analysis

The relevant function is `evaluate()` in the Wood skill's `scripts/wood.py`.

1. `threshold` selects the skill's retained growth minimum unless a deliberate
   probe value is passed to the function.
2. `latest = rows[-1]` selects the most recent fiscal end from chronologically
   ordered rows; it does not use an arbitrary filing's fiscal-year label.
3. `growth` becomes `not known` when the shared engine cannot compute a valid
   revenue CAGR. Otherwise it compares the calculated rate with the threshold
   using `>=`, so an exact boundary passes.
4. `rd` reads the latest calculated R&D/revenue ratio.
5. `innovation` becomes `not known` if that ratio is missing or undefined;
   otherwise it compares the ratio with `RD_MINIMUM`.
6. The return value contains named checks with the investor, threshold and
   pass/fail/not-known status. The model does not supply these statuses.

**What happens when an input is missing?** If annual R&D is not reported under
the permitted tag, its raw value and derived ratio stay missing. The function
returns `not known` for the intensity check instead of substituting zero, while
the separately supported growth check can still pass or fail.

This is a written explanation; I did not perform the no-AI oral demonstration.

## Bull and bear — Written analysis

**Bull case:** NVIDIA passes Buffett's profitability and owner-earnings checks
and Wood's growth and R&D checks, with historical revenue CAGR of 68.30% and
latest R&D intensity of 8.57%. Owner earnings rise from $8,132 million to $96,676
million, supporting further research into whether that earning power can endure.

**Bear case:** Burry's cash-conversion check fails, including the latest year's
$102,718 million operating cash flow against $120,067 million net income.
The growth and profitability passes therefore do not settle cash realization
or valuation, so I would investigate the reconciliation before allocating capital.

These are opposing arguments I prepared from the same panel. I did
not conduct a partner exchange, and neither argument is attributed to a partner.

## My decision

**Only with a condition:** I would use the panel to prioritize Project 2 research
only if every retained result has traceable annual facts, unknowns remain
unknown, and I investigate NVIDIA's failed cash-conversion check before any
allocation; the panel cannot override my portfolio mandate or establish price.

## A panel of AI agents — Learning answers

**What is it?** A panel applies several named analytical perspectives to a
common evidence set, then makes their agreements, disagreements and limitations
visible together. Here each perspective has a skill, deterministic checks and
a separate memo.

**How does it work, and why disagree?** The shared script selects the data once.
Each skill evaluates a different rule, then the AI interprets those results.
Wood can favor rapid revenue growth while Burry objects to cash conversion,
without either using different annual facts. Their disagreement reveals
different criteria; it is not resolved by counting favorable personas.

**My explanation of the design:** I separate source selection, arithmetic and
judgment. This makes a disagreement inspectable: I can identify the specific
threshold, missing fact or failed condition rather than rely on the confidence
of a persona's prose. These are simulated perspectives using common data and
AI assistance, not independent endorsements from the named investors.

## Reflect

**Where did the panel agree and split on NVIDIA?** Buffett and Wood both support
further business-quality research; Burry agrees that latest leverage clears the
cap but rejects consistent cash conversion. Positive owner earnings and cash
flow below net income can coexist because they compare different quantities.
The panel exposes that distinction instead of hiding the weak check inside a
single average score.

**What does the threshold probe say about a screen's verdict?** Costco's growth
check changes from fail to pass with identical financial facts when I lower the
hurdle. A verdict therefore depends on a chosen policy as well as on data. I
should state and retain the threshold before choosing companies and report
sensitivity rather than treat the screen as an objective investment truth.

## Verification

```sh
source .venv/bin/activate
python verify_lab19.py
python verify_lab18.py
```

The tests cover the current known answer, the original Buffett values, NVIDIA's
disagreement, missing data and invalid denominators, exact threshold boundaries,
the restored growth rule, issuer-holdings selection, all six memo fingerprints,
and interactive Streamlit behavior. Each of the three memo editors was tested
with an unsupported `40.0%`; both the individual flag and panel-wide flag
identified it, and the error cleared when the original text was restored.

Results are saved in [verification.json](data/lab19/verification.json) and the
[executed test log](data/lab19/verification_output.txt). The known-answer constants
are test expectations only; neither the app nor the data engine imports them.
No additional Python package was installed for this lab.

The number flag checks that a numeric value was printed with its type and
rounding. It cannot prove a sentence assigned the value to the right metric
or that its interpretation is sound. The source ledger and memo review still
matter. Saved data are historical snapshots; a deliberate refresh can change
which filings or values are selected.

## Run and checkout

```sh
source .venv/bin/activate
python -m streamlit run legend_panel_app.py
```

The app starts with COST. Enter NVDA for my company run. It shows the chart,
annual table, investor-by-check panel, screen summaries, memo verdicts, three
memos side by side and the number flags. The original `buffett_app.py` also has
a **Show Lab 19 investor panel** option; its Lab 18 view is preserved.

The code can be reproduced without another network request:

```sh
python legend_panel.py COST --offline
python legend_panel.py NVDA --offline
python legend_panel.py COST --offline --growth-minimum 0.05
python .agents/skills/wood-business/scripts/wood.py COST --offline
python .agents/skills/burry-business/scripts/burry.py NVDA --offline
```

Live downloads use the existing ignored SEC contact configuration. A first run
for another ticker downloads its SEC facts; `--refresh` deliberately replaces
an existing snapshot. No API key is needed. I have not submitted a Brightspace
quiz in this session.

The checkout artifacts are this write-up, the two new skills and their scripts,
the shared engine and panel app, both companies' SEC snapshots and reports,
the six memos, the holdings-selection evidence and the verification record.

GitHub checkout links:

- [This write-up](https://github.com/Mrigna01/FIN439Project2/blob/main/lab19.md)
- [Panel app](https://github.com/Mrigna01/FIN439Project2/blob/main/legend_panel_app.py),
  [display code](https://github.com/Mrigna01/FIN439Project2/blob/main/legend_panel_ui.py),
  and [shared calculations](https://github.com/Mrigna01/FIN439Project2/blob/main/legend_panel.py)
- [Investor skills and bundled scripts](https://github.com/Mrigna01/FIN439Project2/tree/main/.agents/skills)
- [Company memos](https://github.com/Mrigna01/FIN439Project2/tree/main/docs/lab19)
- [SEC facts, computed results, fund selection and verification evidence](https://github.com/Mrigna01/FIN439Project2/tree/main/data/lab19)
- [Verification script](https://github.com/Mrigna01/FIN439Project2/blob/main/verify_lab19.py)

## Sources

- [Controlling Lab 19 revision](https://github.com/CinderZhang/FIN43900-Fall2026/blob/c4ad923d058d5250a237de56db26dfa99dbf87f6/lessons/week-11/lab-19-legend-panel.md).
- [Wood's assigned philosophy](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/cathie_wood.md),
  [Burry's assigned philosophy](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/michael_burry.md),
  and [Buffett's assigned philosophy](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/warren_buffett.md).
- [Vanguard's VT holdings page](https://advisors.vanguard.com/investments/products/vt/vanguard-total-world-stock-etf)
  and its [public holdings data](https://investor.vanguard.com/irr/funds/profile/3141-AdditionalFundData).
- [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces),
  [COST annual facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000909832.json),
  and [NVDA annual facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json).
