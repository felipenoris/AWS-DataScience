# Stage 18 — A deployment-only SageMaker project in Staging, measured and unwound

| | |
|---|---|
| **Status** | **Not started. Written 2026-10-17** from a cloud session with no AWS reading, on the user's word of that day at 18:28 UTC (*"vamos medir em staging o que falta para completar o quadro"*), the answer to the card of 2026-10-16 that offered to measure before [Stage 10](stage-10-orchestration-promotion.md) builds [D41](../decisions/D41-sagemaker-application.md) item 2. A measurement and its teardown, not a build: AWS's default shape for a deployment account, a SageMaker Unified Studio project that the CI/CD CLI deploys into and no person works in, is created once in `Staging`, read against this estate's perimeter, and unwound at pass 8 whatever the verdict. **D41 stands until the verdict** (8.9, decision 7): Stage 10 keeps item 2's design, no project in Staging or Production, while this stage runs. Nothing below is a measurement unless it carries its date |
| **Prerequisites** | **[Stage 8](stage-08-cicd-pipelines.md)**: `awsds-deploy-staging` and the deploy runner (pass 1), the deploy image `v0.2.0` with the CLI 1.0.9, and `app-etl` as an application whose release carries a bundle (2.5, 2.5a) and whose `process` task names a `VolumeKmsKeyId`: its `ClusterConfig` holds none on `main`, and `DenySageMakerJobsWithoutVolumeEncryption` refuses such a job in `Workloads` and under Sandbox's D13 boundary alike [inferred from the two documents: the application has not run]. **[6a](stage-06a-unified-studio.md)**: the domain `awsds-studio` and the profile machinery of `data-governance/governance/`. **[6b](stage-06b-development-becomes-staging.md) pass 1**: the unwinding order pass 8 repeats, measured on this account on 2026-09-06. **[6c](stage-06c-networking-hub.md)**: Staging's private routing and its 11 `[E]` endpoints, so a sitting is `make hub-up` then `make up ENV=staging`. **[Stage 9](stage-09-deployment-targets.md) pass 1's `identity/org-policies/` apply**: its job statements are in `awsds-org-scp-ou-workloads.json` on `main` since PR #144 and not attached, so any apply of the slice attaches them; 1.3 runs after Stage 9's apply and battery, and this stage's processing jobs run under them (risk "The `Workloads` document"). Stage 9 pass 5 (`staging/data/`, step 4) is not a prerequisite, and this stage runs before it (risk "The Lake Formation seat") |
| **Consumes** | [D7](../decisions/D07-orchestration.md), [D11](../decisions/D11-lab-lifecycle.md), [D12](../decisions/D12-budget-ceiling.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D18](../decisions/D18-data-scientist-access.md), [D20](../decisions/D20-staging-account.md), [D26](../decisions/D26-unified-studio.md), [D28](../decisions/D28-workflow-contract.md), [D41](../decisions/D41-sagemaker-application.md) |
| **Proves** | — (no `INT-nn` row: the association is [INT-12](../integrations.md)'s shape on an account INT-12 leaves out, and pass 8 removes it). It exercises [INT-23](../integrations.md) once, a subscription across two accounts over sample data (7.2, decision 5), and answers for Stage 10 how much of its steps 1.1, 2.4 and 4.2 a `deploy --targets staging` from the bundle does (4.5) |

*Read with [`docs/SMUS.md`](../../SMUS.md) (the blueprint table, the `ToolingLite` row, the CI/CD CLI),
D41's "What the lab measured on 2026-10-15", and 6b pass 1, whose steps pass 8 repeats. The report this
stage answers, in Portuguese, is `discussoes/runtime-sagemaker.md` in the Claude project's library.*

---

**Objective:** one project in `Staging`, created from a deployment-only project profile, whose only members
are the identities that deploy, holding two applications the CI/CD CLI deployed from their bundles; read for
what the blueprint creates in a `Workloads` account, what the CLI's `deploy` and `run` do there, what a
person can and cannot do in it, and what lineage and the catalog gain from it; then every piece removed in
the reverse order. The verdict says whether D41 item 2 holds (no project in Staging or Production, the
pipeline deploying the bundle itself) or its alternative replaces it (a project in each deployment
account, the CLI deploying every stage).

**Why Staging.** It carries Production's SCP document (`Workloads`), holds sample or synthetic data only
(D20), and was an associated account until 6b (2026-09-06), so both the association and its removal are
paths already measured on it. Production is not touched.

## The questions

Each is answered in the stage log with its date, the ones that come out fine included. Items i to vii are
the report's list of 2026-10-16; viii to x are the user's three lines of 2026-10-17; xi follows from Stage
6f's reading of the domain unit's policies.

| # | Question | Step |
|---|---|---|
| i | Does a project live in a `Workloads` account with spaces and apps still denied? `Tooling` creates a SageMaker AI domain per project, which `DenyInteractiveSageMakerSurface` refuses on `CreateDomain`; does `ToolingLite` create one? | 3.2 |
| ii | What does the blueprint create in a deployment account (roles and their policies, a domain, security groups, buckets and prefixes, keys, Glue databases, Athena workgroups, Lake Formation registrations and admins, data sources and their schedules, RAM shares), and which principals call `datazone:*` there? | 3.3 |
| iii | What does `deploy --targets staging` from `app-etl`'s release bundle write, as which identity, and how much of Stage 10's steps 1.1, 2.4 and 4.2 does it do; what stays to be built (the chain, the failure rule, Stage 8's manual gate, D28's per-workflow role)? | 4.2-4.5 |
| iv | Does a membership designation (`PROJECT_CATALOG_VIEWER` or another the API lists) give a person a view of the workflows and their runs with no write? | 6.1 |
| v | Does a profile with `enableSpaces` false and not editable give a project with no spaces, in which the CLI still deploys with the project's network and key? | 3.2, 4.2 |
| vi | Does a boundary on the project role that denies the `airflow-serverless` writes to a person's session lock the editor and the portal's run button while the worker's session still runs the tasks, and which session key tells the two apart? | 6.2 |
| vii | Does a role that is not a member of the project find a CLI-made workflow by its composed name and start it, as Stage 10's chain role must? | 0.4 |
| viii | Do two applications share one project cleanly (workflow names, storage prefixes, tags, the one project role), and does removing one leave the other's workflows and files? What does one project per application cost and change? | 0.1, 5.1-5.4 |
| ix | Does the CLI's `run` start anything but a workflow, for an application whose manifest deploys a model or holds no workflow? The code says no (0.1), and 4.4 runs it once | 0.1, 4.4 |
| x | Does a Glue job the Staging project runs post lineage that the domain shows, and does a Sandbox project's subscription to an asset the Staging project publishes become a Lake Formation grant across the two accounts? | 7.1, 7.2 |
| xi | Do the domain unit's policies keep people out of the project: who may create a project from the deployment profile, add a member, or take ownership? | 6.1 |

## What this stage builds, and in which accounts

Every row is removed at pass 8, at the step the last column names.

| Where | What | Layer | Removed at |
|---|---|---|---|
| `identity/org-policies/` (amended) | the carve-out of `Staging Account` from `DenyDataZoneEntirely`, and from `sagemaker:CreateDomain` only if decision 1 lands on `Tooling`, by `aws:PrincipalAccount` against a new placeholder `<ACCOUNT_ID_STAGING>`; the battery's rows for both directions | — | 8.7 |
| Data Governance, console (user) | the association of `Staging Account` to `awsds-studio` | — | 8.4 |
| `scripts/tfhygiene/backend.py` | a list of its own for an associated account no person works in (2.3), and the `SMUS_ASSOCIATED` row | — | 8.2 |
| `staging/studio/` (new) | the blueprint prerequisites `sandbox/sagemaker/` holds, through `terraform-modules/sagemaker-prereqs/` (the provisioning and manage-access roles, the D13 boundary for the project role, the project key, the projects bucket, the log group), and on its second apply the configuration of decision 1's base blueprint alone, with its grant | `[P]` for the stage's life | 8.3, 8.6 |
| `data-governance/governance/` (amended) | the project profile `deployment`: one environment configuration, the base blueprint, with `enableSpaces` false and not editable where the blueprint has it; its create grant names the identity decision 3 picks and no persona group | — | 8.2 |
| The domain | the project `deploy-staging`, whose only members are the identities that deploy (decision 3) | DataZone's | 8.1 |
| `staging/foundation/` (amended, only if decision 4 runs 4.3) | the actions 4.2's CloudTrail list adds to `awsds-deploy-staging` | `[P]` | 8.8 |
| `awsds/app-etl` and one awsds-workflows example | a `staging` stage in each manifest, on a measurement branch that is never merged | — | 8.8 |

**Not built**: `staging/orchestration/`, a chain or a schedule, the Glue job's declaration in a Staging
slice (D41 item 9), anything in Production. **Why `staging/studio/` and not `staging/sagemaker/`**:
conventions §6 keeps `staging/sagemaker/` for Stage 9 step 4.3's job roles, which stay, and a slice
destroyed whole at 8.6 cannot share a folder with one that does not.

## Who executes each action

| Tag | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls, done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write, only after the user authorizes that action in chat, with the SSO user, the account and the permission set stated first |
| **[user]** | the console and portal acts, GitLab settings, git pushes, and every log entry the user writes |
| **[Claude reads, user decides]** | a measurement Claude takes and a choice only the user can make, in the same sitting |
| **[pipeline]** | the deploy runner as `awsds-deploy-staging` |

## Step numbers are identifiers, not an order

| Pass | What | Who |
|---|---|---|
| **0** | preflight: the CLI read, the Sandbox environment as the before, Staging as it is, question vii in Sandbox | Claude; Claude⚡ for 0.4 |
| **1** | the carve-out, battery first | Claude, user, Claude⚡ |
| **2** | the association, the blueprint configuration, the profile | user, Claude⚡ |
| **3** | the project and what it created | Claude⚡; Claude reads |
| **4** | the deploy and the run, from the laptop, then from the deploy runner | Claude⚡; pipeline |
| **5** | a second application in the same project | Claude⚡ |
| **6** | a person in the project, and the boundary | user; Claude reads |
| **7** | lineage, and a subscription across accounts | Claude⚡; user |
| **8** | the unwinding, then the verdict | Claude⚡; user |

Pass 8 runs whatever the earlier passes found: a pass that fails stops the stage and goes to pass 8, which
removes only what exists, in its order.

## To execute

### 0. Preflight

- **0.1 — [Claude] The CLI 1.0.9's code, for what the passes rely on** (viii, ix): read 2026-10-17 from
  its sdist, nothing executed; the log records the file and line of each answer.
  - **A stage names its project** by name, or with `create`, `profileName`, `owners`, `contributors` and
    `role`, and its domain by id, name or tags with a region and no account (`application_manifest.py`).
    The CLI calls AWS with the caller's credentials in that region and assumes no role, and a `deploy`
    takes the first stage `--targets` names, so one call deploys one stage in one account.
  - **With `create: false` a missing project stops the deploy** (*"make sure the SMUS project is
    pre-created manually"*). With `create: true` it calls `CreateProject` with the profile named, or the
    domain's only profile, and an unknown profile name takes the first profile silently; `role.policies`
    without an ARN creates an IAM role `smus-<project>-role`. It never enables a blueprint
    (`project_manager.py`).
  - **Two applications in one project** differ by the workflow name `<application>_<project>_<workflow>`
    and the tags `Pipeline` and `Target`. Their files share the project's storage root with no
    application prefix, and `workflow.create` scans that whole root and takes the first file per DAG id,
    so two applications with one DAG id can take each other's file [inferred from the code]. The copies
    under `operatorFiles/` are never pruned; a bundle lookup falls back to any zip in its folder; a name
    keeps only letters, digits and `_` at creation while `run` and `destroy` map only `-`, so an
    application's name stays within letters, digits and `-` (`deploy.py`, `bundle_storage.py`).
  - **`destroy` removes what the manifest declares**, never what a deploy recorded: the workflows by
    name; the S3 prefix `<root>/<targetDirectory>` with no trailing slash, so `exemplos/demo` also covers
    `exemplos/demo-x/` [inferred]; every catalog object the project owns unless `catalog.disable: true`;
    and the whole project when `project.create` is true. It deletes no IAM role
    (`destroy_validator.py`, `destroy_executor.py`).
  - **`run` starts one workflow per call** (`StartWorkflowRun`, the stage's variables as overrides) and
    returns without waiting; its `--command` reaches the Airflow CLI on provisioned MWAA only. Nothing in
    the code starts a notebook, a pipeline, a training job or an endpoint, and `destroy` knows only the
    `GlueJobOperator`'s job (`run.py`, `operator_registry.py`). The CLI's own ML examples train and
    deploy inside workflow tasks: `ml/training`, `ml/deployment` and `genai` through
    `SageMakerNotebookOperator`, which this estate's lint refuses (6d decision 14 (b)), and `mlops`
    from a processing job that creates the endpoint. Stage 10 step 5.4 serves a model by batch
    transform inside a workflow.
- **0.2 — [Claude] Read the Sandbox project's `Tooling` environment as the before** (ii): its
  CloudFormation stack's resources, each role's trust and policies, its data sources and their
  schedules, `./aws/studio.py`. Question ii is a comparison with this list.
- **0.3 — [Claude] Read Staging as it is**: `./aws/studio.py`'s `US-6` (`datazone` reads denied in
  `Workloads`); CloudTrail's `datazone.amazonaws.com` events in Staging for 30 days, denials only
  expected; the `Workloads` document as attached, Stage 9 pass 1's statements in it (Prerequisites);
  Staging's Lake Formation admins (`get-data-lake-settings`); `awsds-deploy-staging`'s policy and
  ceiling, against the calls the CLI made in `test` (Stage 8 verification xix's list).
- **0.4 — [Claude⚡] Question vii, in Sandbox, with no Staging project**: as `awsds-infra-sandbox`, first
  read whether `InfrastructureAccess` is a member of the `test` project (`EXC-17` leaves it
  unanswered), then `aws mwaa-serverless list-workflows` and `start-workflow-run` on the workflow the
  CLI made there, found by its composed name `<application>_<project>_<workflow>`, and
  `get-workflow-run` to its end. A non-member's run that starts shows that the service authorizes by IAM
  alone, which is what Stage 10's `awsds-<env>-chain-exec` needs; a refusal names the layer. One run,
  cents.
- **0.5 — [Claude] Run the battery as it stands**: `./aws/probes/scp-battery.py --phase ou`, the before
  for 1.3.

### 1. The carve-out (D17, D26)

`DenyDataZoneEntirely` refuses every call this stage makes from Staging: the blueprint configuration is
written from the member account, and the CLI reads the project and its connections as the identity that
deploys.

- **1.1 — [Claude] Write it.** In `awsds-org-scp-ou-workloads.json`, `DenyDataZoneEntirely` gains
  `"Condition": {"StringNotEquals": {"aws:PrincipalAccount": "<ACCOUNT_ID_STAGING>"}}`. If decision 1
  lands on `Tooling`, `sagemaker:CreateDomain` leaves `DenyInteractiveSageMakerSurface` for a statement
  of its own under the same condition, so `CreateSpace`, `CreateApp`, `CreateUserProfile`,
  `CreatePresignedDomainUrl` and `StartSession` stay denied in Staging. `<ACCOUNT_ID_STAGING>` joins the
  substitutions of `locals.tf` and of `render.py`, resolved by the exact vended name `Staging Account`
  with `status == "ACTIVE"`, the way `identity_account_id` is, so no id enters a tracked file.
  `POLICIES.md`'s rows name the carve-out, this stage and 8.7; `docs/AWS_STATE.md` gains an `EXC-nn`
  for the window. Production stays under the whole deny.
- **1.2 — [Claude] Write the battery's rows** (`aws/probes/probes.py`): from `awsds-infra-staging`,
  `datazone list-domains` reaches authorization (the carve-out matches); from the canary under the
  candidate document, the same call is denied with the SCP's wording (the condition does not leak); if
  1.1 split `CreateDomain`, `sagemaker:CreateSpace` from Staging is still denied.
- **1.3 — [user + Claude⚡] Exercise, then attach**: the candidate on `Policy Test` first
  ([`scp-battery.md`](../runbooks/scp-battery.md)), then `identity/org-policies/` applied as
  `awsds-infra-identity`, expecting one in-place update of the `Workloads` document; then the battery's
  phase `ou`, and from `awsds-infra-prod` a `datazone list-domains` still denied.

### 2. The association, the blueprint and the profile (D26)

- **2.1 — [user] Associate `Staging Account`** in the console: sign in as the *Infrastructure User*,
  account **Data Governance**, permission set **`InfrastructureAccess`**, then Amazon DataZone → View
  Domains → `awsds-studio` → Account associations → request the association for `Staging Account`. The
  association raised no invitation on 2026-08-21 under org-wide RAM.
- **2.2 — [Claude] Read it back**: as `awsds-infra-staging`, `datazone
  list-environment-blueprint-configurations` succeeds and returns an empty list, the call that cannot
  succeed before the association; `ram get-resource-shares --resource-owner OTHER-ACCOUNTS` holds the
  `DataZone-EXTENDED_ACCESS-…-ORG-ONLY` share, and its permission is read against the
  `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess` that AWS's release note of 2026-07-30
  names for cross-account setups (*"Existing RAM resource shares do not auto-update"*).
- **2.3 — [Claude] Give the deployment account a list of its own before any row moves.**
  `SMUS_MEMBERS` holds two meanings today, the accounts associated to the domain and the accounts people
  work in, and its readers outside `governance/` mean the second: `PERSONA_VENDING_ACCOUNTS` (the
  persona's vending policy in each member's `foundation/`), `interactive_private_cidrs()` (the GitLab
  security group's HTTPS sources), the `readers` of `production/sagemaker/` (Stage 9's model-status
  readers), and refusal 8 in `layers.py`, which would refuse `awsds-deploy-staging` every Staging slice.
  Staging is the first account that is associated and no person's workspace (Lesson 51). So the edit adds
  a list of deployment members, read by `governance/`'s `members` map and by `profiles_enabled`, and by
  none of the four. The order of `backend.py`'s note holds: `SMUS_ASSOCIATED` gains `staging` before the
  new list does, or `profiles_enabled` flips false and the next `governance/` apply destroys
  `experimentation`. After each regeneration, `sandbox/foundation/`, `production/tooling/` and
  `staging/foundation/` re-plan `No changes`.
- **2.4 — [Claude] Write `staging/studio/`**: `sandbox/sagemaker/`'s shape through
  `terraform-modules/sagemaker-prereqs/` at its pinned tag, `blueprints_enabled` from `SMUS_ASSOCIATED`,
  decision 1's blueprint alone in the configurations and their regional parameters (not the eleven), the
  D13 boundary field set; `layers.py` gains its rank and `[P]` row.
- **2.5 — [Claude⚡] Apply it twice as `awsds-infra-staging`**: the prerequisites, then, after 2.3's
  `SMUS_ASSOCIATED` row, the configuration and its grant; the boundary field read back with `get-role`,
  since it is write-only.
- **2.6 — [Claude] Write the profile `deployment`** in `governance/`: `local.project_profiles` gains it,
  and `profiles.tf` takes each profile's blueprint list from the profile (every profile reads
  `category_one_blueprints` today); its base `ON_CREATE`; `experimentation`'s Tooling parameters, plus
  `enableSpaces` false and not editable where the blueprint carries it; its
  `CREATE_PROJECT_FROM_PROJECT_PROFILE` grant to decision 3's identity, never to
  `sso-group-data-scientists`.
- **2.7 — [Claude⚡] Apply `governance/` as `awsds-infra-data`**: the profile and its grant added,
  `experimentation` unchanged. A plan that destroys
  `awscc_datazone_project_profile.this["experimentation"]` stops the step.

### 3. The project

- **3.1 — [Claude⚡] Create `deploy-staging`** from `deployment`, as decision 3 picks: `datazone
  create-project` as `awsds-infra-staging`, then `list-project-memberships` read back, the creating role
  its only member.
- **3.2 — [Claude] Read whether it provisioned** (i, v): the environment's status and, on a failure, the
  refused call and the policy its wording names. An environment that fails pins its configuration
  (Lesson 39), so a failure here goes to pass 8, which deletes the project before the configuration.
- **3.3 — [Claude] Read what the blueprint created** (ii): the environment's stack against 0.2's list;
  each role's trust, policies and boundary; the security groups and their rules; the buckets, prefixes
  and keys; Glue databases and Athena workgroups; Lake Formation's registrations, admins and opt-ins;
  the data sources and their schedules (`EXC-11`'s cron in Sandbox); RAM shares; and CloudTrail's
  `datazone.amazonaws.com` events in Staging grouped by principal, the list a carve-out by principal
  would name (decision 2).

### 4. The deploy and the run (D28, D41)

- **4.1 — [Claude] Add a `staging` stage** to `app-etl`'s manifest on a measurement branch: the domain,
  `deploy-staging`, Staging's `{env.*}` values (the job subnets, the `process` task's volume key, the
  image by digest), the `workflow.create` action, no `workflow.run`.
- **4.2 — [Claude⚡] Deploy from the laptop** as `awsds-infra-staging`: `deploy --targets staging` with
  the release's bundle, `--skip-validation --no-events` (D41's flags). Read what it wrote: the objects
  under the project's storage, the workflow by its composed name, `manual_only`, its execution role (the
  project role, D41 item 4), its network and key (v), its log group and retention, its tags, its
  versions (each deploy spent one on 2026-10-16, of a workflow's 50), and whether the Glue job was
  created by the operator rather than declared (D41 item 9). CloudTrail's list of the deploy's calls is
  the input of 4.3.
- **4.3 — [pipeline] The same deploy as `awsds-deploy-staging`** (decision 4): the role made an owner
  of `deploy-staging` first, since DataZone refuses a non-member's reads (`EXC-17`'s refusal); the
  actions 4.2's list adds to the role, written in `staging/foundation/` and applied as
  `awsds-infra-staging`; the job on a measurement branch the user protects in `awsds/app-etl` for the
  window, since the deploy runner takes protected refs only (Lesson 67 is the cost: protecting the
  branch extends the runner to it).
