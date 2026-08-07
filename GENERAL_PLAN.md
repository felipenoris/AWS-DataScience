# General Implementation Plan

Staged plan to build the AWS Data Science environment described in `CLAUDE.md`.

## How to use this file

- `CLAUDE.md` holds the **goals and the working rules**. This file holds the **route** to get there.
- Every entry in the `Claude LOG` section of `CLAUDE.md` must reference the stage of this plan it belongs to
  (e.g. "Stage 3 - Networking, in progress").
- This plan is expected to change. Whenever a stage is finished or a decision is revisited, update this file
  and record the change in "Plan revision history" at the bottom.
- Stages are ordered by dependency, not by importance. A stage can be split or reordered, but the
  prerequisites listed inside each stage must hold.

---

## 1. Baseline (state at the time this plan was written: 2026-08-07)

**Repository**

- Documentation only: `CLAUDE.md`, `LOG.md`, `README.md`, `REFERENCES.md`, `GENERAL_PLAN.md`, `LICENSE`.
- `secrets/` (git-ignored) holds `accounts.md` and `sso-users.md`.
- `terraform/` exists but is empty. It must be replaced by `terraform-live/` and `terraform-modules/`
  (the layout defined in `CLAUDE.md`).
- Git remote is GitHub (`felipenoris/AWS-DataScience`). **This infrastructure repository stays on GitHub**;
  GitLab (Stage 7) hosts the *application* repositories and the CI/CD pipelines.

**Local tooling** (verified)

- `aws-cli` 2.36.18, `terraform` 1.15.8, `uv` installed.
- `~/.aws/config` has only a `[default]` profile with invalid credentials. No SSO profile configured yet.

**AWS**

- Management Account created manually through the AWS console. Nothing else exists.

**Planned accounts** (`secrets/accounts.md`): Management, Sandbox, Production, Log Archive, Audit,
Identity — all six e-mails are registered.
**Planned SSO users** (`secrets/sso-users.md`): infrastructure (admin), sandbox (regular), manager (approvals).

**Region:** `us-west-2` (decision D1, recorded in `CLAUDE.md`).

---

## 2. Guiding principles

These come from `CLAUDE.md` and constrain every stage:

1. **The Management account is bootstrap-only.** Anything done there is manual, through the console, and
   recorded by the user in `LOG.md`. Terraform does not manage the Management account.
2. **No IAM Users.** Humans authenticate through IAM Identity Center (SSO) and assume roles. Machines
   (GitLab CI) use OIDC federation to assume roles. No long-lived access keys anywhere.
3. **Everything else is Terraform.** One state per account/environment, no shared state across environments.
4. **Private by default.** Data assets and databases never face the public internet. The only public entry
   points are the VPN and, later (Stage 13), an experimental web tier.
5. **Incremental.** Each stage must leave the environment in a working, verifiable state.
6. **Cost is a first-class constraint.** This is a personal account. Every stage lists its recurring cost and,
   where relevant, a cheaper alternative.
7. **Pay nothing while idle** (decision D11). Between sessions, metered resources are destroyed, stateful
   ones are stopped, and anything free at rest is simply left alone. See §5.1 — every stage must say which
   layer its resources belong to, so this shapes how each stage is designed, not just how it is operated.
8. **The region is a variable, not an assumption** (decision D1). The lab runs in `us-west-2` and stays
   there; keeping the region out of the code is plain Terraform hygiene, not migration work. See §4.1.

---

## 3. Target architecture (summary)

Layers per §5.1: `[P]` persistent (free at rest), `[D]` dormant (stopped between sessions),
`[E]` ephemeral (destroyed between sessions).

```
AWS Organization (Management account - console only)                        [P]
├── Log Archive account      (created by Control Tower)                     [P]
├── Audit account            (created by Control Tower) <- security guardian [P]
├── Identity account         <- Identity Center delegated administration    [P]
├── Sandbox account          <- data scientists work here
│   ├── VPC, subnets, IGW, security groups, private DNS zone                [P]
│   ├── S3 (raw/curated/artifacts) + Glue Catalog (Iceberg) + Athena        [P]
│   ├── Lake Formation (fine-grained permissions, cross-account share)      [P]
│   ├── ECR (dev-env images, application images)                            [P]
│   ├── WireGuard EC2        <- the only human entry point                  [D]
│   ├── GitLab (EC2, private) + GitLab Pages                                [D]
│   ├── NAT Gateway + interface VPC endpoints                               [E]
│   ├── SageMaker Studio domain (VPC-only, restricted egress)               [E]
│   ├── EFS (NFS shared filesystem, synced to S3 before teardown)           [E]
│   └── GitLab Runners                                                      [E]
└── Production account       <- only Terraform and CI/CD touch this
    ├── VPC (mirrors sandbox topology)                                      [P]
    ├── S3 + Glue Data Catalog (Iceberg) + Lake Formation                   [P]
    ├── ECR (promoted images) / or cross-account pull from sandbox          [P]
    ├── MWAA or Step Functions (workflow execution)                         [E]
    └── (Stage 13) public web tier -> private backend                       [E]
```

---

## 4. Key decisions

