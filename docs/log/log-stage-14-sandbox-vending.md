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
