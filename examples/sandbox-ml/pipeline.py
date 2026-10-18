"""Stage 17 steps 5.1, 5.2 and 5.4: the chain of passes 2 and 3 as one ML pipeline.

    upsert    fill pipeline/definition.json's placeholders from the value files, upload prepare.py
              to shared/ml-demo/pipeline/code/, and create or update the pipeline
              ml-demo-pipeline, whose RoleArn is the project role (verification xi reads the
              iam:PassRole)
    start     StartPipelineExecution, printing the execution's ARN
    status    the latest execution and its steps: each step's status, its job's ARN, the
              condition's outcome and a Fail step's message
    compare   the live definition, its account-scoped values turned back into placeholders,
              against the committed source (5.2, the two directions of 6i decision 1)

The definition is the source, as JSON for boto3 rather than through the SageMaker SDK, whose
pipeline API moved between major versions (README.md): Prepare runs prepare.py in the house image
on ml.t3.medium; Train is train.py's admitted request; CheckAuc compares validation:auc with the
AucThreshold parameter (0.75); Register adds a PendingManualApproval version to ml-demo-xgboost,
and AucBelowThreshold fails the execution with the threshold in its message. Every job carries
the boundary's four settings, the project key and the project tag. It prints names, statuses and
ARNs, never a row.

    /opt/awsds/venv/bin/python pipeline.py upsert
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys

from botocore.exceptions import ClientError
from common import (
    HERE,
    PLACEHOLDER,
    client,
    load_values,
    need,
    project_tags,
    refusal,
    role_arn,
    s3_uri,
    split_s3_uri,
)

PIPELINE = "ml-demo-pipeline"
DEFINITION = HERE / "pipeline" / "definition.json"


def source_names() -> list:
    """The placeholders the committed definition names."""
    return sorted(set(PLACEHOLDER.findall(DEFINITION.read_text(encoding="utf-8"))))


def filled_definition(values: dict) -> str:
    """The committed definition with every placeholder replaced by its value."""
    text = DEFINITION.read_text(encoding="utf-8")
    names = source_names()
    need(values, *names)
    for name in names:
        text = text.replace(f"<{name}>", values[name])
    json.loads(text)  # a value that broke the JSON stops here, before any call
    return text


def upsert(values: dict) -> int:
    definition = filled_definition(values)
    bucket, key = split_s3_uri(s3_uri(values, "pipeline", "code", "prepare.py"))
    client(values, "s3").upload_file(str(HERE / "prepare.py"), bucket, key)
    print(f"prepare.py -> s3://{bucket}/{key}")

    sagemaker = client(values, "sagemaker")
    request = {
        "PipelineName": PIPELINE,
        "PipelineDefinition": definition,
        "PipelineDescription": "Stage 17: the churn model prepared, trained, checked, registered",
        "RoleArn": role_arn(values),
    }
    try:
        sagemaker.describe_pipeline(PipelineName=PIPELINE)
        exists = True
    except ClientError as err:
        if "does not exist" not in refusal(err):
            raise
        exists = False
    try:
        if exists:
            answer = sagemaker.update_pipeline(**request)
        else:
            answer = sagemaker.create_pipeline(**request, Tags=project_tags(values))
    except ClientError as err:
        print(f"{PIPELINE}: refused")
        print(refusal(err))
        return 1
    print(f"{PIPELINE}: {'updated' if exists else 'created'}, {answer['PipelineArn']}")
    return 0


def start(values: dict) -> int:
    try:
        answer = client(values, "sagemaker").start_pipeline_execution(PipelineName=PIPELINE)
    except ClientError as err:
        print(f"{PIPELINE}: start refused")
        print(refusal(err))
        return 1
    print(f"{PIPELINE}: execution {answer['PipelineExecutionArn']}")
    return 0


def step_line(step: dict) -> str:
    """One step of an execution: its status, its job and what it decided."""
    metadata = step.get("Metadata") or {}
    arns = [v["Arn"] for v in metadata.values() if isinstance(v, dict) and v.get("Arn")]
    line = f"{step['StepName']}: {step['StepStatus']}"
    if arns:
        line += f" {arns[0]}"
    if "Condition" in metadata:
        line += f", outcome {metadata['Condition'].get('Outcome', '-')}"
    if "Fail" in metadata:
        line += f", {metadata['Fail'].get('ErrorMessage', '-')}"
    if step.get("FailureReason"):
        line += f" - {step['FailureReason']}"
    return line


def status(values: dict) -> int:
    sagemaker = client(values, "sagemaker")
    executions = sagemaker.list_pipeline_executions(
        PipelineName=PIPELINE, SortBy="CreationTime", SortOrder="Descending", MaxResults=1
    )["PipelineExecutionSummaries"]
    if not executions:
        print(f"{PIPELINE}: no execution")
        return 0
    latest = executions[0]
    print(
        f"{latest['PipelineExecutionArn']}: {latest['PipelineExecutionStatus']}, "
        f"started {latest['StartTime']}"
    )
    steps = sagemaker.list_pipeline_execution_steps(
        PipelineExecutionArn=latest["PipelineExecutionArn"], SortOrder="Ascending"
    )["PipelineExecutionSteps"]
    for step in steps:
        print(step_line(step))
    return 0


def compare(values: dict) -> int:
    live = client(values, "sagemaker").describe_pipeline(PipelineName=PIPELINE)
    text = live["PipelineDefinition"]
    # The longest value first, so a value that holds another (the role's name holds the
    # project's id) becomes its own placeholder.
    names = sorted(source_names(), key=lambda n: len(values.get(n, "")), reverse=True)
    for name in names:
        if name in values and not PLACEHOLDER.search(values[name]):
            text = text.replace(values[name], f"<{name}>")
    source = json.loads(DEFINITION.read_text(encoding="utf-8"))
    left = json.dumps(source, indent=2, sort_keys=True).splitlines()
    right = json.dumps(json.loads(text), indent=2, sort_keys=True).splitlines()
    diff = list(difflib.unified_diff(left, right, "committed", "live", lineterm=""))
    if not diff:
        print(f"{PIPELINE}: the live definition is the committed source")
        return 0
    print("\n".join(diff))
    return 1


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pipeline.py")
    parser.add_argument("command", choices=("upsert", "start", "status", "compare"))
    args = parser.parse_args(argv)

    values = load_values()
    commands = {"upsert": upsert, "start": start, "status": status, "compare": compare}
    return commands[args.command](values)


if __name__ == "__main__":
    sys.exit(main())
