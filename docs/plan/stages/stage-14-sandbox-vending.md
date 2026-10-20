# Stage 14 — Per-business-unit Sandbox vending

| | |
|---|---|
| **Status** | **blocked on the account quota** (2026-09-05) and scoped by it, with its pre-vend half done: `./aws/vending.py` read the hand-built unit on 2026-10-18 as nine passes and one note, and [`docs/PRICING.md`](../../PRICING.md) §3 prices a unit at 3.50 USD/month at rest and 0.180/h working. Step 2 (request the account) and step 7 (prove it with a **second** unit) cannot run, so the stage cannot close; the rest may be authored, against this stage's own rule that automating what has never been built is speculation. Steps 2 and 6 hold the vendor's readings of 2026-10-20: terminating the provisioned product unenrolls the account without closing it, and the address an account holds at its closure can never be another account's primary address; the product's own reading in Management and D34's rung are the user's. **Its central question is answered elsewhere and without N**: where the VPN terminates is settled as a *designated hub* — `VPC-Networking` in Production ([D38](../decisions/D38-single-egress-hub.md)) — one of the three shapes this stage listed (Lesson 34). What remains here when a slot frees: the `sandbox-unit` module, the CIDR draw from `10.16.0.0/13`, the peering pair to `VPC-Networking` and `VPC-SharedServices`, and one more zone in the `awsds.internal` family. Per-business-unit isolation inside the single Sandbox — SMUS projects plus Stage 16's per-group prefixes — is the interim. This is the first stage about *scale* rather than about a new capability |
| **Prerequisites** | Stages 2, 3, 4, **5** and 6 — Stage 5a for the consumer side the module composes (`terraform-modules/consumer-data/` — `sandbox/data/` pins v0.6.0 on 2026-10-18, and a vend pins whatever tag is current then — the per-account `DataLakeSettings` and the share map step 5 extends). Everything a business unit's Sandbox must arrive holding has to exist and have been applied by hand at least once |
| **Consumes** | [D21](../decisions/D21-development-account.md), [D23](../decisions/D23-ou-structure.md), [D26](../decisions/D26-unified-studio.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md), [D37](../decisions/D37-nested-ou-inheritance.md) |
| **Proves** | that a business unit's `Sandbox` can be created, made usable and closed without a hand-written slice |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

> **One input this stage's mechanism was never told about** (measured 2026-09-06 by Stage 6b step 0.5b,
> recorded in [`INV-17`](../../AWS_STATE.md) and argued in [D34](../decisions/D34-account-vending.md)):
> the landing zone has **account auto-enrollment ON**, so an account created with
> `organizations:CreateAccount` and placed in a **registered OU** is baselined without Account Factory.
> This stage takes D34's rung 2 (`aws_servicecatalog_provisioned_product`) because a non-Factory account
> was assumed unenrolled. **That assumption is false and the choice is unchanged for now** — the stage is
> blocked on the quota, and the provisioned product is what makes the console's *Update account* flow work
> — but the alternative is to be weighed when this stage is written. Step 2 weighs it from the vendor's
> pages, read 2026-10-20; the choice is D34's and the user's.

---

**Objective:** adding a business unit is a merge request. One input — the unit's name — produces its
`Sandbox` account, in the **`Sandboxes` OU** (nested under `Interactive`, D23), with networking, identity
and its domain association, and nothing about it is typed twice. The OU is what makes the account
governed on arrival: the `Interactive` policy set inherits down into it, so `ManagedOrganizationalUnit` in
step 2 points at `Sandboxes` and the account needs no policy attachment of its own.

