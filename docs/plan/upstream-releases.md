# Upstream releases read against the plan

What SageMaker Unified Studio, the SMUS CI/CD CLI, Terraform core and the `aws` and `awscc` providers
released between 2026-08-01 and 2026-10-18, and the older changes the plan still records as a gap, each
mapped onto the steps, decisions and open questions it moves. Read on 2026-10-18 with the environment down.
Only changes that move something in the plan are listed.

## How to read this file

Each tool opens with the version or date the plan was written against and the latest one read on
2026-10-18. Each row names the change, its date and its source, the plan items it moves (by stable id), a
verdict and what confirmed it.

| Verdict | Meaning |
|---|---|
| unblocks | a planned step becomes possible or simpler |
| stale | a fact the plan records no longer holds, or holds only in part |
| risk | a regression, a new channel or a silent failure mode |
| bump | a proposed pin change, listed again in [Proposed pin bumps](#proposed-pin-bumps) |
| holds | re-read, and the plan's reading stands |
| watch | unreleased upstream work that would move the plan if it lands |

A release note is a claim (Lessons 8, 38 and 41), so the last column says what confirmed it:

| Confirmed by | What was read |
|---|---|
| schema | `terraform providers schema -json` of `aws` 6.60.0 + `awscc` 1.98.0 against `aws` 6.69.1 + `awscc` 1.106.0, initialised in a scratch directory outside the repository |
| registry | `aws cloudformation describe-type` and `list-types`, `us-west-2`, as the infrastructure user in Sandbox |
| model | the API model the installed AWS CLI 2.37.12 ships, compared with botocore's `develop` branch |
| code | the CLI's sdist `aws_smus_cicd_cli-1.0.9.tar.gz`, sha256 `173e91af…eff6`, read and never executed; for the `aws` provider, its Go source and `go.mod` at the release tags on GitHub |
| read | a read-only call in this estate |
| page | the AWS documentation page, read 2026-10-18 unless its row dates another reading |
| price list | the AWS Price List offer file, with its publication date |
| note | the release note or announcement alone |

## SageMaker Unified Studio and DataZone

**Written against**: the readings in [`docs/SMUS.md`](../SMUS.md) (the managed roster of 2026-08-21) and the
DataZone model of the AWS CLI 2.37.12 the laptop runs since 2026-10-10. **Read 2026-10-18**: What's New to
2026-10-16 (nothing posted on 2026-10-17 or 2026-10-18), botocore 1.43.114 (2026-10-14), the admin guide's
document history to 2026-10-08, and the domain `awsds-studio`.

| Change | Plan items it moves | Verdict | Confirmed by |
|---|---|---|---|
| Git connections at the account level and the repository experience ([release notes](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/release-notes.html), 2026-07-30; [Git connections](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/git-connections.html); [cross-account Git](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/cross-account-git.html)), read 2026-10-25: connections to GitHub, GitLab, GitLab self-managed and Bitbucket are created in *Settings → Account settings → Git connections* and, once enabled, reach every domain and project in the account; projects add repositories, with per-artifact tracking, branches, explicit push; a domain may use a connection of another account through RAM, with `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess` at its latest version; new project profiles no longer choose S3 or Git | [INT-13](integrations.md): the path a Production host and a shared connection open, the user's decision (the waiting list); `docs/SMUS.md` item 2's profile reading of 2026-08-26 (`gitConnectionArn` not editable) predates nothing here but describes the profile, not the account-level page, which is read at the next console sitting; open question 26 | a decision, not a bump | the three pages |
| Custom Tooling blueprints ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/10/sagemaker-custom-tooling-blueprints/), 2026-10-09; [admin guide](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/tooling-custom-blueprints.html)). `CreateEnvironmentBlueprint` takes `blueprintCategory` `TOOLING` (botocore 1.43.102, 2026-09-24), and a profile may name such a blueprint as its base | [Stage 18](stages/stage-18-staging-deployment-project.md) decision 1 gains a third candidate beside `ToolingLite` and `Tooling`: a CloudFormation template this repository writes. The guide's minimum template for an Identity Center domain holds a bucket, a log group, the project role and the three default connections, and no SageMaker AI domain, so question i needs no `CreateDomain` carve-out. In such a domain the template creates the project role, so its policies and the D13 boundary become this repository's text: an option for [INT-15](integrations.md), open questions 21 and 22, and Lessons 11 and 17. The template must sit where the provisioning role reads it: the managed provisioning policy reads buckets named `amazon-sagemaker-cf-templates*`. The CLI's fallback (next section) applies to it; open questions 21 and 22 and INT-15 carry the authorship note | unblocks | model, page; read: `awsds-studio` holds no custom blueprint; registry: no `AWS::DataZone::EnvironmentBlueprint` type, so the blueprint is a hand object (Lesson 8) |
| Trusted identity propagation from notebooks ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/08/amazon-sagemaker/), 2026-08-19; [admin guide](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/trusted-identity-propagation.html)) | Open question 13's "notebooks do not support TIP" is stale for the native notebook experience: in a profile with `enableTrustedIdentityPropagationPermissions` true, Athena, Redshift and EMR Serverless sessions from a notebook carry the Identity Center identity; Glue and EMR on EC2 stay in compatibility mode. Remote space connections are still unsupported in a TIP profile (re-read 2026-10-18), so Stage 6 decision 2 holds. The guide recommends a dedicated TIP profile beside the others, and says Lake Formation's conditional grants, the ones `docs/SMUS.md` §S3 item 1b records, do not reach Identity Center principals, so such a profile needs grants to users or groups. The 2026-08-13 entry for the notebooks page in `docs/REFERENCES.md` describes the page as it was | stale | page |
| Native notebook kernels in the domain-level VPC ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/04/sagemaker-unified-studio-vpc/), 2026-04-23) and Athena for Apache Spark still the notebooks' default Spark runtime, still outside any VPC ([user guide](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/notebooks.html)) | Open question 12 stands for Spark; the Python kernel of a native notebook runs in the VPC. The querybook's quotas read 0 here, but `L-DBBAE884` (notebooks on `sc.t3.medium`) read 2 on 2026-09-12 (`docs/SMUS.md` §Querybook compute), so a native notebook, and the Data Agent below, may start in Sandbox: unmeasured | holds | page |
| Connections: `CreateConnection` takes the project role in `iamProperties.roleArn` (2026-09-24), and the model's connection types include `VPC` and `GIT`, with a `DOMAIN` or `PROJECT` scope | A domain-scoped VPC connection is where the portal and the CLI take a workflow's subnets and security group from before the Tooling environment's (the CLI's `helpers/datazone.py`), a network lever no instrument watches. Read 2026-10-18: `awsds-studio` holds none. CloudFormation's `AWS::DataZone::Connection` (2026-10-03) and `awscc_datazone_connection` (1.106.0) carry neither a VPC nor a Git connection, and the latter gains `props.iam_properties.role_arn`, which matters to [6h](stages/stage-06h-redshift-connection.md) decision 1 or a custom Tooling template only | risk | model, code, read, registry, schema |
| `DeleteDomain` takes `cascadeDelete` (botocore 1.43.82, 2026-08-27): one call deletes every project, environment and subscription and their AWS resources | `aws_datazone_domain` (6.69.1) has no such argument, so a destroy of `data-governance/governance/` is unchanged. No SCP denies `datazone:DeleteDomain` in the `Data` OU: the only DataZone action the root document names is `CreateDomain`, outside that OU ([D26](decisions/D26-unified-studio.md)); Stage 12 8.4 names the domain's RTO | risk | model, schema |
| `GetSubscriptionGrant` returns `assetScope.scopeName`, the materialized asset scope (botocore 1.43.69, 2026-08-11) | [6f](stages/stage-06f-data-governance.md)'s subscription readings and [Stage 11](stages/stage-11-dlp.md)'s `DP-*` checks can name the Lake Formation data cells filter or Redshift view a grant created | unblocks | model |
| ODBC from BI tools ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/09/sagemaker-unified-studio-odbc-power-bi/), 2026-09-11): the Athena ODBC driver 2.2.0.1 or later, authenticating with `SageMakerBrowserIdc` or `SageMakerIam`, reads project data | A channel from project data to a laptop beside the remote IDE (open question 14), which under [D39](decisions/D39-access-by-identity.md) needs no tunnel; Stage 11's [threat model](threat-model.md) carries it as `TM-22` | risk | note |
| Iceberg REST Catalog connections ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/09/sagemaker-iceberg-rest-iam-documentdb/), 2026-09-28): Snowflake Open Catalog, Databricks Unity Catalog or a generic catalog, with OAuth2 or a bearer token and vended S3 credentials | A project connection to a catalog outside the perimeter; the compute plane's allow-list (`docs/NETWORK.md`) refuses the catalog's host until a name joins it; `TM-24` | risk | note |
| SageMaker Data Agent in notebooks and the Query Editor ([data storage page](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/data-agent-data-storage.html); Identity Center domains since [2026-04-23](https://aws.amazon.com/about-aws/whats-new/2026/04/amazon-sagemaker-idc/)) | Prompts and generated code are stored in the domain's Region and may be inferred in another by cross-region inference. The threat model carries it as `TM-23`; [6e](stages/stage-06e-claude-code-bedrock.md)'s exception to [D1](decisions/D01-region.md) covers the `us.` profiles the project role calls, not the agent | risk | page |
| MLflow App customer-managed key ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/08/sagemaker-mlflow-custom-keys), 2026-08-24; `CreateMlflowApp` and `DescribeMlflowApp`, botocore 1.43.76, 2026-08-20) | [Stage 17](stages/stage-17-sandbox-machine-learning.md) 1.5 and 1.7: the CLI 2.37.12 documents `create-mlflow-app --kms-key-id`, and an app created without it carries no customer-managed key, so whether the portal's form passes the project key is a reading for `ML-2` against `docs/GOVERNANCE.md` §Encryption. `AWS::SageMaker::MlflowApp` (updated 2026-10-18), `aws_sagemaker_mlflow_app` (6.69.1) and `awscc_sagemaker_mlflow_app` (1.106.0) carry no key field. The `AmazonSageMaker` offer of 2026-10-16 still lists no MLflow App usage type (`docs/SMUS.md`'s row) | risk | model, registry, schema, price list |
| CI/CD notebook promotion and the `generate-bundle-manifest` skill ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/09/sagemaker-cicd-notebook-ai-manifest/), 2026-09-02; CLI 1.0.7) | [D28](decisions/D28-workflow-contract.md) keeps "the notebook does not graduate" and [6d](stages/stage-06d-unified-studio-remainder.md) decision 14 (b) keeps the portal's notebook task out, now as a choice against an available path: the CLI promotes native notebooks between projects, never into a target with no project | holds | note, code |
| AWS-managed policies of the project and provisioning roles ([document history](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/doc-history.html): 2026-08-24, 2026-09-14, 2026-10-08) | Open question 22. Re-read in Sandbox 2026-10-18: `SageMakerStudioProjectUserRolePolicy` v75, `SageMakerStudioProjectRoleMachineLearningPolicy` v45, `SageMakerStudioProjectProvisioningRolePolicy` v84, `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy` v9 and `SageMakerStudioDomainExecutionRolePolicy` v23, the versions the 2026-10-17 reading and `docs/SMUS.md` record | holds | read |
| The managed blueprint roster | Read 2026-10-18: 23 names, the ones `docs/SMUS.md`'s table carries. `Tooling` was updated 2026-08-19 and has 26 user parameters, `enableSpaces` among them (default `true`, not editable at the blueprint), which Stage 18 step 2.6 sets | holds | read |

