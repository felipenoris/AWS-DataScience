# Sandbox machine learning: the exercise's files

The files [Stage 17](../../docs/plan/stages/stage-17-sandbox-machine-learning.md) runs from a space: the
data, the training job and its negatives, the registry, the serving, the pipeline and the knowledge base's
documents. The stage file is the procedure and carries the reasoning; this file says what each piece is,
which step runs it, and what it assumes.

Every script runs in a terminal of a JupyterLab space on the house image, in the Sandbox project, from a
clone of this repository, with the house interpreter `/opt/awsds/venv/bin/python` and the space's own
credentials, the project role's. The scripts call the SageMaker API through boto3's low-level client, so
each negative is the admitted request with one field changed (Lesson 20) and each refusal prints its code
and `errorMessage` whole. The pipeline is a JSON definition sent through boto3 for the same reason, and
because the house environment's SageMaker SDK is 3.21.0 (the image's lock), whose training and pipeline
classes are not the 2.x `Estimator` and `Pipeline` that AWS's recipe imports. No script prints a row of
data.

Nothing here has run against AWS. The scripts were written on 2026-10-17 in a session with no AWS
credentials, against the house environment's lock: `boto3` 1.43.92, `mlflow` 3.16.0, `sagemaker-mlflow`
0.5.0, `sagemaker` 3.21.0, `pandas` 2.3.3, `xgboost-cpu` 3.3.0, Python 3.12. Step 0.3 reads the versions
the space holds, and a script that disagrees with them changes before it runs (Lesson 65). What ran on
that session's build host is under "What ran outside the lab".

## Layout

| Path | What it is | Step |
|---|---|---|
| `common.py` | the value files, the prefix `<DOMAIN_ID>/<PROJECT_ID>/shared/ml-demo`, the request fields the D13 boundary demands (subnets and security group, the project key, the project tag), and how a refusal prints | every script |
| `prepare.py` | the recipe's preparation: `TotalCharges` to numeric and its blank rows dropped, the label `churn_label` and six features, shuffled with `random_state=1729`, split 70/15/15 in XGBoost's CSV layout (label first, no header) | 2.1, imported by `data.py`; 5.1, run by the pipeline's processing step |
| `data.py` | the Telco churn CSV fetched from `raw.githubusercontent.com` through the space's proxy, written as `data/raw/telco.csv` and split into `data/train.csv`, `data/validation.csv` and `data/test.csv` | 2.1 |
| `train.py` | the XGBoost training job: the admitted request (`tagged`) and six variants that each change one field, an MLflow run per attempt tagged with the job's name or the refusal, a negative the boundary admits stopped at once | 2.2, 2.3, 3.1 |
| `register.py` | `log-model`: the job's `model.tar.gz` logged into its run, then the booster as an MLflow model; `package`: the group `ml-demo-xgboost` and a `PendingManualApproval` version; `from-mlflow`: a version through MLflow's registry | 3.1, 3.2 |
| `serve.py` | `endpoint`: a real-time endpoint invoked and deleted in the same run; `transform`: a batch transform, and its negative without the volume key; `serverless`: the two negatives Stage 9 3.7 asks for | 4.1, 4.3, 4.4 |
| `pipeline/definition.json` | the pipeline `ml-demo-pipeline`, every account-scoped value a placeholder: `Prepare` (processing, the house image, `ml.t3.medium`), `Train`, `CheckAuc` on `validation:auc` against the parameter `AucThreshold` (0.75), then `Register` or the Fail step `AucBelowThreshold` | 5.1 |
| `pipeline.py` | `upsert` (the definition filled, `prepare.py` uploaded, the pipeline created or updated with the project role as its `RoleArn`), `start`, `status`, and `compare` against the live definition | 5.1, 5.2, 5.4 |
| `knowledge_base.py` | the runbooks, `docs/plan/runbooks/*.md` (16 files and 556,006 bytes at this commit), copied to `bedrock/kb/` under the prefix, with the commit and each document's size printed | 7.4a |
| [`bedrock/`](bedrock/README.md) | what the portal exports in pass 7 | 7.4, 7.4b |
| `extra_values.json` | the values no space reading gives, each `"<NAME>"` until it is filled | — |

Every object carries the tag `AmazonDataZoneProject` with the project's id and a name starting with
`ml-demo-`. `./aws/sandbox-ml.py` reads them from the laptop; `ML-6` compares the live pipeline's steps with
`pipeline/definition.json`.

## The values

