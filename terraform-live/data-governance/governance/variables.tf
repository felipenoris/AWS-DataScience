# Inputs. All of them arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py data-governance governance).

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1). The domain and IAM Identity Center MUST share it (Stage 6 step 1.1) and neither can move afterwards."
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

variable "members" {
  description = "The accounts a project profile may provision into (SMUS_MEMBERS in scripts/tfhygiene/backend.py - D26/D35's decision). Keyed by account folder, carrying the profile an aliased provider resolves the account id from. Staging and Production are absent BY DESIGN (D28), not by omission."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "identity_profile" {
  description = "The CLI profile for the Identity account, used by ONE read-only aliased provider: resolving the sso-group-* names in local.project_profiles to the group ids the CREATE_PROJECT_FROM_PROJECT_PROFILE grants take. IdC is delegated to Identity (Stage 2 step 5), so the directory cannot be read from Data Governance; the value arrives from the generated tfvars (PROFILES in scripts/tfhygiene/backend.py), never as a literal here."
  type        = string
  nullable    = false
}

variable "profiles_enabled" {
  description = "false until EVERY member account's association has been accepted (SMUS_ASSOCIATED in backend.py). true is the pass 2c apply: the two project profiles, whose environment configurations name blueprints that must already be configured in the target account."
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "The SMUS domain name. One domain for the whole design (D26) - the plural is the thing INT-12's forbidden fallback would create."
  type        = string
  default     = "awsds-studio"
}

variable "idle_timeout_minutes" {
  description = "Stage 6 step 8.1 - how long a space may sit idle before SMUS shuts the app down. D11 is a property of the design, not of the user's habits: an open JupyterLab bills at ~USD 0.050/h whether anyone is typing in it (docs/PRICING.md 8)."
  type        = number
  default     = 60
}

variable "max_idle_timeout_minutes" {
  description = "The ADMIN CEILING a project member cannot raise (Stage 6 step 8.1). The pair matters: idle_timeout_minutes is the default, this is the most a user may set it to, and without the second the first is a suggestion (Lesson 5)."
  type        = number
  default     = 120
}

variable "max_ebs_volume_size_gb" {
  description = "The per-space EBS ceiling (Stage 6 step 1.5). A stopped app still bills its volume, monthly, which is why this is locked rather than defaulted."
  type        = number
  default     = 100
}

variable "enable_trusted_identity_propagation" {
  description = "Stage 6 DECISION 2, and the recommendation is FOLLOW THE GRAIN STAGE 5 CHOSE. Stage 5 decision 6 put the entitlement grain at the assumable role/project (docs/GOVERNANCE.md §'The grain'), and TIP's documented cost is that REMOTE ACCESS STOPS WORKING - so false is the setting that matches the grain already decided. Flipping it to true is a decision that re-opens Stage 5 decision 6, not a tuning knob."
  type        = bool
  default     = false
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
  default     = "stage-06"
}