> **The OU needs no attachment either** ([D37](../decisions/D37-nested-ou-inheritance.md), measured in
> Stage 1c 7.6/7.7).
> **Nothing is attached or enabled on `Sandboxes` — no SCP, no RCP, no tag policy, no Control Tower
> control — unless it is a configuration that *differs* from `Interactive`'s.** The OU is a registered
> target and would accept one; it is declined so that sameness is expressed by inheriting rather than by
> copying, because a duplicated statement is a second place to forget an amendment (Lesson 14). So this
> stage's `for_each` must not grow a per-OU policy attachment for the sandbox branch, and the one thing to
> carry: **`Sandboxes` reads as zero enabled controls in Control Tower while its accounts are fully
> governed** — an enabled control is per OU and is not inherited as an enablement, only the statements it
> emits are. Read `Interactive` when asking what applies to a Sandbox account.

**Scope, which is narrower than it first looks (D35).** Only `Sandbox` multiplies. `Staging`, `Production`
and `Data Governance` are structural and singular, so **the promotion chain is untouched by this stage** — one set
of pipelines, one deploy role pair, one approval gate, however many units exist. The multiplication is
entirely upstream of the graduation boundary, which is the cheapest place for it to be, and it is why this
stage can be built without reopening Stages 8 to 10.

**Why this stage is late.** Automating a thing that has been built once by hand is
engineering; automating a thing that has never been built is speculation. Every slice this stage
parameterises — `foundation/`, `egress/`, the identity assignment, the domain association — exists and
has been applied by Stages 3 to 6. **What this stage adds is the substitution of a name for a hardcoded
account.**

**The central question this stage was holding is closed, and without N** (2026-09-05,
[D38](../decisions/D38-single-egress-hub.md)). Stage 4 landed the tunnel in *the* Sandbox account, which put
the VPN on the multiplied side and made it a per-unit problem. **6c moved it**: the tunnel and the estate's
only egress now terminate in **`VPC-Networking`, a hub in Production**, and every spoke peers to it. That is
one of the three shapes this stage listed — *a designated hub* — taken early and deliberately, because the
client-plane DNS break of 2026-08-26 forced the topology before N did.

The two shapes not taken, kept because the trigger to revisit them is real:

- **A shared network account with Transit Gateway** — the institutional answer
  (`docs/plan/institutional-delta.md`), a new structural account, and a real hourly cost per attachment.
  Peering is O(n) here rather than O(n²), so TGW starts paying when the route tables stop fitting in one
  head, not when the arithmetic says so. **This is where the hub goes when a slot frees** — D38 §2's
  revision trigger, with `10.60.0.0/16` already reserved.
- **Per-unit VPN endpoints** — the strongest isolation, no shared path, the largest per-unit cost. Ruled
  out by the same argument that ruled out per-account NAT: one internet-facing host per unit is N hosts to
  patch and N client endpoints to distribute.

**What this stage still owes the topology at each vend:** a CIDR drawn from `10.16.0.0/13`, **two** peering
pairs (to `VPC-Networking` for the proxy and the tunnel, to `VPC-SharedServices` for GitLab), one more child
zone in the `awsds.internal` family with its association authorization **toward** Production (INT-22's
reversed choreography), and one more source block in the proxy's allow-list. All four are generated from
the same peering map 6c step 3.1 wrote — a vend adds a row, not a design.

**What a vend owes the catalog, written at [6f](stage-06f-data-governance.md) step 9.1
(2026-09-18).** A **domain unit** is DataZone's own container for a business unit, and it is the
object this stage's cardinality maps onto — never a second domain, which the vendor documents no
publishing, subscription or Share between (`institutional-delta.md`, "Domain topology"). What a
domain unit scopes, read from the concepts page and from the live domain:

- **The authorization policies**, which are per unit and per type. On this domain's root unit, of the
  types that apply there, exactly one carries a grant: `CREATE_PROJECT_FROM_PROJECT_PROFILE`, naming
  one Identity Center group. `CREATE_PROJECT`, `CREATE_DOMAIN_UNIT`, `CREATE_GLOSSARY`,
  `CREATE_FORM_TYPE` and `CREATE_ASSET_TYPE` are empty, and both `OVERRIDE_*` types are empty. So a
  per-unit domain unit is where *"who in this business unit may create a project"* stops being one
  answer for the whole estate.
