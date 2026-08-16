#!/usr/bin/env -S uv run --quiet
# org-delegation.py - can the Identity account manage the ORGANIZATION'S POLICIES, and
# exactly which of them? The standing instrument for INT-20.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/org-delegation.py                 # awsds-infra-identity
#             python3 aws/org-delegation.py -         # no --profile: CloudShell on
#                                                     # MANAGEMENT, as CT Admin (no uv
#                                                     # there; bring the aws/ folder)
#   writes:   aws/output/org-delegation.txt   (untracked - see .gitignore)
#   reads:    organizations:DescribeResourcePolicy, DescribeOrganization, ListRoots,
#             ListOrganizationalUnitsForParent, ListPoliciesForTarget,
#             sts:GetCallerIdentity. It never creates, updates or deletes anything.
#   exits:    0 the report was produced | 1 a call failed unexpectedly | 2 a check FAILED
#
# WHY THIS EXISTS. Permission sets reach the Identity account through the IAM Identity
# Center delegated administrator, which Stage 1b step 1 proved. SCPs, RCPs, tag policies and
# declarative policies DO NOT: they are AWS Organizations objects, and reaching them needs a
# second, different mechanism - a RESOURCE-BASED DELEGATION POLICY on the organization
# (organizations:PutResourcePolicy), written from Management. Nothing before Stage 2 step 5.1
# creates it, and INT-20 records the plausible failure as "the delegation works and still
# cannot touch a root attachment". Since Stage 1c put SIX OF THE TEN DOCUMENTS ON THE ROOT,
# that outcome costs most of terraform-live/identity/org-policies/ rather than a corner of
# it - which is why Stage 2 answers this before writing a line of that slice.
#
# THE TRAP THIS SCRIPT IS BUILT AROUND, and it is the reason section 4 exists as a warning
# rather than as a result. ORGANIZATIONS *READS* ALREADY ANSWER FROM THE IDENTITY ACCOUNT
# WITHOUT ANY POLICY DELEGATION - measured 2026-08-12/13 (Stage 1c verification (x)), because
# a delegated administrator for ANY service may read the organization. So `describe-policy`
# succeeding here proves nothing about the policy delegation: it returns the same answer
# before and after step 5.1, which is Lesson 13 exactly. THE ONLY DECISIVE READ IS THE
# DELEGATION DOCUMENT ITSELF, and the only decisive test is a WRITE - which this script
# deliberately does not perform. That line is the same one aws/probes/ draws: a measurement
# that changes a policy is a human act on Management.
#
# So what this script decides is SCOPE, by reading: does a delegation exist, does it name
# this account, which policy TYPES does it admit, and - the half that fails silently - does
# its Resource list reach the ROOT, the NESTED OUs, and the POLICY-type ARNs at all (DEL-9:
# a target-only list denies every write). AWS documents that naming a single OU "excludes
# child OUs and accounts under child OUs", and this organization is two levels deep (D23:
# `Sandboxes` under `Interactive`).
#
# IDENTITY. Default profile is `awsds-infra-identity` - the account the delegation is FOR,
# which is the only place the answer means anything. The `-` fallback is CloudShell on
# Management as `AWS Control Tower Admin`, and it answers a different question: it shows the
# document from the side that wrote it, and it always succeeds, so a green run there says
# nothing about whether Identity can use it. Prefer the profile.

from __future__ import annotations

import json
import os
import sys
from collections import deque

from awslib import context
from awslib.awscli import AwsCli, head2
from awslib.report import Checks, Report, note

OUT_NAME = "org-delegation.txt"

POLICY_TYPES = [
    "SERVICE_CONTROL_POLICY",
    "RESOURCE_CONTROL_POLICY",
    "TAG_POLICY",
    "DECLARATIVE_POLICY_EC2",
]


