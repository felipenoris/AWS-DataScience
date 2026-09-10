#!/usr/bin/env -S uv run --quiet
# vpn.py - Stage 4's evidence, side by side: the WireGuard host ([D]) and its IMDS
# setting, the Elastic IP, the one world-open security-group rule and the host-key secret
# ([P] anchors - the secret must carry its value-read deny and keep rotation off), the
# handshake log and health alarm, and which permission sets carry the control-plane deny
# of step 8 (read back from Identity Center, never assumed).
#
# The GuardDuty reading is ./aws/guardduty.py (GD-1..GD-3) since 2026-08-18, the day
# GuardDuty left Stage 4 for Stage 15. VP-8 is retired here, not renumbered - the Stage 4
# log cites it by that name.
#
#   needs:    a live SSO session, the only prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/vpn.py                        # every awsds-infra-* profile (VP-3 reads all)
#             ./aws/vpn.py awsds-infra-prod  # only the ones named
#             ./aws/vpn.py --on-host              # also read inside the host (see below)
#             python3 aws/vpn.py -                # CloudShell, ambient credentials
#   writes:   aws/output/vpn.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeInstances, DescribeVolumes, DescribeAddresses,
#             DescribeSecurityGroups,
#             logs:DescribeLogGroups, cloudwatch:DescribeAlarms,
#             secretsmanager:ListSecrets, GetResourcePolicy,
#             sso-admin:ListInstances, ListPermissionSets, DescribePermissionSet,
#             GetInlinePolicyForPermissionSet, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything - see the next line for the
#             single, typed exception.
#   sends:    nothing in AWS, unless --on-host is typed. That flag adds ssm:SendCommand +
#             GetCommandInvocation, and SendCommand is a write API: it creates a Command,
#             is a mutating CloudTrail event, and runs code on an instance, even though
#             every command it carries is a read. It is a flag and not a default so that
#             `./aws/vpn.py` stays safe to fire at anything. Section 2a says what it buys -
#             which peers the running wg0 actually holds, which no describe answers.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# It is two-profile, which aws/INDEX.md admits only for a reason: the step 8 deny lives in
# the Identity account's permission sets while the Elastic IP it names lives in the VPN
# home, so the two halves of one control sit in two accounts by design. Since the GuardDuty
# reading left (2026-08-18) those two are the whole subject, and the default run selects
# exactly them; naming profiles on the command line still measures any set. Section 1 pays
# the rule back with the caller ARN of every profile.
#
# The contracts this file reads, each named in the stage file so a rename fails loudly:
#   - the instance Name tag matches awsds-*-vpn (Stage 4 step 1.1)
#   - the deny statement's Sid is DenyControlPlaneOffVpn (Stage 4 step 8.1)
#   - the host-key secret's name ends in -vpn-host-key (Stage 4 step 2.2a)
#   - its resource policy's Sid is DenyValueReadExceptHostAndInfrastructure (2.2a)
#
# What it cannot see, stated because an empty listing and a missing account look alike:
#   - The behavioural proofs - the tunnel pair, the control-plane deny pair, the
#     on-behalf carve-out - are the stage's own, run from the laptop with the tunnel up
#     and down. A describe call proves none of them (Lesson 20).
#   - Whether the deny actually gates the Unified Studio portal is INT-16 and is answered
#     by opening the portal, not by reading a policy.
#   - Management, Log Archive and Audit hold no CLI profile; nothing here reads them.

from __future__ import annotations

import json
import sys
import time

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "vpn.txt"

# The VPN home is a role an account plays (D35, Stage 4's forward constraint). Sandbox played
# it from Stage 4 until 6c step 4.7; Production plays it since 2026-09-06, because D38 puts the
# tunnel endpoint in VPC-Networking beside the proxy.
#
# This constant moves with the host. Left pointing at an account with no tunnel in it, every
# check here goes on describing the wrong place - VP-3 reading `pass` about a world-open rule
# guarding nothing, VP-1 finding no host and calling it a finding - while the live tunnel goes
# unmeasured (Lesson 31).
#
# NAME_TAG_PATTERN below needs no such edit: `awsds-*-vpn` matched `awsds-sandbox-vpn` and
# matches `awsds-prod-vpn`, where a literal would have been a second edit nobody would find
# until a check came back empty.
VPN_HOME_PROFILE = "awsds-infra-prod"
IDENTITY_PROFILE = "awsds-infra-identity"

