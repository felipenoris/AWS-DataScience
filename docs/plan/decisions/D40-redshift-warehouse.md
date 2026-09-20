# D40 — A Redshift Serverless warehouse beside the lake, built by hand and never by blueprint

**Status:** Decided (2026-09-19, user): the estate gets a Redshift Serverless warehouse, at the documented
floor of **4 base RPUs**, holding two classes of database — **governed**, written only by a Production
workload, and **sandbox**, written by SageMaker project roles under a grant made per database × project.
The `RedshiftServerless` and `LakehouseCatalog` **blueprints stay disabled**, and the D26/D12 argument that
disabled them is unchanged.

**In one line:** what D26 and D12 refused was a warehouse **any project member could provision in one
click**, and refusing that is compatible with building **one** warehouse whose capacity, cost ceiling and
grants are written down here.

**Related decisions:** [D12](D12-budget-ceiling.md), [D13](D13-lake-formation-enforcement.md),
[D17](D17-interactive-vs-runtime.md), [D22](D22-data-governance-account.md),
[D26](D26-unified-studio.md), [D31](D31-approver-read.md), [D35](D35-sandbox-cardinality.md)

**Referenced by stages:** [Stage 5b](../stages/stage-05b-redshift-serverless.md),
[Stage 6h](../stages/stage-06h-redshift-connection.md), [Stage 9](../stages/stage-09-deployment-targets.md),
[Stage 11](../stages/stage-11-dlp.md) (the audit-log feed), [Stage 12](../stages/stage-12-observability-finops.md)

---

## What is being reversed, and what is not

`docs/SMUS.md`'s blueprint table carries `RedshiftServerless` as a **Never**, on the strength of D26 and
D12, and `docs/GOVERNANCE.md` said *"No warehouse is built here"*. The user asked for a warehouse on
2026-09-19, **in chat — `objectives.md` does not carry it yet**
([Stage 5b](../stages/stage-05b-redshift-serverless.md) step 0.0 is where it does). Reading the exclusion's
own words decides how much of it has to go.

**What that file already says about a warehouse is the thing to revise, and it is not silence:** *"Use AWS
Glue Data Catalog with data stored on S3 buckets, using ICEBERG format, as Data Warehouse."* This decision
reads that as **still true** — the lake remains the warehouse of record, D13 still enforces it, and Redshift
is a second engine with a store of its own beside it. If the requirement means Redshift *replaces*
Iceberg-on-S3 as the warehouse, this decision is the wrong one and D13, D22 and the producer path re-open
rather than extend. 5b step 0.0's table is where that fork is put to the user.

D12's argument was a **per-query RPU minimum on top of Athena's bill**, and it is correct: at
**USD 0.36/RPU-hour** in `us-west-2`, four RPUs bill **USD 1.44 for every hour a query is running**
(`docs/PRICING.md` §5, read 2026-09-19). D26's argument was that a blueprint puts the object **one click
from a project member**, sized by the service, with no central cap — the same argument that put
`LakehouseAdmin` in category 2 and `EmrOnEc2` in category 3.

Those two arguments separate cleanly:

| | The blueprint | One hand-built warehouse |
|---|---|---|
| Who creates it | any project member, per project | Terraform, once, in a `[P]` slice |
| How many exist | one per project that asks | one per account that has one |
| Base capacity | the blueprint's default (**128 RPUs** is the service default) | `base_capacity = 4`, in code |
| Cost ceiling | none | `max_capacity` **and** a `redshift-serverless` usage limit with `breach_action = deactivate` |
| Who may write which database | whatever the blueprint grants | a `GRANT` per database × project, registered |

**So the blueprints stay disabled** — the row in `docs/SMUS.md` keeps its `Never` and its `US-3` failure
message, with its trigger reworded to name this decision rather than D26/D12 — and the warehouse arrives
as an *existing compute resource* that a SageMaker project reaches through a **connection**
([Stage 6h](../stages/stage-06h-redshift-connection.md)). That is the same shape Stage 16 used for the
sandbox lake: the portal mounts something Terraform owns, rather than provisioning something nobody sized.

