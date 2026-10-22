"""Lab 14 portfolio baselines. Run with: python portfolio.py"""

from math import isclose, isfinite, sqrt
import csv
from datetime import date
from io import StringIO
from pathlib import Path
from statistics import mean, stdev, correlation


# Editable course training inputs, not market estimates.
# Returns, volatilities and weights are decimals: 0.035 means 3.5%.
# The order here also sets the rows and columns of CORRELATIONS.
SLEEVES = [
    {"name": "Treasury bills", "return": 0.035, "volatility": 0.005,
     "reserve_eligible": True},
    {"name": "Treasury 10-year note", "return": 0.043, "volatility": 0.070,
     "reserve_eligible": True},
    {"name": "Investment-grade bond fund", "return": 0.050, "volatility": 0.060,
     "reserve_eligible": False},
    {"name": "Global equity index fund", "return": 0.080, "volatility": 0.160,
     "reserve_eligible": False},
]

#  The row and column order is:

#   0 = Bills
#   1 = 10-year Treasury
#   2 = IG bonds
#   3 = Equity

CORRELATIONS = [
    [1.00, 0.10, 0.05, 0.00],
    [0.10, 1.00, 0.80, -0.10],
    [0.05, 0.80, 1.00, 0.25],
    [0.00, -0.10, 0.25, 1.00],
]


CPI_ESTIMATE = 0.025  # Labelled estimate used by the lab.
OBJECTIVE_RETURN = CPI_ESTIMATE + 0.04  # CPI + 4% = 6.5%.
BENCHMARK_ALLOCATIONS = {
    "Investment-grade bond fund": 0.40,
    "Global equity index fund": 0.60,
}


def validate_inputs(sleeves, correlations):
    """Reject invalid inputs before calculating any portfolio."""
    size = len(sleeves)
    if not size or len(correlations) != size or any(
        len(row) != size for row in correlations
    ):
        raise ValueError("Correlation table must have one row and column per sleeve.")
    for sleeve in sleeves:
        if not isfinite(sleeve["return"]):
            raise ValueError("Expected returns must be finite.")
        if not isfinite(sleeve["volatility"]) or sleeve["volatility"] <= 0:
            raise ValueError("Volatilities must be finite and positive.")
    for i in range(size):
        for j in range(size):
            value = correlations[i][j]
            if not isfinite(value) or not -1 <= value <= 1:
                raise ValueError("Every correlation must be between -1 and 1.")
            if not isclose(value, correlations[j][i], rel_tol=0, abs_tol=1e-12):
                raise ValueError("Correlation table must be symmetric.")
        if not isclose(correlations[i][i], 1.0, rel_tol=0, abs_tol=1e-12):
            raise ValueError("Each sleeve's correlation with itself must be 1.")


def covariance_matrix(sleeves, correlations):
    """Covariance(i, j) = correlation(i, j) * volatility(i) * volatility(j)."""
    validate_inputs(sleeves, correlations)
    return [
        [correlations[i][j] * left["volatility"] * right["volatility"]
         for j, right in enumerate(sleeves)]
        for i, left in enumerate(sleeves)
    ]


def benchmark_weights(sleeves, allocations):
    return [allocations.get(sleeve["name"], 0.0) for sleeve in sleeves]


def equal_weights(sleeves):
    return [1.0 / len(sleeves) for _ in sleeves]


def inverse_volatility_weights(sleeves):
    inverse_volatilities = [1.0 / sleeve["volatility"] for sleeve in sleeves]
    total = sum(inverse_volatilities)
    return [value / total for value in inverse_volatilities]


def expected_return(weights, sleeves):
    return sum(weight * sleeve["return"] for weight, sleeve in zip(weights, sleeves))


def portfolio_volatility(weights, covariance):
    # Include every pair, including both off-diagonal terms for each pair.
    variance = sum(
        weights[i] * weights[j] * covariance[i][j]
        for i in range(len(weights))
        for j in range(len(weights))
    )
    if variance < 0:
        raise ValueError("Portfolio variance is negative; check the correlation inputs.")
    return sqrt(variance)


def reserve_weight(weights, sleeves):
    return sum(weight for weight, sleeve in zip(weights, sleeves)
               if sleeve["reserve_eligible"])


def meets_objective(portfolio_return, objective_return):
    return portfolio_return >= objective_return


def weight_grid(asset_count, remaining=20, prefix=()):
    """Yield each fully invested long-only mix once, in units of 5%."""
    if asset_count == 1:
        yield [(unit / 20) for unit in (*prefix, remaining)]
    else:
        for units in range(remaining + 1):
            yield from weight_grid(asset_count - 1, remaining - units, (*prefix, units))


def search_portfolio(sleeves, correlations, objective_return, reserve_minimum):
    """Return the minimum-volatility feasible 5-point grid mix, or None.

    In an exact risk tie, keep the first mix in deterministic grid order.
    This searches the grid, not every possible continuous allocation.
    """
    if not 3 <= len(sleeves) <= 6:
        raise ValueError("Use three to six assets for the grid search.")
    if not isfinite(objective_return):
        raise ValueError("Objective return must be finite.")
    if not isfinite(reserve_minimum) or not 0 <= reserve_minimum <= 1:
        raise ValueError("Reserve minimum must be between 0% and 100%.")
    covariance = covariance_matrix(sleeves, correlations)
    best = None
    evaluated = feasible = 0
    for weights in weight_grid(len(sleeves)):
        evaluated += 1
        result = expected_return(weights, sleeves)
        reserve = reserve_weight(weights, sleeves)
        # Tiny tolerance prevents binary rounding from rejecting an exact boundary.
        if result < objective_return - 1e-12 or reserve < reserve_minimum - 1e-12:
            continue
        feasible += 1
        volatility = portfolio_volatility(weights, covariance)
        if best is None or volatility < best["volatility"]:
            best = {"weights": weights, "return": result,
                    "volatility": volatility, "reserve": reserve}
    if best is not None:
        best.update(evaluated=evaluated, feasible=feasible)
    return best


