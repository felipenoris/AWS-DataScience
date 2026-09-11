#!/usr/bin/env -S uv run --quiet
# buildbox.py - the [E] build host of Stage 6 step 5.0: bring it up, put the build context on
# it, open a shell, tear it down.
#
# A script of its own rather than `make up ENV=production`, because that target acts on every [E]
# slice in an account, which for Production means egress/, workloads-egress/, probes/ and this one
# - nothing in layers.py refuses it, so `make up` raises the build host too. A build session needs
# exactly two of the four: egress/, for the SSM endpoints that are the only door into the host,
# and this slice. `scripts/slices.py up --only <names>` can narrow an apply since 6c step 7.1, and
# is what `make hub-up` is built on. What a narrowed apply still cannot do is the rest of a build
# session: the two prerequisite checks below (one of them in another account, which no rank can
# express), the context sync, the shell and the teardown.
#
# It moved accounts at 6c step 5.8, and both its refusals changed with the design. D38 removed
# every default route and put the WireGuard host in another VPC, where a route cannot point at
# it. What replaced that one dependency is two, and neither is in this slice:
#
#   the shell     `production/egress/`'s `ssm` / `ssmmessages` / `ec2messages` endpoints (5.5).
#                 Without them the agent cannot register and there is no way into the host.
#   the internet  `production/proxy/` in VPC-Networking, reached over a peering. A build that
#                 cannot reach it fails on every package source at once.
#
# What it refuses, each refusal here rather than in a comment (Lesson 5):
#
#   1. `up` with `production/egress/` down. The SSM endpoints are this host's only management
#      path, and their absence produces the most misleading symptom in the set: the apply
#      succeeds, the instance runs, and `ssm start-session` says it is not connected, which
#      reads as a slow boot for as long as anyone is willing to wait (Lesson 52).
#   2. `up` with the proxy host not running. `up` starts it rather than failing: the [D]
#      contract is stop/start, so starting one is not a change of state anybody has to approve.
#   3. `sync` and `ssm` against a host that is not `Online` in Session Manager, with the
#      PingStatus printed. An empty answer and a failed answer are different things
#      (Lesson 13).
#
# There is no refusal about `sandbox/probes/`. It existed because that slice's perimeter probe
# measures the Sandbox isolated tier's absence of a default route while this slice's mechanism
# was adding one there; this slice creates no route anywhere now and is not in that account. A
# guard that no longer guards anything is the one a later reader trusts by mistake.
#
# What `down` does not do: stop the proxy, or tear down `egress/`. This script owns one [E]
# slice; the proxy is [D], it is the whole estate's single egress, and stopping it because a
# build finished would cut off every other account. `make hub-down` is what stops it, and it is
# the user's call.
#
# The one write that is not terraform is `sync`, fenced the way ./aws/vpn.py --on-host is, and it
# has two transports. Both put the same deterministic tar of images/ at /opt/awsds/images, and
# both verify it by digest on the host before extracting: a transfer that arrives short would
# otherwise leave a tree missing a file nobody looks for.
#
#   --via ssh   the default. The tarball rides the SSH channel through the Session Manager
#               tunnel, on a key EC2 Instance Connect authorises for sixty seconds. Nothing new
#               is opened on the host: no listening port, no security group rule, no traffic
#               through the proxy - the laptop talks to the SSM API and the agent connects to
#               sshd on localhost. Write api: ec2-instance-connect:SendSSHPublicKey.
#   --via ssm   the fallback, needing no ssh client. The tarball is base64 inside SendCommand,
#               which caps document and parameters together at 97 KB - so it is sent in chunks
#               and reassembled. Write api: ssm:SendCommand.
#
# Why the default moved on 2026-09-10: the Python environment's uv.lock put the context at 235 KB
# of base64 and the single-command form failed outright. Chunking answered that, and the ssh path
# answers the next one too, because a build context only grows. The alternatives both routes were
# chosen over: user data caps at 16 KB, a git clone needs a credential on a throwaway host, and an
# S3 hop needs a bucket and a grant on a role that today holds nothing but Session Manager.
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
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tfhygiene import backend, layers  # noqa: E402

