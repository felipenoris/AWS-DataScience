#!/usr/bin/env bash
# Builds the operator archives of Stage 6i steps 4 and 5 into dist/ (untracked):
#
#   python-operator.zip   demo_tasks.py, the project's package and the vendored set of
#                         python/requirements.txt, all at the archive's root, built for the
#                         worker: CPython 3.12 on manylinux2014 x86_64
#   bash-operator.zip     reach_pypi.sh and the project's package
#
# The vendored set is downloaded here, on the machine that builds, never on the worker, which
# has no internet path. The archives are uploaded in the portal's Settings -> Storage.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
package="$here/../awsds-demo-job/src/awsds_demo_job"
dist="$here/dist"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

rm -rf "$dist"
mkdir -p "$dist" "$stage/python" "$stage/bash"

cp "$here/python/demo_tasks.py" "$stage/python/"
cp -R "$package" "$stage/python/"
uv pip install --quiet --target "$stage/python" \
  --python-platform x86_64-manylinux2014 --python-version 3.12 --only-binary :all: \
  -r "$here/python/requirements.txt"

cp "$here/bash/reach_pypi.sh" "$stage/bash/"
cp -R "$package" "$stage/bash/"

for variant in python bash; do
  find "$stage/$variant" -name __pycache__ -type d -prune -exec rm -rf {} +
  (cd "$stage/$variant" && zip -qr "$dist/$variant-operator.zip" . -x '*.pyc')
done

ls -l "$dist"
unzip -l "$dist/python-operator.zip" | tail -1
