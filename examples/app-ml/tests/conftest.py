"""What the tests of TRAINING_SOURCE share: a git repository holding an application's tracked paths,
built in a temporary folder by a git whose configuration is none of the caller's."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# The test runner's image may carry no git; the tests that need one skip there.
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is not on PATH")

# No global or system configuration, so a caller's hooks or signing never reach a commit; an author
# that is no address; and no search for a repository above the test's folder.
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "tests",
    "GIT_AUTHOR_EMAIL": "tests",
    "GIT_COMMITTER_NAME": "tests",
    "GIT_COMMITTER_EMAIL": "tests",
}


@pytest.fixture
def git_env(monkeypatch, tmp_path) -> dict:
    """GIT_ENV in this process's environment, the ceiling at the test's folder; the variables."""
    variables = {**GIT_ENV, "GIT_CEILING_DIRECTORIES": str(tmp_path)}
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    return variables


def git(folder: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(folder), *args], check=True, capture_output=True, text=True
    )
    return done.stdout


def commit_application(repository: Path, subfolder: str = "", scripts: tuple = ()) -> Path:
    """A repository whose `subfolder` holds the paths TRAINING_SOURCE covers, a second workflow, a
    README and the named scripts of this application, all committed; the application's folder."""
    app = repository / subfolder
    (app / "src" / "app_ml").mkdir(parents=True)
    (app / "src" / "app_ml" / "prepare.py").write_text("FEATURES = ()\n")
    (app / "samples").mkdir()
    (app / "samples" / "churn.csv").write_text("tenure_months,churned\n1,0\n")
    (app / "workflows").mkdir()
    (app / "workflows" / "app-ml-train.yaml").write_text("app-ml-train: {}\n")
    (app / "workflows" / "app-ml-score.yaml").write_text("app-ml-score: {}\n")
    (app / "README.md").write_text("# app-ml\n")
    if scripts:
        (app / "scripts").mkdir()
        for name in scripts:
            shutil.copy2(ROOT / "scripts" / name, app / "scripts" / name)
    git(repository, "init", "-q")
    git(repository, "add", "-A")
    git(repository, "commit", "-q", "-m", "the application")
    return app
