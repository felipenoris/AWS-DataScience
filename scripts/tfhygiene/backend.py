"""The literals a slice cannot interpolate - the one place that builds its two generated files.

A ``backend`` block cannot interpolate anything, so the bucket, the key and the region have to
be literals somewhere; the plan forbids region literals in ``.tf`` files, and partial backend
configuration is the reconciliation (Stage 2 step 2.5). ``gen-backend-hcl.py`` is the only
writer and this module is its content; a Makefile target calls the script rather than growing
a second copy (Lesson 14).

``terraform.auto.tfvars`` is the same problem one step out. The provider's ``region`` may not
be a literal either, and a slice may not hardcode ``sandbox`` (step 3.3, D35), so both arrive
as variables, from a file that is generated, untracked (``*.tfvars`` in ``.gitignore``) and
written from this table. Two generators, one vocabulary: the region the backend writes and the
region the provider uses cannot disagree.
"""

from __future__ import annotations

import json

# The one region literal, in the one place, for the whole tree.
REGION = "us-west-2"

# The account folder and the <env> name token are two different vocabularies, and the
# Environment tag value is a third (docs/plan/conventions.md):
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
    "data-governance": "data",
    "staging": "staging",
    "production": "production",
    "identity": "org",
}


# The fourth vocabulary, keyed by the account folder like the other three: a second file keyed
# by the same thing is Lesson 14 waiting (Stage 2 step 8). `make up` / `make down` have to reach
# an account, and the only sanctioned way is a named SSO profile on the command line - never
# `eval $(aws sts assume-role ...)`, whose credential outlives the command and makes every later
# error name the wrong account (Lesson 25). The profile is on the command line because that is
# where it can be read.
#
# `sandbox` is an allocation, not a final name, the same caveat ENV_TOKENS carries. D35 vends
# one Sandbox per business unit and N is 1, so `awsds-infra-sandbox-1` is unit 1's profile and
# not "the sandbox profile". Open question 10's per-unit token is deferred to N=2, and this row
# moves with it.
#
# Two accounts are absent on purpose: Log Archive and Audit hold no CLI profile at all and no
# Terraform slice either.
PROFILES = {
    "sandbox": "awsds-infra-sandbox-1",
    "staging": "awsds-infra-staging",
    "data-governance": "awsds-infra-data",
    "production": "awsds-infra-prod",
    "identity": "awsds-infra-identity",
}


# The address allocation (Stage 3 decision 1), keyed by account folder like the other
# vocabularies and reaching each network slice through the generated terraform.auto.tfvars. No
# second file: this module is already the one place a slice's generated files are built from
# (Stage 2 step 2.6), and Stage 14 reads this table to allocate the next Sandbox unit, which is
# why it is tracked Python and not a generated file.
#
# Entries are authored, never computed. The rule for whoever adds a Sandbox unit: the lowest
# free /16 in the 10.16.0.0/13 supernet, so unit 2 is 10.16.0.0/16, not 10.21 (10.20 is the
# fifth slot; the table need not be dense, and keeping unit 1 at 10.20 spared editing four
# files). A CIDR computed at vend time is a [P] value that can move on a rebuild, in an
# account somebody is working in (Stage 3 step 1.3).
#
# The `sandbox` key is an allocation, not a final name (D35, open question 10), the same caveat
# as ENV_TOKENS and PROFILES. The duplicate-/16 check is born with N=2; at N=1 it has nothing
# to compare.
SANDBOX_SUPERNET = "10.16.0.0/13"  # room for 8 business units; avoids 10.30/10.40/10.50

# Keyed by (account, slice), not by account, because a per-account `CIDRS` had no reader that
# asks an account-level question (measured 2026-09-06, every call site): `vpc_cidr` wants the
# slice's own VPC, the D22 guard wants "does this slice have an allocation", `peer_cidrs` wants a
# peer VPC's range, and the doc gate iterates the values. Each of those read per-account only
# because every account had exactly one VPC. With three in Production (D38) the per-account shape
# stops being expressible - `CIDRS["production"]` has no single answer - and two tables carrying
# the same numbers is Lesson 33 with nothing bought.
#
# Stage 14 is the one human reader and it still works: "the lowest free /16 in 10.16.0.0/13" is a
# question about the values, and they are all here. So unit 2 is 10.16.0.0/16, not 10.21.
#
# Entries are authored, never computed: a CIDR computed at vend time is a [P] value that can
# move on a rebuild, in an account somebody is working in (Stage 3 step 1.3). The `sandbox` key
# is an allocation, not a final name (D35, open question 10).
#
# 10.40.0.0/16 is deliberately absent and stays that way. It was reserved for a `Staging` vend
# the account cap refused; Stage 6b renamed `Development` instead, so Staging is 10.50 and 10.40
# belongs to nobody. `./aws/networking.py`'s NT-3/NT-5/NT-6 measure that AWS agrees.
# 10.60.0.0/16 is D38's reservation for the day an account slot frees.
#
# The two Production rows with no folder yet are here under the same rule as `layers.py`'s ranks:
# declared before the slice arrives, because the address plan is the part that gets got wrong
# once. `networking` is D38's hub (the estate's only IGW); `workloads` is the production runtime.
VPC_CIDRS = {
    ("sandbox", "foundation"): "10.20.0.0/16",  # unit 1 - the literal Stage 4 and the views use
    ("production", "foundation"): "10.30.0.0/16",  # VPC-SharedServices after 6c step 1.1
    ("production", "networking"): "10.31.0.0/16",  # VPC-Networking, D38's hub (6c step 1.2)
    ("production", "workloads"): "10.32.0.0/16",  # VPC-Workloads (6c step 1.3)
    ("staging", "foundation"): "10.50.0.0/16",  # the renamed Development - a CIDR is immutable
}


