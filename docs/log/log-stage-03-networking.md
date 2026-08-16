# Log — Stage 3 — Networking

*Manual actions performed by the user. Written by the user, **never** by Claude.
Stage: [`docs/plan/stages/stage-03-networking.md`](../plan/stages/stage-03-networking.md).*

---

*One exception, recorded so the provenance is not guessed later. **On 2026-08-16 the user authorised
Claude, once and explicitly, to create this file and write the entry below** — a decision sitting held
with the user in that same session, with no AWS call in it. Everything from here is the user's, as
usual, and the rule is unchanged.*

---

## 2026-08-16 — the five execute-time decisions, settled before the stage

**No AWS call in this entry, and nothing in this stage has been executed.** The sitting settled the five
choices the stage lists under "Decisions due while executing", so that none of them is taken at the
keyboard (Lesson 16). Two of them were brought forward because their consequences leave the stage: step 0
has an ordering against the `Staging` vend, and step 9.3's list is a prerequisite of Stage 4.

| # | Step | Settled as |
|---|---|---|
| 1 | 1.2, 1.3 | Supernet `10.16.0.0/13`, unit 1 at `10.20.0.0/16`. The allocation — CIDR and `zone_ids` — lives in `scripts/tfhygiene/backend.py` and reaches each slice through the generated `terraform.auto.tfvars`. **No new file**: that module is already the one place a slice's generated files are built from (Stage 2 step 2.6). Entries are authored, never computed; the rule is the lowest free `/16`; the duplicate check is born with N=2 |
| 3 | 5.1 | CloudWatch Logs, **30 days**. Not a cost choice — between 7 and 30 days the difference is cents. S3 delivery was the real alternative and was declined: it halves the delivery price and costs Logs Insights, on a log whose stated purpose is debugging |
| 4 | 10.1 | **`egress_mode = A`**. The USD 0.030/h decides nothing; what decides it is that B has no default route and its package path is not built until Stages 6-7. The switch stays per account and D5's comparison is unaffected |
| 5 | 9.3 | **Five families**, written now as the module variable's documented default: AL2023 repositories, CloudWatch agent, SSM agent, **ECR layer storage** and SageMaker |
| 6 | step 0 | **Delete all six Account Factory VPCs, and turn creation off in Account Factory.** The Management half before the `Staging` vend; the deletions by hand, per account, whenever. Closes with 0.4 |

- **The sitting's one finding, and it outranks the decision that produced it: a NAT does not bypass an
  endpoint policy.** A gateway endpoint puts a route to the S3 prefix list in the route table and the more
  specific route wins, so in-region S3 traffic goes through it and is judged by its policy whether or not a
  `0.0.0.0/0` route exists. Design A carries only what is *not* in-region S3. **So the allow-list of 9.3 is
  load-bearing from [Stage 4](../plan/stages/stage-04-vpn.md), not from Stage 6** — the first EC2 instance
  in the project is the WireGuard host, and it installs WireGuard from `dnf` in its user data. The stage's
  own 9.5 had said the endpoint is the only route "under design B", which is true and reads as though A had
  a second one.

- **One entry the step was missing, found while enumerating: ECR pulls its image layers from an S3 bucket.**
  `ecr.api`/`ecr.dkr` (8.2) authorise the pull; the layers come from `prod-<region>-starport-layer-bucket`,
  which is AWS-owned and therefore denied by the `aws:ResourceOrgID` condition like any other. It fails
  *after* a successful login and the error points at S3, not at ECR.

- **What the list is not: measured.** The five families' bucket names are taken from AWS's documentation,
  not read from an account, so each is confirmed at execution by verification (iii) — Lesson 23. And AL2023
  resolves its mirror list from a public HTTPS endpoint before fetching from S3: under A that leaves through
  the NAT, under B no entry in the list can rescue it, which makes it a design-B input due at Stage 6.

- **Repository, same sitting, no AWS call:** each decision written into the step that owns it (0.2, 1.3,
  5.1, 9.3, 10.1) with the "Decisions due while executing" section left as the index; 9.5's misleading
  sentence corrected; the stage's Status row now records that the five were settled before execution;
  `CLAUDE.md`'s Current position brought current. `make check` green, `make check-docs` still red on the
  same pre-Stage-2 prose, 1056 links resolve.

- **Open, and the next action:** step 0 — the Account Factory network configuration on Management, as
  `AWS Control Tower Admin` through `AWSAdministratorAccess`, which must land **before** the `Staging` vend.
  The six VPC deletions run per account as the **infrastructure user** through `InfrastructureAccess`
  (`awsds-infra-*`), and 0.4 closes the loop: re-run `./aws/networking.py` and update `docs/AWS_STATE.md`
  §C in the same sitting.

## 2026-08-16 — two statements of the previous entry corrected against the documentation

**No AWS write in this sitting** — a plan revision plus read-only snapshots. The Stage 3 roteiro was
revised into the action-checklist format, and the official documentation corrected two statements the
entry above records:

- **The Account Factory VPCs are not removed by a per-account hand-deletion.** The Control Tower
  walkthrough names the supported cleanup: **delete each account's stack instance from the
  `AWSControlTowerBP-VPC-ACCOUNT-FACTORY-V1` StackSet on Management** — so both halves of step 0 are one
  Management sitting as `AWS Control Tower Admin`, and verification (vi) now asks what the removal
  leaves behind. The decision itself — remove all of them, creation off before the `Staging` vend — is
  unchanged.
- **AL2023 does not fetch its mirror list from a generic public endpoint.** The default `mirrorlist=`
  URL points into the regional repository bucket itself (`al2023-repos-<region>-de612dc2`), and AWS's
  no-internet guidance is exactly the 9.3 gateway-endpoint policy — the package path works under both
  egress designs, and the "design-B input due at Stage 6" above is withdrawn. Verification (iii) still
  confirms the behaviour, plus that the AMI's repo files use the mirrorlist, not `cdn.amazonlinux.com`.

Also answered by documentation: verification (vii) — a Route 53 association authorization persists
until deleted, and deleting it does not affect the association.

## Step 0 - 0.2

This is step will delete CloudFormation AccountFactory VPCs default settings.

- Login at AWS Console using `AWS Control Tower Admin` -> Management Account -> AWSAdministratorAccess. CloudFormation → StackSets → AWSControlTowerBP-VPC-ACCOUNT-FACTORY-V1 → Actions → Delete stacks from StackSet.

  - "Accounts" section left the default setting `Deploy stacks in accounts`. I took the account numbers from `StackSet -> `Stack instances` tab.

    - Production Account
    - Development Account
    - Data Governance Account
    - Policy Canary Account
    - Identity Account
    - Sandbox Account 1

  - section Specify Regions, which I set do us-west-2.

  - section `Deployment options`. `Retain stacks` is not marked, and the rest was left with default settings:
    - maximum concurrent accounts set to 1
    - failure tolerance set to 0
    - region concurrency set to sequential
    - concurrency mode set to "Strict failure tolerance"


 → all instances, region `us-west-2`, RetainStacks off. What's left: log groups, Policy Canary's instance.

- Moving to AWS Control Tower -> Account Factory. Network configuration page section -> Edit.
  - `Internet-accessible subnet` is not marked.
  - `Maximum number of private subnets` set to 0.
  - Regions: unmarked `US West (Oregon)`. All the others are unmarked by default.


---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
