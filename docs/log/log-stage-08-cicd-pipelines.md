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
