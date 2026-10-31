#!/usr/bin/env -S uv run --quiet
# render-workflow.py - Stage 10 decision 20 (e): an application's workflow, written in the CI/CD CLI's
# notation for the Sandbox projects, rendered for a deployment target.
#
#   run:      ./scripts/render-workflow.py <account> <workflow.yaml> --tag vX.Y.Z --image-uri <uri>
#                 [--out <file>]            # staging or production; the values read from the states
#             ./scripts/render-workflow.py --check
#                                           # examples/app-etl's workflows, rendered against a stand-in
#                                           # table: what `make check` runs, offline
#   reads:    the account's data/, sagemaker/ and network slices' state objects, as the caller's AWS
#             profile (on the deploy runner, the deploy role, whose state_read_keys name them); nothing
#             with --check.
#   writes:   the rendered YAML, to --out or stdout. Nothing in AWS.
#   exit:     0 rendered | 1 a value or a placeholder the table does not know | 2 usage
#
# The table is Stage 10 decision 6's render table, each value read from the slice that owns it. A
# `{proj.*}`, `{env.*}` or `{domain.*}` the table does not know fails the render, as the promoted D28
# lint fails it on the rendered copy (Stage 10 step 2.3). The Glue task loses the keys with which the
# operator creates its job, the job being the application slice's (D41 item 9); a SageMaker task loses
# its project tag (D41 item 2). A Glue job `<app>-<suffix>-{proj.id}` becomes `awsds-<env>-<app>-<suffix>`
# as `<app>-{proj.id}` becomes `awsds-<env>-<app>`. The training image is sagemaker/'s output, read only
# when a workflow names it. The YAML's leading comment lines, the portal's layout, are kept. The product
# table of Stage 19 (decision 2) is written in a project's database, which a target has none of until
# Stage 19 4.11 moves the deploy to the CLI and retires this render: until then `{env.PRODUCT_DATABASE}`
# renders to the account's `app_outputs`, `{env.PUBLISH_LISTING}` to `false`, and the Glue task loses the
# `--TABLE_DATABASE` and `--TABLE_NAME` arguments, so a target writes no product table and lists nothing.

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml
from tfhygiene import backend
from tfhygiene.states import StateError
from tfhygiene.targets import NETWORK_SLICE, TargetError
from tfhygiene.targets import account_values as target_values

REPO = Path(__file__).resolve().parents[1]

S3_URI = "{proj.connection.default.s3_shared.s3Uri}"

# The classes of an application's prefix under the project's s3Uri, and where each lands in the
# account's outputs bucket (decisions 1, 6, 7 and 12, decision 20 (d)): the application's table under
# tables/ beside work/ and outbox/, and a training job's model under models/<app>/, the prefix Stage 9
# step 1.1 names for model archives and the lint holds a promoted training task to.
RELEASE_CLASSES = ("glue", "src")
INBOX_CLASS = "inbox"
OUTPUT_CLASSES = ("work", "outbox", "tables")
MODEL_CLASS = "models"

GLUE_OPERATOR = "airflow.providers.amazon.aws.operators.glue.GlueJobOperator"
GLUE_JOB_KEYS = (
    "job_desc",
    "script_location",
    "iam_role_arn",
    "update_config",
    "create_job_kwargs",
)
PROJECT_TAG = "AmazonDataZoneProject"
PRODUCT_TABLE_ARGS = ("--TABLE_DATABASE", "--TABLE_NAME")

LEFT_OVER = re.compile(r"\{(?:proj|env|domain)\.[A-Za-z0-9_.]+\}")


class RenderError(Exception):
    pass


def account_values(account: str) -> dict:
    """The table's account column, each value from the slice that owns it (tfhygiene.targets)."""
    try:
        return target_values(account)
    except TargetError as e:
        raise RenderError(str(e)) from e


