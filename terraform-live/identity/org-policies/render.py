#!/usr/bin/env -S uv run --quiet
# render.py - substitute the organization's own identifiers into the policy templates and
# report the size of each result against the Organizations limits.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./terraform-live/identity/org-policies/render.py
#             ./terraform-live/identity/org-policies/render.py awsds-infra-dev   # other profile
#   writes:   aws/output/rendered-policies/<name>.json   (UNTRACKED - .gitignore)
#   reads:    organizations:DescribeOrganization, ListRoots,
#             ListOrganizationalUnitsForParent, ListAccountsForParent,
#             sts:GetCallerIdentity.
#             It never creates, updates or deletes anything in AWS.
#
# WHY THE TEMPLATES CARRY PLACEHOLDERS AND NOT THE REAL IDS. Two independent reasons, and
# either one alone would be enough:
#   - The same organization id appears in awsds-org-scp-perimeter.json, in the tag and RCP
#     documents of step 7.8, and inside the OU path of the datazone carve-out. A value that
#     has to be typed correctly in four places will eventually be wrong in one of them, and
#     the direction it fails in is silent - a deny that never fires (Lesson 14). Generated
#     once, it cannot drift.
#   - At Stage 2 these documents move into Terraform, where the id comes from
#     `data.aws_organizations_organization.this.id` rather than from a literal. A template
#     with a placeholder is already that shape; a file with the id baked in would have to be
#     un-baked, which is an edit nobody remembers is pending.
# The rendered output lands in aws/output/, which is untracked, so no identifier enters a
# tracked file (aws/INDEX.md rule 1) - and the file there is what gets pasted into the
# console, byte for byte, so that Stage 2 step 5.5's import compares a document against
# itself instead of against a re-typing.
#
# WHAT IT CHECKS BESIDES SUBSTITUTING, because both failures are found at the END of the
# evening otherwise: that no placeholder survived (an unsubstituted <...> is a policy that
# attaches and denies nothing, or refuses to attach at all), that the JSON parses, and how
# many characters each document spends against the per-node budget.

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from awslib.awscli import AwsCli
from awslib.context import REGION, SSO_SESSION
from awslib.report import note

SRC_DIR = "terraform-live/identity/org-policies"
OUT_DIR = "aws/output/rendered-policies"

# The documented limits, since Service Quotas publishes none of them for `organizations`
# (Stage 1c step 7.0 step 5, measured): SCPs are 10 per node and 10 240 characters per
# document since the May 2026 increase; RCPs were not part of it and are still 5 and 5 120.
# This script checks every document against the TIGHTER number on purpose - the same folder
# holds 7.8's RCP, one file among several, and a limit that is right for most of them is the
# kind that is discovered by the one it was wrong for.
LIMIT = 5120

SURVIVOR_RE = re.compile(r"<[A-Z_]+>")


def die(message: str) -> None:
    note("")
    note(f"ERROR: {message}")
    sys.exit(1)


