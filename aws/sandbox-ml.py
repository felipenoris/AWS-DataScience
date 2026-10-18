#!/usr/bin/env -S uv run --quiet
# sandbox-ml.py - Stage 17's evidence: the machine learning a SageMaker Unified Studio project
# offers, read in the Sandbox account. The project roles (the ML tag, the managed policy's
# version and its create and tag statements, the D13 boundary's five statements and its
# instance ceiling, the Tooling stack's enableNetworkIsolation), the MLflow Apps, every training
# job against the boundary's four job settings, the Model Registry group ml-demo-xgboost, the
# serving objects (no endpoint may survive a sitting), the ML pipelines, the entries read
# without being created (HyperPod, Partner AI apps) with the quotas that bound the exercise,
# the Generative AI objects and the roles behind them, the doors a session opens (the interface
# endpoints, the S3 gateway's allow-list, the DNS Firewall list), and CloudTrail's record of
# who created each object, and through which door.
#
#   needs:    a live SSO session, the only prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             and an AWS CLI that knows `sagemaker list-mlflow-apps`, `s3vectors` and
#             `bedrock get-foundation-model-availability`. A CLI that does not fails those
#             calls into section 13, and the checks that needed them say so.
#   run:      ./aws/sandbox-ml.py                        # the Sandbox profile
#             ./aws/sandbox-ml.py awsds-infra-sandbox-1  # the same, named
#             python3 aws/sandbox-ml.py -                # CloudShell, ambient
#   writes:   aws/output/sandbox-ml.txt, and each pipeline's live definition under
#             aws/output/sandbox-ml/ (untracked - see .gitignore)
#   reads:    iam:ListRoles, GetRole, ListAttachedRolePolicies, GetPolicy, GetPolicyVersion;
#             kms:ListAliases; cloudformation:DescribeStacks; sagemaker:ListMlflowApps,
#             DescribeMlflowApp, ListTrainingJobs, DescribeTrainingJob, ListModelPackageGroups,
#             DescribeModelPackageGroup, ListModelPackages, DescribeModelPackage, ListEndpoints,
#             ListEndpointConfigs, ListModels, DescribeModel, ListTransformJobs,
#             DescribeTransformJob, ListPipelines, DescribePipeline, ListPipelineExecutions,
#             ListPipelineExecutionSteps, ListClusters, ListPartnerApps, DescribeImageVersion,
#             ListTags; servicequotas:ListServiceQuotas, ListAWSDefaultServiceQuotas,
#             ListRequestedServiceQuotaChangeHistory;
#             bedrock:ListGuardrails, ListEvaluationJobs, GetFoundationModelAvailability,
#             ListTagsForResource; bedrock-agent (bedrock:) ListKnowledgeBases, GetKnowledgeBase,
#             ListDataSources, ListAgents, ListPrompts, ListFlows; aoss:ListCollections;
#             s3vectors:ListVectorBuckets; lambda:ListFunctions; ec2:DescribeSubnets,
#             DescribeSecurityGroups, DescribeVpcEndpoints; route53resolver:
#             ListFirewallDomainLists, ListFirewallDomains; cloudwatch:ListMetrics,
#             GetMetricStatistics; s3api:HeadObject; cloudtrail:LookupEvents;
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
# runs as or whose tag it carries.
#
# What it cannot see, since an empty listing and a missing account look alike:
#   - The space: the SDK's configuration files and the interpreters' versions (Stage 17 step
#     0.3) - a person reads them in JupyterLab.
#   - The portal's forms (step 0.7) - a person reads them.
#   - The MLflow data plane's calls and InvokeEndpoint write no management event: the
#     endpoints' BytesProcessed and the Invocations metric (sections 6 and 10) are the
#     readings, and a metric with no traffic in the window is absent, not zero.
#   - The quality of a model: the validation AUC is reported, never checked.
#   - "Not built yet" is a note, never a fail.

from __future__ import annotations

import fnmatch
import json
import re
import sys
from datetime import datetime, timedelta, timezone

