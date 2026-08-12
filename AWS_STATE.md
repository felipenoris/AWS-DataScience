# AWS_STATE.md — what to expect from this environment

**Read this next to a snapshot, never instead of one.** A snapshot says what AWS reports; this file says
what a snapshot is *expected* to report, and which differences are already accounted for. Without it, a
reading of `aws/output/` produces false alarms — and, worse, makes a real one indistinguishable from the
six that were already known.

Four files answer four different questions. Keeping them apart is what keeps any of them true:

| Question | Where |
|---|---|
| What should exist, and why | [`GENERAL_PLAN.md`](GENERAL_PLAN.md), `plan/`, [`ORGANIZATION.md`](ORGANIZATION.md) |
| What was typed by hand, and when | [`log/`](log/INDEX.md) |
| What AWS reports right now | `aws/output/` — regenerate it, see [`aws/INDEX.md`](aws/INDEX.md) |
| **Whether the difference between those is expected** | **this file** |

Two rules keep this file from becoming a stale copy of the three above:

- **No identifiers.** Names only. Account ids, OU ids, ARNs, instance ids and email addresses live in the
  snapshot, which is regenerated on demand. A file that carries no identifier cannot be wrong about one.
- **No reasoning.** *Why* something is so belongs in [`plan/decisions/`](plan/decisions/INDEX.md); *what was
  done* belongs in `log/`. Here: only what is expected, and what a deviation from it means.

Everything below was measured from a script in [`aws/`](aws/INDEX.md). **A bare section number refers to
`aws/output/list-identities.txt`** (first run 2026-08-11); a reference prefixed with a file name, such as
`AZs.txt` 3, refers to that snapshot instead (`aws/AZs.sh`, 2026-08-12).

## A. Invariants — what a snapshot must show