def main(argv: list) -> int:
    profile = argv[0] if argv else os.environ.get("AWSDS_PROFILE", "awsds-infra-identity")
    cli = AwsCli(profile=profile, region=REGION)

    os.chdir(Path(__file__).resolve().parents[3])  # repository root
    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------------ preflight
    res = cli.call("sts", "get-caller-identity", "--query", "Arn", "--output", "text")
    if not res.ok:
        note(f"cannot authenticate as '{profile}':")
        for line in res.merged.splitlines():
            if line.strip():
                note(f"  {line}")
        note("")
        note(f"log in first:  aws sso login --sso-session {SSO_SESSION}")
        return 1
    note(f"caller : {res.stdout}")

    # ------------------------------------------------------------------- the identifiers
    def text_of(*args: str) -> str:
        r = cli.call(*args)
        out = r.stdout if r.ok else ""
        return "" if out == "None" else out

    org_id = text_of(
        "organizations", "describe-organization", "--query", "Organization.Id", "--output", "text"
    )
    if not org_id:
        die("could not read the organization id")

    root_id = text_of("organizations", "list-roots", "--query", "Roots[0].Id", "--output", "text")
    if not root_id:
        die("could not read the root id")

    # The Data OU, by NAME - the one lookup that would otherwise be a hand-copied id. If the
    # OU is ever renamed this fails loudly here rather than producing a carve-out that
    # matches nothing, which is the failure direction that does not announce itself.
    ou_id_data = text_of(
        "organizations",
        "list-organizational-units-for-parent",
        "--parent-id",
        root_id,
        "--query",
        "OrganizationalUnits[?Name==`Data`].Id | [0]",
        "--output",
        "text",
    )
    if not ou_id_data:
        die(f"no OU named 'Data' directly under {root_id} - has it been renamed or nested?")

    # aws:PrincipalOrgPaths is the full path WITH a trailing slash, and `Data` sits directly
    # under the root, so this is the whole path. A nested OU would need one more segment -
    # and `*` in place of the final slash only if the carve-out is meant to reach children.
    org_path_data = f"{org_id}/{root_id}/{ou_id_data}/"

    # The Data Governance account id, resolved by OU MEMBERSHIP rather than pasted. The Data
    # OU document (step 7.6) carves the catalog-maintenance role out of its crawler deny
    # (D27), and an ARN condition may not name a wildcard account
    # (docs/plan/conventions.md) - so the id has to come from somewhere, and the only source
    # that cannot go stale is the organization itself. Exactly one account is expected:
    # `Data` holds Data Governance alone, and every account in this design except `Sandbox`
    # is structural (D35). Two accounts here is not a rendering problem to route around, it
    # is a change to the account map, so it stops.
    acct_ids = text_of(
        "organizations",
        "list-accounts-for-parent",
        "--parent-id",
        ou_id_data,
        "--query",
        "Accounts[?Status==`ACTIVE`].Id",
        "--output",
        "text",
    ).split()
    if len(acct_ids) != 1:
        die(
            f"expected exactly ONE active account in the Data OU ({ou_id_data}), found "
            f"{len(acct_ids)} - the account map changed, and the carve-out cannot be "
            "rendered until the plan says which account it names"
        )
    account_id_data = acct_ids[0]

    note(f"org    : {org_id}")
    note(f"root   : {root_id}")
    note(f"Data OU: {ou_id_data}")
    note(f"path   : {org_path_data}")
    # Masked on purpose: this line is read off a terminal that gets pasted into docs/log/,
    # and an account id is one of the three things `CLAUDE.md` keeps out of tracked files.
    # The full id is in the rendered document under aws/output/, which is untracked.
    note(f"Data ac: ...{account_id_data[-4:]}")
    note("")

    # ------------------------------------------------------------------------- rendering
    substitutions = {
        "<ORG_ID>": org_id,
        "<ROOT_ID>": root_id,
        "<OU_ID_DATA>": ou_id_data,
        "<ORG_PATH_DATA>": org_path_data,
        "<ACCOUNT_ID_DATA>": account_id_data,
    }

    rendered = 0
    failed = 0

    def render_one(src: Path) -> None:
        nonlocal rendered, failed
        base = src.name
        out = Path(OUT_DIR) / base

        text = src.read_text(encoding="utf-8")
        for placeholder, value in substitutions.items():
            text = text.replace(placeholder, value)
        out.write_text(text, encoding="utf-8")

        # 1. no placeholder may survive
        survivors = sorted(set(SURVIVOR_RE.findall(text)))
        if survivors:
            note(f"  {base}  UNSUBSTITUTED PLACEHOLDER:")
            for s in survivors:
                note(f"      {s}")
            failed += 1
            return

        # 2. it must be valid JSON
        try:
            doc = json.loads(text)
        except json.JSONDecodeError:
            note(f"  {base}  INVALID JSON")
            failed += 1
            return

        # 3. the size, as pasted (the file's own bytes) and minified
        raw = out.stat().st_size
        minified = len(json.dumps(doc, separators=(",", ":")))
        if minified > LIMIT:
            note(f"  {base}  TOO LARGE even minified: {minified} > {LIMIT}")
            failed += 1
            return
        note(
            f"  {base:<40} {raw:>5} bytes as written, {minified:>5} minified  "
            f"(limit {LIMIT}, margin {LIMIT - minified})"
        )
        rendered += 1

    note(f"rendering {SRC_DIR}/policies/ :")
    for f in sorted(Path(SRC_DIR, "policies").glob("*.json"), key=str):
        render_one(f)

    if Path(SRC_DIR, "canary").is_dir():
        note("")
        note(f"rendering {SRC_DIR}/canary/  (throwaway documents for the 7.3 battery):")
        for f in sorted(Path(SRC_DIR, "canary").glob("*.json"), key=str):
            render_one(f)

    # ---------------------------------------------------------------------------- verdict
    note("")
    note(f"wrote {rendered} file(s) to {OUT_DIR}/")
    if failed:
        note(f"{failed} file(s) FAILED - nothing there is safe to paste")
        return 1

    note("")
    note(f"PASTE FROM {OUT_DIR}/, not from {SRC_DIR}/ - the templates still hold placeholders.")
    note("Record the returned policy id beside each filename in")
    note(
        "docs/log/log-stage-01c-preventive-policies.md, as you attach it. An id read back out of a"
    )
    note("console you have just denied yourself access to is the failure that note prevents.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
