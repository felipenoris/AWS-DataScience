"""The worker's Python tasks over boto3 clients stubbed with botocore's Stubber, at the version the
worker carries (1.43.1): each call in its order, each request checked against the service model, and
the model's and the package's requests asserted with their network, isolation, tag and status."""

from __future__ import annotations

import hashlib
import inspect
import io
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import boto3
import botocore
import pytest
from botocore.response import StreamingBody
from botocore.stub import ANY, Stubber

import app_ml_tasks
from app_ml_tasks import common, registry, scoring, training

ROOT = Path(__file__).resolve().parents[1]
BUCKET = "projects-bucket"
SHARED = f"s3://{BUCKET}/domain/project/shared/"
MODELS = f"{SHARED}app-ml/models/"
JOB = "app-ml-train-20261117T120000"
IMAGE = "000000000000.dkr.ecr.us-west-2.amazonaws.com/sagemaker-xgboost@sha256:" + "a" * 64
ARCHIVE = b"\x1f\x8b a model archive"
DIGEST = hashlib.sha256(ARCHIVE).hexdigest()
GROUP = "awsds-staging-model-app-ml"
VERSION = f"arn:aws:sagemaker:us-west-2:000000000000:model-package/{GROUP}/1"
ROLE = "arn:aws:iam::000000000000:role/project-role"
NOW = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)
EVALUATION = {
    "version": 0.0,
    "binary_classification_metrics": {"auc": {"value": 0.84, "standard_deviation": "NaN"}},
}


def test_the_stubs_check_against_the_workers_botocore():
    assert botocore.__version__ == "1.43.1"


def client(service: str):
    return boto3.client(
        service,
        region_name="us-west-2",
        aws_access_key_id="stub",
        aws_secret_access_key="stub",
    )


def body(data: bytes) -> dict:
    return {"Body": StreamingBody(io.BytesIO(data), len(data))}


def key(uri: str) -> dict:
    bucket, name = common.split_uri(uri)
    return {"Bucket": bucket, "Key": name}


class Clients:
    """An S3 and a SageMaker client, each under a Stubber, and every object written to S3."""

    def __init__(self):
        self.s3, self.sagemaker = client("s3"), client("sagemaker")
        self.s3_stub, self.sm_stub = Stubber(self.s3), Stubber(self.sagemaker)
        self.written = {}
        self.s3.meta.events.register("before-parameter-build.s3.PutObject", self.record)

    def record(self, params, **kwargs):
        self.written[f"s3://{params['Bucket']}/{params['Key']}"] = params["Body"]

    def read(self, uri: str, data: bytes):
        self.s3_stub.add_response("get_object", body(data), key(uri))

    def write(self, uri: str, data=ANY, content_type: str | None = None):
        expected = {**key(uri), "Body": data}
        if content_type:
            expected["ContentType"] = content_type
        self.s3_stub.add_response("put_object", {"ETag": '"e"'}, expected)

    def call(self, operation: str, response: dict, expected: dict | None = None):
        self.sm_stub.add_response(operation, response, expected)

    def __enter__(self):
        self.s3_stub.activate()
        self.sm_stub.activate()
        return self

    def __exit__(self, *exc):
        if exc[0] is None:
            self.s3_stub.assert_no_pending_responses()
            self.sm_stub.assert_no_pending_responses()
        self.s3_stub.deactivate()
        self.sm_stub.deactivate()


@pytest.fixture
def aws():
    return Clients()