| # | Decision | Status | Notes |
|---|---|---|---|
| D1 | Region | Decided (2026-08-07): **`us-west-2`**, and it stays there | Oregon, chosen on cost — roughly half São Paulo's price on metered items. Data residency is explicitly not a concern: this is a test with no real data. The project mirrors something that would run in `sa-east-1` in practice, but **that move is hypothetical and is not planned work**; the only thing it implies is the Terraform hygiene in §4.1, which is worth doing anyway. The availability question was answered and recorded there: nothing this plan uses is missing from São Paulo. |
| D2 | Control Tower vs. plain Organizations | Decided: **Control Tower** | Required by `CLAUDE.md`. It creates the Log Archive and Audit accounts, enables CloudTrail/Config org-wide and provides guardrails. Downside: AWS Config is the main recurring cost of the landing zone. |
| D3 | Terraform state location | Decided: **per-account S3 bucket, native S3 locking** | Terraform 1.15 supports `use_lockfile = true`, so no DynamoDB table is needed. Sandbox state lives in the Sandbox account, Production state in the Production account, and identity state in the Identity account (D10). This avoids putting state in the Management account (principle 1) and avoids cross-account state access. |
| D4 | VPN technology | Decided (2026-08-07): **self-managed WireGuard** | A `t4g.nano` EC2 instance in a public subnet, layer `[D]` — stopped between sessions, not destroyed, so the host key and peer configuration stay stable. Idle cost is its 8 GB EBS volume (~USD 0.65/month) plus the Elastic IP, which lives in the `[P]` foundation slice (~USD 3.65/month) so the endpoint address never changes. Consequences to handle in Stage 4: no native Identity Center integration, so peer public keys are provisioned by Terraform from a git-ignored variable file; and it is a single point of failure, which is acceptable for a lab. AWS Client VPN (~USD 73/month, SAML to Identity Center) stays documented as the managed alternative if SSO-integrated VPN becomes a requirement. |
| D5 | SageMaker internet restriction mechanism | **DEFERRED to Stage 6** | Options carried forward: (a) **Route 53 Resolver DNS Firewall** with a domain allowlist — cheap, blocks by DNS name, bypassable by raw IP. (b) **Squid proxy on EC2** with an allowlist — cheap, full HTTP(S) control, needs maintenance. (c) **AWS Network Firewall** — real egress filtering with TLS SNI inspection, ~USD 290/month. Nothing before Stage 6 depends on this, provided Stage 3 leaves the NAT route table and egress path easy to reshape. |
| D6 | DLP approach | Decided (2026-08-07): **native AWS combination** | The objective in `CLAUDE.md` is now split into the four problems it has to solve, each with its own control: discovery/classification → **Macie**; fine-grained access → **Lake Formation** (LF-Tags, column and row filters); egress control → **D5** plus the SageMaker VPC-only domain; exfiltration detection → **CloudTrail data events + GuardDuty + Security Hub** with CloudWatch alarms. A third-party agent-based DLP is only evaluated in Stage 11, after these four are in place and their gaps are known. |
| D7 | Workflow orchestration in production | **DEFERRED to Stage 10** | Options carried forward: **Step Functions + ECS/Fargate** (pay per execution, near-zero idle cost — the natural fit for an ephemeral lab), **MWAA** (~USD 350+/month, but it is what `CLAUDE.md` names explicitly), or **self-managed Airflow on ECS**. The decision only becomes real once an application from Stage 8 needs scheduling. Keep the application's entry point a plain container so it can be driven by any of the three. |
| D8 | GitLab hosting | Decided: **self-managed on EC2, layer `[D]`** | Required by `CLAUDE.md`. GitLab CE Omnibus on a private-subnet EC2 instance, reached through the VPN, backed up to S3. Sizing: 8 GB RAM is the realistic minimum for GitLab + Pages — `t4g.large` (ARM) is ~20% cheaper than `t3.large` for the same memory and GitLab Omnibus ships arm64 packages. Stopped between sessions rather than destroyed (~USD 4/month of EBS), because rebuilding from backup on every session is the fragile path. |
| D9 | Number of AZs | Decided: **2 for subnets, 1 for metered endpoints** | Subnets, route tables and NAT-less network plumbing are free, so the topology spans 2 AZs and stays honest. Interface VPC endpoints are charged per AZ, so they default to a single AZ during lab sessions; a resource in the other AZ still resolves and reaches them, at the cost of cross-AZ traffic and no AZ redundancy — an acceptable trade in a lab, and a one-variable change if it ever is not. |
| D10 | Identity Center administration | Decided (2026-08-07): **delegated to a dedicated Identity account** | The Identity Center instance and its identity store are created in the Management account and cannot be moved; what is delegated is their *administration*. One member account is registered as delegated administrator (`sso.amazonaws.com`), and from there Terraform manages permission sets, groups and assignments — so Terraform never needs credentials in the Management account, which is what makes principle 1 real rather than aspirational. The role goes to a **dedicated Identity account** rather than to the Audit account: Audit stays the security guardian (GuardDuty, Security Hub, Macie findings) and Identity owns access management, so the two concerns do not share a blast radius. Costs one extra Control Tower-governed account, i.e. one more AWS Config recorder (~USD 0.50-1/month) — accepted in exchange for the separation. **Consequences:** (i) assignments whose *target* is the Management account cannot be managed from the delegated account and stay manual; (ii) the Identity account can grant administrative access to any account in the organization, so it is as sensitive as Management — the Sandbox user must never have access to it; (iii) Control Tower's own permission sets (`AWSAdministratorAccess` and friends) are left alone, since editing them causes landing-zone drift. |
| D11 | Lifecycle of the lab | Decided (2026-08-07): **resources are ephemeral, accounts are not** | The environment runs for a few hours per session and is shut down in between. Accounts, the Organization, Control Tower and Identity Center are never destroyed. Within the accounts the rule is not "destroy everything" but **"pay nothing while idle"**: resources that cost nothing at rest are simply left in place, resources that meter are destroyed, and stateful services that are awkward to rebuild are stopped rather than destroyed. Three layers, defined in §5.1. |
| D12 | Budget ceiling | Decided (2026-08-07): **USD 50/month** | With the three-layer model the projection is ~USD 15/month floor plus ~USD 0.25 per lab hour, so roughly USD 20/month at the expected usage. The AWS Budget created in Stage 1 alerts at 50/80/100% of USD 50. This ceiling is what rules out always-on GitLab (~USD 60/month by itself) and confirms the stop/start approach. |

### 4.1 Region portability

The lab runs in `us-west-2` and **stays there**. A move to São Paulo is hypothetical and is not planned
work — no stage builds towards it, and no migration procedure is maintained here.

What remains is ordinary Terraform hygiene, which costs nothing and is worth doing on its own merits:

| Thing | Rule |
|---|---|
| Region | A single `var.region`, set per environment in `.tfvars`. No `us-west-2` literal in `.tf` files. |
| Availability zones | `data.aws_availability_zones` indexed by position, never `us-west-2a`. |
| AMI IDs | AMI IDs are region-scoped. Resolve through SSM public parameters (e.g. `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64`), never a literal `ami-…`. |
| Bucket names | S3 names are globally unique — build them from variables rather than pasting a region in. |

