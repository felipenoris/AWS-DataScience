# Version pin - Stage 2 step 1. THIS FILE IS BYTE-IDENTICAL IN EVERY SLICE.
#
# Why it is a step of its own rather than a detail of the tooling: two of Stage 2's
# verifications are phrased "in the pinned provider version" - whether
# aws_organizations_policy accepts DECLARATIVE_POLICY_EC2, and whether the descendant-OU
# data source really recurses - and a verification whose subject was never written down is a
# verification nobody can repeat.
#
# Terraform has no repository-wide pin: the constraint belongs to each root module. So the
# same four lines are repeated per slice and step 9 checks the copies have not drifted -
# Lesson 14, a condition that must appear in N places by hand will be missing from one of
# them. Change it in one slice and the check fails; change it everywhere and it is a
# deliberate act with a diff.
#
# The constraint here admits a range; the exact build is pinned in the committed
# .terraform.lock.hcl, which carries darwin_arm64, linux_amd64 and linux_arm64 (step 6.3) so
# the Stage 7-8 runners do not fail init with a checksum error that reads like an attack.

# ---------------------------------------------------------------------------------------
# THE ONE SLICE-LEVEL DEVIATION FROM "BYTE-IDENTICAL IN EVERY SLICE", and it is recorded here
# rather than left to be noticed in a diff (Stage 6, 2026-08-21).
#
# This slice declares a SECOND provider. The `aws` block above is unchanged and stays the
# thing the drift rule is about - what is added is `awscc`, because two resources in this
# stage exist in no other provider at all (measured against the pinned schemas, 2026-08-21):
#
#   awscc_datazone_project_profile                     - the V2 project profile; the aws
#                                                        provider has no equivalent resource
#   awscc_datazone_environment_blueprint_configuration - carries
#                                                        environment_role_permission_boundary,
#                                                        which is how the D13 boundary reaches
#                                                        roles DataZone AUTHORS (INT-15). The
#                                                        aws provider's version of the same
#                                                        resource has no such field
#
# docs/plan/conventions.md §6 anticipated exactly this split - "domain + IAM through the aws
# provider, project profiles / blueprints / projects through awscc" - so the deviation is the
# convention being followed, not broken. Slices with no awscc resource keep the four-line file.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }

    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 1.89"
    }
  }
}