ACCOUNT = "production"
SLICE = "buildbox"
CONTEXT = Path("images")
REMOTE_DIR = "/opt/awsds/images"

# Where the base64 is reassembled on the host, and how much of it travels per SendCommand.
#
# The API caps the document and every parameter together at 97 KB, and the build context passed it
# on 2026-09-10: images/dev-env/python/uv.lock made the payload 235 KB of base64 and `sync` failed
# with MaxDocumentSizeExceeded. 60 000 characters leaves the rest of each command generous room
# under the cap, and the transfer is verified rather than assumed - the host compares the digest of
# what it reassembled with the one this script computed (see cmd_sync).
REMOTE_USER = "ec2-user"
STAGING_TAR = "/tmp/awsds-images.tar.gz"
STAGING_B64 = "/tmp/awsds-images.b64"
CHUNK_CHARS = 60_000

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

    None means not present. A read that failed raises instead of returning None: the two must
    not collapse into one answer (Lesson 13), because "no buildbox" and "cannot see the
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


# The endpoint whose absence is the failure this script exists to make loud. `ssmmessages` rather
# than `ssm`: `ssm` carries the API and `ssmmessages` carries the session channel, so it is the
# one whose absence produces "the instance is not connected" on a host that is otherwise perfect.
SSM_SESSION_ENDPOINT = "ssmmessages"


# --------------------------------------------------------------------------- the refusals


def refuse_if_no_ssm_endpoints() -> None:
    """Refusal 1 - the SSM endpoints in this VPC are the only door into the host.

    With `production/egress/` down the apply succeeds, the instance reaches `running`, and
    `ssm start-session` reports it as not connected, which is indistinguishable from a slow
    boot for as long as anyone is willing to wait (Lesson 52). Read the endpoints instead,
    before the apply, where the answer is a yes or a no.
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
    and every `RUN` step in a build goes through this one host. `up` starts it rather than
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
    """This slice's row in the one layer table - never a second copy of its path or its rate.

    It raises if the row is missing: a slice this script can drive but `make status` cannot
    see would be an [E] host outside D11's accounting, the failure the table exists to
    prevent.
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
    """The second readiness question: the agent being reachable is not the box being usable.

    The SSM agent registers while cloud-init is still running, so `Online` arrives a minute or
    so before `dnf install docker` finishes - measured 2026-08-21, not guessed: a
    `docker --version` taken the moment `up` returned came back empty, with `systemctl
    is-active docker` saying `inactive` and the boot log mid-install. Printing "up. next: sync,
    ssm" at that instant is a readiness claim about the wrong thing (Lesson 13).
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


def instance_az(iid: str) -> str:
    """The instance's AZ, which EC2 Instance Connect asks for. Empty when the read fails."""
    res = sh(
        aws(
            "ec2",
            "describe-instances",
            "--instance-ids",
            iid,
            "--query",
            "Reservations[0].Instances[0].Placement.AvailabilityZone",
            "--output",
            "text",
        )
    )
    return res.stdout.strip() if res.returncode == 0 else ""


