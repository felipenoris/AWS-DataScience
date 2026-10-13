# Log — Stage 8 — CI/CD pipelines

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-08-cicd-pipelines.md`](../plan/stages/stage-08-cicd-pipelines.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-10-12 — pass 0 and step 6.2, with the environment down

- **[Claude] The recorded answers, read from Stage 7.** The edition: CE v19.4.2 shows neither protected
  environments nor deployment approvals (Stage 7 3.3, its verification iv), so both gates take the
  protected-tag shape (verification i). The registration mechanism: `default-v0.6.0` became Sandbox's
  image version 6 at Stage 7 step 2.6, in `dev-env.md` §B's order. The mirror: none standing (Stage 7
  decision 4).
- **[Claude] The image scans, as the infrastructure user on Production** (`awsds-infra-prod`). Registry
  scanning is `BASIC` with no rules; scan on push is on for `awsds-prod-ecr-base`, `-dev-env` and
  `-app-etl` and off for the five cache repositories. `aws ecr describe-image-scan-findings`, every status
  `COMPLETE`, times in −03:00:

  | Repository | Tag | Pushed | Scan completed | CRITICAL | HIGH | MEDIUM | LOW | UNDEFINED |
  |---|---|---|---|---|---|---|---|---|
  | `base` | `default-v0.1.0` | 2026-08-22 02:21:51 | 02:23:55 | 30 | 430 | 514 | 3 | 7 |
  | `dev-env` | `default-v0.1.0` | 2026-08-22 02:30:34 | 02:34:30 | 30 | 430 | 514 | 3 | 7 |
  | `base` | `default-v0.5.0` | 2026-10-10 17:29:05 | 17:31:06 | 0 | 130 | 88 | 4 | 45 |
  | `dev-env` | `default-v0.5.0` | 2026-10-10 17:38:41 | 17:42:34 | 0 | 130 | 88 | 4 | 45 |
  | `base` | `default-v0.6.0` | 2026-10-12 16:29:13 | 16:30:56 | 0 | 130 | 88 | 4 | 45 |
  | `dev-env` | `default-v0.6.0` | 2026-10-12 16:40:24 | 16:47:47 | 0 | 130 | 88 | 4 | 45 |

  `aws ecr describe-images` returns neither `imageScanStatus` nor `imageScanFindingsSummary` for any of
  the 14 images in the two repositories; its keys are `artifactMediaType`, `imageDigest`,
  `imageManifestMediaType`, `imagePushedAt`, `imageSizeInBytes`, `imageStatus`, `imageTags`,
  `lastRecordedPullTime`, `registryId` and `repositoryName`. The call's own reference says so: AWS-native
  basic scanning does not use those two attributes, and `DescribeImageScanFindings` is the reader.
  `aws ecr wait image-scan-complete` polls every
  5 s and exits 255 after 60 checks (its help text), so the `dev-env` scan of `default-v0.6.0`, complete
  442 s after its push, outlasts it.
- **[Claude] `./aws/cicd.py awsds-infra-prod awsds-infra-sandbox-1 awsds-infra-staging`**, the stage's
  before. The first run read 1 FAILED: `CI-5` failed the refused Staging read of `awsds-prod-ecr-app-etl`
  while the repository carries no policy, which is the reading before step 3.0 (Lesson 50); it now notes
  the refusal until a policy exists or a deploy role is built. `CI-6` read `BaseImage` from
  `ListImageVersions`, which returns no image reference, so its column was always `-` and the check could
  neither pass nor fail (Lesson 13); it now reads `ContainerImage` from `DescribeImageVersion`, as
  `devenv.py` `DE-5` does. After both: **0 FAILED, 9 notes**, `CI-6` reading `N = 1, parity trivially
  true: awsds-prod-ecr-dev-env@sha256:43079013…5518`. Version 6's `BaseImage` is the tag
  (`:default-v0.6.0`) and its `ContainerImage` the digest.
- **[Claude] A CLI trap, read while writing that fix**: `aws sagemaker describe-image-version --version 6`
  prints the CLI's own version and exits 0 without calling SageMaker; the parameter is `--version-number`.
- **[Claude] Prices for decision 4**, the Price List Query API (`us-east-1` endpoint, Linux, shared
  tenancy, on demand; offer published 2026-10-12T19:39:25Z, effective 2026-10-01): `t3.small` 0.0208
  USD/h in `us-west-2` and 0.0336 in `sa-east-1`, `t3a.small` 0.0188 and 0.0302, `t4g.small` 0.0168 in
  `us-west-2`, the rate `docs/PRICING.md` already held.
- **[Claude] `pre-commit run --all-files` and `make check` on the laptop** (11 CPUs, 18 GB), before
  writing step 6.2. `make check`: OK in 1.5 s. `pre-commit`: 1 min 54 s, exit 1, every hook passing but
  `terraform_validate`, which failed five module folders: three with "the cached package for
  registry.terraform.io/hashicorp/aws 6.68.0 (in .terraform/providers) does not match any of the checksums
  recorded in the dependency lock file", two with "Failed to load plugin schemas". A second run failed five
  module folders again, all with the second message. `terraform-modules/iam-role` validated alone in
  1.4 s, and the hook passed in 27 s at three folders at a time, the limit `.pre-commit-config.yaml` now
  sets.
- **[Claude] Step 6.2 written**: `.github/workflows/offline-gates.yml`, on every pull request and by hand.
  Read before choosing the pins: the repository is public, Actions are enabled with every action allowed,
  the default token is read-only, and no workflow existed. Each action is pinned by commit, from a release
  at least two weeks old: `actions/checkout` v7.0.1, `actions/cache` v6.1.0, `astral-sh/setup-uv`
  v10.2.0, `hashicorp/setup-terraform` v4.0.1, `terraform-linters/setup-tflint` v6.3.1.
- **[Claude] `aws/egress.py`** no longer says Staging is unvended; its profile is `awsds-infra-staging`
  since 6b.
- **[Claude] The workflow's first complete run, on PR #123**: run `38314108044` (`pull_request`), job
  `pre-commit and make check`, **success in 7 min 50 s**. The run before it was cancelled by the
  workflow's concurrency group when the PR's second commit arrived. Step 6.3's first half: a pull request
  shows the gates.
- **[user] Decisions 1 to 9 taken as recommended, in chat**: the scanners block a CRITICAL or HIGH
  finding absent from a committed baseline (1); a dual push from the laptop mirrors this repository (2);
  the infrastructure pipeline holds no credential (3); the deploy runner is a `t3a.small` (4); one
  `awsds-<env>-alerts` topic per deployment-target account (5); the recipe moves to GitLab
  `awsds/dev-env` at pass 3 (6); the dev-env hand half stays (7); the image keeps passwordless `sudo` (8);
  the D28 lint is a command of `awsds-workflows` (9).
- **[Claude] Step 6.3 proven, with the user's go-ahead.** PR #123 went `CONFLICTING` when Stage 17's
  merge reached `main`, and a conflicting pull request runs no `pull_request` workflow: the violation
  commit got no run until the branch was synced (one conflict, `CLAUDE.md`'s Current position, both bullets
  kept). The merge commit carrying the violation failed run `38328376553` at the step "Every pre-commit
  hook over every file": `terraform_fmt`, "files were modified by this hook", `variables.tf`, with the diff
  printed. The violation was reverted in the next commit.
- **[Claude] Two readings that change pass 1 before it is written**, from AWS's documentation on
  2026-10-12. IAM stores a role named in a trust policy as its unique id, so a deleted and re-created role is
  not trusted again: the deploy runner's role is `[P]` while its host is `[E]`. EventBridge lists STS
  `AssumeRole` among the read-only management events, which a rule receives only in state
  `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`; `./aws/cicd.py` `CI-7` passed a plain `ENABLED`, the
  state that never fires, and now fails it.
- **[Claude] Pass 1's `[P]` half written, not applied.** The module `terraform-modules/deploy-role/`, tagged
  `deploy-role-v0.1.0` on its own commit and pushed before any caller named it (Recipe B), and three
  callers: `production/foundation/deploy-anchors.tf`, `staging/foundation/deploy-role.tf` and
  `sandbox/foundation/deploy-role.tf`. `DEPLOY_ROLES` and `DEPLOY_RUNNER_HOME` in `backend.py` generate
  `deploy_role_name`, `deploy_targets` and `deploy_runner` for the three. Offline: `terraform validate` and
  `tflint` clean on the module and the three slices; checkov failed `CKV_AWS_111` and `CKV_AWS_356` on the
  Staging egress grant until the Resolver statement was scoped to this account's ARNs, and the two writes
  that take no ARN of the account (`route53:AssociateVPCWithHostedZone`, the CloudWatch Logs delivery
  calls) carry a skip with the reason. A probe on the AWS provider 6.60.0 the three slices lock refused
  `state = "ENABLED_WITH_NONSENSE"` and listed `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS` as valid.
- **[Claude] The plans wait on a login.** The `awsds` SSO token expired mid-sitting: `aws sts
  get-caller-identity` still answered on `awsds-infra-prod` from the CLI's cached role credentials while
  Terraform's init failed with `refresh cached SSO token failed ... InvalidGrantException`, and every
  profile without cached credentials failed with `Token has expired and refresh failed`.
- **[user] The alerts address and the applies, in chat**: the user asked for `alert_email` to be written
  into the untracked `alerts.auto.tfvars` of `production/foundation/` and `staging/foundation/` (both
  matched by `*.tfvars` in `.gitignore`), and authorized the three applies.
- **[Claude] The three sessions on this machine were told before the first write**: Sonnet 4.5
  deprecation, Control Tower default VPC review, Redshift Serverless upgrade, all idle.
- **[Claude] Pass 1's `[P]` half applied, as the infrastructure user (`InfrastructureAccess`)**, from saved
  plans re-taken with the address set: `production/foundation/` **16 added** (the plan's 15 and the email
  subscription), then `staging/foundation/` **9 added**, then `sandbox/foundation/` **4 added**; nothing
  changed or destroyed. Staging's trust policy named the Production role created about a minute earlier
  and IAM accepted it. Each re-plan read `No changes` (`-detailed-exitcode` 0).
- **[Claude] `./aws/cicd.py awsds-infra-prod awsds-infra-sandbox-1 awsds-infra-staging`**: `CI-2` passes for
  the three roles (`awsds-staging-deploy-boundary`, `awsds-prod-deploy-boundary`,
  `awsds-sandbox-deploy-boundary`), `CI-3` (every principal names `awsds-prod-runner-deploy`,
  `sts:AssumeRole` only), `CI-4` (one inline statement, all `awsds-deploy-*`) and `CI-7` (both rules
  `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`); `CI-1` notes the absent runner. The first run read 2
  FAILED: `CI-5` turned red because the deploy roles now exist, the discriminator it had, while its grant
  is step 3.0's. It now reads whether an application slice holds state under `staging/app/` in
  `awsds-staging-tfstate`: **0 FAILED, 4 notes**. The app repository already holds `v0.1.0-b30af685` and
  `v0.1.0-0817e161`, Stage 7's first-pipeline images, so "a release image exists" would have been the
  wrong discriminator.
- **[Claude] `aws iam simulate-principal-policy` on the new roles.** Without context every action read
  `explicitDeny` with `AllowedByOrganizations: False`: the SCPs' Region and `aws:ResourceOrgID` conditions
  evaluate against keys the simulator does not invent. With `aws:RequestedRegion = us-west-2` and the
  organization id as context entries:

  | Role | Action and resource | Decision |
  |---|---|---|
  | `awsds-deploy-staging` | `s3:PutObject`, `s3:DeleteObject` on `staging/egress/terraform.tfstate` | allowed |
  | `awsds-deploy-staging` | `s3:PutObject` on `staging/foundation/terraform.tfstate` | implicitDeny |
  | `awsds-deploy-staging` | `s3:GetObject` on `staging/foundation/terraform.tfstate` | allowed |
  | `awsds-deploy-staging` | `ec2:CreateVpcEndpoint` on its VPC | allowed |
  | `awsds-deploy-staging` | `route53resolver:CreateResolverRule` | implicitDeny |
  | `awsds-deploy-staging` | `iam:CreateRole` | explicitDeny, by the ceiling |
  | `awsds-deploy-devenv-sandbox` | `sagemaker:CreateImageVersion` on `awsds-sandbox-dev-env` | allowed |
  | `awsds-deploy-devenv-sandbox` | `iam:PassRole` of the image role to SageMaker, `iam:PutRolePolicy` on it | allowed |
  | `awsds-deploy-devenv-sandbox` | `iam:PassRole` of any other role | explicitDeny, by the ceiling |
  | `awsds-deploy-devenv-sandbox` | `sagemaker:UpdateDomain` | explicitDeny, by the ceiling |
  | `awsds-deploy-devenv-sandbox` | `s3:PutObject` on `sandbox/dev-env/` state / `sandbox/foundation/` state | allowed / implicitDeny |
  | `awsds-deploy-prod` | `s3:PutObject` on `production/app/` state / `production/foundation/` state | allowed / implicitDeny |
  | `awsds-deploy-prod` | `iam:CreateRole` | explicitDeny |
  | `awsds-prod-runner-deploy` | `sts:AssumeRole` of `awsds-deploy-staging` / of a role outside the list | allowed / implicitDeny |

- **[Claude] Both alerts subscriptions read `PendingConfirmation`** (`aws sns list-subscriptions-by-topic`):
  each waits for the link AWS mailed.

## 2026-10-12 — the environment up, from a stale checkout

- **[user] `make hub-up`, then `make gitlab-up RUNNERS=0 AUTO=1`**, from the project folder, whose `main`
  stood at `52d526f` (#118), four merges behind `origin/main`.
- **[Claude] What that checkout did**, read afterwards: its Makefile predates `RUNNERS`, and make takes an
  unknown variable in silence, so `make -n` there expands to `--only tooling,egress,runners` where this
  branch expands to `--only tooling,egress`. GitLab, `[D]`, was only started; `production/egress/` was
  applied with #118's list, the SageMaker pair included; and the build runner `awsds-prod-runner`
  (`m8i.xlarge`) was created from #118's user data, without the ECR credential helper or `ECR_REGISTRY`.
  Planned from this branch's code: `egress/` `0 to add, 0 to change, 2 to destroy`
  (`sagemaker.api`, `sagemaker.runtime`); `runners/` `aws_instance.runner must be replaced`.

## 2026-10-13 — the deploy image and the deploy runner's anchors in GitLab

- **[Claude, through the user's Chrome, at the user's request] GitLab project `awsds/deploy-image`**:
  private, empty, one member (the local administrator, Owner, inherited from `awsds`); the build runner
  (#1) assigned to it in the admin area, staying Protected, locked and untagged; the minimum role to pass
  pipeline variables raised from Developer to Maintainer, read back after a reload.
- **[user] The deploy runner in GitLab**: a protected project runner of `awsds/app-etl`, tag
  `awsds-deploy`, no untagged jobs, locked, maximum job timeout 3600 s, assigned to `awsds/dev-env`.
  Two such runners exist, #2 (created about 02:42 UTC, no timeout) and #3 (about 03:20 UTC); the token
  container `awsds-prod-runner-deploy-token` holds two versions, `AWSPREVIOUS` put 02:44:11 UTC and
  `AWSCURRENT` 03:20:58 UTC, so #3 is the current token by the times. #2 is to be deleted once the
  instance registers.
- **[Claude] Applies, authorized by the user**: `production/registry/` 2 added (`awsds-prod-ecr-deploy`,
  `IMMUTABLE`, scan on push, KMS, and its lifecycle policy), `production/foundation/` outputs only
  (`deploy_role_arns`), `production/runners/` 0 added, 1 changed (the build runner's push statement gains
  the new repository; read before the build, since the role's list is fixed at that slice's apply). Each
  re-plan `No changes`.
- **[Claude] `.gitlab-ci.yml` committed to `awsds/deploy-image`** through the GitLab API in the browser
  session (status 201), read back and equal to `images/deploy/build.gitlab-ci.yml` by SHA-256; `main`
  protected for Maintainers; no pipeline started by the commit.
- **[Claude] Pipeline #5 run from the Run pipeline form** (`IMAGE_TAG=v0.1.0`,
  `RECIPE_SHA=de2dc08c9cade13a6279e7c70199b2ac31b38e76`, source `web`): job 14 on `awsds-prod-runner`,
  **success in 68 s**. The base `python:3.14-slim` came through the cache at index
  `sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170` (Debian 13);
  `terraform.zip: OK`, `Terraform v1.15.8`; `uv.tar.gz: OK`, `uv 0.12.13`; `gpg: Good signature from
  "AWS CLI Team <the team's address>"`, `aws-cli/2.37.12`. Pushed `awsds-prod-ecr-deploy:v0.1.0`,
  `sha256:1b1a583030cc7b963c2bd9ffdaf57af215aa6dd76e3599139bc8cf06dc38a53a`, 208,935,352 bytes.
- **[Claude] Its scan**, `COMPLETE`: CRITICAL 2, HIGH 8, MEDIUM 10, LOW 4, by source package `curl` (2
  CRITICAL, CVE-2026-8924 and CVE-2026-8927, 1 HIGH), `glibc` (2 HIGH), `expat` (2 HIGH), `gnupg2`,
  `cyrus-sasl2` and `zlib` (1 HIGH each). Debian's tracker reads trixie `8.14.1-2+deb13u5 vulnerable`,
  `<no-dsa> (Minor issue)`, fixed only in forky and sid: no fixed package exists for this base, and git,
  which the jobs need, links libcurl.
- **[user] Accepted `v0.1.0`** with its two CRITICALs named, CVE-2026-8924 and CVE-2026-8927, as the
  deploy image's baseline (decision 1); a rebuild is owed once Debian 13 ships a fixed curl. **Authorized
  the `production/runners` apply** that creates the deploy runner, as the infrastructure user, account
  Production, permission set `InfrastructureAccess`.
- **[Claude] `deploy_image_digest` pinned** to `sha256:1b1a5830…a53a` in `production/runners/variables.tf`.
  Planned before the apply: `Plan: 1 to add, 0 to change, 0 to destroy`, `aws_instance.deploy_runner[0]`
  (`t3a.small`, instance profile `awsds-prod-runner-deploy`), the rendered configuration holding the
  profiles `awsds-deploy-prod`, `awsds-deploy-devenv-sandbox` and `awsds-deploy-staging`.

## 2026-10-13 — the deploy runner, applied and registered

- **[Claude] `production/runners/` applied**: `Apply complete! Resources: 1 added, 0 changed, 0
  destroyed.`, `aws_instance.deploy_runner[0]` created in 16 s: `i-0836b280406db0cd3` on `10.30.27.146`,
  launched 03:59:28 UTC, `t3a.small`, instance profile `awsds-prod-runner-deploy`, hop limit 2. The re-plan
  `No changes`. `./aws/cicd.py`: `CI-1` passes on the instance, 0 FAILED.
- **[Claude] Its first boot, read through the serial console**: 03:59:46 to 04:03:17 UTC, 3 min 31 s.
  `docker-25.0.16`, `git-2.50.1`, the ECR credential helper `0.12.0` `OK` against its pinned sha256,
  `gitlab-runner-19.4.1`. Each profile assumed once with the instance's credentials:
  `assumed-role/awsds-deploy-prod/…`, `assumed-role/awsds-deploy-devenv-sandbox/…` and
  `assumed-role/awsds-deploy-staging/…`, the last two in Sandbox and Staging. GitLab's sign-in page `200`,
  `Verifying runner... is valid`, registered as `awsds-prod-runner-deploy-i-0836b280406db0cd3`; through
  the proxy `pypi.org` `200` and `10.31.0.1` `403`, GitLab direct `200`; the job image pulled through the
  helper as `awsds-prod-ecr-deploy@sha256:1b1a5830…a53a`.
- **[Claude] GitLab's API, read in the browser session**: runner #3 `online`, access level
  `ref_protected`, locked, `run_untagged` false, tag `awsds-deploy`, maximum timeout 3600, projects
  `awsds/app-etl` and `awsds/dev-env`, one manager (`19.4.1`) contacted 04:03:02 UTC. Runner #2
  `never_contacted`, with the same projects and tag: the orphan.
- **[Claude, through the user's Chrome, authorized by the user] Runner #2 deleted** through GitLab's API in
  the browser session, after reading it back as `never_contacted` with the description
  `awsds-prod-runner-deploy`. `/runners/2` then answers `404`; the instance's runners are #1
  `awsds-prod-runner` and #3 `awsds-prod-runner-deploy`, both `online`.
- **[Claude] The probe for verifications (ii) and (iii), prepared and not committed**: a job
  `deploy-runner-probe` for `awsds/app-etl`'s `.gitlab-ci.yml` (tag `awsds-deploy`, rule
  `$DEPLOY_RUNNER_PROBE`), and `- if: $DEPLOY_RUNNER_PROBE` / `when: never` ahead of each of the five
  existing jobs' rule, so a probe pipeline holds the probe alone. GitLab's CI lint (`dry_run` on `main`,
  `include_jobs`) reads it `valid`, and its simulated push pipeline on `main` holds the same five jobs as
  the current file's. Claude Code's permission classifier refused the commit through the browser ("Modify
  Shared Resources"), so the user commits it.

## 2026-10-13 — verifications (ii) and (iii), and the cross-account caller

- **[user] The probe committed and run**: the `.gitlab-ci.yml` Claude prepared, committed on `awsds/app-etl`'s
  `main` at 04:21:22 UTC with `[skip ci]` (push pipeline #6 `skipped`); pipeline #7 run on `main` from the
  Run pipeline form with `DEPLOY_RUNNER_PROBE=1`; the branch `deploy-runner-probe` created from `main`
  (push pipeline #8 `skipped`) and pipeline #9 run on it the same way.
- **[Claude] Verification (ii), read from job #15's log**: pipeline #7 held `deploy-runner-probe` alone,
  queued 0.3 s and `Job succeeded` in 14.3 s on `awsds-prod-runner-deploy-i-0836b280406db0cd3`, in
  `awsds-prod-ecr-deploy@sha256:1b1a5830…a53a`. The container printed `instance ->
  arn:aws:sts::<Production>:assumed-role/awsds-prod-runner-deploy/i-0836b280406db0cd3`, then
  `assumed-role/awsds-deploy-prod/…`, `assumed-role/awsds-deploy-staging/…` and
  `assumed-role/awsds-deploy-devenv-sandbox/…`.
- **[Claude] Verification (iii), read from job #16**: on the unprotected branch, `pending` with no runner,
  314 s queued at 04:28:13 UTC, under GitLab's notice "This job is stuck because of one of the following
  problems. There are no active runners online, no runners for the protected branch, or no runners that
  match all of the job's tags: awsds-deploy". Runner #3 was `online` throughout and listed job #15 alone.
- **[Claude] `./aws/cicd.py`: `CI-8` failed** on Staging's two records of the runner's assumptions, caller
  `(unknown)`. The raw records (`cloudtrail lookup-events` in Staging): `userIdentity.type` `AWSAccount`, no
  `arn`, `principalId` `<role unique id>:i-0836b280406db0cd3`, the caller's account as `accountId`, a
  `sharedEventID`. The instrument now reads the runner role's unique id (`iam get-role`) and attributes such
  a record by it: `CI-8` `8 event(s), every caller is the deploy runner`, 0 FAILED.
- **[Claude] The misuse rules' metrics**, 2026-10-12 20:00 to 2026-10-13 05:00 UTC: no datapoint for
  `MatchedEvents`, `TriggeredRules`, `Invocations` or `FailedInvocations` on `awsds-staging-deploy-misuse`
  and `awsds-prod-deploy-misuse`, and none for `NumberOfMessagesPublished` on either alerts topic. Staging's
  rule reads `userIdentity.arn`, which a cross-account record does not carry.

## 2026-10-13 — the misuse rule names the runner by its role id (`deploy-role-v0.2.0`)

- **[user] The fix authorized in chat**, after the cross-account finding: a new module version and the
  applies of `production/foundation/` and `staging/foundation/`.
- **[Claude] Both patterns tested with EventBridge's `TestEventPattern`** (`aws events
  test-event-pattern`), against the runner's real records and three variants with another caller. The
  deployed pattern, exempting the runner by `userIdentity.arn`: Staging's real record `False`, another
  account's role in it `False`, a Staging role `True`; Production's real record `False`, another
  Production role `True`. The proposed one, by `userIdentity.principalId` `anything-but` prefix
  `<runner role unique id>:`: the same, except another account's role in Staging `True`. An absent field
  does not match `anything-but`.
- **[Claude] `deploy-role-v0.2.0`**, tagged on `1acf7b0` and read back from origin: the rule matches
  `userIdentity.principalId`, and a new input `runner_role_id` is required when `misuse_alarm` is true.
  The callers read the id from IAM (`data "aws_iam_role"`, in Staging through the `deploy_runner` alias);
  all three pin `v0.2.0` (`29733fc`). Plans, against the local module and again against the tag: Production
  and Staging `0 to add, 1 to change, 0 to destroy`, the rule's `event_pattern` alone; Sandbox, which
  carries no rule, `No changes`.
- **[Claude] The four sessions on this machine told before the applies**, then both applied from saved
  plans: `module.deploy_role.aws_cloudwatch_event_rule.misuse[0]: Modifications complete after 1s` in
  each, `Apply complete! Resources: 0 added, 1 changed, 0 destroyed.`, each re-plan `No changes`.
  `TestEventPattern` on the deployed patterns now reads the proposed column above.
- **[Claude] `./aws/cicd.py` `CI-7`** now also reads each rule's pattern and fails one that exempts the
  runner by ARN, or by anything but the runner role's unique id: both rules `pass`, `CI-8` `8 event(s),
  every caller is the deploy runner`, 0 FAILED. Still unread: whether Staging's bus receives a
  cross-account record at all, which verification (xvi) answers.

## 2026-10-13 — verification (xvi): the misuse rules fire, from both sides of the account boundary

- **[user] The positive test authorized in chat** ("autorizo"), after Claude described it: each deploy
  role's trust opened for under a minute to the infrastructure user's Production `InfrastructureAccess`
  role, one assumption each, the saved trust restored. Claude Code's permission classifier had refused
  writing the test script ("Permission Grant") until then.
- **[Claude] The refused half first, nothing changed**: at 04:56:22Z the infrastructure user's Production
  session asked for `awsds-deploy-prod` and for `awsds-deploy-staging`, and both answered `AccessDenied`
  (`... is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::<Production>:role/awsds-deploy-prod`,
  and the same for `<Staging>`'s role). Production's CloudTrail recorded both (04:56:23Z, 04:56:24Z) with
  `errorCode` `AccessDenied` and `requestParameters` null, so no `roleArn` and no session name: the role
  refused is named in `errorMessage` alone. Staging recorded nothing of the refused cross-account attempt
  over the next 11 minutes.
- **[Claude] The four sessions on this machine told, then the positive half**:
  `awsds-deploy-prod`'s trust widened 05:08:18Z, assumed as `xvi-misuse-same-account` 05:08:32Z, restored
  05:08:33Z; `awsds-deploy-staging`'s widened 05:08:34Z, assumed from Production as
  `xvi-misuse-cross-account` 05:08:47Z, restored 05:08:49Z. Each restored trust read back equal to the
  saved one, and `production/foundation/` and `staging/foundation/` both plan `No changes`.
- **[Claude] Both rules fired at 05:08Z**: `MatchedEvents` 1, `TriggeredRules` 1, `Invocations` 1 and no
  `FailedInvocations` on `awsds-prod-deploy-misuse` and on `awsds-staging-deploy-misuse`, and
  `NumberOfMessagesPublished` 1 on each alerts topic. Staging's event bus receives the cross-account record,
  and `deploy-role-v0.2.0`'s pattern matches it, where `v0.1.0`'s would not have (`TestEventPattern`,
  above).
- **[Claude] The three test assumptions in CloudTrail**: Production recorded `xvi-misuse-same-account`
  (05:08:32Z) and its copy of `xvi-misuse-cross-account` (05:08:48Z, with a `sharedEventID`), each with the
  caller's `arn`; Staging recorded `xvi-misuse-cross-account` (05:08:48Z) as `userIdentity.type`
  `AssumedRole` with no `arn`, where the runner's own records there read `AWSAccount`. The caller's ARN is
  absent from the role's account either way, and the principal id is present.
- **[Claude] `./aws/cicd.py` `CI-8` read one page**: it looked up `EventName=AssumeRole` with
  `--max-results 50`, and Production's AssumeRole events of every kind had pushed the runner's 04:02:58Z
  assumption of `awsds-deploy-prod` off that page within an hour. It now looks each deploy role up by its
  ARN (`ResourceName`), every page, and excuses the two test sessions by name and minute (05:08Z): 11
  records, `CI-8` `8 event(s), every caller is the deploy runner` plus a note for the 3 test records, `CI-3`
  every trust naming the runner alone, 0 FAILED.
- **[user] Both alert emails received**, and Production's pasted in chat. Its body is the whole EventBridge
  event: `"detail-type":"AWS API Call via CloudTrail"`, `"source":"aws.sts"`, `"eventName":"AssumeRole"`,
  `"requestParameters":{"roleArn":"arn:aws:iam::<Production>:role/awsds-deploy-prod","roleSessionName":"xvi-misuse-same-account"}`,
  the caller `assumed-role/AWSReservedSSO_InfrastructureAccess_c2bcabf74c885115/<the infrastructure user>`,
  `"eventTime":"2026-10-13T05:08:32Z"`, `"readOnly":true`. Account ids, the address and the credentials
  are redacted here.
- **[Claude] What the email carries**: `responseElements.credentials`, the new session's `accessKeyId` and
  `sessionToken`, expiring 06:08:32Z. CloudTrail writes no secret access key, so the pair cannot sign a
  request; still, every alert puts a session token in a mailbox. An input transformer on the rule's
  target would send the caller, the role, the time and the source address alone. Not written.

## 2026-10-13 — the misuse alert without its credentials (`deploy-role-v0.3.0`)

- **[user] The input transformer authorized in chat**, after asking whether a token in the email is
  dangerous. Claude's answer: the record carries no secret access key, so the pair cannot sign a request,
  and that session had expired at 06:08:32Z; the email is a copy of account ids and identifiers in a
  mailbox, outside AWS.
- **[Claude] The transformer, from EventBridge's input transformation page**: a path missing from the
  event drops its variable rather than failing the target; an extracted value is not escaped, so no field
  the caller writes freely goes in (the `userAgent` stays out); a multi-line string is one quoted string
  per line. The message: the rule's name, the time, the role, the caller's `principalId`, type and
  account, the session name, the source address and the event id.
- **[Claude] `deploy-role-v0.3.0`**, tagged on `52b1c3b` and read back from origin; the three callers on it
  (`49c25a8`). Plans against the local module and against the tag: Production and Staging `0 to add, 1 to
  change, 0 to destroy`, the alert target alone; Sandbox `No changes`. The three sessions on this machine
  told (the fourth had ended), both applied from saved plans, `Modifications complete after 1s` and each
  re-plan `No changes`; `list-targets-by-rule` reads 8 input paths and the template on both rules. The
  message itself is unread until the rule fires.
