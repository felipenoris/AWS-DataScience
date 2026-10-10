# Log — Stage 6i — Sandbox orchestration

*The stage file is [`docs/plan/stages/stage-06i-sandbox-orchestration.md`](../plan/stages/stage-06i-sandbox-orchestration.md).
Every entry names whose hand wrote it. `[Claude]` is a reading or an authored change; `[Claude⚡]` is
an AWS write; `[user]` is something done by hand, with any measurement pasted verbatim.*

*Identifiers are redacted as [`INDEX.md`](INDEX.md) requires: an account id becomes the account's name
in angle brackets, an e-mail address inside an ARN becomes that user's role. Everything else in a pasted
output stays verbatim. All times UTC.*

---

## 2026-10-10 — pass 0: the readings, the CLI, the instrument and the files

*Written by Claude in the sitting that ran it, at the user's instruction to start pass 0. Every reading is
Claude's own, from `awsds-infra-sandbox-1` (account `<Sandbox Account 1>`, permission set
`InfrastructureAccess`). Nothing was written to AWS.*

### [user] 0.2 — the CLI

**[user]** "Atualizei o aws cli para v2.37.12."

**[Claude]** `aws --version` reads `aws-cli/2.37.12`, and `aws mwaa-serverless create-workflow help`
carries `--code`. `get-workflow` on the two earlier workflows returns `Code` and `CodeSnapshottedAt` as
null: neither has a Python or Bash task.

### [Claude] 0.1 — the identifiers

| What | Value |
|---|---|
| project | `avhvbqn37ty7m8`, domain `dzd-d8yrvx1ko7im6o`, the only project role in the account |
| project key | `alias/awsds-sandbox-project`, the role's `KmsKeyId` tag, `Enabled`, `CUSTOMER` |
| project storage | `awsds-sandbox-smus-projects`, prefixes `dev/` and `shared/` under the project; no `shared/orchestration-demo/` yet |
| network the portal puts on a workflow | `awsds-sandbox-private-usw2-az1` and `-usw2-az2`, security group `datazone-avhvbqn37ty7m8-dev` |
| house image | `awsds-sandbox-dev-env` version 5, `sha256:8ec04e357792e4cb1beaace2c1dcfde0f60ba6074195cc31091452e11db89dd6`, in `<Production Account>`'s `awsds-prod-ecr-dev-env` |

`./aws/devenv.py` exited 2 on `DE-2` alone: the state of `sandbox/egress` holds no outputs because the
slice is down, the expected reading between sessions.

### [Claude] Readings the plan did not have

- **The portal stores the visual layout as the definition's first line**, a YAML comment carrying each
  task's canvas position: `# {"S3-task":{"x":430,"y":230}}`. The task's operator is the full class path,
  `airflow.providers.amazon.aws.operators.s3.S3CopyObjectOperator`.
- **A task instance id is `ex_<uuid>_<task id>_<attempt>`**, and a retried task lists every attempt with
  its own status (`UP_FOR_RETRY`, then `FAILED`), in an order that is not the attempts' order.
- **`MyWorkflow` holds five versions** (2026-08-27 to 2026-09-10) and `simple-s3-copy` one, so every
  definition edit of 6d's sittings is still readable with `get-workflow --workflow-version`.
- **The workflows' log groups are encrypted with the project key** and have no retention.

### [Claude] 0.3 — `./aws/sandbox-orchestration.py`, the before

Exit 0. `SO-1` notes the three contract workflows absent, `SO-5` no processing job, `SO-6`
`/aws/sagemaker/ProcessingJobs` absent, `SO-7` an empty `orchestration-demo/` and no package uploaded,
`SO-8` no `CreateProcessingJob` in the trail window.

A self-test pointed the contract at the two earlier workflows, in memory, to exercise `SO-2`..`SO-4`
before any contract workflow exists:

- `SO-1` attributed both creations to the project role from CloudTrail;
- `SO-2` passed both: the project role, both private subnets in two AZs, no default route, the project's
  security group and key;
- `SO-3` saved all six versions, and the sanitized copies carried no account id to replace.

It also found one defect, fixed before the commit: `SO-4` read a retried task's state from the last
attempt the listing returned, and reported `UP_FOR_RETRY` for a run whose last attempt `FAILED`. The
self-test's outputs were deleted.

### [Claude] 0.4 — the files

`examples/sandbox-orchestration/` holds the following, and the repository layout in `README.md` names it:

- the project `awsds-demo-job`, whose 6 tests pass;
- the two paste-ready processing configurations;
- the operator files and their build script;
- the sample;
- `render.py`.

`render.py --values` read the same project, security group and subnets as 0.1, which the portal also
uses, and the probe configuration rendered to valid JSON.
