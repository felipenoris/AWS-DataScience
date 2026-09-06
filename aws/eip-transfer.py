#!/usr/bin/env -S uv run --quiet
# eip-transfer.py - Stage 6c step 4.2. Can the WireGuard Elastic IP move from Sandbox to
# Production, and what exactly are the two calls that would move it?
#
# WHY THIS EXISTS AS ITS OWN FILE. An Elastic IP transfer has FOUR documented refusals and
# they are not symmetrical in when they fire: three are visible on the source address before
# anything is called, and the fourth - the destination account being at its Elastic IP quota
# - is invisible from the source entirely. Worse, the refusal that costs a sitting fires at
# ACCEPT time and not at ENABLE time: `enable-address-transfer` on an ASSOCIATED address
# succeeds, and `accept-address-transfer` then answers `InvalidTransfer.AddressAssociated`
# with the transfer already pending and a seven-day clock running. So the reading that
# matters has to be taken across two accounts, before the first write, which is exactly what
# no single `describe-addresses` can do.
#
# THE ADDRESS IS THE ONE THING IN THIS ESTATE THAT MAY NOT CHANGE (Stage 4 step 2.1): every
# client `.conf` pins it as `Endpoint =`, and `DenyControlPlaneOffVpn` and the lake's bucket
# policy carry it as a branch. Transferring it is what keeps a cut-over that moves the tunnel
# between two AWS accounts invisible to every device. The fallback - a fresh allocation in
# Production - is a new `Endpoint` line in every configuration, which is a client-side edit
# in the stage's risk table and not the plan.
#
# IT PRINTS THE TWO WRITE COMMANDS AND RUNS NEITHER. `aws/` is a read-only folder (CLAUDE.md);
# the two calls are [Claude+] acts the user authorizes in chat, one at a time, and they are
# printed with the ids already resolved so that neither is retyped from prose (Lesson 38 - an
# identifier read out of prose is a claim, not a reading).
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             One login covers both profiles below: the cached token is keyed by the
#             sso-session name, not by profile or account (see aws/INDEX.md).
#
#   run:      ./aws/eip-transfer.py
#   writes:   aws/output/eip-transfer.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeAddresses, ec2:DescribeAddressTransfers, ec2:DescribeInstances,
#             servicequotas:GetServiceQuota, sts:GetCallerIdentity.  It never creates,
#             updates or deletes anything - including the transfer it prints.
#   exits:    0 every check passed - the transfer would be accepted
#             1 a call failed
#             2 a check FAILED - the transfer would be refused, and the row says which refusal
#
# EXIT 2 IS THE EXPECTED READING BEFORE STEP 4.4, and saying so here is the point (Lesson 50 -
# a check written to a stage's FINAL expectation is red for every pass until that stage ends).
# ET-2 fails while the address is still associated with the Sandbox host, because that is a
# true statement about the transfer: run 4.4, then run this again. What separates "not yet"
# from "never" is WHICH row is red - ET-2 clears with one destroy; ET-4 would not clear at all.
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing read look alike:
#   - Whether the ALLOCATION ID survives the transfer. It is not documented either way, and
#     no read taken before the transfer can answer it. That is verification 1 of this stage
#     and it decides 4.6's `import` id: re-run this file after the accept and read section 2.
#   - A quota INCREASE request in flight. `get-service-quota` returns the applied value; a
#     pending increase lives in `list-requested-service-quota-change-history`, which this
#     file does not read because a pending increase is not headroom.
#   - The destination account's IDENTITY beyond its profile. Account ids do not appear in
#     this repository's tracked files (aws/INDEX.md rule 1), so the destination is named by
#     profile and the id is resolved live for the printed command only.

from __future__ import annotations

import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "eip-transfer.txt"

# The address is resolved by its Name TAG and never by a literal id: an id in this file would
# be a copy of state that `sandbox/foundation/` owns, and the tag is the same seam
# scripts/slices.py already uses. The tag survives the address; the TRANSFER does not carry it
# (tags are reset), which is why section 4 says so and Terraform re-applies them at 4.6.
SOURCE_PROFILE = "awsds-infra-sandbox-1"
SOURCE_NAME_TAG = "awsds-sandbox-vpn"

DEST_PROFILE = "awsds-infra-prod"

