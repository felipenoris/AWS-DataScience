#!/usr/bin/env -S uv run --quiet
# buildbox.py - the [E] build host of Stage 6 step 5.0: bring it up, put the build context on
# it, open a shell, tear it down.
#
# WHY IT IS A SCRIPT OF ITS OWN AND NOT `make up ENV=production`. That target acts on EVERY [E]
# slice in an account, which for Production means egress/, workloads-egress/, probes/ AND this one
# - nothing in layers.py refuses it, so `make up` raises the build host too. A build session needs
# exactly two of the four - egress/, for the SSM endpoints that are the only door into the host,
# and this slice - and paying for the other two while a build runs is money for nothing.
# `scripts/slices.py up --only <names>` can narrow an apply since 6c step 7.1 (2026-09-07; it is
# what `make hub-up` is built on, and the Makefile exposes it for the hub pair alone), which
# retired the sentence that stood here until then - "slices.py has no per-slice targeting". What
# a narrowed apply still cannot do is the rest of a build session: the two prerequisite checks
# below (one of them in another account, which no rank can express), the context sync, the shell
# and the teardown. So this file drives the slice, deliberately, and says why.
#
# IT MOVED ACCOUNTS AT 6c STEP 5.8 (2026-09-06), AND BOTH ITS REFUSALS CHANGED WITH THE DESIGN.
# The host used to live in `sandbox/buildbox/` and reach the internet through a default route at
# the WireGuard host's ENI, in the Sandbox isolated tier. D38 removed every default route and put
# the WireGuard host in another VPC, where a route cannot point at it. What replaced that one
# dependency is two, and neither is in this slice:
#
#   the SHELL     `production/egress/`'s `ssm` / `ssmmessages` / `ec2messages` endpoints (5.5).
#                 Without them the agent cannot register and there is NO way into the host - not
#                 a degraded way, none. This is the refusal that used to be about a route.
#   the INTERNET  `production/proxy/` in VPC-Networking, reached over a peering. A build that
#                 cannot reach it fails on every package source at once.
#
# WHAT IT REFUSES, AND WHY EACH REFUSAL IS HERE RATHER THAN IN A COMMENT (Lesson 5):
#
#   1. `up` with `production/egress/` down. The SSM endpoints are this host's only management
#      path, and their absence produces the most misleading symptom in the set: the apply
#      SUCCEEDS, the instance runs, and `ssm start-session` says it is not connected - which
#      reads as a slow boot for as long as anyone is willing to wait (Lesson 52).
#   2. `up` with the proxy host not RUNNING. `up` starts it rather than failing - the [D]
#      contract is stop/start, so starting one is not a change of state anybody has to approve.
#   3. `sync` and `ssm` against a host that is not `Online` in Session Manager, with the
#      PingStatus printed. An empty answer and a failed answer are different things
#      (Lesson 13).
#
# THE REFUSAL THAT WAS DELETED RATHER THAN RETARGETED: `sandbox/probes/`. It existed because that
# slice's perimeter probe measures the Sandbox ISOLATED tier's absence of a default route while
# this slice's whole mechanism was adding one there. This slice creates no route anywhere now and
# is not in that account. A guard that no longer guards anything is worse than no guard - it is
# the one a later reader trusts by mistake.
#
# WHAT `down` DELIBERATELY DOES NOT DO: stop the proxy, or tear down `egress/`. This script owns
# one [E] slice; the proxy is [D], it is the whole estate's single egress, and stopping it because
# a build finished would cut off every other account. `make hub-down` is what stops it, and it is
# the user's call.
#
# THE ONE WRITE THAT IS NOT TERRAFORM - `sync`, and it is fenced the way ./aws/vpn.py
# --on-host is: ssm:SendCommand is a WRITE API. It is used here to place a tar of images/ on
# the host, because the build context has to get there somehow and every alternative was
# worse - a 27 KB base64 blob does not fit user data's 16 KB, a git clone needs a credential
# on a throwaway host, and an S3 hop needs a bucket and a grant for a file that lives for an
# hour. It sends no credential and reads nothing back but the command's own status.
#
#   run:   ./scripts/buildbox.py up         # apply the slice (starts the proxy host first)
#          ./scripts/buildbox.py sync       # copy images/ to /opt/awsds/images on the host
#          ./scripts/buildbox.py ssm        # interactive shell (needs session-manager-plugin)
#          ./scripts/buildbox.py status     # what is up, and what it is costing
#          ./scripts/buildbox.py down       # destroy the slice - the host and nothing else
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

ACCOUNT = "production"
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


def proxy_name() -> str:
    return f"awsds-{backend.env_token(ACCOUNT)}-proxy"


