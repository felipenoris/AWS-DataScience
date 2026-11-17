#!/usr/bin/env python3
"""TRAINING_SOURCE, the mark of the code, the sample and the training request a deploy carries.

    python3 scripts/training-source.py [APPLICATION_FOLDER]

The SHA-256 of `git ls-tree -r HEAD` over src/, samples/ and workflows/app-ml-train.yaml, each path
relative to the application's folder (by default the parent of this script's), so the value is the
same where the application is a repository's root and where it is a folder of one. It is the word
`dirty` where the working copy differs from HEAD under those paths, an untracked file included.
scripts/dev-cli.sh gives each deploy to `dev` this value as the stage variable TRAINING_SOURCE, the
publish task writes it into model.json, and scripts/check-model-bundle.py computes it over the tag
and fails a release whose candidate carries another.

The value is the deployer's own statement: it catches a training run older than the tag's code, and
it is no control over a member who writes the candidate's prefix by hand. Exit 0 with the value on
stdout, 1 where git cannot read the folder. The standard library and git alone.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

PATHS = ("src", "samples", "workflows/app-ml-train.yaml")
DIRTY = "dirty"


class SourceError(RuntimeError):
    pass


def git(folder: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(folder), *args], capture_output=True, text=True)
    if done.returncode != 0:
        raise SourceError(f"git {args[0]} in {folder}: {done.stderr.strip()}")
    return done.stdout


def training_source(folder: Path) -> str:
    """The SHA-256 of HEAD's listing of PATHS, or DIRTY where the working copy differs there."""
    status = git(folder, "status", "--porcelain", "--untracked-files=all", "--", *PATHS)
    if status.strip():
        return DIRTY
    listing = git(folder, "ls-tree", "-r", "HEAD", "--", *PATHS)
    if not listing.strip():
        raise SourceError(f"HEAD holds none of {', '.join(PATHS)} under {folder}")
    return hashlib.sha256(listing.encode()).hexdigest()


def main(argv: list[str]) -> int:
    folder = Path(argv[0]) if argv else Path(__file__).resolve().parents[1]
    try:
        print(training_source(folder))
    except (OSError, SourceError) as exc:
        print(f"training-source: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
