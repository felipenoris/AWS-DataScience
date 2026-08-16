#!/usr/bin/env -S uv run --quiet
# slices.py - Stage 2 step 8. The teardown/rebuild tooling of D11, and the table behind it.
#
#   ./scripts/slices.py list [<env>]        the layer table, whole or for one account folder
#   ./scripts/slices.py check               table vs. disk - runs inside `make check`
#   ./scripts/slices.py up   --env <env>    start the [D] slices, apply the [E] ones
#   ./scripts/slices.py down --env <env>    delete the Studio apps, destroy [E], stop [D]
#   ./scripts/slices.py status [--env <env>] what is up, and the hourly burn
#
#   exit: 0 clean | 1 something failed | 2 a usage or refusal error
#
# THE MAKEFILE CALLS THIS AND OWNS NONE OF IT, the same division step 9 established: `make`
# names the bundles, scripts do the work, and Stage 8 moves them into a pipeline by adding a
# .gitlab-ci.yml line rather than by rewriting anything.
#
# EVERY SLICE ON DISK IS [P] TODAY, so `up` and `down` do nothing at all. That is the reason to
# write them now rather than later: the first [E] slice is Stage 3's `egress/` and the first
# [D] one is Stage 4's WireGuard `vpn/` (Stage 5's EFS is [P] - conventions 5.1 rule 2, D24),
# and both should arrive to a `make down` that already refuses what it must. It is step 8.6's
# argument applied to the whole target - a hook added later is a hook that was missing from the
# first teardown that needed it.
#
# THE FOUR REFUSALS OF 8.3, and where each is enforced:
#
#   1. never touch a [P] slice          layers.is_refused, per slice, reason printed
#   2. `down` with no ENV must fail     argparse `required=True` AND the Makefile guard - two
#                                       independent guards, because this is the one whose
#                                       failure mode is "destroy everything"
#   3. production/pki/ never destroyed  layers.NEVER_DESTROY (D36), independent of its layer
#   4. bootstrap/ unreachable, both     layers.NEVER_ANY_TARGET_SLICE_NAMES - it holds its own
#      targets                          state (step 2.2)
#
# HOW IT AUTHENTICATES, and it is not a detail: AWS_PROFILE is set ON EACH COMMAND, from
# backend.PROFILES, and no credential is ever exported into this process's environment. A
# borrowed session outlives the command that needed it and every later error names the wrong
# account (Lesson 25). --dry-run prints the exact commands and runs none of them, which is also
# how the Validation reads the plan instead of trusting the target list.

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from tfhygiene import backend, layers

LIVE = Path("terraform-live")
BOLD, RESET = "\033[1m", "\033[0m"


def run(cmd: list, env_extra: dict | None = None, dry: bool = False, capture: bool = False):
    """One subprocess, always announced. Nothing in this file runs a command it did not print."""
    shown = " ".join(f"{k}={v}" for k, v in (env_extra or {}).items())
    print(f"  $ {shown + ' ' if shown else ''}{' '.join(cmd)}")
    if dry:
        return None
    env = dict(os.environ)
    env.update(env_extra or {})
    if capture:
        return subprocess.run(cmd, env=env, capture_output=True, text=True)
    return subprocess.run(cmd, env=env)


def prepare(sl: layers.Slice, dry: bool) -> bool:
    """The two generated files and `init`. Both generators read ONE table (step 2.6)."""
    for gen in ("gen-tfvars.py", "gen-backend-hcl.py"):
        res = run([f"./scripts/{gen}", sl.account, sl.name], dry=dry, capture=True)
        if res is not None and res.returncode != 0:
            print(res.stderr.strip(), file=sys.stderr)
            return False
    res = run(
        ["terraform", f"-chdir={sl.path}", "init", "-backend-config=backend.hcl", "-input=false"],
        env_extra={"AWS_PROFILE": backend.profile(sl.account)},
        dry=dry,
    )
    return dry or res.returncode == 0


# ------------------------------------------------------------------ the two dormant hooks
#
# [D] IS "STOP, NEVER DESTROY" (D11), AND NOTHING ON DISK IS [D] YET. The first is Stage 4's
# WireGuard `vpn/` and the second Stage 7's GitLab EC2 with its EBS volume - conventions 5.1
# names exactly those two, and the EFS of `nfs/` is NOT among them: it is [P] by rule 2 (D24),
# which is the distinction to keep, since "stateful" is what makes a slice [D] *or* [P].
# These two functions exist so that the stage which
# creates the first [D] slice adds a body here instead of discovering that `make down` never
# had a place to put one - and they print what they did NOT do, because a hook that is silent
# when empty is indistinguishable from a hook that ran (Lesson 13).


