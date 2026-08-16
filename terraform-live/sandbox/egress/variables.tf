# Inputs. The first five arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py <account> egress) - region and env for Stage 2's standing
# reasons, zone_ids because the AZ choice lives in scripts/tfhygiene/backend.py (D9), and
# account_folder because the remote-state key is keyed by the account FOLDER, which no .tf
# file may re-derive from the env token (Lesson 14).

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
