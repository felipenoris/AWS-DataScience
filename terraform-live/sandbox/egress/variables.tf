# Inputs, most of them from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py <account> egress): region and env for Stage 2's standing reasons,
# zone_ids because the AZ choice lives in scripts/tfhygiene/backend.py (D9), and account_folder
# because the remote-state key is keyed by the account folder, which no .tf file may re-derive
# from the env token (Lesson 14).

variable "region" {
  description = "AWS region for this slice. No default: see the note above."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> NAME TOKEN of docs/plan/conventions.md - what goes into a resource name."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "dev", "data", "staging", "prod", "org"], var.env)
    error_message = "env must be one of the six name tokens in docs/plan/conventions.md."
  }
}

variable "environment_tag" {
  description = "The Environment TAG value - the third vocabulary."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "development", "data", "staging", "production", "org"], var.environment_tag)
    error_message = "environment_tag must be one of the six tag values in docs/plan/conventions.md."
  }
}

variable "zone_ids" {
  description = "The two AZ zone ids subnets anchor on (step 1.5, D9). The FIRST entry is where this slice's single-AZ resources land - a selection among authored zones, made in one place."
  type        = list(string)
  nullable    = false
}

variable "account_folder" {
  description = "This slice's terraform-live/ folder name - the first path segment of every state key (scripts/tfhygiene/backend.py backend_values). Consumed by the remote-state read of foundation/."
  type        = string
  nullable    = false
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy."
  type        = string
  default     = "AWS-DataScience"
}

variable "owner" {
  description = "Owner tag - an sso-group-* GROUP, never a person (docs/plan/conventions.md)."
  type        = string
  default     = "sso-group-infrastructure"
}

variable "cost_center" {
  description = "CostCenter tag - the stage that created the resource."
  type        = string
  default     = "stage-03"
}

# Stage 6c step 5.3, the user's decision of 2026-09-06. Neither generated nor authored in a tfvars:
# it arrives from the environment as `TF_VAR_optional_service_groups`, threaded by
# `make up ENV=sandbox GROUPS=bedrock,emr`. Empty is the default and the decision - an apply that
# does not name a group creates no optional endpoint, so a family nobody is using that day costs
# nothing.
#
# It comes from the environment rather than a tracked tfvars because it is a property of one apply,
# not of a standing shape somebody should review in git history. A tracked file would have to be
# edited back, and a flag left on in a file is the failure mode the empty default exists to avoid.
# The closed list of names lives in the module, where the group map is.
variable "optional_service_groups" {
  description = "Optional endpoint families for this apply: bedrock, emr (mwaa is reserved and empty). Empty by default. Set with `make up ENV=sandbox GROUPS=bedrock,emr`; each endpoint is ~USD 0.010/h while the slice is up."
  type        = list(string)
  default     = []
}
