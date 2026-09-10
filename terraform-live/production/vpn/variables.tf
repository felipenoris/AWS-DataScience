# Inputs, from two files, and one deliberate absence. The generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py production vpn) supplies region and env for Stage
# 2's standing reasons, zone_ids because the AZ choice lives in scripts/tfhygiene/backend.py (D9),
# account_folder because the remote-state key is keyed by the account folder, and peer_cidr because
# an address range written in a .tf file is a copy of the allocation table that nothing keeps in
# step (Lesson 14).
#
# `peers` arrives from the one file a person writes, peers.auto.tfvars. It is tracked, because the
# public halves are the network's authorization roster and a roster benefits from review and
# history; ./scripts/check-tfvars-shape.py holds it to that shape.
#
# The host's private key is not a variable of this slice at all (third design review, 2026-08-16).
# It lives in networking/'s [P] Secrets Manager secret, enrolled by the user (step 4.3) and fetched
# by the instance at first boot, so it crosses neither tfvars nor state nor user data. Keys are
# generated on a laptop and never by Terraform (steps 4.1, 4.3): a tls_private_key resource would
# put the key in state and make it something Terraform rotates on its own schedule. README.md
# beside this file has the roster's shape and the enrollment command.

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
  description = "The two AZ zone ids subnets anchor on (Stage 3 step 1.5, D9). Which one the host lands in is zone_index below."
  type        = list(string)
  nullable    = false
}

variable "zone_index" {
  description = "Which authored zone the WireGuard host lands in. Everything it consumes is AZ-free - the Elastic IP, the security group, the internet gateway and the S3 gateway endpoint all belong to the VPC - so this is a one-variable retry when nano capacity is short in a zone, which was measured during Stage 3 rather than anticipated."
  type        = number
  default     = 0
}

variable "instance_type" {
  description = "The host's size, selected per apply - the first of the two knobs this slice adds to the wireguard module (root_volume_size below is the second, and it is the one that does not go both ways), so the tunnel can be run either as a forwarder or as a machine with room to work in, without a code change either way. t3.nano is D4's shape and the default; t3.medium (2 vCPU, 4 GiB) is the larger option; t3.micro is section S5's documented capacity fallback, kept here so the fallback is a value rather than an edit. Every allowed value is x86_64 on purpose, and the list does not decide that - the module pins the AL2023 x86_64 AMI (it pinned the arm64 one until 2026-08-20, when the user moved the host off Graviton), and an AMI is specific to its processor architecture, so t4g.medium is not a same-shape alternative to t3.medium: EC2 refuses the request. The direction matters when this list is ever edited: the image decides the family and this list follows it, so a different family here is a module change first - a different SSM parameter, a replaced instance and a re-run of the user data - and never a value somebody adds to the closed list below. How A selection is made: not here, and not on the command line, but in the tracked file beside this one - instance_type.auto.tfvars, an exception to the wholesale *.tfvars ignore and the first one .gitignore names outright. Assigning there overrides this default; commenting the assignment out falls back to it. The .auto. in the name is load-bearing: Terraform reads the file by itself, so both directions are a complete `AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/vpn apply` with no -var-file to append and no flag anybody can forget. What this default therefore is: the value that governs whenever nothing is assigned - so it is also what a fresh clone builds, and what the cost tables are written against. Changing it is changing the baseline, which is a different act from switching the running host. The procedure is docs/plan/runbooks/vpn.md section S6."
  type        = string
  default     = "t3.nano"
}

