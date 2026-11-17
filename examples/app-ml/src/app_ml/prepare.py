"""`python -m app_ml.prepare MODE --input DIR --output DIR`: the processing jobs' command.

`train` reads the churn table, `churn.csv` under --input, and writes XGBoost's CSV layout, the label
first and no header: one row in five, by position, to `validation/validation.csv`, the others to
`train/train.csv`. `score` reads the labelled holdout, `holdout.csv`, and writes the batch set, the
features alone in the table's order, to `batch/batch.csv`, and its labels, one per line in the same
order, to `labels/labels.csv`. Each mode reads its own file by name, and the job's input carries
that file alone, so the training never reads the holdout.

Every value is checked to be a number and every label 0 or 1, and is written as the table spells it.
What it prints lands in /aws/sagemaker/ProcessingJobs, which other roles in the account can read, so
it prints counts and file names, never a value. The standard library alone: the image adds nothing
to base's interpreter.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

from . import __version__

LABEL = "churned"
FEATURES = ("tenure_months", "monthly_charges", "support_calls", "contract_months", "late_payments")
INPUTS = {"train": "churn.csv", "score": "holdout.csv"}
# One row in VALIDATION_EVERY, by position, is the validation set's.
VALIDATION_EVERY = 5


class TableError(ValueError):
    """A table the job refuses: a missing column, a value that is not a number, a label off 0/1."""


def read_table(text: str) -> list[dict[str, str]]:
    """The table's rows, each checked: the label 0 or 1 and every feature a number."""
    reader = csv.DictReader(io.StringIO(text))
    missing = [name for name in (LABEL, *FEATURES) if name not in (reader.fieldnames or [])]
    if missing:
        raise TableError(f"the table has no column {', '.join(missing)}")
    rows = []
    for number, row in enumerate(reader, start=2):
        if row[LABEL] not in ("0", "1"):
            raise TableError(f"line {number}: {LABEL} is not 0 or 1")
        for name in FEATURES:
            try:
                float(row[name])
            except (TypeError, ValueError) as exc:
                raise TableError(f"line {number}: {name} is not a number") from exc
        rows.append(row)
    if not rows:
        raise TableError("the table has no row")
    return rows


def split(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """(training rows, validation rows): one in VALIDATION_EVERY, by position, to validation."""
    train = [row for i, row in enumerate(rows) if i % VALIDATION_EVERY != VALIDATION_EVERY - 1]
    validation = [row for i, row in enumerate(rows) if i % VALIDATION_EVERY == VALIDATION_EVERY - 1]
    return train, validation


def labelled_line(row: dict[str, str]) -> str:
    """One row in XGBoost's CSV layout: the label, then the features."""
    return ",".join([row[LABEL], *(row[name] for name in FEATURES)])


def features_line(row: dict[str, str]) -> str:
    """One row of the batch set: the features alone."""
    return ",".join(row[name] for name in FEATURES)


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def prepare(mode: str, source: Path, output: Path) -> dict[str, int]:
    """The mode's sets written under `output` from the table at `source`; the count of each."""
    rows = read_table(source.read_text(encoding="utf-8"))
    if mode == "train":
        train, validation = split(rows)
        write_lines(output / "train" / "train.csv", [labelled_line(row) for row in train])
        write_lines(
            output / "validation" / "validation.csv", [labelled_line(r) for r in validation]
        )
        return {"train": len(train), "validation": len(validation)}
    write_lines(output / "batch" / "batch.csv", [features_line(row) for row in rows])
    write_lines(output / "labels" / "labels.csv", [row[LABEL] for row in rows])
    return {"batch": len(rows), "labels": len(rows)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app-ml-prepare", description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=sorted(INPUTS), help="train or score")
    parser.add_argument("--input", required=True, type=Path, help="directory holding the table")
    parser.add_argument("--output", required=True, type=Path, help="directory for the sets")
    args = parser.parse_args(argv)

    print(f"app-ml {__version__} prepare {args.mode}, python {sys.version.split()[0]}")
    source = args.input / INPUTS[args.mode]
    if not source.is_file():
        print(f"no {INPUTS[args.mode]} under {args.input}", file=sys.stderr)
        return 1
    try:
        counts = prepare(args.mode, source, args.output)
    except TableError as exc:
        print(f"{source.name}: {exc}", file=sys.stderr)
        return 1
    print(
        f"{source.name}: " + ", ".join(f"{name} {count} row(s)" for name, count in counts.items())
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
