# Inputs. The first five arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py production runners): region and env for Stage 2's standing reasons,
# zone_ids because the AZ choice lives in scripts/tfhygiene/backend.py (D9), and account_folder
# because every remote-state key is built from the account folder. The shape is a default, the
# buildbox's measured one (decision 5).

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
  description = "The Environment tag value - the third vocabulary. Not cosmetic: awsds-org-scp-tag-enforcement denies ec2:RunInstances outright when Environment or Project is absent."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "development", "data", "staging", "production", "org"], var.environment_tag)
    error_message = "environment_tag must be one of the six tag values in docs/plan/conventions.md."
  }
}

variable "zone_ids" {
  description = "The two AZ zone ids subnets anchor on (Stage 3 step 1.5, D9). Which one the runner lands in is zone_index below."
  type        = list(string)
  nullable    = false
}

variable "zone_index" {
  description = "Which authored zone the runner lands in. Nothing it consumes is AZ-bound, so this is a one-variable retry when capacity is short in a zone."
  type        = number
  default     = 0
}

variable "account_folder" {
  description = "This slice's terraform-live/ folder name - the first path segment of every state key."
  type        = string
  nullable    = false
}

variable "instance_type" {
  description = "The runner's size - the buildbox's measured shape (decision 5): m8i.xlarge, 4 vCPU, 16 GiB, 0.2117 USD/h (docs/PRICING.md 8), because the dev-env build is CPU-bound and saturated four burstable vCPUs on 2026-09-11. x86_64, and not a preference: the images are amd64 and SageMaker runs them on x86."
  type        = string
  default     = "m8i.xlarge"

  validation {
    condition     = contains(["m8i.large", "m8i.xlarge", "m8i.2xlarge"], var.instance_type)
    error_message = "instance_type must be m8i.large, m8i.xlarge or m8i.2xlarge - x86_64, because the images built here are amd64."
  }
}

variable "root_volume_size" {
  description = "The runner's disk, in GiB. 64 fits the two dev-env images and little more (the buildbox's figure); [E], so it bills only while the host does."
  type        = number
  default     = 64

  validation {
    condition     = var.root_volume_size >= 32 && var.root_volume_size <= 256
    error_message = "root_volume_size must be between 32 and 256 GiB."
  }
}

variable "ecr_credential_helper" {
  description = "Amazon's ECR credential helper, fetched by the boot through the proxy and mounted read-only into every job: the registry login a rootless build job cannot install for itself. Pinned by version and by the SHA256 its release page publishes (v0.12.0, 2026-02-27); a mismatch fails the boot. The upstream build is static (CGO_ENABLED=0), so it runs in Alpine and glibc images alike."
  type = object({
    version = string
    sha256  = string
  })
  default = {
    version = "0.12.0"
    sha256  = "a22ab6d59dbac777b8fb31984709461da00a4c778b6ae14c8d3729e8d5ded1a6"
  }

  validation {
    condition     = can(regex("^[0-9a-f]{64}$", var.ecr_credential_helper.sha256))
    error_message = "ecr_credential_helper.sha256 must be a 64-character lowercase hex digest."
  }
}

variable "concurrent_jobs" {
  description = "How many jobs the runner manager runs at once. Two: a docs build beside an image build; a third would contend for the same four vCPUs."
  type        = number
  default     = 2
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy - and required at RunInstances by awsds-org-scp-tag-enforcement."
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
  default     = "stage-07"
}
