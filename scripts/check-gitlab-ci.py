#!/usr/bin/env -S uv run --quiet
# check-gitlab-ci.py - the GitLab CI files this repository carries, read offline.
#
#   run:      ./scripts/check-gitlab-ci.py
#   reads:    every tracked *.gitlab-ci.yml, `.gitlab-ci.yml` included, and the files their includes
#             name. No GitLab session, no network, nothing written.
#   exit:     0 clean | 1 at least one violation
#
# Two mistakes in a GitLab CI file, found before a push; GitLab's CI Lint answers only through the
# VPN. The GitLab behaviour cited is v19.4.2's source.
#
#   A. A job named after a global keyword. GitLab reads a top-level `image`, `services`, `cache`,
#      `before_script`, `after_script`, `variables`, `stages` or `include` as the keyword whatever it
#      holds, and refuses the pipeline at creation with 0 jobs: "image name should be a string" for a
#      job named `image` (awsds/app-etl pipeline #12, 2026-10-14). A top-level `default` or
#      `workflow` holding `script`, `run`, `trigger` or `needs` becomes a job of that name instead,
#      and the keyword is lost. Under any of the ten names, the key fails when its mapping carries a
#      key only a job takes. `pages` is a job name.
#   B. A `needs:` or `dependencies:` entry naming no job, which GitLab refuses at creation: "<job>
#      job: undefined need: <name>". Names resolve per pipeline, a file no other file includes merged
#      with everything it includes, in GitLab's order; an included file is judged inside each
#      pipeline that includes it. A job's lists are its own or the ones `extends` gives it, with
#      `!reference` resolved and each `rules:` entry's `needs:` included.
#
# A `local:` include resolves against the project root: the folder of the file a pipeline starts
# from, or a carried project's folder. A `project:` include of a project in CARRIED is read from that
# folder at this commit, not at the include's `ref`. No other include is read: each is listed, and a
# need on a job only it defines fails.
#
# What it does not see: a need on a job that `rules:` leave out of one run's pipeline, a need on a
# job of a later stage, a need listed twice, and a list held by a template or a `!reference` target
# in no file read (listed as unchecked). An `optional: true` need on no job is a note: GitLab admits
# it.

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# The top-level keys GitLab reads as global keywords (Entry::Root's ALLOWED_KEYS).
GLOBAL_KEYWORDS = tuple(
    (
        "image services cache before_script after_script variables stages include default workflow"
    ).split()
)

# Entry::Root reserves the other eight. Under one of these, a mapping carrying one of JOB_MARKERS is a
# job (Root#filter_jobs!, with Job and Bridge `matching?`).
TAKEN_AS_JOB = frozenset({"default", "workflow"})
JOB_MARKERS = frozenset({"script", "run", "trigger", "needs"})

# Job keywords that no global keyword takes inside its own mapping.
JOB_ONLY = frozenset(
    (
        "script run trigger stage extends needs dependencies environment release parallel coverage"
        " resource_group allow_failure pages secrets inherit dast_configuration manual_confirmation"
        " start_in only except"
    ).split()
)

# A variable's value is a scalar, or a mapping of these keys.
VARIABLE_KEYS = frozenset({"value", "description", "options", "expand"})

# The GitLab projects whose content this repository carries, by the folder each project's root maps
# to (ci-gates/README.md). A project include of one is read from that folder.
CARRIED = {"awsds/ci-gates": Path("ci-gates")}

# A parallel job's instances are named `<job> 1/2` or `<job>: [<values>]`, and a need may name one.
INSTANCE = re.compile(r"(?P<job>.+?)(?: \d+/\d+|: \[.*\])\Z")

CI_SUFFIXES = (".gitlab-ci.yml", ".gitlab-ci.yaml")

ABSENT = object()  # a key nothing sets
UNREAD = object()  # a value only a file this script does not read can hold


class Reference(list):
    """A `!reference [job, key, ...]` tag, resolved once the pipeline's jobs are merged."""


class Loader(yaml.SafeLoader):
    """PyYAML's safe loader with GitLab's one custom tag."""


