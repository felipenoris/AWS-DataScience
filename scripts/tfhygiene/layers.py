"""Which slice belongs to which lifecycle layer - the table `make up` and `make down` read.

Stage 2 step 8.1 asks for exactly this and phrases the requirement as a refusal of the
obvious alternative: **a slice declares its layer in a table, not in a comment.** A comment is
read by a person; `make down` has to be read by a program, and D11's whole claim - "pay
nothing while idle" - is a claim about a command, not about an intention (Lesson 5).

THE THREE LAYERS (D11, docs/plan/conventions.md 5.1):

  [P] persistent  created once, never destroyed. Free or nearly free at rest.
  [D] dormant     kept, but powered off between sessions - stop/start, never destroy.
  [E] ephemeral   destroyed at the end of a session and rebuilt from code.

WHAT THIS TABLE WAS *FOR* WHEN EVERY ROW IN IT SAID [P] AND `make down` DID NOTHING. The
machinery was written BEFORE the first [E] slice existed rather than after it, which
is step 8.6's own reasoning applied to the whole target: a hook added later is a hook that was
missing from the first teardown that needed it. Stage 3's `egress/` is the first [E] slice and
Stage 4's WireGuard `vpn/` the first [D] one; both arrive to a `make down` that already refuses the four things it must
refuse. **Since Stage 3 the table carries six [E] rows and Stage 4 added the [D] one, so both
targets act for real** - `make down ENV=sandbox` destroys `egress/` and `probes/` and stops the
WireGuard host.

THE TABLE IS AUTHORED, THE TREE IS DISCOVERED, AND THE DISAGREEMENT IS AN ERROR - the same
two-list shape `attachments.json` uses on the policy side, for the same reason. A slice on disk
with no row here would be skipped by `make down` **silently**, which is the expensive direction:
an [E] slice nobody destroys is a bill. A row here with no slice on disk is a stale entry that
makes the table stop being evidence. `./scripts/slices.py check` fails on both, and it runs
inside `make check`.

WHAT IS NOT IN THIS FILE: which resources a slice contains, and what it costs to run. The
first is the slice's own code; the second is `usd_per_hour` below, and it is copied from
docs/PRICING.md 3 with the row named - prices are measured, never reasoned (Lesson 6).
"""

from __future__ import annotations

from dataclasses import dataclass

PERSISTENT = "P"
DORMANT = "D"
EPHEMERAL = "E"

LAYER_NAMES = {
    PERSISTENT: "persistent - created once, never destroyed",
    DORMANT: "dormant - kept, powered off between sessions",
    EPHEMERAL: "ephemeral - destroyed at the end of a session",
}