from awslib import bedrockscope, context, profiles
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
UNREAD = "(unread)"  # a value whose call failed: the call is in section 13

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
    the execution's own job is what ML-3 reads."""
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
            "EnableNetworkIsolation": net.get("EnableNetworkIsolation"),
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
        return "its increase requests unread (section 13)"
    request = requests.get(code)
    if not request:
        return "no increase request"
    created = str(request.get("Created") or "-")[:10]
    return (
        f"increase to {quota_text(request.get('DesiredValue'))} requested {created}, "
        f"{request.get('Status', '-')}"
    )


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

    def policy_document(arn: str) -> tuple:
        """(default version id, document) of a managed policy, or ('-', None)."""
        got = run_json("iam", "get-policy", "--policy-arn", arn) or {}
        version = (got.get("Policy") or {}).get("DefaultVersionId")
        if not version:
            return "-", None
        doc = (
            run_json("iam", "get-policy-version", "--policy-arn", arn, "--version-id", version)
            or {}
        )
        return version, (doc.get("PolicyVersion") or {}).get("Document")

    def tags_of(arn: str) -> dict:
        got = run_json("sagemaker", "list-tags", "--resource-arn", arn) or {}
        return {t["Key"]: t["Value"] for t in got.get("Tags", [])}

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
    collections = (run_json("opensearchserverless", "list-collections") or {}).get(
        "collectionSummaries", []
    )
    vector_buckets = (run_json("s3vectors", "list-vector-buckets") or {}).get("vectorBuckets", [])
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
        "guardrails": [
            (x.get("name", "-"), x.get("arn", "-"))
            for x in (run_json("bedrock", "list-guardrails") or {}).get("guardrails", [])
        ],
        "evaluation jobs": [
            (x.get("jobName", "-"), x.get("jobArn", "-"))
            for x in (run_json("bedrock", "list-evaluation-jobs") or {}).get("jobSummaries", [])
        ],
    }
    # The project tag of each object whose ARN a listing gives. bedrock-agent answers a map,
    # bedrock a list of {key, value} (botocore 1.43.114).
    genai_tags = {}  # arn -> project tag value
    tagged = [("bedrock-agent", arn) for kind in ("prompts", "flows") for _n, arn in genai[kind]]
    tagged += [("bedrock", arn) for _n, arn in genai["guardrails"]]
    tagged += [("bedrock-agent", kb.get("knowledgeBaseArn", "")) for kb in kbs]
    for service, arn in tagged:
        if not arn.startswith("arn:"):
            continue
        got = run_json(service, "list-tags-for-resource", "--resource-arn", arn)
        if got is None:
            genai_tags[arn] = UNREAD
            continue
        tags = got.get("tags") or {}
        if isinstance(tags, list):
            tags = {t.get("key"): t.get("value") for t in tags}
        genai_tags[arn] = tags.get(PROJECT_TAG, "")
    availability = (
        run_json("bedrock", "get-foundation-model-availability", "--model-id", EMBEDDINGS_MODEL)
        or {}
    )
    scp_models, _regions, scp_why = bedrockscope.scp_declaration(
        ctx.repo_root / bedrockscope.SCP_PATH
    )

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
            checks.note("ML-4", url, "head-object failed - see section 13.")
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

    # ML-5: serving. No endpoint may outlive its sitting (decision 6).
    for e in endpoints:
        checks.fail(
            "ML-5",
            e.get("EndpointName", "-"),
            f"{e.get('EndpointStatus', '-')} since {e.get('CreationTime', '-')} - an endpoint "
            "bills while it exists (0.115 USD/h per ml.m5.large) and no slice or make down "
            "reaches it: DeleteEndpoint now.",
        )
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
    for br in bedrock_roles:
        what = f"role {br['name']}"
        if not br["boundary"]:
            checks.fail(
                "ML-8",
                what,
                f"no permissions boundary - an interactive principal outside D13 (policies: "
                f"{', '.join(br['policies']) or 'none'}).",
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
            "admitted by the repository's SCP (decision 11); ./aws/org-policy-baseline.py "
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
            "12 checks ML-1..ML-9; 13 calls that failed.\n"
            f"Contracts: MODEL_GROUP={MODEL_GROUP}  DEMO_DIR=shared/{DEMO_DIR}  "
            f"ML_POLICY={ML_POLICY} {ML_POLICY_VERSION}\n"
            f"           EXERCISE_TYPES={', '.join(t for _u, t in EXERCISE_TYPES)}  "
            f"CEILING_NEGATIVE={CEILING_NEGATIVE}\n"
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

        rep.h1("12. Checks")
        rep.checks_table(checks)

        rep.h1("13. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/sandbox-ml.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 13)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 12)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