def dormant(env: str, action: str, dry: bool) -> None:
    """[D] is stop/start and NEVER destroy (D11). Stage 4 step 1.3 gave this hook its body.

    THE INSTANCES ARE FOUND BY NAME TAG, NOT BY STATE FILE, and the tag is derived from the
    row rather than written a second time: `awsds-<env token>-<slice name>` is what a [D]
    slice's module already tags with, so `sandbox`+`vpn` is `awsds-sandbox-vpn` and Stage 7's
    GitLab row will be `awsds-prod-gitlab` without touching this function. Two consequences
    are worth naming. It keeps working when the slice's state is empty - it finds nothing and
    says which of the two nothings it found. And IT CANNOT DESTROY: the only mutating calls
    below are start-instances and stop-instances, so the refusal that matters most for a [D]
    slice is structural rather than a check that could be forgotten.

    EVERY OUTCOME IS PRINTED, including the ones that did nothing (Lesson 13). "No instance
    tagged X" and "already stopped" are different findings - the first means the slice was
    never applied or its host is gone, the second means the hook had nothing left to do - and
    a hook that reported both as silence would be indistinguishable from one that ran.
    """
    declared = [s for s in layers.for_env(env) if s.layer == layers.DORMANT]
    if not declared:
        print(f"  [D] none declared in {env} - nothing to {'start' if action == 'up' else 'stop'}")
        print("      (the first is Stage 4's WireGuard vpn/; Stage 7 adds GitLab's instance)")
        return

    token = backend.env_token(env)
    profile = backend.profile(env)
    verb, wanted, ready = (
        ("start", "running", "stopped") if action == "up" else ("stop", "stopped", "running")
    )

    for sl in declared:
        name = f"awsds-{token}-{sl.name}"
        res = run(
            [
                "aws",
                "ec2",
                "describe-instances",
                "--region",
                backend.REGION,
                "--filters",
                f"Name=tag:Name,Values={name}",
                "Name=instance-state-name,Values=pending,running,stopping,stopped",
                "--query",
                "Reservations[].Instances[].[InstanceId,State.Name]",
                "--output",
                "text",
            ],
            env_extra={"AWS_PROFILE": profile},
            dry=dry,
            capture=True,
        )
        if res is None:  # --dry-run: the command above was printed and not run
            print(f"    would {verb} whatever is tagged {name} and currently {ready}")
            continue
        if res.returncode != 0:
            print(f"    FAILED to read instances tagged {name}", file=sys.stderr)
            print(res.stderr.strip(), file=sys.stderr)
            raise SystemExit(1)

        found = [ln.split("\t") for ln in res.stdout.split("\n") if ln.strip()]
        if not found:
            print(f"    no instance tagged {name} - {sl.path} is not applied, or its host is gone")
            continue

        todo = [i for i, st in found if st == ready]
        for i, st in found:
            if st == wanted:
                print(f"    {i} already {wanted}")
            elif st != ready:
                # pending or stopping: acting now races the transition, so it is reported.
                print(f"    {i} is {st} - transitional, left alone; re-run when it settles")
        if not todo:
            continue

        res = run(
            [
                "aws",
                "ec2",
                f"{verb}-instances",
                "--region",
                backend.REGION,
                "--instance-ids",
                *todo,
            ],
            env_extra={"AWS_PROFILE": profile},
            dry=dry,
            capture=True,
        )
        if res is not None and res.returncode != 0:
            print(f"    FAILED to {verb} {', '.join(todo)}", file=sys.stderr)
            print(res.stderr.strip(), file=sys.stderr)
            raise SystemExit(1)
        print(
            f"    {verb}ped {', '.join(todo)}  ({name})"
            if verb == "stop"
            else f"    started {', '.join(todo)}  ({name})"
        )


def studio_apps(env: str, dry: bool) -> int:
    """Step 8.6's hook, and it guards its own obsolescence rather than passing quietly."""
    return (
        run(["./scripts/down-studio-apps.py", env], dry=dry) or subprocess.CompletedProcess([], 0)
    ).returncode


