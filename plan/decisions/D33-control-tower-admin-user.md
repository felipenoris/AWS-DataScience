# D33 — The `AWS Control Tower Admin` user, and who drives Account Factory

**Status:** Decided (2026-08-09): **Account Factory is driven from the access portal, never from root; Control Tower's own admin user carries the vending.** **Amended the same day by [D34](D34-account-vending.md): the retirement is withdrawn — the user is kept enabled as the standing owner of Control Tower administration.** Everything below about *reach*, *the shared inbox* and *why not to rename or delete it* stands unchanged; only the end date is gone.

**In one line:** root cannot vend accounts at all — the landing zone creates its own administrator, carrying the Management root's e-mail and reaching Management, Log Archive and Audit, and that user drives the vending (permanently, since D34).

**Related decisions:** [D10](D10-identity-center-delegation.md), [D16](D16-break-glass.md), [D32](D32-account-factory-sso-user.md), [D34](D34-account-vending.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 1b](../stages/stage-01b-identity-and-controls.md)

---

## Rationale and consequences

**What execution found, in two parts.** Enabling Control Tower produced an *"Invitation to join AWS IAM
Identity Center"* addressed to the **Management account's root e-mail**, and an Identity Center user with
display name **`AWS Control Tower Admin`** carrying that same address. Nobody asked for it: the landing zone
creates a directory with its own groups, permission sets and a first administrator, and that administrator's
address is the management account's. Then, from the root user, Account Factory refused to open at all —
*"Your AWS IAM identity does not have access to the AWS Control Tower Account Factory portfolio in AWS
Service Catalog"*. That is **documented behaviour, not a misconfiguration**: Account Factory is a Service
Catalog product, access to its portfolio is granted to IAM users, groups and roles, and the AWS docs state
plainly that to provision you must be signed in with `AWSServiceCatalogEndUserFullAccess` and **"you cannot
be signed in as the Root user"**. There is no principal to associate for root, so the fix is not to grant
something — it is to stop using root, which is what this project wanted anyway (principle 2). The working
path, and now the specified one: sign in at the **AWS access portal** as `AWS Control Tower Admin`, take
`AWSAdministratorAccess` on the Management account, then Account Factory.

**The problem this leaves, and it is bigger than "an administrator of Management" — corrected 2026-08-09
against the console.** The user's whole footprint comes from **two group memberships and no direct
assignment**, which is what the documented table produces:

| Group | Management | Log Archive | Audit | Member accounts |
|---|---|---|---|---|
| `AWSControlTowerAdmins` | `AWSAdministratorAccess` | `AWSAdministratorAccess` | `AWSAdministratorAccess` | `AWSOrganizationsFullAccess` |
| `AWSAccountFactory` | `AWSServiceCatalogEndUserAccess` | — | — | — |

So it is **administrator of Management, Log Archive *and* Audit** — and that third and second are the ones
that matter. Log Archive holds the organization CloudTrail bucket; Audit holds the security findings plane.
**The bootstrap administrator can therefore delete the evidence of its own use, including the trail D16's
break-glass alarm is built on.** That is the watcher problem, not a scoping detail, and it is why the
retirement below is a schedule rather than a preference. The `AWSOrganizationsFullAccess` on member
accounts is by contrast nearly inert — Organizations is a management-account API — **with one member-account
call that is not: `organizations:LeaveOrganization`**, which drops every SCP and every Control Tower control
for that account in a single call. 1b step 7 already denies it at the organization root; this finding is
what turns that line from hygiene into a load-bearing control.

On top of that reach sits the original collision: the **login identity is the root e-mail address** — the
exact shape D32 refuses for vended accounts, arrived at from the other direction. It does not make D16's
alarm wrong: that alarm fires on `userIdentity.type = Root`, and a federated Identity Center session is not
that, so the two sign-ins stay distinguishable in CloudTrail. What it collapses is the **inbox**: one
address receives the root credential's recovery mail, the break-glass warning, and a routine daily-login
invitation. Two consequences, both immediate — the SNS subscription built in 1a step 5 **must not be that
address**, and this user **must have MFA** before the next vend.

