# Decisions — index

Thirty-one closed decisions. Read this table first; open a decision file only when you need
its reasoning, its consequences or its revision trigger.

| # | Decision | In one line | Stages |
|---|---|---|---|
| [D1](D01-region.md) | Region | `us-west-2`, and it stays there; region portability is Terraform hygiene, not planned work. | S1a |
| [D2](D02-control-tower.md) | Control Tower vs. plain Organizations | Control Tower rather than plain Organizations; AWS Config is the price of it. | — |
| [D3](D03-terraform-state.md) | Terraform state location | Terraform state in a per-account S3 bucket with native S3 locking; no DynamoDB, nothing in Management. | S2 |
| [D4](D04-vpn-wireguard.md) | VPN technology | Self-managed WireGuard on `t4g.nano`, layer `[D]`; Client VPN documented as the managed alternative. | S4 |
| [D5](D05-sagemaker-egress.md) | SageMaker internet restriction mechanism | Two egress designs built behind a switch and compared: (A) NAT plus allowlist, (B) no NAT at all. | S3, S6, S8, S11 |
| [D6](D06-dlp-approach.md) | DLP approach | DLP is four problems with four native controls, all sitting on top of the data perimeter. | S11 |
| [D7](D07-orchestration.md) | Workflow orchestration in production | Two orchestrators built and compared: (A) MWAA Serverless, (B) EventBridge Scheduler + Step Functions. | S10 |
| [D8](D08-gitlab-hosting.md) | GitLab hosting | GitLab CE self-managed on EC2 in Production, layer `[D]` — stopped between sessions, not destroyed. | S7, S8 |
| [D9](D09-az-count.md) | Number of AZs | Two AZs for free subnet plumbing, one AZ for metered interface endpoints. | S3 |
| [D10](D10-identity-center-delegation.md) | Identity Center administration | Identity Center administration delegated to a dedicated Identity account, so Terraform never holds Management credentials. | S1b, S2 |
| [D11](D11-lab-lifecycle.md) | Lifecycle of the lab | Resources are ephemeral, accounts are not: pay nothing while idle, in three layers. | S1b, S2 |
| [D12](D12-budget-ceiling.md) | Budget ceiling | USD 50/month ceiling; it is what rules out always-on GitLab and forces stop/start. | S1a, S1b, S6, S7 |
| [D13](D13-lake-formation-enforcement.md) | How Lake Formation is actually enforced | Execution roles get NO direct S3 access to Lake Formation-registered prefixes, or every filter is decoration. | S5, S6, S11 |
| [D14](D14-supply-chain-account.md) | Where GitLab, Runners, ECR and CodeArtifact live | GitLab, Runners, ECR and CodeArtifact live in Production, not next to the people the gate gates. | S1a, S1b, S3, S6, S7, S8, S9 |
| [D15](D15-tls-internal.md) | TLS for internal endpoints | A real public domain plus split-horizon DNS; ACM cannot certify `.internal` and Private CA is over budget. **Needs a domain name from the user.** | S1b, S3, S7 |
| [D16](D16-break-glass.md) | Break-glass access | Break-glass is the Management account root and nothing else; every compensating control is detective. | S1a, S1b, S4 |
| [D17](D17-interactive-vs-runtime.md) | Where the data scientist works, and what crosses the account boundary | Interactive compute exists only in the Interactive OU; deployment targets carry the runtime, and only pipelines submit to it. | S1b, S8, S9, S10 |
| [D18](D18-data-scientist-access.md) | Data scientist access outside the Interactive OU | Outside the Interactive OU the data scientist gets the data plane, no compute, no control plane; writes only to enumerated prefixes. | S1b, S3, S5, S9 |
| [D19](D19-derived-zone.md) | The derived zone — what Lake Formation does *not* do (extends D13) | The derived copy is not prevented; the destination is managed and the perimeter contains it. Its CMK is the read control (D31). | S1b, S5, S11 |
| [D20](D20-staging-account.md) | The Staging account | A Staging account in a `Workloads` OU: a deployment target with sampled data, no domain, no registry of its own. | S1a, S1b, S3, S7, S8, S9, S10 |
| [D21](D21-development-account.md) | The Development account, and where experimentation ends | A Development account: Sandbox becomes pure experimentation and the promotion chain starts in Development. | S1a, S1b, S3, S6, S8, S10 |
| [D22](D22-data-governance-account.md) | The Data Governance account — state separated from compute | The governed lake moves to a dedicated Data Governance account; every environment reaches it through Lake Formation shares. | S1a, S1b, S3, S5, S9, S11 |
| [D23](D23-ou-structure.md) | OU structure — the account is the isolation boundary, the OU is the… | Five OUs, each named for the policy set it carries; the account isolates, the OU attaches policy. | S1a, S1b |
| [D24](D24-shared-filesystem.md) | Where the shared filesystem lives, now that there are two Studio do… | EFS in Sandbox only; Development gets neither its own nor a path to it — the exchange is S3 and git. | S5, S6 |
| [D25](D25-drop-box-consumer.md) | Who consumes the ingestion drop-box | The Production job role consumes the ingestion drop-box, and the `Data` OU SCP is tightened to deny Glue jobs. | S1a, S1b, S5, S9 |
| [D26](D26-unified-studio.md) | The development experience: SageMaker Unified Studio, and where its… | One SageMaker unified domain (DataZone V2) in Data Governance, associated to Sandbox and Development; a registry, never a runtime. | S1a, S4, S5, S6, S7 |
| [D27](D27-catalog-maintenance.md) | Catalog-maintenance compute in the Data OU: crawlers and optimizers | Crawlers and table optimizers may run in Data Governance under a named catalog-maintenance exception; never on Iceberg tables. | S1a, S5 |
| [D28](D28-workflow-contract.md) | The production workflow contract: what must exist for a scientist-a… | What crosses the gate into a headless deployment target: exactly six artifact classes, carried by the repository. | S6, S9, S10 |
| [D29](D29-policy-canary.md) | Where a Service Control Policy is tested before it reaches anything… | A tenth account, `Policy Canary`, alone in a fifth OU, `Policy Test` — because an empty OU tests nothing. | S1a, S1b |
| [D30](D30-scp-recovery.md) | The SCP recovery principal — a named role exempt from every custom … | `awsds-scp-recovery`, one enumerated role exempt from every custom `Deny`; adopted against the recommendation, with the trade-off recorded. | S1a, S1b, S2, S3 |
| [D31](D31-approver-read.md) | What a release approver may read | A bespoke `DeploymentManagerAccess` replaces `ReadOnlyAccess`, and the derived zone gets its own CMK. | S1b, S5 |

---

**All thirty-one are decided.** A decision is revisited only through its own *revision trigger*;
when one is, edit its file in place and add a line to [`plan/history.md`](../history.md).

*Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