# EC2-VPC Elastic IPs, the per-Region quota. Default five; adjustable. The transfer needs ONE
# free slot in the destination at ACCEPT time.
EIP_QUOTA_CODE = "L-0263D0A3"
EIP_QUOTA_SERVICE = "ec2"


def _addresses(cli: AwsCli) -> list:
    res = cli.run("ec2", "describe-addresses", "--output", "json")
    if not res.ok:
        return []
    try:
        return json.loads(res.text).get("Addresses", [])
    except json.JSONDecodeError:
        return []


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    # BOTH PROFILES ALWAYS, and the argv is ignored on purpose: this measurement is a
    # COMPARISON across two accounts, and a single-profile version of it answers nothing -
    # the same deliberate deviation from aws/INDEX.md's one-profile rule that AZs.py carries.
    selected = [SOURCE_PROFILE, DEST_PROFILE]
    source = f"{SOURCE_PROFILE} (source) + {DEST_PROFILE} (destination) - fixed, argv ignored"

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = {c.profile: c for c in callers if c.live}
    checks = Checks()

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    # --------------------------------------------------------------- 1. the source address
    addr: dict = {}
    source_rows: list = []
    if SOURCE_PROFILE in live:
        cli = cli_for(SOURCE_PROFILE)
        matches = [
            a
            for a in _addresses(cli)
            if any(
                t.get("Key") == "Name" and t.get("Value") == SOURCE_NAME_TAG
                for t in a.get("Tags", [])
            )
        ]
        if len(matches) == 1:
            addr = matches[0]
            checks.ok(
                "ET-1", "the address resolves", f"one allocation tagged Name={SOURCE_NAME_TAG}"
            )
        elif not matches:
            checks.fail(
                "ET-1",
                "the address resolves",
                f"no allocation tagged Name={SOURCE_NAME_TAG} - already transferred, or the tag moved",
            )
        else:
            checks.fail(
                "ET-1",
                "the address resolves",
                f"{len(matches)} allocations share Name={SOURCE_NAME_TAG} - the tag stopped being a key",
            )
    else:
        checks.note("ET-1", "the address resolves", f"{SOURCE_PROFILE} not live - not read")

    if addr:
        source_rows = [
            f"public IP\t{addr.get('PublicIp', '-')}\tthe value every client .conf pins",
            f"allocation\t{addr.get('AllocationId', '-')}\tthe id `enable-address-transfer` takes",
            f"association\t{addr.get('AssociationId') or '(none)'}\tmust be NONE at accept time (ET-2)",
            f"instance\t{addr.get('InstanceId') or '(none)'}\twhat holds it today",
            f"pool\t{addr.get('PublicIpv4Pool', '-')}\t`amazon` means not BYOIP/IPAM (ET-4)",
            f"customer-owned\t{addr.get('CustomerOwnedIp') or '(none)'}\ta CoIP cannot transfer (ET-4)",
            f"reverse DNS\t{addr.get('PtrRecord') or '(none)'}\tmust be NONE (ET-3)",
            f"border group\t{addr.get('NetworkBorderGroup', '-')}\tthe transfer is same-Region only (ET-5)",
        ]

        # ET-2 - the refusal that fires LATE. `enable-address-transfer` accepts an associated
        # address without complaint; the accept then answers InvalidTransfer.AddressAssociated
        # with the seven-day clock already running.
        if addr.get("AssociationId"):
            checks.fail(
                "ET-2",
                "the address is disassociated",
                f"still associated ({addr['AssociationId']}) - step 4.4 destroys the association; "
                "note that `make down` stops the host and does NOT disassociate",
            )
        else:
            checks.ok("ET-2", "the address is disassociated", "no AssociationId")

        if addr.get("PtrRecord"):
            checks.fail(
                "ET-3",
                "no reverse-DNS record",
                f"PtrRecord={addr['PtrRecord']} - InvalidTransfer.AddressCustomPtrSet; reset it first",
            )
        else:
            checks.ok("ET-3", "no reverse-DNS record", "PtrRecord unset")

        pool = addr.get("PublicIpv4Pool", "")
        coip = addr.get("CustomerOwnedIp") or addr.get("CustomerOwnedIpv4Pool")
        if pool == "amazon" and not coip:
            checks.ok(
                "ET-4",
                "an Amazon-provided address",
                "PublicIpv4Pool=amazon, no customer-owned pool",
            )
        else:
            checks.fail(
                "ET-4",
                "an Amazon-provided address",
                f"pool={pool or '(none)'} coip={coip or '(none)'} - BYOIP, IPAM and CoIP addresses "
                "do not transfer, and this is the one row that does not clear by waiting",
            )

        if addr.get("NetworkBorderGroup") == context.REGION:
            checks.ok("ET-5", "same Region", f"border group {context.REGION}")
        else:
            checks.fail(
                "ET-5",
                "same Region",
                f"border group {addr.get('NetworkBorderGroup', '(none)')} - a transfer never crosses Regions",
            )
    else:
        for cid, what in (
            ("ET-2", "the address is disassociated"),
            ("ET-3", "no reverse-DNS record"),
            ("ET-4", "an Amazon-provided address"),
            ("ET-5", "same Region"),
        ):
            checks.note(cid, what, "the address did not resolve - not read")

    # ------------------------------------------------- 2. the destination: headroom, arrivals
    dest_account = "(not read)"
    dest_used = None
    dest_quota = None
    dest_rows: list = []
    incoming: list = []
    if DEST_PROFILE in live:
        cli = cli_for(DEST_PROFILE)
        dest_account = live[DEST_PROFILE].account or "(not read)"
        dest_used = len(_addresses(cli))

        res = cli.run(
            "service-quotas",
            "get-service-quota",
            "--service-code",
            EIP_QUOTA_SERVICE,
            "--quota-code",
            EIP_QUOTA_CODE,
            "--output",
            "json",
        )
        if res.ok:
            try:
                dest_quota = int(json.loads(res.text)["Quota"]["Value"])
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                logerr(DEST_PROFILE, f"service-quotas get-service-quota {EIP_QUOTA_CODE}", str(exc))

        # Transfers already in flight, both directions. The destination sees `pending`
        # arrivals; a `disabled` row is one the source withdrew.
        res = cli.run("ec2", "describe-address-transfers", "--output", "json")
        if res.ok:
            try:
                incoming = json.loads(res.text).get("AddressTransfers", [])
            except json.JSONDecodeError:
                incoming = []

        if dest_quota is None:
            checks.note("ET-6", "the destination has a free slot", "the quota did not read")
        elif dest_used is not None and dest_used < dest_quota:
            checks.ok(
                "ET-6",
                "the destination has a free slot",
                f"{dest_used} of {dest_quota} used - {dest_quota - dest_used} free",
            )
        else:
            checks.fail(
                "ET-6",
                "the destination has a free slot",
                f"{dest_used} of {dest_quota} used - AddressLimitExceeded at accept time; "
                "the quota is adjustable, and a request is not headroom",
            )

        dest_rows = [
            f"profile\t{DEST_PROFILE}\tthe destination account",
            f"addresses held\t{dest_used if dest_used is not None else '(not read)'}\tbefore the transfer",
            f"quota ({EIP_QUOTA_CODE})\t{dest_quota if dest_quota is not None else '(not read)'}\tEC2-VPC Elastic IPs, per Region",
            f"transfers visible\t{len(incoming)}\tsection 3",
        ]
    else:
        checks.note(
            "ET-6", "the destination has a free slot", f"{DEST_PROFILE} not live - not read"
        )

    # ------------------------------------------------------- 3. transfers already in flight
    outgoing: list = []
    if SOURCE_PROFILE in live:
        cli = cli_for(SOURCE_PROFILE)
        res = cli.run("ec2", "describe-address-transfers", "--output", "json")
        if res.ok:
            try:
                outgoing = json.loads(res.text).get("AddressTransfers", [])
            except json.JSONDecodeError:
                outgoing = []

    pending = [t for t in outgoing + incoming if t.get("AddressTransferStatus") == "pending"]
    if not (SOURCE_PROFILE in live or DEST_PROFILE in live):
        checks.note("ET-7", "no transfer already pending", "neither profile is live - not read")
    elif pending:
        checks.fail(
            "ET-7",
            "no transfer already pending",
            f"{len(pending)} pending - accept or disable it before enabling another; "
            "the accept window is seven days and AWS notifies nobody",
        )
    else:
        checks.ok("ET-7", "no transfer already pending", "nothing in flight")

    # ------------------------------------------------------------------------- the report
    alloc = addr.get("AllocationId", "<the Sandbox allocation>")
    public_ip = addr.get("PublicIp", "<the address>")
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("eip-transfer - can the WireGuard address move to Production, and how?")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/eip-transfer.py   (index: aws/INDEX.md)

