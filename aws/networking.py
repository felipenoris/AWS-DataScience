#!/usr/bin/env -S uv run --quiet
# networking.py - the [P] networking half, per account, side by side: VPCs (default ones
# flagged), DNS attributes, subnets anchored on zone IDs, route tables and routes, internet
# gateways, the S3/DynamoDB gateway endpoints (the INT-05 anchor), VPC peerings seen from
# both sides, the private hosted zones with their associations and pending authorizations,
# flow logs, NACLs and security groups - plus the regional endpoint-service catalog
# (section 10, NT-9) and the [E] endpoints instantiated from it with the DNS names each
# has seized (section 11, NT-10). The preflight for Stage 3, and the standing regression
# after each of its passes.
#
#   needs:    a live SSO session, the only prerequisite:
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
# It is multi-profile, which aws/INDEX.md admits only for a reason: the subject is a
# per-account fact whose meaning is the comparison between accounts. A CIDR overlap is a
# relation between two VPCs in two accounts, a peering has a requester and an accepter on
# opposite sides of a boundary, and a cross-account zone association exists because one
# account owns the zone and another owns the VPC. Same shape as AZs.py and tf-backends.py,
# and it pays the rule back the same way - section 1 prints the caller ARN of every profile.
#
# What it is for, before and after Stage 3.
#
#   Before Stage 3: what networking already exists. The first run (2026-08-15) measured
#   that every vended account carries an Account Factory VPC (172.31.0.0/16, private-only -
#   docs/AWS_STATE.md C), which step 0 now removes. Principle 4 says private by default;
#   D22 says Data Governance gets no VPC at all. Section 2 answers whether either sentence
#   is true today.
#
#   After each Stage 3 pass: the readings that would otherwise be one console tab per
#   account - validation 2 (no route into 10.40.0.0/16), step 6.5 (10.90.0.0/24 in no
#   route table), step 4.4 (the four zone associations), step 5 (a flow log per VPC),
#   step 4.1 (both DNS attributes on). Each is a check that fails, not a listing to eyeball.
#
# The [P]-stability deliverable is a diff of two runs of this file. Stage 3's lifecycle
# deliverable wants every foundation/ id byte-identical across a make down / make up.
# Run this, copy aws/output/networking.txt aside, cycle, run again, diff:
#
#   cut() { awk '/^# 11\./{s=1} /^# 12\./{s=0} !s' "$1"; }
#   diff <(cut before.txt) <(cut after.txt)
#
# and the only line left that may change is the timestamp. Section 11 is excluded: it is
# the one [E] section in a [P] file, placed here so the seized-DNS-name reading sits beside
# section 10's catalog rather than in egress.py. It moves by design - empty while egress/
# is down, one row per interface endpoint while it is up, with a new vpce-* id on every
# make up. A foundation/ id moving is the finding.
#
# Sections 10 and 11 answer opposite halves of one question and behave oppositely here:
# 10 is regional (AWS's offer, identical whether egress/ is up, down, or never applied -
# only AWS changes it, which is NT-9's job), 11 is this account's instantiation of it.
#
# What it cannot see, stated because an empty listing and a missing account look alike:
#   - The account the Stage 3 deliverable called Staging was never vended - the quota refused
#     it - so "describe-vpc-peering-connections in Staging returns empty" has no account to run
#     in. Today's Staging is Development renamed (Stage 6b, 2026-09-06); it is measured here
#     like any other. Absence from this report is silence, not evidence.
#   - Management, Log Archive and Audit hold no CLI profile by design; their default VPCs
#     (if any) are unmeasured here. None of them is meant to hold a Stage 3 VPC.
#   - This is a control-plane reading. The stage's behavioural proofs - dnf through the
#     gateway endpoint, NXDOMAIN from Staging, the probe reaching GitLab's port - need the
#     throwaway probe instances the stage describes; a describe call proves none of them
#     (Lesson 20).

from __future__ import annotations

import sys
from itertools import combinations

from awslib import cidr, context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.context import short_svc
from awslib.report import Checks, Report, note

OUT_NAME = "networking.txt"

# The profiles step 4.4's association checks resolve against. Profile names are the
# convention aws/INDEX.md documents; if one is renamed, the check reports "cannot resolve"
# rather than failing wrongly.
SBX_PROFILE = "awsds-infra-sandbox-1"
STAGING_PROFILE = "awsds-infra-staging"
DATA_PROFILE = "awsds-infra-data"
CANARY_PROFILE = "awsds-policy-canary"