# THE RANK IS BY SLICE NAME, NOT BY ACCOUNT, because the dependency runs along the slice axis:
# every account's bootstrap precedes every account's foundation, which precedes its egress. Two
# accounts at the same rank are independent of each other and their order is a convenience
# (step 3.6 already said so for the four bootstrap applies).
#
# A SLICE NAME WITH NO ROW HERE CANNOT BE ADDED TO THE TABLE AT ALL - `slice()` below raises on
# it, at import, before any target runs. A new kind of slice declares its dependency order
# deliberately; defaulting it to the end is how a destroy runs in the wrong order once.
#
# The cross-account exception is Stage 3's pass 2 - the peerings and the zone associations,
# which need pass 1 done on BOTH sides. That is a second apply of the same slice, not a
# different rank, and Stage 3 owns it.
RANKS = {
    "bootstrap": 0,
    # THE ONE ROW WHOSE RANK IS NOT ITS DEPENDENCY, and it is said out loud here rather than
    # left to be re-derived: identity/sso/ READS slices that rank below it. Since Stage 4 step
    # 8.1 it reads each VPN home's foundation/ (rank 20) for the Elastic IP, and since Stage 5
    # pass 4c the three data/ states (rank 45) for the workgroup, derived-bucket and drop-box
    # ARNs. The rank is NOT moved: every slice on both ends is [P], so `up`/`down` refuse them
    # all and no ordering ever acts on the inversion; moving `sso` to 46 would change only the
    # `make slices` display and would falsely suggest a teardown ordering exists. The real
    # order is enforced by the apply failing BY NAME on an unapplied remote state. What the
    # rank does say is that the entitlement plane precedes the accounts it entitles. Revisit
    # the day either end stops being [P].
    "sso": 10,
    "org-policies": 11,
    "foundation": 20,
    # THE TWO RANKS WITH NO SLICE BEHIND THEM YET, and the comment they went four months
    # without (added 2026-08-21). A rank is legal on its own - `slices.py check` validates the
    # SLICES table against the tree and only asks that every ROW have a rank, never the
    # reverse - and both of these are deliberate, for the reason `vpn` states above: the
    # ORDER is the part that gets got wrong once, so it is declared before the slice arrives.
    #
    #   pki      production/pki/, Stage 7 pass 1. Its state key has existed since 2026-08-15
    #            (production/bootstrap/pki-key.tf, D36) and NEVER_DESTROY below already arms
    #            refusal 3 for it. It was scheduled ahead of Stage 6 until 2026-08-21, when
    #            D36 3 was amended: nothing serves a .internal name before Stage 7.
    #   registry production/registry/, written under Stage 7 step 5 and applied in two passes -
    #            5.a at STAGE 6's pass 0 (Stage 6 step 5.0 pushes into it), 5.b at Stage 7.
    #            The rank landed ahead of the slice because an unranked name raises at import,
    #            so a registry/ folder written without one fails `make check` before it can be
    #            applied at all. After foundation: the slice reads the VPC/subnet outputs.
    "pki": 30,
    "registry": 31,
    # BELOW egress ON PURPOSE (Stage 4 step 1.3): `up` ascends rank and `down` descends it,
    # so a rank under egress starts the tunnel BEFORE the [E] slices exist and stops it AFTER
    # they are gone. That is the order 8.3 makes load-bearing - from then on every API call
    # must exit through the VPN EIP, so the tunnel is the first thing up and the last down.
    # The row itself lands with the slice, in one commit (step 1.3): this check fails on a
    # declared slice that is not on disk, and it is right to - a row with nothing behind it
    # makes the table stop being evidence. The rank is here early because the ORDER is the
    # part that was got wrong once and is worth fixing before anything consumes it.
    "vpn": 40,
    # The governed lake (Stage 5). After foundation because its perimeter policy READS the
    # consumers' foundation/ states (the [P] gateway-endpoint ids, INT-05) - a cross-account
    # read, so the rank is documentation of dependency, not an ordering up/down ever acts on:
    # every slice at this rank is [P].
    "data": 45,
    # STAGE 6, AND THE TWO RANKS WHOSE ORDER IS ONLY THE ORDER OF THE *FIRST* APPLY.
    # Both are [P], so `up` and `down` refuse them and no target ever acts on the number -
    # what it records is the dependency an executor has to respect by hand. The real
    # sequence is FOUR applies over two slices, because the account association in the
    # middle of it has no public API (Stage 6 step 1.3):
    #
    #   1. */sagemaker/     the blueprint PREREQUISITES - provisioning and manage-access
    #                       roles, the D13 boundary, the KMS key, the VPC parameters
    #   2. governance/      the domain and its two IAM roles - execution and service, with
    #                       their two managed-policy attachments: five resources, measured
    #                       2026-08-21 (governance/iam.tf names the third and why it is absent)
    #   3. (console)        request + accept the account association, per member account,
    #                       then add the row to backend.SMUS_ASSOCIATED
    #   4. */sagemaker/     again - the blueprint CONFIGURATIONS, which need both a domain
    #                       and an accepted association
    #   5. governance/      again - the two project profiles, which name blueprints that
    #                       have to be configured in the target account first
    #
    # So sagemaker ranks BELOW governance on the strength of step 1, and steps 4 and 5 are
    # the inversion the two-pass split exists to make safe - the same shape Stage 3 pass 2
    # has for the peerings, and the cross-account exception note above covers it.
    "sagemaker": 46,
    "governance": 47,
    # STAGE 16'S SANDBOX LAKE (2026-08-26). AFTER `data` (45), and that is the only one of the
    # three ranks below it that is a real dependency: the bucket encrypts under
    # alias/awsds-<env>-data, which the `data` slice's consumer-data module creates. It sits
    # above sagemaker/governance for no dependency reason at all - nothing here reads the
    # domain - and the number simply had to go somewhere below egress.
    #
    # THE FIRST APPLY IS THREE ACTS OVER TWO SLICES, and the rank cannot say so, which is why
    # this comment does (the sagemaker/governance pair above has the same shape for the same
    # reason - both ends are [P], so `up`/`down` refuse them and no target ever acts on the
    # order):
    #
    #   1. data/   already applied - it owns the CMK this bucket names
    #   2. lake/   the bucket, the access role, the location, the per-group grants
    #   3. data/   AGAIN - one key-policy statement admitting the access role. It is second
    #              because KMS validates a key policy's principals: a statement naming a role
    #              that does not exist yet is rejected, so the role has to precede it
    "lake": 48,
    "egress": 50,
    # STAGE 6 STEP 5.0's BUILD HOST (2026-08-21). ABOVE `vpn` (40) and BELOW `probes` (60),
    # and only one of those two neighbours is a dependency:
    #
    #   vpn      IS one, and hard. This slice's single route points at the WireGuard host's
    #            ENI and the host must be RUNNING, or the route is a blackhole rather than an
    #            error. `up` ascends rank, so the [D] hook starts the tunnel first.
    #   egress   is NOT one, and the absence is the design rather than an accident: the build
    #            reaches the internet through the VPN host, so no NAT gateway is involved and
    #            `egress/` need never come up for a build session (0.160 USD/h not spent).
    #            The rank sits above it anyway - nothing is ordered wrongly by that, and it
    #            keeps the reading "everything ephemeral in this account is at or above 50".
    #   probes   is a CONFLICT, not a dependency, and it is the reason this row's slice
    #            refuses to coexist with it: sandbox/probes/'s perimeter probe measures the
    #            isolated tier's ABSENCE of a default route, and this slice's whole mechanism
    #            is adding one. ./scripts/buildbox.py enforces the exclusion; the rank only
    #            records that this one goes down first.
    "buildbox": 55,
    "probes": 60,
}


