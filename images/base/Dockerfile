# awsds base - the COMMON ANCESTOR (Stage 6 step 5.0; Stage 8 step 1 owns it afterwards).
#
# WHY THIS IMAGE EXISTS AT ALL, and it is not "somewhere to put shared packages": D17 says
# promote only the CODE, which is only true if the runtime the code lands on is identical to
# the one it was written against. Stage 8 step 1 makes that true by construction rather than
# by convention - every application image is `FROM base:<pinned tag>` and the notebook image
# dev-env/ is `FROM base` too. Two images built independently from the same package LIST
# diverge at the first rebuild; two images built from the same ANCESTOR cannot.
#
# THE ANCESTRY IS FORCED FROM BOTH ENDS, AND THE TWO ENDS NEARLY COLLIDE (read 2026-08-21,
# from the specification rather than from the plan's summary of it):
#
#   from below   SMUS's BYOI specification requires the notebook image to be built FROM
#                public.ecr.aws/sagemaker/sagemaker-distribution, version >= 2.6-cpu - those
#                images carry the extensions without which an image will not run in Unified
#                Studio at all. The stage file's older note ("base on jupyterlab/default")
#                was the SageMaker AI health-check URL, not the base image.
#   from above   D17 wants ONE ancestor for the notebook and the application images.
#
# The only shape satisfying both is the one below: `base` IS the SageMaker distribution plus
# this project's shared layer, and everything else descends from `base`. The cost is honest
# and is written down rather than discovered: an ETL container inherits a JupyterLab
# distribution it never opens (~4 GB compressed). The alternative - a slim application base
# beside a distribution-rooted dev-env - is exactly the "two independently built images" that
# Stage 8 step 1 rejects in as many words.
#
# NO ENTRYPOINT, AND IT IS A REQUIREMENT RATHER THAN AN OMISSION: the SMUS BYOI page states
# that adding ENTRYPOINT "will not work as expected" - the distribution's own
# /usr/local/bin/_entrypoint.sh must survive. A custom entry point is configured through the
# ContainerConfig API, never here.
#
# WHAT MUST NOT BE TOUCHED (custom image specification): /opt/ml and /opt/.sagemakerinternal
# are AWS's metadata directories, /var/log/studio is the reserved logging directory, and the
# EBS volume of a space mounts at /home/sagemaker-user - the mount path cannot be changed.
#
# BUILD (amd64 - the distribution publishes no arm64 tag; see images/README.md):
#   docker buildx build --platform linux/amd64 -t awsds/base:local images/base

# --------------------------------------------------------------- the pin, and why by DIGEST
#
# The tag is kept for a human and the DIGEST is what actually resolves (Lesson 23: bind to
# contents, never to a name a publisher may move). Read 2026-08-21 straight from the public
# registry's manifest API - anonymous, no IAM action, which is why `DenyEcrPublicEntirely`
# does not reach it:
#
#   4.3.0-cpu   sha256:7f5d9c64684cebd53f65173c1f41d7bfe68419e5de9d0f55c4c25910a92f5f2c
#               linux/amd64, Ubuntu 24.04, micromamba at /opt/conda, built 2026-07-10,
#               24 layers / ~3.93 GB compressed. Satisfies the ">= 2.6-cpu" floor with room.
#
# THE VERSION IS THE USER'S CHOICE, TAKEN 2026-08-21, and the digest beside it is this
# repository's job rather than theirs: `4.3.0-cpu` was asked for by name, and what was
# measured here is what that name resolves to today. `4.4.1-cpu` (2026-08-07) is the newest
# `-cpu` tag published and is what an unpinned build would have drifted onto.
#
# THE ARCHITECTURE IS NOT A CHOICE EITHER WAY: SageMaker images are amd64, and the repository
# publishes `cpu`/`gpu` suffixes with no arm64 variant at all - measured from the tag list the
# same day. That is the fact the devbox exists for (terraform-live/sandbox/devbox/README.md).
#
# REVISION TRIGGER: a SMUS release raising the floor, or a base advisory the ECR scan flags.
# Bump the pair TOGETHER - a tag without its digest is the thing this comment exists against.
ARG SMD_IMAGE=public.ecr.aws/sagemaker/sagemaker-distribution
ARG SMD_TAG=4.3.0-cpu
ARG SMD_DIGEST=sha256:7f5d9c64684cebd53f65173c1f41d7bfe68419e5de9d0f55c4c25910a92f5f2c

