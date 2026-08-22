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

## 2026-08-20 — The stage re-read against Stage 5 as CLOSED: nine defects, one of them a probe that could have built the thing the stage forbids

*Provenance: **Claude's hand throughout, on the user's request in this sitting**; no AWS write, and the
only AWS calls are the read-only `./aws/studio.py` before-reading and CLI `help` output. **One decision in
here is the user's** — the instruction to run the step 0 probes, recorded in the next entry with what they
returned. No identifier substitutions were needed: nothing in this sitting produced an account id.*

Stage 5 closed completely earlier today. This stage's prose was written 2026-08-16/19, so parts of it
describe a world that no longer exists — and the interesting finding is that **staleness was the smaller
half**. The larger half is two places where the plan, as written, could not have been executed at all, and
one where executing it exactly would have created the object the stage exists to forbid.

### Method, and the part of it that was wrong first

Five reading lenses over the stage against Stage 5's outcomes, each finding then handed to an adversarial
verifier told to **refute** it and to default to refuted when uncertain. **23 candidate defects, 9
survived, 14 refuted.** The refutations are kept below rather than discarded: several were right for
reasons worth not re-deriving.

**The first pass capped verification at the top 8 and left 15 unread** — a cap that was written into the
harness deliberately and then reported by it, which is the only reason it was caught. The sweep was re-run
without the cap before anything was applied. A capped audit that reports its own cap is recoverable; one
that does not is indistinguishable from a complete one.

### Two defects that make the stage un-executable as written

**The pass table sent step 1.6 to a slice that cannot do the work.** 1.6's own body says the Athena Spark
deny lands in `awsds-org-scp-ou-interactive` through battery phase 4b — an Organizations document, in
`terraform-live/identity/org-policies/`, appliable from **Identity** alone (`INV-15`). The table filed the
whole of step 1 under `data-governance/governance/` with `awsds-infra-data`, which cannot update an
organization policy at all. **Lesson 35 in its exact shape**, and the same trap Stage 5's 4e hit at the
keyboard. Now its own row, and the build table gained the slice it never listed.

**Step 2.6 prescribed widening the wrong variable.** It said to widen `consumer-data`'s
`data_scientist_role_arn` to a list. Read in the module: that variable is the **single-string `principal`
of three `aws_lakeformation_permissions`** and the `Principal` of the key policy. So the instruction is
either a plan-time failure, or — if a future reader "fixes" the type — a silent fan-out of the persona's
`DESCRIBE`/`SELECT` re-grants over the project roles, a Lake Formation grant this stage never takes and no
row of the register carries. **A data grant wearing the costume of a refactor.** It is a new list input now.

### The premise that was false, and the fourth destination it was hiding

Decision 6's recommendation rested on *"each project brings its OWN Athena workgroup, so the
one-workgroup-one-location ceiling dissolves"*. It does not dissolve: a blueprint-provisioned workgroup
writes into the **project path**, not into `awsds-<env>-derived`. The unsound half was load-bearing — it
was what made "Stage 11's scope is unchanged" sound true. With it removed, the project path is a **fourth**
designed destination, owed the three things the derived zone already has: a row under `docs/GOVERNANCE.md`
§Encryption, an expiry, and a place in Stage 11's Macie/data-event scope, which `consumer-data/buckets.tf`
declares precisely because Stage 11 cannot discover it. **That is the second, undesigned copy zone Stage 5
step 8's enforced output location was written to prevent, arriving by a different hand.**

**And the error that made it hard to see was in `docs/SMUS.md`, the one copy of the object model:** its
"Three buckets in a member account" table listed `awsds-<env>-athena` as a bucket. Read in the module,
`athena.tf` creates a **workgroup** by that name and `buckets.tf` creates exactly **one** bucket — so the
enforced results already live inside the derived zone, and there was never a third bucket. Corrected there,
where the fact is owned, rather than in the stage that points at it.

### The probe that could have built what the stage forbids

Step 0.2 said to run `datazone create-domain` *"from any account outside the `Data` OU (e.g.
`awsds-infra-dev`)"*. `create-domain` is creation-shaped and has no `--dry-run`, and
[`aws/probes/README.md`](../../aws/probes/README.md)'s `safety` rule refuses exactly that outside
`Policy Canary`. **The failure mode is not abstract: if the deny does not fire — which is the whole thing
the probe is testing — the probe has created a DataZone V2 domain in Development**, the second interactive
entry point D26 exists to forbid, with its own blueprints and project roles. A probe whose *negative*
result builds the forbidden object. Moved to the canary, where the same accident is disposable.

