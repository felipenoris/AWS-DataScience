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

## 2026-10-13 — pass 2, written with the environment down

- **[user] Four answers in chat, each the recommended option**: the shared gates live in a GitLab project
  of their own, included with `include:project` and pinned by commit (decision 10); a third runner,
  unprotected and holding no AWS credential, serves the unprotected branches (decision 11); the
  application's Terraform lives in `terraform-live/` (decision 12); and `alerts.auto.tfvars` and
  `saml.auto.tfvars` stay in the project folder's `secrets/`, where the user copied them, read by every
  plan of `production/foundation/`, `staging/foundation/` and `production/tooling/` through `-var-file`.
  No worktree receives a copy, since Claude copies nothing from `secrets/`.
- **[Claude] The refusals step 2.4 writes are 7 and 8, not 6 and 7.** Stage 7 step 1.6 gave number 6 to the
  hub pair `ENV=production` leaves alone (`scripts/slices.py`), after this stage's text was written, so
  "numbered after the existing five" names a number already taken. The stage file, the plan core and the
  stage index now say 7 (`make up` never applies an `app/` or `orchestration/` slice) and 8 (no pipeline
  profile applies a `sandbox/` slice but `sandbox/dev-env/`).
- **[Claude] Read before writing pass 2, with the environment down**: no runner serves an unprotected ref
  (both are protected, verification iii), which decision 11 answers; and step 5.6's sentence that class
  (2b) "joins D28's list in the same commit" went stale when PR #124 merged D28's classes (2b) and (2c).
- **[Claude] The scans the baselines are seeded from**, as the infrastructure user on Production
  (`awsds-infra-prod`), `aws ecr describe-image-scan-findings`, every status `COMPLETE`: `base` and
  `dev-env` at `default-v0.6.0` carry the same 130 HIGH keys, `<finding>|<package>`, 121 of them
  `linux-libc-dev`, the rest `expat`/`libexpat1` (6), `openssl`/`libssl3t64` (2) and `sudo`; the deploy
  image `v0.1.0` carries CVE-2026-8924 and CVE-2026-8927 (`curl`, CRITICAL) and 8 HIGH; Stage 7's
  `app-etl:v0.1.0-b30af685` (alpine) carries one HIGH, `CVE-2026-85091|zlib`.
- **[Claude] What the pins were read from, 2026-10-13**: the SageMaker Distribution 4.5.2's resolved
  environment pins `python-3.12.14`; its v4.5 template writes `ALL ALL=(ALL) NOPASSWD: ALL` into
  `/etc/sudoers`; GitLab v19.4.2's `Jobs/Secret-Detection.gitlab-ci.yml` sets `allow_failure: true` and runs
  on `CI_COMMIT_BRANCH`; the analyzer `secrets:7` and `7.40.0` are one image built 2026-10-10, `7.39.0`
  was built 2026-09-10; `pip-audit` 2.10.1 was published 2026-06-10; `moby/buildkit:rootless` and
  `v0.34.0-rootless` are one digest, published 2026-10-07; uv's images moved from bookworm to trixie, so
  the gates use `0.12.17-python3.12-trixie-slim`.
- **[Claude] The gates exercised offline.** The scan gate's script, run against the scans above with a
  stand-in `aws`: the two seeds pass, Stage 7's alpine image under the `app-etl` repository fails on its
  zlib HIGH, a deploy baseline missing CVE-2026-8927 fails, and a refused call, a `FAILED` scan and an
  unknown repository fail. The pip-audit script, on the laptop against OSV: `app-etl` passes (1 package,
  pyarrow), a project pinning `requests==2.19.0` fails (38 vulnerabilities with a fixed version), a project
  with no lock fails at the export (`uv` exit 2). pip-audit warns that `--require-hashes` with the OSV
  service checks the hashes' presence and not their validity; the image build's `uv sync --locked` is
  what verifies them.
- **[Claude] Plans, read-only, as the infrastructure user**: `production/foundation/` with
  `-var-file=<project folder>/secrets/alerts.auto.tfvars`, `2 to add, 0 to change, 0 to destroy` (the test
  runner's token container and its policy); `production/registry/`, `1 to add` (Sandbox's pull on
  `awsds-prod-ecr-app-etl`); `sandbox/data/`, `6 to add, 1 to change` (the outputs bucket, and the key's
  one new statement). `production/runners/` and `sandbox/app/app-etl/` plan only once `production/egress/`
  is up and `sandbox/data/` is applied, the outputs their remote states read.
- **[Claude] `./aws/cicd.py awsds-infra-prod awsds-infra-sandbox-1 awsds-infra-staging`**: 0 FAILED; `CI-5`
  notes the repository with no policy and both cross-account reads refused, `CI-9` the absent test
  runner.
- **[Claude] A commit hook found this worktree's `production/foundation/.terraform` older than pass 1**:
  `terraform_validate` failed with "Module not installed" on `deploy_runner_role` and `deploy_role` until
  the slice was initialised again (`init -backend-config=backend.hcl`, read-only).
- **[Claude] `git push` was refused by Claude Code's permission classifier** ("Out-of-Place
  Publication"), so the branch's commits wait for the user's push.

## 2026-10-13 — pass 2's `[P]` half, applied

- **[user] In chat**: signed in as the infrastructure user, pushed the branch, authorized the three applies
  of pass 2's `[P]` half (`production/foundation/`, `production/registry/`, `sandbox/data/`) and the
  removal of this worktree's copy of `saml.auto.tfvars`.
- **[Claude] The copy removed**: `terraform-live/production/tooling/saml.auto.tfvars`, matched by
  `.gitignore`'s `*.tfvars` and byte-identical (`cmp`) to the project folder's `secrets/saml.auto.tfvars`,
  which a `tooling/` plan reads through `-var-file`.
- **[Claude] PR #125 opened** against `main` from `claude/unruffled-taussig-429adc`.
- **[Claude] Before the applies**: the three peer sessions on this machine, all idle (the Sonnet 4.5
  deprecation migration, the Control Tower default VPC review, the Redshift Serverless Terraform upgrade),
  were told what the applies change. `aws sts get-caller-identity` on `awsds-infra-prod` and
  `awsds-infra-sandbox-1` read the infrastructure user through `InfrastructureAccess`, in Production and
  in Sandbox.
- **[Claude] The saved plans, read before applying** (Recipe A, each plan file outside the repository),
  with the read-only plans' counts:
  - `production/foundation/`, with `-var-file=<project folder>/secrets/alerts.auto.tfvars`:
    `awsds-prod-runner-test-token` and its policy `DenyValueReadExceptTestRunnerAndInfrastructure`, which
    denies `secretsmanager:GetSecretValue` to every principal but `awsds-prod-runner-test` and
    `InfrastructureAccess`;
  - `production/registry/`: `AllowConsumerAccountsToPull` on `awsds-prod-ecr-app-etl`, one principal, the
    Sandbox account's root, with `BatchCheckLayerAvailability`, `BatchGetImage`,
    `GetDownloadUrlForLayer` and `DescribeImages`;
  - `sandbox/data/`: the data key's policy keeps its statements and gains `AllowApplicationJobRolesViaS3`
    alone; `awsds-sandbox-outputs` is encrypted under the data key with a bucket key, its policy the
    module's `DenyInsecureTransport`, its lifecycle a 30-day expiry, noncurrent versions at 90 days and
    incomplete uploads at 7.
- **[Claude] The applies** (UTC), each from its saved plan:
  - `production/foundation/` 13:07:08Z-13:07:21Z, `2 added, 0 changed, 0 destroyed`;
  - `production/registry/` 13:07:34Z-13:07:43Z, `1 added`;
  - `sandbox/data/` 13:07:55Z-13:09:10Z, `6 added, 1 changed`, 58 s of it the bucket's lifecycle
    configuration.

  Each re-plan read `No changes` (`-detailed-exitcode` 0).
- **[Claude] The instruments, 0 FAILED each**:
  - `./aws/cicd.py`: `CI-5` passes the repository policy, which admits Sandbox, and Sandbox's read, and
    notes Staging's refused (step 3.0); `CI-9` notes the test runner absent;
  - `./aws/supplychain.py`: `SC-7`'s Sandbox reads answer;
  - `./aws/s3-persistence.py awsds-infra-sandbox-1`: 4 buckets, `awsds-sandbox-outputs` passing `SP-1` to
    `SP-6` and `SP-8`;
  - `./aws/datalake.py` and `./aws/dlp.py`: notes only.

  The multi-profile scripts exit 1 because seven profiles on other SSO sessions hold no token
  (`awsds-ctadmin`, `awsds-deploy`, `awsds-devenv`, `awsds-governance`, `awsds-scientist`), which each
  script's section 10 lists.
- **[Claude] `CI-5` and `SC-7` printed a capped count as a count.** "1 image(s) visible" came from
  `describe-images --max-results 1`, while Sandbox's `describe-images` on `awsds-prod-ecr-app-etl` lists
  two, Stage 7's `v0.1.0-0817e161` and `v0.1.0-b30af685`. Both checks now print `ok (asked for 1 image,
  1 returned)`; the verdict was right.
- **[Claude] A reading left as it is**: `awsds-sandbox-outputs` carries `CostCenter=stage-05`,
  `sandbox/data/`'s default tag, where the token container carries `stage-08` from its own `tags`.
  `s3-bucket-v0.3.0` takes no tags, so the bucket cannot carry its stage without a module input or a
  second provider.
- **Owed**: GitLab's half (`awsds/ci-gates`, its tag and commit; the test runner's registration and its
  token; `app-etl`'s roles, protected tag and push), then `production/runners/` and `sandbox/app/app-etl/`
  in a GitLab session, the first release and verification (xviii).

## 2026-10-14 — the GitLab session opens, and `s3-bucket-v0.4.0`

- **[user] In chat**: signed in as the infrastructure user, ran `make hub-up` and
  `make gitlab-up RUNNERS=0`, and approved `s3-bucket-v0.4.0` for `awsds-sandbox-outputs`'s `CostCenter`,
  its apply in the Sandbox sitting.
- **[Claude] What is up**: `make status ENV=production` read `vpn` and `proxy` `UP` (0.0052 and
  0.0104 USD/h), `tooling` `UP` (0.0672), `egress` `UP` with 12 resources (0.1200) and `runners` down,
  an estimated burn of 0.2028 USD/h. The one peer session on this machine, idle, was told.
- **[Claude] `s3-bucket-v0.4.0`, by Recipe B**: the module gains a `tags` input on its bucket, in commit
  `6b23d60` alone. `git ls-remote` read `v0.1.0` to `v0.3.0` on origin before the tag, and
  `s3-bucket-v0.4.0` at `6b23d601…` after the push. The caller commit `3a7e805` moves `sandbox/data/`'s
  `outputs_bucket` to it with `CostCenter = "stage-08"`; the hook refused its first attempt with
  `Module source has changed`, since the slice's `.terraform/` still recorded `v0.3.0`, and the slice's
  own init cleared it (`terraform-changes.md` §7).
- **[Claude] The plan of `sandbox/data/`**, read-only as `awsds-infra-sandbox-1`, against the local module
  and again against the pushed tag: `0 to add, 1 to change, 0 to destroy`, the bucket's `tags_all`
  `CostCenter` from `stage-05` to `stage-08`, the other four tags unchanged. The plan file is saved outside
  the repository.
- **[Claude] `gitlab.md` §K, "The application template"**: the push that replaces `awsds/app-etl`'s files
  with `examples/app-etl/`, written before it runs.
- **Owed**: the previous entry's list, and `sandbox/data/`'s tag apply.

## 2026-10-14 — `awsds/ci-gates` and the test runner in GitLab

- **[user] In GitLab, as `felipenoris`**: created `awsds/ci-gates` (`gitlab.md` §G steps 1-3) and the
  test runner in `awsds/app-etl` (§K), put its token into `awsds-prod-runner-test-token`, linked it to
  `awsds/dev-env` and `awsds/ci-gates` and locked it; gave `awsds/app-etl` its two persona groups and the
  protected tag `v*` (step 2.1); pushed `ci-gates/` and the tag `gates-v0.1.0`, whose commit is
  `9ae8f1b437a6fdbc2c7498e0c446d62d627abaad`. The clone of the empty project came on `main`, with git
  2.54 and `init.defaultBranch` unset.
- **[Claude] Read back** through GitLab's API in the user's browser session, GET only:
  - `awsds/ci-gates`: private, default branch `main`, the four persona groups at access level 20
    (Reporter), `main` pushed and merged by Maintainers with no force push, `gates-v*` created by
    Maintainers; the tag's four files carry the blob hashes `git hash-object` gives for `ci-gates/`;
  - `awsds/app-etl`: `awsds/data-scientists` at 30 (Developer), `awsds/deployment-managers` at 40
    (Maintainer), `v*` created by Maintainers;
  - runner #4, `awsds-prod-runner-test`: tag `awsds-test`, `run_untagged` false, `not_protected`, timeout
    3600, projects `app-etl`, `ci-gates` and `dev-env`. It read `locked` false, and true after the user
    locked it.

  `describe-secret` on the token container: one `AWSCURRENT` version, changed 16:06:49Z; the value was not
  read.
- **[Claude] The include `ref`** in `examples/app-etl/.gitlab-ci.yml` is that commit (`1e92dee`).
- **[user] `make gitlab-up`**, from this worktree, since the test runner is only on this branch.
- **[Claude] The readings**:
  - the three runner instances started 16:22:36Z-16:22:44Z, IMDSv2 required on each: the test runner a
    `t3a.small` with hop limit 1, the build runner an `m8i.xlarge` and the deploy runner a `t3a.small`, both
    with hop limit 2;
  - `make status ENV=production`: `runners` `UP` with 12 resources, an estimated burn of 0.4521 USD/h;
  - the test runner's first boot, 16:23:00Z-16:26:30Z on its serial console: `no token from a container:
    the jobs hold no AWS identity`, GitLab's sign-in page `200`, then `pypi.org` `200`, `10.31.0.1` `403`
    and GitLab direct `200`;
  - GitLab: runners #1, #3 and #4 online and locked, #4 contacted 16:27:02Z by a manager at `v19.4.1`;
  - `./aws/cicd.py`: 0 FAILED, `CI-9` passing on the instance (running, IMDSv2 required, hop limit 1) and
    on the role (its token, the CA root and Session Manager, nothing else); the exit is 1 from the
    untokened profiles of section 10;
  - `awsds/ci-gates`' pipelines, both `success` on `awsds-prod-runner-test`: #10 on `main`
    (`baselines-shape` 20 s, `secret_detection` 22 s, `secret-detection-gate` 7 s) and #11 on
    `gates-v0.1.0` (`baselines-shape` 6 s).
- **Owed**: the application template's push (`gitlab.md` §K) with verifications (iv), (x) and (xiii), then
  the Sandbox sitting: `release.tf`, `sandbox/app/app-etl/`, `sandbox/data/`'s tag and verification (xviii).

## 2026-10-14 — the application template on a branch, and verification (xiii)

- **[user] The template pushed** to `awsds/app-etl` on the branch `application-template` (`gitlab.md` §K,
  "The application template", steps 1-3), commit `e976b204`.
- **[Claude] Pipeline #12 refused at creation**, read on its page: `yaml invalid`, 0 jobs, "Unable to run
  pipeline", "image name should be a string". The template named a job `image`, which at the top level of a
  `.gitlab-ci.yml` is the global keyword, and the offline gates parse no GitLab CI. The job is `build-image`
  since `bf6d69e`, with `scan-gate`'s `needs`, the template's README and the runbook. GitLab's CI Lint,
  called in the user's browser session (`POST /projects/:id/ci/lint`, which creates nothing), read the
  renamed file valid with no error or warning, statically and as dry runs: 5 jobs on `application-template`,
  6 on `main` with `pages`.
- **[user] The fix pushed** as a second commit, `4e751eda`; `gate-without-proxy` run by hand.
- **[Claude] Pipeline #13**, every job on `awsds-prod-runner-test`, read through GitLab's API:
  - `secret_detection` 10 s and `secret-detection-gate` 8 s: 0 secrets in the scanned commits;
  - `pip-audit` 15 s: 1 pinned package (the runtime set is pyarrow), 1 audited, 0 vulnerabilities with a
    fixed version;
  - `test` 12 s: ruff `All checks passed!`, 5 files already formatted, 7 tests passed in 0.45 s;
  - `gate-without-proxy` 51 s, `success`: with the proxy variables removed, `uvx` failed with
    `Request failed after 3 retries in 44.5s`, `client error (Connect)`, `operation timed out`, exit 2 after
    45 s, under the job's 300 s bound.

  Verification (xiii) is answered yes on both halves.
- **Owed**: the merge into `main` (Pages) and the tag `v0.1.0` (`build-image`, `scan-gate`, verification
  (iv)), then the Sandbox sitting.

## 2026-10-14 — the first release `v0.1.0`, blocked by the scan gate

- **[user]** Merged `application-template` into `main` (pipeline #14) and tagged `v0.1.0` on `d7e093a9`
  (pipeline #15).
- **[Claude] Pipeline #14**, on `main`, every job `success` on the test runner: `secret_detection` 9 s,
  `secret-detection-gate` 8 s, `pip-audit` 17 s, `test` 12 s, `pages` 13 s, with `gate-without-proxy` left
  manual. The Pages deployment of 16:45:06Z is at `https://app-etl-ffa1fa.awsds-pages.internal`, which
  served pdoc's `app_etl` page in the user's browser.
- **[Claude] Pipeline #15**, on `v0.1.0`: `test` 12 s and `pip-audit` 16 s on the test runner, then
  `build-image` 217 s on `awsds-prod-runner`, its BuildKit pulling base from ECR in about 45 s. The push,
  `v0.1.0-d7e093a9` at 16:49:28Z: `sha256:33f76dec8bf7b7be760db1daf575c388172e49862381f66f8032b534bce5280d`,
  3,796,518,899 bytes.
- **[Claude] The push's basic scan** completed at 16:55:12Z, 5 min 44 s after the push, its vulnerability
  source dated the same instant: CRITICAL 113, HIGH 610, MEDIUM 154, LOW 4, UNDEFINED 436, in 1,317 findings.
  Every CRITICAL and 601 of the HIGH are `linux-libc-dev` 6.8.0-142.142. The image's package and version set
  equals `base` `default-v0.6.0`'s scan of 2026-10-12 (CRITICAL 0, HIGH 130), so the difference is two days
  of the vulnerability source, not the build.
- **[Claude] `scan-gate` failed after 368 s**, as decision 1 writes it: "CRITICAL and HIGH: 723 found, 130 in
  the baseline" and "FAIL: 593 CRITICAL or HIGH finding(s) absent from the baseline", 113 CRITICAL and 480
  HIGH, every one `linux-libc-dev`. The 130 baseline entries were all found again. Verification (iv)'s first
  half is answered; its re-scan half is not exercised.
- **[Claude] A wait loop of my own never exited**: `describe-image-scan-findings --query
  imageScanStatus.status --output text` on 1,317 findings paginates, and the CLI prints the field once per
  page, `COMPLETE` and then `None` for every later page, so the output never equalled `COMPLETE`. The gate
  reads the merged JSON with `jq` and is not affected.
- **Owed**: the user's decision on the `linux-libc-dev` findings (decision 1), a release whose gate passes,
  then the Sandbox sitting.

## 2026-10-14 — the ECR scan made informative, and the first Sandbox run of `app-etl`

- **[user] In chat**: amended decision 1, so that the scan findings inform the operator in the CI/CD log
  and block no deployment; pushed `gates-v0.2.0`; authorized the Sandbox sitting, running `make up` and
  `make down` themselves and leaving the rest to Claude; ran `make up ENV=sandbox ONLY=egress` from this
  worktree; moved `awsds/app-etl`'s `main` to `gates-v0.2.0`; left the environment up.
- **[Claude] The informative gate**: `.gates-ecr-scan` carries `allow_failure: true` and prints `WARN` over
  the findings absent from the baseline. The script, run offline against `v0.1.0`'s real scan, listed the
  593 findings and exited 1; GitLab's CI Lint read the template valid, a job extending it
  `allow_failure=true`. `pip-audit`, Secret Detection and `checkov` still block.
- **[Claude] Read back in GitLab**: `gates-v0.2.0` at `a335f37f2e8c85bcde31d378fac478899c355515`, protected,
  its four files with `ci-gates/`'s blob hashes, pipelines #16 (`main`) and #17 (the tag) green on the test
  runner; `awsds/app-etl`'s `main` at `62189229`, the `ref` line and one README line changed, pipeline #18
  green (`secret_detection` 10 s, `secret-detection-gate` 8 s, `pip-audit` 17 s, `test` 12 s, `pages` 14 s).
