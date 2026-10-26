# Runbook — the dev-env image in SageMaker

| | |
|---|---|
| **Scope** | The house image as SageMaker AI sees it: the `[P]` slice that registers it in a member account (`sandbox/dev-env/`), the attachment that makes it appear in the portal's image list, the version a release adds and the retirement of old ones, moving a space to another version, and the detach. The build and the push are [`gitlab/awsds/dev-env/README.md`](../../../gitlab/awsds/dev-env/README.md)'s; the naming rule is [`docs/SMUS.md`](../../SMUS.md)'s. This file is what runs **per account and per release**, forever |
| **Operator** | The **infrastructure user** — account **Sandbox** (or the member account being configured), permission set **`InfrastructureAccess`**, profile `awsds-infra-sandbox-1`. §C's registry read also touches Production through `awsds-infra-prod`, and one SSO login covers both. Every write is authorized per occurrence. §C6 is the one act this repository does not own in code |
| **The rules** | **The domain is the blueprint's object, not Terraform's.** `Tooling` provisions the SageMaker AI domain per project, so the attachment (§C6) is a hand step against a live object and never an `import` (Lesson 17). **A registered version is frozen to a digest**: SageMaker resolves the tag once, at `CreateImageVersion`, and a rebuilt tag would not move it — the repositories are tag-immutable anyway. **Half a proxy environment is worse than none** (§E) |
| **The picture around it** | Why there is a house image at all: [D17](../decisions/D17-interactive-vs-runtime.md) and `gitlab/awsds/dev-env/README.md`. What a space reaches once it starts: [`docs/NETWORK.md`](../../NETWORK.md) and [`sg-proxy.md`](sg-proxy.md). What the portal does with the image: [`docs/SMUS.md`](../../SMUS.md), *Custom images (BYOI)* |
| **Written** | 2026-09-10 at [Stage 6d](../stages/stage-06d-unified-studio-remainder.md) step 2, and rewritten 2026-10-15 for [Stage 8](../stages/stage-08-cicd-pipelines.md) decisions 7 and 18: a release adds a version, the domain attaches the image with no version number, and a retirement deletes old versions. Every behaviour §B rests on was measured that day on a probe image (the Stage 8 log). Exercised in its earlier form, a version replaced and the domain detached and re-attached around it: §C in full on `default-v0.1.1`, the replace on `default-v0.2.0` to `v0.5.0` and on `default-v0.7.1`, the first release by the pipeline, §X step 1, §V. §B's register and retire jobs ran on `default-v0.7.3` (2026-10-15), version 8 offered by the version-less attach with no domain write. Unexercised, and each says so in place: the console route of §C6, §X steps 2-3, and the reconciliation reading §C7 ends on (step 2.4). The vendor pages are the 2026-09-10, 2026-09-11 and 2026-10-14 rows of [`docs/REFERENCES.md`](../../REFERENCES.md) |

---

## O. The objects, and who owns each

Four objects stand between a container in ECR and a data scientist choosing it in the portal. Only the
first three are this repository's.

| Object | What it is | Owner |
|---|---|---|
| **Image** | the named thing a domain attaches. Account-scoped, versionless, carries a `RoleArn` | `sandbox/dev-env/`, Terraform |
| **Image version** | one immutable pointer at one container image. Numbered by the service, 1 upwards | the **release pipeline**: `awsds/dev-env`'s `register` job creates it, its `retire` job deletes it (§B; Stage 8 decision 18) |
| **App image configuration** | how a space starts that container: entrypoint, arguments, environment. One per app type | `sandbox/dev-env/`, Terraform |
| **`CustomImages` on the domain** | the list a space's image picker is built from | the **`Tooling` blueprint**, and §C6 by hand |

The seam is the fourth row, and it is a per-app-type field of the domain's **user settings** —
`JupyterLabAppSettings.CustomImages`, `CodeEditorAppSettings.CustomImages`. A **space** carries no image
*list*: `SpaceSettings.CodeEditorAppSettings` is a different shape, with neither `CustomImages` nor
`LifecycleConfigArns`, so what the picker **offers** is decided on the domain alone. An entry with no
`ImageVersionNumber` offers **every version** of the image, newest first, each labelled `<display name>
v<n>` (measured 2026-10-15), which is how this estate attaches it (§C6).

**What a space runs is decided on the space.** Its `DefaultResourceSpec` names one image and one
version, written when the space is created, and it **overrides the domain default** from then on
(measured 2026-09-12, correcting a 2026-09-10 reading here that said a space cannot name an image and
that the answer to *can we do this per space* is no). The portal writes the version chosen in its picker:
`CreateSpace` carries the version's ARN, measured 2026-10-15. So the domain governs what a new space can
choose, each space keeps what it was created on, and a release reaches an existing space only when the
space is moved (§B). A space whose version is deleted does not start (`EXC-09`).

## C. Configuring an account so a custom image is selectable

