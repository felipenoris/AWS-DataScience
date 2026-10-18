# Inputs. region, env, environment_tag and account_folder arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py sandbox observability); alert_email from the
# untracked alerts.auto.tfvars the user writes; the quota list and its threshold are this slice's own.

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> name token of docs/plan/conventions.md - what goes into a resource name. Never *the* sandbox: D35 vends one per business unit."
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
  description = "The terraform-live/ folder of this account: the state keys of foundation/ and warehouse/ are built from it, never from the env token (Lesson 14)."
  type        = string
  nullable    = false
}

# Who awsds-<env>-alerts reaches, the same variable and the same file as production/foundation/'s
# (Stage 8 decision 5). Never committed and never generated.
variable "alert_email" {
  description = "The address awsds-<env>-alerts sends to. Unset, the topic exists with no subscriber, which a check block reports on every plan."
  type        = string
  default     = null
}

# Step 9.2's quotas, read 2026-10-18: the SageMaker types October's bill (days 1-17) and the 14 days of
# usage metrics show in use, at most 3 of 10 apps of one type; and the VPC's interface endpoints, at
# most 24 of 50. Each is read back from Service Quotas by its code, and its name is compared with
# `name` (Lesson 38). A type that starts being used joins this map at the stage that uses it.
variable "quotas" {
  description = "The quotas alarmed at quota_alarm_percent, keyed by the alarm's suffix: the Service Quotas service and quota code, words the quota's name carries, and whether the usage is per VPC (this account's foundation/ VPC)."
  type = map(object({
    service_code = string
    quota_code   = string
    name         = string
    per_vpc      = optional(bool, false)
  }))

  default = {
    "jupyterlab-ml-t3-medium" = {
      service_code = "sagemaker"
      quota_code   = "L-71FAF417"
      name         = "jupyterlab apps running on ml.t3.medium"
    }
    "jupyterlab-ml-t3-large" = {
      service_code = "sagemaker"
      quota_code   = "L-2733D4D5"
      name         = "jupyterlab apps running on ml.t3.large"
    }
    "codeeditor-ml-t3-large" = {
      service_code = "sagemaker"
      quota_code   = "L-656A17FA"
      name         = "codeeditor apps running on ml.t3.large"
    }
    "processing-ml-t3-medium" = {
      service_code = "sagemaker"
      quota_code   = "L-0CE343FE"
      name         = "ml.t3.medium for processing job usage"
    }
    "interface-endpoints-per-vpc" = {
      service_code = "vpc"
      quota_code   = "L-29B6F2EB"
      name         = "interface vpc endpoints per vpc"
      per_vpc      = true
    }
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
