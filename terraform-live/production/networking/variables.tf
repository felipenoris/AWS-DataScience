# Inputs. The first six arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py production foundation) - region and env for Stage 2's standing
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

# THE `peers` MAP - and at 1.2 this slice deliberately had none, because nothing consumed it.
# Step 2.5 gave it a consumer: the REVERSED zone authorizations. Each spoke owns a child zone
# under the estate apex and must authorize this VPC on it, and the shape peers.tf already uses -
# the hub acting AS each spoke through an aliased provider - makes both halves of a cross-account
# handshake one apply. That needs a profile per account, which is what this carries. 3.1 replaces
# the shape with the peering matrix; the need survives.
variable "peers" {
  description = "Profile, env token and VPC name suffix per VPC-bearing account. Generated in scripts/tfhygiene/backend.py; consumed here by the aliased providers of step 2.5's reversed zone authorizations."
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

# Stage 6c pass 2 - the three Production VPC slices read each other's zone ids and VPC ids, so
# every one of them needs the folder its state keys are built from (backend.py backend_values).
variable "account_folder" {
  description = "This slice's terraform-live/ folder name - the first path segment of every state key."
  type        = string
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

# Stage 6c step 4.1 - the WireGuard client range, generated from scripts/tfhygiene/backend.py's
# WIREGUARD_PEER_CIDR, which is where every address literal in this project lives (Stage 3
# decision 1). It arrives here and not only at the vpn/ slice because D38 puts the tunnel
# endpoint and the proxy in ONE VPC: step 4.7 stops masquerading packets bound for the proxy, so
# this range becomes a source the proxy's security group must admit and a destination the hub's
# public route table must send at the WireGuard host. Emitted on VPN_HOST_SLICE, which is
# deliberately not VPN_HOMES - see that tuple's comment.
variable "wireguard_peer_cidr" {
  description = "The WireGuard client range. Generated - never authored here."
  type        = string
  nullable    = false
}