The checklist for a **new case** — a new member account, a new project's domain, or the first image in
either. Steps 1-2 are read-and-check; 3-6 are the work; 7 is the proof.

### 1. What must already exist

| Prerequisite | How to check it | If it is missing |
|---|---|---|
| The image, built and pushed under a `<flavour>-v<semver>` tag | `aws ecr describe-images --repository-name awsds-prod-ecr-dev-env --profile awsds-infra-prod` | [`gitlab/awsds/dev-env/README.md`](../../../gitlab/awsds/dev-env/README.md) — the build runner's pipeline, about 16 minutes (2026-10-12) |
| The repository's pull grant naming this account | `aws ecr get-repository-policy --repository-name awsds-prod-ecr-dev-env --profile awsds-infra-prod` — the `AllowConsumerAccountsToPull` statement | add the account to `REGISTRY_CONSUMERS` (`scripts/tfhygiene/backend.py`) and apply `production/registry/` |
| `ecr.api` and `ecr.dkr` endpoints in the account's VPC | they are in `vpc-egress`'s `core_services`, so `make up ENV=<env>` is enough | there is no NAT anywhere (D38): without them a space cannot pull at all |
| The SMUS domain for the project, and the account association | `./aws/studio.py` | [Stage 6a](../stages/stage-06a-unified-studio.md); an image cannot be attached to a domain that does not exist |

### 2. The image's own shape

Not repeated here: the ancestor (`public.ecr.aws/sagemaker/sagemaker-distribution` ≥ `2.6-cpu`), the
absent `ENTRYPOINT`, AWS's three owned paths, and the `jupyterlab/default` base URL with its health check
on 8888 are [`gitlab/awsds/dev-env/README.md`](../../../gitlab/awsds/dev-env/README.md)'s *Before editing either file* and the vendor's
BYOI specifications. An image that fails them registers happily and fails when a space starts, which is
the expensive place to find out.

### 3. The Terraform, when the slice does not exist yet

Three files outside the slice, and they come first — the tooling refuses an undeclared slice before any
target runs:

1. **`scripts/tfhygiene/layers.py`** — a rank in `RANKS` (`dev-env` is 49) and a row in `SLICES`, layer
   `PERSISTENT`. A slice on disk with no row is skipped by `make down` silently, so `./scripts/slices.py
   check` fails on either half alone.
2. **`scripts/tfhygiene/backend.py`** — the slice reads `production/registry/`'s state, so it needs the
   `registry` map emitted into its tfvars (`REGISTRY_HOME`, and the `if slice_name == "dev-env"` block in
   `tfvars_values`). A profile literal never sits in a `.tf` file (Lesson 14) and an ECR URI pasted by
   hand would carry the registry account's id into a tracked file (`aws/INDEX.md` rule 1).
3. **`terraform-live/<account>/dev-env/`** — copy `sandbox/dev-env/`; the account-shaped values arrive
   from the generated tfvars, so the copy needs no edit. It holds no version: that is §4's last step.

### 4. Registering the image

Recipe A of [`terraform-changes.md`](terraform-changes.md), with the three-platform lock a new slice owes:

```bash
./scripts/gen-backend-hcl.py sandbox dev-env && ./scripts/gen-tfvars.py sandbox dev-env
```

```bash
AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/dev-env init -backend-config=backend.hcl -input=false
```

```bash
AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/dev-env providers lock -platform=darwin_arm64 -platform=linux_amd64 -platform=linux_arm64
```

```bash
AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/dev-env plan -input=false -out="$HOME/tmp/dev-env.tfplan"
```

Applying it is authorized per occurrence, and the plan to read is the saved one. A first apply is five
resources: the image, two app image configurations, the image role and the role's inline policy.
`aws_sagemaker_image` takes about a minute; everything else is immediate.

**The first version** is the release pipeline's (§B), which reaches a new account once the deploy runner
holds its `awsds-deploy-devenv-<unit>` profile. By hand, as the infrastructure user, from a checkout of
`awsds/dev-env` or its copy under `gitlab/awsds/dev-env/`; an image with no version yet has none to read
the repository from, so the first call names it, read from the registry rather than typed:

```bash
python3 gitlab/awsds/dev-env/release/versions.py register --target awsds-infra-sandbox-1 --tag <tag> --digest <sha256:digest> --repository "$(AWS_PROFILE=awsds-infra-prod aws ecr describe-repositories --repository-names awsds-prod-ecr-dev-env --query 'repositories[0].repositoryUri' --output text)"
```

### 5. The image role, which is not decorative

`CreateImage` requires a `RoleArn`, and the vendor's console flow offers to attach
`AmazonSageMakerFullAccess` to it. This estate does not, and the measurement says it does not need to.

