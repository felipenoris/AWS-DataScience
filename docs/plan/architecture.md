# Target architecture, region portability, perimeter and egress

What the environment is meant to look like, and the three cross-cutting design pieces that
shape every stage. Section numbers are kept from the original single-file plan.

---

## 3. Target architecture (summary)

Layers per `docs/plan/conventions.md` §5.1: `[P]` persistent (free at rest), `[D]` dormant (stopped
between sessions), `[E]` ephemeral (destroyed between sessions).

```
AWS Organization (Management account - console only)                        [P]
│
├── OU Security              <- foundational: Control Tower owns this OU and
│   │                           will not accept an account it did not create
│   ├── Log Archive account  (created by Control Tower, S3 Object Lock)     [P]
│   └── Audit account        (created by Control Tower) <- security guardian [P]
│                               GuardDuty / Security Hub / Macie / Analyzer
│
├── OU Identity              <- its own OU since 2026-08-09: the vend into
│   │                           Security was refused (D23). Inherits none of
│   │                           Security's foundational guardrails, so its
│   │                           policy set is attached, not inherited
│   └── Identity account     <- Identity Center delegated administration    [P]
│
├── OU Policy Test           <- no policy set of its own: this is where a
│   │                           candidate SCP/RCP is attached and exercised
│   │                           before it reaches anything real (D29)
│   └── Policy Canary account <- deliberately empty: no VPC, no data, no
│                                Terraform slice, no state bucket. Holds one
│                                thing: an admin principal, because an SCP
│                                tested by a restricted principal measures
│                                the identity policy instead                 [P]
│
├── OU Interactive           <- no set of its own: interactive compute is allowed
│   │                           here because, unlike Workloads and Data, nothing
│   │                           denies it - the org-root set is the whole ceiling.
│   │                           What holds infrastructure change off the data
│   │                           scientist is DataScientistAccess, an identity
│   │                           policy, not this OU (D23; Stage 1c step 7 carries
│   │                           the choice of whether to give the OU a set at all,
│   │                           and why the literal SCP cannot be written without
│   │                           exempting the builder). If it ever gains one, it
│   │                           attaches here and inherits into Sandboxes below
│   ├── OU Sandboxes         <- groups the one class of account that
│   │   │                       multiplies. No policy set of its own: the
│   │   │                       Interactive set above inherits into it, which
│   │   │                       is what makes a new unit governed on arrival
│   │   └── Sandbox account  <- experimentation: the unit of work is a notebook.
│   │       │                   One per business unit (D35) - the only account
│   │       │                   in this tree that multiplies; N is 1 today, and
│   │       │                   this subtree is what Stage 14 vends from a
│   │       │                   unit name. Everything else is structural
│   │       ├── VPC, subnets, IGW, security groups, private DNS zone        [P]
│   │       ├── blueprint target (D26): the experimentation project's
│   │       │     environments are provisioned here by the domain in
│   │       │     Data Governance (SageMaker AI apps VPC-only,
│   │       │     restricted egress). Slice is [P]; running apps are      [P/E]
│   │       ├── derived zone = the SMUS project path (D19 rev. 2026-08-26): [P]
│   │       │     awsds-sandbox-smus-projects/<domain>/<project>/<scope>/,
│   │       │     project CMK (D31's carrier); data CMK = the sandbox lake's
│   │       └── interface VPC endpoints - no NAT, no default route (D38):
│   │             the internet is Production's proxy, over the peering    [E]
│   │
│   │   (a Development account stood here until 2026-09-06 - Stage 6b
│   │    converted it into Staging below; D21 superseded)
│
├── OU Data                  <- one SCP set: no user compute (two named
│   │                           exceptions); data cannot be deleted, only
│   │                           governed (D22, D23, D26, D27)
│   └── Data Governance account <- the ownership axis: owns the state of
│       │                          data and its governance. Nobody signs in
│       ├── S3 raw/curated (Iceberg) - the only copy of governed data       [P]
│       ├── Glue Data Catalog + Lake Formation (LF-Tags, D13 registration)  [P]
│       ├── SageMaker unified domain (DataZone V2) + project profiles,
│       │     blueprints (`Tooling` + the enabled set - docs/SMUS.md), account
│       │     associations, SageMaker Catalog            <- D26            [P]
│       │     A registry, not a runtime: blueprints provision compute
│       │     into the Sandbox accounts, never here
│       ├── Glue Crawlers (raw + drop-box) under the maintenance role,
│       │     event-driven; Iceberg optimizers           <- D27            [P] cfg
│       ├── ingestion drop-box prefix (PutObject-only, dated, D18)          [P]
│       └── LF cross-account shares -> Sandbox (read; Development's revoked at 6b),
│           Production (read + governed write: the producer path)           [P]
│
└── OU Workloads             <- one SCP set for both: no interactive compute,
    │                           no human control plane (D20)
    ├── Staging account      <- deployment target; integration tests land here
    │   ├── VPC (same module, own CIDR; peered to VPC-Networking since 6c)  [P]
    │   ├── S3 + Glue Catalog (Iceberg) - sampled or synthetic data only,
    │   │     local to this account, never LF-shared production data        [P]
    │   ├── SageMaker job execution roles (no domain, no Model Registry)    [P]
    │   ├── interface VPC endpoints, no NAT (only during a promotion run)  [E]
    │   └── app slices, deployed by the pipeline and torn down after tests  [E]
    │
    └── Production account   <- no human runs code here; no Studio domain   D17
        │                       and, since 6c (D38), the network platform
        ├── VPC-SharedServices (10.30/16): GitLab, runners, the build host;
        │     the awsds.internal apex zone; peering accepter                [P]
        ├── VPC-Networking (10.31/16): the estate's only internet gateway,
        │     the peering accepter for every spoke, both hub anchors        [P]
        │     ├── WireGuard EC2 <- the only human entry point (see below)   [D]
        │     └── Squid EC2     <- the single egress, an explicit proxy     [D]
        ├── VPC-Workloads (10.32/16): the production runtime, no IGW route  [P]
        ├── ECR (dev-env images, application images)          <- D14        [P]
        ├── CodeArtifact (package proxy: PyPI, Cargo, ...)    <- D14        [P]
        ├── SageMaker Model Registry + job execution roles    <- D17        [P]
        │     └── training/processing jobs, endpoints (pipeline-submitted)  [E]
        │         reading and writing the lake through the LF share (D22)
        ├── GitLab (EC2, private) + GitLab Pages              <- D14        [D]
        ├── internal ALB for GitLab/Pages (rebuilt per session)             [E]
        ├── GitLab Runners                                    <- D14        [E]
        ├── interface VPC endpoints per VPC - no NAT anywhere (D38)         [E]
        ├── orchestration: MWAA Serverless only (D7 amended 2026-09-05)     [E]
        └── (Stage 13) public web tier -> private backend                   [E]
```

