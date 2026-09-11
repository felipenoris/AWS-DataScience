# Runbook — the dev-env image in SageMaker

| | |
|---|---|
| **Scope** | The house image as SageMaker AI sees it: the `[P]` slice that registers it in a member account (`sandbox/dev-env/`), the attachment that makes it appear in the portal's image list, the version bump when a steward approves a new build, and the detach. The build and the push are [`images/README.md`](../../../images/README.md)'s and [`buildbox.md`](buildbox.md)'s; the naming rule is [`docs/SMUS.md`](../../SMUS.md)'s. This file is what runs **per account and per release**, forever |
| **Operator** | The **infrastructure user** — account **Sandbox** (or the member account being configured), permission set **`InfrastructureAccess`**, profile `awsds-infra-sandbox-1`. §C's registry read also touches Production through `awsds-infra-prod`, and one SSO login covers both. Every write is authorized per occurrence. §C6 is the one act this repository does not own in code |
| **The rules** | **The domain is the blueprint's object, not Terraform's.** `Tooling` provisions the SageMaker AI domain per project, so the attachment (§C6) is a hand step against a live object and never an `import` (Lesson 17). **A registered version is frozen to a digest**: SageMaker resolves the tag once, at `CreateImageVersion`, and a rebuilt tag would not move it — the repositories are tag-immutable anyway. **Half a proxy environment is worse than none** (§E) |
| **The picture around it** | Why there is a house image at all: [D17](../decisions/D17-interactive-vs-runtime.md) and `images/README.md`. What a space reaches once it starts: [`docs/NETWORK.md`](../../NETWORK.md) and [`sg-proxy.md`](sg-proxy.md). What the portal does with the image: [`docs/SMUS.md`](../../SMUS.md), *Custom images (BYOI)* |
| **Written** | 2026-09-10, at [Stage 6d](../stages/stage-06d-unified-studio-remainder.md) step 2, from the applies it describes. §C steps 1-6 and §V ran that day, on `default-v0.1.1` in Sandbox — §C6 by the CLI route, with the whole settings block diffed before and after. §C7, §B and §X are written from the API contract and the vendor pages (the 2026-09-10 rows of [`docs/REFERENCES.md`](../../REFERENCES.md)) and are **unexercised** — each says so in place (Lesson 37) |

---

## O. The objects, and who owns each

Four objects stand between a container in ECR and a data scientist choosing it in the portal. Only the
first three are this repository's.

| Object | What it is | Owner |
|---|---|---|
| **Image** | the named thing a domain attaches. Account-scoped, versionless, carries a `RoleArn` | `sandbox/dev-env/`, Terraform |
| **Image version** | one immutable pointer at one container image. Numbered by the service, 1 upwards | `sandbox/dev-env/`, Terraform |
| **App image configuration** | how a space starts that container: entrypoint, arguments, environment. One per app type | `sandbox/dev-env/`, Terraform |
| **`CustomImages` on the domain** | the list a space's image picker is built from | the **`Tooling` blueprint**, and §C6 by hand |

The seam is the fourth row, and it is a per-app-type field of the domain's **user settings** —
`JupyterLabAppSettings.CustomImages`, `CodeEditorAppSettings.CustomImages`. A **space** cannot name an
image: `SpaceSettings.CodeEditorAppSettings` is a different shape and carries neither `CustomImages` nor
`LifecycleConfigArns`. That is why every delivery question in this file lands on the domain, and why the
answer to *can we do this per space* is no.

## C. Configuring an account so a custom image is selectable

The checklist for a **new case** — a new member account, a new project's domain, or the first image in
either. Steps 1-2 are read-and-check; 3-6 are the work; 7 is the proof.

### 1. What must already exist

| Prerequisite | How to check it | If it is missing |
|---|---|---|
| The image, built and pushed under a `<flavour>-v<semver>` tag | `aws ecr describe-images --repository-name awsds-prod-ecr-dev-env --profile awsds-infra-prod` | [`buildbox.md`](buildbox.md) §P — a build session, not a five-minute job |
| The repository's pull grant naming this account | `aws ecr get-repository-policy --repository-name awsds-prod-ecr-dev-env --profile awsds-infra-prod` — the `AllowConsumerAccountsToPull` statement | add the account to `REGISTRY_CONSUMERS` (`scripts/tfhygiene/backend.py`) and apply `production/registry/` |
| `ecr.api` and `ecr.dkr` endpoints in the account's VPC | they are in `vpc-egress`'s `core_services`, so `make up ENV=<env>` is enough | there is no NAT anywhere (D38): without them a space cannot pull at all |
| The SMUS domain for the project, and the account association | `./aws/studio.py` | [Stage 6a](../stages/stage-06a-unified-studio.md); an image cannot be attached to a domain that does not exist |

