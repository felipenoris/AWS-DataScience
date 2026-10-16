# deploy-role.tf - Stage 8 decision 19: awsds-deploy-sandbox-test, the role the pipeline's test-deploy
# job assumes to put a release of an application into D41's `test` project and run it there with the
# CI/CD CLI (step 2.5). It is this account's second deploy role, beside sandbox/foundation/'s
# awsds-deploy-devenv-sandbox (step 4.2), and it lives here because what it reaches is this slice's
# subject: a project role and the workflows that run as it.
#
# The grants are what the CLI 1.0.9's `bundle` and `deploy --targets test` called in the lab
# (2026-10-16, the stage log) and what the job calls around them, each scoped to the `test` project:
# the DataZone reads, the workflow calls on a workflow tagged with the project, the project role
# passed to the service, the project's shared/ prefix in the projects bucket and the project key, the
# workflow's log group, and the endpoint reading the job opens with. DataZone's own membership layer
# is not IAM: the role is made a member of the `test` project in the portal, by hand (EXC-17).
#
# The ceiling adds, to the module's denies, every role change, passing any role but the project's,
# and deleting a workflow. No state, since the role applies no slice (refusal 8), and no application
# ceiling, since the roles here are the service's, not an application's.
#
# The trust names the runner's role in the runner's home, built from the runner's name and the home's
# account id, which the alias below resolves (aws/INDEX.md rule 1). production/foundation/ must exist
# first: IAM refuses a trust policy naming a role that does not.

provider "aws" {
  alias   = "deploy_runner"
  region  = var.region
  profile = one([for k, v in var.deploy_runner : v.profile])
}

data "aws_caller_identity" "deploy_runner" {
  provider = aws.deploy_runner
}

locals {
  deploy_runner_role_arn = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.deploy_runner.account_id}:role/awsds-${one([for k, v in var.deploy_runner : v.env])}-runner-deploy"

  # The `test` project: its role, and its id, the second segment of the role's name,
  # datazone_usr_role_<project>_<environment> (variables.tf).
  test_project_role_arn = data.aws_iam_role.project[var.test_project_role].arn
  test_project_id       = regex("^datazone_usr_role_([a-z0-9]+)_", var.test_project_role)[0]

  # Where the CLI writes: the project's shared/ prefix in the projects bucket (sagemaker-prereqs/
  # s3.tf names it), <domain>/<project>/shared/, with the application's folders and operatorFiles/,
  # where `deploy` copies a workflow's code object, under it.
  projects_bucket_arn = "arn:${data.aws_partition.current.partition}:s3:::awsds-${var.env}-smus-projects"
  test_shared_prefix  = "${var.datazone_domain_id}/${local.test_project_id}/shared/"

  workflows       = "arn:${data.aws_partition.current.partition}:airflow-serverless:${var.region}:${data.aws_caller_identity.current.account_id}:workflow/*"
  test_log_groups = "arn:${data.aws_partition.current.partition}:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/mwaa-serverless/${var.datazone_domain_id}-${local.test_project_id}/*"
}

module "deploy_role_test" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/deploy-role?ref=deploy-role-v0.5.0"

  name            = var.deploy_role_name
  description     = "Stage 8's test deploy of an application (decision 19, step 2.5) - assumed only by the deploy runner's role; deploys a release to the test project with the CI/CD CLI and runs it, and applies no slice"
  env             = var.env
  boundary_name   = "awsds-${var.env}-deploy-test-boundary"
  runner_role_arn = local.deploy_runner_role_arn
  state_prefixes  = []

  inline_policies = {
    "project-reads" = data.aws_iam_policy_document.test_project_reads.json
    "workflows"     = data.aws_iam_policy_document.test_workflows.json
    "storage"       = data.aws_iam_policy_document.test_storage.json
  }

  boundary_denies_json = data.aws_iam_policy_document.test_ceiling.json
}

