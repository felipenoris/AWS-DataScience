# Inputs. The first six arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py production probes) - region and env for Stage 2's standing
# reasons, zone_ids because the AZ choice lives in scripts/tfhygiene/backend.py (D9),
# account_folder because the remote-state key is keyed by the account FOLDER, and peer_cidrs
# because an address range written in a .tf file is a copy of the allocation table that
# nothing keeps in step (Lesson 14).

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
  description = "The two AZ zone ids subnets anchor on (step 1.5, D9). BOTH interfaces of the target land in the FIRST entry: a secondary ENI must sit in the same AZ as the instance it attaches to, which is the constraint that makes this a selection rather than a preference."
  type        = list(string)
  nullable    = false
}

variable "account_folder" {
  description = "This slice's terraform-live/ folder name - the first path segment of every state key. Consumed by the remote-state read of foundation/."
  type        = string
  nullable    = false
}

variable "peer_cidrs" {
  description = "Every SOURCE account's whole VPC range (scripts/tfhygiene/backend.py PROBE_PEERS), each admitted on the listener port. TWO of them, and the second is the point: Sandbox is the peering the Deliverables measure and Development is INT-09, the integration this stage claims to prove - one target host answers both. Each range is kept WHOLE deliberately: the permitted address and the forbidden one are both inside the peer, so this security group is constant across the pair and the ROUTE in the source account is the single variable the reading turns on."
  type        = list(string)
  nullable    = false
}

variable "listener_port" {
  description = "The GitLab port of the Deliverables - what a Sandbox client would really be reaching for in Production (D8, Stage 7). Served by python3's http.server, so the probe speaks HTTP on it; TLS is Stage 7's, and nothing here depends on the protocol."
  type        = number
  default     = 443
}

# THERE IS NO blocked_port VARIABLE HERE, and tflint is why the reasoning is written down
# rather than the variable kept: this slice admits exactly ONE port and denies everything
# else by having no other rule, so a second port number would be a declaration nothing reads.
# The blocked-port reading belongs to the side that attempts it - sandbox/probes/ - and what
# makes any port other than listener_port serve is the ingress rule below being the only one.

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
