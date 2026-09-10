#!/usr/bin/env -S uv run --quiet
# slices.py - Stage 2 step 8. The teardown/rebuild tooling of D11, and the table behind it.
#
#   ./scripts/slices.py envs               the ENV values, and what each one acts on
#   ./scripts/slices.py list [<env>]        the layer table, whole or for one account folder
#   ./scripts/slices.py check               table vs. disk - runs inside `make check`
#   ./scripts/slices.py up   --env <env>    start the [D] slices, apply the [E] ones
#   ./scripts/slices.py down --env <env>    delete the Studio apps, destroy [E], stop [D]
#   ./scripts/slices.py status [--env <env>] what is up, and the hourly burn
#
#   exit: 0 clean | 1 something failed | 2 a usage or refusal error
#
# The Makefile calls this and owns none of it, the same division step 9 established: `make`
# names the bundles, scripts do the work, and Stage 8 moves them into a pipeline by adding a
# .gitlab-ci.yml line rather than by rewriting anything.
#
# The refusals - 8.3's four, and the one Stage 4's first [D] row exposed:
#
#   1. never touch a [P] slice          layers.is_refused, per slice, reason printed
#   2. `down` with no ENV must fail     argparse `required=True` and the Makefile guard - two
#                                       independent guards, because this is the one whose
#                                       failure mode is "destroy everything"
#   3. production/pki/ never destroyed  layers.NEVER_DESTROY (D36), independent of its layer
#   4. bootstrap/ unreachable, both     layers.NEVER_ANY_TARGET_SLICE_NAMES - it holds its own
#      targets                          state (step 2.2)
#   5. a [D] slice is never destroyed   layers.is_refused on the layer. Nothing said this while
#      and never applied from here      nothing was [D], so a [D] row would have joined the
#                                       list `down` destroys - against D11 and conventions 5.1
#
# How it authenticates: AWS_PROFILE is set on each command, from backend.PROFILES, and no
# credential is ever exported into this process's environment. A borrowed session outlives the
# command that needed it and every later error names the wrong account (Lesson 25). --dry-run
# prints the exact commands and runs none of them, which is also how the Validation reads the
# plan instead of trusting the target list.

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
RED = "\033[31m"  # step 7.2's refusal


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
    """The two generated files and `init`. Both generators read one table (step 2.6)."""
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
# [D] is "stop, never destroy" (D11). The first row is Stage 4's WireGuard `vpn/` and the
# second will be Stage 7's GitLab EC2 with its EBS volume - conventions 5.1 names exactly
# those two; everything else stateful is [P] by rule 2, since "stateful" is what makes a
# slice [D] *or* [P]. The hooks print what they did not do, because a hook that is silent
# when empty is indistinguishable from a hook that ran (Lesson 13).


def instance_name(env: str, slice_name: str) -> str:
    """The Name tag a [D] slice's host carries - derived from the row, never written twice.

    `sandbox`+`vpn` is `awsds-sandbox-vpn`, which is the contract Stage 4 step 1.1 writes into
    the module and `./aws/vpn.py` reads back; Stage 7's row becomes `awsds-prod-gitlab` without
    touching this file.
    """
    return f"awsds-{backend.env_token(env)}-{slice_name}"


def instance_states(env: str, slice_name: str, dry: bool) -> list | None:
    """[(instance id, power state)] for one [D] slice, found by Name tag - or None.

    None means nothing was read, and the caller can tell the two causes apart because it
    passed `dry` itself: under --dry-run the command was printed and not run, otherwise the
    call failed and the error is already on stderr. A caller must never read None as
    "nothing is running" (Lesson 13) - `status` reports UNREADABLE for that reason, and its
    total is a floor rather than a measurement.
    """
    res = run(
        [
            "aws",
            "ec2",
            "describe-instances",
            "--region",
            backend.REGION,
            "--filters",
            f"Name=tag:Name,Values={instance_name(env, slice_name)}",
            "Name=instance-state-name,Values=pending,running,stopping,stopped",
            "--query",
            "Reservations[].Instances[].[InstanceId,State.Name]",
            "--output",
            "text",
        ],
        env_extra={"AWS_PROFILE": backend.profile(env)},
        dry=dry,
        capture=True,
    )
    if res is None:
        return None
    if res.returncode != 0:
        print(
            f"    FAILED to read instances tagged {instance_name(env, slice_name)}", file=sys.stderr
        )
        print(res.stderr.strip(), file=sys.stderr)
        return None
    return [tuple(ln.split("\t")) for ln in res.stdout.split("\n") if ln.strip()]


