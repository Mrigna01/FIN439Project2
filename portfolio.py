"""Lab 14 portfolio baselines. Run with: python portfolio.py"""

from math import isclose, isfinite, sqrt


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