Recorded for reference, from the check on 2026-08-07: `sa-east-1` has endpoints for every service this
plan uses — Control Tower, IAM Identity Center, SageMaker (Studio with `ml.t3.medium`, `ml.g5`, `p5.4xl`),
MWAA, Macie, GuardDuty, Security Hub, Lake Formation, Glue, Athena, EFS, ECR, Client VPN, Network Firewall
and Graviton `t4g`. So the answer to "would anything break in São Paulo?" is no; the differences are price
(~1.5-2x) and a lag on the newest SageMaker features. If a move ever became real, the one genuinely
expensive part would be redeploying the Control Tower landing zone, whose home region is fixed at
deployment time.

One cross-region rule is permanent and unrelated to any of this: ACM certificates for CloudFront must live
in `us-east-1` regardless of where the workload runs (relevant only at Stage 13).

---

## 5. Cost model

Because of D11 the relevant question is not "what does this cost per month" but "what is the floor when
nothing is running, and what does an hour of lab time add on top". Order-of-magnitude figures for
`us-west-2`, to be confirmed with the AWS Pricing Calculator before each stage.

**The floor — paid every month even with the lab shut down (~USD 15):**

| Item | Approx. USD/month | Note |
|---|---|---|
| Organization, accounts, Identity Center, VPC, subnets, IGW, security groups, IAM roles | 0 | These cost nothing at rest, so there is no reason to destroy them |
| GitLab EBS volume (50 GB gp3) | ~4.00 | Paid while the instance is stopped; this is the price of not rebuilding GitLab |
| Elastic IP for WireGuard | ~3.65 | All public IPv4 addresses are charged hourly, attached or not |
| KMS customer-managed keys (3) | ~3.00 | ~1.00 per key per month |
| S3 data + state + backups (~25 GB) | ~1.00 | |
| ECR images (~10 GB) | ~1.00 | |
| AWS Config (Control Tower) | ~1-3 | One recorder per governed account (six, per D10); scales with configuration changes, near zero while idle |
| Route 53 private hosted zone | ~0.50 | |
| WireGuard EBS (8 GB) + CloudWatch logs | ~1.00 | |

**Per hour of lab time — added while the environment is up (~USD 0.25/h):**

| Item | Approx. USD/h |
|---|---|
| NAT Gateway (1) + its public IPv4 | ~0.050 + 0.045/GB processed |
| Interface VPC endpoints (~6, single AZ per D9) | ~0.060 (~0.120 if spread across 2 AZs) |
| GitLab EC2 `t4g.large` | ~0.067 (`t3.large` would be ~0.083) |
| SageMaker Studio `ml.t3.medium` (per running app) | ~0.050 |
| WireGuard EC2 `t4g.nano` | ~0.004 |
| EFS, Athena, Glue | usage-based; negligible at lab scale |

**Projection:** USD 15 floor + 20 h/month × USD 0.25 ≈ **USD 20/month**, against the USD 50 ceiling (D12).

**What the ceiling rules out:** always-on GitLab (~USD 60/month on its own), AWS Client VPN
(~USD 73/month, the D4 alternative), Network Firewall (~USD 290/month, option D5c) and MWAA
(~USD 350/month, option D7). Any of these becomes affordable only as a short, deliberate experiment —
which is precisely what the operating model below is for.

**Guardrail:** AWS Budgets with e-mail alerts must exist before any compute is created (Stage 1).

### 5.1 Operating model: three layers (D11)

The naive reading of "destroy it between sessions" is wrong, because most AWS resources cost nothing at
rest. The rule is **pay nothing while idle**, not **destroy everything**. That splits the environment into
three layers, and every stage must say which layer each of its resources belongs to.

**[P] Persistent — created once, never destroyed.** Free or nearly free at rest, or too slow to rebuild:
the Organization, the six accounts, Control Tower, Identity Center, SCPs, Terraform state buckets, the
**VPC itself** (VPC, subnets, route tables, internet gateway, security groups, NACLs cost nothing),
Route 53 private zone, IAM roles, KMS keys, S3 data buckets, ECR repositories, budgets and alarms.

**[D] Dormant — kept, but powered off between sessions.** Stateful services where a rebuild is riskier
than the idle cost: the GitLab EC2 instance and its EBS volume, and the WireGuard instance. `make down`
stops them, `make up` starts them. Idle cost is their EBS volumes (~USD 4.65/month) plus the Elastic IP
that WireGuard re-attaches on start — the address itself is allocated in `[P]`, so it survives even if the
instance is replaced. This is what makes the Stage 7 backup/restore cycle a disaster-recovery procedure
rather than a daily dependency.

**[E] Ephemeral — destroyed at the end of a session.** Everything metered by the hour and rebuildable in
minutes: NAT Gateway, interface VPC endpoints, SageMaker domain and apps, EFS, GitLab Runners,
MWAA/Step Functions, the Stage 13 web tier.

**Rules this imposes:**

1. Terraform slices are split along these lines. `terraform destroy` of an `[E]` slice must never be able
   to reach a `[P]` resource; persistent buckets get `prevent_destroy` lifecycle blocks.
2. No state lives only inside an `[E]` resource. EFS content syncs to S3 before teardown; SageMaker Studio
   home directories are **scratch** — real work lives in GitLab or S3 (note that deleting a Studio domain
   deletes its home EFS unless a retention policy is set, and a retained filesystem is awkward to re-attach).
3. `make up` and `make down` per environment, in dependency order, and both must be tested. A rebuild that
   only works by hand is a bug.
4. Anything slow or awkward to create — Control Tower, accounts, ACM DNS validation, Identity Center —
   belongs in `[P]` by construction.
5. Keep addresses stable: private DNS names instead of IPs, and a retained Elastic IP for WireGuard, so
   client configs survive a rebuild.
6. Each stage documents its teardown as well as its build, and records the measured rebuild time.
7. The layer assignment is a cost judgement and can change. If a `[D]` service turns out to be cheap to
   rebuild, demote it to `[E]`; if an `[E]` rebuild proves slow or fragile, promote it to `[D]` and pay
   the idle cost.

---

## 6. Conventions (to be applied from Stage 2 onwards)

**Naming:** `<project>-<env>-<component>[-<detail>]`, lowercase with hyphens.
Project prefix: `awsds`. Example: `awsds-sandbox-vpc`, `awsds-prod-raw-data`.

**Mandatory tags on every resource:**
`Project=AWS-DataScience`, `Environment=sandbox|production|shared`, `ManagedBy=terraform`,
`Owner=<sso-user>`, `CostCenter=<stage>`.

