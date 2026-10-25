# `awsds/dev-env` — the house image's recipe

This project holds the build code for the two images every notebook and every application runs on, and
the pipeline that builds them. It is the recipe's source of truth since 2026-10-14 (AWS-DataScience's
[Stage 8](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/stages/stage-08-cicd-pipelines.md) decision 16): a change is a commit here, and
the infrastructure repository keeps a copy of this project's last commit under `gitlab/awsds/dev-env/`,
written by its `scripts/gitlab-mirror.py`. Nothing here is applied by Terraform:
`terraform-live/production/registry/` owns the ECR repositories these push into, and this project owns
what goes in them.

| Image | ECR repository | What it is |
|---|---|---|
| [`base/`](base/Dockerfile) | `awsds-prod-ecr-base` | The **common ancestor**. Every application image is `FROM base:<pinned tag>`, and so is `dev-env` — D17's *"promote only the code"* holds by construction |
| [`dev-env/`](dev-env/Dockerfile) | `awsds-prod-ecr-dev-env` | The **SMUS custom image (BYOI)** — the runtime every notebook and Unified Studio project app runs on, plus the Julia, R and Rust that CodeArtifact cannot deliver |

The deploy image, what the deploy runner's jobs run in, is the GitLab project `awsds/deploy-image`'s.

## Who builds them

**Once, by hand, at [Stage 6](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/stages/stage-06a-unified-studio.md) step 5.0** — the single
place in this plan where an artifact reaches an AWS account without a pipeline.
[Stage 8](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/stages/stage-08-cicd-pipelines.md) step 1 replaces it with a pipeline that builds
these files from this project, which the data scientist can write to, smoke-tests them, scans them, and
releases them behind the **Dev Env Steward**'s approval gate (AWS-DataScience's `docs/ORGANIZATION.md`).
Until that exists, the files themselves enforce the discipline the pipeline will: every base pinned by
**digest**, every download **checksum-verified**, every assumption about the base image expressed as a
build-time assertion rather than a comment, and every package moved inside the base's conda environment
made to prove it moved nothing else.

**One rebuild in between**: **Stage 7 step 2.6** filled the CA-install layer with the internal PKI root
(D36 §3, amended 2026-08-21) and pointed the image's other trust readers at it; `default-v0.6.0`, built on
2026-10-12 by the build runner's pipeline (below), is the first image that carries it — see
[`base/ca-certificates/README.md`](base/ca-certificates/README.md).

## Releasing

