"""A deployment target's values, each read from the slice that owns it: what the promotion's scripts
name in an account (scripts/render-workflow.py, scripts/model-chain.py). The states are read as the
caller's AWS profile (tfhygiene.states): on the deploy runner the deploy role, whose state_read_keys
name the data, sagemaker and network slices; by hand the account's infrastructure profile.
"""

from __future__ import annotations

from tfhygiene import backend
from tfhygiene.states import state_outputs

# The slice that owns the account's private subnets: Staging's single VPC, Production's VPC-Workloads.
NETWORK_SLICE = {"staging": "foundation", "production": "workloads"}

# The slice whose outputs name another account's Model Registry: Staging's foundation/, where the
# deploy role's grant on Production's groups is written (Stage 9 4.6). Production owns its registry,
# read from its own sagemaker/ outputs.
REGISTRY_SLICE = {"staging": "foundation"}


class TargetError(Exception):
    pass


def account_values(account: str) -> dict:
    """The account's names: its env token and Region, the outputs bucket and the data key, the job
    role, its security group and subnets, the training image when sagemaker/ outputs one, and the
    prefix of another account's registry group ARNs when the account reads one."""
    if account not in NETWORK_SLICE:
        raise TargetError(f"{account}: not a deployment target ({', '.join(NETWORK_SLICE)})")
    data = state_outputs(account, "data")
    sagemaker = state_outputs(account, "sagemaker")
    network = state_outputs(account, NETWORK_SLICE[account])
    registry = state_outputs(account, REGISTRY_SLICE[account]) if account in REGISTRY_SLICE else {}
    subnets = network["private_subnet_ids"]
    return {
        "env": backend.ENV_TOKENS[account],
        "region": backend.REGION,
        "bucket": data["outputs_bucket_name"],
        "data_key_arn": data["data_key_arn"],
        "job_role_arn": sagemaker["job_role_arn"],
        "security_group": sagemaker["job_security_group_id"],
        "subnets": [subnets[z] for z in backend.ZONE_IDS[account]],
        "training_image_uri": sagemaker.get("training_image_uri"),
        "model_package_group_arns": sagemaker.get("model_package_group_arns") or {},
        "registry_group_arn_prefix": registry.get("registry_model_package_group_arn_prefix"),
    }