# The ranges the route checks are about (Stage 3 validation 2 and step 6.5).
#
# 10.40.0.0/16 is unallocated. It was reserved for a `Staging` account this project never vended
# - the quota refused it - and Stage 6b made Staging by renaming `Development`, which has held
# 10.50.0.0/16 since Stage 3 and is peered to Production. Stage 6b step 4.1 says Stage 6c
# consumes the freed range; Stage 6c step 0.2 says 10.40.0.0/16 "is free and stays unallocated",
# and D38's hub is built from 10.30 (the existing VPC, re-labelled), 10.31 and 10.32. The stage
# that has to build it is the one that governs (Lesson 32).
#
# The assertion is about the range, not about any account: nothing should route or peer into a
# range nobody has allocated, and a route that does is either a mistake or an allocation somebody
# made without writing it down. The three checks measure that AWS agrees with
# scripts/tfhygiene/backend.py's allocation table about a range nobody has claimed, which nothing
# else in the estate measures; they need re-pointing only if a later stage allocates 10.40.
UNALLOCATED_CIDR = "10.40.0.0/16"

# D38's hub, and the one VPC allowed to hold a route to the WireGuard client range (NT-4, re-cut
# at 6c step 3.6). An address in a .tf file is a copy; an address in an instrument is a claim
# about the allocation table, which scripts/tfhygiene/backend.py's VPC_CIDRS owns.
HUB_CIDR = "10.31.0.0/16"
WIREGUARD_CIDR = "10.90.0.0/24"

# INT-22's zone matrix, read by NT-12 (6c steps 2.4 and 2.6). Keyed by zone, valued by the VPC
# ranges that must be associated - and by exactly those, because an absent association carries as
# much of the design as a present one: `prod.awsds.internal` is not in Sandbox,
# `awsds-pages.internal` not in Workloads.
#
# Keyed by CIDR and not by Name tag: a range is this estate's identifier for a VPC
# (`scripts/tfhygiene/backend.py`'s allocation table), it is already in this file's readings, and it
# does not move when a Name tag does - which it did at 6c step 1.1, breaking two spokes while every
# id-shaped gate read clean (Lesson 48). The human names are here as comments so a reader can
# compare this table with `docs/NETWORK.md` without a lookup.
INT22_MATRIX = {
    # the apex: every VPC, because it holds the shared names (gitlab, proxy, vpn) and the [E] probes
    "awsds.internal": (
        "10.20.0.0/16",  # Sandbox
        "10.30.0.0/16",  # VPC-SharedServices
        "10.31.0.0/16",  # VPC-Networking
        "10.32.0.0/16",  # VPC-Workloads
        "10.50.0.0/16",  # Staging
    ),
    "sandbox.awsds.internal": ("10.20.0.0/16", "10.31.0.0/16"),  # Sandbox + the hub
    "staging.awsds.internal": ("10.50.0.0/16", "10.31.0.0/16"),  # Staging + the hub
    "prod.awsds.internal": ("10.30.0.0/16", "10.31.0.0/16", "10.32.0.0/16"),  # the three Production
    "awsds-pages.internal": ("10.30.0.0/16", "10.31.0.0/16"),  # where Pages is served and read
}

# The range Control Tower's Account Factory VPC occupies (measured 2026-08-15: every vended
# account carries one - IsDefault=False, three private subnets named aws-controltower-*, no
# IGW, a flow log at 90 days). The project's own address plan is 10.0.0.0/8-based (step
# 1.2), so a VPC in this range is a vend artifact, never one of ours.
AF_CIDR = "172.31.0.0/16"

# NT-9 / section 10: the endpoint-service catalog families whose membership is a recorded
# architectural premise (measured 2026-08-24). The load-bearing fact is an absence: among
# the region's ~569 services, no entry serves the SMUS portal's browser surfaces - the
# on.aws portal itself, its CloudFront assets, agent.datazone.<region>.api.aws,
# sagemaker-unified-studio.<region>.api.aws - so no endpoint set reaches the portal
# privately and public egress stays required for it, served by the client plane's proxied
# egress (architecture.md §4.3; OQ 23) and by neither D5 compute design. An absence cannot
# be listed, so the check pins the families the missing door would appear in: if AWS ships
# one the way it shipped Console Private Access (the console/signin rows of section 10),
# the membership moves and NT-9 goes red - the signal to re-read the client-plane design
# (OQ 23), never a network failure.
PORTAL_FAMILY_BASELINE = {
    "datazone": {"datazone", "datazone-fips"},
    "sagemaker-unified-studio": {"sagemaker-unified-studio-mcp"},
}