# Which VPC inside the account, by name. A second table keyed identically to VPC_CIDRS rather
# than a field of it, because it answers a different question: that one is the address plan,
# this one is the naming plan, and they change for different reasons. Sharing the key keeps them
# from drifting apart on the part that matters.
#
# Absent means empty, and empty reproduces the pre-6c names byte for byte, which is why
# `sandbox/foundation` and `staging/foundation` are not here and their plans read `No changes`
# across the vpc-v0.2.0 bump. `foundation` maps to `shared` rather than to itself because the
# folder name is a lifecycle word and the VPC is VPC-SharedServices (D38); the other two are
# their slice names, which is what makes the pair readable in a console.
VPC_NAME_SUFFIXES = {
    ("production", "foundation"): "shared",
    ("production", "networking"): "networking",
    ("production", "workloads"): "workloads",
}


def vpc_name_suffix_of(account: str, slice_name: str) -> str:
    """The VPC's name suffix inside its account - empty when the account holds only one."""
    return VPC_NAME_SUFFIXES.get((account, slice_name), "")


# The peering matrix (Stage 6c step 3.1). Each row is (requester account, requester slice,
# accepter account, accepter slice). Both sides of every peering are generated from this one
# list, which is what 0.6 asked for: the requester lives in the spoke and the accepter in
# Production, and each side used to be hand-written in its own file with nothing tying them
# together (Lesson 14).
#
# What is not here is a control, not a backlog, and is named so it is not "fixed" by someone who
# reads a gap as an oversight:
#
#   Sandbox <-> Staging                 - Interactive and Workloads never talk. The user's brief.
#   Sandbox <-> VPC-Workloads           - same rule, other end.
#   VPC-SharedServices <-> Staging      - deployment is an API act. The runner assumes a role
#   VPC-SharedServices <-> VPC-Workloads  across the account boundary and calls SageMaker,
#                                         CloudFormation and S3; artifacts travel as ECR images,
#                                         CodeArtifact packages and S3 objects, each reached
#                                         through an endpoint in the target's own VPC. Nothing in
#                                         a deployment target clones a repository - the image
#                                         carries the code (D28) - so a runtime `git clone` there
#                                         is a contract violation to catch, not a path to give.
#                                         Building them would grant standing L3 reach from the
#                                         host that executes repository-supplied build code into
#                                         both deployment targets: D14's blast radius, widened
#                                         (Lesson 2).
#
# The trigger for adding one, so it is recognised rather than rediscovered: a shared service
# consumed at runtime rather than at deploy time. Candidates, none of which exists today - a
# package mirror on an instance (as opposed to ECR and CodeArtifact, which are endpoints), a
# metrics or log collector that is not CloudWatch, an internal secrets or configuration service,
# a certificate-status endpoint. The internal CA is not one: D36 issues no CRL and runs no OCSP
# responder, by decision. Prefer a regional service or an endpoint; the peering is the last
# resort, and it is generated from this same list.
#
# Staging reaches only the hub, for the proxy: the
# `("staging", "foundation", "production", "foundation")` row was removed at this step.
PEERINGS = [
    ("sandbox", "foundation", "production", "networking"),  # VPN reach, the proxy
    ("staging", "foundation", "production", "networking"),  # the proxy
    ("production", "workloads", "production", "networking"),  # the proxy
    ("production", "foundation", "production", "networking"),  # the proxy, and the VPN to GitLab
    ("sandbox", "foundation", "production", "foundation"),  # git clone from a notebook (INT-09)
]


def peerings_of(account: str, slice_name: str) -> list[dict]:
    """Every peering this slice is an end of, with the far end resolved from the same tables.

    One list per slice, both roles in it: a slice can be the requester of one peering and the
    accepter of another, which `production/foundation` is today.
    """
    out = []
    for r_acct, r_slice, a_acct, a_slice in PEERINGS:
        if (account, slice_name) == (r_acct, r_slice):
            role, peer_a, peer_s = "requester", a_acct, a_slice
        elif (account, slice_name) == (a_acct, a_slice):
            role, peer_a, peer_s = "accepter", r_acct, r_slice
        else:
            continue
        out.append(
            {
                "key": f"{r_acct}-{r_slice}--{a_acct}-{a_slice}",
                "role": role,
                "peer_account": peer_a,
                "peer_slice": peer_s,
                "peer_cidr": VPC_CIDRS[(peer_a, peer_s)],
                "peer_profile": PROFILES[peer_a],
                "peer_env": ENV_TOKENS[peer_a],
                "peer_name_suffix": vpc_name_suffix_of(peer_a, peer_s),
                "same_account": peer_a == account,
            }
        )
    return out


def vpc_cidr_of(account: str, slice_name: str) -> str | None:
    """The /16 of one slice's VPC, or None when that slice has no allocation."""
    return VPC_CIDRS.get((account, slice_name))


def account_cidrs(account: str) -> list[str]:
    """Every /16 an account holds, in table order. Production holds three since 6c."""
    return [c for (a, _s), c in VPC_CIDRS.items() if a == account]


