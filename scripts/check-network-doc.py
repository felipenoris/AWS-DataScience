#!/usr/bin/env -S uv run --quiet
# check-network-doc.py - docs/NETWORK.md still describes the network the code builds.
#
#   run:      ./scripts/check-network-doc.py
#   reads:    scripts/tfhygiene/backend.py (the address allocation), terraform-modules/vpc/main.tf
#             (the per-tier cut), every .tf under terraform-live/, and docs/NETWORK.md.
#             Touches nothing, needs no AWS session.
#   exit:     0 when the document names everything below | 1 when it is behind the code.
#
# WHY THIS EXISTS. docs/NETWORK.md is the one picture of the whole network - the address plan,
# every element that holds an internal address, the routes, both egress paths, the DNS layer.
# It is written to be read INSTEAD of opening six slices, which is exactly what makes a stale
# copy expensive: a reader who trusts it does not go and check. The failure is silent in the
# direction that costs most - a slice added in Stage 7, 9, 13 or 14 puts a host on the wire and
# nothing in the repository says the picture is now incomplete (Lesson 34: a deferred obligation
# recorded only at the deferring end is a promise the receiving stage never gets).
#
# WHAT IT DECIDES, and all three are DERIVED rather than restated here (Lesson 14 - a second
# copy of the arithmetic would be one more thing to keep in step):
#
#   A. Every /16 in backend.CIDRS appears in the document, plus the WireGuard client range.
#      This is what a `Staging` vend or a second Sandbox unit trips.
#   B. For every account that HAS a foundation/ slice on disk, every per-tier subnet CIDR
#      appears - RECOMPUTED from the `cidrsubnet` calls in terraform-modules/vpc/main.tf, so
#      re-cutting the tiers there is what makes this fail rather than a number typed twice.
#      An account with an allocation and no foundation/ (Staging today) is checked by rule A
#      alone: its subnets do not exist, and demanding them would be demanding a fiction.
#   C. Every NETWORK-BEARING slice is named, as `<account>/<slice>`. Three ways to be one, and
#      the union is deliberate because each catches what the others miss:
#        - it declares a resource that holds an address, carries traffic or filters it
#        - it calls one of the network modules (a slice like sandbox/egress/ declares nothing
#          itself - the whole slice is one module call)
#        - its name is one of backend.NETWORK_SLICES (the allocation's own vocabulary)
#
# WHAT IT DELIBERATELY DOES NOT DECIDE, said out loud because a check that hides its blind side
# is not a check (Lesson 13):
#
#   - Whether a SENTENCE is still true. Nothing can. A route table that gained a route, a
#     security group that gained a rule, a measured date that has gone stale: those are the
#     reading, and the reading is what CLAUDE.md's upkeep row asks for. This decides the one
#     property a machine can - that the document still NAMES what exists.
#   - A slice that only REFERENCES a network (*/sagemaker/ hands the blueprint a VPC id and
#     subnet ids, and creates no network object of its own). It is named in the document
#     anyway, and its row says why - but nothing here would have noticed its absence.
#   - Anything AWS reports. This file never opens a session; what is deployed right now is
#     aws/networking.py and aws/egress.py, and whether a difference is expected is
#     docs/AWS_STATE.md.

from __future__ import annotations

import ipaddress
import os
import re
import sys
from pathlib import Path

from tfhygiene import backend

DOC = Path("docs/NETWORK.md")
VPC_MODULE = Path("terraform-modules/vpc/main.tf")
LIVE = Path("terraform-live")

# A resource that holds an address, moves a packet, or decides whether one passes. It is a
# LIST rather than a prefix match on `aws_vpc`/`aws_route` because the interesting ones do not
# share a prefix - an instance and a hosted zone are both network facts - and because a prefix
# rule would drag in aws_vpc_endpoint_policy-style attachments that add nothing to the picture.
NETWORK_RESOURCES = frozenset(
    {
        "aws_vpc",
        "aws_default_security_group",
        "aws_subnet",
        "aws_route",
        "aws_route_table",
        "aws_route_table_association",
        "aws_internet_gateway",
        "aws_nat_gateway",
        "aws_egress_only_internet_gateway",
        "aws_eip",
        "aws_eip_association",
        "aws_vpc_endpoint",
        "aws_security_group",
        "aws_vpc_security_group_ingress_rule",
        "aws_vpc_security_group_egress_rule",
        "aws_network_interface",
        "aws_network_interface_attachment",
        "aws_network_acl",
        "aws_instance",
        "aws_lb",
        "aws_vpc_peering_connection",
        "aws_vpc_peering_connection_accepter",
        "aws_flow_log",
        "aws_route53_zone",
        "aws_route53_record",
        "aws_route53_zone_association",
        "aws_route53_vpc_association_authorization",
        "aws_route53_resolver_firewall_rule_group_association",
    }
)