**Terraform layout:**

Each slice carries its layer from §5.1: `[P]` persistent, `[D]` dormant (stop/start), `[E]` ephemeral.

```
terraform-live/
├── identity/             # [P] permission sets, groups, assignments - applied with the
│   │                     #     delegated-admin profile (D10); never touches Management
│   └── bootstrap/        # [P] state bucket for the Identity account
├── sandbox/
│   ├── bootstrap/        # [P] state bucket for this account (local state, committed)
│   ├── foundation/       # [P] VPC, subnets, route tables, IGW, security groups, private
│   │                     #     hosted zone, KMS keys, IAM roles, WireGuard Elastic IP
│   ├── data/             # [P] S3 buckets, ECR, Glue databases, Lake Formation registrations,
│   │                     #     Athena workgroup - all free or near-free at rest
│   ├── egress/           # [E] NAT gateway, interface VPC endpoints - the metered network
│   ├── shared-services/  # [D] GitLab EC2 + EBS, WireGuard EC2 (stopped, not destroyed)
│   ├── nfs/              # [E] EFS filesystem, mount targets, access points
│   ├── runners/          # [E] GitLab Runners
│   ├── sagemaker/        # [E] domain, user profiles, apps
│   └── app/
│       └── app-etl/      # [E]
└── production/
    └── ... (same slices)

terraform-modules/        # reusable: vpc, wireguard, iam-role, ecr-repo, s3-bucket, step-function, ...
```

`make down ENV=sandbox` destroys the `[E]` slices in reverse dependency order and stops the `[D]`
instances; `make up ENV=sandbox` starts the `[D]` instances and applies the `[E]` slices; `make status`
reports what is running and the current hourly burn. `[P]` slices are never touched by any of them — they
are applied deliberately, by hand.

**Terraform rules:**

- Pin the provider version and `required_version`. One `providers.tf` per slice.
- Region, AZs and AMIs follow the portability rules in §4.1 — no region literals in `.tf` files.
- Authentication through named SSO profiles (`awsds-infra-sandbox`, `awsds-infra-prod`) — never keys.
- Every slice: `terraform fmt`, `validate` and `plan` must be clean before apply.
- Remote state read across slices through `terraform_remote_state` data sources, never hardcoded IDs.

---

## 7. Stages

### Stage 0 - Baseline (DONE)

Management account created manually; `aws`, `terraform` and `uv` installed; repository documentation written
and reviewed. Nothing provisioned.

---

### Stage 1 - Organization, accounts and identity (manual, console)

**Objective:** a working AWS Organization with the environment accounts and SSO access, so that everything
after this can be done by Terraform without root credentials.

**Prerequisites:** none outstanding. D1 is decided (`us-west-2`) and all six account e-mails are in
`secrets/accounts.md`.

**To execute (all manual, by the user, recorded in `LOG.md`):**

1. Secure the Management account root user: hardware or virtual MFA, strong password, no access keys,
   billing alerts enabled.
2. Create a Budget of **USD 50/month** (D12) with e-mail alerts at 50%/80%/100%.
3. Enable AWS Control Tower with `us-west-2` as the home region. It will create the Organization, the
   Log Archive and the Audit accounts (e-mails already in `secrets/accounts.md`), and turn on org-wide
   CloudTrail and Config. Note: the home region cannot be changed afterwards without redeploying the
   landing zone.
4. Create the `Sandbox`, `Production` and `Identity` accounts through Account Factory, using the e-mails
   in `secrets/accounts.md`. OUs: `Sandbox` OU, `Production` OU, and `Identity` in the `Security` OU
   alongside Log Archive and Audit.
5. **Register the Identity account as delegated administrator of IAM Identity Center (D10).** From the
   Management account:
   `aws organizations register-delegated-administrator --account-id <IDENTITY_ACCOUNT_ID> --service-principal sso.amazonaws.com`.
   This is reversible (`deregister-delegated-administrator`), so it is a cheap step to get wrong.
   Everything in steps 6 and 7 is then done **from the Identity account**, not from Management.
6. In IAM Identity Center, create the three users from `secrets/sso-users.md` and the groups
   `infrastructure`, `data-scientists`, `managers`. Enforce MFA.
7. Create permission sets: `AdministratorAccess` (infrastructure), `DataScientistAccess` (sandbox, initially
   `PowerUserAccess`, tightened in Stage 6), `ReadOnlyAccess` and `DeployApprover` (managers).
   Assign them: infrastructure → Sandbox + Production + Identity; data-scientists → Sandbox; managers →
   Sandbox + Production, read-only plus approval. The Sandbox user gets no access to Identity or Audit.
   Leave Control Tower's own permission sets untouched — editing them causes landing-zone drift.
   These are created by hand here only because Terraform cannot run before SSO login works; Stage 2 moves
   them into `terraform-live/identity/` and imports them.
8. The infrastructure user's assignment **on the Management account itself** has to be created from the
   Management account — the delegated administrator cannot manage assignments targeting Management.
   This is the one identity task that stays there permanently.
9. Attach a first set of SCPs to the OUs: deny leaving the organization, deny disabling CloudTrail/Config,
   deny root user actions, and restrict usable regions to `us-west-2` — the region SCP must still allow
   `us-east-1`, because IAM, Organizations, Route 53, CloudFront and Support only have endpoints there.
10. Configure local SSO profiles: `aws configure sso` for `awsds-infra-sandbox`, `awsds-infra-prod` and
    `awsds-infra-identity`.

**Deliverables:** accounts created; SSO login working; `aws sts get-caller-identity --profile awsds-infra-sandbox`
returns the Sandbox account ID; `aws sso-admin list-instances --profile awsds-infra-identity` returns the
Identity Center instance, which is the proof that the delegation took effect.

**Blocking questions for the user:** none.

**Risks:** Control Tower landing zone deployment takes ~60 minutes and is awkward to undo. Account e-mails
cannot be reused after an account is closed (a closed account holds its e-mail for 90 days) — which is
exactly why D11 keeps accounts in the persistent layer. Everything created in this stage is persistent;
nothing here is torn down between sessions.

