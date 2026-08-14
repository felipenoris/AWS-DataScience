
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

- AWS Organizations - Declarative policies: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_declarative.html>. **Read for 7.8, and it settled three things the battery's shape depends on.** (i) *"Declarative policies are enforced in the service's control plane"*, not in authorization — so they name no policy id, emit no *"explicit deny"* wording, and **govern service-linked roles**, which SCPs and RCPs do not. That is why `--phase decl`'s probes carry no `--dry-run`: a dry run stops after authorization and would report `DryRunOperation` whether or not the policy is attached. (ii) **Detaching rolls each attribute back to its previous state**, which makes the attach far more reversible than it looks. (iii) With no custom `exception_message`, AWS supplies its own — *"This action is denied due to an organizational policy in effect"* — so the message that arrives is the attribution, and the driver reports `custom-message` or `AWS-default-msg` to tell them apart. **What the page does *not* say is also load-bearing: it names no management-account exemption**, unlike the SCP and RCP pages, and control-plane enforcement is not where that exemption lives — so a root attach is expected to reach Management, and `./aws/declarative-ec2.sh -` run there is the only way to find out.

- **AWS Service Reference Information — the machine-readable list of every IAM action a service publishes**, one JSON per service at `https://servicereference.us-east-1.amazonaws.com/v1/<service>/<service>.json`, indexed at <https://servicereference.us-east-1.amazonaws.com/>: <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_service-reference.html>. Used in Stage 1c step 7.6 to answer verification (viii) — it is the only source that says what an action is *called today*, and unlike the Service Authorization Reference pages it can be read by a script rather than by eye. **Known gap, measured 2026-08-13 while scoping decision 5: it does not map `aws:RequestTag` to any of EC2's 793 actions** while declaring the key in EC2's top-level `ConditionKeys` — where S3 maps it on 11 of 180 actions and RDS on 35 of 169. So a negative answer from this file is only evidence when the same service answers positively somewhere else (Lesson 13); for EC2, use the Service Authorization Reference page or a probe.

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

- Block public access for EBS snapshots — free, **account-level and Regional**, settable org-wide only
  through a declarative policy (and then no longer changeable inside the account). The sentence Stage 1c
  step 7.8 turns on: *"Block public access for snapshots does not prevent private snapshot sharing"*, which
  is why the cross-account share is denied by SCP in 7.5 instead. It also does not cover EBS-backed AMIs —
  those need block public access for AMIs, separately:
  <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/block-public-access-snapshots.html>.

- IAM Access Analyzer — the six capabilities and, in the same page, the three things D6 and
  `plan/architecture.md` §4.2 depend on: the **resource-type list for external access** (it includes EBS and
  RDS snapshots, EFS, Lambda and SNS, none of which any RCP covers), the **narrower resource-type list for
  internal access** (S3, RDS snapshots, DynamoDB — no EFS, no catalog), and the statement that an
  external-access analyzer analyzes **only its own Region** while unused access does not:
  <https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html>. The billing dimensions are
  named on the same page — per principal-month for unused access, **per resource-month for internal access**,
  per request for custom policy checks — but the numbers are not; measure them (Lesson 6). Creating the
  internal analyzer:
  <https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-create-internal.html>.

- IAM root user (including centralized root access management for member accounts): <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html>.

- IAM permissions boundaries: <https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html>.

- Granting a user permissions to pass a role (`iam:PassRole`): <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_passrole.html>.

- `aws organizations` CLI reference (the calls `aws/list-identities.sh` uses to walk the OU tree and list the accounts): <https://docs.aws.amazon.com/cli/latest/reference/organizations/>.

- `aws sso-admin` CLI reference (Identity Center *entitlements*: instances, permission sets, assignments): <https://docs.aws.amazon.com/cli/latest/reference/sso-admin/>.

