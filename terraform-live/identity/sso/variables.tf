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

# The VPN homes whose Elastic IP the control plane is pinned to - Stage 4 step 8.1.
#
# A MAP, NOT A STRING, AND THAT IS THE DESIGN RATHER THAN GENEROSITY. D35 vends one Sandbox per
# business unit and the tunnel lives on exactly that multiplied side (Stage 4's forward
# constraint), so the deny names a LIST of addresses from day one: adding unit 2 appends a row
# to VPN_HOMES in scripts/tfhygiene/backend.py and changes no policy document. INT-05 gives the
# same reason from the other end.
#
# WHY THE PROFILE RIDES IN THE VALUE. Each row becomes a terraform_remote_state read of that
# account's foundation/ slice - the repository's first read that CROSSES an account boundary,
# so the data source needs a profile the way a same-account read does not. Pass 2's rule is
# that a profile literal never sits in a .tf file, so it arrives here instead; `env` is the
# name token the state bucket is built from, which is a third vocabulary this slice may not
# derive (backend.py's own table).
#
# WHAT AN EMPTY MAP WOULD MEAN, and why data.tf refuses it rather than tolerating it: no homes
# means no addresses means a `NotIpAddress` over an empty list, which IAM reads as "matches
# nothing" - the deny would fire on EVERY call from EVERY network and lock all six personas out
# of everything. An empty allow-list is the one input shape whose failure is total.
variable "vpn_homes" {
  description = "Account folder -> { profile, env } for every account terminating a WireGuard tunnel. Generated (backend.py VPN_HOMES); read for its foundation/ Elastic IP."
  type = map(object({
    profile = string
    env     = string
  }))
  nullable = false

  validation {
    condition     = length(var.vpn_homes) > 0
    error_message = "vpn_homes is empty. An empty allow-list makes DenyControlPlaneOffVpn match every call from every network - see the note above. Regenerate with ./scripts/gen-tfvars.py identity sso."
  }
}

# The lake's consumer accounts - Stage 5 pass 4c. Same shape and same argument as vpn_homes:
# each row becomes a terraform_remote_state read of that account's data/ slice, so the
# workgroup and derived-bucket ARNs the DataScientistAccess statements name are ENUMERATED
# from state rather than wildcarded (the reason 4c was sequenced after the slices at all).
# Adding a consumer (Stage 9's production leg, a Stage 14 vend) is a row in backend.py's
# DATA_CONSUMERS, never an edit to a policy document.
#
# AN EMPTY MAP FAILS CLOSED HERE, NOT OPEN - the opposite polarity from vpn_homes, so it gets
# its own sentence: no consumers means empty resource lists in three ALLOW statements, which
# IAM rejects at provisioning (a statement must name a resource), in every account the set is
# provisioned into. The validation turns that per-account provisioning failure into one
# plan-time message.
variable "data_consumers" {
  description = "Account folder -> { profile, env } for every account consuming the lake (backend.py DATA_CONSUMERS). Read for each one's data/ slice outputs: the Athena workgroup and derived-bucket ARNs."
  type = map(object({
    profile = string
    env     = string
  }))
  nullable = false

  validation {
    condition     = length(var.data_consumers) > 0
    error_message = "data_consumers is empty: three DataScientistAccess allows would render with no resource and fail at provisioning, per account. Regenerate with ./scripts/gen-tfvars.py identity sso."
  }
}

# The account that OWNS the lake - Stage 5 pass 4c, the same one-element table the consumer
# slices take (backend.py DATA_LAKE). Read for the drop-box bucket ARN, its write prefix and
# the lake data-key ARN: the drop-box write is CROSS-ACCOUNT, so the bucket policy's grant is
# only half of the permission and the identity half has to name real ARNs - the key ARN
# carries the account id, which may live in state but never in a tracked file.
variable "lake" {
  description = "Account folder -> { profile, env } for the account owning the governed lake (backend.py DATA_LAKE). Read for data-governance/data/ outputs: the drop-box ARN + prefix and the data-key ARN."
  type = map(object({
    profile = string
    env     = string
  }))
  nullable = false

  validation {
    condition     = length(var.lake) == 1
    error_message = "lake must name exactly one account - D22 makes the Data Governance account a structural singleton. Regenerate with ./scripts/gen-tfvars.py identity sso."
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

    IT IS MEASURED AGAINST THE RENDERED DOCUMENT, NOT AGAINST WHAT AWS STORES, and the first
    apply showed those are not the same number: 3547-4563 characters rendered here against
    2414-3148 read back with `get-inline-policy-for-permission-set` - Identity Center keeps a
    compacted form, about a quarter smaller. The rendered figure is the one the API receives,
    so measuring it is the conservative side of a difference that would otherwise be discovered
    by a set that passed the check and failed the call.
  EOT
  type        = number
  default     = 10240
}
