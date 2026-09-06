# Inputs. The first six arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py development foundation) - region and env for Stage 2's standing
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
  description = "Profile, env token and VPC name suffix per VPC-bearing account (Stage 3 pass 2; the suffix arrived at 6c step 0.6). Derived in scripts/tfhygiene/backend.py from the same tables as everything else - never authored here. The suffix is how a requester builds the accepter's VPC Name tag: 6c step 1.1 re-labelled Production's to awsds-prod-shared-vpc, and a lookup that assumed awsds-<env>-vpc stopped resolving."
  type        = map(object({ profile = string, env = string, name_suffix = string }))
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

# Stage 6c step 0.4 - which VPC inside the account this slice builds. Empty for an account with
# one VPC (every account but Production); generated per (account, slice) by
# scripts/tfhygiene/backend.py, never authored here.
variable "name_suffix" {
  description = "Distinguishes VPCs inside one account: names become awsds-<env>-<suffix>-*. Empty for a single-VPC account."
  type        = string
  default     = ""
  nullable    = false
}

# Stage 6c steps 0.6 / 3.1 - every peering this slice is an end of, generated from ONE list in
# scripts/tfhygiene/backend.py so a requester and an accepter can never disagree about which
# peerings exist. A slice can hold both roles: production/foundation requests one and accepts
# another. `same_account` decides the SHAPE - within an account a single resource with
# auto_accept is the whole handshake; across one it is a requester, an accepter and two applies.
variable "peerings" {
  description = "The peering matrix, projected onto this slice. Generated - never authored here."
  type = list(object({
    key              = string
    role             = string
    peer_account     = string
    peer_slice       = string
    peer_cidr        = string
    peer_profile     = string
    peer_env         = string
    peer_name_suffix = string
    same_account     = bool
  }))
  nullable = false
}
