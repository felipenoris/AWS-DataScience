"""The transformation: one CSV in, one JSON summary out.

The summary carries the row count, the column names, the sum, minimum and maximum of every
column whose cells are all numbers, and the input's sha256, so a result can be checked
against the file it came from without reading either one into a log.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json


def summarize(name: str, data: bytes) -> dict:
    """The summary of one CSV, given its name and its bytes."""
    reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
    rows = list(reader)
    columns = list(reader.fieldnames or [])
    numeric = {}
    for column in columns:
        values = []
        for row in rows:
            cell = (row.get(column) or "").strip()
            try:
                values.append(float(cell))
            except ValueError:
                values = []
                break
        if values:
            numeric[column] = {"sum": sum(values), "min": min(values), "max": max(values)}
    return {
        "input": name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "rows": len(rows),
        "columns": columns,
        "numeric": numeric,
    }


def result_name(input_name: str) -> str:
    """`inbox/sales.csv` -> `sales.result.json`."""
    stem = input_name.rsplit("/", 1)[-1]
    if stem.lower().endswith(".csv"):
        stem = stem[: -len(".csv")]
    return f"{stem}.result.json"


def render(summary: dict) -> bytes:
    return (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8")
