#!/usr/bin/env -S uv run --quiet
# networking.py - the [P] networking half, per account, side by side: VPCs (default ones
# flagged), DNS attributes, subnets anchored on zone IDs, route tables and routes, internet
# gateways, the S3/DynamoDB GATEWAY endpoints (the INT-05 anchor), VPC peerings seen from
# both sides, the private hosted zones with their associations and pending authorizations,
# flow logs, NACLs and security groups - plus one REGIONAL reading, the endpoint-service
# catalog against the SMUS portal's surfaces (section 10, NT-9). The preflight for Stage 3,
# and the standing regression after each of its passes.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/networking.py                        # every awsds-* profile
#             ./aws/networking.py awsds-infra-prod       # only the ones named
#             python3 aws/networking.py -                # CloudShell, ambient credentials
#   writes:   aws/output/networking.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeVpcs, DescribeVpcAttribute, DescribeSubnets, DescribeRouteTables,
#             DescribeInternetGateways, DescribeVpcEndpoints, DescribeVpcEndpointServices,
#             DescribeVpcPeeringConnections,
#             DescribeFlowLogs, DescribeNetworkAcls, DescribeSecurityGroups,
#             route53:ListHostedZones, GetHostedZone, ListVPCAssociationAuthorizations,
#             logs:DescribeLogGroups, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The subject is a
# PER-ACCOUNT fact whose meaning is the comparison BETWEEN accounts: a CIDR overlap is a
# relation between two VPCs in two accounts, a peering has a requester and an accepter on
# opposite sides of a boundary, and a cross-account zone association exists precisely
# because one account owns the zone and another owns the VPC. A single-profile version
# would answer nothing. Same shape as AZs.py and tf-backends.py, and it pays the rule back
# the same way - section 1 prints the caller ARN of every profile.
#
# WHAT IT IS FOR, IN TWO PHASES.
#
#   BEFORE Stage 3: "what networking already exists". The first run (2026-08-15) measured
#   what no plan file had: every vended account carries an ACCOUNT FACTORY VPC
#   (172.31.0.0/16, private-only - docs/AWS_STATE.md C), which step 0 now removes.
#   Principle 4 says private by default; D22 says Data Governance gets no VPC at all.
#   Whether either sentence is TRUE TODAY is what section 2 answers.
#
#   AFTER each Stage 3 pass: the readings that would otherwise be one console tab per
#   account - validation 2 (no route into 10.40.0.0/16), step 6.5 (10.90.0.0/24 in no
#   route table), step 4.4 (the four zone associations), step 5 (a flow log per VPC),
#   step 4.1 (both DNS attributes on). Each is a check that FAILS, not a listing to eyeball.
#
# THE [P]-STABILITY DELIVERABLE IS A DIFF OF TWO RUNS OF THIS FILE. Stage 3's lifecycle
# deliverable wants every foundation/ ID byte-identical across a make down / make up.
# Run this, copy aws/output/networking.txt aside, cycle, run again, diff: the only lines
# that may change are the timestamp and the [E] resources this file deliberately omits.
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - Staging is UNVENDED (held on the account cap) and has no profile: the deliverable
#     "describe-vpc-peering-connections in Staging returns empty" cannot run from here
#     until the vend. Absence from this report is silence, not evidence.
#   - Management, Log Archive and Audit hold no CLI profile by design; their default VPCs
#     (if any) are unmeasured here. None of them is meant to hold a Stage 3 VPC.
#   - This is a CONTROL-PLANE reading. The stage's behavioural proofs - dnf through the
#     gateway endpoint, NXDOMAIN from Staging, the probe reaching GitLab's port - need the
#     throwaway probe instances the stage describes; a describe call proves none of them
#     (read the configuration when the question is configuration, keep probes for
#     behaviour - Lesson 20).

from __future__ import annotations

import sys
from itertools import combinations

from awslib import cidr, context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, note

OUT_NAME = "networking.txt"

# The profiles step 4.4's association checks resolve against. Profile names are the
# convention aws/INDEX.md documents; if one is renamed, the check reports "cannot resolve"
# rather than failing wrongly.
SBX_PROFILE = "awsds-infra-sandbox-1"
DEV_PROFILE = "awsds-infra-dev"
DATA_PROFILE = "awsds-infra-data"
CANARY_PROFILE = "awsds-policy-canary"

# The two ranges the route checks are about (Stage 3 validation 2 and step 6.5).
STAGING_CIDR = "10.40.0.0/16"
WIREGUARD_CIDR = "10.90.0.0/24"

# The range Control Tower's ACCOUNT FACTORY VPC occupies (measured 2026-08-15: every vended
# account carries one - IsDefault=False, three private subnets named aws-controltower-*, no
# IGW, a flow log at 90 days). The project's own address plan is 10.0.0.0/8-based (step
# 1.2), so a VPC in this range is a vend artifact, never one of ours.
AF_CIDR = "172.31.0.0/16"

# NT-9 / section 10: the endpoint-service catalog families whose MEMBERSHIP is a recorded
# architectural premise (measured 2026-08-24). The load-bearing fact is an ABSENCE: among
# the region's ~569 services, NO entry serves the SMUS portal's BROWSER surfaces - the
# on.aws portal itself, its CloudFront assets, agent.datazone.<region>.api.aws,
# sagemaker-unified-studio.<region>.api.aws - so no endpoint set reaches the portal
# privately and public egress stays REQUIRED for it (architecture.md §4.3a's design-B
# input). An absence cannot be listed, so the check pins the families the missing door
# would appear IN: if AWS ships one the way it shipped Console Private Access (the
# console/signin rows of section 10), the membership moves and NT-9 goes red - the signal
# to re-read the premise, never a network failure.
PORTAL_FAMILY_BASELINE = {
    "datazone": {"datazone", "datazone-fips"},
    "sagemaker-unified-studio": {"sagemaker-unified-studio-mcp"},
}