# ----------------------------------------------------------- the hub (6c steps 7.1 and 7.2)
#
# The hub is one account's pair of [D] hosts, and every other account's session depends on them.
# D38 gives the estate one way in (the WireGuard host) and one way out (the Squid proxy), both in
# `production/networking`'s VPC. `make up` / `make down` act on one env and have no concept of
# that, so two things follow, and both are here rather than in a runbook (Lesson 5):
#
#   7.1  a Sandbox session must be able to start the two hub hosts without starting GitLab or
#        Production's [E] endpoints - hence `--only`, and `make hub-up` / `make hub-down`.
#   7.2  a spoke's `make up` must refuse while either hub host is down, naming it. Left alone a
#        stopped hub is a blackhole rather than an error: the apply succeeds, and every symptom
#        afterwards is a timeout that looks like a broken mirror or a broken package index. That
#        is the failure `runbooks/buildbox.md` documented for one tier, now estate-wide.
HUB_ENV = "production"
HUB_SLICES = ("vpn", "proxy")


def hub_state(dry: bool) -> list:
    """[(name, id, power state)] for the two hub hosts, or [] when nothing could be read.

    A direct `describe-instances` rather than `./aws/vpn.py`, which step 7.2 names ("reads the
    hub hosts' state through ./aws/vpn.py"). `vpn.py` writes a full report and is what a person
    runs to find out why the tunnel is unhappy; this needs one boolean before an apply and must
    not turn `make up` into a report generator. The two agree because both find the host by the
    same Name tag, which is the contract `instance_name()` owns.
    """
    out = []
    for name in HUB_SLICES:
        states = instance_states(HUB_ENV, name, dry)
        tag = instance_name(HUB_ENV, name)
        if states is None:
            out.append((tag, "-", "UNREADABLE"))
        elif not states:
            out.append((tag, "-", "absent"))
        else:
            out.append((tag, states[0][0], states[0][1]))
    return out


def refuse_if_hub_down(env: str, dry: bool) -> bool:
    """True to proceed. Applies to spokes only - the hub's own env starts it as part of `up`.

    UNREADABLE is not a refusal, and the asymmetry is deliberate: a spoke operator may hold no
    session on Production at all (the profiles are per account), so a failed read here would make
    a legitimate `make up ENV=sandbox` impossible for the person it is meant to protect. A read
    that fails is reported and waved through; a read that succeeds and says `stopped` stops the
    apply. The two nothings are told apart, and only one of them is a finding (Lesson 13).
    """
    if env == HUB_ENV:
        return True
    print(f"\n  {BOLD}the hub (step 7.2){RESET} - one way in, one way out, in another account:")
    rows = hub_state(dry)
    stopped = [r for r in rows if r[2] not in ("running", "UNREADABLE")]
    for tag, iid, state in rows:
        mark = "" if state in ("running", "UNREADABLE") else "  <-- this one"
        print(f"    {tag:<22} {state} {iid}{mark}")
    if not stopped:
        if any(r[2] == "UNREADABLE" for r in rows):
            print(
                "    NOT READ - no session on the hub account, so this refusal is waived rather\n"
                "    than failed. `make hub-up` from an identity that has one if a spoke misbehaves."
            )
        return True
    print(
        f"\n  {RED}REFUSED{RESET}: the hub is not up, and a stopped hub is a BLACKHOLE rather than\n"
        "  an error - this apply would succeed and every symptom afterwards would be a timeout.\n"
        "  Start it:  make hub-up",
        file=sys.stderr,
    )
    return False


def dormant(env: str, action: str, dry: bool, only: list | None = None) -> None:
    """[D] is stop/start and never destroy (D11). Stage 4 step 1.3 gave this hook its body.

    The instances are found by Name tag, not by state file (instance_name above), with two
    consequences. It keeps working when the slice's state is empty: it finds nothing and says
    which of the two nothings it found. And it cannot destroy - the only mutating calls below
    are start-instances and stop-instances - so half of refusal 5 is structural rather than a
    check that could be forgotten; the other half is that `down` does not hand the slice to
    `terraform destroy` at all (layers.py).

    Every outcome is printed, including the ones that did nothing (Lesson 13). "No instance
    tagged X" and "already stopped" are different findings: the first means the slice was
    never applied or its host is gone, the second means the hook had nothing left to do.
    """
    declared = [s for s in layers.for_env(env) if s.layer == layers.DORMANT]
    if only is not None:
        declared = [s for s in declared if s.name in only]
    if not declared:
        print(f"  [D] none declared in {env} - nothing to {'start' if action == 'up' else 'stop'}")
        print("      (the first is Stage 4's WireGuard vpn/; Stage 7 adds GitLab's instance)")
        return

    profile = backend.profile(env)
    verb, wanted, ready = (
        ("start", "running", "stopped") if action == "up" else ("stop", "stopped", "running")
    )

    for sl in declared:
        name = instance_name(env, sl.name)
        found = instance_states(env, sl.name, dry)
        if found is None:
            if dry:  # the command above was printed and not run
                print(f"    would {verb} whatever is tagged {name} and currently {ready}")
                continue
            raise SystemExit(1)

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


