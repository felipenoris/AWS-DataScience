# Inputs. The first six arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py development probes) - region and env for Stage 2's standing
# reasons, zone_ids because the AZ choice lives in scripts/tfhygiene/backend.py (D9),
# account_folder because the remote-state key is keyed by the account FOLDER, and peer_cidrs
# because an address range written in a .tf file is a copy of the allocation table that
# nothing keeps in step (Lesson 14).
#
# WHAT IS DELIBERATELY NOT AN INPUT: the target's addresses. This slice reaches Production by
# NAME, in a private zone pass 2 associated with this VPC - so no id crosses the account
# boundary and nothing is pasted.

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
  description = "The two AZ zone ids subnets anchor on (step 1.5, D9). Which one the probe lands in is zone_index below."
  type        = list(string)
  nullable    = false
}

variable "zone_index" {
  description = "Which authored zone the probe lands in. THE READING IS AZ-AGNOSTIC and that is measured, not assumed: both private route tables carry the same two INT-09 peering routes and the same NAT default, and the peer routes back to both private ranges. It exists for one reason: RunInstances answers Server.InsufficientInstanceCapacity per AZ and per instance type, and a probe blocked by a transient shortage in one zone should move rather than wait."
  type        = number
  default     = 0

  validation {
    condition     = var.zone_index >= 0 && var.zone_index < length(var.zone_ids)
    error_message = "zone_index must be an index into zone_ids."
  }
}

variable "account_folder" {
  description = "This slice's terraform-live/ folder name - the first path segment of every state key. Consumed by the remote-state read of foundation/."
  type        = string
  nullable    = false
}

variable "peer_cidrs" {
  description = "Every TARGET account VPC range this slice reaches (scripts/tfhygiene/backend.py PROBE_PEERS) - one here, Production. Each is kept WHOLE deliberately: the permitted address and the forbidden one are both inside it, so this security group is constant across the pair and the ROUTE is the single variable the reading turns on."
  type        = list(string)
  nullable    = false
}

variable "target_name" {
  description = "The target's name in the peer account's private zone - the permitted address, in a tier this account routes to over INT-09."
  type        = string
  default     = "probe.prod.internal"
}

variable "target_forbidden_name" {
  description = "The SAME host's second interface, in a tier this account holds no route to. That this name RESOLVES and still does not connect is the reading: resolution proves the zone association reaches THIS VPC too - the half of the DNS Deliverable a Sandbox host cannot answer - and proves the host is known, so only the route is left to explain the silence."
  type        = string
  default     = "probe-isolated.prod.internal"
}

variable "listener_port" {
  description = "The GitLab port the target listens on - must match production/probes' listener_port."
  type        = number
  default     = 443
}

variable "blocked_port" {
  description = "Any port the target does NOT admit, which is every port but listener_port. The packet reaches the ENI and is dropped by the group, writing a REJECT flow-log record; the forbidden ADDRESS produces no record at all because the packet never leaves this account."
  type        = number
  default     = 8080

  validation {
    condition     = var.blocked_port != var.listener_port
    error_message = "blocked_port must differ from listener_port - equal, the reading measures nothing."
  }
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