# ----------------------------------------------------------------------------- the targets


def cmd_list(args) -> int:
    rows = layers.for_env(args.env) if args.env else layers.all_slices()
    if not rows:
        print(f"no slice declared for env '{args.env}'. known: {', '.join(layers.environments())}")
        return 2
    print(f"{BOLD}rank  layer  slice{RESET}")
    for sl in rows:
        print(f"{sl.rank:>4}  [{sl.layer}]    {sl.path:<46} {sl.why}")
    print()
    for key, text in layers.LAYER_NAMES.items():
        n = len([s for s in rows if s.layer == key])
        print(f"  [{key}] {n:>2}  {text}")
    return 0


def cmd_check(args) -> int:
    """Table vs. disk, in both directions - the two-list shape of step 9.3."""
    failures = []

    on_disk = {(p.parent.parent.name, p.parent.name) for p in LIVE.glob("*/*/*.tf")}
    declared = {(s.account, s.name) for s in layers.SLICES}

    for account, name in sorted(on_disk - declared):
        failures.append(
            f"terraform-live/{account}/{name}/ holds .tf files and has NO ROW in "
            "scripts/tfhygiene/layers.py. `make down` would skip it in silence, which for an "
            "[E] slice is a bill. Add the row with its layer (step 8.1)."
        )
    for account, name in sorted(declared - on_disk):
        failures.append(
            f"layers.py declares {account}/{name} and there is no such slice on disk. "
            "A stale row makes the table stop being evidence."
        )
    for sl in layers.SLICES:
        if sl.account not in backend.PROFILES:
            failures.append(
                f"{sl.path}: account folder '{sl.account}' has no profile in backend.PROFILES, "
                "so up/down cannot reach it."
            )
        # The rank is READ from layers.RANKS rather than stored per row, so it cannot
        # disagree with itself; what a check can still catch is a name that has no rank at
        # all, which raises rather than defaulting to the end of the order.
        if sl.name not in layers.RANKS:
            failures.append(
                f"{sl.path}: slice name '{sl.name}' has no entry in layers.RANKS. A new slice "
                "declares its dependency order deliberately, never by defaulting."
            )
        if sl.layer not in layers.LAYER_NAMES:
            failures.append(f"{sl.path}: unknown layer '{sl.layer}'.")

    print(f"{len(declared)} slice(s) declared, {len(on_disk)} on disk")
    if failures:
        for f in failures:
            print(f"  FAIL  {f}")
        print(f"\n{BOLD}slice layers: {len(failures)} FAILED{RESET}")
        return 1
    print("  every slice on disk declares a layer, and every row has a slice")
    return 0


def cmd_updown(args) -> int:
    action = args.action
    if args.env not in layers.environments():
        print(
            f"unknown env '{args.env}'. known: {', '.join(layers.environments())}",
            file=sys.stderr,
        )
        return 2

    take, skipped = layers.actionable(args.env, action)

    print(f"{BOLD}make {action} ENV={args.env}{RESET}")
    print(f"\n  refused ({len(skipped)}), and the reason is printed rather than implied:")
    for sl, reason in skipped:
        print(f"    - {sl.path}: {reason}")

    if action == "down":
        print("\n  studio apps (step 8.6):")
        if not take:
            # THE HOOK NEEDS AN SSO SESSION AND THIS `down` DOES NOT. Running it anyway would
            # make a no-op `make down` fail on credentials, which is a target that reports a
            # problem it does not have. It rides on the session the destroy already needs.
            print("    skipped - nothing to destroy in this env, so this run opens no session")
        elif studio_apps(args.env, args.dry_run) != 0:
            return 1

    print("\n  dormant [D] (step 8.2):")
    dormant(args.env, action, args.dry_run)

    print(
        f"\n  ephemeral [E] ({len(take)}), in {'reverse ' if action == 'down' else ''}dependency order:"
    )
    if not take:
        print("    none - every slice in this env is refused above, so this is a NO-OP.")
        print("    The first [E] slice is Stage 3's egress/.")
        return 0

    for sl in take:
        print(f"\n  --- {sl.path}")
        if not prepare(sl, args.dry_run):
            print(f"    init failed for {sl.path}", file=sys.stderr)
            return 1
        cmd = ["terraform", f"-chdir={sl.path}", "destroy" if action == "down" else "apply"]
        if args.auto_approve:
            cmd.append("-auto-approve")
        res = run(cmd, env_extra={"AWS_PROFILE": backend.profile(sl.account)}, dry=args.dry_run)
        if res is not None and res.returncode != 0:
            return 1
    return 0


