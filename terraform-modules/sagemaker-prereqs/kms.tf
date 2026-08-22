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
# THE CONSUMER ARRIVED 2026-08-22 (v0.3.2) - the paragraph that stood here said "nothing names
# it as of pass 1" with verification (xx) as the revision trigger, and what fired the trigger
# was a measurement, not (xx): aws-samples' SMUS-IaC Tooling block passes the key as the
# KmsKeyArn REGIONAL PARAMETER (the wizard's optional "Data encryption" field, which the
# API-enabled configuration had silently left at the AWS managed key). Two consumers now name
# it: Tooling's KmsKeyArn in blueprints.tf, and the projects bucket's SSE in s3.tf.
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
