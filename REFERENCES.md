
# References

## Tools

- AWS Console login: <https://aws.amazon.com/>.

- Docs to install the `aws` client: <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>.

- Docs to install `terraform`: <https://developer.hashicorp.com/terraform/install>.

- uv: <https://docs.astral.sh/uv/>.

- AWS Pricing Calculator: <https://calculator.aws/>.

- AWS Price List bulk API - offer index (all service codes): <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json>. Per service and Region: `offers/v1.0/aws/<serviceCode>/current/<region>/index.json`; the Regions a service is offered in are at `offers/v1.0/aws/<serviceCode>/current/region_index.json`. Public, no credentials required - the source of every rate in `PRICING.md`.

- AWS CodeArtifact endpoints and quotas (used to confirm that CodeArtifact is **not** available in `sa-east-1`): <https://docs.aws.amazon.com/general/latest/gr/codeartifact.html>.

- etl-cookbook-tutorial: <https://github.com/felipenoris/etl-cookbook-tutorial>.

## Organization and identity

- AWS Control Tower: <https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html>.

- AWS Control Tower endpoints by Region (used to check `sa-east-1` availability): <https://docs.aws.amazon.com/general/latest/gr/controltower.html>.

- Regional differences for AWS Control Tower functionality: <https://docs.aws.amazon.com/controltower/latest/userguide/regional-differences.html>.

- AWS Organizations - Service Control Policies: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html>.

- AWS Organizations - Resource Control Policies (RCPs): <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html>.

- AWS Organizations - Tag policies: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html>.

- AWS Organizations - Declarative policies: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_declarative.html>.

- AWS Security Reference Architecture (SRA): <https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/welcome.html>.

- Building a data perimeter on AWS (whitepaper): <https://docs.aws.amazon.com/whitepapers/latest/building-a-data-perimeter-on-aws/building-a-data-perimeter-on-aws.html>.

- AWS Control Tower Account Factory for Terraform (AFT): <https://docs.aws.amazon.com/controltower/latest/userguide/aft-overview.html>.

- Provision and manage accounts with Account Factory (the `SSOUserEmail` may be an existing Identity Center user; changing it later creates a *second* user and leaves the first): <https://docs.aws.amazon.com/controltower/latest/userguide/account-factory.html>.

- Provisioning an account in Account Factory, field by field (`SSOUserEmail` gets administrative access to the vended account; `AccountEmail` must not already belong to an AWS account): <https://docs.aws.amazon.com/controltower/latest/userguide/provision-as-end-user.html>.

- Permissions required for provisioning accounts (`AWSServiceCatalogEndUserFullAccess`, and **"you cannot be signed in as the Root user"** — why Account Factory refuses root, D33): <https://docs.aws.amazon.com/controltower/latest/userguide/provision-and-manage-accounts.html>.

- Identity and access management in AWS Control Tower (root user vs. IAM Identity Center user, and what authenticates a Control Tower operation): <https://docs.aws.amazon.com/controltower/latest/userguide/auth-access.html>.

- Recommendations for setting up groups, roles and policies in AWS Control Tower: <https://docs.aws.amazon.com/controltower/latest/userguide/roles-recommendations.html>.

- Removing an Account Factory portfolio and product from Service Catalog (shows the portfolio/principal model behind the Account Factory access error): <https://docs.aws.amazon.com/controltower/latest/userguide/controltower-walkthrough-cleanup-account-factory.html>.

- **IAM Identity Center groups for AWS Control Tower — the authoritative table of which group gets which permission set in which account** (`AWSControlTowerAdmins` = administrator on Management, Log Archive *and* Audit, plus `AWSOrganizationsFullAccess` on member accounts; `AWSAccountFactory` = `AWSServiceCatalogEndUserAccess` on Management only; and only `AWSControlTowerAdmins` members reach the Control Tower console): <https://docs.aws.amazon.com/controltower/latest/userguide/sso-groups.html>.

- AWS IAM Identity Center: <https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html>.

- Working with IAM Identity Center and AWS Control Tower (the default directory, its groups and permission sets, and the delegated-administration caveat): <https://docs.aws.amazon.com/controltower/latest/userguide/sso.html>.

- Disabling an IAM Identity Center user (read under D33 as the mechanism, not as a plan: the retirement of `AWS Control Tower Admin` it was cited for was withdrawn by D34, so no user in this design is scheduled for disabling): <https://docs.aws.amazon.com/singlesignon/latest/userguide/disableuser.html>.