# Section 10's display filter: the families the 2026-08-24 hand query grepped for, so the
# rows arrive beside the interpretation.
CATALOG_SURFACES = ("datazone", "sagemaker", "sqlworkbench", "console", "signin")

# NT-10 / section 11: the names AWS's SMUS network-isolation page lists under public internet
# access, in its third table (read 2026-08-24). The page requires these of the portal web
# client while the same page's first table tells you to create the datazone endpoint; the
# collision is what broke the portal on the tunnel.
#
# Only the concrete names are here. The page's wildcard rows (*.sagemaker.aws,
# *.execute-api.<region>.amazonaws.com, *.console.api.aws, *.console.aws.a2z.com,
# *.sagemaker.aws.dev and the CDN ones) are not mechanised: a wildcard required-name cannot
# be tested for shadowing without deciding what it stands for, and a check that needs a
# judgement reports the judgement rather than the fact (Lesson 13). Section 11's prose names
# them so the gap is visible instead of silent.
PORTAL_PUBLIC_NAMES = (
    f"agent.datazone.{context.REGION}.api.aws",
    f"sagemaker-unified-studio.{context.REGION}.api.aws",
    f"monitoring.{context.REGION}.amazonaws.com",
)


def shadow_verdict(required: str, seized: str) -> str | None:
    """How a deployed endpoint's seized name interferes with a public-required name.

    An interface endpoint's private DNS installs a hosted zone that is authoritative for
    the whole subtree of each name it seizes - there is no fall-through to public DNS,
    which gives two distinct breakages:

      SEIZED   the required name is the seized name: it answers privately, and a browser
               outside the VPC path never sees the public service at all.
      SHADOWED the required name is a strict subdomain of a seized name. If the seizure
               carries no wildcard the answer is NXDOMAIN (measured 2026-08-24:
               agent.datazone.<region>.api.aws); with a wildcard it resolves to the
               endpoint, which is the wrong target rather than no target.
    """
    zone = seized[2:] if seized.startswith("*.") else seized
    if required == zone:
        return "SEIZED"
    if required.endswith("." + zone):
        return "SHADOWED"
    return None


def catalog_family(token: str) -> str | None:
    """The PORTAL_FAMILY_BASELINE family a com.amazonaws.<region>.<token> belongs to."""
    for family in PORTAL_FAMILY_BASELINE:
        if token == family or token.startswith(family + "-") or token.startswith(family + "."):
            return family
    return None


