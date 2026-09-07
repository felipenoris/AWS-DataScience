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

import json

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
# TWO ACCOUNTS ARE ABSENT ON PURPOSE. Log Archive and Audit hold no CLI profile at all and no
# Terraform slice either. `staging` used to be the third, "unvended, so it has no profile to
# name" - the quota refused that vend, and Stage 6b made the account by RENAMING `Development`
# instead (2026-09-06).
#
# THE WINDOW CLOSED ON 2026-09-06. For the length of Stage 6b pass 4, `development` and `staging`
# were two keys naming one AWS account, because the slices moved one at a time and
# `development/bootstrap/` had to go LAST - it owned the bucket every other migration read FROM.
# Step 4.7 destroyed that bucket, so the row is gone from here, from ENV_TOKENS and from
# ENVIRONMENT_TAGS, and `terraform-live/development/` no longer exists.
PROFILES = {
    "sandbox": "awsds-infra-sandbox-1",
    "staging": "awsds-infra-staging",
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

# KEYED BY (ACCOUNT, SLICE), NOT BY ACCOUNT - and Stage 6c step 0.2 asked for this table to sit
# BESIDE a per-account `CIDRS` rather than to replace it. It replaces it, and the reason is that
# `CIDRS` turned out to have NO reader that actually asks an account-level question (measured
# 2026-09-06, every call site): `vpc_cidr` wants the slice's own VPC, the D22 guard wants "does
# this slice have an allocation", `peer_cidrs` wants a peer VPC's range, and the doc gate
# iterates the values. Each of those read per-ACCOUNT only because every account had exactly one
# VPC. The moment Production has three (D38), the per-account shape stops being expressible -
# `CIDRS["production"]` has no single answer - and two tables carrying the same numbers is
# Lesson 33 with nothing bought.
#
# STAGE 14 IS THE ONE HUMAN READER and it still works: "the LOWEST FREE /16 in 10.16.0.0/13" is a
# question about the VALUES, and they are all still here. So unit 2 is 10.16.0.0/16, not 10.21.
#
# ENTRIES ARE AUTHORED, NEVER COMPUTED - a CIDR computed at vend time is a [P] value that can
# move on a rebuild, in an account somebody is working in (Stage 3 step 1.3). The `sandbox` key
# is an ALLOCATION, NOT A FINAL NAME (D35, open question 10).
#
# 10.40.0.0/16 IS DELIBERATELY ABSENT AND STAYS THAT WAY. It was reserved for a `Staging` vend
# the account cap refused; Stage 6b renamed `Development` instead, so Staging is 10.50 and 10.40
# belongs to nobody. `./aws/networking.py`'s NT-3/NT-5/NT-6 are what measure that AWS agrees.
# 10.60.0.0/16 is D38's reservation for the day an account slot frees.
#
# THE TWO PRODUCTION ROWS WITH NO FOLDER YET are here under the same rule as `layers.py`'s ranks:
# declared before the slice arrives, because the address plan is the part that gets got wrong
# once. `networking` is D38's hub (the estate's only IGW); `workloads` is the production runtime.
VPC_CIDRS = {
    ("sandbox", "foundation"): "10.20.0.0/16",  # unit 1 - the literal Stage 4 and the views use
    ("production", "foundation"): "10.30.0.0/16",  # VPC-SharedServices after 6c step 1.1
    ("production", "networking"): "10.31.0.0/16",  # VPC-Networking, D38's hub (6c step 1.2)
    ("production", "workloads"): "10.32.0.0/16",  # VPC-Workloads (6c step 1.3)
    ("staging", "foundation"): "10.50.0.0/16",  # the renamed Development - a CIDR is immutable
}


# WHICH VPC INSIDE THE ACCOUNT, BY NAME - a second table keyed identically to VPC_CIDRS, and the
# reason it is separate rather than a field is that it answers a different question: that one is
# the ADDRESS plan, this one is the NAMING plan, and they change for different reasons. Sharing
# the key is what keeps them from drifting apart on the part that matters.
#
# ABSENT MEANS EMPTY, and empty reproduces the pre-6c names byte for byte - which is why
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


# THE PEERING MATRIX (Stage 6c step 3.1, 2026-09-06) - THE NINTH VOCABULARY, and the first one
# whose ABSENCES are a control rather than a backlog.
#
# Each row is (requester account, requester slice, accepter account, accepter slice). Both sides
# of every peering are generated from this one list, which is what 0.6 asked for: the requester
# lives in the spoke and the accepter in Production, and until now each side was hand-written in
# its own file with nothing tying them together (Lesson 14).
#
# WHAT IS NOT HERE IS THE CHEAPEST CONTROL IN THE DESIGN, and it is worth naming so it is not
# "fixed" by someone who reads a gap as an oversight:
#
#   Sandbox <-> Staging                 - Interactive and Workloads never talk. The user's brief.
#   Sandbox <-> VPC-Workloads           - same rule, other end.
#   VPC-SharedServices <-> Staging      - DEPLOYMENT IS AN API ACT. The runner assumes a role
#   VPC-SharedServices <-> VPC-Workloads  across the account boundary and calls SageMaker,
#                                         CloudFormation and S3; artifacts travel as ECR images,
#                                         CodeArtifact packages and S3 objects, each reached
#                                         through an endpoint in the TARGET's own VPC. Nothing in
#                                         a deployment target clones a repository - the image
#                                         carries the code (D28) - so a runtime `git clone` there
#                                         is a contract violation to catch, not a path to give.
#                                         Building them would grant standing L3 reach from the
#                                         host that executes repository-supplied build code into
#                                         both deployment targets: D14's blast radius, widened
#                                         (Lesson 2).
#
# THE TRIGGER FOR ADDING ONE, so it is recognised rather than rediscovered: a shared service
# consumed at RUNTIME rather than at deploy time. Candidates, none of which exists today - a
# package mirror on an instance (as opposed to ECR and CodeArtifact, which are endpoints), a
# metrics or log collector that is not CloudWatch, an internal secrets or configuration service,
# a certificate-status endpoint. THE INTERNAL CA IS NOT ONE: D36 issues no CRL and runs no OCSP
# responder, by decision. Prefer a regional service or an endpoint; the peering is the last
# resort, and it is generated from this same list.
#
# THE ROW THAT LEFT. `("staging", "foundation", "production", "foundation")` existed until this
# step - Stage 3 built it and Stage 6b preserved it through a for_each rename with five moved{}
# blocks. Preserving it was right: the alternative was destroying it mid-conversion with no
# replacement, and INT-09 rode on it until here. Staging now reaches only the hub, for the proxy.
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
# "AND NEVER SEEN INSIDE AWS ... EMITTED TO THE vpn/ SLICE AND TO NOTHING ELSE" IS WHAT THIS
# COMMENT SAID UNTIL 6c step 4.1, AND BOTH HALVES STOPPED BEING TRUE ON THE SAME DAY - Lesson
# 49 exactly: a comment about a knob nobody turns is a claim about the callers that existed
# when it was written. D38 puts the proxy and the tunnel endpoint in ONE VPC, and step 4.7
# stops masquerading packets bound for the proxy so that Squid's access log carries a
# per-device address. From that apply on, `10.90.0.0/24` IS seen inside AWS - by the proxy's
# security group, which must admit it, and by the hub's public route table, which must send it
# at the WireGuard host's ENI. So it is emitted to VPN_HOST_SLICE as well.
WIREGUARD_PEER_CIDR = "10.90.0.0/24"

# THE PRIVATE ADDRESS SPACE - a STANDARD constant, not one of this project's allocations, and
# the distinction is why it sits apart from VPC_CIDRS above (6c steps 4.7/4.8, 2026-09-06).
#
# WHY IT IS CENTRAL RATHER THAN WRITTEN TWICE. Pass 4 puts the same list in two places with
# OPPOSITE polarity: the WireGuard host FORWARDS tunnel packets only to these ranges (a private
# network client has no business reaching a public address directly - the proxy is the door),
# and Squid DENIES these ranges as destinations (without that, an explicit proxy is an L7 bridge
# between VPCs that peering deliberately keeps apart - D38's own hole). A range added to one and
# missed in the other is not a cosmetic drift: it is a spoke reachable through the proxy that
# the topology says is unreachable.
#
# WHAT IS *NOT* SHARED, and Lesson 51 is why it is spelled out here rather than assumed: Squid's
# deny list is this list PLUS `169.254.0.0/16` and `100.64.0.0/10`, which are link-local and
# CGNAT and are not RFC1918. Those two are the proxy's own and are authored in the proxy slice.
# The shared half is the concept both really mean; the extras are one caller's.
RFC1918_CIDRS = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

# WHERE THE TUNNEL IS BUILT - and this is NOT the question VPN_HOMES below answers, which is
# why it is a second name rather than a second consumer of the first (6c step 4.1, 2026-09-06).
#
# LESSON 51, ARRIVING ON SCHEDULE. Until this pass the two intents were one list because they
# named the same slice:
#
#   (a) whose exported Elastic IP the control-plane deny and the lake's perimeter pin to
#       - VPN_HOMES, read by identity/sso/ and data-governance/data/
#   (b) which slice OWNS the WireGuard anchors and needs the tunnel's address range
#
# Pass 4 is the sitting in which they must differ. (b) moves to the hub at 4.1, because the
# security group and the route are built before any host exists; (a) may not move until 4.12,
# because flipping it earlier makes identity/sso read an EMPTY state and `DenyControlPlaneOffVpn`
# then denies every call from every network. Deriving (b) from VPN_HOMES - the shape that was
# one edit away and looked tidier - is the failure Lesson 51 describes: a change made for one
# intent silently made for the other, and the symptom is a total lockout rather than a plan error.
#
# It is a single tuple and not a list on purpose: the estate terminates ONE tunnel. When a second
# business unit terminates its own (D35), this becomes a list and VPN_HOMES stays the separate
# question it now is.
VPN_HOST_SLICE = ("production", "networking")

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
# EACH ROW IS (ACCOUNT, SLICE) SINCE 6c step 0.5 (2026-09-06), and the second half is the whole
# point. Both consumers turn a row into a `terraform_remote_state` read of that account's
# **foundation/** slice - the slice name was HARD-CODED in identity/sso/data.tf's key. D38 moves
# the tunnel into `VPC-Networking`, whose Elastic IP, VPC id and gateway-endpoint id live in
# `production/networking/`, so the slice stops being derivable from the account.
#
# THE VALUE STILL POINTS AT SANDBOX, DELIBERATELY. 0.5 builds the seam; **step 4.9 flips the
# row** to ("production", "networking") once that slice exists and has applied. Flipping it now
# would make identity/sso read an EMPTY state, and `DenyControlPlaneOffVpn` would then deny every
# call from every network - the failure permission-sets.tf's precondition already has an error
# message for. So this commit changes the shape and not one generated value.
# TWO ROWS SINCE 6c step 4.12's FIRST HALF (2026-09-06), and the second row is the UNION the
# step demands rather than the cut-over it warns against: "a single cut-over apply is one typo
# away from locking out all six personas."
#
# WHY A UNION IS POSSIBLE AT ALL, which was misjudged once before being measured. The union
# looked blocked because Sandbox's `wireguard_eip_public_ip` is about to be removed - but that
# output is only ONE of the three things a row yields. The other two, `vpc_id` and
# `s3_gateway_endpoint_id`, are the slice's ordinary outputs and do not move with the address.
# And because the address itself TRANSFERRED, both rows resolve to the SAME `52.89.212.1`, which
# `sort()`/`distinct()` collapse. So the union changes nothing on the `aws:SourceIp` axis and is
# purely ADDITIVE on the other two: both VPCs and both gateway endpoints are trusted, so nothing
# that passed before stops passing.
#
# THE TRIM IS PASS 6's, after the readings, and it is what makes this a union rather than a
# permanent widening. Removing the Sandbox row is also what unblocks `removed {}` on
# `sandbox/foundation`'s Elastic IP - the two are one act, in that order.
VPN_HOMES = [("sandbox", "foundation"), ("production", "networking")]

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
# ONE CONSUMER SINCE STAGE 6b STEP 2.3 (2026-09-06): `development` becomes the headless
# `Staging`, and D20 keeps a deployment target off the lake share entirely. Dropping the row
# does three things at once, which is why it is one edit and not three - it stops emitting the
# aliased-provider identity read, stops emitting that account's `consumer_foundation` remote
# state (whose gateway-endpoint id is INT-05's `aws:SourceVpce` allow-list), and stops emitting
# the `lake` map to a consumer slice that step 2.4 destroys.
DATA_CONSUMERS = ["sandbox"]
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
# `development` became `staging` on 2026-09-06 (Stage 6b step 4.5) and the ROW SURVIVED, which is
# the half worth noticing: a deployment target pulls images and packages like anything else, so
# the account stays a registry consumer even though it stopped being a lake consumer at step 2.4.
# That is the split the paragraph above predicted would matter one day, arriving.
REGISTRY_CONSUMERS = ["sandbox", "staging"]

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
# ONE MEMBER SINCE STAGE 6b STEP 1.2 (2026-09-06). It was two; `development` left because the
# account stops being Interactive - it becomes the headless `Staging` - and the row is what
# generates `blueprints_enabled` for its sagemaker/ slice. Removing it is therefore not
# bookkeeping after the fact: it IS the edit that destroys the eleven blueprint configurations,
# and it is taken in the same commit as the SMUS_ASSOCIATED row below (see that comment).
SMUS_MEMBERS = ["sandbox"]
# MEASURED 2026-08-21, not assumed: the association raised no invitation (organization-scoped share,
# Stage 1d's org-wide RAM enablement), so the console's "Associated" label is not the evidence. What is:
# `datazone list-environment-blueprint-configurations --domain-identifier dzd-...` run as each member's
# OWN profile SUCCEEDS and returns an empty list - a call that cannot succeed at all before the
# association. Both rows were added in one edit because both accounts were associated in one act; the
# APPLY ORDER is what is staged, not this list (Stage 6 step 1.4 before 1.5).
#
# AND BOTH ROWS LEAVE IN ONE EDIT TOO, FOR A DIFFERENT REASON (Stage 6b step 1.2, 2026-09-06).
# `profiles_enabled` is `set(SMUS_MEMBERS) <= set(SMUS_ASSOCIATED)`, so shrinking either list
# alone flips it FALSE and the next governance/ apply destroys the `experimentation` project
# profile as well. The empty governance/ plan is the proof that it did not.
#
# THIS LIST NOW MEANS "SHOULD CARRY BLUEPRINT CONFIGURATIONS", WHICH IS NOT "IS ASSOCIATED", and
# for one pass the two differ: the console disassociation is Stage 6b step 1.4 and it comes AFTER
# the configurations are destroyed - necessarily, since only the member can delete them and only
# while the association still exists.
SMUS_ASSOCIATED: list = ["sandbox"]

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
#
# THAT SENTENCE WAS CASHED IN FOR ONE PASS AND THE DERIVATION IS BACK (Stage 6b, 2026-09-06).
# Step 1.2 took `development` out of SMUS_MEMBERS while `DataScientistAccess` was still assigned
# to that account until 2.1 - the two lists diverged, and the rule above says this one follows
# the ASSIGNMENTS, so it was the literal ["sandbox", "development"] for exactly that window.
# Step 2.1 removed the assignment and 2.2 removed the object, so the divergence is closed and
# the derivation is correct again. The literal is worth remembering rather than the fix: the
# next account to leave will re-open the same window between its 1.2 and its 2.1.
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
NETWORK_SLICES = {
    "foundation",
    "egress",
    "vpn",
    "probes",
    "buildbox",
    # 6c step 0.3's slices, declared here with their ranks (2026-09-06). `networking` and
    # `workloads` are VPC-BEARING; `proxy` and `workloads-egress` ride inside one and read its
    # state, exactly as `egress` and `vpn` do.
    "networking",
    "workloads",
    "proxy",
    "workloads-egress",
}

# THE SUBSET THAT CREATES A VPC RATHER THAN LIVING INSIDE ONE, and it needed a name the day
# Production got three (6c step 0.2). `foundation` was the whole answer while every account had
# one VPC; now `vpc_cidr` is emitted to whichever slice OWNS a VPC, and every other network slice
# reads its host VPC's [P] facts through terraform_remote_state instead.
VPC_SLICES = {"foundation", "networking", "workloads"}

# Stage 3's reachability probes: which accounts each side has to admit or reach. Every side's
# security group names the OTHER side's VPC range, and the pairing is authored here rather
# than in any slice, for the same reason CIDRS is - an address literal in a .tf file is a copy
# of this table that nothing keeps in step (Lesson 14).
#
# THE TARGET ADMITS BOTH SOURCES, and that is not symmetry for its own sake: Sandbox to
# Production is the peering the Deliverables measure, and Development to Production is INT-09,
# the integration this stage's Proves row claims. One target host exercises both, so the
# second source costs one instance rather than a second target.
# DELETED AT 6c STEP 6.3 (2026-09-06), AND ITS OWN COMMENT PREDICTED THE DAY. The table read:
#
#     PROBE_PEERS = {"sandbox": ["production"], "development": ["production"],
#                    "production": ["sandbox", "development"]}
#
# and the emission below said *"every peer named here has exactly one `foundation/` VPC ... which
# is the reading that will force PROBE_PEERS to name slices rather than accounts."* Step 6.3 is
# that reading, and it arrived as a TIMEOUT rather than as a diff: the Sandbox peering probe could
# not reach the proxy at all, because pass 3 added `sandbox/foundation <-> production/networking`
# to `PEERINGS` and nothing added `10.31.0.0/16` here. One intent - *which VPCs does this account
# reach* - in two tables, and only one of them moved (Lesson 33). The row was ALSO stale from 6b:
# `development` is a key no account has answered to since that rename.
#
# SO IT IS DERIVED FROM `PEERINGS` AND NOT REPLACED BY A BETTER LIST. A hand-kept table keyed by
# slice would have the same defect one peering later. `peerings_of()` already answers exactly this
# question, and a probe whose egress is generated from the peering matrix cannot be blind to a
# peering the matrix has.


def probe_peer_cidrs(account: str) -> list:
    """Every VPC range this account's `foundation/` VPC is peered with, from PEERINGS.

    The peering probe's egress security group is scoped to these, and each is kept WHOLE
    deliberately: the permitted address and the forbidden one are both inside one of them, so the
    group is constant across the pair and the ROUTE is the single variable the reading turns on.
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
        # THE GUARD IS PER (ACCOUNT, SLICE) SINCE 6c step 0.2, and the difference is not cosmetic:
        # Production carries three VPCs, so "does this ACCOUNT have an allocation" stopped being
        # the question. A network slice with no row fails here rather than applying with a hole.
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
            # A VPC SLICE NEEDS THE FOLDER ONLY IF IT HAS A SIBLING TO READ, and the condition
            # is the point rather than a nicety (2026-09-06). Until 6c a `foundation` had nothing
            # in its own account to read, so this was emitted to the non-foundation network
            # slices alone. Now production/{foundation,networking,workloads} read each other's
            # zone ids through terraform_remote_state, and the state KEY is built from the
            # account FOLDER - which no .tf file may re-derive from the env token (Lesson 14).
            #
            # EMITTING IT TO A SINGLE-VPC ACCOUNT WOULD DECLARE AN INPUT NOTHING CONSUMES, which
            # tflint rejects - measured, not predicted: the first version of this line put it in
            # both spokes and the hook said so.
            if len([a for a, _s in VPC_CIDRS if a == account]) > 1:
                values["account_folder"] = account
            # BOTH SIDES OF EVERY PEERING FROM ONE LIST (0.6 / 3.1). A slice gets the rows it is
            # an end of, with its role in each - so a requester and an accepter can never
            # disagree about which peerings exist, which is exactly what hand-writing the two
            # halves in two files made possible.
            values["peerings"] = peerings_of(account, slice_name)
            # THE TUNNEL RANGE, TO THE SLICE THAT TERMINATES THE TUNNEL (6c step 4.1). Two
            # resources in the hub need it and neither may carry it as a literal (Stage 3
            # decision 1 - address allocation lives in this file): the proxy's security group
            # admits `10.90.0.0/24` on TCP/3128, and the public route table sends it at the
            # WireGuard host's ENI. Keyed on VPN_HOST_SLICE and not on VPN_HOMES: see that
            # tuple's comment for why the two questions had to stop sharing one list.
            if (account, slice_name) == VPN_HOST_SLICE:
                values["wireguard_peer_cidr"] = WIREGUARD_PEER_CIDR
            # Stage 3 pass 2: the peers map - every VPC-bearing account that has a profile,
            # DERIVED rather than authored a third time (Lesson 14). The slice's aliased
            # providers read a peer's [P] facts (VPC, subnets, route tables) live instead of
            # copying them here: an id in a tfvars would be a stale copy of another slice's
            # state. The self-row is emitted too and simply unused.
            #
            # STILL KEYED BY ACCOUNT, AND THAT IS A SEAM 6c step 0.6 CLOSES. Today every peering
            # in the estate joins two accounts that have one `foundation/` VPC each, so an
            # account key names a VPC unambiguously and `production/foundation/peers.tf` reads
            # `var.peers["sandbox"]` and `["staging"]` by literal. The moment Production holds
            # three, the key stops naming a VPC - which is why 0.6 moves the peering LIST here
            # and generates both sides from it. Until then this derivation is deliberately the
            # old one, so 0.2 changes the table without changing a single generated file.
            # EMITTED TO `foundation` AND `networking`, AND THIS INPUT'S SCOPE MOVED TWICE IN
            # ONE DAY - worth saying rather than hiding. At 1.2 it was narrowed to `foundation`,
            # because the hub had no peers.tf and a declared input nothing consumes is what
            # tflint rejects. At 2.5 the hub acquired a real consumer: the REVERSED zone
            # authorizations. Each spoke owns a child zone and must authorize VPC-Networking on
            # it, and the cheapest correct shape is the one peers.tf already uses - the hub acts
            # AS each spoke through an aliased provider, so both halves of a cross-account
            # handshake are one apply. That needs a profile per account, which is this map.
            #
            # 3.1 REPLACES THE SHAPE, not the fact: the peering MATRIX supersedes "every
            # VPC-bearing account" as the thing this is derived from. The row survives that.
            # NARROWED TO PRODUCTION'S TWO ON 2026-09-06, and this is `peers` being SUPERSEDED
            # rather than trimmed. It answered "which VPC-bearing accounts are there, and how do
            # I reach one" - a question `peerings` now answers precisely, per row, with the role
            # and the far end resolved. The spokes moved onto `peerings` when their peering files
            # became generated (3.4), so the only consumers left are the two Production slices
            # whose ALIASED PROVIDERS need a profile per peer account, and providers cannot be
            # iterated. When that constraint is gone, so is this map.
            if account == "production" and slice_name in ("foundation", "networking"):
                # THE `name_suffix` FIELD ARRIVED ON 2026-09-06 AND IT IS 0.6's SMALLEST HALF,
                # PULLED FORWARD BY AN OUTAGE STEP 1.1 CAUSED. A requester finds the accepter's
                # VPC by the tag `awsds-<env>-vpc`; 1.1 re-labelled Production's to
                # `awsds-prod-shared-vpc`, and BOTH spokes stopped being able to apply -
                # `data.aws_vpc.production` returned "no matching EC2 VPC found". The VPC id
                # never changed, so 1.1's own gate ("any id in the replacement list stops the
                # step") could not see it: what moved was a NAME another account resolves by.
                #
                # This is why 0.6 sits in pass 0 rather than in pass 3, and deferring it to 3.1
                # was the wrong call - the peering LIST can wait for the matrix, but the peer
                # LOOKUP cannot wait past the rename that breaks it.
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
            # state KEY is keyed by the ACCOUNT FOLDER (backend_values above), which no
            # .tf file may re-derive from the env token: the reverse map would be a
            # second copy of ENV_TOKENS (Lesson 14). So the folder name rides along.
            values["account_folder"] = account
            # THE PRIVATE ADDRESS SPACE, TO THE TWO HUB [D] SLICES THAT ENFORCE IT (6c 4.7/4.8).
            # Scoped to Production explicitly rather than to the slice NAME alone, because
            # `sandbox/vpn/` is a `vpn` slice too and declares no such variable - an emission it
            # cannot consume is a warning on every plan of a slice that is about to be destroyed.
            # When a second business unit terminates its own tunnel (D35), this becomes the set
            # VPN_HOST_SLICE becomes a list.
            if account == "production" and slice_name in ("vpn", "proxy"):
                values["rfc1918_cidrs"] = RFC1918_CIDRS
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
                # THE GUARD IS NOW THE MATRIX ITSELF, which is stricter than the membership
                # test it replaces: an account whose `foundation/` is an end of no peering has
                # nothing for a peering probe to measure, and an empty egress list would produce
                # a probe reporting silence about a question nobody asked.
                if not probe_peer_cidrs(account):
                    raise UnknownAccountFolder(
                        f"{account}: 'probes' needs at least one peering its foundation/ VPC is "
                        "an end of - add it to PEERINGS deliberately, not here"
                    )
                # A PROBE PEER IS A VPC, NOT AN ACCOUNT, since 6c step 6.3 - which is the
                # promise the deleted PROBE_PEERS table made to itself and never kept. Generated
                # from `PEERINGS`, so a probe cannot be blind to a peering the matrix has: the
                # Sandbox probe now reaches the hub (10.31) as well as SharedServices (10.30),
                # which is what makes step 6.3's proxy readings possible at all.
                values["peer_cidrs"] = probe_peer_cidrs(account)

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
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct], "slice": sl}
            for acct, sl in VPN_HOMES
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
            acct: {"profile": PROFILES[acct], "env": ENV_TOKENS[acct], "slice": sl}
            for acct, sl in VPN_HOMES
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
    # EMITTED ONLY WHEN NON-EMPTY (6c step 0.4). The variable defaults to "" in every caller, so
    # a single-VPC account's file is byte-identical to its pre-6c one - which is the whole gate on
    # the vpc-v0.2.0 bump: the three foundation slices re-plan `No changes` on the version alone.
    if v.get("name_suffix"):
        out += f'name_suffix     = "{v["name_suffix"]}"\n'
    if "zone_ids" in v:
        zone_list = ", ".join(f'"{z}"' for z in v["zone_ids"])
        out += f"zone_ids        = [{zone_list}]\n"
    if "account_folder" in v:
        out += f'account_folder  = "{v["account_folder"]}"\n'
    if "peer_cidr" in v:
        out += f'peer_cidr       = "{v["peer_cidr"]}"\n'
    # SPELLED IN FULL AND NOT `peer_cidr` (6c step 4.1). The vpn/ slice's `peer_cidr` is that
    # slice's ONE peer range and the module's own input name; in the hub the same value sits
    # beside `peerings[*].peer_cidr`, four VPC ranges that are peers in the OTHER sense. Two
    # different things called `peer_cidr` in one tfvars is the ambiguity worth a longer name.
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
