#!/usr/bin/env -S uv run --quiet
"""login.py - the SSO login of the `awsds` sso-session, the infrastructure user's. One login covers
every profile on that session (aws/AWS-CLI.md, "Signing in").

run:      ./aws/login.py
calls:    aws sso login --sso-session awsds --no-browser. The CLI prints the URL and the code,
          and the URL goes to another browser or a private window.
"""

from __future__ import annotations

import subprocess
import sys

from awslib import cmdline

cmdline.check(sys.argv[1:], __doc__, positional=False)
sys.exit(subprocess.call(["aws", "sso", "login", "--sso-session", "awsds", "--no-browser"]))
