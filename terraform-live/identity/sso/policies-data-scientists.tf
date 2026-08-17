# The three data scientist sets - Stage 2 step 5.2, from the design of record in Stage 1b
# steps 3.4 and 3.6 (D18, D20, D21). That step specifies them; this file does not restate it.
#
# ============================================================================================
# THE LINE THIS FILE DRAWS, AND IT APPLIES TO EVERY PERSONA POLICY IN THE SLICE
# ============================================================================================
#
# These sets are written five stages before the resources they will govern. So:
#
#   GRANTED NOW - every action whose resource is the SERVICE or the ACCOUNT: catalog metadata,
#                 job and pipeline STATUS, log reads, registry discovery. These are complete
#                 and are not placeholders.
#   DENIED NOW  - everything the design denies. The denials are the durable half (1b step 3.5
#                 says so out loud for the approvers) and none of them needs a resource to
#                 exist: they are about actions.
#   NOT GRANTED - every action scoped to an OBJECT that does not exist yet: the lake prefixes
#                 and the derived zone (Stage 5), the Athena workgroups (Stages 5 and 9), the
#                 Studio domains (Stage 6), the ECR repositories (Stage 7). Each is named
#                 below against the stage that owes it.
#
# WHY NOT WRITE THEM ANYWAY, FROM THE NAMING CONVENTION. Because it would be a guess at an
# interface, which this stage already refuses to make for a MODULE (step 7's reordering note:
# "writing and tagging a module before any caller exists is guessing at an interface"). A
# bucket named by guess produces an ALLOW that matches nothing today - deny-by-typo, invisible
# in a plan - or, worse, an ALLOW carrying an `awsds-*` wildcard, which in an S3 ARN means any
# bucket of that shape ON EARTH, since bucket names are global. The deny fragment uses exactly
# that wildcard, and it is safe there for the reason that makes it unsafe here.
#
# NOTHING SIGNS IN BEFORE STAGE 6 (1b step 3.9), so no persona is blocked by this. What the
# stage delivers is the object, its name, its denials and its assignment - reviewable, with a
# diff and a rollback, which is what none of them had while the design lived only in a plan.
#
# ============================================================================================
# CKV_AWS_356 IS SUPPRESSED IN ALL SIX DOCUMENTS, AND THE REASON IS THE SAME ONE (step 6.5:
# decide the suppressions, do not discover them). It fires on `Resource: "*"` in an ALLOW.
# ============================================================================================
#
# WHY THE ARN CANNOT BE NARROWED HERE. A permission set is ONE document provisioned into MANY
# accounts, so every ARN it could write would have to leave the ACCOUNT field a wildcard - the
# form step 9.2 refuses outright, and refuses for a stronger reason than checkov's: a
# wildcard-account ARN in an ALLOW reaches a resource anybody can create. Taking checkov's
# advice literally would produce a worse policy than ignoring it, which is the one case where a
# gate has to be answered rather than obeyed.
#
# WHAT THE STATEMENTS ACTUALLY ARE: metadata and status reads - catalog descriptions, job and
# pipeline state, log events, registry listings. Not a single one of them returns a row of
# lake data; the calls that DO are either denied by name or absent, and both halves are
# written out per set below.
#
# WHAT CONTAINS THEM IS NOT THE ARN, AND THAT IS D19's ARGUMENT ONE LAYER UP: reaching another
# account's Glue catalog needs THAT account to allow it, and the organization's RCP perimeter
# denies access from outside the organization altogether (1c step 7.8). The perimeter is the
# containment; the resource list never was.
#
# THE NARROWING THAT IS AVAILABLE IS A CONDITION, NOT A RESOURCE - `aws:ResourceAccount` equal
# to the caller's own account - AND IT IS DELIBERATELY NOT TAKEN YET. Two reasons, and the
# second is the one that decides it: several of these services do not populate that key at all
# (ecr:GetAuthorizationToken has no resource), so it would have to be the `IfExists` form - and
# a condition that silently denies every call is exactly the failure 5.1 hit with
# `StringEquals`, one layer down and with nobody signed in to notice. It is added at Stage 6,
# where a real sign-in can measure it, and it is recorded here so that "not done" and "not
# thought of" stay distinguishable.

