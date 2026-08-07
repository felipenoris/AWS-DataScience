# General Implementation Plan

Staged plan to build the AWS Data Science environment described in `CLAUDE.md`.

## How to use this file

- `CLAUDE.md` holds the **goals and the working rules**. This file holds the **route** to get there.
- Every entry in the `Claude LOG` section of `CLAUDE.md` must reference the stage of this plan it belongs to
  (e.g. "Stage 3 - Networking, in progress").
- This plan is expected to change. Whenever a stage is finished or a decision is revisited, update this file
  and record the change in "Plan revision history" at the bottom.
- Stages are ordered by dependency, not by importance. A stage can be split or reordered, but the
  prerequisites listed inside each stage must hold.

---

## 1. Baseline (state at the time this plan was written: 2026-08-07)

**Repository**

- Documentation only: `CLAUDE.md`, `LOG.md`, `README.md`, `REFERENCES.md`, `GENERAL_PLAN.md`, `LICENSE`.
- `secrets/` (git-ignored) holds `accounts.md` and `sso-users.md`.
- `terraform/` exists but is empty. It must be replaced by `terraform-live/` and `terraform-modules/`
  (the layout defined in `CLAUDE.md`).
- Git remote is GitHub (`felipenoris/AWS-DataScience`). **This infrastructure repository stays on GitHub**;
  GitLab (Stage 7) hosts the *application* repositories and the CI/CD pipelines.

**Local tooling** (verified)

- `aws-cli` 2.36.18, `terraform` 1.15.8, `uv` installed.
- `~/.aws/config` has only a `[default]` profile with invalid credentials. No SSO profile configured yet.

**AWS**

- Management Account created manually through the AWS console. Nothing else exists.

**Planned accounts** (`secrets/accounts.md`): Management, Sandbox, Production, Log Archive, Audit,
Identity — all six e-mails are registered.
**Planned SSO users** (`secrets/sso-users.md`): infrastructure (admin), sandbox (regular), manager (approvals).

**Region:** `us-west-2` (decision D1, recorded in `CLAUDE.md`).

---

## 2. Guiding principles

These come from `CLAUDE.md` and constrain every stage:

1. **The Management account is bootstrap-only.** Anything done there is manual, through the console, and
   recorded by the user in `LOG.md`. Terraform does not manage the Management account.
2. **No IAM Users.** Humans authenticate through IAM Identity Center (SSO) and assume roles. Machines
   (GitLab CI) use OIDC federation to assume roles. No long-lived access keys anywhere — with exactly one
   documented exception, break-glass access (D16), because a rule with no escape hatch is a rule that gets
   broken under pressure.
3. **Everything else is Terraform.** One state per account/environment, no shared state across environments.
4. **Private by default.** Data assets and databases never face the public internet. The only public entry
   points are the VPN and, later (Stage 13), an experimental web tier.
5. **Incremental.** Each stage must leave the environment in a working, verifiable state.
6. **Cost is a first-class constraint.** This is a personal account. Every stage lists its recurring cost and,
   where relevant, a cheaper alternative.
7. **Pay nothing while idle** (decision D11). Between sessions, metered resources are destroyed, stateful
   ones are stopped, and anything free at rest is simply left alone. See §5.1 — every stage must say which
   layer its resources belong to, so this shapes how each stage is designed, not just how it is operated.
8. **The region is a variable, not an assumption** (decision D1). The lab runs in `us-west-2` and stays
   there; keeping the region out of the code is plain Terraform hygiene, not migration work. See §4.1.
9. **Preventive controls come before detective ones.** The data perimeter (§4.2) is part of the landing
   zone, not of the DLP stage. Detecting an exfiltration you could have made impossible is a worse outcome
   than preventing it, and the preventive half (SCPs, RCPs, endpoint policies) is free.
10. **The lab is not the reference architecture.** Most decisions here are bent by a USD 50/month ceiling
    and a single operator. §11 records, decision by decision, what a large institution would do instead —
    so that what is learned here is the pattern, not the compromise.

---

## 3. Target architecture (summary)

Layers per §5.1: `[P]` persistent (free at rest), `[D]` dormant (stopped between sessions),
`[E]` ephemeral (destroyed between sessions).

```
AWS Organization (Management account - console only)                        [P]
│
├── OU Security
│   ├── Log Archive account  (created by Control Tower, S3 Object Lock)     [P]
│   ├── Audit account        (created by Control Tower) <- security guardian [P]
│   │                           GuardDuty / Security Hub / Macie / Analyzer
│   └── Identity account     <- Identity Center delegated administration    [P]
│
├── OU Sandbox
│   └── Sandbox account      <- data scientists work here
│       ├── VPC, subnets, IGW, security groups, private DNS zone            [P]
│       ├── S3 (raw/curated/artifacts) + Glue Catalog (Iceberg) + Athena    [P]
│       ├── Lake Formation (fine-grained permissions)                       [P]
│       ├── WireGuard EC2    <- the only human entry point, for BOTH VPCs   [D]
│       ├── NAT Gateway + interface VPC endpoints                           [E]
│       ├── SageMaker Studio domain + user profiles (VPC-only)              [P]
│       │     └── Studio apps (JupyterLab/CodeEditor, restricted egress)    [E]
│       └── EFS (NFS shared filesystem, lifecycle to IA)                    [P]
│
└── OU Production
    └── Production account   <- no human changes infrastructure here
        ├── VPC (mirrors sandbox topology, peered to sandbox)               [P]
        ├── S3 + Glue Data Catalog (Iceberg) + Lake Formation               [P]
        ├── ECR (dev-env images, application images)          <- D14        [P]
        ├── CodeArtifact (package proxy: PyPI, Cargo, ...)    <- D14        [P]
        ├── GitLab (EC2, private) + GitLab Pages              <- D14        [D]
        ├── internal ALB for GitLab/Pages (rebuilt per session)             [E]
        ├── GitLab Runners                                    <- D14        [E]
        ├── NAT Gateway + interface VPC endpoints                           [E]
        ├── SageMaker Pipelines / Step Functions / MWAA (workflow)          [E]
        └── (Stage 13) public web tier -> private backend                   [E]
```

**Why the tooling sits in Production (D14).** GitLab, its runners, ECR and CodeArtifact are the supply
chain: whoever controls them controls what runs in Production. They must not live in the account where
the `data-scientists` group has broad permissions. Two consequences shape several stages: the Production
VPC has to exist before Stage 7 (so it is built in Stage 3, not Stage 9), and the human path to GitLab is
laptop → WireGuard in Sandbox → VPC peering → GitLab in Production.

Note the refinement this forces on "only Terraform and CI/CD touch Production": nobody changes Production
*infrastructure* by hand, but humans do *use* a service hosted there (GitLab, over the VPN). The boundary
is the control plane, not the account.

---

## 4. Key decisions

| # | Decision | Status | Notes |
|---|---|---|---|
| D1 | Region | Decided (2026-08-07): **`us-west-2`**, and it stays there | Oregon, chosen on cost — roughly half São Paulo's price on metered items. Data residency is explicitly not a concern: this is a test with no real data. The project mirrors something that would run in `sa-east-1` in practice, but **that move is hypothetical and is not planned work**; the only thing it implies is the Terraform hygiene in §4.1, which is worth doing anyway. The availability question was answered and recorded there: nothing this plan uses is missing from São Paulo. |
| D2 | Control Tower vs. plain Organizations | Decided: **Control Tower** | Required by `CLAUDE.md`. It creates the Log Archive and Audit accounts, enables CloudTrail/Config org-wide and provides guardrails. Downside: AWS Config is the main recurring cost of the landing zone. |
| D3 | Terraform state location | Decided: **per-account S3 bucket, native S3 locking** | Terraform 1.15 supports `use_lockfile = true`, so no DynamoDB table is needed. Sandbox state lives in the Sandbox account, Production state in the Production account, and identity state in the Identity account (D10). This avoids putting state in the Management account (principle 1) and avoids cross-account state access. |
| D4 | VPN technology | Decided (2026-08-07): **self-managed WireGuard** | A `t4g.nano` EC2 instance in a public subnet, layer `[D]` — stopped between sessions, not destroyed, so the host key and peer configuration stay stable. Idle cost is its 8 GB EBS volume (~USD 0.65/month) plus the Elastic IP, which lives in the `[P]` foundation slice (~USD 3.65/month) so the endpoint address never changes. Consequences to handle in Stage 4: no native Identity Center integration, so peer public keys are provisioned by Terraform from a git-ignored variable file; and it is a single point of failure, which is acceptable for a lab. AWS Client VPN (~USD 73/month, SAML to Identity Center) stays documented as the managed alternative if SSO-integrated VPN becomes a requirement. |
| D5 | SageMaker internet restriction mechanism | Decided (2026-08-07): **build BOTH and compare, in Stage 6** | Not one mechanism but two designs, implemented behind a switch and evaluated against each other — see §4.3. **(A) Limited internet:** NAT plus an allowlist, using Route 53 Resolver DNS Firewall and/or a Squid proxy. **(B) No internet:** no NAT at all for the SageMaker subnets; packages arrive through CodeArtifact (upstream to the public repositories) and ECR pull-through cache, everything else through VPC endpoints. AWS Network Firewall (~USD 290/month) stays documented as the enterprise variant of (A) but is not built. The user's stated reservation about (B) is recorded in §4.3: CodeArtifact does not cover every language this environment needs. |
| D6 | DLP approach | Decided (2026-08-07): **native AWS combination**, on top of a data perimeter | The objective in `CLAUDE.md` is split into four problems, each with its own control: discovery/classification → **Macie**; fine-grained access → **Lake Formation** (LF-Tags, column and row filters), made enforceable by D13; egress control → **D5** plus the SageMaker VPC-only domain; exfiltration detection → **CloudTrail data events + GuardDuty + Security Hub** with CloudWatch alarms. **Underneath all four sits the data perimeter (§4.2)** — SCPs, RCPs and VPC endpoint policies built in Stage 1, not Stage 11, because they are the only controls that make exfiltration structurally impossible rather than merely visible. A third-party agent-based DLP is only evaluated in Stage 11, after these are in place and their gaps are known. |
| D7 | Workflow orchestration in production | **DEFERRED to Stage 10** | Options carried forward: **SageMaker Pipelines** (native to the environment the workflow is developed in, pay per execution — the shortest path from notebook to production, and the option the previous version of this table wrongly omitted), **Step Functions + ECS/Fargate** (pay per execution, near-zero idle cost), **MWAA** (~USD 350+/month, but it is what `CLAUDE.md` names explicitly), or **self-managed Airflow on ECS**. The decision only becomes real once an application from Stage 8 needs scheduling. Keep the application's entry point a plain container so it can be driven by any of the four. |
| D8 | GitLab hosting | Decided: **self-managed on EC2 in the Production account, layer `[D]`** | Required by `CLAUDE.md`. GitLab CE Omnibus on a private-subnet EC2 instance, reached through the VPN, backed up to S3. Account placement per D14. Sizing: 8 GB RAM is the realistic minimum for GitLab + Pages — `t4g.large` (ARM) is ~20% cheaper than `t3.large` for the same memory and GitLab Omnibus ships arm64 packages. Stopped between sessions rather than destroyed (~USD 4/month of EBS), because rebuilding from backup on every session is the fragile path. |
| D9 | Number of AZs | Decided: **2 for subnets, 1 for metered endpoints** | Subnets, route tables and NAT-less network plumbing are free, so the topology spans 2 AZs and stays honest. Interface VPC endpoints are charged per AZ, so they default to a single AZ during lab sessions; a resource in the other AZ still resolves and reaches them, at the cost of cross-AZ traffic and no AZ redundancy — an acceptable trade in a lab, and a one-variable change if it ever is not. |
| D10 | Identity Center administration | Decided (2026-08-07): **delegated to a dedicated Identity account** | The Identity Center instance and its identity store are created in the Management account and cannot be moved; what is delegated is their *administration*. One member account is registered as delegated administrator (`sso.amazonaws.com`), and from there Terraform manages permission sets, groups and assignments — so Terraform never needs credentials in the Management account, which is what makes principle 1 real rather than aspirational. The role goes to a **dedicated Identity account** rather than to the Audit account: Audit stays the security guardian (GuardDuty, Security Hub, Macie findings) and Identity owns access management, so the two concerns do not share a blast radius. Costs one extra Control Tower-governed account, i.e. one more AWS Config recorder (~USD 0.50-1/month) — accepted in exchange for the separation. **Consequences:** (i) assignments whose *target* is the Management account cannot be managed from the delegated account and stay manual; (ii) the Identity account can grant administrative access to any account in the organization, so it is as sensitive as Management — the Sandbox user must never have access to it; (iii) Control Tower's own permission sets (`AWSAdministratorAccess` and friends) are left alone, since editing them causes landing-zone drift. |
| D11 | Lifecycle of the lab | Decided (2026-08-07): **resources are ephemeral, accounts are not** | The environment runs for a few hours per session and is shut down in between. Accounts, the Organization, Control Tower and Identity Center are never destroyed. Within the accounts the rule is not "destroy everything" but **"pay nothing while idle"**: resources that cost nothing at rest are simply left in place, resources that meter are destroyed, and stateful services that are awkward to rebuild are stopped rather than destroyed. Three layers, defined in §5.1. |
| D12 | Budget ceiling | Decided (2026-08-07): **USD 50/month** | With the three-layer model the projection is a ~USD 18-22/month floor plus ~USD 0.28-0.35 per lab hour, so roughly USD 26-27/month at the expected usage (§5). The AWS Budget created in Stage 1 alerts at 50/80/100% of USD 50, with Cost Anomaly Detection alongside it. This ceiling is what rules out always-on GitLab (~USD 60/month by itself) and confirms the stop/start approach. |
| D13 | How Lake Formation is actually enforced | Decided (2026-08-07): **execution roles get no direct S3 access to registered locations** | Lake Formation only constrains engines that ask it. A role holding `s3:GetObject` on a registered bucket can read the raw Parquet from a notebook and every column and row filter becomes decoration. So the fine-grained access control objective in `CLAUDE.md` is only real if the SageMaker execution role's S3 permissions **exclude** the Lake Formation-registered prefixes, and tabular access goes exclusively through an LF-aware engine: Athena, Glue interactive sessions, or EMR with runtime roles. Non-registered prefixes (scratch, artifacts, model outputs) keep ordinary IAM access. Lake Formation's **hybrid access mode** is the documented migration path if a workload turns out to need both, and is a deliberate exception rather than the default. This is decided in Stage 5, before Stage 6 can bake the bypass into the execution role. |
| D14 | Where GitLab, Runners, ECR and CodeArtifact live | Decided (2026-08-07): **the Production account** | These four are the software supply chain. In the Sandbox account they would sit next to a `data-scientists` group with broad permissions, which means the runner holding the deploy credentials, and the registry Production pulls from, would both be modifiable by the people the approval gate is supposed to gate. Putting them in Production removes that path and costs no extra account. **Accepted trade-off:** build and runtime now share an account, so there is no blast-radius boundary between "the thing that builds" and "the thing that runs" — a compromise of GitLab is a compromise of Production. A large institution splits these into a Shared Services / Tooling account in an `Infrastructure` OU (§11). **Consequences:** the Production VPC moves from Stage 9 to Stage 3; Sandbox↔Production VPC peering is needed so the VPN reaches GitLab; ECR and CodeArtifact are consumed cross-account from Sandbox; and the Sandbox user needs a narrow, service-level (not infrastructure-level) reach into Production. |
| D15 | TLS for internal endpoints | Decided (2026-08-07): **a real public domain plus split-horizon DNS** | ACM cannot issue a certificate for `sandbox.internal` — public certificates require a domain you can validate publicly, and AWS Private CA costs ~USD 400/month (~USD 50 in short-lived mode), both over the ceiling. The workable path: register one public domain, keep a public hosted zone **for DNS validation only**, issue free public ACM certificates (including the wildcard GitLab Pages needs), and resolve the names to private addresses through the **private** hosted zone. A public certificate on an internal ALB is supported; nothing is published. Cost ~USD 0.50/zone plus the domain (~USD 12-15/year). **Needs input from the user: which domain name to register.** |
| D16 | Break-glass access | Decided (2026-08-07): **one documented emergency path, tested and alarmed** | "No IAM Users" (principle 2) has no answer for an IAM Identity Center outage or a misapplied SCP that locks everyone out, and an absolute rule with no escape hatch is one that gets broken improvised, under pressure, at the worst moment. The exception: a break-glass mechanism in the Management account with hardware MFA, credentials stored offline, never used in normal operation, and a CloudWatch alarm on any use of it. Documented in Stage 1 and tested once. The Management account root user's recovery path is documented alongside it. |

