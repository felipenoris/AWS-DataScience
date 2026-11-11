# deploy-project.tf - Stage 19 step 4.8: what this account's deploy role calls when the pipeline's leg
# runs the CI/CD CLI's `deploy` into the account's deployment project and follows the run it starts
# (decision 6 (b)). The statements are Stage 18 step 4.3's, read from the calls the CLI 1.0.9 made as
# awsds-deploy-staging on 2026-10-21, plus the catalog import's (its helpers/catalog_import.py, read
# 2026-11-11), which that deploy did not run.
#
# One customer-managed policy the infrastructure user attaches, as apply-orchestration.tf's are: the
# role's inline documents share 10,240 characters. It exists once the project does, since every scope
# below is built from the project role's name (variables.tf).
#
# DataZone's own layer is not IAM. The role reads and writes a project's catalog as a member of it,
# an owner of the deployment project alone, added by hand once its first call has created its group
# profile. The actions below take no resource type, so membership is what confines them.
#
# The same file in staging/foundation/ and production/foundation/, byte for byte
# (./scripts/check-copies.py).

locals {
  deployment_project_enabled  = var.deployment_project_role != ""
  deployment_project_role_arn = "arn:${local.partition}:iam::${local.account_id}:role/${var.deployment_project_role}"
  # The project's id, the second segment of its role's name, datazone_usr_role_<project>_<environment>.
  deployment_project_id = try(regex("^datazone_usr_role_([a-z0-9]+)_", var.deployment_project_role)[0], "")
  # Where the CLI writes: <domain>/<project>/shared/ in the projects bucket, the application's folders
  # and operatorFiles/ under it.
  deployment_projects_bucket_arn = "arn:${local.partition}:s3:::awsds-${var.env}-smus-projects"
  deployment_shared_prefix       = "${var.datazone_domain_id}/${local.deployment_project_id}/shared/"
  deployment_workflows           = "arn:${local.partition}:airflow-serverless:${local.region_account}:workflow/*"
  deployment_log_groups          = "arn:${local.partition}:logs:${local.region_account}:log-group:/aws/mwaa-serverless/${var.datazone_domain_id}-${local.deployment_project_id}/*"
  deployment_keys                = "arn:${local.partition}:kms:${local.region_account}:key/*"
}

# IAM has no call that changes a managed policy's description: a change plans its replacement.
resource "aws_iam_policy" "deploy_project" {
  count = local.deployment_project_enabled ? 1 : 0

  name        = "awsds-${var.env}-deploy-project"
  description = "Stage 19 step 4.8 - the deploy role's CI/CD CLI deploy into the account's deployment project: the project's reads, its catalog import, its workflows, its shared prefix and its key"
  policy      = data.aws_iam_policy_document.deploy_project.json

  tags = merge(local.deploy_anchor_tags, {
    Name = "awsds-${var.env}-deploy-project"
  })
}

resource "aws_iam_role_policy_attachment" "deploy_project" {
  count = local.deployment_project_enabled ? 1 : 0

  role       = module.deploy_role.role_name
  policy_arn = aws_iam_policy.deploy_project[0].arn
}