- **[Claude] Before the writes**: the two peer sessions on this machine, both idle, were told;
  `get-caller-identity` read the infrastructure user through `InfrastructureAccess` in Sandbox and in
  Production.
- **[Claude] `sandbox/data/`** from its saved plan, 17:43:59Z-17:44:15Z: `0 added, 1 changed, 0
  destroyed`; the re-plan read `No changes`, and `awsds-sandbox-outputs` reads `CostCenter=stage-08`.
- **[Claude] `sandbox/app/app-etl/`**, with `release.tf` naming `v0.1.0` and
  `sha256:33f76dec8bf7b7be760db1daf575c388172e49862381f66f8032b534bce5280d`. The first apply,
  17:44:50Z-17:45:01Z, created `awsds-sandbox-app-etl-job` and stopped: EC2 refused `CreateSecurityGroup`
  with `InvalidParameterValue`, a description taking `a-zA-Z0-9. _-:/()#,@[]+=&;{}!$*` alone, and the
  group's and both rules' descriptions carried an apostrophe the plan had not checked. Reworded in
  `65b06c4`, re-planned `4 to add`, applied 17:46:20Z-17:46:34Z; the re-plan read `No changes`.
- **[Claude] The endpoints**, after the user's `make up`: the 18 interface and 2 gateway endpoints of
  Sandbox read `available`.
- **[Claude] The job `app-etl-20261014T175359`**, created with `create-processing-job` from the slice's
  `processing_job_request` (`ml.t3.medium`, network isolation, inter-container encryption, the data key on
  the volume and the output, 900 s): created 17:54:01Z, processing 17:54:53Z-17:59:32Z, `Completed`
  18:01:33Z. Its interface sat in `awsds-sandbox-private-usw2-az1` (`us-west-2b`) under the job's security
  group. Its log, at 17:59:13Z:

  ```
  app-etl 0.1.0, python 3.12.14 at /opt/app-etl/venv/bin/python
  pyarrow 25.0.1 from /opt/app-etl/venv/lib/python3.12/site-packages/pyarrow
  trades.csv: 10 rows -> trades.parquet
  1 file(s) processed
  ```

  The keys, at 17:59:27Z: `app-etl/v0.1.0/trades.parquet` 1,780 bytes and `trades.summary.json` 407 bytes,
  SSE-KMS under `alias/awsds-sandbox-data` with a bucket key, expiring 2026-11-14. Listed and headed, never
  read.
- **[Claude] Verification (xviii)**: yes. Pipeline #15's smoke stage, networking off, printed `uid 1000,
  output owned 0:0 755` and wrote the Parquet after `sudo -n chown`; the job ran the same command on the
  same image under network isolation, and its two outputs arrived.
- **[user] The environment left up**: Production's hub, GitLab and runners (`make status`: 0.4521 USD/h)
  and Sandbox's `egress` (0.18 USD/h) and `app/app-etl`.
- **Owed**: `make down ENV=sandbox` from a checkout carrying `app/app-etl` (until this branch merges, this
  worktree), then `make gitlab-down` and `make hub-down`; verification (iv)'s re-scan half; (x) with a pinned
  vulnerability in GitLab.

## 2026-10-14 — the environment down

- **[user]** Ran `make down ENV=sandbox` from this worktree, then `make gitlab-down` and `make hub-down`.
- **[Claude] Read back**: `make status` reads 0.0000 USD/h in Sandbox (`egress`, `warehouse-compute`,
  `app/app-etl` and `probes` with no resource) and in Production (`vpn`, `proxy` and `tooling` stopped,
  `egress` and `runners` with no resource). `get-role` on `awsds-sandbox-app-etl-job` answers
  `NoSuchEntity`; no security group of that name, no `awsds-prod-runner*` instance and no Sandbox interface
  endpoint remain. The two outputs under `app-etl/v0.1.0/` stay in the `[P]` bucket until their 30-day
  expiry.

## 2026-10-14 — pass 3 read, and the house environment on Python 3.12

- **[Claude] Before the pass**: the Stage 8 pass 2 session on this machine was asked whether it still held a
  Stage 8 edit, slice, log entry or state lock, and answered that it held none, its worktree removed and the
  estate down.
- **[Claude] Read in Sandbox** as the infrastructure user (`InfrastructureAccess`), read-only:
  `awsds-sandbox-dev-env` version 6 `CREATED`, `BaseImage` `awsds-prod-ecr-dev-env:default-v0.6.0`,
  `ContainerImage` `…@sha256:43079013d424374161bc4025444623bfe31cc933bbde3637a51a05cb28bc5518`; the one
  project domain attaches version 6 to both app types; no app is running; its one space names no image
  version, so a bump strands nothing.
- **[Claude] pip-audit 2.10.1 on the house environment's lock**, offline on the laptop, run as the gate runs
  it: 452 pins exported, **0 audited**, "No known vulnerabilities found", exit 0. Every line of the export
  carries `platform_machine == 'x86_64' and sys_platform == 'linux'`, which pip-audit evaluates against the
  interpreter running it and skips. With the markers removed: 452 audited, **73 vulnerabilities with a
  fixed version in 14 packages**: fsspec, jupyterlab, mako, multidict, notebook, oauthlib, pyjwt,
  setuptools, sqlparse, torch, tornado, urllib3, virtualenv, werkzeug.
- **[Claude] A targeted re-lock, in a scratch copy and not committed**: `uv lock --upgrade-package` for the
  14 and torchvision resolved and moved 13 (jupyterlab 4.6.4, mako 1.4.3, multidict 6.9.1, notebook 7.6.3,
  oauthlib 4.0.0, pyjwt 2.15.1, python-discovery 1.6.2, torch 2.13.0+cpu, torchvision 0.28.0+cpu, tornado
  6.5.10, urllib3 2.8.0, virtualenv 21.14.7, werkzeug 3.1.9). Three stayed, carrying 8 of the findings:
  fsspec 2025.3.0 (required by autogluon-multimodal, datasets, evaluate, huggingface-hub, lightning, ray
  and others), setuptools 81.0.0 (autogluon-core, tensorflow, tensorboard, torch, spacy and others) and
  sqlparse 0.5.0 (amazon-sagemaker-sql-magic 0.1.3, mlflow-skinny 3.16.0,
  sagemaker-studio-dataengineering-sessions 1.3.25).
- **[Claude] The gate's export of that lock**: the gate's image is CPython 3.12 with
  `UV_PYTHON_DOWNLOADS=never`, and the project asked `>=3.13`. With no compatible interpreter visible and
  downloads off, `uv export --locked` exits 2: "No interpreter found for Python >=3.13 in managed
  installations or search path"; with `--python 3.12` it refuses the interpreter against
  `requires-python`. `--frozen`, which the runbook's §J1 export uses, needs no interpreter (2026-10-12).
- **[user] In chat**: downgrade, every Python environment on 3.12 (decision 13).
- **[Claude] The change**, in `images/dev-env/`: `requires-python = ">=3.12,<3.13"` and
  `PYTHON_VERSION=3.12`. `uv lock` resolved 453 packages, **every one at the version it had**; the lock's
  `requires-python` reads `==3.12.*` and its resolution markers collapse to the platform alone. Read from
  the lock's wheel names: 444 packages publish a `cp312` Linux x86_64 wheel and 8 are built from source in
  the image (amazon-sagemaker-sql-magic, antlr4-python3-runtime, gssapi, krb5, nvidia-ml-py3, pyhive,
  sagemaker-kernel-wrapper, seqeval), against 9 under `cp313`, where statsforecast 2.0.1 publishes no
  wheel. Under the gate's conditions, only CPython 3.12 visible and downloads off, the export exits 0 with
  452 pins; pip-audit on it, markers removed, reads the same 73 findings in the same 14 packages.
- **[Claude] 6i's `awsds-demo-deps`** on 3.12: `.python-version` 3.12, `requires-python = ">=3.12,<3.13"`,
  re-locked at msgspec 0.22.0, petl 1.7.29 and pyarrow 24.0.0, each with a `cp312` manylinux x86_64 wheel;
  its 8 tests pass on CPython 3.12.13, and `awsds-demo-job`'s 6 on the repository's Python. The folder 6i
  copied to `shared/jobs/` stays `cp313`, matching the `default-v0.5.0` its workflows run, so `SO-7`'s
  suffix is unchanged.
- **Not built**: no image carries 3.12 until `default-v0.7.0`. **Owed**: the user's answer on decisions 14
  to 17 (the registry state read, the accepted findings, the recipe's checkout, the register job's guards)
  and the mirror's mechanics, then the rest of pass 3.

## 2026-10-14 — decisions 14 to 17, and the image recipes move to GitLab

- **[user] In chat**: decisions 14 and 15 as recommended. Decision 16 wider than recommended: everything
  under `images/` is controlled in the private GitLab, its source of truth, with a copy of each project's
  last commit kept here under `gitlab/` by a script, a second script checking the copy's `NO_PROXY` and
  Bedrock parameters, and any change pushed to GitLab by the user. Decision 17: no guard, the steward's
  discipline, with the guards in a GitHub issue.
- **[Claude] Issue [#129](https://github.com/felipenoris/AWS-DataScience/issues/129)** opened: the four
  guards, the four read actions they cost, and when to revisit.
- **[Claude] The seed**: `images/` moved by `git mv` into `gitlab/awsds/dev-env/` (`base/`, `dev-env/`,
  `smoke/`, the pipeline as `.gitlab-ci.yml`, `README.md`) and `gitlab/awsds/deploy-image/` (`Dockerfile`,
  `aws-cli-team.asc`, the pipeline, a new `README.md` and a `.dockerignore`). Both pipelines build their own
  project's commit, BuildKit `v0.34.0-rootless` by digest; the recipe's comments and OCI `source` labels name
  the GitLab projects, and its links to this repository are absolute. GitLab holds none of it yet.
- **[Claude] `scripts/gitlab-mirror.py`**, against a GitLab of `file://` repositories: a first copy (3 files
  each, an executable bit kept); a second run reporting the copy unchanged; a commit that edited, added,
  deleted and dropped an executable bit, reported 1 added, 1 removed, 2 changed; an uncommitted edit under
  the copy refused with exit 2 and listed by `--dry-run`; a committed edit replaced by GitLab's content; an
  unknown project exit 2; a bad URL exit 1.
- **[Claude] `scripts/check-gitlab-mirror.py`** on the seed, as the infrastructure user in Sandbox. From the
  state, `GM-3` fails: `sandbox/egress` is down and its state holds no outputs. With `--plan`, in 43 s, every
  check passes and `GM-1` notes the copy was never copied from GitLab: 70 names, sha256
  `aafa08da98a61f5c` on both sides, the proxy URL, the settings parsing, Bedrock in `us-west-2`, 3 pins each
  in the SCP and the grant. With the copy broken on purpose (one Bedrock name removed and an unknown one
  added, the Haiku pin moved to an unscoped profile, `AWS_REGION` set to `us-east-1`), `GM-4`, `GM-7` and
  `GM-8` fail, the repairs name the two GitLab files, and `aws/output/gitlab-mirror-no-proxy.txt` carries the
  line; the copy was restored.
- **[Claude] The instruments read the copy**, through `aws/awslib/devenvrecipe.py` and
  `awslib.bedrockscope`: `./aws/devenv.py` `DE-1` 70 entries, sha256 `aafa08da98a61f5c`, `DE-5` version 6
  baking the same list, `DE-2` failing on the slice being down; `./aws/bedrock-scope.py` 7 pass.
- **[Claude] The repository around the copy**: pre-commit's fixers and ruff skip `gitlab/<group>/<project>/`
  while `check-json` and the key and identifier checks read it; the link checker skips the copies' markdown;
  the references to `images/` point at the copy, records of a date kept as written; `make check` OK.
- **Owed**: a GitLab session in which the user pushes each folder's content to its project and the copy is
  refreshed from GitLab; then pass 3's chain (decisions 14 and 15 in code, the release pipeline, the
  registration job).

## 2026-10-14 — pass 3's chain, written with the environment down