def decompose(doc: dict, org_id: str, root_id: str, identity_acct: str) -> dict:
    """Reading the document is the instrument (Lesson 22). What is checked is SCOPE, in the
    three places it fails silently: the policy TYPES it admits, whether the Resource list
    reaches the ROOT, and whether it reaches OUs AT ANY DEPTH rather than one named OU."""
    stmts = doc.get("Statement", [])
    if isinstance(stmts, dict):
        stmts = [stmts]

    def as_list(v):
        if v is None:
            return []
        return v if isinstance(v, list) else [v]

    actions, resources, principals, conds = set(), set(), set(), []
    for s in stmts:
        if s.get("Effect") != "Allow":
            continue
        for a in as_list(s.get("Action")):
            actions.add(a)
        for r in as_list(s.get("Resource")):
            resources.add(r)
        p = s.get("Principal")
        if isinstance(p, dict):
            for v in p.values():
                for x in as_list(v):
                    principals.add(x)
        else:
            for x in as_list(p):
                principals.add(x)
        if s.get("Condition"):
            conds.append(s["Condition"])

    def covers(action: str) -> bool:
        for a in actions:
            if a in ("*", "organizations:*"):
                return True
            if a == action:
                return True
            if a.endswith("*") and action.startswith(a[:-1]):
                return True
        return False

    # The write half Stage 2 step 5.1 requires, and the two that must be ABSENT.
    write = [
        "organizations:CreatePolicy",
        "organizations:UpdatePolicy",
        "organizations:DeletePolicy",
        "organizations:AttachPolicy",
        "organizations:DetachPolicy",
    ]
    forbid = ["organizations:EnablePolicyType", "organizations:DisablePolicyType"]
    read = [
        "organizations:DescribeOrganization",
        "organizations:ListRoots",
        "organizations:ListOrganizationalUnitsForParent",
        "organizations:ListChildren",
        "organizations:ListParents",
        "organizations:ListAccounts",
        "organizations:ListPolicies",
        "organizations:ListPoliciesForTarget",
        "organizations:ListTargetsForPolicy",
        "organizations:ListTagsForResource",
        # Added 2026-08-15 with Stage 2 step 5.1's correction, so DEL-4 covers what 5.1
        # now names. DescribePolicy is the load-bearing one - the provider calls it on
        # every refresh of an aws_organizations_policy, so without it 5.5's import
        # succeeds and the next plan fails. DescribeResourcePolicy is for THIS script:
        # if it were ever denied, DEL-1 would report "denied" and every check below it
        # would go vacuous.
        "organizations:DescribeOrganizationalUnit",
        "organizations:DescribeAccount",
        "organizations:DescribePolicy",
        "organizations:DescribeEffectivePolicy",
        "organizations:DescribeResourcePolicy",
        "organizations:ListAccountsForParent",
    ]

    # DEL-9 (added 2026-08-15). Create/Update/DeletePolicy authorize against the POLICY ARN
    # and Attach/DetachPolicy against target AND policy, so a target-only Resource list
    # denies every write. Shape:
    # arn:aws:organizations::<mgmt>:policy/o-<org>/<policy_type>/<id-or-*>; a bare "*" or a
    # policy/o-<org>/* entry covers every type.
    required_policy_types = [
        "service_control_policy",
        "resource_control_policy",
        "tag_policy",
        "declarative_policy_ec2",
    ]

    def policy_arn_covers(t: str) -> bool:
        for r in resources:
            if r == "*":
                return True
            if ":policy/" not in r:
                continue
            parts = r.split(":policy/", 1)[1].split("/")
            if len(parts) > 1 and parts[1] in ("*", t):
                return True
        return False

    out = {
        "principals": sorted(principals),
        "resources": sorted(resources),
        "actions": sorted(actions),
        "write_missing": [a for a in write if not covers(a)],
        "read_missing": [a for a in read if not covers(a)],
        "forbidden_granted": [a for a in forbid if covers(a)],
        "identity_named": any(identity_acct in p for p in principals) or "*" in principals,
        "wildcard_principal": "*" in principals,
        # Resource coverage, the half that fails silently.
        "root_covered": any(
            r == "*" or root_id in r or (":root/" in r and r.endswith("*")) for r in resources
        ),
        "ou_wildcard": any(
            r == "*" or (":ou/" in r and r.rstrip().endswith("*")) for r in resources
        ),
        "ou_single_named": sorted(
            r for r in resources if ":ou/" in r and not r.rstrip().endswith("*")
        ),
        "policy_types_missing": [t for t in required_policy_types if not policy_arn_covers(t)],
        "policy_type_conditions": sorted(
            {
                v
                for c in conds
                for op, kv in c.items()
                for k, vals in kv.items()
                if k.lower() == "organizations:policytype"
                for v in (vals if isinstance(vals, list) else [vals])
            }
        ),
        # DEL-8's operator half (added 2026-08-15, after step 5.0's write). The value list
        # alone cannot tell a working delegation from one that refuses every write: without
        # IfExists, any call whose request context omits organizations:PolicyType fails the
        # condition and is DENIED. That arrives at the keyboard as "every write refused" -
        # which is exactly what a delegation unable to reach a root attachment looks like,
        # the one thing step 5.0 exists to distinguish. The check that cannot separate them
        # is Lesson 13.
        "policy_type_operators": sorted(
            {
                op
                for c in conds
                for op, kv in c.items()
                for k in kv
                if k.lower() == "organizations:policytype"
            }
        ),
        "n_statements": len(stmts),
    }
    # Any/Value-set prefixes are irrelevant here; what matters is the IfExists suffix.
    # Operators are ANDed inside a Condition block, so ONE strict operator on this key
    # denies the call regardless of what its siblings say.
    out["policy_type_operators_strict"] = [
        op for op in out["policy_type_operators"] if not op.lower().endswith("ifexists")
    ]

    # DEL-10 (added 2026-08-15, Stage 2 step 5.1a). The delegation's Principal is the
    # ACCOUNT - a resource policy has no narrower principal to write - so every principal
    # in Identity that also holds organizations:* identity-side is reached, and Control
    # Tower put one there nobody chose (AWSOrganizationsFullAccess -> AWSControlTowerAdmins,
    # open question 11). 5.1a narrows the two WRITE statements with a Condition on
    # aws:PrincipalArn matching the InfrastructureAccess role pattern; the navigation
    # statement stays uncondiitoned by design (it grants nothing the account does not
    # already hold as a delegated administrator of another service). Without this check
    # the condition is an intention rather than a control (Lesson 5).
    sso_pattern = "AWSReservedSSO_InfrastructureAccess_"
    tag_actions = {"organizations:TagResource", "organizations:UntagResource"}

    def principal_arn_operator(s: dict) -> str | None:
        for op, kv in (s.get("Condition") or {}).items():
            for k, vals in kv.items():
                if k.lower() == "aws:principalarn":
                    vals = vals if isinstance(vals, list) else [vals]
                    if any(sso_pattern in v for v in vals):
                        return op
        return None

    missing, operators = [], []
    for s in stmts:
        acts = set(as_list(s.get("Action")))
        if not (acts & set(write) or acts & tag_actions):
            continue
        op = principal_arn_operator(s)
        if op is None:
            missing.append(s.get("Sid") or "<no Sid>")
        else:
            operators.append(f"{s.get('Sid') or '<no Sid>'}: {op}")
    out["write_stmts_missing_principal_arn"] = missing
    out["write_stmts_principal_arn_operators"] = operators
    return out


