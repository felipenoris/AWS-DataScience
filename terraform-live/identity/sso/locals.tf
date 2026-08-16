# The authored halves - Stage 2 steps 5.2 and 5.3.
#
# D34's rule, on the side of the seam where it says ENUMERATED: an account acquires a
# permission set because somebody wrote its name down here, never because it appeared in the
# organization. A `for_each` over a human-authored map is still enumeration
# (docs/plan/conventions.md); a `for_each` over a data source is the failure mode.

locals {
  # ----------------------------------------------------------------- the instance and store
  #
  # `one()` rather than `[0]`, and the difference is a diagnosis: an empty list returns null
  # here and a MULTI-element list raises immediately, where an index would have silently taken
  # the first of several instances. The null case is caught by the precondition on every
  # permission set, which names the Region rather than a list index.
  instance_arn      = one(data.aws_ssoadmin_instances.this.arns)
  identity_store_id = one(data.aws_ssoadmin_instances.this.identity_store_ids)

  # -------------------------------------------------------------------------- the accounts
  #
  # THE NAMES ARE EXACT AND THEY ARE NOT THE NAMES ANYBODY WOULD GUESS. Measured 2026-08-16:
  # Control Tower vended every account with an ` Account` suffix, and Stage 1d step 9 already
  # paid for this once - a lookup for `Log Archive` returns nothing, because the account is
  # `Log Archive Account`. Written out rather than composed from a token, so the trap is
  # visible instead of hidden in a format string.
  #
  # AND THERE IS A LIVE COLLISION IN THE ROSTER. A SUSPENDED account called plain `Sandbox`
  # still appears in list-accounts. `Sandbox Account 1` is the vended one (D35, N=1); a map
  # keyed on `Sandbox` would resolve to a closed account and the assignment would fail in a
  # way that reads like a permissions problem. account_ids below therefore filters on ACTIVE,
  # which is a second line of defence rather than the primary one - the primary one is that
  # the name is written out in full.
  #
  # NO `staging` ENTRY: the account is unvended (step 3.2, held on the account cap), so every
  # Staging cell of 1b step 3.1 is skipped here exactly as it was skipped there. The SET for
  # Staging is still created - see permission-sets.tf - because a set costs nothing and having
  # it reviewed now is the point of writing it in code.
  #
  # THE KEY IS THE ACCOUNT FOLDER OF terraform-live/, NOT A SLUG INVENTED HERE. That
  # vocabulary already exists - scripts/tfhygiene/backend.py's ENV_TOKENS is keyed on it, and
  # every path in this repository is `terraform-live/<key>/...`. Using it means the for_each
  # key of an assignment IS the folder whose infrastructure the assignment grants, and
  # ./aws/import-ids.py can emit an import address that matches this configuration instead of
  # guessing at one (step 5.5a(iii): the wrong key does not error, it plans a create beside an
  # orphan).
  accounts = {
    sandbox           = "Sandbox Account 1"
    development       = "Development Account"
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
  # THE TABLE OF 1b STEP 3.1, TRANSCRIBED. That step is the design of record for all seven
  # sets and this file does not restate it - what is here is the ASSIGNMENT half, one row per
  # (set, account) pair, written out one by one because an account silently acquiring
  # DataScientistAccess on the next apply is the failure this design exists to prevent.
  #
  # THE KEY IS AUTHORED TEXT AND CARRIES NO ID. That is what makes it stable: adding an
  # account or a set appends a key and touches no existing one, so no attachment is destroyed
  # and re-created (the concern verification (v) raises for the other slice, and it applies
  # here for the same reason - a re-created assignment is a moment in which somebody cannot
  # sign in).
  #
  # WHAT IS DELIBERATELY ABSENT, because absence has to be readable (1b step 3.7):
  #   - sso-group-data-scientists on Data Governance      - the lake is read through the Lake
  #                                                         Formation share, never in place
  #   - sso-group-deployment-managers on Data Governance  - a release approver has no business
  #                                                         in the account that grants access
  #   - sso-group-dev-env-stewards on Staging, Data Governance, Identity, Audit, Log Archive,
  #     Policy Canary                                     - it judges a container image
  #   - EVERY persona on Identity, Audit, Log Archive, Policy Canary, and Management
  #   - every Staging cell                                - the account is unvended
  assignments = {
    # DataScientistAccess - Sandbox AND Development (D21). One set, two accounts (1b 3.3):
    # the two are policy-identical at this level, which is what putting them in one OU asserts.
    "data-scientist@sandbox"     = { set = "data_scientist", group = "data_scientists", account = "sandbox" }
    "data-scientist@development" = { set = "data_scientist", group = "data_scientists", account = "development" }

    # DataScientistProdAccess - Production only (D18). A different SHAPE, not a weaker copy.
    "data-scientist-prod@production" = { set = "data_scientist_prod", group = "data_scientists", account = "production" }

    # DeploymentManagerAccess (D31) - diagnosis, not reading. Nothing on Data Governance.
    "deployment-manager@sandbox"     = { set = "deployment_manager", group = "deployment_managers", account = "sandbox" }
    "deployment-manager@development" = { set = "deployment_manager", group = "deployment_managers", account = "development" }
    "deployment-manager@production"  = { set = "deployment_manager", group = "deployment_managers", account = "production" }

    # GovernanceManagerAccess - Data Governance ONLY, and it is the mirror image of the row
    # above: the one account the deployment manager cannot enter is the only one this one can.
    "governance-manager@data-governance" = { set = "governance_manager", group = "governance_managers", account = "data-governance" }

    # DevEnvStewardAccess - Production, plus Sandbox and Development. The set is read-only
    # everywhere by construction, so "read-only on Sandbox and Development" is a property of
    # the policy rather than of the assignment (1b 3.3: one set object is one policy, however
    # many accounts it reaches).
    "dev-env-steward@production"  = { set = "dev_env_steward", group = "dev_env_stewards", account = "production" }
    "dev-env-steward@sandbox"     = { set = "dev_env_steward", group = "dev_env_stewards", account = "sandbox" }
    "dev-env-steward@development" = { set = "dev_env_steward", group = "dev_env_stewards", account = "development" }
  }

  # ------------------------------------------------------------------- the six written sets
  #
  # THE NAME IS THE ONE THING HERE THAT CANNOT BE CHANGED CASUALLY. `<Persona>Access`, and
  # never within four characters of a Control Tower set - 1b step 3.2 renamed this project's
  # administrator set for exactly that reason, and the argument was that an assignment made
  # against the wrong one still WORKS, so nothing reports it. Changing a name here destroys
  # and re-creates the set, which is a window in which nobody holds it.
  persona_sets = {
    data_scientist = {
      name        = "DataScientistAccess"
      description = "Studio use, scratch and derived read-write, Athena, ECR pull. Not PowerUser, not SageMakerFullAccess (1b 3.4, D21)"
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

  # The two indirections the assignment map resolves through. Written here so a row stays a row
  # of names and the wiring is in one place.
  permission_set_arns = { for k, v in aws_ssoadmin_permission_set.persona : k => v.arn }

  group_ids = {
    data_scientists     = data.aws_identitystore_group.data_scientists.group_id
    deployment_managers = data.aws_identitystore_group.deployment_managers.group_id
    governance_managers = data.aws_identitystore_group.governance_managers.group_id
    dev_env_stewards    = data.aws_identitystore_group.dev_env_stewards.group_id
  }

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
