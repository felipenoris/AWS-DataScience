#!/usr/bin/env -S uv run --quiet
# check-gitlab-mirror.py - Stage 8 decision 16. Reads this repository's copy of the GitLab project
# awsds/dev-env (gitlab/awsds/dev-env/, written by scripts/gitlab-mirror.py) against the estate, for the
# two things the house image carries that the estate generates or declares: the NO_PROXY literal and
# the Bedrock settings. GitLab holds the recipe, so a failure here is a change to make there: the report
# names the file and the value, the user pushes the change to GitLab, and scripts/gitlab-mirror.py
# copies it back.
#
#   needs:    an SSO session as the infrastructure user, for the account's list (the Bedrock half
#             reads only this repository):
#
#                 aws sso login --sso-session awsds
#
#   run:      ./scripts/check-gitlab-mirror.py           # the list from sandbox/egress's state
#             ./scripts/check-gitlab-mirror.py --plan    # from a read-only plan of sandbox/egress,
#                                                        # for when the slice is down and its state
#                                                        # holds no outputs
#   reads:    s3:GetObject on awsds-sandbox-tfstate's sandbox/egress/terraform.tfstate and the
#             kms:Decrypt its key requires; with --plan, `terraform init` and `terraform plan` of
#             sandbox/egress, which apply nothing; the copy, gitlab/mirror.json, the SCP,
#             sandbox/bedrock/variables.tf and sandbox/probes/variables.tf
#   writes:   aws/output/gitlab-mirror-no-proxy.txt (untracked), the NO_PROXY_LIST line the
#             Dockerfile must carry, when GM-4 fails
#   exit:     0 every check passed | 1 a read failed | 2 a check FAILED
#
# The checks, each naming the file in GitLab its repair edits:
#
#   GM-1  the copy exists, and gitlab/mirror.json names the GitLab commit it holds
#   GM-2  dev-env/Dockerfile declares one NO_PROXY_LIST, on one line, with no whitespace in an entry
#   GM-3  the account's no_proxy_all_groups is readable
#   GM-4  the literal is that list exactly. A name only the account has leaves through the proxy and
#         succeeds without aws:SourceVpce; a name only the image has times out (aws/devenv.py's header)
#   GM-5  dev-env/Dockerfile's PROXY_URL is sandbox/probes' proxy URL
#   GM-6  dev-env/claude-code/managed-settings.json parses. Claude Code ignores an unparseable one
#         silently, and the session runs on the client's own defaults, against api.anthropic.com
#   GM-7  CLAUDE_CODE_USE_BEDROCK is "1" and AWS_REGION is the estate's region
#   GM-8  every pinned profile is one the SCP scopes and the grant slice grants, and every alias in
#         availableModels has a pin
#
# What it does not see: the image the registry holds (aws/devenv.py DE-5 reads those bytes), and
# whether GitLab still holds what the copy holds (scripts/gitlab-mirror.py --dry-run reads that).

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from awslib import profiles
from awslib.awscli import AwsCli, ErrorLog
from awslib.bedrockscope import (
    GRANT_VARS,
    SCP_PATH,
    grant_models,
    scp_declaration,
    settings_pins,
)
from awslib.devenvrecipe import (
    ARG_LIST_RE,
    ARG_PROXY_RE,
    DOCKERFILE,
    FULL_OUTPUT,
    MIRROR,
    MIRROR_PROJECT,
    MIRROR_RECORD,
    PROBES_PROXY_RE,
    PROBES_VARIABLES,
    SETTINGS,
    digest,
    entries,
)
from awslib.report import Checks, Report, failed_calls_epilogue
from tfhygiene import backend

ACCOUNT = "sandbox"
EGRESS = f"terraform-live/{ACCOUNT}/egress"
LINE_OUT = Path("aws/output/gitlab-mirror-no-proxy.txt")

# Where each file sits inside the GitLab project, for the repair instructions.
IN_GITLAB_DOCKERFILE = DOCKERFILE.removeprefix(f"{MIRROR}/")
IN_GITLAB_SETTINGS = SETTINGS.removeprefix(f"{MIRROR}/")


