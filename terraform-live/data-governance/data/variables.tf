# Inputs. The first three arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py data-governance data) - region and env for Stage 2's standing
# reasons - and so do the three maps, because profile names live in the PROFILES table of
# scripts/tfhygiene/backend.py and may be a literal in no .tf file (Lesson 14).

variable "region" {
  description = "AWS region for this slice. No default: see the note above."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> NAME TOKEN of docs/plan/conventions.md - what goes into a resource name. 'data' for this account."
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

variable "consumers" {
  description = "Profile + env token per consumer account (INT-03's N+2, minus Production until Stage 9), derived in scripts/tfhygiene/backend.py - never authored here. Consumed twice: the terraform_remote_state reads of each consumer's foundation/ (the [P] S3 gateway-endpoint id, INT-05's anchor), and the aliased providers that resolve each account id for the drop-box statements."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "vpn_homes" {
  description = "The accounts playing the VPN-home role (VPN_HOMES in scripts/tfhygiene/backend.py) - one Elastic IP each, read from that account's foundation/ state. The aws:SourceIp branch of the perimeter deny (step 1.3, D18) is built from this list, per D35."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "producers" {
  description = "The account whose job role empties the drop-box (D25, INT-10) - production, resolved to an id by an aliased provider. The role itself (awsds-prod-job-exec) does not exist until Stage 9; the statements name it by ArnLike condition, which S3 does not validate - a nonexistent Principal ARN would reject the whole policy."
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
  default     = "stage-05"
}
