# Lab 13 — Portfolio Mandate Defense

Student: Mrigna

[Assignment](https://github.com/CinderZhang/FIN43900-Fall2026/blob/main/lessons/week-08/lab-13-portfolio-mandate.md) · [Required IPS reading](https://github.com/CinderZhang/FIN43900-Fall2026/blob/main/lessons/week-08/student-prework.md)

Authorship note: This is an AI-assisted worked response, including the written analysis and sample quiz answer. The checker was executed and verified. This document does not claim that the AI-closed exercises, personal reflection, or live quiz exchange were completed independently by the student.

## D — Common-case question

Which of these portfolios does the Meridian Foundation's mandate permit — and what must the CIO answer before anyone optimizes?

A passes every rule checked by the requested program. B fails three rules; C fails one. This is not full mandate approval: the calendar-year loss statement remains undefined, the optimization objective is missing, and a snapshot cannot establish return performance, annual turnover, or rebalancing compliance.

## R — Sort before building; map into an IPS

The table separates the outcome the client wants from the rules that limit the portfolio. Some rules need information beyond the holdings snapshot to check them.

| Statement | Type | One-line reason | IPS role |
|---|---|---|---|
| S1: Horizon seven years; annual rebalancing. | Hard constraint | These set the planning horizon and required review schedule, although weights alone cannot show compliance. | Time horizon and rebalancing policy |
| S2: CPI + 4% a year, net of costs, over rolling five-year periods. | Objective | This states the desired real return and evaluation period, not a guaranteed outcome. | Return objective |
| S3: $0.75 million quarterly payouts; twelve months held in cash or daily-liquid government securities. | Hard constraint | Four payouts require $3 million of eligible reserves, or 3% of the current portfolio. | Spending needs and cash reserve |
| S4: Benchmark is 60% global equities, 40% U.S. investment-grade bonds. | Preference | Of the available labels, this best describes the chosen comparison standard; it does not require matching those weights. | Performance benchmark |
| S5: Long-only; no borrowing, short sales, or derivatives. | Hard constraint | These are explicit restrictions on positions and instruments. | Permitted investments and leverage restrictions |
| S6: No single issuer above 8%. | Hard constraint | Company exposures must be added together and kept within the cap, with the stated exemptions. | Issuer concentration limit |
| S7: Annual turnover at most 25% without committee approval. | Hard constraint | Trading above the limit requires approval; checking it needs trading history and a turnover definition. | Trading limits and approval authority |
| S8: At least 90% redeemable within five business days. | Hard constraint | This gives a measurable minimum liquid share and redemption window. | Liquidity requirement |
| S9: No calendar-year loss greater than 10%; no measure or breach rule. | Unverifiable promise | The wording promises an outcome without defining how to measure risk or respond to a breach. | Risk policy requiring clarification |
| S10: No sector, ESG, tax, or home-bias preference; pilot optimization target unspecified. | Missing | No extra preferences are imposed, but the quantity the pilot should optimize has not been chosen. | Optimization decision still needed |

## I — Run and understand the checker

The standard-library-only implementation is [mandate.py](mandate.py). Inputs are editable at the top. Weights use percentage units; reserve amounts use USD millions.

```sh
python mandate.py
```

The reserve minimum is computed as `4 * 0.75 / 100 * 100 = 3.0%`. The checker uses the supplied eligibility table, including the Treasury 10-year note as reserve-eligible. It aggregates securities by company and excludes cash, Treasury, and diversified funds from the issuer cap. It never tests S9.

Sample code quiz, provided as a worked example rather than a completed student exchange:

- Line: `companies[issuer] = companies.get(issuer, 0) + weights[name]`
- Question: What value does Acme end with in B, and why?
- Sample answer: Acme ends with 9 because the portfolio holds 5% in its bonds and 4% in its stock. The limit applies to the company, so checking the two holdings separately would miss the breach.
- Explanation: `get(issuer, 0)` returns the company's running total, starting at zero if it has not appeared yet. Each holding adds its weight to that same company's total. The final total is then compared with the 8% limit.

## V — Verification evidence

Executed `python mandate.py`; all A–C values and verdicts match the assignment. The table below records the measured results, also checked with assertions against the known answer.

| Rule | A | B | C | D |
|---|---|---|---|---|
| Weights sum to 100 | 100.0 pass | 100.0 pass | 100.0 pass | 100.0 pass |
| Long-only: lowest weight | 0.0 pass | 0.0 pass | 0.0 pass | 0.0 pass |
| Reserve >= 3.0% | 14.0 pass | 1.0 FAIL | 2.0 FAIL | 100.0 pass |
| Redeemable in 5 days >= 90% | 100.0 pass | 85.0 FAIL | 100.0 pass | 100.0 pass |
| Largest single company <= 8% | 0.0 pass | 9.0 FAIL | 8.0 pass | 0.0 pass |
| Calendar-year loss | requires CIO clarification | requires CIO clarification | requires CIO clarification | requires CIO clarification |
| Verdict | passes every checkable rule | fails 3 rule(s) | fails 1 rule(s) | passes every checkable rule |

Probe executed: temporarily changed A's Cash to -2 and Global equity index fund to 64, ran the script, and then restored the original inputs. A's results were total 100.0 pass, lowest weight -2.0 FAIL, reserve 10.0 pass, five-day liquidity 100.0 pass, and largest company 0.0 pass. Its verdict was `fails 1 rule(s)`. Assertions confirmed that long-only was the only failure. Original A is restored in the submitted script.

## E — Attack the checker

AI proposal, not an optimized portfolio: D holds 100% Cash and 0% of every other permitted holding. D is included in the script and was run successfully; its measured values appear above.

AI objection: S2 gives a CPI + 4% net return objective over rolling five-year periods. Passing the cash, liquidity, issuer, and weight checks provides no evidence that an all-cash allocation can achieve that objective. The CIO could reasonably reject D on that basis; no future cash return or guaranteed failure is assumed.

Two-sentence judgment: The objection holds as a reason to question suitability, because passing the checker does not show that 100% cash can support the client's return target. S2 decides the objection: the target is CPI + 4% net of costs over rolling five-year periods, although the information supplied does not prove that D will miss it.

Sceptical colleague perspective: I would also cite S2 against D and ask for evidence that its expected net real return supports the target. I would not reject it just for differing from S4's benchmark, since the benchmark is not an exact allocation requirement.

## One question for the CIO

- **Question:** Given S2's return target and the need to clarify S9 separately, should the pilot minimize estimated volatility subject to that modeled return target, or minimize tracking error relative to the 60/40 benchmark?
- **Answer and resulting design change:** If the CIO chooses minimum estimated volatility subject to the return target, I would compare feasible allocations by their modeled volatility and allow departures from the benchmark. If the CIO instead chooses minimum tracking error, I would favor allocations that behave more like the 60/40 benchmark while still meeting the hard constraints. S10 leaves this choice open; the objectives could lead to different portfolios, so I would not choose one silently. S9 still needs an agreed measure and breach procedure before the resulting portfolio can receive full mandate approval.

## Investment policy statement

An investment policy statement (IPS) is a written agreement about the purpose, objectives, limits, responsibilities, and review process for managing an investment portfolio. Objectives describe intended outcomes; constraints restrict the investments or actions permitted while pursuing them. A benchmark provides a reference for evaluation. Monitoring and breach procedures specify how compliance is reviewed and what happens when limits are exceeded.

For this lab, the numerical checker tests only the constraints measurable from the supplied holdings and weights. A full IPS also needs operational rules and a clear interpretation of risk and objectives. The S1–S10 table maps the horizon, return goal, liquidity needs, benchmark, investment restrictions, oversight rules, and unresolved decisions into those parts of an IPS.

## Reflect

1. **Why can a portfolio pass every checkable rule and still be wrong for this client?** The checker establishes whether the supplied weights satisfy a few measurable limits. It does not establish that the portfolio will earn the required return or fit the client's risk expectations. D makes this clear: cash passes the limits, but the return objective still needs a defensible investment plan. The checker also cannot establish annual turnover or rebalancing compliance from one set of weights.
2. **Classification that needs the most judgment — sample reflection:** S4 is the hardest to place among the five labels. A benchmark sounds like an allocation rule, but the statement only identifies a comparison portfolio. Preference is the closest available label, with the qualification that an IPS would normally give the benchmark its own role. Treating it as a hard requirement to hold exactly 60/40 would add a restriction the CIO did not state.

## Project 2 — Proposed own-client mandate

AI-assisted mandate for a fictional client; these are chosen case assumptions, not supplied facts about an actual client.

Client: Campus Scholarship Reserve, a fictional $1 million fund with a seven-year horizon.

- **Objective:** Seek CPI + 3% annually, net of costs, over rolling five-year periods while supporting scholarship payments.
- **Hard constraints:** Long-only, fully invested weights totaling 100%; no borrowing, short sales, or derivatives. Pay $10,000 quarterly and maintain at least $40,000 (4% of the initial reserve) in cash or daily-liquid government securities, recalculated as a portfolio percentage at review. At least 90% must be redeemable within five business days. Cap aggregate securities of each company at 8%, exempting cash, U.S. Treasury securities, and diversified funds. Rebalance annually; annual turnover above 25% requires committee approval. Use the Lab 13 holding universe for the pilot.
- **One client question:** Should the pilot minimize estimated volatility subject to a modeled CPI + 3% net return target, or maximize expected net return subject to a separately agreed risk limit?

This question must be resolved before optimization; the return target is an objective, not a guarantee.

## Checkout

- [Markdown submission](https://github.com/Mrigna01/FIN439Project2/blob/main/lab13.md)
- [Python submission](https://github.com/Mrigna01/FIN439Project2/blob/main/mandate.py)

The written responses and code are provided here. The course's independent-work activities, actual student quiz response, assigned reading, guest-talk attendance, and submission of links in the Lab 13 quiz cannot be certified by this document.