def sync_over_ssh(iid: str, tarball: bytes, digest: str) -> bool:
    """Send the context over the Session Manager tunnel, on a key that lives sixty seconds.

    Nothing new is opened on the host. The laptop talks to the SSM API; the service reaches the
    agent through the outbound channel it already holds - the ssm/ssmmessages/ec2messages
    interface endpoints 6c step 5.5 put in this VPC - and the agent connects to sshd on
    localhost. No security group rule, no listening port, and nothing through the proxy, which
    carries what the HOST initiates outbound and this is not.

    The key is ephemeral: EC2 Instance Connect authorises one login for sixty seconds and the
    host stores nothing, so the slice's property holds - zero authorized keys, the access path is
    IAM (production/buildbox/main.tf's IN section).

    The tarball travels on the connection's stdin rather than as a second scp hop: one
    connection, one key window, and the digest is checked on the host before anything is
    extracted, so a truncated transfer refuses instead of leaving a tree short of a file.
    """
    for tool in ("ssh", "ssh-keygen"):
        if shutil.which(tool) is None:
            print(f"{RED}{tool} is not on PATH{RESET} - use --via ssm.")
            return False

    with tempfile.TemporaryDirectory() as tmp:
        key = Path(tmp) / "id_ed25519"
        if sh(["ssh-keygen", "-t", "ed25519", "-N", "", "-q", "-f", str(key)]).returncode != 0:
            print(f"{RED}ssh-keygen failed{RESET}")
            return False

        print(
            f"  {YELLOW}this is a WRITE api{RESET} (ec2-instance-connect:SendSSHPublicKey), "
            "a public key the host honours for 60 seconds"
        )
        eic = [
            "ec2-instance-connect",
            "send-ssh-public-key",
            "--instance-id",
            iid,
            "--instance-os-user",
            REMOTE_USER,
            "--ssh-public-key",
            f"file://{key}.pub",
        ]
        az = instance_az(iid)
        if az:
            eic += ["--availability-zone", az]
        if sh(aws(*eic)).returncode != 0:
            print(f"{RED}the key was not delivered{RESET} - use --via ssm.")
            return False

        proxy = (
            f"aws ssm start-session --target %h --document-name AWS-StartSSHSession "
            f"--parameters portNumber=%p --region {backend.REGION} --profile {profile()}"
        )
        # accept-new against a throwaway known_hosts: the tunnel is addressed by instance id and
        # built by the SSM service itself, so the identity this would otherwise pin is one AWS
        # already asserts - and the file dies with the temporary directory either way.
        opts = [
            "-i",
            str(key),
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            f"UserKnownHostsFile={tmp}/known_hosts",
            "-o",
            f"ProxyCommand={proxy}",
        ]
        remote = "; ".join(
            [
                "set -eu",
                f"cat > {STAGING_TAR}",
                f'got="$(sha256sum {STAGING_TAR} | cut -d" " -f1)"',
                f'[ "$got" = "{digest}" ] || {{ echo "FATAL: received $got, expected {digest}" >&2; exit 1; }}',
                f"sudo rm -rf {REMOTE_DIR}",
                "sudo mkdir -p /opt/awsds",
                f"sudo tar xzf {STAGING_TAR} -C /opt/awsds",
                f"rm -f {STAGING_TAR}",
                f"sudo chown -R {REMOTE_USER}:{REMOTE_USER} /opt/awsds",
                f"ls -la {REMOTE_DIR}",
            ]
        )
        print(f"  ssh {REMOTE_USER}@{iid} through AWS-StartSSHSession - {len(tarball)} bytes")
        res = subprocess.run(
            ["ssh", *opts, f"{REMOTE_USER}@{iid}", remote],
            input=tarball,
            capture_output=True,
        )
        if res.stdout:
            print(res.stdout.decode(errors="replace"))
        if res.returncode != 0:
            print(res.stderr.decode(errors="replace").strip(), file=sys.stderr)
            print(f"{RED}the transfer failed{RESET} - retry, or fall back with --via ssm.")
            return False
        return True


def run_on_host(iid: str, script: list, label: str) -> bool:
    """One SendCommand, waited to a terminal status. True on Success.

    The 97 KB the API allows covers the document AND every parameter together, so a caller that
    sends data rather than a command is responsible for staying under it - see CHUNK_CHARS.
    """
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
        return False
    cid = res.stdout.strip()
    print(f"  {label}: command {cid} - waiting")
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
            if status != "Success" or label == "extract":
                print(got.stdout)
            return status == "Success"
    print(f"{RED}{label}: the command never reached a terminal status{RESET}")
    return False


