#!/usr/bin/env -S uv run --quiet
# vpn.py - Stage 4's evidence, per account, side by side: the WireGuard host ([D]) and its
# IMDS setting, the Elastic IP, the one world-open security-group rule and the host-key
# secret ([P] anchors - the secret must carry its value-read deny and keep rotation OFF),
# the handshake log and health alarm, WHICH permission sets carry the control-plane deny of
# step 8 (read back from Identity Center, never assumed), and the GuardDuty state - detector
# per account, delegated administrator, and the two paid add-ons that must still be OFF.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/vpn.py                        # every awsds-* profile
#             ./aws/vpn.py awsds-infra-sandbox-1  # only the ones named
#             python3 aws/vpn.py -                # CloudShell, ambient credentials
#   writes:   aws/output/vpn.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeInstances, DescribeAddresses, DescribeSecurityGroups,
#             logs:DescribeLogGroups, cloudwatch:DescribeAlarms,
#             secretsmanager:ListSecrets, GetResourcePolicy,
#             guardduty:ListDetectors, GetDetector,
#             sso-admin:ListInstances, ListPermissionSets, DescribePermissionSet,
#             GetInlinePolicyForPermissionSet,
#             organizations:ListDelegatedAdministrators, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. Two of the
# subjects are facts ACROSS accounts: GuardDuty's whole point is org-wide coverage, so "the
# detector is enabled" is only meaningful read in every account side by side - one account
# silently uncovered is exactly the finding; and the step 8 deny lives in the IDENTITY
# account's permission sets while the Elastic IP it names lives in the VPN home, so the two
# halves of one control sit in two accounts by design. Section 1 pays the rule back with
# the caller ARN of every profile.
#
# FOUR CONTRACTS THIS FILE READS, each named in the stage file so a rename fails loudly:
#   - the instance Name tag matches awsds-*-vpn (Stage 4 step 1.1)
#   - the deny statement's Sid is DenyControlPlaneOffVpn (Stage 4 step 8.1)
#   - the host-key secret's name ends in -vpn-host-key (Stage 4 step 2.2a)
#   - its resource policy's Sid is DenyValueReadExceptHostAndInfrastructure (2.2a)
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - The behavioural proofs - the tunnel pair, the control-plane deny pair, the
#     on-behalf carve-out - are the stage's own, run from the laptop with the tunnel up
#     and down. A describe call proves none of them (Lesson 20).
#   - Whether the deny actually gates the Unified Studio portal is INT-16 and is answered
#     by opening the portal, not by reading a policy.
#   - Management, Log Archive and Audit hold no CLI profile; GuardDuty's org configuration
#     in Audit is read only as far as the delegation registration visible from Identity.

from __future__ import annotations

import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "vpn.txt"

# The VPN home is a ROLE an account plays (D35, Stage 4's forward constraint); unit 1's
# Sandbox plays it today. Stage 14 revisits the topology; this constant moves with it.
VPN_HOME_PROFILE = "awsds-infra-sandbox-1"
IDENTITY_PROFILE = "awsds-infra-identity"

# The contracts (see header).
NAME_TAG_PATTERN = "awsds-*-vpn"
DENY_SID = "DenyControlPlaneOffVpn"
HOST_KEY_SECRET_SUFFIX = "-vpn-host-key"
HOST_KEY_DENY_SID = "DenyValueReadExceptHostAndInfrastructure"

# The six persona sets the step 8 fragment reaches, and the one it deliberately does not
# (8.2/8.3). Control Tower's own sets are ignored entirely.
PERSONA_SETS = (
    "DataScientistAccess",
    "DataScientistStagingAccess",
    "DataScientistProdAccess",
    "DeploymentManagerAccess",
    "GovernanceManagerAccess",
    "DevEnvStewardAccess",
)
INFRA_SET = "InfrastructureAccess"

