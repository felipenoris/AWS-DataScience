# Glossary

Every acronym used in `GENERAL_PLAN.md`, plus the notation the plan relies on and the IAM condition keys it
quotes without expanding. Grouped by area rather than alphabetically, because the grouping is itself part of
the explanation.

Where an expansion is historical and no longer used by AWS, it is marked as such — several AWS service names
are now officially just the acronym.

---

## Notation used by this project

| Symbol | Meaning |
|---|---|
| `[P]` | **Persistent** layer. Resources created once and never destroyed, because they cost nothing (or nearly nothing) at rest, or are too slow to rebuild. See `plan/conventions.md` §5.1. |
| `[D]` | **Dormant** layer. Resources kept but powered off between sessions — stateful services where rebuilding is riskier than paying the idle cost. `make down` stops them; `make up` starts them. |
| `[E]` | **Ephemeral** layer. Resources destroyed at the end of every session: everything metered by the hour and rebuildable in minutes. |
| `D1` … `D31` | Numbered key decisions. **One file each** in `plan/decisions/`, with a one-line summary per decision in `plan/decisions/INDEX.md`. Referenced by ID from the stages that consume them. |
| **Sandbox / Development / Staging / Production** | The four environments, one AWS account each. Sandbox is experimentation (the unit of work is a notebook); Development is where pipelines are engineered (the unit of work is a repository); Staging and Production are *deployment targets* that only a pipeline writes to. Promotion runs Development → Staging → Production; Sandbox feeds Development through git. See `README.md`, "Three distinctions the layout is built on". |
| **Data Governance** | The account that owns the *state* of data: the governed lake, its catalog, Lake Formation and the classification scheme. No compute, no interactive sign-in; every environment reaches it through Lake Formation cross-account shares. |
| `INT-nn` | Numbered cross-account integrations that must be proven, each with a fallback: `plan/integrations.md`. Replaces the old "§4.4 row *n*" references, which renumbered whenever a row was inserted. |
| `§` | A section of the plan as it was when it lived in one file. The numbers are kept **inside** the `plan/` files as historical anchors (e.g. `plan/architecture.md` §4.2 is the data perimeter), but the address of anything is its file plus its stable ID — `D26`, `INT-11`, `Stage 1b step 7`. |

---

## AWS Organizations, governance and identity