def described_job(auc: float = 0.84, status: str = "Completed") -> dict:
    return {
        "TrainingJobName": JOB,
        "TrainingJobArn": f"arn:aws:sagemaker:us-west-2:000000000000:training-job/{JOB}",
        "ModelArtifacts": {"S3ModelArtifacts": f"{MODELS}{JOB}/output/model.tar.gz"},
        "TrainingJobStatus": status,
        "SecondaryStatus": "Completed",
        "AlgorithmSpecification": {"TrainingImage": IMAGE, "TrainingInputMode": "File"},
        "HyperParameters": {"objective": "binary:logistic", "eval_metric": "auc"},
        "StoppingCondition": {"MaxRuntimeInSeconds": 1800},
        "CreationTime": NOW,
        "FinalMetricDataList": [
            {"MetricName": "train:auc", "Value": 0.93, "Timestamp": NOW},
            {"MetricName": "validation:auc", "Value": auc, "Timestamp": NOW},
        ],
    }


# The train task's XCom as the worker renders it into a template: the JSON of the operator's dict.
TRAINED = json.dumps({"Training": {"TrainingJobName": JOB, "TrainingJobStatus": "Completed"}})


def model_json(**changes) -> dict:
    return {
        "application": "app-ml",
        "training_job": JOB,
        "serving_image": IMAGE,
        "sha256": DIGEST,
        "auc": 0.84,
        "training_source": "f" * 64,
        **changes,
    }


# ------------------------------------------------------------------------------ the shared helpers


def test_split_uri_and_folder():
    assert common.split_uri("s3://b/a/k.json") == ("b", "a/k.json")
    assert common.folder("s3://b/a") == common.folder("s3://b/a/") == "s3://b/a/"
    with pytest.raises(ValueError, match="not an s3:// URI"):
        common.split_uri("https://b/a")


@pytest.mark.parametrize(
    "value",
    [{"a": 1}, '{"a": 1}', json.dumps('{"a": 1}'), "{'a': 1}"],
)
def test_an_xcom_is_decoded_from_json_twice_encoded_text_a_dict_or_a_literal(value):
    assert common.decode_xcom(value, "t") == {"a": 1}


def test_an_xcom_that_is_not_a_mapping_fails_naming_the_task():
    with pytest.raises(RuntimeError, match="the t task's XCom is neither JSON nor a literal"):
        common.decode_xcom("not json", "t")
    with pytest.raises(RuntimeError, match="the t task's XCom is a list"):
        common.decode_xcom("[1]", "t")


@pytest.mark.parametrize(
    ("scores", "labels", "expected"),
    [
        ([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1], 1.0),
        ([0.9, 0.8, 0.2, 0.1], [0, 0, 1, 1], 0.0),
        ([0.5, 0.5, 0.5, 0.5], [0, 1, 0, 1], 0.5),
        ([0.1, 0.4, 0.35, 0.8], [0, 0, 1, 1], 0.75),
        ([0.2, 0.3, 0.3, 0.9], [0, 0, 1, 1], 0.875),
    ],
)
def test_the_auc_by_rank(scores, labels, expected):
    assert common.auc_by_rank(scores, labels) == pytest.approx(expected)


def test_the_auc_needs_both_labels_and_one_score_per_label():
    with pytest.raises(RuntimeError, match="both labels"):
        common.auc_by_rank([0.1, 0.2], [1, 1])
    with pytest.raises(RuntimeError, match="2 score"):
        common.auc_by_rank([0.1, 0.2], [1])


@pytest.mark.parametrize("value", ["0.5", "1", "x", ""])
def test_a_threshold_off_the_open_interval_fails(value):
    with pytest.raises(RuntimeError, match="MIN_AUC"):
        common.threshold(value)


# ----------------------------------------------------------------------------------- app-ml-train


