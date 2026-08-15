# D21 — The Development account, and where experimentation ends

**Status:** Decided (2026-08-08): **a dedicated Development account; Sandbox becomes pure experimentation; the promotion chain starts in Development.** **Re-examined 2026-08-13 and held unchanged** — what came out of that review is a named test and a revision trigger, recorded below, not an amendment.

**In one line:** A Development account: Sandbox becomes pure experimentation and the promotion chain starts in Development.

**Related decisions:** [D17](D17-interactive-vs-runtime.md), [D18](D18-data-scientist-access.md), [D19](D19-derived-zone.md), [D22](D22-data-governance-account.md), [D23](D23-ou-structure.md), [D26](D26-unified-studio.md), [D35](D35-sandbox-cardinality.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 1c](../stages/stage-01c-preventive-policies.md), [Stage 3](../stages/stage-03-networking.md), [Stage 6](../stages/stage-06-unified-studio.md), [Stage 8](../stages/stage-08-cicd-pipelines.md), [Stage 10](../stages/stage-10-orchestration-promotion.md)

---

## The distinction this restores

The AWS MLOps roadmap draws a line that the previous revision had collapsed "because there is one user":

- **Experimentation (Sandbox)** — the unit of work is a **notebook**. No versioning expectation, nothing
  survives, cost is spasmodic and human-driven.
- **Development** — the unit of work is a **pipeline**. A repository with tests, a SageMaker Pipeline, git,
  CI, and the expectation that running it again on Tuesday gives the same answer.

## What the boundary buys, even with a single operator

1. **The promotion chain gets an honest origin.** What enters CI is already repository-shaped, so the
   pipeline never has to pretend a notebook is an artifact.
2. **The graduation step becomes visible.** Leaving Sandbox is a deliberate act — a git commit into a
   Development repository — not a gradual blurring inside one account.
3. **Cost attribution separates exploration from engineering**, which is the split a real budget
   conversation needs.

## What Development is

- A second **Interactive-OU** account, with a Studio domain (VPC-only, the same module as Sandbox).
- A derived zone of its own (D19), and an LF read share from the lake (D22).
- Peered to Production for GitLab.
- The place SageMaker Pipelines are **authored and test-run** before the pipeline promotes them.

## What Development is not

- **Not a deployment target** — humans work here interactively.
- **Not a staging area** — its runs prove the *pipeline* works, not that the *artifact* deploys.

## Graduation is git, not a pipeline

- Sandbox → Development is a **rewrite**: the notebook's logic is rewritten into the repository, reviewed
  and committed.
- There is deliberately **no automated path** that lifts a notebook out of Sandbox — **the rewrite is the
  quality gate**.
- Promotion is Development → Staging → Production, and it never starts in Sandbox.

---

## Re-examined 2026-08-13 — does Development need an interactive surface at all?

**The decision is held as written.** This section records the reasoning so the question is not re-derived
from scratch the next time it is asked, and so the thing that would actually settle it is written down.

### Two questions, and they turn on different facts

The review conflated them once; keeping them apart is what makes either one answerable.

| Question | What settles it |
|---|---|
| Does Development need an **interactive surface**? | **The data test** below. It is a question about duplicated tooling |
| Should Development be the **origin of the promotion chain**? | **Who carries the code convergence** — see below. It is a question about where the promotion anchors |

**The data test does not reach the second question**, and this is the trap: Development's role in the chain
was never to be where the data is, it was to be the **funnel** — N sandboxes converge on one Development,
one Staging, one Production. Finding that Sandbox holds the same data removes the duplicated Studio and says
nothing about the funnel. Answering the first question does **not** license acting on the second.

### The funnel is a repository namespace, not an account (settled 2026-08-13)

The second question was first written as *"it turns on N"*, on the reading that N sandboxes deploying into
Staging would multiply the trust paths into it. **That reading was wrong on the mechanism**, and correcting
it is what produced the answer:

- **The deploy path does not multiply with N.** The runner lives in Production (D14) and assumes **one**
  deploy role in Staging. A Sandbox is where the person was sitting when they committed; it is not in the
  deploy path at all. What multiplies is **artifact streams**, not credentials and not trust directions.
