"""The literals a slice cannot interpolate - the ONE place that builds its two generated files.

A ``backend`` block cannot interpolate anything, so the bucket, the key and the REGION have
to be literals somewhere; the plan forbids region literals in ``.tf`` files, and partial
backend configuration is the reconciliation (Stage 2 step 2.5). ``gen-backend-hcl.py`` is
the only writer and this module is its content; a Makefile target calls the script rather
than growing a second copy (Lesson 14: two mechanisms for one file is a defect waiting).

``terraform.auto.tfvars`` is the same problem one step out and it lands here for the same
reason. The provider's ``region`` may not be a literal either, and a slice may not hardcode
``sandbox`` (step 3.3, D35), so both arrive as variables - from a file that is generated,
untracked (``*.tfvars`` in ``.gitignore``) and written from THIS table. Two generators, one
vocabulary: the region the backend writes and the region the provider uses cannot disagree,
which they could the moment somebody typed the second one.
"""

from __future__ import annotations

# The one region literal, in the one place, for the whole tree.
REGION = "us-west-2"

# The account folder and the <env> NAME TOKEN are two different vocabularies, and there is a
# third - the Environment TAG value - which is different again (docs/plan/conventions.md):
#
#   folder            name token   Environment tag
#   sandbox           sandbox      sandbox
#   development       dev          development
#   data-governance   data         data
#   staging           staging      staging
#   production        prod         production
#   identity          org          org
#
# Only the middle column builds a resource name. Conflating it with the first produces
# `awsds-production-tfstate`, a bucket nobody created; conflating it with the third produces
# `awsds-development-tfstate`, the same failure spelled differently.
ENV_TOKENS = {
    "sandbox": "sandbox",
    "development": "dev",
    "data-governance": "data",
    "staging": "staging",
    "production": "prod",
    "identity": "org",
}

# The third column of the table above, kept separate because it is a different vocabulary and
# not a transformation of the second: `dev` names a bucket, `development` tags one, and a map
# that derived one from the other would be a rule with three exceptions.
ENVIRONMENT_TAGS = {
    "sandbox": "sandbox",
    "development": "development",
    "data-governance": "data",
    "staging": "staging",
    "production": "production",
    "identity": "org",
}


# THE FOURTH VOCABULARY, and it lands here for the reason the other three did: the account
# folder is the key, and a second file keyed by the same thing is Lesson 14 waiting (Stage 2
# step 8, 2026-08-16). `make up` / `make down` have to reach an account, and the only sanctioned
# way is a NAMED SSO PROFILE on the command line - never `eval $(aws sts assume-role ...)`,
# whose credential outlives the command and makes every later error name the wrong account
# (Lesson 25). The profile is on the command line because that is where it can be read.
#
# `sandbox` IS AN ALLOCATION, NOT A FINAL NAME - the same caveat ENV_TOKENS carries. D35 vends
# one Sandbox per business unit and N is 1, so `awsds-infra-sandbox-1` is unit 1's profile and
# not "the sandbox profile". Open question 10's per-unit token is deferred to N=2, and this row
# moves with it.
#
# TWO ACCOUNTS ARE ABSENT ON PURPOSE. `staging` is unvended (step 3.2), so it has no profile to
# name; Log Archive and Audit hold no CLI profile at all and no Terraform slice either.
PROFILES = {
    "sandbox": "awsds-infra-sandbox-1",
    "development": "awsds-infra-dev",
    "data-governance": "awsds-infra-data",
    "production": "awsds-infra-prod",
    "identity": "awsds-infra-identity",
}