def internet_exit_default(dest: str, target: str) -> bool:
    """The catch-all route out to the internet - the shape every public tier carries (2.1).

    0.0.0.0/0 contains every RFC1918 range arithmetically, but an internet exit cannot
    deliver into one: an IGW or NAT forwards to the internet routing table, where 10/8 is
    unroutable. Left in the overlap test, the mandatory public default route keeps NT-3 and
    NT-4 red forever, and a permanently red check is one nobody reads (Lesson 13; first
    tripped on the pass-1 measurement, 2026-08-16). Only exactly this shape is excluded: a
    route naming a guarded range itself, whatever its target, is still flagged, and NT-6
    covers the peering side.
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
    ifeps: list = []  # (p, vpce, service, state, private dns, vpc, [seized names])
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

        # Interface endpoints - the [E] doors terraform-modules/vpc-egress/endpoints.tf
        # instantiates, one per name of core_services + extra_services. egress.py owns the
        # [E] audit of these (one AZ per D9, the org condition, the burn); what is read here
        # is DnsEntries, the public names each deployed endpoint seizes in this VPC's
        # resolver. That is a namespace fact about the VPC, it pairs with section 10's
        # catalog, and it is the mechanism behind the portal breakage of 2026-08-24.
        res = cli.run(
            "ec2",
            "describe-vpc-endpoints",
            "--filters",
            "Name=vpc-endpoint-type,Values=Interface",
            "--query",
            "VpcEndpoints[].[VpcEndpointId,ServiceName,State,PrivateDnsEnabled,VpcId,"
            "join(`,`, DnsEntries[].DnsName)]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "ec2 describe-vpc-endpoints (interface)", res.stderr)
        else:
            for line in res.stdout.splitlines():
                f = line.split("\t")
                if len(f) >= 5 and f[0]:
                    names = f[5] if len(f) > 5 else ""
                    # A vpce-*-prefixed entry is endpoint-specific and seizes no public
                    # name; only the rest override what the VPC resolver answers.
                    seized = sorted(n for n in names.split(",") if n and not n.startswith("vpce-"))
                    ifeps.append((p, f[0], f[1], f[2], f[3], f[4], seized))

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

    # The endpoint-service catalog - regional, not per-account: one call from the first live
    # profile answers for everyone. egress.py section 7 reads the same API for a different
    # question, which services support an endpoint policy (EG-1, an [E]-session concern);
    # this read is a standing premise of the egress design itself, which doors exist for
    # this estate's surfaces. The two are kept apart, each beside the checks it feeds
    # (Lesson 33).
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
    # Lesson 17). Three shapes: a true default VPC (public subnets, an IGW); the Account
    # Factory VPC every vend leaves behind (172.31.0.0/16, private-only); and a
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

    # NT-3: no non-local route whose destination overlaps the unallocated range (validation 2).
    # `local` routes are excluded because a VPC always routes to itself, and the internet-exit
    # default route for the reason internet_exit_default() carries. What is left is a route
    # somebody built into a range the allocation table says belongs to nobody.
    nt3 = 0
    for p, rtb, _vpc, dest, target, state in routes:
        if target == "local" or internet_exit_default(dest, target):
            continue
        if cidr.overlap(dest, UNALLOCATED_CIDR):
            checks.fail(
                "NT-3",
                "route into the unallocated range",
                f"{p} {rtb}: {dest} -> {target} ({state}) overlaps "
                f"{UNALLOCATED_CIDR}, which scripts/tfhygiene/backend.py's CIDRS "
                "table allocates to nobody. Either the route is a mistake or the "
                "range was spent without being written down. No stage plans to allocate "
                "it: 6c step 0.2 keeps it free, and 10.60 is what D38 reserves.",
            )
            nt3 += 1
    if nt3 == 0 and routes:
        n_accounts = len({r[0] for r in routes})
        checks.ok(
            "NT-3",
            f"no non-local route overlaps {UNALLOCATED_CIDR}",
            f"{len(routes)} routes read across {n_accounts} account(s)",
        )

    # NT-4: 10.90.0.0/24 in no route table outside VPC-Networking (Stage 3 step 6.5, re-cut at
    # 6c step 3.6). Peering does no edge-to-edge routing, so a route to the WireGuard client
    # range in a spoke is a route that can never carry a packet.
    #
    # The one exception is inside the hub. Step 4.7 adds `10.90.0.0/24 -> the WireGuard host's
    # ENI` to VPC-Networking's public route table: the tunnel terminates there, and that route is
    # what stops the host masquerading traffic bound for the proxy, which gives the proxy's access
    # log a per-device address without any logging change. Same VPC, so no edge-to-edge routing is
    # involved.
    #
    # The re-cut lands before 4.7 rather than with it: it widens what is allowed, so the check
    # stays green either way, and a check edited in the same sitting as the change it would have
    # failed on is a rubber stamp (Lesson 50).
    #
    # The hub is resolved from a reading rather than from a hard-coded id, and the signal is its
    # CIDR - the one fact in the `vpcs` rows that names the VPC rather than describing it.
    # `scripts/tfhygiene/backend.py`'s VPC_CIDRS allocates 10.31.0.0/16 to (production,
    # networking) and nothing else may hold it: NT-5 measures that no two VPCs overlap, so a
    # second VPC answering to this range fails there rather than mis-identifying the hub here.
    hub_vpc_ids = {v for _p, v, c, _d, _s, _h in vpcs if c == HUB_CIDR}

    nt4 = 0
    for p, rtb, vpc, dest, target, state in routes:
        if internet_exit_default(dest, target):
            continue
        if not cidr.overlap(dest, WIREGUARD_CIDR):
            continue
        if vpc in hub_vpc_ids:
            checks.ok(
                "NT-4",
                f"the one {WIREGUARD_CIDR} route, inside the hub",
                f"{p} {rtb}: {dest} -> {target} ({state}) - VPC-Networking's own, step 4.7's "
                "exception, which is what gives the proxy log a per-device address",
            )
            continue
        checks.fail(
            "NT-4",
            "route touching the WireGuard client range",
            f"{p} {rtb}: {dest} -> {target} ({state}) overlaps "
            f"{WIREGUARD_CIDR} OUTSIDE VPC-Networking - that range is SNATed by the "
            "WireGuard instance and reaches no spoke by design (step 6.5); peering does "
            "no edge-to-edge routing, so this route can never carry a packet.",
        )
        nt4 += 1
    if nt4 == 0 and routes:
        checks.ok(
            "NT-4", f"no route overlaps {WIREGUARD_CIDR} outside the hub", "same read as NT-3"
        )

    # NT-5: pairwise CIDR overlap among project VPCs, across every measured account (1.2:
    # ranges are non-overlapping even between accounts that will never peer). Default and
    # Account Factory VPCs are excluded - they are all 172.31.0.0/16, they never peer, and
    # their overlap rows would bury a real one; their fate is NT-1's question, and they are
    # counted once below.
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

    # NT-6: no peering touches the unallocated range from either side. Same reading as NT-3 one
    # layer up - a peering is how a range nobody allocated acquires a path into this estate.
    for p, pcx, status, rvpc, rcidr, avpc, acidr in sorted(set(peers)):
        for c in (rcidr, acidr):
            if cidr.overlap(c, UNALLOCATED_CIDR):
                checks.fail(
                    "NT-6",
                    "peering touching the unallocated range",
                    f"{pcx} ({status}, seen from {p}): {rvpc} {rcidr} <-> "
                    f"{avpc} {acidr} - that range is allocated to nobody in "
                    "scripts/tfhygiene/backend.py's CIDRS table.",
                )
    if peers and checks.n_fail("NT-6") == 0:
        n_distinct = len({pr[1] for pr in peers})
        checks.ok(
            "NT-6",
            f"no peering touches {UNALLOCATED_CIDR}",
            f"{n_distinct} distinct peering(s) read",
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

    # NT-12 replaces the retired NT-8 (6c step 2.6). NT-8 asked whether `prod.internal` and
    # `pages.internal` reached the two spoke VPCs - four questions about a zone family that no
    # longer exists. Its replacement is INT-22's matrix, five zones against five VPCs, where an
    # absent association carries as much of the design as a present one: `prod.awsds.internal` is
    # not in Sandbox, `awsds-pages.internal` not in Workloads.
    #
    # The check is two-sided. A missing association is a name that NXDOMAINs where somebody
    # expects it; an extra one is a spoke resolving into a plane it was kept out of, which no test
    # of the expected direction would find.
    #
    # The VPCs are resolved by CIDR, not by position: an account with three VPCs (Production has
    # three) cannot be reduced to "its non-default VPC", the assumption NT-8 carried and could
    # carry only while every account had one.
    vpc_by_cidr = {c: vpc for _p, vpc, c, is_default, _s, _h in vpcs if is_default == "False"}
    zone_names = {z[2] for z in zones}
    for zone, want_names in sorted(INT22_MATRIX.items()):
        if zone not in zone_names:
            checks.fail("NT-12", f"zone {zone}", "does not exist - the matrix names it (INT-22)")
            continue
        want = {vpc_by_cidr[c] for c in want_names if c in vpc_by_cidr}
        unresolved = [c for c in want_names if c not in vpc_by_cidr]
        got = {zv for _p, zn, zv, _r in zonevpcs if zn == zone}
        missing = sorted(want - got)
        extra = sorted(got - want)
        if unresolved:
            checks.note(
                "NT-12",
                f"{zone} - the matrix as documented equals the matrix as deployed",
                f"no VPC with range(s) {', '.join(unresolved)} was measured in this run - that account holds no live profile here. Reported rather than assumed.",
            )
        elif missing or extra:
            checks.fail(
                "NT-12",
                f"{zone} - the matrix as documented equals the matrix as deployed",
                (
                    f"MISSING {missing} - a name that NXDOMAINs where the matrix says it resolves. "
                    if missing
                    else ""
                )
                + (
                    f"EXTRA {extra} - a VPC resolving into a plane INT-22 keeps it out of, which is "
                    "the half no expected-direction test would find."
                    if extra
                    else ""
                ),
            )
        else:
            checks.ok(
                "NT-12",
                f"{zone} - the matrix as documented equals the matrix as deployed",
                f"{len(want)} association(s), and no others",
            )

    # NT-9: the private-door premise of 2026-08-24 (PORTAL_FAMILY_BASELINE). A membership
    # change in either direction is a recorded premise moving, so it fails loudly rather
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
            "unreadable this run (no live profile, or the call failed - section 14): the "
            "private-door premise is UNMEASURED, not confirmed (Lesson 13).",
        )

    # NT-10: does any deployed interface endpoint's private DNS take over a name AWS's
    # network-isolation page requires of the portal over the public internet? The 2026-08-24
    # breakage as a check - the half of that reading a describe call can answer, so it never
    # has to be rediscovered from a browser error.
    if not ifeps:
        checks.note(
            "NT-10",
            "portal public names vs deployed endpoints",
            "no interface endpoint is deployed in any measured account - egress/ is [E] "
            "and down, so this check is VACUOUS rather than passing (Lesson 13). It "
            "becomes a real reading only while egress/ is up.",
        )
    else:
        # Which VPC the seizure is in decides the verdict (6c step 6.5). A private zone binds the
        # clients of that VPC's resolver. Until 6c the tunnelled laptop was one of Sandbox's (the
        # 2026-08-24 breakage); under D38 it resolves in VPC-Networking, which holds no interface
        # endpoint, and 6.2 measured both portal names public from the tunnel. A seizure in a
        # compute VPC is design B working - 5.3 requires the datazone endpoint there, and the apps
        # inside are not portal web clients - so only a seizure in the hub is the finding. Written
        # to the final expectation with the discriminator (Lesson 50).
        collisions = [
            (p, ep, svc, required, seized, verdict, vpc)
            for p, ep, svc, _state, privdns, vpc, seized_names in ifeps
            if privdns == "True"
            for required in PORTAL_PUBLIC_NAMES
            for seized in seized_names
            if (verdict := shadow_verdict(required, seized))
        ]
        in_hub = [c for c in collisions if c[6] in hub_vpc_ids]
        in_compute = [c for c in collisions if c[6] not in hub_vpc_ids]
        for p, ep, svc, required, seized, verdict, vpc in in_hub:
            checks.fail(
                "NT-10",
                f"{required} vs {ep} ({short_svc(svc)}, {p}, {vpc})",
                f"{verdict} by the endpoint's seizure of '{seized}' IN THE CLIENT PLANE'S VPC - "
                "AWS's SMUS network-isolation page lists this name under PUBLIC INTERNET ACCESS "
                "for the portal web client, the tunnelled laptop resolves here (D38), and this "
                "endpoint's private DNS is authoritative for its subtree. The fix is the "
                "ENDPOINT (the hub carries none by design), never the DNS firewall allow-list, "
                "which cannot reach a private zone.",
            )
        if in_compute and not in_hub:
            checks.ok(
                "NT-10",
                "portal public names vs deployed endpoints",
                f"{len(in_compute)} seizure(s), all in COMPUTE VPCs ("
                + ", ".join(sorted({f"{c[6]} ({c[0]})" for c in in_compute}))
                + ") - design B working: the endpoint is required there (5.3) and the client "
                "plane resolves in the hub, where none is deployed. The page's WILDCARD rows "
                "are not mechanised (section 11).",
            )
        if not collisions:
            checks.ok(
                "NT-10",
                "portal public names vs deployed endpoints",
                f"{len(PORTAL_PUBLIC_NAMES)} concrete public-required name(s) checked "
                f"against {len(ifeps)} deployed endpoint(s) - none seized or shadowed. "
                "The page's WILDCARD rows are not mechanised (section 11).",
            )

    # NT-11: every active peering has a route on both sides (Stage 6c step 3.7).
    #
    # The reference implementation this project keeps as a comparison has exactly this defect: a
    # peering connection that is `active` and a route table on one side that never learned about
    # it. Nothing describes that as an error - the attachment shows healthy, the CIDRs look right
    # in a diagram, and traffic in one direction dies with no ICMP and no log line. Peering shares
    # an address, never a path (Lesson 44), and the path is this route.
    #
    # The two findings never share a verdict:
    #
    #   declared but not routed   an `active` peering with no route on one side. The normal state
    #                             for the minutes between creating a peering and adding its
    #                             routes, so it is reported with the side named, not as a bare
    #                             count.
    #   routed but not active     a route whose target is a peering that is deleted, failed or
    #                             pending - a blackhole: packets leave and nothing comes back. It
    #                             is the more urgent one, and a single verdict covering both would
    #                             let it hide behind the first.
    #
    # It asserts only about accounts it actually read. A VPC whose account holds no live profile
    # is skipped and said so, because "no route found" and "no session" are the same silence
    # (Lesson 13); this check runs across accounts by construction, so that case is normal rather
    # than exceptional.
    read_vpcs = {v for _p, v, _c, _d, _s, _h in vpcs}
    routed_by_pcx: dict = {}
    for _p, _rtb, vpc, _dest, target, _state in routes:
        if isinstance(target, str) and target.startswith("pcx-"):
            routed_by_pcx.setdefault(target, set()).add(vpc)

    active_pcx: dict = {}  # pcx -> (status, {req vpc, acc vpc})
    for _p, pcx, status, rvpc, _rc, avpc, _ac in peers:
        prev = active_pcx.get(pcx)
        sides = (prev[1] if prev else set()) | {rvpc, avpc}
        active_pcx[pcx] = (status, sides)

    not_routed, blackholes = [], []
    for pcx, (status, sides) in sorted(active_pcx.items()):
        have = routed_by_pcx.get(pcx, set())
        if status != "active":
            if have:
                blackholes.append(
                    f"{pcx} is {status} and {len(have)} route table side(s) still point at it"
                )
            continue
        for side in sorted(sides):
            if side not in read_vpcs:
                continue  # no session on that account - silence here is not a finding
            if side not in have:
                not_routed.append(f"{pcx}: {side} has no route to it")

    for pcx, sides in sorted(routed_by_pcx.items()):
        if pcx not in active_pcx:
            blackholes.append(
                f"{pcx} is routed from {', '.join(sorted(sides))} and no peering by that id was read"
            )

    if blackholes:
        for line in blackholes:
            checks.fail(
                "NT-11",
                "a route points at a peering that is not active",
                f"{line} - packets leave and nothing comes back, with no ICMP and no log "
                "line. This is the opposite of the finding below and the more urgent one.",
            )
    if not_routed:
        for line in not_routed:
            checks.fail(
                "NT-11",
                "an active peering is not routed on both sides",
                f"{line} - peering shares an ADDRESS, never a PATH (Lesson 44), and the "
                "path is this route. Normal for the minutes between creating a peering and "
                "adding its routes; a finding at any other time.",
            )
    if active_pcx and not blackholes and not not_routed:
        n_active = len([1 for s, _ in active_pcx.values() if s == "active"])
        checks.ok(
            "NT-11",
            "every active peering is routed on both sides",
            f"{n_active} active peering(s), both sides routed in every account this run "
            f"could read ({len(read_vpcs)} VPC(s))",
        )
    elif not active_pcx:
        checks.note(
            "NT-11",
            "every active peering is routed on both sides",
            "no peering was read - nothing to check",
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
  11. Interface endpoints - which doors this estate actually opened
  12. CHECKS
  13. The accounts nothing here is measuring
  14. Calls that failed

HOW TO READ THIS FILE
  - "NO VPC" IS THE EXPECTED ANSWER UNTIL STAGE 3 PASS 1 HAS RUN - except the
    ACCOUNT FACTORY vend artifact, which section 2 and check NT-1 expose and
    which step 0 (settled 2026-08-16) removes via its StackSet on Management.
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT. Section 13 names the ones nothing
    reached - Staging above all, which is UNVENDED and therefore silent.
  - THIS IS A CONTROL-PLANE READING. The behavioural proofs of the stage (dnf
    through the endpoint, NXDOMAIN, the probe reaching GitLab) need the throwaway
    probe instances the stage describes; no describe call substitutes for them.
  - THE [P]-STABILITY DELIVERABLE IS A DIFF OF TWO RUNS: copy this file aside,
    make down + make up, re-run, diff with SECTION 11 EXCLUDED - it is the one
    [E] section here and moves by design (empty while egress/ is down, new
    vpce-* ids on every make up). With it out, only the timestamp may change.
    Section 10 is regional and does not move with egress/ at all.

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
is done: exactly two distinct ids - Sandbox<->Production and Staging<->Production
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
(Sandbox), prod.internal and pages.internal (Production) - AND THAT FAMILY IS RETIRED.
6c step 2.6 destroyed the two Production zones on 2026-09-07 and NT-12 replaced NT-8's
four questions with INT-22's whole matrix. What resolves now is one APEX (awsds.internal,
all five VPCs, holding gitlab/proxy/vpn and the [E] probe records), three per-account
child zones, and awsds-pages.internal. `sandbox.internal`, the last of the old family, left
at 6c step 6.5 (2026-09-08) with the apply that unfroze sandbox/foundation; NT-12 reads the
whole matrix, two-sided, with no dated exception left.

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
configuration - the CLIENT plane's egress serves it under the 2026-08-25
re-scope (architecture.md §4.3; OQ 23), never either D5 compute design. The console /
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
        rep.h1("11. Interface endpoints - which doors this estate actually opened")

        rep.text("""SECTION 10 IS THE OFFER; THIS IS THE CHOICE. Every row below is one
