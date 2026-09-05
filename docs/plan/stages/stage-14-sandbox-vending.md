# Stage 14 — Per-business-unit Sandbox vending

| | |
|---|---|
| **Status** | not started — **BLOCKED ON THE ACCOUNT QUOTA (2026-09-05)** and re-scoped by it. Step 2 (request the account) and step 7 (prove it with a **second** unit) cannot run, so nothing here can be marked done; the rest may be authored, against this stage's own rule that automating what has never been built is speculation. **Its central question is answered elsewhere and without N**: where the VPN terminates is settled as a *designated hub* — `VPC-Networking` in Production ([D38](../decisions/D38-single-egress-hub.md)) — which is one of the three shapes this stage listed, taken early and deliberately (Lesson 34's shape, said out loud). What remains here when a slot frees: the `sandbox-unit` module, the CIDR draw from `10.16.0.0/13`, the peering pair to `VPC-Networking` and `VPC-SharedServices`, and one more zone in the `awsds.internal` family. Per-business-unit isolation inside the single Sandbox — SMUS projects plus Stage 16's per-group prefixes — is the interim. — *earlier:* not started — the first stage that is about *scale* rather than about a new capability |
| **Prerequisites** | Stages 2, 3, 4, **5** and 6 — Stage 5 for the consumer side the module composes (`terraform-modules/consumer-data/` — v0.2.0 today, pinned at whatever tag is current at the vend — the per-account `DataLakeSettings` and the share map step 5 extends). Everything a business unit's Sandbox must arrive holding has to exist and have been applied by hand at least once |
| **Consumes** | [D21](../decisions/D21-development-account.md), [D23](../decisions/D23-ou-structure.md), [D26](../decisions/D26-unified-studio.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md), [D37](../decisions/D37-nested-ou-inheritance.md) |
| **Proves** | that a business unit's `Sandbox` can be created, made usable and closed without a hand-written slice |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** adding a business unit is a merge request. One input — the unit's name — produces its
`Sandbox` account, in the **`Sandboxes` OU** (nested under `Interactive`, D23), with networking, identity
and its domain association, and nothing about it is typed twice. The OU is what makes the account
governed on arrival: the `Interactive` policy set inherits down into it, so `ManagedOrganizationalUnit` in
step 2 points at `Sandboxes` and the account needs no policy attachment of its own.

> **And neither does the OU — that is [D37](../decisions/D37-nested-ou-inheritance.md), settled 2026-08-13
> and measured in Stage 1c 7.6/7.7.**
> **Nothing is attached or enabled on `Sandboxes` — no SCP, no RCP, no tag policy, no Control Tower
> control — unless it is a configuration that *differs* from `Interactive`'s.** The OU is a registered
> target and would accept one; it is declined so that sameness is expressed by inheriting rather than by
> copying, because a duplicated statement is a second place to forget an amendment (Lesson 14). So this
> stage's `for_each` must not grow a per-OU policy attachment for the sandbox branch, and the one thing to
> carry: **`Sandboxes` reads as zero enabled controls in Control Tower while its accounts are fully
> governed** — an enabled control is per OU and is not inherited as an enablement, only the statements it
> emits are. Read `Interactive` when asking what applies to a Sandbox account.

**Scope, which is narrower than it first looks (D35).** Only `Sandbox` multiplies. `Development`, `Staging`
and `Production` are structural and singular, so **the promotion chain is untouched by this stage** — one set
of pipelines, one deploy role pair, one approval gate, however many units exist. The multiplication is
entirely upstream of the graduation boundary, which is the cheapest place for it to be, and it is why this
stage can be built without reopening Stages 8 to 10.

**Why this is a late stage and not an early one.** Automating a thing that has been built once by hand is
engineering; automating a thing that has never been built is speculation. Every slice this stage
parameterises — `foundation/`, `egress/`, the identity assignment, the domain association — exists and
has been applied by Stages 3 to 6. **What this stage adds is not new infrastructure, it is the substitution
of a name for a hardcoded account.**

**The central open question, deliberately unsettled until here (D35): where the VPN terminates.** Stage 4
lands the tunnel in *the* Sandbox account, points the client resolver at that VPC and carries one
Sandbox↔Production peering to reach GitLab — and the VPN lives on the multiplied side, so all of it is
per-unit. Three shapes are live, and the choice depends on N and on whether units may reach one another at
all:

- **A designated hub** — one account keeps the VPN and every unit VPC peers to it. Cheapest to build, and it
  makes one Sandbox structural, which is a wart worth naming rather than discovering.
