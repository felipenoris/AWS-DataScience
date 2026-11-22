"""Stage 17 step 7.4: the evaluation job's dataset copied into the project bucket.

Copies bedrock/evaluation-dataset.jsonl to the project's shared/ml-demo/bedrock/, where the portal's
evaluation form can choose it from S3. The file holds twenty prompts of the task *Question and answer*,
each line a JSON object with the `prompt`, `referenceResponse` and `category` keys of a custom prompt
dataset. Every line is checked before the copy, and the script prints the line count, the size and the
key.

    /opt/awsds/venv/bin/python evaluation_dataset.py
"""

from __future__ import annotations

import json
import sys

from common import HERE, client, demo_prefix, load_values

DATASET = HERE / "bedrock" / "evaluation-dataset.jsonl"
KEYS = {"prompt", "referenceResponse", "category"}


def check(lines: list[str]) -> None:
    """Stop on a line that is not a JSON object holding exactly the dataset's keys."""
    for number, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as err:
            sys.exit(f"{DATASET.name}:{number} is not JSON: {err}")
        if not isinstance(row, dict) or set(row) != KEYS:
            sys.exit(f"{DATASET.name}:{number} does not hold exactly {sorted(KEYS)}")


def main() -> int:
    lines = DATASET.read_text(encoding="utf-8").splitlines()
    check(lines)
    values = load_values()
    bucket = values["PROJECTS_BUCKET"]
    key = f"{demo_prefix(values)}/bedrock/{DATASET.name}"
    client(values, "s3").upload_file(str(DATASET), bucket, key)
    print(f"{len(lines)} prompts, {DATASET.stat().st_size} bytes -> s3://{bucket}/{key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
