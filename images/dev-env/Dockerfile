# awsds dev-env - THE SMUS CUSTOM IMAGE (BYOI). Stage 6 step 5.0; Stage 8 step 1 owns it after.
#
# This is the runtime every notebook and every Unified Studio project app runs on, and it is
# the one artifact in this plan that reaches an account without a pipeline - once, by hand, at
# bootstrap (Stage 6 step 5.0), replaced by Stage 8's pipeline building this same file.
#
# FROM `base`, NOT FROM THE DISTRIBUTION DIRECTLY, and that is D17 rather than tidiness: the
# application images are `FROM base:<pinned tag>`, so the only way "the runtime the code runs
# on is the runtime it was written against" is true BY CONSTRUCTION is for this image to share
# that ancestor. images/base/Dockerfile carries the argument and the SMUS BYOI constraint that
# forced base's own root; read it before changing either.
#
# WHAT THIS IMAGE ADDS, AND WHY IT IS THREE LANGUAGES AND NOT ONE (docs/plan/architecture.md
# §4.3): the environment must support Python, Julia, Rust and R, and CodeArtifact covers only
# two of them - PyPI and crates.io. Julia and CRAN have no external connection, so under
# egress design B (no NAT at all) THIS IMAGE IS THE DELIVERY MECHANISM for them. That is the
# reframing design B rests on, and step 6.1 measures its cost: an ad-hoc `pip install` under
# design A becomes a merge request, a build, a scan and a steward approval under design B.
#
# NO ENTRYPOINT, NO CMD - see images/base/Dockerfile §the SMUS BYOI rule. The base's
# /usr/local/bin/_entrypoint.sh must survive.
#
# NOTHING IS COMPILED HERE. Julia, rustup and the R environment are all prebuilt binary
# downloads, which is what keeps an amd64 build under emulation on an Apple Silicon laptop
# slow rather than impossible (images/README.md).
#
# BUILD (after base, amd64):
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
# A DOWNLOAD WITHOUT A CHECKSUM IS AN UNSIGNED DEPENDENCY, and this image is the runtime the
# whole estate shares. Both archives are verified before anything is executed.
ARG JULIA_VERSION=1.12.7
ARG JULIA_SHA256=4e7e9e776634d24835250de67cde39b0d4af15bc432eb20697e6be6c28ea69e8
ARG RUSTUP_VERSION=1.29.0
ARG RUSTUP_SHA256=4acc9acc76d5079515b46346a485974457b5a79893cfb01112423c89aeb5aa10
ARG RUST_TOOLCHAIN=1.98.0

USER root

# ------------------------------------------------------------------------------ 1. Python
#
# On top of the distribution's stack, never re-stating it - python/requirements.txt says why
# it is empty today. `--requirement` on an all-comment file is a no-op, which is the point:
# the seam exists before it has content.
COPY python/requirements.txt /tmp/awsds-requirements.txt
RUN set -eu; \
    pip install --no-cache-dir --requirement /tmp/awsds-requirements.txt; \
    rm -f /tmp/awsds-requirements.txt

# --------------------------------------------------------------------------------- 2. Julia
#
# THE DEPOT IS SHARED AND READ-ONLY, AND THE SEARCH PATH PUTS THE USER'S FIRST. A depot under
# /opt is baked into the image and identical for everyone; a Pkg operation a user runs in a
# notebook must not need to write there, so JULIA_DEPOT_PATH lists the home depot first (Pkg
# writes to the first entry) and the shared one second (Pkg reads from all of them). The home
# depot lives on the space's EBS volume at /home/sagemaker-user, which is where a space's
# state is meant to live.
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
# THE KERNELSPEC IS RELOCATED AND THEN ASSERTED, because where IJulia puts it depends on what
# it finds: `installkernel` delegates to `jupyter kernelspec install --user` when a `jupyter`
# is on the PATH - and there is one, the base environment's - which lands the spec in ROOT's
# home, where `sagemaker-user` never looks. JUPYTER_DATA_DIR is set for the branch where it
# does not delegate. A kernel only root can see is a kernel nobody sees, and it fails silently
# as "Julia is missing from the launcher", so the build fails here instead.
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
    rm -f /tmp/awsds-julia-packages.txt; \
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
# NO JUPYTER KERNEL, ON PURPOSE. Rust here is a toolchain for building things - the ecosystem
# open question 5 asks about against CodeArtifact's `crates` repository - not a notebook
# language; the one kernel that exists (evcxr) compiles on install and would be the only
# compilation in this image.
#
# CARGO_HOME IS DELIBERATELY LEFT UNSET so it defaults to the user's ~/.cargo at runtime: the
# registry cache and anything `cargo install` produces then land on the space's EBS volume,
# writable, instead of failing against a read-only /opt. The rustup SHIMS come from PATH and
# resolve the toolchain through RUSTUP_HOME, which is what makes that split work.
#
# THE CODEARTIFACT HOOK IS STEP 5.2's, NOT THIS FILE'S: cargo reads its registry configuration
# from $CARGO_HOME/config.toml (i.e. the user's home) or from the environment, so pointing it
# at the `crates` repository is a runtime setting on the project, not a build-time layer here.
ENV RUSTUP_HOME=/opt/rust/rustup \
    PATH=/opt/rust/cargo/bin:${PATH}

RUN set -eu; \
    url="https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init"; \
    echo "== rustup ${RUSTUP_VERSION} from ${url}"; \
    curl -fsSL "${url}" -o /tmp/rustup-init; \
    echo "${RUSTUP_SHA256}  /tmp/rustup-init" | sha256sum -c -; \
    chmod +x /tmp/rustup-init; \
    CARGO_HOME=/opt/rust/cargo /tmp/rustup-init -y --no-modify-path --profile minimal \
        --default-toolchain "${RUST_TOOLCHAIN}" --component rustfmt --component clippy; \
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
      echo "python          : $(python --version 2>&1)"; \
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

USER $MAMBA_USER
