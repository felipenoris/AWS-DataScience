"""Step 4.5's processing job: the task's request as the CLI deploys it and the service renders it in
each stage, the settings the infrastructure repository's denies and the lint read, the code input
under the folder every stage copies, the dev stage alone creating the workflow, and job/probe.py
over doubles of boto3 and of the proxy."""

from __future__ import annotations

import importlib.util
import re
import sys
import time
import types
import urllib.error

import pytest
import rendering
import yaml
from jinja2 import StrictUndefined
from jinja2.exceptions import UndefinedError
from jinja2.sandbox import SandboxedEnvironment

PROCESSING = "airflow.providers.amazon.aws.operators.sagemaker.SageMakerProcessingOperator"
DOCUMENT = yaml.safe_load((rendering.ROOT / "workflows" / "app-dbt-job.yaml").read_text())
TASK = DOCUMENT["app-dbt-job"]["tasks"]["job"]
CONFIG = TASK["config"]
# The instance types the Workloads ceiling and the pipeline's lint admit.
CEILING = {
    "ml.t3.medium",
    "ml.t3.large",
    "ml.t3.xlarge",
    "ml.m5.large",
    "ml.m5.xlarge",
    "ml.c5.large",
    "ml.c5.xlarge",
}
# A SageMaker job name.
JOB_NAME = re.compile(r"[a-zA-Z0-9](-*[a-zA-Z0-9]){0,62}")


def placeholders(stage: str) -> dict[str, str]:
    values = {}
    for name, value in rendering.stage_variables(stage).items():
        values[name] = re.sub(r"\$\{(\w+)\}", r"placeholder-\1", str(value))
    return values


def rendered(node, params: dict[str, str]):
    """The config as the run renders it: each string translated by the CLI, then by Jinja with the
    run's parameters and the service's macros."""
    environment = SandboxedEnvironment(undefined=StrictUndefined)
    macros = types.SimpleNamespace(time=time)
    if isinstance(node, dict):
        return {key: rendered(value, params) for key, value in node.items()}
    if isinstance(node, list):
        return [rendered(value, params) for value in node]
    if isinstance(node, str):
        template = environment.from_string(rendering.translate(node))
        return template.render(params=params, macros=macros)
    return node


def test_the_task_is_one_processing_job_tried_once():
    assert list(DOCUMENT["app-dbt-job"]["tasks"]) == ["job"]
    assert TASK["operator"] == PROCESSING
    assert TASK["retries"] == 0


def test_the_job_runs_without_isolation_in_the_projects_network():
    network = CONFIG["NetworkConfig"]
    assert network["EnableNetworkIsolation"] is False
    assert network["EnableInterContainerTrafficEncryption"] is True
    assert network["VpcConfig"] == {
        "Subnets": ["{env.SUBNET_AZ1}", "{env.SUBNET_AZ2}"],
        "SecurityGroupIds": ["{env.PROJECT_SG}"],
    }
    cluster = CONFIG["ProcessingResources"]["ClusterConfig"]
    assert cluster["InstanceType"] in CEILING
    assert cluster["InstanceCount"] == 1
    assert cluster["VolumeKmsKeyId"] == "{env.PROJECT_KEY_ARN}"
    assert CONFIG["StoppingCondition"]["MaxRuntimeInSeconds"] <= 2820
    assert CONFIG["Tags"] == [{"Key": "AmazonDataZoneProject", "Value": "{proj.id}"}]
    assert CONFIG["RoleArn"] == "{proj.iam_role_arn}"
    assert CONFIG["AppSpecification"]["ImageUri"] == "{env.JOB_IMAGE_URI}"
    assert "ProcessingOutputConfig" not in CONFIG


def test_the_code_input_is_the_job_folder_every_stage_copies():
    [code] = CONFIG["ProcessingInputs"]
    assert code["InputName"] == "code"
    assert code["S3Input"]["LocalPath"] == "/opt/ml/processing/code"
    assert code["S3Input"]["S3Uri"] == "{proj.connection.default.s3_shared.s3Uri}app-dbt/job/"
    for stage in rendering.STAGES:
        storage = rendering.manifest()["stages"][stage]["deployment_configuration"]["storage"]
        assert {
            "name": "job",
            "connectionName": "default.s3_shared",
            "targetDirectory": "app-dbt/job",
        } in storage
    entrypoint = CONFIG["AppSpecification"]["ContainerEntrypoint"]
    assert entrypoint == ["/opt/conda/bin/python", "/opt/ml/processing/code/probe.py"]
    assert (rendering.ROOT / "job" / "probe.py").is_file()


def test_the_dev_stage_alone_creates_the_workflow():
    for stage in rendering.STAGES:
        actions = rendering.manifest()["stages"][stage]["bootstrap"]["actions"]
        named = [action for action in actions if action["workflowName"] == "app-dbt-job"]
        assert named == (
            [{"type": "workflow.create", "workflowName": "app-dbt-job"}] if stage == "dev" else []
        )


