# Inputs, from TWO files - and one deliberate absence. The first five arrive from the
# generated, untracked terraform.auto.tfvars (./scripts/gen-tfvars.py sandbox vpn) - region
# and env for Stage 2's standing reasons, zone_ids because the AZ choice lives in
# scripts/tfhygiene/backend.py (D9), account_folder because the remote-state key is keyed by
# the account FOLDER, and peer_cidr because an address range written in a .tf file is a copy
# of the allocation table that nothing keeps in step (Lesson 14).
#
# `peers` ARRIVES FROM THE ONE FILE A PERSON WRITES: peers.auto.tfvars - TRACKED,
# deliberately, because the public halves are the network's authorization roster and a
# roster benefits from review and history; ./scripts/check-tfvars-shape.py holds it to that
# shape. THE ABSENCE IS THE HOST'S PRIVATE KEY (third design review, 2026-08-16): it is not
# a variable of this slice at all - it lives in foundation/'s [P] Secrets Manager secret,
# enrolled by the user (step 4.3) and fetched by the instance at first boot, so it crosses
# neither tfvars nor state nor user data. Keys are still generated on a laptop and never by
# Terraform (steps 4.1, 4.3): a tls_private_key resource would both put the key in state and
# make it something Terraform rotates on its own schedule. README.md beside this file has
# the roster's shape and the enrollment command.

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
  description = "The two AZ zone ids subnets anchor on (Stage 3 step 1.5, D9). Which one the host lands in is zone_index below."
  type        = list(string)
  nullable    = false
}

variable "zone_index" {
  description = "Which authored zone the WireGuard host lands in. Everything it consumes is AZ-free - the Elastic IP, the security group, the internet gateway and the S3 gateway endpoint all belong to the VPC - so this is a one-variable retry when t4g.nano capacity is short in a zone, which was MEASURED during Stage 3 rather than anticipated."
  type        = number
  default     = 0
}

variable "instance_type" {
  description = "THE HOST'S SIZE, SELECTED PER APPLY - the only knob this slice adds to the wireguard module, so the tunnel can be run either as a forwarder or as a machine with room to work in, without a code change either way. t4g.nano is D4's shape and the default; t4g.medium (2 vCPU, 4 GiB) is the larger option; t4g.micro is section S5's documented capacity fallback, kept here so the fallback is a value rather than an edit. EVERY ALLOWED VALUE IS arm64 ON PURPOSE - the module pins the AL2023 arm64 AMI, and an AMI is specific to its processor architecture, so t3.medium is not a same-shape alternative to t4g.medium: EC2 refuses the request. HOW A SELECTION IS MADE: not here, and not on the command line, but in the TRACKED FILE BESIDE THIS ONE - instance_type.auto.tfvars, the second exception to the wholesale *.tfvars ignore and the first one .gitignore names outright. Assigning there overrides this default; COMMENTING THE ASSIGNMENT OUT falls back to it. The .auto. in the name is load-bearing: Terraform reads the file by itself, so both directions are a complete `AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/vpn apply` with no -var-file to append and no flag anybody can forget. WHAT THIS DEFAULT THEREFORE IS: the value that governs whenever nothing is assigned - so it is also what a FRESH CLONE builds, and what the cost tables are written against. Changing it is changing the baseline, which is a different act from switching the running host. The procedure is docs/plan/runbooks/vpn.md section S6."
  type        = string
  default     = "t4g.nano"

  validation {
    # A CLOSED LIST, not a free-form string, and the failure it prevents is not a typo: the
    # module's AMI is arm64, so an x86 type is rejected by EC2 at apply time with an
    # architecture error - late, after a stop has already happened. Widening this list is a
    # decision that belongs with the reading of section S6's two pre-flight commands
    # (architecture, and whether the type is offered in the zone_index AZ), never a
    # convenience.
    condition     = contains(["t4g.nano", "t4g.micro", "t4g.medium"], var.instance_type)
    error_message = "instance_type must be one of t4g.nano, t4g.micro or t4g.medium - all arm64, as the module's pinned AL2023 AMI requires (vpn.md section S6)."
  }
}

variable "account_folder" {
  description = "This slice's terraform-live/ folder name - the first path segment of every state key. Consumed by the remote-state read of foundation/."
  type        = string
  nullable    = false
}

variable "peer_cidr" {
  description = "The WireGuard client range, from scripts/tfhygiene/backend.py through the generated tfvars (step 4.2). NOT chosen here."
  type        = string
  nullable    = false
}

# ------------------------------------------------- the one hand-written file, one variable

variable "peers" {
  description = "One entry per PERSON PER DEVICE, keyed by a name that reads in `wg show` output. `public_key` is the device's public half, generated ON the device (step 4.1: on a laptop the silent `(umask 077 && wg genkey | tr -d '\n' > d-private.key) && wg pubkey < d-private.key > d-public.key`, run outside this repository; on a phone, by the WireGuard app itself - either way the private half never leaves the device and never enters this repository). `host` is the device's address inside peer_cidr, authored so that revoking a device cannot renumber anybody else. The SERVER's key has no variable here at all: see the header."
  type = map(object({
    public_key = string
    host       = number
  }))
  nullable = false
}

# ------------------------------------------------------------------------- the five tags

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
  default     = "stage-04"
}
