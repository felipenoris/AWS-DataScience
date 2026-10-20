# Log — Stage 15 — GuardDuty org-wide

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-15-guardduty.md`](../plan/stages/stage-15-guardduty.md).
Account ids are replaced by the account's name in angle brackets. All times UTC.*

---

## 2026-10-20 — before step 1: detectors, trusted access, policy types, service-linked roles

- **[Claude] The request.** One of the parallel tasks the orchestrating session ran on 2026-10-20 at the
  user's request, one stage each, in PR #223: read what Stage 15 owes by reading AWS only, and bring
  `aws/guardduty.py` to decision 4. Every call was a read from the laptop, as the infrastructure user
  through `InfrastructureAccess` (`awsds-infra-data`, `awsds-infra-identity`, `awsds-infra-prod`,
  `awsds-infra-sandbox-1`, `awsds-infra-staging`). Decision 4's reading of the same day (PR #215) made
  no AWS call; the stage file carries it.
- **[Claude] `./aws/guardduty.py`** on the five profiles, report generated 22:09:05, exit 0, no failed
  call: no detector in `<Data Governance Account>`, `<Identity Account>`, `<Production Account>`,
  `<Sandbox Account 1>` or `<Staging Account>`, and no delegated administrator registered for
  `guardduty.amazonaws.com`, read from `<Identity Account>`. `GD-1` and `GD-2` read `note`, the state
  expected before step 1, and `GD-3` had no detector to read. The script was this PR's version:
  `AI_PROTECTION` in the report's column order, decision 4's policy in the header, and `GD-3` reading
  past `CLOUD_TRAIL`, `DNS_LOGS` and `FLOW_LOGS`, which the AWS CLI 2.37.12 model lists among
  `GetDetector`'s features and no create or update input names. That change has met no detector: six
  fabricated `get-detector` documents read the verdict intended, among them a detector with every plan
  `DISABLED` and those three `ENABLED`, which the script before the change failed on `GD-3`. The
  harness is the session's scratch file and is not tracked.
- **[Claude] Trusted access.** `./aws/org-trusted-access-services.py` from `awsds-infra-identity`,
  generated 22:06:07, exit 0: ten service principals (`access-analyzer`, `account`, `cloudtrail`,
  `config`, `controltower`, `iam`, `member.org.stacksets.cloudformation`, `ram`, `securityhub`, `sso`),
  `guardduty.amazonaws.com` not among them; four delegated administrators, `access-analyzer`, `config`
  and `securityhub` to `<Audit Account>` and `sso` to `<Identity Account>`, all `ACTIVE`. `INV-09`
  holds as written.
- **[Claude] The root's policy types**, `organizations list-roots` from `awsds-infra-identity`, exit 0:
  `DECLARATIVE_POLICY_EC2`, `RESOURCE_CONTROL_POLICY`, `SERVICE_CONTROL_POLICY` and `TAG_POLICY`, each
  `ENABLED`. `GUARDDUTY_POLICY` is not among them.
- **[Claude] Step 5's before, re-read.** `iam list-roles --path-prefix /aws-service-role/` in the five
  accounts, each exit 0, filtered on role names holding `GuardDuty` or `SecurityHub`: no role holding
  `GuardDuty` in any of them, and `AWSServiceRoleForSecurityHub` in all five, which shows the listing
  returns service-linked roles. The stage file's before of 2026-10-17 stands.
