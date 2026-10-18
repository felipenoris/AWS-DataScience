# Log — Stage 11 — Data protection and DLP

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is [`docs/plan/stages/stage-11-dlp.md`](../plan/stages/stage-11-dlp.md).
Account ids are replaced by the account's name. All times UTC.*

---

## 2026-10-17 — step 2.1.1, the organization analyzer read and triaged

- **[user] The Audit snapshot.** `aws/cloudshell/audit-iam-analyser.sh` ran in Audit's CloudShell at
  23:38:36Z under `AWSAdministratorAccess`, and its output was attached in the Claude project's thread
  "Esqueleto do threat model". The file carries account ids and stays out of git.
- **[Claude] Sections 2, 3, 5 and 6.** CHECK OK: one analyzer, `awsds-org-external-access`,
  `ORGANIZATION`, `ACTIVE`, created 2026-08-12T03:38:38Z, the five project tags, no archive rule, last
  resource analyzed at 23:10:48Z (`awsds-prod-tfstate`); no call failed. `INV-10` holds.
- **[Claude] Section 4 counts 49 findings, all `ExternalAccess`: 46 `ACTIVE`, 3 `RESOLVED`.** 45 of the
  active ones are `AWSReservedSSO_*` roles, one per assignment-backed permission set per account:

  | Account | Active role findings | Beyond A.1's class rows |
  |---|---|---|
  | Management | 5 | none |
  | Audit | 3 | none |
  | Log Archive | 3 | none |
  | Policy Canary | 4 | none |
  | Identity | 4 | none |
  | Data Governance | 5 | `GovernanceManagerAccess` |
  | Production | 7 | `DataScientistProdAccess`, `DeploymentManagerAccess`, `DevEnvStewardAccess` |
  | Sandbox Account 1 | 7 | `DataScientistAccess`, `DeploymentManagerAccess`, `DevEnvStewardAccess` |
  | Staging | 7 | `DataScientistStagingAccess`, `DeploymentManagerAccess`, and the direct `AWSAdministratorAccess` an account update re-created on 2026-09-06 |

  That is the 35 of 2026-08-15, the nine persona rows of `identity/sso`'s `local.assignments` and
  Staging's direct assignment: `INV-16`'s shape, restated in `docs/AWS_STATE.md`.
- **[Claude] The three `RESOLVED` findings are in Staging**: the `DevEnvStewardAccess` and
  `DataScientistAccess` roles whose assignments Stage 6b step 2.1 removed on 2026-09-06, and the KMS key
  `ef2e17cd-…`, which no document here names. That it is the Development project key 6b destroyed
  (`PendingDeletion` until 2026-10-06) is inferred.