FROM ${SMD_IMAGE}:${SMD_TAG}@${SMD_DIGEST}

# RE-DECLARED, and not by accident: an ARG stated before FROM is scoped to the FROM line
# alone. Without these three lines the provenance LABELs at the bottom would record the empty
# string - a label that looks like a measurement and is not (Lesson 37's shape, in a file).
ARG SMD_IMAGE
ARG SMD_TAG
ARG SMD_DIGEST

# The distribution's own identity values, restated because the AWS sample restates them and
# because a reader should not have to inspect the base to know who the image runs as. The
# LIVE values in 4.4.1-cpu are USER=sagemaker-user with MAMBA_USER_ID/GID=57439 - NOT the
# 1000/100 of the sample - and it does not matter: the specification calls 1000/100
# "supported values", and SageMaker remaps the ids at runtime either way.
ARG NB_USER="sagemaker-user"
ARG NB_UID=1000
ARG NB_GID=100
ENV MAMBA_USER=$NB_USER

# The package index, for BOTH Python installers - the name is pip's for continuity, the reach
# is not (section 4). EMPTY means "the public one" - which is what the hand build of step 5.0
# uses, and what egress design A keeps using. Design B (step 5.2) and Stage 8's pipeline pass
# the CodeArtifact endpoint instead, so the switch is a build argument rather than an edit.
ARG PIP_INDEX_URL=""

# How many CA roots the layer below is EXPECTED to install. It is 0 for every build Stage 6
# makes and 1 from Stage 7 step 2.6 onward; the RUN asserts the count, so the number is a
# check rather than a label (see the CA section further down).
ARG CA_ROOTS_EXPECTED=0

USER root

# ------------------------------------------------------ 1. the extension idle shutdown needs
#
# THIS IS AN ASSERTION, NOT AN INSTALL, AND THE DIFFERENCE IS THE POINT. Step 8's idle
# shutdown cannot see activity without the JupyterLab activity-monitor extension; the
# SageMaker distribution is documented to carry "important extensions that are required to
# execute an image on Amazon SageMaker Unified Studio". Documented is not measured. Installing
# it again would paper over a base that stopped shipping it - the failure would then surface
# as an idle app billing all night (US-7/US-10), which is the expensive place to find out.
# So the build FAILS here instead, and the evidence is printed either way.
RUN set -eu; \
    echo "== searching the base for the activity-monitor extension =="; \
    ( pip list --format=freeze 2>/dev/null || true; micromamba list 2>/dev/null || true ) \
      | grep -iE 'jupyter[-_]activity[-_]monitor' | sort -u | tee /tmp/awsds-activity-monitor.txt; \
    if [ ! -s /tmp/awsds-activity-monitor.txt ]; then \
      echo "FATAL: no activity-monitor extension in this base image." >&2; \
      echo "  Stage 6 step 8's idle shutdown reads activity through it; without it an app" >&2; \
      echo "  bills until someone notices. Either the base moved, or the pin is wrong." >&2; \
      echo "  Do NOT pip-install it as a workaround before reading images/README.md." >&2; \
      exit 1; \
    fi; \
    rm -f /tmp/awsds-activity-monitor.txt

