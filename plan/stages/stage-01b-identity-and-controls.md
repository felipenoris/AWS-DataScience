# Stage 1b — Identity, policies, detective controls, org-wide enablement

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stage 1a complete |
| **Consumes** | [D10](../decisions/D10-identity-center-delegation.md), [D11](../decisions/D11-lab-lifecycle.md), [D12](../decisions/D12-budget-ceiling.md), [D14](../decisions/D14-supply-chain-account.md), [D15](../decisions/D15-tls-internal.md), [D16](../decisions/D16-break-glass.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D18](../decisions/D18-data-scientist-access.md), [D19](../decisions/D19-derived-zone.md), [D20](../decisions/D20-staging-account.md), [D21](../decisions/D21-development-account.md), [D22](../decisions/D22-data-governance-account.md), [D23](../decisions/D23-ou-structure.md), [D25](../decisions/D25-drop-box-consumer.md), [D29](../decisions/D29-policy-canary.md), [D31](../decisions/D31-approver-read.md) |
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
2. In IAM Identity Center, create the users from `ACCOUNTS_AND_USERS.md` (e-mails in `secrets/emails.md`)
   and the groups `infrastructure`, `data-scientists`, **`deployment-managers`**, **`governance-managers`**
   and **`dev-env-stewards`**. Enforce MFA.
   **Prerequisite to check first: `secrets/emails.md` must carry an address for every user created here.**
   As of 2026-08-08 it does not have one for the **Dev Env Steward**, which was added to the design after
   the file was last filled in. An Identity Center user cannot be created without one.
   The approver groups were a single `managers` group until 2026-08-08 and have been split twice since,
   each time along a different axis — release (lifecycle), data access (ownership), runtime image (supply
   chain). The reason is cumulative and it is the whole point: one persona holding all of them means a
   single human can write a job that reads restricted data, approve its release, approve its access to that
   data, **and** approve the runtime image the job was written on — four acts, one signature.
   **Never put the same person in more than one of these groups**, or in one of them plus
   `data-scientists`, even while there is only one human: the moment that happens the split is notation
   again, and nothing in AWS will warn you.
3. Create permission sets: `AdministratorAccess` (infrastructure), `DataScientistAccess` (the Interactive
   OU), `DeploymentManagerAccess` (deployment-managers). An earlier draft also created a `DeployApprover`
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
   `PowerUserAccess` "until Stage 6", which contradicts `ACCOUNTS_AND_USERS.md` ("no permissions to
   perform infrastructure changes, except for artifacts managed by AWS SageMaker") and, worse, would let
   the data scientist create a public S3 bucket or an internet-facing EC2 instance — i.e. walk around the
   whole design — for five stages. It starts as: SageMaker Studio use, read/write on the account's scratch
   and derived prefixes, Athena, ECR pull, and nothing else. `AmazonSageMakerFullAccess` is *not* a safe
   starting point either: it grants `s3:*` on any bucket with "sagemaker" in the name plus a broad
   `iam:PassRole`. Attach a permissions boundary and scope `PassRole` per the IAM rules in `plan/conventions.md` §6.
   **One set, two targets (D21):** `DataScientistAccess` is assigned on Sandbox *and* Development — the
   two accounts are policy-identical at this level (that is what putting them in one OU asserts), and what
   differs between them is the work, not the permission shape.
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
   principal could not have exercised anyway proves nothing about the ceiling; data-scientists →
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
   These are created by hand here only because Terraform cannot run before SSO login works; Stage 2 moves
   them into `terraform-live/identity/` and imports them.
4. The infrastructure user's assignment **on the Management account itself** has to be created from the
   Management account — the delegated administrator cannot manage assignments targeting Management.
   This is the one identity task that stays there permanently.
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
    - **`Interactive` OU** (D21): no extra SageMaker denies — Studio is the point — but the same
      no-infrastructure guardrails as everywhere else. The differences between Sandbox and Development
      are differences of content, not of policy, which is why they share the OU.
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
      the organization, deny disabling CloudTrail/Config/GuardDuty, and **deny writes to S3 resources
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
      and this project has three consumers with more implied by every `plan/institutional-delta.md` row about scale.
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
yet (**1b step 11**) — if it cannot, that setting moves into Stage 5 and the rest of the step stays here.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