- **4.4 — [Claude⚡] Run it** (ix): the sample input placed, then `run --targets staging --workflow`
  from the laptop, and `start-workflow-run` as the deploy identity; `get-workflow-run` to the end; the
  tasks' identity, subnets and endpoints read from CloudTrail and the logs.
- **4.5 — [Claude] Read the deploy against Stage 10** (iii): one row per Stage 10 step, done by the CLI
  or not, with what replaces it: 1.1 (`awscc_mwaaserverless_workflow` against `workflow.create`, which
  leaves the workflow outside Terraform's state), 1.2 (the network), 1.3 (the project role against D28's
  per-workflow role), 2.4 (the definitions home against the project's storage), 4.2 (the API rung the
  CLI is), 3.1 to 3.7 (the failure rule and the chain layer, which nothing in the CLI builds) and
  Stage 8's manual gate.

### 5. Several applications in one project

- **5.1 — [Claude⚡] Deploy a second application into `deploy-staging`**: an awsds-workflows example
  with a Python task (`demo-python-operator`), its manifest's `staging` stage naming the same project,
  its DAG id and its prefix distinct from `app-etl`'s, its bundle in a folder of its own (0.1). Read
  the two workflows' names, the two prefixes, the tags, and whether either deploy changed the other's
  files.
- **5.2 — [Claude⚡] The shared DAG id**: a copy of the second application whose workflow reuses
  `app-etl`'s DAG id, deployed once; read whether `workflow.create` took or rewrote `app-etl`'s file,
  0.1's inference, then `app-etl` redeployed from its bundle and its workflow read back.