def main(argv: list) -> int:
    profile = argv[0] if argv else os.environ.get("AWSDS_PROFILE", "awsds-infra-identity")
    cli = AwsCli(profile=profile, region=context.REGION)
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    checks = Checks()

    # ---------------------------------------------------------------------------- preflight
    note(f"profile: {cli.label} (region {cli.region})")
    res = cli.call("sts", "get-caller-identity", "--query", "Arn", "--output", "text")
    if not res.ok:
        note("")
        note(f"cannot authenticate as '{cli.label}':")
        for line in res.merged.splitlines():
            if line.strip():
                note(f"  {line}")
        note("")
        note("log in first:")
        note(f"  aws sso login --sso-session {context.SSO_SESSION}")
        note("")
        note(f"the previous {out_label}, if any, is left untouched.")
        return 1
    caller = res.stdout

    acct_res = cli.call("sts", "get-caller-identity", "--query", "Account", "--output", "text")
    caller_acct = acct_res.stdout if acct_res.ok else ""
    note(f"caller : {caller}")

    # --------------------------------------------------------------- the delegation document
    note("reading the organization resource policy...")

    # The ONE call whose failure is the answer. Three outcomes have to stay distinguishable:
    #   - a document                       -> a delegation exists; sections 3 and 5 read it
    #   - ResourcePolicyNotFoundException  -> no delegation. Step 5.1 has not run. NOT a
    #     denial
    #   - AccessDenied / anything else     -> the read itself was refused, a THIRD state
    # Collapsing the last two is the mistake this script exists to make impossible.
    res = cli.call(
        "organizations",
        "describe-resource-policy",
        "--query",
        "ResourcePolicy.Content",
        "--output",
        "text",
    )
    respol_err = res.stderr
    respol_content = ""
    if res.ok and res.stdout:
        respol_content = res.stdout
        respol_state = "present"
    elif "ResourcePolicyNotFound" in respol_err or "resourcepolicynotfound" in respol_err.lower():
        respol_state = "absent"
    elif any(t in respol_err.lower() for t in ("accessdenied", "not authorized", "explicit deny")):
        respol_state = "denied"
    else:
        respol_state = "error"
        cli.errors.entries.append(
            f"aws organizations describe-resource-policy\n    {head2(respol_err)}"
        )

    # ------------------------------------------------------ what is attached, per class
    note("finding the documents a write would have to reach...")

    res = cli.run(
        "organizations", "list-roots", "--query", "Roots[0].[Name,Id]", "--output", "text"
    )
    fields = res.text.split("\t") if res.text else []
    root_name = fields[0] if len(fields) > 0 else ""
    root_id = fields[1] if len(fields) > 1 else ""

    res = cli.run(
        "organizations",
        "describe-organization",
        "--query",
        "Organization.[Id,MasterAccountId]",
        "--output",
        "text",
    )
    fields = res.text.split("\t") if res.text else []
    org_id = fields[0] if len(fields) > 0 else ""
    mgmt_id = fields[1] if len(fields) > 1 else ""

    targets: list = []  # (CLASS, node name, node id, TYPE, pid, pname)

    def collect_target(node_class: str, node_name: str, node_id: str) -> None:
        for ptype in POLICY_TYPES:
            res = cli.run(
                "organizations",
                "list-policies-for-target",
                "--target-id",
                node_id,
                "--filter",
                ptype,
                "--query",
                "Policies[].[Id,Name]",
                "--output",
                "text",
            )
            for line in res.text.splitlines():
                f = line.split("\t")
                if len(f) < 2 or not f[0]:
                    continue
                pid, pname = f[0], f[1]
                if pname in ("FullAWSAccess", "RCPFullAWSAccess"):
                    continue
                if pname.startswith("aws-guardrails-"):  # Control Tower's own - never ours
                    continue
                targets.append((node_class, node_name, node_id, ptype, pid, pname))

    if root_id:
        collect_target("ROOT", root_name, root_id)
        # breadth-first: `Sandboxes` is at depth 2, and a walk written for depth 1 misses it
        # silently - the same nesting the delegation's Resource list has to survive.
        ous: list = []
        queue = deque([root_id])
        while queue:
            parent_id = queue.popleft()
            res = cli.run(
                "organizations",
                "list-organizational-units-for-parent",
                "--parent-id",
                parent_id,
                "--query",
                "OrganizationalUnits[].[Name,Id]",
                "--output",
                "text",
            )
            for line in res.text.splitlines():
                f = line.split("\t")
                if len(f) < 2 or not f[1]:
                    continue
                ous.append((f[0], f[1]))
                queue.append(f[1])
        for ou_name, ou_id in ous:
            collect_target("OU", ou_name, ou_id)

    # ------------------------------------------------------------- decompose the delegation
    dec: dict = {}
    if respol_state == "present":
        try:
            dec = decompose(json.loads(respol_content), org_id, root_id, caller_acct)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            cli.errors.entries.append(f"decomposing the resource policy\n    {e}")
            respol_state = "unparseable"

    def jq(key: str) -> str:
        """The shell's jq_ helper: JSON for lists/dicts, plain str otherwise."""
        v = dec.get(key)
        if isinstance(v, (list, dict)):
            return json.dumps(v)
        return str(v)

    # ------------------------------------------------------------------------------- checks
    if respol_state == "absent":
        checks.note(
            "DEL-1",
            "an organization resource policy exists",
            "NO - ResourcePolicyNotFoundException. This is the EXPECTED answer "
            "before Stage 2 step 5.1, and it is NOT a denial: the call was "
            "authorized and returned 'there is none'. Every check below is vacuous "
            "until it runs.",
        )
    elif respol_state == "denied":
        checks.fail(
            "DEL-1",
            "an organization resource policy exists",
            "UNKNOWN - the READ itself was refused, so this run cannot tell 'no "
            "delegation' from 'a delegation this account may not see'. Re-run from "
            "CloudShell on Management: python3 aws/org-delegation.py -",
        )
    elif respol_state == "present":
        checks.ok(
            "DEL-1",
            "an organization resource policy exists",
            f"yes - {jq('n_statements')} statement(s); the document is in section 2",
        )
    elif respol_state == "unparseable":
        checks.fail(
            "DEL-1",
            "an organization resource policy exists",
            "a document was returned and did not parse as JSON - see section 6",
        )
    else:
        checks.fail(
            "DEL-1",
            "an organization resource policy exists",
            "the call failed for a reason that is neither 'not found' nor a denial - see section 6",
        )

    if respol_state == "present":
        if dec["wildcard_principal"]:
            checks.fail(
                "DEL-2",
                "the principal is this account, not everyone",
                'Principal is "*" - every account in the organization can manage '
                "every policy in it, including Control Tower's own guardrails. This "
                "is wider than Stage 2 step 5.1 designs and wider than INT-20 "
                "accepts.",
            )
        elif dec["identity_named"]:
            checks.ok(
                "DEL-2",
                "the principal is this account, not everyone",
                "the calling account is named in the Principal",
            )
        else:
            checks.fail(
                "DEL-2",
                "the principal is this account, not everyone",
                f"the calling account is NOT in the Principal: {jq('principals')}. "
                "Either this run is in the wrong account, or the delegation was "
                "written for a different one.",
            )

        if not dec["write_missing"]:
            checks.ok(
                "DEL-3",
                "the write half is granted",
                "Create/Update/Delete/Attach/DetachPolicy all covered",
            )
        else:
            checks.fail(
                "DEL-3",
                "the write half is granted",
                f"missing: {jq('write_missing')}. terraform apply against "
                "identity/org-policies/ fails on the first of these it needs.",
            )

        if not dec["read_missing"]:
            checks.ok(
                "DEL-4",
                "the read half is granted",
                "every list/describe Stage 2 step 5.1 names is covered",
            )
        else:
            checks.note(
                "DEL-4",
                "the read half is granted",
                f"missing from the delegation: {jq('read_missing')} - which may "
                "still WORK, because a delegated administrator for any service may "
                "read the organization anyway (see section 4). Grant them "
                "regardless: relying on the other delegation makes this one's "
                "scope a fiction.",
            )

        if not dec["forbidden_granted"]:
            checks.ok(
                "DEL-5", "EnablePolicyType/DisablePolicyType are NOT granted", "correctly absent"
            )
        else:
            checks.fail(
                "DEL-5",
                "EnablePolicyType/DisablePolicyType are NOT granted",
                f"granted: {jq('forbidden_granted')}. Disabling a policy type on "
                "the root DETACHES EVERY POLICY OF THAT TYPE AT ONCE. Nothing in "
                "this design needs it after 1c step 7.2.",
            )

        if dec["root_covered"]:
            checks.ok(
                "DEL-6",
                "the Resource list reaches the ROOT",
                "yes - and this is the one that decides the size of Stage 2: six of "
                "the ten documents are attached to the root",
            )
        else:
            checks.fail(
                "DEL-6",
                "the Resource list reaches the ROOT",
                f"NO. The root ARN (root/{org_id}/{root_id}) is not covered by: "
                f"{jq('resources')}. Six of the ten attached documents are on the "
                "root, so identity/org-policies/ can hold at most the four per-OU "
                "ones. This is INT-20's predicted outcome, not a mistake to fix by "
                "widening blindly.",
            )

        if dec["ou_wildcard"]:
            checks.ok(
                "DEL-7",
                "the Resource list reaches NESTED OUs",
                "a wildcard OU ARN is present, so depth 2 (Sandboxes under Interactive) is covered",
            )
        else:
            checks.fail(
                "DEL-7",
                "the Resource list reaches NESTED OUs",
                "no wildcard OU ARN. AWS documents that naming a single OU "
                "'excludes child OUs and accounts under child OUs', and this "
                "organization is two levels deep (D23). Named OUs: "
                f"{jq('ou_single_named')}",
            )

        pt = jq("policy_type_conditions")
        ptop = jq("policy_type_operators")
        ptstrict = jq("policy_type_operators_strict")
        if pt == "[]":
            checks.note(
                "DEL-8",
                "scoped by organizations:PolicyType, via IfExists",
                "no PolicyType condition - the delegation admits EVERY policy "
                "type, present and future. Wider than Stage 2 step 5.1 designs, "
                "and it is a Deny-by-omission that will not announce itself.",
            )
        elif ptstrict != "[]":
            checks.fail(
                "DEL-8",
                "scoped by organizations:PolicyType, via IfExists",
                f"types {pt}, but the operator is {ptstrict} - NOT an IfExists "
                "form. A strict operator denies every call whose request context "
                "omits organizations:PolicyType, and not every write supplies it. "
                "The result is 'all writes refused', which is indistinguishable at "
                "the keyboard from a delegation that cannot reach a root "
                "attachment - DEL-6's failing answer. Use StringLikeIfExists "
                "(Stage 2 step 5.1). Until this is fixed, do not read a denied "
                "write as scope.",
            )
        else:
            checks.ok(
                "DEL-8",
                "scoped by organizations:PolicyType, via IfExists",
                f"{pt}, via {ptop} - the IfExists form, so a call that does not "
                "carry the key is not denied by this condition",
            )

        if not dec["policy_types_missing"]:
            checks.ok(
                "DEL-9",
                "the Resource list carries the POLICY-type ARNs",
                "all four types covered. Create/Update/DeletePolicy authorize "
                "against the policy ARN, Attach/DetachPolicy against target AND "
                "policy.",
            )
        else:
            checks.fail(
                "DEL-9",
                "the Resource list carries the POLICY-type ARNs",
                f"missing: {jq('policy_types_missing')}. A target-only Resource "
                "list denies EVERY write on EVERY document - the absent class is "
                "arn:...:policy/o-<org>/<policy_type>/* - so 5.0's write test "
                "fails everywhere and reads exactly like 'the delegation cannot "
                "touch a root attachment'. Fix the delegation before reading "
                "DEL-6's answer into scope. (Added 2026-08-15; Stage 2 step 5.1.)",
            )

        # DEL-10 - the 5.1a narrowing. EXPECTED TO FAIL between 5.1's attach and 5.1a's
        # console paste: the failing answer is the true state, not a broken script.
        if not dec["write_stmts_missing_principal_arn"]:
            checks.ok(
                "DEL-10",
                "the write statements are narrowed to the InfrastructureAccess role",
                "aws:PrincipalArn condition present on every write statement "
                f"({'; '.join(dec['write_stmts_principal_arn_operators'])}). The "
                "account-wide principal no longer reaches policy writes through "
                "principals nobody chose (open question 11).",
            )
        else:
            checks.fail(
                "DEL-10",
                "the write statements are narrowed to the InfrastructureAccess role",
                f"no aws:PrincipalArn condition on: {', '.join(dec['write_stmts_missing_principal_arn'])}. "
                "Every principal in Identity holding organizations:* identity-side can "
                "write organization policies - measured 2026-08-15, the CT admin "
                "reaches them through AWSOrganizationsFullAccess. Expected until "
                "step 5.1a's console paste lands; a fail AFTER it is a regression. "
                "(Added 2026-08-15; Stage 2 step 5.1a.)",
            )

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("Can the Identity account manage the organization POLICIES - INT-20")
        rep.text(f"""generated : {context.utc_stamp()}
profile   : {cli.label}
caller    : {caller}
produced  : aws/org-delegation.py   (index: aws/INDEX.md)

SECTIONS
  1. Where this ran - read it FIRST
  2. The organization resource policy, and which of three states it is in
  3. What the delegation grants, decomposed - the checks
  4. WHAT THIS SCRIPT CANNOT ANSWER, and why a green run is not a green delegation
  5. The documents a write would have to reach, by target class
  6. Calls that failed

HOW TO READ THIS FILE
  - SECTION 4 IS NOT A DISCLAIMER, IT IS THE MAIN FINDING. Organizations READS
    already answer from the Identity account with no policy delegation at all
    (Stage 1c verification (x)), so nothing that merely reads is evidence here.
    What this script decides is SCOPE, by reading the delegation document.
  - THREE STATES, NOT TWO, in section 2. "No delegation" and "the read was denied"
    are different facts and only one of them is the expected pre-5.1 answer.
  - A `note` IN SECTION 3 BEFORE STEP 5.1 IS NOT A FAILURE. Until the delegation
    exists there is nothing to check, and the report says that rather than passing.""")

        # ==============================================================================
        rep.h1("1. Where this ran - read it FIRST")

        rep.text("""Every other section is about whatever account answered, so this is the section that
says whether the answer is about the right one. The delegation is FOR the Identity
account; a run from Management shows the same document from the side that wrote it
and always succeeds, which answers a different question.

""")

        rep.tabulate(
            [
                "FIELD\tVALUE",
                f"caller ARN\t{caller}",
                f"account id\t{caller_acct or '(unknown)'}",
                f"management account\t{mgmt_id or '(unread)'}",
                f"organization\t{org_id or '(unread)'}",
                f"root\t{root_name or '(unread)'} ({root_id})",
            ]
        )

        rep.line()
        if mgmt_id and caller_acct == mgmt_id:
            rep.text("""THIS RAN IN THE MANAGEMENT ACCOUNT. Management is outside every SCP and owns the
organization, so section 3 measures the DOCUMENT and not the reach of the delegated
administrator. Re-run as ./aws/org-delegation.py to get the answer that matters.""")
        else:
            rep.line("This ran in a member account, which is where the delegation has to work.")

        # ==============================================================================
        rep.h1("2. The organization resource policy")

        rep.line()
        rep.line("$ aws organizations describe-resource-policy")
        rep.line()

        if respol_state == "present":
            rep.line("STATE: PRESENT - a delegation exists.")
            rep.line()
            try:
                rep.line(json.dumps(json.loads(respol_content), indent=4))
            except json.JSONDecodeError:
                rep.line(respol_content)
        elif respol_state == "absent":
            rep.text(f"""STATE: ABSENT - ResourcePolicyNotFoundException.

This is the EXPECTED answer before Stage 2 step 5.1, and it is an ANSWER rather
than a failure: the call was authorized and reported that there is no such policy.
Keeping this apart from a denial is the whole reason this section prints a state
rather than an empty block - a listing that returns nothing and a listing that was
refused look identical otherwise (Lesson 13).

raw error: {head2(respol_err)}""")
        elif respol_state == "denied":
            rep.text(f"""STATE: DENIED - the READ itself was refused.

This run cannot tell "there is no delegation" from "there is one and this account
may not see it". Re-run from CloudShell on Management as AWS Control Tower Admin:
  python3 aws/org-delegation.py -

raw error: {head2(respol_err)}""")
        else:
            rep.text(f"""STATE: {respol_state.upper()} - see section 6.

raw error: {head2(respol_err)}""")

        # ==============================================================================
        rep.h1("3. What the delegation grants, decomposed")

        rep.text("""Reading the document is the instrument, because the principal that would exercise it
is the one running Terraform and attempting the call is a write (Lesson 22). Each
check below is a place the delegation fails SILENTLY - it attaches, it looks right,
and the apply is refused on the one document nobody tested.

""")

        rep.checks_table(checks)
        rep.line()
        rep.line(f"{checks.n_fail()} check(s) FAILED.")

        if respol_state == "present":
            rep.line()
            rep.line("The raw decomposition, so any row above can be re-derived:")
            rep.line()
            rep.raw(json.dumps(dec, indent=2, sort_keys=True))

        # ==============================================================================
        rep.h1("4. WHAT THIS SCRIPT CANNOT ANSWER")

        rep.text("""TWO THINGS, AND THE FIRST IS THE REASON THE SECOND MATTERS.

1. A SUCCESSFUL READ IS NOT EVIDENCE OF THIS DELEGATION. Organizations reads already
   answer from the Identity account without any policy delegation - measured in Stage
   1b step 4 and Stage 1c verification (x), because a delegated administrator for ANY
   service may read the organization. ./aws/org-policies.py runs green from here today
   and always has. So `describe-policy` succeeding proves nothing, and a script built
   on it would return OK before AND after step 5.1 - which is not a verification
   (Lesson 13). That is why section 3 reads the delegation document instead.

2. THE DECISIVE TEST IS A WRITE, AND IT IS NOT PERFORMED HERE. Stage 2 step 5.0 names
   it precisely: `organizations update-policy` against `awsds-org-tag-policy` with its
   own current content - the least dangerous document in the organization, because its
   enforcement is off (`enforced_for` unset), so an identical rewrite changes nothing
   even if it lands somewhere nobody expected. NOT the baseline SCP. That call belongs
   to a human, for the same reason aws/probes/ is fenced off from the rest of aws/: a
   measurement that can change a policy is run deliberately, not to gather information.

WHAT A FAILED DEL-6 MEANS, since it is the outcome INT-20 predicts. It does not mean
the delegation is broken. It means terraform-live/identity/org-policies/ holds the four
per-OU documents and the six on the root stay console-managed - Stage 2 step 5.0 records
that as a scope decision rather than as a defect, and step 9.2 keeps all ten in scope by
reading policies/*.json regardless of who manages them.

AND ONE FALSE READING OF IT: a Resource list of TARGETS ALONE - no policy/ ARNs -
denies every write on every document, which at the keyboard reads exactly like "all
refused". Read DEL-9 before reading a denied write as DEL-6's answer.""")

        # ==============================================================================
        rep.h1("5. The documents a write would have to reach")

        rep.text("""This project`s documents only - Control Tower`s aws-guardrails-* are filtered out,
and so are FullAWSAccess and RCPFullAWSAccess. THE CLASS COLUMN IS THE POINT: ROOT
rows are the ones DEL-6 decides, OU rows the ones DEL-7 decides.

""")

        if targets:
            rows = ["CLASS\tNODE\tNODE ID\tTYPE\tPOLICY ID\tPOLICY NAME"]
            rows += sorted("\t".join(t) for t in targets)
            rep.tabulate(rows)
            rep.line()
            n_root = sum(1 for t in targets if t[0] == "ROOT")
            n_ou = sum(1 for t in targets if t[0] == "OU")
            rep.line(f"{n_root} document(s) on the ROOT, {n_ou} on an OU.")
            rep.line(
                "Expected shape as of 2026-08-15: 6 on the root, 4 on OUs (docs/AWS_STATE.md)."
            )
        else:
            rep.line("(nothing found - see section 6)")

        # ==============================================================================
        rep.h1("6. Calls that failed")

        if cli.errors:
            rep.line(cli.errors.text())
            rep.text("""
If these are AccessDenied, retry from CloudShell on Management as
`AWS Control Tower Admin`:  python3 aws/org-delegation.py -""")
        else:
            rep.line("None. Every call returned successfully.")
            rep.line("(Section 2 reporting ABSENT is not a failure - it is that call answering.)")

        rep.line()
        rep.line("Regenerate with:  ./aws/org-delegation.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if cli.errors:
        note(f"wrote {out_label} (some calls FAILED - see section 6)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 3)")
        return 2
    if respol_state == "absent":
        note(f"wrote {out_label} (NO DELEGATION YET - expected before Stage 2 step 5.1)")
        return 0
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
