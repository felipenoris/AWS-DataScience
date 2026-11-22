#!/usr/bin/env python3
"""The application's synthetic sample: a churn table and a labelled holdout, from a fixed seed.

    python3 scripts/make-samples.py               # samples/churn.csv and samples/holdout.csv
    python3 scripts/make-samples.py --output DIR  # the same files under DIR

Each row is a customer: tenure in months, the monthly charge, support calls, the contract's length
in months, late payments, and `churned`, drawn with a probability that falls with tenure and a
longer contract and rises with the charge, the calls and the late payments. The holdout is drawn
after the table from the same stream, so its rows are other customers, and app-ml-train never reads
it: its job's input carries churn.csv alone. No data is fetched and none is governed (Stage 17
decision 3).

The same seed writes the same bytes: every draw is `random.Random.random()`, whose sequence for a
seed Python keeps across versions, and every value is formatted, never printed as a float's repr.
The standard library alone.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

SEED = 20261117
ROWS = {"churn.csv": 400, "holdout.csv": 200}
HEADER = "tenure_months,monthly_charges,support_calls,contract_months,late_payments,churned"


def customer(rng: random.Random) -> str:
    """One row of the table, its label drawn from the row's churn probability."""
    tenure = 1 + int(rng.random() * 72)
    charge = 20 + rng.random() * 100
    calls = int(rng.random() ** 2 * 10)
    draw = rng.random()
    contract = 1 if draw < 0.55 else 12 if draw < 0.8 else 24
    late = int(rng.random() ** 3 * 7)
    logit = (
        0.4
        - 0.06 * tenure
        + 0.02 * (charge - 70)
        + 0.45 * calls
        + 0.5 * late
        - (1.1 if contract == 12 else 2.0 if contract == 24 else 0.0)
    )
    churned = 1 if rng.random() < 1 / (1 + math.exp(-logit)) else 0
    return f"{tenure},{charge:.2f},{calls},{contract},{late},{churned}"


def tables(seed: int = SEED) -> dict[str, str]:
    """Each file's text, in ROWS's order, from one stream."""
    rng = random.Random(seed)
    return {
        name: "".join(f"{line}\n" for line in [HEADER, *(customer(rng) for _ in range(count))])
        for name, count in ROWS.items()
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "samples",
        help="the folder to write (default: the application's samples/)",
    )
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, text in tables().items():
        (args.output / name).write_text(text, encoding="utf-8")
        churned = sum(line.endswith(",1") for line in text.splitlines()[1:])
        print(f"{args.output / name}: {text.count(chr(10)) - 1} rows, {churned} churned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