- **What the funnel actually buys is a place where N units' work meets *as code*** — one review, one
  standard, a home for shared libraries — and that is a **GitLab group**, which lives in Production and in
  no environment account.
- **Remove the funnel from git and three things break together:** Staging is where two units first meet, and
  they meet as *deployed artifacts* rather than as code; `terraform-live/staging/app/app-etl/` is one state
  and one set of resources, so N streams either collide or force Staging to namespace per unit — the
  multiplication does not vanish, it lands somewhere less free than upstream; and a shared transform needed
  by two units has no owner.
- **Remove it from AWS but keep it in git and none of them break**, because convergence has already happened
  before the tag. The chain reads: N sandboxes → one shared repository namespace → tag → Staging.

**So the deciding fact is narrower than N.** If a shared repository namespace carries the convergence, the
Development *account* has only two residual jobs — cost attribution (benefit 3), plausibly carried by tags
instead, and being a runtime target for data Sandbox does not hold, which is the data test again. Neither
holds a whole account on its own, and **Sandbox → Staging becomes defensible even with N > 1**.

**One correction to carry, on how expensive the reversal is.** Rebuilding the funnel later is not expensive
because of the *account* — Account Factory vends it and [Stage 14](../stages/stage-14-sandbox-vending.md) is
already the machinery for exactly that. It is expensive because of **repository structure and habit**: N
units that each grew their own layout, CI configuration and Terraform tree are N divergent structures to
merge. The irreversibility is structural and social, not technical — which also says where to spend the care
if the branch is ever taken.

### Back to the first question, in D17's vocabulary

SageMaker is two halves and D17 runs the account boundary between them.

- Development needs the **runtime** half without argument: pipeline executions, training and processing
  jobs, and the by-hand apply of `terraform-live/development/app/app-etl/` against its own data (Stage 8).
- The open question is only the **interactive** half — the domain, the spaces, the apps.

It is a live question because **everything the person does to *author* is already available in Sandbox**: a
notebook, a VS Code space, the visual workflow and ETL tools, an export of the pipeline definition, and a
git commit. And the commit triggers CI **on the Production runner (D14), not in Development** — CI then
assumes a deploy role *into* Development. So Development certainly needs a deploy role; whether it needs a
Studio is a separate claim.

### What holds the interactive surface in place today

| Where | What depends on it |
|---|---|
| [Stage 6](../stages/stage-06-unified-studio.md) | the `engineering` project profile, whose ML blueprint provisions a SageMaker AI domain **into** Development |
| [D18](D18-data-scientist-access.md) | "Sandbox and Development — read-write, interactive, the D19 derived zones; this is where the person works" |
| [D19](D19-derived-zone.md) | a per-principal derived zone, with its own CMK, in **each** Interactive account |
| [Stage 8](../stages/stage-08-cicd-pipelines.md) | `awsds-deploy-devenv-dev` — half of INT-18 exists to deliver the `dev-env` image to Development's Studio |

### What argues the other way

- **No data difference is declared anywhere.** Both accounts read the lake through the same LF share, both
  have a derived zone, both are read-write for the same `DataScientistAccess`, both are associated with the
  same unified domain. Development's interactive surface is a **duplicate** of Sandbox's.
- **So the notebook/pipeline distinction is one of *discipline*, which an account boundary does not
  enforce.** Nothing stops an exploratory notebook in Development or a pipeline in Sandbox — the account
  does not know what the unit of work is (Lesson 5).
- **Two of the three benefits above are carried by something other than the account.** Benefits 1 and 2 are
  properties of the **git repository**, which lives in GitLab in Production: a commit from a Sandbox VS Code
  and one from a Development VS Code are the same commit. Stage 6 already names the enforcing thing — the
  **project profile**: *"it stops being which URL the person opened and becomes a property of the project
  they opened."* Only benefit 3 is carried by the account, and it survives without a Studio, because
  pipeline executions are still billed where they run.
- **The plan already treats Development's interactive surface as second-class.** It has no shared filesystem
  at all — D24 puts EFS in each unit's Sandbox — and its exchange with Sandbox is S3 and git.

### The discriminating test — it is about data, not about tooling

> **Is there anything a person must do next to *Development's* data that they cannot do next to
> *Sandbox's* data?**