def vpc_bearing_accounts() -> list[str]:
    """The accounts with at least one VPC, sorted - what the `peers` map is keyed on today."""
    return sorted({a for a, _s in VPC_CIDRS})


# Outside every VPC range - the WireGuard instance SNATs (Stage 3 step 6.5, Stage 4 step 4.2).
# Recorded here because this table is where address literals live.
#
# `10.90.0.0/24` is seen inside AWS since 6c step 4.1 (Lesson 49). D38 puts the proxy and the
# tunnel endpoint in one VPC, and step 4.7 stops masquerading packets bound for the proxy so
# that Squid's access log carries a per-device address. The proxy's security group must admit
# the range and the hub's public route table must send it at the WireGuard host's ENI, so it is
# emitted to VPN_HOST_SLICE as well.
WIREGUARD_PEER_CIDR = "10.90.0.0/24"

# The same tunnel, in the other family. A ULA, and it exists to make `AllowedIPs = ::/0` in a
# client config real rather than to carry IPv6 traffic: every VPC in this estate is IPv4-only
# (measured), so the tunnel host has no IPv6 uplink, and what this buys is that a device's IPv6
# enters the tunnel and is rejected there instead of leaving by the device's own uplink, outside
# the proxy and outside the access log.
#
# `fd90::` mirrors `10.90.` on purpose, a deliberate departure from RFC 4193's
# randomly-generated global ID. That rule exists so two private networks can merge without
# colliding; this prefix never leaves the tunnel and this estate has no other IPv6, so the
# collision it guards against cannot happen, while the readability is real: `fd90::3` is the
# device that is `10.90.0.3`, and the roster, the handshake log and the proxy's access log all
# key on that host number.
WIREGUARD_PEER_CIDR_V6 = "fd90::/64"

# The private address space - a standard constant, not one of this project's allocations, which
# is why it sits apart from VPC_CIDRS above (6c steps 4.7/4.8).
#
# It is central rather than written twice because pass 4 puts the same list in two places with
# opposite polarity: the WireGuard host forwards tunnel packets only to these ranges (a private
# network client has no business reaching a public address directly - the proxy is the door),
# and Squid denies these ranges as destinations (without that, an explicit proxy is an L7 bridge
# between VPCs that peering deliberately keeps apart - D38's own hole). A range added to one and
# missed in the other is a spoke reachable through the proxy that the topology says is
# unreachable.
#
# What is *not* shared (Lesson 51): Squid's deny list is this list plus `169.254.0.0/16` and
# `100.64.0.0/10`, which are link-local and CGNAT and are not RFC1918. Those two are the proxy's
# own and are authored in the proxy slice. The shared half is the concept both mean; the extras
# are one caller's.
RFC1918_CIDRS = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

# Where the tunnel is built, which is not the question VPN_HOMES below answers (6c step 4.1).
# Two intents, one list until this pass because they named the same slice (Lesson 51):
#
#   (a) whose exported Elastic IP the control-plane deny and the lake's perimeter pin to
#       - VPN_HOMES, read by identity/sso/ and data-governance/data/
#   (b) which slice owns the WireGuard anchors and needs the tunnel's address range
#
# Pass 4 is the sitting in which they must differ. (b) moves to the hub at 4.1, because the
# security group and the route are built before any host exists; (a) may not move until 4.12,
# because flipping it earlier makes identity/sso read an empty state and `DenyControlPlaneOffVpn`
# then denies every call from every network. Deriving (b) from VPN_HOMES makes a change for one
# intent silently for the other, and the symptom is a total lockout rather than a plan error.
#
# A single tuple and not a list on purpose: the estate terminates one tunnel. When a second
# business unit terminates its own (D35), this becomes a list and VPN_HOMES stays the separate
# question it now is.
VPN_HOST_SLICE = ("production", "networking")

# The accounts that play the VPN-home role (Stage 4 step 8.1) - a role an account plays, not a
# property. Stage 4's forward constraint from D35 says it in those words: the VPN home is a role,
# not "the Sandbox account", so what identity/sso/ pins the control plane to is a list from day
# one - one Elastic IP per home as D35 multiplies business units, and adding unit 2 is appending
# a row here rather than editing a policy document.
#
# Authored, never derived from VPC_CIDRS or PROFILES. Every account in PROFILES has a state
# bucket and most will have a VPC; almost none of them terminates a tunnel. Deriving this would
# silently pin the control plane to whatever slice happened to export a
# `wireguard_eip_public_ip`, and an account that stopped being a VPN home would keep its address
# in the allow-list until somebody noticed. The row is the decision.
#
# What consumes it: two emissions, both named `vpn_homes` - to identity/sso (below), which turns
# each row into a terraform_remote_state read of that slice, and to data-governance/data since
# Stage 5 pass 1, where the same addresses become a branch of the lake's perimeter deny. An entry
# must therefore be a slice that exports the EIP.
#
# Each row is (account, slice) since 6c step 0.5: the slice name was hard-coded in
# identity/sso/data.tf's key, and D38 moves the tunnel into `VPC-Networking`, whose Elastic IP,
# VPC id and gateway-endpoint id live in `production/networking/`, so the slice stopped being
# derivable from the account.
#
# The Sandbox row left at 6c step 6.5 (2026-09-07), after the readings the union it stood in was
# waiting for: both laptop proofs passed from the new tunnel, and CloudTrail read the two doors
# the hub's row covers - `sts` arriving from the proxy's Elastic IP, `s3control` arriving from
# the proxy host's private address through VPC-Networking's S3 gateway endpoint (verification 4:
# both branches of DenyControlPlaneOffVpn are load-bearing, by service family). The Elastic IP
# `52.89.212.1` transferred with the host, so no persona presents Sandbox's VPC or an old address
# any more. Removing the row also unblocked `removed {}` on `sandbox/foundation`'s Elastic IP.
VPN_HOMES = [("production", "networking")]