# Section 10's display filter - the families the 2026-08-24 hand query grepped for,
# mechanised so the next reader gets the rows beside the interpretation.
CATALOG_SURFACES = ("datazone", "sagemaker", "sqlworkbench", "console", "signin")


def catalog_family(token: str) -> str | None:
    """The PORTAL_FAMILY_BASELINE family a com.amazonaws.<region>.<token> belongs to."""
    for family in PORTAL_FAMILY_BASELINE:
        if token == family or token.startswith(family + "-") or token.startswith(family + "."):
            return family
    return None


def internet_exit_default(dest: str, target: str) -> bool:
    """The catch-all route out to the internet - the shape every public tier carries (2.1).

    0.0.0.0/0 contains every RFC1918 range ARITHMETICALLY, but an internet exit cannot
    deliver INTO one: an IGW or NAT forwards to the internet routing table, where 10/8 is
    unroutable. Left in the overlap test, the mandatory public default route keeps NT-3 and
    NT-4 red forever - and a permanently red check is one nobody reads (Lesson 13's
    corollary; first tripped on the pass-1 measurement, 2026-08-16). Only exactly this
    shape is excluded: a route naming a guarded range ITSELF, whatever its target, is still
    flagged - somebody wrote that range deliberately, and NT-6 covers the peering side.
    """
    return dest == "0.0.0.0/0" and (target.startswith("igw-") or target.startswith("nat-"))


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    checks = Checks()

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    # ------------------------------------------------------------------- measure each account
    vpcs: list = []  # (p, vpc, cidr, default, dnssup, dnshost)
    routes: list = []  # (p, rtb, vpc, dest, target, state)
    gweps: list = []  # (p, vpce, service, vpc)
    peers: list = []  # (p, pcx, status, req vpc, req cidr, acc vpc, acc cidr)
    zones: list = []  # (p, zone id, zone name)
    zonevpcs: list = []  # (p, zone name, vpc, region)
    flows: set = set()  # (p, resource id with a flow log)

    for p in live:
        cli = cli_for(p)
        note(f"measuring {p} ...")

        # VPCs, then the two DNS attributes each - DescribeVpcs does not return them.
        res = cli.run(
            "ec2",
            "describe-vpcs",
            "--query",
            "Vpcs[].[VpcId,CidrBlock,IsDefault,State]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "ec2 describe-vpcs", res.stderr)
            continue
        for line in res.stdout.splitlines():
            f = line.split("\t")
            if len(f) < 4 or not f[0]:
                continue
            vpc, vpc_cidr = f[0], f[1]
            is_default = f[2]
            r = cli.run(
                "ec2",
                "describe-vpc-attribute",
                "--vpc-id",
                vpc,
                "--attribute",
                "enableDnsSupport",
                "--query",
                "EnableDnsSupport.Value",
                "--output",
                "text",
                log=False,
            )
            dnssup = r.text or "?"
            if not r.ok:
                logerr(p, f"ec2 describe-vpc-attribute enableDnsSupport {vpc}", r.stderr)
            r = cli.run(
                "ec2",
                "describe-vpc-attribute",
                "--vpc-id",
                vpc,
                "--attribute",
                "enableDnsHostnames",
                "--query",
                "EnableDnsHostnames.Value",
                "--output",
                "text",
                log=False,
            )
            dnshost = r.text or "?"
            if not r.ok:
                logerr(p, f"ec2 describe-vpc-attribute enableDnsHostnames {vpc}", r.stderr)
            vpcs.append((p, vpc, vpc_cidr, is_default, dnssup, dnshost))

        # Routes, one call per route table so the rows stay flat.
        res = cli.run(
            "ec2",
            "describe-route-tables",
            "--query",
            "RouteTables[].[RouteTableId,VpcId]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "ec2 describe-route-tables", res.stderr)
        else:
            for line in res.stdout.splitlines():
                f = line.split("\t")
                if len(f) < 2 or not f[0]:
                    continue
                rtb, vpc = f[0], f[1]
                r = cli.run(
                    "ec2",
                    "describe-route-tables",
                    "--route-table-ids",
                    rtb,
                    "--query",
                    "RouteTables[0].Routes[].[DestinationCidrBlock || "
                    "DestinationIpv6CidrBlock || DestinationPrefixListId || `-`, "
                    "GatewayId || NatGatewayId || VpcPeeringConnectionId || "
                    "TransitGatewayId || EgressOnlyInternetGatewayId || "
                    "NetworkInterfaceId || InstanceId || `-`, State || `-`]",
                    "--output",
                    "text",
                    log=False,
                )
                if not r.ok:
                    logerr(p, f"ec2 describe-route-tables --route-table-ids {rtb}", r.stderr)
                    continue
                for route_line in r.stdout.splitlines():
                    rf = route_line.split("\t")
                    if len(rf) < 3 or not rf[0]:
                        continue
                    routes.append((p, rtb, vpc, rf[0], rf[1], rf[2]))

        # Gateway endpoints - the [P] anchor INT-05 conditions on.
        res = cli.run(
            "ec2",
            "describe-vpc-endpoints",
            "--filters",
            "Name=vpc-endpoint-type,Values=Gateway",
            "--query",
            "VpcEndpoints[].[VpcEndpointId,ServiceName,VpcId]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "ec2 describe-vpc-endpoints (gateway)", res.stderr)
        else:
            for line in res.stdout.splitlines():
                f = line.split("\t")
                if len(f) >= 3 and f[0]:
                    gweps.append((p, f[0], f[1], f[2]))

        # Peerings - the API answers from both sides, so the same pcx-* appears under both
        # profiles.
        res = cli.run(
            "ec2",
            "describe-vpc-peering-connections",
            "--query",
            "VpcPeeringConnections[].[VpcPeeringConnectionId,Status.Code,"
            "RequesterVpcInfo.VpcId,RequesterVpcInfo.CidrBlock || `-`,"
            "AccepterVpcInfo.VpcId,AccepterVpcInfo.CidrBlock || `-`]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "ec2 describe-vpc-peering-connections", res.stderr)
        else:
            for line in res.stdout.splitlines():
                f = line.split("\t")
                if len(f) >= 6 and f[0]:
                    peers.append((p, f[0], f[1], f[2], f[3], f[4], f[5]))

        # Private hosted zones this account owns, their associated VPCs, pending
        # authorizations.
        res = cli.run(
            "route53",
            "list-hosted-zones",
            "--query",
            "HostedZones[?Config.PrivateZone].[Id,Name]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "route53 list-hosted-zones", res.stderr)
        else:
            for line in res.stdout.splitlines():
                f = line.split("\t")
                if len(f) < 2 or not f[0]:
                    continue
                zid = f[0].rsplit("/", 1)[-1]
                zname = f[1].rstrip(".")
                zones.append((p, zid, zname))
                r = cli.run(
                    "route53",
                    "get-hosted-zone",
                    "--id",
                    zid,
                    "--query",
                    "VPCs[].[VPCId,VPCRegion]",
                    "--output",
                    "text",
                    log=False,
                )
                if not r.ok:
                    logerr(p, f"route53 get-hosted-zone {zid}", r.stderr)
                else:
                    for zline in r.stdout.splitlines():
                        zf = zline.split("\t")
                        if len(zf) >= 2 and zf[0]:
                            zonevpcs.append((p, zname, zf[0], zf[1]))

        # Flow logs - which VPCs have one.
        res = cli.run(
            "ec2",
            "describe-flow-logs",
            "--query",
            "FlowLogs[].[ResourceId]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "ec2 describe-flow-logs", res.stderr)
        else:
            for rid in res.stdout.split():
                if rid:
                    flows.add((p, rid))

    # The endpoint-service CATALOG - regional, not per-account: one call from the first
    # live profile answers for everyone. egress.py section 7 reads the SAME API for a
    # DIFFERENT question - which services support an endpoint POLICY, feeding EG-1, an
    # [E]-session concern - while this read is a standing premise of the egress design
    # itself: which doors EXIST for this estate's surfaces. Two files, one API, two
    # questions - kept apart deliberately (Lesson 33), each beside the checks it feeds.
    svc_catalog: list = []  # (service name, service type, private dns name)
    catalog_read = False
    if live:
        res = cli_for(live[0]).run(
            "ec2",
            "describe-vpc-endpoint-services",
            "--query",
            "ServiceDetails[].[ServiceName,ServiceType[0].ServiceType,PrivateDnsName || `-`]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(live[0], "ec2 describe-vpc-endpoint-services", res.stderr)
        else:
            catalog_read = True
            for line in res.stdout.splitlines():
                f = line.split("\t")
                if len(f) >= 3 and f[0]:
                    svc_catalog.append((f[0], f[1], f[2]))

    # ------------------------------------------------------------------------------- checks
    nondef = sum(1 for v in vpcs if v[3] == "False")

    # NT-1: VPCs nobody in this project created - the field Stage 3 never named (Lesson 16,
    # Lesson 17). Three shapes: a true DEFAULT VPC (public subnets, an IGW); the ACCOUNT
    # FACTORY VPC every vend leaves behind (172.31.0.0/16, private-only); and a
    # project-range VPC in an account where a decision says there must be none.
    for p, vpc, vpc_cidr, is_default, _s, _h in vpcs:
        extra = ""
        if p == DATA_PROFILE:
            extra = (
                " In THIS account the sentence is stronger: D22 says Data Governance "
                "gets no VPC at all - today that sentence is an intention, not a "
                "state (Lesson 5)."
            )
        if p == CANARY_PROFILE:
            extra = (
                " In THIS account the sentence is stronger: the canary is deliberately empty (D29)."
            )
        if is_default == "True":
            checks.note(
                "NT-1",
                f"default VPC in {p}",
                f"{vpc} ({vpc_cidr}) - public subnets and an attached IGW nobody "
                "chose (principle 4: private by default). Not a Stage 3 step 0 "
                "artifact; decide its fate deliberately and record it in the "
                f"log.{extra}",
            )
        elif cidr.overlap(vpc_cidr, AF_CIDR):
            checks.note(
                "NT-1",
                f"Account Factory VPC in {p}",
                f"{vpc} ({vpc_cidr}) - the vend artifact Control Tower leaves in "
                "every account (Lesson 17: a service that sets itself up creates "
                "resources nobody chose). Stage 3 step 0 (settled 2026-08-16) "
                "removes it: delete its stack instance from the Account Factory "
                "StackSet on Management (0.2), and turn creation off in Account "
                "Factory (0.3) BEFORE the Staging vend, so the next account "
                f"arrives without one.{extra}",
            )
        elif p == DATA_PROFILE:
            checks.fail(
                "NT-1",
                f"project-range VPC in {p}",
                f"{vpc} ({vpc_cidr}) - D22 says Data Governance gets no VPC at "
                "all. An intention is not a control (Lesson 5); this is the "
                "measurement.",
            )
        elif p == CANARY_PROFILE:
            checks.fail(
                "NT-1",
                f"project-range VPC in {p}",
                f"{vpc} ({vpc_cidr}) - the canary is deliberately empty (D29). A "
                "leftover here usually means an interrupted battery: read the log "
                "before deleting anything.",
            )

    # NT-2: both DNS attributes on every non-default VPC (step 4.1) - endpoint private DNS
    # and everything in step 4 silently fails without them, and aws_vpc defaults hostnames
    # to false.
    for p, vpc, _c, is_default, dnssup, dnshost in vpcs:
        if is_default != "False":
            continue
        if dnssup == "True" and dnshost == "True":
            checks.ok(
                "NT-2",
                f"DNS attributes on {vpc} ({p})",
                "enableDnsSupport=True enableDnsHostnames=True",
            )
        else:
            checks.fail(
                "NT-2",
                f"DNS attributes on {vpc} ({p})",
                f"enableDnsSupport={dnssup} enableDnsHostnames={dnshost} - step "
                "4.1 needs BOTH; private DNS on every interface endpoint and "
                "every zone of step 4 resolves nothing without them.",
            )

    # NT-3: no non-local route whose destination overlaps 10.40.0.0/16 (validation 2). The
    # local route of a future Staging VPC is excluded on purpose: the validation's intent is
    # "no PEERING path into Staging" (D20), not "Staging may not route to itself" - and the
    # internet-exit default route is excluded for the reason internet_exit_default() carries.
    nt3 = 0
    for p, rtb, _vpc, dest, target, state in routes:
        if target == "local" or internet_exit_default(dest, target):
            continue
        if cidr.overlap(dest, STAGING_CIDR):
            checks.fail(
                "NT-3",
                "route into the Staging range",
                f"{p} {rtb}: {dest} -> {target} ({state}) overlaps "
                f"{STAGING_CIDR} - Staging is deliberately unpeered (D20, "
                "step 6.6).",
            )
            nt3 += 1
    if nt3 == 0 and routes:
        n_accounts = len({r[0] for r in routes})
        checks.ok(
            "NT-3",
            f"no non-local route overlaps {STAGING_CIDR}",
            f"{len(routes)} routes read across {n_accounts} account(s)",
        )

    # NT-4: 10.90.0.0/24 in no route table anywhere (step 6.5) - peering does no
    # edge-to-edge routing, so a route to the WireGuard client range is a route that can
    # never work, and its presence means somebody is about to lose an evening to it. The
    # internet-exit default route is excluded here for the same reason as in NT-3.
    nt4 = 0
    for p, rtb, _vpc, dest, target, state in routes:
        if internet_exit_default(dest, target):
            continue
        if cidr.overlap(dest, WIREGUARD_CIDR):
            checks.fail(
                "NT-4",
                "route touching the WireGuard client range",
                f"{p} {rtb}: {dest} -> {target} ({state}) overlaps "
                f"{WIREGUARD_CIDR} - that range is SNATed by the WireGuard "
                "instance and appears in no route table by design (step 6.5).",
            )
            nt4 += 1
    if nt4 == 0 and routes:
        checks.ok("NT-4", f"no route overlaps {WIREGUARD_CIDR}", "same read as NT-3")

    # NT-5: pairwise CIDR overlap among project VPCs, across every measured account (1.2:
    # ranges are non-overlapping even between accounts that will never peer). Default and
    # Account Factory VPCs are excluded - they are ALL 172.31.0.0/16, they never peer, and
    # fifteen overlap rows with one root cause would bury a real one; their fate is NT-1's
    # question, and they are counted once below.
    project_vpcs = [
        (p, vpc, c)
        for p, vpc, c, is_default, _s, _h in vpcs
        if is_default == "False" and not c.startswith("172.31.")
    ]
    n_af = sum(1 for v in vpcs if v[2].startswith("172.31."))
    if n_af > 0:
        checks.note(
            "NT-5",
            "VPCs excluded from the overlap check",
            f"{n_af} in the 172.31.0.0/16 range (default or Account Factory) - "
            "all mutually overlapping by construction, never peered, and covered "
            "by NT-1 instead.",
        )
    if project_vpcs:
        overlaps = []
        for (p1, v1, c1), (p2, v2, c2) in combinations(project_vpcs, 2):
            # the same VPC seen through two profiles that reach the same account is one
            # VPC, not an overlap
            if v1 == v2:
                continue
            if cidr.overlap(c1, c2):
                overlaps.append(f"{p1} {v1} ({c1}) overlaps {p2} {v2} ({c2})")
        if overlaps:
            for line in overlaps:
                checks.fail(
                    "NT-5",
                    "VPC CIDR overlap",
                    f"{line} - a CIDR chosen to overlap cannot be revisited "
                    "without rebuilding the VPC (step 1.2).",
                )
        else:
            checks.ok(
                "NT-5",
                "no CIDR overlap among non-default VPCs",
                f"{nondef} VPC(s) compared pairwise",
            )

    # NT-6: no peering touches the Staging range from either side (D20, step 6.6).
    for p, pcx, status, rvpc, rcidr, avpc, acidr in sorted(set(peers)):
        for c in (rcidr, acidr):
            if cidr.overlap(c, STAGING_CIDR):
                checks.fail(
                    "NT-6",
                    "peering touching the Staging range",
                    f"{pcx} ({status}, seen from {p}): {rvpc} {rcidr} <-> "
                    f"{avpc} {acidr} - there is no peering to Staging, by "
                    "decision (D20).",
                )
    if peers and checks.n_fail("NT-6") == 0:
        n_distinct = len({pr[1] for pr in peers})
        checks.ok(
            "NT-6", f"no peering touches {STAGING_CIDR}", f"{n_distinct} distinct peering(s) read"
        )

    # NT-7: every non-default VPC has a flow log (step 5 is in the same slice as step 1, so
    # a project VPC without one is a slice that half-applied).
    for p, vpc, _c, is_default, _s, _h in vpcs:
        if is_default != "False":
            continue
        if (p, vpc) in flows:
            checks.ok("NT-7", f"flow log on {vpc} ({p})", "present")
        else:
            checks.fail(
                "NT-7",
                f"flow log on {vpc} ({p})",
                "none - step 5 puts one per VPC in the same foundation/ slice, so "
                "a VPC without one is a half-applied slice, and under design B "
                "the flow log is how a dropped packet is seen at all.",
            )

    # NT-8: the four cross-account zone associations of step 4.4, resolved against the
    # single non-default VPC of the Sandbox and Development profiles. If an account has
    # zero or more than one non-default VPC the check says "cannot resolve" rather than
    # guessing.
    zone_names = {z[2] for z in zones}
    for zone in ("prod.internal", "pages.internal"):
        if zone not in zone_names:
            checks.note("NT-8", f"zone {zone}", "not created yet - expected before Stage 3 step 4.")
            continue
        for tp in (SBX_PROFILE, DEV_PROFILE):
            candidates = [
                vpc for p, vpc, _c, is_default, _s, _h in vpcs if p == tp and is_default == "False"
            ]
            tv = candidates[0] if len(candidates) == 1 else ""
            if not tv:
                checks.note(
                    "NT-8",
                    f"{zone} associated with the {tp} VPC",
                    f"cannot resolve: {tp} has zero or several non-default VPCs, "
                    "or was not measured.",
                )
            elif any(zn == zone and zv == tv for _p, zn, zv, _r in zonevpcs):
                checks.ok("NT-8", f"{zone} associated with the {tp} VPC", f"{tv} (step 4.4)")
            else:
                checks.fail(
                    "NT-8",
                    f"{zone} associated with the {tp} VPC",
                    f"{tv} is NOT in the zone's association list - the query for "
                    f"gitlab.{zone} from that VPC returns NXDOMAIN, and over the "
                    "VPN that is 'GitLab is down' (step 4.4).",
                )
    if "sandbox.internal" in zone_names:
        checks.ok(
            "NT-8",
            "zone sandbox.internal exists",
            "associated at creation, no handshake needed (step 4.4)",
        )
    else:
        checks.note(
            "NT-8", "zone sandbox.internal", "not created yet - expected before Stage 3 step 4."
        )

    # NT-9: the private-door premise of 2026-08-24 (PORTAL_FAMILY_BASELINE). A membership
    # change in EITHER direction is a recorded premise moving, so it FAILS loudly rather
    # than noting quietly - red is the signal to re-read, never a network to fix.
    if catalog_read:
        prefix = f"com.amazonaws.{context.REGION}."
        for family, baseline in sorted(PORTAL_FAMILY_BASELINE.items()):
            measured = {
                name[len(prefix) :]
                for name, _stype, _dns in svc_catalog
                if name.startswith(prefix) and catalog_family(name[len(prefix) :]) == family
            }
            if measured == baseline:
                checks.ok(
                    "NT-9",
                    f"catalog family '{family}'",
                    f"exactly {sorted(measured)} - still NO private door for the SMUS "
                    "portal's browser surfaces (section 10); the portal needs public "
                    "egress under every endpoint set.",
                )
            else:
                checks.fail(
                    "NT-9",
                    f"catalog family '{family}'",
                    f"membership MOVED: measured {sorted(measured)}, recorded "
                    f"{sorted(baseline)} - a browser-surface door may have appeared, or "
                    "one was withdrawn. Re-read section 10's premise and architecture.md "
                    "§4.3a before trusting any sentence that leans on the 2026-08-24 "
                    "absence, then move this baseline WITH the re-reading, never alone.",
                )
    else:
        checks.note(
            "NT-9",
            "endpoint-service catalog",
            "unreadable this run (no live profile, or the call failed - section 13): the "
            "private-door premise is UNMEASURED, not confirmed (Lesson 13).",
        )

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("Networking - the [P] foundation half, per account, side by side")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/networking.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. VPCs, and the two DNS attributes of each
  3. Subnets - anchored on the ZONE ID column
  4. Route tables, routes, internet gateways
  5. Gateway endpoints - the [P] anchor (INT-05)
  6. VPC peerings, seen from both sides
  7. Private hosted zones, associations, pending authorizations
  8. Flow logs, and their retention
  9. NACLs and security groups
  10. The endpoint-service catalog - the doors that EXIST for these surfaces
  11. CHECKS
  12. The accounts nothing here is measuring
  13. Calls that failed

HOW TO READ THIS FILE
  - "NO VPC" IS THE EXPECTED ANSWER UNTIL STAGE 3 PASS 1 HAS RUN - except the
    ACCOUNT FACTORY vend artifact, which section 2 and check NT-1 expose and
    which step 0 (settled 2026-08-16) removes via its StackSet on Management.
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT. Section 12 names the ones nothing
    reached - Staging above all, which is UNVENDED and therefore silent.
  - THIS IS A CONTROL-PLANE READING. The behavioural proofs of the stage (dnf
    through the endpoint, NXDOMAIN, the probe reaching GitLab) need the throwaway
    probe instances the stage describes; no describe call substitutes for them.
  - THE [P]-STABILITY DELIVERABLE IS A DIFF OF TWO RUNS: copy this file aside,
    make down + make up, re-run, diff. Only the timestamp may change.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

        # ==============================================================================
        rep.h1("1. Which accounts were measured, and as whom")

        rep.text("""A profile is an (account, permission set) pair; every awsds-* profile here resolves
to the infrastructure user. A `(failed)` row is a profile that did not authenticate,
never a compliant one.

""")
        rep.tabulate(
            ["PROFILE\tACCOUNT\tCALLER ARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )

        # ==============================================================================
        rep.h1("2. VPCs, and the two DNS attributes of each")

        if vpcs:
            rep.tabulate(
                ["PROFILE\tVPC\tCIDR\tDEFAULT\tdnsSupport\tdnsHostnames"]
                + sorted("\t".join(v) for v in vpcs)
            )
            rep.text("""
The DEFAULT column is the Stage 3 preflight: a True row is a VPC nobody in this
project created - public subnets, an attached IGW - and the stage never says what
happens to it (check NT-1). The two DNS columns are step 4.1: aws_vpc defaults
dnsHostnames to FALSE, and everything in step 4 needs both True.""")
        else:
            rep.line("NO VPC IN ANY MEASURED ACCOUNT - including no default VPC.")

        rep.text("""
Secondary CIDR associations, where any exist:

""")
        for p in live:
            rep.h2(p)
            rep.show(
                cli_for(p),
                "ec2",
                "describe-vpcs",
                "--query",
                "Vpcs[?length(CidrBlockAssociationSet) > `1`]"
                ".[VpcId, join(`,`, CidrBlockAssociationSet[].CidrBlock)]",
                "--output",
                "table",
            )

        # ==============================================================================
        rep.h1("3. Subnets - anchored on the ZONE ID column")

        rep.text("""Subnets anchor on zone IDs, never on list position (step 1.5, settled by 1b step 6).
The AZ NAME column is a per-account label; the ZONE ID names the datacenter. Compare
this section against aws/output/AZs.txt when a peering seems slow: two peered subnets
whose zone IDs differ pay USD 0.01/GB each way with no error anywhere.

""")
        for p in live:
            rep.h2(p)
            rep.show(
                cli_for(p),
                "ec2",
                "describe-subnets",
                "--query",
                "sort_by(Subnets,&SubnetId)[].[SubnetId,VpcId,CidrBlock,"
                "AvailabilityZone,AvailabilityZoneId,MapPublicIpOnLaunch,"
                "Tags[?Key==`Name`].Value|[0]]",
                "--output",
                "table",
            )

        # ==============================================================================
        rep.h1("4. Route tables, routes, internet gateways")

        rep.text("""The rows checks NT-3 and NT-4 read. A route whose TARGET is "local" is the VPC
routing to itself and is excluded from NT-3 on purpose. The private tier should show
a 0.0.0.0/0 route ONLY under design A and only while egress/ is up (step 2.2); the
isolated tier should never show one - that is what makes it isolated.

""")

        if routes:
            rep.tabulate(
                ["PROFILE\tROUTE TABLE\tVPC\tDESTINATION\tTARGET\tSTATE"]
                + sorted("\t".join(r) for r in routes)
            )
        else:
            rep.line("(no route table in any measured account)")

        rep.text("""
Internet gateways:

""")
        for p in live:
            rep.h2(p)
            rep.show(
                cli_for(p),
                "ec2",
                "describe-internet-gateways",
                "--query",
                "InternetGateways[].[InternetGatewayId, Attachments[0].VpcId]",
                "--output",
                "table",
            )

        # ==============================================================================
        rep.h1("5. Gateway endpoints - the [P] anchor (INT-05)")

        rep.text("""THESE IDS ARE WHAT STAGE 5 MAY CONDITION ON, AND THE ONLY ENDPOINT IDS THAT MAY BE
NAMED IN ANY POLICY (Lesson 3, step 3.3): they are [P], survive every make down, and
live in the same slice as the VPC. The interface endpoints of egress.py get new IDs
on every make up and may anchor nothing. If a row here CHANGES across a make down /
make up cycle, that is the INT-05 failure mode arriving early - stop and look.

""")

        if gweps:
            rep.tabulate(["PROFILE\tENDPOINT\tSERVICE\tVPC"] + sorted("\t".join(g) for g in gweps))
        else:
            rep.line("(none in any measured account - expected before Stage 3 step 3)")

        # ==============================================================================
        rep.h1("6. VPC peerings, seen from both sides")

        rep.text("""The API answers from both sides, so one healthy peering between two measured
accounts appears TWICE below - same pcx-* id, two PROFILE rows. A peering that
appears under only one measured side is worth a second look. Expected once pass 2
is done: exactly two distinct ids - Sandbox<->Production and Development<->Production
(INT-09) - and nothing touching 10.40.0.0/16 (NT-6, D20).

""")

        if peers:
            rep.tabulate(
                ["PROFILE\tPCX\tSTATUS\tREQ VPC\tREQ CIDR\tACC VPC\tACC CIDR"]
                + sorted("\t".join(pr) for pr in peers)
            )
        else:
            rep.line("(no peering in any measured account - expected before Stage 3 pass 2)")

        # ==============================================================================
        rep.h1("7. Private hosted zones, associations, pending authorizations")

        rep.text("""Step 4.2 creates THREE zones and deliberately not one per account: sandbox.internal
(Sandbox), prod.internal and pages.internal (Production). Development and Staging
get none. The association table is step 4.4: prod.internal and pages.internal must
each reach the Sandbox AND Development VPCs, or gitlab.prod.internal is NXDOMAIN
over the VPN. Check NT-8 resolves it mechanically.

""")

        if zones:
            rep.tabulate(["OWNER PROFILE\tZONE ID\tZONE"] + sorted("\t".join(z) for z in zones))
            rep.text("""
Associated VPCs per zone (owner-side view). The account owning each VPC is
resolved against section 2 where possible:
""")
            rows = ["OWNER\tZONE\tVPC\tREGION\tVPC BELONGS TO"]
            for zp, zn, zv, zr in sorted(set(zonevpcs)):
                owner = next((v[0] for v in vpcs if v[1] == zv), "(not measured here)")
                rows.append(f"{zp}\t{zn}\t{zv}\t{zr}\t{owner}")
            rep.tabulate(rows)
        else:
            rep.line(
                "(no private hosted zone in any measured account - expected before Stage 3 step 4)"
            )

        rep.text("""
Association authorizations, per zone. 4.5 keeps them in state, so a row that ALSO
appears in the association table above is a completed handshake, not a pending one;
a row with NO matching association is the handshake whose second half has not run.
(Documented: an authorization persists until deleted, and a re-created association
after a VPC rebuild needs a fresh one.)

""")
        if zones:
            for zp, zid, zname in zones:
                rep.h2(f"{zname} ({zp})")
                rep.show(
                    cli_for(zp),
                    "route53",
                    "list-vpc-association-authorizations",
                    "--hosted-zone-id",
                    zid,
                    "--query",
                    "VPCs[].[VPCId,VPCRegion]",
                    "--output",
                    "table",
                )
        else:
            rep.line("(no zone to ask about)")

        # ==============================================================================
        rep.h1("8. Flow logs, and their retention")

        for p in live:
            cli = cli_for(p)
            rep.h2(p)
            rep.show(
                cli,
                "ec2",
                "describe-flow-logs",
                "--query",
                "FlowLogs[].[FlowLogId,ResourceId,TrafficType,LogDestinationType,"
                "LogGroupName,DeliverLogsStatus]",
                "--output",
                "table",
            )
            res = cli.run(
                "ec2",
                "describe-flow-logs",
                "--query",
                "FlowLogs[].LogGroupName",
                "--output",
                "text",
                log=False,
            )
            log_groups = sorted({lg for lg in res.text.split() if lg and lg != "None"})
            for lg in log_groups:
                r = cli.run(
                    "logs",
                    "describe-log-groups",
                    "--log-group-name-prefix",
                    lg,
                    "--query",
                    f"logGroups[?logGroupName==`{lg}`].retentionInDays | [0]",
                    "--output",
                    "text",
                    log=False,
                )
                rep.line(f"log group {lg}: retention {r.text or '?'}")
                rep.line()

        rep.text("""Retention is the term that accumulates (step 5.1, settled 2026-08-16: CloudWatch
Logs, 30 days); "None" means NEVER EXPIRE, the one value that cannot be intended here.""")

        rep.text("""
Log groups left behind by the Account Factory stack (the verification (vi)
residual: a group listed here after step 0 ran is what the stack-instance
removal did NOT delete):

""")
        for p in live:
            rep.h2(p)
            rep.show(
                cli_for(p),
                "logs",
                "describe-log-groups",
                "--log-group-name-prefix",
                "StackSet-AWSControlTowerBP",
                "--query",
                "logGroups[].[logGroupName,retentionInDays,storedBytes]",
                "--output",
                "table",
            )

        # ==============================================================================
        rep.h1("9. NACLs and security groups")

        rep.text("""NACLs stay at the default allow, by decision (step 2.3): a False row in the DEFAULT
column below is a stateless deny somebody added, and the fastest way to break a path
nobody can then debug.

""")
        for p in live:
            rep.h2(p)
            rep.show(
                cli_for(p),
                "ec2",
                "describe-network-acls",
                "--query",
                "NetworkAcls[].[NetworkAclId,VpcId,IsDefault,length(Entries)]",
                "--output",
                "table",
            )

        rep.text("""
Security groups, and the subset with an ingress rule open to the world. Wide-open
ingress is a LISTING here, not a failure: from Stage 4 on, exactly one such rule is
expected - UDP 51820 on the WireGuard host SG - and anything beyond it is what this
block exists to make visible (step 6.4: never 0.0.0.0/0 on a peering path).

""")
        for p in live:
            cli = cli_for(p)
            rep.h2(p)
            rep.show(
                cli,
                "ec2",
                "describe-security-groups",
                "--query",
                "SecurityGroups[].[GroupId,GroupName,VpcId]",
                "--output",
                "table",
            )
            rep.line("open to 0.0.0.0/0 or ::/0 (ingress):")
            rep.line()
            rep.show(
                cli,
                "ec2",
                "describe-security-groups",
                "--query",
                "SecurityGroups[?IpPermissions[?IpRanges[?CidrIp==`0.0.0.0/0`] || "
                "Ipv6Ranges[?CidrIpv6==`::/0`]]].[GroupId,GroupName,VpcId]",
                "--output",
                "table",
            )

        # ==============================================================================
        rep.h1("10. The endpoint-service catalog - the doors that EXIST for these surfaces")

        rep.text("""ONE REGIONAL CALL, not a per-account fact: every service AWS offers as an
INTERFACE endpoint here - the OFFER, never the choice. Which door a slice
actually opens is that slice's own list (egress/'s extra_services, the module's
core_services), deliberately not restated here (Lesson 14). egress.py section 7
reads the same API for a different question - which deployed endpoints can
carry a policy (EG-1).

WHERE AN ENTRY BELOW FITS IN A VPC CONFIGURATION. An interface endpoint is the
[E] door egress/ instantiates: under design A it is OPTIONAL beside the NAT,
bought for the trusted-network axis (the org-conditioned endpoint policy, and
aws:SourceVpc in the policies that key on it); under design B it would be the
ONLY path. Its private DNS also OVERRIDES the service's public names for every
VPC-resolver client - the PRIVATE DNS NAME column shows the primary one, and a
deployed endpoint's DnsEntries can seize MORE (datazone also takes
datazone.<region>.api.aws) - authoritatively, for the WHOLE SUBTREE: an
unlisted SUBDOMAIN of a seized name is NXDOMAIN inside the VPC while the
endpoint is up (measured 2026-08-24: agent.datazone.<region>.api.aws, a name
AWS's own network-isolation page lists as PUBLIC-INTERNET-required for the
portal web client).

THE LOAD-BEARING READING IS AN ABSENCE. No entry below - or anywhere in the
catalog - serves the SMUS portal's BROWSER surfaces: the on.aws portal itself,
its CloudFront assets, agent.datazone.<region>.api.aws,
sagemaker-unified-studio.<region>.api.aws. So NO endpoint set reaches the
portal privately, and public egress stays required for it whatever the VPC
configuration (architecture.md §4.3a - the design-B input). The console /
console-static / signin rows are the PRECEDENT, not a dependency: AWS builds
private doors for browser surfaces one at a time (Console Private Access), the
SMUS portal has none yet, and NT-9 pins the families such a door would appear
in so its arrival is a red check, not a surprise.

A row appearing or vanishing here across a make down / make up diff is AWS's
catalog moving, never [P] instability - read it with NT-9, not with the
stability deliverable.

""")

        if catalog_read:
            shown = [
                (name, stype, dns)
                for name, stype, dns in sorted(svc_catalog)
                if any(t in name for t in CATALOG_SURFACES)
            ]
            rep.line(
                f"{len(shown)} of {len(svc_catalog)} services match {'|'.join(CATALOG_SURFACES)}:"
            )
            rep.line()
            rep.tabulate(
                ["SERVICE NAME\tTYPE\tPRIVATE DNS NAME"] + ["\t".join(row) for row in shown]
            )
        else:
            rep.line("(catalog unreadable this run - see section 13; NT-9 is a note, not a pass)")

        # ==============================================================================
        rep.h1("11. CHECKS")

        if nondef == 0:
            rep.text("""NO NON-DEFAULT VPC WAS MEASURED, so most checks below are vacuous rather than
passing (Lesson 13). Before Stage 3 pass 1 that is the expected state, and the
value of this run is section 2 (are there default VPCs?) and section 12.
""")

        rep.checks_table(checks)

        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  NT-1  default and Account Factory VPCs flagged (Lessons 16, 17); a
        project-range VPC in Data Governance (D22) or the canary (D29) FAILs
  NT-2  both DNS attributes on every non-default VPC (step 4.1)
  NT-3  no non-local route overlapping 10.40.0.0/16 (validation 2, D20);
        the 0.0.0.0/0 -> igw/nat internet exit is excluded - it cannot
        deliver into an RFC1918 range
  NT-4  no route overlapping 10.90.0.0/24 anywhere (step 6.5); same exclusion
  NT-5  no CIDR overlap among project VPCs, across accounts (step 1.2);
        172.31.0.0/16 vend artifacts counted once, not pairwise
  NT-6  no peering touching the Staging range (D20, step 6.6)
  NT-7  a flow log on every non-default VPC (step 5)
  NT-8  the four cross-account zone associations of step 4.4
  NT-9  the endpoint-service catalog still offers NO private door for the
        SMUS portal's browser surfaces - family membership vs the 2026-08-24
        baseline (section 10)""")

        # ==============================================================================
        rep.h1("12. The accounts nothing here is measuring")

        rep.text("""Read this BEFORE reading section 11 as a pass.

  - `Staging` has no profile because the account is UNVENDED, held on the account
    cap (Stage 1a). Two Stage 3 deliverables are therefore not runnable from here
    until the vend: its VPC, and the proof that its peering list is EMPTY. NT-3 and
    NT-6 cover the other half - that no measured account routes toward it.
  - Management, Log Archive and Audit hold NO CLI profile, by design (D33/D34).
    None of them gets a Stage 3 VPC; whether they hold a DEFAULT VPC is unmeasured
    here and readable only from CloudShell (`python3 aws/networking.py -`).
  - Every Sandbox beyond the first has no profile until Stage 14 vends it (D35).
  - Data Governance IS measured and should show no VPC at all (D22) - the one
    account where an empty section 2 is the passing answer.""")

        # ==============================================================================
        rep.h1("13. Calls that failed")

        if errors:
            rep.text("""Each entry is a call whose output is missing above. An empty block anywhere else
in this file means the call succeeded and returned nothing.

""")
            rep.line(errors.text())
        else:
            rep.line("None. Every call returned successfully.")

        rep.line()
        rep.line("Regenerate with:  ./aws/networking.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 13)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 11)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
