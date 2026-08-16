#!/usr/bin/env -S uv run --quiet
# studio.py - Stage 6's evidence, registry and runtimes side by side: the one DataZone V2
# domain in Data Governance (a REGISTRY - so also the negative reading: no SageMaker resource
# may exist there), its blueprint configurations and project profiles, the blueprint-
# provisioned SageMaker AI domain in each Interactive account (VPC-only, private subnets,
# idle shutdown), the D13 permissions boundary on the project roles (INT-15's mechanical
# half), the step 3 deny Sids in the persona sets, the dev-env image registration (INT-17's
# mechanical half), and the running apps - the burn meter of the one [E] thing Terraform
# does not own.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/studio.py                      # every awsds-* profile
#             ./aws/studio.py awsds-infra-data     # only the ones named
#             python3 aws/studio.py -              # CloudShell, ambient credentials
#   writes:   aws/output/studio.txt   (untracked - see .gitignore)
#   reads:    datazone:ListDomains, GetDomain, ListEnvironmentBlueprintConfigurations,
#             ListEnvironmentBlueprints, ListProjectProfiles, ListProjects,
#             sagemaker:ListDomains, DescribeDomain, ListApps, ListSpaces, ListImages,
#             ListAppImageConfigs, iam:ListRoles, GetRole,
#             elasticfilesystem:DescribeAccessPoints,
#             sso-admin:ListInstances, ListPermissionSets, DescribePermissionSet,
#             GetInlinePolicyForPermissionSet, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The whole point of
# D26 is that one account holds the registry and OTHER accounts hold the compute the registry
# provisions: "the domain is a registry, not a runtime" is only readable with Data Governance
# and the two Interactive accounts side by side - a SageMaker domain in the wrong column IS
# the finding. Section 1 pays the rule back with the caller ARN of every profile.
#
# CONTRACTS THIS FILE READS, each named in the stage file so a rename fails loudly:
#   - the two project profiles are named `experimentation` and `engineering` (Stage 6 step 1)
#   - the step 3 deny Sids are DenySageMakerJobsOffVpc and DenySageMakerInstanceCeiling
#   - the D13 boundary on project roles is named awsds-<env>-project-boundary (step 2)
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - The behavioural proofs - the portal opening (INT-16), a notebook reading the lake
#     through the LF share, the egress pair under designs A and B - are the stage's own,
#     run from a browser and a notebook (Lesson 20).
#   - Whether a boundary SURVIVES a blueprint reconciliation (INT-15) is answered by
#     provisioning, waiting, and re-running this script - the diff is the evidence.
#   - Whether the SCP carve-out lets Data Governance create a domain (step 0) is a probe,
#     not a reading - a describe call cannot exercise a deny.

from __future__ import annotations

import json
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "studio.txt"

# The registry account and the blueprint targets (D26, D35 - the sandbox side is per unit).
DATA_PROFILE = "awsds-infra-data"
INTERACTIVE_PROFILES = ("awsds-infra-sandbox-1", "awsds-infra-dev")
IDENTITY_PROFILE = "awsds-infra-identity"
# Accounts where nothing DataZone- or Studio-shaped may ever appear (D28: deployment
# targets stay headless). Staging has no profile until the vend.
HEADLESS_PROFILES = ("awsds-infra-prod", "awsds-infra-staging")

# The contracts (see header).
PROJECT_PROFILE_NAMES = ("experimentation", "engineering")
STEP3_SIDS = ("DenySageMakerJobsOffVpc", "DenySageMakerInstanceCeiling")
BOUNDARY_NAME_FRAGMENT = "project-boundary"