def test_evaluate_writes_the_evaluation_and_the_pointer(aws, capsys):
    aws.call("describe_training_job", described_job(), {"TrainingJobName": JOB})
    aws.write(f"{MODELS}{JOB}/evaluation.json", content_type="application/json")
    aws.write(f"{MODELS}last-run.json", content_type="application/json")
    with aws:
        run = training.evaluate_job(aws.sagemaker, aws.s3, TRAINED, MODELS, "0.70")
    evaluation = json.loads(aws.written[f"{MODELS}{JOB}/evaluation.json"])
    assert evaluation["binary_classification_metrics"]["auc"]["value"] == 0.84
    assert evaluation["awsds"]["training_job"] == JOB
    assert json.loads(aws.written[f"{MODELS}last-run.json"]) == run
    assert run == {
        "training_job": JOB,
        "model_data": f"{MODELS}{JOB}/output/model.tar.gz",
        "training_image": IMAGE,
        "hyperparameters": {"objective": "binary:logistic", "eval_metric": "auc"},
        "auc": 0.84,
        "evaluation": f"{MODELS}{JOB}/evaluation.json",
    }
    assert f"{JOB}: validation:auc 0.84, MIN_AUC 0.7" in capsys.readouterr().out


def test_evaluate_records_a_run_under_min_auc_and_fails(aws):
    aws.call("describe_training_job", described_job(auc=0.61), {"TrainingJobName": JOB})
    aws.write(f"{MODELS}{JOB}/evaluation.json", content_type="application/json")
    aws.write(f"{MODELS}last-run.json", content_type="application/json")
    with aws, pytest.raises(RuntimeError, match="0.61 is under MIN_AUC 0.7"):
        training.evaluate_job(aws.sagemaker, aws.s3, TRAINED, MODELS, "0.70")


def test_evaluate_refuses_a_job_that_did_not_complete(aws):
    aws.call("describe_training_job", described_job(status="Failed"), {"TrainingJobName": JOB})
    with aws, pytest.raises(RuntimeError, match="is Failed, not Completed"):
        training.evaluate_job(aws.sagemaker, aws.s3, TRAINED, MODELS, "0.70")


def test_publish_copies_the_archive_and_the_evaluation_then_writes_model_json(aws):
    evaluation = json.dumps(EVALUATION).encode()
    aws.call("describe_training_job", described_job(), {"TrainingJobName": JOB})
    aws.read(f"{MODELS}{JOB}/evaluation.json", evaluation)
    aws.read(f"{MODELS}{JOB}/output/model.tar.gz", ARCHIVE)
    aws.write(f"{MODELS}latest/model.tar.gz", ARCHIVE)
    aws.write(f"{MODELS}latest/evaluation.json", evaluation, "application/json")
    aws.write(f"{MODELS}latest/model.json", content_type="application/json")
    with aws:
        model = training.publish_model(
            aws.sagemaker, aws.s3, TRAINED, MODELS, IMAGE, "f" * 64, "0.70"
        )
    assert json.loads(aws.written[f"{MODELS}latest/model.json"]) == model
    assert list(aws.written)[-1] == f"{MODELS}latest/model.json"
    assert model["sha256"] == DIGEST
    assert model["size_bytes"] == len(ARCHIVE)
    assert model["training_source"] == "f" * 64
    assert model["training_image"] == model["serving_image"] == IMAGE
    assert model["training_job"] == JOB and model["auc"] == 0.84


@pytest.mark.parametrize("source", ["", "none", "  "])
def test_publish_refuses_a_deploy_without_its_training_source(aws, source):
    aws.call("describe_training_job", described_job(), {"TrainingJobName": JOB})
    with aws, pytest.raises(RuntimeError, match="TRAINING_SOURCE is empty or none"):
        training.publish_model(aws.sagemaker, aws.s3, TRAINED, MODELS, IMAGE, source, "0.70")


def test_publish_refuses_a_serving_image_without_its_digest_before_any_write(aws):
    aws.call("describe_training_job", described_job(), {"TrainingJobName": JOB})
    with aws, pytest.raises(RuntimeError, match="names no digest"):
        training.publish_model(
            aws.sagemaker, aws.s3, TRAINED, MODELS, "registry/xgboost:3.0-5", "f" * 64, "0.70"
        )
    assert not aws.written