- **`ADD_TO_PROJECT_MEMBER_POOL` is the one to look at before vending the second unit.** It reads
  `allUsersGrantFilter` today — every user of the domain may be added to any project's member pool,
  DataZone's default. With one business unit that is the same set of people either way; with two it
  is the difference between units that can see each other's projects and units that cannot, and
  nothing in this stage's module touches it.
- **Delegation**, which is the reason the object exists: a domain unit grants a unit's own owner the
  authority to set those policies, *"a delegated authority from account owners to domain unit
  owners"*. That is the governance half of what this stage does for the network half.
- **Glossaries, metadata forms and custom asset types** are owned per unit by the same policies, so a
  unit can carry its own vocabulary without the estate's.

**It fits D35 and costs one decision.** `Sandbox` multiplies per business unit and the domain does
not, so a vend adds a **domain unit** beside its account rather than a domain — one more row in the
same shape as the CIDR, the peerings and the zone. What is not decided here is whether the member
pool stays open across units, and that is the first reading the second vend takes.

**To execute:**

1. **`terraform-modules/sandbox-unit/`** — one module, one input (the unit name), composing what already
   exists: a `foundation/` VPC from the Stage 3 module with its CIDR taken from the allocation table, the
   `egress/` slice, and the Route 53 associations that let the unit
   reach GitLab by name. **Two PKI items, not one, and the second is the easy one to miss (D36):** the zone
   associations *and* the **internal CA root reaching this unit's `dev-env` image** (INT-19). The first
   fails as `NXDOMAIN`, the second as a TLS handshake error inside a notebook — neither says "a business
   unit was vended without it". Both belong in this module, or they are Lesson 14 in a new place.
   **Composition, not new resources** — if this module needs a resource type that
   Stage 3 or Stage 5a did not already build, that is a signal the earlier stage was written for a singleton
   and should be fixed there instead.

   **What a unit's account owes Bedrock, which no module carries** ([Stage 6e](stage-06e-claude-code-bedrock.md),
   recorded at this receiving end, Lesson 34): the model-access use-case form, submitted per account while
   6e step 2.1 keeps it in `Sandbox` alone (the form from `Management`, which extends to child accounts, is
   that step's named alternative for the day a second account needs one); one agreement per scoped model
   and account ([`claude-code-sagemaker.md`](../runbooks/claude-code-sagemaker.md) M4), the act that
   actually enables a model; the retention mode `none` in every enabled Region, per account and Region and
   set by hand (6e decision 16); and the grant, which is `sandbox/bedrock/`'s per-project policy today and,
   at the second unit, 6e's shape (c), a dedicated role the project role chains into, once a measurement
   says whether a same-account `sts:AssumeRole` needs an identity grant on the calling role or the trust
   policy alone suffices.

   **The portal's Generative AI models owe a unit objects of their own** ([Stage 17](stage-17-sandbox-machine-learning.md)
   decision 13 (b), applied in `Sandbox` on 2026-10-19 and recorded at this receiving end, Lesson 34), in
   this order:
   - **The unit's `model-access/` slice**, `[P]` at rank 52 as `sandbox/model-access/` is, after the unit's
     `sagemaker/` pass 1, whose D13 boundary both roles carry. The provisioning role is
     `AmazonSageMakerBedrockModelManagementRole-<Data Governance account>`, the name the console's *Submit*
     looks for before it creates a role of its own outside the boundary; the slice builds it from the domain
     ARN in `governance/`'s state. The consumption role is `awsds-<env>-bedrock-model-consumption`. Both are
     trusted by `datazone.amazonaws.com` under the domain's account.
   - **A membership in `data-governance/governance/`**: the unit's `InfrastructureAccess` role, through its
     `IAM_ROLE_SESSION_GROUP` profile, as a `PROJECT_CONTRIBUTOR` of `GenerativeAIModelGovernanceProject`.
     `model-governance.tf` names Sandbox's role alone, resolved through the `sandbox` provider alias, so a
     unit adds a role lookup, a group-profile lookup and a membership. The lookup needs the role's group
     profile to exist; Sandbox's was made in the portal on 2026-10-15 (INT-25). Without the membership the
     unit's console finds no governance project and keeps *Manage* greyed, *"Model governance project does
     not exist"* (inferred from Stage 17's reading of the console's code).
   - **The console's *Manage* in the unit's account and Region**, a console act: the governance project
     chosen, the models ticked under *Enable in projects* and *Enable in playground*, the slice's
     consumption role in each playground model's *Manage roles*, then *Submit*. It writes each model's
     environment, asset and listing in the governance project, and the playground's application inference
     profiles in the unit's account. Sandbox's rows are in Stage 17's log of 2026-10-19.

   The governance project and its profile are the domain's, one for every unit, and the Bedrock SCP's
   entries, 6e's and decision 11's, reach a unit through `Interactive`.