class UnknownSlice(Exception):
    """A slice name with no entry in RANKS - it has never declared a dependency order."""


@dataclass(frozen=True)
class Slice:
    """One row of the table: an applied unit, its layer, and where it sits in the order."""

    account: str  # the terraform-live/ folder, which is also backend.py's key
    name: str  # the slice folder inside it
    layer: str  # P | D | E
    why: str  # what the slice holds, in one line - so a reader need not open it
    usd_per_hour: float = 0.0  # 0.0 when nothing in the slice is metered by the hour

    @property
    def path(self) -> str:
        return f"terraform-live/{self.account}/{self.name}"

    @property
    def rank(self) -> int:
        """Read from RANKS, never stored - two copies of an order is Lesson 14 in a table."""
        try:
            return RANKS[self.name]
        except KeyError:
            raise UnknownSlice(self.name) from None


# ---------------------------------------------------------------------------- the table
#
# EVERY SLICE ON DISK TODAY. The [P] rows are free or nearly free at rest: five state
# buckets and their keys (KMS is priced per key-MONTH, docs/PRICING.md 2, so it is a floor
# line and not an hourly one), two Identity Center / Organizations slices whose objects cost
# nothing at all, and the foundation networks. The egress/ rows are the repository's first
# [E] ones (Stage 3 pass 3) and the first with `usd_per_hour` - from here `make up` and
# `make down` stop being no-ops and `make status` reports a real burn.
#
# usd_per_hour IS COPIED FROM docs/PRICING.md 3, MEASURED us-west-2 RATES (Lesson 6), and
# is the AT-REST-WHILE-UP figure - per-GB processing is traffic, not time, and stays in the
# stage's Cost section: interface endpoint 0.010/h each, NAT gateway 0.045/h + public IPv4
# 0.005/h. Per account: endpoints x 0.010 + 0.050 where a NAT exists (egress_mode A).
SLICES = [
    Slice("sandbox", "bootstrap", PERSISTENT, "state bucket + its KMS key (step 2)"),
    Slice("development", "bootstrap", PERSISTENT, "state bucket + its KMS key (step 3)"),
    Slice("data-governance", "bootstrap", PERSISTENT, "state bucket + its KMS key (step 3)"),
    Slice("production", "bootstrap", PERSISTENT, "state bucket + TWO keys - D36's is 2nd (3.4)"),
    Slice("identity", "bootstrap", PERSISTENT, "state bucket + its KMS key (step 3)"),
    Slice("identity", "sso", PERSISTENT, "7 permission sets, their policies, 10 assignments"),
    Slice("identity", "org-policies", PERSISTENT, "the 10 SCP/RCP/tag/declarative docs + 10 att."),
    # Stage 3 pass 1 (2026-08-16). Free at rest, [P]: VPC, subnets, IGW, route tables, SGs,
    # gateway endpoints + their policies, flow log - plus zones where the account owns one.
    # data-governance has NO row here by decision (D22: no VPC at all); staging joins at vend.
    Slice("sandbox", "foundation", PERSISTENT, "VPC 3x2, gateway endpoints, sandbox.internal"),
    Slice("development", "foundation", PERSISTENT, "VPC 3x2, gateway endpoints, no zone (4.2)"),
    Slice("production", "foundation", PERSISTENT, "VPC 3x2, gw endpoints, prod+pages.internal"),
    # Stage 3 pass 3 (2026-08-16). The endpoint counts are step 8.3's per-role lists:
    # core 8 + the account's extras; every row includes a mode-A NAT (0.050 = 0.045 + IPv4).
    Slice("sandbox", "egress", EPHEMERAL, "NAT + 11 interface endpoints (8.3)", 0.160),
    Slice(
        "development",
        "egress",
        EPHEMERAL,
        "NAT + 11 interface endpoints (8.3)",
        0.160,
    ),
    Slice("production", "egress", EPHEMERAL, "NAT + 10 interface endpoints (8.3)", 0.150),
    # Stage 3's Deliverables, as slices rather than as a script (2026-08-16). These are
    # INSTRUMENTS: created, read from the serial console, destroyed in the same sitting -
    # `make down` is the whole reason they are here and not in aws/probes/, whose declared
    # safety class is that nothing is created. Three t4g.nano at 0.0042/h (docs/PRICING.md 8);
    # no IAM principal is created by either row. THESE STAYED ON GRAVITON when the VPN host
    # moved to amd64 on 2026-08-20: they are their own slices with their own AMI data source,
    # nothing about them was the subject of that change, and a probe pays the ~20% Graviton
    # discount for measuring exactly what an x86 one would.
    # THEY ARE ORDERED: production/probes is the target, so it applies BEFORE the two source
    # rows, which find it by name in prod.internal. rank 60 puts all three after egress/,
    # whose S3 gateway policy the perimeter probe measures.
    Slice("production", "probes", EPHEMERAL, "peering target: 1 host, 2 ENIs, 2 A records", 0.0042),
    Slice("sandbox", "probes", EPHEMERAL, "perimeter probe (isolated) + peering probe", 0.0084),
    Slice(
        "development",
        "probes",
        EPHEMERAL,
        "INT-09 reachability + the DNS half Sandbox cannot answer",
        0.0042,
    ),
    # Stage 4 pass 1 (step 1.3, third edit) - THE REPOSITORY'S FIRST [D] ROW, and the rank
    # above it (40, between foundation and egress) landed early because the ORDER is what was
    # got wrong once. usd_per_hour is the t3.nano row of docs/PRICING.md 3, measured us-west-2
    # (Lesson 6) - t4g.nano's 0.0042 until 2026-08-20, when the host moved to amd64 and the
    # baseline it prices moved with it: the same shape on x86 is +23.8%, measured the same day.
    # AND IT IS THE WHILE-RUNNING figure: the EBS volume and the [P] Elastic IP go on billing
    # while the host is stopped, monthly rather than hourly, and they are floor lines in
    # docs/plan/cost-model.md rather than anything this column can carry.
    #
    # IT ALSO PRICES THE BASELINE AND NOT THE HOST. instance_type is a slice parameter (vpn.md
    # section S6), so a t3.medium session burns 0.0416/h - EIGHT times this figure - and
    # `make status` still quotes this one. Deliberate: ./aws/vpn.py VP-1 is where the reader is
    # told the two have parted company.
    Slice("sandbox", "vpn", DORMANT, "WireGuard host - the only human path in (Stage 4)", 0.0052),
    # Stage 6 step 5.0 (2026-08-21) - the amd64 build host, [E]. usd_per_hour is the
    # t3.xlarge row of docs/PRICING.md 8, MEASURED us-west-2 (Lesson 6) - and unlike the
    # WireGuard row above it, this figure DOES follow the tracked tfvars, because the default
    # and the assignment agree by design (the slice's own instance_type.auto.tfvars says why).
    # The 64 GiB gp3 is ~0.007/h on top and is not in this column: it is billed per GB-MONTH
    # and this slice is [E], so it exists only while the host does.
    Slice(
        "sandbox",
        "buildbox",
        EPHEMERAL,
        "amd64 build host for the dev-env image (St.6 5.0)",
        0.1664,
    ),
    # Stage 5 pass 1 (2026-08-18). Free or floor-priced at rest: one CMK (key-month), five
    # buckets, catalog objects, LF settings/tags/grants, two on-demand crawlers and the
    # compaction optimizer (config free; runs metered per DPU-hour, docs/PRICING.md 5).
    Slice(
        "data-governance",
        "data",
        PERSISTENT,
        "the lake: account data CMK, 5 buckets, catalog, LF (Stage 5)",
    ),
    # Stage 5 pass 4 (2026-08-19) - the consumer side, one module applied twice. [P] and free
    # or floor-priced at rest: one CMK per account (key-month, docs/PRICING.md 2), one bucket,
    # an Athena workgroup, the LF settings, two resource links and three grants. Athena bills
    # per TB SCANNED, which is a query and not an hour, so usd_per_hour stays 0.0 and the guard
    # is the workgroup's own bytes_scanned_cutoff_per_query.
    #
    # THE RANK IS `data` (45), SHARED WITH THE LAKE, and that is right rather than a collision:
    # every slice at that rank is [P], so no up/down order ever acts on it. What orders these
    # two in practice is the SHARE - a resource link resolves nothing before the lake grants -
    # and that is a dependency between accounts, which this table has never been the place for
    # (the cross-account exception note above says the same about Stage 3 pass 2).
    Slice(
        "sandbox",
        "data",
        PERSISTENT,
        "consumer side: account data CMK, derived zone, workgroup, links",
    ),
    Slice(
        "development",
        "data",
        PERSISTENT,
        "consumer side: same module as sandbox/data (Stage 5)",
    ),
    # Stage 6 pass 0 (2026-08-21) - Stage 7 step 5.a, applied one stage early because Stage 6
    # step 5.0 pushes the first dev-env image into it. [P] and floor-priced at rest: one CMK
    # (key-month, docs/PRICING.md 2), two ECR repositories and a CodeArtifact domain with two
    # repositories - all three billed for STORED BYTES and requests, never by the hour, so
    # usd_per_hour is 0.0 and the guard is the lifecycle policy on untagged images. The rank
    # (31) landed on 2026-08-21, ahead of the folder, because an unranked name raises at
    # import; this row is the half that had to wait for the slice to exist.
    Slice(
        "production",
        "registry",
        PERSISTENT,
        "ECR base+dev-env, CodeArtifact, the slice key (St.7 5.a)",
    ),
    # Stage 6 pass 1 - the blueprint prerequisites in each member account. [P] and FREE at
    # rest: two IAM roles, a permissions boundary policy and one CMK (the key-month floor
    # line). What the blueprint later provisions from them - the per-project SageMaker AI
    # domain and its apps - is NOT in this slice and never will be: DataZone owns those, and
    # the running apps are the [E] half, deleted by scripts/down-studio-apps.py rather than
    # by terraform destroy (conventions 6; Stage 6 step 8.3).
    Slice("sandbox", "sagemaker", PERSISTENT, "blueprint prereqs: 2 roles, D13 boundary, CMK"),
    Slice("development", "sagemaker", PERSISTENT, "same module as sandbox/sagemaker (Stage 6)"),
    # Stage 6 pass 2 - the registry, and it is a registry (D26): the DataZone V2 domain, its
    # two IAM roles and the two project profiles. [P] and metadata-priced (~USD 0.50/month,
    # docs/PRICING.md 5). NO COMPUTE LIVES HERE and none ever may - US-2 measures exactly
    # that, and Stage 6 step 0.4 reads the plan for it before the first apply.
    Slice(
        "data-governance", "governance", PERSISTENT, "the DataZone V2 domain + 2 project profiles"
    ),
    # Stage 16 - the sandbox lake. [P] and FREE at rest in the only sense this column measures:
    # nothing in it is metered by the HOUR. Storage is metered by the GB-month and grows without
    # bound by design (there is no expiry rule - that is the requirement), so this row's 0.0 is
    # true and incomplete at once, and the bill this slice does generate is docs/PRICING.md's
    # and the stage's Cost section rather than `make status`'s. Sandbox only today: Development
    # has no S3 Access Grants instance, so the same slice there would have nothing to register
    # a location against.
    Slice("sandbox", "lake", PERSISTENT, "permanent per-group artifacts + their AG grants"),
]