## 4 RPUs, and why the number is not arbitrary

**4 is the documented floor**, and it is available in `us-west-2` — one of the ten Regions AWS lists
(`docs/REFERENCES.md`, the 2026-09-19 Redshift rows). Base capacity takes 4, then units of 8 from 8
upward, so **there is no value between 4 and 8**: the next step up is a doubling of the hourly rate.

What 4 RPUs buys, from the same page: 64 GB of memory, up to 32 TB of Redshift Managed Storage, and a
recommendation of **at most 100 columns per table**. All three are far above this lab.

Two properties of the floor shape the rest of the design:

- **AI-driven scaling is not recommended at 4 base RPUs** — AWS says so explicitly — and yet the
  price-performance target *"is enabled by default for all new Serverless workgroups and is set to
  **Balanced**"*. The default therefore contradicts the recommendation for the only capacity this estate
  uses, so the target is set deliberately rather than left alone.
- **The ratchet.** *"Once you scale your data warehouse beyond 4 RPUs, your data warehouse will continue to
  use more RPUs, and Amazon Redshift won't scale your data warehouse back down to 4 RPUs."* One expensive
  query therefore moves the floor permanently, and nothing in the billing data announces it. This is why
  `max_capacity` is set, why the usage limit exists, and why `ComputeCapacity` gets an alarm
  ([Stage 5b](../stages/stage-05b-redshift-serverless.md) pass 3).

## Nothing at rest, and what makes that stop being true

Compute is metered per second with a **60-second minimum charge**, and a workgroup serving no query bills
no compute. That makes a workgroup `[P]` in shape — like MWAA Serverless under D7 amended — with only
Redshift Managed Storage billing at rest, **USD 0.024/GB-month**: cents.

The three documented ways an idle warehouse bills anyway are all named so an instrument can look for them:

1. **An open transaction.** *"If you don't end or roll back an open transaction, Amazon Redshift Serverless
   continues to use RPUs."* `SESSION TIMEOUT` ends an idle session at 3600 s and an open transaction at
   21600 s — six hours of RPUs, which at 4 RPUs is **USD 8.64**, from one forgotten `BEGIN`.
2. **Connection pooling.** *"Amazon Redshift Serverless treats all incoming queries as billable user
   activity, including lightweight health-check queries sent by connection pools."* A `SELECT 1` keep-alive
   is a billed query.
3. **A cancelled query.** *"If you run a query and cancel it before it finishes, you are still billed for
   the time the query ran."*

None of these is a reason not to build it; each is a reason the cost guards are part of the build rather
than of Stage 12.

## The classes of database, and why they do not share an account

The requirement names two classes. The account is the only hard boundary in this estate
(`README.md` §Account segregation), and the two classes are on the two different axes this plan already
separates:

| Class | Written by | Lives in | Stage |
|---|---|---|---|
| **sandbox** | SageMaker project roles, per database × project | `Sandbox` — `sandbox/warehouse/` | [5b](../stages/stage-05b-redshift-serverless.md) builds the warehouse, [6h](../stages/stage-06h-redshift-connection.md) the first database |
| **governed** | a Production workload alone | `Production` — `production/warehouse/` | [9](../stages/stage-09-deployment-targets.md) builds both |

**One namespace holding both was considered and declined on two documentation readings.** Neither is a
measurement — nothing has been applied — so both are named with the page they come from, and both are
verifications [Stage 5b](../stages/stage-05b-redshift-serverless.md) and
[6h](../stages/stage-06h-redshift-connection.md) have to answer for real.

- **A namespace is not a boundary between its databases.** The cross-database query page says, of an
  unconnected database, *"you have read access only to those database objects"* and, two bullets later,
  *"You can write from databases that you are connected to, and also write from any other database that you
  have permissions to."* The page carries both sentences, so the boundary between a governed and a sandbox
  database in one namespace is **the `GRANT` and nothing else** — no account line, no policy layer, no
  Lake Formation. Lesson 41's shape, on one page.
