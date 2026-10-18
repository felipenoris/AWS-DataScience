# Stage 9 step 3.5 - the job settings in the Workloads OU document (decision 9, shape (a)).
#
# The five statements are sagemaker-denies' document, the one source the persona sets and the D13
# boundary compose (Lesson 33). They bind whoever calls Create*Job, never the role the job runs as
# (Lesson 66), so in Staging and Production they belong on the OU: the callers there are Stage 10's
# execution roles, the deploy roles and any role a pipeline creates.
#
# policies/ stays the one place a document is read from, by this slice and by render.py,
# ./scripts/check-index.py, the battery and ./aws/deploytargets.py DT-11. So the statements are
# copied into awsds-org-scp-ou-workloads.json, and policies.tf's precondition compares the copy
# with the module's rendering on every plan: an edit to either side, or a tag bump, that the other
# did not follow fails the plan and names the Sid.
#
# DenySageMakerServerlessInference (3.7, shape (b)) is the document's own and is not compared.

module "sagemaker_denies" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/sagemaker-denies?ref=sagemaker-denies-v0.2.0"
}

locals {
  workloads_document = "awsds-org-scp-ou-workloads"

  sagemaker_denies_statements = {
    module   = jsondecode(module.sagemaker_denies.json).Statement
    document = jsondecode(local.rendered[local.workloads_document]).Statement
  }

  # Each statement reduced to what IAM reads, keyed by Sid. Every value list is sorted and a
  # one-element string becomes a one-element list, so the provider's ordering of a set and the
  # file's spelling compare equal.
  sagemaker_denies_normalized = {
    for side, statements in local.sagemaker_denies_statements : side => {
      for s in statements : s.Sid => jsonencode({
        Effect    = s.Effect
        Action    = sort(flatten([try(s.Action, [])]))
        NotAction = sort(flatten([try(s.NotAction, [])]))
        Resource  = sort(flatten([s.Resource]))
        Condition = {
          for operator, pairs in try(s.Condition, {}) : operator => {
            for key, value in pairs : key => sort(flatten([value]))
          }
        }
      })
    }
  }

  # The module's Sids the document lacks or spells differently.
  sagemaker_denies_drift = [
    for sid, statement in local.sagemaker_denies_normalized.module : sid
    if lookup(local.sagemaker_denies_normalized.document, sid, "") != statement
  ]
}
