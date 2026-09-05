# Stage 12 — Observability, governance and FinOps

| | |
|---|---|
| **Status** | not started — **rewritten 2026-09-05 into the action-checklist format** and re-scoped against [D38](../decisions/D38-single-egress-hub.md): the dashboards lose their NAT panels (there is no NAT), and gain three lines the hub creates — the **proxy's access log and its refusal rate**, the **DNS Firewall's per-query charge** in each compute VPC (whose job is now closing DNS exfiltration rather than filtering the internet, so if the query bill outweighs what it catches, retiring it is a decision this stage's reading informs), and the **peering bytes**, which the hub makes a real line for the first time |
| **Prerequisites** | any stage that created resources — and **one real invoice**, which is what separates this stage from a projection |
| **Consumes** | [D11](../decisions/D11-lab-lifecycle.md), [D12](../decisions/D12-budget-ceiling.md), [D38](../decisions/D38-single-egress-hub.md) |
| **Proves** | nothing new crosses an account boundary. What it **retires** is a set of estimates |

*Read with [`docs/plan/conventions.md`](../conventions.md) §5.1 (the three layers) and
[`docs/plan/cost-model.md`](../cost-model.md) (the projection this stage replaces with measurements).*

---

**Objective:** know what is running, what it costs, and be told when something breaks — from the bill, not
from the plan.

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls — done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write — only after the user authorizes that specific action in chat, with the SSO user / account / permission set stated first |
| **[user]** | the Billing console (Management only), the backup restore tests, and every log entry |
| **[Claude reads, user decides]** | a measurement Claude takes and a choice only the user can make |

## Step numbers are identifiers, not an order

Steps 1-3 are the observability half, 4-6 the cost half, 7-9 the governance half; **step 8 is the one with
a hard prerequisite** (a real bill) and step 3 the one with an irreversible floor.

---

## To execute

### 1. Build the dashboards — one per environment, and one for the hub

**Action:** a CloudWatch dashboard per account plus a hub dashboard. **Why:** every earlier stage measured
its own thing once; nothing shows the estate at a glance, and D38 made one account's two hosts a dependency
of every other account's session. **Explanation:** the panels are chosen so that a *stopped* hub host and a
*full* disk look different from each other — a dashboard where every failure looks the same is a screenshot.

- **1.1 — [Claude] Write the per-environment dashboard**: SageMaker app and job hours, Athena bytes
  scanned against the workgroup limit, GitLab instance and EBS, the `[E]` endpoint count, and — replacing
  the NAT panels that no longer have a resource — **the DNS Firewall query count** for that VPC.
- **1.2 — [Claude] Write the hub dashboard**: the WireGuard host's state and handshake age, the **proxy's
  request rate, its 403 rate and its top destinations**, and **peering bytes cross-AZ**. The 403 rate is
  the one panel that reads as a design signal rather than a fault: a rising refusal rate means the
  allow-list is behind the work.
- **1.3 — [Claude] Point every panel at a `[P]` log group or metric**, never at an `[E]` resource's id
  (Lesson 4) — a dashboard that empties on `make down` is a dashboard nobody trusts afterwards.

### 2. Wire the alarms to a human

**Action:** alarms to the Stage 1b SNS pattern for the failures nobody would otherwise notice. **Why:** D12
deliberately left the budget notifying nobody, and every stage since has added a thing that can fail
quietly. **Explanation:** each alarm names the runbook that answers it, or it is not worth creating.

- **2.1 — [Claude] Alarm the budget thresholds** — this is where D12's deferral is closed, with the real
  spend curve in hand rather than a guess.
- **2.2 — [Claude] Alarm the hub**: either hub host stopped while a spoke session is up, and the proxy's
  403 rate over a threshold. Both point at [`runbooks/vpn.md`](../runbooks/vpn.md) and `./aws/proxy.py`.
- **2.3 — [Claude] Alarm the pipelines and GitLab**: a failed promotion, a GitLab health-check failure, an
  unusual Athena scan volume.
- **2.4 — [Claude⚡] Apply, then [user] provoke one alarm of each class once** — an alarm that has never
  fired is a configuration, not an alarm (Lesson 13).

### 3. Set log retention everywhere — and respect the one floor that cannot be lifted

**Action:** an explicit retention on every log group. **Why:** the default is "forever", which costs money
quietly. **Explanation:** one retention in this estate is floored by a compliance-mode lock, and getting it
wrong is unrecoverable rather than merely expensive.

- **3.1 — [Claude] Set retention on every group this project creates**, including the proxy access log and
  the DNS query logs.
- **3.2 — [Claude] Do NOT shorten the organization CloudTrail bucket's lifecycle below 90 days.** Its
  objects carry S3 Object Lock in **compliance** mode at 90 days (Stage 1d step 9), and its lifecycle rule
  expires versions at 365. **Shortening it below 90 makes the landing zone's own expirations start failing
  against locked versions, and the lock cannot be shortened to fix it.** 365 → anything ≥ 90 is safe;
  below 90 is unrecoverable (`INV-14`).

### 4. Activate cost allocation and read the first real bill

**Action:** turn on the cost allocation tags and reconcile the invoice against
[`cost-model.md`](../cost-model.md). **Why:** every price in this project is measured (Lesson 6), but the
*quantities* have only ever been projected. **Explanation:** this is the step the whole stage exists for —
everything else is instrumentation around it.

- **4.1 — [user] Activate the cost allocation tags in Billing** (Management account, console only).
- **4.2 — [Claude] Reconcile the invoice line by line against `cost-model.md`**, and rewrite the model from
  the invoice rather than patching it.
- **4.3 — [Claude reads, user decides] Re-open the two estimates most likely to be wrong**: the interface
  endpoints (the largest hourly item, and since 6c there are more VPCs holding them) and GitLab's EBS (the
  largest idle item). Update `conventions.md` §5.1 with measured numbers.
