#!/usr/bin/env -S uv run --quiet
# cicd.py - Stage 8's evidence, the credential layer read from every side: the deploy runner
# (protected, [E]) and its narrow instance role, the four deploy roles with their permissions
# boundaries and single-principal trust (INT-08, INT-18), the misuse-alarm rules, the
# app-repository grant Staging pulls through (INT-07), the dev-env registration read side by
# side across the Interactive accounts (D17's identical-runtime claim), and the recent
# AssumeRole events per deploy role - the record INT-08 exists for.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/cicd.py                      # every awsds-* profile
#             ./aws/cicd.py awsds-infra-prod     # only the ones named
#             python3 aws/cicd.py -              # CloudShell, ambient credentials
#   writes:   aws/output/cicd.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeInstances, iam:GetRole, ListRolePolicies, GetRolePolicy,
#             ListAttachedRolePolicies, events:ListRules, ecr:GetRepositoryPolicy,
#             DescribeRepositories, DescribeImages, sagemaker:ListImages,
#             ListImageVersions, cloudtrail:LookupEvents, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything, and it never assumes a role:
#             reading WHO assumed one is CloudTrail's job, and this file only looks it up.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The subject is
# trust BETWEEN accounts: the runner lives in Production while its roles live in Staging and
# the Interactive accounts (INT-08, INT-18), and D17's claim - the same runtime registered
# everywhere - is only readable with the Interactive accounts side by side. Section 1 pays
# the rule back with the caller ARN of every profile.
#
# CONTRACTS THIS FILE READS, each named in the stage file so a rename fails loudly:
#   - the deploy runner's Name tag and role name contain awsds-prod-runner-deploy (step 4.3)
#   - the deploy roles are awsds-deploy-staging, awsds-deploy-prod (step 4.1, INT-08) and
#     awsds-deploy-devenv-sandbox, awsds-deploy-devenv-dev (step 4.2, INT-18)
#   - the misuse-alarm rules carry "deploy-misuse" in their name (step 4.6)
#   - the application repository is awsds-prod-ecr-app-etl (Stage 7 step 5.1)
#   - a registered dev-env image's name contains "dev-env" (Stage 6 step 5.1's record)
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - GitLab's side of the stage - the three .gitlab-ci.yml files, protected tags, which
#     runner a job scheduled onto - lives behind gitlab.prod.internal; no AWS API reads it.
#   - The behavioural proofs (a broken version dying in Staging, the blocked vulnerable
#     dependency, the by-hand parity of 3.8) are the stage's own (Lesson 20).
#   - Whether a registration SURVIVES a blueprint reconciliation (INT-17's open half) is a
#     diff of two runs of this file, not one run.

from __future__ import annotations

import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "cicd.txt"

# The producer account and the deploy-role homes (D14; D35 - the sandbox side is per unit).
PROD_PROFILE = "awsds-infra-prod"
ROLE_BY_PROFILE = {
    "awsds-infra-staging": "awsds-deploy-staging",
    "awsds-infra-prod": "awsds-deploy-prod",
    "awsds-infra-sandbox-1": "awsds-deploy-devenv-sandbox",
    "awsds-infra-dev": "awsds-deploy-devenv-dev",
}
# The two roles CloudTrail is asked about, in the account each lives in (INT-08).
PROMOTION_PROFILES = ("awsds-infra-staging", "awsds-infra-prod")

