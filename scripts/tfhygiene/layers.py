"""Which slice belongs to which lifecycle layer - the table `make up` and `make down` read.

Stage 2 step 8.1 asks for exactly this: **a slice declares its layer in a table, not in a
comment.** A comment is read by a person; `make down` has to be read by a program, and D11's
claim - "pay nothing while idle" - is a claim about a command, not about an intention
(Lesson 5).

The layers (D11, docs/plan/conventions.md 5.1):

  [P] persistent  created once, never destroyed. Free or nearly free at rest.
  [D] dormant     kept, but powered off between sessions - stop/start, never destroy.
  [E] ephemeral   destroyed at the end of a session and rebuilt from code.

The table is authored, the tree is discovered, and a disagreement between them is an error -
the same two-list shape `attachments.json` uses on the policy side. A slice on disk with no row
here would be skipped by `make down` **silently**, which is the expensive direction: an [E]
slice nobody destroys is a bill. A row here with no slice on disk is a stale entry that makes
the table stop being evidence. `./scripts/slices.py check` fails on both, and it runs inside
`make check`.

What is not in this file: which resources a slice contains, and what it costs to run. The
first is the slice's own code; the second is `usd_per_hour` below, copied from
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


# The rank is by slice name, not by account, because the dependency runs along the slice axis:
# every account's bootstrap precedes every account's foundation, which precedes its egress. Two
# accounts at the same rank are independent of each other and their order is a convenience
# (step 3.6 already said so for the four bootstrap applies).
#
# A slice name with no row here cannot be added to the table at all: `slice()` below raises on
# it, at import, before any target runs. A new kind of slice declares its dependency order
# deliberately; defaulting it to the end is how a destroy runs in the wrong order once.
#
# The cross-account exception is Stage 3's pass 2, the peerings and the zone associations,
# which need pass 1 done on both sides. That is a second apply of the same slice, not a
# different rank, and Stage 3 owns it.
RANKS = {
    "bootstrap": 0,
    # The one row whose rank is not its dependency: identity/sso/ reads slices that rank below
    # it. Since Stage 4 step 8.1 it reads each VPN home's foundation/ (rank 20) for the Elastic
    # IP, and since Stage 5 pass 4c the lake's data/ state (rank 45) for the drop-box ARNs (the
    # two consumer data/ reads left 2026-08-26 with the derived zone, D19 revised). The rank is
    # not moved: every slice on both ends is [P], so `up`/`down` refuse them all and no ordering
    # ever acts on the inversion; moving `sso` to 46 would change only the `make slices` display
    # and would falsely suggest a teardown ordering exists. The real order is enforced by the
    # apply failing by name on an unapplied remote state. What the rank does say is that the
    # entitlement plane precedes the accounts it entitles. Revisit the day either end stops
    # being [P].
    "sso": 10,
    "org-policies": 11,
    "foundation": 20,
    # Stage 6c's new ranks, declared before any folder exists (step 0.3), under the same
    # discipline as `vpn` and `pki`: the order is the part that gets got wrong once, so it is
    # written down before anything consumes it.
    #
    #   networking  production/networking/, D38's hub - the estate's only internet gateway, the
    #               proxy's VPC and the WireGuard endpoint's after Stage 6c step 4. It ranks 21
    #               rather than 20 because `production/foundation/` (VPC-SharedServices) is the
    #               peering accepter for every spoke and must exist first.
    #   workloads   production/workloads/, the production runtime's VPC. 23, after the hub it
    #               peers to.
    #
    # Both are [P] and neither rank is ever acted on by up/down: what the numbers record is the
    # dependency an executor respects by hand, exactly as `data` at 45 does.
    "networking": 21,
    "workloads": 23,
    # Two ranks with no slice behind them yet. A rank is legal on its own - `slices.py check`
    # validates the SLICES table against the tree and only asks that every row have a rank,
    # never the reverse - and both are deliberate, for the reason the `vpn` row states: the
    # order is the part that gets got wrong once, so it is declared before the slice arrives.
    #
    #   pki      production/pki/, Stage 7 pass 1. Its state key has existed since 2026-08-15
    #            (production/bootstrap/pki-key.tf, D36) and NEVER_DESTROY below already arms
    #            refusal 3 for it. D36 3 was amended on 2026-08-21: nothing serves a .internal
    #            name before Stage 7.
    #   registry production/registry/, written under Stage 7 step 5 and applied in two passes -
    #            5.a at Stage 6's pass 0 (Stage 6 step 5.0 pushes into it), 5.b at Stage 7.
    #            The rank landed ahead of the slice because an unranked name raises at import,
    #            so a registry/ folder written without one fails `make check` before it can be
    #            applied at all. After foundation: the slice reads the VPC/subnet outputs.
    "pki": 30,
    "registry": 31,
    # Below egress on purpose (Stage 4 step 1.3): `up` ascends rank and `down` descends it, so
    # a rank under egress starts the tunnel before the [E] slices exist and stops it after they
    # are gone. Step 8.3 makes that order load-bearing: from then on every API call must exit
    # through the VPN EIP, so the tunnel is the first thing up and the last down. The row itself
    # lands with the slice, in one commit (step 1.3), because this check fails on a declared
    # slice that is not on disk: a row with nothing behind it makes the table stop being
    # evidence.
    "vpn": 40,
    # The governed lake (Stage 5). After foundation because its perimeter policy reads the
    # consumers' foundation/ states (the [P] gateway-endpoint ids, INT-05) - a cross-account
    # read, so the rank is documentation of dependency, not an ordering up/down ever acts on:
    # every slice at this rank is [P].
    "data": 45,
    # Stage 6, and two ranks whose order is only the order of the *first* apply. Both are [P],
    # so `up` and `down` refuse them and no target ever acts on the number; what it records is
    # the dependency an executor has to respect by hand. The real sequence is four applies over
    # two slices, because the account association in the middle of it has no public API
    # (Stage 6 step 1.3):
    #
    #   1. */sagemaker/     the blueprint prerequisites - provisioning and manage-access
    #                       roles, the D13 boundary, the KMS key, the VPC parameters
    #   2. governance/      the domain and its two IAM roles - execution and service, with
    #                       their two managed-policy attachments: five resources, measured
    #                       2026-08-21 (governance/iam.tf names the third and why it is absent)
    #   3. (console)        request + accept the account association, per member account,
    #                       then add the row to backend.SMUS_ASSOCIATED
    #   4. */sagemaker/     again - the blueprint configurations, which need both a domain
    #                       and an accepted association
    #   5. governance/      again - the two project profiles, which name blueprints that
    #                       have to be configured in the target account first
    #
    # So sagemaker ranks below governance on the strength of step 1, and steps 4 and 5 are the
    # inversion the two-pass split exists to make safe - the same shape Stage 3 pass 2 has for
    # the peerings, covered by the cross-account exception note above.
    "sagemaker": 46,
    "governance": 47,
    # Stage 16's sandbox lake. After `data` (45), the only real dependency of the three ranks
    # below it: the bucket encrypts under alias/awsds-<env>-data, which the `data` slice's
    # consumer-data module creates. It sits above sagemaker/governance for no dependency reason
    # at all - nothing here reads the domain - and the number simply had to go somewhere below
    # egress.
    #
    # The first apply is three acts over two slices, which the rank cannot say (the
    # sagemaker/governance pair above has the same shape for the same reason: both ends are [P],
    # so `up`/`down` refuse them and no target ever acts on the order):
    #
    #   1. data/   already applied - it owns the CMK this bucket names
    #   2. lake/   the bucket, the access role, the location, the per-group grants
    #   3. data/   again - one key-policy statement admitting the access role. It is second
    #              because KMS validates a key policy's principals: a statement naming a role
    #              that does not exist yet is rejected, so the role has to precede it
    "lake": 48,
    # The proxy is [D] and its rank decides the session (Stage 6c step 0.3). `up` ascends and
    # `down` descends, so 41 puts it up before any egress/ (50, 51) and down after them, which
    # keeps a spoke's package path alive for the entire life of an [E] session. Under D38 there
    # is no NAT gateway anywhere, so a spoke with its endpoints up and no proxy has no route to
    # the internet at all.
    "proxy": 41,
    "egress": 50,
    # VPC-Workloads' own [E] endpoint slice (Stage 6c step 1.3a). 51 rather than 50 only so the
    # two Production egress slices have a defined order between them; both sit above `proxy`.
    "workloads-egress": 51,
    # Stage 6 step 5.0's build host. Above `vpn` (40) and below `probes` (60):
    #
    #   vpn      a dependency, and a hard one. This slice's single route points at the
    #            WireGuard host's ENI and the host must be running, or the route is a
    #            blackhole rather than an error. `up` ascends rank, so the [D] hook starts the
    #            tunnel first.
    #   egress   a hard prerequisite since 6c step 5.8. The build host moved to
    #            `production/buildbox/`, its default route is gone, and its shell is an
    #            interface endpoint - `ssm`/`ssmmessages`/`ec2messages`, put in
    #            VPC-SharedServices by step 5.5 one step ahead of it. Without `egress/` there
    #            is no way into the host at all, so the ordering is load-bearing and 0.130
    #            USD/h is a cost of a build session rather than a cost avoided.
    #   proxy    is in a different account: the internet arrives as an explicit proxy over the
    #            SharedServices <-> Networking peering. A rank cannot express a cross-account
    #            dependency, which is why ./scripts/buildbox.py checks it - a rank is not a
    #            control (Lesson 5).
    #   probes   no longer conflicts. The exclusion existed because `sandbox/probes/`'s
    #            perimeter probe measures the Sandbox isolated tier's absence of a default
    #            route while this slice's mechanism was adding one there; this slice creates no
    #            route anywhere now and is not in that account.
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
# Every slice on disk today. The [P] rows are free or nearly free at rest: five state
# buckets and their keys (KMS is priced per key-month, docs/PRICING.md 2, so it is a floor
# line and not an hourly one), two Identity Center / Organizations slices whose objects cost
# nothing at all, and the foundation networks. The [E] rows carry `usd_per_hour`, which is
# what `make status` reports.
#
# usd_per_hour is copied from docs/PRICING.md 3, measured us-west-2 rates (Lesson 6), and
# is the at-rest-while-up figure - per-GB processing is traffic, not time, and stays in the
# stage's Cost section: interface endpoint 0.010/h each, NAT gateway 0.045/h + public IPv4
# 0.005/h. Per account: endpoints x 0.010 + 0.050 where a NAT exists (egress_mode A).
SLICES = [
    Slice("sandbox", "bootstrap", PERSISTENT, "state bucket + its KMS key (step 2)"),
    # Stage 6b step 4.2: the account was renamed, not vended, so this row replaced a
    # `development` one. This slice is the state home the account's other slices migrated into
    # (Recipe E step 2 - the destination bucket must exist before any -migrate-state names it),
    # and `development/bootstrap/` owned the bucket every one of those migrations read from.
    # Step 4.7 destroyed it; awsds-staging-tfstate is now the only state bucket in that account.
    Slice("staging", "bootstrap", PERSISTENT, "state bucket + its KMS key (6b 4.2)"),
    Slice("data-governance", "bootstrap", PERSISTENT, "state bucket + its KMS key (step 3)"),
    Slice("production", "bootstrap", PERSISTENT, "state bucket + TWO keys - D36's is 2nd (3.4)"),
    Slice("identity", "bootstrap", PERSISTENT, "state bucket + its KMS key (step 3)"),
    Slice("identity", "sso", PERSISTENT, "7 permission sets, their policies, 10 assignments"),
    Slice("identity", "org-policies", PERSISTENT, "the 10 SCP/RCP/tag/declarative docs + 10 att."),
    # Stage 3 pass 1. Free at rest, [P]: VPC, subnets, IGW, route tables, SGs, gateway
    # endpoints + their policies, flow log - plus zones where the account owns one.
    # data-governance has no row here by decision (D22: no VPC at all).
    Slice("sandbox", "foundation", PERSISTENT, "VPC 3x2, gw endpoints, sandbox.awsds.internal"),
    Slice("staging", "foundation", PERSISTENT, "VPC 3x2, gateway endpoints, no zone (4.2)"),
    Slice("production", "foundation", PERSISTENT, "VPC 3x2, gw endpoints, the apex + Pages zones"),
    # Stage 6c step 1.2 - D38's hub. The only VPC in the estate whose public tier routes to an
    # internet gateway; every other one is private by that route's absence. Free at rest like
    # every other foundation-shaped slice: the metered things (the proxy, the VPN host) are
    # [D]/[E] slices of their own that live inside it.
    Slice(
        "production", "networking", PERSISTENT, "VPC-Networking 3x2: the estate's only IGW route"
    ),
    # Stage 6c step 1.3 - the production runtime's VPC, private by the absence of the IGW route
    # rather than by lacking a gateway. Its interface endpoints are the [E] slice
    # production/workloads-egress/ (rank 51), never here: a VPC and its endpoints have different
    # lifecycles, and D11 is that split.
    Slice("production", "workloads", PERSISTENT, "VPC-Workloads 3x2: private, no IGW route"),
    # Stage 3 pass 3. The endpoint counts are step 8.3's per-role lists: core 8 + the account's
    # extras. The NAT left at 6c step 5.1 and these three figures moved with it: each was
    # NAT 0.045 + its Elastic IP 0.005 + the endpoints, and each is now the endpoints alone,
    # counted from the slice's own plan rather than from a list somebody might have edited
    # (`terraform plan | grep -c aws_vpc_endpoint.interface`), at the measured 0.010/h per
    # endpoint of docs/PRICING.md 8.
    #
    # Sandbox's idle floor went **up**, 0.160 -> 0.180, because 5.2 has to enumerate what the NAT
    # used to cover silently, and that is the only axis on which it rises. Per gigabyte a NAT is
    # 0.045 against an interface endpoint's 0.010 (both measured, docs/PRICING.md 8), so design B
    # costs +0.020/h fixed here and saves 0.035 per GB: break-even ~0.57 GB/h, which one container
    # pull passes in minutes. Estate-wide the fixed rate falls as well, 0.470 -> 0.390/h. This
    # column is hourly only, so it cannot show the axis that decides the comparison.
    #
    # None of the three includes 5.3's optional groups: `bedrock` adds 0.040 and `emr` 0.070 only
    # for an apply that names them, and a static rate that assumed them would over-report every
    # session that does not. `make status` quotes this column; the flag's cost is in `make help`.
    Slice("sandbox", "egress", EPHEMERAL, "18 interface endpoints (5.2) - no NAT", 0.180),
    Slice(
        "staging",
        "egress",
        EPHEMERAL,
        "11 interface endpoints (8.3) - no NAT",
        0.110,
    ),
    Slice("production", "egress", EPHEMERAL, "13 interface endpoints (5.5) - no NAT", 0.130),
    # Stage 6c step 1.3a - VPC-Workloads' endpoint slice, written empty and egress_mode "B" from
    # birth: zero NAT (D38) and no endpoint until Stage 9/10 names one, so usd_per_hour is 0.0
    # and true rather than 0.0 and pending. It exists now because an [E] slice that arrives
    # after the teardown target was last read is how a bill starts.
    Slice(
        "production",
        "workloads-egress",
        EPHEMERAL,
        "VPC-Workloads endpoints - empty until St.9/10",
        0.0,
    ),
    # Stage 3's Deliverables, as slices rather than as a script. These are instruments: created,
    # read from the serial console, destroyed in the same sitting - `make down` is why they are
    # here and not in aws/probes/, whose declared safety class is that nothing is created. Three
    # t4g.nano at 0.0042/h (docs/PRICING.md 8); no IAM principal is created by either row. They
    # are on Graviton, with their own AMI data source, and a probe pays the ~20% Graviton
    # discount for measuring exactly what an x86 one would.
    # They are ordered: production/probes is the target, so it applies before the two source
    # rows, which find it by name in the awsds.internal apex. rank 60 puts all three after
    # egress/, whose S3 gateway policy the perimeter probe measures.
    Slice("production", "probes", EPHEMERAL, "peering target: 1 host, 2 ENIs, 2 A records", 0.0042),
    Slice("sandbox", "probes", EPHEMERAL, "perimeter probe (isolated) + peering probe", 0.0084),
    Slice(
        "staging",
        "probes",
        EPHEMERAL,
        "INT-09 reachability + the DNS half Sandbox cannot answer",
        0.0042,
    ),
    # Stage 4 pass 1 (step 1.3), the repository's first [D] row. usd_per_hour is the t3.nano row
    # of docs/PRICING.md 3, measured us-west-2 (Lesson 6): t4g.nano's 0.0042 until 2026-08-20,
    # when the host moved to amd64 and the baseline it prices moved with it, the same shape on
    # x86 being +23.8%, measured the same day. It is the while-running figure: the EBS volume and
    # the [P] Elastic IP go on billing while the host is stopped, monthly rather than hourly, and
    # they are floor lines in docs/plan/cost-model.md rather than anything this column can carry.
    #
    # It prices the baseline and not the host. instance_type is a slice parameter (vpn.md
    # section S6), so a t3.medium session burns 0.0416/h, eight times this figure, and
    # `make status` still quotes this one. ./aws/vpn.py VP-1 is where the reader is told the two
    # have parted company.
    #
    # 6c step 4.7 moved the same host one account across; the Sandbox row (Stage 4's first [D]
    # slice) stood beside this one until 6c step 6.5 retired it with an empty state
    # (2026-09-08). Same rank, same DORMANT layer, same measured t3.nano rate: what moved is the
    # account and the job. It is no longer a NAT instance for a private tier (wireguard-v0.5.0
    # dropped vpc_nat_cidrs) and it is not an internet door - it forwards to the private address
    # space and rejects the rest, because under D38 the internet is the proxy's, one rank below.
    Slice(
        "production",
        "vpn",
        DORMANT,
        "WireGuard host in the hub - the only human path in (D38)",
        0.0052,
    ),
    # 6c step 4.8 - the estate's single internet exit, and the reason there is no NAT gateway
    # anywhere: an explicit Squid proxy on a host of its own, priced from the same
    # docs/PRICING.md row (Lesson 6). Two hosts and not one because the WireGuard host receives
    # untrusted UDP from the internet and this one parses untrusted internet responses;
    # separating them keeps a compromise of either off the other, for the price of one more host.
    #
    # It ranks below vpn (41 against 40) and that order is load-bearing: `make down` walks the
    # table in reverse, so the proxy goes first and the tunnel last - the tunnel is the way back
    # in, and a session that killed its own path out would have killed its path in one step
    # earlier. `up` runs it the right way round for the same reason.
    #
    # 0.0104 is the t3.micro row of docs/PRICING.md 8, measured 2026-09-06 (Lesson 6). The size
    # is decided by the build and not the steady state: `dnf install squid jq
    # amazon-cloudwatch-agent` was OOM-killed on a nano (415 MiB usable), with the kernel naming
    # it. It fit on the first host and not the second, which makes the nano marginal rather than
    # small, and the estate's single internet exit is the wrong place for a coin-flip.
    Slice(
        "production",
        "proxy",
        DORMANT,
        "Squid explicit proxy - the estate's only internet exit",
        0.0104,
    ),
    # Stage 6 step 5.0 - the amd64 build host, [E]. usd_per_hour is the t3.xlarge row of
    # docs/PRICING.md 8, measured us-west-2 (Lesson 6), and unlike the WireGuard row above it
    # this figure does follow the tracked tfvars, because the default and the assignment agree
    # by design (the slice's own instance_type.auto.tfvars says why). The 64 GiB gp3 is
    # ~0.007/h on top and is not in this column: it is billed per GB-month and this slice is
    # [E], so it exists only while the host does.
    #
    # 6c step 5.8 moved it to Production, account and tier both, at the same rate and in the
    # same [E] layer. The host has two prerequisites it cannot express, `production/egress/` in
    # its own account (the SSM endpoints that are its only door) and `production/proxy/` in the
    # hub (the only way to the internet), so a build session costs this row plus 0.130 plus
    # 0.0104.
    Slice(
        "production",
        "buildbox",
        EPHEMERAL,
        "amd64 build host for the dev-env image (St.6 5.0)",
        0.1664,
    ),
    # Stage 5 pass 1. Free or floor-priced at rest: one CMK (key-month), five buckets, catalog
    # objects, LF settings/tags/grants, two on-demand crawlers and the compaction optimizer
    # (config free; runs metered per DPU-hour, docs/PRICING.md 5).
    Slice(
        "data-governance",
        "data",
        PERSISTENT,
        "the lake: account data CMK, 5 buckets, catalog, LF (Stage 5)",
    ),
    # Stage 5 pass 4 - the consumer side, one module applied twice. [P] and free or floor-priced
    # at rest: one CMK per account (key-month, docs/PRICING.md 2), one bucket, an Athena
    # workgroup, the LF settings, two resource links and three grants. Athena bills per TB
    # scanned, which is a query and not an hour, so usd_per_hour stays 0.0 and the guard is the
    # workgroup's own bytes_scanned_cutoff_per_query.
    #
    # The rank is `data` (45), shared with the lake, which is not a collision: every slice at
    # that rank is [P], so no up/down order ever acts on it. What orders these two in practice
    # is the share - a resource link resolves nothing before the lake grants - and that is a
    # dependency between accounts, which this table has never been the place for (the
    # cross-account exception note above says the same about Stage 3 pass 2).
    Slice(
        "sandbox",
        "data",
        PERSISTENT,
        "consumer side: account data CMK, links, DataLakeSettings (derived zone removed 2026-08-26)",
    ),
    # Stage 6 pass 0 - Stage 7 step 5.a, applied one stage early because Stage 6 step 5.0
    # pushes the first dev-env image into it. [P] and floor-priced at rest: one CMK (key-month,
    # docs/PRICING.md 2), two ECR repositories and a CodeArtifact domain with two repositories -
    # all three billed for stored bytes and requests, never by the hour, so usd_per_hour is 0.0
    # and the guard is the lifecycle policy on untagged images.
    Slice(
        "production",
        "registry",
        PERSISTENT,
        "ECR base+dev-env, CodeArtifact, the slice key (St.7 5.a)",
    ),
    # Stage 6 pass 1 - the blueprint prerequisites in each member account. [P] and free at
    # rest: two IAM roles, a permissions boundary policy and one CMK (the key-month floor
    # line). What the blueprint later provisions from them - the per-project SageMaker AI
    # domain and its apps - is not in this slice and never will be: DataZone owns those, and
    # the running apps are the [E] half, deleted by scripts/down-studio-apps.py rather than
    # by terraform destroy (conventions 6; Stage 6 step 8.3).
    Slice("sandbox", "sagemaker", PERSISTENT, "blueprint prereqs: 2 roles, D13 boundary, CMK"),
    # Stage 6 pass 2 - the registry, and it is a registry (D26): the DataZone V2 domain, its
    # two IAM roles and the two project profiles. [P] and metadata-priced (~USD 0.50/month,
    # docs/PRICING.md 5). No compute lives here and none may: US-2 measures that, and Stage 6
    # step 0.4 reads the plan for it before the first apply.
    Slice(
        "data-governance", "governance", PERSISTENT, "the DataZone V2 domain + 2 project profiles"
    ),
    # Stage 16 - the sandbox lake. [P] and free at rest in the only sense this column measures:
    # nothing in it is metered by the hour. Storage is metered by the GB-month and grows without
    # bound by design (there is no expiry rule - that is the requirement), so this row's 0.0 is
    # true and incomplete at once, and the bill this slice does generate is docs/PRICING.md's
    # and the stage's Cost section rather than `make status`'s. Sandbox only today: an S3 Access
    # Grants instance needs a SMUS member account to be born in, and Sandbox is the only one since
    # Stage 6b step 1.2, so the same slice elsewhere would have nothing to register a location
    # against.
    Slice("sandbox", "lake", PERSISTENT, "permanent per-group artifacts + their AG grants"),
]


# ------------------------------------------------------------------------- the refusals
#
# Step 8.3 lists four, "each of which is a bug if it is missing". Three are enforced here as
# data and one in the caller as an argument check, and two of these three are deliberately
# redundant with the layer filter - a `bootstrap/` row is already [P], so `up` and `down` would
# skip it anyway. The redundancy is deliberate: the day somebody mislabels a row, the layer
# filter fails open and this list does not.
#
# Refusal 5 joined them at Stage 4, when the first [D] slice arrived: until then nothing
# refused a [D] slice, because none existed. Its note is below refusal 4.

# Refusal 3 - D36. production/pki/ holds the internal root CA's private key in its state.
# Rotating a root on a session boundary invalidates three client surfaces at 09:00, so the
# slice is unreachable from `down` whatever layer its row claims.
NEVER_DESTROY = {("production", "pki")}

# Refusal 4 - `bootstrap/` is unreachable from either target. It holds its own state (step
# 2.2), so a destroy would delete the bucket that records the destroy. This is the case the
# stage's Validation tests by reading the plan rather than by trusting the target list.
NEVER_ANY_TARGET_SLICE_NAMES = {"bootstrap"}

# Refusal 5 is enforced in is_refused() below rather than as a set, because it is a property of
# the layer and not of a named slice.
#
# A [D] slice is refused by both targets, and the power state is handled by the dormant hook
# instead. Without the refusal a [D] row falls into the same list as the [E] ones, the one
# `down` runs `terraform destroy` over, and `make down ENV=sandbox` destroys the tunnel
# endpoint, its instance profile and its handshake log - what the [P]/[D] split of Stage 4
# step 2 exists to prevent. D11 and conventions 5.1 say so in as many words ("`make down` stops
# them, `make up` starts them"), and so does slices.py's header: "up: start the [D] slices,
# apply the [E] ones".
#
# `up` is refused as well as `down`: applying a [D] slice on every `make up` would re-plan the
# SSM-resolved AMI, and a moved AL2023 release replaces the instance (Stage 4 step 1.1), a
# silent rebuild of the VPN host on a routine start. Creating and changing a [D] slice is a
# deliberate `terraform apply`, read first.


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
