# Inputs - Stage 2 step 5.
#
# The first three have no default and arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py identity sso), for the reasons in
# scripts/tfhygiene/backend.py: `region` may not be a literal in a .tf file, and the two env
# vocabularies are a property of the account folder rather than of this slice.
#
# Nothing here is an account id or a group GUID. Accounts are named in locals.tf and resolved
# through the Organizations API; groups are named in data.tf and resolved through the identity
# store. aws/INDEX.md rule 1 on one side, docs/plan/conventions.md's "resolve a group by display
# name" on the other.

variable "region" {
  description = "AWS region for this slice - also the Region the Identity Center instance lives in. No default: see the note above."
  type        = string
  nullable    = false
}

# Declared and not referenced. The <env> name token builds resource names, and nothing in the
# identity plane is named after an environment: the six sets are named after personas and the
# assignments after accounts. It is declared because terraform.auto.tfvars is written from one
# table for every slice (scripts/tfhygiene/backend.py, step 2.6), so the value arrives whether
# this slice wants it or not, and dropping the variable turns every plan into a "value for
# undeclared variable" warning. The validation below fails loudly if the generated file was
# built for a different account folder.
# tflint-ignore: terraform_unused_declarations
variable "env" {
  description = "The <env> name token of docs/plan/conventions.md. `org` for the identity plane."
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
# A map rather than a string, by design. D35 vends one Sandbox per business unit and the tunnel
# lives on exactly that multiplied side (Stage 4's forward constraint), so the deny names a list
# of addresses from day one: adding unit 2 appends a row to VPN_HOMES in
# scripts/tfhygiene/backend.py and changes no policy document. INT-05 gives the same reason from
# the other end.
#
# The profile rides in the value because each row becomes a terraform_remote_state read of that
# account's foundation/ slice, a read that crosses an account boundary, so the data source needs
# a profile the way a same-account read does not. Pass 2's rule is that a profile literal never
# sits in a .tf file, so it arrives here instead; `env` is the name token the state bucket is
# built from, a third vocabulary this slice may not derive (backend.py's own table).
#
# An empty map is refused rather than tolerated: no homes means no addresses means a
# `NotIpAddress` over an empty list, which IAM reads as "matches nothing" - the deny would fire
# on every call from every network and lock all six personas out of everything. An empty
# allow-list is the one input shape whose failure is total.
variable "vpn_homes" {
  description = "Account folder -> { profile, env, slice } for every account terminating a WireGuard tunnel. Generated (backend.py VPN_HOMES); read for that slice's Elastic IP. The slice field arrived at Stage 6c step 0.5: the tunnel moves into VPC-Networking, whose EIP lives in production/networking/ rather than in a foundation/, so the slice stopped being derivable from the account."
  type = map(object({
    profile = string
    env     = string
    slice   = string
  }))
  nullable = false

  validation {
    condition     = length(var.vpn_homes) > 0
    error_message = "vpn_homes is empty. An empty allow-list makes DenyControlPlaneOffVpn match every call from every network - see the note above. Regenerate with ./scripts/gen-tfvars.py identity sso."
  }
}

# The account that owns the lake - Stage 5 pass 4c, the same one-element table the consumer
# slices take (backend.py DATA_LAKE). Read for the drop-box bucket ARN, its write prefix and
# the lake data-key ARN: the drop-box write is cross-account, so the bucket policy's grant is
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

    Two limits exist and this is the smaller one. The Identity Center API accepts an inline
    policy up to 32768 characters, but a permission set becomes an IAM role in every account it
    is provisioned into, and an inline role policy is capped far lower. The expensive failure is
    the second: it lands per account, at provisioning time, in an account nobody is looking at -
    the quiet shape decision 4 avoids for the boundary. The plan fails here instead, and a set
    that genuinely needs more becomes a customer-managed policy, which lands back on decision 4.

    It is measured against the rendered document, not against what AWS stores, and the first
    apply showed those are not the same number: 3547-4563 characters rendered here against
    2414-3148 read back with `get-inline-policy-for-permission-set` - Identity Center keeps a
    compacted form, about a quarter smaller. The rendered figure is the one the API receives,
    so measuring it is the conservative side of a difference that would otherwise be discovered
    by a set that passed the check and failed the call.
  EOT
  type        = number
  default     = 10240
}

# Generated into the tfvars, never typed (Lesson 14). The object it names is created by each
# member account's foundation/ slice, under this exact name - a reference that does not resolve
# in an account fails provisioning there, not planning here, so the two sides read one constant:
# scripts/tfhygiene/backend.py's PERSONA_VENDING_POLICY_NAME.
variable "persona_vending_policy_name" {
  description = "Name of the customer-managed policy carrying the persona's S3 Access Grants vending handshake."
  type        = string
  nullable    = false
}
