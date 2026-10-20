# Log — Stage 14 — Per-business-unit Sandbox vending

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-14-sandbox-vending.md`](../plan/stages/stage-14-sandbox-vending.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-10-18 — `./aws/vending.py` written and read against the hand-built unit, the environment down

- **[Claude] The request.** One of five tasks the orchestrating session ran as subagents, which the user
  approved on 2026-10-18: write the instrument the stage asks for before the first vend, and price a
  unit. Every call was a read, as the infrastructure user through `InfrastructureAccess`
  (`awsds-infra-identity`, `awsds-infra-sandbox-1`, `awsds-infra-prod`, and `awsds-infra-staging` for
  the control below). The environment was down: no interface endpoint in `<Sandbox Account 1>` or
  `<Production Account>`, and no running instance in `<Production Account>`.
- **[Claude] The hand-built unit reads as the stage predicts.** `./aws/vending.py`, last run's report
  generated 22:51:53 UTC, exit 0, nine passes, one note, no failed call, as in the earlier runs:
  - `VN-1`: `<Sandbox Account 1>` `ACTIVE` under `Interactive`/`Sandboxes`, the only account there;
    the account and the OU each carry `FullAWSAccess` and `RCPFullAWSAccess` and no tag or
    declarative policy.
  - `VN-2`: `10.20.0.0/16` inside `10.16.0.0/13`, overlapping none of `VPC_CIDRS`' other rows; the
    account's one VPC carries it as `awsds-sandbox-vpc`.
  - `VN-3`: to `production/networking`, `pcx-039c2a6f7e6ace720` active, 8 routes out of the two private
    tables and 6 back from three hub tables; to `production/foundation`, `pcx-00014eccfa5af65dd`
    active, 6 routes out of three tables (the public table among them) and 8 back from two. No other
    peering.
  - `VN-4`: `sandbox.awsds.internal` associated with the unit's VPC and `VPC-Networking` only and
    authorized toward `VPC-Networking`; the unit's VPC resolves `awsds.internal` and
    `sandbox.awsds.internal` only, and the apex's authorization toward it stands.
  - `VN-5`: `awsds-prod-proxy` admits `10.20.0.0/16` on TCP/3128; plane `sandbox-foundation`,
    `allowlist`, 41 names.
  - `VN-6`: `sso-group-data-scientists` holds `DataScientistAccess` on `<Sandbox Account 1>`, its one
    seat in `Sandboxes`; the note names its seats in `Workloads`, `DataScientistStagingAccess` on
    `<Staging Account>` and `DataScientistProdAccess` on `<Production Account>`.
- **[Claude] A live negative control.** `./aws/vending.py staging` read `<Staging Account>`, which is no
  unit, as four failures: `VN-1` (its parent is `Workloads`), `VN-2` (`10.50.0.0/16` outside the
  supernet), `VN-3` (one peer slice where the hand-built unit has two), `VN-6` (nobody holds
  `DataScientistAccess` there). Its hub peering, `staging.awsds.internal` and its plane passed, the plane
  with a note that it allows no name.
- **[Claude] Every failure branch, against fabricated readings.** 44 cases fed to the six judges with
  no AWS call, under Python 3.14 and the system 3.9.6, each reading the verdict intended. The harness is
  the session's scratch file and is not tracked.
- **[Claude] A call that answers where its page says it cannot.** `sso-admin
  list-account-assignments-for-principal` answered from `<Identity Account>`, the delegated
  administrator, where its API reference says it must be called from the management account.
  Recorded in `docs/plan/lessons.md`'s list of what AWS does that its documentation does not say.
- **[Claude] What a unit holds that bills at rest**, read in `<Sandbox Account 1>`: three
  customer-managed keys (`alias/awsds-sandbox-tfstate`, `alias/awsds-sandbox-data`,
  `alias/awsds-sandbox-project`; the other four keys are AWS-managed), one private zone
  (`sandbox.awsds.internal`) and one secret, the warehouse's admin secret, which Stage 5b made and a vend
  does not. `docs/PRICING.md` §3, *A Sandbox unit*, prices the counts.

---

## 2026-10-20 — Every infrastructure profile's VPCs and the organization's account states, read for steps 2 and 6

- **[Claude] The request.** One of the tasks the orchestrating session started on 2026-10-20 at the
  user's request, one stage each: this log, D34 and `docs/AWS_STATE.md`'s VPC row brought to the vendor
  readings PR #214 put in steps 2 and 6. PR #214 read the vendor's pages with no session on AWS, so those
  readings live in the stage file and `docs/REFERENCES.md`, not here. Every call below was a read, as the
  infrastructure user through `InfrastructureAccess`, in `us-west-2`. The entry is PR #221's.
- **[Claude] No default VPC, and nothing in `172.31.0.0/16`.** `ec2 describe-vpcs` at 22:00Z, exit 0 from
  each of `awsds-infra-sandbox-1`, `awsds-infra-staging`, `awsds-infra-prod`, `awsds-infra-data`,
  `awsds-infra-identity` and `awsds-policy-canary`: five VPCs, each `IsDefault` false on a single block,
  `<Sandbox Account 1>` `10.20.0.0/16` (`awsds-sandbox-vpc`), `<Staging Account>` `10.50.0.0/16`
  (`awsds-staging-vpc`) and `<Production Account>` `10.30.0.0/16`, `10.31.0.0/16` and `10.32.0.0/16`
  (`awsds-prod-shared-vpc`, `awsds-prod-networking-vpc`, `awsds-prod-workloads-vpc`). `<Data Governance
  Account>`, `<Identity Account>` and `<Policy Canary Account>` hold none. All six joined the organization
  on 2026-08-09, before Stage 3 step 0.3 turned VPC creation off, so whether Account Factory deletes the
  default VPC with creation off stays the first vend's reading (step 2).
- **[Claude] The organization's one closed account.** `organizations list-accounts` from
  `awsds-infra-identity`, exit 0: ten accounts, nine `ACTIVE`, and `Sandbox` (`EXC-01`) with `Status`
  `SUSPENDED` and `State` `CLOSED`, joined 2026-08-01. Step 6's `PENDING_CLOSURE`, then `SUSPENDED`, is the
  `Status` field; `./aws/vending.py` reads `State` first, and its closed states hold `CLOSED`.