def test_publish_refuses_an_evaluation_under_min_auc_before_any_write(aws):
    evaluation = json.dumps(EVALUATION).encode()
    aws.call("describe_training_job", described_job(), {"TrainingJobName": JOB})
    aws.read(f"{MODELS}{JOB}/evaluation.json", evaluation)
    with aws, pytest.raises(RuntimeError, match="0.84 is under MIN_AUC 0.9, nothing published"):
        training.publish_model(aws.sagemaker, aws.s3, TRAINED, MODELS, IMAGE, "f" * 64, "0.90")
    assert not aws.written


# -------------------------------------------------------------------------------- app-ml-register

PREFIX = f"{SHARED}app-ml/bundle/model/"
COPY = f"{MODELS}sha256/{DIGEST}/"


def summary(description: str, status: str = "PendingManualApproval", arn: str = VERSION) -> dict:
    return {
        "ModelPackageArn": arn,
        "ModelPackageGroupName": GROUP,
        "ModelPackageDescription": description,
        "CreationTime": NOW,
        "ModelPackageStatus": "Completed",
        "ModelApprovalStatus": status,
    }


def test_register_proposes_the_candidate_pending_manual_approval(aws, capsys):
    evaluation = json.dumps(EVALUATION).encode()
    aws.read(f"{PREFIX}model.json", json.dumps(model_json()).encode())
    aws.read(f"{PREFIX}model.tar.gz", ARCHIVE)
    aws.call(
        "list_model_packages",
        {"ModelPackageSummaryList": [summary("app-ml sha256:" + "0" * 64)]},
        {"ModelPackageGroupName": GROUP},
    )
    aws.write(f"{COPY}model.tar.gz", ARCHIVE)
    aws.read(f"{PREFIX}evaluation.json", evaluation)
    aws.write(f"{COPY}evaluation.json", evaluation, "application/json")
    request = {
        "ModelPackageGroupName": GROUP,
        "ModelPackageDescription": f"app-ml sha256:{DIGEST}, trained by {JOB}",
        "ModelApprovalStatus": "PendingManualApproval",
        "InferenceSpecification": {
            "Containers": [{"Image": IMAGE, "ModelDataUrl": f"{COPY}model.tar.gz"}],
            "SupportedContentTypes": ["text/csv"],
            "SupportedResponseMIMETypes": ["text/csv"],
            "SupportedTransformInstanceTypes": ["ml.m5.large"],
        },
        "ModelMetrics": {
            "ModelQuality": {
                "Statistics": {
                    "ContentType": "application/json",
                    "S3Uri": f"{COPY}evaluation.json",
                }
            }
        },
        "CustomerMetadataProperties": {
            "sha256": DIGEST,
            "training_job": JOB,
            "source_prefix": PREFIX,
            "training_source": "f" * 64,
            "validation_auc": "0.84",
        },
    }
    aws.call("create_model_package", {"ModelPackageArn": VERSION}, request)
    with aws:
        result = registry.register_model(aws.sagemaker, aws.s3, PREFIX, GROUP, MODELS, IMAGE)
    assert result == {
        "registered": True,
        "sha256": DIGEST,
        "version": VERSION,
        "training_job": JOB,
    }
    assert f"proposed {VERSION}: sha256 {DIGEST}" in capsys.readouterr().out


def test_register_refuses_an_archive_whose_hash_differs_and_calls_nothing(aws):
    aws.read(f"{PREFIX}model.json", json.dumps(model_json()).encode())
    aws.read(f"{PREFIX}model.tar.gz", ARCHIVE + b" changed")
    with aws, pytest.raises(RuntimeError, match=f"and model.json names {DIGEST}"):
        registry.register_model(aws.sagemaker, aws.s3, PREFIX, GROUP, MODELS, IMAGE)
    assert not aws.written


def test_register_refuses_a_serving_image_that_is_not_the_stages(aws):
    aws.read(f"{PREFIX}model.json", json.dumps(model_json(serving_image="other@sha256:1")).encode())
    aws.read(f"{PREFIX}model.tar.gz", ARCHIVE)
    with aws, pytest.raises(RuntimeError, match="and the stage serves"):
        registry.register_model(aws.sagemaker, aws.s3, PREFIX, GROUP, MODELS, IMAGE)