# The CLI resolves the domain, the project, its membership, its environments and its connections (the
# shared/ prefix and the workflows connection) before it copies anything. None of these reads takes a
# resource type but GetDomain, and the domain lives in the domain account (SMUS_DOMAIN in
# scripts/tfhygiene/backend.py), so its ARN names the domain by id in any account: an aliased
# identity of that account would cost this slice a third profile at plan for one read.
data "aws_iam_policy_document" "test_project_reads" {
  statement {
    sid    = "ReadTheProjectItsMembersAndItsConnections"
    effect = "Allow"
    actions = [
      "datazone:GetConnection",
      "datazone:GetEnvironment",
      "datazone:GetGroupProfile",
      "datazone:GetProject",
      "datazone:GetUserProfile",
      "datazone:ListConnections",
      "datazone:ListDomains",
      "datazone:ListEnvironmentBlueprints",
      "datazone:ListEnvironments",
      "datazone:ListProjectMemberships",
      "datazone:ListProjects",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "ReadTheDomain"
    effect    = "Allow"
    actions   = ["datazone:GetDomain"]
    resources = ["arn:${data.aws_partition.current.partition}:datazone:${var.region}:*:domain/${var.datazone_domain_id}"]
  }

  # The job's first reading, before anything is copied: the interface endpoints the run needs.
  statement {
    sid       = "ReadTheEndpoints"
    effect    = "Allow"
    actions   = ["ec2:DescribeVpcEndpoints"]
    resources = ["*"]
  }
}

# The workflow calls, on a workflow tagged with the `test` project: the CLI tags the workflow at its
# creation (AmazonDataZoneProject among six tags), and the tag is what every later call is scoped by,
# so a workflow of any other project is out of reach. ListWorkflows takes no resource type.
data "aws_iam_policy_document" "test_workflows" {
  statement {
    sid       = "ListTheWorkflows"
    effect    = "Allow"
    actions   = ["airflow-serverless:ListWorkflows"]
    resources = ["*"]
  }

  statement {
    sid       = "CreateAWorkflowOfTheTestProject"
    effect    = "Allow"
    actions   = ["airflow-serverless:CreateWorkflow"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = [local.test_project_id]
    }
  }

  # TagResource may re-apply the project tag with the project's own value and never another's.
  statement {
    sid    = "UpdateTagRunAndReadAWorkflowOfTheTestProject"
    effect = "Allow"
    actions = [
      "airflow-serverless:GetWorkflow",
      "airflow-serverless:GetWorkflowRun",
      "airflow-serverless:ListTagsForResource",
      "airflow-serverless:ListWorkflowRuns",
      "airflow-serverless:StartWorkflowRun",
      "airflow-serverless:TagResource",
      "airflow-serverless:UpdateWorkflow",
    ]
    resources = [local.workflows]

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = [local.test_project_id]
    }

    condition {
      test     = "StringEqualsIfExists"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = [local.test_project_id]
    }
  }

  # CreateWorkflow and UpdateWorkflow pass the project role to the service, the role the workflow runs
  # as: that role, to that service, and nothing else.
  statement {
    sid       = "PassTheTestProjectRoleToTheService"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = [local.test_project_role_arn]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["airflow-serverless.amazonaws.com"]
    }
  }

  # The workflow's log group: created in the caller's session when the workflow is created (measured
  # 2026-10-16; the CLI itself creates none), and read by `trailLogs` after the run.
  statement {
    sid       = "CreateAndReadTheWorkflowsLogGroup"
    effect    = "Allow"
    actions   = ["logs:CreateLogGroup", "logs:FilterLogEvents"]
    resources = [local.test_log_groups]
  }
}

# The `test` project's shared/ prefix in the projects bucket, and nothing of any other project: the
# listing the CLI and the job's `aws s3 rm` do, and the objects read, written and deleted under it,
# the application's folders and operatorFiles/ alike.
data "aws_iam_policy_document" "test_storage" {
  statement {
    sid       = "ListTheTestProjectsSharedPrefix"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [local.projects_bucket_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${local.test_shared_prefix}*"]
    }
  }

  statement {
    sid       = "ReadWriteAndEmptyUnderTheTestProjectsSharedPrefix"
    effect    = "Allow"
    actions   = ["s3:AbortMultipartUpload", "s3:DeleteObject", "s3:GetObject", "s3:PutObject"]
    resources = ["${local.projects_bucket_arn}/${local.test_shared_prefix}*"]
  }

  # The project key, which the bucket encrypts under: the data keys of the uploads and the reads, and
  # the grants the service creates on the caller's behalf when the workflow is created (two per
  # creation, measured 2026-10-16; the CLI itself calls CreateGrant nowhere).
  statement {
    sid       = "UseTheProjectKey"
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:DescribeKey", "kms:GenerateDataKey"]
    resources = [data.aws_kms_alias.project.target_key_arn]
  }

  statement {
    sid       = "LetTheServiceGrantItselfTheProjectKey"
    effect    = "Allow"
    actions   = ["kms:CreateGrant"]
    resources = [data.aws_kms_alias.project.target_key_arn]

    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
  }
}

# The denies particular to this role, merged into the module's ceiling: no role created, changed or
# removed, no role passed but the test project's, and no workflow deleted - the CLI's `destroy` is
# nobody's job here.
data "aws_iam_policy_document" "test_ceiling" {
  statement {
    sid    = "DenyEveryRoleChangeButPassing"
    effect = "Deny"
    actions = [
      "iam:AttachRolePolicy",
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:DeleteRolePermissionsBoundary",
      "iam:DeleteRolePolicy",
      "iam:DetachRolePolicy",
      "iam:PutRolePermissionsBoundary",
      "iam:PutRolePolicy",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:UpdateRole",
      "iam:UpdateRoleDescription",
    ]
    resources = ["*"]
  }

  statement {
    sid           = "DenyPassingAnyRoleButTheTestProjects"
    effect        = "Deny"
    actions       = ["iam:PassRole"]
    not_resources = [local.test_project_role_arn]
  }

  statement {
    sid       = "DenyDeletingAWorkflow"
    effect    = "Deny"
    actions   = ["airflow-serverless:DeleteWorkflow"]
    resources = ["*"]
  }
}
