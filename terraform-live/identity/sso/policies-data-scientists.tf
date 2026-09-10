# The three data scientist sets - Stage 2 step 5.2, from the design of record in Stage 1b
# steps 3.4 and 3.6 (D18, D20, D21). That step specifies them; this file does not restate it.
#
# ============================================================================================
# The line this file draws, and it applies to every persona policy in the slice
# ============================================================================================
#
# These sets are written five stages before the resources they will govern. So:
#
#   granted now - every action whose resource is the service or the account: catalog metadata,
#                 job and pipeline status, log reads, registry discovery. These are complete
#                 and are not placeholders.
#   denied now  - everything the design denies. The denials are the durable half (1b step 3.5
#                 says so for the approvers) and none of them needs a resource to exist: they
#                 are about actions.
#   not granted - every action scoped to an object that does not exist yet: the Studio domains
#                 (Stage 6), the ECR repositories (Stage 7), Production's own workgroup and
#                 output prefixes (Stage 9). Each is named below against the stage that owes
#                 it. Two entries left this list at Stage 5 pass 4c and the per-set ledgers
#                 below say how - the derived zone and the two enforced workgroups as
#                 deliveries, the lake prefixes as a correction (never owed).
#
# They are not written from the naming convention instead, because that would be a guess at an
# interface, which this stage already refuses to make for a module (step 7's reordering note:
# "writing and tagging a module before any caller exists is guessing at an interface"). A
# bucket named by guess produces an allow that matches nothing today - deny-by-typo, invisible
# in a plan - or, worse, an allow carrying an `awsds-*` wildcard, which in an S3 ARN means any
# bucket of that shape on earth, since bucket names are global. The deny fragment uses exactly
# that wildcard, and it is safe there for the reason that makes it unsafe here.
#
# Nothing signs in before Stage 6 (1b step 3.9), so no persona is blocked by this. What the
# stage delivers is the object, its name, its denials and its assignment - reviewable, with a
# diff and a rollback.
#
# ============================================================================================
# CKV_AWS_356 is suppressed in all six documents, for the same reason (step 6.5: decide the
# suppressions, do not discover them). It fires on `Resource: "*"` in an allow.
# ============================================================================================
#
# The ARN cannot be narrowed here. A permission set is one document provisioned into many
# accounts, so every ARN it could write would have to leave the account field a wildcard - the
# form step 9.2 refuses outright, and refuses for a stronger reason than checkov's: a
# wildcard-account ARN in an allow reaches a resource anybody can create. Taking checkov's
# advice literally would produce a worse policy than ignoring it, which is the one case where a
# gate has to be answered rather than obeyed.
#
# The statements are metadata and status reads - catalog descriptions, job and pipeline state,
# log events, registry listings. Not one of them returns a row of lake data; the calls that do
# are either denied by name or absent, and both halves are written out per set below.
#
# What contains them is not the ARN, which is D19's argument one layer up: reaching another
# account's Glue catalog needs that account to allow it, and the organization's RCP perimeter
# denies access from outside the organization altogether (1c step 7.8). The perimeter is the
# containment; the resource list never was.
#
# The narrowing that is available is a condition rather than a resource - `aws:ResourceAccount`
# equal to the caller's own account - and it is not taken yet, for two reasons. Several of these
# services do not populate that key at all (ecr:GetAuthorizationToken has no resource), so it
# would have to be the `IfExists` form, and a condition that silently denies every call is the
# failure 5.1 hit with `StringEquals`, one layer down and with nobody signed in to notice. It is
# added at Stage 6, where a real sign-in can measure it, and it is recorded here so that "not
# done" and "not thought of" stay distinguishable.

