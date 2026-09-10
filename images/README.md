# `images/` — the container images and how they are built

This directory holds the build code for the two images the estate runs on. Nothing here is applied by
Terraform: `terraform-live/production/registry/` owns the ECR repositories these push into, and this
directory owns what goes in them.

| Image | ECR repository | What it is |
|---|---|---|
| [`base/`](base/Dockerfile) | `awsds-prod-ecr-base` | The **common ancestor**. Every application image is `FROM base:<pinned tag>`, and so is `dev-env` — D17's *"promote only the code"* holds by construction |
| [`dev-env/`](dev-env/Dockerfile) | `awsds-prod-ecr-dev-env` | The **SMUS custom image (BYOI)** — the runtime every notebook and Unified Studio project app runs on, plus the Julia, R and Rust that CodeArtifact cannot deliver |

## Who builds them

**Once, by hand, at [Stage 6](../docs/plan/stages/stage-06a-unified-studio.md) step 5.0** — the single
place in this plan where an artifact reaches an AWS account without a pipeline.
[Stage 8](../docs/plan/stages/stage-08-cicd-pipelines.md) step 1 replaces it with a pipeline that builds
these same files from a GitLab repository the data scientist can write to, smoke-tests them, scans them,
and releases them behind the **Dev Env Steward**'s approval gate (`docs/ORGANIZATION.md`). Until that
exists, the files themselves enforce the discipline the pipeline will: every base pinned by **digest**,
every download **checksum-verified**, every assumption about the base image expressed as a build-time
assertion rather than a comment, and every package moved inside the base's conda environment made to
prove it moved nothing else.

**One rebuild in between**: **Stage 7 step 2.6** fills the CA-install layer with the internal PKI root
(D36 §3, amended 2026-08-21). The layer already exists and is asserted empty — see
[`base/ca-certificates/README.md`](base/ca-certificates/README.md).

## Building them on the buildbox

Both images are `linux/amd64` and the laptop is `arm64`. The SageMaker Distribution publishes `-cpu` and
`-gpu` tags and no `arm64` variant (read 2026-08-21 from the public registry's tag list), and SMUS spaces
run on x86 instance types, so the platform is not a choice; the laptop has no docker installed either.
The build happens on
[`terraform-live/production/buildbox/`](../terraform-live/production/buildbox/README.md) — an `[E]`
`t3.xlarge` in `VPC-SharedServices`'s private tier (Production, since
[6c step 5.8](../docs/plan/stages/stage-06c-networking-hub.md)), reached over Session Manager through
`production/egress/`'s SSM endpoints, with no ingress rule at all, reaching the internet only as a client
of the explicit proxy. It exists while a build runs and is destroyed after; the session's order — the
door first, then the host — is [`docs/plan/runbooks/buildbox.md`](../docs/plan/runbooks/buildbox.md) §U.

```bash
./scripts/buildbox.py up && ./scripts/buildbox.py sync && ./scripts/buildbox.py ssm
```

Then, in the session (you land as `ssm-user` with `sudo`; the `docker` group belongs to `ec2-user`):

```bash
cd /opt/awsds/images && sudo docker build -t awsds/base:local base
```

```bash
sudo docker build -t awsds/dev-env:local dev-env
```

**Check the baked `NO_PROXY` before that build** (6d decision 8, 2026-09-10). The image carries the six
proxy variables as `ENV`, and `NO_PROXY` — what keeps AWS traffic on the VPC endpoints — is a **literal
in the Dockerfile**, dated in its own comment. An image whose list predates the account's current
endpoint set still works, and sends the names added since out through the proxy as public calls. So
read the current value on the laptop, and if it differs from the one in `dev-env/Dockerfile` §6, update
the file first:

```bash
AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/egress output -raw no_proxy
```

Another account's image overrides it without editing the file:
`--build-arg NO_PROXY_LIST="$(…)"`.

**This is what makes the image estate-shaped.** It is baked with one VPC's endpoint list, so an endpoint
added anywhere in that account — `sandbox/egress` went 28 → 50 entries on 2026-09-09 without a hand edit,
on a module bump — makes every existing image stale, and the repair is a rebuild, a new tag, a new
SageMaker image version and a re-attach. A second Sandbox (D35) needs its own build for the same reason.
The trade was taken with its eyes open, against two API-side mechanisms that cannot carry the value at
all: [`docs/plan/runbooks/dev-env.md`](../docs/plan/runbooks/dev-env.md) §E. **What reports a stale
Dockerfile** is `./aws/devenv.py`, which compares the literal against the account's current output and
names the entries each side is missing; **what reports a stale image** is `/opt/awsds-proxy.txt` inside
it, the entry count and the first 16 hex of the list's sha256. Neither is enforced by a gate: both are
readings, and [`dev-env.md`](../docs/plan/runbooks/dev-env.md) §E says when to take them.

