# The three approver sets - Stage 2 step 5.2, from the design of record in Stage 1b step 3.5
# (D31 for the first, D22/D26 for the second, D14/INT-19 for the third).
#
# ALL THREE ARE APPROVERS, AND AN APPROVER WHO CAN ALREADY READ EVERYTHING IS NOT EXERCISING A
# CONTROL WHEN THEY APPROVE. That sentence is 1b step 3.5's, and it is why these three sets are
# the ones whose DENIALS are the substance: what each may not reach is what makes its approval
# mean something. The denials need no resource to exist, so unlike the allows they are complete
# here rather than owed to a later stage (see the header of policies-data-scientists.tf for
# the line this slice draws).
#
# NONE OF THE THREE APPROVAL GATES IS AN AWS PERMISSION. The deployment approval and the
# dev-env approval both live in GitLab (Stage 8), driven by GitLab group membership; the
# governance approval is a DataZone subscription decision. These sets exist for the work that
# happens BEFORE the click - diagnosing a failed promotion, judging an image, seeing who is
# asking for what - which is exactly why reaching the data itself would defeat them.

# ============================================================================================
# DeploymentManagerAccess - Sandbox, Development, Production (D31). NOTHING on Data Governance
# ============================================================================================
#
# WHAT THIS SET REPLACED, because the replacement is the decision. It used to be the AWS-managed
# `ReadOnlyAccess`, which on the lifecycle accounts reaches the D19 derived zones - where the
# output of a query over `restricted` data lives and, by D19's own classification rule, IS
# `restricted` - and reaches athena:GetQueryResults, which returns other people's query output.
#
# ONE PRECISION WORTH CARRYING, because it is why the old arrangement looked harmless:
# ReadOnlyAccess grants no athena:StartQueryExecution and no kms:Decrypt, so it could never
# ORIGINATE a read of the lake and could not decrypt an SSE-KMS object at all. The exposure was
# being prevented by ENCRYPTION rather than by design - which stops being true the first time a
# bucket is created without a CMK. That is Lesson 5 from the other side: what looked like a
# control was a side effect.
#
# THE JOB IS DIAGNOSIS, NOT READING: why did this promotion fail, and should it be released.
#
# STILL OWED: Stage 8 s3:GetObject on ENUMERATED build-artifact and test-report prefixes -
# never a bucket wildcard, which is the shape that produced D31 in the first place.