def test_register_proposes_no_second_version_for_a_hash_the_group_holds(aws, capsys):
    aws.read(f"{PREFIX}model.json", json.dumps(model_json()).encode())
    aws.read(f"{PREFIX}model.tar.gz", ARCHIVE)
    aws.call(
        "list_model_packages",
        {"ModelPackageSummaryList": [summary(f"app-ml sha256:{DIGEST}, trained by x", "Approved")]},
        {"ModelPackageGroupName": GROUP},
    )
    with aws:
        result = registry.register_model(aws.sagemaker, aws.s3, PREFIX, GROUP, MODELS, IMAGE)
    assert result == {"registered": False, "sha256": DIGEST, "versions": [VERSION]}
    assert not aws.written
    assert "nothing proposed" in capsys.readouterr().out


def test_no_task_holds_a_path_to_another_status():
    source = "".join(inspect.getsource(m) for m in (common, registry, scoring, training))
    assert "update_model_package" not in source
    assert "create_model_package_group" not in source
    request = registry.package_request(GROUP, model_json(), "s3://b/k", "s3://b/e", PREFIX)
    assert request["ModelApprovalStatus"] == "PendingManualApproval"


# ----------------------------------------------------------------------------------- app-ml-score

MODEL_NAME = "app-ml-score-project"
SUBNETS = ["subnet-az1", "subnet-az2"]
NETWORK = {
    "ExecutionRoleArn": ROLE,
    "VpcConfig": {"Subnets": SUBNETS, "SecurityGroupIds": ["sg-project"]},
    "EnableNetworkIsolation": True,
    "Tags": [{"Key": "AmazonDataZoneProject", "Value": "project"}],
}


def resolve(aws, source: str):
    return scoring.resolve_model(
        aws.sagemaker,
        aws.s3,
        model_prefix=PREFIX,
        source=source,
        group=GROUP,
        serving_image=IMAGE,
        model_name=MODEL_NAME,
        role=ROLE,
        subnets=SUBNETS,
        security_group="sg-project",
        project="project",
    )


def described_version(status: str = "Approved", image: str = IMAGE) -> dict:
    return {
        "ModelPackageName": GROUP,
        "ModelPackageArn": VERSION,
        "CreationTime": NOW,
        "ModelPackageStatus": "Completed",
        "ModelPackageStatusDetails": {"ValidationStatuses": []},
        "ModelApprovalStatus": status,
        "InferenceSpecification": {
            "Containers": [{"Image": image, "ModelDataUrl": f"{COPY}model.tar.gz"}]
        },
    }


MODEL_ARN = f"arn:aws:sagemaker:us-west-2:000000000000:model/{MODEL_NAME}"


def leftover(name: str) -> dict:
    arn = f"arn:aws:sagemaker:us-west-2:000000000000:model/{name}"
    return {"Models": [{"ModelName": name, "ModelArn": arn, "CreationTime": NOW}]}


def test_resolve_serves_the_approved_version_whose_archive_has_the_hash(aws):
    aws.read(f"{PREFIX}model.json", json.dumps(model_json()).encode())
    aws.call(
        "list_model_packages",
        {"ModelPackageSummaryList": [summary(f"app-ml sha256:{DIGEST}", "Approved")]},
        {"ModelPackageGroupName": GROUP},
    )
    aws.call("describe_model_package", described_version(), {"ModelPackageName": VERSION})
    aws.read(f"{COPY}model.tar.gz", ARCHIVE)
    aws.call("list_models", leftover(MODEL_NAME), {"NameContains": MODEL_NAME})
    aws.call("delete_model", {}, {"ModelName": MODEL_NAME})
    request = {"ModelName": MODEL_NAME, **NETWORK, "Containers": [{"ModelPackageName": VERSION}]}
    aws.call("create_model", {"ModelArn": MODEL_ARN}, request)
    with aws:
        served = resolve(aws, "registry")
    assert served == {
        "model_name": MODEL_NAME,
        "source": "registry",
        "sha256": DIGEST,
        "version": VERSION,
        "model_data": f"{COPY}model.tar.gz",
        "training_job": JOB,
    }


