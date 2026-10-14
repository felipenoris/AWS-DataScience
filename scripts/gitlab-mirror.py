#!/usr/bin/env -S uv run --quiet
# gitlab-mirror.py - Stage 8 decision 16. Copies the last commit of each GitLab project this
# repository mirrors into gitlab/<group>/<project>/, so the repository keeps a copy of what the private
# GitLab holds. GitLab is the source of truth: a change is made there, and this script copies it back.
#
#   ./scripts/gitlab-mirror.py                       every project in PROJECTS
#   ./scripts/gitlab-mirror.py awsds/dev-env         one project
#   ./scripts/gitlab-mirror.py --dry-run             what would change, nothing written
#
#   needs:    the VPN tunnel up and GitLab running (`make hub-up`, `make gitlab-up`), and git able to
#             read the projects over HTTPS with the operator's own credential helper and the internal
#             root in `http.sslCAInfo` (runbook gitlab.md §C). The script passes no credential, and
#             GIT_TERMINAL_PROMPT=0 makes a missing one fail instead of waiting on a prompt (Lesson 47).
#   reads:    one `git clone --depth 1` of each project's branch
#   writes:   gitlab/<group>/<project>/, replaced whole by the commit's tree, and gitlab/mirror.json,
#             the commit each copy holds. Nothing outside gitlab/, and nothing in GitLab.
#   exit:     0 copied, or nothing to copy | 1 a clone or a copy failed | 2 usage, or uncommitted
#             changes under a copy that would be overwritten
#
# The copy is the commit's tree as `git archive` exports it: the tracked files at their modes, no
# history and no .git. A file under gitlab/ that GitLab does not hold is reported and removed, and a
# file that differs is reported and replaced, so an edit made here first is a proposal: it is true
# once GitLab holds it and this script reports the copy unchanged. Uncommitted changes under a copy
# stop the run before anything is written, since replacing them would lose them.

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

BASE_URL = "https://gitlab.awsds.internal"

# GitLab project path -> the branch whose last commit is copied. The copy lands at gitlab/<path>/.
# ci-gates/ and examples/app-etl/ are not here: this repository is their source and GitLab the copy.
PROJECTS = {
    "awsds/dev-env": "main",
    "awsds/deploy-image": "main",
}

MIRROR_ROOT = Path("gitlab")
RECORD = MIRROR_ROOT / "mirror.json"


def run(cmd: list, cwd: Path | None = None, capture: bool = False) -> subprocess.CompletedProcess:
    """One subprocess, announced first. A failure is returned, never raised."""
    print(f"  $ {' '.join(cmd)}")
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=capture, text=True)


def tree_digest(root: Path) -> dict:
    """Relative path -> (sha256, executable bit) for every file and symlink under root."""
    found = {}
    if not root.is_dir():
        return found
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            found[rel] = ("link:" + os.readlink(path), False)
        elif path.is_file():
            data = hashlib.sha256(path.read_bytes()).hexdigest()
            found[rel] = (data, os.access(path, os.X_OK))
    return found


def uncommitted(target: Path) -> list:
    """Uncommitted changes git reports under target, as `git status --porcelain` lines."""
    res = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", target.as_posix()],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        return [f"git status failed: {res.stderr.strip()}"]
    return [line for line in res.stdout.splitlines() if line.strip()]


def copy_project(path: str, branch: str, base_url: str, dry: bool, scratch: Path) -> dict | None:
    """Clone one project, export its last commit and replace the copy. The commit record, or None."""
    target = MIRROR_ROOT / path
    print(f"\n== {path} ({branch}) -> {target}/")

    pending = uncommitted(target)
    if pending:
        verdict = "would be lost" if dry else "would be lost - REFUSED"
        print(f"  {len(pending)} uncommitted change(s) under {target}/ {verdict}:")
        for line in pending[:20]:
            print(f"    {line}")
        if not dry:
            print("  Commit them as a proposal or discard them, then run this again.")
            raise SystemExit(2)

    clone = scratch / path.replace("/", "__")
    res = run(
        [
            "git",
            "clone",
            "--quiet",
            "--depth",
            "1",
            "--single-branch",
            "--branch",
            branch,
            f"{base_url}/{path}.git",
            str(clone),
        ]
    )
    if res.returncode != 0:
        print(f"  FAILED: the clone exited {res.returncode}")
        return None

    res = run(["git", "log", "-1", "--format=%H%x00%cI%x00%s"], cwd=clone, capture=True)
    if res.returncode != 0:
        print(f"  FAILED: git log exited {res.returncode}: {res.stderr.strip()}")
        return None
    commit, committed, subject = res.stdout.strip().split("\0", 2)
    print(f"  commit {commit}  {committed}  {subject}")

    archive = scratch / f"{clone.name}.tar"
    res = run(["git", "archive", "--format=tar", "--output", str(archive), "HEAD"], cwd=clone)
    if res.returncode != 0:
        print(f"  FAILED: git archive exited {res.returncode}")
        return None
    tree = scratch / f"{clone.name}.tree"
    tree.mkdir()
    with tarfile.open(archive) as tar:
        tar.extractall(tree, filter="data")

    before, after = tree_digest(target), tree_digest(tree)
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])
    for label, paths in (("added", added), ("removed", removed), ("changed", changed)):
        for p in paths:
            print(f"  {label:<8}{p}")
    if not (added or removed or changed):
        print(f"  the copy already holds this commit's {len(after)} file(s)")
    else:
        print(f"  {len(added)} added, {len(removed)} removed, {len(changed)} changed")

    if not dry and (added or removed or changed):
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tree), str(target))

    return {"branch": branch, "commit": commit, "committed": committed, "subject": subject}


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])
    # Each line reaches the terminal before the subprocess output it introduces.
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(
        description="Copy the last commit of each mirrored GitLab project into gitlab/."
    )
    parser.add_argument("projects", nargs="*", help="GitLab project paths; default: every one")
    parser.add_argument(
        "--dry-run", action="store_true", help="report the differences, write nothing"
    )
    parser.add_argument(
        "--base-url",
        default=BASE_URL,
        help=f"where the projects are cloned from (default {BASE_URL}); a file:// URL for a test",
    )
    args = parser.parse_args(argv)

    unknown = [p for p in args.projects if p not in PROJECTS]
    if unknown:
        print(
            f"not mirrored: {', '.join(unknown)} - the table is PROJECTS in this file",
            file=sys.stderr,
        )
        return 2
    selected = args.projects or list(PROJECTS)

    record = json.loads(RECORD.read_text(encoding="utf-8")) if RECORD.is_file() else {}
    copied = 0
    failed = 0
    with tempfile.TemporaryDirectory(prefix="gitlab-mirror-") as tmp:
        for path in selected:
            entry = copy_project(
                path, PROJECTS[path], args.base_url.rstrip("/"), args.dry_run, Path(tmp)
            )
            if entry is None:
                failed += 1
            elif not args.dry_run:
                record[path] = entry
                copied += 1

    if copied:
        RECORD.parent.mkdir(parents=True, exist_ok=True)
        RECORD.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nwrote {RECORD}; review with `git status gitlab/` and commit the copy")
    if failed:
        print(f"{failed} project(s) not copied", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