def estimate_from_csv(source, last_36=False):
    """Estimate annual return/risk from monthly adjusted prices, standard library only.

    source: path, uploaded file-like object, or UTF-8 bytes.
    Last 36 means 36 RETURNS, using 37 prices. Sample standard deviation
    uses n-1. Return estimates are arithmetic mean * 12, not CAGR.
    """
    if isinstance(source, (str, Path)):
        text = Path(source).read_text(encoding="utf-8-sig")
    else:
        text = source if isinstance(source, bytes) else source.read()
        if isinstance(text, bytes):
            text = text.decode("utf-8-sig")
    rows = list(csv.reader(StringIO(text)))
    if not rows or not rows[0] or rows[0][0].strip().lower() != "date":
        raise ValueError("CSV must start with Date, followed by ticker columns.")
    names = [name.strip() for name in rows[0][1:]]
    if not 3 <= len(names) <= 6 or not all(names) or len(set(names)) != len(names):
        raise ValueError("CSV must contain three to six unique, nonblank ticker columns.")
    dates, prices = [], []
    for line, row in enumerate(rows[1:], 2):
        if len(row) != len(names) + 1:
            raise ValueError(f"CSV row {line}: missing or extra columns.")
        try:
            day = date.fromisoformat(row[0].strip())
            values = [float(value) for value in row[1:]]
        except ValueError as error:
            raise ValueError(f"CSV row {line}: use YYYY-MM-DD dates and numeric prices.") from error
        if any(not isfinite(value) or value <= 0 for value in values):
            raise ValueError(f"CSV row {line}: prices must be finite and positive.")
        if dates:
            month_gap = (day.year - dates[-1].year) * 12 + day.month - dates[-1].month
            if day <= dates[-1] or month_gap != 1:
                raise ValueError("CSV must have one observation per consecutive month, oldest first.")
        dates.append(day)
        prices.append(values)
    if len(prices) < 3:
        raise ValueError("At least three monthly prices are needed to estimate risk.")
    returns = [[now[i] / before[i] - 1 for i in range(len(names))]
               for before, now in zip(prices, prices[1:])]
    if last_36:
        if len(returns) < 36:
            raise ValueError("Last-36-months estimation requires at least 37 monthly prices.")
        returns = returns[-36:]
    columns = list(zip(*returns))
    deviations = [stdev(column) for column in columns]
    if any(value == 0 or not isfinite(value) for value in deviations):
        raise ValueError("A fund has zero or invalid return variation; its correlation is undefined.")
    sleeves = [{"name": name, "return": mean(column) * 12,
                "volatility": deviation * sqrt(12),
                "reserve_eligible": name.upper() in {"SGOV", "SCHR"}}
               for name, column, deviation in zip(names, columns, deviations)]
    correlations = [[1.0 if i == j else max(-1.0, min(1.0, correlation(a, b)))
                     for j, b in enumerate(columns)] for i, a in enumerate(columns)]
    validate_inputs(sleeves, correlations)
    return {"sleeves": sleeves, "correlations": correlations,
            "observations": len(returns),
            "price_start": dates[-len(returns)-1].isoformat(),
            "return_start": dates[-len(returns)].isoformat(),
            "end": dates[-1].isoformat()}


def largest_weight_change(first, second):
    """Largest absolute allocation change in percentage points; None if infeasible."""
    if first is None or second is None:
        return None
    if len(first["weights"]) != len(second["weights"]):
        raise ValueError("Compare portfolios with the same asset order.")
    return max(abs(a - b) for a, b in zip(first["weights"], second["weights"])) * 100


def main():
    covariance = covariance_matrix(SLEEVES, CORRELATIONS)
    portfolios = {
        "Benchmark": benchmark_weights(SLEEVES, BENCHMARK_ALLOCATIONS),
        "Equal weight": equal_weights(SLEEVES),
        "Inverse volatility": inverse_volatility_weights(SLEEVES),
    }
    print("Lab 14 - Portfolio baselines (course training inputs)")
    print(f"Objective: {OBJECTIVE_RETURN:.1%} (CPI estimate: {CPI_ESTIMATE:.1%} + 4.0%)")
    for name, weights in portfolios.items():
        if len(weights) != len(SLEEVES) or any(weight < 0 for weight in weights) or not isclose(
            sum(weights), 1.0, rel_tol=0, abs_tol=1e-12
        ):
            raise ValueError(f"{name}: weights must be nonnegative and sum to 100%.")
        result = expected_return(weights, SLEEVES)
        print(f"\n{name}")
        for sleeve, weight in zip(SLEEVES, weights):
            print(f"  {sleeve['name']}: {weight:.1%}")
        print(f"  Expected return: {result:.2%}")
        print(f"  Volatility: {portfolio_volatility(weights, covariance):.2%}")
        print(f"  Reserve-eligible weight: {reserve_weight(weights, SLEEVES):.1%}")
        print(f"  Meets {OBJECTIVE_RETURN:.1%} objective: "
              f"{'yes' if meets_objective(result, OBJECTIVE_RETURN) else 'no'}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        raise SystemExit(f"Input error: {error}") from None