# THE ADDRESS ALLOCATION (Stage 3 decision 1, settled 2026-08-16) - the fifth vocabulary,
# keyed by account folder like the other four, reaching each network slice through the
# generated terraform.auto.tfvars. No second file: this module is already the one place a
# slice's generated files are built from (Stage 2 step 2.6), and Stage 14 READS this table
# to allocate the next Sandbox unit - which is why it is tracked Python, not a generated file.
#
# ENTRIES ARE AUTHORED, NEVER COMPUTED. The rule for whoever adds a Sandbox unit: the LOWEST
# FREE /16 in the 10.16.0.0/13 supernet - so unit 2 is 10.16.0.0/16, not 10.21 (10.20 is the
# fifth slot; the table need not be dense, and keeping unit 1 at 10.20 spared editing four
# files). A CIDR computed at vend time is a [P] value that can move on a rebuild, in an
# account somebody is working in (Stage 3 step 1.3).
#
# THE `sandbox` KEY IS AN ALLOCATION, NOT A FINAL NAME (D35, open question 10) - same caveat
# as ENV_TOKENS and PROFILES. The duplicate-/16 check is born with N=2; at N=1 it has nothing
# to compare.
SANDBOX_SUPERNET = "10.16.0.0/13"  # room for 8 business units; avoids 10.30/10.40/10.50

CIDRS = {
    "sandbox": "10.20.0.0/16",  # unit 1 - the literal Stage 4 and the stage's views use
    "production": "10.30.0.0/16",
    "staging": "10.40.0.0/16",
    "development": "10.50.0.0/16",
}

# Outside every VPC range and never seen inside AWS - the WireGuard instance SNATs (Stage 3
# step 6.5, Stage 4 step 4.2). Recorded here because this table is where address literals
# live; emitted as `peer_cidr` to the vpn/ slice since Stage 4 pass 1, and to nothing else.
WIREGUARD_PEER_CIDR = "10.90.0.0/24"

# THE ACCOUNTS THAT PLAY THE VPN-HOME ROLE (Stage 4 step 8.1, 2026-08-17) - the sixth
# vocabulary, and the one that is a ROLE rather than a property. Stage 4's forward constraint
# from D35 says it in those words: the VPN home is a role an account plays, not "the Sandbox
# account", so the thing identity/sso/ pins the control plane to is a LIST from day one -
# one Elastic IP per home as D35 multiplies business units, and adding unit 2 is appending a
# row here rather than editing a policy document.
#
# A LIST, AUTHORED, NEVER DERIVED FROM CIDRS OR PROFILES. Every account in PROFILES has a
# state bucket and most will have a VPC; almost none of them terminates a tunnel. Deriving
# this would silently pin the control plane to whatever foundation/ happened to export an
# `wireguard_eip_public_ip` from - and an account that stops being a VPN home would keep its
# address in the allow-list until somebody noticed. The row is the decision.
#
# WHAT CONSUMES IT: two emissions, both named `vpn_homes` - to identity/sso (below), which
# turns each row into a terraform_remote_state read of that account's foundation/ slice, and
# to data-governance/data since Stage 5 pass 1, where the same addresses become a branch of
# the lake's perimeter deny. Entries must therefore be accounts whose foundation/ EXPORTS the
# EIP - today only sandbox does (Stage 4 step 2.1).
VPN_HOMES = ["sandbox"]

# THE LAKE'S CONSUMERS AND ITS PICKUP PRODUCER (Stage 5 pass 1, 2026-08-18) - the seventh
# vocabulary, authored like VPN_HOMES and for the same reason: which accounts consume the
# governed lake is a decision (INT-03's N+2; decision 5 granted to the two named accounts),
# not something derivable from PROFILES. Consumed by THREE emissions - `consumers`,
# `vpn_homes` and `producers` to data-governance/data, where each row becomes a
# terraform_remote_state read (the [P] gateway-endpoint ids, the WireGuard EIPs) or an
# aliased-provider identity read (the account ids the drop-box statements are built from,
# which aws/INDEX.md rule 1 keeps out of tracked files); and the `lake` map to each
# consumer's OWN data/ slice (pass 4). A THIRD emission - `data_consumers` to identity/sso,
# pass 4c's workgroup and derived-bucket ARNs - left on 2026-08-26 with the derived zone
# itself (D19 revised), which also retired the reason Stage 9 step 1.4 had to SPLIT this list
# before adding Production: no emission reaches identity/sso from here any more. Production
# joins at Stage 9; a vended Sandbox unit at Stage 14.
DATA_CONSUMERS = ["sandbox", "development"]
DATA_PRODUCERS = ["production"]

