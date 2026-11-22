# Inputs. All of them but the debug window arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py production sagemaker).

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> name token of docs/plan/conventions.md - what goes into a resource name."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "dev", "data", "staging", "prod", "org"], var.env)
    error_message = "env must be one of the six name tokens in docs/plan/conventions.md."
  }
}

variable "environment_tag" {
  description = "The Environment tag value - the third vocabulary."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "development", "data", "staging", "production", "org"], var.environment_tag)
    error_message = "environment_tag must be one of the six tag values in docs/plan/conventions.md."
  }
}

variable "account_folder" {
  description = "This account's terraform-live/ folder - the state keys of foundation/ and registry/ are built from it, never re-derived from the env token (Lesson 14)."
  type        = string
  nullable    = false
}

variable "lake" {
  description = "The account that owns the lake (DATA_LAKE in scripts/tfhygiene/backend.py), keyed by account folder, carrying the profile and the env token its state bucket name is built from. Read once, for the drop-box bucket, its prefix and the lake data key the job role's pickup statements name (Stage 5a step 1.4's other half)."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "readers" {
  description = "The accounts whose data scientists read model status (Stage 9 decision 10): SMUS_MEMBERS in scripts/tfhygiene/backend.py, keyed by account folder, carrying the profile an aliased provider resolves the account id from. Each key needs an alias in providers.tf."
  type        = map(object({ profile = string, env = string }))
  nullable    = false

  validation {
    condition     = toset(keys(var.readers)) == toset(["sandbox"])
    error_message = "readers must hold exactly the keys providers.tf has an alias for (sandbox): a new reader account needs its alias and its identity read first."
  }
}

# ------------------------------------------------------------- the escape hatch (step 6.1)
#
# Not generated: the window is the deployment manager's approval, recorded in the stage log and
# applied by hand (decision 4). The default sits in the past, so the role exists and nobody can
# assume it. Opening a window is `-var debug_window_end=<the approved end>` on one apply; closing
# it is the next apply without the flag.
variable "debug_window_end" {
  description = "End of the approved debugging window, RFC 3339 in UTC (e.g. 2026-11-02T18:00:00Z). The debug role's trust admits the persona only while aws:CurrentTime is earlier. The default is in the past: closed at rest."
  type        = string
  default     = "2026-01-01T00:00:00Z"
  nullable    = false

  validation {
    condition     = can(timecmp(var.debug_window_end, "2026-01-01T00:00:00Z"))
    error_message = "debug_window_end must be an RFC 3339 timestamp, e.g. 2026-11-02T18:00:00Z."
  }
}

# ------------------------------------------------------------------- the job log groups (3.1)
variable "log_retention_days" {
  description = "Retention on the job log groups this slice pre-creates. 30 days, Stage 3 decision 3's figure for the flow logs, which the SMUS and warehouse groups also carry."
  type        = number
  default     = 30
}

variable "zone_ids" {
  description = "The two AZ zone ids subnets anchor on (D9). The first entry is where the Glue connection's subnet is selected - a selection among authored zones, made in one place."
  type        = list(string)
  nullable    = false
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy."
  type        = string
  default     = "AWS-DataScience"
}

variable "owner" {
  description = "Owner tag - an sso-group-* group, never a person (docs/plan/conventions.md)."
  type        = string
  default     = "sso-group-infrastructure"
}

variable "cost_center" {
  description = "CostCenter tag - the stage that created the resources."
  type        = string
  default     = "stage-09"
}
