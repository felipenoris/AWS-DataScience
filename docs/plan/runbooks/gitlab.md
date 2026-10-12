# Runbook — GitLab

| | |
|---|---|
| **Scope** | The GitLab host (`production/tooling/`, `[D]`), its anchors (`production/foundation/`), the internal CA that certifies it (`production/pki/`), the build runner (`production/runners/`, `[E]`) and the acts a person performs on them. Built by [Stage 7](../stages/stage-07-gitlab-runners-ecr.md); the design is in the stage file and the slices' own comments, and this file repeats none of it |
| **Operator** | The **infrastructure user** through `awsds-infra-prod` (Production, `InfrastructureAccess`) for every AWS act; the GitLab `root` account or a SAML user for everything inside GitLab's UI |
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

## U. The session

The hub is somebody else's dependency, so a GitLab session leaves it alone (Stage 7 step 1.6):

```bash
make hub-up
```

```bash
make gitlab-up
```

`gitlab-up` starts the host, applies `production/egress/` (the SSM endpoints are the only door into both hosts) and applies `production/runners/`, which registers against GitLab at boot. The reverse order ends the session, destroying the runner and the endpoints and stopping GitLab:

```bash
make gitlab-down
```

`make up ENV=production` and `make down ENV=production` do the same for every Production `[E]` slice and never touch the hub pair (refusal 6). `make status` prices the host while it runs; stopped, it bills its two volumes and its snapshots.

**The first boot** of a fresh instance takes about ten minutes: the Omnibus package through the proxy, `gitlab-ctl reconfigure`, the readiness probe. Its log is `/var/log/awsds-gitlab-boot.log` on the host, readable with no SSM endpoint through the serial console:

```bash
aws ec2 get-console-output --profile awsds-infra-prod --region us-west-2 --instance-id "$(AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/tooling output -raw instance_id)" --latest --output text
```

**A shell** is Session Manager, from any network, as the infrastructure user; you land as `ssm-user` with passwordless `sudo`:

```bash
aws ssm start-session --profile awsds-infra-prod --region us-west-2 --target "$(AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/tooling output -raw instance_id)"
```

**The first sign-in** (step 1.8) is the local `root` account, whose initial password the host wrote to `/etc/gitlab/initial_root_password` and deletes after 24 hours. Read it in the shell above, sign in at `https://gitlab.awsds.internal` with the tunnel up, set a new password, and keep the account: it is GitLab's own break-glass when SAML breaks.

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

