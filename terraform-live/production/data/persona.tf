# production/data/persona.tf - Stage 9 step 5.1: DataScientistProdAccess's allows on this slice's
# objects, as a customer-managed policy the permission set attaches by name (identity/sso/,
# permission-sets.tf). The identity half of D18's read-only production persona; the bucket policy's
# principal branch (buckets.tf) and the data key's AllowTheDataScientistViaS3 (main.tf) are the resource
# halves, and a read is the intersection of the two (Lesson 28).
#
# A managed policy rather than statements in the permission set: with them inline the set rendered
# 10,550 characters against the 10,240 an inline role policy holds (planned 2026-10-22), the case the
# vending policy set the precedent for (sandbox/foundation/persona-vending.tf). It lives here rather
# than in foundation/ because every ARN below is this slice's own, read from the resources that carry
# it and never composed from a naming convention, which identity/sso/'s README forbids; the debug
# role's ARN is the one contract, by name, as the key policy already names it. The slice is [P], so
# the object outlives every session, and a set that references a policy that does not exist fails to
# provision in this account: the apply order is this slice, then identity/sso/.
#
# What is not here: no lake bucket and no lakeformation action (the vending call stays inline in the
# set, as DataScientistAccess holds it); no write anywhere but the results prefix Athena writes as the
# caller; no `s3:ListBucket` outside the named prefixes, which the bucket policy also refuses. No
# network condition (D39).

data "aws_iam_policy_document" "persona" {
  # Queries on the one enforced workgroup (steps 1.2 and 5.1, decision 11): the workgroup replaces
  # the client's result location, encryption and expected bucket owner with its own, and cancels a
  # query past the scan limit (verification vi). The four actions a query takes, and the two the
  # console's history page reads, on this workgroup and no other.
  statement {
    sid    = "RunQueriesOnTheProductionWorkgroup"
    effect = "Allow"

    actions = [
      "athena:BatchGetQueryExecution",
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:ListQueryExecutions",
      "athena:StartQueryExecution",
      "athena:StopQueryExecution",
    ]

    resources = [aws_athena_workgroup.this.arn]
  }

  # The named application-output prefixes, the same list the bucket policy's principal branch is
  # written from (var.persona_read_prefixes, generated into this slice from backend.py). The listing
  # is held to the prefixes too, so the console's folder view works where the objects do
  # (verification x).
  statement {
    sid    = "ReadTheNamedApplicationOutputs"
    effect = "Allow"

    actions = ["s3:GetObject", "s3:GetObjectVersion"]

    resources = [for p in var.persona_read_prefixes : "${module.outputs_bucket.bucket_arn}/${p}*"]
  }

  statement {
    sid    = "ListTheNamedApplicationOutputs"
    effect = "Allow"

    actions = ["s3:ListBucket", "s3:GetBucketLocation"]

    resources = [module.outputs_bucket.bucket_arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = concat([""], [for p in var.persona_read_prefixes : "${p}*"])
    }
  }

  # The results Athena writes as the caller under the enforced location (step 1.2): the actions AWS's
  # Athena policy names for a results bucket, on results/ alone. The read of another person's result is
  # the stage's stated limit (its risk on query visibility; D31 keeps it from the approvers).
  statement {
    sid    = "ReadAndWriteTheQueryResults"
    effect = "Allow"

    actions = [
      "s3:AbortMultipartUpload",
      "s3:GetObject",
      "s3:ListMultipartUploadParts",
      "s3:PutObject",
    ]

    resources = ["${module.derived_bucket.bucket_arn}/results/*"]
  }

  statement {
    sid    = "ListTheQueryResults"
    effect = "Allow"

    actions = ["s3:ListBucket", "s3:GetBucketLocation"]

    resources = [module.derived_bucket.bucket_arn]
  }

  # Both buckets are under the account data CMK, whose policy admits this persona's role through S3
  # alone (main.tf, AllowTheDataScientistViaS3). The identity half of that pair, and nothing outside
  # S3's use of the key (D31).
  statement {
    sid    = "UseTheDataKeyThroughS3"
    effect = "Allow"

    actions = ["kms:Decrypt", "kms:GenerateDataKey"]

    resources = [module.consumer_data.data_key_arn]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = [local.s3_via]
    }
  }

  # The escape hatch (step 6): its trust admits this persona's reserved role inside an approved
  # window alone, and a successful assumption fires awsds-prod-debug-assume. This is the persona's
  # half; outside the window the trust refuses, and the statement opens nothing.
  statement {
    sid    = "AssumeTheDebugRoleInsideAnApprovedWindow"
    effect = "Allow"

    actions = ["sts:AssumeRole"]

    resources = [local.debug_role_arn]
  }
}

resource "aws_iam_policy" "persona" {
  name        = var.persona_policy_name
  description = "DataScientistProdAccess's allows on this account's data platform (Stage 9 step 5.1): the enforced workgroup, the named output prefixes, the query results, the data key through S3, the debug role inside its window"
  policy      = data.aws_iam_policy_document.persona.json

  tags = {
    Name = var.persona_policy_name
  }
}
