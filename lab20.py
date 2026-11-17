"""Print the Campus Scholarship Reserve decision inputs and stress results."""

from copy import deepcopy
from pathlib import Path

import portfolio as engine

OBJECTIVE = 0.055
RESERVE_MINIMUM = 0.04


def print_mix(label, weights, sleeves, covariance, minimum=RESERVE_MINIMUM):
    annual_return = engine.expected_return(weights, sleeves)
    volatility = engine.portfolio_volatility(weights, covariance)
    reserve = engine.reserve_weight(weights, sleeves)
    allocation = " / ".join(f"{sleeve['name']} {weight:.0%}"
                            for sleeve, weight in zip(sleeves, weights))
    return_check = "pass" if annual_return >= OBJECTIVE - 1e-12 else "fail"
    reserve_check = "pass" if reserve >= minimum - 1e-12 else "fail"
    print(f"{label}: {allocation} | Return {annual_return:.2%} | "
          f"Volatility {volatility:.2%} | Reserve {reserve:.2%} | "
          f"Return objective {return_check}, reserve floor {reserve_check}")


def print_search(label, estimate, minimum=RESERVE_MINIMUM):
    sleeves = estimate["sleeves"]
    correlations = estimate["correlations"]
    result = engine.search_portfolio(sleeves, correlations, OBJECTIVE, minimum)
    if result is None:
        print(f"{label}: no grid allocation meets the {OBJECTIVE:.2%} return objective "
              f"and the {minimum:.0%} reserve floor")
    else:
        print_mix(label, result["weights"], sleeves,
                  engine.covariance_matrix(sleeves, correlations), minimum)
        print(f"  Feasible allocations: {result['feasible']:,} of {result['evaluated']:,}")
    return result


def main():
    prices = Path(__file__).with_name("prices.csv")
    full = engine.estimate_from_csv(prices)
    recent = engine.estimate_from_csv(prices, last_36=True)
    sleeves = full["sleeves"]
    covariance = engine.covariance_matrix(sleeves, full["correlations"])
    print("Campus Scholarship Reserve")
    print(f"Full sample: {full['observations']} monthly returns, "
          f"{full['return_start']} through {full['end']}")
    print(f"Objective: {OBJECTIVE:.2%} annually | Base reserve floor: {RESERVE_MINIMUM:.0%}")
    print("All displayed mixes are long-only and fully invested.")
    print_mix("Equal weight", engine.equal_weights(sleeves), sleeves, covariance)
    print_mix("Benchmark", engine.benchmark_weights(sleeves, {"USIG": 0.4, "VT": 0.6}),
              sleeves, covariance)
    print_search("Full sample", full)
    print_search(f"Last 36 months ({recent['return_start']} through {recent['end']})", recent)

    lower_return = deepcopy(full)
    next(sleeve for sleeve in lower_return["sleeves"] if sleeve["name"] == "VT")["return"] -= 0.01
    print_search("VT estimate down 1 percentage point", lower_return)

    net = deepcopy(full)
    for sleeve in net["sleeves"]:
        sleeve["return"] -= 0.003
    print_search("Illustrative annual cost of 30 basis points (net return)", net)
    print_mix("Original pilot after that cost", [0.75, 0, 0, 0.25], net["sleeves"], covariance)

    print_search("Reserve floor raised to 80%", full, minimum=0.80)
    print_mix("Highest-return mix at an 80% reserve floor", [0.80, 0, 0, 0.20],
              sleeves, covariance, minimum=0.80)
    print("Decision: Pilot 75% SGOV / 25% VT. Stop if the mix falls below the "
          "5.50% annual net return objective or breaches the applicable reserve floor.")


if __name__ == "__main__":
    main()