# ------------------------------------------------------------------ 2. the shared OS layer
#
# DELIBERATELY SHORT. Everything here is inherited by every application image and by every
# notebook, so a package added for one consumer is paid for by all of them. `git` and the
# build essentials are the two that genuinely are universal: INT-09's clone, and any pip
# install that has no wheel for this platform.
RUN set -eu; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        unzip; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# --------------------------------------- 3. uv - an UPGRADE in place, never a second binary
#
# THE DISTRIBUTION ALREADY SHIPS uv, and that single fact is the whole shape of this layer.
# Measured 2026-08-21 from the distribution's own resolved environment - `cpu.env.out` under
# build_artifacts/v4/v4.3/v4.3.0/ in aws/sagemaker-distribution, the @EXPLICIT list this exact
# tag is built from - whose line 913 pins `uv-0.11.28` from conda-forge, i.e. /opt/conda/bin/uv.
# So "install the latest uv" is a version MOVE inside a package that is already here.
#
# WHICH RULES OUT THE OBVIOUS IMPLEMENTATION, and the first draft of this layer was it: drop
# Astral's static binary into /opt/uv/bin and put it first on PATH. That leaves TWO uv in the
# image, and which one answers depends on where you ask - a RUN in a descendant, the
# entrypoint's activated environment and a Jupyter kernel do not share one PATH. One intent in
# two places (Lesson 33), with the added cruelty that both answers look right in isolation.
# It goes through micromamba for the same reason: the package manager's manifest keeps agreeing
# with the filesystem, so the next `micromamba update` cannot silently revert this layer.
#
# NOTHING ELSE MAY MOVE, AND `--freeze-installed` CANNOT EXPRESS THAT. The flag was in the
# first draft of this layer and came out again after mamba's own source was read
# (`create_install_request`, libmamba/src/api/install.cpp): with it set, mamba emits a Freeze
# job for EVERY package already in the prefix, with no exemption for the specs you are
# explicitly asking for. `uv` is in the prefix - so the flag would freeze the one package this
# layer exists to move, giving either an unsolvable request or a silent no-op, both of which
# read afterwards as "the flag protected me". A guard that cannot distinguish those is not one.
#
# SO THE GUARANTEE IS A MEASUREMENT, and a cheaper one: conda's own on-disk record.
# $MAMBA_ROOT_PREFIX/conda-meta holds one `<name>-<version>-<build>.json` per installed package,
# so the before/after listing IS the change set - no output format to guess at, no solver
# behaviour to trust. Anything in it that is not `uv-*` means the solve moved a locked
# environment underneath this build, and it stops with the names printed. The expected change
# set is exactly two lines: uv 0.12.5 declares only `__glibc >=2.17`, `libgcc >=15` and
# `libstdcxx >=15`, and this image carries libgcc/libstdcxx 15.2.0 - read from conda-forge and
# from cpu.env.out the same day.
#
# THE VERSION IS AN ARG so Stage 8's pipeline bumps it without editing a build - and `UV_VERSION`
# is NOT one of uv's own environment variables (checked against uv-static's `EnvVars` at 0.12.5),
# so the build argument cannot be read back by the tool it names.
ARG UV_VERSION=0.12.5
RUN set -eu; \
    echo "== uv before: $(uv --version 2>/dev/null || echo none)"; \
    ls "${MAMBA_ROOT_PREFIX}/conda-meta" | sed 's/\.json//' | sort > /tmp/awsds-env-before.txt; \
    micromamba install -y --name base -c conda-forge "uv==${UV_VERSION}"; \
    micromamba clean --all --yes --force-pkgs-dirs; \
    ls "${MAMBA_ROOT_PREFIX}/conda-meta" | sed 's/\.json//' | sort > /tmp/awsds-env-after.txt; \
    changed="$(diff /tmp/awsds-env-before.txt /tmp/awsds-env-after.txt | grep -E '^[<>] ' || true)"; \
    echo "== the change set this install produced =="; echo "${changed}"; \
    unexpected="$(echo "${changed}" | grep -vE '^[<>] uv-' | grep -E '^[<>] ' || true)"; \
    [ -z "${unexpected}" ] \
      || { echo "FATAL: the solve moved packages other than uv:" >&2; \
           echo "${unexpected}" >&2; exit 1; }; \
    rm -f /tmp/awsds-env-before.txt /tmp/awsds-env-after.txt; \
    found="$(uv --version | cut -d' ' -f2)"; \
    where="$(command -v uv)"; \
    echo "== uv after : ${found} at ${where}"; \
    [ "${found}" = "${UV_VERSION}" ] \
      || { echo "FATAL: asked for uv ${UV_VERSION}, got ${found}." >&2; exit 1; }; \
    [ "${where}" = "${MAMBA_ROOT_PREFIX}/bin/uv" ] \
      || { echo "FATAL: uv resolves to ${where}, not to the managed one in" >&2; \
           echo "  ${MAMBA_ROOT_PREFIX}/bin - a second uv is ahead of it on PATH." >&2; \
           echo "  Read section 3's comment before working around this." >&2; \
           exit 1; }