- **4.4 — [Claude reads, user decides] Settle the DNS Firewall's per-query bill.** Its job changed at 6c:
  it no longer filters the internet, it closes the recursive resolver as an exfiltration channel. If the
  query charge outweighs what it catches, retiring it is a legitimate outcome — but it is a decision with
  a recorded reason, not a silent deletion.

### 5. Re-check the layer assignments against the bill

**Action:** confirm each slice's `[P]`/`[D]`/`[E]` letter still earns itself. **Why:** conventions §5.1
rule 7 says a layer choice is re-opened by measurement, and this is the first measurement.
**Explanation:** the likely movers are a `[D]` whose idle EBS costs more than its rebuild, and an `[E]`
that is up so often it may as well be `[D]`.

- **5.1 — [Claude] Produce the per-slice actual spend** from the invoice plus `make status`' history.
- **5.2 — [Claude reads, user decides] Propose any letter changes**, each with the arithmetic beside it.

### 6. Review the Config recorder scope against what it actually cost

**Action:** re-read Stage 1d step 10's decision with a bill. **Why:** the recorder was left alone on an
estimate of ~USD 0.5/month, and Management was deliberately left unrecorded. **Explanation:** a Config
conformance pack on top of the Control Tower guardrails is the natural next step **only if** the recorder's
real cost supports it.

- **6.1 — [Claude] Read the recorder's actual line** from the invoice.
- **6.2 — [Claude reads, user decides] Add conformance packs, or record why not.**

### 7. Tighten the permission sets against real usage

**Action:** narrow `identity/sso/` using IAM Access Analyzer **unused-access** findings. **Why:** a review
reports what a reader thinks the policy says; the analyzer reports what was granted and never exercised —
which is the question. **Explanation:** the personas were written narrow and then widened by six stages of
"the object now exists"; this is where the widening is paid back.

- **7.1 — [Claude] Enable an unused-access analyzer and read its findings** — note that it is a *different*
  analyzer from Stage 11's internal-access one, and priced differently.
- **7.2 — [Claude] Propose the removals**, then **[Claude⚡] apply `identity/sso/`** as
  `awsds-infra-identity`, `terraform output inline_policy_bytes` still under the ceiling.

### 8. Build backup and recoverability — the thing no earlier stage owns

