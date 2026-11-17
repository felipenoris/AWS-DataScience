"""app_ml_tasks.track over a double of the MLflow client and a stubbed S3: the run the pointer names
logged as one MLflow run, the refusal of a stage without an MLflow App before any read, and the exit
code when the archive's client is missing."""

from __future__ import annotations

import io
import json
import sys
from types import SimpleNamespace

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from app_ml_tasks import track

SERVER = "arn:aws:sagemaker:us-west-2:000000000000:mlflow-app/app-double"
POINTER = "s3://projects-bucket/shared/app-ml/models/last-run.json"
EVALUATION_URI = "s3://projects-bucket/shared/app-ml/models/job/evaluation.json"
RUN = {
    "training_job": "app-ml-train-20261117T120000",
    "model_data": "s3://projects-bucket/shared/app-ml/models/job/output/model.tar.gz",
    "training_image": "registry/sagemaker-xgboost@sha256:" + "a" * 64,
    "hyperparameters": {"max_depth": "3", "num_round": "50"},
    "auc": 0.84,
    "evaluation": EVALUATION_URI,
}
EVALUATION = {"binary_classification_metrics": {"auc": {"value": 0.84}}}


class MLflow:
    """The calls track makes, recorded in order."""

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return lambda *args, **kwargs: self.calls.append((name, args, kwargs))

    def start_run(self, **kwargs):
        self.calls.append(("start_run", (), kwargs))
        mlflow = self

        class Run:
            info = SimpleNamespace(run_id="run-1")

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                mlflow.calls.append(("end_run", (), {}))

        return Run()


def stubbed_s3(*documents: tuple[str, dict]):
    s3 = boto3.client(
        "s3", region_name="us-west-2", aws_access_key_id="stub", aws_secret_access_key="stub"
    )
    stub = Stubber(s3)
    for uri, document in documents:
        bucket, key = uri.removeprefix("s3://").split("/", 1)
        data = json.dumps(document).encode()
        stub.add_response(
            "get_object",
            {"Body": StreamingBody(io.BytesIO(data), len(data))},
            {"Bucket": bucket, "Key": key},
        )
    stub.activate()
    return s3, stub


def test_the_run_is_logged_with_its_parameters_metric_tags_and_evaluation(capsys):
    s3, stub = stubbed_s3((POINTER, RUN), (EVALUATION_URI, EVALUATION))
    mlflow = MLflow()
    assert track.track(s3, mlflow, POINTER, f" {SERVER} ") == "run-1"
    stub.assert_no_pending_responses()
    assert mlflow.calls == [
        ("set_tracking_uri", (SERVER,), {}),
        ("set_experiment", ("app-ml",), {}),
        ("start_run", (), {"run_name": RUN["training_job"]}),
        ("log_params", (RUN["hyperparameters"],), {}),
        ("log_metric", ("validation_auc", 0.84), {}),
        (
            "set_tags",
            (
                {
                    "training_job": RUN["training_job"],
                    "model_data": RUN["model_data"],
                    "training_image": RUN["training_image"],
                    "evaluation": EVALUATION_URI,
                },
            ),
            {},
        ),
        ("log_dict", (EVALUATION, "evaluation.json"), {}),
        ("end_run", (), {}),
    ]
    assert "as run run-1 of the experiment app-ml: validation_auc 0.84" in capsys.readouterr().out


@pytest.mark.parametrize(
    "server", ["none", "", "arn:aws:sagemaker:us-west-2:000000000000:model/app-ml"]
)
def test_a_stage_without_an_mlflow_app_is_refused_before_any_read(server):
    s3, stub = stubbed_s3()
    mlflow = MLflow()
    with pytest.raises(RuntimeError, match="is not an MLflow App's ARN"):
        track.track(s3, mlflow, POINTER, server)
    assert mlflow.calls == []
    stub.assert_no_pending_responses()


def test_main_logs_the_run_with_the_workers_clients(monkeypatch):
    s3, stub = stubbed_s3((POINTER, RUN), (EVALUATION_URI, EVALUATION))
    mlflow = MLflow()
    monkeypatch.setitem(sys.modules, "mlflow", mlflow)
    monkeypatch.setattr(boto3, "client", lambda service: s3)
    assert track.main(["--run", POINTER, "--tracking-server", SERVER]) == 0
    stub.assert_no_pending_responses()
    assert ("set_experiment", ("app-ml",), {}) in mlflow.calls


def test_main_exits_1_without_the_archives_mlflow_client(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "mlflow", None)
    assert track.main(["--run", POINTER, "--tracking-server", SERVER]) == 1
    assert "track: " in capsys.readouterr().err


def test_main_exits_1_on_a_refusal(monkeypatch, capsys):
    s3, stub = stubbed_s3()
    monkeypatch.setitem(sys.modules, "mlflow", MLflow())
    monkeypatch.setattr(boto3, "client", lambda service: s3)
    assert track.main(["--run", POINTER, "--tracking-server", "none"]) == 1
    assert "MLFLOW_APP_ARN 'none'" in capsys.readouterr().err
    stub.assert_no_pending_responses()