| Acronym | Expansion | What it means here |
|---|---|---|
| **OU** | Organizational Unit | A folder of AWS accounts inside an Organization. Policies attach to an OU or to an account — never to a tag. The account is the isolation boundary; the OU is the *policy* boundary (D23), and each OU here is named for the policy set it carries: `Security`, `Interactive` (Sandbox + Development — interactive compute allowed), `Data` (Data Governance — no *user* compute; two named carve-outs, the DataZone control plane and the catalog-maintenance role, D26/D27), `Workloads` (Staging + Production — no interactive compute, no human control plane); and `Policy Test`, which carries **no** policy set of its own — it is where a *candidate* SCP or RCP is attached and exercised against the disposable `Policy Canary` account before it reaches anything real (D29). **The name collision this avoids:** the industry calls that last one a *Policy Staging OU*, which sits confusingly next to the `Staging` **account** in the `Workloads` OU. This project uses `Policy Test` / `Policy Canary` so that the word `Staging` names exactly one thing. |
| **Policy Canary** | — | The disposable account (D29), alone in the `Policy Test` OU, deliberately empty: no VPC, no data, no Terraform slice, no state bucket. It exists because an SCP is a permission *ceiling* evaluated only when a principal makes a call — so an empty policy-staging OU tests nothing, and the account inside it is what turns the OU into a test. Holds one thing: an administrator principal, since a deny exercised by a principal that lacked the permission anyway proves nothing about a ceiling. |
| **SCP** | Service Control Policy | A maximum-permission ceiling attached to an OU or account, evaluated on the **identity** side. It cannot grant anything; it only removes. Applies to *every* principal in the account including administrators — but **never to the Management account**, which is what makes the D16 break-glass path work. Used here to deny leaving the organization, deny disabling CloudTrail, restrict regions, and deny writes to S3 outside the organization. |
| **`awsds-scp-recovery`** | — | **Not built — the name survives only in the record of a reverted decision.** D30 proposed one role per governed account, exempt by an explicit `ArnNotEquals` condition from every `Deny` this project writes; it was adopted and then reverted the same day, so **this design has no standing SCP exemption**. The recovery path is the Management account root (D16), and a bad policy is caught before attachment by the `Policy Canary` battery (D29). Two writing rules outlived the decision and apply to the per-function carve-outs that do exist (D26's `datazone:*`, D27's catalog-maintenance role): never a wildcard account ID in an ARN condition (`arn:aws:iam::*:role/…` exempts a role of that name in *any* account), and any condition repeated across policies is generated rather than typed — which is why the SCPs live in code. |
| **RCP** | Resource Control Policy | The mirror image of an SCP, evaluated on the **resource** side. Sets a maximum permission on resources (S3, STS, KMS, SQS, Secrets Manager) regardless of what any account-level policy allows. The piece that stops principals outside the organization touching your data. |
| **IAM** | Identity and Access Management | AWS's permission system: users, roles, policies. This project uses no IAM Users — humans get temporary credentials by assuming roles through SSO. |
| **SSO** | Single Sign-On | One login for many accounts. Here it means AWS IAM Identity Center (the service formerly called AWS SSO). |
| **IdP** | Identity Provider | The system that authenticates a person (Entra ID, Okta, or Identity Center itself). |
| **SAML** | Security Assertion Markup Language | The XML-based protocol that lets an external IdP authenticate a user into an application. Used to log into GitLab with Identity Center credentials. |
| **SCIM** | System for Cross-domain Identity Management | The protocol that *provisions and deprovisions* users and groups from an IdP, as opposed to merely authenticating them. Named in `plan/institutional-delta.md` as what an institution adds on top of SAML. |
| **OIDC** | OpenID Connect | An identity layer over OAuth 2.0. In CI/CD it lets a pipeline job prove who it is to AWS with a short-lived token instead of a stored access key. Blocked in this project's GitLab because validating the token requires AWS to reach the issuer over the public internet (D8, D14). |
| **JWKS** | JSON Web Key Set | The public keys an OIDC issuer publishes so a verifier can validate its tokens. AWS fetches this over the public internet, which is exactly why a VPN-only GitLab cannot use OIDC federation. |
| **MFA** | Multi-Factor Authentication | A second proof of identity beyond the password. Mandatory on every user here, and on the break-glass path (D16). |
| **AFT** | Account Factory for Terraform | AWS's tooling for provisioning Control Tower accounts from code. Deliberately not used: this handful of accounts, created once, by hand, does not repay the setup (`plan/institutional-delta.md`). |
| **SRA** | (AWS) Security Reference Architecture | AWS's published reference for how to lay out security services across a multi-account organization. |

## Networking

| Acronym | Expansion | What it means here |
|---|---|---|
| **VPC** | Virtual Private Cloud | A private, isolated network inside an AWS account. One per account in this project, non-overlapping so they can be peered. |
| **AZ** | Availability Zone | A physically separate datacenter within a region. Note that AZ *names* (`us-west-2a`) map to different physical AZs in different accounts; the AZ *ID* (`usw2-az1`) is the stable identifier. This distinction has a bill attached (`plan/open-questions.md` item 3). |
| **CIDR** | Classless Inter-Domain Routing | The `10.20.0.0/16` notation for an address range. |
| **IGW** | Internet Gateway | The VPC component that allows traffic to and from the public internet. |
| **NAT** | Network Address Translation | Rewriting source addresses so many private hosts share one public address. A **NAT Gateway** lets private subnets reach the internet without being reachable from it — and is the single largest hourly cost in this project, which is why egress design B removes it. |
| **NACL** | Network Access Control List | A stateless packet filter at the subnet level, below security groups. |
| **SG** | Security Group | A stateful firewall attached to a resource. Can reference *another security group* as its source, which is how this project avoids hardcoding addresses. |
| **EIP** | Elastic IP | A public IPv4 address you own rather than one assigned at boot. Billed hourly whether attached or not. Kept in the `[P]` layer so the VPN endpoint address survives a rebuild. |
| **IP / IPv4** | Internet Protocol (version 4) | — |
| **TCP / UDP** | Transmission Control Protocol / User Datagram Protocol | WireGuard uses UDP/51820; NFS uses TCP/2049. |
| **DNS** | Domain Name System | Name-to-address resolution. **Split-horizon DNS** means the same name resolves to a public address from outside and a private one from inside — the mechanism that lets a public TLS certificate serve an internal-only endpoint (D15). |
| **TLS** | Transport Layer Security | The encryption under HTTPS. |
| **HTTP / HTTPS** | HyperText Transfer Protocol (Secure) | — |
| **SSH** | Secure Shell | Remote shell access. Deliberately not exposed here: shell access goes through SSM Session Manager instead of port 22. |
| **ALB** | Application Load Balancer | An HTTP-aware load balancer. Cannot be stopped — only created or destroyed — which is why it lives in the `[E]` layer. |
| **LCU** | Load Balancer Capacity Unit | The usage-based half of an ALB's bill, on top of its hourly charge. |
| **WAN** | Wide Area Network | In "Cloud WAN", AWS's managed multi-region network fabric (`plan/institutional-delta.md`). |
| **IPAM** | IP Address Manager | AWS's service for allocating CIDR ranges across an organization so they do not collide (`plan/institutional-delta.md`). |
| **VPN** | Virtual Private Network | The encrypted tunnel that is the only human entry point to the private network. WireGuard here (D4). |

