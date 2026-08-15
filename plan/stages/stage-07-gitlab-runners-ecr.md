# Stage 7 — GitLab, Runners and ECR

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stages 3 (which now builds the Production VPC), 4; decisions D8, D14, D15. |
| **Consumes** | [D8](../decisions/D08-gitlab-hosting.md), [D12](../decisions/D12-budget-ceiling.md), [D14](../decisions/D14-supply-chain-account.md), [D15](../decisions/D15-tls-internal.md), [D20](../decisions/D20-staging-account.md), [D26](../decisions/D26-unified-studio.md), [D36](../decisions/D36-internal-pki.md) |
| **Proves** | [INT-08](../integrations.md), [INT-09](../integrations.md), [INT-13](../integrations.md), [INT-19](../integrations.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** source control, docs hosting and a container registry, all private, **all in the Production
account** (D14).

**Prerequisites:** Stages 3 (which now builds the Production VPC), 4; decisions D8, D14, D15.

**Note on ordering — two slices are pulled forward and applied before Stage 6, for the same class of
reason:** step 5 (ECR and CodeArtifact), because under egress design B it is how packages reach SageMaker;
and **`production/pki/` from step 2 (D36)**, because the `dev-env` image exists from Stage 6 (INT-01) and
has to be *built* with the CA root already in it — a CA created at its natural place here would mean the
first image is built without it and rebuilt afterwards. The rest of this stage stays here.

**Note on option preservation — build this so a Shared Services account stays cheap to add (D14).**
D14 keeps the supply chain in Production for two reasons that are both about running cost, not about
security: a second VPC floor (~50-65 USD/month) and the account quota. Its revision trigger can fire, so
this stage is written to make the move a **re-target**, not a rewrite. **Be clear about what the folders do
and do not buy**: separate slices reduce *migration* cost and nothing else — they are not a boundary, they
share one account, one IAM space, one SCP ceiling and one blast radius (Lesson 5). What actually makes such
a move expensive is not the folder but **implicit same-account coupling**, so the four measures below are
about coupling:

1. **The registries get their own slice, `production/registry/` `[P]`** — ECR, the pull-through cache and
   CodeArtifact, *out of* `production/data/`, which keeps the application-output buckets and the Lake
   Formation resource links. Those two sets move in opposite directions the day the trigger fires: the
   registries leave, the buckets and links stay. `plan/conventions.md` §6 carries this layout.
2. **Cross-account by construction, even inside one account.** The pipeline reaches its targets by
   `AssumeRole` with the account id coming from a variable, **including into Production** — never by
   same-account implicitness. Likewise the ECR and CodeArtifact resource policies and their KMS key
   policies enumerate consumers from a **map of account ids** (Lesson 14 — a principal pasted in by hand in
   N places will be missing from one). If the registries move, the map gains a key; nothing else changes.
3. **No implicit sharing with Production's own resources.** `tooling/`, `runners/` and `registry/` read
   `production/foundation/` only through `terraform_remote_state` outputs that would still exist if
   foundation lived in another account — VPC id, subnet ids, CIDRs — and they get **their own KMS key**,
   not the key `production/data/` uses for application data. A shared key is the single hardest thing to
   unpick later, because it is referenced from every consumer account's policy.
4. **Reserve the CIDR now, in Stage 3's allocation table.** It costs nothing and avoids renumbering a
   peered topology later.

What stays genuinely sticky, and is worth knowing rather than avoiding: **GitLab's state** — repositories,
CI history, registry metadata on EBS/S3 — plus the private DNS name, the certificate and the runner
registration. Moving those is a restore-and-repoint with a maintenance window, not a redesign, which is
exactly why step 1's backup/restore cycle has to be tested for real.

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
2. **TLS per D15, as revised on 2026-08-09 — an internal CA, and no registered domain at this stage.**
   ACM cannot issue for `prod.internal` (public certificates need public validation) and Private CA is over
   budget, but the audience here is three clients we build ourselves, so the trust chain is ours:
   - Generate the **internal root CA** once, in **`production/pki/` `[P]` — its own slice, its own state
     file and its own KMS key (D36), applied early per the ordering note above.** Not in `foundation/`:
     that slice is opened to change a CIDR or accept a peering, and every such edit would otherwise be made
     by a principal holding the root. Record the CA certificate's fingerprint in
     `log/log-stage-07-gitlab-runners-ecr.md` when it is
     created — without it, a substituted root is indistinguishable from the real one by inspection.
   - Issue the leaves from it: `gitlab.prod.internal` and the **wildcard** Pages needs. The consuming slice
     reads them through `terraform_remote_state`; **the root private key is never an output** (D36).
     **Import them into ACM** and attach to the internal ALB. Imported certificates are free, but **ACM does
     not renew them** — issue at or below 398 days and schedule the re-import (D15 phase 1 note 5).
   - **Distribute the root to all three client surfaces (INT-19): the laptop, the `dev-env` image, and the
     runners.** A surface that is missed fails with an opaque TLS error at the moment somebody is trying to
     `git clone`, not with an access denial that names itself. Do this before step 3, because the SAML
     round-trip in step 3 is a browser flow through `gitlab.prod.internal` and an untrusted certificate
     turns it into an unexplained loop.
   **Nothing is published, no domain is registered, and the internal names never enter a Certificate
   Transparency log** — which a public ACM certificate would have made unavoidable. The public domain, the
   public zone and public certificates arrive at Stage 13, for the tier that is actually public.

   **Worth evaluating here rather than assuming: with the certificate no longer coming from ACM, the ALB
   loses its main job.** It was in the design to terminate a public ACM certificate; GitLab Omnibus's own
   nginx can serve the internal CA's certificate — including the Pages wildcard — directly on the instance,
   with the `prod.internal` record pointing at it. That removes an `[E]` resource, its ~USD 0.023/h and its
   rebuild path from `make up`. Measure both and record the choice; the CA is the same either way.
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
   **GitLab groups to create here, one per persona, mirroring the Identity Center groups 1:1 in
   *membership* and deliberately not in *name*:** `data-scientists`, `deployment-managers`,
   `governance-managers` and `dev-env-stewards` — **without** the `sso-group-` prefix the directory
   objects carry (`plan/conventions.md`, the identity seam's first rule). The prefix marks an Identity
   Center group, and these are GitLab objects in a different system, granting nothing in AWS; a bare name
   in this repository means the GitLab group and a prefixed one means the directory. **The 1:1 that
   matters is the person behind each**, which is what makes the Stage 8 gate consistent with the AWS
   access model and what a future upgrade to SAML group sync would automate — and it is also the pairing
   that has to be re-checked by hand until then, since nothing enforces that
   `sso-group-deployment-managers` and GitLab's `deployment-managers` hold the same people. And the repositories: the
   application repositories, plus **`dev-env/`** — the image build code, **writable by
   `data-scientists`** and with its release tag protected so only `dev-env-stewards` can push it.
4. GitLab Pages enabled for documentation, reachable only through the VPN. Pages requires a **domain
   distinct from the GitLab host** — it serves user-supplied content, so sharing the origin would hand it
   the GitLab session cookie — plus a **wildcard DNS record and a wildcard certificate**. Under the revised
   D15 all three are internal and cost nothing: a **second private hosted zone**, `pages.internal`, separate
   from `prod.internal` so the cookie boundary is a real domain boundary and not just a different host;
   a wildcard record `*.pages.internal` in it; and a `*.pages.internal` leaf from the internal CA.
   **The zone itself and its two cross-account associations are already built — Stage 3 step 4** creates
   `pages.internal` beside `prod.internal` and associates both with the Sandbox and Development VPCs, since
   Pages is read from the laptop and from Studio. What this step adds is the wildcard record and the leaf.
5. **Registries, in `production/registry/`, layer `[P]` — applied early (before Stage 6):**
   ECR repositories `dev-env` (SageMaker images) and `app/*` (application images), with lifecycle policies
   to expire untagged images and **ECR enhanced scanning** enabled; an **ECR pull-through cache** rule for
   the upstream public registries; and a **CodeArtifact** domain with repositories per ecosystem, each
   configured with an upstream to the public registry. Both carry a resource policy granting the **Sandbox
   and Development** accounts pull/read access, and the KMS key policy has to grant both as well — the
   direction of sharing is the reverse of the previous plan, because the registries moved. **Both policies
   enumerate their consumers from a map of account ids, and the key is this slice's own key, not
   `production/data/`'s** (option-preservation note above, measures 2 and 3). `plan/architecture.md` §4.3 records
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
HTTPS with a certificate that validates **against the internal CA, on all three client surfaces** — laptop
browser, `dev-env` notebook and runner (INT-19). "It works in my browser" only tests the one surface where
somebody clicked through a warning. **Plus the one deferred from Stage 6:** a `git clone` from GitLab inside the
`engineering` project, which proves the Development↔Production peering carries it (INT-09) — the
*network* path, independent of the CodeConnections attachment in INT-13 that D26 accepts losing. INT-13
itself is also answered here, since this is when GitLab first exists: check whether a CodeConnections host
can be created at all from an account with no VPC, and record the manual `git remote add` as the accepted
path when it cannot.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