### 2. The image's own shape

Not repeated here: the ancestor (`public.ecr.aws/sagemaker/sagemaker-distribution` ≥ `2.6-cpu`), the
absent `ENTRYPOINT`, AWS's three owned paths, and the `jupyterlab/default` base URL with its health check
on 8888 are [`images/README.md`](../../../images/README.md)'s *Before editing either file* and the vendor's
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
   from the generated tfvars, so `image_tag` is usually the only edit.

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

Applying it is authorized per occurrence, and the plan to read is the saved one. A first apply is six
resources: the image, its version, two app image configurations, the image role and the role's inline
policy. `aws_sagemaker_image` takes about a minute; everything else is immediate.

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

**The console route, and the one to prefer for a one-off.** SageMaker AI console → *Admin
configurations* → *Domains* → the project's domain → *Environment* → *Custom images for personal Studio
apps* → **Attach image** → *Existing image*, then the image and version this slice created, and the app
type matching the Dockerfile. The wizard assembles the settings block itself, which is what makes it
the safer route for a one-off — that it preserves every other field of `DefaultUserSettings` is the
shape of the wizard rather than a reading of this domain, so `describe-domain` afterwards is still the
proof (§C7).

**The CLI route, for a scripted or repeated case.** `UpdateDomain` replaces `DefaultUserSettings` as a
whole: every field not passed back is deleted, and this domain's block carries idle shutdown, the
`shared` S3 mount, the storage ceiling, the portal settings and `AutoMountHomeEFS`, none of which any
error would mention afterwards (Lesson 60). So read, edit, send back — never hand-write a minimal block:

```bash
aws sagemaker describe-domain --domain-id <domain-id> --profile awsds-infra-sandbox-1 --query DefaultUserSettings > "$HOME/tmp/user-settings.json"
```

**That file is the rollback, so it is not the file you edit.** It holds the block as it was before the
write, and it is the only copy of it: edit into a second file and keep this one until §C7's read-back
has passed.

**It is a rollback for this sitting, and for nothing later.** Any later act on this domain — the detach
of §X, the re-attach of §B — reads the block again first. Sending back a kept snapshot is a
full-replace with a picture of the past: whatever changed in between goes away, and no error mentions
it. The file is safe to use only while it is still true, which is only while nobody else has written.

Add to the copy — `terraform output -json custom_images` on the slice prints both entries in the API's
own spelling, so nothing is retyped:

```json
"JupyterLabAppSettings": {
  "CustomImages": [
    { "ImageName": "awsds-sandbox-dev-env", "ImageVersionNumber": 1, "AppImageConfigName": "awsds-sandbox-dev-env-jupyterlab" }
  ]
}
```

`JupyterLabAppSettings` already exists in the block with its `AppLifecycleManagement`; `CustomImages` is
added beside it, not in place of it. The Code Editor entry is the same three keys under
`CodeEditorAppSettings`, naming `awsds-sandbox-dev-env-codeeditor`.

```bash
aws sagemaker update-domain --domain-id <domain-id> --default-user-settings "file://$HOME/tmp/user-settings-with-images.json" --profile awsds-infra-sandbox-1
```

**Then diff the whole block, not the key you added.** The hazard is a field that went missing, and
`--query CustomImages` cannot see one. Read the block back and compare it against the file you kept:

```bash
aws sagemaker describe-domain --domain-id <domain-id> --profile awsds-infra-sandbox-1 --query DefaultUserSettings > "$HOME/tmp/user-settings-after.json" && diff <(python3 -m json.tool "$HOME/tmp/user-settings.json") <(python3 -m json.tool "$HOME/tmp/user-settings-after.json")
```

The only differences must be the entries you added. Anything else — a missing mount, a dropped idle
setting — is Lesson 60 having happened, and the kept file is what puts it back.

**`ImageVersionNumber` is a decision, not a formality.** The API marks the field optional, and what an
omitted version resolves to — the latest, by the vendor's description — is unread here. Name it: a
version named is a version reviewed, and §B's bump then reaches a space only when somebody moves this
number.

**A SMUS space reads the user-settings block, measured 2026-09-10.** The experiment had its control:
`DefaultSpaceSettings` carried no `CustomImages` and no `CodeEditorAppSettings` at all, read after the
attach. The picker offered the image and **both a JupyterLab and a Code Editor space started on it**,
so the domain's `DefaultUserSettings` is the attachment point and `DefaultSpaceSettings` is the fallback
nobody needs. One image serves both app types here, which the Dockerfile does not promise — it is
JupyterLab-shaped by the vendor's rule — so treat it as a reading about this image rather than a
property of BYOI.

### 7. Selecting it, and reading the attachment back

