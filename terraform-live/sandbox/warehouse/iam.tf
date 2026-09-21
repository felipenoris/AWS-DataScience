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
#   sqlworkbench:* on *      refused as an unmeasured wildcard, NOT by any gate in this repository:
#                            check-iam-wildcards.py matches `arn:aws:iam::*:` and scans the identity
#                            plane, so it neither sees this slice nor judges an action (read
#                            2026-09-21, correcting the reason this line first gave). The project
#                            role already carries SageMakerStudioProjectUserRolePolicy, whose
#                            sqlworkbench grants are the portal's own; whether that is enough for a
#                            same-account connection is 6h 3.5's CloudTrail reading. If the portal
#                            turns out to need it, it goes on the ACCESS ROLE below rather than here.
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
  # region - never `*`, which would admit a workgroup in any account this role might ever reach.
  #
  # THE WILDCARD IS ON THE ID AND IT HAS TO BE (measured at 5b step 1.9, 2026-09-20). A workgroup's
  # ARN carries a SERVICE-MINTED UUID, not its name, and a destroy/re-create under the same name
  # produces a different one: `workgroup/75b926c8-…` became `workgroup/4b0577a2-…` across one
  # `make down`/`make up`. So a policy naming this workgroup's ARN exactly would authorize nothing
  # after the next session, and the failure would arrive as a project whose queries stopped
  # authenticating with no diff anywhere. The name is stable and the id is not; the ARN carries the
  # id; therefore the resource is the account-and-region pattern. The same reading constrains the
  # 5b 3.2 SCP, which must not name a usage limit by ARN either - that id moved too.
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

  # The project role must be able to ASSUME THE ACCESS ROLE below, and this is stated here rather
  # than relied on. AWS's cross-account procedure publishes the access role's trust policy and never
  # mentions granting the project role anything - which implies one of the managed policies the
  # service attaches already carries it. That is a claim about an AWS managed policy's contents, and
  # AWS edits those (Lesson 49): a grant that works today because somebody else's document happens
  # to include it is a grant with no owner. One resource, this project's access role only.
  statement {
    sid       = "AssumeThisProjectsAccessRole"
    effect    = "Allow"
    actions   = ["sts:AssumeRole"]
    resources = [aws_iam_role.project_access[each.key].arn]
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

# ------------------------------------- the access role, one per admitted project (6h 3.1, 3.2)
#
# THE PORTAL REQUIRES THIS ROLE AND AWS'S DOCUMENTATION SAYS IT DOES NOT (measured 2026-09-21, by
# the user, in the portal, on a same-account connection). AWS's "Gaining access to Amazon Redshift
# resources" splits into two procedures: the SAME-ACCOUNT one is three steps and names no access
# role at all - the admin tags the objects and "must send you a username and password" - while the
# access role, its trust policy and the `RedshiftDbUser` tag all live under "resources in a
# different account". The form's own help repeats it: "Access role ARN is optional. Required when
# connecting to resources in a different AWS account."
#
# The form then refuses to submit without it, in this account, for this workgroup. "AWS Secret" is
# marked optional beside it and the access role is not. So the implemented form and the documented
# procedure disagree, and the form is what has to be satisfied.
#
# WHY THAT IS THE BETTER OUTCOME ANYWAY. The API's own credential model (`create-connection`'s
# `redshiftProperties.credentials`) is a tagged union with exactly two variants, `secretArn` and
# `usernamePassword` - there is NO IAM variant. The portal's "IAM credentials" is this role plus the
# `RedshiftDbUser` tag, which is how it reaches a database with no standing credential anywhere.
# That is what 6h decision 2 asked for and could not find a mechanism for; the mechanism is here,
# and the purpose-made secret that decision 2 held in reserve is not needed.
resource "aws_iam_role" "project_access" {
  for_each = var.projects

  name        = "${local.name}-access-${each.key}"
  description = "Stage 6h 3.1: the access role the SMUS project's Redshift connection assumes to mint a database session. Required by the portal form even same-account, where AWS's own procedure names no such role."

  assume_role_policy = data.aws_iam_policy_document.project_access_trust[each.key].json

  # `RedshiftDbUser` DECIDES THE DATABASE USER, which is why the value is the project role's name
  # rather than something new. AWS: the tag "determines the federated database user within the
  # databases". Whether the platform uses it VERBATIM or prefixes it the way an IAM-derived user is
  # spelled (`IAMR:<role>`) is not stated on any page read on 2026-09-21 - so the value is chosen to
  # make the two candidate spellings collapse onto the pair of database users layer 3 would have
  # needed anyway:
  #
  #   verbatim  -> `datazone_usr_role_<project>_<env>`
  #   prefixed  -> `IAMR:datazone_usr_role_<project>_<env>`, which is also what a direct IAM session
  #                from JupyterLab would resolve to
  #
  # Both exist in the database and both hold `sbx_lab_rw`, so the first connection cannot land on a
  # user with no grants. Which one it picked is then a readable fact in `pg_user`, and the other is
  # one `DROP USER` - the same discipline the runbook's section P takes for the identifier itself.
  #
  # `RedshiftDbRoles` IS DELIBERATELY ABSENT. It would map a database role at first sign-in and save
  # the GRANT, but AWS: "In a case where you pass a role name that doesn't exist in the database,
  # it's ignored" - a typo would produce a session with no privileges and nothing anywhere saying
  # why. Layer 3 stays in SQL, where WH-12 reads it back.
  tags = { RedshiftDbUser = each.value.role_name }
}

data "aws_iam_policy_document" "project_access_trust" {
  for_each = var.projects

  # AWS's documented trust policy for this role, kept whole. All three statements name the project
  # role, so only that project can assume it - the tag on the workgroup admits the project to the
  # compute and this admits it to the role, and both are keyed off the same map entry.
  statement {
    sid     = "TheProjectRoleAssumesThisRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = [data.aws_iam_role.project[each.key].arn]
    }

    # The external id is the project id. Same-account it is not a confused-deputy guard - both roles
    # are here - but it is what AWS's sample sends and what the portal fills, so a connection built
    # by the portal would fail an assume without it.
    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = [each.key]
    }
  }

  # The session carries WHO is querying, not just which project. `datazone:userId` is a principal tag
  # the portal sets on the project role's session, and propagating it as the source identity is what
  # makes 6h 3.5's CloudTrail reading able to name a person rather than a role - the question 6d
  # step 7 left open when `StartSession` turned out to be called as the project role.
  statement {
    sid     = "TheSessionCarriesTheUsersIdentity"
    effect  = "Allow"
    actions = ["sts:SetSourceIdentity"]

    principals {
      type        = "AWS"
      identifiers = [data.aws_iam_role.project[each.key].arn]
    }

    condition {
      test     = "StringLike"
      variable = "sts:SourceIdentity"
      values   = ["$${aws:PrincipalTag/datazone:userId}"]
    }
  }

  # Session tags, and the pair is required rather than decorative: the portal tags the assumed
  # session with the project and the domain, and this is the statement that permits it. Both values
  # are pinned, so a session tagged with another project's id cannot be minted through this role.
  statement {
    sid     = "TheSessionIsTaggedWithThisProjectAndDomain"
    effect  = "Allow"
    actions = ["sts:TagSession"]

    principals {
      type        = "AWS"
      identifiers = [data.aws_iam_role.project[each.key].arn]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = [each.key]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/AmazonDataZoneDomain"
      values   = [var.datazone_domain_id]
    }
  }
}

