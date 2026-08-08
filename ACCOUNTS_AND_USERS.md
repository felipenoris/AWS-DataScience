
# AWS Accounts

Nine accounts, in four organizational units. The account is the isolation boundary; the OU is the policy
boundary, so each OU is named for the policy set it carries rather than for its contents (`GENERAL_PLAN.md`
D23).

| Account | OU | Policy set the OU carries |
|---|---|---|
| Management | root | Bootstrap only, manual, never managed by Terraform |
| Log Archive | Security | Control Tower guardrails |
| Audit | Security | Control Tower guardrails; delegated security administration |
| Identity | Security | Control Tower guardrails; delegated Identity Center administration |
| Sandbox | Interactive | Interactive compute allowed; human infrastructure changes denied |
| Development | Interactive | Same as Sandbox — the two differ in content, not in policy |
| Data Management | Data | No compute at all; deletion denied |
| Staging | Workloads | No interactive compute; no human control plane |
| Production | Workloads | Same as Staging |

## Management Account

- represents the root account. Never touch it. This will be used only to bootstrap the AWS environment manually. All further actions will be performed using auxiliary accounts.

## Sandbox Account

- Represents an experimentation sandbox environment, where the unit of work is a notebook. Sandbox users will use this to experiment and develop artifacts.

## Development Account

- Represents a development environment, where the unit of work is a pipeline (repository with tests, SageMaker pipeline). In contrast with the Sandbox environment, the Development environment uses git, CI and automation tools.

## Staging Account

- Staging area before promotion to Production.

## Production Account

- represents the production environment. All actions in this account will be done using terraform.

## Data Management Account

- Responsible for state of data: production of data, data quality, access policies.

## Log Archive Account

- Log Archive account linked to Control Tower.

## Audit Account

- Audit account linked to Control Tower.

## Identity Account

- Manage identity store, users, groups and permissions.

# SSO Users

## Infrastructure user

- roles: can assume infrastructure change roles

## Data Scientist user

- roles: regular user with read-only access to production environment data, and read-write access to sandbox and development environment. Can't perform infrastructure changes, unless it is managed by some AWS Service (SageMaker).

- the access matrix this expands into, per account (`GENERAL_PLAN.md` D18):

  - **Sandbox and Development**: read-write and interactive. This is where the person works.
  - **Staging**: read-only, with no write of any kind. Staging is written by the pipeline and read by a
    human diagnosing why the pipeline failed.
  - **Production**: the data plane without compute — logs, catalog metadata, job status, named S3
    prefixes and Athena on a dedicated workgroup. No control plane, no ability to start compute.
  - **Data Management**: no sign-in at all. The lake is read from Sandbox and Development through the
    Lake Formation cross-account share. The only write toward the lake is `s3:PutObject` into the
    ingestion drop-box, granted by bucket policy rather than by a sign-in.
  - **Identity, Audit, Log Archive**: no access.

## Manager user

- roles: when infrastructure changes are deployed through CD tool, this user will be used for approving deployment of artifacts.
