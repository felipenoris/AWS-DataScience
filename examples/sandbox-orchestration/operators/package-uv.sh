#!/usr/bin/env bash
# Packages a uv project as one MWAA Serverless code archive for a Python or Bash task: the project's
# own wheel and the dependencies its uv.lock pins, installed side by side at the archive's root and
# built for the worker, plus the entry module the task names.
#
#   package-uv.sh [--python X.Y] [--platform TAG] <project dir> <entry module .py> <archive .zip>
#   OMIT="name ..." package-uv.sh ...     # more packages to leave out
#
# The worker is CPython 3.12 on x86_64 Linux (the guide, read 2026-10-11), so --python defaults to
# 3.12 and --platform to x86_64-manylinux2014; both are flags because the service can move the worker
# to another interpreter without notice, and the task log names it (a path under .../python3.X/).
# The packages the worker pre-installs are pruned with every dependency only they need: the guide
# says the worker imports its own copy whatever the archive holds. The procedure, and why each step is
# there: docs/plan/runbooks/serverless-workflows.md section C.
set -euo pipefail

python=3.12
platform=x86_64-manylinux2014
while [[ $# -gt 0 && $1 == --* ]]; do
  case $1 in
    --python) python=$2; shift 2 ;;
    --platform) platform=$2; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
if [[ $# -ne 3 ]]; then
  echo "usage: $0 [--python X.Y] [--platform TAG] <project dir> <entry module .py> <archive .zip>" >&2
  exit 2
fi
project=$(cd "$1" && pwd)
entry="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
archive="$(cd "$(dirname "$3")" && pwd)/$(basename "$3")"
[[ -f "$project/uv.lock" ]] || { echo "no uv.lock in $project - run uv lock there first" >&2; exit 2; }
[[ -f "$entry" ]] || { echo "no entry module at $entry" >&2; exit 2; }
target=(--python-version "$python" --python-platform "$platform")

# The worker's pre-installed set, from the guide's table (read 2026-10-11).
worker_provided=(
  apache-airflow apache-airflow-providers-amazon boto3 botocore dag-factory pyyaml lz4
  aws-encryption-sdk aws-cryptographic-material-providers aws-cryptography-internal-kms
  aws-cryptography-internal-dynamodb aws-cryptography-internal-primitives
)
prune=()
for name in "${worker_provided[@]}" ${OMIT:-}; do prune+=(--prune "$name"); done

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/root" "$stage/dist"

# The locked closure as a requirements file, without the project itself. --locked refuses a
# uv.lock that no longer matches pyproject.toml.
(cd "$project" && uv export --locked --no-dev --no-emit-project --no-header --quiet \
  "${prune[@]}" -o "$stage/requirements.txt")

# The worker's wheels for that closure. --no-deps keeps the export's closure as it is, so nothing
# pruned comes back; --only-binary refuses a source distribution, which would build for this machine.
uv pip install --quiet --target "$stage/root" --no-deps --only-binary :all: "${target[@]}" \
  -r "$stage/requirements.txt"

# The project as a wheel built from its pyproject.toml; its requires-python must admit the target.
# A wheel with extension modules would be built for this machine, so only a pure one is accepted.
uv build "$project" --wheel --out-dir "$stage/dist" --quiet
for wheel in "$stage"/dist/*.whl; do
  [[ $wheel == *-none-any.whl ]] || { echo "$(basename "$wheel"): not pure Python, cannot be built here for the worker" >&2; exit 1; }
done
uv pip install --quiet --target "$stage/root" --no-deps "${target[@]}" "$stage"/dist/*.whl

# The module python_callable names as <module>.<function>, at the root.
cp "$entry" "$stage/root/"

# uv's lock file for --target, console scripts and bytecode are not code the worker imports.
rm -rf "$stage/root/.lock" "$stage/root/bin"
find "$stage/root" -name __pycache__ -type d -prune -exec rm -rf {} +

rm -f "$archive"
(cd "$stage/root" && zip -qr "$archive" . -x '*.pyc')

# The guide's limit is 250 MB, unzipped as well.
unzipped=$(unzip -l "$archive" | tail -1 | awk '{print $1}')
if ((unzipped > 250000000)); then
  echo "$archive unzips to $unzipped bytes, over the 250 MB limit" >&2
  exit 1
fi
echo "$archive: $(wc -c <"$archive" | tr -d ' ') bytes, $unzipped unzipped, for CPython $python on $platform"
unzip -Z1 "$archive" | awk -F/ '{print $1}' | sort -u
