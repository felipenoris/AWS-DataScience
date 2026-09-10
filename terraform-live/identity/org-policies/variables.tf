# Inputs - Stage 2 step 5.
#
# The first three have no default and arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py identity org-policies), for the reasons in
# scripts/tfhygiene/backend.py: `region` may not be a literal in a .tf file, and the two env
# vocabularies are a property of the account folder rather than of this slice.
#
# Nothing here is an organization id, a root id, an OU id or an account id. All five identifiers
# the documents need are resolved from the Organizations API in data.tf and composed in
# locals.tf - the same five render.py substitutes, by the same names (aws/INDEX.md rule 1).

# The region is described in a comment because step 9.1's check scans string values for a region
# literal and skips full-line comments. Organizations is global and answers at its own single
# endpoint whatever this says (1d step 12 measured that from the Identity account, under the
# Region ceiling). This value decides the S3 backend: the bucket that holds this slice's state,
# and the KMS key that encrypts it. Point it elsewhere and no policy call breaks - the state read
# does, with a message that reads like a credentials problem.
variable "region" {
  description = "AWS region for this slice - the region of the S3 backend that holds its state, not the endpoint Organizations answers at. No default: see the notes above."
  type        = string
  nullable    = false
}

# Declared and not referenced. The <env> name token builds resource names, and nothing here is
# named after an environment: a policy is named after what it denies, and the ten names are fixed
# by what is already attached. It is declared because terraform.auto.tfvars is written from one
# table for every slice (scripts/tfhygiene/backend.py, step 2.6), so the value arrives whether
# this slice wants it or not, and dropping the variable turns every plan into a "value for
# undeclared variable" warning. The validation below fails loudly if the generated file was built
# for a different account folder.
# tflint-ignore: terraform_unused_declarations
variable "env" {
  description = "The <env> name token of docs/plan/conventions.md. `org` for the organization's policy plane."
  type        = string
  nullable    = false

  validation {
    condition     = var.env == "org"
    error_message = "identity/org-policies/ is org-level: env must be `org`. A different token means the generated tfvars was built for another account folder."
  }
}

variable "environment_tag" {
  description = "The Environment TAG value - the third vocabulary. `org` marks org-level and platform resources."
  type        = string
  nullable    = false

  validation {
    condition     = var.environment_tag == "org"
    error_message = "identity/org-policies/ tags Environment=org. See docs/plan/conventions.md, mandatory tags."
  }
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy, which requires the key."
  type        = string
  default     = "AWS-DataScience"
}

variable "owner" {
  description = "Owner tag - an sso-group-* GROUP, never a person (docs/plan/conventions.md). The organization's ceiling is the infrastructure group's to author, whichever OU a document lands on."
  type        = string
  default     = "sso-group-infrastructure"
}

variable "cost_center" {
  description = "CostCenter tag - the stage that created the resource. All ten documents were written and attached by hand in Stage 1c step 7; Stage 2 imports them and creates none, so the value is stage-01c for the whole slice rather than an override per resource."
  type        = string
  default     = "stage-01c"
}

variable "policy_max_bytes" {
  description = <<-EOT
    The size a single document may not exceed once minified, enforced as a plan-time
    precondition rather than discovered at the API (step 5.2, "count before writing").

    Two limits exist and this is the smaller one - the same number render.py carries, because
    two mechanisms measuring one document against two ceilings is the shape Lesson 14 keeps
    producing. SCPs went to 10 240 characters in May 2026; RCPs were not part of that increase
    and are still 5 120. This folder holds both kinds, so every document is checked against the
    tighter figure.

    It is measured on the minified form, which is what `jsonencode` produces and what the API
    receives, not on the bytes of the tracked template, which carry indentation the API never
    sees. Widest margin today is 4 919 characters and the tightest 3 469; the check is here for
    the stage that adds a statement.
  EOT
  type        = number
  default     = 5120
}
