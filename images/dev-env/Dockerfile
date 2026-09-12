# awsds dev-env - the SMUS custom image (BYOI). Stage 6 step 5.0; Stage 8 step 1 owns it after.
#
# This is the runtime every notebook and every Unified Studio project app runs on, and it is
# the one artifact in this plan that reaches an account without a pipeline - once, by hand, at
# bootstrap (Stage 6 step 5.0), replaced by Stage 8's pipeline building this same file.
#
# FROM `base`, not from the distribution directly, because of D17: the application images are
# `FROM base:<pinned tag>`, so "the runtime the code runs on is the runtime it was written
# against" is true BY CONSTRUCTION only if this image shares that ancestor.
# images/base/Dockerfile carries the argument and the SMUS BYOI constraint that forced base's
# own root; read it before changing either.
#
# What this image adds, and why it is three languages (docs/plan/architecture.md §4.3): the
# environment must support Python, Julia, Rust and R, and CodeArtifact covers only two of them
# - PyPI and crates.io. Julia and CRAN have no external connection, so under egress design B
# (no NAT at all) this image is the delivery mechanism for them. Step 6.1 measures the cost: an
# ad-hoc `pip install` under design A becomes a merge request, a build, a scan and a steward
# approval under design B.
#
# No ENTRYPOINT, no CMD - see images/base/Dockerfile §the SMUS BYOI rule. The base's
# /usr/local/bin/_entrypoint.sh must survive.
#
# Nothing is compiled here. Julia, rustup and the R environment are all prebuilt binary
# downloads, which is what keeps an amd64 build under emulation on an Apple Silicon laptop
# slow rather than impossible (images/README.md).
#
# Build (after base, amd64):
#   docker buildx build --platform linux/amd64 -t awsds/dev-env:local images/dev-env

ARG BASE_IMAGE=awsds/base
ARG BASE_TAG=local
FROM ${BASE_IMAGE}:${BASE_TAG}

# Re-declared for the same reason images/base/Dockerfile re-declares its three: an ARG stated
# before FROM does not survive it, and both are read back in section 5.
ARG BASE_IMAGE
ARG BASE_TAG

# ------------------------------------------------------------------------------- the pins
#
# Every version and every checksum below was read on 2026-08-21 from the publisher's own
# metadata, not from a memory of what is current:
#
#   Julia    julialang-s3.julialang.org/bin/versions.json - the sha256 is that file's, for
#            the linux/x86_64 archive of 1.12.7
#   rustup   static.rust-lang.org/rustup/archive/1.29.0/x86_64-unknown-linux-gnu/rustup-init.sha256
#   Rust     static.rust-lang.org/dist/channel-rust-stable.toml (1.98.0, 2026-08-18)
#
# A download without a checksum is an unsigned dependency, and this image is the runtime the
# whole estate shares. Both archives are verified before anything is executed.
ARG JULIA_VERSION=1.12.7
ARG JULIA_SHA256=4e7e9e776634d24835250de67cde39b0d4af15bc432eb20697e6be6c28ea69e8
ARG RUSTUP_VERSION=1.29.0
ARG RUSTUP_SHA256=4acc9acc76d5079515b46346a485974457b5a79893cfb01112423c89aeb5aa10
ARG RUST_TOOLCHAIN=1.98.0

USER root

