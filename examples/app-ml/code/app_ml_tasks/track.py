"""`python3 -m app_ml_tasks.track --run S3_URI --tracking-server ARN`: the run app-ml-train's
evaluate task recorded, logged to the project's MLflow App.

The workflow runs it in a Bash task, whose `python3` imports the archive's packages first (SUP-274):
the MLflow client and the plugin that signs a call to an `mlflow-app` ARN come from
code/app-ml-train.zip, and boto3 from the worker. It reads `last-run.json`, the pointer evaluate
wrote, so it needs no XCom, and logs one run: the hyperparameters as parameters, the validation AUC
as a metric, the training job, its model data, its image and the evaluation's URI as tags, and the
evaluation file as an artifact. The MLflow App is the `dev` project's alone (Stage 17 decision 17).
"""

from __future__ import annotations

import argparse
import sys

from .common import read_json

EXPERIMENT = "app-ml"


def log_run(mlflow, run: dict, evaluation: dict, tracking_server: str, experiment: str) -> str:
    """One MLflow run for the training run; its id."""
    mlflow.set_tracking_uri(tracking_server)
    mlflow.set_experiment(experiment)
    with mlflow.start_run(run_name=run["training_job"]) as active:
        mlflow.log_params(run.get("hyperparameters") or {})
        mlflow.log_metric("validation_auc", float(run["auc"]))
        mlflow.set_tags(
            {
                "training_job": run["training_job"],
                "model_data": run["model_data"],
                "training_image": run["training_image"],
                "evaluation": run["evaluation"],
            }
        )
        mlflow.log_dict(evaluation, "evaluation.json")
        return active.info.run_id


def track(s3, mlflow, run_uri: str, tracking_server: str, experiment: str = EXPERIMENT) -> str:
    """The run the pointer names, logged; the MLflow run's id."""
    server = tracking_server.strip()
    if not server.startswith("arn:aws:sagemaker:") or ":mlflow-" not in server:
        raise RuntimeError(
            f"MLFLOW_APP_ARN {server!r} is not an MLflow App's ARN: the dev stage tracks every run"
        )
    run = read_json(s3, run_uri)
    evaluation = read_json(s3, run["evaluation"])
    run_id = log_run(mlflow, run, evaluation, server, experiment)
    print(
        f"tracked {run['training_job']} as run {run_id} of the experiment {experiment}: "
        f"validation_auc {run['auc']}"
    )
    return run_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app-ml-track", description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True, help="the S3 URI of last-run.json")
    parser.add_argument("--tracking-server", required=True, help="the MLflow App's ARN")
    parser.add_argument("--experiment", default=EXPERIMENT)
    args = parser.parse_args(argv)
    try:
        import boto3
        import mlflow

        track(boto3.client("s3"), mlflow, args.run, args.tracking_server, args.experiment)
    except (ImportError, RuntimeError) as exc:
        print(f"track: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
