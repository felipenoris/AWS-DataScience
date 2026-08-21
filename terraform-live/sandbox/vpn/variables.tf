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
  description = "Which authored zone the WireGuard host lands in. Everything it consumes is AZ-free - the Elastic IP, the security group, the internet gateway and the S3 gateway endpoint all belong to the VPC - so this is a one-variable retry when nano capacity is short in a zone, which was MEASURED during Stage 3 rather than anticipated."
  type        = number
  default     = 0
}

variable "instance_type" {
  description = "THE HOST'S SIZE, SELECTED PER APPLY - the first of the two knobs this slice adds to the wireguard module (root_volume_size below is the second, and it is the one that does NOT go both ways), so the tunnel can be run either as a forwarder or as a machine with room to work in, without a code change either way. t3.nano is D4's shape and the default; t3.medium (2 vCPU, 4 GiB) is the larger option; t3.micro is section S5's documented capacity fallback, kept here so the fallback is a value rather than an edit. EVERY ALLOWED VALUE IS x86_64 ON PURPOSE, AND THE LIST DOES NOT DECIDE THAT - the module pins the AL2023 x86_64 AMI (it pinned the arm64 one until 2026-08-20, when the user moved the host off Graviton), and an AMI is specific to its processor architecture, so t4g.medium is not a same-shape alternative to t3.medium: EC2 refuses the request. THE DIRECTION MATTERS WHEN THIS LIST IS EVER EDITED: the image decides the family and this list follows it, so a different family here is a MODULE change first - a different SSM parameter, a REPLACED instance and a re-run of the user data - and never a value somebody adds to the closed list below. HOW A SELECTION IS MADE: not here, and not on the command line, but in the TRACKED FILE BESIDE THIS ONE - instance_type.auto.tfvars, the second exception to the wholesale *.tfvars ignore and the first one .gitignore names outright. Assigning there overrides this default; COMMENTING THE ASSIGNMENT OUT falls back to it. The .auto. in the name is load-bearing: Terraform reads the file by itself, so both directions are a complete `AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/vpn apply` with no -var-file to append and no flag anybody can forget. WHAT THIS DEFAULT THEREFORE IS: the value that governs whenever nothing is assigned - so it is also what a FRESH CLONE builds, and what the cost tables are written against. Changing it is changing the baseline, which is a different act from switching the running host. The procedure is docs/plan/runbooks/vpn.md section S6."
  type        = string
  default     = "t3.nano"

  validation {
    # A CLOSED LIST, not a free-form string, and the failure it prevents is not a typo: the
    # module's AMI is x86_64, so a Graviton type is rejected by EC2 at apply time with an
    # architecture error - late, after a stop has already happened. Widening this list is a
    # decision that belongs with the reading of section S6's two pre-flight commands
    # (architecture, and whether the type is offered in the zone_index AZ), never a
    # convenience - and widening it ACROSS families is not a decision this file can take at
    # all, because the module's AMI would refuse it (see the description).
    condition     = contains(["t3.nano", "t3.micro", "t3.medium"], var.instance_type)
    error_message = "instance_type must be one of t3.nano, t3.micro or t3.medium - all x86_64, as the module's pinned AL2023 AMI requires (vpn.md section S6)."
  }
}

variable "root_volume_size" {
  description = "THE HOST'S DISK, IN GiB, SELECTED PER APPLY - the second knob this slice adds to the wireguard module, and the one that does NOT behave like instance_type. 8 GiB is the module's default and D4's shape: a host that only forwards packets needs the image and little else. A larger value is for a host that has to HOLD something - a working copy, a container image, a capture - which is the same reason t3.medium exists as a value above, applied to the other axis. WHERE THE SELECTION IS MADE: the same tracked file the type is selected in, instance_type.auto.tfvars beside this one, whose NAME is therefore now narrower than its contents - a rename would cost the .gitignore negation, check-tfvars-shape.py's SIZE constant and every path written about the file, and would buy what that file's header already buys. THE DIRECTION IS THE DIFFERENCE, and it is the one thing to read before assuming this knob mirrors the one above: an EBS volume GROWS in place - the provider issues ModifyVolume and does not even stop the instance - but EBS CANNOT SHRINK A VOLUME. Commenting the assignment out does not walk the disk back the way it walks the type back; it asks for a shrink, and going smaller is a host REPLACEMENT under Part K's rules. GROWING THE VOLUME IS ALSO NOT GROWING THE FILESYSTEM: the extra GiB reach the OS only when cloud-init's growpart runs, which is at BOOT - so a change made alongside an instance_type switch is picked up by the stop/start that switch performs, and a change made ALONE needs a reboot or a hand-run growpart + xfs_growfs (AL2023's root is xfs). AND IT IS A STANDING COST, unlike the type: EBS bills while the host is STOPPED, which is the deal a [D] slice makes. The procedure, the readings that prove the filesystem grew, and the cost arithmetic are docs/plan/runbooks/vpn.md section S6."
  type        = number
  default     = 8

  validation {
    # A BAND, not a closed list - what is being defended here is a floor and a bill, not an
    # architecture, so the instance_type validation's shape would be the wrong instrument.
    # FLOOR 8: EC2 refuses a root volume smaller than the snapshot of the AMI it restores, and
    # the module's pinned AL2023 x86_64 image ships an 8 GiB one - a refusal that arrives at
    # APPLY, after a plan that read clean. CEILING 128: at the us-west-2 gp3 rate of 0.08
    # USD/GB-mo (docs/PRICING.md 8) that is ~10.24 USD/month STANDING - it accrues whether or
    # not the host runs, and unlike an oversized instance type it cannot be given back, only
    # replaced away. So the ceiling is where a fat-fingered 640 (~51 USD/month, D12's entire
    # budget) is caught at PLAN time; raising it is a decision taken against that budget with
    # section S6's arithmetic in hand, never a convenience.
    condition     = var.root_volume_size >= 8 && var.root_volume_size <= 128
    error_message = "root_volume_size must be between 8 GiB (the AL2023 x86_64 image's snapshot, the floor EC2 accepts for a root volume) and 128 GiB (~10.24 USD/month standing at this region's gp3 rate; vpn.md section S6)."
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
