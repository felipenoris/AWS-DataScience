locals {
  # DECISION 5's CATEGORY 1, by API name - the blueprints a project profile may bundle. The
  # SAME list terraform-modules/sagemaker-prereqs/ enables per member account and the same one
  # ./aws/studio.py US-3 holds; docs/SMUS.md is the reference table with the three categories
  # and the billing shapes. A category-2 blueprint (Workflows OnDemand, MLExperiments) joins
  # all three in ONE commit, which is Lesson 14's rule applied to a list that lives in a
  # module, a slice and a check.
  #
  # EMRServerless FOLLOWS DECISION 1, which is reopened on an endpoint count and settled
  # in-stage by two readings (4.2's flow logs; whether a `fineGrained` EMR-S connection is
  # usable from an IdC-domain notebook). Landing on Glue interactive sessions removes this one
  # entry - and needs no blueprint at all, a Glue connection in the project instead.
  category_one_blueprints = ["Tooling", "DataLake", "EMRServerless", "AmazonBedrockGenerativeAI"]

  member_account_ids = {
    sandbox     = data.aws_caller_identity.sandbox.account_id
    development = data.aws_caller_identity.development.account_id
  }

  # THE TWO PROFILES AND WHERE EACH PROVISIONS (D21/D26). The names are a contract with
  # ./aws/studio.py (US-4) and the account pinning is what turns D21's boundary from "which URL
  # did the person open" into a property of the project.
  project_profiles = {
    experimentation = {
      account     = "sandbox"
      description = "Experimentation (D21): the unit of work is a notebook. Provisions into a business unit's Sandbox."
    }
    engineering = {
      account     = "development"
      description = "Engineering (D21): the unit of work is a pipeline. Provisions into Development, where the promotion chain starts."
    }
  }

  # THE TOOLING PARAMETERS STAGE 6 STEP 1.5 LOCKS. Every one is marked NON-EDITABLE, and that
  # flag is the whole difference between a default and a control (Lesson 5): the parameter
  # exists so nobody can flip a project to PublicInternetOnly, raise its idle ceiling, or give
  # itself a 16 TiB volume.
  #
  # sagemakerDomainNetworkType = VpcOnly IS ALREADY THE BLUEPRINT DEFAULT (read 2026-08-16).
  # It is written here anyway, for the reason above - a default that nobody may change is a
  # different object from a default.
  tooling_parameters = [
    { name = "sagemakerDomainNetworkType", value = "VpcOnly", is_editable = false },
    { name = "lifecycleManagement", value = "true", is_editable = false },
    { name = "idleTimeoutInMinutes", value = tostring(var.idle_timeout_minutes), is_editable = true },
    { name = "maxIdleTimeoutInMinutes", value = tostring(var.max_idle_timeout_minutes), is_editable = false },
    { name = "maxEbsVolumeSize", value = tostring(var.max_ebs_volume_size_gb), is_editable = false },
    {
      name        = "enableTrustedIdentityPropagationPermissions"
      value       = tostring(var.enable_trusted_identity_propagation)
      is_editable = false
    },
  ]
}
