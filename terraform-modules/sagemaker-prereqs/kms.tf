# THE ACCOUNT'S PROJECT KMS KEY (Stage 6 step 2.1).
#
# WHAT IT IS FOR: the resources a blueprint provisions in this account that take a customer
# key - the per-project SageMaker AI domain's EBS volumes and its home EFS, the blueprint's
# own artifacts. It is NOT the account's DATA key: docs/GOVERNANCE.md §Encryption puts one
# data CMK per account (alias/awsds-<env>-data, D31) and the derived zone lives under it. Two
# keys, two jobs - a project's scratch volume and a governed copy of the lake are not the same
# blast radius, and the second one's key policy is a control this module has no business
# widening.
#
# NOTHING NAMES IT AS OF PASS 1, and the paragraph above is written in the future tense, so this
# says the present one out loud: no parameter written in this module takes a key -
# blueprints.tf's regional_parameters carry VpcId/Subnets/AZs and nothing else - and none of the
# Tooling settings docs/SMUS.md lists is a key parameter either. The key exists because Stage 6
# step 2.1's build list asks for it. REVISION TRIGGER: Stage 6 verification (xx), which is what
# decides whether it has a consumer at all.
#
# THE POLICY DELEGATES TO THIS ACCOUNT'S IAM, which is the module default (kms-key's own
# comment). What may use it is decided by the boundary and by the roles below, not by a second
# copy of that decision written as a key policy.

module "project_key" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/kms-key?ref=kms-key-v0.1.0"

  alias_name  = "awsds-${var.env}-project"
  description = "SMUS project resources in this account - blueprint-provisioned volumes and artifacts (Stage 6). NOT the data CMK."
}
