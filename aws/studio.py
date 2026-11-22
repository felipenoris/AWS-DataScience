#!/usr/bin/env -S uv run --quiet
# studio.py - Stage 6's evidence, registry and runtimes side by side: the one DataZone V2
# domain in Data Governance (a registry, so also the negative reading: no SageMaker resource
# may exist there), its blueprint configurations with the grant that authorizes each, its
# project profiles, the blueprint-provisioned SageMaker AI domains in each Interactive account
# (VPC-only, private subnets, idle shutdown, the house image's pinned version), the D13
# permissions boundary on the project roles (INT-15's mechanical half), the step 3 deny Sids in
# the persona sets, the dev-env image registration (INT-17's mechanical half), the running
# apps - the burn meter of the one [E] thing Terraform does not own - and the buckets a deleted
# environment left behind.
#
#   needs:    a live SSO session, and nothing else:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/studio.py                      # every awsds-* profile
#             ./aws/studio.py awsds-infra-data     # only the ones named
#             python3 aws/studio.py -              # CloudShell, ambient credentials
#   writes:   aws/output/studio.txt   (untracked - see .gitignore)
#   reads:    datazone:ListDomains, GetDomain, ListEnvironmentBlueprintConfigurations,
#             GetEnvironmentBlueprint, ListPolicyGrants, ListProjectProfiles, GetProjectProfile,
#             ListProjects, GetProject, ListEnvironments, GetEnvironment, ListSubscriptionTargets,
#             sagemaker:ListDomains, DescribeDomain, ListTags, ListApps, ListImages,
#             ListImageVersions,
#             iam:ListRoles, GetRole, ListAttachedRolePolicies and ListRolePolicies on a flow
#             environment's role (EXC-27),
#             cloudformation:DescribeStacks, tag:GetResources, s3:GetBucketTagging,
#             sso-admin:ListInstances, ListPermissionSets, DescribePermissionSet,
#             GetInlinePolicyForPermissionSet, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# The subject spans accounts, so this script is multi-profile: under D26 one account holds the
# registry and other accounts hold the compute it provisions, so "the domain is a registry, not
# a runtime" is only readable with Data Governance and the two Interactive accounts side by
# side, and a SageMaker domain in the wrong column is the finding. Section 1 prints the caller
# ARN of every profile.
#
# The contracts it reads, each named in the stage file so a rename fails loudly:
#   - the project profiles' names: `experimentation`, `lake-publishing`, `deployment-staging`,
#     `deployment-production` and `Generative AI model governance`; `engineering` is retired
#   - the step 3 deny Sids are DenySageMakerJobsOffVpc and DenySageMakerInstanceCeiling
#   - the D13 boundary on project roles is named awsds-<env>-project-boundary (step 2)
#   - a flow environment's own role, AmazonBedrockFlowServiceRole-*, is EXC-27 while its shape
#     holds (awslib/flowrole.py)
#
# What it cannot see, since an empty listing and a missing account look alike:
#   - The behavioural proofs - a notebook reading the lake
#     through the LF share, the egress pair under designs A and B - are the stage's own,
#     run from a browser and a notebook (Lesson 20).
#   - Whether a boundary survives a blueprint reconciliation (INT-15) is answered by
#     provisioning, waiting, and re-running this script - the diff is the evidence.
#   - Whether the SCP carve-out lets Data Governance create a domain (step 0) is a probe,
#     not a reading - a describe call cannot exercise a deny.

from __future__ import annotations

import json
import sys

from awslib import context, flowrole, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "studio.txt"

# The registry account and the blueprint targets (D26, D35 - the sandbox side is per unit).
DATA_PROFILE = "awsds-infra-data"
INTERACTIVE_PROFILES = ("awsds-infra-sandbox-1",)

# A member account whose association was removed on purpose: its blueprint configurations are
# destroyed and the domain is no longer shared into it, but its OU has not changed yet, so
# `datazone:*` is not denied and it is not headless either. Without this list the two "nothing
# here" notes below read `correct BEFORE this account's association` - green, while describing
# the wrong side of the event. Empty again since 2026-09-06: the one row it ever held was held
# for the few hours between step 1.5 (the association removed) and step 3.4 (the OU moved), and
# that account is a Workloads member now, denied `datazone:*` and carried by HEADLESS_PROFILES
# below. The state is not hypothetical - any member retired this way passes through it.
RETIRED_MEMBER_PROFILES: tuple[str, ...] = ()
IDENTITY_PROFILE = "awsds-infra-identity"
# The deployment targets: no person works there and no SageMaker AI domain may appear (D17). Since
# Stage 19 decision 6 (b) each is associated to the domain and holds one deployment project, born
# of its own profile, with two blueprint configurations (DEPLOYMENT_BLUEPRINTS); the Workloads SCP
# admits this script's InfrastructureAccess session to DataZone there once that stage's step 4.1 is
# applied, and before it the refusal reads as that step pending. `awsds-infra-staging` resolves
# since Stage 6b step 5.0; the account behind it is the renamed `Development`.
HEADLESS_PROFILES = ("awsds-infra-prod", "awsds-infra-staging")
# What <env>/studio/ configures in a deployment target (Stage 19 step 4.4): Tooling, with spaces off
# in the deployment profile, and DataLake, the home of an application's product database.
DEPLOYMENT_BLUEPRINTS = ("Tooling", "DataLake")
# The deployment profiles, one per target (Stage 19 step 4.5): rows of
# data-governance/governance/'s locals.tf behind `deployment_profiles_enabled`. Admitted when
# present, and their absence is no failure: the stage creates them after each target's blueprints.
DEPLOYMENT_PROFILE_NAMES = ("deployment-staging", "deployment-production")
# Which target each deployment profile provisions in, whose InfrastructureAccess owns the one
# project born of it (Stage 19 step 4.6, INV-21).
DEPLOYMENT_TARGET_OF = {
    "deployment-staging": "awsds-infra-staging",
    "deployment-production": "awsds-infra-prod",
}

# The contracts (see header).
# Decision 5's category 1 (2026-08-19; docs/SMUS.md carries the reference table): the only
# blueprints that may be enabled. A category-2 blueprint (MLExperiments, for example)
# joins this tuple in the same commit that enables it (Lesson 14). Names are spelled as
# `datazone list-environment-blueprints` returns them - `EmrServerless`, not `EMRServerless` -
# and the AmazonBedrock family is enumerated rather than matched by prefix, so a blueprint AWS
# adds under that namespace surfaces as a finding instead of passing as expected (Lesson 38).
#
# The same list lives in three places (Lesson 14): here, terraform-modules/sagemaker-prereqs/'s
# blueprint_names default, and data-governance/governance/locals.tf. One commit moves all three.
BLUEPRINT_ALLOWLIST = (
    "Tooling",
    "DataLake",
    "S3Bucket",
    "S3TableCatalog",
    "EmrServerless",
    "AmazonBedrockChatAgent",
    "AmazonBedrockEvaluation",
    "AmazonBedrockFlow",
    "AmazonBedrockFunction",
    "AmazonBedrockGuardrail",
    "AmazonBedrockPrompt",
    # Out of category 2 at Stage 17 pass 1 (decision 2); MLExperiments, the tracking server,
    # stays in category 2 and fails here.
    "MLflowApp",
    # Out of category 2 at Stage 17 step 7.0a (decision 1).
    "AmazonBedrockKnowledgeBase",
    # Out of `undefined` at 6d decision due 15 (b), 2026-10-30: the pilot's spaces domain, RStudio on.
    "SageMakerAIDomain",
)
# `experimentation` provisions into Sandbox. `engineering` was retired at Stage 6b step 1.1:
# Development became the headless `Staging`, so nothing provisions a Studio project there. The
# retired name is kept so that `engineering` reappearing reads as the finding it is, rather than
# as a profile this file has no opinion about.
PROJECT_PROFILE_NAMES = ("experimentation",)
# A profile admitted for a stage's window alone. Empty since Stage 18 step 8.2, which deleted
# `deployment`, so a `deployment` profile reappearing reads as an uncontracted one.
WINDOW_PROFILE_NAMES: tuple = ()
# The lake-publishing pilot (Stage 6f decision 1, shape (b), step 11): its profile provisions into the
# domain's own account, and its one blueprint configuration there is the only one US-3 admits in that
# account. Both are rows of data-governance/governance/'s locals.tf and data-governance/publishing/,
# behind scripts/tfhygiene/backend.py's LAKE_PUBLISHERS, and leave with the pilot's rollback.
PILOT_PROFILE_NAMES = ("lake-publishing",)
DOMAIN_ACCOUNT_BLUEPRINTS = ("Tooling",)
# The governance project's profile (Stage 17 decision 13): no environment configuration, so it
# provisions nothing anywhere. The console's model access publishes into the project born of it,
# GenerativeAIModelGovernanceProject, and the name is the console's contract, not this file's.
MODEL_GOVERNANCE_PROFILE_NAMES = ("Generative AI model governance",)
RETIRED_PROFILE_NAMES = ("engineering",)
STEP3_SIDS = ("DenySageMakerJobsOffVpc", "DenySageMakerInstanceCeiling")
BOUNDARY_NAME_FRAGMENT = "project-boundary"