**Measured 2026-09-10, in Production's CloudTrail at the moment of the first apply**: `CreateImageVersion`
made SageMaker assume `awsds-sandbox-sagemaker-image` — session name `SageMaker`, `userIdentity.type`
`AWSAccount`, an AWS-internal source address — and call **`BatchGetImage`** and
**`GetDownloadUrlForLayer`** on `awsds-prod-ecr-dev-env` in the registry account. So the role is the
principal that reads the repository across the account boundary at registration, its four ECR actions are
the ones exercised, and the repository policy's `AllowConsumerAccountsToPull` is the other half of the
intersection (Lesson 28). The version came back `CREATED` with `ContainerImage` naming the digest the
steward pushed — the tag resolved to `sha256:6916fc13…6d13`, which is 9.5's own reading.

A role with no ECR reach registers nothing: the version would land `CREATE_FAILED` with a permissions
`FailureReason`, and `describe-image-version` is where that sentence lives (§F).

### 6. Attaching the image to the domain

**The CLI route ran on 2026-09-10 and the block survived it.** `awsds-sandbox-dev-env` version 1 was
attached to both app settings in one `update-domain`; the domain came back `InService` with no
`FailureReason`, and the before/after diff of the whole `DefaultUserSettings` showed **only the two
added entries** — the mount, the idle settings, the storage ceiling and `AutoMountHomeEFS` all still
there. Lesson 60's hazard is real and did not fire here, which is a reading about one write and not a
property of the API. The console route stays unexercised.

Two routes, and the difference is who assembles the settings block.

The domain to attach to is the project's, and its id is not guessable — read it, never transcribe it:

```bash
aws sagemaker list-domains --profile awsds-infra-sandbox-1 --query 'Domains[].[DomainId,DomainName]' --output text
```

**The console route, and why it is not this estate's.** SageMaker AI console → *Admin configurations*
→ *Domains* → the project's domain → *Environment* → *Custom images for personal Studio apps* →
**Attach image** → *Existing image*, then an image **and a version**, and the app type matching the
Dockerfile. The wizard assembles the settings block itself and preserves the rest of
`DefaultUserSettings` by its shape, but by the vendor's page it attaches the version chosen, a number,
and decision 7's entry carries none. Unexercised here.

**The CLI route, for a scripted or repeated case.** Send the block back whole — read, edit, send —
never a hand-written minimal one. Two readings say why, and they do not say the same thing:
`UpdateDomain` is documented and treated as a full replace of `DefaultUserSettings`, so a field not
passed back is at risk (Lesson 60), and this block carries idle shutdown, the `shared` S3 mount, the
storage ceiling, the portal settings and `AutoMountHomeEFS`. But **an omitted `CustomImages` is not
cleared**, measured 2026-09-11: a block sent without that key left both entries exactly as they were.
The vendor's own detach page is where the rule is written — *"you will need to leave `CustomImages`
blank, such that `"CustomImages": []`"* — so clearing a list means sending an empty one, while
everything else is sent back as read.

**No app has to go first, whatever the vendor's page says.** Its detach page reads *"Before you can
update the custom images, you must delete all of the applications in your domain."* On 2026-10-15
`update-domain` changed `CustomImages` four times with apps `InService`: an entry added, the same image
listed twice, the list reverted, and an entry removed while two apps ran on that image. Each was
accepted, read back identical, and left the running apps as they were (Lesson 41). A running app keeps
the image it started with either way.

The write is two commands. The first reads the live block and puts the slice's own entries into it, so
nothing is typed and nothing depends on a file an earlier step left behind (Lesson 61); the `cat` is
there to be read before anything is sent:

```bash
aws sagemaker describe-domain --domain-id <domain-id> --profile awsds-infra-sandbox-1 --query DefaultUserSettings > "$HOME/tmp/before.json" && jq --argjson ci "$(AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/dev-env output -json custom_images)" '.JupyterLabAppSettings.CustomImages = [$ci.jupyterlab] | .CodeEditorAppSettings.CustomImages = [$ci.code_editor]' "$HOME/tmp/before.json" > "$HOME/tmp/attached.json" && cat "$HOME/tmp/attached.json"
```

```bash
aws sagemaker update-domain --domain-id <domain-id> --default-user-settings "file://$HOME/tmp/attached.json" --profile awsds-infra-sandbox-1
```

**Then diff the whole block, not the key you added.** The hazard is a field that went missing, and
`--query CustomImages` cannot see one. `$HOME/tmp/before.json` is that comparison's other half, and it
is also the rollback — for this sitting only, since any later act reads the block again:

```bash
aws sagemaker describe-domain --domain-id <domain-id> --profile awsds-infra-sandbox-1 --query DefaultUserSettings > "$HOME/tmp/after.json" && diff <(python3 -m json.tool "$HOME/tmp/before.json") <(python3 -m json.tool "$HOME/tmp/after.json")
```

The only differences must be the entries you added. **Measured** on the attach of 2026-09-10, the
re-attaches on versions 2, 5, 6 and 7 (2026-09-11 to 2026-10-15), and the four writes of the probe
image on 2026-10-15: each time the diff carried nothing but `CustomImages`, and the domain came back
`InService` with no `FailureReason`.

