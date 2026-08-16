# Stage 8 — CI/CD pipelines

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stage 7. |
| **Consumes** | [D5](../decisions/D05-sagemaker-egress.md), [D8](../decisions/D08-gitlab-hosting.md), [D14](../decisions/D14-supply-chain-account.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md) |
| **Proves** | [INT-07](../integrations.md), [INT-08](../integrations.md), [INT-17](../integrations.md), [INT-18](../integrations.md) |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** the automation described in `CLAUDE.md`.

**Prerequisites:** Stage 7.

**To execute:**

1. **Development-environment pipeline — a promotion chain with its own gate, in the same shape as the
   application chain in step 3.** This is not a build job that pushes an image; it is a release process for
   the runtime every notebook and every Unified Studio project app runs on, and it has its own approver
   (`dev-env-stewards`, `docs/ORGANIZATION.md`).

   **The repository.** `dev-env/` in GitLab, holding the `Dockerfile`s and their pinned package manifests,
   **writable by the data scientist**. That write access is deliberate and is the point of the design: which
   Julia version, which CRAN snapshot, which Rust toolchain is their expertise, and routing it through a
   ticket is what makes an environment stale — after which people install things by hand in a notebook and
   discover the version skew at promotion time. The control is not *who may propose* but *who may release*.

   **Two images, not one, and the split is what makes the whole promotion story true:**
   - **`base`**: the language runtimes and their pinned versions — Python, Julia, R, the Rust toolchain —
     and nothing else. Tagged immutably.
   - **`dev-env`** = `base` + JupyterLab/Code Editor, notebook tooling, the interactive extras.

   The reason for the split is D17: "promote only the code" is only true if the runtime the code lands on
   is identical to the one it was written against, and the only way to make that true *by construction* is
   a common ancestor image. Two independently built images with the same package list are two images that
   will diverge, quietly, at the first rebuild — and the divergence surfaces in production, as a version
   skew nobody changed. The application image is `FROM base:<pinned tag>` (step 2), never `FROM dev-env`.

   **The chain, on a tag:**
   1. build `base` and `dev-env`, immutable tags derived from the commit;
   2. **smoke-test the image** — it starts, every language runtime resolves, the pinned versions are the
      ones the manifest asked for, the key libraries import. This is the analogue of step 3's integration
      tests: cheap, and it catches the class of failure that otherwise reaches every workstation at once;
   3. **ECR scanning**, blocking on critical findings — basic scan-on-push per Stage 7 decision 2; the
      gate reads `DescribeImageScanFindings` either way, so a Stage 11 upgrade to enhanced changes nothing
      here;
   4. push to the Production ECR under the immutable tag — **visible to nobody yet**;
   5. **manual approval, assigned to the `dev-env-stewards` group**, with the image diff, the scan report
      and the smoke-test output attached. Same GitLab edition caveat as step 3.5 and Stage 7 step 3: a
      group-assigned approval is Premium, and the CE fallback is a `when: manual` job on a protected tag;
   6. **register the approved version** so it becomes selectable in the Sandbox and Development projects.

   **Step 6 is the one that is not yet known to be buildable, and it is `INT-17`.** Registration used to be
   ours end to end — `aws_sagemaker_image`, `image_version`, `app_image_config`, attached to a domain this
   repository wrote. Since D26 the domain is the per-project SageMaker AI domain that the **ML blueprint**
   provisions, which this repository does not author, so *what call makes an image appear in the selector,
   and whether it survives blueprint reconciliation*, is unverified. It is the same authorship question as
   INT-15, applied to image registration instead of to the execution role. **Answer it in Stage 6, before
   this pipeline is written**, and record the mechanism. If no automated path holds, the pipeline still
   delivers everything up to step 5 and the steward performs step 6 by hand — the approval, which is the
   control, is unaffected; what is lost is automation.

   **The version pointer is a promotion, not an overwrite.** Tags are immutable (Stage 7 step 5), so
   nothing is "moved". The approved artifact is a *new registered version* that the projects then resolve
   to — the same shape as the Model Registry, where a model version is approved rather than a file copied
   (D17). That parallel is worth keeping: it means "which runtime is everyone on" is a queryable fact with
   an approval attached, not the result of whoever pushed last.

   **Cross-account consequence to build deliberately:** the runner lives in Production (D14), and step 6
   writes into **Sandbox and Development**. That is a new trust direction — the supply chain reaching into
   the Interactive accounts, where every other flow in this plan runs the other way. It gets its own narrow
   deploy roles (`awsds-deploy-devenv-sandbox`, `awsds-deploy-devenv-dev`), scoped to the dev-env slice and
   nothing else, and it is `INT-18`.

   Under D5(B) this pipeline carries more weight still: it is where Julia, R and the Rust toolchain are
   installed, so it is the dependency delivery mechanism for every ecosystem CodeArtifact does not cover
   (`docs/plan/architecture.md` §4.3). Its rebuild time is therefore a usability metric, not just a CI metric —
   **and the gate now sits inside that loop**, which is a real cost to the D5 comparison and is recorded
   there: under design B, "I need package X" means a rebuild *and* an approval.
