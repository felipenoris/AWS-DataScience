#!/usr/bin/env -S uv run --quiet
# check-network-doc.py - docs/NETWORK.md still describes the network the code builds.
#
#   run:      ./scripts/check-network-doc.py
#   reads:    scripts/tfhygiene/backend.py (the address allocation), terraform-modules/vpc/main.tf
#             (the per-tier cut), every .tf under terraform-live/, and docs/NETWORK.md.
#             Touches nothing, needs no AWS session.
#   exit:     0 when the document names everything below | 1 when it is behind the code.
#
# docs/NETWORK.md is written to be read instead of opening six slices, so a stale copy is expensive
# and silent: a slice added by a later stage puts a host on the wire and nothing says the picture is
# incomplete (Lesson 34). The three rules are derived from the code, never restated here:
#
#   A. Every /16 in backend.CIDRS appears in the document, plus the WireGuard client range.
#   B. For every account with a foundation/ slice on disk, every per-tier subnet CIDR appears,
#      recomputed from the `cidrsubnet` calls in terraform-modules/vpc/main.tf. An account with an
#      allocation and no foundation/ (a Stage 14 vend before its slices exist) is checked by rule A
#      alone: its subnets do not exist.
#   C. Every network-bearing slice is named as `<account>/<slice>`. A slice is network-bearing when
#      it declares a resource that holds an address, carries traffic or filters it; when it calls
#      one of the network modules (sandbox/egress/ is one module call); or when its name is in
#      backend.NETWORK_SLICES.
#
# Not decided here (Lesson 13): whether a sentence is still true (a route gained, a rule added, a
# stale measured date - that is the reading CLAUDE.md's upkeep row asks for); a slice that only
# references a network (*/sagemaker/ hands the blueprint a VPC id and subnet ids); and anything AWS
# reports (aws/networking.py and aws/egress.py read the estate; whether a difference is expected is
# docs/AWS_STATE.md).

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

# A resource that holds an address, moves a packet, or decides whether one passes. A list rather
# than a prefix match: an instance and a hosted zone are both network facts, and a prefix rule would
# drag in aws_vpc_endpoint_policy-style attachments that add nothing to the picture.
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

# The modules whose whole content is network. A slice calling one is network-bearing even when it
# declares nothing itself: egress/ and vpn/ are one module call each.
NETWORK_MODULES = frozenset({"vpc", "vpc-egress", "wireguard"})

RESOURCE_RE = re.compile(r'^\s*resource\s+"([a-z0-9_]+)"', re.M)
MODULE_SOURCE_RE = re.compile(r'source\s*=\s*"[^"]*terraform-modules/([a-z0-9-]+)\?ref=')

# The three `cidrsubnet` calls the vpc module cuts a /16 with, matching the module's shape
# `[for i in range(2) : cidrsubnet(var.vpc_cidr, 4, 8 + i)]`. If the shape changes this fails loudly
# rather than finding nothing: a checker that skips what it cannot parse reports success about a
# file it never read.
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

    # Per (account, slice): Production holds three VPCs (D38), so rule A asks for every /16 the
    # address plan allocates, not for an account's CIDR.
    print("== the address allocation (backend.VPC_CIDRS + the WireGuard client range) ==")
    for (account, slice_name), cidr in sorted(backend.VPC_CIDRS.items()):
        require(cidr, f"{account}/{slice_name}'s VPC CIDR")
    require(backend.WIREGUARD_PEER_CIDR, "the WireGuard client range")
    require(backend.SANDBOX_SUPERNET, "the Sandbox supernet")
    print(f"  {len(backend.VPC_CIDRS)} allocation(s) + the client range and the supernet")

    print()
    print("== the per-tier subnets, recomputed from terraform-modules/vpc/main.tf ==")
    for (account, slice_name), cidr in sorted(backend.VPC_CIDRS.items()):
        # A slice whose folder does not exist yet is checked by rule A alone: its subnets are not
        # cut anywhere. Stage 14 puts a vended Sandbox unit in this state.
        if not (LIVE / account / slice_name).is_dir():
            print(
                f"  {account}/{slice_name}: no slice on disk - its subnets do not exist, rule A only"
            )
            continue
        for tier, cidrs in subnets_of(cidr, cuts).items():
            for sub in cidrs:
                require(sub, f"{account}/{slice_name}'s {tier} subnet")
        n = sum(len(v) for v in subnets_of(cidr, cuts).values())
        print(f"  {account}/{slice_name}: {n} subnet(s)")

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