# THE OTHER DIRECTION, added at pass 4 (2026-08-19): the account that OWNS the lake, read BY
# the consumers. It is a one-element table and it is still a table, for the reason the three
# above are: the consumer slices resolve the lake's catalog id through an aliased provider and
# read its state for the shared database names, and both need a PROFILE - which may be a
# literal in no .tf file (Lesson 14). D22 makes this a singleton forever, so the list is not
# expected to grow; what it buys is that the emissions below have the same shape as every
# other cross-account read in this tree instead of a special case. Two of them: the `lake` map
# goes to each consumer's data/ slice (pass 4) and to identity/sso (pass 4c, for the drop-box
# prefix and the lake data key the persona's write statements name).
DATA_LAKE = ["data-governance"]

# THE SUPPLY CHAIN'S CONSUMERS (Stage 7 step 5.4, applied at Stage 6 pass 0) - the eighth
# vocabulary, and D35's forward constraint written as a table rather than as three literals.
# production/registry/ enumerates them in FOUR policies: the ECR registry policy, the two
# repository policies, the CodeArtifact domain policy and the slice's own KMS key policy. A
# vend adds one row here and nothing else changes (Lesson 14; Stage 7's option-preservation
# note). The row carries the profile because the slice resolves each consumer's ACCOUNT ID
# through an aliased provider - aws/INDEX.md rule 1 keeps ids out of tracked files, and a
# pasted id would be the copy Lesson 3 warns about.
#
# IT IS NOT DATA_CONSUMERS. The two lists happen to hold the same two rows today and answer
# different questions: who reads the governed LAKE, and who pulls IMAGES AND PACKAGES. Stage 9
# adds production to the first and must not add it to the second (the registry lives there),
# which is exactly the split Stage 9 step 1.4 already anticipates for the lake list.
REGISTRY_CONSUMERS = ["sandbox", "development"]

# THE UNIFIED DOMAIN AND ITS MEMBER ACCOUNTS (Stage 6, D26/D35) - the ninth and tenth
# vocabularies, and the second one is a MEASUREMENT rather than a decision, which is why it
# is worth reading the comment before editing the list.
#
# SMUS_DOMAIN is the account that owns the domain: a singleton by D22/D26, kept as a list so
# the emissions below have the same shape as every other cross-account read in this tree.
# Consumed by each member's sagemaker/ slice, which resolves the domain id out of
# data-governance/governance/'s state.
#
# TWO LISTS, AND THE SPLIT IS THE WHOLE POINT: one is a DECISION and the other a MEASUREMENT,
# and merging them would make it impossible to tell "we have not associated this account yet"
# from "this account was never meant to be a member" (D28: Staging and Production never are).
#
#   SMUS_MEMBERS     the accounts that are meant to be associated - D26/D35's answer, and the
#                    map the project profiles' environment configurations are built from. It
#                    is also what the aliased providers in data-governance/governance/ resolve
#                    account ids through, so it must be populated from the first apply.
#   SMUS_ASSOCIATED  the accounts whose association has actually been ACCEPTED. The account
#                    association is console-only - there is no public associate-account API
#                    (Stage 6 step 1.3) - so a row is added AFTER the invitation is accepted in
#                    the member account, and the SECOND apply of that account's sagemaker/
#                    slice is what creates its blueprint configurations. Adding a row before
#                    the association exists produces an apply that fails inside
#                    PutEnvironmentBlueprintConfiguration - the honest failure; adding one
#                    after an association was REVOKED produces a slice that keeps re-creating
#                    a configuration nobody can use, which is not.
#
# THE MEASUREMENT GATES BOTH SIDES OF THE SAME ORDERING. A project profile's environment
# configurations name (blueprint, account, region), and the blueprint has to be configured in
# that account first - so the profiles wait until EVERY member is associated, which is what
# `profiles_enabled` below computes rather than restates.
# THE GATE IS MONOTONE ONLY ON THE FIRST BUILD, and that is the half a reader of the two rows
# above will not guess. `profiles_enabled` below feeds a `for_each` in
# data-governance/governance/profiles.tf - and the blueprint-id lookup in its data.tf - so it
# REVERSES: a member added to SMUS_MEMBERS while SMUS_ASSOCIATED lacks it takes the flag back to
# false, and the next apply of governance/ DESTROYS the project profiles that already exist, or
# fails outright if projects hang off them.
#
# SO, ONCE A PROFILE EXISTS, THE SMUS_ASSOCIATED ROW IS WRITTEN BEFORE THE SMUS_MEMBERS ROW,
# never the other way round. The tell is a plan showing `awscc_datazone_project_profile`
# destroyed - which is why the by-hand change reads the add/change/DESTROY counts before
# applying (docs/plan/runbooks/terraform-changes.md, Recipe A step 5). The ordering itself is
# not this file's to carry: the stage that performs it is Stage 14 step 4, for a vended unit.

