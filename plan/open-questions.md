# Open questions

Only things to find out by doing. **All thirty-one decisions are closed** — a question that
turns into a choice becomes a decision file, not a longer entry here.

---

## 9. Open questions

Everything that was open before execution started is now closed in `plan/decisions/` (D1-D31). What follows is
what is genuinely still unanswered:

1. **Which domain name to register (D15).** The one input needed from the user. Not blocking Stage 1, but
   blocking Stage 7, and worth doing early since registration and validation take time.
2. **D7/D28 - two verifications, not decisions.** The orchestration decision is closed (both built,
   Stage 10; alternative A is MWAA Serverless via `awscc_mwaaserverless_workflow`, verified to exist
   2026-08-08). What is open: (i) whether the awscc resource *applies* cleanly under the CI deploy role
   (INT-14 — fallback chain recorded there); (ii) whether logs-only observability — Serverless has
   no Airflow UI — is livable for a data scientist debugging a failed run, which only the Stage 10
   comparison can answer. Keep application entry points as plain containers so both implementations, and
   the two options that were not built, remain viable.
3. **AZ name-to-ID mapping across accounts.** AWS maps AZ names to physical datacenters independently per
   account, so `data.aws_availability_zones` indexed by position can place "the same" AZ in different
   datacenters in Sandbox, Development and Production — which turns peering traffic that looks intra-AZ
   into cross-AZ traffic at USD 0.01/GB each way. **D14 and D21 made this concrete rather than
   theoretical:** the VPN, SageMaker and GitLab talk across the two peerings constantly. Check it in
   Stage 1b step 6
   (`aws ec2 describe-availability-zones --query 'AvailabilityZones[].[ZoneName,ZoneId]'` under each
   profile). If the mappings differ, Stage 3 anchors subnets on `zone_ids` (`usw2-az1`, passed per
   environment in `.tfvars`) instead of on list position, and `plan/architecture.md` §4.1 is updated accordingly.
4. **Layer assignments.** `[P]`/`[D]`/`[E]` are cost judgements based on estimates. Revisit them at Stage 12
   against the real bill — especially the interface endpoints (the largest hourly item, now ~9 of them)
   and GitLab (the largest idle item).
5. **CodeArtifact ecosystem coverage (`plan/architecture.md` §4.3).** The CodeArtifact documentation lists Cargo among its
   supported formats, so the Rust question is down to confirming it in practice at Stage 6. Julia and R remain genuinely uncovered and keep their `plan/architecture.md` §4.3 fallbacks — they
   are what decides whether egress design B is livable.
6. **Whether SageMaker Studio can block file download** (Stage 6 — the question carries over unchanged to
   the ML-blueprint apps under D26). If not, Stage 11's threat model has to
   record an accepted risk rather than a control.
7. **The sixteen cross-account integrations in `plan/integrations.md`.** Each has a stated fallback, so none of them blocks
   a stage, but none of them is known to work either. They are listed there rather than repeated here.
   **INT-15 and 16, added 2026-08-08 by the pre-Stage-1 review, are not integration risks but
   control risks** — whether D13's constraint on execution roles survives blueprint-authored roles (INT-15),
   and whether the VPN restriction reaches the Unified Studio portal at all (INT-16). Each can invalidate an
   objective stated in `CLAUDE.md`, so they are answered at Stages 6 and 4 respectively and their outcome is
   written down either way.
   INT-11 (organization-wide RAM sharing and the Lake Formation cross-account version) is the one to
   settle earliest, because it is enabled in Stage 1b and consumed in Stage 5 — and since D26 it also
   carries the domain's account associations (INT-12) — and its failure mode is silence rather than an
   error. INT-13 (CodeConnections from the unified domain to the self-hosted GitLab in a private subnet)
   is the one with no convenience-preserving fallback: check it while building Stage 7, when GitLab first
   exists.
8. **How much of the S3 console survives the `aws:SourceVpce` condition** (INT-06, Stage 9). This
   decides whether D18's "read named S3 prefixes in Production" is usable through the console at all, or
   whether it is a CLI-over-the-tunnel operation that `README.md` has to say so about. Cheap to answer,
   annoying to discover by symptom.
9. **Whether sampled or synthetic Staging data makes the integration tests meaningful** (D20, Stage 9).
   The decision that Staging never holds a copy of production data is firm — the reasoning is in D20 and
   it is a security argument, not a cost one. What is open is the consequence: a test suite running
   against a sample catches permission, schema and wiring errors and misses everything that only appears
   at production distribution and volume. Answer it by recording, for each production incident this
   environment ever has, whether a Staging run could have caught it. Until there is such a record, this
   is a belief rather than a finding.