[`.gitlab-ci.yml`](.gitlab-ci.yml) is the release chain of AWS-DataScience's
[Stage 8](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/stages/stage-08-cicd-pipelines.md) step 1. Every push runs the gates on the test
runner, whose jobs hold no AWS identity: Secret Detection on a branch, `pip-audit` over `dev-env/python`,
and `recipe-checks` (the `NO_PROXY` literal's shape, the managed settings parsing). A merge request is how
a change arrives; Developers, the data scientists, open it, and Maintainers, the stewards, merge it.

A release is a tag `<flavour>-v<semver>` on `main`, which only a Maintainer can create (the protected tag
`*-v*`, the release's authorization in GitLab CE). On it:

| Stage | Job | What it does | Runner |
|---|---|---|---|
| build | `build-images` | builds `base` with the distribution through the pull-through cache and pushes it as `<tag>-<short sha>`, builds `dev-env` `FROM` that base by digest and pushes it under the same tag, then builds [`smoke/`](smoke/Dockerfile) `FROM` the pushed `dev-env`: the trust checks, the runtimes at the pinned versions, the key imports, and the manifests | build |
| verify | `scan-base`, `scan-dev-env` | each push's own scan against the lineage's baseline in `awsds/ci-gates`; informative, a red one stops nothing | build |
| release | `release-gate` | the steward's gate, a manual job the chain waits on; running it is the approval, and it keeps the evidence | test |
| register | `register` | on the deploy runner: [`release/versions.py`](release/versions.py) `register` creates the release's SageMaker image version in every target account from the pushed digest, with the release's semver as an alias, and reads it back against that digest | deploy |
| register | `retire` | on the deploy runner: `release/versions.py retire --keep 10` deletes every version past the newest 10 that no space and no domain names, and lists the ones a space still names | deploy |

The order around the gate is the steward's, in [`dev-env.md`](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/runbooks/dev-env.md) §B:

1. Read the evidence: `build-images`' `manifests/` (the package sets of both Pythons, R and Julia, the
   runtimes, the proxy list's digest, the imports) and both scans.
2. Run `release-gate`. `register` follows and prints the version it created and its `ContainerImage`, and
   `retire` the versions it deleted or kept.
3. Record the release: a row below.

No domain write follows. Each domain attaches the image with no version number (AWS-DataScience's Stage 8
decision 7), so the portal offers every version of it, newest first, and a new space pins the one it is
created on. An existing space keeps its version: the steward moves the ones `retire` lists before their
version can go. By hand, the same script runs from a checkout as the infrastructure user,
`python3 release/versions.py register --target awsds-infra-sandbox-1 --tag <tag> --digest <digest>`.

A tag is spent on first landing. When `base` landed and `dev-env` did not, run the pipeline again on the
same tag with `SKIP_BASE=1`: `dev-env` then names the base by its tag, the same bytes in a tag-immutable
repository, and `scan-base` fails for want of a digest, which stops nothing.

## Before a build

**Both images are `linux/amd64`**, and the laptop is `arm64` with no docker. The SageMaker Distribution
publishes `-cpu` and `-gpu` tags and no `arm64` variant (read 2026-08-21 from the public registry's tag
list), and SMUS spaces run on x86 instance types, so the platform is not a choice: it is why the build
runner is an `amd64` `m8i.xlarge`. The six builds before it ran by hand on the buildbox, an `[E]` host of
the same shape that Stage 7 step 6.5 retired on 2026-10-12.

**Check the baked `NO_PROXY` first** (6d decision 8, 2026-09-10). The image carries the six proxy
variables as `ENV`, and `NO_PROXY` — what keeps AWS traffic on the VPC endpoints — is a **literal in the
Dockerfile**, dated in its own comment. An image whose list predates the account's current endpoint set
still works, and sends the names added since out through the proxy as public calls. So read it on the
laptop before the run, with AWS-DataScience's `scripts/check-gitlab-mirror.py` over its copy of this
project (`--plan` while `sandbox/egress` is down): `GM-4` fails when `dev-env/Dockerfile` §7 and the
account's list differ in either direction, writes the line the file must carry, and that is the edit to
make here first.

The account's list is the output `no_proxy_all_groups`, and the literal is that output verbatim. The
image serves every session whatever `GROUPS=` it names, so it carries **every** optional endpoint
group's names (2026-10-10), and the output generates them from the endpoint-service catalog at plan
time, whatever the last apply named. `no_proxy`, beside it, names only the endpoints the last apply
created and is not the image's list. Both are outputs of AWS-DataScience's `sandbox/egress`:

```bash
AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/egress output -raw no_proxy_all_groups
```

While `sandbox/egress` is down its state holds no outputs (`DE-2` fails); a read-only `terraform plan` of
the slice prints `no_proxy_all_groups` all the same, which is how 2026-10-12's check was taken. Another
account's image overrides the literal without editing the file: `--build-arg NO_PROXY_LIST="$(…)"`.

**This is what makes the image estate-shaped.** It is baked with one VPC's endpoint list, so an endpoint
added anywhere in that account — `sandbox/egress` went 28 → 50 entries on 2026-09-09 without a hand edit,
on a module bump — makes every existing image stale, and the repair is a rebuild, a new tag, a new
SageMaker image version and every space moved to it. A second Sandbox (D35) needs its own build for the same reason.
The trade was taken with its eyes open, against two API-side mechanisms that cannot carry the value at
all: [`dev-env.md`](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/runbooks/dev-env.md) §E. **What reports a stale Dockerfile** is
`scripts/check-gitlab-mirror.py`, and `./aws/devenv.py` beside it, which compare the literal against the
account's current `no_proxy_all_groups` and name the entries each side is missing; **what reports a stale
image** is `/opt/awsds-proxy.txt` inside it, the entry count and the first 16 hex of the list's sha256.
Neither is enforced by a gate: both are readings, and [`dev-env.md`](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/runbooks/dev-env.md)
§E says when to take them.

**Audit the lock on the laptop before the tag.** `pip-audit` reads OSV's records of the day, so the gate's
verdict is dated: the lock of 2026-10-16 passed `default-v0.8.0`'s gate and met 73 blocking findings at
`default-v0.9.0`'s on 2026-10-25 (pipelines #89 to #91), which spent the tag with nothing built. The gate's
own audit runs on the laptop in about two and a half minutes once the export's environment markers are
stripped: pip-audit skips a line whose marker the running interpreter does not match, and every line names
`linux` and `x86_64` (AWS-DataScience Stage 8 verification x). From a checkout of AWS-DataScience:

```bash
uv export --project gitlab/awsds/dev-env/dev-env/python --locked --no-dev --no-emit-project --format requirements-txt --quiet --output-file "$HOME/tmp/dev-env-pins.txt"
```

```bash
sed -i '' -E 's/ ; [^\\]*( \\)?$/\1/' "$HOME/tmp/dev-env-pins.txt"
```

```bash
uvx --from pip-audit==2.10.1 pip-audit --requirement "$HOME/tmp/dev-env-pins.txt" --disable-pip --require-hashes --vulnerability-service osv --progress-spinner off
```

What it prints beyond the accepted list in `ci-gates/baselines.gitlab-ci.yml` blocks the tag. A finding with a
fixed version leaves by `uv lock --upgrade-package <name>`, one per blocked package, never a bare `--upgrade`,
which on 2026-10-25 resolved an older autogluon and failed building `configspace`; a fixed version another
package forbids (`Pillow<13` from autogluon-multimodal 1.6.1) enters the accepted list by name, through a
`gates-v*` tag and this file's `include:` `ref` ([`gitlab.md`](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/runbooks/gitlab.md) §G).

**The uv cache must never be written into a layer.** Measured on the first `default-v0.2.0` build
(2026-09-11): the Python layer came out at 10.7 GB against a 5.2 GB environment, because `uv` unpacks
every wheel into `/root/.cache/uv` before materialising it into the venv and both live in the same
layer. `UV_NO_CACHE=1` inside that `RUN` is the fix and a later `rm -rf` is not one — the bytes are
committed the moment the layer closes. With it the image is **22.7 GB** on disk, against 28.1 GB
without; the ECR figure is the compressed one and is roughly a third of that.

**A change to `base` rebuilds `dev-env` from its first layer.** A build of both on the runner's 64 GiB root
succeeded on 2026-10-12, its disk use not read; the runner is `[E]`, so every session starts with an empty disk.

Julia is a prebuilt tarball, `rustup` fetches prebuilt binaries and the R environment is conda-forge
binaries, which is why the build is short. Python's lock names 8 packages that publish no Linux wheel for
CPython 3.12 (`gssapi` and `krb5` among them, read from the lock on 2026-10-14), and uv builds those from
source. The one other compilation is Julia's `Pkg.precompile()`, kept as the build's proof that the
package set compiles and then **discarded** — a precompilation cache carries native code for the CPU that produced it,
so the first `using` in a space compiles for that space's CPU instead.

**The repositories are tag-immutable**: a tag is spent the first time it lands and a re-push under the same
tag is rejected. **Record the pushed digests in the stage log** —
[Stage 6d step 2.1](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/stages/stage-06d-unified-studio-remainder.md) registers a SageMaker
image *version* against one, and the next release has to be able to say which digest it replaced.

**What tag to spend is not decided here.** The convention — `<flavour>-v<major>.<minor>.<patch>`, the
same number in both repositories, `default-v0.1.0` first written 2026-08-22 — lives in
[`docs/SMUS.md`](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/SMUS.md) §*Custom images (BYOI) — and how they are named*, with the reason the
flavour comes first and the trigger that turns a flavour into a repository of its own.

## The releases

Every tag spent in both repositories, the one complete record (moved here from the buildbox's runbook at
Stage 7 step 6.5). Sizes are ECR's, compressed and per repository.

| Tag | Built | What changed | Reading |
|---|---|---|---|
| `default-v0.1.0` | 2026-08-22, buildbox | the first build (Stage 6a step 5.0) | 12.1 and 17.5 GB on the host became 3.96 and 5.65 GB in ECR |
| `default-v0.1.1` | 2026-09-08, buildbox | nothing in the recipe: the same files rebuilt | `base` +942 bytes, `dev-env` −11.8 MB, all upstream drift: a **patch** |
| `default-v0.2.0` | 2026-09-11, buildbox | the proxy environment as `ENV`, the apt and sudoers files, a second Python environment with its own kernel | the recipe changed: a **minor**; the uv-cache measurement above |
| `default-v0.3.0` | 2026-09-12, buildbox | `/etc/claude-code/managed-settings.json`, a `NO_PROXY` literal of 52 entries with the two Bedrock names, `rust-src`, no Julia precompilation cache | |
| `default-v0.4.0` | 2026-09-12, buildbox | Stage 6e's model pins, the 4.5 generation ([`claude-code-sagemaker.md`](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/runbooks/claude-code-sagemaker.md) M4) | `dev-env` 5,453 bytes smaller than `v0.3.0` (7,182,170,437 against 7,182,175,890): a string change |
| `default-v0.5.0` | 2026-10-10, buildbox | the ancestor moved to SageMaker Distribution `4.5.2-cpu`, uv kept at the distribution's 0.12.17, a `NO_PROXY` literal of 70 entries | both about 213 MB smaller than `v0.4.0`, within 0.9 MB of each other (`base` 3,745,881,983, `dev-env` 6,969,138,672): the ancestor's delta |
| `default-v0.6.0` | 2026-10-12, the build runner's pipeline | the internal CA root in `base`, with OpenSSL, `requests`, curl and Node pointed at the system bundle (Stage 7 step 2.6); `redshift-connector` declared | `base` 3,745,648,934 (`sha256:94359041…1975`), `dev-env` 6,675,093,373 (`sha256:43079013…5518`), 294 MB smaller; built in about 16 minutes with the distribution through the pull-through cache |
| `default-v0.7.0` | 2026-10-15, release pipeline #24 from `69ad278e` | every Python environment on 3.12 (AWS-DataScience Stage 8 decision 13); the house lock past every pip-audit finding it can leave, the steward's 8 accepted (decision 15) | `default-v0.7.0-69ad278e`: `base` 3,745,649,522 (`sha256:c17191c9…22be`), `dev-env` 6,678,357,140 (`sha256:b1e896e0…685c`), built in 951 s; **never registered**: `release-gate` failed at bash's parse on a quote in its own script |
| `default-v0.7.1` | 2026-10-15, release pipeline #28 from `c268de48` | the release gate's quote (!2); the recipe is `v0.7.0`'s | `default-v0.7.1-c268de48`: `base` 3,745,649,509 (`sha256:4accbaf5…e525`), `dev-env` 6,678,358,952 (`sha256:3b6d706a…84a4`), built in 956 s, the manifests `v0.7.0`'s but the base digest; both scans CRITICAL 113 and HIGH 610, the 593 past the baseline all `linux-libc-dev`; registered by `register` as Sandbox's version 7 |
| `default-v0.7.3` | 2026-10-15, release pipeline #38 from `15fac237` | nothing in the recipe: the include at `gates-v0.4.0` (!5), whose pip-audit accepts a finding by any of its ids, after `default-v0.7.2` at `8e78ab53` stopped at `pip-audit` on fsspec's accepted finding under a new OSV id and pushed nothing | `default-v0.7.3-15fac237`: `base` 3,745,649,508 (`sha256:b05552a8…2ba1`), `dev-env` 6,682,673,224 (`sha256:38f4864c…dd6f`), built in 983 s, the manifests `v0.7.1`'s but the base digest; both scans CRITICAL 113 and HIGH 610, the 593 past the baseline all `linux-libc-dev`; the first release under AWS-DataScience Stage 8 decision 18: `register` created Sandbox's version 8, alias `0.7.3`, with no domain write, and `retire` kept versions 8 and 7 |
| `default-v0.8.0` | 2026-10-16, release pipeline #46 from `7c59998c` | the SageMaker CI/CD CLI `aws-smus-cicd-cli` 1.0.9 in the house Python environment (AWS-DataScience Stage 8 decision 22, !7), and `mcp` held to `>=1.30.0,<2`, the 1.x line's fix for CVE-2026-59951, since `strands-agents` requires `mcp<2.2` | `default-v0.8.0-7c59998c`: `base` 3,745,649,519 (`sha256:681dcb20…f23e`), `dev-env` 6,678,573,838 (`sha256:b788dbd9…1b87`), built in 955 s; the Python manifest adds `aws-smus-cicd-cli` 1.0.9, `httpx-sse` 0.4.3 and `pydantic-settings` 2.16.0, moves `mcp` 2.1.1 → 1.30.0 and drops `mcp-types`, the other manifests `v0.7.3`'s but the base digest; both scans CRITICAL 113 and HIGH 610, the 593 past the baseline all `linux-libc-dev`; `register` created Sandbox's version 9, alias `0.8.0`, with no domain write, and `retire` kept versions 9, 8 and 7 |
| `default-v0.9.1` | 2026-10-25, release pipeline #96 from `746ef084` | the 72-name `NO_PROXY` literal of `vpc-egress-v0.18.0` (AWS-DataScience Stage 8 1.1, merged as `f71cafcd`); the lock moved past the findings OSV published since 2026-10-16, 17 entries in 9 packages (`aiohttp`, `brotli`, `certifi`, `filelock`, `gitpython`, `mlflow` with `-skinny` and `-tracing`, `nbconvert`, the opentelemetry family, `virtualenv`, `yarl`); the include at `gates-v0.5.0`, whose dev-env list accepts pillow 12.3.0's 41 findings and setuptools' second by name (!10), after `default-v0.9.0` at `f71cafcd` stopped at `pip-audit` on the lock of 2026-10-16 (73 blocking) and pushed nothing | `default-v0.9.1-746ef084`: `base` 3,754,767,181 (`sha256:ac9bd82b…044e`), `dev-env` 6,687,899,330 (`sha256:20a1017a…ca39`), built in 970 s; `pip-audit` 50 accepted and 0 blocking; the Python manifest moves the lock's 17 entries, `proxy.txt` 72 entries `6faf2e4761622508`, the other manifests `v0.8.0`'s but the base digest; both scans CRITICAL 113 and HIGH 612, the 595 past the baseline 593 `linux-libc-dev` and, new, `CVE-2026-85091` on `zlib` and `zlib1g`; `register` created Sandbox's version 10, alias `0.9.1`, with no domain write, and `retire` kept versions 10, 9, 8 and 7 |

**The recipe is not reproducible byte-for-byte**: `v0.1.1` moved both digests with no commit to the
recipe, and a retry of the same commit builds another manifest (Stage 7 6.4). A pipeline that assumes
otherwise reports a spurious change on every run. **The push takes the registry's `dkr.ecr` name**, which
resolves to `VPC-SharedServices`' `ecr.dkr` interface endpoint: measured on `v0.5.0`'s push in CloudTrail
(`vpcEndpointId` on every `InitiateLayerUpload` and the `PutImage`), and on `v0.6.0`'s by the absence of
any ECR name in the proxy's access log.

## Before editing either file

1. **The ancestry is forced from both ends.** SMUS's BYOI specification requires the notebook image to
   descend from `public.ecr.aws/sagemaker/sagemaker-distribution` (≥ `2.6-cpu`); D17 requires one
   ancestor shared with the application images. The only shape satisfying both is `base` *being* the
   distribution plus this project's layer. The cost is an ETL container inheriting a JupyterLab
   distribution — the cheaper half of the trade Stage 8 step 1 argued.
2. **No `ENTRYPOINT`.** The BYOI page states that adding one *"will not work as expected"*; the
   distribution's `_entrypoint.sh` must survive. A custom entry point is a `ContainerConfig` setting, not
   a Dockerfile line.
3. **`/opt/ml`, `/opt/.sagemakerinternal` and `/var/log/studio` belong to AWS**, and the space's EBS
   volume mounts at `/home/sagemaker-user` on a path that cannot be changed. Anything written to `/opt`
   by these builds is therefore **read-only shared state**, and anything a user must be able to write
   goes under the home directory — which is why the Julia depot search path lists the user's depot first
   and the baked one second. Since 2026-09-11 the baked depot carries package sources, artifacts, the
   registry and the resolved environment but **no precompilation cache**, so that first entry is where a
   space's Julia caches land — on its own EBS volume, per space and per user.

## The editable surface

It is not the `Dockerfile`s. The package sets are files a person edits, because the data scientist owns
them (AWS-DataScience's `docs/ORGANIZATION.md`, *Dev Env Steward*) and a merge request against a list is reviewable in a
way one against a `RUN` line is not:

| File | Ecosystem | CodeArtifact covers it? |
|---|---|---|
| [`dev-env/python/pyproject.toml`](dev-env/python/pyproject.toml) + its `uv.lock` | Python, in **an environment of its own** — not the distribution's | Yes (`pypi`) — so this file is the *ad-hoc* path's backstop, not its only one |
| [`dev-env/julia/packages.txt`](dev-env/julia/packages.txt) | Julia | **No** — under design B this image is the only path |
| [`dev-env/r/conda-packages.txt`](dev-env/r/conda-packages.txt) | R (conda-forge) | **No** — same |
| — | Rust | Yes (`crates`) — the toolchain is baked, the crates are not |

**The Python row is edited in two steps, never one** (2026-09-10): change `dependencies` in the
`pyproject.toml`, then `uv lock --directory dev-env/python`, and commit both files. The build
runs `uv sync --frozen`, which refuses a lock that disagrees with the project rather than resolving
something nobody reviewed — so a package added without re-locking fails the build instead of arriving
unreviewed. The lock is also what makes two builds of one commit the same environment.

**In a space, uv finds the distribution's Python only.** This environment's CPython lives under
`/opt/awsds/python`, installed by a `uv python install` whose `UV_PYTHON_INSTALL_DIR` only the build step
sets, it is on no search path, and the base image sets `UV_PYTHON_DOWNLOADS=never`. A uv project that
wants this environment's interpreter therefore names it: `UV_PYTHON=$AWSDS_PYTHON_ENV/bin/python uv sync`.
Read from this recipe and reproduced on 2026-10-11 in a simulation of a space's interpreters, where the
space itself answered `which python` with `/opt/conda/bin/python`. `awsds-workflows package-job` takes it
the same way, from `UV_PYTHON` in its environment
([`serverless-workflows.md`](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/runbooks/serverless-workflows.md) §J1). Up to `default-v0.6.0`
this environment is 3.13 against the distribution's 3.12, so a project asking for 3.13 finds nothing
unless it names it; the recipe carries 3.12 since 2026-10-14 (Stage 8 decision 13), the distribution's
minor, and the first image built from it is `default-v0.7.0`. A later image version that exported
`UV_PYTHON_INSTALL_DIR=/opt/awsds/python` would make it discoverable to every uv command.

**For two of those rows the merge request review is the only control there is.** Measured 2026-08-22,
when Stage 6a step 5.0 pushed the first images: ECR's scan read `base` and `dev-env` to identical
severity counts, so the Julia, R and Rust content of this image produced zero findings because nothing
scanned it — basic scanning reads OS packages, and Amazon Inspector's supported languages for container
images do not include Julia or R at any price. This project's own Python environment has a second
reader, `pip-audit` over `dev-env/python/uv.lock` (Stage 8 step 5); the distribution's `/opt/conda`
packages are no uv project and have none, nor have Julia and R, and under design B this image is their
only delivery path.

**A version pinned in these files is admitted to the whole estate by a human reading a diff.** The
acceptance, what it costs and what would reverse it are one row in
[`docs/plan/institutional-delta.md`](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/plan/institutional-delta.md), *"Vulnerability scanning of
what the notebook image actually contains"*. Two consequences for whoever reviews one of these merge
requests: prefer a version you can look up an advisory for, and remember the review sees the package at
the moment it is pinned — a CVE published next month against a version already in the image will be
found by nobody here.