# The contracts (see header).
NAME_TAG_PATTERN = "awsds-*-vpn"
DENY_SID = "DenyControlPlaneOffVpn"
# The deny's third condition, which has had two spellings. Until 2026-08-23 it was
# aws:SourceVpce over the VPN home's two gateway endpoint ids, one case short: with egress/
# up, every service holding an interface endpoint resolves to a private address through the
# VPC resolver and the call presents that endpoint's id, which the list did not carry and
# may never carry ([E], new on every make up - Lesson 3). It was widened to aws:SourceVpc,
# which is [P] and subsumes the two gateway ids (AWS_STATE.md). The retired form is still
# read here, so the narrower predecessor is named rather than lumped in with the
# address-only defect.
#
# Both are matched quoted: "aws:SourceVpc" is a prefix of "aws:SourceVpce", so a bare
# substring test cannot tell the current form from the retired one, which is the distinction
# the check has to make.
VPC_CONDITION_KEY = "aws:SourceVpc"
RETIRED_VPCE_CONDITION_KEY = "aws:SourceVpce"
HOST_KEY_SECRET_SUFFIX = "-vpn-host-key"
HOST_KEY_DENY_SID = "DenyValueReadExceptHostAndInfrastructure"

# The size the cost model is written against - D4's shape, the slice's default, and the only
# one scripts/tfhygiene/layers.py and docs/PRICING.md 3 price. The slice takes instance_type as
# a parameter (t3.nano | t3.micro | t3.medium, vpn.md section S6), so a host that is not this
# size is a deliberate selection and not a failure: VP-1 reports the type it found and passes.
# The burn line of `make status` and the hourly rows of PRICING keep quoting the nano's rate
# whatever is running, so this line is the only place the reader is told the two have parted
# company (a t3.medium is eight times the rate).
#
# The family is t3, not t4g: the wireguard module's AMI is AL2023 x86_64. This constant follows
# the module, never the running host - a host still reading t4g here after that apply is not
# drift this check is measuring, it is an apply that has not happened yet.
BASELINE_INSTANCE_TYPE = "t3.nano"

# The disk the cost model is written against - the wireguard module's default, and the size
# docs/PRICING.md 2's `WireGuard EBS (8 GB)` row prices. The slice takes root_volume_size as
# a parameter too (8-128 GiB, vpn.md section S6), so a host on a bigger disk is a deliberate
# selection and not a failure: VP-1 reports the size it found and passes, as it does for the
# type.
#
# It is a second constant rather than a second clause on the first because the two gaps are
# not the same kind of wrong, and one "non-baseline" verdict would blur them. A stopped
# instance bills no hours, so the type's understatement is only live while somebody is
# working. The volume bills every hour of the month regardless, so its understatement is
# standing: it is wrong in a month when the tunnel was never brought up at all (64 GiB is
# ~5.12 USD/month against this baseline's ~0.64). VP-1 names them separately, and points at
# different cost lines.
BASELINE_ROOT_VOLUME_SIZE_GIB = 8

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