aws_vpc_endpoint from terraform-modules/vpc-egress/endpoints.tf, which for_eachs
over concat(core_services, extra_services) with private_dns_enabled = true - the
module's core list plus whatever that account's egress/ slice declares for its own
role. A row here and no matching name in that slice means somebody created an
endpoint by hand.

THESE IDS ANCHOR NOTHING (Lesson 3, INT-05). They are [E]: destroyed by make down
and NEW on every make up, so no policy may name one. Section 5's GATEWAY ids are
the ones that may. A row appearing or vanishing across the [P]-stability diff is
egress/ being up or down, not foundation/ moving.

WHAT THIS SECTION READS THAT egress.py DOES NOT - and the reason it is here rather
than there. egress.py owns the [E] AUDIT of these endpoints: one AZ per D9 (EG-2),
private DNS on (EG-3), the org condition on each policy (EG-1), and the hourly burn.
The column below that neither script carried until 2026-08-25 is SEIZED DNS NAMES -
the public service names each deployed endpoint has taken over IN THIS VPC'S
RESOLVER, read from DnsEntries. That is a fact about the VPC's namespace rather than
about the endpoint's configuration, it is what section 10's PRIVATE DNS NAME column
becomes once instantiated, and it is the mechanism behind the 2026-08-24 portal
breakage. Endpoint-specific vpce-*-prefixed entries are dropped: they seize nothing.