# ------------------------------------------------------------------------------ 1. Python
#
# A second Python, complete and separate, with its own kernel in the Launcher. The
# distribution's environment is left exactly as it ships (the user's decision, 2026-09-10): no
# package of ours goes into it, its `python3` kernelspec is not touched, and nothing of ours
# joins PATH ahead of its interpreter. A space therefore offers two Python kernels, and only
# the second one is ours to curate.
#
# uv owns this environment end to end: it installs the interpreter (a managed CPython under
# /opt/awsds/python, not conda's) and resolves the packages from python/pyproject.toml through
# the committed python/uv.lock. `--frozen` is what makes the lock load-bearing - it refuses a
# lock that disagrees with the pyproject rather than resolving something nobody reviewed, so a
# dependency added without `uv lock` fails the build instead of arriving unreviewed.
#
# UV_PYTHON_DOWNLOADS is `never` in the base image, by decision, so that a user's `uv run`
# cannot silently pull an interpreter that is not the distribution's. This one command lifts
# it - the base's own comment names that escape hatch - and the download happens at build time,
# on the build plane, never in a space.
#
# Under design B the index is switched at build time, not here:
# `--build-arg UV_DEFAULT_INDEX=<the CodeArtifact pypi URL>` and no line of pyproject.toml
# changes. The lock's hashes stay valid; CodeArtifact serves the same artifacts.
#
# UV_NO_CACHE is what keeps the layer the size of the environment. Measured 2026-09-11 on the first
# build: uv unpacks every wheel into /root/.cache/uv and then materialises it into the venv, and
# both live in the same layer - 5.4 GB of cache beside a 5.2 GB environment, in a layer of 10.7 GB.
# A later `rm -rf` would return nothing, since the bytes are already committed to this layer; the
# cache has to never be written. The build is a single resolve, so nothing is lost by it.
ARG PYTHON_VERSION=3.13
ARG UV_DEFAULT_INDEX=""

ENV AWSDS_PYTHON_ENV=/opt/awsds/venv \
    AWSDS_PYTHON_HOME=/opt/awsds/python

COPY python/pyproject.toml python/uv.lock /opt/awsds/python-project/

RUN set -eu; \
    command -v uv >/dev/null 2>&1 \
      || { echo "FATAL: no uv on PATH. The base image installs it (images/base section 3)." >&2; exit 1; }; \
    echo "== uv $(uv --version), asking for CPython ${PYTHON_VERSION}"; \
    export UV_PYTHON_DOWNLOADS=automatic; \
    export UV_PYTHON_INSTALL_DIR="${AWSDS_PYTHON_HOME}"; \
    export UV_PROJECT_ENVIRONMENT="${AWSDS_PYTHON_ENV}"; \
    export UV_NO_CACHE=1; \
    if [ -n "${UV_DEFAULT_INDEX}" ]; then export UV_DEFAULT_INDEX; else unset UV_DEFAULT_INDEX; fi; \
    uv python install "${PYTHON_VERSION}"; \
    cd /opt/awsds/python-project; \
    uv sync --frozen --no-dev --python "${PYTHON_VERSION}"; \
    "${AWSDS_PYTHON_ENV}/bin/python" -m ipykernel install \
      --prefix=/opt/conda --name awsds-python --display-name "Python (awsds dev-env)"; \
    spec=/opt/conda/share/jupyter/kernels/awsds-python/kernel.json; \
    test -f "${spec}" \
      || { echo "FATAL: ipykernel wrote no kernelspec where the distribution's jupyter reads." >&2; exit 1; }; \
    grep -q "${AWSDS_PYTHON_ENV}/bin/python" "${spec}" \
      || { echo "FATAL: the kernelspec names an interpreter other than this environment's:" >&2; \
           cat "${spec}" >&2; exit 1; }; \
    if grep -rq "${AWSDS_PYTHON_ENV}" /opt/conda/share/jupyter/kernels --exclude-dir=awsds-python; then \
      echo "FATAL: a kernelspec that is not ours now names this environment." >&2; \
      echo "  The distribution's kernels are left as they ship - read section 1's comment." >&2; \
      exit 1; \
    fi; \
    echo "== kernels the distribution's jupyter will offer:"; \
    ls /opt/conda/share/jupyter/kernels; \
    "${AWSDS_PYTHON_ENV}/bin/python" -c 'import sys; print("== awsds python", sys.version)'; \
    chmod -R a+rX /opt/awsds /opt/conda/share/jupyter/kernels/awsds-python