**The two axes (D22, D23, D26).** The OU axis is *lifecycle*: how mature and how protected the compute in
an account is (Interactive → Workloads). The Data OU sits on the other axis, *ownership*: the lake
outlives every application that reads it, so it lives in an account whose policy set is about retention
and governance, not deployment. Environments hold **compute**; the Data Governance account holds **state
and governance**, which since D26 includes the SageMaker unified domain — a registry of projects and data
products, and therefore an ownership-axis resource. **The platform accounts sit on neither axis** —
Management, Log Archive, Audit, Identity and D29's `Policy Canary`: they serve every account and belong
to no environment. `Policy Canary` is the only platform account that is **disposable** rather than
permanent, and disposability is a cardinality property that cuts across the axes (D35) rather than an axis
of its own. *An account off the lifecycle axis is not "a production account"*: some of them — Identity,
Data Governance — are nonetheless high blast radius, because sensitive and production are different
properties. `docs/ORGANIZATION.md` carries the same classification per account. Every environment reaches
the same single copy of the data through a Lake Formation cross-account share, which is `CLAUDE.md`'s
"use AWS Lake Formation to share data cross-account" taken to its conclusion: the share is the *default*
read path, not an exception.

**Why the tooling sits in Production (D14).** GitLab, its runners, ECR and CodeArtifact are the supply
chain: whoever controls them controls what runs in Production. They must not live in the account where
the `sso-group-data-scientists` group has broad permissions. Two consequences shape several stages: the
Production VPC has to exist before Stage 7 (so it is built in Stage 3, not Stage 9), and the human path
to GitLab is laptop → WireGuard in `VPC-Networking` → peering → GitLab in `VPC-SharedServices` (both
Production VPCs since 6c; the tunnel terminated in Sandbox until 2026-09-06).

This refines "only Terraform and CI/CD touch Production": nobody changes Production *infrastructure* by
hand, but humans do *use* a service hosted there (GitLab, over the VPN). The boundary is the control
plane, not the account.