# The contracts (see header).
RUNNER_NAME = "awsds-prod-runner-deploy"
APP_REPO = "awsds-prod-ecr-app-etl"
MISUSE_RULE_SUBSTR = "deploy-misuse"
DEVENV_IMAGE_SUBSTR = "dev-env"
LOOKUP_MAX = 50  # CloudTrail lookup page - 90 days of AssumeRole is small at lab scale


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    checks = Checks()

    prod_live = PROD_PROFILE in live
    prod_account = next((c.account for c in callers if c.profile == PROD_PROFILE), None)

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    # ------------------------------------------------ the deploy runner (Production, [E])
    runner_rows: list = []  # (id, type, state, imdsv2, instance-profile arn tail)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        note(f"measuring {PROD_PROFILE} (deploy runner) ...")
        res = cli.run(
            "ec2",
            "describe-instances",
            "--filters",
            f"Name=tag:Name,Values={RUNNER_NAME}",
            "Name=instance-state-name,Values=pending,running,stopping,stopped",
            "--query",
            "Reservations[].Instances[].[InstanceId,InstanceType,State.Name,"
            "MetadataOptions.HttpTokens,IamInstanceProfile.Arn]",
            "--output",
            "json",
            log=False,
        )
        if res.ok and res.stdout:
            for iid, itype, state, tokens, prof in json.loads(res.stdout or "[]"):
                tail = str(prof).rsplit("/", 1)[-1] if prof else "(none)"
                runner_rows.append((str(iid), str(itype), str(state), str(tokens), tail))
        elif not res.ok:
            logerr(PROD_PROFILE, "ec2 describe-instances (deploy runner)", res.stderr)

    # -------------- the runner's role: inline statements, and what AssumeRole may reach
    runner_role_found = False
    runner_inline: list = []  # (policy name, actions, resources) for sts statements
    runner_attached: list = []
    runner_bad_resources: list = []
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        res = cli.run(
            "iam",
            "get-role",
            "--role-name",
            RUNNER_NAME,
            "--query",
            "Role.RoleName",
            "--output",
            "text",
            log=False,
            tolerate="NoSuchEntity",
        )
        runner_role_found = bool(res.ok and not res.tolerated)
        if runner_role_found:
            res = cli.run(
                "iam",
                "list-attached-role-policies",
                "--role-name",
                RUNNER_NAME,
                "--query",
                "AttachedPolicies[].PolicyName",
                "--output",
                "json",
                log=False,
            )
            if res.ok and res.stdout:
                runner_attached = [str(x) for x in json.loads(res.stdout or "[]")]
            res = cli.run(
                "iam",
                "list-role-policies",
                "--role-name",
                RUNNER_NAME,
                "--query",
                "PolicyNames",
                "--output",
                "json",
                log=False,
            )
            for pname in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
                r = cli.run(
                    "iam",
                    "get-role-policy",
                    "--role-name",
                    RUNNER_NAME,
                    "--policy-name",
                    pname,
                    "--query",
                    "PolicyDocument",
                    "--output",
                    "json",
                    log=False,
                )
                if not (r.ok and r.stdout):
                    continue
                doc = json.loads(r.stdout)
                stmts = doc.get("Statement", [])
                if isinstance(stmts, dict):
                    stmts = [stmts]
                for st in stmts:
                    actions = st.get("Action", [])
                    actions = [actions] if isinstance(actions, str) else actions
                    if not any(str(a).lower().startswith("sts:assumerole") for a in actions):
                        continue
                    resources = st.get("Resource", [])
                    resources = [resources] if isinstance(resources, str) else resources
                    runner_inline.append(
                        (str(pname), " ".join(map(str, actions)), " ".join(map(str, resources)))
                    )
                    for arn in resources:
                        s = str(arn)
                        if s == "*" or "::*:" in s or "/awsds-deploy-" not in s:
                            runner_bad_resources.append((str(pname), s))

    # ----------------------- the four deploy roles: existence, boundary, trust (per home)
    role_rows: list = []  # (profile, role, state, boundary tail, trust summary)
    trust_bad: list = []  # (role, principal or action that breaks the contract)
    roles_found = 0
    for p, role in ROLE_BY_PROFILE.items():
        if p not in live:
            continue
        cli = cli_for(p)
        note(f"measuring {p} ({role}) ...")
        res = cli.run(
            "iam",
            "get-role",
            "--role-name",
            role,
            "--query",
            "Role.[PermissionsBoundary.PermissionsBoundaryArn,AssumeRolePolicyDocument]",
            "--output",
            "json",
            log=False,
            tolerate="NoSuchEntity",
        )
        if res.tolerated:
            role_rows.append((p, role, "(absent)", "-", "-"))
            continue
        if not (res.ok and res.stdout):
            role_rows.append((p, role, "(read failed)", "-", "-"))
            continue
        boundary, trust = json.loads(res.stdout)
        roles_found += 1
        btail = str(boundary).rsplit("/", 1)[-1] if boundary else "(none)"
        principals: list = []
        stmts = (trust or {}).get("Statement", [])
        if isinstance(stmts, dict):
            stmts = [stmts]
        for st in stmts:
            actions = st.get("Action", [])
            actions = [actions] if isinstance(actions, str) else actions
            aws_p = (st.get("Principal", {}) or {}).get("AWS", [])
            aws_p = [aws_p] if isinstance(aws_p, str) else aws_p
            principals += [str(x) for x in aws_p]
            for a in actions:
                if str(a) not in ("sts:AssumeRole",):
                    trust_bad.append((role, f"action {a}"))
            for prin in aws_p:
                if RUNNER_NAME not in str(prin):
                    trust_bad.append((role, f"principal {prin}"))
            if (st.get("Principal", {}) or {}).get("Service") or (
                st.get("Principal", {}) or {}
            ).get("Federated"):
                trust_bad.append((role, "a non-AWS principal type in the trust policy"))
        role_rows.append((p, role, "present", btail, " ".join(principals) or "(no principal)"))

    built = roles_found > 0 or bool(runner_rows)

    # ------------------------------------------- the misuse-alarm rules (step 4.6, D14)
    rule_rows: list = []  # (profile, rule, state)
    for p in PROMOTION_PROFILES:
        if p not in live:
            continue
        cli = cli_for(p)
        res = cli.run(
            "events",
            "list-rules",
            "--query",
            "Rules[].[Name,State]",
            "--output",
            "json",
            log=False,
        )
        for rname, state in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
            if MISUSE_RULE_SUBSTR in str(rname):
                rule_rows.append((p, str(rname), str(state)))

    # ------------------- the app-repository grant and the Staging read (INT-07's halves)
    app_policy_state = "(not measured)"
    app_repo_exists = False
    staging_read = "(no staging profile)"
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        res = cli.run(
            "ecr",
            "get-repository-policy",
            "--repository-name",
            APP_REPO,
            "--query",
            "policyText",
            "--output",
            "text",
            log=False,
            tolerate="RepositoryNotFoundException|RepositoryPolicyNotFoundException",
        )
        if res.tolerated:
            app_policy_state = "(no repository, or no policy on it)"
            r = cli.run(
                "ecr",
                "describe-repositories",
                "--repository-names",
                APP_REPO,
                "--query",
                "repositories[0].repositoryName",
                "--output",
                "text",
                log=False,
                tolerate="RepositoryNotFoundException",
            )
            app_repo_exists = bool(r.ok and not r.tolerated)
        elif res.ok:
            app_repo_exists = True
            n = res.stdout.count('"AWS"')
            app_policy_state = f"present ({n} principal block(s))"
    if "awsds-infra-staging" in live and prod_account:
        cli = cli_for("awsds-infra-staging")
        res = cli.run(
            "ecr",
            "describe-images",
            "--registry-id",
            prod_account,
            "--repository-name",
            APP_REPO,
            "--max-results",
            "1",
            "--query",
            "length(imageDetails)",
            "--output",
            "text",
            log=False,
            tolerate="RepositoryNotFoundException|AccessDenied",
        )
        if res.tolerated:
            staging_read = "(denied or no repository)"
        elif res.ok:
            staging_read = f"ok ({res.stdout.strip()} image(s) visible)"
        else:
            staging_read = "(call failed)"

    # ----------------- the dev-env registration, side by side (INT-17/INT-18 mechanical)
    image_rows: list = []  # (profile, image name, latest version, base image tail)
    for p in ("awsds-infra-sandbox-1", "awsds-infra-dev"):
        if p not in live:
            continue
        cli = cli_for(p)
        note(f"measuring {p} (registered images) ...")
        res = cli.run(
            "sagemaker",
            "list-images",
            "--query",
            "Images[].ImageName",
            "--output",
            "json",
            log=False,
        )
        names = [
            str(n)
            for n in (json.loads(res.stdout or "[]") if res.ok and res.stdout else [])
            if DEVENV_IMAGE_SUBSTR in str(n)
        ]
        if not names:
            image_rows.append((p, "(none)", "-", "-"))
            continue
        for iname in names:
            r = cli.run(
                "sagemaker",
                "list-image-versions",
                "--image-name",
                iname,
                "--sort-by",
                "CREATION_TIME",
                "--sort-order",
                "DESCENDING",
                "--max-results",
                "1",
                "--query",
                "ImageVersions[0].[Version,BaseImage]",
                "--output",
                "json",
                log=False,
            )
            if r.ok and r.stdout:
                version, base = json.loads(r.stdout or "[null,null]") or [None, None]
                base_tail = str(base).rsplit("/", 1)[-1] if base else "-"
                image_rows.append((p, iname, str(version), base_tail))
            else:
                image_rows.append((p, iname, "(read failed)", "-"))

    # --------------- who assumed a deploy role - CloudTrail's 90-day lookup (INT-08)
    event_rows: list = []  # (profile, time, role tail, caller tail)
    event_bad: list = []  # (profile, caller) for a non-runner caller
    for p in PROMOTION_PROFILES:
        if p not in live:
            continue
        cli = cli_for(p)
        note(f"measuring {p} (AssumeRole events) ...")
        res = cli.run(
            "cloudtrail",
            "lookup-events",
            "--lookup-attributes",
            "AttributeKey=EventName,AttributeValue=AssumeRole",
            "--max-results",
            str(LOOKUP_MAX),
            "--query",
            "Events[].CloudTrailEvent",
            "--output",
            "json",
            log=False,
        )
        for raw in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
            try:
                ev = json.loads(raw)
            except (TypeError, ValueError):
                continue
            role_arn = str(((ev.get("requestParameters") or {}).get("roleArn")) or "")
            if "/awsds-deploy-" not in role_arn:
                continue
            caller = str((ev.get("userIdentity") or {}).get("arn") or "(unknown)")
            when = str(ev.get("eventTime") or "-")
            event_rows.append(
                (p, when, role_arn.rsplit("/", 1)[-1], caller.rsplit("/", 1)[-1][:40])
            )
            if RUNNER_NAME not in caller:
                event_bad.append((p, caller))

    # -------------------------------------------------------------------------- the checks

    # CI-1: the deploy runner - IMDSv2 required, an instance profile attached. Absent is
    # [E] between sessions (D11 working) or the stage not yet run - a note either way.
    if prod_live:
        if not runner_rows:
            checks.note(
                "CI-1",
                "the deploy runner",
                "absent - [E] between sessions is D11 working; expected before step 4.5.",
            )
        else:
            for iid, itype, state, tokens, prof in runner_rows:
                if tokens != "required":
                    checks.fail("CI-1", f"IMDSv2 on {iid}", f"HttpTokens={tokens} - not enforced.")
                elif prof == "(none)":
                    checks.fail(
                        "CI-1",
                        f"instance profile on {iid}",
                        "none attached - the instance profile IS the deploy credential "
                        "(step 4.3, principle 2).",
                    )
                else:
                    checks.ok("CI-1", f"the deploy runner ({iid})", f"{itype}, {state}, {prof}")

    # CI-2: each deploy role exists with a permissions boundary (steps 4.1-4.2; INT-14
    # later applies under it, which is where the boundary's shape is really tested).
    for p, role, state, btail, _trust in role_rows:
        if state == "(absent)":
            checks.note("CI-2", f"{role} ({p})", "absent - expected before steps 4.1-4.2.")
        elif state == "present" and btail == "(none)":
            checks.fail(
                "CI-2",
                f"boundary on {role}",
                "no permissions boundary - steps 4.1-4.2 attach one to every deploy role.",
            )
        elif state == "present":
            checks.ok("CI-2", f"{role}", f"boundary {btail}")

    # CI-3: every trust policy admits ONLY the deploy runner's role, only sts:AssumeRole -
    # an enumerated principal, never a wildcard account (conventions 6; INT-08/INT-18).
    if trust_bad:
        for role, what in sorted(set(trust_bad)):
            checks.fail("CI-3", f"trust on {role}", f"{what} - outside the 4.1/4.2 contract.")
    elif any(state == "present" for _p, _r, state, _b, _t in role_rows):
        checks.ok(
            "CI-3",
            "the deploy-role trust policies",
            f"every principal names {RUNNER_NAME}, sts:AssumeRole only",
        )

    # CI-4: the runner role's own AssumeRole reach is the enumerated deploy-role list -
    # no "*", no wildcard account, nothing outside awsds-deploy-* (step 4.3).
    if runner_role_found:
        if runner_bad_resources:
            for pname, arn in sorted(set(runner_bad_resources)):
                checks.fail(
                    "CI-4",
                    f"AssumeRole resource in {pname}",
                    f"{arn} - the runner role may assume ONLY the enumerated "
                    "awsds-deploy-* ARNs (step 4.3).",
                )
        elif runner_inline:
            checks.ok(
                "CI-4",
                "the runner role's AssumeRole reach",
                f"{len(runner_inline)} inline statement(s), all awsds-deploy-*",
            )
        elif runner_attached:
            checks.note(
                "CI-4",
                "the runner role's policies",
                f"no inline sts statement; attached: {', '.join(runner_attached[:3])} - "
                "read those documents by hand.",
            )
    elif prod_live and built:
        checks.note("CI-4", f"role {RUNNER_NAME}", "absent - expected before step 4.3.")

    # CI-5: the app-repository grant (INT-07's enabling half) and the Staging-side read.
    if prod_live:
        if app_policy_state.startswith("present"):
            checks.ok("CI-5", f"policy on {APP_REPO}", app_policy_state)
        elif app_repo_exists:
            (checks.fail if built else checks.note)(
                "CI-5",
                f"policy on {APP_REPO}",
                "repository exists with no policy - Staging cannot pull (step 3.0).",
            )
        else:
            checks.note("CI-5", f"repository {APP_REPO}", "absent - Stage 7 step 5.1 creates it.")
    if staging_read.startswith("ok"):
        checks.ok("CI-5", "the Staging cross-account read", staging_read)
    elif "awsds-infra-staging" in live and app_repo_exists:
        checks.fail(
            "CI-5",
            "the Staging cross-account read",
            f"{staging_read} - the repository exists, so the 3.0 grant is missing.",
        )

    # CI-6: the registered dev-env versions agree across the Interactive accounts -
    # D17's identical-runtime-by-construction, read at the registration (step 1.6).
    real = [r for r in image_rows if r[1] != "(none)" and r[3] != "-"]
    if len(real) >= 2:
        tails = {r[3] for r in real}
        if len(tails) == 1:
            checks.ok("CI-6", "dev-env parity", f"one base image everywhere: {tails.pop()}")
        else:
            checks.fail(
                "CI-6",
                "dev-env parity",
                f"{len(tails)} different base images across the Interactive accounts - "
                "D17's premise; re-run step 1.6 on the lagging account.",
            )
    elif image_rows and built:
        checks.note(
            "CI-6",
            "dev-env registrations",
            "fewer than two accounts registered - expected before Stage 6 step 5.1 / "
            "Stage 8 step 1.6.",
        )

    # CI-7: the misuse-alarm rules exist and are ENABLED in both promotion accounts (4.6).
    for p in PROMOTION_PROFILES:
        if p not in live:
            continue
        mine = [r for r in rule_rows if r[0] == p]
        if not mine:
            (checks.fail if built else checks.note)(
                "CI-7",
                f"misuse rule in {p}",
                "no *deploy-misuse* rule - "
                + ("step 4.6's compensation is absent." if built else "expected before 4.6."),
            )
        else:
            for _p, rname, state in mine:
                if state != "ENABLED":
                    checks.fail("CI-7", f"rule {rname}", f"state {state} - not watching.")
                else:
                    checks.ok("CI-7", f"rule {rname} ({p})", "ENABLED")

    # CI-8: every recorded AssumeRole of a deploy role was made by the deploy runner. A
    # different caller is exactly what 4.6 alarms on - visible here too, after the fact.
    if event_bad:
        for p, caller in sorted(set(event_bad)):
            checks.fail(
                "CI-8",
                f"deploy-role assumption in {p}",
                f"caller {head2(caller)} is not the deploy runner - review against 4.6's alarm.",
            )
    elif event_rows:
        checks.ok(
            "CI-8",
            "deploy-role assumptions",
            f"{len(event_rows)} event(s), every caller is the deploy runner",
        )

    # ---------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("CI/CD - the Stage 8 evidence: deploy credentials, gates' substrate, events")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/cicd.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The deploy runner and its role (Production, [E])
  3. The four deploy roles: boundary and trust (INT-08, INT-18)
  4. The misuse-alarm rules (step 4.6)
  5. The application repository: the grant, and the read from Staging (INT-07)
  6. The dev-env registrations, side by side (INT-17/INT-18, D17)
  7. Who assumed a deploy role - CloudTrail's last 90 days (INT-08)
  8. CHECKS
  9. The accounts nothing here is measuring
 10. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 8 RUNS - each such reading
    is a note, not a failure; it becomes a regression the moment the stage closes.
  - AN ABSENT deploy runner is [E] working between sessions, not an outage.
    `Staging` rows appear only once the account is vended and holds a profile.
  - THIS IS A CONTROL-PLANE READING. Whether a pipeline actually schedules onto
    the protected runner, blocks on a finding, or dies in Staging is behavioural
    - the stage's own proofs (Lesson 20). INT-17's reconciliation-survival half
    is a DIFF of two runs of this file, never one run.

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
        rep.h1("2. The deploy runner and its role (Production, [E])")
        if not prod_live:
            rep.line(f"{PROD_PROFILE} was not measured - nothing to show.")
        else:
            if runner_rows:
                rep.tabulate(
                    ["ID\tTYPE\tSTATE\tIMDSV2\tINSTANCE PROFILE"]
                    + ["\t".join(r) for r in runner_rows]
                )
            else:
                rep.line(f"No instance named {RUNNER_NAME}. [E] between sessions, or pre-4.5.")
            rep.line()
            if runner_inline:
                rep.tabulate(
                    ["INLINE POLICY\tACTIONS\tRESOURCES"] + ["\t".join(r) for r in runner_inline]
                )
            elif runner_role_found:
                rep.line(
                    "No inline sts statement on the role; attached: "
                    + (", ".join(runner_attached) or "(none)")
                )
            else:
                rep.line(f"No role named {RUNNER_NAME}. Expected before step 4.3.")

        # ==============================================================================
        rep.h1("3. The four deploy roles: boundary and trust (INT-08, INT-18)")
        if role_rows:
            rep.tabulate(
                ["PROFILE\tROLE\tSTATE\tBOUNDARY\tTRUSTED PRINCIPAL(S)"]
                + ["\t".join(r) for r in role_rows]
            )
        else:
            rep.line("No deploy-role home was measured.")
        rep.text("""
The trust contract (4.1-4.2): exactly the deploy runner's role, sts:AssumeRole
only, never a wildcard account. Staging's row is absent until the vend; the
sandbox row is per business unit and grows with the D35 map.""")

        # ==============================================================================
        rep.h1("4. The misuse-alarm rules (step 4.6)")
        if rule_rows:
            rep.tabulate(["PROFILE\tRULE\tSTATE"] + ["\t".join(r) for r in rule_rows])
        else:
            rep.line("No *deploy-misuse* rule in any measured promotion account (pre-4.6).")

        # ==============================================================================
        rep.h1("5. The application repository: the grant, and the read from Staging (INT-07)")
        rep.line(f"{APP_REPO} policy: {app_policy_state}")
        rep.line(f"Staging cross-account read: {staging_read}")
        rep.text("""
Presence, never sufficiency: the behavioural INT-07 proof is 3.2's pull under
awsds-deploy-staging during a real promotion. This grant is deliberately NOT the
D35 Interactive consumer map (supplychain.py section 9 records why).""")

        # ==============================================================================
        rep.h1("6. The dev-env registrations, side by side (INT-17/INT-18, D17)")
        if image_rows:
            rep.tabulate(
                ["PROFILE\tIMAGE\tLATEST VERSION\tBASE IMAGE"] + ["\t".join(r) for r in image_rows]
            )
        else:
            rep.line("No Interactive account was measured.")
        rep.text("""
D17's claim is the BASE IMAGE column agreeing across every row: the same digest
registered everywhere, promoted by approval rather than pushed by whoever built
last. One row lagging after a 1.6 run is the registration failing quietly.""")

        # ==============================================================================
        rep.h1("7. Who assumed a deploy role - CloudTrail's last 90 days (INT-08)")
        if event_rows:
            rep.tabulate(["PROFILE\tTIME\tROLE\tCALLER"] + ["\t".join(r) for r in event_rows[:25]])
            if len(event_rows) > 25:
                rep.line(f"... and {len(event_rows) - 25} more event(s).")
        else:
            rep.line("No AssumeRole event names a deploy role yet (or no account measured).")
        rep.text("""
This is the record INT-08's two-name design exists for: which role ran which
leg, answerable per event. Every caller should be the deploy runner; anything
else is what 4.6's alarm fires on, and CI-8 fails on it here.""")

        # ==============================================================================
        rep.h1("8. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  CI-1  the deploy runner: IMDSv2 required, an instance profile attached (4.3)
  CI-2  every deploy role carries a permissions boundary (4.1-4.2)
  CI-3  every trust policy: the runner's role only, sts:AssumeRole only (4.1-4.2)
  CI-4  the runner role assumes ONLY the enumerated awsds-deploy-* ARNs (4.3)
  CI-5  the app-repository grant, and the read from Staging (3.0, INT-07)
  CI-6  the dev-env base image agrees across Interactive accounts (1.6, D17)
  CI-7  the *deploy-misuse* rules exist and are ENABLED (4.6)
  CI-8  every recorded deploy-role assumption was the deploy runner (INT-08)""")

        # ==============================================================================
        rep.h1("9. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 8 as a pass.

  - `Staging` has no profile until the vend - sections 3-5 and 7 are then half
    blind: the awsds-deploy-staging row, its alarm rule and the cross-account
    read all appear only after 3.0.
  - Every Sandbox beyond unit 1 has no profile until Stage 14 - the deploy-role
    map and section 6 must both grow with N (D35).
  - GitLab's objects (the three .gitlab-ci.yml files, protected tags, runner
    assignments) live behind gitlab.prod.internal - the stage log records them.""")

        # ==============================================================================
        rep.h1("10. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/cicd.py")

    # ------------------------------------------------------------------------------ run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 10)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 8)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
