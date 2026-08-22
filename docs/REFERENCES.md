
# References

## Tools

- AWS Console login: <https://aws.amazon.com/>.

- Docs to install the `aws` client: <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>.

- Docs to install `terraform`: <https://developer.hashicorp.com/terraform/install>.

- uv: <https://docs.astral.sh/uv/>. Used to install the two Python gates below, so the versions in
  `CLAUDE.md` are reproducible on another machine with one command each — and, since 2026-08-15, to run
  **every script in this repository**: they are Python 3 on the project in `pyproject.toml`, and their
  `#!/usr/bin/env -S uv run --quiet` shebang makes `uv run` resolve the pinned interpreter
  (`.python-version`) and the locked environment (`uv.lock`) per invocation. Read for the project /
  script-running model: <https://docs.astral.sh/uv/guides/projects/>.

- `ruff`: <https://docs.astral.sh/ruff/>. Linter + formatter for the repository's Python (dev-only
  dependency of the uv project); runs through `pre-commit` via `uv run`, so the gate binds to the locked
  version rather than to whatever is on PATH.

- `pre-commit`: <https://pre-commit.com/>. The hook collection the repository configures is
  `antonbabenko/pre-commit-terraform`: <https://github.com/antonbabenko/pre-commit-terraform> — read for the
  `terraform_validate` argument syntax, which is `--tf-init-args=`, not the `--init-args=` a paraphrase
  would produce (Stage 2 step 6.4).

- `checkov`: <https://www.checkov.io/>. The required policy gate of Stage 2 step 6.5; suppressions are
  inline `# checkov:skip=CKV_...` with a reason, never a global exclusion.

- `tflint`: <https://github.com/terraform-linters/tflint>, with the AWS ruleset
  <https://github.com/terraform-linters/tflint-ruleset-aws>. **A Go binary with no Python or Homebrew path**,
  so on a machine without `brew`/`go`/`npm` it is a release download plus a checksum check — which is why
  its install is a step somebody performs rather than a line in a manifest.

- AWS Pricing Calculator: <https://calculator.aws/>.

- AWS Price List bulk API - offer index (all service codes): <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json>. Per service and Region: `offers/v1.0/aws/<serviceCode>/current/<region>/index.json`; the Regions a service is offered in are at `offers/v1.0/aws/<serviceCode>/current/region_index.json`. Public, no credentials required - the source of every rate in `docs/PRICING.md`.

- AWS CodeArtifact endpoints and quotas (used to confirm that CodeArtifact is **not** available in `sa-east-1`): <https://docs.aws.amazon.com/general/latest/gr/codeartifact.html>.

- etl-cookbook-tutorial: <https://github.com/felipenoris/etl-cookbook-tutorial>.

## Organization and identity

- AWS Control Tower: <https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html>.

- AWS Control Tower endpoints by Region (used to check `sa-east-1` availability): <https://docs.aws.amazon.com/general/latest/gr/controltower.html>.

- Regional differences for AWS Control Tower functionality: <https://docs.aws.amazon.com/controltower/latest/userguide/regional-differences.html>.

- AWS Organizations - Service Control Policies: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html>.

- AWS Organizations - Resource Control Policies (RCPs): <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html>.

- AWS Organizations - Tag policies: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html>.

- AWS Organizations - Declarative policies: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_declarative.html>. **Read for 7.8, and it settled three things the battery's shape depends on.** (i) *"Declarative policies are enforced in the service's control plane"*, not in authorization — so they name no policy id, emit no *"explicit deny"* wording, and **govern service-linked roles**, which SCPs and RCPs do not. That is why `--phase decl`'s probes carry no `--dry-run`: a dry run stops after authorization and would report `DryRunOperation` whether or not the policy is attached. (ii) **Detaching rolls each attribute back to its previous state**, which makes the attach far more reversible than it looks. (iii) With no custom `exception_message`, AWS supplies its own — *"This action is denied due to an organizational policy in effect"* — so the message that arrives is the attribution, and the driver reports `custom-message` or `AWS-default-msg` to tell them apart. **What the page does not say, and what cost two false failures on 2026-08-14: the same message is echoed by a *successful* read of a managed attribute** — `ec2 get-instance-metadata-defaults` returns rc=0 with `"ManagedBy": "declarative-policy"` and the custom text in `"ManagedExceptionMessage"` — so the marker distinguishes *this* policy from AWS's default wording but not enforcement from confirmation. Only the exit code does that, which is why `classify` now gates both declarative branches on it. **What the page does *not* say is also load-bearing: it names no management-account exemption**, unlike the SCP and RCP pages, and control-plane enforcement is not where that exemption lives — so a root attach is expected to reach Management, and `./aws/declarative-ec2.py -` run there is the only way to find out.

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
  `docs/plan/architecture.md` §4.2 depend on: the **resource-type list for external access** (it includes EBS and
  RDS snapshots, EFS, Lambda and SNS, none of which any RCP covers), the **narrower resource-type list for
  internal access** (S3, RDS snapshots, DynamoDB — no EFS, no catalog), and the statement that an
  external-access analyzer analyzes **only its own Region** while unused access does not:
  <https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html>. The billing dimensions are
  named on the same page — per principal-month for unused access, **per resource-month for internal access**,
  per request for custom policy checks — **and the numbers are measured since 2026-08-17**
  (`docs/PRICING.md` §6: internal USD 9.00/resource-month, unused 0.20, checks 0.002; the pricing page,
  <https://aws.amazon.com/iam/access-analyzer/pricing/>, adds that internal/unused analyzers are charged
  **once during setup and then monthly on the first**, not prorated). Creating the internal analyzer — org
  zone of trust from the delegated administrator, **only one org-level internal analyzer per
  organization**, resources by exact ARN (S3 bucket ARNs only, no prefixes):
  <https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-create-internal.html>.

- IAM root user (including centralized root access management for member accounts): <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html>.

- IAM permissions boundaries: <https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html>.

- Granting a user permissions to pass a role (`iam:PassRole`): <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_passrole.html>.

- `aws organizations` CLI reference (the calls `aws/list-identities.py` uses to walk the OU tree and list the accounts): <https://docs.aws.amazon.com/cli/latest/reference/organizations/>.

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

- **Route 53: associating a VPC and a private hosted zone across accounts** — the two-call handshake of Stage 3 step 4.4, and the sentence that answered verification (vii): deleting the authorization is *recommended*, "does not affect the association", and a re-association needs a fresh one: <https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zone-private-associate-vpcs-different-accounts.html>.

- **Walkthrough: configure AWS Control Tower without a VPC** — the page that corrected Stage 3 step 0 (2026-08-16): the supported cleanup of an existing account's Account Factory VPC is **removing its stack instance from `AWSControlTowerBP-VPC-ACCOUNT-FACTORY-V1`**, and the Account Factory fields that stop future vends creating one (internet-accessible subnet off, private subnets 0, every Region checkbox cleared): <https://docs.aws.amazon.com/controltower/latest/userguide/configure-without-vpc.html>.

