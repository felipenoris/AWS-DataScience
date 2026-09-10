# What this slice reads and does not own.
#
# The lookups, each keeping an identifier out of a tracked file:
#
#   1. This account's own identity and partition           -> ARN parts
#   2. The consumers' foundation/ states                   -> the [P] S3 gateway-endpoint ids
#      and each VPN home's foundation/ state               -> the [P] WireGuard Elastic IP
#   3. The peer accounts' identities (aliased providers)   -> the ids the drop-box statements
#                                                             and the key policy are built from
#   4. The InfrastructureAccess role, by pattern           -> the data lake administrator ARN

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

# ------------------------------------------------- the consumers' gateway endpoints (INT-05)
#
# The aws:SourceVpce branch of the perimeter deny is built from the [P] gateway endpoints each
# consumer's foundation/ exports, never from the [E] interface endpoints of egress/, whose ids
# change on every `make up` and live in another account this policy could never repair itself
# against (Lesson 3, INT-05).
#
# Cross-account, so the profile rides in the config - the identity/sso/ vpn_home idiom, and the
# same failure mode: a home or consumer whose foundation/ has not been applied fails by name
# here, instead of resolving to nothing three resources later. What the read needs beyond S3 is
# kms:Decrypt on that account's alias/awsds-<env>-tfstate key; the profile is that account's
# InfrastructureAccess, which holds it.

data "terraform_remote_state" "consumer_foundation" {
  for_each = var.consumers

  backend = "s3"

  config = {
    bucket  = "awsds-${each.value.env}-tfstate"
    key     = "${each.key}/foundation/terraform.tfstate"
    region  = var.region
    profile = each.value.profile
  }
}

# ---------------------------------------------------------------- the VPN homes' Elastic IPs

data "terraform_remote_state" "vpn_home" {
  for_each = var.vpn_homes

  backend = "s3"

  config = {
    bucket = "awsds-${each.value.env}-tfstate"
    # The slice comes from the row, not from a literal (Stage 6c step 0.5). D38 moves the tunnel
    # into VPC-Networking, whose Elastic IP lives in production/networking/, so the slice is not
    # derivable from the account: a hard-coded one would read an empty state and silently produce
    # an allow-list of nothing.
    key     = "${each.key}/${each.value.slice}/terraform.tfstate"
    region  = var.region
    profile = each.value.profile
  }
}

# ------------------------------------------------------------------- the peer account ids

data "aws_caller_identity" "sandbox" {
  provider = aws.sandbox
}


data "aws_caller_identity" "production" {
  provider = aws.production
}

# --------------------------------------------------------- the data lake administrator (5.3)
#
# By pattern, never pasted: the AWSReservedSSO_* suffix is minted per account (1c decision 7),
# so the ARN cannot be written down. locals.tf asserts exactly one match - zero means the
# permission set is not provisioned here, two means the pattern went stale; both must fail by
# name, not index into nothing.

data "aws_iam_roles" "infrastructure_access" {
  name_regex  = "AWSReservedSSO_InfrastructureAccess_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

# ------------------------------------------------------ the governance manager (step 6)
#
# The same pattern read for the persona that does the tagging (decision 5 - specific grants,
# never admin). Provisioned here by identity/sso/'s `governance-manager@data-governance`
# assignment, the only account that assignment names.

data "aws_iam_roles" "governance_manager" {
  name_regex  = "AWSReservedSSO_GovernanceManagerAccess_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}
