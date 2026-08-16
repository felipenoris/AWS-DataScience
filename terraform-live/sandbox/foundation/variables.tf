# Inputs. The first six arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py sandbox foundation) - region and env for Stage 2's standing
# reasons, vpc_cidr and zone_ids because the address allocation lives in
# scripts/tfhygiene/backend.py (Stage 3 decision 1) and may be a literal in no .tf file,
# and peers because the profile names live in the same module's PROFILES table (pass 2).

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

variable "vpc_cidr" {
  description = "This account's /16 from the allocation table (Stage 3 decision 1, step 1.2)."
  type        = string
  nullable    = false
}

variable "zone_ids" {
  description = "The two AZ zone ids subnets anchor on (step 1.5, D9)."
  type        = list(string)
  nullable    = false
}

variable "peers" {
  description = "Profile + env token per VPC-bearing account (Stage 3 pass 2), derived in scripts/tfhygiene/backend.py from the same tables as everything else - never authored here. Consumed by the aliased providers of the cross-account handshake; the self-row is emitted and unused."
  type        = map(object({ profile = string, env = string }))
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
