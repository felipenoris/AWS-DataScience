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