# --------------------------------------------------------------- the inside of the host (2a)
#
# This is the one part of this file that is not read-only, so it is opt-in. Everything the
# commands below do on the host is a read - grep, cat, wg show, systemctl is-active, tail -
# but `ssm:SendCommand` is a write API: it creates a Command, appears in CloudTrail as a
# mutating call, and executes code on an instance. `aws/*` is read-only so that anyone may
# run these scripts to gather information without thinking about it, so the escalation has to
# be typed: without --on-host nothing here runs.
#
# A read-only path was tried first. ec2:GetConsoleOutput is a pure read and returns the boot's
# say-lines, but it returned zero bytes on both Stage 4 hosts for the first several minutes
# (measured 2026-08-17), and it cannot answer the questions that matter after the boot: which
# peers the interface actually holds, whether the name map matches the roster, whether the
# sampler timer is alive. Those are the live state of the tunnel, and SSM is the only path to
# them.
#
# `wg show wg0` and never `wg show all dump`: the dump form prints the interface's private key
# on its first line, and this output is written verbatim into aws/output/vpn.txt. The host's
# own sampler avoids the same form for the same reason (Stage 4 step 7); the check below is
# the gate under that rule rather than a memory of it (Lesson 5).
HOST_PROBE_COMMANDS = (
    "grep -a AWSDS-VPN /var/log/cloud-init-output.log",
    "echo ---STATUS---",
    "cloud-init status",
    "echo ---WG---",
    "wg show wg0",
    "echo ---NAMES---",
    "cat /etc/wireguard/peer-names",
    "echo ---SAMPLER---",
    "systemctl is-active awsds-wg-handshakes.timer",
    "tail -4 /var/log/wireguard-handshakes.log",
    # The other half of the disk reading, and why it is worth an SSM round trip: section 2's
    # ROOT DISK column is DescribeVolumes, which is the block device. Growing a volume does not
    # grow the partition or the XFS on top of it - cloud-init's growpart does that, at boot -
    # so a disk change applied to a running host leaves the two disagreeing, and vpn.md section
    # S6 says to read both rather than one. These two lines are the only place the second one
    # is legible. Both are reads (HOST_PROBE_BANNED is unmoved).
    "echo ---DISK---",
    "lsblk",
    "df -h /",
    # The refusing side's counters (6c step 6.1, 2026-09-07; Lesson 55). A refusal the sender
    # cannot see is indistinguishable from silence: the FORWARD chain REJECTs every tunnel
    # packet not bound for RFC1918 with icmp-admin-prohibited but rate-limits the ICMP that
    # would say so (the ICMP block below, step 6.4), so the client reads a timeout more often
    # than not. The only place the refusal is legible is the rule's packet count here, which is
    # what 6c step 6.4 reads across a client's attempt. The nat table is 4.7's other half: the
    # RETURN rule for the proxy's subnet is the deliberate masquerade hole that lets Squid log
    # a per-device address, and its counter should move only for proxy-bound connections. All
    # three are `-L` listings - reads, under the same ban list as everything above.
    "echo ---FORWARD---",
    "iptables -L FORWARD -v -n --line-numbers",
    "ip6tables -L FORWARD -v -n --line-numbers",
    "echo ---NAT---",
    "iptables -t nat -L POSTROUTING -v -n --line-numbers",
    # Whether the host says "no" out loud (6c step 6.4, 2026-09-07). A REJECT counts a packet
    # whether or not the ICMP error it is meant to send actually left: Linux rate-limits ICMP
    # errors per destination (icmp_ratelimit / icmp_ratemask), so a laptop whose background
    # applications are being refused dozens of times a second can starve the bucket, and the one
    # packet the user is watching gets no ICMP at all - a timeout on the client that the REJECT
    # counter alone would attribute to macOS. The contrast is REJECT pkts against
    # Icmp OutDestUnreachs (and Icmp6OutDestUnreachs for the ULA rule): equal means every
    # refusal was spoken; a gap is the host's own silence. Reads, all four.
    "echo ---ICMP---",
    "grep -E '^Icmp:' /proc/net/snmp",
    "grep -E '^Icmp6(In|Out)(DestUnreachs|Errors|Msgs) ' /proc/net/snmp6",
    "sysctl net.ipv4.icmp_ratelimit net.ipv4.icmp_ratemask net.ipv4.icmp_msgs_per_sec net.ipv4.icmp_msgs_burst",
)
HOST_PROBE_BANNED = ("dump", ">", "rm ", "systemctl start", "systemctl stop", "wg set")
HOST_PROBE_POLLS = 20
HOST_PROBE_INTERVAL_S = 5


def _assert_probe_commands_are_reads() -> None:
    """Refuse to send a command list that stopped being a read, before it is sent.

    A banned fragment is a safety gate: `dump` would ship the interface's private key into an
    output file, and the three write forms would make this script something nobody can run to
    gather information any more.
    """
    for cmd in HOST_PROBE_COMMANDS:
        for banned in HOST_PROBE_BANNED:
            if banned in cmd:
                note(f"REFUSING --on-host: {banned!r} appears in {cmd!r}")
                sys.exit(1)