# THE TWO SETTINGS uv NEEDS IN A GOVERNED IMAGE, AND ONE IT DELIBERATELY DOES NOT GET.
#
#   UV_PYTHON_DOWNLOADS=never  uv's default, when it cannot find the Python a project asks for,
#                              is to FETCH a standalone CPython from the internet. That would
#                              put code on an interpreter which is not the distribution's - the
#                              exact thing D17 buys by making every image share one ancestor -
#                              and under egress design B it fails as a network timeout instead
#                              of saying what it wanted. `never` turns it into an error naming
#                              the missing Python; a user who genuinely wants one passes
#                              --python-downloads=allow for that one command.
#   UV_SYSTEM_CERTS=true       uv carries its own root bundle and does not read the OS trust
#                              store unless told to. Section 5 lists the tools that "each have
#                              their own opinion" and leaves them to Stage 7; uv's half is
#                              closed here because it is one word, and because the alternative
#                              is Stage 7 rediscovering it as a TLS error.
#
# NOT SET: UV_LINK_MODE. `copy` is the container reflex and it would be wrong here - uv's cache
# (~/.cache/uv) and any project venv both land on the space's EBS volume under
# /home/sagemaker-user, one filesystem, where hardlinking is exactly what should happen.
ENV UV_PYTHON_DOWNLOADS=never \
    UV_SYSTEM_CERTS=true

# ---------------------------------- 4. the package index, and it must reach BOTH installers
#
# Applied once, so every later install in every descendant inherits it.
#
# WRITTEN TO /etc/pip.conf RATHER THAN THROUGH `pip config set`, and the difference is the
# whole value of the layer: `pip config set` defaults to the USER level, so run as root during
# a build it lands in /root/.config/pip/pip.conf - a file `sagemaker-user` never reads. The
# setting would then hold for the rest of the build and silently not hold at runtime, which is
# the failure mode that looks like a network fault in a notebook.
#
# AND uv DOES NOT READ /etc/pip.conf AT ALL, which is why one RUN writes two files. Section 3
# put a second Python installer in this image and it has its own configuration system; switching
# only pip would leave Stage 8 and egress design B pointing pip at CodeArtifact while uv keeps
# talking to public PyPI - one intent in two places again, in the direction that fails least
# visibly. The branch below writes both or neither.
#
# /etc/uv/uv.toml IS THE SYSTEM LEVEL, AND IS DISCOVERED RATHER THAN FORCED. Read from uv's own
# source at 0.12.5 (`system_config_file` in uv-dirs): on Linux it tries XDG_CONFIG_DIRS first
# and falls back to /etc/uv/uv.toml. Pointing UV_CONFIG_FILE at the file would also work and is
# WRONG - --config-file replaces discovery, so a data scientist's own project uv.toml would stop
# being read. System level layers UNDER the user's, which is the point of a default here.
#
# `[[index]]` rather than the top-level `index-url` key: both resolve at 0.12.5 (measured), and
# `index-url` is the deprecated spelling.
RUN set -eu; \
    mkdir -p /etc/uv; \
    if [ -n "${PIP_INDEX_URL}" ]; then \
      printf '[global]\nindex-url = %s\n' "${PIP_INDEX_URL}" > /etc/pip.conf; \
      printf '[[index]]\nurl = "%s"\ndefault = true\n' "${PIP_INDEX_URL}" > /etc/uv/uv.toml; \
      echo "package index: ${PIP_INDEX_URL} (/etc/pip.conf + /etc/uv/uv.toml)"; \
    else \
      printf '# Built against the public index: no override.\n' > /etc/uv/uv.toml; \
      echo "package index: default (public PyPI)"; \
    fi