**How a human reaches each account.** The WireGuard host lives in Production's `VPC-Networking` (since 6c,
2026-09-06; Sandbox before) and, in the **monitored** profile, is a **full tunnel** (Stage 4 step 5; the
**split-tunnel** profile of 6c pass 8, named in `objectives.md`, leaves the cloud side identical and only
the laptop's own internet outside the tunnel), so *all* the laptop's traffic enters it and leaves the
estate only through the **proxy's** Elastic IP (D38). That, not a route into every VPC, is what makes the
single entry point true for a laptop with the tunnel up; the Unified Studio portal is the measured
exception (INT-16, 2026-08-22 — a portal session works with the tunnel down; closed 2026-09-07 as a
recorded acceptance, revisited at Stage 11 step 3.4). There are two paths, and they should not be
confused:

- **VPC-level reach**. The tunnel terminates in `VPC-Networking`, and the five peerings extend it to
  every VPC — an address, never a path (Lesson 44). This is the path for private DNS
  names and anything addressed by a private IP.
- **AWS API and portal reach**, which every account has, over public AWS endpoints exited through the
  **proxy's** Elastic IP (6c 4.12). This is how **the unified domain is used (D26)**: the Unified
  Studio portal — like the presigned Studio URL before it — is a public endpoint even when project
  compute is `VpcOnly`; VPC-only governs how the *app containers* reach the network, not how the browser
  reaches the UI. The laptop needs no route into the Staging VPC.

The control that makes the second path VPN-only is **`aws:SourceIp` on the proxy's Elastic IP** (Stage 4
step 8), not `aws:SourceVpce`. Measured 2026-08-22: it gates the API/console half of this path and **not
the portal half**, because the portal is entered by an IdC sign-in the permission-set deny never sees
(INT-16; `README.md` item 3 carries the full statement — a recorded acceptance since 2026-09-07, which
Stage 11 step 3.4 revisits and whose 5.2 alarms on an off-proxy portal session).

