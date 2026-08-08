# Stage 7 — GitLab, Runners and ECR

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stages 3 (which now builds the Production VPC), 4; decisions D8, D14, D15. |
| **Consumes** | [D8](../decisions/D08-gitlab-hosting.md), [D12](../decisions/D12-budget-ceiling.md), [D14](../decisions/D14-supply-chain-account.md), [D15](../decisions/D15-tls-internal.md), [D20](../decisions/D20-staging-account.md), [D26](../decisions/D26-unified-studio.md) |
| **Proves** | [INT-08](../integrations.md), [INT-09](../integrations.md), [INT-13](../integrations.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

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
   daily dependency `plan/conventions.md` §5.1 rule 2 warns about. So the instance and its EBS volume are **stopped**, not
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
   **A second edition caveat, in the same family and with larger consequences: the Stage 8 approval gate
   itself is probably not expressible in CE as designed.** Stage 8 step 3.5 wants a manual approval
   *assigned to the `deployment-managers` group*; **protected environments** and **deployment approval
   rules** — the features that express "this job may only be run by members of group X" — are Premium.
   What CE does give is a `when: manual` job on a **protected branch or protected tag**, where the set of
   people who may run it is the set allowed to deploy to that ref. Verify which of the two this instance
   supports **before Stage 8 is written**, not during it, because the answer changes what "the approval
   gate" means:
   - if Premium is available, the gate is what D20 describes;
   - if not, the fallback is protected-tag permissions plus a GitLab group whose membership is maintained by
     hand — the same compromise already accepted for SAML group sync one paragraph up, applied to the
     control D20 leans on rather than to a convenience. It is weaker in a specific way worth writing down:
     the constraint is *who can push the protected tag*, not *who approves this particular release*, and
     CloudTrail on the two deploy roles (INT-08) becomes the record of what actually happened rather
     than a supplement to it.

   `plan/institutional-delta.md` gains a row either way: an institution buys the tier and gets the approval as a first-class object.
   **Note that the edition question now decides *two* gates, not one.** Since the `dev-env` image got its
   own promotion chain and its own approver (Stage 8 step 1, `dev-env-stewards`), the same Premium feature
   governs whether "only a dev env steward may release a runtime image" is expressible, or whether it
   degrades to "only certain people may push the protected tag". Check it once, for both.
   **GitLab groups to create here, mirroring the Identity Center groups 1:1:** `data-scientists`,
   `deployment-managers`, `governance-managers` and `dev-env-stewards`. And the repositories: the
   application repositories, plus **`dev-env/`** — the image build code, **writable by
   `data-scientists`** and with its release tag protected so only `dev-env-stewards` can push it.
4. GitLab Pages enabled for documentation, reachable only through the VPN. Pages requires a **domain
   distinct from the GitLab host** (it serves user-supplied content, so sharing the origin would hand it
   the GitLab session cookie) and a **wildcard DNS record plus wildcard certificate** — both provided by
   D15, which is why that decision has to be made before this stage.
5. **Registries, in `production/data/`, layer `[P]` — applied early (before Stage 6):**
   ECR repositories `dev-env` (SageMaker images) and `app/*` (application images), with lifecycle policies
   to expire untagged images and **ECR enhanced scanning** enabled; an **ECR pull-through cache** rule for
   the upstream public registries; and a **CodeArtifact** domain with repositories per ecosystem, each
   configured with an upstream to the public registry. Both carry a resource policy granting the **Sandbox
   and Development** accounts pull/read access, and the KMS key policy has to grant both as well — the
   direction of sharing is the reverse of the previous plan, because the registries moved. `plan/architecture.md` §4.3 records
   which ecosystems CodeArtifact does not cover and what happens to them instead. Whether SageMaker Studio
   actually accepts the `dev-env` image cross-account is verified in Stage 6; the fallback is an ECR
   replication rule into a repository in each Interactive account.
6. GitLab Runners in `production/runners/`, layer `[E]`: autoscaling on EC2 or Fargate, in the private
   subnet, with an instance role that can push to ECR. Container builds with Kaniko or BuildKit (no
   privileged Docker-in-Docker). Runners hold no state worth keeping, so they are rebuilt every session.
   The runners need egress to fetch public dependencies while building the dev-env image — that is the one
   place internet access is legitimate under both egress designs, and it belongs to the build account, not
   to the notebook.
7. Decide and document the mirroring policy between this GitHub repository and GitLab.
8. Add GitLab start/stop to `make up` / `make down`, and measure the boot time — if it turns out to be
   much worse than the ~3-5 minutes assumed in D8, revisit the layer choice (`plan/conventions.md` §5.1 rule 7).

**Deliverables:** a repository pushed to GitLab over the VPN, a pipeline running on a private runner, an
image in ECR pulled successfully **from both Interactive accounts**, and a docs site served by Pages over
HTTPS with a valid certificate. **Plus the one deferred from Stage 6:** a `git clone` from GitLab inside the
`engineering` project, which proves the Development↔Production peering carries it (INT-09) — the
*network* path, independent of the CodeConnections attachment in INT-13 that D26 accepts losing. INT-13
itself is also answered here, since this is when GitLab first exists: check whether a CodeConnections host
can be created at all from an account with no VPC, and record the manual `git remote add` as the accepted
path when it cannot.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