### 4.1 Region portability

The lab runs in `us-west-2` and **stays there**. A move to São Paulo is hypothetical and is not planned
work — no stage builds towards it, and no migration procedure is maintained here.

What remains is ordinary Terraform hygiene, which costs nothing and is worth doing on its own merits:

| Thing | Rule |
|---|---|
| Region | A single `var.region`, set per environment in `.tfvars`. No `us-west-2` literal in `.tf` files. |
| Availability zones | `data.aws_availability_zones` indexed by position, never `us-west-2a`. |
| AMI IDs | AMI IDs are region-scoped. Resolve through SSM public parameters (e.g. `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64`), never a literal `ami-…`. |
| Bucket names | S3 names are globally unique — build them from variables rather than pasting a region in. |

Recorded for reference, from the check on 2026-08-07: `sa-east-1` has endpoints for every service this
plan uses — Control Tower, IAM Identity Center, SageMaker (Studio with `ml.t3.medium`, `ml.g5`, `p5.4xl`),
MWAA, Macie, GuardDuty, Security Hub, Lake Formation, Glue, Athena, EFS, ECR, Client VPN, Network Firewall
and Graviton `t4g`. So the answer to "would anything break in São Paulo?" is no; the differences are price
(~1.5-2x) and a lag on the newest SageMaker features. If a move ever became real, the one genuinely
expensive part would be redeploying the Control Tower landing zone, whose home region is fixed at
deployment time.

One cross-region rule is permanent and unrelated to any of this: ACM certificates for CloudFront must live
in `us-east-1` regardless of where the workload runs (relevant only at Stage 13).

### 4.2 Data perimeter

The four DLP controls in D6 are all *inside* the accounts. None of them answers the question a perimeter
answers: **can a credential from this organization move data to somewhere outside it, or can something
outside it read data from here?** AWS publishes a three-axis framework for this, every part of it free, and
it belongs in the landing zone (Stage 1) rather than in the DLP stage:

| Axis | Question it answers | Control | Built in |
|---|---|---|---|
| Trusted identities | Can a principal from outside the organization touch my resources? | Resource policies and **RCPs** with `aws:PrincipalOrgID` | Stage 1 |
| Trusted resources | Can my principals write to resources outside the organization? | **SCPs** with `aws:ResourceOrgID` | Stage 1 |
| Trusted networks | Can my identities reach my resources from outside my networks? | **VPC endpoint policies** and resource policies with `aws:SourceVpce` / `aws:SourceVpc` | Stage 3 |

**Resource Control Policies (RCPs)** are the piece that does the most work here and the piece most easily
missed: applied at the OU or organization root, they set a maximum permission on the *resource* side for
S3, STS, KMS, SQS and Secrets Manager, regardless of what any account-level policy says. An RCP denying S3
access to principals outside the organization is, for the stated goal of preventing data leakage, worth more
than Macie — it removes the path instead of reporting on it afterwards.

The symmetric SCP (`aws:ResourceOrgID`) is what stops the most obvious exfiltration route in a data science
environment: a notebook copying a dataset to a personal S3 bucket in someone else's account. Note the known
gaps to keep in mind rather than assume away: these conditions do not cover every service, presigned URLs
are evaluated under the signer's identity, and any path that leaves through the *application* layer (an
HTTPS POST to an allowlisted site) is D5's problem, not the perimeter's.

**Implementation note:** none of these policies should be written from scratch. The aws-samples
**`data-perimeter-policy-examples`** repository carries reference SCPs, RCPs and endpoint policies with
the service carve-outs (`aws:ViaAWSService`, `aws:PrincipalIsAWSService`) that every one of these
conditions needs. A perimeter without the carve-outs blocks AWS services acting on your behalf — and the
first casualty in this plan would be Athena reading S3 under Lake Formation, i.e. the exact access path
D13 forces everything through (see Stage 5).

### 4.3 The two egress designs (D5)

Rather than pick one mechanism up front, Stage 6 builds both and measures them. They are not variations on
a theme — they answer the "SageMaker should have access to the internet" requirement in `CLAUDE.md` in
opposite ways, and the point of building both is to find out what the strict one actually costs in
day-to-day friction.

**(A) Limited internet — NAT plus allowlist.** The SageMaker private subnets route to the NAT gateway;
Route 53 Resolver DNS Firewall permits an explicit list of domains (PyPI, conda, CRAN, the Julia package
server, crates.io, the distro mirrors, GitLab) and blocks the rest, optionally with a Squid proxy for
HTTP-layer control. Familiar and flexible. Its honest weakness is that DNS-name filtering is bypassable by
connecting to a raw IP, so it is a strong control against accident and a weak one against intent.

**(B) No internet — proxied artifacts only.** The SageMaker subnets have no route to a NAT gateway at all.
Packages arrive through **CodeArtifact** repositories configured with an upstream to the public registry
(CodeArtifact itself fetches from the internet — AWS-side, not through your VPC), container images through
**ECR pull-through cache**, and everything else through VPC endpoints. There is no egress path to misuse,
which is why this is the shape regulated institutions converge on. It also removes the NAT gateway, the
single largest hourly line item in §5 — at the price of the two CodeArtifact interface endpoints
(~USD 0.02/h), still a clear net saving.

**The user's reservation about (B), recorded as a real constraint, not an objection to be argued away:**
this environment must support **Python, Julia, Rust and R**, and CodeArtifact does not cover all of them.
Concretely:

| Ecosystem | CodeArtifact | Fallback if not covered |
|---|---|---|
| Python (PyPI) | Supported | — |
| Rust (Cargo) | Supported — **confirm at Stage 6**, this is a comparatively recent format | `cargo vendor`, or a `panamax` mirror on S3 |
| Julia (Pkg) | **Not supported** | Self-hosted `PkgServer.jl` storage server, or bake into the dev-env image, or allowlist `pkg.julialang.org` |
| R (CRAN) | **Not supported** | Posit Package Manager (commercial), a `miniCRAN` mirror served from S3, or bake into the image |
| OS packages (dnf/apt) | Not applicable | Distro mirror on S3, or bake into the image |

The reframing that makes this tractable: **the dev-env container image is itself the dependency delivery
mechanism.** It is built by a CI pipeline (Stage 8) on a runner that *does* have internet, so Julia, R,
Rust and their package sets are installed at build time and arrive in SageMaker pre-installed. A package
proxy is then only needed for *ad-hoc* installation during exploration — which is mostly Python, which
CodeArtifact does cover. Design (B) therefore does not require solving four ecosystems; it requires solving
one, and making image rebuilds cheap enough that the other three are not painful. Whether that holds in
practice is exactly what Stage 6 is meant to find out.

**Deliverable of the comparison** (Stage 6): a written verdict covering, for each design, the measured
hourly cost, what breaks in a normal working session, how long a "I need package X right now" loop takes,
and what an intentional exfiltration attempt achieves. The plan does not pre-commit to a winner.

---

## 5. Cost model

Because of D11 the relevant question is not "what does this cost per month" but "what is the floor when
nothing is running, and what does an hour of lab time add on top". Order-of-magnitude figures for
`us-west-2`, to be confirmed with the AWS Pricing Calculator before each stage.

**The floor — paid every month even with the lab shut down (~USD 18-22):**

| Item | Approx. USD/month | Note |
|---|---|---|
| Organization, accounts, Identity Center, VPC, subnets, IGW, security groups, IAM roles | 0 | These cost nothing at rest, so there is no reason to destroy them |
| GitLab EBS volume (50 GB gp3) | ~4.00 | Paid while the instance is stopped; this is the price of not rebuilding GitLab |
| Elastic IP for WireGuard | ~3.65 | All public IPv4 addresses are charged hourly, attached or not |
| KMS customer-managed keys (3) | ~3.00 | ~1.00 per key per month |
| S3 data + state + backups (~25 GB) | ~1.00 | |
| ECR images (~10 GB) | ~1.00 | |
| AWS Config (Control Tower) | ~1-3 | One recorder per governed account (six, per D10). The estimate assumes an idle lab; a heavy `terraform apply` session records a configuration item per resource change and can multiply this. Control Tower allows restricting the recorded resource types — the main cost lever of the landing zone, applied in Stage 1 |
| Route 53 hosted zones (1 private + 1 public, D15) | ~1.00 | The public zone exists only for ACM DNS validation |
| Public domain registration (D15) | ~1.00 | ~USD 12-15/year amortised |
| CodeArtifact | ~0.10 | USD 0.05/GB-month storage plus USD 0.05 per 10k requests; negligible at lab scale |
| Security Hub + IAM Access Analyzer | ~1-2 | Enabled org-wide from Stage 1 (principle 9). Access Analyzer external-access findings are free; Security Hub charges per check and per finding |
| GuardDuty | 0 → ~3-5 | Free for the first 30 days per account, then driven by CloudTrail/VPC flow/DNS log volume. S3 Protection and Malware Protection are extra and are the ones to watch against the ceiling |
| WireGuard EBS (8 GB) + CloudWatch logs | ~1.00 | |
| EFS (shared filesystem + Studio homes, lifecycle to IA) | ~0.50 | `[P]` since the third review — cents at rest, and it buys the removal of the sync-to-S3-on-teardown machinery (§5.1 rule 2) |
| **Revised floor** | **~USD 18-22** | Up from the ~USD 15 estimate, almost entirely from moving the detective controls into the landing zone (principle 9). Still comfortably under the USD 50 ceiling |

