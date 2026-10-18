#!/usr/bin/env bash
# The PyPI negative of demo-bash-operator (Stage 6i step 5). The worker has no route to the
# internet, so both reaches are expected to fail: within seconds here, where the DNS Firewall
# refuses the name, and after the connect timeouts where the name resolves (errno 101 after
# 43 s and 64 s outside this lab, 2026-10-12). The exit status is the
# reading: 1 when nothing answered, the expected outcome, and 0 when something did. Each
# failure prints its cause on one line, since a resolver error and a timeout are different
# readings. demo-bash-operator.probe.yaml runs the same commands inline, with no Code object.
# A BashOperator renders a .sh file through Jinja before running it: no double braces and
# no brace-hash in this file.
set -u

echo "proxy: $(env | grep -i -o -E '^(https?|no|all)_proxy=' | tr '\n' ' ')"
reached=0

start=$(date +%s)
if python3 - <<'PY'
import socket
import sys
import urllib.request

try:
    print("resolve: pypi.org ->", socket.getaddrinfo("pypi.org", 443)[0][4][0])
except OSError as e:
    print("resolve: pypi.org failed:", repr(e))
try:
    urllib.request.urlopen("https://pypi.org/simple/", timeout=10)
except OSError as e:
    print("urllib:", repr(e))
    sys.exit(1)
PY
then
  echo "urllib: pypi.org ANSWERED"
  reached=1
else
  echo "urllib: no answer from pypi.org"
fi
echo "urllib: $(( $(date +%s) - start )) s"

python3 -m pip --version
log=$(mktemp)
start=$(date +%s)
python3 -m pip download -vvv --no-deps --timeout 10 --retries 0 -d "$(mktemp -d)" six > "$log" 2>&1
rc=$?
grep -E 'Looking in indexes|Could not fetch URL|Successfully downloaded|^ERROR' "$log"
if [ "$rc" -eq 0 ]; then
  echo "pip: pypi.org ANSWERED"
  reached=1
else
  echo "pip: download failed, exit $rc"
fi
echo "pip: $(( $(date +%s) - start )) s"

if [ "$reached" -eq 1 ]; then
  exit 0
fi
exit 1