SMUS_DOMAIN = ["data-governance"]
SMUS_MEMBERS = ["sandbox", "development"]
# MEASURED 2026-08-21, not assumed: the association raised no invitation (organization-scoped share,
# Stage 1d's org-wide RAM enablement), so the console's "Associated" label is not the evidence. What is:
# `datazone list-environment-blueprint-configurations --domain-identifier dzd-...` run as each member's
# OWN profile SUCCEEDS and returns an empty list - a call that cannot succeed at all before the
# association. Both rows are added in one edit because both accounts were associated in one act; the
# APPLY ORDER is what is staged, not this list (Stage 6 step 1.4 before 1.5).
SMUS_ASSOCIATED: list = ["sandbox", "development"]

# ------------------------------------------------- the persona's project-storage vending policy
#
# ONE NAME, THREE SLICES, AND IT IS A CONTRACT RATHER THAN A CONVENTION. A customer-managed
# policy is referenced from a permission set BY NAME, and the object must exist under that exact
# name in EVERY account the set is provisioned into - a missing one fails PROVISIONING, per
# account, in an account nobody is watching (the failure decision 4 deferred the boundary over).
# So the name is generated here and consumed by three slices, never typed three times
# (Lesson 14): each member's foundation/ creates the object, identity/sso/ references it.
#
# `org` IS THE CORRECT ENV TOKEN AND THE EXCEPTION IS THE POINT. Every other name in this design
# carries the token of the account it lives in - but this object is materialised in sandbox AND
# development under ONE name, so an <env> token would make the two names differ and a permission
# set can reference only one. conventions.md gives `org` to platform resources of the identity
# plane, which is exactly what this is: entitlement-plane content that happens to need a per-
# account body. The Environment TAG still says sandbox or development, because the tag describes
# where the object lives and the name describes what references it.
PERSONA_VENDING_POLICY_NAME = "awsds-org-project-storage-vending"

# WHERE THAT OBJECT MUST EXIST - and the list AWS actually constrains is "every account
# DataScientistAccess is provisioned into", which is authored in identity/sso/locals.tf's
# `assignments` map and cannot be read from here. DERIVED from SMUS_MEMBERS rather than authored
# a third time: only a SMUS member account can hold an S3 Access Grants instance to vend from,
# and the set's two assignment rows name exactly these accounts today. If the two ever diverge,
# THIS LIST FOLLOWS THE ASSIGNMENTS, not the members - the symptom of getting it wrong is a
# provisioning error in the account that was left out, not a plan failure here.
PERSONA_VENDING_ACCOUNTS = list(SMUS_MEMBERS)

# Subnets anchor on ZONE IDS, never on AZ names and never on list position (Stage 3 step 1.5,
# settled by 1b step 6; ./aws/AZs.py is the measurement). Authored per account because a
# vended account is assigned its own name->id mapping and may legitimately differ (INV-08);
# all measured accounts agree today, so the pairs are identical - that is a reading, not a rule.
ZONE_IDS = {
    "sandbox": ["usw2-az1", "usw2-az2"],
    "production": ["usw2-az1", "usw2-az2"],
    "staging": ["usw2-az1", "usw2-az2"],
    "development": ["usw2-az1", "usw2-az2"],
}

