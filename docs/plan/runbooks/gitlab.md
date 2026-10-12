# Runbook — GitLab

| | |
|---|---|
| **Scope** | The GitLab host (`production/tooling/`, `[D]`), its anchors (`production/foundation/`), the internal CA that certifies it (`production/pki/`), the build runner (`production/runners/`, `[E]`) and the acts a person performs on them. Built by [Stage 7](../stages/stage-07-gitlab-runners-ecr.md); the design is in the stage file and the slices' own comments, and this file repeats none of it |
| **Operator** | The **infrastructure user** through `awsds-infra-prod` (Production, `InfrastructureAccess`) for every AWS act; GitLab's local administrator (`felipenoris`, §I) or a SAML user for everything inside GitLab's UI |
| **Instruments** | `./aws/supplychain.py` (`SC-1`..`SC-12`), `./aws/proxy.py`, `./aws/egress.py` §6 at the session's end |

## S. The pieces

| Piece | Where | Layer |
|---|---|---|
| the host `awsds-prod-gitlab`, a `t4g.large` | `VPC-SharedServices`, private tier, az1 | `[D]` `production/tooling/` |
| its data volume, 50 GiB at `/var/opt/gitlab`, and the daily DLM snapshot (03:30 UTC, 7 kept) | the same slice | `[D]` |
| `gitlab.awsds.internal` and `*.awsds-pages.internal`, both A records to the host's private address | the two `[P]` zones of `production/foundation/`, the records in `tooling/` | `[D]` |
| `config/gitlab.rb`, rendered from `tooling/gitlab.rb.tftpl` | `s3://awsds-prod-gitlab-objects/config/gitlab.rb` | `[D]` object in a `[P]` bucket |
| the object-storage bucket, the backup bucket, their key `alias/awsds-prod-gitlab` | `production/foundation/` | `[P]` |
| `awsds-prod-gitlab-secrets` (`gitlab-secrets.json`), `awsds-prod-runner-token` | `production/foundation/`, containers only | `[P]` |
| the root CA, the two leaves, their keys in `awsds-prod-tls-gitlab` / `awsds-prod-tls-pages`, the certificates in `/datascience/prod/pki/*-pem` and `s3://awsds-prod-gitlab-objects/pki/` | `production/pki/` | `[P]`, never destroyed |
| the runner `awsds-prod-runner`, an `m8i.xlarge` | `VPC-SharedServices`, private tier, az1 | `[E]` `production/runners/` |
| the `secretsmanager` endpoint beside 6c's thirteen | `production/egress/` | `[E]` |

Everything reaches the internet through `proxy.awsds.internal:3128` and nothing else: there is no default route in the VPC (D38). Everything reaches AWS through the VPC's endpoints and the S3 gateway, which is what the bypass list says.

## U. The session: up and down

The hub is somebody else's dependency, so a GitLab session leaves it alone (Stage 7 step 1.6): `make gitlab-up` and `make gitlab-down` touch `tooling/`, `egress/` and `runners/` and nothing else, and both refuse while a hub host is stopped. `make up ENV=production` / `make down ENV=production` do the same for every Production `[E]` slice and never touch the hub pair either (refusal 6).

**Up**, in this order:

1. Sign in as the infrastructure user (Production, `InfrastructureAccess`; one login covers every `awsds-infra-*` profile):

   ```bash
   ./aws/login.py
   ```

2. The hub, unless `make status` already reads both hosts running:

   ```bash
   make hub-up
   ```

3. GitLab's slices: the host started, `VPC-SharedServices`' endpoints applied, the runner applied and registering at boot (§K):

   ```bash
   make gitlab-up
   ```

   Without the runner, for a session that runs no pipeline, and always until the runner's token is in its container (§K), or a runner boots that cannot register and bills until `gitlab-down`. `make gitlab-down` destroys the runner either way:

   ```bash
   make gitlab-up RUNNERS=0
   ```

4. The tunnel on the laptop ([client runbook](client-vpn-proxy-configuration.md) §1); `gitlab.awsds.internal` resolves through it and nowhere else.

5. `https://gitlab.awsds.internal` answers two to three minutes after a start (a start reconfigures nothing); the runner appears on `awsds/app-etl`'s **Settings → CI/CD → Runners** at the end of its own first boot (§K).