data "aws_iam_policy_document" "deployment_manager" {
  # checkov:skip=CKV_AWS_356:one document, N accounts - no ARN can name the account; see the CKV_AWS_356 note in policies-data-scientists.tf
  source_policy_documents = [
    data.aws_iam_policy_document.shared_denies.json,
    data.aws_iam_policy_document.control_plane_vpn.json,
  ]

  # THE CLOUDWATCH LOGS GRANT IS NOT HERE ANY MORE (2026-08-17). It is the AWS managed policy
  # CloudWatchLogsReadOnlyAccess, attached in permission-sets.tf, where the whole argument for
  # that choice is written once instead of four times.

  statement {
    sid    = "ReadSageMakerJobAndRegistryStatus"
    effect = "Allow"

    actions = [
      "sagemaker:Describe*",
      "sagemaker:List*",
      "sagemaker:Search",
    ]

    resources = ["*"]
  }

  statement {
    sid    = "ReadGlueCatalogMetadata"
    effect = "Allow"

    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTableVersions",
      "glue:GetTables",
      "glue:SearchTables",
    ]

    resources = ["*"]
  }

  statement {
    sid    = "ReadEcrImageMetadataAndScanFindings"
    effect = "Allow"

    actions = [
      "ecr:DescribeImageScanFindings",
      "ecr:DescribeImages",
      "ecr:DescribeRepositories",
      "ecr:ListImages",
    ]

    resources = ["*"]
  }

  # D7's two orchestration designs both land here: the native one is Step Functions plus
  # EventBridge Scheduler, and "did the schedule fire and did the machine finish" is the first
  # question of any failed promotion. EXECUTION STATUS, never execution.
  statement {
    sid    = "ReadOrchestrationExecutionStatus"
    effect = "Allow"

    actions = [
      "scheduler:GetSchedule",
      "scheduler:GetScheduleGroup",
      "scheduler:ListScheduleGroups",
      "scheduler:ListSchedules",
      "states:DescribeExecution",
      "states:DescribeStateMachine",
      "states:GetExecutionHistory",
      "states:ListExecutions",
      "states:ListStateMachines",
    ]

    resources = ["*"]
  }

  # ---------------------------------------------------------------------------------------
  # THE FOUR DENIALS D31 NAMES, AND EACH CLOSES A DIFFERENT ROUTE TO THE SAME PLACE.
  #
  #   athena:*                   both ORIGINATING a query over the lake and reading somebody
  #                              else's results. The whole service, because GetQueryResults is
  #                              reachable with nothing but a query execution id.
  #   kms:Decrypt                the derived zone's CMK is the read control (D19 practice vi,
  #                              added by D31). This is what makes that control apply to a
  #                              principal who might otherwise be handed s3:GetObject later.
  #   secretsmanager:GetSecretValue,
  #   ssm:GetParameter*          a promotion's secrets are not diagnostic material, and both
  #                              are the standard route from "read-only" to "credentialed".
  #
  # The Terraform state buckets are the fifth and they are in the shared fragment, because they
  # are denied to all six.
  statement {
    sid    = "DenyDataReadPaths"
    effect = "Deny"

    actions = [
      "athena:*",
      "kms:Decrypt",
      "secretsmanager:GetSecretValue",
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
    ]

    resources = ["*"]
  }

  # "The control plane in full" - the release approver diagnoses and approves; the pipeline
  # acts. A principal that can both approve a release and perform one is a gate with a bypass
  # built in.
  statement {
    sid    = "DenyControlPlaneInFull"
    effect = "Deny"

    actions = [
      "ecr:BatchDeleteImage",
      "ecr:PutImage",
      "glue:Create*",
      "glue:Delete*",
      "glue:Start*",
      "glue:Update*",
      "lakeformation:Grant*",
      "lakeformation:Put*",
      "lakeformation:Revoke*",
      "sagemaker:Create*",
      "sagemaker:Delete*",
      "sagemaker:Start*",
      "sagemaker:Stop*",
      "sagemaker:Update*",
      "scheduler:Create*",
      "scheduler:Delete*",
      "scheduler:Update*",
      "states:Delete*",
      "states:StartExecution",
      "states:StartSyncExecution",
      "states:StopExecution",
      "states:Update*",
    ]

    resources = ["*"]
  }
}

# ============================================================================================
# GovernanceManagerAccess - Data Governance ONLY
# ============================================================================================
#
# THE CATALOG, NEVER THE ROWS. The governance manager approves WHO MAY READ DATA, so their own
# reach has to stop at the catalog - otherwise the approval is being made by somebody who
# already has what they are approving.
#
# IT IS THE MIRROR IMAGE OF THE SET ABOVE (1b step 3.7): the one account the deployment manager
# cannot enter is the only one this persona can.
#
# STILL OWED: Stage 5/6 the DataZone domain ARN, so the approval actions below can be scoped to
# THIS organization's domain rather than to any domain in the account.

