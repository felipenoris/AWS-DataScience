# Inputs. All five arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py sandbox warehouse-compute). THERE IS NO CAPACITY VARIABLE HERE, and the
# absence is the design: base_capacity, max_capacity, the usage limit and the per-query ceiling are
# declared by sandbox/warehouse/ and read from its state. Two copies of one ceiling is Lesson 33,
# and the copy that would go stale is the one in the slice that gets destroyed every session.

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
  description = "The terraform-live/ folder this slice lives in - the first segment of every state key it reads."
  type        = string
  nullable    = false
}

variable "zone_ids" {
  description = "The account's AZ zone ids, in authored order. foundation/ reports its subnets as a map KEYED BY ZONE ID, so a subnet is selected by zone id and never by list position: an AZ NAME maps to a different physical zone in each account, while a zone id does not."
  type        = list(string)
  nullable    = false

  validation {
    condition     = length(var.zone_ids) >= 2
    error_message = "a workgroup needs at least two subnets in two Availability Zones (AWS, `Considerations when using Amazon Redshift Serverless`). D9 gives this estate exactly two."
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
  default     = "stage-05b"
}