# --------------------------------------------------------------------------------- 2. Julia
#
# The depot is shared and read-only, and the search path puts the user's first. A depot under
# /opt is baked into the image and identical for everyone; a Pkg operation a user runs in a
# notebook must not need to write there, so JULIA_DEPOT_PATH lists the home depot first (Pkg
# writes to the first entry) and the shared one second (Pkg reads from all of them). The home
# depot lives on the space's EBS volume at /home/sagemaker-user, which is where a space's
# state is meant to live.
#
# What the shared depot carries is package sources, artifacts, the registry and the resolved
# environment - not precompilation output. Since Julia 1.9 a precompilation cache is a package
# image carrying native code, and Julia accepts one only when the CPU features recorded in it
# are a subset of the running CPU's. JULIA_CPU_TARGET is unset here on purpose, so the compiler
# targets the machine it runs on: baking a cache would tie it to the build host's CPU family,
# and pinning a portable target would cost the optimisations the user's own CPU offers. The
# build therefore discards its own precompilation output at the end of the package RUN below,
# and the first `using` in a space compiles for that space's CPU, into the home depot on its
# EBS volume (per space, per user - a new space compiles again). The user's decision, 2026-09-11.
ENV JULIA_ROOT=/opt/julia \
    JULIA_SHARED_DEPOT=/opt/julia-depot
ENV JULIA_DEPOT_PATH=/home/sagemaker-user/.julia:${JULIA_SHARED_DEPOT} \
    PATH=${JULIA_ROOT}/bin:${PATH}

RUN set -eu; \
    minor="$(echo "${JULIA_VERSION}" | cut -d. -f1,2)"; \
    url="https://julialang-s3.julialang.org/bin/linux/x64/${minor}/julia-${JULIA_VERSION}-linux-x86_64.tar.gz"; \
    echo "== julia ${JULIA_VERSION} from ${url}"; \
    curl -fsSL "${url}" -o /tmp/julia.tar.gz; \
    echo "${JULIA_SHA256}  /tmp/julia.tar.gz" | sha256sum -c -; \
    mkdir -p "${JULIA_ROOT}"; \
    tar -xzf /tmp/julia.tar.gz -C "${JULIA_ROOT}" --strip-components=1; \
    rm -f /tmp/julia.tar.gz; \
    julia --version

# The package set, and the kernel.
#
# The kernelspec is relocated and then asserted, because where IJulia puts it depends on what
# it finds: `installkernel` delegates to `jupyter kernelspec install --user` when a `jupyter`
# is on the PATH - and there is one, the base environment's - which lands the spec in ROOT's
# home, where `sagemaker-user` never looks. JUPYTER_DATA_DIR is set for the branch where it
# does not delegate. A kernel only root can see is a kernel nobody sees, and it fails silently
# as "Julia is missing from the launcher", so the build fails here instead.
#
# Pkg.precompile() stays although this RUN discards its output at the end: it is the build's
# only proof that this package set compiles at all, and without it a package that does not
# build is discovered by a scientist in a notebook. The `du -sh` before the removal prints what
# the discarded cache weighed, so the build log answers the size question without a second run.
# The removal names the shared depot's cache and nothing else - /opt/julia/share/julia/compiled
# holds the distribution's own stdlib caches, which ship with the portable target the official
# binaries are built with and must stay.
COPY julia/packages.txt /tmp/awsds-julia-packages.txt
RUN set -eu; \
    export JULIA_DEPOT_PATH="${JULIA_SHARED_DEPOT}"; \
    export JULIA_PROJECT="${JULIA_SHARED_DEPOT}/environments/awsds"; \
    export JUPYTER_DATA_DIR=/opt/conda/share/jupyter; \
    mkdir -p "${JULIA_PROJECT}" /opt/conda/share/jupyter/kernels; \
    pkgs="$(grep -vE '^[[:space:]]*(#|$)' /tmp/awsds-julia-packages.txt \
            | tr -d '\r' | sed 's/[[:space:]]*$//' | sed 's/.*/"&"/' | paste -sd, -)"; \
    echo "== julia packages: ${pkgs}"; \
    julia -e "using Pkg; Pkg.add([${pkgs}]); Pkg.precompile()"; \
    julia -e 'using IJulia; IJulia.installkernel("Julia", env=Dict("JULIA_PROJECT" => ENV["JULIA_PROJECT"]))'; \
    julia -e 'using Pkg; Pkg.status()'; \
    for k in $(find /root /home/sagemaker-user -type d -path '*/jupyter/kernels/julia-*' 2>/dev/null || true); do \
      echo "relocating kernelspec ${k} into the shared prefix"; \
      mv "${k}" /opt/conda/share/jupyter/kernels/; \
    done; \
    ls -d /opt/conda/share/jupyter/kernels/julia-* >/dev/null 2>&1 \
      || { echo "FATAL: IJulia installed no kernelspec the shared prefix can see." >&2; exit 1; }; \
    grep -q "${JULIA_PROJECT}" /opt/conda/share/jupyter/kernels/julia-*/kernel.json \
      || { echo "FATAL: the Julia kernelspec does not name the project this build resolved." >&2; \
           echo "  A kernel on the default environment would ignore julia/packages.txt." >&2; \
           cat /opt/conda/share/jupyter/kernels/julia-*/kernel.json >&2; exit 1; }; \
    rm -f /tmp/awsds-julia-packages.txt; \
    du -sh "${JULIA_SHARED_DEPOT}/compiled"; \
    rm -rf "${JULIA_SHARED_DEPOT}/compiled"; \
    chmod -R a+rX "${JULIA_SHARED_DEPOT}" "${JULIA_ROOT}" /opt/conda/share/jupyter/kernels