- **5.3 — [Claude⚡] Remove the second one**: `destroy --targets staging` on its manifest, which says
  `project.create: false` and `catalog.disable: true`, since `destroy` deletes every catalog object the
  project owns and, with `create: true`, the project (0.1). Read that `app-etl`'s workflow, runs, files
  and catalog survive, and list what `destroy` left behind (the `operatorFiles/` copies, the log group).
- **5.4 — [Claude reads, user decides] One project per application** (decision 6): the quotas AWS
  publishes, read 2026-10-17, are 1,000 projects and 1,000 environments per account and Region in
  SageMaker Unified Studio (*"the depletion of resource quotas in one project can affect all other
  projects within the account"*) and 1,000 environments per DataZone domain; MWAA Serverless allows
  100 workflows and 50 versions of each per account and Region, which every application spends
  whatever the project count. Read Staging's values in Service Quotas, and what a second project costs
  at rest and adds to question ii's list; a second project is created only on the user's word.

### 6. A person in the project (D18)

- **6.1 — [user] Add the data scientist with the narrowest designation the API offers** (iv, xi), sign
  in to the portal as that person and read what the project shows (the workflows, a run and its logs,
  the editor, the run button); try each write and read its refusal in CloudTrail. Then try, as the same
  person, to create a project from `deployment`, to add a member and to take ownership, which the domain
  unit's policies govern (`ADD_TO_PROJECT_MEMBER_POOL` is open to every user, read at Stage 6f).
- **6.2 — [Claude reads, user decides] The boundary on the project role** (vi), only if 6.1 shows a
  person's write landing: read the session's name and context keys of a portal action against a
  worker's task (6h read the portal's session as `<user id>@<env id>` and a space's as `SageMaker`); a
  deny conditioned on the person's session is written in `staging/studio/` and re-read on both sides
  only if a key separates them.

### 7. Lineage and the catalog (D26)

- **7.1 — [Claude⚡] Lineage from a Staging Glue job** (x): `app-etl`'s Glue task with Glue 5.0's
  OpenLineage configuration naming the domain, its role holding `datazone:PostLineageEvent`; the
  domain's `list-lineage-events` read twice with a delay (Stage 10 verification xix's form), then the
  portal's graph.