Loader.add_constructor(
    "!reference", lambda loader, node: Reference(loader.construct_sequence(node, deep=True))
)


class Refused(Exception):
    """A file or an include GitLab would refuse too."""


@dataclass
class CIFile:
    path: Path
    root: Path
    config: dict
    lines: dict
    includes: list[CIFile] = field(default_factory=list)
    unread: list[str] = field(default_factory=list)
    carried: list[str] = field(default_factory=list)


def load(path: Path) -> tuple[dict, dict]:
    """The file's configuration, and the line of each top-level key.

    A file declaring inputs carries two documents, its `spec:` header first.
    """
    try:
        text = path.read_text(encoding="utf-8")
        docs = list(yaml.load_all(text, Loader=Loader))
        nodes = list(yaml.compose_all(text, Loader=Loader))
    except OSError as e:
        raise Refused(f"unreadable: {e.strerror}") from None
    except yaml.MarkedYAMLError as e:
        mark = e.problem_mark or e.context_mark
        where = f"line {mark.line + 1}: " if mark else ""
        raise Refused(f"{where}{e.problem or e.context}") from None
    except yaml.YAMLError as e:
        raise Refused(str(e)) from None
    if len(docs) == 2 and isinstance(docs[0], dict) and set(docs[0]) == {"spec"}:
        docs, nodes = docs[1:], nodes[1:]
    if len(docs) > 1:
        raise Refused(f"{len(docs)} YAML documents, and the first is not a `spec:` header")
    config = docs[0] if docs and docs[0] is not None else {}
    if not isinstance(config, dict):
        raise Refused("the top level is not a mapping")
    lines = {}
    if nodes and isinstance(nodes[0], yaml.MappingNode):
        for key, _ in nodes[0].value:
            if isinstance(key, yaml.ScalarNode):
                lines[key.value] = key.start_mark.line + 1
    return config, lines


def keyword_jobs(config: dict) -> list[tuple[str, list[str]]]:
    """(keyword, keys) for each global keyword whose mapping carries keys only a job takes."""
    found = []
    for word in GLOBAL_KEYWORDS:
        body = config.get(word)
        if not isinstance(body, dict):
            continue
        keys = [k for k in body if k in JOB_ONLY]
        if word == "variables":
            # Any name is a variable's; the value says whether it is one.
            keys = [k for k in keys if not is_variable(body[k])]
        if keys:
            found.append((word, keys))
    return found


def is_variable(value: object) -> bool:
    if isinstance(value, dict):
        return set(value) <= VARIABLE_KEYS
    return not isinstance(value, list)


def is_job(name: str, body: dict) -> bool:
    """Whether GitLab reads the top-level `name` as a job or a template rather than a keyword."""
    if name not in GLOBAL_KEYWORDS:
        return True
    return name in TAKEN_AS_JOB and bool(JOB_MARKERS & set(body))


def include_entries(value: object) -> list:
    """The entries of an `include:` value: a path, a mapping, or a list of either."""
    if value is None:
        return []
    entries = []
    for item in value if isinstance(value, list) else [value]:
        if isinstance(item, str):
            remote = item.startswith(("http://", "https://"))
            entries.append({"remote": item} if remote else {"local": item})
        else:
            entries.append(item)
    return entries


def wildcard(pattern: str) -> re.Pattern:
    """An `include:local` path with GitLab's wildcards: `*` within a folder, `**` across folders."""
    parts = re.split(r"(\*\*|\*)", pattern)
    body = "".join(".*" if p == "**" else "[^/]*" if p == "*" else re.escape(p) for p in parts)
    return re.compile(body + r"\Z")


