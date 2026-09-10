# The three approver sets - Stage 2 step 5.2, from the design of record in Stage 1b step 3.5
# (D31 for the first, D22/D26 for the second, D14/INT-19 for the third).
#
# An approver who can already read everything is not exercising a control when they approve (1b
# step 3.5). These are the sets whose denials are the substance: what each may not reach is what
# makes its approval mean something. The denials need no resource to exist, so unlike the allows
# they are complete here rather than owed to a later stage (the header of
# policies-data-scientists.tf draws the line this slice takes).
#
# None of the three approval gates is an AWS permission. The deployment approval and the dev-env
# approval both live in GitLab (Stage 8), driven by GitLab group membership; the governance
# approval is a DataZone subscription decision. These sets exist for the work that happens before
# the click - diagnosing a failed promotion, judging an image, seeing who is asking for what -
# which is why reaching the data itself would defeat them.

# ============================================================================================
# DeploymentManagerAccess - Sandbox, Development, Production (D31). Nothing on Data Governance
# ============================================================================================
#
# This set replaced the AWS-managed `ReadOnlyAccess`, which on the lifecycle accounts reaches
# the D19 derived zone - where the output of a query over `restricted` data lives and, by D19's
# own classification rule, is `restricted` - and reaches athena:GetQueryResults, which returns
# other people's query output.
#
# The old arrangement looked harmless because ReadOnlyAccess grants no
# athena:StartQueryExecution and no kms:Decrypt, so it could never originate a read of the lake
# and could not decrypt an SSE-KMS object at all. The exposure was being prevented by encryption
# rather than by design, which stops being true the first time a bucket is created without a
# CMK: what looked like a control was a side effect (Lesson 5).
#
# The job is diagnosis, not reading: why did this promotion fail, and should it be released.
#
# Still owed: Stage 8 s3:GetObject on enumerated build-artifact and test-report prefixes, never
# a bucket wildcard, which is the shape that produced D31 in the first place.