data "aws_iam_policy_document" "governance_manager" {
  # checkov:skip=CKV_AWS_356:one document, N accounts - no ARN can name the account; see the CKV_AWS_356 note in policies-data-scientists.tf
  source_policy_documents = [
    data.aws_iam_policy_document.shared_denies.json,
    data.aws_iam_policy_document.control_plane_vpn.json,
  ]

  statement {
    sid    = "ReadGlueCatalogMetadata"
    effect = "Allow"

    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetPartition",
      "glue:GetPartitions",
      "glue:GetSchema",
      "glue:GetSchemaVersion",
      "glue:GetTable",
      "glue:GetTableVersions",
      "glue:GetTables",
      "glue:SearchTables",
    ]

    resources = ["*"]
  }

  # LF-TAG AND PERMISSION ADMINISTRATION - this is the persona's actual work (D13). Note what
  # is NOT in the list: lakeformation:GetDataAccess, the call that vends credentials for the
  # underlying objects. It is denied below rather than merely omitted, because it is the one
  # action in this service that turns an administrator of access into a reader of data.
  statement {
    sid    = "AdministerLakeFormation"
    effect = "Allow"

    actions = [
      "lakeformation:AddLFTagsToResource",
      "lakeformation:BatchGrantPermissions",
      "lakeformation:BatchRevokePermissions",
      "lakeformation:CreateLFTag",
      "lakeformation:DeleteLFTag",
      "lakeformation:DescribeResource",
      "lakeformation:GetDataLakeSettings",
      "lakeformation:GetLFTag",
      "lakeformation:GetResourceLFTags",
      "lakeformation:GrantPermissions",
      "lakeformation:ListLFTags",
      "lakeformation:ListPermissions",
      "lakeformation:ListResources",
      "lakeformation:RemoveLFTagsFromResource",
      "lakeformation:RevokePermissions",
      "lakeformation:SearchDatabasesByLFTags",
      "lakeformation:SearchTablesByLFTags",
      "lakeformation:UpdateLFTag",
    ]

    resources = ["*"]
  }

  # DOMAIN OWNERSHIP, READ AS THE APPROVAL VERBS RATHER THAN AS datazone:*. A subscription
  # request is the DataZone shape of "may I read this", and accepting or rejecting one is the
  # governance manager's decision. Everything else in the service is read.
  statement {
    sid    = "OwnTheDataZoneDomain"
    effect = "Allow"

    actions = [
      "datazone:AcceptSubscriptionRequest",
      "datazone:CreateProjectMembership",
      "datazone:DeleteProjectMembership",
      "datazone:Get*",
      "datazone:List*",
      "datazone:RejectSubscriptionRequest",
      "datazone:RevokeSubscription",
      "datazone:Search*",
      "datazone:UpdateSubscriptionGrantStatus",
      "datazone:UpdateSubscriptionRequest",
    ]

    resources = ["*"]
  }

  # Macie is a Stage 11 instrument and this is its consumer: findings say where sensitive data
  # actually accumulated, which is the input to a tagging decision. Findings, never objects.
  statement {
    sid    = "ReadMacieFindings"
    effect = "Allow"

    actions = [
      "macie2:DescribeBuckets",
      "macie2:DescribeClassificationJob",
      "macie2:GetFindingStatistics",
      "macie2:GetFindings",
      "macie2:ListClassificationJobs",
      "macie2:ListFindings",
    ]

    resources = ["*"]
  }

  # ---------------------------------------------------------------------------------------
  # THE THREE ROUTES FROM THE CATALOG TO THE ROWS, CLOSED BY NAME. Each is a different service
  # and each would be enough on its own:
  #
  #   lakeformation:GetDataAccess  vends temporary credentials for the underlying S3 objects.
  #                                The set ADMINISTERS this mechanism; using it is the thing it
  #                                must not do.
  #   s3:Get*                      the direct route, and it is denied whole rather than
  #                                prefix-scoped: the lake prefixes do not exist yet (Stage 5),
  #                                and a governance manager has no legitimate object read to
  #                                lose. A prefix-scoped deny written today would be a guess
  #                                that fails open.
  #   athena:*                     the query route. 1b step 3.5 says "no Athena workgroup" -
  #                                written here as the service, because a workgroup that
  #                                appears later would otherwise be reachable without anyone
  #                                revisiting this file.
  #
  # kms:Decrypt is deliberately NOT a fourth: with s3:Get* and GetDataAccess closed there is no
  # object to decrypt, and a fourth lock on the same door is a denial nothing will ever
  # exercise (Lesson 20 - when several policies deny the same call, only one is proven).
  statement {
    sid    = "DenyReadingTheRows"
    effect = "Deny"

    actions = [
      "athena:*",
      "lakeformation:GetDataAccess",
      "s3:Get*",
    ]

    resources = ["*"]
  }
}

