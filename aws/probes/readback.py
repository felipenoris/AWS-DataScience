#!/usr/bin/env -S uv run --quiet
"""Compare the policies attached in the organization against the documents in policies/.

    readback.py <policy-dir> <profile>

Run by scp-battery.py before a single probe fires, and answering one question: is the thing
about to be measured the thing in the repository? Every amendment this project has made was
uploaded by hand into a console, and a battery run against the previous content is
indistinguishable from a battery run against the current one - it passes, and it proves the
old ceiling. Reads only; needs the Identity profile, where Organizations reads answer.

It compares entries in order and the total action count, not the whole document: the rendered
copy carries substituted ids the template still holds as placeholders, so a byte comparison
would report a difference on every run and be ignored by the second week.

FOUR POLICY TYPES SINCE 7.8, and the type is derived from the DOCUMENT rather than from the
filename. A `list-policies` call takes exactly one --filter, so a version that listed only
SERVICE_CONTROL_POLICY reported every RCP, tag policy and declarative policy as "no policy of
that name in the organization" - which is indistinguishable from "not attached yet" and stays
that way forever after it is attached. That is a read-back that reassures without measuring.
"""

import glob
import json
import os
import subprocess
import sys

# The one place the four types are enumerated. `list-policies` accepts a single --filter, so
# this is also the list of calls made.
POLICY_TYPES = [
    "SERVICE_CONTROL_POLICY",
    "RESOURCE_CONTROL_POLICY",
    "TAG_POLICY",
    "DECLARATIVE_POLICY_EC2",
]


def aws_json(args, profile):
    out = subprocess.run(
        ["aws", *args, "--profile", profile, "--output", "json"], capture_output=True, text=True
    )
    if out.returncode != 0:
        return None, out.stderr.strip().splitlines()[-1] if out.stderr else "failed"
    return json.loads(out.stdout), None


def kind(doc):
    """The policy TYPE, read off the document's shape.

    An RCP is an SCP that carries `Principal` - that element is mandatory in an RCP and
    forbidden in an SCP, which makes it the discriminator rather than a heuristic.
    """
    if "Statement" in doc:
        if any("Principal" in s for s in doc["Statement"]):
            return "RESOURCE_CONTROL_POLICY"
        return "SERVICE_CONTROL_POLICY"
    if "tags" in doc:
        return "TAG_POLICY"
    if "ec2_attributes" in doc:
        return "DECLARATIVE_POLICY_EC2"
    return None


def counts(doc):
    """(entries, weight) - what plays the part of a Sid, and a second number that changes
    when a statement is edited without being renamed. For the two management-policy types
    there is no action list, so the weight is the number of leaf settings."""
    if "Statement" in doc:
        sids = [s["Sid"] for s in doc["Statement"]]
        actions = sum(
            len(s["Action"]) if isinstance(s["Action"], list) else 1 for s in doc["Statement"]
        )
        return sids, actions
    if "tags" in doc:
        keys = [v["tag_key"]["@@assign"] for v in doc["tags"].values()]
        values = sum(len(v.get("tag_value", {}).get("@@assign", [])) for v in doc["tags"].values())
        return keys, values
    if "ec2_attributes" in doc:
        attrs = list(doc["ec2_attributes"].keys())
        leaves = sum(len(v) if isinstance(v, dict) else 1 for v in doc["ec2_attributes"].values())
        return attrs, leaves
    raise SystemExit("unrecognised policy document - teach readback.py its shape")


def run(policy_dir, profile):
    """The comparison, importable by scp-battery.py (which used to shell out to this
    file); `main()` below keeps the standalone command-line form working."""
    # name -> (id, type). Built from all four listings, because a document's type is not
    # knowable from its name and a missing listing reads exactly like a missing policy.
    deployed = {}
    for ptype in POLICY_TYPES:
        listing, err = aws_json(["organizations", "list-policies", "--filter", ptype], profile)
        if listing is None:
            print(f"     ??   could not list {ptype}: {err}")
            print("          every document of that type below reads as 'not attached'.")
            continue
        for p in listing["Policies"]:
            deployed[p["Name"]] = (p["Id"], ptype)

    drift = 0

    for path in sorted(glob.glob(os.path.join(policy_dir, "*.json"))):
        name = os.path.basename(path)[:-5]
        repo_doc = json.load(open(path))
        repo_kind = kind(repo_doc)
        if repo_kind is None:
            print(f"     ??   {name}: unrecognised document shape - not compared")
            drift += 1
            continue

        if name not in deployed:
            print(f"     --   {name} ({repo_kind}): no policy of that name in the organization")
            continue

        pid, live_kind = deployed[name]

        # A name reused across types would compare a document against something that is not
        # it, and the comparison could still pass on counts alone.
        if live_kind != repo_kind:
            drift += 1
            print(
                f"     DIFF {name} ({pid}): attached as {live_kind}, "
                f"repository document is a {repo_kind}"
            )
            continue

        live_raw, err = aws_json(["organizations", "describe-policy", "--policy-id", pid], profile)
        if live_raw is None:
            print(f"     ??   {name} ({pid}): {err}")
            drift += 1
            continue

        live_sids, live_actions = counts(json.loads(live_raw["Policy"]["Content"]))
        repo_sids, repo_actions = counts(repo_doc)

        unit = "statements" if "Statement" in repo_doc else "entries"
        if live_sids == repo_sids and live_actions == repo_actions:
            print(f"     ok   {name} ({pid}): {len(live_sids)} {unit}, {live_actions} leaves")
            continue

        drift += 1
        print(
            f"     DIFF {name} ({pid}): attached {len(live_sids)} {unit} / {live_actions} leaves, "
            f"repository {len(repo_sids)} / {repo_actions}"
        )
        for s in repo_sids:
            if s not in live_sids:
                print(f"            in the repository, NOT attached: {s}")
        for s in live_sids:
            if s not in repo_sids:
                print(f"            attached, NOT in the repository: {s}")

    if drift:
        print()
        print("     ^ the probes below measure what is ATTACHED. Upload first, or read every")
        print("       result as a statement about the older content.")
    return 0


def main():
    return run(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    sys.exit(main())