- **7.2 — [user + Claude reads] A subscription across accounts** (x, decision 5): the Staging project
  publishes the Glue task's output table, sample data; the Sandbox project subscribes and the Staging
  owner approves; read the grants DataZone writes in each account and through RAM (INT-23's claim), and
  whether a Sandbox notebook reads the table. Revoked at 8.1. AWS's pages, read 2026-10-17, set the
  publishing side's terms: the table Lake Formation-managed, its location registered in Lake Formation
  or hybrid mode with no `IAMAllowedPrincipals`, the publishing project's role holding `DESCRIBE` and
  `SELECT` with the grant option, and no LF-TBAC; the subscriber gets `SELECT`, and a resource link
  cannot be subscribed to, so the Sandbox project cannot republish what it receives. Every path those
  pages document for publishing a table puts a project in the table's account, which is what makes
  this step a question for the verdict.
- **7.3 — [Claude] Redshift is read, not measured**: Staging has no warehouse, and a Sandbox project
  reading a governed Redshift table is INT-24, Stage 9 step 9.7's. AWS's pages, read 2026-10-17: a
  subscription to a Redshift asset across accounts adds a datashare that the producer side authorizes
  and the consumer side associates, with both accounts associated, both warehouses encrypted and RA3
  or Serverless, and the subscribed tables appear as views in the consumer's warehouse; a direct
  datashare, with no DataZone, gives a database of `SELECT` only. The pages name no Lake Formation step
  on either path, the property INT-24's shapes are measured by.

### 8. The unwinding, then the verdict

The reverse of passes 1 to 3, in 6b pass 1's order, each step read back before the next.

- **8.1 — [Claude⚡] Remove what the project holds, then the project**: the subscription and the asset,
  the applications, the project, whose deletion deletes its environment's stack; the stack read gone;
  the CLI's log groups, which carry no retention, deleted or recorded under `EXC-10`'s shape.
- **8.2 — [Claude⚡] Remove the profile and the rows in one edit**: the `deployment` profile and its grant,
  the deployment list's row and the `SMUS_ASSOCIATED` row (6b step 1.6's rule: one list alone flips
  `profiles_enabled`), `governance/` applied as `awsds-infra-data`, `experimentation` unchanged.