# US-13 (6d decision 16 (a), INV-23): a project born of `experimentation` holds the
# SageMakerAIDomain blueprint's domain, which pins the house image at the version the profile's
# image lists name. A domain is told apart by the tag the blueprint writes, never by its name: an
# unnamed blueprint domain takes the Tooling domains' pattern (6d 2.7 step 5). The projects created
# before the profile changed keep their Tooling domain beside it (EXC-26), named here by the
# portal's names, which are the user's.
BLUEPRINT_TAG = "AmazonDataZoneBlueprint"
PROJECT_TAG = "AmazonDataZoneProject"
PINNED_BLUEPRINT = "SageMakerAIDomain"
OPEN_ENTRY_BLUEPRINT = "Tooling"
TOOLING_DOMAIN_PROJECTS = ("app-etl-dev", "eighth-experimentation", "test-experimentation")
PIN_PARAMETERS = {"JupyterLab": "customImagesJupyterLab", "CodeEditor": "customImagesCodeEditor"}

# The persona sets the step 3 fragment reaches (same set as Stage 4 step 8.2).
PERSONA_SETS = (
    "DataScientistAccess",
    "DataScientistStagingAccess",
    "DataScientistProdAccess",
    "DeploymentManagerAccess",
    "GovernanceManagerAccess",
    "DevEnvStewardAccess",
)


def profile_pins(doc: dict) -> dict:
    """App type -> (image name, version) from a profile's SageMakerAIDomain image lists.

    Each list is JSON with one entry here. An absent configuration, parameter or version leaves
    the app type out, and US-13 reports the gap.
    """
    pins: dict = {}
    for cfg in doc.get("environmentConfigurations", []):
        if cfg.get("name") != PINNED_BLUEPRINT:
            continue
        overrides = (cfg.get("configurationParameters") or {}).get("parameterOverrides", [])
        values = {o.get("name"): o.get("value") for o in overrides}
        for app, param in PIN_PARAMETERS.items():
            try:
                entries = json.loads(values.get(param) or "[]")
            except json.JSONDecodeError:
                continue
            if len(entries) == 1 and entries[0].get("ImageVersionNumber") is not None:
                pins[app] = (entries[0].get("ImageName"), entries[0].get("ImageVersionNumber"))
    return pins


def judge_image_pins(
    checks: Checks,
    p: str,
    rows: list,
    profile_pin: dict | None,
    tops: dict,
    project_names: dict,
    born: dict | None,
) -> None:
    """US-13 on one Interactive account: the profile's pin, each domain by its blueprint tag, then
    each ACTIVE project born of the profile against the blueprint domains.

    rows are (domain id, tags or None, {app type: [(image, version)]}); tops maps an image to its
    newest CREATED version; project_names maps a project id to the portal's name; born maps the
    id of each ACTIVE project born of the profile to its name, None when unread.
    """
    what = f"{PROJECT_PROFILE_NAMES[0]}'s pin for {p}"
    if profile_pin is None:
        checks.note("US-13", what, "unread - each domain is read against the newest version.")
    elif not profile_pin:
        checks.fail(
            "US-13",
            what,
            f"no image in its {PINNED_BLUEPRINT} configuration: a project born of it gets the "
            "SageMaker Distribution alone (INV-23).",
        )
    else:
        behind = [
            f"{app} {n} v{v}, the newest CREATED v{tops[n]}"
            for app, (n, v) in profile_pin.items()
            if tops.get(n) is not None and v != tops[n]
        ]
        pins = ", ".join(f"{app} {n} v{v}" for app, (n, v) in profile_pin.items())
        if behind:
            checks.fail(
                "US-13",
                what,
                f"{'; '.join(behind)} - the pin's pull request on data-governance/governance/ "
                "is pending (dev-env.md §B).",
            )
        elif all(tops.get(n) is not None for n, _v in profile_pin.values()):
            checks.ok("US-13", what, f"{pins}, the newest CREATED version")
        else:
            checks.note("US-13", what, f"{pins}; the newest version was not read.")
    for did, tags, entries in rows:
        if tags is None:
            checks.note(
                "US-13", f"{p} domain {did}", "tags unread (section 10): blueprint unknown."
            )
            continue
        project = project_names.get(tags.get(PROJECT_TAG, ""), tags.get(PROJECT_TAG) or "untagged")
        what = f"{p} domain {did} ({project})"
        blueprint = tags.get(BLUEPRINT_TAG)
        if blueprint == OPEN_ENTRY_BLUEPRINT:
            if project in TOOLING_DOMAIN_PROJECTS:
                checks.note(
                    "US-13",
                    what,
                    "the Tooling domain kept beside the blueprint's (EXC-26); its entry with no "
                    "version is not judged",
                )
            else:
                checks.fail(
                    "US-13",
                    what,
                    "a Tooling domain outside EXC-26's projects: a project born since 2026-11-18 "
                    "holds the blueprint's domain alone (INV-23), and this one offers every "
                    "version unpinned.",
                )
            continue
        if blueprint != PINNED_BLUEPRINT:
            checks.note(
                "US-13",
                what,
                f"{BLUEPRINT_TAG}={blueprint or 'absent'} - not a domain US-13 judges",
            )
            continue
        shape, lag, pinned = [], [], []
        for app in PIN_PARAMETERS:
            have = entries.get(app, [])
            if len(have) != 1 or have[0][1] is None:
                shape.append(f"{app} {have or 'no entry'}")
                continue
            name, ver = have[0]
            pinned.append(f"{app} {name} v{ver}")
            ref = (profile_pin or {}).get(app)
            if ref is None and tops.get(name) is not None:
                ref = (name, tops[name])
            if ref is not None and (name, ver) != tuple(ref):
                lag.append(f"{app} {name} v{ver} against {ref[0]} v{ref[1]}")
        if shape:
            checks.fail(
                "US-13",
                what,
                f"{'; '.join(shape)} - a blueprint domain pins one version per app type (INV-23).",
            )
        elif lag:
            checks.fail(
                "US-13",
                what,
                f"{'; '.join(lag)} - the project owner's Update project is pending "
                "(dev-env.md §B).",
            )
        else:
            checks.ok("US-13", what, ", ".join(pinned))
    # A domain whose tags were unread could be the project's, so a missing one is judged only when
    # every domain's tags were read.
    if born is None or any(tags is None for _did, tags, _e in rows):
        return
    held = {
        tags.get(PROJECT_TAG)
        for _did, tags, _e in rows
        if tags.get(BLUEPRINT_TAG) == PINNED_BLUEPRINT
    }
    if born and all(pid in held for pid in born):
        checks.ok(
            "US-13",
            f"{p} projects of {PROJECT_PROFILE_NAMES[0]}",
            f"{len(born)} ACTIVE, each holding a {PINNED_BLUEPRINT} domain: "
            + ", ".join(sorted(born.values())),
        )
    for pid, name in sorted(born.items(), key=lambda item: item[1]):
        if pid not in held:
            checks.fail(
                "US-13",
                f"{p} project {name}",
                f"born of {PROJECT_PROFILE_NAMES[0]} with no {PINNED_BLUEPRINT} domain here: the "
                "profile's ON_CREATE environment gives every project one (INV-23).",
            )


# US-14 (INV-24): terraform-modules/sagemaker-prereqs/grants.tf declares one
# CREATE_ENVIRONMENT_FROM_BLUEPRINT grant on every blueprint configuration, to every project of the
# root domain unit with designation CONTRIBUTOR, child units excluded. The grant decides which
# blueprints a project's Resource blueprints page deploys (docs/SMUS.md §Resource blueprints), and a
# blueprint's Authorization tab adds one outside Terraform's state.
GRANT_DESIGNATION = "CONTRIBUTOR"


def is_module_grant(principals: list, root_unit: str) -> bool:
    """True when a configuration's grants are exactly the one sagemaker-prereqs declares."""
    if len(principals) != 1:
        return False
    project = principals[0].get("project") or {}
    unit = (project.get("projectGrantFilter") or {}).get("domainUnitFilter") or {}
    return (
        project.get("projectDesignation") == GRANT_DESIGNATION
        and not project.get("projectIdentifier")
        and not project.get("userCreatedDesignationId")
        and unit.get("domainUnit") == root_unit
        and not unit.get("includeChildDomainUnits")
    )


def grant_text(principals: list | None, root_unit: str) -> str:
    """A configuration's grants, one phrase per principal: section 3's column, US-14's detail."""
    if principals is None:
        return "(unread)"
    if not principals:
        return "none"
    phrases = []
    for principal in principals:
        project = principal.get("project")
        if project is None:
            phrases.append(json.dumps(principal, separators=(",", ":")))
            continue
        who = project.get("projectDesignation", "?")
        if project.get("userCreatedDesignationId"):
            who = f"designation {project['userCreatedDesignationId']}"
        unit = (project.get("projectGrantFilter") or {}).get("domainUnitFilter") or {}
        if project.get("projectIdentifier"):
            scope = f"project {project['projectIdentifier']}"
        elif unit.get("domainUnit") == root_unit:
            scope = "root unit"
        elif unit:
            scope = f"unit {unit.get('domainUnit', '?')}"
        else:
            scope = "no filter"
        if unit.get("includeChildDomainUnits"):
            scope += " and its children"
        phrases.append(f"{who}, {scope}")
    return "; ".join(phrases)


