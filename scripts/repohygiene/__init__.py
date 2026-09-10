"""Hygiene over the project's prose files: markdown links, stable IDs, size budgets.

The library behind ``scripts/check-plan-refs.py``. It walks the repository's markdown, extracts
relative links and stable-ID references (``D26``, ``INT-11``), and separates the spans that merely
*mention* old notation from the ones that use it.

It imports nothing from ``awslib`` or ``tfhygiene``, so a change to how AWS is queried or how ``.tf``
files are scanned cannot change what counts as a broken link. Functions take paths and text; the
calling script decides where the repository root is and what to do with a finding.
"""