# The persona sets the step 3 fragment reaches (same set as Stage 4 step 8.2).
PERSONA_SETS = (
    "DataScientistAccess",
    "DataScientistStagingAccess",
    "DataScientistProdAccess",
    "DeploymentManagerAccess",
    "GovernanceManagerAccess",
    "DevEnvStewardAccess",
)


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    checks = Checks()

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    # -------------------------------------------- the DataZone domain, in EVERY account
    # One listing everywhere, on purpose: a domain in any account but Data Governance is
    # either the INT-12 fallback happening by accident or the 1c root deny not holding.
    # In the HEADLESS accounts the Workloads OU denies datazone:* in full (1c, D26), so an
    # SCP denial THERE is the D28 control holding, not a failed call - measured on this
    # script's first run, 2026-08-16.
    SCP_DENIED = "SCP_DENIED"
    dz_domains: dict = {}  # profile -> [(id, name, version, status)] | None | SCP_DENIED
    for p in live:
        cli = cli_for(p)
        note(f"measuring {p} ...")
        res = cli.run(
            "datazone",
            "list-domains",
            "--output",
            "json",
            log=False,
            tolerate=(
                "explicit deny in a service control policy" if p in HEADLESS_PROFILES else None
            ),
        )
        if res.tolerated:
            dz_domains[p] = SCP_DENIED
            continue
        if not res.ok:
            logerr(p, "datazone list-domains", res.stderr)
            dz_domains[p] = None
            continue
        doc = json.loads(res.stdout or "{}")
        dz_domains[p] = [
            (
                d.get("id", "?"),
                d.get("name", "?"),
                d.get("domainVersion", "?"),
                d.get("status", "?"),
            )
            for d in doc.get("items", [])
        ]

    # ------------------------------- the registry's contents (Data Governance only)
    data_live = DATA_PROFILE in live
    bp_configs: list = []  # (blueprint name, enabled regions, provisioning role set?, accounts)
    project_profiles: list = []  # (name, id, status)
    projects: list = []  # (name, id, status)
    domain_id = ""
    if data_live and dz_domains.get(DATA_PROFILE):
        cli = cli_for(DATA_PROFILE)
        domain_id = dz_domains[DATA_PROFILE][0][0]
        res = cli.run(
            "datazone",
            "list-environment-blueprint-configurations",
            "--domain-identifier",
            domain_id,
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(DATA_PROFILE, "datazone list-environment-blueprint-configurations", res.stderr)
        else:
            doc = json.loads(res.stdout or "{}")
            for c in doc.get("items", []):
                bpid = c.get("environmentBlueprintId", "?")
                r = cli.run(
                    "datazone",
                    "get-environment-blueprint",
                    "--domain-identifier",
                    domain_id,
                    "--identifier",
                    bpid,
                    "--query",
                    "name",
                    "--output",
                    "text",
                    log=False,
                )
                name = r.stdout.strip() if r.ok else bpid
                bp_configs.append(
                    (
                        name,
                        " ".join(c.get("enabledRegions", []) or ["-"]),
                        "yes" if c.get("provisioningRoleArn") else "-",
                        "yes" if c.get("manageAccessRoleArn") else "-",
                    )
                )
        res = cli.run(
            "datazone",
            "list-project-profiles",
            "--domain-identifier",
            domain_id,
            "--output",
            "json",
            log=False,
            tolerate="ValidationException|UnknownOperationException",
        )
        if res.ok and res.stdout:
            doc = json.loads(res.stdout or "{}")
            project_profiles = [
                (i.get("name", "?"), i.get("id", "?"), i.get("status", "?"))
                for i in doc.get("items", [])
            ]
        res = cli.run(
            "datazone",
            "list-projects",
            "--domain-identifier",
            domain_id,
            "--output",
            "json",
            log=False,
        )
        if res.ok and res.stdout:
            doc = json.loads(res.stdout or "{}")
            projects = [
                (i.get("name", "?"), i.get("id", "?"), i.get("projectStatus", "?"))
                for i in doc.get("items", [])
            ]

    # ------------------------- SageMaker domains: the runtimes, and the negative reading
    sm_domains: dict = {}  # profile -> [(id, name, status, network, subnets)]
    sm_details: dict = {}  # profile -> [(id, VpcOnly?, idle summary)]
    sm_apps: dict = {}  # profile -> [(app name, type, status, instance type)]
    sm_images: dict = {}  # profile -> [image names]
    for p in live:
        cli = cli_for(p)
        res = cli.run("sagemaker", "list-domains", "--output", "json", log=False)
        if not res.ok:
            logerr(p, "sagemaker list-domains", res.stderr)
            sm_domains[p] = None
            continue
        doc = json.loads(res.stdout or "{}")
        sm_domains[p] = [
            (d.get("DomainId", "?"), d.get("DomainName", "?"), d.get("Status", "?"))
            for d in doc.get("Domains", [])
        ]
        details = []
        for did, _name, _status in sm_domains[p]:
            r = cli.run(
                "sagemaker",
                "describe-domain",
                "--domain-id",
                did,
                "--output",
                "json",
                log=False,
            )
            if not r.ok:
                logerr(p, f"sagemaker describe-domain {did}", r.stderr)
                continue
            d = json.loads(r.stdout or "{}")
            net = d.get("AppNetworkAccessType", "?")
            lcm = (
                d.get("DefaultUserSettings", {})
                .get("JupyterLabAppSettings", {})
                .get("AppLifecycleManagement", {})
                .get("IdleSettings", {})
            )
            idle = f"{lcm.get('LifecycleManagement', 'absent')}" + (
                f"/{lcm.get('IdleTimeoutInMinutes')}min" if lcm.get("IdleTimeoutInMinutes") else ""
            )
            details.append((did, net, idle, " ".join(d.get("SubnetIds", []) or ["-"])))
        sm_details[p] = details
        if sm_domains[p]:
            r = cli.run(
                "sagemaker",
                "list-apps",
                "--query",
                "Apps[?Status!='Deleted'].[AppName,AppType,Status,ResourceSpec.InstanceType]",
                "--output",
                "json",
                log=False,
            )
            if r.ok and r.stdout:
                sm_apps[p] = [tuple(str(x) for x in row) for row in json.loads(r.stdout or "[]")]
            r = cli.run(
                "sagemaker",
                "list-images",
                "--query",
                "Images[].ImageName",
                "--output",
                "text",
                log=False,
            )
            if r.ok:
                sm_images[p] = r.stdout.split()

    # ---------------- the project roles and their boundary (INT-15's mechanical half)
    # Blueprint-provisioned roles carry 'datazone' in the name; the reading is which of
    # them hold a permissions boundary, and whether it is the D13 one from the sagemaker/
    # prerequisite slice.
    role_rows: dict = {}  # profile -> [(role name, boundary name or '-')]
    for p in INTERACTIVE_PROFILES:
        if p not in live:
            continue
        cli = cli_for(p)
        res = cli.run(
            "iam",
            "list-roles",
            "--query",
            "Roles[?contains(RoleName, 'datazone') || contains(RoleName, 'DataZone')]"
            ".[RoleName,PermissionsBoundary.PermissionsBoundaryArn]",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(p, "iam list-roles", res.stderr)
            continue
        rows = []
        for name, barn in json.loads(res.stdout or "[]"):
            rows.append((name, (barn or "-").split("/")[-1]))
        role_rows[p] = rows

    # ----------------------------- EFS access points in the VPN home (step 7, D24)
    efs_aps: list = []  # (access point id, filesystem, path)
    sbx = INTERACTIVE_PROFILES[0]
    if sbx in live:
        cli = cli_for(sbx)
        res = cli.run(
            "efs",
            "describe-access-points",
            "--query",
            "AccessPoints[].[AccessPointId,FileSystemId,RootDirectory.Path]",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(sbx, "efs describe-access-points", res.stderr)
        else:
            efs_aps = [tuple(str(x) for x in r) for r in json.loads(res.stdout or "[]")]

    # ------------------- the step 3 deny, read back from Identity Center (like vpn.py)
    identity_live = IDENTITY_PROFILE in live
    set_rows: list = []  # (set name, sid1 yes/no, sid2 yes/no)
    if identity_live:
        cli = cli_for(IDENTITY_PROFILE)
        note(f"reading permission sets through {IDENTITY_PROFILE} ...")
        res = cli.run(
            "sso-admin",
            "list-instances",
            "--query",
            "Instances[0].InstanceArn",
            "--output",
            "text",
            log=False,
        )
        inst_arn = res.stdout.strip() if res.ok else ""
        if not res.ok:
            logerr(IDENTITY_PROFILE, "sso-admin list-instances", res.stderr)
        if inst_arn and inst_arn != "None":
            res = cli.run(
                "sso-admin",
                "list-permission-sets",
                "--instance-arn",
                inst_arn,
                "--query",
                "PermissionSets[]",
                "--output",
                "text",
                log=False,
            )
            arns = res.stdout.split() if res.ok else []
            if not res.ok:
                logerr(IDENTITY_PROFILE, "sso-admin list-permission-sets", res.stderr)
            for arn in arns:
                r = cli.run(
                    "sso-admin",
                    "describe-permission-set",
                    "--instance-arn",
                    inst_arn,
                    "--permission-set-arn",
                    arn,
                    "--query",
                    "PermissionSet.Name",
                    "--output",
                    "text",
                    log=False,
                )
                name = r.stdout.strip() if r.ok else ""
                if name not in PERSONA_SETS:
                    continue
                r = cli.run(
                    "sso-admin",
                    "get-inline-policy-for-permission-set",
                    "--instance-arn",
                    inst_arn,
                    "--permission-set-arn",
                    arn,
                    "--query",
                    "InlinePolicy",
                    "--output",
                    "text",
                    log=False,
                )
                if not r.ok:
                    logerr(IDENTITY_PROFILE, f"get-inline-policy ({name})", r.stderr)
                    set_rows.append((name, "(call failed)", "(call failed)"))
                else:
                    body = r.stdout
                    set_rows.append((name, *("yes" if sid in body else "no" for sid in STEP3_SIDS)))

    # -------------------------------------------------------------------------- the checks
    # US-1: exactly one DataZone domain, in Data Governance, version V2. Absent = not
    # built yet; a second is INT-12's fallback happening by accident.
    if data_live and dz_domains.get(DATA_PROFILE) is not None:
        doms = dz_domains[DATA_PROFILE]
        if not doms:
            checks.note(
                "US-1",
                "the unified domain in Data Governance",
                "none - expected before Stage 6 step 1.",
            )
        elif len(doms) > 1:
            checks.fail(
                "US-1",
                "the unified domain in Data Governance",
                f"{len(doms)} domains - D26 says exactly one; a second is a registry split "
                "nobody decided.",
            )
        elif doms[0][2] not in ("V2", "?"):
            checks.fail(
                "US-1",
                f"domain {doms[0][0]} version",
                f"domainVersion={doms[0][2]} - a V1 DataZone domain is not the SageMaker "
                "unified domain D26 chose.",
            )
        else:
            checks.ok("US-1", f"one unified domain ({doms[0][0]})", f"version {doms[0][2]}")

    # US-2: no DataZone domain anywhere else (1c's root deny holding), and NOTHING
    # SageMaker-shaped in Data Governance (the registry-not-runtime negative deliverable).
    for p in live:
        if p == DATA_PROFILE or dz_domains.get(p) is None:
            continue
        if dz_domains[p] == SCP_DENIED:
            checks.ok(
                "US-6",
                f"datazone reads denied in {p}",
                "the Workloads OU denying datazone:* - D28's headless control holding",
            )
            continue
        if dz_domains[p]:
            checks.fail(
                "US-2",
                f"DataZone domain in {p}",
                f"{len(dz_domains[p])} domain(s) outside Data Governance - either INT-12's "
                "fallback happened by accident or the 1c root deny is not holding.",
            )
    if data_live and sm_domains.get(DATA_PROFILE) is not None:
        if sm_domains[DATA_PROFILE]:
            checks.fail(
                "US-2",
                "SageMaker domain in Data Governance",
                "the registry account runs compute - the premise of the Data OU's "
                "sagemaker:Create* wildcard is broken (step 0's second preflight).",
            )
        else:
            checks.ok(
                "US-2",
                "Data Governance holds no SageMaker domain",
                "the registry/runtime split holding (D26)",
            )

    # US-3: blueprint configurations exist for the enabled blueprints and no others
    # (Tooling, Lakehouse in its Glue/Athena form, ML - step 1). Names are read, not
    # assumed; the check is presence + the Redshift absence.
    if data_live and domain_id:
        if not bp_configs:
            checks.note(
                "US-3",
                "blueprint configurations",
                "none - expected before Stage 6 step 1.",
            )
        else:
            bad = [n for n, _r, _p, _m in bp_configs if "redshift" in n.lower()]
            if bad:
                checks.fail(
                    "US-3",
                    "Redshift blueprint enabled",
                    f"{', '.join(bad)} - D26/D12 exclude the Redshift Serverless variant "
                    "by decision.",
                )
            else:
                checks.ok(
                    "US-3",
                    f"{len(bp_configs)} blueprint configuration(s)",
                    "none of them Redshift",
                )

    # US-4: the two project profiles, by their contracted names.
    if data_live and domain_id:
        have = {n for n, _i, _s in project_profiles}
        missing = [n for n in PROJECT_PROFILE_NAMES if n not in have]
        if not project_profiles:
            checks.note("US-4", "project profiles", "none - expected before Stage 6 step 1.")
        elif missing:
            checks.fail(
                "US-4",
                "project profiles",
                f"missing {', '.join(missing)} - the two-profile shape (experimentation -> "
                "Sandbox, engineering -> Development) is step 1's contract.",
            )
        else:
            checks.ok("US-4", "project profiles", "experimentation and engineering exist")

    # US-5: every blueprint-provisioned SageMaker AI domain in the Interactive accounts is
    # VpcOnly. PublicInternetOnly is the whole VPC design bypassed at the app layer.
    for p in INTERACTIVE_PROFILES:
        for did, net, _idle, _subnets in sm_details.get(p, []):
            if net == "VpcOnly":
                checks.ok("US-5", f"{p} domain {did}", "AppNetworkAccessType=VpcOnly")
            else:
                checks.fail(
                    "US-5",
                    f"{p} domain {did}",
                    f"AppNetworkAccessType={net} - step 1 requires VpcOnly; anything else "
                    "puts every app outside the endpoint policies and the flow logs.",
                )

    # US-6: no SageMaker domain in the headless accounts (D28).
    for p in HEADLESS_PROFILES:
        if p in live and sm_domains.get(p):
            checks.fail(
                "US-6",
                f"SageMaker domain in {p}",
                "deployment targets are never associated and never carry a domain (D28).",
            )

    # US-7: idle shutdown configured on every Interactive domain (step 8).
    for p in INTERACTIVE_PROFILES:
        for did, _net, idle, _subnets in sm_details.get(p, []):
            if idle.startswith("ENABLED"):
                checks.ok("US-7", f"idle shutdown on {p} {did}", idle)
            else:
                checks.fail(
                    "US-7",
                    f"idle shutdown on {p} {did}",
                    f"IdleSettings {idle} - the mandatory cost control of step 8; without "
                    "it D11 depends on the user's habits.",
                )

    # US-8: every blueprint-provisioned project role carries a permissions boundary,
    # and it is the D13 one (INT-15). Roles with no boundary are the INT-15 failure
    # shape made visible.
    for p, rows in role_rows.items():
        if not rows:
            continue
        unbounded = [n for n, b in rows if b == "-"]
        wrong = [n for n, b in rows if b != "-" and BOUNDARY_NAME_FRAGMENT not in b]
        if unbounded:
            checks.fail(
                "US-8",
                f"project-role boundary in {p}",
                f"{len(unbounded)} datazone role(s) with NO permissions boundary "
                f"({', '.join(unbounded[:3])}...) - INT-15's mechanism is absent.",
            )
        elif wrong:
            checks.note(
                "US-8",
                f"project-role boundary in {p}",
                f"boundary present but not '{BOUNDARY_NAME_FRAGMENT}': {', '.join(wrong[:3])}",
            )
        else:
            checks.ok(
                "US-8",
                f"project-role boundary in {p}",
                f"all {len(rows)} datazone role(s) bounded",
            )

    # US-9: the step 3 deny Sids in the persona sets - together or not at all
    # (Lesson 14; the same one-fragment rule as Stage 4 step 8.2).
    if identity_live and set_rows:
        for i, sid in enumerate(STEP3_SIDS, start=1):
            carrying = [n for n, *v in set_rows if v[i - 1] == "yes"]
            missing = [n for n in PERSONA_SETS if n not in carrying]
            if not carrying:
                checks.note(
                    "US-9",
                    f"{sid} in the persona sets",
                    "absent from all six - expected before Stage 6 step 3.",
                )
            elif missing:
                checks.fail(
                    "US-9",
                    f"{sid} in the persona sets",
                    f"present in {len(carrying)} of six, missing from {', '.join(missing)} "
                    "- a partial rollout is Lesson 14.",
                )
            else:
                checks.ok("US-9", f"{sid} in the persona sets", "all six carry it")

    # US-10: the burn meter - running apps are the [E] resource make down must delete
    # (conventions 6; scripts/down-studio-apps.py owes its body to Stage 6 step 8).
    running = [(p, a) for p, apps in sm_apps.items() for a in apps if a[2] == "InService"]
    if running:
        checks.note(
            "US-10",
            f"{len(running)} running app(s)",
            "metered by the hour - expected during a session, a leak after `make down` "
            "(the same reading its hook makes per env).",
        )
    elif any(sm_domains.get(p) for p in INTERACTIVE_PROFILES):
        checks.ok("US-10", "no running apps", "zero everywhere is D11 working")

    # ---------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("Unified Studio - the Stage 6 evidence: registry, runtimes, boundaries")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/studio.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. DataZone domains, in EVERY account (one expected, in one account)
  3. The registry's contents: blueprints, project profiles, projects
  4. SageMaker AI domains per account (the runtimes - and the negative reading)
  5. Running apps and registered images (the burn, and INT-17's mechanical half)
  6. The project roles and their permissions boundary (INT-15)
  7. EFS access points in the VPN home (step 7, D24)
  8. The step 3 deny, per permission set
  9. CHECKS
 10. The accounts nothing here is measuring
 11. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 6 RUNS - each such reading
    is a note, not a failure; it becomes a regression the moment the stage closes.
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT - section 10 names what nothing here
    reached.
  - THIS IS A CONTROL-PLANE READING. The portal reading (INT-16), the lake reads,
    the egress pairs and the boundary's SURVIVAL of a blueprint reconciliation
    (INT-15) are behavioural proofs; re-running this file after provisioning is
    how the survival half is diffed.

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
        rep.h1("2. DataZone domains, in EVERY account (one expected, in one account)")
        rows = ["PROFILE\tDOMAIN\tNAME\tVERSION\tSTATUS"]
        for p in live:
            doms = dz_domains.get(p)
            if doms is None:
                rows.append(f"{p}\t(call failed)\t-\t-\t-")
            elif doms == SCP_DENIED:
                rows.append(f"{p}\t(denied by SCP - Workloads datazone:* ceiling, D28)\t-\t-\t-")
            elif not doms:
                rows.append(f"{p}\t(none)\t-\t-\t-")
            else:
                for i, n, v, s in doms:
                    rows.append(f"{p}\t{i}\t{n}\t{v}\t{s}")
        rep.tabulate(rows)
        rep.text("""
Exactly one row may name a domain, and its profile must be awsds-infra-data (D26).
A domain anywhere else is either INT-12's per-account fallback happening by
accident or the 1c root deny (DenyDataZoneDomainOutsideDataOu) not holding.""")

        # ==============================================================================
        rep.h1("3. The registry's contents: blueprints, project profiles, projects")
        if not data_live:
            rep.line(f"{DATA_PROFILE} was not measured - nothing to show.")
        elif not domain_id:
            rep.line("No domain yet. Expected before Stage 6 step 1.")
        else:
            rep.line(f"DOMAIN_ID={domain_id}")
            rep.line()
            if bp_configs:
                rep.tabulate(
                    ["BLUEPRINT\tREGIONS\tPROVISIONING ROLE\tMANAGE-ACCESS ROLE"]
                    + [f"{n}\t{r}\t{pr}\t{m}" for n, r, pr, m in bp_configs]
                )
            else:
                rep.line("No blueprint configuration.")
            rep.line()
            if project_profiles:
                rep.tabulate(
                    ["PROJECT PROFILE\tID\tSTATUS"]
                    + [f"{n}\t{i}\t{s}" for n, i, s in project_profiles]
                )
            else:
                rep.line("No project profile.")
            rep.line()
            if projects:
                rep.tabulate(["PROJECT\tID\tSTATUS"] + [f"{n}\t{i}\t{s}" for n, i, s in projects])
            else:
                rep.line("No project.")

        # ==============================================================================
        rep.h1("4. SageMaker AI domains per account (the runtimes - and the negative reading)")
        rows = ["PROFILE\tDOMAIN\tNETWORK\tIDLE SETTINGS\tSUBNETS"]
        for p in live:
            details = sm_details.get(p, [])
            doms = sm_domains.get(p)
            if doms is None:
                rows.append(f"{p}\t(call failed)\t-\t-\t-")
            elif not doms:
                rows.append(f"{p}\t(none)\t-\t-\t-")
            else:
                for did, net, idle, subnets in details:
                    rows.append(f"{p}\t{did}\t{net}\t{idle}\t{subnets}")
        rep.tabulate(rows)
        rep.text("""
Domains belong ONLY in the Interactive columns (the blueprint targets). One in
Data Governance breaks the registry premise (US-2); one in Production or Staging
breaks D28 (US-6). VpcOnly and an ENABLED idle setting are steps 1 and 8.""")

        # ==============================================================================
        rep.h1("5. Running apps and registered images (the burn, and INT-17's mechanical half)")
        any_apps = False
        for p in INTERACTIVE_PROFILES:
            apps = sm_apps.get(p, [])
            if apps:
                any_apps = True
                rep.h2(p)
                rep.tabulate(["APP\tTYPE\tSTATUS\tINSTANCE"] + ["\t".join(a) for a in apps])
        if not any_apps:
            rep.line("No apps (or no domain yet). Zero running apps is D11 working.")
        rep.line()
        for p in INTERACTIVE_PROFILES:
            imgs = sm_images.get(p, [])
            rep.line(f"{p}: registered SageMaker images: {' '.join(imgs) if imgs else '(none)'}")
        rep.text("""
The images line is INT-17's mechanical half: whatever mechanism makes dev-env
selectable, the registration it produces (aws_sagemaker_image or the blueprint's
equivalent) shows up here - and Stage 8 step 1's pipeline is written against it.""")

        # ==============================================================================
        rep.h1("6. The project roles and their permissions boundary (INT-15)")
        if not role_rows:
            rep.line("No datazone-named role in any Interactive account (or not measured).")
        else:
            for p, rows_ in role_rows.items():
                rep.h2(p)
                if rows_:
                    rep.tabulate(["ROLE\tPERMISSIONS BOUNDARY"] + [f"{n}\t{b}" for n, b in rows_])
                else:
                    rep.line("(none)")
        rep.text("""
Presence, never survival: whether the boundary outlives a blueprint
reconciliation is INT-15's behavioural half - provision, wait, re-run this file
and diff section 6.""")

        # ==============================================================================
        rep.h1("7. EFS access points in the VPN home (step 7, D24)")
        if efs_aps:
            rep.tabulate(["ACCESS POINT\tFILESYSTEM\tPATH"] + ["\t".join(a) for a in efs_aps])
        else:
            rep.line("None. Expected before Stage 5 step 10 / Stage 6 step 7.")

        # ==============================================================================
        rep.h1("8. The step 3 deny, per permission set")
        rep.text(f"""The reading greps each set's inline policy for the Sids {", ".join(STEP3_SIDS)} -
presence, never sufficiency: the conditions inside them are proven by the stage's
own deny pair (a job submitted with no VPC config, an oversized instance type).

""")
        if not identity_live:
            rep.line(f"{IDENTITY_PROFILE} was not measured - the sets were not read.")
        elif not set_rows:
            rep.line("No project permission set was found - see section 11.")
        else:
            rep.tabulate(
                [f"PERMISSION SET\t{STEP3_SIDS[0]}\t{STEP3_SIDS[1]}"]
                + [f"{n}\t{a}\t{b}" for n, a, b in sorted(set_rows)]
            )

        # ==============================================================================
        rep.h1("9. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  US-1   exactly one DataZone V2 domain, in Data Governance (step 1; D26)
  US-2   no domain anywhere else; nothing SageMaker-shaped in Data Governance
         (step 0's second preflight; the registry/runtime split)
  US-3   blueprint configurations exist and none is Redshift (step 1; D12/D26)
  US-4   the experimentation and engineering project profiles exist (step 1)
  US-5   every Interactive SageMaker AI domain is VpcOnly (step 1)
  US-6   the deployment targets stay headless (D28): no SageMaker domain there,
         and datazone reads denied by the Workloads ceiling read as the control
  US-7   idle shutdown ENABLED on every Interactive domain (step 8)
  US-8   every blueprint-provisioned project role carries the D13 boundary
         (step 2, INT-15 - presence half only)
  US-9   the step 3 deny Sids reach all six persona sets together (Lesson 14)
  US-10  running apps reported as the burn they are (conventions 6)""")

        # ==============================================================================
        rep.h1("10. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 9 as a pass.

  - `Staging` has no profile until the vend: US-6's Staging half is unmeasurable
    until then (its absence from section 1 is the design, not coverage).
  - Every Sandbox beyond unit 1 has no profile until Stage 14 - re-run after
    each vend; the domain association list must grow with N (D35, INT-12).
  - The portal (INT-16) is a browser surface; no profile reads it.""")

        # ==============================================================================
        rep.h1("11. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/studio.py")

    # ------------------------------------------------------------------------------ run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 11)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 9)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
