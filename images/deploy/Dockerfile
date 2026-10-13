# The deploy image (Stage 8 steps 3.1 and 4.3): what the deploy runner's jobs run in. It carries what
# this repository's lifecycle calls and nothing else - make, uv and the Python .python-version names,
# Terraform at the version the slices pin, git and the AWS CLI - built for amd64, the deploy runner's
# architecture (decision 4).
#
# Every download is pinned: Terraform and uv by the SHA-256 their publishers list, the AWS CLI by the
# AWS CLI team's signature, checked against a key whose fingerprint is pinned below. Built by the
# GitLab project awsds/deploy-image (build.gitlab-ci.yml beside this file) on the build runner, and
# run by the deploy runner by digest, so a later push to the repository changes nothing it runs.

ARG REGISTRY
FROM ${REGISTRY}/ecr-public/docker/library/python:3.14-slim

ARG TERRAFORM_VERSION=1.15.8
ARG TERRAFORM_SHA256=d25ce7b6902013ad905db3d2eab0be4cd905887fe88b81a6171b8d5503c31f3d
ARG UV_VERSION=0.12.13
ARG UV_SHA256=745765a3b6e360ad76743599ae5c42e9278c7edf8bbff9fc76d05bf2623a04dd
ARG AWSCLI_VERSION=2.37.12
ARG AWSCLI_FINGERPRINT=FB5DB77FD5C118B80511ADA8A6310ACC4672475C

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl git gnupg jq make unzip \
 && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o /tmp/terraform.zip \
      "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" \
 && echo "${TERRAFORM_SHA256}  /tmp/terraform.zip" | sha256sum -c - \
 && unzip -q /tmp/terraform.zip terraform -d /usr/local/bin \
 && rm /tmp/terraform.zip \
 && terraform version

RUN curl -fsSL -o /tmp/uv.tar.gz \
      "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" \
 && echo "${UV_SHA256}  /tmp/uv.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/uv.tar.gz -C /tmp \
 && install -m 755 /tmp/uv-x86_64-unknown-linux-gnu/uv /tmp/uv-x86_64-unknown-linux-gnu/uvx /usr/local/bin/ \
 && rm -rf /tmp/uv.tar.gz /tmp/uv-x86_64-unknown-linux-gnu \
 && uv --version

# The key is AWS's, copied from the AWS CLI install page; the build refuses it unless its fingerprint
# is the pinned one, and refuses the archive unless the key signed it.
COPY aws-cli-team.asc /tmp/aws-cli-team.asc
RUN export GNUPGHOME="$(mktemp -d)" \
 && test "$(gpg --show-keys --with-colons /tmp/aws-cli-team.asc | awk -F: '/^fpr/ {print $10; exit}')" = "${AWSCLI_FINGERPRINT}" \
 && gpg --batch --quiet --import /tmp/aws-cli-team.asc \
 && curl -fsSL -o /tmp/awscliv2.zip "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-${AWSCLI_VERSION}.zip" \
 && curl -fsSL -o /tmp/awscliv2.sig "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-${AWSCLI_VERSION}.zip.sig" \
 && gpg --batch --verify /tmp/awscliv2.sig /tmp/awscliv2.zip \
 && unzip -q /tmp/awscliv2.zip -d /tmp \
 && /tmp/aws/install \
 && rm -rf /tmp/aws /tmp/awscliv2.zip /tmp/awscliv2.sig /tmp/aws-cli-team.asc "$GNUPGHOME" \
 && aws --version

# Every module source is an scp-style SSH URL; the repository is public, so a job reads both spellings
# over HTTPS with no key, as the GitHub workflow does.
RUN git config --system url."https://github.com/".insteadOf "git@github.com:" \
 && git config --system --add url."https://github.com/".insteadOf "ssh://git@github.com/"

# uv runs the scripts on this image's interpreter and downloads none: a Python fetched at job time
# would be a toolchain nobody reviewed.
ENV UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=/usr/local/bin/python3.14

LABEL org.opencontainers.image.source="https://github.com/felipenoris/AWS-DataScience" \
      org.opencontainers.image.title="awsds deploy image"
