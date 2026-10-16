# Lab 13 — Portfolio Mandate Defense

Student: Mrigna

[Assignment](https://github.com/CinderZhang/FIN43900-Fall2026/blob/main/lessons/week-08/lab-13-portfolio-mandate.md) · [Required IPS reading](https://github.com/CinderZhang/FIN43900-Fall2026/blob/main/lessons/week-08/student-prework.md)

Status: The AI-assisted checker and verification are complete. Sections marked **Student completion required** remain unfinished; they are not claims of independent student work.

## D — Common-case question

Which of these portfolios does the Meridian Foundation's mandate permit — and what must the CIO answer before anyone optimizes?

A passes every rule checked by the requested program. B fails three rules; C fails one. This is not full mandate approval: the calendar-year loss statement remains undefined, the optimization objective is missing, and a snapshot cannot establish return performance, annual turnover, or rebalancing compliance.

## R — Sort before building; map into an IPS

**Student completion required, without AI:** Fill in a type and one-line reason for each statement. Use objective, hard constraint, preference, unverifiable promise, or missing. In the last column, identify where it belongs in an investment policy statement. The assignment requests this exercise before building; the checker has already been produced, so do not claim that sequence was followed.

| Statement | Type | One-line reason | IPS role |
|---|---|---|---|
| S1: Horizon seven years; annual rebalancing. | TODO | TODO | TODO |
| S2: CPI + 4% a year, net of costs, over rolling five-year periods. | TODO | TODO | TODO |
| S3: $0.75 million quarterly payouts; twelve months held in cash or daily-liquid government securities. | TODO | TODO | TODO |
| S4: Benchmark is 60% global equities, 40% U.S. investment-grade bonds. | TODO | TODO | TODO |
| S5: Long-only; no borrowing, short sales, or derivatives. | TODO | TODO | TODO |
| S6: No single issuer above 8%. | TODO | TODO | TODO |
| S7: Annual turnover at most 25% without committee approval. | TODO | TODO | TODO |
| S8: At least 90% redeemable within five business days. | TODO | TODO | TODO |
| S9: No calendar-year loss greater than 10%; no measure or breach rule. | TODO | TODO | TODO |
| S10: No sector, ESG, tax, or home-bias preference; pilot optimization target unspecified. | TODO | TODO | TODO |

## I — Run and understand the checker

The standard-library-only implementation is [mandate.py](mandate.py). Inputs are editable at the top. Weights use percentage units; reserve amounts use USD millions.

```sh
python mandate.py
```

The reserve minimum is computed as `4 * 0.75 / 100 * 100 = 3.0%`. The checker uses the supplied eligibility table, including the Treasury 10-year note as reserve-eligible. It aggregates securities by company and excludes cash, Treasury, and diversified funds from the issuer cap. It never tests S9.

**Student completion required:** Read and run the code. Identify the line you understand least, answer an AI quiz question about it before receiving an explanation, and record the exchange here.

- Proposed quiz line: `companies[issuer] = companies.get(issuer, 0) + weights[name]`
- Question: What value does Acme end with in B, and why? Choose a different line if this is not the one you understand least.
- Student answer: TODO
- Explanation after the student answers: Pending

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

**Student completion required, AI closed:** Write two sentences deciding whether that objection holds and naming the statement that decides it.

TODO

**Student completion required:** Play the sceptical colleague role, as instructed for this solo lab, and name the statement you would cite against D.

TODO

## One question for the CIO

**Student completion required, AI closed:** Write exactly one question that must be answered before optimization, then specify an answer that would change your portfolio design.

- Question: TODO
- Answer and resulting design change: TODO

## Investment policy statement

An investment policy statement (IPS) is a written agreement about the purpose, objectives, limits, responsibilities, and review process for managing an investment portfolio. Objectives describe intended outcomes; constraints restrict the investments or actions permitted while pursuing them. A benchmark provides a reference for evaluation. Monitoring and breach procedures specify how compliance is reviewed and what happens when limits are exceeded.

For this lab, the numerical checker tests only the constraints measurable from the supplied holdings and weights. A full IPS also needs operational rules and a clear interpretation of risk and objectives. Complete the S1–S10 mapping in the table above after doing the assigned reading.

## Reflect

**Student completion required:** Explain these aloud in both roles, then write your own responses.

1. Why can a portfolio pass every checkable rule and still be wrong for this client? TODO
2. Which S1–S10 classification were you least sure of, and why? TODO

## Project 2 — Proposed own-client mandate

AI-assisted draft for a fictional client, subject to student adoption; these are proposed case assumptions, not supplied facts about an actual client.

Client: Campus Scholarship Reserve, a fictional $1 million fund with a seven-year horizon.

- **Objective:** Seek CPI + 3% annually, net of costs, over rolling five-year periods while supporting scholarship payments.
- **Hard constraints:** Long-only, fully invested weights totaling 100%; no borrowing, short sales, or derivatives. Pay $10,000 quarterly and maintain at least $40,000 (4% of the initial reserve) in cash or daily-liquid government securities, recalculated as a portfolio percentage at review. At least 90% must be redeemable within five business days. Cap aggregate securities of each company at 8%, exempting cash, U.S. Treasury securities, and diversified funds. Rebalance annually; annual turnover above 25% requires committee approval. Use the Lab 13 holding universe for the pilot.
- **One client question:** Should the pilot minimize estimated volatility subject to a modeled CPI + 3% net return target, or maximize expected net return subject to a separately agreed risk limit?

This question must be resolved before optimization; the return target is an objective, not a guarantee.

## Checkout remaining

Complete the marked student sections, read the assigned IPS material, finish the code quiz, and adopt or revise the proposed Project 2 client. Commit and push those edits. Paste the GitHub links to this Markdown file and `mandate.py` into the Lab 13 quiz. Attend the guest talk as instructed by the course.
