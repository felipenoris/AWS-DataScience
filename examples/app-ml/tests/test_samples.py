"""scripts/make-samples.py: the committed sample is what the script writes from its seed, the
holdout holds other customers, and both labels are in both files."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def generator():
    return runpy.run_path(str(ROOT / "scripts" / "make-samples.py"), run_name="make_samples")


def test_the_committed_sample_is_the_scripts_output(generator, tmp_path):
    assert generator["main"](["--output", str(tmp_path)]) == 0
    for name in ("churn.csv", "holdout.csv"):
        assert (tmp_path / name).read_bytes() == (ROOT / "samples" / name).read_bytes(), name


def test_the_same_seed_writes_the_same_tables_and_another_does_not(generator):
    assert generator["tables"]() == generator["tables"]()
    assert generator["tables"](1) != generator["tables"]()


def test_the_holdout_is_other_customers_with_both_labels(generator):
    tables = generator["tables"]()
    churn = tables["churn.csv"].splitlines()
    holdout = tables["holdout.csv"].splitlines()
    assert churn[0] == holdout[0] == generator["HEADER"]
    assert not set(churn[1:]) & set(holdout[1:])
    for rows in (churn[1:], holdout[1:]):
        assert {row.rsplit(",", 1)[1] for row in rows} == {"0", "1"}
