# Stage 6d — Unified Studio: what 6a left owed

| | |
|---|---|
| **Status** | not started — **created 2026-09-05** by splitting the old Stage 6, revised the same day into the action-checklist format. It holds only what had not run, re-cut to the estate the split produces: **one** Interactive account (Sandbox), no NAT anywhere, every internet call through the institutional proxy. Two items the old stage carried are gone rather than pending — the design A / design B **comparison** (6c settles it by construction) and the derived-zone decision (dissolved 2026-08-26) |
| **Prerequisites** | **[6c](stage-06c-networking-hub.md) pass 5** — what a Studio app can reach changes there, so any measurement below taken earlier would have to be retaken. [6b](stage-06b-development-becomes-staging.md) only in that its instrument re-scoping removes the second Interactive account from the readings |
| **Consumes** | [D5](../decisions/D05-sagemaker-egress.md), [D11](../decisions/D11-lab-lifecycle.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D26](../decisions/D26-unified-studio.md), [D28](../decisions/D28-workflow-contract.md), [D38](../decisions/D38-single-egress-hub.md) |
| **Proves** | [INT-01](../integrations.md) and [INT-17](../integrations.md) (the cross-account image pull and the selector — 6a built the repositories and pushed the image; nothing has consumed it), [INT-02](../integrations.md)'s consumer half under design B |

*Read with [`docs/SMUS.md`](../../SMUS.md) (the object model, the blueprint roster, the custom-image tag
convention) and [`docs/plan/conventions.md`](../conventions.md).*

---

**Objective:** finish the working environment. A data scientist opens a project in Sandbox, picks the house
image, installs a package through the proxy, submits a job that is refused outside the VPC, authors a
workflow that can be promoted, and leaves nothing running when the session ends.

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls — done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write — run **only after the user authorizes that specific action in chat** |
| **[user]** | the portal, the JupyterLab terminal, and the provoking half of every measurement — the parts no AWS API performs |
| **[Claude reads, user decides]** / **[Claude and user]** | a measurement Claude takes and a choice only the user can make, in the same sitting — the reading is written down whichever way the choice goes |

## Step numbers are identifiers, not an order

Steps 1, 2 and 5 are independent. **Step 3 depends on step 2** (the friction reading is taken in the house
image, not the stock one) and **step 4 depends on step 3** only for the session. Step 6 is the close.

---

## To execute

### 1. Prove the deny pair — the control 6a attached and never exercised

**Action:** submit one job that must be refused and one that must run, from a data-scientist session.
**Why:** 6a step 3 put `DenySageMakerJobsOffVpc` and its instance-type ceiling into all six persona sets and
measured nothing. **Explanation:** a statement that is attached but never exercised is one of several that
could be doing the work (Lesson 20), and this one is D13's perimeter for compute — so the pair is read as a
contrast, and the **wording** is the evidence, not the exit code.

- **1.1 — [user] Submit the refused job**: a processing job with **no** `VpcConfig`, from a data-scientist
  session in the Sandbox project. Read the refusal wording — it must name the policy.
- **1.2 — [user] Submit the accepted job**: the same job with the project's subnets and an allowed instance
  type. It runs.
- **1.3 — [Claude] Record the contrast**: both wordings into the log. If the refusal names a different
  document than expected, the attribution is a contrast probe, not a re-reading (Lesson 24).

### 2. Make the house image selectable, and pull it across the account boundary

**Action:** register `default-v0.1.0` as a SageMaker AI image, attach it to the domain and select it from
the portal. **Why:** the image has sat in `awsds-prod-ecr-dev-env` since 2026-08-22 and nothing has ever
selected it. **Explanation:** this is INT-01 and INT-17's only proof, and verification (vi) — *which call
makes the image selectable, does it survive a blueprint reconciliation, and does the cross-account pull
work at all* — is still open.

- **2.1 — [Claude⚡] Register the image**: the SageMaker AI image and image-version resources in a new
  `sandbox/dev-env/` slice, `[P]` (registration is metadata), with the ECR URI and the `<flavour>-v<semver>`
  tag convention `docs/SMUS.md` owns. Add the `dev-env` rank in `layers.py` first.
- **2.2 — [Claude⚡] Attach it to the domain**: the app image configuration, carrying 6c step 5.6's proxy
  variables as `ContainerEnvironmentVariables` rather than baked into the Dockerfile.
- **2.3 — [user] Select it**: create a JupyterLab space on the house image from the portal, and record
  whether it appears in the list without any further act.
- **2.4 — [Claude] Read reconciliation**: `./aws/studio.py` before and after a blueprint reconciliation. If
  the selector is a blueprint-authored object it may be reset — verification (vi)'s second half.
- **2.5 — [Claude] Read the cross-account pull**: the CloudTrail record showing the Sandbox project role
  reading `awsds-prod-ecr-dev-env` — INT-01 measured rather than assumed.