**Where the humans are (D17, D18, D21).** *Humans run code in the Interactive OU and nowhere else; they
read the deployment targets' data planes; nobody changes a Workloads-OU control plane by hand; and the
lake is written only through governed engines.* Interactive compute exists in Sandbox and nowhere else
(Development's half left at Stage 6b, 2026-09-06): since D26 one unified domain, registered in Data
Governance, whose project blueprints provision compute into the Sandbox accounts and into no others (D17
as revised by D21, re-read by D26, and narrowed by 6b). The domain being elsewhere changes nothing about
where code runs: it is a registry, and the project profile names the target account. The data scientist
holds read-only permission sets on Staging and Production for logs, catalog metadata, job status and
Athena (D18); the SageMaker runtime in Staging and Production is reachable only by a pipeline; and no
human signs in to the Data Governance account at all outside the infrastructure role (D22).

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

**The AZ row is a control rather than hygiene**, and the measurement argues the other way. AWS maps AZ
*names* to physical datacenters independently per account. Stage 1b step 6 measured it across every
account that has a profile and found them **identical** — `us-west-2a` → `usw2-az2`, `b` → `az1`,
`c` → `az3`, `d` → `az4`, so the names are not even in ID order. Index-based placement would work today,
and is still forbidden: the measurement can only speak for accounts that exist. `Staging` is unvended, D35
and Stage 14 multiply Sandboxes, and each new account is assigned its own mapping at vend time. **The
failure is silent** — two peered subnets land in different datacenters, nothing errors, and the only
symptom is cross-AZ transfer at USD 0.01/GB each way on the two peerings D14 and D21 keep constantly busy.
A rule that holds only while the account set is frozen is not a rule (Lesson 5). Re-run `./aws/AZs.py`
after each vend; with `zone_id` anchoring, a disagreement is information rather than a rebuild.

From the check of 2026-08-07, corrected 2026-08-08: `sa-east-1` has endpoints for almost every service
this plan uses — Control Tower, IAM Identity Center, SageMaker (Studio with `ml.t3.medium`, `ml.g5`,
`p5.4xl`), MWAA, Macie, GuardDuty, Security Hub, Lake Formation, Glue, Athena, EFS, ECR, Client VPN,
Network Firewall and Graviton `t4g`. **The exception, missed by the original check: AWS CodeArtifact is
not available in `sa-east-1`** — it exists in thirteen Regions, `us-west-2` among them, and São Paulo is
not one. That is a missing component rather than a price difference: D14 puts CodeArtifact in the supply
chain and egress design B (D5) depends on it as the *only* package path when there is no NAT. A move to
São Paulo would have to replace it (a self-hosted proxy such as devpi, or design A only). The rest of the
answer to "would anything break in São Paulo?" is no; the remaining difference is price, **measured
2026-08-08: roughly 1.5-2.1x**, service by service, in `docs/PRICING.md`. If a move ever became real, the
one genuinely expensive part would be redeploying the Control Tower landing zone, whose home region is
fixed at deployment time.

One cross-region rule is permanent: ACM certificates for CloudFront must live in `us-east-1` regardless of
where the workload runs (relevant only at Stage 13). The region restriction (Stage 1c step 7) governs
`us-west-2` alone, so `acm:*` has to be among the globally exempt actions or Stage 13 cannot issue that
certificate at all. Since D15's revision (2026-08-09) that exemption is unexercised until Stage 13: before
it, ACM is used only to *import* the internal CA's leaves in `us-west-2`, which the region control permits
anyway. Leave the exemption in the policy regardless — adding it later means editing an SCP under time
pressure — and the same applies to `route53domains:*`, whose single use is the registration in Stage 13
step 1. Control Tower's Region deny control carries the restriction.

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

**Resource Control Policies (RCPs)** do the most work here and are the most easily missed: applied at the
OU or organization root, they set a maximum permission on the *resource* side regardless of what any
account-level policy says. They cover **a subset of AWS services, and the subset grows** — S3, STS, KMS,
SQS, Secrets Manager, DynamoDB, ECR, CloudWatch Logs, EventBridge and others. **Re-read AWS's list rather
than trusting a list written here**: a copied enumeration goes stale, and the *gap* between that list and
Access Analyzer's coverage is what the subsection below reasons about. An RCP denying S3 access to
principals outside the organization is, for the stated goal of preventing data leakage, worth more than
Macie — it removes the path instead of reporting on it afterwards.

The symmetric SCP (`aws:ResourceOrgID`) stops the most obvious exfiltration route in a data science
environment: a notebook copying a dataset to a personal S3 bucket in someone else's account. The known
gaps: these conditions do not cover every service, presigned URLs are evaluated under the signer's
identity, and any path that leaves through the *application* layer (an HTTPS POST to an allowlisted site)
is D5's problem, not the perimeter's.

**Implementation note:** none of these policies should be written from scratch. The aws-samples
**`data-perimeter-policy-examples`** repository carries reference SCPs, RCPs and endpoint policies with
the service carve-outs (`aws:ViaAWSService`, `aws:PrincipalIsAWSService`) that every one of these
conditions needs. A perimeter without the carve-outs blocks AWS services acting on your behalf — and the
first casualty in this plan would be Athena reading S3 under Lake Formation, i.e. the exact access path
D13 forces everything through (see Stage 5).

**The second casualty is AWS's own service-owned S3 buckets**, which no condition key covers.
`aws:ResourceOrgID` is a statement about *your* organization, and the Amazon Linux repositories, the
SageMaker image and JumpStart buckets and the SSM/CloudWatch agent buckets are outside it. A `dnf update`
is your credential fetching an object, so `aws:ViaAWSService` is false and the request is denied. Every
place this plan applies a trusted-resources condition therefore needs a companion allow-list of AWS-owned
bucket ARNs: the S3 gateway endpoint policy (Stage 3 step 9) bites first and hardest, since under egress
design B it is the *only* route to those buckets. Treat "which AWS-owned buckets does this environment
depend on" as a maintained list, not as a one-off discovery.

#### Measuring the perimeter — IAM Access Analyzer (Stage 1b step 8.2)

The three axes above are preventive, and **a preventive control that works is silent**. Nothing in that
table emits a signal saying the perimeter holds; a missing carve-out and a missing policy look identical
from outside. IAM Access Analyzer's external-access findings are that signal, and they are free: with the
organization as the zone of trust, it enumerates every supported resource whose resource-based policy grants
to a principal outside it, by logic-based reasoning over all possible requests rather than by matching
patterns. D6 carries its place in the DLP strategy; what belongs *here* is its relationship to these three
axes.

**Read the findings before attaching the RCPs, not after.** They are the inventory of what an organization-
wide `aws:PrincipalOrgID` deny is about to break — AWS's own recommended order, and the second reason 8.2
comes before Stage 1c is repeated in code at Stage 2.

**The two coverage sets do not coincide**, and the difference is where this perimeter is blind:

| Reachable from outside the organization, and… | Resource types |
|---|---|
| …an RCP can deny it — the analyzer is a *check* on the perimeter | S3 buckets and directory buckets, KMS keys, SQS queues, Secrets Manager secrets, DynamoDB tables and streams, ECR repositories, IAM role trust policies (via `sts`) |
| **…no RCP reaches it — the analyzer is the *only* control** | **Lambda functions and layers, SNS topics, EBS volume snapshots, RDS DB and DB-cluster snapshots, EFS file systems** |

Two entries in the second row are data-bearing *in this design*, which turns an informational finding into
an operational one. **An EBS or RDS snapshot shared with an account outside the organization is a
whole-volume or whole-database copy, and no policy in the axis table can stop it** — the sharing is an
EC2/RDS API call against a resource type the RCP list does not cover. For these, "the perimeter contains
it" — the sentence D19 leans on — is not true, and D19 was narrowed on 2026-08-12 to say so. (EFS was the
third data-bearing entry until 2026-08-17, when the NFS requirement was withdrawn and D24 with it.)