SECTIONS
  1. The source address, field by field
  2. The destination: headroom
  3. Transfers already in flight
  4. CHECKS
  5. The two write commands - PRINTED, NEVER RUN
  6. Calls that failed

HOW TO READ THIS FILE
  - EXIT 2 BEFORE STEP 4.4 IS EXPECTED. ET-2 is false while the Sandbox host still
    holds the address, and that is a true statement about the transfer rather than a
    defect. What separates "not yet" from "never" is WHICH row is red: ET-2 and ET-6
    clear with one action each, ET-4 does not clear at all.
  - THE REFUSALS ARE NOT SYMMETRICAL IN TIME. ET-2 and ET-6 fire at ACCEPT time, with
    the transfer already pending and a seven-day clock running. That is the whole
    reason this file is read before the first write and not after it.
  - THE TRANSFER RESETS TAGS. The address arrives in Production untagged; Terraform
    re-applies the project tag set on the apply that follows the import (4.6).""")

        rep.h1("1. The source address")
        if source_rows:
            rep.tabulate(
                [("field", "value", "why it matters")] + [tuple(r.split("\t")) for r in source_rows]
            )
        else:
            rep.line("  (not read - see the checks)")

        rep.h1("2. The destination: headroom")
        if dest_rows:
            rep.tabulate([("field", "value", "note")] + [tuple(r.split("\t")) for r in dest_rows])
        else:
            rep.line("  (not read - see the checks)")

        rep.h1("3. Transfers already in flight")
        rows = [("side", "address", "status", "accept by")]
        for label, transfers in (("source", outgoing), ("destination", incoming)):
            for t in transfers:
                rows.append(
                    (
                        label,
                        t.get("PublicIp", "-"),
                        t.get("AddressTransferStatus", "-"),
                        t.get("AddressTransferExpirationTimestamp", "-"),
                    )
                )
        if len(rows) == 1:
            rep.line("  none on either side")
        else:
            rep.tabulate(rows)
        rep.text("""
  A source can see an ACCEPTED transfer for 14 days after the fact; a destination sees
  pending arrivals. An empty listing on both sides means nothing has been enabled yet.""")

        rep.h1("4. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are:
  ET-1  exactly one allocation carries the Name tag - the seam this file resolves by
  ET-2  the address is DISASSOCIATED. InvalidTransfer.AddressAssociated is raised at
        ACCEPT time, not at enable time (step 4.4 is the remedy)
  ET-3  no reverse-DNS record - InvalidTransfer.AddressCustomPtrSet
  ET-4  an Amazon-provided address: not BYOIP, not IPAM, not CoIP. The one row that
        does not clear by waiting
  ET-5  the address stays in its Region - a transfer never crosses one
  ET-6  the destination is under its Elastic IP quota - AddressLimitExceeded, also at
        accept time. A pending increase request is not headroom
  ET-7  no transfer is already pending on either side""")

        rep.h1("5. The two write commands - PRINTED, NEVER RUN")
        rep.text(f"""
  Both are [Claude+] acts under docs/plan/stages/stage-06c-networking-hub.md step 4.5,
  authorized one at a time in chat. They are ONE SITTING: the accept window is seven
  days and AWS notifies nobody, so an enabled-but-unaccepted transfer is a thing only
  this file would ever find again.

  1. in the SOURCE account ({SOURCE_PROFILE}):

     aws --profile {SOURCE_PROFILE} --region {context.REGION} ec2 enable-address-transfer \\
         --allocation-id {alloc} \\
         --transfer-account-id {dest_account}

  2. in the DESTINATION account ({DEST_PROFILE}):

     aws --profile {DEST_PROFILE} --region {context.REGION} ec2 accept-address-transfer \\
         --address {public_ip}

  Then re-run this file. Section 2 will show the address in the destination and section 3
  the accepted row, and the ALLOCATION ID it reports is what step 4.6's `import` block
  takes - it is not documented whether that id survives, so it is read and never assumed.""")

        rep.h1("6. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/eip-transfer.py")

    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 6)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 4)")
        return 2
    note(f"wrote {out_label} (all checks passed - the transfer would be accepted)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