Two cost levers worth applying rather than discovering later:

- **S3 Bucket Keys** on every SSE-KMS bucket. They cut KMS request charges by up to ~99%, and a data
  environment issues a KMS request per object operation — without this, KMS requests can quietly exceed
  the cost of the keys themselves. Free to enable; set it in the `s3-bucket` module from Stage 2.
- **Scope Macie deliberately** (Stage 11). Macie charges per GB inspected for sensitive-data discovery. Run
  it against a sampled prefix, not the whole lake, or it becomes the largest single line item in the
  project. The same caution applies to **CloudTrail S3 data events**, which bill per event: a single Spark
  job listing and reading thousands of objects generates a matching number of events.

**Per hour of lab time — added while the environment is up (~USD 0.25/h):**

| Item | Approx. USD/h |
|---|---|
| NAT Gateway (1) + its public IPv4 | ~0.050 + 0.045/GB processed — **zero under egress design B** (§4.3) |
| Interface VPC endpoints (9, single AZ per D9; 11 under design B) | ~0.090-0.110 (double if spread across 2 AZs) |
| GitLab EC2 `t4g.large` | ~0.067 (`t3.large` would be ~0.083) |
| Internal ALB in front of GitLab/Pages (only while GitLab is up) | ~0.023 + LCU usage |
| Production NAT + endpoints (only while runner builds need egress) | ~0.050 + 0.045/GB |
| SageMaker Studio `ml.t3.medium` (per running app) | ~0.050 |
| WireGuard EC2 `t4g.nano` | ~0.004 |
| Sandbox ↔ Production VPC peering | free within an AZ; USD 0.01/GB each way across AZs — see §9 item 3 |
| EFS, Athena, Glue | usage-based; negligible at lab scale |

The endpoint count rose from 6 to 9 (11 under design B) because the Stage 3 list was incomplete: Studio in
VPC-only mode also needs `sagemaker.studio` and `kms`, and design B adds the two `codeartifact` endpoints.
At ~USD 0.01/h per endpoint per AZ this is the largest hourly item, so the list stays minimal and
single-AZ. The table now also carries the **Production** side — the runners' NAT and the GitLab ALB were
missing from earlier versions of this plan, which undercounted a full-stack hour.

**Projection:** ~USD 20 floor + 20 h/month × ~USD 0.28-0.35 (the upper end is a full-stack hour: GitLab,
its ALB and a runner build all running at once) ≈ **USD 26-27/month**, against the USD 50 ceiling (D12).
Design B trades the NAT gateway for two CodeArtifact endpoints, so it is the *cheaper* of the two egress
options as well as the stricter one — which is worth knowing before the Stage 6 comparison starts.

**What the ceiling rules out:** always-on GitLab (~USD 60/month on its own), AWS Client VPN
(~USD 73/month, the D4 alternative), Network Firewall (~USD 290/month, option D5c) and MWAA
(~USD 350/month, option D7). Any of these becomes affordable only as a short, deliberate experiment —
which is precisely what the operating model below is for.

**Guardrail:** AWS Budgets with e-mail alerts must exist before any compute is created (Stage 1).

### 5.1 Operating model: three layers (D11)

The naive reading of "destroy it between sessions" is wrong, because most AWS resources cost nothing at
rest. The rule is **pay nothing while idle**, not **destroy everything**. That splits the environment into
three layers, and every stage must say which layer each of its resources belongs to.

**[P] Persistent — created once, never destroyed.** Free or nearly free at rest, or too slow to rebuild:
the Organization, the six accounts, Control Tower, Identity Center, SCPs, Terraform state buckets, the
**VPC itself** (VPC, subnets, route tables, internet gateway, security groups, NACLs cost nothing),
Route 53 private zone, IAM roles, KMS keys, S3 data buckets, ECR repositories, budgets and alarms — and,
since the third review, the **SageMaker Studio domain with its user profiles** (a domain at rest bills
nothing; only running apps and home-filesystem GBs do) and the **EFS filesystem** (lifecycle to
Infrequent Access; cents per month at lab scale). Rule 2 below records why those two moved out of `[E]`.

**[D] Dormant — kept, but powered off between sessions.** Stateful services where a rebuild is riskier
than the idle cost: the GitLab EC2 instance and its EBS volume, and the WireGuard instance. `make down`
stops them, `make up` starts them. Idle cost is their EBS volumes (~USD 4.65/month) plus the Elastic IP
that WireGuard re-attaches on start — the address itself is allocated in `[P]`, so it survives even if the
instance is replaced. This is what makes the Stage 7 backup/restore cycle a disaster-recovery procedure
rather than a daily dependency.

**[E] Ephemeral — destroyed at the end of a session.** Everything metered by the hour and rebuildable in
minutes: NAT Gateway, interface VPC endpoints, SageMaker Studio *apps* (the domain stays), the internal
ALB in front of GitLab (an ALB cannot be stopped, only destroyed — it bills ~USD 0.023/h for as long as
it exists), GitLab Runners, MWAA/Step Functions, the Stage 13 web tier.

**Rules this imposes:**

1. Terraform slices are split along these lines. `terraform destroy` of an `[E]` slice must never be able
   to reach a `[P]` resource; persistent buckets get `prevent_destroy` lifecycle blocks.
2. No state lives only inside an `[E]` resource — enforced by construction since the third review, which
   moved the two stateful ex-`[E]` resources into `[P]` for exactly this reason. The EFS used to be `[E]`
   with a sync-to-S3-before-teardown step; that sync was the single most likely way to lose real work in
   this design, and at EFS-IA prices (~USD 0.016/GB-month) persistence costs cents. The Studio domain used
   to be `[E]` with an explicit home-filesystem delete in `make down`, because deleting a domain
   **retains** its home EFS by default (`RetentionPolicy` defaults to `Retain`) and every teardown would
   otherwise orphan a billing filesystem; a domain at rest is free, so keeping it removes both the hazard
   and the rebuild. SageMaker Studio home directories remain **scratch** by policy — real work lives in
   GitLab or S3.
3. `make up` and `make down` per environment, in dependency order, and both must be tested. A rebuild that
   only works by hand is a bug.
4. Anything slow or awkward to create — Control Tower, accounts, ACM DNS validation, Identity Center —
   belongs in `[P]` by construction.
5. Keep addresses stable: private DNS names instead of IPs, and a retained Elastic IP for WireGuard, so
   client configs survive a rebuild.
6. Each stage documents its teardown as well as its build, and records the measured rebuild time.
7. The layer assignment is a cost judgement and can change. If a `[D]` service turns out to be cheap to
   rebuild, demote it to `[E]`; if an `[E]` rebuild proves slow or fragile, promote it to `[D]` and pay
   the idle cost.

---

## 6. Conventions (to be applied from Stage 2 onwards)

**Naming:** `<project>-<env>-<component>[-<detail>]`, lowercase with hyphens.
Project prefix: `awsds`. Example: `awsds-sandbox-vpc`, `awsds-prod-raw-data`.

**Mandatory tags on every resource:**
`Project=AWS-DataScience`, `Environment=sandbox|production|shared`, `ManagedBy=terraform`,
`Owner=<sso-user>`, `CostCenter=<stage>`. (`shared` marks org-level resources — the identity slice — not
a Shared Services account, which D14 decided against.)

**Terraform layout:**

Each slice carries its layer from §5.1: `[P]` persistent, `[D]` dormant (stop/start), `[E]` ephemeral.

```
terraform-live/
├── identity/             # [P] permission sets, groups, assignments - applied with the
│   │                     #     delegated-admin profile (D10); never touches Management
│   └── bootstrap/        # [P] state bucket for the Identity account
├── sandbox/
│   ├── bootstrap/        # [P] state bucket for this account (state migrated in, never committed)
│   ├── foundation/       # [P] VPC, subnets, route tables, IGW, security groups, private
│   │                     #     hosted zone, KMS keys, IAM roles, WireGuard Elastic IP,
│   │                     #     peering requester + routes to Production (D14)
│   ├── data/             # [P] S3 buckets, Glue databases, Lake Formation registrations,
│   │                     #     Athena workgroup - all free or near-free at rest
│   ├── egress/           # [E] NAT gateway, interface VPC endpoints - the metered network.
│   │                     #     Two variants behind a switch: D5(A) with NAT, D5(B) without
│   ├── vpn/              # [D] WireGuard EC2 (stopped, not destroyed)
│   ├── nfs/              # [P] EFS filesystem, mount targets, access points (lifecycle to IA)
│   ├── sagemaker/        # [P] domain + user profiles; running apps are [E] (deleted by make down)
│   └── app/
│       └── app-etl/      # [E]
└── production/
    ├── bootstrap/        # [P]
    ├── foundation/       # [P] VPC etc. + peering accepter. Built in Stage 3, because
    │                     #     Stage 7 (GitLab) depends on it (D14)
    ├── data/             # [P] S3, Glue, Lake Formation, ECR, CodeArtifact (D14)
    ├── egress/           # [E] NAT, endpoints, internal ALB for GitLab/Pages (ALBs cannot stop)
    ├── tooling/          # [D] GitLab EC2 + EBS (D8, D14) - its ALB lives in egress/ [E]
    ├── runners/          # [E] GitLab Runners (D14)
    ├── orchestration/    # [E] Step Functions / SageMaker Pipelines / MWAA (D7)
    └── app/
        └── app-etl/      # [E]

terraform-modules/        # reusable: vpc, wireguard, iam-role, ecr-repo, s3-bucket, step-function, ...
                          # consumed by git tag, never by branch - a module that moves under a
                          # caller is a broken caller
```

`make down ENV=sandbox` destroys the `[E]` slices in reverse dependency order and stops the `[D]`
instances; `make up ENV=sandbox` starts the `[D]` instances and applies the `[E]` slices; `make status`
reports what is running and the current hourly burn. `[P]` slices are never touched by any of them — they
are applied deliberately, by hand. One `[E]` resource lives outside any slice: running SageMaker Studio
*apps* are created by users, not by Terraform, so `make down` deletes them through the API before
touching the slices.

**Terraform rules:**

- Pin the provider version and `required_version`. One `providers.tf` per slice.
- Region, AZs and AMIs follow the portability rules in §4.1 — no region literals in `.tf` files.
- Authentication through named SSO profiles (`awsds-infra-sandbox`, `awsds-infra-prod`) — never keys.
- Every slice: `terraform fmt`, `validate` and `plan` must be clean before apply.
- Remote state read across slices through `terraform_remote_state` data sources, never hardcoded IDs.
- Modules are referenced by **git tag**, never by branch, so a module change cannot silently alter an
  existing deployment.

**IAM rules** (these are conventions because they are easy to violate one role at a time):

- Every role that a non-administrator can create or influence carries a **permissions boundary**.
- `iam:PassRole` is never granted unqualified. It is always scoped by `iam:PassedToService` and by resource
  ARN. `PassRole` plus a job-creating API (`sagemaker:CreateTrainingJob` is the relevant one here) is a
  privilege-escalation path: it lets a user run code under any role they are allowed to pass.
- Nothing gets `AdministratorAccess` or `PowerUserAccess` "for now". The starting point of a permission set
  is narrow, because loosening a permission is a five-minute change and tightening one is a negotiation.

---

## 7. Stages

### Stage 0 - Baseline (DONE)

Management account created manually; `aws`, `terraform` and `uv` installed; repository documentation written
and reviewed. Nothing provisioned.

---

### Stage 1 - Organization, accounts and identity (manual, console)

**Objective:** a working AWS Organization with the environment accounts and SSO access, so that everything
after this can be done by Terraform without root credentials.

**Prerequisites:** none outstanding. D1 is decided (`us-west-2`) and all six account e-mails are in
`secrets/accounts.md`.

**To execute (all manual, by the user, recorded in `LOG.md`):**

1. Secure the Management account root user: hardware or virtual MFA, strong password, no access keys,
   billing alerts enabled.
2. Create a Budget of **USD 50/month** (D12) with e-mail alerts at 50%/80%/100%. Enable **Cost Anomaly
   Detection** next to it — it is free, and it catches a bad cost *pattern* days before a budget
   threshold trips. Optionally add a budget *action* that attaches a deny-compute SCP at 100% — a
   lab-appropriate emergency brake.
