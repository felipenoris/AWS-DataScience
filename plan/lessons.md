# Lessons carried forward

**The one file here whose content is not recoverable from anywhere else.** These are findings from the
planning period that re-reading the plan will not give back. Add to this list only what would otherwise
be relearned the hard way.

Read it before planning, reviewing, or settling a decision. `CLAUDE.md` carries the seventeen titles so a
lesson can be *recognised* without opening this file; the reasoning that makes each one usable is here.

---

1. **A copy of governed data landing somewhere less governed is not a hole to be closed.** It is a
   property of every SageMaker installation, not something D18 introduced. The control is the data
   perimeter (`plan/architecture.md` §4.2), which stops the copy leaving the organization; preventing the copy was never the
   control. The first answer given on this got it wrong and treated it as a newly opened gap.
2. **A stand-in that shares an account with the thing it de-risks proves nothing about permissions.** A
   `staging` Glue namespace *inside* Production was once invented to substitute for a Staging account: it
   shared an IAM surface and a blast radius with its own subject, so it could catch a schema error and
   never a permission error — which is the failure class a cross-account promotion actually produces.
   That is why D20 exists.
3. **When a decision moves a resource across an account boundary, re-check every condition that
   referenced it — especially conditions pointing at ephemeral things.** This nearly shipped: Stage 5
   pinned the Data Governance bucket policies to the consumers' `aws:SourceVpce`, but interface endpoints
   are `[E]` (new IDs on every `make up`) and since D22 live in a *different* account, so nothing would
   ever repair them. Anchor on the `[P]` S3 **gateway** endpoint, or on `aws:SourceVpc`.
4. **State that lives only inside an `[E]` resource is this design's recurring failure mode** (`plan/conventions.md` §5.1 rule
   2). Three hits already — EFS, the Studio domain, MWAA's metadata database — and it will recur for
   every stateful service considered for the `make up`/`make down` cadence. Check it before adopting one.
5. **An intention is not a control.** "No compute in Data Governance" was written down for a whole
   revision before anyone noticed the `Data` OU SCP never denied Glue jobs (D25). Likewise the three Lake
   Formation shares assumed organization-wide RAM sharing and cross-account version 3+ that no stage
   enabled — and their absence makes a share fail *silently*, the grant succeeding while the resource
   never appears. For every stated property, name the policy line that enforces it.
6. **Prices are measured, not reasoned.** The AWS Price List bulk API
   (`pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<service>/current/<region>/index.json`) is public,
   needs no credentials, and answers in seconds what the pricing pages answer in paragraphs. It is also
   how a *missing component* was found rather than a price difference — CodeArtifact does not exist in
   `sa-east-1` — which the Region check done by reading had missed. `PRICING.md` is built this way.
7. **A rejected-on-cost option goes stale in the direction that flatters the rejection.** The D7 table
   ruled MWAA out on a standing-cost floor that `mw1.micro` and MWAA Serverless had since removed.
   Re-check the price and the shape of any service the plan rejected on cost before acting on it. The
   same pattern closed D26 a day later: Unified Studio was rejected partly for having no IaC path, and
   official Terraform support had arrived (2026-07) before the rejection was ever acted on.
8. **When the classic `aws` provider lacks a resource, check the CloudFormation registry and `awscc`
   before declaring a Terraform gap.** `AWS::MWAAServerless::Workflow` existed, and `awscc` exposes
   every registry type mechanically — the "open issue, no branch" on the classic provider was the wrong
   place to look. The `aws-ia` Unified Studio module itself splits the same way: domain via `aws`,
   projects and blueprints via `awscc`.
9. **The axis question applies to people as well as to resources.** The same pass that moved the domain
   onto the ownership axis split the `Manager` persona along it: **Deployment Manager** (lifecycle —
   approves releases) and **Governance Manager** (ownership — approves data access). This had been
   written into `plan/institutional-delta.md` as "what an institution would do, notational here" a few hours earlier, and that was
   wrong: with one persona, a single human writes a job that reads restricted data, approves its release
   **and** approves its access to that data. Three acts, one signature. Never assign one person to both
   groups. The related trap: the governance manager must **not** have blanket read on the data they gate
   — an approver who can already read everything is not exercising a control.
10. **Before placing a new resource in an account, ask which axis it is on — and check whether a
   *registry* is being confused with a *runtime*.** D26's first draft put the Unified Studio domain in
   Development because that is where people work. Wrong: a domain holds projects, profiles, blueprints
   and the catalog, while blueprints provision the compute into whichever account the profile names. It
   is an ownership-axis resource and belongs with the catalog it governs (which is also what makes
   subscription fulfilment a *local* Lake Formation grant). The recurring symptom of getting this wrong
   is the question "so is that a production account?" — the honest answer is that off-axis accounts are
   not production, they are cross-cutting, and some of them are high blast radius instead.
11. **A decision that changes *who authors* an IAM policy invalidates every claim made about that policy.**
   Lesson 3 is about resources crossing an account boundary; this is the same failure one level up. D13's
   entire force is "the execution role holds no S3 on registered prefixes" — a sentence that was true
   because *we wrote the role*. D26 handed role authorship to a blueprint and nobody re-read D13 for a
   whole revision. The general form: when adopting a managed or opinionated service, list which resources
   it will now create on your behalf, and re-read every decision whose enforcement depends on one of them.
   INT-15 exists because of this.
12. **An edition or tier limit can reach a load-bearing control, not just a convenience.** The plan caught
   that GitLab CE lacks SAML group sync and correctly filed it as an annoyance. It did not notice that the
   *approval gate* — the thing D20's entire argument rests on — is the same kind of paid feature, so the
   lab's gate constrains "who can push a protected tag" rather than "who approves this release". Check the
   tier of every product feature a *control* depends on, separately from the features the workflow merely
   prefers.