- **JupyterLab needs the warehouse in the project's own VPC.** AWS: *"If you want to query the Amazon
  Redshift resources using JupyterLab within Amazon SageMaker Unified Studio, the Amazon Redshift resource
  must use the same VPC as the Amazon SageMaker Unified Studio project."* The project's VPC is Sandbox's,
  and **Sandbox does not peer with `VPC-Workloads`** — an absence `docs/NETWORK.md` §3 keeps as a control.
  So a single namespace either sits in Sandbox, putting governed data in the least-governed account against
  D22 and D17, or sits in Production, where no notebook can reach it.

Two warehouses cost no more than one at rest: compute meters per query and storage per namespace, so the
second namespace adds cents, not a second floor.

**What the split costs, and it is a real cost.** A governed warehouse in Production is the **first governed
store outside Data Governance**, which is D22's line. The compensation is that the governed namespace is
**registered to the Glue Data Catalog as a federated catalog**, so Lake Formation governs its schemas and
tables exactly as it governs the lake's — the shape
[`institutional-delta.md`](../institutional-delta.md) already described as the institutional answer, now
half-built. The grantor for those tables is Production rather than Data Governance, so the grant register
gains a second grantor account; Stage 9 owns that consequence. Giving Data Governance a VPC to keep one
grantor was declined for the same reasons D26 declined it for INT-13: a CIDR, two peerings, a child zone
and an `egress/` slice, bought for tidiness.

## D13 is not weakened, and the reason has to be written down

D13 says a principal running a query holds **no S3 permission on Lake Formation-registered prefixes**, or
every filter is decoration. A Redshift namespace introduces a new principal — the IAM role attached to the
namespace, which `COPY`, `UNLOAD` and the auto-mounted `awsdatacatalog` database run as — and that role is
exactly the kind of principal D13 is about. **It holds no S3 on any lake prefix**, in either account, and
its reach into the catalog is whatever Lake Formation grants it and nothing else
([Stage 5b](../stages/stage-05b-redshift-serverless.md) 2.4).

Redshift's own read of the Data Catalog is read-only by documentation — *"Queries against the
`awsdatacatalog` database can only be read-only"* — so the warehouse cannot become a write path into the
lake that bypasses the producer path.

## Cost

Measured 2026-09-19 from the Price List bulk API, offer file published 2026-09-11
(`docs/PRICING.md` §5):

| Item | `us-west-2` | `sa-east-1` | Ratio |
|---|---|---|---|
| Redshift Serverless compute | **0.36 USD/RPU-hour** | 0.5976 | 1.66 |
| — at `base_capacity = 4` | **1.44 USD per query-hour** | 2.3904 | |
| Redshift Managed Storage (serverless) | **0.024 USD/GB-month** | 0.043 | 1.79 |
| A workgroup serving no query | **0.00** | 0.00 | |

At the USD 50 ceiling this is **the most expensive thing in the estate per unit of time** — 1.44 USD/h
against the WireGuard host's 0.0052 and the whole `egress/` estate's 0.410. Ten hours of querying in a
month is 14.40 USD, roughly a third of the ceiling. The guard is therefore a **hard** one: a usage limit
whose breach action is `deactivate`, not a budget notification (D12's own open defect, which
[Stage 6e](../stages/stage-06e-claude-code-bedrock.md) 8.3 re-opened).

## Revision trigger

- **The usage limit fires more than once.** That means the design is under-capacity rather than
  mis-configured, and the question becomes 8 RPUs with a re-priced ceiling — not a bigger limit.
- **A query pattern Athena serves adequately.** If the warehouse's only queries would have run on Athena at
  5.00 USD/TB, the warehouse is paying an hourly rate for a per-scan workload and should go.
- **The governed class stays empty past Stage 10.** A warehouse with one class of database is one
  namespace, in Sandbox, and `production/warehouse/` should not be built to hold nothing.
- **Trusted identity propagation becomes affordable** (open question 13). TIP carries the Identity Center
  user into Redshift, which would replace the per-project database user of
  [Stage 6h](../stages/stage-06h-redshift-connection.md) with a per-person identity — and `--enable-trusted-identity-propagation`
  exists **per connection**, not only per project profile, which is new information against that question's
  premise.

---

*Decision index: [INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