# US-15 (INV-25): the S3Bucket template keeps its bucket when DataZone deletes the environment's
# stack, and the bucket keeps the environment's tags while its policy is deleted (SUP-394). DataZone
# answers GetEnvironment from a caller outside the project "Environment not found" for an environment
# that exists (SUP-157), so the reading stays in the bucket's own account: every stack DataZone
# deploys carries the environment's tag, and a tagged resource whose environment no live stack
# carries was left by a deleted one. The tagging API reads one Region, the domain's, where every
# environment deploys.
ENV_TAG = "AmazonDataZoneEnvironment"


def short_arn(arn: str) -> str:
    """An ARN without its partition, Region and account: `s3 <bucket>`, `logs log-group:<name>`."""
    parts = arn.split(":", 5)
    return f"{parts[2]} {parts[5]}" if len(parts) == 6 else arn


def bucket_name(arn: str) -> str | None:
    """The bucket an ARN names; None for any other resource, an access point among them."""
    parts = arn.split(":", 5)
    if len(parts) == 6 and parts[2] == "s3" and not parts[3] and "/" not in parts[5]:
        return parts[5]
    return None


def env_text(tags: dict) -> str:
    """The environment, project and blueprint a resource's DataZone tags name."""
    return (
        f"environment {tags.get(ENV_TAG, '?')}, project {tags.get('AmazonDataZoneProject', '?')}, "
        f"{tags.get('AmazonDataZoneBlueprint', '?')}"
    )


