#!/usr/bin/env -S uv run --quiet
# bedrock.py - what Amazon Bedrock is enabled for, per account: the gates, the catalogue, and
#              the resources that would be billing.
#
#   needs:    a live SSO session, the only prerequisite:
#
#                 aws sso login --sso-session awsds
#
#             One login covers every profile below: the cached token is keyed by the
#             sso-session name, not by profile or account (see aws/INDEX.md).
#
#   run:      ./aws/bedrock.py                            every awsds-* profile
#             ./aws/bedrock.py awsds-infra-sandbox-1      only the profiles named
#             python3 aws/bedrock.py -                    ambient credentials (CloudShell)
#   writes:   aws/output/bedrock.txt   (untracked - see .gitignore)
#   reads:    bedrock:GetUseCaseForModelAccess, GetAccountDataRetention,
#             GetModelInvocationLoggingConfiguration, ListFoundationModels,
#             GetFoundationModelAvailability, ListInferenceProfiles, ListGuardrails,
#             ListCustomModels, ListImportedModels, ListProvisionedModelThroughputs,
#             ListMarketplaceModelEndpoints; iam:ListRoles and iam:ListAttachedRolePolicies for
#             section 7; and sts:GetCallerIdentity. Every one is a read;
#             this script never creates, updates or deletes anything and invokes no model.
#   exits:    0 every check passed | 1 a call failed | 2 a check FAILED
#
# THE DISTINCTION THIS FILE EXISTS TO HOLD. "Enabled" is three different questions and the
# console blurs them:
#
#   1. Does the ACCOUNT pass the gates - the use-case form submitted, the data retention mode
#      declared. Account-wide, and section 2 reads it.
#   2. Is the MODEL in the catalogue and invocable, and through which inference profile.
#      Region-wide, and section 4 reads it.
#   3. Can a PRINCIPAL invoke it. NOT READABLE HERE AT ALL - it is the intersection of the
#      identity policy, the permissions boundary, the SCPs and the endpoint policy
#      (Lesson 28), and the only instrument for it is a call. Section 7 says so at length,
#      because every reading above looks like an answer to it and none of them is.
#
# WHY THE AVAILABILITY READING IS PRINTED AND THEN DISBELIEVED. On 2026-09-11
# get-foundation-model-availability returned AUTHORIZED / AVAILABLE / AVAILABLE for all
# thirteen Anthropic models in us-west-2 - before the use-case form was submitted, after it was
# submitted, and after the account's retention mode moved to `none`. Four identical readings
# across two state changes. BR-7 turns that into a standing control: it compares the reading in
# an account that has the form against the accounts that do not, and reports whether the
# instrument distinguishes them. An instrument that answers the same thing whatever happened is
# not evidence (Lesson 62), and this is the one place that stays true after everyone forgets.
#
# WHAT `mode: none` DOES AND DOES NOT SHOW. The API documents `none` as zero data retention and
# `inherit` as *no mode set at this scope*; the vendor's design is that a model whose minimum
# retention is above `none` becomes unavailable rather than quietly retaining. NOTHING IN THE
# CONTROL PLANE SHOWS THAT HAPPENING: `allowed_modes` is in no Bedrock API, and the models the
# vendor names as retaining read exactly like the scoped ones. BR-5 therefore reports their
# PRESENCE rather than their reachability, and the only negative control is an invocation
# (Stage 6e step 7.2a).

from __future__ import annotations

import base64
import json
import re
import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.bedrockscope import SCP_PATH, scp_declaration
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "bedrock.txt"

# The slice that owns the grant, and the variable inside it that lists the project roles. BR-8
# compares that declaration against IAM, the way devenv.py compares the image's baked NO_PROXY
# against the account that generates it: neither side is authoritative on its own, and the two
# divergences are DIFFERENT FAULTS (see BR-8's own report block).
GRANT_SLICE_VARS = "terraform-live/sandbox/bedrock/variables.tf"
# Matched by shape, not by a fixed name. The policy is `awsds-<env>-bedrock-assistant` and this
# script does not know an account's env token - it runs against profiles, and the mapping lives in
# scripts/tfhygiene/backend.py, which aws/ deliberately does not import (aws/INDEX.md, the
# CloudShell fallback). A pattern answers the question without a second copy of that table.
GRANT_POLICY_RE = re.compile(r"^awsds-[a-z0-9]+-bedrock-assistant$")
PROJECT_ROLE_PREFIX = "datazone_usr_role_"