# ------------------------------------------------------------------------------------- 3. R
#
# Its own conda environment, never the base one - r/conda-packages.txt carries the reasoning.
# The kernelspec is written by hand from kernels/ir/kernel.json rather than by
# IRkernel::installspec(), because installspec resolves the destination from whichever
# `jupyter` is on the PATH of the environment it runs in - and `jupyter` is not in the R
# environment. A three-line JSON naming an absolute interpreter is the smaller moving part.
COPY r/conda-packages.txt /tmp/awsds-r-packages.txt
COPY kernels/ir /opt/conda/share/jupyter/kernels/ir
RUN set -eu; \
    grep -vE '^[[:space:]]*(#|$)' /tmp/awsds-r-packages.txt | tr -d '\r' > /tmp/awsds-r-specs.txt; \
    echo "== R environment specs:"; cat /tmp/awsds-r-specs.txt; \
    micromamba create -y -p /opt/conda/envs/r -c conda-forge --file /tmp/awsds-r-specs.txt; \
    micromamba clean -y --all; \
    rm -f /tmp/awsds-r-packages.txt /tmp/awsds-r-specs.txt; \
    test -x /opt/conda/envs/r/bin/R || { echo "FATAL: no R interpreter at the path kernels/ir/kernel.json names" >&2; exit 1; }; \
    /opt/conda/envs/r/bin/R --version; \
    /opt/conda/envs/r/bin/R --no-echo -e 'library(IRkernel); cat("IRkernel ", as.character(packageVersion("IRkernel")), "\n")'; \
    chmod -R a+rX /opt/conda/envs/r /opt/conda/share/jupyter/kernels/ir

# ---------------------------------------------------------------------------------- 4. Rust
#
# No Jupyter kernel, on purpose. Rust here is a toolchain for building things - the ecosystem
# open question 5 asks about against CodeArtifact's `crates` repository - not a notebook
# language; the one kernel that exists (evcxr) compiles on install and would be the only
# compilation in this image.
#
# CARGO_HOME is deliberately left unset so it defaults to the user's ~/.cargo at runtime: the
# registry cache and anything `cargo install` produces then land on the space's EBS volume,
# writable, instead of failing against a read-only /opt. The rustup shims come from PATH and
# resolve the toolchain through RUSTUP_HOME, which is what makes that split work.
#
# The CodeArtifact hook is step 5.2's, not this file's: cargo reads its registry configuration
# from $CARGO_HOME/config.toml (i.e. the user's home) or from the environment, so pointing it
# at the `crates` repository is a runtime setting on the project, not a build-time layer here.
#
# rust-src is the third component because `minimal` does not carry it and rust-analyzer cannot
# index the standard library without it. Measured 2026-09-11 in a remote VS Code session on
# `default-v0.2.0`: `ERROR can't load standard library, try installing rust-src
# sysroot_path=/opt/rust/rustup/toolchains/1.98.0-x86_64-unknown-linux-gnu`, repeated per
# analysis run, with no visible effect on the user's own crate - so the loss is completion,
# hover and go-to-definition for `std`, and it announces itself only in the extension's log.
# It cannot be repaired from a space that matters: RUSTUP_HOME is under /opt, root-owned and
# `a+rX`, so `rustup component add` needs sudo and the result dies with the container.
ENV RUSTUP_HOME=/opt/rust/rustup \
    PATH=/opt/rust/cargo/bin:${PATH}

