"""The house image's recipe, read out of this repository's copy of the GitLab project that holds it.

The recipe's source of truth is the private GitLab's `awsds/dev-env` (Stage 8 decision 16), and this
repository keeps a copy of its last commit under gitlab/, written by scripts/gitlab-mirror.py. Every
reader of the recipe here reads that copy through these paths, so the copy's location is spelled once.

Two values in it are generated or declared elsewhere in the estate, and both readers compare them:
the NO_PROXY literal in the Dockerfile against `<account>/egress`'s `no_proxy_all_groups`, and the
Bedrock pins in the managed settings against the SCP and the grant slice (awslib.bedrockscope).
"""

from __future__ import annotations

import hashlib
import re

MIRROR = "gitlab/awsds/dev-env"
DOCKERFILE = f"{MIRROR}/dev-env/Dockerfile"
SETTINGS = f"{MIRROR}/dev-env/claude-code/managed-settings.json"
MIRROR_RECORD = "gitlab/mirror.json"
MIRROR_PROJECT = "awsds/dev-env"

# The proxy URL's other tracked copy (Lesson 33): nothing keeps the two equal but a reader.
PROBES_VARIABLES = "terraform-live/sandbox/probes/variables.tf"

# The egress slice's two lists: every optional group's names, the authority the literal must equal;
# and the last apply's, which is context.
FULL_OUTPUT = "no_proxy_all_groups"
APPLIED_OUTPUT = "no_proxy"

ARG_LIST_RE = re.compile(r'^ARG NO_PROXY_LIST="(?P<value>[^"]*)"\s*$', re.M)
ARG_PROXY_RE = re.compile(r"^ARG PROXY_URL=(?P<value>\S+)\s*$", re.M)
PROBES_PROXY_RE = re.compile(r'default\s*=\s*"(?P<value>http://proxy\.[^"]+)"')


def digest(value: str) -> str:
    """The first 16 hex of the list's sha256 - what the image writes to /opt/awsds-proxy.txt."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def entries(value: str) -> list:
    """The list as names. Empty in, empty out - never a list holding one empty string."""
    return [item for item in value.split(",") if item]