# The lake's consumers and its pickup producer (Stage 5 pass 1), authored like VPN_HOMES and for
# the same reason: which accounts consume the governed lake is a decision (INT-03's N+2;
# decision 5 granted to the two named accounts), not something derivable from PROFILES. Consumed
# by three emissions - `consumers`, `vpn_homes` and `producers` to data-governance/data, where
# each row becomes a terraform_remote_state read (the [P] gateway-endpoint ids, the WireGuard
# EIPs) or an aliased-provider identity read (the account ids the drop-box statements are built
# from, which aws/INDEX.md rule 1 keeps out of tracked files) - and by the `lake` map to each
# consumer's own data/ slice (pass 4). The `data_consumers` emission to identity/sso, pass 4c's
# workgroup and derived-bucket ARNs, left on 2026-08-26 with the derived zone itself (D19
# revised), so no emission reaches identity/sso from here any more, and Stage 9 step 1.4 no
# longer has to split this list before adding Production. Production joins at Stage 9; a vended
# Sandbox unit at Stage 14.
#
# One consumer since Stage 6b step 2.3: `development` becomes the headless `Staging`, and D20
# keeps a deployment target off the lake share entirely. Dropping the row stops emitting the
# aliased-provider identity read, stops emitting that account's `consumer_foundation` remote
# state (whose gateway-endpoint id is INT-05's `aws:SourceVpce` allow-list), and stops emitting
# the `lake` map to a consumer slice that step 2.4 destroys.
DATA_CONSUMERS = ["sandbox"]
DATA_PRODUCERS = ["production"]

# The other direction, added at pass 4: the account that owns the lake, read by the consumers. A
# one-element table, and still a table for the reason the three above are: the consumer slices
# resolve the lake's catalog id through an aliased provider and read its state for the shared
# database names, and both need a profile, which may be a literal in no .tf file (Lesson 14).
# D22 makes this a singleton forever, so the list is not expected to grow; what it buys is that
# the emissions below have the same shape as every other cross-account read in this tree. Two of
# them: the `lake` map goes to each consumer's data/ slice (pass 4) and to identity/sso (pass 4c,
# for the drop-box prefix and the lake data key the persona's write statements name).
DATA_LAKE = ["data-governance"]

# The supply chain's consumers (Stage 7 step 5.4, applied at Stage 6 pass 0) - D35's forward
# constraint written as a table rather than as three literals. production/registry/ enumerates
# them in four policies: the ECR registry policy, the two repository policies, the CodeArtifact
# domain policy and the slice's own KMS key policy. A vend adds one row here and nothing else
# changes (Lesson 14; Stage 7's option-preservation note). The row carries the profile because
# the slice resolves each consumer's account id through an aliased provider - aws/INDEX.md rule 1
# keeps ids out of tracked files, and a pasted id would be the copy Lesson 3 warns about.
#
# It is not DATA_CONSUMERS. The two lists answer different questions: who reads the governed
# lake, and who pulls images and packages. Stage 9 adds production to the first and must not add
# it to the second (the registry lives there). `staging` is here and not in DATA_CONSUMERS: a
# deployment target pulls images and packages like anything else, and stopped being a lake
# consumer at Stage 6b step 2.4.
REGISTRY_CONSUMERS = ["sandbox", "staging"]

# The unified domain and its member accounts (Stage 6, D26/D35). SMUS_MEMBERS is a decision and
# SMUS_ASSOCIATED is a measurement, so read this before editing either.
#
# SMUS_DOMAIN is the account that owns the domain: a singleton by D22/D26, kept as a list so
# the emissions below have the same shape as every other cross-account read in this tree.
# Consumed by each member's sagemaker/ slice, which resolves the domain id out of
# data-governance/governance/'s state.
#
# Merging the other two would make it impossible to tell "we have not associated this account
# yet" from "this account was never meant to be a member" (D28: Staging and Production never
# are).
#
#   SMUS_MEMBERS     the accounts that are meant to be associated - D26/D35's answer, and the
#                    map the project profiles' environment configurations are built from. It
#                    is also what the aliased providers in data-governance/governance/ resolve
#                    account ids through, so it must be populated from the first apply.
#   SMUS_ASSOCIATED  the accounts whose association has actually been accepted. The account
#                    association is console-only - there is no public associate-account API
#                    (Stage 6 step 1.3) - so a row is added after the invitation is accepted in
#                    the member account, and the second apply of that account's sagemaker/
#                    slice is what creates its blueprint configurations. Adding a row before
#                    the association exists produces an apply that fails inside
#                    PutEnvironmentBlueprintConfiguration - the honest failure; adding one
#                    after an association was revoked produces a slice that keeps re-creating
#                    a configuration nobody can use, which is not.
#
# The measurement gates both sides of the same ordering. A project profile's environment
# configurations name (blueprint, account, region), and the blueprint has to be configured in
# that account first, so the profiles wait until every member is associated, which is what
# `profiles_enabled` below computes rather than restates.
#
# The gate is monotone only on the first build. `profiles_enabled` feeds a `for_each` in
# data-governance/governance/profiles.tf, and the blueprint-id lookup in its data.tf, so it
# reverses: a member added to SMUS_MEMBERS while SMUS_ASSOCIATED lacks it takes the flag back to
# false, and the next apply of governance/ destroys the project profiles that already exist, or
# fails outright if projects hang off them.
#
# So, once a profile exists, the SMUS_ASSOCIATED row is written before the SMUS_MEMBERS row,
# never the other way round. The tell is a plan showing `awscc_datazone_project_profile`
# destroyed, which is why a by-hand change reads the add/change/destroy counts before applying
# (docs/plan/runbooks/terraform-changes.md, Recipe A step 5). The ordering itself is not this
# file's to carry: the stage that performs it is Stage 14 step 4, for a vended unit.

