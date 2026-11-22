# ------------------------------------------------------- the namespace role (5b 1.5, Stage 9 9.2)
#
# The principal COPY, UNLOAD and the auto-mounted `awsdatacatalog` database run as, which makes it
# the role D13 is about: a warehouse that could read a lake prefix directly would be a second producer
# into the governed lake, outside Lake Formation.
#
# It holds no policy, and the absence is step 9.2's decision. A Glue or Lake Formation grant here
# turns `awsdatacatalog` on over Production's resource links to the lake, with the engine reading as
# this role rather than as the caller: a second reader of the lake, bounded only by the role's own
# grants. If 9.5's shape needs the role, its Lake Formation grants are enumerated in the register and
# WH-1b gets a Production rule. In every case the role holds no `s3:*` on a lake prefix (D13), and 9.6
# measures it.
#
# It exists because a namespace wants one: `default_iam_role_arn` is what Redshift assumes for those
# operations, and leaving it unset would have the service pick or refuse rather than have this
# repository name an empty role on purpose. WH-1b reads that it holds no policy.
resource "aws_iam_role" "namespace_exec" {
  name        = "${local.name}-exec"
  description = "Redshift Serverless namespace role (Stage 9 step 9.2). Holds no policy: D13 keeps the warehouse off every lake prefix until a named requester asks."

  assume_role_policy = data.aws_iam_policy_document.namespace_trust.json
}

data "aws_iam_policy_document" "namespace_trust" {
  # Both service principals. `redshift.amazonaws.com` is what the documented Redshift role trust
  # uses and what the provisioned service assumes; `redshift-serverless.amazonaws.com` is this
  # design's own control plane. Naming only one fails as a COPY that cannot assume its own role.
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
