#!/usr/bin/env -S uv run --quiet
# egress.py - the [E] networking half, per account, side by side: interface endpoints (with
# their AZ count and private-DNS flag), NAT gateways and elastic IPs, every endpoint POLICY
# read against step 9 (the org condition and the AWS-owned-bucket allow-list), the
# service-per-account matrix step 8's lists produce, the hourly burn those resources cost
# RIGHT NOW, and the region's endpoint service-name catalog.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/egress.py                        # every awsds-* profile
#             ./aws/egress.py awsds-infra-prod       # only the ones named
#             python3 aws/egress.py -                # CloudShell, ambient credentials
#   writes:   aws/output/egress.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeVpcEndpoints, DescribeVpcEndpointServices, DescribeNatGateways,
#             DescribeAddresses, DescribeSubnets, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The subject is a
# PER-ACCOUNT fact whose meaning is the comparison BETWEEN accounts: step 8's endpoint list
# is deliberately different per account role, so "is the set right" is only readable with
# the columns side by side - an endpoint present in five accounts and missing in the sixth
# is either the sixth account's gap or the five accounts' waste, and both are the point.
# Section 1 prints the caller ARN of every profile, which is what the one-profile rule
# exists to make visible.
#
# WHAT IT IS FOR, AT THE TWO ENDS OF A SESSION.
#
#   AT make up: did egress/ produce the right set - the per-role lists of step 8, one AZ
#   per endpoint (D9), private DNS on (8.5), and a policy on every endpoint that names the
#   organization (9.1) plus the AWS-owned-bucket allow (9.3). Each is a check that FAILS,
#   not a listing to eyeball - and 9's failure mode in real life is a package manager that
#   HANGS, which no error message will ever attribute to an endpoint policy.
#
#   AT make down - AND WHENEVER IN DOUBT: section 6 is the burn meter. A forgotten egress/
#   costs ~USD 4.08/day and, by decision D12, NO BUDGET ALERT EXISTS to catch it; this
#   section is the manual instrument that risk gets. Zero everywhere is the correct
#   between-sessions answer (D11).
#
#   THE 4.08 IS RE-DERIVED, NOT COPIED (2026-08-21): 12 interface endpoints x 0.010 plus
#   the NAT and its IPv4 at 0.050 = 0.170/h = 4.08/day, at the Sandbox list. It read 4.08
#   here and 3.84 in section 6's own text for four days - the 2026-08-17 commit that
#   removed elasticfilesystem decremented one and not the other - and `datazone` joining
#   at Stage 6 step 4.2 has now made the stale figure accidentally right. Both are stated
#   from the same arithmetic so the next change moves them together (docs/PRICING.md 3).
#
# ONE MORE PREFLIGHT IT CARRIES, before anything is paid for: section 7 lists the region's
# endpoint service names - which answers stage verification (i) (is SageMaker Studio's
# endpoint `aws.sagemaker.<region>.studio` rather than `com.amazonaws.*`?), confirms the
# CodeArtifact pair exists in this region (Lesson 6 found it absent in sa-east-1), and
# records which services support an endpoint POLICY at all, which is what keeps check EG-1
# from failing a service that cannot comply.
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - Staging is UNVENDED and has no profile; every Sandbox beyond the first likewise
#     (Stage 14). Absence from this report is silence, not evidence.
#   - Whether the allow-list of 9.3 is COMPLETE is behavioural: `dnf makecache` from a
#     probe instance with no NAT route is the honest test, and it is the stage's, not this
#     script's. This file proves the statement is PRESENT, never that it is sufficient.
#   - INTERFACE ENDPOINT IDS ARE [E] AND MAY BE NAMED BY NOTHING (Lesson 3, step 8.6):
#     they are new on every make up. The IDs a policy may anchor on are the gateway
#     endpoints in networking.py section 5.

from __future__ import annotations

import re
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, note

OUT_NAME = "egress.txt"

# Hourly rates, from the Stage 3 cost table (measured for docs/PRICING.md, not reasoned -
# Lesson 6; re-measure THERE if these look stale). The NAT figure includes its public IPv4.
RATE_IFEP = 0.010
RATE_NAT = 0.050