- **[Claude] One `ACTIVE` finding has another shape: the KMS key `a81b1ef3-…` in Sandbox Account 1**,
  `alias/awsds-sandbox-project` (the id [`log-stage-06i`](log-stage-06i-sandbox-orchestration.md)
  records). Two statements of its policy, written by `terraform-modules/sagemaker-prereqs/kms.tf`,
  grant `Principal: {"AWS": "*"}` under conditions that bound neither the caller's account nor its
  organization: `GrantKMSPermissionsForAllProjectRoles` and `AllowCreateGrantForProjectRoles`. Which
  of them the finding carries is inferred, since the summary names neither. Outside the organization the
  RCP's `EnforceOrgIdentitiesOnSecretsAndKeys` denies `kms:*`, read and never attempted, and an external
  finding does not weigh an RCP (AWS's `ExternalAccessDetails` reference, read 2026-10-17), so the
  finding stands with the RCP in place. Recorded as `TM-21` in
  [`threat-model.md`](../plan/threat-model.md) and as `EXC-18`; the user chooses between narrowing the
  two statements and archiving the finding individually.
- **[Claude] No finding names an S3 bucket**: not the lake's five, not `awsds-sandbox-smus-projects`,
  not `awsds-sandbox-lake`. None names the lake's data CMK `alias/awsds-data-data`, Sandbox's
  `alias/awsds-sandbox-data`, a function, a topic, a snapshot or a file system. The threat model's
  outside column is filled from this reading.

## 2026-10-18 — `TM-21`: the Sandbox project key's narrowing chosen

Written by Claude in the cloud session of the project thread, with no AWS identity, in PR #164; nothing
changed in AWS.

- **[user] The choice** (00:02:46, on a card): narrow the project key policy's two
  `Principal: {"AWS": "*"}` statements to this organization's principals, rather than archive the
  finding individually.
- **[Claude] What the change waits on.** The statement the finding carries, which `get-finding-v2` in
  Audit names, asked of the user at 00:03:35. And Stage 17's pass 1 (PR #157), which moves the same
  module, `terraform-modules/sagemaker-prereqs/`, to `v0.5.0`, a tag not yet on origin: the narrowing
  is the module's next tag after it, read from `git ls-remote --tags origin` when it is tagged, and its
  `sandbox/sagemaker/` apply runs from the laptop. `TM-21` and `EXC-18` stay open until a snapshot
  reads the finding `RESOLVED`.

## 2026-10-18 — `TM-21`: the finding read by `get-finding-v2`

- **[user] The finding's detail**, read in Audit's CloudShell with the commands asked at 00:03:35 and
  pasted in the thread at 00:18:51:

  ```bash
  ANALYZER=$(aws accessanalyzer list-analyzers --region us-west-2 --query "analyzers[?name=='awsds-org-external-access'].arn" --output text)
  ID=$(aws accessanalyzer list-findings-v2 --region us-west-2 --analyzer-arn "$ANALYZER" --filter '{"resourceType":{"eq":["AWS::KMS::Key"]},"status":{"eq":["ACTIVE"]}}' --query 'findings[0].id' --output text)
  aws accessanalyzer get-finding-v2 --region us-west-2 --analyzer-arn "$ANALYZER" --id "$ID" --query '[resource, findingDetails]' --output json
  ```

  The output, with the account id replaced by the account's name:

  ```json
  [
      "arn:aws:kms:us-west-2:<Sandbox Account 1>:key/a81b1ef3-716f-4105-bb42-14184a6e2174",
      [
          {
              "externalAccessDetails": {
                  "action": [
                      "kms:CreateGrant",
                      "kms:Decrypt",
                      "kms:GenerateDataKey"
                  ],
                  "condition": {},
                  "isPublic": true,
                  "principal": {
                      "AWS": "*"
                  },
                  "resourceControlPolicyRestriction": "APPLICABLE"
              }
          }
      ]
  ]
  ```

- **[Claude] Both statements carry the finding.** Its three actions are the union of
  `GrantKMSPermissionsForAllProjectRoles` (`kms:GenerateDataKey`, `kms:Decrypt`) and
  `AllowCreateGrantForProjectRoles` (`kms:CreateGrant`), and its principal is theirs. The analyzer
  reads the key as public (`isPublic: true`) and weighs neither statement's conditions as bounding
  (`condition: {}`); `APPLICABLE` is the RCP present and left out of the evaluation. That an
  `aws:PrincipalOrgID` condition on both statements resolves the finding is inferred: no AWS page read
  here says how the analyzer weighs it on a key, and the snapshot after the apply decides it. AWS's key
  permissions for the Tooling blueprint, the contract `kms.tf` adapts, give both statements without an
  account or organization condition and do not mention Access Analyzer (read 2026-10-18). The change
  now waits only on Stage 17's pass 1 (PR #157).

## 2026-10-18 — `TM-21`: the narrowing tagged `sagemaker-prereqs-v0.6.0`

Written by Claude in the cloud session of the project thread, with no AWS identity, in PR #166; nothing
changed in AWS.

- **[Claude] The module change** (`0dc159f`, on `main` after PR #157 merged as `e6dfc6a`):
  `aws:PrincipalOrgID` in the `StringEquals` of `GrantKMSPermissionsForAllProjectRoles` and of
  `AllowCreateGrantForProjectRoles`, the id read from the data source
  `aws_organizations_organization.current` as `vpc` and `vpc-egress` read it. Checked in the cloud
  session: `terraform fmt -check`; `init -backend=false` and `validate` with the providers
  `sandbox/sagemaker/`'s lock file pins (aws 6.61.0, awscc 1.98.0); a scratch `terraform test` with
  mocked providers, in which both statements rendered with the organization id when `domain_id` is set
  and neither rendered without it; `make check` OK; the offline gates green on the commit.
- **[user] The tag**, pushed from the laptop because the cloud session's tag pushes are refused, and
  pasted in the thread at 06:10:04:

  ```text
  git fetch origin claude/project-thread-yrm4u1
  git log --oneline -1 0dc159f
  git tag sagemaker-prereqs-v0.6.0 0dc159f
  git push origin sagemaker-prereqs-v0.6.0
  git ls-remote --tags origin sagemaker-prereqs-v0.6.0
  From github.com:felipenoris/AWS-DataScience
   * branch            claude/project-thread-yrm4u1 -> FETCH_HEAD
  Total 0 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
  To github.com:felipenoris/AWS-DataScience.git
   * [new tag]         sagemaker-prereqs-v0.6.0 -> sagemaker-prereqs-v0.6.0
  0dc159f5a6a034b3ac80d39ee4fbbc981b840866	refs/tags/sagemaker-prereqs-v0.6.0
  ```

- **[Claude] The caller.** `terraform-live/sandbox/sagemaker/` points at `sagemaker-prereqs-v0.6.0`,
  not planned and not applied. The slice also carries Stage 17's pass 1 (`v0.5.0`, `MLflowApp`), not
  applied either, whose step 1.2 reads the slice's plan as one configuration and one grant added. With
  its step 1.3 applied first, this version's plan should change only the key's policy, in place
  (inferred: no plan has run). `TM-21` and `EXC-18` stay open until a snapshot reads the finding
  `RESOLVED`.
