"""`python -m awsds_demo_job --input DIR --output DIR`: the processing job's mode.

Every CSV under --input becomes a JSON summary in --output. SageMaker downloads the inputs
into --input before the command starts and uploads --output after it exits, so the command
reaches no network and holds no credentials: the D13 boundary runs every job isolated.

What it prints lands in /aws/sagemaker/ProcessingJobs, which every project role in the
account can read, so it prints the interpreter, counts and paths, never a cell of data.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import transform


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="awsds_demo_job")
    parser.add_argument("--input", required=True, type=Path, help="directory holding the CSVs")
    parser.add_argument("--output", required=True, type=Path, help="directory for the results")
    args = parser.parse_args(argv)

    print(f"python {sys.version.split()[0]} at {sys.executable}")
    files = sorted(p for p in args.input.rglob("*") if p.is_file() and p.suffix.lower() == ".csv")
    if not files:
        print(f"no CSV under {args.input}", file=sys.stderr)
        return 1
    args.output.mkdir(parents=True, exist_ok=True)
    for path in files:
        summary = transform.summarize(path.name, path.read_bytes())
        target = args.output / transform.result_name(path.name)
        target.write_bytes(transform.render(summary))
        print(f"{path.name}: {summary['rows']} rows -> {target}")
    print(f"{len(files)} file(s) processed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