# `default = [ "datazone_usr_role_x_y", ... ]` inside the project_roles block. Anchored on the
# variable name so a second list variable in the same file cannot be picked up by accident.
PROJECT_ROLES_RE = re.compile(
    r'variable\s+"project_roles"\s*\{.*?default\s*=\s*\[(?P<body>.*?)\]', re.S
)

# The scoped set is READ from the SCP that declares it (awslib/bedrockscope.py), never spelled
# here. This file carried a literal until 2026-09-12 and it named the generation Stage 6e decision
# 14 had already abandoned, so BR-4 reported `pass` about three profiles nobody had scoped.

# The models the vendor's abuse-detection page named as retaining all traffic for up to 30 days,
# read 2026-09-11. This list is DATED, not derived: `allowed_modes` is in no API, so nothing here
# can refresh it. Stage 6e step 7.5's second deny is written against these ids.
RETAINING = ("anthropic.claude-fable-5", "anthropic.claude-fable-5-1")

# The calls whose non-empty answer is a bill. Each is (service-verb, JMESPath to the list).
BILLING = (
    ("list-provisioned-model-throughputs", "provisionedModelSummaries"),
    ("list-custom-models", "modelSummaries"),
    ("list-imported-models", "modelSummaries"),
    ("list-marketplace-model-endpoints", "marketplaceModelEndpoints"),
)

AVAIL_QUERY = (
    "[authorizationStatus,entitlementAvailability,regionAvailability,agreementAvailability.status]"
)


def decode_form(blob: str) -> dict | None:
    """The use-case form as the account declared it.

    ``formData`` is a blob on both Put and Get, and the CLI prints the outer base64. What is
    inside is itself base64 over a flat JSON object of the six fields - measured 2026-09-11,
    which is what makes the record readable at all. Any other shape returns None rather than
    guessing.
    """
    try:
        inner = base64.b64decode(blob, validate=True)
        doc = json.loads(base64.b64decode(inner, validate=True))
    except Exception:
        return None
    return doc if isinstance(doc, dict) else None


def declared_project_roles(path) -> list | None:
    """The role names `project_roles` declares, or None when the file is unreadable.

    None and [] are different answers and the report says which: an empty list is a slice that
    grants nothing yet, and None is a script running outside the repository (CloudShell).
    """
    if not path.is_file():
        return None
    match = PROJECT_ROLES_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        return None
    return re.findall(r'"([^"]+)"', match.group("body"))


def json_or_none(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c for c in callers if c.live]

    checks = Checks()
    gates: dict = {}  # profile -> dict(form, retention, logging)
    avail: dict = {}  # profile -> {model_id: reading}

    # None when the document is unreadable - standalone in CloudShell, or a malformed SCP. The
    # sections that need the set say why instead of falling back to a copy that would go stale.
    SCOPED, _, scope_why = scp_declaration(ctx.repo_root / SCP_PATH)
    SCOPED = SCOPED or {}

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("Amazon Bedrock: what is enabled, per account")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/bedrock.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The account gates: the use-case form, the retention mode, invocation logging
  3. What the form declared, decoded
  4. The catalogue, and the scoped set's availability per account
  5. Inference profiles the account holds
  6. Bedrock resources that would be billing
  7. The grant on the project roles, code against account
  8. What "enabled" does NOT mean
  9. Checks
 10. Calls that failed

HOW TO READ THIS FILE
  - THE CATALOGUE IS NOT REACH. A model reading AVAILABLE says the account may invoke
    it; whether a given principal may is the intersection of four policy layers and is
    answered by a call, never by a read. Section 8.
  - SECTION 7 READS BOTH SIDES OF THE GRANT, and the two divergences are different
    faults: a declared attachment that is gone was removed by something (INT-15), and
    an attachment nothing declares will be removed by the next apply (Lesson 35).
  - `ResourceNotFoundException` ON THE FORM IS THE "NEVER SUBMITTED" ANSWER, reported as
    NOT SUBMITTED rather than as a failure.
  - `inherit` IS NOT `none`. The API documents it as *no data retention mode is set at
    this scope*, so the account has declared nothing and each model's own default applies.
  - AN EMPTY SECTION 6 IS THE GOOD ANSWER. Every list there costs money when it is not
    empty, and none of it is created by this project today.
  - This is a point-in-time snapshot, not a source of truth: regenerate it rather than
    trusting a stale copy, and record intent in docs/plan/ or docs/log/, never here.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore). IT CONTAINS ACCOUNT IDS AND
