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
from pathlib import Path

from . import backend

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
    # A row whose rank is not its dependency (`warehouse` is another): identity/sso/ reads a slice
    # that ranks below it, the lake's data/ state (rank 45), for the drop-box ARNs. The rank is
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
    # are gone. The monitored profile makes that order load-bearing: an operator on it sends every
    # AWS call through the tunnel and the proxy, so the tunnel is the first thing up and the last
    # down. No permission set needs the tunnel (D39); the route is the constraint. The row itself
    # lands with the slice, in one commit (step 1.3), because this check fails on a declared
    # slice that is not on disk: a row with nothing behind it makes the table stop being
    # evidence.
    "vpn": 40,
    # The governed lake (Stage 5a). After foundation because its perimeter policy reads the
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
    # Stage 6d step 2.1 - the registered house image. [P], so `up`/`down` refuse it and no target
    # ever acts on the number; what the rank records is the dependency an executor respects by
    # hand, and it is a cross-account one: the image version names a container in the registry
    # account, so production/registry/ is applied first. Nothing in this account precedes it, which
    # is why the number is merely the free slot below egress.
    "dev-env": 49,
    # Stage 6e step 3: the Bedrock grant for SMUS project roles. Above `sagemaker` (46), which
    # creates the blueprint the roles come from, and there is nothing else it depends on. The
    # number is above the two egress slices only because 47, 48 and 49 are taken: a [P] rank
    # records apply order for a person, and `up`/`down` skip [P] rows entirely, so nothing here
    # is interleaved with an [E] session. Its real prerequisite is one no rank can express - a
    # PROJECT must exist in the portal, because the role this slice attaches to is named after
    # it (runbooks/claude-code-sagemaker.md section P).
    "bedrock": 52,
    # Stage 17 decision 13: the two roles of the console's model access, beside `bedrock` and above
    # `sagemaker` (46), whose boundary they carry. [P], so up/down skip it. Its real prerequisite
    # is in another account: data-governance/governance/'s governance project, without which the
    # console's Manage stays greyed and the roles are never used.
    "model-access": 52,
    # Stage 6i decision 6: the workflows grant for SMUS project roles, the same shape as `bedrock`
    # and above `sagemaker` (46) for the same reason. [P], so up/down skip it; 56 is the first free
    # slot, and nothing interleaves with it.
    "workflows": 56,
    # Stage 5b step 1.7 - the Redshift Serverless warehouse, split across two ranks because the two
    # halves have different lifecycles and the order between them is a real dependency:
    #
    #   warehouse          [P] the namespace, its admin secret, its three audit log groups, the
    #                      namespace role, the workgroup's security group and the alarms. Above
    #                      `data` (45), whose CMK encrypts the namespace, and above `foundation`
    #                      (20), whose private subnets the compute lands in. Below `observability`
    #                      (70) and applied after it, the inversion `sso` has: the alarms' topic
    #                      is read from that slice's state, and the plan fails on the read until
    #                      it exists. Nothing in up/down ever acts on the number: every [P] row is
    #                      skipped by both.
    #   warehouse-compute  [E] the workgroup and its usage limit, nothing else. Above `warehouse`
    #                      because a workgroup needs its namespace, and `up` ascends rank while
    #                      `down` descends it - so the compute is created after the namespace
    #                      exists and destroyed before anything under it, the same reasoning that
    #                      put `vpn` below `egress`.
    #
    # The split is not a preference. Redshift Serverless has `create-workgroup` and
    # `delete-workgroup` and nothing in between - no pause, no stop, no zero-capacity setting - so
    # "powered off" means "does not exist", which is the definition of [E]. The namespace stays [P]
    # because it holds the schemas, the database users, the roles and the GRANTs, which Terraform
    # never wrote and no plan could re-create (5.1 rule 2).
    "warehouse": 53,
    "warehouse-compute": 54,
    # The proxy is [D] and its rank decides the session (Stage 6c step 0.3). `up` ascends and
    # `down` descends, so 41 puts it up before any egress/ (50, 51) and down after them, which
    # keeps a spoke's package path alive for the entire life of an [E] session. Under D38 there
    # is no NAT gateway anywhere, so a spoke with its endpoints up and no proxy has no route to
    # the internet at all.
    "proxy": 41,
    # Stage 7 step 1.6 - GitLab, [D]. Below `egress` (50) for the reason `vpn` and `proxy` are:
    # `up` ascends, so the host is started before the [E] slices exist, and `down` descends, so it
    # is stopped after they are gone. A started GitLab needs nothing from `egress/` to serve: its
    # configuration, certificates and secrets are on its data volume from the first boot, S3 is
    # the gateway endpoint, and the proxy is in another account. Only the FIRST boot needs the
    # endpoints (the bootstrap reads Secrets Manager and registers with SSM), and that apply is by
    # hand, after `egress/` (step 1.7). The host's Name tag is `awsds-prod-gitlab`, not the slice
    # name - DORMANT_HOST_NAMES below carries the exception.
    "tooling": 42,
    "egress": 50,
    # VPC-Workloads' own [E] endpoint slice (Stage 6c step 1.3a). 51 rather than 50 only so the
    # two Production egress slices have a defined order between them; both sit above `proxy`.
    "workloads-egress": 51,
    # Stage 7 step 6.1 - the build runner, [E], the buildbox's successor (the buildbox, rank 55,
    # retired at 6.5). Above `egress` (50): it needs the SSM endpoints for its only door and reads
    # `egress/`'s `no_proxy` output at apply time, which a destroyed slice fails by name.
    "runners": 57,
    # Stage 8 step 2.4 - an application slice, one folder further down (conventions 6:
    # terraform-live/<env>/app/<app>/), [E] in every account. Above `egress` (50), so `down` destroys
    # the application before the endpoints its jobs log through; Stage 10's `orchestration` ranks
    # above it, so `down` removes a workflow before the application the workflow starts.
    "app/app-etl": 58,
    # Stage 10 step 1.4 - the orchestration/ slices, [E] in Staging and Production: the workflows and
    # the chain layer that starts them. Above `app/app-etl` (58), so `down` removes a schedule and the
    # workflows it starts before the application slice's Glue job they run; `up` refuses it (refusal 7).
    "orchestration": 59,
    "probes": 60,
    # Stage 12 step 1 - the dashboards and the alarms no other slice owns, one [P] slice per account
    # with something to watch. It reads the [P] states of the slices it watches and names the [D]
    # hosts' alarms by name, never by state (Lesson 4), so it ranks after every one of them; up/down
    # skip it like every [P] row.
    "observability": 70,
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
    # A host the slice creates only when an apply asks for it, as (resource address, USD/h) pairs:
    # usd_per_hour is the slice without them, and `make status` adds a pair's rate for each instance
    # of that address the state holds.
    optional_hosts: tuple[tuple[str, float], ...] = ()

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
# nothing at all, and the foundation networks. The [D] and [E] rows carry `usd_per_hour`, and
# `make status` meters both - the two [D] hosts bill while every [E] slice is down.
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
    # None of the three includes 5.3's optional groups: `bedrock-base` and `bedrock-agent` add
    # 0.020 each, `emr` 0.070, `mlflow` and `redshift` 0.010 each, only for an apply that names
    # them, and a static rate that assumed them would over-report every session that does not.
    # `make status` quotes this column; the flag's cost is in `make help`.
    Slice("sandbox", "egress", EPHEMERAL, "18 interface endpoints (5.2) - no NAT", 0.180),
    # Stage 9 step 4.3a re-cut it to VPC-Workloads' set (3.3a), the endpoints a job and a worker call.
    Slice(
        "staging",
        "egress",
        EPHEMERAL,
        "7 interface endpoints (St.9 4.3a, decision 12) + DNS Firewall - no NAT",
        0.070,
    ),
    # 12 since Stage 7 (2026-10-12): 6c 5.5's 13 plus `secretsmanager` (step 1.7), which the GitLab
    # host's bootstrap reads its leaf keys and gitlab-secrets.json through and the runner its
    # registration token, minus the SageMaker pair nothing in this VPC calls (decision 9).
    Slice(
        "production",
        "egress",
        EPHEMERAL,
        "12 interface endpoints (5.5, 7 1.7, 7 dec 9) - no NAT",
        0.120,
    ),
    # Stage 6c step 1.3a - VPC-Workloads' endpoint slice, zero NAT (D38). Stage 9 step 3.3a names
    # its seven endpoints: sts, logs, kms, glue and lakeformation of the core (decision 12),
    # sagemaker.api and secretsmanager. The DNS Firewall bills per query and per domain list, never by
    # the hour, so it adds nothing to this column.
    Slice(
        "production",
        "workloads-egress",
        EPHEMERAL,
        "7 interface endpoints (St.9 3.3a, decision 12) + DNS Firewall - no NAT",
        0.070,
    ),
    # Stage 8 steps 3.2 and 3.6 - the application's Glue job, applied by the pipeline with the release it
    # promotes (refusal 7) and destroyed by Staging's `make down`. A job bills per run, nothing at rest.
    Slice("staging", "app/app-etl", EPHEMERAL, "app-etl's Glue job (St.8 3.2), pipeline-applied"),
    Slice(
        "production", "app/app-etl", EPHEMERAL, "app-etl's Glue job (St.8 3.6), pipeline-applied"
    ),
    # Stage 10 step 1.4 - the MWAA Serverless workflows with their roles and log groups, and the chain
    # layer above them, applied by the pipeline. Nothing here meters by the hour: a run bills
    # task-hours and a chain's execution its state transitions (the stage's Cost section).
    Slice(
        "staging",
        "orchestration",
        EPHEMERAL,
        "workflows + the chain layer (St.10), pipeline-applied",
    ),
    Slice(
        "production",
        "orchestration",
        EPHEMERAL,
        "workflows + the chain layer (St.10), pipeline-applied",
    ),
    # Stage 3's Deliverables, as slices rather than as a script. These are instruments: created,
    # read from the serial console, destroyed in the same sitting - `make down` is why they are
    # here and not in aws/probes/, whose declared safety class is that nothing is created. Three
    # t4g.nano at 0.0042/h (docs/PRICING.md 8); no IAM principal is created by either row. They
    # are on Graviton, with their own AMI data source, and a probe pays the ~20% Graviton
    # discount for measuring exactly what an x86 one would.
    # They are ordered: production/probes is the target, so it applies before the source row,
    # which finds it by name in the awsds.internal apex. rank 60 puts both after egress/, whose
    # S3 gateway policy the perimeter probe measures. Staging has no probe slice: it peers with
    # VPC-Networking alone, so it cannot reach the target in VPC-SharedServices.
    Slice("production", "probes", EPHEMERAL, "peering target: 1 host, 2 ENIs, 2 A records", 0.0042),
    Slice("sandbox", "probes", EPHEMERAL, "perimeter probe (isolated) + peering probe", 0.0084),
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
        "WireGuard host in the hub - the only human path into the private network (D38, D39)",
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
    # Stage 5a pass 1. Free or floor-priced at rest: one CMK (key-month), five buckets, catalog
    # objects, LF settings/tags/grants, two on-demand crawlers and the compaction optimizer
    # (config free; runs metered per DPU-hour, docs/PRICING.md 5).
    Slice(
        "data-governance",
        "data",
        PERSISTENT,
        "the lake: account data CMK, 5 buckets, catalog, LF (Stage 5a)",
    ),
    # Stage 5a pass 4 - the consumer side, one module applied twice. [P] and free or floor-priced
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
    # Stage 9 steps 1 and 4.1 - the two deployment targets' data platforms: the consumer-data call (the
    # account data CMK, the LF settings, the resource links and their re-grants), the outputs bucket,
    # the results bucket and the enforced Athena workgroup. Production's read rides beside its governed
    # write (2.3); Staging reads alone (decision 3). [P], free or floor-priced at rest, like Sandbox's.
    Slice(
        "production",
        "data",
        PERSISTENT,
        "consumer-data, outputs + derived buckets, the enforced workgroup, the job role's regrants",
    ),
    Slice(
        "staging",
        "data",
        PERSISTENT,
        "consumer-data (read only), outputs + derived buckets, the enforced workgroup",
    ),
    # Stage 7 pass 1 (step 2.1) - the internal CA: the root and two leaves in the `tls`
    # provider's state, three SSM parameters and three S3 objects publishing the certificates,
    # two Secrets Manager secrets holding the leaf keys. [P], never destroyed (NEVER_DESTROY,
    # D36), and free at rest but for the two secrets (USD 0.40/month each, docs/PRICING.md 6).
    Slice(
        "production",
        "pki",
        PERSISTENT,
        "the internal CA root + 2 leaves, published; leaf keys in Secrets Manager (D36)",
    ),
    # Stage 7 step 1.2 - GitLab CE, the repository's third [D] row. usd_per_hour is the t4g.large
    # row of docs/PRICING.md 8, measured us-west-2 (Lesson 6), the while-running figure: the two
    # EBS volumes (12 GiB root, 50 GiB data) and the daily DLM snapshots bill monthly while the
    # host is stopped and are floor lines in docs/plan/cost-model.md. Started and stopped by
    # `make gitlab-up` / `make gitlab-down`, which name this slice through `--only`; a plain
    # `make up ENV=production` starts it too, and leaves the hub pair to `make hub-up` (1.6).
    Slice(
        "production",
        "tooling",
        DORMANT,
        "GitLab CE on a t4g.large + its 50 GiB data volume (Stage 7 step 1.2)",
        0.0672,
    ),
    # Stage 7 step 6.1 - the build runner, [E], and the buildbox's successor on the same measured
    # shape (m8i.xlarge 0.2117/h, docs/PRICING.md 8); Stage 8 step 4.3 adds the deploy runner
    # (t3a.small 0.0188/h) once deploy_image_digest is set, and decision 11 the test runner (t3a.small
    # 0.0188/h). The build runner exists only while an apply sets var.build_runner (`make gitlab-up
    # BUILD=1`, Stage 7 decision 5), so it is an optional host and the slice's own rate is the other
    # two. Destroyed by `make gitlab-down` and by `make down ENV=production`; a forgotten set is this
    # stage's likeliest leak, at 0.2493/h with the build runner.
    Slice(
        "production",
        "runners",
        EPHEMERAL,
        "the deploy and test runners, and the build runner on BUILD=1 (St.7 6.1, St.8 4.3, d. 11)",
        0.0376,
        optional_hosts=(("aws_instance.runner", 0.2117),),
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
    # Stage 9 step 3 - the same slice name in a deployment target, and a different content: the
    # job role, the Model Registry's package groups, the debug role and its alarm, the job log
    # groups (D17's runtime half). [P] and free at rest: roles, rules and empty groups cost
    # nothing. Rank 46 sits above foundation/ and registry/, whose states it reads; the first apply
    # also precedes production/data/ (45), whose key and bucket policies name the two roles, the
    # inversion the sso/data row above describes and for the same reason no order acts on it.
    Slice("production", "sagemaker", PERSISTENT, "job role, model registry, debug role + alarm"),
    # Stage 9 step 4.3 - Staging's copy of the runtime half, the job role and its log groups alone:
    # the registry and the escape hatch stay Production's. [P] and free at rest. It reads
    # production/registry/'s state for the application repository, a cross-account read no rank orders.
    Slice("staging", "sagemaker", PERSISTENT, "job role + the job log groups (St.9 4.3)"),
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
    # Stage 6d step 2 - the house image made selectable: the image, one immutable version and one
    # app image configuration per app type, all metadata. The container it points at lives in the
    # registry account and is pulled by the project role when a space starts, which is where the
    # cost is.
    Slice("sandbox", "dev-env", PERSISTENT, "the dev-env image, its version + 2 app configs"),
    # Stage 6e step 3 - one IAM policy and one attachment per SMUS project that may invoke the
    # scoped Claude models. Persistent and nearly free: a policy costs nothing and an attachment
    # is not a resource anybody pays for. What it is NOT is self-maintaining - `project_roles` is
    # hand-written once per project, which decision 8 took deliberately.
    Slice(
        "sandbox", "bedrock", PERSISTENT, "the Bedrock grant: 1 policy + 1 attachment per project"
    ),
    # Stage 17 decision 13 - the model provisioning role, under the name the console adopts, and the
    # playground's model consumption role, both under the D13 boundary. IAM only, free at rest; the
    # application inference profiles DataZone creates with the first role are not this slice's.
    Slice(
        "sandbox",
        "model-access",
        PERSISTENT,
        "the console's model access: 2 roles, 1 inline policy each",
    ),
    # Stage 6i decision 6 - one IAM policy and one attachment per SMUS project whose workflows run
    # SageMaker processing jobs: DescribeProcessingJob on a job no project tag marks, which is what
    # the operator's existence check needs, and AddTags of the caller's project tag, which the create needs. Free at rest, hand-written per project like `bedrock`.
    Slice(
        "sandbox",
        "workflows",
        PERSISTENT,
        "the workflows grant: 1 policy + 1 attachment per project",
    ),
    # Stage 5b pass 1 - the data half of the warehouse. [P] and free at rest in the sense this
    # column measures: nothing in it is metered by the hour. What it DOES cost is Redshift Managed
    # Storage at 0.024 USD/GB-month (docs/PRICING.md 5), which `make down` does not remove and
    # which a schema filled to its 1 TB quota takes to 24.58 USD/month - so this row's 0.0 is true
    # and incomplete at once, exactly as `sandbox/lake`'s is, and the bill it does generate is the
    # stage's Cost section rather than `make status`'s.
    Slice(
        "sandbox",
        "warehouse",
        PERSISTENT,
        "the Redshift namespace, its admin secret, 3 audit groups, the exec role + alarms",
    ),
    # Stage 5b pass 1 - the compute half, and the whole point of the split.
    #
    # usd_per_hour IS THE WORST CASE, NOT THE RATE, and it was 0.0 until 2026-09-20 cost 9.48 USD to
    # correct. The argument for the zero was true and useless: Redshift Serverless bills 0.36
    # USD/RPU-hour of QUERY time and nothing while idle, so an existing workgroup serving no query
    # really is 0.00/h. What that reasoning missed is what `make status` is FOR - an operator asking
    # "what is this session costing me" - and on the day one forgotten query ran for 6 h 33 min at
    # base capacity, `make status` answered 0.0000 USD/h for the whole of it. An authored zero on the
    # estate's most expensive object made its only runaway invisible to the estate's own burn meter.
    #
    # So the number here is 4 RPU x 0.36 = 1.44, the rate while a query IS running, and the column's
    # meaning for this one row is a CEILING rather than an average. That over-reads a quiet session,
    # which is the safe direction: the failure this row exists to prevent is an operator who reads
    # 0.00 and stops looking. The real rate for a session is ./aws/warehouse.py's burn line, which
    # reads ComputeSeconds - and note that the metric lands per HALF-HOUR interval, so a figure taken
    # right after an expensive query under-reads it.
    #
    # The other guards, and what each one turned out to be worth on 2026-09-20:
    #   the usage limit    UNPROVEN against this statement: breach_action = deactivate refused every
    #                      query needing the compute during 5.1's two minutes of breach, and the
    #                      runaway, a catalog query that runs on the leader node alone, kept running
    #                      through them (log-stage-05b, 2026-10-18). The user lowered the limit from
    #                      40 to 10 RPU-hours the same day - 3.60 USD/month.
    #   max_query_execution_time  DID NOT STOP IT. It was 1800 s, read back as 1800, and the query
    #                      ran 23,601 s. Three candidates stand: a superuser exempt from the
    #                      query-monitoring rules, a ceiling that binds nobody, or a leader-node
    #                      statement no WLM limit reaches (log-stage-05b, owed item 3).
    #   `make down`        WORKED, and is the only guarantee that is not a setting: no pause exists,
    #                      so destroying the workgroup is what stops the meter.
    Slice(
        "sandbox",
        "warehouse-compute",
        EPHEMERAL,
        "the 4-RPU workgroup + its serverless-compute usage limit - no pause exists, so [E]",
        usd_per_hour=1.44,
    ),
    # Stage 9 step 9.1 - the governed class of D40's warehouse, the Sandbox pair copied into Production
    # with the same split and the same rank. [P] here is 0.0 for the same reason Sandbox's row is: the
    # Redshift Managed Storage it bills is per GB-month, outside this column.
    Slice(
        "production",
        "warehouse",
        PERSISTENT,
        "the governed Redshift namespace, its admin secret, 3 audit groups, the exec role + alarms",
    ),
    # Stage 9 step 9.4: the operator raises the compute by hand before the DDL job and takes it down
    # after; awsds-deploy-prod cannot (the root SCP exempts InfrastructureAccess alone). The ceiling is
    # Sandbox's reasoning, 4 RPU x 0.36 while a query runs. The slice reads production/warehouse/'s
    # state, applied 2026-10-23, so `up` no longer holds it (refusal 9's table is empty).
    Slice(
        "production",
        "warehouse-compute",
        EPHEMERAL,
        "the 4-RPU governed workgroup + its serverless-compute usage limit - no pause exists, so [E]",
        usd_per_hour=1.44,
    ),
    # Stage 12 steps 1, 2 and 9 - a dashboard, alarms and quota alarms. Nothing here bills by the
    # hour: a dashboard and an alarm bill by the month past CloudWatch's free tier (three dashboards,
    # ten alarms, counted once per bill, docs/PRICING.md 6), and a metric filter's metric only for the
    # hours the proxy writes a log line.
    Slice(
        "production",
        "observability",
        PERSISTENT,
        "the hub dashboard, the proxy log's 2 metric filters, 2 alarms",
    ),
    Slice(
        "sandbox",
        "observability",
        PERSISTENT,
        "the alerts topic, the account dashboard, 5 quota alarms",
    ),
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

# A [D] slice whose host carries a Name tag other than `awsds-<env>-<slice>`. The dormant hook
# derives the tag from the row (slices.py instance_name) and this map is the one exception:
# conventions 6 names the slice `tooling/` while Stage 7 step 1.2 names the host
# `awsds-prod-gitlab`, the contract ./aws/supplychain.py SC-1 reads. One map, read by the hook,
# so the two names cannot drift apart in a third place (Lesson 14).
DORMANT_HOST_NAMES = {("production", "tooling"): "awsds-prod-gitlab"}

# Refusal 4 - `bootstrap/` is unreachable from either target. It holds its own state (step
# 2.2), so a destroy would delete the bucket that records the destroy. This is the case the
# stage's Validation tests by reading the plan rather than by trusting the target list.
NEVER_ANY_TARGET_SLICE_NAMES = {"bootstrap"}

# Refusal 5 is enforced in is_refused() below rather than as a set, because it is a property of
# the layer and not of a named slice.
#
# Refusal 6 is the hub's and lives in slices.py (Stage 7 step 1.6): ENV=production leaves the hub
# pair to hub-up and hub-down.
#
# Refusal 7 - Stage 8 step 2.4. `up` never applies an application or orchestration slice: its applier
# is the pipeline, which passes the release it promotes. A `make up` for an unrelated session would
# deploy the recorded release outside it, and an orchestration slice's schedule would start firing.
# `down` destroys both normally (Stage 10 step 1.4 relies on it).
APPLIED_BY_THEIR_OWN_HAND = {"orchestration"}
APPLICATION_PARENT = "app"
#
# Refusal 9 - an [E] slice held from `up` while the [P] state it reads does not exist, keyed by
# (account, slice) like NEVER_DESTROY, with the reason printed: a `make up` would otherwise stop at
# the slice's state read after raising the slices before it. `down` is unaffected. The table held
# production/warehouse-compute/ from 2026-10-22 until the namespace it reads was applied on
# 2026-10-23, and holds nothing today.
HELD_FROM_UP: dict[tuple[str, str], str] = {}
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


def deploy_profiles() -> set:
    """The pipeline profiles: the deploy runner names each after its deploy role (Stage 8 step 4.4)."""
    return set(backend.DEPLOY_ROLES.values()) | set(backend.DEPLOY_ROLES_BY_SLICE.values())


def pipeline_refusal(account: str, slice_name: str, profile: str) -> str | None:
    """Refusal 8 (Stage 8 step 2.4): why a pipeline profile must not apply this slice, or None.

    A pipeline profile is a deploy role's (backend.DEPLOY_ROLES and DEPLOY_ROLES_BY_SLICE; the deploy
    runner names each profile after its role). In an Interactive account it applies no slice: CI
    never applies into Sandbox (D21's surviving objection), and the two flows that write where people
    work create their objects through the API - the dev-env release its image versions (step 1.6,
    decision 18), the test deploy its workflow (decision 19). Neither deploy role holds state access,
    which refuses the same writes in IAM; this says so before anything runs.
    """
    if profile not in deploy_profiles() or account not in backend.SMUS_MEMBERS:
        return None
    return (
        f"refusal 8: the pipeline profile {profile} applies no {account}/ slice - CI never applies "
        "into the account people work in; the dev-env release creates image versions and the test "
        "deploy its workflow through the API (Stage 8 step 2.4, decisions 18 and 19)"
    )


# A slice folder sits under its account folder, or one level further down under one of these parents
# (conventions 6). Every reader of the tree discovers slices here, so `make check`, the lock check and
# the network-doc check see a nested slice alike.
NESTED_SLICE_PARENTS = (APPLICATION_PARENT,)


def slice_dirs_on_disk(live: Path) -> dict:
    """(account, slice name) -> the folder, for every slice folder under `live` holding a .tf file."""
    found = {(p.parent.parent.name, p.parent.name): p.parent for p in live.glob("*/*/*.tf")}
    for parent in NESTED_SLICE_PARENTS:
        for p in live.glob(f"*/{parent}/*/*.tf"):
            found[(p.parents[2].name, f"{parent}/{p.parent.name}")] = p.parent
    return found


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
    if action == "up" and (
        sl.name.startswith(f"{APPLICATION_PARENT}/") or sl.name in APPLIED_BY_THEIR_OWN_HAND
    ):
        return (
            "refusal 7: up never applies an application or orchestration slice - the pipeline "
            "applies it with the release it runs (Stage 8 step 2.4)"
        )
    if action == "up" and (sl.account, sl.name) in HELD_FROM_UP:
        return f"refusal 9: held from up - {HELD_FROM_UP[(sl.account, sl.name)]}"
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
