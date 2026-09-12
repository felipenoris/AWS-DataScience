# Inputs. region, env, environment_tag and the registry map arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py <account> dev-env). image_tag is this slice's
# own, edited by hand when a steward approves a build.

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> name token of docs/plan/conventions.md - what goes into a resource name. Never *the* sandbox: D35 vends one per business unit."
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

# ------------------------------------------------------------------- the registry account
#
# The image lives in Production and is registered here, so this slice reads one state across an
# account boundary: production/registry/'s outputs carry the repository URL the image version is
# built from and the two repository ARNs the image role's statement names. Both would otherwise be
# account-id-bearing literals in a tracked file, which aws/INDEX.md rule 1 forbids (Lesson 3).
#
# The map shape and the profile-from-tfvars idiom are the ones sandbox/sagemaker/ uses for the lake
# and the domain: a profile literal never sits in a .tf file (Lesson 14).

variable "registry" {
  description = "The account holding the ECR repositories: account folder => { profile, env }. One entry - REGISTRY_HOME in scripts/tfhygiene/backend.py."
  type = map(object({
    profile = string
    env     = string
  }))

  validation {
    condition     = length(var.registry) == 1
    error_message = "exactly one registry account - both repositories live in Production (docs/SMUS.md, Custom images)."
  }
}

# --------------------------------------------------------------------------- what is registered
#
# The tag, not a digest. docs/SMUS.md's tag rule is `<flavour>-v<major>.<minor>.<patch>` and both
# repositories are tag-immutable, so a tag names exactly one digest for the life of the repository
# and the two forms carry the same guarantee. The tag is also what the steward approves and what a
# reader recognises; a digest is neither.
#
# Bumping it replaces the image version: a SageMaker image version is immutable, so base_image is a
# force-new attribute. What the domain then serves depends on how the attachment names the version
# - runbooks/dev-env.md, "Attaching the image to the domain".

variable "image_tag" {
  description = "The dev-env image tag to register, `<flavour>-v<semver>` (docs/SMUS.md). default-v0.3.0 carries Stage 6e step 5.4's three changes: /etc/claude-code/managed-settings.json, a NO_PROXY_LIST that includes the two Bedrock endpoint names, and rust-src in the rustup profile (2026-09-12)."
  type        = string
  default     = "default-v0.3.0"

  validation {
    condition     = can(regex("^[a-z0-9]+-v[0-9]+\\.[0-9]+\\.[0-9]+$", var.image_tag))
    error_message = "the tag is <flavour>-v<major>.<minor>.<patch> - the hand-build form, with no -<short-sha> suffix (docs/SMUS.md, The tag rule)."
  }
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy."
  type        = string
  default     = "AWS-DataScience"
}

variable "owner" {
  description = "Owner tag - an sso-group-* group, never a person (docs/plan/conventions.md). The dev-env stewards own the image; the slice that registers it is the infrastructure group's."
  type        = string
  default     = "sso-group-infrastructure"
}

variable "cost_center" {
  description = "CostCenter tag - the stage that created the resource."
  type        = string
  default     = "stage-06d"
}
