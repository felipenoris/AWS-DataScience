# `images/` — the two container images, and the one time they are built by hand

This directory holds the build code for the two images the estate runs on. It is **not**
infrastructure code and nothing here is applied by Terraform; `terraform-live/production/registry/`
owns the ECR repositories these push into, and this directory owns what goes in them.

| Image | ECR repository | What it is |
|---|---|---|
| [`base/`](base/Dockerfile) | `awsds-prod-ecr-base` | The **common ancestor**. Every application image is `FROM base:<pinned tag>` and `dev-env` is too — that is what makes D17's *"promote only the code"* true by construction rather than by convention |
| [`dev-env/`](dev-env/Dockerfile) | `awsds-prod-ecr-dev-env` | The **SMUS custom image (BYOI)** — the runtime every notebook and Unified Studio project app runs on, plus the Julia, R and Rust that CodeArtifact cannot deliver |

## Who builds them, and when that stops being true

**Once, by hand, at [Stage 6](../docs/plan/stages/stage-06a-unified-studio.md) step 5.0** — the single
place in this plan where an artifact reaches an AWS account without a pipeline. It is acceptable
exactly once, at bootstrap, and it is **replaced by [Stage 8](../docs/plan/stages/stage-08-cicd-pipelines.md)
step 1**, whose pipeline builds these same files from a GitLab repository the data scientist can write
to, smoke-tests them, scans them, and releases them behind the **Dev Env Steward**'s approval gate
(`docs/ORGANIZATION.md`). Until that exists, the discipline the pipeline will enforce is enforced here
by the files themselves: every base pinned by **digest**, every download **checksum-verified**, every
assumption about the base image expressed as a **build-time assertion** rather than a comment, and every
package moved inside the base's conda environment made to **prove it moved nothing else**.

**One rebuild in between**, and it is scheduled rather than incidental: **Stage 7 step 2.6** fills the
CA-install layer with the internal PKI root (D36 §3, amended 2026-08-21). The layer already exists and
is asserted empty — see [`base/ca-certificates/README.md`](base/ca-certificates/README.md).

## Building them — on the buildbox, not on the laptop

**Both images are `linux/amd64` and the laptop is `arm64`.** The SageMaker Distribution publishes
`-cpu` and `-gpu` tags and **no `arm64` variant at all** (read 2026-08-21 from the public registry's
tag list), and SMUS spaces run on x86 instance types, so the platform is not a choice. The laptop
also has no docker installed. So the build happens on
[`terraform-live/sandbox/buildbox/`](../terraform-live/sandbox/buildbox/README.md) — an `[E]` `t3.xlarge`
in the Sandbox account's isolated tier, reached over Session Manager and **with no ingress rule at
all**, reaching the internet only through the WireGuard host. It exists while a build runs and is
destroyed after.

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

```bash
./scripts/buildbox.py down
```

**A change to `base` rebuilds `dev-env` from its first layer**, and a rebuild needs room for a second
copy of a ~17 GB image before the old one loses its tag. The 64 GiB root is enough for that and not for
much more: [`docs/plan/runbooks/buildbox.md`](../docs/plan/runbooks/buildbox.md) §S is how to look before
starting one, and what to prune when the answer is no.

**Nothing in either `Dockerfile` compiles anything** — Julia is a prebuilt tarball, `rustup` fetches
prebuilt binaries, the R environment is conda-forge binaries. That was a requirement while the build
was still planned for an emulated laptop; on the buildbox it is simply why the build is short.

**The buildbox cannot push, and the build does not survive it being asked to.** Its role carries
Session Manager and no `ecr:` permission, because the Production registry grants the Interactive
accounts a *pull* and nothing more — read live on 2026-08-22, both repository policies carry one
statement and it is `AllowConsumerAccountsToPull`. The push into `awsds-prod-ecr-base` /
`awsds-prod-ecr-dev-env` is Stage 6 step 5.0's own act from an identity that may
(`awsds-infra-prod`), and it reaches this host as a 12-hour ECR **authorization token** rather than
as a permission: **the whole procedure is [`buildbox.md`](../docs/plan/runbooks/buildbox.md) §P.** Read
it before the build, not after — **the host is `[E]` and its volume dies with it, so build and push
are one session** and a `down` in between costs the rebuild. The repositories are tag-immutable, so
a tag is spent the first time it lands and a re-push under the same tag is rejected — that is the
control, not a nuisance. **Record the pushed digests in the stage log**: Stage 6 step 5.1 registers
a SageMaker image *version*, and Stage 7 step 2.6 has to be able to say which digest it replaced.

