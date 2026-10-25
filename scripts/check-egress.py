#!/usr/bin/env -S uv run --quiet
# check-egress.py - Stage 8 steps 3.1 and 3.6 (decision 27): whether an account's egress slice is up,
# read before a promotion leg writes anything.
#
#   run:      ./scripts/check-egress.py <account-folder> <slice>
#             ./scripts/check-egress.py staging egress                 # staging-check, as awsds-deploy-staging
#             ./scripts/check-egress.py production workloads-egress    # production-deploy, as awsds-deploy-prod
#   reads:    the slice's state object (the output interface_endpoint_ids and the DNS Firewall
#             association it holds), ec2:DescribeVpcEndpoints on those ids and
#             route53resolver:GetFirewallRuleGroupAssociation on that association, all as AWS_PROFILE.
#             Nothing is created, changed or destroyed.
#   exit:     0 up | 1 down, or partly up | 2 a call failed
#
# The pipeline raises and destroys no shared slice: every egress slice is the user's `make up` /
# `make down`, in every account (Stage 8 decision 27, 2026-10-24). A leg that started with the slice down
# would fail minutes later, in a worker at the firewall (`errno 16`, 6i), so the leg asks first, and the
# answer is read from the state the user's apply wrote: a slice that is down holds no endpoint in its
# state, and a slice that is up has every endpoint `available` and its firewall association `COMPLETE`.
# The state is read rather than the VPC listed because a listing would need a copy of the slice's
# service list here (Lesson 51), and the state is what the apply declared. A state the role cannot read
# is exit 2 with the refusal's text, never "down" (Lesson 62).

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tfhygiene import backend
from tfhygiene.states import StateError, state_document

FIREWALL_ASSOCIATION = "aws_route53_resolver_firewall_rule_group_association"


class CallError(Exception):
    pass


def aws_json(*args: str) -> dict:
    res = subprocess.run(["aws", *args, "--output", "json"], capture_output=True, text=True)
    if res.returncode != 0:
        raise CallError(f"aws {' '.join(args[:2])}: {res.stderr.strip() or 'failed'}")
    return json.loads(res.stdout)


def raise_hint(account: str, slice_name: str) -> str:
    """The command and the identity that raise the slice, printed with every refusal."""
    return (
        f"run `make up ENV={account} ONLY={slice_name}` from the project folder as the infrastructure "
        f"user (profile {backend.profile(account)}: account {account.capitalize()}, permission set "
        "InfrastructureAccess), then retry this job"
    )


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])
    if len(argv) != 2:
        print("usage: check-egress.py <account-folder> <slice>", file=sys.stderr)
        return 2
    account, slice_name = argv
    if account not in backend.ENV_TOKENS:
        print(f"unknown account folder '{account}'", file=sys.stderr)
        return 2
    hint = raise_hint(account, slice_name)

    try:
        state = state_document(account, slice_name)
    except StateError as e:
        print(f"FATAL: {account}/{slice_name}/'s state could not be read: {e}")
        return 2

    ids = state.get("outputs", {}).get("interface_endpoint_ids", {}).get("value") or {}
    if not ids:
        print(
            f"FATAL: {account}/{slice_name}/ is down: its state holds no interface endpoint; {hint}"
        )
        return 1

    try:
        endpoints = aws_json("ec2", "describe-vpc-endpoints", "--vpc-endpoint-ids", *ids.values())
    except CallError as e:
        if "InvalidVpcEndpointId.NotFound" in str(e):
            print(
                f"FATAL: {account}/{slice_name}/ is down: an endpoint its state names is gone; {hint}"
            )
            return 1
        print(f"FATAL: {e}")
        return 2
    states = {ep["VpcEndpointId"]: ep["State"] for ep in endpoints.get("VpcEndpoints", [])}
    print(f"== {account}/{slice_name}/: the interface endpoints its state holds")
    not_up = []
    for service, endpoint_id in sorted(ids.items()):
        state_of = states.get(endpoint_id, "absent")
        print(f"  {service:<16} {endpoint_id}  {state_of}")
        if state_of != "available":
            not_up.append(service)

    # The association is read from the state's resources, not from an output: the module exports no id
    # on purpose (its outputs.tf), and a slice without the firewall declares no such resource.
    associations = [
        inst["attributes"]["id"]
        for r in state.get("resources", [])
        if r.get("type") == FIREWALL_ASSOCIATION
        for inst in r.get("instances", [])
    ]
    if not associations:
        print("  no DNS Firewall association in the state: the slice declares none")
    for association_id in associations:
        try:
            got = aws_json(
                "route53resolver",
                "get-firewall-rule-group-association",
                "--firewall-rule-group-association-id",
                association_id,
            )
        except CallError as e:
            if "ResourceNotFoundException" in str(e):
                print(f"  DNS Firewall association {association_id}  gone")
                not_up.append("dns-firewall")
                continue
            print(f"FATAL: {e}")
            return 2
        status = got["FirewallRuleGroupAssociation"]["Status"]
        print(f"  DNS Firewall association {association_id}  {status}")
        if status != "COMPLETE":
            not_up.append("dns-firewall")

    if not_up:
        print(f"FATAL: {account}/{slice_name}/ is partly up ({', '.join(not_up)}); {hint}")
        return 1
    firewall = (
        f" and {len(associations)} DNS Firewall association(s) COMPLETE" if associations else ""
    )
    print(
        f"ok: {account}/{slice_name}/ is up: {len(ids)} interface endpoint(s) available{firewall}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
