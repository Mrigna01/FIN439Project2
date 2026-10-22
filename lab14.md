# Lab 14 - Portfolio Baselines

## The question

What does each simple portfolio earn and risk, and does any of them meet the Meridian mandate?

The benchmark is the only one with an expected return above 6.5%, but it has no eligible reserves. Equal weight and inverse volatility have enough reserves but fall short of the return target. So none of these three baselines meets both requirements using the lab's inputs.

## Inputs and code

These are course training values, not estimates from market data. CPI is a labelled estimate of 2.5%, making the CPI + 4% objective 6.5%.

| Sleeve | Expected return | Volatility | Reserve-eligible? |
|---|---:|---:|---|
| Treasury bills | 3.5% | 0.5% | Yes |
| Treasury 10-year note | 4.3% | 7.0% | Yes |
| Investment-grade bond fund | 5.0% | 6.0% | No |
| Global equity index fund | 8.0% | 16.0% | No |

| Correlation | Bills | 10-year | IG bonds | Equity |
|---|---:|---:|---:|---:|
| Bills | 1.00 | 0.10 | 0.05 | 0.00 |
| 10-year | 0.10 | 1.00 | 0.80 | -0.10 |
| IG bonds | 0.05 | 0.80 | 1.00 | 0.25 |
| Equity | 0.00 | -0.10 | 0.25 | 1.00 |

[portfolio.py](portfolio.py) uses only the Python standard library. Returns, volatilities and weights are decimals inside the code. Each calculation has its own function so the code can be reused later.

```sh
python portfolio.py
python mandate.py
python verify_lab14.py
```

## Results from the run

| Portfolio | Bills | 10-year | IG bonds | Equity | Return | Volatility | Reserve | Meets 6.5%? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Benchmark | 0.0% | 0.0% | 40.0% | 60.0% | 6.80% | 10.46% | 0.0% | Yes |
| Equal weight | 25.0% | 25.0% | 25.0% | 25.0% | 5.20% | 5.21% | 50.0% | No |
| Inverse volatility | 84.3% | 6.0% | 7.0% | 2.6% | 3.77% | 1.05% | 90.3% | No |

All displayed results match the lab's known answers. Inverse-volatility weights appear to sum to 99.9% because each is rounded to one decimal place. The actual weights sum to 100%.

## Verification

[verify_lab14.py](verify_lab14.py) ran five tests successfully. It changes copies of the correlation table in memory, so the original inputs stay intact.

| Check | Actual result |
|---|---|
| Compare all three baselines with the known answers | All weights, returns, volatilities, reserves and objective verdicts match |
| Set both IG-equity correlations to 0.50 and rerun the engine | Benchmark volatility becomes 11.00% |
| Set both IG-equity correlations to 1.3, then separately to -1.3 | Both rejected: `Every correlation must be between -1 and 1.` |
| Set only one IG-equity cell to 0.50 | Rejected: `Correlation table must be symmetric.` |
| Run candidate E through the mandate checker | Only the reserve rule fails |

After the checks, the baseline engine was run again with both IG-equity cells at 0.25. Benchmark volatility returned to 10.46%. These are local automated checks of this repo's code; they do not represent a partner code swap.

## Benchmark through the mandate checker

Candidate E in [mandate.py](mandate.py) holds 40% IG bonds and 60% global equity, with zero in all other holdings.

```text
Candidate E
Weights sum to 100: 100.0 pass
Long-only (lowest weight): 0.0 pass
Reserve >= 3.0%: 0.0 FAIL
Redeemable in 5 days >= 90.0%: 100.0 pass
Largest single company <= 8.0%: 0.0 pass
Calendar-year loss: requires CIO clarification
fails 1 rule(s)
```

Meridian needs four quarterly payments of $0.75 million, which is $3 million or 3% of the $100 million portfolio. E has 0% eligible reserves. Its holdings meet the five-day liquidity rule, but that does not make them eligible for the separate reserve rule. The client's benchmark can be useful for comparison while still breaking the client's own mandate.

The 6.80% expected return clears the lab's modeled objective. It does not guarantee that return or prove compliance with the calendar-year loss statement. Volatility is not a maximum possible loss.

## Diversification and the hand calculation

Diversification means spreading a portfolio across investments that do not all move together. When correlation is below +1, the investments do not move in perfect step, so their combined risk is lower than the weighted average of their individual volatilities. This can make a mix less risky than either asset in some cases, but it does not always do that.

For the benchmark, the two weights are 0.40 and 0.60, the volatilities are 0.06 and 0.16, and correlation is 0.25.

```text
Expected return = 0.40 * 0.05 + 0.60 * 0.08
                = 0.068 = 6.80%

Variance = (0.40 * 0.06)^2 + (0.60 * 0.16)^2
           + 2 * 0.40 * 0.60 * 0.06 * 0.16 * 0.25
         = 0.000576 + 0.009216 + 0.001152
         = 0.010944

Volatility = sqrt(0.010944) = 0.1046136 = 10.46%
```

If correlation were +1, the volatility would be 12.00%, the weighted average of 6% and 16%. At 0.25 it is 10.46%. That shows the diversification benefit, even though the mix is still riskier than the bond fund alone.

With correlation changed to 0.50, variance is 0.012096 and volatility is 10.9982%, which rounds to 11.00%.

## How the risk code works

`covariance_matrix()` multiplies each correlation by the two relevant sleeve volatilities. The diagonal entries are each sleeve's variance, since its correlation with itself is 1.

The main risk calculation is:

```python
variance = sum(
    weights[i] * weights[j] * covariance[i][j]
    for i in range(len(weights))
    for j in range(len(weights))
)
```