- **Amazon ECR interface VPC endpoints** — the minimum S3 gateway-endpoint permission for image pulls: `s3:GetObject` on `arn:aws:s3:::prod-<region>-starport-layer-bucket/*` (Stage 3 step 9.3's fourth family, confirmed). **Re-read 2026-08-22 for the other direction** (Stage 6 step 5.0, `devbox.md` §P): the same page states that `ecr.dkr` is the Docker Registry API and that *"Docker client commands such as `push` and `pull` use this endpoint"*, while S3 is what a container reaches to **download** layers — so a **push** never touches the S3 gateway endpoint and the allow-list's missing `PutObject` on the starport bucket is the documented shape rather than a gap: <https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html>.

- **SSM Agent communications with AWS managed S3 buckets** — the documented bucket list behind Stage 3 step 9.3's SSM family: `amazon-ssm-<region>` (agent updates) and `aws-ssm-<region>` (SSM document modules) at minimum, plus the patching and Distributor buckets this design does not use yet: <https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-agent-technical-details.html>.

- **Update dnf on an Amazon Linux instance without internet access** — the page that withdrew Stage 3's mirror-list claim (2026-08-16): AL2023's default `mirrorlist=` URL points into the regional repository bucket itself (`al2023-repos-<region>-de612dc2`, the S3 dualstack hostname), so the S3 gateway endpoint carries the whole package path; only a repo file referencing `cdn.amazonlinux.com` needs internet: <https://repost.aws/knowledge-center/ec2-al1-al2-update-yum-without-internet>.

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

- SageMaker Unified Studio terminology and concepts — the definitions `docs/SMUS.md`'s object-model section quotes (domain, domain unit, project and its three capabilities, project profile, the project S3 path and its `<bucket>/<domain_id>/<project_id>/<scope>/` structure, S3 Object Collection): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/concepts.html>. Read 2026-08-19.

- Project profiles in SageMaker Unified Studio — the template definition and the four template profiles: <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/project-profiles.html>. Read 2026-08-19.

- Custom project profile — the console fields a profile fixes (blueprint set, pinned account/Region or account pools, Tooling deployment settings, S3-or-Git files storage, authorization, readiness) and the "Projects do not provide strong security isolation" sentence `docs/SMUS.md` quotes: <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/custom.html>. Read 2026-08-19.

- S3-based shared project storage for SMUS projects (2025-09 announcement) — the `amazon-datazone-<account-id>-<region>-<domain-id>` bucket pattern, the `shared/` mount in JupyterLab/Code Editor, S3 as the post-CodeCommit default: <https://aws.amazon.com/blogs/big-data/amazon-sagemaker-introduces-amazon-s3-based-shared-storage-for-enhanced-project-collaboration/>. Read 2026-08-19.

- Amazon S3 data in SageMaker Unified Studio — the S3 Object Collection asset type for existing buckets/prefixes: <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/data-s3.html>. Read 2026-08-19.

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

- Athena workgroup settings, including `EnforceWorkGroupConfiguration` — the console calls it "override client-side settings" (the control that makes D19's enforced results zone a boundary rather than a suggestion — one location per workgroup, so `results/` is per-persona; first applied at Stage 5 pass 4b in both consumers): <https://docs.aws.amazon.com/athena/latest/ug/workgroups-settings.html>.

- Specifying an Athena query result location using a workgroup (and the CTAS `external_location` conflict it causes): <https://docs.aws.amazon.com/athena/latest/ug/query-results-specify-location-workgroup.html>.

- AWS Lake Formation cross-account permissions: <https://docs.aws.amazon.com/lake-formation/latest/dg/cross-account-permissions.html>.

- Lake Formation cross-account sharing prerequisites (the grantor needs `AWSLakeFormationCrossAccountManager`; the target's data lake administrator needs `ram:AcceptResourceShareInvitation` and `ram:EnableSharingWithAwsOrganization`): <https://docs.aws.amazon.com/lake-formation/latest/dg/cross-account-prereqs.html>.

- Updating Lake Formation cross-account data sharing version settings (version 3 or above is required to share with an Organization or an OU, and it is what removes the per-share RAM invitation): <https://docs.aws.amazon.com/lake-formation/latest/dg/optimize-ram.html>.

- Lake Formation cross-account data sharing best practices and considerations: <https://docs.aws.amazon.com/lake-formation/latest/dg/cross-account-notes.html>.

- Lake Formation hybrid access mode (the documented exception in D13): <https://docs.aws.amazon.com/lake-formation/latest/dg/hybrid-access-mode.html>.

- Lake Formation tag-based access control — best practices and considerations (LF-Tag creators and delegation, expression grants, cross-account LF-TBAC prerequisites, the limits; read 2026-08-17 for the Stage 5 governance review): <https://docs.aws.amazon.com/lake-formation/latest/dg/lf-tag-considerations.html>.

- **LF-Tag permissions — the grants that let a persona TAG rather than read** (read 2026-08-19 for Stage 5 pass 2, the governance manager's own grants). What the pages establish and this stage relies on: the permissions grantable *on an LF-Tag itself* are `ASSOCIATE`, `ALTER` and `DROP`; **a principal holding `ASSOCIATE` may assign that tag to a Data Catalog resource, and granting `ASSOCIATE` implicitly grants `DESCRIBE`**; the permissions are themselves grantable, so only a data lake administrator can grant them until it delegates with the grant option. **A provenance note, because it changes how far this row may be leaned on:** these pages are JavaScript-rendered and did **not** return a body to an automated fetch — the statements above come from AWS's own indexed text via search, not from a read of the rendered page. **Superseded 2026-08-19 (pass 3), and the correction is a method rather than a fact:** the same pages read normally through a *rendering* browser, so "AWS docs cannot be fetched" was never true — only "cannot be fetched by the plain fetcher" was. Anything below dated 2026-08-19 or later is a read of the rendered page. **The complementary question that was deliberately left unasserted is now answered, in the LF-TBAC considerations page rather than in any of the three pages linked here:** *"You need to have `Grant with LF-Tag expressions` permission to grant data permissions on Data Catalog resources by using the LF-TBAC method. The data lake administrator and the LF-Tag creator implicitly receive this permission"* — so a persona holding only `ASSOCIATE` on the tags and `DESCRIBE` on the catalog, which is exactly what the governance manager holds, **can tag and cannot grant.** That is what decision 5 intended, now established rather than assumed. **One ambiguity survives and is Stage 6's, unchanged:** the same sentence gives the implicit permission to the *LF-Tag creator*, and the persona's IAM half carries `lakeformation:CreateLFTag` — whether that makes it a creator for tags it did **not** create is not stated anywhere, and only a real governance-manager session answers it: <https://docs.aws.amazon.com/lake-formation/latest/dg/TBAC-granting-tags.html>, <https://docs.aws.amazon.com/lake-formation/latest/dg/TBAC-security.html> and the permissions reference <https://docs.aws.amazon.com/lake-formation/latest/dg/lf-permissions-reference.html>.

- **Cross-account LF-TBAC sharing — the two statements Stage 5 pass 3 is built on** (read 2026-08-19, rendered pages, for step 7). **First, the grant option is an imperative and not a style:** *"Because the data lake administrator must grant permissions on shared resources to the principals in the grantee account, you must always grant cross-account permissions with the grant option"* — a cross-account grant lands on the **account**, and nothing inside it can use the share until that account's own data lake administrator passes it on, which requires the option. The receiving side of the same rule, with the worked LF-Tag example, is on the regranting page. The bound that keeps it from being a delegation is on the considerations page: a resource shared **with** an account may be granted only to principals **in** that account — never onward to another account, to an organization, or to `IAMAllowedPrincipals`. **Second, the prerequisite this stage recorded flatly on 2026-08-17 is conditional**, and the two AWS pages differ in emphasis: the LF-TBAC considerations page says cross-account LF-TBAC "requires additions to the Data Catalog resource policy", while the Prerequisites page scopes it — the `glue:ShareResource` statement is needed by an account **already** sharing through an AWS Glue Data Catalog resource policy (the version 1/2 path), and "is not required if your account has made no cross-account grants using the AWS Glue Data Catalog resource policy". Measured in Data Governance the same day: `glue:GetResourcePolicy` → `EntityNotFoundException`, so the condition does not hold and no policy is written: <https://docs.aws.amazon.com/lake-formation/latest/dg/cross-account-TBAC.html>, <https://docs.aws.amazon.com/lake-formation/latest/dg/regranting-shared-resources.html>.

- **What the consumer side of a share requires, which is why pass 4 is more than resource links** (read 2026-08-19, the Prerequisites and LF-TBAC pages): *"at least one user in the consumer account must be a data lake administrator to view shared resources"*, and *"other principals can't access shared resources until the data lake administrator grants them permissions"*. So each Interactive account owes a `DataLakeSettings` of its own before a link can resolve — and it owes it with the same two hazards this stage already met on the producer side: the `Parameters` map that a settings apply replaces wholesale (INT-11) and the `Create*DefaultPermissions` that must be cleared **before** the first local database exists (Lesson 27).

- AWS data governance framing — the curate/understand/protect triad (read 2026-08-17; the "curate" third is the one this plan has no owner for): <https://aws.amazon.com/what-is/data-governance/>.

- AWS Well-Architected **Data Analytics Lens** (design principles: least privilege for analytics users, classify data, govern data changes): <https://docs.aws.amazon.com/wellarchitected/latest/analytics-lens/analytics-lens.html>. **Machine Learning Lens**, data-protection section (non-production environments get restricted or anonymized datasets — the row the Sandbox share deviates from): <https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/data-protection.html>.

- Implementing data governance on AWS — automation, tagging and lifecycle (AWS Security Blog, part 2; classification-driven controls and tag-driven lifecycle, read 2026-08-17): <https://aws.amazon.com/blogs/security/implementing-data-governance-on-aws-automation-tagging-and-lifecycle-strategy-part-2/>.

- Data classification whitepaper (using AWS Cloud to support data classification): <https://docs.aws.amazon.com/whitepapers/latest/data-classification/using-aws-cloud-to-support-data-classification.html>.

- **Lake Formation data filtering and cell-level security** — data cells filters (a per-table object:
  column include/exclude list + a PartiQL row expression), granted with `SELECT` and applying to reads
  only; the mechanism behind Stage 11 step 2:
  <https://docs.aws.amazon.com/lake-formation/latest/dg/data-filtering.html>.

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

- **Read for the Stage 7 revision (2026-08-16)** — the pass that produced the corrections in that stage's
  status row:
  - *Protected environments and deployment approvals are Premium* — the tier line behind Lesson 12 and the
    two Stage 8 gates (Stage 7 step 3.3): <https://docs.gitlab.com/ci/environments/protected_environments/>.
  - *SAML Group Sync is Premium* (login itself is Free; memberships stay hand-maintained):
    <https://docs.gitlab.com/user/group/saml_sso/group_sync/>.
  - *Runner authentication tokens* — runners are created first (UI/API), then registered with a `glrt-…`
    token; registration tokens are deprecated with removal scheduled for 20.0 (Stage 7 step 6.1):
    <https://docs.gitlab.com/runner/register/>.
  - *GitLab backups* — `gitlab-backup create` uploads to S3 via `backup_upload_connection`;
    **`gitlab-secrets.json` and `gitlab.rb` are excluded** and a restore without the secrets file cannot
    decrypt the database — the reason for Stage 7 step 1.5's restore-or-generate flow:
    <https://docs.gitlab.com/administration/backup_restore/backup_gitlab/>.
  - *Consolidated object storage* — one configuration block for artifacts/LFS/uploads, `use_iam_profile`
    (no keys — principle 2), single-bucket virtual buckets documented, **backups excluded from this form**
    (Stage 7 step 1.3): <https://docs.gitlab.com/administration/object_storage/>.
  - *GitLab Pages on Omnibus* — a domain **distinct from the GitLab host** (the cookie/XSS rationale behind
    `pages.internal`), the wildcard record + wildcard certificate shape, `pages_external_url` +
    `pages_nginx` TLS keys, and access control as a Free-tier feature (Stage 7 step 4):
    <https://docs.gitlab.com/administration/pages/>.
  - *Omnibus supported OSes* — Amazon Linux 2023 is supported since 16.3.0, amd64 **and arm64**, which is
    what lets the GitLab host keep the project's AL2023/SSM-parameter AMI pattern (Stage 7 step 1.2):
    <https://docs.gitlab.com/administration/package_information/supported_os/>.
  - *Kaniko is archived* (2025-06) and its GitLab tutorial removed — container builds use BuildKit rootless
    or Buildah (Stage 7 step 6.2): <https://github.com/GoogleContainerTools/kaniko> and the removed page
    <https://docs.gitlab.com/ci/docker/using_kaniko/>.
  - *ECR pull-through cache* — the supported upstreams, the `ecr-pullthroughcache/…` secret-name
    requirement for credentialed ones, the **immutability trap** (an immutable tag blocks the cache
    update) and the **first-pull internet-route requirement** (Stage 7 step 5.2):
    <https://docs.aws.amazon.com/AmazonECR/latest/userguide/pull-through-cache.html>.
  - *ECR scanning types* — basic (free, OS-only, scan-on-push, findings via
    `DescribeImageScanFindings`) versus enhanced (Amazon Inspector, OS + language packages, continuous,
    metered) — Stage 7 decision 2: <https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html>.
  - *CodeArtifact Cargo support* (GA 2024-06, external connection `public:crates-io` — closes the
    confirm-half of `docs/plan/open-questions.md` item 5's Rust row at the documentation level; the
    in-practice half stays at Stage 6): <https://docs.aws.amazon.com/codeartifact/latest/ug/configure-use-cargo.html>.
  - *Custom SAML 2.0 applications in IAM Identity Center* — the ACS URL / SAML audience fields and
    attribute mappings Stage 7 step 3.1 names: <https://docs.aws.amazon.com/singlesignon/latest/userguide/samlapps.html>.
  - *CodeConnections hosts for self-managed GitLab* — a host needs network reach to the instance, which the
    no-VPC domain account does not have (INT-13's expected failure, Stage 7 step 7.2):
    <https://docs.aws.amazon.com/dtconsole/latest/userguide/connections-host.html>.
  - *Prices measured for this revision* (Lesson 6, the bulk API): Secrets Manager
    <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSSecretsManager/current/us-west-2/index.json>
    and Amazon Inspector v2
    <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonInspectorV2/current/us-west-2/index.json>.

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

- Terraform AWS provider issue #45254, "Support for Amazon MWAA Serverless" - open, no implementation yet in the classic provider (checked 2026-08-08; re-checked 2026-08-16 - PR #45256 merged only service scaffolding, no resource: <https://github.com/hashicorp/terraform-provider-aws/pull/45256>): <https://github.com/hashicorp/terraform-provider-aws/issues/45254>.

- `AWS::MWAAServerless::Workflow` CloudFormation resource - the registry type that closes the gap above (D28): <https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-mwaaserverless-workflow.html>.

- `awscc_mwaaserverless_workflow` - the Cloud Control (awscc provider) resource generated from that registry type: <https://registry.terraform.io/providers/hashicorp/awscc/latest/docs/resources/mwaaserverless_workflow>.

- Amazon MWAA Serverless key concepts (YAML workflows, per-workflow IAM role, EventBridge Scheduler underneath, no Airflow UI): <https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/mwaas-concepts.html>.

- **Read for the Stage 10 revision, 2026-08-16** — the documentation pass behind the pass/verification rewrite:
  - *MWAA Serverless supported operators* — Amazon-provider operators only, no `PythonOperator`/`BashOperator`; ECS/EKS/Batch/Lambda/Glue/SageMaker are the code paths: <https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/operators.html>.
  - *MWAA Serverless supported Airflow parameters* — the schedule lives in the YAML (`schedule`, cron); `retries` ≤ 3, `retry_delay` ≤ 300 s, `execution_timeout` ≤ 3 600 s; `catchup`, callbacks and `trigger_rule` are ignored: <https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/supported-airflow-parameters.html>.
  - *MWAA Serverless quotas* — 50 KB YAML, **60-minute task timeout**, 100 workflows, **50 versions per workflow**, 20 concurrent runs per workflow: <https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/mwaa-serverless-quotas.html>.
  - *MWAA Serverless networking* — `NetworkConfiguration` optional; absent, tasks run in the **service's** VPC; set, ECS workers land in the customer's private subnets (≥ 2 AZs, self-referencing SG), with VPC endpoints for each service the tasks call under private routing: <https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/networking.html>.
  - *MWAA Serverless execution role* — trust `airflow-serverless.amazonaws.com`, one role per workflow, `logs:CreateLogStream`/`PutLogEvents` required: <https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/get-started-execution-role.html>; the service-linked role `AWSServiceRoleForAmazonMWAAServerless`, auto-created at the first `CreateWorkflow` (Lesson 17): <https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/using-service-linked-roles.html>.
  - *MWAA Serverless observability* — run/task APIs, per-task log streams, the auto-created `/aws/mwaa-serverless/<id>/` group when none is named: <https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/observe-with-cloudwatch.html>; **EventBridge events since 2026-06** (source `aws.airflow-serverless`, 15 detail types): <https://docs.aws.amazon.com/eventbridge/latest/ref/events-ref-airflow-serverless.html> and <https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-mwaa-serverless-eventbridge/>.
  - *The Python→YAML converter* — `python-to-yaml-dag-converter-mwaa-serverless` (dag-factory 1.0 target; AWS-provider operators only; no dynamic task mapping): <https://github.com/awslabs/python-to-yaml-dag-converter-mwaa-serverless>.
  - *Serverless workflows in SageMaker Unified Studio* — and the two-way sync ("create workflows in either platform and access them from both"): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/serverless-workflows.html> and <https://docs.aws.amazon.com/mwaa/latest/mwaa-serverless-userguide/workflows.html>.
  - *The OnDemand Workflows blueprint* — the **provisioned**-MWAA flavour of the Studio's Workflows tool, refused at Stage 10 step 0.4: <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/modify-on-demand-workflows-blueprint.html>.
  - *Step Functions Standard vs Express* — Express supports no `.sync` pattern and caps at 5 minutes, which is what makes design B Standard: <https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html>.
  - *Step Functions logging* — `LoggingConfiguration`, the ten `logs:*` delivery actions on `Resource: "*"`, the `/aws/vendedlogs/states` prefix against the 5 120-character resource-policy limit and the ten-policies-per-Region quota: <https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html>.
  - *Step Functions `.sync` integrations* — ECS (`StepFunctionsGetEventsForECSTaskRule` + scoped `PassRole`): <https://docs.aws.amazon.com/step-functions/latest/dg/connect-ecs.html>; Glue (polling, no managed rule): <https://docs.aws.amazon.com/step-functions/latest/dg/connect-glue.html>; SageMaker (training/transform rules + conditioned `PassRole`): <https://docs.aws.amazon.com/step-functions/latest/dg/connect-sagemaker.html>.
  - *Step Functions error handling* (`Retry`/`Catch`, the predefined error names): <https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html>; *execution-status events to EventBridge* (Standard only — B's failure rule): <https://docs.aws.amazon.com/step-functions/latest/dg/eventbridge-integration.html> and <https://docs.aws.amazon.com/eventbridge/latest/ref/events-ref-states.html>.
  - *EventBridge Scheduler* — what it is, and AWS's own recommendation of it over legacy scheduled rules: <https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html> and <https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html>; templated targets (`states:StartExecution`, the `scheduler.amazonaws.com` execution role): <https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-templated.html>; cron/timezone/DST semantics: <https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html>.
  - *Terraform resources for design B*: <https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sfn_state_machine> and <https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/scheduler_schedule>.
  - *Model Registry cross-account deployment* — the model-package-group resource policy, the ECR repository policy, the artifact S3/KMS, and the requirement that training `OutputDataConfig` name a KMS key: <https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry-deploy.html>; *approval statuses and `UpdateModelPackage`*: <https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry-approve.html>; *the `SageMaker Model Package State Change` EventBridge event* (duplicates possible): <https://docs.aws.amazon.com/sagemaker/latest/dg/automating-sagemaker-with-eventbridge.html>.
  - *Serving shapes priced against D11/D12* — batch transform (per-job instances): <https://docs.aws.amazon.com/sagemaker/latest/dg/batch-transform.html>; Serverless Inference (scales to zero, **no VPC configuration**): <https://docs.aws.amazon.com/sagemaker/latest/dg/serverless-endpoints.html>.
  - *Prices measured for this revision* (Lesson 6, the bulk API): Step Functions <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonStates/current/us-west-2/index.json>, EventBridge/Scheduler <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSEvents/current/us-west-2/index.json>, and the SageMaker serving rows of `docs/PRICING.md` §8 <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonSageMaker/current/us-west-2/index.json>.

- `terraform-aws-sagemaker-unified-studio` - the official aws-ia module for provisioning SageMaker Unified Studio (domain + IAM via the aws provider, project profiles/blueprints/projects via awscc) (D26): <https://github.com/aws-ia/terraform-aws-sagemaker-unified-studio>.

- Announcement of Terraform support for SageMaker Unified Studio (2026-07): <https://aws.amazon.com/about-aws/whats-new/2026/07/amazon-sagemaker-unified-studio-terraform/>.

- Upgrading Amazon DataZone domains to SageMaker unified domains - the `domainVersion` V1/V2 distinction: <https://docs.aws.amazon.com/datazone/latest/userguide/upgrade-domain.html>.

- AWS Step Functions: <https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html>.

## Security, monitoring and cost

- Amazon Macie: <https://docs.aws.amazon.com/macie/latest/user/what-is-macie.html>.

- Amazon Macie endpoints by Region (used to check `sa-east-1` availability): <https://docs.aws.amazon.com/general/latest/gr/macie.html>.

- **Managing Macie accounts with AWS Organizations, and the integration steps** — the two facts Stage 11
  step 1 is written against: designating the delegated administrator *enables Macie in that account*, and
  auto-enable covers **new** accounts only — "Turning on this setting doesn't affect existing accounts in
  your organization", which must be added one by one (`create-member` takes the account's e-mail; the
  console flow does not): <https://docs.aws.amazon.com/macie/latest/user/macie-organizations.html> and
  <https://docs.aws.amazon.com/macie/latest/user/accounts-mgmt-ao-integrate.html>.

- Amazon GuardDuty: <https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html>.

- **GuardDuty S3 Protection** — monitors CloudTrail data events for S3 through GuardDuty's own stream
  ("you don't need to explicitly enable or configure S3 data event logging in AWS CloudTrail"), with its
  own 30-day free trial on first enablement — the fact that keeps Stage 11 steps 4 and 5 complementary
  rather than redundant: <https://docs.aws.amazon.com/guardduty/latest/ug/s3-protection.html>.

- AWS Security Hub: <https://docs.aws.amazon.com/securityhub/latest/userguide/what-is-securityhub.html>.

- AWS CloudWatch: <https://aws.amazon.com/pt/cloudwatch/>.

- AWS Secrets Manager: <https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html>.

- AWS Budgets: <https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html>.

- AWS Cost Anomaly Detection (free, ML-based spend anomaly alerts): <https://docs.aws.amazon.com/cost-management/latest/userguide/manage-ad.html>.

- AWS Well-Architected Machine Learning Lens (the AWS best-practice checklist for ML environments): <https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/machine-learning-lens.html>.

- CloudTrail log file validation (tamper-evident audit trail): <https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html>.

- **Logging CloudTrail data events** — the advanced event selectors Stage 11 step 5 scopes its trails
  with (`resources.type = AWS::S3::Object`, `resources.ARN` starts-with, `readOnly`), and the statement
  that a trail logging *only* data events carries no management copy:
  <https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-data-events-with-cloudtrail.html>.

- **AWS service events delivered via CloudTrail to EventBridge** — the rule-state table Stage 11's alarm
  design rests on: **data events are matched by rules in the default `ENABLED` state** once a trail logs
  them (the read-only restriction applies to *management* events, which need
  `ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`):
  <https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-service-event-cloudtrail.html>.

- S3 Object Lock — **governance vs. compliance mode**, the distinction that decides whether an administrator of the Log Archive account can bypass it (`s3:BypassGovernanceRetention`): <https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html>.

- Configuring S3 Object Lock (enabling it in place on an **existing** versioned bucket, and applying retention to existing objects with S3 Batch Operations): <https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-configure.html>.

- AWS Backup Vault Lock (Stage 12): <https://docs.aws.amazon.com/aws-backup/latest/devguide/vault-lock.html>.

- AWS Service Quotas: <https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html>.

- Track alerts through Amazon SNS in AWS Control Tower (the topics the landing zone creates, and the fact that the Audit account e-mail is subscribed to `aws-controltower-AggregateSecurityNotifications` by default): <https://docs.aws.amazon.com/controltower/latest/userguide/sns.html>.

- Compliance notifications by SNS in the audit account (why those topics are too noisy to carry a break-glass alarm): <https://docs.aws.amazon.com/controltower/latest/controlreference/receive-notifications.html>.

- Amazon SNS SMS subscriptions (the second channel for the break-glass alarm, Stage 1a step 5): <https://docs.aws.amazon.com/sns/latest/dg/sns-mobile-phone-number-as-subscriber.html>.

- Amazon SNS **SMS sandbox** (a new account may only send to *verified* destination numbers — the one-time step before the break-glass SMS channel works): <https://docs.aws.amazon.com/sns/latest/dg/sns-sms-sandbox.html>, and the verification procedure: <https://docs.aws.amazon.com/sns/latest/dg/sns-sms-sandbox-verifying-phone-numbers.html>.

- Supported countries for SMS with AWS End User Messaging (the **Brazil row**: short codes yes, long codes no, sender IDs no, no registration required — so nothing has to be bought or filed for the break-glass SMS): <https://docs.aws.amazon.com/sms-voice/latest/userguide/phone-numbers-sms-by-country.html>.

- AWS End User Messaging SMS pricing (the only published source for the per-country SMS message price, which is **not** in the Price List bulk API — see `docs/PRICING.md` §6): <https://aws.amazon.com/end-user-messaging/pricing/>.

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

- **Create a resource-based delegation policy** — the console path used in Stage 2 step 5.1 (**Settings** → **Delegated administrator for AWS Organizations** → **Delegate** → JSON editor → **Create policy**), the `PutResourcePolicy` + `DescribeResourcePolicy` minimum, and the reminder that the delegated account's principals still need the matching **identity-based** permissions. **Two constraints found here and nowhere else:** `NotAction` and `NotResource` are **rejected in delegation policies since 2026-06-30** as *"incompatible with the delegation allowlist model"* — so `policies/`'s exemption idiom is unavailable in this one document — and the delegable actions are a **published closed list**, which is what to check before widening the grant: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs-policy-delegate.html>.

- `aws_organizations_resource_policy` — the Terraform resource for the delegation document (`content`, `tags`; import id `rp-…`). **Read to establish that leaving the delegation out of Terraform is a decision and not a provider gap** (Lesson 8), the reasoning being `docs/GENERAL_PLAN.md`'s principle 1 plus the circularity of a slice owning its own authorization — recorded in [`POLICIES.md`](../terraform-live/identity/org-policies/POLICIES.md): <https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_resource_policy>.

- **Configuring S3 Object Lock** — enabling it on an *existing* bucket from the console or `put-object-lock-configuration`, the permanence ("you can't disable Object Lock or suspend versioning for that bucket"), and the constraint that decides which Control Tower bucket this applies to: **a bucket with Object Lock cannot be a destination for S3 server access logs** (Stage 1d step 9): <https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-configure.html>.

- **Managing GuardDuty accounts with AWS Organizations** — "For this administrator account, GuardDuty gets enabled automatically only in the current AWS Region", which is why the delegation moved out of Stage 1b step 8 to travel with the enablement — Stage 4 then, Stage 15 since the 2026-08-18 split: <https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_organizations.html>.

- **Setting GuardDuty organization auto-enable preferences** — `ALL` covers "all the accounts in an organization", including "those accounts that may have been suspended or removed" and "the delegated GuardDuty administrator account", with up to 24 h to propagate. The reading that corrected the org-configuration step's "existing members need the explicit add" (now Stage 15 step 2); Management's own coverage was later answered NO by the members page (Stage 15 verification (i)): <https://docs.aws.amazon.com/guardduty/latest/ug/set-guardduty-auto-enable-preferences.html>.

- **Designating a delegated GuardDuty administrator account** — the one-line CLI form
  (`enable-organization-admin-account --admin-account-id … --region us-west-2`), and the two properties
  that shape Stage 15 step 1: the designation is **per-Region**, and the *same* account must be the
  administrator in every Region where GuardDuty is enabled:
  <https://docs.aws.amazon.com/guardduty/latest/ug/delegated-admin-designate.html>.

- **Permissions required to designate a delegated GuardDuty administrator account** — the management
  account needs `guardduty:EnableOrganizationAdminAccount` plus the Organizations reads, and the only
  principal the service creates is the **service-linked role `AWSServiceRoleForAmazonGuardDuty`**. Read
  for Stage 15 step 5: it settles that `POLICIES.md`'s "carve out a named administration role"
  alternative has no candidate among GuardDuty's own creations:
  <https://docs.aws.amazon.com/guardduty/latest/ug/organizations_permissions.html>.

- **Adding members to the GuardDuty organization** — "There is an exception to the organization
  management account. Before the management account gets added as a GuardDuty member, it must have
  GuardDuty enabled." **This answers the first half of Stage 15 verification (i) by documentation**:
  auto-enable `ALL` does not reach Management on its own, so coverage there is a deliberate act (its
  step 2a, decision 3): <https://docs.aws.amazon.com/guardduty/latest/ug/add-member-accounts-guardduty-organization.html>.

- **Monitoring GuardDuty usage and estimating costs** — the 30-day free trial is per account and covers
  every protection plan, and usage is published **hourly to CloudWatch** under `AWS/GuardDuty`
  (`AnalyzedCount`/`AnalyzedBytes` per data source). Read for Stage 15's Cost section: the trial
  *could* price S3 Protection without paying for it — and pricing it over an empty estate is Lesson 7
  rather than a measurement, which is half of the argument for the 2026-08-18 deferral itself: at
  Stage 15 the estate is populated and the window finally measures something:
  <https://docs.aws.amazon.com/guardduty/latest/ug/monitoring_costs.html>.

- **Amazon GuardDuty FAQs** — "GuardDuty Runtime Monitoring is the only protection plan that is not
  enabled by default when you turn on GuardDuty for the first time", with the same "turned on by
  default" answer given for S3 Protection, EKS Protection and Malware Protection. **The reading that
  inverted the switch-off step (now Stage 15 step 3)**: the paid add-ons are not left off, they arrive on
  and must be switched off — and the switch is denied to Audit by `DenyGuardDutyTampering` (Stage 15
  step 0, decision 1):
  <https://aws.amazon.com/guardduty/faqs/>.

- **How EC2 instance stop and start works** — Elastic IP addresses belong to the network interface, which is listed under "resources that persist" across a stop/start (and the address bills while the instance is stopped). Answers Stage 4 verification (ii) by documentation: "re-associate on start" is unnecessary code: <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/how-ec2-instance-stop-start-works.html>.

- **Compatibility for changing the instance type** — *"AMIs are specific to the architecture of the processor, so you must select an instance type with the same processor architecture as the current instance type"*, and an incompatible choice is not a resize at all: it sends you to launch a new instance and migrate. Read 2026-08-20 when the VPN host's size became a slice parameter (`vpn.md` §S6): it is why every value that parameter admits sits in **one family**, the one the module's pinned AL2023 AMI matches. **Re-read the same day, from the other end**, when the user moved the host to amd64: the sentence that made a cross-family *resize* impossible is the same sentence that makes the architecture move a **replacement** — the module's AMI changes (`-arm64` → `-x86_64`, `wireguard-v0.3.0`), the instance is destroyed and recreated, the user data re-runs, and the admitted values become `t3.*` where they were `t4g.*`: <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/resize-limitations.html>.

- **Change the instance type for your Amazon EC2 instance** — *"You must stop your instance before you can change its instance type"*, and the public-IPv4 warning that follows it is scoped to addresses that are **not** Elastic: read in the same sitting, and together they are why switching the VPN host's size is a stop/start the Terraform provider performs in one apply — in either direction, with the `[P]` Elastic IP, and therefore every client `.conf`, untouched: <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/change-instance-type-of-ebs-backed-instance.html>.

- **AWS: Denies access to AWS based on the source IP** — the deny-by-IP example, with the note that "the policy does not deny requests made by AWS services using forward access sessions, as the original requester's IP address is preserved". That re-scopes Stage 4 step 8.1's `aws:ViaAWSService` carve-out: FAS flows survive the bare `NotIpAddress`, and the carve-out defends the on-behalf calls that are *not* FAS: <https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_aws_deny-ip.html>.

- **Quotas and limits in IAM Identity Center** — a permission set's inline policy holds at most 32,768 bytes and **10,240 non-whitespace bytes**, not increasable — the ceiling Stage 4 verification (vii) watches, because the overflow fails at provisioning rather than in `plan`: <https://docs.aws.amazon.com/singlesignon/latest/userguide/limits.html>.

- **The AL2023 core repository index for `us-west-2`, read through the repo bucket itself** — the measurement (2026-08-16) that `wireguard-tools`, `amazon-cloudwatch-agent` and `iptables-nft` all exist in the repository the 9.3 allow-list admits, so Stage 4's user data installs everything through the S3 gateway endpoint (Stage 4 steps 1.2 and 7.2; the repo's `primary.xml.gz` was grepped from the mirror the bucket names). **Note which mirror path that URL carries — `/x86_64/`** — and that it was read while the host was still arm64: the measurement was taken on the architecture the host moved *to* on 2026-08-20, so the amd64 move inherits it rather than owing a re-read. The arm64 host it was originally quoted for is the one that was, strictly, taking it on faith: <https://al2023-repos-us-west-2-de612dc2.s3.dualstack.us-west-2.amazonaws.com/core/mirrors/latest/x86_64/mirror.list>.

- **Integrating Security Hub CSPM with AWS Organizations** — designating the delegated administrator "enables Security Hub CSPM in the current AWS Region for the delegated administrator account", the same coupling as GuardDuty (Stage 1b step 8.1): <https://docs.aws.amazon.com/securityhub/latest/userguide/designate-orgs-admin-account.html>.

- **Introduction to AWS Security Hub CSPM** — read 2026-08-20, before Stage 5 step 13 ran, and it settles the name: the product that "runs checks against security controls" for FSBP/CIS/PCI/NIST is **Security Hub CSPM**, distinct from the newer **Security Hub** beside it in the console and in the CLI (`describe-hub` vs `describe-security-hub-v2`). Also the 30-day, per-account free trial on first enablement, which is why step 13 puts nothing on the bill for a month: <https://docs.aws.amazon.com/securityhub/latest/userguide/what-is-securityhub.html>.

- **Understanding central configuration in Security Hub CSPM** — the page that rewrote Stage 5 step 13. **Local configuration** (the default) auto-enables only "in *new* organization accounts in the current Region" and "doesn't apply to existing organization accounts" — so the step's original "auto-enable for existing and future accounts" was not a setting anyone could choose (verification (ix), answered NO by documentation; Lesson 36). **Central configuration** is the mechanism that does it: configuration policies associated with the root, covering existing accounts, future accounts and every OU, and the *recommended* policy is FSBP-and-nothing-else with "all existing and new FSBP controls" enabled. Also the constraint that reshaped step 13.3: a centrally managed account cannot run `BatchUpdateStandardsControlAssociations`, so disabling a control means editing the policy, not clicking in the account: <https://docs.aws.amazon.com/securityhub/latest/userguide/central-configuration-intro.html>.

- **Enabling central configuration in Security Hub CSPM** — the prerequisites and both paths. The **home Region** doubles as the finding-aggregation Region; the console workflow says "Select at least one Region to link to the home Region", which on this organization would push a configuration policy into a Region the `us-west-2` ceiling denies, while the CLI path (`update-organization-configuration --no-auto-enable --organization-configuration ConfigurationType=CENTRAL`, run **from the delegated administrator**) takes no linked-Region argument at all. That is why step 13.1a prefers CloudShell in Audit over the console. The aggregator's `NO_REGIONS` mode — "aggregates no data because no Regions are selected" — is the single-Region case: <https://docs.aws.amazon.com/securityhub/latest/userguide/start-central-configuration.html>.

- **Enabling and configuring AWS Config for Security Hub CSPM** — two things Stage 5 step 13.0 turns on. First, the failure mode of recording gaps: a control whose resource type is not recorded returns a `WARNING` finding that "doesn't actually evaluate the configuration state of the resource" — a dashboard that looks answered and is not (Lesson 13's shape as a service behaviour). Second, and the reason step 13.0 refuses the v2 product: with **both** Security Hub CSPM and Security Hub enabled, CSPM creates a service-linked recorder `AWSConfigurationRecorderForSecurityHubCSPM` and "Security Hub does not use the customer-managed configuration recorder in AWS Config" — which here is Control Tower's `aws-controltower-BaselineConfigRecorder`. The page also states that recording `AWS::Config::ResourceCompliance` is not required for the checks to work, a Stage 12 cost lever: <https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-setup-prereqs.html>.

- **Monitor resource changes with AWS Config (Control Tower)** — landing zone 3.0+ limits *global* resources to the home Region, and the only documented way to customise which resource types are recorded is the lifecycle-event solution, not a Control Tower setting (Stage 1d step 10): <https://docs.aws.amazon.com/controltower/latest/userguide/monitoring-with-config.html> and <https://aws.amazon.com/blogs/mt/customize-aws-config-resource-tracking-in-aws-control-tower-environment/>.

- **`iam-root-access-key-check` (AWS Config managed rule)** — identifier `IAM_ROOT_ACCESS_KEY_CHECK`, **trigger type Periodic, no parameters**: it evaluates on a schedule against the account rather than on a recorded configuration item, which is why it is **independent of whatever Stage 1d step 10.3 decides about the recorder's scope** — correcting D16's "enabled with the recorder scope" (Stage 1d step 10.4): <https://docs.aws.amazon.com/config/latest/developerguide/iam-root-access-key-check.html>.

- **Managing AWS Config rules across an organization** — the reason 10.4 creates the rule by hand in Management instead of deploying it as an organization Config rule from the Audit delegated administrator: AWS Config does not create the service-linked role in the management account by itself, and "if you do not have an SLR for your management account, you will not be able to deploy resources to that account from a delegated administrator account" — member accounts are unaffected (Stage 1d step 10.4): <https://docs.aws.amazon.com/config/latest/developerguide/config-rule-multi-account-deployment.html>.

- **Region deny control applied to the OU (`CT.MULTISERVICE.PV.1`)** — the *configurable*, OU-scoped Region deny, with its `AllowedRegions` / `ExemptedActions` / `ExemptedPrincipalARNs` parameters and the full default `NotAction` and principal-exemption lists in its SCP artifact. This is the control that **can** be exercised against the `Policy Test` OU first, which is what corrected Stage 1c step 7.7: <https://docs.aws.amazon.com/controltower/latest/userguide/ou-region-deny.html>.

- **Configure the Region deny control (`GRREGIONDENY`)** — the landing-zone-wide variant: enabled from *Landing zone settings → Modify settings*, applies to every registered OU at once, cannot deny the home Region, and requires that no resources already exist in the denied Regions (Stage 1c step 7.7): <https://docs.aws.amazon.com/controltower/latest/userguide/region-deny.html>.

- **Strongly recommended preventive controls (Control Tower)** — the status of `AWS-GR_RESTRICT_ROOT_USER` and `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS`, and the `ExemptAssumeRoot` parameter that carves the centralized-root `sts:AssumeRoot` path back out — set per OU, only on `AWS-GR_RESTRICT_ROOT_USER`, and it does not accept `false` (Stage 1c step 7.7): <https://docs.aws.amazon.com/controltower/latest/controlreference/strongly-recommended-preventive-controls.html>.

- **IAM Identity Center information in CloudTrail** — the three event sources that record a group-membership change: `sso-directory.amazonaws.com` (`AddMemberToGroup`/`RemoveMemberFromGroup`, console), `identitystore.amazonaws.com` (`CreateGroupMembership`/`DeleteGroupMembership`, API/Terraform) and `sso.amazonaws.com` (`CreateAccountAssignment`/`DeleteAccountAssignment`), with AWS's own recommendation to "consider both public and console API operations" (Stage 1b step 8.3): <https://docs.aws.amazon.com/singlesignon/latest/userguide/sso-info-in-cloudtrail.html>.

- **Modifications to CloudTrail event data of IAM Identity Center** — the January 2025 changes to `userName`, `principalId`, `userIdentity` type and group `displayName`. It used to be cited as the reason the Stage 1b step 8.3 filter keys on group **IDs**; since 2026-08-09 that filter **matches every membership and assignment event and keys on nothing**, and this reference is one of the three reasons why — a pattern keyed on identity-plane payload fields, name or GUID, is a pattern with a hidden expiry (`docs/plan/institutional-delta.md` carries the row for when filtering becomes necessary again): <https://aws.amazon.com/blogs/security/modifications-to-aws-cloudtrail-event-data-of-iam-identity-center/>.

- **AWS Organizations increases SCP quotas (May 2026)** — 10 SCPs per node and 10 240 characters per policy, up from 5 and 5 120; RCP quotas are not part of the same increase, which is the sizing budget Stage 1c step 7.1 now states: <https://aws.amazon.com/about-aws/whats-new/2026/05/aws-organizations-increased-scp-quotas/>.

- **Establish permissions guardrails using data perimeters** — the trusted-resources SCP shape that Stage 1c step 7.5 now uses for `aws:ResourceOrgID`: `StringNotEqualsIfExists` beside `BoolIfExists` on `aws:PrincipalIsAWSService`, so a call that does not populate the key is not denied and calls AWS makes on your behalf are not caught: <https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_data-perimeters.html> and <https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/>.

- **Notebooks in SageMaker Unified Studio** — the page that settles three things at once for the 2026-08-13 objectives: notebooks run on **JupyterLab spaces**, the default Spark runtime is **Amazon Athena for Apache Spark, which "doesn't support Virtual Private Cloud (VPC)"** with EMR Serverless / EMR / Glue as the VPC-capable alternatives and a *Network isolation* procedure for disabling it, and **notebooks do not support trusted identity propagation** — in an Identity Center domain they use *compatibility permission mode* for data access (Stage 1c step 7.6's action table; `docs/plan/open-questions.md` items 12 and 13): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/notebooks.html>.

- **Spaces in SageMaker Studio / Unified Studio** — a space is "a combination of a compute instance, storage and other runtime configurations" behind a JupyterLab or Code Editor application, created through `sagemaker:CreateSpace` / `sagemaker:CreateApp`. This is the evidence that settled **decision 1** of Stage 1c: denying the *classic* `sagemaker:CreateNotebookInstance` costs none of the `CLAUDE.md` notebook objectives, because they are a different product surface: <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-jl-user-guide-create-space.html> and <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/jupyterlab.html>.

- **The 2026-08-16 documentation pass behind the Stage 6 revision** — the pages that replaced beliefs with doc facts in [`stage-06-unified-studio.md`](plan/stages/stage-06-unified-studio.md):
  - *Network isolation in SMUS* — the required VPC-endpoint table (`datazone` included), the three-control Athena Spark disable (the SCP on `athena:StartSession`/`UpdateSession` being the only one that spares Athena SQL), and the network-conditioned deny for the domain execution role that INT-16's fallback (i) now names: <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/network-isolation.html>. **Re-read 2026-08-19 and three things were sharper than this row said** — AWS ships the deny statement verbatim (`Sid` `DenyAthenaSparkStartSession`, `Resource` `arn:aws:athena:*:*:workgroup/*`); the Tooling Athena flag applies to **new projects only**, and the third control is *"remove Amazon Athena Spark permissions from individual project IAM policies"*, i.e. a grant-shaped edit on blueprint-authored policies rather than the permissions boundary Stage 6 step 2.1 builds; and `DenyUserAccessFromUnauthorizedVPCs` carries **three** conditions, the third being `StringLike aws:userid = *:user-*`, which is what confines it to portal users and spares the catalog service on the same role. The endpoint tables are split **required** (`athena`, `datazone`(+`-fips`), `ec2`, `ec2messages`, `q`, `s3`, `sagemaker.api`, `sagemaker.runtime`, `glue`, `kms`, `secretsmanager`, `sts`, `ssm`, `ssmmessages`) and **optional** (per blueprint) — and the `q` row pairs with `com.amazonaws.us-east-1.codewhisperer`, *"available only in us-east-1"*, which a `us-west-2` VPC cannot reach through an interface endpoint at all (Stage 6 step 4.2).
  - *Manage Tooling blueprint parameters* — `sagemakerDomainNetworkType` (**default `VpcOnly`**), `lifecycleManagement` / `idleTimeoutInMinutes` / `maxIdleTimeoutInMinutes`, `maxEbsVolumeSize`, and the per-parameter **Editable** flag that turns a default into a control (Stage 6 steps 1.5, 8.1): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/manage-tooling-blueprint.html>.
  - *Supported blueprints* — the real names (Tooling, LakeHouseDatabase/`DataLake`, LakehouseCatalog, RedshiftServerless, EMRServerless, EMRonEC2, Workflows, MLExperiments, PartnerApps, Quicksight, AmazonBedrockGenerativeAI); there is no "ML experience" blueprint (corrects D26's wording): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/supported-blueprints.html>. **Re-read 2026-08-19, this time for the per-blueprint *Resources created* column, and it inverted a recommendation**: `LakehouseCatalog` *"provisions a new catalog in the Amazon SageMaker Lakehouse that is backed by Amazon Redshift Managed Storage"* — the Glue/Athena form is **`LakeHouseDatabase`/`DataLake`** (Glue databases, Lake Formation permissions, Athena workgroups), the opposite of what the name reading assumed (Stage 6 decision 4; D26's "Lakehouse Catalog in its Glue/Athena form" carried the same misreading). Also settled there: `Workflows` *provides the CloudFormation template* for the MWAA environment — the environment itself is born when a project uses the blueprint, not when it is enabled; `MLExperiments` is an OnDemand MLflow tracking server; the combined `AmazonBedrockGenerativeAI` blueprint carries seven `AmazonBedrock*` sub-blueprints (the `US-3` prefix rule). **MEASURED AGAINST THE LIVE DOMAIN 2026-08-21, and the page's names are not all the API's**: `datazone list-environment-blueprints --managed` returns **23** where the console lists **13**, and they reconcile exactly — `AmazonBedrockGenerativeAI` is a **console grouping with no API identifier**, expanding into the seven; `LakeHouseDatabase` is the API's `DataLake`; and **four are API-only, never offered by the console** (`LakehouseAdmin`, `S3Bucket`, `S3TableCatalog`, `ToolingLite`). Three names this row and the plan carried do not resolve at all — `EMRServerless`→`EmrServerless`, `EMRonEC2`→`EmrOnEc2`, `Quicksight`→`QuickSight`. The prefix rule mentioned above **was removed the same day**: it silently admitted anything AWS might add under the namespace, so `US-3` now enumerates. **Lesson 38** came out of this pair of readings — an identifier taken from prose is a claim, and the enumeration that falsifies it is one command.
  - *Associated accounts* — the association is a console flow in which DataZone creates the RAM share on the domain's behalf (no public API; 7-day invitation window), and the member account configures blueprints, the provisioning and manage-access roles and the VPC parameters (Stage 6 steps 1.3-1.4, INT-12): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/associated-accounts.html> and <https://docs.aws.amazon.com/datazone/latest/userguide/working-with-associated-accounts.html>. **Both pages re-read 2026-08-21, immediately before executing 1.3, and three things came back that the 2026-08-16 summary above does not contain.** (1) **The surface is `https://console.aws.amazon.com/datazone` on BOTH sides** — *View domains → the domain → **Account associations** tab → **Request association*** in the domain account, *View requests → **Review request** → **Accept and configure AWS association** → **Accept new permissions*** in the member — **not** the `dzd-*.sagemaker.<region>.on.aws` portal the stage step had named, and the correction landed in step 1.3 before it was run. (2) **The V1 page carries a field the V2 page never mentions: a *RAM Policy* selector**, `AWSRAMPermissionDataZonePortalReadWrite` (DataZone APIs **plus** data portal access) against `AWSRAMPermissionDataZoneDefault` (APIs only) — so the permission name the earlier summary states as a fact is one of two choices, and this design takes the **Default**. (3) **Both accept flows offer to build the environment inline** — V2's *Next steps for your domain* **Configure** buttons, V1's *DefaultDataLake/DefaultDataWarehouse* checkboxes with their *"have Amazon DataZone create and use a new IAM role"* pickers — which is Lesson 17 waiting on the happy path: the console route mints roles this repository already owns by name and skips `environment_role_permission_boundary` entirely (INT-15). The V1 page is also where the **7-day** expiry is actually stated; the V2 page states no expiry at all. **MEASURED 2026-08-21, by running the flow, and two of this row's particulars did not survive it.** There is **no invitation and no expiry**: with Stage 1d's org-wide RAM enablement the console creates the share organization-scoped and it **auto-accepts** — zero invitations in either member account — so the V1 page's 7 days is a clock that never starts and the accept flows described above are never reached. And the **RAM Policy selector does not exist in this console**; what it offers instead is *AWS Organization-only RAM share* and *IAM users can access APIs only*, producing **`AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`** — a name RAM publishes and the documentation does not. `ram list-permissions --resource-type datazone:Domain` returns six, and **neither `AWSRAMPermissionDataZoneDefault` nor `AWSRAMPermissionDataZonePortalReadWrite` is among them**: both were proper nouns taken from prose. The APIs-only choice is the design's no-portal decision, honoured under a different name.
  - *Trusted identity propagation in SMUS* — supported since 2025-09 for Athena/Redshift/Glue/EMR through the Tooling parameter `enableTrustedIdentityPropagationPermissions`; JupyterLab and Visual ETL still resolve through the project role (open question 13, Stage 6 decision 2): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/trusted-identity-propagation.html> and <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/using-project-tip.html>.
  - *Remote access to spaces* — the SMUS policy scoping `sagemaker:StartSession` by the `AmazonDataZoneProject`/`AmazonDataZoneUser` tags, the `sagemaker:RemoteAccess` condition key, the IAM-credential/12-hour residual, and the incompatibility with TIP (Stage 6 step 3.2): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/configuring-sagemaker-unified-studio-remote-access.html> and <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/network-config-remote-access.html>.
  - *BYOI in SMUS* — a custom image attaches to the Tooling-provisioned **SageMaker AI domain** in the member account, the Dockerfile specification, and the ECR same-Region requirement (Stage 6 steps 5.0-5.1, INT-01/INT-17): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/byoi-how-to.html>, <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/byoi-specifications.html> and <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-byoi-how-to-attach-to-domain.html>. **Re-read 2026-08-21, to write the build code (`images/`), and the summary above was wrong on the load-bearing half:** *"base on `jupyterlab/default`"* is the **Base URL** from the health-check section (`jupyterlab/default/api/status`, port 8888, one application always named `default`) — the required **base image** is `public.ecr.aws/sagemaker/sagemaker-distribution`, version **≥ `2.6-cpu`**, and the reason is that those images already carry the extensions without which an image will not run in SMUS at all. Three constraints the summary did not carry, each now enforced in the `Dockerfile`s: **no `ENTRYPOINT`** — the page states adding one *"will not work as expected"*, because the distribution's `_entrypoint.sh` must survive, and a custom one is a `ContainerConfig` setting; **`/opt/ml`, `/opt/.sagemakerinternal` and `/var/log/studio` are AWS's**; and the space's EBS volume mounts at **`/home/sagemaker-user`** on a path that cannot be changed (which is why anything a user must write goes there and everything baked goes read-only under `/opt`). The user/filesystem page also says `UID=1000`/`GID=100` are *supported values* and the ids are **remapped at runtime** — the live `4.4.1-cpu` image actually runs `sagemaker-user` at 57439, so the AWS sample's `NB_UID`/`NB_GID` are a convention rather than a requirement. **Measured against the public registry the same day** (anonymous Docker Registry v2 API — no IAM action, so `DenyEcrPublicEntirely` does not reach it): `4.4.1-cpu` is `sha256:9c1ea89f6ae62261de895f51fceb9f084c526829d50e21bcead175e3cfcfeb40`, `linux/amd64`, Ubuntu 24.04, micromamba at `/opt/conda`, 24 layers ≈ 4.1 GB compressed — and the repository publishes **`cpu`/`gpu` suffixes only, with no `arm64` variant**, which is what makes an Apple Silicon build an emulated one. The JupyterLab custom-images page is where the health check and the `jupyter-activity-monitor-extension` package name are actually stated: <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-byoi-specs.html> and <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-jl-admin-guide-custom-images.html>.
  - *Idle shutdown mechanics* — per-app idle settings with `MaxIdleTimeoutInMinutes` as the admin ceiling, requiring SageMaker Distribution v2+ (Stage 6 step 8.1): <https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-idle-shutdown.html> and <https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_IdleSettings.html>.
  - *`sagemaker:InstanceTypes` condition key* — listed for `CreateApp`, `CreateSpace`, `UpdateSpace` and `CreateTrainingJob`, which is what makes Stage 6 step 3's instance ceiling reach spaces as well as jobs: <https://docs.aws.amazon.com/service-authorization/latest/reference/list_sagemaker.html>.
  - *The `aws-ia` module, measured* — registry name `aws-ia/sagemaker-unified-studio/aws`, v0.2.0 (2026-07-02), providers `aws ≥ 6.51.0` / `awscc ≥ 1.89.0` / `random` / `time`; the domain is `aws_datazone_domain` with `domain_version = "V2"`, and the root **requires `vpc_id`/`subnet_ids` and enables Tooling in the domain account** — the single-account assumption Stage 6 verification (ii) is about: <https://registry.terraform.io/modules/aws-ia/sagemaker-unified-studio/aws/latest>.
  - *The associated-account half in Terraform — two resources, two spellings of one input* — the aws provider's `aws_datazone_environment_blueprint_configuration` takes `environment_blueprint_id`, an **id** its example resolves through a data source, and carries **no** `environment_role_permission_boundary`, which is why the module uses `awscc_datazone_environment_blueprint_configuration` instead (INT-15): <https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/datazone_environment_blueprint_configuration>. **Measured 2026-08-21, the day step 1.4's first apply failed twelve for twelve:** the awscc resource rides CloudFormation's contract, whose `EnvironmentBlueprintIdentifier` is the blueprint **NAME** — the awscc example passes the literal `"DefaultDataLake"`, and the CFN page's separate `EnvironmentBlueprintId` GetAtt is the resolved id — so feeding it the data-source id made the handler hunt for a blueprint *named* like an id (`Managed Environment Blueprint with <id> doesn't exist`) while `get-environment-blueprint` answered for those same ids from the same profile, and a plain-CLI `put-environment-blueprint-configuration` for `Tooling` (id, provisioning role, boundary, two-subnet regional parameters) succeeded and was deleted (Lesson 32; Lesson 30). The CFN page still says *"only `DefaultDataLake` and `DefaultDataWarehouse` are supported"* — V1-era names a V2 domain does not even carry; whether the handler takes the live roster's names is what the re-run apply measures. The live type schema (`describe-type`) marks `EnvironmentBlueprintIdentifier` createOnly + **writeOnly**, so name-passing is diff-safe — and `EnvironmentRolePermissionBoundary` writeOnly too, so boundary drift is invisible to `plan` and `./aws/studio.py` US-8 is the sentinel: <https://registry.terraform.io/providers/hashicorp/awscc/latest/docs/resources/datazone_environment_blueprint_configuration> and <https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-datazone-environmentblueprintconfiguration.html>.
  - *SMUS multi-Region IdC* (2026-04) — a domain may sit outside IdC's Region **only with an external IdP**, and TIP does not cross Regions; with the native directory the same-Region rule stands (Stage 6 step 1.1): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/manage-users-idc-based-domains.html>.
  - *Disabling the JupyterLab download UI* — the official, bypassable lifecycle-configuration mitigation open question 6 now records: <https://github.com/aws-samples/sample-disable-sagemaker-jupyterlab-download>.
  - *Account pools* — CLI-only, account-agnostic project profiles; noted for Stage 14, not adopted at N=1: <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/account-pools-create.html>.

- **Athena Spark and AWS PrivateLink (2026-04-21) — the announcement that looks like it retires Stage 6 decision 3, and does not.** Read 2026-08-19 because it *should* be checked before the deny is written. What it moves is the **client → session** path: three interface endpoints — Spark Connect (`com.amazonaws.<region>.athena.sessions`), Live UI (`athena.dashboard`) and the Spark History Server (`athena.persistent-dashboard`), on workgroups running **Apache Spark 3.5**, the version SMUS notebooks use. What it does **not** move is where the session runs: there is no `NetworkConfiguration`, no subnet and no security group anywhere in the Athena Spark API, and the SMUS network-isolation page — current after the release — still answers VPC connectivity with *"use Amazon EMR or AWS Glue instead"*. The executor therefore stays outside the customer VPC, which is the whole of open question 12. **Two details on the feature's own page argue for the deny rather than against it:** *"VPC endpoint policies are not supported on Athena Spark Connect, Live UI, or Persistent UI endpoints"* (the documented workaround is a policy on the Athena **API** endpoint governing `GetSessionEndpoint`/`GetResourceDashboard`), and a session URL generated inside a VPC *"can be accessed from that same VPC or from the public internet, but not from a different VPC"* — by design, for the open-the-dashboard-locally workflow. The **negative control** for the compute claim is the considerations-and-limitations page, which mentions no VPC, subnet or network configuration at any release version: <https://aws.amazon.com/about-aws/whats-new/2026/04/amazon-athena-spark-aws-privatelink/>, <https://docs.aws.amazon.com/athena/latest/ug/athena-spark-vpc-endpoint.html> and <https://docs.aws.amazon.com/athena/latest/ug/notebooks-spark-considerations-and-limitations.html>.

- **The 2026-08-19 Spark-runtime block behind Stage 6 decision 1's correction** — the pages that corrected
  the reopening's number and added the FGAC counter-axis (the decision row carries the consequences):
  - *Spark Compute (Spark Connect)* — the notebook's per-engine limitations, identical for AWS Glue, EMR
    Serverless and EMR on EC2: *"Fine-grained access control (FGAC) is not supported. Only full-table
    access is available"*, and TIP idem; EMR Serverless on this path needs `emr-7.13.0`+ with Interactive
    Sessions and **compatibility** mode, and the SMUS-provisioned pre-initialized capacity is 1 driver +
    3 executors, released after 15 min idle:
    <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/notebooks-spark-connect.html>.
  - *The compute-connection permission modes* — `project.spark.fineGrained` (rows/columns via SageMaker
    Catalog subscriptions) versus `project.spark.compatibility` (full-table): the EMR Serverless *Add
    compute* dialog offers both, Glue's `fineGrained` is documented for **Visual ETL flows**, and the
    notebook connects to an EMR-S compute of either mode through the PySpark connection type — the
    asymmetry decision 1's second reading measures:
    <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/adding-new-emr-serverless.html>,
    <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/compute-permissions-mode-glue.html> and
    <https://docs.aws.amazon.com/next-generation-sagemaker/latest/userguide/emr-serverless.html>.
  - *EMR Serverless interactive workloads* — the idle tail decision 1's cost side needed: a started
    interactive application maintains **one pre-initialized kernel worker (4 vCPU/16 GB)** even with no
    pre-initialized capacity configured, `autoStopConfig` defaults to 30 min idle, the **kernel idle
    timeout is 60 min and cannot be modified**, LF-enabled workloads want ≥ 28 vCPU of quota, and
    `spark.emr-serverless.lakeformation.enabled` is the LF switch:
    <https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/interactive-workloads.html>.
  - *AWS Glue pricing* — the session default the corrected row quotes: *"An Interactive Session has 5 DPU
    by default"* (× USD 0.44/DPU-h in `us-west-2` ≈ USD 2.20/h while open, billed per second):
    <https://aws.amazon.com/glue/pricing/>.

- **Remote access to SageMaker spaces from a local IDE** — the `sagemaker:StartSession` API behind "connect your local VS Code to a Unified Studio space", the three connection methods (deep link, AWS Toolkit, SSH), and AWS's own recommendation to scope `StartSession` by tag to a user's *own* private applications. It is the action that matches neither `sagemaker:Create*` nor `datazone:*`, which is why Stage 1c step 7.6 names it explicitly and why `docs/plan/open-questions.md` item 14 treats it as an egress channel: <https://docs.aws.amazon.com/sagemaker/latest/dg/remote-access.html> and <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/local-ide-support.html>.

- **Workflows in SageMaker Unified Studio** — the Workflows tool is **Amazon MWAA**, in both a *serverless* and a *provisioned* form, and existing MWAA environments can be connected to a project. It confirms rather than changes D7/D28: the `CLAUDE.md` "workflows" feature and Stage 10's orchestration comparison are the same surface (`docs/plan/open-questions.md` item 15): <https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/workflow-orchestration.html>.

- **AWS Control Tower RCP controls — the artifacts of the RCP-based controls, and `CT.STS.PV.1` in particular.** The page that diagnosed the 2026-08-14 SSO lockout and now sets the scope of `EnforceOrgIdentitiesOnRoleAssumption`: AWS's own trusted-identities control for STS names **only `sts:AssumeRole` and `sts:SetContext`**, and states why the other four are out of scope — *"the respective STS operations do not use AWS security credentials, and therefore do not include the `aws:PrincipalOrgID` condition key value in the request context"*, with `sts:SetSourceIdentity` and `sts:TagSession` excluded as well so that `AssumeRoleWithSAML` and `AssumeRoleWithWebIdentity` are not denied. The page is also the reference shape for the other five statements of the RCP — `CT.S3.PV.4`, `CT.SQS.PV.1`, `CT.KMS.PV.7` and `CT.SECRETSMANAGER.PV.1` are the same `BoolIfExists` + `StringNotEqualsIfExists` pair this document already used — and it carries the `ExemptedPrincipalArns` parameter that is the supported way to add a carve-out (Stage 1c step 7.8): <https://docs.aws.amazon.com/controltower/latest/controlreference/list-of-rcp-controls.html>.

- **Restrictions on SSM Parameter Store parameter names** — the rule Stage 2's Validation hit at
  `PutParameter`: a parameter name **can't be prefixed with `aws` or `ssm`, case-insensitive**, and the
  refusal arrives as `AccessDeniedException: No access to reserved parameter name`, which reads like a
  policy problem and is a naming one. This project's `awsds` prefix begins with `aws`, so Parameter Store is
  the one service where the convention of `docs/plan/conventions.md` cannot be used verbatim (Stage 2, the
  Validation; the rule is now in that file's naming section):
  <https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-parameter-name-constraints.html>.

- **`aws_organizations_organizational_unit_descendant_organizational_units` (Terraform AWS provider)** — the
  data source Stage 2 verification (iv) is about: given a parent, it returns organizational units **at any
  depth**, unlike `aws_organizations_organizational_units`, which returns one level of children. That is
  what makes `make check-ou` see `Sandboxes` at depth 2 under `Interactive` (D23), and it was confirmed
  against the pinned provider (aws 6.60.0) rather than taken from the page:
  <https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/organizations_organizational_unit_descendant_organizational_units>.

- **GitLab deployment approvals are Premium** — the tier line behind both Stage 8 gates' CE fallback
  (Lesson 12; Stage 7 verification (iv) reads the running instance, this page says what to expect):
  approvals attach to *protected environments*, approver groups must be invited to the project, and an
  approved job still has to be run manually (Stage 8 steps 1.5/3.5):
  <https://docs.gitlab.com/ci/environments/deployment_approvals/>.

- **GitLab manual jobs — who may run one, and when it blocks** — the two facts Stage 8's CE gate shape
  stands on: *"to run a manual job, you must have permission to merge to the assigned branch"*, and
  `when: manual` **outside** `rules:` defaults `allow_failure: true` (an optional job that gates nothing)
  while **inside** `rules:` it defaults `false` and stops the pipeline (Stage 8 steps 1.5/3.5):
  <https://docs.gitlab.com/ci/jobs/job_control/>.

- **GitLab Dependency Scanning is Ultimate** — not available to this CE instance, so Stage 8's dependency
  gate is `pip-audit` in an ordinary job rather than the built-in analyzer (Lesson 12 — a tier limit
  reaching a control, found before the stage rather than during it; Stage 8 step 5.2):
  <https://docs.gitlab.com/user/application_security/dependency_scanning/>.

- **GitLab pipeline Secret Detection is Free** — the one built-in scanner the CE instance does get, as a
  template include (`Jobs/Secret-Detection.gitlab-ci.yml`); the dashboards above it are Ultimate and are
  not pretended (Stage 8 step 5.3):
  <https://docs.gitlab.com/user/application_security/secret_detection/pipeline/>.

- **GitLab protected runners are Free** — a runner marked *Protected* runs only jobs on protected
  branches/tags, in every tier, and a project runner is scoped to the projects it is registered to. This
  pair is what makes Stage 8's deploy runner enforceable on CE: an ordinary CI job cannot schedule onto
  the deploy credential (Stage 8 step 4.3):
  <https://docs.gitlab.com/ci/runners/configure_runners/>.

- **ECR basic scanning** — free, OS packages only (the language-package half is Stage 8's `pip-audit`),
  scan-on-push per repository filter, findings via `DescribeImageScanFindings` — and **one scan per image
  per 24 hours**, which is why Stage 8's gate reads the push's own scan and never triggers another
  (Stage 8 step 1.4; Stage 7 decision 2 priced the enhanced alternative):
  <https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning-basic.html>.

- **`pip-audit`** — PyPA's dependency auditor, the open tool carrying Stage 8's dependency gate after the
  tier finding above; consumes a requirements export (`uv export --format requirements-txt`) and queries
  the OSV/PyPI advisory databases (Stage 8 step 5.2): <https://pypi.org/project/pip-audit/>.

- **ECR encryption at rest — who decrypts a pull.** The page that deleted half of Stage 9's old step 7:
  ECR creates **two grants on the repository's KMS key for itself** at repository creation, makes the
  `Decrypt` call on pulls on the caller's behalf, and the KMS permissions it documents
  (`kms:CreateGrant`, `RetireGrant`, `DescribeKey`) belong to the principal *creating or deleting the
  repository* — a pulling principal, cross-account included, needs the repository policy and no
  `kms:Decrypt` (Stage 9 step 7.3 records the non-grant so nobody "fixes" the absence):
  <https://docs.aws.amazon.com/AmazonECR/latest/userguide/encryption-at-rest.html>.

- **Deploying a model version from a different account** — the reference shape for Stage 9 step 3 and
  its vend amendment (4.6): cross-account deployment needs **three resource policies** — on the model
  package group, on the ECR repository of the inference image, and on the S3 (and KMS) of the model
  artifacts (INT-07's registry half; INT-04):
  <https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry-deploy-xaccount.html>.

- **`PutModelPackageGroupPolicy`** — the resource policy on a model package group (≤ 20 480 bytes), the
  API behind D28 item 6's "written here, not improvised in Stage 10"; Terraform exposes it as
  `aws_sagemaker_model_package_group_policy` (Stage 9 step 3.2):
  <https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_PutModelPackageGroupPolicy.html> and
  <https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_model_package_group_policy>.

- **Athena workgroups — override client-side settings** — the documented behaviour Stage 9's workgroup
  boundary stands on: with the override on, *"Athena uses the workgroup's settings for all queries that
  run in the workgroup, including the settings for query results location, expected bucket owner,
  encryption, and control of objects written"*, and a query that asks for its own location *runs, with
  the workgroup's settings used*. One location per workgroup — which is why the "per-principal result
  prefix" was rewritten into an enforced results zone (Stage 9 steps 1.2/5.4, verification (vi)):
  <https://docs.aws.amazon.com/athena/latest/ug/workgroups-settings-override.html>.

- **Lake Formation cross-account data sharing** — the mechanism of Stage 9's producer path, and the
  reason the grant is two steps: grants go to external accounts, organizations or OUs (named resources
  or LF-TBAC, version 3+ for org/OU grants); **a grantee in the same organization sees the share
  immediately, with no invitation to accept**; integrated services (Athena) require **resource links**
  on the consumer side; and the consumer's own admin regrants received permissions to local principals
  (Stage 9 steps 2.1-2.3, `DT-6`'s pending-invitation check):
  <https://docs.aws.amazon.com/lake-formation/latest/dg/cross-account-permissions.html>.

- **CloudWatch agent configuration file — the `logs` section** — every field of the config the Stage 4
  WireGuard host writes in its user data was read here rather than remembered: `agent.run_as_user`
  (optional, root when absent), and `logs.logs_collected.files.collect_list[]` with `file_path`,
  `log_group_name`, `log_stream_name` — where `{instance_id}`, `{hostname}`, `{local_hostname}` and
  `{ip_address}` are the substitutions allowed in the stream name — and `timezone`, whose only valid
  values are `UTC` and `Local`. It also names the diagnostic the first boot needs: on start the agent
  copies each configuration into `…/etc/amazon-cloudwatch-agent.d/` prefixed `file_` for a local source
  and `ssm_` for a Parameter Store one, so the prefix says where the running configuration came from:
  <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Agent-Configuration-File-Details.html>.
  **What this page does *not* cover, and it is recorded as unverified rather than assumed:** the
  `amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:…` invocation itself, whose page did
  not render on three fetch attempts (2026-08-16). The user data therefore reports that command's exit
  status and follows it with `-a status`, so the first boot answers it.

- **AWS Price List bulk API — the Amazon Bedrock offer files, `us-west-2` and `sa-east-1`** (read
  2026-08-21, both published `2026-08-20`): the measured source of `docs/PRICING.md` §5's Bedrock rows,
  owed before the Stage 6 step 1.4 apply because decision 5 put `AmazonBedrockGenerativeAI` in
  category 1 with the cell empty. Two readings came out of the files themselves rather than out of a
  pricing page: **the `us-west-2` file carries no `output-tokens` usagetype for any Claude model** (the
  current models are reached through cross-region inference profiles, whose SKUs publish under the
  profile's home region), and **the `sa-east-1` file carries no Claude and no Nova model at all** — so
  §9's "what moving to São Paulo would change" is, for Bedrock, a change of *model* rather than of
  price. The endpoint needs no credentials:
  <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/us-west-2/index.json>.

- **KMS pricing and key rotation — the unit that is billed is a key VERSION, not a key** (read 2026-08-21,
  from the Stage 6 plan review). The bulk API prices SKU `us-west-2-KMS-Keys` as *"$1 per customer managed
  KMS key **version**"*, and the rotation page is what turns that wording into a multi-year number: a
  rotation-enabled CMK bills **1 version in its first year, 2 after its first rotation, 3 after its second,
  and is capped there**. Every CMK in this design sets `enable_key_rotation = true` with no
  `rotation_period_in_days` — the 365-day default, measured live as `True 365` on every key the same day —
  so `docs/PRICING.md` §2's count cell is a **year-one** figure and `docs/plan/cost-model.md`'s Floor row
  is where the consequence is carried. **Recorded as a rule rather than as an API rate**, so §0's claim
  that every number in that file came from the bulk API stays exactly true:
  <https://aws.amazon.com/kms/pricing/> and
  <https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html>.

- **`uv` in the `base` image — the five sources behind its layer, two of which overturned the obvious
  implementation** (read 2026-08-21, to answer *"install the latest uv"*). **The latest is `0.12.5`,
  published 2026-08-14** — the same version this repository's own tooling runs on (`CLAUDE.md`), which
  is a coincidence worth not mistaking for a constraint:
  <https://github.com/astral-sh/uv/releases/tag/0.12.5>. **The first overturn is that the image was
  never without uv**: the distribution's own resolved environment — the `@EXPLICIT` list the `4.3.0-cpu`
  tag is built from — pins `uv-0.11.28` from conda-forge at line 913, so this is a version **move**
  inside an existing package and not an install, and a second binary under `/opt` would have left two
  `uv` whose answers depend on which PATH asks (Lesson 33):
  <https://github.com/aws/sagemaker-distribution/blob/main/build_artifacts/v4/v4.3/v4.3.0/cpu.env.out>.
  conda-forge publishes `0.12.5` for `linux-64` with dependencies `__glibc >=2.17`, `libgcc >=15` and
  `libstdcxx >=15`, all satisfied at 15.2.0 in this image, so the move should cost nothing else:
  <https://anaconda.org/conda-forge/uv>. **The second overturn is `--freeze-installed`, which cannot
  express what it looks like it expresses**: `create_install_request` emits a `Freeze` job for *every*
  package in the prefix with **no exemption for the specs on the command line**, so the flag would have
  frozen `uv` itself — an unsolvable request or a silent no-op, indistinguishable afterwards from
  protection. The guarantee became a before/after reading of `$MAMBA_ROOT_PREFIX/conda-meta` instead:
  <https://github.com/mamba-org/mamba/blob/main/libmamba/src/api/install.cpp>. Two readings from uv's
  own source close the layer: `system_config_file` tries `XDG_CONFIG_DIRS` and falls back to
  **`/etc/uv/uv.toml`**, which is why the CodeArtifact default is written there to be *discovered*
  rather than forced through `UV_CONFIG_FILE` (`--config-file` **replaces** discovery and would silence
  a data scientist's own project config); and `uv-static`'s `EnvVars` confirms `UV_SYSTEM_CERTS` and
  `UV_PYTHON_DOWNLOADS` while containing **no `UV_VERSION`**, which is what makes the build argument of
  that name safe: <https://github.com/astral-sh/uv/blob/0.12.5/crates/uv-dirs/src/lib.rs> and
  <https://github.com/astral-sh/uv/blob/0.12.5/crates/uv-static/src/env_vars.rs>. **Astral's static
  binary was measured and not used** — `uv-x86_64-unknown-linux-gnu.tar.gz` at
  `sha256:68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2`, recorded here so the
  rejected branch stays legible rather than looking unexamined.
