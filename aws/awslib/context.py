"""Where a script is running, and where its report goes.

The snapshot scripts have two homes. Normally they run from a clone of this repository and
write to ``aws/output/`` (untracked). The ``-`` fallback runs them in CloudShell, which may
hold only the ``aws/`` folder - so the repository root is *located* rather than assumed, and
when there is none the report lands beside the script, where the operator can download it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# The three constants every script in aws/ shares. The region is the one deliberate literal:
# these scripts REPORT on infrastructure and are not infrastructure code, so the "region is a
# variable" rule for .tf files (docs/plan/architecture.md) does not reach them - same as the
# shell versions, which carried REGION="us-west-2" at the top of every file.
REGION = "us-west-2"
SSO_SESSION = "awsds"
PROFILE_PREFIX = "awsds-"

# The marker that identifies the repository root. CLAUDE.md sits only there, which is what
# the shell versions tested with `[ -f "$SCRIPT_DIR/../CLAUDE.md" ]`.
_ROOT_MARKER = "CLAUDE.md"


@dataclass(frozen=True)
class Context:
    """Resolved location of one script run."""

    script_dir: Path
    repo_root: Path  # the script's own folder when standalone (CloudShell)
    out_dir: Path
    standalone: bool  # True when no repository surrounds the script

    def out_file(self, name: str) -> Path:
        """The report path for ``name`` (e.g. ``AZs.txt``), directory created."""
        self.out_dir.mkdir(parents=True, exist_ok=True)
        return self.out_dir / name

    def out_label(self, name: str) -> str:
        """How the report path is spelled in messages: relative when inside the repo."""
        if self.standalone:
            return name
        return str(Path("aws/output") / name)


def locate(script_file: str, levels_up: int = 1) -> Context:
    """Locate the repository around ``script_file``.

    ``levels_up`` is how many directories separate the script from the repository root
    (1 for ``aws/x.py``, 2 for ``aws/probes/x.py``).
    """
    script_dir = Path(script_file).resolve().parent
    candidate = script_dir.parents[levels_up - 1]
    if (candidate / _ROOT_MARKER).is_file():
        return Context(
            script_dir=script_dir,
            repo_root=candidate,
            out_dir=candidate / "aws" / "output",
            standalone=False,
        )
    # CloudShell: no repository. The report lands beside the script - writing to a path
    # relative to a home directory that is not the repo is how a snapshot gets lost.
    return Context(
        script_dir=script_dir,
        repo_root=script_dir,
        out_dir=script_dir,
        standalone=True,
    )


def utc_stamp() -> str:
    """The report timestamp, exactly as the shell's ``date -u +%Y-%m-%dT%H:%M:%SZ``."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def subprocess_env() -> dict:
    """Environment for aws CLI calls: the pager disabled, everything else inherited."""
    env = dict(os.environ)
    env["AWS_PAGER"] = ""
    return env


def short_svc(svc: str) -> str:
    """``com.amazonaws.us-west-2.ecr.api`` -> ``ecr.api``; ``aws.sagemaker.us-west-2.studio``
    -> ``aws.sagemaker.studio``.

    Lives here rather than in a script because it is a pure function of a service name and
    ``REGION``, which this module owns, and because two scripts now need it: ``egress.py``
    labels its endpoint checks with it, and ``networking.py`` (NT-10) labels the collisions
    between a deployed endpoint's seized DNS names and the portal's public-required ones.
    Moved out of ``egress.py`` on 2026-08-25 rather than copied - one intent enforced in two
    places diverges (Lesson 33).
    """
    out = svc.replace(f".{REGION}", "")
    if out.startswith("com.amazonaws."):
        out = out[len("com.amazonaws.") :]
    return out