# The two GuardDuty features Stage 11 step 4 decides against a real bill; until then they
# must read DISABLED (Stage 4 step 10.3).
DEFERRED_FEATURES = ("S3_DATA_EVENTS", "EBS_MALWARE_PROTECTION")


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

    # ------------------------------------------------------------------- GuardDuty, per account
    gd_rows: list = []  # (profile, detector id or '-', status, deferred-feature summary)
    for p in live:
        cli = cli_for(p)
        note(f"measuring {p} ...")
        res = cli.run(
            "guardduty",
            "list-detectors",
            "--query",
            "DetectorIds[0]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(p, "guardduty list-detectors", res.stderr)
            gd_rows.append((p, "-", "(call failed)", "-"))
            continue
        det = res.stdout.strip()
        if not det or det == "None":
            gd_rows.append((p, "-", "no detector", "-"))
            continue
        r = cli.run(
            "guardduty", "get-detector", "--detector-id", det, "--output", "json", log=False
        )
        if not r.ok:
            logerr(p, f"guardduty get-detector {det}", r.stderr)
            gd_rows.append((p, det, "(call failed)", "-"))
            continue
        doc = json.loads(r.stdout or "{}")
        status = doc.get("Status", "?")
        feat = {f.get("Name"): f.get("Status") for f in doc.get("Features", [])}
        deferred = " ".join(f"{n}={feat.get(n, 'absent')}" for n in DEFERRED_FEATURES)
        gd_rows.append((p, det, status, deferred))

    # ------------------------------------------------------- the VPN home: host, EIP, SG, alarm
    home_live = VPN_HOME_PROFILE in live
    instances: list = []  # (id, type, state, subnet, public ip, http tokens, sg ids)
    addresses: list = []  # (allocation id, public ip, instance id or '-')
    world_open: list = []  # (sg id, sg name, proto, from, to)
    log_groups: list = []  # (name, retention)
    alarms: list = []  # (name, state)
    host_key_secrets: list = []  # (name, rotation enabled, value-read deny: yes/no/(call failed))
    if home_live:
        cli = cli_for(VPN_HOME_PROFILE)
        res = cli.run(
            "ec2",
            "describe-instances",
            "--filters",
            f"Name=tag:Name,Values={NAME_TAG_PATTERN}",
            "Name=instance-state-name,Values=pending,running,stopping,stopped",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(VPN_HOME_PROFILE, "ec2 describe-instances", res.stderr)
        else:
            doc = json.loads(res.stdout or "{}")
            for resv in doc.get("Reservations", []):
                for inst in resv.get("Instances", []):
                    instances.append(
                        (
                            inst.get("InstanceId", "?"),
                            inst.get("InstanceType", "?"),
                            inst.get("State", {}).get("Name", "?"),
                            inst.get("SubnetId", "-"),
                            inst.get("PublicIpAddress", "-"),
                            inst.get("MetadataOptions", {}).get("HttpTokens", "?"),
                            [g.get("GroupId") for g in inst.get("SecurityGroups", [])],
                        )
                    )

        res = cli.run(
            "ec2",
            "describe-addresses",
            "--query",
            "Addresses[].[AllocationId,PublicIp,InstanceId]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(VPN_HOME_PROFILE, "ec2 describe-addresses", res.stderr)
        else:
            for line in res.stdout.splitlines():
                f = line.split("\t")
                if len(f) >= 3 and f[0]:
                    addresses.append((f[0], f[1], f[2] if f[2] != "None" else "-"))

        res = cli.run("ec2", "describe-security-groups", "--output", "json", log=False)
        if not res.ok:
            logerr(VPN_HOME_PROFILE, "ec2 describe-security-groups", res.stderr)
        else:
            doc = json.loads(res.stdout or "{}")
            for sg in doc.get("SecurityGroups", []):
                for perm in sg.get("IpPermissions", []):
                    open_v4 = any(r.get("CidrIp") == "0.0.0.0/0" for r in perm.get("IpRanges", []))
                    open_v6 = any(r.get("CidrIpv6") == "::/0" for r in perm.get("Ipv6Ranges", []))
                    if open_v4 or open_v6:
                        world_open.append(
                            (
                                sg.get("GroupId", "?"),
                                sg.get("GroupName", "?"),
                                perm.get("IpProtocol", "?"),
                                str(perm.get("FromPort", "-")),
                                str(perm.get("ToPort", "-")),
                            )
                        )

        res = cli.run(
            "logs",
            "describe-log-groups",
            "--log-group-name-prefix",
            "/awsds/",
            "--query",
            "logGroups[].[logGroupName,retentionInDays]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(VPN_HOME_PROFILE, "logs describe-log-groups", res.stderr)
        else:
            for line in res.stdout.splitlines():
                f = line.split("\t")
                if len(f) >= 2 and f[0] and "vpn" in f[0]:
                    log_groups.append((f[0], f[1]))

        res = cli.run(
            "cloudwatch",
            "describe-alarms",
            "--alarm-name-prefix",
            "awsds-",
            "--query",
            "MetricAlarms[].[AlarmName,StateValue]",
            "--output",
            "text",
            log=False,
        )
        if not res.ok:
            logerr(VPN_HOME_PROFILE, "cloudwatch describe-alarms", res.stderr)
        else:
            for line in res.stdout.splitlines():
                f = line.split("\t")
                if len(f) >= 2 and f[0] and "vpn" in f[0]:
                    alarms.append((f[0], f[1]))

        # The [P] host-key secret (step 2.2a; decision 4, third review). ListSecrets carries
        # the rotation flag; the resource policy is a second read per match. Matched by NAME,
        # like the instance's Name tag above: the name is the documented contract.
        res = cli.run(
            "secretsmanager",
            "list-secrets",
            "--query",
            "SecretList[].[Name,ARN,RotationEnabled]",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(VPN_HOME_PROFILE, "secretsmanager list-secrets", res.stderr)
        else:
            for name, arn, rot in json.loads(res.stdout or "[]"):
                if not (name.startswith("awsds-") and name.endswith(HOST_KEY_SECRET_SUFFIX)):
                    continue
                r = cli.run(
                    "secretsmanager",
                    "get-resource-policy",
                    "--secret-id",
                    arn,
                    "--query",
                    "ResourcePolicy",
                    "--output",
                    "text",
                    log=False,
                )
                if not r.ok:
                    logerr(VPN_HOME_PROFILE, f"get-resource-policy ({name})", r.stderr)
                    deny = "(call failed)"
                else:
                    deny = "yes" if HOST_KEY_DENY_SID in r.stdout else "no"
                host_key_secrets.append((name, bool(rot), deny))

    # ------------------------------------------- the step 8 deny, read back from Identity Center
    identity_live = IDENTITY_PROFILE in live
    set_rows: list = []  # (set name, carries sid: yes/no/(no inline policy))
    if identity_live:
        cli = cli_for(IDENTITY_PROFILE)
        note(f"reading permission sets through {IDENTITY_PROFILE} ...")
        res = cli.run(
            "sso-admin",
            "list-instances",
            "--query",
            "Instances[0].InstanceArn",
            "--output",
            "text",
            log=False,
        )
        inst_arn = res.stdout.strip() if res.ok else ""
        if not res.ok:
            logerr(IDENTITY_PROFILE, "sso-admin list-instances", res.stderr)
        if inst_arn and inst_arn != "None":
            res = cli.run(
                "sso-admin",
                "list-permission-sets",
                "--instance-arn",
                inst_arn,
                "--query",
                "PermissionSets[]",
                "--output",
                "text",
                log=False,
            )
            if not res.ok:
                logerr(IDENTITY_PROFILE, "sso-admin list-permission-sets", res.stderr)
            arns = res.stdout.split() if res.ok else []
            wanted = set(PERSONA_SETS) | {INFRA_SET}
            for arn in arns:
                r = cli.run(
                    "sso-admin",
                    "describe-permission-set",
                    "--instance-arn",
                    inst_arn,
                    "--permission-set-arn",
                    arn,
                    "--query",
                    "PermissionSet.Name",
                    "--output",
                    "text",
                    log=False,
                )
                name = r.stdout.strip() if r.ok else ""
                if name not in wanted:
                    continue
                r = cli.run(
                    "sso-admin",
                    "get-inline-policy-for-permission-set",
                    "--instance-arn",
                    inst_arn,
                    "--permission-set-arn",
                    arn,
                    "--query",
                    "InlinePolicy",
                    "--output",
                    "text",
                    log=False,
                )
                if not r.ok:
                    logerr(IDENTITY_PROFILE, f"get-inline-policy ({name})", r.stderr)
                    set_rows.append((name, "(call failed)"))
                elif not r.stdout.strip():
                    set_rows.append((name, "(no inline policy)"))
                else:
                    set_rows.append((name, "yes" if DENY_SID in r.stdout else "no"))

    # -------------------------------------------------------- the GuardDuty delegation, one read
    delegation = "(not read)"
    if identity_live:
        cli = cli_for(IDENTITY_PROFILE)
        res = cli.run(
            "organizations",
            "list-delegated-administrators",
            "--service-principal",
            "guardduty.amazonaws.com",
            "--query",
            "DelegatedAdministrators[].[Id,Name,Status]",
            "--output",
            "text",
            log=False,
            tolerate="AccessDenied",
        )
        if res.tolerated:
            delegation = "(read denied from Identity - check from Management)"
        elif res.ok:
            delegation = res.stdout.strip() or "(none registered)"

    # -------------------------------------------------------------------------------- the checks
    # VP-1: exactly one WireGuard host in the VPN home, t4g.nano (D4). Absent = not built
    # yet; two = a rebuild that leaked.
    if home_live:
        if not instances:
            checks.note(
                "VP-1",
                "WireGuard host in the VPN home",
                f"no instance tagged {NAME_TAG_PATTERN} - expected before Stage 4 step 1.",
            )
        elif len(instances) > 1:
            checks.fail(
                "VP-1",
                "WireGuard host in the VPN home",
                f"{len(instances)} instances match {NAME_TAG_PATTERN} - a [D] slice holds "
                "exactly one; a second is a rebuild that leaked (step 1.3).",
            )
        else:
            iid, itype, istate, _sub, _ip, _tok, _sgs = instances[0]
            if itype != "t4g.nano":
                checks.fail(
                    "VP-1",
                    f"instance type of {iid}",
                    f"{itype} - D4 says t4g.nano; anything larger is paying for idle CPU.",
                )
            else:
                checks.ok("VP-1", f"one WireGuard host ({iid})", f"t4g.nano, state {istate}")

    # VP-2: the [P] Elastic IP exists and is associated with the host (step 2.1). The EIP
    # bills whether or not it is associated, so an orphan allocation is pure cost.
    if home_live:
        if not addresses:
            checks.note(
                "VP-2",
                "Elastic IP in the VPN home",
                "none allocated - expected before Stage 4 step 2.",
            )
        elif instances:
            iid = instances[0][0]
            assoc = [a for a in addresses if a[2] == iid]
            if assoc:
                checks.ok("VP-2", "Elastic IP associated with the host", f"{assoc[0][1]} -> {iid}")
            else:
                checks.fail(
                    "VP-2",
                    "Elastic IP associated with the host",
                    f"{len(addresses)} address(es) allocated, none associated with {iid} - "
                    "clients are pinned to an IP that reaches nothing (step 2.1), and "
                    "step 8's deny would then deny everyone everywhere.",
                )

    # VP-3: exactly one world-open ingress rule in the whole VPN home: UDP/51820 (step 3).
    if home_live and (instances or world_open):
        bad = [r for r in world_open if not (r[2] == "udp" and r[3] == "51820" and r[4] == "51820")]
        good = [r for r in world_open if r[2] == "udp" and r[3] == "51820" and r[4] == "51820"]
        for sgid, sgname, proto, pfrom, pto in bad:
            checks.fail(
                "VP-3",
                "world-open ingress rule",
                f"{sgid} ({sgname}): {proto}/{pfrom}-{pto} open to the world - step 3 "
                "allows exactly UDP/51820; port 22 belongs to SSM, not the internet.",
            )
        if instances and not good:
            checks.fail(
                "VP-3",
                "UDP/51820 reachable",
                "the host exists and no SG opens UDP/51820 - the tunnel cannot come up.",
            )
        if good and not bad:
            checks.ok(
                "VP-3",
                "exactly one world-open rule",
                f"UDP/51820 on {good[0][0]} - the expected shape from Stage 4 on",
            )

    # VP-4: IMDSv2 required on the host - it holds a role credential on a public subnet.
    if home_live and instances:
        iid, _t, _s, _sub, _ip, tokens, _sgs = instances[0]
        if tokens == "required":
            checks.ok("VP-4", f"IMDSv2 on {iid}", "HttpTokens=required")
        else:
            checks.fail(
                "VP-4",
                f"IMDSv2 on {iid}",
                f"HttpTokens={tokens} - a world-reachable NAT host with IMDSv1 is the "
                "textbook credential-theft target GuardDuty exists to catch; require tokens.",
            )

    # VP-5 / VP-6: the handshake log and the health alarm (step 7).
    if home_live and instances:
        if log_groups:
            lg, ret = log_groups[0]
            if ret and ret != "None":
                checks.ok("VP-5", f"handshake log group {lg}", f"retention {ret}d")
            else:
                checks.fail(
                    "VP-5",
                    f"handshake log group {lg}",
                    "no retention - an unbounded log group accumulates forever (step 7 "
                    "says 30 days).",
                )
        else:
            checks.fail(
                "VP-5",
                "handshake log group",
                "the host exists and no /awsds/*vpn* log group does - the CloudWatch "
                "agent is not shipping (step 7), or its allow-list entry is wrong "
                "(Stage 3, 9.3).",
            )
        if alarms:
            checks.ok("VP-6", "health alarm", "; ".join(f"{n} ({s})" for n, s in alarms))
        else:
            checks.fail(
                "VP-6",
                "health alarm",
                "the host exists and no awsds-*vpn* alarm does (step 7).",
            )
    elif home_live:
        checks.note("VP-5", "handshake log + alarm", "no host yet - expected before Stage 4.")

    # VP-7: which permission sets carry the step 8 deny. The six persona sets move
    # together (one shared fragment, 8.2); InfrastructureAccess is a separate decision
    # (8.3) and is reported, not judged.
    if identity_live and set_rows:
        persona = {n: v for n, v in set_rows if n in PERSONA_SETS}
        carrying = [n for n, v in persona.items() if v == "yes"]
        missing = [n for n in PERSONA_SETS if persona.get(n) != "yes"]
        if not carrying:
            checks.note(
                "VP-7",
                f"{DENY_SID} in the persona sets",
                "absent from all six - expected before Stage 4 step 8.",
            )
        elif missing:
            checks.fail(
                "VP-7",
                f"{DENY_SID} in the persona sets",
                f"present in {len(carrying)} of six, missing from: {', '.join(missing)} - "
                "a partial rollout is Lesson 14; the fragment reaches all six in one diff "
                "(step 8.2).",
            )
        else:
            checks.ok("VP-7", f"{DENY_SID} in the persona sets", "all six carry it")
        infra = dict(set_rows).get(INFRA_SET)
        if infra == "yes":
            checks.note(
                "VP-7",
                f"{DENY_SID} in {INFRA_SET}",
                "present - the deliberate 8.3 diff has been applied; break-glass (D16) is "
                "now the only path outside the VPN.",
            )
        elif carrying:
            checks.note(
                "VP-7",
                f"{DENY_SID} in {INFRA_SET}",
                "absent - the expected state until the deliverable pair is recorded (8.3).",
            )

    # VP-8: GuardDuty coverage, and the two deferred features still off (step 10).
    detectors = [r for r in gd_rows if r[1] != "-" and r[2] not in ("(call failed)",)]
    if not detectors:
        checks.note(
            "VP-8",
            "GuardDuty detectors",
            "none in any measured account - expected before Stage 4 step 10.",
        )
    else:
        for p, det, status, deferred in gd_rows:
            if det == "-" and status == "no detector":
                checks.fail(
                    "VP-8",
                    f"GuardDuty in {p}",
                    "no detector while other accounts have one - auto-enable did not reach "
                    "this account (verification (v)); a member outside coverage is exactly "
                    "the gap org-wide enablement exists to close.",
                )
            elif det != "-" and status != "ENABLED":
                checks.fail("VP-8", f"GuardDuty in {p}", f"detector {det} status {status}")
            elif det != "-":
                bad_feat = [n for n in DEFERRED_FEATURES if f"{n}=ENABLED" in deferred]
                if bad_feat:
                    checks.fail(
                        "VP-8",
                        f"GuardDuty features in {p}",
                        f"{' '.join(bad_feat)} ENABLED - S3/Malware Protection are decided "
                        "in Stage 11 step 4 against a real bill, not before (step 10.3).",
                    )
                else:
                    checks.ok("VP-8", f"GuardDuty in {p}", "ENABLED, deferred add-ons off")

    # VP-9: the [P] host-key secret (step 2.2a; decision 4, third review): present once the
    # stage runs, the value-read deny attached, and rotation OFF - the keys runbook's one
    # rule, mechanised into a failure if it ever flips.
    if home_live:
        if not host_key_secrets:
            checks.note(
                "VP-9",
                "host-key secret",
                f"no awsds-*{HOST_KEY_SECRET_SUFFIX} secret - expected before Stage 4 step 2.",
            )
        else:
            for name, rot, deny in host_key_secrets:
                if rot:
                    checks.fail(
                        "VP-9",
                        f"rotation on {name}",
                        "RotationEnabled - an automatic rotation replaces the key without "
                        "touching a single client config (the runbook's one rule, violated "
                        "by machine); turn it off and rotate by procedure C instead.",
                    )
                if deny == "no":
                    checks.fail(
                        "VP-9",
                        f"resource policy on {name}",
                        f"no statement with Sid {HOST_KEY_DENY_SID} - the value is one IAM "
                        "allow away from every principal in the account (step 2.2a): the "
                        "containment is attached, or it is an intention (Lesson 5).",
                    )
                elif deny == "yes" and not rot:
                    checks.ok(
                        "VP-9", f"host-key secret {name}", "value-read deny attached, rotation off"
                    )

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("VPN - the Stage 4 evidence: host, anchors, the step 8 deny, GuardDuty")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/vpn.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The WireGuard host ([D])
  3. The Elastic IP, the world-open rules and the host-key secret ([P] anchors)
  4. Handshake log and health alarm
  5. The control-plane deny (step 8), per permission set
  6. GuardDuty, org-wide
  7. CHECKS
  8. The accounts nothing here is measuring
  9. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 4 RUNS - each such reading
    is a note, not a failure; it becomes a regression the moment the stage closes.
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT - section 8 names what nothing here
    reached, GuardDuty's org configuration in Audit above all.
  - THIS IS A CONTROL-PLANE READING. The tunnel pair, the deny pair and the
    on-behalf carve-out are behavioural proofs run from the laptop (Lesson 20);
    INT-16's portal reading is a browser, not an API.

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
        rep.h1("2. The WireGuard host ([D])")
        if not home_live:
            rep.line(f"{VPN_HOME_PROFILE} was not measured - nothing to show.")
        elif not instances:
            rep.line(f"No instance tagged {NAME_TAG_PATTERN}. Expected before Stage 4 step 1.")
        else:
            rep.tabulate(
                ["INSTANCE\tTYPE\tSTATE\tSUBNET\tPUBLIC IP\tIMDS"]
                + [f"{i}\t{t}\t{s}\t{sub}\t{ip}\t{tok}" for i, t, s, sub, ip, tok, _ in instances]
            )
            rep.text("""
State `stopped` between sessions is D11 working, not an outage. `running` while
nobody is working is the [D] idle burn (~USD 0.004/h + the EBS).""")

        # ==============================================================================
        rep.h1("3. The Elastic IP, the world-open rules and the host-key secret ([P] anchors)")
        if home_live:
            if addresses:
                rep.tabulate(
                    ["ALLOCATION\tPUBLIC IP\tASSOCIATED INSTANCE"]
                    + [f"{a}\t{ip}\t{i}" for a, ip, i in addresses]
                )
                if instances:
                    assoc = [a for a in addresses if a[2] == instances[0][0]]
                    if assoc:
                        rep.line()
                        rep.line(f"WG_EIP={assoc[0][1]}")
                        rep.line("  - the value step 8's NotIpAddress list names, and a branch of")
                        rep.line("    Stage 5 step 1.3's bucket-policy condition (INT-05).")
            else:
                rep.line("No Elastic IP allocated. Expected before Stage 4 step 2.")
            rep.line()
            if world_open:
                rep.tabulate(
                    ["SG\tNAME\tPROTO\tFROM\tTO  (world-open ingress)"]
                    + [f"{g}\t{n}\t{pr}\t{f}\t{t}" for g, n, pr, f, t in world_open]
                )
            else:
                rep.line("No world-open ingress rule in the VPN home.")
            rep.line()
            if host_key_secrets:
                rep.tabulate(
                    ["SECRET\tROTATION\tVALUE-READ DENY"]
                    + [f"{n}\t{'ENABLED' if r else 'off'}\t{d}" for n, r, d in host_key_secrets]
                )
                rep.line("  - the deny is presence, never sufficiency: who can actually read the")
                rep.line("    value is proven by a persona's denied GetSecretValue, not here.")
            else:
                rep.line(
                    f"No awsds-*{HOST_KEY_SECRET_SUFFIX} secret. Expected before Stage 4 step 2."
                )
        else:
            rep.line(f"{VPN_HOME_PROFILE} was not measured - nothing to show.")

        # ==============================================================================
        rep.h1("4. Handshake log and health alarm")
        if home_live:
            if log_groups:
                rep.tabulate(["LOG GROUP\tRETENTION (days)"] + [f"{n}\t{r}" for n, r in log_groups])
            else:
                rep.line("No /awsds/*vpn* log group.")
            rep.line()
            if alarms:
                rep.tabulate(["ALARM\tSTATE"] + [f"{n}\t{s}" for n, s in alarms])
            else:
                rep.line("No awsds-*vpn* alarm.")
        else:
            rep.line(f"{VPN_HOME_PROFILE} was not measured - nothing to show.")

        # ==============================================================================
        rep.h1("5. The control-plane deny (step 8), per permission set")
        rep.text(f"""The reading greps each set's inline policy for the Sid `{DENY_SID}` - presence,
never sufficiency: the conditions inside it (the EIP list, aws:ViaAWSService) are
proven by the stage's deny pair, not by this file.

""")
        if not identity_live:
            rep.line(f"{IDENTITY_PROFILE} was not measured - the sets were not read.")
        elif not set_rows:
            rep.line("No project permission set was found - see section 9.")
        else:
            rep.tabulate(
                [f"PERMISSION SET\tCARRIES {DENY_SID}"] + [f"{n}\t{v}" for n, v in sorted(set_rows)]
            )

        # ==============================================================================
        rep.h1("6. GuardDuty, org-wide")
        rep.tabulate(
            ["PROFILE\tDETECTOR\tSTATUS\tDEFERRED ADD-ONS (must be DISABLED)"]
            + [f"{p}\t{d}\t{s}\t{f}" for p, d, s, f in gd_rows]
        )
        rep.line()
        rep.line(f"delegated administrator (guardduty.amazonaws.com): {delegation}")
        rep.text("""
Delegating IS enabling (Stage 4 step 10.1): the registration is made from
Management, the org configuration from Audit - neither holds a profile, so this
file can only read the registration and each member's detector. Restate INV-09
in docs/AWS_STATE.md when the delegation lands, and re-run
./aws/org-trusted-access-services.py.""")

        # ==============================================================================
        rep.h1("7. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  VP-1  exactly one t4g.nano WireGuard host in the VPN home (steps 1.1, 1.3; D4)
  VP-2  the [P] Elastic IP exists and is associated with the host (step 2.1)
  VP-3  exactly one world-open ingress rule, UDP/51820; never port 22 (step 3)
  VP-4  IMDSv2 required on the host
  VP-5  the handshake log group exists, with retention (step 7)
  VP-6  the health alarm exists (step 7)
  VP-7  the persona sets carry the step 8 deny together, or not at all (8.2);
        InfrastructureAccess is reported as the separate 8.3 decision
  VP-8  GuardDuty enabled in every measured account, deferred add-ons off (step 10)
  VP-9  the [P] host-key secret carries its value-read deny and rotation is OFF
        (step 2.2a; decision 4, third review - the keys runbook's one rule)""")

        # ==============================================================================
        rep.h1("8. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 7 as a pass.

  - GuardDuty's ORG CONFIGURATION lives in Audit, which holds no CLI profile
    (D33/D34): auto-enable-for-future-accounts is verified in the Audit console
    or CloudShell, not here. Section 6 reads only the members' detectors.
  - Management's own detector is outside every profile here; read it from
    CloudShell if the coverage question ever includes it.
  - `Staging` is unvended; every Sandbox beyond unit 1 has no profile until
    Stage 14. A vend must ARRIVE covered by auto-enable - re-run this script
    after each one (verification (v)).""")

        # ==============================================================================
        rep.h1("9. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/vpn.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 9)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 7)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
