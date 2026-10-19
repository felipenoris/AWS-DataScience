# The blueprint PREREQUISITES for Staging's deployment-only project (Stage 18 step 2.4), layer
# [P] for the stage's life.
#
# The same module sandbox/sagemaker/ calls, pointed at a Workloads account: what differs per account
# is which account, and a setting that lived here instead of in terraform-modules/sagemaker-prereqs/
# would differ between the two by accident (Lesson 14). The slice is studio/ and not sagemaker/
# because staging/sagemaker/ is Stage 9 step 4.3's job-role slice, which stays, and this one is
# destroyed whole at Stage 18 step 8.6 (conventions §6).
#
# What the stage measures with it: AWS's default shape for a deployment account, a project the
# CI/CD CLI deploys into and no person works in. D41 item 2 stands until the verdict, and nothing
# here is Production's.
#
# A project environment is not here and will never be: DataZone owns those, and a Terraform
# resource for one would fight the blueprint (conventions §6).
#
# The apply happens in two sittings, separated by a console act this repository cannot perform
# (Stage 6 step 1.3 measured the order):
#
#   1. terraform apply                       roles, boundary, key, bucket, log group
#                                            (blueprints_enabled = false)
#   2. (console) the user associates Staging Account to the domain from the domain account's
#      console (Stage 18 step 2.1), then adds its row to SMUS_ASSOCIATED in
#      scripts/tfhygiene/backend.py and regenerates the tfvars (2.3)
#   3. terraform apply                       decision 1's base blueprint configuration and its
#                                            grant (2.5); the boundary read back with get-role
#
# Step 1 makes no datazone: call, so it needs no carve-out; steps 2 and 3 do, which is why Stage
# 18 pass 1 precedes them.

locals {
  # The lake's Lake Formation-registered locations - raw and curated (Stage 5a pass 1). The drop-box
  # is not among them: files land there by IAM and are catalogued afterwards, which is what makes
  # D18's write possible. `artifacts` and `logs` are not registered either and are not the
  # boundary's business.
  lake_registered_bucket_arns = [
    data.terraform_remote_state.lake.outputs.bucket_arns["raw"],
    data.terraform_remote_state.lake.outputs.bucket_arns["curated"],
  ]

  # The one sanctioned direct write - the same expression identity/sso/locals.tf builds for the
  # persona (INT-10's identity half, mirrored: the persona set governs humans, the boundary governs
  # the roles the blueprint writes).
  lake_dropbox_write_arn = format(
    "%s/%s/*",
    data.terraform_remote_state.lake.outputs.bucket_arns["dropbox"],
    data.terraform_remote_state.lake.outputs.dropbox_prefix,
  )
}

module "sagemaker_prereqs" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/sagemaker-prereqs?ref=sagemaker-prereqs-v0.6.0"

  env    = var.env
  region = var.region

  vpc_id             = data.terraform_remote_state.foundation.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.foundation.outputs.private_subnet_ids

  lake_registered_bucket_arns = local.lake_registered_bucket_arns
  lake_dropbox_write_arn      = local.lake_dropbox_write_arn
  lake_data_key_arn           = data.terraform_remote_state.lake.outputs.data_key_arn

  allowed_instance_types = var.allowed_instance_types

  # Decision 1's base blueprint alone (variables.tf), never the module's default list.
  blueprint_names = var.blueprint_names

  blueprints_enabled = var.blueprints_enabled
  # The domain account is read rather than pasted (v0.3.3): the lake and the domain share the Data
  # Governance account, the lake state is read unconditionally (unlike governance/, which is gated),
  # and its data-key ARN carries the account id in field 4 - so the trust correction needs no new
  # provider, no new gate and no literal.
  domain_account_id = element(split(":", data.terraform_remote_state.lake.outputs.data_key_arn), 4)
  domain_execution_role_arn = (
    var.blueprints_enabled
    ? data.terraform_remote_state.governance[0].outputs.domain_execution_role_arn
    : null
  )
  domain_id = (
    var.blueprints_enabled
    ? data.terraform_remote_state.governance[0].outputs.domain_id
    : null
  )
  root_domain_unit_id = (
    var.blueprints_enabled
    ? data.terraform_remote_state.governance[0].outputs.root_domain_unit_id
    : null
  )
}
