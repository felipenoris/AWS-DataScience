"""Which profiles to measure, and which of them authenticate right now.

The multi-profile scripts (AZs, account-bpa, declarative-ec2, tf-backends, networking,
egress) share one preflight: enumerate the ``awsds-*`` profiles (or take the ones named on
the command line), ask ``sts get-caller-identity`` through each, and split them into the
live set the report measures and the ``(failed)`` rows section 1 shows. A failed profile is
excluded from every check and never counted as compliant - the preflight is where that rule
is enforced once.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass

from . import context
from .awscli import AwsCli, ErrorLog
from .report import note


def discover(prefix: str = context.PROFILE_PREFIX) -> list:
    """Every matching profile in ~/.aws/config, sorted - or [] when none/no aws CLI."""
    try:
        proc = subprocess.run(
            ["aws", "configure", "list-profiles"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    return sorted(p for p in proc.stdout.splitlines() if p.startswith(prefix))


def select(argv: list, prefix: str = context.PROFILE_PREFIX):
    """The scripts' shared argument convention: names on the command line, else discovery.

    Returns ``(profiles, source_description)``; exits 1 with the shell's message when
    nothing matched.
    """
    if argv:
        return list(argv), "named on the command line"
    profiles = discover(prefix)
    source = f"every '{prefix}*' profile in ~/.aws/config"
    if not profiles:
        note(f"no profiles to measure ({source} matched nothing)")
        sys.exit(1)
    return profiles, source


@dataclass
class Caller:
    """One profile's preflight answer."""

    profile: str
    account: str | None  # None when the profile did not authenticate
    arn: str | None

    @property
    def live(self) -> bool:
        return self.account is not None


def preflight(
    profiles: list,
    errors: ErrorLog,
    region: str = context.REGION,
    out_label: str = "",
) -> list:
    """sts:GetCallerIdentity through every profile; one Caller per profile, in order.

    Progress goes to stderr exactly as before (``  <profile>  OK`` / ``FAILED``). When no
    profile authenticates the script cannot measure anything: say how to log in and exit 1,
    leaving any previous report untouched.
    """
    note(f"region: {region}")
    callers = []
    for p in profiles:
        cli = AwsCli(profile=p, region=region, errors=errors, echo_profile=True)
        res = cli.call("sts", "get-caller-identity", "--query", "[Account,Arn]", "--output", "text")
        if res.ok:
            fields = res.stdout.split()
            callers.append(Caller(p, fields[0], fields[1] if len(fields) > 1 else "-"))
            note(f"  {p}  OK")
        else:
            errors.add(("sts", "get-caller-identity"), res.merged, p)
            callers.append(Caller(p, None, None))
            note(f"  {p}  FAILED")
    if not any(c.live for c in callers):
        note("")
        note("no profile authenticated. log in first:")
        note(f"  aws sso login --sso-session {context.SSO_SESSION}")
        if out_label:
            note("")
            note(f"the previous {out_label}, if any, is left untouched.")
        sys.exit(1)
    return callers


def cli_for(profile: str, errors: ErrorLog, region: str = context.REGION) -> AwsCli:
    """An AwsCli for one profile of a multi-profile run, sharing the run's error log."""
    return AwsCli(profile=profile, region=region, errors=errors, echo_profile=True)