The snapshot route is closed preventively after all — not by the axis table but **beside** it, with an
unconditional SCP deny on `ec2:ModifySnapshotAttribute`, `ec2:ModifyImageAttribute` and the RDS pair, in
**Stage 1c step 7.5**. The asymmetry: **RCPs are limited to a service list; SCPs are not.** So a resource
type the trusted-identities axis cannot reach is often still reachable from the trusted-resources side,
and "no RCP covers it" is a reason to look at the identity half rather than to fall back on detection. EFS
used to be where that ran out — no RCP, no SCP worth writing, only the analyzer's finding for a control,
an accepted risk destined for Stage 11's deliverable; the NFS requirement's withdrawal (2026-08-17)
retired the risk along with the filesystem.

Two structural exemptions are holes in the axis table that no amount of policy authoring closes: **RCPs do
not apply to resources in the management account**, and **not to service-linked roles** — principals
created by services rather than chosen by anyone (Lesson 17). The analyzer sees both.

**Region portability (§4.1) reaches this too, and silently.** An external-access analyzer only analyzes
resources in **its own Region**. One analyzer in `us-west-2` is complete exactly while the environment is
single-region; the day a second Region is added, the perimeter stops being measured there and nothing says so
(Lesson 13). Region-count is therefore an input to §4.1's cost of moving, not only to the resource inventory.
*(Unused-access findings are the exception — they are not Region-scoped.)*

Access Analyzer's **custom policy checks** (`CheckNoNewAccess`, `CheckAccessNotGranted`,
`CheckNoPublicAccess`) are the mechanism that would make these perimeter rules fail a merge request
instead of relying on review, the natural home being the Terraform pipeline over `terraform-live/`.
**No stage owns it**: it is recorded as an available mechanism and an open gap, not as a control
(Lesson 5).

---

### 4.3 The two egress designs (D5)

Rather than pick one mechanism up front, Stage 6 builds both and measures them. They answer the "SageMaker
should have access to the internet" requirement in `CLAUDE.md` in opposite ways; building both measures
what the strict one costs in day-to-day friction.

