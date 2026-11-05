# Lab 18 — Legend Investor as Skill

AI use: Codex created the skill, scripts, app, tests, memos and draft written
responses. Financial facts were downloaded from SEC EDGAR and the numbers were
computed in Python. The written decisions below are AI-assisted drafts, not
evidence of an independent student explanation or a partner conversation.
Built with AI help, a learning demonstration, not investment advice.

## D — The question

**Can an investor's philosophy become a skill the AI runs the same way every
time, with every number computed from annual filings and judgment left to the
model?**

The measurable part can. This skill always applies the same fact-selection
rules, formulas and Buffett checks. The memo then interprets the printed
results. The skill does not turn a limited accounting screen into a complete
version of Buffett's judgment: the durability of an advantage and management's
quality are not proved by passing the financial checks.

## R — What belongs in code and what requires judgment

Code computes ROE, the lab's owner-earnings proxy, whether each annual figure
meets its threshold, and whether owner earnings rose between the first and last
years. Assessing whether a competitive advantage can persist requires judgment
and evidence beyond this table. The quantitative pass is a reason to investigate,
not proof that a moat exists.

The skill adapts the philosophy in
[FAskills' Buffett page](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/warren_buffett.md).
It does not install that repository or use its paid sources. The lab's narrower
instructions control: owner earnings are operating cash flow minus reported
capital spending; no estimated maintenance spending, price targets, forecasts,
or valuation are added.

The script follows these rules:

- Only USD facts from `10-K` filings with an annual fiscal-period designation.
- The most recent five annual net-income period ends identify the years. The
  period's end date is the label; a comparative fact's `fy` field is not used as
  the year label.
- Flow periods must span 350–380 elapsed days. This includes retail fiscal
  calendars with fifty-two or fifty-three weeks and excludes quarterly flows.
- For each required tag and period, the latest filing wins. Conflicting values
  in the latest filing cause an error rather than an arbitrary choice.
- Revenue uses `RevenueFromContractWithCustomerExcludingAssessedTax`, falling
  back to `Revenues`. Capital spending uses
  `PaymentsToAcquirePropertyPlantAndEquipment`, falling back to
  `PaymentsToAcquireProductiveAssets`. A fallback is used only when the earlier
  tag has no eligible value for that period.
- ROE is `NetIncomeLoss / StockholdersEquity`, using year-end equity.
- Owner earnings are `NetCashProvidedByUsedInOperatingActivities` minus the
  selected capital-spending fact.
- Missing raw facts print `not found`. ROE with missing or nonpositive equity
  is `not known`. A check with a missing required input is `not known`.

## I — The skill, app and run commands

The repository skill lives at
[.agents/skills/buffett-business/SKILL.md](.agents/skills/buffett-business/SKILL.md),
in the repository location described by the
[official Codex skills documentation](https://developers.openai.com/codex/skills).
It bundles [the SEC downloader and calculation script](.agents/skills/buffett-business/scripts/buffett.py).
Invoke it in Codex with `$buffett-business` and a ticker.

From the repository root:

```sh
source .venv/bin/activate
python .agents/skills/buffett-business/scripts/buffett.py COST --offline
python .agents/skills/buffett-business/scripts/buffett.py JPM --offline
python -m streamlit run buffett_app.py
```

The saved snapshots allow reproduction without a new request. To fetch a new
ticker, run the script without `--offline`. To intentionally replace an existing
snapshot, add `--refresh`. The app has the same deliberate refresh button and
shows the download timestamp. A network failure produces an error, not a table
of apparently missing financial facts.

Live downloads send the caller's real name and contact email as SEC's User-Agent.
This Mac's contact is in `.sec-user-agent`, which is ignored by Git. On another
computer, set `SEC_USER_AGENT` to your own name and email, or create that local
file. No API key or paid service is required. No additional package was installed
for this lab; the app uses the existing Streamlit environment.

The app shows the owner-earnings and net-income chart, the full annual table,
the three checks, a filing/tag ledger, and an editable memo with an unsupported
number flag. Memo edits in the app are temporary unless downloaded and saved.
The saved memo's fingerprint warns if the underlying facts have changed.

## V — Costco's known answer

The SEC download on November 5, 2026 reproduces **every value in the professor's
Costco table** for fiscal year ends August 28, 2022 through August 30, 2026.
See the [complete computed table and source ledger](data/lab18/COST_output.md).
The known-answer table appears only in the verification script as an independent
test expectation; it is not used to populate the app or calculations.

| Buffett check | Computed result |
| --- | --- |
| ROE at least 15.0% every year | pass |
| Owner earnings positive every year | pass |
| Owner earnings grew from first to last year | pass |

For example, the latest year's ROE is `9,226 / 35,803 = 25.8%` after rounding.
Owner earnings are `15,817 - 6,435 = 9,382` million dollars. First-year owner
earnings are `7,392 - 3,891 = 3,501` million dollars. These are calculations from
the selected reported facts, not estimates supplied by the model.

**Important interpretation:** owner earnings fell from $6,745 million to $6,629
million in the middle of the period. The first-to-last growth check still passes;
it does not mean owner earnings rose every year.

The [COST memo](docs/lab18/COST_buffett.md) says **own the business**, conditional
on treating the result as a business-quality screen rather than a conclusion
about price. Every number in the memo passes the number check.

## V — Probes

| Probe | Actual observed result | Evidence |
| --- | --- | --- |
| Run JPM through the same script | Capital spending and owner earnings are `not found` in every year; both owner-earnings checks are `not known`. The ROE-every-year check fails. | [JPM output](data/lab18/JPM_output.md), [JPM memo](docs/lab18/JPM_buffett.md) |
| Add `40.0%` to the COST memo in the app | The app shows `Unprinted number(s): 40.0%`. Restoring the original memo clears the error. | `test_edit_probe_and_restore` in [the executed test log](data/lab18/verification_output.txt) |
| Ask a fresh browser AI with no skill for Costco's annual ROEs | **Not performed.** This chat already contains the skill and the known answer, and is not an independent browser comparison. | No browser response is claimed. |

The JPM memo explicitly says it cannot judge owner earnings. It does not use
zero or another cash-flow measure as a replacement for missing capital spending.

The unsupported-number test establishes numeric provenance only. It cannot
detect every misleading sentence: attaching a real printed number to the wrong
year or metric still needs human review. Percentages and ordinary amounts are
checked as distinct units. Dates must match a displayed fiscal end.

## Verification and source record

Run:

```sh
python verify_lab18.py
```

The checks cover the complete COST known answer, JPM's gaps, memo numbers and
fingerprints, annual-period filtering, comparative-year labels, latest-filing
selection, tag fallbacks, nonpositive equity, insufficient history, conflicting
facts, and Streamlit interactions. Results are saved in
[verification.json](data/lab18/verification.json) and
[verification_output.txt](data/lab18/verification_output.txt).

The bundled skill's simple frontmatter and script are checked using the standard
library. The skill-creator's optional validator requires PyYAML, which is not
installed; no package was added solely to run that validator.

The [COST](data/lab18/COST_facts.json) and [JPM](data/lab18/JPM_facts.json)
snapshots contain unmodified relevant fact records selected from the SEC JSON,
with their original filing metadata. Each records the source URL, download time,
and SHA-256 digest of the complete HTTP response before filtering. The snapshots
omit unrelated tags; calculated reports are regenerated from the retained facts.
Later refreshes can change historical values or filing selections.

Sources: [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces),
[COST company facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000909832.json),
[JPM company facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000019617.json),
and [the controlling Lab 18 instructions](https://github.com/CinderZhang/FIN43900-Fall2026/blob/main/lessons/week-11/lab-18-legend-investor-as-skill.md).

## Decision — drafted response

I trust the COST verdict as a reproducible business-quality screen because each
number has a filing source and the checks reproduce the known answer. I would
not use the verdict alone to invest: accounting returns and this simplified
owner-earnings proxy do not establish a durable moat or an attractive price.

## Agent skills — drafted learning answers

**What is an agent skill?** A reusable folder of task instructions, identified
by a name and description, with optional scripts or references. Here it packages
the Buffett screen's data rules and a deterministic financial script.

**Why read the name and description first?** They let the AI decide whether the
skill fits the request without loading every skill's full instructions. It loads
the detailed instructions and script only when the task calls for them.

**Why do the numbers belong in code?** Code applies explicit rules to reported
facts, performs the arithmetic consistently, and leaves an auditable trail.
The model can explain the output, but its confidence or prose is not a financial
source. A program can still be wrong, which is why the known answer and changed
inputs are tested.

## Reflect — drafted answers

**What stays the same, and what remains judgment?** Fact selection, formulas,
missing-data rules and checks stay the same for the same snapshot. Deciding
whether the business deserves further investigation remains judgment; different
memos can interpret the same results differently without changing the numbers.

**Why prefer `not found` to an estimate?** It separates what the permitted source
supports from what is unknown. An estimated capital-spending value would create
an apparently computed owner-earnings result and could turn an unsupported check
into a false pass. JPM is the concrete example.

## Code explanation — study notes, not a completed AI-off exercise

The function to open is `year_row()` in the bundled script:

1. `selected` calls `pick_fact()` for every required raw metric and the chosen
   fiscal end. Each result keeps the value, tag and source record.
2. `values` extracts the numeric values without discarding `None` for missing
   facts.
3. `income, equity` names the inputs to ROE.
4. The conditional division computes ROE only when income is present and equity
   is present and positive. Otherwise the result is `None`.
5. `cash, capex` names the inputs to owner earnings.
6. The subtraction happens only when both inputs exist. Missing spending is not
   treated as zero.
7. The returned row combines the fiscal end, numeric and derived values, and the
   complete selected source records.

Where does `not found` come from? `pick_fact()` returns `None` when neither
permitted tag has an eligible fact. `display_value()` converts a missing raw
value or owner-earnings result to `not found`; it displays an undefined ROE as
`not known`. The numeric computation never uses these strings in arithmetic.

## Completion status and checkout

The skill, SEC script, COST and JPM runs, app, memos, automated number probe, and
draft written answers are complete locally. No partner conversation, no-AI
explanation, separate browser-AI response, Brightspace quiz,
or course submission is claimed. Partner work was intentionally left unperformed.

The browser-AI probe remains an actual exercise to do in a fresh browser chat:
ask the prompt in the lab, preserve its answer, and compare its numbers and
sources with the printed table. These notes are not a substitute for that run.

GitHub checkout links:

- [This write-up](https://github.com/Mrigna01/FIN439Project2/blob/main/lab18.md)
- [Buffett skill and bundled script](https://github.com/Mrigna01/FIN439Project2/tree/main/.agents/skills/buffett-business)
- [App](https://github.com/Mrigna01/FIN439Project2/blob/main/buffett_app.py)
- [Memos](https://github.com/Mrigna01/FIN439Project2/tree/main/docs/lab18)
- [SEC facts, results and verification evidence](https://github.com/Mrigna01/FIN439Project2/tree/main/data/lab18)
- [Verification script](https://github.com/Mrigna01/FIN439Project2/blob/main/verify_lab18.py)

The local commands above are ready to demonstrate the application.
