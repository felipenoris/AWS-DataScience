# Stage 12 — Observability, governance and FinOps

| | |
|---|---|
| **Status** | not started **Amended 2026-09-05:** two new lines to read against the first real invoice — the **DNS Firewall's per-query charge** in each compute VPC, now that its allow-list is intranet-only and its job is closing DNS exfiltration rather than filtering the internet (if the query bill outweighs what it catches, retiring it is a decision this stage's reading informs), and the **peering bytes**, which the hub makes a real line for the first time. |
| **Prerequisites** | any stage that created resources. |
| **Consumes** | — |
| **Proves** | — |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** know what is running, what it costs, and be told when something breaks.

**Prerequisites:** any stage that created resources.

**To execute:**

1. CloudWatch dashboards per environment (SageMaker, GitLab, VPN, NAT traffic, Athena scans).
2. Alarms → SNS → e-mail for: budget thresholds, failed pipelines, VPN down, GitLab unhealthy,
   unusual data scans.
3. Log retention policies everywhere (default retention is "forever", which quietly costs money).
   **One retention here is floored and the floor cannot be lifted:** the organization CloudTrail bucket
   in Log Archive carries S3 Object Lock in **compliance** mode at 90 days (Stage 1d step 9, decision 3),
   and its lifecycle rule expires versions at 365 days. **Shortening that lifecycle below 90 days makes
   the landing zone's own expirations start failing against locked versions, and the lock cannot be
   shortened to fix it.** 365 → anything ≥ 90 is safe; below 90 is unrecoverable. See INV-14.
4. Cost allocation tags activated in Billing; a monthly cost review against `docs/plan/cost-model.md`.
5. **Review the `[P]`/`[D]`/`[E]` assignments against the real bill**, which by this point exists. The two
   estimates most likely to be wrong are the interface endpoints (the largest hourly item) and GitLab
   (the largest idle item). Update `docs/plan/cost-model.md` and `docs/plan/conventions.md` §5.1 with measured numbers rather than the projections.
6. Config rules / conformance packs on top of the Control Tower guardrails; review the recorder scope set
   in Stage 1d step 10 against what the bill actually shows.
7. Tighten the permission sets in `terraform-live/identity/sso/` against real usage, using **IAM Access
   Analyzer unused-access findings** — which is a better instrument than review, because it reports
   permissions that were granted and never exercised.
8. **Backup and recoverability**, which no earlier stage owns: an org-wide **AWS Backup** plan through an
   Organizations backup policy, covering the EBS volumes of the `[D]` instances;
   **Vault Lock** on the backup vault so a compromised administrator cannot delete the backups; and
   cross-region copies for the state buckets and the GitLab backup. Then state the numbers the plan has so
   far avoided: what the recovery time objective actually is for GitLab, for the Terraform state, and for
   the data lake, and test each one at least once. An untested backup is a hypothesis.
9. Review **Service Quotas** for the services in use, and set CloudWatch alarms on the ones that would
   silently break a session (SageMaker instance limits, EIPs, VPC endpoints).
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