### 3. Run a working session under the proxy — the friction reading, retaken under the design that ships

**Action:** install packages in five ecosystems, then read which door each call took. **Why:** 4.3 ran on
2026-08-23 against design A with a NAT and a DNS firewall, and every conclusion it drew about what has a
path was superseded twice. **Explanation:** what breaks under an explicit proxy is a different list, and it
is the one the environment will actually have — a denied name is a decision to take, not a failure to work
around.

- **3.1 — [user] Install packages** from a JupyterLab terminal: `pip`, `uv`, `conda`, `Pkg` (Julia) and R.
  Each either works through the proxy or produces the name that must be added to the Sandbox ACL.
- **3.2 — [Claude] Check the door each AWS call takes**: in the same session, `aws s3 ls` on the projects
  bucket must still show `vpcEndpointId` in CloudTrail — the proof that `NO_PROXY` kept AWS traffic on the
  endpoints and that the 4d defect shape has not returned.
- **3.3 — [Claude] Read what the proxy saw**: `./aws/proxy.py --on-host` for the session's access log.
- **3.4 — [Claude] Measure the SMUS components**: whether the DataZone agent, the S3 Access Grants plugin
  and Amazon Q honour `HTTP_PROXY` is **undocumented**. The reading settles it; anything that does not is
  either given an endpoint or written down as an accepted loss.
- **3.5 — [Claude reads, user decides] Take the one compute-side name with no private path**: Amazon Q
  Developer's second endpoint is `com.amazonaws.us-east-1.codewhisperer`, and the network-isolation guide
  marks it *available only in `us-east-1`* — a `us-west-2` VPC cannot consume it, even though the same table
  lists it as **required**. So in-space Q features either cross the **proxy** (an AWS-owned destination on
  the Sandbox list, a small widening) or they do not work. **Recommended: leave it out** until somebody asks
  for the feature — an allow-list entry nobody uses is reach nobody needed. Record whichever way it goes;
  do not let it be discovered as a breakage.
- **3.6 — [Claude] Read the two portal surfaces the optional table names, before they are needed**: the
  **Portal Query Editors** (`sqlworkbench`, `sqlworkbench-v2`) and **CloudWatch** (`logs`). Under design B a
  portal feature whose endpoint is absent has no path at all; measuring which of the two the estate actually
  uses is cheaper here than discovering it in Stage 9. The `codeconnections.api` /
  `codestar-connections.api` pair from the same table is **Stage 7's** input, not this stage's — it is what
  open question 26's `gitConnectionArn` would need.
- **3.7 — [Claude] Answer the two Stage 3 questions**: whether anything misses the AL2023 mirror path, and
  whether `lakeformation` leaves the core endpoint list (verification (ix)).

### 4. Measure the workflow surface — the premise the promotion chain now rests on

**Action:** author a two-task workflow in the Sandbox project and read what it produced. **Why:** with
Development gone, **all** authoring happens in Sandbox and every workflow that reaches Production is
promoted from there. **Explanation:** nothing has confirmed that a Studio-authored workflow produces a
definition a pipeline can carry — no Workflows blueprint is enabled here, the synchronisation between
Unified Studio and MWAA Serverless is documented as a fact with no mechanism, and `start_date` *must be in
the future* at `CreateWorkflow`, so a YAML exported earlier fails at deploy. This was Stage 10's
verification (i), pulled forward because Stage 10's design now depends on it.

- **4.1 — [Claude] Find what enables the surface**: which act creates a project's workflow connection — a
  blueprint, or a connection on the project. `docs/SMUS.md`'s roster says the serverless Workflows surface
  is separate from the eleven configurations, and the answer decides whether 6a's blueprint list changes.
- **4.2 — [user] Author a two-task workflow** in the Sandbox `experimentation` project.
- **4.3 — [Claude] Read the definition**: `aws mwaa-serverless list-workflows` / `get-workflow` as
  `awsds-infra-sandbox-1`; fetch `DefinitionS3Location` and run the YAML through D28's promotion lint.
- **4.4 — [Claude] Read the run's identity**: which role the Sandbox-side run used (it is not D28 item 3's
  per-workflow role), from CloudTrail.
- **4.5 — [Claude] Extend the lint, into Stage 8**: reject project-scoped references (connection names,
  notebook ids, `datazone_usr_role_*`), rewrite `start_date` at deploy time, enforce the operator
  allow-list, cap `execution_timeout` at 3600 s, and pin `DefinitionS3Location.VersionId`. Add artifact
  class **(2b) operator code package** to D28 — Python and Bash operators carry a code archive the six
  classes do not name.