**To verify while executing this stage**, because Control Tower's handling of Identity Center has changed
more than once and the plan should not assume: (i) that the delegation coexists with the landing zone
without raising drift; (ii) that the restriction in step 8 is exactly as described — that assignments
targeting the Management account are the *only* thing the delegated administrator cannot manage; and
(iii) the AZ name-to-ID mapping across the Sandbox and Production accounts, which decides whether Stage 3
anchors subnets on list position or on AZ IDs (§4.1).

---

### Stage 2 - Terraform foundation

**Objective:** the repository can provision infrastructure reproducibly.

**Prerequisites:** Stage 1.

**To execute:**

1. Delete the empty `terraform/` folder; create `terraform-live/` and `terraform-modules/` as in §6.
2. `terraform-live/sandbox/bootstrap/`: S3 state bucket (versioning, SSE-KMS, public access blocked,
   `use_lockfile = true`). Applied once with local state, then the state file is committed — this is the
   documented chicken-and-egg exception.
3. Same for `terraform-live/production/bootstrap/` and `terraform-live/identity/bootstrap/`.
4. Migrate every subsequent slice to the remote backend.
5. `terraform-live/identity/`: import the permission sets, groups and assignments created by hand in
   Stage 1, so identity stops being console-managed (D10). Applied with the `awsds-infra-identity`
   profile. `terraform plan` must come back empty after the import — that is the check that the import
   is faithful.
6. Repository hygiene: `.gitignore` for `.terraform/` and `*.tfstate.backup`; `.terraform.lock.hcl` is
   committed on purpose; `pre-commit` with `terraform fmt`, `terraform validate` and `tflint`; optionally
   `checkov` for policy checks.
7. First reusable modules in `terraform-modules/`: `s3-bucket`, `iam-role`, `kms-key`.
8. **Teardown/rebuild tooling (D11).** Each slice declares its layer (`[P]`/`[D]`/`[E]`), and a `Makefile`
   at the repository root exposes `make up ENV=sandbox` / `make down ENV=sandbox`: `down` destroys the
   `[E]` slices in reverse dependency order and stops the `[D]` instances; `up` starts the `[D]` instances
   and applies the `[E]` slices. Both must refuse to touch `[P]` slices. Add `make status` to report what
   is currently running and the estimated hourly burn.
9. **No region literals (§4.1).** `var.region` in every slice, AZs from `data.aws_availability_zones`,
   AMIs from SSM public parameters. A `grep` check in CI that fails on a hardcoded region keeps this
   honest at no cost.
10. Update `README.md` with the repository layout and the AWS resource structure (required by `CLAUDE.md`).

**Deliverables:** `terraform apply` works end-to-end against the Sandbox account using an SSO profile;
the `Makefile` exists with the slice-to-layer table wired up, even though no `[E]` or `[D]` slice exists
yet — `make down` at this point must be a safe no-op, not a command that reaches the `[P]` bootstrap slice.

**Validation:** destroy and re-create a throwaway `[E]` slice to prove reproducibility, and confirm
`make down` leaves `bootstrap/` untouched.

---

### Stage 3 - Networking (Sandbox)

**Objective:** the private network that everything else sits in.

**Prerequisites:** Stage 2.

**To execute:**

The network is split across two slices, because the free half and the metered half have different
lifecycles (§5.1).

*`foundation/` — layer `[P]`, costs nothing at rest, never destroyed:*

1. `terraform-modules/vpc/`: VPC (e.g. `10.20.0.0/16` sandbox, `10.30.0.0/16` production — non-overlapping,
   so they can be peered later), 2 AZs, public + private + isolated (data) subnets.
2. Internet Gateway, route tables, NACLs, baseline security groups.
3. S3 and DynamoDB **gateway** endpoints — these are free, so they live here.
4. Route 53 private hosted zone (e.g. `sandbox.internal`).
5. VPC Flow Logs to CloudWatch Logs with a short retention (a few days — retention is what costs).

*`egress/` — layer `[E]`, destroyed at the end of every session:*

6. A single NAT Gateway, with a documented switch for one-per-AZ.
7. Interface VPC endpoints, added on demand per stage (`sts`, `logs`, `ecr.api`, `ecr.dkr`,
   `sagemaker.api`, `sagemaker.runtime`, `elasticfilesystem`). Default to a single AZ during lab sessions
   (D9) — at ~USD 0.01/h per endpoint per AZ, two AZs doubles the largest hourly line item. A resource in
   the other AZ still resolves the endpoint DNS and reaches it; the cost is cross-AZ traffic and the loss
   of AZ redundancy, neither of which matters in a lab.
8. Keep this slice's route-table associations parameterised, so D5 (Stage 6) can insert a firewall or proxy
   into the egress path without reshaping the foundation.

**Deliverables:** VPC applied by Terraform, flow logs visible, endpoints resolving privately, and
`make down` followed by `make up` restoring internet egress without touching the VPC.

**Cost note:** this is where the metered bill starts, and `egress/` is the single biggest hourly cost of the
lab: ~USD 0.11/h with 6 endpoints in one AZ, ~USD 0.17/h across two. Keep the endpoint list minimal.

---

### Stage 4 - VPN access

**Objective:** the only human path into the private network.

**Prerequisites:** Stage 3. D4 is decided: self-managed WireGuard.

**To execute:**

1. `terraform-modules/wireguard/`: `t4g.nano` (ARM, Amazon Linux 2023) in a public subnet, WireGuard
   installed and configured by user data, IP forwarding and NAT to the VPC CIDR enabled.
   Layer `[D]`: the instance is **stopped** between sessions, not destroyed (~USD 0.65/month of EBS),
   which keeps the host key and the peer configuration stable.
2. Elastic IP allocated in the `[P]` foundation slice and re-associated on start, so the endpoint address
   survives a teardown and client configs never have to be regenerated. ~USD 3.65/month — the price of not
   editing every client config on every rebuild.
3. Security group allowing only UDP/51820 inbound; SSH access only through SSM Session Manager, never
   port 22 from the internet.
4. Peer public keys supplied through a git-ignored `.tfvars` (keys are generated on the client and the
   private key never leaves the laptop). One peer per person and per device.
5. Split tunnel: only the VPC CIDRs are routed through the tunnel. `DNS` in the client config points at
   the VPC resolver (`.2` of the VPC CIDR) so private hosted zones and VPC endpoints resolve.