SMUS_DOMAIN = ["data-governance"]
# One member since Stage 6b step 1.2: `development` left because the account stops being
# Interactive and becomes the headless `Staging`. The row is what generates `blueprints_enabled`
# for its sagemaker/ slice, so removing it is not bookkeeping after the fact - it is the edit
# that destroys the eleven blueprint configurations, taken in the same commit as the
# SMUS_ASSOCIATED row below.
SMUS_MEMBERS = ["sandbox"]
# Measured 2026-08-21, not assumed: the association raised no invitation (organization-scoped
# share, Stage 1d's org-wide RAM enablement), so the console's "Associated" label is not the
# evidence. What is: `datazone list-environment-blueprint-configurations --domain-identifier
# dzd-...` run as each member's own profile succeeds and returns an empty list, a call that
# cannot succeed at all before the association. The apply order is what is staged, not this list
# (Stage 6 step 1.4 before 1.5).
#
# Rows leave in one edit (Stage 6b step 1.2): `profiles_enabled` is
# `set(SMUS_MEMBERS) <= set(SMUS_ASSOCIATED)`, so shrinking either list alone flips it false and
# the next governance/ apply destroys the `experimentation` project profile as well. The empty
# governance/ plan is the proof that it did not.
#
# This list means "should carry blueprint configurations", which is not "is associated", and for
# one pass the two differ: the console disassociation is Stage 6b step 1.4 and it comes after
# the configurations are destroyed - necessarily, since only the member can delete them and only
# while the association still exists.
SMUS_ASSOCIATED: list = ["sandbox"]

# ------------------------------------------------- the persona's project-storage vending policy
#
# One name, three slices, and a contract rather than a convention. A customer-managed policy is
# referenced from a permission set by name, and the object must exist under that exact name in
# every account the set is provisioned into - a missing one fails provisioning, per account, in
# an account nobody is watching (the failure decision 4 deferred the boundary over). So the name
# is generated here and consumed by three slices, never typed three times (Lesson 14): each
# member's foundation/ creates the object, identity/sso/ references it.
#
# `org` is the correct env token, and the exception is deliberate. Every other name in this
# design carries the token of the account it lives in, but this object is materialised in sandbox
# and development under one name, so an <env> token would make the two names differ and a
# permission set can reference only one. conventions.md gives `org` to platform resources of the
# identity plane, which is what this is: entitlement-plane content that happens to need a
# per-account body. The Environment tag still says sandbox or development, because the tag
# describes where the object lives and the name describes what references it.
PERSONA_VENDING_POLICY_NAME = "awsds-org-project-storage-vending"

# Where that object must exist. The list AWS actually constrains is "every account
# DataScientistAccess is provisioned into", which is authored in identity/sso/locals.tf's
# `assignments` map and cannot be read from here. Derived from SMUS_MEMBERS rather than authored
# a third time: only a SMUS member account can hold an S3 Access Grants instance to vend from,
# and the set's two assignment rows name exactly these accounts today. If the two ever diverge,
# this list follows the assignments, not the members - the symptom of getting it wrong is a
# provisioning error in the account that was left out, not a plan failure here.
#
# An account leaving opens that window. Stage 6b step 1.2 took `development` out of SMUS_MEMBERS
# while `DataScientistAccess` was still assigned to that account until step 2.1, so this was the
# literal ["sandbox", "development"] until 2.1 removed the assignment and 2.2 removed the object.
# The next account to leave re-opens the same window between its 1.2 and its 2.1.
PERSONA_VENDING_ACCOUNTS = list(SMUS_MEMBERS)

# Subnets anchor on zone ids, never on AZ names and never on list position (Stage 3 step 1.5,
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
NETWORK_SLICES = {
    "foundation",
    "egress",
    "vpn",
    "probes",
    "buildbox",
    # 6c step 0.3's slices, declared here with their ranks. `networking` and `workloads` are
    # VPC-bearing; `proxy` and `workloads-egress` ride inside one and read its state, exactly
    # as `egress` and `vpn` do.
    "networking",
    "workloads",
    "proxy",
    "workloads-egress",
}

# The subset that creates a VPC rather than living inside one, named the day Production got three
# (6c step 0.2). `foundation` was the whole answer while every account had one VPC; now
# `vpc_cidr` is emitted to whichever slice owns a VPC, and every other network slice reads its
# host VPC's [P] facts through terraform_remote_state instead.
VPC_SLICES = {"foundation", "networking", "workloads"}