def s3_target(rest: str, app: str, values: dict) -> str:
    """One `{s3Uri}<app>/<class>/<path>` reference, placed in the account's outputs bucket."""
    head, _, tail = rest.partition("/")
    cls, _, path = tail.partition("/")
    bucket = values["bucket"]
    if head != app:
        raise RenderError(f"{S3_URI}{rest}: outside the application's prefix {app}/")
    if cls in RELEASE_CLASSES:
        return f"s3://{bucket}/applications/{app}/{values['tag']}/{cls}/{path}"
    if cls == INBOX_CLASS:
        return f"s3://{bucket}/inbox/{app}/{path}"
    if cls in OUTPUT_CLASSES:
        return f"s3://{bucket}/{app}/{cls}/{path}"
    if cls == MODEL_CLASS:
        return f"s3://{bucket}/{MODEL_CLASS}/{app}/{path}"
    raise RenderError(f"{S3_URI}{rest}: the class {cls!r} has no row in the render table")


def render_string(text: str, app: str, values: dict) -> str:
    text = re.sub(
        re.escape(S3_URI) + r"([^\s\"']*)",
        lambda m: s3_target(m.group(1), app, values),
        text,
    )
    text = re.sub(
        re.escape(app) + r"((?:-[a-z0-9]+)*)-\{proj\.id\}",
        lambda m: f"awsds-{values['env']}-{app}{m.group(1)}",
        text,
    )
    for placeholder, value in (
        ("{proj.iam_role_arn}", values["job_role_arn"]),
        ("{env.JOB_IMAGE_URI}", values["image_uri"]),
        ("{env.TRAINING_IMAGE_URI}", values.get("training_image_uri")),
        ("{env.SUBNET_AZ1}", values["subnets"][0]),
        ("{env.SUBNET_AZ2}", values["subnets"][1]),
        ("{env.PROJECT_SG}", values["security_group"]),
        ("{env.PROJECT_KEY_ARN}", values["data_key_arn"]),
        ("{env.PRODUCT_DATABASE}", values.get("product_database", "app_outputs")),
        ("{env.PUBLISH_LISTING}", values.get("publish_listing", "false")),
        ("{domain.region}", values["region"]),
    ):
        if value is not None:
            text = text.replace(placeholder, value)
    left = LEFT_OVER.findall(text)
    if left:
        raise RenderError(f"{', '.join(sorted(set(left)))}: no row in the render table")
    return text


def render_value(node, app: str, values: dict):
    if isinstance(node, dict):
        return {k: render_value(v, app, values) for k, v in node.items()}
    if isinstance(node, list):
        return [render_value(v, app, values) for v in node]
    if isinstance(node, str):
        return render_string(node, app, values)
    return node


def drop_project_keys(doc: dict) -> None:
    """The Glue task's job-creation keys and product-table arguments, and a SageMaker task's project
    tag, removed in place."""
    for workflow in doc.values():
        for task in (workflow.get("tasks") or {}).values():
            if task.get("operator") == GLUE_OPERATOR:
                for key in GLUE_JOB_KEYS:
                    task.pop(key, None)
                script_args = task.get("script_args")
                if isinstance(script_args, dict):
                    for key in PRODUCT_TABLE_ARGS:
                        script_args.pop(key, None)
            config = task.get("config")
            if isinstance(config, dict) and isinstance(config.get("Tags"), list):
                config["Tags"] = [t for t in config["Tags"] if t.get("Key") != PROJECT_TAG]
                if not config["Tags"]:
                    del config["Tags"]


def render(text: str, app: str, values: dict) -> str:
    """The workflow file `text`, rendered with `values`; its leading comment lines kept."""
    header = []
    for line in text.splitlines():
        if not line.startswith("#"):
            break
        header.append(line)
    doc = yaml.safe_load(text)
    if not isinstance(doc, dict):
        raise RenderError("the workflow file is not a mapping of workflows")
    drop_project_keys(doc)
    doc = render_value(doc, app, values)
    body = yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, width=1_000_000)
    return "\n".join(header + [body.rstrip("\n")]) + "\n"


