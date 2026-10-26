# Inputs. All of them arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py data-governance publishing).

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
    condition     = var.env == "data"
    error_message = "publishing/ is the lake account's slice alone (D22: the lake is in Data Governance)."
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

# ------------------------------------------------------------------------------- the network
#
# The allocation is backend.VPC_CIDRS's ("data-governance", "publishing") row, which no .tf file
# repeats (Stage 3 decision 1).

variable "vpc_cidr" {
  description = "This account's /16 from scripts/tfhygiene/backend.py's VPC_CIDRS."
  type        = string
  nullable    = false
}

variable "zone_ids" {
  description = "The two AZ zone ids the subnets anchor on (backend.ZONE_IDS)."
  type        = list(string)
  nullable    = false
}

variable "peerings" {
  description = "The peering matrix, projected onto this slice. Generated - never authored here, and empty: main.tf's check holds it there."
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

# ------------------------------------------------------------------- the lake and the domain
#
# Both are this account's own slices. The maps carry the profile the read runs as, so no profile
# literal sits in a .tf file (Lesson 14).

variable "lake" {
  description = "The account that owns the governed lake (DATA_LAKE in scripts/tfhygiene/backend.py) - read for the Lake Formation-registered bucket ARNs the D13 boundary excludes, the drop-box prefix and the lake data key."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "domain" {
  description = "The account that owns the SMUS domain (SMUS_DOMAIN in scripts/tfhygiene/backend.py). Read only on the second apply, for the domain id the blueprint configuration names."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "blueprints_enabled" {
  description = "false until backend.LAKE_PUBLISHERS carries this account (Stage 6f step 11.3). true is the second apply: the Tooling configuration and its CREATE_ENVIRONMENT_FROM_BLUEPRINT grant."
  type        = bool
  default     = false
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
  default     = "stage-06f"
}