**Whose internet this is about** (user clarification, 2026-08-25; `docs/plan/objectives.md` carries the
requirement text). Both designs constrain the **SageMaker-managed compute** and nothing else. The **client
plane** — the laptop on the VPN — has its own egress: all of its internet runs through the cloud's single
egress point behind an institutional **HTTP/HTTPS proxy** (monitored, broad; D6's territory, Stage 11's
build, open question 23's topology), and that plane serves the SMUS portal's public-internet requirements.
Three consequences. The (A)/(B) gap is smaller than the names suggest: with a whitelist as the mechanism,
(B) is the empty list and (A) a short one, and under both designs the compute reaches the *intranet*
(GitLab included) identically. Every allowed compute connection still crosses the institutional proxy —
two filters, the proxy's and then SageMaker's stricter one, so the compute's effective reach is the
intersection. And the lab's per-account NATs are the **interim** shape of an egress that converges on one
point; the comparison below measures the designs, not the interim topology.

**(A) Limited internet — NAT plus allowlist.** The SageMaker private subnets route to the NAT gateway;
Route 53 Resolver DNS Firewall permits an explicit list of domains and blocks the rest, optionally with a
Squid proxy for HTTP-layer control. **The list itself is not written here and is not in the module
either** — since `vpc-egress-v0.3.0` the module default is empty, and each `egress/` slice declares the
set its own account may reach.

**Measured 2026-08-23 (Stage 6 step 4.3), then repaired the same day.** DNS Firewall evaluated the **whole
resolution chain**, so a listed name whose CNAME target was unlisted was blocked. Every package ecosystem
serves its **artifacts** from a shared CDN — `files.pythonhosted.org`, `index`/`static.crates.io`,
`static.rust-lang.org`, `sh.rustup.rs`, `pkg.julialang.org`, `cloud.r-project.org`, `deb.debian.org`,
`archive.ubuntu.com`, `public.ecr.aws` — so an allow-list of *names* carried every index and had **no
download path**, and the only apparent repair was to allow `*.fastly.net`, `*.cloudfront.net`,
`*.cdn.cloudflare.net` and friends: **self-service namespaces** anyone can publish into, which ends the
control.

**It was the API default.** `FirewallDomainRedirectionAction` is a per-rule setting with a second value,
`TRUST_REDIRECTION_DOMAIN` (released 2024-05); `terraform-modules/vpc-egress` had never set it and so took
`INSPECT_REDIRECTION_DOMAIN`. Since **`vpc-egress-v0.4.0`** it is a module **input** whose default stays
`INSPECT`, and **each `egress/` slice declares its own**, beside the allow-list it governs. Both
Interactive slices pass `TRUST`: the firewall inspects the **queried** name and trusts the chain beneath
it. Production, which sets no list at all, is untouched. **This does not open the CDN:** the trust is
scoped to a single query transaction, so a redirection target *queried directly* is evaluated
independently, matches nothing and is blocked by the catch-all. The estate gets the artifact hosts without
the namespace they sit in — twelve hop entries came off the Sandbox list, one off Development's, and each
removal is a narrowing.

**A's weakness** is that name filtering is bypassable by a raw IP — strong against accident, weak against
intent — and by **asking a different resolver**. DNS Firewall only inspects what the VPC resolver is
asked, and nothing stops a process from reaching `1.1.1.1:53` over the NAT or DoH on 443: the tier
security groups permit all egress and the NACLs are at the default allow. Neither bypass is closable at
the DNS layer; both need an **SNI/Host** control (AWS Network Firewall's stateful domain list, or an
explicit proxy — §4.3a). That, and not the CDN chain, is why design B is the shape regulated institutions
converge on.

#### 4.3a L7 options, priced but not built

Both bypasses above are invisible to a DNS control and visible to one that reads the **connection**. Two
shapes exist; they are recorded so a future session does not re-derive them.

| | Where it matches | Measured cost (`us-west-2`) | The catch |
|---|---|---|---|
| **AWS Network Firewall**, stateful domain list | **TLS SNI** and **HTTP Host** — never DNS, so the CNAME chain is irrelevant by construction | USD **0.395/h** per endpoint + **0.065/GB** (`docs/PRICING.md`) | ~USD 288/month **always-on**, against a USD 50 ceiling (D12) — but `egress/` is `[E]`, so an 8-hour session is ~USD 3.16. The monthly figure is the one that made this look unaffordable; the hourly one is what this estate actually pays. Still ~8× the NAT |
| **Explicit HTTP `CONNECT` proxy** (Squid) — **chosen, and built at [Stage 6c](stages/stage-06c-networking-hub.md) under [D38](decisions/D38-single-egress-hub.md)** | the `CONNECT` line, which is plaintext to the proxy — so it survives **ECH**, which will eventually blind SNI matching | **0.0104/h**, the `t3.micro` that was built (settled 6c step 7.4, 2026-09-06). `PRICING.md` §8. It began as a `t3.nano` at 0.0052 and was sized up because **`dnf` was OOM-killed on 415 MiB**. **It charges nothing per GB**: a NAT gateway adds 0.045/GB of processing and an EC2 proxy adds none | an EC2 to run and patch; every tool needs `http_proxy`/`https_proxy` (pip, cargo, `Pkg`, R, apt, the container runtime); and the proxy must resolve **outside** the DNS Firewall, so it needs its own resolver or a VPC without the rule-group association |

Neither is a Stage 6 deliverable. They answer *"the requirement is SNI, not name"* — a different
requirement from the one design A was built for. The objectives state an institutional **HTTP/HTTPS
proxy** between the VPN-connected client and the cloud's single egress, which every compute connection
also crosses, so the explicit-proxy row above is a **candidate shape for a stated requirement**. The
objectives name only "an HTTP/HTTPS proxy", so which shape is built (this row, or Network Firewall's) is
open question 23's to settle; the build belongs to Stage 11's egress-control leg, and the row's two
catches (every tool needs `http_proxy`/`https_proxy`; the proxy resolves outside the DNS Firewall) are
design inputs rather than reasons not to build it.

**(B) No internet — proxied artifacts only.** The SageMaker subnets have no route to a NAT gateway at all.
Packages arrive through **CodeArtifact** repositories configured with an upstream to the public registry
(CodeArtifact itself fetches from the internet — AWS-side, not through your VPC), container images through
**ECR pull-through cache**, and everything else through VPC endpoints. There is no egress path to misuse.
It also removes the NAT gateway, at the price of the two CodeArtifact interface endpoints: a net saving
of **~USD 0.030/h** (`docs/plan/cost-model.md`).

**The endpoint list omitted `athena`, `glue` and `lakeformation` until 2026-08-08, which nearly made
design B unbuildable.** Under design A the NAT hid that; under design B there is no NAT, so the design as
written could not have executed a single query — and D13 routes *every* tabular read through an LF-aware
engine, which is the whole access path. The three are now in the common core of both designs (Stage 3
step 8), which raises both designs' cost and leaves **the saving above as the NAT alone**. Three cents an
hour decides nothing: the comparison below is settled by friction, which is what D5 said it wanted to
measure.

**The SMUS portal requires the public internet**, and that lands on the client plane rather than on (B)
(2026-08-24, re-scoped by the user 2026-08-25). AWS's network-isolation page carries a *Public internet
access* table beside its required-endpoints one: client assets, client APIs
(`agent.datazone.<region>.api.aws` among them) and the IdC sign-in endpoints, *"for client operations that
do not handle customer data"* in the page's own words. The portal is loaded by the *client's browser*, and
the client plane has its own monitored egress — VPN → institutional proxy → the cloud's single egress —
which is where those public names are served; (B) constrains the compute VPC, which never needed to host
the portal experience. What is still load-bearing: **the client's DNS path must not be shadowed by the
compute's endpoints**. An interface endpoint installs a private zone **authoritative for the whole
subtree** of its service name (Lesson 40; `NETWORK.md` §5 carries the measured case, the `datazone` zone
shadowing exactly the `agent.datazone…` name the portal needs), and the full-tunnel laptop shares the VPC
resolver by requirement. So the constraint on (B) — and on (A) equally — is which endpoints may exist in a
VPC whose resolver the *client* also uses, not whether the portal can live at all.

**The user's reservation about (B), recorded as a constraint:** this environment must support **Python,
Julia, Rust and R**, and CodeArtifact does not cover all of them:

| Ecosystem | CodeArtifact | Fallback if not covered |
|---|---|---|
| Python (PyPI) | Supported | — |
| Rust (Cargo) | Supported — **confirm at Stage 6**, this is a comparatively recent format | `cargo vendor`, or a `panamax` mirror on S3 |
| Julia (Pkg) | **Not supported** | Self-hosted `PkgServer.jl` storage server, or bake into the dev-env image, or allowlist `pkg.julialang.org` |
| R (CRAN) | **Not supported** | Posit Package Manager (commercial), a `miniCRAN` mirror served from S3, or bake into the image |
| OS packages (dnf/apt) | Not applicable | Distro mirror on S3, or bake into the image |

**That rebuild has a gate in it**, which is a real cost to this comparison: the `dev-env` image is
released through its own promotion chain with an approval by the **Dev Env Steward** (Stage 8 step 1).
Under design A a missing Python package is a `pip install` in the notebook; under design B it is a merge
request, a build, a scan and a human approval. That is the right governance for a runtime everyone shares,
and it is the friction the Stage 6 verdict has to measure rather than average away. Whether the gate can
be automated at all is `INT-17`.

**The dev-env container image is itself the dependency delivery mechanism.** It is built by a CI pipeline
(Stage 8) on a runner that *does* have internet, so Julia, R, Rust and their package sets are installed at
build time and arrive in SageMaker pre-installed. A package proxy is then only needed for *ad-hoc*
installation during exploration — mostly Python, which CodeArtifact does cover. Design (B) therefore
requires solving one ecosystem rather than four, and making image rebuilds cheap enough that the other
three are not painful. Whether that holds in practice is what Stage 6 is meant to find out.

**Deliverable of the comparison** (Stage 6): a written verdict covering, for each design, the measured
hourly cost, what breaks in a normal working session, how long a "I need package X right now" loop takes,
and what an intentional exfiltration attempt achieves. The plan does not pre-commit to a winner.

---

## The mental model

A mental model, not a status. Every old habit contradicts some part of it.

- **The environment roles sit on one axis, lifecycle** (Stage 6b converted `Development` into `Staging` on
  2026-09-06, D21 superseded): Sandbox (experimentation — the unit of work is a notebook, and the only
  account where a human runs code), Staging and Production (deployment targets, written only by the
  pipeline). Promotion runs **Staging → Production**; Sandbox feeds the pipeline through **git
  graduation**, never through a pipeline of its own.
- **A role is not one account: `Sandbox` is one account per business unit (D35).** The chain is
  **N Sandboxes → one Staging → one Production**, so the cardinality boundary is the same line as the
  graduation boundary above — experimentation multiplies, the engineering chain after it does not, and the
  promotion chain is therefore untouched by N. N is 1 today. Per-unit isolation ends at that line; past it,
  isolation is Lake Formation's job and not an account boundary's.
- **The accounts fall into groups, not into one sequence** (`docs/ORGANIZATION.md` carries the per-account
  classification): the **lifecycle** axis (Sandbox → Staging → Production), the **ownership** axis (Data
  Governance alone), and the **platform** accounts on neither — the organization's own machinery, serving
  every account and belonging to no environment. *An account off the lifecycle axis is not "a production
  account"*: Data Governance and Identity are **high blast radius**, which is a different property from
  being production.
- **One account is off that axis entirely:** Data Governance (D22) owns the governed lake; every
  environment reaches it through Lake Formation cross-account shares — read for Sandbox/Development, read
  plus **governed write** for Production's job role (the producer path). Nobody signs in to it
  interactively.
- **What each OU carries is not uniform (D23).** Read it per OU:
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
    **The rule (D37, settled by the user 2026-08-13, and it governs Stage 14 as much as Stage 1c):
    nothing is attached or enabled on `Sandboxes` — no SCP, no RCP, no tag policy, no Control Tower
    control — *unless it is a configuration that differs from `Interactive`'s*.** Sameness is expressed by
    inheriting, never by copying.
    **Measured:** Stage 1c 7.6 proved the SCP half — `sagemaker:CreateNotebookInstance` is denied in
    `awsds-infra-sandbox-1` by `Interactive`'s document, with nothing on `Sandboxes` — and 7.7 proved the
    OU *can* take an enablement of its own, so carrying nothing is a choice rather than a limitation.
    **What it costs is Control Tower's own reporting**: an enabled control is per OU and is *not*
    inherited as an enablement, only the SCP statements it emits are. So `Sandboxes` reads as having zero
    controls while its accounts are fully governed, and the drift view is not the ceiling. Read the parent
    when asking what applies to a Sandbox account. **What it buys is Lesson 14 in reverse**: a duplicated
    statement is a second place to forget an amendment, and the `ExemptAssumeRoot` omission is the worked
    example of that failure.
  - **`Interactive` carries a one-statement set** (Stage 1c step 7.6, decision 1, 2026-08-13): deny
    `sagemaker:CreateNotebookInstance` and `CreatePresignedNotebookInstanceUrl`. It holds Development plus
    the nested `Sandboxes`, it is the only OU where a domain may exist (D17), and every *other* interactive
    surface is allowed there because nothing denies it — the organization-root set plus that one statement
    is the whole ceiling. What holds infrastructure change off the data scientist is
    `DataScientistAccess`, an **identity** policy, not this OU.
    **Why that statement and nothing more:** the classic notebook instance is the one interactive
    surface this design uses nowhere — Unified Studio notebooks and VS Code are *spaces and apps*
    (`sagemaker:CreateSpace`/`CreateApp`) — so denying it needs **no carve-out at all** and binds the
    builder as hard as anyone, which is what separates a control from a convention. Any broader deny here
    would have to exempt the identity that *builds* these accounts, which is the shape D30 had reverted.
  - **`Policy Test` (D29) carries none on purpose** — it is where a *candidate* SCP/RCP is attached and
    exercised against the disposable `Policy Canary` account before it reaches anything real. It exists as
    an account and not just a folder because an SCP is only evaluated when a principal makes a call, so an
    empty staging OU tests nothing; and the test principal is an **administrator**, because a deny
    exercised by a principal that lacked the permission anyway proves nothing about a ceiling. Never call
    it "Policy Staging" — that is the industry term and it collides with the `Staging` account, which is
    exactly what the naming avoids.
- **One unified domain, projects as the isolation unit (D26):** the DataZone V2 domain is registered in
  **Data Governance** because a domain is a registry of projects and data products — ownership axis, not
  lifecycle axis. **It holds no compute:** the
  `experimentation` project profile provisions into Sandbox, `engineering` into Development, and nothing
  is ever provisioned into the domain account itself. Sandbox×Development is therefore *strengthened*, not
  dissolved — it stops being "which URL did the person open" and becomes a property of the project.
  Lakehouse blueprint in its Glue/Athena form only — **never** the Redshift Serverless variant.
  Staging and Production are never associated. What crosses the gate is
  the D28 artifact set — image, workflow YAML in S3, per-workflow role, orchestration resource, log
  group, model package group — carried by the project's git repository, linted against domain-scoped
  references.
- **D18** gives the data scientist read-only permission sets on Staging and Production (data plane, no
  compute); **D19** keeps the derived zone designed rather than left over — since 2026-08-26 it is the
  SMUS project path, per project, the service's hand.
- **There are two access paths.** "The VPN is the only entry point" is true because the tunnel is *full*,
  not because it routes into every VPC. Only Sandbox and Production are reachable at the VPC level;
  Development and Staging are used entirely through AWS API endpoints exited via the WireGuard Elastic IP
  — including the Unified Studio portal, which is a public endpoint even when project compute is
  VPC-only. The control there is `aws:SourceIp`, never `aws:SourceVpce` (`docs/plan/architecture.md` §3),
  and **INT-16 answered** (2026-08-22, at Stage 6): that control does not reach the portal. The portal is
  entered by an Identity Center sign-in, not by an IAM-authorized call under a permission set, and the
  off-VPN reading took the strong form — the whole interactive surface works with the tunnel down,
  JupyterLab included (`VpcOnly` governs the app's egress, never the user's ingress). The condition covers
  the API/console half only; the closing choice — fallback (i) on the domain execution role versus
  recorded acceptance — is the user's, deferred, presumed nowhere.
- **D24 (withdrawn 2026-08-17):** the NFS requirement left `objectives.md`, and the shared filesystem
  with it; the exchange between Sandbox and the pipeline is S3 and git. **D25:** the ingestion drop-box is
  picked up by Production's job role on the producer path — which also closed a hole where the `Data` OU
  SCP never denied Glue jobs.

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
