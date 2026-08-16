# What this slice reads and does not own - Stage 2 step 5.
#
# THREE LOOKUPS, AND EACH ONE EXISTS TO KEEP AN IDENTIFIER OUT OF A TRACKED FILE.
#
#   1. The Identity Center instance and its identity store   -> ARNs minted by AWS
#   2. This project's four persona groups, BY DISPLAY NAME   -> GUIDs owned by the directory
#   3. The organization's accounts, so an authored NAME      -> the id an assignment requires
#      becomes an id
#
# ON (3) AND THE SLICE SPLIT. Step 5's deliverable says `terraform state list` in sso/ names no
# aws_organizations_* MANAGED resource - and this data source is why the word is there. There
# is no second way to turn an account name into an id while aws/INDEX.md rule 1 keeps ids out
# of git, and it is the same shape org-policies/attachments.json already uses from the other
# side: names in the file, ids resolved by the consumer. The independence the split buys is
# about who OWNS an object; a read owns nothing, and nothing here has a lifecycle.
#
# ON (2) AND WHY IT IS NOT A GUID. docs/plan/conventions.md: resolve a group by DISPLAY NAME.
# Group IDs are properties of ONE directory instance - federate to a corporate IdP, which is
# what any real deployment does, and every pasted GUID becomes a resource that matches
# nothing. The GUIDs live on the `terraform import` command line for the administrator set
# (aws/output/import-ids.txt §3) and nowhere else.
#
# WHAT THE STATE FILE ENDS UP HOLDING, said out loud: the organization's account roster,
# including the e-mail address on each account. That is one more reason the Identity state
# bucket is SSE-KMS under an account-local key whose policy is the read control (bootstrap/),
# and it is why nothing in this folder ever prints an account attribute to stdout.

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

# ------------------------------------------------------------------ Identity Center instance

# AN EMPTY LIST IS THE FAILURE MODE HERE, NOT AN ERROR. This data source returns whatever the
# CONFIGURED REGION has, and an Identity Center instance is regional: point the provider at
# another Region and `arns` comes back empty, every reference below indexes into nothing, and
# the message names a list index rather than the Region that was wrong. locals.tf asserts the
# count before anything indexes it.
data "aws_ssoadmin_instances" "this" {}

# ------------------------------------------------------------------------ the persona groups
#
# FOUR GROUPS, NOT FIVE. `sso-group-infrastructure` is deliberately absent: its assignments are
# IMPORTED with the administrator set (infrastructure-access.tf), and the group is looked up
# there for exactly that purpose. Splitting the lookups follows the split in what the objects
# ARE - six sets written, one imported - so a reader can tell which half a group belongs to.
#
# THE GROUPS THEMSELVES ARE NOT DECLARED ANYWHERE IN TERRAFORM, and that is the identity seam
# (docs/plan/conventions.md): a group is person-shaped and its count grows with headcount, so
# it stays a directory object. What is here is the ENTITLEMENT that points at it.

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

# Read for ONE value per account: the id behind a name written down in locals.tf. Everything
# else this returns is incidental and nothing below consumes it.
data "aws_organizations_organization" "this" {}