@pytest.mark.parametrize("status", ["PendingManualApproval", "Rejected"])
def test_resolve_serves_no_version_that_is_not_approved(aws, status):
    aws.read(f"{PREFIX}model.json", json.dumps(model_json()).encode())
    aws.call(
        "list_model_packages",
        {"ModelPackageSummaryList": [summary(f"app-ml sha256:{DIGEST}", status)]},
        {"ModelPackageGroupName": GROUP},
    )
    aws.call("describe_model_package", described_version(status), {"ModelPackageName": VERSION})
    with aws, pytest.raises(RuntimeError, match=f"is {status}: a target serves an Approved"):
        resolve(aws, "registry")


def test_resolve_refuses_a_version_whose_archive_changed(aws):
    aws.read(f"{PREFIX}model.json", json.dumps(model_json()).encode())
    aws.call(
        "list_model_packages",
        {"ModelPackageSummaryList": [summary(f"app-ml sha256:{DIGEST}", "Approved")]},
        {"ModelPackageGroupName": GROUP},
    )
    aws.call("describe_model_package", described_version(), {"ModelPackageName": VERSION})
    aws.read(f"{COPY}model.tar.gz", b"another archive")
    with aws, pytest.raises(RuntimeError, match=f"not {DIGEST}"):
        resolve(aws, "registry")


def test_resolve_refuses_a_hash_no_version_carries(aws):
    aws.read(f"{PREFIX}model.json", json.dumps(model_json()).encode())
    aws.call(
        "list_model_packages", {"ModelPackageSummaryList": []}, {"ModelPackageGroupName": GROUP}
    )
    with aws, pytest.raises(RuntimeError, match="0 version"):
        resolve(aws, "registry")


def test_resolve_in_dev_serves_the_archive_beside_model_json(aws):
    aws.read(f"{PREFIX}model.json", json.dumps(model_json()).encode())
    aws.read(f"{PREFIX}model.tar.gz", ARCHIVE)
    aws.call("list_models", {"Models": []}, {"NameContains": MODEL_NAME})
    request = {
        "ModelName": MODEL_NAME,
        **NETWORK,
        "PrimaryContainer": {"Image": IMAGE, "ModelDataUrl": f"{PREFIX}model.tar.gz"},
    }
    aws.call("create_model", {"ModelArn": MODEL_ARN}, request)
    with aws:
        served = resolve(aws, "prefix")
    assert served["version"] is None and served["source"] == "prefix"


def test_resolve_in_dev_refuses_an_archive_model_json_does_not_describe(aws):
    aws.read(f"{PREFIX}model.json", json.dumps(model_json()).encode())
    aws.read(f"{PREFIX}model.tar.gz", b"another archive")
    with aws, pytest.raises(RuntimeError, match="and model.json names"):
        resolve(aws, "prefix")


def test_resolve_refuses_a_source_it_does_not_know(aws):
    with aws, pytest.raises(RuntimeError, match="MODEL_SOURCE 'bucket'"):
        resolve(aws, "bucket")


def test_a_leftover_with_another_name_is_kept(aws):
    aws.call("list_models", leftover(f"{MODEL_NAME}-2"), {"NameContains": MODEL_NAME})
    with aws:
        assert scoring.delete_leftover(aws.sagemaker, MODEL_NAME) is False


