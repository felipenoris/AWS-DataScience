# The release smoke test (AWS-DataScience's Stage 8 step 1.2, from Stage 7 step 2.6's trust check):
# built FROM a freshly pushed dev-env and never pushed. The `check` stage runs the checks inside the
# image as its own user; the `manifests` stage holds what they wrote, which the pipeline exports as the
# release gate's evidence:
#
#   buildctl build --local context=smoke --local dockerfile=smoke --no-cache \
#     --opt build-arg:DEV_ENV=<registry>/awsds-prod-ecr-dev-env@<digest> \
#     --opt build-arg:PYTHON_VERSION=<..> --opt build-arg:JULIA_VERSION=<..> \
#     --opt build-arg:RUST_TOOLCHAIN=<..> --opt target=manifests --output type=local,dest=manifests
#
# What fails the build: a client that does not trust the internal root, a runtime at another version
# than the recipe pins, a key library of the house environment that does not import, a CI/CD CLI by its
# name that is not the house environment's after the activation a space runs. The image's proxy
# environment is read from /opt/awsds-proxy.txt and never from `printenv`: the build's proxy arguments
# shadow the image's own ENV inside a RUN, as a docker client's `proxies` block does in a container.
ARG DEV_ENV
FROM ${DEV_ENV} AS check

ARG GITLAB_URL=https://gitlab.awsds.internal
ARG PYTHON_VERSION
ARG JULIA_VERSION
ARG RUST_TOOLCHAIN

RUN mkdir -p /tmp/out

# curl: exits non-zero on a certificate it cannot verify, so the assignment fails the RUN.
RUN set -eu; \
    r="$(curl -sS -o /dev/null -w '%{http_code} ssl_verify=%{ssl_verify_result}' "${GITLAB_URL}/users/sign_in")"; \
    echo "curl ($(command -v curl)): ${r}" | tee -a /tmp/out/trust.txt

# git: an anonymous ls-remote of a private project fails either way; the message says which wall it
# hit, and only a certificate wall is a failure here.
RUN set -eu; \
    out="$(GIT_TERMINAL_PROMPT=0 git ls-remote "${GITLAB_URL}/awsds/dev-env.git" 2>&1 || true)"; \
    echo "git ($(command -v git)): ${out}" | tee -a /tmp/out/trust.txt; \
    if echo "${out}" | grep -qiE 'certificate|ssl'; then \
      echo "FATAL: git does not trust the internal root." >&2; exit 1; \
    fi

# Both Python environments, through the standard library (OpenSSL's default paths) and through
# requests (certifi's bundle unless REQUESTS_CA_BUNDLE says otherwise).
RUN set -eu; \
    for py in /opt/conda/bin/python "${AWSDS_PYTHON_ENV}/bin/python"; do \
      "${py}" -c "import sys, urllib.request; print(sys.executable, 'urllib', urllib.request.urlopen(sys.argv[1], timeout=20).status)" "${GITLAB_URL}/users/sign_in"; \
      "${py}" -c "import sys, requests; print(sys.executable, 'requests', requests.get(sys.argv[1], timeout=20).status_code)" "${GITLAB_URL}/users/sign_in"; \
    done | tee -a /tmp/out/trust.txt

# The runtimes at the versions the recipe pins: the pipeline reads each ARG out of dev-env/Dockerfile,
# and the image's own record of what it built is /opt/awsds-runtimes.txt.
RUN set -eu; \
    py="$("${AWSDS_PYTHON_ENV}/bin/python" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"; \
    jl="$(julia --version | awk '{print $3}')"; \
    rs="$(rustc --version | awk '{print $2}')"; \
    echo "house python ${py} (pinned ${PYTHON_VERSION}), julia ${jl} (${JULIA_VERSION}), rust ${rs} (${RUST_TOOLCHAIN})"; \
    test "${py}" = "${PYTHON_VERSION}" || { echo "FATAL: the house Python is ${py}" >&2; exit 1; }; \
    test "${jl}" = "${JULIA_VERSION}" || { echo "FATAL: Julia is ${jl}" >&2; exit 1; }; \
    test "${rs}" = "${RUST_TOOLCHAIN}" || { echo "FATAL: Rust is ${rs}" >&2; exit 1; }; \
    cp /opt/awsds-runtimes.txt /tmp/out/runtimes.txt; \
    cp /opt/awsds-proxy.txt /tmp/out/proxy.txt

# The CI/CD CLI by its name, read after `micromamba activate base`, as a space's server and terminal
# read it. A RUN here activates nothing (MAMBA_DOCKERFILE_ACTIVATE is an ARG of the distribution's own
# build), so a check without the activation reads the image's ENV and passes in an image whose spaces
# resolve the distribution's CLI. The activation runs before `set -u`, as in the start scripts.
RUN set -e; \
    eval "$(micromamba shell hook --shell=bash)"; \
    micromamba activate base; \
    set -u; \
    cli="$(command -v aws-smus-cicd-cli)"; \
    target="$(readlink -f "${cli}")"; \
    reported="$(aws-smus-cicd-cli --version)"; \
    house="$("${AWSDS_PYTHON_ENV}/bin/python" -c 'from importlib.metadata import version; print(version("aws-smus-cicd-cli"))')"; \
    echo "aws-smus-cicd-cli by its name: ${cli} -> ${target}, '${reported}'; the house environment carries ${house}" \
      | tee /tmp/out/cicd-cli.txt; \
    case "${target}" in \
      "${AWSDS_PYTHON_ENV}/bin/"*) ;; \
      *) echo "FATAL: the CLI by its name is ${target}, not the house environment's" >&2; exit 1 ;; \
    esac; \
    test "${reported}" = "aws-smus-cicd-cli ${house}" \
      || { echo "FATAL: the CLI by its name reports '${reported}'" >&2; exit 1; }

# The house environment's key libraries, each imported and its version written down.
RUN set -eu; \
    "${AWSDS_PYTHON_ENV}/bin/python" -c "import importlib; [print(m, getattr(importlib.import_module(m), '__version__', '?')) for m in ('numpy', 'pandas', 'scipy', 'pyarrow', 'sklearn', 'matplotlib', 'boto3', 's3fs', 'redshift_connector', 'torch', 'tensorflow', 'xgboost', 'mlflow', 'ipykernel')]" \
      | tee /tmp/out/imports.txt

# What the release carries, for the steward's review: each environment's packages at their versions.
RUN set -eu; \
    uv pip list --python "${AWSDS_PYTHON_ENV}/bin/python" --format freeze > /tmp/out/python-awsds.txt; \
    /opt/conda/bin/python -m pip list --format=freeze > /tmp/out/python-conda.txt; \
    /opt/conda/envs/r/bin/R --no-echo -e 'ip <- installed.packages()[, c("Package", "Version")]; write.table(ip, sep = "==", quote = FALSE, row.names = FALSE, col.names = FALSE)' > /tmp/out/r.txt; \
    JULIA_PROJECT=/opt/julia-depot/environments/awsds julia -e 'using Pkg; Pkg.status()' > /tmp/out/julia.txt; \
    wc -l /tmp/out/*.txt

FROM scratch AS manifests
COPY --from=check /tmp/out/ /
