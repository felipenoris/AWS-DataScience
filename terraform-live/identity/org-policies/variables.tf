# Inputs - Stage 2 step 5.
#
# The first three have no default and arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py identity org-policies), for the reasons in
# scripts/tfhygiene/backend.py: `region` may not be a literal in a .tf file, and the two env
# vocabularies are a property of the account folder rather than of this slice.
#
# NOTHING HERE IS AN ORGANIZATION ID, A ROOT ID, AN OU ID OR AN ACCOUNT ID, and that is the
# point of the file. All five identifiers the documents need are resolved from the
# Organizations API in data.tf and composed in locals.tf - the same five render.py substitutes,
# by the same names (aws/INDEX.md rule 1).

# WHAT THIS REGION IS AND IS NOT, kept in a comment because step 9.1's check scans string
# VALUES for a region literal and skips full-line comments - deliberately, since a comment
# creates nothing. Organizations is global and answers at its own single endpoint whatever this
# says (1d step 12 measured that from the Identity account, under the Region ceiling). What this
# value decides is the S3 backend: the bucket that holds this slice's state, and the KMS key
# that encrypts it. Point it elsewhere and no policy call breaks - the STATE read does, with a
# message that reads like a credentials problem.
variable "region" {
  description = "AWS region for this slice - the region of the S3 backend that holds its state, not the endpoint Organizations answers at. No default: see the notes above."
  type        = string
  nullable    = false
}

# DECLARED AND NOT REFERENCED, ON PURPOSE. The <env> name token builds RESOURCE NAMES, and
# nothing here is named after an environment - a policy is named after what it denies, and the
# ten names are fixed by what is already attached. It is declared anyway because
# terraform.auto.tfvars is written from ONE table for every slice (scripts/tfhygiene/backend.py,
# step 2.6), so the value arrives whether this slice wants it or not; dropping the variable
# turns every plan into a "value for undeclared variable" warning, which is how a real warning
# stops being read. The validation below is what it is actually for: it fails loudly if the
# generated file was built for a different account folder.
# tflint-ignore: terraform_unused_declarations
variable "env" {
  description = "The <env> NAME TOKEN of docs/plan/conventions.md. `org` for the organization's policy plane."
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

    TWO LIMITS EXIST AND THIS IS THE SMALLER ONE, ON PURPOSE - the same reasoning render.py
    carries, and deliberately the same number, because two mechanisms measuring one document
    against two ceilings is the shape Lesson 14 keeps producing. SCPs went to 10 240 characters
    in May 2026; RCPs were not part of that increase and are still 5 120. This folder holds
    both kinds, so every document is checked against the tighter figure. A limit that is right
    for most of them is the kind that gets discovered by the one it was wrong for.

    IT IS MEASURED ON THE MINIFIED FORM, which is what `jsonencode` produces and what the API
    receives - not on the bytes of the tracked template, which carry indentation the API never
    sees. Widest margin today is 4 919 characters and the tightest 3 469, so nothing is close;
    the check is here for the stage that adds a statement, not for this one.
  EOT
  type        = number
  default     = 5120
}