- **8.3 — [Claude⚡] Destroy the blueprint configuration and its grant** in `staging/studio/` as
  `awsds-infra-staging`, while the association exists: only the member deletes them.
- **8.4 — [user] Disassociate `Staging Account`**, the console path of 2.1 → Disassociate (6b step 1.4).
- **8.5 — [Claude] Read the association back**: `list-environment-blueprint-configurations` from Staging
  fails with `UnauthorizedException` (6b step 1.5), and RAM holds no DataZone share.
- **8.6 — [Claude⚡] Destroy the rest of `staging/studio/`**: the projects bucket listed with its versions
  and delete markers and emptied, the slice destroyed, the folder and its `layers.py` row deleted, the
  project key's deletion date in the log, Staging's Lake Formation admins read back to 0.3's.
- **8.7 — [Claude⚡] Restore the SCP**: the carve-out and the placeholder removed, `identity/org-policies/`
  applied, the battery's rows removed, and from `awsds-infra-staging` a `datazone list-domains` denied
  with the SCP's wording; the `EXC-nn` closed.
- **8.8 — [user + Claude] Close the repositories**: the measurement branches deleted unmerged, the
  protected branch unprotected, the deploy role's added actions removed and applied.
- **8.9 — [Claude reads, user decides] The verdict** (decision 7): the answers to i to xi in the log;
  then D41 item 2 kept, with the measurements in place of the argument, or reopened, with Stage 10's
  steps 1.1, 2.4 and 4.2 rewritten around the CLI; `SMUS.md` gains what the blueprint creates in a
  deployment account; `POLICIES.md`'s revision trigger on `DenyDataZoneEntirely` names the result.