HOW TO READ A SEIZED NAME. The private hosted zone behind it is authoritative for
the WHOLE SUBTREE, with no fall-through to public DNS. So an unlisted SUBDOMAIN of
a seized name is NXDOMAIN for every client of THAT VPC's resolver. Until 6c the
full-tunnel laptop was one of Sandbox's (the 2026-08-24 breakage); under D38 it
resolves in VPC-Networking, which holds no interface endpoint by design, and 6.2
measured both portal names PUBLIC from the tunnel. NT-10 therefore tests the concrete
names AWS's SMUS network-isolation page lists under PUBLIC INTERNET ACCESS against the
CLIENT plane's VPC alone: a seizure in a COMPUTE VPC is design B working (the datazone
endpoint is required there, 5.3), a seizure in the hub is the finding. The page's
WILDCARD rows are NOT mechanised (*.sagemaker.aws, *.execute-api.<region>.
amazonaws.com, *.console.api.aws, *.console.aws.a2z.com, *.sagemaker.aws.dev, the
CDN ones) - testing one needs a judgement about what it stands for, so the gap is
named here instead of hidden inside a check.

""")

        if ifeps:
            rep.tabulate(
                ["PROFILE\tENDPOINT\tSERVICE\tSTATE\tPRIV DNS\tSEIZED DNS NAMES"]
                + sorted(
                    "\t".join([p, ep, short_svc(svc), state, privdns, ", ".join(seized) or "-"])
                    for p, ep, svc, state, privdns, _vpc, seized in ifeps
                )
            )
        else:
            rep.text("""(none in any measured account)