- `aws identitystore` CLI reference (Identity Center *people*: users, groups, memberships - the other side of the identity seam): <https://docs.aws.amazon.com/cli/latest/reference/identitystore/>.

## Terraform

- Terraform S3 backend (including native state locking): <https://developer.hashicorp.com/terraform/language/backend/s3>.

- Terraform AWS provider: <https://registry.terraform.io/providers/hashicorp/aws/latest/docs>.

- `aws_organizations_organizational_units` — returns the **direct children** of one parent, which is why a single `for_each` over the root misses the nested `Sandboxes` OU (Stage 2 step 5.3): <https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/organizations_organizational_units>.

- `aws_organizations_organizational_unit_descendant_organizational_units` — the recursive counterpart, given the root ID; **to be verified against the pinned provider version** before Stage 2 step 5.3 relies on it: <https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/organizations_organizational_unit_descendant_organizational_units>.

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

- ACM: importing certificates (how the internal CA's leaves reach an ALB — free, but never auto-renewed): <https://docs.aws.amazon.com/acm/latest/userguide/import-certificate.html>.

- ACM: certificate transparency logging (why a public certificate would publish the internal hostnames — D15 phase 1): <https://docs.aws.amazon.com/acm/latest/userguide/acm-concepts.html#concept-transparency>.

- Route 53 private hosted zones (the only zones this project owns before Stage 13): <https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html>.

- ICANN resolution 2024.07.29.06, reserving `.internal` from delegation in the root zone for private use — why D36 fixes the internal naming on that suffix: <https://www.icann.org/en/board-activities-and-meetings/materials/approved-resolutions-special-meeting-of-the-icann-board-29-07-2024-en>.

- VPC endpoint private DNS (served by an AWS-managed zone, scoped to the endpoint's own VPC — the limit behind Stage 3 step 4's second note): <https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html>.

- MWAA: VPC endpoints for a private-routing environment, and the Route 53 private-zone technique for names an endpoint's own private DNS will not answer (Stage 10 step 4): <https://docs.aws.amazon.com/mwaa/latest/userguide/vpc-vpe-create-access.html>.

- MWAA: managing access to service-specific VPC endpoints: <https://docs.aws.amazon.com/mwaa/latest/userguide/vpc-vpe-access.html>.

- SageMaker Unified Studio: accessing the portal — the domain URL is issued by AWS and handed to users, so nothing here needs a domain of ours (D15 phase 1): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/getting-started-access-the-portal.html>.

## SageMaker and shared storage

- SageMaker Studio notebooks and internet access: <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-notebooks-and-internet-access.html>.

- SageMaker Studio custom images: <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-byoi.html>.

- Connect to SageMaker Studio through an interface VPC endpoint (`aws.sagemaker.<region>.studio`, plus the note that `CreatePresignedDomainUrl` travels through the *SageMaker API* endpoint, and that users outside the VPC can still reach the Studio UI over the internet unless an IAM condition stops them): <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-interface-endpoint.html>.

- SageMaker IAM condition keys (`sagemaker:VpcSubnets`, `NetworkIsolation`, `InstanceTypes`, `VolumeKmsKey`): <https://docs.aws.amazon.com/sagemaker/latest/dg/security_iam_service-with-iam.html>.

- SageMaker `RetentionPolicy` for `DeleteDomain` (defaults to `Retain`): <https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_RetentionPolicy.html>.

- SageMaker Pipelines (a D7 option the first draft omitted): <https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines.html>.

- SageMaker Model Registry (model promotion, Stage 10): <https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html>.

- Amazon SageMaker Unified Studio (the direction a large institution would evaluate first, §11): <https://aws.amazon.com/sagemaker/unified-studio/>.

- Create a SageMaker Unified Studio domain, manual setup — the page that names the two roles the domain asks for, `AmazonSageMakerDomainExecution` and `AmazonSageMakerDomainService`, and shows the domain being created through the **DataZone** console: <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/create-domain-sagemaker-unified-studio-manual.html>. Read in Stage 1c step 7.6 to settle which namespace the domain evaluates under.

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

- **Centralize root access for member accounts** — the prerequisites, the two capabilities, the console and CLI paths, and the statement that accounts created afterwards have no root credentials at all (Stage 1a step 6): <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-enable-root-access.html>.

- Perform a privileged task on an AWS Organizations member account — the five task-policy ARNs, the console `Take privileged action` flow, and the two constraints that shape the step: **root cannot call `sts:AssumeRoot`**, and there is **no global STS endpoint** for it: <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user-privileged-task.html>.

- `AssumeRoot` API reference (session capped at 900 seconds, `TaskPolicyArn` required): <https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoot.html>.

- Track privileged tasks in AWS CloudTrail — the two event shapes the break-glass alarm has to be read against: the `AssumeRoot` call itself (`sessionContext.assumedRoot = "true"`, `targetPrincipal`) and the in-session actions, which are logged in the target account as `userIdentity.type = "Root"` and therefore match the root-activity filter: <https://docs.aws.amazon.com/IAM/latest/UserGuide/cloudtrail-track-privileged-tasks.html>.

- AWS Control Tower **strongly recommended preventive controls** — the SCP artifacts for `AWS-GR_RESTRICT_ROOT_USER` and `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS`, neither enabled by default, and the `ExemptAssumeRoot` / `ExemptedPrincipalArns` parameters that keep the first one compatible with centralized root access (Stage 1c step 7): <https://docs.aws.amazon.com/controltower/latest/controlreference/strongly-recommended-preventive-controls.html>.

- AWS News Blog, centrally managing root access for customers using AWS Organizations (the launch post; the CLI sequence `enable-aws-service-access` → `enable-organizations-root-credentials-management` → `enable-organizations-root-sessions`): <https://aws.amazon.com/blogs/aws/centrally-managing-root-access-for-customers-using-aws-organizations/>.

- **Resource control policies (RCPs)** — the policy type has to be enabled at the organization root before an RCP can be attached, RCPs require an organization with *all features*, they **do not affect resources in the management account**, and service-linked roles are exempt while ordinary AWS service principals are not (Stage 1c step 7.8): <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html>.

- RCP examples, and the AWS caution that a deny-based RCP "can unintentionally limit or block your use of AWS services unless you add the necessary exceptions" — the source of the `aws:PrincipalIsAWSService` carve-out beside `aws:PrincipalOrgID`: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps_examples.html> and <https://github.com/aws-samples/resource-control-policy-examples>.

- Enabling an organization policy type (`RESOURCE_CONTROL_POLICY`, `TAG_POLICY`, `DECLARATIVE_POLICY_EC2` — none of them on by default, unlike the SCPs Control Tower enables): <https://docs.aws.amazon.com/organizations/latest/userguide/enable-policy-type.html>.

- **Delegated administrator for AWS Organizations** — policy management delegated to a member account through a **resource-based delegation policy**, which is a different mechanism from `register-delegated-administrator` and is the precondition Stage 2 step 5.1 (INT-20) has to create before Terraform can own the SCPs: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_delegate_policies.html>.

- **Resource-based policy examples for AWS Organizations** — the action lists, the `organizations:PolicyType` condition, the root/OU/account resource ARNs, the caution that the delegation reaches *"policies created by any account in the organization, including the management account"*, and the sentence that decides the wildcard form for a two-level OU tree: naming a single OU *"excludes child OUs and accounts under child OUs"* (Stage 2 step 5.1): <https://docs.aws.amazon.com/organizations/latest/userguide/security_iam_resource-based-policy-examples.html>.

- **Configuring S3 Object Lock** — enabling it on an *existing* bucket from the console or `put-object-lock-configuration`, the permanence ("you can't disable Object Lock or suspend versioning for that bucket"), and the constraint that decides which Control Tower bucket this applies to: **a bucket with Object Lock cannot be a destination for S3 server access logs** (Stage 1d step 9): <https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-configure.html>.

- **Managing GuardDuty accounts with AWS Organizations** — "For this administrator account, GuardDuty gets enabled automatically only in the current AWS Region", which is why the delegation moves to Stage 4 with the enablement rather than happening in Stage 1b step 8: <https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_organizations.html>.

- **Integrating Security Hub CSPM with AWS Organizations** — designating the delegated administrator "enables Security Hub CSPM in the current AWS Region for the delegated administrator account", the same coupling as GuardDuty (Stage 1b step 8.1): <https://docs.aws.amazon.com/securityhub/latest/userguide/designate-orgs-admin-account.html>.

- **Monitor resource changes with AWS Config (Control Tower)** — landing zone 3.0+ limits *global* resources to the home Region, and the only documented way to customise which resource types are recorded is the lifecycle-event solution, not a Control Tower setting (Stage 1d step 10): <https://docs.aws.amazon.com/controltower/latest/userguide/monitoring-with-config.html> and <https://aws.amazon.com/blogs/mt/customize-aws-config-resource-tracking-in-aws-control-tower-environment/>.

- **`iam-root-access-key-check` (AWS Config managed rule)** — identifier `IAM_ROOT_ACCESS_KEY_CHECK`, **trigger type Periodic, no parameters**: it evaluates on a schedule against the account rather than on a recorded configuration item, which is why it is **independent of whatever Stage 1d step 10.3 decides about the recorder's scope** — correcting D16's "enabled with the recorder scope" (Stage 1d step 10.4): <https://docs.aws.amazon.com/config/latest/developerguide/iam-root-access-key-check.html>.

- **Managing AWS Config rules across an organization** — the reason 10.4 creates the rule by hand in Management instead of deploying it as an organization Config rule from the Audit delegated administrator: AWS Config does not create the service-linked role in the management account by itself, and "if you do not have an SLR for your management account, you will not be able to deploy resources to that account from a delegated administrator account" — member accounts are unaffected (Stage 1d step 10.4): <https://docs.aws.amazon.com/config/latest/developerguide/config-rule-multi-account-deployment.html>.

- **Region deny control applied to the OU (`CT.MULTISERVICE.PV.1`)** — the *configurable*, OU-scoped Region deny, with its `AllowedRegions` / `ExemptedActions` / `ExemptedPrincipalARNs` parameters and the full default `NotAction` and principal-exemption lists in its SCP artifact. This is the control that **can** be exercised against the `Policy Test` OU first, which is what corrected Stage 1c step 7.7: <https://docs.aws.amazon.com/controltower/latest/userguide/ou-region-deny.html>.

- **Configure the Region deny control (`GRREGIONDENY`)** — the landing-zone-wide variant: enabled from *Landing zone settings → Modify settings*, applies to every registered OU at once, cannot deny the home Region, and requires that no resources already exist in the denied Regions (Stage 1c step 7.7): <https://docs.aws.amazon.com/controltower/latest/userguide/region-deny.html>.

- **Strongly recommended preventive controls (Control Tower)** — the status of `AWS-GR_RESTRICT_ROOT_USER` and `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS`, and the `ExemptAssumeRoot` parameter that carves the centralized-root `sts:AssumeRoot` path back out — set per OU, only on `AWS-GR_RESTRICT_ROOT_USER`, and it does not accept `false` (Stage 1c step 7.7): <https://docs.aws.amazon.com/controltower/latest/controlreference/strongly-recommended-preventive-controls.html>.

- **IAM Identity Center information in CloudTrail** — the three event sources that record a group-membership change: `sso-directory.amazonaws.com` (`AddMemberToGroup`/`RemoveMemberFromGroup`, console), `identitystore.amazonaws.com` (`CreateGroupMembership`/`DeleteGroupMembership`, API/Terraform) and `sso.amazonaws.com` (`CreateAccountAssignment`/`DeleteAccountAssignment`), with AWS's own recommendation to "consider both public and console API operations" (Stage 1b step 8.3): <https://docs.aws.amazon.com/singlesignon/latest/userguide/sso-info-in-cloudtrail.html>.

- **Modifications to CloudTrail event data of IAM Identity Center** — the January 2025 changes to `userName`, `principalId`, `userIdentity` type and group `displayName`. It used to be cited as the reason the Stage 1b step 8.3 filter keys on group **IDs**; since 2026-08-09 that filter **matches every membership and assignment event and keys on nothing**, and this reference is one of the three reasons why — a pattern keyed on identity-plane payload fields, name or GUID, is a pattern with a hidden expiry (`plan/institutional-delta.md` carries the row for when filtering becomes necessary again): <https://aws.amazon.com/blogs/security/modifications-to-aws-cloudtrail-event-data-of-iam-identity-center/>.

- **AWS Organizations increases SCP quotas (May 2026)** — 10 SCPs per node and 10 240 characters per policy, up from 5 and 5 120; RCP quotas are not part of the same increase, which is the sizing budget Stage 1c step 7.1 now states: <https://aws.amazon.com/about-aws/whats-new/2026/05/aws-organizations-increased-scp-quotas/>.

- **Establish permissions guardrails using data perimeters** — the trusted-resources SCP shape that Stage 1c step 7.5 now uses for `aws:ResourceOrgID`: `StringNotEqualsIfExists` beside `BoolIfExists` on `aws:PrincipalIsAWSService`, so a call that does not populate the key is not denied and calls AWS makes on your behalf are not caught: <https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_data-perimeters.html> and <https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/>.

- **Notebooks in SageMaker Unified Studio** — the page that settles three things at once for the 2026-08-13 objectives: notebooks run on **JupyterLab spaces**, the default Spark runtime is **Amazon Athena for Apache Spark, which "doesn't support Virtual Private Cloud (VPC)"** with EMR Serverless / EMR / Glue as the VPC-capable alternatives and a *Network isolation* procedure for disabling it, and **notebooks do not support trusted identity propagation** — in an Identity Center domain they use *compatibility permission mode* for data access (Stage 1c step 7.6's action table; `plan/open-questions.md` items 12 and 13): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/notebooks.html>.

- **Spaces in SageMaker Studio / Unified Studio** — a space is "a combination of a compute instance, storage and other runtime configurations" behind a JupyterLab or Code Editor application, created through `sagemaker:CreateSpace` / `sagemaker:CreateApp`. This is the evidence that settled **decision 1** of Stage 1c: denying the *classic* `sagemaker:CreateNotebookInstance` costs none of the `CLAUDE.md` notebook objectives, because they are a different product surface: <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-jl-user-guide-create-space.html> and <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/jupyterlab.html>.

- **Remote access to SageMaker spaces from a local IDE** — the `sagemaker:StartSession` API behind "connect your local VS Code to a Unified Studio space", the three connection methods (deep link, AWS Toolkit, SSH), and AWS's own recommendation to scope `StartSession` by tag to a user's *own* private applications. It is the action that matches neither `sagemaker:Create*` nor `datazone:*`, which is why Stage 1c step 7.6 names it explicitly and why `plan/open-questions.md` item 14 treats it as an egress channel: <https://docs.aws.amazon.com/sagemaker/latest/dg/remote-access.html> and <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/local-ide-support.html>.

- **Workflows in SageMaker Unified Studio** — the Workflows tool is **Amazon MWAA**, in both a *serverless* and a *provisioned* form, and existing MWAA environments can be connected to a project. It confirms rather than changes D7/D28: the `CLAUDE.md` "workflows" feature and Stage 10's orchestration comparison are the same surface (`plan/open-questions.md` item 15): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/workflow-orchestration.html>.