- IAM OIDC identity providers (the issuer's discovery/JWKS URL must be publicly reachable — relevant to Stage 8 with a private GitLab): <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html>.

- AWS global condition context keys (`aws:ViaAWSService`, `aws:PrincipalIsAWSService`, `aws:SourceIp` caveats): <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html>.

- Data perimeter policy examples (aws-samples — reference implementations of the §4.2 SCPs/RCPs/endpoint policies with the service carve-outs): <https://github.com/aws-samples/data-perimeter-policy-examples>.

- S3 condition keys, including `s3:signatureAge` (limits the lifetime of presigned URLs): <https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazons3.html>.

- IAM Access Analyzer: <https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html>.

- IAM root user (including centralized root access management for member accounts): <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html>.

- IAM permissions boundaries: <https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html>.

- Granting a user permissions to pass a role (`iam:PassRole`): <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_passrole.html>.

## Terraform

- Terraform S3 backend (including native state locking): <https://developer.hashicorp.com/terraform/language/backend/s3>.

- Terraform AWS provider: <https://registry.terraform.io/providers/hashicorp/aws/latest/docs>.

## Networking and access

- WireGuard: <https://www.wireguard.com/>.

- AWS Systems Manager Session Manager (SSH-less access to EC2): <https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html>.

- AWS Client VPN (documented alternative to WireGuard): <https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/what-is.html>.

- Amazon VPC pricing (NAT gateway, endpoints, public IPv4 addresses): <https://aws.amazon.com/vpc/pricing/>.

- Amazon EC2 T4g instances in additional Regions: <https://aws.amazon.com/about-aws/whats-new/2023/06/amazon-ec2-t4g-instances-additional-regions>.

- Amazon MWAA in additional Regions: <https://aws.amazon.com/about-aws/whats-new/2024/05/amazon-mwaa-additional-regions/>.

- AWS PrivateLink / VPC endpoints: <https://docs.aws.amazon.com/vpc/latest/privatelink/what-is-privatelink.html>.

- Route 53 Resolver DNS Firewall: <https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall.html>.

- AWS Network Firewall: <https://docs.aws.amazon.com/network-firewall/latest/developerguide/what-is-aws-network-firewall.html>.

- VPC peering: <https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html>.

- VPC peering unsupported configurations (no edge-to-edge routing — a VPN attached to one VPC cannot reach the peer VPC without NAT): <https://docs.aws.amazon.com/vpc/latest/peering/invalid-peering-configurations.html>.

- Elastic Load Balancing pricing (an ALB bills hourly while it exists — it cannot be "stopped"): <https://aws.amazon.com/elasticloadbalancing/pricing/>.

- AWS Certificate Manager: <https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html>.

- AWS Private CA (the expensive alternative rejected in D15): <https://docs.aws.amazon.com/privateca/latest/userguide/PcaWelcome.html>.

## SageMaker and shared storage

- SageMaker Studio notebooks and internet access: <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-notebooks-and-internet-access.html>.

- SageMaker Studio custom images: <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-byoi.html>.

- Connect to SageMaker Studio through an interface VPC endpoint (`aws.sagemaker.<region>.studio`, plus the note that `CreatePresignedDomainUrl` travels through the *SageMaker API* endpoint, and that users outside the VPC can still reach the Studio UI over the internet unless an IAM condition stops them): <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-interface-endpoint.html>.

- SageMaker IAM condition keys (`sagemaker:VpcSubnets`, `NetworkIsolation`, `InstanceTypes`, `VolumeKmsKey`): <https://docs.aws.amazon.com/sagemaker/latest/dg/security_iam_service-with-iam.html>.

- SageMaker `RetentionPolicy` for `DeleteDomain` (defaults to `Retain`): <https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_RetentionPolicy.html>.

- SageMaker Pipelines (a D7 option the first draft omitted): <https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines.html>.

- SageMaker Model Registry (model promotion, Stage 10): <https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html>.

- Amazon SageMaker Unified Studio (the direction a large institution would evaluate first, §11): <https://aws.amazon.com/sagemaker/unified-studio/>.

- MLOps foundation roadmap for enterprises with Amazon SageMaker (the AWS account model behind D17: an experimentation account with Studio, a dev account, and a tooling account holding the Model Registry and ECR): <https://aws.amazon.com/blogs/machine-learning/mlops-foundation-roadmap-for-enterprises-with-amazon-sagemaker/>.

- `aws-samples/amazon-sagemaker-secure-mlops` (the three-account reference used to check D17: only the development account runs Studio; staging and production are deployment targets, with read-only access for data scientists in staging): <https://github.com/aws-samples/amazon-sagemaker-secure-mlops>.

- MLOps Workload Orchestrator - multi-account architecture (dev/staging/production separated by Organizational Unit): <https://docs.aws.amazon.com/solutions/latest/mlops-workload-orchestrator/architecture-overview.html>.

- Instance types available for SageMaker Studio: <https://docs.aws.amazon.com/sagemaker/latest/dg/notebooks-available-instance-types.html>.

- SageMaker Studio notebooks with G5 instances in South America (São Paulo): <https://aws.amazon.com/about-aws/whats-new/2023/07/amazon-sagemaker-studio-notebooks-g5-instance-south-america-sao-paulo-region>.

- SageMaker Studio notebooks support P5.4xl instance types: <https://aws.amazon.com/about-aws/whats-new/2026/01/p5.4xl-new-launch-sagemaker-studio-notebooks/>.

- Amazon EFS: <https://docs.aws.amazon.com/efs/latest/ug/whatisefs.html>.

- EFS lifecycle management (Infrequent Access storage class — makes a persistent EFS cost cents at lab scale): <https://docs.aws.amazon.com/efs/latest/ug/lifecycle-management-efs.html>.

- AWS DataSync (S3 <-> EFS synchronisation): <https://docs.aws.amazon.com/datasync/latest/userguide/what-is-datasync.html>.

## Data platform

- AWS Glue Data Catalog: <https://docs.aws.amazon.com/glue/latest/dg/catalog-and-crawler.html>.

- Querying Apache Iceberg tables with Athena: <https://docs.aws.amazon.com/athena/latest/ug/querying-iceberg.html>.

- Iceberg table maintenance with Athena (`OPTIMIZE`, `VACUUM` — compaction and snapshot expiration): <https://docs.aws.amazon.com/athena/latest/ug/querying-iceberg-data-optimization.html>.

- Amazon S3 Tables (managed Iceberg with automatic maintenance — the AWS-native alternative to hand-rolled Iceberg buckets): <https://aws.amazon.com/s3/features/tables/>.

- Athena workgroup settings, including `EnforceWorkGroupConfiguration` — the console calls it "override client-side settings" (the control that makes D19's per-principal result prefixes a boundary rather than a suggestion): <https://docs.aws.amazon.com/athena/latest/ug/workgroups-settings.html>.

- Specifying an Athena query result location using a workgroup (and the CTAS `external_location` conflict it causes): <https://docs.aws.amazon.com/athena/latest/ug/query-results-specify-location-workgroup.html>.

- AWS Lake Formation cross-account permissions: <https://docs.aws.amazon.com/lake-formation/latest/dg/cross-account-permissions.html>.

- Lake Formation cross-account sharing prerequisites (the grantor needs `AWSLakeFormationCrossAccountManager`; the target's data lake administrator needs `ram:AcceptResourceShareInvitation` and `ram:EnableSharingWithAwsOrganization`): <https://docs.aws.amazon.com/lake-formation/latest/dg/cross-account-prereqs.html>.

- Updating Lake Formation cross-account data sharing version settings (version 3 or above is required to share with an Organization or an OU, and it is what removes the per-share RAM invitation): <https://docs.aws.amazon.com/lake-formation/latest/dg/optimize-ram.html>.

- Lake Formation cross-account data sharing best practices and considerations: <https://docs.aws.amazon.com/lake-formation/latest/dg/cross-account-notes.html>.

- Lake Formation hybrid access mode (the documented exception in D13): <https://docs.aws.amazon.com/lake-formation/latest/dg/hybrid-access-mode.html>.

- Amazon S3 Bucket Keys (KMS cost reduction): <https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-key.html>.

- Amazon S3 Object Lock (immutable log archive): <https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html>.

## Containers, CI/CD and orchestration

- Amazon ECR: <https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html>.

- Amazon ECR pull-through cache (egress design B, §4.3): <https://docs.aws.amazon.com/AmazonECR/latest/userguide/pull-through-cache.html>.

- Amazon ECR image scanning: <https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html>.

- Amazon ECR private image replication (cross-account — the fallback if SageMaker custom images cannot be pulled cross-account from Production): <https://docs.aws.amazon.com/AmazonECR/latest/userguide/replication.html>.

- GitLab SAML SSO for self-managed instances (login works in CE; SAML group sync is a paid-tier feature): <https://docs.gitlab.com/ee/integration/saml.html>.

- AWS CodeArtifact (package proxy for egress design B; check the supported formats page for Cargo, and note that Julia and CRAN are not covered): <https://docs.aws.amazon.com/codeartifact/latest/ug/welcome.html>.

- Julia `PkgServer.jl` (self-hosted Julia package server, the D5(B) fallback for Julia): <https://github.com/JuliaPackaging/PkgServer.jl>.

- Posit Package Manager (commercial CRAN mirror, the D5(B) fallback for R): <https://posit.co/products/enterprise/package-manager/>.

- `panamax` (crates.io mirror, an alternative D5(B) fallback for Rust): <https://github.com/panamax-rs/panamax>.

- GitLab installation options: <https://about.gitlab.com/install/>.

- GitLab Pages: <https://docs.gitlab.com/ee/user/project/pages/>.

- GitLab back up and restore: <https://docs.gitlab.com/ee/administration/backup_restore/>.

- GitLab CI/CD OIDC federation with AWS: <https://docs.gitlab.com/ee/ci/cloud_services/aws/>.

- Amazon MWAA (Managed Workflows for Apache Airflow): <https://docs.aws.amazon.com/mwaa/latest/userguide/what-is-mwaa.html>.

- Amazon MWAA pricing (environment fee billed hourly, at one-second resolution, for as long as the environment exists): <https://aws.amazon.com/managed-workflows-for-apache-airflow/pricing/>.

- AWS Price List bulk API, used to read the authoritative `us-west-2` MWAA rates: <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonMWAA/current/us-west-2/index.json>.

- Amazon MWAA environment classes (`mw1.micro` ... `mw1.2xlarge`): <https://docs.aws.amazon.com/mwaa/latest/userguide/environment-class.html>.

- Amazon MWAA `mw1.micro` environments announcement: <https://aws.amazon.com/blogs/big-data/introducing-amazon-mwaa-micro-environments-for-apache-airflow/>.

- Amazon MWAA Serverless (pay per task, GA November 2025 - relevant to D7): <https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/what-is-mwaa-serverless.html>.

- Amazon MWAA Serverless announcement: <https://aws.amazon.com/about-aws/whats-new/2025/11/mwaa-serverless-deployment-apache-airflow-workflows/>.

- Amazon MWAA service quotas (10 environments per account per Region, 25 workers and 5 web servers per environment): <https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-quotas.html>.

- Workflows in Amazon SageMaker Unified Studio - the "Workflows" feature, which supports both MWAA Serverless and MWAA provisioned: <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/workflow-orchestration.html>.

- SageMaker Unified Studio support for importing existing MWAA environments: <https://aws.amazon.com/about-aws/whats-new/2026/07/amazon-sagemaker-unified-studio-import-existing-mwaa-environments/>.

- `aws_mwaa_environment` Terraform resource (provisioned MWAA only): <https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/mwaa_environment>.

- Terraform AWS provider issue #45254, "Support for Amazon MWAA Serverless" - open, no implementation yet in the classic provider (checked 2026-08-08): <https://github.com/hashicorp/terraform-provider-aws/issues/45254>.

- `AWS::MWAAServerless::Workflow` CloudFormation resource - the registry type that closes the gap above (D28): <https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-mwaaserverless-workflow.html>.

- `awscc_mwaaserverless_workflow` - the Cloud Control (awscc provider) resource generated from that registry type: <https://registry.terraform.io/providers/hashicorp/awscc/latest/docs/resources/mwaaserverless_workflow>.

- Amazon MWAA Serverless key concepts (YAML workflows, per-workflow IAM role, EventBridge Scheduler underneath, no Airflow UI): <https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/mwaas-concepts.html>.

- `terraform-aws-sagemaker-unified-studio` - the official aws-ia module for provisioning SageMaker Unified Studio (domain + IAM via the aws provider, project profiles/blueprints/projects via awscc) (D26): <https://github.com/aws-ia/terraform-aws-sagemaker-unified-studio>.

- Announcement of Terraform support for SageMaker Unified Studio (2026-07): <https://aws.amazon.com/about-aws/whats-new/2026/07/amazon-sagemaker-unified-studio-terraform/>.

- Upgrading Amazon DataZone domains to SageMaker unified domains - the `domainVersion` V1/V2 distinction: <https://docs.aws.amazon.com/datazone/latest/userguide/upgrade-domain.html>.

- AWS Step Functions: <https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html>.

## Security, monitoring and cost

- Amazon Macie: <https://docs.aws.amazon.com/macie/latest/user/what-is-macie.html>.

- Amazon Macie endpoints by Region (used to check `sa-east-1` availability): <https://docs.aws.amazon.com/general/latest/gr/macie.html>.

- Amazon GuardDuty: <https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html>.

- AWS Security Hub: <https://docs.aws.amazon.com/securityhub/latest/userguide/what-is-securityhub.html>.

- AWS CloudWatch: <https://aws.amazon.com/pt/cloudwatch/>.

- AWS Secrets Manager: <https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html>.

- AWS Budgets: <https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html>.

- AWS Cost Anomaly Detection (free, ML-based spend anomaly alerts): <https://docs.aws.amazon.com/cost-management/latest/userguide/manage-ad.html>.

- AWS Well-Architected Machine Learning Lens (the AWS best-practice checklist for ML environments): <https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/machine-learning-lens.html>.

- CloudTrail log file validation (tamper-evident audit trail): <https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html>.

- S3 Object Lock — **governance vs. compliance mode**, the distinction that decides whether an administrator of the Log Archive account can bypass it (`s3:BypassGovernanceRetention`): <https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html>.

- Configuring S3 Object Lock (enabling it in place on an **existing** versioned bucket, and applying retention to existing objects with S3 Batch Operations): <https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-configure.html>.

- AWS Backup Vault Lock (Stage 12): <https://docs.aws.amazon.com/aws-backup/latest/devguide/vault-lock.html>.

- AWS Service Quotas: <https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html>.

- Track alerts through Amazon SNS in AWS Control Tower (the topics the landing zone creates, and the fact that the Audit account e-mail is subscribed to `aws-controltower-AggregateSecurityNotifications` by default): <https://docs.aws.amazon.com/controltower/latest/userguide/sns.html>.

- Compliance notifications by SNS in the audit account (why those topics are too noisy to carry a break-glass alarm): <https://docs.aws.amazon.com/controltower/latest/controlreference/receive-notifications.html>.

- Amazon SNS SMS subscriptions (the second channel for the break-glass alarm, Stage 1a step 5): <https://docs.aws.amazon.com/sns/latest/dg/sns-mobile-phone-number-as-subscriber.html>.

- Amazon SNS **SMS sandbox** (a new account may only send to *verified* destination numbers — the one-time step before the break-glass SMS channel works): <https://docs.aws.amazon.com/sns/latest/dg/sns-sms-sandbox.html>, and the verification procedure: <https://docs.aws.amazon.com/sns/latest/dg/sns-sms-sandbox-verifying-phone-numbers.html>.

- Supported countries for SMS with AWS End User Messaging (the **Brazil row**: short codes yes, long codes no, sender IDs no, no registration required — so nothing has to be bought or filed for the break-glass SMS): <https://docs.aws.amazon.com/sms-voice/latest/userguide/phone-numbers-sms-by-country.html>.

- AWS End User Messaging SMS pricing (the only published source for the per-country SMS message price, which is **not** in the Price List bulk API — see `PRICING.md` §6): <https://aws.amazon.com/end-user-messaging/pricing/>.

- Logging and monitoring in AWS Control Tower (what the landing zone logs and where): <https://docs.aws.amazon.com/controltower/latest/userguide/logging-and-monitoring.html>, and about logging: <https://docs.aws.amazon.com/controltower/latest/userguide/about-logging.html>.

- Resources not removed when a landing zone is decommissioned — the page that names the CloudWatch log group **`aws-controltower/CloudTrailLogs`** and its blueprint `AWSControlTowerBP-BASELINE-CLOUDTRAIL-MASTER`; from landing zone 3.0 it is created **only in the management account**, which is the log group the break-glass metric filter attaches to: <https://docs.aws.amazon.com/controltower/latest/userguide/resources-not-removed.html>.

- CloudTrail **AWS Management Console sign-in events** — root user sign-ins are recorded in `us-east-1` because console sign-in is a global service; the break-glass alarm only sees them because the Control Tower trail is multi-region with global service events included (Stage 1a step 5): <https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-aws-console-sign-in-events.html>.

- Sending CloudTrail events to CloudWatch Logs (the delivery leg the metric filter reads): <https://docs.aws.amazon.com/awscloudtrail/latest/userguide/send-cloudtrail-events-to-cloudwatch-logs.html>.

- Preparing an organization trail (why member-account events reach the **management account's** log group, which is what makes one metric filter cover every account): <https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-an-organizational-trail-prepare.html>.

- CloudWatch Logs metric filters, and the JSON filter-pattern syntax used by the root-activity filter: <https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html> and <https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html>.
