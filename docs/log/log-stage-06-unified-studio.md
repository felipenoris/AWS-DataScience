# Log — Stage 6 — SageMaker Unified Studio

*Manual actions performed in AWS, by hand. Written cooperatively by the user and Claude — **Claude
only when the user asks, never on its own initiative** ([`INDEX.md`](INDEX.md), which also carries the
provenance rule). **An entry carrying no provenance note of its own is the user's.**
Stage: [`docs/plan/stages/stage-06-unified-studio.md`](../plan/stages/stage-06-unified-studio.md).*

*Provenance is named by SUBJECT rather than by ordinal — the convention
[Stage 3's log](log-stage-03-networking.md) adopted and every stage since has kept. Identifiers are
redacted as `scripts/check-identifiers.py` requires, with the substitutions declared once per entry.*

*File initialized 2026-08-19 on the user's request. **The stage has not opened**: it is initialized early
because two of its five execute-time decisions were settled before it, and the stage file says those
decisions are recorded here (Lesson 16).*

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