# The access role carries the SAME layer 2 policy as the project role. One authored document, two
# holders: the project role for a direct IAM session from JupyterLab, the access role for the
# portal's connection. Giving the access role its own copy is how the two would drift (Lesson 33).
resource "aws_iam_role_policy_attachment" "project_access_warehouse" {
  for_each = var.projects

  role       = aws_iam_role.project_access[each.key].name
  policy_arn = aws_iam_policy.project_warehouse[each.key].arn
}

# The two tag reads, and they are the access role's alone. AWS names them for exactly this case -
# "signing in using IAM credentials", where the roles and user come from a tag key and value - so
# the identity that signs in has to be able to read its own tags. Neither takes a resource. They are
# not on the project role because nothing on that path reads a tag to decide a database user.
resource "aws_iam_policy" "project_access_tags" {
  for_each = var.projects

  name        = "${local.name}-access-tags-${each.key}"
  description = "Stage 6h 3.1: the tag reads the IAM-credentials sign-in needs, so the access role can resolve its own RedshiftDbUser tag."
  policy      = data.aws_iam_policy_document.project_access_tags[each.key].json
}

data "aws_iam_policy_document" "project_access_tags" {
  for_each = var.projects

  statement {
    sid       = "ResolveOwnPrincipalTags"
    effect    = "Allow"
    actions   = ["tag:GetResources", "tag:GetTagKeys"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy_attachment" "project_access_tags" {
  for_each = var.projects

  role       = aws_iam_role.project_access[each.key].name
  policy_arn = aws_iam_policy.project_access_tags[each.key].arn
}
