# Inputs, from two files - the same split sandbox/vpn/ uses, and for the same reason.
#
# The first five arrive from the GENERATED, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py sandbox devbox): region and env for Stage 2's standing reasons,
# zone_ids because the AZ choice lives in scripts/tfhygiene/backend.py (D9), and account_folder
# because a remote-state key is keyed by the account FOLDER.
#
# peer_cidr LEFT THIS FILE ON 2026-08-21, with the ingress rule it fed: the user withdrew the
# "reachable only over the VPN" requirement once a measurement showed it was not true of the
# shell, and an input with no consumer sends the next reader hunting for the resource that
# uses it (the same argument that keeps zone_ids out of bootstrap/'s tfvars).
#
# The two SIZE knobs arrive from the TRACKED instance_type.auto.tfvars beside this file - the
# second file in this repository to use that mechanism, deliberately mirroring the first so a
# reader who knows one knows both. What is NOT mirrored is the meaning of the defaults, and
# the difference is written on each of them below.

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
  description = "The Environment TAG value - the third vocabulary. NOT cosmetic here: awsds-org-scp-tag-enforcement denies ec2:RunInstances outright when Environment or Project is absent, so a missing default_tag is an apply that fails at the instance."
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
  description = "Which authored zone the build host lands in. Nothing it consumes is AZ-bound - the route table is the tier's, the security group and the NAT host belong to the VPC - so this is a one-variable retry when capacity is short in a zone, the same fallback sandbox/vpn/ carries for the same measured reason."
  type        = number
  default     = 0
}

variable "account_folder" {
  description = "This slice's terraform-live/ folder name - the first path segment of every state key. Consumed by the remote-state reads of foundation/ and vpn/."
  type        = string
  nullable    = false
}

# ------------------------------------------------------------ the two knobs, and one caveat

variable "instance_type" {
  description = "THE BUILD HOST'S SIZE, SELECTED PER APPLY, from the tracked instance_type.auto.tfvars beside this file. WHERE THIS DIFFERS FROM sandbox/vpn/'s KNOB OF THE SAME NAME, and it is the thing to read before assuming the two files behave alike: there, the default is a POSTURE - t3.nano is what the design runs at and a larger value is a temporary switch. Here the default is a FLOOR. This host exists to build a container image whose base alone is ~3.9 GB compressed and several times that unpacked, and a default too small to do that would be a value that looks like a choice and is a trap. So the default IS the working shape (t3.xlarge - 4 vCPU, 16 GiB, 0.1664 USD/h measured, docs/PRICING.md 8) and the file beside this one assigns it explicitly, so the two agree and a fresh clone builds something that works. THE LIST IS x86_64, and that is not a preference either: SageMaker images are amd64 and the sagemaker-distribution repository publishes no arm64 tag at all, so building on Graviton would produce an image no SMUS space can run. It is the whole reason this slice exists rather than a laptop."
  type        = string
  default     = "t3.xlarge"

  validation {
    # A CLOSED LIST, like vpn/'s and unlike root_volume_size's band: what is being defended is
    # an architecture (the AMI is x86_64; a t4g is a machine this image cannot run on and EC2
    # refuses it) and a ceiling on an hourly rate that is already 32x the tunnel host's.
    condition     = contains(["t3.large", "t3.xlarge", "t3.2xlarge"], var.instance_type)
    error_message = "instance_type must be t3.large, t3.xlarge or t3.2xlarge - x86_64, because the image being built is amd64 (docs/PRICING.md 8 carries the rates)."
  }
}

variable "root_volume_size" {
  description = "THE BUILD HOST'S DISK, IN GiB, from the same tracked file. 64 is the working value: the base image is ~3.9 GB compressed and roughly 12 GB unpacked, dev-env adds Julia, an R environment and a Rust toolchain on top, and docker keeps the pulled layers AND the built ones - so 64 is comfortable rather than generous, and the failure mode of guessing low is a build that dies most of the way through. THE ASYMMETRY THAT BITES IN sandbox/vpn/ DOES NOT BITE HERE, and that is the one real difference between the two slices' copies of this knob: there the host is [D] and the volume is a STANDING cost that EBS will not shrink, so the value is a commitment. This slice is [E]. The volume is created with the host and destroyed with it, so a value that turns out wrong costs one teardown and one apply, and it bills only while the session runs."
  type        = number
  default     = 64

  validation {
    # FLOOR 32: below that the two images do not both fit and the failure arrives late.
    # CEILING 256: at 0.08 USD/GB-mo that is ~20 USD/month IF it were standing - it is not,
    # because this slice is [E], but a devbox left up for a week at 256 GiB is still real
    # money against D12, and this is where a fat-fingered 2560 is caught at PLAN time.
    condition     = var.root_volume_size >= 32 && var.root_volume_size <= 256
    error_message = "root_volume_size must be between 32 GiB (below this the two images do not both fit) and 256 GiB."
  }
}

# ------------------------------------------------------------------------- the five tags

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy - and REQUIRED at RunInstances by awsds-org-scp-tag-enforcement."
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
  default     = "stage-06"
}