In the portal, as a data scientist: the project's *Compute* → *Spaces*, create a JupyterLab space, and the
image appears under the custom images beside the SageMaker Distribution versions. That the picker offers
it is the whole of this section's proof; that a space **starts** on it is the endpoints' and the pull
grant's proof, and it is where a missing `ecr.dkr` shows up as a start that never finishes.

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
| `ContainerEnvironmentVariables` on the app image configuration | each value caps at 256 characters (`ContainerConfig`: 25 entries, 256 per key and per value) against a `NO_PROXY` of about 2,300 — `CreateAppImageConfig` refuses it outright, measured at step 2.2 |
| A lifecycle configuration | it fits — a 16 KB script — but there is no `UpdateStudioLifecycleConfig`, and the API says deleting one needs *"no running apps using the Lifecycle Configuration"* and its removal *"from UserSettings in all Domains and UserProfiles"*: every list change becomes detach, replace, re-attach, in a console the CLI cannot stand in for |

So [`images/dev-env/Dockerfile`](../../../images/dev-env/Dockerfile) §6 sets the six as `ENV`, plus the
two files the variables alone do not cover — `/etc/apt/apt.conf.d/01proxy` and a sudoers `env_keep`,
because `sudo` resets the environment (measured 2026-09-08, and true under every candidate).

**The list is a dated literal in the Dockerfile**, Sandbox's, read on 2026-09-10 (50 entries,
sha256 `856bc57bb73c4134`). The comment beside it carries the command that produces the current value —
`terraform output -raw no_proxy` on `<account>/egress` — because the list is generated there and eight
of its names are not derivable from a service token. A second account overrides it at build time with
`--build-arg NO_PROXY_LIST=…` rather than editing the file. The section sits last in the file so its
`ENV` does not reach the build's own `RUN` steps, which run in `VPC-SharedServices` against a different
endpoint set.

### What an endpoint change costs

The price of this choice, and the reason it is written here rather than remembered: **the image is
shaped by one VPC's endpoint list**. A change to that list — including one nobody typed, as when
`sandbox/egress` went 28 → 50 entries on a module bump — makes every existing image stale, and the
repair is the whole chain:

1. `make up ENV=<env>`, read the new value (`terraform output -raw no_proxy`) and put it in
   `images/dev-env/Dockerfile` §6, with its date.
2. A buildbox session ([`buildbox.md`](buildbox.md) §U): `base` if it moved, then `dev-env`, and a push
   under a **new tag** — the repositories are tag-immutable.
3. `image_tag` in [`terraform-live/sandbox/dev-env/variables.tf`](../../../terraform-live/sandbox/dev-env/variables.tf), then apply — a version replace (§B).
4. Re-attach: the domain's `CustomImages` names a version number (§C6).
5. Every space restarts. A running app keeps the environment it started with, under any mechanism.

**What reports the divergence** is `./aws/devenv.py`: it reads the account's list out of
`<account>/egress`'s state and compares it with the Dockerfile's literal, naming each side's extra
entries (`DE-1`..`DE-4`, exit 2 on a divergence). It compares the **repository**, so it cannot see an
image older than the file. That second gap is what `/opt/awsds-proxy.txt` closes — the entry count and
the first 16 hex of the list's sha256, written at build time. From inside a space:

```bash
cat /opt/awsds-proxy.txt
```

against the operator's side, in the account the space runs in:

```bash
AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/egress output -raw no_proxy | shasum -a 256 | cut -c1-16
```

Two different digests mean the image predates the current endpoint set, and the first symptom to expect
is not a refusal but a **success without `aws:SourceVpce`** for a name added since the build — which
CloudTrail shows and the space does not.

## B. A new build, and the version bump

A steward approves a digest, the tag lands in both repositories, and the change here is one line:
`image_tag` in the slice's `variables.tf`. A **list change** reaches this same place by a longer road —
§E's chain — because the proxy environment is baked at build time.

`base_image` is force-new, because a SageMaker image version is immutable. The plan therefore reads
`1 to add, 1 to destroy` on `aws_sagemaker_image_version` — the image itself and both configurations stay
— and after the apply the version number has moved.

**Detach before the apply, and the vendor says why.** Terraform replaces by destroying first, and the
version it destroys is the one the domain's `CustomImages` names. AWS does not promise a refusal — it
promises a **later** failure: *"You must first detach your custom image from your domain before deleting
the image from the SageMaker AI image store. If not, you may experience errors while viewing your domain
information or attaching new custom images to your domain."* The second half of that sentence is the
re-attach, so skipping the detach breaks the step that would have repaired it. So: detach (§X step 1),
apply, re-attach on the new number.

