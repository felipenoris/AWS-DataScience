#!/usr/bin/env -S uv run --quiet
# buildbox.py - the [E] build host of Stage 6 step 5.0: bring it up, put the build context on
# it, open a shell, tear it down.
#
# WHY IT IS A SCRIPT OF ITS OWN AND NOT `make up ENV=sandbox`. That target acts on EVERY [E]
# slice in an account, which for Sandbox means egress/ (a NAT gateway and twelve interface
# endpoints, 0.170 USD/h) and probes/ (Stage 3's instruments). A build session needs neither -
# it reaches the internet through the WireGuard host - and one of them, probes/, must NOT be
# up at the same time. `scripts/slices.py` has no per-slice targeting and giving it some would
# weaken the refusals it exists for, so this file drives one slice deliberately.
#
# WHAT IT REFUSES, AND WHY EACH REFUSAL IS HERE RATHER THAN IN A COMMENT (Lesson 5):
#
#   1. `up` while sandbox/probes/ exists. The perimeter probe's premise is that the isolated
#      tier has NO default route; this slice's mechanism is adding one. Up together, the
#      probe reports a perimeter finding that is an artefact of this host. A comment saying
#      "do not run these together" is an intention.
#   2. `up` with the WireGuard host not RUNNING. The route points at its ENI, so a stopped
#      host turns every request into a timeout that looks like a broken package mirror.
#      `up` starts it rather than failing - the [D] contract is stop/start, so starting one
#      is not a change of state anybody has to approve.
#   3. `sync` and `ssm` against a host that is not `Online` in Session Manager, with the
#      PingStatus printed. An empty answer and a failed answer are different things
#      (Lesson 13).
#
# WHAT `down` DELIBERATELY DOES NOT DO: stop the WireGuard host. This script owns one [E]
# slice; the tunnel is [D], it is shared with everything else in the account, and stopping it
# because a build finished would be this script reaching outside its own slice. `make down
# ENV=sandbox` is what stops it, and it is the user's call.
#
# THE ONE WRITE THAT IS NOT TERRAFORM - `sync`, and it is fenced the way ./aws/vpn.py
# --on-host is: ssm:SendCommand is a WRITE API. It is used here to place a tar of images/ on
# the host, because the build context has to get there somehow and every alternative was
# worse - a 27 KB base64 blob does not fit user data's 16 KB, a git clone needs a credential
# on a throwaway host, and an S3 hop needs a bucket and a grant for a file that lives for an
# hour. It sends no credential and reads nothing back but the command's own status.
#
#   run:   ./scripts/buildbox.py up         # apply the slice (starts the tunnel host first)
#          ./scripts/buildbox.py sync       # copy images/ to /opt/awsds/images on the host
#          ./scripts/buildbox.py ssm        # interactive shell (needs session-manager-plugin)
#          ./scripts/buildbox.py status     # what is up, and what it is costing
#          ./scripts/buildbox.py down       # destroy the slice - the host AND its route
#
#   needs: a live SSO session as the infrastructure user:  aws sso login --sso-session awsds

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tfhygiene import backend, layers  # noqa: E402

ACCOUNT = "sandbox"
SLICE = "buildbox"
CONTEXT = Path("images")
REMOTE_DIR = "/opt/awsds/images"

BOLD, RESET, RED, YELLOW = "\033[1m", "\033[0m", "\033[31m", "\033[33m"


