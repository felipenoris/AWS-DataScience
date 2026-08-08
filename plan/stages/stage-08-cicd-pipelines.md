# Stage 8 — CI/CD pipelines

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stage 7. |
| **Consumes** | [D5](../decisions/D05-sagemaker-egress.md), [D8](../decisions/D08-gitlab-hosting.md), [D14](../decisions/D14-supply-chain-account.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md) |
| **Proves** | [INT-07](../integrations.md), [INT-08](../integrations.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** the automation described in `CLAUDE.md`.

**Prerequisites:** Stage 7.

**To execute:**

1. **Development-environment pipeline — and the shared base image underneath it.** This pipeline builds
   *two* images, not one, and the split is what makes the whole promotion story true:
   - **`base`**: the language runtimes and their pinned versions — Python, Julia, R, the Rust toolchain —
     and nothing else. Tagged immutably.
   - **`dev-env`** = `base` + JupyterLab/Code Editor, notebook tooling, the interactive extras. Pushed to
     ECR and registered as a SageMaker custom image / app image config **in both Interactive domains**
     (D21) — same image, same version, both accounts, so Sandbox exploration and Development engineering
     run on the same runtime by construction. Triggered by tags.

   The reason for the split is D17: "promote only the code" is only true if the runtime the code lands on
   is identical to the one it was written against, and the only way to make that true *by construction* is
   a common ancestor image. Two independently built images with the same package list in them are two
   images that will diverge, quietly, at the first rebuild — and the divergence surfaces in production, as
   a version skew nobody changed.
   Under D5(B) this pipeline carries more weight still: it is where Julia, R and the Rust toolchain are
   installed, so it is the dependency delivery mechanism for every ecosystem CodeArtifact does not cover
   (`plan/architecture.md` §4.3). Its rebuild time is therefore a usability metric, not just a CI metric — measure it.
2. **Application build pipeline:** the `app-etl` template from `CLAUDE.md` — `uv` for dependencies,
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
   plausible at Stage 13); `plan/institutional-delta.md` records it.
   **Note the consequence of D14, now partly softened by D20:** the deploy runner and its *Production*
   target are still in the same account, so no cross-account boundary protects Production from a
   compromised runner. The Staging leg does cross one, which is worth something — a runner compromise now
   has to survive the integration tests and the approval to reach Production, rather than simply reaching
   it. Compensate for the rest with what is available inside one account: deploy roles scoped to the
   `app/*` slices only, `terraform plan` output attached to the approval, and CloudTrail alarms on any use
   of either deploy role outside a pipeline context. `plan/institutional-delta.md` records the build/deploy account split an
   institution would use instead.
5. **Security gates in every pipeline:** `checkov` on Terraform, ECR enhanced scanning results blocking a
   promotion on critical findings, and dependency scanning on the application. A gate that only warns is
   documentation, not a gate — decide explicitly which findings block.
6. A pipeline for this infrastructure repository as well: `fmt` / `validate` / `plan` on merge requests,
   `apply` gated by approval. This repository lives on GitHub (`GENERAL_PLAN.md` §1), so that pipeline is either GitHub
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