**Trusting the root on a laptop** (step 2.5, INT-19's first surface). Each client has its own store:

```bash
aws ssm get-parameter --profile awsds-infra-prod --region us-west-2 --name /datascience/prod/pki/ca-root-pem --query Parameter.Value --output text > "$HOME/awsds-root.crt"
```

macOS, the system keychain (Safari, Chrome, `curl` on macOS):

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$HOME/awsds-root.crt"
```

`git`, which reads its own bundle:

```bash
git config --global http.https://gitlab.awsds.internal/.sslCAInfo "$HOME/awsds-root.crt"
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

The runner is created in GitLab first (step 6.1): **Admin area → CI/CD → Runners → New instance runner**, no tags, run untagged jobs, description `awsds-prod-runner`. GitLab hands back an authentication token (`glrt-…`), which goes into its container once, by hand, as the infrastructure user; it never enters a file in this repository:

```bash
aws secretsmanager put-secret-value --profile awsds-infra-prod --region us-west-2 --secret-id awsds-prod-runner-token --secret-string "$(read -rs T && printf '%s' "$T")"
```

Every `make gitlab-up` then boots a new instance that reads the token, registers as a new runner manager under the same runner, and appears in the admin area within a minute. `make gitlab-down` destroys it; the stale manager row in GitLab clears itself. The runner's first-boot log is `/var/log/awsds-runner-boot.log`; `gitlab-runner verify` and `/etc/gitlab-runner/config.toml` are on the host, reachable like §U's shell.

**What a job can rely on**: the proxy in `HTTP_PROXY`/`http_proxy` and `NO_PROXY`/`no_proxy`, the CA root at `/etc/gitlab-runner/certs/ca.crt` inside the container (the helper installs it for the clone; a script copies it into its own store), and the instance role's credentials through the metadata service two hops away. A build that pulls or installs anything passes the proxy on as a build argument.

**The first pipeline** (step 6.4), a `.gitlab-ci.yml` on `app-etl` that builds and pushes an image with BuildKit rootless, no privileged mode, the registry login minted from the instance role. Stage 8 owns the three pipeline types; this is the shape that proves the runner:

```yaml
stages: [build]

variables:
  AWS_REGION: us-west-2
  IMAGE_REPO: awsds-prod-ecr-app-etl

build-image:
  stage: build
  image:
    name: moby/buildkit:rootless
    entrypoint: [""]
  variables:
    BUILDKITD_FLAGS: --oci-worker-no-process-sandbox
  before_script:
    - apk add --no-cache aws-cli
    - export ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
    - export REGISTRY="$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com"
    - mkdir -p ~/.docker
    - >
      printf '{"auths":{"%s":{"auth":"%s"}}}' "$REGISTRY"
      "$(printf 'AWS:%s' "$(aws ecr get-login-password --region "$AWS_REGION")" | base64 -w0)" > ~/.docker/config.json
  script:
    - >
      buildctl-daemonless.sh build --frontend dockerfile.v0 --local context=. --local dockerfile=.
      --opt build-arg:http_proxy="$http_proxy" --opt build-arg:https_proxy="$https_proxy" --opt build-arg:no_proxy="$no_proxy"
      --output type=image,name="$REGISTRY/$IMAGE_REPO:v0.1.0-$CI_COMMIT_SHORT_SHA",push=true
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

`aws-cli` and `moby/buildkit:rootless` arrive through the proxy (the plane is `open`); the push leaves by the `ecr.api`/`ecr.dkr` endpoints and the layers by the S3 gateway, since the job carries the host's `NO_PROXY`. The tag is immutable: a second push of the same tag is refused, which is the deliverable's second half. If rootless BuildKit fails with `operation not permitted` under the runner's `seccomp=unconfined`, verification viii records it and the fallback is rootless Buildah.

## A. SAML

Step 3.1 creates the custom SAML 2.0 application in the Identity Center console (Identity, as the delegated administrator) and downloads its metadata. The two values GitLab needs are typed once into `terraform-live/production/tooling/saml.auto.tfvars`, which `.gitignore` refuses:

```hcl
saml_idp_sso_target_url = "https://portal.sso.us-west-2.amazonaws.com/saml/assertion/<application id>"
saml_idp_cert_pem       = <<-PEM
  -----BEGIN CERTIFICATE-----
  ...
  -----END CERTIFICATE-----
PEM
```

Then §R: apply `tooling/` (the rendered `gitlab.rb` gains the `omniauth_providers` block) and refresh the host. A loop at sign-in has two suspects, an untrusted certificate and the browser's policy on a `POST` from Identity Center's public origin to a private host (Lesson 43); the fix for the first is §C, the reading for the second is the browser's own.

## V. The instruments

| Instrument | Reads |
|---|---|
| `./aws/supplychain.py` | the host and its `[D]` state (`SC-1`), the groups (`SC-2`), the anchors (`SC-3`), the repositories (`SC-4`, `SC-5`), CodeArtifact (`SC-6`), the consumer reads (`SC-7`), the leaves' runway (`SC-8`), the root parameter (`SC-9`), the runner (`SC-10`), the proxy configuration (`SC-11`), the cache's first pull (`SC-12`) |
| `./aws/proxy.py` | the proxy and its planes, `PX-1`..`PX-4` |
| `./aws/egress.py` §6 | what is still up at the session's end — a forgotten runner is 0.2117 USD/h |

---

*Runbooks: [buildbox](buildbox.md) · [terraform-changes](terraform-changes.md) · [vpn](vpn.md) · Stage: [Stage 7](../stages/stage-07-gitlab-runners-ecr.md)*