def cmd_sync(args) -> int:
    print(f"{BOLD}buildbox sync{RESET} - {CONTEXT}/ -> {REMOTE_DIR}")
    print("  the WRITE api this verb uses is fenced the way ./aws/vpn.py --on-host is")
    iid = require_buildbox()
    if not ssm_online(iid):
        raise SystemExit(
            f"{RED}{iid} is not Online in Session Manager{RESET} - see the status above."
        )

    if not CONTEXT.is_dir():
        raise SystemExit(f"{RED}{CONTEXT}/ does not exist{RESET} - run from the repository root.")

    # A deterministic tar: sorted names and zeroed mtimes, so re-syncing an unchanged tree
    # produces an identical payload, and "did my edit land?" is answerable by comparing two
    # command ids rather than by trusting a timestamp.
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for f in sorted(CONTEXT.rglob("*")):
            if f.is_file():
                info = tar.gettarinfo(str(f), arcname=str(f))
                info.mtime, info.uid, info.gid = 0, 0, 0
                info.uname = info.gname = ""
                with f.open("rb") as fh:
                    tar.addfile(info, fh)
    tarball = buf.getvalue()
    digest = hashlib.sha256(tarball).hexdigest()
    files = sum(1 for f in CONTEXT.rglob("*") if f.is_file())
    print(f"  {len(tarball)} bytes of tar.gz for {files} files, sha256 {digest[:16]}")

    if getattr(args, "via", "ssh") == "ssh":
        return 0 if sync_over_ssh(iid, tarball, digest) else 1

    payload = base64.b64encode(tarball).decode()
    chunks = [payload[i : i + CHUNK_CHARS] for i in range(0, len(payload), CHUNK_CHARS)]
    print(f"  {len(payload)} bytes of base64, in {len(chunks)} command(s) of at most {CHUNK_CHARS}")

    # The transfer is staged and then verified, because a chunk that does not arrive leaves a tar
    # that extracts into a tree missing a file nobody looks for. The host compares the digest of
    # what it reassembled against the one computed here, and refuses to extract on a mismatch.
    for n, chunk in enumerate(chunks, start=1):
        redirect = ">" if n == 1 else ">>"
        if not run_on_host(
            iid,
            ["set -eu", f"printf '%s' '{chunk}' {redirect} {STAGING_B64}"],
            f"chunk {n}/{len(chunks)}",
        ):
            print(f"{RED}the transfer stopped at chunk {n}{RESET} - nothing was extracted.")
            return 1

    script = [
        "set -eu",
        f'got="$(base64 -d < {STAGING_B64} | sha256sum | cut -d" " -f1)"',
        f'[ "$got" = "{digest}" ] || {{ echo "FATAL: reassembled $got, expected {digest}" >&2; exit 1; }}',
        f"rm -rf {REMOTE_DIR}",
        "mkdir -p /opt/awsds",
        f"base64 -d < {STAGING_B64} | tar xzf - -C /opt/awsds",
        f"rm -f {STAGING_B64}",
        "chown -R ec2-user:ec2-user /opt/awsds",
        f"ls -la {REMOTE_DIR}",
    ]
    if not run_on_host(iid, script, "extract"):
        return 1
    print(f"\n  {BOLD}synced.{RESET} on the host:  cd {REMOTE_DIR}")
    return 0


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
    # Not captured: this is an interactive terminal, and the session-manager-plugin needs the
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
        if name == "sync":
            # `ssh` is the transport; `ssm` is the fallback that needs no ssh client and no
            # ec2-instance-connect, and pays for it with a cap the context has already passed
            # once (CHUNK_CHARS).
            p.add_argument("--via", choices=("ssh", "ssm"), default="ssh")
        p.set_defaults(fn=fn, auto_approve=False)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