def run(cmd: list, profile: str, capture: bool = False) -> subprocess.CompletedProcess:
    """One subprocess as `profile`, announced first. A failure is returned, never raised."""
    print(f"  $ AWS_PROFILE={profile} {' '.join(cmd)}", file=sys.stderr)
    env = dict(os.environ, AWS_PROFILE=profile)
    return subprocess.run(cmd, env=env, capture_output=capture, text=True, stdin=subprocess.DEVNULL)


def list_from_state(cli: AwsCli) -> tuple[str | None, str]:
    """(no_proxy_all_groups, how it was read) out of the egress slice's state object."""
    bucket = f"awsds-{backend.env_token(ACCOUNT)}-tfstate"
    key = f"{ACCOUNT}/egress/terraform.tfstate"
    res = cli.run("s3", "cp", f"s3://{bucket}/{key}", "-", tolerate="NoSuchKey|Not Found|404")
    if res.tolerated:
        return None, f"no state object at s3://{bucket}/{key}"
    if not res.ok:
        return None, "the state read failed (section 5)"
    try:
        outputs = json.loads(res.stdout).get("outputs") or {}
    except json.JSONDecodeError as exc:
        return None, f"the state is not JSON: {exc}"
    value = outputs.get(FULL_OUTPUT, {}).get("value")
    if not value:
        return None, (
            f"the state holds no `{FULL_OUTPUT}`: the slice is down. Run again with --plan, or "
            f"`make up ENV={ACCOUNT} ONLY=egress` first"
        )
    return value, f"the state of {EGRESS}"