## Deliverables

- The log's answers to questions i to xi, each with its date and its reading.
- 4.5's table of Stage 10's steps against the CLI's deploy.
- 3.3's list of what the blueprint creates and which principals call `datazone:*` in a deployment
  account.
- The verdict on D41 item 2, as the user takes it at 8.9.
- An estate equal to 0.3's reading: no association, no profile, no project, no `staging/studio/`, the
  `Workloads` document as before.

## Validation

- `./aws/studio.py` green at 0.3 and at 8.5, with `US-6` back to `Workloads` denying `datazone` reads.
- The battery green at 1.3 and at 8.7.
- `data-governance/governance/`, `staging/foundation/`, `sandbox/foundation/` and `production/tooling/`
  re-planning `No changes` after 8.2 and 8.8.

## Cost

Rates measured in `us-west-2` (`docs/PRICING.md`): Staging's 11 endpoints at USD 0.110 an hour while up,
with the hub; MWAA Serverless at 0.088 per task-hour; Glue at 0.44 per DPU-hour; the DataZone domain's
metadata in cents per month. A project's environment holds no compute of its own unless the blueprint
starts one, which question ii reads. The stage's spend is read from Cost Explorer at 8.9, not estimated
(Lesson 6).

## Decisions due while executing

Each is decided during the stage and written into the stage log with its recommendation (Lesson 16).

