#!/usr/bin/env -S uv run --quiet
# One login covers every profile on the `awsds` sso-session (aws/AWS-CLI.md, "Signing in").
from __future__ import annotations

import subprocess
import sys

sys.exit(subprocess.call(["aws", "sso", "login", "--sso-session", "awsds"]))