Two JSON files beside the scripts hold every account-scoped value. The pre-commit hook refuses an account id
in a tracked file, so neither reaches git filled:

- **`space_values.json`**, untracked (`.gitignore`): the JSON awsds-workflows' `scripts/space_values.py`
  prints inside the space, with `REGION`, `ACCOUNT_ID`, `PROJECT_ROLE_NAME`, `PROJECT_ID`, `DOMAIN_ID`,
  `PROJECTS_BUCKET`, `PROJECT_KEY_ID`, `PROJECT_SG`, `SUBNET_AZ1` and `SUBNET_AZ2`. The laptop's
  `awsds-workflows values` prints the same JSON with `JOB_IMAGE_URI` added (the runbook's
  [§T](../../docs/plan/runbooks/serverless-workflows.md)), and either output can be the file.
- **`extra_values.json`**, tracked with each value `"<NAME>"`, is filled in the space's clone and never
  committed filled. A `"<NAME>"` left in it never replaces a value `space_values.json` gave, and a script
  stops, naming the value, while one it needs is still unfilled.

| Value | What it is | Where it is read | Needed by |
|---|---|---|---|
| `XGBOOST_IMAGE_URI` | AWS's XGBoost algorithm image for the Region, version `3.0-5` ("The model format") | the SDK's image table, in the space, below | `train.py`, `pipeline.py` |
| `MLFLOW_APP_ARN` | the project's MLflow App, once step 1.5 has created it | the app's page in the portal, or `ML-2` in `aws/output/sandbox-ml.txt` | `train.py`, `register.py log-model` and `from-mlflow` |
| `JOB_IMAGE_URI` | the house image pinned by digest, which the pipeline's processing step runs | `awsds-workflows values --profile awsds-infra-sandbox-1 --subnet-name 'awsds-sandbox-private-*' --image-name awsds-sandbox-dev-env` on the laptop | `pipeline.py` |

In the space, from `examples/sandbox-ml/` in the clone, the first two commands write `space_values.json` and
the third prints `XGBOOST_IMAGE_URI`:

```bash
curl -fsSL https://raw.githubusercontent.com/felipenoris/awsds-workflows/main/scripts/space_values.py -o /tmp/space_values.py
```

```bash
/opt/awsds/venv/bin/python /tmp/space_values.py > space_values.json
```

```bash
/opt/awsds/venv/bin/python -c 'from sagemaker.core import image_uris; print(image_uris.retrieve("xgboost", "us-west-2", version="3.0-5"))'
```

`image_uris.retrieve` is SDK 3.x's path (`sagemaker-core` 2.21.0, read in its wheel on 2026-10-17); under
SDK 2.x the import is `from sagemaker import image_uris`.

## The model format

AWS's recipe trains with XGBoost `1.7-1`, and this exercise trains with `3.0-5`. The SageMaker XGBoost
container saves the booster as `xgboost-model`, a name with no extension, for which XGBoost 1.7 writes its
binary format, and XGBoost 3.1 removed that format; the container's own source was not read. Measured on
2026-10-17 on this session's build host, not in the lab:

- a booster that `xgboost` 1.7.6 saved as `xgboost-model` starts with the bytes `binf`, and
  `xgboost-cpu` 3.3.0 refuses it: *"The binary format has been deprecated in 1.6 and removed in 3.1, use
  UBJ or JSON instead"*;
- the same booster saved by `xgboost` 3.0.5 is UBJSON, and 3.3.0 loads it, warning that it guessed the
  format from a name with no extension.

So with `1.7-1`, step 3.1's `mlflow.xgboost.log_model` cannot run in the house interpreter. `3.0-5` is in
the same repository, `sagemaker-xgboost`, and the same registry for `us-west-2` as `1.7-1`, in SDK 3.21.0's
image table, so `ML-3`'s image check reads it the same way. `register.py log-model` logs the archive before
it loads the booster, so verification iv has its object in the artifact store whatever the image, and with
a `1.7-1` job it prints xgboost's refusal. `register.py from-mlflow` registers the job's `model.tar.gz`
itself, as AWS's recipe does, so the format does not reach it.

## What ran outside the lab

Read on 2026-10-17 on the build host of the session that wrote the scripts, with fabricated account
values and no AWS credentials. None of it is a lab measurement:

- **`data.py`** fetched the CSV (7,043 rows, 970,457 bytes) through that host's proxy, not the lab's;
  `prepare.py` dropped 11 rows for a blank `TotalCharges` and split the rest 4,922 / 1,054 / 1,056, with
  byte-identical parts under `pandas` 2.3.3, the image's, and 3.0.6.