```bash
./scripts/buildbox.py down
```

**A change to `base` rebuilds `dev-env` from its first layer**, and a rebuild needs room for a second
copy of a ~17 GB image before the old one loses its tag. The 64 GiB root is enough for that and not for
much more: [`docs/plan/runbooks/buildbox.md`](../docs/plan/runbooks/buildbox.md) §S is how to look before
starting one, and what to prune when the answer is no.

Nothing in either `Dockerfile` compiles anything: Julia is a prebuilt tarball, `rustup` fetches prebuilt
binaries, the R environment is conda-forge binaries. That is why the build is short.

**The buildbox cannot push.** Its role carries Session Manager and no `ecr:` permission, and the host
lives in the registry's own account, where no repository policy grants a push to anybody (read live on
2026-08-22: both carry one statement, `AllowConsumerAccountsToPull`) and same-account access is decided
by the identity policy alone. The push into `awsds-prod-ecr-base` / `awsds-prod-ecr-dev-env` is the
user's own act from an identity that may (`awsds-infra-prod`; first done at Stage 6a step 5.0), and it
reaches this host as a 12-hour ECR **authorization token** rather than as a permission. The procedure is
[`buildbox.md`](../docs/plan/runbooks/buildbox.md) §P; read it before the build. The host is `[E]` and
its volume dies with it, so build and push are one session, and a `down` in between costs the rebuild.
The repositories are tag-immutable: a tag is spent the first time it lands and a re-push under the same
tag is rejected. **Record the pushed digests in the stage log** —
[Stage 6d step 2.1](../docs/plan/stages/stage-06d-unified-studio-remainder.md) registers a SageMaker
image *version*, and Stage 7 step 2.6 has to be able to say which digest it replaced.

**What tag to spend is not decided here.** The convention — `<flavour>-v<major>.<minor>.<patch>`, the
same number in both repositories, `default-v0.1.0` first written 2026-08-22 — lives in
[`docs/SMUS.md`](../docs/SMUS.md) §*Custom images (BYOI) — and how they are named*, with the reason the
flavour comes first and the trigger that turns a flavour into a repository of its own.

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
   and the baked one second.

## The editable surface

It is not the `Dockerfile`s. The package sets are files a person edits, because the data scientist owns
them (`docs/ORGANIZATION.md`, *Dev Env Steward*) and a merge request against a list is reviewable in a
way one against a `RUN` line is not:

| File | Ecosystem | CodeArtifact covers it? |
|---|---|---|
| [`dev-env/python/pyproject.toml`](dev-env/python/pyproject.toml) + its `uv.lock` | Python, in **an environment of its own** — not the distribution's | Yes (`pypi`) — so this file is the *ad-hoc* path's backstop, not its only one |
| [`dev-env/julia/packages.txt`](dev-env/julia/packages.txt) | Julia | **No** — under design B this image is the only path |
| [`dev-env/r/conda-packages.txt`](dev-env/r/conda-packages.txt) | R (conda-forge) | **No** — same |
| — | Rust | Yes (`crates`) — the toolchain is baked, the crates are not |

**The Python row is edited in two steps, never one** (2026-09-10): change `dependencies` in the
`pyproject.toml`, then `uv lock --directory images/dev-env/python`, and commit both files. The build
runs `uv sync --frozen`, which refuses a lock that disagrees with the project rather than resolving
something nobody reviewed — so a package added without re-locking fails the build instead of arriving
unreviewed. The lock is also what makes two builds of one commit the same environment.

**For two of those rows the merge request review is the only control there is.** Measured 2026-08-22,
when Stage 6a step 5.0 pushed the first images: ECR's scan read `base` and `dev-env` to identical
severity counts, so the Julia, R and Rust content of this image produced zero findings because nothing
scanned it — basic scanning reads OS packages, and Amazon Inspector's supported languages for container
images do not include Julia or R at any price. Python has a second reader (`pip-audit`, Stage 8 step 5);
Julia and R have none, and under design B this image is their only delivery path.

**A version pinned in these files is admitted to the whole estate by a human reading a diff.** The
acceptance, what it costs and what would reverse it are one row in
[`docs/plan/institutional-delta.md`](../docs/plan/institutional-delta.md), *"Vulnerability scanning of
what the notebook image actually contains"*. Two consequences for whoever reviews one of these merge
requests: prefer a version you can look up an advisory for, and remember the review sees the package at
the moment it is pinned — a CVE published next month against a version already in the image will be
found by nobody here.
