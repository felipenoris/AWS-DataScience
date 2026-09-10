# The access role (Stage 16 pass 2) - awsds-<env>-lake-access.
#
# One role does two jobs: it is the Access Grants location role (the identity S3 vends when it
# answers GetDataAccess) and the SMUS connection's access role (the ARN typed into the portal's
# S3-connection form). One object means one principal to name in the key policy and one session
# identity in every CloudTrail row for this bucket.
#
# Reach here is an intersection (Lesson 28) and this file writes one half. A vended read of an
# SSE-KMS object needs both the S3 permission below and a key policy that admits this role; the key
# lives in sandbox/data/. Step 2.3 proves the negative before pass 3 opens anything.

locals {
  bucket_arn = "arn:${data.aws_partition.current.partition}:s3:::awsds-${var.env}-lake"

  # The Access Grants instance ARN is built rather than read, because the provider has no data
  # source for it. Not a version lag: checked 2026-08-26 against the provider's docs tree on `main`
  # (ahead of the v6.61.0 release, carrying the unreleased 6.62.0), website/docs/r/ has all three
  # s3control_access_grants_* resources and website/docs/d/ has none of them, so upgrading does not
  # remove this workaround. The managed resource is what this slice must not declare, because the
  # instance is SMUS-born and service-owned (Lesson 17). What is left is construction, from values
  # none of which is pasted: the partition and the account come from data.tf, the region from the
  # tfvars. `default` is the only instance an account can have, and the form is confirmed by the
  # 2026-08-26 baseline reading of ./aws/sandboxlake.py, which printed exactly this ARN.
  # Revision trigger: a d/s3control_access_grants_instance page appearing in that tree.
  access_grants_instance_arn = format(
    "arn:%s:s3:%s:%s:access-grants/default",
    data.aws_partition.current.partition,
    var.region,
    data.aws_caller_identity.current.account_id,
  )
}

# ------------------------------------------------------------------------------- the trust
#
# The first statement is the service, and the only one that exists before pass 4. It is AWS's
# documented Access Grants location-role trust, with the S3 guide's stricter aws:SourceArn adopted
# alongside the mandatory aws:SourceAccount: the pin is the instance ARN built in
# local.access_grants_instance_arn, so this role is bound to this account's one instance.
#
# sts:SetContext is absent from it. That action belongs to the directory-grantee path (an Identity
# Center-associated instance vending against a group), and decision 2 chose the IAM grain so that
# association stays open question 13's decision. If OQ 13 closes the other way, this is the line
# that changes.
#
# The remaining statements are the wired projects, documentation-derived and unmeasured until step
# 4.2 answers verification (ii). The shape is AWS's connection documentation read on 2026-08-26: an
# assume gated on the project id as sts:ExternalId, a source identity matched to the caller's own
# datazone:userId principal tag, and session tags for the two DataZone request tags. They are
# separate statements because they are different actions - a trust that admits sts:AssumeRole alone
# rejects an assume that also sets tags or a source identity.
#
# The TagSession statement pins AmazonDataZoneProject to this entry's project id and leaves
# AmazonDataZoneDomain unconstrained. The principal is already one project's role and the project id
# is already pinned, so pinning the domain would add nothing and would cost a cross-account
# remote-state read of the domain account. Revision trigger: a second domain in this estate.