# ============================================================================================
# DataScientistAccess - Sandbox and Development (D21)
# ============================================================================================
#
# 1b step 3.4: not PowerUserAccess and not AmazonSageMakerFullAccess. The second is the one
# that looks safe and is not - it grants s3:* on any bucket with "sagemaker" in the name, plus
# a broad iam:PassRole, which is the privilege-escalation pair the IAM rules exist to prevent.
#
# Delivered at Stage 5 pass 4c (2026-08-19), with one line of the old ledger corrected rather
# than delivered: the set runs queries in the two enforced workgroups, reads and writes the
# derived zone's three prefix families, and holds the identity half of the drop-box write -
# every ARN read from the consumer and lake slices' state (data.tf), which is what the "not
# granted" rule above was waiting for. The old ledger also owed "s3:GetObject on the governed
# lake through the Lake Formation share"; no such grant will ever arrive. D13 is only real
# because tabular access goes through LF-aware engines vending credentials
# (lakeformation:GetDataAccess, granted below), and a direct s3:GetObject on a registered
# prefix is the bypass D13 exists to exclude. That line was Stage 2 guessing at Stage 5's
# interface - this file's own warning, caught by delivery.
#
# Still owed, and by whom:
#   Stage 6  SageMaker Studio use against the blueprint-provisioned domain, including
#            sagemaker:CreatePresignedDomainUrl scoped to that domain, and the iam:PassRole
#            that goes with job submission - scoped by iam:PassedToService and by role ARN
#   Stage 7  ecr pull on the dev-env repository in Production (D14)