3. Enable AWS Control Tower with `us-west-2` as the home region. It will create the Organization, the
   Log Archive and the Audit accounts (e-mails already in `secrets/accounts.md`), and turn on org-wide
   CloudTrail and Config. Note: the home region cannot be changed afterwards without redeploying the
   landing zone.
4. Create the `Sandbox`, `Production` and `Identity` accounts through Account Factory, using the e-mails
   in `secrets/accounts.md`. OUs: `Sandbox` OU, `Production` OU, and `Identity` in the `Security` OU
   alongside Log Archive and Audit. **No further accounts are needed** — D14 places the tooling in
   Production rather than in a separate Shared Services account, so the six accounts already registered
   are the complete set. §11 records what a larger organization would add.
   Account creation here is manual through Account Factory; **Account Factory for Terraform (AFT)** is the
   automated equivalent and is deliberately not used — with three accounts to create, once, it would cost
   more to set up than it saves (§11).
5. **Register the Identity account as delegated administrator of IAM Identity Center (D10).** From the
   Management account:
   `aws organizations register-delegated-administrator --account-id <IDENTITY_ACCOUNT_ID> --service-principal sso.amazonaws.com`.
   This is reversible (`deregister-delegated-administrator`), so it is a cheap step to get wrong.
   Everything in steps 6 and 7 is then done **from the Identity account**, not from Management.
6. In IAM Identity Center, create the three users from `secrets/sso-users.md` and the groups
   `infrastructure`, `data-scientists`, `managers`. Enforce MFA.
7. Create permission sets: `AdministratorAccess` (infrastructure), `DataScientistAccess` (sandbox),
   `ReadOnlyAccess` (managers). An earlier draft also created a `DeployApprover` permission set; it was
   dropped — the deploy approval gate lives in GitLab (Stage 8), driven by GitLab group membership, and
   consumes no AWS-side permission. Create such a permission set only when something actually consumes it.
   **`DataScientistAccess` does not start as `PowerUserAccess`.** An earlier version of this plan gave it
   `PowerUserAccess` "until Stage 6", which contradicts `CLAUDE.md` ("no permissions to perform
   infrastructure changes, except for artifacts managed by AWS SageMaker") and, worse, would let the
   sandbox user create a public S3 bucket or an internet-facing EC2 instance — i.e. walk around the whole
   design — for five stages. It starts as: SageMaker Studio use, read/write on the sandbox data prefixes,
   Athena, ECR pull, and nothing else. `AmazonSageMakerFullAccess` is *not* a safe starting point either:
   it grants `s3:*` on any bucket with "sagemaker" in the name plus a broad `iam:PassRole`. Attach a
   permissions boundary and scope `PassRole` per the IAM rules in §6.
   Assign them: infrastructure → Sandbox + Production + Identity; data-scientists → Sandbox, plus a
   narrow service-level reach into Production for GitLab and ECR (D14) that grants no infrastructure
   permission there; managers → Sandbox + Production, read-only (the approval itself happens in GitLab).
   The Sandbox user gets no access to Identity, Audit or Log Archive.
   Leave Control Tower's own permission sets untouched — editing them causes landing-zone drift.
   These are created by hand here only because Terraform cannot run before SSO login works; Stage 2 moves
   them into `terraform-live/identity/` and imports them.
8. The infrastructure user's assignment **on the Management account itself** has to be created from the
   Management account — the delegated administrator cannot manage assignments targeting Management.
   This is the one identity task that stays there permanently.
9. **Break-glass access (D16).** Set up the emergency path in the Management account: hardware or virtual
   MFA, credentials recorded offline (never in this repository, never in `secrets/`), a CloudWatch alarm on
   any use of it, and a documented procedure. Test it once, then leave it alone. Do the same for the
   Management root user's recovery path.
10. **Centralized root access management.** Control Tower creates five member accounts, each with its own
    root user and its own recovery e-mail — five credentials nobody will ever rotate. AWS Organizations can
    remove root credentials from member accounts centrally and perform the few privileged root actions on
    demand. Enable it; this is one console setting that eliminates a whole class of dormant risk.
11. **Preventive policies.** Attach to the OUs, in this order:
    - **SCPs:** deny leaving the organization, deny disabling CloudTrail/Config/GuardDuty, restrict usable
      regions to `us-west-2` — the region SCP must still allow `us-east-1`, because IAM, Organizations,
      Route 53, CloudFront and Support only have endpoints there — and **deny writes to S3 resources
      outside this organization** (`aws:ResourceOrgID`), which is the trusted-resources axis of §4.2 and
      closes the most direct exfiltration route a notebook has. Two more, cheap and load-bearing:
      **deny `iam:CreateUser` and `iam:CreateAccessKey`** — principle 2 ("no IAM Users") is otherwise a
      convention with no enforcement, and break-glass (D16) is unaffected because the Management account
      is exempt from SCPs — and **deny `s3:PutAccountPublicAccessBlock`**, which protects the
      account-level setting enabled below.
    - **RCPs:** deny access to S3, STS, KMS, SQS and Secrets Manager from principals outside the
      organization (`aws:PrincipalOrgID`) — the trusted-identities axis of §4.2.
    - **Tag policies:** standardize the mandatory tags from §6 — with a precision the previous version of
      this plan got wrong: tag policies constrain *tagging operations*, they cannot force a resource to be
      created with tags at all. The forcing function is an SCP with `aws:RequestTag`/`aws:TagKeys`
      conditions on the create actions that matter (EC2, S3, SageMaker). One or the other, or the tags are
      a convention — and conventions do not survive contact with a `terraform apply` at 23:00.
    - **Account-level S3 Block Public Access** in every member account. The module-level block from
      Stage 2 only covers buckets the module creates; the account-level setting is the blanket that also
      covers the bucket someone creates outside it. Protected by the SCP above.
    - **Declarative policies:** enforce IMDSv2 and EC2 public-access defaults org-wide.
    Apply these to a test OU first — an SCP mistake is the fastest way to lock yourself out of your own
    organization, which is what step 9 exists for.
12. **Detective controls** (principle 9 — these belong to the landing zone, not to Stage 11). The
    *delegation* of each service to the Audit account runs **from the Management account**
    (`enable-organization-admin-account` / `register-delegated-administrator`, one manual console action
    per service — consistent with principle 1); everything after that is done from the Audit account:
    enable org-wide **Security Hub**, **IAM Access Analyzer** (external access, and unused access for
    Stage 12) and **GuardDuty**. Watch the cost of GuardDuty's S3 Protection and Malware
    Protection against D12 — enable the base service now and decide on those two with a real bill in hand.
13. **Make the audit trail tamper-evident:** enable **S3 Object Lock** on the Control Tower Log Archive
    bucket and **CloudTrail log file validation**. An audit log that the compromised party can edit is not
    an audit log. Do this before there is anything worth hiding in it.
14. **Restrict the AWS Config recorder** to the resource types this project actually uses. Config is the
    main recurring cost of the landing zone (§5) and the default records everything, in six accounts.
15. Configure local SSO profiles: `aws configure sso` for `awsds-infra-sandbox`, `awsds-infra-prod` and
    `awsds-infra-identity`.
16. **Check the AZ name-to-ID mapping** across the Sandbox and Production accounts
    (`aws ec2 describe-availability-zones --query 'AvailabilityZones[].[ZoneName,ZoneId]'` under each
    profile). D14 makes this matter for real: Sandbox↔Production peering traffic is free within an AZ and
    USD 0.01/GB each way across AZs, so a mismatch has a bill attached. See §9 item 3.

**Deliverables:** accounts created; SSO login working; `aws sts get-caller-identity --profile awsds-infra-sandbox`
returns the Sandbox account ID; `aws sso-admin list-instances --profile awsds-infra-identity` returns the
Identity Center instance, which is the proof that the delegation took effect; an attempt to write to an S3
bucket outside the organization is denied, which is the proof that the perimeter is real.

**Blocking questions for the user:** the domain name to register (D15). Not needed to start the stage, but
needed before Stage 7.

**Risks:** Control Tower landing zone deployment takes ~60 minutes and is awkward to undo. Account e-mails
cannot be reused after an account is closed (a closed account holds its e-mail for 90 days) — which is
exactly why D11 keeps accounts in the persistent layer. Everything created in this stage is persistent;
nothing here is torn down between sessions.

**To verify while executing this stage**, because Control Tower's handling of Identity Center has changed
more than once and the plan should not assume: (i) that the delegation coexists with the landing zone
without raising drift; (ii) that the restriction in step 8 is exactly as described — that assignments
targeting the Management account are the *only* thing the delegated administrator cannot manage; and
(iii) that the RCPs and SCPs in step 11 do not conflict with the SCPs Control Tower manages itself, which
is the usual source of "the guardrail I wrote silently does nothing"; and (iv) that enabling S3 Object
Lock on the Control Tower-managed Log Archive bucket (step 13) does not raise landing-zone drift.

---

### Stage 2 - Terraform foundation

**Objective:** the repository can provision infrastructure reproducibly.

**Prerequisites:** Stage 1.

**To execute:**

1. Delete the empty `terraform/` folder; create `terraform-live/` and `terraform-modules/` as in §6.
2. `terraform-live/sandbox/bootstrap/`: S3 state bucket (versioning, SSE-KMS, public access blocked,
   `use_lockfile = true`). Applied once with local state, then the state is migrated into the bucket it
   just created (add the `backend "s3"` block, `terraform init -migrate-state`) — this is the documented
   chicken-and-egg exception. **The state file is never committed**: state carries account IDs and
   resource ARNs, which do not belong in the Git history of a repository hosted on GitHub.
3. Same for `terraform-live/production/bootstrap/` and `terraform-live/identity/bootstrap/`.
4. Migrate every subsequent slice to the remote backend.
5. `terraform-live/identity/`: import the permission sets, groups and assignments created by hand in
   Stage 1, so identity stops being console-managed (D10). Applied with the `awsds-infra-identity`
   profile. `terraform plan` must come back empty after the import — that is the check that the import
   is faithful.
6. Repository hygiene: `.gitignore` for `.terraform/` and `*.tfstate.backup`; `.terraform.lock.hcl` is
   committed on purpose; `pre-commit` with `terraform fmt`, `terraform validate` and `tflint`; and
   **`checkov` as a required gate, not an optional one** — a policy check that can be skipped is a policy
   check that will be skipped on the day it would have mattered.
7. First reusable modules in `terraform-modules/`: `s3-bucket`, `iam-role`, `kms-key`. The `s3-bucket`
   module enables **S3 Bucket Keys** by default (§5) and blocks public access unconditionally; the
   `iam-role` module takes a permissions boundary as a required argument, so omitting one has to be
   deliberate. Tag every module release; callers pin the tag (§6).
8. **Teardown/rebuild tooling (D11).** Each slice declares its layer (`[P]`/`[D]`/`[E]`), and a `Makefile`
   at the repository root exposes `make up ENV=sandbox` / `make down ENV=sandbox`: `down` destroys the
   `[E]` slices in reverse dependency order and stops the `[D]` instances; `up` starts the `[D]` instances
   and applies the `[E]` slices. Both must refuse to touch `[P]` slices. Add `make status` to report what
   is currently running and the estimated hourly burn.
9. **No region literals (§4.1).** `var.region` in every slice, AZs from `data.aws_availability_zones`,
   AMIs from SSM public parameters. A `grep` check in CI that fails on a hardcoded region keeps this
   honest at no cost.
10. Update `README.md` with the repository layout and the AWS resource structure (required by `CLAUDE.md`).

**Deliverables:** `terraform apply` works end-to-end against the Sandbox account using an SSO profile;
the `Makefile` exists with the slice-to-layer table wired up, even though no `[E]` or `[D]` slice exists
yet — `make down` at this point must be a safe no-op, not a command that reaches the `[P]` bootstrap slice.

**Validation:** destroy and re-create a throwaway `[E]` slice to prove reproducibility, and confirm
`make down` leaves `bootstrap/` untouched.

---

### Stage 3 - Networking (Sandbox **and Production**)

**Objective:** the private networks that everything else sits in.

**Prerequisites:** Stage 2.

**Scope change (D14):** this stage now builds the Production VPC as well, not just the Sandbox one. It has
to: GitLab lives in Production (Stage 7) and cannot be built before its network exists. The VPC layer is
free at rest, so there is no cost argument for deferring it, and using the same module for both accounts on
the same day is how the modules get proven.

**To execute:**

The network is split across two slices per account, because the free half and the metered half have
different lifecycles (§5.1).

*`foundation/` — layer `[P]`, costs nothing at rest, never destroyed:*

1. `terraform-modules/vpc/`: VPC (`10.20.0.0/16` sandbox, `10.30.0.0/16` production — non-overlapping,
   because they will be peered), 2 AZs, public + private + isolated (data) subnets. Applied to **both**
   accounts.
2. Internet Gateway, route tables, NACLs, baseline security groups.
3. S3 and DynamoDB **gateway** endpoints — these are free, so they live here.
4. Route 53 private hosted zone per account (e.g. `sandbox.internal`, `prod.internal`), plus the private
   zone that resolves the D15 public domain names to internal addresses (split-horizon DNS).
5. VPC Flow Logs to CloudWatch Logs with a short retention (a few days — retention is what costs).
6. **Sandbox ↔ Production VPC peering.** The requester lives in `sandbox/foundation/`, the accepter in
   `production/foundation/` (a provider alias, cross-account). Routes are added **per subnet, not per VPC**:
   the Sandbox private subnets reach only the Production subnet holding GitLab and the endpoints, and
   security groups reference the peer CIDR explicitly. Peering is a network path between an account where
   people experiment and the account that runs production — it earns a narrow route table, not a
   convenient one. This is also the path the VPN uses to reach GitLab (Stage 4).

*`egress/` — layer `[E]`, destroyed at the end of every session:*

7. NAT Gateway — a single one, with a documented switch for one-per-AZ. **Built behind the D5 switch:**
   under egress design B (§4.3) the SageMaker subnets get no NAT route at all, so this resource is
   conditional, not assumed.
8. Interface VPC endpoints, added on demand per stage. The working list, corrected — the previous version
   of this plan was missing three that Studio and D5(B) require:
   `sts`, `logs`, `ecr.api`, `ecr.dkr`, `sagemaker.api`, `sagemaker.runtime`, **`sagemaker.studio`**
   (required for JupyterLab/CodeEditor apps in a VPC-only domain — Studio simply does not work without
   it), `elasticfilesystem`, **`kms`**, and under D5(B) **`codeartifact.api`** and
   **`codeartifact.repositories`**. Default to a single AZ during lab sessions (D9) — at ~USD 0.01/h per
   endpoint per AZ, two AZs doubles the largest hourly line item. A resource in the other AZ still resolves
   the endpoint DNS and reaches it; the cost is cross-AZ traffic and the loss of AZ redundancy, neither of
   which matters in a lab.
9. **Endpoint policies — the trusted-networks axis of §4.2.** Every interface and gateway endpoint carries
   a policy restricting it to resources within the organization (`aws:PrincipalOrgID` / `aws:ResourceOrgID`).
   Without this, the S3 gateway endpoint is a private, unlogged, unmetered path to *any* bucket on the
   internet, including someone's personal one — which is the exact failure mode the whole DLP objective is
   about. Free. Take the policy shapes from the `data-perimeter-policy-examples` repository (§4.2) rather
   than writing them by hand — the service carve-outs are the part everyone forgets.
10. Keep this slice's route-table associations parameterised, so D5 (Stage 6) can insert a firewall or
    proxy into the egress path, or remove it entirely under design B, without reshaping the foundation.

**Deliverables:** both VPCs applied by Terraform from the same module; flow logs visible; endpoints
resolving privately; peering reachable in the intended direction and *not* reachable outside the permitted
subnets; an attempt to reach an out-of-organization S3 bucket through the gateway endpoint denied; and
`make down` followed by `make up` restoring egress without touching either VPC.

**Cost note:** this is where the metered bill starts, and `egress/` is the single biggest hourly cost of the
lab: ~USD 0.14/h with 9 endpoints and a NAT in one AZ; ~USD 0.11/h under design B — no NAT, but the two
CodeArtifact endpoints bring the count to 11. Keep the endpoint list minimal — every entry is a permanent
hourly charge for the whole session.

---

### Stage 4 - VPN access

**Objective:** the only human path into the private network.

**Prerequisites:** Stage 3. D4 is decided: self-managed WireGuard.

**To execute:**

1. `terraform-modules/wireguard/`: `t4g.nano` (ARM, Amazon Linux 2023) in a public subnet, WireGuard
   installed and configured by user data, IP forwarding and NAT (masquerade) enabled. **NAT is not
   optional** — a correction to the previous version, which mixed a NAT model with a routed one: VPC
   peering does no edge-to-edge routing and only forwards packets whose source and destination sit inside
   the two VPCs' CIDRs, so the WireGuard client range can never cross the peering to Production. Every
   packet the instance forwards must carry its own private IP, which also means security groups admit the
   WireGuard instance's SG (referencing a peer VPC's security group works across a same-region peering),
   never the client CIDR.
   Layer `[D]`: the instance is **stopped** between sessions, not destroyed (~USD 0.65/month of EBS),
   which keeps the host key and the peer configuration stable.
