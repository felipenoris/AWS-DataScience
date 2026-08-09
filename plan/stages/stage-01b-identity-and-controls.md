# Stage 1b — Identity, policies, detective controls, org-wide enablement

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stage 1a complete |
| **Consumes** | [D10](../decisions/D10-identity-center-delegation.md), [D11](../decisions/D11-lab-lifecycle.md), [D12](../decisions/D12-budget-ceiling.md), [D14](../decisions/D14-supply-chain-account.md), [D15](../decisions/D15-tls-internal.md), [D16](../decisions/D16-break-glass.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D18](../decisions/D18-data-scientist-access.md), [D19](../decisions/D19-derived-zone.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D23](../decisions/D23-ou-structure.md), [D25](../decisions/D25-drop-box-consumer.md), [D29](../decisions/D29-policy-canary.md), [D31](../decisions/D31-approver-read.md), [D32](../decisions/D32-account-factory-sso-user.md), [D33](../decisions/D33-control-tower-admin-user.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | [INT-11](../integrations.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

Everything in 1b is fast, reversible and iterative — which is exactly why it is separated from the half
that is not.

1. **Register the Identity account as delegated administrator of IAM Identity Center (D10).** From the
   Management account:
   `aws organizations register-delegated-administrator --account-id <IDENTITY_ACCOUNT_ID> --service-principal sso.amazonaws.com`.
   This is reversible (`deregister-delegated-administrator`), so it is a cheap step to get wrong.
   Everything in steps 2 and 3 is then done **from the Identity account**, not from Management.
   **One property of delegation that is easy to miss and is load-bearing here:** an Identity Center delegated
   administrator can manage **groups assigned to the Management account** — including Control Tower's
   `AWSControlTowerAdmins`. So whoever administers this account can grant themselves Management
   administrator by editing a group membership. That is the same blast radius `ORGANIZATION.md`
   already ascribes to the Identity account ("whoever controls Identity can grant access to any account");
   it is recorded here because these particular groups (D33) make it concrete rather than theoretical.
2. In IAM Identity Center, create the users from `ORGANIZATION.md` (e-mails in `secrets/emails.md`)
   and the groups `infrastructure`, `data-scientists`, **`deployment-managers`**, **`governance-managers`**
   and **`dev-env-stewards`**. Enforce MFA.
   **The infrastructure user is not created here — it already exists (D32).** Account Factory created it in
   1a step 4 from the `SSOUserEmail` field, and it already holds a direct administrator assignment on every
   vended account. So this step creates **four** users, not five, and the only thing to do about the fifth
   is to put it in the `infrastructure` group. Re-creating it under a second address gives one human two
   administrators, one of which nobody is watching.
   **This step does not start from an empty directory, and it was written as if it did.** Enabling Control
   Tower in 1a step 3 created the Identity Center directory *and populated it* — its own groups
   (`AWSAccountFactory`, `AWSControlTowerAdmins`, the auditor groups, one administrator group per vended
   account), its own permission sets, and a first administrator. **Enumerate what is already there before
   creating anything**, and treat the two sets as separate: Control Tower owns its objects and may re-create
   them, this stage owns `infrastructure`, `data-scientists`, `deployment-managers`, `governance-managers`
   and `dev-env-stewards`. **Do not add a project persona to a Control Tower group and do not repurpose
   one** — those groups arrive with their assignments already made, so a membership edit is an
   organization-wide grant: `AWSControlTowerAdmins` is administrator on Management, Log Archive *and* Audit,
   and `AWSSecurityAuditPowerUsers` is `AWSPowerUserAccess` on every account. They are empty today, and
   empty is not the same as harmless.
   **The sixth identity is `AWS Control Tower Admin` (D33), and it stays (D34).** Created with the Management
   root's e-mail, it is not a *persona* of this plan — no project group, not the infrastructure user — but it
   does hold one duty: it is the standing owner of Control Tower administration, creating OUs and vending
   accounts from the console. **Do not disable it.** An earlier version of this step retired it here, on the
   premise that vending ends inside Stage 1a; the account list is not static, so what it needed was an owner
   and not an end date. Three consequences for this stage:
   - **Its MFA is a standing control** (set in 1a step 3), not a stopgap for a few days.
   - **Do not add it to any project group and do not give it a project permission set.** Its whole footprint
     stays the two Control Tower groups it arrived with.
   - **The narrow alternative stays documented and unused**, so nobody rediscovers it as a fault:
     `AWSAccountFactory` alone reaches the Account Factory product through the **Service Catalog** console,
     which is enough to *vend into an existing OU* but not to reach the **Control Tower console** — where OUs
     are created and accounts enrolled — which AWS documents as reachable only by `AWSControlTowerAdmins`
     members. Creating OUs is part of the job, which is what decided D34.
   **Prerequisite to check first: `secrets/emails.md` must carry an address for every user created here.**
   Verified on 2026-08-08 — it does, including the **Dev Env Steward**, which was missing when this step was
   first written. An Identity Center user cannot be created without one, so re-check before starting rather
   than half-way through.
   The approver groups were a single `managers` group until 2026-08-08 and have been split twice since,
   each time along a different axis — release (lifecycle), data access (ownership), runtime image (supply
   chain). The reason is cumulative and it is the whole point: one persona holding all of them means a
   single human can write a job that reads restricted data, approve its release, approve its access to that
   data, **and** approve the runtime image the job was written on — four acts, one signature.
   **Never put the same person in more than one of these groups**, or in one of them plus
   `data-scientists`, even while there is only one human: the moment that happens the split is notation
   again, and nothing in AWS will warn you.
3. Create permission sets: `AdministratorAccess` (infrastructure), `DataScientistAccess` (the Interactive
   OU), `DeploymentManagerAccess` (deployment-managers).
   **First, the name collision this walks into.** Control Tower already created a permission set called
   **`AWSAdministratorAccess`**, and this step creates one called `AdministratorAccess` — two objects, four
   characters apart, both granting administrator, one owned by Control Tower and one by this project. Every
   later sentence of the form "assign the administrator permission set" becomes ambiguous, and the failure
   mode is silent: an assignment made against the wrong one still works, so nothing tells you. Either name
   this project's set distinctly (`InfrastructureAccess` is the honest name — it is the `infrastructure`
   group's set) or record explicitly, here, which of the two every assignment in this plan means. Do not
   reuse or edit the Control Tower set: it is theirs, and a landing-zone update may reset it.
   An earlier draft also created a `DeployApprover`
   permission set; it was
   dropped — the deploy approval gate lives in GitLab (Stage 8), driven by GitLab group membership, and
   consumes no AWS-side permission. Create such a permission set only when something actually consumes it.
   **Note that `DeploymentManagerAccess` is not that set coming back:** the *approval* still consumes no AWS
   permission; this set exists for the other half of the job, which is **diagnosis** — reading why a
   promotion failed before deciding whether to release it.
   **The two approver permission sets are the ones whose *denials* are the point of them, and until
   2026-08-08 only one of them was written that way.**
   **`GovernanceManagerAccess`.** The governance manager approves who may read data, so their own reach must
   stop at the *catalog*, not the
   rows: Glue catalog metadata read, Lake Formation LF-Tag and permission administration, DataZone domain
   ownership, Macie findings read — and **no `s3:GetObject` on lake prefixes and no Athena workgroup**. An
   approver who can already read everything is not exercising a control when they approve a subscription.
   **`DeploymentManagerAccess` (D31), which used to be the AWS-managed `ReadOnlyAccess` and should not have
   been.** The argument above is symmetric and the plan applied it to one approver only. `ReadOnlyAccess` on
   the lifecycle accounts reaches the D19 derived zones — where the output of a query over `restricted` data lives
   and, by D19's own classification rule, *is* `restricted` — and reaches `athena:GetQueryResults`, which
   returns other people's query output. So it is replaced by a set in the same shape as
   `DataScientistProdAccess` (D18): CloudWatch Logs read including Logs Insights (diagnosing a failed
   promotion is the job), SageMaker job/pipeline/Model Registry **status**, Glue catalog metadata, ECR image
   metadata and scan findings, Step Functions and EventBridge Scheduler execution status, and
   `s3:GetObject` on **enumerated** prefixes only — build artifacts and test reports, never a bucket
   wildcard. Denied explicitly rather than by omission: **`athena:*`** (both starting a query and reading
   someone else's results), **`kms:Decrypt`**, `secretsmanager:GetSecretValue`, `ssm:GetParameter*`, the
   Terraform state buckets, and the control plane in full.
   One precision worth carrying, because it is why the old arrangement looked harmless: `ReadOnlyAccess`
   grants no `athena:StartQueryExecution` and no `kms:Decrypt`, so it could never *originate* a read of the
   lake and could not decrypt an SSE-KMS object at all. The exposure was being prevented by encryption
   rather than by design — which stops being true the first time a bucket is created without a CMK.
   **`DataScientistAccess` does not start as `PowerUserAccess`.** An earlier version of this plan gave it
   `PowerUserAccess` "until Stage 6", which contradicts `ORGANIZATION.md` ("no permissions to
   perform infrastructure changes, except for artifacts managed by AWS SageMaker") and, worse, would let
   the data scientist create a public S3 bucket or an internet-facing EC2 instance — i.e. walk around the
   whole design — for five stages. It starts as: SageMaker Studio use, read/write on the account's scratch
   and derived prefixes, Athena, ECR pull, and nothing else. `AmazonSageMakerFullAccess` is *not* a safe
   starting point either: it grants `s3:*` on any bucket with "sagemaker" in the name plus a broad
   `iam:PassRole`. Attach a permissions boundary and scope `PassRole` per the IAM rules in `plan/conventions.md` §6.
   **One set, two targets (D21):** `DataScientistAccess` is assigned on Sandbox *and* Development — the
   two accounts are policy-identical at this level (that is what putting them in one OU asserts), and what
   differs between them is the work, not the permission shape.
   **Forward constraint from D35, and it applies to only half of this assignment.** `Sandbox` is one account
   per business unit; `Development` is singular. So the **Development half stays exactly as written** — one
   shared engineering account, one group — while the **Sandbox half becomes `data-scientists-<bu>`, assigned
   on that unit's Sandbox only**, or every data scientist can enter every unit's experimentation account.
   The approver groups stay single, because approval is an institutional function. **Do not create per-unit
   groups now** — there is one unit. Create the *naming* and write the assignment so that a second unit is an
   addition rather than a refactor; the permission set itself is unchanged and shared. Note what this means
   and does not mean: per-unit isolation ends at the graduation boundary, so isolating one unit's *work* past
   that point is Lake Formation's job, not the account boundary's.
   **`DevEnvStewardAccess`, the third approver set, and it follows the same rule as the other two: its
   *denials* are the point.** The steward approves the `dev-env` image — the runtime every notebook and
   every project app runs on — and the approval itself happens in GitLab, consuming no AWS permission. What
   the set is for is judging the artifact: ECR image metadata and **enhanced-scanning findings**, the build
   pipeline's CloudWatch Logs, and read access to the `aws_sagemaker_image` / `app_image_config` resources
   in Sandbox and Development so they can confirm what is actually registered. Assigned on **Production**
   (the registry, D14) and read-only on **Sandbox and Development**; nothing on Staging, Data Governance,
   Identity, Audit, Log Archive or Policy Canary.
   **Denied explicitly, because these are what would turn the gate into theatre:** `ecr:PutImage`,
   `ecr:BatchDeleteImage`, `sagemaker:CreateImage`, `sagemaker:CreateImageVersion` and
   `sagemaker:UpdateAppImageConfig` — the pipeline holds those and runs only after the approval, so a
   steward who also holds them can ship an image nobody reviewed, including their own. Also denied:
   `athena:*`, `kms:Decrypt`, and `s3:GetObject` on lake or derived prefixes. Approving a *runtime* never
   requires reading data.
   **A second permission set targeting Production (D18)** —
   `DataScientistProdAccess`, and it is a different shape, not a weaker copy: **data plane read, no
   compute, no control plane.** It grants CloudWatch Logs read, Glue catalog metadata read, SageMaker
   job/pipeline/Model Registry *status* read, `s3:GetObject` on named application-output prefixes, and
   Athena on the dedicated workgroup from Stage 9, and nothing else. It denies, explicitly rather than by
   omission: the control plane, `sagemaker:Create*Job`, `sagemaker:CreatePresignedDomainUrl`,
   `glue:StartJobRun` and `lakeformation:GrantPermissions`. GitLab and ECR access (D14) folds into this
   set rather than living as a separate grant. (The ingestion drop-box moved with the lake to Data
   Governance, D22 — it is granted by bucket policy to the Interactive-OU roles, not by this set.)
   **And a third, `DataScientistStagingAccess` (D20)** — read-only, with no write of any kind, not even a
   drop-box. Staging exists to be written by the pipeline and read by a human working out why the pipeline
   failed; a staging environment a person can write to stops being evidence of what the pipeline actually
   does. Same denies as the Production set, minus every write grant.
   Assign them: infrastructure → the Terraform-managed accounts (Sandbox, Development, Data
   Governance, Staging, Production, Identity) **plus `AdministratorAccess` on `Policy Canary` (D29)** —
   which is not a seventh Terraform-managed account but the test principal for step 7, and it has to be an
   administrator or the test measures the wrong thing: an SCP is a ceiling, so a deny that a restricted
   principal could not have exercised anyway proves nothing about the ceiling. **On `Policy Canary` this is
   a confirmation rather than a task (D32):** vending it in 1a step 4 with the infrastructure user's
   `SSOUserEmail` already gave that account an administrator, and a direct assignment is the right shape
   there — the account is deliberately outside the Terraform-managed set and has no `awsds-infra-*` profile
   either. Continuing: data-scientists →
   `DataScientistAccess` on Sandbox and Development, `DataScientistStagingAccess` on Staging,
   `DataScientistProdAccess` on Production, **no assignment of any kind on Data Governance** (D18/D22);
   deployment-managers → `DeploymentManagerAccess` on Sandbox, Development, Staging and Production (the
   approval itself happens in GitLab; this set is for diagnosis, D31), and **nothing on Data Governance** —
   a release approver has no business in the account that grants data access; governance-managers → `GovernanceManagerAccess` on **Data
   Governance only**, which is the mirror image: the one account the deployment manager cannot enter is the
   only one the governance manager can; dev-env-stewards → `DevEnvStewardAccess` on **Production** plus
   read-only on **Sandbox and Development**, and nothing anywhere else — the narrowest of the three,
   because the artifact it judges is a container image and not an environment.
   The data scientist gets no access to Identity, Audit, Log Archive or Policy Canary — the last one
   matters less than it looks, since the account is empty, but an account whose whole purpose is to have
   broken permissions is not somewhere a second persona should be able to sign in and draw conclusions.
   Leave Control Tower's own permission sets untouched — editing them causes landing-zone drift.
   **The direct assignments Account Factory left behind are a separate question from those permission sets,
   and the ordering is the whole of it (D32).** Every vended account carries a *direct* assignment of
   Control Tower's administrator set to the infrastructure user, created in 1a step 4 and sitting outside
   the group model built here. **Remove none of them until the group path is proven end to end** —
   `infrastructure` → `AdministratorAccess` → an actual `aws sts get-caller-identity` under each profile in
   step 5. Removing them first is the cheapest way to lock the only administrator out of an account whose
   sole remaining recovery path is the Management root (D16; D30 reverted). **And verify before promising
   the cleanup at all:** Control Tower may re-create the assignment on a landing-zone update, an account
   update or a re-enrollment, in which case the honest outcome is to record it as a permanent property of
   Account Factory-vended accounts rather than to keep deleting something that keeps returning. Record
   which of the two it turned out to be.
   These are created by hand here only because Terraform cannot run before SSO login works; Stage 2 moves
   them into `terraform-live/identity/` and imports them.
4. **No project persona holds an assignment on the Management account — the infrastructure user included.**
   This step used to create one, and it contradicted the reason `AWS Control Tower Admin` is kept standing at
   all: the Management-account work is *its* job, and what D34 buys is precisely that the infrastructure user
   gains no standing reach there. Principle 1 says the same from the other side — Management is
   bootstrap-only and console-only, Terraform never runs against it, so there is nothing for an
   `awsds-infra-*` profile to do. Step 3's assignment list above already omits it; this step now says so
   deliberately rather than by omission, which is the difference between a decision and an oversight.
   **Keep the mechanical fact the old step carried, because it is true and it bites two steps later:** the
   delegated administrator **cannot manage assignments targeting the Management account** — those can only be
   created from Management itself. That is a constraint on *creating* an assignment, and it is not a
   constraint on group membership: `AWSControlTowerAdmins` already carries `AWSAdministratorAccess` on
   Management, created by the landing zone, and step 1 records that the delegated administrator can edit who
   is in it. So the preventive path into Management is closed and the membership path is not — which is why
   step 8's alarm is the control rather than a nicety. The verification list at the bottom of this stage
   carries the item that confirms the restriction is exactly as described.
5. **Configure the local SSO profiles now, not at the end of the stage.** `aws configure sso` for
   `awsds-infra-sandbox`, `awsds-infra-dev`, `awsds-infra-staging`, `awsds-infra-prod`, `awsds-infra-data`
   and `awsds-infra-identity` — plus one more that is deliberately named differently,
   **`awsds-policy-canary`** (D29). It is not an `awsds-infra-*` profile because `Policy Canary` is not a
   Terraform-managed account and nothing is ever applied into it; the profile exists only to run step 7's
   test battery, and the naming keeps that visible in shell history. **This used to be step 10 and that was
   an ordering bug:** every step below
   this one does CLI or console work *inside a member account* — restricting the Config recorder, enabling
   Object Lock on the Log Archive bucket, raising the Lake Formation cross-account version in Data
   Governance, reading AZ IDs per account — and none of it is reachable without a profile. Doing it here
   also gives the first real proof that steps 1-4 worked.
6. **Check the AZ name-to-ID mapping** across the Sandbox, Development and Production accounts
   (`aws ec2 describe-availability-zones --query 'AvailabilityZones[].[ZoneName,ZoneId]'` under each
   profile). D14 and D21 make this matter for real: both peerings into Production are free within an AZ
   and USD 0.01/GB each way across AZs, so a mismatch has a bill attached. See `plan/open-questions.md` item 3. Cheap to do here,
   and Stage 3 needs the answer before it writes a subnet.
7. **Preventive policies.** Attach to the OUs, in this order. They come in tiers, one per OU policy set
    (D23), on top of an organization-root set that applies everywhere.

    **No `Deny` written below carries a blanket exemption for any principal (D30, reverted).** A standing
    role exempt from every custom deny was proposed and removed; the only carve-outs in this design are
    per-function and per-statement — the catalog-maintenance role against the `Data` OU's Glue deny (D27),
    the `datazone:*` control plane (D26), and a deploy role against a specific deny where automation would
    otherwise stall. **The practical consequence, and it is why the battery at the bottom of this step is
    not optional: a policy attached here has no in-account repair.** A mistake is undone by detaching the
    policy from the Management account, which is exempt from SCPs by design (D16) — so the procedure below
    is the control, and the Management console being already open is a precondition rather than a
    precaution.

    Two writing rules survive the reverted decision, because they apply to any condition in this set:
    **a condition that has to appear in several policies is generated, not typed** (which is why these
    policies live in `terraform-live/identity/` from Stage 2 rather than in the console), and **any ARN
    condition uses an enumerated list, never a wildcard account** — `arn:aws:iam::*:role/x` means "anyone
    who can create a role named `x`, anywhere".
    **A third rule arrives with D34, and it is the one that survives an account being added later.** OUs and
    accounts are created from the console, outside every Terraform state — which cannot cause drift, because
    nothing here declares them, but *can* leave a new OU with no policy attached and a new account outside
    every enumerated condition, with `terraform plan` reporting "No changes" either way. So when these
    policies move into `terraform-live/identity/` at Stage 2: **the floor is discovered and the grants are
    enumerated** — attachments and org-wide sets driven by `for_each` over the Organizations data sources,
    permission set assignments written out one by one.
    - **`Workloads` OU** (D20): deny `sagemaker:CreateDomain`, `sagemaker:CreateUserProfile` and
      `sagemaker:CreatePresignedDomainUrl` — this is what turns D17 from an intention into a control:
      "no Studio outside the Interactive OU" cannot be undone by anyone with a console and a good reason.
      **And deny `datazone:*` outright, which the SageMaker list above does not cover (corrected
      2026-08-08).** Those three actions were the whole control when the interactive surface was the
      classic Studio; since D26 it is a DataZone V2 domain, and D26's "Staging and Production are never
      associated" had no policy line behind it. Three things were reachable and are now not:
      - **A DataZone domain created locally** in Staging or Production.
      - **The account associating itself to a domain and configuring a blueprint**
        (`datazone:PutEnvironmentBlueprintConfiguration`), which mints provisioning and manage-access
        roles with broad permissions in the account — even where the provisioning then fails.
      - **The blueprints that are not the ML one.** Tooling and Lakehouse provision a project bucket, a
        Glue database and an Athena workgroup; none of that passes through `sagemaker:*`, so none of it
        was denied.

      **Why the whole namespace rather than a list of actions.** This plan has already paid for an
      enumerated deny once: the `Data` OU list below omitted `glue:CreateJob` and left the whole ingestion
      runnable in the wrong account until D25 caught it. DataZone gains APIs, and a list written today
      goes stale in the direction of the false negative. Nothing legitimate in this design calls DataZone
      from a deployment target: what crosses the gate is the D28 artifact set, and Production's governed
      write resolves through Lake Formation, not through DataZone. **Revision trigger:** the first time
      Production needs to publish a data product of its own.

      **What is *not* the gate, and it is worth knowing before debugging this.** The account association
      is not held back by anyone declining a RAM invitation: `ram:EnableSharingWithAwsOrganization`
      (step 11, enabled for Lake Formation) makes shares inside the organization arrive without an
      invitation to accept. The gate is the target account being unable to configure a blueprint.

      **To verify while attaching, because the product surface moves:** confirm in the `Policy Canary`
      battery which namespace each Unified Studio action actually evaluates under — some of the portal's
      surface is `datazone:*` and some is `sagemaker:*` — and widen the deny rather than assuming the
      prefix covers it.
    - **`Data` OU** (D22): deny compute creation outright (`ec2:RunInstances`, `sagemaker:Create*`,
      `glue:CreateDevEndpoint`, **`glue:CreateJob` and `glue:StartJobRun`** — added by D25, because the
      original list left a Glue ETL job as a perfectly legal way to run the whole ingestion in the account
      whose entire policy set says nothing runs there — and ECS/Lambda creation), deny `s3:DeleteBucket`
      and `lakeformation:DeregisterResource`. The lake account's SCP is about what can never happen there,
      because nothing is supposed to *run* there at all.
    - **`Interactive` OU** (D21) — **read this before writing anything here, because the phrase the plan
      used to carry did not describe a policy.** "Human infrastructure changes denied" appeared across six
      files as a property of this OU's SCP set, and no SCP implements it. What actually stops the data
      scientist from creating a VPC is `DataScientistAccess` and its permissions boundary — an **identity**
      policy, enumerated by hand, which is exactly the sort of thing an SCP is supposed to back up rather
      than the thing an SCP *is* (Lesson 5). Corrected across those files on 2026-08-09. The honest statement
      of what this OU carries is **nothing of its own**: interactive compute is allowed here because, unlike
      `Workloads` and `Data`, nothing denies it, and the organization-root set is the whole ceiling.

      **Why the literal SCP was not simply written, which is the part to understand before writing one.** A
      deny of "infrastructure changes" in these accounts would have to exempt the identity that *builds* the
      infrastructure in them — Terraform applies the VPC, the buckets, the roles and the keys here under
      `AdministratorAccess`. A standing exemption for the builder from every infrastructure deny is the exact
      shape D30 proposed and had reverted. A second exemption would follow it: D26's blueprints provision
      project buckets, execution roles and apps into these accounts under DataZone's own provisioning roles —
      principals that do not exist until Stage 6 (Lesson 17), and whose absence from a carve-out surfaces as
      a failed project creation rather than as a policy error.

      **So there is a choice to make while attaching, rather than a sentence to inherit.** Either leave this
      OU with no set of its own — and say so in one place instead of implying a control — or give it denies
      that are *interactive-specific and need no exemption at all*. The candidate worth pricing is the
      ungoverned interactive surface: **`sagemaker:CreateNotebookInstance` and
      `sagemaker:CreatePresignedNotebookInstanceUrl`**. Nothing in this design uses a classic notebook
      instance; it bypasses the VPC-only app configuration and the `dev-env` image gate in one step; and
      denying it binds the builder too, which is what would make it a control rather than a carve-out. It is
      named here as a candidate and **deliberately not adopted** — adopting it is a decision, and it belongs
      to whoever runs this step against the `Policy Canary` battery. Record which way it went.

      The differences between Sandbox and Development are differences of content, not of policy, which is
      why they share the OU.
      **If this OU does gain a set, attach it here and not to the nested `Sandboxes` OU** (D23, D35).
      `Sandboxes` groups the accounts that multiply and carries no set of its own; inheritance is what makes
      a unit vended next year governed on arrival, and a set attached twice is a set that will diverge in one
      of the two places. **Until it gains one, that instruction is about the root set** — which reaches a
      newly vended Sandbox whatever the nesting, so "governed on arrival" is true today for a reason that has
      nothing to do with where the attachment goes.
    - **`Identity` OU** (D10, D23 as revised 2026-08-09) — **the tier this plan did not have, because the
      account was supposed to be in `Security`.** It is not: Control Tower refused the vend into a
      foundational OU, so the account sits in a sibling OU created from the console — and **a
      console-created OU carries no policy set until code attaches one** (D34). Two things to do here, in
      this order:
      - **Establish the baseline before writing anything.** List the Control Tower controls enabled on
        `Security` and on `Identity` and diff them; whatever `Security` got by being foundational and
        `Identity` did not is the gap. Enable the equivalent elective controls on `Identity` where they
        exist. Record the diff in `LOG.md` — "it used to inherit that" is not a control (Lesson 5).
      - **Then the hand-written set.** The organization-root SCPs and RCPs already reach this account by
        inheritance from the root, so what belongs *here* is what makes the identity plane's own blast
        radius smaller: deny `organizations:LeaveOrganization` (already at the root), deny deletion or
        disabling of the CloudTrail this account is recorded in, and deny the account creating compute at
        all — there is no workload here, only Terraform managing Identity Center, so `ec2:RunInstances`,
        `sagemaker:Create*` and the rest of the D22 compute list apply to this OU for exactly the same
        reason they apply to `Data`.
      **Do not put the Identity account under the `Data` OU's set to save writing one**, tempting as the
      overlap looks: `Data`'s set denies `s3:DeleteBucket` and `lakeformation:DeregisterResource` and carves
      out `datazone:*` and the catalog-maintenance role, none of which means anything here, and an OU whose
      policy is *mostly* right is the kind of thing nobody re-reads.
    - **Region restriction — use Control Tower's own control, do not write this one by hand** (revised
      2026-08-08). Enable Control Tower's **Region deny** control with **`us-west-2` as the only governed
      region**. Why it is not in the hand-written set below:
      - **Global services resolve to `us-east-1`.** `iam:CreateRole` goes to `iam.amazonaws.com`, which
        answers in `us-east-1`, so `aws:RequestedRegion` is `us-east-1` and a naive deny breaks IAM
        outright. The correct exemption is **`NotAction` on the global service prefixes**, never adding
        `us-east-1` to the allowed regions — the second is what an earlier version of this plan described,
        and it is much looser: it would permit `ec2:RunInstances` in a region with no Config recorder, no
        GuardDuty and no endpoints, which is precisely the blind spot the control exists to remove.
      - **That exemption list has to stay complete as AWS ships services, and AWS maintains theirs.** This
        is Lesson 14 applied to a list rather than to a condition. The plan's own list was already missing
        the ones this project depends on: Billing/Cost Explorer/Budgets (`Stage 1a step 2` creates a
        budget, `Stage 12 step 4` reviews cost), `route53domains:*` (a *separate* prefix from `route53:*`,
        and the one that registers the D15 domain), `acm:*` (a CloudFront certificate must live in
        `us-east-1` — `plan/architecture.md` §4.1 states this and nothing connected it to the region
        policy), `sts:*`, `waf:*`/`wafv2:*` for Stage 13, and **`s3:PutAccountPublicAccessBlock` plus
        `s3:ListAllMyBuckets`**, which are account-level calls evaluated outside the region — that last one
        collides with the account-level Block Public Access bullet further down *in this same step*.
      - **It also needs principal exemptions, not just service ones:** the Control Tower execution role and
        the AWS service-linked roles, or the landing zone's own machinery breaks. The managed control
        carries these; a hand-written one has to remember them.

      **The cost of choosing the managed control, stated rather than discovered:** Region deny is a
      **landing-zone-level setting**, not an elective control attached per OU — so it very likely **cannot
      be exercised against the `Policy Test` OU first**, and applies everywhere the moment it is turned on.
      **Verify this before enabling it**, and if it is indeed landing-zone-wide, note that the D29 battery
      does not apply to this one control: the compensating facts are that it is an AWS-tested control and
      that it is reversible from the Control Tower console. Keep that console open, as with everything else
      in this step.
    - **SCPs (hand-written, in the set that moves to `terraform-live/identity/` at Stage 2):** deny leaving
      the organization — **not hygiene: a real principal can call it.** Control Tower's
      `AWSControlTowerAdmins` group carries `AWSOrganizationsFullAccess` on every member account (D33), and
      `organizations:LeaveOrganization` is one of the few Organizations calls a *member* account can make.
      One call drops every SCP and every Control Tower control for that account. Also deny disabling
      CloudTrail/Config/GuardDuty, and **deny writes to S3 resources
      outside this organization** (`aws:ResourceOrgID`), which is the trusted-resources axis of `plan/architecture.md` §4.2 and
      closes the most direct exfiltration route a notebook has. Two more, cheap and load-bearing:
      **deny `iam:CreateUser` and `iam:CreateAccessKey`** — principle 2 ("no IAM Users") is otherwise a
      convention with no enforcement, and break-glass (D16) is unaffected because the Management account
      is exempt from SCPs — and **deny `s3:PutAccountPublicAccessBlock`**, which protects the
      account-level setting enabled below.
      **And one more, added 2026-08-08: deny `datazone:CreateDomain` at the root, with a carve-out for
      the `Data` OU.** D26 says there is one unified domain and it is registered in Data Governance; until
      now that was a sentence rather than a control, and a second domain anywhere would quietly reintroduce
      the thing the account split exists to prevent — a second interactive entry point with its own
      blueprints and its own project roles. The carve-out is the OU, not a role: `aws:PrincipalOrgPaths`
      (or an `Organizations` path condition) admitting the `Data` OU and nothing else.
      **It must be `CreateDomain` alone and not `datazone:*` at the root** — Sandbox and Development need
      `datazone:PutEnvironmentBlueprintConfiguration` for the blueprints to provision into them at all, so
      a root-wide namespace deny would break Stage 6 rather than protect it. The `Workloads` OU tightens
      to the full namespace on top of this, as above.
      **Read this against INT-12 before attaching it, because the two collide.** INT-12's stated fallback,
      if the domain's account associations do not work, is *one V2 domain per Interactive account* — which
      this deny makes impossible. That is acceptable only because it is now explicit: if Stage 6 has to
      fall back, this policy is amended first (carve the `Interactive` OU in, or drop the root deny to the
      `Workloads` OU only), deliberately and with the reason recorded. A fallback silently forbidden by a
      policy written five stages earlier is the worst version of this.
    - **The two root-user controls Control Tower ships, and the one parameter that decides whether they
      break Stage 1a step 6.** `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS` and `AWS-GR_RESTRICT_ROOT_USER` are
      *strongly recommended* controls — **not enabled by default**, so today the organization has neither.
      The access-key one is free of consequences and matches the invariant D16 already states. The other
      denies `*` wherever `aws:PrincipalArn` matches `arn:*:iam::*:root`, and **that reaches the privileged
      root sessions 1a step 6 depends on**: in a member account an `sts:AssumeRoot` session *is* that
      principal, so the control would deny the very action that restores a root credential or unlocks a
      self-denied S3 bucket policy. Enable it **with the `ExemptAssumeRoot` parameter**, which adds
      `"Null": {"aws:AssumedRoot": "true"}` to the condition and carves the centralized path back out. Both
      controls also take `ExemptedPrincipalArns`; neither exemption should be a wildcard account (the
      writing rule above). Note the asymmetry that makes this safe to enable at all: the controls attach to
      OUs, and **the Management account is exempt from SCPs**, so the break-glass root is untouched either
      way (D16). Enabled from the Control Tower console, so this one is reversible without a detach.
    - **RCPs:** deny access to S3, STS, KMS, SQS and Secrets Manager from principals outside the
      organization (`aws:PrincipalOrgID`) — the trusted-identities axis of `plan/architecture.md` §4.2.
    - **Tag policies:** standardize the mandatory tags from `plan/conventions.md` §6 — with a precision the previous version of
      this plan got wrong: tag policies constrain *tagging operations*, they cannot force a resource to be
      created with tags at all. The forcing function is an SCP with `aws:RequestTag`/`aws:TagKeys`
      conditions on the create actions that matter (EC2, S3, SageMaker). One or the other, or the tags are
      a convention — and conventions do not survive contact with a `terraform apply` at 23:00.
    - **Account-level S3 Block Public Access** in every member account. The module-level block from
      Stage 2 only covers buckets the module creates; the account-level setting is the blanket that also
      covers the bucket someone creates outside it. Protected by the SCP above.
    - **Declarative policies:** enforce IMDSv2 and EC2 public-access defaults org-wide.
    **Every one of these is attached to the `Policy Test` OU first and exercised from `Policy Canary`
    before it goes anywhere real (D29).** An SCP mistake is the fastest way to lock yourself out of your
    own organization — recoverable, because the Management account is exempt from SCPs and the break-glass
    path from 1a step 5 exists, but recoverable is not the same as cheap. **Since D30 was reverted this is
    the only thing standing between a mistake and that recovery**, so the canary is load-bearing rather
    than diligent: there is no principal inside a governed account that can work around a bad deny. The
    procedure, and it is a procedure rather than a gesture:

    - **One policy at a time.** Attach, test, record, then move on. A batch that breaks tells you that
      something in the batch is wrong, which is the least useful form of that information.
    - **Test in both directions, because the two failure modes are opposites.** *Too tight* — run the calls
      that must still **succeed**: an `sts:GetCallerIdentity`, a `s3:ListBuckets`, an `ec2:DescribeVpcs` in
      `us-west-2`, and — for the region restriction — an `iam:ListRoles`, a `budgets:DescribeBudgets` and a
      `ce:GetCostAndUsage`, all of which answer in `us-east-1` and must keep working.
      *Too loose* — run the calls that must now **fail**: a `PutObject` to a bucket outside the
      organization, an `iam:CreateUser`, and **an `ec2:RunInstances` in `us-east-1` specifically**. That
      last one is the discriminating test and it has to name `us-east-1` rather than "a denied region":
      under the correct construction `us-east-1` is *not* an allowed region and the call must fail, while
      under the loose construction this plan used to describe it would succeed and look like a pass. A
      policy that denies nothing fails silently and leaves you believing you have a control (Lessons 5 and
      13 in `CLAUDE.md`), and only this half of the battery catches it.
    - **From an administrator principal**, which is why 1b step 3 assigns `AdministratorAccess` here. An
      SCP is a ceiling; a deny exercised by a principal that lacked the permission anyway proves nothing.
    - **Test each per-function carve-out the same way, in both directions.** The design has no blanket
      exemption (D30, reverted) but it does have named ones — D27's catalog-maintenance role against the
      `Data` OU Glue deny, `datazone:*` as a control plane (D26). For each: confirm the exempt principal
      *can* do the thing, and that a principal outside the carve-out *cannot*. A carve-out that silently
      fails to match is either a control you do not have or a job that will not run, and neither announces
      itself.
    - **With the detach command written down and the Management account already open** before the first
      attach. Verify you can reach it *now*, not in theory — this is the whole recovery path, not a
      backup to one.
    - Then move the attachment to its real target — the OU named in each bullet above, or the organization
      root for the org-wide set. Note that the root-level policies can be exercised here exactly as they
      will behave in production, because `Policy Test` sits under the root and inherits from it like every
      other OU.

    Record each outcome. A policy that passed both halves of the battery is a control; one that was only
    attached is a hope.
8. **Security delegation now; the free detective control now; the metered ones later** (principle 9, as
    amended 2026-08-08). This step used to enable Security Hub, GuardDuty and Access Analyzer here, all at
    once, citing principle 9. That was a misreading of it: the principle argues that **prevention has
    precedence and that the preventive half belongs in the landing zone because it is free** — it says
    nothing in favour of paying for detection over empty accounts. Between this stage and Stage 5 there is
    no governed data to exfiltrate and no workload to attack; what exists is empty accounts, VPCs and state
    buckets, while Stages 2-3 are the heaviest `terraform apply` period the project will ever have.

    **Do here:**
    - **Delegate each security service to the Audit account**, from the **Management account**
      (`enable-organization-admin-account` / `register-delegated-administrator`, one manual console action
      per service — consistent with principle 1). Delegation is free and is an organization-level manual
      act, which is what this stage is for; the later stages that enable the services are Terraform stages
      and should not have to come back to the Management console. **Verify per service whether delegation
      can be made without enabling the service** — some couple the two, and where that is the case the
      delegation moves to the stage that enables it. Record which ones coupled.
    - **IAM Access Analyzer, external-access findings, org-wide from the Audit account.** These are
      **free**, so they follow the preventive rule rather than the detective one — and they catch exactly
      the class of mistake Stages 2 and 3 create: a bucket policy or a role trust policy that grants to a
      principal outside the organization. Unused-access findings are the paid half and stay in Stage 12.
    - **An alarm on membership changes to Control Tower's own groups (D33), which D34 promotes from prudent
      to load-bearing.** Those groups are pre-wired: one membership edit puts a person into
      `AWSAdministratorAccess` on Management, Log Archive and Audit, or `AWSPowerUserAccess` on every account,
      with nothing to review and no approval anywhere. **`AWSControlTowerAdmins` is no longer empty** — it
      permanently holds the vending owner — so this alarm is now the only thing that distinguishes "the
      expected member" from "a second one somebody added".
      **There is no preventive control above this** — the Identity Center administrator is the top of the
      identity plane, and after step 1 that is the delegated administrator in the Identity account, who can
      place themselves in `AWSControlTowerAdmins`. So the control is detective and it has to exist:
      an EventBridge rule on the Identity Center management events that change group membership and account
      assignments, filtered to the Control Tower group names, delivering to the same SNS topic as the
      break-glass alarm. Free, and it is the only thing standing between "nobody is in those groups" and
      "somebody is". **Fire it once**, by adding and removing a member deliberately — an untested alarm is a
      hypothesis (1a step 5 makes the same point about the same topic).

    **Deliberately not here:**
    - **GuardDuty → Stage 4 step 10**, with the WireGuard instance: the first internet-facing resource in
      the project, and the one whose compromise GuardDuty actually detects.
    - **Security Hub → Stage 5 step 13**, with the first governed data — its standards checks report on
      resources, and before Stage 5 there are almost none to report on. Note the compounding this avoids:
      Security Hub's checks are implemented as **AWS Config rules**, so enabling it adds rule evaluations
      on top of the configuration items Control Tower is already recording, precisely during the stages
      that create and destroy the most resources.
    - **Macie → Stage 11**, unchanged.

    **What this costs, honestly.** An institution enables all of it on day one, because the money is noise
    and "we will turn it on later" is how detective controls never get turned on (`plan/institutional-delta.md`
    carries the row). The mitigation here is that each service names the *step* that enables it and carries
    a deliverable there, rather than being deferred to a vague later.
9. **Make the audit trail tamper-evident:** enable **S3 Object Lock** on the Control Tower Log Archive
    bucket and **CloudTrail log file validation**. An audit log that the compromised party can edit is not
    an audit log. Do this before there is anything worth hiding in it.
    **This is the step that limits D33, and it only does so in one of the two modes** — which the earlier
    wording left unsaid, so it was an intention rather than a control (Lesson 5). `AWSControlTowerAdmins`
    is administrator *of the Log Archive account*, so the principal this step defends against holds
    `s3:BypassGovernanceRetention`: in **governance** mode it walks straight through. Use **compliance**
    mode, where a locked object version cannot be deleted or overwritten by anyone, including that
    account's root. **Since D34 that principal is permanent**, so this is not a control covering a
    two-week bootstrap window — it is what keeps the audit trail surviving its own administrator for as
    long as the organization exists. Getting the mode wrong here is therefore a permanent hole, not a
    temporary one. Three practical constraints, all of which bite later if ignored:
    - **Compliance mode is not reversible and not shortenable.** The retention period is a commitment, so
      keep it **short** — long enough that tampering is detectable, not long enough to become an archive.
      This is a detection control, not a retention policy.
    - **Keep the retention shorter than Control Tower's own log lifecycle expiration**, or the landing
      zone's lifecycle deletions start failing against locked objects. Read the bucket's existing lifecycle
      rule first and set the lock inside it.
    - **The bucket already exists**, which used to make this step impossible; since November 2023 Object
      Lock can be enabled in place on an existing bucket, and doing so requires versioning (S3 turns it on).
      Existing objects are not locked retroactively — the default retention applies to objects written
      *after* it, which is fine here and is the reason for "before there is anything worth hiding".
10. **Restrict the AWS Config recorder** to the resource types this project actually uses. Config is the
    main recurring cost of the landing zone (`plan/cost-model.md`), and the default records everything, in
    every governed account — so the cost scales with the account count and with how busy `terraform apply`
    is, which is exactly the shape that surprises people during the build-out stages.
11. **Enable organization-wide resource sharing, so the Lake Formation shares of Stage 5 can exist**
    (D22, INT-11). Three separate settings, **in three different accounts** — which is half of why
    this step is easy to get wrong — and none of which announces its absence:
    - **`ram:EnableSharingWithAwsOrganization`, called from the *Management* account.** It enables trusted
      access for RAM across the organization; it is not a Data Governance setting and cannot be done from
      there. Without it, a Lake Formation grant to another account produces an AWS RAM *invitation* that
      somebody has to accept by hand, and it reappears every time the share is recreated. With it, accounts
      inside the organization receive shares directly.
    - **Lake Formation cross-account version 3 or above**, set **in the Data Governance account**. Versions
      below 3 cannot grant to an Organization or an OU at all, only to an explicit list of account IDs —
      and this project has three consumers at N=1, one more per business unit (D35), with more implied by
      every `plan/institutional-delta.md` row about scale.
    - The **`AWSLakeFormationCrossAccountManager`** managed policy on the grantor (Data Governance), and
      `ram:AcceptResourceShareInvitation` on the data lake administrator role **in each consumer account**,
      which is the fallback path if the two settings above are ever unavailable.

    **How to verify it, because the obvious command does not.** `aws ram get-resource-share-associations`
    requires an `--association-type` and lists the associations of shares that already exist — with no
    share yet created it returns an empty list, which is indistinguishable from the failure it is supposed
    to detect. The check that actually answers the question is
    `aws organizations list-aws-service-access-for-organization` from the Management account, looking for
    `ram.amazonaws.com`; and, for the second setting,
    `aws lakeformation get-data-lake-settings --profile awsds-infra-data`, reading the cross-account
    version back. Confirming a silent-failure mode with a command that is itself silent is how INT-11
    stays open for a month.

    This step is here rather than in Stage 5 because it is organization-level and manual, like everything
    else in this stage. Stage 5 step 7 assumes it and will fail confusingly without it: the grant appears
    to succeed on the producer side and the resource simply never shows up on the consumer side.

**Deliverables of 1b:** SSO login working; `aws sts get-caller-identity --profile awsds-infra-sandbox`
returns the Sandbox account ID; `aws sso-admin list-instances --profile awsds-infra-identity` returns the
Identity Center instance, which is the proof that the delegation took effect; an attempt to write to an S3
bucket outside the organization is denied, which is the proof that the perimeter is real; and
`aws organizations list-aws-service-access-for-organization` (from Management) lists `ram.amazonaws.com`
while `aws lakeformation get-data-lake-settings --profile awsds-infra-data` reports a cross-account
version of 3 or above — together, the proof that Stage 5's shares have somewhere to land. Note what this
deliverable used to say: `aws ram get-resource-share-associations` from the Data Governance profile, which
returns an empty list both when sharing is enabled and when it is not.

**Blocking questions for the user:** the domain name to register (D15). Not needed to start the stage, but
needed before Stage 7.

**Risks:** Control Tower landing zone deployment takes ~60 minutes and is awkward to undo. Account e-mails
cannot be reused after an account is closed (a closed account holds its e-mail for 90 days) — which is
exactly why D11 keeps accounts in the persistent layer. Everything created in this stage is persistent;
nothing here is torn down between sessions.

**To verify while executing this stage**, because Control Tower's handling of Identity Center has changed
more than once and the plan should not assume: (i) that the delegation coexists with the landing zone
without raising drift; (ii) that the restriction in 1b step 4 is exactly as described — that assignments
targeting the Management account are the *only* thing the delegated administrator cannot manage; and
(iii) that the RCPs and SCPs in **1b step 7** do not conflict with the SCPs Control Tower manages itself,
which is the usual source of "the guardrail I wrote silently does nothing"; (iv) that enabling S3 Object
Lock on the Control Tower-managed Log Archive bucket (**1b step 9**) does not raise landing-zone drift; and
(v) that the Lake Formation cross-account version can be raised to 3+ in an account that has no lake in it
yet (**1b step 11**) — if it cannot, that setting moves into Stage 5 and the rest of the step stays here;
and (vi) whether removing the direct administrator assignment Account Factory created on each vended
account (**1b step 3**, D32) sticks, or is re-created by a landing-zone update, an account update or a
re-enrollment — the answer decides whether that assignment is cleanup or a permanent property, and D32 is
amended either way.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