# ------------------------------------------------------------------------- the refusals
#
# Step 8.3 lists four, "each of which is a bug if it is missing". Three are enforced here as
# DATA and one in the caller as an argument check, and two of these three are deliberately
# REDUNDANT with the layer filter - a `bootstrap/` row is already [P], so `up` and `down` would
# skip it anyway. The redundancy is the point: the day somebody mislabels a row, the layer
# filter fails open and this list does not.
#
# A FIFTH JOINED THEM AT STAGE 4 (2026-08-16) and it was missing rather than deliberately
# absent: nothing refused a [D] slice, because none existed. Its note is below refusal 4.

# Refusal 3 - D36. production/pki/ holds the internal root CA's private key in its state.
# Rotating a root on a session boundary invalidates three client surfaces at 09:00, so the
# slice is unreachable from `down` WHATEVER LAYER ITS ROW EVER CLAIMS.
NEVER_DESTROY = {("production", "pki")}

# Refusal 4 - `bootstrap/` is unreachable from either target. It holds its own state (step
# 2.2), so a destroy would delete the bucket that records the destroy. This is the case the
# stage's Validation tests by reading the plan rather than by trusting the target list.
NEVER_ANY_TARGET_SLICE_NAMES = {"bootstrap"}

# REFUSAL 5 - THE ONE THE FIRST [D] ROW EXPOSED, and it is enforced in is_refused() below
# rather than as a set, because it is a property of the LAYER and not of a named slice.
#
# Stage 4's `sandbox/vpn` is the first row that is neither [P] nor [E], and until it existed
# the refusal list had no reason to say anything about [D]: `is_refused` returned None for
# any non-[P] slice, so a [D] row would have gone into the SAME list as the [E] ones - the one
# `down` runs `terraform destroy` over. D11 and conventions 5.1 say the opposite in as many
# words ("`make down` stops them, `make up` starts them"), and so do this repository's own two
# docstrings: slices.py's header reads "up: start the [D] slices, apply the [E] ones". The
# code did not implement its own contract, and the failure mode is the expensive direction -
# `make down ENV=sandbox` destroying the tunnel endpoint, its instance profile and its
# handshake log, which is exactly what the [P]/[D] split of Stage 4 step 2 exists to prevent.
#
# SO A [D] SLICE IS REFUSED BY BOTH TARGETS, and the power state is handled by the dormant
# hook instead. `up` is refused as well as `down`, which is the half worth arguing: applying a
# [D] slice on every `make up` would re-plan the SSM-resolved AMI, and a moved AL2023 release
# REPLACES the instance (Stage 4 step 1.1) - a silent rebuild of the VPN host on a routine
# start. Creating and changing a [D] slice is a deliberate `terraform apply`, read first.


