#!/usr/bin/env python3
"""The guard on a release's catalog (the pipeline's `bundle` job): what the bundle's catalog export
holds against the product this application declares in product.json.

    python3 scripts/check-catalog-export.py artifacts/app-etl.zip product.json

The CI/CD CLI exports every catalog resource the `dev` project owns, with no filter, and a deploy
imports the export into each target's project. A bundle that carries more than the declared product
would promote it, and one that carries less would promote a product without what the scientist
curated in the `dev` project, so both fail the release. An export that failed leaves the bundle
whole and the CLI's exit status 0, so a bundle without catalog/catalog_export.json fails too.

product.json names, by section of the export, the resources a release must carry (`required`, each
one exactly once) and the ones it may carry (`allowed`): a form type or a glossary the project owns
travels with the product, and one another project owns does not. A name outside both fails.

Exit 0 when the export is the declared product, 1 otherwise; 2 on a file it cannot read. It prints
names and counts, never a form's content. The standard library alone: the job runs it on the
deploy runner's Python.
"""

from __future__ import annotations

import json
import sys
import zipfile

EXPORT = "catalog/catalog_export.json"
SECTIONS = ("glossaries", "glossaryTerms", "formTypes", "assetTypes", "assets", "dataProducts")


def names_of(export: dict, section: str) -> list:
    """The names of the resources a section of the export holds."""
    return [str(item.get("name")) for item in export.get(section) or []]


def compare(export: dict, declared: dict) -> list:
    """The export against the declaration: the problems, none when it is the declared product."""
    problems = []
    required = declared.get("required") or {}
    allowed = declared.get("allowed") or {}
    for section in sorted(set(required) | set(allowed)):
        if section not in SECTIONS:
            problems.append(f"product.json names a section the export has none of: {section}")
    for section in SECTIONS:
        must = list(required.get(section) or [])
        may = set(allowed.get(section) or []) | set(must)
        found = names_of(export, section)
        for name in must:
            count = found.count(name)
            if count != 1:
                problems.append(
                    f"{section}: {name} is in the export {count} time(s), once expected"
                )
        for name in sorted(set(found) - may):
            problems.append(f"{section}: {name} is in the export and not in product.json")
    return problems


def read_export(bundle: str) -> dict:
    with zipfile.ZipFile(bundle) as archive:
        if EXPORT not in archive.namelist():
            raise KeyError(EXPORT)
        return json.loads(archive.read(EXPORT))


def main(argv: list) -> int:
    if len(argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    bundle, declaration = argv
    try:
        with open(declaration, encoding="utf-8") as handle:
            declared = json.load(handle)
    except (OSError, ValueError) as e:
        print(f"check-catalog-export: {declaration}: {e}", file=sys.stderr)
        return 2
    try:
        export = read_export(bundle)
    except KeyError:
        print(
            f"FAIL  {bundle} carries no {EXPORT}: the export failed, or the manifest's "
            "content.catalog is off"
        )
        return 1
    except (OSError, ValueError, zipfile.BadZipFile) as e:
        print(f"check-catalog-export: {bundle}: {e}", file=sys.stderr)
        return 2
    for section in SECTIONS:
        found = names_of(export, section)
        print(f"  {section}: {len(found)}{' (' + ', '.join(sorted(found)) + ')' if found else ''}")
    problems = compare(export, declared)
    for problem in problems:
        print(f"FAIL  {problem}")
    print("OK" if not problems else "FAILED")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