# The slices whose generated tfvars carry the allocation. bootstrap/ deliberately does not:
# it has no subnet, and an unused zone list would send the next reader hunting for the
# resource that consumes it (gen-tfvars.py's original argument, now scoped instead of total).
NETWORK_SLICES = {"foundation", "egress", "vpn", "probes", "buildbox"}

# Stage 3's reachability probes: which accounts each side has to admit or reach. Every side's
# security group names the OTHER side's VPC range, and the pairing is authored here rather
# than in any slice, for the same reason CIDRS is - an address literal in a .tf file is a copy
# of this table that nothing keeps in step (Lesson 14).
#
# THE TARGET ADMITS BOTH SOURCES, and that is not symmetry for its own sake: Sandbox to
# Production is the peering the Deliverables measure, and Development to Production is INT-09,
# the integration this stage's Proves row claims. One target host exercises both, so the
# second source costs one instance rather than a second target.
PROBE_PEERS = {
    "sandbox": ["production"],
    "development": ["production"],
    "production": ["sandbox", "development"],
}


class UnknownAccountFolder(Exception):
    """An account folder outside the vocabulary above."""


def profile(account: str) -> str:
    """The SSO profile a slice in this account is applied through."""
    try:
        return PROFILES[account]
    except KeyError:
        raise UnknownAccountFolder(account) from None


def env_token(account: str) -> str:
    try:
        return ENV_TOKENS[account]
    except KeyError:
        raise UnknownAccountFolder(account) from None


def backend_values(account: str, slice_name: str) -> dict:
    """bucket, key and kms alias for one slice - the values the file is written from."""
    token = env_token(account)
    kms_alias = f"alias/awsds-{token}-tfstate"
    # D36, and it is the detail that decides whether D36 is a control or a folder:
    # production/pki/ holds the internal root CA's private key IN ITS STATE FILE. If it
    # shared the account state key, "who can read Production state" and "who can mint a
    # certificate for any internal name" would be one permission. Both keys are created by
    # production/bootstrap/ (step 3.4) - a key the pki/ slice created could not encrypt the
    # backend that has to exist before it applies.
    if account == "production" and slice_name == "pki":
        kms_alias = "alias/awsds-prod-tfstate-pki"
    return {
        "bucket": f"awsds-{token}-tfstate",
        "key": f"{account}/{slice_name}/terraform.tfstate",
        "region": REGION,
        "kms_key_id": kms_alias,
    }


