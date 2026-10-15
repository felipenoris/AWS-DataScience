# `ci-gates/` — the shared security gates

The content of the GitLab project **`awsds/ci-gates`** (Stage 8 step 5, decision 10): the gates every
pipeline includes, written once, and the findings each image lineage carries with a person's
acceptance. This directory is the reviewed source, and the project receives it by a push (runbook
[`gitlab.md`](../docs/plan/runbooks/gitlab.md) §G); nothing here is applied by Terraform.

| File | What it is |
|---|---|
| [`gates.gitlab-ci.yml`](gates.gitlab-ci.yml) | the gates: Secret Detection and its gate, `pip-audit`, `checkov`, and the template of the ECR scan gate |
| [`baselines.gitlab-ci.yml`](baselines.gitlab-ci.yml) | the accepted CRITICAL and HIGH findings, one list per image lineage, which the scan gate compares against |
| [`.gitlab-ci.yml`](.gitlab-ci.yml) | the project's own pipeline: the gates run on itself, and a check of the baselines' shape |

## Including the gates

A pipeline takes both files at one commit of the project, the gates release's tag beside it for a reader:

```yaml
include:
  - project: awsds/ci-gates
    ref: <commit>                # gates-v<semver>
    file: [/gates.gitlab-ci.yml, /baselines.gitlab-ci.yml]
```

The commit and not the tag: a tag can be deleted and pushed again at another commit, a commit cannot
change. The pipeline declares a `test` stage, and whoever runs a pipeline that includes the project needs
read access to it, so the four persona groups are its members (Reporter at least).

| Gate | Runs | Blocks on | Set by the including pipeline |
|---|---|---|---|
| `secret_detection` + `secret-detection-gate` | every branch pipeline, on the test runner | any finding in the scanned commits (5.3) | nothing |
| `pip-audit` | every pipeline, on the test runner | a known vulnerability with a fixed version, in the runtime set the lock pins, unless the project's accepted list names it; and fewer packages audited than the export pins (5.2, decision 15) | `GATES_UV_PROJECTS`: the uv projects, space-separated paths |
| `checkov` | every pipeline, on the test runner | any failed check (5.1) | `GATES_CHECKOV_DIRS`: the Terraform directories, space-separated |
| `.gates-ecr-scan` | the job that extends it, after an image push, on the build runner | nothing: it lists each CRITICAL or HIGH finding absent from the lineage's baseline, and the job may fail without stopping the pipeline (1.4, 5.4) | `needs:` on the push job, a stage, the protected-tag rule, `SCAN_REPOSITORY`, and `SCAN_DIGEST` from the push job's dotenv report |

The test runner (tag `awsds-test`) holds no AWS identity its jobs can reach (decision 11); the scan gate is
untagged, so it lands on the build runner, the protected runner whose role reads the scan. Each rule is
decision 1's, recorded in the stage file. The scan gate informs since the user amended decision 1 on
2026-10-14: the operator reads its log before a deployment, and a red scan job never stops one.

## The baselines

A line is `<finding>|<package>` and nothing else is compared; the severity and the version after `#` are
for the reader. The repository an image was pushed to chooses the list, never the pipeline:

| Lineage | Repositories | Seeded from |
|---|---|---|
| `GATES_BASELINE_SAGEMAKER_DISTRIBUTION` | `awsds-prod-ecr-base`, `-dev-env` and every `awsds-prod-ecr-app-*`, each `FROM` base | `default-v0.6.0`, scanned 2026-10-12: CRITICAL 0, HIGH 130 |
| `GATES_BASELINE_DEPLOY` | `awsds-prod-ecr-deploy` | `v0.1.0`, scanned 2026-10-13: CRITICAL 2, HIGH 8 |

pip-audit's accepted lists follow the same rule, chosen by the project's path, which GitLab sets
(`CI_PROJECT_PATH`), and never by the gated pipeline:

| List | Project | Seeded from |
|---|---|---|
| `GATES_PIP_AUDIT_ACCEPTED_DEV_ENV` | `awsds/dev-env`, its `dev-env/python/uv.lock` | the lock a targeted `uv lock --upgrade-package` left on 2026-10-14: 8 findings whose fixed version another package of the environment forbids (fsspec, setuptools, sqlparse), accepted by name by the user as the Dev Env Steward |

**A finding enters a list by name**, in a reviewed commit whose message says who accepted it and why; for
the SageMaker Distribution lineage that is the Dev Env Steward approving the release that carries it
(decision 1). A finding the gate prints as no longer found leaves the list in the next commit. A new gates
release is a tag on the project's `main`, and each consumer moves its `ref` to it in a commit of its own.