**Why the reach cannot be narrowed while it is still in use, which is worth stating so nobody tries.**
`AWSControlTowerAdmins` is atomic: its Management administrator — the thing 1a steps 4, 5 and 6 actually run
on — arrives in the same membership as the Log Archive and Audit administrator, and leaving the group to
drop the latter drops the former too. Splitting it would mean writing direct user assignments, which is the
pattern this plan is removing rather than adding. So the control is **not** a smaller grant; it is **MFA plus
a bounded window**. **Since D34 the window is not bounded**, and that changes what has to carry the weight:
MFA becomes a standing control rather than a stopgap, and the two things that limit this principal after the
fact — **Object Lock in *compliance* mode** on the Log Archive bucket (1b step 9) and the **group-membership
alarm** (1b step 8) — stop being belt-and-braces and become the control set. D34 states them in that form.

**Where the ability to vend actually lives, which decides how it is replaced.** AWS states the rule at the
group level — *"IAM Identity Center users that provision accounts must be in the `AWSAccountFactory` group
or the management group"* — so **vending is a property of group membership, not of this user**, and the two
groups are very far from equivalent. `AWSAccountFactory` grants exactly one thing,
`AWSServiceCatalogEndUserAccess` on Management, which is what Account Factory mechanically requires;
`AWSControlTowerAdmins` grants administrator across Management, Log Archive and Audit. **The narrow replacement is therefore
real, with one precision that decides how it is used:** AWS's own table says users of
`AWSControlTowerAdmins` in the Management account *"are the only ones that have access to the AWS Control
Tower console"*. So a principal holding only `AWSAccountFactory` vends through the **Service Catalog**
console — the Account Factory product — and not through the Control Tower console. That is a usability
difference, not a capability one, and it is the trade this plan takes.

**The decision as originally taken: treat it as a bootstrap credential with a defined end** — it vends the
accounts Stage 1a needs, a finite job ending inside that stage, and is **disabled** (not deleted) once the
infrastructure user's group-based path has been proven in 1b.

**This is the half D34 withdrew, and the reason is that "a finite job" was a premise about frequency rather
than a finding.** The account list is not static: a sandbox for a different line of work, a second data
domain or a per-workload staging account are ordinary requests, and each of them is an account *and*
sometimes an OU. So the user stays enabled and owns Control Tower administration. **The narrow replacement
described below remains correct and remains unused, for one reason that decides it:** `AWSAccountFactory`
reaches the Account Factory *product* through the Service Catalog console, but AWS documents the **Control
Tower console** — where OUs are created, accounts enrolled and the landing zone updated — as reachable only
by `AWSControlTowerAdmins`. Creating OUs is part of the job, so the narrow path does not cover it. What the
choice preserves is the thing worth preserving: **the infrastructure user gains no Management-account reach**,
so D32's one-administrator-one-MFA-device shape over the vended accounts is untouched.

**Why not delete it, and why not simply repoint it at a fresh address** — the second is the tempting
answer and it is the wrong one. Deleting the only identity that has ever reached Account Factory, before the
replacement has been *proven*, is the lockout shape D16 exists to avoid: prove first, then close. And
changing its e-mail keeps a **standing Management administrator alive in order to fix a mail-routing
problem** — it treats the symptom (the shared inbox) and leaves the cause (an administrator nobody
assigned). It is also the change most likely to be silently undone: Control Tower owns this user, and a
landing-zone update or repair that re-creates it under the management account's address would leave the
carefully-renamed one behind as a dormant administrator — precisely the "the placeholder does not get
replaced, it gets *joined*" failure D32 already refuses. **That argument survives D34 and is strengthened by
it:** an identity that is now permanent is exactly the one whose name must not depend on Control Tower not
re-creating it. The controls are therefore the two in the paragraph above, made permanent: **MFA on the
user**, and an **alarm subscription that is not that address** (with the SMS endpoint of 1a step 5 doing the
work the second address cannot, since every address here is a `+alias` on one mailbox).

