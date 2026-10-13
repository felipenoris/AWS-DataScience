"""`python -m app_etl --input DIR --output DIR`: the processing job's command.

Every CSV under --input becomes `<name>.parquet` and `<name>.summary.json` in --output. The job
runs with no network, so the command first prints the interpreter and where pyarrow was imported
from; a failed import ends it before any file is read.

What it prints lands in /aws/sagemaker/ProcessingJobs, which other roles in the account can read,
so it prints versions, counts and file names, never a cell of data.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app-etl", description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, type=Path, help="directory holding the CSVs")
    parser.add_argument("--output", required=True, type=Path, help="directory for the results")
    args = parser.parse_args(argv)

    print(f"app-etl {__version__}, python {sys.version.split()[0]} at {sys.executable}")
    try:
        import pyarrow

        from . import pipeline
    except ImportError as exc:
        print(f"pyarrow: import failed: {exc!r}", file=sys.stderr)
        return 1
    print(f"pyarrow {pyarrow.__version__} from {Path(pyarrow.__file__).parent}")

    files = sorted(p for p in args.input.rglob("*") if p.is_file() and p.suffix.lower() == ".csv")
    if not files:
        print(f"no CSV under {args.input}", file=sys.stderr)
        return 1
    args.output.mkdir(parents=True, exist_ok=True)
    for path in files:
        summary = pipeline.process(path, args.output)
        print(f"{path.name}: {summary['rows']} rows -> {pipeline.stem(path.name)}.parquet")
    print(f"{len(files)} file(s) processed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
