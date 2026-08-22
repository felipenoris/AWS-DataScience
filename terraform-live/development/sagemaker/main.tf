# The blueprint PREREQUISITES for this account (Stage 6 step 2.1), layer [P].
#
# THIS SLICE IS DELIBERATELY THIN, the same argument sandbox/data/ makes: everything in it is
# the same design in both Interactive accounts - and in every business unit's Sandbox once
# D35's N passes 1 - so the design lives in terraform-modules/sagemaker-prereqs/ and what
# changes per account is which account. A setting that lives here instead of in the module is
# a setting that will differ between accounts by accident (Lesson 14).
#
# WHAT IS NOT HERE, AND WILL NEVER BE: a project ENVIRONMENT. DataZone owns those, and a
# Terraform resource for one would fight the blueprint (conventions §6). The running apps a
# project leaves behind are the [E] half and are deleted by scripts/down-studio-apps.py
# through SageMaker, never through DataZone, which owns no compute (Stage 6 step 8.3).
#
# THE APPLY IS TWO STEPS, AND THE SECOND IS NOT A CONTINUATION - it is a different sitting,
# after a console act this repository cannot perform:
#
#   1. terraform apply                       roles, boundary, key (blueprints_enabled = false)
#   2. (console) request + accept the SMUS account association for this account, then add its
#      row to SMUS_ASSOCIATED in scripts/tfhygiene/backend.py and regenerate the tfvars
#   3. terraform apply                       the blueprint configurations
#
# STEP 2 IS WHERE verification (iv) IS ANSWERED (is there any API path at all?) and where
# Lesson 16 applies hardest: record every field the console asks for.

locals {
  # The lake's Lake Formation-REGISTERED locations - raw and curated (Stage 5 pass 1). The
  # drop-box is deliberately NOT among them: files land there by IAM and are catalogued
  # afterwards, which is what makes D18's write possible at all. `artifacts` and `logs` are
  # not registered either and are not the boundary's business.
  lake_registered_bucket_arns = [
    data.terraform_remote_state.lake.outputs.bucket_arns["raw"],
    data.terraform_remote_state.lake.outputs.bucket_arns["curated"],
  ]

  # The one sanctioned direct write - the SAME expression identity/sso/locals.tf builds for
  # the persona (INT-10's identity half, mirrored: the persona set governs humans, the
  # boundary governs the roles the blueprint writes).
  lake_dropbox_write_arn = format(
    "%s/%s/*",
    data.terraform_remote_state.lake.outputs.bucket_arns["dropbox"],
    data.terraform_remote_state.lake.outputs.dropbox_prefix,
  )
}

module "sagemaker_prereqs" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/sagemaker-prereqs?ref=sagemaker-prereqs-v0.2.3"

  env    = var.env
  region = var.region

  vpc_id             = data.terraform_remote_state.foundation.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.foundation.outputs.private_subnet_ids

  lake_registered_bucket_arns = local.lake_registered_bucket_arns
  lake_dropbox_write_arn      = local.lake_dropbox_write_arn
  lake_data_key_arn           = data.terraform_remote_state.lake.outputs.data_key_arn

  allowed_instance_types = var.allowed_instance_types

  blueprints_enabled = var.blueprints_enabled
  domain_id = (
    var.blueprints_enabled
    ? data.terraform_remote_state.governance[0].outputs.domain_id
    : null
  )
}
