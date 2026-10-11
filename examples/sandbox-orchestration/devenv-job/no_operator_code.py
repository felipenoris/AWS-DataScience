"""Placeholder operator file for demo-devenv-job, which runs no Python or Bash task.

The portal sends a code location on every save, `dev/operatorFiles/<workflow name>.zip`, and
the service refuses the save when no object is there (measured 2026-10-10: "Code not found in
specified S3 location"). Uploading this file in Settings -> Storage is what puts one there.
Nothing imports it.
"""
