# Lessons carried forward

**The one file here whose content is not recoverable from anywhere else.** These are findings from the
planning period that re-reading the plan will not give back. Add to this list only what would otherwise
be relearned the hard way.

Read it before planning, reviewing, or settling a decision. `CLAUDE.md` carries the titles so a
lesson can be *recognised* without opening this file; the reasoning that makes each one usable is here.

---

1. **A copy of governed data landing somewhere less governed is not a hole to be closed.** It is a
   property of every SageMaker installation, not something D18 introduced. The control is the data
   perimeter (`docs/plan/architecture.md` §4.2), which stops the copy leaving the organization; preventing the copy was never the
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
4. **State that lives only inside an `[E]` resource is this design's recurring failure mode** (`docs/plan/conventions.md` §5.1 rule
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
   `sa-east-1` — which the Region check done by reading had missed. `docs/PRICING.md` is built this way.
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
   written into `docs/plan/institutional-delta.md` as "what an institution would do, notational here" a few hours earlier, and that was
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
   1d's deliverable (Stage 1b's, when it was written) proposed `aws ram get-resource-share-associations` as the proof that organization-wide
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
18. **A policy never constrains the principal that authors it.** Lesson 11 says that changing *who authors*
   an IAM policy invalidates every claim made about that policy; this is the same fact from the other side,
   and it holds permanently rather than being triggered by a change. Every control in this design — the two
   approvers' denials, the derived zone's CMK, the OU policy sets, the permissions boundaries — is written by
   the infrastructure user and applied under its credentials. "Can a data scientist read the derived zone?"
   has an answer; the same question about the identity that owns the key policy does not, and it went unasked
   until someone read `docs/ORGANIZATION.md` and noticed that the persona with the thinnest description was the
   one holding administrator everywhere. **The general form:** for each control, name the principal that
   authors it, exclude that principal from the claim, and then ask what is *left* holding it. The answer is
   almost always detective — a log that principal cannot edit, an alarm on the membership that would grant
   the reach, an object lock its own administrator cannot lift — and the useful move is to enumerate those
   three rather than to attempt a preventive control that the author would simply rewrite. **The tell** is a
   separation-of-duties table whose rows are all *approvers*: the builder is missing from it not because it
   was cleared, but because the table was written about approval and the builder does not approve. The
   related tell, cheaper to spot: **the persona with the shortest section in the document is usually the one
   with the widest reach**, because reach that nobody had to argue for is reach nobody wrote down.
19. **A blocking input has to be re-checked against the requirement it actually serves, not against the
   mechanism that was chosen for it.** D15 needed *a certificate a client would trust*. The mechanism chosen
   was *a public domain*, and from then on the plan tracked the mechanism: "the domain name" sat for weeks as
   the one input needed from the user, blocking Stage 7, listed in `CLAUDE.md`, in `open-questions.md` and in
   two stage files. It survived because it was never re-derived — nobody asked again what the certificate was
   *for*, and the answer, once asked, was "three clients we build ourselves", which needs no public trust
   chain at all. The trigger that exposed it was unrelated: `CLAUDE.md` gained a line saying GitLab is
   intranet-only, and the mechanism's whole premise went with it. **The general form:** when a requirement is
   restated — especially when it is *narrowed* — walk the decisions downstream of it and ask which of them
   were solving the old, wider version. And there is a second half worth the same attention: deferring the
   mechanism turned out to *improve* the design rather than merely postpone it, because a public certificate
   publishes its names to Certificate Transparency logs. **A prerequisite that has quietly become optional is
   usually also carrying a cost nobody has priced**, since nothing was forcing anyone to look at it.