def judge_leftovers(
    checks: Checks, p: str, live_envs: set | None, tagged: list | None, reread
) -> None:
    """US-15 in one account.

    `tagged` holds (arn, tags) for every resource carrying ENV_TAG, `live_envs` the environment ids
    a live stack carries, and `reread(bucket)` answers ("ok", tags), ("gone", {}) or ("unread", {}).
    A bucket is read again before it is judged, since the tagging index lags a deletion.
    """
    what = f"buckets left by deleted environments in {p}"
    if live_envs is None or tagged is None:
        checks.note("US-15", what, "unjudged - a listing failed (section 10).")
        return
    orphans, stale, others = [], [], []
    for arn, tags in tagged:
        if tags.get(ENV_TAG) in live_envs:
            continue
        name = bucket_name(arn)
        if name is None:
            others.append(short_arn(arn))
            continue
        state, real = reread(name)
        env = real.get(ENV_TAG) if state == "ok" else tags.get(ENV_TAG)
        if state == "gone" or env is None or env in live_envs:
            stale.append(name)
            continue
        orphans.append(f"{name} ({env_text(real if state == 'ok' else tags)})")
    if orphans:
        checks.fail(
            "US-15",
            what,
            f"{'; '.join(orphans)} - no live stack carries the environment, and the bucket stayed "
            "with its policy deleted (SUP-394). An administrator empties and deletes it (INV-25).",
        )
    else:
        n = sum(1 for arn, tags in tagged if bucket_name(arn) and tags.get(ENV_TAG) in live_envs)
        checks.ok(
            "US-15",
            f"buckets of environments in {p}",
            f"{n} bucket(s) carry the tag of an environment whose stack is live"
            if n
            else f"no bucket carries an environment's tag; {len(live_envs)} environment stack(s) live",
        )
    if stale:
        checks.note(
            "US-15",
            what,
            f"{', '.join(stale)}: the tagging index lists a bucket S3 no longer holds or no longer "
            "tags so - re-run.",
        )
    if others:
        shown = ", ".join(others[:8]) + (f" and {len(others) - 8} more" if len(others) > 8 else "")
        checks.note(
            "US-15",
            f"other resources left by deleted environments in {p}",
            f"{len(others)}: {shown} - no live stack carries their environment's tag. A deleted "
            "Tooling environment leaves its log group (SUP-174); each is deleted by hand.",
        )


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    account_of = {c.profile: c.account for c in callers if c.live}
    checks = Checks()

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    def config_grants(cli: AwsCli, profile: str, domain: str, blueprint_id: str) -> list | None:
        """US-14's reading: the principals of one configuration's grants, None when unread.

        The entity is `<account-id>:<blueprint-id>`, the account being the configuration's
        owner, which is the caller here (sagemaker-prereqs/grants.tf).
        """
        res = cli.run(
            "datazone",
            "list-policy-grants",
            "--domain-identifier",
            domain,
            "--entity-type",
            "ENVIRONMENT_BLUEPRINT_CONFIGURATION",
            "--entity-identifier",
            f"{account_of.get(profile, '?')}:{blueprint_id}",
            "--policy-type",
            "CREATE_ENVIRONMENT_FROM_BLUEPRINT",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(profile, "datazone list-policy-grants", res.stderr)
            return None
        grants = json.loads(res.stdout or "{}").get("grantList", [])
        return [g.get("principal") or {} for g in grants]

    # -------------------------------------------- the DataZone domain, in every account
    # One listing everywhere, with the owner read from the ARN rather than inferred from who is
    # asking: an associated account's ListDomains returns the domain it is a member of, so only
    # the owning account separates "a domain was created here" (the violation) from "this
    # account can see the one domain" (step 1.3 working). The id alone cannot tell those apart
    # (Lesson 31).
    # In the deployment targets the Workloads OU denied datazone:* in full until Stage 19 step 4.1
    # excepted InfrastructureAccess, so an SCP denial there is that step not applied yet, not a
    # failed call.
    SCP_DENIED = "SCP_DENIED"
    dz_domains: dict = {}  # profile -> [(id, name, version, status, owner)] | None | SCP_DENIED
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
                # element 4 is the owning account, split out of the ARN rather than assumed to
                # be the caller; positions 0-3 keep their meaning.
                (d.get("arn", "") or "").split(":")[4]
                if len((d.get("arn", "") or "").split(":")) > 4
                else "?",
            )
            for d in doc.get("items", [])
        ]

    # ------------------------------- the registry's contents (Data Governance only)
    data_live = DATA_PROFILE in live
    # profile -> [(blueprint name, enabled regions, provisioning role set?, manage-access set?)]
    #
    # Keyed by profile: PutEnvironmentBlueprintConfiguration takes a domainIdentifier and no
    # account parameter, so the account it configures is the caller's, and an associated account
    # can enable blueprints against a shared domain. Reading only the domain account cannot tell
    # "no blueprint is configured anywhere" from "every blueprint is configured where it is
    # supposed to be" (Lesson 13).
    bp_configs: dict = {}
    bp_grants: dict = {}  # profile -> [(blueprint name, grant principals or None when unread)]
    project_profiles: list = []  # (name, id, status)
    profile_pin: dict | None = None  # app type -> (image, version); None when unread
    projects: list = []  # (name, id, status)
    domain_id = ""
    root_unit = ""  # the domain's root domain unit, the one US-14's grant names
    if data_live and dz_domains.get(DATA_PROFILE):
        cli = cli_for(DATA_PROFILE)
        domain_id = dz_domains[DATA_PROFILE][0][0]
        res = cli.run(
            "datazone",
            "get-domain",
            "--identifier",
            domain_id,
            "--query",
            "rootDomainUnitId",
            "--output",
            "text",
            log=False,
        )
        if res.ok:
            root_unit = (res.stdout or "").strip()
        else:
            logerr(DATA_PROFILE, "datazone get-domain", res.stderr)
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
                bp_configs.setdefault(DATA_PROFILE, []).append(
                    (
                        name,
                        " ".join(c.get("enabledRegions", []) or ["-"]),
                        "yes" if c.get("provisioningRoleArn") else "-",
                        "yes" if c.get("manageAccessRoleArn") else "-",
                    )
                )
                bp_grants.setdefault(DATA_PROFILE, []).append(
                    (name, config_grants(cli, DATA_PROFILE, domain_id, bpid))
                )
        # The member accounts' half: same domain id, each member's own session, because the
        # configuration belongs to the caller's account. Between the domain's creation and the
        # console account association the call legitimately fails, so `tolerate` keeps that
        # window from flipping this script's exit code (the seam list-project-profiles uses
        # below).
        for member in INTERACTIVE_PROFILES + HEADLESS_PROFILES:
            if member not in live:
                continue
            mcli = cli_for(member)
            mres = mcli.run(
                "datazone",
                "list-environment-blueprint-configurations",
                "--domain-identifier",
                domain_id,
                "--output",
                "json",
                log=False,
                tolerate="AccessDenied|ResourceNotFound|ValidationException",
            )
            if not mres.ok:
                continue
            for c in json.loads(mres.stdout or "{}").get("items", []):
                bpid = c.get("environmentBlueprintId", "?")
                r = mcli.run(
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
                    tolerate="AccessDenied|ResourceNotFound",
                )
                name = r.stdout.strip() if r.ok else bpid
                bp_configs.setdefault(member, []).append(
                    (
                        name,
                        " ".join(c.get("enabledRegions", []) or ["-"]),
                        "yes" if c.get("provisioningRoleArn") else "-",
                        "yes" if c.get("manageAccessRoleArn") else "-",
                    )
                )
                bp_grants.setdefault(member, []).append(
                    (name, config_grants(mcli, member, domain_id, bpid))
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
        # US-13's registry half: the version the profile's SageMakerAIDomain configuration pins.
        pid = {n: i for n, i, _s in project_profiles}.get(PROJECT_PROFILE_NAMES[0])
        if pid:
            res = cli.run(
                "datazone",
                "get-project-profile",
                "--domain-identifier",
                domain_id,
                "--identifier",
                pid,
                "--output",
                "json",
                log=False,
            )
            if res.ok and res.stdout:
                profile_pin = profile_pins(json.loads(res.stdout or "{}"))
            else:
                logerr(DATA_PROFILE, "datazone get-project-profile", res.stderr)
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
    sm_details: dict = {}  # profile -> [(id, VpcOnly?, idle summary, subnets, ceiling)]
    sm_apps: dict = {}  # profile -> [(app name, type, status, instance type)]
    sm_images: dict = {}  # profile -> [image names]
    sm_pins: dict = {}  # Interactive profile -> [(id, tags or None, {app type: [(image, version)]})]
    newest_versions: dict = {}  # Interactive profile -> {image: newest CREATED version or None}
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
        pin_rows = []
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
            # The ceiling is the control, so it is read separately. `IdleTimeoutInMinutes` is
            # the default, which a project member may change; `MaxIdleTimeoutInMinutes` is the
            # most they may raise it to, and step 8.1 names that one - "the admin ceiling the
            # user cannot raise". Both arrive in the same describe-domain response, and a domain
            # whose ceiling was raised or removed reads like a compliant one on the first alone.
            #
            # The value is reported, never asserted: the threshold is declared once, in
            # data-governance/governance/variables.tf, and a copy here would diverge (Lesson 33).
            # US-7 asserts that the control exists; the number rides in the table, where a change
            # shows up in the diff two runs make.
            ceiling = lcm.get("MaxIdleTimeoutInMinutes")
            idle = f"{lcm.get('LifecycleManagement', 'absent')}" + (
                f"/{lcm.get('IdleTimeoutInMinutes')}min" if lcm.get("IdleTimeoutInMinutes") else ""
            )
            idle += f" ceiling={ceiling}min" if ceiling else " ceiling=ABSENT"
            details.append((did, net, idle, " ".join(d.get("SubnetIds", []) or ["-"]), ceiling))
            if p in INTERACTIVE_PROFILES:
                user = d.get("DefaultUserSettings", {})
                entries = {
                    app: [
                        (e.get("ImageName"), e.get("ImageVersionNumber"))
                        for e in (user.get(f"{app}AppSettings") or {}).get("CustomImages") or []
                    ]
                    for app in PIN_PARAMETERS
                }
                t = cli.run(
                    "sagemaker",
                    "list-tags",
                    "--resource-arn",
                    d.get("DomainArn", ""),
                    "--output",
                    "json",
                    log=False,
                )
                tags = None
                if t.ok:
                    tags = {
                        x.get("Key"): x.get("Value")
                        for x in json.loads(t.stdout or "{}").get("Tags", [])
                    }
                else:
                    logerr(p, f"sagemaker list-tags {did}", t.stderr)
                pin_rows.append((did, tags, entries))
        sm_details[p] = details
        if p in INTERACTIVE_PROFILES:
            sm_pins[p] = pin_rows
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

    # US-13's image half: the newest CREATED version of each image a pin or a domain names.
    for p in INTERACTIVE_PROFILES:
        if p not in sm_pins:
            continue
        wanted = {n for n, _v in (profile_pin or {}).values()}
        wanted |= {n for _did, _t, ents in sm_pins[p] for es in ents.values() for n, _v in es}
        cli = cli_for(p)
        tops: dict = {}
        for name in sorted(n for n in wanted if n):
            r = cli.run(
                "sagemaker",
                "list-image-versions",
                "--image-name",
                name,
                "--output",
                "json",
                log=False,
            )
            if not r.ok:
                logerr(p, f"sagemaker list-image-versions {name}", r.stderr)
                continue
            created = [
                v.get("Version")
                for v in json.loads(r.stdout or "{}").get("ImageVersions", [])
                if v.get("ImageVersionStatus") == "CREATED"
            ]
            tops[name] = max(created) if created else None
        newest_versions[p] = tops

    # ---------------- the project roles and their boundary (INT-15's mechanical half)
    # Which roles are blueprint-provisioned is read from the tag, not from the name. The Tooling
    # stack creates three roles in Sandbox - datazone_usr_role_<project>_<env> and two
    # AmazonBedrock*Role-<project>-<env> (measured 2026-08-26) - and AWS's own Tooling template
    # gives its two conditional EMR roles no permissions boundary (read from the template,
    # 2026-08-22), so a name filter would report `pass` beside two unbounded roles the day
    # `createEmrResourceInTooling` turns true (Lesson 31).
    #
    # The tag is the service's own stamp: every role the blueprint provisions carries
    # AmazonDataZoneDomain / AmazonDataZoneProject / AmazonDataZoneBlueprint (measured on all
    # three roles, 2026-08-26). The name match is kept as an OR so an untagged role named
    # datazone* is still reported rather than silently dropped.
    #
    # ListRoles returns neither Tags nor PermissionsBoundary - both are GetRole-only, with
    # RoleLastUsed (Lesson 30) - so the candidate set is enumerated and every candidate is read
    # with GetRole, which returns both in one call.
    #
    # The candidate set excludes two IAM paths, and a path is not a name: /aws-service-role/
    # holds service-linked roles, which a service creates for itself and a blueprint cannot
    # provision, and /aws-reserved/ holds Identity Center's. Everything a blueprint could
    # have made is at '/', so this costs ~14 GetRole calls per account rather than ~33.
    #
    # The deployment targets are read too: a deployment project's Tooling environment creates the
    # same three roles there (Stage 19 step 4.6), under that account's D13 boundary.
    #
    # The domain account is read as well: the lake-publishing project's role lives there (Stage 6f
    # step 11). The same GetRole answers each role's trust policy. AWS's policy on a project role
    # allows sts:AssumeRole on every role, so a trust that names the account's root or any
    # principal is a role the project's code may assume (US-12, TM-30).
    role_rows: dict = {}  # profile -> [(role name, boundary name or '-', how it was found)]
    flow_shapes: dict = {}  # profile -> {unbounded flow role: what keeps it out of EXC-27}
    open_trust: dict = {}  # profile -> [(role name, whom its trust names)]
    roles_read: dict = {}  # profile -> how many roles' trust was read
    for p in INTERACTIVE_PROFILES + HEADLESS_PROFILES + (DATA_PROFILE,):
        if p not in live:
            continue
        cli = cli_for(p)
        own = next((c.account for c in callers if c.profile == p), None) or ""
        loose: list = []
        n_read = 0
        res = cli.run(
            "iam",
            "list-roles",
            "--query",
            "Roles[?!starts_with(Path, '/aws-service-role/') "
            "&& !starts_with(Path, '/aws-reserved/')].RoleName",
            "--output",
            "json",
            log=False,
        )
        if not res.ok:
            logerr(p, "iam list-roles", res.stderr)
            continue
        rows = []
        for name in json.loads(res.stdout or "[]"):
            rr = cli.run(
                "iam",
                "get-role",
                "--role-name",
                name,
                "--output",
                "json",
                log=False,
            )
            if not rr.ok:
                logerr(p, f"iam get-role {name}", rr.stderr)
                continue
            role = json.loads(rr.stdout or "{}").get("Role", {})
            n_read += 1
            statements = (role.get("AssumeRolePolicyDocument") or {}).get("Statement") or []
            for st in statements if isinstance(statements, list) else [statements]:
                if st.get("Effect") != "Allow":
                    continue
                principal = st.get("Principal") or {}
                named = principal.get("AWS") or [] if isinstance(principal, dict) else principal
                for who in [named] if isinstance(named, str) else named:
                    if who == "*":
                        loose.append((name, "any principal"))
                    elif own and who in (own, f"arn:aws:iam::{own}:root"):
                        loose.append((name, "the account's root"))
            tags = {t["Key"]: t.get("Value", "") for t in role.get("Tags", [])}
            by_tag = "AmazonDataZoneDomain" in tags
            by_name = "datazone" in name.lower()
            if not (by_tag or by_name):
                continue
            barn = (role.get("PermissionsBoundary") or {}).get("PermissionsBoundaryArn") or "-"
            found = "tag" if by_tag else "name"
            rows.append((name, barn.split("/")[-1], found))
            if barn == "-" and name.startswith(flowrole.NAME_PREFIX):
                listed = []
                for sub, key, field in (
                    ("list-attached-role-policies", "AttachedPolicies", "PolicyName"),
                    ("list-role-policies", "PolicyNames", None),
                ):
                    lr = cli.run("iam", sub, "--role-name", name, "--output", "json", log=False)
                    if not lr.ok:
                        logerr(p, f"iam {sub} {name}", lr.stderr)
                        listed = None
                        break
                    items = json.loads(lr.stdout or "{}").get(key, [])
                    listed.append([i.get(field, "") for i in items] if field else items)
                if listed is not None:
                    flow_shapes.setdefault(p, {})[name] = flowrole.shape_problems(
                        name, role.get("AssumeRolePolicyDocument"), listed[0], listed[1], own
                    )
        role_rows[p] = rows
        open_trust[p] = loose
        roles_read[p] = n_read

    # US-15's reading, per account: the environments a live stack carries, any status but
    # DELETE_COMPLETE, and every resource carrying an environment's tag. No DataZone call answers
    # this: a project's non-member is told an existing environment is not found (SUP-157).
    env_stacks: dict = {}  # profile -> environment ids a live stack carries, None when unread
    env_tagged: dict = {}  # profile -> [(arn, tags)] carrying ENV_TAG, None when unread
    for p in INTERACTIVE_PROFILES + HEADLESS_PROFILES + (DATA_PROFILE,):
        if p not in live:
            continue
        cli = cli_for(p)
        res = cli.run(
            "cloudformation",
            "describe-stacks",
            "--query",
            f"Stacks[].Tags[?Key=='{ENV_TAG}'][].Value",
            "--output",
            "json",
            log=False,
        )
        env_stacks[p] = set(json.loads(res.stdout or "[]") or []) if res.ok else None
        if not res.ok:
            logerr(p, "cloudformation describe-stacks", res.stderr)
        res = cli.run(
            "resourcegroupstaggingapi",
            "get-resources",
            "--tag-filters",
            f"Key={ENV_TAG}",
            "--query",
            "ResourceTagMappingList[].[ResourceARN, Tags]",
            "--output",
            "json",
            log=False,
        )
        env_tagged[p] = (
            [
                (arn, {t["Key"]: t.get("Value", "") for t in tags or []})
                for arn, tags in json.loads(res.stdout or "[]") or []
            ]
            if res.ok
            else None
        )
        if not res.ok:
            logerr(p, "resourcegroupstaggingapi get-resources", res.stderr)

    def bucket_reader(p: str):
        """US-15's second reading of a bucket: its own tag set, which the index may lag."""
        cli = cli_for(p)

        def reread(name: str) -> tuple:
            res = cli.run(
                "s3api", "get-bucket-tagging", "--bucket", name, "--output", "json", log=False
            )
            if res.ok:
                doc = json.loads(res.stdout or "{}")
                return "ok", {t["Key"]: t.get("Value", "") for t in doc.get("TagSet", [])}
            if "NoSuchBucket" in res.stderr:
                return "gone", {}
            if "NoSuchTagSet" in res.stderr:
                return "ok", {}
            logerr(p, f"s3api get-bucket-tagging {name}", res.stderr)
            return "unread", {}

        return reread

    # ------------- the deployment projects: one per target, with its environments (INV-21)
    deploy_projects: dict = {}  # deployment profile name -> [(project name, id)]
    deploy_rows: list = []  # (target, project, environment, status, glue database, targets)
    profile_of: dict = {}  # project id -> its project profile's id; US-13 reads it too
    if DATA_PROFILE in live and domain_id:
        cli = cli_for(DATA_PROFILE)
        for _name, pid, _status in projects:
            r = cli.run(
                "datazone",
                "get-project",
                "--domain-identifier",
                domain_id,
                "--identifier",
                pid,
                "--query",
                "projectProfileId",
                "--output",
                "text",
                log=False,
            )
            if r.ok and r.stdout.strip() not in ("", "None"):
                profile_of[pid] = r.stdout.strip()
        profile_id = {n: i for n, i, _s in project_profiles}
        for dname, target in DEPLOYMENT_TARGET_OF.items():
            if dname not in profile_id:
                continue
            mine = [(n, i) for n, i, _s in projects if profile_of.get(i) == profile_id[dname]]
            deploy_projects[dname] = mine
            if target not in live:
                continue
            tcli = cli_for(target)
            for pname, pid in mine:
                res = tcli.run(
                    "datazone",
                    "list-environments",
                    "--domain-identifier",
                    domain_id,
                    "--project-identifier",
                    pid,
                    "--query",
                    "items[].[name,id,status]",
                    "--output",
                    "json",
                )
                if not res.ok:
                    continue
                for ename, eid, estatus in json.loads(res.stdout or "[]"):
                    g = tcli.run(
                        "datazone",
                        "get-environment",
                        "--domain-identifier",
                        domain_id,
                        "--identifier",
                        eid,
                        "--query",
                        "provisionedResources[?name=='glueDBName'].value | [0]",
                        "--output",
                        "text",
                    )
                    glue_db = g.stdout.strip() if g.ok else ""
                    s = tcli.run(
                        "datazone",
                        "list-subscription-targets",
                        "--domain-identifier",
                        domain_id,
                        "--environment-identifier",
                        eid,
                        "--query",
                        "items[].name",
                        "--output",
                        "json",
                    )
                    targets = ", ".join(json.loads(s.stdout or "[]")) if s.ok else "(not read)"
                    deploy_rows.append(
                        (
                            target,
                            pname,
                            ename,
                            estatus,
                            glue_db if glue_db not in ("", "None") else "-",
                            targets or "(none)",
                        )
                    )

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

    # US-2: no DataZone domain owned anywhere else (1c's root deny holding), and nothing
    # SageMaker-shaped in Data Governance (the registry-not-runtime negative deliverable).
    # Owned, not visible - see the collection comment above.
    for p in live:
        if p == DATA_PROFILE or dz_domains.get(p) is None:
            continue
        if dz_domains[p] == SCP_DENIED:
            checks.note(
                "US-2",
                f"datazone reads denied in {p}",
                "the Workloads SCP still refuses InfrastructureAccess: Stage 19 step 4.1's "
                "amendment is not applied. After it this session reads the shared domain here.",
            )
            continue
        here = account_of.get(p)
        owned = [d for d in dz_domains[p] if d[4] == here]
        shared_in = [d for d in dz_domains[p] if d[4] != here]
        if owned:
            checks.fail(
                "US-2",
                f"DataZone domain OWNED by {p}",
                f"{len(owned)} domain(s) created outside Data Governance "
                f"({', '.join(d[0] for d in owned)}) - either INT-12's fallback happened by "
                "accident or the 1c root deny is not holding.",
            )
        if shared_in:
            foreign = [d for d in shared_in if domain_id and d[0] != domain_id]
            if foreign:
                checks.fail(
                    "US-2",
                    f"an UNEXPECTED domain is shared into {p}",
                    f"{', '.join(d[0] for d in foreign)} - not {domain_id}, the one domain "
                    "D26 allows. A share from somewhere nobody chose.",
                )
            else:
                checks.ok(
                    "US-2",
                    f"{p} sees the shared domain and owns none",
                    f"{shared_in[0][0]} owned by Data Governance - "
                    + (
                        "the deployment target's association (Stage 19 step 4.2)"
                        if p in HEADLESS_PROFILES
                        else "step 1.3's association"
                    )
                    + ", measured rather than read off a console label",
                )
        if not owned and not shared_in and p in HEADLESS_PROFILES:
            checks.fail(
                "US-2",
                f"no DataZone domain visible in {p}",
                "a deployment target is associated to the domain since Stage 19 step 4.2 "
                "(2026-11-11) and holds a deployment project: an empty answer means the "
                "association is gone, and the project with it.",
            )
        elif not owned and not shared_in:
            checks.note(
                "US-2",
                f"no DataZone domain visible in {p}",
                "the association was REMOVED here (Stage 6b step 1.4) - this account is "
                "leaving the domain, so nothing visible is the finished state and not a "
                "pending one. Its OU has not changed yet, so datazone: is not denied: the "
                "call succeeds and returns nothing."
                if p in RETIRED_MEMBER_PROFILES
                else "correct before this account's association (Stage 6 step 1.3).",
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

    # US-3: blueprint configurations exist only for decision 5's category 1 - the allow-list
    # above (step 1.4; docs/SMUS.md). Names are read, not assumed. The Redshift-backed
    # blueprints keep their own message: enabling either reopens D26/D12, not decision 5
    # (LakehouseCatalog is RMS-backed - the 2026-08-19 re-read, decision 4).
    # The verdict is split by column, and the two halves are opposite in sign. In the domain
    # account, zero configurations is the correct state and passes with its own message: D22
    # forbids enabling any blueprint there, so one appearing is US-2-shaped rather than an
    # allow-list question. In each member account the allow-list is what is measured, and the
    # verdict is a note while the association does not exist, since before it the call cannot
    # succeed at all.
    if data_live and domain_id:
        domain_bps = [n for n, *_ in bp_configs.get(DATA_PROFILE) or []]
        stray = [n for n in domain_bps if n not in DOMAIN_ACCOUNT_BLUEPRINTS]
        if stray:
            checks.fail(
                "US-3",
                "blueprint configured in the DOMAIN account",
                f"{', '.join(stray)} - D22 admits one configuration in Data Governance, the "
                "lake-publishing pilot's Tooling (Stage 6f step 11), and the OU's "
                "sagemaker:Create* deny is free only because nothing else is enabled here.",
            )
        elif domain_bps:
            checks.note(
                "US-3",
                "blueprint configured in the domain account",
                f"{', '.join(domain_bps)} - the lake-publishing pilot's (Stage 6f decision 1, "
                "step 11; D22 amended 2026-10-26), with spaces off; its rollback removes it.",
            )
        else:
            checks.ok(
                "US-3",
                "no blueprint configured in the domain account",
                "the registry/runtime split holding (D26, D22)",
            )

        for member in INTERACTIVE_PROFILES:
            if member not in live:
                continue
            rows = bp_configs.get(member)
            if not rows:
                # Which gate is still shut is measured, not assumed: before 1.3 the call could
                # not succeed at all; after it, an empty list means 1.4 has not run. The two are
                # separated by whether the shared domain is visible here, rather than by the
                # tfvars generator's SMUS_ASSOCIATED, which reports the intention.
                associated = any(
                    d[4] != account_of.get(member) for d in (dz_domains.get(member) or [])
                )
                checks.note(
                    "US-3",
                    f"blueprint configurations in {member}",
                    "none - the association exists (step 1.3, measured above), so what is "
                    "left is step 1.4: backend.SMUS_ASSOCIATED carries this account's row "
                    "and the sagemaker/ slice is applied a second time."
                    if associated
                    else "none, and none is expected - the eleven were destroyed by Stage 6b "
                    "step 1.2 and the association removed by 1.4. Reading them back from here "
                    "now FAILS rather than returning empty (UnauthorizedException), which is "
                    "what makes this row a retirement instead of a pending association."
                    if member in RETIRED_MEMBER_PROFILES
                    else "none - expected until this account's SMUS association is accepted "
                    "(Stage 6 step 1.3) and backend.SMUS_ASSOCIATED carries its row.",
                )
                continue
            names = [n for n, _r, _p, _m in rows]
            redshift = [n for n in names if "redshift" in n.lower() or n == "LakehouseCatalog"]
            extra = [n for n in names if n not in BLUEPRINT_ALLOWLIST and n not in redshift]
            if redshift:
                checks.fail(
                    "US-3",
                    f"Redshift-backed blueprint enabled in {member}",
                    f"{', '.join(redshift)} - D26/D12 exclude the Redshift-managed-storage "
                    "family by decision (RedshiftServerless, and LakehouseCatalog since "
                    "2026-08-19).",
                )
            if extra:
                checks.fail(
                    "US-3",
                    f"blueprint outside decision 5's category 1 in {member}",
                    f"{', '.join(extra)} - the allow-list is "
                    f"{', '.join(BLUEPRINT_ALLOWLIST)} "
                    "(docs/SMUS.md carries the full table and the category of every blueprint "
                    "the domain publishes); enabling more amends Stage 6 decision 5. A name "
                    "that is ALMOST one of these is the likely cause - the API spells them "
                    "EmrServerless, EmrOnEc2, QuickSight (Lesson 38).",
                )
            if not redshift and not extra:
                checks.ok(
                    "US-3",
                    f"{len(rows)} blueprint configuration(s) in {member}",
                    "all inside decision 5's category 1",
                )

        # A deployment target's configurations: the two <env>/studio/ declares, and no other.
        for target in HEADLESS_PROFILES:
            if target not in live or dz_domains.get(target) in (None, SCP_DENIED):
                continue
            names = [n for n, _r, _p, _m in bp_configs.get(target) or []]
            extra = [n for n in names if n not in DEPLOYMENT_BLUEPRINTS]
            if extra:
                checks.fail(
                    "US-3",
                    f"blueprint outside the deployment project's in {target}",
                    f"{', '.join(extra)} - a deployment target configures "
                    f"{' and '.join(DEPLOYMENT_BLUEPRINTS)} alone (Stage 19 step 4.4): no "
                    "capability a person would use, and nothing Redshift-backed.",
                )
            elif names:
                checks.ok(
                    "US-3",
                    f"{len(names)} blueprint configuration(s) in {target}",
                    f"{', '.join(sorted(names))} - the deployment project's",
                )
            else:
                checks.note(
                    "US-3",
                    f"blueprint configurations in {target}",
                    "none - the account is associated and <env>/studio/'s second apply has "
                    "not run (Stage 19 step 4.4).",
                )

    # US-14: every configuration holds the one grant sagemaker-prereqs declares, read in the
    # configuration's own account. A second grant, another designation or another unit is a hand
    # grant from a blueprint's Authorization tab; no grant is a blueprint no project can deploy.
    if data_live and domain_id:
        for p in sorted(bp_grants):
            rows = bp_grants[p]
            unread = [n for n, g in rows if g is None]
            stray = [
                f"{n} ({grant_text(g, root_unit)})"
                for n, g in rows
                if g is not None and not is_module_grant(g, root_unit)
            ]
            if not root_unit:
                checks.note(
                    "US-14",
                    f"blueprint grants in {p}",
                    "unjudged - the root domain unit was not read (get-domain, above).",
                )
                continue
            if stray:
                checks.fail(
                    "US-14",
                    f"blueprint grants in {p}",
                    f"{'; '.join(stray)} - sagemaker-prereqs/grants.tf declares one "
                    f"CREATE_ENVIRONMENT_FROM_BLUEPRINT grant per configuration, {GRANT_DESIGNATION} "
                    "projects of the root unit, children excluded (INV-24). Any other grant was "
                    "added by hand and widens what a project's Resource blueprints page deploys.",
                )
            if unread:
                checks.note(
                    "US-14",
                    f"blueprint grants in {p}",
                    f"{', '.join(unread)} unread - the failed call is listed at the end.",
                )
            if not stray and not unread:
                checks.ok(
                    "US-14",
                    f"blueprint grants on {len(rows)} configuration(s) in {p}",
                    f"each holds the module's one grant: {GRANT_DESIGNATION}, root unit",
                )

    # US-4: the project profiles, by their contracted names - and the retired one by its.
    if data_live and domain_id:
        have = {n for n, _i, _s in project_profiles}
        missing = [n for n in PROJECT_PROFILE_NAMES if n not in have]
        retired = [n for n in RETIRED_PROFILE_NAMES if n in have]
        contracted = (
            set(PROJECT_PROFILE_NAMES)
            | set(WINDOW_PROFILE_NAMES)
            | set(MODEL_GOVERNANCE_PROFILE_NAMES)
            | set(PILOT_PROFILE_NAMES)
            | set(DEPLOYMENT_PROFILE_NAMES)
        )
        unknown = sorted(have - contracted - set(RETIRED_PROFILE_NAMES))
        window = sorted(have & set(WINDOW_PROFILE_NAMES))
        if not project_profiles:
            checks.note("US-4", "project profiles", "none - expected before Stage 6 step 1.")
        elif missing:
            checks.fail(
                "US-4",
                "project profiles",
                f"missing {', '.join(missing)} - `experimentation` provisions into Sandbox and "
                "is the one profile this domain is contracted to carry (Stage 6a step 1.5, "
                "narrowed to one by Stage 6b step 1.1).",
            )
        elif retired:
            checks.fail(
                "US-4",
                "project profiles",
                f"{', '.join(retired)} is back - it was destroyed by Stage 6b step 1.1 because "
                "its member account became the headless `Staging`. A project created from it "
                "would provision into an account with no interactive surface.",
            )
        elif unknown:
            checks.fail(
                "US-4",
                "project profiles",
                f"{', '.join(unknown)} is no contracted profile - every profile is a row of "
                "data-governance/governance/'s locals.tf and a name in this script.",
            )
        elif window:
            checks.ok(
                "US-4",
                "project profiles",
                f"{', '.join(sorted(have))} - experimentation as contracted, "
                f"{', '.join(window)} in Stage 18's window, the model governance profile "
                "Stage 17 decision 13's",
            )
        else:
            checks.ok(
                "US-4",
                "project profiles",
                f"{', '.join(sorted(have))} - experimentation as contracted"
                + (
                    ", the model governance profile Stage 17 decision 13's"
                    if have & set(MODEL_GOVERNANCE_PROFILE_NAMES)
                    else ""
                )
                + (
                    ", lake-publishing Stage 6f step 11's pilot"
                    if have & set(PILOT_PROFILE_NAMES)
                    else ""
                )
                + (
                    ", "
                    + " and ".join(sorted(have & set(DEPLOYMENT_PROFILE_NAMES)))
                    + " Stage 19 step 4.5's"
                    if have & set(DEPLOYMENT_PROFILE_NAMES)
                    else ""
                ),
            )

    # US-5: every blueprint-provisioned SageMaker AI domain in the Interactive accounts is
    # VpcOnly. PublicInternetOnly is the whole VPC design bypassed at the app layer.
    for p in INTERACTIVE_PROFILES:
        for did, net, _idle, _subnets, _ceiling in sm_details.get(p, []):
            if net == "VpcOnly":
                checks.ok("US-5", f"{p} domain {did}", "AppNetworkAccessType=VpcOnly")
            else:
                checks.fail(
                    "US-5",
                    f"{p} domain {did}",
                    f"AppNetworkAccessType={net} - step 1 requires VpcOnly; anything else "
                    "puts every app outside the endpoint policies and the flow logs.",
                )

    # US-6: no SageMaker AI domain in the deployment targets (D17): a deployment project's Tooling
    # has spaces off and creates none (Stage 18 question i).
    for p in HEADLESS_PROFILES:
        if p in live and sm_domains.get(p):
            checks.fail(
                "US-6",
                f"SageMaker domain in {p}",
                "a deployment target carries no SageMaker AI domain (D17): its project's "
                "Tooling has spaces off, and the Workloads SCP denies sagemaker:CreateDomain.",
            )
        elif p in live and sm_domains.get(p) is not None:
            checks.ok("US-6", f"no SageMaker domain in {p}", "no interactive surface (D17)")

    # US-7: idle shutdown configured on every Interactive domain (step 8), and the admin
    # ceiling beside it, since either half alone is a suggestion.
    for p in INTERACTIVE_PROFILES:
        for did, _net, idle, _subnets, ceiling in sm_details.get(p, []):
            if not idle.startswith("ENABLED"):
                checks.fail(
                    "US-7",
                    f"idle shutdown on {p} {did}",
                    f"IdleSettings {idle} - the mandatory cost control of step 8; without "
                    "it D11 depends on the user's habits.",
                )
            elif ceiling is None:
                checks.fail(
                    "US-7",
                    f"idle ceiling on {p} {did}",
                    f"IdleSettings {idle} - shutdown is ENABLED, but nothing bounds what a "
                    "project member may raise the timeout to, so the default is a suggestion "
                    "(step 8.1's maxIdleTimeoutInMinutes, locked non-editable in the project "
                    "profile). An app left at the raised timeout bills the whole way.",
                )
            else:
                checks.ok("US-7", f"idle shutdown on {p} {did}", idle)

    # US-8: every blueprint-provisioned project role carries a permissions boundary,
    # and it is the D13 one (INT-15). Roles with no boundary are the INT-15 failure
    # shape made visible.
    for p, rows in role_rows.items():
        if not rows:
            # An account with no datazone roles yet is unexercised, not passing: absence of
            # a row reads the same as absence of a measurement (Lesson 13).
            checks.note(
                "US-8",
                f"project-role boundary in {p}",
                "no blueprint-provisioned role exists, and none ever will here - the two "
                "service roles and the boundary policy were destroyed with the slice at "
                "Stage 6b step 1.7. The word this note used to carry was `yet`."
                if p in RETIRED_MEMBER_PROFILES
                else "no blueprint-provisioned role exists yet - the check is unexercised here.",
            )
            continue
        # A flow environment's own role is EXC-27 while its shape holds (awslib/flowrole.py).
        shapes = flow_shapes.get(p, {})
        excepted = [n for n, b, _ in rows if b == "-" and n in shapes and not shapes[n]]
        for n in excepted:
            checks.note("US-8", f"role {n} in {p}", flowrole.NOTE)
        unbounded = [n for n, b, _ in rows if b == "-" and n not in excepted]
        wrong = [n for n, b, _ in rows if b != "-" and BOUNDARY_NAME_FRAGMENT not in b]
        if unbounded:
            outside = [f"{n}: {'; '.join(shapes[n])}" for n in unbounded if shapes.get(n)]
            checks.fail(
                "US-8",
                f"project-role boundary in {p}",
                f"{len(unbounded)} blueprint-provisioned role(s) with NO permissions "
                f"boundary ({', '.join(unbounded[:3])}...) - INT-15's mechanism is absent."
                + (
                    f" Outside {flowrole.EXCEPTION_ID}'s shape: {' | '.join(outside)}."
                    if outside
                    else ""
                ),
            )
        elif wrong:
            checks.note(
                "US-8",
                f"project-role boundary in {p}",
                f"boundary present but not '{BOUNDARY_NAME_FRAGMENT}': {', '.join(wrong[:3])}",
            )
        else:
            by_tag = sum(1 for _, _, f in rows if f == "tag")
            besides = f", besides {len(excepted)} under {flowrole.EXCEPTION_ID}" if excepted else ""
            checks.ok(
                "US-8",
                f"project-role boundary in {p}",
                f"all {len(rows) - len(excepted)} blueprint-provisioned role(s) bounded{besides} "
                f"({by_tag} found by tag)",
            )

    # US-11: each deployment target holds one project, born of its own profile, with every
    # environment ACTIVE (INV-21). The subscription targets are printed and not judged: a
    # deployment project subscribes to nothing (Stage 19 decision 14).
    for dname, target in DEPLOYMENT_TARGET_OF.items():
        if dname not in deploy_projects:
            continue
        mine = deploy_projects[dname]
        what = f"projects of {dname}"
        if not mine:
            checks.note("US-11", what, "none yet - Stage 19 step 4.6 creates the one.")
            continue
        if len(mine) > 1:
            checks.fail(
                "US-11",
                what,
                f"{len(mine)}: {', '.join(n for n, _i in mine)} - a target holds one deployment "
                "project (INV-21).",
            )
            continue
        envs = [r for r in deploy_rows if r[0] == target and r[1] == mine[0][0]]
        down = [f"{r[2]} {r[3]}" for r in envs if r[3] != "ACTIVE"]
        if down:
            checks.fail(
                "US-11",
                what,
                f"{mine[0][0]}: {', '.join(down)} - an environment that is not ACTIVE pins its "
                "blueprint configuration (Lesson 39).",
            )
        elif envs:
            checks.ok("US-11", what, f"{mine[0][0]} alone, {len(envs)} environment(s) ACTIVE")
        else:
            checks.note("US-11", what, f"{mine[0][0]} alone; its environments were not read.")

    # US-12: where a project role exists, no role's trust names the account's root or any
    # principal. The trust policy is the one layer between a project role and another role.
    for p, loose in open_trust.items():
        if not role_rows.get(p):
            continue
        if loose:
            named = "; ".join(f"{n} trusts {w}" for n, w in loose[:4])
            checks.fail(
                "US-12",
                f"role trust in {p}",
                f"{named} - AWS's policy allows a project role sts:AssumeRole on every role, so "
                "this trust is the project's to use (TM-30).",
            )
        else:
            checks.ok(
                "US-12",
                f"role trust in {p}",
                f"{roles_read.get(p, 0)} role(s) read, none trusts the account's root or any principal",
            )

    # US-13: the house image's pin (6d decision 16 (a), INV-23). The profile pins the newest
    # CREATED version and each blueprint domain the profile's version, so a release is red here from
    # its `register` to the last owner's Update project (dev-env.md §B). A Tooling domain is noted
    # in the projects EXC-26 names and failed anywhere else.
    # `experimentation` provisions into the one Interactive profile, so its projects are judged there.
    project_names = {i: n for n, i, _s in projects}
    exp_id = {n: i for n, i, _s in project_profiles}.get(PROJECT_PROFILE_NAMES[0])
    born = (
        {i: n for n, i, s in projects if s == "ACTIVE" and profile_of.get(i) == exp_id}
        if exp_id and DATA_PROFILE in live
        else None
    )
    for p in INTERACTIVE_PROFILES:
        if sm_pins.get(p) is not None:
            judge_image_pins(
                checks,
                p,
                sm_pins[p],
                profile_pin,
                newest_versions.get(p, {}),
                project_names,
                born,
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

    # US-15 (INV-25): no bucket outlives the environment that created it. Only a bucket fails:
    # it holds a project's data with its policy gone. Other resources are noted.
    for p in INTERACTIVE_PROFILES + HEADLESS_PROFILES + (DATA_PROFILE,):
        if p in live:
            judge_leftovers(checks, p, env_stacks.get(p), env_tagged.get(p), bucket_reader(p))

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
  7. The step 3 deny, per permission set
  8. CHECKS
  9. The accounts nothing here is measuring
 10. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 6 RUNS - each such reading
    is a note, not a failure; it becomes a regression the moment the stage closes.
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT - section 9 names what nothing here
    reached.
  - THIS IS A CONTROL-PLANE READING. The lake reads,
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
        rep.h1("2. DataZone domains VISIBLE in every account, and who OWNS each")
        rows = ["PROFILE\tDOMAIN\tNAME\tVERSION\tSTATUS\tOWNER"]
        for p in live:
            doms = dz_domains.get(p)
            if doms is None:
                rows.append(f"{p}\t(call failed)\t-\t-\t-\t-")
            elif doms == SCP_DENIED:
                rows.append(f"{p}\t(denied by SCP - Stage 19 step 4.1 not applied)\t-\t-\t-\t-")
            elif not doms:
                rows.append(f"{p}\t(none)\t-\t-\t-\t-")
            else:
                for i, n, v, st, own in doms:
                    where = "self" if own == account_of.get(p) else "shared in"
                    rows.append(f"{p}\t{i}\t{n}\t{v}\t{st}\t{where}")
        rep.tabulate(rows)
        rep.text("""
Read the OWNER column, never the row count - the two answer different questions
and only one of them is a control. Exactly one row may say `self`, and its
profile must be awsds-infra-data (D26); a `self` anywhere else is either
INT-12's per-account fallback happening by accident or the 1c root deny
(DenyDataZoneDomainOutsideDataOu) not holding.

A `shared in` row is Stage 6 step 1.3 working: an associated account's
ListDomains returns the domain it is a member of. Before 1.3 the member rows
read `(none)`, and this table's earlier version - which had no OWNER column -
called the first `shared in` a violation on the day the association succeeded.""")

        # ==============================================================================
        rep.h1("3. The registry's contents: blueprint configurations (per account),")
        rep.h1("   project profiles and projects")
        if not data_live:
            rep.line(f"{DATA_PROFILE} was not measured - nothing to show.")
        elif not domain_id:
            rep.line("No domain yet. Expected before Stage 6 step 1.")
        else:
            rep.line(f"DOMAIN_ID={domain_id}")
            rep.line()
            if bp_configs:
                grant_of = {(prof, n): g for prof, rows_ in bp_grants.items() for n, g in rows_}
                rep.tabulate(
                    ["ACCOUNT\tBLUEPRINT\tREGIONS\tPROVISIONING ROLE\tMANAGE-ACCESS ROLE\tGRANTS"]
                    + [
                        f"{prof}\t{n}\t{r}\t{pr}\t{m}\t"
                        + grant_text(grant_of.get((prof, n)), root_unit)
                        for prof in sorted(bp_configs)
                        for n, r, pr, m in bp_configs[prof]
                    ]
                )
            else:
                rep.line("No blueprint configuration, in any measured account.")
            rep.line()
            rep.text("""THE ACCOUNT COLUMN IS THE POINT. A blueprint configuration belongs to the
account that CALLED PutEnvironmentBlueprintConfiguration - the API takes a domain
and no account - so an associated member enables blueprints against the shared
domain, and a reading taken only in Data Governance cannot tell "nothing is
configured" from "everything is configured where it belongs" (Lesson 13). Rows in
awsds-infra-data are a US-3 FAILURE, not a success, but for the lake-publishing
pilot's Tooling (Stage 6f step 11, D22 amended 2026-10-26).

GRANTS is US-14's reading: the CREATE_ENVIRONMENT_FROM_BLUEPRINT grants on each
configuration, which decide what a project's Resource blueprints page deploys.
The module declares one per configuration, `CONTRIBUTOR, root unit`; any other
was added from a blueprint's Authorization tab (INV-24).""")
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
            if deploy_rows:
                rep.line()
                rep.tabulate(
                    [
                        "TARGET\tDEPLOYMENT PROJECT\tENVIRONMENT\tSTATUS\tGLUE DATABASE\tSUBSCRIPTION TARGETS"
                    ]
                    + ["\t".join(r) for r in deploy_rows]
                )
                rep.text("""
One project per deployment target, born of that target's profile (US-11, INV-21).
The subscription targets are a reading: a deployment project subscribes to
nothing (Stage 19 decision 14), and the organization denies it the request.""")

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
                for did, net, idle, subnets, _ceiling in details:
                    rows.append(f"{p}\t{did}\t{net}\t{idle}\t{subnets}")
        rep.tabulate(rows)
        rep.line()
        image_rows = ["PROFILE\tDOMAIN\tBLUEPRINT\tPROJECT\tJUPYTERLAB\tCODEEDITOR"]
        for p in INTERACTIVE_PROFILES:
            for did, tags, entries in sm_pins.get(p) or []:
                t = tags or {}
                cells = [
                    " ".join(f"{n} v{v if v is not None else '*'}" for n, v in entries.get(app, []))
                    or "-"
                    for app in PIN_PARAMETERS
                ]
                who = project_names.get(t.get(PROJECT_TAG, ""), t.get(PROJECT_TAG, "?"))
                image_rows.append("\t".join([p, did, t.get(BLUEPRINT_TAG, "?"), who, *cells]))
        rep.tabulate(image_rows)
        pin_text = (
            ", ".join(f"{app} {n} v{v}" for app, (n, v) in profile_pin.items())
            if profile_pin
            else "(unread or none)"
        )
        rep.line(f"{PROJECT_PROFILE_NAMES[0]}'s pin: {pin_text}")
        for p in INTERACTIVE_PROFILES:
            for name, top in sorted(newest_versions.get(p, {}).items()):
                rep.line(f"{p}: newest CREATED version of {name}: {top}")
        rep.text("""
Domains belong ONLY in the Interactive columns (the blueprint targets). One in
Data Governance breaks the registry premise (US-2); one in Production or Staging
breaks D17 (US-6). VpcOnly and an ENABLED idle setting are steps 1 and 8.

The second table is US-13's: `v*` is an entry with no version number, which offers
every version; a blueprint domain pins one, the profile's. Each domain's BLUEPRINT
is its AmazonDataZoneBlueprint tag, the one way to tell the two kinds apart.

IDLE SETTINGS carries TWO numbers and step 8.1 rests on the second: the timeout
is the default a project member may change, `ceiling` is the most they may raise
it to. `ceiling=ABSENT` is a US-7 failure even with shutdown ENABLED. The value
itself is declared in the project profile, never asserted here - it is printed so
a change shows up in the diff two runs make.""")

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
            rep.line("No blueprint-provisioned role in any member account (or not measured).")
        else:
            for p, rows_ in role_rows.items():
                rep.h2(p)
                if rows_:
                    rep.tabulate(
                        ["ROLE\tPERMISSIONS BOUNDARY\tFOUND BY"]
                        + [f"{n}\t{b}\t{f}" for n, b, f in rows_]
                    )
                else:
                    rep.line("(none)")
        rep.text("""
Presence, never survival: whether the boundary outlives a blueprint
reconciliation is INT-15's behavioural half - provision, wait, re-run this file
and diff section 6.

FOUND BY says how the role entered this table. `tag` is the service's own stamp
(AmazonDataZoneDomain), which is what makes the reading independent of what AWS
decides to call a role: the Tooling stack creates AmazonBedrock*Role-<project>-
<env> beside datazone_usr_role_*, and its two conditional EMR roles - which AWS's
template leaves with NO boundary - would be named after neither. `name` is the
legacy datazone* match, kept so an untagged role is reported rather than dropped.""")
        if open_trust:
            rep.line()
            rows = ["PROFILE\tROLES READ\tTRUST NAMING THE ACCOUNT'S ROOT OR ANY PRINCIPAL"]
            for p, loose in open_trust.items():
                named = "; ".join(f"{n} ({w})" for n, w in loose) or "none"
                rows.append(f"{p}\t{roles_read.get(p, 0)}\t{named}")
            rep.tabulate(rows)
            rep.text("""
AWS's SageMakerStudioProjectUserRolePolicy allows a project role sts:AssumeRole
on every role, so a role's trust policy is what keeps a project's code out of it
(US-12, TM-30). Service-linked and Identity Center roles are not read: neither
path's trust names an account.""")

        # ==============================================================================
        rep.h1("7. The step 3 deny, per permission set")
        rep.text(f"""The reading greps each set's inline policy for the Sids {", ".join(STEP3_SIDS)} -
presence, never sufficiency: the conditions inside them are proven by the stage's
own deny pair (a job submitted with no VPC config, an oversized instance type).

""")
        if not identity_live:
            rep.line(f"{IDENTITY_PROFILE} was not measured - the sets were not read.")
        elif not set_rows:
            rep.line("No project permission set was found - see section 10.")
        else:
            rep.tabulate(
                [f"PERMISSION SET\t{STEP3_SIDS[0]}\t{STEP3_SIDS[1]}"]
                + [f"{n}\t{a}\t{b}" for n, a, b in sorted(set_rows)]
            )

        # ==============================================================================
        rep.h1("8. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  US-1   exactly one DataZone V2 domain, in Data Governance (step 1; D26)
  US-2   no domain OWNED anywhere else (a shared-in one is 1.3, not a breach);
         nothing SageMaker-shaped in Data Governance
         (step 0's second preflight; the registry/runtime split)
  US-3   blueprint configurations, read PER ACCOUNT and judged in opposite
         directions: in the domain account none but the lake-publishing pilot's
         Tooling (D22 amended; Stage 6f step 11), in each Interactive account none
         Redshift-backed and none outside decision 5's category 1 (step 1.4;
         D12/D26, docs/SMUS.md), and in each deployment target Tooling and
         DataLake alone (Stage 19 step 4.4)
  US-4   the `experimentation` project profile exists and no uncontracted one does -
         a stage's window profile is admitted while WINDOW_PROFILE_NAMES names it,
         the lake-publishing pilot's while PILOT_PROFILE_NAMES does, the deployment
         profiles of Stage 19 step 4.5 once they exist,
         `engineering` was retired by Stage 6b step 1.1 and its return is a failure
  US-5   every Interactive SageMaker AI domain is VpcOnly (step 1)
  US-6   the deployment targets hold no SageMaker AI domain (D17). They are
         associated to the domain since Stage 19 step 4.2, which US-2 reads
  US-7   idle shutdown ENABLED on every Interactive domain, WITH the admin
         ceiling that bounds what a member may raise the timeout to (step 8.1)
  US-8   every blueprint-provisioned project role carries the D13 boundary
         (step 2, INT-15 - presence half only); a flow environment's own role
         is noted while EXC-27's shape holds
  US-9   the step 3 deny Sids reach all six persona sets together (Lesson 14)
  US-10  running apps reported as the burn they are (conventions 6)
  US-11  each deployment target holds one project, born of its own profile, with every
         environment ACTIVE (Stage 19 step 4.6, INV-21)
  US-12  where a project role exists, no role's trust names the account's root or any
         principal: the one layer under AWS's sts:AssumeRole on every role (TM-30)
  US-13  the house image's pin (6d decision 16 (a), INV-23): `experimentation` pins the
         newest CREATED version, each ACTIVE project born of it holds a SageMakerAIDomain
         domain, and each such domain pins the profile's version on both app types; a
         Tooling domain is noted in EXC-26's projects and fails in any other. Red from a
         release's register to its last Update project
  US-14  every blueprint configuration holds the one grant sagemaker-prereqs declares,
         CONTRIBUTOR projects of the root unit (INV-24); any other was added from a
         blueprint's Authorization tab and widens a project's Resource blueprints page
  US-15  no bucket outlives its environment (INV-25): a bucket carrying an
         environment's tag has that environment's stack live in its account. A deleted
         S3Bucket environment keeps its bucket and deletes its policy (SUP-394); any
         other resource a deleted environment left is a note (SUP-174)""")

        # ==============================================================================
        rep.h1("9. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 8 as a pass.

  - Every Sandbox beyond unit 1 has no profile until Stage 14 - re-run after
    each vend; the domain association list must grow with N (D35, INT-12).
  - The portal is a browser surface, reached from any network with an Identity
    Center session (D39); no profile reads it.
  - US-15 reads the tagging API in the domain's Region alone, where every
    environment deploys; a bucket an environment left elsewhere is not seen.""")

        # ==============================================================================
        rep.h1("10. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/studio.py")

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