def cmd_envs(args) -> int:
    """The values ENV accepts, and what each one would actually act on.

    The list is read from the table `up` and `down` validate against, never typed into the
    Makefile. An account-folder list written out a second time goes stale on the first vend,
    in the copy nobody re-reads (Lesson 33), and this one would go stale silently, because no
    check reads `make help`.

    It prints the [D]/[E] counts beside each name, because the name on its own answers the
    wrong question. Three of the five folders hold nothing but [P] slices today, so `make
    down ENV=identity` is a target that correctly does nothing, and an operator who cannot
    tell that from a target that silently did nothing is reading the shape Lesson 13 warns
    about. The counts say which one they are about to get, before they type it.
    """
    print(
        f"{BOLD}ENV values{RESET} - the account folders of terraform-live/, "
        "declared in scripts/tfhygiene/layers.py:"
    )
    for env in layers.environments():
        rows = layers.for_env(env)
        acts = [
            f"{len([s for s in rows if s.layer == key])} [{key}]"
            for key in (layers.DORMANT, layers.EPHEMERAL)
            if any(s.layer == key for s in rows)
        ]
        why = ", ".join(acts) if acts else "only [P] - up and down are honest no-ops here"
        print(f"  {env:<17}{why}")
    print("\n  `./scripts/slices.py list <env>` for the slices behind one of these.")
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
        # The rank is read from layers.RANKS rather than stored per row, so it cannot
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

    # `--only` (step 7.1) narrows and never widens: a slice this env refuses stays refused, and
    # the reason is still printed. A closed list rather than a filter that silently matches
    # nothing - an unknown name here would produce a run that does nothing and reports success,
    # which is the shape `optional_service_groups` was given a validation block for.
    only = None
    if getattr(args, "only", None):
        only = [s.strip() for s in args.only.split(",") if s.strip()]
        known = {sl.name for sl in layers.for_env(args.env)}
        unknown = [s for s in only if s not in known]
        if unknown:
            print(
                f"unknown slice(s) for env '{args.env}': {', '.join(unknown)}. "
                f"known: {', '.join(sorted(known))}",
                file=sys.stderr,
            )
            return 2
        take = [sl for sl in take if sl.name in only]

    print(f"{BOLD}make {action} ENV={args.env}{RESET}")
    if only:
        print(f"  --only {','.join(only)} - every other slice in this env is untouched")
    print(f"\n  refused ({len(skipped)}), and the reason is printed rather than implied:")
    for sl, reason in skipped:
        print(f"    - {sl.path}: {reason}")

    if action == "down":
        print("\n  studio apps (step 8.6):")
        if not take:
            # The hook needs an SSO session and this `down` does not. Running it anyway would
            # make a no-op `make down` fail on credentials, which is a target that reports a
            # problem it does not have. It rides on the session the destroy already needs.
            print("    skipped - nothing to destroy in this env, so this run opens no session")
        elif studio_apps(args.env, args.dry_run) != 0:
            return 1

    # The [D] hook runs on the side of the [E] loop its rank says it should. Stage 4 step 1.3
    # put `vpn` at 40, below `egress` at 50, for one reason stated in words: "the tunnel is the
    # first thing up and the last thing down", because from step 8.3 onwards every AWS API call
    # has to exit through its Elastic IP. Stopping the host and only then destroying two slices
    # over the AWS API is the order that becomes a self-inflicted lockout the day
    # InfrastructureAccess joins the deny.
    #
    # A rank is not an intention (Lesson 5): it decides the order inside the [E] loop, and it
    # has to decide which side of that loop the hook sits on too.
    def run_dormant() -> None:
        print("\n  dormant [D] (step 8.2):")
        dormant(args.env, action, args.dry_run, only=only)

    # The hub check goes before the [D] hook and before the first apply (step 7.2), because a
    # refusal after either would leave the env half-raised, which is worse than not starting.
    if action == "up" and not refuse_if_hub_down(args.env, args.dry_run):
        return 1

    if action == "up":
        run_dormant()

    print(
        f"\n  ephemeral [E] ({len(take)}), in {'reverse ' if action == 'down' else ''}dependency order:"
    )
    if not take:
        print("    none - every [E] slice in this env is refused above, so this half is a NO-OP.")
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
            # The host is left running on purpose when a destroy fails: the operator has
            # something to fix over the tunnel this hook would otherwise have closed.
            print(
                "\n  dormant [D]: NOT stopped - an [E] destroy failed above and the",
                file=sys.stderr,
            )
            print(
                "  tunnel is how the account is reached. Re-run `make down` once it is fixed.",
                file=sys.stderr,
            )
            return 1

    if action == "down":
        run_dormant()
    return 0