- **[user] In chat**: the rest of pass 3 before the GitLab session.
- **[Claude] Decision 14 in code**: the runner role's inline policy `registry-state` in `production/foundation/`
  (`s3:ListBucket` on the key's prefix, `s3:GetObject` on `production/registry/terraform.tfstate`,
  `kms:Decrypt` on the account's state key); the runner's own profile in `production/runners/`' AWS
  configuration; `./scripts/gen-tfvars.py --pipeline` writes `awsds-prod-runner-deploy` for the registry
  read, where the laptop's file names `awsds-infra-prod`. Read-only plans as the infrastructure user:
  `production/foundation/` `1 to add, 1 to change` (the inline policy, the role's description), planned with
  the alerts tfvars; `sandbox/dev-env/` `0 to add, 1 to change` (the image's description), the default tag
  passing the new validation.
- **[Claude] `scripts/devenv-register.py`**: dry runs in both modes print the generators, `init` with
  `-lockfile=readonly`, a plan with `-var=image_tag=`, the apply of the saved plan and the version read
  back; a tag without the rule's shape exits 2.
- **[Claude] The targeted upgrade on the 3.12 lock**, in a scratch copy: 453 packages resolved, the same 13
  moved as on the 3.13 lock, and the same 8 findings left. Their holders, read from PyPI's metadata:
  `amazon-sagemaker-sql-magic` 0.1.3 requires `sqlparse==0.5.0`, `autogluon-multimodal` 1.6.1
  `fsspec[http]<=2025.3`, `autogluon-core` 1.6.1 `setuptools<82`.
- **[Claude] `gates-v0.3.0`**, in `ci-gates/`: the pip-audit job with the accepted list chosen by
  `CI_PROJECT_PATH` and the audit-count guard, and `GATES_PIP_AUDIT_ACCEPTED_DEV_ENV` with the 8, proposed for
  the steward. Exercised offline: the whole job on the laptop read 0 of 452 audited and failed, exit 1; its
  summary on the 3.12 lock read 59 blocking lines and 14 accepted, exit 1; on the upgraded lock 0 blocking,
  exit 0; with 460 pins against 452 audited it failed.
- **[Claude] The release chain**, in the copy's `.gitlab-ci.yml`: `recipe-checks`, `build-images` (with the
  smoke build), `scan-base`, `scan-dev-env`, `release-gate`, `register`; the smoke Dockerfile's `check` and
  `manifests` stages; `dev-env/Dockerfile`'s `ARG BASE_REF`. Every pipeline file parses; `recipe-checks`
  passes on the copy and fails a trailing comma in the managed settings.
- **Owed**: the steward's acceptance of the 8 findings; the applies of `production/foundation/` and
  `sandbox/dev-env/`; the GitLab session of runbook `gitlab.md` §M, with the pipeline linted in GitLab first.

## 2026-10-14 — the steward's acceptance, and decision 14 applied

- **[user] In chat**: accepted by name, as the Dev Env Steward, the 8 findings of
  `GATES_PIP_AUDIT_ACCEPTED_DEV_ENV`; authorized the applies of `production/foundation/` and
  `sandbox/dev-env/`.
- **[Claude] Before the writes**: the two peer sessions on this machine, both idle, were told;
  `get-caller-identity` read the infrastructure user through `InfrastructureAccess` in Production and in
  Sandbox.
- **[Claude] `production/foundation/`** from its saved plan, 21:52:52Z-21:53:04Z: `1 added, 1 changed, 0
  destroyed`, the runner role's description and its inline policy `registry-state`; the re-plan, with the
  alerts tfvars, read `No changes`.
- **[Claude] `sandbox/dev-env/`** from its saved plan, 21:53:30Z-21:53:40Z: `0 added, 1 changed, 0
  destroyed`, the image's description; the re-plan read `No changes`, and `describe-image` reads `CREATED`
  with the new description.
- **[Claude] The policy simulator** on `awsds-prod-runner-deploy`, given `aws:RequestedRegion` and
  `aws:PrincipalOrgID` as context: `s3:GetObject` on `production/registry/terraform.tfstate` allowed and on
  `production/foundation/terraform.tfstate` implicitly denied; `s3:ListBucket` allowed with the registry's
  key as prefix and denied with `production/`; `kms:Decrypt` on the state key allowed and `kms:Encrypt`
  denied; `s3:PutObject` on the registry's key explicitly denied. Without the context every S3 action read
  `explicitDeny` from the organization's policies, the simulator lacking the Region the S3 ARN does not
  carry.

## 2026-10-14 — the GitLab session: gates-v0.3.0 and the two seeds

- **[user]** Ran `make hub-up` and `make gitlab-up` from this worktree; published `gates-v0.3.0` on
  `awsds/ci-gates` (`gitlab.md` §G step 4, the four `ci-gates/` files of this branch); pushed the two seeds
  (`gitlab.md` §M), `awsds/dev-env` `main` at `f44f19e3` and `awsds/deploy-image` `main` at `98a3dc7e`.
- **[Claude] The runners**: `./aws/cicd.py` 0 FAILED, `CI-1` the deploy runner `t3a.small` running, `CI-9`
  the test runner with hop limit 1. The deploy runner's first boot, read with `get-console-output`, lists
  four profiles and assumed each: the three deploy roles, and `awsds-prod-runner-deploy` as
  `assumed-role/awsds-prod-runner-deploy/<instance id>`, the instance's own role (decision 14's profile
  through the AWS CLI; Terraform's read of it is unexercised).
- **[Claude] `gates-v0.3.0`**, read through the user's Chrome session: the tag at
  `2cc067490b603f6767802035faed624d5213e3ab`, `main` at the same commit; pipelines #5 (`main`) and #6 (the
  tag) green on the test runner, `baselines-shape` reading `GATES_PIP_AUDIT_ACCEPTED_DEV_ENV: 8 key(s)`.
- **[Claude] GitLab's CI Lint** (`POST /projects/:id/ci/lint`, which creates nothing) on the two pipeline
  files as GitHub served them at `e45e1e3a`: both valid, no error or warning; a dry run of `awsds/dev-env`'s
  `main` lists `secret_detection`, `secret-detection-gate`, `pip-audit` and `recipe-checks`.
- **[Claude] The copy**: `./scripts/gitlab-mirror.py --dry-run` read both projects' last commits as the files
  the copy holds, 13 and 5; the run wrote `gitlab/mirror.json` alone.
- **[Claude] `awsds/dev-env` pipeline #2**, on the seed: `recipe-checks` passed in 5 s (`NO_PROXY_LIST: 70
  entries`, the settings parsing, 7 env keys), `secret_detection` and its gate passed, and `pip-audit`
  failed in 87 s with "452 package(s) audited, 73 vulnerability(ies) with a fixed version" on the test
  runner: the uv export the gate's 3.12 image could not run at 3.13 ran at 3.12 (decision 13), and the
  count is the laptop's with the markers removed. `awsds/deploy-image` created no pipeline, its rule
  admitting the web form alone.
- **[user] Stage 8 step 1.0's owed reading**: as the data-scientist persona, a Developer, tried to create
  the tag `default-v0.0.0` on `awsds/dev-env`, and GitLab refused it. **[Claude]** Read through the user's
  Chrome session: the project holds no tag, and its one protected tag is `*-v*`, created by Maintainers.
- **[user] The release's merge request**, as the local administrator: `awsds/dev-env` !1 from the branch
  `lock-past-the-findings` (`e9daa79d`), the targeted `uv lock --upgrade-package` and the `include` moved to
  `gates-v0.3.0`'s commit `2cc06749`. **[Claude]** Its diff: `dev-env/python/uv.lock` +41/-40 lines and the
  one `ref` line of `.gitlab-ci.yml`. Pipeline #3 green on the test runner: `recipe-checks` 6 s,
  `secret_detection` 10 s and its gate 6 s, and `pip-audit` 89 s reading "8 accepted finding(s)" and "452 of
  452 pinned package(s) audited, 0 blocking vulnerability(ies)". With pipeline #2's 73 on the seed, that is
  verification (x) on a real lock: the gate stops the vulnerable set and admits the upgraded one with the
  steward's list.
- **[user]** Merged `awsds/dev-env` !1 as the steward, at 00:11:36Z on 2026-10-15 (UTC), merge commit
  `69ad278e`.
- **[Claude] `main` pipeline #4** on `69ad278e`, green on the test runner: `pip-audit` 89 s, "8 accepted
  finding(s)" and "452 of 452 pinned package(s) audited, 0 blocking vulnerability(ies)", `recipe-checks`,
  `secret_detection` and its gate.
- **[Claude] The copy**: `./scripts/gitlab-mirror.py awsds/dev-env` read 2 changed (`.gitlab-ci.yml`'s
  `ref` line and `dev-env/python/uv.lock`), 0 added, 0 removed; the merged lock is byte for byte the one
  audited offline, with the same 8 source builds and 444 packages carrying a `cp312` Linux x86_64 wheel.
  `./scripts/check-gitlab-mirror.py --plan` passes all eight checks: `GM-1` the copy at `69ad278e`, `GM-4`
  70 names, sha256 `aafa08da98a61f5c` on both sides, `GM-8` 3 pins each scoped and granted.
- **Owed, after PR #131 merges**: the mirror `awsds/infrastructure` and `git push gitlab main` (`gitlab.md`
  §M), then the tag `default-v0.7.0` and the release in `dev-env.md` §B's order. The hub, GitLab and the
  three runners are left up.

## 2026-10-15 — the infrastructure mirror, and `default-v0.7.0` stopped at its gate

- **[user]** Created the GitLab project `awsds/infrastructure` (`gitlab.md` §M): private, `main` protected
  for Maintainers, `awsds/dev-env-stewards` as Reporter, `awsds/dev-env` on the job token's allowlist;
  added the remote `gitlab` to the project folder and pushed `main`.
- **[Claude] Read through the user's Chrome session**: project 6, private, default branch `main` at
  `b7d37ff`, `origin/main`'s commit; `main` protected, push and merge Maintainers, no force push; the
  stewards group shared at Reporter, no direct member; the job token's inbound scope on, its allowlist
  `awsds/dev-env` and the project itself.
- **[user] As the steward**, as the local administrator: the tag `default-v0.7.0` on `awsds/dev-env`'s
  `main`, `69ad278e`.
- **[Claude] Pipeline #24**, created 00:40:07Z. `pip-audit` 81 s and `recipe-checks` 6 s on the test
  runner. `build-images` 951 s on the build runner: `base` 3 min 3 s, `dev-env` 10 min 58 s, the smoke
  build 1 min 32 s.

  | Image | Digest | Size (ECR) | Pushed (UTC) |
  |---|---|---|---|
  | `awsds-prod-ecr-base:default-v0.7.0-69ad278e` | `sha256:c17191c96d03c20f529ebe324349352b0188b54b48057fbfe730d85b52e122be` | 3,745,649,522 | 00:44:45 |
  | `awsds-prod-ecr-dev-env:default-v0.7.0-69ad278e` | `sha256:b1e896e043de6e46a286ec5b455f659d427dee885abc0c67a440508f801d685c` | 6,678,357,140 | 00:55:43 |

  The smoke build, inside the image as its user: curl `200 ssl_verify=0`; git stopped at the
  authentication wall, not a certificate; urllib and requests `200` in both Pythons; the house Python
  3.12 (pinned 3.12), Julia 1.12.7, Rust 1.98.0; the 14 imports, torch `2.13.0+cpu` and tensorflow
  2.21.0 among them. The manifests: Python 3.12.14 in both environments, uv 0.12.17, R 4.5.3, the
  `NO_PROXY` literal 70 entries with sha256 `aafa08da98a61f5c`; the house environment's 452 packages
  equal the merged lock to the version, the virtual project the one lock entry absent; the distribution
  621, R 70.
- **[Claude] The scans**, informative (decision 1): both images read CRITICAL 113, HIGH 610, MEDIUM 154,
  LOW 4, UNDEFINED 436. The 130 baseline findings are all still found, and the 593 past it are all
  `linux-libc-dev 6.8.0-142.142` (113 CRITICAL, 480 HIGH), identical in both images and the count
  `app-etl`'s `v0.1.0` met. The SageMaker Distribution pin is `default-v0.6.0`'s,
  `sha256:e4ca47c4…476b`; `dev-env` is 3,263,767 bytes larger than `v0.6.0`'s.
- **[user] In chat**: authorized the detach. **[Claude]** `dev-env.md` §B steps 1 and 2: no app running;
  the two peer sessions told; `update-domain` from the live block at 01:13:42Z, `InService` at 01:13:44Z,
  the read-back identical to the block sent, both `CustomImages` empty.
- **[user]** Ran `release-gate` at 01:15:06Z. **[Claude]** It failed in 7 s on the test runner: it printed
  `released by felipenoris: default-v0.7.0-69ad278e`, then bash stopped with `unexpected EOF while looking
  for matching '"'`. The apostrophe in `${BASE_DIGEST:-(an earlier run's, SKIP_BASE=1)}` opened a quote
  that never closed. `register` was skipped: nothing applied, version 6 intact, the domain left detached.
  `bash -n` over every script item of the six tracked pipeline files fails this one item and no other.
- **[user] In chat**: asked whether the detach is needed on every deployment, and why the mirror is a
  copy rather than a clone of GitHub. **[Claude]** Yes under the current design (decision 7); the mirror's
  argument is now in decision 2's text. The measurement of a release without the detach was proposed
  as a separate session and started by the user.

## 2026-10-15 — the gate's quote fixed, and two defects of the register path found before it

- **[user]** `awsds/dev-env` merge request !2 (`fn/fix_eof`), opened 01:22:27Z, merged 01:24:06Z at
  `c268de48`: the one line, `(from an earlier run, SKIP_BASE=1)`. Then the tag `default-v0.7.1` at
  `c268de48`. `default-v0.7.0-69ad278e` stays in both repositories, built and never registered.
- **[Claude] The copy**: `./scripts/gitlab-mirror.py awsds/dev-env` read 1 changed (`.gitlab-ci.yml`).
  `scripts/check-gitlab-ci.py` gained check C, every `before_script`, `script` and `after_script` item
  read with `bash -n`: 24 items in 6 files pass, and the copy before !2 fails at the release gate.
- **[Claude] `ListAliases`**, read before the gate. The register job's plan is the slice's first as
  `awsds-deploy-devenv-sandbox`. CloudTrail of the infrastructure user's replace of version 5
  (2026-10-12) lists the provider's calls: on refresh `DescribeImage`, `DescribeImageVersion`,
  `ListAliases`, `ListTags`, `DescribeAppImageConfig`; on the replace `DeleteImageVersion`,
  `CreateImageVersion` and `ListAliases` again. The role's `apply-dev-env` lacked `ListAliases`, and
  the policy simulator read it `implicitDeny` on the image and the version. **[user] In chat**:
  authorized the apply. **[Claude]** `sandbox/foundation/` from its saved plan, 01:35:55Z-01:36:05Z:
  `0 added, 1 changed, 0 destroyed`, the one action added; re-plan `No changes`; the simulator then read
  it allowed on both.
- **[Claude] The runner's own profile**, read before the gate. The register job reads
  `production/registry/`'s state through `awsds-prod-runner-deploy` (decision 14), which the runner
  wrote with `credential_source = Ec2InstanceMetadata` and no `role_arn`. On the laptop, Terraform
  1.15.8's S3 backend in a `terraform_remote_state` refused that shape: `Error: credential type
  credential_source requires role_arn`. A profile with a `role_arn` passed that check and a profile
  with a region alone did too, both then stopping at the instance metadata the laptop lacks; the AWS
  CLI, which the runner's boot used, ignores the key. **[user] In chat**: authorized the apply.
  **[Claude]** `production/runners/` from its saved plan, 01:50:16Z-01:51:13Z: the deploy runner
  replaced (`1 added, 1 destroyed`), the user data's one difference the removed line; re-plan `No
  changes`. The new instance's first boot (01:51:15Z-01:55:00Z) assumed the three deploy roles and
  read `awsds-prod-runner-deploy` as the instance's own role, registered as a new manager of runner #3
  at 01:54:45Z, and pulled the deploy image by digest.
- **[Claude] The resource policies on the path**: both state buckets carry `DenyInsecureTransport` alone,
  and both state keys delegate to the account's IAM alone.
- **[Claude] Pipeline #28**, created 01:24:30Z. `pip-audit` 84 s, `recipe-checks` 5 s. `build-images`
  956 s: `base` 3 min 5 s, `dev-env` 11 min 8 s, the smoke build about 1 min 40 s.

  | Image | Digest | Size (ECR) | Pushed (UTC) |
  |---|---|---|---|
  | `awsds-prod-ecr-base:default-v0.7.1-c268de48` | `sha256:4accbaf5fbed110e805a79e7893bb13d9b8246425bc4447264b8bb81b481e525` | 3,745,649,509 | 01:29:10 |
  | `awsds-prod-ecr-dev-env:default-v0.7.1-c268de48` | `sha256:3b6d706a9a16025a4b3d749fbe0d8dbca76ccacb69f1080ed5b0b2c29c3384a4` | 6,678,358,952 | 01:40:18 |

  The smoke build read as `v0.7.0`'s, and the eight manifests are byte for byte `v0.7.0`'s but the base
  digest's line. `scan-base` 35 s, `scan-dev-env` 5 min 46 s with 20 polls of `IN_PROGRESS`: the same
  723, 130 and 593 `linux-libc-dev`.

## 2026-10-15 — version 7, registered by the pipeline

- **[user]** Ran `release-gate` of pipeline #28: 01:58:57Z-01:59:06Z, `released by felipenoris:
  default-v0.7.1-c268de48` with both digests.
- **[pipeline] `register`**, 01:59:07Z-02:00:05Z on the new deploy runner instance: the proxy answered
  `404`; `infrastructure checkout: b7d37ff…`, the mirror's commit; target `sandbox` as
  `awsds-deploy-devenv-sandbox`; `init` with the module from GitHub and the providers through the proxy;
  `data.terraform_remote_state.registry: Read complete after 0s` through the runner's own profile; `Plan:
  1 to add, 0 to change, 1 to destroy`; version 6 destroyed and version 7 created at 01:59:57Z, `Apply
  complete! Resources: 1 added, 0 changed, 1 destroyed`; `awsds-sandbox-dev-env version 7: CREATED`, its
  `ContainerImage` the pushed digest `sha256:3b6d706a…84a4`.
- **[Claude] Read from the laptop**: version 7 `CREATED`, `ContainerImage`
  `…/awsds-prod-ecr-dev-env@sha256:3b6d706a…84a4`, `BaseImage` the tag `default-v0.7.1-c268de48`, the only
  version of the image. `image_tag`'s default set to the released tag, and the slice's plan as the
  infrastructure user read `No changes`.
- **[user] In chat**: authorized the re-attach and `make up ENV=sandbox ONLY=egress AUTO=1`. **[Claude]**
  §B step 5: `update-domain` from the live block and the slice's `custom_images` output at 02:11:36Z,
  `InService` at 02:11:38Z, the read-back identical to the block sent, and against the block read before
  the detach only `ImageVersionNumber` 6 to 7 on both app types. Step 6: the project's one space,
  `default-28f1b390-…`, names AWS's distribution by alias `4.5`, nothing to repair. `sandbox/egress`
  applied 02:11:50Z-02:14:44Z, `27 added`, 18 interface endpoints `available`.
- **[user] The new space**, in the portal as the Data Scientist User: `jup-house-image`, JupyterLab,
  created 03:05:41Z with `DefaultResourceSpec` naming `image-version/awsds-sandbox-dev-env/7`; its app
  `CreateApp` 03:05:45Z, `InService`, `ResourceSpec` version 7. **[Claude]** Production's CloudTrail:
  `BatchGetImage` on `awsds-prod-ecr-dev-env` at 03:07:32Z, `AWSAccount` with session `SageMaker`, by the
  digest `sha256:3b6d706a…84a4`. The project's default space had started an app at 03:01:24Z, the
  project role with the user's identity as `sourceIdentity`, on its own `sagemaker-distribution-cpu`
  `4.5`: a space keeps the image it was created with.
- **[Claude] The instruments**: `./aws/devenv.py` passes `DE-1` to `DE-6`, `DE-5` reading version 7,
  `sha256:3b6d706a9a16…`, 70 names, sha256 `aafa08da98a61f5c`; `./aws/cicd.py` 0 checks failed, `CI-6`
  noting N = 1 with `awsds-prod-ecr-dev-env@sha256:3b6d706a…84a4`, `CI-1` the new runner instance, `CI-8`
  27 assumptions, all the deploy runner's; `./aws/studio.py` every `US-*` passing. Its exit 1 is the
  signed-out persona and `ctadmin` profiles. The attachment read version 7 on both app types at 03:17:13Z,
  the domain's `LastModifiedTime` still the re-attach's.
- **[Claude] The release loop (step 1.7)**, on `default-v0.7.1`, a one-line change: merge request opened
  01:22:27Z, version registered 02:00:05Z, 37 min 38 s. Of it, the pipeline's machine time was about 24
  min (gates 1.5, build 16, scans 6, registration 1) and the steward's gate waited 11 min 12 s, the
  deploy runner's replacement inside it. The re-attach followed 11 min 31 s later. The first release took 3 h
  23 min from merge request !1 (23:44:01Z) to the first space's pull, three first-run defects included.

## 2026-10-15 — `default-v0.7.0` and `default-v0.7.1` in the release ledger, and the copy

- **[Claude] Read before the merge request**: `awsds/dev-env`'s `main` at `c268de48`, no merge request
  past !2, and the copy holding that commit's 13 files (`./scripts/gitlab-mirror.py --dry-run`).
  `aws ecr describe-images` as the infrastructure user on Production (`awsds-infra-prod`) read the four
  images the proposed rows name at the digests, sizes and push times of pipelines #24 and #28 above.
  `./scripts/check-gitlab-mirror.py --plan` passed `GM-1` to `GM-8` on that copy. The mirror
  `awsds/infrastructure` read `b7d37ff`, one commit behind `origin/main`'s `ffa23d7`.
- **[Claude] The rows** the release session proposed, after `default-v0.6.0`'s in README.md's "The
  releases": commit `69a1333` on the branch `the-releases-v0.7` of a clone, not pushed.
- **[user]** Pushed the branch, opened merge request !3 and merged it as the steward at 03:52:01Z:
  `main` at `bb13918b`.
- **[Claude] The copy**: `./scripts/gitlab-mirror.py --dry-run`, then `./scripts/gitlab-mirror.py`:
  `awsds/dev-env` 1 changed, `README.md`, byte for byte `69a1333`'s; `awsds/deploy-image` unchanged at
  `98a3dc7e`. `./scripts/check-gitlab-mirror.py --plan` passed `GM-1` to `GM-8`, `GM-1` naming
  `bb13918b` and `GM-4` reading 70 names, sha256 `aafa08da98a61f5c`, on both sides. `awsds/infrastructure`
  then read `ffa23d7`, `origin/main`'s commit.

## 2026-10-15 — decision 7 reopened, and decision 18

- **[user] In chat, 2026-10-14**: proposed that each dev-env tag add an image version instead of replacing
  one, as SageMaker publishes its own images, with a second flow retiring any version past a history of
  10; and asked whether `register` applies, how its state reaches this repository, and whether
  `sandbox/dev-env/` could live in GitLab alone.
- **[Claude] Read as the infrastructure user on Sandbox** (`awsds-infra-sandbox-1`, `InfrastructureAccess`),
  read-only, at about 01:35Z with the release in flight: both `CustomImages` lists `[]`, version 6 the
  image's only version and no alias on it, the project's default space on AWS's distribution by alias
  `4.5`, no app running, `sandbox/egress` down. Service Quotas: 500 SageMaker images per account (default
  250), and no quota on versions per image. Every bump in this log and in Stage 6d's deleted the domain's
  apps before the first `update-domain`, so whether it refuses with an app running has never been read.
- **[Claude] Read in the references**: `CustomImage` carries `ImageName`, an optional `ImageVersionNumber`
  and `AppImageConfigName`, and no alias field; `ResourceSpec.SageMakerImageVersionAlias` is semver-shaped;
  `UpdateImageVersion` takes `AliasesToAdd`, `AliasesToDelete` and `VendorGuidance`, whose
  `TO_BE_ARCHIVED` archives a custom version after three months and whose `ARCHIVED` is "not searchable".
  Provider 6.64.0 keys `aws_sagemaker_image_version` by name and number, reads aliases with `ListAliases`,
  updates aliases and `VendorGuidance` in place, and forces a new version only on `base_image` and
  `image_name`.
- **[user] Decision 18 taken**: the image version is a release artifact, created by `awsds/dev-env`'s
  pipeline with a semver alias, and the versions leave Terraform's state; the stage file carries the
  decision and its alternatives.

## 2026-10-15 — decision 7's readings on a probe image

Every write below as the infrastructure user on Sandbox (`awsds-infra-sandbox-1`, `InfrastructureAccess`),
authorized by the user in chat per write; account ids masked as `<acct>` while reading.

- **[Claude] W1-W3**, authorized: `create-image awsds-sandbox-dev-env-probe` (role
  `awsds-sandbox-sagemaker-image`, the five tags, `ManagedBy=console`, `CostCenter=stage-08`) at 04:33:05Z,
  `CREATED` within 9 s; `create-app-image-config awsds-sandbox-dev-env-probe-jupyterlab` (JupyterLab, empty)
  at 04:33:06Z; `create-image-version` at 04:33:25Z with `BaseImage` the `awsds-prod-ecr-dev-env` repository
  **by digest** (`default-v0.5.0`'s `@sha256:8ec04e35…9dd6`), alias `0.5.0`, `VendorGuidance STABLE`:
  version 1 `CREATED` 2 s later, `BaseImage` and `ContainerImage` both the digest form, `list-aliases`
  reading `0.5.0`. The first attempt of W1 and W2 failed in the CLI (exit 252, `ParamValidation` on
  `--tags`, an unsplit zsh variable) and sent nothing.
- **[Claude] W4**, authorized: `update-domain` at 04:33:51Z, the live `DefaultUserSettings` with the
  JupyterLab list holding version 7's entry unchanged and `{awsds-sandbox-dev-env-probe,
  awsds-sandbox-dev-env-probe-jupyterlab}` with **no** `ImageVersionNumber`, sent while two apps were
  `InService` (`jup-house-image` and the project's default space). **Accepted**: `InService` at 04:33:53Z with
  no `FailureReason`, the block read back identical to the one sent, the probe entry stored with no version
  number, and both apps still `InService` at their 03:05:45Z and 03:01:24Z creation times. So the vendor's
  *"you must delete all of the applications in your domain"* is not enforced on adding a custom image.
- **[Claude] `probe-p1`, through the user's Chrome at the user's request**, in the portal's project
  `eighth-experimentation` as the data scientist. *Create new space*'s **Image** picker listed *Default*:
  `SageMaker Distribution 4.5`; *Custom Images (2)*: `AWS-DataScience dev-env v7` and `dev-env probe (Stage 8
  decision 7) v1`; *Image Versions (19)*: AWS's distribution `2.14`, `3.9`, `4.0` to `4.4`, and twelve more
  marked `(End of support)`. **The entry with no version number is labelled with the image's newest
  version.** `probe-p1` (JupyterLab, `ml.t3.medium`, 16 GB, remote access disabled) was created at
  04:43:58Z: CloudTrail's `CreateSpace`, by the project role in the data scientist's portal session, carried
  a `defaultResourceSpec` naming the probe's image **and `image-version/awsds-sandbox-dev-env-probe/1`**. So
  the portal resolves the entry to the newest version and pins that number into the new space, and
  `describe-space` reads it back. `CreateApp` at 04:44:03Z, through `sagemaker.amazonaws.com`, sent an empty
  `resourceSpec`; the app was `InService` at 04:53:59Z on version 1, 9 min 56 s after its creation.
- **[Claude] Two apps stopped meanwhile, neither by this session**: `jup-house-image`'s `DeleteApp` at
  04:41:12Z, by the project role in the data scientist's portal session from the browser's address; the
  default space's at 04:44:04Z, by `AWSServiceRoleForAmazonSageMakerNotebooks` (idle shutdown,
  `log-debugging.md`). Both had read `InService` after W4.
- **[Claude] W5**, authorized with W6-W17 and the portal steps: probe version 2 at 05:00:59Z, by digest of
  `default-v0.6.0` (`@sha256:43079013…5518`), alias `0.6.0`, `CREATED` 3 s later. `probe-p1` still read
  version 1 in its spec and its running app. With the entry still version-less, the picker then listed
  **every version**: *Custom Images (3)*, `dev-env v7`, `probe … v2` and `probe … v1`, newest first.
  `probe-p2` was created on `v2` at 05:01:54Z and its spec reads `image-version/…-probe/2`.
- **[Claude] `jup-house-image` deleted meanwhile**, not by this session: `DeleteSpace` at 04:58:03Z by the
  project role in the data scientist's portal session, from the browser's address.
- **[Claude] W6**: `update-domain` at 05:02:24Z with the JupyterLab list holding version 7's entry and the
  probe **twice**, `ImageVersionNumber` 1 and 2, while `probe-p1` and the default space ran. **Accepted**,
  `InService` within 3 s, the block read back identical. The picker listed the same three options.
- **[Claude] W7**: probe version 1 to `VendorGuidance TO_BE_ARCHIVED` at 05:03:09Z; its label in the
  picker stayed `… v1`, with no `(End of support)`. **W8**: version 1 to `ARCHIVED` at 05:03:49Z;
  `describe-image-version` reads `CREATED` and `ARCHIVED`, `list-image-versions` still lists it, and the
  picker still offered it with the entry naming it.
- **[Claude] W9**: `update-domain` at 05:05:03Z back to the version-less probe entry, read back identical
  to the block after W4. **With version 1 `ARCHIVED`, the picker still listed `… v2` and `… v1`**: archiving
  hides nothing from the portal's picker. `probe-p1` was stopped in the portal at 05:04Z and started at
  05:06Z, its spec still naming the archived version 1.
- **[Claude] The default space started by the portal**: `CreateApp` on `default-28f1b390-…` at 05:01:18Z, by
  the project role in the data scientist's portal session, with AWS's distribution by alias `4.5`, and a
  second one in the same second refused `ResourceInUse`. It came with this session's navigation to the
  project's *Spaces* page in the user's Chrome, so opening the project starts its default space.
- **[Claude] `probe-p1` restarted on the archived version**: stopped in the portal at 05:04Z and started at
  05:05:53Z. The portal's `CreateApp` sent the space's own spec, `image-version/…-probe/1`, and the service
  accepted it with version 1 `ARCHIVED`.
- **[Claude] W10**, the first run of `dev-env.md` §B step 6's CLI route: `probe-p2` stopped in the portal
  (its app `Deleted` at 05:12:37Z), then `update-space` at 05:12:38Z with the live `SpaceSettings`, its
  `DefaultResourceSpec` carrying `SageMakerImageVersionAlias: "0.6.0"` and `SageMakerImageVersionArn:
  "None"`. **Accepted**, `InService` within 2 s. Read back, the spec names the image and the alias and no
  version; the idle settings, the 16 GB volume, `RemoteAccess: DISABLED` and the project's S3 mount are
  intact, and **`SpaceManagedResources: ENABLED`, sent with the block, is gone from the read**. The portal
  then bannered `probe-p2` as running an *outdated SageMaker Distribution image*, `Recommended Version:
  4.5`: it reads any alias as the distribution's. `probe-p2` started from the portal at 05:13Z, its app
  `ResourceSpec` carrying the alias `0.6.0`.
- **[Claude] Read in Production's CloudTrail** (`awsds-infra-prod`), `BatchGetImage` on
  `awsds-prod-ecr-dev-env`, each record `AWSAccount` with a `<role id>:SageMaker` principal, the role ids
  resolved in Sandbox: at each `CreateImageVersion` the image role `awsds-sandbox-sagemaker-image` (05:01:01Z
  for version 2, 05:23:28Z for version 3), and at each app start the project role
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, always by digest: `probe-p1`'s first start
  `8ec04e35…9dd6` at 04:45:45Z; `probe-p2`'s first start `43079013…5518` at 05:03:39Z; **`probe-p1`'s
  restart on the `ARCHIVED` version 1, `8ec04e35…9dd6` at 05:07:35Z**, its app `InService` at 05:16:29Z;
  and **`probe-p2`'s start on the alias `0.6.0`, `43079013…5518` at 05:14:46Z**, version 2's digest, its app
  `InService` at 05:22:43Z. So an archived version still starts the space that names it, and a space's
  alias resolves to the version holding it.
- **[Claude] W11-W13**: probe version 3 at 05:23:26Z, by digest of `default-v0.7.1-c268de48`
  (`@sha256:3b6d706a…84a4`), no alias, `CREATED` 3 s later; alias `0.6.0` deleted from version 2 at
  05:23:29Z and added to version 3 at 05:23:30Z. The picker then listed *Custom Images (4)*: `dev-env v7`
  and `probe … v3`, `v2`, `v1`, so a version-less entry offers versions no space names. `probe-p2` was
  stopped and started again in the portal at about 05:24:30Z.
- **[Claude] W14**: `delete-image-version` of probe version 1 at 05:25:27Z, `ARCHIVED`, named by no domain
  entry and by `probe-p1`'s spec while its app ran. Gone within 5 s; `list-image-versions` reads 3 and 2.
  The domain stayed `InService` with no `FailureReason`, its `LastModifiedTime` W9's and
  `DefaultUserSettings` unchanged; `probe-p1`'s app stayed `InService` on the deleted version, and its spec
  still names `image-version/…-probe/1`, so its next start is stranded (`EXC-09`). The picker then listed
  `dev-env v7`, `probe … v3` and `v2`: a deleted version leaves it, an archived one does not.
- **[Claude] `probe-p2` after the alias moved**: its restart pulled **`3b6d706a…84a4` at 05:26:41Z**,
  version 3's digest, as the project role. A space naming an alias follows the alias to its new version
  at its next start.
- **[Claude] W15**: `update-domain` at 05:29:28Z removing the probe's entry, while three apps ran,
  `probe-p1` and `probe-p2` on the probe among them. **Accepted**, `InService` within 2 s, the block read
  back identical and **identical to the one read before W4**; the three apps unchanged. So adding, listing
  twice and removing a custom image were each accepted with apps running, one of them an image in use.
- **[user] Deleted `probe-p1` and `probe-p2`** in the portal; at 05:41:57Z `list-spaces` read the project's
  default space alone, and neither domain list named the probe.
- **[Claude] W16-W17**: `delete-image awsds-sandbox-dev-env-probe` at 05:42:09Z, `DELETING`, then gone by
  05:42:18Z with versions 2 and 3; `delete-app-image-config awsds-sandbox-dev-env-probe-jupyterlab` at
  05:42:18Z, gone. Left: `awsds-sandbox-dev-env` with version 7, its two configurations, the domain's block
  as before W4, the default space's app started by the portal at 05:01:18Z, and `sandbox/egress` up since
  the release's re-attach.
- **[user] Decision 7 taken, as recommended**: the house image is attached once per domain with no version
  number, a release is the pipeline's `create-image-version`, and the retirement deletes every version past
  the newest 10 that no space names. Implemented in the same pull request, each apply and the domain write
  authorized per occurrence.

## 2026-10-15 — decisions 7 and 18 applied

Pull request #134, as the infrastructure user on Sandbox (`awsds-infra-sandbox-1`, `InfrastructureAccess`),
the registry's state read through `awsds-infra-prod`; each act authorized by the user in chat.

- **[Claude] `deploy-role-v0.4.0`**, Recipe B: the module alone in commit `454ca7e`, tagged and pushed,
  `git ls-remote` reading the tag at that commit. `state_prefixes` may be empty, and a role with no prefix
  and no read key gets no state policy.
- **[Claude] A1**: `sandbox/dev-env/`'s saved plan applied at 06:11:51Z, `Apply complete! Resources: 0 added,
  0 changed, 0 destroyed.`, with `aws_sagemaker_image_version.dev_env` no longer managed (`destroy =
  false`); re-plan `No changes`, the state listing the image, the two configurations and the image role
  only. Version 7 still `CREATED` at `@sha256:3b6d706a…84a4`.
- **[Claude] A2**: `sandbox/foundation/`'s saved plan applied at 06:12:32Z, `1 added, 2 changed, 2
  destroyed`: the inline policies `state` and `apply-dev-env` destroyed, the ceiling and the role's
  description updated, `dev-env-versions` created; `list-role-policies` reads `dev-env-versions` alone.
  **The re-plan read `0 to add, 1 to change`**: the saved plan predates the commit that added
  `sagemaker:ListDomains` and `DescribeDomain` on `domain/*` to `dev-env-versions` for the retire job's
  domain read, so that change waits for its own authorization, saved as a plan.
- **[Claude] D1**: `update-domain` on the project's domain at 06:14:04Z, the live `DefaultUserSettings` with
  both lists set from the slice's `custom_images` output. `InService` 2 s later, read back identical, and
  against the block read before it the only change is `ImageVersionNumber: 7` gone from both entries; the
  default space's app, running, untouched. The house image is attached with no version number.
- **[Claude] A2b**, authorized separately: the saved plan applied at 06:17:00Z, `0 added, 1 changed, 0
  destroyed`, `dev-env-versions` with `sagemaker:ListDomains` and `DescribeDomain` on `domain/*`; re-plan
  `No changes`. The policy simulator, given the Region as context, reads the role's edges:
  `CreateImageVersion` on `awsds-sandbox-dev-env`, `DeleteImageVersion` on its versions, `ListImages`,
  `ListSpaces`, `ListDomains`, `DescribeSpace` and `DescribeDomain` allowed; `CreateImageVersion` on another
  image, `DeleteImage` and `s3:GetObject` on `sandbox/dev-env/`'s state an implicit deny; `UpdateDomain`,
  `UpdateSpace`, `iam:PassRole` and `iam:PutRolePolicy` on the image role an explicit deny, the ceiling's.
- **[Claude] The GitLab half**: the branch `decision-18-versions` of a clone of `awsds/dev-env` (commit
  `ef0e0e5`, byte for byte the copy under `gitlab/awsds/dev-env/`) pushed at 06:22:41Z, authorized by the
  user after a first push had not left the clone (`git ls-remote` read `main` alone).
- **[user]** Opened merge request !4 and merged it as the steward at 06:24:47Z: `main` at `8e78ab53`.
- **[Claude] The copy**: `./scripts/gitlab-mirror.py awsds/dev-env` read the commit's 14 files and found the
  copy already holding them, and moved `gitlab/mirror.json` to `8e78ab53`. `./scripts/check-gitlab-mirror.py
  --plan`: `GM-1`, `GM-2` (70 entries, sha256 `aafa08da98a61f5c`) and `GM-5` to `GM-8` pass; `GM-3` failed
  in `terraform init` on refreshing the expired SSO token while the CLI's cached role credentials still
  answered, so `GM-4` read one side. The merge request changed no line of `dev-env/Dockerfile`, and its
  literal is the one `GM-4` matched this morning.

## 2026-10-15 — the first release under decisions 7 and 18

Every reading below as the infrastructure user, `InfrastructureAccess`: on Sandbox through
`awsds-infra-sandbox-1`, on Production through `awsds-infra-prod`.

- **[Claude] Read before the tag**, 06:53Z-06:57Z, with the environment down. `awsds-sandbox-dev-env` holds
  version 7 alone: `CREATED`, `ContainerImage` `…/awsds-prod-ecr-dev-env@sha256:3b6d706a…84a4`, no alias.
  `awsds-deploy-devenv-sandbox` carries the inline policy `dev-env-versions` alone, under the ceiling
  `awsds-sandbox-deploy-boundary`, last used at 02:00:03Z (version 7's registration).
  `release/versions.py retire --dry-run --target awsds-infra-sandbox-1` read the one version, kept it and
  would delete nothing.
- **[Claude] The domains**: `d-p6gthxc82ckg`, project `avhvbqn37ty7m8`, attaches the image with no version
  number on both app types, its `LastModifiedTime` 06:14:04Z (D1 above). A second domain, `d-lfgbdrjncmsu`
  of project `4gqfau9xuo6e4w`, was created at 06:06:13Z by `awsds-sandbox-smus-provisioning` in an
  `AmazonDataZoneEnvironmentDeployer` session: a second project's `Tooling` environment. It attaches no
  custom image, so its picker does not offer the house image. Each domain holds one space, its default,
  and no app ran. Both `DefaultUserSettings` were saved for the comparison after the release, and read
  unchanged again at 15:23:10Z.
- **[Claude] The instruments before the tag**: `./aws/devenv.py` passes `DE-1` and `DE-4`, and `DE-5` reads
  version 7, `sha256:3b6d706a9a16…`, 70 names, sha256 `aafa08da98a61f5c`; `DE-2` fails and `DE-3` notes,
  since `sandbox/egress` is down and its state holds no outputs. `DE-3`'s comparison, read from a plan
  instead: `./scripts/check-gitlab-mirror.py --plan` passes `GM-1` to `GM-8`, `GM-4` 70 names and sha256
  `aafa08da98a61f5c` on both sides, on the copy at `8e78ab53`. `./aws/cicd.py`: 0 checks failed, `CI-6`
  noting N = 1 with `awsds-prod-ecr-dev-env@sha256:3b6d706a…84a4`, `CI-8` 27 assumptions, all the deploy
  runner's; its exit 1 is the seven persona and `ctadmin` profiles that hold no token.
- **[user]** `make hub-up` and `make gitlab-up` from the project folder's `main`, at `87c1a87`,
  `origin/main`'s commit. **[Claude] Read** at 15:22:57Z: the hub hosts started at 15:18:09Z and
  15:18:13Z, GitLab at 15:19:18Z, the three runners launched 15:21:19Z-15:21:27Z, and 12 interface
  endpoints `available`. `git ls-remote` of `awsds/dev-env` read `main` at `8e78ab53` and the tags
  `default-v0.7.0` and `default-v0.7.1`.
- **[Claude] The runners' first boots**, read on their serial consoles: the build runner done at
  15:24:20Z; the deploy runner done at 15:25:45Z, having assumed `awsds-deploy-prod`,
  `awsds-deploy-devenv-sandbox` and `awsds-deploy-staging` with the instance's credentials, registered as
  `awsds-prod-runner-deploy-i-0e9f2c8c81a1f9295` (gitlab-runner 19.5.0) and pulled the deploy image by
  digest `sha256:1b1a5830…a53a`; the test runner done at 15:26:40Z, reading `no token from a container:
  the jobs hold no AWS identity`. Each read `pypi.org` `200` and a private address `403` through the
  proxy, and the sign-in page `200` direct.
- **[user] As the steward**: the tag `default-v0.7.2` on `awsds/dev-env`'s `main`, `8e78ab53`, a rebuild
  with no recipe change (`base/`, `dev-env/` and `smoke/` unchanged since `c268de48`). Pipeline #33,
  created 15:34:14Z.
- **[Claude] Read through the user's Chrome session, GitLab's API, GET only, at the user's request**:
  `recipe-checks` passed (15:34:17Z-15:34:35Z); `pip-audit` failed on the test runner, job #106
  15:34:16Z-15:36:02Z and its retry #114 15:37:44Z-15:39:10Z, each auditing 452 of 452; `build-images` and
  every later job skipped, so nothing was built or pushed. The one finding: `BLOCK fsspec 2025.3.0
  PYSEC-2026-4217 (GHSA-27vj-qcqg-25rc, CVE-2026-104851) fixed in 2026.6.0`, printed twice by #106 and
  once by #114, each run also printing `gone CVE-2026-104851|fsspec: accepted and no longer found`. The
  steward accepted that vulnerability on 2026-10-14 as `CVE-2026-104851|fsspec`: the same version, the
  same fix, another id.
- **[Claude] Read in OSV** (`api.osv.dev`): a query for fsspec 2025.3.0 answers `GHSA-27vj-qcqg-25rc`
  (published 2026-10-05, modified 14:56:18Z) and `PYSEC-2026-4217` (published 10:22:44Z), each naming
  `CVE-2026-104851` as an alias. The record `CVE-2026-104851` still exists, modified at 14:56:18Z, and
  names no PyPI package, so the query no longer returns it. pip-audit reports one id per alias group, and
  the id the gate keys on moved with OSV's records. One query per package of the copy's `uv.lock` (452)
  found the other seven accepted entries unchanged.
- **[user] In chat**: decision 15 amended, the gate to match an accepted entry by the finding's id or any
  of its aliases (`gates-v0.4.0`), rather than the list re-keyed to `PYSEC-2026-4217`.
- **[Claude] `gates-v0.4.0`, written** in `ci-gates/gates.gitlab-ci.yml` and its README: an entry is
  accepted when its id is the finding's id or one of its aliases, prints `accepted as <id>` when the
  match is an alias, and is no longer found only when no finding carries it. Run offline on reports
  shaped like job #114's: the fsspec finding `accpt` twice `accepted as CVE-2026-104851`, 0 blocking,
  exit 0; an added finding with a fix `BLOCK`, exit 1; a removed accepted finding `gone`, exit 0.
  `./scripts/check-gitlab-ci.py` passes, 25 script items in 6 files. GitLab's `awsds/ci-gates` read
  `main` at `2cc06749` (`gates-v0.3.0`), byte for byte this repository's `ci-gates/`. Committed in a
  clone of it as `6fcea132`, and the include moved to that commit in a clone of `awsds/dev-env`, branch
  `gates-alias-match`, as `679e33a6`; neither pushed.
- **[user]** Pushed `awsds/ci-gates`' `main` at `6fcea132` and the tag `gates-v0.4.0` on it, whose
  pipelines #34 and #35 passed, then the branch `gates-alias-match` of `awsds/dev-env` (pipeline #36,
  16:00:57Z). **[Claude, through the user's Chrome, at the user's request]** Opened merge request !5 from
  it into `main`, its title and description the commit's.
- **[Claude, through the user's Chrome, at the user's request]** Pipeline #36 passed at 16:02:31Z:
  `pip-audit` audited 452 of 452 with 0 blocking, the fsspec finding read `accpt … PYSEC-2026-4217 …
  accepted as CVE-2026-104851`, the 8 accepted findings took 15 `accpt` lines (OSV answers some twice),
  `nltk 3.10.3 PYSEC-2026-3740` warned with no fixed version, and no entry read `gone`. Merged !5 at
  16:03:26Z as the local administrator, the source branch deleted: `main` at `15fac237`, whose pipeline
  #37 passed at 16:05:02Z. Then the tag `default-v0.7.3` from `main`, `15fac237`, lightweight and
  protected: pipeline #38, created 16:05:28Z.
- **[Claude] Pipeline #38**, read through GitLab's API and ECR. `pip-audit` 87 s, 0 blocking, and
  `recipe-checks` 7 s on the test runner. `build-images` 983 s on the build runner, 16:07:00Z-16:23:23Z:

  | Image | Digest | Size (ECR) | Pushed (UTC) |
  |---|---|---|---|
  | `awsds-prod-ecr-base:default-v0.7.3-15fac237` | `sha256:b05552a8ef413a5cfca9cf37e73a74520c6f9718ce1ac2712778d5ef3bc92ba1` | 3,745,649,508 | 16:10:23 |
  | `awsds-prod-ecr-dev-env:default-v0.7.3-15fac237` | `sha256:38f4864c8b85c1e99d3093368cb2a10a8c094c92a17bd8da777f3f5adfffdd6f` | 6,682,673,224 | 16:21:35 |

  The eight manifests are byte for byte `v0.7.1`'s but the base digest's line, and `dev-env` is
  4,314,272 bytes larger than `v0.7.1`'s with the same package sets. `scan-base` 43 s and `scan-dev-env`
  151 s failed as informative jobs: each read CRITICAL 113, HIGH 610, MEDIUM 158, LOW 16, UNDEFINED 436,
  the 593 past the baseline all `linux-libc-dev` (113 CRITICAL, 480 HIGH).
- **[user] As the steward**: ran `release-gate` 16:33:59Z-16:34:08Z, `released by felipenoris:
  default-v0.7.3-15fac237` with both digests.
- **[pipeline] `register`**, 16:34:11Z-16:34:32Z on the deploy runner: the proxy answered `404`; target
  `awsds-deploy-devenv-sandbox`; `awsds-sandbox-dev-env, 1 version(s), release default-v0.7.3-15fac237`;
  `create-image-version` from the pushed digest; `awsds-sandbox-dev-env version 8: CREATED, alias 0.7.3`,
  its `ContainerImage` the pushed digest `sha256:38f4864c…dd6f`.
- **[pipeline] `retire`**, 16:34:35Z-16:34:59Z: `2 version(s), keeping the newest 10`, `keep version 8
  0.7.3`, `keep version 7`, nothing deleted. Pipeline #38 succeeded at 16:34:59Z.
- **[Claude] Read from the laptop**: version 8 `CREATED` at 16:34:29Z, `BaseImage` and `ContainerImage`
  both `…/awsds-prod-ecr-dev-env@sha256:38f4864c…dd6f`, `VendorGuidance` `STABLE`, release notes
  `default-v0.7.3-15fac237`, alias `0.7.3`; version 7 kept, with no alias. Both domains'
  `DefaultUserSettings` read at 16:35Z byte for byte the 06:54Z reading, and their `LastModifiedTime`
  unchanged (06:14:04Z for `d-p6gthxc82ckg`, 06:06:23Z for `d-lfgbdrjncmsu`): the release made no domain
  write, and `d-p6gthxc82ckg`'s version-less entry now offers version 8.
- **[Claude] Sandbox's CloudTrail** for the deploy role, two sessions, every call allowed and from
  `35.95.20.251`, the proxy's address, since `VPC-SharedServices` has no SageMaker endpoint. `register`:
  `ListImages`, `ListImageVersions`, `DescribeImageVersion` and `ListAliases` on version 7, then
  `CreateImageVersion` at 16:34:29Z with the digest as `baseImage`, then `DescribeImageVersion` on version
  8. `retire`: `ListImages`, `ListImageVersions`, `DescribeImageVersion` and `ListAliases` on versions 8
  and 7, `ListSpaces`, `DescribeSpace` on both default spaces, `ListDomains`, and `DescribeDomain` on both
  domains. No `DeleteImageVersion`, `UpdateImageVersion`, `UpdateDomain`, `UpdateSpace` or `DeleteImage`
  by any caller since 16:30Z. Each session's `AssumeRole` was recorded as `AWSAccount` with the principal
  `<runner role id>:i-0e9f2c8c81a1f9295`, from the runner's private address. AWS Config's recorder read
  version 8 at 16:35:18Z.
- **[Claude] The instruments after**: `./aws/devenv.py` `DE-5` reads version 8, `sha256:38f4864c8b85…`,
  config blob `sha256:af0e1150…e818` hash-checked, 70 names, sha256 `aafa08da98a61f5c`; `DE-2` fails and
  `DE-3` notes as before the tag, `sandbox/egress` being down. `./aws/cicd.py` at 16:37:24Z: 0 checks
  failed, `CI-6` noting N = 1 with `awsds-prod-ecr-dev-env@sha256:38f4864c…dd6f`, `CI-8` 33 assumptions,
  all the deploy runner's, `CI-1` and `CI-9` passing on the running runners.
- **[Claude] The release loop under decision 18**: the tag at 16:05:28Z to the registered version at
  16:34:32Z, 29 min 3 s, with no domain write after it; merge request !5 at 16:02:03Z to the version, 32
  min 29 s. Of it, the gates 1 min 29 s, the build 16 min 23 s, the scans 2 min 33 s and the registration
  21 s; the steward's gate waited 8 min 3 s.
- **[Claude] The ledger row**: `default-v0.7.3` after `default-v0.7.1`'s in README.md's "The releases",
  `default-v0.7.2` named in it as a tag that pushed no image. **[user] In chat**: the push, the merge
  request and the merge are Claude's, through the user's Chrome. **[Claude]** The branch
  `the-releases-v0.7.3` at `5a422781` pushed from a clone; merge request !6 opened at 16:43:03Z, its
  pipeline #39 passed at 16:44:16Z, merged at 16:44:41Z as the local administrator, the branch deleted:
  `main` at `1372b471`.
- **[Claude] The copy**: `./scripts/gitlab-mirror.py --dry-run awsds/dev-env`, then without it: 2 changed,
  `.gitlab-ci.yml` (the include at `gates-v0.4.0`) and `README.md` (the row), and `gitlab/mirror.json` at
  `1372b471`. `./scripts/check-gitlab-mirror.py --plan` passes `GM-1` to `GM-8` on it, `GM-4` 70 names and
  sha256 `aafa08da98a61f5c` on both sides.
- **[user]** `make gitlab-down` and `make hub-down` from the project folder. **[Claude] Read** at
  17:15:39Z: the three runners terminated, GitLab and the WireGuard host stopped, the proxy stopping, no
  interface endpoint left in Production; `make status` at about 17:18Z read every host stopped, every
  `[E]` slice down and an estimated burn of USD 0.0000/h.

## 2026-10-15 — the house image attached to the second project's domain

As the infrastructure user on Sandbox (`awsds-infra-sandbox-1`, `InfrastructureAccess`), after an SSO
login by the user; account ids masked as `<acct>` while reading.

- **[user] In chat**: the second project's domain is to offer the house image.
- **[Claude] Read** at 23:49Z-23:51Z. `list-projects` returns two projects to this identity,
  `eighth-experimentation` and `test-experimentation` (`4gqfau9xuo6e4w`, `ACTIVE`, created at 06:05:18Z):
  by its name, D41's `test` project. Its domain `d-lfgbdrjncmsu`, `InService`, `LastModifiedTime`
  06:06:23Z, is tagged `AmazonDataZoneBlueprint=Tooling` and `AmazonDataZoneEnvironment=bi356s1sacz0cw`.
  Its `DefaultUserSettings` carries the project role, one security group, idle settings alone in both app
  settings with no `CustomImages` key, a 16 GB volume under a 100 GB ceiling, the `shared` S3 mount, the
  portal settings and `AutoMountHomeEFS`: outside `CustomImages`, the key paths of `d-p6gthxc82ckg`'s.
  One user profile, one space (the default), its JupyterLab app `Deleted`. `sandbox/dev-env/`'s output
  `custom_images` holds one entry per app type with no `ImageVersionNumber`; the image is `CREATED`, its
  versions 8 and 7 `CREATED`.
- **[Claude] The write**, authorized by the user in chat: `dev-env.md` §C6's CLI route, as D1 on
  `d-p6gthxc82ckg`. The block generated from the 23:51:01Z read differed from it in the two lists alone,
  and a re-read just before the send found the live block unchanged. `update-domain` at
  2026-10-16T00:31:24Z. Read back at 00:31:42Z: `InService` with no `FailureReason`, `LastModifiedTime`
  00:31:26Z, the block identical to the one sent, and against the 23:51:01Z read the only change is the two
  lists, `awsds-sandbox-dev-env` with `awsds-sandbox-dev-env-jupyterlab` and with
  `awsds-sandbox-dev-env-codeeditor`, no version number; the rest of the domain object unchanged, the
  default space's app still `Deleted`. The portal's picker in `test-experimentation` is not read (§C7).
- **[Claude] Read after the write**: both projects come from the same project profile and were created by
  the same Identity Center user, `28f1b390-…`, whose user profile and default space each domain holds.

## 2026-10-16 — the workflows grant attached to the second project's role

As the infrastructure user on Sandbox (`awsds-infra-sandbox-1`, `InfrastructureAccess`). Every time is UTC
on 2026-10-16.

- **[user] `terraform-live/sandbox/workflows/` applied**, Recipe A, after PR #140 listed
  `datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw`, the role of `test-experimentation` (D41's `test`
  project), in `project_roles`. The apply's output was not pasted.
- **[user] Read back after the apply**, `aws iam list-attached-role-policies --profile awsds-infra-sandbox-1
  --role-name datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw --query "AttachedPolicies[].PolicyName"
  --output text`, pasted in the chat of the session that opened PR #140 and relayed verbatim:

  ```text
  SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy    SageMakerStudioProjectRoleMachineLearningPolicy SageMakerStudioProjectUserRolePolicy    awsds-sandbox-workflows
  ```

- **[Claude] The re-plan** by the session that opened PR #140, 02:22:58Z-02:23:07Z, from content identical
  to `main`'s `f33a6d1` for the slice: `No changes. Your infrastructure matches the configuration.`
- **[Claude] CloudTrail**, `lookup-events` in `us-east-1` for `AttachRolePolicy` since 2026-10-15T20:00Z:
  one event, at 02:21:44Z, `awsds-sandbox-workflows` on `test-experimentation`'s role, by the
  infrastructure user's `InfrastructureAccess` session with Terraform 1.15.8's user agent, no error code.
  That is the apply's time.
- **[Claude] Read back**: `list-attached-role-policies` at 02:23:25Z lists the same four policies, the
  blueprint's three and `awsds-sandbox-workflows`. The re-plan, 02:23:53Z-02:24:02Z: `No changes`,
  `-detailed-exitcode` 0, both roles' attachments refreshed.
- **[Claude]** The workflows grant is on both Sandbox projects' roles, `eighth-experimentation` (D41's
  `dev`) and `test-experimentation`. Stage 6i verification xiv's second half, another project's processing
  jobs out of reach, needed a second project and is not run here.

## 2026-10-16 — step 2.5 written: app-etl as an application

Written by Claude in the cloud session of the project thread, with no AWS identity: the application
in `examples/app-etl/` and its pipeline, read against the CLI 1.0.9 and the lint offline. No tag ran
it; the Terraform of decisions 19 and 20 and the CLI in the deploy image are PRs of their own.

- **[Claude] Verification xxv, the CLI on the deploy image's Python**: in a scratch venv on CPython
  3.14.6 with `UV_PYTHON_DOWNLOADS=never`, `uv pip install aws-smus-cicd-cli==1.0.9` resolved 25
  distributions, every one a wheel (boto3 1.43.114, botocore 1.43.114, typer 0.27.3, rich 15.0.0,
  jsonschema 4.26.0, PyYAML 6.0.3, requests 2.34.2, urllib3 2.8.0, s3transfer 0.19.2 among them), and
  `aws-smus-cicd-cli --version` printed `aws-smus-cicd-cli 1.0.9`, exit 0, with the proxy and the AWS
  variables unset.
- **[Claude] `bundle` over the application, offline** (`env -i`, the proxies on a closed port, no
  credentials, fabricated values for the manifest's variables, a copy of the folder): with the
  manifest's `code` item as `include: ["code/*.zip"]` and the zip present, `Warning: Pattern not
  found: code/*.zip` on stderr, `Bundled 0 files for 'code'`, exit 0, a bundle of 5,609 bytes without
  the zip. Read in 1.0.9's `commands/bundle.py`: an include is `os.path.isfile` or `os.path.isdir`,
  never a glob, while `commands/deploy.py` expands it with `glob.glob`. With `include:
  [code/app-etl.zip]`: `Copied file: code/app-etl.zip`, a bundle of 6,968 bytes holding
  `code/app-etl.zip`, `src/app_etl/` (3 files), `glue/transform.py`, `samples/trades.csv` and
  `workflows/app-etl.yaml`; without the zip, the warning and exit 0, which `test-deploy` turns into a
  failure. The domain lookup logged three `ERROR` lines (`Unable to locate credentials`) and the
  bundle went on. The manifest's `${DOMAIN_ID}` is validated against `^dzd-[a-z0-9]+$` before anything
  runs.
- **[Claude] GitLab's `cli` image for the `release` keyword**, read from `registry.gitlab.com`'s tags
  and manifests and from the project's releases: `v1.120.0`, released 2026-09-29, digest
  `sha256:ec2d1cd59b2343fe6270acf67d6ac92b56d9898c5e70cda6395fb617c7373812` (linux amd64 and arm64);
  `v1.119.0` of 2026-09-22 is `sha256:79223ad3fa6e3c3226119ac5d0b73e55f1b909e6d5bbf8469726480723b63ba8`;
  the newest, `v1.123.0` of 2026-10-13, is under the two-week bound. The job pins `v1.120.0`.
- **[Claude] The local checks**: `uv run --locked pytest` 14 passed (the seven of the pipeline, five
  of the worker's task over a double of boto3, two of the Glue script over doubles of awsglue, pyspark
  and boto3); `ruff check` and `ruff format --check` clean; `awsds-workflows lint examples/app-etl`
  at `3c1708e`, `ok: 6 arquivo(s)`; the zip built with `python3 -m zipfile` (1,246 bytes, the module
  alone) and imported from the zip on CPython 3.12.3; `./scripts/check-gitlab-ci.py` OK (13 jobs from
  3 files, 8 names resolved for `examples/app-etl/.gitlab-ci.yml`); `./scripts/check-identifiers.py`
  OK; `./scripts/check-plan-refs.py` OK.

## 2026-10-16 — decisions 21 to 23, and the Terraform of decisions 19 and 20 written

Written by Claude in the cloud session of the project thread, with no AWS identity, in PR #145 after
step 2.5, by the user's scope of 14:30 UTC ("tudo num PR"); nothing applied. Every time is UTC.

- **[user] Decision 21** (14:55, on a card): `sandbox/app/app-etl/` retires, with `awsds-sandbox-outputs`
  and `AllowApplicationJobRolesViaS3`; the destroy is the user's. **Decision 22** (14:57): the CLI pinned
  in the house image, run from a space as the project role. **Decision 23** (14:58): pass 4 after Stage
  9, with Stage 10's passes 1 and 2. **The `test` project's prefix** (14:53): emptied before each deploy,
  as 2.5 wrote it. Each as recommended.
- **[Claude] `deploy-role-v0.5.0`** (`39cf834`): `boundary_name`, null by default, validated as
  `awsds-<env>-*-boundary`, names the ceiling's policy and its tag; the misuse rule keeps its one name
  per account, so a second role in an account carries no alarm. The module folder validated with
  `terraform validate` and `tflint`. The session's GitHub credential pushes the branch and refuses a tag
  (`HTTP 403` on the tag ref alone), so the user tagged and pushed it from the laptop (15:28).
- **[Claude] `sandbox/workflows/deploy-role.tf`**: `awsds-deploy-sandbox-test` on the module, with the
  policy decision 19 records, built from the lab's 158 CloudTrail events of `bundle` and
  `deploy --targets test`, and the ceiling `awsds-sandbox-deploy-test-boundary`. A provider alias on the
  deploy runner's profile reads the runner role's ARN, the trust's principal, so a plan of the slice
  takes both profiles. `terraform init` refused the module ref until the tag existed (`invalid ref:
  deploy-role-v0.5.0`); with it, `validate`, `fmt -check` and `tflint` pass.
- **[Claude] `production/foundation/`, `registry/` and `runners/`**: `deploy_targets` gains
  `other_roles`, the output `deploy_role_arns_by_name` feeds the runner's assume list and profiles,
  `deploy_role_arns` stays by account for `production/sagemaker/`; `releases.tf` holds the bucket; the
  runner role's `releases` read and the build runner's `releases` write. `terraform validate`, `fmt
  -check` and `tflint` pass on the three (provider `aws` 6.64.0 from a filesystem mirror, since the
  registry is refused to the session; the lock files restored after `-upgrade`).
- **[Claude] The hygiene scripts and `./aws/cicd.py`**: `DEPLOY_ROLES_BY_SLICE` in `backend.py`, keyed by
  account and slice, with `gen-tfvars` rendering `other_roles = ["awsds-deploy-sandbox-test"]` for the
  `sandbox` target of `production/foundation/` and `deploy_role_name` and `deploy_runner` for
  `sandbox/workflows/`; refusal 8 reading both maps; `cicd.py` listing the four roles by profile.
  `ruff format` and `ruff check` clean.
- **[Claude] The deploy image's recipe** (`gitlab/awsds/deploy-image/`): `requirements-cli.txt`, the 25
  distributions of `aws-smus-cicd-cli==1.0.9` compiled for Python 3.14 with hashes; the Dockerfile
  installing them into `/opt/smus-cli` with `--require-hashes --no-deps` and linking the command; the
  README. A proposal for the GitLab project, the source; `mirror.json` is unchanged until it is pushed.
- **[Claude] The authorization pages read**, in `docs/REFERENCES.md`: MWAA Serverless's (`workflow` the
  one resource type, `CreateWorkflow` with `aws:RequestTag`, `iam:PassedToService`) and DataZone's
  (`GetDomain` the one read with a resource type).

## 2026-10-16 — the Terraform of decisions 19 and 20 applied, from the laptop

Applied by Claude in a laptop session the user started with the procedure the cloud session wrote,
authorized by the user at 16:02, 16:45 ("deixe o ambiente no ar") and 16:47 UTC ("autorizo os
commits e applies necessários"), with the hub, Sandbox, GitLab and the VPN tunnel up by the user's
own hand (16:45); each slice a Recipe A plan read before its apply and re-planned after it, the
cloud session recording. Every time is UTC.

- **[Claude⚡] Step 0** (17:25:55 to 17:28:40): the infrastructure user's SSO session valid, with
  `InfrastructureAccess` in Production and Sandbox, no login; the worktree
  `.claude/worktrees/stage-08-2.5a` on a local branch `claude/smus-applications-rw30u1` tracking
  `origin`, at `819e830`, a branch and not the detached HEAD the procedure named, since `git pull
  --ff-only` and the push need one; the other laptop sessions told of the four writes.
- **[Claude⚡] `production/foundation/` applied as `awsds-infra-prod`** (17:28:41 to 17:32:01), with
  `-var-file=<project folder>/secrets/alerts.auto.tfvars`: `Plan: 1 to add, 1 to change, 0 to
  destroy`, as expected: `module.deploy_runner_role.aws_iam_role_policy.inline["releases"]` created
  (`ListBucket` and `GetObject` on `awsds-prod-releases`, `kms:Decrypt` under the alias
  `awsds-prod-registry` through S3), `inline["deploy"]` changed (`awsds-deploy-sandbox-test` joins
  the `AssumeRole` list, the other three entries reordered), the output `deploy_role_arns_by_name`
  new with four roles; no drift, the alerts subscription untouched. `Apply complete! Resources: 1
  added, 1 changed, 0 destroyed.` (17:31:24 to 17:31:36); re-plan `No changes`.
- **[Claude⚡] `production/registry/` applied as `awsds-infra-prod`** (17:32:20 to 17:35:23): `Plan:
  6 to add, 0 to change, 0 to destroy`, as expected, `module.releases_bucket`: the bucket
  `awsds-prod-releases` (`force_destroy = false`, `CostCenter = stage-08`), versioning `Enabled`,
  SSE `aws:kms` with the bucket key under `alias/awsds-prod-registry` (the alias's `TargetKeyId`
  read against the plan before the apply), the public access block on all four, the lifecycle
  (noncurrent versions expire in 90 days, incomplete multipart uploads are aborted after 7) and the
  bucket policy. `Apply complete! Resources: 6 added, 0 changed, 0 destroyed.` (17:33:44 to
  17:35:00, the lifecycle 58 s); re-plan `No changes`; output `releases_bucket_name =
  awsds-prod-releases`.
- **[Claude⚡] `sandbox/workflows/` applied as `awsds-infra-sandbox-1`** (17:35:44 to 17:36:51),
  after a fresh `init` that fetched `deploy_role_test` from the tag `deploy-role-v0.5.0`, whose
  `terraform-modules/deploy-role` is the branch's: `Plan: 5 to add, 0 to change, 0 to destroy`, as
  expected, `aws_iam_policy.workflows` and its attachments untouched, so the Glue grant applied at
  14:54 (policy v3) stays: the ceiling `awsds-sandbox-deploy-test-boundary`, the role
  `awsds-deploy-sandbox-test` trusting `awsds-prod-runner-deploy` alone (sid `OnlyTheDeployRunner`),
  the inline policies `project-reads`, `storage` (the `test` project's `shared/` prefix in
  `awsds-sandbox-smus-projects` and the project's key) and `workflows` (creation with the `test`
  project's tag, `PassRole` of that project's role alone to `airflow-serverless`). `Apply complete!
  Resources: 5 added, 0 changed, 0 destroyed.` (17:36:28 to 17:36:40); re-plan `No changes`.
- **[Claude⚡] `production/runners/` applied as `awsds-infra-prod`** (17:37:16 to 17:40:17), after
  the user's `make gitlab-up` of 16:45 had applied it with `main`'s code, by the commands `slices.py
  up --env production --only runners --dry-run` prints (`gen-tfvars`, `gen-backend-hcl`, `init`)
  with the plan saved and read, since `up` without `--auto-approve` waits for a typed `yes`; the hub
  read first (`awsds-prod-vpn` and `awsds-prod-proxy` running). `Plan: 2 to add, 0 to change, 1 to
  destroy`: only `aws_instance.deploy_runner[0]` replaced, its user data gaining `[profile
  awsds-deploy-sandbox-test]` with the profiles now read from `deploy_role_arns_by_name`, sorted by
  name; the build runner `awsds-prod-runner` keeps its user data and its role gains the inline
  `releases` (`PutObject` and `AbortMultipartUpload` on `awsds-prod-releases/*`, the registry key
  through S3); the test runner untouched. The procedure's "both runners' user data" was wrong: the
  PR changes `deploy-runner.tf` (reading `deploy_role_arns_by_name`) and `main.tf` (the inline
  `releases`), and the build runner's template does not change. `Apply complete! Resources: 2 added,
  0 changed, 1 destroyed.` (17:38:57 to 17:39:55), the old deploy runner instance destroyed and a
  new one created, its console read for the boot; re-plan `No changes`.
- **[Claude⚡] Step 5, `awsds/deploy-image`** (17:40:40 to 17:41:01): `main` cloned at `98a3dc7`, the
  commit of `gitlab/mirror.json`; the branch `cli-1.0.9` with `Dockerfile`, `README.md` and
  `requirements-cli.txt` copied from `gitlab/awsds/deploy-image/` (the other three files already
  identical to the copy); commit `acb73f1`, pushed without refusal; the project's pipeline runs from
  the form only, so the push started none. The user's: the merge request, the merge and Build >
  Pipelines > Run pipeline on `main` with `IMAGE_TAG=v0.2.0`; then the laptop reads the digest
  (`awsds-prod-ecr-deploy:v0.2.0`, or the job's `deploy.json: containerimage.digest` line), writes
  it to `deploy_image_digest`, applies `production/runners/` again, runs `gitlab-mirror.py` and
  commits to PR #145.
- **[Claude⚡] Step 6, `awsds/dev-env`** (17:41:30 to 17:42:31; decision 22): `main` cloned at
  `1372b47`; the branch `cli-1.0.9` with `aws-smus-cicd-cli==1.0.9` in
  `dev-env/python/pyproject.toml` and a comment citing decision 22; `uv lock` resolved 454 packages,
  the CLI the only entrant and no version changed; commit `7345733`, pushed without refusal; the
  push started the branch's pipeline with the test jobs only (`recipe-checks` and the gates of
  `gates-v0.4.0`), its result not read. The user's: that pipeline's verdict, the merge request, the
  merge and the tag; the README's rule makes a recipe change a minor, `default-v0.8.0`, the user's
  choice.

## 2026-10-16 — the new deploy runner's first boot

Written by Claude in the laptop session that applied step 2.5a (the entry above), as the
infrastructure user through `awsds-infra-prod` (`InfrastructureAccess`). Every time is UTC.

- **[Claude] `i-0cf719f584e9bdfcd`'s serial console**, read at 17:47:21 with `aws ec2
  get-console-output --latest`: cloud-init finished at 17:43:32, 226 s after boot. `docker-25.0.16`,
  `git-2.50.1`, the ECR credential helper `OK`, and `gitlab-runner-19.5.0`, where the deploy runner's
  boot of 2026-10-13 installed `19.4.1`: the three runner templates run `dnf -y -q install
  gitlab-runner` with no version, so each new instance takes the repository's newest. Each profile
  assumed once with the instance's credentials: `assumed-role/awsds-deploy-devenv-sandbox/…`,
  `assumed-role/awsds-deploy-prod/…`, `assumed-role/awsds-deploy-sandbox-test/…` and
  `assumed-role/awsds-deploy-staging/…`. `Verifying runner... is valid`, registered as
  `awsds-prod-runner-deploy-i-0cf719f584e9bdfcd`; through the proxy `pypi.org` `200` and `10.31.0.1`
  `403`, GitLab's sign-in page direct `200`; the job image pulled through the helper as
  `awsds-prod-ecr-deploy@sha256:1b1a5830…a53a`, `v0.1.0`'s digest.

## 2026-10-16 — `awsds-sandbox-outputs` retired (decision 21)

Written by Claude in the laptop session that applied step 2.5a, as the infrastructure user through
`awsds-infra-sandbox-1` (`InfrastructureAccess`). The deletion of the two versions is the user's, by
a command naming the same profile. Every time is UTC.

- **[Claude] `make status ENV=sandbox`** (17:43:07): `sandbox/app/app-etl` `down`, 0 resources, so no
  `make down` ran; `egress`, `warehouse-compute` and `probes` up.
- **[Claude] The bucket read** with `list-object-versions`: two versions and no delete marker, both
  `IsLatest` and written 2026-10-14T17:59:27Z: `app-etl/v0.1.0/trades.parquet` (1,780 bytes) and
  `app-etl/v0.1.0/trades.summary.json` (407 bytes). The bucket policy holds `DenyInsecureTransport`
  alone.
- **[Claude] `sandbox/data/` planned**, after `git pull --ff-only`, to a saved file: `Plan: 0 to add, 1
  to change, 6 to destroy`: the six resources of `module.outputs_bucket` (`force_destroy = false`)
  and the data key `awsds-sandbox-data` losing `AllowApplicationJobRolesViaS3`, its other statements
  unchanged.
- **[Claude] The deletion handed to the user** at 17:53, in this session's chat: `aws s3api
  delete-objects` on the bucket with both keys and their version ids, since Claude deletes no data
  permanently.
- **[user] The deletion's output**, pasted before 18:00:

  ```json
  {
      "Deleted": [
          {
              "Key": "app-etl/v0.1.0/trades.parquet",
              "VersionId": "algi3DIbv6NUBfebgvQFBLSJfE0V._He"
          },
          {
              "Key": "app-etl/v0.1.0/trades.summary.json",
              "VersionId": "zdwjxFYdQgdThMtjUtorpU18r5xHXEge"
          }
      ]
  }
  ```

- **[Claude] The bucket empty** at 18:00:13: `list-object-versions` returns neither `Versions` nor
  `DeleteMarkers`.
- **[Claude] `sandbox/data/` applied** from the saved plan (18:00:35 to 18:00:52): `Apply complete!
  Resources: 0 added, 1 changed, 6 destroyed.`; re-plan `No changes` (18:01:17).
- **[Claude] Read back**: `head-bucket` on `awsds-sandbox-outputs` answers `404 Not Found`; the data
  key's policy holds three statements, `EnableKeyAdministrationInThisAccount`,
  `AllowSandboxLakeAccessRoleViaS3` and `AllowRedshiftServerlessViaServiceInThisAccount`. Outside
  `sandbox/app/app-etl/`, no Terraform, script or GitLab copy names the bucket; `production/sagemaker/`'s
  `awsds-${var.env}-outputs` is `awsds-prod-outputs`.

## 2026-10-16 — the deploy image's first rebuild, failed on `.dockerignore`
Written by Claude, from the pipeline's job log read in the user's browser from the laptop, after the
user's run. Every time is UTC.

- **[user] The merge and the run**: the merge request of `cli-1.0.9` landed on
  `awsds/deploy-image`'s `main` at 18:57 (`b599b12`), and pipeline #42 was started from Build →
  Pipelines → Run pipeline on `main` with `IMAGE_TAG=v0.2.0`; its job `build-deploy-image` (#147)
  ran on the build runner.
- **[Claude] The failure** (20:38:39): the step
  `[8/9] COPY requirements-cli.txt /tmp/requirements-cli.txt` ended with
  `"/requirements-cli.txt": not found`. The project's `.dockerignore` excludes everything (`*`) and
  readmits `aws-cli-team.asc` alone, so the file the recipe gained in PR #145 (`976dae4`) never
  entered the build context: 1.76 kB transferred, the earlier layers from cache and the base through
  the pull-through cache. Nothing was pushed: `awsds-prod-ecr-deploy` holds `v0.1.0` alone, read
  after the failure, and the tag `v0.2.0` is free.
- **[Claude] Why no run caught it before the merge**: the pipeline's rule admits the `web` source
  with `IMAGE_TAG` alone, so neither the branch nor the merge built the recipe; this run was its
  first build (Lesson 54).
- **[Claude] The fix**: `!requirements-cli.txt` in `.dockerignore`, with its comment, written in the
  copy under `gitlab/awsds/deploy-image/` in PR #145, and in GitLab, the source of truth, by the
  user's own edit, who started the pipeline again with `IMAGE_TAG=v0.2.0` by 20:54; the mirror then
  reports the copy unchanged.
- **[Claude] The rebuild** (read in the user's browser): the user's edit `b064ba80` ("Edit
  .dockerignore") went straight to `main`, and pipeline #43's job `build-deploy-image` (#148) ran
  from 20:53:30 to 20:54:34, 64 s: the `COPY` passed, the venv took `aws-smus-cicd-cli==1.0.9` and
  its 24 dependencies by hash, `aws-smus-cicd-cli --help` answered in the build, and the image was
  pushed as `awsds-prod-ecr-deploy:v0.2.0`, digest
  `sha256:ee31048e743c9d05bd26bbdfdf28cca18cb834313c5c6445f754c4168c7e91ac`, 255,596,236 bytes
  against `v0.1.0`'s 208,935,352, pushed at 20:54:33 by ECR's reading. The digest step, the runner's
  re-apply and the mirror follow in the laptop session's own entry.

## 2026-10-16 — the deploy image `v0.2.0` pinned, and the runners rebuilt on a new AMI

Written by Claude in the laptop session that applied step 2.5a, as the infrastructure user through
`awsds-infra-prod` (`InfrastructureAccess`). Every time is UTC.

- **[Claude] `v0.2.0` read from ECR**: `sha256:ee31048e…7e91ac`, pushed 20:54:33, 255,596,236 bytes,
  from `awsds/deploy-image`'s `main` at `b064ba80`. Its scan, `COMPLETE` at 20:54:48: CRITICAL 0, HIGH
  4 (`glibc` CVE-2026-19499 and CVE-2026-5435, `zlib` CVE-2026-85091, `gnupg2` CVE-2026-24882), MEDIUM
  10, LOW 4; no finding names `curl`. The pull-through cache's `python:3.14-slim` is still
  `sha256:a2b82f3c…9170`.
- **[Claude] `deploy_image_digest`** set to it in `production/runners/variables.tf`, commit `a99721b`.
- **[Claude] No deploy job could be waiting**: `git ls-remote --tags` reads `awsds/dev-env`'s newest tag
  as `default-v0.7.3` and `awsds/app-etl`'s as `v0.1.0`, both older than the day.
- **[Claude] `production/runners/` planned** (20:58:51) to a saved file: `Plan: 3 to add, 0 to change, 3
  to destroy`, where the deploy runner alone was expected. Each of `aws_instance.deploy_runner[0]`,
  `aws_instance.runner` and `aws_instance.test_runner` reads `ami = (sensitive value) # forces
  replacement`, and the deploy runner's `DEPLOY_IMAGE` moves to the new digest. The three take `ami`
  from `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64`, which changed at
  20:01:25 (version 194) to `ami-0803a33fd43db1fbf`; all three ran `ami-042bfcefcf88b2ac8` (Amazon
  Linux 2023.12.20261014), and step 2.5a's plan at 17:37 touched neither the build nor the test
  runner. Held until the user's decision.
- **[Claude] The test runner's boot of 16:36, read through its serial console**: `i-018f82308a703b5fa`
  stopped at "the CA root, from its one source" with `aws: [ERROR]: An error occurred (NoCredentials):
  Unable to locate credentials.` at 16:36:29, and `cloud-final` `FAILED`, so runner #4 never
  registered. Its role and instance profile came from the same `make gitlab-up`, created
  16:36:01-02 by another session's reading, and the templates read the root once, with no retry.
- **[user] The apply**, authorized in this session's chat: "Aplique o plano salvo de
  production/runners, com os três runners substituídos, e leia os três boots."
- **[Claude] Applied** from the saved plan (21:07:45 to 21:08:47): `Apply complete! Resources: 3 added,
  0 changed, 3 destroyed.`, each destruction 32 s and each creation 15 s: `i-0f053b2cd9bdf492e` (build),
  `i-0cc9c1b95621c5be2` (deploy), `i-00c29f8ea8e6265c4` (test), all on `ami-0803a33fd43db1fbf`, launched
  21:08:32. Re-plan `No changes` (21:09:14).
- **[Claude] The three first boots, read through the serial console**, each on Amazon Linux
  2023.12.20261016 with `docker-25.0.16`, `git-2.50.1` and `gitlab-runner-19.5.0`:
  - the build runner, 21:08:41 to 21:10:24 (107.5 s): the credential helper `OK`, `Verifying
    runner... is valid`, registered as `awsds-prod-runner-i-0f053b2cd9bdf492e`; through the proxy
    `pypi.org` `200` and `10.31.0.1` `403`, GitLab direct `200`.
  - the test runner, 21:08:46 to 21:12:09 (209.6 s): the CA root read with no error, `Verifying
    runner... is valid`, registered as `awsds-prod-runner-test-i-00c29f8ea8e6265c4`; `200`, `403`,
    `200`.
  - the deploy runner, 21:08:49 to 21:12:56 (255.5 s): the four deploy roles assumed with the
    instance's credentials (`awsds-deploy-devenv-sandbox`, `awsds-deploy-prod`,
    `awsds-deploy-sandbox-test`, `awsds-deploy-staging`), `Verifying runner... is valid`, registered as
    `awsds-prod-runner-deploy-i-0cc9c1b95621c5be2`; `200`, `403`, `200`; the job image pulled through
    the helper as `awsds-prod-ecr-deploy@sha256:ee31048e…7e91ac`, `v0.2.0`.
- **[Claude] The mirror**, `./scripts/gitlab-mirror.py`: `awsds/dev-env`'s copy already held `1372b47`;
  `awsds/deploy-image` copied at `b064ba80`, one file changed, `.dockerignore`, whose GitLab version
  ends with no newline. Commit `9eb1406`.

## 2026-10-16 — the `v0.2.0` release row, and `mcp` held to 1.30.0 in the house environment

Written by Claude in the laptop session that applied step 2.5a; both pushes go to the private GitLab
over HTTPS with the laptop's credential helper, each on the user's request in that session's chat.
Every time is UTC.

- **[Claude] `awsds/deploy-image` branch `the-releases-v0.2.0`**, commit `05e10a5` (21:11) on `main`'s
  `b064ba80`, pushed on the user's request: the `v0.2.0` row of the README's releases table, from the
  previous entry's ECR readings and pipeline #43's job (64 s). The merge request and the merge are the
  user's.
- **[Claude] `awsds/dev-env` pipeline #41's `pip-audit`**, run again at 21:15 on the new test runner
  (read by another session): 453 of 453 packages audited, blocked on `mcp` 2.1.1, CVE-2026-59951
  (GHSA-84m7-p3x7-pcfv), published 2026-10-15, GitHub severity `MODERATE`, unbounded session
  accumulation in the StreamableHTTP transport. OSV lists two fixed releases, 1.30.0 on the 1.x line
  and 2.2.0 on the 2.x line.
- **[Claude] Why 2.2.0 cannot resolve**: `uv lock --upgrade-package mcp`, with and without
  `--refresh-package mcp`, reads `No lockfile changes detected`. PyPI's metadata for `strands-agents`
  gives `mcp<2.2,>=1.23.0` in 1.55.1, the locked version, and in 1.61.1, the newest (2026-10-15).
  PyPI holds `mcp` 1.30.0 (2026-09-07), 2.2.0 (2026-09-07) and 2.3.0 (2026-10-02).
- **[Claude] The 1.x bound tested** with `uv lock --dry-run` and the edit reverted: 455 packages,
  `mcp` 2.1.1 → 1.30.0, `mcp-types` removed, `httpx-sse` 0.4.3 and `pydantic-settings` 2.16.0 added.
- **[user] The choice**, in this session's chat: "Restrinja o mcp a >=1.30.0,<2 no
  dev-env/python/pyproject.toml do branch cli-1.0.9, refaça o lock e empurre."
- **[Claude] `cli-1.0.9` commit `386fd52`** (21:25), pushed over `7345733`: `"mcp>=1.30.0,<2"` with its
  reason in the comment, and `uv lock` with the same four changes and no other version moved. The
  push starts the branch's pipeline; its verdict is not read here.
- **[user] The merges**: `the-releases-v0.2.0` into `awsds/deploy-image`'s `main` at 21:28:08
  (`7bf9acf`), and `cli-1.0.9` into `awsds/dev-env`'s `main` at 21:28:34 (`7c59998`, merge request !7),
  after the branch's pipeline #44 passed, as another session read it.
- **[Claude] The copies** (21:30): `./scripts/gitlab-mirror.py` changed `dev-env/python/pyproject.toml`
  and `uv.lock` in `gitlab/awsds/dev-env/` and `README.md` in `gitlab/awsds/deploy-image/`, and
  `mirror.json` records both commits; commit `1d63588`. `./scripts/check-gitlab-mirror.py` failed
  `GM-3` first, since `sandbox/egress`'s state held no `no_proxy_all_groups` (the slice down); with
  `--plan`, `GM-1` to `GM-8` pass, the literal and the account's list both 70 names, `sha256
  aafa08da98a61f5c`. No tag `default-v0.8.0` exists yet.

## 2026-10-16 — the release `default-v0.8.0`: Sandbox's image version 9

- **[user] The tag** `default-v0.8.0` on `awsds/dev-env`'s `main` `7c59998`, created in GitLab at
  21:39, the user's word in the thread: "Criei a tag `default-v0.8.0` no repositório `dev-env`.
  Pipeline está em execução." It starts release pipeline #46 (test, build, verify, release,
  register).
- **[Claude] The build**, read in GitLab and ECR by another session: `build-images` 955 s on the
  rebuilt build runner, its BuildKit cache gone with the instance; the smoke green (trust, runtimes,
  imports, manifests); the images tagged `default-v0.8.0-7c59998c`: `base` 3,745,649,519 bytes
  (`sha256:681dcb20…f23e`), `dev-env` 6,678,573,838 bytes (`sha256:b788dbd9…1b87`), 4.1 MB under
  `v0.7.3`'s.
- **[Claude] The manifests against `v0.7.3`'s**: the house Python gains `aws-smus-cicd-cli` 1.0.9,
  `httpx-sse` 0.4.3 and `pydantic-settings` 2.16.0, moves `mcp` from 2.1.1 to 1.30.0 and loses
  `mcp-types` (452 to 454 packages); `runtimes` changes in the base's digest alone; imports, Julia,
  R, conda, trust and the proxy list identical.
- **[Claude] The scans**: both CRITICAL 113 and HIGH 610, the 593 past the baseline every one
  `linux-libc-dev`, as in `v0.7.1` and `v0.7.3`; nothing new. Both jobs fail, since they inform and
  never block (decision 1 amended), and the pipeline shows `Warning`.
- **[user] The gate**: `release-gate` run at 22:02:51 with the scans red, the user's word in the
  thread: "O `scan-base` e `scan-dev-env` falhou. Mas aprovei o gate de release mesmo assim."
- **[Claude] `register`**, read in Sandbox by another session: version 9 of `awsds-sandbox-dev-env`
  created at 22:03:16, alias `0.8.0`, `ContainerImage` the pushed digest, no write on the domain;
  `retire` kept versions 9, 8 and 7. The README's `v0.8.0` row and the mirror follow.

## 2026-10-16 — the runners' boot hardened, and decisions 24 and 25 taken

Written by Claude in the laptop session of PR #147, as the infrastructure user through `awsds-infra-prod`
(`InfrastructureAccess`), reads only; nothing applied. Every time is UTC.

- **[Claude] The AMI parameter read** (between 21:22 and 21:34): the runners' parameter,
  `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64`, at version 194,
  `ami-0803a33fd43db1fbf`, modified 20:01:25. `get-parameter-history` on it is refused
  (`AccessDeniedException: Cannot access/update data for the restricted parameter`), and `get-parameter`
  with the selectors `:193` and `:194` answers `ParameterVersionNotFound`. `describe-images` (owner
  `amazon`): 8 AL2023 releases in the 30 days to 2026-10-16, 4 of them in October; `ami-042bfcefcf88b2ac8`
  and `ami-0803a33fd43db1fbf` each carry a `DeprecationTime` 90 days after their `CreationDate`.
- **[Claude] `production/runners/` planned, read-only**: on PR #145's head, `No changes` (21:27:14); with
  the hardening (`dbd5dbc`), `Plan: 3 to add, 0 to change, 3 to destroy` (21:41:59), each instance's
  `replace_paths` `user_data` alone and its AMI `ami-0803a33fd43db1fbf` before and after; after `main`
  merged in with #145 (`66f0b1e`), the same at 22:18:02.
- **[user] Decisions 24 and 25** (by 22:21, in this session's chat): "Aceito as decisões 24 e 25 como
  recomendadas. Registre no arquivo da etapa 8." `gitlab-runner` pinned at 19.4.1, and each runner's AMI
  held by `ignore_changes`. The apply stays the user's.

## 2026-10-16 — the `default-v0.8.0` release row, copied back

Written by Claude in the laptop session that applied step 2.5a, the reads as the infrastructure user
through `awsds-infra-prod` and `awsds-infra-sandbox-1` (`InfrastructureAccess`), the push to the private
GitLab over HTTPS with the laptop's credential helper on the user's request. Every time is UTC.

- **[Claude] The row's figures read back** before the push: ECR's `default-v0.8.0-7c59998c` in
  `awsds-prod-ecr-base` (`sha256:681dcb20…f23e`, 3,745,649,519 bytes, pushed 21:43:56) and in
  `awsds-prod-ecr-dev-env` (`sha256:b788dbd9…1b87`, 6,678,573,838 bytes, pushed 21:54:54), both scans
  `COMPLETE` at CRITICAL 113, HIGH 610, MEDIUM 158, LOW 16, UNDEFINED 436; Sandbox's
  `awsds-sandbox-dev-env` version 9 `CREATED` at 22:03:16 on the `dev-env` digest, alias `0.8.0`, beside
  versions 8 and 7. The build time, the pipeline and the manifests' changes come from another session's
  reading of the jobs.
- **[Claude] `awsds/dev-env` branch `the-releases-v0.8.0`**, commit `dff50f4` (22:30) on `main`'s
  `7c59998`: the `default-v0.8.0` row of the README's releases table.
- **[user] The merge** at 22:41:51 (`5d5391a`).
- **[Claude] The copy**: `./scripts/gitlab-mirror.py` changed `README.md` in `gitlab/awsds/dev-env/` and
  `mirror.json`; `awsds/deploy-image`'s copy already held `7bf9acf`.

## 2026-10-16 — the 22:26 apply of `production/runners/`, and the hardened runners' first boots (verification xxvii)

Written by Claude in the laptop session that applied step 2.5a, by the user's word that this session
records the 22:26 apply and verification xxvii, as the infrastructure user through `awsds-infra-prod`
(`InfrastructureAccess`), reads only. Every time is UTC.

- **[user] `make gitlab-up`** after PR #147 reached `main`: the three runners recreated, launched 22:26:05
  on `ami-0803a33fd43db1fbf`: `i-0e2329501161e2feb` (build), `i-08a2443adfe11fa0d` (test) and
  `i-069d264f327b93700` (deploy). The apply's output was not pasted.
- **[Claude] The apply in CloudTrail** (Production, `us-west-2`): `TerminateInstances` at 22:25:33-34 on
  `i-0f053b2cd9bdf492e`, `i-0cc9c1b95621c5be2` and `i-00c29f8ea8e6265c4`, the runners of 21:08, and three
  `RunInstances` at 22:26:05: the build runner `m8i.xlarge` with a 64 GiB `gp3` root, the deploy and test
  runners `t3a.small`, each on `ami-0803a33fd43db1fbf`, the test runner's metadata hop limit 1 against
  the others' 2. Every event by the infrastructure user's `InfrastructureAccess` session (created
  22:25:31) with Terraform 1.15.8 and provider `aws` 6.68.0 as its user agent.
- **[Claude] Their first boots, read through the serial console** by 23:08, each on Amazon Linux
  2023.12.20261016: the build runner 22:26:14 to 22:27:57 (107.2 s), the test runner 22:26:20 to
  22:29:44 (211.8 s), the deploy runner 22:26:25 to 22:30:15 (240.2 s). Each passed "the CA root, from its
  one source, once the instance's role answers" on its first read, with no `not yet` line and no
  `FATAL`; `rpm -q` printed `gitlab-runner-19.4.1-1.x86_64` and
  `gitlab-runner-helper-images-19.4.1-1.noarch`; `Verifying runner... is valid`, registered as
  `awsds-prod-runner-i-0e2329501161e2feb`, `awsds-prod-runner-test-i-08a2443adfe11fa0d` and
  `awsds-prod-runner-deploy-i-069d264f327b93700`; through the proxy `pypi.org` `200` and `10.31.0.1`
  `403`, GitLab direct `200`. The test runner printed `no token from a container: the jobs hold no AWS
  identity`. The deploy runner assumed its four deploy roles and pulled the job image as
  `awsds-prod-ecr-deploy@sha256:ee31048e…7e91ac`, `v0.2.0`.
- **[Claude] Verification xxvii, the boot half**: each runner read the root, installed 19.4.1-1 with its
  helper images and registered. The retry was not exercised: the three roles predate their hosts, so no
  read failed and no `not yet` line printed; only an apply that creates a role and its host together,
  as at 16:36, reaches it. The plan half waits on the next Amazon Linux release.

## 2026-10-16 — `devenv.py` on version 9

- **[user] `./aws/devenv.py`**, run from the project folder on `main` (`a5862bd`) with Sandbox down,
  the user's paste in the thread at 23:04: "region: us-west-2 / awsds-infra-sandbox-1 OK / wrote
  aws/output/devenv.txt checks: 5 passed or noted, 1 FAILED".
- **[Claude] The report**, read on the laptop: `DE-5` green, version 9's `ContainerImage`
  (`sha256:b788dbd9…1b87`) baking the 70 names, sha256 `aafa08da98a61f5c`; `DE-1` and `DE-4` green;
  `DE-2` FAILED because `sandbox/egress` is down and its state holds neither output, the absence the
  check itself names, with `DE-3` and `DE-6` noted as not compared. The exit 2 reads the
  environment's state, not the image's; the two comparisons wait for a `make up ENV=sandbox`.

## 2026-10-18 — readings with the environment down, and the next `NO_PROXY` literal

Written by Claude, session "Stage 8: readings, NO_PROXY proposal, text fixes", as the infrastructure
user through `awsds-infra-prod`, `awsds-infra-sandbox-1`, `awsds-infra-staging`, `awsds-infra-data`
and `awsds-infra-identity` (`InfrastructureAccess`), reads and plans only; nothing applied. The whole
environment was down (`make status` 0.0000 USD/h, read by the orchestrating session). Every time is UTC.

- **[Claude] `./aws/cicd.py`** (19:48:13 to 19:48:52): exit 1 on every profile, from the seven persona
  and Control Tower profiles with no SSO token; on the three infrastructure profiles (19:49:08 to
  19:49:40) exit 0, 11 pass, 5 notes, 0 FAILED. `CI-2` passes `awsds-deploy-sandbox-test` with
  `awsds-sandbox-deploy-test-boundary`, `CI-3` reads every principal `awsds-prod-runner-deploy` and
  `sts:AssumeRole` only, `CI-8` 54 assumptions, every caller the deploy runner; `CI-1` and `CI-9` note
  both runners absent, `CI-6` version 9's `sha256:b788dbd9…1b87`.
- **[Claude] The policy simulator on `awsds-deploy-sandbox-test`** (19:50:41 to 19:51:33), with
  `aws:RequestedRegion`, `aws:PrincipalOrgID` and `aws:ResourceOrgID` as context, each call asked for
  the `test` project (`4gqfau9xuo6e4w`) and for the `dev` project (`avhvbqn37ty7m8`):

  | Calls | `test` | `dev` |
  |---|---|---|
  | `airflow-serverless:` `StartWorkflowRun`, `UpdateWorkflow`, `GetWorkflow`, `GetWorkflowRun`, `ListWorkflowRuns`, `TagResource`, by `aws:ResourceTag/AmazonDataZoneProject`; `CreateWorkflow` by `aws:RequestTag/AmazonDataZoneProject` | allowed, `workflows` | implicitDeny |
  | `s3:GetObject`, `PutObject`, `DeleteObject` under `<domain>/<project>/shared/`; `s3:ListBucket` with that `s3:prefix` | allowed, `storage` | implicitDeny |
  | `iam:PassRole` of the project's role to `airflow-serverless.amazonaws.com` | allowed, `workflows` | explicitDeny, `awsds-sandbox-deploy-test-boundary` |
  | `logs:CreateLogGroup`, `FilterLogEvents` on `/aws/mwaa-serverless/<domain>-<project>/*` | allowed, `workflows` | implicitDeny |

  `DeleteWorkflow` on a `test` workflow reads `explicitDeny` from the same ceiling; `TagResource` and
  `UpdateWorkflow` on a `test` workflow with the `dev` id as request tag, `CreateWorkflow` with no request
  tag and `StartWorkflowRun` with no resource tag read `implicitDeny`. `AllowedByOrganizations` is true
  on every row.
- **[Claude] What the role has called, in Sandbox's CloudTrail**: `lookup-events` by `ResourceName`,
  with the role's name or its ARN, returned nothing since 2026-10-16, while the `AssumeRole` events name
  the role in their resources; filtering `AssumeRole` from 2026-10-16T17:00Z to 2026-10-18T20:00Z found
  three, at 17:43:14, 21:12:32 and 22:29:51 on 2026-10-16, each by the deploy runner's role from the
  boots of `i-0cf719f584e9bdfcd`, `i-0cc9c1b95621c5be2` and `i-069d264f327b93700`. Looked up by its
  access key, each session made one call, `GetCallerIdentity`, in the second of its assumption. The
  role has run no deploy.
- **[Claude] Verification vii's third half**, after 6d's reading of 2026-10-17: in Sandbox, one
  `UpdateStack` since 2026-10-11, `DataZone-Env-5hkjdsy3umpi1c` at 22:05:48 that day by
  `awsds-sandbox-smus-provisioning`, invoked by `datazone.amazonaws.com`. Ten `UpdateDomain` events since
  2026-10-11 (19:52:44), every one the infrastructure user's through `aws-cli/2.37.12`, the last on
  `d-lfgbdrjncmsu` at 2026-10-16 00:31:25; none invoked by a service and none after. Before the
  reconciliation, the first domain's last write was 2026-10-10 20:51:38, naming
  `awsds-sandbox-dev-env:5`. Both domains' `CustomImages` name `awsds-sandbox-dev-env` on JupyterLab and
  Code Editor with no `ImageVersionNumber`, `LastModifiedTime` 2026-10-15 06:14:06 and 2026-10-16
  00:31:26.
- **[Claude] Decision 19's premise**, the membership (19:53:39 to 19:53:45): `datazone
  list-project-memberships` and `list-connections` answer `InfrastructureAccess` from Sandbox on both
  projects; `dev` holds 11 connections, `redshift-serverless.redshift` among them, and `test` 9. Each
  project's members: one SSO user as `PROJECT_OWNER`, the same in both; the project's own role, an IAM
  user profile, as `PROJECT_CONTRIBUTOR`; and the group profile `839bcde8-f8b8-4ada-936a-1441352db302`
  as `PROJECT_CONTRIBUTOR` in both. `get-group-profile` is refused from Sandbox ("no resource-based
  policy allows the datazone:GetGroupProfile action") and answers from Data Governance: `ASSIGNED`,
  `rolePrincipalArn` Sandbox's `AWSReservedSSO_InfrastructureAccess_59e5b26af457128d`. Data Governance's
  CloudTrail holds two `CreateProjectMembership` for that group, `PROJECT_CONTRIBUTOR`, on 2026-10-15 at
  06:15:15 (`4gqfau9xuo6e4w`) and 06:15:45 (`avhvbqn37ty7m8`), by `awsds-data-studio-domain-execution`
  with a browser's user agent, and no `CreateGroupProfile` since 2026-09-01. `awsds-deploy-sandbox-test`
  is no member.
- **[Claude] Validation 2, `./aws/egress.py`** on the five infrastructure profiles (19:54:53 to
  19:55:42): exit 0; section 6 reads 0 interface endpoints, 0 NAT gateways and 0.000 USD/h in every
  account; `EG-1` and `EG-4` pass on the gateway endpoints, `EG-5` notes no metered egress.
- **[Claude] Refusal 8, dry** (19:56:50 to 19:57:12): `scripts/slices.py` runs every command through
  `run()`, which prints and returns under `--dry-run`, the reads included. `make up ENV=sandbox
  ONLY=dev-env PROFILE=awsds-deploy-devenv-sandbox DRY=1` and `ONLY=workflows
  PROFILE=awsds-deploy-sandbox-test` refuse both slices by refusal 1, `[P]`, and apply nothing; `make up
  ENV=sandbox PROFILE=awsds-deploy-sandbox-test DRY=1` and `make down ENV=sandbox
  PROFILE=awsds-deploy-devenv-sandbox DRY=1` refuse `egress`, `warehouse-compute` and `probes` by
  refusal 8, and the nine others by 1 and 4; `make up ENV=staging ONLY=egress
  PROFILE=awsds-deploy-staging DRY=1` prints `staging/egress/`'s generators, `init` and `apply` as that
  profile. The hub check, its reads printed and not run, says "NOT READ - no session on the hub
  account". The simulator (19:57:36 to 19:57:48) reads both Sandbox deploy roles `implicitDeny` on
  `s3:GetObject` and `PutObject` of `sandbox/dev-env/` and `sandbox/workflows/` state in
  `awsds-sandbox-tfstate`, on `s3:ListBucket` with either prefix, and on `kms:Decrypt` with
  `alias/awsds-sandbox-tfstate`'s key.
- **[Claude] The next `NO_PROXY` literal**: `./scripts/check-gitlab-mirror.py --plan` (19:58:12 to
  19:58:33), a plan of `sandbox/egress` on `vpc-egress-v0.18.0` with `-refresh=false`, exit 2:

  ```
    only in the account : .mlflow.sagemaker.us-west-2.app.aws
    only in the account : mlflow.sagemaker.us-west-2.app.aws
  fail    GM-4  the literal is the account's list          2 name(s) only in the account, 0 only in the image
  pass    GM-2  the Dockerfile declares one NO_PROXY_LIST  70 entries, sha256 aafa08da98a61f5c
  pass    GM-3  the account's list is readable             72 entries, sha256 6faf2e4761622508, from a plan of terraform-live/sandbox/egress
  ```

  The written line replaced `ARG NO_PROXY_LIST` in `gitlab/awsds/dev-env/dev-env/Dockerfile`, its
  comment dated, two names added and none removed; the second run (19:59:39 to 19:59:55) exit 0, `GM-1`
  to `GM-8` pass, `GM-4` 72 names, `6faf2e4761622508` on both sides. A proposal: GitLab holds 70 until
  the user's merge request.
- **[Claude] Verification xiv**, offline: `awsds-workflows` at `3c1708e` (2026-10-16 13:39, "O lint de
  uma aplicação da CLI de CI/CD (#21)"), installed from its archive into a scratch virtual environment,
  the user's own tool untouched; `main`'s head, `d2b33ca`, changes documents only. Over scratch copies of
  `examples/app-etl/`, which itself reads `ok: 6 arquivo(s)`, 40 deliberate violations each exit 1 under
  their rule: `projeto` 8, `datas` 3, `operador` 2, `limites` 4, `imagem` 2, `job` 5, `templates` 2,
  `codigo` 1, `glue` 2 and `manifest` 8 in the authoring mode, and in the promoted mode `projeto` on a
  rendered copy left with CLI variables and on one with a `datazone-<project>-dev` prefix, and `job` on
  one without its volume key. A dev-env image by digest passes without `--image-repository`, a job with
  no volume key passes outside the promoted mode, and a clean rendered copy passes the promoted mode. No
  rule reads a `VersionId` or a release's manifest.

## 2026-10-18 — the lint's options, the mirror's readers and members, and the runners' echo

*Provenance. Claude, in the side session of the orchestrating session that carries the cross-stage fixes
(worktree `plan-propagation-1018-6f9a01`, at `origin/main` `46abfcf`), with the whole environment down. The
AWS calls were reads as the infrastructure user with `InfrastructureAccess`, `awsds-infra-data` in
`Data Governance` and `awsds-infra-prod` in `Production`; nothing applied. No quoted line carries an
account id or an e-mail address, and the group profile's role is named by its permission set. Times are
UTC.*

- **[Claude] The lint's options, offline.** `awsds-workflows` at `3c1708e` extracted with `git archive`
  from the user's checkout into the scratchpad, its `lint_application` and `lint_definition` called from
  a script run by the interpreter of the `checkov` tool, which carries PyYAML and `packaging`; the user's
  installed tool, at `c9a4c20`, has no `lint` and answers `invalid choice: 'lint'`, and was not touched.
  26 readings over scratch copies of `examples/app-etl/` with one edit each and over single definitions
  rendered by hand, each as expected:

  | Reading | Authoring, as `lint .` runs it | With the option |
  |---|---|---|
  | `examples/app-etl/` unmodified | no finding | |
  | a literal `dev-env` image by digest | no finding | `imagem` under `image_repository` |
  | a literal image by tag | `imagem` | |
  | an `InstanceType` outside any list | no finding | `job` under `instance_types` |
  | no `VolumeKmsKeyId` | no finding | `job` in the promoted mode |
  | a training operator with isolation off | no finding | the processing operator reads `job` |
  | a `schedule` on the DAG; a `retry_delay` of 600 | `datas`; `limites` | |
  | a code input outside the manifest's folders | `codigo` | |
  | `task_instance` in a template; `dag_run` | no finding; `templates` | |
  | a placeholder as `ImageUri` | no finding | `imagem` and `projeto` in the promoted mode |
  | an `AmazonDataZoneProject` tag; a code input outside `--prefix` | no finding | `projeto`; `codigo`, in the promoted mode |

  A rendered copy of `app-etl`'s workflow with its CLI variables filled and nothing else is refused by
  the promoted mode three times, `projeto`: the project tag, a `datazone-glue-network-connection-` name
  and the `datazone-<project>-dev` log-group prefix. The command's code refuses `lint <folder> --promoted`:
  the mode takes one rendered file and `--prefix`. No pipeline file in the repository passes `--promoted`,
  `--image-repository` or `--instance-type`.
- **[Claude] The infrastructure mirror's readers.** `grep -rn 'CI_JOB_TOKEN\|awsds/infrastructure\|git
  clone' gitlab/ examples/app-etl ci-gates` finds one remark, in
  `gitlab/awsds/dev-env/base/ca-certificates/README.md`, about a clone from a notebook, and no job.
  Decision 2 holds open whether pass 4's promotion jobs read the mirror or it is retired.
- **[Claude] The Sandbox projects' members** (`datazone list-project-memberships` and `get-group-profile`
  as `awsds-infra-data`, about 21:07): `test-experimentation` and `eighth-experimentation` each list a
  project owner (a user), a contributor (a user) and a contributor group profile, the same in both and
  `ASSIGNED`, whose role principal is Sandbox's `AWSReservedSSO_InfrastructureAccess` role. No project lists
  `awsds-deploy-sandbox-test`. INT-25 carries the reading.
- **[Claude] `production/runners`**, `./scripts/gen-backend-hcl.py`, `./scripts/gen-tfvars.py`, `init` and
  `plan -input=false` as `awsds-infra-prod`: `Plan: 10 to add, 0 to change, 0 to destroy`, the two roles,
  their policies and the two instance profiles, then `Error: Unsupported attribute` at `main.tf` line 38,
  `data.terraform_remote_state.egress.outputs.no_proxy`: `production/egress/` is down and its state holds
  no outputs, so the three instances and their user data are not planned. The user data is read by
  rendering the three templates with `templatefile()` and dummy values, before and after: one line
  differs in each, the echo `a started host answers two to three minutes after its start` now `up to 60
  tries, ten seconds apart`. The one timed start bounds a start at 3 min 36 s (Stage 7's log). Nothing
  applied; the text reaches a host at the next `make gitlab-up`.
- **[Claude] `scripts/slices.py`, the hub check under `--dry-run`.** `make up ENV=sandbox DRY=1` printed
  `UNREADABLE` for the two hub hosts and `NOT READ - no session on the hub account` (the entry above
  quotes that wording), though the reads were printed and none ran. It prints `not run (--dry-run)` and
  `--dry-run printed the reads above and ran none, so this refusal is not evaluated`. Every branch of
  `refuse_if_hub_down` exercised with stubbed reads: a dry run, a failed read (the old wording), both
  hosts running, the proxy stopped and the proxy absent (refused), the tunnel stopped (proceeds), and
  `make hub-up` itself (skipped).

## 2026-10-18 — `staging/probes/` retired, the lint's two ceilings, and verification xxi's simulator half

*Provenance. Claude, in a side session of the orchestrating session (worktree `agent-a00b8f159703aa2af`,
branch `claude/stage-08-probes-lint` from `origin/main` `28f340c`), with the whole environment down. The
AWS calls were reads as the infrastructure user with `InfrastructureAccess`: `awsds-infra-staging` in
`Staging`, `awsds-infra-prod` in `Production` and `awsds-infra-sandbox-1` in `Sandbox Account 1`;
nothing applied and nothing written in AWS. Roles are named by their permission set, and no quoted line
carries an account id or an e-mail address. Times are UTC.*

- **[Claude] The Staging state bucket** (22:21:04). `aws s3 ls s3://awsds-staging-tfstate/ --recursive`
  lists two objects, `staging/bootstrap/terraform.tfstate` and `staging/foundation/terraform.tfstate`;
  `list-object-versions` with the prefix `staging/probes` returns no version and no delete marker, and
  over the whole bucket the other keys are those two objects' lock files and
  `staging/egress/terraform.tfstate.tflock`, lock versions of 2026-09-06 and 2026-09-09 with no state
  object beside them. `staging/probes/` never held a state here, so step 3.1 retired it as code
  alone: `make up ENV=staging DRY=1` listed `ephemeral [E] (2)`, `staging/egress` and `staging/probes`,
  before the folder left, and `ephemeral [E] (1)`, `staging/egress`, after (22:36:17); `make down
  ENV=staging DRY=1` the same.
- **[Claude] `./aws/devenv.py`** as `awsds-infra-sandbox-1` (22:31:42 to 22:31:49): exit 2, 4 passed or
  noted, 2 FAILED:

  ```
  fail    DE-2  the account's list is readable                      the state holds neither `no_proxy_all_groups` nor `no_proxy`: the slice is DOWN (an [E] destroy leaves the object and removes the outputs). `make up ENV=sandbox` first - the comparison below is not a divergence, it is an absence
  fail    DE-5  the registered image carries the account's list     version 9 (sha256 aafa08da98a61f5c) against the Dockerfile's (sha256 6faf2e4761622508): 2 name(s) the image lacks, 0 it has and should not - DE-3 may pass while the domain serves this
  pass    DE-1  the Dockerfile declares one NO_PROXY_LIST           72 entries, sha256 6faf2e4761622508
  ```

  With `sandbox/egress` down, `DE-5` compares version 9 with the 72 names of the copy under `gitlab/`,
  so it reads red with the environment down as well as up.
- **[Claude] The lint's two ceilings, offline.** `awsds-workflows` at `3c1708e` extracted with `git
  archive` from the user's checkout into the scratchpad and run by `uvx` with `UV_OFFLINE=1` from that
  source, built from uv's cache; the user's installed tool not touched. `--image-repository` takes one
  repository, compared with the repository of a literal `ImageUri` that is an ECR URI by digest, a
  placeholder passing in the authoring mode; `--instance-type` repeats, and a
  `SageMakerProcessingOperator`'s `ProcessingResources.ClusterConfig.InstanceType` must be one of the
  values. `examples/app-etl/.gitlab-ci.yml`'s `test` job gained `--image-repository "$IMAGE_REPO"` and
  one `--instance-type` per name of `LINT_INSTANCE_TYPES`, the seven of `terraform-modules/sagemaker-denies`'
  `allowed_instance_types` at `sagemaker-denies-v0.2.0`, the list the `Workloads` SCP carries. The job's
  last script item, read from the file and run with bash over scratch copies of `examples/app-etl/`
  (22:37:13 to 22:37:14):

  | Copy | The job's line | `lint .` |
  |---|---|---|
  | the example | exit 0, `ok: 6 arquivo(s)` | exit 0 |
  | `InstanceType: ml.m5.2xlarge` | exit 1, `job: task process: InstanceType ml.m5.2xlarge fora de ml.t3.medium, ml.t3.large, ml.t3.xlarge, ml.m5.large, ml.m5.xlarge, ml.c5.large, ml.c5.xlarge` | exit 0 |
  | `InstanceType: ml.g5.xlarge` | exit 1, `job` | — |
  | a literal `awsds-prod-ecr-dev-env` image by digest | exit 1, `imagem: task process: ImageUri do repositório awsds-prod-ecr-dev-env, e não de awsds-prod-ecr-app-etl` | exit 0 |
  | a literal `awsds-prod-ecr-app-etl` image by digest | exit 0 | — |
  | the example, `LINT_INSTANCE_TYPES` unset | exit 1, `LINT_INSTANCE_TYPES: unbound variable` | — |

  Nothing was pushed to GitLab: `awsds/app-etl` runs `lint .` until the user pushes the file.
- **[Claude] Verification xxi's simulator half** (22:30:47 to 22:30:52). `iam simulate-principal-policy`
  on `s3://awsds-prod-releases/app-etl/v0.0.0/app-etl.zip`, with the bucket's live policy from
  `get-bucket-policy` as the resource policy (two statements, `DenyInsecureTransport` and
  `DenyDeletesExceptInfrastructure`), the context `aws:PrincipalArn` (the simulated role),
  `aws:RequestedRegion`, `aws:SecureTransport` true, `aws:PrincipalOrgID` and `aws:ResourceOrgID`, and a
  simulated IAM user as the caller a resource policy requires:

  | Principal | Calls | Decision | Matched |
  |---|---|---|---|
  | Production's `AWSPowerUserAccess` role, `PowerUserAccess` attached | `s3:DeleteObject`, `s3:DeleteObjectVersion` | `explicitDeny` | the resource policy's second statement, `DenyDeletesExceptInfrastructure` |
  | Production's `InfrastructureAccess` role | the same | `allowed` | `AdministratorAccess` |
  | Sandbox's `InfrastructureAccess` role, Production the resource owner | `s3:GetObject`; `s3:ListBucket` on the bucket | `implicitDeny` | none: the resource policy `implicitDeny`, the identity policy `allowed` |
  | `awsds-deploy-sandbox-test`, Production the resource owner | `s3:GetObject` | `implicitDeny` | none: both policies `implicitDeny`, its boundary `allowed` |
  | Sandbox's `InfrastructureAccess` role, Sandbox the resource owner | `s3:GetObject` | `allowed` | `AdministratorAccess` |
  | `awsds-prod-runner-deploy` | `s3:GetObject` | `allowed` | its inline `releases` |

  `AllowedByOrganizations` is true on every row. The `InfrastructureAccess` contrast reads `allowed` only
  if the simulator took `aws:PrincipalArn` from the context rather than from the simulated user, so the
  delete refusal is the deny's condition; the two Sandbox rows put the read refusal on the account
  boundary. The simulator evaluates no key policy. The attempt half and the `If-None-Match` half stay
  owed.

## 2026-10-19 — 3.0's first half, Staging's pull grant, applied in Stage 18's window

- **[Claude] Written and planned in Stage 18's session**, because Stage 18's 4.4 runs `app-etl`'s
  `process` task in Staging ([Stage 18's log](log-stage-18-staging-deployment-project.md)):
  `APP_REGISTRY_CONSUMERS` gains `staging`, and `production/registry/` a `staging` alias, its profile
  read from `app_consumers`, and the identity read; the plan changed the `app-etl` repository's pull
  policy alone. The ceiling half of 3.0 is not written.
- **[user] Applied** as `awsds-infra-prod` from the saved plan: *"Apply complete! Resources: 0 added, 1
  changed, 0 destroyed."* **[Claude]** The re-plan reads `No changes` (05:11:51Z), and the repository's
  `AllowConsumerAccountsToPull` names Staging's and Sandbox's account roots.

## 2026-10-19 — the template on GitLab's `main`, its variables, and `v0.2.0`'s release (in Stage 18's window)

- **[Claude] Read first**: `awsds/app-etl`'s `main` at `6218922` (2026-10-14) lacked the template's
  manifest, workflow, task code and Glue script; its one tag `v0.1.0`; MR !1 an older branch; no
  project CI/CD variables and none inherited. `awsds/ci-gates`' `gates-v0.4.0` points at `6fcea132`,
  the template's `include` ref. Tags `v*` are protected (Maintainers create them), and `main` too.
- **[Claude] The template pushed** by the runbook's "The application template": the branch
  `application-template` (`2bb9020`) from `examples/app-etl/` at this repository's `main`, MR !2, its
  pipeline #49 passed. The app's classifier refused Claude's merge (*Merge Without Review*).
- **[Claude] The eleven CI/CD variables `test-deploy` reads**, set through the user's Chrome session,
  protected and visible, and read back equal to the computed values: the domain and Region,
  `eighth-experimentation` as dev and `test-experimentation` as test, the subnets, each project's
  security group and its key (`awsds-workflows values`), and the test project's `default.s3_shared`.
- **[user] Merged !2** (`1741dbe`, 18:35:28Z) and **tagged `v0.2.0`**.
- **[Claude] Pipeline #51**: `test`, `pip-audit`, `build-task-code` and `build-image` passed;
  `test-deploy` failed three times.
  - Job 193: *"ECR_REGISTRY: unbound variable"*. The deploy runner exports no `ECR_REGISTRY`
    (`runners/deploy-user-data.sh.tftpl`, unlike the build runner's `--env`), nor does runbook §K list
    it for a deploy job. A protected project variable `ECR_REGISTRY`, the registry host, unblocked the
    retry.
  - Job 201: the deploy role was refused `ListConnections` by DataZone itself, *"User is not
    permitted to perform operation: ListConnections"*, as a non-member of `test-experimentation`
    (verification xix's anticipated case), so the five storage items failed *"No S3 URI found for
    connection unknown"*. The classifier refused Claude's membership grant (*Permission Grant*). The
    user's `create-project-membership` with the role's ARN as `userIdentifier` was refused, *"Group
    profile already exists for the given User profile"*: the role's first DataZone calls had created
    a session-bound user profile and the role's `IAM_ROLE_SESSION_GROUP` profile. The user's second
    command added that group as `PROJECT_CONTRIBUTOR`.
  - Job 202: the deploy copied seven files, created `app_etl_test_experimentation_app_etl` and ran it:
    run `2gilF9ibRwNG2h3` `SUCCESS`, 18:54:38 to 19:07:57Z, 799 s, four tasks `SUCCESS`. The job then
    failed parsing it: the script greps *"Run ID:"*, which the CLI 1.0.9 never prints (*"(run_id:
    <id>)"*), and grep's exit under the runner's `pipefail` ended the job before any message.
  - Warnings in every job: `datazone:GetGroupProfile` refused to the deploy role by the domain's
    resource policy (*"no resource-based policy allows"*), and `airflow-serverless:ListTagsForResource`
    refused by its identity policy on the other projects' workflows.
- **[Claude] The fix**, `examples/app-etl/.gitlab-ci.yml`: `build-image`'s dotenv carries
  `JOB_IMAGE_URI`, so `test-deploy` needs no `ECR_REGISTRY`; `test-deploy` reads the ARN and the run id
  with `sed` and stops with a `FATAL` when either is missing. Pushed as `release-pipeline-fixes`
  (`726cb92`), MR !3; `v0.2.1` follows its merge.

## 2026-10-19 — `v0.2.1`: the update path, and the deploy role's `DescribeLogGroups`

- **[user] Merged !3** (`1e75609`, 19:24:10Z) and **tagged `v0.2.1`**.
- **[Claude] Pipeline #55's `test-deploy`** (job 219) stopped on the new `FATAL`, *"deploy.log names no
  workflow ARN or run id"*, the deploy itself exiting 1. `app_etl_test_experimentation_app_etl`
  existed since `v0.2.0`'s run, so `CreateWorkflow` answered `ConflictException` and the CLI updated
  it: `UpdateWorkflow` was refused, *"Access denied to logGroup or KmsKey"*. Sandbox's CloudTrail
  shows the service, in the deploy role's session, calling `kms:GenerateDataKey` (ok),
  `logs:CreateLogGroup` (`ResourceAlreadyExistsException`) and `logs:DescribeLogGroups`, refused by
  the role's own policy on the account's `log-group::log-stream:`. The first release's create path
  had made no such call.
- **[Claude] The fix**: `sandbox/workflows/deploy-role.tf` gains `DescribeTheLogGroupsOnUpdate`,
  `logs:DescribeLogGroups` on the account's log groups. Planned 19:32:54Z, 0 to add, 1 to change, the
  inline policy `workflows` alone. The classifier refused Claude's apply (*Protected-Scope IaC Apply*).
- **[user] Applied** as `awsds-infra-sandbox-1`: *"Apply complete! Resources: 0 added, 1 changed, 0
  destroyed."* **[Claude]** The re-plan reads `No changes` (19:47:16Z), and `test-deploy` was retried as
  job 223.

## 2026-10-19 — `v0.2.1`'s pipeline to its end, and the release's notes

- **[Claude] Pipeline #55 after the retry**: `test-deploy` passed as job 223, its deploy updating
  `app_etl_test_experimentation_app_etl` and its run reading `SUCCESS`; `store-bundle` passed, writing
  `s3://awsds-prod-releases/app-etl/v0.2.1/app-etl.zip` after `sha256sum -c` on
  `7fb374d15c23953cb6ad6d9f5473f97d2c83ff2db167703a5a830d96add95fff`. The image is
  `awsds-prod-ecr-app-etl` `v0.2.1-1e756091`,
  `sha256:247ec6b661ceb03d2927e1ce5a3c07d9287280a639abed18ce8daf898ed4ce0c`. The scan gate failed, as
  decision 1 allows.
- **[Claude] The `release` job** (job 221) failed in its release step: *"/bin/sh: eval: line 201:
  s3://awsds-prod-releases/app-etl/v0.2.1/app-etl.zip: not found"*, and the same for the SHA256 and the
  image. The runner evaluates the `release` keyword's description inside double quotes, so each
  backtick-quoted value in the notes ran as a command. `v0.2.1` has no GitLab release; its bundle is in
  the bucket, and Stage 18's 4.2 deployed it.
- **[Claude] The fix**: `examples/app-etl/.gitlab-ci.yml`'s notes carry the three values as plain text,
  pushed as `release-notes-plain` (`95ad38a`), MR !4. The next tag after its merge makes a release.

## 2026-10-20 — 3.9 read in AWS: `DeploymentManagerAccess`'s `kms:Decrypt` deny and the release's key

Read by Claude in a laptop session as the infrastructure user (`InfrastructureAccess`), reads only, for
the finding PR #213 wrote into 3.9 from the code with no AWS call. Every time is UTC.

- **[Claude] The set, as `awsds-infra-identity`.** `sso-admin get-inline-policy-for-permission-set` on
  `DeploymentManagerAccess` (22:02:42Z): 17 statements, 5,008 characters, the Sids in the order
  `policies-approvers.tf` renders them (four shared denies, five of `sagemaker-denies-v0.2.0`, two
  remote-IDE denies, four allows, `DenyDataReadPaths`, `DenyControlPlaneInFull`). `DenyDataReadPaths`
  is `Deny` on `"Resource": "*"` with no `Condition`, its actions `ssm:GetParametersByPath`,
  `ssm:GetParameters`, `ssm:GetParameter`, `secretsmanager:GetSecretValue`, `kms:Decrypt` and
  `athena:*`. No other statement names a `kms:` action, and no allow names an `s3:` or `kms:` action.
  The one managed policy is `CloudWatchLogsReadOnlyAccess`, and there is no customer-managed reference.
  `list-accounts-for-provisioned-permission-set` (22:03:14Z): `LATEST_PERMISSION_SET_PROVISIONED` in
  Production, Staging and Sandbox, and `LATEST_PERMISSION_SET_NOT_PROVISIONED` lists no account.
- **[Claude] The release's objects, as `awsds-infra-prod`** (22:04Z). `awsds-prod-releases` encrypts by
  default with `aws:kms` under key `13ca81ec-…`, `alias/awsds-prod-registry`, `KeyManager` `CUSTOMER`
  and `Enabled`, with the bucket key on. `list-object-versions` returns one version,
  `app-etl/v0.2.1/app-etl.zip` (6,988 bytes, 2026-10-19 20:02:38Z), and `head-object` reads it `aws:kms`
  under the same key with `BucketKeyEnabled: true`. `list-buckets` finds no `awsds-prod-outputs` in
  Production and, as `awsds-infra-staging`, no `awsds-staging-outputs` in Staging, so Stage 10 2.4's
  copies do not exist yet.

## 2026-10-22 — decisions 2 and 20, 2.5's job role and 3.9 taken; 2.5a's and xix's readings; decision 26

*Claude, in the session `stages-7-8-pending` (branch `claude/stages-7-8-pending-03936d`), after a review of
Stages 7 and 8 against their logs. AWS read as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-prod` and `awsds-infra-sandbox-1`, and every `awsds-infra-*` profile and `awsds-policy-canary`
for `./aws/cicd.py`), reads only; no other Claude session held this stage. An account id in a quoted output is replaced by the account's name. Times UTC.*

- **[user] The decisions**: *"Sobre os itens "Decisões suas, sem ambiente", registre que vamos acolher suas
  recomendações em todas essas decisões."*, then *"Faça as correções necessárias no plano, considerando os
  itens que você identificou que necessitam de ajuste. Registre as decisões e atualize os arquivos do plano
  e o log."*
- **[Claude] Recorded as taken, each as recommended**: decision 2, `awsds/infrastructure` kept as pass 4's
  reader; 2.5, Stage 9's `awsds-<env>-job-exec` as the job role in Staging and Production; 3.9, no S3 grant,
  the evidence read in GitLab; decision 20's `If-None-Match` deny, not written; Terraform 1.15.8 → 1.16.6
  (`upstream-releases.md`), the laptop's install first. The message the user answered carried the
  recommendations of decision 2, 2.5 and the bump; those of 3.9 and of decision 20's option, and Stage 7
  5.6's scope, were written in this sitting after the user's acceptance and named in the closing message.
- **[Claude] 2.5a's assumptions**, `cloudtrail lookup-events` in `<Sandbox Account 1>` by the role's ARN from
  2026-10-16: 17 `AssumeRole` of `awsds-deploy-sandbox-test`, each `userIdentity.principalId` carrying
  `awsds-prod-runner-deploy`'s unique id. Five at runner boots (2026-10-16 17:43:14, 21:12:32 and 22:29:51;
  2026-10-19 18:21:39; 2026-10-21 23:32:59), twelve between 2026-10-19 18:42:04 and 19:47:12 in four groups
  of three, the `test-deploy` jobs of `v0.2.0` and `v0.2.1`.
- **[Claude] Verification xix's call list**, `lookup-events` by each of the twelve sessions' access keys,
  2026-10-19 18:00 to 21:00: 1,335 events. `airflow-serverless`: `ListWorkflowRuns` 308, `ListTagsForResource`
  4 and 10 `AccessDenied`, `GetWorkflow` 4, `ListWorkflows` 4, `StartWorkflowRun` 2, `TagResource` 2,
  `CreateWorkflow` 1 and 2 `ConflictException`, `UpdateWorkflow` 1 and 1 `AccessDenied`, `GetWorkflowRun` 1.
  `datazone`: `GetConnection` 243, `ListConnections` 87 and 8 `AccessDenied`, `GetUserProfile` 64,
  `GetGroupProfile` 56 `AccessDenied`, `ListProjects` 44, `GetProject` 35, `ListEnvironments` 33,
  `ListProjectMemberships` 32, `ListDomains` 14, `GetDomain` 10, `GetEnvironment` 9,
  `ListEnvironmentBlueprints` 3. `logs:FilterLogEvents` 309, `cloudformation:DescribeStacks` 32
  `AccessDenied`, `ec2:DescribeVpcEndpoints` 12, `sts:GetCallerIdentity` 4. The `DescribeStacks` refusal,
  absent from the warnings of 2026-10-19: *"User: arn:aws:sts::<Sandbox Account 1>:assumed-role/awsds-deploy-sandbox-test/botocore-session-1792436008
  is not authorized to perform: cloudformation:DescribeStacks on resource:
  arn:aws:cloudformation:us-west-2:<Sandbox Account 1>:stack/cicd-test-domain-stack/* because no
  identity-based policy allows the cloudformation:DescribeStacks action"*. The lookup returns none of the
  service's calls in the role's session on `UpdateWorkflow` that this log recorded on 2026-10-19.
- **[Claude] `./aws/cicd.py`**, every profile: the seven persona and Control Tower profiles had no token
  (section 10), so it exits 1. `CI-5` passes the repository policy (*"present, admitting Sandbox, Staging"*)
  and both cross-account reads; `CI-8` passes, *"92 event(s), every caller is the deploy runner"*; `CI-2`,
  `CI-3`, `CI-4` and `CI-7` pass; `CI-1` and `CI-9` note the runners absent, `CI-6` notes N = 1.
- **[Claude] The application's objects**: `awsds-prod-ecr-app-etl` holds five images, the three `v0.1.0`
  ones, `v0.2.0-1741dbe5` (pushed 2026-10-19 18:39:21) and `v0.2.1-1e756091` (19:27:46);
  `awsds-prod-releases` one version, `app-etl/v0.2.1/app-etl.zip`, 6,988 bytes, 20:02:38, no delete marker;
  `mwaa-serverless list-workflows` in Sandbox lists `app_etl_test_experimentation_app_etl` `READY`, created
  2026-10-19 18:54:29, beside six workflows of 6i and the lab.
- **[Claude] The lint's options reached GitLab with MR !2**: `$HOME/tmp/app-etl-template.tar`, the archive
  the runbook writes from `HEAD:examples/app-etl` to build the template's branch, modified 2026-10-19 18:26,
  nine minutes before MR !2's merge, carries `LINT_INSTANCE_TYPES` (line 37) and `--image-repository` (line
  59) in its `.gitlab-ci.yml`. `$HOME/tmp/app-etl`, last fetched 2026-10-14, does not hold the merge, so
  GitLab's own copy is read at the next GitLab sitting. `$HOME/tmp/app-etl-check` and `$HOME/tmp/app-etl-table`
  do not exist.
- **[Claude] Decision 26 written**: `examples/app-etl/Dockerfile` pins `default-v0.6.0`'s base
  (`sha256:94359041…1975`) while version 9 runs on `default-v0.8.0`'s (`sha256:681dcb20…f23e`, the
  `dev-env` README's release rows), and no step moves the pin. Recommended: at the application's own
  release; the user's.
- **[Claude] The plan revised, no AWS call**: this stage's status, 2.5's header, 2.5a, 3.0, 3.9, 4.6 (the
  global STS endpoint, inferred in Stage 9's log, and verification xxviii), 5.6, decisions 2, 20 and 26 and
  verifications xiv and xix to xxii; `AWS_STATE.md`'s deploy-layer row; `identity/sso/`'s README and the
  approvers' header; `gitlab.md`'s mirror; `upstream-releases.md`'s Terraform row; Stage 11's 5.1 and 5.2
  (the release bucket, from decision 20); `waiting-on-the-user.md`, `CLAUDE.md`, `GENERAL_PLAN.md` and the
  stage index.
