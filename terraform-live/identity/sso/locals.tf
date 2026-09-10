# The authored halves - Stage 2 steps 5.2 and 5.3.
#
# D34's rule, on the side of the seam where it says enumerated: an account acquires a
# permission set because somebody wrote its name down here, never because it appeared in the
# organization. A `for_each` over a human-authored map is still enumeration
# (docs/plan/conventions.md); a `for_each` over a data source is the failure mode.

locals {
  # ----------------------------------------------------------------- the instance and store
  #
  # `one()` rather than `[0]`: an empty list returns null here and a multi-element list raises
  # immediately, where an index would have silently taken the first of several instances. The
  # null case is caught by the precondition on every permission set, which names the Region
  # rather than a list index.
  instance_arn      = one(data.aws_ssoadmin_instances.this.arns)
  identity_store_id = one(data.aws_ssoadmin_instances.this.identity_store_ids)

  # -------------------------------------------------------------------------- the accounts
  #
  # The names are exact, and they are not the names anybody would guess. Measured 2026-08-16:
  # Control Tower vended every account with an ` Account` suffix, and Stage 1d step 9 paid for
  # this once - a lookup for `Log Archive` returns nothing, because the account is `Log Archive
  # Account`. Written out rather than composed from a token, so the trap is visible instead of
  # hidden in a format string.
  #
  # The roster carries a live collision: a SUSPENDED account called plain `Sandbox` still
  # appears in list-accounts. `Sandbox Account 1` is the vended one (D35, N=1); a map keyed on
  # `Sandbox` would resolve to a closed account and the assignment would fail in a way that
  # reads like a permissions problem. account_ids below filters on ACTIVE as a second line of
  # defence; the primary one is that the name is written out in full.
  #
  # No `staging` entry: the account is unvended (step 3.2, held on the account cap), so every
  # Staging cell of 1b step 3.1 is skipped here exactly as it was skipped there. The set for
  # Staging is still created - see permission-sets.tf - because a set costs nothing and having
  # it reviewed now is the point of writing it in code.
  #
  # The key is the account folder of terraform-live/, not a slug invented here. That vocabulary
  # already exists - scripts/tfhygiene/backend.py's ENV_TOKENS is keyed on it, and every path
  # in this repository is `terraform-live/<key>/...`. Using it means the for_each key of an
  # assignment is the folder whose infrastructure the assignment grants, and
  # ./aws/import-ids.py can emit an import address that matches this configuration instead of
  # guessing at one (step 5.5a(iii): the wrong key does not error, it plans a create beside an
  # orphan).
  accounts = {
    sandbox           = "Sandbox Account 1"
    staging           = "Staging Account"
    "data-governance" = "Data Governance Account"
    production        = "Production Account"
    identity          = "Identity Account"
  }

  # Only ACTIVE accounts are candidates - see the collision note above. `one()` raises if a
  # name is ambiguous and yields null if it matched nothing; the null is turned into a
  # readable failure by the precondition in assignments.tf.
  account_ids = {
    for slug, name in local.accounts :
    slug => one([
      for a in data.aws_organizations_organization.this.accounts :
      a.id if a.name == name && a.status == "ACTIVE"
    ])
  }

  # ------------------------------------------------------------------------ the entitlements
  #
  # The table of 1b step 3.1, transcribed. That step is the design of record for all seven
  # sets and this file does not restate it; what is here is the assignment half, one row per
  # (set, account) pair, written out one by one so that no account silently acquires
  # DataScientistAccess on the next apply.
  #
  # The key is authored text and carries no id, which is what makes it stable: adding an
  # account or a set appends a key and touches no existing one, so no attachment is destroyed
  # and re-created. A re-created assignment is a moment in which somebody cannot sign in
  # (verification (v) raises the same concern for the other slice).
  #
  # Absent by design, because absence has to be readable (1b step 3.7):
  #   - sso-group-data-scientists on Data Governance      - the lake is read through the Lake
  #                                                         Formation share, never in place
  #   - sso-group-deployment-managers on Data Governance  - a release approver has no business
  #                                                         in the account that grants access
  #   - sso-group-dev-env-stewards on Staging, Data Governance, Identity, Audit, Log Archive,
  #     Policy Canary                                     - it judges a container image
  #   - every persona on Identity, Audit, Log Archive, Policy Canary, and Management
  #
  # Staging exists since Stage 6b renamed `Development` into it (2026-09-06), the quota having
  # refused the vend. It carries exactly two personas - DataScientistStagingAccess (D18,
  # read-only) and DeploymentManagerAccess - and the steward's absence above is an absence for
  # its own reason.
  assignments = {
    # DataScientistAccess - Sandbox only since Stage 6b step 2.1. D21 said "one set, two
    # accounts, policy-identical because they share an OU"; the accounts no longer share an OU
    # and are no longer policy-identical, which is why the row below is a different set.
    "data-scientist@sandbox" = { set = "data_scientist", group = "data_scientists", account = "sandbox" }
    # Swapped by Stage 6b step 2.1 and re-keyed by step 4.6 (both 2026-09-06). The two halves
    # were separate: 2.1 changed which permission set the account gets, 4.6 changed the address,
    # and an address change is a destroy-and-create unless a moved {} block says otherwise -
    # moved.tf carries it. D18: Staging is read-only and nothing else.
    "data-scientist-staging@staging" = { set = "data_scientist_staging", group = "data_scientists", account = "staging" }

    # DataScientistProdAccess - Production only (D18). A different shape, not a weaker copy.
    "data-scientist-prod@production" = { set = "data_scientist_prod", group = "data_scientists", account = "production" }

    # DeploymentManagerAccess (D31) - diagnosis, not reading. Nothing on Data Governance.
    "deployment-manager@sandbox"    = { set = "deployment_manager", group = "deployment_managers", account = "sandbox" }
    "deployment-manager@staging"    = { set = "deployment_manager", group = "deployment_managers", account = "staging" }
    "deployment-manager@production" = { set = "deployment_manager", group = "deployment_managers", account = "production" }

    # GovernanceManagerAccess - Data Governance only, the mirror image of the row above: the
    # one account the deployment manager cannot enter is the only one this one can.
    "governance-manager@data-governance" = { set = "governance_manager", group = "governance_managers", account = "data-governance" }

    # DevEnvStewardAccess - Production, plus Sandbox and Development. The set is read-only
    # everywhere by construction, so "read-only on Sandbox and Development" is a property of
    # the policy rather than of the assignment (1b 3.3: one set object is one policy, however
    # many accounts it reaches).
    # Stage 6b step 2.1 (2026-09-06) removed it from this account. The reason is D14's, not "a
    # Workload account has no image steward" - Production is a Workload account and holds the
    # seat. The steward curates images, the registry is ECR in Production, and Staging has no
    # registry to steward. The set survives; two assignments are what leave.
    "dev-env-steward@production" = { set = "dev_env_steward", group = "dev_env_stewards", account = "production" }
    "dev-env-steward@sandbox"    = { set = "dev_env_steward", group = "dev_env_stewards", account = "sandbox" }
  }

  # ------------------------------------------------------------------- the six written sets
  #
  # The name is the one thing here that cannot be changed casually: `<Persona>Access`, and
  # never within four characters of a Control Tower set - 1b step 3.2 renamed this project's
  # administrator set for that reason, because an assignment made against the wrong one still
  # works and nothing reports it. Changing a name here destroys and re-creates the set, which
  # is a window in which nobody holds it.
  persona_sets = {
    data_scientist = {
      name        = "DataScientistAccess"
      description = "Studio use through SMUS projects, drop-box write, ECR pull. Not PowerUser, not SageMakerFullAccess (1b 3.4, D21; Athena and the derived zone left 2026-08-26, D19 revised)"
    }
    data_scientist_staging = {
      name        = "DataScientistStagingAccess"
      description = "Staging: read-only, no write of any kind, not even a drop-box (1b 3.6, D20)"
    }
    data_scientist_prod = {
      name        = "DataScientistProdAccess"
      description = "Production: data plane read, no compute, no control plane (1b 3.6, D18)"
    }
    deployment_manager = {
      name        = "DeploymentManagerAccess"
      description = "Diagnosis, not reading. Nothing on Data Governance (1b 3.5, D31)"
    }
    governance_manager = {
      name        = "GovernanceManagerAccess"
      description = "The catalog, never the rows. Data Governance only (1b 3.5)"
    }
    dev_env_steward = {
      name        = "DevEnvStewardAccess"
      description = "The artifact, never the data (1b 3.5, D14, INT-19)"
    }
  }

  # The two indirections the assignment map resolves through, so a row stays a row of names and
  # the wiring is in one place.
  permission_set_arns = { for k, v in aws_ssoadmin_permission_set.persona : k => v.arn }

  group_ids = {
    data_scientists     = data.aws_identitystore_group.data_scientists.group_id
    deployment_managers = data.aws_identitystore_group.deployment_managers.group_id
    governance_managers = data.aws_identitystore_group.governance_managers.group_id
    dev_env_stewards    = data.aws_identitystore_group.dev_env_stewards.group_id
  }

  # ------------------------------------------------------- the addresses the control plane is
  #                                                          pinned to - Stage 4 step 8.1
  #
  # One /32 per VPN home, read from that home's foundation/ state and never pasted. The address
  # is a [P] allocation so a client config is written once and an instance rebuild changes
  # nothing (step 2.1); pasting it here would make this file the second place it lives.
  #
  # `/32` is required: an IAM `IpAddress`/`NotIpAddress` condition takes CIDR notation and the
  # output is a bare address, so the mask is added here rather than in the policy document.
  #
  # `sort()` for a stable diff. A map iterates in key order already, but the list feeds a policy
  # JSON whose textual value is what `terraform plan` compares, and once N > 1 the day a home
  # is added should not also be a reordering.
  #
  # `distinct()` because 6c step 4.12 made two homes share one address: the Elastic IP was
  # transferred between accounts rather than reallocated, so `sandbox/foundation` and
  # `production/networking` both answer `52.89.212.1`. Without it the policy document carries
  # the same /32 twice.
  #
  # The proxy's address joined this list at 6c step 4.12 (2026-09-06), and under D38 it is the
  # one that matters. A VPN client is a private-network client: its whole internet crosses an
  # explicit Squid proxy in the hub, so a persona's control-plane call leaves the estate from
  # the proxy's Elastic IP and never from the tunnel endpoint's. The WireGuard address stays
  # because the tunnel host still originates traffic of its own, and because pass 4's rule is
  # union first and trim after the readings - a single cut-over apply here is one typo away from
  # denying six personas every call from every network.
  #
  # `try(..., null)` and not a direct read: a VPN home is not required to hold a proxy - Sandbox
  # exports no such output and is still a home while the union stands - so a missing output is a
  # legitimate shape rather than an error. `compact()` drops the nulls that produces.
  vpn_egress_cidrs = sort(distinct(compact(flatten([
    for home, remote in data.terraform_remote_state.vpn_home : [
      "${remote.outputs.wireguard_eip_public_ip}/32",
      try("${remote.outputs.proxy_eip_public_ip}/32", null),
    ]
  ]))))

  # The same homes, by the VPC they exit through. This local replaced a list of gateway endpoint
  # ids on 2026-08-23, that list having been one case short.
  #
  # The 4d half, which stands: tunnel traffic splits by destination. S3 and DynamoDB leave
  # through the home's [P] gateway endpoints - prefix-list routes beating the IGW default - and
  # arrive carrying the host's private address plus a vpce id, never the Elastic IP. So the
  # aws:SourceIp pin alone explicitly denied every direct S3 call a persona made from inside
  # the perimeter (Lesson 33; stage 5 log, 4d).
  #
  # The half it missed, measured 2026-08-23 with a negative control: while `egress/` is up, the
  # laptop's DNS goes to the VPC resolver (the client config's own `DNS = 10.20.0.2`) and every
  # service holding an interface endpoint resolves to a private address - `dig sts.us-west-2
  # .amazonaws.com` answered 10.20.12.229, while `dig s3.us-west-2.amazonaws.com` answered
  # public addresses, the gateway doing no private DNS. Those calls present the interface
  # endpoint's id, which this list did not carry and may not carry: interface endpoints are
  # [E], with new ids on every `make up` (Lesson 3). The persona was explicitly denied
  # `sts:GetCallerIdentity` with the tunnel up and `curl checkip` reading the EIP - two true
  # readings of two different paths.
  #
  # The anchor is therefore the VPC, which is what Lesson 3 prescribes ("anchor on the [P]
  # gateway endpoint, OR on aws:SourceVpc"). It is [P], it survives every `make up`, and it
  # subsumes the gateway ids this local used to hold - a request through any endpoint in that
  # VPC carries both keys, so nothing that passed before stops passing. What it widens is the
  # intent of the control: the persona works from inside the perimeter. It does not admit
  # in-VPC workloads wearing this identity - a persona role is reachable only through the IdC
  # sign-in, never by an instance profile.
  #
  # `distinct()` here for the mirror reason: two homes cannot share a VPC today, but the guard
  # costs nothing and the two locals should fail the same way if they ever can.
  vpn_egress_vpc_ids = sort(distinct([
    for home, remote in data.terraform_remote_state.vpn_home :
    remote.outputs.vpc_id
  ]))

  # ------------------------------------------------- the lake's consumer-side ARNs - pass 4c
  #
  # Enumerated from state, never composed from a naming convention - the whole point of 4c's
  # sequencing (policies-data-scientists.tf carries the argument).

  # The lake singleton's three values (D22; the variable validates length == 1). `one()` with
  # the same diagnosis as instance_arn above: null on empty, loud on many.
  lake_dropbox_write_arn = "${one([for l, r in data.terraform_remote_state.lake_data : r.outputs.bucket_arns["dropbox"]])}/${one([for l, r in data.terraform_remote_state.lake_data : r.outputs.dropbox_prefix])}/*"

  lake_data_key_arn = one([
    for l, r in data.terraform_remote_state.lake_data : r.outputs.data_key_arn
  ])

  # The rendered inline policy of each written set, in one map, so the size precondition and
  # the reporting output read the same values (Lesson 14, at the smallest scale it occurs).
  inline_policies = {
    data_scientist         = data.aws_iam_policy_document.data_scientist.json
    data_scientist_staging = data.aws_iam_policy_document.data_scientist_staging.json
    data_scientist_prod    = data.aws_iam_policy_document.data_scientist_prod.json
    deployment_manager     = data.aws_iam_policy_document.deployment_manager.json
    governance_manager     = data.aws_iam_policy_document.governance_manager.json
    dev_env_steward        = data.aws_iam_policy_document.dev_env_steward.json
  }
}
