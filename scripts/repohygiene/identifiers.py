"""Identifier hygiene over the repository's TRACKED files - account ids and e-mail addresses.

The library behind ``scripts/check-identifiers.py``. The rule it mechanises is older than it:
`CLAUDE.md` says a stage log carries "no account ids", and `aws/INDEX.md` rule 1 says never to
copy an account id or an e-mail address out of a snapshot into a tracked file. Both were
enforced by attention alone until 2026-08-17, and attention had already missed four files -
Lesson 14's exact shape, a condition that must hold in N places by hand.

WHAT COUNTS AS A HIT, and why the boundary is the interesting part. An account id in an ARN is
delimited by `:`; in prose by a space, a backtick or a paren. A 12-digit run *inside* a token -
`abc_123456789012_def` in a base64 blob, a hash, a lock-file digest - is not an identifier, and
the encoded authorization failure messages the logs record verbatim are full of them. So the
scan requires the run to be bounded by something outside ``[0-9A-Za-z_-]`` on both sides. That
is what "standalone" means here, and it is the difference between a check people keep and one
they learn to skip.

TRACKED FILES ONLY, because the rule is about what reaches git. ``aws/output/`` and ``secrets/``
hold these identifiers legitimately and are both ignored, so ``git ls-files`` excludes them
without needing a rule of its own.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterator
from pathlib import Path

# Twelve digits bounded by a non-identifier character. See the module docstring for why the
# boundary class carries `_` and `-`: without them every base64 blob in docs/log/ is a hit.
ACCOUNT_ID = re.compile(r"(?<![0-9A-Za-z_-])[0-9]{12}(?![0-9A-Za-z_-])")

EMAIL = re.compile(r"[0-9A-Za-z._%+-]+@[0-9A-Za-z.-]+\.[A-Za-z]{2,}")

# THE ALLOWANCES ARE THREE LITERALS AND THEY ARE LISTED, NOT PATTERNED. An allowlist wide
# enough to be convenient is one that reports clean on a real leak (Lesson 13), so each entry
# here is a string somebody can read and disagree with.
#
#   000000000000     the probe battery's placeholder account id (aws/probes/probes.py, and the
#                    runbook row that quotes it) - a dummy chosen BECAUSE it is not an account.
#   git@github.com   the SSH remote inside `source = "git::git@github.com:..."` in every
#                    terraform-live slice. A host, not a person.
#   example.*        RFC 2606 reserved domains, the only e-mail form documentation may carry.
ALLOWED = ("000000000000", "git@github.com")
ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")


def tracked_files(root: Path) -> list[Path]:
    """Every file `git` tracks under ``root``, sorted for stable output."""
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted(root / name for name in out.split("\0") if name)


def _read_text(path: Path) -> str | None:
    """The file's text, or ``None`` when it is binary or unreadable as UTF-8."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _allowed(hit: str) -> bool:
    if hit in ALLOWED:
        return True
    return "@" in hit and hit.rsplit("@", 1)[1].lower() in ALLOWED_EMAIL_DOMAINS


def findings(paths, root: Path) -> Iterator[tuple[Path, int, str, str]]:
    """``(path, line-number, kind, hit)`` for every identifier that is not allowed.

    ``kind`` is ``"account id"`` or ``"e-mail"`` - the message says which convention to apply,
    because the two have different replacements: an id becomes the account's name, an e-mail
    inside an ARN becomes that user's role name.
    """
    for path in paths:
        text = _read_text(path)
        if text is None:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for rx, kind in ((ACCOUNT_ID, "account id"), (EMAIL, "e-mail")):
                for m in rx.finditer(line):
                    if not _allowed(m.group(0)):
                        yield path.relative_to(root), n, kind, m.group(0)