data "aws_iam_policy_document" "lake_access_trust" {
  statement {
    sid     = "AccessGrantsServiceVending"
    effect  = "Allow"
    actions = ["sts:AssumeRole", "sts:SetSourceIdentity"]

    principals {
      type        = "Service"
      identifiers = ["access-grants.s3.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [local.access_grants_instance_arn]
    }
  }

  dynamic "statement" {
    for_each = var.wired_projects

    content {
      sid     = "SmusProjectAssume${replace(statement.key, "/[^0-9A-Za-z]/", "")}"
      effect  = "Allow"
      actions = ["sts:AssumeRole"]

      principals {
        type        = "AWS"
        identifiers = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/${statement.value.project_role_name}"]
      }

      condition {
        test     = "StringEquals"
        variable = "sts:ExternalId"
        values   = [statement.value.project_id]
      }
    }
  }

  dynamic "statement" {
    for_each = var.wired_projects

    content {
      sid     = "SmusProjectSourceIdentity${replace(statement.key, "/[^0-9A-Za-z]/", "")}"
      effect  = "Allow"
      actions = ["sts:SetSourceIdentity"]

      principals {
        type        = "AWS"
        identifiers = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/${statement.value.project_role_name}"]
      }

      condition {
        test     = "StringLike"
        variable = "sts:SourceIdentity"
        values   = ["$${aws:PrincipalTag/datazone:userId}"]
      }
    }
  }

  dynamic "statement" {
    for_each = var.wired_projects

    content {
      sid     = "SmusProjectTagSession${replace(statement.key, "/[^0-9A-Za-z]/", "")}"
      effect  = "Allow"
      actions = ["sts:TagSession"]

      principals {
        type        = "AWS"
        identifiers = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/${statement.value.project_role_name}"]
      }

      condition {
        test     = "StringEquals"
        variable = "aws:RequestTag/AmazonDataZoneProject"
        values   = [statement.value.project_id]
      }
    }
  }
}

# -------------------------------------------------------------------------- the permissions
#
# Scoped to one bucket and one key, which is what lets the role carry no permissions boundary
# (below). The object actions are the READWRITE set the grants hand out; the bucket actions are what
# a listing needs. s3:DeleteObject is included because a permanent artifact store needs correction:
# versioning is what makes that safe, and the module's noncurrent-version rule keeps it from being
# free forever.
#
# The KMS block is not a grant. It is the identity half of an intersection whose other half is the
# key policy in sandbox/data/ (pass 2.2); until that half lands, every call here fails with an
# AccessDenied naming KMS rather than S3, which is what step 2.3 records.

data "aws_iam_policy_document" "lake_access" {
  statement {
    sid    = "ReadWriteLakeObjects"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload",
      "s3:ListMultipartUploadParts",
    ]

    resources = ["${local.bucket_arn}/*"]
  }

  statement {
    sid    = "ListTheLake"
    effect = "Allow"

    actions = [
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:GetBucketLocation",
    ]

    resources = [local.bucket_arn]
  }

  statement {
    sid    = "UseTheAccountDataKeyViaS3"
    effect = "Allow"

    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]

    resources = [data.aws_kms_alias.data.target_key_arn]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["s3.${var.region}.amazonaws.com"]
    }
  }
}

# Absent from the permissions, a deviation from AWS's documented "option 1" location role: the S3AG*
# location- and grant-management statements, and the iam:PassRole to the Access Grants service. Those
# exist so that a connection can register its own location; here the location is pre-registered by
# grants.tf and the portal form is handed an existing one. Verification (ii) is the gate - if
# creating a connection demands them, they join this role as a measured amendment with a date.

module "lake_access_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "awsds-${var.env}-lake-access"
  description = "S3 Access Grants location role for awsds-${var.env}-lake, and the access role of every SMUS S3 connection into it (Stage 16)."

  assume_role_policy = data.aws_iam_policy_document.lake_access_trust.json

  inline_policies = {
    lake-access = data.aws_iam_policy_document.lake_access.json
  }

  # Null is a decision; the module makes the argument required so that it has to be one. A boundary
  # is a ceiling, and this role's identity policy is already one bucket and one key, with every
  # vended session narrowed again by the grant's own scope-down policy. A boundary here would be a
  # third copy of the same narrowing, and where three documents deny one call only one is proven
  # (Lesson 20). The D13 project boundary is not a candidate either: it is the SMUS project ceiling.
  # Revision trigger: the first statement added to this role that names anything other than this
  # bucket or this account's data key.
  permissions_boundary = null
}