# The modules whose whole content is network. A slice calling one of these IS network-bearing
# even when it declares nothing itself, which is the ordinary shape here: egress/ and vpn/ are
# one module call each.
NETWORK_MODULES = frozenset({"vpc", "vpc-egress", "wireguard"})

RESOURCE_RE = re.compile(r'^\s*resource\s+"([a-z0-9_]+)"', re.M)
MODULE_SOURCE_RE = re.compile(r'source\s*=\s*"[^"]*terraform-modules/([a-z0-9-]+)\?ref=')

# The three `cidrsubnet` calls the vpc module cuts a /16 with. Written to match the module's
# actual shape - `[for i in range(2) : cidrsubnet(var.vpc_cidr, 4, 8 + i)]` - and to FAIL LOUDLY
# rather than silently find nothing if that shape ever changes: a checker that quietly skips
# what it cannot parse reports success about a file it never read.
TIER_RE = re.compile(
    r"(\w+)_cidrs\s*=\s*\[for i in range\((\d+)\)\s*:\s*"
    r"cidrsubnet\(var\.vpc_cidr,\s*(\d+),\s*(?:(\d+)\s*\+\s*)?i\)\]"
)


def tier_cuts(text: str) -> dict:
    """tier -> (how many, newbits, first index) - read from the module, never restated."""
    cuts = {}
    for tier, count, newbits, base in TIER_RE.findall(text):
        cuts[tier] = (int(count), int(newbits), int(base or 0))
    if len(cuts) < 3:
        sys.exit(
            f"{VPC_MODULE}: expected three cidrsubnet tier cuts, parsed {sorted(cuts)}. "
            "The module's locals block changed shape - update TIER_RE before trusting this gate."
        )
    return cuts


def subnets_of(vpc_cidr: str, cuts: dict) -> dict:
    """The subnet CIDRs the module WOULD build for one /16, tier by tier."""
    net = ipaddress.ip_network(vpc_cidr)
    out = {}
    for tier, (count, newbits, base) in sorted(cuts.items()):
        pieces = list(net.subnets(prefixlen_diff=newbits))
        out[tier] = [str(pieces[base + i]) for i in range(count)]
    return out


def network_bearing_slices() -> dict:
    """`account/slice` -> why it counts as network-bearing, for every slice on disk."""
    found = {}
    for slice_dir in sorted(p for p in LIVE.glob("*/*") if p.is_dir()):
        account, name = slice_dir.parent.name, slice_dir.name
        why = []
        if name in backend.NETWORK_SLICES:
            why.append(f"a `{name}` slice (backend.NETWORK_SLICES)")
        resources, modules = set(), set()
        for tf in sorted(slice_dir.glob("*.tf")):
            text = tf.read_text(encoding="utf-8", errors="replace")
            resources |= set(RESOURCE_RE.findall(text)) & NETWORK_RESOURCES
            modules |= set(MODULE_SOURCE_RE.findall(text)) & NETWORK_MODULES
        if modules:
            why.append("calls " + ", ".join(sorted(modules)))
        if resources:
            why.append("declares " + ", ".join(sorted(resources)))
        if why:
            found[f"{account}/{name}"] = "; ".join(why)
    return found


def main() -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    doc = DOC.read_text(encoding="utf-8")
    cuts = tier_cuts(VPC_MODULE.read_text(encoding="utf-8"))
    bad = 0

    def require(needle: str, what: str) -> None:
        nonlocal bad
        if needle in doc:
            return
        bad += 1
        print(f"MISSING {what}: {needle}")

    print("== the address allocation (backend.CIDRS + the WireGuard client range) ==")
    for account, cidr in sorted(backend.CIDRS.items()):
        require(cidr, f"{account}'s VPC CIDR")
    require(backend.WIREGUARD_PEER_CIDR, "the WireGuard client range")
    require(backend.SANDBOX_SUPERNET, "the Sandbox supernet")
    print(f"  {len(backend.CIDRS)} allocation(s) + the client range and the supernet")

    print()
    print("== the per-tier subnets, recomputed from terraform-modules/vpc/main.tf ==")
    for account, cidr in sorted(backend.CIDRS.items()):
        if not (LIVE / account / "foundation").is_dir():
            print(f"  {account}: no foundation/ slice - its subnets do not exist, rule A only")
            continue
        for tier, cidrs in subnets_of(cidr, cuts).items():
            for sub in cidrs:
                require(sub, f"{account}'s {tier} subnet")
        print(f"  {account}: {sum(len(v) for v in subnets_of(cidr, cuts).values())} subnet(s)")

    print()
    print("== every network-bearing slice is named ==")
    slices = network_bearing_slices()
    for path, why in sorted(slices.items()):
        if path in doc:
            continue
        bad += 1
        print(f"MISSING slice {path} - {why}")
    print(f"  {len(slices)} network-bearing slice(s) on disk")

    print()
    if bad:
        print(f"REVIEW NEEDED - {bad} thing(s) the code has and {DOC} does not name")
        return 1
    print(
        f"clean - {DOC} names everything the code builds (whether it is still TRUE is the reading)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