1. **The base blueprint** (1.1, 2.4, 3.1). Recommended: **`ToolingLite` first, then `Tooling` if it
   fails**. `ToolingLite` is category 3 as a second base on the eleven-blueprint profiles, and `SMUS.md`
   says it returns, if ever, as a profile of its own, which `deployment` is; what it creates is unread.
   `Tooling` creates a SageMaker AI domain per project, so it needs `CreateDomain` carved out too.
2. **The carve-out's form** (1.1). Recommended: **by account, for the stage's window**: which principals
   call `datazone:*` in a deployment account is what 3.3 measures, so a carve-out by principal cannot be
   written before it. A carve-out by principal is the form a permanent one would take, from 3.3's list.
   Moving Staging out of `Workloads` is refused: it would drop every job-settings deny with it.
3. **Who creates the project, and who owns it** (2.6, 3.1). Recommended: **`awsds-infra-staging`, with
   `datazone create-project`, and no manifest says `project.create: true`**. With `create: true` the
   CLI's `destroy` deletes the whole project (0.1), so removing one application could take the other's
   project with it, and AWS's rollback guide calls `create: false` the typical production setup. The
   profile's grant names that role, which owns the project for 4.2; `awsds-deploy-staging` joins as an
   owner before 4.3, and no person is a member before 6.1. The CLI creating it as the deploy role is
   the alternative: it measures the CLI's creation path and ties the project's life to a `destroy`.