### Blocking Stage 1 — the choices the user has to make, added 2026-08-08 by the pre-Stage-1 review

Items 1-9 above are things to *find out*. These are things to *decide*, they have no defensible
default, and each one is referenced from the step that needs it.

10. ~~**What "apply these to a test OU first" means, since there is no test OU**~~ — **closed 2026-08-08 as
    D29:** a tenth account, `Policy Canary`, alone in a fifth OU, `Policy Test`. The reasoning that closed
    it is worth keeping in one line, because the obvious answer was the wrong one: an *empty* policy
    staging OU tests nothing, since an SCP is only evaluated when a principal makes a call, so the OU is
    worth having only because there is a disposable account inside it. Stage 1b step 7 now carries the
    procedure — one policy at a time, exercised from an administrator principal, in both directions
    (what must still succeed *and* what must now fail), with the detach command ready. Two verifications
    ride along with it and are answered while executing: whether the **IAM Policy Simulator** evaluates
    SCPs for member-account principals — if it does, it is a cheaper first pass than any OU — and whether
    the OU has to be **registered with Control Tower** for the test to run against the real control
    baseline, which D29 assumes and Stage 1a step 4 instructs.
11. ~~**What the break-glass credential actually is**~~ — **closed 2026-08-08: the Management account root,
    and nothing else** (D16). It removes the exception from principle 2 rather than documenting one, since
    the root is not an IAM user; it merges Stage 1a steps 1 and 5, which were describing the same credential;
    and it composes with centralized root access management, which strips root from the member accounts and
    leaves exactly one. The cost, recorded rather than hidden: the root cannot be scoped, so every
    compensating control is detective — MFA, offline password, no access keys (with
    `iam-root-access-key-check` as the instrument, since SCPs cannot reach Management), and an alarm whose
    SNS destination is deliberately *not* the mailbox that is the login.
    **The MFA type is deliberately left unspecified**, which is a decision and not an omission: nothing in
    this plan depends on it, and the user already has MFA on this root. What survives is not about the type
    — with a single registered device, recovery runs through AWS support and depends on the account's phone
    number and payment method, so those are part of the design.
    **And the second half of this item went the other way (D30):** the SCP recovery principal — a role
    exempt from every custom deny — was recommended against and **adopted by the user's decision**. It is
    built, with an enumerated ARN list rather than a wildcard, a companion deny on creating the role, a
    scoped identity policy, MFA-gated trust, an assume alarm, and a CI check that no `Deny` ships without
    the carve-out. It also forced a hole closed that predated it: the SCPs now live in code
    (`terraform-live/identity/`), because a condition repeated by hand across four documents is a condition
    that will be missing from one.
12. ~~**Whether the deployment manager keeps blanket `ReadOnlyAccess` on four accounts**~~ — **closed
    2026-08-08 as D31: it does not.** Two changes, and the more durable one is the second. `ReadOnlyAccess`
    is replaced by a bespoke **`DeploymentManagerAccess`** in the shape D18 already uses — diagnosis, not
    reading: logs, job and pipeline status, catalog metadata, scan findings, enumerated artifact prefixes;
    `athena:*` and `kms:Decrypt` denied explicitly. And the **derived zone gets its own KMS CMK** in each
    Interactive account, whose key policy is where "who may read materialised `restricted` data" is
    expressed — default-deny, so a derived prefix nobody enumerated is still covered. That second half
    closes a gap in D19 that had nothing to do with this persona: five practices for the derived zone, none
    of them about the key. Cost: two more CMKs, ~USD 2/month.
    **One precision worth keeping, because it is why the old arrangement looked fine:** `ReadOnlyAccess`
    grants neither `athena:StartQueryExecution` nor `kms:Decrypt`, so it could not originate a read of the
    lake and could not decrypt an SSE-KMS object. The exposure was real but was being prevented by
    *encryption* rather than by *design* — a property that evaporates the first time a bucket is created
    without a CMK, which is exactly the kind of accident this plan should not depend on.

**Every item in this section that was a *decision* is now closed. Items 1-9 remain, and they are all
things to find out by doing.** Stage 1a has no outstanding prerequisite.

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [plan/stages/INDEX.md](stages/INDEX.md)*