def sh(cmd: list, capture: bool = True, check: bool = False):
    """One subprocess, always announced - the same rule scripts/slices.py works under."""
    print(f"  $ {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=capture, text=True)
    if check and res.returncode != 0:
        if capture:
            print(res.stderr.strip(), file=sys.stderr)
        raise SystemExit(1)
    return res


def profile() -> str:
    return backend.profile(ACCOUNT)


def aws(*args: str) -> list:
    return ["aws", *args, "--region", backend.REGION, "--profile", profile()]


def instance(name: str) -> tuple[str, str] | None:
    """(id, state) of a running-or-stopped instance by Name tag, or None if there is none.

    None means NOT PRESENT. A read that FAILED raises instead of returning None - the two
    must not collapse into one answer (Lesson 13), because "no buildbox" and "cannot see the
    account" lead to opposite next moves.
    """
    res = sh(
        aws(
            "ec2",
            "describe-instances",
            "--filters",
            f"Name=tag:Name,Values={name}",
            "Name=instance-state-name,Values=pending,running,stopping,stopped",
            "--query",
            "Reservations[].Instances[].[InstanceId,State.Name]",
            "--output",
            "text",
        )
    )
    if res.returncode != 0:
        print(res.stderr.strip(), file=sys.stderr)
        raise SystemExit(
            f"{RED}cannot read instances in {ACCOUNT}{RESET} - is the SSO session live?"
        )
    rows = [tuple(ln.split("\t")) for ln in res.stdout.split("\n") if ln.strip()]
    return rows[0] if rows else None


def buildbox_name() -> str:
    return f"awsds-{backend.env_token(ACCOUNT)}-{SLICE}"


def vpn_name() -> str:
    return f"awsds-{backend.env_token(ACCOUNT)}-vpn"


def probe_names() -> list[str]:
    token = backend.env_token(ACCOUNT)
    return [f"awsds-{token}-probe-perimeter", f"awsds-{token}-probe-peering"]


# --------------------------------------------------------------------------- the refusals


def refuse_if_probes_up() -> None:
    """Refusal 1 - the perimeter probe and this slice contradict each other."""
    print(f"\n  {BOLD}refusal 1: the perimeter probe's premise{RESET}")
    for name in probe_names():
        found = instance(name)
        if found:
            raise SystemExit(
                f"\n{RED}REFUSED{RESET}: {name} is {found[1]} ({found[0]}).\n"
                "  sandbox/probes/ measures that the isolated tier has NO default route.\n"
                "  This slice's whole mechanism is adding one, so up together the probe\n"
                "  reports a perimeter finding that is an artefact of the build host.\n"
                "  Tear the probes down first:  make down ENV=sandbox"
            )
    print("    clear - no probe instance in this account")


def ensure_vpn_running() -> str:
    """Refusal 2 - the route points at the WireGuard host's ENI, so it must be running."""
    print(f"\n  {BOLD}refusal 2: the route target{RESET}")
    found = instance(vpn_name())
    if not found:
        raise SystemExit(
            f"\n{RED}REFUSED{RESET}: no {vpn_name()} instance exists.\n"
            "  This slice routes 0.0.0.0/0 at that host's ENI; without it there is nothing\n"
            "  to point at. Apply terraform-live/sandbox/vpn/ first (Stage 4 pass 1)."
        )
    iid, state = found
    if state == "running":
        print(f"    {vpn_name()} is running ({iid})")
        return iid
    print(f"    {vpn_name()} is {state} - starting it ([D] is stop/start, D11)")
    sh(aws("ec2", "start-instances", "--instance-ids", iid), check=True)
    sh(aws("ec2", "wait", "instance-running", "--instance-ids", iid), capture=False, check=True)
    print(f"    started {iid} - note that `buildbox.py down` will NOT stop it again")
    return iid


def ssm_online(iid: str, quiet: bool = False) -> bool:
    """Refusal 3 - and it prints PingStatus rather than a boolean, so a wait is diagnosable."""
    res = sh(
        aws(
            "ssm",
            "describe-instance-information",
            "--filters",
            f"Key=InstanceIds,Values={iid}",
            "--query",
            "InstanceInformationList[].[PingStatus,AgentVersion]",
            "--output",
            "text",
        )
    )
    status = res.stdout.strip() or "(not registered)"
    if not quiet:
        print(f"    SSM: {status}")
    return res.returncode == 0 and status.startswith("Online")


def require_buildbox() -> str:
    found = instance(buildbox_name())
    if not found:
        raise SystemExit(
            f"\n{RED}no {buildbox_name()}{RESET} - bring it up first:  ./scripts/buildbox.py up"
        )
    iid, state = found
    if state != "running":
        raise SystemExit(f"\n{RED}{buildbox_name()} is {state}{RESET}, not running ({iid}).")
    return iid


# ------------------------------------------------------------------------------ the verbs


def row() -> layers.Slice:
    """This slice's row in the ONE layer table - never a second copy of its path or its rate.

    It raises if the row is missing, and that is right: a slice this script can drive but
    `make status` cannot see would be an [E] host outside D11's accounting, which is the
    exact failure the table exists to prevent.
    """
    for sl in layers.all_slices():
        if sl.account == ACCOUNT and sl.name == SLICE:
            return sl
    raise SystemExit(
        f"{RED}no row for {ACCOUNT}/{SLICE} in scripts/tfhygiene/layers.py{RESET} - "
        "an [E] slice with no row is one `make status` cannot see."
    )


def terraform(action: str, auto: bool) -> int:
    path = row().path

    for gen in ("gen-tfvars.py", "gen-backend-hcl.py"):
        sh([f"./scripts/{gen}", ACCOUNT, SLICE], check=True)

    env = dict(os.environ)
    env["AWS_PROFILE"] = profile()
    for cmd in (
        ["terraform", f"-chdir={path}", "init", "-backend-config=backend.hcl", "-input=false"],
        ["terraform", f"-chdir={path}", action, "-input=false"]
        + (["-auto-approve"] if auto else []),
    ):
        print(f"  $ AWS_PROFILE={env['AWS_PROFILE']} {' '.join(cmd)}")
        if subprocess.run(cmd, env=env).returncode != 0:
            return 1
    return 0


def wait_for_docker(iid: str) -> bool:
    """The SECOND readiness question, and `up` used to answer only the first (2026-08-21).

    The SSM agent registers while cloud-init is still running, so `Online` arrives a minute or
    so BEFORE `dnf install docker` finishes - measured, not guessed: a `docker --version` taken
    the moment `up` returned came back EMPTY, with `systemctl is-active docker` saying
    `inactive` and the boot log mid-install. Printing "up. next: sync, ssm" at that instant is
    a readiness claim about the wrong thing - the agent being reachable and the box being
    usable are two different measurements, and one was standing in for the other (Lesson 13).
    """
    for attempt in range(20):
        res = sh(
            aws(
                "ssm",
                "send-command",
                "--instance-ids",
                iid,
                "--document-name",
                "AWS-RunShellScript",
                "--parameters",
                json.dumps({"commands": ["systemctl is-active docker"]}),
                "--query",
                "Command.CommandId",
                "--output",
                "text",
            )
        )
        if res.returncode == 0:
            time.sleep(5)
            got = sh(
                aws(
                    "ssm",
                    "get-command-invocation",
                    "--command-id",
                    res.stdout.strip(),
                    "--instance-id",
                    iid,
                    "--query",
                    "StandardOutputContent",
                    "--output",
                    "text",
                )
            )
            if got.returncode == 0 and got.stdout.strip() == "active":
                print("    docker: active")
                return True
        print(f"    docker not up yet ({attempt + 1}) - the first boot is still installing")
        time.sleep(10)
    print(f"\n{RED}docker never came up.{RESET} Read /var/log/awsds-buildbox-boot.log over `ssm`.")
    return False


def cmd_up(args) -> int:
    print(f"{BOLD}buildbox up{RESET} - Stage 6 step 5.0's build host, in {ACCOUNT}")
    refuse_if_probes_up()
    ensure_vpn_running()
    print(f"\n  {BOLD}apply{RESET}")
    if terraform("apply", args.auto_approve) != 0:
        return 1

    found = instance(buildbox_name())
    if not found:
        # The apply returned 0 and there is no instance. That is not "wait longer" - it is a
        # state file describing something the account does not have, and the next command to
        # touch this slice should be a plan, not a retry.
        print(f"\n{RED}apply succeeded but no {buildbox_name()} exists.{RESET}")
        print("  Read the plan before doing anything else - the state and the account disagree.")
        return 1
    iid = found[0]
    print(f"\n  {BOLD}waiting for Session Manager{RESET} (first boot installs docker and git)")
    for attempt in range(30):
        if ssm_online(iid, quiet=attempt not in (0, 29)):
            print(f"\n  {BOLD}up{RESET} - the agent is online. Now the toolchain.")
            if not wait_for_docker(iid):
                return 1
            print(f"\n  {BOLD}ready.{RESET} next:")
            print("    ./scripts/buildbox.py sync     put images/ on the host")
            print("    ./scripts/buildbox.py ssm      open a shell")
            print(
                f"\n  {YELLOW}it is billing from now on{RESET} - "
                f"{row().usd_per_hour} USD/h (docs/PRICING.md 8). "
                "Finish with ./scripts/buildbox.py down"
            )
            return 0
        time.sleep(10)
    print(f"\n{RED}the host is up but never registered with Session Manager.{RESET}")
    print("  That is the route through the WireGuard host failing, nine times out of ten.")
    print(
        f"  Read the first boot without SSM:  aws ec2 get-console-output --instance-id {iid} --latest"
    )
    return 1


def cmd_sync(args) -> int:
    print(f"{BOLD}buildbox sync{RESET} - {CONTEXT}/ -> {REMOTE_DIR}")
    print(
        f"  {YELLOW}this is the one WRITE api in this file{RESET} (ssm:SendCommand), "
        "the ./aws/vpn.py --on-host fence"
    )
    iid = require_buildbox()
    if not ssm_online(iid):
        raise SystemExit(
            f"{RED}{iid} is not Online in Session Manager{RESET} - see the status above."
        )

    if not CONTEXT.is_dir():
        raise SystemExit(f"{RED}{CONTEXT}/ does not exist{RESET} - run from the repository root.")

    # A DETERMINISTIC TAR: sorted names and zeroed mtimes, so re-syncing an unchanged tree
    # produces an identical payload. It costs nothing and it makes "did my edit land?"
    # answerable by comparing two command ids rather than by trusting a timestamp.
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for f in sorted(CONTEXT.rglob("*")):
            if f.is_file():
                info = tar.gettarinfo(str(f), arcname=str(f))
                info.mtime, info.uid, info.gid = 0, 0, 0
                info.uname = info.gname = ""
                with f.open("rb") as fh:
                    tar.addfile(info, fh)
    payload = base64.b64encode(buf.getvalue()).decode()
    print(
        f"  {len(payload)} bytes of base64 for {sum(1 for f in CONTEXT.rglob('*') if f.is_file())} files"
    )

    script = [
        "set -eu",
        f"rm -rf {REMOTE_DIR}",
        "mkdir -p /opt/awsds",
        f"echo '{payload}' | base64 -d | tar xzf - -C /opt/awsds",
        "chown -R ec2-user:ec2-user /opt/awsds",
        f"ls -la {REMOTE_DIR}",
    ]
    res = sh(
        aws(
            "ssm",
            "send-command",
            "--instance-ids",
            iid,
            "--document-name",
            "AWS-RunShellScript",
            "--parameters",
            json.dumps({"commands": script}),
            "--query",
            "Command.CommandId",
            "--output",
            "text",
        )
    )
    if res.returncode != 0:
        print(res.stderr.strip(), file=sys.stderr)
        return 1
    cid = res.stdout.strip()
    print(f"  command {cid} - waiting")
    for _ in range(30):
        time.sleep(3)
        got = sh(
            aws(
                "ssm",
                "get-command-invocation",
                "--command-id",
                cid,
                "--instance-id",
                iid,
                "--query",
                "[Status,StandardOutputContent,StandardErrorContent]",
                "--output",
                "text",
            )
        )
        if got.returncode != 0:
            continue
        status = got.stdout.split("\t")[0].strip()
        if status in ("Success", "Failed", "Cancelled", "TimedOut"):
            print(got.stdout)
            if status == "Success":
                print(f"\n  {BOLD}synced.{RESET} on the host:  cd {REMOTE_DIR}")
                return 0
            return 1
    print(f"{RED}the command never reached a terminal status{RESET}")
    return 1


def cmd_ssm(args) -> int:
    print(f"{BOLD}buildbox ssm{RESET}")
    iid = require_buildbox()
    if not ssm_online(iid):
        raise SystemExit(
            f"{RED}{iid} is not Online in Session Manager{RESET} - see the status above."
        )
    print("\n  You land as ssm-user with passwordless sudo. The docker group belongs to")
    print("  ec2-user, so:  sudo docker ...   or   sudo -iu ec2-user")
    print(f"  Build context (after `sync`): {REMOTE_DIR}\n")
    # NOT captured: this is an interactive terminal, and the session-manager-plugin needs the
    # real stdin/stdout. It is also the one command in this file that does not return until
    # the user exits.
    return subprocess.run(aws("ssm", "start-session", "--target", iid)).returncode


def cmd_status(args) -> int:
    print(f"{BOLD}buildbox status{RESET} - {ACCOUNT}")
    box = instance(buildbox_name())
    vpn = instance(vpn_name())
    print(
        f"\n  {buildbox_name():<28} {box[1] + ' ' + box[0] if box else 'absent (nothing billing)'}"
    )
    print(f"  {vpn_name():<28} {vpn[1] + ' ' + vpn[0] if vpn else 'absent'}")
    if box and box[1] == "running":
        ssm_online(box[0])
        print(f"\n  {YELLOW}billing{RESET}: the build host is up. ./scripts/buildbox.py down")
    for name in probe_names():
        found = instance(name)
        if found:
            print(f"  {RED}{name}{RESET} is {found[1]} - it and the buildbox contradict each other")
    return 0


def cmd_down(args) -> int:
    print(f"{BOLD}buildbox down{RESET} - destroying the host AND its default route")
    print(
        "  the WireGuard host is [D] and shared: this does NOT stop it (make down ENV=sandbox does)"
    )
    rc = terraform("destroy", args.auto_approve)
    if rc == 0:
        print(f"\n  {BOLD}down.{RESET} the isolated tier has no default route again.")
    return rc


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])
    ap = argparse.ArgumentParser(
        prog="buildbox.py", description="Stage 6 step 5.0's [E] build host"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, needs_approve in (
        ("up", cmd_up, True),
        ("sync", cmd_sync, False),
        ("ssm", cmd_ssm, False),
        ("status", cmd_status, False),
        ("down", cmd_down, True),
    ):
        p = sub.add_parser(name)
        if needs_approve:
            p.add_argument("--auto-approve", action="store_true")
        p.set_defaults(fn=fn, auto_approve=False)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