# Stage 3's reachability probes: which accounts each side has to admit or reach. Every side's
# security group names the other side's VPC range, and the pairing is derived from `PEERINGS`
# rather than authored in any slice - an address literal in a .tf file is a copy of this table
# that nothing keeps in step (Lesson 14).
#
# The target admits both sources: Sandbox to Production is the peering the Deliverables measure,
# and Development to Production is INT-09, the integration this stage's Proves row claims. One
# target host exercises both, so the second source costs one instance rather than a second
# target.
#
# The hand-kept `PROBE_PEERS` table was deleted at 6c step 6.3, and it arrived as a timeout
# rather than as a diff: the Sandbox peering probe could not reach the proxy at all, because
# pass 3 added `sandbox/foundation <-> production/networking` to `PEERINGS` and nothing added
# `10.31.0.0/16` to the second table. One intent - which VPCs does this account reach - in two
# tables, and only one of them moved (Lesson 33). A hand-kept table keyed by slice would have
# the same defect one peering later; `peerings_of()` already answers exactly this question, and
# a probe whose egress is generated from the peering matrix cannot be blind to a peering the
# matrix has.


def probe_peer_cidrs(account: str) -> list:
    """Every VPC range this account's `foundation/` VPC is peered with, from PEERINGS.

    The peering probe's egress security group is scoped to these, and each is kept whole
    deliberately: the permitted address and the forbidden one are both inside one of them, so the
    group is constant across the pair and the route is the single variable the reading turns on.
    """
    return sorted({p["peer_cidr"] for p in peerings_of(account, "foundation")})


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
    # D36: production/pki/ holds the internal root CA's private key in its state file. If it
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

    The extras are emitted only where a consumer exists, per slice: an emitted value no
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
        # The guard is per (account, slice) since 6c step 0.2: Production carries three VPCs, so
        # "does this account have an allocation" stopped being the question. A network slice with
        # no row fails here rather than applying with a hole.
        if not any(a == account for a, _s in VPC_CIDRS):
            raise UnknownAccountFolder(
                f"{account}: network slice '{slice_name}' but no CIDR allocation anywhere - "
                "D22 accounts hold no VPC; a new account is added to VPC_CIDRS deliberately"
            )
        values["zone_ids"] = ZONE_IDS[account]
        if slice_name in VPC_SLICES:
            own = vpc_cidr_of(account, slice_name)
            if own is None:
                raise UnknownAccountFolder(
                    f"{account}/{slice_name}: a VPC-bearing slice with no row in VPC_CIDRS. "
                    "The address plan is authored before the folder exists (6c step 0.2), so "
                    "this is a missing row rather than a missing decision."
                )
            values["vpc_cidr"] = own
            values["name_suffix"] = vpc_name_suffix_of(account, slice_name)
            # A VPC slice needs the folder only if it has a sibling to read.
            # production/{foundation,networking,workloads} read each other's zone ids through
            # terraform_remote_state, and the state key is built from the account folder, which
            # no .tf file may re-derive from the env token (Lesson 14).
            #
            # Emitting it to a single-VPC account would declare an input nothing consumes, which
            # tflint rejects - measured, not predicted: the first version of this line put it in
            # both spokes and the hook said so.
            if len([a for a, _s in VPC_CIDRS if a == account]) > 1:
                values["account_folder"] = account
            # Both sides of every peering from one list (0.6 / 3.1). A slice gets the rows it is
            # an end of, with its role in each, so a requester and an accepter cannot disagree
            # about which peerings exist - which hand-writing the two halves in two files made
            # possible.
            values["peerings"] = peerings_of(account, slice_name)
            # The tunnel range, to the slice that terminates the tunnel (6c step 4.1). Two
            # resources in the hub need it and neither may carry it as a literal (Stage 3
            # decision 1 - address allocation lives in this file): the proxy's security group
            # admits `10.90.0.0/24` on TCP/3128, and the public route table sends it at the
            # WireGuard host's ENI. Keyed on VPN_HOST_SLICE and not on VPN_HOMES: see that
            # tuple's comment for why the two questions stopped sharing one list.
            if (account, slice_name) == VPN_HOST_SLICE:
                values["wireguard_peer_cidr"] = WIREGUARD_PEER_CIDR
                # And not the ULA. The hub's two consumers are a security group and a route
                # table, and both deal in IPv4 because every VPC in this estate is IPv4-only
                # (measured 2026-09-07). Emitting `fd90::/64` here would be an unused value in
                # a generated file, and the use somebody found for it would be an IPv6 path this
                # design does not have. The ULA reaches the one slice that needs it,
                # `production/vpn`, and stops there.
            # Stage 3 pass 2: the peers map - every VPC-bearing account that has a profile,
            # derived rather than authored a third time (Lesson 14). The slice's aliased
            # providers read a peer's [P] facts (VPC, subnets, route tables) live instead of
            # copying them here: an id in a tfvars would be a stale copy of another slice's
            # state. The self-row is emitted too and simply unused.
            #
            # Emitted to Production's `foundation` and `networking` alone. `peerings` supersedes
            # this map: it answers "which VPC-bearing accounts are there, and how do I reach one"
            # per row, with the role and the far end resolved, and the spokes moved onto it when
            # their peering files became generated (3.4). What is left are the two Production
            # slices whose aliased providers need a profile per peer account, and providers
            # cannot be iterated. The hub's consumer is the reversed zone authorizations: each
            # spoke owns a child zone and must authorize VPC-Networking on it, and the hub acts
            # as each spoke through an aliased provider, so both halves of a cross-account
            # handshake are one apply. When that constraint is gone, so is this map.
            if account == "production" and slice_name in ("foundation", "networking"):
                # The `name_suffix` field carries 0.6's smallest half, pulled forward by an
                # outage step 1.1 caused. A requester finds the accepter's VPC by the tag
                # `awsds-<env>-vpc`; 1.1 re-labelled Production's to `awsds-prod-shared-vpc`,
                # and both spokes stopped being able to apply - `data.aws_vpc.production`
                # returned "no matching EC2 VPC found". The VPC id never changed, so 1.1's own
                # gate ("any id in the replacement list stops the step") could not see it: what
                # moved was a name another account resolves by. The peering list can wait for
                # the matrix; the peer lookup cannot wait past the rename that breaks it.
                values["peers"] = {
                    acct: {
                        "profile": PROFILES[acct],
                        "env": ENV_TOKENS[acct],
                        "name_suffix": vpc_name_suffix_of(acct, "foundation"),
                    }
                    for acct in vpc_bearing_accounts()
                    if acct in PROFILES
                }
        else:
            # egress/ (pass 3) - and Stage 4's vpn/ when it decides - read foundation/'s
            # [P] facts through terraform_remote_state instead of carrying copies. The
            # state key is keyed by the account folder (backend_values above), which no
            # .tf file may re-derive from the env token: the reverse map would be a
            # second copy of ENV_TOKENS (Lesson 14). So the folder name rides along.
            values["account_folder"] = account
            # The private address space, to the two hub [D] slices that enforce it (6c 4.7/4.8).
            # Scoped to Production explicitly rather than to the slice name alone, because
            # `sandbox/vpn/` is a `vpn` slice too and declares no such variable - an emission it
            # cannot consume is a warning on every plan of a slice that is about to be destroyed.
            # When a second business unit terminates its own tunnel (D35), this becomes the set
            # VPN_HOST_SLICE becomes a list.
            if account == "production" and slice_name in ("vpn", "proxy"):
                values["rfc1918_cidrs"] = RFC1918_CIDRS
            if slice_name == "vpn":
                # Stage 4 step 4.2 - the WireGuard client range, which is not chosen in the
                # slice. Its single job is not colliding with a home or cafe LAN.
                values["peer_cidr"] = WIREGUARD_PEER_CIDR
                # And the ULA: the module takes both, and an IPv4-only tunnel is what let a
                # device's IPv6 leave outside it entirely.
                values["peer_cidr_v6"] = WIREGUARD_PEER_CIDR_V6
            # Nothing extra for `buildbox`, and the absence is a decision. It briefly took
            # WIREGUARD_PEER_CIDR, to admit the tunnel's clients on its security group, and the
            # requirement behind that was withdrawn by the user the same day, once a measurement
            # showed the rule did not gate the one path anybody uses: `ssm start-session` reaches
            # the agent's outbound channel and no security group sees it. The buildbox has no
            # ingress rule at all, so an emission here would feed a variable that feeds nothing.
            if slice_name == "probes":
                # Each side's security group names the other side's VPC range: Production
                # admits the source, Sandbox egresses to the target. Keeping the peer range
                # whole is deliberate - the permitted address and the forbidden one are both
                # inside it, so the security group is constant across the pair and the route
                # is the single variable the reading turns on.
                # The guard is the matrix itself, which is stricter than a membership test: an
                # account whose `foundation/` is an end of no peering has nothing for a peering
                # probe to measure, and an empty egress list would produce a probe reporting
                # silence about a question nobody asked.
                if not probe_peer_cidrs(account):
                    raise UnknownAccountFolder(
                        f"{account}: 'probes' needs at least one peering its foundation/ VPC is "
                        "an end of - add it to PEERINGS deliberately, not here"
                    )
                # A probe peer is a VPC, not an account, since 6c step 6.3. Generated from
                # `PEERINGS`, so a probe cannot be blind to a peering the matrix has: the
                # Sandbox probe reaches the hub (10.31) as well as SharedServices (10.30),
                # which is what makes step 6.3's proxy readings possible at all.
                values["peer_cidrs"] = probe_peer_cidrs(account)

    # The first non-network emission, and the repository's first cross-account remote-state read
    # (Stage 4 step 8.1); Stage 5's maps below follow the same shape. identity/sso/ pins the six
    # persona sets to the WireGuard Elastic IP, and the address may not be pasted: it is read
    # from each VPN home's state. That read crosses an account boundary, so, unlike every
    # same-account read in this tree, it needs a profile in the data source's config, and pass
    # 2's rule is that a profile literal never sits in a .tf file (Lesson 14; peers.tf's own
    # comment). So it arrives the same way `peers` does for foundation/: keyed by account folder,
    # carrying the profile and the env token the bucket name is built from. One SSO login covers
    # both profiles, because they share the `awsds` sso-session.
    # Stage 5's cross-account reads - the identity/sso shape, three maps (see DATA_CONSUMERS).
    if account == "data-governance" and slice_name == "data":
        values["consumers"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in DATA_CONSUMERS
        }
        values["vpn_homes"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct], "slice": sl}
            for acct, sl in VPN_HOMES
        }
        values["producers"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in DATA_PRODUCERS
        }

    # The consumer side of the lake (Stage 5 pass 4). Emitted for `data` in any account that
    # consumes the lake, never for data-governance itself, which owns it and whose own `data`
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
    # network slice takes: this slice reads its own foundation/ state for the VPC, the subnets
    # and the endpoint security group, and the state key is keyed by the account folder, which
    # no .tf file may re-derive from the env token (Lesson 14).
    if slice_name == "sagemaker":
        values["account_folder"] = account
        # Two maps at the same account, and they are not one map. `lake` is the governed lake's
        # state (the registered bucket ARNs the D13 boundary excludes, the drop-box prefix, the
        # lake data key); `domain` is the SMUS registry's. D22/D26 put both in Data Governance
        # today, so the two rows are identical, and merging them would be the coincidence
        # Lesson 10 warns about: they answer different questions, and a design that separated
        # them would have to unpick one emission from the other.
        values["lake"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in DATA_LAKE
        }
        values["domain"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in SMUS_DOMAIN
        }
        values["blueprints_enabled"] = account in SMUS_ASSOCIATED

    # Stage 6 pass 2 - the domain account's own slice. The members map is what the project
    # profiles' environment configurations are built from (one per member account); the flag is
    # a SMUS_ASSOCIATED reading over the same members, so the profiles cannot be written before
    # the blueprints they name are configured.
    if account == "data-governance" and slice_name == "governance":
        values["members"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in SMUS_MEMBERS
        }
        values["profiles_enabled"] = bool(SMUS_MEMBERS) and set(SMUS_MEMBERS) <= set(
            SMUS_ASSOCIATED
        )
        # The directory read (grants.tf): who may create a project from which profile is
        # granted to an sso-group-*, and IdC is delegated to Identity, so the slice needs one
        # read-only alias pointing there. The names are the decision and they live in the
        # slice's locals.tf; only the profile that can resolve them comes from here, the same
        # way every other cross-account read in this table does.
        values["identity_profile"] = PROFILES["identity"]

    # The persona's vending policy: the object half, in each account the set reaches (the name
    # block above carries the argument). foundation/ rather than sagemaker/ because a permission
    # set that cannot find this policy fails to provision, so it must outlive every slice that
    # can be torn down, and foundation/ is [P].
    if slice_name == "foundation" and account in PERSONA_VENDING_ACCOUNTS:
        values["persona_vending_policy_name"] = PERSONA_VENDING_POLICY_NAME

    if account == "identity" and slice_name == "sso":
        values["vpn_homes"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct], "slice": sl}
            for acct, sl in VPN_HOMES
        }
        # Stage 5 pass 4c put two cross-account reads here. The `data_consumers` map (each
        # consumer's workgroup + derived-bucket ARNs) left on 2026-08-26 with the derived zone
        # itself (D19 revised - the zone re-homed onto the SMUS project path, the persona's
        # Athena and derived statements removed). The lake map stays: the drop-box write and its
        # key are the ingestion path, untouched by the revision.
        values["lake"] = {
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct]} for acct in DATA_LAKE
        }
        # The persona's vending policy: the reference half. The set names the policy; the object
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
    # Emitted only when non-empty (6c step 0.4). The variable defaults to "" in every caller, so
    # a single-VPC account's file is byte-identical to its pre-6c one, which is the gate on the
    # vpc-v0.2.0 bump: the three foundation slices re-plan `No changes` on the version alone.
    if v.get("name_suffix"):
        out += f'name_suffix     = "{v["name_suffix"]}"\n'
    if "zone_ids" in v:
        zone_list = ", ".join(f'"{z}"' for z in v["zone_ids"])
        out += f"zone_ids        = [{zone_list}]\n"
    if "account_folder" in v:
        out += f'account_folder  = "{v["account_folder"]}"\n'
    if "peer_cidr" in v:
        out += f'peer_cidr       = "{v["peer_cidr"]}"\n'
    # Spelled in full and not `peer_cidr` (6c step 4.1). The vpn/ slice's `peer_cidr` is that
    # slice's one peer range and the module's own input name; in the hub the same value sits
    # beside `peerings[*].peer_cidr`, VPC ranges that are peers in the other sense. Two
    # different things called `peer_cidr` in one tfvars is the ambiguity worth a longer name.
    if "peer_cidr_v6" in v:
        out += f'peer_cidr_v6    = "{v["peer_cidr_v6"]}"\n'
    if "wireguard_peer_cidr" in v:
        out += f'wireguard_peer_cidr = "{v["wireguard_peer_cidr"]}"\n'
    if "rfc1918_cidrs" in v:
        cidr_list = ", ".join(f'"{c}"' for c in v["rfc1918_cidrs"])
        out += f"rfc1918_cidrs   = [{cidr_list}]\n"
    if "peer_cidrs" in v:
        cidr_list = ", ".join(f'"{c}"' for c in v["peer_cidrs"])
        out += f"peer_cidrs      = [{cidr_list}]\n"
    if "peerings" in v:
        rows = "".join(
            "  {\n"
            + "".join(
                f"    {k} = {json.dumps(pr[k])}\n"
                for k in (
                    "key",
                    "role",
                    "peer_account",
                    "peer_slice",
                    "peer_cidr",
                    "peer_profile",
                    "peer_env",
                    "peer_name_suffix",
                    "same_account",
                )
            )
            + "  },\n"
            for pr in v["peerings"]
        )
        out += f"peerings = [\n{rows}]\n"
    if "peers" in v:
        rows = "".join(
            f'  {acct} = {{ profile = "{p["profile"]}", env = "{p["env"]}", '
            f'name_suffix = "{p["name_suffix"]}" }}\n'
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
            f'  {acct} = {{ profile = "{p["profile"]}", env = "{p["env"]}", '
            f'slice = "{p["slice"]}" }}\n'
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
