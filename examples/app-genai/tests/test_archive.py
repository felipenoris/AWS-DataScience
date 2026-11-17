"""scripts/build_archive.py: the archive's entries, its bytes stable across builds, no bytecode,
and the check that reads it as the worker does."""

from __future__ import annotations

import shutil
import zipfile

import pytest

import build_archive

EXPECTED = [
    "app_genai_tasks/__init__.py",
    "app_genai_tasks/check.py",
    "app_genai_tasks/common.py",
    "app_genai_tasks/guardrail.py",
    "app_genai_tasks/probe.py",
    "app_genai_tasks/triage.py",
    "guardrail/definition.json",
    "prompts/triage.md",
]


@pytest.fixture
def tree(tmp_path):
    """A copy of the files the archive is built from, with bytecode beside the package."""
    root = tmp_path / "app"
    shutil.copytree(
        build_archive.ROOT / "code" / "app_genai_tasks", root / "code" / "app_genai_tasks"
    )
    for name in build_archive.FILES:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(build_archive.ROOT / name, root / name)
    cache = root / "code" / "app_genai_tasks" / "__pycache__"
    cache.mkdir(exist_ok=True)
    (cache / "common.cpython-312.pyc").write_bytes(b"stale")
    return root


def test_the_archive_holds_the_package_and_its_files_and_no_bytecode(tree, tmp_path):
    target = tmp_path / "app-genai.zip"
    assert build_archive.build(target, tree) == EXPECTED
    with zipfile.ZipFile(target) as archive:
        assert archive.namelist() == EXPECTED


def test_two_builds_are_the_same_bytes(tree, tmp_path):
    first, second = tmp_path / "1.zip", tmp_path / "2.zip"
    build_archive.build(first, tree)
    build_archive.build(second, tree)
    assert first.read_bytes() == second.read_bytes()


def test_the_archive_imports_as_the_worker_reads_it(tree, tmp_path):
    target = tmp_path / "app-genai.zip"
    build_archive.build(target, tree)
    printed = build_archive.verify(target)
    assert "ensure_guardrail,triage_messages,check_answers,probe_unguarded" in printed
    assert "prompts/triage.md,guardrail/definition.json" in printed


def test_an_archive_without_the_prompt_fails_the_check(tree, tmp_path):
    target = tmp_path / "app-genai.zip"
    with zipfile.ZipFile(target, "w") as archive:
        for source, name in build_archive.entries(tree):
            if name != "prompts/triage.md":
                archive.write(source, name)
    with pytest.raises(RuntimeError, match="does not import as the worker reads it"):
        build_archive.verify(target)


def test_a_missing_file_stops_the_build(tree, tmp_path):
    (tree / "guardrail" / "definition.json").unlink()
    with pytest.raises(FileNotFoundError, match="definition.json"):
        build_archive.build(tmp_path / "app-genai.zip", tree)