variable "root_volume_size" {
  description = "The host's disk, in GiB, selected per apply - the second knob this slice adds to the wireguard module, and the one that does not behave like instance_type. 8 GiB is the module's default and D4's shape: a host that only forwards packets needs the image and little else. A larger value is for a host that has to hold something - a working copy, a container image, a capture - which is the same reason t3.medium exists as a value above, applied to the other axis. Where the selection is made: the same tracked file the type is selected in, instance_type.auto.tfvars beside this one, whose name is therefore now narrower than its contents - a rename would cost the .gitignore negation, check-tfvars-shape.py's size constant and every path written about the file, and would buy what that file's header already buys. The direction is the difference, and it is the one thing to read before assuming this knob mirrors the one above: an EBS volume grows in place - the provider issues ModifyVolume and does not even stop the instance - but EBS cannot shrink A volume. Commenting the assignment out does not walk the disk back the way it walks the type back; it asks for a shrink, and going smaller is a host replacement under Part K's rules. Growing the volume is also not growing the filesystem: the extra GiB reach the OS only when cloud-init's growpart runs, which is at boot - so a change made alongside an instance_type switch is picked up by the stop/start that switch performs, and a change made alone needs a reboot or a hand-run growpart + xfs_growfs (AL2023's root is xfs). And it is A standing cost, unlike the type: EBS bills while the host is stopped, which is the deal a [D] slice makes. The procedure, the readings that prove the filesystem grew, and the cost arithmetic are docs/plan/runbooks/vpn.md section S6."
  type        = number
  default     = 8

  validation {
    # A band, not a closed list: what is defended here is a floor and a bill, not an architecture,
    # so the instance_type validation's shape would be the wrong instrument.
    # Floor 8: EC2 refuses a root volume smaller than the snapshot of the AMI it restores, and the
    # module's pinned AL2023 x86_64 image ships an 8 GiB one - a refusal that arrives at apply,
    # after a plan that read clean. Ceiling 128: at the us-west-2 gp3 rate of 0.08 USD/GB-mo
    # (docs/PRICING.md 8) that is ~10.24 USD/month standing - it accrues whether or not the host
    # runs, and unlike an oversized instance type it cannot be given back, only replaced away. The
    # ceiling is where a fat-fingered 640 (~51 USD/month, D12's entire budget) is caught at plan
    # time; raising it is a decision taken against that budget with section S6's arithmetic in hand.
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
  description = "The WireGuard client range, from scripts/tfhygiene/backend.py through the generated tfvars (step 4.2). Not chosen here."
  type        = string
  nullable    = false
}

# ------------------------------------------- the tunnel's IPv6 prefix and the peer roster

variable "peer_cidr_v6" {
  description = "The tunnel's IPv6 ULA prefix, generated beside `peer_cidr` from the one allocation table (2026-09-07). It carries no traffic - every VPC here is IPv4-only - and exists so that `AllowedIPs = ::/0` in a client config is real: without an IPv6 address on the interface, `wg-quick` installs no IPv6 route and the device's IPv6 leaves by its own uplink, outside the tunnel, the proxy and the access log."
  type        = string
  nullable    = false
}

variable "peers" {
  description = "One entry per person per device, keyed by a name that reads in `wg show` output. `public_key` is the device's public half, generated on the device (step 4.1: on a laptop the silent `(umask 077 && wg genkey | tr -d '\n' > d-private.key) && wg pubkey < d-private.key > d-public.key`, run outside this repository; on a phone, by the WireGuard app itself - either way the private half never leaves the device and never enters this repository). `host` is the device's address inside peer_cidr, authored so that revoking a device cannot renumber anybody else. The server's key has no variable here at all: see the header."
  type = map(object({
    public_key = string
    host       = number
  }))
  nullable = false
}

# ------------------------------------------------------------------------------ the tags

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
  default     = "stage-04"
}

# Stage 6c step 4.7 - the private address space, generated from scripts/tfhygiene/backend.py's
# RFC1918_CIDRS. It is a standard constant rather than one of this project's allocations, which is
# why it does not live beside vpc_cidr in VPC_CIDRS, and it is generated rather than written here
# because the same ranges appear in the proxy slice's Squid ACL with the opposite polarity: the
# tunnel admits them as destinations, Squid denies them. A range in one list and not in the other
# is a spoke reachable through the proxy that the topology says is unreachable.
variable "rfc1918_cidrs" {
  description = "The private address space - the only destinations this tunnel forwards to. Generated; never authored here."
  type        = list(string)
  nullable    = false
}