**Both halves need the domain's apps deleted first**, from the same page: *"Before you can update the
custom images, you must delete all of the applications in your domain."* Not the user profiles and not
the spaces — the running apps. `make down ENV=sandbox` is this estate's way (Stage 6d step 5.2), or stop
the space in the portal when the session's endpoints are still wanted. `aws sagemaker list-apps
--domain-id-equals <id>` is how to know before the call refuses. Omitting `ImageVersionNumber` at §C6 removes both hand steps and the
review gate with them. What a space starts then depends on §C6's decision: a
domain pinned to `ImageVersionNumber: 1` still serves the old version, which the apply has just deleted,
so **the attachment is updated in the same sitting as the bump**, or the picker offers a version that no
longer exists.

Stage 8 step 1's pipeline takes this slice over (INT-18): the same two acts, with the digest arriving from
the approval rather than from an editor.

## X. Detaching and removing

**Unexercised.** Order matters, and it is the reverse of §C: the domain first, the objects after. A
version cannot be deleted while a domain names it, and an app image configuration cannot be deleted while
a `CustomImages` entry references it — both refuse with a `ResourceInUse`-shaped error naming the domain,
which is the guard rather than a problem.

1. Remove the entry from `CustomImages` — the console's *Detach*, or the same read-edit-send as §C6,
   **built from a fresh `describe-domain`** and never from a file kept since the attach.
2. `terraform apply -destroy` on the slice, or delete the resources from the code and apply.
3. The ECR image is not this slice's to remove: the repository's lifecycle policy expires it, and
   `images/README.md` owns that rule.

## V. Reading it back, and what each instrument proves

| Question | Command | What it proves |
|---|---|---|
| Is the version registered, and against which digest? | `aws sagemaker describe-image-version --image-name awsds-sandbox-dev-env --version-number <n>` | `ImageVersionStatus: CREATED` and `ContainerImage` naming a `sha256:` — the tag was resolved once, and the digest is the one the steward pushed |
| Do the configurations exist, and do they carry an environment? | `aws sagemaker describe-app-image-config --app-image-config-name awsds-sandbox-dev-env-jupyterlab` | the app type binding; today an empty `ContainerConfig` is the expected reading (§E) |
| Does the domain offer the image? | `describe-domain … --query 'DefaultUserSettings.JupyterLabAppSettings.CustomImages'` | the attachment, which no Terraform state records |
| Did the registration read the repository across the boundary? | `aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=BatchGetImage --profile awsds-infra-prod` | the image role as `AWSAccount`/`…:SageMaker` on `awsds-prod-ecr-dev-env` (§C5) |
| Did a **space** pull it? | the same lookup, in the window a space started | the project role rather than the image role, and **by digest** rather than by tag — measured 2026-09-10, both app types |
| Is the baked `NO_PROXY` still the account's? | `./aws/devenv.py` | the repository's two copies, name by name; an image older than the Dockerfile is the gap it cannot see (§E) |

## F. Failures, and what each one is

| Symptom | What it is | What to do |
|---|---|---|
| `ValidationException … length less than or equal to 256` at `CreateAppImageConfig` | a value over the API's cap, and `NO_PROXY` is the one that trips it | §E — the delivery is not this object's |
| `ImageVersionStatus: CREATE_FAILED`, with a `FailureReason` naming permissions | the image role cannot read the repository: the identity half (§C5) or the repository policy half is missing | fix the half named, then taint and re-apply the version |
| The image does not appear in the portal's picker | the attachment, not the registration | re-read §C7's `describe-domain`; if the entry is there, try the `DefaultSpaceSettings` block, which is §C6's unmeasured fallback |
| A space stays in *starting* and never comes up | a pull that cannot complete: `ecr.dkr`, `ecr.api` or the S3 gateway endpoint absent, or the session down | `make up ENV=<env>`, then `./aws/egress.py` |
| A space starts, and the terminal has no proxy | the space is on the stock image, or on a `dev-env` built before 2026-09-10 | select the house image (§C7); until one is attached, the by-hand export is [`sg-proxy.md`](sg-proxy.md) |
| `sudo apt` fails to resolve a name that is on the plane | on an image built before 2026-09-10, `sudo` resets the environment and `apt` runs with none of the six variables | the `-o Acquire::http::Proxy=` form in `sg-proxy.md`; the durable fix is the Dockerfile's two files, live since §E's decision |
| An AWS call from a space arrives with no `aws:SourceVpce`, and nothing failed | a name added to the endpoint set after the image was built: it is not in the baked `NO_PROXY`, so it went out through the proxy | compare `/opt/awsds-proxy.txt` against the current list (§E), then rebuild |

---

*Runbook index: [`CLAUDE.md`](../../../CLAUDE.md)'s routing table · Stage: [6d](../stages/stage-06d-unified-studio-remainder.md)*
