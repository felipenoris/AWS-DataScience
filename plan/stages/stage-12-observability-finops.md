# Stage 12 — Observability, governance and FinOps

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | any stage that created resources. |
| **Consumes** | — |
| **Proves** | — |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** know what is running, what it costs, and be told when something breaks.

**Prerequisites:** any stage that created resources.

**To execute:**

1. CloudWatch dashboards per environment (SageMaker, GitLab, VPN, NAT traffic, Athena scans).
2. Alarms → SNS → e-mail for: budget thresholds, failed pipelines, VPN down, GitLab unhealthy,
   unusual data scans.
3. Log retention policies everywhere (default retention is "forever", which quietly costs money).
4. Cost allocation tags activated in Billing; a monthly cost review against `plan/cost-model.md`.
5. **Review the `[P]`/`[D]`/`[E]` assignments against the real bill**, which by this point exists. The two
   estimates most likely to be wrong are the interface endpoints (the largest hourly item) and GitLab
   (the largest idle item). Update `plan/cost-model.md` and `plan/conventions.md` §5.1 with measured numbers rather than the projections.
6. Config rules / conformance packs on top of the Control Tower guardrails; review the recorder scope set
   in Stage 1b step 10 against what the bill actually shows.
7. Tighten the permission sets in `terraform-live/identity/` against real usage, using **IAM Access
   Analyzer unused-access findings** — which is a better instrument than review, because it reports
   permissions that were granted and never exercised.
8. **Backup and recoverability**, which no earlier stage owns: an org-wide **AWS Backup** plan through an
   Organizations backup policy, covering the EBS volumes of the `[D]` instances and the EFS filesystem;
   **Vault Lock** on the backup vault so a compromised administrator cannot delete the backups; and
   cross-region copies for the state buckets and the GitLab backup. Then state the numbers the plan has so
   far avoided: what the recovery time objective actually is for GitLab, for the Terraform state, and for
   the data lake, and test each one at least once. An untested backup is a hypothesis.
9. Review **Service Quotas** for the services in use, and set CloudWatch alarms on the ones that would
   silently break a session (SageMaker instance limits, EIPs, VPC endpoints).
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
