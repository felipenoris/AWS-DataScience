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

## 2026-10-12 — pass 1, the applies (steps 1.1, 1.7, 2.2, 2.3, 2.4)

- **[user] `make hub-up`** before the sitting; both hub hosts read `running` (launched 02:42 UTC) when
  the applies began. **[user]** signed in again as the infrastructure user after the token finding
  above; `awsds-infra-prod` answered.
- **[Claude] `production/foundation/` applied (1.1): `18 to add, 0 to change, 0 to destroy`, re-plan
  `No changes`.** The key `alias/awsds-prod-gitlab`, the two buckets `awsds-prod-gitlab-objects` and
  `awsds-prod-gitlab-backup` (versioned, the second expiring at 30 days), the two containers
  `awsds-prod-gitlab-secrets` and `awsds-prod-runner-token` with their `GetSecretValue` denies.
- **[Claude] `production/egress/` applied (1.7) through `./scripts/slices.py up --env production --only
  egress --auto-approve`: `14 added`.** The hub check ran first and read both hub hosts `running`; the
  dormant hook was narrowed to no `[D]` slice by `--only`; `vpn`, `proxy` and `tooling` were listed as
  refused by name. `vpc-egress-v0.17.0`, 6c 5.5's thirteen plus `secretsmanager`. The plan-time output
  `no_proxy_all_groups` read **60 entries, sha256 `f8bc1df99d224181`**, and is the literal
  `production/tooling/variables.tf` carries (1.3). Before the output was re-exported by the slice the
  plan showed only `no_proxy` as `(known after apply)`: the module had the output since v0.17.0, the
  slice did not.
- **[Claude] `production/pki/` applied (2.1, 2.2): `20 to add, 0 to change, 0 to destroy`, re-plan `No
  changes`**, the first object ever encrypted under `alias/awsds-prod-tfstate-pki` (created 2026-08-15).
  The plan printed no private key. Read back from the published parameters with `openssl x509`:

  | Certificate | Subject | notAfter | SHA256 fingerprint |
  |---|---|---|---|
  | the root (D36 §5) | `O=AWS-DataScience, CN=awsds internal root CA` | 2036-10-09 06:35:12 UTC | `7B:E4:89:85:32:EB:98:E6:54:B0:19:AA:B2:C0:B3:FE:3C:46:1B:E4:FF:0B:18:5B:00:F3:C1:50:72:1D:1D:52` |
  | `gitlab.awsds.internal` | `O=AWS-DataScience, CN=gitlab.awsds.internal` | 2027-10-22 06:35:12 UTC | `D0:9A:BE:44:F2:18:2C:6E:FE:A4:CD:0C:F1:AE:09:4D:69:8A:23:1C:8B:4A:D1:31:A1:BF:33:1A:1E:2B:E5:6C` |
  | `*.awsds-pages.internal` | `O=AWS-DataScience, CN=*.awsds-pages.internal` | 2027-10-22 06:35:12 UTC | `23:D6:0C:3A:79:CB:5D:34:39:00:42:B8:B4:D7:09:B7:BB:81:CB:B9:80:1D:0D:55:81:61:E8:F7:74:E6:94:B9` |

  The leaves' re-issue is owed by 2027-09-22, when the plan starts proposing it (`early_renewal_hours`
  720). Published: `/datascience/prod/pki/{ca-root,leaf-gitlab,leaf-pages}-pem` and
  `s3://awsds-prod-gitlab-objects/pki/{awsds-root,gitlab.awsds.internal,awsds-pages.internal}.crt`; the
  keys in `awsds-prod-tls-gitlab` and `awsds-prod-tls-pages`.
- **[user] Decisions 6 and 7 taken as recommended, in chat:** CodeArtifact stays idle with no endpoint
  and no `assets` bucket family; Staging leaves the registry consumer map, which `registry/`'s 5.b apply
  carries (the four policies re-applied without it).

## 2026-10-12 — pass 1, GitLab applied (steps 1.2-1.6); the registry apply did not run

- **[Claude] `production/tooling/` planned twice and applied once.** The first plan failed at
  validation: `Error: invalid value for description` on the DLM lifecycle policy, whose description
  admits letters, digits, spaces, underscores and hyphens and nothing else; the apostrophe and the
  parentheses in the first wording were the fault, fixed in the slice. The second plan read `17 to add,
  0 to change, 0 to destroy`, with the rendered `gitlab.rb` as the S3 object's content (Lesson 54): the
  four `['env']` blocks carrying the 60-entry literal, `letsencrypt['enable'] = false`, the consolidated
  object storage with nine prefixes on `awsds-prod-gitlab-objects`, the backup upload to
  `awsds-prod-gitlab-backup`, Pages on `awsds-pages.internal` with access control, no SAML block. Applied:
  `17 added` at 06:38 UTC - the host `awsds-prod-gitlab` (`t4g.large`, `usw2-az1`), its 50 GiB data
  volume and the attachment, both security groups, the role and its profile, the DLM role and policy,
  the alarm, the S3 object and the two records.
- **[Claude] The `awsds` SSO token expired between the apply and the re-plan** (`refresh cached SSO
  token failed`, `CreateToken` `400`): the tooling re-plan, `terraform output` and the whole
  `production/registry/` apply failed on credentials before touching anything, so **`registry/` 5.b is
  not applied** and its plan (`8 to add, 6 to change, 0 to destroy` - the app-etl repository, three cache
  rules and three creation templates added; the six policies losing Staging's principal) is owed. The
  `aws` CLI kept answering for `awsds-infra-prod` from its cached role credential, which is how the
  readings below were taken. The session token lived about an hour and could not be refreshed.
