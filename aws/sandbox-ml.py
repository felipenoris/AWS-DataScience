#!/usr/bin/env -S uv run --quiet
# sandbox-ml.py - Stage 17's evidence: the machine learning a SageMaker Unified Studio project
# offers, read in the Sandbox account. The project roles (the ML tag, the managed policy's
# version and its create and tag statements, the D13 boundary's five statements and its
# instance ceiling, the Tooling stack's enableNetworkIsolation), the MLflow Apps, every training
# job against the boundary's four job settings, the Model Registry group ml-demo-xgboost, the
# serving objects (each endpoint with its price, decision 6), the ML pipelines, the entries read
# without being created (HyperPod, Partner AI apps) with the quotas that bound the exercise,
# the Generative AI objects and the roles behind them, the doors a session opens (the interface
# endpoints, the S3 gateway's allow-list, the DNS Firewall list), and CloudTrail's record of
# who created each object, and through which door. Passes 9 and 10's applications in their
# `dev` projects: app-ml's jobs, its leftover model, its candidate, the version it proposed and
# its MLflow run (ML-10); app-genai's guardrail against the checkout's definition, its inference
# profile, its two reports, the deny on its role and the account-level guardrail configuration
# (ML-11).
#
#   needs:    a live SSO session, the only prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             and an AWS CLI that knows `sagemaker list-mlflow-apps`, `s3vectors`,
#             `bedrock get-foundation-model-availability` and
#             `bedrock list-enforced-guardrails-configuration` (2.37.12 knows all four). A CLI
#             that does not fails those calls into section 15, and the checks that needed them
#             say so.
#   run:      ./aws/sandbox-ml.py                        # the Sandbox profile
#             ./aws/sandbox-ml.py awsds-infra-sandbox-1  # the same, named
#             python3 aws/sandbox-ml.py -                # CloudShell, ambient
#   writes:   aws/output/sandbox-ml.txt, and each pipeline's live definition under
#             aws/output/sandbox-ml/ (untracked - see .gitignore)
#   reads:    iam:ListRoles, GetRole, ListAttachedRolePolicies, ListRolePolicies, GetPolicy,
#             GetPolicyVersion;
#             kms:ListAliases; cloudformation:DescribeStacks; sagemaker:ListMlflowApps,
#             DescribeMlflowApp, ListTrainingJobs, DescribeTrainingJob, ListProcessingJobs,
#             DescribeProcessingJob, ListModelPackageGroups,
#             DescribeModelPackageGroup, ListModelPackages, DescribeModelPackage, ListEndpoints,
#             DescribeEndpoint, DescribeEndpointConfig,
#             ListEndpointConfigs, ListModels, DescribeModel, ListTransformJobs,
#             DescribeTransformJob, ListPipelines, DescribePipeline, ListPipelineExecutions,
#             ListPipelineExecutionSteps, ListClusters, ListPartnerApps, DescribeImageVersion,
#             ListTags; servicequotas:ListServiceQuotas, ListAWSDefaultServiceQuotas,
#             ListRequestedServiceQuotaChangeHistory;
#             bedrock:ListGuardrails, GetGuardrail, ListEvaluationJobs,
#             GetFoundationModelAvailability, ListTagsForResource, ListInferenceProfiles,
#             ListEnforcedGuardrailsConfiguration; bedrock-agent (bedrock:) ListKnowledgeBases,
#             GetKnowledgeBase,
#             ListDataSources, ListAgents, ListPrompts, ListFlows; aoss:ListCollections;
#             s3vectors:ListVectorBuckets; lambda:ListFunctions; ec2:DescribeSubnets,
#             DescribeSecurityGroups, DescribeVpcEndpoints; route53resolver:
#             ListFirewallDomainLists, ListFirewallDomains; cloudwatch:ListMetrics,
#             GetMetricStatistics; s3api:HeadObject, ListObjectsV2; s3:GetObject (`aws s3 cp`
#             to stdout, or to a temporary folder for an archive's hash); cloudtrail:LookupEvents;
#             sts:GetCallerIdentity. It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# One profile: everything Stage 17 creates is in the Sandbox account - the project and its
# roles, the jobs, the registry, the endpoints, the pipelines, the MLflow App and the Bedrock
# objects - so awsds-infra-sandbox-1 (the infrastructure user, InfrastructureAccess in Sandbox)
# reads every one of them. The stage's two changes outside it are read elsewhere: the blueprint
# roster in the domain's profile by ./aws/studio.py (US-3), and the SCP amendment as attached by
# ./aws/org-policy-baseline.py, which prints the documents. The SCP's model list is read here
# from this repository's document, the declaration decision 11 amends.
#
# The project is read from the project roles' tags (AmazonDataZoneProject, ...Domain, KmsKeyId,
# DomainBucketName), never from this file, and an object belongs to the project whose role it
# runs as or whose tag it carries. ML-10 and ML-11 name their two projects by id (APP_ML_DEV,
# APP_GENAI_DEV), since a role's tags carry a project's id and not its name.
#
# What it cannot see, since an empty listing and a missing account look alike:
#   - The space: the SDK's configuration files and the interpreters' versions (Stage 17 step
#     0.3) - a person reads them in JupyterLab.
#   - The portal's forms (step 0.7) - a person reads them.
#   - The MLflow data plane's calls and InvokeEndpoint write no management event: the
#     endpoints' BytesProcessed and the Invocations metric (sections 6 and 10) are the
#     readings, and a metric with no traffic in the window is absent, not zero.
#   - An MLflow run's record: ML-10 reads the run app-ml's track task logged through the
#     evaluation artifact it leaves in the app's artifact store.
#   - The quality of a model: the validation AUC is reported, never checked.
#   - "Not built yet" is a note, never a fail.

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from awslib import bedrockscope, context, flowrole, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "sandbox-ml.txt"
DEFS_DIR = "sandbox-ml"

SANDBOX_PROFILE = "awsds-infra-sandbox-1"

# Contracts named in the stage file, so a rename fails loudly rather than silently.
PROJECT_ROLE_PREFIX = "datazone_usr_role_"  # datazone_usr_role_<project>_<environment>
BEDROCK_ROLE_PREFIX = "AmazonBedrock"  # AmazonBedrock*Role-<project>-<env>, measured 2026-08-26
PRIVATE_SUBNET_PREFIX = "awsds-sandbox-private-"
PROJECT_TAG = "AmazonDataZoneProject"
MODEL_GROUP = "ml-demo-xgboost"
# Under each project's shared/: the scripts' data/, models/, predictions/, pipeline/ and bedrock/,
# and the MLflow App's mlflow/.
DEMO_DIR = "ml-demo/"
HOUSE_IMAGE = "awsds-sandbox-dev-env"
XGBOOST_REPOSITORY = "sagemaker-xgboost"  # AWS's algorithm registry; any tag (2.2 names 3.0-5)
PIPELINE_SOURCE = "examples/sandbox-ml/pipeline/definition.json"

# The project role's managed policy. The managed-policy reference read v44 on 2026-10-12; Sandbox
# served v45 on 2026-10-17, whose create, tag and MLflow statements are v44's (the Stage 17 log
# carries the diff).
ML_TAG = "EnableSageMakerMLWorkloadsPermissions"
BEDROCK_TAGS = ("EnableAmazonBedrockPermissions", "EnableAmazonBedrockIDEPermissions")
ML_POLICY = "SageMakerStudioProjectRoleMachineLearningPolicy"
ML_POLICY_VERSION = "v45"
SID_CREATE = "SageMakerCreatePermissions"
SID_TAG = "SageMakerTagPermissions"
SID_MLFLOW = "SageMakerMlflowServerlessPermission"

# The D13 boundary's five statements (terraform-modules/sagemaker-denies), and the instance types
# the exercise asks for. The ceiling is read from the live boundary, never copied here.
BOUNDARY_SIDS = (
    "DenySageMakerJobsOffVpc",
    "DenySageMakerInstanceCeiling",
    "DenySageMakerJobsWithoutNetworkIsolation",
    "DenySageMakerJobsWithoutInterContainerEncryption",
    "DenySageMakerJobsWithoutVolumeEncryption",
)
SID_CEILING = "DenySageMakerInstanceCeiling"
EXERCISE_TYPES = (
    ("training, step 2.2", "ml.m5.xlarge"),
    ("endpoint, step 4.1", "ml.m5.large"),
    ("transform, step 4.3", "ml.m5.large"),
    ("processing, step 5.1", "ml.t3.medium"),
)
CEILING_NEGATIVE = "ml.m5.2xlarge"  # step 2.3's fifth negative, refused while it is off the list

# Real-time hosting per instance-hour in us-west-2 (docs/PRICING.md, measured 2026-10-12). An
# endpoint on a type missing here is printed with its count and no price.
HOSTING_USD_PER_HOUR = {"ml.m5.large": 0.115}

# Step 0.2's quotas, by the names Service Quotas gives them. A zero stops the stage.
QUOTAS = (
    "ml.m5.xlarge for training job usage",
    "ml.m5.large for endpoint usage",
    "ml.m5.large for transform job usage",
    "ml.t3.medium for processing job usage",
)

# The Tooling environment's stack, and the parameter step 0.8 reads.
TOOLING_STACK = "DataZone-Env-{env}"
ISOLATION_PARAMETER = "enableNetworkIsolation"

# The session's doors (step 0.5). The interface endpoints are [E]: sandbox/egress raises them.
ALWAYS_ON = ("sagemaker.api", "sagemaker.runtime", "ecr.api", "ecr.dkr", "logs", "kms", "sts")
MLFLOW_SERVICE = f"aws.sagemaker.{context.REGION}.mlflow"
EXPERIMENTS_SERVICE = f"aws.sagemaker.{context.REGION}.experiments"
RUNTIME_SERVICE = f"com.amazonaws.{context.REGION}.sagemaker.runtime"
S3_GATEWAY_NAME = "awsds-sandbox-s3-gateway"
GATEWAY_SID = "AllowAwsOwnedServiceBuckets"
GATEWAY_BUCKETS = (f"sagemaker-{context.REGION}", f"jumpstart-cache-prod-{context.REGION}")
DNS_LIST = "awsds-sandbox-egress-allow"
# The MLflow data plane's names, unknown until step 1.6 reads which name the client resolves
# (verification vi). Each name written here is then checked against the DNS Firewall list.
MLFLOW_NAMES: tuple = ()

# Control Tower deploys its own functions into every enrolled account; ML-8 judges the others.
CONTROL_TOWER_FUNCTION_PREFIX = "aws-controltower-"

# Pass 7: the knowledge base's embeddings model (decision 11) and the store decision 12 keeps.
EMBEDDINGS_MODEL = "amazon.titan-embed-text-v2:0"
IDLE_FREE_STORES = ("S3_VECTORS",)

# Passes 9 and 10's `dev` projects (steps 9.6 and 10.4), by id: a project role's tags carry its
# project's id and not its name, so the names are written here, as catalog.py writes app-etl-dev's.
APP_ML_DEV = "5rzplmk81vma34"  # app-ml-dev
APP_GENAI_DEV = "b8fz4ovppjijv4"  # app-genai-dev

# app-ml's names in its `dev` project (examples/app-ml/manifest.yaml and workflows/): each job kind
# with the name prefix its workflow gives it and the workflows that create it; the model resolve
# creates, app-ml-score-<project id>; the candidate publish writes under shared/; the group register
# proposes in, and how a version's description carries the archive's hash (registry.py).
APP_ML_JOBS = (
    ("processing", "app-ml-prepare-", "app-ml-train and app-ml-score"),
    ("training", "app-ml-train-", "app-ml-train"),
    ("transform", "app-ml-score-", "app-ml-score"),
)
APP_ML_MODEL_PREFIX = "app-ml-score-"
APP_ML_CANDIDATE = "app-ml/models/latest/"
APP_ML_GROUP = "app-ml-dev"
APP_ML_HASH_MARK = "sha256:"
# A model resolve created and cleanup has not deleted: younger, a run in progress or one that
# failed; older, a failed run no run has followed (9.9).
MODEL_MAX_AGE = timedelta(days=1)
# No gate reads a `dev` version's status, and 9.6 approves one by hand.
DEV_VERSION_STATUSES = ("PendingManualApproval", "Approved")
# track logs the evaluation as the run's artifact evaluation.json, which MLflow keeps under
# <artifact store>/<experiment id>/<run id>/artifacts/: a layout unmeasured on an MLflow App here.
MLFLOW_EVALUATION_SUFFIX = "/artifacts/evaluation.json"
MLFLOW_RUNS_READ = 5  # the newest evaluation artifacts read

# app-genai's names in its `dev` project (examples/app-genai/): the guardrail its guardrail task
# keeps, app-genai-<project id>, and the two tags it writes after a publish; the definition in the
# checkout; the model of decision 23 (a); the reports under shared/ with the workflow writing each;
# the policy sandbox/bedrock attaches to the role, the statement application_guardrail_required adds
# to it (10.4 step 4), and the guardrail account_guardrail_enabled creates (10.4 step 6).
GENAI_GUARDRAIL_PREFIX = "app-genai-"
GENAI_HASH_TAG = "awsds:definition-sha256"
GENAI_VERSION_TAG = "awsds:definition-version"
GENAI_DEFINITION = "examples/app-genai/guardrail/definition.json"
GENAI_MODEL = "amazon.nova-lite-v1:0"
GENAI_OUTBOX = "app-genai/outbox/"
GENAI_REPORTS = (
    ("triage-report.json", "app-genai-triage"),
    ("probe-report.json", "app-genai-probe"),
)
GENAI_POLICY = "awsds-sandbox-bedrock-application"
GENAI_DENY_SID = "DenyAnInvocationWithNoPublishedGuardrailOfTheAccount"
ACCOUNT_GUARDRAIL = "awsds-sandbox-account-guardrail"

SAGEMAKER_EVENTS = (
    "CreateMlflowApp",
    "CreateTrainingJob",
    "CreateModelPackageGroup",
    "CreateModelPackage",
    "CreateModel",
    "CreateEndpointConfig",
    "CreateEndpoint",
    "CreateTransformJob",
    "CreatePipeline",
    "StartPipelineExecution",
)
BEDROCK_EVENTS = (
    "CreateKnowledgeBase",
    "CreateDataSource",
    "StartIngestionJob",
    "CreateAgent",
    "CreateAgentAlias",
    "CreateGuardrail",
    "CreatePrompt",
    "CreateFlow",
    "CreateEvaluationJob",
)
# A training job's image pull, read for XGBoost's repository only (6i iv read the pull of the
# house image as the project role, session SageMaker, through no endpoint).
PULL_EVENT = "BatchGetImage"
# The request field that names what an event created, in the order tried.
SUBJECT_KEYS = (
    "trainingJobName",
    "transformJobName",
    "endpointName",
    "endpointConfigName",
    "modelName",
    "modelPackageGroupName",
    "pipelineName",
    "agentName",
    "agentAliasName",
    "jobName",
    "name",
    "knowledgeBaseId",
    "repositoryName",
)

JOBS_MAX = 20  # recent training and transform jobs read
JOB_QUERY = (
    "{Status:TrainingJobStatus,Failure:FailureReason,Output:OutputDataConfig,"
    "Metrics:FinalMetricDataList}"
)
LOOKUP_MAX = 50  # CloudTrail page per event name: --max-results turns the CLI's paging off
METRIC_DAYS = 14  # list-metrics returns only the metrics with data in the last two weeks

# CloudFormation says ValidationError for a missing stack, SageMaker ValidationException.
ABSENT = (
    "NoSuchEntity|ResourceNotFound|Validation(Exception|Error).*does not exist|NoSuchKey|Not Found"
)
UNREAD = "(unread)"  # a value whose call failed: the call is in section 15

# A training job's terminal and transient states, as DescribeTrainingJob spells them; transform
# jobs use the same words.
RUNNING = ("InProgress", "Stopping")


def as_list(value) -> list:
    """An IAM element that may be a string or a list, as a list."""
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)


def statements_by_sid(doc: dict) -> dict:
    return {st.get("Sid", ""): st for st in as_list((doc or {}).get("Statement"))}


def condition_keys(statement: dict) -> list:
    """Every condition key a statement names, operators flattened."""
    keys = []
    for block in (statement.get("Condition") or {}).values():
        keys.extend(block.keys())
    return sorted(set(keys))


def tag_key_admitted(statement: dict, key: str) -> bool | None:
    """Whether a statement's aws:TagKeys conditions admit a request that writes ``key`` alone.

    True or False when every aws:TagKeys operator is one of the four string families read below;
    None when an operator outside them appears, so the reading is printed rather than guessed.
    A statement with no aws:TagKeys condition admits every key.
    """
    verdicts = []
    for operator, block in (statement.get("Condition") or {}).items():
        if "aws:TagKeys" not in block:
            continue
        patterns = as_list(block["aws:TagKeys"])
        base = operator.split(":")[-1].replace("IfExists", "")
        if base == "StringLike":
            verdicts.append(any(fnmatch.fnmatchcase(key, p) for p in patterns))
        elif base == "StringEquals":
            verdicts.append(key in patterns)
        elif base == "StringNotLike":
            verdicts.append(not any(fnmatch.fnmatchcase(key, p) for p in patterns))
        elif base == "StringNotEquals":
            verdicts.append(key not in patterns)
        else:
            return None
    return all(verdicts)


