"""Which slice belongs to which lifecycle layer - the table `make up` and `make down` read.

Stage 2 step 8.1 asks for exactly this and phrases the requirement as a refusal of the
obvious alternative: **a slice declares its layer in a table, not in a comment.** A comment is
read by a person; `make down` has to be read by a program, and D11's whole claim - "pay
nothing while idle" - is a claim about a command, not about an intention (Lesson 5).

THE THREE LAYERS (D11, docs/plan/conventions.md 5.1):

  [P] persistent  created once, never destroyed. Free or nearly free at rest.
  [D] dormant     kept, but powered off between sessions - stop/start, never destroy.
  [E] ephemeral   destroyed at the end of a session and rebuilt from code.

WHAT THIS TABLE IS *FOR*, since every row in it today says [P] and `make down` therefore does
nothing. The machinery is written BEFORE the first [E] slice exists rather than after it, which
is step 8.6's own reasoning applied to the whole target: a hook added later is a hook that was
missing from the first teardown that needed it. Stage 3's `egress/` is the first [E] slice and
Stage 4's WireGuard `vpn/` the first [D] one (Stage 5's EFS is [P] by decision - conventions
5.1 rule 2, D24); both arrive to a `make down` that already refuses the four things it must
refuse.

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
    "sso": 10,
    "org-policies": 11,
    "foundation": 20,
    "pki": 30,
    # BELOW egress ON PURPOSE (Stage 4 step 1.3): `up` ascends rank and `down` descends it,
    # so a rank under egress starts the tunnel BEFORE the [E] slices exist and stops it AFTER
    # they are gone. That is the order 8.3 makes load-bearing - from then on every API call
    # must exit through the VPN EIP, so the tunnel is the first thing up and the last down.
    # The row itself lands with the slice, in one commit (step 1.3): this check fails on a
    # declared slice that is not on disk, and it is right to - a row with nothing behind it
    # makes the table stop being evidence. The rank is here early because the ORDER is the
    # part that was got wrong once and is worth fixing before anything consumes it.
    "vpn": 40,
    "egress": 50,
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
    Slice("sandbox", "egress", EPHEMERAL, "NAT + 12 interface endpoints (8.3)", 0.170),
    Slice("development", "egress", EPHEMERAL, "NAT + 11 interface endpoints, no EFS (D24)", 0.160),
    Slice("production", "egress", EPHEMERAL, "NAT + 10 interface endpoints (8.3)", 0.150),
    # Stage 3's Deliverables, as slices rather than as a script (2026-08-16). These are
    # INSTRUMENTS: created, read from the serial console, destroyed in the same sitting -
    # `make down` is the whole reason they are here and not in aws/probes/, whose declared
    # safety class is that nothing is created. Three t4g.nano at 0.0042/h (docs/PRICING.md 3,
    # the same row Stage 4's WireGuard host uses); no IAM principal is created by either row.
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
]


# ------------------------------------------------------------------------- the refusals
#
# Step 8.3 lists four, "each of which is a bug if it is missing". Three are enforced here as
# DATA and one in the caller as an argument check, and two of these three are deliberately
# REDUNDANT with the layer filter - a `bootstrap/` row is already [P], so `up` and `down` would
# skip it anyway. The redundancy is the point: the day somebody mislabels a row, the layer
# filter fails open and this list does not.

# Refusal 3 - D36. production/pki/ holds the internal root CA's private key in its state.
# Rotating a root on a session boundary invalidates three client surfaces at 09:00, so the
# slice is unreachable from `down` WHATEVER LAYER ITS ROW EVER CLAIMS.
NEVER_DESTROY = {("production", "pki")}

# Refusal 4 - `bootstrap/` is unreachable from either target. It holds its own state (step
# 2.2), so a destroy would delete the bucket that records the destroy. This is the case the
# stage's Validation tests by reading the plan rather than by trusting the target list.
NEVER_ANY_TARGET_SLICE_NAMES = {"bootstrap"}


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
