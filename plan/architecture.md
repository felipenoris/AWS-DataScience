# Target architecture, region portability, perimeter and egress

What the environment is meant to look like, and the three cross-cutting design pieces that
shape every stage. Section numbers are kept from the original single-file plan.

---

## 3. Target architecture (summary)

Layers per `plan/conventions.md` §5.1: `[P]` persistent (free at rest), `[D]` dormant (stopped between sessions),
`[E]` ephemeral (destroyed between sessions).

```
AWS Organization (Management account - console only)                        [P]
│
├── OU Security              <- FOUNDATIONAL: Control Tower owns this OU and
│   │                           will not accept an account it did not create
│   ├── Log Archive account  (created by Control Tower, S3 Object Lock)     [P]
│   └── Audit account        (created by Control Tower) <- security guardian [P]
│                               GuardDuty / Security Hub / Macie / Analyzer
│
├── OU Identity              <- its own OU since 2026-08-09: the vend into
│   │                           Security was refused (D23). Inherits NONE of
│   │                           Security's foundational guardrails, so its
│   │                           policy set is attached, not inherited
│   └── Identity account     <- Identity Center delegated administration    [P]
│
├── OU Policy Test           <- NO policy set of its own: this is where a
│   │                           candidate SCP/RCP is attached and exercised
│   │                           before it reaches anything real (D29)
│   └── Policy Canary account <- deliberately EMPTY: no VPC, no data, no
│                                Terraform slice, no state bucket. Holds one
│                                thing, and it is the point - an admin
│                                principal, because an SCP tested by a
│                                restricted principal measures the identity
│                                policy instead                              [P]
│
├── OU Interactive           <- NO set of its own: interactive compute is allowed
│   │                           here because, unlike Workloads and Data, nothing
│   │                           denies it - the org-root set is the whole ceiling.
│   │                           What holds infrastructure change off the data
│   │                           scientist is DataScientistAccess, an IDENTITY
│   │                           policy, not this OU (D23; Stage 1c step 7 carries
│   │                           the choice of whether to give the OU a set at all,
│   │                           and why the literal SCP cannot be written without
│   │                           exempting the builder). If it ever gains one, it
│   │                           attaches HERE and inherits into Sandboxes below
│   ├── OU Sandboxes         <- groups the one class of account that
│   │   │                       multiplies. NO policy set of its own: the
│   │   │                       Interactive set above inherits into it, which
│   │   │                       is what makes a new unit governed on arrival
│   │   └── Sandbox account  <- EXPERIMENTATION: the unit of work is a notebook.
│   │       │                   ONE PER BUSINESS UNIT (D35) - the only account
│   │       │                   in this tree that multiplies; N is 1 today, and
│   │       │                   this whole subtree is what Stage 14 vends from
│   │       │                   a unit name. Everything else is structural
│   │       ├── VPC, subnets, IGW, security groups, private DNS zone        [P]
│   │       ├── blueprint target (D26): the experimentation project's
│   │       │     environments are provisioned here by the domain in
│   │       │     Data Governance (SageMaker AI apps VPC-only,
│   │       │     restricted egress). Slice is [P]; running apps are      [P/E]
│   │       ├── scratch / derived-zone S3 buckets (per-principal, D19)      [P]
│   │       ├── WireGuard EC2 <- the only human entry point (see below)     [D]
│   │       ├── NAT Gateway + interface VPC endpoints                       [E]
│   │       └── EFS (NFS shared filesystem, lifecycle to IA), per unit  D24 [P]
│   │
│   └── Development account  <- DEVELOPMENT: the unit of work is a pipeline
│       │                       (repository with tests, workflows)          D21
│       ├── VPC (same module, own CIDR, peered to Production for GitLab)    [P]
│       ├── blueprint target (D26): the engineering project's
│       │     environments are provisioned here by the domain in
│       │     Data Governance. Slice is [P]; running apps are            [P/E]
│       ├── scratch / derived-zone S3 buckets (per-principal, D19)          [P]
│       └── NAT + interface VPC endpoints                                   [E]
│
├── OU Data                  <- one SCP set: no USER compute (two named
│   │                           exceptions); data cannot be deleted, only
│   │                           governed (D22, D23, D26, D27)
│   └── Data Governance account <- the OWNERSHIP axis: owns the STATE of
│       │                          data AND its governance. Nobody signs in
│       ├── S3 raw/curated (Iceberg) - the only copy of governed data       [P]
│       ├── Glue Data Catalog + Lake Formation (LF-Tags, D13 registration)  [P]
│       ├── SageMaker unified domain (DataZone V2) + project profiles,
│       │     blueprints (Tooling, Lakehouse Glue/Athena, ML), account
│       │     associations, SageMaker Catalog            <- D26            [P]
│       │     A REGISTRY, NOT A RUNTIME: blueprints provision compute
│       │     into Sandbox and Development, never here
│       ├── Glue Crawlers (raw + drop-box) under the maintenance role,
│       │     event-driven; Iceberg optimizers           <- D27            [P] cfg
│       ├── ingestion drop-box prefix (PutObject-only, dated, D18)          [P]
│       └── LF cross-account shares -> Sandbox, Development (read),
│           Production (read + governed write: the producer path)           [P]
│
└── OU Workloads             <- one SCP set for both: no interactive compute,
    │                           no human control plane (D20)
    ├── Staging account      <- deployment target; integration tests land here
    │   ├── VPC (same module, own CIDR; deliberately not peered - Stage 3)  [P]
    │   ├── S3 + Glue Catalog (Iceberg) - sampled or synthetic data only,
    │   │     local to this account, never LF-shared production data        [P]
    │   ├── SageMaker job execution roles (no domain, no Model Registry)    [P]
    │   ├── NAT + interface VPC endpoints (only during a promotion run)     [E]
    │   └── app slices, deployed by the pipeline and torn down after tests  [E]
    │
    └── Production account   <- no human runs code here; no Studio domain   D17
        ├── VPC (mirrors sandbox topology; peering accepter for Sandbox
        │     and Development)                                              [P]
        ├── ECR (dev-env images, application images)          <- D14        [P]
        ├── CodeArtifact (package proxy: PyPI, Cargo, ...)    <- D14        [P]
        ├── SageMaker Model Registry + job execution roles    <- D17        [P]
        │     └── training/processing jobs, endpoints (pipeline-submitted)  [E]
        │         reading and writing the lake through the LF share (D22)
        ├── GitLab (EC2, private) + GitLab Pages              <- D14        [D]
        ├── internal ALB for GitLab/Pages (rebuilt per session)             [E]
        ├── GitLab Runners                                    <- D14        [E]
        ├── NAT Gateway + interface VPC endpoints                           [E]
        ├── orchestration, built twice and compared (D7):                   [E]
        │     (A) MWAA  (B) EventBridge + Step Functions + Lambda/Fargate
        └── (Stage 13) public web tier -> private backend                   [E]
```