RUN set -eu; \
    url="https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init"; \
    echo "== rustup ${RUSTUP_VERSION} from ${url}"; \
    curl -fsSL "${url}" -o /tmp/rustup-init; \
    echo "${RUSTUP_SHA256}  /tmp/rustup-init" | sha256sum -c -; \
    chmod +x /tmp/rustup-init; \
    CARGO_HOME=/opt/rust/cargo /tmp/rustup-init -y --no-modify-path --profile minimal \
        --default-toolchain "${RUST_TOOLCHAIN}" --component rustfmt --component clippy \
        --component rust-src; \
    rm -f /tmp/rustup-init; \
    chmod -R a+rX /opt/rust; \
    rustc --version; \
    cargo --version

# ------------------------------------------------------- 5. what the image says about itself
#
# The three runtimes are read back here so that a build log carries them, and so that Stage 8
# step 1.2's smoke test has an in-image equivalent to assert against.
RUN set -eu; \
    { echo "base image      : ${BASE_IMAGE}:${BASE_TAG}"; \
      echo "python (base)   : $(python --version 2>&1)"; \
      echo "python (awsds)  : $(${AWSDS_PYTHON_ENV}/bin/python --version 2>&1) at ${AWSDS_PYTHON_ENV}"; \
      echo "uv              : $(uv --version)"; \
      echo "julia           : $(julia --version)"; \
      echo "R               : $(/opt/conda/envs/r/bin/R --version | head -1)"; \
      echo "rust            : $(rustc --version)"; \
    } | tee /opt/awsds-runtimes.txt; \
    echo "== jupyter kernels =="; \
    jupyter kernelspec list

LABEL org.opencontainers.image.title="awsds-dev-env" \
      org.opencontainers.image.description="The SMUS custom image (BYOI): the shared ancestor plus Julia, R and Rust." \
      org.opencontainers.image.source="https://github.com/felipenoris/AWS-DataScience" \
      org.awsds.stage="6.5.0" \
      org.awsds.julia="${JULIA_VERSION}" \
      org.awsds.rust="${RUST_TOOLCHAIN}"