2. **The account request itself, and the rung to use (D34).** The stage's rung creates the account through
   **Account Factory**, and what changes is who fills in the form:
   `aws_servicecatalog_provisioned_product` against the Account Factory product, with `AccountEmail`,
   `AccountName`, `ManagedOrganizationalUnit` and the SSO fields as provisioning parameters — the middle rung
   of D34's ladder, which buys a diff and a review without AFT's dedicated management account and pipelines.
   An account created with `CreateAccount` and moved into `Sandboxes` is enrolled too, by auto-enrollment
   (the note at the top); the two are weighed below. Three things rung 2 needs, and they are why this is a
   stage and not a footnote:
   - **A principal with Service Catalog rights in the Management account.** This reopens D34's ownership
     question and must be answered explicitly: a pipeline role, not a standing human administrator, is the
     whole point of moving off the console. Its rights are wider than Service Catalog's (read 2026-10-20):
     `AWSServiceCatalogEndUserFullAccess`, `organizations:CreateAccount` and `DescribeCreateAccountStatus`,
     and, for an identity that provisions programmatically (the page's case is a Lambda function), `sso:`
     and `sso-directory:` actions on `*`, `sso-directory:CreateUser` and `sso-directory:AddMemberToGroup`
     among them, with `controltower:CreateManagedAccount` and `controltower:DeregisterManagedAccount`.
   - **`prevent_destroy` on the provisioned product**, in its own slice. Terminating it does not close the
     account (read 2026-10-20): Service Catalog's *terminate* unenrolls it, and Control Tower removes its
     controls, its baseline and `AWSControlTowerExecution` and moves it to the organization's root, while
     the account keeps its resources and the Account Factory SSO user's administrator access. A
     `terraform destroy` reaching it leaves a unit running outside `Sandboxes` and the `Interactive` policy
     set, and must not be possible. The provider (v6.69.1) plans a change of `name` or `notification_arns`
     as a replacement, which `prevent_destroy` refuses like any destroy; removing the resource block removes
     the protection with it.
   - **The e-mail address**, per unit and immutable. It follows the `+alias` convention and is registered in
     `secrets/emails.md` before the apply, never generated. No AWS account may already use it, and
     `CreateAccount`, which Account Factory calls, takes 6 to 64 characters of 7-bit ASCII and does not
     refuse `+`. A closed account's address is spent rather than held for ~90 days (step 6).

   **The product and its keys, read 2026-10-20 from the vendor's pages.** The product is `AWS Control Tower
   Account Factory`, in the portfolio `AWS Control Tower Account Factory Portfolio`. Its provisioning
   parameters are `AccountEmail`, `AccountName`, `ManagedOrganizationalUnit`, `SSOUserEmail`,
   `SSOUserFirstName` and `SSOUserLastName`. `ManagedOrganizationalUnit` takes `OU_NAME (OU_ID)`, a format
   that replaced `OU_NAME`, so `Sandboxes`' value carries its OU id. `ProvisionProduct` also names the
   product, a provisioning artifact and a launch path by id. The console procedure forbids TagOptions,
   notifications and a resource plan, each of which can fail the provisioning; whether the provider's
   `default_tags`, which reach the provisioned product's `Tags`, count as TagOptions is not on the page.
   At most five account operations run at once, and the target OU needs `AWSControlTowerBaseline` enabled.
   The binding reading is the product's own, in Management: `servicecatalog
   describe-provisioning-parameters` against its current provisioning artifact, the user's.

   **The auto-enrollment rung, weighed against rung 2 from the same pages.** Nothing here is measured.
   - **Management.** `CreateAccount` and `MoveAccount` are callable from the management account alone, so
     this rung keeps the ownership question, with Organizations rights in place of Service Catalog's and
     no Identity Center directory writes. `CreateAccount` takes no resource, only request-tag conditions.
     `MoveAccount` is scoped by account, OU and root ARNs, with no key that tells the source from the
     destination, so a policy naming the root and `Sandboxes` admits a move either way.
   - **The role.** Every enrolled account holds `AWSControlTowerExecution`. `CreateAccount`'s `RoleName`
     names the administrator role Organizations creates, trusted by the management account, and Control
     Tower's own vend passes that name; the provider cannot read `role_name` back. Whether enrollment
     creates the role when it is absent is not on these pages.
   - **What arrives.** Account Factory deletes the default VPC, which has an internet gateway and a public
     subnet per Availability Zone, in the governed Regions of an account it creates; enrollment deletes no
     VPC, so this rung owes that deletion. The pages do not say whether Account Factory still deletes it
     with VPC creation off (Stage 3 step 0.3); the first vend reads it, under either rung, by `IsDefault`,
     since a default VPC is `172.31.0.0/16`, the range the Account Factory VPCs held. No account with a
     profile holds a default VPC in `us-west-2` (read 2026-10-20, the log), but all six were vended before
     0.3, so that reading does not answer it. No `SSOUserEmail` exists, so the account arrives without
     D32's direct assignment (inferred: the field is the product's).
   - **Timing.** Enrollment is eventually consistent, minutes to hours, so the vend's next steps wait for it.
   - **Destroy.** `aws_organizations_account` removes the account from the organization by default, which a
     created account allows only after four days and with a payment method, a support plan and verified
     contacts of its own; with `close_on_deletion` it closes the account while still enrolled, which
     Control Tower's closing page says not to do (step 6). `prevent_destroy` is owed here too.
   - **Afterwards.** No provisioned product exists: re-registering the OU updates the account, and a move
     to the root or to an unregistered OU unenrolls it.

   Which rung is D34's revision and the user's ([`waiting-on-the-user.md`](../waiting-on-the-user.md)).
   Recommended for that choice: the auto-enrollment rung, whose Management principal holds no Service
   Catalog and no directory writes on `*`, with the default VPC's deletion and the enrollment wait written
   as readings `./aws/vending.py` takes; the first vend reads both and decides whether the rung stays.
3. **Identity per unit (D35).** A `sso-group-data-scientists-<bu>` group, assigned `DataScientistAccess` on that unit's
   Sandbox and nothing else. **There is no second Interactive account to assign into since 6b** — the
   approver groups stay institutional and single, and `DataScientistStagingAccess` is a read-only seat on a
   Workload account, not a per-unit one. Generated from the same unit name as
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
4. **Domain association (D26, INT-12) — the one act in this stage that no merge request can perform, in a
   fixed order.** Nothing creates a domain — the root deny on `datazone:CreateDomain`
   stands (exercised in both directions on 2026-08-21, so it is known to fire rather than merely
   attached), and this stage is where the pressure to break it will first be felt. **INT-12 owns the
   mechanics** — console-only, a RAM share the domain initiates — and they are not restated here.
   **Measured 2026-08-21: the share is organization-scoped and auto-accepts, so there is no invitation and
   no clock.** What this step owes is the sentence INT-12 cannot carry: **a stage whose whole
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

      > **The association does not live in the domain's admin portal** — the
      > `dzd-*.sagemaker.<region>.on.aws` surface. Stage 6 step 1.3 was corrected on that exact point on
      > 2026-08-21, **before** it was executed, and this copy never heard: the correction landed at one end
      > while the stale path stayed alive at the other (**Lesson 35**).
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
   5. **By-hand edits in `data-governance/governance/`, and an alias alone is not enough.** The
      `backend.SMUS_MEMBERS` row, a new aliased provider in `providers.tf` (Terraform cannot `for_each` a
      provider) **and** new entries in `locals.tf`: `member_account_ids` and `project_profiles` are static
      literals, and `experimentation` is pinned to `sandbox`, so unit 2 is reachable by no profile until
      both maps grow. **Record the choice this raises rather than performing it by rote:** these three
      hand edits per unit against AWS's own account-agnostic mechanism, `datazone create-account-pool`
      (CLI-only) — the note Stage 6's forward-constraint paragraph deliberately did not adopt at N=1.
      Step 1's model governance membership and its two lookups are further edits in the same slice.
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

   **But the *plumbing* is the module's**, and the distinction matters because the failure looks identical
   from the outside (Stage 5a pass 3, 2026-08-19). The mechanical facts the
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
     reason Stage 5a was told to write every list as a map from day one;
   - **and the unit's own consumer slice is already a module — `terraform-modules/consumer-data/`,
     applied 2026-08-19** (Stage 5a pass 4; v0.2.0 since the same-day revision). `sandbox-unit` composes a
     *call* to it with one changed input,
     not a copy of it: the settings, the `alias/awsds-<env>-data` CMK (**no derived zone or workgroup since `consumer-data-v0.6.0`, 2026-08-26** — D19 revised),
     the resource links and the local re-grants all come with it. **The re-grant is a pair**: `DESCRIBE`
     on each resource link *and* the permission on the target — and a vend that lands only the second half
     produces a unit whose scientists see no database at all;
   - **and two machinery edits, neither of them a policy edit.** The unit joins `DATA_CONSUMERS` in
     `scripts/tfhygiene/backend.py` — which emits the `lake` map to its own `data/` slice. **There is no
     second emission** (D19 revised): `data_consumers` to `identity/sso/` left with the persona's
     Athena/derived statements, so a new unit no longer re-plans `identity/sso/` at all. If a future set
     ever enumerates per-consumer resources again, the 4c rule returns with it: enumeration from state,
     never a wildcard.
6. **The teardown half, which is what makes a unit disposable.** `make down ENV=<bu>` must work against a
   generated Sandbox exactly as it does against the hand-built one, and closing a unit must be a documented
   procedure with the slot and the e-mail address stated up front (D34's headroom item, whose e-mail half
   the reading below corrects).

   **Closing an account, read 2026-10-20 from the vendor's pages:**
   - **Unenrolling comes first**, by Control Tower's and Account Management's pages alike: the provisioned
     product's *terminate* under rung 2, a move to the root or to an unregistered OU under auto-enrollment.
     An account closed while enrolled reads *Suspended* and *Enrolled*, blocks its OU's re-registration for
     the 90 days, and leaves its provisioned product to delete after them.
   - **The close** is `organizations close-account` from Management: `PENDING_CLOSURE`, then `SUSPENDED`.
     Those are the account's `Status`; its `State` reads `CLOSED` beside `SUSPENDED` (`EXC-01`'s account,
     read 2026-10-20, the log).
   - **The post-closure period is 90 days.** AWS Support can reopen the account during it. After it AWS
     closes the account permanently and deletes its content except its CloudTrail trails, the account id is
     never reused, and Management's event history records `AccountDepartedOrganization` with
     `departureMethod:CLEANED`.
   - **The slot** counts against the organization's account quota until the account is permanently closed.
     Removing the account from the organization before the close frees it, but a created account leaves
     only after four days and with a support plan, verified contacts and a payment method of its own, and
     then pays its own bill outside every organization policy.
   - **The e-mail address** registered at closure can never become another account's primary address; the
     page names no period, so it is spent, not held for ~90 days. To keep it for a later vend, the root
     address is changed before the close: from Management, `account start-primary-email-update` and
     `accept-primary-email-update`, with a one-time code sent to the new address, under the Account
     Management trusted access Stage 6b enabled.
7. **Prove it with the second unit, not the first.** The first unit through this module is the one that was
   built by hand and is being adopted; the proof is a *second* one, created from nothing but a name, whose
   `terraform plan` on every shared slice comes back empty afterwards.

**The mechanical half, which the stage gets before the first vend:** a vend's failure mode is *an account
that is 90 % configured*, and **`./aws/vending.py`** reads it ([`aws/INDEX.md`](../../../aws/INDEX.md)).
Its checks are the same list eight `aws/` scripts already run, parameterised by unit and generated from
`scripts/tfhygiene/backend.py`'s tables: `VN-1` the account is in `Sandboxes` with no policy attachment of
its own, nor the OU (D37), and every active account in `Sandboxes` is a declared unit; `VN-2` its CIDR is
inside `10.16.0.0/13` and overlaps nothing in `backend.VPC_CIDRS`; `VN-3` **both** peerings exist with
routes on both sides (`NT-11`'s rule, per unit), no other peering does, and the unit names the hand-built
unit's peer slices; `VN-4` its child zone is associated into `VPC-Networking` and its authorization still
exists (INT-22), and the unit's VPC resolves the apex and its child zone alone; `VN-5` its source block is
in the proxy's allow-list and its security group (`PX-3`'s and `PX-1`'s rules, per unit); `VN-6` its SSO
group has exactly one assignment in `Sandboxes`. **Against the hand-built unit**, where every answer is
already known, it read `sandbox` on 2026-10-18 with the environment down as nine passes and one note.
`VN-6`'s discriminator (Lesson 50) is the reason the note is not a failure: the shared
`sso-group-data-scientists` is unit 1's principal while one unit is declared, and its two seats in
`Workloads` stay on it by design (`docs/ORGANIZATION.md`, the dagger under Assignments); at the second unit
the shared group holding a unit's seat fails. A check that has only ever run against the thing it was
written from is not a check, so the same day it read `Staging`, which is no unit, as four failures (`VN-1`,
`VN-2`, `VN-3`'s peer slices, `VN-6`), and every failure branch was exercised against fabricated readings.
The proof is still step 7's second unit.

**Deliverables:** a business unit's Sandbox account, its VPC, its identity assignment and its
domain association all produced from one name in a merge request; a second unit created without editing any
module; **two peering pairs, one child zone and one proxy source block generated from the same map** rather
than authored; and the quota headroom restated in units rather than in accounts — **one slot per business
unit**. The VPN-topology decision this stage used to owe is D38's, taken on 2026-09-05 at N = 1.

**Cost:** measured into [`docs/PRICING.md`](../../PRICING.md) §3, *A Sandbox unit*, before the first vended
one (Lesson 6), from the hand-built unit's counts on 2026-10-18: **3.50 USD/month at rest** in year one
(three CMKs and the child zone; 6.50 and 9.50 as the keys gain versions), **0.180/h** of interface
endpoints while the unit works, and 0.36-0.87 of Config per `[E]` cycle. The account and the hub add
nothing. The dominant term is not the account — it is **one set of interface VPC endpoints per unit**,
N × 0.180/h with N units working, which is what decides whether centralized endpoints shared by RAM stop
being optional (D35).

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