## The SMUS CI/CD CLI

**Written against**: `aws-smus-cicd-cli` 1.0.9, released 2026-10-05, measured in the lab on 2026-10-15
([D41](decisions/D41-sagemaker-application.md)) and read from its sdist on 2026-10-17 and 2026-10-18
(Stage 18 step 0.1). **Read 2026-10-18**: 1.0.9 is the latest release on PyPI and GitHub, and `main` is the
`v1.0.9` commit `3418ae1b07`. **Read again 2026-10-26** on PyPI: 1.0.9, uploaded 2026-10-05, is still the
latest.

| Change | Plan items it moves | Verdict | Confirmed by |
|---|---|---|---|
| No release after 1.0.9 ([releases](https://github.com/aws/CICD-for-SageMakerUnifiedStudio/releases), [PyPI](https://pypi.org/project/aws-smus-cicd-cli/)) | [Stage 8](stages/stage-08-cicd-pipelines.md) step 2.5's readings stand: `wait` crashes 1.0.9, and no deploy-time variable carries the tag. D41's owed `monitor` and `logs` readings are unchanged; `run` returns once `StartWorkflowRun` answers, and a pipeline job followed the run with `get-workflow-run` to `SUCCESS` (Stage 18 4.3, run `I3A52lFlgpcaxpN`, 2026-10-21) | holds | read |
| 1.0.9's own changes: a Python or Bash task's `code` field (PR #370), workflow tags overwritten from the manifest at each deploy (PR #361), names sanitized to `[A-Za-z0-9_]` (PR #354) | D41's owed "a Python or Bash task's `Code` through the CLI" and [Stage 10](stages/stage-10-orchestration-promotion.md) verification xxiii: the code path exists, and Stage 18 4.2 and 4.4 measured it in Staging on 2026-10-19: the CLI wrote the workflow's code object under the project's `shared/operatorFiles/`, and the Python task `summarize` ran from it | holds | code |
| The domain lookup by name, measured from a space on 2026-10-26. The project step of every deploy with bootstrap actions (`_ensure_environments_exist`) and `workflow.create`'s role lookup (`get_project_user_role_arn`) call `get_domain_id_by_name`, which lists domains and ignores the manifest's `domain.id`; DataZone refuses `ListDomains` to a project's role. The SageMaker Distribution ships 1.0.8 first on a space's `PATH`, which refuses the manifest's `code` field | [Stage 10](stages/stage-10-orchestration-promotion.md) 2.1 and [Stage 8](stages/stage-08-cicd-pipelines.md) decision 22: a deploy from a space goes through the template's `scripts/dev-cli.sh`, which answers the lookup with the manifest's id and calls the house environment's CLI by its path ([`sagemaker-application.md`](runbooks/sagemaker-application.md) §D); the pipeline's deploy roles are refused nothing. The report upstream is drafted (2026-10-26), its posting the user's. The next release is read for a lookup that takes the id, which would retire the script | risk | code, measured |
| Every stage names a project: the manifest refuses a stage without `project.name` (`application/application_manifest.py`), and AWS's [CI/CD page](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/cicd.html) maps each stage to its own project | D41 item 2's premise and D26's "a deployment target is never associated" hold; nothing released deploys into an account with no project. Stage 18 measured the alternative in Staging, and the user kept item 2 on 2026-10-22 (D41, "Where production runs") | holds | code, page |
| The network and key fallback. When neither a domain-scoped VPC connection nor the Tooling environment's `privateSubnets`, `securityGroup` and `kmsKeyArn` can be read, `workflow.create` omits `NetworkConfiguration` and `EncryptionConfiguration`, prints one line and creates the workflow in the service's default worker network under a service-managed key (`helpers/datazone.py`, `bootstrap/handlers/workflow_create_handler.py`, `helpers/airflow_serverless.py`); [issue 318](https://github.com/aws/CICD-for-SageMakerUnifiedStudio/issues/318) shows it on a deploy role refused `ListEnvironmentBlueprints` | A deploy role needs the DataZone reads `awsds-deploy-sandbox-test` holds (`GetEnvironment`, `ListEnvironmentBlueprints`, `ListEnvironments`, `ListConnections`) and a project membership, and a custom Tooling template must expose the three values. Stage 18 4.3 read the membership half on `awsds-deploy-staging` (2026-10-21): as a non-member every storage item stopped on `ListConnections`, before `workflow.create`; once a person made its `IAM_ROLE_SESSION_GROUP` profile `PROJECT_OWNER`, the deploy passed, the CLI's `cloudformation:DescribeStacks` and `datazone:GetGroupProfile` refusals stopping nothing. MWAA Serverless's IAM carries only tag condition keys ([policy generator catalogue](https://awspolicygen.s3.amazonaws.com/js/policies.js)), so no SCP can require a network on `CreateWorkflow`; Stage 10's `OR-3` is the only check, after the fact. The key is fixed at creation | risk | code, catalogue |
| Open upstream work: PR [#289](https://github.com/aws/CICD-for-SageMakerUnifiedStudio/pull/289) (a specification for Glue Visual ETL in `bundle`, `deploy`, `destroy` and the dry run, 2026-07-21) and issue [#355](https://github.com/aws/CICD-for-SageMakerUnifiedStudio/issues/355) (`content.git` deployments) | A merged #289 would give D28 class (2c)'s `.vetl`, which stays in the project, a CLI path between the Sandbox projects | watch | read |

## MWAA Serverless and Step Functions

**Written against**: the MWAA Serverless API with `Code` (botocore 1.43.72, 2026-08-14), D7's 0.088 USD per
task-hour, and Stage 10 verification xxii open. **Read 2026-10-18**: the model the CLI 2.37.12 ships equals
botocore's `develop`.

| Change | Plan items it moves | Verdict | Confirmed by |
|---|---|---|---|
| No API change since 2026-08-14. `StartWorkflowRun` takes `WorkflowArn`, `ClientToken` (an idempotency token), `OverrideParameters` and `WorkflowVersion`; a run's status is one of `STARTING`, `QUEUED`, `RUNNING`, `SUCCESS`, `FAILED`, `TIMEOUT`, `STOPPING`, `STOPPED` | Stage 10 verification xxii and step 3.5's `Choice` state: the status set and the token's documented idempotency are read from the model; the behaviour is still 3.5's measurement | unblocks | model |
| The Step Functions SDK integration `arn:aws:states:::aws-sdk:mwaaserverless:<action>` ([supported services](https://docs.aws.amazon.com/step-functions/latest/dg/supported-services-awssdk.html)), listed since 2026-03-12 ([release history](https://docs.aws.amazon.com/step-functions/latest/dg/awssdk-release-history.html)); new integrations now arrive without announcements ([2026-09-15](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-step-functions-integrations/)) | Stage 10 step 3.5's integration name is the one the guide lists, so verification xxii keeps only the console's confirmation at the first apply. D41's revision trigger "an integration the console does not list" does not fire | unblocks | page |
| `AWS::MWAAServerless::Workflow` (registry, 2026-10-12): `Name` and `EncryptionConfiguration` are create-only; `WorkflowVersion`, `ScheduleConfiguration` and `CodeSnapshottedAt` are read-only | Stage 10 decision 2's fallback to `AWS_MANAGED_KEY` is a replacement: a new ARN, no run history, and every chain's `WorkflowArn` moves. The schedule lives only in the YAML, as step 3 says | stale | registry |
| An `aws` provider resource is still unmerged: issue [#45254](https://github.com/hashicorp/terraform-provider-aws/issues/45254) open, PRs [#49927](https://github.com/hashicorp/terraform-provider-aws/pull/49927) (`aws_mwaaserverless_workflow`) and [#49929](https://github.com/hashicorp/terraform-provider-aws/pull/49929) (its `code`) open since 2026-09-09 | D28 class (4) stays `awscc_mwaaserverless_workflow`. A merge would add a second spelling of the object (Lesson 32) | watch | read |
| The price, USD 0.088 per task-hour, in the `AmazonMWAA` offer of 2026-09-11 | D7 | holds | price list |

## Services under the SMUS surface

| Change | Plan items it moves | Verdict | Confirmed by |
|---|---|---|---|
| Instance preference lists for training and processing jobs ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/09/amazon-sagemaker-training-processing-instance-pref-lists/), 2026-09-15; [guide](https://docs.aws.amazon.com/sagemaker/latest/dg/train-instance-preferences.html)): training takes `ResourceConfig.InstancePreferences` and processing `ProcessingResources.ClusterConfig.InstancePreferences`, each up to five types, in place of `InstanceType` | `DenySageMakerInstanceCeiling` (the `Workloads` SCP, and the D13 boundary through `sagemaker-denies`) leaves alone a request carrying no `sagemaker:InstanceTypes`. Whether the service fills the key from a preference list is unread, and the policy generator's catalogue lists no new key. SageMaker checks the quota of every listed type, so a type at quota 0 still refuses the request. The battery rows for `CreateTrainingJob` and `CreateProcessingJob` whose list names an off-ceiling type, expected `DENY-SCP`, ran on 2026-10-22 at 01:53Z in phase `ou`, each as expected (Stage 18 8.7; [Stage 9](stages/stage-09-deployment-targets.md) 3.5, PR #216; [the battery runbook](runbooks/scp-battery.md)'s phase 4b): the lists naming an off-ceiling type answered `DENY-SCP` and the list inside the ceiling was authorized, so the service fills the key from the list. The first SageMaker job in `Workloads`, Staging's on 2026-10-19, named its type as `InstanceType` | holds | page, catalogue, model |
| Lake Formation row-level security policies (botocore 1.43.113, 2026-10-13; AWS CLI 2.38.0): `CreateRLSPolicy` holds a filter expression over named columns, and `AttachRLSPolicy` attaches it to a resource for a principal, with an optional Lake Formation condition, or as the default for every principal | Stage 11 step 2.1a and its decision 12 gain a second mechanism for the row half beside `aws_lakeformation_data_cells_filter`. No CloudFormation type and no resource in either provider carries it, so it would be an API object | unblocks | model, registry, schema |
| Redshift system table integration with S3 Tables ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/08/redshift-long-term-system-table-retention/), 2026-08-20; [guide](https://docs.aws.amazon.com/redshift/latest/mgmt/system-table-s3-tables.html)): per Serverless namespace, `update-namespace --log-destination-type s3table`, delivering `SYS_QUERY_HISTORY`, `SYS_QUERY_TEXT`, `SYS_CONNECTION_LOG`, `SYS_USERLOG` and `SYS_SESSION_HISTORY` among others to a service-managed table bucket `aws-redshift` in the account | `EXC-16`, `TM-16` and Stage 11 decision 13, its DLP feed: a record of every completed query that does not depend on the CloudWatch export (unmeasured here), delivered without keeping a workgroup up, immutable, written free and stored at S3 Tables rates (`docs/PRICING.md` §5). The key chosen at the first enable cannot change; `SYS_QUERY_TEXT` carries literals, the residual [5b](stages/stage-05b-redshift-serverless.md) step 4 names. Neither `aws_redshiftserverless_namespace` (6.69.1) nor `awscc_redshiftserverless_namespace` (1.106.0) carries the setting, so it is a hand `update-namespace`, and whether `sandbox/warehouse/`'s next apply keeps it is unread | unblocks | page, model, schema |
| Glue 6.0 ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/08/aws-glue-6-0-price-reduction-iceberg-v3), 2026-08-21): USD 0.308 per DPU-hour in `us-west-2` against 0.44 before 6.0 (`AWSGlue` offer of 2026-10-12) | `app-etl`'s Glue task is `GlueVersion: "6.0"` (`examples/app-etl/workflows/app-etl.yaml`), so Stage 10's cost table and Stage 18's Cost section price it at 0.44 where it bills 0.308; Stage 9's producer jobs too if they run 6.0. Stage 18 step 7.1 names Glue 5.0's lineage configuration, which DataZone documents for 5.0 and later | stale | price list |
| Bedrock data retention mode `aws_review` (botocore 1.43.89, 2026-09-04) | 6e step 7.2's table of the enum, read with CLI 2.36.18, lists four values; the model the CLI 2.37.12 ships lists `default`, `none`, `aws_review`, `provider_data_share` and `inherit`. `DenyBedrockRetentionModeOtherThanNone` denies every value but `none`, so the new one is refused | stale | model |
| Bedrock product attributes in Cost Explorer, Budgets and dashboards ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/10/aws-bedrock-attributes-in-cost-explorer/), 2026-10-08): model, provider, inference type, feature | 6e step 8.3 and its decision 6: a budget with a real subscriber can be filtered to one model; 8.4 can attribute spend by model | unblocks | note |
| GuardDuty managed by AWS Organizations policies ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/10/guardduty-org-enablement-policies/), 2026-10-01; the `GUARDDUTY_POLICY` type, botocore 1.43.106, in which `GetDetector` also marks each feature a policy manages with `ManagedBy`) | [Stage 15](stages/stage-15-guardduty.md) decision 4, read 2026-10-20: `aws_organizations_policy` accepts the type from 6.68.0, the first release bundling the Go SDK's `service/organizations` v1.61.0, whose enum its `type` validator reads; `identity/org-policies/` locks 6.60.0, which refuses it. The policy sets the foundational detector and seven plans per Region, its attachment is the scope, and the delegated administrator stays step 1's act; whether it turns Audit's own plans off past `DenyGuardDutyTampering` is unread | unblocks | code, page, model |
| Network access controls for the Identity Store ([announcement](https://aws.amazon.com/about-aws/whats-new/2026/10/aws-identity-store-network-controls/), 2026-10-05) | D39 and Stage 11's identity premise stand: the controls bind the Identity Store and SCIM APIs, not the sign-in | holds | note |

## Terraform core

**Written against**: 1.15.8 (2026-07-08), the version `CLAUDE.md`'s tool list,
`.github/workflows/offline-gates.yml` and `gitlab/awsds/deploy-image/Dockerfile` pin; every slice requires
`~> 1.15`, which admits 1.16 and 1.17. **Read 2026-10-18**: 1.16.6 (2026-10-14) is the latest release, and
1.17.0-rc2 the latest candidate ([releases](https://github.com/hashicorp/terraform/releases)). **Read 2026-10-25**
from the CLI's own version notice on the laptop: 1.17.0 is released; its `-minimal-refresh` rule is due (the list
below), and the lab stays on 1.16.6.

| Change | Plan items it moves | Verdict | Confirmed by |
|---|---|---|---|
| The 1.15 line ends at 1.15.9 (2026-08-19). 1.16.6 carries the fix for CVE-2026-78669, an HTTP/2 resource exhaustion a compromised registry could cause, which HashiCorp places outside core's security guarantees | The laptop, the offline-gates job and the deploy image fetch providers from the registry at every `init` | bump | note |
| `lifecycle { destroy = false }` on a resource (1.16.0, [PR #38784](https://github.com/hashicorp/terraform/pull/38784); fixed with `create_before_destroy` in 1.16.3): a destroy removes the object from state and leaves it | The in-place form of the `removed` block Stage 6c used for the Elastic IP; no planned step needs it | unblocks | note |
| `import` blocks inside modules (1.16.0); `state show -json` (1.16.0) | An adoption (Lesson 35) can live in a module; an instrument can read one resource as JSON | unblocks | note |
| `-minimal-refresh` (1.17.0-rc): a plan refreshes only the resources it proposes to change | `sandbox/sagemaker/` forbids `-refresh=false` because SMUS is a Lake Formation admin there (open question 24), and the new option skips the same refresh for every resource the plan leaves alone: the rule should name both once 1.17.0 is released | risk | note |
| Variables and locals in provider requirements (1.17.0-rc) | The per-slice pin (Lesson 14, each `versions.tf`) stays per root module | holds | note |

## The `hashicorp/aws` provider

**Written against**: the locks, 6.60.0 in most slices and in `sandbox/foundation/`, the tree's reference;
6.61.0, 6.62.0, 6.64.0 and 6.68.0 elsewhere; 6.69.1 in the two observability slices; constraint `~> 6.60`.
**Read 2026-10-18**: 6.69.1 (2026-10-15)
([releases](https://github.com/hashicorp/terraform-provider-aws/releases)).

| Change | Plan items it moves | Verdict | Confirmed by |
|---|---|---|---|
| `aws_secretsmanager_secret_rotation.rotation_enabled` becomes settable, and `false` cancels rotation on a secret whose rotation AWS manages (6.62.0, [PR #49659](https://github.com/hashicorp/terraform-provider-aws/pull/49659)) | `EXC-13`: the admin secret's rotation could be declared off. The first rotation succeeded on 2026-10-20 with no workgroup, against AWS's page, and whether the database took the password is unread. `sandbox/warehouse/` locks 6.64.0, so no bump is needed. The PR names RDS secrets; whether Secrets Manager accepts the call on a Redshift-owned secret is unread, and whether to declare it off stays the user's decision; `EXC-13` records the path | unblocks | schema |
| `aws_datazone_policy_grant` (6.63.0) | A second spelling of `awscc_datazone_policy_grant`, which `governance/grants.tf` and `sagemaker-prereqs`' `grants.tf` use (Lesson 32); no reason to move | holds | schema |
| `aws_glue_catalog_table`: `storage_descriptor` fields become optional and computed, and the resource gains an identity (6.65.0) | `data-governance/data/catalog.tf`'s `sample_trades`: the first plan at 6.65.0 or later is read before it is trusted | risk | schema |
| `aws_redshiftserverless_workgroup`: server-only `config_parameter` entries filtered (6.66.0), then the whole list read again when no block is declared (6.68.0) | `CLAUDE.md`'s "provider ≥ 6.66.0 ignores undeclared keys" holds while the workgroup declares `config_parameter` blocks, which `sandbox/warehouse-compute/` does at 6.68.0 | holds | note |
| Still absent at 6.69.1: an MWAA Serverless resource, a Lake Formation RLS resource, a key on `aws_sagemaker_mlflow_app`, the S3 Tables logging of `aws_redshiftserverless_namespace`, a cascade on `aws_datazone_domain` | The rows above that rest on an API object | holds | schema |

## The `hashicorp/awscc` provider

**Written against**: 1.98.0 (2026-08-19) in `data-governance/governance/` and `sandbox/sagemaker/`,
constraint `~> 1.89`. **Read 2026-10-18**: 1.106.0 (2026-10-14)
([releases](https://github.com/hashicorp/terraform-provider-awscc/releases)). awscc's changelog lists new
types only, so the attribute changes below come from the schema diff.

| Change | Plan items it moves | Verdict | Confirmed by |
|---|---|---|---|
| `awscc_mwaaserverless_workflow` gains `code` (`s3_location.bucket`, `object_key`, `version_id`) and `code_snapshotted_at` (1.99.0); `workflow_version` is computed in both versions | Stage 10 step 1.1 needs 1.99.0 or later for a workflow with Python or Bash tasks, as step 0.2 reads. Verification xxii's last question is answered by the schema: the version a chain pins is exposed | unblocks | schema, registry |
| `awscc_datazone_policy_grant`: `principal` and `detail` change from optional to required | Both callers set both, so a bump should plan `No changes` | holds | schema |
| `awscc_datazone_connection.props.iam_properties.role_arn` | 6h decision 1 and a custom Tooling template only | holds | schema |
| New types since 1.98.0 include `awscc_glue_connection` (1.99.0), `awscc_sagemaker_endpoint_config` (1.100.0) and `awscc_glue_table` (1.106.0) | No planned step needs them | holds | schema |
| Still absent at 1.106.0: a custom blueprint type, a DataZone VPC or Git connection, a key on `awscc_sagemaker_mlflow_app`, Lake Formation RLS | The rows of the earlier sections that rest on an API object | holds | schema, registry |

## The AWS CLI

**Written against**: 2.37.12 (2026-10-09), on the laptop and pinned in the deploy image. **Read
2026-10-18**: 2.38.1 (2026-10-14) ([changelog](https://github.com/aws/aws-cli/blob/v2/CHANGELOG.rst)).

| Change | Plan items it moves | Verdict | Confirmed by |
|---|---|---|---|
| 2.38.0 turns on the CRT S3 transfer client on every host | The deploy image's `aws s3` calls in `test-deploy` and `store-bundle` run through the build plane's proxy; the new HTTP stack is read there before the image's pin moves | risk | note |
| 2.38.0 carries the Lake Formation RLS operations | Needed only to call them | holds | note |

## Proposed pin bumps

None is applied here; each is a change of its own, with the plan read first.

| Pin | From → to | Serves | Where | Read at the bump |
|---|---|---|---|---|
| Terraform core, **taken by the user 2026-10-22** | 1.15.8 → 1.16.6 | CVE-2026-78669; `lifecycle { destroy = false }`; module `import` blocks | in order: the laptop's binary (the user's install) and `CLAUDE.md`'s tool list, then `.github/workflows/offline-gates.yml` (`TERRAFORM_VERSION`) and `gitlab/awsds/deploy-image/Dockerfile` (`TERRAFORM_VERSION`, `TERRAFORM_SHA256`, a new deploy image release at a GitLab sitting); no `versions.tf` changes | the published `linux_amd64` checksum `38034b38…f1b7` against its signature; every slice re-plans `No changes`. **The laptop runs 1.16.6 since 2026-10-25** (the user's install, the `darwin_arm64` zip checked against the published sums), `CLAUDE.md`'s list, the workflow's pin and the Dockerfile's two pins moved the same day, `production/warehouse/` re-planned `No changes` under it. The image's release is owed at the GitLab sitting and comes **before any laptop apply or `make up` of a slice the pipeline reads or applies**: a state written by 1.16.6 is refused by the image's 1.15.8, by a plan, a `terraform_remote_state` read or `terraform output` alike (*state snapshot was created by a newer version*) |
| `awscc` | none for the two 1.98.0 locks | No planned step on those slices needs a newer schema | — | a slice that first declares `awscc_mwaaserverless_workflow` (`staging/orchestration/`, `production/orchestration/`) initialises at the latest, 1.99.0 or later |
| `aws` | none required | `rotation_enabled` is in `sandbox/warehouse/`'s 6.64.0 | `data-governance/data/` at its next change | the `aws_glue_catalog_table` plan |
| `aws` on `identity/org-policies/` | 6.60.0 → 6.68.0 or later, only if Stage 15 decision 4 authors the GuardDuty policy there | the `GUARDDUTY_POLICY` type | the slice's `.terraform.lock.hcl`; the `~> 6.60` constraint admits it | the ten documents re-plan `No changes` before the policy joins them (`type` is ForceNew) |
| AWS CLI in the deploy image | 2.37.12 → 2.38.x, only with a reason | Lake Formation RLS by API | `gitlab/awsds/deploy-image/Dockerfile` (`AWSCLI_VERSION`) | the CRT client behind the proxy |
| `aws-smus-cicd-cli` | none | 1.0.9 is the latest | — | — |

## Next reading

- **awscc's next weekly release** (expected 2026-10-21): whether `awscc_sagemaker_mlflow_app` gains the key
  field, since `AWS::SageMaker::MlflowApp` changed on 2026-10-18; and any custom blueprint or RLS type.
- **The `aws` provider's PRs #49927 and #49929**, before Stage 10 pass 2 writes `orchestration/`.
- **The CLI** on PyPI and GitHub before Stage 10 pass 1; at a new release, re-read the
  fallback in `helpers/datazone.py` and `workflow_create_handler.py`, and PR #289.
- **DataZone's model and the custom blueprint pages**: closed 2026-10-19, when the applies of Stage 18's
  passes 1 and 2 took its decisions 1-3, decision 1 on the managed `Tooling` blueprint.
- **Terraform 1.17.0**, released by 2026-10-25 (the CLI's version notice): the `-minimal-refresh` rule, and whether
  the lab moves past 1.16.6.
- **A battery run of the instance-preference rows** PR #216 wrote (`./aws/probes/scp-battery.py --phase
  ou`, Production, `awsds-infra-prod`): closed 2026-10-22, when Stage 18 8.7's battery ran the seven rows
  at 01:53Z, each as expected.
- **The price list**: `AWSGlue` and `AmazonS3` when Stage 11 decides the Redshift feed; `AmazonSageMaker` at
  Stage 17 step 8.2 for an MLflow App usage type.
- **This file**, every two weeks while a stage that depends on these tools is in progress. The method: the
  What's New directory API
  (<https://aws.amazon.com/api/dirs/items/search?item.directoryId=whats-new-v2&sort_by=item.additionalFields.postDateTime&sort_order=desc&size=100&item.locale=en_US&page=0>),
  botocore's changelog dated by its PyPI uploads, a provider schema diff in a scratch directory, and
  `describe-type` for each CloudFormation type a row names.
