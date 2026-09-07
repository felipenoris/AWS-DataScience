# Stage 6d — Unified Studio: what 6a left owed

| | |
|---|---|
| **Status** | not started — **created 2026-09-05** by splitting the old Stage 6, revised the same day into the action-checklist format. It holds only what had not run, re-cut to the estate the split produces: **one** Interactive account (Sandbox), no NAT anywhere, every internet call through the institutional proxy. Two items the old stage carried are gone rather than pending — the design A / design B **comparison** (6c settles it by construction) and the derived-zone decision (dissolved 2026-08-26). **Step 7 added 2026-09-06**, from a reading of the plan against [`objectives.md`](../objectives.md): the local-VS-Code clause had its **policy** half applied at 6a step 3.2 and no step anywhere that opens the connection — so the endpoints it needs under design B were never derived (AWS's own two pages sit in `REFERENCES.md`, consumed by nothing), the two denies were never exercised, and **nothing had ever checked that the principal carrying them is the one that calls `sagemaker:StartSession`** |
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

**Step 7 needs a space to attach to**, so it follows 2.3 — its own is a **Code Editor** space, not the
JupyterLab one 2.3 creates — but **7.1 is taken before anything else in the stage**: if the channel needs an
endpoint the Sandbox list lacks, that is a `sandbox/egress/` edit and an apply, not a portal click. It is
numbered after the close because numbers here are identifiers: step 6 remains the close, and 7's answers are
read into it.

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
- **3.6 — DONE 2026-09-07, AND THE TWO SURFACES ARE IN OPPOSITE STATES.** Measured against the
  Region's own catalog, all four names exist. **`logs` is already covered — by accident**: it has
  been in `vpc-egress`'s `core_services` since Stage 3, for another reason, so CloudWatch has an
  endpoint in every VPC. **Portal Query Editors has none, in any VPC** — and under design B that is
  not a slower path but **no path at all**, a feature that exists in the portal and fails on first
  use. **Both spellings exist** (`sqlworkbench`, `sqlworkbench-v2`) and which one the portal calls
  needs the feature opened, so it is recorded as a **named gap** rather than closed by adding both
  at 0.020/h for something nobody has used. `codeconnections.api` and `codestar-connections.api`
  both exist and are confirmed as **Stage 7's** input. *The original step follows:*
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

### 7. Open the remote-IDE channel — the objective everything so far has only scoped

**Action:** connect a VS Code on the laptop to a Sandbox space, over the tunnel and through the proxy, and
read both perimeters the connection crossed. **Why:** [`objectives.md`](../objectives.md) asks for it in one
clause — *"possibility of remote connecting their local computer vscode to a remote session"* — and every
artefact built for it so far is a **deny**: [1c](stage-01c-preventive-policies.md) withholds
`sagemaker:StartSession` from the `Interactive` document alone (`Workloads`, `Data` and `Identity` deny it,
and 1c says in its own text that denying it here would deny the feature `CLAUDE.md` asks for), and
[6a](stage-06a-unified-studio.md) step 3.2 put two tag-scoped denies into the six persona sets. **Nobody has
ever made the call.** **Explanation:** a channel whose entire implementation is a pair of conditions on an
action never invoked is Lesson 5 and Lesson 20 at once — an intention, and a statement that is attached
rather than exercised. It is also the only feature in the estate that crosses **both** perimeters in a
single act: the laptop's half leaves through the tunnel and the explicit proxy, the space's half sits in a
spoke with no default route. Neither half has ever been read.

**How the VPN enters this, because it enters twice and the two halves fail differently.** *The tunnel is
required for two independent reasons, and an executor who knows only one of them will misdiagnose the
other.* **(1) The call.** `DenyControlPlaneOffVpn` (`identity/sso/policies-shared.tf`) denies `*` on `*` in
the six persona sets — deliberately total rather than a list of actions — so `sagemaker:StartSession` is
inside it. Its three conditions are ANDed and off the tunnel all three hold: the source is not a VPN home's
Elastic IP, the call is not `ViaAWSService`, and a laptop carries no `aws:SourceVpc` at all, which the
`IfExists` form passes rather than rescues. The refusal is an explicit IAM deny naming that document, not a
timeout. **(2) The path.** Under D38 the VPN client is a *private-network* client: the tunnel routes
`0.0.0.0/0, ::/0`, the laptop's whole internet crosses the explicit proxy, and both the API call and the
session's data channel therefore present the **proxy's** Elastic IP — which is where 6c re-keys every
VPN-only condition. Squid is default-deny, so the channel also needs its destination on the allow-list:
**the tunnel can be up, the identity correct, and the connection still die at the proxy** (7.5). The two
halves hold each other up — a **split** tunnel would leave every API call on the laptop's own connection
and the statement of (1) would then deny the user everything, tunnel up or not.

**One measured caveat, and one thing that is not settled.** The **portal is not covered** by that statement
— it is entered by an IdC sign-in, not by an IAM call, measured both ways on 2026-08-22 (6a step 1.7: off
the tunnel a persona opened the portal and enumerated its project profiles, while the console was refused
by name). So the **deep link** can be started off the VPN and the refusal arrives at `StartSession` rather
than before it — a diagnosis note, not a hole. What is **not** settled is whether "VPN-only" is a true
sentence about this channel at all: it holds only if the caller is a **persona** role, which is 7.2's
question, and it is a claim about the **call** rather than the **channel** until 7.7 says whether an
established session outlives the tunnel. **The space side is indifferent to all of this** — it needs
endpoints (7.1), not a tunnel — so the two requirements are separate, and failing one looks nothing like
failing the other.

- **7.1 — [Claude] Derive the required set from AWS's pages, not from the estate's list**: two
  [`docs/REFERENCES.md`](../../REFERENCES.md) rows already carry them — *configuring remote access* and
  *network configuration for remote access* — and **no step has ever consumed either**. Write down which
  names the **space** side needs and which the **laptop** side does. Under design B this is not a latency
  question: an absent endpoint is no path at all. The `ssm` / `ssmmessages` / `ec2messages` trio that
  [6c](stage-06c-networking-hub.md) step 5.5 puts in every instance-bearing spoke is a **candidate** answer
  and not a measured one — it was added for Session Manager on EC2, and whether a space's remote agent uses
  the same three is exactly what this reading settles. Take it **first**: a name the Sandbox list lacks is a
  slice edit with a lead time, not a portal click.
- **7.2 — THE STATIC HALF IS DONE 2026-09-07, AND IT IS DECISIVE WITHOUT CLOUDTRAIL.** Read back
  from Identity Center: `DataScientistAccess` carries **both denies** on `sagemaker:StartSession`
  and **no `Allow` for it at all** — its only SageMaker Allow is `ReadSageMakerStatus`
  (`Search`, `List*`, `Describe*`). `policies-sagemaker.tf` says in its own comment where the grant
  lives: *"the project role is"*. **So the pair is attached to a principal that cannot make the call
  and absent from the principal that can**, and the conclusion holds whichever way 7.5 resolves the
  caller: with persona credentials the call fails for want of an Allow (an access-denied that is
  **not** the deny pair, and reads like a broken feature); with the project role it succeeds
  **unscoped**. **The objective's scoping was granted by nothing** — Lesson 18 plainly, with
  Lesson 28 underneath, since the grant and the constraint are in two different slices.
  The repair the step already names is right and is **not** a new SCP: the **D13 permissions
  boundary**, the one instrument this estate has that reaches a blueprint-authored role. Not applied
  here — the boundary field is write-only and 7.5's CloudTrail is what names the role.
  *The original step follows:*
- **7.2 — [Claude] Find out which principal makes the call, because the scoping rests on the answer**: 6a
  step 3.2's two denies live in the **six persona sets**, and `policies-sagemaker.tf` says in its own
  comment that `sagemaker:StartSession` is granted by the **project role**, not by those sets. A deny is a
  control only over the principal that carries it (Lesson 18, Lesson 28): if the caller is a
  blueprint-authored project role, the pair never evaluates and the objective was granted with no scoping
  at all. Read the caller from CloudTrail in 7.5's own record. **If it is not a persona, the repair is the
  D13 permissions boundary of 6a step 2.1** — the only thing this estate attaches to a role the blueprint
  writes — and not a new SCP, which would deny the feature rather than scope it.
- **7.3 — [Claude reads, user decides] Decide whether a space is created with remote access at all**:
  nothing in the estate turns it on, and `sagemaker:RemoteAccess` appears in this repository only as the
  kill-switch named in a comment (`terraform-live/identity/sso/policies-sagemaker.tf`). Read whether the
  portal exposes the choice per space, whether the project or the domain must permit it first, and whether
  it can be set after creation. **Recommended: on for one space, by hand, and off as the default** until
  7.7 has a reading — the residual is a 12-hour credential, so the feature earns its default after the
  measurement rather than before it.
- **7.4 — [user] Connect, and record which of the three methods worked**: deep link, AWS Toolkit and SSH
  are all documented. They are not one channel and they will not fail the same way. One working method
  satisfies the objective; the other two are recorded as *worked*, *refused* or *not tried*, never left
  blank — a method nobody tried is not a method that does not work.
- **7.5 — [Claude] Read the two perimeters the connection crossed**, one instrument each. CloudTrail must
  show the **proxy's** Elastic IP as `sourceIPAddress` on the `StartSession`; the laptop's own address
  there is the finding and not the happy path, and it is what separates a split tunnel from a statement
  that did not fire. Then `./aws/proxy.py --on-host` for the CONNECT the client opened: a long-lived tunnel
  to an AWS-owned name that either is on the allow-list already or is the entry this step adds. **If the
  client ignores `HTTPS_PROXY`, this is 3.4's shape on the laptop** — the same undocumented question, the
  other side of the tunnel. **Take the negative control in the same sitting** — the same connection
  attempted with the tunnel **down**. It must be refused, by name: that is the first exercise
  `DenyControlPlaneOffVpn` has ever had on this action. If it is **not** refused, 7.2 has been answered
  from the other direction, because no statement attached to a persona reached the call.
- **7.6 — [user provokes, Claude records] Exercise 6a step 3.2's pair — its first exercise**: attach to a
  space carrying **another project's** tag, and to **another user's** space in the same project. Both must
  be refused, and the wording must name an **identity-based policy** — an SCP says *service control
  policy*, a boundary says *permissions boundary*, so the wording is the attribution and the exit code is
  not (Lesson 24). A refusal naming something else is 7.2's answer arriving from the other direction.
- **7.7 — [Claude] Measure the residual instead of restating it** (open question 14,
  [Stage 11](stage-11-dlp.md) step 3.3): does the session survive the tunnel going down, and does it
  survive portal logout — AWS documents up to **12 h**. One reading each, and both change what Stage 11 may
  write: a session that outlives the tunnel makes the VPN-only statement a control on the **call** and not
  on the **channel**, which is a different sentence from the one accepted today.
- **7.8 — [Claude] Write the client half down**, in a runbook that does not exist yet —
  `docs/plan/runbooks/remote-ide.md`: what a laptop needs (client and toolkit versions, the proxy
  variables, the tunnel, the identity to sign in as), which failures are silent, and the one symptom that
  is **not** a client problem: an endpoint the space side does not have. Its row in `CLAUDE.md`'s routing table lands in the same sitting, the way every
  other runbook's did — a runbook nothing points at is a file, not a procedure.

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
- **The remote-IDE channel opened once from the laptop** — the endpoint set it needs under design B, the
  principal that calls `StartSession`, 6a step 3.2's two denies exercised, the 12-hour residual measured
  rather than restated, and the client half in a runbook the routing table points at.

## Validation

`./aws/studio.py` all-pass with one Interactive account; `US-10` zero running apps after `make down`;
`./aws/egress.py` showing no NAT and no default route while a session runs; `./aws/proxy.py` `PX-3` green
after any ACL entry step 3 or step 7 adds; the deny pair's two wordings in the log, and the remote-IDE
pair's two alongside them; one `sagemaker:StartSession` in CloudTrail carrying the proxy's Elastic IP, and
the same call refused **by name** with the tunnel down.

## Cost

No standing cost of its own. A session costs the Sandbox `[E]` endpoint set plus the space's instance; the
workflow measurement costs MWAA Serverless task-hours with a one-minute minimum. Both rates come from
`docs/PRICING.md` as 6c step 7.4 leaves them. **Step 7 can add a line rather than an hour:** each endpoint
7.1 turns out to require is USD 0.010/h per AZ in this Region ([`docs/PRICING.md`](../../PRICING.md) §3) —
`[E]`, so it is up only while `egress/` is, and it is a *recurring* cost decided by a *one-off*
measurement, which is the shape worth naming before it is paid.

## Decisions due while executing

1. **Whether `codewhisperer` joins the Sandbox proxy list** (3.5). Recommended: no, until asked for.
2. **Which portal surfaces of the optional endpoint table this estate actually uses** (3.6) — each one used
   is an endpoint to add, each one unused is a line not to pay for.
3. **Whether a space is created with remote access enabled, and whether that becomes the default** (7.3).
   Recommended: one space by hand, default off until 7.7 reads the 12-hour residual.
4. **Where the tag-scoped `StartSession` pair belongs, if 7.2 says the caller is not a persona** — the D13
   permissions boundary rather than the six persona sets. This is a *re-homing*, not a widening: the same
   two conditions, attached to the principal that actually makes the call.

## Verifications to answer while executing

The ten rows of 6.1, plus: does the registered image survive a blueprint reconciliation (2.4); does the
workflow surface exist without a blueprint change (4.1); **which principal calls `sagemaker:StartSession`
(7.2), which endpoints the remote channel needs under design B (7.1), and whether a remote session outlives
the tunnel and the portal logout (7.7)**.

## Risks

- **The workflow surface is not enabled by anything we control**, which moves 4.1's answer into a blueprint
  change and re-opens 6a's decision 5. Recorded as that step's own alternative.
- **A component with no proxy support inside the image** (3.4). The fallback is an endpoint, then D38's
  per-VPC NAT contingency — in that order, and never a default route.
- **The VS Code client or its toolkit may not honour the proxy** (7.5) — 3.4's risk on the laptop, with the
  same ladder and one rung fewer: the client is not ours to configure past its own settings, and there is no
  endpoint to fall back to on that side of the tunnel.
- **The scoping may never have applied** (7.2). If the project role is the caller, 6a step 3.2 has been
  attached to the wrong principal since the day it was applied — a control believed to exist, which is worse
  than a known gap, and the reason this step reads the caller before it reads anything else about the
  refusals.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
