# Version pin - Stage 2 step 1. This file is byte-identical in every slice.
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
#
# No backend block here, in any slice. It lives in providers.tf as partial configuration (step
# 2.5), and in bootstrap/ it arrives only after the first apply: this slice creates the bucket that
# would hold its own state, so phase 1 runs local and phase 2 migrates (2.2).

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}
