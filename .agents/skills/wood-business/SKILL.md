---
name: wood-business
description: Apply FIN439 Lab 19's Cathie Wood business screen to SEC annual facts, checking revenue growth and R&D intensity and writing a memo using only the printed panel numbers. Use for the innovation screen, not price targets or trades.
---

# Cathie Wood business screen

From the repository root run:

```sh
.venv/bin/python .agents/skills/wood-business/scripts/wood.py COST --offline
```

Replace COST with the requested ticker. Omit `--offline` for a company's first
SEC download; add `--refresh` only for an intentional update. Reuse the common
facts and annual-period rules in `legend_panel.py`. The bundled script computes
these checks: first-to-last revenue CAGR at least 15%, and latest-year R&D at
least 5% of revenue. The annual CAGR uses four intervals over five fiscal years.
Missing or invalid inputs produce `not known`; missing R&D is never zero.

Use the [FAskills Wood page](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/cathie_wood.md)
as philosophy only. The course takes priority: no paid sources, projections,
holdings assertions, price targets, or claims about what Cathie actually traded.
Historical growth and R&D intensity do not prove future technological success.

Read the complete printed report before writing the AI memo at
`docs/lab19/TICKER_wood.md`. State **own the business**, **watch it**, or **pass**
as a simulated Wood-inspired business judgment; explain the code's checks and
any gaps. Every numeric claim must appear in the printed financial table or
thresholds, with matching units. Under the memo record the threshold retained
and why. Use the default growth threshold unless a deliberate probe is requested;
the lab probe lowers it to 5%, without changing R&D's missing status.

After all panel memos exist, bind them with
`.venv/bin/python legend_panel.py COST --offline --bind-memos`.
This verifies the numbers and records both the facts and the threshold-dependent
analysis fingerprint. Do not describe simulations as real partner work or
AI-off activity. The panel is a screen, not a valuation or vote to buy shares.