| # | Expected | Section | A deviation means |
|---|---|---|---|
| **INV-01** | Exactly **one** Identity Store instance | 3.2 | The single-directory assumption the whole identity plane rests on is broken. The script stops here on purpose — reconcile before doing any identity work |
| **INV-02** | Every account is `ACTIVE`, and every account **but two** sits inside an OU. The two attached directly to the root are the **management account** — Control Tower leaves it there — and EXC-01 | 2.3, 2.4 | A *third* account at the root inherits no policy set at all. That is a hole in the ceiling, not a detail |
| **INV-03** | The OU tree is **two levels deep** — `Sandboxes` nested under `Interactive` | 2.3 | A one-level `for_each` over OUs sees nothing below depth 1, so every Sandbox account is invisible to it |
| **INV-04** | **Five** `sso-group-*` groups, each with **exactly one** member | 3.3, 3.5 | Memberships are directory state, changed by hand and by nobody else. Stage 1b step 8.3's alarm should have fired — if it did not, the alarm is the finding |
| **INV-05** | Six Control Tower groups are **empty**: `AWSAuditAccountAdmins`, `AWSLogArchiveAdmins`, `AWSLogArchiveViewers`, `AWSSecurityAuditors`, `AWSSecurityAuditPowerUsers`, `AWSServiceCatalogAdmins`. `AWSControlTowerAdmins` and `AWSAccountFactory` hold the Control Tower admin user, and nothing else does | 3.5 | Each of those six already **holds live assignments** — `AWSAuditAccountAdmins` is administrator on the Audit account. They grant nothing only because they are empty, so one added member is one granted access |
| **INV-06** | `InfrastructureAccess` carries the **five** project tags and a `PT4H` session | 4.2, 4.3 | A tag missing here is the tag convention failing at its first instance, which is where a tag policy would later fail silently |
| **INV-07** | Each account shows the assignment rows in **A.1** below, and no others | 5.1, 5.2 | A path exists that nobody wrote. Check A.1 first — most of those rows are Control Tower's, not this project's |
| **INV-08** | Every account returns the **same** AZ name→ID mapping, four zones, all `available` and `opt-in-not-required` | `AZs.txt` 3, 4 | **Not a finding, and not drift** — a vended account is assigned its own mapping and may legitimately differ. It is recorded because the plan anchors subnets on the **ID** precisely so a divergence costs nothing; if one appears, confirm no slice indexes AZs by list position, and leave it. The reverse — accounts agreeing while a slice indexes by position — is the state that looks fine and bills |
| **INV-10** | In **Audit**, `us-west-2`: exactly **one** IAM Access Analyzer, named `awsds-org-external-access`, type **`ORGANIZATION`**, `ACTIVE`, carrying the five project tags and **no archive rule** | `audit-iam-analyser.txt` 2, 3, 5 — the one snapshot here that can only be produced from CloudShell inside Audit | Type `ACCOUNT` is the wrong zone of trust: it stays `ACTIVE`, reports on one near-empty account and raises nothing. A **second** analyzer of an unused-access type is the paid half arriving early (Stage 12) and bills per resource per month. An **archive rule** suppresses matching findings silently — the plan creates none |
| **INV-11** | Every OU shows `FullAWSAccess` **plus exactly one `aws-guardrails-*` SCP — except `Sandboxes`**, which shows only `FullAWSAccess`. The organization root shows `FullAWSAccess` alone. **Every node also shows `RCPFullAWSAccess`** — AWS attached it to the whole tree by itself when Stage 1c step 7.2 enabled the RCP type, exactly as `FullAWSAccess` mirrors the SCP type | `org-policy-baseline.txt` 3 | A guardrail missing from an OU that had one is Control Tower drift, not this project's doing. **`Sandboxes` acquiring one is information, not drift**: it would mean the nested OU became a registered target, which is exactly what Stage 1c verification (xi) is trying to establish. The `Security` document is the only one with 11 statements rather than 8 — the extra three are about the log-archive and audit buckets. **`RCPFullAWSAccess` missing from a node is an RCP that would deny everything there**, since an RCP set with no allow is a closed door |
| **INV-12** | Enabled Control Tower controls, per OU: **9 `AWS-GR_*` on `Workloads`, `Data`, `Interactive`, `Identity` and `Policy Test`; 12 on `Security` — the same 9 plus `CT.S3.PV.7`, `CT.S3.PV.8` and `CT.SNS.PV.1`; and *zero* on `Sandboxes`**, whose call returns an **empty list rather than an error**. `Security` names its controls in the `controlcatalog:::control/<opaque>` namespace, every other OU in `controltower:<region>::control/AWS-GR_*` | `org-policy-baseline.txt` 5 — **Management only**; a member account is told *"you must create a landing zone first"* | The `Security` extras are the control-half of its three extra SCP statements, so the two halves agreeing is the expected state and a divergence is Control Tower drift. **The empty `Sandboxes` answer is not yet evidence of registration**: nothing in that run errored, so the "unregistered targets error" discriminator was never exercised (Lesson 13). Stage 1c step 7.7's `enable-control` is what settles it. The two id namespaces are one service, not two — resolve either with `controlcatalog get-control`, whose `Aliases[0]` is the `AWS-GR_*` name |
| **INV-09** | **Seven** service principals hold trusted access — `access-analyzer`, `cloudtrail`, `config`, `controltower`, `iam`, `member.org.stacksets.cloudformation` and `sso` — and exactly **three** are delegated: `access-analyzer` and `config` to **Audit**, `sso` to **Identity** | `org-trusted-access-services.txt` 1, 3 | An eighth principal is a service allowed to read the organization and create its own roles in every account, that no stage turned on. A *fourth* delegation is a member account administering a service org-wide. Six of the seven are the landing zone's; `access-analyzer` is the only one this project added |

### A.1 — the assignment shape, per class of account

An account is reached by more principals than the project put there. Counting only the project's two and
calling a Control Tower row "drift" is the mistake this table exists to prevent.

| Account class | Assignment rows expected |
|---|---|
| **Vended** — Data Governance, Development, Identity, Production, Sandbox Account 1 | `InfrastructureAccess` → `sso-group-infrastructure`; `AWSOrganizationsFullAccess` → `AWSControlTowerAdmins`; `AWSPowerUserAccess` → `AWSSecurityAuditPowerUsers`; `AWSReadOnlyAccess` → `AWSSecurityAuditors`. **No direct `USER` assignment** — the D32 Account Factory ones were removed in 1b step 5.1 (2026-08-12), and their return is what verification (vi) is watching for |
| **Policy Canary** | **`AWSAdministratorAccess` → the infrastructure user *directly*** (D32) and nothing else of this project's — no `InfrastructureAccess`, by design (D29). It is the **only** direct `USER` assignment left in the organization, and it is permanent: there is no group and no `awsds-infra-*` profile behind it, so removing it removes the only way in |
| **Audit** | `AWSAdministratorAccess` → `AWSAuditAccountAdmins` and → `AWSControlTowerAdmins`; `AWSPowerUserAccess` → `AWSSecurityAuditPowerUsers`; `AWSReadOnlyAccess` → `AWSSecurityAuditors` |
| **Log Archive** | `AWSAdministratorAccess` → `AWSControlTowerAdmins` and → `AWSLogArchiveAdmins`; `AWSPowerUserAccess` → `AWSSecurityAuditPowerUsers`; `AWSReadOnlyAccess` → `AWSLogArchiveViewers` and → `AWSSecurityAuditors` |
| **Management** | Control Tower's own only: `AWSAdministratorAccess`, `AWSPowerUserAccess`, `AWSReadOnlyAccess`, `AWSServiceCatalogAdminFullAccess` → `AWSServiceCatalogAdmins`, `AWSServiceCatalogEndUserAccess` → `AWSAccountFactory`. **No `InfrastructureAccess` and no direct user assignment** |