@pytest.mark.parametrize("stage", rendering.STAGES)
def test_the_request_renders_with_each_stage(stage):
    params = placeholders(stage)
    request = rendered(CONFIG, params)
    text = repr(request)
    assert (
        "{env." not in text and "{proj." not in text and "{domain." not in text and "{{" not in text
    )
    assert JOB_NAME.fullmatch(request["ProcessingJobName"]), request["ProcessingJobName"]
    assert request["ProcessingJobName"].startswith("app-dbt-job-")
    assert request["NetworkConfig"]["VpcConfig"]["SecurityGroupIds"] == [params["PROJECT_SG"]]
    assert (
        request["ProcessingResources"]["ClusterConfig"]["VolumeKmsKeyId"]
        == params["PROJECT_KEY_ARN"]
    )
    arguments = request["AppSpecification"]["ContainerArguments"]
    assert arguments == [
        "--region",
        "us-west-2",
        "--workgroup",
        "workgroup-simulated-project",
        "--database",
        "app_dbt",
        "--domain",
        "dzd-simulated",
    ]
    image = request["AppSpecification"]["ImageUri"]
    assert image == ("placeholder-JOB_IMAGE_URI" if stage == "dev" else "none")


def test_a_parameter_the_run_does_not_carry_fails_the_rendering():
    params = placeholders("dev")
    for name in ("JOB_IMAGE_URI", "PROJECT_SG", "PROJECT_KEY_ARN"):
        missing = {key: value for key, value in params.items() if key != name}
        with pytest.raises(UndefinedError, match=name):
            rendered(CONFIG, missing)


def load_probe():
    spec = importlib.util.spec_from_file_location("probe", rendering.ROOT / "job" / "probe.py")
    module = importlib.util.module_from_spec(spec)
    writes = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = writes
    return module


class Client:
    """A boto3 client's double: each method answers its value or raises it."""

    def __init__(self, answers: dict):
        self.answers = answers

    def __getattr__(self, name):
        answer = self.answers[name]

        def method(**arguments):
            if isinstance(answer, Exception):
                raise answer
            return answer

        return method


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *details):
        return False


ARGUMENTS = [
    "--region",
    "us-west-2",
    "--workgroup",
    "workgroup-simulated-project",
    "--database",
    "app_dbt",
    "--domain",
    "dzd-simulated",
]
ANSWERS = {
    "sts": Client(
        {"get_caller_identity": {"Arn": "arn:aws:sts::000000000000:assumed-role/r/SageMaker"}}
    ),
    "athena": Client(
        {
            "start_query_execution": {"QueryExecutionId": "q1"},
            "get_query_execution": {
                "QueryExecution": {
                    "Status": {"State": "SUCCEEDED"},
                    "ResultConfiguration": {"OutputLocation": "s3://simulated-bucket/q1.csv"},
                }
            },
            "get_query_results": {
                "ResultSet": {
                    "Rows": [
                        {"Data": [{"VarCharValue": "_col0"}]},
                        {"Data": [{"VarCharValue": "1"}]},
                    ]
                }
            },
        }
    ),
    "glue": Client(
        {
            "get_database": {
                "Database": {"Name": "app_dbt", "LocationUri": "s3://simulated-bucket/app_dbt"}
            }
        }
    ),
    "datazone": Client({"list_lineage_events": {"items": [{"processingStatus": "SUCCESS"}]}}),
}


def proxy(url, timeout):
    """The Sandbox plane's answers: the name on it reached, the name on no plane refused."""
    assert timeout == 10
    if "pypi.org" in url:
        return Response()
    raise urllib.error.HTTPError(url, 403, "Forbidden", None, None)


def test_the_probe_prints_each_answer(capsys):
    probe = load_probe()
    assert probe.main(ARGUMENTS, clients=ANSWERS.__getitem__, opener=proxy) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "caller: arn:aws:sts::000000000000:assumed-role/r/SageMaker" in lines
    assert "select 1: SUCCEEDED - output s3://simulated-bucket/q1.csv" in lines
    assert "select 1: rows [['_col0'], ['1']]" in lines
    assert "database: app_dbt s3://simulated-bucket/app_dbt" in lines
    assert "lineage: 1 events ['SUCCESS']" in lines
    assert "on the plane: https://pypi.org/ HTTP 200" in lines
    assert "on no plane: http://example.com/ HTTP 403 Forbidden" in lines


def test_the_probe_ends_0_when_every_call_is_refused(capsys):
    probe = load_probe()

    def refused(service):
        raise RuntimeError(f"no {service}")

    def unreachable(url, timeout):
        raise urllib.error.URLError("Tunnel connection failed: 403 Forbidden")

    assert probe.main(ARGUMENTS, clients=refused, opener=unreachable) == 0
    lines = capsys.readouterr().out.splitlines()
    services = {"caller": "sts", "athena": "athena", "database": "glue", "lineage": "datazone"}
    for name, service in services.items():
        assert f"{name}: REFUSED RuntimeError: no {service}" in lines
    assert any(
        line.startswith("on the plane: https://pypi.org/ REFUSED URLError:") for line in lines
    )
    assert any(
        line.startswith("on no plane: http://example.com/ REFUSED URLError:") for line in lines
    )


def test_the_probe_reports_a_query_that_failed(capsys):
    probe = load_probe()
    athena = Client(
        {
            "start_query_execution": {"QueryExecutionId": "q2"},
            "get_query_execution": {
                "QueryExecution": {"Status": {"State": "FAILED", "StateChangeReason": "denied"}}
            },
        }
    )
    probe.query("select 1", athena, "workgroup-simulated-project", "SELECT 1", sleep=lambda _: None)
    assert capsys.readouterr().out.splitlines() == ["select 1: FAILED denied output None"]