**What the shared address does *not* break, so the risk is sized correctly.** IAM and IAM Identity Center
are separate identity systems with separate credentials and separate sign-in pages; one address in both
creates no authentication path between them and no privilege inheritance. CloudTrail still separates them by
`userIdentity.type`. The whole exposure is operational — one inbox holding a credential, its warning, and
routine login traffic — which is why the answer is MFA plus a distinct alarm address rather than a rebuild.

**What is limited later, and what is not — because "we will tighten this afterwards" is exactly the
sentence Lesson 5 exists to catch.** Separate the *credential* from the *scaffolding*. The credential — this
user — **is now standing (D34), so the three controls below are not supplements to a retirement; they are all
there is.** The scaffolding — Control Tower's groups, permission
sets and standing assignments — **is deliberately not deleted, and stays empty instead**: they are Control
Tower's objects, removing them breaks Account Factory and the Control Tower console, and a landing-zone
update may re-create them anyway. An empty group grants nothing; the exposure is not that it exists but that
**someone can add a member to it**. Three things address that, and two were already in the plan:

- **1b step 9 — S3 Object Lock in *compliance* mode on the Log Archive bucket, plus CloudTrail log file
  validation.** This is the direct answer to "the bootstrap administrator can erase its own trail", and the
  mode is the whole control: this principal is an administrator *of that account*, so it holds
  `s3:BypassGovernanceRetention` and walks through **governance** mode untouched. Compliance mode binds even
  that account's root. The step said only "Object Lock" until 2026-08-09.
- **1b step 8 — an alarm on membership changes to those groups.** Detective, free, and necessary because
  **there is no preventive control above the Identity Center administrator**: after D10 that is the
  delegated administrator in the Identity account, who can place themselves in `AWSControlTowerAdmins`. That
  residual is accepted and stated rather than papered over — it is the identity plane's own top.
- **Stage 12 — IAM Access Analyzer unused-access findings**, already scheduled there as the paid half of
  step 8's free one. That is what keeps "these permission sets are used by nobody" a measured fact instead
  of an assumption.

**Consequence for `ACCOUNTS_AND_USERS.md`: it is documented, and since D34 it holds a duty — but it is still
not one of the five personas.** The `SSO Users` section
lists the five humans the separation of duties is built from, and this is not a sixth — it approves nothing,
signs nothing, owns no data or workload and appears in no separation of duties. The one duty it does hold
since D34 — Control Tower administration — is an operational job attached to an identity, not a persona, and
it has no end date. But leaving it out entirely is worse than either option, because the
file would claim a directory of five while the console shows six: **an administrator that appears in no
document is indistinguishable from one that should not be there**, which is exactly the judgement a later
review has to make quickly. So it goes in its own subsection, "Identities this project did not create",
together with the Control Tower groups and permission sets that arrived with it.

**The edge this deliberately left open — now closed, by the trigger below firing.** Control Tower
administration *after* 1a — a landing-zone update, registering an OU, enrolling an account — had no assigned
owner once this user was disabled, which was tolerable only while the account list was closed. **The second
revision trigger fired on 2026-08-09** ("any stage after 1a needs Account Factory, at which point the owner
question above must be answered rather than deferred"), and the answer is [D34](D34-account-vending.md): this
user is the owner, permanently, and the file no longer promises a retirement. **What remains of the first
trigger** — Control Tower re-creating or re-enabling this user on a landing-zone update — **is no longer a
trigger at all**, since that is now the intended state. Its replacement, in D34: account creation becoming
frequent enough to be run from memory, or a second human, at which point AFT is re-priced.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
