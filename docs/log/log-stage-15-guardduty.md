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

## 2026-10-21 — the Malware Protection service-linked role and the `AI_ANALYST` feature, read on 2026-10-20 (PR #227), recorded

*Claude's sitting, no AWS call: the task of the orchestrating session that opened PR #227 (merged
2026-10-20T22:54:07Z), to make the corrections PR #223's session had found outside its files, read
GuardDuty's pages on the Malware Protection role and on Investigation, the two roles' managed policies and
the AWS CLI 2.37.12 model, recorded in [`REFERENCES.md`](../REFERENCES.md) the same sitting. It wrote no
entry, under the rule of that day; this one is written on 2026-10-21 from the PR's body and diff, with no
AWS call either.*

- **[Claude] A second service-linked role.** Malware Protection for EC2 creates
  `AWSServiceRoleForAmazonGuardDutyMalwareProtection`, trusted by
  `malware-protection.guardduty.amazonaws.com`, when the plan is first enabled, which it is by default in
  an account new to GuardDuty, and keeps it when the plan is disabled. Neither
  `AmazonGuardDutyServiceRolePolicy` v13 nor `AmazonGuardDutyMalwareProtectionServiceRolePolicy` v2 holds
  a `guardduty:` action, so decision 1 (c)'s only candidate stays Audit's Identity Center administrator
  role.
- **[Claude] The `AI_ANALYST` detector feature** is in the model's `DetectorFeature` and
  `DetectorFeatureResult` and not in `OrgFeature`, the names `UpdateOrganizationConfiguration` and
  `UpdateMemberDetectors` take, and the `GUARDDUTY_POLICY` syntax has no key for it, so `UpdateDetector`
  in the account is its only switch. `CreateInvestigation`, a preview in Oregon, needs it on the
  administrator's detector and runs on Bedrock through cross-Region inference. Steps 0, 2 and 3, decision
  4, verification ii and the deliverables name it.
- **[Claude] `aws/guardduty.py`'s `GD-3` message** names decision 4's policy as a member account's
  alternative, and `UpdateDetector` as the only update call naming `AI_ANALYST`; `aws/INDEX.md`'s row
  matches PR #223's script, and
  `REFERENCES.md`'s permissions row no longer credits a page with "the only principal the service
  creates". `POLICIES.md`'s two corrections wait in the PR's body for PR #108's holder, and main's
  collision note still names the service-linked role alone.