def actions_include(statement: dict, action: str) -> bool:
    service = action.split(":", 1)[0]
    return any(
        a == action or a == f"{service}:*" or a == "*" or fnmatch.fnmatchcase(action, a)
        for a in as_list(statement.get("Action"))
    )


def resource_types(statement: dict) -> list:
    """The SageMaker resource types a statement's ARNs name: processing-job, training-job, ..."""
    out = []
    for arn in as_list(statement.get("Resource")):
        parts = arn.split(":", 5)
        out.append(parts[5].split("/", 1)[0] if len(parts) == 6 else arn)
    return sorted(set(out))


def ceiling_types(boundary: dict) -> list | None:
    """The instance types DenySageMakerInstanceCeiling leaves alone, or None when unreadable."""
    st = statements_by_sid(boundary).get(SID_CEILING)
    if st is None:
        return None
    for operator, block in (st.get("Condition") or {}).items():
        if "sagemaker:InstanceTypes" in block and operator.endswith("StringNotEquals"):
            return sorted(as_list(block["sagemaker:InstanceTypes"]))
    return None


def covered(name: str, entries: list) -> str | None:
    """The DNS Firewall entry that matches ``name``, or None. An entry matches exactly; `*.x`
    matches every level beneath x and never x itself (dns-firewall.tf, vpc-egress)."""
    fqdn = name.rstrip(".") + "."
    for entry in entries:
        if entry == fqdn:
            return entry
        if entry.startswith("*.") and fqdn.endswith(entry[1:]) and fqdn != entry[2:]:
            return entry
    return None


def short_service(service: str) -> str:
    """com.amazonaws.us-west-2.ecr.api -> ecr.api; aws.sagemaker.us-west-2.mlflow -> mlflow.
    The second spelling is shortened past `sagemaker.`, unlike context.short_svc."""
    out = context.short_svc(service)
    return out[len("aws.sagemaker.") :] if out.startswith("aws.sagemaker.") else out


def devenv_de5(text: str) -> tuple:
    """(generated stamp, result, detail) of DE-5 in a devenv.txt report, or ('-', None, '')."""
    stamp = "-"
    m = re.search(r"^generated\s*:\s*(\S+)", text, re.M)
    if m:
        stamp = m.group(1)
    for line in text.splitlines():
        fields = re.split(r"\s{2,}", line.strip())
        if len(fields) >= 3 and fields[1] == "DE-5" and fields[0] in ("pass", "fail", "note"):
            return stamp, fields[0], fields[-1]
    return stamp, None, ""


def all_steps(definition: dict) -> list:
    """Every step of a pipeline definition, a Condition step's IfSteps and ElseSteps included."""
    out, pending = [], list(definition.get("Steps", []))
    while pending:
        step = pending.pop(0)
        out.append(step)
        if step.get("Type") == "Condition":
            args = step.get("Arguments") or {}
            pending.extend(args.get("IfSteps", []) + args.get("ElseSteps", []))
    return out


def step_settings(step: dict) -> tuple:
    """(instance type, problems, parameterized) for one Training, Processing or Transform step of
    a pipeline definition. A value that is a {"Get": ...} reference is reported as parameterized:
    the execution's own job is what ML-3 reads. A Processing step's network isolation is not read:
    the boundary leaves it to the application since Stage 20 decision 13 (TM-35)."""
    args = step.get("Arguments") or {}
    kind = step.get("Type")
    if kind == "Training":
        res = args.get("ResourceConfig") or {}
        vpc = args.get("VpcConfig")
        fields = {
            "VpcConfig": vpc,
            "EnableNetworkIsolation": args.get("EnableNetworkIsolation"),
            "EnableInterContainerTrafficEncryption": args.get(
                "EnableInterContainerTrafficEncryption"
            ),
            "VolumeKmsKeyId": res.get("VolumeKmsKeyId"),
        }
        itype = res.get("InstanceType")
    elif kind == "Processing":
        net = args.get("NetworkConfig") or {}
        cluster = (args.get("ProcessingResources") or {}).get("ClusterConfig") or {}
        fields = {
            "VpcConfig": net.get("VpcConfig"),
            "EnableInterContainerTrafficEncryption": net.get(
                "EnableInterContainerTrafficEncryption"
            ),
            "VolumeKmsKeyId": cluster.get("VolumeKmsKeyId"),
        }
        itype = cluster.get("InstanceType")
    elif kind == "Transform":
        res = args.get("TransformResources") or {}
        fields = {"VolumeKmsKeyId": res.get("VolumeKmsKeyId")}
        itype = res.get("InstanceType")
    else:
        return None, [], []
    problems, parameterized = [], []
    for field, value in fields.items():
        if isinstance(value, dict) and ("Get" in value or "Std:Join" in value):
            parameterized.append(field)
        elif field in ("EnableNetworkIsolation", "EnableInterContainerTrafficEncryption"):
            if value is not True:
                problems.append(f"{field} {value}")
        elif not value:
            problems.append(f"no {field}")
    if isinstance(itype, dict):
        parameterized.append("InstanceType")
        itype = None
    return itype, problems, parameterized


def utc_iso(when: datetime) -> str:
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def last_segment(arn: str | None) -> str:
    """The last path segment of an ARN or a URI, or '-'."""
    return (arn or "-").rsplit("/", 1)[-1]


def quota_text(value) -> str:
    """A Service Quotas value as the console prints it: 1, not 1.0."""
    return "-" if value is None else f"{value:g}"


def request_text(requests: dict | None, code: str) -> str:
    """A quota's newest increase request as one phrase; None means the history went unread."""
    if requests is None:
        return "its increase requests unread (section 15)"
    request = requests.get(code)
    if not request:
        return "no increase request"
    created = str(request.get("Created") or "-")[:10]
    return (
        f"increase to {quota_text(request.get('DesiredValue'))} requested {created}, "
        f"{request.get('Status', '-')}"
    )


def endpoint_summary(endpoint: dict, now: datetime) -> str:
    """An endpoint as ML-5 prints it: its status, its age and its price (decision 6)."""
    status = endpoint.get("EndpointStatus", "-")
    created = endpoint.get("CreationTime")
    try:
        age = now - datetime.fromisoformat(str(created))
        hours = age.total_seconds() / 3600
        age_text = f"{hours:.0f} h old" if hours < 48 else f"{hours / 24:.1f} days old"
    except ValueError:
        age_text = "of unread age"
    variants = endpoint.get("_variants")
    if variants is None:
        return f"{status} since {created}, {age_text}; its configuration unread, so no price."
    hourly, parts = 0.0, []
    for name, itype, count in variants:
        if itype == "serverless":
            parts.append(f"{name} serverless, billed per request")
            continue
        price = HOSTING_USD_PER_HOUR.get(itype)
        if price is None or count is None:
            parts.append(f"{name} {count} x {itype}, not priced here (docs/PRICING.md)")
            continue
        hourly += price * count
        parts.append(f"{name} {count} x {itype}")
    return (
        f"{status} since {created}, {age_text}; {', '.join(parts) or 'no variant'}: "
        f"{hourly:.3f} USD/h, {hourly * 24:.2f} a day, until its member deletes it."
    )


def job_view(kind: str, job: dict) -> dict:
    """What ML-10 judges of one processing, training or transform job, in one shape. A transform
    job carries no network settings: they are its model's, which app-ml-score's cleanup deletes."""
    noun = kind.capitalize()
    vpc = isolation = ice = None
    if kind == "processing":
        net = job.get("NetworkConfig") or {}
        cluster = (job.get("ProcessingResources") or {}).get("ClusterConfig") or {}
        vpc = net.get("VpcConfig") or {}
        isolation = net.get("EnableNetworkIsolation")
        ice = net.get("EnableInterContainerTrafficEncryption")
        volume_key, itype = cluster.get("VolumeKmsKeyId"), cluster.get("InstanceType", "-")
        output_key = (job.get("ProcessingOutputConfig") or {}).get("KmsKeyId")
    elif kind == "training":
        res = job.get("ResourceConfig") or {}
        vpc = job.get("VpcConfig") or {}
        isolation = job.get("EnableNetworkIsolation")
        ice = job.get("EnableInterContainerTrafficEncryption")
        volume_key, itype = res.get("VolumeKmsKeyId"), res.get("InstanceType", "-")
        output_key = (job.get("OutputDataConfig") or {}).get("KmsKeyId")
    else:
        res = job.get("TransformResources") or {}
        volume_key, itype = res.get("VolumeKmsKeyId"), res.get("InstanceType", "-")
        output_key = (job.get("TransformOutput") or {}).get("KmsKeyId")
    return {
        "name": job.get(f"{noun}JobName", "-"),
        "status": job.get(f"{noun}JobStatus", "-"),
        "failure": job.get("FailureReason"),
        "vpc": vpc,
        "isolation": isolation,
        "ice": ice,
        "volume_key": volume_key,
        "output_key": output_key,
        "itype": itype,
    }