2. Elastic IP allocated in the `[P]` foundation slice and re-associated on start, so the endpoint address
   survives a teardown and client configs never have to be regenerated. ~USD 3.65/month — the price of not
   editing every client config on every rebuild.
3. Security group allowing only UDP/51820 inbound; SSH access only through SSM Session Manager, never
   port 22 from the internet.
4. Peer public keys supplied through a git-ignored `.tfvars` (keys are generated on the client and the
   private key never leaves the laptop). One peer per person and per device.
5. **Full tunnel, not split** — a correction to the previous version, forced by step 8: the client routes
   `0.0.0.0/0` through WireGuard, so AWS API and console traffic exits through the instance's Elastic IP
   and the `aws:SourceIp` condition can match it. A split tunnel routing only the two VPC CIDRs would
   leave every API call on the laptop's own connection — and step 8 would then deny the user everything,
   tunnel up or not. The cost of full tunnel is that ordinary browsing also transits the instance and
   bills as EC2 data transfer out (~USD 0.09/GB): connect for lab sessions, not as an always-on VPN.
   Reaching GitLab in Production still works through the Stage 3 peering (NATed by step 1). `DNS` in the
   client config points at the VPC resolver (`.2` of the Sandbox VPC CIDR) so private hosted zones and
   VPC endpoints resolve.
6. No return routes for the WireGuard peer network exist anywhere — with NAT on the instance (step 1) the
   VPCs only ever see the instance's private IP, and across the peering such a route would be dropped
   anyway (edge-to-edge, again). What is actually needed: Production's route back to the **Sandbox VPC
   CIDR** through the peering (already built in Stage 3), and security groups on GitLab, EFS and the
   endpoints that admit the WireGuard instance's SG or IP.
7. CloudWatch agent shipping the WireGuard handshake log; alarm if the instance is unhealthy.
8. **Close the other half of the objective: restrict the AWS control plane to the VPN.** `CLAUDE.md` says
   "all user access to the cloud infrastructure will be performed through a VPN", and a tunnel to the VPC
   only delivers the data plane — the console and the AWS APIs remain reachable from any network in the
   world with a valid SSO session. Add a deny with `NotIpAddress` on the WireGuard Elastic IP **combined
   with `aws:ViaAWSService: false`** to the permission sets in `terraform-live/identity/` — the second
   condition is not optional: services calling on the user's behalf (Athena reaching S3 is this plan's
   first casualty) do not carry the user's source IP, and a bare `aws:SourceIp` deny breaks them. Add the
   same condition pair on `sagemaker:CreatePresignedDomainUrl` so a Studio URL cannot even be minted from
   outside the tunnel. This restriction is what step 5's full tunnel exists for.
   Two cautions, both of which have locked people out before: apply it to the `data-scientists` and
   `managers` permission sets first and to `AdministratorAccess` only once it demonstrably works, and note
   that this pins access to a single Elastic IP — which is precisely why that IP lives in `[P]` (D4).
   Break-glass (D16) is the way out if this goes wrong.
9. Write the client setup instructions in `README.md`, including how to regenerate the config after a
   rebuild.

**Deliverables:** connecting from the laptop gives private access to a test resource in **both** accounts;
the same resource is unreachable with the tunnel down; an AWS API call with the tunnel down is denied for
the sandbox user **and the same call with the tunnel up succeeds** — the pair that proves the
full-tunnel/`aws:SourceIp` wiring; `make down` followed by `make up` restores connectivity without
changing the client configuration.

**Known trade-off (D4):** no Identity Center integration — revoking a person's access means removing their
peer and re-applying. Acceptable for a single-operator lab, and the reason AWS Client VPN stays documented
as the alternative.

---

### Stage 5 - Data foundation (S3, NFS, Glue, Iceberg, Lake Formation)

**Objective:** where data lives and how it is catalogued.

**Prerequisites:** Stage 3.

**To execute:**

Like Stage 3, this stage spans two slices with different lifecycles: the data itself never goes away, the
filesystem in front of it does.

*`data/` — layer `[P]`, and the KMS CMKs it uses live in `foundation/`:*

1. KMS CMKs per data domain; S3 buckets `raw`, `curated`, `artifacts`, `athena-results`, `logs` with
   versioning, encryption, **S3 Bucket Keys** (§5), lifecycle rules, `prevent_destroy`, and a bucket policy
   that denies access not coming through the VPC endpoint (`aws:SourceVpce`) — the resource-side half of
   the trusted-networks axis in §4.2, complementing the endpoint policies from Stage 3. **The deny must
   carry the `aws:ViaAWSService` carve-out**, or it blocks Athena and Lake Formation vended access — the
   exact path D13 forces all tabular reads through; a bare `aws:SourceVpce` deny makes step 6 unusable.
   Take the policy shape from `data-perimeter-policy-examples` (§4.2). While in the bucket policy, add a
   `s3:signatureAge` cap: it bounds the lifetime of any presigned URL, the preventive counterpart of the
   detection Stage 11 sets up.
2. **Define the data classification scheme before defining LF-Tags.** LF-Tags are the mechanism; the
   classification is the decision — which levels exist (e.g. public / internal / restricted / personal),
   who owns the assignment, and what each level permits. Writing the tags first produces a taxonomy shaped
   by whatever the first table happened to contain, and Stage 11's Macie findings then have nothing to map
   onto. This is the smallest piece of real data governance in the plan and it costs nothing but thought.
3. Glue Data Catalog databases (`raw`, `curated`); Glue crawlers only where they earn their keep.
4. Iceberg tables on S3, queried through Athena; Athena workgroup with a result bucket and a per-query
   data scan limit (cost guardrail). **Table maintenance gets an owner on day one**: scheduled `OPTIMIZE`
   (compaction) and `VACUUM` (snapshot expiry) through Athena, or Glue's automatic compaction — an
   Iceberg table nobody compacts degrades quietly and pays storage for every dead snapshot. **Amazon S3
   Tables** — managed Iceberg with automatic maintenance and Lake Formation integration — is the
   AWS-native alternative, deliberately not used here: D13's registered/unregistered prefix split leans
   on general-purpose buckets. Recorded in §11.
5. Enable Lake Formation as the permission model for the catalog; register the S3 locations; apply the
   LF-Tags from step 2.
6. **Implement D13 — make Lake Formation enforceable.** Split the buckets into *registered* prefixes
   (governed by Lake Formation, tabular data) and *unregistered* prefixes (scratch, artifacts, model
   outputs, Athena results, governed by plain IAM). The SageMaker execution role and the
   `DataScientistAccess` permission set get **no `s3:GetObject` on the registered prefixes** — tabular
   access goes through Athena, Glue interactive sessions or EMR runtime roles, which ask Lake Formation.
   This is the step that decides whether the fine-grained access control objective in `CLAUDE.md` is a
   control or a decoration, and it has to happen here, because Stage 6 writes the execution role.
   Record any exception through Lake Formation **hybrid access mode** rather than by quietly widening the
   role.

*`nfs/` — layer `[P]`, reclassified in the third review: mount targets are free, and EFS storage with a
lifecycle policy to Infrequent Access is ~USD 0.016/GB-month — cents at lab scale:*

7. EFS filesystem + mount targets in the private subnets, access points per group; this is the NFS layer
   shared between users and SageMaker. Enable the lifecycle policy (transition to IA after 30 days).
   S3 ↔ EFS movement is an explicit copy in code when a dataset needs to cross — no standing
   synchronisation machinery (DataSync would cost per GB moved, and there is no teardown left to protect
   against).
8. **Access from the user's own machine**, which `CLAUDE.md` asks for ("exchange files between users, the
   SageMaker environment and S3"): NFSv4 over the WireGuard tunnel, TCP/2049 allowed from the VPN peer
   CIDR, using the EFS mount helper with TLS. Two caveats to state rather than discover: throughput over a
   VPN is poor enough that this is for exchanging files, not for working off; and **EFS has no mapping
   between POSIX UIDs and SSO identities**, so "who wrote this file" is not auditable. EFS Access Points
   pin a UID/GID per group, which bounds the problem to the group level — good enough for a lab, and named
   in §11 as a real gap for an institution.
9. **S3 is the source of truth for data; the filesystem itself now persists.** An earlier version had the
   EFS `[E]` with a sync-to-S3 step inside `make down` — and correctly called that sync the single most
   likely way to lose real work in this design. Persistence removes the failure mode outright, for cents;
   `make down` does not touch the filesystem at all.