**Three more things step 0 gained, all of them so a failure is not misread as the SCP:** four pre-checks
against the live organization (the RCP's `PrincipalIsAWSService` exclusion, the `Data` OU document's three
statements naming no `iam:`/`datazone:`/`sts:` action, tag enforcement covering `ec2:RunInstances` only,
and the managed policy's real ARN under `service-role/`); a **real** throwaway execution role, because
DataZone validates before authorizing and a fake ARN measures nothing; and a **V1 fallback** with the
argument that licenses it — both condition keys of the statement are version-independent, so the
authorization decision is identical and only the validation ahead of it is lighter.

**The same misreading was live in the SCP battery.** Its row 6 read *"any validation error about the role
= **allowed**"* — a conclusion — while `POLICIES.md` said the identical outcome *"measures nothing"*. The
second is right, and the first is **Lesson 24 in reverse**: a result that cannot be attributed from its own
text does not become attributable through a better reading. Row 6 corrected, with the real-role recipe and
the V1 ladder.

### Two readings the stage demanded and never recorded

Verification **(xviii)** — where the project S3 path lands, by whose hand, and **under which key**;
`docs/SMUS.md` §S3 books that reading onto step 2.4 by name, the step named two questions and no bucket,
and the encryption key was in neither list. Verification **(xix)** — which `aws:SourceVpce` an S3 call from
a project subnet actually presents; Stage 5 pass 4d routed that measurement to "Stage 6 step 4.2" by name,
4.2 framed its whole reading as a cost question, and **the instrument it named cannot answer it**: gateway
traffic crosses no ENI, so flow logs are silent and the field is CloudTrail's `vpcEndpointId`. Both
amendments they may force are now budgeted in the build table; verification (viii) was narrowed so a reader
cannot believe the flow-log reading discharged either.

### What was deliberately NOT changed

**`INT-05` keeps its stage column, and `docs/AWS_STATE.md` gains no row.** Adding Stage 6 to either now
would assert as settled the very thing verification (xix) exists to decide. They are joined in the sitting
the measurement returns, with the measured id in hand.

**No Security Hub or AWS Config row in the Cost table.** Stage 5 pass 6 turned Security Hub CSPM on
org-wide today, so every resource this stage creates is now evaluated against FSBP — but `docs/PRICING.md`
and `cost-model.md` own the rate, Stage 5 step 13 already routes the re-read to **Stage 12** and the
trial-expiry reading to **Stage 11 step 4**, and this stage creates neither resource and holds no lever
over either. Lesson 34 is satisfied at both ends already; a row here would be a third copy.

**Decision 3's register entry keeps its superseded recommendation.** The revocation is thirteen lines
below it in bold, which is the register's shape — decision 4 preserves its own the same way. A third
in-file copy of "no boundary mirror (Lesson 20)" would have been the defect.

**Nine other refutations**, kept so they are not re-raised: no `identity/sso/` widening is entailed by
family-first (`…/results/*` already covers `results/<project>/`, and the runtime principal in a project is
the project role, not the persona — open question 13); `athena_workgroup_arns` is enumerated from
`consumer_data` remote state by design and a blueprint workgroup exists in no state it reads; step 0.4 is
about `sagemaker:Create*`, which 4e never touched; the three separate claims that 2.1 widens the drop-box
writer set without receiving `EXC-02`/OQ 19 are already answered by line 345's pointer to
`docs/GOVERNANCE.md` §Drop-box; and copying `docs/SMUS.md`'s gateway/interface reasoning into 4.2 would
have been the defect rather than the fix — **that last refutation was correcting the instruction given to
the audit, not the file under audit.**

### Paperwork

`docs/plan/open-questions.md` item 19 gained its **addressee** — Stage 6 step 2.1 is the first consumer of
the crawler question, so it is read *before* that grant, not after; the question had been recorded only at
the end that raised it (Lesson 34). The stage's Prerequisites row stops asserting a clean inheritance from
Stage 5 and names that residue. `docs/SMUS.md` §S3 item 1 gained the encryption-key field at the deferring
end, so both ends list the same fields.

**Before-reading, `./aws/studio.py`, taken this sitting:** `US-1` no unified domain in Data Governance;
`US-2` no SageMaker domain there either (the registry/runtime split holding, D26); `US-6` `datazone` reads
denied in Production (D28's headless control holding); `US-9` both deny statements absent from all six
persona sets. All four expected before this stage runs. The `FAILED` rows in section 10 are persona
`sso-session`s with no login, not findings.

`make check` green. `check-docs` red only on the three pre-existing pre-Stage-2 lines. Nothing committed.

## 2026-08-20 — Step 0 RAN and did not close: four variants, two accounts, one identical string — the contrast came out flat

*Provenance: **Claude's hand, on the user's explicit instruction in this sitting** — "pode rodar os
probes". **The stage assigns step 0 to the user** ("the step 0 probes (they write)"), so this is an
authorized deviation for one sitting and not a change to the split; the stage file still reads **user**.
These were WRITE calls: three IAM roles created and deleted, four `datazone create-domain` attempts.
Account ids are redacted as `<Data Governance>` and `<Policy Canary>`, declared once here.*

### What ran

Sessions confirmed first: `awsds-infra-data` reaches **Data Governance** through `InfrastructureAccess`,
`awsds-policy-canary` reaches **Policy Canary** through `AWSAdministratorAccess` — worth recording because
the second is *broader* than the first, and it removes "the canary lacked a permission" from the table of
explanations later.

A throwaway execution role was created in each account — trust on `datazone.amazonaws.com` for
`sts:AssumeRole`+`sts:TagSession`, `arn:aws:iam::aws:policy/service-role/AmazonDataZoneDomainExecutionRolePolicy`
attached — and `datazone create-domain` called against it. **Four variants, and every one returned the
byte-identical string:**

```
An error occurred (AccessDeniedException) when calling the CreateDomain operation:
Cross-account pass role is not allowed.
```

| Variant | Account | Result |
|---|---|---|
| `awsds-datazone-probe`, trust with `aws:SourceAccount`, `--domain-version V2` | `<Data Governance>` | the string above |
| same, retried after IAM propagation | `<Data Governance>` | the string above |
| same role, trust condition **removed**, V2 | `<Data Governance>` | the string above |
| same role, `--domain-version V1` | `<Data Governance>` | the string above |
| `awsds-datazone-probe`, V2 | `<Policy Canary>` | the string above |
| `AmazonDataZoneDomainExecutionRole` — the **conventional** name — V2 | `<Policy Canary>` | the string above |

Before each attempt the caller's account and the role's account were compared programmatically and
**proved equal**. `InfrastructureAccess` carries `AdministratorAccess`, and the `create-role` and
`attach-role-policy` calls that preceded the probe both succeeded, so no `iam:PassRole` deny is available
to explain it either.

### The finding, and it is a negative one

**The contrast came out FLAT.** The account the deny is written to miss and the account it is written to
catch answer with the same string, so **neither call reached authorization**, and
`DenyDataZoneDomainOutsideDataOu` is **still unexercised in both directions** — precisely the state 1c
recorded and this step existed to leave behind.

**So step 0's premise is wrong, and that is the useful output.** The sub-step said a role "DataZone will
accept (a throwaway role trusting `datazone.amazonaws.com`)" was the missing ingredient, and its third
outcome row said *"fix the role and retry"*. **The role was fixed four ways and there is no CLI fix of
this shape.** A probe that cannot reach the thing it probes is not a probe that needs another attempt; it
is a probe that needs a different instrument.

**What this does NOT establish, written down because it is the tempting sentence:** that DataZone forbids
a same-account pass role. It plainly does not — domains exist in the world. The message is **not
attributable from its own text** (Lesson 24), and **a tool's failure is not a property of the world**
(Lesson 30). Recording "DataZone rejects same-account pass role" would be inventing a fact about AWS out
of an error string, and the next reader would design around it.

**The next lever is the console** — it builds its own execution role and names the fields it needs, which
is exactly the thing this probe could not synthesize (Lesson 16 makes recording those fields the point) —
or SageMaker Unified Studio's own setup path. The canary half runs in that sitting too, whatever the
instrument: a positive result alone still cannot separate *the carve-out matches* from *the statement
fires nowhere*.

### State left behind

**Nothing was created.** `datazone list-domains` reads `0` in both accounts after the attempts, and all
**three** probe roles were detached and deleted (`awsds-datazone-probe` in each account, plus the
conventionally-named one in the canary). The 0.2 relocation made earlier in this sitting was load-bearing
in a way that only shows in the counterfactual: had the negative half still named Development and had one
of these attempts got past validation, the "failure" would have been a DataZone V2 domain in the account
D26 forbids one in.

Step 0 in the stage file now carries the measurement as a blockquote, including the sentence about what it
does not license. `make check` green. Nothing committed.

## 2026-08-21 — Step 0 rebuilt around the instrument that died: the probe now rides step 1.2's own creation act

*Provenance: **Claude's hand throughout, on the user's request in this sitting.** No AWS call at all —
this is a plan revision responding to the previous entry's measurement. **The sitting is continuous with
that one and crossed midnight**, which is why the measurement is dated the 20th and the replacement the
21st. No identifier substitutions were needed.*

The entry above measured step 0's CLI probe pair dead in both directions. That reading was recorded there
and nothing else moved — so for one sitting the stage carried a **step whose procedure was known not to
work**, which is the state Lesson 35 is about. This entry is the repair.

### What a dead instrument actually costs, and why annotating it was not enough

A blockquote saying "this does not work" leaves the executor with an unrunnable step and no next move,
and leaves two other files pointing at the procedure as though it ran. The question the step exists to
answer — **does `DenyDataZoneDomainOutsideDataOu` reach `Data` too** — did not go away when its instrument
did. So the repair had to name a *different* instrument rather than downgrade the question.

### The replacement: the probe rides the creation act it was protecting

**0.1a.** There is exactly one `CreateDomain` this organization is going to issue anyway — step 1.2's
`aws_datazone_domain`. It rides the same API the CLI could not clear, in the same account, as the same
principal. So the apply *is* the positive probe, and the step's remaining job is to make it **read** as
one: stage it so the domain goes first (Recipe D — the sanctioned `-target`, so nothing is half-built
around a refused domain), and meet it with a three-outcome fork instead of a surprise.

The third outcome is the one worth having written down in advance: **if Terraform inherits the same
validation wall, the answer is adoption, not force.** Create the domain through the SMUS console setup
path — which builds its own execution and service roles and names every field it needs — then
`terraform import` it. **The reading that makes this more than a workaround is Lesson 16's**: the fields
AWS's own wizard fills in are precisely what four hand-built roles could not synthesize, so the branch
that looks like a defeat is the branch that produces the missing knowledge. The precedent is Stage 2's
`identity/sso/` and `identity/org-policies/` — **adopted, none created** — and Lesson 35 attaches the
moment it happens: the module's create-path prose stops describing this domain.

### The canary half comes back through a different door

The negative half cannot be a console wizard: that would strand wizard-built roles in `Policy Canary` and,
worse, **change the instrument between the two accounts** — which is exactly the defect that made
yesterday's contrast unreadable. Both halves answered the same string because both failed *upstream* of
the thing being compared.

So the replay is built from **CloudTrail**: once a `CreateDomain` has succeeded in Data Governance, its
event carries the request shape that clears validation. Rebuild that shape in the canary and replay it.
`AccessDenied` there → the deny fired, and it is attributable *because* the same shape succeeded next
door (Lesson 24's different channel, supplied by the event rather than by the error text). A domain
created → the statement fires nowhere, INT-12's forbidden fallback is already open — delete it and go to
0.3. **Holding the instrument constant across the two accounts is the property the flat contrast lacked**,
and it is the whole design criterion for the replacement.

### The Status row had been born stale — the second time in this repository on the same day

`5df5a83` committed a Status row reading **"step 0 is now runnable"**, written hours before the same day's
execution proved it was not. That is the identical shape as the `CLAUDE.md` VPN bullet recorded in
[Stage 4's log](log-stage-04-vpn.md) — **prose describing state, written from the intention rather than
from a reading, in the commit that was about to make the reading available.** Both were corrected from
measurements rather than from the text that produced them.

Two instances in one day is a pattern but not yet a lesson: `docs/plan/lessons.md` gets a new entry if it
appears a third time in a different shape. Recorded here and in Stage 4's log so the third occurrence is
recognisable rather than novel.

### The two indexes that still pointed at the dead procedure

Annotating only the stage would have left both of these describing a probe that cannot be run — the
failure mode Lesson 35 names, where the stale path is the one that still *looks* fine.

- **`scp-battery.md`'s DataZone probe** now carries the second measurement: the real role does not clear
  validation either, so the probe **has no runnable CLI form today** — the same standing as the snapshot
  probe measured un-runnable in 1c — and its future template is the CloudTrail-read request shape. *The
  `check-plan-refs.py` gate caught this edit referring to a sibling probe by its row number, which the
  project forbids for exactly the reason the reference was convenient; replaced with a stable one.*
- **`POLICIES.md`'s `DenyDataZoneDomainOutsideDataOu` row** reads *re-measured 2026-08-20*: still
  unexercised in both directions, no standalone CLI probe exists, the exercise moved to 0.1a. Its "attached
  but unexercised" effect is unchanged — **what changed is that it is now unexercised for a measured
  reason rather than an assumed one.**

### Also revised in the stage

The 0.1 outcome table's third row keeps its "not evidence" reading and strikes its *"fix the role and
retry"* advice — four shapes, two accounts, one string. The 0.2 and 0.3 triggers, the pass-0 row, the
"who does what" sentence and step 1.2 itself all now name 0.1a rather than the CLI pair, so the executor
meets the fork at the moment of the apply rather than after it.

`make check` green; `check-docs` red only on the three pre-existing pre-Stage-2 lines;
`check-identifiers` clean. Three files changed, nothing committed.

---

## 2026-08-21 — The pull-forward audited: a prerequisite asserted for five days with nothing behind it, and the re-cut that followed

*Provenance: **Claude's hand throughout, on the user's request, in one sitting later the same day as the
entry above.** **No AWS call of any kind — not a write, not a read.** Every measurement below is `git` or
`grep` against this working tree. No identifier substitutions were needed.*

### What was asked, in two steps

The user asked for the next step of the plan to be prepared. Preparing it surfaced that
`production/pki/` and `production/registry/` — named in the Prerequisites row as *"pulled forward and
**applied** before this stage"* — do not exist in `terraform-live/production/`, which holds only
`bootstrap/`, `egress/`, `foundation/` and `probes/`. The user then asked whether any previous session's
log records **why** it had not been done. That question is what this entry answers, and the answer turned
out to be structural rather than anecdotal.

### The audit

Run as a fan-out over five corpora — the stage logs, the stage and decision files, the git history, the
cross-cutting plan files, and the executable half (`scripts/`, `aws/`, both Terraform trees) — then two
adversarial passes against the result and a synthesis. Every load-bearing citation was re-checked by hand
afterwards. The three commands that decide it:

```
git log --all --oneline -S "Pulled forward and applied before this stage" \
    -- docs/plan/stages/stage-06-unified-studio.md
f44559f review stage 6. proceding stage 3.

git show --stat f44559f
 14 files changed, 1924 insertions(+), 720 deletions(-)        # zero under terraform-live/

git log --all --diff-filter=ADR --name-only \
    -- 'terraform-live/production/pki*' 'terraform-live/production/registry*'
                                                               # empty, every ref
```

So: the clause entered on **2026-08-16**, in a documentation-only commit, and the two paths have **never
been added, never deleted, never renamed** anywhere in the history. Nothing was deferred, attempted or
torn down.

### The finding, and it is a negative one

**No file records a reason, because there was no event to record.** Supporting reads, each a `grep` over
the tracked tree:

| Where a reason would live | What is there |
|---|---|
| `docs/plan/history.md` | no match for pki / registry / ECR / CodeArtifact / D36 — and per that file's own contract a row is earned only once something is *provisioned*, so the silence is the policy working |
| `docs/AWS_STATE.md` | no match for either slice: the gap is not filed as a known exception either |
| this log file | `grep -ic 'pki'` returns **0** through six entries; its only `registry` token is D26's registry/runtime split |
| the corpus generally | when something *is* weighed for pulling forward, this log tables it and records the verdict — the 2026-08-19 entry does exactly that for five candidates. Neither slice ever entered such a table |

**The tense disagreement was four-sided**, and the isolated party was this stage: Stage 7 states the same
pull-forward in the **future** tense (*"Pass 0 … runs before Stage 6"*), `production/bootstrap/pki-key.tf`
schedules the slice at *"Stage 7"* — written **2026-08-15, one day before** the Stage 6 clause — and D36's
own *Referenced by stages* row never listed Stage 6 at all.

**What HAD been executed is one half of D36 and only the lower half:** `production/bootstrap/pki-key.tf`,
applied 2026-08-15 (Stage 2 step 3.4) — the second state key, `alias/awsds-prod-tfstate-pki`, ~USD 1/month,
encrypting nothing until its slice exists. Three further name-only pre-wirings, all for `pki`: the
`RANKS` entry, `NEVER_DESTROY = {("production", "pki")}`, and `gen-backend-hcl.py`'s usage example. For
`registry` there was nothing at all — **not even a rank**, and an unranked slice name raises at import, so
a `production/registry/` written today would have failed `make check` before it could be applied.

**Nothing in the repository would have surfaced this before it bit.** `./aws/studio.py` never asks;
`./aws/supplychain.py` reads ECR, CodeArtifact and the CA parameter but gates its whole note→fail flip on
`built = bool(host_rows)` — the GitLab host, two stages away — so it stays green over a missing pass 0;
`scripts/slices.py` validates the declared `SLICES` table against the tree and would not look for a folder
nobody declared.

### The re-cut, on the user's instruction: move to Stage 7 what belongs there and is not a prerequisite

Decided by asking, per piece, *who consumes it before Stage 7 ends*:

- **`production/pki/` → Stage 7 pass 1, with the leaves.** Its only Stage-6-time consumer was step 5.0's
  image, and the only names the root lets a container trust are served by nothing until Stage 7 — whose
  own step 2.4 defers the leaves for that reason. **D36 §3 amended**; the cost is named rather than
  removed: **new Stage 7 step 2.6** rebuilds and repushes the `dev-env` image with the root, in the
  sitting that first has something to clone (INT-09 already lives there). Step 5.0 keeps an **empty
  CA-install layer** so 2.6 fills a blank instead of editing a build.
- **`production/registry/` stays a prerequisite, narrowed to what this stage consumes, and becomes this
  stage's PASS 0.** Step 5 of Stage 7 splits: **5.a** — the `base`/`dev-env` repositories, CodeArtifact,
  the slice's KMS key and the D35-map consumer policies, authored there and applied here; **5.b** — the
  pull-through cache and the per-application repositories, which nothing before Stage 7 pulls from.
- **The obligation moved out of prose into structures an executor reads:** a build-table row, a pass-table
  row, a sentence in the ordering paragraph, and the `registry` rank in `layers.py` (added ahead of the
  slice, deliberately, for the import-time reason above).

### Files changed in this sitting

`docs/plan/stages/stage-06-unified-studio.md`, `…/stage-07-gitlab-runners-ecr.md`,
`…/stage-08-cicd-pipelines.md` (step 1.1's `Dockerfile` requirement list), `…/stage-03-networking.md`
(step 8.4's CodeArtifact domain), `…/stages/INDEX.md`, `docs/plan/decisions/D36-internal-pki.md` (§3 and
the Status line), `docs/plan/decisions/INDEX.md`, `docs/plan/conventions.md` (both slice comments),
`docs/plan/integrations.md` (INT-01 and INT-19 — where each surface takes the root, recorded at the
receiving end), `docs/GENERAL_PLAN.md`, `CLAUDE.md`, `scripts/tfhygiene/layers.py`, `docs/log/INDEX.md`.

**Deliberately not written:** a `docs/plan/history.md` row — nothing described by the amendment has been
provisioned, which is that file's own bar.

### Lesson 37, promoted by the trigger the previous entry declared

The entry above recorded two instances of *prose describing state, written from the intention rather than
from a reading*, and said a third in a different shape would make it a lesson. This is the third, and the
first to survive five days and two full stage reviews. `docs/plan/lessons.md` gains it and `CLAUDE.md` the
recognition key: **the tell is a clause carrying no date, no measurement and no verdict while its
neighbours in the same row carry all three**, and the risk concentrates in claims about another stage or
another account, which no gate reads and no owner re-reads.

`make check` green; `check-docs` red only on the pre-existing pre-Stage-2 lines, byte-identical to the
baseline at `HEAD`; `check-identifiers` clean. Nothing committed.

## 2026-08-21 — Passes 0, 1 and 2a APPLIED, and verification (i) answered in both directions after being attached and unexercised since Stage 1c

*Provenance. **Claude's hand throughout, and the user ran nothing.** Three authorizations, all given by
the user in this sitting: the standing one that opened it — *"prepare todos os artefatos e autorizo o
terraform apply para tudo que não depender de decisão minha"* — and two asked for and granted mid-sitting,
for the git commits with their module tags and for the two probe batteries. **The stage file assigns
0.1a's canary replay and 1.6's phase-4b probes to the *user*; running them here is an authorized
deviation, named rather than absorbed.** One mechanical substitution, made here and nowhere else:
**account ids → the account's name**. Nothing else is edited — the organization and policy ids, the
`AWSReservedSSO_*` suffix and the error wording arrived as they read; the e-mail inside the one pasted ARN
becomes that user's role, as every entry in this repository does.*

*The session was the **infrastructure user** throughout (`felipenoris+infrastructure_user@…`), through
`InfrastructureAccess` in each account's own `awsds-infra-*` profile — and through
`AWSAdministratorAccess` in `Policy Canary`, which is what `awsds-policy-canary` reaches.*

### What ran, in order

Each apply was planned to a file outside the repository, applied from that file, and re-planned. **Every
re-plan read `No changes`.**

| # | Slice / act | Profile | Result |
|---|---|---|---|
| 1 | `production/registry/` | `awsds-infra-prod` | `14 added` |
| 2 | `sandbox/sagemaker/` | `awsds-infra-sandbox-1` | `7 added` |
| 3 | `development/sagemaker/` | `awsds-infra-dev` | `7 added` |
| 4 | `identity/sso/` | `awsds-infra-identity` | `0 added, 6 to change, 0 to destroy` |
| 5 | `data-governance/governance/` | `awsds-infra-data` | `5 added` — the domain `dzd-d8yrvx1ko7im6o`, `AVAILABLE`, `V2` |
| 6 | `identity/org-policies/` | `awsds-infra-identity` | `0 added, 1 to change, 0 to destroy` |
| 7 | both `*/sagemaker/` again | as above | `1 added` each — the step 9.1 log group, added to the module in the same sitting |
| 8 | 0.1a's canary replay | `awsds-policy-canary` | `AccessDeniedException`, below |
| 9 | `scp-battery.py --phase ou` | six profiles | `25 as expected, 0 unexpected, 7 not measured` |

**No `[E]` slice was applied.** Their lifecycle is `make up` / `make down` (D11), and the runbook lists a
hand-apply of one under *what you never do* — so design A's DNS Firewall was written, validated and
planned (`25 to add` against a torn-down `sandbox/egress/`) and left waiting. `make status` reads
**USD 0.0052/h** at the end of the sitting, the `[D]` VPN host and nothing else.

### Step 0.4, taken before the first apply of the domain slice

`terraform plan` of `data-governance/governance/` renders **five** resource changes: one
`aws_datazone_domain`, two `aws_iam_role`, two `aws_iam_role_policy_attachment`. **No `aws_sagemaker_*`
and no `awscc_sagemaker_*`.** The premise that makes the `Data` OU's `sagemaker:Create*` deny free holds,
and `./aws/studio.py` `US-2` keeps it read after the fact.

### Verification (i) — the half that had never been measured, and the half that explains the previous entry

**Positive.** Apply #5 issued `CreateDomain` from Data Governance and it succeeded in 16 seconds. That is
outcome 1 of 0.1a's three-way fork; the console plan B and the V1 fallback were never needed.

**Negative, in the same sitting.** Two throwaway roles were created in `Policy Canary` — an execution role
and a **service** role, trust and managed policies copied from the two the apply had just built — and the
identical call replayed there:

```
aws datazone create-domain --profile awsds-policy-canary --region us-west-2 \
  --name awsds-probe-canary --domain-version V2 \
  --domain-execution-role arn:aws:iam::<Policy Canary Account>:role/awsds-datazone-probe-exec \
  --service-role         arn:aws:iam::<Policy Canary Account>:role/awsds-datazone-probe-svc
```

```
An error occurred (AccessDeniedException) when calling the CreateDomain operation: User:
arn:aws:sts::<Policy Canary Account>:assumed-role/AWSReservedSSO_AWSAdministratorAccess_59a09ed7d34a9cd1/<the infrastructure user>
is not authorized to perform: datazone:CreateDomain on resource:
arn:aws:datazone:us-west-2:<Policy Canary Account>:domain/* with an explicit deny in a service control
policy: arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/service_control_policy/p-1fp032g8
```

`describe-policy` resolves that id to **`awsds-org-scp-baseline`**. So `aws:PrincipalOrgPaths` **does**
populate for DataZone, the `ForAllValues`-over-an-empty-set failure mode did not fire, and
`DenyDataZoneDomainOutsideDataOu` — *attached but unexercised* in every reading since 1c — is exercised
in **both** directions. The instrument was held constant across the two accounts, which is exactly the
property the flat contrast of the fifth entry lacked.

**And it explains that flat contrast, by measurement rather than by inference.** The four variants of
2026-08-20 passed `--domain-execution-role` and **no `--service-role`**; this replay passed both and
reached authorization, from the same CLI on the same machine. `Cross-account pass role is not allowed` was
DataZone objecting to the *absent service role* — in a message that names neither the field nor the
account, which is why no amount of re-reading it could have said so. The V1 fallback note had suspected it
in one clause (*"a V2 domain may also demand `--service-role`"*) and the probe never tested it.

**State left behind: none.** Both probe roles were detached and deleted in the same sitting;
`list-domains` and `list-roles --query 'Roles[?starts_with(RoleName,\`awsds-\`)]'` both read empty in
`Policy Canary`.

### Phase 4b, for the amendment applied at #6

`./aws/probes/scp-battery.py --phase ou`, the four rows `probes.py` gained this sitting plus one that
already existed:

```
note ou dev      deny  DENY-NOT-SCP                interactive: athena:StartSession (1.6; Athena names no policy - see prod row)
note ou sandbox1 deny  DENY-NOT-SCP                sandboxes: athena:StartSession inherits Interactive's deny (1.6)
ok   ou prod     allow ALLOWED reached-authorization  workloads: athena:StartSession still authorized (1.6 contrast)
ok   ou dev      allow ALLOWED reached-authorization  interactive: athena:StartQueryExecution STILL WORKS (1.6's negative probe - D13)
ok   ou sandbox1 allow ALLOWED reached-authorization  sandboxes: athena:StartQueryExecution still authorized (4e contrast)
```

Three things this settles, and only the first was expected. The deny reaches **both** Interactive
accounts, Sandbox by **inheritance** through the nested OU that carries no document of its own (D37). The
**negative probe passed** — `StartQueryExecution` still reaches authorization in both — so the amendment
did not take D13's query path with it, which was the one outcome that would have made 1.6 a mistake. And
**`StartSession` authorizes before it validates**: 4e measured that for `StartQueryExecution` only, and
Lesson 21 forbids carrying it across actions, so it had to be read here. The seven `not measured` rows are
pre-existing — `ec2:RunInstances` / `RequestSpotInstances` in the two accounts that have no VPC.

### Four readings that were measurements rather than choices

- **The SMUS managed-policy family, read from `iam list-policies --scope AWS` rather than remembered.**
  What exists: `service-role/SageMakerStudioDomainExecutionRolePolicy`,
  `service-role/SageMakerStudioDomainServiceRolePolicy`,
  `service-role/SageMakerStudioProjectProvisioningRolePolicy`,
  `AmazonDataZoneSageMakerManageAccessRolePolicy`. What does **not**, though each is a plausible guess:
  `SageMakerStudioProjectRoleForManageAccessPolicy`, `AmazonDataZoneSageMakerProvisioningPolicy`.
  A fifth exists and was deliberately **not** used — `service-role/SageMakerStudioQueryExecutionRolePolicy`
  reads as an Athena **federation** role (`glue:GetConnection`, an Athena spill bucket,
  `lambda:InvokeFunction`), and nothing in this design federates a query, so creating it would be a
  principal nobody chose.
- **`athena:UpdateSession` is in no Athena API model.** The botocore model shipped with the installed CLI
  (`athena/2017-05-18`) carries `StartSession`, `TerminateSession`, `GetSession`, `GetSessionStatus`,
  `GetSessionEndpoint`, `ListSessions`, `ListNotebookSessions` and `StartCalculationExecution` — and no
  `UpdateSession`. Shipped in the statement anyway, since it is AWS's own sample and denies nothing while
  costing nothing, with `StartCalculationExecution` **added** beside it: `StartSession` choking a
  calculation by dependency was a *should*, and the API takes a `SessionId` obtained however.
- **`awscc_datazone_environment_blueprint_configuration` carries `environment_role_permission_boundary`
  and `aws_datazone_environment_blueprint_configuration` does not** — read from
  `terraform providers schema -json` on both pinned providers, not from a changelog.
- **`PutEnvironmentBlueprintConfiguration` takes a `domainIdentifier` and no account parameter**, so the
  account it configures is the caller's. The stage's pass table had the resource in the domain account;
  step 1.4's own body said *"user applies as that account's profile"* and was right.

### Two pieces of hygiene the sitting produced rather than planned

- **The new slices locked `hashicorp/aws` at `6.61.0` while every slice before them holds `6.60.0`**, both
  inside `~> 6.60`. Left as it landed — a slice initialised today gets today's patch, which is what a lock
  file is for — but the **platform coverage was fixed**: `terraform providers lock` re-run for
  `darwin_arm64`, `linux_amd64`, `linux_arm64` on all four new slices, because Stage 2 step 6.3's reason
  is the Stage 7-8 runners failing `init` with a checksum error that reads like an attack. Re-planned
  `No changes` afterwards, all four.
- **`versions.tf` stopped being byte-identical in every slice**, in three of them, deliberately: the two
  `sagemaker/` slices and `governance/` declare a second provider (`awscc`). The `aws` block is
  untouched, each file says why in place, and `terraform-live/README.md` records the exception.

### What was deliberately not done

No `[E]` apply (above). No log entry until this one was asked for. No `docs/plan/history.md` row: the two
things this sitting changed about the *plan* — the blueprint configuration's owning slice and the pass
table split — describe objects that were provisioned in the same sitting, so the correction and the build
are one event rather than a later revision. And `scripts/down-studio-apps.py` deletes apps but **not**
spaces by default: step 8.3 puts only the running apps in `[E]`, a space is an EBS volume plus whatever
was not committed yet, and `--spaces` is the opt-in.

### Files, commits, and what is owed

Two commits on `claude/stage-06-unified-studio`, in Recipe B's order. **Commit 1** — `terraform-modules/`
alone: `ecr-repo/`, `sagemaker-denies/`, `sagemaker-prereqs/` (new) and `vpc-egress/dns-firewall.tf`. Then
`ecr-repo-v0.1.0`, `sagemaker-denies-v0.1.0`, `sagemaker-prereqs-v0.1.0`, `vpc-egress-v0.2.0`, pushed with
`--tags` and **each one confirmed on origin with `git ls-remote` before commit 2**, which is the step §3
exists to make routine. **Commit 2** — the four new slices, the amended ones, `scripts/`, and the
documentation. The four applied slices were then **re-initialised against the pushed tags** rather than
the local paths the authoring plans used, and all four re-planned `No changes`: that is what says the tag
serves exactly the code that was applied. [PR #24](https://github.com/felipenoris/AWS-DataScience/pull/24).

`make check` green. `make check-ou` green. `check-docs` red only on the pre-existing pre-Stage-2 lines.
`./aws/studio.py` **0 FAILED** — `US-1`, `US-2`, `US-6` and both `US-9` rows pass; `US-3` and `US-4` read
`note`, which is the correct reading before an account association exists rather than a gap.
`./aws/supplychain.py` **0 FAILED**, and `SC-7` reads both ECR repositories and the CodeArtifact endpoint
**cross-account from both Interactive accounts** — 0 images visible, which is the honest answer before
step 5.0. `./aws/org-policies.py` and `./aws/datalake.py` both clean.

**Owed, and none of it is code:** the account association in the console (1.3 — no public API), which
gates the row in `backend.SMUS_ASSOCIATED`, the second apply of both `sagemaker/` slices (the blueprint
configurations) and the second apply of `governance/` (the two project profiles); the `base`/`dev-env`
image build and push (5.0); then passes 3, 4 and 5. Decisions 1, 2 and 6 remain in-stage — decision 2 is
**coded** as `enable_trusted_identity_propagation = false`, following the grain Stage 5 chose, and
flipping it is a decision that reopens Stage 5's decision 6 rather than a parameter change.

## 2026-08-21 — The plan reviewed against the build: two defects in the sitting above, a four-month gap no gate read, and an ECR grant that was never needed

*Provenance. **Claude's hand throughout, on the user's request in this sitting** — *"revise o plano com base
nos achados da sessão"*, after *"fiz o merge do PR, sincroniza a pasta local"* — plus a separate
authorization, given at the end, for the commits, the module tag and the pull request. **The user ran
nothing.** One AWS write is recorded below and it was covered by the standing `terraform apply`
authorization of the sitting above; everything else in this entry is reading, editing and measurement. **No
identifier substitution was needed in this entry.***

### The sync, and the check the runbook makes non-optional after it

`main` at `f828730`, worktree clean, `claude/stage-06-unified-studio` deleted. **The merge was a REBASE
merge**, so all three commit hashes moved and **all four module tags came out `orphaned`** — which
[`terraform-changes.md`](../plan/runbooks/terraform-changes.md) §3 says is the normal outcome and instructs
you not to fix. What it does ask for is the content check, one command per module:

```
git rev-parse "<tag>^{}:terraform-modules/<name>"  vs  "main:terraform-modules/<name>"
```

**Four out of four IDENTICAL** — `ecr-repo` `2e8e0af…`, `sagemaker-denies` `3c75d54…`, `sagemaker-prereqs`
`8fdc99b…`, `vpc-egress` `5791bf7…` — so every tag serves exactly what `main` carries and no version bump
was owed on the merge. **Worth one note for the next reader:** the first attempt at this check produced four
false DIFFERENTs, because in zsh `"$t:terraform-…"` applies the `:t` history modifier to the variable. The
shape that works is `"${t}^{}:path"`, and the `^{}` also dereferences an annotated tag.

### The review itself, and what it cost

Six lenses over the surfaces a build sitting can invalidate — the decision files, the stages that come
after, the cross-cutting documents, cost, the gates, and "is what is recorded actually true" — with **every
candidate finding verified adversarially against the repository before it was allowed to count**. **97
candidates, 37 survived, 20 edits after deduplication**; 104 agents, ~70 minutes. **The refutations were
kept rather than discarded**, which is the half worth having: fourteen of them are variations on *this is
already written two files away*, and in a repository whose rule is one copy per fact, a restatement is a
defect rather than an improvement. Three of the refuted ones are recorded here because they read like
findings and are not: a `history.md` row is **not** owed (its bar is "after provisioning", and what changed
describes objects that are not provisioned); decision 2 has **not** been taken silently by a default
(`profiles_enabled` is false, so the `for_each` is empty and no apply can take it); and `CLAUDE.md` gets
**nothing** (its Current position is already over budget, and every fact below has an owner elsewhere).

### Two defects in the sitting above, and both are mine

1. **Seven executor instructions named the wrong table.** Six files told whoever runs step 1.3 to add the
   row to `backend.SMUS_MEMBERS`. The flag that gates the second apply reads `SMUS_ASSOCIATED`. **Following
   the instruction is a no-op that announces nothing**: `blueprints_enabled` stays false, pass 2c re-plans
   `No changes`, and the reader concludes the association did not work. The worst instance did not merely
   name the wrong table — it assigned the *decision* table the *measurement* table's defining property
   ("a table whose rows are measurements, not intentions").
2. **`profiles_enabled` REVERSES, and nothing said so.** It feeds a `for_each` in
   `governance/profiles.tf`, so a member added to `SMUS_MEMBERS` while `SMUS_ASSOCIATED` lacks it takes the
   flag back to false and **the next `governance/` apply destroys the project profiles that already
   exist** — or fails, if projects hang off them. The rule that falls out of it is an ordering: once a
   profile exists, the `SMUS_ASSOCIATED` row is written **before** the `SMUS_MEMBERS` row, never the other
   way round. The property is now in `backend.py`; the ordering went to **Stage 14 step 4**, the step that
   performs it — which until today read "associate the new Sandbox … and configure the ML blueprint into
   it", a sentence naming a blueprint that does not exist and hiding six ordered acts, two of them
   different applies of one slice.

### A gap four months old, exposed sideways

Setting up the three-platform lock for the four new slices is what made it visible: **three slices carried
ONE platform** — `{data-governance,development,sandbox}/data/`, byte-identical to each other, one `h1:`
hash each — where every other slice carried three. Stage 2 step 6.3 has required three since 2026-08-15 and
**nothing had ever read a lock file.**

**The failure mode was measured rather than assumed, and it is two different things:** with the
`TF_PLUGIN_CACHE_DIR` this repository *mandates*, Terraform has a directory and not a zip, so it can only
compute an `h1:` — there is none for that platform and `init` **fails outright**, with a checksum error that
reads like a supply-chain attack. Without the cache it verifies against the 16 `zh:` hashes the registry
signs, **appends** the missing `h1:` and silently rewrites a committed file. The consumers are Stage 7-8's
runners (Linux, both architectures) and Stage 8 step 6.2's GitHub Actions job.

Fixed by **copying** `sandbox/foundation`'s lock over the three — step 6.3's own instruction — rather than
by `terraform providers lock`, which re-resolves `~> 6.60` and would have carried three applied `[P]` slices
to 6.61.0 and manufactured a third version island. All three re-planned `No changes` afterwards and the
`init` did not rewrite them.

**And it landed with a gate, in the same commit** — `scripts/check-provider-locks.py`, in `make check` and
in `pre-commit`. **The negative control was run**: two `h1:` hashes were removed from one slice on purpose,
**both** of its checks fired (the platform count, and the subset-of-a-sibling-at-the-same-version test), and
the file was restored. It reports the version census (`aws 6.60.0 ×20, 6.61.0 ×4, awscc 1.98.0 ×3`) without
failing on it, because the split was accepted the day before — and its header states what it **cannot** see:
a lock file records no platform *name*, so counts and sets are all it can compare.

### The cost cluster — the floor had moved and four rows disagreed

- **The KMS enumeration resolved to ten keys; twelve were measured live** (`list-aliases` across the five
  profiled accounts). None of the three Stage 6 keys matched any clause of it — which is exactly how a floor
  moves unrecorded. Both `cost-model.md` and `PRICING.md` §2 now say thirteen at N=1, and the attribution of
  D36's key is corrected: it is `alias/awsds-prod-tfstate-pki`, created by `production/bootstrap/` on
  2026-08-15, and **`production/pki/` has still never existed**.
- **The unit is a key VERSION, not a key.** The offer file prices *"$1 per customer managed KMS key
  version"*, and every CMK here rotates at the 365-day default (`True 365`, measured on six keys). So the
  count cell is a **year-one** figure: the Stage 2 keys reach two versions around 2027-08 and three around
  2028-08. Recorded as a **rule** beside the row rather than as a rate, so §0's "every number came from the
  bulk API" stays true.
- **The Floor range was deliberately NOT moved.** Two independent re-sums of the same column during the
  review disagreed on the base by half a dollar, and that row already holds an unapplied −USD 2-4.5 Config
  correction. A dated note instead, and the recompute stays Stage 12 step 5's.
- **A business unit costs three CMKs, not two** — its Sandbox is an Interactive account and now hosts SMUS
  projects too. D35's own parenthetical became a pointer, so the enumeration has one copy.
- **`datazone` took the Interactive accounts from 11 endpoints to 12.** That was the previous sitting's own
  edit and it was not propagated: `layers.py`'s `usd_per_hour` (0.160 → **0.170**), `PRICING.md` §3 in both
  region columns, the two hourly summaries, `cost-model.md`, Stage 3's table and `aws/egress.py`. **`make
  status` had been under-reporting the burn by a cent an hour per account.** One curiosity kept:
  `egress.py` carried "~USD 4.08/day" in one place and 3.84 in another for four days — the 2026-08-17
  NFS-removal commit decremented one and not the other — and `datazone` has now made the stale figure
  accidentally right. Both are stated from the same arithmetic so the next change moves them together.
- **D12 stopped carrying a second era of arithmetic.** Its "~USD 21-27/month floor … roughly USD 29-31" were
  the pre-D29/D31 numbers `cost-model.md` retired on 2026-08-08 as understatements, while the revision
  trigger four lines below already read USD 29-43. One decision file, two eras, the older one flattering the
  ceiling — Lesson 7's shape. It now points at the file that owns the projection and carries no figure.

### The one AWS write, and it corrects a claim of mine

**A cross-account ECR pull needs the repository policy and NO KMS grant.** ECR creates two grants on the
repository's key for itself at repository creation and makes the `Decrypt` call on the caller's behalf —
`REFERENCES.md` has carried that page since it deleted half of Stage 9's old step 7, and Stage 9 says it in
three places. The registry key's consumer statement named `ecr` beside `codeartifact` anyway, and the INT-01
sentence written the day before claimed `SC-7` proved "the repository policy and the key policy agree".
**It proved neither half of that**: `describe-images` decrypts no layer.

Narrowed to `kms:ViaService = codeartifact` alone — where the pair *is* real, because CodeArtifact assets
are decrypted **as the reader** — applied (`0 to add, 1 to change, 0 to destroy`), re-planned `No changes`,
and read back from `get-key-policy`: three statements, one `ViaService`, `codeartifact.us-west-2`. **What is
still unmeasured is said out loud in the file itself**: Stage 6 step 5.1's first real cross-account pull is
the test, and if it fails on KMS the AWS page is wrong and the fix is one service name.

### Six more corrections, each in the file that owns it

`layers.py` said the domain had "three IAM roles" where `governance/iam.tf` heads itself *TWO, NOT THREE* —
the count was copied from the `aws-ia` module's shape and was never true of this slice. `GLOSSARY.md` and
`SMUS.md` still routed a reader to that module and to the wrong step number. **Verification (ii) had never
recorded its own answer** — it lived only in a tree comment in `conventions.md` — and step 1.2's "consume
the module selectively" is now marked superseded, since it is the instruction that re-seeds the error.
**"The ML blueprint" appeared in six places and names nothing**; the per-project SageMaker AI domain comes
from `Tooling`. `aws/INDEX.md` said three probes would really act where `probes/README.md` says seven, and
still described the supply-chain baseline in the future tense. And **`US-3` read empty on success and on
failure, permanently** (Lesson 13): it looked only in the domain account, where a blueprint configuration
must never appear. It now reads every member account too — the configuration belongs to the account that
*called* the API — and its verdict is split by column: `pass` for an empty domain account, `note` per member
until its association exists.

**A new verification (xx)** was added rather than a fix: `alias/awsds-<env>-project` is referenced by
nothing today — no blueprint regional parameter and no Tooling parameter takes a key — so USD 2.00/month is
being paid for two CMKs whose purpose is written entirely in the future tense. The branch is made explicit
(name the parameter, or delete them) instead of drifting.

### Files, commits, and what this sitting did not do

Two commits on `claude/stage-06-plan-review`, in Recipe B's order — the module alone, then
`sagemaker-prereqs-v0.1.1` pushed and confirmed on origin, then the callers and everything else. **The
module diff is one comment block and one variable `description`, no behaviour**, but the tag would otherwise
stop serving what `main` carries, which §3's post-merge check calls a real problem. Both `*/sagemaker/`
slices were re-initialised against the new tag and re-planned `No changes`.

`make check` green with the new ninth gate in it; `make check-ou` green; `check-docs` red on exactly the one
pre-existing line it was red on before (compared against a stash of the baseline, not assumed); checkov
854/0; every one of the nine applied slices re-plans `No changes`; `./aws/studio.py`, `./aws/supplychain.py`,
`./aws/org-policies.py` and `./aws/datalake.py` all 0 FAILED.

**Not done, deliberately:** no `docs/plan/history.md` row, for the reason the seventh and eighth entries
already reached — that file's bar is *after provisioning*, and what changed here describes objects that are
not provisioned. No `CLAUDE.md` edit. And **no new lesson**: the candidate was *an error message that names
a cause which is not the cause*, and it was refuted as an instance of Lesson 24 (a result that cannot be
attributed from its own text is separated by a different channel) standing on Lesson 30 (a tool's failure is
not a property of the world) — two lessons that already cover it, in a file where the bar is a mistake worth
not repeating rather than an observation worth having.

---

## 2026-08-21 — The build code, and a build host to run it on: `images/`, `sandbox/devbox/`, and the VPN host's second job

**Claude's hand, on the user's request, across two asks in one sitting.** The first was *"escreve os
Dockerfiles"*; the second re-scoped where they would be built. **Nothing in this entry is a measurement of
a running system yet** — the applies are the section at the end, written after they ran, and every
sentence before it describes code, documentation and readings taken from publishers' metadata.

### It started as a doc correction, and the correction was load-bearing

Step 5.0 named the SMUS BYOI requirement as *"base on `jupyterlab/default`, health check on 8888"*. Read
against the specification, **`jupyterlab/default` is the Base URL** from the health-check section
(`jupyterlab/default/api/status`; one application, always named `default`) — the required **base image**
is `public.ecr.aws/sagemaker/sagemaker-distribution`, **≥ `2.6-cpu`**, whose whole point is that it
already carries the extensions without which an image will not run in SMUS at all. Building to the old
sentence would have produced an image the service refuses. Three more constraints the summary did not
carry, each now enforced in the files rather than restated: **no `ENTRYPOINT`** (the page says adding one
*"will not work as expected"* — the distribution's `_entrypoint.sh` must survive, and a custom one is a
`ContainerConfig` setting); `/opt/ml`, `/opt/.sagemakerinternal` and `/var/log/studio` are **AWS's**; and
the space's EBS volume mounts at `/home/sagemaker-user` on a path that cannot be changed.

**And the ancestry is forced from both ends, which nearly collide.** Stage 8 step 1 wants ONE ancestor —
application images `FROM base`, so that D17's *"promote only the code"* is true by construction; the BYOI
spec wants the notebook image to descend from the distribution. The only shape satisfying both is **`base`
being the distribution plus this project's layer**, with everything else descending from it. The cost is
named rather than discovered: an ETL container inherits a JupyterLab distribution it never opens. The
alternative — a slim application base beside a distribution-rooted `dev-env` — is exactly the *"two
independently built images"* Stage 8 rejects in as many words.

### `images/`, and what the files are made to defend

`base/` and `dev-env/`, their package sets as plain text files (the data scientist owns them —
`ORGANIZATION.md`'s *Dev Env Steward* — and a merge request against a list is reviewable in a way one
against a `RUN` line is not), and a README carrying the seam. Every pin came from the publisher's own
metadata on the day: the base **by digest** read anonymously from the public registry's Docker Registry v2
API (no IAM action, so `DenyEcrPublicEntirely` does not reach it), Julia's sha256 from
`versions.json`, `rustup-init`'s from its published `.sha256`.

**Three build-time assertions, because the discipline the Stage 8 pipeline will enforce has to be
somewhere until it exists.** The activity-monitor extension is **checked, not installed** — the base is
*documented* to carry it, documented is not measured, and re-installing would paper over a base that
stopped shipping it, whose symptom is an app billing all night (`US-7`/`US-10`), which is the expensive
place to find out. The **CA-root count** is asserted in both directions, so Stage 7 step 2.6 flipping
`CA_ROOTS_EXPECTED=1` cannot half-happen. The **Julia kernelspec** is relocated and then asserted, because
`IJulia.installkernel` delegates to `jupyter kernelspec install --user` when a `jupyter` is on the PATH —
and there is one — which lands the spec in *root's* home, invisible to `sagemaker-user`, failing later and
silently as *"Julia is missing from the launcher"*.

**The CA layer went into `base`, not `dev-env`**, which is a deviation from the sentence Stage 7 step 2.6
was written with: `dev-env` is `FROM base`, and one intent enforced in two places diverges (Lesson 33).
Step 2.6 now says it rebuilds both, with the BuildKit registry-cache note that keeps the re-push to the
changed layer.

**Four defects in my own first draft, found by re-reading it rather than by running it** (there is no
docker on this laptop, so none of it has been built): `ARG` does not survive `FROM` — three provenance
LABELs would have recorded the empty string, *a label that looks like a measurement and is not*;
`pip config set` defaults to the USER level, so run as root it lands in `/root/.config` and holds for the
rest of the build and not at runtime; a `sed 's/[^,]*/"&"/g'` join emits `""` artifacts at every comma;
and `rustup-init --component rustfmt clippy` needed the repeated-flag form.

### The re-scope, and the two facts that forced it

The user then set the base image to **`4.3.0-cpu`** by name (digest measured here:
`sha256:7f5d9c64…`, amd64, Ubuntu 24.04, 24 layers ≈ 3.93 GB compressed, built 2026-07-10) and moved the
build off the laptop. **Two measurements say it had to move:** the distribution publishes **`cpu`/`gpu`
suffixes and no `arm64` variant at all**, and SMUS spaces run on x86 — while this laptop is `arm64` **with
no docker installed**. What the first draft treated as a slow path was not a path.

### `sandbox/devbox/` — an `[E]` build host whose network shape is the whole design

`t3.xlarge`, 64 GiB, both selectable in a tracked `instance_type.auto.tfvars` that deliberately mirrors
`sandbox/vpn/`'s down to the name and the two keys — **with one difference written on both**: there the
host is `[D]` and the disk is a standing commitment EBS will not shrink; here it is `[E]`, so a wrong
value costs one teardown. **In:** nothing reaches it except from the WireGuard client range; the shell
arrives over Session Manager, which needs no inbound rule at all. **Out:** through the WireGuard host,
with **no NAT gateway anywhere** — `egress/` is not a prerequisite and need never come up for a build,
which is 0.170 USD/h not spent.

**It is the ISOLATED tier, and that was a choice between two conflicts.** The private tier's default route
belongs to `egress/` under `egress_mode=A`, and two slices writing `0.0.0.0/0` into one route table is a
collision rather than a design. The isolated tier has no default route by construction — the property that
leaves room for one, **and** the premise `sandbox/probes/`'s perimeter probe measures. So the conflict was
not removed, it was **moved to a slice that is not normally up**, and then made a control:
`./scripts/devbox.py` refuses to apply while a probe instance exists, because a comment is an intention
(Lesson 5).

**What the host deliberately cannot do is push.** Its role carries `AmazonSSMManagedInstanceCore` and no
`ecr:` at all: the Production registry grants the Interactive accounts a *pull* and nothing more, so a
push from Sandbox is refused at the far end anyway — and granting the near half of a permission the far
half denies would produce a role that reads as if it could publish (Lesson 5 again, from the other side).

### The VPN host's second job, and why one attribute had to change

`wireguard-v0.4.0` adds `vpc_nat_cidrs`. Filled, it turns **source/destination checking off** and adds one
MASQUERADE plus two FORWARD rules per range. **The module's existing comment argued for keeping the check
ON, and that argument was never wrong — it was only ever about the tunnel.** Source/dest checking is
applied by the ENI on the way **in** as well as out: a packet from the isolated tier carries neither the
host's address as source nor as destination, so EC2 drops it *before* the kernel could route or
masquerade it. No `iptables` rule recovers from that — the masquerade makes the **outbound** leg
legitimate, the attribute is about the **inbound** one.

**Two details that are the reusable part.** The rules ride **`wg0`'s `PostUp`**, not the user data,
because this host is `[D]`: user data runs at first boot only, so a rule written there is gone after the
first stop, while `wg-quick` re-runs `PostUp` on every boot — the only re-entrant hook the host already
has. And **the capability is `[D]` while the reach is `[E]`**: a masquerade rule matches nothing until a
route table sends traffic at it, and that route is created and destroyed with the build session. So the
standing change is exactly one attribute.

**Predicted before the apply, from the code rather than from a plan:** turning it on the first time
**replaces the host**, because the rules live in `wg0.conf` which the user data writes and
`user_data_replace_on_change = true`. Under §K's rules that is routine — the `[P]` Elastic IP and host key
survive, so no client `.conf` moves — and **it is not a lockout risk**: `DenyControlPlaneOffVpn` pins the
six **persona** sets to the Elastic IP and `InfrastructureAccess` is not one of them, so the session
running the apply is not the session being interrupted. That is `slices.py`'s *"the day
`InfrastructureAccess` joins the deny"*, still future, and this is the first change that would have cared.

### Readings taken rather than assumed, and one method note

- **No preventive control requires the image push to cross the tunnel** — a `grep` over all ten
  organization policy documents finds no `aws:SourceVpce`, `aws:SourceVpc` or `aws:SourceIp` condition
  anywhere. Worth knowing before sending several GB through a `t3.nano`.
- **`t3.xlarge` = 0.1664 USD/h `us-west-2`, 0.2688 `sa-east-1`** (ratio 1.62, the same every other `t3`
  row carries). Measured — but through **`aws pricing get-products`** rather than the bulk offer file,
  because the `AmazonEC2` region file is hundreds of megabytes. `PRICING.md` §0 now names that door and
  the one difference that matters to somebody repeating it: it needs credentials.
- **The build context does not fit in user data.** A gzip+base64 of `images/` is ~27 KB against the
  16 KB ceiling — measured, not estimated, which is why `devbox.py sync` exists at all and rides
  `ssm:SendCommand`, fenced the way `./aws/vpn.py --on-host` is.
- **`SMUS.md`'s Bedrock cell still said a `PRICING.md` row was owed**, six hours after that row was
  written. Corrected, and the cell now carries the two readings the rate table alone would hide.

### The applies, and the defect they found

**Written after they ran.** Three slices in Sandbox, in this order, every one re-planned to `No changes`
afterwards.

| Slice | Plan | Result |
|---|---|---|
| `sandbox/vpn/` | `2 to add, 1 to change, 2 to destroy` | **The host was REPLACED, exactly as predicted before the plan was taken** — `user_data` *forces replacement*, `source_dest_check true -> false`, the EIP association replaced, the health alarm updated in place. `52.89.212.1` re-associated with the new instance, so the prediction that no client `.conf` moves held |
| `sandbox/foundation/` | `0 to add, 1 to change, 0 to destroy` | **Not planned before the sitting — see below.** One ingress rule added to the `[P]` WireGuard security group |
| `sandbox/devbox/` | `6 to add, 0 to change, 0 to destroy` | The host, its SG, its role and profile, and the one route |

**THE DEFECT IS MINE AND IT IS LESSON 28 IN ITS PUREST FORM: reach is an INTERSECTION, and I built two
thirds of it.** The route sent the isolated tier's default at the WireGuard host, `vpc_nat_cidrs` gave that
host the masquerade rules — and the host's `[P]` security group still admitted **UDP/51820 and nothing
else**, so every forwarded packet was dropped on arrival, after the routing and the translation had both
done their jobs. **The three pieces live in three slices, so no file I wrote or read was wrong.**

**The symptom is worth keeping, because it is not the symptom of a firewall.** The devbox came up,
installed docker and git **successfully** — those come from the AL2023 repository through the S3 *gateway*
endpoint, which needs no route at all — and then sat there until `devbox.py up` gave up waiting for Session
Manager. The console output ends with `Post "https://ssm.us-west-2.amazonaws.com/": dial tcp … i/o
timeout`. A dnf that works followed by an SSM that times out reads as a broken mirror or a flaky agent, not
as a missing security-group rule. **Two things I had already written are what made it a ten-minute
diagnosis instead of an evening**: the first-boot script takes an egress reading and prints
`NO EGRESS - the route through the WireGuard host is not working`, and `devbox.py`'s own failure message
says *"that is the route through the WireGuard host failing, nine times out of ten"*.

**The fix is in `foundation/`, not in the `[E]` slice that wants it, and the reason is mechanical:** that
security group declares its rules **inline**, which makes them authoritative — a separate
`aws_vpc_security_group_ingress_rule` written by `devbox/` would be silently removed by the next apply of
`foundation/` and show as perpetual drift until it was. That is INT-11's failure mode wearing a security
group. So the path now sits at **three lifetimes**: the group `[P]`, the masquerade `[D]` with the host,
the **route** `[E]` with the session — and the route stays the only thing that comes and goes. What is left
standing is a **private** range admitting a tier that is empty between sessions.

**`VP-3` was the check to worry about and it was checked rather than assumed:** `./aws/vpn.py` reads
**`exactly one world-open rule`** after the change, because the new rule is a private range. All nine VP
rows pass. Its second `VP-7` row also states in the tool's own words the thing this sitting reasoned about
before the apply: `DenyControlPlaneOffVpn` is **absent from `InfrastructureAccess` by decision**, which is
why replacing the tunnel endpoint from the laptop is not a lockout.

### The end-to-end reading, which is the only thing that proves the design

Taken over SSM after the fix:

```
public address this host leaves under:
52.89.212.1
docker:  Docker version 25.0.14
arch:    x86_64
disk:    /dev/nvme0n1p1  64G  2.5G  62G  4% /
```

**`52.89.212.1` is the WireGuard host's Elastic IP.** That single line is the whole claim measured rather
than argued: the build host is in a tier with no internet gateway, it reaches the internet, and it leaves
under the address of the one host in this design that is allowed to face the world. `devbox.py sync` also
ran clean — 16 728 bytes of base64, 8 files, landed at `/opt/awsds/images`.

### One more thing I got wrong, and it was already written down two lines away

The security group rule description I first wrote carried an apostrophe, and
`AuthorizeSecurityGroupIngress` rejects the whole call — at **plan** time, on a regex. The file I was
editing already said so, in capitals, eight lines above the block I was adding to: *"A RULE DESCRIPTION
CARRIES NO APOSTROPHE … measured in Stage 3."* It cost one plan. **No new lesson**: the fact was recorded,
in the right place, and I did not read it — which is a reading failure, not a missing rule.

### Files, commits, and what is owed

Two commits on `claude/stage-06-devbox` in Recipe B's order — the module alone, then `wireguard-v0.4.0`
pushed and **confirmed on origin by `git ls-remote` against the local `rev-parse`** before the second. The
commit gate caught two things the runbook's §7 predicts and both were re-inits: `devbox/`'s provider cache
disagreed with the sibling lock file I had copied in (6.61.0 cached, 6.60.0 locked), and `vpn/`'s
`.terraform/modules` still recorded `wireguard-v0.3.0`.

`make check` green, `checkov` 0 failed on both new trees, all three touched slices re-plan `No changes`,
`./aws/vpn.py` 0 FAILED.

**Owed, and both are the user's:** the `docker build` of the two images on this host — which is what the
box exists for and has not been done — and the push of the results into the Production ECR from an identity
that may. **The devbox is UP and billing at 0.1664 USD/h as this is written**; `./scripts/devbox.py down`
is the cure and `status` is the reading.

### A follow-up the same day: the requirement was withdrawn rather than delivered in name

The user asked *"`devbox.py ssm` works without me being on the VPN — is that expected?"* **It is, and the
sentence I had written was wrong.** `ssm start-session` goes laptop → the **public** SSM API → the channel
the agent holds open **outbound**; the security group never sees it. So *"reachable only with the tunnel
up"* was false for the one path anybody uses — and the slice README said so **itself**, two clauses after
claiming the opposite. A sentence disagreeing with itself inside one table cell.

**What the measurement found beside it, and it is the half that decided the outcome.** Asked what other
ways in exist, the host answered: `sshd` **active on 0.0.0.0:22**, `ec2-instance-connect` **installed**,
`AuthorizedKeysCommand` already wired to it, and **zero authorized keys**. So the ingress rule was not
merely failing to gate the shell — it was leaving port 22 *reachable* from the tunnel on a host one
`key_name` away from a second way in that nothing in this design asked for. **A grant with no consumer is
not neutral; it is the shape a later convenience grows out of** (Lesson 5, from the side where the control
is real but guards nothing). Two other paths were priced and reported: **EC2 Instance Connect** would have
worked today with no infrastructure change *and* would genuinely have required the tunnel (ephemeral
60-second key, IAM-authenticated, but the SSH still has to reach a private IP) — and the **serial console**
is shut off org-wide, which the API states in its own words: `SerialConsoleAccessEnabled: false`,
**`ManagedBy: declarative-policy`**. That is Stage 1c step 7.8's declarative policy exercised for the first
time against something real.

**The user's decision: SSM only, and drop the VPN-only requirement — keep the egress one.** So the ingress
rule was **removed entirely** rather than narrowed, `peer_cidr` left the slice's variables and
`backend.py`'s emission with it, and five documents stopped claiming a control that was not one. The
security group now has an **empty ingress list**, and the host registers `Online` with it that way —
which is the same fact measured from the other side.

**A `description` change forces a security-group replacement, so this went out as `down` then `up`** rather
than as an in-place edit fought through ordering. That is what the `[E]` layer is for, and it cost one
teardown.

**And the re-`up` found a defect in my own helper.** `docker --version` taken the moment `up` returned came
back **empty**, with `systemctl is-active docker` saying `inactive` and the boot log mid-install: **the SSM
agent registers while cloud-init is still running**, so `up` had been reporting *"up. next: sync, ssm"*
about the agent while the toolchain was not there yet — one measurement standing in for another
(Lesson 13). `up` now waits for `docker` to be **active** and says which of the two it is waiting on.

**What did not change, and is the requirement that stayed:** egress. The build host still reaches the
internet only through the WireGuard host, still with no NAT gateway anywhere, and still leaves under
`52.89.212.1` — re-measured after the rebuild.

**Not edited: `objectives.md`.** The brief's *"All user access to the cloud infrastructure will be
performed through a VPN"* is untouched by this, because open question 17 already records the reading that
covers it — the objective is delivered **for every persona**, and the administrative credential is
deliberately outside it. This is that exemption being leaned on again, in a new place; the question exists
to keep it visible rather than let it become furniture.

## 2026-08-21 — Step 1.3 RAN: the association auto-accepts, the RAM permission is not one the plan could name, and a check failed because the step worked

### What was done in the console — **the user's hand, their words, verbatim**

- Login AWS Console as Infrastructure User -> Data Governance Account -> InfrastructureAccess -> Amazon DataZone -> View Domains -> `awsds-studio`.

- Account Associations -> Request Association. Added account numbers for `Sandbox-1 Account`, `Development Account` -> Request Association. Selected `AWS Organization-only RAM share` and `IAM users can access APIs only`.

- In `Account Associations` I can see account IDs for `Sandbox` and `Development`, both with RAM Policy `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`, with status `Associated`.

- Changing account to Sandbox Account 1 -> InfrastructureAccess -> Amazon DataZone. It's already associated with the domain. Same for Development Account.


### The readings — **Claude's hand, read-only, through `awsds-infra-{data,sandbox-1,dev}`**

The step asked for two, *"in the same sitting, because the invitation is short-lived"*. Both are answered,
and a third arrived that the step had pre-declared as a reading in case it happened.

**(a) Does a RAM invitation appear at all? No — zero, in both member accounts.**
`ram get-resource-share-invitations` returns an empty list in Sandbox and in Development. On the producer
side the baseline of four `LakeFormation-V4-*` shares is now **five**, the new one being
`DataZone-EXTENDED_ACCESS-dzd-d8yrvx1ko7im6o-ORG-ONLY`, `ACTIVE`, created 18:12 local. The name carries
the whole answer: `ORG-ONLY` is the share the user's *"AWS Organization-only RAM share"* choice produced,
and an organization-scoped share into an organization that has RAM sharing enabled (Stage 1d) raises no
invitation. **(b) follows from (a): there IS no accept step** — which is why the user found both member
accounts *"already associated"* rather than a request waiting. The 7-day expiry the V1 guide warns about
never starts running. Same shape as Stage 5's LF shares, and now measured for DataZone as well.

**(c) The RAM permission is not one of the two the step named, and neither of those exists.** RAM says
the share carries `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`, version 10, `ASSOCIATED`,
on `datazone:Domain` — read from `ram list-resource-share-permissions`, not from the console label.
`ram list-permissions --resource-type datazone:Domain` publishes **six**, and
`AWSRAMPermissionDataZoneDefault` / `AWSRAMPermissionDataZonePortalReadWrite` — the pair the step's table
named from the V1 user guide — are **not among them**. **That became Lesson 38** in the sitting that reviewed the plan against these findings: both were proper nouns quoted accurately out of prose, and one had already reached a Terraform module comment as load-bearing reasoning. What exists is a `...ExtendedServiceAccess` and a
`...ExtendedServiceWithPortalAccess` twin, plus the resource-type default
`AWSRAMDefaultPermissionAmazonDataZoneDomain`. **So the design's decision was honoured and its wording was
not**: the user's *"IAM users can access APIs only"* toggle is precisely the no-portal choice the step
demanded, expressed in the console's words rather than in the doc's.

**How much wider than the default it is, measured rather than feared.** The default carries **111**
actions and the one that landed **152** — a strict superset, nothing removed. The 41 extras are one
coherent family: notebooks, cells, cell runs, `StartCompute`/`StopCompute`, connections, plus
`GetDomainExecutionRoleCredentials` and `StartAccountBootstrapAction`. That is the **SMUS V2 workbench
surface**, which the V1-era default predates. The console did not over-grant by accident; it picked the
permission a V2 domain's members need.

**The step's sentence that this retires.** *"The member accounts need exactly one thing from this share,
`PutEnvironmentBlueprintConfiguration`"* is now known to be unachievable: RAM publishes nothing that
narrow for `datazone:Domain`, and the narrowest available is 111 actions deep and lacks the V2 half.
A share permission is a **ceiling**, and Lesson 28 is what keeps that from being alarming: reach is the
intersection of the RAM permission, the caller's IAM, and the SCPs. Measured on the IAM side — `datazone:`
appears in the persona sets **only** in `policies-approvers.tf`, as the approval verbs
(`AcceptSubscriptionRequest`, `Create`/`DeleteProjectMembership`, `Get*`/`List*`/`Search*`,
`Reject`/`RevokeSubscription`, the two `UpdateSubscription*`); `DataScientistAccess` names none at all.
On the SCP side, `DenyDataZoneEntirely` covers the **Workloads** OU in full and the Interactive OU carries
no `datazone:` deny, so in Sandbox and Development the constraint is IAM alone — and today no persona
reaches the wide half. **Recorded as a ceiling that widened, not as access that did.**

**(d) The functional proof, which no console label can give.**
`datazone list-environment-blueprint-configurations --domain-identifier dzd-d8yrvx1ko7im6o` **succeeds
from both member accounts** and returns `{"items": []}`. Before the association that call could not
succeed at all. Empty is the correct pre-1.4 state, and the *success* is the association working.

### The check that failed because the step succeeded

`./aws/studio.py` came back **`2 check(s) FAILED`** immediately after the association: `US-2`, *"DataZone
domain in awsds-infra-sandbox-1 — 1 domain(s) outside Data Governance"*, and the same in Development. It
was wrong, and the tell was that the failure arrived from the act that was supposed to work.

**Measured before being believed** — the domain visible in each member account is `dzd-d8yrvx1ko7im6o`,
and its **ARN names Data Governance**, not the local account, in all three accounts. There is one domain.
INT-12's fallback did not happen and the 1c root deny is holding.

**The defect:** `US-2` counted the rows `datazone list-domains` returns and treated any non-zero as *"a
domain was created here"*. The collection built a 4-tuple of `(id, name, version, status)` and **discarded
the ARN** — the only field that separates *visible* from *owned*. The premise held exactly as long as
nothing was shared; step 1.3 is the event that made it false. **Lesson 31, arriving as a false FAIL
instead of a false pass** — a check whose scope was inherited from the world it was written in.

**Fixed in the same sitting.** The owner is split out of the ARN and kept as element 4; `US-2` now fails
on a domain **owned** by a member account, passes with *"sees the shared domain and owns none"* when the
shared one is the expected `dzd-*`, and fails distinctly if some other domain is shared in from a place
nobody chose. Section 2 of the report gained an **OWNER** column reading `self` / `shared in`, and its
prose now says to read that column rather than the row count. Two further messages were made to follow the
measurement rather than a guess: `US-2`'s empty case distinguishes an account awaiting association from
one that is never associated (D28), and `US-3`'s note now points at **1.4** once it can see the shared
domain, instead of continuing to ask for a 1.3 that has already happened. **Battery re-run: 0 FAILED.**

### What was deliberately NOT done, and it looks like bookkeeping

**No row was added to `backend.SMUS_ASSOCIATED`.** It reads like the clerical half of 1.3 and it is the
**trigger** for the next two steps: it flips `blueprints_enabled` in both `sagemaker/` slices (1.4) and,
because it would then hold every member, `profiles_enabled` in `data-governance/governance/` (1.5). Both
slices already carry the gated resources, so the row puts an apply one command away — and that apply would
cross two gates this stage has open in writing: **decision 1 is reopened**, yet `category_one_blueprints`
already lists `EMRServerless` and would enable it, and **`AmazonBedrockGenerativeAI`'s `PRICING.md` row is
owed before the 1.4 apply** by the step's own text. The ordering also matters and is not encoded anywhere:
the two `sagemaker/` slices apply **before** `governance/`, because a project profile names blueprints that
must already be configured. Written down here so the next sitting starts from it.

## 2026-08-21 — Steps 1.4 and 1.5 RAN: twelve failures that were the provider's contract, two probes that bracketed it, and a base variant the service refused to bundle

**Claude's hand throughout, under the user's authorizations given in the sitting**: *"pode fazer o
apply"* for the step 1.4/1.5 applies; *"Sim, pode fazer o teste sugerido"* for the two write probes;
and the reclassification below in the user's own words. Every AWS write in this entry is one of those
three. The plan-facing consequences are the stage file's findings 7-11 — this entry is what happened.

### 1.4, first attempt — twelve for twelve, and the error contradicted a read

Recipe A on `sandbox/sagemaker/` (`sagemaker-prereqs-v0.2.0`): plan `12 to add`, apply — **all twelve
blueprint configurations failed**, each with

> waiter state transitioned to FAILED. StatusMessage: Managed Environment Blueprint with `<id>`
> doesn't exist.. ErrorCode: InvalidRequest

while `get-environment-blueprint`, same profile, same domain, same region, **answered for those exact
ids**. Nothing was created: re-plan read `12 to add` again and
`list-environment-blueprint-configurations` returned `{"items": []}`.

### The contract, measured three ways and bracketed by two authorized probes

The CFN page's `EnvironmentBlueprintIdentifier` is documented against **names** (*"only
`DefaultDataLake` and `DefaultDataWarehouse` are supported"* — V1-era names) with the resolved id in a
**separate** `EnvironmentBlueprintId` GetAtt; the awscc example passes the literal `"DefaultDataLake"`;
and the live type schema (`describe-type`) marks the identifier **createOnly + writeOnly**. The `aws`
provider's resource takes the id; the `awscc` one rides CloudFormation and takes the **NAME**. We fed
it ids, so the handler hunted for blueprints *named* like ids (Lesson 32).

Two probes, individually authorized, separated tool from world (Lesson 30): a plain-CLI
`put-environment-blueprint-configuration` for `Tooling` **with the id** — provisioning role, boundary,
two-subnet regional parameters — **succeeded**, was read back intact, and was deleted (`count: 0`); a
Cloud Control `create-resource` **with the name** `"Tooling"` returned `SUCCESS` with identifier
`dzd-d8yrvx1ko7im6o|4k186sfh08eqxc` — the name resolved to the id by the handler itself — and was
deleted the same way. The schema also showed `EnvironmentRolePermissionBoundary` is **write-only**:
boundary drift will never appear in a plan, so `US-8` is verification (v)'s sentinel.

### v0.2.2, and the fix cycle's scar

`sagemaker-prereqs-v0.2.2` passes the name, routed through the data source's `.name` so the roster
guard is a declared dependency (tflint had refused the dangling form — correctly). The cycle minted a
**stillborn `sagemaker-prereqs-v0.2.1`**: the tag was cut while commit 1 was still hook-blocked, the
failure hidden behind a piped exit code, so it landed on the previous `main` tip — v0.2.0 content
under a v0.2.1 name. Runbook §8 forbids moving tags; the version stepped forward and **nothing may
ever reference v0.2.1**. After the merge: `12 added` in Sandbox, `12 added` in Development, re-plan
`No changes` in both, 12/12 carrying the boundary — and `get-data-lake-settings` **byte-identical
before and after** in both members (verification (xiv)'s enablement half: enabling touches no
`DataLakeSettings`), the two-subnet parameters accepted (verification (iii)'s first half).

### 1.5, first attempt — the service refused the bundle, and the user re-cut the roster

`data-governance/governance/` second apply (`profiles_enabled` computed true by `gen-tfvars.py` from
`SMUS_MEMBERS ⊆ SMUS_ASSOCIATED`): plan `2 to add, 0 to destroy`, account pinning verified per profile
against `sts` without printing ids. **Both profile creates failed**, DataZone 400:

> ToolingLite environment blueprint configuration must have deployment mode ON_CREATE.

Nothing was created. The domain's own descriptions settled what that means — `Tooling`: *"Creates
resources for the project, including IAM user role, security groups, Amazon Athena workgroup for
querying data, and Amazon SageMaker domain."*; `ToolingLite`: *"Create basic resources for SageMaker
Unified Studio project."* — a second **BASE**, not a capability, exactly the shape `SMUS.md`'s row had
flagged for reading before trusting. **The user's decision, verbatim: "Reclassifique ToolingLite como
Categoria 3."** Decision 5 re-cut 12/5/6 → 11/5/7; `sagemaker-prereqs-v0.2.3` moved all three copies
of the list; the member applies each read `0 to add, 0 to change, 1 to destroy` — **11 configurations
stand per member**.

### 1.5, second attempt — done

`2 added`: `experimentation` → Sandbox, `engineering` → Development. Read back by
`get-project-profile` (the list call omits configurations — Lesson 13's shape, so the get answered):
**11 environment configurations each, `Tooling` the only base, `ON_CREATE`**, and the five locked
parameters non-editable — `sagemakerDomainNetworkType=VpcOnly`, `lifecycleManagement=true`,
`maxIdleTimeoutInMinutes=120`, `maxEbsVolumeSize=100`, `enableTrustedIdentityPropagationPermissions=false`
— with `idleTimeoutInMinutes=60` the one editable default. **Decision 2 is delivered as coded.**
`./aws/studio.py`: **0 checks FAILED** — `US-3` *"11 blueprint configuration(s) … all inside decision
5's category 1"* in both members, `US-4` *"experimentation and engineering exist"*.

**Left owed after this sitting**: 1.7's portal reading (user), 5.0's image push (user), passes 3-5.

## 2026-08-22 — Step 1.7 RAN and answered INT-16; the same click found two project profiles nobody could instantiate, and `grants.tf` closed it

**Two hands, and the split matters for every claim below.** The portal readings are the **user's**,
in their browser, and are quoted verbatim. Everything else — the read-only AWS calls, the
documentation, the code, and the one apply — is **Claude's**, under the authorizations given in the
sitting: *"Pode sincronizar e preparar a próxima etapa do plano"*, then the association decision in
the user's own words, then *"Pode realizar o apply. Faça commit e abra um PR."* The stage file's
findings 12-13 are the plan-facing consequences; this entry is what happened.

### Before the portal — the push procedure, written from measurements rather than from intent

The sitting opened by synchronising after PR #30 and preparing step 5.0. Preparing it turned up three
things the repository did not say, and one it said wrongly.

**The devbox was absent** (`./scripts/devbox.py status`: *"absent (nothing billing)"*), so the clean
build of 2026-08-21 was gone with its volume. `images/README.md` and step 5.0 described the build and
the push in consecutive sentences that read as two sittings; they are **one session**, because the
host is `[E]` and holds nothing. That reading costs a full rebuild, and it is now stated in three
places.

**No identity in Sandbox can push.** Both repository policies were read live: one statement each,
`AllowConsumerAccountsToPull`, granting the two Interactive accounts
`BatchCheckLayerAvailability`, `BatchGetImage`, `GetDownloadUrlForLayer`, `DescribeImages`. **Nothing
grants a push to anybody**, and nothing needs to — a same-account push is decided by the identity
policy alone. So the push is a Production principal's act and the credential has to travel to the
build host as a 12-hour ECR authorization token; the host's role stays without an `ecr:` permission.

**The ceiling permits it and denies its mirror image.** `awsds-org-scp-perimeter`'s
`DenyEcrPushOutsideOrganization` denies the four push verbs when `aws:ResourceOrgID` is *not* ours;
`awsds-org-rcp-perimeter`'s `EnforceOrgIdentitiesOnRegistry` denies `ecr:*` to principals outside the
organization. Neither sees an org identity pushing into an org registry.

**And the S3 gateway endpoint is not on the push path**, which was checked because the Sandbox
endpoint policy grants `s3:GetObject`/`ListBucket` on `prod-us-west-2-starport-layer-bucket` and no
`PutObject` — a shape that reads like a gap until AWS's own page is read: `ecr.dkr` is the Docker
Registry API and *"Docker client commands such as `push` and `pull` use this endpoint"*, while S3 is
what a container reaches to **download** layers (documented minimum: `s3:GetObject`). The Sandbox VPC
has **no interface endpoint of any kind** (the `egress/` slice is `[E]` and down), so the upload
leaves through the WireGuard `t3.nano` — the same path the build already pulled the distribution in
through, which is what makes it slow rather than novel.

One more read, so the procedure's safety claim is a measurement: the account has **no
`SSM-SessionManagerRunShell` document**, so Session Manager runs on defaults and no session stream is
logged — `read -rs` keeps the token off the screen and out of history, and nothing else records it.

All of it became [`devbox.md`](../plan/runbooks/devbox.md) **§P**, with `images/README.md`, step 5.0
and two pass-table rows corrected to match. **Step 5.0 itself did not run** and is still owed.

### 1.7 — the user's reading, verbatim

Asked for the procedure, Claude gave three readings — a positive control (a console call off VPN,
which must be denied), the portal off VPN, and the portal on VPN — because *"the portal opened"*
alone cannot distinguish a portal that is ungated from a deny that is not firing (Lesson 24). The
user took the second and third:

> o portal abriu normalmente com o túnel desligado, IP `<their carrier's address>`. Consegui logar
> com o sso user sandbox. Aparece opção para criar projeto novo, com perfil `engineering` ou
> `experimentation`. Porém, ao clicar em `Criar projeto` aparece a mensagem `User is not permitted to
> perform operation: CreateProject`. Habilitando VPN, IP `52.89.212.1`, e executando o mesmo
> procedimento, o resultado é exatamente o mesmo.

**The carrier address is deliberately not written down here.** It locates a person, and the
measurement is the *inequality* — that it was not the Elastic IP — not the literal.

Two things were then verified rather than assumed, because the reading is worthless without them.
**`52.89.212.1` is the Sandbox WireGuard Elastic IP** (`describe-addresses`, tagged
`awsds-sandbox-vpn`, attached to the running host), so the second leg genuinely exited through the
perimeter and the tunnel was full rather than split. And **the identity was a persona**: the domain
holds exactly **one `ACTIVATED` SSO user profile**, and that IdC principal is assigned — by group —
to `DataScientistAccess` in Sandbox and Development and `DataScientistProdAccess` in Production, both
of which carry `DenyControlPlaneOffVpn`.

**So INT-16 is answered, and the answer is its fallback (ii).** A `Deny *` on `*` would have refused
the `datazone:` reads that enumerated those two profiles from outside the perimeter; it did not, so
it does not reach the portal's session. What the control delivers is what `policies-shared.tf`
already refused to overclaim — VPN-only APIs and console, not a VPN-only portal.

**What is still missing is one cheap leg**, and it is recorded rather than glossed: the positive
control was not taken in the same sitting, so the attribution rests on the deny being in those two
sets *by code* plus the read-back of 2026-08-20, rather than on a same-minute contrast.

### The second half of the same click, which nobody had planned for

`User is not permitted to perform operation: CreateProject` — **identical with the tunnel up and
down**, which is the contrast that ruled the network out from inside the user's own observation. The
locating reads followed, all read-only through `awsds-infra-data`:

- `list-policy-grants` on the root domain unit: **empty list** for `CREATE_PROJECT` *and* for
  `CREATE_PROJECT_FROM_PROJECT_PROFILE`;
- `list-entity-owners` on the same unit: **one owner**, the group profile whose `rolePrincipalArn` is
  the `InfrastructureAccess` role that created the domain.

**Creating a project from a profile is an authorization, not a property of the profile** — listing
them is a read and needs neither — so the design had exactly one principal able to create a project
and it was the one that runs Terraform. Pass 3 was blocked before it began, and nothing in the stage
would have said so: step 2.4 says *"user provisions one throwaway project per profile"* and no step
created the authorization. `docs/SMUS.md` had carried the facet (*"which users/groups may create
projects from it"*) since it was written; it never became a step.

**Checked before being called a gap** (Lesson 8): `AWS::DataZone::PolicyGrant` is in the
CloudFormation registry, and `awscc_datazone_policy_grant` is present in the **pinned** awscc 1.98.0
binary — the same provider the slice already loads. The schema also settled the grain question:
`Principal` accepts a `Group`, the detail of `CREATE_PROJECT_FROM_PROJECT_PROFILE` takes a
`ProjectProfiles` list, and **every field is `createOnly`**.

### The user's decision, and what got asked before it

Asked what actually differs between the two profiles today, the answer was measured rather than
recalled: field by field, the two are identical in all eleven environment configurations — same
blueprint ids, same order, same deployment modes, same Tooling parameters — and **the only divergent
field is `awsAccountId`**, Sandbox against Development. The names promise a difference of *kind*
(D21) and today deliver a difference of *place*.

That reframed the grant: choosing who may create from `engineering` is choosing who may work
interactively **in Development**, which is the open half of D21. The user's decision, verbatim:

> Vamos de `CREATE_PROJECT_FROM_PROJECT_PROFILE`. `experimentation` fica com data scientists,
> `engineering` para deployment manager. Registre esta associação no `SMUS.md`.

Written up with the two halves distinguished — `experimentation` a standing right, `engineering` the
**instrument** of D21's open question, whose removal would be the expected outcome if that question
closes against the interactive surface.

### The code, and the apply

The association became a **column on the profile's own row** in the slice's `locals.tf`, not a second
structure beside it, so a profile cannot end up pinned to one account while its grant names another
(Lesson 33). `grants.tf` iterates that map. Two supporting pieces: a third read-only provider alias,
`aws.identity`, because Identity Center is delegated to the Identity account and the directory cannot
be read from Data Governance at all; and `identity_profile` emitted from
`scripts/tfhygiene/backend.py`, so no profile literal sits in a `.tf` file. The **group names** are
the decision and live in `locals.tf`; the ids are resolved from `DisplayName` on every plan, which
also turns a renamed or deleted group into a readable plan failure (Lesson 38).

Recipe A, as `awsds-infra-data`: plan **`2 to add`** → apply **`2 added`** → re-plan **`No changes`**.

**One named risk did not materialise.** Both groups show `status: None` in
`search-group-profiles` — no DataZone group profile has been created for either — and the grant was
expected to possibly refuse an unmaterialised group; the fallback, `awscc_datazone_group_profile`,
had been confirmed present in the pinned provider before the apply. The service accepted the IdC
group id directly.

**Read back through the API rather than off Terraform's state**, which is the half that matters:
`list-policy-grants` now returns two grants, `includeChildDomainUnits` false in both, and the pairing
is the decided one — the deployment-managers group against the `engineering` profile id, the
data-scientists group against `experimentation`. `./aws/studio.py`: **0 checks FAILED**.

No new `US-` check was added for this control, and the reason is that one is not needed: unlike the
environment-role boundary, a policy grant **is** readable, so Terraform's own plan is the drift
sentinel — a grant removed by hand comes back as `1 to add`.

### Files, and what is owed

Touched: `docs/plan/runbooks/devbox.md` (§P, new), `images/README.md`, `docs/SMUS.md` (the
installed-profiles table gains a fourth column, plus the new subsection the user asked for),
`docs/plan/stages/stage-06-unified-studio.md` (findings 12-13, step 2.4's prerequisite, step 5.0, the
owed table, two pass rows), `docs/plan/integrations.md` (INT-16 answered), `docs/REFERENCES.md`,
`CLAUDE.md`, and the governance slice — `grants.tf` (new), `locals.tf`, `data.tf`, `providers.tf`,
`variables.tf`, `outputs.tf`, plus `scripts/tfhygiene/backend.py`.

Owed after this sitting: **step 5.0's build and push, one devbox session** (§P); INT-16's missing
positive control, a minute's work; and then pass 3, which the grants have unblocked — **and whose
projects are now provisioned by each profile's persona, not by the infrastructure identity**.

---

## 2026-08-22 — Step 5.0's BUILD ran: both images clean in fifteen minutes, and the tag convention the first push will spend

**Two hands, and the split is the point of the entry.** The user brought the devbox up and gave the
authorization — *"O devbox está ativo. Pode fazer o passo 5.0?"* — and the **tag convention below is
their decision**. Everything else is **Claude's**: the readings, the build, and the doc changes.
**The push is not in this entry.** It had not run when this was written; it is the user's, §P
literal, on the host this build left standing.

### Why the sitting happened

It opened as a plan question — which pending Stage 6 verification uses the devbox — and the answer is
**verification (x)**, the only one whose step column names 5.0: its build-time half is the
activity-monitor assertion, its firing half is 8.1. The user then asked for the step itself.

### The state the host was found in, before anything was built

`./scripts/devbox.py status`: the devbox **running** and **Online** in Session Manager (agent
3.3.4624.0), the WireGuard host **running**, no probe instance — the refusal that matters was not
even close.

Four readings taken because the alternative was to assume them:

- **Both ECR repositories exist and are empty.** `IMMUTABLE`, KMS-encrypted, scan-on-push, and
  `describe-images` returns nothing in either — **no tag has been spent**, so pass 0 is applied and
  the first push is still free to choose its convention.
- **The build context was already on the host and is the repository's.** `/opt/awsds/images` was
  compared file by file against `images/` — **eight files, every md5 identical** — so no `sync` was
  needed and there is no question about *what* was built. `images/` is clean in git.
- **The host was clean**: no images, no containers, no build cache, 62 GiB free of 64.
- **The egress path is the designed one, measured rather than believed**: `curl` from inside the box
  returns the **WireGuard host's Elastic IP**, and that instance carries `SourceDestCheck: false`.
  The `[E]` route, the `[D]` masquerade and the `[P]` security-group rule were all doing their jobs
  at once, which is the intersection `devbox.md` §C says is easy to get wrong.

### The mechanism, and where it deviates from the runbook

§P's build is typed into an interactive `ssm start-session`; Claude cannot hold a TTY, so the build
was driven by **`ssm send-command`** — the same write API `devbox.py sync` and `vpn.py --on-host` are
fenced behind, under this sitting's authorization — and launched **detached under `systemd-run`**,
logging to `/var/log/awsds-build.log`, so a twenty-minute build does not depend on the invocation
that started it. Progress was polled with short Run Commands.

**Nothing about the push was sent this way, and that is deliberate.** Run Command parameters stay
readable from the command history for weeks, so relaying an ECR authorization token through it would
put a 12-hour credential exactly where §P's `read -rs` exists to keep it out of. The runbook's
procedure is unchanged and the push stays the user's act.

### The build

`base` **`exit=0` at 04:17:21Z**, about 4m45s. `dev-env` **`exit=0` at 04:27:35Z**, `BUILD DONE
rc=0` — roughly fifteen minutes end to end. `base` 12.1 GB and `dev-env` 17.5 GB by `docker images`,
which counts shared layers twice: `docker system df` de-duplicates them to **17.46 GB**, and the
root volume went to 19 GiB of 64.

### What the images were asked, rather than assumed

- **The activity-monitor assertion passed with a name and a version**, which is the half of
  verification (x) that lives at 5.0: *"== searching the base for the activity-monitor extension =="*
  then `jupyter-activity-monitor-extension 0.3.2 pyhd8ed1ab_1 conda-forge`. The distribution still
  ships it, so nothing was installed over it. **This does not answer (x)** — that idle shutdown
  *fires* is 8.1's measurement; what is closed here is the failure mode where the base quietly stops
  carrying the extension and the discovery arrives as an app billing overnight.
- **The BYOI entrypoint rule holds**: `Entrypoint=["/usr/local/bin/_entrypoint.sh"]`,
  `Cmd=["/bin/bash"]`, `User=sagemaker-user`, `WorkingDir=/home/sagemaker-user` — the distribution's
  own, inherited, neither `Dockerfile` having set one. Read from `docker inspect` and exercised by a
  `docker run --rm`, which is the same proof from the other side.
- **The CA layer is empty and says so**: *"CA roots found in the build context: 0 (expected 0)"* —
  D36 §3 as amended. Stage 7 step 2.6 fills the blank rather than editing a build.
- **The ancestor is recorded in the image**:
  `org.opencontainers.image.base.name=public.ecr.aws/sagemaker/sagemaker-distribution:4.3.0-cpu`
  with `base.digest=sha256:7f5d9c64684cebd53f65173c1f41d7bfe68419e5de9d0f55c4c25910a92f5f2c`.
- **The runtimes, from `/opt/awsds-runtimes.txt` inside the image**: Python 3.12.13, uv 0.12.5,
  Julia 1.12.7, R 4.5.3 (2026-03-11), rustc 1.98.0. **One thing that file does not carry**: it
  records `base image : awsds/base:local`, the build-time reference — not the ECR tag the image is
  given afterwards. The image cannot be asked what it was published as; only the digest chain can.

### The tag convention — the user's decision, and two corrections on the way to it

The tag had to be settled before the push because both repositories are `IMMUTABLE`: it is spent on
first landing, and Stage 8 step 1's pipeline inherits whatever the first push writes.

The user's requirement is the **flavour** axis — a project wanting GPUs, one wanting Spark libraries,
and one wanting neither are three runtimes — and their first proposal was `dev-env-default-v0.1.0`.
Two corrections were needed before it became the rule:

1. **The two repositories are not "production" and "development".** Both live in the Production
   account: `production/registry/ecr.tf` builds them as `awsds-${var.env}-ecr-*` with `env = prod`,
   and the consumer accounts hold a *pull*. The axis between them is **ancestor** (`base`, D17)
   versus **BYOI runtime** (`dev-env`), not environment.
2. **The repository already is the name**, so `dev-env-…` inside the tag spends it twice in every
   pipeline line that ever references it.

**Decided: `<flavour>-v<major>.<minor>.<patch>`, the same number in both repositories** —
`default-v0.1.0` first. The flavour axis reaches `base` too, because a GPU `dev-env` needs a GPU
ancestor; naming the plain one `default` from the start stops `v0.1.0` from silently coming to mean
*the CPU one*.

**And one of Claude's arguments was checked instead of asserted, which changed it.** Flavour-first
was offered on the claim that a lifecycle policy can only select tags by prefix; the page says
`tagPrefixList` does match a prefix only, but `tagPatternList` takes up to four `*` wildcards, would
match `*-gpu` just as well, and is the one AWS calls best practice. So flavour-first is **convenience
and grouping, not capability**, and `docs/SMUS.md` says that rather than the stronger claim. The same
read turned up the trap for whoever writes the first policy: the two selectors are mutually exclusive
in a rule, and multiple entries are an **AND**.

### Files, and what is owed

Touched, all documentation — **no Terraform, no apply, and the only AWS writes were the Run Commands
that drove the build**: `docs/SMUS.md` (new section, *Custom images (BYOI) — and how they are
named*), `docs/REFERENCES.md` (the ECR lifecycle-policy page, with the three sentences the argument
rests on), `images/README.md` (a pointer, so the convention has one copy and it is not there), and
`CLAUDE.md`'s routing row. `make check` **OK**; `./scripts/check-identifiers.py` **OK**.

Owed: **the push** — `default-v0.1.0` into both repositories, §P, **on this host while it is still
up**, because build and push are one session and a `down` in between costs the fifteen minutes
again. The host bills 0.1664 USD/h meanwhile. Both digests belong in this entry once they exist;
then pass 3, and 5.1's cross-account pull question (INT-01/INT-17, verification (vi)).

---

## 2026-08-22 — Step 5.0 CLOSED: the push ran, both tags spent, and `default-v0.1.0` exists in the registry

**Two hands, and the order tells them apart.** The section immediately below is the **user's** — the
procedure as they ran it, their commands and their pasted output, verbatim. The readings under
*"After the push"* are **Claude's**, read-only through `awsds-infra-prod` and `awsds-infra-sandbox-1`,
on the user's request to *"fazer as verificações pendentes"*. **Substitution, declared once for the
whole entry: `<Production Account>` replaces that account's twelve-digit id wherever it appeared in a
registry URI.** Nothing else in the pasted output is touched.

### The push — the user's hand, verbatim

- Let's test pushing to ECR. Login as infrastructure user on laptop.

```

$ aws ecr describe-repositories --profile awsds-infra-prod --region us-west-2 --query 'repositories[0].repositoryUri' --output text | cut -d/ -f1

<Production Account>.dkr.ecr.us-west-2.amazonaws.com/awsds-prod-ecr-dev-env     <Production Account>.dkr.ecr.us-west-2.amazonaws.com/awsds-prod-ecr-base
```

> **Claude's note, not a correction to the evidence:** the output above is the **two full repository
> URIs**, which is what `--query 'repositories[].repositoryUri'` returns — not what the command line
> above it produces, since `repositories[0]` plus `cut -d/ -f1` yields the bare host on one line. Both
> commands were offered in the same sitting and the paste pairs one with the other's output. The value
> actually used is the next block's, and it is the right one.

- read the session token:

```
$ aws ecr get-login-password --profile awsds-infra-prod --region us-west-2

(output ommited)
```

- starting ssm session:

```
./scripts/devbox.py ssm
```

- Define registry url:

```
REGISTRY=<Production Account>.dkr.ecr.us-west-2.amazonaws.com
```

- put token on variable:

```
read -rs ECR_TOKEN
```

- login:

```
echo "$ECR_TOKEN" | sudo docker login --username AWS --password-stdin "$REGISTRY" && unset ECR_TOKEN

WARNING! Your password will be stored unencrypted in /root/.docker/config.json.
Configure a credential helper to remove this warning. See
https://docs.docker.com/engine/reference/commandline/login/#credentials-store

Login Succeeded

sudo docker tag awsds/base:local "$REGISTRY/awsds-prod-ecr-base:default-v0.1.0" && sudo docker tag awsds/dev-env:local "$REGISTRY/awsds-prod-ecr-dev-env:default-v0.1.0"

sudo docker push "$REGISTRY/awsds-prod-ecr-base:default-v0.1.0"
sudo docker push "$REGISTRY/awsds-prod-ecr-dev-env:default-v0.1.0"
sudo docker logout "$REGISTRY"
```

**The warning in that paste is the reason the procedure ends with `logout`.** `docker login` writes
the token to `/root/.docker/config.json` in clear; the host is `[E]` and takes it to the grave either
way, but `logout` is what makes that a *choice* rather than a dependency on the teardown happening.

### After the push — Claude's readings, read-only

**Both tags landed, and they are now spent** (both repositories are `IMMUTABLE`, so a re-push under
either is refused from here on):

| Repository | Tag | Digest | Stored | Pushed (UTC) |
|---|---|---|---|---|
| `awsds-prod-ecr-base` | `default-v0.1.0` | `sha256:6c53def4fb30acbfff112e8c85c454019d96ca5a256eba563b455d21aeec5b3a` | 3,959,751,035 B | 05:21:51 |
| `awsds-prod-ecr-dev-env` | `default-v0.1.0` | `sha256:76d9b5e8b6b9ada94ba52ae27a8e9a43ba37e7196d0de46f5859cd2325cd3e56` | 5,648,737,291 B | 05:30:34 |

**The stored sizes are the compressed ones and §P's warning is confirmed from the other side**: 12.1
GB and 17.5 GB uncompressed on the devbox became 3.96 GB and 5.65 GB in ECR — and `dev-env` carries
its own copy of `base`'s layers, because ECR stores layers per repository. Two uploads, not one
deduplicated push.

**Scan-on-push ran, and the first reading of it was a trap worth writing down.** `describe-images`
returns **no scan field at all** for these images — not `IN_PROGRESS`, not null-because-pending: the
key is absent from the response — while `describe-image-scan-findings` answers `COMPLETE` for both.
A check written where a reader would naturally look would therefore report *"never scanned"* on a
scanned image, and would report the same thing if scanning were genuinely off (Lesson 13).
`./aws/supplychain.py` does not fall into it — it measures the *configuration* (`BASIC (no rules)`,
the legacy per-repository `scanOnPush: True`) and its own comment already names
`DescribeImageScanFindings` as what the Stage 8 gate must call.

**And the findings counts are identical in the two images**, which is the reading that matters more
than the numbers:

```
base     COMPLETE 05:23:55Z   CRITICAL 30  HIGH 430  MEDIUM 514  LOW 3  UNDEFINED 7
dev-env  COMPLETE 05:34:30Z   CRITICAL 30  HIGH 430  MEDIUM 514  LOW 3  UNDEFINED 7
```

`dev-env` is `base` plus Julia, R and Rust, and it contributed **exactly zero** findings: **basic
scanning reads OS packages only**, so it is blind to the three ecosystems this image exists to add,
and to the conda environment the Python stack lives in. That is Stage 7 decision 2's input measured
rather than argued — the counts themselves are the SageMaker Distribution's inherited debt (the
sampled MEDIUM was a Linux **kernel** CVE, which a container cannot exercise against the host's
kernel), so the number to watch after an ENHANCED upgrade is not this one.

**The consumer side answered for the first time against a real image.** `./aws/supplychain.py`:
**0 checks FAILED**, `SC-4` both repositories `IMMUTABLE`, and `SC-7` *"ECR cross-account read from
`awsds-infra-sandbox-1`: ok (1 image(s) visible)"* — the first exercise of
`AllowConsumerAccountsToPull` with something behind it. **This is visibility, not a pull**:
`DescribeImages` is one of that statement's four actions, and whether the layers actually come down
cross-account is 5.1's question (INT-01/INT-17, verification (vi)).

**One correction to a document written earlier in the same sitting, and the tool caught it.**
`docs/SMUS.md`'s new tag section said the lifecycle policy was still to be written; `supplychain.py`
reports `LIFECYCLE: yes` on both repositories, and `terraform-modules/ecr-repo` does build one — read
back live: **untagged expire at 14 days**, and **tagged kept to the most recent 30**, selected with
`tagPatternList = ["*"]`. The first draft had grepped the live slice and not the module that builds
it. The argument survives and gets sharper: **rule 2 counts every flavour together**, so the day a
`gpu-` image exists a burst of `default-` pushes evicts it, and rule 2 has to be split per flavour —
which is what the flavour segment makes expressible. `docs/SMUS.md` now says this.

### What this closes, and what it leaves

**Step 5.0 is DONE** — build and push, one devbox session, as §P requires. Pass 1 has no unfinished
step left, and **pass 3 is unblocked** (its other predecessor, the `grants.tf` apply, closed in the
previous entry).

**The devbox was still `running` when this was written**, at 0.1664 USD/h, with its images now
redundant — everything worth keeping is in ECR. `./scripts/devbox.py down` is the user's call and the
only thing standing between this sitting and 0 USD/h in Sandbox.

Owed next: **5.1** — image, image version, app image config, and the domain's `CustomImages`, which is
where the cross-account pull is answered rather than assumed.