def definition_hash(definition: dict) -> str:
    """The SHA-256 app-genai's guardrail task publishes a version under: the definition's JSON with
    sorted keys and no spaces, as UTF-8 (examples/app-genai/code/app_genai_tasks/guardrail.py)."""
    text = json.dumps(definition, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def age_of(value, now: datetime) -> timedelta | None:
    """How long before ``now`` a timestamp the CLI printed lies, or None when it does not parse."""
    try:
        return now - datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def hours_text(age: timedelta) -> str:
    hours = age.total_seconds() / 3600
    return f"{hours:.0f} h" if hours < 48 else f"{hours / 24:.1f} days"


def principal_name(arn: str | None) -> str:
    """The role an assumed-role or role ARN names, without its session, or '-'."""
    arn = arn or ""
    if ":assumed-role/" in arn:
        return arn.split(":assumed-role/", 1)[1].split("/", 1)[0]
    return last_segment(arn) if arn else "-"


def cell(value) -> str:
    """A table cell: tabulate drops an empty field, so None and '' print as '-'."""
    return "-" if value is None or value == "" else str(value)


def short_hash(value) -> str:
    """A SHA-256 as a check row prints it: its first 12 hex digits, or '-'."""
    return str(value)[:12] if value else "-"


def flat(text) -> str:
    """Free text on one line: a check row is tab-separated, and a reason can hold either."""
    return " ".join(str(text).split())


def arn_region(arn: str | None) -> str:
    """The Region field of an ARN, or '-'."""
    parts = (arn or "").split(":")
    return parts[3] if len(parts) > 3 and parts[3] else "-"


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)
    defs_root = ctx.out_dir / DEFS_DIR

    selected = list(argv) if argv else [SANDBOX_PROFILE]
    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c for c in callers if c.live]
    checks = Checks()

    cli = AwsCli(profile=live[0].profile, region=context.REGION, errors=errors, echo_profile=True)
    account = live[0].account

    def logerr(what: str, err: str) -> None:
        errors.entries.append(f"[{cli.label}] aws {what}\n    {head2(err)}")

    def run_json(*args: str, tolerate: str | None = None):
        res = cli.run(*args, "--output", "json", log=False, tolerate=tolerate)
        if res.tolerated:
            return None
        if not res.ok:
            logerr(" ".join(args)[:160], res.stderr or res.stdout)
            return None
        return json.loads(res.stdout or "{}")

    policy_dates = {}  # policy ARN -> its default version's CreateDate

    def policy_document(arn: str) -> tuple:
        """(default version id, document) of a managed policy, or ('-', None)."""
        got = run_json("iam", "get-policy", "--policy-arn", arn) or {}
        version = (got.get("Policy") or {}).get("DefaultVersionId")
        if not version:
            return "-", None
        doc = (
            run_json("iam", "get-policy-version", "--policy-arn", arn, "--version-id", version)
            or {}
        ).get("PolicyVersion") or {}
        policy_dates[arn] = doc.get("CreateDate")
        return version, doc.get("Document")

    def tags_of(arn: str) -> dict:
        got = run_json("sagemaker", "list-tags", "--resource-arn", arn) or {}
        return {t["Key"]: t["Value"] for t in got.get("Tags", [])}

    def s3_objects(bucket: str, prefix: str) -> list | None:
        """Every object under a prefix but a folder marker, or None when the listing failed."""
        got = run_json("s3api", "list-objects-v2", "--bucket", bucket, "--prefix", prefix)
        if got is None:
            return None
        return [o for o in got.get("Contents") or [] if not o.get("Key", "").endswith("/")]

    def s3_text(bucket: str, key: str) -> str | None:
        """An object's text through `aws s3 cp` to stdout, or None when the read failed."""
        res = cli.run("s3", "cp", f"s3://{bucket}/{key}", "-")
        return res.stdout if res.ok else None

    def s3_sha256(bucket: str, key: str) -> str | None:
        """The SHA-256 of an object's bytes, copied into a temporary folder the run removes, or
        None when the read failed."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "object"
            res = cli.run("s3", "cp", f"s3://{bucket}/{key}", str(path), "--only-show-errors")
            if not res.ok:
                return None
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1 << 20), b""):
                    digest.update(block)
            return digest.hexdigest()

    note(f"measuring {cli.label} ...")
    now = datetime.now(timezone.utc)

    # ------------------------------------------------------------------ the project(s)
    projects = {}  # role name -> dict
    policies = {}  # policy ARN -> (version, document), each read once
    roles = run_json(
        "iam",
        "list-roles",
        "--query",
        f"Roles[?starts_with(RoleName, '{PROJECT_ROLE_PREFIX}')].RoleName",
    )
    for rname in sorted(roles or []):
        role = run_json("iam", "get-role", "--role-name", rname)
        if not role:
            continue
        r = role.get("Role", {})
        tags = {t["Key"]: t["Value"] for t in r.get("Tags", [])}
        key_id = tags.get("KmsKeyId", "")
        aliases = run_json("kms", "list-aliases", "--key-id", key_id) if key_id else None
        attached = (run_json("iam", "list-attached-role-policies", "--role-name", rname) or {}).get(
            "AttachedPolicies", []
        )
        for pol in attached:
            arn = pol.get("PolicyArn", "")
            if arn and arn not in policies:
                policies[arn] = policy_document(arn)
        boundary = (r.get("PermissionsBoundary") or {}).get("PermissionsBoundaryArn", "")
        if boundary and boundary not in policies:
            policies[boundary] = policy_document(boundary)
        domain, project = tags.get("AmazonDataZoneDomain", ""), tags.get(PROJECT_TAG, "")
        # datazone_usr_role_<project>_<environment>: neither id holds an underscore.
        rest = rname[len(PROJECT_ROLE_PREFIX) :]
        env = rest.split("_", 1)[1] if "_" in rest else ""
        projects[rname] = {
            "role": rname,
            "arn": r.get("Arn", ""),
            "tags": tags,
            "boundary": boundary,
            "attached": attached,
            "project": project,
            "domain": domain,
            "env": env,
            "key_id": key_id,
            "key_aliases": [a.get("AliasName", "") for a in (aliases or {}).get("Aliases", [])],
            "bucket": tags.get("DomainBucketName", ""),
            "prefix": f"{domain}/{project}/",
            "shared": f"{domain}/{project}/shared/",
        }
    by_arn = {p["arn"]: p for p in projects.values()}
    by_project = {p["project"]: p for p in projects.values() if p["project"]}

    def is_project_key(value: str | None, p: dict) -> bool:
        """Whether a KmsKeyId field names the project's key: its id, its ARN, or an alias of it."""
        if not value:
            return False
        if p["key_id"] and p["key_id"] in value:
            return True
        return any(a and value.endswith(a) for a in p["key_aliases"])

    def project_of_uri(uri: str) -> dict | None:
        """The project whose prefix an s3:// URI lies under."""
        for p in projects.values():
            if p["bucket"] and uri.startswith(f"s3://{p['bucket']}/{p['prefix']}"):
                return p
        return None

    # The Tooling stack of each project, for step 0.8's parameter. Its parameter keys are kept,
    # so a run that does not find the name shows what the stack does carry.
    stacks = {}  # role -> (stack name, status, parameter value or None, parameter keys)
    for p in projects.values():
        if not p["env"]:
            continue
        name = TOOLING_STACK.format(env=p["env"])
        got = run_json("cloudformation", "describe-stacks", "--stack-name", name, tolerate=ABSENT)
        stack = ((got or {}).get("Stacks") or [None])[0]
        if stack is None:
            stacks[p["role"]] = (name, "absent", None, [])
            continue
        value, keys = None, []
        for par in stack.get("Parameters", []):
            keys.append(par.get("ParameterKey", ""))
            if par.get("ParameterKey", "").lower() == ISOLATION_PARAMETER.lower():
                value = par.get("ParameterValue")
        stacks[p["role"]] = (name, stack.get("StackStatus", "-"), value, sorted(keys))

    # Every Bedrock-family role the Tooling and Bedrock blueprints create in this account.
    bedrock_roles = []
    names = run_json(
        "iam",
        "list-roles",
        "--query",
        f"Roles[?starts_with(RoleName, '{BEDROCK_ROLE_PREFIX}')].RoleName",
    )
    for rname in sorted(names or []):
        role = (run_json("iam", "get-role", "--role-name", rname) or {}).get("Role", {})
        attached = (run_json("iam", "list-attached-role-policies", "--role-name", rname) or {}).get(
            "AttachedPolicies", []
        )
        inline = (run_json("iam", "list-role-policies", "--role-name", rname) or {}).get(
            "PolicyNames", []
        )
        bedrock_roles.append(
            {
                "name": rname,
                "boundary": (role.get("PermissionsBoundary") or {}).get(
                    "PermissionsBoundaryArn", ""
                ),
                "project": {t["Key"]: t["Value"] for t in role.get("Tags", [])}.get(
                    PROJECT_TAG, ""
                ),
                "policies": [a.get("PolicyName", "") for a in attached],
                "inline": inline,
                "trust": role.get("AssumeRolePolicyDocument"),
            }
        )

    # ------------------------------------------------------------------ the house image
    image = run_json(
        "sagemaker", "describe-image-version", "--image-name", HOUSE_IMAGE, tolerate=ABSENT
    )
    container_image = (image or {}).get("ContainerImage", "")
    image_digest = container_image.split("@", 1)[1] if "@" in container_image else ""

    # ------------------------------------------------------------------ the MLflow Apps
    apps = []
    listed = run_json("sagemaker", "list-mlflow-apps") or {}
    for summary in listed.get("Summaries", []):
        if summary.get("Status") == "Deleted":
            continue
        arn = summary.get("Arn", "")
        desc = run_json("sagemaker", "describe-mlflow-app", "--arn", arn) or dict(summary)
        desc["_tags"] = tags_of(arn)
        apps.append(desc)

    # ------------------------------------------------------------------ training jobs
    def recent(kind: str, key: str) -> list:
        got = (
            run_json(
                "sagemaker",
                f"list-{kind}s",
                "--sort-by",
                "CreationTime",
                "--sort-order",
                "Descending",
                "--max-results",
                str(JOBS_MAX),
            )
            or {}
        )
        return got.get(key, [])

    def named_jobs(kind: str, prefix: str) -> list:
        """The newest jobs of one kind whose name holds ``prefix``, each described and tagged.
        --max-items and not --max-results: the service filters a page after reading it, so one
        page can be empty with more to read (list-processing-jobs, measured 2026-11-20)."""
        noun = kind.capitalize()
        got = (
            run_json(
                "sagemaker",
                f"list-{kind}-jobs",
                "--name-contains",
                prefix,
                "--sort-by",
                "CreationTime",
                "--sort-order",
                "Descending",
                "--max-items",
                str(JOBS_MAX),
            )
            or {}
        )
        out = []
        for summary in got.get(f"{noun}JobSummaries", []):
            name = summary.get(f"{noun}JobName", "")
            desc = run_json("sagemaker", f"describe-{kind}-job", f"--{kind}-job-name", name)
            desc = desc or dict(summary)
            desc["_tags"] = tags_of(desc.get(f"{noun}JobArn", summary.get(f"{noun}JobArn", "")))
            out.append(desc)
        return out

    jobs = []
    for summary in recent("training-job", "TrainingJobSummaries"):
        name = summary.get("TrainingJobName", "")
        desc = run_json("sagemaker", "describe-training-job", "--training-job-name", name) or {}
        desc["_tags"] = tags_of(desc.get("TrainingJobArn", summary.get("TrainingJobArn", "")))
        jobs.append(desc)

    # ------------------------------------------------------------------ the registry
    group = run_json(
        "sagemaker",
        "describe-model-package-group",
        "--model-package-group-name",
        MODEL_GROUP,
        tolerate=ABSENT,
    )
    group_tags = tags_of(group["ModelPackageGroupArn"]) if group else {}
    packages = []
    if group:
        listed = (
            run_json("sagemaker", "list-model-packages", "--model-package-group-name", MODEL_GROUP)
            or {}
        )
        for summary in listed.get("ModelPackageSummaryList", []):
            arn = summary.get("ModelPackageArn", "")
            desc = run_json("sagemaker", "describe-model-package", "--model-package-name", arn)
            packages.append(desc or summary)
    all_groups = [
        g.get("ModelPackageGroupName", "")
        for g in (run_json("sagemaker", "list-model-package-groups") or {}).get(
            "ModelPackageGroupSummaryList", []
        )
    ]
    model_data = {}  # ModelDataUrl -> SSEKMSKeyId or the encryption it reads
    for pkg in packages:
        for container in (pkg.get("InferenceSpecification") or {}).get("Containers", []):
            url = container.get("ModelDataUrl", "")
            m = re.match(r"^s3://([^/]+)/(.+)$", url)
            if not m or url in model_data:
                continue
            head = run_json("s3api", "head-object", "--bucket", m.group(1), "--key", m.group(2))
            if head is None:
                model_data[url] = UNREAD
            else:
                model_data[url] = head.get("SSEKMSKeyId", head.get("ServerSideEncryption", "-"))

    # ------------------------------------------------------------------ serving
    endpoints = (run_json("sagemaker", "list-endpoints") or {}).get("Endpoints", [])
    for e in endpoints:
        # The instance type is the configuration's, the count the endpoint's (decision 6's price).
        desc = run_json("sagemaker", "describe-endpoint", "--endpoint-name", e["EndpointName"])
        config_name = (desc or {}).get("EndpointConfigName")
        config = (
            run_json("sagemaker", "describe-endpoint-config", "--endpoint-config-name", config_name)
            if config_name
            else None
        )
        counts = {
            v.get("VariantName"): v.get("CurrentInstanceCount")
            for v in (desc or {}).get("ProductionVariants", [])
        }
        e["_variants"] = (
            None
            if config is None
            else [
                (
                    v.get("VariantName", "-"),
                    "serverless" if v.get("ServerlessConfig") else v.get("InstanceType", "-"),
                    counts.get(v.get("VariantName"), v.get("InitialInstanceCount")),
                )
                for v in config.get("ProductionVariants", [])
            ]
        )
    endpoint_configs = (run_json("sagemaker", "list-endpoint-configs") or {}).get(
        "EndpointConfigs", []
    )
    models = []
    for summary in (run_json("sagemaker", "list-models") or {}).get("Models", []):
        desc = run_json("sagemaker", "describe-model", "--model-name", summary["ModelName"])
        models.append(desc or summary)
    transforms = []
    for summary in recent("transform-job", "TransformJobSummaries"):
        name = summary.get("TransformJobName", "")
        desc = run_json("sagemaker", "describe-transform-job", "--transform-job-name", name) or {}
        desc["_tags"] = tags_of(desc.get("TransformJobArn", summary.get("TransformJobArn", "")))
        transforms.append(desc)

    # ------------------------------------------------------------------ pipelines
    pipelines = []
    for summary in (run_json("sagemaker", "list-pipelines") or {}).get("PipelineSummaries", []):
        name = summary.get("PipelineName", "")
        desc = run_json("sagemaker", "describe-pipeline", "--pipeline-name", name) or {}
        executions = (
            run_json(
                "sagemaker",
                "list-pipeline-executions",
                "--pipeline-name",
                name,
                "--sort-by",
                "CreationTime",
                "--sort-order",
                "Descending",
                "--max-results",
                "5",
            )
            or {}
        ).get("PipelineExecutionSummaries", [])
        steps = []
        if executions:
            steps = (
                run_json(
                    "sagemaker",
                    "list-pipeline-execution-steps",
                    "--pipeline-execution-arn",
                    executions[0].get("PipelineExecutionArn", ""),
                )
                or {}
            ).get("PipelineExecutionSteps", [])
        try:
            definition = json.loads(desc.get("PipelineDefinition") or "{}")
        except json.JSONDecodeError:
            definition = {}
        if desc.get("PipelineDefinition"):
            defs_root.mkdir(parents=True, exist_ok=True)
            (defs_root / f"{name}.json").write_text(
                json.dumps(definition, indent=2, sort_keys=True) + "\n"
            )
        pipelines.append(
            {
                "name": name,
                "desc": desc,
                "definition": definition,
                "executions": executions,
                "steps": steps,
            }
        )
    source_path = ctx.repo_root / PIPELINE_SOURCE
    try:
        source = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        source = None

    # ------------------------------------------------------------------ entries read, not built
    clusters = (run_json("sagemaker", "list-clusters") or {}).get("ClusterSummaries", [])
    partner_apps = (run_json("sagemaker", "list-partner-apps") or {}).get("Summaries", [])
    applied = (
        run_json("service-quotas", "list-service-quotas", "--service-code", "sagemaker") or {}
    ).get("Quotas", [])
    defaults = (
        run_json("service-quotas", "list-aws-default-service-quotas", "--service-code", "sagemaker")
        or {}
    ).get("Quotas", [])
    quota_rows = {}  # name -> (value, source, code)
    for source_name, listing in (("default", defaults), ("applied", applied)):
        for q in listing:
            quota_rows[q.get("QuotaName", "")] = (
                q.get("Value"),
                source_name,
                q.get("QuotaCode", "-"),
            )
    # An increase below AWS's default is refused (6d, 2026-09-13), so the default is the floor.
    quota_defaults = {q.get("QuotaName", ""): q.get("Value") for q in defaults}
    mlflow_quotas = sorted(n for n in quota_rows if "mlflow" in n.lower())
    # Each quota's newest increase request, by code: a zero with a request open is still a stop,
    # and the request's status says whether it is ending. Timestamps are ISO 8601 in one offset,
    # so the string order is the time order.
    history = run_json(
        "service-quotas",
        "list-requested-service-quota-change-history",
        "--service-code",
        "sagemaker",
    )
    quota_requests = None if history is None else {}  # code -> the newest request
    for r in (history or {}).get("RequestedQuotas", []):
        code = r.get("QuotaCode", "")
        newest = quota_requests.get(code, {})
        if str(r.get("Created") or "") >= str(newest.get("Created") or ""):
            quota_requests[code] = r

    # ------------------------------------------------------------------ Generative AI
    every_function = (run_json("lambda", "list-functions") or {}).get("Functions", [])
    functions = [
        f
        for f in every_function
        if not f.get("FunctionName", "").startswith(CONTROL_TOWER_FUNCTION_PREFIX)
    ]
    kbs = []
    for summary in (run_json("bedrock-agent", "list-knowledge-bases") or {}).get(
        "knowledgeBaseSummaries", []
    ):
        kb_id = summary.get("knowledgeBaseId", "")
        got = (
            run_json("bedrock-agent", "get-knowledge-base", "--knowledge-base-id", kb_id) or {}
        ).get("knowledgeBase", dict(summary))
        sources = (
            run_json("bedrock-agent", "list-data-sources", "--knowledge-base-id", kb_id) or {}
        ).get("dataSourceSummaries", [])
        got["_sources"] = sources
        kbs.append(got)
    # ListCollections has no CLI paginator: pages() follows its nextToken.
    collection_listing = cli.pages("opensearchserverless", "list-collections", token="nextToken")
    collections = collection_listing.items("collectionSummaries")
    vector_buckets = (run_json("s3vectors", "list-vector-buckets") or {}).get("vectorBuckets", [])
    # Without an identifier, ListGuardrails lists the DRAFT of every guardrail of the account.
    guardrail_summaries = (run_json("bedrock", "list-guardrails") or {}).get("guardrails", [])
    genai = {  # kind -> [(name, arn or id)]
        "agents": [
            (a.get("agentName", "-"), a.get("agentId", "-"))
            for a in (run_json("bedrock-agent", "list-agents") or {}).get("agentSummaries", [])
        ],
        "prompts": [
            (x.get("name", "-"), x.get("arn", "-"))
            for x in (run_json("bedrock-agent", "list-prompts") or {}).get("promptSummaries", [])
        ],
        "flows": [
            (x.get("name", "-"), x.get("arn", "-"))
            for x in (run_json("bedrock-agent", "list-flows") or {}).get("flowSummaries", [])
        ],
        "guardrails": [(x.get("name", "-"), x.get("arn", "-")) for x in guardrail_summaries],
        "evaluation jobs": [
            (x.get("jobName", "-"), x.get("jobArn", "-"))
            for x in (run_json("bedrock", "list-evaluation-jobs") or {}).get("jobSummaries", [])
        ],
    }
    # The project tag of each object whose ARN a listing gives. bedrock-agent answers a map,
    # bedrock a list of {key, value} (botocore 1.43.114).
    genai_tags = {}  # arn -> project tag value
    genai_tag_sets = {}  # arn -> every tag, None when unread
    tagged = [("bedrock-agent", arn) for kind in ("prompts", "flows") for _n, arn in genai[kind]]
    tagged += [("bedrock", arn) for _n, arn in genai["guardrails"]]
    tagged += [("bedrock-agent", kb.get("knowledgeBaseArn", "")) for kb in kbs]
    for service, arn in tagged:
        if not arn.startswith("arn:"):
            continue
        got = run_json(service, "list-tags-for-resource", "--resource-arn", arn)
        if got is None:
            genai_tags[arn] = UNREAD
            genai_tag_sets[arn] = None
            continue
        tags = got.get("tags") or {}
        if isinstance(tags, list):
            tags = {t.get("key"): t.get("value") for t in tags}
        genai_tags[arn] = tags.get(PROJECT_TAG, "")
        genai_tag_sets[arn] = tags
    availability = (
        run_json("bedrock", "get-foundation-model-availability", "--model-id", EMBEDDINGS_MODEL)
        or {}
    )
    scp_models, scp_app_profiles, scp_why = bedrockscope.scp_admitted(
        ctx.repo_root / bedrockscope.SCP_PATH
    )

    # ------------------------------------------------------------------ app-ml in app-ml-dev
    ml_dev = by_project.get(APP_ML_DEV)
    app_ml_jobs = []  # (kind, job), the newest first within a kind
    if ml_dev:
        for kind, prefix, _workflows in APP_ML_JOBS:
            for j in named_jobs(kind, prefix):
                if kind == "transform":
                    out = (j.get("TransformOutput") or {}).get("S3OutputPath", "")
                    mine = (project_of_uri(out) or {}).get("project") == APP_ML_DEV or (
                        j.get("ModelName") == f"{APP_ML_MODEL_PREFIX}{APP_ML_DEV}"
                    )
                else:
                    mine = j.get("RoleArn") == ml_dev["arn"]
                if mine:
                    app_ml_jobs.append((kind, j))
    # The candidate: its objects by name under the prefix (None when unread), model.json's text
    # and document, and the archive's SHA-256 as read.
    ml_objects, ml_model_text, ml_model, ml_digest = None, None, None, None
    if ml_dev and ml_dev["bucket"]:
        base = f"{ml_dev['shared']}{APP_ML_CANDIDATE}"
        listed = s3_objects(ml_dev["bucket"], base)
        if listed is not None:
            ml_objects = {o["Key"][len(base) :]: o for o in listed}
        if ml_objects and "model.json" in ml_objects:
            ml_model_text = s3_text(ml_dev["bucket"], f"{base}model.json")
            try:
                ml_model = json.loads(ml_model_text) if ml_model_text is not None else None
            except json.JSONDecodeError:
                ml_model = None
            if not isinstance(ml_model, dict):
                ml_model = None
        if ml_model and "model.tar.gz" in ml_objects:
            ml_digest = s3_sha256(ml_dev["bucket"], f"{base}model.tar.gz")
    ml_hash = str((ml_model or {}).get("sha256") or "")
    ml_group, ml_group_tags, ml_versions = None, {}, []
    if APP_ML_GROUP in all_groups:
        ml_group = run_json(
            "sagemaker",
            "describe-model-package-group",
            "--model-package-group-name",
            APP_ML_GROUP,
            tolerate=ABSENT,
        )
    if ml_group:
        ml_group_tags = tags_of(ml_group.get("ModelPackageGroupArn", ""))
        ml_versions = (
            run_json(
                "sagemaker",
                "list-model-packages",
                "--model-package-group-name",
                APP_ML_GROUP,
                "--sort-by",
                "CreationTime",
                "--sort-order",
                "Descending",
            )
            or {}
        ).get("ModelPackageSummaryList", [])
    ml_carrying = []  # each version whose description carries the candidate's hash, described
    if ml_hash:
        for v in ml_versions:
            if f"{APP_ML_HASH_MARK}{ml_hash}" in (v.get("ModelPackageDescription") or ""):
                arn = v.get("ModelPackageArn", "")
                desc = run_json("sagemaker", "describe-model-package", "--model-package-name", arn)
                ml_carrying.append(desc or v)
    # The project's MLflow App, and the newest runs' evaluation artifacts in its store as
    # (key under the store, LastModified, the training job the evaluation names); None when unread.
    ml_apps = [
        a
        for a in apps
        if (project_of_uri(a.get("ArtifactStoreUri") or "") or {}).get("project") == APP_ML_DEV
        or a["_tags"].get(PROJECT_TAG) == APP_ML_DEV
    ]
    ml_runs = None
    store_uri = (ml_apps[0].get("ArtifactStoreUri") or "") if ml_apps else ""
    store = re.match(r"^s3://([^/]+)/(.*)$", store_uri)
    if store:
        store_bucket, store_prefix = store.group(1), store.group(2).rstrip("/") + "/"
        listed = s3_objects(store_bucket, store_prefix)
        if listed is not None:
            found = sorted(
                (o for o in listed if o.get("Key", "").endswith(MLFLOW_EVALUATION_SUFFIX)),
                key=lambda o: str(o.get("LastModified", "")),
                reverse=True,
            )
            ml_runs = []
            for o in found[:MLFLOW_RUNS_READ]:
                text = s3_text(store_bucket, o["Key"])
                try:
                    evaluation = json.loads(text) if text else {}
                    job = (evaluation.get("awsds") or {}).get("training_job")
                except (json.JSONDecodeError, AttributeError):
                    job = None
                ml_runs.append((o["Key"][len(store_prefix) :], o.get("LastModified", "-"), job))

    # ------------------------------------------------------------------ app-genai in app-genai-dev
    genai_dev = by_project.get(APP_GENAI_DEV)
    gr_name = f"{GENAI_GUARDRAIL_PREFIX}{APP_GENAI_DEV}"
    gr_found = [g for g in guardrail_summaries if g.get("name") == gr_name]
    # With an identifier, ListGuardrails lists that guardrail's versions, the DRAFT among them.
    gr_versions, gr_newest, gr_newest_got = [], None, None
    if len(gr_found) == 1:
        gid = gr_found[0].get("id", "")
        gr_versions = (
            run_json("bedrock", "list-guardrails", "--guardrail-identifier", gid) or {}
        ).get("guardrails", [])
        numbered = [v for v in gr_versions if str(v.get("version", "")).isdigit()]
        if numbered:
            gr_newest = max(numbered, key=lambda v: int(v["version"]))
            gr_newest_got = run_json(
                "bedrock",
                "get-guardrail",
                "--guardrail-identifier",
                gid,
                "--guardrail-version",
                str(gr_newest["version"]),
            )
    try:
        definition = json.loads((ctx.repo_root / GENAI_DEFINITION).read_text(encoding="utf-8"))
        checkout_hash = definition_hash(definition)
    except (OSError, json.JSONDecodeError):
        checkout_hash = None
    genai_profiles = []  # the application inference profiles tagged with the project
    for prof in (
        run_json("bedrock", "list-inference-profiles", "--type-equals", "APPLICATION") or {}
    ).get("inferenceProfileSummaries", []):
        got = run_json(
            "bedrock",
            "list-tags-for-resource",
            "--resource-arn",
            prof.get("inferenceProfileArn", ""),
        )
        tags = {t.get("key"): t.get("value") for t in (got or {}).get("tags") or []}
        if tags.get(PROJECT_TAG) == APP_GENAI_DEV:
            genai_profiles.append(prof)
    genai_reports = None  # report name -> (LastModified, text or None); None when unread
    if genai_dev and genai_dev["bucket"]:
        base = f"{genai_dev['shared']}{GENAI_OUTBOX}"
        listed = s3_objects(genai_dev["bucket"], base)
        if listed is not None:
            names = {name for name, _workflow in GENAI_REPORTS}
            genai_reports = {
                o["Key"][len(base) :]: (
                    o.get("LastModified", "-"),
                    s3_text(genai_dev["bucket"], o["Key"]),
                )
                for o in listed
                if o["Key"][len(base) :] in names
            }
    # sandbox/bedrock's policy on the role: (ARN, version, its CreateDate, whether it carries the
    # deny, None when its document went unread); None when the role does not carry it.
    genai_policy = None
    if genai_dev:
        pol = next((a for a in genai_dev["attached"] if a.get("PolicyName") == GENAI_POLICY), None)
        if pol:
            arn = pol.get("PolicyArn", "")
            version, doc = policies.get(arn, ("-", None))
            deny = None if doc is None else GENAI_DENY_SID in statements_by_sid(doc)
            genai_policy = (arn, version, policy_dates.get(arn), deny)
    enforced = run_json("bedrock", "list-enforced-guardrails-configuration")
    enforced_configs = None if enforced is None else enforced.get("guardrailsConfig") or []

    # ------------------------------------------------------------------ network objects
    private = {}  # subnet id -> (name, AZ id)
    got = (
        run_json(
            "ec2", "describe-subnets", "--filters", f"Name=tag:Name,Values={PRIVATE_SUBNET_PREFIX}*"
        )
        or {}
    )
    for s in got.get("Subnets", []):
        name = next((t["Value"] for t in s.get("Tags", []) if t["Key"] == "Name"), "-")
        private[s["SubnetId"]] = (name, s.get("AvailabilityZoneId", "-"))
    sg_ids = set()
    for j in jobs:
        sg_ids.update((j.get("VpcConfig") or {}).get("SecurityGroupIds", []))
    for m in models:
        sg_ids.update((m.get("VpcConfig") or {}).get("SecurityGroupIds", []))
    for kind, j in app_ml_jobs:
        sg_ids.update((job_view(kind, j)["vpc"] or {}).get("SecurityGroupIds", []))
    sg_project = {}
    if sg_ids:
        got = run_json("ec2", "describe-security-groups", "--group-ids", *sorted(sg_ids)) or {}
        for g in got.get("SecurityGroups", []):
            tags = {t["Key"]: t["Value"] for t in g.get("Tags", [])}
            sg_project[g["GroupId"]] = tags.get(PROJECT_TAG, "")

    interface = (
        run_json(
            "ec2",
            "describe-vpc-endpoints",
            "--filters",
            "Name=vpc-endpoint-type,Values=Interface",
        )
        or {}
    ).get("VpcEndpoints", [])
    interface = [e for e in interface if e.get("State") not in ("deleted", "deleting")]
    by_service = {}
    for e in interface:
        by_service.setdefault(short_service(e.get("ServiceName", "")), []).append(e)
    gateway = (
        (
            run_json(
                "ec2",
                "describe-vpc-endpoints",
                "--filters",
                f"Name=tag:Name,Values={S3_GATEWAY_NAME}",
            )
            or {}
        ).get("VpcEndpoints")
        or [None]
    )[0]
    lists = (run_json("route53resolver", "list-firewall-domain-lists") or {}).get(
        "FirewallDomainLists", []
    )
    dns = next((x for x in lists if x.get("Name") == DNS_LIST), None)
    dns_entries = []
    if dns:
        dns_entries = (
            run_json(
                "route53resolver",
                "list-firewall-domains",
                "--firewall-domain-list-id",
                dns.get("Id", ""),
            )
            or {}
        ).get("Domains", [])

    # ------------------------------------------------------------------ metrics
    start, end = now - timedelta(days=METRIC_DAYS), now

    def metric_sum(namespace: str, metric: str, dimensions: list) -> float | None:
        got = (
            run_json(
                "cloudwatch",
                "get-metric-statistics",
                "--namespace",
                namespace,
                "--metric-name",
                metric,
                "--dimensions",
                json.dumps(dimensions),
                "--statistics",
                "Sum",
                "--period",
                "86400",
                "--start-time",
                utc_iso(start),
                "--end-time",
                utc_iso(end),
            )
            or {}
        )
        points = got.get("Datapoints", [])
        return sum(p.get("Sum", 0.0) for p in points) if points else None

    invocations = []  # (endpoint, variant, sum)
    for m in (
        run_json(
            "cloudwatch",
            "list-metrics",
            "--namespace",
            "AWS/SageMaker",
            "--metric-name",
            "Invocations",
        )
        or {}
    ).get("Metrics", []):
        dims = m.get("Dimensions", [])
        named = {d["Name"]: d["Value"] for d in dims}
        if set(named) == {"EndpointName", "VariantName"}:
            invocations.append(
                (
                    named["EndpointName"],
                    named["VariantName"],
                    metric_sum("AWS/SageMaker", "Invocations", dims),
                )
            )
    endpoint_bytes = []  # (service, endpoint id, subnet or '-', sum)
    for m in (
        run_json(
            "cloudwatch",
            "list-metrics",
            "--namespace",
            "AWS/PrivateLinkEndpoints",
            "--metric-name",
            "BytesProcessed",
        )
        or {}
    ).get("Metrics", []):
        dims = m.get("Dimensions", [])
        named = {d["Name"]: d["Value"] for d in dims}
        if named.get("Service Name") not in (RUNTIME_SERVICE, MLFLOW_SERVICE):
            continue
        endpoint_bytes.append(
            (
                short_service(named.get("Service Name", "")),
                named.get("VPC Endpoint Id", "-"),
                named.get("Subnet Id", "-"),
                metric_sum("AWS/PrivateLinkEndpoints", "BytesProcessed", dims),
            )
        )

    # ------------------------------------------------------------------ CloudTrail
    def lookup(event_name: str) -> list:
        got = (
            run_json(
                "cloudtrail",
                "lookup-events",
                "--lookup-attributes",
                f"AttributeKey=EventName,AttributeValue={event_name}",
                "--max-results",
                str(LOOKUP_MAX),
            )
            or {}
        )
        out = []
        for e in got.get("Events", []):
            try:
                out.append(json.loads(e.get("CloudTrailEvent", "{}")))
            except json.JSONDecodeError:
                continue
        return out

    def caller_of(ev: dict) -> tuple:
        """(role name, session name) of an assumed-role caller, else (arn, '-')."""
        identity = ev.get("userIdentity") or {}
        arn = identity.get("arn", "") or identity.get("invokedBy", "")
        m = re.match(r"^arn:aws:sts::\d{12}:assumed-role/([^/]+)/(.+)$", arn)
        return (m.group(1), m.group(2)) if m else (arn or "-", "-")

    def subject_of(ev: dict) -> str:
        rp = ev.get("requestParameters") or {}
        if not isinstance(rp, dict):
            return "-"
        return next((str(rp[k]) for k in SUBJECT_KEYS if rp.get(k)), "-")

    events = {name: lookup(name) for name in SAGEMAKER_EVENTS + BEDROCK_EVENTS}
    events[PULL_EVENT] = [
        ev
        for ev in lookup(PULL_EVENT)
        if (ev.get("requestParameters") or {}).get("repositoryName") == XGBOOST_REPOSITORY
    ]

    # ================================================================== checks
    # ML-1: the project roles, the managed policy, the boundary, the Tooling stack.
    if not projects:
        checks.fail(
            "ML-1",
            f"{PROJECT_ROLE_PREFIX}*",
            "no project role read in this account - the stage has no project to run in.",
        )
    for p in projects.values():
        who = p["project"] or p["role"]
        value = p["tags"].get(ML_TAG)
        if value == "true":
            checks.ok("ML-1", f"{who}: {ML_TAG}", "true")
        else:
            checks.fail(
                "ML-1",
                f"{who}: {ML_TAG}",
                f"{value or 'absent'} - every sagemaker:Create* of {ML_POLICY} needs 'true'; "
                "the stage stops at step 0.1 and takes decision 9.",
            )
        ml = next((a for a in p["attached"] if a.get("PolicyName") == ML_POLICY), None)
        if ml is None:
            checks.fail(
                "ML-1",
                f"{who}: {ML_POLICY}",
                "not attached - the project role holds none of the AI/ML menu's creates.",
            )
        else:
            version, doc = policies.get(ml.get("PolicyArn", ""), ("-", None))
            sids = statements_by_sid(doc)
            create = sids.get(SID_CREATE)
            detail = f"default version {version}"
            if create is None:
                detail += f"; no {SID_CREATE}"
            elif f"aws:PrincipalTag/{ML_TAG}" not in condition_keys(create):
                detail += f"; {SID_CREATE} no longer reads {ML_TAG}"
            if SID_MLFLOW not in sids:
                detail += f"; no {SID_MLFLOW}"
            if version == ML_POLICY_VERSION and create is not None and SID_MLFLOW in sids:
                checks.ok("ML-1", f"{who}: {ML_POLICY}", detail)
            else:
                checks.note(
                    "ML-1",
                    f"{who}: {ML_POLICY}",
                    f"{detail} - read 2026-10-17 as {ML_POLICY_VERSION}; re-read its create, "
                    "tag and MLflow statements before pass 1.",
                )
            tag_st = sids.get(SID_TAG)
            admitted = tag_key_admitted(tag_st, PROJECT_TAG) if tag_st else None
            if tag_st is None:
                checks.note("ML-1", f"{who}: {SID_TAG}", f"absent from {ML_POLICY} {version}.")
            elif admitted is False:
                checks.note(
                    "ML-1",
                    f"{who}: {SID_TAG}",
                    f"AddTags refuses {PROJECT_TAG}, as read 2026-10-12: a create that carries "
                    "it meets 6i's gap, step 2.2 (b), decision 7.",
                )
            elif admitted is True:
                checks.note(
                    "ML-1",
                    f"{who}: {SID_TAG}",
                    f"AddTags now admits {PROJECT_TAG} - the gap 6i measured may be gone; "
                    "step 2.2 (b) reads it.",
                )
            else:
                checks.note(
                    "ML-1",
                    f"{who}: {SID_TAG}",
                    "an aws:TagKeys operator this script does not read - see section 2.",
                )
        # The AddTags grants the role already holds outside AWS's policies (decision 7's baseline).
        grants = []
        for a in p["attached"]:
            arn = a.get("PolicyArn", "")
            if arn.startswith("arn:aws:iam::aws:"):
                continue
            for st in as_list((policies.get(arn, ("-", None))[1] or {}).get("Statement")):
                if st.get("Effect") == "Allow" and actions_include(st, "sagemaker:AddTags"):
                    grants.append(f"{a.get('PolicyName')}: {', '.join(resource_types(st))}")
        checks.note(
            "ML-1",
            f"{who}: AddTags of {PROJECT_TAG} granted outside AWS's policies",
            "; ".join(grants) if grants else "none",
        )
        # The boundary: its five statements and its ceiling against the exercise's types.
        if not p["boundary"]:
            checks.fail(
                "ML-1",
                f"{who}: D13 boundary",
                "none - the stage's negatives would have nothing to refuse them (US-8).",
            )
            continue
        _bversion, bdoc = policies.get(p["boundary"], ("-", None))
        missing = [s for s in BOUNDARY_SIDS if s not in statements_by_sid(bdoc)]
        ceiling = ceiling_types(bdoc) if bdoc else None
        problems = []
        if bdoc is None:
            problems.append(f"{p['boundary']} unreadable")
        if missing:
            problems.append(f"missing {', '.join(missing)}")
        if bdoc is not None and ceiling is None:
            problems.append(f"{SID_CEILING} names no sagemaker:InstanceTypes list")
        if ceiling is not None:
            outside = [f"{t} ({use})" for use, t in EXERCISE_TYPES if t not in ceiling]
            if outside:
                problems.append(f"outside the ceiling: {', '.join(outside)}")
            if CEILING_NEGATIVE in ceiling:
                problems.append(
                    f"{CEILING_NEGATIVE} is inside the ceiling, so step 2.3's fifth negative "
                    "would be admitted and bill"
                )
        if problems:
            checks.fail("ML-1", f"{who}: D13 boundary", "; ".join(problems) + ".")
        else:
            checks.ok(
                "ML-1",
                f"{who}: D13 boundary",
                f"{p['boundary'].rsplit('/', 1)[-1]}: the five statements; the exercise's "
                f"types inside the ceiling, {CEILING_NEGATIVE} outside it",
            )
    for role, (name, status, value, _keys) in stacks.items():
        what = f"{projects[role]['project'] or role}: {name} {ISOLATION_PARAMETER}"
        if status == "absent":
            checks.note("ML-1", what, "no such stack - read the parameter from the portal (0.8).")
        elif value is None:
            checks.note(
                "ML-1", what, f"{status}; the stack carries no such parameter - see section 2."
            )
        else:
            checks.note(
                "ML-1",
                what,
                f"{value} ({status}) - whether the portal's own creates ask for isolation.",
            )

    # ML-2: the MLflow Apps.
    if not apps:
        checks.note("ML-2", "MLflow Apps", "none - not built yet (pass 1, steps 1.5 to 1.7).")
    for app in apps:
        name = app.get("Name", app.get("Arn", "-"))
        status = app.get("Status", "-")
        store = app.get("ArtifactStoreUri", "") or ""
        p = project_of_uri(store)
        role = (app.get("RoleArn") or "-").rsplit("/", 1)[-1]
        detail = (
            f"{status}; MLflow {app.get('MlflowVersion', '-')}; role {role}; registration "
            f"{app.get('ModelRegistrationMode', '-')}; account default "
            f"{app.get('AccountDefaultStatus', '-')}; maintenance "
            f"{app.get('WeeklyMaintenanceWindowStart', '-')}; tag "
            f"{app['_tags'].get(PROJECT_TAG, 'none')}"
        )
        if p is None:
            checks.fail(
                "ML-2",
                name,
                f"artifact store {store or '-'} lies under no project's prefix ({detail}).",
            )
            continue
        if status.endswith("Failed"):
            checks.fail("ML-2", name, f"{detail} - read CreateMlflowApp's errorMessage.")
        elif status not in ("Created", "Updated"):
            checks.note("ML-2", name, f"{detail} - read again when it settles.")
        elif not is_project_key(app.get("KmsKeyId"), p):
            checks.note(
                "ML-2",
                name,
                f"{detail}; key {app.get('KmsKeyId') or 'none'} is not the project key "
                "(verification iv).",
            )
        else:
            under = f"shared/{DEMO_DIR}mlflow/" in store
            checks.ok(
                "ML-2",
                name,
                f"{detail}; store under {p['project']}'s prefix"
                + (f" at shared/{DEMO_DIR}mlflow/" if under else "")
                + ", the project key",
            )
    for ev in events["CreateMlflowApp"]:
        role, session = caller_of(ev)
        checks.note(
            "ML-2",
            f"CreateMlflowApp {subject_of(ev)} at {ev.get('eventTime', '-')}",
            f"{role}/{session}, {ev.get('vpcEndpointId') or 'no vpcEndpointId'}"
            + (
                f"; {ev.get('errorCode')}: {head2(ev.get('errorMessage') or '-')}"
                if ev.get("errorCode")
                else ""
            )
            + " (verification ii).",
        )

    # ML-3: each training job against the four settings, the ceiling, the key, the tag, the image.
    # A setting outside the boundary fails on any job; a failed outcome on the newest job only,
    # since a training job cannot be deleted and an earlier failure stays listed.
    ceiling = None
    for p in projects.values():
        ceiling = ceiling or ceiling_types(policies.get(p["boundary"], ("-", None))[1] or {})
    if not jobs:
        checks.note("ML-3", "training jobs", "none - not built yet (pass 2).")
    for j in jobs:
        jname = j.get("TrainingJobName", "-")
        vpc = j.get("VpcConfig") or {}
        res = j.get("ResourceConfig") or {}
        p = by_arn.get(j.get("RoleArn", ""))
        problems = []
        if not vpc.get("Subnets"):
            problems.append("no VpcConfig")
        else:
            bad = [s for s in vpc["Subnets"] if s not in private]
            if bad:
                problems.append(f"subnets outside the private tier: {', '.join(bad)}")
        if j.get("EnableNetworkIsolation") is not True:
            problems.append("network isolation off")
        if j.get("EnableInterContainerTrafficEncryption") is not True:
            problems.append("inter-container encryption off")
        itype = res.get("InstanceType", "-")
        if ceiling is not None and itype not in ceiling:
            problems.append(f"{itype} outside the ceiling")
        notes = []
        if p is None:
            problems.append(f"role {j.get('RoleArn', '-')} is no project role")
        else:
            if not res.get("VolumeKmsKeyId"):
                problems.append("no volume key")
            elif not is_project_key(res.get("VolumeKmsKeyId"), p):
                problems.append(f"volume key {res['VolumeKmsKeyId']} not the project's")
            out_key = (j.get("OutputDataConfig") or {}).get("KmsKeyId")
            if not out_key:
                notes.append("no output key: the model lands under the bucket's default (ML-4)")
            elif not is_project_key(out_key, p):
                problems.append(f"output key {out_key} not the project's")
            if j["_tags"].get(PROJECT_TAG) != p["project"]:
                problems.append(f"no {PROJECT_TAG} tag naming the project")
            if any(sg_project.get(g) != p["project"] for g in vpc.get("SecurityGroupIds", [])):
                problems.append("a security group not tagged with the project")
        uri = (j.get("AlgorithmSpecification") or {}).get("TrainingImage", "")
        repo = uri.split("/", 1)[1].split("@")[0].split(":")[0] if "/" in uri else uri
        if repo != XGBOOST_REPOSITORY and not (image_digest and image_digest in uri):
            notes.append(f"image repository {repo or '-'}, neither XGBoost's nor the house image")
        status = j.get("TrainingJobStatus", "-")
        auc = next(
            (
                m.get("Value")
                for m in j.get("FinalMetricDataList", [])
                if m.get("MetricName") == "validation:auc"
            ),
            None,
        )
        summary = f"{status}, {itype}, {j.get('BillableTimeInSeconds', '-')} s billed" + (
            f", validation AUC {auc:.4f}" if isinstance(auc, (int, float)) else ""
        )
        failure = None
        if status == "Failed":
            failure = f"Failed: {j.get('FailureReason') or '-'}"
            if j is jobs[0]:
                problems.append(failure)
        tail = f" ({summary})" + (f"; {'; '.join(notes)}" if notes else "")
        if problems:
            checks.fail("ML-3", jname, "; ".join(problems) + tail + ".")
        elif failure or status in RUNNING or status == "Stopped" or notes:
            checks.note("ML-3", jname, (failure or summary) + tail)
        else:
            checks.ok("ML-3", jname, f"{summary}; the four settings, project role, key and tag")
    for ev in events["CreateTrainingJob"]:
        role, session = caller_of(ev)
        vpce = ev.get("vpcEndpointId") or ""
        what = f"CreateTrainingJob {subject_of(ev)} at {ev.get('eventTime', '-')}"
        if ev.get("errorCode"):
            checks.note(
                "ML-3",
                what,
                f"refused, {role}/{session}: {ev['errorCode']}: "
                f"{head2(ev.get('errorMessage') or '-')}",
            )
        elif not role.startswith(PROJECT_ROLE_PREFIX):
            checks.fail("ML-3", what, f"admitted, called by {role}/{session} - no project role.")
        elif vpce:
            checks.ok(
                "ML-3",
                what,
                f"{role}/{session} through {vpce} from {ev.get('sourceIPAddress', '-')}",
            )
        else:
            checks.note(
                "ML-3",
                what,
                f"{role}/{session}, no vpcEndpointId - from {ev.get('sourceIPAddress', '-')}.",
            )

    for ev in events[PULL_EVENT]:
        role, session = caller_of(ev)
        checks.note(
            "ML-3",
            f"{PULL_EVENT} {XGBOOST_REPOSITORY} at {ev.get('eventTime', '-')}",
            f"{role}/{session}, {ev.get('vpcEndpointId') or 'no vpcEndpointId'}"
            + (f"; {ev['errorCode']}" if ev.get("errorCode") else ""),
        )
    if jobs and not events[PULL_EVENT]:
        checks.note(
            "ML-3",
            f"{PULL_EVENT} {XGBOOST_REPOSITORY}",
            f"none among the latest {LOOKUP_MAX} {PULL_EVENT} events of this account.",
        )

    # ML-4: the registry.
    others = [g for g in all_groups if g != MODEL_GROUP]
    if group is None:
        checks.note("ML-4", MODEL_GROUP, "absent - not built yet (pass 3, step 3.2).")
    else:
        tag = group_tags.get(PROJECT_TAG)
        statuses = ", ".join(
            f"v{pkg.get('ModelPackageVersion', '?')} {pkg.get('ModelApprovalStatus', '-')}"
            for pkg in packages
        )
        if tag in by_project:
            checks.ok(
                "ML-4", MODEL_GROUP, f"tagged {tag}; {len(packages)} version(s): {statuses or '-'}"
            )
        else:
            checks.note(
                "ML-4",
                MODEL_GROUP,
                f"tag {tag or 'none'}; {len(packages)} version(s): {statuses or '-'}",
            )
    for url, kms in model_data.items():
        p = project_of_uri(url)
        if kms == UNREAD:
            checks.note("ML-4", url, "head-object failed - see section 15.")
        elif p is None:
            checks.note("ML-4", url, f"{kms} - under no project's prefix.")
        elif is_project_key(kms, p):
            checks.ok("ML-4", url, "the model data under the project key")
        elif kms in ("-", "AES256"):
            checks.note("ML-4", url, f"{kms} - no project key on the model data.")
        else:
            checks.fail("ML-4", url, f"{kms} - a key other than the project's.")
    if others:
        checks.note("ML-4", "other model package groups", ", ".join(sorted(others)))

    # ML-5: serving. 4.1's endpoint stays between sittings and its member deletes it (decision 6),
    # so each endpoint is a note with its status, its age and its price: no slice, make down or
    # make status reaches one.
    for e in endpoints:
        checks.note("ML-5", e.get("EndpointName", "-"), endpoint_summary(e, now))
    if not endpoints:
        checks.ok("ML-5", "endpoints", "none")
    if endpoint_configs:
        checks.note(
            "ML-5",
            "endpoint configurations",
            ", ".join(c.get("EndpointConfigName", "-") for c in endpoint_configs),
        )
    for m in models:
        vpc = m.get("VpcConfig") or {}
        checks.note(
            "ML-5",
            f"model {m.get('ModelName', '-')}",
            f"{'VpcConfig' if vpc.get('Subnets') else 'no VpcConfig'}, isolation "
            f"{m.get('EnableNetworkIsolation', '-')}, role "
            f"{(m.get('ExecutionRoleArn') or '-').rsplit('/', 1)[-1]}",
        )
    if not transforms:
        checks.note("ML-5", "transform jobs", "none - not built yet (pass 4, step 4.3).")
    for t in transforms:
        tname = t.get("TransformJobName", "-")
        res = t.get("TransformResources") or {}
        out = t.get("TransformOutput") or {}
        p = project_of_uri(out.get("S3OutputPath", ""))
        problems = []
        itype = res.get("InstanceType", "-")
        if ceiling is not None and itype not in ceiling:
            problems.append(f"{itype} outside the ceiling")
        if p is None:
            problems.append(f"output {out.get('S3OutputPath', '-')} under no project's prefix")
        else:
            if not res.get("VolumeKmsKeyId"):
                problems.append("no volume key")
            elif not is_project_key(res.get("VolumeKmsKeyId"), p):
                problems.append(f"volume key {res['VolumeKmsKeyId']} not the project's")
            if t["_tags"].get(PROJECT_TAG) != p["project"]:
                problems.append(f"no {PROJECT_TAG} tag naming the project")
        status = t.get("TransformJobStatus", "-")
        summary = f"{status}, {itype}, output key {out.get('KmsKeyId') or 'none'}"
        if status == "Failed" and t is transforms[0]:
            problems.append(f"Failed: {t.get('FailureReason') or '-'}")
        if problems:
            checks.fail("ML-5", tname, "; ".join(problems) + f" ({summary}).")
        elif status in RUNNING or status in ("Failed", "Stopped"):
            checks.note("ML-5", tname, f"{summary} {t.get('FailureReason') or ''}".strip())
        else:
            checks.ok("ML-5", tname, f"{summary}; the project's key, prefix and tag")
    for endpoint, variant, total in invocations:
        checks.note(
            "ML-5",
            f"Invocations {endpoint}/{variant}",
            f"{total:.0f} over {METRIC_DAYS} days" if total is not None else "no data point",
        )
    runtime_bytes = [row for row in endpoint_bytes if row[0] == "sagemaker.runtime"]
    for service, vpce, subnet, total in runtime_bytes:
        checks.note(
            "ML-5",
            f"BytesProcessed {service} {vpce}" + ("" if subnet == "-" else f" in {subnet}"),
            f"{total:.0f} bytes over {METRIC_DAYS} days" if total is not None else "no data point",
        )

    # ML-6: the pipelines.
    if not pipelines:
        checks.note("ML-6", "ML pipelines", "none - not built yet (pass 5).")
    source_steps = sorted((s.get("Name", ""), s.get("Type", "")) for s in all_steps(source or {}))
    for pl in pipelines:
        desc, definition = pl["desc"], pl["definition"]
        p = by_arn.get(desc.get("RoleArn", ""))
        problems, parameterized = [], []
        if p is None:
            problems.append(f"RoleArn {desc.get('RoleArn', '-')} is no project role")
        live = all_steps(definition)
        for step in live:
            itype, step_problems, step_params = step_settings(step)
            label = step.get("Name", "?")
            problems.extend(f"{label}: {x}" for x in step_problems)
            parameterized.extend(f"{label}.{x}" for x in step_params)
            if itype and ceiling is not None and itype not in ceiling:
                problems.append(f"{label}: {itype} outside the ceiling")
        latest = pl["executions"][0] if pl["executions"] else {}
        state = latest.get("PipelineExecutionStatus", "no execution")
        # A Fail step is the definition's own verdict on the model (the condition on
        # validation:auc), reported like the AUC and never checked; any other failed step is.
        verdicts, broken = [], []
        for s in pl["steps"]:
            if s.get("StepStatus") != "Failed":
                continue
            fail = (s.get("Metadata") or {}).get("Fail")
            if fail is not None:
                verdicts.append(f"{s.get('StepName', '?')}: {fail.get('ErrorMessage') or '-'}")
            else:
                broken.append(f"{s.get('StepName', '?')}: {s.get('FailureReason') or '-'}")
        if state in ("Failed", "CompletedWithFailures") and (broken or not verdicts):
            reason = "; ".join(broken) or latest.get("PipelineExecutionFailureReason") or "-"
            problems.append(f"latest execution {state}: {reason}")
        live_steps = sorted((s.get("Name", ""), s.get("Type", "")) for s in live)
        if source is None:
            same = f"{PIPELINE_SOURCE} unreadable"
        elif live_steps == source_steps:
            same = "steps as in the committed source"
        else:
            same = "steps differ from the committed source"
        detail = (
            f"{state}; {len(live_steps)} step(s), {same}"
            + (f"; the Fail step ran: {'; '.join(verdicts)}" if verdicts else "")
            + (f"; parameterized: {', '.join(parameterized)}" if parameterized else "")
            + f"; saved under aws/output/{DEFS_DIR}/"
        )
        if problems:
            checks.fail("ML-6", pl["name"], "; ".join(problems) + f" ({detail}).")
        elif state != "Succeeded" or source is None or live_steps != source_steps:
            checks.note("ML-6", pl["name"], detail)
        else:
            checks.ok("ML-6", pl["name"], f"project role; the four settings; {detail}")

    # ML-7: HyperPod and Partner AI apps are read, never created; the quotas bound the exercise.
    if clusters:
        for c in clusters:
            checks.fail(
                "ML-7",
                f"HyperPod cluster {c.get('ClusterName', '-')}",
                f"{c.get('ClusterStatus', '-')} - the stage creates none (step 6.1).",
            )
    else:
        checks.ok("ML-7", "HyperPod clusters", "none")
    if partner_apps:
        for a in partner_apps:
            checks.fail(
                "ML-7",
                f"Partner AI app {a.get('Name', '-')}",
                f"{a.get('Type', '-')} {a.get('Status', '-')} - the stage creates none (6.2).",
            )
    else:
        checks.ok("ML-7", "Partner AI apps", "none")
    for qname in QUOTAS:
        row = quota_rows.get(qname)
        if row is None:
            checks.note("ML-7", qname, "not listed by Service Quotas - read the console's page.")
        elif not row[0]:
            checks.fail(
                "ML-7",
                qname,
                f"{quota_text(row[0])} ({row[1]}, {row[2]}) - a zero stops the stage; "
                f"{request_text(quota_requests, row[2])}. An increase is the user's to "
                f"request, at no less than AWS's default ({quota_text(quota_defaults.get(qname))}).",
            )
        else:
            checks.ok("ML-7", qname, f"{quota_text(row[0])} ({row[1]}, {row[2]})")
    checks.note(
        "ML-7",
        "MLflow quotas",
        "; ".join(
            f"{n} = {quota_text(quota_rows[n][0])} ({quota_rows[n][1]})" for n in mlflow_quotas
        )
        or "none published under sagemaker",
    )

    # ML-8: the Generative AI menu: the roles before, the objects after.
    for p in projects.values():
        checks.note(
            "ML-8",
            f"{p['project'] or p['role']}: Bedrock tags",
            ", ".join(f"{t} {p['tags'].get(t, 'absent')}" for t in BEDROCK_TAGS)
            + " (verification xvii).",
        )
    # A flow environment's own role is EXC-27 while its shape holds (awslib/flowrole.py).
    for br in bedrock_roles:
        what = f"role {br['name']}"
        if not br["boundary"]:
            problems = flowrole.shape_problems(
                br["name"], br["trust"], br["policies"], br["inline"], account
            )
            if br["name"].startswith(flowrole.NAME_PREFIX) and not problems:
                checks.note("ML-8", what, flowrole.NOTE)
                continue
            outside = (
                f"; outside {flowrole.EXCEPTION_ID}'s shape: {'; '.join(problems)}"
                if br["name"].startswith(flowrole.NAME_PREFIX)
                else ""
            )
            checks.fail(
                "ML-8",
                what,
                f"no permissions boundary - an interactive principal outside D13 (policies: "
                f"{', '.join(br['policies']) or 'none'}){outside}.",
            )
        else:
            checks.ok(
                "ML-8",
                what,
                f"boundary {br['boundary'].rsplit('/', 1)[-1]}; project "
                f"{br['project'] or '-'}; policies {', '.join(br['policies']) or 'none'}",
            )
    if not bedrock_roles:
        checks.note("ML-8", f"{BEDROCK_ROLE_PREFIX}* roles", "none in this account.")
    for f in functions:
        vpc = (f.get("VpcConfig") or {}).get("VpcId")
        checks.note(
            "ML-8",
            f"Lambda {f.get('FunctionName', '-')}",
            f"in {vpc}" if vpc else "no VPC: the internet a function has by default (decision 10).",
        )
    if not functions:
        checks.ok(
            "ML-8",
            "Lambda functions",
            "none" if not every_function else "none but Control Tower's own",
        )
    if not kbs:
        checks.note("ML-8", "knowledge bases", "none - not built yet (pass 7, step 7.4a).")
    for kb in kbs:
        config = kb.get("knowledgeBaseConfiguration") or {}
        vector = config.get("vectorKnowledgeBaseConfiguration") or {}
        model = (vector.get("embeddingModelArn") or "-").rsplit("/", 1)[-1]
        store = (kb.get("storageConfiguration") or {}).get("type", "-")
        tag = genai_tags.get(kb.get("knowledgeBaseArn", ""), "")
        detail = (
            f"{kb.get('status', '-')}; embeddings {model}; store {store}; role "
            f"{(kb.get('roleArn') or '-').rsplit('/', 1)[-1]}; tag {tag or 'none'}; sources "
            + (
                ", ".join(f"{s.get('name', '-')} {s.get('status', '-')}" for s in kb["_sources"])
                or "none"
            )
        )
        if store not in IDLE_FREE_STORES:
            checks.note(
                "ML-8",
                f"knowledge base {kb.get('name', '-')}",
                f"{detail} - read the store's idle bill before keeping it (decision 12).",
            )
        elif model != EMBEDDINGS_MODEL:
            checks.note(
                "ML-8", f"knowledge base {kb.get('name', '-')}", f"{detail} - not Titan V2."
            )
        else:
            checks.ok("ML-8", f"knowledge base {kb.get('name', '-')}", detail)
    for c in collections:
        checks.note(
            "ML-8",
            f"OpenSearch Serverless collection {c.get('name', '-')}",
            f"{c.get('status', '-')} - a classic collection holds at least one OCU, 5.76 USD a "
            "day while it exists (decision 12).",
        )
    if not collection_listing.complete:
        checks.note(
            "ML-8",
            "OpenSearch Serverless collections",
            f"{len(collections)} read; the listing was not read to its last page (section 15), "
            "and a collection not read is a bill this report does not show.",
        )
    checks.note(
        "ML-8",
        "S3 vector buckets",
        ", ".join(b.get("vectorBucketName", "-") for b in vector_buckets) or "none",
    )
    for kind, items in genai.items():
        if not items:
            checks.note("ML-8", kind, "none - not built yet (pass 7).")
            continue
        listed_items = []
        for item_name, arn in items:
            tag = genai_tags.get(arn)
            listed_items.append(item_name + ("" if tag is None else f" [tag {tag or 'none'}]"))
        checks.note("ML-8", kind, ", ".join(listed_items))
    if availability:
        # agreementAvailability is a structure with a status; the other three are strings.
        agreement = availability.get("agreementAvailability") or {}
        checks.note(
            "ML-8",
            f"{EMBEDDINGS_MODEL} availability",
            f"agreement {agreement.get('status', '-')}, authorization "
            f"{availability.get('authorizationStatus', '-')}, entitlement "
            f"{availability.get('entitlementAvailability', '-')}, region "
            f"{availability.get('regionAvailability', '-')}",
        )
    if scp_models is None:
        checks.note("ML-8", f"{bedrockscope.SID_MODELS} {EMBEDDINGS_MODEL}", scp_why)
    elif EMBEDDINGS_MODEL in scp_models:
        checks.note(
            "ML-8",
            f"{bedrockscope.SID_MODELS} {EMBEDDINGS_MODEL}",
            "admitted by the repository's SCP (decision 11), application inference profiles "
            f"{'admitted' if scp_app_profiles else 'NOT admitted'}; ./aws/org-policy-baseline.py "
            "prints the attached document.",
        )
    else:
        checks.note(
            "ML-8",
            f"{bedrockscope.SID_MODELS} {EMBEDDINGS_MODEL}",
            "not admitted by the repository's SCP - step 7.4a's first sync is expected refused "
            "until decision 11's amendment.",
        )
    for name in BEDROCK_EVENTS:
        for ev in events[name]:
            role, session = caller_of(ev)
            checks.note(
                "ML-8",
                f"{name} {subject_of(ev)} at {ev.get('eventTime', '-')}",
                f"{role}/{session}, {ev.get('vpcEndpointId') or 'no vpcEndpointId'}"
                + (f"; {ev['errorCode']}" if ev.get("errorCode") else "")
                + " (verification xviii).",
            )

    # ML-9: the doors a session opens, and the image's list.
    present = [s for s in ALWAYS_ON if s in by_service]
    if not present:
        checks.note(
            "ML-9",
            "the session's interface endpoints",
            "none - the session is down; raise it (make hub-up, then make up ENV=sandbox, "
            "with GROUPS=mlflow once step 1.4 adds the group) to read the doors.",
        )
    elif len(present) < len(ALWAYS_ON):
        missing = [s for s in ALWAYS_ON if s not in by_service]
        checks.fail(
            "ML-9",
            "the session's interface endpoints",
            f"up, but without {', '.join(missing)} - a job or a client call through them fails.",
        )
    else:
        checks.ok("ML-9", "the session's interface endpoints", ", ".join(ALWAYS_ON))
    mlflow = by_service.get("mlflow", [])
    if mlflow:
        e = mlflow[0]
        checks.ok(
            "ML-9",
            MLFLOW_SERVICE,
            f"{e.get('VpcEndpointId', '-')} {e.get('State', '-')}, private DNS "
            f"{e.get('PrivateDnsEnabled', '-')}",
        )
    else:
        checks.note("ML-9", MLFLOW_SERVICE, "no endpoint - step 1.4 adds the mlflow group.")
    if "experiments" in by_service:
        checks.note(
            "ML-9", EXPERIMENTS_SERVICE, "present - a tracking server's endpoint (decision 2)."
        )
    for service, vpce, subnet, total in endpoint_bytes:
        if service != "mlflow":
            continue
        checks.note(
            "ML-9",
            f"BytesProcessed mlflow {vpce}" + ("" if subnet == "-" else f" in {subnet}"),
            f"{total:.0f} bytes over {METRIC_DAYS} days" if total is not None else "no data point",
        )
    if gateway is None:
        checks.fail("ML-9", S3_GATEWAY_NAME, "absent - the [P] gateway endpoint is gone.")
    else:
        try:
            gdoc = json.loads(gateway.get("PolicyDocument") or "{}")
        except json.JSONDecodeError:
            gdoc = {}
        allowed = set(as_list((statements_by_sid(gdoc).get(GATEWAY_SID) or {}).get("Resource")))
        lacking = [
            b
            for b in GATEWAY_BUCKETS
            if not {f"arn:aws:s3:::{b}", f"arn:aws:s3:::{b}/*"} <= allowed
        ]
        if lacking:
            checks.fail(
                "ML-9",
                f"{S3_GATEWAY_NAME} {GATEWAY_SID}",
                f"lacks {', '.join(lacking)} - the SDK's and JumpStart's reads would hang.",
            )
        else:
            checks.ok(
                "ML-9",
                f"{S3_GATEWAY_NAME} {GATEWAY_SID}",
                f"names {', '.join(GATEWAY_BUCKETS)} (verification iii exercises them)",
            )
    if dns is None:
        checks.note("ML-9", DNS_LIST, "absent - the list is [E], raised with sandbox/egress.")
    elif not MLFLOW_NAMES:
        checks.note(
            "ML-9",
            DNS_LIST,
            f"{len(dns_entries)} entries; the MLflow data plane's names are not known yet "
            "(verification vi, step 1.6).",
        )
    else:
        unmatched = [n for n in MLFLOW_NAMES if covered(n, dns_entries) is None]
        if unmatched:
            checks.fail("ML-9", DNS_LIST, f"no entry resolves {', '.join(unmatched)}.")
        else:
            checks.ok("ML-9", DNS_LIST, f"covers {', '.join(MLFLOW_NAMES)}")
    devenv = ctx.out_dir / "devenv.txt"
    if devenv.is_file():
        stamp, result, detail = devenv_de5(devenv.read_text(encoding="utf-8"))
        checks.note(
            "ML-9",
            "DE-5, from aws/output/devenv.txt",
            f"{result or 'no DE-5 row'} at {stamp}: {detail or '-'} - red is expected once the "
            "mlflow group lands (decision 4).",
        )
    else:
        checks.note("ML-9", "DE-5", "aws/output/devenv.txt absent - run ./aws/devenv.py first.")

    # ML-10: app-ml in app-ml-dev (step 9.9): its jobs against the settings and the tag, the model
    # app-ml-score leaves, the candidate, the version app-ml-register proposed and the MLflow run
    # track logged. A failed outcome fails on the newest job of its task only, as in ML-3.
    leftovers = [m for m in models if m.get("ModelName", "").startswith(APP_ML_MODEL_PREFIX)]
    for m in leftovers:
        age = age_of(m.get("CreationTime"), now)
        what = f"model {m.get('ModelName', '-')}"
        if age is None:
            checks.note("ML-10", what, f"created {m.get('CreationTime', '-')}, of unread age.")
        elif age > MODEL_MAX_AGE:
            checks.fail(
                "ML-10",
                what,
                f"{hours_text(age)} old: a failed run's model no run has followed - the next "
                "app-ml-score run's resolve deletes it.",
            )
        else:
            checks.note(
                "ML-10",
                what,
                f"{hours_text(age)} old: a run in progress, or a failed one whose model the next "
                "run's resolve deletes.",
            )
    if not leftovers:
        checks.ok("ML-10", f"models {APP_ML_MODEL_PREFIX}*", "none")
    if ml_dev is None:
        checks.note(
            "ML-10",
            f"app-ml-dev {APP_ML_DEV}",
            f"no project role tagged {PROJECT_TAG} {APP_ML_DEV} - 9.6 runs the application there.",
        )
    else:
        newest = {}  # a job's task, its name without the timestamp -> the newest job's name
        for kind, j in app_ml_jobs:
            name = job_view(kind, j)["name"]
            newest.setdefault(name.rsplit("-", 1)[0], name)
        if not app_ml_jobs:
            checks.note(
                "ML-10", "app-ml jobs", "none - app-ml-train and app-ml-score create them (9.6)."
            )
        for kind, j in app_ml_jobs:
            v = job_view(kind, j)
            problems = []
            if kind != "transform":
                vpc = v["vpc"] or {}
                bad = [s for s in vpc.get("Subnets", []) if s not in private]
                if not vpc.get("Subnets"):
                    problems.append("no VpcConfig")
                elif bad:
                    problems.append(f"subnets outside the private tier: {', '.join(bad)}")
                if any(sg_project.get(g) != APP_ML_DEV for g in vpc.get("SecurityGroupIds", [])):
                    problems.append("a security group not tagged with the project")
                if v["isolation"] is not True:
                    problems.append("network isolation off")
                if v["ice"] is not True:
                    problems.append("inter-container encryption off")
            if ceiling is not None and v["itype"] not in ceiling:
                problems.append(f"{v['itype']} outside the ceiling")
            for which, key in (("volume", v["volume_key"]), ("output", v["output_key"])):
                if not key:
                    problems.append(f"no {which} key")
                elif not is_project_key(key, ml_dev):
                    problems.append(f"{which} key {last_segment(key)} not the project's")
            if j["_tags"].get(PROJECT_TAG) != APP_ML_DEV:
                problems.append(f"no {PROJECT_TAG} tag naming app-ml-dev")
            status = v["status"]
            summary = f"{kind}, {status}, {v['itype']}"
            failure = f"Failed: {flat(v['failure'] or '-')}" if status == "Failed" else None
            if failure and newest.get(v["name"].rsplit("-", 1)[0]) == v["name"]:
                problems.append(failure)
            if problems:
                checks.fail("ML-10", v["name"], "; ".join(problems) + f" ({summary}).")
            elif failure or status in RUNNING or status == "Stopped":
                checks.note("ML-10", v["name"], summary + (f"; {failure}" if failure else ""))
            elif kind == "transform":
                checks.ok(
                    "ML-10",
                    v["name"],
                    f"{summary}; the ceiling, the project key and tag (its network settings are "
                    "its model's)",
                )
            else:
                checks.ok(
                    "ML-10",
                    v["name"],
                    f"{summary}; the four settings, the ceiling, the project key and tag",
                )
        what = f"shared/{APP_ML_CANDIDATE}"
        if not ml_dev["bucket"]:
            checks.note("ML-10", what, "the role carries no DomainBucketName - nothing to list.")
        elif ml_objects is None:
            checks.note("ML-10", what, "the listing failed - see section 15.")
        elif "model.json" not in ml_objects:
            checks.note(
                "ML-10",
                what,
                f"no model.json (holds {', '.join(sorted(ml_objects)) or 'nothing'}) - "
                "app-ml-train's publish writes the candidate (9.6).",
            )
        elif ml_model_text is None:
            checks.note("ML-10", what, "model.json unread - see section 15.")
        elif ml_model is None:
            checks.fail(
                "ML-10", what, "model.json is no JSON object: register and resolve refuse it."
            )
        elif "model.tar.gz" not in ml_objects:
            checks.fail("ML-10", what, "model.json without model.tar.gz beside it.")
        elif ml_digest is None:
            checks.note("ML-10", what, "model.tar.gz unread - see section 15.")
        else:
            size = ml_objects["model.tar.gz"].get("Size")
            problems = []
            if ml_digest != ml_hash:
                problems.append(
                    f"the archive hashes to {short_hash(ml_digest)}, model.json names "
                    f"{short_hash(ml_hash)}"
                )
            if str(size) != str(ml_model.get("size_bytes")):
                problems.append(
                    f"the archive holds {size} bytes, model.json names "
                    f"{ml_model.get('size_bytes', '-')}"
                )
            detail = (
                f"sha256 {short_hash(ml_digest)}, {size} bytes, trained by "
                f"{ml_model.get('training_job', '-')}, AUC {ml_model.get('auc', '-')}, published "
                f"{ml_model.get('published', '-')}"
            )
            if problems:
                checks.fail("ML-10", what, "; ".join(problems) + f" ({detail}).")
            else:
                checks.ok("ML-10", what, f"the archive's hash is model.json's: {detail}")
    what = f"model package group {APP_ML_GROUP}"
    if APP_ML_GROUP not in all_groups:
        checks.note("ML-10", what, "absent - created once from the space at 9.6.")
    elif ml_group is None:
        checks.note("ML-10", what, "unread - see section 15.")
    else:
        tag = ml_group_tags.get(PROJECT_TAG)
        statuses = (
            ", ".join(
                f"v{v.get('ModelPackageVersion', '?')} {v.get('ModelApprovalStatus', '-')}"
                for v in ml_versions
            )
            or "no version"
        )
        if tag == APP_ML_DEV:
            checks.ok("ML-10", what, f"tagged app-ml-dev; {statuses}")
        else:
            checks.fail(
                "ML-10",
                what,
                f"tag {tag or 'none'} - 9.6 creates it with app-ml-dev's tag alone; {statuses}.",
            )
        what = "the version app-ml-register proposed"
        if not ml_hash:
            checks.note(
                "ML-10", what, "no candidate to read it against - 9.6's publish writes one."
            )
        elif not ml_carrying:
            checks.note(
                "ML-10",
                what,
                f"none carries sha256:{short_hash(ml_hash)} - app-ml-register proposes it (9.6).",
            )
        elif len(ml_carrying) > 1:
            checks.fail(
                "ML-10",
                what,
                f"{len(ml_carrying)} versions carry sha256:{short_hash(ml_hash)} ("
                + ", ".join(f"v{p.get('ModelPackageVersion', '?')}" for p in ml_carrying)
                + ") - register proposes one per archive.",
            )
        else:
            pkg = ml_carrying[0]
            meta = pkg.get("CustomerMetadataProperties") or {}
            urls = [
                c.get("ModelDataUrl", "")
                for c in (pkg.get("InferenceSpecification") or {}).get("Containers", [])
            ]
            problems = []
            if meta.get("sha256") != ml_hash:
                problems.append(f"its metadata names sha256 {short_hash(meta.get('sha256'))}")
            if meta.get("training_job") != ml_model.get("training_job"):
                problems.append(
                    f"its metadata names {meta.get('training_job') or 'no training job'}, "
                    f"model.json {ml_model.get('training_job', '-')}"
                )
            if ml_dev is not None:
                copy = (
                    f"s3://{ml_dev['bucket']}/{ml_dev['shared']}app-ml/models/sha256/"
                    f"{ml_hash}/model.tar.gz"
                )
                if urls != [copy]:
                    problems.append(
                        "its model data is not the copy under app-ml/models/sha256/: "
                        + (", ".join(u.split(ml_dev["prefix"], 1)[-1] for u in urls) or "none")
                    )
            status = pkg.get("ModelApprovalStatus", "-")
            by = principal_name(((pkg.get("CreatedBy") or {}).get("IamIdentity") or {}).get("Arn"))
            detail = (
                f"v{pkg.get('ModelPackageVersion', '?')} {status}, trained by "
                f"{meta.get('training_job', '-')}, validation AUC "
                f"{meta.get('validation_auc', '-')}, registered by {by}"
            )
            if problems:
                checks.fail("ML-10", what, "; ".join(problems) + f" ({detail}).")
            elif status not in DEV_VERSION_STATUSES:
                checks.note("ML-10", what, f"{detail} - no gate reads a dev version's status.")
            else:
                checks.ok("ML-10", what, f"{detail}; its metadata and model data the candidate's")
    if ml_dev is not None:
        what = "the MLflow run app-ml-train's track logged"
        job = (ml_model or {}).get("training_job")
        if not ml_apps:
            checks.note(
                "ML-10",
                what,
                "app-ml-dev has no MLflow App - the user's create-environment before day 3 "
                "creates it (9.6).",
            )
        elif ml_runs is None:
            checks.note(
                "ML-10",
                what,
                f"{ml_apps[0].get('Name', '-')}'s store unread: no s3:// store, or the listing "
                "failed (section 15).",
            )
        elif not ml_runs:
            checks.note(
                "ML-10",
                what,
                f"no key ending {MLFLOW_EVALUATION_SUFFIX} in {ml_apps[0].get('Name', '-')}'s "
                "store - track logs one per run (9.6); the layout is unmeasured.",
            )
        else:
            match = next((r for r in ml_runs if job and r[2] == job), None)
            if match:
                checks.ok(
                    "ML-10",
                    what,
                    f"run {match[0].split('/artifacts/', 1)[0]} at {match[1]} logged {job}'s "
                    "evaluation, the candidate's",
                )
            else:
                named = ", ".join(sorted({r[2] or "no training job" for r in ml_runs}))
                tail = f", not the candidate's {job}." if job else "; no candidate to read them by."
                checks.note("ML-10", what, f"the newest {len(ml_runs)} run(s) name {named}{tail}")

    # ML-11: app-genai in app-genai-dev (step 10.9): its guardrail and the hash its newest version
    # carries against the checkout's definition, its inference profile, its two reports, the deny
    # on its role and the account-level guardrail configuration.
    if genai_dev is None:
        checks.note(
            "ML-11",
            f"app-genai-dev {APP_GENAI_DEV}",
            f"no project role tagged {PROJECT_TAG} {APP_GENAI_DEV} - 10.4 runs the application "
            "there.",
        )
    gr = gr_found[0] if len(gr_found) == 1 else None
    gr_tags = genai_tag_sets.get(gr.get("arn", "")) if gr else None
    what = f"guardrail {gr_name}"
    if gr is None:
        checks.note("ML-11", what, "absent - app-genai-triage's guardrail task creates it (10.4).")
    else:
        status = gr.get("status", "-")
        tag = (gr_tags or {}).get(PROJECT_TAG)
        if gr_tags is None:
            checks.note("ML-11", what, f"{status}; its tags unread - see section 15.")
        elif tag != APP_GENAI_DEV:
            checks.fail(
                "ML-11",
                what,
                f"{status}; tag {tag or 'none'} - the role keeps a guardrail of its own project "
                "alone, by that tag.",
            )
        elif status == "FAILED":
            checks.fail("ML-11", what, "FAILED - read GetGuardrail's failureRecommendations.")
        elif status != "READY":
            checks.note("ML-11", what, f"{status} - read again when it settles.")
        else:
            checks.ok("ML-11", what, f"READY, id {gr.get('id', '-')}, tagged app-genai-dev")
        what = f"{gr_name}'s newest version"
        if gr_newest is None:
            checks.note(
                "ML-11", what, "no published version - the guardrail task publishes one (10.4)."
            )
        else:
            version = str(gr_newest["version"])
            carried = (gr_newest_got or {}).get("description") or ""
            tag_hash = (gr_tags or {}).get(GENAI_HASH_TAG)
            tag_version = (gr_tags or {}).get(GENAI_VERSION_TAG)
            # The tags are the task's record of a publish; GetGuardrail's description on a version
            # is the hash only if the call returns the version's own (guardrail.py reads which).
            if tag_hash and tag_version == version:
                carries, source = tag_hash, "its tags"
            elif re.fullmatch(r"[0-9a-f]{64}", carried):
                carries, source = carried, "GetGuardrail's description"
            else:
                carries, source = None, None
            told = (
                f"; GetGuardrail's description {'is' if carried == carries else 'is not'} the hash"
                if source == "its tags"
                else ""
            )
            if carries is None:
                checks.note(
                    "ML-11",
                    what,
                    f"version {version} carries no hash: the tags name version "
                    f"{tag_version or '-'} - the next run of the guardrail task publishes and "
                    "tags one.",
                )
            elif checkout_hash is None:
                checks.note(
                    "ML-11",
                    what,
                    f"version {version} carries {short_hash(carries)}; {GENAI_DEFINITION} "
                    "unreadable.",
                )
            elif carries == checkout_hash:
                checks.ok(
                    "ML-11",
                    what,
                    f"version {version} carries {short_hash(carries)}, the checkout's definition, "
                    f"by {source}{told}",
                )
            else:
                checks.note(
                    "ML-11",
                    what,
                    f"version {version} carries {short_hash(carries)} by {source}, the checkout's "
                    f"definition {short_hash(checkout_hash)} - a deploy of the checkout and a run "
                    "of app-genai-triage publish it.",
                )
    if genai_dev is not None:
        nova = [
            prof
            for prof in genai_profiles
            if any(last_segment(m.get("modelArn")) == GENAI_MODEL for m in prof.get("models") or [])
        ]
        if not nova:
            checks.note(
                "ML-11",
                f"inference profile for {GENAI_MODEL}",
                "none tagged with app-genai-dev - the project's first use of the model creates it "
                "(10.4).",
            )
        for prof in nova:
            arns = {m.get("modelArn", "") for m in prof.get("models") or []}
            pid = prof.get("inferenceProfileId") or last_segment(prof.get("inferenceProfileArn"))
            what = f"inference profile {prof.get('inferenceProfileName') or pid}"
            if arns == {f"arn:aws:bedrock:{context.REGION}::foundation-model/{GENAI_MODEL}"}:
                checks.ok(
                    "ML-11",
                    what,
                    f"{prof.get('status', '-')}, id {pid}; {GENAI_MODEL} in {context.REGION} "
                    "alone (decision 23 (a))",
                )
            else:
                listed = ", ".join(sorted(f"{last_segment(a)} in {arn_region(a)}" for a in arns))
                checks.fail(
                    "ML-11",
                    what,
                    f"{listed} - decision 23 (a) keeps {GENAI_MODEL} inside {context.REGION}.",
                )
    genai_report_rows = []  # (report, written, passed, detail) for section 13
    for name, workflow in GENAI_REPORTS:
        if genai_dev is None:
            break
        what = f"shared/{GENAI_OUTBOX}{name}"
        if genai_reports is None:
            checks.note(
                "ML-11",
                what,
                "the outbox unread: no bucket on the role, or the listing failed (section 15).",
            )
            continue
        if name not in genai_reports:
            checks.note("ML-11", what, f"absent - {workflow}'s run writes it (10.4).")
            continue
        modified, text = genai_reports[name]
        if text is None:
            checks.note("ML-11", what, "unread - see section 15.")
            continue
        try:
            report = json.loads(text)
        except json.JSONDecodeError:
            report = None
        if not isinstance(report, dict):
            checks.fail("ML-11", what, f"written {modified}, and no JSON object.")
            continue
        passed = report.get("passed")
        failures = [flat(f) for f in report.get("failures") or []]
        if "outcome" in report:
            detail = f"outcome {report.get('outcome', '-')}, expected {report.get('expected', '-')}"
            detail += f", {report['error']}" if report.get("error") else ""
        else:
            guard = report.get("guardrail") or {}
            detail = (
                f"accuracy {report.get('accuracy', '-')} against {report.get('min_accuracy', '-')}; "
                f"{report.get('answers', '-')} answers to {report.get('messages', '-')} messages, "
                f"{report.get('let_through', '-')} let through, {report.get('blocked', '-')} "
                f"blocked; guardrail version {guard.get('version', '-')}, sha256 "
                f"{short_hash(guard.get('sha256'))}"
            )
        detail += f"; model {last_segment(report.get('model'))}; written {modified}"
        genai_report_rows.append((name, modified, passed, detail))
        if passed is True:
            checks.ok("ML-11", what, f"passed: {detail}")
        elif failures and all(f.startswith("accuracy ") for f in failures):
            checks.note(
                "ML-11",
                what,
                f"{failures[0]}: the model's quality, reported and never checked ({detail}).",
            )
        elif passed is False:
            checks.fail(
                "ML-11",
                what,
                f"not passed: {'; '.join(failures[:5]) or 'no failure listed'} ({detail}).",
            )
        else:
            checks.fail("ML-11", what, f"no verdict in the report ({detail}).")
    if genai_dev is not None:
        what = f"{GENAI_POLICY} on app-genai-dev's role"
        if genai_policy is None:
            checks.fail(
                "ML-11",
                what,
                "not attached - sandbox/bedrock attaches it to application_roles, and the "
                "guardrail task needs it (10.4).",
            )
        else:
            _arn, version, created, deny = genai_policy
            stamp = f"{version}, created {created or '-'}"
            if deny is None:
                checks.note("ML-11", what, f"{stamp}; its document unread - see section 15.")
            elif deny:
                checks.note(
                    "ML-11",
                    what,
                    f"{stamp}: carries {GENAI_DENY_SID} - application_guardrail_required true, 10.4 "
                    "step 4's state until its sitting ends.",
                )
            else:
                checks.note(
                    "ML-11",
                    what,
                    f"{stamp}: no {GENAI_DENY_SID} - application_guardrail_required false, the "
                    "state between sittings.",
                )
    what = "ListEnforcedGuardrailsConfiguration"
    if enforced_configs is None:
        checks.note("ML-11", what, "unread - see section 15.")
    elif not enforced_configs:
        checks.ok("ML-11", what, "empty")
    else:
        names = {g.get("id"): g.get("name", "-") for g in guardrail_summaries}
        listed = "; ".join(
            f"{names.get(c.get('guardrailId'), c.get('guardrailId', '-'))} version "
            f"{c.get('guardrailVersion', '-')} on "
            + (", ".join((c.get("modelEnforcement") or {}).get("includedModels") or []) or "-")
            for c in enforced_configs
        )
        checks.fail(
            "ML-11",
            what,
            f"{listed} - empty outside 10.4 step 6's sitting, which deletes the configuration "
            f"of {ACCOUNT_GUARDRAIL} before it ends.",
        )

    # ================================================================== report
    with open(out_path, "w") as stream:
        rep = Report(stream)
        rep.banner(
            f"sandbox-ml.txt - machine learning in a Sandbox project (Stage 17)\n"
            f"generated {context.utc_stamp()} by ./aws/sandbox-ml.py"
        )
        rep.text(
            "\nSections: 1 who is asking; 2 the project roles; 3 MLflow Apps; 4 training jobs;\n"
            "5 the Model Registry; 6 serving; 7 ML pipelines; 8 the entries read and the\n"
            "quotas; 9 the Generative AI menu; 10 the session's doors; 11 CloudTrail;\n"
            "12 app-ml in app-ml-dev; 13 app-genai in app-genai-dev; 14 checks ML-1..ML-11;\n"
            "15 calls that failed.\n"
            f"Contracts: MODEL_GROUP={MODEL_GROUP}  DEMO_DIR=shared/{DEMO_DIR}  "
            f"ML_POLICY={ML_POLICY} {ML_POLICY_VERSION}\n"
            f"           EXERCISE_TYPES={', '.join(t for _u, t in EXERCISE_TYPES)}  "
            f"CEILING_NEGATIVE={CEILING_NEGATIVE}\n"
            f"           APP_ML_DEV={APP_ML_DEV}  APP_ML_GROUP={APP_ML_GROUP}  "
            f"APP_GENAI_DEV={APP_GENAI_DEV}  GENAI_MODEL={GENAI_MODEL}\n"
        )

        rep.h1("1. Who is asking")
        rep.tabulate(
            ["PROFILE\tACCOUNT\tARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )
        rep.line()
        rep.line(f"ACCOUNT_ID={account}")
        rep.line(f"REGION={context.REGION}")
        rep.line(f"JOB_IMAGE_URI={container_image or '-'}")
        rep.line(
            f"(the house image {HOUSE_IMAGE}, version {(image or {}).get('Version', '-')}: the "
            "pipeline's processing step runs it)"
        )

        rep.h1("2. The project roles - ML-1")
        rows = [f"ROLE\tPROJECT\tDOMAIN\t{ML_TAG}\tKEY\tBUCKET\tBOUNDARY"]
        for p in projects.values():
            rows.append(
                f"{p['role']}\t{p['project'] or '-'}\t{p['domain'] or '-'}\t"
                f"{p['tags'].get(ML_TAG, 'absent')}\t"
                f"{(p['key_aliases'] or [p['key_id'] or '-'])[0]}\t{p['bucket'] or '-'}\t"
                f"{p['boundary'].rsplit('/', 1)[-1] or '(none)'}"
            )
        rep.tabulate(rows if len(rows) > 1 else rows + ["(no project role)\t-\t-\t-\t-\t-\t-"])
        for p in projects.values():
            rep.line()
            rep.line(f"ROLE={p['role']}")
            rep.line(f"PROJECT_ID={p['project'] or '-'}  ENVIRONMENT_ID={p['env'] or '-'}")
            rep.line(f"BOUNDARY_ARN={p['boundary'] or '-'}")
            rep.line(
                "attached: " + (", ".join(a.get("PolicyName", "-") for a in p["attached"]) or "-")
            )
        for arn, (version, doc) in sorted(policies.items()):
            if not arn.endswith(f"/{ML_POLICY}"):
                continue
            rep.h2(f"{ML_POLICY} {version}")
            rows = ["SID\tACTIONS\tCONDITION KEYS"]
            for sid in (SID_CREATE, SID_TAG, SID_MLFLOW):
                st = statements_by_sid(doc).get(sid)
                if st is None:
                    rows.append(f"{sid}\t(absent)\t-")
                    continue
                rows.append(
                    f"{sid}\t{len(as_list(st.get('Action')))} action(s)\t"
                    f"{', '.join(condition_keys(st)) or '-'}"
                )
            rep.tabulate(rows)
            tag_st = statements_by_sid(doc).get(SID_TAG)
            if tag_st:
                rep.line()
                rep.line(f"{SID_TAG} condition, as served:")
                rep.line(json.dumps(tag_st.get("Condition") or {}, sort_keys=True))
        for arn, (version, doc) in sorted(policies.items()):
            if "boundary" not in arn.rsplit("/", 1)[-1]:
                continue
            rep.h2(f"{arn.rsplit('/', 1)[-1]} {version}")
            present_sids = statements_by_sid(doc)
            rep.tabulate(
                ["SID\tPRESENT"]
                + [f"{s}\t{'yes' if s in present_sids else 'NO'}" for s in BOUNDARY_SIDS]
            )
            rep.line()
            rep.line(f"ceiling: {', '.join(ceiling_types(doc) or ['(unreadable)'])}")
        rep.h2(f"The Tooling stacks - {ISOLATION_PARAMETER} (step 0.8)")
        rows = ["ROLE\tSTACK\tSTATUS\tVALUE"]
        for role, (name, status, value, _keys) in stacks.items():
            rows.append(f"{role}\t{name}\t{status}\t{value if value is not None else '-'}")
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-"])
        for role, (name, status, value, keys) in stacks.items():
            if value is None and keys:
                rep.line()
                rep.line(f"{name} carries these parameters, none named {ISOLATION_PARAMETER}:")
                rep.line(", ".join(keys))
        for p in list(projects.values())[:1]:
            rep.show(
                cli,
                "iam",
                "get-role",
                "--role-name",
                p["role"],
                "--query",
                "Role.Tags",
                "--output",
                "table",
                lead_blank=True,
            )

        rep.h1("3. MLflow Apps - ML-2")
        rows = ["NAME\tSTATUS\tVERSION\tARTIFACT STORE\tKEY\tROLE\tREGISTRATION\tTAG"]
        for app in apps:
            cells = [
                app.get("Name", "-"),
                app.get("Status", "-"),
                app.get("MlflowVersion", "-"),
                app.get("ArtifactStoreUri") or "-",
                last_segment(app.get("KmsKeyId")),
                last_segment(app.get("RoleArn")),
                app.get("ModelRegistrationMode", "-"),
                app["_tags"].get(PROJECT_TAG, "-"),
            ]
            rows.append("\t".join(str(c) for c in cells))
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-\t-\t-\t-\t-"])
        # The value examples/sandbox-ml/extra_values.json and app-ml's deploy name MLFLOW_APP_ARN.
        for app in apps:
            rep.line(f"MLFLOW_APP_ARN={app.get('Arn', '-')}  ({app.get('Name', '-')})")

        rep.h1("4. Training jobs - ML-3")
        rows = ["JOB\tSTATUS\tINSTANCE\tBILLED S\tVPC\tISOLATED\tICE\tVOLUME KEY\tTAG\tIMAGE"]
        for j in jobs:
            res = j.get("ResourceConfig") or {}
            cells = [
                j.get("TrainingJobName", "-"),
                j.get("TrainingJobStatus", "-"),
                res.get("InstanceType", "-"),
                j.get("BillableTimeInSeconds", "-"),
                "yes" if (j.get("VpcConfig") or {}).get("Subnets") else "no",
                j.get("EnableNetworkIsolation", "-"),
                j.get("EnableInterContainerTrafficEncryption", "-"),
                last_segment(res.get("VolumeKmsKeyId")),
                j["_tags"].get(PROJECT_TAG, "-"),
                last_segment((j.get("AlgorithmSpecification") or {}).get("TrainingImage")),
            ]
            rows.append("\t".join(str(c) for c in cells))
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-\t-\t-\t-\t-\t-\t-"])
        for j in jobs[:2]:
            rep.show(
                cli,
                "sagemaker",
                "describe-training-job",
                "--training-job-name",
                j.get("TrainingJobName", ""),
                "--query",
                JOB_QUERY,
                lead_blank=True,
            )

        rep.h1(f"5. The Model Registry - {MODEL_GROUP} - ML-4")
        rows = ["VERSION\tAPPROVAL\tSTATUS\tREGISTRATION\tMODEL DATA"]
        for pkg in packages:
            containers = (pkg.get("InferenceSpecification") or {}).get("Containers", [])
            cells = [
                pkg.get("ModelPackageVersion", "-"),
                pkg.get("ModelApprovalStatus", "-"),
                pkg.get("ModelPackageStatus", "-"),
                pkg.get("ModelPackageRegistrationType", "-"),
                ", ".join(c.get("ModelDataUrl", "-") for c in containers) or "-",
            ]
            rows.append("\t".join(str(c) for c in cells))
        rep.tabulate(
            rows
            if len(rows) > 1
            else rows + [f"({'no version' if group else 'no group'})\t-\t-\t-\t-"]
        )
        rep.line()
        rep.line(f"every model package group: {', '.join(all_groups) or '(none)'}")

        rep.h1("6. Serving - ML-5")
        rows = ["KIND\tNAME\tSTATUS\tCREATED"]
        rows += [
            f"endpoint\t{e.get('EndpointName', '-')}\t{e.get('EndpointStatus', '-')}\t"
            f"{e.get('CreationTime', '-')}"
            for e in endpoints
        ]
        rows += [
            f"endpoint config\t{c.get('EndpointConfigName', '-')}\t-\t{c.get('CreationTime', '-')}"
            for c in endpoint_configs
        ]
        rows += [
            f"model\t{m.get('ModelName', '-')}\t-\t{m.get('CreationTime', '-')}" for m in models
        ]
        rows += [
            f"transform job\t{t.get('TransformJobName', '-')}\t{t.get('TransformJobStatus', '-')}\t"
            f"{t.get('CreationTime', '-')}"
            for t in transforms
        ]
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-"])
        rep.show(cli, "sagemaker", "list-endpoints", "--output", "table", lead_blank=True)
        rep.h2(f"Metrics over the last {METRIC_DAYS} days")
        rows = ["METRIC\tDIMENSION\tSUM"]
        rows += [
            f"Invocations\t{e}/{v}\t{'-' if s is None else f'{s:.0f}'}" for e, v, s in invocations
        ]
        rows += [
            f"BytesProcessed\t{svc} {vpce}{'' if sub == '-' else ' ' + sub}\t"
            f"{'-' if s is None else f'{s:.0f}'}"
            for svc, vpce, sub, s in endpoint_bytes
        ]
        rep.tabulate(rows if len(rows) > 1 else rows + ["(no data point)\t-\t-"])
        rep.line()
        rep.line("A metric is published only for a period with traffic, and list-metrics returns")
        rep.line("only those with data in the last two weeks: an absent row is no traffic read.")

        rep.h1("7. ML pipelines - ML-6")
        rows = ["PIPELINE\tSTATUS\tROLE\tSTEPS\tLATEST EXECUTION\tSTARTED"]
        for pl in pipelines:
            latest = pl["executions"][0] if pl["executions"] else {}
            rows.append(
                f"{pl['name']}\t{pl['desc'].get('PipelineStatus', '-')}\t"
                f"{(pl['desc'].get('RoleArn') or '-').rsplit('/', 1)[-1]}\t"
                f"{len(all_steps(pl['definition']))}\t"
                f"{latest.get('PipelineExecutionStatus', '-')}\t{latest.get('StartTime', '-')}"
            )
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-\t-\t-"])
        for pl in pipelines:
            if not pl["steps"]:
                continue
            rep.h2(f"{pl['name']} - the latest execution's steps")
            rep.tabulate(
                ["STEP\tSTATUS\tMETADATA\tFAILURE"]
                + [
                    f"{s.get('StepName', '-')}\t{s.get('StepStatus', '-')}\t"
                    f"{', '.join(sorted((s.get('Metadata') or {}).keys())) or '-'}\t"
                    f"{s.get('FailureReason') or '-'}"
                    for s in pl["steps"]
                ]
            )

        rep.h1("8. The entries read, not created, and the quotas - ML-7")
        rows = ["KIND\tNAME\tSTATUS"]
        rows += [
            f"HyperPod cluster\t{c.get('ClusterName', '-')}\t{c.get('ClusterStatus', '-')}"
            for c in clusters
        ]
        rows += [
            f"Partner AI app\t{a.get('Name', '-')}\t{a.get('Status', '-')}" for a in partner_apps
        ]
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-"])
        rep.line()
        rows = ["QUOTA\tVALUE\tSOURCE\tAWS DEFAULT\tCODE\tLATEST REQUEST"]
        for qname in QUOTAS + tuple(mlflow_quotas):
            value, source_name, code = quota_rows.get(qname, (None, "-", "-"))
            default = quota_text(quota_defaults.get(qname))
            latest = request_text(quota_requests, code)
            rows.append(f"{qname}\t{quota_text(value)}\t{source_name}\t{default}\t{code}\t{latest}")
        rep.tabulate(rows)

        rep.h1("9. The Generative AI menu - ML-8")
        rows = ["ROLE\tBOUNDARY\tPROJECT\tPOLICIES"]
        rows += [
            f"{br['name']}\t{last_segment(br['boundary']) if br['boundary'] else '(none)'}\t"
            f"{br['project'] or '-'}\t{', '.join(br['policies']) or '-'}"
            for br in bedrock_roles
        ]
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-\t-"])
        rep.line()
        rows = ["KIND\tNAME\tDETAIL"]
        rows += [
            f"Lambda\t{f.get('FunctionName', '-')}\t"
            f"{(f.get('VpcConfig') or {}).get('VpcId') or 'no VPC'}"
            for f in every_function
        ]
        rows += [
            f"knowledge base\t{kb.get('name', '-')}\t{kb.get('status', '-')}, "
            f"{(kb.get('storageConfiguration') or {}).get('type', '-')}"
            for kb in kbs
        ]
        rows += [
            f"OpenSearch Serverless collection\t{c.get('name', '-')}\t{c.get('status', '-')}"
            for c in collections
        ]
        rows += [
            f"S3 vector bucket\t{b.get('vectorBucketName', '-')}\t{b.get('creationTime', '-')}"
            for b in vector_buckets
        ]
        for kind, items in genai.items():
            rows += [f"{kind}\t{item_name}\t-" for item_name, _arn in items]
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none)\t-\t-"])
        rep.line()
        rep.line(
            f"{bedrockscope.SID_MODELS} in the repository's SCP admits: "
            + (", ".join(sorted(scp_models)) if scp_models else scp_why or "-")
            + ("; application inference profiles" if scp_app_profiles else "")
        )

        rep.h1("10. The session's doors - ML-9")
        rows = ["SERVICE\tENDPOINT\tSTATE\tPRIVATE DNS\tSUBNETS"]
        for service in sorted(by_service):
            for e in by_service[service]:
                rows.append(
                    f"{service}\t{e.get('VpcEndpointId', '-')}\t{e.get('State', '-')}\t"
                    f"{e.get('PrivateDnsEnabled', '-')}\t{len(e.get('SubnetIds', []))}"
                )
        rep.tabulate(rows if len(rows) > 1 else rows + ["(no interface endpoint)\t-\t-\t-\t-"])
        rep.line()
        rep.line(
            f"S3 gateway: {(gateway or {}).get('VpcEndpointId', '(absent)')}; DNS Firewall list "
            f"{DNS_LIST}: {(dns or {}).get('Id', '(absent)')}, {len(dns_entries)} entries"
        )
        rep.line(
            "private subnets: "
            + (", ".join(f"{n} {az}" for n, az in sorted(private.values())) or "(none read)")
        )

        rep.h1("11. CloudTrail - the stage's creates")
        rows = ["TIME\tEVENT\tSUBJECT\tROLE\tSESSION\tVPC ENDPOINT\tSOURCE\tERROR"]
        for name in SAGEMAKER_EVENTS + BEDROCK_EVENTS + (PULL_EVENT,):
            for ev in events[name]:
                role, session = caller_of(ev)
                rows.append(
                    f"{ev.get('eventTime', '-')}\t{name}\t{subject_of(ev)}\t{role}\t{session}\t"
                    f"{ev.get('vpcEndpointId') or '-'}\t{ev.get('sourceIPAddress', '-')}\t"
                    f"{ev.get('errorCode') or '-'}"
                )
        rep.tabulate(
            rows if len(rows) > 1 else rows + ["(none in the window)\t-\t-\t-\t-\t-\t-\t-"]
        )
        rep.line()
        rep.line(f"The latest {LOOKUP_MAX} events per name, in the 90-day lookup window;")
        rep.line(f"{PULL_EVENT} only for {XGBOOST_REPOSITORY}.")

        rep.h1("12. app-ml in app-ml-dev - ML-10")
        rep.line(f"PROJECT_ID={APP_ML_DEV}  ROLE={(ml_dev or {}).get('role', '(no role read)')}")
        rep.line()
        rows = ["KIND\tJOB\tSTATUS\tINSTANCE\tVPC\tISOLATED\tICE\tVOLUME KEY\tOUTPUT KEY\tTAG"]
        for kind, j in app_ml_jobs:
            v = job_view(kind, j)
            vpc = "-" if v["vpc"] is None else ("yes" if v["vpc"].get("Subnets") else "no")
            cells = [
                kind,
                v["name"],
                v["status"],
                v["itype"],
                vpc,
                cell(v["isolation"]),
                cell(v["ice"]),
                last_segment(v["volume_key"]),
                last_segment(v["output_key"]),
                j["_tags"].get(PROJECT_TAG, "-"),
            ]
            rows.append("\t".join(str(c) for c in cells))
        rep.tabulate(rows if len(rows) > 1 else rows + ["(no app-ml job)" + "\t-" * 9])
        rep.line()
        rows = ["MODEL\tCREATED\tROLE"]
        rows += [
            f"{m.get('ModelName', '-')}\t{m.get('CreationTime', '-')}\t"
            f"{last_segment(m.get('ExecutionRoleArn'))}"
            for m in leftovers
        ]
        rep.tabulate(rows if len(rows) > 1 else rows + [f"(no model {APP_ML_MODEL_PREFIX}*)\t-\t-"])
        rep.h2(f"The candidate - shared/{APP_ML_CANDIDATE}")
        rows = ["OBJECT\tSIZE\tLAST MODIFIED"]
        rows += [
            f"{n}\t{o.get('Size', '-')}\t{o.get('LastModified', '-')}"
            for n, o in sorted((ml_objects or {}).items())
        ]
        state = "unread" if ml_objects is None else "nothing"
        rep.tabulate(rows if len(rows) > 1 else rows + [f"({state})\t-\t-"])
        if ml_model:
            rep.line()
            for key in ("training_job", "sha256", "size_bytes", "auc", "published"):
                rep.line(f"model.json {key}: {cell(ml_model.get(key))}")
            rep.line(f"model.tar.gz sha256, as read: {ml_digest or '(unread)'}")
        rep.h2(f"The model package group - {APP_ML_GROUP}")
        rows = ["VERSION\tAPPROVAL\tSTATUS\tCREATED\tSHA256 IN ITS DESCRIPTION"]
        for v in ml_versions:
            mark = re.search(r"sha256:([0-9a-f]{64})", v.get("ModelPackageDescription") or "")
            rows.append(
                f"{v.get('ModelPackageVersion', '-')}\t{v.get('ModelApprovalStatus', '-')}\t"
                f"{v.get('ModelPackageStatus', '-')}\t{v.get('CreationTime', '-')}\t"
                f"{mark.group(1) if mark else '-'}"
            )
        if ml_group:
            state = "no version"
        else:
            state = "no group" if APP_ML_GROUP not in all_groups else "unread"
        rep.tabulate(rows if len(rows) > 1 else rows + [f"({state})\t-\t-\t-\t-"])
        if ml_group:
            rep.line()
            rep.line(f"{PROJECT_TAG}: {ml_group_tags.get(PROJECT_TAG, '(none)')}")
        for pkg in ml_carrying:
            meta = pkg.get("CustomerMetadataProperties") or {}
            by = principal_name(((pkg.get("CreatedBy") or {}).get("IamIdentity") or {}).get("Arn"))
            rep.line(
                f"version {pkg.get('ModelPackageVersion', '-')} carries the candidate's hash; "
                f"registered by {by}; training_job {meta.get('training_job', '-')}, "
                f"validation_auc {meta.get('validation_auc', '-')}"
            )
        rep.h2("The MLflow App and the runs track logged")
        rows = ["APP\tSTATUS\tARTIFACT STORE"]
        rows += [
            f"{a.get('Name', '-')}\t{a.get('Status', '-')}\t{a.get('ArtifactStoreUri') or '-'}"
            for a in ml_apps
        ]
        rep.tabulate(rows if len(rows) > 1 else rows + ["(no MLflow App of app-ml-dev)\t-\t-"])
        if ml_runs:
            rep.line()
            rows = ["EXPERIMENT/RUN\tLAST MODIFIED\tTRAINING JOB"]
            rows += [
                f"{key.split('/artifacts/', 1)[0]}\t{modified}\t{job or '-'}"
                for key, modified, job in ml_runs
            ]
            rep.tabulate(rows)
        rep.line()
        rep.line(
            f"The newest {MLFLOW_RUNS_READ} keys ending {MLFLOW_EVALUATION_SUFFIX} in the store;"
        )
        rep.line("the layout <experiment id>/<run id>/artifacts/ is MLflow's, unmeasured here.")

        rep.h1("13. app-genai in app-genai-dev - ML-11")
        rep.line(
            f"PROJECT_ID={APP_GENAI_DEV}  ROLE={(genai_dev or {}).get('role', '(no role read)')}"
        )
        rep.line(f"{GENAI_DEFINITION}: sha256 {checkout_hash or '(unreadable)'}")
        rep.line()
        rows = ["GUARDRAIL\tVERSION\tSTATUS\tDESCRIPTION\tUPDATED"]
        rows += [
            f"{gr_name}\t{v.get('version', '-')}\t{v.get('status', '-')}\t"
            f"{cell(v.get('description'))}\t{v.get('updatedAt', '-')}"
            for v in gr_versions
        ]
        rep.tabulate(rows if len(rows) > 1 else rows + [f"(no guardrail {gr_name})\t-\t-\t-\t-"])
        if gr:
            rep.line()
            tags_text = ", ".join(f"{k}={v}" for k, v in sorted((gr_tags or {}).items()))
            rep.line(f"id {gr.get('id', '-')}; tags {tags_text or '(none read)'}")
        if gr_newest:
            rep.line(
                f"GetGuardrail on version {gr_newest.get('version', '-')}: description "
                f"{cell((gr_newest_got or {}).get('description'))}"
            )
        rep.line()
        rows = ["INFERENCE PROFILE\tID\tSTATUS\tMODELS"]
        for prof in genai_profiles:
            listed = ", ".join(
                sorted(
                    f"{last_segment(m.get('modelArn'))} in {arn_region(m.get('modelArn'))}"
                    for m in prof.get("models") or []
                )
            )
            rows.append(
                f"{prof.get('inferenceProfileName', '-')}\t"
                f"{prof.get('inferenceProfileId') or last_segment(prof.get('inferenceProfileArn'))}"
                f"\t{prof.get('status', '-')}\t{listed or '-'}"
            )
        rep.tabulate(rows if len(rows) > 1 else rows + ["(none tagged with the project)\t-\t-\t-"])
        rep.line()
        rows = ["REPORT\tWRITTEN\tPASSED\tDETAIL"]
        rows += [f"{n}\t{w}\t{cell(p)}\t{d}" for n, w, p, d in genai_report_rows]
        rep.tabulate(rows if len(rows) > 1 else rows + [f"(none read in {GENAI_OUTBOX})\t-\t-\t-"])
        rep.line()
        if genai_policy is None:
            rep.line(f"{GENAI_POLICY}: not attached to the role")
        else:
            _arn, version, created, deny = genai_policy
            state = {True: "present", False: "absent"}.get(deny, "(unread)")
            rep.line(
                f"{GENAI_POLICY} {version}, created {created or '-'}: {GENAI_DENY_SID} {state}"
            )
        rep.line()
        rows = ["ENFORCED GUARDRAIL\tVERSION\tOWNER\tINCLUDED MODELS\tEXCLUDED MODELS\tUPDATED"]
        names = {g.get("id"): g.get("name", "-") for g in guardrail_summaries}
        for c in enforced_configs or []:
            enforcement = c.get("modelEnforcement") or {}
            rows.append(
                f"{names.get(c.get('guardrailId'), c.get('guardrailId', '-'))}\t"
                f"{c.get('guardrailVersion', '-')}\t{c.get('owner', '-')}\t"
                f"{', '.join(enforcement.get('includedModels') or []) or '-'}\t"
                f"{', '.join(enforcement.get('excludedModels') or []) or '-'}\t"
                f"{c.get('updatedAt', '-')}"
            )
        state = "unread" if enforced_configs is None else "empty"
        rep.tabulate(rows if len(rows) > 1 else rows + [f"({state})\t-\t-\t-\t-\t-"])

        rep.h1("14. Checks")
        rep.checks_table(checks)

        rep.h1("15. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/sandbox-ml.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 15)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 14)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