**What tag to spend is not decided here.** The convention — `<flavour>-v<major>.<minor>.<patch>`, the
same number in both repositories, `default-v0.1.0` first written 2026-08-22 — has one copy, in
[`docs/SMUS.md`](../docs/SMUS.md) §*Custom images (BYOI) — and how they are named*, together with the
reason the flavour comes first and the trigger that turns a flavour into a repository of its own.

## The three things worth knowing before editing either file

1. **The ancestry is forced from both ends and they nearly collide.** SMUS's BYOI specification
   requires the notebook image to descend from `public.ecr.aws/sagemaker/sagemaker-distribution`
   (≥ `2.6-cpu`); D17 requires one ancestor shared with the application images. The only shape
   satisfying both is `base` *being* the distribution plus this project's layer. The cost — an ETL
   container inheriting a JupyterLab distribution — is real, and is the cheaper half of the trade
   Stage 8 step 1 already argued.
2. **No `ENTRYPOINT`, ever.** The BYOI page states plainly that adding one *"will not work as
   expected"*; the distribution's `_entrypoint.sh` must survive. A custom entry point is a
   `ContainerConfig` setting, not a Dockerfile line.
3. **`/opt/ml`, `/opt/.sagemakerinternal` and `/var/log/studio` belong to AWS**, and the space's EBS
   volume mounts at `/home/sagemaker-user` on a path that cannot be changed. Anything written to
   `/opt` by these builds is therefore **read-only shared state**, and anything a user must be able to
   write goes under the home directory — which is why the Julia depot search path lists the user's
   depot first and the baked one second.

## Where the editable surface is

Not in the `Dockerfile`s. The package sets are plain text files, because the data scientist owns them
(`docs/ORGANIZATION.md`, *Dev Env Steward*) and a merge request against a list is reviewable in a way
a merge request against a `RUN` line is not:

| File | Ecosystem | CodeArtifact covers it? |
|---|---|---|
| [`dev-env/python/requirements.txt`](dev-env/python/requirements.txt) | Python, **on top of** the distribution's stack | Yes (`pypi`) — so this file is the *ad-hoc* path's backstop, not its only one |
| [`dev-env/julia/packages.txt`](dev-env/julia/packages.txt) | Julia | **No** — under design B this image is the only path |
| [`dev-env/r/conda-packages.txt`](dev-env/r/conda-packages.txt) | R (conda-forge) | **No** — same |
| — | Rust | Yes (`crates`) — the toolchain is baked, the crates are not |

**And for two of those rows, reviewing the merge request is not just good practice — it is the only
control there is.** Measured 2026-08-22, when Stage 6 step 5.0 pushed the first images: ECR's scan read
`base` and `dev-env` to **identical** severity counts, so the Julia, R and Rust content of this image
produced **zero findings because nothing scanned it** — basic scanning reads OS packages, and Amazon
Inspector's supported languages for container images do not include Julia or R at any price. Python has
a second reader (`pip-audit`, Stage 8 step 5); Julia and R have none, and under design B this image is
their only delivery path.

**So the version pinned in these files is admitted to the whole estate by a human reading a diff.**
That is the accepted position, not an oversight — the acceptance, what it costs and what would reverse
it are one row in [`docs/plan/institutional-delta.md`](../docs/plan/institutional-delta.md),
*"Vulnerability scanning of what the notebook image actually contains"*. Two practical consequences for
whoever reviews one of these merge requests: **prefer a version you can look up an advisory for**, and
remember the review sees the package **at the moment it is pinned** — a CVE published next month against
a version already in the image will be found by nobody here.
