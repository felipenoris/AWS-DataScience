"""`python -m awsds_demo_deps --input DIR --output DIR`: the processing job's command.

Every CSV under --input becomes `<name>.summary.json` and `<name>.parquet` in --output. The job
reaches no network, so each dependency is either in the house environment or in the code input,
and the command first prints where each one was imported from, its extension module included.
A failed import is printed and ends the command before any file is read.

What it prints lands in /aws/sagemaker/ProcessingJobs, which every project role in the account
can read, so it prints the interpreter, versions, counts and paths, never a cell of data.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

# Each dependency, and the extension module that holds its compiled code (None: pure Python).
DEPENDENCIES = {"petl": None, "msgspec": "msgspec._core", "pyarrow": "pyarrow.lib"}


def report_dependencies() -> bool:
    """Print each dependency's version and where it was imported from; False if one failed."""
    ok = True
    for name, extension in DEPENDENCIES.items():
        try:
            module = importlib.import_module(name)
            line = (
                f"{name} {getattr(module, '__version__', '?')} from {Path(module.__file__).parent}"
            )
            if extension:
                line += f", extension {Path(importlib.import_module(extension).__file__).name}"
        except Exception as exc:  # the failure is the reading: print it, then stop
            line = f"{name}: import failed: {exc!r}"
            ok = False
        print(line)
    return ok


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="awsds_demo_deps")
    parser.add_argument("--input", required=True, type=Path, help="directory holding the CSVs")
    parser.add_argument("--output", required=True, type=Path, help="directory for the results")
    args = parser.parse_args(argv)

    print(f"python {sys.version.split()[0]} at {sys.executable}")
    if not report_dependencies():
        return 1
    from . import transform

    files = sorted(p for p in args.input.rglob("*") if p.is_file() and p.suffix.lower() == ".csv")
    if not files:
        print(f"no CSV under {args.input}", file=sys.stderr)
        return 1
    args.output.mkdir(parents=True, exist_ok=True)
    for path in files:
        data = path.read_bytes()
        summary = transform.summarize(path.name, data)
        stem = transform.stem(path.name)
        (args.output / f"{stem}.summary.json").write_bytes(transform.render(summary))
        (args.output / f"{stem}.parquet").write_bytes(transform.to_parquet(data))
        print(f"{path.name}: {summary['rows']} rows -> {stem}.summary.json, {stem}.parquet")
    print(f"{len(files)} file(s) processed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