# ============================================================================================
# DevEnvStewardAccess - Production, Sandbox and Development
# ============================================================================================
#
# THE ARTIFACT, NEVER THE DATA. The steward approves the `dev-env` image - the runtime every
# notebook and every project app runs on (INT-19) - and the approval itself happens in GitLab,
# consuming no AWS permission. What the set is for is JUDGING the artifact: what is in the
# image, what the scanner found, and what is actually registered as a SageMaker image.
#
# ONE SET, THREE ACCOUNTS, AND IT IS READ-ONLY IN ALL OF THEM (1b step 3.3). "Production plus
# read-only on Sandbox and Development" describes the assignment table; the policy itself
# writes nothing anywhere, so the distinction is carried by the content rather than by the
# assignment.
#
# STILL OWED: Stage 7 the ECR repository ARNs, so the metadata reads below can be scoped to the
# dev-env repository rather than to every repository in the account.

data "aws_iam_policy_document" "dev_env_steward" {
  # checkov:skip=CKV_AWS_356:one document, N accounts - no ARN can name the account; see the CKV_AWS_356 note in policies-data-scientists.tf
  source_policy_documents = [
    data.aws_iam_policy_document.shared_denies.json,
    data.aws_iam_policy_document.control_plane_vpn.json,
  ]

  statement {
    sid    = "ReadEcrImageMetadataAndScanFindings"
    effect = "Allow"

    actions = [
      "ecr:DescribeImageScanFindings",
      "ecr:DescribeImages",
      "ecr:DescribeRegistry",
      "ecr:DescribeRepositories",
      "ecr:GetRegistryScanningConfiguration",
      "ecr:ListImages",
      "ecr:ListTagsForResource",
    ]

    resources = ["*"]
  }

  # The build pipeline's own logs: what the image build did, not what a job using it read.
  statement {
    sid    = "ReadBuildPipelineLogs"
    effect = "Allow"

    actions = [
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:FilterLogEvents",
      "logs:GetLogEvents",
    ]

    resources = ["*"]
  }

  # WHAT IS ACTUALLY REGISTERED, which is a different question from what is in the registry: an
  # approved image only matters if the image/app_image_config pair pointing at it is the one
  # Studio hands out. Narrow on purpose - this set does not read jobs, endpoints or pipelines.
  statement {
    sid    = "ReadSageMakerImageRegistration"
    effect = "Allow"

    actions = [
      "sagemaker:DescribeAppImageConfig",
      "sagemaker:DescribeImage",
      "sagemaker:DescribeImageVersion",
      "sagemaker:ListAppImageConfigs",
      "sagemaker:ListImageVersions",
      "sagemaker:ListImages",
    ]

    resources = ["*"]
  }

  # ---------------------------------------------------------------------------------------
  # THE FIVE ACTIONS THAT WOULD TURN THE GATE INTO THEATRE (1b step 3.5, by name). The pipeline
  # holds all five and runs only AFTER the approval - so a steward who also held them could
  # ship an image nobody reviewed, including their own.
  statement {
    sid    = "DenyShippingTheArtifactItApproves"
    effect = "Deny"

    actions = [
      "ecr:BatchDeleteImage",
      "ecr:CompleteLayerUpload",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
      "sagemaker:CreateAppImageConfig",
      "sagemaker:CreateImage",
      "sagemaker:CreateImageVersion",
      "sagemaker:DeleteImage",
      "sagemaker:DeleteImageVersion",
      "sagemaker:UpdateAppImageConfig",
      "sagemaker:UpdateImage",
    ]

    resources = ["*"]
  }

  # APPROVING A RUNTIME NEVER REQUIRES READING DATA - the same triple as the governance manager,
  # for a different reason: there the persona administers access, here the persona has no
  # relationship with the data at all. It is the narrowest of the three approver sets, because
  # what it judges is a container image and not an environment.
  statement {
    sid    = "DenyReadingData"
    effect = "Deny"

    actions = [
      "athena:*",
      "kms:Decrypt",
      "lakeformation:GetDataAccess",
      "s3:Get*",
    ]

    resources = ["*"]
  }
}