- **Today the plan names nothing.** If it still names nothing once Stage 5 fixes the actual grants, the
  interactive surface in Development is redundant.
- **If something does appear, the decision was never about interactivity** — it is about **data grants**,
  which is a far better place to argue it.
- **The one real cost of removing it is the feedback loop.** A pipeline exercisable only through
  commit → runner → logs iterates slowly, and data-science pipelines fail for *data* reasons — schema,
  nulls, cardinality, distribution — that are much faster to diagnose sitting beside the data. That
  diagnosis can happen in Sandbox **only if Sandbox holds the same data**, which is the same test again.
  The pattern for everywhere else already exists in D17: debugging a failed run is a time-boxed elevated
  role with an approval, not a standing notebook.
- **One assumption to measure before relying on "author everything in Sandbox":** that SMUS visual workflow
  and ETL artifacts export to a git-committable definition CI can consume. That is D28's contract and it is
  **unverified** — if the export is not clean, "export and commit from Sandbox" silently becomes "rewrite by
  hand", which is a different decision.

### If the test ever answers "nothing" — what moves

- **D17's invariant sharpens.** Development keeps the runtime and loses the domain, so the sentence becomes
  *humans run code in Sandbox and nowhere else* — one account class with interactive compute instead of two.
- **The account leaves `Interactive` for `Workloads`**, whose set already denies `sagemaker:CreateDomain`,
  `CreateUserProfile`, `CreatePresignedDomainUrl`, `CreateSpace`, `StartSession` and `datazone:*`. The
  intention becomes a **control** rather than a convention (Lesson 5).
- **Files that would be revised:** this one (benefit 1 moves to Sandbox), **D17**, **D18**, **D19**, **D23**
  (`Interactive` collapses onto `Sandboxes`), **D26** and Stage 6 (domain associations become N, not N + 1;
  the `engineering` profile changes target or disappears), **D35**, Stage 8 (INT-18 loses half) and
  Stage 10.
- **The cost model barely moves, and an earlier draft of this section said otherwise.** Losing the Studio
  does **not** return Development's interface endpoints: the account keeps running pipeline jobs, those jobs
  are VPC-only, and the endpoints are what they resolve through — which is the term that dominates
  `docs/plan/cost-model.md`. What is saved is the domain and its apps, which are `[E]` and idle-cheap anyway.
  **The endpoints only come back in the larger branch below**, where the account leaves the chain entirely.
  Stating it the other way makes the cheaper, likelier move look like the one that pays.

### The larger branch — CI/CD deploying from Sandbox into Sandbox

If experimentation shows the two accounts are barely distinguishable in practice, the move is not just
"Development without a Studio" but **Development out of the chain**:

- The commit made in Sandbox triggers the Production runner, which **applies straight back into Sandbox** —
  the account the person is already working in.
- The promotion chain shortens to **Sandbox → Staging → Production**, and Development stops being the
  pipeline's test target rather than merely losing its Studio.
- **Its precondition is the shared repository namespace above**, not the data test. Taken without one, this
  is the branch that scatters N divergent repository structures and makes the reversal expensive.
- **One objection survives and it is worth keeping:** it puts CI-applied infrastructure in the account with
  the loosest policy set and the widest human access. That is an argument about *where an apply runs*, and
  it is unaffected by anything above.
- **The objection that does not survive, recorded so it is not raised again:** that removing the account
  removes the visible graduation act. The account boundary never *enforced* the rewrite — it prompted it,
  and a prompt is not a control (Lesson 5). What carries the act is an immutable tag on a reviewed
  repository, which is in GitLab either way.

### Why this stays open, and what would close it

- **Nothing is blocked by leaving it open.** The accounts are vended and the OU tree is built; what the
  answer changes is Stage 6's project profiles and which OU an empty account sits in.
- **The cheap moment has not passed, but it is passing.** Stages 3, 5 and 6 have not run, so today the
  change is prose. After Stage 6 it is a domain, a blueprint and an OU move.
- **Revision trigger:** the test above being asked with **real grants in place** — that is, once Stage 5
  settles what Sandbox and Development may each read — or a first stretch of real work in Development that
  reports nothing Sandbox could not have done.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
