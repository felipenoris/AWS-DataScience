"""The transformation and both entry points, offline.

python -m unittest discover -s examples/sandbox-orchestration/awsds-demo-job/tests
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from awsds_demo_job import __main__ as local  # noqa: E402
from awsds_demo_job import s3 as worker  # noqa: E402
from awsds_demo_job import transform  # noqa: E402

SAMPLE = Path(__file__).resolve().parents[2] / "samples" / "sample.csv"


class Transform(unittest.TestCase):
    def test_summary_of_the_sample(self):
        data = SAMPLE.read_bytes()
        summary = transform.summarize("sample.csv", data)
        self.assertEqual(summary["rows"], 10)
        self.assertEqual(summary["columns"], ["date", "region", "units", "unit_price"])
        self.assertEqual(sorted(summary["numeric"]), ["unit_price", "units"])
        self.assertEqual(summary["sha256"], hashlib.sha256(data).hexdigest())

    def test_a_column_with_text_is_not_numeric(self):
        summary = transform.summarize("x.csv", b"a,b\n1,x\n2,3\n")
        self.assertEqual(list(summary["numeric"]), ["a"])
        self.assertEqual(summary["numeric"]["a"], {"sum": 3.0, "min": 1.0, "max": 2.0})

    def test_result_name(self):
        self.assertEqual(transform.result_name("inbox/sales.CSV"), "sales.result.json")
        self.assertEqual(transform.result_name("notes.txt"), "notes.txt.result.json")


class LocalMode(unittest.TestCase):
    def test_every_csv_becomes_a_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp, "in"), Path(tmp, "out")
            src.mkdir()
            (src / "sample.csv").write_bytes(SAMPLE.read_bytes())
            self.assertEqual(local.main(["--input", str(src), "--output", str(dst)]), 0)
            result = json.loads((dst / "sample.result.json").read_text())
            self.assertEqual(result["rows"], 10)

    def test_no_csv_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(local.main(["--input", tmp, "--output", str(Path(tmp, "out"))]), 1)


class FakeS3:
    """The four calls `s3.run` makes, over a dict."""

    def __init__(self, objects):
        self.objects = dict(objects)
        self.order = []

    def get_paginator(self, _name):
        objects = self.objects

        class Pages:
            def paginate(self, Bucket, Prefix):
                yield {"Contents": [{"Key": k} for k in sorted(objects) if k.startswith(Prefix)]}

        return Pages()

    def get_object(self, Bucket, Key):
        data = self.objects[Key]

        class Body:
            def read(self):
                return data

        return {"Body": Body()}

    def put_object(self, Bucket, Key, Body):
        self.order.append(("put", Key))
        self.objects[Key] = Body

    def delete_object(self, Bucket, Key):
        self.order.append(("delete", Key))
        del self.objects[Key]


class WorkerMode(unittest.TestCase):
    def test_the_source_is_deleted_after_its_result_is_written(self):
        fake = FakeS3({"p/inbox/sample.csv": SAMPLE.read_bytes()})
        self.assertEqual(worker.run("b", "p/inbox", "p/outbox", client=fake), 1)
        kinds = [kind for kind, _key in fake.order]
        self.assertEqual(kinds, ["put", "delete"])
        self.assertNotIn("p/inbox/sample.csv", fake.objects)
        results = [k for k in fake.objects if k.endswith("/sample.result.json")]
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].startswith("p/outbox/"))


if __name__ == "__main__":
    unittest.main()
