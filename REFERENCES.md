
# References

## Tools

- AWS Console login: <https://aws.amazon.com/>.

- Docs to install the `aws` client: <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>.

- Docs to install `terraform`: <https://developer.hashicorp.com/terraform/install>.

- uv: <https://docs.astral.sh/uv/>.

- AWS Pricing Calculator: <https://calculator.aws/>.

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

- AWS IAM Identity Center: <https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html>.

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

- AWS Backup Vault Lock (Stage 12): <https://docs.aws.amazon.com/aws-backup/latest/devguide/vault-lock.html>.

- AWS Service Quotas: <https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html>.
