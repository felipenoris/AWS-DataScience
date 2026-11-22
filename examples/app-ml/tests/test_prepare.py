"""app_ml.prepare over the committed sample and over tables built here: XGBoost's layout in the
training mode, the features and the labels in the scoring mode, each mode reading its own file, and
the refusals of a table that is not the churn table."""

from __future__ import annotations

from pathlib import Path

import pytest

from app_ml import prepare

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
HEADER = "tenure_months,monthly_charges,support_calls,contract_months,late_payments,churned"


def lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def test_the_training_mode_writes_xgboosts_layout_one_row_in_five_to_validation(tmp_path):
    assert prepare.main(["train", "--input", str(SAMPLES), "--output", str(tmp_path)]) == 0
    train = lines(tmp_path / "train" / "train.csv")
    validation = lines(tmp_path / "validation" / "validation.csv")
    rows = lines(SAMPLES / "churn.csv")[1:]
    assert (len(train), len(validation)) == (320, 80)
    first = rows[0].split(",")
    assert train[0] == ",".join([first[-1], *first[:-1]])
    fifth = rows[4].split(",")
    assert validation[0] == ",".join([fifth[-1], *fifth[:-1]])
    assert all(line.split(",")[0] in ("0", "1") and line.count(",") == 5 for line in train)
    assert not any(line.startswith("tenure") for line in train + validation)


def test_the_scoring_mode_writes_the_features_and_the_labels_in_one_order(tmp_path):
    assert prepare.main(["score", "--input", str(SAMPLES), "--output", str(tmp_path)]) == 0
    batch = lines(tmp_path / "batch" / "batch.csv")
    labels = lines(tmp_path / "labels" / "labels.csv")
    rows = lines(SAMPLES / "holdout.csv")[1:]
    assert len(batch) == len(labels) == len(rows) == 200
    assert batch == [row.rsplit(",", 1)[0] for row in rows]
    assert labels == [row.rsplit(",", 1)[1] for row in rows]


def test_each_mode_reads_its_own_file_alone(tmp_path):
    source = tmp_path / "in"
    source.mkdir()
    (source / "holdout.csv").write_text(f"{HEADER}\n1,20.00,0,1,0,1\n")
    assert prepare.main(["train", "--input", str(source), "--output", str(tmp_path / "o")]) == 1
    (source / "churn.csv").write_text(
        f"{HEADER}\n" + "".join(f"{i},20.00,0,1,0,0\n" for i in range(5))
    )
    assert prepare.main(["train", "--input", str(source), "--output", str(tmp_path / "o")]) == 0
    assert lines(tmp_path / "o" / "validation" / "validation.csv") == ["0,4,20.00,0,1,0"]


@pytest.mark.parametrize(
    ("table", "refusal"),
    [
        ("tenure_months,churned\n1,0\n", "has no column monthly_charges"),
        (f"{HEADER}\n1,20.00,0,1,0,2\n", "line 2: churned is not 0 or 1"),
        (f"{HEADER}\n1,twenty,0,1,0,1\n", "line 2: monthly_charges is not a number"),
        (f"{HEADER}\n", "has no row"),
    ],
)
def test_a_table_that_is_not_the_churn_table_is_refused(tmp_path, capsys, table, refusal):
    (tmp_path / "churn.csv").write_text(table)
    assert prepare.main(["train", "--input", str(tmp_path), "--output", str(tmp_path / "o")]) == 1
    assert refusal in capsys.readouterr().err
    assert not (tmp_path / "o").exists()


def test_it_prints_counts_and_never_a_value(tmp_path, capsys):
    prepare.main(["score", "--input", str(SAMPLES), "--output", str(tmp_path)])
    out = capsys.readouterr().out
    assert "holdout.csv: batch 200 row(s), labels 200 row(s)" in out
    assert lines(SAMPLES / "holdout.csv")[1] not in out
