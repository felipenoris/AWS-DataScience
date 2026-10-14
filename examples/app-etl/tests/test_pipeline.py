"""The transformation and the command, offline, in the project's environment: `uv run pytest`."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from app_etl import __main__ as command
from app_etl import pipeline

SAMPLE = Path(__file__).resolve().parents[1] / "samples" / "trades.csv"


def test_the_sample_summary():
    data = SAMPLE.read_bytes()
    summary = pipeline.summarize("trades.csv", data, pipeline.read(data))
    assert summary["rows"] == 10
    assert summary["columns"] == ["trade_date", "desk", "instrument", "quantity", "price"]
    assert summary["numeric"]["quantity"] == {"sum": 1530, "min": 30, "max": 500}
    assert summary["numeric"]["price"]["sum"] == pytest.approx(701.24)
    assert summary["numeric"]["price"]["min"] == pytest.approx(1.08)
    assert summary["sha256"] == hashlib.sha256(data).hexdigest()


def test_a_text_or_date_column_is_not_summarized():
    data = b"day,label,n\n2026-10-01,x,1\n2026-10-02,y,2\n"
    summary = pipeline.summarize("x.csv", data, pipeline.read(data))
    assert list(summary["numeric"]) == ["n"]


def test_the_summary_renders_sorted_and_parses():
    data = SAMPLE.read_bytes()
    rendered = pipeline.render(pipeline.summarize("trades.csv", data, pipeline.read(data)))
    assert rendered.endswith("}\n")
    parsed = json.loads(rendered)
    assert list(parsed) == sorted(parsed)


def test_process_writes_a_table_and_a_summary(tmp_path):
    summary = pipeline.process(SAMPLE, tmp_path)
    table = pq.read_table(tmp_path / "trades.parquet")
    assert table.num_rows == summary["rows"] == 10
    assert table.schema.field("quantity").type == pa.int64()
    assert table.schema.field("desk").type == pa.string()
    assert json.loads((tmp_path / "trades.summary.json").read_text()) == summary


def test_stem():
    assert pipeline.stem("trades.CSV") == "trades"
    assert pipeline.stem("notes.txt") == "notes.txt"


def test_the_command_processes_every_csv(tmp_path, capsys):
    source, target = tmp_path / "in", tmp_path / "out"
    (source / "nested").mkdir(parents=True)
    (source / "nested" / "trades.csv").write_bytes(SAMPLE.read_bytes())
    (source / "readme.txt").write_text("not a CSV")
    assert command.main(["--input", str(source), "--output", str(target)]) == 0
    assert sorted(p.name for p in target.iterdir()) == ["trades.parquet", "trades.summary.json"]
    out = capsys.readouterr().out
    assert "1 file(s) processed" in out
    assert "UST10Y" not in out


def test_the_command_fails_with_no_csv(tmp_path):
    assert command.main(["--input", str(tmp_path), "--output", str(tmp_path / "out")]) == 1
