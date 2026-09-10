# What this slice reads and does not own - Stage 2 step 5.
#
# Each lookup keeps an identifier out of a tracked file.
#
#   1. The Identity Center instance and its identity store   -> ARNs minted by AWS
#   2. This project's four persona groups, by display name   -> GUIDs owned by the directory
#   3. The organization's accounts, so an authored name      -> the id an assignment requires
#      becomes an id
#
# On (3) and the slice split: step 5's deliverable says `terraform state list` in sso/ names no
# aws_organizations_* managed resource, and this data source is why the word is there. There is
# no second way to turn an account name into an id while aws/INDEX.md rule 1 keeps ids out of
# git, and it is the same shape org-policies/attachments.json uses from the other side: names
# in the file, ids resolved by the consumer. The split is about who owns an object; a read owns
# nothing, and nothing here has a lifecycle.
#
# On (2): docs/plan/conventions.md resolves a group by display name. Group ids are properties of
# one directory instance - federate to a corporate IdP, which is what any real deployment does,
# and every pasted GUID becomes a resource that matches nothing. The GUIDs live on the
# `terraform import` command line for the administrator set (aws/output/import-ids.txt §3) and
# nowhere else.
#
# The state file ends up holding the organization's account roster, including the e-mail address
# on each account. The Identity state bucket is SSE-KMS under an account-local key whose policy
# is the read control (bootstrap/), and nothing in this folder ever prints an account attribute
# to stdout.

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

# ------------------------------------------------------------------ Identity Center instance

# An empty list, not an error, is the failure mode here. This data source returns whatever the
# configured Region has, and an Identity Center instance is regional: point the provider at
# another Region and `arns` comes back empty, every reference below indexes into nothing, and
# the message names a list index rather than the Region that was wrong. locals.tf asserts the
# count before anything indexes it.
data "aws_ssoadmin_instances" "this" {}

# ------------------------------------------------------------------------ the persona groups
#
# `sso-group-infrastructure` is absent: its assignments are imported with the administrator set
# (infrastructure-access.tf), and the group is looked up there. Splitting the lookups follows
# the split in what the objects are - six sets written, one imported - so a reader can tell
# which half a group belongs to.
#
# The groups themselves are not declared anywhere in Terraform, which is the identity seam
# (docs/plan/conventions.md): a group is person-shaped and its count grows with headcount, so
# it stays a directory object. What is here is the entitlement that points at it.

data "aws_identitystore_group" "data_scientists" {
  identity_store_id = local.identity_store_id

  alternate_identifier {
    unique_attribute {
      attribute_path  = "DisplayName"
      attribute_value = "sso-group-data-scientists"
    }
  }
}

data "aws_identitystore_group" "deployment_managers" {
  identity_store_id = local.identity_store_id

  alternate_identifier {
    unique_attribute {
      attribute_path  = "DisplayName"
      attribute_value = "sso-group-deployment-managers"
    }
  }
}

data "aws_identitystore_group" "governance_managers" {
  identity_store_id = local.identity_store_id

  alternate_identifier {
    unique_attribute {
      attribute_path  = "DisplayName"
      attribute_value = "sso-group-governance-managers"
    }
  }
}

data "aws_identitystore_group" "dev_env_stewards" {
  identity_store_id = local.identity_store_id

  alternate_identifier {
    unique_attribute {
      attribute_path  = "DisplayName"
      attribute_value = "sso-group-dev-env-stewards"
    }
  }
}

# ----------------------------------------------------------------------------- the accounts

# Read for one value per account: the id behind a name written down in locals.tf. Everything
# else this returns is incidental and nothing below consumes it.
data "aws_organizations_organization" "this" {}

# ---------------------------------------------------------------- the VPN homes' Elastic IPs
#
# Stage 4 step 8.1, the first read in this repository that crosses an account boundary.
# Everything above is read from the account this slice is applied into; this reads the Sandbox
# account's foundation/ state from the Identity account.
#
# Remote state rather than an aws_eip data source, because of what happens when the answer is
# wrong. A tag-filtered aws_eip lookup returns whatever carries the tag, in whatever account the
# provider happens to point at, and an address that matched nothing is an empty result rather
# than an error - the shape that turns into the empty allow-list variables.tf refuses. Remote
# state names the slice that owns the address (step 2.1: allocated in foundation/, never in
# vpn/, so it survives every `make down`), so a home whose foundation/ has not been applied
# fails by name here instead of resolving to nothing three resources later.
#
# The profile is in the config because a same-account read inherits AWS_PROFILE from the command
# line (sandbox/vpn/main.tf reads foundation/ that way and passes no profile) and this one
# cannot: the apply runs as awsds-infra-identity and the bucket lives in Sandbox. Both profiles
# sit on the `awsds` sso-session, so one sign-in covers the pair - aws/AWS-CLI.md, "Signing in".
#
# Beyond S3 the read needs kms:Decrypt on the home's own alias/awsds-<env>-tfstate key, because
# the state object is SSE-KMS. The profile is that account's InfrastructureAccess, which holds
# it, so the failure mode of a mis-generated tfvars is an AccessDenied naming KMS rather than a
# silently stale address.
data "terraform_remote_state" "vpn_home" {
  for_each = var.vpn_homes

  backend = "s3"

  config = {
    # The key is built from the account folder, which is the map key - the same rule
    # scripts/tfhygiene/backend.py's backend_values() applies, and the reason the folder rides
    # in the tfvars rather than being re-derived from the env token (that reverse map would be
    # a second copy of ENV_TOKENS - Lesson 14).
    bucket  = "awsds-${each.value.env}-tfstate"
    key     = "${each.key}/${each.value.slice}/terraform.tfstate"
    region  = var.region
    profile = each.value.profile
  }
}

# ------------------------------------------------------------------------------ the lake
#
# Stage 5 pass 4c. Same mechanics as vpn_home above: cross-account, the profile rides in the
# generated tfvars, one sign-in covers every profile on the `awsds` sso-session.
#
# There is no consumer_data read and no workgroup or derived-bucket ARN: the derived zone
# re-homed onto the SMUS project path and the persona's query surface is a SMUS project
# (D19 revised).
data "terraform_remote_state" "lake_data" {
  for_each = var.lake

  backend = "s3"

  config = {
    bucket  = "awsds-${each.value.env}-tfstate"
    key     = "${each.key}/data/terraform.tfstate"
    region  = var.region
    profile = each.value.profile
  }
}
