# `awsds/deploy-image` — the deploy image's recipe

The image the deploy runner's jobs run in (AWS-DataScience's
[Stage 8](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/stages/stage-08-cicd-pipelines.md)
steps 3.1 and 4.3): make, uv, Python 3.14, Terraform 1.15.8, git, the AWS CLI and the SageMaker CI/CD
CLI `aws-smus-cicd-cli` 1.0.9 (step 2.5, D41), every download pinned, built for `amd64`, the deploy
runner's architecture (Stage 8 decision 4). This project is its
source of truth since 2026-10-14 (Stage 8 decision 16), and the infrastructure repository keeps a copy of
its last commit under `gitlab/awsds/deploy-image/`, written by its `scripts/gitlab-mirror.py`.

Only the infrastructure owner is a member, because whoever builds this image chooses what runs with the
deploy roles' credentials. The build runner serves it, assigned in the admin area, the runner staying
locked.

| File | What it is |
|---|---|
| [`Dockerfile`](Dockerfile) | the image: Terraform and uv checked against the SHA-256 their publishers list, the AWS CLI against its team's signature |
| [`aws-cli-team.asc`](aws-cli-team.asc) | the AWS CLI team's public key, whose fingerprint the Dockerfile pins |
| [`requirements-cli.txt`](requirements-cli.txt) | the CI/CD CLI and every package it pulls, pinned with the hashes of their files, installed into `/opt/smus-cli` with `--require-hashes`; regenerated with `uv pip compile --python-version 3.14 --generate-hashes` from the one line `aws-smus-cicd-cli==1.0.9` |
| [`.gitlab-ci.yml`](.gitlab-ci.yml) | the build on the build runner and the push to `awsds-prod-ecr-deploy` |

## Building it

1. **Build → Pipelines → Run pipeline** on `main`, with `IMAGE_TAG` (`v<semver>`). The pipeline runs only
   from that form: its rule admits the `web` source alone, so a pipeline started through the API creates
   no job.
2. The job builds this project's commit with its base through the pull-through cache, pushes
   `awsds-prod-ecr-deploy:<IMAGE_TAG>` and prints the digest.
3. The digest becomes `deploy_image_digest` in AWS-DataScience's
   `terraform-live/production/runners/variables.tf`, committed: the deploy runner exists only once it is
   set, and runs that digest and no other image.

The pins follow the infrastructure repository's toolchain, the versions its `CLAUDE.md` names, so a
change of one there is a change here.

## The releases

| Tag | Built | Digest | Scan |
|---|---|---|---|
| `v0.1.0` | 2026-10-13, pipeline #5 from AWS-DataScience `de2dc08`, 68 s | `sha256:1b1a5830…a53a`, 208,935,352 bytes, on `python:3.14-slim` (Debian 13) `sha256:a2b82f3c…9170` | CRITICAL 2, HIGH 8, MEDIUM 10, LOW 4. Both CRITICALs are Debian's `curl` (CVE-2026-8924, CVE-2026-8927), `<no-dsa>` with no fixed package for Debian 13, and git links libcurl; accepted by name by the user 2026-10-13 as this image's baseline (Stage 8 decision 1), rebuilt once Debian 13 ships the fix |
| `v0.2.0` | 2026-10-16, pipeline #43 from `b064ba80`, 64 s; the SageMaker CI/CD CLI 1.0.9 added | `sha256:ee31048e…7e91ac`, 255,596,236 bytes, on `python:3.14-slim` (Debian 13) `sha256:a2b82f3c…9170` | CRITICAL 0, HIGH 4, MEDIUM 10, LOW 4. The HIGHs are the Debian 13 base's: `glibc` (CVE-2026-19499, CVE-2026-5435), `zlib` (CVE-2026-85091) and `gnupg2` (CVE-2026-24882); no finding names `curl` |