**No `ImageVersionNumber`, by Stage 8 decision 7 (taken 2026-10-15).** The slice's `custom_images`
output carries none, so the attach writes entries the portal reads as *every version of the image*.
Measured on a probe image that day: the picker listed each version, newest first, as `<display name>
v<n>`; a version created afterwards appeared at the top with no domain write; and a new space pinned the
version it was created on. So this attach is the last domain write a release needs. What a review gate
guards is the version's existence, and the steward's `release-gate` precedes it (§B). With a number, the
picker offers that version alone, and every release costs this write again.

**A SMUS space reads the user-settings block, measured 2026-09-10.** The experiment had its control:
`DefaultSpaceSettings` carried no `CustomImages` and no `CodeEditorAppSettings` at all, read after the
attach. The picker offered the image and **both a JupyterLab and a Code Editor space started on it**,
so the domain's `DefaultUserSettings` is the attachment point and `DefaultSpaceSettings` is the fallback
nobody needs. One image serves both app types here, which the Dockerfile does not promise — it is
JupyterLab-shaped by the vendor's rule — so treat it as a reading about this image rather than a
property of BYOI.

### 7. Selecting it, and reading the attachment back

In the portal, as a data scientist: the project's *Compute* → *Spaces*, create a JupyterLab space, and the
image appears under *Custom Images* beside the SageMaker Distribution versions, one option per version,
`AWS-DataScience dev-env v<n>`, newest first. That the picker offers it is the whole of this section's
proof; that a space **starts** on it is the endpoints' and the pull grant's proof, and it is where a
missing `ecr.dkr` shows up as a start that never finishes. Opening the project's *Spaces* page also
starts the project's default space (a `CreateApp` by the portal, read 2026-10-15), billed until its
idle shutdown.

**AWS's image sits in the same picker, and a space created on it looks like this image failing.**
The custom image is listed beside the SageMaker Distribution versions, and on 2026-09-12 the user
created a space on the distribution without meaning to — reported as picking *"a imagem padrão do
SageMaker"*. A space on it starts normally, runs the same IDE, and has
**no proxy variables and no internet name reachable** — which reads exactly like a defect in this
image's proxy environment. Measured 2026-09-12: a Code Editor space created that way ran
`sagemaker-distribution-cpu` by alias `4.3` and reached nothing, while the image it was meant to run
carried all six variables. Two readings separate the cases, and neither needs a theory:

| From | Reading | This image | Anything else |
|---|---|---|---|
| inside the space | `cat /opt/awsds-proxy.txt` | prints the proxy URL, entry count and list digest | `No such file` — only this image writes it |
| outside | `describe-app … --query ResourceSpec` | `image/awsds-sandbox-dev-env`, a version ARN | another image ARN, often `sagemaker-distribution-cpu` with an alias |

```bash
aws sagemaker describe-app --domain-id <domain-id> --space-name <space> --app-type CodeEditor --app-name default --profile awsds-infra-sandbox-1 --query ResourceSpec
```

**`describe-app` answers for an app that has already been deleted**, so a space removed in frustration
can still be attributed afterwards — the 2026-09-12 reading above was taken that way. And
`./aws/devenv.py`'s `DE-5` answers the other half of the question: whether the image the registry
holds carries the variables at all, read from its config blob rather than from any space.

**`RemoteAccess` is per space and a new one can come up without it.** Of the two spaces created on
this image on 2026-09-12, one read `RemoteAccess: DISABLED` (`ml.t3.large`, 16 GB) and the other
`ENABLED` (`ml.m7i.xlarge`, 64 GB); which values the portal form proposes was not recorded. A space is
not reachable from a laptop's VS Code until the flag is on — [`remote-ide.md`](remote-ide.md).

Read back what the domain now holds, and keep the reading:

```bash
aws sagemaker describe-domain --domain-id <domain-id> --profile awsds-infra-sandbox-1 --query 'DefaultUserSettings.JupyterLabAppSettings.CustomImages'
```

A blueprint reconciliation may rewrite the settings this attachment lives in — the same risk the D13
boundary carries (INT-15), and Stage 6d step 2.4 is the reading. Until it has an answer, treat the
attachment as something to re-check after any blueprint or project-profile change, and re-attach rather
than re-argue.

## E. The proxy environment, and where it is delivered

Every internet call from a space crosses the Squid proxy (D38), so a working session needs six variables
and `NO_PROXY` is the load-bearing one: it is what keeps AWS traffic on the VPC endpoints. Without it,
and with a proxy set, every AWS call leaves through the hub as a public call carrying neither
`aws:SourceVpc` nor `aws:SourceVpce` — and the compute plane allows `.amazonaws.com`, so it **succeeds**
while the perimeter is quietly gone. Half the pair is worse than neither.

