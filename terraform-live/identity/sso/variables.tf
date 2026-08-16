# Inputs - Stage 2 step 5.
#
# The first three have no default and arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py identity sso), for the reasons in
# scripts/tfhygiene/backend.py: `region` may not be a literal in a .tf file, and the two env
# vocabularies are a property of the account folder rather than of this slice.
#
# NOTHING HERE IS AN ACCOUNT ID OR A GROUP GUID, and that is the point of the file. Accounts
# are named in locals.tf and resolved through the Organizations API; groups are named in
# data.tf and resolved through the identity store. aws/INDEX.md rule 1 on one side,
# docs/plan/conventions.md's "resolve a group by display name" on the other.

variable "region" {
  description = "AWS region for this slice - also the Region the Identity Center instance lives in. No default: see the note above."
  type        = string
  nullable    = false
}

# DECLARED AND NOT REFERENCED, ON PURPOSE. The <env> name token builds RESOURCE NAMES, and
# nothing in the identity plane is named after an environment - the six sets are named after
# personas and the assignments after accounts. It is declared anyway because
# terraform.auto.tfvars is written from ONE table for every slice (scripts/tfhygiene/backend.py,
# step 2.6), so the value arrives whether this slice wants it or not; dropping the variable
# turns every plan into a "value for undeclared variable" warning, which is how a real warning
# stops being read. The validation below is what it is actually for: it fails loudly if the
# generated file was built for a different account folder.
# tflint-ignore: terraform_unused_declarations
variable "env" {
  description = "The <env> NAME TOKEN of docs/plan/conventions.md. `org` for the identity plane."
  type        = string
  nullable    = false

  validation {
    condition     = var.env == "org"
    error_message = "identity/sso/ is the org-level identity plane: env must be `org`. A different token means the generated tfvars was built for another account folder."
  }
}

variable "environment_tag" {
  description = "The Environment TAG value - the third vocabulary. `org` marks org-level and platform resources."
  type        = string
  nullable    = false

  validation {
    condition     = var.environment_tag == "org"
    error_message = "identity/sso/ tags Environment=org. See docs/plan/conventions.md, mandatory tags."
  }
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy, which requires the key."
  type        = string
  default     = "AWS-DataScience"
}

variable "owner" {
  description = "Owner tag - an sso-group-* GROUP, never a person (docs/plan/conventions.md). The entitlement plane is the infrastructure group's, whichever persona a set describes."
  type        = string
  default     = "sso-group-infrastructure"
}

variable "cost_center" {
  description = "CostCenter tag - the stage that created the resource. Stage 2 creates the six persona sets; the imported InfrastructureAccess set overrides this with stage-01b, which is where it was actually made."
  type        = string
  default     = "stage-02"
}

variable "session_duration" {
  description = "How long a console or CLI session from any of these sets lasts, ISO-8601. PT4H is what InfrastructureAccess already carries (measured 2026-08-16), and matching it keeps one answer to 'how long is a session here'. It is roughly a working block: long enough that re-authenticating is not the job, short enough that a session does not outlive the reason it was opened - the standing shape of Lesson 25."
  type        = string
  default     = "PT4H"
}

variable "inline_policy_max_bytes" {
  description = <<-EOT
    The size a set's inline policy may not exceed, enforced as a plan-time precondition rather
    than discovered at provisioning (step 5.2, "count before writing").

    TWO LIMITS EXIST AND THIS IS THE SMALLER ONE, ON PURPOSE. The Identity Center API accepts
    an inline policy up to 32768 characters, but a permission set BECOMES AN IAM ROLE in every
    account it is provisioned into, and an inline role policy is capped far lower. The
    expensive failure is the second one: it lands per account, at provisioning time, in an
    account nobody is looking at - the same quiet shape decision 4 avoids for the boundary. So
    the plan fails here instead, and a set that genuinely needs more becomes a customer-managed
    policy, which lands back on decision 4.
  EOT
  type        = number
  default     = 10240
}