def all_slices() -> list:
    return sorted(SLICES, key=lambda s: (s.rank, s.account, s.name))


def for_env(env: str) -> list:
    """Every declared slice of one account folder, in dependency order."""
    return [s for s in all_slices() if s.account == env]


def environments() -> list:
    return sorted({s.account for s in SLICES})


def is_refused(sl: Slice, action: str) -> str | None:
    """The reason `up`/`down` must not touch this slice, or None. A reason, not a boolean.

    A refusal reported as True/False produces a target that silently did nothing and a target
    that correctly did nothing, which read the same (Lesson 13). Every caller prints this.
    """
    if sl.name in NEVER_ANY_TARGET_SLICE_NAMES:
        return f"refusal 4: {sl.name}/ is unreachable from up and down - it holds its own state"
    if action == "down" and (sl.account, sl.name) in NEVER_DESTROY:
        return "refusal 3: D36 - production/pki/ is excluded from every down path"
    if sl.layer == PERSISTENT:
        return "refusal 1: [P] slices are never touched by up or down (D11)"
    if sl.layer == DORMANT:
        return (
            "refusal 5: [D] is stopped and started, never destroyed and never applied by "
            "this target (D11) - see the dormant hook, which acts on it"
        )
    return None


def actionable(env: str, action: str) -> tuple:
    """(slices to act on, [(slice, reason)] refused) for one env, in the action's order.

    `up` ascends the rank - a slice's dependencies apply first. `down` descends it, so an [E]
    slice is destroyed before anything it depends on could be.
    """
    take, skipped = [], []
    for sl in for_env(env):
        reason = is_refused(sl, action)
        if reason:
            skipped.append((sl, reason))
        else:
            take.append(sl)
    take.sort(key=lambda s: s.rank, reverse=(action == "down"))
    return take, skipped