6. Route table entry so private subnets can answer the WireGuard peer network.
7. CloudWatch agent shipping the WireGuard handshake log; alarm if the instance is unhealthy.
8. Write the client setup instructions in `README.md`, including how to regenerate the config after a
   rebuild.

**Deliverables:** connecting from the laptop gives private access to a test resource; the same resource is
unreachable with the tunnel down; `make down` followed by `make up` restores connectivity without changing
the client configuration.

**Known trade-off (D4):** no Identity Center integration — revoking a person's access means removing their
peer and re-applying. Acceptable for a single-operator lab, and the reason AWS Client VPN stays documented
as the alternative.

---

### Stage 5 - Data foundation (S3, NFS, Glue, Iceberg, Lake Formation)

**Objective:** where data lives and how it is catalogued.

**Prerequisites:** Stage 3.

**To execute:**

Like Stage 3, this stage spans two slices with different lifecycles: the data itself never goes away, the
filesystem in front of it does.

*`data/` — layer `[P]`, and the KMS CMKs it uses live in `foundation/`:*

1. KMS CMKs per data domain; S3 buckets `raw`, `curated`, `artifacts`, `athena-results`, `logs` with
   versioning, encryption, lifecycle rules, `prevent_destroy`, and a bucket policy that denies access not
   coming through the VPC endpoint.
2. Glue Data Catalog databases (`raw`, `curated`); Glue crawlers only where they earn their keep.
3. Iceberg tables on S3, queried through Athena; Athena workgroup with a result bucket and a per-query
   data scan limit (cost guardrail).
4. Enable Lake Formation as the permission model for the catalog; register the S3 locations; define
   LF-Tags for the classification scheme that Stage 11 will build on.

*`nfs/` — layer `[E]`, destroyed with the session:*

5. EFS filesystem + mount targets in the private subnets, access points per group; this is the NFS layer
   shared between users and SageMaker. Decide the S3 ↔ EFS synchronisation pattern (DataSync, or an
   explicit copy in code — DataSync costs per GB moved).
6. **S3 is the source of truth.** The sync back to S3 runs before teardown and is part of `make down`;
   a `make down` that silently loses EFS content is the single most likely way to lose real work in this
   design, so this step gets tested deliberately, not assumed.

**Deliverables:** a sample Iceberg table written and queried through Athena, with access granted through
Lake Formation rather than raw IAM policies; and an EFS teardown/rebuild cycle that provably preserves
its content.

---

### Stage 6 - SageMaker Studio (Sandbox)

**Objective:** the data scientist's working environment.

**Prerequisites:** Stages 3, 4, 5. **D5 is taken at the start of this stage** — it is not an external
input, it is this stage's first decision (step 3 below).

**To execute:**

1. SageMaker Studio domain in **VPC-only** mode, in the private subnets, with the interface endpoints
   from Stage 3.
2. Execution roles per user profile, scoped to the sandbox buckets and the Glue/Lake Formation permissions
   from Stage 5. Map user profiles to the Identity Center users.
3. Controlled internet egress (D5): allowlist for PyPI, conda, the distro package mirrors, the GitLab
   host and whatever else is agreed. Everything else denied and logged.
4. Attach EFS access points for the shared NFS area.
5. Lifecycle configuration for idle shutdown — mandatory cost control.
   Layer `[E]`: the domain is destroyed at the end of each session. Consequence to design around —
   deleting a domain deletes its home EFS unless a retention policy is set, and a retained filesystem is
   awkward to re-attach to a new domain. **Studio home directories are scratch**: notebooks live in GitLab,
   data lives in S3, shared files live on the Stage 5 EFS. State this to users explicitly.
6. Tighten the `DataScientistAccess` permission set to what Studio actually needs (no infrastructure
   changes outside SageMaker-managed resources, as required by `CLAUDE.md`).
7. CloudWatch log groups and metrics for the domain.

**Deliverables:** the sandbox SSO user logs in through the VPN, opens Studio, installs a package from
PyPI, reads an Iceberg table, writes to EFS — and cannot reach a non-allowlisted site.

---

### Stage 7 - GitLab, Runners and ECR

**Objective:** source control, docs hosting and a container registry, all private.

**Prerequisites:** Stages 3, 4; decision D8.

**To execute:**

1. GitLab CE Omnibus on EC2 in a private subnet; EBS with a snapshot schedule; internal ALB/NLB with an
   ACM certificate; Route 53 record in the private zone.
   **Layer `[D]` (dormant), decided up front.** GitLab holds real state — repositories, CI history,
   registry metadata — and rebuilding it from a backup on every session is exactly the kind of fragile
   daily dependency §5.1 rule 2 warns about. So the instance and its EBS volume are **stopped**, not
   destroyed: ~USD 4/month idle, ~3-5 minutes to boot. Always-on would be ~USD 60/month, which the
   USD 50 ceiling (D12) rules out.
   Backups are still mandatory, but as disaster recovery rather than routine operation: scheduled
   `gitlab-backup create` to a `[P]` S3 bucket, plus `gitlab-secrets.json` in Secrets Manager — without
   that file a restored backup cannot decrypt its own data. Test the full backup → destroy → restore cycle
   once, so the recovery path is known to work.
   Instance type per D8: `t4g.large` (ARM, 8 GB).
2. SAML integration between GitLab and IAM Identity Center, so GitLab has no local accounts.
3. GitLab Pages enabled for documentation, reachable only through the VPN.
4. GitLab Runners in the `runners/` slice, layer `[E]`: autoscaling on EC2 or Fargate, in the private
   subnet, with an instance role that can push to ECR. Container builds with Kaniko or BuildKit (no
   privileged Docker-in-Docker). Runners hold no state worth keeping, so they are rebuilt every session.
5. ECR repositories in the `data/` slice, layer `[P]` — images survive teardown, which is the whole point
   of having a registry: `dev-env` (SageMaker images), `app/*` (application images). Lifecycle policies to
   expire untagged images. Repository policy allowing the Production account to pull.
6. Decide and document the mirroring policy between this GitHub repository and GitLab.
7. Add GitLab start/stop to `make up` / `make down`, and measure the boot time — if it turns out to be
   much worse than the ~3-5 minutes assumed in D8, revisit the layer choice (§5.1 rule 7).

**Deliverables:** a repository pushed to GitLab, a pipeline running on a private runner, an image in ECR,
a docs site served by Pages.

