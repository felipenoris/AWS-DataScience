"""The transformation: one CSV in, a JSON summary and a Parquet table out.

The summary carries what awsds-demo-job's does: the row count, the column names, the sum, minimum
and maximum of every column whose cells are all numbers, and the input's sha256. The table holds
the same rows, a numeric column as float64 and every other one as text.
"""

from __future__ import annotations

import hashlib

import msgspec
import petl
import pyarrow as pa
import pyarrow.parquet as pq

ENCODER = msgspec.json.Encoder(order="sorted")


def read(data: bytes):
    """The CSV as a petl table: a header row, then one record per line."""
    return petl.fromcsv(petl.MemorySource(data), encoding="utf-8")


def numeric_columns(table) -> dict:
    """Column -> its values as floats, for every column whose cells all parse as numbers."""
    found = {}
    for column in petl.header(table):
        values = []
        for cell in petl.values(table, column):
            try:
                values.append(float((cell or "").strip()))
            except ValueError:
                values = []
                break
        if values:
            found[column] = values
    return found


def summarize(name: str, data: bytes) -> dict:
    """The summary of one CSV, given its name and its bytes."""
    table = read(data)
    numeric = {
        column: {"sum": sum(values), "min": min(values), "max": max(values)}
        for column, values in numeric_columns(table).items()
    }
    return {
        "input": name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "rows": petl.nrows(table),
        "columns": list(petl.header(table)),
        "numeric": numeric,
    }


def to_parquet(data: bytes) -> bytes:
    """The CSV's rows as one Parquet file."""
    table = read(data)
    numeric = numeric_columns(table)
    arrays = {}
    for column in petl.header(table):
        if column in numeric:
            arrays[column] = pa.array(numeric[column], type=pa.float64())
        else:
            arrays[column] = pa.array(list(petl.values(table, column)), type=pa.string())
    sink = pa.BufferOutputStream()
    pq.write_table(pa.table(arrays), sink)
    return sink.getvalue().to_pybytes()


def stem(input_name: str) -> str:
    """`inbox/sales.csv` -> `sales`."""
    base = input_name.rsplit("/", 1)[-1]
    return base[: -len(".csv")] if base.lower().endswith(".csv") else base


def render(summary: dict) -> bytes:
    return msgspec.json.format(ENCODER.encode(summary), indent=2) + b"\n"
