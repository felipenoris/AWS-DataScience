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
# live; emitted to no slice until Stage 4's vpn/ consumes it.
WIREGUARD_PEER_CIDR = "10.90.0.0/24"

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
NETWORK_SLICES = {"foundation", "egress", "vpn"}


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

    The extra two (vpc_cidr, zone_ids) are emitted only where a consumer exists: a network
    slice of an account that holds a row in CIDRS. Data Governance has no VPC (D22) and no
    row, so a network slice there fails loudly here rather than applying with a hole.
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
        values["vpc_cidr"] = CIDRS[account]
        values["zone_ids"] = ZONE_IDS[account]
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
        zone_list = ", ".join(f'"{z}"' for z in v["zone_ids"])
        out += f'vpc_cidr        = "{v["vpc_cidr"]}"\nzone_ids        = [{zone_list}]\n'
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