13. **A verification command that returns empty on both success and failure is not a verification.** Stage
   1b's deliverable proposed `aws ram get-resource-share-associations` as the proof that organization-wide
   sharing was enabled; with no share yet created it returns an empty list in both cases. This is the
   detection-side twin of Lesson 5: an intention is not a control, and a command that cannot fail is not a
   check. Before writing a deliverable, ask what its output looks like when the thing is *broken*.

14. **A condition that has to appear in N places by hand is a control that will be missing from one of
   them.** The case that produced this was D30's blanket carve-out — a principal exempt from every custom
   `Deny`, which meant the *same condition* had to appear in every statement, and a set where three
   policies carry it and the fourth does not is one nobody can reason about, with no error to say which.
   **D30 was later reverted, and the lesson outlived it**, in two parts that apply to any policy set: any
   condition that must appear in N places gets **generated, not typed** — which is what forced the SCPs
   into Terraform, a gap that had sat unowned since Stage 1b was written and which is still the right call
   without the carve-out; and any ARN condition gets an **enumerated list, never a wildcard account**,
   because `arn:aws:iam::*:role/x` means "anyone who can create a role named x, anywhere". Both traps are
   invisible in a `plan` and cheap in CI. The per-function carve-outs the design still has (D26, D27) are
   subject to both.
15. **An adopted-against-advice decision is undone by *delivery*, not by re-argument — and a revision
   trigger written about operating something cannot fire while you are still building it.** D30 was
   recommended against, adopted anyway for reasons that held at the time, and reverted the same day. What
   reversed it was not the original argument being re-run: it was a review finding that the role could not
   be placed where its own justification needed it (the SCPs had moved to the Identity account in the same
   pass, and that was one of the two accounts the delivery mechanism could not reach). Three things to
   carry:
   - **Write the trade-off into the decision rather than re-arguing it**, and then spend the effort on the
     mitigations — that part was right, and it is what makes a decision inspectable later.
   - **Then check that the thing can actually be built where the argument needs it.** "Is this a good
     idea?" and "can this be delivered to the place that justifies it?" are different reviews, and the
     second one is the one that was missing.
   - **Write revision triggers that can fire during construction.** D30's were "a second person gains
     access" and "the role is assumed for something other than repairing a policy" — both about operating
     it, so neither could catch a defect in scoping it. Add at least one trigger of the form "if the thing
     turns out not to exist where X assumes it does".
16. **A manual step delegated to a console wizard is only as specified as the fields it names — and an
   unnamed field that grants permissions is a permission decision made by whoever is at the keyboard.**
   This one was caught by execution rather than by review, which is the point of writing it down. Stage 1a
   step 4 read "create the accounts through Account Factory, using the e-mails in `secrets/emails.md`" —
   complete-sounding, and wrong: the wizard asks for a **second** address under **Access configuration**,
   and AWS's wording for it is that the user *"will have administrative access to the account you're
   provisioning"*. The plan named one e-mail and the form has two, so the obvious answer — reuse the
   account's own address — would have made a root e-mail a federated administrator on every vended account, two
   steps before the same stage removes root credentials centrally. D32 settles the value. **The general
   form:** for every manual step, write down **every required field and the value it takes**, not only the
   fields the plan already has an opinion about. The unnamed ones do not stay unanswered; they get answered
   by whoever is executing, at the moment they least want to be designing identity. The tell is a step
   whose verb is "create X **using** Y" — `using` almost always hides a form.
17. **A service that "sets itself up" creates principals nobody chose — enumerate them before the next
   step depends on one.** Lesson 16 is about fields a wizard *asks* about; this is the class it does not
   cover, because the wizard never asks. Enabling Control Tower created an Identity Center user,
   `AWS Control Tower Admin`, holding administrative access to the Management account under the **root
   account's e-mail address** — the very collision D32 refuses for vended accounts, arrived at from the
   other side, and it surfaced only because an invitation e-mail landed in an inbox. Its twin finding is the
   opposite shape: the root user, which had done every step so far, **cannot use Account Factory at all**
   (documented), so a step written as "create the accounts through Account Factory" was not executable by
   the identity that was executing the stage. **The general form:** after enabling any service that
   provisions identity or federation, list the principals that now exist and ask of each one *which of this
   plan's personas is it* — the honest answer is often "none, and it is an administrator". And for any
   manual step, say **which identity performs it**, not only what it does; "whoever has the console" is not
   an identity, and the console the previous step accepted is not evidence about the next one. D33 settles
   both halves.
   **The expensive part is downstream, and it is what makes this worth a lesson of its own.** Stage 1a step
   3 described what Control Tower creates on the *account* axis — the Organization, Log Archive, Audit,
   CloudTrail, Config — and said nothing on the *identity* axis. So two later steps were written against a
   state that was never going to hold: 1b step 2 said "create the users and the groups" and 1b step 3 said
   "create permission sets: `AdministratorAccess`, …" **in a directory that already contains Control Tower's
   groups and a permission set named `AWSAdministratorAccess`** — four characters away, also granting
   administrator, and an assignment against the wrong one still works, so nothing would have reported it.
   A missing enumeration does not stay local: it becomes a wrong assumption in every step that reads the
   same resource later. **When a step ends with "X now exists", enumerate what X *contains*, on every axis,
   not only the one the step was about.**

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [plan/stages/INDEX.md](stages/INDEX.md)*