---

### Stage 8 - CI/CD pipelines (the three types)

**Objective:** the automation described in `CLAUDE.md`.

**Prerequisites:** Stage 7.

**To execute:**

1. **Development-environment pipeline:** builds the Docker image used by data scientists, pushes it to ECR
   and registers it as a SageMaker custom image / app image config. Triggered by tags.
2. **Application build pipeline:** the `app-etl` template from `CLAUDE.md` — `uv` for dependencies,
   `pytest` for tests, linting, docs build published to Pages, Docker image pushed to ECR on tag.
3. **Production deploy pipeline:** GitLab OIDC → assume an IAM role in the Production account (no static
   keys), promote the image, run `terraform apply` for `terraform-live/production/app/app-etl/` pinned to the
   application tag, with a manual approval gate assigned to the `managers` group.
4. A pipeline for this infrastructure repository as well: `fmt` / `validate` / `plan` on merge requests,
   `apply` gated by approval.

**Deliverables:** a version tag on `app-etl` flows automatically from source to a running artifact in
Production, with one human approval.

---

### Stage 9 - Production account and cross-account data sharing

**Objective:** a production environment that mirrors sandbox and shares data with it under control.

**Prerequisites:** Stages 3, 5, 8.

**To execute:**

1. Re-apply the networking and data slices in the Production account using the same modules
   (different CIDRs, tighter policies).
2. Lake Formation cross-account sharing: production catalog resources shared read-only with the sandbox
   account for the `data-scientists` group; nothing flows the other way except through the deploy pipeline.
3. Cross-account IAM: the deploy role, the ECR pull policy, KMS key grants.
4. Confirm the SCPs actually prevent the sandbox user from changing production infrastructure.

**Deliverables:** the sandbox user reads a production table from Studio and is denied on write.

---

### Stage 10 - Workflow orchestration and promotion

**Objective:** take a workflow developed in SageMaker and run it in production on a schedule.

**Prerequisites:** Stages 8, 9. **D7 is taken at the start of this stage**, once a real application
finally needs scheduling — that is the point at which the MWAA-versus-Step-Functions trade stops being
abstract.

**To execute:**

1. Implement the chosen orchestrator (Step Functions module, or an MWAA environment).
2. Define how a SageMaker-developed pipeline becomes a deployable artifact — most likely a container plus
   a workflow definition, both versioned in the application repository.
3. Schedule, retry, alerting on failure to CloudWatch/SNS.
4. If MWAA is used, document how to create and destroy it on demand to avoid the idle cost.

**Deliverables:** a workflow developed in the sandbox runs on schedule in production without manual steps.

---

### Stage 11 - Data protection and DLP

**Objective:** the protection layer, built on top of a working environment rather than before it.

**Prerequisites:** Stages 5, 6, 9; decision D6.

**To execute:**

1. Amazon Macie for sensitive-data discovery on the S3 buckets; findings to Security Hub.
2. Lake Formation column-level and row-level filters driven by the LF-Tags from Stage 5.
3. Egress hardening review of Stage 6 (D5); block SageMaker Studio file download / notebook export where
   the requirement calls for it.
4. GuardDuty (including S3 and Malware Protection) and Security Hub enabled org-wide from the Audit account.
5. CloudTrail data events on the sensitive buckets; CloudWatch alarms for exfiltration patterns
   (mass `GetObject`, unusual egress volume, presigned URL creation).
6. Only then evaluate whether a third-party DLP agent adds anything the above does not cover.

**Deliverables:** a documented threat model with the control that addresses each item, and alarms that fire
on a simulated exfiltration attempt.

---

### Stage 12 - Observability, governance and FinOps

**Objective:** know what is running, what it costs, and be told when something breaks.

**Prerequisites:** any stage that created resources.

**To execute:**

1. CloudWatch dashboards per environment (SageMaker, GitLab, VPN, NAT traffic, Athena scans).
2. Alarms → SNS → e-mail for: budget thresholds, failed pipelines, VPN down, GitLab unhealthy,
   unusual data scans.
3. Log retention policies everywhere (default retention is "forever", which quietly costs money).
4. Cost allocation tags activated in Billing; a monthly cost review against §5.
5. **Review the `[P]`/`[D]`/`[E]` assignments against the real bill**, which by this point exists. The two
   estimates most likely to be wrong are the interface endpoints (the largest hourly item) and GitLab
   (the largest idle item). Update §5 and §5.1 with measured numbers rather than the projections.
6. Config rules / conformance packs on top of the Control Tower guardrails.
7. Tighten the permission sets in `terraform-live/identity/` against real usage, using IAM Access Analyzer
   — `DataScientistAccess` in particular, which starts as `PowerUserAccess` in Stage 1.

---

### Stage 13 - Public-facing web tier (experiment)

**Objective:** the experiment described in `CLAUDE.md` — a public web server reaching a private backend.

**Prerequisites:** Stages 3, 9.

**To execute:**

1. Public ALB in the public subnets with WAF and an ACM certificate; a public Route 53 hosted zone.
2. Application on ECS Fargate in the private subnets; database (RDS or the Iceberg catalog through Athena)
   in the isolated subnets.
3. Security groups allowing only ALB → app → data, and nothing else.
4. Document the blast radius and how to tear the whole tier down.

---

## 8. Cross-cutting work (continuous, not a stage)

- `LOG.md`: the user records every manual step (never edited by Claude).
- `CLAUDE.md` → `Claude LOG`: updated at the end of each stage, referencing the stage number from this plan.
- `REFERENCES.md`: every link used as a reference.
- `README.md`: kept in sync with the real resource structure and repository layout.
- `GENERAL_PLAN.md`: revised whenever a decision changes or a stage is re-scoped.

---

## 9. Open questions

**Resolved on 2026-08-07:** region → `us-west-2` (D1); Control Tower account e-mails → registered in
`secrets/accounts.md`; VPN → WireGuard (D4); DLP → native AWS combination (D6); lifecycle → resources
ephemeral, accounts permanent (D11); budget → USD 50/month (D12); Identity Center administration →
delegated to a dedicated Identity account (D10).

**Still open, none blocking Stage 1:**

1. **D5 - SageMaker egress restriction.** Decided at Stage 6. Stage 3 must leave the egress path easy to
   reshape so this stays a cheap decision.
