"""The Telco churn table prepared and split as AWS's XGBoost recipe does (Stage 17 step 2.1).

`TotalCharges` is coerced to numeric and its blank rows dropped; the label `churn_label` and six
features are derived; the rows are shuffled with random_state=1729 and split 70/15/15. Each part
is written in XGBoost's CSV layout: the label first, no header, no index.

Two callers: `data.py` imports `prepare` and `split` in the space, and the pipeline's processing
step runs this file in the house image (Stage 17 step 5.1):

    python prepare.py --input DIR --output DIR

where --input holds the raw CSV and --output receives train/, validation/ and test/, one CSV
each. What it prints lands in /aws/sagemaker/ProcessingJobs, so it prints counts, never a row.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

LABEL = "churn_label"
FEATURES = (
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "lifetime_value",
    "is_month_to_month",
    "is_fiber_optic",
)
SEED = 1729
PARTS = (("train", 0.70), ("validation", 0.15), ("test", 0.15))


def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    """The recipe's columns from the raw table, the label first."""
    raw = raw.copy()
    raw["TotalCharges"] = pd.to_numeric(raw["TotalCharges"], errors="coerce")
    raw = raw.dropna(subset=["TotalCharges"])
    table = pd.DataFrame(
        {
            LABEL: (raw["Churn"] == "Yes").astype(int),
            "tenure_months": raw["tenure"],
            "monthly_charges": raw["MonthlyCharges"],
            "total_charges": raw["TotalCharges"],
            "lifetime_value": raw["MonthlyCharges"] * raw["tenure"],
            "is_month_to_month": (raw["Contract"] == "Month-to-month").astype(int),
            "is_fiber_optic": (raw["InternetService"] == "Fiber optic").astype(int),
        }
    )
    return table[[LABEL, *FEATURES]]


def split(table: pd.DataFrame) -> dict:
    """Shuffled once, cut 70/15/15: {part name: rows}. The last part takes the remainder."""
    shuffled = table.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    parts, start = {}, 0
    for i, (name, share) in enumerate(PARTS):
        end = len(shuffled) if i == len(PARTS) - 1 else start + int(len(shuffled) * share)
        parts[name] = shuffled.iloc[start:end]
        start = end
    return parts


def to_csv(rows: pd.DataFrame) -> str:
    """XGBoost's CSV layout: the label first, no header, no index."""
    return rows.to_csv(header=False, index=False)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="prepare.py")
    parser.add_argument("--input", required=True, type=Path, help="directory holding the raw CSV")
    parser.add_argument("--output", required=True, type=Path, help="directory for the parts")
    args = parser.parse_args(argv)

    print(f"python {sys.version.split()[0]} at {sys.executable}, pandas {pd.__version__}")
    sources = sorted(args.input.glob("*.csv"))
    if len(sources) != 1:
        print(f"expected one CSV under {args.input}, found {len(sources)}", file=sys.stderr)
        return 1
    table = prepare(pd.read_csv(sources[0]))
    print(f"{sources[0].name}: {len(table)} rows prepared")
    for name, rows in split(table).items():
        target = args.output / name / f"{name}.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(to_csv(rows), encoding="utf-8")
        print(f"{name}: {len(rows)} rows -> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