# ------------------------------------------------- 5. the CA-install layer - EMPTY BY DESIGN
#
# THE LAYER IS HERE; THE CONTENT ARRIVES AT STAGE 7 STEP 2.6. D36 §3 was amended 2026-08-21:
# the internal CA root moved back to Stage 7 with the leaves, because the only names the root
# lets a container trust - gitlab.prod.internal, *.pages.internal - do not exist while Stage 6
# runs, and every endpoint this stage touches is an AWS public endpoint with a public
# certificate. What stays behind is the HOOK, so that step 2.6 fills a blank instead of
# editing a build.
#
# TO FILL IT (Stage 7 step 2.6): drop the root PEM into images/base/ca-certificates/ with a
# .crt extension, read from production/pki/'s output and never pasted (INT-19), and build with
# --build-arg CA_ROOTS_EXPECTED=1. The assertion below is what makes "I thought I added it"
# impossible: a mismatch in either direction fails the build.
#
# IT LIVES IN `base`, NOT IN `dev-env`, and that is a deviation from the sentence Stage 7 step
# 2.6 is written with. One intent enforced in two places diverges (Lesson 33), and the root is
# not only the notebook's concern - the runner, and any application container that speaks to
# an internal TLS surface, want the same trust. The price is that step 2.6 rebuilds BOTH
# images; that step now says so.
#
# NOT COVERED HERE, and it is Stage 7's to close: Python does not read the OS trust store -
# `certifi` ships its own bundle, and `git`, `curl` and conda each have their own opinion.
# uv had the same opinion and is the one already answered, in section 3 (UV_SYSTEM_CERTS) -
# it is listed here so Stage 7 crosses it off rather than rediscovering it.
COPY ca-certificates/ /usr/local/share/ca-certificates/awsds/
RUN set -eu; \
    installed="$(find /usr/local/share/ca-certificates/awsds -name '*.crt' -type f | wc -l | tr -d ' ')"; \
    echo "CA roots found in the build context: ${installed} (expected ${CA_ROOTS_EXPECTED})"; \
    if [ "${installed}" != "${CA_ROOTS_EXPECTED}" ]; then \
      echo "FATAL: CA root count mismatch - build arg says ${CA_ROOTS_EXPECTED}, context has ${installed}." >&2; \
      exit 1; \
    fi; \
    update-ca-certificates

# --------------------------------------------------------------------------- 6. provenance
#
# Read back with `docker inspect`, and by the Stage 8 pipeline that replaces this hand build.
LABEL org.opencontainers.image.title="awsds-base" \
      org.opencontainers.image.description="The common ancestor image - SageMaker Distribution plus this project's shared layer (D17)." \
      org.opencontainers.image.source="https://github.com/felipenoris/AWS-DataScience" \
      org.opencontainers.image.base.name="${SMD_IMAGE}:${SMD_TAG}" \
      org.opencontainers.image.base.digest="${SMD_DIGEST}" \
      org.awsds.stage="6.5.0" \
      org.awsds.ca-roots="${CA_ROOTS_EXPECTED}" \
      org.awsds.uv="${UV_VERSION}"

USER $MAMBA_USER