def managed_resources(module: dict) -> int:
    """Deployed resources in a state tree, recursively and managed-only.

    Counting `len(child_modules)` counts one per module rather than one per resource: a
    sandbox/egress/ holding a NAT, an EIP, two routes and twelve endpoints reported
    "2 resource(s)", one remote-state data source plus the single module (measured
    2026-08-16). The burn is unaffected, since it comes from the layers.py table, but the
    line that reports what is running was understated by an order of magnitude.

    Managed-only is the other half: a data source is something the slice reads, never
    something it created, so a state holding nothing else is `down` - and `up` is derived
    from this count.
    """
    n = sum(1 for r in module.get("resources", []) if r.get("mode") == "managed")
    return n + sum(managed_resources(c) for c in module.get("child_modules", []))


def cmd_status(args) -> int:
    """What is up, and the burn - rates from a static table, never a live pricing call (8.4)."""
    envs = [args.env] if args.env else layers.environments()
    metered = [
        s for e in envs for s in layers.for_env(e) if s.layer in (layers.DORMANT, layers.EPHEMERAL)
    ]

    print(f"{BOLD}status{RESET}  env(s): {', '.join(envs)}")
    if not metered:
        # Not "0.00 USD/h". "Nothing is declared" and "everything is down" are different
        # answers, and a status command that prints one for the other is Lesson 13 (see 8.4).
        print("\n  no [D] or [E] slice is DECLARED in this repository, so there is nothing")
        print("  hourly to be up. This is Stage 2: every slice on disk is [P]. The first")
        print("  metered slice is Stage 3's egress/, and it declares its own usd_per_hour")
        print("  in scripts/tfhygiene/layers.py from docs/PRICING.md 3.")
        print("\n  estimated burn: USD 0.00/h - because the set is empty, not because it was read")
        return 0

    total, unreadable = 0.0, 0
    for sl in metered:
        # A [D] slice is not measured by its state file. `terraform show` reports the instance
        # as present whether it is running or stopped, which is what [D] means, so counting
        # resources would add 0.0042/h to the burn forever and the 0.0000/h reading Stage 3
        # closed on could never come back. What is metered by the hour here is the power state,
        # so it is read from EC2 by the same Name tag the dormant hook uses, and no
        # `terraform init` is needed to answer it.
        if sl.layer == layers.DORMANT:
            found = instance_states(sl.account, sl.name, args.dry_run)
            if found is None:
                if args.dry_run:
                    continue
                print(f"  {sl.path:<40} UNREADABLE")
                unreadable += 1
                continue
            running = [i for i, st in found if st in ("running", "pending")]
            total += sl.usd_per_hour if running else 0.0
            state = "UP" if running else ("stopped" if found else "absent")
            print(
                f"  {sl.path:<40} {state:<7} {len(found):>3} instance(s)"
                f"   {sl.usd_per_hour if running else 0.0:.4f} USD/h"
            )
            continue
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
    if any(s.layer == layers.DORMANT for s in metered):
        # 0.0000/h is not "free" once a [D] slice exists. A stopped host keeps its EBS volume
        # and its [P] Elastic IP, both billed monthly, so the hourly total is silent about them
        # by construction.
        print("  a stopped [D] host still bills its EBS volume and its [P] Elastic IP,")
        print("  monthly rather than hourly - the floor lines of docs/plan/cost-model.md.")
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

    sub.add_parser("envs").set_defaults(fn=cmd_envs)

    sub.add_parser("check").set_defaults(fn=cmd_check)

    for action in ("up", "down"):
        p = sub.add_parser(action)
        # Refusal 2, first of its two guards: no default, no "all". `make down` with no ENV
        # must fail rather than mean everything.
        p.add_argument("--env", required=True)
        p.add_argument("--auto-approve", action="store_true")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument(
            "--only",
            help="comma-separated slice names to act on, instead of the whole env (6c step 7.1). "
            "Narrows only: a slice this env refuses stays refused. `make hub-up` is "
            "`up --env production --only vpn,proxy`.",
        )
        p.set_defaults(fn=cmd_updown, action=action)
    p = sub.add_parser("status")
    p.add_argument("--env")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_status)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
