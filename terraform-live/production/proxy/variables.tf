# Inputs, all generated (./scripts/gen-tfvars.py production proxy), none authored here: region and
# env for Stage 2's standing reasons, zone_ids because the AZ choice lives in
# scripts/tfhygiene/backend.py (D9), account_folder because the remote-state key is built from the
# account folder, and rfc1918_cidrs because the private address space appears in the tunnel's
# forward rules with the opposite polarity and the two may not drift apart.

variable "region" {
  description = "AWS region for this slice. No default: see the note above."
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

# The same ranges the tunnel forwards to, used the other way round (6c steps 4.7/4.8): here they
# are denied as destinations, and that deny is the single line standing between an explicit proxy
# and an L7 bridge between VPCs peering keeps apart. Generated from one constant so the two lists
# cannot part company (Lesson 51).
variable "rfc1918_cidrs" {
  description = "The private address space - denied as a proxy destination. Generated; never authored here."
  type        = list(string)
  nullable    = false
}

variable "zone_index" {
  description = "Which authored zone this host lands in. Everything it consumes is AZ-free - the Elastic IP, the security group and the internet gateway all belong to the VPC - so this is a one-variable retry when nano capacity is short in a zone, which Stage 3 measured rather than anticipated."
  type        = number
  default     = 0
}

variable "instance_type" {
  description = "The proxy's size. t3.micro (1 GiB) at a measured 0.0104 USD/h (docs/PRICING.md 8; Lesson 6 - the rate is measured, never reasoned). The size is decided by the build, not by the steady state: a forward proxy that relays CONNECT and caches nothing is a socket pump and would run on a nano forever - but `dnf install squid jq amazon-cloudwatch-agent` will not fit on one. Measured 2026-09-06, twice and with opposite outcomes: the first proxy host installed fine, the second was OOM-killed mid-resolve with the kernel naming it (`Out of memory: Killed process (dnf)`) on a host reporting 415 MiB usable. So the nano is not too small, it is marginal - which is worse, because it boots most of the time and the estate's single internet exit is the wrong place to keep a coin-flip. Every admitted value is x86_64 because main.tf pins the AL2023 x86_64 AMI, and an AMI is specific to its architecture: a t4g is not a same-shape alternative, EC2 refuses the request. Unlike the VPN host this slice has no tracked size file, deliberately - nobody works on the proxy, so there is no reason to switch it up for a session."
  type        = string
  default     = "t3.micro"

  validation {
    condition     = contains(["t3.nano", "t3.micro", "t3.small"], var.instance_type)
    error_message = "instance_type must be one of t3.nano, t3.micro, t3.small - x86_64, matching the AMI main.tf pins."
  }
}

# A `cron()` expression and not `rate(30 minutes)`, because the API refuses the combination
# (measured 2026-09-06): `ApplyOnlyAtCronInterval is not supported for Rate Schedule
# associations`. That flag keeps the association from firing at creation time, seconds after
# RunInstances, onto a host still running `dnf install` - a run that cannot succeed and leaves a
# `Failed` association as a working proxy's first impression. `0/30` is the same half-hourly
# cadence, at predictable wall-clock times.
variable "reconfigure_schedule" {
  description = "How often State Manager re-renders the allow-lists onto the running host (step 4.10). Half-hourly is the trade the step names: an allow-list edit is an apply plus at most one interval, against no write API from the laptop, no host replacement and no estate-wide outage. Must be a cron() expression: apply_only_at_cron_interval, which is what stops the boot race, is rejected by the API on a rate() schedule."
  type        = string
  default     = "cron(0/30 * * * ? *)"

  validation {
    condition     = startswith(var.reconfigure_schedule, "cron(")
    error_message = "must be a cron() expression - the API rejects apply_only_at_cron_interval on a rate() schedule, and without that flag the association fires at creation onto a host that has not finished booting."
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
  default     = "stage-06c"
}