## Storage, data and analytics

| Acronym | Expansion | What it means here |
|---|---|---|
| **S3** | Simple Storage Service | Object storage. The source of truth for all data in this project. |
| **EBS** | Elastic Block Store | Network-attached block storage for EC2 instances. Billed even while the instance is stopped — the idle cost of the `[D]` layer. |
| **EFS** | Elastic File System | Managed NFS. The shared filesystem between users and SageMaker. |
| **FSx** | (Amazon FSx) | A family of managed file systems. FSx for Lustre is named in `plan/institutional-delta.md` as what an institution uses for training throughput. |
| **NFS / NFSv4** | Network File System (version 4) | The protocol for mounting a remote filesystem as if it were local. |
| **IA** | Infrequent Access | A cheaper storage class for data that is rarely read. EFS and S3 both have one; the lifecycle transition to IA is what makes persistent EFS cost cents. |
| **POSIX** | Portable Operating System Interface | The Unix filesystem semantics EFS implements — including numeric **UID**/**GID** (user/group identifiers), which have no connection to SSO identities. That gap is why "who wrote this file" is unanswerable in this design. |
| **CMK** | Customer Managed Key | A KMS key you create and control, as opposed to an AWS-managed one. ~USD 1/month each. |
| **SSE** | Server-Side Encryption | Encryption applied by the storage service. `SSE-KMS` means encrypted with a KMS key. |
| **KMS** | Key Management Service | AWS's key store. Charges per key **and per request** — which is why S3 Bucket Keys matter (`plan/cost-model.md`). |
| **ETL** | Extract, Transform, Load | The classic data pipeline shape. The sample application in `CLAUDE.md` is `app-etl`. |
| **LF** | Lake Formation | AWS's permission layer over the Glue Data Catalog. **LF-Tags** are the labels its grants are expressed against, allowing "grant on everything tagged `restricted`" instead of table-by-table. |
| **DLP** | Data Loss Prevention | Preventing sensitive data from leaving. In this project it is not one product but four problems, each with its own control (D6). |
| **EMR** | (originally Elastic MapReduce) | AWS's managed Hadoop/Spark service. Now officially just "Amazon EMR". Relevant here only as one of the Lake Formation-aware engines. |
| **RDS** | Relational Database Service | Managed relational databases. Only appears in the Stage 13 experiment. |
| **OPTIMIZE / VACUUM** | — | Iceberg table maintenance operations: `OPTIMIZE` compacts small files, `VACUUM` expires old snapshots. Not acronyms, but jargon that decides whether a table degrades quietly. |

## Compute and containers

| Acronym | Expansion | What it means here |
|---|---|---|
| **EC2** | Elastic Compute Cloud | Virtual machines. Used for WireGuard, GitLab and the CI runners. |
| **ECS** | Elastic Container Service | AWS's container orchestrator. |
| **ECR** | Elastic Container Registry | AWS's private Docker registry. **Pull-through cache** makes it mirror a public registry on demand. |
| **AMI** | Amazon Machine Image | The disk image an EC2 instance boots from. Region-scoped, which is why the plan resolves them through SSM parameters rather than pasting IDs. |
| **ARM** | (the instruction set architecture) | The CPU family AWS Graviton implements. `t4g` instances are ARM and roughly 20% cheaper than their x86 equivalents for the same memory. |
| **GPU** | Graphics Processing Unit | The expensive kind of instance. `sagemaker:InstanceTypes` conditions exist to stop one being started by accident. |
| **IMDSv2** | Instance Metadata Service version 2 | The session-authenticated version of the endpoint an EC2 instance uses to fetch its own credentials. Enforcing it org-wide closes a well-known credential-theft path. |
| **BYOI** | Bring Your Own Image | Running a custom container image in SageMaker Studio instead of an AWS-provided one. |
| **CE** | Community Edition | The free, self-hostable edition of GitLab. Some features named in the plan (SAML group sync) are Premium-only. |
| **LFS** | Large File Storage | The Git extension for versioning large binaries outside the repository proper. |

## CI/CD, MLOps and operations

| Acronym | Expansion | What it means here |
|---|---|---|
| **CI / CD** | Continuous Integration / Continuous Delivery | Automated build-and-test, and automated deployment. This project builds three kinds of pipeline (Stage 8). |
| **MLOps** | Machine Learning Operations | The practice of getting models from a notebook into production reliably. AWS's multi-account MLOps references are what D17's and D20's account placement follow; the three used are linked and summarised in `README.md`. |
| **Deployment target** | — | An account that only a pipeline writes to — Staging and Production here. Not an acronym, but the load-bearing term in the AWS references: a deployment target has no IDE, no interactive compute, and no human with control-plane permissions. |
| **Promotion** | — | Moving a versioned artifact from one environment to the next through the pipeline, with a gate in between. In this project the chain is Development → Staging → Production, and the four artifacts that travel are listed in D17. |
| **Graduation** | — | The step *before* promotion: notebook logic from Sandbox is rewritten into a Development repository, reviewed and committed (D21). It is git, not a pipeline — the rewrite is the quality gate, and there is deliberately no automated path that lifts a notebook out of Sandbox. |
| **Producer path** | — | The Lake Formation governed-write grant held by Production's job execution role (D22): production ETL writing curated tables into the Data Governance lake, cross-account, through LF-aware engines. The only way governed data is ever written. |
| **Ingestion drop-box** | — | A dated S3 prefix in the Data Governance account that the Interactive-OU roles may `PutObject` into and nothing else — no read, no list, no delete: a letterbox, not a shared folder (D18). The pickup runs in Production on the producer path (D25), which is what stops it from becoming the general-purpose exchange bucket between accounts that the plan deliberately refuses to build. |
| **MWAA** | Managed Workflows for Apache Airflow | AWS's hosted Airflow. Named explicitly in `CLAUDE.md`. The classic form charges an **environment fee per hour of existence** whether or not a DAG runs (~USD 212/month for `mw1.micro`, ~USD 358/month for `mw1.small` in `us-west-2`); **MWAA Serverless** (November 2025) charges per task-hour instead — YAML workflow definitions, one IAM role per workflow, no Airflow UI, provisioned in Terraform as `awscc_mwaaserverless_workflow` (D28). D7 builds it as alternative **A**, against a native EventBridge Scheduler + Step Functions + Lambda stack as alternative **B**. |
| **Unified Studio** | SageMaker Unified Studio | The AWS-consolidated development portal: one **DataZone V2 domain** with projects, blueprints and SageMaker Catalog on top of Glue + Lake Formation. Adopted by D26 — one domain registered in **Data Governance** (a registry, not a runtime), project blueprints provisioning compute into Sandbox and Development; deployment targets are never associated. In Terraform via the `aws-ia/terraform-aws-sagemaker-unified-studio` module (domain via `aws`, projects/blueprints via `awscc`). A `aws_datazone_domain` without `domain_version = "V2"` is plain DataZone, **not** Unified Studio — the default is V1. |
| **Blueprint** | Environment blueprint (DataZone) | The template a Unified Studio project profile composes to provision real resources into an associated account. This plan enables three and no others: Tooling, **Lakehouse in its Glue/Athena form** (never the Redshift Serverless variant, D26/D12) and ML. The cost of Unified Studio is what blueprints provision, not the domain. |
| **Deployment Manager** | — | The SSO persona that approves promotion of an artifact along Development → Staging → Production, and the time-boxed elevated role used to debug a failed production job. Acts in GitLab; group `deployment-managers`; read-only in the four lifecycle accounts and **absent from Data Governance**. Cannot grant access to data. |
| **Governance Manager** | — | The SSO persona that approves data subscriptions and every other access to data, and owns the classification scheme and LF-Tag assignments. Domain owner of the Unified Studio domain; group `governance-managers`; present **only** in Data Governance. Sees the catalog, not the rows — an approver who can already read everything is not exercising a control. Split from the single `Manager` persona on 2026-08-08, together with [Deployment Manager]. |
| **CodeConnections** | AWS CodeConnections | The service that attaches an external git repository (GitHub, GitLab, self-managed GitLab via a **host**) to AWS services — the path by which a Unified Studio project uses the self-hosted GitLab (`INT-13`, the one integration with no convenience-preserving fallback). |
| **DR** | Disaster Recovery | Restoring after something is destroyed, as opposed to routine operation. |
| **RTO / RPO** | Recovery Time / Recovery Point Objective | How long recovery may take, and how much data may be lost. Stage 12 requires stating both as numbers rather than assuming them. |
| **FinOps** | Financial Operations | Treating cloud cost as an engineering concern with owners and feedback loops. |
| **SigV4** | Signature Version 4 | AWS's request-signing algorithm. Relevant because signing a presigned URL is a purely **local** SigV4 operation — it makes no API call and therefore appears nowhere in CloudTrail (Stage 11). |
| **PyPI** | Python Package Index | The public Python package repository. |
| **CRAN** | Comprehensive R Archive Network | The public R package repository. Not supported by CodeArtifact, which is one of the constraints shaping egress design B (`plan/architecture.md` §4.3). |
| **UI** | User Interface | — |
| **OS** | Operating System | — |
| **HR** | Human Resources | Only in `plan/institutional-delta.md`, describing group membership driven by an HR system. |

## AWS services referred to by acronym

| Acronym | Expansion |
|---|---|
| **ACM** | AWS Certificate Manager — issues and renews TLS certificates. Cannot issue for a private-only domain, which is the whole of D15. |
| **CA** | Certificate Authority — in "AWS Private CA", the ~USD 400/month alternative D15 rules out. |
| **RAM** | AWS **Resource Access Manager** — the service that shares resources across accounts. Not random-access memory; the collision is unfortunate and the plan means the service every time. Lake Formation cross-account sharing runs on it. |
| **SNS** | Simple Notification Service — the fan-out for alerts. |
| **SQS** | Simple Queue Service — appears only in the list of services RCPs can constrain. |
| **SSM** | AWS Systems Manager — used here for Session Manager (shell access without SSH) and for public parameters (AMI lookup). |
| **STS** | Security Token Service — issues the temporary credentials behind every `AssumeRole`. |
| **WAF** | Web Application Firewall — only in the Stage 13 public web tier. |

## IAM condition keys and policy elements quoted in the plan

These are not acronyms, but they carry most of the plan's meaning and are the densest jargon in it.

| Key | What it tests |
|---|---|
| `aws:PrincipalOrgID` | Is the caller part of *my* organization? The trusted-identities axis of the data perimeter (`plan/architecture.md` §4.2). |
| `aws:ResourceOrgID` | Is the resource being touched part of *my* organization? The trusted-resources axis — this is what stops a notebook copying data to a personal S3 bucket. |
| `aws:SourceVpc` / `aws:SourceVpce` | Did the request arrive through my VPC, or through a specific VPC endpoint? The trusted-networks axis. Note that a request from a laptop, even over the VPN, may carry a *different* account's endpoint ID — see `INT-05` and `INT-06`. |
| `aws:SourceIp` | The caller's public source address. Used to require that AWS API calls arrive through the VPN's Elastic IP (Stage 4 step 8). |
| `aws:ViaAWSService` | Is an AWS service making this call on the user's behalf, rather than the user directly? **The carve-out that everyone forgets.** Without it, a perimeter that looks correct blocks Athena reading S3 under Lake Formation — the exact path D13 forces all tabular reads through. |
| `aws:PrincipalIsAWSService` | The same idea from the resource side: the caller is a service principal, not a person. |
| `aws:RequestTag` / `aws:TagKeys` | The tags being applied by *this* request. The forcing function for mandatory tags — tag *policies* only constrain tagging operations, they cannot require a resource to be created with tags at all. |
| `iam:PassRole` / `iam:PassedToService` | Handing a role to a service so it can act under it. Unqualified `PassRole` plus a job-creating API is a privilege-escalation path: it lets a user run code under any role they may pass. Always scoped by service and by resource ARN here. |
| `IAMAllowedPrincipals` | A Lake Formation backwards-compatibility setting that makes the catalog fall back to plain IAM. If it is left in place, Lake Formation grants restrict nothing — which is why Stage 9 verifies the grant rather than trusting it. |
| **Permissions boundary** | A policy that caps what a role can ever be granted, independently of the policies attached to it. Required on every role a non-administrator can create or influence. |
| **Hybrid access mode** | A Lake Formation mode allowing a location to be governed by both Lake Formation and plain IAM at once. The documented exception path for D13, never the default. |
| **ARN** | Amazon Resource Name — the globally unique identifier of any AWS resource, e.g. `arn:aws:s3:::bucket/key`. |

## Units

| Symbol | Meaning |
|---|---|
| **USD** | United States dollar. All costs in the plan are USD, in `us-west-2`, and are order-of-magnitude estimates until Stage 12 replaces them with measured figures. |
| **GB** | Gigabyte. |
| **USD/h**, **USD/month** | The two figures the cost model always separates: the hourly burn while the lab is up, and the floor paid even when it is shut down (`plan/cost-model.md`). |