**Action:** an org-wide AWS Backup plan, Vault Lock over it, cross-region copies, and a **tested** RTO.
**Why:** every earlier stage protected against a permission failure; none protects against deletion.
**Explanation:** an untested backup is a hypothesis, so each restore is walked once — the same discipline
Stage 7 step 8.2 applies to GitLab.

- **8.1 — [Claude] Write the org-wide backup plan** through an Organizations backup policy, covering the
  EBS volumes of the `[D]` instances (GitLab, both hub hosts).
- **8.2 — [Claude⚡] Apply Vault Lock on the backup vault**, so a compromised administrator cannot delete
  the backups. **Read the lock's own irreversibility before applying it** — this is the second
  compliance-mode object in the estate, and 3.2's lesson applies.
- **8.3 — [Claude⚡] Configure cross-region copies** for every account's state bucket and the GitLab backup.
- **8.4 — [user] State and test the RTO, once each**: GitLab (Stage 7 8.2 already measured it — reuse the
  number), the Terraform state, and the data lake. Write the three numbers in the log.

### 9. Alarm the quotas that would silently break a session

**Action:** review Service Quotas and alarm the ones with a session-breaking failure mode. **Why:** the
account quota that forced the 2026-09-05 re-scope was discovered by being refused, which is the expensive
way to learn a limit. **Explanation:** the candidates are the ones this estate has actually approached.

- **9.1 — [Claude] Read the current utilisation** for SageMaker instance limits, **Elastic IPs (the default
  is five per Region and the hub now holds two)**, VPC endpoints per VPC, and hosted zones.
- **9.2 — [Claude⚡] Set CloudWatch alarms** on each at 80 %, pointing at the request-increase path.

### 10. Write the instrument this stage has been missing

**Action:** a read-only `./aws/observability.py`. **Why:** every other stage since 2 is pre-instrumented,
and this one — the stage whose whole subject is *what is actually there* — has nothing. **Explanation:** it
is the last stage in the plan with no mechanical half, and the checks are cheap because the facts are all
`describe`-shaped.

- **10.1 — [Claude] Write the checks**: **`OB-1`** every log group this project creates carries an explicit
  retention (the sweep 3.1 is otherwise trusted to have done); **`OB-2`** the CloudTrail bucket's lifecycle
  is ≥ 90 days, which is `INV-14` made mechanical rather than remembered; **`OB-3`** every alarm has a
  notification target that resolves; **`OB-4`** the backup plan covers every `[D]` instance's volume, by
  reading `layers.py`'s `[D]` rows rather than a second list (Lesson 14); **`OB-5`** each quota in 9.1 is
  under 80 % of its limit.
- **10.2 — [Claude] Add it to [`aws/INDEX.md`](../../../aws/INDEX.md)** with its profile and its snapshot
  path, in the same commit as the script.

---

## Deliverables

- Dashboards per environment and one for the hub, every panel on a `[P]` source.
- Alarms wired to a human, each provoked once.
- Explicit retention on every log group, with `INV-14`'s floor respected.
- **`cost-model.md` rewritten from an invoice** rather than patched — the stage's central artifact.
- A backup plan with Vault Lock, cross-region copies, and three tested RTO numbers.
- **`./aws/observability.py`** — the mechanical half this stage did not have.

## Validation

1. Provoke one alarm per class and confirm the notification arrives (2.4).
2. Restore one backup of each kind (8.4) — a restore that has never run is not a backup.
3. Diff `cost-model.md` before and after 4.2; every changed row names the invoice line that changed it.
4. Run `./aws/observability.py` — `OB-1`..`OB-5` pass.

## Risks

- **Shortening the CloudTrail lifecycle below the 90-day lock is unrecoverable** (3.2, `INV-14`).
- **Vault Lock is the second irreversible control in the estate** — read its own documentation on the
  compliance-mode transition before applying, not after.
- **A dashboard on an `[E]` id empties at the first `make down`** (Lesson 4) — 1.3 is the control.
- **The unused-access analyzer bills per resource** like Stage 11's internal-access one; read the price
  before enabling it standing (Lesson 6).

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
