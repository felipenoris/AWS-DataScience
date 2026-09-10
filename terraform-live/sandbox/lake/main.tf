# The sandbox lake (Stage 16 pass 1), layer [P].
#
# The bucket is permanent, per-SSO-group artifact storage in the experimentation account: the class
# D13 leaves ungoverned (`scratch`), made durable so a project can mature across weeks and across
# projects instead of dying with either.
#
# It is the one bucket in this tree with no expiry. The module's `expiration_days` exists so that the
# shadow lake does not silently become permanent (s3-bucket v0.3.0, written for the derived zone);
# here permanence is the requirement, and what pays for it is named in
# docs/plan/stages/stage-16-sandbox-lake.md and docs/plan/institutional-delta.md.
#
# It is not the governed lake: no Lake Formation registration, no LF-Tag, no resource link, no share.
# D13's denies over awsds-data-raw and awsds-data-curated are untouched and this bucket appears in
# none of them (measured 2026-08-26, step 0.3). A copy of governed data landing here is Stage 11's
# finding to make, not a hole this slice can close (Lesson 1).

module "lake" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v0.3.0"

  bucket_name = "awsds-${var.env}-lake"
  kms_key_arn = data.aws_kms_alias.data.target_key_arn

  # No expiration_days - see the header. The module's two unconditional rules still apply: a
  # superseded version is collected after 90 days, an abandoned multipart upload after 7.

  # No additional_policy_statements: nothing reaches this bucket by naming it in a bucket policy.
  # The only principal with a statement over its objects is the access role (iam.tf), and the only
  # way to become that principal is a vended session (grants.tf). SL-5 measures the identity side:
  # no persona document names this bucket.
}
