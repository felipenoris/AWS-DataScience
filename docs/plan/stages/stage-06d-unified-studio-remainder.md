# Stage 6d — Unified Studio: what 6a left owed

| | |
|---|---|
| **Status** | not started — **created 2026-09-05** by splitting the old Stage 6. It holds only what had not run, re-cut to the estate the split produces: **one** Interactive account (Sandbox), no NAT anywhere, and every internet call through the institutional proxy. Two items the old stage carried are gone rather than pending: the design A / design B **comparison** (6c settles it by construction — a spoke has no default route, so the compute's list lives on the proxy) and the derived-zone decision (dissolved 2026-08-26) |
| **Prerequisites** | [6c](stage-06c-networking-hub.md) pass 5 — what a Studio app can reach changes there, so every measurement below taken before it would have to be retaken. [6b](stage-06b-development-becomes-staging.md) only in that its instrument re-scoping removes the second Interactive account from the readings |
| **Consumes** | [D5](../decisions/D05-sagemaker-egress.md), [D11](../decisions/D11-lab-lifecycle.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D26](../decisions/D26-unified-studio.md), [D28](../decisions/D28-workflow-contract.md), **D38** (written at 6c) |
| **Proves** | [INT-01](../integrations.md) and [INT-17](../integrations.md) (the cross-account image pull and the selector — 6a built the repositories and pushed the image; nothing has consumed it), [INT-02](../integrations.md)'s consumer half under design B |

*Read with [`docs/SMUS.md`](../../SMUS.md) (the object model, the blueprint roster, the custom-image tag
convention) and [`docs/plan/conventions.md`](../conventions.md).*

---

**Objective:** finish the working environment. A data scientist opens a project in Sandbox, picks the
house image, installs a package through the proxy, submits a job that is refused outside the VPC, authors a
workflow that can be promoted, and leaves nothing running when the session ends.

**Who does what:** **Claude** writes every slice and reads every instrument; **the user** applies, signs in
to the portal, and runs the provoking half of each measurement. Tagged below only where it is not obvious.

---

## To execute

### 1. Prove the deny pair — the control 6a attached and never exercised

**Why:** 6a step 3 put `DenySageMakerJobsOffVpc` and its instance-type ceiling into all six persona sets
and measured nothing from a data-scientist session. A statement that is attached but never exercised is one
of several that could be doing the work (Lesson 20), and this one is D13's perimeter for compute.

- **Submitting the refused job — user**, from a data-scientist session in the Sandbox project: a processing
  job with **no** `VpcConfig`. Read the **wording** — it must name the policy — not the exit code.
- **Submitting the accepted job — user**, same session: the same job with the project's subnets and an
  allowed instance type. It runs.
- **Recording the contrast — Claude:** both wordings into the log; if the refusal names a different
  document than expected, the attribution is a contrast probe, not a re-reading (Lesson 24).

### 2. Make the house image selectable, and pull it across the account boundary

**Why:** `default-v0.1.0` sits in `awsds-prod-ecr-dev-env` since 2026-08-22 and nothing has ever selected
it. This is INT-01 and INT-17's only proof, and verification (vi) — *which call makes the image selectable,
does it survive a blueprint reconciliation, and does the cross-account pull work at all* — is still open.

- **Registering the image — Claude writes, user applies:** the SageMaker AI image and image-version
  resources in a new `sandbox/dev-env/` slice, `[P]` (registration is metadata), with the ECR URI and the
  `<flavour>-v<semver>` tag convention `docs/SMUS.md` owns. Add the `dev-env` rank in `layers.py` first.
- **Attaching it to the domain — Claude writes, user applies:** the app image configuration, with the
  proxy environment variables 6c's step 5 defines carried as `ContainerEnvironmentVariables` rather than
  baked into the Dockerfile.
- **Selecting it — user**, portal: create a JupyterLab space on the house image and record whether it
  appears in the list without any further act.
- **Reading reconciliation — Claude:** `./aws/studio.py` before and after a blueprint reconciliation; if
  the selector is a blueprint-authored object it may be reset, which is verification (vi)'s second half.
- **Pulling across accounts — Claude:** the CloudTrail record of the pull, showing the Sandbox project role
  reading `awsds-prod-ecr-dev-env` — INT-01 measured rather than assumed.

### 3. Run a working session under the proxy — the friction reading, retaken under the design that ships

**Why:** 4.3 ran on 2026-08-23 against design A with a NAT and a DNS firewall, and every conclusion it drew
about what has a path was superseded twice — first by the chain-evaluation finding, then by 6c removing the
NAT entirely. What breaks under an explicit proxy is a different list, and it is the one the environment
will actually have.

- **Installing packages — user**, from a JupyterLab terminal: `pip`, `uv`, `conda`, `Pkg` (Julia) and R.
  Each either works through the proxy or produces the name that must be added to the Sandbox ACL.
- **Checking the door each AWS call takes — Claude:** in the same session, `aws s3 ls` on the projects
  bucket must still show `vpcEndpointId` in CloudTrail — proof that `NO_PROXY` kept AWS traffic on the
  endpoints, and that the 4d defect shape has not returned.
- **Reading what the proxy saw — Claude:** `./aws/proxy.py --on-host` for the session's access log; a
  denied line is a name to decide on, not a failure to work around.
- **Measuring the SMUS components — Claude:** whether the DataZone agent, the S3 Access Grants plugin and
  Amazon Q honour `HTTP_PROXY` is **undocumented**. The reading is what settles it; anything that does not
  is either given an endpoint or written down as an accepted loss.
- **Deciding the one compute-side name with no private path — user, on Claude's reading:** Amazon Q
  Developer's second endpoint is `com.amazonaws.us-east-1.codewhisperer`, *available only in `us-east-1`*,
  and a `us-west-2` VPC cannot consume it. So the in-space Q features either cross the **proxy** (add the
  name to the Sandbox allow-list, which is an AWS-owned destination and a small widening) or they do not
  work. **Recommended: leave it out of the list** until somebody asks for the feature — an allow-list entry
  nobody uses is reach nobody needed. Record whichever way it goes; do not let it be discovered as a
  breakage.
- **Answering the two Stage 3 questions — Claude:** whether anything misses the AL2023 mirror path, and
  whether `lakeformation` leaves the core endpoint list (verification (ix)).

### 4. Measure the workflow surface — the premise the promotion chain now rests on

**Why:** with Development gone, **all** authoring happens in Sandbox and every workflow that reaches
Production is promoted from there. Nothing has ever confirmed that a Studio-authored workflow produces a
definition a pipeline can carry: no Workflows blueprint is enabled here, the synchronisation between
Unified Studio and MWAA Serverless is documented as a fact with no mechanism, and `start_date`
*must be in the future* at `CreateWorkflow`, so a YAML exported earlier fails at deploy. This measurement
was Stage 10's verification (i); it is pulled forward because Stage 10's design now depends on it.

- **Finding what enables the surface — Claude:** which act creates a project's workflow connection — a
  blueprint, or a connection on the project. `docs/SMUS.md`'s roster says the serverless Workflows surface
  is separate from the eleven configurations, and the answer decides whether 6a's blueprint list changes.
- **Authoring a two-task workflow — user**, in the Sandbox `experimentation` project.
- **Reading the definition — Claude:** `aws mwaa-serverless list-workflows` / `get-workflow` as
  `awsds-infra-sandbox-1`; fetch `DefinitionS3Location` and run the YAML through D28's promotion lint.
- **Reading the run's identity — Claude:** which role the Sandbox-side run used (it is not D28 item 3's
  per-workflow role), from CloudTrail.