def tfvars_values(account: str, slice_name: str) -> dict:
    """region, env token, Environment tag - plus, for a network slice, the allocation.

    The extras are emitted ONLY WHERE A CONSUMER EXISTS, per slice: an emitted value no
    variable declares is a Terraform warning on every plan, and a declared variable nothing
    consumes is a tflint failure - either way, noise that trains the reader to stop reading.
    The D22 guard covers every network slice: Data Governance has no VPC and no CIDRS row,
    so a network slice there fails loudly here rather than applying with a hole.
    """
    token = env_token(account)  # raises UnknownAccountFolder before anything else is read
    values = {
        "region": REGION,
        "env": token,
        "environment_tag": ENVIRONMENT_TAGS[account],
    }
    if slice_name in NETWORK_SLICES:
        if account not in CIDRS:
            raise UnknownAccountFolder(
                f"{account}: network slice '{slice_name}' but no CIDR allocation - "
                "D22 accounts hold no VPC; a new account is added to CIDRS deliberately"
            )
        values["zone_ids"] = ZONE_IDS[account]
        if slice_name == "foundation":
            values["vpc_cidr"] = CIDRS[account]
            # Stage 3 pass 2: the peers map - every VPC-bearing account that has a profile,
            # DERIVED from the two tables above rather than authored a third time (Lesson 14).
            # The slice's aliased providers read a peer's [P] facts (VPC, subnets, route
            # tables) live instead of copying them here: an id in a tfvars would be a stale
            # copy of another slice's state. Staging is absent because PROFILES has no row
            # until the vend; the self-row is emitted too and simply unused.
            values["peers"] = {
                acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]}
                for acct in sorted(CIDRS)
                if acct in PROFILES
            }
        else:
            # egress/ (pass 3) - and Stage 4's vpn/ when it decides - read foundation/'s
            # [P] facts through terraform_remote_state instead of carrying copies. The
            # state KEY is keyed by the ACCOUNT FOLDER (backend_values above), which no
            # .tf file may re-derive from the env token: the reverse map would be a
            # second copy of ENV_TOKENS (Lesson 14). So the folder name rides along.
            values["account_folder"] = account
            if slice_name == "vpn":
                # Stage 4 step 4.2 - the WireGuard client range, which is NOT chosen in the
                # slice. It is the one address literal in this table that never appears
                # inside AWS: the host SNATs, so no VPC, route table or security group ever
                # sees it, and its single job is not colliding with a home or cafe LAN.
                values["peer_cidr"] = WIREGUARD_PEER_CIDR
            # NOTHING EXTRA FOR `buildbox`, AND THE ABSENCE IS A DECISION TAKEN THE DAY THE
            # SLICE WAS BUILT (2026-08-21). It briefly took WIREGUARD_PEER_CIDR, to admit the
            # tunnel's clients on its security group - and the requirement behind that was
            # WITHDRAWN by the user the same day, once a measurement showed the rule did not
            # gate the one path anybody uses: `ssm start-session` reaches the agent's OUTBOUND
            # channel and no security group sees it. The buildbox now has no ingress rule at
            # all, so an emission here would feed a variable that feeds nothing.
            if slice_name == "probes":
                # Each side's security group names the OTHER side's VPC range: Production
                # admits the source, Sandbox egresses to the target. Keeping the peer range
                # WHOLE is deliberate - the permitted address and the forbidden one are both
                # inside it, so the security group is constant across the pair and the route
                # is the single variable the reading turns on.
                if account not in PROBE_PEERS:
                    raise UnknownAccountFolder(
                        f"{account}: 'probes' is the Sandbox-Production pair of Stage 3's "
                        "Deliverables - another account joins PROBE_PEERS deliberately"
                    )
                values["peer_cidrs"] = [CIDRS[p] for p in PROBE_PEERS[account]]

    # THE FIRST NON-NETWORK EMISSION, and the repository's first CROSS-ACCOUNT remote-state
    # read (Stage 4 step 8.1) - Stage 5's maps below follow the same shape.
    # identity/sso/ pins the six persona sets to the WireGuard Elastic IP,
    # and the address may not be pasted: it is read from each VPN home's foundation/ state.
    # That read crosses an account boundary, so - unlike every same-account read in this tree -
    # it needs a PROFILE in the data source's config, and pass 2's rule is that a profile
    # literal never sits in a .tf file (Lesson 14; peers.tf's own comment). So it arrives the
    # same way `peers` does for foundation/: keyed by ACCOUNT FOLDER, carrying the profile and
    # the env token the bucket name is built from. One SSO login covers both profiles - they
    # share the `awsds` sso-session - which is what makes a cross-account read workable at all.
    # Stage 5's cross-account reads - the identity/sso shape, three maps (see DATA_CONSUMERS).
    if account == "data-governance" and slice_name == "data":
        values["consumers"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in DATA_CONSUMERS
        }
        values["vpn_homes"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in VPN_HOMES
        }
        values["producers"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in DATA_PRODUCERS
        }

    # The consumer side of the lake (Stage 5 pass 4). Emitted for `data` in any account that
    # CONSUMES the lake - never for data-governance itself, which owns it and whose own `data`
    # slice takes the three maps above instead. The guard is DATA_CONSUMERS rather than "not
    # data-governance", so a new consumer arrives by being written down (Stage 9 adds
    # production, Stage 14 a vended unit) rather than by having a folder.
    if slice_name == "data" and account in DATA_CONSUMERS:
        values["lake"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in DATA_LAKE
        }

    # Stage 6 pass 0 - production/registry/'s consumer map (Stage 7 step 5.4).
    if account == "production" and slice_name == "registry":
        values["consumers"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]}
            for acct in REGISTRY_CONSUMERS
        }

    # Stage 6 pass 1 and pass 2 - the blueprint prerequisites and, on the second apply, the
    # blueprint configurations. account_folder is the same emission every non-foundation
    # network slice takes: this slice reads its OWN foundation/ state for the VPC, the subnets
    # and the endpoint security group, and the state KEY is keyed by the account FOLDER, which
    # no .tf file may re-derive from the env token (Lesson 14).
    if slice_name == "sagemaker":
        values["account_folder"] = account
        # TWO MAPS AT THE SAME ACCOUNT, AND THEY ARE NOT ONE MAP. `lake` is the governed lake's
        # state (the registered bucket ARNs the D13 boundary excludes, the drop-box prefix, the
        # lake data key); `domain` is the SMUS registry's. D22/D26 put both in Data Governance
        # today, so the two rows are identical - and merging them would be the coincidence
        # Lesson 10 warns about: they answer different questions and a design that separated
        # them would have to unpick one emission from the other.
        values["lake"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in DATA_LAKE
        }
        values["domain"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in SMUS_DOMAIN
        }
        values["blueprints_enabled"] = account in SMUS_ASSOCIATED

    # Stage 6 pass 2 - the domain account's own slice. The members map is what the project
    # profiles' environment configurations are built from (one per member account); the flag
    # is a SMUS_ASSOCIATED reading over the same members, so the profiles cannot be written before the
    # blueprints they name are configured.
    if account == "data-governance" and slice_name == "governance":
        values["members"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in SMUS_MEMBERS
        }
        values["profiles_enabled"] = bool(SMUS_MEMBERS) and set(SMUS_MEMBERS) <= set(
            SMUS_ASSOCIATED
        )
        # The directory read (2026-08-22, grants.tf): who may create a project from which
        # profile is granted to an sso-group-*, and IdC is delegated to Identity - so the
        # slice needs one read-only alias pointing there. The NAMES are the decision and they
        # live in the slice's locals.tf; only the profile that can resolve them comes from
        # here, the same way every other cross-account read in this table does.
        values["identity_profile"] = PROFILES["identity"]

    # The persona's vending policy: the OBJECT half, in each account the set reaches (the name
    # block above carries the argument). foundation/ rather than sagemaker/ because a permission
    # set that cannot find this policy fails to provision - so it must outlive every slice that
    # can be torn down, and foundation/ is [P].
    if slice_name == "foundation" and account in PERSONA_VENDING_ACCOUNTS:
        values["persona_vending_policy_name"] = PERSONA_VENDING_POLICY_NAME

    if account == "identity" and slice_name == "sso":
        values["vpn_homes"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in VPN_HOMES
        }
        # Stage 5 pass 4c put TWO cross-account reads here; ONE left on 2026-08-26. The
        # `data_consumers` map (each consumer's workgroup + derived-bucket ARNs) left with the
        # derived zone itself (D19 revised - the zone re-homed onto the SMUS project path, the
        # persona's Athena and derived statements removed). The lake map stays: the drop-box
        # write and its key are the INGESTION path, untouched by the revision.
        values["lake"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in DATA_LAKE
        }
        # The persona's vending policy: the REFERENCE half. The set names the policy; the object
        # is created by each member's foundation/ (the emission above), and the apply order is
        # members first - a reference to a policy that does not exist yet fails provisioning.
        values["persona_vending_policy_name"] = PERSONA_VENDING_POLICY_NAME

    return values