data "aws_iam_policy_document" "data_scientist" {
  # checkov:skip=CKV_AWS_356:one document, N accounts - no ARN can name the account; see the CKV_AWS_356 note in policies-data-scientists.tf
  source_policy_documents = [
    data.aws_iam_policy_document.shared_denies.json,
    data.aws_iam_policy_document.control_plane_vpn.json,
    data.aws_iam_policy_document.stage6_denies.json,
  ]

  # Reading the catalog is not reading the data. Lake Formation is the entitlement mechanism
  # (D13) and it is enforced at the moment of data access, so metadata read here is
  # subordinate to it rather than a way around it.
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

  # The read side of Lake Formation: what tags exist, what they cover, and the credential
  # vending call itself. Granting is not here and is denied below - a data scientist is never
  # the grantor (1b step 3.7, and it is the whole of GovernanceManagerAccess).
  statement {
    sid    = "ReadThroughLakeFormation"
    effect = "Allow"

    actions = [
      "lakeformation:GetDataAccess",
      "lakeformation:GetLFTag",
      "lakeformation:GetResourceLFTags",
      "lakeformation:ListLFTags",
      "lakeformation:SearchDatabasesByLFTags",
      "lakeformation:SearchTablesByLFTags",
    ]

    resources = ["*"]
  }

  # ------------------------------------------------------------------------------------------
  # Six statements left this document on 2026-08-26, and the absence is the design (D19 as
  # revised that day - the derived zone re-homed onto the SMUS project path, awsds-<env>-derived
  # and the enforced workgroups removed):
  #
  #   DiscoverAthenaWorkgroupsAndTables, RunQueriesInTheEnforcedWorkgroups - the persona's
  #   direct Athena path. Its result home was the derived zone; with the zone gone the grant
  #   would pin output nowhere, which is the one thing D19 practice (i) refused. A data
  #   scientist queries through a SMUS project - the project's own enforced workgroup, under
  #   the project role, into the project path - so the query surface moved from the persona to
  #   the project, and this document carries no athena: action at all.
  #
  #   UseDerivedZoneBuckets, ReadDerivedZoneObjects, WriteDerivedZonePrefixes,
  #   DeleteScratchObjects - the three prefix families of the removed bucket. The working-file
  #   role of scratch/ is the project path's shared/ scope (mounted in JupyterLab); the
  #   results role is dev/sys/athena/ under the project workgroup; per-principal write has no
  #   analog there (the path has no person grain - attribution is Stage 11's data events).
  #
  # What stayed, because it is the ingestion path and not the query path: the drop-box write
  # below and its lake-key KMS half. The LF read (ReadThroughLakeFormation above) also stays -
  # it is what a SMUS subscription rides and what catalog visibility needs.

  # ------------------------------------------------------------------------------------------
  # The drop-box write - the identity half of a cross-account permission (D18, D25; Stage 5
  # pass 4c). The resource half has existed since pass 1: the drop-box bucket policy's
  # AllowInteractiveWriterPutOnly and the lake data-key policy's AllowDropBoxWritersViaS3, both
  # reaching this role through the Interactive account roots. Cross-account evaluation requires
  # both policies to allow - the fact stage 6.2's reading missed when it called this statement's
  # absence "correct rather than missing" (corrected 2026-08-19, in the stage file). The
  # statement mirrors the bucket policy's asymmetry exactly: PutObject only, the dated prefix
  # only - no read-back, no list, no delete, and no multipart-abort because the resource side
  # grants none.
  #
  # Exercised 2026-08-20 (Stage 5 pass 4d), and the write is asymmetric in three verbs, not
  # one: the persona's PutObject into the dated prefix succeeds, while GetObject on the object
  # it just wrote, ListObjectsV2 on the prefix and DeleteObject on its own object are each
  # denied implicitly - absence of grant, no deny statement involved. The delete probe completes
  # the claim: a writer that can retract is a writer that can launder, which is the exchange
  # bucket D18 refuses. Two consequences for anyone editing this statement:
  #   - the missing multipart-abort is load-bearing on the caller's side too. A stdin stream of
  #     unknown length goes multipart, and this statement does not cover it, so a probe written
  #     that way fails for a reason that is not the one under test. Write a fixed-size file.
  #   - the write needs three allows, not two - this statement, the bucket policy, and the lake
  #     CMK's key policy meeting the UseLakeDataKeyViaS3 block below. The third is invisible on
  #     failure (it surfaces as a KMS error about an action nobody wrote here) and legible only
  #     in a successful PutObject's SSEKMSKeyId. Lesson 28, amended by this proof.
  statement {
    sid    = "WriteIngestionDropBox"
    effect = "Allow"

    actions = ["s3:PutObject"]

    resources = [local.lake_dropbox_write_arn]
  }

  # The KMS half of the same write, and only via S3: SSE-KMS PutObject needs GenerateDataKey,
  # a multipart upload needs Decrypt (the lake slice's README row says why), and ViaService
  # keeps this role away from the lake key outside an S3 call - the same condition the key
  # policy itself carries, each side scoping the other.
  statement {
    sid    = "UseLakeDataKeyViaS3"
    effect = "Allow"

    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
    ]

    resources = [local.lake_data_key_arn]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["s3.${var.region}.amazonaws.com"]
    }
  }

  # ------------------------------------------------------------------------------------------
  # The project-storage vending handshake is not here, and its absence is the delivery (user
  # decision of 2026-08-23, strategy 1-A; consumer: `s3-read-write/`). It is a customer-managed
  # policy - `var.persona_vending_policy_name`, created by each member's foundation/ and
  # referenced in permission-sets.tf - because this document had 23 characters of headroom
  # against the size precondition and the statement costs ~251. The README's size discipline says
  # the answer is a customer-managed policy rather than a larger threshold, and the threshold is
  # the IAM inline-role limit this set becomes in every account it reaches. What the statement
  # says, and why it opens nothing, is argued once - in
  # terraform-live/<member>/foundation/persona-vending.tf, beside the object itself.

  # Status of the work, in the account the work runs in. Describe/List only - every verb that
  # creates, changes or stops anything is denied below.
  statement {
    sid    = "ReadSageMakerStatus"
    effect = "Allow"

    actions = [
      "sagemaker:Describe*",
      "sagemaker:GetSearchSuggestions",
      "sagemaker:List*",
      "sagemaker:Search",
    ]

    resources = ["*"]
  }

  # The registry handshake and nothing else. GetAuthorizationToken is account-scoped by the
  # caller and cannot be narrowed by resource - it hands back a token for the registries the
  # caller already has access to, so it opens nothing on its own. The pull it precedes is a
  # repository-scoped grant and arrives with Stage 7.
  statement {
    sid    = "AuthenticateToEcr"
    effect = "Allow"

    actions = ["ecr:GetAuthorizationToken"]

    resources = ["*"]
  }

  # The CloudWatch Logs grant is the AWS managed policy CloudWatchLogsReadOnlyAccess, attached
  # in permission-sets.tf, where the argument for that choice is written once instead of four
  # times.

  # The grantor is somebody else, and that separation is the point (1b step 3.7). A principal
  # that can grant itself a Lake Formation permission has an entitlement mechanism that
  # entitles nothing. Written as a Deny rather than left to omission because Stage 5 grants
  # this set real lake access, and the grant and the granting sit in the same service.
  statement {
    sid    = "DenyLakeFormationAdministration"
    effect = "Deny"

    actions = [
      "lakeformation:AddLFTagsToResource",
      "lakeformation:CreateLFTag",
      "lakeformation:DeleteLFTag",
      "lakeformation:DeregisterResource",
      "lakeformation:GrantPermissions",
      "lakeformation:PutDataLakeSettings",
      "lakeformation:RegisterResource",
      "lakeformation:RemoveLFTagsFromResource",
      "lakeformation:RevokePermissions",
      "lakeformation:UpdateLFTag",
    ]

    resources = ["*"]
  }
}