WHATEVER THE USE-CASE FORM DECLARED, WHICH INCLUDES A NAME AND A WEBSITE. Do not copy
any of it into a tracked file.""")

        # ------------------------------------------------------------------------------
        rep.h1("1. Which accounts were measured, and as whom")

        rep.tabulate(
            ["PROFILE\tACCOUNT\tCALLER ARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )
        rep.text("""
A `(failed)` row is a profile that did not authenticate and is excluded from every
table below. MANAGEMENT, LOG ARCHIVE and AUDIT hold no project persona (guiding
principle 1) and cannot appear here at all - absent, not reassuring.""")

        # ------------------------------------------------------------------------------
        rep.h1("2. The account gates: the use-case form, the retention mode, invocation logging")

        for c in live:
            cli = cli_for(c.profile)
            rep.h2(f"2.x {c.profile}  ({c.account})")
            state = {"form": None, "retention": "?", "logging": "?"}

            res = cli.call(
                "bedrock",
                "get-use-case-for-model-access",
                "--query",
                "formData",
                "--output",
                "text",
            )
            rep.line(cli.echo(("bedrock", "get-use-case-for-model-access")))
            if res.ok:
                state["form"] = res.stdout.strip()
                rep.line("  => SUBMITTED (returns a formData blob; decoded in section 3)")
            elif "ResourceNotFoundException" in res.merged:
                rep.line(
                    "  => NOT SUBMITTED - the documented shape of a form that was never filled"
                )
            else:
                rep.line(f"  !! {head2(res.merged)}")
                errors.add(("bedrock", "get-use-case-for-model-access"), res.merged, c.profile)

            res = cli.call("bedrock", "get-account-data-retention", "--output", "json")
            rep.line(cli.echo(("bedrock", "get-account-data-retention")))
            doc = json_or_none(res.stdout) if res.ok else None
            if doc:
                state["retention"] = doc.get("mode", "?")
                when = doc.get("updatedAt", "never set at this scope")
                rep.line(f"  => mode {state['retention']}   (updatedAt: {when})")
            elif not res.ok:
                rep.line(f"  !! {head2(res.merged)}")
                errors.add(("bedrock", "get-account-data-retention"), res.merged, c.profile)

            res = cli.call(
                "bedrock", "get-model-invocation-logging-configuration", "--output", "json"
            )
            rep.line(cli.echo(("bedrock", "get-model-invocation-logging-configuration")))
            if res.ok:
                state["logging"] = "OFF" if not res.stdout.strip() else "ON"
                if state["logging"] == "OFF":
                    rep.line(
                        "  => OFF - an empty answer is the documented shape of no configuration"
                    )
                else:
                    rep.line("  => ON. The full prompt and completion are being written somewhere:")
                    rep.line(res.stdout)
            else:
                rep.line(f"  !! {head2(res.merged)}")
                errors.add(
                    ("bedrock", "get-model-invocation-logging-configuration"), res.merged, c.profile
                )

            gates[c.profile] = state

        rep.line()
        rep.tabulate(
            ["PROFILE\tACCOUNT\tUSE-CASE FORM\tRETENTION MODE\tINVOCATION LOGGING"]
            + [
                f"{c.profile}\t{c.account}\t"
                f"{'SUBMITTED' if gates[c.profile]['form'] else 'not submitted'}\t"
                f"{gates[c.profile]['retention']}\t{gates[c.profile]['logging']}"
                for c in live
            ]
        )

        # ------------------------------------------------------------------------------
        rep.h1("3. What the form declared, decoded")

        submitted = [c for c in live if gates[c.profile]["form"]]
        if not submitted:
            rep.line("No account measured here has a use-case form. Nothing to decode.")
        for c in submitted:
            doc = decode_form(gates[c.profile]["form"])
            rep.h2(f"3.x {c.profile}  ({c.account})")
            if doc is None:
                rep.text("""The blob did not decode as double base64 over a flat JSON object, which is
