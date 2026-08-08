# Cross-account integrations to prove (INT-01 … INT-16)

**Each row has a stable ID.** Reference an integration as `INT-11`, never as "row 11" —
inserting a row must not renumber a reference. Stage files list the IDs they prove.

---

### 4.4 Cross-account integrations to prove

The account split (see `README.md`, "Account segregation") is the right call, and it is not free: it turns
several things that are one API call inside a single account into a resource policy, a KMS grant and a RAM
share spanning two. Earlier versions of this plan carried these as "verify this rather than assume" notes
scattered across five stages. Scattered, each one is an evening lost in isolation and re-derived from
nothing. Consolidated, they are a checklist with a stated fallback per row — which is the shape that
survives contact with a Tuesday night.

| ID | Integration | Stage | Fallback if it does not work |
|---|---|---|---|
| **INT-01** | Studio custom image pulled from the **Production** ECR (D14) into the Sandbox **and Development** domains | 6 | An ECR cross-account replication rule into a repository in each Interactive account. Not a pipeline |
| **INT-02** | CodeArtifact consumed cross-account from Sandbox and Development — domain policy *and* KMS key policy | 6, 7 | Bake the packages into the dev-env image (`plan/architecture.md` §4.3), which is the delivery mechanism anyway |
| **INT-03** | Lake Formation cross-account shares through AWS RAM, now **three** (D22): Data Governance → Sandbox (read), → Development (read), → Production (read + governed write, the producer path) — resource links and `IAMAllowedPrincipals` have version-dependent behaviour, and the *write* grant is the least-travelled variant | 5, 9 | None; instead, prove each grant restricts with the "read it with pandas" test *before* believing it, and prove the write path with a job that writes a curated table cross-account |
| **INT-04** | Model Registry: reading or approving a Production model package group from Development (D17) | 9, 10 | Registration happens only under the pipeline's own Production role; the Development side never writes to the registry |
| **INT-05** | S3 bucket policies (now mostly in **Data Governance**, D22) whose `aws:SourceVpce` condition must admit the endpoints of *every* consuming account — Sandbox, Development, Production — plus the WireGuard Elastic IP (D18). **The IDs must come from the `[P]` S3 gateway endpoints in each consumer's `foundation/`, never from the `[E]` interface endpoints in `egress/`**, whose IDs change on every `make up` — and which now sit in a different account from the policy | 5, 9 | Replace the condition with `aws:SourceVpce ∈ list` **or** `aws:SourceIp = <WireGuard EIP>`, maintained as a variable per consuming account rather than edited by hand; or anchor on `aws:SourceVpc` (the VPC ID, also `[P]`) |
| **INT-06** | Whether S3 **console** browsing survives the `aws:SourceVpce` deny at all — console operations issued by the console backend carry neither the endpoint nor the user's source IP | 9 | Tell users to use the CLI over the tunnel, and write that in `README.md` rather than leaving a broken console as a surprise |
| **INT-07** | **Staging** (D20) consuming Production: pulling the application image from the Production ECR and reading the approved model version from the Production Model Registry, both under the pipeline's Staging role | 8, 9 | Replicate the image into a Staging ECR repository as part of the promotion, and pass the model artifact's S3 URI explicitly instead of resolving it through the registry |
| **INT-08** | The deploy roles assuming **across** accounts — the runner is in Production (D14), so the trust policies run Production → Staging and Production → Production | 8 | None needed; but write the two trust policies as separate roles with separate names, so an audit can tell which one was used |
| **INT-09** | **Development ↔ Production VPC peering** (D21): Studio in Development must reach GitLab in Production to clone and push — the same narrow, per-subnet route shape as the Sandbox peering | 3, 7 | None at the network level; if the second peering proves troublesome, the mirror-to-GitHub policy from Stage 7 step 7 is the interim path for Development commits |
| **INT-10** | **The ingestion drop-box pickup** (D25): the Production job role reading and deleting from a Data Governance prefix that the Interactive-OU roles write to — a bucket policy with two asymmetric statements, plus a grant on the drop-box KMS key | 5, 9 | Have the Interactive-OU roles write to a bucket in Production instead, and accept that the file lands outside the governed account before it is curated. Strictly worse — it puts an ungoverned copy in the deployment target — so treat it as a stopgap, not an alternative |
| **INT-11** | **Organization-wide sharing enablement for Lake Formation** (D22): `ram:EnableSharingWithAwsOrganization`, LF **cross-account version 3 or above** (required to grant to an Organization or an OU rather than to an account list), and `AWSLakeFormationCrossAccountManager` on the Data Governance grantor | 1, 5 | Grant to explicit **account IDs** rather than to the OU, and accept a RAM invitation per share. Three shares accepted by hand, once, is survivable — but the invitations reappear whenever a share is recreated, so it is a tax on every rebuild |
| **INT-12** | **The unified domain's account associations** (D26): the DataZone V2 domain in **Data Governance** associated with **Sandbox and Development** through RAM, and blueprints provisioning project environments into those accounts under their provisioning roles. This is the row that carries the whole D26 shape — if associations do not work, the domain is a catalog with no compute attached | 6 | One V2 domain **per Interactive account**, no associations — losing the single portal and the cross-account project model, but keeping projects, the catalog and the Terraform module. The domain would then sit on the lifecycle axis after all, which D26 rejects on principle, so treat this as a degraded mode rather than a design |
| **INT-13** | **Unified Studio project git ↔ the self-hosted GitLab** (D14, D26): projects attach a repository through CodeConnections, which for self-managed GitLab requires a **CodeConnections host** reaching the instance in Production's private subnet. **Since D26 the domain is in Data Governance, which has no VPC** — so the host has nowhere to attach, and this row is expected to fail rather than merely at risk | 6, 7 | Accepted as the normal path, not as a fallback: the project keeps its default repository and the push into GitLab is a manual `git remote add` + push. The D21 graduation is a rewrite through a repository either way, so what is lost is convenience, not a control. Giving Data Governance a VPC and a peering to buy it back was considered and declined (D26) |
| **INT-14** | **The pipeline creating `awscc_mwaaserverless_workflow` in Production** (D28): the Cloud Control path from the deploy role — verified to exist 2026-08-08, not yet verified to *apply* cleanly under a CI role with a permission boundary | 10 | `aws_cloudformation_stack` wrapping `AWS::MWAAServerless::Workflow`; second fallback, provisioned MWAA (`aws_mwaa_environment`, `[E]`, metadata-database caveat in force — D7) |
| **INT-15** | **Whether D13 survives D26: who authors the project execution roles.** D13 requires that the roles running notebooks hold *no* S3 access to Lake Formation-registered prefixes. Until D26 those roles were written here, in Terraform; now the ML and Lakehouse blueprints provision the project environment **and its roles**. Verify what is actually attached to a provisioned project role, and whether a customer-managed policy or a permissions boundary can be imposed on it without the blueprint reconciling it away | 6 | In order: (i) attach a **permissions boundary** to the project role through the `sandbox/sagemaker/` and `development/sagemaker/` prerequisite slices, which is the mechanism least likely to be overwritten; (ii) if the blueprint's own grants cannot be narrowed, fall back to Lake Formation **hybrid access mode** for the affected prefixes and record it as a D13 exception rather than a silent widening; (iii) worst case, keep the lake's registered prefixes out of every blueprint-provisioned role's reach by putting them behind a *separate* LF share that is granted per project rather than per account |
| **INT-16** | **Whether an `aws:SourceIp` deny on a permission set actually gates the Unified Studio portal** (D26, Stage 4 step 8). The portal is opened by signing in to Identity Center and following the domain URL, not by an IAM-authorized API call under a permission set — so the control `plan/architecture.md` §3 claims for the "API and portal" path may cover the API half and not the portal half, which is the data scientist's primary working surface | 4, 6 | In order: (i) an IdC-level or DataZone-level network restriction, if one exists; (ii) accept that the portal is reachable from anywhere with a valid IdC session and rely on the fact that *the project compute it fronts* is VPC-only and its data access is LF-gated — stating plainly in `README.md` that "all access through the VPN" holds for the AWS control plane and not for the portal; (iii) the honest fallback of last resort, which is to say so in the threat model rather than to leave a control listed that nobody implemented (the same discipline Stage 11 step 3 applies to Studio file download) |

