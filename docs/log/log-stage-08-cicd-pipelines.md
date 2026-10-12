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