the shape measured on 2026-09-11. THIS IS A FINDING, not a failure: the encoding
is undocumented, so it can change. Print the raw value and look at it.""")
                continue
            rep.tabulate(["FIELD\tVALUE"] + [f"{k}\t{v!r}" for k, v in doc.items()])
            rep.text("""
The form is ACCOUNT-LEVEL: neither PutUseCaseForModelAccess nor
GetUseCaseForModelAccess takes a modelId, in the path or in the body. Selecting a
model in the console is the route to the form, not a per-model grant - so one
submission covers every Anthropic model in the account.""")

        # ------------------------------------------------------------------------------
        rep.h1("4. The catalogue, and the scoped set's availability per account")

        anchor = submitted[0] if submitted else (live[0] if live else None)
        if anchor:
            cli = cli_for(anchor.profile)
            rep.h2(f"4.1 Providers in the {context.REGION} catalogue (read as {anchor.profile})")
            res = cli.call(
                "bedrock",
                "list-foundation-models",
                "--query",
                "modelSummaries[].providerName",
                "--output",
                "text",
            )
            if res.ok:
                counts: dict = {}
                for name in res.stdout.split():
                    counts[name] = counts.get(name, 0) + 1
                rep.tabulate(
                    ["PROVIDER\tMODELS"]
                    + [f"{k}\t{v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]
                )
            else:
                errors.add(("bedrock", "list-foundation-models"), res.merged, anchor.profile)

            rep.h2("4.2 The scoped set, and the retaining models beside it")
            if scope_why:
                rep.text(f"The scoped set is empty here: {scope_why}")
            rows = ["MODEL\tROLE\tLIFECYCLE\tINFERENCE TYPES"]
            for model in list(SCOPED) + list(RETAINING):
                role = "scoped" if model in SCOPED else "RETAINS (vendor page, 2026-09-11)"
                res = cli.call(
                    "bedrock",
                    "get-foundation-model",
                    "--model-identifier",
                    model,
                    "--query",
                    "modelDetails.[modelLifecycle.status,inferenceTypesSupported]",
                    "--output",
                    "json",
                )
                doc = json_or_none(res.stdout) if res.ok else None
                if doc:
                    rows.append(f"{model}\t{role}\t{doc[0]}\t{','.join(doc[1])}")
                else:
                    rows.append(f"{model}\t{role}\tNOT IN CATALOGUE\t-")
                    if not res.ok and "ValidationException" not in res.merged:
                        errors.add(
                            ("bedrock", "get-foundation-model", model), res.merged, anchor.profile
                        )
            rep.tabulate(rows)
            rep.text("""
`INFERENCE_PROFILE` alone means THE BARE MODEL ID IS NOT INVOCABLE: a request must
name a profile, and section 5 says which exist.""")

        rep.h2("4.3 get-foundation-model-availability, per account - the instrument under test")
        head = ["PROFILE\tFORM\t" + "\t".join(m.split(".", 1)[1] for m in SCOPED)]
        rows = []
        for c in live:
            cli = cli_for(c.profile)
            readings = {}
            for model in SCOPED:
                res = cli.call(
                    "bedrock",
                    "get-foundation-model-availability",
                    "--model-id",
                    model,
                    "--query",
                    AVAIL_QUERY,
                    "--output",
                    "text",
                )
                readings[model] = "/".join(res.stdout.split()) if res.ok else "CALL FAILED"
                if not res.ok:
                    errors.add(
                        ("bedrock", "get-foundation-model-availability", model),
                        res.merged,
                        c.profile,
                    )
            avail[c.profile] = readings
            form = "yes" if gates[c.profile]["form"] else "no"
            rows.append(f"{c.profile}\t{form}\t" + "\t".join(readings[m] for m in SCOPED))
        rep.tabulate(head + rows)
        rep.text("""
