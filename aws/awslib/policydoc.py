"""What plays the part of a ``Sid`` in each of the four organization policy types.

Used by ``org-policies.py`` (section 1's entry lists, section 3's statement greps) and by
the battery's ``readback.py``. The extraction is deliberately the same as the one in
``scripts/tfhygiene/policydoc.py``, which ``check-index.py`` runs against the repository
copies - and the two are SEPARATE COPIES on purpose, the same trade the shell versions
made: this one must keep working in CloudShell with nothing but the ``aws/`` folder
present, and the hygiene package must not depend on anything under ``aws/``. Twelve lines
duplicated with a cross-reference beat a shared module that couples the two worlds.
"""

from __future__ import annotations

import json


def statements(doc: dict) -> list:
    """The Statement list of an SCP/RCP, normalised (a bare dict becomes a one-item list)."""
    stmts = doc.get("Statement", [])
    if isinstance(stmts, dict):
        stmts = [stmts]
    return stmts


def statement_lines(doc: dict) -> list:
    """One ``(sid, compact-json-of-the-rest)`` per statement.

    Binding to the Sid is the point (Lesson 23); the second half is what condition checks
    grep, exactly as the shell's embedded ``stmt.py`` emitted it.
    """
    out = []
    for s in statements(doc):
        sid = s.get("Sid", "(no Sid)")
        rest = {k: v for k, v in s.items() if k != "Sid"}
        out.append((sid, json.dumps(rest, separators=(",", ":"), sort_keys=True)))
    return out


def entries(doc: dict) -> list:
    """The entry names of a document, whatever its type.

    ``Sid``s for an SCP or RCP, tag keys for a tag policy, attribute names for a
    declarative policy. A shape nobody taught this function is REPORTED rather than
    skipped - a listing that silently drops a document is exactly the omission the
    callers were widened to fix (Lesson 13).
    """
    if "Statement" in doc:
        return [s.get("Sid", "(no Sid)") for s in statements(doc)]
    if "tags" in doc:
        return [v["tag_key"]["@@assign"] for v in doc["tags"].values()]
    if "ec2_attributes" in doc:
        return list(doc["ec2_attributes"].keys())
    return ["(unrecognised document - no Statement, tags or ec2_attributes key)"]
