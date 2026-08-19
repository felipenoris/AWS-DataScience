# Log — Stage 6 — SageMaker Unified Studio

*Manual actions performed in AWS, by hand. Written cooperatively by the user and Claude — **Claude
only when the user asks, never on its own initiative** ([`INDEX.md`](INDEX.md), which also carries the
provenance rule). **An entry carrying no provenance note of its own is the user's.**
Stage: [`docs/plan/stages/stage-06-unified-studio.md`](../plan/stages/stage-06-unified-studio.md).*

*Provenance is named by SUBJECT rather than by ordinal — the convention
[Stage 3's log](log-stage-03-networking.md) adopted and every stage since has kept. Identifiers are
redacted as `scripts/check-identifiers.py` requires, with the substitutions declared once per entry.*

*File initialized 2026-08-19 on the user's request. **The stage has not opened**: it is initialized early
because three of its five execute-time decisions were settled before it (3, 4 and 5), and the stage file
says those decisions are recorded here (Lesson 16). **The three entries below are all doc-and-decision
sittings, not build sittings** — the third is the only one that touched AWS at all, and only to read.*

---

## 2026-08-19 — Decision 3 closed before the stage, and the announcement that looked like it retired it

*Provenance: **this entry is Claude's**, written on the user's request in the same sitting. **No AWS call
of any kind was made — not a write, not a read.** Every source below is AWS *documentation*, fetched from
the public web and cited in [`docs/REFERENCES.md`](../REFERENCES.md); everything else is repository edits.
Where this entry says "measured", it means measured against a document, never against the account — the
distinction matters more here than in any earlier stage log, because a documentation reading is exactly the
kind of evidence that ages.*

**Nothing was built, applied, attached or probed.** Stage 5 was mid-flight in a parallel session throughout;
this sitting touched none of its files.

### Why the sitting happened: which Stage 6 decision could be pulled forward

The user asked whether any decision blocks Stages 5 and 6, and then which of Stage 6's could be settled
early. Both stage files answer the first question the same way — *"Blocking questions for the user: none"* —
so the useful answer was the second, and it came out as three of the five:

| Decision | Verdict on pulling it forward |
|---|---|
| 3 — the Athena Spark disable set | **Yes, and with a concrete gain**: Stage 5 step 4.3 already owes a phase-4b amendment, so both could share one battery sitting |
| 1 — the Spark runtime | **Yes**: prices already measured, and the answer feeds the endpoint lists Claude authors |
| 5 — the blueprints left off | **Yes**: no measurement in it, a restatement of D7/D28 and Lesson 6 |
| 2 — TIP | **No**: its input is Stage 5's verification (viii) map, authored in that stage's pass 2 |
| 4 — the Lakehouse blueprint | **No gain**: a minimal default, one resource to add later |

The user chose to take decision 3 first, and asked for its context before deciding — which is what turned
this sitting from a decision into a documentation pass.

### The re-read, and four things the 2026-08-16 reading had slightly wrong

Before presenting the decision, Claude re-read AWS's *Network isolation in SageMaker Unified Studio* page in
full rather than trusting the summary carried in the plan since 2026-08-16. **The plan's characterisation
held — the SCP is the only one of the three documented controls that is preventive and spares Athena
SQL — but four details were sharper than recorded**, and all four are now in the stage file:

1. **AWS ships the statement itself**: `Sid` `DenyAthenaSparkStartSession`, actions
   `athena:StartSession` + `athena:UpdateSession`, `Resource` `arn:aws:athena:*:*:workgroup/*`, with the
   page explicitly permitting a narrower Region/account/workgroup scope.
2. **The Tooling blueprint's Athena flag is worse than "blunt"**: AWS's own wording is that it prevents
   Athena SQL *and* Athena Spark from being provisioned **in new projects** — so it is also **not
   retroactive**. Two reasons to leave it on, where the plan had one.
3. **The third documented control is not the permissions boundary the plan assumed.** It is *"remove
   Amazon Athena Spark permissions from individual project IAM policies"* — a **grant**-shaped edit on
   **blueprint-authored** policies, i.e. Lesson 11's trap and INT-15's reconciliation risk. Step 2.1's
   boundary is a deny-shaped ceiling from a slice this repository owns: **stronger than the documentation,
   and therefore a deviation to record rather than a copy to claim.**
4. **`DenyUserAccessFromUnauthorizedVPCs` carries three conditions, not two.** The missing one is
   `StringLike aws:userid = *:user-*`, and it is the load-bearing one: it confines the deny to portal
   users and spares the catalog service running on the same role. **The on-behalf carve-out INT-16's
   fallback (i) wanted proven is already in AWS's shape**, and its mechanism is the `userid` form rather
   than `aws:ViaAWSService` alone. Propagated to [`integrations.md`](../plan/integrations.md)'s INT-16 row.

**Two findings arrived that belong to other decisions**, and are recorded where they land rather than here:
the required-endpoint table is materially longer than the four-name sample the plan carried (and pairs `q`
with a **`us-east-1`-only** `codewhisperer` endpoint that a `us-west-2` VPC cannot reach through an
interface endpoint at all — step 4.2), and the optional table asks for **four** endpoints for EMR Serverless
against **one** for Glue interactive sessions. That second one **reopened decision 1**: the recommendation
had compared compute and never saw an idle line of order USD 0.12/h running 24×7.

### The user's challenge: the 2026-04 PrivateLink release

The user then produced [the announcement of 2026-04-21](https://aws.amazon.com/about-aws/whats-new/2026/04/amazon-athena-spark-aws-privatelink/) —
*Amazon Athena Spark adds support for AWS PrivateLink* — and asked whether it had already solved the
problem. **It had not, and establishing why is the most useful thing in this entry**, because the headline
is exactly what will re-open the question later:

- **What the release moves is the client → session path**: Spark Connect (gRPC submission), the Live UI and
  the Spark History Server, reachable through three new interface endpoints on Spark 3.5 workgroups.
- **What it does not move is where the session runs.** There is no `NetworkConfiguration` — no subnet, no
  security group — anywhere in the Athena Spark API. Confirmed twice, independently: the *considerations and
  limitations* page mentions VPC at no release version, and the SMUS network-isolation page, **current after
  the release**, still answers VPC connectivity with *"use Amazon EMR or AWS Glue instead"*. The two pages
  are not in conflict; they describe different halves.
- **The executor therefore stays outside the VPC**, which is the whole of open question 12 — outside the
  endpoint policies, the flow logs and every `aws:SourceVpce` condition.

**Two details on the feature's own page argue for the deny rather than against it**, and both were new to
the plan: **VPC endpoint policies are not supported** on the three session endpoints (the documented
workaround is to police `GetSessionEndpoint`/`GetResourceDashboard` on the Athena **API** endpoint instead —
an indirection, in allow shape), and **a session URL minted inside the VPC is reachable from the public
internet by design**, carrying plans, schema and stage detail and persisting in the History Server.

### The question that closed the last open item, and the answer worth keeping

The user's remaining doubt was whether declining the three `athena.*` session endpoints could damage Athena
**SQL**, which D13 depends on. **It cannot, and the naming is what invites the fear:** the SQL path rides
`com.amazonaws.<region>.athena`, the **API** endpoint, which the same page lists as **required** and which
this design creates; the three declined ones are Spark session surfaces and nothing else. **One shared edge
exists and is worth knowing**: `GetSessionEndpoint` and `GetResourceDashboard` — the calls that *mint*
session URLs — travel over that same required `athena` API endpoint, which is also the only Athena endpoint
that accepts a VPC endpoint policy. It is the one place the two paths meet.

### Decision 3 — taken in full, 2026-08-19, by the user

**Reformulated first.** The re-read closed two of the three questions Claude had originally posed, and it
was worth saying so rather than presenting settled things as choices: **the Tooling flag stays on** and
**the SCP is the mechanism** stopped being decisions once the evidence was in, and the `Resource` stays at
AWS's wildcard because narrowing it to `us-west-2` would *permit* Spark elsewhere. What genuinely remained
was three smaller things, and the user took them in order:

1. **Timing — not pulled forward.** The amendment and its probes stay at step 1.6, run when the stage
   opens. The gain of sharing Stage 5's phase-4b sitting did not outweigh inheriting 4.3's scheduling
   constraint, and there is no surface to protect until this stage builds one.
2. **The boundary gets no Athena Spark clause** (the recommendation adopted). An OU SCP reaches every IAM
   principal in the member accounts, project roles included — the only exemption is service-linked roles,
   and no SLR opens a Spark session — so the clause would deny nothing the SCP does not, and **Lesson 20
   turns that from redundancy into cost**: where two policies deny one call, only one is ever proven and
   the other reads as coverage. Revision trigger: the first principal an OU SCP does not reach.
3. **The endpoint abstention is written, not tacit** (the recommendation adopted, after the SQL question
   above was settled). A commented exclusion beside `extra_services` in `sandbox/egress/main.tf` and
   `development/egress/main.tf`, plus step 4.1's instruction to keep the Spark session domains **off** the
   DNS Firewall allow-list — where default-deny already excludes them, so what is added is the *"do not
   add"*, for whoever is one day debugging a blocked lookup. Lesson 5, at the cost of two comment blocks
   that change no plan (`terraform fmt -check` clean on both).

**And the revision trigger for the deny itself, worded so that a press release cannot fire it:** Athena
Spark gaining an equivalent of `NetworkConfiguration` — **executors in our subnets, under our security
group**. *Not* "Athena Spark supports VPC", which the April headline already says and which is about the
control path. It travels into `POLICIES.md` with the statement.

### What this sitting owes the stage

- **`POLICIES.md` has no row yet, and correctly so** — no policy changed. The row is written in the sitting
  that writes the statement, at 1.6, and step 1.6 carries the three things it must say: the deviation from
  the documented third control, why the `Resource` stays a wildcard, and the revision trigger.
- **The probes are 1.6's**: the positive (`athena:StartSession` denied naming the policy, from a persona
  session in Development or Sandbox) and — the one that matters — **the negative**
  (`athena:StartQueryExecution` still succeeding in the same account, or the amendment took D13 with it).
- **Decision 1 is now reopened rather than merely undecided**, and must be settled with the endpoint-count
  number in hand.

### Files touched in this sitting

[`docs/REFERENCES.md`](../REFERENCES.md) (the network-isolation entry corrected; a new entry for the
PrivateLink release with its two documentation pages, written as *why it does not retire decision 3*),
[`stage-06-unified-studio.md`](../plan/stages/stage-06-unified-studio.md) (steps 1.6, 1.7, 4.1, 4.2,
decisions 1 and 3, the Status row), [`open-questions.md`](../plan/open-questions.md) item 12,
[`integrations.md`](../plan/integrations.md) INT-16, both Interactive `egress/main.tf` files, `CLAUDE.md`,
and this file. **`make check` green throughout; `make check-docs` red only on its pre-existing pre-Stage-2
prose and the `CLAUDE.md` size budget — nothing new.** Nothing committed by Claude.

---

## 2026-08-19 — Decisions 4 and 5 closed before the stage: the blueprint allow-list, and the re-read that inverted a recommendation

*Provenance: **this entry is Claude's**, written on the user's request in the same sitting. **The
decisions are the user's**, taken in chat over context Claude assembled; **no AWS call of any kind was
made — not a write, not a read.** The one piece of evidence is a fresh fetch of the *Supported
blueprints* admin-guide page ([`docs/REFERENCES.md`](../REFERENCES.md) carries the annotated entry);
everything else is repository edits. The same ageing caveat as the previous entry applies: measured here
means measured against a document.*

**Nothing was built, applied, attached or probed.**

### Why the sitting happened

Preparing decision 5's context, the *Supported blueprints* page was re-read — this time for its
per-blueprint **Resources created** column, which the 2026-08-16 pass had used only for the names. Two
facts came out of that column; the first is a correction.

### The finding that decided decision 4

The page says `LakehouseCatalog` *"provisions a new catalog in the Amazon SageMaker Lakehouse that is
backed by Amazon Redshift Managed Storage"* — while the Glue/Athena project surface (Glue databases,
Lake Formation permissions, an Athena workgroup, the shape that lands on Stage 5's substrate) is
**`LakeHouseDatabase`, API name `DataLake`**. The plan had the two inverted: D26 wrote "Lakehouse
Catalog in its Glue/Athena form" and decision 4's recommendation was to start with `LakehouseCatalog`
alone. Lesson 16's shape — the name said one thing, the field list another; nobody had read the second
column until a user question ("what is the difference between the two?") forced it.

**Decision 4, the user's: `DataLake` alone. `LakehouseCatalog` is disabled** — filed in decision 5's
category 3, beside its storage sibling `RedshiftServerless`, whose D12 argument (a second, larger query
bill on top of Athena's) reaches it.

The second fact, recorded in passing: the `Workflows` blueprint *provides the CloudFormation template*
for the MWAA environment — the fee-bearing environment is born when a **project first uses** the
blueprint, not when it is enabled. Three states, and the billing starts at the third.

### Decision 5, the user's: three categories, every blueprint owned

Taken as an **allow-list, not a deny-list** — the sitting's starting observation was that the
recommendation named three exclusions and left `EMRonEC2`, `PartnerApps` and `Quicksight` owned by
nobody. The user's distribution:

- **Category 1 — enabled by default** (the step 1.4 map, and `US-3`'s allow-list): `Tooling`,
  `DataLake`, `EMRServerless` — **following reopened decision 1's outcome** — and
  `AmazonBedrockGenerativeAI`, all per-use. Bedrock's `PRICING.md` row is **owed before the 1.4 apply**
  (Lesson 6), and its runtime endpoints join 4.2's measurement.
- **Category 2 — on demand**: authorized, outside the map until a **named trigger** fires, then commit +
  apply (price measured at that moment where the table lacks one). `Workflows` OnDemand — trigger:
  **D28's last-rung fallback**, INT-14's chain falling through at Stage 10, and then `[E]`;
  `MLExperiments` — trigger: experiment tracking concretely needed, the MLflow tracking server being a
  standing resource with no idle shutdown.
- **Category 3 — disabled**: enabling **amends decision 5**, price first. `EMRonEC2`, `PartnerApps`,
  `Quicksight`, and `LakehouseCatalog` per decision 4. `RedshiftServerless` stays a **never** — enabling
  it reopens D26/D12, not this decision.

The mechanism, stated once in [`docs/SMUS.md`](../SMUS.md) (created this sitting as the descriptive
reference, with a `CLAUDE.md` routing row so it is re-read whenever the SageMaker surface changes): the
`US-3` allow-list holds category 1; a category-2 blueprint joins the constant **in the same commit**
that adds it to the step 1.4 map (Lesson 14). No preventive form exists — no IAM condition key names
*which* blueprint a call enables — so enforcement is authoring plus the reading (Lesson 22), on top of
the 1c fence around who can call `datazone` at all.

### Files touched in this sitting

[`stage-06-unified-studio.md`](../plan/stages/stage-06-unified-studio.md) (step 1.4's enabled set
rewritten against the categories; decision rows 4 and 5), [`docs/SMUS.md`](../SMUS.md) (created, then
corrected for the inversion), [`aws/studio.py`](../../aws/studio.py) (`US-3` tightened from
Redshift-absence to the category-1 allow-list, `AmazonBedrock*` prefix rule for the seven
sub-blueprints; `ruff` clean), [`docs/REFERENCES.md`](../REFERENCES.md) (the *Supported blueprints*
entry annotated with the re-read), `CLAUDE.md` (the routing row and the position bullet), this file,
and [`INDEX.md`](INDEX.md). `./scripts/check-identifiers.py` OK. Nothing committed by Claude.

---

## 2026-08-19 — Decision 1's reopening, re-read: the number corrected, and the axis neither weighing saw

*Provenance: **this entry is Claude's**, written on the user's request in the same sitting. **Unlike the
two entries above, this sitting did make AWS calls — two, and both are reads**: `sts get-caller-identity`
(the check the rules require before any `aws` command) and `ec2 describe-vpc-endpoint-services` in
`us-west-2`, as the **infrastructure user** on **Sandbox** through `InfrastructureAccess`. **Nothing was
created, changed, attached or probed**, and no Terraform ran. Everything else is AWS documentation fetched
from the public web — cited in [`docs/REFERENCES.md`](../REFERENCES.md) — plus repository edits. The
ageing caveat of the two entries above still applies to the documentary half; the one paragraph below
marked *measured against the account* does not carry it.*

### Why the sitting happened

The user had closed decisions 3, 4 and 5 in a parallel session and asked Claude to re-read the repository
and say whether the framing it had given earlier still held. **It did not, in one place.** Decision 1's
reopening is right that the compute comparison missed a cost — and **wrong about how much**, in a way that
was inherited rather than invented: it priced the endpoints at AWS's recommendation instead of at this
project's applied rule.

### What was measured against the account — the only claim here that is not a document

`aws ec2 describe-vpc-endpoint-services`, filtered on `emr`/`glue`/`datazone`, returns in `us-west-2`:
`emr-serverless`, `emr-serverless-services.livy`, `emr-serverless-services.sessions`,
`emr-serverless.dashboard` and `emr-dashboard`; `glue`, `glue.sessions`, `glue-fips`, `glue.dashboard`,
`glue-studio-sparkui-service`; `datazone` and `datazone-fips`. **What this establishes is small and worth
having**: the names in the admin guide's optional table are real service names in this Region, so neither
side of decision 1 rests on a documentation artifact, and `glue.sessions` is genuinely a *second* endpoint
beside the `glue` the required list already carries. **What it does not establish is which of them a
session actually needs** — no API answers that, which is why step 4.2's rule is *measure from the flow
logs, do not copy the table*, and why it is one of the two readings this decision now ends in.

### The correction: two errors, pointing the same way

1. **It priced two AZs.** Two is AWS's high-availability recommendation on the network-isolation page, and
   it is exactly what **Stage 3 step 8.5 declined in writing** (D9 — *"two AZs doubles the largest hourly
   line item, and a resource in the other AZ still resolves and reaches it"*); the 33 interface endpoints
   of that stage were applied, measured and torn down **single-AZ**. Under the rule this project actually
   applies, the delta is three endpoints × USD 0.010/h × two Interactive accounts ≈ **USD 0.06/h** — half
   of the row's figure.
2. **It called the line 24×7.** The interface endpoints live in `egress/`, which is **`[E]`**: under the
   D11 discipline they exist only while the slices are up, and `make down` takes them to zero — Stage 3
   measured exactly that (USD 0.0000/h after teardown). **The always-on reading is not a rate; it is a
   teardown-discipline failure** — and it is kept as a named risk rather than deleted, because the failure
   has a precedent in this project (Stage 4 left its host `running`) and D12's budget notifies nobody.

### The symmetry that makes this a pattern rather than an erratum

**The original recommendation weighed only per-use compute metering and missed a standing line. The
reopening weighed only the standing endpoint line and missed that the compute side has a standing tail of
its own.** Both halves of that second sentence are documented:

- A **started** EMR Serverless interactive application maintains **one pre-initialized kernel worker of
  4 vCPU/16 GB** — *"even if you don't specify any pre-initialized capacity for drivers"* — ≈ USD 0.30/h
  at the x86 rate. It is bounded by `autoStopConfig` at 30 minutes of application idle, but the **kernel
  idle timeout is 60 minutes and cannot be modified**. The SMUS Spark Connect path adds a pre-initialized
  1 driver + 3 executors, released after 15 minutes idle.
- Glue's floor is not the 1-DPU minimum the recommendation cited: *"An Interactive Session has 5 DPU by
  default"* — ≈ **USD 2.20/h** while a session is open, at the measured 0.44/DPU-h.

Each reading corrected its predecessor's blind spot and introduced one of its own. **The third does not get
to claim it broke the pattern**, which is why decision 1 now ends in *readings* rather than in a number.

### The axis neither weighing saw: fine-grained access control

Preparing the context turned up something that outranks both cost readings and had not appeared in either:

- On the notebook's **Spark Connect** path, the SMUS user guide states the same limitation for **all three
  engines** — AWS Glue, EMR Serverless and EMR on EC2 alike: *"Fine-grained access control (FGAC) is not
  supported. Only full-table access is available"*, with trusted identity propagation unsupported beside
  it. EMR Serverless on that path is documented as **compatibility mode only**.
- At the **compute-connection** level the two permission modes are `project.spark.compatibility` and
  **`project.spark.fineGrained`**. The EMR Serverless *Add compute* dialog offers both, and the notebook
  connects to that compute through the PySpark connection type; **Glue's `fineGrained` is documented for
  Visual ETL flows**, not for the notebook.

**So the only documented route by which a notebook Spark session inherits Lake Formation column and row
filtering is an EMR Serverless compute connection in `fineGrained` mode** (EMR ≥ 7.2.0;
`spark.emr-serverless.lakeformation.enabled`, and AWS suggests ≥ 28 vCPU of quota against 24 without it).
That reaches D13 and the `restricted` column Stage 5 built precisely to prove classification scoping: **if
decision 1 lands on Glue, column scoping lives on the Athena SQL path alone, and that is a scope statement
to write down rather than a gap to discover.**

**Why this became a reading and not the decision.** The two pages emphasise different paths and neither
of us has seen the surface; a product claim assembled by reconciling two documentation pages is exactly the
evidence class the first entry in this file flagged as ageing. **It is also, on its face, an argument
*for* EMR Serverless — the opposite direction from the reopening** — which is one more reason to measure
it rather than to adopt it: a finding that reverses the current lean is the one most worth testing.

**One thing it settles rather than opens**, and it travels to decision 2: with TIP unsupported on every
notebook Spark path, the TIP lever is a **SQL/query-path** lever only. Recorded in
[`open-questions.md`](../plan/open-questions.md) item 13; decision 2 is unchanged in substance and better
supported.

### What decision 1 now needs, stated so the stage cannot skip it

Not one number. **Two readings, both at the start of the stage:**

1. **Which of the four EMR Serverless endpoints a working session actually exercises** — step 4.2's flow
   logs, under design A first. The corrected USD 0.06/h is a ceiling, not a measurement.
2. **Whether a `fineGrained` EMR Serverless compute connection is actually usable from an IdC-domain
   notebook** — the FGAC axis above, which no document answers unambiguously.

**And the propagation is already written**, so neither outcome leaves a stale cell: decision 5's category 1
lists `EMRServerless` as *following decision 1*. Landing on Glue removes it from `US-3`'s allow-list,
[`docs/SMUS.md`](../SMUS.md) and the step 1.4 map **in one commit** (Lesson 14) — and needs no blueprint at
all, since Glue arrives as a project connection.

### Files touched in this sitting

[`stage-06-unified-studio.md`](../plan/stages/stage-06-unified-studio.md) (decision 1's row and the Status
row), [`stages/INDEX.md`](../plan/stages/INDEX.md), [`docs/SMUS.md`](../SMUS.md) (the `EMRServerless` row —
the corrected number, the FGAC note, and *"pre-initialized capacity not used"* rewritten: the service keeps
a kernel worker regardless), [`open-questions.md`](../plan/open-questions.md) item 13,
[`docs/REFERENCES.md`](../REFERENCES.md) (a new 2026-08-19 Spark-runtime block with its four pages),
`CLAUDE.md`, this file and [`INDEX.md`](INDEX.md).

**Two housekeeping notes rather than findings.** The *Account pools* sub-bullet in `REFERENCES.md` had been
left hanging under the PrivateLink entry instead of the 2026-08-16 documentation-pass block it belongs to;
re-homed. And `check-plan-refs.py` flagged a **new** hit that was a false positive of its own bluntness —
`STALE_SECTION_RE` is `\brows? \d+`, so the phrase *"decision row 1"* reads as a stale row reference; the
sentence was reworded rather than the rule loosened, which is the right way round for a check that exists
to be blunt.

**`make check` green. `make check-docs` red only where it already was** — the pre-Stage-2 prose in
`stage-03-networking.md` and the `CLAUDE.md` size budget, which this sitting pushed further over (31.9 KB
against 20); **the re-trim is owed at the stage's close**, as the file's own budget note says. Nothing
committed by Claude.