- **4.6 — [Claude] Carry the network shape forward to Stage 10**: the workers' documented private-routing
  shape (two private subnets in **two AZs**, no NAT and no IGW route, interface endpoints for `logs`,
  `monitoring` and `kms`, a self-referencing security group) is what Stage 10 builds in `VPC-Workloads`.
  Note the two-AZ requirement as a **named D9 exception with a price**, and treat the guide's
  "outbound deny-all NACL" line as a claim to verify at build time rather than to copy — a stateless ACL
  denying all egress would break the endpoints it sits in front of.

### 5. Prove the lifecycle — the half of D11 that Studio has never had

**Action:** observe idle shutdown and run the teardown. **Why:** `scripts/down-studio-apps.py` has had a
body since 2026-08-21 and has never deleted a running app; idle shutdown is configured and has never been
observed to fire. **Explanation:** both are D11's promise for the most expensive thing in the estate, and
neither has been measured once.

- **5.1 — [user] Observe idle shutdown**: leave a space idle past its threshold and read the app's
  disappearance (verification (x)'s second half).
- **5.2 — [user] Run the teardown**: `make down ENV=sandbox` deletes every running app and touches nothing
  else; `US-10` reads zero running apps (verification (xi)).
- **5.3 — [Claude] State the layers**: which Studio objects are `[P]` (the domain, the profiles, the
  configurations, the registered image), which are `[E]` (spaces, apps, jobs) and what `make down` may
  never touch — into `conventions.md` §5.1.
- **5.4 — [user] Exercise the hub precondition**: `make up ENV=sandbox` must refuse while 6c's hub hosts are
  stopped, naming the stopped host. This is the first exercise of 6c step 7.2 from a Studio session, and the
  first time INT-21's availability cost is felt deliberately rather than discovered.

### 6. Close the open verifications and the log-group residue

**Action:** answer the ten rows the old stage left open and restate the SMUS document. **Why:** each names a
claim nobody has measured. **Explanation:** closing them is what makes the environment's description true
rather than intended.

- **6.1 — [Claude and user] Answer iii, viii, xiv, xv, xvi, xvii and xix**: the two-AZ blueprint acceptance;
  a VPC-only space starting on the endpoint set under design B; whether the blueprint's manage-access role
  must be a Lake Formation administrator (open question 24's other half); whether a blueprint-created
  database arrives without `IAMAllowedPrincipals`; the shape of the grant the portal writes when it fulfils
  a subscription; whether `datazone:Get*` reaches `GetEnvironmentCredentials` (open question 20, with the
  vend attempt 2.5 never made); and which `aws:SourceVpce` an S3 call from a project subnet presents now
  that the account's gateway endpoint is the only candidate.
- **6.2 — [Claude] Finish the log groups**: confirm the named group receives the apps' output and that a
  running-app metric exists to alarm on; `9.1` created the groups and never read one.
- **6.3 — [Claude] Restate the SMUS document**: `docs/SMUS.md` for one associated account, one project
  profile, the workflow surface as measured in step 4, and the CI/CD tool as what it is — an exporter on the
  Sandbox side, never a deployer into a Workload account (D28's amendment, written at Stage 8).

---

## Deliverables

- The house image registered, selectable and pulled across the account boundary.
- A working session's friction list under the proxy, and the `NO_PROXY` contract proven by a CloudTrail
  reading.
- A Studio-authored workflow whose definition passes the promotion lint, with its run identity recorded,
  and the workers' network shape handed to Stage 10.
- Idle shutdown and `make down` both observed; the Studio layer table written; the hub precondition
  exercised.
- Ten verification rows answered, or explicitly re-homed with an owner.

## Validation

`./aws/studio.py` all-pass with one Interactive account; `US-10` zero running apps after `make down`;
`./aws/egress.py` showing no NAT and no default route while a session runs; `./aws/proxy.py` `PX-3` green
after any ACL entry step 3 adds; the deny pair's two wordings in the log.

## Cost

No standing cost of its own. A session costs the Sandbox `[E]` endpoint set plus the space's instance; the
workflow measurement costs MWAA Serverless task-hours with a one-minute minimum. Both rates come from
`docs/PRICING.md` as 6c step 7.4 leaves them.

## Decisions due while executing

1. **Whether `codewhisperer` joins the Sandbox proxy list** (3.5). Recommended: no, until asked for.
2. **Which portal surfaces of the optional endpoint table this estate actually uses** (3.6) — each one used
   is an endpoint to add, each one unused is a line not to pay for.

## Verifications to answer while executing

The ten rows of 6.1, plus: does the registered image survive a blueprint reconciliation (2.4), and does the
workflow surface exist without a blueprint change (4.1)?

## Risks

- **The workflow surface is not enabled by anything we control**, which moves 4.1's answer into a blueprint
  change and re-opens 6a's decision 5. Recorded as that step's own alternative.
- **A component with no proxy support inside the image** (3.4). The fallback is an endpoint, then D38's
  per-VPC NAT contingency — in that order, and never a default route.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