**Only three of those rows reach a principal that exists today**; the rest point at the empty groups of
INV-05. They are `sso-group-infrastructure` on the vended accounts and the one surviving direct D32
assignment on `Policy Canary` — both the infrastructure user — and **`AWSControlTowerAdmins` through
`AWSOrganizationsFullAccess`, which reaches every vended account**. The third one is Control Tower's, not
the plan's, and **Stage 1c step 7.5 is where its reach finally gets measured** (open question 11).

## B. Known exceptions

| ID | What the snapshot shows | Disposition |
|---|---|---|
| **EXC-01** | An account named `Sandbox`, `SUSPENDED`, attached **directly to the organization root** — not to be confused with `Sandbox Account 1`, which is correctly under `Sandboxes` | Left over from an experiment that predates this project and has nothing to do with it (user, 2026-08-11). **Ignore it.** Do not propose adopting it, moving it into an OU, or deleting it, and do not read it as a violation of INV-02. It runs nothing, so the policy sets never reaching it costs nothing. *Not verified:* whether a closed account still occupies a slot in the organization's account quota — which matters only if the cap binds again |

## C. True now, and expected to change

Listed so that a future session does not "fix" something that a later stage is going to do properly.

| What the snapshot shows today | Changes at |
|---|---|
| ~~Only `SERVICE_CONTROL_POLICY` is `ENABLED` on the root~~ — **done: all four types read `ENABLED`** (7.2). What it left behind is `RCPFullAWSAccess` on every node, now part of INV-11 | Nothing further. 7.8 is what finally attaches an RCP, a tag policy and a declarative policy |
| `InfrastructureAccess` is the only permission set that is not Control Tower's, and it has **no permissions boundary** | Stage 2 step 5 writes the other six and their boundaries. One permission set was created by hand on purpose; six were only *specified* |
| Only `sso-group-infrastructure` holds any assignment — the other four `sso-group-*` groups reach no account | Same place: the group→account assignments are Terraform, not console |
| **Account-level S3 Block Public Access reads all four flags `true` in all nine accounts** (7.4 step 1) — the six with a profile are re-measurable here; **Management, Log Archive and Audit were set and console-verified by the user and this laptop cannot read them**, so `account-bpa.txt` will always say "6 of 6 *measured*" and section 4 is the rest of the sentence. Still no RCP, tag or declarative policy *attached* | **Stage 1c**: 7.5 denies changing BPA with one carve-out, 7.8 attaches the rest. **At every vend, forever**: a new account lands with BPA unset and inherits the deny on arrival (D34/D35, Stage 14) |
| **No policy of this project's is attached to any node** — every SCP shown is `FullAWSAccess` or Control Tower's (INV-11) | **Stage 1c**: 7.5 puts two documents on the root, 7.6 one per OU, 7.7 one Region control per OU, 7.8 the RCP, tag and declarative policies. Restate INV-11 as each lands |
| There is no `Staging` account | The vend is held on the account cap; see the Current position in [`CLAUDE.md`](CLAUDE.md) |
| Audit holds one analyzer, external-access only (INV-10) | **Stage 12** adds the unused-access analyzer, which is the paid half. Until then a second analyzer there is a finding, not a head start |
| The trusted-access list of INV-09 has seven principals and three delegations | It grows by one at each of **Stage 1d step 11** (`ram`), **Stage 4** (GuardDuty), **Stage 5** (Security Hub) and **Stage 11** (Macie). For those three services delegating *is* enabling, which is why they are not there yet — restate INV-09 as each one lands |

## D. Keeping this file true

- **When a stage closes**, move whatever it changed out of section C — an entry there that has already
  happened is worse than no entry, because it tells a future session to expect the old world.
- **When a snapshot surprises you**, the surprise ends up here as an `INV-nn` or an `EXC-nn`, or it is a
  real finding and belongs in `log/` and possibly in a decision. Deciding which is the whole job.
- **An entry that names an identifier, or explains why, is in the wrong file.** Move it and leave a name.
- Reference entries by **stable ID** — `INV-03`, `EXC-01` — never by row position.

---

*Live state: [`aws/INDEX.md`](aws/INDEX.md) · Target state: [`ORGANIZATION.md`](ORGANIZATION.md) ·
What was done by hand: [`log/INDEX.md`](log/INDEX.md)*
