#!/usr/bin/env -S uv run --quiet
# down-studio-apps.py - the [E] half of a SageMaker Unified Studio project.
#
#   ./scripts/down-studio-apps.py <env>              delete every running app in that account
#   ./scripts/down-studio-apps.py <env> --dry-run    list what WOULD be deleted, delete nothing
#   ./scripts/down-studio-apps.py <env> --spaces     also delete the spaces (see the warning)
#   exit: 0 nothing left running | 1 could not look, or a delete failed | 2 usage
#
# A Studio app is metered by the hour (~USD 0.050/h for an ml.t3.medium JupyterLab,
# docs/PRICING.md 8) and it is created from the portal, by a person, through a blueprint, so
# `terraform destroy` does not reach it. Terraform owns none of it: conventions 6 and Stage 6
# step 8.3 put the DataZone domain, the project profiles, the sagemaker/ prerequisites and the
# per-project SageMaker AI domains in [P], and destroying any of them would orphan home storage
# and churn every id. That leaves the running apps as the only [E] piece, and this script is the
# whole of `make down`'s reach into it.
#
# The domain id is discovered, never pasted (conventions 6). The Tooling blueprint chose it; a
# paste would copy a value nobody in this repository owns (Lesson 3), and it would go stale the
# first time a project is recreated.
#
# Deleting a space is opt-in and deleting an app is not, because they are on different D11
# layers: Stage 6 step 8.3 puts only the running apps in [E]. A space is a home directory plus
# an EBS volume; the volume bills monthly rather than hourly, it survives the app, and it holds
# whatever the person had not committed yet. Project home directories are scratch by policy
# (notebooks live in git, data in S3), and that policy is a thing users are told rather than a
# thing this script enforces on a Friday evening. --spaces exists because step 8.2 names the
# enclosing spaces; the default does not use it.
#
# What it writes: sagemaker:DeleteApp, and with --spaces sagemaker:DeleteSpace. Nothing else.
# Every call goes through the account's own SSO profile, passed per command in the environment
# (Lesson 25).

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from tfhygiene import backend

# App statuses that are billing or on their way to it. `Deleted` and `Failed` are neither, and
# `Deleting` is already on the right path - re-issuing DeleteApp against it just errors.
LIVE_APP_STATUSES = {"InService", "Pending"}

# How long to wait for the apps to actually go away before deleting spaces. DeleteSpace is
# refused while a space still has an app, so --spaces has to wait for it.
DELETE_POLL_SECONDS = 10
DELETE_TIMEOUT_SECONDS = 600


