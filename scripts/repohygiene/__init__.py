"""Hygiene over the PROJECT's prose files - markdown links, stable IDs, size budgets.

The library behind ``scripts/check-plan-refs.py``. It knows how to walk the repository's
markdown, extract relative links and stable-ID references (``D26``, ``INT-11``), and strip
the spans that merely *mention* old notation from the ones that use it.

Deliberately independent: no AWS, no Terraform. It imports nothing from ``awslib`` or
``tfhygiene``, so a change to how AWS is queried or how ``.tf`` files are scanned can never
change what counts as a broken link. Functions take paths and text; the calling script
decides where the repository root is and what to do with a finding.
"""