**Down**, in the reverse order:

1. The runner and the endpoints destroyed, then GitLab stopped:

   ```bash
   make gitlab-down
   ```

2. The tunnel down ([client runbook](client-vpn-proxy-configuration.md) §2), unless another session needs it.

3. The hub, unless another session is on it; then what is left to bill:

   ```bash
   make hub-down
   ```

   ```bash
   make status
   ```

Stopped, GitLab bills its two volumes and its snapshots; running, `make status` prices the host. The endpoints are `production/egress/`'s whole set, 14 at 0.010 USD/h each, the SageMaker pair and the data-plane three included (Stage 7 decision 9): a GitLab session carries them whether or not anything in the VPC calls them.

**The first boot** of a fresh instance took nine minutes to `gitlab Reconfigured!` on 2026-10-12 and fourteen to the end of cloud-init: the Omnibus package through the proxy, `gitlab-ctl reconfigure` (5 min), the readiness probe over loopback. Its log is `/var/log/awsds-gitlab-boot.log` on the host, readable with no SSM endpoint through the serial console:

```bash
aws ec2 get-console-output --profile awsds-infra-prod --region us-west-2 --instance-id "$(AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/tooling output -raw instance_id)" --latest --output text
```

**A shell** is Session Manager, from any network, as the infrastructure user; you land as `ssm-user` with passwordless `sudo`:

```bash
aws ssm start-session --profile awsds-infra-prod --region us-west-2 --target "$(AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/tooling output -raw instance_id)"
```

## P. The installation

There is no hand installation. A GitLab host is built by Terraform and configured by its own first boot; what a person touches is the applies, then §I. The order, for a host that does not exist yet:

1. **Prerequisites**, as the infrastructure user with the hub up (§U steps 1-2): `production/foundation/` applied (the two buckets, the key, the two secret containers), `production/pki/` applied (the root and the two leaves, published), `production/egress/` up (`./scripts/slices.py up --env production --only egress`). The bootstrap reaches S3 through the gateway, Secrets Manager and SSM through the endpoints and `packages.gitlab.com` through the proxy; without the endpoints it dies at its first `aws` call.

2. **The apply** ([terraform-changes.md](terraform-changes.md) Recipe A) in `terraform-live/production/tooling/`: `terraform init -backend-config=backend.hcl`, plan, apply. 17 resources on 2026-10-12: the two security groups, the role and its profile, the rendered `gitlab.rb` as the S3 object, the 50 GiB data volume, the instance, the attachment, the two records, the DLM role and policy, the alarm. `slices.py up` does not build: for a `[D]` slice it starts an instance that exists and says so when none does.

3. **The first boot**, cloud-init running `user-data.sh.tftpl` as root, logged to the serial console and to `/var/log/awsds-gitlab-boot.log` (§U gives the console command):
   1. the proxy into `/etc/environment`: the explicit proxy and the generated `NO_PROXY`;
   2. the data volume: the one disk that is not the root, formatted XFS only when it carries no filesystem (a re-attached volume keeps its data), mounted at `/var/opt/gitlab` by UUID through `/etc/fstab`;
   3. `jq` from the AL2023 repositories (S3, no proxy);
   4. the GitLab package repository for Amazon Linux 2023 with its three keys and `proxy=` set per repository, then `dnf install gitlab-ce` under `/etc/gitlab/skip-auto-reconfigure`, so the package installs without configuring;
   5. the fetch: `gitlab.rb` from `s3://awsds-prod-gitlab-objects/config/gitlab.rb`; the root into `/etc/gitlab/trusted-certs/`; the two leaves from their SSM parameters into `/etc/gitlab/ssl/<host>.crt`, each followed by the root, which is the chain the host serves; the two keys from Secrets Manager into `/etc/gitlab/ssl/<host>.key` at mode 600; `update-ca-trust`;
   6. `gitlab-secrets.json`: restored from `awsds-prod-gitlab-secrets` when the container holds a value, otherwise left for the reconfigure to generate;
   7. `gitlab-ctl reconfigure`, the first and the long one: Chef converges every service, initialises PostgreSQL and runs the migrations (5 min 03 s on 2026-10-12). `gitlab.rb` orders the supervisor after `network-online.target`, since Omnibus's default `After=multi-user.target` waits for cloud-init, which is waiting for this step;
   8. the generated `gitlab-secrets.json` pushed into its container, when step 6 generated nothing to restore;
   9. `/usr/local/sbin/awsds-gitlab-refresh` (§R) and the daily backup timer (§B) installed;
   10. the readiness probe over loopback, then `=== awsds gitlab first boot done`.

   Nine minutes to `gitlab Reconfigured!` and fourteen to the end, measured 2026-10-12.

