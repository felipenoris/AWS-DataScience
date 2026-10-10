#!/usr/bin/env bash
# The PyPI negative of demo-bash-operator (Stage 6i step 5). The worker has no route to the
# internet, so both reaches are expected to fail within seconds. The exit status is the
# reading: 1 when nothing answered, the expected outcome, and 0 when something did.
# A BashOperator renders a .sh file through Jinja before running it: no double braces and
# no brace-hash in this file.
set -u

reached=0

start=$(date +%s)
if python3 - <<'EOF'
import urllib.request

urllib.request.urlopen("https://pypi.org/simple/", timeout=10)
EOF
then
  echo "urllib: pypi.org ANSWERED"
  reached=1
else
  echo "urllib: no answer from pypi.org"
fi
echo "urllib: $(( $(date +%s) - start )) s"

start=$(date +%s)
if python3 -m pip download --no-deps --timeout 10 --retries 0 -d /tmp/reach-pypi six; then
  echo "pip: pypi.org ANSWERED"
  reached=1
else
  echo "pip: download failed"
fi
echo "pip: $(( $(date +%s) - start )) s"

if [ "$reached" -eq 1 ]; then
  exit 0
fi
exit 1
