"""The authored per-OU attachment map (``org-policies/attachments.json``).

The two-list shape is the point: OUs that carry a document AND OUs that deliberately carry
none, with the reason - so "absent" and "deliberately absent" stay distinguishable
(Lesson 13; ``Sandboxes`` is the entry a future reader will try to fix, D37). The map is
read by ``check-ou-coverage.py`` and by the org-policies Terraform slice's ``for_each``;
this module is the one loader.
"""

from __future__ import annotations

import json
from pathlib import Path


class AttachmentsMap:
    """The parsed map, with the three views the coverage check reads."""

    def __init__(self, raw: dict):
        self.root: list[str] = list(raw.get("root", []))
        self.ou: dict[str, list[str]] = dict(raw.get("ou", {}))
        self.ou_with_no_document: dict[str, str] = dict(raw.get("ou_with_no_document", {}))

    def documents(self) -> list[str]:
        """Every document name the map references, deduplicated and sorted."""
        names = set(self.root)
        for docs in self.ou.values():
            names.update(docs)
        return sorted(names)


def load(path: Path) -> AttachmentsMap:
    """Parse the map; raises on unreadable/undecodable input (the caller exits 2)."""
    return AttachmentsMap(json.loads(path.read_text(encoding="utf-8")))