def check() -> int:
    """examples/app-etl's workflows rendered against a stand-in table, and the rendering's invariants."""
    values = {
        "env": "staging",
        "region": backend.REGION,
        "tag": "v0.0.0",
        "image_uri": "registry.example/awsds-prod-ecr-app-etl@sha256:" + "0" * 64,
        "bucket": "awsds-staging-outputs",
        "data_key_arn": "arn:aws:kms:region:account:key/stand-in",
        "job_role_arn": "arn:aws:iam::account:role/awsds-staging-job-exec",
        "security_group": "sg-stand-in",
        "subnets": ["subnet-stand-in-1", "subnet-stand-in-2"],
        "training_image_uri": "registry.example/sagemaker-xgboost@sha256:" + "1" * 64,
    }
    app_dir = REPO / "examples" / "app-etl"
    app = yaml.safe_load((app_dir / "manifest.yaml").read_text(encoding="utf-8"))["applicationName"]
    fail = 0
    files = sorted((app_dir / "workflows").glob("*.yaml"))
    for path in files:
        rel = path.relative_to(REPO)
        try:
            out = render(path.read_text(encoding="utf-8"), app, values)
        except RenderError as e:
            print(f"  FAIL  {rel}: {e}")
            fail = 1
            continue
        doc = yaml.safe_load(out)
        problems = []
        for workflow in doc.values():
            for name, task in (workflow.get("tasks") or {}).items():
                if task.get("operator") == GLUE_OPERATOR:
                    kept = [k for k in GLUE_JOB_KEYS if k in task]
                    if kept:
                        problems.append(f"{name} keeps {', '.join(kept)}")
                    job = str(task.get("job_name"))
                    if not re.fullmatch(rf"awsds-staging-{re.escape(app)}(-[a-z0-9]+)*", job):
                        problems.append(f"{name}'s job_name is {job!r}")
        flat = json.dumps(doc)
        for uri in re.findall(r"s3://[^\"\s]+", flat):
            if not uri.startswith(f"s3://{values['bucket']}/"):
                problems.append(f"{uri} is outside the account's outputs bucket")
        if PROJECT_TAG in flat:
            problems.append(f"the {PROJECT_TAG} tag survives")
        if any(arg in flat for arg in PRODUCT_TABLE_ARGS):
            problems.append("the product table's arguments survive")
        for problem in problems:
            print(f"  FAIL  {rel}: {problem}")
        if problems:
            fail = 1
        else:
            print(f"  ok    {rel}")
    if not files:
        print("  FAIL  examples/app-etl/workflows/ holds no workflow")
        fail = 1
    print()
    print("OK" if fail == 0 else "FAILED")
    return fail


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="Render an application's workflow for a target.")
    ap.add_argument("account", nargs="?", choices=sorted(NETWORK_SLICE))
    ap.add_argument("workflow", nargs="?", type=Path)
    ap.add_argument("--tag")
    ap.add_argument("--image-uri")
    ap.add_argument("--app", default="app-etl")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    if args.check:
        return check()
    if not (args.account and args.workflow and args.tag and args.image_uri):
        ap.error("<account> <workflow.yaml> --tag and --image-uri are required without --check")
    if not re.fullmatch(r"v\d+\.\d+\.\d+", args.tag):
        ap.error("--tag is the release tag, vMAJOR.MINOR.PATCH")
    try:
        text = args.workflow.read_text(encoding="utf-8")
        values = account_values(args.account)
        values.update(tag=args.tag, image_uri=args.image_uri)
        out = render(text, args.app, values)
    except (OSError, RenderError, StateError) as e:
        print(f"render-workflow: {e}", file=sys.stderr)
        return 1
    if args.out:
        args.out.write_text(out, encoding="utf-8")
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