def resolve(entry: object, root: Path, tracked: set[str]) -> tuple[list, str | None, str | None]:
    """The (path, project root) pairs an include entry names, why it is not read, and the note a
    carried project's read takes."""
    if not isinstance(entry, dict):
        raise Refused(f"include entry {entry!r} is neither a path nor a mapping")
    if "local" in entry:
        local = entry["local"]
        if not isinstance(local, str):
            raise Refused(f"include local {local!r} is not a path")
        if "$" in local:
            return [], f"local {local}, a path carrying a variable", None
        pattern = (root / local.lstrip("/")).as_posix()
        if "*" in pattern:
            matcher = wildcard(pattern)
            hits = sorted(p for p in tracked if matcher.match(p))
        else:
            hits = [pattern] if pattern in tracked else []
        if not hits:
            raise Refused(f"include local {local} names no tracked file under {root.as_posix()}/")
        return [(Path(h), root) for h in hits], None, None
    if "project" in entry:
        project, names = entry["project"], entry.get("file")
        names = [names] if isinstance(names, str) else names
        if not isinstance(project, str) or not isinstance(names, list) or not names:
            raise Refused(f"include project {project!r} names no file")
        listed = f"project {project} {', '.join(map(str, names))}"
        folder = CARRIED.get(project)
        if folder is None or "$" in listed:
            return [], listed, None
        pairs = []
        for name in names:
            path = (folder / str(name).lstrip("/")).as_posix()
            if path not in tracked:
                raise Refused(f"include project {project} names {name}, absent from {folder}/")
            pairs.append((Path(path), folder))
        ref = entry.get("ref")
        at = f"its ref {str(ref)[:12]}" if ref else "its default branch"
        return pairs, None, f"{project} read from {folder}/ at this commit, not at {at}"
    for kind in ("template", "remote", "component"):
        if kind in entry:
            return [], f"{kind} {entry[kind]}", None
    raise Refused(f"include entry {entry!r} names no local, project, template, remote or component")


def walk(
    path: Path, root: Path, tracked: set[str], files: dict, failures: list, stack: tuple = ()
) -> CIFile | None:
    """The file at `path` and, recursively, the files it includes; None when it cannot be read."""
    key = (path, root)
    if key in files:
        return files[key]
    try:
        config, lines = load(path)
    except Refused as e:
        failures.append(f"{path}: {e}")
        files[key] = None
        return None
    node = CIFile(path, root, config, lines)
    for entry in include_entries(config.get("include")):
        try:
            pairs, unread, carried = resolve(entry, root, tracked)
        except Refused as e:
            failures.append(f"{path}:{lines.get('include', '?')}: {e}")
            continue
        node.unread += [unread] if unread else []
        node.carried += [carried] if carried else []
        for child_key in pairs:
            if child_key in stack + (key,):
                failures.append(f"{path}: includes {child_key[0]}, which includes it back")
                continue
            child = walk(*child_key, tracked, files, failures, stack + (key,))
            if child is not None:
                node.includes.append(child)
    files[key] = node
    return node


def merge_order(top: CIFile) -> list[CIFile]:
    """The pipeline's files in GitLab's merge order: each include before its includer and after the
    includes listed above it, the file itself last; a file included twice keeps its last place."""
    seq: list[CIFile] = []

    def visit(node: CIFile) -> None:
        for child in node.includes:
            visit(child)
        seq.append(node)

    visit(top)
    last = {id(node): i for i, node in enumerate(seq)}
    return [node for i, node in enumerate(seq) if last[id(node)] == i]


def deep_merge(base: object, over: object) -> object:
    if isinstance(base, dict) and isinstance(over, dict):
        merged = dict(base)
        for k, v in over.items():
            merged[k] = deep_merge(base[k], v) if k in base else v
        return merged
    return over


def merge_jobs(order: list[CIFile]) -> tuple[dict, dict]:
    """Every job and template of the pipeline, merged across its files, and the file that last
    wrote each (job, key)."""
    jobs: dict = {}
    origin: dict = {}
    for f in order:
        for name, body in f.config.items():
            if not isinstance(name, str) or not isinstance(body, dict) or not is_job(name, body):
                continue
            jobs[name] = deep_merge(jobs.get(name, {}), body)
            for key in body:
                origin[(name, key)] = f
    return jobs, origin