**Deliverables:** a sample Iceberg table written and queried through Athena, with access granted through
Lake Formation rather than raw IAM policies; **a demonstration that the same table cannot be read by
pointing pandas at its S3 path** — which is the only convincing evidence that D13 holds; **a demonstration
that Athena still works with the bucket policy attached** — the evidence that the `aws:ViaAWSService`
carve-out is wired correctly; and a `make down`/`make up` cycle that provably leaves EFS content
untouched.

---

### Stage 6 - SageMaker Studio (Sandbox)

**Objective:** the data scientist's working environment.

**Prerequisites:** Stages 3, 4, 5, and the ECR/CodeArtifact repositories from Stage 7 step 5 — **pulled
forward**, because under egress design B they are how packages arrive, so they cannot come after the thing
that consumes them. **D5 is executed, not decided, in this stage**: both designs get built (§4.3).

**To execute:**

1. SageMaker Studio domain in **VPC-only** mode, in the private subnets, with the interface endpoints
   from Stage 3 — including `sagemaker.studio`, without which the domain will not start.
2. Execution roles per user profile, honouring **D13**: no `s3:GetObject` on Lake Formation-registered
   prefixes. Map user profiles to the Identity Center users.
3. **Lock down what the notebook can create, not just what the domain can reach.** A VPC-only domain
   constrains Studio itself; it does not constrain training, processing or transform jobs launched from a
   notebook through the API, which accept their own network configuration and will happily run outside the
   VPC. Add IAM conditions to the execution role and the permission set:
   `sagemaker:VpcSubnets` and `sagemaker:VpcSecurityGroupIds` (deny when null), `sagemaker:NetworkIsolation`,
   `sagemaker:InterContainerTrafficEncryption`, `sagemaker:VolumeKmsKey`. Add `sagemaker:InstanceTypes` as
   well: it is the only control that actually stops a USD 30/hour GPU instance from being started by a
   misplaced parameter, and idle-shutdown does not help within the first hour. Without this step, the
   entire VPC-only design is one API call away from being bypassed.
4. **Build egress design A (§4.3):** NAT route plus Route 53 Resolver DNS Firewall with an explicit
   allowlist (PyPI, CRAN, the Julia package server, crates.io, the distro mirrors, the GitLab host).
   Everything else denied and logged.
5. **Build egress design B (§4.3):** the same domain with no NAT route at all; packages from CodeArtifact
   (cross-account from Production, per D14 — a CodeArtifact domain policy grants the Sandbox account) and
   images from ECR pull-through cache. Julia, R and the Rust toolchain arrive pre-installed in the dev-env
   image rather than through a proxy.
6. **Compare them and write the verdict** (the deliverable in §4.3): measured hourly cost, what breaks in a
   normal session, how long the "I need package X right now" loop takes, and what a deliberate
   exfiltration attempt achieves under each. Then choose, and record the choice as the closure of D5.
7. Attach EFS access points for the shared NFS area.
8. Lifecycle configuration for idle shutdown — mandatory cost control.
   **Layers, corrected in the third review: the domain and its user profiles are `[P]`; only the apps are
   `[E]`.** A domain at rest bills nothing — charges are per running app plus home-filesystem GBs — so
   destroying it each session bought nothing and created two problems: the orphaned-home-EFS hazard (the
   `RetentionPolicy` default is `Retain`, so every teardown left a billing filesystem behind unless it was
   deleted explicitly) and the churn of domain ID, user profiles and Identity Center mappings on every
   `make up`. `make down` now deletes running *apps* only and leaves the domain alone. **Studio home
   directories are scratch** by policy: notebooks live in GitLab, data lives in S3, shared files live on
   the Stage 5 EFS — and the home directories stay small, so their storage rounds to cents. State this to
   users explicitly.
9. CloudWatch log groups and metrics for the domain.

**To verify rather than assume:** whether a Studio custom image can be pulled from the **Production**
account's ECR (D14) — the BYOI documentation is strict about region and thin on cross-account; if it
fails, the fallback is a native ECR cross-account replication rule into a Sandbox repository, not a
pipeline. And whether SageMaker Studio offers any supported way to disable file
download or notebook export from the JupyterLab UI. As far as this plan knows it does not, and Stage 11
step 3 should not be written as though the control exists. If it does not, the honest position is that
preventing a determined user from taking data out through their own browser session requires a different
architecture (streaming desktop, or no direct data access at all), and everything else is detection.

**Deliverables:** the sandbox SSO user logs in through the VPN, opens Studio, installs a package, reads an
Iceberg table through Athena, writes to EFS — and cannot reach a non-allowlisted site under design A, nor
any site at all under design B. Plus the written comparison of the two.

**Note on the product direction:** this stage builds the current generation of SageMaker Studio
(JupyterLab / Code Editor apps — *not* the deprecated "Studio Classic"). Since 2024 AWS has been
consolidating on **SageMaker Unified Studio** with SageMaker Catalog/Lakehouse, which is what a large
institution starting today would evaluate first — it bundles the governance layer this plan assembles by
hand from Lake Formation, LF-Tags and Glue. It is deliberately not used here: it carries a heavier baseline
(a DataZone domain and its own projects/accounts model) than a USD 50/month lab supports, and the
hand-assembled version teaches more about the mechanics underneath. Recorded in §11.

---

### Stage 7 - GitLab, Runners and ECR

**Objective:** source control, docs hosting and a container registry, all private, **all in the Production
account** (D14).

**Prerequisites:** Stages 3 (which now builds the Production VPC), 4; decisions D8, D14, D15.

**Note on ordering:** step 5 (ECR and CodeArtifact) is pulled forward and applied before Stage 6, because
under egress design B it is how packages reach SageMaker. The rest of this stage stays here.

**To execute:**

1. GitLab CE Omnibus on EC2 in a **Production** private subnet; EBS with a snapshot schedule; an internal
   ALB in front — **layer `[E]`, in `production/egress/`**, correcting the previous version, which put it
   in the `[D]` tooling slice: an ALB cannot be stopped, it bills (~USD 0.023/h) for as long as it exists,
   so it is destroyed with the session and rebuilt by `make up` (target group, listener and certificate
   attachment are plain Terraform; the private DNS name hides the recreation). Route 53 record in the
   private zone. Reached from the laptop over the VPN through the Stage 3 peering.
   **Layer `[D]` (dormant), decided up front.** GitLab holds real state — repositories, CI history,
   registry metadata — and rebuilding it from a backup on every session is exactly the kind of fragile
   daily dependency §5.1 rule 2 warns about. So the instance and its EBS volume are **stopped**, not
   destroyed: ~USD 4/month idle, ~3-5 minutes to boot. Always-on would be ~USD 60/month, which the
   USD 50 ceiling (D12) rules out.
   Backups are still mandatory, but as disaster recovery rather than routine operation: scheduled
   `gitlab-backup create` to a `[P]` S3 bucket, plus `gitlab-secrets.json` in Secrets Manager — without
   that file a restored backup cannot decrypt its own data. Test the full backup → destroy → restore cycle
   once, so the recovery path is known to work.
   Instance type per D8: `t4g.large` (ARM, 8 GB). Point GitLab's object storage (artifacts, LFS, uploads,
   registry) at S3 rather than at the EBS volume — it keeps the volume small and puts the bulky, valuable
   data in a `[P]` bucket that is versioned and lifecycle-managed.
2. **TLS per D15**, correcting an error in the previous version of this plan: an ACM certificate cannot be
   issued for `sandbox.internal` or any other private-only name, because public certificates require
   public domain validation. Register the chosen domain, keep a public hosted zone for DNS validation only,
   issue a public ACM certificate (wildcard, for Pages), attach it to the **internal** ALB, and resolve the
   names privately. Nothing is published; the public zone contains validation records and nothing else.
3. SAML integration between GitLab and IAM Identity Center, so GitLab has no local accounts. **A caveat
   the previous version missed: SAML *login* works in GitLab CE, but SAML group sync is a paid-tier
   (Premium) feature.** GitLab group membership is therefore maintained by hand — acceptable at three
   users — with group names mirroring the Identity Center groups 1:1, so the Stage 8 approval gate is
   driven by the same identity names and a future upgrade to group sync changes nothing visible.
4. GitLab Pages enabled for documentation, reachable only through the VPN. Pages requires a **domain
   distinct from the GitLab host** (it serves user-supplied content, so sharing the origin would hand it
   the GitLab session cookie) and a **wildcard DNS record plus wildcard certificate** — both provided by
   D15, which is why that decision has to be made before this stage.
5. **Registries, in `production/data/`, layer `[P]` — applied early (before Stage 6):**
   ECR repositories `dev-env` (SageMaker images) and `app/*` (application images), with lifecycle policies
   to expire untagged images and **ECR enhanced scanning** enabled; an **ECR pull-through cache** rule for
   the upstream public registries; and a **CodeArtifact** domain with repositories per ecosystem, each
   configured with an upstream to the public registry. Both carry a resource policy granting the **Sandbox**
   account pull/read access, and the KMS key policy has to grant Sandbox too — the direction of sharing is
   the reverse of the previous plan, because the registries moved. §4.3 records which ecosystems
   CodeArtifact does not cover and what happens to them instead. Whether SageMaker Studio actually accepts
   the `dev-env` image cross-account is verified in Stage 6; the fallback is an ECR replication rule into
   a Sandbox repository.
6. GitLab Runners in `production/runners/`, layer `[E]`: autoscaling on EC2 or Fargate, in the private
   subnet, with an instance role that can push to ECR. Container builds with Kaniko or BuildKit (no
   privileged Docker-in-Docker). Runners hold no state worth keeping, so they are rebuilt every session.
   The runners need egress to fetch public dependencies while building the dev-env image — that is the one
   place internet access is legitimate under both egress designs, and it belongs to the build account, not
   to the notebook.
7. Decide and document the mirroring policy between this GitHub repository and GitLab.
8. Add GitLab start/stop to `make up` / `make down`, and measure the boot time — if it turns out to be
   much worse than the ~3-5 minutes assumed in D8, revisit the layer choice (§5.1 rule 7).

**Deliverables:** a repository pushed to GitLab over the VPN, a pipeline running on a private runner, an
image in ECR pulled successfully **from the Sandbox account**, and a docs site served by Pages over HTTPS
with a valid certificate.

---

### Stage 8 - CI/CD pipelines (the three types)

**Objective:** the automation described in `CLAUDE.md`.

**Prerequisites:** Stage 7.

**To execute:**

1. **Development-environment pipeline:** builds the Docker image used by data scientists, pushes it to ECR
   and registers it as a SageMaker custom image / app image config. Triggered by tags.
   Under D5(B) this pipeline carries more weight than it looks: it is where Julia, R and the Rust toolchain
   are installed, so it is the dependency delivery mechanism for every ecosystem CodeArtifact does not
   cover (§4.3). Its rebuild time is therefore a usability metric, not just a CI metric — measure it.
2. **Application build pipeline:** the `app-etl` template from `CLAUDE.md` — `uv` for dependencies,
   `pytest` for tests, linting, docs build published to Pages, Docker image pushed to ECR on tag.
3. **Production deploy pipeline:** no static keys — but **not GitLab OIDC federation either, correcting
   the previous version**: to validate a job's ID token, IAM/STS fetches the issuer's discovery document
   and JWKS over the public internet, and a VPN-only GitLab (D8/D14) serves neither. The mechanism is a
   **dedicated deploy runner with an EC2 instance profile** — the runner's role *is* the deploy
   credential, no token exchange — locked to protected branches/tags and a protected environment, so an
   ordinary CI job never schedules onto it. Promote the image, run `terraform apply` for
   `terraform-live/production/app/app-etl/` pinned to the application tag, with a manual approval gate
   assigned to the `managers` group. OIDC remains the target design if a minimal public surface ever
   exists (exposing only `/.well-known/openid-configuration` and the JWKS path through a public ALB —
   plausible at Stage 13); §11 records it.
   **Note the consequence of D14:** the deploy runner and its target are in the same account, so there is
   no cross-account boundary protecting Production from a
   compromised runner. Compensate with what is available inside one account: a deploy role scoped to the
   `app/*` slices only, `terraform plan` output attached to the approval, and CloudTrail alarms on any use
   of the deploy role outside a pipeline context. §11 records the account split an institution would use
   instead.
4. **Security gates in every pipeline:** `checkov` on Terraform, ECR enhanced scanning results blocking a
   promotion on critical findings, and dependency scanning on the application. A gate that only warns is
   documentation, not a gate — decide explicitly which findings block.
5. A pipeline for this infrastructure repository as well: `fmt` / `validate` / `plan` on merge requests,
   `apply` gated by approval. This repository lives on GitHub (§1), so that pipeline is either GitHub
   Actions — with its own OIDC role into AWS; GitHub's issuer *is* public, so federation works there — or
   it runs on the GitLab mirror from Stage 7 step 7. Decide alongside the mirroring policy.

