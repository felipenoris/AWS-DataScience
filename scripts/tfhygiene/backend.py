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
# which aws/INDEX.md rule 1 keeps out of tracked files); the `lake` map to each consumer's
# OWN data/ slice (pass 4); and `data_consumers` to identity/sso (pass 4c, where each row
# becomes the workgroup and derived-bucket ARNs the persona statements name). Adding a row
# therefore re-plans three slices, identity/sso among them - so a consumer that is NOT an
# Interactive persona account must not reach that third emission, which is why Stage 9 step 1.4
# SPLITS this list before adding Production rather than appending to it. Production joins the
# lake-consumer half at Stage 9; a vended Sandbox unit joins the whole list at Stage 14.
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
NETWORK_SLICES = {"foundation", "egress", "vpn", "probes"}

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

    if account == "identity" and slice_name == "sso":
        values["vpn_homes"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in VPN_HOMES
        }
        # Stage 5 pass 4c: the persona grants are scoped to ARNs read from the consumer
        # slices' state (the workgroup, the derived bucket) and from the lake's (the drop-box
        # and its key) - the enumerated form the 4c sequencing bought. Same three-way rule as
        # everywhere else: the CONSUMERS list is the decision, the profile may not sit in a
        # .tf file, and the env token builds the state-bucket name no slice may re-derive.
        values["data_consumers"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in DATA_CONSUMERS
        }
        values["lake"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in DATA_LAKE
        }

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
    if "lake" in v:
        rows = "".join(
            f'  {acct} = {{ profile = "{p["profile"]}", env = "{p["env"]}" }}\n'
            for acct, p in v["lake"].items()
        )
        out += f"lake = {{\n{rows}}}\n"
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
