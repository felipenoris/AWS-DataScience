# Stage 6 — SageMaker Unified Studio

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stages 3, 4, 5, and the ECR/CodeArtifact repositories from Stage 7 step 5 — **pulled forward**, because under egress design B they are how packages arrive, so they cannot come after the thing that consumes them. **D5 is executed, not decided, in this stage**: both designs get built (`plan/architecture.md` §4.3). |
| **Consumes** | [D5](../decisions/D05-sagemaker-egress.md), [D12](../decisions/D12-budget-ceiling.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D14](../decisions/D14-supply-chain-account.md), [D21](../decisions/D21-development-account.md), [D24](../decisions/D24-shared-filesystem.md), [D26](../decisions/D26-unified-studio.md), [D28](../decisions/D28-workflow-contract.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | [INT-01](../integrations.md), [INT-09](../integrations.md), [INT-12](../integrations.md), [INT-13](../integrations.md), [INT-15](../integrations.md), [INT-16](../integrations.md), [INT-17](../integrations.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** the data scientist's working environment — since the 2026-08-08 revision (D26), one
SageMaker unified domain (DataZone V2) with projects, rather than two classic Studio domains.

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
  hand-built image in `log/stage-06-unified-studio.md`, so the changeover is visible.
- **The `plan/architecture.md` §4.3 verdict on egress design B is provisional until Stage 8.** Design B's whole claim is that
  the image *is* the dependency delivery mechanism, and the usability of that claim depends on how long a
  rebuild takes — which is a property of the pipeline, not of a laptop build. So Stage 6 step 6 measures
  everything else and marks the rebuild-loop number as "measured on a laptop, re-measure at Stage 8". The
  choice that closes D5 can be made here; the number behind it is confirmed there.

**To execute:**

1. **The unified domain (D26), from the official module** — `aws-ia/terraform-aws-sagemaker-unified-studio`
   (`aws` ≥ 6.51 for the domain and its IAM roles, `awscc` ≥ 1.89 for project profiles, blueprints and
   projects): a single **DataZone V2 domain** in the **Data Governance** account
   (`data-governance/governance/`), authenticating through
   Identity Center. **Check before creating anything:** the domain must live in IdC's home Region
   (`us-west-2` if Stage 1 went as planned) — neither can move afterwards. Account associations through
   the org-wide RAM sharing Stage 1b step 11 enabled (INT-12): **Sandbox** and **Development**;
   **Staging and Production are never associated** (D28). **And under D35 the associated set is not two
   accounts but N + 1** — one Sandbox per business unit plus the single Development — each needing its own
   blueprint configuration against the same single domain. That is the intended mechanism, so it scales; what
   it makes heavier is the root deny on `datazone:CreateDomain` (1b step 7), because with many sandboxes the
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
   interactively" is a time-boxed elevated role approved by `deployment-managers`, logged and alarmed — designed in
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