INT-05, 6 and 11 are the ones most likely to surface as an `AccessDenied` — or, in INT-11's case, as a
share that appears to have been granted and simply never arrives. INT-07-10 are the price of real
environment separation: the promotion crosses an account boundary twice, the lake is consumed
cross-account from everywhere (D22), and each crossing is a place where a resource policy can be missing.
INT-12-16 arrived with D26-D28 and are the Unified Studio set — INT-13 is the one with no workaround
that preserves convenience, and INT-14 is the one that decides whether D7's alternative A ships in
Terraform or in a wrapper. Check them deliberately rather than by symptom.

**INT-15 and 16 are different in kind from the other fourteen and should be read first.** Every other row
is an integration that either works or has a fallback that costs convenience. These two are rows where a
*stated control* may not exist:

- **INT-15 is the one that can invalidate a stated objective of `CLAUDE.md`.** "Fine-grained access
  control" is real only because of D13, and D13 is real only if the execution role's S3 permissions can be
  constrained. D26 moved the authorship of those roles from this repository to a blueprint, and nobody has
  checked what that changed. If INT-15 fails and no fallback holds, the correct response is not to widen
  D13 quietly but to record that column and row filtering is an entitlement mechanism whose enforcement is
  incomplete — which is the same honesty Stage 11 step 3 demands about file download.
- **INT-16 is the one that can invalidate a stated objective of the same file** — "all user access to the
  cloud infrastructure will be performed through a VPN". It is cheap to answer (open the portal with the
  tunnel down) and it is answered at Stage 4, the first moment it can be.

Both follow the pattern of Lesson 7 in `CLAUDE.md`: a decision taken for good reasons moved something, and
the conditions that referenced it were not re-checked. Here the thing that moved was *who writes the IAM
policy* and *what a session is authenticated by*.

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [plan/stages/INDEX.md](stages/INDEX.md)*