**Deliverables:** a version tag on `app-etl` flows automatically from source to a running artifact in
Production, with one human approval; and a build with a known-vulnerable dependency is stopped by the gate.

---

### Stage 9 - Production data platform and cross-account sharing

**Objective:** the production data platform, and controlled sharing with the sandbox.

**Prerequisites:** Stages 3, 5, 8.

**Scope change (D14):** the Production *networking* moved to Stage 3 and the *registries* to Stage 7, both
because GitLab needed them earlier. What remains here is the data platform and the sharing model — which
is the interesting part anyway.

**To execute:**

1. Apply the `data/` slice in the Production account using the same modules as Stage 5 (different bucket
   names, tighter policies), including D13's registered/unregistered prefix split.
2. Lake Formation cross-account sharing: production catalog resources shared read-only with the sandbox
   account for the `data-scientists` group; nothing flows the other way except through the deploy pipeline.
   Note that cross-account Lake Formation sharing goes through AWS RAM and has its own version-dependent
   behaviour around resource links and `IAMAllowedPrincipals` — verify the grant actually restricts rather
   than assuming it, using the same "read it with pandas" test as Stage 5.
3. Cross-account IAM: the deploy role, the KMS key grants.
4. **Verify the boundary rather than declare it.** Confirm from a sandbox session that: production
   infrastructure cannot be changed; a production table can be read but not written; a write to an S3
   bucket outside the organization is denied (§4.2); and the GitLab/ECR reach into Production granted in
   Stage 1 step 7 does not extend to anything else in that account. Each of these is a test, with its
   result recorded.

**Deliverables:** the sandbox user reads a production table from Studio and is denied on write; the four
verifications above pass and are written down.

---

### Stage 10 - Workflow orchestration and promotion

**Objective:** take a workflow developed in SageMaker and run it in production on a schedule.

**Prerequisites:** Stages 8, 9. **D7 is taken at the start of this stage**, once a real application
finally needs scheduling — that is the point at which the MWAA-versus-Step-Functions trade stops being
abstract.

**To execute:**

1. Implement the chosen orchestrator (SageMaker Pipelines, a Step Functions module, or an MWAA environment).
2. Define how a SageMaker-developed pipeline becomes a deployable artifact — most likely a container plus
   a workflow definition, both versioned in the application repository.
3. Schedule, retry, alerting on failure to CloudWatch/SNS.
4. If MWAA is used, document how to create and destroy it on demand to avoid the idle cost.
5. **Close the notebook-to-production gap for models, not just for ETL.** The CI/CD in Stage 8 promotes a
   container; that covers the `app-etl` template in `CLAUDE.md` but not the other thing a data science
   environment produces, which is a trained model. Define, even minimally: the **SageMaker Model Registry**
   as the promotion boundary (a model version is approved, not a file copied), how a registered model is
   served (batch transform or an endpoint), and what is recorded about it — training data version, metrics,
   owner. Without this, "data science environment" means "notebooks with a nice network", and the whole
   promotion story only works for code.

**Deliverables:** a workflow developed in the sandbox runs on schedule in production without manual steps,
and a model trained in the sandbox reaches production through the registry rather than by being copied.

---

### Stage 11 - Data protection and DLP

**Objective:** the protection layer, built on top of a working environment rather than before it.

**Prerequisites:** Stages 5, 6, 9; decision D6.

**To execute:**

**What is no longer in this stage:** the data perimeter (§4.2) moved to Stage 1 and Security Hub, GuardDuty
and Access Analyzer moved there with it (principle 9). What remains here is genuinely data-specific.

1. Amazon Macie for sensitive-data discovery on the S3 buckets; findings to Security Hub; results mapped
   onto the classification scheme defined in Stage 5 step 2. **Scope it to a sampled prefix** — Macie bills
   per GB inspected and can dwarf every other line item in §5.
2. Lake Formation column-level and row-level filters driven by the LF-Tags from Stage 5, enforceable
   because of D13.
3. Egress hardening review of Stage 6, once D5 has been closed by the comparison in §4.3.
   **Correction:** the previous version of this plan listed "block SageMaker Studio file download /
   notebook export" as a control. Verify it exists before relying on it (Stage 6 flags the same doubt) —
   as far as this plan knows, Studio has no supported setting for that. If it does not, say so plainly in
   the threat model rather than leaving a control listed that nobody implemented.
4. Turn on GuardDuty's **S3 Protection and Malware Protection** — deferred from Stage 1 specifically so the
   decision could be made against a real bill (§5).
5. CloudTrail data events on the sensitive buckets; CloudWatch alarms for exfiltration patterns: mass
   `GetObject`, unusual egress volume, `PutObject` to an unexpected destination.
   **Correction:** the previous version listed an alarm on "presigned URL creation". That is not
   detectable — signing a presigned URL is a local SigV4 operation against credentials already held, it
   makes no API call and appears nowhere in CloudTrail. What *is* detectable is the **use** of one, which
   shows up as a request whose authentication method differs from a normal SigV4 call. Alarm on that.
6. Only then evaluate whether a third-party DLP agent adds anything the above does not cover.

**Deliverables:** a documented threat model with the control that addresses each item — and, for the items
where no control exists, an explicit statement that the risk is accepted rather than a control that was
never built; alarms that fire on a simulated exfiltration attempt.

---

### Stage 12 - Observability, governance and FinOps

**Objective:** know what is running, what it costs, and be told when something breaks.

**Prerequisites:** any stage that created resources.

**To execute:**

1. CloudWatch dashboards per environment (SageMaker, GitLab, VPN, NAT traffic, Athena scans).
2. Alarms → SNS → e-mail for: budget thresholds, failed pipelines, VPN down, GitLab unhealthy,
   unusual data scans.
3. Log retention policies everywhere (default retention is "forever", which quietly costs money).
4. Cost allocation tags activated in Billing; a monthly cost review against §5.
5. **Review the `[P]`/`[D]`/`[E]` assignments against the real bill**, which by this point exists. The two
   estimates most likely to be wrong are the interface endpoints (the largest hourly item) and GitLab
   (the largest idle item). Update §5 and §5.1 with measured numbers rather than the projections.
6. Config rules / conformance packs on top of the Control Tower guardrails; review the recorder scope set
   in Stage 1 step 14 against what the bill actually shows.
7. Tighten the permission sets in `terraform-live/identity/` against real usage, using **IAM Access
   Analyzer unused-access findings** — which is a better instrument than review, because it reports
   permissions that were granted and never exercised.
8. **Backup and recoverability**, which no earlier stage owns: an org-wide **AWS Backup** plan through an
   Organizations backup policy, covering the EBS volumes of the `[D]` instances and the EFS filesystem;
   **Vault Lock** on the backup vault so a compromised administrator cannot delete the backups; and
   cross-region copies for the state buckets and the GitLab backup. Then state the numbers the plan has so
   far avoided: what the recovery time objective actually is for GitLab, for the Terraform state, and for
   the data lake, and test each one at least once. An untested backup is a hypothesis.
9. Review **Service Quotas** for the services in use, and set CloudWatch alarms on the ones that would
   silently break a session (SageMaker instance limits, EIPs, VPC endpoints).

---

### Stage 13 - Public-facing web tier (experiment)

**Objective:** the experiment described in `CLAUDE.md` — a public web server reaching a private backend.

**Prerequisites:** Stages 3, 9.

**To execute:**

1. Public ALB in the public subnets with WAF and an ACM certificate; a public Route 53 hosted zone.
2. Application on ECS Fargate in the private subnets; database (RDS or the Iceberg catalog through Athena)
   in the isolated subnets.
3. Security groups allowing only ALB → app → data, and nothing else.
4. Document the blast radius and how to tear the whole tier down.

---

## 8. Cross-cutting work (continuous, not a stage)

- `LOG.md`: the user records every manual step (never edited by Claude).
- `CLAUDE.md` → `Claude LOG`: updated at the end of each stage, referencing the stage number from this plan.
- `REFERENCES.md`: every link used as a reference.
- `README.md`: kept in sync with the real resource structure and repository layout.
- `GENERAL_PLAN.md`: revised whenever a decision changes or a stage is re-scoped.
- The **Well-Architected Machine Learning Lens** is the per-stage checklist: when a stage is built, walk
  its questions for the components the stage touched — it is to this environment what the SRA is to the
  account structure.

---

## 9. Open questions

**Resolved on 2026-08-07:** region → `us-west-2` (D1); Control Tower account e-mails → registered in
`secrets/accounts.md`; VPN → WireGuard (D4); DLP → native AWS combination (D6); lifecycle → resources
ephemeral, accounts permanent (D11); budget → USD 50/month (D12); Identity Center administration →
delegated to a dedicated Identity account (D10).

**Resolved on 2026-08-07 (second review):** D5 → both egress designs are built and compared in Stage 6
(§4.3); D13 → Lake Formation enforcement model; D14 → GitLab, Runners, ECR and CodeArtifact live in the
Production account; D15 → a public domain plus split-horizon DNS for internal TLS; D16 → break-glass access.

**Still open:**

1. **Which domain name to register (D15).** The one input needed from the user. Not blocking Stage 1, but
   blocking Stage 7, and worth doing early since registration and validation take time.
2. **D7 - Production orchestrator.** Decided at Stage 10. Keep application entry points as plain containers
   so any of the four options remains viable.
3. **AZ name-to-ID mapping across accounts.** AWS maps AZ names to physical datacenters independently per
   account, so `data.aws_availability_zones` indexed by position can place "the same" AZ in different
   datacenters in Sandbox and Production — which turns peering traffic that looks intra-AZ into
   cross-AZ traffic at USD 0.01/GB each way. **D14 made this concrete rather than theoretical:** the VPN,
   SageMaker and GitLab now talk across the peering constantly. Check it in Stage 1 step 16
   (`aws ec2 describe-availability-zones --query 'AvailabilityZones[].[ZoneName,ZoneId]'` under each
   profile). If the mappings differ, Stage 3 anchors subnets on `zone_ids` (`usw2-az1`, passed per
   environment in `.tfvars`) instead of on list position, and §4.1 is updated accordingly.
4. **Layer assignments.** `[P]`/`[D]`/`[E]` are cost judgements based on estimates. Revisit them at Stage 12
   against the real bill — especially the interface endpoints (the largest hourly item, now ~9 of them)
   and GitLab (the largest idle item).
5. **CodeArtifact ecosystem coverage (§4.3).** Narrowed by the third review: the CodeArtifact
   documentation now lists Cargo among its supported formats, so the Rust question is down to confirming
   it in practice at Stage 6. Julia and R remain genuinely uncovered and keep their §4.3 fallbacks — they
   are what decides whether egress design B is livable.
6. **Whether SageMaker Studio can block file download** (Stage 6). If not, Stage 11's threat model has to
   record an accepted risk rather than a control.

---

## 10. Plan revision history