**The image carries them, decided 2026-09-10 by the user** (Stage 6d decision 8). Neither API-side
mechanism can:

| Mechanism | Why not |
|---|---|
| `ContainerEnvironmentVariables` on the app image configuration | each value caps at 256 characters (`ContainerConfig`: 25 entries, 256 per key and per value) against a `NO_PROXY` of about 1,500 — `CreateAppImageConfig` refuses it outright, measured at step 2.2 |
| A lifecycle configuration | it fits — a 16 KB script — but there is no `UpdateStudioLifecycleConfig`, and the API says deleting one needs *"no running apps using the Lifecycle Configuration"* and its removal *"from UserSettings in all Domains and UserProfiles"*: every list change becomes detach, replace, re-attach, in a console the CLI cannot stand in for |

So [`gitlab/awsds/dev-env/dev-env/Dockerfile`](../../../gitlab/awsds/dev-env/dev-env/Dockerfile) §7 sets the six as `ENV`, plus the
two files the variables alone do not cover — `/etc/apt/apt.conf.d/01proxy` and a sudoers `env_keep`,
because `sudo` resets the environment (measured 2026-09-08, and true under every candidate).

**The list is a dated literal in the Dockerfile**, Sandbox's: the output `no_proxy_all_groups` of
`<account>/egress`, verbatim. The copy under `gitlab/` carries the reading of 2026-10-26 (73 entries,
sha256 `61f1e1646df12c14`, the `mwaa` group's `airflow-serverless.us-west-2.api.aws` the newest), which
reaches GitLab with the next release's merge request; version 10, `default-v0.9.1`, bakes the reading of
2026-10-18 (72 entries, sha256 `6faf2e4761622508`, the `mlflow` group's names among them), and version 9,
`default-v0.8.0`, the reading of 2026-10-10 (70 entries, sha256 `aafa08da98a61f5c`). The image
serves every session, so it carries every optional endpoint group's names whatever `GROUPS=` a session
names. Without them, a session that turns a group on sends that group's calls out through the proxy as
public calls; with them, a session that leaves it off times out on those names. The output reads each
service's `private_dns_names` from the endpoint-service catalog at plan time, which returns exactly the
names the module reads from `dns_entry` on an endpoint that exists (compared on seven services,
2026-10-10), so it does not depend on which groups any apply named. `no_proxy`, beside it, names only
the endpoints the slice's **last apply** created — 51 entries under `GROUPS=redshift` — and is the wrong
value for the image. The comment beside the list carries the command, because the names are generated
rather than derivable from a service token. A second account overrides it at build time with
`--build-arg NO_PROXY_LIST=…` rather than editing the file. The section sits last in the file so its
`ENV` does not reach the build's own `RUN` steps, which run in `VPC-SharedServices` against a different
endpoint set.

### What an endpoint change costs

The price of this choice, and the reason it is written here rather than remembered: **the image is
shaped by one VPC's endpoint list**. A change to that list — including one nobody typed, as when
`sandbox/egress` went 28 → 50 entries on a module bump — makes every existing image stale, and the
repair is the whole chain:

1. `./scripts/check-gitlab-mirror.py` (`--plan` with the session down) reads the new value, the output
   `no_proxy_all_groups` whatever `GROUPS=` the apply named, against the recipe's copy and writes the
   line `dev-env/Dockerfile` §7 must carry; put it in the GitLab project `awsds/dev-env`, with its date,
   and copy the project back with `./scripts/gitlab-mirror.py`. The value
   depends on no resource, so with the session down a `terraform plan` on the slice prints it under
   *Changes to Outputs*, as the authoring plan of `vpc-egress-v0.17.0` printed it before the output
   existed (2026-10-10).
2. A release ([`gitlab/awsds/dev-env/README.md`](../../../gitlab/awsds/dev-env/README.md)): `base` if it moved, then `dev-env`, pushed
   under a **new tag** (the repositories are tag-immutable), and the version `register` creates (§B).
3. **Every existing space moved to the new version** (§B, *Moving a space*). A space keeps the version it
   was created on, so the stale list stays in it until it moves, and the move is what an endpoint change
   cannot skip.
4. Every space restarts. A running app keeps the environment it started with, under any mechanism.

**What reports the divergence** is `./aws/devenv.py`: it reads `no_proxy_all_groups` out of
`<account>/egress`'s state and compares it with the Dockerfile's literal exactly, naming each side's
extra entries (`DE-1`..`DE-4`, exit 2 on a divergence in either direction), and `DE-6` fails on a name
the last apply's endpoints answer for that the catalog reading lacks — one the image would lack while
`DE-3` passes. It compares the **repository**, so it cannot see an image older than the file. That
second gap is what `/opt/awsds-proxy.txt` closes — the entry count and the first 16 hex of the list's
sha256, written at build time. From inside a space:

```bash
cat /opt/awsds-proxy.txt
```

against the operator's side, in the account the space runs in:

```bash
AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/egress output -raw no_proxy_all_groups | shasum -a 256 | cut -c1-16
```

Two different digests mean the image predates the current endpoint set, and the first symptom to expect
is not a refusal but a **success without `aws:SourceVpce`** for a name added since the build — which
CloudTrail shows and the space does not.

## B. A release, the retirement, and moving a space

A steward approves a digest at the `release-gate` of the GitLab project `awsds/dev-env`, and its
`register` job creates the release's image version in every target account (Stage 8 decisions 7 and 18,
taken 2026-10-15). Nothing in this repository changes and no domain write follows: each domain attaches
the image with no version number (§C6), so the portal offers the new version at once, at the top of the
picker, and a new space created on it pins it. A **list change** reaches the same place by a longer road,
§E's chain, because the proxy environment is baked at build time.

A release's tag pipeline runs on all three runners: `build-images` and the two scans on the build runner,
`release-gate` on the test runner, `register` and `retire` on the deploy runner. Its GitLab session is
therefore `make gitlab-up BUILD=1` ([`gitlab.md`](gitlab.md) §U), and without the flag the chain stops at
`build-images`, *stuck* with no runner to take it.

### The release, and the reading that ends it

1. **Read the evidence and run the gate**: the steward's acts, in
   [`gitlab/awsds/dev-env/README.md`](../../../gitlab/awsds/dev-env/README.md)'s *Releasing*.
2. **`register`**, on the deploy runner as each target's `awsds-deploy-devenv-<unit>` role:
   `release/versions.py register` calls `create-image-version` from the pushed digest,
   `<repository>@sha256:…`, with the release's semver as an alias and the tag as the release notes. It
   waits for `CREATED` and fails unless the version's `ContainerImage` is the pushed digest. A release
   already registered is reported and not created again; a semver another version holds is refused, since
   that release is spent.
3. **`retire`**: *The retirement*, below.
4. **Read it back** from the laptop when the job's log is not enough:

   ```bash
   aws sagemaker list-image-versions --image-name awsds-sandbox-dev-env --profile awsds-infra-sandbox-1 --query 'ImageVersions[].[Version,ImageVersionStatus]' --output text
   ```

   ```bash
   aws sagemaker describe-image-version --image-name awsds-sandbox-dev-env --version-number <n> --profile awsds-infra-sandbox-1 --query '[ImageVersionStatus,ContainerImage]' --output text
   ```

By hand, step 2 is the same script, from a checkout of `awsds/dev-env` or from its copy here, as the
infrastructure user; the target the deploy runner finds by its profiles' names is named instead:

```bash
python3 gitlab/awsds/dev-env/release/versions.py register --target awsds-infra-sandbox-1 --tag <tag> --digest <sha256:digest>
```

The deploy role holds what the script calls and nothing else: the image's versions created, read and
deleted, their aliases, and every space and domain read (Stage 8 step 4.2, INT-18). Its ceiling denies
every domain write, every space write and every role change, so the one domain write per domain
(§C6) and the moves below stay the steward's.

**The readings behind this order**, all measured 2026-10-15 on a probe image (the Stage 8 log):

| Reading | What it settles |
|---|---|
| An entry with no `ImageVersionNumber` makes the picker list every version, newest first, `<display name> v<n>`; a version created afterwards appears with no domain write | a release needs no domain write |
| The portal's `CreateSpace` carries the chosen version's ARN, and the space keeps it while newer versions arrive | a release reaches an existing space only when the space moves |
| `update-domain` on `CustomImages` was accepted with apps running, four times | no app is deleted around a domain write (§C6) |
| `VendorGuidance` `TO_BE_ARCHIVED` and `ARCHIVED` change nothing in the picker, and an archived version still starts the space that names it | archiving retires nothing |
| A deleted version leaves the picker at once, with the domain `InService` and an app running on it still running; the space naming it is stranded at its next start (`EXC-09`) | a retirement deletes, and never a version a space names |
| A space whose spec names an alias resolves it at each start and follows the alias to another version; the portal then banners it as an outdated SageMaker Distribution | an alias labels a release and pins no space |

### The retirement

`retire` runs after `register`, on the same runner: `release/versions.py retire --keep 10` keeps the
newest 10 versions and deletes every older one that no space and no domain names. A version a space still
names stays, and the job lists the space: the steward moves it (below) before its version can go, because
a space whose version is deleted does not start (measured 2026-09-12, with no fallback to the domain
default). A domain entry that still carries a number keeps its version too. So a retirement strands no
space, and a version in use outlives the history of 10 for as long as a space names it.

What it would delete, read without deleting anything:

```bash
python3 gitlab/awsds/dev-env/release/versions.py retire --dry-run --target awsds-infra-sandbox-1
```

### Moving a space to another version

A space keeps the version it was created on, so a release reaches an existing space only when the space
moves: by its owner, in the portal (*Spaces*, the space's menu, *Configure space*, *Image*, with the space
stopped), or by the steward when a release must reach every space, as an endpoint change does (§E), or
when `retire` lists a space on a version past the history.

Every space's version, read first:

```bash
for SP in $(aws sagemaker list-spaces --domain-id-equals <domain-id> --profile awsds-infra-sandbox-1 --query 'Spaces[].SpaceName' --output text); do printf '%-50s ' "$SP"; aws sagemaker describe-space --domain-id <domain-id> --space-name "$SP" --profile awsds-infra-sandbox-1 --query 'SpaceSettings.[CodeEditorAppSettings.DefaultResourceSpec.SageMakerImageVersionArn,JupyterLabAppSettings.DefaultResourceSpec.SageMakerImageVersionArn]' --output text; done
```

**The portal is the route to prefer.** The user moved `remote-editor-claude` there on 2026-09-12, and it
came up with `RemoteAccess: ENABLED`, its 64 GB and the project's S3 connection intact. **The CLI route
ran once**, on a probe space on 2026-10-15: `update-space` with the space's live `SpaceSettings` was
accepted and kept the idle settings, the volume, `RemoteAccess` and the S3 mount, while
`SpaceManagedResources: ENABLED`, sent with the block, was gone from the read afterwards, a loss nothing
here explains. When the CLI is the only way, the block is the live read with the version ARN's trailing
number changed and every other field kept, the space's app stopped first:

```bash
aws sagemaker describe-space --domain-id <domain-id> --space-name <space> --profile awsds-infra-sandbox-1 --query SpaceSettings | jq --arg n "<version number>" '(.. | objects | select(.SageMakerImageVersionArn) | .SageMakerImageVersionArn) |= sub("/[0-9]+$"; "/" + $n)' > "$HOME/tmp/space.json" && cat "$HOME/tmp/space.json"
```

```bash
aws sagemaker update-space --domain-id <domain-id> --space-name <space> --space-settings "file://$HOME/tmp/space.json" --profile awsds-infra-sandbox-1
```

**Read the generated block before the second command.** The `..` walk rewrites every app type's spec in
one pass. A hand-written block would drop what the live read carries besides the spec: `AppType`, the
volume size, `RemoteAccess`, without which the remote IDE stops working, and the project's S3 connection
(Lesson 60 for the risk, Lesson 61 for the file: regenerate it, never reuse one an earlier move left in
`$HOME/tmp`).

## X. Detaching and removing

Order matters, and it is the reverse of §C: the domain first, the objects after. **Do not expect the
service to enforce it.** AWS does not promise a refusal on deleting an attached image — it promises a
later failure: *"You must first detach your custom image from your domain before deleting the image from
the SageMaker AI image store. If not, you may experience errors while viewing your domain information or
attaching new custom images to your domain."* So the order is the operator's to keep, and the symptom of
breaking it arrives on the next attach rather than on the delete.

Step 1 ran on 2026-09-11 and on 2026-10-15, as the detach half of the replace §B used to be; steps 2 and
3 are unexercised. A release needs none of this section: §X removes the image.

1. Empty `CustomImages` — the console's *Detach*, or the two commands below. **An empty list, not a
   removed key**: a block sent without the key left both attachments exactly as they were (2026-09-11),
   so the field has to be present and empty. They read the live block, and nothing here depends on a
   file an earlier step left behind (Lesson 61).

   ```bash
   aws sagemaker describe-domain --domain-id <domain-id> --profile awsds-infra-sandbox-1 --query DefaultUserSettings | jq '.JupyterLabAppSettings.CustomImages = [] | .CodeEditorAppSettings.CustomImages = []' > "$HOME/tmp/detached.json" && cat "$HOME/tmp/detached.json"
   ```

   ```bash
   aws sagemaker update-domain --domain-id <domain-id> --default-user-settings "file://$HOME/tmp/detached.json" --profile awsds-infra-sandbox-1
   ```
2. `terraform apply -destroy` on the slice, or delete the resources from the code and apply. The
   versions are not in the slice's state, and `DeleteImage` deletes every version of the image with it,
   as the probe image's deletion did on 2026-10-15.
3. The ECR image is not this slice's to remove: the repository's lifecycle policy expires it, and
   `gitlab/awsds/dev-env/README.md` owns that rule.

## V. Reading it back, and what each instrument proves

| Question | Command | What it proves |
|---|---|---|
| Is the version registered, and against which digest? | `aws sagemaker describe-image-version --image-name awsds-sandbox-dev-env --version-number <n>` | `ImageVersionStatus: CREATED` and `ContainerImage` naming the `sha256:` the steward pushed; `register` fails on any other |
| Which versions are held, and which release is each? | `aws sagemaker list-image-versions --image-name awsds-sandbox-dev-env`, then `list-aliases --version-number <n>` | the history the picker offers; each version's alias is its release's semver, from version 8 on (version 7 predates decision 18) |
| Do the configurations exist, and do they carry an environment? | `aws sagemaker describe-app-image-config --app-image-config-name awsds-sandbox-dev-env-jupyterlab` | the app type binding; today an empty `ContainerConfig` is the expected reading (§E) |
| Does the domain offer the image? | `describe-domain … --query 'DefaultUserSettings.JupyterLabAppSettings.CustomImages'` | the attachment, which no Terraform state records |
| Did the registration read the repository across the boundary? | `aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=BatchGetImage --profile awsds-infra-prod` | the image role as `AWSAccount`/`…:SageMaker` on `awsds-prod-ecr-dev-env` (§C5) |
| Did a **space** pull it, and which version? | the same lookup, in the window a space started | the project role rather than the image role, and **by digest** rather than by tag, which names the version the space resolved — measured 2026-09-10, both app types, and 2026-10-15 for a pinned, an archived and an aliased version |
| Is the baked `NO_PROXY` still the account's? | `./aws/devenv.py`, `DE-1`..`DE-3`, `DE-6` | the **recipe** against the account's `no_proxy_all_groups`, name by name and both ways; `DE-6` that the last apply's endpoints answer for no name that list lacks. An image built from an older checkout passes these |
| Does the image the registry holds carry it? | `./aws/devenv.py`, `DE-5` | the **bytes**: the latest version's digest, its manifest, its config blob hash-checked, and the six variables in its `Env`. Verified both ways 2026-09-12 — `v0.4.0` bakes all six, `v0.1.0` none |
| Which image is a space **running**? | `describe-app … --query ResourceSpec`, or `cat /opt/awsds-proxy.txt` inside it | the only reading that separates this image from AWS's distribution in the same picker, and `describe-app` still answers after the app is deleted (§C7) |
| Does every space still name a version that exists? | the `describe-space` loop in §B, *Moving a space*, or `release/versions.py retire --dry-run` | a space's own copy of the version number, which overrides the domain default; a space naming a deleted version does not start (`EXC-09`), and `retire` keeps every version a space names |

## F. Failures, and what each one is

| Symptom | What it is | What to do |
|---|---|---|
| `ValidationException … length less than or equal to 256` at `CreateAppImageConfig` | a value over the API's cap, and `NO_PROXY` is the one that trips it | §E — the delivery is not this object's |
| `ImageVersionStatus: CREATE_FAILED`, with a `FailureReason` naming permissions | the image role cannot read the repository: the identity half (§C5) or the repository policy half is missing | fix the half named, delete the failed version, and run `register` again |
| `register` refuses: the semver is another version's alias | that release was registered from another digest, and a release is spent once | release a new semver |
| `retire` keeps a version past the newest 10, naming a space | the space still names it, and deleting it would strand the space | move the space (§B), and the next `retire` deletes the version |
| The image does not appear in the portal's picker | the attachment, not the registration | re-read §C7's `describe-domain`; if the entry is there, try the `DefaultSpaceSettings` block, which is §C6's unmeasured fallback |
| The picker offers one version where the image holds several | the domain's entry carries an `ImageVersionNumber` | attach with no number (§C6) |
| A space shows *outdated SageMaker Distribution images* in the portal | its spec names an alias: the portal reads any alias as the distribution's | move it to a version number (§B); nothing is wrong with the image |
| A space stays in *starting* and never comes up | a pull that cannot complete: `ecr.dkr`, `ecr.api` or the S3 gateway endpoint absent, or the session down | `make up ENV=<env>`, then `./aws/egress.py` |
| A space starts, and the terminal has no proxy | the space is on the stock image, or on `default-v0.1.1` or earlier — the environment arrived with `default-v0.2.0` | select the house image (§C7); on an older one, the by-hand export is [`sg-proxy.md`](sg-proxy.md) |
| `sudo apt` fails to resolve a name that is on the plane | on `default-v0.1.1` or earlier, `sudo` resets the environment and `apt` runs with none of the six variables | the `-o Acquire::http::Proxy=` form in `sg-proxy.md`; `default-v0.2.0` carries the two image-side files that end it |
| `update-domain` returns success and `CustomImages` is unchanged | the key was omitted rather than sent empty; an absent field reads as *unchanged* here | send `"CustomImages": []` — §X step 1's command |
| `update-domain` refuses, naming applications | the vendor's page gates a custom-image change on every app being deleted; on 2026-10-15 the service accepted four such writes with apps running, so a refusal is new | `./scripts/down-studio-apps.py <env>`, `list-apps` until it is empty, then record the refusal in the stage log |
| An AWS call from a space arrives with no `aws:SourceVpce`, and nothing failed | a name added to the endpoint set after the image was built: it is not in the baked `NO_PROXY`, so it went out through the proxy | compare `/opt/awsds-proxy.txt` against the current list (§E), then rebuild |

---

*Runbook index: [`CLAUDE.md`](../../../CLAUDE.md)'s routing table · Stage: [6d](../stages/stage-06d-unified-studio-remainder.md)*