# ------------------------------------------------- 6. the estate's proxy contract (6d decision 8)
#
# Every internet call from a space crosses the Squid proxy (D38), and NO_PROXY is what keeps AWS calls
# on the VPC endpoints. A proxy without its bypass list does not fail: the call goes out through the
# hub as a public one, with no aws:SourceVpc and no aws:SourceVpce, so the perimeter is lost silently.
#
# The list below is Sandbox's, read on 2026-09-10 (50 entries). It goes stale when that account's
# endpoint set changes - a stale image is a working image with a hole, and `./aws/devenv.py` is what
# reports the difference. Refresh it with:
#
#   AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/egress output -raw no_proxy
#
# and rebuild. Eight of the names are not derivable from a service token, which is why the list is
# read from the slice that builds the endpoints rather than composed. Another account overrides it
# with --build-arg NO_PROXY_LIST=... ; it is one long line because a continuation would put leading
# whitespace inside an entry, and an entry with a space matches nothing.
#
# The section is last in the file: an ENV set earlier would apply to every RUN above it, and those
# build in VPC-SharedServices, whose endpoint set is not this one.
ARG PROXY_URL=http://proxy.awsds.internal:3128
ARG NO_PROXY_LIST=".awsds-pages.internal,.awsds.internal,.dkr-ecr.us-west-2.on.aws,.dkr.ecr.us-west-2.amazonaws.com,.studio.sagemaker.us-west-2.app.aws,.studio.us-west-2.sagemaker.aws,127.0.0.1,169.254.169.254,169.254.170.2,api.ecr.us-west-2.amazonaws.com,api.sagemaker.us-west-2.amazonaws.com,api.sagemaker.us-west-2.api.aws,athena.us-west-2.amazonaws.com,athena.us-west-2.api.aws,datazone.us-west-2.amazonaws.com,datazone.us-west-2.api.aws,dkr-ecr.us-west-2.on.aws,dkr.ecr.us-west-2.amazonaws.com,dynamodb.dualstack.us-west-2.amazonaws.com,dynamodb.us-west-2.amazonaws.com,ec2.us-west-2.amazonaws.com,ec2.us-west-2.api.aws,ec2messages.us-west-2.amazonaws.com,ecr.us-west-2.api.aws,glue.us-west-2.amazonaws.com,glue.us-west-2.api.aws,kms.us-west-2.amazonaws.com,kms.us-west-2.api.aws,lakeformation.us-west-2.amazonaws.com,lakeformation.us-west-2.api.aws,localhost,logs.us-west-2.amazonaws.com,logs.us-west-2.api.aws,runtime.sagemaker.us-west-2.amazonaws.com,runtime.sagemaker.us-west-2.api.aws,s3.dualstack.us-west-2.amazonaws.com,s3.us-west-2.amazonaws.com,s3tables.us-west-2.amazonaws.com,s3tables.us-west-2.api.aws,secretsmanager.us-west-2.amazonaws.com,ssm.us-west-2.amazonaws.com,ssm.us-west-2.api.aws,ssmmessages.us-west-2.amazonaws.com,ssmmessages.us-west-2.api.aws,streaming-logs.us-west-2.amazonaws.com,streaming-logs.us-west-2.api.aws,sts.us-west-2.amazonaws.com,sts.us-west-2.api.aws,studio.sagemaker.us-west-2.app.aws,studio.us-west-2.sagemaker.aws"

# The variables alone are not enough, measured 2026-09-08 (6d step 3.1): `sudo` resets the
# environment, so `apt` ran with no proxy and failed to resolve a name that is on the plane. apt gets
# its own file, and sudoers keeps the six names across `sudo` for everything else.
# /opt/awsds-proxy.txt is what makes a stale image readable from inside a space.
RUN set -eu; \
    test -n "${NO_PROXY_LIST}" || { echo "NO_PROXY_LIST is empty - an image with a proxy and no bypass list loses the perimeter"; exit 1; }; \
    printf 'Acquire::http::Proxy "%s";\nAcquire::https::Proxy "%s";\n' "${PROXY_URL}" "${PROXY_URL}" \
      > /etc/apt/apt.conf.d/01proxy; \
    printf 'Defaults env_keep += "http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY"\n' \
      > /etc/sudoers.d/awsds-proxy; \
    chmod 0440 /etc/sudoers.d/awsds-proxy; \
    if command -v visudo >/dev/null 2>&1; then visudo -cf /etc/sudoers.d/awsds-proxy; fi; \
    { echo "proxy           : ${PROXY_URL}"; \
      echo "no_proxy entries: $(printf '%s' "${NO_PROXY_LIST}" | awk -F, '{print NF}')"; \
      echo "no_proxy sha256 : $(printf '%s' "${NO_PROXY_LIST}" | sha256sum | cut -c1-16)"; \
    } | tee /opt/awsds-proxy.txt

ENV http_proxy="${PROXY_URL}" \
    https_proxy="${PROXY_URL}" \
    HTTP_PROXY="${PROXY_URL}" \
    HTTPS_PROXY="${PROXY_URL}" \
    no_proxy="${NO_PROXY_LIST}" \
    NO_PROXY="${NO_PROXY_LIST}"

USER $MAMBA_USER
