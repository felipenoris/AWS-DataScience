"""scripts/training-source.py over repositories built here: one value for one content, whether the
application is a repository's root or a folder of one; a new value for a commit under the paths it
covers and none for a commit elsewhere; `dirty` for a change or an untracked file under them; and
exit 1 where git reads no repository."""

from __future__ import annotations

import hashlib
import runpy

import pytest
from conftest import ROOT, commit_application, git, needs_git

pytestmark = needs_git


@pytest.fixture(scope="module")
def helper():
    return runpy.run_path(str(ROOT / "scripts" / "training-source.py"), run_name="training_source")


def test_the_value_is_the_hash_of_heads_listing_of_the_paths(helper, git_env, tmp_path):
    app = commit_application(tmp_path / "app")
    listing = git(
        app, "ls-tree", "-r", "HEAD", "--", "src", "samples", "workflows/app-ml-train.yaml"
    )
    assert "app-ml-score.yaml" not in listing and "README.md" not in listing
    assert helper["training_source"](app) == hashlib.sha256(listing.encode()).hexdigest()


def test_the_value_is_the_same_at_a_repositorys_root_and_in_a_folder_of_one(
    helper, git_env, tmp_path
):
    alone = commit_application(tmp_path / "alone")
    nested = commit_application(tmp_path / "infrastructure", subfolder="examples/app-ml")
    assert helper["training_source"](alone) == helper["training_source"](nested)


def test_a_commit_elsewhere_keeps_the_value_and_one_under_the_paths_changes_it(
    helper, git_env, tmp_path
):
    app = commit_application(tmp_path / "app")
    first = helper["training_source"](app)
    (app / "README.md").write_text("# app-ml, the second line\n")
    (app / "workflows" / "app-ml-score.yaml").write_text("app-ml-score: {tasks: {}}\n")
    git(app, "commit", "-q", "-am", "elsewhere")
    assert helper["training_source"](app) == first
    (app / "samples" / "churn.csv").write_text("tenure_months,churned\n1,1\n")
    git(app, "commit", "-q", "-am", "the sample")
    assert helper["training_source"](app) not in (first, "dirty")


@pytest.mark.parametrize(
    "change",
    ["src/app_ml/prepare.py", "workflows/app-ml-train.yaml", "samples/extra.csv", "src/new.py"],
)
def test_a_change_or_an_untracked_file_under_the_paths_is_dirty(helper, git_env, tmp_path, change):
    app = commit_application(tmp_path / "app")
    (app / change).write_text("changed\n")
    assert helper["training_source"](app) == "dirty"


def test_an_untracked_file_elsewhere_is_not_dirty(helper, git_env, tmp_path):
    app = commit_application(tmp_path / "app")
    first = helper["training_source"](app)
    (app / "model.env").write_text("MODEL_SHA256=x\n")
    assert helper["training_source"](app) == first


def test_main_prints_the_value(helper, git_env, tmp_path, capsys):
    app = commit_application(tmp_path / "app")
    assert helper["main"]([str(app)]) == 0
    assert capsys.readouterr().out.strip() == helper["training_source"](app)


def test_main_exits_1_where_git_reads_no_repository(helper, git_env, tmp_path, capsys):
    loose = tmp_path / "loose"
    loose.mkdir()
    assert helper["main"]([str(loose)]) == 1
    assert "training-source: git status in" in capsys.readouterr().err
