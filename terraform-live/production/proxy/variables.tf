# Inputs, all generated (./scripts/gen-tfvars.py production proxy). Nothing here is authored:
# region and env for Stage 2's standing reasons, zone_ids because the AZ choice lives in
# scripts/tfhygiene/backend.py (D9), account_folder because the remote-state key is built from
# the account FOLDER, and rfc1918_cidrs because the private address space appears in the tunnel's
# forward rules with the OPPOSITE polarity and the two may not drift apart.

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
  description = "The two AZ zone ids subnets anchor on (Stage 3 step 1.5, D9). Which one this host lands in is zone_index below."
  type        = list(string)
  nullable    = false
}

variable "account_folder" {
  description = "This slice's terraform-live/ folder name - the first path segment of every state key."
  type        = string
  nullable    = false
}

# THE SAME RANGES THE TUNNEL FORWARDS TO, USED THE OTHER WAY ROUND (6c steps 4.7/4.8). Here they
# are DENIED as destinations, and that deny is the single line standing between an explicit proxy
# and an L7 bridge between VPCs that peering deliberately keeps apart - D38's own hole, if it
# were missing. Generated from one constant so the two lists cannot part company (Lesson 51).
variable "rfc1918_cidrs" {
  description = "The private address space - denied as a proxy DESTINATION. Generated; never authored here."
  type        = list(string)
  nullable    = false
}

variable "zone_index" {
  description = "Which authored zone this host lands in. Everything it consumes is AZ-free - the Elastic IP, the security group and the internet gateway all belong to the VPC - so this is a one-variable retry when nano capacity is short in a zone, which Stage 3 MEASURED rather than anticipated."
  type        = number
  default     = 0
}

variable "instance_type" {
  description = "The proxy's size. t3.nano is the baseline and the measured rate the cost tables are written against (docs/PRICING.md 3, in this project's Region; Lesson 6 - the rate is measured, never reasoned). A forward proxy terminates TLS for nobody - it relays CONNECT - so it is a socket pump, and the shape that carries the tunnel carries this too. EVERY ADMITTED VALUE IS x86_64 because main.tf pins the AL2023 x86_64 AMI, and an AMI is specific to its architecture: a t4g is not a same-shape alternative, EC2 refuses the request. Unlike the VPN host this slice has no tracked size file, deliberately - nobody works ON the proxy, so there is no reason to switch it up for a session."
  type        = string
  default     = "t3.nano"

  validation {
    condition     = contains(["t3.nano", "t3.micro", "t3.small"], var.instance_type)
    error_message = "instance_type must be one of t3.nano, t3.micro, t3.small - x86_64, matching the AMI main.tf pins."
  }
}

variable "reconfigure_schedule" {
  description = "How often State Manager re-renders the allow-lists onto the running host (step 4.10). rate(30 minutes) is the trade the step names: an allow-list edit is an apply plus at most one interval, against no write API from the laptop, no host replacement and no estate-wide outage. Shorter buys little - a list changes rarely; longer makes an urgent removal feel broken."
  type        = string
  default     = "rate(30 minutes)"
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
  default     = "stage-06c"
}
