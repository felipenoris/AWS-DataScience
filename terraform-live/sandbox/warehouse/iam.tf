# ------------------------------------------------------- the namespace role (5b 1.5, decision 5)
#
# This is the principal COPY, UNLOAD and the auto-mounted `awsdatacatalog` database run as, which
# makes it exactly the role D13 is about: a warehouse that could read a lake prefix directly would
# be a second producer into the governed lake, outside Lake Formation.
#
# IT REACHES NOTHING, AND THAT IS THE DECISION (5b decision 5). No s3:* on any of the five lake
# buckets, no lakeformation:GetDataAccess, no glue: anything. COPY from awsds-sandbox-lake is the
# plausible first ask and it has no demander yet; a role with no policy makes the first grant a
# deliberate act with a named requester, which is how the drop-box's statements were eventually got
# right.
#
# It exists at all because a namespace wants one: `default_iam_role_arn` is what Redshift assumes
# for those operations, and leaving it unset would have the service pick or refuse rather than have
# this repository name an empty role on purpose. WH-1 reads that it holds no policy; an attached
# policy is a diff somebody has to explain.
resource "aws_iam_role" "namespace_exec" {
  name        = "${local.name}-exec"
  description = "Redshift Serverless namespace role (Stage 5b step 1.5). Deliberately holds NO policy: D13 keeps the warehouse off every lake prefix until a named requester asks (decision 5)."

  assume_role_policy = data.aws_iam_policy_document.namespace_trust.json
}

data "aws_iam_policy_document" "namespace_trust" {
  # Both service principals, and neither is redundant. `redshift.amazonaws.com` is what the
  # documented Redshift role trust uses and what the provisioned service assumes;
  # `redshift-serverless.amazonaws.com` is this design's own control plane. Naming only one is the
  # kind of guess whose failure arrives as a COPY that cannot assume its own role.
  statement {
    sid     = "RedshiftAssumesThisRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["redshift.amazonaws.com", "redshift-serverless.amazonaws.com"]
    }

    # The confused-deputy pair. Without them any account's Redshift namespace could name this role.
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:redshift-serverless:${var.region}:${data.aws_caller_identity.current.account_id}:namespace/*"]
    }
  }
}

# ------------------------------------------------------------ layer 2: the project role's reach
#
# ONE POLICY PER ADMITTED PROJECT, resource-scoped to this account's workgroups. What it grants is
# AWS's own same-shape list from the SMUS Redshift access-role sample, minus everything that sample
# asks for and this design refuses:
#
#   sqlworkbench:* on *      refused - check-iam-wildcards.py rejects it, and the project role
#                            already carries SageMakerStudioProjectUserRolePolicy, whose sqlworkbench
#                            grants are the portal's own. Whether that is enough for a same-account
#                            connection is 6h 3.5's CloudTrail reading, not a guess made here.
#   redshift:*               refused - those are the PROVISIONED cluster APIs. This design has no
#                            cluster, and 5b 3.1 denies creating one organization-wide. Whether the
#                            portal calls them anyway is read from CloudTrail at 6h 3.5, which is
#                            also what decides 5b 1.10's third endpoint.
#   secretsmanager:*         refused on the ADMIN secret above all: a project role that can read the
#                            namespace admin's credential has the admin's rights, and layer 3 stops
#                            meaning anything. A purpose-made secret for the project's own database
#                            user is a different object and is 6h decision 2's fallback.
#   redshift-data:*          absent until 6h's credential answer needs it. A plain JDBC/psycopg
#                            connection over 5439 does not touch the Data API at all, so this is
#                            decided by a measurement rather than added on spec (Lesson 41).
resource "aws_iam_policy" "project_warehouse" {
  for_each = var.projects

  name        = "${local.name}-project-${each.key}"
  description = "Layer 2 of the Redshift connection (Stage 6h step 2.2): mint a database session on this account's warehouse. Attached to the SMUS project role for project ${each.key}."
  policy      = data.aws_iam_policy_document.project_warehouse[each.key].json
}

data "aws_iam_policy_document" "project_warehouse" {
  for_each = var.projects

  # The credential call and the two reads that ride with it. GetCredentials is what mints a database
  # session; GetWorkgroup and ListTagsForResource are how the portal resolves the compute and reads
  # layer 1's tag off it. All three are scoped to the workgroup ARN pattern of this account and
  # region - never `*`, which would admit a workgroup a future stage creates for another purpose.
  statement {
    sid    = "MintADatabaseSessionOnThisAccountsWarehouse"
    effect = "Allow"
    actions = [
      "redshift-serverless:GetCredentials",
      "redshift-serverless:GetWorkgroup",
      "redshift-serverless:ListTagsForResource",
    ]
    resources = [
      "arn:aws:redshift-serverless:${var.region}:${data.aws_caller_identity.current.account_id}:workgroup/*",
    ]
  }

  # ListWorkgroups takes no resource - it is how a client discovers which workgroup it may use
  # instead of being told one. Without it the portal's dropdown is empty and the only path left is a
  # hand-typed JDBC URL, which is the shape 6h 3.1 is trying to avoid measuring.
  statement {
    sid       = "ListingWorkgroupsHasNoResource"
    effect    = "Allow"
    actions   = ["redshift-serverless:ListWorkgroups", "redshift-serverless:ListNamespaces"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy_attachment" "project_warehouse" {
  for_each = var.projects

  role       = data.aws_iam_role.project[each.key].name
  policy_arn = aws_iam_policy.project_warehouse[each.key].arn

  lifecycle {
    # THE BOUNDARY IS THE CHECK, and it is checked here rather than trusted. A role that is not
    # under awsds-sandbox-project-boundary is not a project role this estate governs, whatever its
    # name looks like, and giving it GetCredentials would put a database session outside D13 - the
    # exact property the Bedrock grant chose its own shape to keep (Stage 6e decision 8).
    precondition {
      condition     = try(data.aws_iam_role.project[each.key].permissions_boundary, null) != null && can(regex("policy/${local.boundary_name}$", data.aws_iam_role.project[each.key].permissions_boundary))
      error_message = "${each.value.role_name} does not carry the D13 permissions boundary ${local.boundary_name}. A role outside the boundary is not a SMUS project role this estate governs, and layer 2 is not attached to one."
    }
  }
}