def read_host(cli: AwsCli, instance_id: str, logerr) -> tuple:
    """Run HOST_PROBE_COMMANDS on one instance through SSM; return (status, output).

    Returns ``(status, text)`` where status is SSM's own - ``Success``, ``Failed``,
    ``TimedOut`` - or one of this function's two: ``(send failed)`` when SendCommand itself
    was refused, and ``(still running)`` when the invocation had not settled inside
    HOST_PROBE_POLLS * HOST_PROBE_INTERVAL_S seconds. The three are distinguishable on
    purpose: a refused send is usually the instance not being SSM-managed yet, while a
    never-settling one is a host that is up and not answering.
    """
    params = json.dumps({"commands": list(HOST_PROBE_COMMANDS)})
    res = cli.run(
        "ssm",
        "send-command",
        "--instance-ids",
        instance_id,
        "--document-name",
        "AWS-RunShellScript",
        "--parameters",
        params,
        "--query",
        "Command.CommandId",
        "--output",
        "text",
        log=False,
    )
    if not res.ok:
        logerr(VPN_HOME_PROFILE, f"ssm send-command {instance_id}", res.stderr)
        return "(send failed)", ""
    command_id = res.stdout.strip()

    status, out, err = "(still running)", "", ""
    for _ in range(HOST_PROBE_POLLS):
        inv = cli.run(
            "ssm",
            "get-command-invocation",
            "--command-id",
            command_id,
            "--instance-id",
            instance_id,
            "--output",
            "json",
            log=False,
        )
        if inv.ok:
            doc = json.loads(inv.stdout or "{}")
            status = doc.get("Status", "?")
            out = doc.get("StandardOutputContent", "") or ""
            err = doc.get("StandardErrorContent", "") or ""
            if status not in ("Pending", "InProgress", "Delayed"):
                break
        time.sleep(HOST_PROBE_INTERVAL_S)

    text = out
    if err.strip():
        text += "\n--- stderr ---\n" + err
    return status, text


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    # The one flag this file has, stripped before profiles.select(), which reads every
    # remaining argument as a profile name (see awslib/profiles.py).
    on_host = "--on-host" in argv
    argv = [a for a in argv if a != "--on-host"]
    if on_host:
        _assert_probe_commands_are_reads()

    if argv:
        selected, source = profiles.select(argv)
    else:
        # Every awsds-infra-* profile, the home and Identity among them (6c step 6.5): VP-3
        # asks whether the estate holds exactly one world-open rule, and a check that reads
        # one account keeps reporting pass while another account carries a second (Lesson 31).
        selected = sorted(
            set(profiles.discover("awsds-infra-")) | {VPN_HOME_PROFILE, IDENTITY_PROFILE}
        )
        source = "every awsds-infra-* profile (VP-3 reads every account's security groups)"

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    checks = Checks()

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    # ------------------------------------------------------- the VPN home: host, EIP, SG, alarm
    home_live = VPN_HOME_PROFILE in live
    instances: list = []  # (id, type, state, subnet, public ip, http tokens, sg ids)
    root_volumes: dict = {}  # instance id -> (volume id, size in GiB, volume type)
    addresses: list = []  # (allocation id, public ip, instance id or '-')
    world_open: list = []  # (profile, sg id, sg name, proto, from, to) - EVERY live infra account
    log_groups: list = []  # (name, retention)
    alarms: list = []  # (name, state)
    host_key_secrets: list = []  # (name, rotation enabled, value-read deny: yes/no/(call failed))
    host_reads: list = []  # (instance id, ssm status, output) - only with --on-host
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
                    # The root device only - a WireGuard host has one, but the mapping is a
                    # list, and matching on RootDeviceName keeps this honest if a second
                    # volume is ever attached for something.
                    root_name = inst.get("RootDeviceName")
                    for bdm in inst.get("BlockDeviceMappings", []):
                        if bdm.get("DeviceName") == root_name:
                            vol_id = (bdm.get("Ebs") or {}).get("VolumeId")
                            if vol_id:
                                root_volumes[inst.get("InstanceId", "?")] = (vol_id, "?", "?")

        # The size is not in the answer above, which is why this is a second call rather than
        # one more field: DescribeInstances names the root device and its volume id and stops,
        # and capacity is a property of the volume. One extra call, for the hosts already
        # found. A failure here leaves the size reading `?` rather than taking the section
        # down: the disk is a report and not a control, and nothing in this file fails on it
        # (see BASELINE_ROOT_VOLUME_SIZE_GIB).
        if root_volumes:
            res = cli.run(
                "ec2",
                "describe-volumes",
                "--volume-ids",
                *sorted(v[0] for v in root_volumes.values()),
                "--query",
                "Volumes[].[VolumeId,Size,VolumeType]",
                "--output",
                "text",
                log=False,
            )
            if not res.ok:
                logerr(VPN_HOME_PROFILE, "ec2 describe-volumes", res.stderr)
            else:
                sized = {}
                for line in (res.stdout or "").splitlines():
                    parts = line.split("\t")
                    if len(parts) == 3:
                        sized[parts[0]] = (parts[1], parts[2])
                for iid, (vol_id, _sz, _vt) in list(root_volumes.items()):
                    size, vtype = sized.get(vol_id, ("?", "?"))
                    root_volumes[iid] = (vol_id, size, vtype)

        # Only a running host can answer; a stopped one is D11 working, not a failure, so it
        # is skipped rather than attempted and reported as an error.
        if on_host:
            for inst in instances:
                if inst[2] != "running":
                    continue
                note(f"reading inside {inst[0]} through SSM (--on-host) ...")
                status, text = read_host(cli, inst[0], logerr)
                host_reads.append((inst[0], status, text))

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
        # the rotation flag; the resource policy is a second read per match. Matched by name,
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
                    # Presence of the Sid is not enough: on 2026-08-20 the statement carried
                    # the right Sid and the wrong condition set for three days while this
                    # check reported "all six carry it" (Lesson 31). Tunnel traffic splits by
                    # destination, so an aws:SourceIp-only test denies every direct S3 call
                    # made from inside the perimeter. The third condition is read as well,
                    # in the spelling that is current (see VPC_CONDITION_KEY).
                    if DENY_SID not in r.stdout:
                        set_rows.append((name, "no"))
                    elif f'"{VPC_CONDITION_KEY}"' in r.stdout:
                        set_rows.append((name, "yes"))
                    elif f'"{RETIRED_VPCE_CONDITION_KEY}"' in r.stdout:
                        set_rows.append((name, "yes, vpce only"))
                    else:
                        set_rows.append((name, "yes, IP only"))

    # -------------------------------------------------------------------------------- the checks
    # VP-1: exactly one WireGuard host in the VPN home. Absent = not built yet; two = a
    # rebuild that leaked. The shape - the instance type and the root volume - is reported,
    # never judged: both are slice parameters (vpn.md section S6), so a host that is not the
    # baseline is somebody's decision, and a check red about it is a check nobody reads
    # (Lesson 31). See BASELINE_INSTANCE_TYPE and BASELINE_ROOT_VOLUME_SIZE_GIB.
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
            _vol, vsize, vtype = root_volumes.get(iid, ("-", "?", "?"))
            shape = f"{itype} on {vsize} GiB {vtype}, state {istate}"

            # The two departures are named separately because they break different cost lines,
            # and a single "not the baseline" sentence would hide the one that keeps costing
            # while nothing is happening. Hourly first, standing second, so the sentence ends
            # on the one a reader who stops early should still have seen.
            drift = []
            if itype != BASELINE_INSTANCE_TYPE:
                drift.append(
                    f"the type is not the {BASELINE_INSTANCE_TYPE} baseline, so every HOURLY "
                    "figure here and in `make status` understates the burn while it runs"
                )
            if vsize.isdigit() and int(vsize) != BASELINE_ROOT_VOLUME_SIZE_GIB:
                drift.append(
                    f"the root volume is not the {BASELINE_ROOT_VOLUME_SIZE_GIB} GiB baseline, "
                    "so docs/PRICING.md 2's monthly floor understates the burn even while the "
                    "host is STOPPED"
                )
            if drift:
                checks.ok(
                    "VP-1",
                    f"one WireGuard host ({iid})",
                    f"{shape} - " + "; and ".join(drift) + " (vpn.md section S6).",
                )
            else:
                checks.ok("VP-1", f"one WireGuard host ({iid})", shape)

    # VP-2: the [P] Elastic IP exists and is associated with the host (step 2.1). The EIP
    # bills whether or not it is associated, so an orphan allocation is pure cost.
    #
    # The allocated-but-hostless case is a reading, not a silence: between the [P] apply and
    # step 1.4 there is legitimately an address and no instance, and unreported it would leave
    # the one state this check exists to price - an allocation nobody ever attaches -
    # unmentioned for as long as it lasted (Lesson 13). It is a note rather than a FAIL
    # because the stage's own order produces it.
    if home_live:
        if not addresses:
            checks.note(
                "VP-2",
                "Elastic IP in the VPN home",
                "none allocated - expected before Stage 4 step 2.",
            )
        elif not instances:
            checks.note(
                "VP-2",
                f"Elastic IP allocated, no host yet ({addresses[0][1]})",
                "expected between step 2.3 and step 1.4 - and it bills unassociated "
                "(~USD 3.65/month), so this reading standing for longer than that stretch "
                "is an orphan allocation, not a stage in progress.",
            )
        else:
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

    # World-open ingress, read in every live infra account (6c step 6.5). Reading the VPN home
    # alone kept VP-3 passing while Sandbox's retired anchors carried a second world-open rule
    # guarding no listener (Lesson 31). One describe-security-groups per account; all reads.
    sg_accounts_read: list = []
    for prof in [c.profile for c in callers if c.live and c.profile.startswith("awsds-infra-")]:
        res = cli_for(prof).run("ec2", "describe-security-groups", "--output", "json", log=False)
        if not res.ok:
            logerr(prof, "ec2 describe-security-groups", res.stderr)
            continue
        sg_accounts_read.append(prof)
        doc = json.loads(res.stdout or "{}")
        for sg in doc.get("SecurityGroups", []):
            for perm in sg.get("IpPermissions", []):
                open_v4 = any(r.get("CidrIp") == "0.0.0.0/0" for r in perm.get("IpRanges", []))
                open_v6 = any(r.get("CidrIpv6") == "::/0" for r in perm.get("Ipv6Ranges", []))
                if open_v4 or open_v6:
                    world_open.append(
                        (
                            prof,
                            sg.get("GroupId", "?"),
                            sg.get("GroupName", "?"),
                            perm.get("IpProtocol", "?"),
                            str(perm.get("FromPort", "-")),
                            str(perm.get("ToPort", "-")),
                        )
                    )

    # VP-3: exactly one world-open ingress rule in the whole estate, the VPN home's UDP/51820
    # (step 3; widened at 6c step 6.5). A rule in any other account is a finding whatever its
    # port, and so is a second one in the home.
    def _is_the_tunnel(rule: tuple) -> bool:
        prof, _g, _n, proto, pfrom, pto = rule
        return prof == VPN_HOME_PROFILE and proto == "udp" and pfrom == "51820" and pto == "51820"

    if world_open or (home_live and instances):
        good = [r for r in world_open if _is_the_tunnel(r)]
        bad = [r for r in world_open if not _is_the_tunnel(r)]
        for prof, sgid, sgname, proto, pfrom, pto in bad:
            where = "the VPN home" if prof == VPN_HOME_PROFILE else prof
            checks.fail(
                "VP-3",
                "world-open ingress rule",
                f"{sgid} ({sgname}) in {where}: {proto}/{pfrom}-{pto} open to the world - step 3 "
                "allows exactly UDP/51820 in the VPN home and nothing anywhere else; port 22 "
                "belongs to SSM, not the internet.",
            )
        if home_live and instances and not good:
            checks.fail(
                "VP-3",
                "UDP/51820 reachable",
                "the host exists and no SG opens UDP/51820 - the tunnel cannot come up.",
            )
        if good and not bad:
            others = len([p for p in sg_accounts_read if p != VPN_HOME_PROFILE])
            checks.ok(
                "VP-3",
                "exactly one world-open rule in the estate",
                f"UDP/51820 on {good[0][1]} in the VPN home, none in the {others} other account(s) read",
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

    # VP-7: which permission sets carry the step 8 deny. The six persona sets move together
    # (one shared fragment, 8.2). InfrastructureAccess stays off-VPN (open question 17,
    # 2026-08-17, option a): the VPN host is a [D] instance that credential must be able to
    # start from anywhere, or the tunnel's own outage is unrecoverable without break-glass, so
    # for the seventh set the deny is judged in the opposite direction.
    if identity_live and set_rows:
        persona = {n: v for n, v in set_rows if n in PERSONA_SETS}
        carrying = [n for n, v in persona.items() if v.startswith("yes")]
        missing = [n for n in PERSONA_SETS if not persona.get(n, "").startswith("yes")]
        ip_only = sorted(n for n, v in persona.items() if v == "yes, IP only")
        vpce_only = sorted(n for n, v in persona.items() if v == "yes, vpce only")
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
        elif ip_only:
            checks.fail(
                "VP-7",
                f"{DENY_SID} tests {VPC_CONDITION_KEY}",
                f"MISSING from: {', '.join(ip_only)} - the statement is present and "
                "wrong, which is the Stage 5 pass 4d defect (Lesson 33). Tunnel traffic "
                "SPLITS BY DESTINATION: S3 and DynamoDB leave through the VPN home's [P] "
                "gateway endpoints and arrive with the host's PRIVATE address plus a "
                "vpcEndpointId, never the Elastic IP - so an address-only test denies "
                "every direct S3 call a persona makes from INSIDE the perimeter (the "
                "scientist runs the query and cannot fetch the CSV). The fix is a third "
                "condition, StringNotEqualsIfExists over the HOME's VPC - see "
                "terraform-live/identity/sso/policies-shared.tf.",
            )
        elif vpce_only:
            checks.fail(
                "VP-7",
                f"{DENY_SID} tests {VPC_CONDITION_KEY}",
                f"{', '.join(vpce_only)} still test {RETIRED_VPCE_CONDITION_KEY}, the "
                "spelling retired 2026-08-23. A list of the HOME's two GATEWAY endpoint "
                "ids cannot carry the INTERFACE endpoint a call presents while egress/ is "
                "up - those ids are [E], new on every make up (Lesson 3) - so a persona is "
                "denied sts:GetCallerIdentity with the tunnel UP and curl reading the "
                "Elastic IP. aws:SourceVpc is [P] and SUBSUMES both gateways, so nothing "
                "that passed before stops passing - see "
                "terraform-live/identity/sso/policies-shared.tf.",
            )
        else:
            checks.ok(
                "VP-7",
                f"{DENY_SID} in the persona sets",
                f"all six carry it, each testing {VPC_CONDITION_KEY} as well as the address",
            )
        infra = dict(set_rows).get(INFRA_SET, "")
        if infra.startswith("yes"):
            checks.fail(
                "VP-7",
                f"{DENY_SID} in {INFRA_SET}",
                "PRESENT - open question 17 decided this set stays off-VPN (option a, "
                "2026-08-17): with the deny on it, a stopped VPN host cannot be started "
                "except from the address of the host that is stopped, and break-glass "
                "(D16) becomes the routine way back in. Somebody applied what the "
                "decision declined.",
            )
        elif carrying:
            checks.ok(
                "VP-7",
                f"{DENY_SID} absent from {INFRA_SET}",
                "by decision (open question 17): the recovery path stays off-VPN",
            )

    # VP-9: the [P] host-key secret (step 2.2a; decision 4, third review): present once the
    # stage runs, the value-read deny attached, and rotation off - the keys runbook's one
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

        rep.banner("VPN - the Stage 4 evidence: host, anchors, the step 8 deny")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/vpn.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The WireGuard host ([D])
  2a. Inside the host - OPT-IN, --on-host
  3. The Elastic IP, the world-open rules and the host-key secret ([P] anchors)
  4. Handshake log and health alarm
  5. The control-plane deny (step 8), per permission set
  6. CHECKS
  7. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 4 RUNS - each such reading
    is a note, not a failure; it becomes a regression the moment the stage closes.
  - THIS IS A CONTROL-PLANE READING. The tunnel pair, the deny pair and the
    on-behalf carve-out are behavioural proofs run from the laptop (Lesson 20);
    INT-16's portal reading is a browser, not an API.
  - THE GUARDDUTY READING IS ./aws/guardduty.py SINCE 2026-08-18 (Stage 15); its
    former id here, VP-8, is retired.

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
                ["INSTANCE\tTYPE\tROOT DISK\tSTATE\tSUBNET\tPUBLIC IP\tIMDS"]
                + [
                    "{}\t{}\t{} GiB {}\t{}\t{}\t{}\t{}".format(
                        i, t, *root_volumes.get(i, ("-", "?", "?"))[1:], s, sub, ip, tok
                    )
                    for i, t, s, sub, ip, tok, _ in instances
                ]
            )
            rep.text("""
State `stopped` between sessions is D11 working, not an outage. `running` while
nobody is working is the [D] idle burn (~USD 0.004/h + the EBS) - and the EBS
half is the one that does NOT stop, which is why the disk is in the table.

ROOT DISK IS THE BLOCK DEVICE, NOT THE FILESYSTEM. It comes from DescribeVolumes
- what EC2 attached. Growing a volume does not grow the partition or the XFS on
top of it; cloud-init's growpart does that, at BOOT. So after a disk change
applied to a RUNNING host the two legitimately disagree, and this column shows
the half you are already paying for. Section 2a's `lsblk` / `df -h /` is the
only place the other half is legible (vpn.md section S6).""")

        # ==============================================================================
        rep.h1("2a. Inside the host - OPT-IN, --on-host")
        if not on_host:
            rep.text("""Not run. Everything else in this file is read-only; this section is the one
part that is not, so it has to be typed:

    ./aws/vpn.py --on-host

It runs eighteen READ commands on the host through SSM Run Command - the boot's
say-lines, `cloud-init status`, `wg show wg0`, the name map, the sampler timer
and the tail of its log, then `lsblk` and `df -h /`, and (since 2026-09-07) the FORWARD
chain and nat POSTROUTING counters - the refusing side's evidence (Lesson 55). The commands read;
`ssm:SendCommand` writes, which is the whole reason for the flag. A stopped host
is skipped, not attempted.

What it answers that no describe call can, and there are two of them now:

  WHICH PEERS THE INTERFACE ACTUALLY HOLDS. Section 3's checks prove the host,
  the address and the secret exist - they cannot prove that the running wg0
  matches peers.auto.tfvars, and the gap between those two is exactly what the
  keys runbook section 4 calls `peer=unknown`.

  WHETHER THE FILESYSTEM FOLLOWED THE VOLUME. Section 2's ROOT DISK is what EC2
  attached; growing it does not grow the XFS on top, which happens at boot via
  growpart. `lsblk` and `df -h /` are the only reading that separates the two -
  a device that grew under a filesystem that did not is a host billed for space
  it cannot use (vpn.md section S6).""")
        elif not host_reads:
            rep.line("--on-host was given, but no RUNNING host was found to read.")
        else:
            for iid, status, text in host_reads:
                rep.line(f"{iid}   ssm status: {status}")
                rep.line()
                rep.raw(text.rstrip() if text.strip() else "(no output)")
                rep.line()
                rep.line()
            rep.text("""Read `wg show wg0`'s peer list against `peers.auto.tfvars`, and the name map
against both. A peer the interface holds and the roster does not is a peer
somebody added by hand (`wg set` - the keys runbook section 4 stopgap): it will
disappear at the next `make down` / `make up` without telling anybody, and until
then the handshake log calls it `peer=unknown`.""")

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
                    ["ACCOUNT\tSG\tNAME\tPROTO\tFROM\tTO  (world-open ingress, every account read)"]
                    + [f"{p}\t{g}\t{n}\t{pr}\t{f}\t{t}" for p, g, n, pr, f, t in world_open]
                )
            else:
                rep.line("No world-open ingress rule in any account read.")
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
        rep.text(f"""The reading greps each set's inline policy for the Sid `{DENY_SID}` and for the
condition key `{VPC_CONDITION_KEY}` inside it. Presence of the Sid alone was the
reading until 2026-08-20, and it reported "all six carry it" for three days over a
statement that denied every direct S3 call a persona made from inside the perimeter
(Stage 5 pass 4d; Lesson 33). `yes, IP only` is that defect. `yes, vpce only` is its
NARROWER SUCCESSOR, retired 2026-08-23: {RETIRED_VPCE_CONDITION_KEY} over the home's two
gateway ids, which no interface endpoint can ever appear in. It is still not
sufficiency - the values in the lists, and aws:ViaAWSService, are proven by the
stage's deny pair and by a behavioural probe, not by this file.

""")
        if not identity_live:
            rep.line(f"{IDENTITY_PROFILE} was not measured - the sets were not read.")
        elif not set_rows:
            rep.line("No project permission set was found - see section 7.")
        else:
            rep.tabulate(
                [f"PERMISSION SET\tCARRIES {DENY_SID}"] + [f"{n}\t{v}" for n, v in sorted(set_rows)]
            )

        # ==============================================================================
        rep.h1("6. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  VP-1  exactly one WireGuard host in the VPN home (steps 1.1, 1.3; D4). The host's
        SHAPE - instance TYPE and ROOT VOLUME - is reported, not judged: both are slice
        parameters (vpn.md section S6), and each is named here when it leaves its
        baseline because the cost lines follow neither. The two are named separately
        because they are wrong differently - the type's gap is HOURLY and only while the
        host runs, the volume's is STANDING and survives a month nobody connects
  VP-2  the [P] Elastic IP exists and is associated with the host (step 2.1)
  VP-3  exactly one world-open ingress rule in the ESTATE: the home's UDP/51820, never
        port 22, nothing in any other account (step 3; every account since 6c 6.5)
  VP-4  IMDSv2 required on the host
  VP-5  the handshake log group exists, with retention (step 7)
  VP-6  the health alarm exists (step 7)
  VP-7  the persona sets carry the step 8 deny together, or not at all (8.2), each
        testing aws:SourceVpc as well as the address (the 2026-08-23 spelling);
        InfrastructureAccess must NOT carry it (open question 17, option a)
  VP-8  RETIRED 2026-08-18 - the GuardDuty reading moved to ./aws/guardduty.py
        (GD-1..GD-3) when GuardDuty left Stage 4 for Stage 15; the id is kept
        out of use so the Stage 4 log's VP-8 readings stay unambiguous
  VP-9  the [P] host-key secret carries its value-read deny and rotation is OFF
        (step 2.2a; decision 4, third review - the keys runbook's one rule)""")

        # ==============================================================================
        rep.h1("7. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/vpn.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 7)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 6)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