def managed_resources(module: dict) -> int:
    """Deployed resources in a state tree, RECURSIVELY and managed-only.

    Corrected 2026-08-16, on the first status reading of a real [E] slice. The previous
    count added `len(child_modules)` - one per module rather than one per resource - and
    counted data sources as deployed, so a sandbox/egress/ holding a NAT, an EIP, two
    routes and twelve endpoints reported "2 resource(s)": one remote-state data source
    plus the single module. The burn was right (it comes from the layers.py table, not
    from this number) but the line that reports what is RUNNING understated it by an
    order of magnitude, which is the half of the output a reader actually acts on.

    Managed-only is the other half of the fix: a data source is something the slice READS,
    never something it created, so a state holding nothing else is `down` - and `up` is
    derived from this count.
    """
    n = sum(1 for r in module.get("resources", []) if r.get("mode") == "managed")
    return n + sum(managed_resources(c) for c in module.get("child_modules", []))


def cmd_status(args) -> int:
    """What is up, and the burn - rates from a STATIC table, never a live pricing call (8.4)."""
    envs = [args.env] if args.env else layers.environments()
    metered = [
        s for e in envs for s in layers.for_env(e) if s.layer in (layers.DORMANT, layers.EPHEMERAL)
    ]

    print(f"{BOLD}status{RESET}  env(s): {', '.join(envs)}")
    if not metered:
        # NOT "0.00 USD/h". "Nothing is declared" and "everything is down" are different
        # answers and a status command that prints one for the other is Lesson 13 (see 8.4).
        print("\n  no [D] or [E] slice is DECLARED in this repository, so there is nothing")
        print("  hourly to be up. This is Stage 2: every slice on disk is [P]. The first")
        print("  metered slice is Stage 3's egress/, and it declares its own usd_per_hour")
        print("  in scripts/tfhygiene/layers.py from docs/PRICING.md 3.")
        print("\n  estimated burn: USD 0.00/h - because the set is empty, not because it was read")
        return 0

    total, unreadable = 0.0, 0
    for sl in metered:
        if not prepare(sl, args.dry_run):
            print(f"  {sl.path:<40} UNREADABLE")
            unreadable += 1
            continue
        res = run(
            ["terraform", f"-chdir={sl.path}", "show", "-json"],
            env_extra={"AWS_PROFILE": backend.profile(sl.account)},
            dry=args.dry_run,
            capture=True,
        )
        if res is None:
            continue
        if res.returncode != 0:
            print(f"  {sl.path:<40} UNREADABLE")
            unreadable += 1
            continue
        state = json.loads(res.stdout or "{}").get("values", {}).get("root_module", {})
        n = managed_resources(state)
        up = n > 0
        total += sl.usd_per_hour if up else 0.0
        print(
            f"  {sl.path:<40} {'UP' if up else 'down':<5} {n:>3} resource(s)"
            f"   {sl.usd_per_hour:.4f} USD/h"
        )

    print(f"\n  estimated burn: USD {total:.4f}/h   (rates: docs/PRICING.md 3, static)")
    if unreadable:
        # A slice that could not be read is not a slice that is down.
        print(f"  {unreadable} slice(s) UNREADABLE - this total is a floor, not a measurement")
        return 1
    return 0


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    ap = argparse.ArgumentParser(prog="slices.py", description="Stage 2 step 8 - D11 lifecycle")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list")
    p.add_argument("env", nargs="?")
    p.set_defaults(fn=cmd_list)

    sub.add_parser("check").set_defaults(fn=cmd_check)

    for action in ("up", "down"):
        p = sub.add_parser(action)
        # REFUSAL 2, first of its two guards: no default, no "all". `make down` with no ENV
        # must fail rather than mean everything.
        p.add_argument("--env", required=True)
        p.add_argument("--auto-approve", action="store_true")
        p.add_argument("--dry-run", action="store_true")
        p.set_defaults(fn=cmd_updown, action=action)
    p = sub.add_parser("status")
    p.add_argument("--env")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_status)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