The outer loop selects one sleeve and the inner loop pairs it with every sleeve. Multiplying by both weights scales each covariance to the portfolio's holdings. Adding those contributions gives portfolio variance. The function checks that variance is not negative and then takes its square root to get volatility.

## Reflection

**Why does inverse volatility put so much into bills?**

The method gives more weight to a sleeve with lower volatility. Bills have volatility of just 0.005, so their inverse volatility is 200. The corresponding values for the 10-year note, IG bonds and equity are about 14.29, 16.67 and 6.25. Dividing each by the total gives bills about 84.3% of the portfolio. The method does not use the return target when choosing weights, which explains why it has low risk but only a 3.77% expected return.

**Which baseline would I show the CIO first?**

I would start with the benchmark because it is already the client's comparison point. It makes the main issue clear: the expected return is high enough, but the reserve allocation is zero. Then I would show equal weight and inverse volatility to explain the trade-off. They reduce risk and add reserves, but their expected returns are too low. We need a different mix to meet both requirements.

## Code discussion prompt

Why does the portfolio-volatility loop include both covariance[i][j] and covariance[j][i]? What happens to the benchmark's risk estimate if both cross terms are left out?

**My answer:** We include both covariance[i][j] and covariance[j][i] because both represent how the two assets move together, and both cross terms are needed to calculate the portfolio's total variance correctly.

If we left out both cross terms, the benchmark's calculated volatility would be lower, dropping from 10.46% to 9.90%. This is because the correlation between bonds and equities is positive (0.25), so the covariance terms add to the portfolio's risk. Removing them would underestimate the actual volatility.

## Before Thursday - my fund universe

My Project 2 client is the Campus Scholarship Reserve from Lab 13. It has $1 million, a seven-year horizon, and $10,000 quarterly scholarship payments. It needs at least $40,000, or 4%, in eligible reserves and aims for CPI + 3% over rolling five-year periods. I chose four funds so each part of the portfolio has a clear job.

| Ticker | Full fund name | Role in my portfolio | Why I included it |
|---|---|---|---|
| BIL | State Street SPDR Bloomberg 1-3 Month T-Bill ETF | Cash and reserves | Short-term Treasury bills provide a cash-like sleeve for scholarship payments. This is the main fund I would use for the reserve allocation. |
| IEF | iShares 7-10 Year Treasury Bond ETF | Government bonds | Adds Treasury exposure beyond short-term bills. Its price can move with interest rates, so it is not the same as cash. |
| LQD | iShares iBoxx $ Investment Grade Corporate Bond ETF | Fixed income | Adds diversified investment-grade corporate bonds and a different source of income. |
| VT | Vanguard Total World Stock ETF | Global equity | Adds global stocks for long-term growth toward the return objective. |

Fund details checked on the issuer pages: [BIL](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil), [IEF](https://www.ishares.com/us/products/239456/ishares-710-year-treasury-bond-etf), [LQD](https://www.ishares.com/us/products/239566/lqd-ishares-iboxx-investment-grade-corporate-bond-etf), and [VT](https://advisors.vanguard.com/investments/products/vt/vanguard-total-world-stock-etf).

These funds map to the four roles used in the lab. For the classroom model, BIL and IEF represent the reserve-eligible government sleeves. I would mainly use BIL for near-term payments because IEF has more interest-rate risk. LQD and VT are not reserve sleeves. This selects the investments; it does not set their final portfolio weights.

My own client's objective is CPI + 3%, which would be 5.5% using the lab's 2.5% CPI estimate. Meridian's 6.5% objective in `portfolio.py` stays separate from my client's target.

## Monthly price data

The combined file is [prices.csv](prices.csv). Its columns are `Date,BIL,IEF,LQD,VT`, with the oldest month first. All prices are in U.S. dollars and use Yahoo Finance's **Adj Close**, which adjusts historical closing prices for distributions and splits.

| Ticker | Price source | Download date |
|---|---|---|
| BIL | [Yahoo Finance historical data](https://finance.yahoo.com/quote/BIL/history/) | October 22, 2026 |
| IEF | [Yahoo Finance historical data](https://finance.yahoo.com/quote/IEF/history/) | October 22, 2026 |
| LQD | [Yahoo Finance historical data](https://finance.yahoo.com/quote/LQD/history/) | October 22, 2026 |
| VT | [Yahoo Finance historical data](https://finance.yahoo.com/quote/VT/history/) | October 22, 2026 |

The download used Yahoo Finance's chart endpoint. It retrieved daily adjusted closes and kept the last trading day's value in each completed month. That gives monthly observations dated on their actual trading days, rather than monthly averages. No prices were interpolated or forward-filled.

The file contains **61 month-end prices per fund, from September 30, 2021 through September 30, 2026**. September 2021 is the starting observation, so the data can produce **60 monthly returns from October 2021 through September 2026**. October 2026 is excluded because it was still in progress on the download date.

Checks on the saved file found all 61 months, four complete numeric price columns, no missing or nonpositive prices, no duplicate dates, and matching dates across funds. The file is sorted from oldest to newest. Each price matches the corresponding saved source observation.

Adjusted prices can be revised by the provider after later distributions. The downloaded snapshot is saved in [data/prices_source.json](data/prices_source.json), along with the exact request URLs, download timestamp, original closing prices and selected adjusted closes. [download_prices.py](download_prices.py) reproduces the download with `python download_prices.py` using Python's standard library.

For Thursday, monthly returns can be calculated as `current adjusted price / previous adjusted price - 1`. Those returns will provide historical estimates for my fund universe. The course training values in `portfolio.py` remain unchanged so Meridian can still be checked against the known answer.
