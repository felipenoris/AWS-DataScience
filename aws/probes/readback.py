#!/usr/bin/env python3
"""Compare the SCPs attached in the organization against the documents in policies/.

    readback.py <policy-dir> <profile>

Run by scp-battery.sh before a single probe fires, and answering one question: is the thing
about to be measured the thing in the repository? Every amendment this project has made was
uploaded by hand into a console, and a battery run against the previous content is
indistinguishable from a battery run against the current one - it passes, and it proves the
old ceiling. Reads only; needs the Identity profile, where Organizations reads answer.

It compares Sids in order and the total action count, not the whole document: the rendered
copy carries substituted ids the template still holds as placeholders, so a byte comparison
would report a difference on every run and be ignored by the second week.
"""

import glob
import json
import os
import subprocess
import sys


def aws_json(args, profile):
    out = subprocess.run(["aws", *args, "--profile", profile, "--output", "json"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        return None, out.stderr.strip().splitlines()[-1] if out.stderr else "failed"
    return json.loads(out.stdout), None


def counts(doc):
    sids = [s["Sid"] for s in doc["Statement"]]
    actions = sum(len(s["Action"]) if isinstance(s["Action"], list) else 1
                  for s in doc["Statement"])
    return sids, actions


def main():
    policy_dir, profile = sys.argv[1], sys.argv[2]

    listing, err = aws_json(["organizations", "list-policies",
                             "--filter", "SERVICE_CONTROL_POLICY"], profile)
    if listing is None:
        print(f"     ??   could not list policies: {err}")
        return 1

    deployed = {p["Name"]: p["Id"] for p in listing["Policies"]}
    drift = 0

    for path in sorted(glob.glob(os.path.join(policy_dir, "*.json"))):
        name = os.path.basename(path)[:-5]
        if name not in deployed:
            print(f"     --   {name}: no policy of that name in the organization")
            continue

        pid = deployed[name]
        live_raw, err = aws_json(["organizations", "describe-policy", "--policy-id", pid],
                                 profile)
        if live_raw is None:
            print(f"     ??   {name} ({pid}): {err}")
            drift += 1
            continue

        live_sids, live_actions = counts(json.loads(live_raw["Policy"]["Content"]))
        repo_sids, repo_actions = counts(json.load(open(path)))

        if live_sids == repo_sids and live_actions == repo_actions:
            print(f"     ok   {name} ({pid}): {len(live_sids)} statements, {live_actions} actions")
            continue

        drift += 1
        print(f"     DIFF {name} ({pid}): attached {len(live_sids)} stmt / {live_actions} act, "
              f"repository {len(repo_sids)} stmt / {repo_actions} act")
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


if __name__ == "__main__":
    sys.exit(main())
