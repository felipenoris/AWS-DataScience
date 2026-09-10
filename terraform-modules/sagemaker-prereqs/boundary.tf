# The D13 permissions boundary - awsds-<env>-project-boundary (name contract: ./aws/studio.py
# US-8). The one mechanism in this stage least likely to be overwritten by the thing it
# constrains.
#
# A boundary rather than a policy: D26 moved the authorship of the project execution roles to a
# blueprint (Lesson 11), and editing what the blueprint wrote is a change the next
# reconciliation may undo, silently. A boundary caps what the role can ever be granted, whoever
# writes the grant, and it is delivered by the blueprint configuration itself
# (environment_role_permission_boundary, blueprints.tf, 2026-08-21), so the service imposes it
# while creating the role rather than us racing it afterwards. INT-15's question survives the
# change and gets narrower: does the boundary stay attached across a reconciliation (Stage 6
# step 2.5, verification (v))?
#
# The first statement is Allow * on *, because a permissions boundary is a ceiling, not a grant:
# a principal's effective permissions are the intersection of its identity policies and this
# document. A boundary containing only Deny statements has an empty allow set and would stop the
# project role doing anything at all, including the work SMUS provisioned it for. So a
# deny-shaped ceiling is a total allow with the exclusions written under it, and the exclusions
# are the content:
#
#   1. D13         no direct S3 on Lake Formation-registered prefixes. This is why the object
#                  exists (Stage 6 decision 3's own wording: "the boundary stays for the job it
#                  exists for").
#   2. D18         the drop-box is carved out of that deny, because the one sanctioned direct
#                  write has to remain possible (docs/GOVERNANCE.md §Drop-box, INT-10).
#   3. the lake    the lake's data CMK is usable only through S3 - the same kms:ViaService
#      key        condition the key policy carries, each side scoping the other.
#   4. Stage 6     the step 3 pair, mirrored: jobs off the VPC, and the instance ceiling. The
#      step 3     persona set governs humans; this governs the roles the blueprint writes.
#
# Absent: an Athena Spark clause. Decided 2026-08-19 by the user - an OU SCP reaches every IAM
# principal in this account, project roles included, so the clause would deny nothing the SCP
# does not, and where two policies deny one call only one is ever proven, the other reading as
# coverage while merely attached (Lesson 20). Revision trigger: the first principal in these
# accounts an OU SCP does not reach.

# The step 3 pair (and the three hardening statements beside them) come from the shared
# fragment, not from a copy: terraform-modules/sagemaker-denies/ is the one document, composed
# here and in terraform-live/identity/sso/ (Lesson 33). A relative source, because a git-sourced
# module clones the whole repository and its submodules resolve inside that clone; the pin is
# therefore this module's tag - a change to the denies is a new tag here too.
module "denies" {
  source = "../sagemaker-denies"

  allowed_instance_types = var.allowed_instance_types
}

data "aws_iam_policy_document" "project_boundary" {
  # The nine suppressions below are one finding, and a false one: checkov reads any policy
  # document as a grant, and this document is a permissions boundary. The two are opposite in
  # sign - a grant's `Allow *` hands out everything, a boundary's `Allow *` hands out nothing
  # and merely declines to narrow what the identity policy already granted. Every rule below
  # fires on the same statement, `CeilingIsEverythingTheIdentityPolicyGrants`, for the same
  # reason, and the header above is the argument. checkov has no `boundary` context to tell it
  # apart, so the judgement is recorded here (the runbook's rule: judge before suppressing).
  #
  # What would make these real: this document being attached as a policy to any principal. It
  # is attached in exactly one place - environment_role_permission_boundary on the blueprint
  # configuration (blueprints.tf) - and `./aws/studio.py` US-8 reads back that every
  # blueprint-provisioned project role carries it as a boundary. The day something attaches it
  # with aws_iam_role_policy_attachment, these nine stop being suppressions and become a bug.
  # checkov:skip=CKV_AWS_1:permissions BOUNDARY, not a grant - a total allow is the only shape a deny-shaped ceiling can have (header)
  # checkov:skip=CKV_AWS_49:idem - the "*" action IS the ceiling; the content is the Deny statements under it
  # checkov:skip=CKV_AWS_107:idem - no credential is exposed by a ceiling that grants nothing
  # checkov:skip=CKV_AWS_108:idem - the exfiltration control here is D13's s3:* deny, in this same document
  # checkov:skip=CKV_AWS_109:idem
  # checkov:skip=CKV_AWS_110:idem - a boundary can only reduce privilege, never escalate it
  # checkov:skip=CKV_AWS_111:idem
  # checkov:skip=CKV_AWS_356:idem
  # checkov:skip=CKV2_AWS_40:idem
  source_policy_documents = [module.denies.json]

  # ---------------------------------------------------------------- the ceiling itself
  statement {
    sid       = "CeilingIsEverythingTheIdentityPolicyGrants"
    effect    = "Allow"
    actions   = ["*"]
    resources = ["*"]
  }

  # ------------------------------------------------------------------------------- D13
  #
  # The ARN list is the bucket and its contents, both forms: `s3:ListBucket` is authorized
  # against the bucket arn and `s3:GetObject` against the object arn, so a deny naming only
  # one of the two leaves the other standing.
  statement {
    sid       = "DenyDirectS3OnLakeFormationRegisteredPrefixes"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = concat(var.lake_registered_bucket_arns, [for a in var.lake_registered_bucket_arns : "${a}/*"])
  }

  # ------------------------------------------------------------------------------- D18
  #
  # Not an exception to the deny above - the drop-box is a different bucket, and it is not
  # Lake Formation-registered: files land by IAM and are catalogued afterwards. The statement
  # is here because the boundary has to admit the write for the identity half of INT-10 to be
  # possible at all, and because a reader arriving at the deny above needs to find the
  # carve-out beside it rather than infer it.
  #
  # Open question 19 rides on this: the write is measured working and nothing catalogues what
  # lands there - the crawlers admit no principal that can start them. Granting the write is
  # not the same as the pipeline existing.
  statement {
    sid       = "AllowIngestionDropBoxWrite"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = [var.lake_dropbox_write_arn]
  }

  statement {
    sid       = "DenyLakeDataKeyExceptThroughS3"
    effect    = "Deny"
    actions   = ["kms:*"]
    resources = [var.lake_data_key_arn]

    condition {
      test     = "StringNotEquals"
      variable = "kms:ViaService"
      values   = ["s3.${var.region}.amazonaws.com"]
    }
  }
}