OUTPUT = f"{SHARED}app-ml/predictions/20261117/"
BATCH = f"{SHARED}app-ml/work/score/batch/batch.csv"
LABELS = f"{SHARED}app-ml/work/score/labels/labels.csv"
REPORT = f"{SHARED}app-ml/outbox/score-report.json"
SCORED = json.dumps(
    json.dumps(
        {
            "Model": {"ModelName": MODEL_NAME},
            "Transform": {
                "TransformJobName": "app-ml-score-20261117T120500",
                "TransformJobStatus": "Completed",
                "TransformOutput": {"S3OutputPath": OUTPUT},
            },
        }
    )
)
RESOLVED = json.dumps(
    {"sha256": DIGEST, "source": "registry", "version": VERSION, "training_job": JOB}
)


def check(aws, predictions: bytes, floor: str = "0.70", written: bool = True):
    """check_scores over four batch lines labelled 0, 0, 1, 1; `written` stubs the report."""
    aws.read(BATCH, b"1,20.00,0,1,0\n" * 4)
    aws.read(LABELS, b"0\n0\n1\n1\n")
    aws.read(f"{OUTPUT}batch.csv.out", predictions)
    if written:
        aws.write(REPORT, content_type="application/json")
    return scoring.check_scores(
        aws.s3,
        scored=SCORED,
        resolved=RESOLVED,
        batch=BATCH,
        labels=LABELS,
        report=REPORT,
        min_auc=floor,
    )


def test_check_writes_the_report_with_the_auc_by_rank(aws):
    with aws:
        report = check(aws, b"0.1\n0.4\n0.35\n0.8\n")
    assert json.loads(aws.written[REPORT]) == report
    assert report == {
        "transform_job": "app-ml-score-20261117T120500",
        "sha256": DIGEST,
        "source": "registry",
        "version": VERSION,
        "training_job": JOB,
        "rows": 4,
        "predictions": 4,
        "auc": 0.75,
        "min_auc": 0.7,
    }


def test_check_writes_the_report_then_fails_under_min_auc(aws):
    with aws, pytest.raises(RuntimeError, match="AUC 0.75 is under MIN_AUC 0.8"):
        check(aws, b"0.1\n0.4\n0.35\n0.8\n", floor="0.80")
    assert REPORT in aws.written


@pytest.mark.parametrize(
    ("predictions", "refusal"),
    [
        (b"0.1\n0.4\n0.8\n", "3 prediction"),
        (b"0.1\n0.4\n1.2\n0.8\n", "prediction 3 is not a probability"),
        (b"0.1\n0.4\nyes\n0.8\n", "prediction 3 is not a number"),
    ],
)
def test_check_refuses_an_output_that_is_not_one_probability_per_line(aws, predictions, refusal):
    with aws, pytest.raises(RuntimeError, match=refusal):
        check(aws, predictions, written=False)
    assert not aws.written


# ------------------------------------------------------------------------------- the workflows


def test_each_python_callable_of_the_workflows_is_a_task_of_the_package():
    for path in sorted((ROOT / "workflows").glob("*.yaml")):
        for name in re.findall(r"python_callable: (\S+)", path.read_text()):
            module, _, attribute = name.rpartition(".")
            assert module == "app_ml_tasks", f"{path.name}: {name}"
            assert callable(getattr(app_ml_tasks, attribute)), f"{path.name}: {name}"
            assert "context" in inspect.signature(getattr(app_ml_tasks, attribute)).parameters


def test_the_task_functions_take_the_workflows_op_kwargs():
    text = "".join(p.read_text() for p in sorted((ROOT / "workflows").glob("*.yaml")))
    blocks = re.findall(
        r"python_callable: app_ml_tasks\.(\w+)\n\s+op_kwargs:\n((?:\s{8}\w+: .+\n)+)", text
    )
    assert {name for name, _ in blocks} == {"evaluate", "publish", "register", "resolve", "check"}
    for name, kwargs in blocks:
        given = set(re.findall(r"^\s{8}(\w+):", kwargs, flags=re.MULTILINE))
        parameters = set(inspect.signature(getattr(app_ml_tasks, name)).parameters) - {"context"}
        assert given == parameters, name
