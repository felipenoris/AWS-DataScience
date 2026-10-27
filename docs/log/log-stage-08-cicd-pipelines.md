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

## 2026-10-22 — decision 26 taken: no rule for an application's base pin

*Claude, in the session `stages-7-8-pending`, the same sitting. AWS read as the infrastructure user with
`InfrastructureAccess` (`awsds-infra-prod`, `awsds-infra-sandbox-1`), reads only. Times UTC.*

- **[user] The question**: *"Pode detalhar a decisão 26, as opções e recomendação?"*
- **[Claude] The two bases compared**, `ecr batch-get-image` on `awsds-prod-ecr-base` for
  `sha256:94359041…1975` (`default-v0.6.0`, `app-etl`'s pin) and `sha256:681dcb20…f23e`
  (`default-v0.8.0-7c59998c`, version 9's): 30 layers each, layers 1 to 25 identical, 26 to 30 different,
  each within 556 bytes of its counterpart (1,087,261 against 1,087,817 the largest). The base recipe
  between `a3f698bf` (`default-v0.6.0`'s commit) and `HEAD` differs in three comment lines, one error
  message and the `org.opencontainers.image.source` label.
- **[Claude] The options put to the user**: (a) the pin moves at the application's own release, the
  recommendation; (b) a `dev-env` release opening a merge request on each application; (c) a moving tag;
  (d) no rule; (e) the application naming its development version; and a drift note in `./aws/cicd.py`
  as a complement to (a).
- **[user] The decision**: *"Não deveria haver regra. Se a aplicação está estacionada numa versão antiga do
  Base, isso deve permanecer até que o desenvolvedor atualize explicitamente. O desenvolvedor deverá ter a
  disciplina de selecionar versão do space que seja equivalente ao base da aplicação."*
- **[Claude] What the decision meets**, `sagemaker list-image-versions` and `describe-image-version` on
  `awsds-sandbox-dev-env` in `<Sandbox Account 1>`: versions 7 (`default-v0.7.1-c268de48`), 8
  (`sha256:38f4864c…dd6f`) and 9 (`sha256:b788dbd9…1b87`). Version 6, built on `app-etl`'s base, was
  destroyed on 2026-10-15 at 01:59:57 (this log), so its equivalent versions are 7 to 9 by the layer
  reading above. `release/versions.py`'s `retire` keeps the newest 10 and every version a space or a
  domain names, and reads no application's pin.
- **[Claude] Recorded**: decision 26 taken, with those facts; the stage's status and 2.2;
  `waiting-on-the-user.md`'s row removed; `CLAUDE.md`, `GENERAL_PLAN.md` and the stage index.

## 2026-10-22 — pass 4 read against Stages 9, 10 and 18; `prepare()` fixed; xix and xxviii's passive half

*Claude, in the session `stages-7-8-pending`, which orchestrates the parallel review of Stages 8, 9 and
10; the sessions "Stage 9 — revisão e preparação" and "Stage 10 — revisão e preparação" hold those
stages. AWS read as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`,
`awsds-infra-staging`, `awsds-infra-sandbox-1`), reads only, the environment down. Times UTC.*

- **[user] The request**: *"Revise o plano dos estágios 8, 9 e 10, considerando o andamento atual do
  plano, em especial as decisões registradas na sessão atual, bem como o aprendizado com a conclusão do
  stage 18. Faça todas as leituras que não dependam do ambiente no ar. Usuário infra sso está logado.
  Faça a preparação necessária para todas as etapas dos estágios 8, 9 e 10 que forem possíveis de serem
  preparadas e que não precisam da minha intervenção ou decisão. Abra quantas tarefas em paralelo forem
  necessárias para estas atividades. Faça as correções necessárias no plano, atualize o log dos
  estágios correspondentes com o andamento feito. Ao final, planeje as etapas seguintes que dependem do
  ambiente no ar."*
- **[Claude] Pass 4, item by item**, a read-only subagent over this stage, Stages 9, 10 and 18 and the
  code: no item can be written whole now. 3.2, 3.3 and 3.6 wait on Stage 9's platforms (4.3's
  `awsds-staging-job-exec`, `staging/data/`, `production/data/`, behind its decisions 1 and 3) and on
  Stage 10's decisions 1, 2, 8 and 12 and its `orchestration/` slices; 3.0's ceiling content on Stage 10's
  roles; 3.7 and 3.8 follow a promotion. What each needs of Stages 9 and 10 was sent to their sessions.
- **[Claude] The readings**:
  - `iam get-role`: `awsds-staging-job-exec` *"cannot be found"*; `awsds-prod-job-exec` created
    2026-10-18 19:59:03, no permissions boundary. `s3api head-bucket`: no `awsds-staging-outputs` or
    `awsds-prod-outputs`. `iam list-policies --scope Local`: no `awsds-<env>-app-boundary` in either.
  - `iam list-role-policies`: `awsds-deploy-staging` holds `apply-egress` and `state`,
    `awsds-deploy-prod` holds `state`.
  - Verification xxviii's passive half, `cloudtrail lookup-events --region us-east-1` on `AssumeRole`
    from 2026-10-12: 0 events naming an `awsds-deploy-*` role in Production, Staging and Sandbox, beside
    32, 35 and 41 service-linked `AssumeRole` events (`AWSServiceRoleForOrganizations`, Athena's,
    Resource Explorer's, Service Quotas').
  - Verification vii's third half: no `UpdateDomain` in Sandbox since 2026-10-18.
  - Verification xix's comparison: AWS's sample IAM policy for the CI/CD feature, read 2026-10-22, holds
    18 entries on `*` and covers 7 of the role's 25 actions; the 18 it leaves out are in the stage file.
- **[Claude] `scripts/slices.py`'s `prepare()`**: with `--profile` naming a deploy role it now runs
  `gen-tfvars.py --pipeline`, so `make down ENV=staging PROFILE=awsds-deploy-staging` (3.4) writes an
  application slice's registry profile as the runner's own rather than `awsds-infra-prod`, which the
  runner does not hold; `layers.deploy_profiles()` is the set refusal 8 already used. Read: `slices.py
  down --env staging --profile awsds-deploy-staging --dry-run` prints `gen-tfvars.py --pipeline staging
  egress`, without the profile it prints no flag, and the three `egress` slices' tfvars render the same
  with and without it; `ruff` clean.
- **[Claude] The plan revised, no AWS call**: the status, the build table (the two ceilings), the pass
  table, 2.5's ceiling claim (five role-policy writes, not every change), 3.0 (its applied half, the
  ceiling's shape), 3.1 to 3.8 (Stage 18's measurements and the asks of Stages 9 and 10), 4.1 (the scope by
  name, Stage 18's amendment and removal of three inline documents, the residual profiles, 1.5's fuller
  list), 4.4, 4.6, 6.1 and the risk on decision 2, verifications xix and xxviii; the comments in
  `staging/foundation/deploy-role.tf`, `production/foundation/deploy-anchors.tf` and `backend.py` that
  still cited 2.4; `docs/REFERENCES.md`'s CI/CD pages line.

## 2026-10-22 — Stages 9 and 10's hand-over consolidated, and the sittings with the environment up planned

*Claude, in the session `stages-7-8-pending`, after the sessions "Stage 9 — revisão e preparação" (PR #245)
and "Stage 10 — revisão e preparação" (PR #246) ended their turns; no AWS call in this entry.*

- **[Claude] The two reports**, read from the sessions' notes: each PR kept to its own files and left the
  shared upkeep files to this session. Stage 9 wrote and planned `staging/sagemaker/` (8 to add), the
  Production job role's `glue:GetConnection` (1 to change), the `staging/egress/` re-cut (15 to add) and
  `production/workloads/` on `vpc-v0.4.0` (1 to change), and opened its decision 12. Stage 10 wrote and
  planned `terraform-modules/orchestration/` and both `orchestration/` slices, and opened its decisions 19
  and 20. The classifier refused that session's push of the tag `orchestration-v0.1.0`
  (*Out-of-Place Publication*), so its slices pin the module by path until the user authorizes the push.
- **[Claude] What Stage 8 received**: the application ceiling's content (3.0, an allow-list from Stage 10);
  the application halves' specification (4.1), whose orchestration grant has its single home in Stage 10
  1.5; the place of Stage 9 4.4's seed and 3.4's approval half (3.3). Stage 10 was asked to align its 1.3
  sentence on the deploy role's ceiling with the six actions the module denies.
- **[Claude] The shared files, rewritten once from the reports**: `waiting-on-the-user.md` (the quota row,
  Stage 9's decisions with 12, the registry row, the Stage 9 applies, the tag push, Stage 10's decisions,
  and the sittings table with a Promotion row for pass 4), `CLAUDE.md`, `GENERAL_PLAN.md` (39,471 bytes), the
  stage index, the log index and `AWS_STATE.md`'s network row.

## 2026-10-22 — Stage 9's decisions 2, 5 to 8, 11 and 12 taken, and what Stage 8 follows

*Claude, in the session `stages-7-8-pending`, no AWS call. The decisions themselves are recorded in
Stage 9's log by the session that holds Stage 9 (PR #245), to which the user's words were relayed.*

- **[user] The decisions**: *"Pode registrar como aceitas as recomendações de decisão em relação aos
  seguintes itens: # Stage 9 * #2 Limite de dados por query no athena. * #11 onde ficam os resultados de
  query em Staging e Produção * #12 a rede do job glue * #5 como um projeto do sandbox lê uma tabela
  governada no redshift * #6 Quem cria as tabelas do warehouse governado * #7 Os limites de custo do
  warehouse * #8 os logs de auditoria do warehouse"*. Stage 9's decisions 3 and 1 stay open, and no
  Stage 10 decision was taken.
- **[Claude] What follows here**: 4.1's application halves no longer wait on Stage 9 decision 12, whose
  option (a) puts the Glue connection and the job security group in `*/sagemaker/` for the application
  slice to reference. Stage 10 was told that its decision 20(b), which had the application slice declare
  both, must follow 12(a). `waiting-on-the-user.md`, `CLAUDE.md`, `GENERAL_PLAN.md` and the stage index
  carry the taken decisions.

## 2026-10-22 — Stage 9's revised recommendations for decisions 1 and 3 reach Stage 8 and the shared files

*Claude, in the session `stages-7-8-pending`, no AWS call. The revision was asked for by the user in a
session started from this one under the same title, which relayed it to the Stage 9 session; that
session recorded it in PR #245 (`55ed4c90`) as recommendations, with the decisions still the user's.*

- **[Claude] What changed here**: 4.1's list no longer carries the archive read on `awsds-deploy-staging`,
  since Stage 9 decision 1 now recommends that Staging read nothing of Production's outputs, the model
  archives included; the read survives as that decision's option (a). `waiting-on-the-user.md`,
  `GENERAL_PLAN.md` and the stage index carry the two revised recommendations. The threat model's
  `TM-25` and D20's amendment wait on decision 3 being taken.

## 2026-10-22 — Stage 9's decisions 1 and 3 taken: D20 amended, `TM-25`, the design documents

*Claude, in the session `stages-7-8-pending`, no AWS call, on a message from the session started from
this one under the same title, relaying the user's words there; the words were read in that session's
transcript before anything was written. The Stage 9 session records the decisions in its own log.*

- **[user] The decisions**, relayed verbatim: *"Avise às sessões que irei acatar as recomendações em
  relação às decisões 3 e 1, conforme conversamos nesta sessão."* Stage 9 decisions 3 and 1 are taken as
  revised in PR #245 (`55ed4c90`): no mirror, Staging reading the governed lake in place, read-only,
  through the LF-Tag share Sandbox holds, and nothing of Production's outputs read in Staging, the model
  archives included. Every Stage 9 decision is taken.
- **[Claude] The files that described the previous design**: D20 amended in place and its index row;
  `threat-model.md` gains `TM-25`, the read accepted with its compensations and revision triggers, and
  its catalog-layer row names Staging; `GOVERNANCE.md` (the diagram, the account table, the test
  paragraph), `ORGANIZATION.md`, `README.md`, `architecture.md`'s tree and open question 9, closed. The
  waiting list loses Stage 9's decisions row; `CLAUDE.md`, `GENERAL_PLAN.md` and the stage index say every
  Stage 9 decision is taken; Stage 8 4.1 writes no archive read, and 3.3 places the deploy's own tables
  between 3.2 and 3.3.

## 2026-10-22 — the rest of decision 3's text from Stage 9's record

*Claude, in the session `stages-7-8-pending`, no AWS call, from the Stage 9 session's report of its
commit `29302c94` (PR #245), which records decisions 3 and 1 and withdraws 4.4.*

- **[Claude] Applied**: `GOVERNANCE.md`'s Staging row (its own catalog filled by each deploy, with resource
  links to `raw` and `curated`; read through the TBAC share and the local re-grants, `DESCRIBE` and
  `SELECT` alone), the warehouse sentence, the grants' principals and node 5 of the development cycle;
  INT-03's restored Staging read; D20's argument, the user's; the Stage 9 rows of `CLAUDE.md` and the log
  index. Stage 8 3.3 no longer names 4.4: each deploy fills Staging's own catalog (Stage 9 4.1).

## 2026-10-22 — Stage 10 decision 1 taken: the definitions home moves to `applications/`

*Claude, in the session `stages-7-8-pending`, no AWS call, on the Stage 10 session's report of its
commit `f2bd47a7` (PR #246); the user's words were read in the transcript of the session started from
this one, where they were written.*

- **[user] The decision**, in that session: *"Sim, peço registrar esta recomendação revisada e acatar esta
  como sendo a decisão tomada."* Stage 10 decision 1, revised: the bundle stays whole in
  `awsds-prod-releases`, its tree is unpacked under `awsds-<env>-outputs/applications/<app>/<tag>/`, the
  workflow's YAML alone rendered and every other file copied byte for byte, `MANIFEST.sha256` proving it.
- **[Claude] What follows here**: 2.5's job-role cost, 3.2's copy, 3.8's exemption, 3.9's reading and
  5.6 (h) name `applications/` for `workflows/`; the waiting list drops decision 1 from Stage 10's row.
  The module tag `orchestration-v0.1.0` now goes on `26bfc15d`, the module's last commit.

## 2026-10-22 — Stage 10 decisions 5, 8 and 12 confirmed

*Claude, in the session `stages-7-8-pending`, no AWS call; the Stage 10 session records the decisions in
its own log, the user's words relayed to it.*

- **[user] The confirmation**: *"Confirmo estes itens:"*, above the orchestrator's list of Stage 10's
  decisions 5 (the orchestration slice `[E]`), 8 (a SageMaker processing job, not an ECS task) and 12 (the
  Glue scripts under the release's `applications/<app>/<tag>/glue/`, writes to `applications/*` denied to
  all but the release role and `InfrastructureAccess`).
- **[Claude] What follows here**: 3.0's ceiling admits no ECS action and waits on Stage 10 decision 2 alone;
  the waiting list keeps Stage 10's decisions 2, 3, 4, 9, 11, 19 and 20, and `CLAUDE.md` and the stage
  index name 2, 19 and 20 as the ones pass 4 waits on.

## 2026-10-22 — Stage 10 decisions 2, 3, 4, 9, 11, 19 and 20 taken

*Claude, in the session `stages-7-8-pending`, no AWS call; the Stage 10 session records the decisions in
its own log, the user's words relayed to it, and the Stage 9 session was told of 20(d)'s exception.*

- **[user] The decisions**: *"Aceito as recomendações das decisões 2, 3, 4, 9, 11, 19 e 20 (a, d, e) do
  Stage 10, com a 20(d) como exceção explícita do template. Registre-as."* Every Stage 9 and Stage 10
  decision is taken.
- **[Claude] What follows here**: 3.0's ceiling has its content settled (decisions 2 and 8); 4.1's
  application halves no longer wait on a decision; 3.2 names the Glue job `awsds-<env>-app-etl`, the render
  by `scripts/render-workflow.py` and the inbox seeded from the bundle's `samples/`, the template's
  explicit exception to Stage 9 decision 3; 3.3's leg starts the chain's state machine (decision 19). The
  waiting list loses Stage 10's decisions row; `CLAUDE.md`, `GENERAL_PLAN.md` and the stage index say every
  decision of both stages is taken.

## 2026-10-22 — 3.0's ceiling and 4.1's application halves written and planned

*Claude, in the session `stages-7-8-pending`; read-only AWS calls and two plans as the infrastructure user
(`awsds-infra-staging`, `awsds-infra-prod`, `awsds-infra-sandbox-1` for Production's aliased read), no
apply.*

- **[user] The request**: *"Prepare o teto awsds-<env>-app-boundary (3.0) e as permissões de aplicação dos
  deploy roles (4.1) nas slices foundation de Staging e Produção, só com plano, sem aplicar."*
- **[Claude] What was written**, in both `foundation/` slices: `app-boundary.tf` (the ceiling, Stage 10's
  hand-over) and `apply-orchestration.tf` (Stage 10 1.5's enumeration), each one file copied byte for byte
  and held by the new `./scripts/check-copies.py`, wired into `make check` and pre-commit. What one account
  adds is in its deploy role's file: Staging's `StartTheChainInTheLeg` and `FollowTheChainInTheLeg` (Stage 10
  decision 19), `ReadTheApprovedModelVersions` on `awsds-prod-model-*` packages with Production's account
  read through the `deploy_runner` alias, and `ListTheModelVersions`; Production's
  `CreateTheWorkflowServiceLinkedRole`. `apply-application`, inline on both roles, holds `PassTheJobRole`
  (`awsds-<env>-job-exec` to Glue and SageMaker). The module calls gain `<folder>/orchestration/` and the
  read keys (`staging/foundation/` and `staging/sagemaker/`; `production/workloads/`, `foundation/` and
  `sagemaker/`), still on `deploy-role-v0.3.0`.
- **[Claude] The first plan's measurement**: with the grant as the inline `apply-orchestration` 4.1
  specified, Staging's role would carry 12,483 characters of inline documents without white space
  (`state` 1,062, `apply-egress` 3,023, `apply-application` 562, `apply-orchestration` 7,836), past IAM's
  10,240, and Production's 9,090. The grant alone passes the 6,144 a managed policy holds, so 4.1's
  fallback, one customer-managed policy, could not hold it either: it became two, split by content,
  `awsds-<env>-deploy-orchestration-resources` (the workflows, the state machines, schedules and rules,
  the workers' group) and `-access` (the roles and their `PassRole`, the definitions home, the data key, the
  log groups), attached by the slice.
- **[Claude] The plans**, with `-var-file=<project folder>/secrets/alerts.auto.tfvars`: `staging/foundation/`
  6 to add, 2 to change, 0 to destroy; `production/foundation/` the same. The two changes in each are the
  role's description and its `state` document (the new prefix and read keys); no other pending change
  in either slice. Sizes: inline 4,647 (Staging) and 1,382 (Production) of 10,240; managed
  `app-boundary` 1,641 and 1,629, `-access` 3,811 and 3,760, `-resources` 4,063 and 3,986, of 6,144.
- **[Claude] Readings**: `AWSServiceRoleForAmazonMWAAServerless` exists in Staging, path
  `/aws-service-role/airflow-serverless.amazonaws.com/`, created 2026-10-19T20:09:32Z, and `GetRole` answers
  `NoSuchEntity` in Production, the ARN the statement names. Every permission action
  `orchestration-v0.1.0` grants its `wf-` and `chain-` roles (36) falls inside the ceiling's allow-list;
  `sts:AssumeRole`, from the trusts, is the only action outside it. Neither PR #245 nor PR #246 touches
  either `foundation/` slice.
- **[Claude] What follows**: the two applies wait on the user's authorization (the waiting list). Stage 9's
  stage file still says 3.0's ceiling half is not written; the Stage 9 session was told, since that file
  is its own.

## 2026-10-22 — 4.1 completed from Stage 9's report, and Stage 10 decision 11's carve-out

*Claude, in the session `stages-7-8-pending`; three plans as the infrastructure user (`awsds-infra-staging`,
`awsds-infra-prod`, `awsds-infra-identity`), no apply.*

- **[Claude] What Stage 9's report added to 4.1** (its section 8, after its passes 2, 3 and 5): the release
  job's `inbox/*` beside `applications/*` (Stage 10 decision 20 (d)'s seed), the data key's statements as
  twins of the key policy's `AllowTheReleaseRoles*`, the application's tables in `app_outputs` (Lake
  Formation's half in each `data/`), and the `data/` state keys.
- **[Claude] What was written**: `apply-application.tf` joins the copied files with `PassTheJobRole` and
  `ManageTheApplicationTables`, each account's additions in `apply_application_in_this_account` (Staging's
  registry read; Production's empty until Stage 9 9.4's Data API grant). The orchestration grant's access
  policy writes `applications/*` and `inbox/*`, and `EncryptTheWorkflows` gives way to
  `UseTheDataKeyForTheWorkflows` (the workflow-ARN encryption context), `GrantTheDataKeyToTheServices`
  (`kms:GrantIsForAWSResource`) and `DescribeTheDataKey`. The read keys gain `<folder>/data/`.
- **[Claude] The foundation plans**: each still 6 to add, 2 to change, 0 to destroy. Sizes without white
  space: inline 5,098 (Staging) and 1,836 (Production) of 10,240; `-access` 4,490 and 4,427, `-resources`
  4,063 and 3,986, the ceilings 1,641 and 1,629, of 6,144.
- **[user] Stage 10 decision 11's carve-out**: *"Pode aprovar a exceção, conforme a recomendação."* The
  recommendation: `kms:Decrypt` for `DeploymentManagerAccess` only when the encryption context carries
  `aws:airflow-serverless:workflow-arn`, D31's decrypt deny narrowed to requests without it, `kms:ViaService`
  added once a trail shows the calls carry it.
- **[Claude] What follows here**: `identity/sso/policies-approvers.tf` gains `ReadWorkflowRunStatus` (the
  six `airflow-serverless:` reads), `DecryptWhatTheWorkflowServiceEncrypts` and
  `DenyDecryptOutsideTheWorkflowService`, and `DenyDataReadPaths` loses `kms:Decrypt`. Its plan: 0 to add,
  1 to change, 0 to destroy, the set's inline policy alone, 7,289 to 8,223 rendered characters of the
  slice's 10,240 ceiling. The apply joins the waiting list; the key-policy half is Stage 9's `data/`
  slices'. The Stage 10 session was given the user's words and the commit for its decision and its log.

## 2026-10-22 — 3.0's ceiling, 4.1's application halves and Stage 10 decision 11's carve-out applied

*Claude, in the session `stages-7-8-pending`, as the infrastructure user (`awsds-infra-prod`,
`awsds-infra-staging`, `awsds-infra-sandbox-1`, `awsds-infra-identity`, each `InfrastructureAccess`).*

- **[user] The authorization**: *"I authorize applying staging/foundation, production/foundation and
  identity/sso as the infrastructure user. Warn the other sessions and re-plan before applying."*
- **[Claude] Before**: the sessions Stage 9, Stage 10 and `Chat lateral` warned by message. Fresh saved
  plans: `production/foundation/` and `staging/foundation/` 6 to add, 2 to change, 0 to destroy, each with
  the alerts var-file; `identity/sso/` 0 to add, 1 to change.
- **[Claude] The applies**, in order: `production/foundation/` *"Apply complete! Resources: 6 added, 2
  changed, 0 destroyed."*; `staging/foundation/` the same; `identity/sso/` *"0 added, 1 changed, 0
  destroyed"*, the permission set's inline policy modified in 7 s.
- **[Claude] After**: each re-plan `No changes` (`-detailed-exitcode` 0). Read back:
  - `awsds-deploy-prod`: inline `apply-application` and `state`, attached
    `awsds-prod-deploy-orchestration-resources` and `-access`, boundary `awsds-prod-deploy-boundary`;
  - `awsds-deploy-staging`: inline `apply-application`, `apply-egress` and `state`, the same two attached,
    boundary `awsds-staging-deploy-boundary`;
  - `awsds-prod-app-boundary` and `awsds-staging-app-boundary` at `v1`, attachment count 0, boundary usage
    0;
  - `AWSReservedSSO_DeploymentManagerAccess_*`'s `AwsSSOInlinePolicy` in Sandbox, Staging and Production
    carries `ReadWorkflowRunStatus`, `DecryptWhatTheWorkflowServiceEncrypts` and
    `DenyDecryptOutsideTheWorkflowService`, and its `DenyDataReadPaths` lists no `kms:Decrypt`;
  - `./aws/cicd.py awsds-infra-prod awsds-infra-staging awsds-infra-sandbox-1`: all checks passed, `CI-2`
    for the four deploy roles, `CI-3`, `CI-4`, `CI-5` three times, `CI-7` twice, `CI-8` 92 events, every
    caller the deploy runner; notes `CI-1`, `CI-6`, `CI-8` (xvi) and `CI-9`.
- **[Claude] What follows**: the waiting list loses both apply rows and the promotion sitting's
  prerequisite on them; Stage 8 3.9's sentences name `DenyDecryptOutsideTheWorkflowService`, and so does
  6g's set table. The Stage 9 and Stage 10 sessions were told.

## 2026-10-22 — Stage 9's applies consolidated into the shared files

*Claude, in the session `stages-7-8-pending`, reads only (`awsds-infra-prod`, `awsds-infra-staging`,
`awsds-infra-data`), on the Stage 9 session's report of its applies (PR #245, section 10 of its note).*

- **[Claude] Readings, before writing its results down**: in Production and Staging, `alias/awsds-<env>-data`
  `Enabled`, `CUSTOMER`; `awsds-<env>-outputs` present; `awsds-<env>-job-exec` present (Staging's created
  2026-10-22T19:47:33Z); the Glue connection `awsds-<env>-jobs`, `NETWORK`; Lake Formation one administrator,
  both default lists empty, `CROSS_ACCOUNT_VERSION` 4; the database `app_outputs`. In Data Governance,
  `list-permissions` lists seven triples to the two accounts, each with the grant option: to each, `DESCRIBE`
  on the databases `layer ∈ {raw, curated}` and `SELECT`, `DESCRIBE` on the tables adding `classification ∈
  {public, internal}`; to Production, `DESCRIBE` on `curated` and, on its `ALL_TABLES`, `ALTER`, `DELETE`,
  `DESCRIBE`, `INSERT` and `SELECT`.
- **[Claude] What follows here**: the waiting list loses Stage 9's applies row and the promotion sitting's
  prerequisite on them, and both egress rows read 16 to add; `CLAUDE.md`, `GENERAL_PLAN.md`, the stage and
  log indexes take Stage 9's text; `AWS_STATE.md` gains the six grant rows, the lake's three trusted gateway
  endpoints and `curated.trades`, and the deployment targets' Lake Formation row; `PRICING.md` reads 17 keys.

## 2026-10-22 — pass 4's code written, the application slices planned

*Claude, in the session `stages-7-8-pending`; plans and reads as the infrastructure user
(`awsds-infra-staging`, `awsds-infra-prod`), no apply.*

- **[user] The request**: as Stage 7's entry of the same sitting quotes, then Stage 8 pass 4's code.
- **[Claude] The application slices**: `staging/app/app-etl/` and `production/app/app-etl/`, one slice
  copied but `release.tf`, the Glue job `awsds-<env>-app-etl` on `sagemaker/`'s job role and connection,
  its script under the release's prefix. Plans: `No changes` with no release in each; with `v0.2.1` as a
  stand-in (`sha256:247ec6b6…ce0c`, read with `ecr describe-images`, and the bundle's
  `7fb374d1…5fff`), 1 to add in each, the job reading `awsds-<env>-job-exec`, `awsds-<env>-jobs` and
  `s3://awsds-<env>-outputs/applications/app-etl/v0.2.1/glue/transform.py`.
- **[Claude] The deploy roles**: `ManageTheApplicationGlueJob` in `apply-application.tf`; each
  `foundation/` plans 0 to add, 1 to change, the inline documents 5,359 and 2,094 of 10,240.
- **[Claude] The scripts**: `scripts/render-workflow.py` (`--check` in `make check` and pre-commit) rendered
  `v0.2.1`'s workflow from Staging's and Production's states; `scripts/release-application.py`'s dry run on
  the same bundle, downloaded from `awsds-prod-releases` as `awsds-infra-prod`, listed seven objects and a
  manifest in which only `workflows/app-etl.yaml` differs from the bundle, and refused a wrong SHA256.
  `scripts/tfhygiene/states.py` reads a slice's outputs for both.
- **[Claude] The template's legs**: `staging-up`, `staging-deploy`, `staging-test`, `staging-down`,
  `production-plan`, `production-gate`, `production-deploy`; `check-gitlab-ci.py` read 20 jobs, every name
  resolved, every script item through `bash -n`.
- **[Claude] What follows**: the two `foundation/` applies and `identity/sso/`'s join the waiting list;
  the template reaches `awsds/app-etl` by an MR at a GitLab sitting; the application's tables and 3.3's
  share read wait for a schema.

## 2026-10-22 — the deploy roles' Glue job grant applied

*Claude, in the session `stages-7-8-pending`, as the infrastructure user (`awsds-infra-prod`,
`awsds-infra-staging`), on the user's authorization quoted in Stage 7's entry of the same sitting.*

- **[Claude] The applies**, from fresh saved plans, Production first: `production/foundation/` and
  `staging/foundation/` *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."* each.
- **[Claude] After**: each re-plan `No changes` (`-detailed-exitcode` 0); `apply-application` reads
  `PassTheJobRole`, `ManageTheApplicationGlueJob` and `ManageTheApplicationTables` on `awsds-deploy-prod`,
  and the same with `ReadTheApprovedModelVersions` and `ListTheModelVersions` on `awsds-deploy-staging`.

## 2026-10-22 — 3.3's integration tests read through the share, pinned to an Iceberg snapshot

*Claude, in the session `stages-7-8-pending`, no AWS call; the step of 15:19 (commit `26c06cc7`), from
the Stage 9 session's revised 4.4 (PR #245), recorded at the end of the sitting.*

- **[Claude] Applied**: Stage 9's 4.4, withdrawn by decision 3, says that in the Staging leg the deploy
  creates the application's own tables after 3.2 and before 3.3, and that a test reads them and the
  governed tables through the share, pinned to an Iceberg snapshot. Stage 8 3.3 says so and names 4.4
  again, a reference the entry on the rest of decision 3's text had removed the same minute.

## 2026-10-22 — the third sitting with the environment down: the promoted lint in the legs, Staging's release file kept, 3.8's sequence

*Claude, in the session `stages-8-9-10-review` (the branch `claude/stages-8-9-10-review`), on the user's
request to review Stages 8, 9 and 10 against their state, Stage 18's lessons and the readings so far, and
to prepare everything that needs no environment. AWS read as the infrastructure user with
`InfrastructureAccess` (`awsds-infra-prod`, `awsds-infra-staging`, `awsds-infra-sandbox-1`), reads and
plans only, the tunnel down (`NO_PROXY='*'`). Nothing applied. Times UTC.*

- **[user] The request**: *"Em relação aos estágios 8, 9 e 10, peço fazer o seguinte: verifique o
  status atual de cada estágio. revise o plano destes estágios considerando o andamento atual, o
  resultado com as leituras e preparações prévias realizadas para execução destes estágios, e o
  aprendizado com a implementação do estágio 18. Avalie se as etapas pendentes do plano destes
  estágios é exequível e faça os ajustes necessários. Faça a preparação necessária para a execução
  destes estágios com tudo o que pode ser feito sem que seja necessário subir o ambiente. Usuário infra
  sso logado para as leituras."*
- **[Claude] The instruments, between 22:00 and 22:10**: `./aws/cicd.py` on the three profiles 0 FAILED,
  `CI-2` to `CI-9` passing, `CI-1`, `CI-6` notes; `./aws/egress.py` 0 FAILED, the burn 0.000 USD/h in
  the six profiled accounts, no interface endpoint and no NAT gateway anywhere. `make up ENV=staging
  ONLY=egress PROFILE=awsds-deploy-staging AUTO=1 DRY=1` prints `staging/egress/` alone, and `make down
  ENV=staging PROFILE=awsds-deploy-staging AUTO=1 DRY=1` prints `orchestration`, `app/app-etl`, then
  `egress`, each `gen-tfvars.py --pipeline`; `gen-tfvars.py --pipeline staging app/app-etl` writes the
  registry profile as `awsds-prod-runner-deploy`, the laptop form `awsds-infra-prod`. The deploy image's
  recipe rewrites `git@github.com:` to HTTPS (`insteadOf`), so the module sources by tag resolve on the
  runner; the two `release.auto.tfvars.json` files the legs write are ignored by git.
- **[Claude] Stage 10 2.3's lint in the legs**: `scripts/release-application.py` gains `--lint`, which
  runs `awsds-workflows lint <rendered copy> --promoted --prefix s3://<bucket>/applications/<app>/<tag>/
  --image-repository $IMAGE_REPO --instance-type <each of LINT_INSTANCE_TYPES>` on every rendered
  workflow before a byte is written, the tool from `AWSDS_WORKFLOWS` (`uvx --from`) or `PATH`; an empty
  variable fails the job. The first draft read the repository off the image URI, and the negative
  control passed a `dev-env` image on its own repository name: the repository is the pipeline's
  `IMAGE_REPO` since. Both legs pass the flag, and `staging-deploy` keeps
  `staging/orchestration/release.auto.tfvars.json` as an artifact with a `cat`, which it did not: the
  Staging `VersionId`s 3.7 records would have died with the job. `check-gitlab-ci.py` `OK`.
- **[Claude] The lint read offline**, 22:14 to 22:16, against the stored `v0.2.1` bundle (read as
  `awsds-infra-prod`, SHA256 `7fb374d1…5fff`, the log of 2026-10-19's) and Staging's live state as
  `awsds-infra-staging`, with a stand-in digest: `release-application.py staging … --lint --dry-run` rendered
  the workflow, the lint read `ok: 1 arquivo(s)`, seven objects and the manifest were listed, the YAML the
  one file whose SHA256 differs from the bundle's; with `LINT_INSTANCE_TYPES` empty the run was refused
  before the lint; with the image under `awsds-prod-ecr-dev-env` the lint refused *"ImageUri do
  repositório awsds-prod-ecr-dev-env, e não de awsds-prod-ecr-app-etl"*, exit 1.
- **[Claude] 3.8**: the by-hand sequence written into the step, for a re-apply after 3.7 (no copy, the
  objects persist) and for a tag the pipeline never promoted (the copy first, with `--lint`).
- **[Claude] The plan**: the Status row, 3.2, pass 4's code bullet, 3.8 and Validation 2.

## 2026-10-23 — the session's branch and its PR

*Claude, the same session; no AWS call.*

- **[Claude] The PR**: the sitting's first commit opened PR #247 against `main` on 2026-10-22 at
  22:4x UTC, and every later commit of the session joined it: Stage 9's 5.1 applies, its 6.3 from the
  approval to the refusal read in the trail, and the records. The description was rewritten on
  2026-10-23 to carry the whole branch.

## 2026-10-23 — the fourth sitting with the environment down: the sittings in order, the GitLab acts before the tag

*Claude's hand, in the session `stages-8-9-10-prep-2`, on the user's request quoted in Stage 9's entry of
the same sitting. AWS read as the infrastructure user (`awsds-infra-prod`, `awsds-infra-staging`,
`awsds-infra-sandbox-1`, `awsds-infra-data`, `awsds-infra-identity`), reads only, the tunnel down. Nothing
applied. Times UTC.*

- **[Claude] `./aws/cicd.py`**, 16:19: *"all checks passed"* on the five infrastructure profiles;
  `./aws/egress.py` at 16:23: the burn 0.000 USD/h in the five accounts, no interface endpoint, no NAT
  gateway. `make check` OK at 16:17 on `main`'s tree.
- **[Claude] The laptop's Terraform**: `terraform version` reads 1.15.8, so the bump of 2026-10-22 waits on
  the user's install, and the two pins (`offline-gates.yml`, the deploy image's recipe) stay at 1.15.8 by
  `upstream-releases.md`'s order.
- **[Claude] Pass 4's sittings written in order**: [`runbooks/promotion.md`](../plan/runbooks/promotion.md),
  §H the hub and GitLab (decision 2's settings and the memberships, MR !4, the legs' merge request built
  from `examples/app-etl/` at `main` by `gitlab.md`'s "The application template" procedure,
  `default-v0.9.0` as version 10, the deploy image on 1.16.6), §T the tag with Stage 10's passes 1 and 2
  and Stage 9's 8.5, job by job, with what each leg reads for the first time; `waiting-on-the-user.md`'s
  GitLab row carries the legs' merge request.
- **[Claude] The plan**: the Status row.

## 2026-10-23 — 3.8 by hand before the pipeline's leg: the release `v0.2.1` written into Staging

*Claude's hand, on the user's authorization in chat (*"pode prosseguir com o plano"*, after the leg was
spelled out command by command), as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-staging` for the writes, `awsds-infra-prod` for the bundle and the image digest);
Staging's `egress/` up (Stage 9's log), Production coming down. Times UTC.*

- **[Claude] The inputs**: the bundle `s3://awsds-prod-releases/app-etl/v0.2.1/app-etl.zip`, 6,988
  bytes, SHA256 `7fb374d15c23953cb6ad6d9f5473f97d2c83ff2db167703a5a830d96add95fff` computed on the
  download, seven files inside (`code/app-etl.zip`, three under `src/app_etl/`, `glue/transform.py`,
  `samples/trades.csv`, `workflows/app-etl.yaml`); the image `awsds-prod-ecr-app-etl` tagged
  `v0.2.1-1e756091`, digest `sha256:247ec6b661ceb03d2927e1ce5a3c07d9287280a639abed18ce8daf898ed4ce0c`,
  pushed 2026-10-19 19:27 UTC; the pipeline's three variables exported by hand (`IMAGE_REPO`,
  `LINT_INSTANCE_TYPES`, `AWSDS_WORKFLOWS`).
- **[Claude] The dry run** at 22:45:01, exit 0: the render from Staging's live state, the promoted lint
  *"ok: 1 arquivo(s)"*, seven objects and the manifest listed, the YAML the one file whose SHA256 differs
  from the bundle's (`5b7900ee…` to `d367ab29…`, 3,351 bytes), the inbox seed listed.
- **[Claude] The release** at 22:45:11 to 22:45:42, exit 0: eight objects written under
  `s3://awsds-staging-outputs/applications/app-etl/v0.2.1/`, the seven and `MANIFEST.sha256`, *"read
  back: 8 objects, each checksum the manifest's"*; the inbox `inbox/app-etl/trades.csv` written; the
  orchestration slice's `release.auto.tfvars.json` carries `definition_version_id`
  `SdX0AVkSy1aoIiHQMcvDMC8vQvzfXYwe` and `code_version_id` `NSfKoAyWNRb0FS6R6BlVtIwAAUDpu5jM`, the
  values 3.7 records; the application slice's release file written by hand from the tag, the digest and
  the SHA256.
- **[Claude] The two applies**, each from a fresh plan (Recipe A), as `awsds-infra-staging`:
  `staging/app/app-etl/` planned at 22:47:04 *"1 to add"* and applied at 22:47:13, the Glue job
  `awsds-staging-app-etl` created in 1 s, re-planned `No changes`; `staging/orchestration/` planned at
  22:47:39 *"21 to add, 0 to change, 0 to destroy"* and applied 22:47:39 to 22:48:02, every resource of
  `orchestration-v0.1.0` with the release: the workflow `awsds-staging-wf-app-etl-hHNGu2YFTv` (the
  `awscc` resource, created in 7 s), the machine `awsds-staging-chain-app-etl`, the schedule in the
  group `awsds-staging-chains`, the roles `awsds-staging-wf-app-etl`, `-chain-exec`, `-chain-scheduler`
  and `-chain-events`, the workers' group `sg-0f4a4308a0ac1e29a`, the log groups `/awsds/staging/wf/app-etl`
  and `/aws/vendedlogs/states/awsds-staging-chains`, the two failure rules and their targets;
  re-planned `No changes`. The classifier let both applies through on the user's authorization in chat.
- **[Claude] The chain, 22:49 to 22:52**: `FAILED` at the first task, the worker refused
  `kms:GenerateDataKey` on the data key while encrypting its XCom after its Glue job had succeeded
  (Stage 10's log carries the run, the task log and the trail); the fix is the data key's statement for
  the `awsds-<env>-wf-*` roles, in both deployment targets. Verification xi's parity reading waits for the
  pipeline's leg; what this leg proved so far: the release path, both slices' applies, the machine's start
  and diagnosis, the Glue job on the release's script.
- **[Claude] 3.8's chain, at the third execution** (23:21 to 23:36, after the data keys' and the
  execution role's `GenerateDataKey`, Stage 10's log): `SUCCEEDED` end to end, the Glue job, the
  processing job on the release's image, the summary and `app-etl/outbox/report.json` (10 rows). The
  by-hand sequence of 3.8 is proven before the pipeline's leg: `make up ENV=staging ONLY=egress`, the
  release written, the two applies, the chain started and followed; what it could not prove is the
  pipeline's own half, `uv run` on the runner and the deploy role's calls against its grants (Stage 10
  verification ii), and xi's parity, which the pipeline's leg reads against these objects.
- **[Claude] 3.4's `make down ENV=staging`** (`AUTO=1`, 23:41:56 to 23:50:25): the three `[E]` slices
  destroyed in rank order, `orchestration/` *"21 destroyed"* (the machine took 80 s to go), `app/app-etl/`
  *"1 destroyed"*, `egress/` *"16 destroyed"*; the four `[P]` slices refused as always. After it, at
  23:53: `./aws/egress.py awsds-infra-staging` reads no interface endpoint and no NAT, `EG-5` *"none - the
  correct between-sessions state"*; 0 workflows, 0 state machines, the Glue job gone; `make status` reads
  every `[E]` slice down and the burn 0.0156 USD/h, the hub's two hosts alone, whose `make hub-down` is the
  user's. What the leg leaves in Staging: the release tree, the inbox seed, `app-etl/work/` and
  `app-etl/outbox/report.json` in the `[P]` outputs bucket, the data key's amended statement, and the
  service-linked role; `release.auto.tfvars.json` in both slices, gitignored, carries the `VersionId`s for 3.7.

## 2026-10-24 — the template's pin at `ff25eae` and the plan lint in the legs

*Claude's hand, in the session `awsds-workflows-ff25eae-plan`, on the user's request pasted in chat (a
prompt the project's cloud session wrote after `awsds-workflows` PR #23), which authorised plans and
reads as the infrastructure user (`awsds-infra-staging`, `awsds-infra-prod`, `InfrastructureAccess`) and
no apply. The plans, their JSON and the stand-in release's tfvars stayed under `$TMPDIR`; nothing was
applied or written in AWS, nothing done in GitLab. Times UTC.*

- **[Claude] The starting point**, 00:58: `origin/main` at `1d3a5f2`, the template's `AWSDS_WORKFLOWS` at
  `3c1708e`; `awsds-workflows` PR #23 merged at 00:38:02 as `ff25eae`, that repository's `main`. Asked
  whether `runbooks/promotion.md` §H step 2 had run, the user asked Claude to verify it: the legs' merge
  request cannot exist, since `awsds-prod-gitlab` is `stopped` since 2026-10-22 01:01:50 and the legs
  reached `main` with PR #244 at 2026-10-22 21:38:07, so this PR's `examples/app-etl/` is the MR's
  source.
- **[Claude] The pin** moved to `ff25eae`; the template's own line at 01:04:22, offline, the seven
  instance types and `--image-repository awsds-prod-ecr-app-etl`: *"ok: 6 arquivo(s)"*, exit 0.
- **[Claude] `scripts/lint-plan.py`**, beside `release-application.py`: `lint-plan.py <account> <plan.json>
  --tag <tag>` reads the outputs bucket from `data/`'s state as the release job does, builds
  `s3://<bucket>/applications/<app>/<tag>/glue/` and runs `awsds-workflows lint-plan` from
  `AWSDS_WORKFLOWS` or PATH; a plan leaving no `aws_glue_job` fails after the tool's `ok: 0 job(s)`
  (Lesson 71), and so does an empty bucket name. The legs: `staging-deploy` and `production-deploy` plan
  `app/app-etl/` with `-out` into `mktemp -d`, write `show -json` beside it, lint it and apply that plan;
  `production-plan` lints its plan, so a refusal stops the pipeline before the gate; `orchestration/`
  unchanged. `check-gitlab-ci.py` OK, 40 script items through `bash -n`; ruff passes.
- **[Claude] The script on fabricated plans**, 01:13:27, a stand-in `aws` serving `data/`'s state:
  exit 0 for a created job and a kept one under `v0.2.1`'s prefix; exit 1 for another tag's prefix, a
  PyPI module (`pandas==2.2.3`), an `--extra-py-files` item outside, a script unknown in the plan,
  Production's bucket on Staging's plan (each a `glue` refusal), a state and a non-JSON file (`forma`), a
  plan with no Glue job and one deleting it (the tool's `ok: 0 job(s) do Glue: -`, the script's failure),
  a state without `outputs_bucket_name`, no tool, and the laptop's installed tool, still at `c9a4c20`
  (*"invalid choice: 'lint-plan'"*); exit 2 for a tag that is not `vX.Y.Z`.
- **[Claude] The release's promoted lint at the new pin**: the bundle
  `s3://awsds-prod-releases/app-etl/v0.2.1/app-etl.zip` downloaded as `awsds-infra-prod` at 01:17:26,
  6,988 bytes, SHA256 `7fb374d1…5fff`, the logs' value. `release-application.py staging … --lint
  --dry-run` (01:17:38 to 01:17:45, `AWSDS_WORKFLOWS` at `ff25eae`, `IMAGE_REPO` and the seven types):
  *"ok: 1 arquivo(s)"*, seven objects and the manifest listed, the rendered YAML `5b7900ee…` as 3.8's,
  exit 0, nothing written. The same for Production (01:18:06 to 01:18:14): *"ok: 1 arquivo(s)"*, the
  rendered YAML `fc79af2b…`, 3,324 bytes, exit 0.
- **[Claude] Verification xiv at `ff25eae`**, 01:18:49 to 01:20:01: Staging's rendered copy of the
  template's workflow (the source `d367ab29…`, the bundle's) `ok: 1 arquivo(s)` in the promoted mode; each
  of rule (6)'s five keys put back on its Glue task refused under `glue`, exit 1, and the unrendered source
  in the promoted mode refused sixteen times, rule (6) naming all five; a copy of `examples/app-etl/` with
  `include: code/*.zip` refused under `manifest`, *"é um glob, que o bundle não expande"*, exit 1, the
  untouched copy `ok: 6 arquivo(s)`; a rendered copy with a `dev-env` image and `ml.m5.2xlarge` `ok` without
  the two options and refused twice with them. `lint-plan`'s refusals on the two application slices' plans
  are Stage 10's entry of this date. The 40 violations of 2026-10-18 were not run again.
- **[Claude] The texts**: the plan's 3.2, 3.5, 3.6, pass 4's bullets, 5.6 with its table, the bundle's
  include item and xiv, and the Status row; the template's `.gitlab-ci.yml` comments, `manifest.yaml`'s
  header and `README.md`; the root `README.md`; `runbooks/serverless-workflows.md` §T (the `lint` row,
  a `lint-plan` row, and a `prepare-offline` row, in the package since 2026-10-13 and missing from the
  table, outside PR #23); `runbooks/promotion.md` §T.

## 2026-10-24 — the deploy and test runners' load history, read against their instance type

*Claude's hand, in the session `gitlab-runners-instance-analysis`, on the user's request in chat (the
runners' load history, whether their instance types fit, and the types to use), as the infrastructure user
(`awsds-infra-prod`, `InfrastructureAccess`). Reads only. Times UTC; GitLab and the build runner are Stage
7's log entry of the same date.*

- **[Claude] The method**: each instance's running window from CloudTrail's `RunInstances` and
  `TerminateInstances` in Production, CloudWatch's `AWS/EC2` metrics at five minutes over it (a point's
  `Maximum` is its busiest minute), the newest instances' kernel console (`get-console-output --latest`),
  and the Price List Query API's offer of 2026-10-23T22:13:55Z. Neither runner runs the CloudWatch agent,
  so memory has no history.
- **[Claude] The deploy runner (decision 4) and the test runner (decision 11), both `t3a.small`**: 11
  deploy-runner instances, 27.26 h from 2026-10-13 03:59, and 8 test-runner instances, 25.53 h from
  2026-10-14 16:22, to 2026-10-22 00:53. Past the first 15 minutes the deploy runner averaged 0.8% (p95
  2.2%, peak 9.8%) and the test runner 1.1% (p95 5.3%, peak 16.1%), against a 20% baseline; the boot
  (packages, registration, the image pull) peaks at 38-40% over five minutes and about 60% in its busiest
  minute, about one vCPU. Each instance starts with no credits, T3a having no launch credits, borrows 0.4
  to 2.6 surplus credits at its boot and repays them within the session; nothing was charged. The disk
  stayed under 50 IOPS and 4 MB/s at p95 (peak 131 IOPS and 12 MB/s), the network under 3.5 MB/s. The
  console of both runners' 2026-10-19 and 2026-10-21 instances holds no OOM-killer line (the test runner's
  from 4,104 s and 278 s of uptime, the 64 KB window).
- **[Claude] The verdict** (analysis, prices from `docs/PRICING.md` §8): `t3a.small` fits both. After the
  boot the CPU never reaches the baseline; memory, 2 GiB, is what the size buys and is unmeasured.
  `t3a.micro` (1 GiB, 0.0094 USD/h) halves it on no reading, and `t3a.medium` (4 GiB, 0.0376), which both
  variables admit, would follow a memory reading of the test runner running two jobs at once.

## 2026-10-24 — the legs' calls replayed as the deploy roles, and the grant they lack

*Claude's hand, in the session `stages-8-9-10-prep-f13bc2`, on the user's request quoted in Stage 9's entry
of this date. AWS read as the infrastructure user with `InfrastructureAccess`, reads, simulations and plans
only, the tunnel down. Nothing applied. Times UTC.*

- **[Claude] `./aws/cicd.py`** on the five infrastructure profiles at 02:05: all checks passed, `CI-1` and
  `CI-9` notes (both runners absent, `[E]`), `CI-6` *"N = 1"*, `CI-8` the three assumptions of 2026-10-13.
- **[Claude] 3.8's calls replayed** through the policy simulator as `awsds-deploy-staging` and
  `awsds-deploy-prod` (Stage 10's log carries the method and the readings): the legs would have stopped at
  `staging/orchestration/`'s and `production/orchestration/`'s applies, the provider's plan of the state
  machine calling `states:ValidateStateMachineDefinition`, which neither role holds; Staging's role also
  lacks the `iam:CreateServiceLinkedRole` the workflow service calls with its role in place. Every other
  call of `staging-up`, `staging-deploy`, `staging-down` and their Production twins reads `allowed`.
- **[Claude] 4.1's grant amended**: `apply-orchestration.tf` (both copies, `check-copies.py`) and Staging's
  `deploy-role.tf`; `staging/foundation/` and `production/foundation/` each planned *1 to change* with the
  alerts var-file, the applies the user's, before the tag (`runbooks/promotion.md` §0.5 and §T).
- **[Claude] The plan**: the Status row (a sentence of 2026-10-23 joined to the next without a stop,
  separated).

## 2026-10-24 — 4.1's amended grant applied in Staging and Production

*Claude's hand, on the user's authorization in chat, as the infrastructure user with
`InfrastructureAccess`; Stage 10's log of this date carries the plans, the applies and the simulator's
readings. Times UTC.*

- **[Claude] The applies**: `staging/foundation/` at 02:52:30 and `production/foundation/` at 02:53:36,
  each *"0 added, 1 changed, 0 destroyed"* on `awsds-<env>-deploy-orchestration-resources`, each
  re-planned `No changes`; both deploy roles read `allowed` for `states:ValidateStateMachineDefinition`
  and the MWAA Serverless service-linked role. `runbooks/promotion.md` §0.5's first item is done, and §T
  no longer waits on it.

## 2026-10-24 — v0.4.0's legs written; verification xxii's substituted bundle refused offline

*Claude's hand, in the session `planejamento-estagios-8-9-10-847863` (Stage 9's entry of this date quotes
the request), no AWS write. Times UTC.*

- **[Claude] The branch synced** at the user's word: fast-forwarded to `0236a99d` (PR #253, the runbooks
  review); nothing of the branch was committed yet.
- **[Claude] The template's v0.4.0 legs**: `build-task-code` zips `code/app_etl_tasks.py` once per
  workflow; `test-deploy` requires the CI/CD variable `TRAINING_IMAGE_URI` (the user adds it, the value
  `terraform output -raw training_image_uri` on `staging/sagemaker/`); `staging-test` follows both
  chains and reads the application's table; `staging-model` serves Staging's model; after
  `production-deploy`, the manual `production-warehouse-ddl`, `production-register` and
  `production-approve`, then `production-transform`. `check-gitlab-ci.py` OK; the template's 27 tests and
  its lint pass.
- **[Claude] Which template each tag carries**: v0.3.0, the first promotion, is `examples/app-etl/` at
  `0236a99d`; v0.4.0 is `examples/app-etl/` at `main` once this branch is merged.
- **[Claude] Verification xxii's substituted-file half**, 17:31:02, offline: `release-application.py
  staging` handed a bundle of other files with `v0.2.1`'s SHA256, under a profile that does not exist,
  answered *"SHA256 differs from the value the tag pipeline passed"* and exit 1, before reading a state,
  rendering or writing. The `release.tf` half stays 3.7's.
- **[Claude] The peer's note**: Stage 8 3.6 and Stage 9 2.4 and 9.1 wrote the bare `make up
  ENV=production`, which applies `production/runners/` without `BUILD=1` and destroys the build runner;
  they now carry the `ONLY=` forms.

## 2026-10-24 — the session's branch and its PRs

*Claude's hand.*

- **[Claude]** The branch `claude/planejamento-estagios-8-9-10-847863` pushed and PR #254 opened against
  `main`; `awsds-workflows`' branch `treino-e-repositorio-de-algoritmo` pushed and its PR #24 opened, the
  merge of both the user's.

## 2026-10-24 — `runbooks/promotion.md` §H: the environment up, the mirror at `0236a99d`, the legs on `main`

*The user's hand for the environment and every GitLab act; Claude's for the readings, as the
infrastructure user with `InfrastructureAccess` (`awsds-infra-prod` and the four other infrastructure
profiles), reads only, and git reads over the tunnel. Times UTC.*

- **[user]** *"Subi o hub e o GitLab (make hub-up, make gitlab-up BUILD=1) e liguei o túnel."* **[Claude]
  read back**, 18:14 to 18:27: `make status` names `production/vpn/`, `production/proxy/` and
  `production/tooling/` up with one instance each, `production/egress/` with 12 resources and
  `production/runners/` with 13 (the instances launched 18:10:11 to 18:13:17: `t3.nano`, `t3.micro`,
  `t4g.large`, two `t3a.small` and the `m8i.xlarge` build runner), the burn estimated at 0.4521 USD/h;
  `./aws/cicd.py` on the five profiles, 0 checks failed (`CI-1` the deploy runner running, `CI-9` the
  test runner with IMDSv2 required and hop limit 1, its role holding its token, the CA root and Session
  Manager alone). The mirror `awsds/infrastructure` read at `5b9de6b8` (PR #151), an ancestor of
  `0236a99d` 102 commits behind it, so the push was a fast-forward; `awsds/app-etl`'s `main` at `v0.2.1`
  (`1e756091`) with MR !4 open.
- **[user]** *"Fiz os atos do §H: o espelho em 0236a99d, as configurações e memberships, o MR !4 e o MR
  das pernas mesclados, e a variável TRAINING_IMAGE_URI criada."* **[Claude] read back** at 18:43: the
  mirror's `main` at `0236a99d5577b0925e3cd87cbdde238ea6098bba`; `awsds/app-etl`'s `main` at `628f17e`,
  MR !4's merge, with the legs' branch `promotion-legs` (`6a342bc`, MR !5) not in it, its tree identical
  to `examples/app-etl/` at `0236a99d`. The tag was held until the merge.
- **[user]** *"Mesclei o MR !5 na main do awsds/app-etl."* **[Claude] read back** at 18:47:53: `main` at
  `5a7d009a` (*"Merge branch 'promotion-legs' into 'main'"*), its tree identical to `examples/app-etl/`
  at `0236a99d` (`diff -r` against `git archive`), seven `staging-*` and `production-*` jobs, the lint at
  `awsds-workflows` `ff25eae`. The job token's allowlist, the deployment managers' seat and the variable
  `TRAINING_IMAGE_URI` are GitLab settings no read here reaches; the legs' clone of the mirror and
  v0.4.0's `test-deploy` read them.

## 2026-10-24 — `v0.3.0`'s pipeline #64: `test-deploy` passed, the release and the legs refused the lab's CA

*The user's hand for the tag and the egress; Claude's for the reading, through the user's Chrome session
in a tab of its own (the job pages and their raw traces), and as the infrastructure user with
`InfrastructureAccess` for AWS. Times UTC.*

- **[user]** The tag `v0.3.0` on `5a7d009a`, after `make up ENV=sandbox ONLY=egress`; *"falhou no job de
  release."* Pipeline #64, 15 jobs, 19 min 20 s: `pip-audit`, `test`, `build-image` (2 min 49 s),
  `build-task-code` passed; `scan-gate` failed and is allowed to (decision 1); `test-deploy` passed in 15
  min 49 s as `awsds-deploy-sandbox-test`; `store-bundle` passed, the bundle
  `s3://awsds-prod-releases/app-etl/v0.3.0/app-etl.zip`, SHA256 `2c6b7dd4…3705`, the image
  `awsds-prod-ecr-app-etl@sha256:7d18db09…0e61`.
- **[Claude] `release` (job 280)**, 19:19:49: glab logged in with the job token and stopped at its first
  API call, *"Get "https://gitlab.awsds.internal/api/v4/projects/awsds%2Fapp-etl/releases/v0%2E3%2E0":
  tls: failed to verify certificate: x509: certificate signed by unknown authority."* Verification xx's
  open half is answered: GitLab's `cli` image does not trust the lab's CA.
- **[Claude] `staging-up` (job 281)**, 19:19:47, on the deploy runner: the `.promotion` clone of the
  mirror refused, *"fatal: unable to access 'https://gitlab.awsds.internal/awsds/infrastructure.git/':
  server verification failed: certificate signer not trusted. (CAfile:
  /etc/ssl/certs/ca-certificates.crt CRLfile: none)"*, exit 128; `staging-down` (job 284) the same, so
  `staging-deploy`, `staging-test`, `production-plan`, the gate and `production-deploy` were skipped.
  Staging holds no interface endpoint (read 19:3x), so the leg raised nothing. The project's own checkout
  passed in both jobs: the runner's helper installs the CA root it mounts at
  `/etc/gitlab-runner/certs/ca.crt`, and `runbooks/gitlab.md` §K leaves every other HTTPS call to
  GitLab to use that file itself, which the legs, never run in a pipeline before, did not.
- **[Claude] The fix**, in the template's `.gitlab-ci.yml`: the `.promotion` clone carries `-c
  http.sslCAInfo=/etc/gitlab-runner/certs/ca.crt`, and `release` sets `SSL_CERT_DIR` to the mounted
  directory, which Go reads beside the image's bundle. The same two hunks apply to v0.3.0's template
  (`0236a99d`, checked with `git apply --check`) and to v0.4.0's; the tag `v0.3.0` is spent, so the
  first promotion is `v0.3.1`.

## 2026-10-24 — `v0.3.2`'s pipeline #68: the release trusted the CA, the Staging leg stopped three times on the deploy runner

*The user's hand for the tags, the merge request and the retry; Claude's for the reading, through the
user's Chrome session (the job pages, their raw traces and GitLab's API), and as the infrastructure user
with `InfrastructureAccess` for AWS. Times UTC.*

- **[user]** *"Apliquei o patch, mesclei o MR ca-root e criei a tag v0.3.1; o pipeline está rodando."*
  **[Claude] read back**: `v0.3.1` named `5a7d009a`, MR !5's merge, because the branch `ca-root`
  (`780aa419`, pipeline #65 passed at 19:36:10) had no merge request yet; pipeline #66 ran the v0.3.0
  template again. The user cancelled #66 (19:44:19) and merged MR !6, *"The legs' clone and the release
  trust the CA root the runner mounts"*, at 19:45:20 as `f4e4dcf3`; its `.gitlab-ci.yml`, blob
  `74cae03f`, is the template at `0236a99d` with the patch. `v0.3.1` is spent.
- **[user]** The tag `v0.3.2` on `f4e4dcf3`, pipeline #68 created 19:46:13. `scan-gate` (job 319) failed
  and is allowed to (decision 1): 725 CRITICAL or HIGH findings, 130 in the baseline, 595 outside it,
  593 of them `linux-libc-dev 6.8.0-142.142` and one each `zlib` and `zlib1g 1.3.dfsg-3.1ubuntu2.2`.
  `test-deploy` (job 320) passed, 19:49:17 to 20:05:00; `store-bundle` (321) passed; `release` (322)
  passed at 20:05:17, glab trusting the CA through `SSL_CERT_DIR` (verification xx answered).
  `staging-up` (323) passed, 20:05:10 to 20:07:16, the mirror's clone at `0236a99d`, and Staging's seven
  interface endpoints read `available` at 20:07:31.
- **[Claude] `staging-deploy` (job 324)**, 20:07:19 to 20:09:57: the tree written to
  `s3://awsds-staging-outputs/applications/app-etl/v0.3.2/`, the promoted lint `ok`, 8 objects read
  back; `staging/app/app-etl/` applied, the Glue job; `staging/orchestration/` stopped at the workflow,
  *"not authorized to perform: airflow-serverless:TagResource on resource: … workflow/*"*. The refusal,
  its fix and its applies are Stage 10 1.5's, in that log's entry of this date.
- **[Claude] `staging-down` (job 326)**, 20:10:00 to 20:10:15: `make down ENV=staging
  PROFILE=awsds-deploy-staging AUTO=1` stopped at step 8.6's hook before any destroy, *"could not list
  domains in staging (awsds-infra-staging) … The config profile (awsds-infra-staging) could not be
  found"*: `down-studio-apps.py` signs in with `backend.PROFILES`, which the deploy runner does not hold.
  The fix, in `c60ad8d6`: with a deploy profile, `slices.py down` skips the hook and prints why (refusal
  8 keeps the profile in the Workloads accounts, where `DenyInteractiveSageMakerSurface` refuses
  `CreateDomain` and `CreateApp`). It reaches the runner with the mirror's next push.
- **[user]** *"Cliquei em Retry no staging-deploy (job 324)."* **[Claude]** Job 330, 20:32:33 to 20:35:03,
  passed: the mirror at `0236a99d`, the tree written again, the application slice `No changes` after
  `lint-plan`, the orchestration slice *"Apply complete! Resources: 7 added, 0 changed, 0 destroyed."*
  (Stage 10's log). `staging-test` (job 325), 20:35:06 to 20:35:14, failed before its first AWS call:
  *"fatal: destination path '/builds/awsds/app-etl/infrastructure' already exists and is not an empty
  directory."* Its `needs: [staging-deploy]` downloads that job's artifact,
  `infrastructure/terraform-live/staging/orchestration/release.auto.tfvars.json`, before the `.promotion`
  clone into the same folder; `staging-down` downloads it too, by stage, and `production-deploy`'s artifact
  sits on the same path for v0.4.0's jobs that need it. A retry runs the tag's YAML, so the fix needs a
  new tag.
- **[Claude] The template's fix**: each deploy job copies the release file beside the clone,
  `staging-release.auto.tfvars.json` and `production-release.auto.tfvars.json` in `$CI_PROJECT_DIR`, and
  keeps that copy as the artifact; written in `examples/app-etl/.gitlab-ci.yml` (v0.4.0) and as a patch
  on `f4e4dcf3` for `v0.3.3`, both read by `./scripts/check-gitlab-ci.py` and parsed. Staging stays up
  meanwhile: the seven endpoints, the Glue job and the orchestration slice's 21 resources, the chain never
  started.

## 2026-10-24 — `v0.3.3`'s pipeline #71: the first promotion, Staging's leg `SUCCEEDED` and Production deployed

*The user's hand for the merge request, the tag, the gate and Staging's teardown; Claude's for the
reading (the job traces and GitLab's API through the user's Chrome session, AWS as the infrastructure
user with `InfrastructureAccess`) and for 3.7's record. Times UTC.*

- **[user]** The patch applied in `awsds/app-etl` on the branch `artifact-path` (`2b3da15b`, pipeline #69
  passed), MR !7, *"The legs keep their release file beside the clone"*, merged at 20:48:59 as
  `ff4caf1c`, its `.gitlab-ci.yml` blob `fd85db90`, the patched file. A first attempt ran the commands in
  the project folder, where `git apply` found no `.gitlab-ci.yml` and changed nothing: Claude's
  instructions had dropped the clone's `-C`. The tag `v0.3.3` on `ff4caf1c`, pipeline #71 created
  20:50:40.
- **[Claude] The build half**: `pip-audit`, `test`, `build-task-code` and `build-image` (20:51:01 to
  20:53:43) passed; `scan-gate` failed, allowed (decision 1); `test-deploy` 20:53:44 to 21:09:33;
  `store-bundle`; `release` at 21:09:49, its notes naming the bundle
  `s3://awsds-prod-releases/app-etl/v0.3.3/app-etl.zip`, SHA256 `24aea329…02e9`, and the image
  `awsds-prod-ecr-app-etl@sha256:89d0ea21…2aac`.
- **[Claude] The Staging leg**, the mirror at `0236a99d`: `staging-up` 21:09:42 to 21:10:25, no change;
  `staging-deploy` 21:10:28 to 21:12:59, the tree written and read back (8 objects, the promoted lint
  `ok`), the Glue job updated in place to v0.3.3 and the workflow *"Modifications complete after 6s"*
  through Cloud Control as `awsds-deploy-staging`; `staging-test` 21:13:02 to 21:28:39, the execution
  `v0-3-3-71` started by the leg and `SUCCEEDED` from 21:13:12 to 21:28:16, its artifacts
  `execution.json` and `staging-release.auto.tfvars.json`; `staging-down` 21:28:42 to 21:28:55 stopped at
  step 8.6's hook as on #68, its clone passing.
- **[user]** `make down ENV=staging`, after `DRY=1`, from the project folder at `0236a99d` as
  `awsds-infra-staging`. **[Claude] read back** at 21:37:43: no interface endpoint, workflow,
  `awsds-staging-chain-*` machine, Glue job `awsds-staging-app-etl`, `wf` or `chain` role, workers' group,
  schedule group or `/awsds/staging/wf/` log group, and no NAT gateway; the `[P]` rule
  `awsds-staging-deploy-misuse` kept.
- **[Claude] `production-plan`**, 21:28:55 to 21:29:39: *"Plan: 1 to add"*, `aws_glue_job.this[0]` named
  `awsds-prod-app-etl` on `s3://awsds-prod-outputs/applications/app-etl/v0.3.3/glue/transform.py`,
  `lint-plan` *"ok: 1 job(s) do Glue"*.
- **[user]** `production-gate` at 21:31:29. **[Claude] `production-deploy`**, 21:31:37 to 21:34:08 as
  `awsds-deploy-prod`: the tree written and read back, the inbox's `trades.csv` written at 21:32:24,
  before any bridge existed; the application slice *"1 added"* at 21:33:32; the orchestration slice
  *"21 added"* at 21:34:04 (Stage 10's log); the release file kept as
  `production-release.auto.tfvars.json`.
- **[Claude] 3.7, recorded in this repository**: both application slices' `release.tf` default to
  `v0.3.3` with the digest and the bundle's SHA256 of the tag's GitLab release; both orchestration
  slices' to the legs' `VersionId`s, Staging's `i1L7O01m…oOXm` and `mqDM5asD…eQal`, Production's
  `jU1vr4IL…eHZX` and `K.apAb_C…eBtxN`. Each object version read back by `head-object` (3,351 and 1,246
  bytes in Staging, 3,324 and 1,246 in Production), and Production's two match `get-workflow`. The
  mirror's push is the user's, after the merge.

## 2026-10-24 — the readings after the first promotion: `CI-8` and the verifications the run answers

*Claude's hand, as the infrastructure user with `InfrastructureAccess`. Times UTC.*

- **[Claude] `./aws/cicd.py`** on the five infrastructure profiles, after pipeline #71: *"0 check(s)
  FAILED"*; `CI-8` reads 97 deploy-role assumptions, every caller the deploy runner, the three deliberate
  assumptions of 2026-10-13 excused by session name and minute (verification vi, INT-08).
- **[Claude] What the stage file now records**: xi's parity (the leg's 21 orchestration resources and its
  chain's `SUCCEEDED` against 3.8's by-hand run, the tag-on-create the one difference); xii read as *no* at
  the mirror's `0236a99d`, `staging-down` stopping at the Studio hook after #68's failure and #71's success,
  Staging's slices up until the user's `make down`; xx's `release` jobs creating their releases with the CA
  root; xxii's `release.tf` half, the download checked against the SHA256 both application slices record;
  3.4 carries the hook's fix and its reach.
- **[Claude] Verification v's pass 4 half**, Production's trail: three `BatchGetImage` calls on
  `awsds-prod-ecr-app-etl` from Staging at 21:17:02, 21:17:03 and 21:17:52, each `AWSAccount` whose
  principal id is `awsds-staging-job-exec`'s with the session `SageMaker`, the last invoked by
  `ecr.amazonaws.com`: the processing job's role pulled the release's image across the boundary
  (INT-07). Production's own run pulled it at 21:44:50 as `awsds-prod-job-exec`, and one call at
  21:45:36 answered `InvalidParameterException` with no repository named, the run unaffected, as Stage
  18 read on 2026-10-19.

## 2026-10-24 — v0.4.0's merge request and pipeline #74: `test-deploy` read the wrong workflow's ARN

*The user's hand for the merge requests and the tags; Claude's for the patches and the readings (the job
traces through GitLab's API in the user's Chrome session, AWS as the infrastructure user with
`InfrastructureAccess`), in the session of `runbooks/promotion.md` §V (the branch
`claude/eloquent-ishizaka-04f598`). Times UTC.*

- **[Claude] §V step 2's inputs**: the mirror `awsds/infrastructure` read at `c714c47d` (`ls-remote`), PR
  #254's squash merge, which carries `c60ad8d6`'s three files; the patch from `awsds/app-etl`'s `main`
  (`ff4caf1c`, tree `1833426e`) to `examples/app-etl/` at `c714c47d`, 13 files, applied in a scratch
  repository and checked to give the tree `495b8953`.
- **[user]** The branch `data-release` (`8c8e8f48`), MR !8 merged at 22:25:23 as `edff65f9`, read back
  with the tree `495b8953`; the tag `v0.4.0` on `edff65f9`, pipeline #74 created at 22:30:07.
- **[Claude] Pipeline #74's build half**: `pip-audit` (job 370) and `test` (371) passed, 22:30:08 to
  22:30:25, ruff *"All checks passed!"*, *"27 passed"*, and the lint with `--algorithm-repository` *"ok: 9
  arquivo(s)"* on `awsds-workflows` `d60e1ad`; `build-task-code` (373) passed; `build-image` (372),
  22:30:28 to 22:33:12, *"== pushed …/awsds-prod-ecr-app-etl:v0.4.0-edff65f9@sha256:16165035…093f"*;
  `scan-gate` (374) failed, allowed (decision 1), *"CRITICAL and HIGH: 725 found, 130 in the baseline"*,
  the 595 outside it `linux-libc-dev 6.8.0-142.142`, `zlib` and `zlib1g`, as on #68.
- **[Claude] `test-deploy` (375)**, 22:33:15 to 22:49:01, failed after a deploy that worked: the bundle,
  15,638 bytes with both workers' packages and `glue/load_warehouse.py`; in the `test` project the workflow
  `app_etl_test_experimentation_app_etl` updated at 22:34:40 and `app_etl_test_experimentation_app_etl_train`
  created at 22:34:50; the run `GMzt8Abreb3WQCO` triggered at 22:34:52, *"Workflow triggered:
  app_etl_test_experimentation_app_etl (run_id: GMzt8Abreb3WQCO)"*, `SUCCESS` at 22:49:01. The job's
  `get-workflow-run` then answered *"An error occurred (ResourceNotFoundException) when calling the
  GetWorkflowRun operation: Workflow run not found"*, exit 254: the script took the last *"ARN:"* line of
  `deploy.log`, app-etl-train's, for app-etl's run. Every later job was skipped but `staging-down`.
- **[Claude] `staging-down` (382)**, 22:49:04 to 22:50:55, the mirror at `c714c47d`: the three `[E]`
  slices destroyed as `awsds-deploy-staging`, *"Destroy complete! Resources: 0 destroyed."* each, Staging
  being down, and step 8.6's hook *"skipped - a deploy profile acts in a Workloads account, which runs no
  Studio app"*. Verification xii's mechanism holds; its zero-burn half needs a leg that raised something.
- **[Claude] The fix**, in the template: `test-deploy` takes the workflow's name from the run line and the
  *"ARN:"* line carrying that name, read in `bash` and `sh` against the run's log lines (an absent run line
  yields the FATAL) and by `./scripts/check-gitlab-ci.py`. The same change moves `AWSDS_WORKFLOWS` to
  `d856982c`, `awsds-workflows` PR #24's squash merge, whose tree is `d60e1ad`'s (both archives `200`,
  315,757 bytes). The patch over `edff65f9` checked to give the template's tree `8974b06d`. The tag
  `v0.4.0` is spent; the data release is `v0.4.1`, and verification ix's drift takes `v0.4.2`.
- **[user]** MR !9 (`test-deploy-run`, `a9a1358f`) merged at 22:54:29 as `d1ee24cb`, read back with the tree
  `8974b06d`; the tag `v0.4.1` on `d1ee24cb`, pipeline #77 created at 22:55:06.

## 2026-10-24 — `v0.4.1`'s pipeline #77: `test-deploy` fixed, the Staging leg's governed read, `evaluate` stopped at its template, `staging-down` at zero

*The user's hand for the tag; Claude's for the readings (the job traces through GitLab's API in the
user's Chrome session, AWS as the infrastructure user with `InfrastructureAccess`). Times UTC.*

- **[Claude] The build half**: `pip-audit` (job 401) and `test` (402) passed, 22:55:08 to 22:55:29,
  *"27 passed"*, the lint on `awsds-workflows` `d856982c`; `build-image` (403), 22:55:32 to 22:58:15,
  *"== pushed …/awsds-prod-ecr-app-etl:v0.4.1-d1ee24cb@sha256:3032e812…7d42"*; `build-task-code` (404)
  passed; `scan-gate` (405) failed, allowed, the same 725, 130 and 595.
- **[Claude] `test-deploy` (406)**, 22:58:16 to 23:14:10, passed with the fix: *"Workflow triggered:
  app_etl_test_experimentation_app_etl (run_id: C1qEAcWUjr2puBg)"*, then *"deploy: exit 0, run
  C1qEAcWUjr2puBg of …workflow/app_etl_test_experimentation_app_etl-cu3XfT7WrY"*, the run `ON_DEMAND` and
  `SUCCESS` from 23:00:03 to 23:12:36; the bundle 15,638 bytes, SHA256 `0203d20f…3bed`.
- **[Claude] `store-bundle` (407) and `release` (408)**, 23:14:12 to 23:14:26: the bundle at
  `s3://awsds-prod-releases/app-etl/v0.4.1/app-etl.zip`, the release `v0.4.1` at 23:14:25 naming it, its
  SHA256 and the image.
- **[Claude] The Staging leg**, the mirror at `c714c47d`: `staging-up` (409), 23:14:19 to 23:16:56, the
  seven interface endpoints `available` at 23:16:28; `staging-deploy` (410), 23:16:59 to 23:20:08,
  *"bundle.zip: OK"*, the three workflows rendered and linted in the promoted mode (*"ok: 1 arquivo(s)"*
  each, `app-etl-warehouse` among them), *"read back: 12 objects, each checksum the manifest's"*, the
  application slice *"Plan: 2 to add"* (the Glue job and `app_outputs.trades_notional`), `lint-plan`
  *"ok: 1 job(s) do Glue"*, *"2 added"*, the orchestration slice *"31 added"*; `staging-test` (411), 23:20:11
  to 23:41:02: the app-etl chain `SUCCEEDED`, its Glue job `jr_4c6f4a78…ab71` from 23:21:15 to 23:22:57
  as `awsds-staging-job-exec`, *"reading SELECT trade_date, desk, instrument, quantity, price FROM
  lake.curated.trades"*, *"read 30 row(s)"*, the table written with 30 rows and the training sets with
  24, 6 and 30 lines, Staging's full-table flag unset (Stage 9 8.5's governed read); then the train
  chain `FAILED` at `evaluate`, *"FATAL: the chain app-etl-train ended FAILED"* (Stage 10's log: the
  task's template met the XCom as JSON text). `staging-model` and every Production job skipped: the
  gate's needs held Production untouched, verification ix's mechanism met by an unplanted defect.
- **[Claude] `staging-down` (413)**, 23:41:05 to 23:49:24, as `awsds-deploy-staging`: *"Destroy
  complete! Resources: 31 destroyed."*, *"2 destroyed."*, *"16 destroyed."*, the hook skipped.
  `./aws/egress.py awsds-infra-staging` after it: all checks passed, no interface endpoint and no NAT.
  **Verification xii answered yes**: after a failed leg that raised something, the teardown left Staging
  at zero burn.
- **[Claude] The fix** (`evaluate`, Stage 10's log), its patch over `d1ee24cb` checked to give the
  template's tree `e8c12563`, with the README's two sentences; the data release is `v0.4.2`, and ix's
  drift takes `v0.4.3`.

## 2026-10-24 — `v0.4.2`'s pipeline #80: the data release through Staging's leg, the gate and `production-deploy`

*The user's hand for MR !10, the tag and the gate; Claude's for the patch and the readings (the job
traces and artifacts through GitLab's API in the user's Chrome session, AWS as the infrastructure user
with `InfrastructureAccess`, whose session expired at 00:52 UTC and was renewed by the user with
`./aws/login.py`). Times UTC, the pipeline crossing midnight into 2026-10-25.*

- **[user]** MR !10 (`evaluate-xcom`, `cc62f13f`) merged at 23:51:31 as `863f30b1`, read back with the
  template's tree `e8c12563`; the tag `v0.4.2` on it, pipeline #80 created at 23:51:57.
- **[Claude] The build half**: `test` (434) passed; `build-image` (435), 23:52:28 to 23:55:12, *"== pushed
  …/awsds-prod-ecr-app-etl:v0.4.2-863f30b1@sha256:9735e42e…06fd5"*; `scan-gate` (437) failed, allowed;
  `test-deploy` (438), 23:55:15 to 00:11:09, the run `1DCL6kFnnjzKqX6` `SUCCESS`; `store-bundle` (439) and
  `release` (440), 00:11:11 to 00:11:26, the bundle `s3://awsds-prod-releases/app-etl/v0.4.2/app-etl.zip`,
  SHA256 `745955fa…cc3e`.
- **[Claude] The Staging leg**, the mirror at `c714c47d`: `staging-up` (441), 00:11:18 to 00:13:55;
  `staging-deploy` (442), 00:13:58 to 00:17:00, the same counts as #77 (*"2 added"*, *"31 added"*, the
  three workflows linted, 12 objects read back), its artifact's `VersionId`s `app-etl` `nHLndSk3…duuxA`
  and `53rV3UoC…hAINr`, `app-etl-train` `XubSXeT1…l9MsG` and `QvMe.XCe…fN61`, `app-etl-warehouse`
  `MDqIlYw8…YFQgVq`; `staging-test` (443), 00:17:03 to 00:39:56, both chains `SUCCEEDED` and the table read
  back; `staging-model` (444), 00:39:59 to 00:45:46, *"30 prediction(s), one per input row"*, the model
  deleted (Stage 10's log); `staging-down` (445), 00:45:49 to 00:51:28.
- **[Claude] `production-plan` (446)**, 00:51:28 to 00:52:19: *"Plan: 2 to add, 1 to change, 0 to
  destroy."*, `aws_glue_catalog_table.trades_notional[0]` and `aws_glue_job.load[0]` created,
  `aws_glue_job.this[0]` updated in place; *"ok: 2 job(s) do Glue: aws_glue_job.load[0],
  aws_glue_job.this[0]"*.
- **[user]** `production-gate` (447) at 00:54:31.
- **[Claude] `production-deploy` (448)**, 00:54:37 to 00:57:51, as `awsds-deploy-prod`: *"bundle.zip:
  OK"*, *"read back: 12 objects"*, *"inbox inbox/app-etl/trades.csv: unchanged"*, the application slice
  *"2 added, 1 changed"*, the orchestration slice *"20 added, 1 changed"*; its artifact's `VersionId`s
  `app-etl` `0zqwVd2e…pa5wBa` and `NiUAbhcu…p3HKKC`, `app-etl-train` `KYxMwRRM…ei.aGf1` and
  `8LwP7yZe…uKD1d`, `app-etl-warehouse` `GlCsV_FM…KMRB1`. Read at 00:58: the workflows
  `awsds-prod-wf-app-etl`, `-app-etl-train` and `-app-etl-warehouse` `READY`, modified 00:57:33 to
  00:57:37, and the three schedules `ENABLED`.

## 2026-10-24 — decision 27: the pipeline raises and destroys no shared slice

*Claude's hand, with the environment as the promotion sitting left it; every call a read. Times UTC.*

- **[user] The decision**, in chat, after the first promotion's legs were read: *"todo o estado
  compartilhado será gerenciado pelo usuário pelo make up, seja o ENV sandbox/staging/production"*. What
  it answers: a Staging `egress/` up/down cycle records about 200 AWS Config items, about 0.60 USD (107 in
  the 20:00 UTC hour of 2026-10-24 for one `staging-up` and two `staging-deploy` attempts,
  `docs/PRICING.md` §2 and §3), paid by every pipeline run; and `staging-down`'s `make down ENV=staging`
  destroys every `[E]` slice of the account, what the user or another application raised in the one
  state they share.
- **[Claude] The template** (`examples/app-etl/.gitlab-ci.yml` on this repository's branch; `awsds/app-etl`
  and the mirror untouched while §V's promotion runs on the current legs): `staging-up` became
  `staging-check`, `scripts/check-egress.py staging egress` as `awsds-deploy-staging`, which reads the
  slice's state and fails with `make up ENV=staging ONLY=egress` and the identity that runs it;
  `production-deploy` reads `workloads-egress/` the same way as `awsds-deploy-prod`, before the bundle;
  `staging-down` runs `make down ENV=staging ONLY=app/app-etl`, the application's slice alone,
  `orchestration/` staying up between legs (decision 27 says why). `check-gitlab-ci.py` passes.
- **[Claude] `check-egress.py` run by hand** as the infrastructure user, between 00:20 and 00:30 on
  2026-10-25: `staging/egress/` up, seven endpoints `available` and the DNS Firewall association
  `COMPLETE` (the promotion sitting's); `production/workloads-egress/` the same seven, up for 6.1's
  firing at 06:30; the Staging state read as `awsds-infra-prod` answered `403` on `HeadObject`, and the
  script exited 2 with the refusal's text, not "down" (Lesson 62).
- **[Claude] The scripts**: `layers.py` refusal 10, a deploy profile acts on an application slice and the
  orchestration slice alone; `make up ENV=staging ONLY=egress PROFILE=awsds-deploy-staging DRY=1` prints
  it on `staging/egress`, and `make down ENV=staging ONLY=app/app-etl PROFILE=awsds-deploy-staging DRY=1`
  lists the one destroy; `tfhygiene/states.py` gained `state_document`. `make check` OK.
- **[Claude] The grants, written and planned, not applied**: `awsds-deploy-staging` loses `apply-egress`
  and the `staging/egress/` state prefix; both deploy roles gain `DescribeTheEgressEndpoints` and
  `ReadTheDnsFirewallAssociation` in `apply-application`, and the egress slice's state as a read key.
  `staging/foundation/` planned *0 to add, 3 to change, 1 to destroy* (the role's description,
  `apply-application` and `state` changed, `apply-egress` destroyed); `production/foundation/` *0 to add, 3 to
  change, 0 to destroy* (the same three). A `terraform init` run beside pre-commit's `terraform_validate`
  in the same slice folder failed twice (`fetch-pack: invalid index-pack output`, then *Required plugins
  are not installed*) and passed alone. The applies wait for the mirror to carry the new legs: the
  narrowed role refuses the current `staging-up`.
- **[Claude, from §V's session] Readings on the orchestration slice staying up**, pipeline #77: the
  `evaluate` task's log (`/awsds/staging/wf/app-etl-train`) was read at about 23:43, minutes before
  `staging-down` destroyed the log groups with the slice; with the slice up between legs a failed
  execution's log survives until the user's `make down`. The slice accumulates workflow versions until
  then, each leg updating the workflow (the 50-version quota, `OR-7`), and the chains' executions,
  `<tag>-<pipeline>-<chain>`; the destroy took about 2 min and the recreate about 1 min. Recorded in
  decision 27.
- **[user] The teardown job removed, the same sitting** (2026-10-25 UTC): *"Vamos alterar a solução
  proposta para não precisar do `staging-down`. Desta forma, o staging vai funcionar de forma similar ao
  que já é feito no production."* The application slice is a Glue job definition and a catalog table,
  billing nothing at rest, so its destroy bought housekeeping and not cost; Staging holds the last
  release between legs, as Production, and the user's `make down ENV=staging` destroys the three `[E]`
  slices. The maintenance in GitLab (the MR, the mirror's push, the two applies) waits for §V's
  promotion to end, the user's instruction.
- **[user] A gate before Staging** (2026-10-25 UTC): *"peço criar um 'staging-gate' como etapa de
  aprovação para transição entre 'release' e 'staging', nos mesmos moldes do que existe hoje para
  'production-gate'"*. **[Claude]** written as decision 28: `staging-gate`, the stage `staging-gate`
  between `release` and `staging`, manual and blocking, `needs: [release, store-bundle, test-deploy]`,
  `resource_group: staging`; `staging-check` needs it. `check-gitlab-ci.py` passes.

## 2026-10-25 — `production-warehouse-ddl` retried; `v0.4.3`'s pipeline #82 for verification ix, cancelled by the user

*The user's hand for the retry, the tag and the cancel; Claude's for the readings (the traces through
GitLab's API in the user's Chrome session, AWS as the infrastructure user with `InfrastructureAccess`).
Times UTC.*

- **[user] `production-warehouse-ddl` retried** (job 454, 02:10:11 to 02:10:37), after the deploy role's
  `FollowItsOwnStatements` (Stage 9's log): both statements `FINISHED`, the read-back *"IAMR:awsds-deploy-prod"*
  and *"30"*. Verification xxii: the DDL runs again over the existing table; xxvii's reading half: the job
  follows its statement with `DescribeStatement`.
- **[user]** The branch `ix-governed-drift` (the drift patch, `GOVERNED_COLUMNS` with `book` and the tests'
  mock moved with it) and the tag `v0.4.3` on it, pipeline #82 created at 02:11:24 on `3e86c3c6`: `test` and
  `pip-audit` passed (02:11:40 to 02:11:58), `build-image` pushed `v0.4.3-3e86c3c6` (02:12:00 to 02:14:43);
  the user cancelled the pipeline at 02:15 during `test-deploy`, to deploy the promotion legs of PR #256
  first. **[Claude] read back** at 02:17: Staging holds no interface endpoint and no workflow, Production is
  untouched, and the `test` project's newest run is still `v0.4.2`'s `1DCL6kFnnjzKqX6`. The tag `v0.4.3` is
  spent; verification ix waits for the next tag on the new legs.

## 2026-10-25 — decision 27's grants applied in both `foundation/` slices, after PRs #255 and #256

*Claude's hand, on the user's authorization in chat (*"Autorizo os applies dos planos salvos de
production/foundation (0/3/0, awsds-infra-prod) e staging/foundation (0/3/1, awsds-infra-staging) e os
passos 4 e 5 do 9.5 no Sandbox (awsds-infra-sandbox-1)."*), as the infrastructure user with
`InfrastructureAccess`, from `main` at `79651026` (PR #256's merge, after PR #255's `f259e49a`), in the
session's second branch; PR #256's session and the planning session told before the writes. Times UTC.*

- **[Claude] The plans**, 02:31:52 and 02:32:25, each with the alerts var-file: `production/foundation/`
  *"Plan: 0 to add, 3 to change, 0 to destroy."*, the deploy role's description, `apply-application`
  gaining `DescribeTheEgressEndpoints` and `ReadTheDnsFirewallAssociation`, and the state policy reading
  `production/workloads-egress/terraform.tfstate`, with `FollowItsOwnStatements` absent from the diff;
  `staging/foundation/` *"Plan: 0 to add, 3 to change, 1 to destroy."*, the same two reads, the egress state
  moved from the role's writable prefixes to its read keys, and the inline policy `apply-egress` destroyed.
- **[Claude] The applies**: `production/foundation/` at 02:35:29, *"Apply complete! Resources: 0 added, 3
  changed, 0 destroyed."*; `staging/foundation/` at 02:36:00, *"Destruction complete after 3s"* for
  `apply-egress`, *"Apply complete! Resources: 0 added, 3 changed, 1 destroyed."*; both re-planned `No
  changes`; `./scripts/check-copies.py` OK. The simulator, `aws:RequestedRegion` in the context:
  `ec2:DescribeVpcEndpoints` `allowed` for both deploy roles, `route53resolver:GetFirewallRuleGroupAssociation`
  `allowed` on an association's ARN (`implicitDeny` on `"*"`, the grant naming the association's type), and
  `ec2:CreateVpcEndpoint` `implicitDeny`: neither role raises an egress slice any more.

## 2026-10-25 — decision 27's maintenance: the mirror and the legs' merge request

*Claude's hand, in the sitting the user and the §V session hold (the hub, GitLab and the tunnel up); the
user's authorization in this chat for each push. Times UTC.*

- **[user]** PR #256 merged at 02:28:08 as `79651026` (squash), after #255 (`f259e49a`, 02:22:28); this
  session's branch retired with it, and the maintenance's commits go on
  `claude/pipeline-app-slices-maintenance-55a372`, cut from `main`.
- **[Claude] The mirror**, `git push gitlab origin/main:refs/heads/main`, authorized at 02:37: *"Everything
  up-to-date"*, `awsds/infrastructure`'s `main` already at `79651026` at 02:37:56, pushed earlier by another
  hand (the §V session was asked; unanswered when this was written). The runner clones refusal 10 and
  `scripts/check-egress.py` from it.
- **[Claude] The legs' merge request**, MR !11 on `awsds/app-etl`: a fresh clone of `main` (`863f30b1`, the
  template's tree `e8c12563`, v0.4.2) into `$HOME/tmp/app-etl-legs-27`, the files swapped from
  `examples/app-etl/` at `79651026` (`gitlab.md`, "The application template"), commit `764bfe9` with the
  tree `b9f49fa8`, the same as `examples/app-etl`'s at `main`; the diff against `main`: `.gitlab-ci.yml` (58
  lines) and `README.md` (2), nothing else. Pushed at 02:39:09 with the push options that create the merge
  request (`merge_request.create`, target `main`, the source branch removed on merge); the validation in
  the pipeline editor and the merge are the user's. Until it merges, no tag: the narrowed
  `awsds-deploy-staging` the §V session applies refuses the old `staging-up`.
- **[§V's session] The two `foundation/` applies** of decision 27, the user's authorization in that chat,
  are that session's to run and record; this session touched neither slice.
- **[Claude] The applies read back at 02:43:04**, after the §V session reported them (its log entry, commit
  `8873e500` on its branch: plans 02:31:52 and 02:32:25, applies 02:35:29 and 02:36:00, re-plans *No
  changes*): `awsds-deploy-staging` holds the inline policies `apply-application` and `state` alone, no
  `apply-egress`; both roles' `apply-application` carries `DescribeTheEgressEndpoints` and
  `ReadTheDnsFirewallAssociation`, Production's `FollowItsOwnStatements` beside them; each `state` names the
  egress slice's state key (`staging/egress/`, `production/workloads-egress/`). The §V session's simulator
  readings, with `aws:RequestedRegion`: `DescribeVpcEndpoints` `allowed` for both roles,
  `GetFirewallRuleGroupAssociation` `allowed` on an association ARN (`implicitDeny` on `*`),
  `CreateVpcEndpoint` `implicitDeny` for both, `s3:GetObject` on the egress state key `allowed` for both,
  `s3:PutObject` on Staging's egress state `explicitDeny`. The `waiting-on-the-user.md` row removed. The
  mirror's push was not the §V session's, which never pushes to GitLab; the user had said they would push
  `main` after #256's merge, so the attribution is theirs, to confirm.
- **[user] MR !11 merged** at 02:42:32 (`awsds/app-etl`'s `main` `163ccca`, the merge commit; the source
  branch removed). **[Claude] read back** at 02:46: the tree `b9f49fa8`, the same as `examples/app-etl`'s at
  `79651026`; `staging-gate` in the file, no `staging-down`. The new legs exist from the next tag on:
  `staging-gate` manual before anything of the leg, `staging-check` reading Staging's `egress/` as
  `awsds-deploy-staging`, `production-deploy` reading `workloads-egress/` first.
- **[user] How the first tag on the new legs reads `staging-check`** (2026-10-25 UTC): *"na v0.4.4 clico o
  staging-gate com o egress de Staging derrubado para ler a falha do staging-check, depois make up
  ENV=staging ONLY=egress e retry"*: the negative first, at no cost, then the positive on the job's retry.
  **[Claude] The precondition read at 02:47:19**, `./scripts/check-egress.py staging egress` as the
  infrastructure user: *"FATAL: staging/egress/ is down: its state holds no interface endpoint; run `make up
  ENV=staging ONLY=egress` from the project folder as the infrastructure user (profile awsds-infra-staging:
  account Staging, permission set InfrastructureAccess), then retry this job"*, exit 1, the script's "down"
  branch read for the first time. The pipeline's readings are the §V session's, the pointers this log's.
- **[user] The mirror's push was theirs**, confirmed in chat (2026-10-25): `git push gitlab main` from the
  project folder after #256's merge, before this session's authorized push read *"Everything up-to-date"*
  at 02:37:56. The attribution above is closed.

## 2026-10-25 — the legs of decisions 27 and 28 on `v0.4.4` (pipeline #85) and verification ix on `v0.4.5` (pipeline #87)

*The user's hand for MR !11 (opened by PR #256's session), the tags, the gates, `make up ENV=staging
ONLY=egress` and the cancel; Claude's for the readings (the traces through GitLab's API in the user's Chrome
session, AWS as the infrastructure user with `InfrastructureAccess`). Times UTC.*

- **[user]** MR !11 merged at 02:42:32, `awsds/app-etl`'s `main` at `163ccca`, the template's tree `b9f49fa8`
  (`examples/app-etl/` at `79651026`), `staging-gate` and `staging-check` in, `staging-down` out.
- **[Claude] `v0.4.4`, pipeline #85**, the tag on `163cccaa` (`main`, no drift): the build half and
  `test-deploy` passed (02:48:52 to 03:08:06); **the staging gate** clicked by the user at 03:22:54; **the
  negative**: `staging-check` (job 501, 03:23:00 to 03:23:11) as `awsds-deploy-staging`, *"FATAL:
  staging/egress/ is down: its state holds no interface endpoint; run `make up ENV=staging ONLY=egress` from the
  project folder as the infrastructure user…"*; then the user's `make up ENV=staging ONLY=egress`, and **the
  positive**, the retry (job 512, 04:34:22 to 04:34:35): seven endpoints listed `available` (`glue`, `kms`,
  `lakeformation`, `logs`, `sagemaker.api`, `secretsmanager`, `sts`), *"DNS Firewall association
  rslvr-frgassoc-18e6e7bc55304d6b COMPLETE"*, *"ok: staging/egress/ is up: 7 interface endpoint(s) available and 1
  DNS Firewall association(s) COMPLETE"*; `staging-deploy`, `staging-test`, `staging-model` and
  `production-plan` passed (04:34:39 to 05:08:02); the user cancelled the pipeline at 05:28:34 at
  `production-gate`, since the tag carried no drift. Staging stayed up, as decision 27 has it: egress 16
  resources, the application slice 2 and the orchestration slice 31.
- **[Claude] `v0.4.5`, pipeline #87, verification ix**: the branch `ix-governed-drift-2` (`268964ad`, the tree
  `9587ab57`, `b9f49fa8` with the drift patch checked); `test` passed at 05:32:05 with the drift and its tests,
  and `test-deploy` passed (05:34:54 to 05:50:49), the `test` project reading the inbox; the staging gate at
  05:54:57; `staging-check` passed (05:55:07 to 05:55:23) on the egress already up; `staging-deploy` (05:55:26 to
  05:58:43); `staging-test` failed (05:58:46 to 06:04:14), the Glue job `jr_4636eb75…582d` *"RuntimeError:
  lake.curated.trades lacks book: the application's schema source and the governed table disagree"*, the chain
  *"FATAL: the chain app-etl ended FAILED"*; `staging-model` and every Production job skipped, the pipeline
  `failed` at 06:04:15. **Verification ix answered yes**: a deliberately broken version passes `test` and stops
  at 3.3 with Production untouched. The branches `ix-governed-drift` and `ix-governed-drift-2` are owed their
  delete, the user's; `main` is unchanged.

## 2026-10-25 — the simulator's `explicitDeny` on Staging's egress state, attributed

*Claude's hand, as the infrastructure user with `InfrastructureAccess` (`awsds-infra-staging`), the policy
simulator alone. Times UTC.*

- **[Claude] The reading of 02:42**, `s3:PutObject` by `awsds-deploy-staging` on
  `staging/egress/terraform.tfstate` read `explicitDeny` (the maintenance entry above), is the perimeter SCP's
  `DenyS3ObjectWriteOutsideOrganization`, never the role. Re-read at 06:35 with `aws:RequestedRegion` alone:
  `explicitDeny`, *"AllowedByOrganizations: false"*, no matched statement, on `staging/egress/` and on
  `staging/orchestration/`, a key the role writes at every leg. With `aws:ResourceOrgID` set to the
  organization's id beside it, so that the statement's `StringNotEqualsIfExists` no longer matches an absent
  key: `staging/orchestration/` `allowed` by `role_awsds-deploy-staging_state`, `staging/egress/`
  `implicitDeny`. Decision 27's narrowing holds as written: no grant writes the egress state, and no deny is
  involved.

## 2026-10-25 — §R: the downs, and zero burn in every account

*The user's hand for the downs; Claude's for the readings, as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-prod`, `awsds-infra-staging`, `awsds-infra-sandbox-1`). Times UTC.*

- **[user] The downs before 06:57**: `make down ENV=staging` (06:30 to 06:36, its table delete refused and
  unblocked: Stage 9's log), Sandbox and GitLab; Production's `workloads-egress/` kept up for the 07:00 train
  chain.
- **[Claude] Read at 06:57 and 07:01**: `./aws/egress.py` reads 8 interface endpoints in Production (`glue`, `kms`,
  `lakeformation`, `logs`, `sagemaker.api`, `secretsmanager`, `sts`, and `redshift-serverless`, raised by
  `GROUPS=redshift` for the paused warehouse chain), 0.080 USD/h, Staging and Sandbox 0, no NAT anywhere;
  `make status` reads the VPN, proxy and GitLab hosts `stopped`, Production's `workloads-egress/` (17
  resources), `app/app-etl/` (3) and `orchestration/` (41) up, every other `[E]` slice down; no EC2 instance
  running, no Redshift workgroup, no SageMaker app, endpoint or job and no Glue run in the three accounts.
- **[user] `make down ENV=production ONLY=workloads-egress`**, after the train chain ended at 07:07:38.
- **[Claude] Read at 07:14 and 07:19**: `./aws/egress.py`, 0 interface endpoints, 0 NAT and 0.000 USD/h in each
  account, `EG-5` *"none - the correct between-sessions state (D11)"*; `make status`, *"estimated burn: USD
  0.0000/h"*, Production's application and orchestration slices up at 0.0000 USD/h, every other `[E]` slice
  down and the three `[D]` hosts stopped.

## 2026-10-25 — with the environment down: verification vii's attachment read again, the lint's clause table

*Claude's hand, at the user's request to prepare what needs no environment, as the infrastructure user with
`InfrastructureAccess` (`awsds-infra-sandbox-1`), reads only. Times UTC.*

- **[Claude] vii's third half**: both Sandbox domains (`d-p6gthxc82ckg`, `d-lfgbdrjncmsu`) carry
  `awsds-sandbox-dev-env` with no version in `JupyterLabAppSettings` and `CodeEditorAppSettings`, each
  `LastModifiedTime` its last `UpdateDomain` (2026-10-15 06:14:05Z and 2026-10-16 00:31:25Z, both by
  `InfrastructureAccess`). `lookup-events` reads no `UpdateDomain` and no `UpdateStack` since 2026-10-18, the same
  lookup listing the eight re-attach writes of 2026-10-15 and 16: no reconciliation in ten days, the half open.
- **[Claude] 5.6's clause table**: the training task's (f) is `awsds-workflows`' `treino`, in the template's line
  since v0.4.0 (`--algorithm-repository` on `.gitlab-ci.yml` line 69); (f) for any other operator stays without a
  rule until a workflow uses one.
- **[Claude] 1.1's proposal still current**: `./scripts/check-gitlab-mirror.py --plan` at 07:41, from a read-only
  plan of `sandbox/egress/` (down), exit 0: `GM-1` to `GM-8` pass, the copy at `5d5391abd7a3` (2026-10-16), the
  Dockerfile's `NO_PROXY_LIST` and the account's list both 72 names, `sha256 6faf2e4761622508`. The tag
  `default-v0.9.0` stays the user's GitLab act.

## 2026-10-25 — verification ix's branches deleted

*The user's hand; recorded from the user's word in chat (*"Sobre "2. Apagar no GitLab as branches", isso já foi
feito."*), not read back, GitLab down.*

- **[user]** `awsds/app-etl`'s branches `ix-governed-drift` and `ix-governed-drift-2` deleted; `main` carries none of
  the drift.

## 2026-10-25 — the plan read for what is left; the next release's sitting written

*Claude's hand, with two editing agents of this session, at the user's request to review the documentation, the
runbooks and the Terraform comments against the session's learnings, to prepare what can be anticipated and to
review what is left; no AWS write.*

- **[Claude]** The stage file's status cell ends with what is left on 2026-10-25, its stale clauses corrected
  against this log; `runbooks/promotion.md` §N orders every step left in Stages 8, 9 and 10 by the sitting that
  runs it (nothing up, the release through Staging and Production, the warehouses, a Sandbox space, the
  deliberate exercises, what waits on something else). The next tag needs PR #258 merged and `main` pushed to the
  GitLab mirror first, since the mirror at `79651026` holds `production/orchestration/` on `orchestration-v0.2.0`
  with the app-etl and train schedules `ENABLED` (the waiting list).
- **[Claude]** The documentation, runbooks and Terraform comments read against the learnings: Staging's release
  stays until the user's `make down` (decision 27), the governed warehouse is a Lake Formation-managed datashare,
  `EXC-22` in `GOVERNANCE.md`'s encryption rule and the threat model, the save's KMS grant behind every workflow
  run, the plan's `# whitespace changes` on a JSON string in `terraform-changes.md`, the principal-filtered
  `list-permissions` in `log-debugging.md`, and `aws/orchestration.py`'s report texts.

## 2026-10-25 — with the environment down: verification xiv's battery at `d856982c`

*An agent of this session ran the lint offline, at the user's request to prepare what Stages 7 to 10 leave
with nothing up; Claude's hand for the record. No AWS call, no change to the repository or to the user's
`awsds-workflows` checkout, which holds no object `d856982c` (its `main` is `ff25eae`): the lint's source was
read from the uvx cache's copy of the pinned archive. 76 cases, one scratch copy of `examples/app-etl/` each.*

- **[agent] The invocation**: the template's `test` line, `uvx --from "awsds-workflows @ <the d856982c
  archive>" awsds-workflows lint app-etl --image-repository awsds-prod-ecr-app-etl`, one `--instance-type` per
  name of `LINT_INSTANCE_TYPES` (the ceiling's seven) and `--algorithm-repository sagemaker-xgboost`
  (`LINT_ALGORITHM_REPOSITORIES`), each read from `.gitlab-ci.yml`; the promoted mode on one rendered file with
  `--prefix s3://awsds-staging-outputs/applications/app-etl/v9.9.9/` and the same options. The rendered copies
  came from a copy of `scripts/render-workflow.py`'s table with stand-in values, and both passed the promoted
  mode at the first attempt.
- **[agent] The untouched copy** reads `ok: 9 arquivo(s)` (6 on 2026-10-18: the train and warehouse workflows
  and `glue/load_warehouse.py` since v0.4.0); each clean rendered copy `ok: 1 arquivo(s)`. The controls hold:
  a `dev-env` image by digest passes without `--image-repository`, in both modes; a job without its volume key
  passes in the authoring mode; a rendered `ml.m5.2xlarge` passes without `--instance-type` (Lesson 71).
- **[agent] The 40 violations of 2026-10-18 reproduced**, each exit 1 under its rule: `projeto` 8 (the eight
  `_PROJECT_PATTERNS`), `datas` 3, `operador` 2, `limites` 4, `imagem` 2, `job` 5, `templates` 2, `codigo` 1,
  `glue` 2 and `manifest` 8 in the authoring mode; in the promoted mode `projeto` on the unrendered source (16
  findings: nine CLI variables, two promoted patterns, rule (6), `glue`, `imagem`, `codigo`) and on a rendered
  copy with a `datazone-<project>-dev` prefix, and `job` on a rendered copy without its volume key.
- **[agent] The rules since `3c1708e`**: rule (6)'s five keys each refused on a rendered copy under `glue`
  (`create_job_kwargs`, `script_location`, `iam_role_arn`, `update_config`, `job_desc`); `treino` refusing
  `action_if_job_exists` left off, network isolation off, `ml.g5.xlarge`, a validation channel in another
  bucket, a missing `S3OutputPath`, and on a rendered copy an output outside `models/` and a missing output
  key, seven in all; `--instance-type` refusing `ml.m5.2xlarge` and `ml.g5.xlarge` on the processing task and
  `ml.g5.xlarge` on the training task; `--image-repository` refusing the `dev-env` image on `ImageUri` in both
  modes and on `TrainingImage`. 61 refusals in all, every control passing.
- **[agent] Three readings**: a `dev-env` `TrainingImage` is refused under `imagem`, not `treino`
  (`_check_images` reads both `ImageUri` and `TrainingImage`); a CLI variable outside the lint's table
  (`{proj.name}`) is refused under `projeto` and leaves the text untranslated, so four collateral lines follow
  (`glue` twice, `imagem`, `codigo`); the pattern `datazone-<projeto>-dev` does not match the source's
  `datazone-{proj.id}-dev`, whose braces break the word boundary, the file refused on the variable anyway and
  the rendered form caught. Cosmetic: `_check_glue` prints one script location twice when `script_location`
  and `create_job_kwargs.Command.ScriptLocation` carry the same path. No rule reads a `VersionId` or compares
  with a release's manifest, as before.

## 2026-10-25 — the laptop's Terraform at 1.16.6; the pins moved; the deploy image's rebuild ordered first

*The user's hand for the install (*"Rodei os comandos.. aparentemente atualizou para a versão 1.17.0"*); Claude's
reading of the binary and the edits. No AWS write.*

- **[user]** `terraform_1.16.6_darwin_arm64.zip` and the published sums downloaded, the checksum checked, the
  executable unzipped over `~/local/bin/terraform` (the only `terraform` on the PATH, read with `which -a`).
- **[Claude] The reading**: `terraform version` prints `Terraform v1.16.6 on darwin_arm64`; the "1.17.0" the user
  saw is the CLI's own notice, *"Your version of Terraform is out of date! The latest version is 1.17.0"*, so
  1.17.0 is released (`upstream-releases.md`) and the lab stays on 1.16.6, the bump taken 2026-10-22. A read-only
  plan of `production/warehouse/` under the new binary read `No changes`.
- **[Claude] The pins** (`upstream-releases.md`'s order): `CLAUDE.md`'s tool list, `.github/workflows/offline-gates.yml`'s
  `TERRAFORM_VERSION` and `gitlab/awsds/deploy-image/Dockerfile`'s `TERRAFORM_VERSION` and `TERRAFORM_SHA256`
  (the published `linux_amd64` sum), with the recipe's README; the image's release is the GitLab sitting's
  merge request and tag (§H step 4).
- **[Claude] The order this fixes**: Terraform refuses a state snapshot written by a newer version, so the
  deploy image's 1.15.8 cannot plan, read through `terraform_remote_state` or `terraform output` a state the
  laptop's 1.16.6 has written. Every state the pipeline touches is 1.15.8's today (the three applies of this
  date ran before the install). At the next sitting the image is rebuilt before `make up ENV=staging
  ONLY=egress`, `make up ENV=production ONLY=workloads-egress` and any laptop apply of `data/`, `sagemaker/`,
  `foundation/` or `workloads/` in either target (`runbooks/promotion.md` §N.1 step 2, the waiting list).
- **[Claude] Lesson 76** written at the user's request, with its key in `CLAUDE.md`, a bullet in its
  parallel-sessions section and a standing rule, and a note in `terraform-changes.md` §1, so a parallel
  session reads the order before its first apply.

## 2026-10-25 — verification iv's re-scan half: a second scan inside 24 h is refused

*Claude's hand, on the user's authorization in chat (*"Autorizo o aws ecr start-image-scan na imagem v0.4.5 de
awsds-prod-ecr-app-etl como usuário de infraestrutura (awsds-infra-prod), para ler a recusa da releitura dentro
de 24 h."*), as the infrastructure user with `InfrastructureAccess`; the one peer session told before the call.
Times UTC.*

- **[Claude] Before**, 19:43:06: `describe-image-scan-findings` on `v0.4.5-268964ad` reads `COMPLETE`,
  completed 05:36:43 (the push's scan, two minutes after the push at 05:34), CRITICAL 113, HIGH 612, MEDIUM
  158, LOW 16, UNDEFINED 466.
- **[Claude] The call**, 19:43:08: `start-image-scan` refused, *"An error occurred (LimitExceededException) when
  calling the StartImageScan operation (reached max retries: 2): The scan quota per image has been exceeded.
  Wait and try again."*
- **[Claude] After**, 19:43:13: the scan `COMPLETE` with the same completion time, nothing re-run: a second
  scan inside 24 h is refused, not absorbed, and the gate's read of the push's scan is the one reading an image
  gets that day.

## 2026-10-25 — verification xxi's attempt half: the infrastructure user writes and deletes on the release bucket

*The user's hand, the command pasted in chat; Claude's read-back as the infrastructure user with
`InfrastructureAccess` (`awsds-infra-prod`), reads only. Times UTC.*

- **[user]** `echo xxi > /tmp/xxi-probe.txt && aws s3 cp /tmp/xxi-probe.txt
  s3://awsds-prod-releases/xxi-probe/probe.txt --profile awsds-infra-prod --region us-west-2 && aws s3 rm
  s3://awsds-prod-releases/xxi-probe/probe.txt --profile awsds-infra-prod --region us-west-2`: *"upload:
  ../../../../tmp/xxi-probe.txt to s3://awsds-prod-releases/xxi-probe/probe.txt"*, *"delete:
  s3://awsds-prod-releases/xxi-probe/probe.txt"*.
- **[Claude] Read back** at 19:50:55: one version of `xxi-probe/probe.txt`, 4 bytes, 19:50:20, noncurrent,
  under `aws:kms` with the registry key (`alias/awsds-prod-registry`'s id); a delete marker current at
  19:50:21. The lifecycle expires noncurrent versions at 90 days and carries no rule for expired delete
  markers, so the marker outlives the version; nothing else to clean. The bucket's
  `DenyDeletesExceptInfrastructure` spared the infrastructure user as written, the simulator's half of
  2026-10-18 reading the same for the other principals.


## 2026-10-25 — the §N sitting raised: the hub, GitLab with the three runners, the tunnel; the readings

*The user's hand for `make hub-up`, `make gitlab-up BUILD=1` and the tunnel, from the project folder at `main`
(PR #259 merged at 20:06 UTC and pulled); Claude's for the readings, as the infrastructure user with
`InfrastructureAccess`, reads only. This session continues on a branch cut from the merged `main`
(`claude/stages-7-10-env-sitting-1`), the PR's own branch retired. Times UTC.*

- **[user]** `awsds-prod-vpn` and `awsds-prod-proxy` started at 20:07:04 and 20:07:07, `awsds-prod-gitlab` at
  20:07:45; the runners launched at 20:09:52 (deploy, `t3a.small`), 20:09:59 (test, `t3a.small`) and 20:10:04
  (build, `m8i.xlarge`); the tunnel on the laptop.
- **[Claude] `./aws/cicd.py`** on the five infrastructure profiles at 20:12: all checks passed; `CI-1` the deploy
  runner running, `CI-9` the test runner running with IMDSv2 and hop limit 1, `CI-8` 572 deploy-role
  assumptions, every caller the deploy runner, `CI-5` the application repository's policy admitting Sandbox
  and Staging.
- **[Claude] `./aws/egress.py`** at 20:13: all checks passed, no NAT gateway, `EG-5`:
  `PROFILE                IF ENDPOINTS  NATs  USD/HOUR`
  `awsds-infra-prod       12            0     0.120`
  `awsds-infra-staging    0             0     0.000`
  `awsds-infra-sandbox-1  0             0     0.000`
  `TOTAL                  12            0     0.120`
- **[Claude] `make status`** at 20:14: 0.4521 USD/h, the hub's two hosts, GitLab, the three runners and
  `production/egress/`'s twelve endpoints; every other `[E]` slice down.
- **[Claude]** `https://gitlab.awsds.internal/users/sign_in` answered `200` through the tunnel at 20:18, eleven
  minutes after the start.

## 2026-10-25 — §H step 4: the deploy image `v0.3.0` on Terraform 1.16.6, built; its digest pinned

*The user's hand in GitLab (the merge request `terraform-1-16-6` on `awsds/deploy-image`, merged at 20:29:27
UTC as `e502078b`; the pipeline on `main` with `IMAGE_TAG` `v0.3.0`, *"build demorou pouco menos de 1min e
30seg"*, the job's `deploy.json` printing `containerimage.digest` `sha256:9965f1b2…6736`); Claude's for the
readings and the pin, as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`), reads and a
plan only. Times UTC.*

- **[Claude] The image in ECR** at 20:32: `awsds-prod-ecr-deploy:v0.3.0`, digest
  `sha256:9965f1b2a3f1d5705bfdebceb02191de66e5b2c10b68e6789da9a4e941f26736`, 257,379,357 bytes, pushed
  20:31:21. The push's scan, complete at 20:33:02: CRITICAL 0, HIGH 5, MEDIUM 10, LOW 5, against `v0.2.0`'s
  HIGH 4, MEDIUM 10, LOW 4 of 2026-10-16; the four HIGHs of `v0.2.0` stay (`zlib` CVE-2026-85091, `glibc`
  CVE-2026-19499 and CVE-2026-5435, `gnupg2` CVE-2026-24882) and `cyrus-sasl2` CVE-2026-107161 joins them, the
  Debian 13 base's (`python:3.14-slim`); no finding names Terraform, which the scanner does not read.
- **[Claude] The pin**: `deploy_image_digest` in `production/runners/variables.tf` moved to the new digest,
  the description naming `v0.3.0`; a read-only plan with `TF_VAR_build_runner=true` at 20:33 reads *"1 to add,
  0 to change, 1 to destroy"*, `aws_instance.deploy_runner[0]` replaced on its user data, the build and test
  runners untouched. The apply is the user's `make gitlab-up BUILD=1` from the project folder once the pin is
  on `main` (PR #260), and from then on the deploy runner's jobs run Terraform 1.16.6, the laptop's version.
- **[Claude] The copy**: `./scripts/gitlab-mirror.py awsds/deploy-image` at 20:34 read GitLab's `main` at
  `e502078b` holding the copy's six files unchanged, and wrote `gitlab/mirror.json`. The README's release row
  for `v0.3.0` is GitLab's to hold first, the mirror then copying it back.

## 2026-10-25 — the deploy runner replaced on `v0.3.0`; the house image's merge request read

*The user's hand for the merge of PR #260, `git pull` and `make gitlab-up BUILD=1` from the project folder;
Claude's for the readings, as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`), reads
only. This session's records continue on a branch cut from the merged `main`. Times UTC.*

- **[user]** `make gitlab-up BUILD=1`: the deploy runner `i-04c2be6e15f27b9d8` terminated and
  `i-0acaf7ded0e455dcd` launched at 20:40:08, `t3a.small`, the build and test runners untouched.
- **[Claude] `./aws/cicd.py awsds-infra-prod`** at 20:42: all checks passed, `CI-1` the new deploy runner
  running, `CI-9` the test runner as before. From here the deploy runner's jobs run Terraform 1.16.6, and a
  slice the pipeline reads may be raised or applied from the laptop again (Lesson 76).
- **[Claude] Stage 8 1.1's merge request, read before the user's act**: `./scripts/gitlab-mirror.py --dry-run
  awsds/dev-env` at 20:42 reads GitLab's `main` at `5d5391ab` (2026-10-16) and one file differing from the
  copy, `dev-env/Dockerfile`, the 72-name `NO_PROXY` literal; `./scripts/check-gitlab-mirror.py --plan`
  reads `GM-1` to `GM-8` passing on the copy, 72 names and sha256 `6faf2e4761622508` on both sides. The
  merge request carries that one file; the tag `default-v0.9.0` and the gate are the steward's.

## 2026-10-25 — `default-v0.9.0` spent at `pip-audit`: the lock of 2026-10-16 aged; the targeted upgrade and 42 acceptances written for `gates-v0.5.0`

*Claude's hand, from the user's GitLab session read in Chrome and the laptop's own audit; no AWS call. Times
UTC.*

- **[Claude] The gate's verdict**: `awsds/dev-env`'s pipelines #89, #90 and #91, all on `f71cafcd` (the merge
  request's one file, the 72-name literal), failed at `pip-audit` (job #547): 73 blocking findings with a fixed
  version, in `dev-env/python/uv.lock` of 2026-10-16, unchanged since `default-v0.8.0` passed the same gate on
  it. The tag `default-v0.9.0` is spent with nothing built (the README: a tag is spent on first landing), so the
  release is `default-v0.9.1`.
- **[Claude] The same lock on the laptop**, 21:06 to 21:09: the gate's audit (pip-audit 2.10.1, OSV) over the
  export with its environment markers stripped, since every line names `linux` and `x86_64` and the laptop
  matches none (verification x). 89 lines, 82 findings once the marker-split duplicates fold: 73 blocking in 11
  packages (aiohttp 3.14.3, brotli 1.2.0, certifi 2026.7.22, filelock 3.32.6, gitpython 3.1.62, mlflow 3.16.0,
  nbconvert 7.17.1, opentelemetry-api 1.44.0, pillow 12.3.0, setuptools 81.0.0, virtualenv 21.14.7), the 8
  accepted (fsspec, setuptools, sqlparse) matched, and nltk 3.10.3's `PYSEC-2026-3740`, with no fixed version,
  the gate's warning.
- **[Claude] The lock moved** by `uv lock --upgrade-package` naming the 11, after a bare `--upgrade` resolved an
  older autogluon and failed building `configspace`: 17 entries in 9 packages, aiohttp 3.14.5, brotli 1.2.1,
  certifi 2026.10.23, filelock 4.2.4, gitpython 3.2.1, mlflow, mlflow-skinny and mlflow-tracing 3.17.2, nbconvert
  7.17.2, opentelemetry-api and -sdk 1.45.1 with -exporter-prometheus, -instrumentation,
  -instrumentation-threading and -semantic-conventions 0.66b1, virtualenv 21.14.13, yarl 1.25.1;
  `pyproject.toml` untouched, `uv lock --check` passing, the export 454 pins as before. Pillow stays at
  12.3.0: autogluon-multimodal 1.6.1 requires `Pillow<13,>=10.0.1` (PyPI's metadata, read 21:14), and 13.0.0,
  published 2026-10-16, fixes all 41. setuptools stays at 81.0.0: autogluon-core 1.6.1 requires
  `setuptools<82`, and 84.1.0 (2026-10-19) fixes `GHSA-xmj3-9gf7-h52w`. Forcing either resolves an older
  autogluon, torch 2.13 to 2.9.1 and transformers 5.14 to 4.57 among the moves.
- **[Claude] The new lock audited the same way**, 21:23 to 21:25 (2 min 25 s; the recipe is now the dev-env
  README's *Before a build*): 454 pins audited, 58 lines in 5 packages, pillow's 41 and setuptools' second the
  only ones outside the accepted list; fsspec's and sqlparse's accepted, nltk's the warning.
- **[Claude] Written**: the lock into the copy `gitlab/awsds/dev-env/dev-env/python/uv.lock`; 42 entries into
  `ci-gates/baselines.gitlab-ci.yml`'s `GATES_PIP_AUDIT_ACCEPTED_DEV_ENV`, pillow's 41 ids as OSV reports them
  and `GHSA-xmj3-9gf7-h52w|setuptools`, each with its version, its fix and the requirement that forbids it, 50
  entries in all; the gates README's row; Lesson 77 (a gate that reads a feed gives a dated verdict); the
  plan's sentences moved from `default-v0.9.0` to `default-v0.9.1` (`promotion.md` §H step 3 and §N.1 step 1,
  the stage file, `waiting-on-the-user.md`). The acceptance is the user's, as the Dev Env Steward: the
  `gates-v0.5.0` commit on `awsds/ci-gates` (`gitlab.md` §G), the dev-env `include:` `ref` to its commit, the
  merge request carrying the lock and the `ref`, the tag. `examples/app-etl/` stays at `gates-v0.4.0`: the
  change is the dev-env list alone.

## 2026-10-25 — `gates-v0.5.0` pushed; the dev-env `include:` `ref` moved to it

*The user's hand for the GitLab push, as a Maintainer of `awsds/ci-gates`; Claude's for the reading of the
laptop's clone and the copy. Times UTC.*

- **[user]** `awsds/ci-gates` at `7c3552b7effb0cfa1e43f4b91c7a9101d5be257b`, committed 21:32:42 and tagged
  `gates-v0.5.0`: the 42 acceptances and the README's row, the two gates files unchanged since `gates-v0.4.0`;
  the message names the steward and the two upper bounds. `origin`'s `main` and the tag both read that commit
  from the laptop's clone, and its four files equal the copy under `ci-gates/`.
- **[Claude]** `gitlab/awsds/dev-env/.gitlab-ci.yml`'s `include:` `ref` moved from `6fcea132…` (`gates-v0.4.0`)
  to `7c3552b7…` (`gates-v0.5.0`), `./scripts/check-gitlab-ci.py` passing. The merge request on `awsds/dev-env`
  carries the lock, the README and this file; its `pip-audit` is the gate's reading of the day, 50 accepted
  and none blocking expected.

## 2026-10-25 — `default-v0.9.1` tagged by the user; pipeline #96 past the gate; the copy read back

*The user's hand for the merge request, its merge and the tag, as the Dev Env Steward; Claude's for the
readings, from a clone without a checkout in the scratch folder, the mirror script and the user's GitLab
session in Chrome. Times UTC.*

- **[user]** The branch `lock-2026-10-25` at `03e94e4` (21:34:01): the lock, the README and the `include:`
  `ref` at `7c3552b7`; merged into `main` as `746ef084` (21:36:01), and the tag `default-v0.9.1` created on
  that commit.
- **[Claude] The commits read**: `origin`'s `main` and the tag both at `746ef084`, whose parents are
  `f71cafcd` (`default-v0.9.0`) and `03e94e4`; `main` changed three files since `default-v0.9.0`
  (`.gitlab-ci.yml` 2 lines, `README.md` +25, `dev-env/python/uv.lock` 112), each byte-equal to the copy
  under `gitlab/awsds/dev-env/`, and the tree's 14 files equal the copy. `./scripts/gitlab-mirror.py
  awsds/dev-env` at 21:40 read *"the copy already holds this commit's 14 file(s)"* and wrote
  `gitlab/mirror.json` at `746ef084`.
- **[Claude] Pipeline #96 on the tag**, read at 21:41: `pip-audit` (#567, 21:36:56 to 21:38:12) printed
  *"== awsds/dev-env: 50 accepted finding(s)"*, *"454 pinned package(s), audited against OSV"*, *"Found 58
  known vulnerabilities in 5 packages"*, every fsspec, pillow, setuptools and sqlparse line `accpt`, nltk
  3.10.3's `PYSEC-2026-3740` `warn` with no fixed version, no `gone` line, and *"454 of 454 pinned package(s)
  audited, 0 blocking vulnerability(ies)"*; `recipe-checks` (#568) passed in 6 s; `build-images` (#569)
  running since 21:38; `scan-base` (#570), `scan-dev-env` (#571), `release-gate` (#572, manual), `register`
  (#573) and `retire` (#574) created. The gate's reading of the day agrees with the laptop's of 21:23: the
  same 58 lines in the same 5 packages.

## 2026-10-25 — `default-v0.9.1` released: pipeline #96's evidence, version 10 in Sandbox, `DE-5` passing

*The user's hand for the release gate; Claude's for the readings, from the user's GitLab session in Chrome
(the pipeline API, the job logs, the artifacts through the pages host `awsds.awsds-pages.internal`) and
from ECR and SageMaker as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`,
`awsds-infra-sandbox-1`), reads only. Times UTC.*

- **[Claude] Pipeline #96**, the API read at 22:06: `build-images` (#569) 21:38:16 to 21:54:26, 970 s;
  `scan-base` (#570) 21:54:28 to 21:55:11 and `scan-dev-env` (#571) 21:54:29 to 22:02:12, 464 s waiting
  for the push's own scan, both failed as allowed; `release-gate` (#572) **[user]** 22:04:00 to 22:04:09;
  `register` (#573) 22:04:11 to 22:04:42; `retire` (#574) 22:04:45 to 22:05:21; the pipeline `success`.
- **[Claude] The images in ECR** (`describe-images`, 22:05): `awsds-prod-ecr-base:default-v0.9.1-746ef084`
  pushed 21:41:27, 3,754,767,181 bytes, `sha256:ac9bd82b2b9ee441fad814eda819abd72ddc9c364f87f984c1715b0a7898044e`;
  `awsds-prod-ecr-dev-env:default-v0.9.1-746ef084` pushed 21:52:45, 6,687,899,330 bytes,
  `sha256:20a1017a0680c4f837211c02076260815ad998f5f9d863ea746004d97829ca39`; 9,117,662 and 9,325,492 bytes
  more than `v0.8.0`'s, the base's growth carried into `dev-env`.
- **[Claude] The manifests**, `build-images`' artifacts against `v0.8.0`'s (job #162): `runtimes.txt` the
  same but the base digest (Python 3.12.14 in both environments, uv 0.12.17, Julia 1.12.7, R 4.5.3, rustc
  1.98.0); `trust.txt` the same (curl, urllib and requests in both Pythons answer 200 on the lab's root, git
  refused for want of a username, as before); `proxy.txt` 72 entries, sha256 `6faf2e4761622508`, against 70
  and `aafa08da98a61f5c`; `imports.txt` the same but `mlflow 3.17.2`; `julia.txt` and `r.txt` the same;
  `python-awsds.txt` 454 lines equal to the lock's export, 17 moves against `v0.8.0`'s, the lock's;
  `python-conda.txt` identical, 621 lines. The raw log's tail: 26 Julia dependencies precompiled in 75 s,
  the eight manifests written, the smoke stage `DONE 77.7s`.
- **[Claude] Both scans**, ECR's basic scan read whole at 22:07 and the gate jobs' own summaries: CRITICAL
  113, HIGH 612, MEDIUM 158, LOW 16, UNDEFINED 438 for each image, 725 CRITICAL or HIGH findings, 130 in the
  baseline, 595 absent from it: 593 on `linux-libc-dev` 6.8.0-142.142 and two new since `v0.8.0`,
  `CVE-2026-85091` on `zlib` and `zlib1g` 1.3.dfsg-3.1ubuntu2.2 (HIGH 610 → 612), the two images' sets
  identical. Job #570's lines: *"== CRITICAL and HIGH: 725 found, 130 in the baseline"*, *"WARN: 595
  CRITICAL or HIGH finding(s) absent from the baseline, for the operator to read"*, *"The job fails and the
  pipeline goes on (decision 1)"*. Whether the zlib pair enters the lineage's baseline by name is the
  steward's; the deploy lineage's baseline carries `CVE-2026-85091|zlib` for Debian's 1.3.dfsg+really1.3.1-1.
- **[Claude] `register` and `retire` read**: *"proxy answers (404)"*, 3 versions found, then
  *"awsds-sandbox-dev-env version 10: CREATED, alias 0.9.1"* with `ContainerImage` at the pushed digest;
  `retire --keep 10` kept versions 10 (`0.9.1`), 9 (`0.8.0`), 8 (`0.7.3`) and 7.
- **[Claude] AWS read back** at 22:10: `list-image-versions` 10, 9, 8 and 7 all `CREATED`, version 10 created
  22:04:39 with `ContainerImage` and `BaseImage` at the dev-env digest and release notes
  `default-v0.9.1-746ef084`; aliases `0.7.3`, `0.8.0`, `0.9.1`. `./aws/devenv.py` at 22:11: `DE-5` passes,
  version 10's config blob (`sha256:89474298…80ff`, hash checked) carrying 72 names, sha256
  `6faf2e4761622508`, the Dockerfile's; `DE-1` and `DE-4` pass; `DE-2` fails with `sandbox/egress` down, the
  reading of 2026-10-18, so `DE-3` and `DE-6` are not compared. Stage 17 1.4's apply of `vpc-egress-v0.18.0`
  on `sandbox/egress` is no longer held by the image (Stage 17 decision 4).
- **[Claude] Written**: the release row in the copy's README, GitLab's `main` to hold by the steward's
  hand; `CLAUDE.md` (version 10, `DE-5` passing, the deploy image on 1.16.6); the stage file's 1.1,
  `promotion.md` §H step 3 and §N.1 step 1, `waiting-on-the-user.md` (the item taken), `AWS_STATE.md`'s
  `DE-5` sentence.

## 2026-10-25 — the README row mirrored; §N.1 step 3's readings with GitLab up

*Claude's hand; the mirror script, `./aws/cicd.py`, `git ls-remote` on GitLab, SSM, EC2 and a read-only plan as
the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`). Times UTC.*

- **[user]** The merge request `the-releases-v0.9.1` merged as `6ba33971` (22:27:51), the release row on
  GitLab's `main`. **[Claude]** `./scripts/gitlab-mirror.py awsds/dev-env` at 22:28: *"the copy already holds
  this commit's 14 file(s)"*, `gitlab/mirror.json` at `6ba33971`.
- **[Claude] `./aws/cicd.py awsds-infra-prod`** at 22:29: all checks passed, `CI-1` the deploy runner
  `i-0acaf7ded0e455dcd` running, `CI-8` 72 assumption events, every caller the deploy runner, `CI-9` the test
  runner `i-0e7427191bcddf332`.
- **[Claude] `awsds/app-etl`'s refs** (`git ls-remote`, 22:30): one branch, `main` at `163cccaa`; verification
  ix's branches gone, as the user said on 2026-10-25; tags `v0.1.0` to `v0.4.5`, so `v0.4.6` is free for
  step 6.
- **[Claude] The infrastructure mirror** (`awsds/infrastructure`, `git ls-remote`, 22:30): `main` at
  `e011eb14`, PR #257's merge, while `origin`'s and the project folder's `main` read `2d3160f1` (PR #260):
  `orchestration-v0.2.1` and the paused schedules (PR #258) are not on the mirror yet, step 4's push.
- **[Claude] Stage 8 xxvii's plan half**: the parameter
  `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64` reads `ami-0829b74b2a8c619b7`,
  modified 2026-10-24 21:01, and all three runners run that image, launched today (the test runner 20:09:59,
  the build runner 20:10:04, the deploy runner 20:40:08), so the parameter has not moved past them and the
  half still waits; the read-only plan of `production/runners/` with `TF_VAR_build_runner=true` at 22:30
  reads *"No changes"*.
- **[Claude] `make status`** at 22:31: every `[E]` slice down but the hub's and GitLab's, Sandbox's `egress/`
  among them, as step 6's negative needs; the burn 0.4521 USD/h.

## 2026-10-25 — §N.1 steps 4 and 5: the mirror at `main`, the template's `KmsKeyId` merged

*The user's hand for the push and the merge request; Claude's for the readings (`git ls-remote`, the
pipeline API in the user's GitLab session). Times UTC.*

- **[user]** `git push gitlab main` from the project folder: `awsds/infrastructure`'s `main` reads
  `2d3160f1` at 22:45, `origin`'s, so the promotion legs clone `orchestration-v0.2.1`, the paused schedules
  and `model-chain.py`'s registry read.
- **[user]** The merge request `kms-key-id` on `awsds/app-etl`, one line, `ProcessingOutputConfig.KmsKeyId:
  "{env.PROJECT_KEY_ARN}"` in `workflows/app-etl.yaml` (`EXC-22`, Stage 10 xxviii): its branch pipeline #99
  (`e915deac`) passed at 22:43, merged as `8d50f685`, whose `main` pipeline #100 passed at 22:44. **[Claude]**
  the archive compared beforehand: GitLab's `main` and `examples/app-etl/` at `origin/main` differed in that
  line alone.

## 2026-10-25 — §N.1 step 6: the tag `v0.4.6`, verification xxiv's negative, Sandbox's egress raised

*The user's hand for the branch's deletion, the tag, `make up ENV=sandbox ONLY=egress` and the job's retry;
Claude's for the readings, from the user's GitLab session in Chrome (the pipeline API, the job logs). Times
UTC.*

- **[user]** `xi-portal-scoped` deleted; the tag `v0.4.6` on `8d50f685` with Sandbox's `egress/` down:
  pipeline #102, created 22:48:19.
- **[Claude] The stages before the deploy**: `test` (#601) passed in 14 s; `build-image` (#602) passed in
  2 min 44 s, the app layers `CACHED` from the previous build, and printed *"== pushed
  …/awsds-prod-ecr-app-etl:v0.4.6-8d50f685@sha256:ba8d41bf08bebee084b38e7df9b8efa28e6fcccaf9865e0591fdec7d0462f98d"*
  at 22:51:21, the base `awsds-prod-ecr-base@sha256:94359041…1975` as the template pins it; `build-task-code`
  (#603) passed in 8 s; `scan-gate` (#604) failed as allowed after 2 min 25 s: the push's scan at 22:53:39
  read CRITICAL 113, HIGH 612, MEDIUM 158, LOW 16, UNDEFINED 466, *"725 found, 130 in the baseline"*, *"595
  CRITICAL or HIGH finding(s) absent from the baseline"*, the `linux-libc-dev` list.
- **[Claude] Verification xxiv's negative**: `test-deploy` (#605) started 22:51:27 and failed at 22:51:36,
  10 s, before any write: *"== the hub: the proxy answers for the SageMaker API"*, *"== Sandbox's egress: the
  interface endpoints the run needs"*, *"sagemaker.api: None"*, *"FATAL: no sagemaker.api endpoint: is
  Sandbox's egress up (make up ENV=sandbox ONLY=egress)?"*, then *"bundle.env: no matching files"* at the
  artifact upload: the guard reads the endpoint before the deploy, as written.
- **[user]** `make up ENV=sandbox ONLY=egress`, then the job's retry: `test-deploy` (#620) running from
  about 22:58. `store-bundle` (#606) and `release` (#607) follow it; `staging-gate` (#608) is the manual
  job step 8 opens.

## 2026-10-25 — §N.1 steps 6 to 8: `test-deploy` retried, the release stored, Staging's gate and check

*The user's hand for the retry, `make up ENV=staging ONLY=egress` and `staging-gate`; Claude's for the
readings, from the user's GitLab session in Chrome. Times UTC.*

- **[Claude] `test-deploy` (#620)**, 22:58:23 to 23:14:26, 16 min 3 s: the bundle `artifacts/app-etl.zip`,
  16,440 bytes, sha256 `7334604b2f58564ebb3ee3032dea9900b4916966b84376880e36f4c9737fb50c`, the deploy to the
  `test` project, its workflow run `GK8LmpHGAx9OcqR` (`ON_DEMAND`) started 23:00:16, completed 23:12:49,
  `Duration` 753, `RunState` `SUCCESS`, four task instances (`transform`, `process`, `summarize`,
  `write_result`); the known `datazone:GetGroupProfile` warnings of the deploy role.
- **[Claude] `store-bundle` (#606)** at 23:14:32: *"artifacts/app-etl.zip: OK"*, uploaded to
  `s3://awsds-prod-releases/app-etl/v0.4.6/app-etl.zip`. **`release` (#607)** at 23:14:44: *"release v0.4.6,
  bundle s3://awsds-prod-releases/app-etl/v0.4.6/app-etl.zip, sha256 7334604b…b50c, image
  …/awsds-prod-ecr-app-etl@sha256:ba8d41bf08bebee084b38e7df9b8efa28e6fcccaf9865e0591fdec7d0462f98d"*, the
  GitLab release created; the three values of 3.7's record.
- **[user]** `make up ENV=staging ONLY=egress`, then `staging-gate` (#608) at about 23:16. **[Claude]
  `staging-check` (#609)**, 23:16:58 to 23:17:08: the mirror cloned at `2d3160f1`; `staging/egress/`'s state
  holds the seven interface endpoints `available` (glue, kms, lakeformation, logs, sagemaker.api,
  secretsmanager, sts) and the DNS Firewall association `COMPLETE`: *"ok: staging/egress/ is up"*, decision
  27's read of the user's slice. `staging-deploy` (#610) running from 23:17.

## 2026-10-25 — §N.1 step 9, first half: Staging's app-etl chain `SUCCEEDED`, `EXC-22`'s Staging half closed

*Claude's hand; `staging-test`'s log in the user's GitLab session, Step Functions, S3 and KMS as the
infrastructure user with `InfrastructureAccess` (`awsds-infra-staging`), reads only. Times UTC.*

- **[Claude] `staging-test` (#611)** started 23:20:42, the mirror at `2d3160f1`, and at 23:20:53 started the
  execution `v0-4-6-102-app-etl` of `awsds-staging-chain-app-etl`, polled every minute; the execution read
  `SUCCEEDED` at 23:36:55 from the laptop (`list-executions`: stopped 23:35:57, 15 min 4 s), the job's own
  poll printing *"23:36:17 app-etl SUCCEEDED"*; the job went on to the train chain.
- **[Claude] `EXC-22`'s Staging half**, read 23:37:32: `awsds-staging-outputs/app-etl/work/job/trades.summary.json`,
  written 23:29:20, 519 bytes, `ServerSideEncryption` `aws:kms`, `SSEKMSKeyId`
  `arn:aws:kms:us-west-2:…:key/74f5ebbc-41bb-4165-9047-f84a952a833f`, the key `alias/awsds-staging-data`
  resolves to (`describe-key`, `CUSTOMER`): the processing output is under the project's data key and no
  longer under `aws/s3`, the template's `ProcessingOutputConfig.KmsKeyId` at work. The run's other objects:
  `work/glue/trades.csv` 23:23:06, the `tables/trades_notional/` parts 23:23:08, the train inputs under
  `work/train/` 23:23:11, `work/job/trades.parquet` 23:29:20, `outbox/report.json` 23:33:21.

## 2026-10-25 — §N.1 step 9, second half: Staging's train chain `SUCCEEDED`, `staging-model` started

*Claude's hand; Step Functions as the infrastructure user (`awsds-infra-staging`), the pipeline API in the
user's GitLab session, reads only. Times UTC.*

- **[Claude]** `staging-test` (#611) started the execution `v0-4-6-102-app-etl-train` of
  `awsds-staging-chain-app-etl-train` at 23:36:19, after the app-etl chain; it read `SUCCEEDED` at 23:45:29
  from the laptop (stopped 23:45:22, 9 min 3 s), Staging retraining on the release (Stage 10 decision 22).
- **[Claude]** `staging-model` (#612) started 23:45:43 on the deploy runner, Stage 9 xii's registry read
  before Staging's own model; Production's trail showed no `ListModelPackages` or `DescribeModelPackage`
  yet at 23:46 (the trail lags the call).

## 2026-10-25 — §N.1 step 9 closed: `staging-model`, Stage 9 xii's call in the job and in Production's trail

*Claude's hand; the job's log in the user's GitLab session, SageMaker as `awsds-infra-staging`, CloudTrail
and IAM as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`, `awsds-infra-staging`),
reads only. Times UTC.*

- **[Claude] `staging-model` (#612)**, 23:45:43 to 23:51:36, succeeded: first *"Production's registry:
  version 1 of arn:aws:sagemaker:us-west-2:…:model-package-group/awsds-prod-model-app-etl is Approved, v0.4.2
  trained by app-etl-train-20261025T011858"*, then *"== app-etl-v0-4-6-20261025T234609: the model of
  app-etl-train-20261025T233703 on 30 batch row(s)"*, the transform `InProgress` from 23:46:45 and
  `Completed` at 23:51:32 (SageMaker: created 23:46:13, ended 23:51:22), *"30 prediction(s), one per input
  row, at s3://awsds-staging-outputs/models/app-etl/transform/app-etl-v0-4-6-20261025T234609/batch.csv.out"*,
  the model deleted after.
- **[Claude] Stage 9 xii in Production's trail** (`lookup-events`, 23:52): `DescribeModelPackage` at 23:46:03
  on `model-package/awsds-prod-model-app-etl/1`, no error, `principalId`
  `AROAZ4XFWAR7MPYEZXRTM:botocore-session-1792971953`, and `AROAZ4XFWAR7MPYEZXRTM` is `awsds-deploy-staging`'s
  role id (`get-role`): Staging's deploy session read Production's registry through its own account's
  credentials, the cross-account grant of Stage 8 4.1 exercised. `ListModelPackages`, the call before it,
  had not reached the trail at 23:52.
- Step 9 is closed: ix's Staging half (`OR-3`), `EXC-22`'s Staging half, xii. `production-plan` (#613)
  started 23:51:40; `production-gate` (#614) is the manual job step 10 opens after
  `make up ENV=production ONLY=workloads-egress`.

## 2026-10-25 — `production-plan` green; the pipeline at `production-gate`

*Claude's hand; the job's log in the user's GitLab session. Times UTC.*

- **[Claude] `production-plan` (#613)**, 23:51:40 to 23:52:30, succeeded with `production/workloads-egress/`
  still down: `production/app/app-etl/`'s plan *"0 to add, 2 to change, 0 to destroy"*, the Glue job
  `awsds-prod-app-etl`'s `script_location` moving from `applications/app-etl/v0.4.2/glue/transform.py` to
  `v0.4.6`'s, the outputs `image_uri` from `sha256:9735e42e…6fd5` to `sha256:ba8d41bf…f98d` and
  `release_prefix` to `applications/app-etl/v0.4.6`; the saved plan; `lint-plan` *"ok: 2 job(s) do Glue:
  aws_glue_job.load[0], aws_glue_job.this[0]"* (Stage 10 2.3's rule (2c)) with `awsds-workflows` at
  `d856982c`. The pipeline reads `manual` at `production-gate` (#614), §N.1 step 10's.

## 2026-10-26 — §N.1 steps 10 and 11: the Production guard's negative, `production-deploy` on the retry, the chain started by hand

*The user's hand for `production-gate`, `make up ENV=production ONLY=workloads-egress` and the retry;
Claude's for the readings (the user's GitLab session, EC2 and Step Functions as the infrastructure user with
`InfrastructureAccess`, `awsds-infra-prod`) and, on the user's authorization in chat, for the
`start-execution`. Times UTC.*

- **[user]** `production-gate` (#614) at 00:02:35, before the slice: **[Claude]** `production-deploy` (#615)
  failed at 00:02:57 after the mirror's clone, *"FATAL: production/workloads-egress/ is down: its state holds
  no interface endpoint; run `make up ENV=production ONLY=workloads-egress` from the project folder as the
  infrastructure user (profile awsds-infra-prod: account Production, permission set InfrastructureAccess),
  then retry this job"*, nothing applied: decision 27's Production guard read on its negative, as Sandbox's
  was at step 6.
- **[user]** `make up ENV=production ONLY=workloads-egress`: the workloads VPC's seven interface endpoints
  (secretsmanager, sagemaker.api, glue, lakeformation, logs, sts, kms) created 00:03:25 to 00:03:38
  (`describe-vpc-endpoints`), the shared-services VPC's seven of 20:08 untouched; then the retry.
- **[Claude] `production-deploy` (#621)**, 3 min 12 s, passed at 00:09:05: the application slice's 2
  changes applied and the orchestration slice's outputs printed, the workflows
  `awsds-prod-wf-app-etl-DHhc8FiTZC`, `awsds-prod-wf-app-etl-train-tM4WIaNABi` and
  `awsds-prod-wf-app-etl-warehouse-w8XH78cHx3`, the three chains' state machines and the chain roles
  `awsds-prod-chain-exec`, `-scheduler`, `-events`; the release record `v0.4.6` with a definition version id
  per workflow and a code version id for `app-etl` and `app-etl-train`, kept as
  `production-release.auto.tfvars.json`. The three schedules read `DISABLED` at 00:09 (`list-schedules`),
  as the slice declares them.
- **[Claude⚡] Step 11, on the user's authorization**: `aws stepfunctions start-execution` on
  `awsds-prod-chain-app-etl` as the infrastructure user at 00:10:48, the execution
  `v0-4-6-by-hand-2026-10-26-app-etl`; the previous executions, 2026-10-24's two by hand and the schedule's
  of 2026-10-25 03:30, all `SUCCEEDED`.

## 2026-10-26 — step 11 closed: Production's chain `SUCCEEDED`, `EXC-22`'s Production half

*Claude's hand; Step Functions, S3 and KMS as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-prod`), reads only. Times UTC.*

- **[Claude]** The execution `v0-4-6-by-hand-2026-10-26-app-etl` of `awsds-prod-chain-app-etl` read
  `SUCCEEDED` at 00:26:41 (stopped 00:25:52, 15 min 4 s), input `{}`, started by hand: the Glue table's
  parts at 00:13:12, the train inputs at 00:13:15, `work/job/trades.parquet` and `trades.summary.json` at
  00:19:47, `outbox/report.json` at 00:23:45.
- **[Claude] `EXC-22`'s Production half**, read 00:27:20: `awsds-prod-outputs/app-etl/work/job/trades.summary.json`
  (00:19:47, 519 bytes) `ServerSideEncryption` `aws:kms`, `SSEKMSKeyId`
  `arn:aws:kms:us-west-2:…:key/0415a6f0-9b15-4049-841d-d51e7a65d09c`, the key `alias/awsds-prod-data`
  resolves to (`CUSTOMER`): no longer `aws/s3`. Both halves read, `EXC-22` closes.

## 2026-10-26 — §R before the downs: the instruments with Staging up and Production's egress going down

*Claude's hand; `./aws/orchestration.py` and `./aws/cicd.py` as the infrastructure user, reads only. Times UTC.*

- **[Claude] `./aws/orchestration.py`** at 01:11, every profile: 45 checks pass, 0 fail; the only calls
  that failed are the persona and `ctadmin` profiles' `get-caller-identity`, whose SSO sessions hold no
  token tonight (section 14), the instrument reporting them and judging nothing on them.
- **[Claude] `./aws/cicd.py awsds-infra-prod`** at 01:13: all 9 checks pass, `CI-1` the deploy runner
  `i-0acaf7ded0e455dcd`, `CI-9` the test runner.
- **The downs**: `make down ENV=staging` is the user's next act here, the first after a release since
  `app_outputs`' infrastructure grant (step 15's measurement); `production/workloads-egress` and both
  `warehouse-compute` slices are the Stage 9 session's (down in progress at 01:05 for Production);
  `sandbox/egress` follows that session's word; `make gitlab-down` is the Stage 7 session's cycle's first
  act, and `make hub-down` closes the sitting after both report.

## 2026-10-26 — `make down ENV=staging`, the first after a release since `app_outputs`' grant

*The user's hand for the down, from the project folder; Claude's for the readings as the infrastructure user
(`awsds-infra-staging`), reads only. Times UTC.*

- **[user]** `make down ENV=staging` at about 01:18. **[Claude]** read at 01:21:51: no workflow, no
  `awsds-staging-chain-*` state machine, no schedule, no Glue job `awsds-staging-app-etl`, no
  `/awsds/staging/wf/*` log group (the negative run's stream went with its group); the seven interface
  endpoints `deleting`; `make status` at 01:21:58 read `staging/app/app-etl` and `staging/orchestration`
  down with 0 resources and `staging/egress` still `UP` with 10. At 01:24:37 the account held 0 interface
  endpoints and the egress state 0 resources: the three `[E]` slices down, the release's teardown
  unhindered by `app_outputs`' infrastructure grant (step 15's measurement).

## 2026-10-26 — `make down ENV=sandbox`; the sitting's slices down but the hub and GitLab's cycle

*The user's hand for the down; Claude's for the readings as the infrastructure user (`awsds-infra-sandbox-1`),
reads only. Times UTC.*

- **[user]** `make down ENV=sandbox` after the Stage 9 session's `warehouse-compute` down of 01:37.
  **[Claude]** read at 02:00:37: 0 interface endpoints, 0 workgroups, 0 Studio apps running, and
  `sandbox/egress`, `sandbox/warehouse-compute` and `sandbox/probes` at 0 resources in state.
- **The estate at 02:00**: Staging down (01:24), Production's `workloads-egress` and `warehouse-compute` down
  (01:12 and 01:10, the Stage 9 session's), Sandbox down; the hub up for the Stage 7 session's GitLab cycle
  (its PR to come; Stage 9's is #262), `make hub-down` the sitting's last act after it.

## 2026-10-26 — `make hub-down`: the sitting's end

*The user's hand for the down; Claude's for the reading as the infrastructure user, `NO_PROXY='*'` with the
tunnel gone, reads only. Times UTC.*

- **[user]** `make hub-down` after the Stage 7 session's `make gitlab-down` (the host stopped 02:39:13, the
  shared-services endpoints gone 02:38:01). **[Claude]** read at 02:44:13: `awsds-prod-vpn` and
  `awsds-prod-gitlab` `stopped`, `awsds-prod-proxy` `stopping`; 0 interface endpoints in Production, Sandbox
  and Staging. The sitting that began with the environment down on 2026-10-25 ends with it down again, the
  three `[D]` hosts stopped and every `[E]` slice at 0 resources; the sessions' work is in PRs #261 (this
  one), #262 (Stage 9, merged) and #263 (Stage 7), and the `make gitlab-up` order fix of Stage 7's finding
  runs in a session of its own.

## 2026-10-26 — with the environment down: vii's third half read again, xxvii's parameter, 3.3's pin in the template, the record read against the plan

*Claude's hand, from a laptop session as the infrastructure user with `InfrastructureAccess`, no write to
AWS; the session that read Stages 7 to 10 for what is left. Times UTC.*

- **[Claude] Verification vii's third half** (`describe-domain` on both Sandbox domains and `lookup-events`
  in Sandbox's trail, 03:30 to 03:45): both domains carry the version-less `awsds-sandbox-dev-env`
  attachment in JupyterLab and the Code Editor, `LastModifiedTime` 2026-10-16 00:31:26Z and 2026-10-15
  06:14:06Z, as on 2026-10-25; the trail's last `UpdateStack` by the environment deployer is 2026-10-11
  22:05:48Z and the last `UpdateDomain` the infrastructure user's at 2026-10-16 00:31:25Z, none since.
  No reconciliation in fifteen days; the third half stays open on the same terms.
- **[Claude] xxvii's plan half**: the parameter
  `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64` still reads
  `ami-0829b74b2a8c619b7`, the runners' image, so the half still waits, and its plan needs the runners up.
- **[Claude] 3.3's snapshot pin, read in the template**: `glue/transform.py` takes `--SOURCE_SNAPSHOT` since
  v0.4.0 and appends `VERSION AS OF` to the governed query, its tests covering both forms; no workflow,
  slice or leg passes one. What §N.5 calls not written is the leg's source of the snapshot id and its path
  into the job's arguments, a decision before a template change, recorded in the waiting list with a
  recommendation (the job records the snapshot it read and takes a pin when one is given).
- **[Claude] The record read against the plan**: xxiv answered in the table from #102's `test-deploy`
  (2026-10-25); `v0.4.6` and 3.7's record (PR #261) added to the status cell; 3.1's text moved off the deploy
  image `v0.2.0`; 2.1 marked done (2026-10-14); 5.6's sentence on the archive never run dated; the Risks
  bullet on the mirror rewritten: pushed to `2d3160f1` on 2026-10-25, it lacks main's five commits of
  2026-10-26 (#261 to #265), the four `release.tf`s at `v0.4.6` and `production/runners/`' deploy-image pin
  among them, so `main` is pushed before the next tag (the waiting list's first table); `promotion.md`
  §N.1's done markers written; INT-07's and INT-08's measurements written in `integrations.md`;
  `CLAUDE.md`'s "planned and unapplied" on decision 27's egress grant (applied 2026-10-25) corrected.

## 2026-10-26 — after the Sandbox sitting, nothing up: decision 22 measured, 1.1's literal at 73 names, the lock's audit, decision 26's version 10

*Claude's hand, from a laptop session as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-prod`, `awsds-infra-sandbox-1`): reads and one read-only plan, no write to AWS. Times UTC.*

- **[Claude] Decision 22 measured**: the `dev` deploy ran from a space as the project role on 2026-10-26
  (Stage 10's log, 2.1): both workflows in the project's network under its key, the run `SUCCEEDED`, the CLI
  reading the role as a member and its boto3 finding the role's credentials with no configuration. Three
  findings stood between the recipe and the run, each answered in `sagemaker-application.md` §D: the
  SageMaker Distribution's CLI 1.0.8 first on the space's `PATH`, DataZone refusing `ListDomains` to the
  project role, and the MWAA Serverless API on `.api.aws` alone.
- **[Claude] 1.1's literal against the estate**: `vpc-egress-v0.19.0`'s tree equals `HEAD`'s
  `terraform-modules/vpc-egress` (`6f867470…`, Recipe B's content check); `./scripts/check-gitlab-mirror.py
  --plan` exit 0: `GM-1` the copy at `awsds/dev-env` `6ba33971a1d0` (2026-10-25), `GM-2` to `GM-4` 73
  entries, `61f1e1646df12c14` on both sides, `GM-5` to `GM-8` passing. The recipe changes, so the next tag
  is a minor, `default-v0.10.0`.
- **[Claude] The lock's audit on the laptop**, the gate's own command (`pip-audit` 2.10.1, OSV), 06:55:18 to
  06:57:30: 454 pins, 454 audited, 58 findings in 5 packages; by the gate's matcher against
  `GATES_PIP_AUDIT_ACCEPTED_DEV_ENV` (50 entries), 57 accepted by id or alias, none blocking, one warning
  (`nltk` 3.10.3, `PYSEC-2026-3740`, aliases `GHSA-8mgp-746c-j5xp` and `CVE-2026-81726`, no fixed version),
  no accepted entry gone. A dated verdict (Lesson 77), taken again the day of the tag.
- **[Claude] Decision 26's version 10**: ECR reads the base of `default-v0.9.1-746ef084` as
  `sha256:ac9bd82b…044e`, 3,754,767,181 bytes, and `default-v0.6.0`'s as `sha256:94359041…1975`,
  3,745,648,934 bytes; the two share their first 25 of 30 layers, as v0.8.0's did on 2026-10-22, and the
  copy's `base/` holds no commit since `default-v0.8.0`. Version 10 is equivalent to `app-etl`'s base by the
  decision's definition, and the waiting list's row for it is removed.
- **[Claude] xxiii's counts**: the `test` project's `app_etl` at 12 versions and its `_train` twin at 6, the
  `dev` project's at 1 each, `houseprice-etl` at 3.
- **[Claude] xxvii's plan half**: the Amazon Linux parameter still reads `ami-0829b74b2a8c619b7` (modified
  2026-10-24 21:01 UTC), so the half waits.
- **[Claude] What changed in the record**: 1.1's bullet, decisions 22 and 26, xxiii and the status cell;
  `sagemaker-application.md` §D rewritten as the sequence that ran; `upstream-releases.md` (1.0.9 still the
  newest on PyPI, the domain lookup's row), `docs/SMUS.md`, `dev-env.md` and `sg-proxy.md` at 73 names;
  `promotion.md` §N.7.1, the GitLab sitting for `default-v0.10.0`, and the waiting list's image row.

## 2026-10-26 — xxviii's active half: the user's option B, the job written

*Claude's hand, no AWS call. The user's decision, taken in the chat of the session forked from this one and
relayed by it: "Stage 8 xxviii, metade ativa = opção B. Um job manual no runner de deploy na próxima
sentada do GitLab (a da default-v0.10.0, promotion.md §N.7.1) chama AssumeRole de um papel de deploy pelo
endpoint global sts.amazonaws.com; lê-se a trilha de us-east-1 e a mensagem da regra 4.6. Sem alargar
trust."*

- **[Claude] What the job can read**, from the code: the deploy roles' trust, `OnlyTheDeployRunner`, admits
  the runner's role with no condition, so the runner's assumption through the global endpoint succeeds; the
  misuse rule's pattern exempts the runner's role by its unique id (`anything-but` prefix), so the runner's
  assumption fires no rule through either endpoint, and 4.6's message cannot appear in this form. The job
  reads the Region each record lands in: a record written in `us-east-1` reaches no `us-west-2` rule,
  whoever its caller. The `aws:RequestedRegion` clause stays unread, the trust pinning nothing.
- **[Claude] The job**: `sts-global-probe` in the copy of `awsds/dev-env`'s pipeline
  (`gitlab/awsds/dev-env/.gitlab-ci.yml`), tag `awsds-deploy`, `needs: []`, created only in a pipeline run
  on the default branch with `STS_GLOBAL_PROBE` set, and manual there. As the runner's own role it assumes
  both deploy roles through `sts.us-west-2.amazonaws.com` and through `sts.amazonaws.com`, session name
  `xxviii-<pipeline id>`, and prints each ARN; its script parses under `bash -n`. It reaches GitLab with
  `default-v0.10.0`'s merge request.
- **[Claude] The record**: xxviii's row, `promotion.md` §N.5, §N.6 and §N.7.1 step 7, and the waiting
  list's GitLab row.

## 2026-10-26 — decision 1's zlib pair: the user's option A, the baseline written for gates-v0.6.0

*Claude's hand, no AWS call. The user's decision as the Dev Env Steward, taken in the chat of the session
forked from this one and relayed by it: "Stage 8 decisão 1, par zlib = opção A. CVE-2026-85091 em zlib e
zlib1g entra na baseline da linhagem SageMaker por nome, datado e atribuído ao usuário, em
ci-gates/baselines.gitlab-ci.yml, tag gates-v0.6.0 antes da imagem default-v0.10.0 (o include ref do
awsds/dev-env move junto)."*

- **[Claude] The baseline**: `CVE-2026-85091|zlib` and `CVE-2026-85091|zlib1g`, `HIGH 1.3.dfsg-3.1ubuntu2.2`
  as `default-v0.9.1`'s scans read them on 2026-10-25, appended to `GATES_BASELINE_SAGEMAKER_DISTRIBUTION`
  in the copy's `ci-gates/baselines.gitlab-ci.yml`, the list's comment naming the acceptance, its date and
  `gates-v0.6.0`. The deploy lineage's `CVE-2026-85091|zlib`, Debian's package, is unchanged.
- **[Claude] The sitting**: `promotion.md` §N.7.1 gains step 3, the merge request on `awsds/ci-gates`, the
  tag and its commit read back into the image project's `include:` `ref`, before step 4's merge request on
  `awsds/dev-env`; the application template's pin moves with its own next merge request.
- **[Claude] The record**: 1.4's text, the waiting list's GitLab row, `promotion.md` §N.6 and §N.7.1.

## 2026-10-26 — decision 22's third part read against the distribution's start scripts: the `ENV PATH` order reaches no space

*Claude's hand (the session of PR #269), from a laptop with no AWS call: the SageMaker Distribution
4.5.2's sources, libmamba's activation and the micromamba image read on GitHub.*

- **[Claude] A space's `PATH`**: the distribution's `ENV PATH` opens `/etc/sagemaker-inference-server:/opt/conda/bin`;
  `entrypoint-sagemaker-ui-jupyter-server` and `start-sagemaker-ui-jupyter-server` each run `micromamba
  activate base` before `jupyter lab`, as the Code Editor's pair does; libmamba (`micromamba-1.5.11` and
  `main`) puts `/opt/conda/bin` first on activation and, on a reactivation, removes it and puts it first
  again; the server's `terminado_settings` is `{"shell_command": ["/bin/bash"]}`, so a terminal inherits the
  server's `PATH`. The house `bin` ahead of `/opt/conda/bin` on the image's `ENV PATH` leaves
  `aws-smus-cicd-cli` the distribution's 1.0.8 in a space, and a smoke `RUN`, unactivated
  (`_dockerfile_shell.sh` activates only when `MAMBA_DOCKERFILE_ACTIVATE` is `1`, an `ARG` of the
  distribution's own build), reads the house's and passes. The order reaches what runs unactivated: a
  descendant's `RUN`, and, when the container starts without `_entrypoint.sh`, `apply_patches.sh`, whose
  `pip show botocore` and `pip show hdijupyterutils` decide the patches it applies to `/opt/conda`. The house
  lock carries `jupyterlab`, `jupyter-server`, `jupyter-core`, `notebook`, `ipython` and `pip`, so the whole
  `bin` placed where it survives the activation would start the house's JupyterLab as the space's server.
- **[Claude] The form prepared, not in the recipe copy**: `/opt/awsds/bin` holding a symlink to the house
  CLI's entry point alone, prepended by `/opt/conda/etc/conda/activate.d/zz-awsds-bin.sh`, one `case` that
  returns 0 under `set -euf -o pipefail` (run under bash and sh on the laptop), and libmamba exports `PATH`
  before it sources the hook; the smoke reading the name after `micromamba activate base`, failing unless it
  resolves under `$AWSDS_PYTHON_ENV/bin/` and `--version` reports the house environment's version. Neither
  Dockerfile was built. The hook is a file of ours in the distribution's environment, which the user's rule
  of 2026-09-10 leaves as it ships, so the choice between it and no third part is the user's.
- **[Claude] The record**: decision 22 and 1.1's bullet; `promotion.md` §N.7.1 steps 4 and 6;
  `docs/SMUS.md`; a platform entry in `lessons.md`; `docs/REFERENCES.md`.

## 2026-10-26 — 3.3's snapshot, option A, written in the template

*Claude's hand (the session of PR #269), from a laptop with no AWS call; the decision the user's, relayed
by the session the user forked.*

- **[user] Option A**: the Glue job records the snapshot of `curated.trades` it read and keeps taking
  `--SOURCE_SNAPSHOT`; the leg, the chains and the workflows unchanged; the parity of Staging and
  Production by id (option B) waits until it is a requirement.
- **[Claude] The template** (`b65233b1`): `glue/transform.py` reads at the pinned snapshot or else the
  table's current one, `SHOW TBLPROPERTIES <table> ('current-snapshot-id')`, appends `VERSION AS OF <id>`
  and writes `trades.source.json` beside `trades.csv` once `keep_one_file` has emptied the prefix (the
  table, the snapshot, whether pinned); a table reporting no current snapshot fails the run.
  `src/app_etl/pipeline.py` copies a CSV's record into its summary as `source`, and
  `code/app_etl_tasks.py`'s report carries it. The job role's `s3:PutObject` on the outputs bucket covers
  the record. `uv run pytest` 45 passed, ruff clean, the lint at `d856982c` *"ok: 9 arquivo(s)"*,
  `./scripts/render-workflow.py --check` OK. Unrun until the next tag's Staging leg, where `SHOW
  TBLPROPERTIES` meets the job's Lake Formation catalog for the first time.
- **[Claude] The record**: 3.3, its 3.8 sub-bullet and the status cell; `sagemaker-application.md` §E, §G
  and §V; the template's README.

## 2026-10-26 — decision 22's third part taken as the activation hook, written in the recipe copy; the report upstream posted as issue 413

*Claude's hand (the session of PR #269), from a laptop with no AWS call but one `sts get-caller-identity`;
the choice and the issue the user's, in that session's chat.*

- **[user] The choice**: the base environment's activation hook with the narrow directory, over no third
  part.
- **[Claude] The recipe copy** (`e7901335`): `dev-env/Dockerfile` adds `/opt/awsds/bin`, a symlink to
  `$AWSDS_PYTHON_ENV/bin/aws-smus-cicd-cli` alone, and `/opt/conda/etc/conda/activate.d/zz-awsds-bin.sh`,
  one `case` prepending it after each `micromamba activate base`; `smoke/Dockerfile` reads the name after
  that activation, fails unless it resolves under `$AWSDS_PYTHON_ENV/bin/` and `--version` reports the
  house environment's version, and writes `cicd-cli.txt`; the copy's README carries both. Both `RUN`
  bodies pass `bash -n`; neither Dockerfile was built. `make check-docs` and the hooks pass.
- **[user] The report upstream**: aws/CICD-for-SageMakerUnifiedStudio issue 413, opened from the PR's
  draft; **[Claude]** read open, created 18:25:19 UTC, its title the draft's.
- **[Claude] The record**: decision 22, 1.1's bullet, Stage 10 2.1, `promotion.md` §N.7.1 steps 4 and 6
  and §N.7.3, `sagemaker-application.md` §A, §D and §M, the template's README and script, `docs/SMUS.md`,
  `upstream-releases.md`, `lessons.md`, `docs/REFERENCES.md`.

## 2026-10-26 — the GitLab sitting (`promotion.md` §N.7.1), step 1: the lock's audit and the copy against the estate, the day of the tag

*Claude's hand, from a laptop session as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-sandbox-1`): reads and one read-only plan, no write to AWS. Times UTC.*

- **[Claude] The copy against the estate**, `./scripts/check-gitlab-mirror.py --plan`, 21:08:01 to 21:08:27,
  exit 0: `GM-1` the copy at `awsds/dev-env` `6ba33971a1d0` (2026-10-25), `GM-2` to `GM-4` 73 entries,
  `61f1e1646df12c14` on both sides, `GM-5` to `GM-8` passing.
- **[Claude] The lock's audit on the laptop**, the gate's command with its JSON report and matcher (`pip-audit`
  2.10.1, OSV), 21:08:01 to 21:11:08: 454 pins, 454 audited, 58 findings in 5 packages; against
  `GATES_PIP_AUDIT_ACCEPTED_DEV_ENV` (50 entries), 57 accepted by id or alias, fsspec's `PYSEC-2026-4217`
  through its alias `CVE-2026-104851`, none blocking, one warning (`nltk` 3.10.3, `PYSEC-2026-3740`, no fixed
  version), no accepted entry gone. The morning's reading (06:55), so the tag meets no new finding.
- **[Claude] The checkout**: the project folder on `main` at `94ed050d`, `origin`'s, clean, the `gitlab`
  remote in place.

## 2026-10-26 — §N.7.1 step 3: `gates-v0.6.0` with decision 1's zlib pair; the image's `include:` `ref` moved

*The user's hand for the push, the merge request's merge and the tag, as the Dev Env Steward (GitLab's
`felipenoris`); Claude's for the clone, the branch's commit, the reads (`git ls-remote`, the API through the
user's GitLab session in Chrome) and the copy's edit. Times UTC.*

- **[Claude] Before**: `git ls-remote` at 21:21:03, `main` at `7c3552b7` (`gates-v0.5.0`), tags `gates-v0.1.0` to
  `gates-v0.5.0`, so `gates-v0.6.0` free. A clone at `$HOME/tmp/ci-gates-v0.6.0` differed from this
  repository's `ci-gates/` in `baselines.gitlab-ci.yml` alone; the branch `zlib-pair` carried it as `acd31c6`,
  the message naming the acceptance: *"accepted by name in the SageMaker Distribution lineage (the Dev Env
  Steward, 2026-10-26)"*, the pair new in `default-v0.9.1`'s scans and identical in `base` and `dev-env`.
- **[user] The merge request**: the push opened `awsds/ci-gates` !1 at 21:26:50; the branch pipeline #104 green
  (`baselines-shape`, `secret_detection`, `secret-detection-gate`); merged at 21:28:20 as `d0b895c8` (parents
  `7c3552b` and `acd31c6`), `main`'s pipeline #105 green. **[Claude]** `main`'s four files byte-equal to
  `ci-gates/`; `gates-v0.6.0` still free at 21:28:41.
- **[user] The tag** `gates-v0.6.0` on `d0b895c8`, its pipeline #106 green at 21:31 (`baselines-shape`).
  **[Claude] Read back** at 21:33:44: `refs/tags/gates-v0.6.0` at `d0b895c8159e655f6e4af83cc096e37993087c81`.
- **[Claude] The copy**: `gitlab/awsds/dev-env/.gitlab-ci.yml`'s `include:` `ref` from `7c3552b7` (`gates-v0.5.0`)
  to `d0b895c8` (`gates-v0.6.0`), the only gates pin in the copy, carried by step 4's merge request.
  `./scripts/check-gitlab-ci.py` OK: `dev-env`'s 12 jobs from 3 files, 44 script items under `bash -n`.

## 2026-10-26 — §N.7.1 step 4: `awsds/dev-env` !12, the 73-name literal, the activation hook and the probe job merged

*The user's hand for the push and the merge, as the Dev Env Steward; Claude's for the clone, the branch's
commit, the reads (the API through the user's GitLab session in Chrome) and the mirror script. Times UTC.*

- **[Claude] The branch**: a clone at `$HOME/tmp/dev-env-v0.10.0`, `main` at `6ba3397` (the copy's commit), the copy
  under `gitlab/awsds/dev-env/` written over it with `rsync --delete`: four files, `.gitlab-ci.yml` (the
  `include:` at `gates-v0.6.0`, `sts-global-probe`), `README.md`, `dev-env/Dockerfile` (the 73 names, the
  activation hook) and `smoke/Dockerfile` (the CLI read after `micromamba activate base`), 90 insertions and 9
  deletions, committed as `8d904e7` on `no-proxy-73-cli-hook`.
- **[user] The merge request** `awsds/dev-env` !12, opened by the push at 21:33:00; its pipeline #107 green from
  21:33:06 to 21:34:32 on the test runner: `recipe-checks` *"NO_PROXY_LIST: 73 entries"*, the managed
  settings parsing; `pip-audit` *"== awsds/dev-env: 50 accepted finding(s)"*, *"Found 58 known vulnerabilities in
  5 packages"*, nltk 3.10.3's `PYSEC-2026-3740` `warn`, *"454 of 454 pinned package(s) audited, 0 blocking
  vulnerability(ies)"*, the laptop's reading of 21:11; `secret_detection` and its gate green. Merged at
  21:44:01 as `c8bac16e`; `main`'s pipeline #108 started 21:44:02.
- **[Claude] The copy read back**: `./scripts/gitlab-mirror.py awsds/dev-env` at 21:44 *"the copy already holds
  this commit's 14 file(s)"*, `gitlab/mirror.json` at `c8bac16e`. `default-v0.10.0` free at 21:44:23, the
  project's newest tag `default-v0.9.1`.

## 2026-10-26 — §N.7.1 step 7: the infrastructure mirror at `main`

*The user's hand for the push from the project folder; Claude's for the reads (`git ls-remote`, the project's
events through the user's GitLab session in Chrome). Times UTC.*

- **[user] `git push gitlab main`** from the project folder at `94ed050d`. **[Claude] Read** at 21:47:30: the
  event *"pushed to"* `main` by `felipenoris` at 21:29:16, `2d3160f1` to `94ed050d`, 8 commits (#261 to #269);
  `awsds/infrastructure`'s `main`, `origin`'s and the project folder's all at `94ed050df119`. The next tag's
  legs clone the commit `origin/main` holds.

## 2026-10-26 — §N.7.1 step 8: verification xxviii's active half, `sts-global-probe` and the trails

*The user's hand for the pipeline and the manual job on `awsds/dev-env`; Claude's for the reads: the job log
through the user's GitLab session in Chrome, CloudTrail, EventBridge and CloudWatch as the infrastructure user
with `InfrastructureAccess` (`awsds-infra-prod`, `awsds-infra-staging`). No trust widened. Times UTC.*

- **[user] The run**: *Build → Pipelines → Run pipeline* on `main` (`c8bac16e`) with `STS_GLOBAL_PROBE=1`,
  pipeline #110 (21:50:47, `web`), then the manual job `sts-global-probe` (#649), 21:51:30 to 21:51:48 on
  `awsds-prod-runner-deploy-i-05e260a19231bb5e5`. **[Claude] Its log**: *"caller:
  arn:aws:sts::<Production>:assumed-role/awsds-prod-runner-deploy/i-05e260a19231bb5e5"*, then
  `assumed-role/awsds-deploy-prod/xxviii-110` through `https://sts.us-west-2.amazonaws.com` and through
  `https://sts.amazonaws.com`, and `assumed-role/awsds-deploy-staging/xxviii-110` through each; *"Job succeeded"*.
- **[Claude] The trails** (`lookup-events`, 21:52 to 21:57), six records, each with no error:

  | Trail | Region | Time | Role | Host header |
  |---|---|---|---|---|
  | Production | `us-west-2` | 21:51:42 | `awsds-deploy-prod` | `sts.us-west-2.amazonaws.com` |
  | Production | `us-east-1` | 21:51:43 | `awsds-deploy-prod` | `sts.amazonaws.com` |
  | Production | `us-west-2` | 21:51:46 | `awsds-deploy-staging`, the caller's copy | `sts.us-west-2.amazonaws.com` |
  | Production | `us-east-1` | 21:51:47 | `awsds-deploy-staging`, the caller's copy | `sts.amazonaws.com` |
  | Staging | `us-west-2` | 21:51:46 | `awsds-deploy-staging`, caller `AWSAccount` | `sts.us-west-2.amazonaws.com` |
  | Staging | `us-east-1` | 21:51:47 | `awsds-deploy-staging`, caller `AWSAccount` | `sts.amazonaws.com` |

  Each global call's records sit in `us-east-1` alone and each regional call's in `us-west-2`, in both
  accounts. In Staging's `us-east-1` trail the `xxviii-110` record is the role's only assumption since
  2026-10-25; every earlier one, the legs' `botocore-session-*`, is in `us-west-2`, xxviii's passive half.
  A first watch of the trails reported Staging empty: its `jq` filter failed on the cross-account caller's
  null `userIdentity.arn` and dropped the account's answer; the resource-name lookup above read both records,
  the earlier assumptions its positive control (Lesson 62).
- **[Claude] The rules**: `awsds-prod-deploy-misuse` and `awsds-staging-deploy-misuse` live in `us-west-2`
  (`ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`); `events:ListRules` in `us-east-1` answers *"with an explicit
  deny in a service control policy"* (the Region ceiling) in both accounts, so no rule there can be read or
  written by these principals. `MatchedEvents`, `TriggeredRules` and `Invocations` read no datapoint from 21:00
  to 22:04 for either rule, against one `TriggeredRules` each at 2026-10-13 05:00 (verification xvi's firing),
  the instrument's positive control: the runner's role is exempt, and nothing fired.
- **[Claude] The verdict**: an `AssumeRole` of a deploy role through `sts.amazonaws.com` is recorded in
  `us-east-1` and never reaches 4.6's rules, which see `us-west-2` alone, whoever the caller; the Region ceiling
  keeps a rule out of `us-east-1`. Whether a trust pinning `aws:RequestedRegion` refuses the global call stays
  unread, the deploy roles' trust pinning nothing.

## 2026-10-26 — §N.7.1 steps 5 and 6: `default-v0.10.0` released, Sandbox's version 11, `DE-5` passing

*The user's hand for the tag and the release gate, as the Dev Env Steward; Claude's for the readings: the
pipeline API, the job logs and the artifacts through the user's GitLab session in Chrome, and ECR and
SageMaker as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`,
`awsds-infra-sandbox-1`), reads only. Times UTC.*

- **[user] The tag** `default-v0.10.0` on `c8bac16e`, read at 21:46:37 (`refs/tags/default-v0.10.0`), free at
  21:44:23. Pipeline #109, created 21:46:14: `pip-audit` (#637) 21:46:17 to 21:47:48, its reading the branch's;
  `recipe-checks` (#638) 6 s; `build-images` (#639) 21:47:49 to 22:04:09, 980 s.
- **[Claude] The images in ECR**: `awsds-prod-ecr-base:default-v0.10.0-c8bac16e` pushed 21:51:10, 3,754,767,169
  bytes, `sha256:78e253ce9f0785f3b4c02293ecbf0225378f5262f0e493ef515b58840e07f741`, 12 bytes under `v0.9.1`'s
  with `base/` unchanged; `awsds-prod-ecr-dev-env:default-v0.10.0-c8bac16e` pushed 22:02:20, 6,688,199,603 bytes,
  `sha256:658c05d125554950cbac0ad204c44b9fd46b19a6c5508d55f36c9ea8456c19f9`, 300,273 bytes over `v0.9.1`'s. The
  smoke runs after both pushes in `build-images`, so a red smoke would have spent the release tag and both ECR
  tags, the next release being a patch from a fixed commit.
- **[Claude] The smoke, decision 22's first reading**: step `[check 7/9]`, after `micromamba activate base`,
  *"aws-smus-cicd-cli by its name: /opt/awsds/bin/aws-smus-cicd-cli -> /opt/awsds/venv/bin/aws-smus-cicd-cli,
  'aws-smus-cicd-cli 1.0.9'; the house environment carries 1.0.9"*. The manifests against `v0.9.1`'s (job
  #569): `cicd-cli.txt` new; `proxy.txt` 73 entries, sha256 `61f1e1646df12c14`, against 72 and
  `6faf2e4761622508`; `runtimes.txt` the same but the base digest; `trust.txt`, `imports.txt`, `julia.txt`,
  `r.txt` (70 lines), `python-awsds.txt` (454) and `python-conda.txt` (621) identical.
- **[Claude] Both scans**: ECR's scan of `base` complete 21:53:16 and of `dev-env` 22:07:03, each CRITICAL 113 and
  HIGH 612; `scan-base` (#640) and `scan-dev-env` (#641) *"CRITICAL and HIGH: 725 found, 132 in the baseline"*,
  *"WARN: 593 CRITICAL or HIGH finding(s) absent from the baseline"*, all 593 `linux-libc-dev`, both failed as
  allowed: the zlib pair is in the baseline since `gates-v0.6.0` (130 to 132), and no finding is new.
- **[user] `release-gate`** (#642) 22:08:19 to 22:08:27. **[Claude]** `register` (#643) 22:08:28 to 22:08:56:
  *"awsds-sandbox-dev-env version 11: CREATED, alias 0.10.0"*, `ContainerImage` at the pushed digest; `retire`
  (#644) 22:08:59 to 22:09:36: 5 versions, *"keep"* 11 (`0.10.0`), 10 (`0.9.1`), 9 (`0.8.0`), 8 (`0.7.3`) and 7;
  the pipeline `success` at 22:09:36, 22 min 39 s from the tag to the version, the gate waiting 34 s.
- **[Claude] AWS read back** at 22:09: `list-image-versions` 11 to 7 `CREATED`, version 11 created 22:08:53,
  `ContainerImage` and `BaseImage` at the dev-env digest, release notes `default-v0.10.0-c8bac16e`; aliases
  `0.10.0`, `0.7.3`, `0.8.0`, `0.9.1`. `./aws/devenv.py`: **`DE-5` passing**, *"version 11,
  sha256:658c05d12555...: 73 names, sha256 61f1e1646df12c14"*; `DE-1` (73 entries) and `DE-4` passing; `DE-2`
  failing with `sandbox/egress` down, the reading of 2026-10-25, so `DE-3` and `DE-6` are not compared.
- **[Claude] The release row** in the copy's README, both digests and sizes; the branch `the-releases-v0.10.0`
  at `fb5722b` in the clone, for GitLab's `main` by the steward's hand.

## 2026-10-26 — §N.7.1 after the release: the README row on GitLab's `main`; the plan read against the sitting

*The user's hand for the push and the merge, as the Dev Env Steward; Claude's for the branch's commit, the
mirror script and the record. Times UTC.*

- **[user] The release row**: the branch `the-releases-v0.10.0` (`fb5722b`, one line in `README.md`) pushed with
  its merge request and merged as `6eff9056` (22:14:02). **[Claude]** `./scripts/gitlab-mirror.py awsds/dev-env`
  at 22:16 *"the copy already holds this commit's 14 file(s)"*, `gitlab/mirror.json` at `6eff9056`.
- **[Claude] What the sitting changed in the plan**, at the user's request to read it against the findings:
  1.1's and 1.4's bullets and decision 22 marked done; xxviii's row answered and **decision 29** opened, the
  global STS endpoint past 4.6's rules, recommended (b), an SCP statement, not taken; the status cell;
  `promotion.md` §N.6, §N.7.1 (its run, step 10's `proxy-off` and `NO_PROXY='*'`) and §N.7.3; `gitlab.md` §U (the
  agent's reading of 21:18, the down's `proxy-off` and `NO_PROXY='*'`) and the client runbook's §2; a Systems
  Manager entry in `lessons.md`'s platform list; version 11 in `sagemaker-application.md` §D step 4,
  `sg-proxy.md`, `dev-env.md`, `docs/SMUS.md`, `upstream-releases.md`, Stage 10 2.1 and `AWS_STATE.md`'s `DE-5`
  row; the waiting list (the image's and the mirror's rows removed, decision 29 added, the Hub, GitLab and
  Promotion sittings' rows trimmed, the backup of 22:15 dated); `GENERAL_PLAN.md`, `stages/INDEX.md`,
  `docs/log/INDEX.md` and `CLAUDE.md`'s Current position.

## 2026-10-26 — amending the record's entry above: the hub-down changes withdrawn

*Claude's hand, on the user's correction in this chat, quoted in Stage 7's log: no `make hub-down` ran before
the readings that took it as stopping nothing.*

- **[Claude] Withdrawn** from the changes the entry above lists: `promotion.md` §N.7.1 step 10's `proxy-off` and
  `NO_PROXY='*'`, `gitlab.md` §U's on the down, and the client runbook's §2. §N.7.1's run keeps the two readings
  that stand, the smoke after both pushes and GitLab's agent's late first call.