# ============================================================================================
# DataScientistStagingAccess - Staging (D20)
# ============================================================================================
#
# Read-only, with no write of any kind, not even a drop-box (1b step 3.6). Staging exists to be
# written by the pipeline and read by a human working out why the pipeline failed, and a staging
# environment a person can write to has stopped being evidence of what the pipeline actually
# does.
#
# Not assigned yet. The Staging account is unvended (step 3.2, held on the account cap), so
# locals.tf carries no Staging row. The set is created anyway - it costs nothing, and having it
# reviewed now rather than typed at the vend is why six sets are written in code at all.
#
# Nothing is owed to this set. Stage 9 step 5.2 verifies it by reading - no Athena,
# DenyEveryWrite intact, nothing added. The only thing still coming to this document is the
# Stage 3 permissions boundary, owed to all six sets rather than to this one; README.md carries
# the owed table. "Stage 5 s3:GetObject on Staging's own prefixes" is not owed: Stage 5's
# consumers are Sandbox and Development only (backend.py), and a staging environment a human can
# read through IAM rather than through the pipeline's path is the first step back to one a human
# can write.

data "aws_iam_policy_document" "data_scientist_staging" {
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
      "glue:GetTable",
      "glue:GetTableVersions",
      "glue:GetTables",
      "glue:SearchTables",
    ]

    resources = ["*"]
  }

  statement {
    sid    = "ReadSageMakerStatus"
    effect = "Allow"

    actions = [
      "sagemaker:Describe*",
      "sagemaker:List*",
      "sagemaker:Search",
    ]

    resources = ["*"]
  }

  # The CloudWatch Logs grant is the AWS managed policy CloudWatchLogsReadOnlyAccess, attached
  # in permission-sets.tf, where the argument for that choice is written once instead of four
  # times.

  # No Athena at all, and it is a write question rather than a read one. A query writes its
  # result to S3; there is no read-only Athena. So this set does not even discover workgroups,
  # and athena:StartQueryExecution is denied below along with everything else that puts a byte
  # anywhere.

  # ---------------------------------------------------------------------------------------
  # "No write of any kind", written so it can be maintained. Enumerating every write action in
  # AWS is a list that is wrong the week after it is written, so this is bound to a rule
  # instead: it names the write families of exactly the services this set grants anything in,
  # plus athena, which it grants nothing in.
  #
  # The rule, for whoever adds an allow later: a service added to the statements above gets its
  # write family added here in the same diff. That is a reviewable invariant - "the services in
  # the allows and the services in this deny are the same set" - where a bare enumeration is
  # only ever a snapshot of somebody's attention.
  statement {
    sid    = "DenyEveryWrite"
    effect = "Deny"

    actions = [
      "athena:Create*",
      "athena:Delete*",
      "athena:Start*",
      "athena:Update*",
      "glue:Create*",
      "glue:Delete*",
      "glue:Put*",
      "glue:Start*",
      "glue:Update*",
      "lakeformation:Grant*",
      "lakeformation:Put*",
      "lakeformation:Revoke*",
      "lakeformation:Update*",
      "logs:Create*",
      "logs:Delete*",
      "logs:Put*",
      "s3:Delete*",
      "s3:Put*",
      "s3:Restore*",
      "sagemaker:Create*",
      "sagemaker:Delete*",
      "sagemaker:Start*",
      "sagemaker:Stop*",
      "sagemaker:Update*",
    ]

    resources = ["*"]
  }
}