4. **Then §I**: the root trusted on the laptop, the initial password, the first sign-in, the first refresh, the instance settings, the namespace.

**A rebuild.** `terraform apply -replace=aws_instance.gitlab` replaces the host and keeps the data volume: the bootstrap finds a formatted volume and mounts it, restores `gitlab-secrets.json` from its container, and the repositories, the database and the local Pages deployments are where they were. Adding `-replace=aws_ebs_volume.data` discards them, which is what the recovery from the first boot's deadlock did while the host held nothing (the stage log), and what the restore rehearsal in §B follows with a restore from the backup bucket. Neither touches `pki/` or the anchors.

## I. The initial setup, on a fresh host

Once per host: after the stage's first apply, and after a replacement or the restore rehearsal (§B). Done on 2026-10-12 for the host the stage built; the local administrator is **`felipenoris`** since that day, born `root` and renamed at the first sign-in, still local and still the break-glass.

1. **Wait for the bootstrap**, fourteen minutes from launch (§U's first boot): `=== awsds gitlab first boot done` in the console, or in the shell:

   ```bash
   sudo cloud-init status --wait
   ```

2. **Trust the root on the laptop** (§C's first surface). Without it every browser marks `https://gitlab.awsds.internal` "Not secure", and the SAML round-trip later (§A) stops at the same wall; the chain the host serves verifies against the published root and against nothing else (`Verify return code: 0 (ok)` with the root, `self signed certificate in certificate chain` with the system store, 2026-10-12):

   ```bash
   aws ssm get-parameter --profile awsds-infra-prod --region us-west-2 --name /datascience/prod/pki/ca-root-pem --query Parameter.Value --output text > "$HOME/awsds-root.crt"
   ```

   ```bash
   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$HOME/awsds-root.crt"
   ```

   Then restart the browser. Safari and Chrome read the keychain; Firefox reads it with `security.enterprise_roots.enabled` set to `true` in `about:config`, or takes the file under **Settings → Privacy & Security → Certificates → View Certificates → Authorities → Import**. `git` and Python are §C's other two commands.

3. **Read the initial password** in the shell; the file self-deletes 24 hours after the boot:

   ```bash
   aws ssm start-session --profile awsds-infra-prod --region us-west-2 --target "$(AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/tooling output -raw instance_id)"
   ```

   ```bash
   sudo cat /etc/gitlab/initial_root_password
   ```

4. **The first sign-in**: `https://gitlab.awsds.internal`, user `root`, that password, with the tunnel up. Set a new password (**User settings → Password**) and keep the account local: it is GitLab's own break-glass when SAML breaks (Stage 7 step 1.8), and step 3 creates no other local account. The username may change (**User settings → Account**); it did on 2026-10-12.

5. **Bring the configuration current.** An apply that changed the S3 object after the boot (the first one did: `ci_catalog_bundles`) reaches the host only through the refresh, in the same shell; it ends in `gitlab Reconfigured!`, and anything else is read before going on:

   ```bash
   sudo awsds-gitlab-refresh
   ```

6. **The instance settings**, once. **Admin area → Settings → General → New user account restrictions → Allow new user accounts** off (the home page's *"allows anyone to register"* banner is this), since Identity Center is the only sign-in and the local administrator the one exception (Stage 7 step 3), kept on by the user through pass 1 (2026-10-12); **Visibility and access controls → Restricted visibility levels → Public** checked, since nothing here is reachable off the VPN and a public project would still be readable by anything on it; **Admin area → Settings → CI/CD → Auto DevOps → Default to Auto DevOps pipeline for all projects** off, or a project without a `.gitlab-ci.yml` runs a pipeline nobody wrote once a runner exists. The user list holds a `GitLab Duo` bot the instance created by itself (read 2026-10-12, v19.4.2); it holds nothing and stays.

7. **The namespace, the groups and the repositories** (Stage 7 steps 3.4-3.6): the group `awsds/`; inside it the four persona groups `data-scientists`, `deployment-managers`, `governance-managers` and `dev-env-stewards`, whose membership mirrors the Identity Center groups by hand and whose names are deliberately bare; the repositories `awsds/app-etl` and `awsds/dev-env`, created empty and private. On `dev-env`, **Manage → Members → Invite a group**: `awsds/data-scientists` as Developer and `awsds/dev-env-stewards` as Maintainer; **Settings → Repository → Protected tags → Add tag**: the wildcard `*-v*` (the image tag convention `<flavour>-v<semver>`; `v*` would match nothing this repository tags), allowed to create **Maintainers**, which in CE is the whole of the release gate. Done 2026-10-12.

8. **Then the runner** (§K), **SAML** (§A), and **Pages**, which the first pipeline proves (Stage 7 step 4.2).

## R. A configuration change

`gitlab.rb` is code (Stage 7 decision 8). A change is:

1. Edit `terraform-live/production/tooling/gitlab.rb.tftpl`, or a variable it reads.
2. Plan and apply `production/tooling/` by hand ([terraform-changes.md](terraform-changes.md) Recipe A). The plan shows the rendered file as the S3 object's diff and **no change to the instance**: `user_data` and `ami` are held, and a plan proposing a replacement is the signal to stop and read.
3. On the host, fetch and reconfigure:

   ```bash
   sudo awsds-gitlab-refresh
   ```

   The helper re-fetches `gitlab.rb`, the three certificates and the two keys, and runs `gitlab-ctl reconfigure`. Every reconfigure skips Let's Encrypt, since the template says `letsencrypt['enable'] = false`.

The host's state is not in the user data, so a stop/start changes nothing and a rebooted host serves its last configuration.

## C. The certificates

The leaves live 375 days and Terraform proposes their replacement inside the last 30 (`production/pki/`, `early_renewal_hours`). `./aws/supplychain.py` `SC-8` reads the runway from the published parameters and warns under 45 days. A re-issue is:

1. `terraform plan` on `production/pki/`: the two `tls_locally_signed_cert`, their parameters, objects and secret versions change; the root does not.
2. Apply, then §R step 3 on the host, which installs the new pair.
3. Record the date in the stage log.

**The root** lives ten years and its rotation is a rebuild of every client surface (D36 §6, rehearsed at Stage 12): the laptop, the `dev-env` image, the runner and GitLab itself. Its fingerprint is in the stage log; the one check that the root a client trusts is the one this slice generated is:

```bash
aws ssm get-parameter --profile awsds-infra-prod --region us-west-2 --name /datascience/prod/pki/ca-root-pem --query Parameter.Value --output text | openssl x509 -noout -fingerprint -sha256
```

**Trusting the root on a laptop** (step 2.5, INT-19's first surface; §I step 2 is the occasion). A browser's "Not secure" on `gitlab.awsds.internal`, `https` struck through, means the root is in no store the browser reads; the host's chain is not the suspect while step 4 passes with `--cacert`. Done on 2026-10-12 on the user's macOS laptop: Chrome stopped warning after steps 1-2.

1. Fetch the root from its one source (the same bytes are tracked as `images/base/ca-certificates/awsds-root.crt`; the fingerprint command above is the check that the two agree):

   ```bash
   aws ssm get-parameter --profile awsds-infra-prod --region us-west-2 --name /datascience/prod/pki/ca-root-pem --query Parameter.Value --output text > "$HOME/awsds-root.crt"
   ```

2. Put it in the store the browser reads, then quit and reopen the browser. macOS, the System keychain (Safari, Chrome, `curl`):

   ```bash
   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$HOME/awsds-root.crt"
   ```

   Firefox reads the keychain once `security.enterprise_roots.enabled` is `true` in `about:config`, or takes the file under **Settings → Privacy & Security → Certificates → View Certificates → Authorities → Import**. Windows, an administrator prompt (Edge and Chrome read the store): `certutil -addstore -f Root awsds-root.crt`. Debian and Ubuntu: the file copied to `/usr/local/share/ca-certificates/awsds-root.crt`, then `sudo update-ca-certificates`; Fedora and Amazon Linux: copied to `/etc/pki/ca-trust/source/anchors/`, then `sudo update-ca-trust`, which is what the runner's bootstrap does.

3. `git`, which reads its own bundle and not the keychain:

   ```bash
   git config --global http.https://gitlab.awsds.internal/.sslCAInfo "$HOME/awsds-root.crt"
   ```

4. Verify, with the tunnel up. The keychain holds one copy, and `curl` with the system store reads `200` and `ssl_verify=0` (before step 2 it reads `self signed certificate in certificate chain`):

   ```bash
   security find-certificate -c "awsds internal root CA" /Library/Keychains/System.keychain
   ```

   ```bash
   curl -sS -o /dev/null -w 'http=%{http_code} ssl_verify=%{ssl_verify_result}\n' https://gitlab.awsds.internal/users/sign_in
   ```

Python's `requests` and `botocore` read `certifi`, not the keychain; for a session that must reach GitLab from Python on the laptop, `REQUESTS_CA_BUNDLE` pointing at a bundle that holds the root plus `certifi`'s, or `verify=` in the call. The `dev-env` image takes the root at build time (step 2.6); the runner at boot (step 6.1); GitLab itself in `/etc/gitlab/trusted-certs/` (step 1.3).

## B. Backup and restore

A daily `gitlab-backup create` runs at 03:00 UTC while the host is up (`awsds-gitlab-backup.timer`) and uploads to `awsds-prod-gitlab-backup`, where every object expires after 30 days. The data volume is snapshotted daily by DLM besides. `gitlab-secrets.json` is **not** in the backup by GitLab's design: it is in `awsds-prod-gitlab-secrets`, pushed by the first boot, and a fresh boot restores it from there before the first reconfigure (step 1.5).

A backup by hand, in the shell:

```bash
sudo gitlab-backup create STRATEGY=copy
```

**The restore rehearsal** (step 8.2) is: a backup, `terraform destroy` of `production/tooling/` (the only slice a destroy may ever reach here; `pki/` refuses it), a re-apply, a wait for the first boot - which restores the secrets file from its container - then on the host:

```bash
sudo gitlab-ctl stop puma && sudo gitlab-ctl stop sidekiq
```

```bash
sudo gitlab-backup restore BACKUP=<timestamp_gitlab_backup>
```

```bash
sudo gitlab-ctl reconfigure && sudo gitlab-ctl restart && sudo gitlab-rake gitlab:check SANITIZE=true
```

The backup file is fetched first from the backup bucket into `/var/opt/gitlab/backups/`, as `git` (`aws s3 cp` as root, then `chown git:git`). A restore proves itself by a pre-backup repository cloning cleanly.

## K. The runner

The runner is a **protected project runner** of `awsds/app-etl`, never an instance runner (step 6.1). Any job on the host reads the instance role's credentials through the metadata service, and the role pushes to the three image repositories. An instance runner serves every project on the instance, including a self-registered account's while sign-up is open; a protected project runner serves only the protected branches and tags of the projects it is enabled in, so whoever can push an image is whoever can push a protected ref there.

1. **Create it in GitLab**, as the local administrator: `awsds/app-etl` → **Settings → CI/CD → Runners → Create project runner**: no tags, **Run untagged jobs** checked, description `awsds-prod-runner`, **Protected** checked. GitLab shows the authentication token (`glrt-…`) once.

2. **Put the token into its container**, once, by hand, as the infrastructure user; it never enters a file in this repository. The command waits for a paste and echoes nothing:

   ```bash
   aws secretsmanager put-secret-value --profile awsds-infra-prod --region us-west-2 --secret-id awsds-prod-runner-token --secret-string "$(read -rs T && printf '%s' "$T")"
   ```

3. **Enable it on `dev-env` when step 2.6 needs it**: `awsds/dev-env` → **Settings → CI/CD → Runners → Other available runners → Enable for this project**, then on the runner's edit page **Lock to current projects**, so no third project enables it.

Every `make gitlab-up` then boots a new instance that waits up to ten minutes for GitLab's sign-in page, reads the token and registers as a new runner manager under the same runner. `make gitlab-down` destroys it; GitLab removes a manager that stops contacting it. The runner's first-boot log is `/var/log/awsds-runner-boot.log`, readable through the serial console like GitLab's (§U); `gitlab-runner verify` and `/etc/gitlab-runner/config.toml` are on the host, reachable like §U's shell.

**What a job can rely on**:

- the proxy in both cases, `HTTP_PROXY`/`http_proxy`, `HTTPS_PROXY`/`https_proxy` and `NO_PROXY`/`no_proxy`; a build that pulls or installs anything passes them on as build arguments;
- the CA root at `/etc/gitlab-runner/certs/ca.crt` (the helper installs it for the clone; a script copies it into its own store);
- `ECR_REGISTRY`, this account's registry host;
- `/usr/local/bin/docker-credential-ecr-login`, mounted read-only from the host: Amazon's ECR credential helper, pinned by digest in `runners/variables.tf`. A job writes `{"credHelpers":{"<ECR_REGISTRY>":"ecr-login"}}` into `~/.docker/config.json`, and every pull and push on that registry signs in as the instance role, whose credentials the helper reads from the metadata service two hops away. The build image, `moby/buildkit:rootless`, runs as UID 1000 and cannot install a client of its own.

**The first pipeline** (step 6.4) is three files on `app-etl`'s `main`. It answers verification viii (registration, and BuildKit rootless building and pushing without privileged mode), verification vii (the cache's first pull with no route, on all three upstreams, which turns `SC-12` green), the pipeline deliverable (the push, then the immutable tag) and INT-21's proxy pair. Stage 8 owns the pipeline types; this is the shape that proves the runner.

`Dockerfile`, the image: its base comes through the cache, its `RUN` through the proxy:

```dockerfile
ARG REGISTRY
FROM ${REGISTRY}/ecr-public/docker/library/alpine:3.22
RUN apk add --no-cache ca-certificates
```

`ci/cache-probe.Dockerfile`, one image from each cache rule; it is built and discarded:

```dockerfile
ARG REGISTRY
FROM ${REGISTRY}/k8s/pause:3.10 AS k8s
FROM ${REGISTRY}/quay/prometheus/busybox:latest AS quay
FROM ${REGISTRY}/ecr-public/docker/library/busybox:1.37 AS ecr
FROM scratch
COPY --from=k8s /pause /probe/k8s-pause
COPY --from=quay /bin/busybox /probe/quay-busybox
COPY --from=ecr /bin/busybox /probe/ecr-busybox
```

`.gitlab-ci.yml`:

```yaml
stages: [build]

variables:
  IMAGE_REPO: awsds-prod-ecr-app-etl
  BUILDKITD_FLAGS: --oci-worker-no-process-sandbox

.buildkit:
  image:
    name: moby/buildkit:rootless
    entrypoint: [""]
  before_script:
    - mkdir -p ~/.docker
    - printf '{"credHelpers":{"%s":"ecr-login"}}' "$ECR_REGISTRY" > ~/.docker/config.json

build-image:
  extends: .buildkit
  stage: build
  script:
    - >
      buildctl-daemonless.sh build --frontend dockerfile.v0 --local context=. --local dockerfile=.
      --opt build-arg:REGISTRY="$ECR_REGISTRY"
      --opt build-arg:http_proxy="$http_proxy" --opt build-arg:https_proxy="$https_proxy" --opt build-arg:no_proxy="$no_proxy"
      --output type=image,name="$ECR_REGISTRY/$IMAGE_REPO:v0.1.0-$CI_COMMIT_SHORT_SHA",push=true
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

cache-probe:
  extends: .buildkit
  stage: build
  script:
    - >
      buildctl-daemonless.sh build --frontend dockerfile.v0 --local context=. --local dockerfile=ci
      --opt filename=cache-probe.Dockerfile --opt build-arg:REGISTRY="$ECR_REGISTRY"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      changes: [ci/cache-probe.Dockerfile]

proxy-pair:
  stage: build
  image: public.ecr.aws/amazonlinux/amazonlinux:2023
  script:
    - curl -sS -o /dev/null -w 'through the proxy -> %{http_code}\n' --max-time 20 https://pypi.org/
    - >
      if env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY curl -sS -o /dev/null --max-time 20 https://pypi.org/;
      then echo "FAIL: the internet answered with no proxy, so a route exists"; exit 1;
      else echo "no proxy, no answer: the proxy is the only way out"; fi
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
```

The readings, in order:

1. `build-image` and `cache-probe` run on the push; the protected runner takes the first push's pipeline, since `main` is protected before that pipeline exists. `moby/buildkit:rootless` and the job images come from Docker Hub and ECR Public through the proxy (the plane is `open`); every `FROM` is a pull through a cache rule, which ECR answers by creating `<prefix>/<upstream path>` from the rule's creation template and importing every platform of the upstream index; the push leaves by the `ecr.api`/`ecr.dkr` endpoints and the layers by the S3 gateway, since the job carries the host's `NO_PROXY`. A `FROM` that reads `not found` while the runner's `GetAuthorizationToken` succeeds is ECR failing to create the cache's repository: CloudTrail names the refusal under `AWSServiceRoleForECRTemplate`, and a creation template that carries tags or a KMS key needs a creation role (`registry/cache.tf`).
2. **Retry** `build-image`: the same commit builds the same tag, and ECR refuses the push: *"The image tag '…' already exists in the 'awsds-prod-ecr-app-etl' repository and cannot be overwritten because the tag is immutable."* That refusal is the deliverable's second half.
3. Run `proxy-pair` by hand: `through the proxy -> 200`, then `curl: (28) Connection timed out` and `no proxy, no answer`.

Measured 2026-10-12 (the stage log): `build-image` in about 8 s, the cache's first pull 1.3 s with the import, and all three readings as written here.

**Pages** (step 4.2): a job carrying `pages: true` publishes its `public/` directory; GitLab adds `pages:deploy`, and the site lives at `$CI_PAGES_URL`, a unique domain under the wildcard (`https://app-etl-ffa1fa.awsds-pages.internal` for `app-etl`, shown under **Deploy → Pages**). The jobs added to the first pipeline, with `stages: [build, verify]`:

```yaml
pages:
  stage: build
  image: public.ecr.aws/docker/library/alpine:3.22
  script:
    - mkdir -p public
    - >
      printf '<!doctype html><title>app-etl</title><h1>app-etl</h1><p>Published by job %s on %s from commit %s.</p>\n'
      "$CI_JOB_ID" "$CI_RUNNER_DESCRIPTION" "$CI_COMMIT_SHORT_SHA" > public/index.html
  pages: true
  artifacts:
    paths: [public]
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

pages-readback:
  stage: verify
  image: public.ecr.aws/amazonlinux/amazonlinux:2023
  needs: [pages]
  script:
    - echo "CI_PAGES_URL=$CI_PAGES_URL"
    - sleep 30
    - >
      curl -sS -o /dev/null --cacert /etc/gitlab-runner/certs/ca.crt --max-time 20
      -w 'pages: http=%{http_code} ssl_verify=%{ssl_verify_result} redirect=%{redirect_url}\n' "$CI_PAGES_URL/"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

Access control answers an unauthenticated read with `302` to `https://projects.awsds-pages.internal/auth`, so the read-back's proof is `ssl_verify=0`, not the status. A browser's first visit asks the user to authorize **GitLab Pages**, the OAuth application Omnibus registers at the first reconfigure (scope `api`; for an administrator GitLab warns that it can then act as one); each user authorizes it once.

If rootless BuildKit fails with `operation not permitted` under the runner's `seccomp=unconfined`, verification viii records it and the fallback is rootless Buildah.

## A. SAML

Stage 7 step 3 makes Identity Center the sign-in; the local administrator (§I) stays as the break-glass. The order:

1. **The application, in the Identity Center console** (step 3.1): the AWS access portal as the **infrastructure user**, account **Identity** (the delegated administrator of IAM Identity Center), permission set **InfrastructureAccess**, the console in `us-west-2`. **IAM Identity Center → Applications → Customer managed → Add application → I have an application I want to set up → Application type: SAML 2.0 → Next**, then every field named (Lesson 16):
   - Display name `GitLab`.
   - **IAM Identity Center metadata**: copy the **IAM Identity Center sign-in URL** (`https://portal.sso.us-west-2.amazonaws.com/saml/assertion/<application id>`) and **download the IAM Identity Center certificate** (PEM). These are the two values step 4 types.
   - **Application properties**: Application start URL `https://gitlab.awsds.internal` (the portal tile), relay state empty, session duration as it comes.
   - **Application metadata → Manually type your metadata values**: Application ACS URL `https://gitlab.awsds.internal/users/auth/saml/callback`; Application SAML audience `https://gitlab.awsds.internal`. Submit.

2. **Attribute mappings** (the application's **Actions → Edit attribute mappings**): `Subject` → `${user:email}`, format `emailAddress`; a second row `email` → `${user:email}`, format `basic`. Save. GitLab reads the first as the NameID and the second as the `email` attribute; without the second the sign-in fails with an empty e-mail.

3. **Assign users and groups**: the four persona groups among the five `sso-group-*` groups (`INV-04`), `sso-group-infrastructure` left out, since GitLab's administrator is the local account.

4. **The two values**, typed once into `terraform-live/production/tooling/saml.auto.tfvars`, which `.gitignore` refuses; the certificate is public, the file is the record. Both are in the application's metadata, the **IAM Identity Center metadata** URL on the application's page (public, no sign-in): the `SingleSignOnService` with the HTTP-POST binding is the sign-in URL and `X509Certificate` the certificate, which is how 2026-10-12's file was written (`curl`, then a parse). The file exists only in the checkout that wrote it (Lesson 61): a plan from another checkout proposes removing the `omniauth` block from the object, and that plan is the signal to copy the file, never a change to apply:

   ```hcl
   saml_idp_sso_target_url = "https://portal.sso.us-west-2.amazonaws.com/saml/assertion/<application id>"
   saml_idp_cert_pem       = <<-PEM
     -----BEGIN CERTIFICATE-----
     ...
     -----END CERTIFICATE-----
   PEM
   ```

5. **Apply and refresh** (§R): the plan on `production/tooling/` changes the S3 object alone, the rendered `gitlab.rb` gaining `omniauth_enabled`, `omniauth_allow_single_sign_on = ['saml']`, `omniauth_block_auto_created_users = false`, `omniauth_auto_link_saml_user = true` and the `saml` provider (label `AWS Identity Center`, the ACS URL, `idp_cert`, `idp_sso_target_url`, issuer `https://gitlab.awsds.internal`, NameID format `emailAddress`, `attribute_statements email`). Apply, then on the host `sudo awsds-gitlab-refresh`.

6. **Prove it** (step 3.2's user half, verification iii), in a browser profile that holds no other Identity Center session (a sign-in there ends a portal session held as another user), with the tunnel up and the root trusted (§C): `https://gitlab.awsds.internal/users/sign_in` shows the **AWS Identity Center** button; sign in as a data-scientist persona user. GitLab creates the account on the first sign-in and links it by e-mail. Try the portal tile too (the IdP-initiated path). Record which NameID and attribute shape worked, and what the browser did.

7. **After**: add the new users to the persona subgroups of `awsds/` by hand (§I step 7's membership mirroring); keep the local administrator.

A loop at sign-in has two suspects, an untrusted certificate and the browser's policy on a `POST` from Identity Center's public origin to a private host (Lesson 43); the fix for the first is §C, the reading for the second is the browser's own. A refused assertion with the clock named is time: SAML assertions carry a validity window and the host runs `chronyd`. The Identity Center certificate expires; its date is read from the file (`openssl x509 -noout -enddate`) and a rotation re-enters step 4.

## V. The instruments

| Instrument | Reads |
|---|---|
| `./aws/supplychain.py` | the host and its `[D]` state (`SC-1`), the groups (`SC-2`), the anchors (`SC-3`), the repositories (`SC-4`, `SC-5`), CodeArtifact (`SC-6`), the consumer reads (`SC-7`), the leaves' runway (`SC-8`), the root parameter (`SC-9`), the runner (`SC-10`), the proxy configuration (`SC-11`), the cache's first pull (`SC-12`) |
| `./aws/proxy.py` | the proxy and its planes, `PX-1`..`PX-4` |
| `./aws/egress.py` §6 | what is still up at the session's end — a forgotten runner is 0.2117 USD/h |

---

*Runbooks: [buildbox](buildbox.md) · [terraform-changes](terraform-changes.md) · [vpn](vpn.md) · Stage: [Stage 7](../stages/stage-07-gitlab-runners-ecr.md)*