20. **When several policies deny the same call, only one of them is proven — the others are attached, not
   exercised.** Stage 1c step 7.6 parked all four per-OU documents on `Policy Test` at once and ran the
   battery there. Every probe was denied and every denial named a policy id in the API error itself, so the
   run looked complete. It was not: `awsds-org-scp-ou-interactive`'s two actions are also denied by the
   `Workloads` document and matched by the `Identity` document's `sagemaker:Create*`, and AWS names **one**
   matching policy — so that document decided nothing, and a document that never decides is a document whose
   condition, `Sid` and action spelling have never been evaluated. **The tell is cheap and worth looking for
   by name: a candidate that appears in *no* probe's attribution column.** The fix is not more probes but the
   right target — moved to `Interactive`, where nothing else denies `CreateNotebookInstance`, it was proven
   in one call. **The general form:** overlapping denies compose into a *result* that is indistinguishable
   from any one of them working, which is Lesson 13's shape moved from the verification into the policy set —
   and the same argument applies to a deny you inherit from the root while testing an OU-level candidate.
   **The other half, and it is the reason to keep doing it this way:** the composed run was still worth
   running, because the *must still succeed* half only gets stricter under composition, and the denial
   message naming the policy id is what let the gap be spotted at all rather than assumed away.
   **A second instance arrived at 7.7 and it is sharper than the first, because there the attribution
   answered a question nobody had asked.** `Sandboxes` was given its own enabled control, and the probe run
   in `awsds-infra-sandbox-1` came back denied — naming `Interactive`'s policy, not the new one. The
   question under test was *is this nested OU a registered target*, and what the probe measured was
   *coverage*, which inheritance had already guaranteed and which would have looked identical had the
   enablement silently failed. **A probe cannot distinguish a control you just added from a deny you
   already had**; the OU's attached-policy list is what answered it. Read the *configuration* when the
   question is about configuration, and keep probes for behaviour.

21. **"The service validates before authorizing" is a property of the *action*, not of the service — so a
   validation error on the first try is a reason to retry with a real id, not a result.** Stage 1c had
   already met the wall twice and generalised it one step too far: `ec2:ModifySnapshotAttribute` and
   `datazone:CreateDomain` both rejected invented inputs before authorization, so the amendment of 7.5a was
   written expecting the same of every EC2 and RDS probe. In one run, in one account, three different
   answers came back: `ec2:ExportImage` and `ec2:CreateInstanceExportTask` authorized against a **malformed**
   AMI id and returned the deny; `ec2:CreateStoreImageTask` rejected that same id shape and only reached
   authorization once a **real public AMI** was passed; `ec2:StartInstances` never reached it at any id
   length. `ec2:CreateFleet` had been predicted untestable for want of a launch template and was denied
   anyway, because `--dry-run` authorizes before resolving the template. **The cost of the wrong default is
   asymmetric and that is what makes this a lesson**: recording *untested* too early leaves a statement that
   is in fact exercised carried in the notes as unproven, and the next reader either re-tests it or, worse,
   trusts the note and treats a live control as a gap. **The general form:** a negative result from a probe
   is only a result once the probe has been given inputs that exist — the public AMI from SSM, a subnet from
   `describe-subnets`, the account's own id in an ARN — and "the API validates first" is a claim about one
   API call, to be re-established each time rather than inherited from the last one.

22. **A control whose principal the harness cannot produce is verified by *reading* the deployed document,
   not by attempting the call — and a green battery is silent about that whole class.** Stage 1c step 7.7
   enabled `AWS-GR_RESTRICT_ROOT_USER` on `Policy Test` without `ExemptAssumeRoot`, which denies
   `sts:AssumeRoot` into every account beneath it — 1a step 6's only member-account recovery path, since
   6.4 had established that no member account holds root credentials at all. The battery ran **61 of 61 as
   expected** in the same sitting and could not have found it: every principal this project can obtain is
   an Identity Center role, and the statement's condition is `ArnLike aws:PrincipalArn = arn:*:iam::*:root`,
   which no such role matches. The defect was found by reading `p-kve97k0o`. **The discriminator, to apply
   while *writing* a verification rather than after:** can this harness produce a principal that satisfies
   the condition? If not, the plan must state what to **read** and which string proves it, never what to
   attempt. Three statements in this project are already in that class — the root control
   (`aws:AssumedRoot`), the positive half of D27's catalog-maintenance carve-out (needs Stage 5's role to
   exist), and the positive half of the `aws:PrincipalIsAWSService` guard (needs a service principal) —
   and the counter-example proves the discriminator does work: decision 7's BPA carve-out names
   `InfrastructureAccess`, a principal that *does* exist, and was measured in both directions.
   **What makes this worse than Lesson 21 rather than a variant of it:** a probe given a bad id at least
   reports `UNTESTED`, which is visible. A probe that structurally cannot exist reports nothing at all, and
   nothing reads as *fine* — the absence is indistinguishable from the case being covered. So the battery
   needs a companion list of what it cannot see, which is why
   [`docs/plan/runbooks/scp-battery.md`](runbooks/scp-battery.md) now carries one. **The last half is a warning
   against relief:** the omission cost almost nothing only because of an unrelated earlier decision — with
   no root credentials anywhere, the unexempted control denied exactly and only the thing it was meant to
   exempt. That alignment was luck, not design, and will not repeat.
