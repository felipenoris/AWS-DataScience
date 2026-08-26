# The sandbox lake (Stage 16 pass 1), layer [P].
#
# WHAT THIS BUCKET IS, IN ONE LINE: permanent, per-SSO-group artifact storage in the
# experimentation account - the class D13 leaves ungoverned (`scratch`) made durable, so a
# project can mature across weeks and across projects instead of dying with either.
#
# WHY IT IS THE ONE BUCKET IN THIS TREE WITH NO EXPIRY, said here because the module's own
# variable argues the other way. `expiration_days` exists so that "the shadow lake does not
# silently become permanent" (s3-bucket v0.3.0, written for the derived zone). This bucket is
# permanent DELIBERATELY, which is the whole requirement, so the argument does not apply -
# what applies instead is that permanence without governance is a trade, and the five things
# that pay for it are named in docs/plan/stages/stage-16-sandbox-lake.md and summarised in
# docs/plan/institutional-delta.md. Silence here would have made the omission look accidental.
#
# WHAT IT IS NOT: the governed lake. No Lake Formation registration, no LF-Tag, no resource
# link, no share. D13's denies over awsds-data-raw and awsds-data-curated are untouched and
# this bucket appears in none of them (measured 2026-08-26, step 0.3). A copy of governed data
# landing here is Stage 11's finding to make, not a hole this slice can close (Lesson 1).

module "lake" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v0.3.0"

  bucket_name = "awsds-${var.env}-lake"
  kms_key_arn = data.aws_kms_alias.data.target_key_arn

  # NO expiration_days - see the header. The module's two unconditional rules still apply:
  # a superseded version is collected after 90 days, an abandoned multipart upload after 7.
  # Neither removes an object anybody expects to find again.

  # NO additional_policy_statements, and the emptiness is the access model rather than an
  # oversight. Nothing reaches this bucket by naming it in a bucket policy: the only principal
  # with a statement over its objects is the access role (iam.tf), and the only way to become
  # that principal is a vended session (grants.tf). SL-5 measures the identity side of the same
  # claim - no persona document names this bucket - and it passed before the bucket existed.
}