def inherited(name: str, key: str, jobs: dict, trail: tuple = ()) -> tuple[object, str | None]:
    """The value `key` takes in `name` after `extends`, and the job or template that sets it.

    ABSENT when nothing sets it; UNREAD, with the template's name, when an `extends` target that
    could set it is in no file read. The last target listed wins, as in GitLab.
    """
    job = jobs.get(name)
    if job is None:
        return UNREAD, name
    if key in job:
        return job[key], name
    parents = job.get("extends") or []
    seen = trail + (name,)
    for parent in reversed([parents] if isinstance(parents, str) else parents):
        if not isinstance(parent, str) or parent in seen:
            continue
        value, owner = inherited(parent, key, jobs, seen)
        if value is not ABSENT:
            return value, owner
    return ABSENT, None


def deref(value: object, jobs: dict, depth: int = 0) -> object:
    """`value` with each `!reference` replaced by what it names; UNREAD when one names nothing read."""
    if isinstance(value, Reference):
        if depth > 10 or len(value) < 2 or not all(isinstance(k, str) for k in value):
            return UNREAD
        target, _ = inherited(value[0], value[1], jobs)
        for key in value[2:]:
            target = target.get(key, ABSENT) if isinstance(target, dict) else ABSENT
        if target is ABSENT or target is UNREAD:
            return UNREAD
        return deref(target, jobs, depth + 1)
    if isinstance(value, list):
        items = [deref(item, jobs, depth) for item in value]
        return UNREAD if any(item is UNREAD for item in items) else items
    return value


def flat(value: object) -> list:
    """`value` as a list, nested lists spliced in as GitLab splices a `!reference`."""
    out: list = []
    for item in value if isinstance(value, list) else [value]:
        out.extend(flat(item) if isinstance(item, list) else [item])
    return out


def named(value: object) -> tuple[list[tuple[str, bool]], list[str]]:
    """(job, optional) for each entry naming a job of this pipeline, and the entries naming another
    pipeline's job."""
    names, elsewhere = [], []
    for item in flat(value):
        if isinstance(item, str):
            names.append((item, False))
        elif isinstance(item, dict) and ("project" in item or "pipeline" in item):
            source = item.get("project") or item.get("pipeline")
            elsewhere.append(f"`{item.get('job', '(status)')}` of {source}")
        elif isinstance(item, dict) and isinstance(item.get("job"), str):
            names.append((item["job"], item.get("optional") is True))
    return names, elsewhere


def defined(need: str, visible: set, jobs: dict) -> bool:
    """Whether `need` names a job of the pipeline, or one instance of a parallel job."""
    if need in visible:
        return True
    m = INSTANCE.match(need)
    return (
        bool(m) and m["job"] in visible and inherited(m["job"], "parallel", jobs)[0] is not ABSENT
    )


