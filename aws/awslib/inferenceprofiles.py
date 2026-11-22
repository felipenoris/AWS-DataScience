"""Amazon Bedrock inference profiles, read by type, and what an application profile copies.

``ListInferenceProfiles`` with no ``typeEquals`` returns the system-defined profiles alone: measured
2026-10-19 in Sandbox, 96 of 96 ``SYSTEM_DEFINED`` while the account held two application profiles.
The API reference names both types and no default, so each type is asked for by name.

An application profile lists the model it reaches in each Region, not what it was created from. The
console copies a system-defined profile or a model into one, so the source is read back as the
system-defined profile listing exactly the same model ARNs, or as the model when the profile lists
this Region alone. No profile id is written here: the console mints them.
"""

from __future__ import annotations

import json
from collections import defaultdict

from . import context
from .awscli import AwsCli

TYPES = ("APPLICATION", "SYSTEM_DEFINED")


def listing_args(kind: str) -> tuple:
    """The CLI arguments that list one type: each profile's id, status and model ARNs."""
    return (
        "bedrock",
        "list-inference-profiles",
        "--type-equals",
        kind,
        "--query",
        "inferenceProfileSummaries[].[inferenceProfileId,status,models[].modelArn]",
        "--output",
        "json",
    )


def listing(cli: AwsCli, kind: str) -> dict | None:
    """Profile id -> (status, model ARNs) for one type, or None when the call failed."""
    res = cli.run(*listing_args(kind))
    if not res.ok:
        return None
    rows = json.loads(res.stdout or "[]") or []
    return {pid: (status, frozenset(arns or ())) for pid, status, arns in rows}


def by_model_arns(systems: dict) -> dict:
    """Model ARNs -> the ids of the system-defined profiles listing exactly them."""
    index: dict = defaultdict(set)
    for pid, (_status, arns) in systems.items():
        index[arns].add(pid)
    return index


def source(arns: frozenset, index: dict) -> tuple[str | None, str | None, str]:
    """(the model, what the profile copies, what it lists) for an application profile.

    The model is None when the profile reaches more than one, and what it copies is None when its
    model ARNs match neither one system-defined profile nor the model in this Region alone.
    """
    models = sorted({arn.rsplit("/", 1)[-1] for arn in arns})
    if len(models) != 1:
        return None, None, f"lists {len(models)} models: {', '.join(models)}"
    model = models[0]
    copied = sorted(index.get(arns, ()))
    if len(copied) == 1:
        return model, copied[0], f"lists the model ARNs of {copied[0]}"
    if copied:
        return model, None, f"lists the model ARNs of {' and '.join(copied)}, more than one profile"
    if arns == {f"arn:aws:bedrock:{context.REGION}::foundation-model/{model}"}:
        return model, model, f"lists {model} in {context.REGION} alone"
    regions = sorted(arn.split(":")[3] or "no Region" for arn in arns)
    return model, None, f"lists {model} in {', '.join(regions)}, as no system-defined profile does"
