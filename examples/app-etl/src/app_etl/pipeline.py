"""The transformation: one CSV becomes a Parquet table and a JSON summary.

pyarrow reads the CSV and infers each column's type. The table keeps every row and those types. The
summary carries the row count, the column names, the sum, minimum and maximum of every integer or
floating-point column, and the input's sha256, so a summary names the exact bytes it describes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.parquet as pq


def read(data: bytes) -> pa.Table:
    """The CSV's rows as a table, each column's type inferred by pyarrow."""
    return pacsv.read_csv(pa.BufferReader(data))


def summarize(name: str, data: bytes, table: pa.Table) -> dict:
    """The summary of one CSV, given its name, its bytes and the table read from them."""
    numeric = {}
    for field in table.schema:
        if pa.types.is_integer(field.type) or pa.types.is_floating(field.type):
            column = table.column(field.name)
            numeric[field.name] = {
                "sum": pc.sum(column).as_py(),
                "min": pc.min(column).as_py(),
                "max": pc.max(column).as_py(),
            }
    return {
        "input": name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "rows": table.num_rows,
        "columns": table.column_names,
        "numeric": numeric,
    }


def render(summary: dict) -> str:
    """The summary as JSON, keys sorted, one trailing newline."""
    return json.dumps(summary, indent=2, sort_keys=True) + "\n"


def stem(name: str) -> str:
    """`trades.csv` -> `trades`; a name without the suffix is kept whole."""
    return name[: -len(".csv")] if name.lower().endswith(".csv") else name


def process(path: Path, output: Path) -> dict:
    """Write `<stem>.parquet` and `<stem>.summary.json` into `output`, and return the summary."""
    data = path.read_bytes()
    table = read(data)
    summary = summarize(path.name, data, table)
    pq.write_table(table, output / f"{stem(path.name)}.parquet")
    (output / f"{stem(path.name)}.summary.json").write_text(render(summary))
    return summary