23. **When a managed service creates artifacts on your behalf, the container is its implementation detail —
   bind to contents, never to the id or to the job the artifact was created for.** Control Tower emits each
   enabled control as an ordinary SCP, which is what made verification (vii) readable at all. But its
   *packing* is per enablement and is not consistent: in one console session, on the same day, the two
   root-user controls were folded into the **original guardrail** document on `Policy Test`, `Workloads`
   and `Interactive`, and into the **`CT.MULTISERVICE.PV.1`** document on `Identity` (`p-fw2pctqw`) and
   `Data` (`p-pk85fvr1`). Nothing distinguished those two OUs; the same clicks produced two shapes. The
   damage is not to the controls — they all work — but to **every record that named a document by its
   job**: the log had those two ids written down as "the Region policy" for those OUs, and that sentence
   became half-false the moment a second control was enabled. **The general form:** an artifact created for
   you has an identity the service owns, may re-use, and may repack; its id, name and reason for existing
   are all outside your control, and only its *contents* are what you asserted. Read the `Sid` list.
   **The tell** is prose that refers to a managed document by the job it was created for rather than by
   what is in it — and the same caution applies to anything else a service names for you, from
   `AWSReservedSSO_*` role suffixes to service-linked roles.
24. **A harness authenticates through the mechanism it is measuring, so the one result it cannot report is
   a failure of that mechanism — and the defence built for the benign version of that failure is what
   hides the serious one.** On 2026-08-14 `awsds-org-rcp-perimeter` was attached to the root with an STS
   statement naming `sts:AssumeRoleWithSAML` and `sts:TagSession`. Those are the only two actions the
   trust policy of an `AWSReservedSSO_*` role permits, so the deny did not restrict a perimeter — it made
   every permission-set role in all six member accounts unreachable, from the CLI and the access portal
   alike. The battery contained **six probes written for exactly this** (`rcp floor: credentials still
   vend in …`), and not one of them could run: `ensure_session` tested credentials with a bare exit-code
   check and aborted the run as a *dead SSO session*, which is the hardening added after two mid-battery
   token expiries. The earlier lesson's fix produced this lesson's blindness, and it did so silently,
   because at the exit code an expired token and a denied sign-in are the same event. **The discriminator,
   to apply while writing a verification rather than after:** what does the harness itself need in order
   to report at all — credentials, a network path, a role — and can the change under test reach it? If it
   can, the verification cannot live inside that path. Here the outside instruments were the two that do
   not depend on it: **Management, which RCPs do not affect by construction**, and reading the trust
   policy of the role. **A second trap sits behind the first, and it is what makes a bad attach look
   fine:** a vended role credential lives four hours in `~/.aws/cli/cache`, so nothing fails at attach
   time — the probes run against a session minted before the policy existed and pass. Anything touching
   the sign-in path has to be tested against a *fresh* vend, which means invalidating that cache first.
   **Against Lesson 22**, which is its neighbour and not its twin: there the harness cannot *produce* the
   principal a control names, and the silence is a row that was never written; here the harness cannot
   *survive* the control, and the silence is an abort that confidently names the wrong cause — the worse
   of the two, because it comes with an explanation. The script now reads the error wording, stops only
   on an expiry, and records anything else as a floor breach with every probe behind it marked untested;
   the general form outlives this project, and applies to any test rig that signs in through the system
   it is testing.