def short_svc(svc: str) -> str:
    """com.amazonaws.us-west-2.ecr.api -> ecr.api ; aws.sagemaker.us-west-2.studio ->
    aws.sagemaker.studio"""
    out = svc.replace(f".{context.REGION}", "")
    if out.startswith("com.amazonaws."):
        out = out[len("com.amazonaws.") :]
    return out


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
    ifeps: list = []  # (p, vpce, service, state, nsubnets, az ids, privdns)
    nats: list = []  # (p, nat, state, subnet)
    eppol: list = []  # (p, vpce, service, type, vpc, orgkeys yes/no)
    policies: dict = {}  # (p, ep) -> policy document text
    subnet_az: dict = {}  # p -> {subnet: az id}
    vpc_cidr: dict = {}  # p -> {vpc: cidr}

    for p in live:
        cli = cli_for(p)
        note(f"measuring {p} ...")

        # subnet -> AZ-id map, so each endpoint row can say WHICH datacenter it is in (D9).
        res = cli.run(
            "ec2",
            "describe-subnets",
            "--query",
            "Subnets[].[SubnetId,AvailabilityZoneId]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "ec2 describe-subnets", res.stderr)
            subnet_az[p] = {}
        else:
            subnet_az[p] = dict(
                line.split("\t")[:2] for line in res.stdout.splitlines() if "\t" in line
            )

        # vpc -> CIDR map, so an endpoint inside the Account Factory VPC (172.31.0.0/16,
        # the vend artifact networking.py's NT-1 flags) is judged as an artifact, not as
        # Stage 3's.
        res = cli.run(
            "ec2",
            "describe-vpcs",
            "--query",
            "Vpcs[].[VpcId,CidrBlock]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "ec2 describe-vpcs", res.stderr)
            vpc_cidr[p] = {}
        else:
            vpc_cidr[p] = dict(
                line.split("\t")[:2] for line in res.stdout.splitlines() if "\t" in line
            )

        # every endpoint, both types; policies are fetched per endpoint so a JSON body
        # cannot break the rows.
        res = cli.run(
            "ec2",
            "describe-vpc-endpoints",
            "--query",
            "VpcEndpoints[].[VpcEndpointId,ServiceName,VpcEndpointType,State,"
            "PrivateDnsEnabled,VpcId,join(`,`,SubnetIds)]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "ec2 describe-vpc-endpoints", res.stderr)
            continue
        for line in res.stdout.splitlines():
            f = line.split("\t")
            if len(f) < 7 or not f[0]:
                continue
            ep, svc, ep_type, state, privdns, vpc, subnets = f[:7]
            if ep_type == "Interface":
                nsub = 0
                azids = ""
                if subnets and subnets != "None":
                    subnet_ids = [s for s in subnets.split(",") if s]
                    nsub = len(subnet_ids)
                    azids = ",".join(
                        sorted({subnet_az[p][s] for s in subnet_ids if s in subnet_az[p]})
                    )
                ifeps.append((p, ep, svc, state, str(nsub), azids or "-", privdns))

            r = cli.run(
                "ec2",
                "describe-vpc-endpoints",
                "--vpc-endpoint-ids",
                ep,
                "--query",
                "VpcEndpoints[0].PolicyDocument",
                "--output",
                "text",
                log=False,
            )
            if not r.ok:
                logerr(p, f"ec2 describe-vpc-endpoints --vpc-endpoint-ids {ep} (policy)", r.stderr)
                continue
            policies[(p, ep)] = r.stdout
            orgkeys = "yes" if re.search(r"aws:(Principal|Resource)OrgID", r.stdout) else "no"
            eppol.append((p, ep, svc, ep_type, vpc, orgkeys))

        # NAT gateways - the other metered item, and the design-A switch made flesh.
        res = cli.run(
            "ec2",
            "describe-nat-gateways",
            "--query",
            "NatGateways[].[NatGatewayId,State,SubnetId]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "ec2 describe-nat-gateways", res.stderr)
        else:
            for line in res.stdout.splitlines():
                f = line.split("\t")
                if len(f) >= 3 and f[0]:
                    nats.append((p, f[0], f[1], f[2]))

    # The service-name catalog is regional, not per-account: one call, from the first live
    # profile, answers for everyone.
    catalog_profile = live[0]
    note(f"reading the endpoint service catalog ({catalog_profile}) ...")
    catalog: list = []
    res = cli_for(catalog_profile).run(
        "ec2",
        "describe-vpc-endpoint-services",
        "--query",
        "ServiceDetails[].[ServiceName,ServiceType[0].ServiceType,"
        "VpcEndpointPolicySupported,PrivateDnsName || `-`]",
        "--output",
        "text",
        log=False,
    )
    if not res.ok:
        logerr(catalog_profile, "ec2 describe-vpc-endpoint-services", res.stderr)
    else:
        catalog = sorted(ln for ln in res.stdout.splitlines() if ln)

    def pol_supported(svc: str) -> str:
        """Does this service support an endpoint policy? Empty answer means "not in the
        catalog", which EG-1 treats as supported rather than silently skipping (fail-open
        to visibility)."""
        for line in catalog:
            f = line.split("\t")
            if f and f[0] == svc:
                return f[2] if len(f) > 2 else ""
        return ""

    # ------------------------------------------------------------------------------- checks

    def af_endpoint(p: str, vpc: str) -> bool:
        """Is this endpoint's VPC the Account Factory vend artifact (172.31.0.0/16)? Those
        VPCs and their endpoints predate Stage 3, are flagged by networking.py NT-1, and
        must not read as Stage 3's own step 9 failing."""
        return vpc_cidr.get(p, {}).get(vpc, "").startswith("172.31.")

    # EG-1: every endpoint whose service supports a policy carries one naming the
    # organization (9.1) - binding to the CONDITION KEYS, not to a Sid, because the
    # statement's name is the author's and the condition is the control (Lesson 23).
    for p, ep, svc, ep_type, vpc, orgkeys in eppol:
        if af_endpoint(p, vpc):
            checks.note(
                "EG-1",
                f"org condition on {ep} ({short_svc(svc)}, {p})",
                f"policy is {orgkeys}-org - but this endpoint sits in the Account "
                f"Factory VPC ({vpc}), a vend artifact that predates Stage 3 "
                "(networking.py NT-1). It goes with that VPC in step 0's "
                "stack-instance removal, and is not a step 9 failure.",
            )
            continue
        sup = pol_supported(svc)
        if sup == "False":
            checks.note(
                "EG-1",
                f"org condition on {ep} ({short_svc(svc)}, {p})",
                "this service does not support endpoint policies (catalog, "
                "section 7) - the default full-access document cannot be "
                "replaced, so the perimeter for it rests on the other two axes.",
            )
        elif orgkeys == "yes":
            checks.ok(
                "EG-1",
                f"org condition on {ep} ({short_svc(svc)}, {p})",
                "aws:PrincipalOrgID/aws:ResourceOrgID present",
            )
        else:
            checks.fail(
                "EG-1",
                f"org condition on {ep} ({short_svc(svc)}, {p})",
                "policy names NEITHER aws:PrincipalOrgID NOR aws:ResourceOrgID - "
                f"without it this endpoint is a private, unlogged path to ANY "
                f"{ep_type} destination on the internet (step 9.1).",
            )

    # EG-2: one AZ per interface endpoint (D9) - two subnets doubles the largest hourly
    # item.
    for p, ep, svc, _state, nsub, azids, _privdns in ifeps:
        if int(nsub) <= 1:
            checks.ok(
                "EG-2", f"single AZ on {ep} ({short_svc(svc)}, {p})", f"subnets={nsub} az={azids}"
            )
        else:
            checks.fail(
                "EG-2",
                f"single AZ on {ep} ({short_svc(svc)}, {p})",
                f"{nsub} subnets ({azids}) - D9 says one AZ per endpoint; the "
                "second doubles the hourly cost and a resource in the other AZ "
                "still resolves and reaches it.",
            )

    # EG-3: private DNS on every interface endpoint (8.5) - without it the SDK keeps
    # resolving the public name and the endpoint sits unused.
    for p, ep, svc, _state, _nsub, _azids, privdns in ifeps:
        if privdns == "True":
            checks.ok("EG-3", f"private DNS on {ep} ({short_svc(svc)}, {p})", "enabled")
        else:
            checks.fail(
                "EG-3",
                f"private DNS on {ep} ({short_svc(svc)}, {p})",
                f"PrivateDnsEnabled={privdns} - step 8.5 wants it on (which "
                "itself needs step 4.1's VPC attributes); off, clients resolve "
                "the public name and the endpoint answers nothing.",
            )

    # EG-4: the S3 GATEWAY policy carries the AWS-owned-bucket allow (9.3). PRESENCE only -
    # whether the list is COMPLETE is the stage's dnf probe, not a scan. Account Factory
    # endpoints are EG-1's note, not this check's subject.
    for p, ep, svc, ep_type, vpc, _orgkeys in eppol:
        if ep_type != "Gateway" or not svc.endswith(".s3"):
            continue
        if af_endpoint(p, vpc):
            continue
        pol = policies.get((p, ep), "")
        if not pol:
            continue
        # ONE PATTERN PER FAMILY OF 9.3, and every family gets one - added 2026-08-16, on
        # the first measurement of a real egress/: the table had no pattern for ECR layer
        # storage, so the policy's `prod-<region>-starport-layer-bucket` entry was present
        # in the document, invisible to this check, and would have stayed "pass" the day
        # somebody deleted it (Lesson 13 - a check whose output is the same either way).
        # That family is the one 9.3 calls the entry the step was missing, and it fails
        # AFTER a successful ECR login, pointing at S3 rather than at ECR.
        hits = ""
        if "al2023-repos" in pol:
            hits += "al2023 "
        if re.search("sagemaker", pol, re.IGNORECASE):
            hits += "sagemaker "
        if re.search("(amazon-ssm|aws-ssm|ssm-agent)", pol, re.IGNORECASE):
            hits += "ssm "
        if re.search("amazoncloudwatch-agent", pol, re.IGNORECASE):
            hits += "cloudwatch-agent "
        if re.search("starport-layer-bucket", pol, re.IGNORECASE):
            hits += "ecr-layers "
        if "al2023" in hits:
            checks.ok(
                "EG-4",
                f"AWS-owned bucket allow on {ep} ({p})",
                f"statement present; bucket classes matched: {hits}(completeness is "
                "the stage's dnf probe, not this grep)",
            )
        else:
            checks.fail(
                "EG-4",
                f"AWS-owned bucket allow on {ep} ({p})",
                "no al2023-repos allow in the S3 gateway policy - "
                "aws:ResourceOrgID denies AWS's own buckets, so dnf and every "
                "package install HANGS rather than erroring (step 9.3, 9.4). "
                f"Classes matched so far: {hits or 'none'}",
            )

    # EG-5 (never a failure): the burn meter.
    total_ifep = sum(1 for row in ifeps if row[3] == "available")
    total_nat = sum(1 for row in nats if row[2] in ("available", "pending"))
    total_hourly = total_ifep * RATE_IFEP + total_nat * RATE_NAT
    if total_ifep == 0 and total_nat == 0:
        checks.note(
            "EG-5",
            "metered egress alive",
            "none - the correct between-sessions state (D11), and the expected "
            "one before Stage 3 pass 3.",
        )
    else:
        checks.note(
            "EG-5",
            "metered egress alive",
            f"{total_ifep} interface endpoint(s) + {total_nat} NAT(s) = ~USD "
            f"{total_hourly:.3f}/h ({total_hourly * 24:.2f}/day). If no session "
            "is running, this is the forgotten-egress risk - no budget alert "
            "exists to catch it (D12).",
        )

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("Egress - the [E] networking half, per account, side by side")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/egress.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. Interface endpoints, per account
  3. NAT gateways and elastic IPs
  4. Endpoint policies - the trusted-networks axis (step 9)
  5. The endpoint matrix - service x account (step 8)
  6. The burn meter - what metered egress costs right now (the D12 instrument)
  7. The service-name catalog - verification (i), policy support
  8. CHECKS
  9. The accounts nothing here is measuring
  10. Calls that failed

HOW TO READ THIS FILE
  - EVERYTHING HERE IS [E]: new IDs on every make up, and nothing may anchor on
    them (Lesson 3, step 8.6). The [P] IDs a policy may name are networking.py
    section 5. An EMPTY report between sessions is the system working (D11).
  - THE CHECKS PROVE PRESENCE, NOT SUFFICIENCY. EG-4 sees that the 9.3 allow-list
    EXISTS; only the stage`s no-NAT dnf probe shows it is COMPLETE. Both halves
    matter and neither substitutes (deliverables, Lesson 13).
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT - section 9, Staging above all.

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
        rep.h1("2. Interface endpoints, per account")

        if ifeps:
            rep.tabulate(
                ["PROFILE\tENDPOINT\tSERVICE\tSTATE\tSUBNETS\tAZ IDS\tPRIV DNS"]
                + [
                    f"{p}\t{ep}\t{short_svc(svc)}\t{state}\t{nsub}\t{azids}\t{privdns}"
                    for p, ep, svc, state, nsub, azids, privdns in sorted(ifeps)
                ]
            )
            rep.text("""
SUBNETS should read 1 everywhere (D9, check EG-2) and the AZ IDS column says which
datacenter; PRIV DNS should read True (8.5, check EG-3).""")
        else:
            rep.text("""NONE IN ANY MEASURED ACCOUNT - the correct answer between sessions (D11) and
before Stage 3 pass 3. The report is then worth its sections 6 and 7.""")

        # ==============================================================================
        rep.h1("3. NAT gateways and elastic IPs")

        rep.text("""A NAT exists only under design A (step 7.2) and only while egress/ is up. The
elastic-address listing is informational: Stage 4 parks the WireGuard EIP as [P],
and an address associated with nothing still bills.

""")

        if nats:
            rep.tabulate(["PROFILE\tNAT\tSTATE\tSUBNET"] + sorted("\t".join(n) for n in nats))
        else:
            rep.line("(no NAT gateway in any measured account)")

        rep.text("""
Elastic addresses:

""")
        for p in live:
            rep.h2(p)
            rep.show(
                cli_for(p),
                "ec2",
                "describe-addresses",
                "--query",
                "Addresses[].[AllocationId,PublicIp,"
                "AssociationId || `(NOT ASSOCIATED - still billing)`]",
                "--output",
                "table",
            )

        # ==============================================================================
        rep.h1("4. Endpoint policies - the trusted-networks axis (step 9)")

        rep.text("""One row per endpoint, BOTH types: does its policy name the organization? Check EG-1
reads this table. The S3 GATEWAY policy - the single most consequential policy in
the stage (step 3.4) - is printed in full below it, because its allow-list is the
statement most likely to be trimmed by somebody tidying up (step 9.5).

""")

        if eppol:
            rep.tabulate(
                ["PROFILE\tENDPOINT\tSERVICE\tTYPE\tVPC\tORG CONDITION"]
                + [
                    f"{p}\t{ep}\t{short_svc(svc)}\t{t}\t{vpc}\t{orgkeys}"
                    for p, ep, svc, t, vpc, orgkeys in sorted(eppol)
                ]
            )
            rep.line()
            rep.line("The S3 gateway endpoint policies, in full:")
            for p, ep, svc, t, _vpc, _o in eppol:
                if t != "Gateway" or not svc.endswith(".s3"):
                    continue
                rep.h2(f"{ep} ({p})")
                pol = policies.get((p, ep), "")
                if pol:
                    rep.line(pol)
                    rep.line()
                else:
                    rep.line("(policy not readable - see section 10)")
        else:
            rep.line("(no endpoint in any measured account - expected before Stage 3 step 3)")

        # ==============================================================================
        rep.h1("5. The endpoint matrix - service x account (step 8)")

        rep.text("""Step 8`s list is deliberately per account role - the common core of 8.2 plus the
per-role adds of 8.3 - and it is a MODULE VARIABLE, so this matrix is read against
the stage file rather than against a copy here (a list maintained in two places is
Lesson 14). A row present where the plan says absent is an hourly charge nobody
chose; a row absent where the plan says present is, under design B, a data plane
that cannot execute a single query (8.2).

""")

        if ifeps:
            services = sorted({row[2] for row in ifeps})
            rows = ["SERVICE" + "".join(f"\t{p}" for p in live)]
            for s in services:
                cells = "".join(
                    "\tx" if any(r[0] == p and r[2] == s for r in ifeps) else "\t-" for p in live
                )
                rows.append(short_svc(s) + cells)
            rep.tabulate(rows)
        else:
            rep.line("(nothing to tabulate)")

        # ==============================================================================
        rep.h1("6. The burn meter - what metered egress costs right now")

        rep.text(f"""THE ONE SECTION TO READ AT THE END OF A SESSION. A forgotten egress/ costs ~USD
4.08/day at the Sandbox list, and BY DECISION no budget alert exists to catch it
(D12) - this reading is the instrument that risk gets. Rates: interface endpoint
USD {RATE_IFEP:.3f}/h, NAT (with its IPv4) USD {RATE_NAT:.3f}/h; data-processing charges are on top and
not visible here.

""")

        rows = ["PROFILE\tIF ENDPOINTS\tNATs\tUSD/HOUR"]
        for p in live:
            ne = sum(1 for r in ifeps if r[0] == p and r[3] == "available")
            nn = sum(1 for n in nats if n[0] == p and n[2] in ("available", "pending"))
            rows.append(f"{p}\t{ne}\t{nn}\t{ne * RATE_IFEP + nn * RATE_NAT:.3f}")
        rows.append(f"TOTAL\t{total_ifep}\t{total_nat}\t{total_hourly:.3f}")
        rep.tabulate(rows)

        rep.text("""
Zero everywhere is the correct between-sessions answer (D11), not an absence of
evidence - and the Sandbox row multiplies per business unit (D35).""")

        # ==============================================================================
        rep.h1("7. The service-name catalog - verification (i), policy support")

        rep.text(f"""Read-only answers to questions the stage would otherwise pay to discover:
  - verification (i): the SageMaker Studio endpoint`s service name - the rows below
    matching "studio" settle whether it is aws.sagemaker.{context.REGION}.studio.
  - the CodeArtifact pair exists in this region at all (8.4; Lesson 6 caught it
    absent in sa-east-1 - measured, not assumed).
  - POLICY column False = the service cannot carry an endpoint policy, which is why
    EG-1 reports it as a note rather than a failure.

""")

        if catalog:
            rep.line("The rows the stage names (steps 8.2-8.4, 8.7), plus s3/dynamodb - plus")
            rep.line("elasticfilesystem, on no step-8 list since 2026-08-17 (D24 withdrawn)")
            rep.line("but kept in view, so its absence from the lists reads as a choice:")
            rep.line()
            stage_rx = re.compile(
                "(sagemaker|codeartifact|datazone|athena|glue|lakeformation|"
                "elasticfilesystem|ecr|kms|logs|sts|states|scheduler|ssm|secretsmanager|"
                "monitoring|s3|dynamodb)",
                re.IGNORECASE,
            )
            rep.tabulate(
                ["SERVICE\tTYPE\tPOLICY\tPRIVATE DNS NAME"]
                + [ln for ln in catalog if stage_rx.search(ln)]
            )
            rep.line()
            rep.line('Every row matching "studio", whatever its prefix (verification (i)):')
            rep.line()
            studio = [ln for ln in catalog if re.search("studio", ln, re.IGNORECASE)]
            if studio:
                rep.tabulate(studio)
            else:
                rep.line(
                    "(none - the studio endpoint does not exist in this region under any name)"
                )
            rep.line()
            rep.line(f"The full catalog holds {len(catalog)} services; regenerate to re-read it.")
        else:
            rep.line("(the catalog call failed - see section 10)")

        # ==============================================================================
        rep.h1("8. CHECKS")

        if not ifeps and not eppol:
            rep.text("""NO ENDPOINT WAS MEASURED, so EG-1 through EG-4 are vacuous rather than passing
(Lesson 13). Between sessions and before Stage 3 pass 3 that is the expected
state; EG-5 below is the reading that still means something.
""")

        rep.checks_table(checks)

        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  EG-1  every endpoint policy names the organization (step 9.1); services that
        cannot carry a policy are notes, per the catalog
  EG-2  one AZ per interface endpoint (D9)
  EG-3  private DNS enabled per interface endpoint (step 8.5)
  EG-4  the S3 gateway policy carries the al2023 allow (step 9.3) - presence only
  EG-5  the burn meter (always a note, never a failure)""")

        # ==============================================================================
        rep.h1("9. The accounts nothing here is measuring")

        rep.text("""Read this BEFORE reading section 8 as a pass.

  - `Staging` has no profile because the account is UNVENDED, held on the account
    cap (Stage 1a). Its endpoint list (8.3: no sagemaker.studio, NO lakeformation)
    is unmeasurable until the vend.
  - Management, Log Archive and Audit hold NO CLI profile, by design (D33/D34),
    and none of them gets an egress/ slice.
  - Every Sandbox beyond the first has no profile until Stage 14 vends it (D35).
  - Data Governance IS measured and should show NOTHING here: no VPC (D22), so no
    endpoint and no NAT - its consumers bring their own endpoints.""")

        # ==============================================================================
        rep.h1("10. Calls that failed")

        if errors:
            rep.text("""Each entry is a call whose output is missing above. An empty block anywhere else
in this file means the call succeeded and returned nothing.

""")
            rep.line(errors.text())
        else:
            rep.line("None. Every call returned successfully.")

        rep.line()
        rep.line("Regenerate with:  ./aws/egress.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 10)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 8)")
        return 2
    note(f"wrote {out_label} (all checks passed - and read EG-5, the burn meter)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
