---
name: burry-business
description: Apply FIN439 Lab 19's Michael Burry business screen to shared SEC annual facts, checking cash conversion and liabilities versus equity and writing a memo from printed numbers. Use for accounting scrutiny, not short-sale advice or pricing.
---

# Michael Burry business screen

From the repository root run:

```sh
.venv/bin/python .agents/skills/burry-business/scripts/burry.py COST --offline
```

Replace COST with the requested ticker. Omit `--offline` for a first download;
use `--refresh` only to deliberately replace the saved SEC snapshot. The shared
`legend_panel.py` pipeline preserves Lab 18's annual-period, filing, tag and
missing-data rules. The bundled code tests operating cash flow at least net
income in every year and latest liabilities no greater than twice equity.
Missing cash-flow inputs make that check `not known`. Missing or nonpositive
equity makes liabilities/equity and the leverage check `not known`.

Read the [FAskills Burry page](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/michael_burry.md)
as a perspective on accounting skepticism, not as permission to invent fraud,
trade history, price targets or missing data. No paid services or API keys.

Read the script's entire printed report, then write
`docs/lab19/TICKER_burry.md`, using **own the business**, **watch it**, or **pass**
as a simulated Burry-inspired judgment. Use only printed financial numbers with
their units and rounding. Distinguish an individual weak cash-conversion year
from proof of accounting manipulation; passing a leverage cap does not prove
the business is cheap or safe. Keep every unknown explicit.

After all panel memos exist, run
`.venv/bin/python legend_panel.py COST --offline --bind-memos` to verify the
numbers and bind the memos to these facts and checks. Never claim partner work,
an AI-off exercise, or actual investor action occurred without evidence.
