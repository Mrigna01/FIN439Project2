# Lab 16 - Provenance Gate

## D - What could I actually know?

On March 31, 2026, the latest usable month in this training table is February for all three funds. The signals available then are AAA +1.98%, BBB -1.02% and CCC +0.91%. Using the latest data visible later gives different signals because it includes publications that had not happened yet.

The point is to separate the month a number describes from the date someone could have used it. A March observation published in April cannot support a March 31 decision just because its observation label says March.

## R - Inputs and timing

This lab uses the assignment's 12 fictional bond-fund records, not actual bond-market prices or the ETF prices from Lab 15. The original row number stays with each record. Inputs are editable at the top of [asof.py](asof.py), and the default decision date is `2026-03-31`.

Three dates or concepts matter:

- **Month measured:** the period described by a value, such as February 2026.
- **Publication date:** the day the value became available, such as March 10.
- **Revision:** a later publication for the same ticker and measured month, such as AAA's February value changing from 104 to 103 on March 25.

The current assignment includes the one-year zero-coupon bond interpretation and its sanity check. Source version used: [Lab 16 at commit 5e69701](https://github.com/CinderZhang/FIN43900-Fall2026/blob/5e6970110e86ea5487b1e0ec8eb9add94e44f8c6/lessons/week-10/lab-16-provenance-gate.md), retrieved October 27, 2026.

## I - Run the filter

```sh
python asof.py
```

The file uses only Python's standard library. It prints each rule's count and affected row numbers, the remaining panel, the as-of and naive signals, and a separate sanity check. No result is hardcoded into the calculations.

### What each function does

`provenance_gate()` makes copies of the records and applies the four rules in order. It records what happened to each row, rather than quietly deleting data. Quarantined means excluded from the usable panel but still identified for investigation.

`latest_publications()` groups rows by the pair `(ticker, month)`. It processes them in publication-date order, so a later admitted publication replaces an earlier one for that same pair. It keeps the row identifier and returns the identifiers of superseded rows.

`signals()` calculates `latest price / previous month's price - 1`. It reports the latest measured month and the two original row numbers used. It does not bridge a missing calendar month or invent a signal when there is insufficient history.

`sanity_check()` calculates `100 / price - 1` and checks the exercise's price-order assumptions. It is separate from the four-rule provenance gate, so the known-answer panel remains available for inspection.

`analyze()` brings the two comparisons together. The as-of path has a publication cutoff; the naive path cleans missing tickers and duplicates and selects the latest publication per month without a cutoff. The naive result is deliberately contaminated by later knowledge when viewed from March 31.

### Rule 4, line by line

```python
latest = {}
for row in sorted(rows, key=lambda item: (item['published'], item['row'])):
    key = (row['ticker'], row['month'])
    previous = latest.get(key)
    # The full function rejects conflicting values with the same publication date.
    latest[key] = row
```

The dictionary starts empty. Sorting puts older publications before newer ones. `key` identifies one fund and one measured month, so different months do not overwrite one another. `latest.get(key)` retrieves the previously retained publication, if there is one. Assigning to `latest[key]` replaces it with the later publication.

The date cutoff has already been applied before this function runs on the as-of path. That order matters: selecting the latest revision first and filtering dates afterward could throw away the later revision without recovering the older version that was actually knowable.

The full function refuses two different values with the same ticker, month and publication date, rather than pretending it knows which is correct. That is a structural ambiguity check; it is not used to change the supplied known answer.

## V - Results from the actual run

### Row funnel

| Step | Count excluded at this step | Original row numbers | Rows remaining |
|---|---:|---|---:|
| Starting table | 0 | All 12 | 12 |
| Quarantine missing ticker | 1 | 11 | 11 |
| Remove exact duplicate | 1 | 7 | 10 |
| Remove publication after March 31 | 3 | 3, 8, 10 | 7 |
| Replace older vintage | 1 | 2 | 6 |

An exact duplicate has the same ticker, measured month, publication date and price. The row identifier is excluded from the duplicate comparison, otherwise rows 6 and 7 would look different just because they have different row numbers. The earlier original row number is retained.

Every input row is accounted for exactly once: six excluded and six admitted.

### As-of panel

| Row | Ticker | Month measured | Published on | Price |
|---:|---|---|---|---:|
| 1 | AAA | 2026-01 | 2026-02-10 | 101.0 |
| 4 | AAA | 2026-02 | 2026-03-25 | 103.0 |
| 5 | BBB | 2026-01 | 2026-02-10 | 98.0 |
| 6 | BBB | 2026-02 | 2026-03-10 | 97.0 |
| 9 | CCC | 2026-01 | 2026-02-10 | 110.0 |
| 12 | CCC | 2026-02 | 2026-03-10 | 111.0 |

### Signals and calculations

| Ticker | As-of calculation | As-of signal | Naive calculation | Naive signal |
|---|---|---|---|---|
| AAA | 103 / 101 - 1 | +1.98%, February | 109 / 103 - 1 | +5.83%, March |
| BBB | 97 / 98 - 1 | -1.02%, February | 92 / 97 - 1 | -5.15%, March |
| CCC | 111 / 110 - 1 | +0.91%, February | 112 / 110 - 1 | +1.82%, February revised |

AAA and BBB's naive calculations use a later measured month as well as later publications. CCC's measured month stays February, but its value comes from an April 5 revision. This is why checking the measured month alone is not enough.

AAA's February revision was already available on March 31, so row 4 is the correct version. Keeping row 2 instead would calculate `104 / 101 - 1 = +2.97%`, which is not the latest knowable February result.

### Later-date test

```sh
python asof.py --decision-date 2026-04-15
```

| Ticker | April 15 as-of signal | Naive signal | Match? |
|---|---|---|---|
| AAA | +5.83%, March | +5.83%, March | Yes |
| BBB | -5.15%, March | -5.15%, March | Yes |
| CCC | +1.82%, February | +1.82%, February | Yes |

By April 15, every publication in this table has occurred. No rows fail the publication cutoff, and row 10 now replaces row 12. There are eight admitted ticker-month records. The command-line override changes this run only; the saved default remains March 31.

This was a local verification run on this repository's code. It was not a run of a partner's file.

## Sanity check - the hand calculation

For the exercise's one-year zero-coupon bonds, yield is `100 / price - 1`. The price change used as the signal and the yield to the assumed maturity are different calculations.

| Row | Fund and month | Hand calculation | Yield | Issue under the exercise's assumptions |
|---:|---|---|---:|---|
| 1 | AAA January | 100 / 101 - 1 | -0.99% | Negative yield |
| 4 | AAA February | 100 / 103 - 1 | -2.91% | Negative yield |
| 5 | BBB January | 100 / 98 - 1 | +2.04% | None of the stated rules |
| 6 | BBB February | 100 / 97 - 1 | +3.09% | None of the stated rules |
| 9 | CCC January | 100 / 110 - 1 | -9.09% | Negative yield; price above AAA and BBB |
| 12 | CCC February | 100 / 111 - 1 | -9.91% | Negative yield; price above AAA and BBB |

Rows 1, 4, 9 and 12 all arrived on time, but they fail the lab's economic checks. The proposed fifth rule is: **quarantine a positive price above 100 under this exercise's nonnegative-yield assumption, and flag a lower-rated bond priced at least as high as a comparable higher-rated bond.** Nonpositive prices would also be invalid for this yield calculation.

For these inputs, the fifth rule identifies rows 1, 4, 9 and 12. I would keep their row numbers and reasons, then investigate the source instead of inventing replacement prices. Applying that extra quarantine would leave only BBB's two rows, so AAA and CCC would no longer have signals supported by admitted prices.

This is a stated classroom assumption, not a universal claim that negative yields can never occur in real markets. Real credit-price comparisons also require comparable terms. The important result here is that a timing check does not establish economic plausibility.

## Point-in-time and look-ahead bias

Look-ahead bias happens when a historical decision uses information that became available only afterward. The event month tells me what the number describes. Publication time tells me when I could use it, and revisions mean that one event month can have several versions.

AAA shows the problem clearly. At March 31, the latest available prices are January's 101 and revised February's 103, giving +1.98%. March's 109 arrives on April 10. The naive +5.83% uses that later observation and acts as though I already had it on the decision date.

ALFRED preserves historical versions so a researcher can recover what a source reported at a past date. Its help explains that release dates come from the original source when possible, then data providers, and otherwise the date first available in FRED. Vintage values are checked against original sources where available or third-party services when older releases are unavailable. These distinctions matter because an archive timestamp and a source publication timestamp are not automatically interchangeable. [ALFRED Help](https://alfred.stlouisfed.org/help)

The API's real-time interval describes when information was known, with inclusive start and end boundaries. In this training table, `published` corresponds to the simplified `realtime_start` field, while `month` corresponds to the observation period. The comparison deliberately uses `published <= decision_date`, including a publication on the decision date. A real intraday trading study would also need release times and a trading cutoff. [FRED API real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html)

## Reflection

**Which rule removed the row that mattered most?** For the AAA example, rule 3 is the biggest protection because it removes row 3, the March price published in April. Without that rule, the backtest could use a +5.83% signal that did not exist on March 31. Rule 4 still matters: it replaces row 2 with row 4 so the permitted February signal is +1.98%, not +2.97%.

**What would a backtest using the naive column claim?** It would behave as if AAA's stronger March signal, BBB's weaker March signal and CCC's revised February signal were available at the March 31 decision. That gives the strategy future knowledge. It does not prove higher realized trading profits by itself, and not every individual signal becomes more positive, but any resulting decision would be based on an information set the trader did not have.

**What does the fifth rule add?** It asks whether an on-time value makes economic sense. The four provenance rules can correctly retain the six rows and still pass four planted price problems. I need both an availability check and a separate plausibility check.

**What does this mean for my Project 2 data?** The October 22 download date in my ETF source file establishes when that snapshot was collected. It does not prove those exact adjusted historical prices were available on every earlier decision date. Adjusted prices can be revised, so the Lab 15 sample-window comparison is a sensitivity exercise, not a point-in-time trading backtest. This lab's filter needs actual publication/vintage records before it can make that stronger claim for real data.

## Quiz and discussion answers

**Which February value should I keep for AAA on March 31? Why should I exclude March's 109?**

I keep 103, published on March 25, because it is the latest February revision available by my March 31 decision date. The earlier value of 104 was replaced before that date. I exclude March's 109 because it was published on April 10, after my decision. Using it would give my model information I could not have known at the time.

**How do I explain the measured month versus the publication date?**

I think of the measured month as the period the number describes and the publication date as the day I can start using it. A number about February might arrive in March or even April. I decide whether it belongs in my March 31 information set by checking when it was published, not just the month written beside it.

**How do I explain the revision-selection code?**

I first remove publications after my decision date. I then sort the remaining records by publication date and use `(ticker, month)` as the dictionary key. When I encounter a newer publication for the same key, I replace the older record. That lets me keep the latest version I actually could have known while keeping different funds and different months separate.

**Why do I filter by publication date before selecting the latest revision?**

If I select the latest version first, I might choose a revision from the future. Removing that revision afterward could leave me with no record for that month, even though an older usable value exists. For CCC's February observation, I need row 12 with a price of 111 on March 31; row 10 with a price of 112 only becomes available on April 5.

**What happens when I move the cutoff to April 15 and then restore March 31?**

In my local test, April 15 admits every publication date in the table. My as-of signals become AAA +5.83%, BBB -5.15% and CCC +1.82%, matching the naive signals exactly. Running again with the unchanged March 31 default gives AAA +1.98%, BBB -1.02% and CCC +0.91%. This shows that the difference comes from later publications and revisions, not from changing the return formula.

**What does the later-date test prove?**

I can reproduce the naive results once I move the decision date past all the publication dates. That supports the timing logic, but it does not make the questionable bond prices economically sound. I still need the separate sanity check.

## Verification and files

All nine checks in [verify_lab16.py](verify_lab16.py) passed: known funnel and complete row accounting, known signals, later-date equality, inclusive cutoff and revision timing, shuffled input order, rule precedence, separate sanity flags, same-date conflicts, and unavailable signals for insufficient history or a zero denominator.

```sh
python verify_lab16.py
```

The script saves the actual console runs in [data/lab16_output.txt](data/lab16_output.txt) and structured results in [data/lab16_results.json](data/lab16_results.json). The main submission files are this write-up and [asof.py](asof.py).