data "aws_iam_policy_document" "deployment_manager" {
  # checkov:skip=CKV_AWS_356:one document, N accounts - no ARN can name the account; see the CKV_AWS_356 note in policies-data-scientists.tf
  source_policy_documents = [
    data.aws_iam_policy_document.shared_denies.json,
    data.aws_iam_policy_document.control_plane_vpn.json,
    data.aws_iam_policy_document.stage6_denies.json,
  ]

  # The CloudWatch Logs grant is the AWS managed policy CloudWatchLogsReadOnlyAccess, attached
  # in permission-sets.tf, where the argument for that choice is written once instead of four
  # times.

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
  # question of any failed promotion. Execution status, never execution.
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
  # The four denials D31 names, each closing a different route to the same place:
  #
  #   athena:*                   both originating a query over the lake and reading somebody
  #                              else's results. The whole service, because GetQueryResults is
  #                              reachable with nothing but a query execution id.
  #   kms:Decrypt                a CMK's key policy is where "who may read the copy" lives
  #                              (D31; since D19's 2026-08-26 revision the derived zone is the
  #                              SMUS project path under the project CMK - this deny is the
  #                              approver-side half that survives the re-homing, and it makes
  #                              the control apply to a principal who might otherwise be
  #                              handed s3:GetObject later).
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
# GovernanceManagerAccess - Data Governance only
# ============================================================================================
#
# The catalog, never the rows. The governance manager approves who may read data, so their own
# reach has to stop at the catalog; otherwise the approval is made by somebody who already has
# what they are approving.
#
# It is the mirror image of the set above (1b step 3.7): the one account the deployment manager
# cannot enter is the only one this persona can.
#
# Still owed: Stage 5/6 the DataZone domain ARN, so the approval actions below can be scoped to
# this organization's domain rather than to any domain in the account.

data "aws_iam_policy_document" "governance_manager" {
  # checkov:skip=CKV_AWS_356:one document, N accounts - no ARN can name the account; see the CKV_AWS_356 note in policies-data-scientists.tf
  source_policy_documents = [
    data.aws_iam_policy_document.shared_denies.json,
    data.aws_iam_policy_document.control_plane_vpn.json,
    data.aws_iam_policy_document.stage6_denies.json,
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

  # LF-tag and permission administration - the persona's actual work (D13). Not in the list:
  # lakeformation:GetDataAccess, the call that vends credentials for the underlying objects. It
  # is denied below rather than merely omitted, because it is the one action in this service
  # that turns an administrator of access into a reader of data.
  #
  # This statement on its own grants the persona nothing (recorded 2026-08-19, Stage 5 pass 2).
  # Lake Formation runs its own authorization layer on top of IAM: holding
  # lakeformation:AddLFTagsToResource here permits the API call, while whether the call succeeds
  # is decided by an LF permission - ASSOCIATE on the tag - granted in a different account, by a
  # different slice, in a different stage (terraform-live/data-governance/data/governance.tf,
  # step 6). The persona's real reach is the intersection of the two, and this file is only ever
  # one of the halves.
  #
  # The natural unit to read is a slice, and the slice is never the authorization unit. Before
  # pass 2 landed, this list read exactly as it reads now and the persona could not tag a single
  # dataset - the failure being an empty result or an access error at the moment of use, with
  # nothing here to suggest why. The trap runs in reverse too: revoking the LF grant leaves this
  # list untouched and still describing a capability that no longer exists. Verify the pair,
  # never one side (docs/plan/lessons.md, the two-authorization-systems lesson).
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

  # Domain ownership, read as the approval verbs rather than as datazone:*. A subscription
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
  # The routes from the catalog to the rows, closed by name. Each is a different service and
  # each would be enough on its own:
  #
  #   lakeformation:GetDataAccess  vends temporary credentials for the underlying S3 objects.
  #                                The set administers this mechanism; using it is the thing it
  #                                must not do.
  #   s3:Get*                      the direct route, denied whole rather than prefix-scoped:
  #                                the lake prefixes do not exist yet (Stage 5), and a
  #                                governance manager has no legitimate object read to lose. A
  #                                prefix-scoped deny written today would be a guess that fails
  #                                open.
  #   athena:*                     the query route. 1b step 3.5 says "no Athena workgroup" -
  #                                written here as the service, because a workgroup that
  #                                appears later would otherwise be reachable without anyone
  #                                revisiting this file.
  #
  # kms:Decrypt is not a fourth: with s3:Get* and GetDataAccess closed there is no object to
  # decrypt, and a fourth lock on the same door is a denial nothing will ever exercise (Lesson
  # 20 - when several policies deny the same call, only one is proven).
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
# The artifact, never the data. The steward approves the `dev-env` image - the runtime every
# notebook and every project app runs on (INT-19) - and the approval itself happens in GitLab,
# consuming no AWS permission. The set is for judging the artifact: what is in the image, what
# the scanner found, and what is actually registered as a SageMaker image.
#
# One set, three accounts, read-only in all of them (1b step 3.3). "Production plus read-only on
# Sandbox and Development" describes the assignment table; the policy itself writes nothing
# anywhere, so the distinction is carried by the content rather than by the assignment.
#
# Still owed: Stage 7 the ECR repository ARNs, so the metadata reads below can be scoped to the
# dev-env repository rather than to every repository in the account.

data "aws_iam_policy_document" "dev_env_steward" {
  # checkov:skip=CKV_AWS_356:one document, N accounts - no ARN can name the account; see the CKV_AWS_356 note in policies-data-scientists.tf
  source_policy_documents = [
    data.aws_iam_policy_document.shared_denies.json,
    data.aws_iam_policy_document.control_plane_vpn.json,
    data.aws_iam_policy_document.stage6_denies.json,
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

  # What is actually registered, a different question from what is in the registry: an approved
  # image only matters if the image/app_image_config pair pointing at it is the one Studio hands
  # out. Narrow by design - this set does not read jobs, endpoints or pipelines.
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
  # The five actions that would turn the gate into theatre (1b step 3.5, by name). The pipeline
  # holds all five and runs only after the approval, so a steward who also held them could ship
  # an image nobody reviewed, including their own.
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

  # Approving a runtime never requires reading data - the same triple as the governance manager,
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
