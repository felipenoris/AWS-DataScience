# Stage 14 — Per-business-unit Sandbox vending

| | |
|---|---|
| **Status** | not started — the first stage that is about *scale* rather than about a new capability |
| **Prerequisites** | Stages 2, 3, 4 and 6. Everything a business unit's Sandbox must arrive holding has to exist and have been applied by hand at least once |
| **Consumes** | [D21](../decisions/D21-development-account.md), [D23](../decisions/D23-ou-structure.md), [D24](../decisions/D24-shared-filesystem.md), [D26](../decisions/D26-unified-studio.md), [D34](../decisions/D34-account-vending.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | that a business unit's `Sandbox` can be created, made usable and closed without a hand-written slice |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** adding a business unit is a merge request. One input — the unit's name — produces its
`Sandbox` account, in the **`Sandboxes` OU** (nested under `Interactive`, D23), with networking, identity,
domain association and a filesystem, and nothing about it is typed twice. The OU is what makes the account
governed on arrival: the `Interactive` policy set inherits down into it, so `ManagedOrganizationalUnit` in
step 2 points at `Sandboxes` and the account needs no policy attachment of its own.

**Scope, which is narrower than it first looks (D35).** Only `Sandbox` multiplies. `Development`, `Staging`
and `Production` are structural and singular, so **the promotion chain is untouched by this stage** — one set
of pipelines, one deploy role pair, one approval gate, however many units exist. The multiplication is
entirely upstream of the graduation boundary, which is the cheapest place for it to be, and it is why this
stage can be built without reopening Stages 8 to 10.

**Why this is a late stage and not an early one.** Automating a thing that has been built once by hand is
engineering; automating a thing that has never been built is speculation. Every slice this stage
parameterises — `foundation/`, `egress/`, `nfs/`, the identity assignment, the domain association — exists and
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
  (`plan/institutional-delta.md`), a new structural account, and a real hourly cost per attachment. Peering
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
   `egress/` slice, `nfs/` for the unit's filesystem (D24), and the Route 53 associations that let the unit
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
   it** (`plan/conventions.md`): the **assignment** is Terraform, driven by the same human-authored unit map
   as everything else in this stage — which is still "enumerated" under D34, because a unit gets its grant by
   being written down. The **group** and its members are directory objects; here the module may create the
   group as a convenience, but the day the directory comes from an IdP the group arrives over SCIM and this
   module must keep working with only the assignment. Write it so removing the group resource is a deletion,
   not a redesign.
   **This is also the step where the per-unit tokens are first exercised for real**: `<env>` and the tag
   policy's allowed values must both admit the unit's token, or the first apply in the new account is an
   `AccessDenied` (`plan/conventions.md`, the D35 note; Stage 1c step 7.8).

3b. **The account-level baseline that no policy applies retroactively.** This step owes the new account
   **account-level S3 Block Public Access**, and the order is not negotiable: the account inherits the
   organization-root SCP the moment it lands in a governed OU, and there is no cross-account API for the
   setting. **Decision 7 (settled 2026-08-13) is what makes this step possible at all**: the root deny on
   `s3:PutAccountPublicAccessBlock` carves out the `InfrastructureAccess` Identity Center role, so the call
   succeeds from the unit's own `awsds-infra-sandbox-<n>` profile and from nothing else. Run it, verify it
   with `aws s3control get-public-access-block`, and **record it in the vend log** — the carve-out makes the
   baseline recoverable, not automatic, and a unit that silently differs from the others is exactly what
   this stage exists to prevent.
4. **Domain association (D26, INT-12).** Associate the new Sandbox with the single unified domain in Data
   Governance and configure the ML blueprint into it. Nothing creates a domain — the root deny on
   `datazone:CreateDomain` stands, and this stage is where the pressure to break it will first be felt.
5. **Data access is *not* granted here.** A new unit arrives with no Lake Formation permissions. Whether units
   share data or are isolated by LF-Tags is the governance manager's decision (D35), routed through the
   subscription workflow like any other access — a vending flow that also grants data access is a flow that
   grants data access by default.
6. **The teardown half, which is what makes a unit disposable.** `make down ENV=<bu>` must work against a
   generated Sandbox exactly as it does against the hand-built one, and closing a unit must be a documented
   procedure with the ~90-day slot and e-mail retention stated up front (D34's headroom item).
7. **Prove it with the second unit, not the first.** The first unit through this module is the one that was
   built by hand and is being adopted; the proof is a *second* one, created from nothing but a name, whose
   `terraform plan` on every shared slice comes back empty afterwards.

**Deliverables:** a business unit's Sandbox account, its VPC, its filesystem, its identity assignment and its
domain association all produced from one name in a merge request; a second unit created without editing any
module; the VPN topology decision recorded together with the number of units it was made for; and the quota
headroom restated in units rather than in accounts — **one slot per business unit**.

**Cost:** measured into [`PRICING.md`](../../PRICING.md) per unit before the first vended one, not after
(Lesson 6). The dominant term is not the account — it is **one set of interface VPC endpoints per unit**,
which is what decides whether centralized endpoints shared by RAM stop being optional (D35).

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