- **Extending the lint — Claude, into Stage 8:** reject project-scoped references (connection names,
  notebook ids, `datazone_usr_role_*`), rewrite `start_date` at deploy time, enforce the operator
  allow-list, cap `execution_timeout` at 3600 s, and pin `DefinitionS3Location.VersionId`. Add artifact
  class **(2b) operator code package** to D28 — Python and Bash operators carry a code archive the six
  classes do not name.

### 5. Prove the lifecycle — the half of D11 that Studio has never had

**Why:** `scripts/down-studio-apps.py` has a body since 2026-08-21 and has never deleted a running app;
idle shutdown is configured and has never been observed to fire. Both are D11's promise for the most
expensive thing in the estate.

- **Observing idle shutdown — user:** leave a space idle past its threshold and read the app's
  disappearance (verification (x)'s second half).
- **Running the teardown — user:** `make down ENV=sandbox` deletes every running app and touches nothing
  else; `US-10` reads zero running apps (verification (xi)).
- **Stating the layers — Claude:** which Studio objects are `[P]` (the domain, the profiles, the
  configurations, the registered image), which are `[E]` (spaces, apps, jobs) and what `make down` may
  never touch, into `conventions.md` §5.1.
- **Adding the hub precondition — Claude:** `make up ENV=sandbox` refuses while 6c's hub hosts are stopped
  — the guard 6c builds, exercised here for the first time from a Studio session.

### 6. Close the open verifications and the log-group residue

**Why:** ten verification rows from the old stage are still open, and each names a claim nobody has
measured. Closing them is what makes the environment's description true rather than intended.

- **Answering iii, viii, xiv, xv, xvi, xvii, xix — Claude and user:** the two-AZ blueprint acceptance; a
  VPC-only space starting on the endpoint set under design B; whether the blueprint's manage-access role
  must be a Lake Formation administrator (open question 24's other half); whether a blueprint-created
  database arrives without `IAMAllowedPrincipals`; the shape of the grant the portal writes when it
  fulfils a subscription; whether `datazone:Get*` reaches `GetEnvironmentCredentials` (open question 20,
  with the vend attempt 2.5 never made); and which `aws:SourceVpce` an S3 call from a project subnet
  actually presents now that the account's gateway endpoint is the only candidate.
- **Finishing the log groups — Claude:** confirm the named group receives the apps' output and that a
  running-app metric exists to alarm on; `9.1` created the groups and never read one.
- **Restating the SMUS document — Claude:** `docs/SMUS.md` for one associated account, one project profile,
  the workflow surface as measured in step 4, and the CI/CD tool as what it is — an exporter on the
  Sandbox side, never a deployer into a Workload account (D28's amendment, written at Stage 8).

---

## Deliverables

- The house image registered, selectable and pulled across the account boundary.
- A working session's friction list under the proxy, and the `NO_PROXY` contract proven by a CloudTrail
  reading.
- A Studio-authored workflow whose definition passes the promotion lint, with its run identity recorded.
- Idle shutdown and `make down` both observed; the Studio layer table written.
- Ten verification rows answered, or explicitly re-homed with an owner.

## Validation

`./aws/studio.py` all-pass with one Interactive account; `US-10` zero running apps after `make down`;
`./aws/egress.py` showing no NAT and no default route while a session runs; the deny pair's two wordings in
the log.

## Cost

No standing cost of its own. A session costs the Sandbox `[E]` endpoint set (≈0.11-0.14/h under the
completed list) plus the space's instance; the workflow measurement costs MWAA Serverless task-hours at
USD 0.088/h with a one-minute minimum.

## Risks

- **The workflow surface is not enabled by anything we control**, which would move step 4's answer into a
  blueprint change and re-open 6a's decision 5. Recorded as the step's own alternative.
- **A component with no proxy support inside the image** (step 3's SMUS reading). The fallback is an
  endpoint, then the NAT contingency of D38 — in that order, and never a default route.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
