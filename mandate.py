"""Lab 13: check the supplied Meridian mandate inputs. Run: python mandate.py"""

from math import isclose

# Editable inputs: weights and limits are percentages, not fractions.
HOLDINGS = {
    "Cash": {"issuer": "none", "days": 0, "reserve_eligible": True},
    "Treasury bills": {"issuer": "U.S. Treasury", "days": 1, "reserve_eligible": True},
    "Treasury 10-year note": {"issuer": "U.S. Treasury", "days": 1, "reserve_eligible": True},
    "Global equity index fund": {"issuer": "diversified fund", "days": 2, "reserve_eligible": False},
    "Investment-grade bond fund": {"issuer": "diversified fund", "days": 3, "reserve_eligible": False},
    "Private real estate fund": {"issuer": "diversified fund", "days": 90, "reserve_eligible": False},
    "Acme Corp bonds": {"issuer": "Acme Corp", "days": 4, "reserve_eligible": False},
    "Acme Corp stock": {"issuer": "Acme Corp", "days": 1, "reserve_eligible": False},
}
CANDIDATES = {
    "A": dict(zip(HOLDINGS, [2, 2, 10, 60, 26, 0, 0, 0])),
    "B": dict(zip(HOLDINGS, [1, 0, 0, 55, 20, 15, 5, 4])),
    "C": dict(zip(HOLDINGS, [1, 1, 0, 70, 20, 0, 0, 8])),
    "D": dict(zip(HOLDINGS, [100, 0, 0, 0, 0, 0, 0, 0])),
    # Lab 14 benchmark: 40% IG bonds and 60% global equity.
    "E": dict(zip(HOLDINGS, [0, 0, 0, 60, 40, 0, 0, 0])),
}
RESERVE_SIZE = 100  # USD millions
QUARTERLY_DISTRIBUTION = 0.75  # USD millions
QUARTERS_TO_COVER = 4
LIQUIDITY_WINDOW = 5  # business days
MINIMUM_LIQUID_SHARE = 90
ISSUER_LIMIT = 8
EXEMPT_ISSUERS = {"none", "U.S. Treasury", "diversified fund"}


def reserve_minimum():
    return QUARTERS_TO_COVER * QUARTERLY_DISTRIBUTION / RESERVE_SIZE * 100


def check_candidate(weights):
    if set(weights) != set(HOLDINGS):
        raise ValueError("Each candidate must supply a weight for every holding.")
    total = sum(weights.values())
    lowest = min(weights.values())
    reserve = sum(weights[name] for name, holding in HOLDINGS.items()
                  if holding["reserve_eligible"])
    liquid = sum(weights[name] for name, holding in HOLDINGS.items()
                 if holding["days"] <= LIQUIDITY_WINDOW)
    companies = {}
    for name, holding in HOLDINGS.items():
        issuer = holding["issuer"]
        if issuer not in EXEMPT_ISSUERS:
            companies[issuer] = companies.get(issuer, 0) + weights[name]
    largest = max(companies.values(), default=0)
    return [
        ("Weights sum to 100", total, isclose(total, 100, rel_tol=0, abs_tol=1e-9)),
        ("Long-only (lowest weight)", lowest, lowest >= 0),
        (f"Reserve >= {reserve_minimum():.1f}%", reserve, reserve >= reserve_minimum()),
        (f"Redeemable in {LIQUIDITY_WINDOW} days >= {MINIMUM_LIQUID_SHARE:.1f}%",
         liquid, liquid >= MINIMUM_LIQUID_SHARE),
        (f"Largest single company <= {ISSUER_LIMIT:.1f}%", largest, largest <= ISSUER_LIMIT),
    ]


def main():
    print(f"Reserve minimum: {reserve_minimum():.1f}%")
    for name, weights in CANDIDATES.items():
        print(f"\nCandidate {name}")
        checks = check_candidate(weights)
        for label, value, passed in checks:
            print(f"{label}: {value:.1f} {'pass' if passed else 'FAIL'}")
        print("Calendar-year loss: requires CIO clarification")
        failures = sum(not passed for _, _, passed in checks)
        print("passes every checkable rule" if failures == 0 else f"fails {failures} rule(s)")


if __name__ == "__main__":
    main()
