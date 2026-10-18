# Inputs. region, env, environment_tag and account_folder arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py production observability); the thresholds are this
# slice's own.

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
  description = "The terraform-live/ folder of this account: the state keys of foundation/, networking/ and workloads/ are built from it, never from the env token (Lesson 14)."
  type        = string
  nullable    = false
}

# Measured from /awsds/prod/proxy on 2026-10-18 (Logs Insights, 2026-09-07 to 2026-10-16): September
# refused 1,597 of 12,829 requests, ten of its hours at 50 or more, all while the allow-lists were
# being built; October refused 53 of 10,919 and no hour reached 50. So 50 in one hour fires on a
# build-out like September's and stays quiet through ordinary work.
variable "refusal_threshold" {
  description = "Proxy refusals (HTTP 403) in one hour that page the operator: the allow-list is behind the work (Stage 12 step 2.2)."
  type        = number
  default     = 50

  validation {
    condition     = var.refusal_threshold >= 1
    error_message = "refusal_threshold is a count of refused requests per hour, at least 1."
  }
}

variable "quota_alarm_percent" {
  description = "The share of a quota at which its alarm fires (Stage 12 step 9.2)."
  type        = number
  default     = 80

  validation {
    condition     = var.quota_alarm_percent > 0 && var.quota_alarm_percent < 100
    error_message = "quota_alarm_percent is a percentage strictly between 0 and 100."
  }
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
  description = "CostCenter tag - the stage that created the resource."
  type        = string
  default     = "stage-12"
}