def list_from_plan(profile: str) -> tuple[str | None, str]:
    """(no_proxy_all_groups, how it was read) out of a plan of the egress slice, nothing applied."""
    for gen in ("gen-backend-hcl.py", "gen-tfvars.py"):
        res = run([f"./scripts/{gen}", ACCOUNT, "egress"], profile, capture=True)
        if res.returncode != 0:
            return None, f"{gen} exited {res.returncode}: {res.stderr.strip()}"
    tf = ["terraform", f"-chdir={EGRESS}"]
    res = run(
        tf + ["init", "-backend-config=backend.hcl", "-input=false", "-lockfile=readonly"],
        profile,
        capture=True,
    )
    if res.returncode != 0:
        return None, f"terraform init exited {res.returncode}: {res.stderr.strip()[-400:]}"
    with tempfile.TemporaryDirectory(prefix="check-gitlab-mirror-") as tmp:
        plan = Path(tmp) / "egress.tfplan"
        res = run(tf + ["plan", "-input=false", "-refresh=false", f"-out={plan}"], profile, True)
        if res.returncode != 0:
            return None, f"terraform plan exited {res.returncode}: {res.stderr.strip()[-400:]}"
        res = run(tf + ["show", "-json", str(plan)], profile, capture=True)
        if res.returncode != 0:
            return None, f"terraform show exited {res.returncode}: {res.stderr.strip()[-400:]}"
    outputs = json.loads(res.stdout).get("planned_values", {}).get("outputs", {})
    value = outputs.get(FULL_OUTPUT, {}).get("value")
    if not value:
        return None, f"the plan carries no known `{FULL_OUTPUT}`"
    return value, f"a plan of {EGRESS}"


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])
    parser = argparse.ArgumentParser(
        description="Check the copy of awsds/dev-env under gitlab/ against the estate."
    )
    parser.add_argument(
        "--plan", action="store_true", help="read the account's list from a plan of sandbox/egress"
    )
    args = parser.parse_args(argv)

    profile = backend.profile(ACCOUNT)
    errors = ErrorLog()
    checks = Checks()
    repairs: list = []

    # ------------------------------------------------------------------------------- the copy
    record = {}
    if Path(MIRROR_RECORD).is_file():
        record = json.loads(Path(MIRROR_RECORD).read_text(encoding="utf-8")).get(MIRROR_PROJECT, {})
    if not Path(MIRROR).is_dir():
        checks.fail("GM-1", "the copy exists", f"no {MIRROR}/ - run scripts/gitlab-mirror.py")
    elif not record:
        checks.note(
            "GM-1",
            "the copy exists",
            f"{MIRROR}/ was never copied from GitLab: what it holds is this repository's proposal",
        )
    else:
        checks.ok(
            "GM-1",
            "the copy exists",
            f"{MIRROR_PROJECT} {record['commit'][:12]} of {record['committed']}, {record['subject']}",
        )

    # ------------------------------------------------------------------------- the NO_PROXY half
    baked = None
    baked_proxy = None
    if not Path(DOCKERFILE).is_file():
        checks.fail("GM-2", "the Dockerfile declares one NO_PROXY_LIST", f"no {DOCKERFILE}")
    else:
        text = Path(DOCKERFILE).read_text(encoding="utf-8")
        found = ARG_LIST_RE.findall(text)
        proxy = ARG_PROXY_RE.search(text)
        baked_proxy = proxy.group("value") if proxy else None
        bad = (
            [n for n in entries(found[0]) if n.strip() != n or " " in n] if len(found) == 1 else []
        )
        if len(found) != 1:
            checks.fail(
                "GM-2",
                "the Dockerfile declares one NO_PROXY_LIST",
                f'{len(found)} `ARG NO_PROXY_LIST="..."` line(s), where one is the rule',
            )
            repairs.append(
                f'{IN_GITLAB_DOCKERFILE}: keep exactly one `ARG NO_PROXY_LIST="..."` line, on one line'
            )
        elif bad:
            checks.fail(
                "GM-2",
                "the Dockerfile declares one NO_PROXY_LIST",
                f"{len(bad)} entry(ies) carry whitespace, e.g. {bad[0]!r}",
            )
            repairs.append(f"{IN_GITLAB_DOCKERFILE}: remove the whitespace inside NO_PROXY_LIST")
        else:
            baked = found[0]
            checks.ok(
                "GM-2",
                "the Dockerfile declares one NO_PROXY_LIST",
                f"{len(entries(baked))} entries, sha256 {digest(baked)}",
            )

    full = None
    callers = profiles.preflight([profile], errors)
    if callers[0].live:
        if args.plan:
            full, how = list_from_plan(profile)
        else:
            full, how = list_from_state(
                AwsCli(profile=profile, region=backend.REGION, errors=errors)
            )
        if full is None:
            checks.fail("GM-3", "the account's list is readable", how)
        else:
            checks.ok(
                "GM-3",
                "the account's list is readable",
                f"{len(entries(full))} entries, sha256 {digest(full)}, from {how}",
            )

    missing, stale = [], []
    if baked is not None and full is not None:
        missing = sorted(set(entries(full)) - set(entries(baked)))
        stale = sorted(set(entries(baked)) - set(entries(full)))
        if missing or stale or baked != full:
            what = (
                f"{len(missing)} name(s) only in the account, {len(stale)} only in the image"
                if missing or stale
                else "the same names in another order, so /opt/awsds-proxy.txt's digest differs"
            )
            checks.fail("GM-4", "the literal is the account's list", what)
            LINE_OUT.parent.mkdir(parents=True, exist_ok=True)
            LINE_OUT.write_text(f'ARG NO_PROXY_LIST="{full}"\n', encoding="utf-8")
            repairs.append(
                f"{IN_GITLAB_DOCKERFILE}: replace the ARG NO_PROXY_LIST line with the one in "
                f"{LINE_OUT} ({len(entries(full))} entries, sha256 {digest(full)}) and date the "
                "comment above it"
            )
        else:
            checks.ok(
                "GM-4",
                "the literal is the account's list",
                f"{len(entries(full))} names, sha256 {digest(full)} on both sides",
            )
    else:
        checks.note("GM-4", "the literal is the account's list", "one side was not read")

    expected_proxy = None
    if Path(PROBES_VARIABLES).is_file():
        match = PROBES_PROXY_RE.search(Path(PROBES_VARIABLES).read_text(encoding="utf-8"))
        expected_proxy = match.group("value") if match else None
    if baked_proxy is None or expected_proxy is None:
        checks.note("GM-5", "the proxy URL agrees", "one of the two values was not found")
    elif baked_proxy != expected_proxy:
        checks.fail("GM-5", "the proxy URL agrees", f"{baked_proxy} against {expected_proxy}")
        repairs.append(f"{IN_GITLAB_DOCKERFILE}: ARG PROXY_URL={expected_proxy}")
    else:
        checks.ok("GM-5", "the proxy URL agrees", baked_proxy)

    # -------------------------------------------------------------------------- the Bedrock half
    settings = None
    if not Path(SETTINGS).is_file():
        checks.fail("GM-6", "the managed settings parse", f"no {SETTINGS}")
    else:
        try:
            settings = json.loads(Path(SETTINGS).read_text(encoding="utf-8"))
            checks.ok("GM-6", "the managed settings parse", SETTINGS)
        except json.JSONDecodeError as exc:
            checks.fail("GM-6", "the managed settings parse", str(exc))
            repairs.append(f"{IN_GITLAB_SETTINGS}: make it valid JSON ({exc})")

    if settings is not None:
        env = settings.get("env", {})
        wrong = []
        if env.get("CLAUDE_CODE_USE_BEDROCK") != "1":
            wrong.append(
                f'CLAUDE_CODE_USE_BEDROCK is {env.get("CLAUDE_CODE_USE_BEDROCK")!r}, not "1"'
            )
        if env.get("AWS_REGION") != backend.REGION:
            wrong.append(f"AWS_REGION is {env.get('AWS_REGION')!r}, not {backend.REGION!r}")
        if wrong:
            checks.fail("GM-7", "the session is held on Bedrock", "; ".join(wrong))
            repairs += [f"{IN_GITLAB_SETTINGS}: env.{w}" for w in wrong]
        else:
            checks.ok("GM-7", "the session is held on Bedrock", f"Bedrock, {backend.REGION}")

        declared, _regions, why = scp_declaration(Path(SCP_PATH))
        grant = grant_models(Path(GRANT_VARS))
        pins = settings_pins(Path(SETTINGS)) or {}
        if declared is None or grant is None:
            checks.note(
                "GM-8", "every pin is scoped and granted", why or f"{GRANT_VARS} unreadable"
            )
        else:
            problems = []
            for key, pin in sorted(pins.items()):
                if pin not in declared.values():
                    problems.append(f"{key} pins {pin}, which the SCP does not scope")
                if pin not in grant.values():
                    problems.append(f"{key} pins {pin}, which {GRANT_VARS} does not grant")
            for alias in settings.get("availableModels", []):
                if f"ANTHROPIC_DEFAULT_{alias.upper()}_MODEL" not in pins:
                    problems.append(f"availableModels offers {alias!r}, which no pin names")
            if not pins:
                problems.append("no model is pinned")
            if problems:
                checks.fail("GM-8", "every pin is scoped and granted", "; ".join(problems))
                scoped = ", ".join(sorted(declared.values()))
                repairs.append(f"{IN_GITLAB_SETTINGS}: pin only scoped profiles ({scoped})")
            else:
                checks.ok(
                    "GM-8",
                    "every pin is scoped and granted",
                    f"{len(set(pins.values()))} profile(s), each in the SCP and the grant",
                )

    # ------------------------------------------------------------------------------- the report
    rep = Report(sys.stdout)
    rep.banner("The copy of awsds/dev-env, against the estate")
    rep.line(f"copy      : {MIRROR}/")
    rep.line(f"profile   : {profile}")
    rep.line(f"list from : {'a plan of ' + EGRESS if args.plan else 'the state of ' + EGRESS}")
    section = iter(range(1, 5))
    if missing or stale:
        rep.h1(f"{next(section)}. The names that differ")
        for name in missing:
            rep.line(f"  only in the account : {name}")
        for name in stale:
            rep.line(f"  only in the image   : {name}")
    rep.h1(f"{next(section)}. Checks")
    rep.checks_table(checks)
    if repairs:
        rep.h1(f"{next(section)}. What to change in GitLab, project awsds/dev-env")
        for line in repairs:
            rep.line(f"  - {line}")
        rep.line("")
        rep.line("  Push the change to GitLab, then copy it back: ./scripts/gitlab-mirror.py")
    if errors:
        rep.h1(f"{next(section)}. Calls that failed")
        failed_calls_epilogue(rep, errors)

    if checks.n_fail():
        return 2
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