4. **Whether 4.3 runs as `awsds-deploy-staging`** (4.3). Recommended: **yes**, since the variant under
   test is a project the pipeline deploys into with no person in it, and the actions the role gains are
   the price of adopting it. Its cost is a protected branch in `awsds/app-etl` for the window and an amendment of the
   deploy role, both removed at 8.8.
5. **Whether 7.2's subscription runs** (7.2). Recommended: **yes**, on sample data only: INT-23 is
   unexercised, and the user's third line asks whether a Sandbox project reads what a production project
   publishes.
6. **A second project for 5.4** (5.4). Recommended: **read only**: the role, the storage and the stack
   are per project by construction, and the quota and the cost are readings.
7. **The verdict** (8.9). Taken by the user on the answers; recommended at 8.9 from them.

## Risks

- **`SMUS_MEMBERS` gaining Staging changes four things outside the domain** (2.3): the persona's vending
  policy in `staging/foundation/`, the GitLab security group's sources, Production's model-status
  readers, and refusal 8 on every Staging slice. 2.3 splits the list first, and the re-plans prove it.
- **The order of the two rows**: a deployment row before the `SMUS_ASSOCIATED` row flips
  `profiles_enabled` false and destroys `experimentation`, or fails on its projects; 2.7 and 8.2 read
  the plan's destroy count before applying.
- **An incomplete configuration pins its projects both ways** (Lesson 39): pass 8 deletes the project
  before the configuration, and the configuration before the association.
- **The carve-out admits every Staging principal to DataZone for the window.** IAM still grants nothing:
  `DataScientistStagingAccess` holds no `datazone:` action (read 2026-10-17 in
  `terraform-live/identity/sso/policies-data-scientists.tf`), and the deploy role gains only 4.3's
  actions. The `EXC-nn` and 8.7 bound the window.
- **The Lake Formation seat.** SMUS made itself a Lake Formation admin in Sandbox (open question 24); if
  the blueprint does the same in Staging, a `staging/data/` built while the project exists would be
  reachable by it. This stage runs before Stage 9 pass 5, 3.3 reads the admins, and 8.6 reads them back.
- **The `Workloads` document carries Stage 9 pass 1's job statements, merged and not attached** (PR #144).
  An apply of `identity/org-policies/` attaches what `main` holds, so 1.1 edits `main`'s document, 1.3 runs
  only after Stage 9's own apply and battery, and its plan changes only `DenyDataZoneEntirely` and, if 1.1
  split it, `CreateDomain`'s statement. The two stages never share an apply.
- **Residues**: the CLI's log groups carry no retention, the workflows' versions and run history leave
  with the project, and the project key waits out its deletion window.