def aws(profile: str, *args: str) -> tuple[int, str, str]:
    """One CLI call through one profile. Returns (rc, stdout, stderr) - never raises."""
    proc = subprocess.run(
        ["aws", *args, "--region", backend.REGION, "--profile", profile, "--output", "json"],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def fail_to_look(env: str, profile: str, what: str, stderr: str) -> int:
    """A hook that cannot look must not report an empty result.

    The defence against the benign failure (an expired token) is what hides the serious one
    (a domain full of running apps) - Lesson 24, and Lesson 13. `make down` reads this return
    code, so an unreadable account stops the teardown instead of passing through it.
    """
    print(f"    could not {what} in {env} ({profile}) - this is NOT evidence that")
    print("    no app is running. Log in first:  aws sso login --sso-session awsds")
    last = stderr.strip().splitlines()[-1] if stderr.strip() else ""
    if last:
        print(f"    {last}")
    return 1


def list_domains(env: str, profile: str) -> list | int:
    rc, out, err = aws(profile, "sagemaker", "list-domains")
    if rc != 0:
        return fail_to_look(env, profile, "list domains", err)
    return json.loads(out or "{}").get("Domains", [])


def list_live_apps(profile: str, domain_id: str) -> list:
    rc, out, err = aws(profile, "sagemaker", "list-apps", "--domain-id-equals", domain_id)
    if rc != 0:
        raise RuntimeError(f"list-apps failed for {domain_id}: {err.strip()}")
    return [
        a for a in json.loads(out or "{}").get("Apps", []) if a.get("Status") in LIVE_APP_STATUSES
    ]


def delete_app(profile: str, app: dict) -> tuple[int, str]:
    """DeleteApp needs the app's owner, and an app has one of two kinds.

    SMUS provisions space-owned apps (a project space, shared or private); the classic
    Studio flow makes user-profile-owned ones. Passing the wrong one is a ValidationException,
    so the owner is read off the app rather than assumed: this account may hold both if
    anything predates Stage 6.
    """
    owner = (
        ["--space-name", app["SpaceName"]]
        if app.get("SpaceName")
        else ["--user-profile-name", app["UserProfileName"]]
    )
    rc, _, err = aws(
        profile,
        "sagemaker",
        "delete-app",
        "--domain-id",
        app["DomainId"],
        "--app-type",
        app["AppType"],
        "--app-name",
        app["AppName"],
        *owner,
    )
    return rc, err.strip()


def wait_for_apps_gone(profile: str, domain_id: str) -> bool:
    """True when nothing is InService/Pending any more, False on timeout."""
    deadline = time.monotonic() + DELETE_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            if not list_live_apps(profile, domain_id):
                return True
        except RuntimeError as exc:
            print(f"    {exc}")
            return False
        time.sleep(DELETE_POLL_SECONDS)
    return False


def delete_spaces(profile: str, domain_id: str) -> int:
    rc, out, err = aws(profile, "sagemaker", "list-spaces", "--domain-id-equals", domain_id)
    if rc != 0:
        print(f"    could not list spaces of {domain_id}: {err.strip()}")
        return 1
    spaces = json.loads(out or "{}").get("Spaces", [])
    failures = 0
    for sp in spaces:
        rc, _, err = aws(
            profile,
            "sagemaker",
            "delete-space",
            "--domain-id",
            domain_id,
            "--space-name",
            sp["SpaceName"],
        )
        if rc != 0:
            print(f"    FAILED to delete space {sp['SpaceName']}: {err.strip()}")
            failures += 1
        else:
            print(f"    deleted space {sp['SpaceName']}  ({domain_id})")
    return failures


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    flags = {a for a in argv if a.startswith("--")}
    positional = [a for a in argv if not a.startswith("--")]
    if len(positional) != 1 or flags - {"--dry-run", "--spaces"}:
        print("usage: down-studio-apps.py <env> [--dry-run] [--spaces]", file=sys.stderr)
        return 2
    env = positional[0]
    dry = "--dry-run" in flags
    with_spaces = "--spaces" in flags

    try:
        profile = backend.profile(env)
    except backend.UnknownAccountFolder:
        print(f"unknown account folder: {env}", file=sys.stderr)
        return 2

    domains = list_domains(env, profile)
    if isinstance(domains, int):
        return domains
    if not domains:
        print(f"    no SageMaker domain in {env} - nothing to delete")
        return 0

    failures = 0
    touched: list[str] = []

    for domain in domains:
        domain_id = domain["DomainId"]
        try:
            apps = list_live_apps(profile, domain_id)
        except RuntimeError as exc:
            print(f"    {exc}")
            failures += 1
            continue

        if not apps:
            print(f"    {domain_id}: no running app")
        for app in apps:
            label = f"{app['AppType']}/{app['AppName']} ({app.get('SpaceName') or app.get('UserProfileName')})"
            if dry:
                print(f"    WOULD delete {label}  ({domain_id})")
                continue
            rc, err = delete_app(profile, app)
            if rc != 0:
                print(f"    FAILED to delete {label}: {err}")
                failures += 1
            else:
                print(f"    deleting {label}  ({domain_id})")
                touched.append(domain_id)

        if with_spaces and not dry:
            if touched and not wait_for_apps_gone(profile, domain_id):
                print(f"    {domain_id}: apps did not finish deleting - spaces left alone")
                failures += 1
                continue
            failures += delete_spaces(profile, domain_id)
        elif with_spaces and dry:
            print(f"    WOULD then delete every space of {domain_id}")

    if failures:
        print(f"    {failures} failure(s) - `make down` stops here rather than destroying")
        print("    the network under an app that is still billing.")
        return 1

    # The delete is asynchronous and the hour keeps billing until it finishes, so a report
    # saying "deleted" while the app is still Deleting would be one sentence for two different
    # states (Lesson 13). Wait, and say which one happened.
    if touched and not dry and not with_spaces:
        for domain_id in sorted(set(touched)):
            if wait_for_apps_gone(profile, domain_id):
                print(f"    {domain_id}: every app gone")
            else:
                print(f"    {domain_id}: still deleting after {DELETE_TIMEOUT_SECONDS}s -")
                print("      check ./aws/studio.py US-10 before calling the session closed")
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