25. **A borrowed session outlives the command that needed it, and every later error then describes the
   wrong account.** Stage 1d step 9 had to write past `CTS3PV8`, which exempts `AWSControlTowerExecution`
   alone, so the credentials were assumed from Management and exported into the shell. The write was not
   made in that sitting. In the next one, three commands ran as that role without anybody choosing it:
   `list-accounts` was denied — correctly, since it is a management-account API and the caller was now in
   Log Archive — and because the `&&` chain stopped there, the account variable stayed **empty** and the
   following command built `arn:aws:iam:::role/AWSControlTowerExecution`, producing a second
   `AccessDenied` about the role failing to assume *itself*. **Two authorization errors, neither of them
   an authorization problem, and both naming an account the operator had not selected.** The general form
   has two halves and they compound. First: **an exported credential is ambient state with no visible
   marker** — the prompt, the console tab and the CLI profile all still say what they said before, so the
   only instrument is `get-caller-identity`, and `unset` of the three variables is the *pair* of assuming
   them, not an optional tidy-up. Second: **a `&&` chain that carries an empty value forward converts a
   missing input into an authorization failure**, which is strictly worse than crashing, because the error
   text is plausible and sends the reader to the policy instead of to the variable. Resolution steps abort
   on empty; borrowed sessions are unset in the same block that used them. Against Lesson 24, its
   neighbour: there the harness could not survive the control it measured; here the operator could not
   *see* the identity they were using, and the wrong identity was one they had legitimately created.

   **The same blindness has a second entrance, and it is not duration but GRANULARITY** (2026-08-17,
   caught by the user in review before it cost anything, while preparing Stage 4 step 8.3's
   control-plane pair). Above, a credential *outlives* the command that needed it. Here the operator
   performs the switch and the switch does not happen: **the AWS CLI caches an SSO token under the
   `sso-session` NAME**, so profiles sharing a session share one identity, however many different
   people those profiles were written for. Switching `AWS_PROFILE` changes the account and the role
   being *requested* and changes nothing about *who is asking*. It does not vend the wrong credential
   — `sso:GetRoleCredentials` is refused, because the token's user holds no such assignment — but it is
   refused **by the portal at vending time**, which is a third failure mode dressed as the two the
   reading was built to tell apart (Lesson 13's shape, arriving through the harness rather than through
   the check). The rule that prevents it is one `sso-session` per **person**, which
   [`aws/AWS-CLI.md`](../../aws/AWS-CLI.md) already stated and which this drafted config had quietly
   broken by giving four different persona users one shared session. **The general form, and it is the
   reason this sits under 25 rather than beside it:** ambient identity is invisible in exactly the
   places that look authoritative — here the profile name, there the shell prompt — so the discriminator
   is the same in both, `get-caller-identity` and the assumed-role ARN it prints, read *before* the
   call that matters and not after it fails. **The corollary for anything shared by name:** ask what the
   cache is keyed on, not what the flag you typed is named.

26. **An "already exists" error is the cheapest authorization probe there is — and it proves nothing until
   an unprivileged principal has been shown to get a different one.** Stage 2 step 5.0 had to establish that
   the organization delegation reached its `Resource` list's **target** entries, and could not: the write it
   had already run, `UpdatePolicy`, authorizes against the *policy* ARN alone, and the stage's only other
   contact with attachments is an **import**, which calls nothing. The move was to attach a policy that was
   **already attached** — `DuplicatePolicyAttachmentException` if authorization passed, `AccessDenied` if it
   did not, and no possible mutation either way, because the end state is the state that already held. The
   general form: **any create/attach/put with an idempotency conflict can be aimed at an existing object and
   read as an authorization test**, which is how a preventive grant gets measured without exercising it for
   real. **The half that is easy to skip is the one that makes it a measurement.** The reading holds only if
   IAM authorization runs *before* the service's own conflict check, and that ordering is a property of the
   action, not of AWS (Lesson 21, from the other side) — if it were reversed, a principal with no permission
   at all would receive the same conflict, and the probe would return the same answer on success and failure
   (Lesson 13). So the probe is a **pair**: the call from the principal under test, and the same call from
   one known to hold nothing. Here the canary returned `AccessDeniedException`, which is what converted the
   two conflicts into evidence. **And the shape has a boundary worth recognising rather than working
   around:** an entry with no existing object to aim at — `account/…/*`, since nothing in this design is
   attached to an account — cannot be probed inertly at all, and stays a reading. That is the honest
   outcome, not a reason to create an object so the probe becomes available.

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