| Date | Change |
|---|---|
| 2026-08-07 | Initial version. Stages 0-13 defined; decisions D1-D10 registered, D1/D4/D5/D6/D7/D10 still open. |
| 2026-08-07 | **Second review, against the General Objective in `CLAUDE.md` and current AWS guidance.** Structural: D14 places GitLab, Runners, ECR and CodeArtifact in the **Production** account (they were in Sandbox, next to a broadly permissioned group), which moved the Production VPC from Stage 9 to Stage 3, added Sandbox↔Production peering, and reversed the direction of the cross-account registry policies. D5 closed as "build both egress designs and compare" (§4.3), with the user's reservation about CodeArtifact's ecosystem coverage — Python, Julia, Rust, R — recorded as a constraint rather than argued away. New decisions D13 (Lake Formation is only enforceable if execution roles have no direct S3 on registered prefixes), D15 (public domain + split-horizon DNS, because ACM cannot certify a private-only name) and D16 (break-glass). Added §4.2 (data perimeter: SCPs, RCPs, endpoint policies — moved into Stage 1 under new principle 9, "preventive before detective"), §4.3 (the two egress designs) and §11 (the lab-versus-institution delta, under new principle 10). Stage 1 gained centralized root access management, tag and declarative policies, Security Hub/GuardDuty/Access Analyzer, S3 Object Lock on the log archive, Config recorder scoping, and lost `PowerUserAccess` as the data scientist's starting point — which contradicted `CLAUDE.md` outright. Stage 4 gained the control-plane half of "all access through a VPN" (`aws:SourceIp`), which a tunnel alone does not deliver. Stage 6 gained the IAM conditions that stop a notebook launching a job outside the VPC. Stage 12 gained backup/DR and service quotas. **Factual corrections:** the SageMaker domain `RetentionPolicy` defaults to `Retain`, not delete, so the risk is orphaned filesystems rather than lost data; presigned URL *creation* is not visible in CloudTrail, only its use; the VPC endpoint list was missing `sagemaker.studio`, without which a VPC-only domain does not start; D7 omitted SageMaker Pipelines. Cost floor revised from ~USD 15 to ~USD 18-22 and the hourly figure from ~0.25 to ~0.28, almost entirely from moving detective controls into the landing zone. |
| 2026-08-07 | Decisions closed: D1 = `us-west-2`, D4 = self-managed WireGuard, D6 = native AWS combination (the DLP objective in `CLAUDE.md` was split into discovery, access control, egress control and exfiltration detection). D5 and D7 explicitly deferred to the stages that consume them (6 and 10). New decision D11: the lab is ephemeral — added §5.1 (operating model), reworked §5 (cost model now hourly plus a persistent floor), tagged the Terraform slices persistent/ephemeral in §6, and added the teardown/restore requirements to Stages 2, 4, 5 and 7. Stage 1 unblocked: all five account e-mails are registered. |
| 2026-08-07 | Revision after user feedback. D11 restated: the unit of teardown is **resources, not accounts**, and the rule is "pay nothing while idle" rather than "destroy everything" — most AWS resources cost nothing at rest. §5.1 replaced the persistent/ephemeral binary with **three layers** `[P]`/`[D]`/`[E]`, which moved the VPC itself into `[P]` (free at rest) and GitLab and WireGuard into `[D]` (stopped, not destroyed). That removed the backup/restore cycle from the critical path in Stage 7 and split Stage 3 into `foundation/` `[P]` and `egress/` `[E]`. New decision D12: budget ceiling USD 50/month, which is what rules out always-on GitLab, Client VPN, Network Firewall and MWAA. §5 rewritten as a ~USD 15 monthly floor plus ~USD 0.30 per lab hour (~USD 21/month at the expected usage). D1 note corrected: `sa-east-1` was verified against the AWS endpoint tables and is **not** a service-availability problem — the difference is price (~1.5-2x), instance/GPU selection and feature lag. |
| 2026-08-07 | Region question settled. `us-west-2` on cost, and it stays there — LGPD/data residency dropped as a driver (no real data). The `sa-east-1` availability check was recorded as a fact in §4.1, and its answer is that nothing this plan uses is missing from São Paulo; a correction to the previous entry, which wrongly called São Paulo's GPU selection thin (SageMaker Studio has `ml.g5` there since 2023 and `p5.4xl` since 2026, and `t4g` Graviton is available). A move to São Paulo is **hypothetical and not planned work**, so §4.1 was cut back to plain Terraform hygiene — no region literals, AZs from data sources, AMIs from SSM parameters — and the migration checklist, verification commands and the Stage 12 `sa-east-1` trial were dropped. |
| 2026-08-07 | **Consistency review of the whole plan**, after the incremental edits above had left it contradicting itself. Fixed: principle 7 still said "resources are destroyed between sessions" (pre-dates the three-layer model); D4 still described WireGuard as destroyed each session; the WireGuard Elastic IP was assigned to `[D]` in §5.1, `[P]` in Stage 4 and `[D]` in the §6 layout (now `[P]` everywhere); D9 read as "2 AZs" while Stage 3 defaulted endpoints to one AZ (now stated as 2 for subnets, 1 for metered endpoints); the §3 diagram carried no layer markers; §5 priced GitLab as `t3.large` while Stage 7 recommended `t4g.large`; Stage 2's deliverable asked `make down` to drive the `[P]` bootstrap slice, contradicting its own rule; Stages 6 and 10 listed D5/D7 as prerequisites when those decisions are taken *inside* those stages; Stage 5 mixed `[P]` data and `[E]` EFS with no slice boundary (added an `nfs/` slice); Stage 7 did not say which slice ECR and the runners belong to. Also corrected a wrong SSM parameter path in §4.1 (`ami-amazon-linux-latest`, not `ami-amazon-latest`), recalculated the hourly figure against the single-AZ endpoint default (~USD 0.25/h, ~USD 20/month, replacing ~USD 0.30 and ~USD 21 in the entry above), and reordered the two entries above into actual chronological order. |
| 2026-08-07 | **D10 closed: Identity Center administration is delegated to a dedicated Identity account**, a sixth account added to `secrets/accounts.md`. The instance itself stays in Management (it cannot be moved); only its administration is delegated, which lets Terraform manage permission sets without ever holding Management credentials — principle 1 enforced rather than merely stated. Audit keeps a single role, security guardian, and does not also own access management. Updated: §1 (six accounts), the §3 diagram, §5 (Config is per governed account), §5.1, D3 (identity state in the Identity account), Stage 1 (Identity account via Account Factory in the `Security` OU, the `register-delegated-administrator` step, identity work moved out of Management, and the Management-targeted assignment called out as permanently manual), Stage 2 (identity bootstrap plus an import of the Stage 1 console resources), the §6 layout (`terraform-live/identity/`) and Stage 12 (D10 revisit replaced by permission-set tightening). Cost of the decision: one more AWS Config recorder, ~USD 0.50-1/month. Two Control Tower/Identity Center behaviours are flagged in Stage 1 as *to verify during execution* rather than assumed. Also recorded in §9 as open item 3: the AZ name-to-ID mapping between Sandbox and Production, to be checked once the accounts exist, since it decides whether Stage 3 anchors subnets on list position or on AZ IDs. |
| 2026-08-07 | **Third review (user request: inconsistencies + AWS best practices).** Five fixes to things that would not have worked as written. (1) Stage 5's `aws:SourceVpce` bucket policy gained the `aws:ViaAWSService` carve-out — without it the deny blocks Athena/Lake Formation, the exact path D13 mandates. (2) Stage 4 moved from split tunnel to **full tunnel**: with a split tunnel, AWS API/console traffic never carries the WireGuard EIP, so the step-8 `aws:SourceIp` restriction would deny everything; the deny also gained `aws:ViaAWSService: false`. (3) Stage 4's routed-peer-network model was dropped — VPC peering does no edge-to-edge routing, so NAT on the WireGuard instance is mandatory to reach GitLab in Production, and security groups reference the instance SG rather than the client CIDR. (4) Stage 8's GitLab OIDC federation was replaced by a dedicated deploy runner with an instance profile — IAM/STS must fetch the issuer's JWKS over the public internet, which a VPN-only GitLab cannot serve; OIDC stays documented as the target if a minimal public surface ever exists. (5) The internal ALB moved from `[D]` to `[E]` in `production/egress/` — ALBs cannot be stopped and bill ~USD 0.023/h while they exist. **Layer reclassifications on the plan's own "pay nothing while idle" logic:** the SageMaker domain + user profiles and the EFS moved to `[P]` (both free/cents at rest), which deletes the orphaned-home-EFS hazard and the fragile sync-to-S3-on-teardown step — §5.1 rule 2 rewritten accordingly. **Stage 1 gained:** Cost Anomaly Detection; an SCP denying `iam:CreateUser`/`CreateAccessKey` (principle 2 previously had no preventive enforcement); account-level S3 Block Public Access plus its protecting SCP; the tag-policy overstatement corrected (forcing tags at creation needs `aws:RequestTag` SCPs); the delegation-runs-from-Management wording in step 12; and Object Lock added to the verify-for-drift list. **Other corrections:** bootstrap state migrated into its own bucket instead of committed; GitLab CE SAML group sync flagged as paid-tier (membership managed by hand); Studio custom image cross-account pull flagged for verification with ECR replication as the fallback; Iceberg maintenance (`OPTIMIZE`/`VACUUM`) given an owner in Stage 5 and S3 Tables recorded in §11; `DeployApprover` permission set dropped (the gate lives in GitLab); `Environment=shared` documented as org-level; "classic Studio" renamed to current-generation Studio; the ML Lens added to §8 as the per-stage checklist; Cargo confirmed as a CodeArtifact-supported format (§9 item 5 narrowed). **Cost numbers reconciled:** D12 and the §5 header now agree on a ~USD 18-22 floor, ~USD 0.28-0.35/h and ~USD 26-27/month; design B is ~USD 0.11/h with 11 endpoints; the Production-side NAT and the ALB joined the hourly table. |

---

## 11. What a large institution would do differently

Principle 10. Almost every decision in this plan is bent by two constraints a real organization does not
have: a USD 50/month ceiling and a single operator who is also the only user. That is a legitimate way to
build a lab, but it means the environment is not the reference architecture, and the difference should be
learned rather than absorbed by accident. This is the delta, decision by decision.

| Area | This lab | A large institution | Why the difference matters |
|---|---|---|---|
| Account structure | 6 accounts; tooling in Production (D14) | Shared Services / Tooling account in an `Infrastructure` OU; a Network account; per-team sandbox accounts; separate Dev/Staging/Prod per workload | The lab has no boundary between build and runtime, and no boundary between teams. Blast radius is the whole environment |
| OUs | Security, Sandbox, Production | Plus Infrastructure, Workloads (Prod/NonProd), Deployments, Policy Staging, Suspended | Policy staging in particular: an SCP tested on a real OU before it reaches production is the difference between a guardrail and an outage |
| Account vending | Manual Account Factory, three times | **AFT** (Account Factory for Terraform) with a customization pipeline | At three accounts automation costs more than it saves; at thirty it is the only way accounts stay consistent |
| Networking | One VPC per account, peered, NAT and endpoints per account | Transit Gateway or Cloud WAN, centralized egress through an inspection VPC, centralized interface endpoints shared by RAM, **IPAM** for CIDR allocation | Peering is O(n^2) and per-account endpoints are the largest hourly cost multiplied by the number of accounts. CIDRs chosen by hand collide eventually |
| VPN | Self-managed WireGuard, peers in a `.tfvars` (D4) | AWS Client VPN or Verified Access, federated to the corporate IdP, with per-user certificates and session logging | Revoking one person here means editing a file and re-applying. That does not survive an offboarding process |
| Identity | Identity Center as the identity source | Identity Center federated to the corporate IdP (Entra ID, Okta) via SAML + SCIM, groups driven by HR | Joiners/movers/leavers has to be automatic, or entitlements only ever accumulate |
| Data lake placement | Lake inside the Sandbox and Production accounts | Data lake accounts per domain, with producer/consumer separation and Lake Formation cross-account sharing as the default rather than the exception | The lab conflates *environment* with *data domain*; a real organization has many domains per environment |
| Data governance | Glue Catalog + LF-Tags, curated by hand | **SageMaker Unified Studio / SageMaker Catalog** (DataZone): business glossary, data products, subscription workflows, lineage | Discovery and a request/approval workflow are the parts that make a lake usable by people who did not build it |
| Iceberg operations | General-purpose S3 buckets + scheduled Athena `OPTIMIZE`/`VACUUM`, because D13 leans on prefix-level IAM control | **Amazon S3 Tables**: managed Iceberg with automatic compaction, snapshot expiry and Lake Formation integration | The managed service removes the maintenance a hand-rolled lake forgets — but takes away the prefix-level control D13 is built on, so switching is an architecture decision, not a swap |
| Access requests | Terraform merge request | Self-service request with approval workflow, time-bound grants | "Ask the platform engineer" does not scale, and permanent grants never get revoked |
| Egress control | DNS Firewall allowlist, or no internet (§4.3) | AWS Network Firewall with TLS inspection, plus an internal package mirror covering every ecosystem (Posit Package Manager, Artifactory or similar) | A commercial artifact manager solves in one product what §4.3 solves with four different fallbacks. It costs money the lab does not have |
| Egress cost | ~USD 0.05/h NAT | ~USD 290/month Network Firewall, accepted without discussion | The lab has to be clever precisely because it cannot buy the obvious answer |
| Shared storage | EFS with Access Points; POSIX identity not tied to SSO | FSx for Lustre for training throughput, EFS for home directories, and file access auditable per user | "Who read this file" is unanswerable in the lab design. In a regulated institution that is disqualifying |
| CI/CD trust | Same-account deploy runner with an instance profile (D14; OIDC is blocked because IAM cannot fetch a VPN-only issuer's JWKS) | Build account separate from deploy targets; OIDC federation against a publicly resolvable issuer; signed artifacts; provenance attestation | A compromised runner in the lab compromises Production directly |
| Backups | AWS Backup + Vault Lock (Stage 12) | The same, plus tested DR runbooks, cross-region recovery, and RTO/RPO agreed per system rather than assumed | The lab tests recovery once; an institution rehearses it |
| Availability | 1 NAT, single-AZ endpoints, single VPN instance (D9, D4) | Multi-AZ everything, no single points of failure | Every availability shortcut here is a deliberate cost trade, and each one is listed in D4 and D9 |
| Operations | One person, `make up` / `make down` | On-call rotation, runbooks, change management, an internal platform team with its own product backlog | The largest difference of all, and the one no amount of Terraform addresses |

**How to use this table.** When a stage is built, check its row here. If the lab approach would be
indefensible at scale, say so in the stage's notes and record what the alternative was — that is the
artefact worth keeping from this project, more than the infrastructure itself.