2. **D7 - Production orchestrator.** Decided at Stage 10. Keep application entry points as plain containers
   so any of the three options remains viable.
3. **AZ name-to-ID mapping across accounts.** AWS maps AZ names to physical datacenters independently per
   account, so `data.aws_availability_zones` indexed by position can place "the same" AZ in different
   datacenters in Sandbox and Production — which turns peering traffic that looks intra-AZ into
   cross-AZ traffic at USD 0.01/GB each way. Check it in Stage 1, once the accounts exist
   (`aws ec2 describe-availability-zones --query 'AvailabilityZones[].[ZoneName,ZoneId]'` under each
   profile). If the mappings differ, Stage 3 anchors subnets on `zone_ids` (`usw2-az1`, passed per
   environment in `.tfvars`) instead of on list position, and §4.1 is updated accordingly.
4. **Layer assignments.** `[P]`/`[D]`/`[E]` are cost judgements based on estimates. Revisit them at Stage 12
   against the real bill — especially the interface endpoints (the largest hourly item) and GitLab
   (the largest idle item).

---

## 10. Plan revision history

| Date | Change |
|---|---|
| 2026-08-07 | Initial version. Stages 0-13 defined; decisions D1-D10 registered, D1/D4/D5/D6/D7/D10 still open. |
| 2026-08-07 | Decisions closed: D1 = `us-west-2`, D4 = self-managed WireGuard, D6 = native AWS combination (the DLP objective in `CLAUDE.md` was split into discovery, access control, egress control and exfiltration detection). D5 and D7 explicitly deferred to the stages that consume them (6 and 10). New decision D11: the lab is ephemeral — added §5.1 (operating model), reworked §5 (cost model now hourly plus a persistent floor), tagged the Terraform slices persistent/ephemeral in §6, and added the teardown/restore requirements to Stages 2, 4, 5 and 7. Stage 1 unblocked: all five account e-mails are registered. |
| 2026-08-07 | Revision after user feedback. D11 restated: the unit of teardown is **resources, not accounts**, and the rule is "pay nothing while idle" rather than "destroy everything" — most AWS resources cost nothing at rest. §5.1 replaced the persistent/ephemeral binary with **three layers** `[P]`/`[D]`/`[E]`, which moved the VPC itself into `[P]` (free at rest) and GitLab and WireGuard into `[D]` (stopped, not destroyed). That removed the backup/restore cycle from the critical path in Stage 7 and split Stage 3 into `foundation/` `[P]` and `egress/` `[E]`. New decision D12: budget ceiling USD 50/month, which is what rules out always-on GitLab, Client VPN, Network Firewall and MWAA. §5 rewritten as a ~USD 15 monthly floor plus ~USD 0.30 per lab hour (~USD 21/month at the expected usage). D1 note corrected: `sa-east-1` was verified against the AWS endpoint tables and is **not** a service-availability problem — the difference is price (~1.5-2x), instance/GPU selection and feature lag. |
| 2026-08-07 | Region question settled. `us-west-2` on cost, and it stays there — LGPD/data residency dropped as a driver (no real data). The `sa-east-1` availability check was recorded as a fact in §4.1, and its answer is that nothing this plan uses is missing from São Paulo; a correction to the previous entry, which wrongly called São Paulo's GPU selection thin (SageMaker Studio has `ml.g5` there since 2023 and `p5.4xl` since 2026, and `t4g` Graviton is available). A move to São Paulo is **hypothetical and not planned work**, so §4.1 was cut back to plain Terraform hygiene — no region literals, AZs from data sources, AMIs from SSM parameters — and the migration checklist, verification commands and the Stage 12 `sa-east-1` trial were dropped. |
| 2026-08-07 | **Consistency review of the whole plan**, after the incremental edits above had left it contradicting itself. Fixed: principle 7 still said "resources are destroyed between sessions" (pre-dates the three-layer model); D4 still described WireGuard as destroyed each session; the WireGuard Elastic IP was assigned to `[D]` in §5.1, `[P]` in Stage 4 and `[D]` in the §6 layout (now `[P]` everywhere); D9 read as "2 AZs" while Stage 3 defaulted endpoints to one AZ (now stated as 2 for subnets, 1 for metered endpoints); the §3 diagram carried no layer markers; §5 priced GitLab as `t3.large` while Stage 7 recommended `t4g.large`; Stage 2's deliverable asked `make down` to drive the `[P]` bootstrap slice, contradicting its own rule; Stages 6 and 10 listed D5/D7 as prerequisites when those decisions are taken *inside* those stages; Stage 5 mixed `[P]` data and `[E]` EFS with no slice boundary (added an `nfs/` slice); Stage 7 did not say which slice ECR and the runners belong to. Also corrected a wrong SSM parameter path in §4.1 (`ami-amazon-linux-latest`, not `ami-amazon-latest`), recalculated the hourly figure against the single-AZ endpoint default (~USD 0.25/h, ~USD 20/month, replacing ~USD 0.30 and ~USD 21 in the entry above), and reordered the two entries above into actual chronological order. |
| 2026-08-07 | **D10 closed: Identity Center administration is delegated to a dedicated Identity account**, a sixth account added to `secrets/accounts.md`. The instance itself stays in Management (it cannot be moved); only its administration is delegated, which lets Terraform manage permission sets without ever holding Management credentials — principle 1 enforced rather than merely stated. Audit keeps a single role, security guardian, and does not also own access management. Updated: §1 (six accounts), the §3 diagram, §5 (Config is per governed account), §5.1, D3 (identity state in the Identity account), Stage 1 (Identity account via Account Factory in the `Security` OU, the `register-delegated-administrator` step, identity work moved out of Management, and the Management-targeted assignment called out as permanently manual), Stage 2 (identity bootstrap plus an import of the Stage 1 console resources), the §6 layout (`terraform-live/identity/`) and Stage 12 (D10 revisit replaced by permission-set tightening). Cost of the decision: one more AWS Config recorder, ~USD 0.50-1/month. Two Control Tower/Identity Center behaviours are flagged in Stage 1 as *to verify during execution* rather than assumed. Also recorded in §9 as open item 3: the AZ name-to-ID mapping between Sandbox and Production, to be checked once the accounts exist, since it decides whether Stage 3 anchors subnets on list position or on AZ IDs. |
