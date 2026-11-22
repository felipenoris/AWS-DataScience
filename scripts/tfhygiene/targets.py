"""A deployment target's values, each read from the slice that owns it: what the model chain names in
an account (scripts/model-chain.py) beside its deployment project's (tfhygiene.projects). The states
are read as the caller's AWS profile (tfhygiene.states): on the deploy runner the deploy role, whose
state_read_keys name the sagemaker and foundation slices; by hand the account's infrastructure
profile.
"""

from __future__ import annotations

from tfhygiene import backend
from tfhygiene.states import state_outputs

TARGETS = ("staging", "production")

# The slice whose outputs name another account's Model Registry: Staging's foundation/, where the
# deploy role's grant on Production's groups is written (Stage 9 4.6). Production owns its registry,
# read from its own sagemaker/ outputs.
REGISTRY_SLICE = {"staging": "foundation"}


class TargetError(Exception):
    pass


def account_values(account: str) -> dict:
    """The account's names: its env token and Region, its own registry groups, and the prefix of
    another account's registry group ARNs when the account reads one."""
    if account not in TARGETS:
        raise TargetError(f"{account}: not a deployment target ({', '.join(TARGETS)})")
    sagemaker = state_outputs(account, "sagemaker")
    registry = state_outputs(account, REGISTRY_SLICE[account]) if account in REGISTRY_SLICE else {}
    return {
        "env": backend.ENV_TOKENS[account],
        "region": backend.REGION,
        "model_package_group_arns": sagemaker.get("model_package_group_arns") or {},
        "registry_group_arn_prefix": registry.get("registry_model_package_group_arn_prefix"),
    }