THAT IS THE EXPECTED READING WHILE egress/ IS DOWN, and it is not a passing state -
it is an ABSENT one. NT-10 says so rather than going green: with no endpoint
deployed there is no seizure to collide with anything. It also means the SageMaker
apps in this VPC have no private door and, with no NAT either, no egress at all -
the shape whose symptom is the portal's "Network issue detected ... may be using a
public subnet" banner, which names the wrong cause (measured 2026-08-24: the
subnets are private; what is missing is any exit).
""")

        # ==============================================================================
        rep.h1("12. CHECKS")

        if nondef == 0:
            rep.text("""NO NON-DEFAULT VPC WAS MEASURED, so most checks below are vacuous rather than
passing (Lesson 13). Before Stage 3 pass 1 that is the expected state, and the
value of this run is section 2 (are there default VPCs?) and section 13.
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
  NT-4  no route overlapping 10.90.0.0/24 OUTSIDE VPC-Networking (step 6.5,
        re-cut at 6c step 3.6 - the hub carries the estate's one such route,
        which is what gives the proxy a per-device source); same exclusion
  NT-5  no CIDR overlap among project VPCs, across accounts (step 1.2);
        172.31.0.0/16 vend artifacts counted once, not pairwise
  NT-6  no peering touching the unallocated 10.40/16 range (was D20's Staging range)
  NT-7  a flow log on every non-default VPC (step 5)
  NT-8  the four cross-account zone associations of step 4.4
  NT-9  the endpoint-service catalog still offers NO private door for the
        SMUS portal's browser surfaces - family membership vs the 2026-08-24
        baseline (section 10)
  NT-10 no DEPLOYED interface endpoint seizes or shadows a name AWS's SMUS
        network-isolation page requires over the PUBLIC internet (section 11);
        vacuous while egress/ is down""")

        # ==============================================================================
        rep.h1("13. The accounts nothing here is measuring")

        rep.text("""Read this BEFORE reading section 12 as a pass.

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
        rep.h1("14. Calls that failed")

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
        note(f"wrote {out_label} (some calls FAILED - see section 14)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 12)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