# The endpoint whose ABSENCE is the failure this script exists to make loud. `ssmmessages` rather
# than `ssm`: `ssm` carries the API and `ssmmessages` carries the SESSION channel, so it is the
# one whose absence produces "the instance is not connected" on a host that is otherwise perfect.
SSM_SESSION_ENDPOINT = "ssmmessages"


# --------------------------------------------------------------------------- the refusals


def refuse_if_no_ssm_endpoints() -> None:
    """Refusal 1 - the SSM endpoints in this VPC are the only door into the host.

    THE SYMPTOM THIS REPLACES IS THE MISLEADING KIND. With `production/egress/` down the apply
    succeeds, the instance reaches `running`, and `ssm start-session` reports it as not
    connected - which is indistinguishable from a slow boot for as long as anyone is willing to
    wait (Lesson 52: a wait whose only exit is success waits forever once its subject is gone).
    Read the endpoints instead, before the apply, where the answer is a yes or a no.
    """
    print(f"\n  {BOLD}refusal 1: the shell's path{RESET}")
    res = sh(
        aws(
            "ec2",
            "describe-vpc-endpoints",
            "--filters",
            f"Name=service-name,Values=com.amazonaws.{backend.REGION}.{SSM_SESSION_ENDPOINT}",
            "--query",
            "VpcEndpoints[?State==`available`].[VpcId]",
            "--output",
            "text",
        )
    )
    if res.returncode != 0 or not res.stdout.strip():
        raise SystemExit(
            f"\n{RED}REFUSED{RESET}: no available `{SSM_SESSION_ENDPOINT}` interface endpoint in "
            f"this account.\n"
            "  Session Manager is the ONLY way into the build host - no ingress rule, no public\n"
            "  address, and no default route to reach the public SSM API through. Without this\n"
            "  endpoint the apply would succeed and the host would be unreachable.\n"
            "  Bring it up first, and only it:  ./scripts/slices.py up --env production --only egress\n"
            "  (make up ENV=production would also raise workloads-egress/, probes/ and this host)"
        )
    print(f"    {SSM_SESSION_ENDPOINT} endpoint available in {res.stdout.split()[0]}")


def ensure_proxy_running() -> str:
    """Refusal 2 - the internet on this host is a proxy, and a stopped one has no fallback.

    Under design B there is no route to fail over to: every package source, every base image
    and every `RUN` step in a build goes through this one host. `up` STARTS it rather than
    refusing, because [D] is a stop/start contract (D11) and starting one is not a change of
    state anybody has to approve.
    """
    print(f"\n  {BOLD}refusal 2: the internet{RESET}")
    found = instance(proxy_name())
    if not found:
        raise SystemExit(
            f"\n{RED}REFUSED{RESET}: no {proxy_name()} instance exists.\n"
            "  The estate has ONE way to the internet and this is it (D38). Apply\n"
            "  terraform-live/production/proxy/ first (Stage 6c pass 4)."
        )
    iid, state = found
    if state == "running":
        print(f"    {proxy_name()} is running ({iid})")
        return iid
    print(f"    {proxy_name()} is {state} - starting it ([D] is stop/start, D11)")
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
    refuse_if_no_ssm_endpoints()
    ensure_proxy_running()
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
    print("  Refusal 1 read the ssmmessages endpoint before the apply, so the door was there -")
    print("  look at the host, not the path.")
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
    proxy = instance(proxy_name())
    print(
        f"\n  {buildbox_name():<28} {box[1] + ' ' + box[0] if box else 'absent (nothing billing)'}"
    )
    print(f"  {proxy_name():<28} {proxy[1] + ' ' + proxy[0] if proxy else 'absent'}")
    if box and box[1] == "running":
        ssm_online(box[0])
        print(f"\n  {YELLOW}billing{RESET}: the build host is up. ./scripts/buildbox.py down")
        print(
            f"  {YELLOW}and so is its path{RESET}: production/egress/ is a prerequisite of this "
            "host and bills while it is up"
        )
    return 0


def cmd_down(args) -> int:
    print(f"{BOLD}buildbox down{RESET} - destroying the host, and nothing else")
    print(
        "  the proxy is [D] and is the whole estate's single egress: this does NOT stop it\n"
        "  (make hub-down does). production/egress/ is [E] and is NOT torn down here either -\n"
        "  `make down ENV=production` owns that, and it still bills until you run it."
    )
    rc = terraform("destroy", args.auto_approve)
    if rc == 0:
        print(f"\n  {BOLD}down.{RESET} nothing of this slice is left; no route was ever created.")
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