def check_pipeline(order: list[CIFile]) -> tuple[int, int, list[str], list[str]]:
    """(jobs, names resolved, failures, notes) for the pipeline whose files, merged, are `order`."""
    jobs, origin = merge_jobs(order)
    visible = {name for name in jobs if not name.startswith(".")}
    unread = sorted({u for f in order for u in f.unread})
    resolved, fails, notes = 0, [], []
    for name in sorted(visible):
        lists = []  # (label, entries, owner, key): owner is the job or template that sets key
        unseen = set()
        for key in ("needs", "dependencies", "rules"):
            value, owner = inherited(name, key, jobs)
            if value is UNREAD:
                unseen.add(owner)
            elif value is not ABSENT and key != "rules":
                lists.append((key, deref(value, jobs), owner, key))
            elif value is not ABSENT:
                value = deref(value, jobs)
                if value is UNREAD:
                    lists.append(("rules:needs", UNREAD, owner, key))
                    continue
                for rule in flat(value):
                    if isinstance(rule, dict) and "needs" in rule:
                        lists.append(("rules:needs", deref(rule["needs"], jobs), owner, key))
        if unseen:
            notes.append(
                f"{name}: extends {', '.join(sorted(unseen))}, in no file read; the needs it may"
                " carry are not checked"
            )
        for label, entries, owner, key in lists:
            if entries is UNREAD:
                notes.append(f"{name}: a !reference in its {label} names nothing read")
                continue
            names, elsewhere = named(entries)
            notes += [f"{name}: {label} names {e}, another pipeline's job" for e in elsewhere]
            for need, optional in names:
                if defined(need, visible, jobs):
                    resolved += 1
                    continue
                f = origin[(owner, key)]
                said = f"{f.path}:{f.lines.get(owner, '?')}: {name}'s {label}"
                said += f" (from {owner})" if owner != name else ""
                if need in GLOBAL_KEYWORDS:
                    fails.append(f"{said} names `{need}`, a global keyword here and not a job")
                elif need in jobs:
                    fails.append(f"{said} names `{need}`, a hidden template and never a job")
                elif optional:
                    notes.append(
                        f"{said} names `{need}`, optional and no job of this pipeline: GitLab"
                        " admits it, and the job never waits for it"
                    )
                else:
                    kind = "dependency" if key == "dependencies" else "need"
                    fails.append(
                        f"{said} names `{need}`, no job of this pipeline: GitLab refuses"
                        f' "{name} job: undefined {kind}: {need}"'
                        + (f". Not read: {'; '.join(unread)}" if unread else "")
                    )
    return len(visible), resolved, fails, notes


def main() -> int:
    os.chdir(Path(__file__).resolve().parents[1])
    failures: list[str] = []

    def bad(text: str) -> None:
        failures.append(text)
        print(f"  FAIL  {text}")

    listing = subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True, check=True)
    tracked = {p for p in listing.stdout.split("\0") if p}
    found = sorted(Path(p) for p in tracked if p.endswith(CI_SUFFIXES))

    files: dict = {}
    load_failures: list[str] = []
    for path in found:
        walk(path, path.parent, tracked, files, load_failures)
    read = {f.path: f for f in files.values() if f is not None}

    print(f"== GitLab CI files: {len(found)} tracked, {len(read)} read ==")
    for text in load_failures:
        bad(text)
    if not load_failures:
        print("  ok: every file parses, and every include read names a tracked file")

    print("\n== A. a job named after a global keyword ==")
    before = len(failures)
    for path in sorted(read):
        f = read[path]
        for word, keys in keyword_jobs(f.config):
            if is_job(word, f.config[word]):
                effect = f"GitLab takes it as a job named `{word}` and loses the keyword"
            else:
                effect = "GitLab reads the key as the keyword and refuses the file"
            bad(
                f"{path}:{f.lines.get(word, '?')}: `{word}` is a global keyword, and this one"
                f" carries {', '.join(map(str, keys))}, which only a job takes: {effect}."
                " Rename the job"
            )
    if len(failures) == before:
        print(f"  ok, {len(read)} file(s)")

    print("\n== B. needs and dependencies, per pipeline ==")
    included = {child.path for f in read.values() for child in f.includes}
    pipelines = [f for p in found if p not in included and (f := files[(p, p.parent)]) is not None]
    judged_in: dict = {}
    for top in pipelines:
        order = merge_order(top)
        for f in order[:-1]:
            judged_in.setdefault(f.path, []).append(str(top.path))
        jobs, resolved, fails, notes = check_pipeline(order)
        print(f"  {top.path}: {jobs} job(s) from {len(order)} file(s), {resolved} name(s) resolved")
        for note in sorted({c for f in order for c in f.carried}):
            print(f"        {note}")
        for text in fails:
            bad(text)
        for text in notes:
            print(f"  note  {text}")
    for path in sorted(judged_in):
        print(f"  {path}: included, judged in {', '.join(judged_in[path])}")

    print("\n== includes not read: a job only they define is invisible to B ==")
    unread_by = sorted({(u, str(f.path)) for f in read.values() for u in f.unread})
    for what, by in unread_by:
        print(f"  {what}, included by {by}")
    if not unread_by:
        print("  none")

    print()
    print("OK" if not failures else "FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