2. **Application build pipeline:** the `app-etl` template from [`docs/plan/conventions.md`](../conventions.md) — `uv` for dependencies,
   `pytest` for tests, linting, docs build published to Pages, Docker image pushed to ECR on tag.
   While the application is being engineered it is also applied by hand into
   `terraform-live/development/app/app-etl/`, against Development's own data. That slice is **not** a step
   of the promotion chain — the chain starts at the git tag this pipeline builds from, and its first
   target is Staging — but it is where the Terraform in the application repository gets exercised before
   a pipeline runs it unattended.
   The application image is `FROM base:<pinned tag>` — the same ancestor as `dev-env`, never a base of its
   own and never `FROM dev-env` (the application runtime has no business carrying Jupyter). A build that
   floats the base tag defeats the point of step 1.
3. **Promotion pipeline: Development → Staging → Production (D20, D21).** This replaces what earlier
   versions called the "production deploy pipeline", and the change is structural rather than cosmetic —
   there is a real environment between the tag and production, so the pipeline is a chain with a gate in
   the middle instead of a single deploy with an approval bolted on. The chain starts at a **tag on a
   Development repository** — Sandbox work enters it only by graduating into such a repository through
   git (D21); nothing promotes out of Sandbox directly:
   1. `make up ENV=staging` — apply the Staging `[E]` slices (NAT, endpoints), which exist only for the
      duration of this run;
   2. deploy: `terraform apply` for `terraform-live/staging/app/app-etl/`, pinned to the application tag,
      pulling the image from the Production ECR (INT-07);
   3. **run the integration tests against Staging data** — the step that justifies the whole account.
      These are not the unit tests from step 2; they are the ones that exercise the deployed artifact
      against a real catalog, real IAM and a real network;
   4. `make down ENV=staging` — tear it back down, so the metered cost is minutes;
   5. **manual approval**, assigned to the `deployment-managers` group, with the Staging test results and the
      Production `terraform plan` attached to it — **subject to the GitLab edition check in Stage 7 step 3:**
      group-assigned deployment approvals are Premium, and the CE fallback is a `when: manual` job on a
      protected tag, which constrains *who can push the tag* rather than *who approves this release*;
   6. promote the image and `terraform apply` for `terraform-live/production/app/app-etl/`.

   A failure at step 3 stops the chain and Production is never touched. That is the property the earlier
   `staging`-namespace-inside-Production stand-in could not provide, because a permission error there
   would have been evaluated against Production's own IAM and would have passed.
   **Two deploy roles, not one:** the runner lives in Production (D14), so it assumes
   `awsds-deploy-staging` for steps 1-4 and `awsds-deploy-prod` for step 6. Separate names on purpose —
   a CloudTrail audit has to be able to tell which one ran (INT-08).
4. **Credentials for the deploy roles:** no static keys — but **not GitLab OIDC federation either,
   correcting an earlier version**: to validate a job's ID token, IAM/STS fetches the issuer's discovery document
   and JWKS over the public internet, and a VPN-only GitLab (D8/D14) serves neither. The mechanism is a
   **dedicated deploy runner with an EC2 instance profile** — the runner's role *is* the deploy
   credential, no token exchange — locked to protected branches/tags and a protected environment, so an
   ordinary CI job never schedules onto it. OIDC remains the target design if a minimal public surface ever
   exists (exposing only `/.well-known/openid-configuration` and the JWKS path through a public ALB —
   plausible at Stage 13); `docs/plan/institutional-delta.md` records it.
   **Note the consequence of D14, now partly softened by D20:** the deploy runner and its *Production*
   target are still in the same account, so no cross-account boundary protects Production from a
   compromised runner. The Staging leg does cross one, which is worth something — a runner compromise now
   has to survive the integration tests and the approval to reach Production, rather than simply reaching
   it. Compensate for the rest with what is available inside one account: deploy roles scoped to the
   `app/*` slices only, `terraform plan` output attached to the approval, and CloudTrail alarms on any use
   of either deploy role outside a pipeline context. `docs/plan/institutional-delta.md` records the build/deploy account split an
   institution would use instead.
5. **Security gates in every pipeline:** `checkov` on Terraform, ECR scan findings (basic per Stage 7
   decision 2) blocking a promotion on critical findings, and dependency scanning on the application. A
   gate that only warns is documentation, not a gate — decide explicitly which findings block.
6. A pipeline for this infrastructure repository as well: `fmt` / `validate` / `plan` on merge requests,
   `apply` gated by approval. This infrastructure repository lives on GitHub — GitLab hosts the *application* repositories, not this one — so that pipeline is either GitHub
   Actions — with its own OIDC role into AWS; GitHub's issuer *is* public, so federation works there — or
   it runs on the GitLab mirror from Stage 7 step 7. Decide alongside the mirroring policy.

**Note on ordering:** this stage builds the promotion *machinery* — the chain, the gates, the two deploy
roles. The Staging and Production *data platforms* it deploys against are built in Stage 9, so the first
fully meaningful end-to-end promotion happens at the end of that stage, not this one. Until then, exercise
the chain with an application that touches no data; a pipeline proven only against real data is a pipeline
whose failures are ambiguous.

**Deliverables:** a version tag on `app-etl` flows automatically from source through Staging to a running
artifact in Production, with one human approval; **a deliberately broken version fails in Staging and never
reaches Production** — which is the whole point of D20 and the one test that proves the account earns its
Config recorder; and a build with a known-vulnerable dependency is stopped by the gate.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
