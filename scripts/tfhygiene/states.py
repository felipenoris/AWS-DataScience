"""A slice's state, read from its state object - the deploy jobs' way to every account value.

The state is read as the caller's AWS profile through the aws CLI, the repository's one dependency
(pyproject.toml): on the deploy runner the deploy role, whose state_read_keys name the slices an
application reads (Stage 8 step 4.1); by hand the account's infrastructure profile.
"""

from __future__ import annotations

import json
import subprocess

from tfhygiene import backend


class StateError(Exception):
    pass


def state_document(account: str, slice_name: str) -> dict:
    """The state object of terraform-live/<account>/<slice_name>/, parsed: outputs and resources."""
    env = backend.ENV_TOKENS[account]
    uri = f"s3://awsds-{env}-tfstate/{account}/{slice_name}/terraform.tfstate"
    res = subprocess.run(
        ["aws", "s3", "cp", uri, "-", "--only-show-errors"],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise StateError(f"{uri}: {res.stderr.strip() or 'unreadable'}")
    return json.loads(res.stdout)


def state_outputs(account: str, slice_name: str) -> dict:
    """The outputs of terraform-live/<account>/<slice_name>/, as {name: value}."""
    return {
        k: v["value"] for k, v in state_document(account, slice_name).get("outputs", {}).items()
    }