def render_tfvars(account: str, slice_name: str) -> str:
    """The full terraform.auto.tfvars content for one slice, regeneration note included."""
    v = tfvars_values(account, slice_name)
    out = (
        "# GENERATED by scripts/gen-tfvars.py - do not edit, and do not commit (.gitignore).\n"
        f"# Regenerate with: ./scripts/gen-tfvars.py {account} {slice_name}\n"
        "# Auto-loaded by terraform: the name ends in .auto.tfvars, so no -var-file is needed.\n"
        f'region          = "{v["region"]}"\n'
        f'env             = "{v["env"]}"\n'
        f'environment_tag = "{v["environment_tag"]}"\n'
    )
    if "vpc_cidr" in v:
        out += f'vpc_cidr        = "{v["vpc_cidr"]}"\n'
    if "zone_ids" in v:
        zone_list = ", ".join(f'"{z}"' for z in v["zone_ids"])
        out += f"zone_ids        = [{zone_list}]\n"
    if "account_folder" in v:
        out += f'account_folder  = "{v["account_folder"]}"\n'
    if "peer_cidr" in v:
        out += f'peer_cidr       = "{v["peer_cidr"]}"\n'
    if "peer_cidrs" in v:
        cidr_list = ", ".join(f'"{c}"' for c in v["peer_cidrs"])
        out += f"peer_cidrs      = [{cidr_list}]\n"
    if "peers" in v:
        rows = "".join(
            f'  {acct} = {{ profile = "{p["profile"]}", env = "{p["env"]}" }}\n'
            for acct, p in v["peers"].items()
        )
        out += f"peers = {{\n{rows}}}\n"
    if "consumers" in v:
        rows = "".join(
            f'  {acct} = {{ profile = "{p["profile"]}", env = "{p["env"]}" }}\n'
            for acct, p in v["consumers"].items()
        )
        out += f"consumers = {{\n{rows}}}\n"
    if "vpn_homes" in v:
        rows = "".join(
            f'  {acct} = {{ profile = "{p["profile"]}", env = "{p["env"]}" }}\n'
            for acct, p in v["vpn_homes"].items()
        )
        out += f"vpn_homes = {{\n{rows}}}\n"
    if "data_consumers" in v:
        rows = "".join(
            f'  {acct} = {{ profile = "{p["profile"]}", env = "{p["env"]}" }}\n'
            for acct, p in v["data_consumers"].items()
        )
        out += f"data_consumers = {{\n{rows}}}\n"
    if "producers" in v:
        rows = "".join(
            f'  {acct} = {{ profile = "{p["profile"]}", env = "{p["env"]}" }}\n'
            for acct, p in v["producers"].items()
        )
        out += f"producers = {{\n{rows}}}\n"
    if "blueprints_enabled" in v:
        out += f"blueprints_enabled = {str(v['blueprints_enabled']).lower()}\n"
    if "profiles_enabled" in v:
        out += f"profiles_enabled = {str(v['profiles_enabled']).lower()}\n"
    if "domain" in v:
        rows = "".join(
            f'  {acct} = {{ profile = "{p["profile"]}", env = "{p["env"]}" }}\n'
            for acct, p in v["domain"].items()
        )
        out += f"domain = {{\n{rows}}}\n"
    if "members" in v:
        rows = "".join(
            f'  {acct} = {{ profile = "{p["profile"]}", env = "{p["env"]}" }}\n'
            for acct, p in v["members"].items()
        )
        out += f"members = {{\n{rows}}}\n"
    if "lake" in v:
        rows = "".join(
            f'  {acct} = {{ profile = "{p["profile"]}", env = "{p["env"]}" }}\n'
            for acct, p in v["lake"].items()
        )
        out += f"lake = {{\n{rows}}}\n"
    if "persona_vending_policy_name" in v:
        out += f'persona_vending_policy_name = "{v["persona_vending_policy_name"]}"\n'
    if "identity_profile" in v:
        out += f'identity_profile = "{v["identity_profile"]}"\n'
    return out


def render(account: str, slice_name: str) -> str:
    """The full backend.hcl content for one slice, regeneration note included."""
    v = backend_values(account, slice_name)
    return (
        "# GENERATED by scripts/gen-backend-hcl.py - do not edit, and do not commit (.gitignore).\n"
        f"# Regenerate with: ./scripts/gen-backend-hcl.py {account} {slice_name}\n"
        "# Consume with:    terraform init -backend-config=backend.hcl\n"
        f'bucket       = "{v["bucket"]}"\n'
        f'key          = "{v["key"]}"\n'
        f'region       = "{v["region"]}"\n'
        f'kms_key_id   = "{v["kms_key_id"]}"\n'
        "encrypt      = true\n"
        "use_lockfile = true\n"
    )
