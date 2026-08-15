"""Reading the repository's organization policy documents, one statement at a time.

The extraction in :func:`entries` is deliberately the same as the one in
``aws/awslib/policydoc.py`` - a SEPARATE COPY, on purpose: the ``aws/`` scripts must keep
working in CloudShell with nothing but their own folder present, and this package must not
import from ``aws/``. The property being extracted is "what does this document contain, in
order", and a document whose type is not recognised is REPORTED rather than skipped: a
checker that silently ignores a file is not a checker (Lesson 13).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path


class UnknownPolicyShape(Exception):
    """A document with no Statement, tags or ec2_attributes key."""


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def statements(doc: dict) -> list:
    """The Statement list of an SCP/RCP, normalised (a bare dict becomes a one-item list)."""
    stmts = doc.get("Statement", [])
    if isinstance(stmts, dict):
        stmts = [stmts]
    return stmts


def entries(doc: dict, name: str) -> list:
    """What plays the part of a ``Sid`` for this document's type, in document order.

    ``Sid``s for an SCP or RCP, tag keys for a tag policy, attribute names for a
    declarative policy. ``name`` is only for the error message.
    """
    if "Statement" in doc:
        return [s["Sid"] for s in statements(doc)]
    if "tags" in doc:
        return [v["tag_key"]["@@assign"] for v in doc["tags"].values()]
    if "ec2_attributes" in doc:
        return list(doc["ec2_attributes"].keys())
    raise UnknownPolicyShape(
        f"{name}: unrecognised policy document - no Statement, tags or ec2_attributes key. "
        "Teach check-index.py what plays the part of a Sid for this type before adding it."
    )


def is_policy_document(parsed: object) -> bool:
    """A JSON value that is judged statement-by-statement rather than as text.

    A JSON file that is not a policy document (the tag policy, the declarative policy,
    attachments.json) is scanned as plain text by the wildcard check, with no exception
    available - this predicate is where the two classes split.
    """
    return isinstance(parsed, dict) and isinstance(parsed.get("Statement"), list)


def statement_texts(doc: dict) -> Iterator[tuple[str, str]]:
    """``(sid, compact-json-of-the-whole-statement)`` per statement, for pattern tests."""
    for s in statements(doc):
        yield s.get("Sid", "<no Sid>"), json.dumps(s)
