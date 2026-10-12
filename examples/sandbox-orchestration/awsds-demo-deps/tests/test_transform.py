"""The transformation and the command, offline, in the project's own environment.

uv run --directory examples/sandbox-orchestration/awsds-demo-deps python -m unittest discover -s tests
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from awsds_demo_deps import __main__ as command
from awsds_demo_deps import transform

SAMPLE = Path(__file__).resolve().parents[2] / "samples" / "sample.csv"


class Transform(unittest.TestCase):
    def test_summary_of_the_sample(self):
        data = SAMPLE.read_bytes()
        summary = transform.summarize("sample.csv", data)
        self.assertEqual(summary["rows"], 10)
        self.assertEqual(summary["columns"], ["date", "region", "units", "unit_price"])
        self.assertEqual(summary["numeric"]["units"], {"sum": 96.0, "min": 4.0, "max": 15.0})
        self.assertEqual(summary["numeric"]["unit_price"], {"sum": 98.75, "min": 9.5, "max": 10.25})
        self.assertEqual(summary["sha256"], hashlib.sha256(data).hexdigest())

    def test_a_column_with_text_is_not_numeric(self):
        summary = transform.summarize("x.csv", b"a,b\n1,x\n2,3\n")
        self.assertEqual(list(summary["numeric"]), ["a"])
        self.assertEqual(summary["numeric"]["a"], {"sum": 3.0, "min": 1.0, "max": 2.0})

    def test_the_summary_renders_sorted_and_parses(self):
        rendered = transform.render(transform.summarize("sample.csv", SAMPLE.read_bytes()))
        self.assertTrue(rendered.endswith(b"}\n"))
        parsed = json.loads(rendered)
        self.assertEqual(list(parsed), sorted(parsed))
        self.assertEqual(parsed["rows"], 10)

    def test_the_table_keeps_rows_and_types(self):
        table = pq.read_table(pa.BufferReader(transform.to_parquet(SAMPLE.read_bytes())))
        self.assertEqual(table.num_rows, 10)
        self.assertEqual(table.schema.field("units").type, pa.float64())
        self.assertEqual(table.schema.field("region").type, pa.string())
        self.assertEqual(sum(table.column("units").to_pylist()), 96.0)

    def test_stem(self):
        self.assertEqual(transform.stem("inbox/sales.CSV"), "sales")
        self.assertEqual(transform.stem("notes.txt"), "notes.txt")


class Command(unittest.TestCase):
    def test_every_csv_becomes_a_summary_and_a_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp, "in"), Path(tmp, "out")
            src.mkdir()
            (src / "sample.csv").write_bytes(SAMPLE.read_bytes())
            self.assertEqual(command.main(["--input", str(src), "--output", str(dst)]), 0)
            self.assertEqual(json.loads((dst / "sample.summary.json").read_bytes())["rows"], 10)
            self.assertEqual(pq.read_table(dst / "sample.parquet").num_rows, 10)

    def test_no_csv_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(command.main(["--input", tmp, "--output", str(Path(tmp, "out"))]), 1)

    def test_a_failed_import_is_reported_and_stops_the_command(self):
        saved = dict(command.DEPENDENCIES)
        command.DEPENDENCIES["awsds_no_such_module"] = None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(command.main(["--input", tmp, "--output", tmp]), 1)
        finally:
            command.DEPENDENCIES.clear()
            command.DEPENDENCIES.update(saved)


if __name__ == "__main__":
    unittest.main()
