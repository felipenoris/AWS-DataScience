# THE D13 PERMISSIONS BOUNDARY - awsds-<env>-project-boundary (name contract: ./aws/studio.py
# US-8). The one mechanism in this stage least likely to be overwritten by the thing it
# constrains.
#
# WHY A BOUNDARY AND NOT A POLICY. D26 moved the authorship of the project execution roles to
# a blueprint (Lesson 11: a decision that changes WHO AUTHORS an IAM policy invalidates every
# claim about that policy). Editing what the blueprint wrote is a change the next
# reconciliation may undo, silently. A boundary is a different object: it caps what the role
# can ever be granted, whoever writes the grant, and since 2026-08-21 it is delivered by the
# blueprint CONFIGURATION itself (environment_role_permission_boundary, blueprints.tf) - so
# the service imposes it while creating the role rather than us racing it afterwards. INT-15's
# question survives the change and gets narrower: does the boundary stay attached across a
# reconciliation (Stage 6 step 2.5, verification (v))?
#
# WHY THE FIRST STATEMENT IS Allow * ON *, WHICH LOOKS LIKE THE OPPOSITE OF A CONTROL. A
# permissions boundary is a CEILING, not a grant: a principal's effective permissions are the
# INTERSECTION of its identity policies and this document. A boundary containing only Deny
# statements has an empty allow set and would stop the project role doing anything at all -
# including the work SMUS provisioned it for. So the shape of a deny-shaped ceiling is a total
# allow with the exclusions written under it, and the exclusions are the content:
#
#   1. D13         no direct S3 on Lake Formation-registered prefixes. This is the whole
#                  reason the object exists (Stage 6 decision 3's own wording: "the boundary
#                  stays for the job it exists for").
#   2. D18         the drop-box is carved OUT of that deny, because the one sanctioned direct
#                  write has to remain possible (docs/GOVERNANCE.md §Drop-box, INT-10).
#   3. the lake    the lake's data CMK is usable only through S3 - the same kms:ViaService
#      key        condition the key policy carries, each side scoping the other.
#   4. Stage 6     the step 3 pair, mirrored: jobs off the VPC, and the instance ceiling. The
#      step 3     persona set governs humans; this governs the roles the blueprint writes.
#
# WHAT IS DELIBERATELY ABSENT: an Athena Spark clause. Decided 2026-08-19 by the user - an OU
# SCP reaches every IAM principal in this account, project roles included, so the clause would
# deny nothing the SCP does not, and Lesson 20 turns that redundancy into a cost (where two
# policies deny one call, only one is ever proven and the other reads as coverage while being
# merely attached). Revision trigger: the first principal in these accounts an OU SCP does not
# reach.

# The step 3 pair (and the three hardening statements beside them) come from the SHARED
# fragment, not from a copy: terraform-modules/sagemaker-denies/ is the one document, composed
# here and in terraform-live/identity/sso/ (Lesson 33 - one intent in two objects, structure
# shared rather than re-typed). A RELATIVE source, because a git-sourced module clones the
# whole repository and its submodules resolve inside that clone; the pin is therefore THIS
# module's tag, which is the honest coupling - a change to the denies is a new tag here too.
module "denies" {
  source = "../sagemaker-denies"

  allowed_instance_types = var.allowed_instance_types
}

data "aws_iam_policy_document" "project_boundary" {
  # THE NINE SUPPRESSIONS BELOW ARE ONE FINDING, AND IT IS A FALSE ONE - checkov reads any
  # policy document as a GRANT, and this document is a permissions BOUNDARY. The two are
  # opposite in sign: a grant's `Allow *` hands out everything, a boundary's `Allow *` hands
  # out NOTHING and merely declines to narrow what the identity policy already granted. Every
  # rule below fires on the same statement, `CeilingIsEverythingTheIdentityPolicyGrants`, for
  # the same reason, and the header above is the argument. checkov has no `boundary` context
  # to tell it apart, so the judgement is recorded here rather than delegated to a tool that
  # cannot make it (the runbook's rule: judge before suppressing).
  #
  # WHAT WOULD MAKE THESE REAL: this document being attached as a POLICY to any principal.
  # It is attached in exactly one place - environment_role_permission_boundary on the blueprint
  # configuration (blueprints.tf) - and `./aws/studio.py` US-8 reads back that every
  # blueprint-provisioned project role carries it AS A BOUNDARY. The day something attaches it
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
  # THE ARN LIST IS THE BUCKET AND ITS CONTENTS, both forms: `s3:ListBucket` is authorized
  # against the BUCKET arn and `s3:GetObject` against the OBJECT arn, so a deny naming only
  # one of the two leaves the other standing.
  statement {
    sid       = "DenyDirectS3OnLakeFormationRegisteredPrefixes"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = concat(var.lake_registered_bucket_arns, [for a in var.lake_registered_bucket_arns : "${a}/*"])
  }

  # ------------------------------------------------------------------------------- D18
  #
  # NOT AN EXCEPTION TO THE DENY ABOVE - the drop-box is a different bucket, and it is
  # NOT Lake Formation-registered (that is the whole point of a drop-box: files land by IAM
  # and are catalogued afterwards). The statement is here because the boundary has to ADMIT
  # the write for the identity half of INT-10 to be possible at all, and because a reader
  # arriving at the deny above needs to find the carve-out beside it rather than infer it.
  #
  # OPEN QUESTION 19 RIDES ON THIS: the write is measured working and NOTHING CATALOGUES what
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
