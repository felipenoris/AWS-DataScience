# Version pin - Stage 2 step 1. This file is byte-identical in every slice, with the deviation
# recorded below.
#
# It is a step of its own rather than a detail of the tooling because two of Stage 2's
# verifications are phrased "in the pinned provider version": whether aws_organizations_policy
# accepts DECLARATIVE_POLICY_EC2, and whether the descendant-OU data source recurses. A
# verification whose subject was never written down is one nobody can repeat.
#
# Terraform has no repository-wide pin: the constraint belongs to each root module. The same lines
# are repeated per slice and step 9 checks the copies have not drifted (Lesson 14). Change it in
# one slice and the check fails; change it everywhere and it is a deliberate act with a diff.
#
# The constraint admits a range; the exact build is pinned in the committed .terraform.lock.hcl,
# which carries darwin_arm64, linux_amd64 and linux_arm64 (step 6.3) so the Stage 7-8 runners do
# not fail init with a checksum error that reads like an attack.

# ---------------------------------------------------------------------------------------
# The slice-level deviation, recorded here rather than left to be noticed in a diff (Stage 6).
#
# This slice declares a second provider. The `aws` block above is unchanged and stays what the
# drift rule is about; what is added is `awscc`, because two resources in this stage exist in no
# other provider at all (measured against the pinned schemas, 2026-08-21):
#
#   awscc_datazone_project_profile                     - the V2 project profile; the aws provider
#                                                        has no equivalent resource
#   awscc_datazone_environment_blueprint_configuration - carries
#                                                        environment_role_permission_boundary,
#                                                        which is how the D13 boundary reaches
#                                                        roles DataZone authors (INT-15). The aws
#                                                        provider's version of the same resource
#                                                        has no such field
#
# docs/plan/conventions.md §6 anticipates this split - domain and IAM through the aws provider,
# project profiles, blueprints and projects through awscc - so the deviation is the convention
# being followed. Slices with no awscc resource keep the shorter file.

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
