"""Stage 17 step 7.4a: the knowledge base's documents copied into the project bucket.

Copies this repository's runbooks, docs/plan/runbooks/*.md from the clone the script runs in, to
the project's shared/ml-demo/bedrock/kb/, the prefix the Knowledge Base component's *Project data
sources* takes. It prints the clone's commit, each document's key and size, and the total: the
document list the stage log records. A document already under the prefix is overwritten; one the
runbooks no longer hold is left there, and printed.

    /opt/awsds/venv/bin/python knowledge_base.py
"""

from __future__ import annotations

import subprocess
import sys

from common import HERE, client, demo_prefix, load_values

REPO_ROOT = HERE.parents[1]
RUNBOOKS = REPO_ROOT / "docs" / "plan" / "runbooks"


def commit() -> str:
    """The clone's commit, or why it is unread."""
    try:
        done = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as err:
        return f"(unread: {err})"
    return done.stdout.strip()


def main() -> int:
    values = load_values()
    s3 = client(values, "s3")
    bucket, prefix = values["PROJECTS_BUCKET"], f"{demo_prefix(values)}/bedrock/kb"
    documents = sorted(RUNBOOKS.glob("*.md"))
    if not documents:
        sys.exit(f"no runbook under {RUNBOOKS}: run this from a clone of the repository.")

    print(f"commit {commit()}")
    total = 0
    for path in documents:
        key = f"{prefix}/{path.name}"
        s3.upload_file(str(path), bucket, key)
        size = path.stat().st_size
        total += size
        print(f"{size:>8} {path.name} -> s3://{bucket}/{key}")
    print(f"{len(documents)} documents, {total} bytes")

    # Whatever else the prefix holds is in the knowledge base too, at its next sync.
    listed = s3.list_objects_v2(Bucket=bucket, Prefix=f"{prefix}/").get("Contents", [])
    names = {path.name for path in documents}
    stale = [obj["Key"] for obj in listed if obj["Key"].rsplit("/", 1)[-1] not in names]
    for key in stale:
        print(f"also under the prefix: s3://{bucket}/{key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
