# Stage 6d — Unified Studio: what 6a left owed

| | |
|---|---|
| **Status** | **IN PROGRESS — STEP 9 APPLIED, STEP 8 OPEN, 3.2 AND 3.3 DONE, 3.1 HALF TAKEN, 2026-09-08** ([log](../../log/log-stage-06d-unified-studio-remainder.md)): the first working session under the proxy, from a JupyterLab terminal with the variables exported **by hand** (2.2 is still unapplied) and on the **stock** image. `NO_PROXY` held on two channels that do not share a failure mode (CloudTrail's `vpcEndpointId`, and the access log's *absence* of every AWS name); the allow-list enforced (`pypi.org` 200, `example.com` 403); **`conda` and CRAN refused by name — decision due 6's evidence**; the `codeload.github.com` redirect refused on a third source plane. **Owed**: `uv`, Julia and R, in the house image. **And one check was corrected by the user's own first command**: `--noproxy '*'` returning `000` measured a **DNS** refusal, not the absent route — the routing half stays 6c 6.3's probe (Lesson 42). **A second sitting the same day added step 8 and one
plane entry**: `sudo apt update` proved the variables stop at **`sudo`** (`env_reset`), so 2.2 owes two
image-side files beside its `ContainerEnvironmentVariables`; and a **Code Editor** space failed to update
**AWS's own two extensions** at startup with four `getaddrinfo ENOTFOUND open-vsx.org` — a **resolution**
failure, so the VS Code server never saw a proxy and this plane was never consulted. `open-vsx.org` is
authored onto `sandbox-foundation` (**unapplied**); **step 8** carries the rest — the delivery mechanism
2.2 does not cover, and an asset host nobody has read yet. **A third sitting closed 8.2 and opened step 9.**
The DNS Firewall log settled the attribution — `open-vsx.org` **BLOCK**, 8 queries, from a Sandbox address —
and named **three more** the Code Editor needs: `idetoolkits.amazonwebservices.com` (**`amazonwebservices.com`
is not `amazonaws.com`**), `api.github.com` and `raw.githubusercontent.com`, the last two uncovered because
the plane's `github.com` is a **bare** name. And **D38 §6 was amended by the user**: `production-foundation`
is **`open`**, not an allow-list — a build host's control is the reviewed Dockerfile, not a hostname list —
so `proxy_allow_shared` and its CloudFront entry are deleted, a plane's mode is now decided by **which of two
maps** it is in, and `DN-4` was rewritten to *"no plane is open except the ones a decision names"*.
`terraform plan`: `0 to add, 1 to change` — **applied the same day**, re-plan `No changes`, `DN-1`..`DN-4`
all pass. **Owed**: `PX-3` (the running `squid.conf`, after the State Manager half-hour) and 9.5, one full
build and push across the plane whose CloudFront entry this deleted. *Earlier:* **3.6, 7.1 and 7.2 taken 2026-09-07**: the two portal surfaces read, the remote-IDE endpoint set derived (**nothing to add on either side**), and the `StartSession` pair found attached to a principal that never makes the call — so **the connection method decides the perimeter** (decision due 4), and step 7 was re-cut around that the same day. **Created 2026-09-05** by splitting the old Stage 6, revised the same day into the action-checklist format. It holds only what had not run, re-cut to the estate the split produces: **one** Interactive account (Sandbox), no NAT anywhere, every internet call through the institutional proxy. Two items the old stage carried are gone rather than pending — the design A / design B **comparison** (6c settles it by construction) and the derived-zone decision (dissolved 2026-08-26). **Step 7 added 2026-09-06**, from a reading of the plan against [`objectives.md`](../objectives.md): the local-VS-Code clause had its **policy** half applied at 6a step 3.2 and no step anywhere that opens the connection — so the endpoints it needs under design B were never derived (AWS's own two pages sit in `REFERENCES.md`, consumed by nothing), the two denies were never exercised, and **nothing had ever checked that the principal carrying them is the one that calls `sagemaker:StartSession`** |
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

**Step 7 needs a space to attach to**, so it follows 2.3 — its own is a **Code Editor** space at
`ml.t3.large`, not the JupyterLab one 2.3 creates. **7.1 was taken first (2026-09-07) and needs no slice
edit**; what now precedes 7.3 is **decision due 4**, the connection method, because it decides which
principal the repair goes on. Step 7 is numbered after the close because numbers here are identifiers: step 6
remains the close, and 7's answers are read into it.

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
  tag convention `docs/SMUS.md` owns. Add the `dev-env` rank in `layers.py` first. A hand apply, once:
  conventions §6 lists this slice as **pipeline-written** (Stage 8 step 1, INT-18), which takes it over.
- **2.2 — [Claude⚡] Attach it to the domain**: the app image configuration, carrying 6c step 5.6's proxy
  variables as `ContainerEnvironmentVariables` rather than baked into the Dockerfile.
  **NECESSARY AND NOT SUFFICIENT, MEASURED 2026-09-08 (3.1).** `ContainerEnvironmentVariables` sets the
  *process* environment, and two things in a working session never see it: **`sudo`**, which resets the
  environment before `apt` ever runs, and **the VS Code server** in a Code Editor app, which is a
  different app type and not covered by a JupyterLab image configuration at all. So this sub-step's
  deliverable grew by two image-side files — `/etc/apt/apt.conf.d/01proxy` and a sudoers `env_keep`
  for the six proxy variables — and by a cross-reference: the Code Editor half is **step 8**.
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

- **3.1 — HALF TAKEN 2026-09-08, ON THE STOCK IMAGE, AND THE HALF THAT RAN CONFIRMED EVERY
  PREDICTION.** From a JupyterLab terminal with the variables exported by hand (2.2 is not applied):
  `pypi.org` **200**, `pip download requests` fetching index **and** wheel, `example.com` **403** —
  the allow-list *enforced*, not merely configured. **`conda` and CRAN refused BY NAME** in the
  proxy's access log (`repo.anaconda.com`, `cloud.r-project.org`, both `TCP_DENIED`), which is
  **decision due 6's evidence**, taken from the network rather than from the package manager.
  **And a third source plane met the redirect trap**: `github.com` answered `200`, the release
  tarball redirected, and `codeload.github.com` — on no plane — was refused in the same second,
  the same shape as `public.ecr.aws` → CloudFront at 6c 5.8. **And `apt` found a boundary the
  variables do not cross**: `sudo apt update` failed with `Could not resolve archive.ubuntu.com` —
  a name that **is** on the plane — and failed **identically before and after the export**, which
  is the measurement rather than the symptom: `sudo`'s `env_reset` drops `http_proxy`, so `apt` ran
  with a clean environment and resolved the destination itself. `sudo apt -o
  Acquire::http::Proxy=… update` then fetched **10.6 MB in 3 s**. The house image therefore owes
  `/etc/apt/apt.conf.d/` **and** a sudoers `env_keep` **beside** 2.2's variables — see 2.2.
  **What is still owed**: `uv`, `Pkg`
  (Julia) and R were **not run**, and the reading belongs in the **house** image, where Julia and R
  are image-delivered — so the step stands, narrowed to the ecosystems the stock image cannot
  answer for. The sitting is [`log-stage-06d`](../../log/log-stage-06d-unified-studio-remainder.md),
  2026-09-08. *The original step follows:*
- **3.1 — [user] Install packages** from a JupyterLab terminal, one ecosystem per command, and paste each
  result: `pip`, `uv`, `conda`, `Pkg` (Julia) and R. Read against the compute plane's list
  (`hub-anchors.tf`, `proxy_allow_sandbox`, 20 names) before running, so a refusal is expected rather than
  diagnosed: `pip`/`uv` (`pypi.org`, `files.pythonhosted.org`, `astral.sh`), Julia (five `julialang` names)
  and Rust (`crates.io`, `rust-lang.org`) **are on it**; **`conda` (`repo.anaconda.com`,
  `conda.anaconda.org`) and CRAN (`cloud.r-project.org`) are not** — each is a `403` naming the host in
  the proxy's log, and a decision (due 6): allow the name on the compute plane, or record the loss and
  keep the ecosystem image-delivered (`images/dev-env/`'s premise). CodeArtifact needs no endpoint in
  Sandbox: `.amazonaws.com` is on the plane, so INT-02's consumer half is proved **through the proxy**.
- **3.2 — DONE 2026-09-08, AND BY TWO CHANNELS RATHER THAN ONE.** The instrument was
  `sts:GetCallerIdentity` rather than `aws s3 ls` — the call the session made — and CloudTrail carries
  **`vpcEndpointId` `vpce-0f5adbfef0071b8e5`**, confirmed as `com.amazonaws.us-west-2.sts`, with
  `sourceIPAddress` the app ENI and the project role's `SageMaker` session. **The proxy's access log is
  the second channel and it reads by ABSENCE**: not one AWS name in the session's window — and the
  absence is decisive precisely because `.amazonaws.com` **is** on this plane, so a failed `NO_PROXY`
  would have been *permitted*, arriving with neither `aws:SourceVpc` nor `aws:SourceVpce`. The failure
  ruled out is the one that succeeds. *The original step follows:*
- **3.2 — [Claude] Check the door each AWS call takes**: in the same session, `aws s3 ls` on the projects
  bucket must still show `vpcEndpointId` in CloudTrail — the proof that `NO_PROXY` kept AWS traffic on the
  endpoints and that the 4d defect shape has not returned.
- **3.3 — DONE 2026-09-08 FOR THIS SESSION, AND THE STEP NAMES THE WRONG INSTRUMENT FOR HALF OF IT.**
  `./aws/proxy.py --on-host` reads the rendered planes and the host's `squid.conf` — `PX-1`, `PX-2`,
  `PX-3`, `PX-5` `pass`, `PX-4` its standing note — and **carries no access log at all**. The log is a
  CloudWatch group and was read directly: `filter-log-events` on `/awsds/prod/proxy` as
  `awsds-infra-prod`, nine lines, every one sourced from the app ENI. Both readings are in the log
  entry; anyone repeating 3.3 needs the second command as well as the first.
  *The original step follows:*
- **3.3 — [Claude] Read what the proxy saw**: `./aws/proxy.py --on-host` for the session's access log.
- **3.4 — ONE COMPONENT ANSWERED 2026-09-08, AND IT IS THE ONE THE STEP DID NOT LIST.** The Code
  Editor's **extension gallery** does not honour the proxy — not because it refuses one, but because
  nothing puts one in the VS Code server's environment: four `getaddrinfo ENOTFOUND open-vsx.org`, a
  **resolution** failure, which an explicit-proxy client never performs. The list this step enumerates
  is therefore short by at least one, and the failing component turned out to be **AWS's own two
  extensions updating themselves at startup**. Broken out as **step 8** rather than absorbed here,
  because the fix is a plane entry *and* a delivery mechanism 2.2 does not cover. *The original step
  follows:*
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

- **4.1 — [user reads, Claude records] Find what enables the surface** — the vendor pages narrow it
  (read 2026-09-07): the **`Workflows` blueprint creates a provisioned MWAA environment**, the shape D7
  amended away, so enabling it is the *wrong* act; the user guide says SMUS *"supports serverless
  workflows powered by MWAA Serverless"* as a project capability and names no blueprint for it. **[user]**
  Open *Workflows* in the Sandbox `experimentation` project and read whether a **serverless** workflow can
  be created with 6a's eleven configurations unchanged; if the portal asks for a capability, blueprint or
  connection first, record its exact name. **[Claude]** Record the answer in `docs/SMUS.md`'s roster — it
  decides whether 6a's decision 5 re-opens.
- **4.2 — [user] Author a two-task workflow** in the Sandbox `experimentation` project.
- **4.3 — [Claude] Read the definition**: `aws mwaa-serverless list-workflows` / `get-workflow` as
  `awsds-infra-sandbox-1`; fetch `DefinitionS3Location` and run the YAML through D28's promotion lint.
- **4.4 — [Claude] Read the run's identity** from CloudTrail: the vendor says every serverless workflow
  *"runs with its own execution role and worker"*, so the expected reading is a **per-workflow role SMUS
  creates** — D28 item 3's shape arriving from the vendor's side. Record the role's name and who authored
  it: a blueprint-authored role is inside the D13 boundary's reach, a service-created one is not.
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

**Action:** connect a VS Code on the laptop to a Sandbox space and read both perimeters the connection
crossed. **Why:** [`objectives.md`](../objectives.md) asks for it in one clause and every artefact built for it
is a **deny** ([1c](stage-01c-preventive-policies.md) withholds `StartSession` from the `Interactive` document
alone; [6a](stage-06a-unified-studio.md) step 3.2 put two tag-scoped denies into the persona sets) — nobody
has ever made the call. **Explanation:** 7.1 and 7.2 (2026-09-07) changed this step's shape. The endpoints
were already there. What decides everything else is **which connection method the estate adopts**, because
the method decides which principal calls `sagemaker:StartSession` — and so which perimeter applies:

| method | who calls `StartSession` | `DenyControlPlaneOffVpn` | the 6a pair | works off the VPN? |
|---|---|---|---|---|
| **1 — deep link** from the portal | the **project role**, server-side (AWS's managed policy scopes it by the two DataZone tags, in Allow form) | never evaluates | never evaluates | **yes** — INT-16's portal is reachable off-tunnel and the data channel is a token-bearing WebSocket |
| **2 — AWS Toolkit** | the laptop's IdC credentials (the persona) | applies | evaluates — and **denies every space**: a persona session carries no DataZone tag | no |
| **3 — SSH `ProxyCommand`** | the laptop's credentials (the persona) | applies | idem | no |

Two things hold for every method. **The tunnel is required twice** — for the call (off the tunnel the
persona's deny is total, an explicit IAM refusal naming the document) and for the path (the data channel
crosses the explicit proxy, so `HTTPS_PROXY` must reach the process tree: a browser-launched VS Code has
none on macOS and **times out**, Lesson 55). And **the space side is indifferent** — it needs 7.1's seven
endpoints, which exist, and nothing else. **Recommended: Method 3**, the only one whose caller the VPN
statement reaches and whose process tree the user controls, with the repair decision due 4 describes.


- **7.1 — DONE 2026-09-07, AND THE ANSWER IS "NOTHING TO ADD" ON BOTH SIDES — WITH THREE THINGS THE
  PAGES SAY THAT THE STEP DID NOT ASK.** **Space side** (the SMUS admin guide's isolated-VPC table,
  eight rows): `sts`, `ssm`, `ssmmessages`, `sagemaker.studio`, `sagemaker.runtime`, `sagemaker.api`,
  `datazone` — **all seven already in `sandbox/egress/`** (`sts` in the core list, the rest in
  `extra_services`); `datazone-fips` is a compliance variant nobody needs. The SageMaker AI guide's
  private-subnet page adds only `ssm` + `ssmmessages` *"to the standard set"* — **`ec2messages` is on
  neither page**: 6c step 5.5's trio was two-thirds this channel's answer, and the third serves the
  probe hosts. The module's endpoint policy already carries the vendor's recommended
  `aws:PrincipalIsAWSService` branch (`AllowAWSServicePrincipals`), so the space's SSM registration —
  an AWS service principal with no org id — passes statement 2 instead of dying at statement 1.
  **No slice edit, no lead time.** **Laptop side** (the SageMaker AI guide's local prerequisites):
  `ssm`, `ssm…api.aws`, `ssmmessages`, `ec2messages`, plus `api.sagemaker` for the `StartSession`
  call Methods 2 and 3 make locally — all on the tunnel plane, which is **`open`** since 2026-09-07,
  so nothing to add there either; what remains is whether each program **honours the proxy**. `aws`
  does (botocore). `session-manager-plugin` — read from its source, not measured — dials with
  gorilla's `websocket.DefaultDialer`, whose `Proxy` is `http.ProxyFromEnvironment`: it honours
  `HTTPS_PROXY` **when the variable reaches its process**, and that is the catch 7.5 must expect —
  Method 1's deep link launches VS Code from the browser, which on macOS inherits no shell
  environment (issue #67's neighbour), so the plugin dials `ssmmessages` directly, the FORWARD chain
  rejects it and the symptom is a **timeout** (Lesson 55). Method 3 from a terminal that exported
  the variables is the only method whose process tree the user controls. **The three unasked
  answers:** (a) **the space needs ≥ 8 GB** — `ml.t3.medium`, the estate's default and its only
  measured price, is named unsupported; `ml.t3.large` and `ml.m5.large` are **priced the same day** — 0.100/h and 0.115/h — and since
  2026-09-07 the space path carries **no ceiling** at all (`sagemaker-denies-v0.2.0`, the user's decision); (b) the image and the profile already qualify — base
  is SMD **4.3.0** (≥ 2.7) with `curl` and `unzip` installed, and TIP is `false` non-editable (6a
  decision 2, which named this feature as its reason); (c) **the VS Code server is downloaded by the
  SPACE**, from `update.code.visualstudio.com` and `vscode.download.prss.microsoft.com` (extensions:
  `marketplace.visualstudio.com`, `*.gallerycdn.vsassets.io`) — a **compute-plane widening** if done
  the vendor's "HTTP proxy" way (`remote.SSH.httpProxy` on the client). Two shapes keep the compute
  plane unchanged: VS Code's own `remote.SSH.localServerDownload = always` +
  `remote.downloadExtensionsLocally = true` (the **laptop** downloads, on the open plane, and pushes
  through the SSH tunnel), or AWS's pre-packaged tarball installed by a lifecycle configuration from
  S3. **Recommended: the client settings** — zero estate change, reversible per laptop; the four
  Microsoft names on `sandbox-foundation` as the fallback; the LCC as the shape for many users.
  Decision due 5. *The original step follows:*
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
- **7.3 — Decide the method and prepare one space** (decision due 4; the residual is a 12-hour credential,
  so the feature earns its default *after* 7.7, not before):
  - **[user decides] The method** — Method 3 recommended; the deep link is the alternative, and choosing it
    means recording in Stage 11 that "VPN-only" is not a true sentence about this channel.
  - ~~**[Claude] Price `ml.t3.large` and `ml.m5.large`**~~ **DONE 2026-09-07**: 0.100/h and 0.115/h in
    `PRICING.md` §8 (Lesson 6). The remote server needs **≥ 8 GB** and `ml.t3.medium` is named
    unsupported; **the space path carries no instance ceiling since the same day** (`sagemaker-denies-v0.2.0`
    — `CreateApp`/`CreateSpace`/`UpdateSpace` exempt; jobs keep the list), so the size is a cost choice.
  - **[Claude] If Method 3, write the three policy changes in one branch**: a tag-scoped
    `Allow sagemaker:StartSession` on the persona sets keyed on `aws:PrincipalTag/IDC_UserName` (the
    vendor's own ABAC example); the 6a pair rewritten to the same key in `sagemaker-denies`; and
    `sagemaker:StartSession` **denied on the D13 boundary** (`sagemaker-prereqs`), which closes the deep
    link's project-role path. **[user]** Enable Identity Center *attributes for access control* with
    `IDC_UserName` mapped to the user name (Identity account, the delegated administrator's console).
    **[Claude⚡]** Apply `identity/sso/` and `sandbox/sagemaker/` — two-commit tag order for both modules;
    `PX-5` and `US-*` green after.
  - **[user] Create a Code Editor space** at **`ml.t3.large`** on the house image from the portal, toggle
    **Remote Access** on in the space's details (per space; settable after creation with the space
    stopped), and — if Method 3 — tag it `IDC_UserName=<your user name>`.
  - **[Claude] Read it back**: `describe-space` — `RemoteAccess`, the instance type, the tags — into the log.
- **7.4 — Connect, and record which of the three methods worked** (one working method satisfies the
  objective; the other two are recorded as *worked*, *refused* or *not tried*, never left blank):
  - **[user] Prepare the laptop**: Remote-SSH ≥ 0.74 and AWS Toolkit ≥ 3.87 in VS Code, the Session Manager
    plugin, the vendor's `sagemaker_connect.sh` as `ProxyCommand` with the persona's SSO profile, a
    `~/.ssh/config` entry whose `HostName` is the **space ARN**, and two settings —
    `remote.SSH.localServerDownload = always`, `remote.downloadExtensionsLocally = true` — so the space
    downloads nothing (decision due 5).
  - **[user] Connect from a terminal that exported the proxy variables**, tunnel up: `ssh <space>` first
    (the `ProxyCommand`'s own errors are readable there), then `code --remote ssh-remote+<space>`. Record
    the first symptom verbatim — a timeout is the environment before it is anything else.
  - **[user] Try the deep link and the Toolkit** the same way, and record each outcome.
- **7.5 — Read the two perimeters the connection crossed, one instrument each, per method**:
  - **[Claude] CloudTrail** on `StartSession`: Method 1 must show the **project role** with an AWS-side
    `sourceIPAddress`; Methods 2 and 3 the **persona** with the **proxy's** Elastic IP. The laptop's own
    address there is the **split-tunnel profile** (6c pass 8): for Methods 2 and 3 never a happy path — the
    persona's deny fires — and for Method 1 what 6c 8.5 predicts; read under both profiles.
  - **[Claude] `./aws/proxy.py --on-host`** for the CONNECTs the client opened — `api.sagemaker`,
    `ssmmessages` — on the tunnel plane's log, each carrying the device's `10.90.0.x` source.
  - **[user provokes, Claude records] The negative control, tunnel down**: Methods 2 and 3 must be
    **refused by name** — `DenyControlPlaneOffVpn`'s first exercise on this action; Method 1 is **expected
    to succeed**, and that reading is what decision due 4 rests on, not a defect in the statement.
- **7.6 — [user provokes, Claude records] Exercise the tag pair on the principal that carries it** — after
  7.3's choice, or it evaluates on nobody: attach to a space carrying **another user's** tag, and to one in
  **another project**. Both refused, and the wording must name an **identity-based policy** (a boundary says
  *permissions boundary*, an SCP *service control policy* — the wording is the attribution, Lesson 24).
- **7.7 — [Claude] Measure the residual instead of restating it** (open question 14,
  [Stage 11](stage-11-dlp.md) step 3.3): does the session survive the tunnel going down, and portal logout —
  AWS documents up to **12 h**. One reading each; a session that outlives the tunnel makes the VPN statement
  a control on the **call** and not the **channel**, a different sentence from the one accepted today.
- **7.8 — [Claude] Write the client half down** in a new `docs/plan/runbooks/remote-ide.md`: what a laptop
  needs (versions, the two VS Code settings, the proxy variables and **where** they must be exported, the
  tunnel, the identity), which failures are silent, and the one symptom that is not a client problem — an
  endpoint the space lacks. Its row in `CLAUDE.md`'s routing table lands in the same sitting.
- **7.9 — [Claude] Write the instrument**, `./aws/remote-ide.py`, read-only, as `awsds-infra-sandbox-1`:
  `RI-1` the seven endpoints of 7.1 exist while `egress/` is up; `RI-2` every space with `RemoteAccess`
  enabled is ≥ 8 GB, its type and hourly rate **reported** (no ceiling on spaces since 2026-09-07); `RI-3` the project role's `StartSession` statements and its
  boundary (`get-role`, never `list-roles`); `RI-4` the persona sets' Allow and pair agree on one condition
  key; `RI-5` the latest `StartSession` events — caller and `sourceIPAddress` — so 7.5 is repeatable.

---

### 8. Make the Code Editor usable — the extension gallery, and the boundary the variables do not cross

**Action:** allow the gallery on the compute plane, put the proxy in the VS Code server's own process tree,
and install one extension. **Why:** on 2026-09-08 a Code Editor space failed to update **AWS's own two
extensions** at its own startup, with nothing configured and no error a user could act on.
**Explanation:** this is 3.4's risk arriving with a name and a date, and it is a step rather than a note
because the repair has two halves that live in different places — a name on `sandbox-foundation`, authored
here, and a delivery mechanism **2.2 does not cover**, because a Code Editor app is a different app type
from the JupyterLab image configuration. A gallery is a code-download path onto the compute plane, the same
class as `pypi.org`: the question is never *whether* code may be fetched, only *from which names*.

- **8.1 — [Claude] DONE 2026-09-08: allow the gallery.** `open-vsx.org` added to `proxy_allow_sandbox` in
  [`hub-anchors.tf`](../../../terraform-live/production/networking/hub-anchors.tf); `terraform validate`
  clean and the four preconditions unaffected — there is no `.open-vsx.org` sibling, so no `dstdomain`
  collision. **Unapplied.** By the derivation it lands on `production-foundation` as well; the comment
  names why that is right today and what would make it wrong (Lesson 51).
- **8.2 — DONE 2026-09-08, AND THE LOG ANSWERED MORE THAN IT WAS ASKED.** `open-vsx.org.`,
  **`firewall_rule_action: BLOCK`**, `rcode NXDOMAIN`, **8 queries from `10.20.65.56`** — a Sandbox
  address. **The space asked**, as the error's shape predicted; the argument is now a record. The same
  source, in the same minutes, was **also** refused three names nobody had listed:
  **`idetoolkits.amazonwebservices.com`** (20 queries — the AWS Toolkit's own asset host, and note the
  domain: **`amazonwebservices.com` is not `amazonaws.com`**, so `.amazonaws.com` does not cover it,
  while `idetoolkits-hostedfiles.amazonaws.com` beside it **was** allowed), **`api.github.com`** and
  **`raw.githubusercontent.com`** (12 each). All three are the IDE working normally. Two independent
  confirmations came free from the same window: `pypi.org` BLOCK from a second Sandbox address — the
  `curl` before the export in 3.1 — and `archive.ubuntu.com`/`security.ubuntu.com` BLOCK from that same
  address, which is `sudo apt update`. **Every name is queried twice**, bare and with
  `.us-west-2.compute.internal` appended by the VPC search domain, and both forms are blocked.
  *The original step follows:*
- **8.2 — [Claude] Attribute the refusal from the estate's own log**: `/awsds/sandbox/dns-firewall`,
  30-day retention, records the rule action beside the name. Not a formality — it settles **which side
  asked**. The hub carries no DNS Firewall (`production/egress` leaves `dns_firewall` at its default
  `false`: *"the hub must resolve everything the proxy is asked to fetch"*), so a laptop resolving through
  the tunnel would have **succeeded** and failed later at the connection, with a refusal rather than
  `ENOTFOUND`. The error's shape already says *the space asked*; this turns an argument into a record.
- **8.3 — DONE 2026-09-08 (with 9.3 — one apply, as the step said).** `0 to add, 1 to change, 0 to
  destroy`; the re-plan reads `No changes`. See 9.4 for the readings. *The original step follows:*
- **8.3 — [Claude⚡] Apply, then wait the half hour.** A list edit reaches the running host on the State
  Manager schedule with **no host replacement** — the parameter is data, the renderer is code. `PX-3` is
  red between the apply and the association, which is expected, and is why it is read twice rather than
  once.
- **8.4 — [Claude⚡ / user] Put the proxy in the server's process tree**, and the mechanism is the open
  question. Three candidates, in the order to try them, each narrower and cheaper than the next is
  general: **(a)** the space's own `http.proxy` setting, which targets the gallery alone and needs no
  apply; **(b)** a lifecycle configuration writing the six variables where the app's entrypoint reads
  them; **(c)** `ContainerEnvironmentVariables` on a Code Editor-capable image configuration — 2.2's
  mechanism, reaching this app only once the house image is selectable there. Record **which one the
  gallery actually honours**: VS Code's request stack and its extension host do not read the environment
  the same way, and *"the variables are set"* is not the same claim as *"the gallery used them"*
  (Lesson 5).
- **8.5 — [user] Install one extension**, and paste the log. The success criterion is a **`200` in
  `/awsds/prod/proxy` naming `open-vsx.org`** — not merely an extension that appears, which a cached
  `.vsix` also produces.
- **8.6 — [Claude] Read the asset host, and the three names 8.2 already found.** Once 8.4 lands, every
  refusal **moves from a DNS `BLOCK` to a Squid `403`** — the space stops resolving and starts asking —
  and that is when the plane's list becomes the thing being measured. Expect at least three: the
  `.vsix` asset host if `open-vsx.org` redirects the download (a second name, exactly as `public.ecr.aws`
  → CloudFront was at 6c 5.8), plus **`idetoolkits.amazonwebservices.com`**, **`api.github.com`** and
  **`raw.githubusercontent.com`** from 8.2. **The last two are not covered by the plane's `github.com`**:
  that entry is a bare name, and Squid's `dstdomain` matches a bare name **exactly** — which is also why
  `codeload.github.com` was refused at 3.1. Each is a name to allow or a loss to record (decision due 6);
  add names, never namespaces.
- **8.7 — [user] Settle the one string this reading could not explain.** The failing requests asked for
  `targetPlatform=alpine-arm64`, while a JupyterLab space in the same estate fetched **`amd64`** Ubuntu
  packages an hour earlier. `uname -m` and `/etc/os-release` from the Code Editor's terminal cost nothing,
  and either make it a fact about the space or retire it as VS Code's own fallback. Carried as an
  **unexplained string, not a finding** (Lesson 38).

### 9. Take the build plane out of the allow-list business

**Action:** apply `production/networking/` with `production-foundation` in `open` mode and
`proxy_allow_shared` deleted. **Why:** the user, reading `hub-anchors.tf` after the day's measurements,
asked why a build host is restricted at all. **Explanation:** it is not what `objectives.md` restricts —
that is the SageMaker-**managed compute** — and the buildbox stands in for the CI/CD pipeline whose control
is the **reviewed Dockerfile in git**, not a hostname list. The list was also a treadmill: its one
hand-added entry, `d5l0dvt14r5h8.cloudfront.net`, carried a comment calling its own next revision *"a WHEN
rather than an IF"*. [D38](../decisions/D38-single-egress-hub.md) §6 is amended in place; this step is the
apply and the readings that prove it landed. **The slice is 6c's**; the step lives here because 6d is the
open stage and this is where the apply happens.

- **9.1 — [Claude] DONE 2026-09-08: the code.** `proxy_allow_shared` deleted with its CloudFront name;
  `proxy_deny_shared = []` in its place; a second map, `proxy_deny_by_plane`, whose membership **is** the
  plane's mode — so the merge no longer hard-codes `"allowlist"` and cannot contradict the lists. Two new
  preconditions: a plane in **both** maps fails at plan time, and the "plane no peering generates" check
  reads both key sets. `terraform plan`: **`0 to add, 1 to change, 0 to destroy`** — the SSM parameter,
  every precondition passing.
- **9.2 — [Claude] DONE 2026-09-08: the instrument, which the change would otherwise have made red.**
  `./aws/dns-allowlist.py` parses the `.tf` by an explicit grammar; it knew one plane map and hard-coded
  every plane as `allowlist`. It now reads both maps (both **required** — a missing deny map would make an
  `open` plane read as an allow-list with nothing on it, the exact inversion the parser exists to
  prevent). **`DN-4` was rewritten rather than relaxed**: from *"only the client plane is `open`"* to
  *"no plane is `open` except the ones a decision names"*, against an `OPEN_BY_DECISION` map whose values
  are the reasons, printed in the pass line. A **new** plane going open still fails (Lesson 50).
- **9.3 — DONE 2026-09-08, authorized in chat.** One apply for both steps: `aws_ssm_parameter
  .proxy_allowlist` **updated in place**, `Apply complete! Resources: 0 added, 1 changed, 0 destroyed`,
  and the re-plan `No changes`. *The original step follows:*
- **9.3 — [Claude⚡] ONE apply for steps 8 and 9.** Both edits are the same parameter in the same slice;
  applying twice is the mistake to avoid, and reading `PX-3` between them is the other. The plan is
  already taken.
- **9.4 — FIRST LINK DONE 2026-09-08; THE SECOND IS OWED.** `DN-3` went from the failure that
  *was* the diff to **`pass — 5 planes, entry for entry`**, with `DN-1`, `DN-2` and `DN-4` beside it —
  `DN-4` naming both open planes and their reasons. **Code and parameter agree.** `PX-3` is
  **`note — not answered`**: it needs `--on-host`, an `ssm:SendCommand`, so it is taken deliberately and
  is worth taking only after the State Manager half-hour has passed. `PX-1`, `PX-2` and `PX-5` pass on
  the committed file; `PX-4` its standing note. *The original step follows:*
- **9.4 — [Claude] Read that it landed, in two links.** `DN-3` (code → parameter) is **red today and
  names exactly these two changes** — `sandbox-foundation: only in code [open-vsx.org]`,
  `production-foundation: only deployed [the 20 names]`; it must be green after the apply. `PX-3`
  (parameter → the running `squid.conf`) goes green up to a **half hour later**, on the State Manager
  schedule, with **no host replacement**. A green `DN-3` and a red `PX-3` is the expected middle state,
  not a failure.
- **9.5 — [user] Exercise the plane where the old list was load-bearing.** Bring the buildbox up and run
  one full build and push. The name that must now work without being listed is the CloudFront distribution
  `public.ecr.aws` redirects blobs to — the entry this step deleted. A pull that fails with `Forbidden`
  here would mean the mode did not reach the host, not that a name is missing.
- **9.6 — [Claude reads, user decides] Whether the deny list stays empty.** It is empty by the same
  decision the tunnel's is: everything permitted, everything logged, and a list filled when there is a
  written policy to fill it from. An entry here would be a name a **build** may not fetch. Stage 11 owns
  the policy; this step records that nothing was written today.

## Deliverables

- The house image registered, selectable and pulled across the account boundary.
- A working session's friction list under the proxy, and the `NO_PROXY` contract proven by a CloudTrail
  reading.
- A Studio-authored workflow whose definition passes the promotion lint, with its run identity recorded,
  and the workers' network shape handed to Stage 10.
- Idle shutdown and `make down` both observed; the Studio layer table written; the hub precondition
  exercised.
- Ten verification rows answered, or explicitly re-homed with an owner.
- **The Code Editor's extension gallery working through the proxy, or the loss recorded** — with the
  mechanism that delivers the variables to a VS Code server **named**, not assumed.
- **The build plane `open` on the running host**, D38 §6's amendment carried through code, parameter and
  `squid.conf`, with one full build and push exercised across it.
- **The remote-IDE channel opened once from the laptop** — the endpoint set it needs under design B, the
  principal that calls `StartSession`, 6a step 3.2's two denies exercised, the 12-hour residual measured
  rather than restated, and the client half in a runbook the routing table points at.

## Validation

`./aws/studio.py` all-pass with one Interactive account; `US-10` zero running apps after `make down`;
`./aws/egress.py` showing no NAT and no default route while a session runs; `./aws/dns-allowlist.py`
`DN-3` **and** `DN-4` green and `./aws/proxy.py` `PX-3` green after the step 8 / step 9 apply, and after any
ACL entry step 3 or step 7 adds; the deny pair's two wordings in the log, and the remote-IDE
pair's two alongside them; one `sagemaker:StartSession` in CloudTrail carrying the proxy's Elastic IP **for the chosen method**, the
same call refused **by name** with the tunnel down, and `./aws/remote-ide.py` `RI-1`..`RI-5` green.

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
4. **Where the tag-scoped `StartSession` pair belongs — and, first, WHICH CONNECTION METHOD IS THE
   ESTATE'S, because the method decides the perimeter (re-framed 2026-09-07 from the vendor pages).**
   The SMUS guide names the **project role** as the principal that must hold `StartSession`, and says
   AWS's managed policy already grants it *"for the spaces they own"* — conditioned on the same two tags
   the estate's denies use, in **Allow** form, on the principal that makes the call. With the **deep
   link** the portal makes that call server-side as the project role: `DenyControlPlaneOffVpn` never sees
   it, the portal is reachable off-VPN (INT-16) and the data channel is a token-bearing WebSocket, so
   **that method is usable entirely off the VPN** — and on the VPN it is the one most likely to time out
   (7.1's environment catch). *Added 2026-09-08 (6c pass 8):* **under the split-tunnel profile that timeout
   disappears** — the browser-launched process dials `ssmmessages` on the laptop's own uplink, and the
   `StartSession` is the project role's, server-side — so Method 1 is expected to work with nothing
   configured; 7.5 reads it under both profiles before the method is chosen. With **SSH or the Toolkit** the laptop's own credentials call it, so the VPN
   statement applies — but the persona sets hold no Allow, and a persona session carries **no**
   `AmazonDataZoneProject` / `datazone:userId` principal tag, so `StringNotEquals` against an unresolvable
   variable is true for every space: **the pair would deny everything, not scope** — the guard
   `policies-sagemaker.tf`'s comment describes (*"a deny is what survives someone else granting it"*) is a
   kill-switch wearing a scoping's name. **No method is both VPN-bound and scoped today.** Recommended, if
   the objective's VPN-only is to be true of this channel: **Method 3** (the SSH `ProxyCommand` script)
   as the estate's method; a tag-scoped Allow on the persona sets keyed on something a persona session
   carries — the vendor's own ABAC example uses `IDC_UserName` via Identity Center *attributes for access
   control*, with the space tagged by hand at 7.3 — and the pair rewritten to the same key; and
   `sagemaker:StartSession` **denied on the D13 boundary**, which closes the deep link's project-role path.
   If the deep link is chosen instead, AWS's Allow conditions are the scoping, the estate's copy goes to
   the boundary as conditions, and Stage 11 records that the VPN-only sentence is **not true of this
   channel**. Choose after 7.4/7.5 have read each method's caller and address, not before.
5. **How the VS Code server reaches the space** (7.1 (c)): the client settings (recommended), the four
   Microsoft names on the compute plane, or the pre-packaged tarball by lifecycle configuration.
6. **Which compute-plane names step 3 adds** (3.1): every `403` the proxy logs is a name to allow or a loss
   to record — `conda` and CRAN are the two expected, and Julia/R are image-delivered by design.
   **PARTLY TAKEN 2026-09-08 (the user): `open-vsx.org` is allowed**, authored at 8.1 after a Code Editor
   space failed on its own startup — a gallery is the same class of path as `pypi.org`, which this plane
   already carries, so refusing it would not be a narrower perimeter but the same one with an ecosystem
   arbitrarily missing. **And its evidence was a DNS refusal, not a `403`**, which qualifies this
   decision's own instrument: a name missing from this plane can fail **without ever reaching the proxy's
   log**, so "every `403` the proxy logs" is a floor on the list of names to decide, never the whole of
   it. **`conda` and CRAN stay open**, and 8.2 added **three more candidates**:
   `idetoolkits.amazonwebservices.com`, `api.github.com`, `raw.githubusercontent.com`.
7. **Whether the build plane's deny list stays empty** (9.6). Empty by decision today; Stage 11 owns the
   policy that would fill it.

## Verifications to answer while executing

The ten rows of 6.1, plus: does the registered image survive a blueprint reconciliation (2.4); does the
workflow surface exist without a blueprint change (4.1); **which principal calls `sagemaker:StartSession` (7.2 — the method decides it, 7.5 reads it),
~~which endpoints the remote channel needs under design B (7.1)~~ (answered 2026-09-07: none to add), and
whether a remote session outlives the tunnel and the portal logout (7.7)**.

## Risks

- **The workflow surface is not enabled by anything we control**, which moves 4.1's answer into a blueprint
  change and re-opens 6a's decision 5. Recorded as that step's own alternative.
- **A component with no proxy support inside the image** (3.4). The fallback is an endpoint, then D38's
  per-VPC NAT contingency — in that order, and never a default route. **Measured once, 2026-09-08**: the
  Code Editor's extension gallery, and the cause was not *"no proxy support"* but **no proxy in the
  process**, which is a different repair and a cheaper one — step 8. The risk stands for the components
  3.4 still lists; what this instance revises is the diagnosis order, which now begins with *does that
  process have the variables at all*.
- **The VS Code client or its toolkit may not honour the proxy** (7.5) — 3.4's risk on the laptop. Read
  from source 2026-09-07: the Session Manager plugin honours `HTTPS_PROXY` **when it reaches its process**,
  so the risk is now *where the variable is set* (a browser-launched VS Code has none), not whether it is
  read; and there is no endpoint to fall back to on that side of the tunnel.
- **The scoping may never have applied** (7.2). If the project role is the caller, 6a step 3.2 has been
  attached to the wrong principal since the day it was applied — a control believed to exist, which is worse
  than a known gap, and the reason this step reads the caller before it reads anything else about the
  refusals.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