# ============================================================================================
# DataScientistProdAccess - Production (D18)
# ============================================================================================
#
# A different shape, not a weaker copy (1b step 3.6): data plane read, no compute, no control
# plane. GitLab and ECR access (D14) folds into this set rather than living as a separate
# grant. The ingestion drop-box is not here - it moved to Data Governance with the lake (D22)
# and is granted by bucket policy to the Interactive-OU roles, not by a permission set.
#
# Still owed: Stage 9 s3:GetObject on the named application-output prefixes and
# athena:StartQueryExecution on the dedicated Production workgroup (its step 5.1) - Production
# only joins DATA_CONSUMERS at Stage 9 (backend.py), so Stage 5 could not have written these
# ARNs; Stage 7 ecr pull.

data "aws_iam_policy_document" "data_scientist_prod" {
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
      "glue:GetTable",
      "glue:GetTableVersions",
      "glue:GetTables",
      "glue:SearchTables",
    ]

    resources = ["*"]
  }

  # Status, which is what the model registry is read for here. Describe and List reach model
  # packages, pipelines and their executions; nothing below creates or advances one.
  statement {
    sid    = "ReadSageMakerStatus"
    effect = "Allow"

    actions = [
      "sagemaker:Describe*",
      "sagemaker:List*",
      "sagemaker:Search",
    ]

    resources = ["*"]
  }

  # The CloudWatch Logs grant is the AWS managed policy CloudWatchLogsReadOnlyAccess, attached
  # in permission-sets.tf, where the argument for that choice is written once instead of four
  # times.

  # D14's ECR half: which image is deployed, and what its scan says. The pull itself is
  # repository-scoped and arrives at Stage 7.
  statement {
    sid    = "ReadEcrImageMetadata"
    effect = "Allow"

    actions = [
      "ecr:DescribeImageScanFindings",
      "ecr:DescribeImages",
      "ecr:DescribeRepositories",
      "ecr:GetAuthorizationToken",
      "ecr:ListImages",
    ]

    resources = ["*"]
  }

  statement {
    sid    = "DiscoverAthenaWorkgroupsAndTables"
    effect = "Allow"

    actions = [
      "athena:GetDataCatalog",
      "athena:GetTableMetadata",
      "athena:GetWorkGroup",
      "athena:ListDataCatalogs",
      "athena:ListDatabases",
      "athena:ListTableMetadata",
      "athena:ListWorkGroups",
    ]

    resources = ["*"]
  }

  # ---------------------------------------------------------------------------------------
  # 1b step 3.6 names four actions to deny explicitly, and each falls inside one of the
  # families below, so a reader searching for one of the four finds it:
  #
  #   sagemaker:Create*Job              -> sagemaker:Create*   (no compute in Production)
  #   sagemaker:CreatePresignedDomainUrl-> sagemaker:Create*   (there is no domain here - D17)
  #   glue:StartJobRun                  -> glue:Start*
  #   lakeformation:GrantPermissions    -> lakeformation:Grant*
  #
  # The families rather than the four names, because the four are examples of a rule - "no
  # control plane in Production for a human" - and a deny list that stops exactly at the
  # examples is one new API call away from being wrong.
  statement {
    sid    = "DenyProductionControlPlane"
    effect = "Deny"

    actions = [
      "athena:Create*",
      "athena:Delete*",
      "athena:Update*",
      "glue:Create*",
      "glue:Delete*",
      "glue:Put*",
      "glue:Start*",
      "glue:Update*",
      "lakeformation:Grant*",
      "lakeformation:Put*",
      "lakeformation:Revoke*",
      "lakeformation:Update*",
      "sagemaker:Create*",
      "sagemaker:Delete*",
      "sagemaker:Start*",
      "sagemaker:Stop*",
      "sagemaker:Update*",
    ]

    resources = ["*"]
  }
}
