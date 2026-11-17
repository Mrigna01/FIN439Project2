# Lab 20 — Project 2 readiness

## Cold run

I checked the repository from a clean local clone. The first README command, `source .venv/bin/activate`, failed immediately because the clone did not have a virtual environment. The older system Python on this Mac was 3.9.6, so the revised README puts the Python version check first and explains when to create the environment.

After the [README fix](https://github.com/Mrigna01/FIN439Project2/commit/947645a) was pushed, a second clone used Python 3.13.18 to create its own environment. I installed `requirements.txt`, ran `python -m streamlit run app.py` and confirmed the server was healthy. The command `python lab20.py` matched the [saved decision output](data/lab20-output.txt). The rerun took 30.73 seconds including setup and all 11 passing portfolio and app checks.

In the app, select **Campus Scholarship Reserve** and read **Current scenario**. The full-sample result is 75% SGOV and 25% VT, with 5.76% estimated return, 3.82% annual volatility and 75% eligible reserves. The automated app check also verified that changing **Reserve minimum (%)** to 80 produces the no-feasible-mix message.

## Changed input

The [prediction commit](https://github.com/Mrigna01/FIN439Project2/commit/5e4320622c5c438109794c43b3cbd900791dbf50) records the expected effect of raising the reserve minimum from 4% to 80% before the test ran. The 4% case had 408 feasible mixes. The 80% case had none. The highest-return mix at the higher floor was 80% SGOV and 20% VT, with an estimated return of 5.35%, below the 5.50% objective. This reverses the pilot under the changed constraint. The [validation record](docs/validation-and-ai-use.md) includes the cost, return-estimate and window checks.

## Code and reflection

In [portfolio.py](portfolio.py), `search_portfolio` generates fully invested, long-only weights in five-point steps. For each mix it computes the weighted expected return and adds the weights of reserve-eligible holdings. It skips any mix that fails either threshold, then uses the covariance matrix to find the lowest-volatility mix among the survivors. The candidate with the highest return at the 80% floor appears in the report as a diagnostic. The search returns no portfolio because even that candidate misses the target.

The environment worked in the original project folder, which made it easy to miss the setup problem a new reader would hit. I would keep the price snapshot and the base mandate fixed for checkout so the app and [decision memo](docs/decision-memo.md) can be reproduced from the same inputs.

The partner cold run, swap and live code explanation are still open. This checkout records a local rerun and an AI-assisted prediction. The student-written AI-off prediction and the Project 2 video and transcript links are also outstanding.

## Practice partner exchange

The practice exchange focused on the setup step that was easy to miss because the original project folder already had a virtual environment. The fresh-clone rerun took 30.73 seconds including setup and checks, and `python lab20.py` matched the [saved output](data/lab20-output.txt). The code discussion centered on why an 80% reserve floor leaves no feasible allocation. Even the highest-return mix at that floor reaches only 5.35%, below the 5.50% objective.

## Decision

Pilot 75% SGOV and 25% VT, and stop if the mix falls below the 5.50% estimated annual net return objective or breaches the applicable reserve floor.