# ============================================================================================
# DataScientistAccess - Sandbox AND Development (D21)
# ============================================================================================
#
# 1b step 3.4: NOT PowerUserAccess and NOT AmazonSageMakerFullAccess. The second is the one
# that looks safe and is not - it grants s3:* on any bucket with "sagemaker" in the name, plus
# a broad iam:PassRole, which is the privilege-escalation pair the IAM rules exist to prevent.
#
# STILL OWED, and by whom:
#   Stage 5  s3 read/write on this account's scratch and derived prefixes (D19: the derived
#            prefix is per-principal, `.../derived/$${aws:userid}/`, and its CMK is the read
#            control - D31); s3:GetObject on the governed lake through the Lake Formation share
#   Stage 6  SageMaker Studio use against the blueprint-provisioned domain, including
#            sagemaker:CreatePresignedDomainUrl scoped to that domain, and the iam:PassRole
#            that goes with job submission - scoped by iam:PassedToService AND by role ARN
#   Stage 7  ecr pull on the dev-env repository in Production (D14)
#   Stage 9  athena:StartQueryExecution on the dedicated workgroup, whose
#            EnforceWorkGroupConfiguration = true is what makes the output location not the
#            user's choice (D19 practice i)

data "aws_iam_policy_document" "data_scientist" {
  # checkov:skip=CKV_AWS_356:one document, N accounts - no ARN can name the account; see the CKV_AWS_356 note in policies-data-scientists.tf
  source_policy_documents = [
    data.aws_iam_policy_document.shared_denies.json,
    data.aws_iam_policy_document.control_plane_vpn.json,
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
  # vending call itself. GRANTING is not here and is denied below - a data scientist is never
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

  # DISCOVERY, NOT EXECUTION. athena:StartQueryExecution is deliberately absent until the
  # workgroup exists (Stage 9): the workgroup is what pins the result location, so granting the
  # query before the workgroup would put the output location back in the user's hands, which is
  # the one thing D19 practice (i) refuses.
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
  # caller already has access to, so it opens nothing on its own. The PULL it precedes is a
  # repository-scoped grant and arrives with Stage 7.
  statement {
    sid    = "AuthenticateToEcr"
    effect = "Allow"

    actions = ["ecr:GetAuthorizationToken"]

    resources = ["*"]
  }

  # Working out why a job failed is the job. These are the account's own logs; the lake is not
  # in them.
  statement {
    sid    = "ReadCloudWatchLogs"
    effect = "Allow"

    # THE THREE ADDED 2026-08-17 ARE NOT A SCOPE CHANGE - they are the rest of a grant that was
    # already decided and enumerated one member short (Stage 4, verification (iv); Lesson 14 at
    # the smallest scale it occurs). Logs Insights was granted here from the start -
    # StartQuery/StopQuery/GetQueryResults/DescribeQueries - and the console then failed on
    # GetLogGroupFields, which is how Insights discovers a log group's fields at all.
    #
    # DERIVED FROM THE DOCUMENTED CONSOLE PERMISSION LIST, NOT FROM THE ERROR, and that is the
    # point: comparing that list against this one found THREE absent reads, not the one that
    # happened to surface. Patching only the observed failure would have brought the next person
    # back to the same screen for GetLogRecord (expanding one event in a result set) and
    # DescribeQueryDefinitions (listing saved queries).
    #
    # THE WRITE COUNTERPARTS STAY OUT, deliberately: PutQueryDefinition and DeleteQueryDefinition
    # curate the saved-query library, and these sets READ Insights.
    actions = [
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:DescribeQueries",
      "logs:DescribeQueryDefinitions",
      "logs:FilterLogEvents",
      "logs:GetLogEvents",
      "logs:GetLogGroupFields",
      "logs:GetLogRecord",
      "logs:GetQueryResults",
      "logs:StartQuery",
      "logs:StopQuery",
    ]

    resources = ["*"]
  }

  # THE GRANTOR IS SOMEBODY ELSE, AND THAT SEPARATION IS THE POINT (1b step 3.7). A principal
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
# READ-ONLY, WITH NO WRITE OF ANY KIND, NOT EVEN A DROP-BOX (1b step 3.6). The reason is not
# caution: Staging exists to be written by the pipeline and read by a human working out why the
# pipeline failed, and a staging environment a person can write to has stopped being evidence
# of what the pipeline actually does.
#
# NOT ASSIGNED YET. The Staging account is unvended (step 3.2, held on the account cap), so
# locals.tf carries no Staging row. The SET is created anyway - it costs nothing, and having it
# reviewed now rather than typed at the vend is the reason six sets are written in code at all.
#
# STILL OWED: Stage 5 s3:GetObject on Staging's own prefixes; Stage 9 read of the pipeline's
# execution history. Both READS - there is no write in this set's future either.

data "aws_iam_policy_document" "data_scientist_staging" {
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

  statement {
    sid    = "ReadCloudWatchLogs"
    effect = "Allow"

    # THE THREE ADDED 2026-08-17 ARE NOT A SCOPE CHANGE - they are the rest of a grant that was
    # already decided and enumerated one member short (Stage 4, verification (iv); Lesson 14 at
    # the smallest scale it occurs). Logs Insights was granted here from the start -
    # StartQuery/StopQuery/GetQueryResults/DescribeQueries - and the console then failed on
    # GetLogGroupFields, which is how Insights discovers a log group's fields at all.
    #
    # DERIVED FROM THE DOCUMENTED CONSOLE PERMISSION LIST, NOT FROM THE ERROR, and that is the
    # point: comparing that list against this one found THREE absent reads, not the one that
    # happened to surface. Patching only the observed failure would have brought the next person
    # back to the same screen for GetLogRecord (expanding one event in a result set) and
    # DescribeQueryDefinitions (listing saved queries).
    #
    # THE WRITE COUNTERPARTS STAY OUT, deliberately: PutQueryDefinition and DeleteQueryDefinition
    # curate the saved-query library, and these sets READ Insights.
    actions = [
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:DescribeQueries",
      "logs:DescribeQueryDefinitions",
      "logs:FilterLogEvents",
      "logs:GetLogEvents",
      "logs:GetLogGroupFields",
      "logs:GetLogRecord",
      "logs:GetQueryResults",
      "logs:StartQuery",
      "logs:StopQuery",
    ]

    resources = ["*"]
  }

  # NO ATHENA AT ALL, AND IT IS A WRITE QUESTION RATHER THAN A READ ONE. A query writes its
  # result to S3; there is no read-only Athena. So this set does not even discover workgroups,
  # and athena:StartQueryExecution is denied below along with everything else that puts a byte
  # anywhere.

  # ---------------------------------------------------------------------------------------
  # "NO WRITE OF ANY KIND", WRITTEN SO IT CAN BE MAINTAINED. Enumerating every write action in
  # AWS is a list that is wrong the week after it is written, so this is bound to a RULE
  # instead: it names the write families of exactly the services this set grants anything in,
  # plus athena, which it deliberately grants nothing in.
  #
  # THE RULE, for whoever adds an allow later: a service added to the statements above gets its
  # write family added here IN THE SAME DIFF. That is a reviewable invariant - "the services in
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
# A DIFFERENT SHAPE, NOT A WEAKER COPY (1b step 3.6): data plane read, no compute, no control
# plane. GitLab and ECR access (D14) folds into this set rather than living as a separate
# grant. The ingestion drop-box is NOT here - it moved to Data Governance with the lake (D22)
# and is granted by bucket policy to the Interactive-OU roles, not by a permission set.
#
# STILL OWED: Stage 5/9 s3:GetObject on the named application-output prefixes and
# athena:StartQueryExecution on the dedicated Production workgroup; Stage 7 ecr pull.

data "aws_iam_policy_document" "data_scientist_prod" {
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
      "glue:GetTable",
      "glue:GetTableVersions",
      "glue:GetTables",
      "glue:SearchTables",
    ]

    resources = ["*"]
  }

  # STATUS, WHICH IS WHAT THE MODEL REGISTRY IS READ FOR HERE. Describe and List reach model
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

  statement {
    sid    = "ReadCloudWatchLogs"
    effect = "Allow"

    # THE THREE ADDED 2026-08-17 ARE NOT A SCOPE CHANGE - they are the rest of a grant that was
    # already decided and enumerated one member short (Stage 4, verification (iv); Lesson 14 at
    # the smallest scale it occurs). Logs Insights was granted here from the start -
    # StartQuery/StopQuery/GetQueryResults/DescribeQueries - and the console then failed on
    # GetLogGroupFields, which is how Insights discovers a log group's fields at all.
    #
    # DERIVED FROM THE DOCUMENTED CONSOLE PERMISSION LIST, NOT FROM THE ERROR, and that is the
    # point: comparing that list against this one found THREE absent reads, not the one that
    # happened to surface. Patching only the observed failure would have brought the next person
    # back to the same screen for GetLogRecord (expanding one event in a result set) and
    # DescribeQueryDefinitions (listing saved queries).
    #
    # THE WRITE COUNTERPARTS STAY OUT, deliberately: PutQueryDefinition and DeleteQueryDefinition
    # curate the saved-query library, and these sets READ Insights.
    actions = [
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:DescribeQueries",
      "logs:DescribeQueryDefinitions",
      "logs:FilterLogEvents",
      "logs:GetLogEvents",
      "logs:GetLogGroupFields",
      "logs:GetLogRecord",
      "logs:GetQueryResults",
      "logs:StartQuery",
      "logs:StopQuery",
    ]

    resources = ["*"]
  }

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
  # 1b step 3.6 NAMES FOUR ACTIONS TO DENY EXPLICITLY, and each falls inside one of the
  # families below - said here so a reader searching for one of the four finds it:
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