- **A shared network account with Transit Gateway** — the institutional answer
  (`docs/plan/institutional-delta.md`), a new structural account, and a real hourly cost per attachment. Peering
  here is O(n) rather than O(n²), so TGW starts paying at the point where the route tables stop fitting in
  one head, not at the point where the arithmetic says so.
- **Per-unit VPN endpoints** — each unit's Sandbox terminates its own tunnel. The strongest isolation, no
  shared network path at all, and the largest per-unit cost.

**Decide it here with N in hand, not now.** What Stage 4 owes this stage is only that it names the VPN home
as a *role an account plays* rather than as "the Sandbox account", so the topology is a substitution rather
than a rewrite.

**To execute:**

1. **`terraform-modules/sandbox-unit/`** — one module, one input (the unit name), composing what already
   exists: a `foundation/` VPC from the Stage 3 module with its CIDR taken from the allocation table, the
   `egress/` slice, and the Route 53 associations that let the unit
   reach GitLab by name. **Two PKI items, not one, and the second is the easy one to miss (D36):** the zone
   associations *and* the **internal CA root reaching this unit's `dev-env` image** (INT-19). The first
   fails as `NXDOMAIN`, the second as a TLS handshake error inside a notebook — neither says "a business
   unit was vended without it". Both belong in this module, or they are Lesson 14 in a new place.
   **Composition, not new resources** — if this module needs a resource type that
   Stage 3 or Stage 5 did not already build, that is a signal the earlier stage was written for a singleton
   and should be fixed there instead.
2. **The account request itself, and the rung to use (D34).** The account is still created by **Account
   Factory**, because an account created any other way is not enrolled in Control Tower and is ungoverned
   while looking correct. What changes is who fills in the form:
   `aws_servicecatalog_provisioned_product` against the Account Factory product, with `AccountEmail`,
   `AccountName`, `ManagedOrganizationalUnit` and the SSO fields as provisioning parameters — the middle rung
   of D34's ladder, which buys a diff and a review without AFT's dedicated management account and pipelines.
   Three things it needs, and they are why this is a stage and not a footnote:
   - **A principal with Service Catalog rights in the Management account.** This reopens D34's ownership
     question and must be answered explicitly: a pipeline role, not a standing human administrator, is the
     whole point of moving off the console.
   - **`prevent_destroy` on the provisioned product**, in its own slice. Terminating this resource **closes
     an account**; a `terraform destroy` reaching it by accident is a class of error that must not be
     possible.
   - **The e-mail address**, per unit, immutable, and held for ~90 days after closure. It follows the
     `+alias` convention and is registered in `secrets/emails.md` before the apply, never generated.
   *To verify before writing it:* the product name and the exact parameter keys, which are the kind of detail
   that changes between landing-zone versions.
3. **Identity per unit (D35).** A `sso-group-data-scientists-<bu>` group, assigned `DataScientistAccess` on that unit's
   Sandbox and nothing else. The Development assignment stays as it is — one shared engineering account, one
   group — and the approver groups stay institutional and single. Generated from the same unit name as
   everything else: a group whose membership is right and whose *assignment* was typed by hand is the failure
   mode here.
   **The group and the assignment are on opposite sides of the identity seam, and the module has to respect
   it** (`docs/plan/conventions.md`): the **assignment** is Terraform, driven by the same human-authored unit map
   as everything else in this stage — which is still "enumerated" under D34, because a unit gets its grant by
   being written down. The **group** and its members are directory objects; here the module may create the
   group as a convenience, but the day the directory comes from an IdP the group arrives over SCIM and this
   module must keep working with only the assignment. Write it so removing the group resource is a deletion,
   not a redesign.
   **This is also the step where the per-unit tokens are first exercised for real**: `<env>` and the tag
   policy's allowed values must both admit the unit's token, or the first apply in the new account is an
   `AccessDenied` (`docs/plan/conventions.md`, the D35 note; Stage 1c step 7.8).

3b. **The account-level baseline that no policy applies retroactively.** This step owes the new account
   **account-level S3 Block Public Access**, and the order is not negotiable: the account inherits the
   organization-root SCP the moment it lands in a governed OU, and there is no cross-account API for the
   setting. **Decision 7 (settled 2026-08-13) is what makes this step possible at all**: the root deny on
   `s3:PutAccountPublicAccessBlock` carves out the `InfrastructureAccess` Identity Center role, so the call
   succeeds from the unit's own `awsds-infra-sandbox-<n>` profile and from nothing else. Run it, verify it
   with `aws s3control get-public-access-block`, and **record it in the vend log** — the carve-out makes the
   baseline recoverable, not automatic, and a unit that silently differs from the others is exactly what
   this stage exists to prevent.