READ THE `FORM` COLUMN AGAINST THE OTHERS. If accounts that have submitted the form
and accounts that have not report the same availability, this call does not measure
access and must not be used as evidence of it - that is BR-7, and it is the reason
section 2's form reading is the instrument for the gate.""")

        # ------------------------------------------------------------------------------
        rep.h1("5. Inference profiles the account holds")

        for c in live:
            cli = cli_for(c.profile)
            rep.h2(f"5.x {c.profile}  ({c.account})")
            rep.show(
                cli,
                "bedrock",
                "list-inference-profiles",
                "--query",
                "inferenceProfileSummaries[?status=='ACTIVE'].[inferenceProfileId,type,"
                "length(models)]",
                "--output",
                "text",
            )

        rep.text("""A SYSTEM_DEFINED profile is AWS's cross-region routing object and exists whether
or not this account uses it; APPLICATION profiles are created by an account and are
the ones an inference-profile ARN in a policy would be pinned to. The third column is
how many foundation models the profile routes to - anything above 1 is a model
processed outside this Region some of the time (Stage 6e step 7.3).""")

        # ------------------------------------------------------------------------------
        rep.h1("6. Bedrock resources that would be billing")

        billing_rows = ["PROFILE\tRESOURCE\tCOUNT"]
        any_billing = False
        for c in live:
            cli = cli_for(c.profile)
            for verb, path in BILLING:
                res = cli.call("bedrock", verb, "--query", f"length({path})", "--output", "text")
                if not res.ok:
                    billing_rows.append(f"{c.profile}\t{verb}\tCALL FAILED")
                    errors.add(("bedrock", verb), res.merged, c.profile)
                    continue
                count = res.stdout.strip() or "0"
                billing_rows.append(f"{c.profile}\t{verb}\t{count}")
                if count not in ("0", "None", ""):
                    any_billing = True
            res = cli.call(
                "bedrock", "list-guardrails", "--query", "length(guardrails)", "--output", "text"
            )
            billing_rows.append(
                f"{c.profile}\tlist-guardrails\t{res.stdout.strip() or '0'}"
                if res.ok
                else f"{c.profile}\tlist-guardrails\tCALL FAILED"
            )
            if not res.ok:
                errors.add(("bedrock", "list-guardrails"), res.merged, c.profile)
        rep.tabulate(billing_rows)
        rep.text("""
PROVISIONED THROUGHPUT IS THE EXPENSIVE ROW: it is committed capacity billed by the
hour whether or not a token is spent, and `make down` does not reach it. Custom,
imported and marketplace-endpoint models each carry their own standing cost.
Guardrails are cheap and are listed because they change what an invocation does, not
because of the bill.""")

        # ------------------------------------------------------------------------------
        rep.h1("7. The grant on the project roles, code against account")

        declared = declared_project_roles(ctx.repo_root / GRANT_SLICE_VARS)
        rep.text(f"""The grant is per project by design (Stage 6e decision 8): a SMUS project role is
minted by the service, and the blueprint offers no field that grants anything, so
`{GRANT_SLICE_VARS}` names the roles one at a time.

THE TWO DIVERGENCES ARE DIFFERENT FAULTS:

  in the code, missing from the account   the attachment was REMOVED - a blueprint
                                          reconciliation is the suspect (INT-15's open half),
                                          and the symptom a user sees is an assistant that
                                          stopped working with no diff in the repository
  in the account, missing from the code   it was attached BY HAND (the runbook's P3) and the
                                          next `terraform apply` of the slice will take it
                                          away again - Lesson 35, the stale path that still
                                          succeeds

Neither is visible from the other side alone, which is why both sides are read here.""")

        for c in live:
            cli = cli_for(c.profile)
            rep.h2(f"7.x {c.profile}  ({c.account})")

            res = cli.call(
                "iam",
                "list-roles",
                "--query",
                f"Roles[?starts_with(RoleName, `{PROJECT_ROLE_PREFIX}`)].RoleName",
                "--output",
                "text",
            )
            if not res.ok:
                rep.line(f"  !! {head2(res.merged)}")
                errors.add(("iam", "list-roles"), res.merged, c.profile)
                continue
            roles = sorted(res.stdout.split())
            if not roles:
                rep.line(
                    "  no SMUS project role in this account - nothing to grant, and nothing to check"
                )
                continue

            attached: dict = {}
            for role in roles:
                got = cli.call(
                    "iam",
                    "list-attached-role-policies",
                    "--role-name",
                    role,
                    "--query",
                    "AttachedPolicies[].PolicyName",
                    "--output",
                    "text",
                )
                if not got.ok:
                    errors.add(("iam", "list-attached-role-policies", role), got.merged, c.profile)
                    attached[role] = None
                    continue
                attached[role] = any(GRANT_POLICY_RE.match(n) for n in got.stdout.split())

            rows = ["PROJECT ROLE\tIN THE CODE\tGRANT ATTACHED\tVERDICT"]
            for role in roles:
                in_code = "-" if declared is None else ("yes" if role in declared else "no")
                has = attached[role]
                shown = "?" if has is None else ("yes" if has else "no")
                if declared is None or has is None:
                    verdict = "not compared"
                elif (role in declared) == has:
                    verdict = "agree"
                elif has:
                    verdict = "ATTACHED BY HAND"
                else:
                    verdict = "REMOVED"
                rows.append(f"{role}\t{in_code}\t{shown}\t{verdict}")
            rep.tabulate(rows)

            if declared is None:
                checks.note(
                    "BR-8",
                    "the grant declaration is unreadable",
                    f"{GRANT_SLICE_VARS} not found - running outside the repository",
                )
                continue
            removed = [r for r in roles if r in declared and attached.get(r) is False]
            byhand = [r for r in roles if r not in declared and attached.get(r) is True]
            ungranted = [r for r in roles if r not in declared and attached.get(r) is False]
            if removed:
                checks.fail(
                    "BR-8",
                    "a declared grant is NOT attached",
                    f"{', '.join(removed)} - removed since the last apply; suspect a "
                    f"blueprint reconciliation (INT-15)",
                )
            if byhand:
                checks.fail(
                    "BR-8",
                    "a grant is attached that the code does not declare",
                    f"{', '.join(byhand)} - attached by hand; the next apply of "
                    f"sandbox/bedrock/ will detach it (Lesson 35)",
                )
            if not removed and not byhand:
                checks.ok(
                    "BR-8",
                    "code and account agree on the grant",
                    f"{c.profile}: {len(roles)} project role(s), "
                    f"{sum(1 for r in roles if attached.get(r))} granted",
                )
            if ungranted:
                checks.note(
                    "BR-8",
                    "a project has no Bedrock grant",
                    f"{', '.join(ungranted)} - by design unless somebody asked for it; "
                    f"the runbook's section P is how it gets one",
                )

        # ------------------------------------------------------------------------------
        rep.h1('8. What "enabled" does NOT mean')

        rep.text("""NOTHING IN THIS FILE SAYS A PRINCIPAL CAN INVOKE A MODEL. Reach is an
intersection (Lesson 28) and this script reads one term of it:

  the identity policy   - the role's own grant. On a SageMaker project role it is
                          authored by the blueprint, not by this repository, and it
                          may allow InvokeModel on `foundation-model/*` while allowing
                          nothing on the inference-profile ARN the call must also
                          name. Both are evaluated.
  the permissions       - D13's awsds-sandbox-project-boundary. A boundary grants
    boundary              nothing; it only subtracts.
  the SCPs              - the organization's, evaluated before either.
  the endpoint policy   - once the call goes through an interface endpoint, a fourth
                          statement of the same intent.

AND THE RETENTION MODE IS NOT VISIBLE IN ITS EFFECT. `allowed_modes` - which model
admits which mode - is in no Bedrock API: not in get-foundation-model, not in
list-foundation-models, not in get-foundation-model-availability, and not in
list-foundation-model-agreement-offers, whose termDetails carries pricing, legal and
support terms only. The models RETAINING names read exactly like the scoped ones. So
`none` is verified as a SETTING by section 2 and is unverified as a CONTROL until
something invokes a retaining model and reads the refusal.

The instrument for all of it is a call. Stage 6e steps 6 and 7.2a are where it lives.""")

        # ------------------------------------------------------------------------------
        rep.h1("9. Checks")

        for c in live:
            state = gates[c.profile]
            label = f"{c.profile} ({c.account})"

            if state["form"]:
                checks.ok("BR-1", "use-case form submitted", label)
            else:
                checks.note(
                    "BR-1", "no use-case form", f"{label} - no Anthropic model can be invoked here"
                )

            if state["retention"] == "none":
                checks.ok("BR-2", "retention mode is none", label)
            elif state["retention"] in ("inherit", "?"):
                checks.note(
                    "BR-2",
                    f"retention mode is {state['retention']}",
                    f"{label} - nothing declared at this scope; each model's default applies",
                )
            else:
                checks.fail(
                    "BR-2",
                    f"retention mode is {state['retention']}",
                    f"{label} - not none, so prompts may be retained",
                )

            if state["logging"] == "OFF":
                checks.ok("BR-3", "invocation logging off", label)
            elif state["logging"] == "ON":
                checks.fail(
                    "BR-3",
                    "invocation logging ON",
                    f"{label} - full prompts and completions are being written; "
                    f"Stage 6e decision 5 says off until Stage 11 step 5.6",
                )

        if anchor:
            profs = cli_for(anchor.profile).call(
                "bedrock",
                "list-inference-profiles",
                "--query",
                "inferenceProfileSummaries[?status=='ACTIVE'].inferenceProfileId",
                "--output",
                "text",
            )
            have = set(profs.stdout.split()) if profs.ok else set()
            missing = [p for p in SCOPED.values() if p not in have]
            if not SCOPED:
                checks.fail("BR-4", "the scoped set could not be read", scope_why)
            elif profs.ok and not missing:
                checks.ok(
                    "BR-4",
                    "every scoped model has an ACTIVE us. profile",
                    f"{len(SCOPED)} of {len(SCOPED)} in {anchor.profile}",
                )
            elif profs.ok:
                checks.fail("BR-4", "a scoped model has no ACTIVE profile", ", ".join(missing))

            present = []
            for model in RETAINING:
                res = cli_for(anchor.profile).call(
                    "bedrock",
                    "get-foundation-model",
                    "--model-identifier",
                    model,
                    "--query",
                    "modelDetails.modelId",
                    "--output",
                    "text",
                )
                if res.ok:
                    present.append(model)
            if present:
                checks.note(
                    "BR-5",
                    "a retaining model is in the catalogue",
                    f"{', '.join(present)} - outside the scoped set by design; only "
                    f"Stage 6e step 7.5's deny stops an invocation",
                )

        if any_billing:
            checks.fail(
                "BR-6",
                "a Bedrock resource is billing",
                "see section 6 - provisioned throughput, custom, imported or marketplace",
            )
        else:
            checks.ok("BR-6", "nothing in Bedrock is billing by the hour", "section 6 is empty")

        with_form = {p for p, s in gates.items() if s["form"]}
        without = {p for p in avail if p not in with_form}
        if with_form and without:
            same = all(avail[a] == avail[b] for a in with_form for b in without if a in avail)
            if same:
                checks.note(
                    "BR-7",
                    "availability does not distinguish the form",
                    "accounts with and without a submitted form report the same reading - "
                    "this call is not evidence of access",
                )
            else:
                checks.note(
                    "BR-7",
                    "availability DOES distinguish the form",
                    "a reading differs between an account with a form and one without - "
                    "re-read it; the 2026-09-11 measurement said it does not",
                )
        else:
            checks.note(
                "BR-7",
                "availability control not runnable",
                "needs at least one account with a form and one without in the same run",
            )

        rep.checks_table(checks)
        rep.text("""
A `note` is not a failure: BR-1 and BR-2 are notes in an account that is supposed to
have no Bedrock use at all, and BR-5 is a note because the deny it points at is a
Stage 6e step rather than a deployed control, and BR-8's "no grant" note is the design -
a project gets Bedrock when somebody asks, not by existing.""")

        # ------------------------------------------------------------------------------
        rep.h1("10. Calls that failed")

        failed_calls_epilogue(
            rep,
            errors,
            "Regenerate with:  ./aws/bedrock.py",
        )

    # ---------------------------------------------------------------------------------- run
    note("")
    n_fail = checks.n_fail()
    if n_fail:
        note(f"wrote {out_label} ({n_fail} check(s) FAILED - see section 9)")
        return 2
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 10)")
        return 1
    note(f"wrote {out_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
