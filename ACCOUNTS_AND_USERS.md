
# AWS Accounts

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

## Manager user

- roles: when infrastructure changes are deployed through CD tool, this user will be used for approving deployment of artifacts.