data "aws_iam_policy_document" "deploy_project" {
  # checkov:skip=CKV_AWS_111:DataZone's project and catalog actions and ListWorkflows take no resource type, so only "*" matches them; DataZone confines them by project membership, and every other write names the project's workflows, prefix, key or log groups
  # checkov:skip=CKV_AWS_356:idem

  # The CLI resolves the domain, the project, its membership, its environments and its connections
  # before it copies anything. Without the environment and connection reads it creates the workflow in
  # the service's own network under an AWS-owned key and prints one line.
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
    resources = ["arn:${local.partition}:datazone:${var.region}:*:domain/${var.datazone_domain_id}"]
  }

  # The catalog import: what the project holds is searched and read, the bundle's assets and data
  # products are created or revised, each asset's source reference remapped to the project's data
  # source over the same database. ListPolicyGrants is the import's pre-flight on the domain unit:
  # refused, or answered with no grant of a type, the CLI calls AddPolicyGrant, which this role does
  # not hold, and aborts the import; the three grants are data-governance/governance/'s.
  statement {
    sid    = "ImportTheBundlesCatalogIntoTheProject"
    effect = "Allow"
    actions = [
      "datazone:CreateAsset",
      "datazone:CreateAssetRevision",
      "datazone:CreateAssetType",
      "datazone:CreateDataProduct",
      "datazone:CreateDataProductRevision",
      "datazone:CreateFormType",
      "datazone:CreateGlossary",
      "datazone:CreateGlossaryTerm",
      "datazone:GetAsset",
      "datazone:GetDataProduct",
      "datazone:GetDataSource",
      "datazone:GetFormType",
      "datazone:ListDataSourceRuns",
      "datazone:ListDataSources",
      "datazone:ListPolicyGrants",
      "datazone:Search",
      "datazone:SearchTypes",
      "datazone:UpdateGlossary",
      "datazone:UpdateGlossaryTerm",
    ]
    resources = ["*"]
  }

  # The workflow calls, on a workflow tagged with the project: the CLI tags the workflow at its
  # creation, and the tag scopes every later call. ListWorkflows takes no resource type.
  statement {
    sid       = "ListTheWorkflows"
    effect    = "Allow"
    actions   = ["airflow-serverless:ListWorkflows"]
    resources = ["*"]
  }

  statement {
    sid       = "CreateAWorkflowOfTheProject"
    effect    = "Allow"
    actions   = ["airflow-serverless:CreateWorkflow"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = [local.deployment_project_id]
    }
  }

  # TagResource may re-apply the project tag with the project's own value and never another's.
  statement {
    sid    = "UpdateTagRunAndReadAWorkflowOfTheProject"
    effect = "Allow"
    actions = [
      "airflow-serverless:GetTaskInstance",
      "airflow-serverless:GetWorkflow",
      "airflow-serverless:GetWorkflowRun",
      "airflow-serverless:ListTagsForResource",
      "airflow-serverless:ListTaskInstances",
      "airflow-serverless:ListWorkflowRuns",
      "airflow-serverless:ListWorkflowVersions",
      "airflow-serverless:StartWorkflowRun",
      "airflow-serverless:TagResource",
      "airflow-serverless:UpdateWorkflow",
    ]
    resources = [local.deployment_workflows]

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = [local.deployment_project_id]
    }

    condition {
      test     = "StringEqualsIfExists"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = [local.deployment_project_id]
    }
  }

  # CreateWorkflow and UpdateWorkflow pass the project role to the service the workflow runs as.
  statement {
    sid       = "PassTheProjectRoleToTheService"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = [local.deployment_project_role_arn]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["airflow-serverless.amazonaws.com"]
    }
  }

  # The workflow's log group, created in the caller's session at the workflow's creation; an update
  # meets it and lists the account's groups (sandbox/workflows/deploy-role.tf, measured 2026-10-19).
  statement {
    sid       = "CreateAndReadTheWorkflowsLogGroup"
    effect    = "Allow"
    actions   = ["logs:CreateLogGroup", "logs:FilterLogEvents", "logs:GetLogEvents"]
    resources = [local.deployment_log_groups]
  }

  statement {
    sid       = "DescribeTheLogGroupsOnUpdate"
    effect    = "Allow"
    actions   = ["logs:DescribeLogGroups"]
    resources = ["arn:${local.partition}:logs:${local.region_account}:log-group:*"]
  }

  # The project's shared/ prefix in the projects bucket, and the project key it encrypts under, named
  # by its alias so that no key is looked up: the data keys of the uploads, the reads and the run's
  # start, and the grants the service creates on the caller's behalf at the workflow's creation.
  statement {
    sid       = "ListTheProjectsSharedPrefix"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [local.deployment_projects_bucket_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${local.deployment_shared_prefix}*"]
    }
  }

  statement {
    sid       = "ReadAndWriteUnderTheProjectsSharedPrefix"
    effect    = "Allow"
    actions   = ["s3:AbortMultipartUpload", "s3:GetObject", "s3:PutObject"]
    resources = ["${local.deployment_projects_bucket_arn}/${local.deployment_shared_prefix}*"]
  }

  statement {
    sid       = "UseTheProjectKey"
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:DescribeKey", "kms:GenerateDataKey"]
    resources = [local.deployment_keys]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = ["alias/awsds-${var.env}-project"]
    }
  }

  statement {
    sid       = "LetTheServiceGrantItselfTheProjectKey"
    effect    = "Allow"
    actions   = ["kms:CreateGrant"]
    resources = [local.deployment_keys]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = ["alias/awsds-${var.env}-project"]
    }

    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
  }
}
