# The trust smoke test (Stage 7 step 2.6): built FROM a freshly pushed dev-env and discarded, never
# pushed. Every RUN reads https://gitlab.awsds.internal, which only the internal root certifies,
# through the image's own trust configuration (base section 5), from a host where the name
# resolves - the build runner. A certificate error fails the build; an HTTP status does not, since
# none of these clients signs in.
#
#   buildctl build --local context=images/smoke --local dockerfile=images/smoke --no-cache \
#     --opt build-arg:DEV_ENV=<registry>/awsds-prod-ecr-dev-env:<tag>
ARG DEV_ENV
FROM ${DEV_ENV}

ARG GITLAB_URL=https://gitlab.awsds.internal

# curl: exits non-zero on a certificate it cannot verify, so the assignment fails the RUN.
RUN set -eu; \
    r="$(curl -sS -o /dev/null -w '%{http_code} ssl_verify=%{ssl_verify_result}' "${GITLAB_URL}/users/sign_in")"; \
    echo "curl ($(command -v curl)): ${r}"

# git: an anonymous ls-remote of a private project fails either way; the message says which wall it
# hit, and only a certificate wall is a failure here.
RUN set -eu; \
    out="$(GIT_TERMINAL_PROMPT=0 git ls-remote "${GITLAB_URL}/awsds/dev-env.git" 2>&1 || true)"; \
    echo "git ($(command -v git)): ${out}"; \
    if echo "${out}" | grep -qiE 'certificate|ssl'; then \
      echo "FATAL: git does not trust the internal root." >&2; exit 1; \
    fi

# Both Python environments, through the standard library (OpenSSL's default paths) and through
# requests (certifi's bundle unless REQUESTS_CA_BUNDLE says otherwise).
RUN set -eu; \
    for py in /opt/conda/bin/python "${AWSDS_PYTHON_ENV}/bin/python"; do \
      "${py}" -c "import sys, urllib.request; print(sys.executable, 'urllib', urllib.request.urlopen(sys.argv[1], timeout=20).status)" "${GITLAB_URL}/users/sign_in"; \
      "${py}" -c "import sys, requests; print(sys.executable, 'requests', requests.get(sys.argv[1], timeout=20).status_code)" "${GITLAB_URL}/users/sign_in"; \
    done