4. **Domain association (D26, INT-12) — the one act in this stage that no merge request can perform, and
   it is six parts in a fixed order.** Nothing creates a domain — the root deny on `datazone:CreateDomain`
   stands (exercised in both directions on 2026-08-21, so it is now known to fire rather than merely
   attached), and this stage is where the pressure to break it will first be felt. **INT-12 owns the
   mechanics** — console-only, a RAM share the domain initiates — and they are not restated here.
   **The *"7-day invitation window"* this sentence used to add was retired on 2026-08-21 by running the
   act once: the share is organization-scoped and AUTO-ACCEPTS, so there is no invitation and no clock.** What this step owes is the sentence INT-12 cannot carry: **a stage whose whole
   promise is "one input and one merge request" contains a console act, and the parts either side of it
   are two different applies of the same slice.**

   1. **The unit's `sagemaker/` pass-1 apply** — the blueprint prerequisites: the provisioning and
      manage-access roles (**both trusts pinned to the DOMAIN account** — `domain_account_id` is a
      required module input since v0.3.3; the member-pinned trust was the measured defect that made the
      roles unassumable), the D13 boundary, the project CMK (carrying the documented SMUS key-policy
      statement set), the `awsds-<env>-smus-projects` bucket, the VPC/subnet/AZ parameters, with
      `blueprints_enabled` **false**. (Step 1's composition list does not mention a `sagemaker/` slice; it
      is the unit's, and it precedes this act.)
   2. **Request the association** in the **AWS management console** (`console.aws.amazon.com/datazone`)
      of the DOMAIN account — *View domains* → the domain → *Account associations* → *Request
      association*. **There is nothing to accept in the new account** (measured 2026-08-21): the share
      auto-accepts and the unit is associated when you look. Record every field the console asks for
      (Lesson 16) — the two toggles it offers are `AWS Organization-only RAM share` and `IAM users can
      access APIs only`, and the second is the no-portal choice this design requires.

      > **BOTH HALVES OF THE SENTENCE THIS REPLACES WERE WRONG, AND THE FIRST HALF WAS ALREADY KNOWN.**
      > It said *"from the domain's **admin portal**"* — the `dzd-*.sagemaker.<region>.on.aws` surface,
      > which is not where this lives; Stage 6 step 1.3 was corrected on that exact point on 2026-08-21,
      > **before** it was executed, and this copy never heard. **Lesson 35**: the correction landed at one
      > end and the stale path stayed alive at the other, where nothing reads it until someone follows it.
      > The second half — *"accept it in the new account's console"* — was retired by the measurement.
   3. **The `backend.SMUS_ASSOCIATED` row** — the *measurement* table. **Add it only after the
      association is confirmed BY A CALL, never by a console label**: `aws datazone
      list-environment-blueprint-configurations --domain-identifier <dzd-…>` run as the new unit's own
      profile must **succeed** (returning an empty list). Before the association it cannot succeed at
      all, which is what makes the empty answer evidence. **And the row is a TRIGGER, not a note**: it
      arms this step's part 4 *and*, once every member carries one, the project profiles in part 5.
   4. **The unit's `sagemaker/` pass-2 apply** — the blueprint configurations **with the complete
      wizard-field set** (manage-access role on every one; Tooling's `S3Location` + `KmsKeyArn`) **and the
      11 per-configuration `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grants** — all carried by
      `sagemaker-prereqs` at **v0.3.3 or later**, applied **from the member account**, because
      `PutEnvironmentBlueprintConfiguration` takes no account parameter and configures the caller's
      (`terraform-modules/sagemaker-prereqs/blueprints.tf` carries the reasoning). **The measured rule
      (2026-08-22, five attempts): a configuration missing a wizard field pins its projects in BOTH
      directions — deploy and delete both validate it — and a configuration with no grant refuses every
      create one layer past `CreateProject`.** The enabled
      set is [`docs/SMUS.md`](../../SMUS.md)'s category-1 table — **never "the ML blueprint", which does
      not exist**.
   5. **Three by-hand edits in `data-governance/governance/`, and an alias alone is not enough.** The
      `backend.SMUS_MEMBERS` row, a new aliased provider in `providers.tf` (Terraform cannot `for_each` a
      provider) **and** new entries in `locals.tf`: `member_account_ids` and `project_profiles` are static
      literals, and `experimentation` is pinned to `sandbox`, so unit 2 is reachable by no profile until
      both maps grow. **Record the choice this raises rather than performing it by rote:** three hand edits
      per unit against AWS's own account-agnostic mechanism, `datazone create-account-pool` (CLI-only) —
      the note Stage 6's forward-constraint paragraph deliberately did not adopt at N=1.
   6. **The `governance/` apply — and read the plan before running it.** `profiles_enabled` feeds a
      `for_each`, so it **reverses**: a `SMUS_MEMBERS` row added while `SMUS_ASSOCIATED` lacks the same
      account takes the flag false and the next apply **destroys the project profiles that already exist**.
      That is why part 3 precedes part 5. The tell is a plan showing `awscc_datazone_project_profile`
      destroyed; the destroy count is what
      [`terraform-changes.md`](../runbooks/terraform-changes.md) Recipe A step 5 exists to make you read.
5. **Data access is *not* granted here.** A new unit arrives with no Lake Formation permissions. Whether units
   share data or are isolated by LF-Tags is the governance manager's decision (D35), routed through the
   subscription workflow like any other access — a vending flow that also grants data access is a flow that
   grants data access by default.

   **But the *plumbing* is the module's, and the distinction matters because the failure looks identical
   from the outside (written down 2026-08-19, from Stage 5 pass 3).** Five mechanical facts the
   `sandbox-unit` module carries, none of which is an entitlement:
   - **the unit's account needs a `DataLakeSettings` of its own** — a data lake administrator, or a share
     granted to it stays invisible in its catalog no matter how correct the grant is. An account with no
     admin and an empty catalog is *indistinguishable* from a vend that failed, which is why `DL-7` reads
     RAM and the admin count separately;
   - **that resource replaces `admins`, `parameters` and both `Create*DefaultPermissions` blocks
     wholesale** (INT-11), and the defaults act at **creation time** and cannot be expressed empty in a
     plan — so the new account's settings apply **before** its first catalog object, in two steps
     (Lesson 27, Recipe D). A vending flow is exactly where a two-step apply gets collapsed into one;
   - **the share to the new unit is an `N+2` edit in `data-governance/data/`** (INT-03), carrying the
     grant option like every cross-account grant and the `layer` gate like every TBAC expression here
     (Lesson 29). It is a `for_each` over the consumer map, not a copied resource — which is the whole
     reason Stage 5 was told to write every list as a map from day one;
   - **and the unit's own consumer slice is already a module — `terraform-modules/consumer-data/`,
     applied 2026-08-19** (Stage 5 pass 4; v0.2.0 since the same-day revision). `sandbox-unit` composes a
     *call* to it with one changed input,
     not a copy of it: the settings, the `alias/awsds-<env>-data` CMK (**no derived zone or workgroup since `consumer-data-v0.6.0`, 2026-08-26** — D19 revised),
     the resource links and the local re-grants all come with it. **The re-grant is a pair** — `DESCRIBE`
     on each resource link *and* the permission on the target — and a vend that lands only the second half
     produces a unit whose scientists see no database at all;
   - **and two machinery edits, neither of them a policy edit.** The unit joins `DATA_CONSUMERS` in
     `scripts/tfhygiene/backend.py` — which emits the `lake` map to its own `data/` slice. **The second
     emission this sentence used to name is GONE (2026-08-26, D19 revised)**: `data_consumers` to
     `identity/sso/` left with the persona's Athena/derived statements, so a new unit no longer re-plans
     `identity/sso/` at all — one fewer coupling than this step was written against. If a future set
     ever enumerates per-consumer resources again, the 4c rule returns with it: enumeration from state,
     never a wildcard.
6. **The teardown half, which is what makes a unit disposable.** `make down ENV=<bu>` must work against a
   generated Sandbox exactly as it does against the hand-built one, and closing a unit must be a documented
   procedure with the ~90-day slot and e-mail retention stated up front (D34's headroom item).
7. **Prove it with the second unit, not the first.** The first unit through this module is the one that was
   built by hand and is being adopted; the proof is a *second* one, created from nothing but a name, whose
   `terraform plan` on every shared slice comes back empty afterwards.

**Deliverables:** a business unit's Sandbox account, its VPC, its identity assignment and its
domain association all produced from one name in a merge request; a second unit created without editing any
module; the VPN topology decision recorded together with the number of units it was made for; and the quota
headroom restated in units rather than in accounts — **one slot per business unit**.

**Cost:** measured into [`docs/PRICING.md`](../../PRICING.md) per unit before the first vended one, not after
(Lesson 6). The dominant term is not the account — it is **one set of interface VPC endpoints per unit**,
which is what decides whether centralized endpoints shared by RAM stop being optional (D35).

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
