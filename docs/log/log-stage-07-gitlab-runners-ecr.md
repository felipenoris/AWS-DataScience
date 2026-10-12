# Log — Stage 7 — GitLab, Runners and ECR

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-07-gitlab-runners-ecr.md`](../plan/stages/stage-07-gitlab-runners-ecr.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-10-12 — the readings before pass 1

- **[Claude] The prerequisites, read live as the infrastructure user.** `VPC-SharedServices`
  (`10.30.0.0/16`) exists; the Sandbox↔SharedServices peering is `active`; the `awsds.internal` apex is
  associated with 5 VPCs and holds `proxy.` and `vpn.` and nothing else, so 1.4's `gitlab` record is
  owed; `awsds-pages.internal` is associated with 2 VPCs and holds NS and SOA only. The Sandbox domain
  `awsds-studio` holds one project, `eighth-experimentation` (`ACTIVE`), the INT-09 clone's source.
  `alias/awsds-prod-tfstate-pki` exists and no `production/pki/` state object does; the only Production
  secret is `awsds-prod-vpn-host-key`; the only `/datascience/prod/` parameter is the proxy allow-list;
  the only Production bucket is the state bucket, so step 2.3's "existing bucket" does not exist and the
  certificates are published into the GitLab objects bucket 1.1 creates. Production held two instances,
  the hub pair, both `stopped`; `production/egress` and `production/buildbox` were destroyed.
- **[Claude] `./aws/supplychain.py awsds-infra-prod awsds-infra-sandbox-1 awsds-infra-staging`: 0
  FAILED**, 4 notes (`SC-1`, `SC-3` twice, `SC-9`: "expected before Stage 7"), 8 passes: both
  repositories `IMMUTABLE`, registry scanning `BASIC (no rules)`, no pull-through cache rule,
  CodeArtifact `pypi`/`crates` with a domain policy, and the cross-account reads answering from both
  Interactive accounts (1 image visible each, the endpoint answered).
- **[Claude] EBS snapshot storage priced from the Price List Query API** (`aws pricing get-products`,
  `us-east-1`, `productFamily = Storage Snapshot`, `location = US West (Oregon)`): `USW2-EBS:SnapshotUsage`
  **0.05 USD/GB-month**, archive 0.0125, archive early-delete 0.0125, archive retrieval 0.03/GB.
  `docs/PRICING.md` §8 carries the row; the São Paulo column already read 0.068.
- **[Claude] The build plane confirmed `open` and the hub `stopped` at the reading**; the user ran
  `make hub-up` afterwards and authorized the stage's applies in chat.
- **[Claude] A session finding, 02:4x UTC: `GetRoleCredentials` answered `ForbiddenException: No access`
  for `awsds-infra-prod` while `awsds-infra-sandbox-1` still answered.** The `awsds` session's token file
  was rewritten at 02:35 UTC, after the readings above; the Sandbox profile was answering from its cached
  role credential and the Production one needed a fresh mint, which the current token's identity was
  refused. The shape Lesson 25 and 6c's notes record: a login over the same `sso-session` as another
  identity replaces the token. Pass 1's applies wait for a login as the **infrastructure user**.