- **The recipe's hyperparameters**, trained locally with `xgboost-cpu` 3.3.0 over that split, gave a
  validation AUC of 0.818 for 200 rounds at depth 5 and 0.842 for 50 rounds at depth 3, both above the
  pipeline's `AucThreshold` of 0.75. A training job runs the image's XGBoost, so its AUC is its own reading.
- **`register.py`'s booster half** loaded two local models ("The model format").
- **`pipeline.py`'s fill and `compare`** round-tripped the definition.
- **Every AWS call but `register.py log-model`'s** went through botocore's `Stubber`, which checks each
  request against the service's model, with MLflow replaced by a stand-in; each variant of `train.py`
  differs from the admitted request in one field. A request the model accepts can still be refused by the
  service.

## A sitting, step by step

The session is the stage's: `make hub-up`, then `make up ENV=sandbox GROUPS=mlflow` for passes 2 to 5 and
`GROUPS=mlflow,bedrock-base,bedrock-agent` for pass 7. Each line runs from `examples/sandbox-ml/`; a job's
name is what `train.py` printed, and a version's ARN is what `register.py package` printed.

```bash
# 2.1: the data, fetched through the proxy and written under shared/ml-demo/data/
/opt/awsds/venv/bin/python data.py
# 2.2 (a) and (b); (c) is the second line again once decision 7's slice is applied
/opt/awsds/venv/bin/python train.py untagged
/opt/awsds/venv/bin/python train.py tagged --wait
# 2.3: the five negatives, then the admitted request of the same sitting
/opt/awsds/venv/bin/python train.py no-vpc
/opt/awsds/venv/bin/python train.py no-isolation
/opt/awsds/venv/bin/python train.py no-ice
/opt/awsds/venv/bin/python train.py no-volume-key
/opt/awsds/venv/bin/python train.py ceiling
/opt/awsds/venv/bin/python train.py tagged --wait
# 3.1: the second run, then the better job's model into its run
/opt/awsds/venv/bin/python train.py tagged --wait --num-round 50 --max-depth 3
/opt/awsds/venv/bin/python register.py log-model <job>
# 3.2: both doors into the registry
/opt/awsds/venv/bin/python register.py package <job>
/opt/awsds/venv/bin/python register.py from-mlflow <job>
# 4.1, 4.3 and 4.4
/opt/awsds/venv/bin/python serve.py endpoint <version ARN>
/opt/awsds/venv/bin/python serve.py transform <version ARN>
/opt/awsds/venv/bin/python serve.py transform <version ARN> --no-volume-key
/opt/awsds/venv/bin/python serve.py serverless <version ARN>
# 5.1 and 5.2
/opt/awsds/venv/bin/python pipeline.py upsert
/opt/awsds/venv/bin/python pipeline.py start
/opt/awsds/venv/bin/python pipeline.py status
/opt/awsds/venv/bin/python pipeline.py compare
# 7.4a: the knowledge base's documents
/opt/awsds/venv/bin/python knowledge_base.py
```

A `serve.py endpoint` run deletes its endpoint, endpoint configuration and model on its way out, an
interrupted one included; `ML-5` fails on any endpoint that survives, every sitting. A transform job and a
training job cannot be deleted, so they stay as records.

## What the first run decides

These parts of the scripts follow AWS's documentation or the SDK's serialization, and no run has read them
in this estate:

- **The pipeline definition's references**: `Steps.Prepare.ProcessingOutputConfig.Outputs['train'].S3Output.S3Uri`,
  `Steps.Train.ModelArtifacts.S3ModelArtifacts`, and the condition's
  `Steps.Train.FinalMetricDataList['validation:auc'].Value`. A wrong one fails at `upsert` or at the step
  that resolves it, and `pipeline.py status` prints which.
- **`Tags` inside the pipeline's step arguments**, which `SageMakerCreatePermissions` needs on each job;
  whether the service accepts them there and passes them to the jobs is read on the first execution, by
  `ML-3` and `ML-6`.
- **`mlflow.register_model` on an `s3://` URI** into a registry `sagemaker-mlflow` backs, the recipe's call;
  the plugin's `arn` registry store sends it to the MLflow App, and whether the version then reaches
  `ml-demo-xgboost`, which `package` created outside MLflow, is step 3.2's reading.
- **The transform's join**: `InputFilter` `$[1:]` drops the label, `JoinSource` `Input` with
  `OutputFilter` `$[0,-1]` writes the label and the score on each line, from which the AUC is recomputed.