**The two axes, made explicit (D22, D23, D26).** The OU axis is *lifecycle*: how mature and how protected
the compute in an account is (Interactive → Workloads). The Data OU sits on the other axis, *ownership*:
the lake outlives every application that reads it, so it lives in an account whose policy set is about
retention and governance, not deployment. Environments hold **compute**; the Data Governance account holds
**state and governance** — since D26 that includes the SageMaker unified domain, which is a registry of
projects and data products and therefore an ownership-axis resource, not a Development one. **The
platform accounts sit on neither axis** — Management, Log Archive, Audit, Identity and D29's
`Policy Canary`: they serve every account and belong to no environment. *The last of those is the one that
keeps being left off this list, because it is the only platform account that is **disposable** rather than
permanent — and disposability is a cardinality property that cuts across the axes (D35), not an axis of its
own.* The consequence that has to be said out loud, because it is asked
every time: *an account off the lifecycle axis is not "a production account"*. Some of them —
Identity, Data Governance — are nonetheless high blast radius. Sensitive and production are different
properties. `ORGANIZATION.md` carries the same classification per account. Every environment reaches the same single copy of the data through a Lake Formation
cross-account share — which is what `CLAUDE.md` asked for ("use AWS Lake Formation to share data
cross-account") taken to its logical conclusion: the share is the *default* read path, not an exception.

**Why the tooling sits in Production (D14).** GitLab, its runners, ECR and CodeArtifact are the supply
chain: whoever controls them controls what runs in Production. They must not live in the account where
the `sso-group-data-scientists` group has broad permissions. Two consequences shape several stages: the Production
VPC has to exist before Stage 7 (so it is built in Stage 3, not Stage 9), and the human path to GitLab is
laptop → WireGuard in Sandbox → VPC peering → GitLab in Production.

Note the refinement this forces on "only Terraform and CI/CD touch Production": nobody changes Production
*infrastructure* by hand, but humans do *use* a service hosted there (GitLab, over the VPN). The boundary
is the control plane, not the account.

**How a human actually reaches each account, because "the VPN is the only entry point" hides two different
paths.** The WireGuard instance lives in Sandbox and is a **full tunnel** (Stage 4 step 5), so *all* the
laptop's traffic leaves through its Elastic IP — and that, not a route into every VPC, is what makes the
single entry point true. Concretely there are two paths and they should not be confused:

- **VPC-level reach**, which only Sandbox and Production have. The tunnel terminates in the Sandbox VPC,
  and the Sandbox↔Production peering extends it to the GitLab subnet. This is the path for private DNS
  names, the EFS mount (D24) and anything addressed by a private IP.
- **AWS API and portal reach**, which every account has, over public AWS endpoints exited through the
  WireGuard Elastic IP. This is how **the unified domain is used (D26)**: the Unified
  Studio portal — like the presigned Studio URL before it — is a public endpoint even when project
  compute is `VpcOnly`; VPC-only governs how the *app containers* reach the network, not how the browser
  reaches the UI. The laptop needs no route into the Development VPC.

The control that makes the second path VPN-only is therefore **`aws:SourceIp` on the WireGuard Elastic IP**
(Stage 4 step 8), not `aws:SourceVpce`. Getting that backwards is the fastest way to write a condition that
either denies everything or protects nothing.

**Where the humans are (D17, D18, D21).** D14 refined that boundary once; the decisions above refine it
further, and the resulting sentence is the one to remember: *humans run code in the Interactive OU and
nowhere else; they read the deployment targets' data planes; nobody changes a Workloads-OU control plane
by hand, and the lake is written only through governed engines.* Concretely: interactive compute exists in
Sandbox and Development and nowhere else — since D26 one unified domain, registered in Data Governance,
whose project blueprints provision compute into the two Interactive accounts and into no others (D17 as
revised by D21 and re-read by D26). The domain being elsewhere changes nothing about where code runs: it
is a registry, and the project profile names the target account. The data
scientist holds read-only
permission sets on Staging and Production for logs, catalog metadata, job status and Athena (D18); the
SageMaker runtime in Staging and Production is reachable only by a pipeline; and no human signs in to the
Data Governance account at all outside the infrastructure role (D22).

---

### 4.1 Region portability

The lab runs in `us-west-2` and **stays there**. A move to São Paulo is hypothetical and is not planned
work — no stage builds towards it, and no migration procedure is maintained here.

What remains is ordinary Terraform hygiene, which costs nothing and is worth doing on its own merits:

| Thing | Rule |
|---|---|
| Region | A single `var.region`, set per environment in `.tfvars`. No `us-west-2` literal in `.tf` files. |
| Availability zones | **Anchor on the AZ ID** — `zone_ids = ["usw2-az1", …]` per environment in `.tfvars`, matched through `data.aws_availability_zones`'s `zone_ids` attribute. Never a literal `us-west-2a`, and **never list position**. |
| AMI IDs | AMI IDs are region-scoped. Resolve through SSM public parameters (e.g. `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64`), never a literal `ami-…`. |
| Bucket names | S3 names are globally unique — build them from variables rather than pasting a region in. |

**The AZ row is the one that stopped being hygiene and became a control, and the reason is worth keeping
because the measurement argues the other way.** AWS maps AZ *names* to physical datacenters independently
per account. Stage 1b step 6 measured it across every account that has a profile and found them
**identical** — `us-west-2a` → `usw2-az2`, `b` → `az1`, `c` → `az3`, `d` → `az4`, so the names are not even
in ID order. Index-based placement would therefore work today. It is still forbidden, for one reason: the
measurement can only speak for accounts that exist. `Staging` is unvended, D35 and Stage 14 multiply
Sandboxes, and each new account is assigned its own mapping at vend time. **The failure is silent** — two
peered subnets land in different datacenters, nothing errors, and the only symptom is cross-AZ transfer at
USD 0.01/GB each way on the two peerings D14 and D21 keep constantly busy. A rule that holds only while the
account set is frozen is not a rule (Lesson 5). Re-run `./aws/AZs.sh` after each vend; with `zone_id`
anchoring, a disagreement is information rather than a rebuild.

Recorded for reference, from the check on 2026-08-07 and **corrected on 2026-08-08**: `sa-east-1` has
endpoints for almost every service this plan uses — Control Tower, IAM Identity Center, SageMaker (Studio
with `ml.t3.medium`, `ml.g5`, `p5.4xl`), MWAA, Macie, GuardDuty, Security Hub, Lake Formation, Glue,
Athena, EFS, ECR, Client VPN, Network Firewall and Graviton `t4g`. **The exception, missed by the original
check: AWS CodeArtifact is not available in `sa-east-1`** — it exists in thirteen Regions, `us-west-2`
among them, and São Paulo is not one. That is not a price difference, it is a missing component: D14 puts
CodeArtifact in the supply chain and egress design B (D5) depends on it as the *only* package path when
there is no NAT. A move to São Paulo would have to replace it (a self-hosted proxy such as devpi, or
design A only). The rest of the answer to "would anything break in São Paulo?" is no; the remaining
difference is price, **measured rather than guessed on 2026-08-08: roughly 1.5-2.1x**, service by service,
in `PRICING.md`. If a move ever became real, the one genuinely expensive part would be redeploying the
Control Tower landing zone, whose home region is fixed at deployment time.

One cross-region rule is permanent and unrelated to any of this: ACM certificates for CloudFront must live
in `us-east-1` regardless of where the workload runs (relevant only at Stage 13). **This is not merely a
note about where to click** — the region restriction (Stage 1c step 7) governs `us-west-2` alone, so
`acm:*` has to be among the globally exempt actions or Stage 13 cannot issue that certificate at all.
**Since D15's revision on 2026-08-09 that exemption is unexercised until Stage 13** — before it, ACM is used
only to *import* the internal CA's leaves in `us-west-2`, which the region control permits anyway. Leave the
exemption in the policy regardless: adding it later means editing an SCP under time pressure, and the same
applies to `route53domains:*`, whose single use is the registration in Stage 13 step 1.
Control Tower's Region deny control carries it; the point of recording it here is that a fact stated in one
file and a policy written in another were, until 2026-08-08, unaware of each other.

---

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

**The second casualty is not a service carve-out at all, and no condition key covers it: AWS's own
service-owned S3 buckets.** `aws:ResourceOrgID` is a statement about *your* organization, and the Amazon
Linux repositories, the SageMaker image and JumpStart buckets and the SSM/CloudWatch agent buckets are
outside it. A `dnf update` is your credential fetching an object, so `aws:ViaAWSService` is false and the
request is denied. Every place this plan applies a trusted-resources condition therefore needs a companion
allow-list of AWS-owned bucket ARNs: the S3 gateway endpoint policy (Stage 3 step 9) is the one that bites
first and hardest, since under egress design B it is the *only* route to those buckets. Treat "which
AWS-owned buckets does this environment depend on" as a maintained list, not as a one-off discovery.

---

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
which is why this is the shape regulated institutions converge on. It also removes the NAT gateway — at
the price of the two CodeArtifact interface endpoints, a net saving of **~USD 0.030/h** (`plan/cost-model.md`).

**A correction worth carrying into the Stage 6 comparison, because it nearly made design B unbuildable.**
Until 2026-08-08 the endpoint list omitted `athena`, `glue` and `lakeformation`. Under design A the NAT
hid that; under design B there is no NAT, so the design as written could not have executed a single query
— and D13 routes *every* tabular read through an LF-aware engine, which is the whole access path. The
three are now in the common core of both designs (Stage 3 step 8). Two things follow: **both designs cost
more than this file used to say**, and **the saving above is now the NAT alone**, which is the honest form
of it. Three cents an hour decides nothing — the comparison below is settled by friction, which is what
D5 said it wanted to measure.

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

**And since 2026-08-08 that rebuild has a gate in it**, which is a genuine cost to this comparison and not
a footnote: the `dev-env` image is released through its own promotion chain with an approval by the
**Dev Env Steward** (Stage 8 step 1). Under design A a missing Python package is a `pip install` in the
notebook; under design B it is a merge request, a build, a scan and a human approval. That is the right
governance for a runtime everyone shares — and it is exactly the friction the Stage 6 verdict has to
measure honestly rather than average away. Whether the gate can be automated at all is `INT-17`.

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

## The shape to hold in mind

Moved here from `CLAUDE.md` on 2026-08-08: it is a mental model, not a status. Every old habit
contradicts some part of it.

- **Four environment roles, one axis of lifecycle:** Sandbox (experimentation — the unit of work is a
  notebook), Development (the unit of work is a pipeline), Staging and Production (deployment targets,
  written only by the pipeline). Promotion runs **Development → Staging → Production**; Sandbox feeds
  Development through **git graduation**, never through a pipeline (D21).
- **Four roles, but not one account each: `Sandbox` is one account per business unit (D35).** The chain is
  **N Sandboxes → one Development → one Staging → one Production**, so the cardinality boundary is the same
  line as the graduation boundary above — experimentation multiplies, the engineering chain after it does
  not, and the promotion chain is therefore untouched by N. N is 1 today. Per-unit isolation ends at that
  line; past it, isolation is Lake Formation's job and not an account boundary's.
- **Three groups, not one sequence** (`ORGANIZATION.md` carries the per-account classification):
  the **lifecycle** axis (Sandbox before the chain, then Development → Staging → Production), the
  **ownership** axis (Data Governance alone), and the **platform** accounts on neither — the organization's
  own machinery, serving every account and belonging to no environment. *An account off the lifecycle axis
  is not "a production account"* — that
  question gets asked every time; the answer is that Data Governance and Identity are **high blast
  radius**, which is a different property from being production.
- **One account off that axis entirely:** Data Governance (D22) owns the governed lake; every environment
  reaches it through Lake Formation cross-account shares — read for Sandbox/Development, read plus
  **governed write** for Production's job role (the producer path). Nobody signs in to it interactively.
- **Six OUs plus one nested, and what each carries is deliberately not uniform (D23).** *The count is the
  wrong thing to remember — it has gone stale twice already (four, then five, then six plus one), and each
  time it was the **list** that was wrong rather than the number.* Read it per OU instead:
  - **`Security`** (Log Archive, Audit) is **foundational**: its ceiling is Control Tower's guardrails,
    inherited by the accounts being foundational rather than by the folder, and never ours to write.
  - **`Data`** (no *user* compute — D27 carves out catalog maintenance: crawlers and table optimizers under
    the lake's own role, never on Iceberg tables) and **`Workloads`** (Staging + Production — no
    interactive compute, no human control plane) carry the sets this project writes.
  - **`Identity` carries one too, and it is the one that has to be *attached*.** It was split out of
    `Security` on 2026-08-09 because Control Tower would not vend a non-foundational account into a
    foundational OU, so it inherits none of those guardrails — **Stage 1c step 7 attaches them or they are
    not there**, and this is the account whose administrator can grant access to every other one.
  - **`Sandboxes` carries none, by design**: it groups the per-unit Sandbox accounts (D35) and inherits
    `Interactive`. Depth is therefore 2, which any OU enumeration has to be written against (D34).
  - **`Interactive` carries none either — today, and that is an open decision rather than a property.** It
    holds Development plus the nested `Sandboxes`, it is the only OU where a domain may exist (D17), and
    interactive compute is allowed there because nothing denies it: the organization-root set is the whole
    ceiling. What holds infrastructure change off the data scientist is `DataScientistAccess`, an
    **identity** policy, not this OU. Whether it gains a set of its own is Stage 1c step 7.6 — the one
    blocking question of that stage.
  - **`Policy Test` (D29) carries none on purpose** — it is where a *candidate* SCP/RCP is attached and
    exercised against the disposable `Policy Canary` account before it reaches anything real. It exists as
    an account and not just a folder because an SCP is only evaluated when a principal makes a call, so an
    empty staging OU tests nothing; and the test principal is an **administrator**, because a deny
    exercised by a principal that lacked the permission anyway proves nothing about a ceiling. Never call
    it "Policy Staging" — that is the industry term and it collides with the `Staging` account, which is
    exactly what the naming avoids.
- **One unified domain, projects as the isolation unit (D26):** the DataZone V2 domain is registered in
  **Data Governance** (renamed from Data Management on 2026-08-08) because a domain is a registry of
  projects and data products — ownership axis, not lifecycle axis. **It holds no compute:** the
  `experimentation` project profile provisions into Sandbox, `engineering` into Development, and nothing
  is ever provisioned into the domain account itself. Sandbox×Development is therefore *strengthened*, not
  dissolved — it stops being "which URL did the person open" and becomes a property of the project.
  Lakehouse blueprint in its Glue/Athena form only — **never** the Redshift Serverless variant.
  Staging and Production are never associated. What crosses the gate is
  the D28 artifact set — image, workflow YAML in S3, per-workflow role, orchestration resource, log
  group, model package group — carried by the project's git repository, linted against domain-scoped
  references.
- **D18** gives the data scientist read-only permission sets on Staging and Production (data plane, no
  compute); **D19** keeps the derived zones (now per Interactive account) designed rather than left over.
- **Two access paths, not one.** "The VPN is the only entry point" is true because the tunnel is *full*,
  not because it routes into every VPC. Only Sandbox and Production are reachable at the VPC level;
  Development and Staging are used entirely through AWS API endpoints exited via the WireGuard Elastic IP
  — including the Unified Studio portal, which is a public endpoint even when project compute is
  VPC-only. The control there is `aws:SourceIp`, never `aws:SourceVpce` (`plan/architecture.md` §3) — **and whether that control
  reaches the portal at all is INT-16, unverified**: the portal is entered by an Identity Center
  sign-in, not by an IAM-authorized call under a permission set, so the condition demonstrably covers the
  API half and not yet the portal half. Answered at Stage 4.
- **D24:** the shared EFS lives in Sandbox only; Development gets neither its own nor a path to it, and
  the exchange between the two Interactive accounts is S3 and git. **D25:** the ingestion drop-box is
  picked up by Production's job role on the producer path — which also closed a hole where the `Data` OU
  SCP never denied Glue jobs.

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [plan/stages/INDEX.md](stages/INDEX.md)*
