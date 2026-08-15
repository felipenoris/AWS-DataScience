# Stage 6 — SageMaker Unified Studio

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stages 3, 4, 5, and the ECR/CodeArtifact repositories from Stage 7 step 5 — **pulled forward**, because under egress design B they are how packages arrive, so they cannot come after the thing that consumes them. **D5 is executed, not decided, in this stage**: both designs get built (`plan/architecture.md` §4.3). **Also: D36's `production/pki/` slice is applied before this stage**, not at Stage 7 where the CA is first *used* — the `dev-env` image built for these projects has to already trust the root (INT-19). |
| **Consumes** | [D5](../decisions/D05-sagemaker-egress.md), [D12](../decisions/D12-budget-ceiling.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D14](../decisions/D14-supply-chain-account.md), [D21](../decisions/D21-development-account.md), [D24](../decisions/D24-shared-filesystem.md), [D26](../decisions/D26-unified-studio.md), [D28](../decisions/D28-workflow-contract.md), [D35](../decisions/D35-sandbox-cardinality.md), [D36](../decisions/D36-internal-pki.md) |
| **Proves** | [INT-01](../integrations.md), [INT-09](../integrations.md), [INT-12](../integrations.md), [INT-13](../integrations.md), [INT-15](../integrations.md), [INT-16](../integrations.md), [INT-17](../integrations.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** the data scientist's working environment — since the 2026-08-08 revision (D26), one
SageMaker unified domain (DataZone V2) with projects, rather than two classic Studio domains.

**Four mechanics of the product, read off AWS's documentation on 2026-08-13 when `CLAUDE.md` named six
Unified Studio features as objectives.** They are here rather than in the steps because each one changes
what a step has to *decide*, and the first one contradicts a principle rather than a detail. The full
statement of each, with its reference, is [`plan/open-questions.md`](../open-questions.md) items 12-15.

| What the product does | What this stage owes because of it |
|---|---|
| **Notebooks run Spark on Amazon Athena for Apache Spark by default, and Athena for Spark does not support VPC.** The VPC-capable runtimes are EMR Serverless, EMR and Glue, selected per notebook; the Admin Guide documents disabling Athena Spark under *Network isolation* | **Disable it, and choose the runtime deliberately** — a notebook whose compute is outside the VPC is outside the endpoint policies, the flow logs and every `aws:SourceVpce` condition the data perimeter is built from (principle 4, `plan/architecture.md` §4.2). Price the replacement: the default was free of hourly cost and EMR Serverless and Glue are not |
| **Notebooks do not support trusted identity propagation.** In an Identity Center domain they use *compatibility permission mode*, so data access resolves through the project/compute role, not the signed-in human | Decide, and write down, **what the real grain of D13's fine-grained access is**: per-user Lake Formation row/column filters describe a *user*. Either the SQL path carries per-user identity and the notebook path does not — which is a two-grain design and has to be said out loud — or the grain is the project, and `CLAUDE.md`'s DLP objective is met at that grain with the difference recorded |
| **`sagemaker:StartSession` attaches a local VS Code to a running space** — a `CLAUDE.md` objective, and a file-transfer channel to a laptop that no browser-side restriction reaches | This is the concrete form of open question 6, not a separate one. AWS documents tag-scoping `StartSession` to a user's own private apps; that is the lever, and whatever is left over is an accepted risk in **Stage 11**'s threat model rather than an unexamined one. 1c denies the action everywhere it should not happen and deliberately not here |
| **"As many spaces as they like" is billed by the hour**, and **workflows are MWAA** (serverless or provisioned) | D11 is a property of the design, not of the user's habits: **idle shutdown plus a restricted instance-type list** is what closes it, priced into `plan/cost-model.md` against the USD 50 ceiling. The workflows half *confirms* D7/D28 — this feature and Stage 10's orchestration comparison are one surface |

**Read this before the steps, because it is the thing most easily misread:** the domain is registered in
**Data Governance**, but *no compute runs there*. A domain is a registry — projects, profiles, blueprints,
memberships, the catalog. The compute lands in whichever account the project profile names, which is
Sandbox for `experimentation` and Development for `engineering`. So this stage builds one resource in the
Data Governance account and provisions working environments into the two Interactive accounts, and the
Sandbox/Development boundary from D21 comes out of it stronger rather than weaker: it stops being "which
URL did the person open" and becomes a property of the project they opened.

**Prerequisites:** Stages 3, 4, 5, and the ECR/CodeArtifact repositories from Stage 7 step 5 — **pulled
forward**, because under egress design B they are how packages arrive, so they cannot come after the thing
that consumes them. **D5 is executed, not decided, in this stage**: both designs get built (`plan/architecture.md` §4.3).

**And one prerequisite that is not a stage: a `dev-env` image has to already exist in the Production ECR.**
This stage cannot borrow it from Stage 8, which is where the pipeline that builds it lives — and that
pipeline runs on GitLab runners, which are Stage 7. Following that chain honestly, Stage 6 depended on two
later stages, which is why the egress design B comparison could not have been completed as written.

**The resolution, decided 2026-08-08:** the first `base` and `dev-env` images are built **by hand**, locally,
and pushed to the Production ECR before this stage starts. Concretely: build them from the same
`Dockerfile`s that Stage 8 step 1 will later own, on the laptop, `docker login` to ECR through the tunnel,
tag immutably, push. Nothing about the images is provisional — only the thing that built them is. Stage 8
then takes over authorship of exactly the same artefacts, and its first successful pipeline run is verified
by producing a byte-comparable image rather than a different one.

Two consequences worth stating rather than discovering:

- **This is the only place in the plan where an artifact reaching an account is not built by a pipeline**,
  which is precisely the property D14 and Stage 8 exist to guarantee. It is acceptable exactly once, at
  bootstrap, on an image that is replaced by a pipeline-built one at Stage 8. Record the digest of the
  hand-built image in `log/log-stage-06-unified-studio.md`, so the changeover is visible.
- **The `plan/architecture.md` §4.3 verdict on egress design B is provisional until Stage 8.** Design B's whole claim is that
  the image *is* the dependency delivery mechanism, and the usability of that claim depends on how long a
  rebuild takes — which is a property of the pipeline, not of a laptop build. So Stage 6 step 6 measures
  everything else and marks the rebuild-loop number as "measured on a laptop, re-measure at Stage 8". The
  choice that closes D5 can be made here; the number behind it is confirmed there.

**To execute:**

0. **Before anything else: prove that 1c's `datazone:CreateDomain` deny lets *this* account through.**
   Step 1 creates the domain, and the deny that governs it — `DenyDataZoneDomainOutsideDataOu`, in
   `awsds-org-scp-baseline` on the organization root — **was never exercised in either direction.** Stage 1c
   step 7.3 tried, and found the probe unrunnable: DataZone validates `--domain-execution-role` *before*
   authorization, so a call with a throwaway role returns `Cross-account pass role is not allowed` and never
   reaches the SCP. That the same error comes back from the exempt account is what proved the probe measures
   nothing, not that the carve-out works.

   **The failure direction is closed, not open, which is why this is step 0 and not a verification at the
   end.** The condition is `ForAllValues:StringNotLike` on `aws:PrincipalOrgPaths`, and **a `ForAllValues:`
   operator over a multi-valued key that does not populate evaluates *true*** — so if DataZone requests do
   not carry `aws:PrincipalOrgPaths`, the deny applies to **everyone, including `Data`**, and step 1 simply
   cannot create the domain. Discovering that while debugging a Terraform apply costs an evening; the probe
   below costs one call.

   Run it as the principal that will own the domain, in **Data Governance**, with a role DataZone will
   accept — the module's own execution role, or one created for the purpose with a `datazone.amazonaws.com`
   trust policy. Three outcomes, and they are distinguishable:

   | What comes back | What it means |
   |---|---|
   | the domain is created | the carve-out matches. Delete it if step 1 is going to create it properly, and carry on |
   | `AccessDenied … explicit deny in a service control policy` | **`aws:PrincipalOrgPaths` is not populating for DataZone.** Stop. The statement has to be re-keyed — `aws:PrincipalAccount` against the enumerated Data Governance account is the fallback, and it is a 1c amendment run through [`plan/runbooks/scp-battery.md`](../runbooks/scp-battery.md), not an edit made here |
   | any DataZone validation error (`Cross-account pass role…`, trust-policy failures) | the probe is still not reaching authorization. Fix the role before reading anything into it — this is the outcome Stage 1c already had, and it is not evidence |

   **And run the negative half in the same sitting**, from any account outside the `Data` OU: the same call
   must come back with the explicit-deny wording. Without it, "the domain was created" is equally consistent
   with the statement never firing anywhere — which would mean any account can create a domain, and INT-12's
   one-domain-per-account fallback has already happened by accident.

   **Second half of the same preflight, and it is about a different document: `sagemaker:Create*` is denied
   in Data Governance** by `awsds-org-scp-ou-data` (1c step 7.6, measured — five denies in that account).
   This step's whole premise is that the domain account is a *registry* and no blueprint is enabled there,
   which is what makes that wildcard free. **Verify the premise before the apply, not during it**: if the
   `aws-ia` module — or SMUS itself, on domain creation — provisions anything SageMaker-shaped in the domain
   account, the apply dies half-built, in the account where a half-built domain is hardest to unpick. A
   `terraform plan` that shows no `aws_sagemaker_*` or `awscc_sagemaker_*` resource in
   `data-governance/governance/` answers it; a single `sagemaker:Create…` in the plan output is the signal
   to stop. **The correction in that case is to re-check "no blueprint enabled in the domain account", never
   to weaken the OU document** — the wildcard is the statement that no user compute exists in the lake
   account, and a carve-out shaped like "except what SMUS needs" is that statement withdrawn.

1. **The unified domain (D26), from the official module** — `aws-ia/terraform-aws-sagemaker-unified-studio`
   (`aws` ≥ 6.51 for the domain and its IAM roles, `awscc` ≥ 1.89 for project profiles, blueprints and
   projects): a single **DataZone V2 domain** in the **Data Governance** account
   (`data-governance/governance/`), authenticating through
   Identity Center. **Check before creating anything:** the domain must live in IdC's home Region
   (`us-west-2` if Stage 1 went as planned) — neither can move afterwards. Account associations through
   the org-wide RAM sharing Stage 1d step 11 enabled (INT-12): **Sandbox** and **Development**;
   **Staging and Production are never associated** (D28). **And under D35 the associated set is not two
   accounts but N + 1** — one Sandbox per business unit plus the single Development — each needing its own
   blueprint configuration against the same single domain. That is the intended mechanism, so it scales; what
   it makes heavier is the root deny on `datazone:CreateDomain` (1c step 7), because with many sandboxes the
   pressure to let a unit "just create its own domain" is exactly what that deny exists to resist, and
   INT-12's one-domain-per-account fallback gets more expensive with every unit. Two project profiles:
   **`experimentation`**,
   whose blueprints provision into Sandbox (the unit of work is a notebook), and **`engineering`**,
   provisioning into Development (the unit of work is a pipeline) — the D21 graduation is the move of code
   between the two projects' git repositories, unchanged in substance. **The domain account is not a
   provisioning target for anything**: no blueprint is enabled in Data Governance itself, which is what
   keeps the `Data` OU's "no user compute" true while the registry lives there. Blueprints enabled and no
   others:
   **Tooling**; **Lakehouse Catalog in its Glue/Athena form — not the Redshift Serverless variant**
   (D26, D12); and **ML experience**, whose per-project SageMaker AI domain runs in **VPC-only** mode in
   the private subnets with the interface endpoints from Stage 3 — including `sagemaker.studio`, without
   which it will not start. The deployment targets never get a domain or an association: unreviewed code
   must not reach the accounts the split exists to protect, and the SageMaker runtime they carry (Stage 9)
   is submitted to by pipelines, not by people. The escape hatch for "I need to debug a production job
   interactively" is a time-boxed elevated role approved by the **deployment manager**, logged and alarmed — designed in
   Stage 9, not improvised on the night it is first needed.
2. Execution roles per project (the one-role-per-workflow discipline of D28 starts here, not in
   production), honouring **D13**: no `s3:GetObject` on Lake Formation-registered prefixes. Project
   membership maps to Identity Center users and groups, which is what replaced the classic per-user-profile
   mapping when D26 dropped the classic domains.
   **This is INT-15 and it is the step of this stage most likely not to work as written.** D13 assumed
   these roles were authored here, in Terraform. Under D26 the ML and Lakehouse blueprints provision the
   project environment *and its roles*, so what this step can actually do may be limited to constraining
   them from outside — a permissions boundary attached through the `sandbox/sagemaker/` and
   `development/sagemaker/` prerequisite slices — rather than writing them. **Find out before building
   anything on top:** provision one throwaway project, read back the policies attached to its role, and
   check whether a boundary imposed from the prerequisite slice survives a blueprint reconciliation. INT-15
   carries the fallback chain in order. If none of it holds, the outcome is recorded as an incomplete
   control rather than absorbed by widening D13 — D13 is the reason the fine-grained access objective in
   `CLAUDE.md` is a control and not a decoration, and it is worth knowing which of the two it turned out
   to be.
3. **Lock down what the notebook can create, not just what the domain can reach.** A VPC-only domain
   constrains Studio itself; it does not constrain training, processing or transform jobs launched from a
   notebook through the API, which accept their own network configuration and will happily run outside the
   VPC. Add IAM conditions to the execution role and the permission set:
   `sagemaker:VpcSubnets` and `sagemaker:VpcSecurityGroupIds` (deny when null), `sagemaker:NetworkIsolation`,
   `sagemaker:InterContainerTrafficEncryption`, `sagemaker:VolumeKmsKey`. Add `sagemaker:InstanceTypes` as
   well: it is the only control that actually stops a USD 30/hour GPU instance from being started by a
   misplaced parameter, and idle-shutdown does not help within the first hour. Without this step, the
   entire VPC-only design is one API call away from being bypassed.
4. **Build egress design A (`plan/architecture.md` §4.3):** NAT route plus Route 53 Resolver DNS Firewall with an explicit
   allowlist (PyPI, CRAN, the Julia package server, crates.io, the distro mirrors, the GitLab host).
   Everything else denied and logged.
5. **Build egress design B (`plan/architecture.md` §4.3):** the same domain with no NAT route at all; packages from CodeArtifact
   (cross-account from Production, per D14 — a CodeArtifact domain policy grants the Sandbox **and
   Development** accounts) and
   images from ECR pull-through cache. Julia, R and the Rust toolchain arrive pre-installed in the dev-env
   image rather than through a proxy.
6. **Compare them and write the verdict** (the deliverable in `plan/architecture.md` §4.3): measured hourly cost, what breaks in a
   normal session, how long the "I need package X right now" loop takes, and what a deliberate
   exfiltration attempt achieves under each. Then choose, and record the choice as the closure of D5.
   **Mark the rebuild-loop number as provisional** — it is measured against a hand-built image here and
   re-measured against the Stage 8 pipeline, per this stage's prerequisites.
7. Attach EFS access points for the shared NFS area (Sandbox only, D24).
   **To verify rather than assume, and it is a `CLAUDE.md` requirement rather than a convenience:** D24 and
   the NFS objective were written against classic Studio, where the domain's `DefaultUserSettings` accept a
   custom EFS file-system configuration. Under D26 the app is a project environment provisioned by the ML
   blueprint, and whether an additional EFS access point can be attached to it — and through which
   parameter — is not known. Check it here. Fallbacks, in order: (i) mount the EFS from inside the app with
   the EFS mount helper, if the container has the privileges and the security group path (the interface is
   then a documented command rather than a provisioned volume); (ii) restrict the NFS requirement to its
   actual use case, which `CLAUDE.md` states as exchanging files between *users*, the SageMaker environment
   and S3 — the laptop-side mount over the tunnel (step 11 of Stage 5) already delivers two of the three;
   (iii) accept S3 as the exchange path from inside the project and record the POSIX filesystem as
   unavailable to project compute, which is a real reduction in scope and belongs in `plan/institutional-delta.md` next to the
   existing "Development has no shared filesystem at all" row.
8. Lifecycle configuration for idle shutdown — mandatory cost control.
   **Layers: the domain and its projects are `[P]`; only the running apps are `[E]`.** A DataZone domain at
   rest bills metadata only, and the per-project SageMaker AI domain the ML blueprint provisions bills
   nothing until an app runs — so destroying either one each session would buy nothing and would create two
   problems: the orphaned-home-EFS hazard (a SageMaker domain's `RetentionPolicy` defaults to `Retain`, so
   every teardown leaves a billing filesystem behind unless it is deleted explicitly) and the churn of
   domain IDs, project IDs and Identity Center mappings on every `make up`. `make down` deletes running
   *apps* only — through the per-project SageMaker AI domain, not through DataZone, which owns no compute
   (`plan/conventions.md` §6). **Project home directories are scratch** by policy: notebooks live in GitLab, data lives in S3,
   shared files live on the Stage 5 EFS — and the home directories stay small, so their storage rounds to
   cents. State this to users explicitly.
9. CloudWatch log groups and metrics for the domain.

**To verify rather than assume** (INT-01 and 2 carry these with their fallbacks): whether a Studio
custom image can be pulled from the **Production**
account's ECR (D14) — the BYOI documentation is strict about region and thin on cross-account; if it
fails, the fallback is a native ECR cross-account replication rule into a repository in **each Interactive
account**, not a pipeline.
**And the question INT-01 does not answer, which is `INT-17`: what makes an image *selectable* at all.**
Pulling the image cross-account and having it appear in the project's image selector are two different
mechanisms, and only the first has a row of its own. Until D26 the second was ours end to end — image,
image version, app image config, attached to a domain this repository wrote. The attachment point now sits
inside the blueprint-provisioned SageMaker AI domain. **Answer this on the same throwaway project used for
INT-15, and answer it before step 6's egress comparison begins:** the whole claim of design B is that the
`dev-env` image is the dependency delivery mechanism for Julia, R and Rust, so a design B measured without
a working custom image is a design B missing three of its four ecosystems, and the comparison would be
decided by a defect rather than by the trade it exists to measure. Record the mechanism — the Stage 8
step 1 pipeline is written against it. And whether SageMaker Studio offers any supported way to disable file
download or notebook export from the JupyterLab UI. As far as this plan knows it does not, and Stage 11
step 3 should not be written as though the control exists. If it does not, the honest position is that
preventing a determined user from taking data out through their own browser session requires a different
architecture (streaming desktop, or no direct data access at all), and everything else is detection.

**Deliverables:** the data scientist logs in through the VPN, opens the unified portal, works in the
`experimentation` project (compute provisioned in Sandbox) and in the `engineering` project (compute in
Development), installs a package, reads a lake table through Athena over the LF share — surfaced as a
subscribed asset in SageMaker Catalog — writes to EFS (Sandbox, subject to step 7), and cannot reach a
non-allowlisted site under design A, nor any site at all under design B. Plus the written comparison of the
two egress designs, with the rebuild-loop figure marked provisional.

**Two negative deliverables, recorded as results rather than assumed:** nothing was provisioned into the
Data Governance account by any blueprint — check it, because it is the property that keeps the `Data` OU's
policy set honest; and the answer to INT-15, whichever way it went — what is attached to a
blueprint-provisioned project role, and whether a permissions boundary imposed from the prerequisite slice
survived.

**Deferred to Stage 7, deliberately:** the `git clone` from GitLab in the `engineering` project. GitLab does
not exist until Stage 7 step 1, so this stage cannot demonstrate it — an earlier version listed it here and
that was a dependency error, not an ambition. It moves to Stage 7's deliverables, where it belongs together
with the INT-09 network proof (the Development↔Production peering) and independently of the
CodeConnections attachment in INT-13 that D26 accepts losing.

**Note on the product direction (revised 2026-08-08, D26):** the first version of this stage built the
classic Studio generation (JupyterLab / Code Editor domains, one per Interactive account) and recorded
Unified Studio as deliberately not used — heavier baseline, less of the mechanics visible. D26 reverses
that: official Terraform support arrived in 2026-07 (the `aws-ia` module), and the governance layer this
plan assembles by hand in Stage 5 is exactly what SageMaker Catalog puts a portal on. What survives of
the old argument is the order of construction — the LF substrate is still built first, by hand, and the
portal is a storey on top of it, not the foundation. The corresponding `plan/institutional-delta.md` row is closed. One property
worth restating because it did not change: the portal, like the old Development Studio UI, is a **public
endpoint**, intended to be controlled by `aws:SourceIp` against the WireGuard Elastic IP (`plan/architecture.md` §3) — adopting
Unified Studio neither opens nor closes that path. **"Intended to be" is doing real work in that sentence
and it did not before:** the classic UI was reached by an IAM-authorized `CreatePresignedDomainUrl` call, so
a permission-set condition demonstrably applied; the portal is reached by an Identity Center sign-in, and
whether the same condition applies is INT-16, answered at Stage 4.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
