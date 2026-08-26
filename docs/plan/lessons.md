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

   **AMENDED 2026-08-20 — the wording fork above is necessary and it is not sufficient, and the missing
   half is where to look rather than how to read.** The fix this lesson produced classifies by error
   text: expiry stops the run, anything else is recorded as a floor breach. Then a sitting arrived where
   `aws sso login` reported success and every `awsds-*` profile failed with
   `ForbiddenException … GetRoleCredentials … No access` — **the exact wording of 2026-08-14**, and this
   time nothing was wrong with the organization: the browser had silently re-approved a live portal
   session belonging to a *different* human, and the token cache is keyed by **sso-session name, never by
   user**, so the wrong identity's token had come to occupy the right identity's slot. One wording, two
   causes, and they demand opposite handling — record the most serious finding the harness can produce,
   or stop and record nothing. **Adding a second text rule would have repeated this lesson in reverse**:
   any pattern narrow enough to recognise the operator's mistake also matches the real breach, because
   the two produce the same sentence *by construction* — the ceiling denies the sign-in flow, and a
   sign-in flow with no assignment behind it is refused by the same call for the same reason shape.
   **So the discriminator cannot be a better reading of the answer; it has to be a different question,
   put to a system whose path does not traverse the mechanism under measurement.** Here that is Identity
   Center's own listing of what the token is assigned (`sso:ListAccountRoles` against the cached token):
   it never reaches STS, so no SCP and no RCP can shape it. Assigned but refused is the ceiling and the
   finding stands; not assigned is an operator's click and nothing about the estate. **The third state
   is the one that makes it safe to use** — "could not tell" must keep the finding, because a hidden
   breach costs an incident and a spurious one costs an investigation. Note the continuity with the
   parent lesson: its instruments were also chosen for being *outside* the path (Management, which RCPs
   cannot reach; the role's trust policy, which is a read of configuration rather than an exercise of
   it). The amendment only names the rule those choices were already following, and generalises it past
   sign-in: **whenever a negative result has more than one origin, the separating evidence must come from
   a channel the tested mechanism cannot influence.** A corollary worth carrying on its own: an
   operator-side mistake can present as an estate-wide finding, so before a harness writes down a breach
   in *every* account at once, it is worth asking what single local thing could produce that same
   uniformity.

   **WIDENED THE SAME DAY, by a second instance that arrived within the hour and did not fit the sentence
   above.** Pass 4e denied `athena:StartQueryExecution` and probed it. The refusal has exactly **one**
   origin — the SCP — so "more than one origin" does not describe it; what it has is **no attribution in
   its own text**: Athena answers with a bare *"You are not authorized to perform: … on the resource"*,
   naming no policy and no id. The battery's `classify()` has read wording since Stage 1c and files a
   policy-less `AccessDenied` as `DENY-NOT-SCP`, *"an IAM/permission-set deny, not the ceiling"* — sound
   reasoning, wrong here, and **unfixable by any pattern, because the service never emits the string the
   pattern would need.** Every probe written before this one happened to hit a service that names the
   document, so the assumption was invisible for eleven weeks. The remedy was the same one and it was
   reached faster for having been written down: attribution by a **contrast probe** — the same call, same
   principal type, same region, one session, from an account in an OU the amendment does not reach; it
   passed authorization, so the two refusals can only be the ceiling. **So the rule is not about
   ambiguity, it is about locus**: *when a result cannot be attributed from its own text — because the
   text is ambiguous OR because it is silent — the attribution must come from a channel the tested
   mechanism cannot influence.* Two consequences worth acting on. **A probe's expected wording is an
   assumption about the SERVICE, not about the control**, and it is worth stating when writing the probe,
   because it is the kind that holds for years and then does not. And **do not fix this by loosening the
   classifier**: teaching it to read a policy-less deny as the ceiling would misread every genuine IAM
   deny in the battery, so those two rows are left reporting `note` rather than `ok`, permanently and on
   purpose, with the contrast probe beside them carrying the meaning.

   **A THIRD OCCURRENCE (2026-08-22, Stage 6's trust defect) EXTENDED THE PROGRESSION ONE STEP: ambiguous
   text → silent text → ABSENT EVENT.** Both SMUS service-role trusts pinned the member account where the
   documented guard wants the domain account, so the service could never assume them — and the observation
   channel itself was empty: a cross-account service `AssumeRole` denial leaves **no CloudTrail event in
   the target account**. There was no wording to read, no exit code to misread, nothing. The outside
   channel that carried the attribution was the **documentation** — the published trust contract for
   `AmazonSageMakerProvisioning-<domainAccountId>` names `aws:SourceAccount = the domain account` — read
   against the deployed trust, Lesson 22's remedy arriving through Lesson 24's rule. The consequence worth
   acting on: **when the failing principal is another account's service, plan the attribution as a reading
   from the start**, because the trail on your side will structurally never carry the denial.

   **AMENDED 2026-08-23 — the same shape without a harness in it, and the instrument was a LOG.** Stage 6
   step 4.3's session found the SMUS notebook unable to resolve `files.pythonhosted.org` while
   `pythonhosted.org` answered. The Resolver query log was read for attribution and reported, for every
   failing name, `BLOCK` against **the queried name** with the catch-all list id — which reads, exactly
   and only, as *"that name is not on the allow-list"*. It was not: the name was on the list, and what
   the catch-all had matched was a **CNAME target one hop further down**, a name the log never prints. The
   log also populates no `firewall_rule_action` on an ALLOW, so the allowed names looked un-evaluated
   too — two ambiguities in one field, pointing the same wrong way. **A correct hypothesis was abandoned
   on the strength of that reading**, which is this lesson's cost measured on its own terms. The
   discriminator was again not a better reading but a different question: a **paired probe under an
   identical rule shape**, run from a second host in the same VPC — `blobs.duckdb.org` (A records) against
   `index.crates.io` (CNAME to a CDN), both under a wildcard of the same depth. Same rule, opposite
   outcomes, one variable. **The general form for any log: a field naming the object you asked about is
   not evidence about the object that matched**, and when a system resolves through a chain, indirection,
   or redirect, the log will name the entry point every time.

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

27. **A declarative plan is silent about the values the provider owns — so the setting that has to be
   right *before anything else exists* is precisely the one Terraform will not promise.** Stage 5 step
   5.2 rests entirely on D13: the lake's databases must be **born** without the `IAM_ALLOWED_PRINCIPALS`
   default grants, because those act at creation time and clearing them afterwards does not reach a
   database that already exists. That obligation is an *emptying*, and
   `aws_lakeformation_data_lake_settings` offers no way to write it. Three forms were tried against the
   pinned provider and none of them states it: omitting both blocks plans as **`after_unknown: true`**,
   which is Terraform declaring *no intention*; `create_database_default_permissions = []` is refused,
   because they are blocks and not arguments; a `{}` block would declare **one** entry with computed
   fields, which is not zero. So the security property the stage exists to establish could not be
   expressed at all, and the plan rendered **identically** in the case where the apply would clear the
   defaults and the case where it would leave them standing. **That is Lesson 13's shape moved into the
   plan itself** — the artifact you read *before* acting cannot distinguish the two outcomes, which is
   worse than a verification that cannot, because the plan is what authorises the apply.
   **The discriminator is one command on a plan you already have**, and the obvious route does not work:
   `terraform providers schema -json` marks `computed` on attributes and **never on `block_types`**, so
   the schema cannot answer it for blocks. The plan can:

   ```bash
   terraform show -json <plan>.tfplan | jq '.resource_changes[] | select(.address=="<addr>") | .change.after_unknown'
   ```

   Anything coming back `true` is decided by the **provider**, not by your configuration. Ask it on a
   create-or-update plan — on a `no-op` everything is known from state and the answer is `{}`. If the
   cleared state of one of those is load-bearing, the apply must be **split so the result can be read
   before anything depends on it**, which is why [Recipe D](runbooks/terraform-changes.md) now exists.
   **The class is recognisable in advance, and that is the half worth carrying.** The exposed resources
   are the **account-level settings singletons** — the ones that create nothing and overwrite
   server-side state that AWS, not you, initialised: `aws_lakeformation_data_lake_settings` here, and by
   the same shape `aws_s3_account_public_access_block`, `aws_ebs_encryption_by_default`, and most things
   named `*_default_*`. They have no create, only a put, so whatever you omit either keeps what was
   there before you existed or does not, and only the provider's implementation says which.
   **And the good outcome is a measurement of one provider version, not a property of Terraform.**
   Omission turned out to clear (`DbDefaults: []`, then verified per database: no `IAMAllowedPrincipals`
   grant anywhere). That was obtained by looking, the plan still does not state it, and the next
   provider version can change it in silence with nothing failing — so the read-back is kept rather than
   the split being collapsed. **Against Lesson 5**, its nearest neighbour: there a property was written
   down and no policy line enforced it; here the property could not be *written down at all*, and the
   tell is different — not a stated intention missing its enforcing line, but a `plan` that renders the
   same text whether the intention will hold or not.

28. **When a service keeps its own permission layer above IAM, a principal's reach is the *intersection* —
   and this repository's layout puts the two halves in different slices, so a slice is never the unit that
   answers "what can this persona do".** Stage 5 pass 2 made the governance manager's first grants, and the
   reading that preceded them is the lesson. `identity/sso/policies-approvers.tf` carries a statement called
   `AdministerLakeFormation` — `AddLFTagsToResource`, `GrantPermissions`, `CreateLFTag` — which reads like
   the complete answer to what the persona may do, and **on its own it grants nothing**. Lake Formation
   authorizes separately: the IAM action permits the API **call**, an LF permission (`ASSOCIATE` on the tag)
   decides whether the call **succeeds**. The two live in different accounts, different slices and different
   stages, while the natural unit to open is a slice.
   **What makes it expensive rather than merely true is the shape of the failure.** Before pass 2 landed
   that file read exactly as it reads now, and the persona could not tag a single dataset — and with Lake
   Formation enforcing, a missing grant makes `glue:GetDatabases` return an **empty list**, not an error. So
   the wrong conclusion is drawn from a file that is *accurate*, and the symptom is an absence: Lesson 13's
   shape arriving through a service's own result-filtering rather than through a check somebody wrote.
   **The reverse direction is worse, because it has no symptom at all** — revoke the LF grant and the IAM
   policy still describes the capability, leaving a confident statement that nothing in the repository
   contradicts.
   **The general form:** Lake Formation over IAM is one instance; a KMS key policy, an S3 bucket policy, a
   Glue or RAM resource policy are the same shape. Any claim about what a principal can do **names both
   halves or is not a claim**. The discriminator, to apply while writing rather than while debugging: for
   each capability, can you point at the two grants? If you can point at one, the other exists somewhere
   and you have not read it. **Against Lesson 20**, its nearest neighbour: there several policies deny the
   same call and only one is proven — redundancy making a *result* ambiguous; here the two grants are each
   **necessary**, and reading one makes an *absence* invisible. The mitigation shipped with the lesson: a
   comment at each end pointing at the other ([`policies-approvers.tf`](../../terraform-live/identity/sso/policies-approvers.tf),
   [`data/README.md`](../../terraform-live/data-governance/data/README.md) §"A permission here is the
   intersection of two systems").
   **AMENDED 2026-08-19 (Stage 5 pass 4c), because the lesson was stated, listed "an S3 bucket policy"
   in its general form — and still did not fire.** The intersection has a **second trigger, which is not
   a service at all: the account boundary.** Cross-account access requires an allow in the resource
   policy of the account that owns the object **and** an allow in the identity policy of the account that
   owns the principal. No second permission layer is involved; it is one IAM, whose evaluation rule
   changes from OR to AND at the boundary. That is why the first trigger did not recognise it: S3 has no
   layer above IAM, so the case does not look like Lake Formation, and **same-account intuition is
   actively wrong here** — within one account a bucket policy naming a role *is* sufficient, which is the
   form everybody has read a hundred times.
   **What it cost:** the drop-box `PutObject` had lived since pass 1 with only its resource half — three
   correct statements naming the persona roles — and the stage file recorded in writing that the missing
   identity half was *"correct rather than missing"*. The reading behind that sentence was accurate; the
   inference was not. The failure would have surfaced at the first attempt as an `AccessDenied` **whose
   error names the half that is right**, which is why this direction is expensive rather than merely
   wrong.
   **The discriminator, added to the one above:** before claiming any permission works, ask *whose
   account owns the object, and whose owns the principal* — and if the answer is two accounts, the
   question "can you point at both grants?" is not optional advice, it is the evaluation rule. The
   converse is the useful half in review: a resource policy that names a **foreign** principal is by
   itself always incomplete, in every service, with no exception — so it can be read as a marker that an
   identity-side statement exists somewhere or the permission is dead.
   **AMENDED AGAIN 2026-08-20 (Stage 5 pass 4d, when the drop-box `PutObject` finally ran), because
   "the two halves" is the wrong arity on an encrypted write path: there are THREE.** The write
   succeeded only because the identity half (`WriteIngestionDropBox`), the resource half
   (`AllowInteractiveWriterPutOnly`) **and the lake CMK's key policy** meeting `UseLakeDataKeyViaS3` all
   agreed at once — three policies in two accounts, one call. The third term is not an exotic case: it is
   present on **every** write to a bucket with SSE-KMS default encryption, because S3 calls
   `kms:GenerateDataKey` with the **caller's** credentials, not its own.
   **What makes this amendment worth its own paragraph is where the term is legible.** The first two
   halves announce themselves on failure — the `AccessDenied` names the action and the resource, and the
   wording says which layer refused. The key term does not: a missing KMS grant surfaces as a **KMS**
   error about an action nobody wrote in the policy they are debugging, which is exactly the shape the
   Athena `INSERT` failure took the day before (Lesson 34's finding arrived wearing this costume). And on
   **success** the key term is the only one that is visible at all — the `PutObject` response echoes
   `SSEKMSKeyId`, naming the key and its owning account, while nothing in the response mentions the
   bucket policy or the identity policy that also had to allow it.
   **The discriminator, third and last:** after asking *which service has a layer above IAM* and *whose
   account owns the object*, ask **is the target encrypted, and with whose key** — and if the key lives
   in another account, that is a third grant on the same call. The review habit that follows: a
   successful encrypted write is worth reading for its `SSEKMSKeyId` rather than for its exit code,
   because that field is a **positive** proof of a grant that no failure elsewhere would have attributed
   correctly.

29. **An attribute assigned to describe a thing becomes a selector the moment somebody writes a rule over
   it — and the rule inherits every resource that wears the attribute for an unrelated reason.** Stage 5
   pass 3 was one expression away from sharing the drop-box. The classification ontology gives
   `classification=internal` to the drop-box database for a considered reason: arrivals are user-supplied,
   the fail-open default says an unclassified arrival is ordinary working data rather than invisible. The
   default consumer share was then written as `classification ∈ {public, internal}` — a *sensitivity*
   predicate — and sensitivity is not the question a share asks. The question a share asks is **may people
   read this**, and the drop-box's answer is no in the strongest terms the design has: it is the letterbox
   whose whole contract is *write, never read back*. Two correct decisions, one accidental intersection.
   **What makes this more than a slip is where it was caught**: not in review, but at the apply, by reading
   the expression against the catalog **as actually tagged** rather than against the model. A tag ontology
   read as prose looks like a taxonomy; read as a selector it is a set of `WHERE` clauses, and a value
   chosen for meaning A silently qualifies for rule B. **The discriminator, before writing any grant, SCP
   condition, ABAC rule or bucket-policy tag match:** enumerate what *currently* carries each value and ask
   whether every one of them belongs in the result — the model will not tell you, only the inventory will.
   **And the gate belongs on the axis that expresses the intent**: the fix was not to re-tag the drop-box
   but to add the dimension the rule was really about (`layer`), leaving each attribute saying the one
   thing it was chosen to say. **The near-miss also shows how not to reason about it**: the rows would not
   in fact have leaked, because a second control (the unregistered location) blocks the read — and that is
   exactly the argument to distrust. Lesson 5's neighbour, in reverse: an unintended *grant* is a defect
   whether or not a later control happens to cover it, because nobody chose the coverage.

30. **A tool's failure is not a property of the world — and if it gets written down as one, the record
   carries the tool's limit forever.** Stage 5 pass 2 could not fetch AWS's Lake Formation pages: they are
   JavaScript-rendered and the plain fetcher returned no body. The handling was right in every visible way
   — the missing information was *not* asserted from memory, the gap was recorded, the question was
   deferred to the stage that could measure it. But the caveat that went into `REFERENCES.md` said the
   pages "did not return a body to an automated fetch", which reads as *these pages cannot be read*, and
   the true statement was *this fetcher cannot read these pages*. One session later a rendering browser
   opened all of them in a minute, and the question that had been deliberately left open — whether the
   governance-manager persona can *grant* as well as tag — was answered by a sentence sitting in a page
   nobody had failed to read, only failed to try. **The discriminator: before recording an unknown, name
   the instrument that failed and ask what a different instrument would see.** An unread source is a gap in
   *the record*, not a fact about the source, and the two get filed identically unless you separate them on
   purpose. **The generalisation this project should keep**: the same shape sits behind an `aws` call that
   fails on the wrong profile, a plan that "cannot express" something the API supports, and a check that
   returns empty — each says something about the reach of the instrument first, and the world second.

   **A SECOND OCCURRENCE (2026-08-22) MOVED THE LIMIT INSIDE THE API'S OWN CONTRACT.** `US-8` read
   permission boundaries through `iam list-roles` — and `ListRoles` **omits `PermissionsBoundary` by
   documented contract** (`GetRole`-only, along with `Tags` and `RoleLastUsed`), so the reading was a
   constant `null` for every role that had one. The check reported the world's first real project role as
   unbounded while `get-role` showed the boundary in place. Two sharpenings: **reading everything the
   response returned is not enough — the field contract itself has to be read**, because the drop happens
   at the API's end, not in the collection code (Lesson 31's "what did the collection drop?" asked one
   layer deeper); and the defect survived from birth because **no object existed that could falsify the
   check** — its first exercise with a real role was what exposed it, which is Lesson 13's shape stretched
   over time.

31. **A check inherits the scope of the account it was written in, and keeps reporting `pass` about that
   one while the design spreads past it.** `DL-6` decides whether Lake Formation's create-defaults still
   grant `IAM_ALLOWED_PRINCIPALS` — the reading D13 rests on. It was written at Stage 5 pass 1, when Data
   Governance was the only account with a `DataLakeSettings`, so it read `DATA_PROFILE`. By pass 4 two more
   accounts had one, both in the failing state, and the check was **green**. Nothing was broken: it
   answered its question correctly, about a population that had stopped being the whole population.
   **This is not Lesson 13** — that one is a check whose output cannot tell success from failure. This one
   discriminates perfectly and is pointed at the wrong set, which is worse in one specific way: Lesson 13's
   failure looks empty and invites suspicion, while this one looks like evidence. **The discriminator, and
   it is cheap: a check's scope is part of its claim, so write the scope into the line it prints** —
   `DL-6 (awsds-infra-dev)` is a sentence you can falsify by counting accounts, `DL-6` is not.
   **And the trigger to re-read every check is not a code change but a *topology* change**: the day a
   second account gains a resource that only one had, every instrument that reads that resource is scoped
   until proven otherwise. Pass 3 saw this coming and wrote the debt down; the debt still shipped one
   session of a green check over two failing accounts, which is the argument for extending the instrument
   **in the same sitting** as the resource rather than in the one that notices.

   **THE SAME MECHANISM ALSO ARRIVES AS A FALSE `FAIL`, AND THAT IS THE SECOND OCCURRENCE (2026-08-21,
   Stage 6 step 1.3).** `US-2` asks whether a DataZone domain exists outside Data Governance. It counted
   the rows `datazone list-domains` returned in each account and treated any non-zero as *"a domain was
   created here"* — true in a world where nothing is shared, which was the world it was written in. The
   account association shares one domain **into** the member accounts, so on the day the association
   succeeded the check went red in both, about a domain that had never moved. **A topology change again,
   and the same lesson at the opposite sign.**
   **Two things generalise from the second occurrence that the first does not give you.** The **tell** is
   different and cheaper than counting accounts: *the failure arrived from the act that was supposed to
   work*. A check that goes red at the exact moment a step succeeds is making a claim about the world
   before it is making a claim about the estate — audit the check first, and only then the estate.
   And the **fix** is not scope, it is a discarded field: the collection built `(id, name, version,
   status)` and **threw away the ARN**, the one attribute carrying the owner. **A check that infers a
   property it could have read is the shape to look for** — here, inferring ownership from *who is
   asking* instead of reading it from what the API returned. Ask of any list-shaped check: what did the
   collection drop, and does the verdict depend on it?

32. **Two spellings of the same object survive indefinitely while nothing has to build it — and the side
   that has to build it is the one that was right.** For weeks the plan said both "scratch + derived-zone
   **buckets**" (`architecture.md`, `conventions.md` §6, the Stage 5 table) and "scratch and derived
   **prefixes**" (D13, `identity/sso/`'s owed-grants note, Stage 1b, the permission set's own description).
   Both entered in the same commit, so it was never drift — it was one object with two vocabularies, and
   neither spelling failed anything, because no code had yet been written that would have to pick. The
   disagreement surfaced only at the authoring, as a cost question: a second bucket needs either a third
   CMK the cost model does not carry or a key shared for no reason. **The tie-break that worked: follow the
   citation.** All three "bucket" lines credited **D19**, which never mentions `scratch`; the origin is
   **D13** — *"non-registered prefixes (scratch, artifacts, model outputs) keep ordinary IAM access"* —
   where `scratch` names a *class* of thing, beside `artifacts` and `model outputs`, and not a resource.
   **The generalisation: when two files disagree about what something is, the one closer to the mechanism
   wins** — the IAM side had to name a resource in a policy, the topology side only had to draw a box, and
   a box costs nothing to draw wrong. **And the cheap check is the citation itself**: a claim that cites a
   decision which does not contain it is the copy, not the original.

33. **One intent enforced in two places diverges — and sharing the *values* while duplicating the
   *structure* is what makes it look like it cannot.** "Reachable only over the VPN" is written twice in
   this estate: `DenyOutsideTrustedNetworks` in the lake's bucket policy, and `DenyControlPlaneOffVpn` in
   the six persona permission sets. The resource half carries **three** branches — `aws:SourceVpce`,
   `aws:SourceIp`, `aws:PrincipalAccount` — because traffic can arrive by more than one path. The identity
   half carries **one**, `aws:SourceIp`. Stage 5 pass 4d measured the difference: tunnel traffic to S3
   leaves through the `[P]` gateway endpoint and arrives carrying the WireGuard host's *private* address
   (`10.20.160.254`) and an endpoint id, while Glue and Athena leave by the internet gateway wearing the
   Elastic IP — so the identity half denies **every direct S3 call a persona makes from inside the
   perimeter**, including fetching the person's own query result. The resource half was written against the
   measured topology; the identity half against the intended one.
   **The trap is not duplication — it is *partial* de-duplication.** Both halves read the Elastic IP from
   the same `[P]` state and neither pastes it, so the design *looks* like it has one source of truth. It
   has one source for the **values** and two hand-written copies of the **branch structure**, and the
   structure is where the two disagree. Nothing compares them: `terraform plan` sees two unrelated
   documents, and each half is individually plausible on reading. **The discriminator: when one sentence is
   enforced at two layers, ask whether the *shape* is derived or retyped — a shared variable inside two
   hand-written conditions is the most convincing possible disguise for a divergence.**
   **And the reason it survived is worth as much as the finding.** A deny is only debugged by the traffic
   it *wrongly* blocks. The bucket policy sits on the hot path, so an over-broad branch there breaks a
   legitimate read on day one and gets fixed; the identity deny fires only when someone is off-VPN, which
   is a case nobody exercises deliberately — so it accumulated a defect that no apply, no review and no
   plan could surface, and only a behavioural proof from a real session found it. **A control that is
   correct in the common case and wrong in the rare one reports as healthy for exactly as long as nobody
   tries the rare one.**
   **Two smaller shapes fell out of the same finding, both worth recognising.** First, a guard can foresee
   the right *symptom* for the wrong *cause* and give false comfort: `permission-sets.tf` already carried a
   `precondition` whose error message predicts "deny every call from every network for all six personas",
   written against the address list arriving **malformed** — nothing in it considers a well-formed list
   whose key is simply irrelevant on the path the traffic takes. Second, the *proposed fix* was itself
   aimed at the wrong list — the consumers' endpoints rather than the **VPN home's** — because
   `consumer_vpce_ids` is built along "who consumes the lake" and was being asked "what is on the network
   path"; today the two intersect by coincidence, since the single VPN home also happens to be a consumer
   (Lesson 10's axis question and Lesson 29's *describe-becomes-select*, arriving together).
   **CLOSED 2026-08-20 — the fix is applied and *proven*, and the proof shape is the reusable part.** The
   third condition (`StringNotEqualsIfExists aws:SourceVpce` over the VPN home's gateway endpoints) went
   in, and the evidence was taken three ways rather than one. **(a) The same call, before and after:**
   `s3api list-buckets` — the call whose CloudTrail record diagnosed the defect — moved from *explicit
   deny in an identity-based policy* to the **implicit** deny, one variable changed. **(b) A contrast
   pair:** one action (`GetBucketLocation`), two buckets, one session — granted bucket succeeds, lake
   bucket implicit-denies — which is what distinguishes *"the network is blocked"* from *"this bucket is
   not granted"*, two hypotheses that had produced identical output while the over-broad deny sat on top.
   **(c) Both provisioned roles, not the document:** the defect belonged to a shared fragment, so the fix
   is only proven where the fragment lands, and the two accounts that failed identically are the two that
   had to be read back.
   **The lesson's own tail:** a deny that is debugged only by the traffic it wrongly blocks is also
   *closed* only that way — the apply proves the document changed, and nothing more. **The bracket that
   opens with "a control reports healthy until someone tries the rare case" closes by someone trying the
   rare case**, which means the fix and its behavioural proof belong in the same sitting or the finding is
   merely relocated. A second consequence, cheap and general: while an unrelated **explicit** deny is in
   the path, every **implicit** deny behind it is unmeasurable — so a fix like this one does not just
   restore access, it restores the *evidentiary* value of every negative control downstream of it (here,
   D13's whole mechanism).

34. **A deferred obligation recorded only at the deferring end is a promise the receiving stage never
   gets — and a decision scheduled around an unexercised capability inherits a premise nobody measured.**
   The lake's registration role shipped read-only at Stage 5 pass 1, its comment deferring the write
   half to "Stage 9, which amends this policy (its step 2)" — and **Stage 9's file never carried that
   amendment**. The promise lived only where it was made; the stage that was supposed to redeem it had
   never heard of it. Meanwhile Stage 5's own file scheduled a one-way-door decision — *load sample rows
   through Athena before 4.3's amendment closes that door* — on the belief that the in-account write
   path was open. Three files, three spellings of one capability: the plan said *open*, the code said
   *deferred*, the receiving stage said *nothing* — and every one of them survived because **nothing had
   ever exercised the path**. This is Lesson 20's mirror: an unexercised *allow-path* is exactly as
   unmeasured as an unexercised deny, and it fails the first time someone needs it rather than the first
   time someone attacks it. The first governed write ever attempted (2026-08-19) measured all three
   files at once — DENIED, the vended session naming `kms:GenerateDataKey` — and the mechanism side was
   the true one, again (Lesson 32). The user's against-recommendation choice to load rows is what
   surfaced it in the cheapest possible configuration — one account, one role, one key — instead of
   inside Stage 9's cross-account job, where the share, the job role and two keys would all have been on
   the suspect list. **Two discriminators.** When a comment defers work to a later stage, open that
   stage's file and write the obligation there *in the same sitting* — an obligation recorded at one end
   is Lesson 4's state-only-in-one-place, for plans; the cheap check is Lesson 32's citation test run in
   reverse, *follow the promise to its addressee*. And before scheduling anything "before the door
   closes", **try the door**: as posed, both options of the sample-row decision described a door that
   was not there, so whichever the user picked, the decision was argued from a premise the first
   attempt destroyed.

35. **Adopting an object into infrastructure-as-code silently invalidates every *procedure* written about
   it — and the adoption touches none of the files that carry those procedures.** Stage 2 step 5.5
   imported the ten Organizations policy documents into Terraform. Nothing about that commit reached
   `POLICIES.md` or the battery runbook, because adoption changes code and state, not prose *about* the
   object — so both files went on saying, correctly for the world they were written in, that an amendment
   is `update-policy` in place. Four days before pass 4e, that instruction was copied out of them into a
   stage file as the plan for the next act, and it was wrong by a whole stage. **Against Lesson 11, which
   is the neighbour**: there a change of authorship invalidates *claims* — sentences that were true
   because we wrote the thing — and the remedy is to re-read the decisions whose enforcement depends on
   it. Here it invalidates *instructions*, and the remedy is different in kind: **on any adoption into
   IaC, grep every prose file for a mutating command naming that object, and correct it in the adoption's
   own sitting.** A procedure has no revision trigger and no gate; `check-index.py` reads the documents'
   `Sid`s and would not have noticed, and neither would a plan.

   **What makes this one worth its own number rather than a line under 11 is the failure shape, not the
   subject.** A stale procedure that *errors* is self-correcting — you find out immediately and go read.
   This one **succeeds**: `update-policy` would have returned cleanly, the document would have attached,
   every gate in the repository would have stayed green. The damage was one layer down and silent — the
   tracked JSONs carry `<PLACEHOLDER>` tokens substituted at render time, and `awsds-org-scp-ou-data.json`
   carries `<ACCOUNT_ID_DATA>` *inside the D27 crawler carve-out*, so the hand-uploaded document would
   have held an `ArnNotEquals` comparing against the literal string `<ACCOUNT_ID_DATA>`: a carve-out
   matching no principal, no error at upload, none at evaluation, and a control that has quietly become
   decoration (Lesson 5, arrived at by accident instead of by argument). Two guards exist against exactly
   that — `render.py`'s survivor check and `policies.tf`'s precondition — and **the abandoned path is
   precisely the one that uses neither**, which is the general danger: the guards were built into the
   sanctioned route, so leaving the route leaves the guards, and nothing announces that you have. **The
   discriminator to apply while reading any procedure: does it name a command that mutates a real object,
   and is that object still changed the way this text says?** If the text predates the tree that now owns
   the object, assume it is stale until checked.

36. **"Auto-enable" is a word each service defines for itself — and a cross-service finding written down
    in the stage that hit it stays in that stage.**

    *Found 2026-08-20, checking Stage 5 step 13 against the service before running it — the third time
    this plan has made the same assumption about a different service, and the second time it had already
    been corrected in writing.*

    Three security services in this plan share a management **shape**: delegate administration to Audit,
    then turn the thing on for the whole organization. The shape is real. The semantics underneath it are
    not shared at all, and this project has now measured three different answers:

    | Service | What "auto-enable" actually covers | Where it was learned |
    |---|---|---|
    | GuardDuty | `ALL` — existing accounts included | Stage 4, recorded; Stage 15 step 2 inherits it |
    | Macie | **new accounts only**; existing ones added one at a time by the administrator | Stage 11, corrected 2026-08-17 |
    | Security Hub CSPM | **new accounts only, current Region only** — so on an organization whose accounts all already exist, it covers **none of them** | Stage 5 step 13, corrected 2026-08-20 |

    The plan wrote *"auto-enable for existing and future accounts"* into Stage 5 because the surrounding
    shape was familiar from GuardDuty. Familiarity is exactly the mechanism: nothing about the sentence
    looked like a guess, because the sentence next door had been true.

    **The part worth more than the table: the repair was not a different setting.** For Macie the fix was
    "then add the existing accounts too" — same feature, more work. For Security Hub the fix is an
    entirely different feature: **central configuration**, with its own prerequisite (a home Region /
    finding aggregator), its own API family, its own console workflow, its own drift semantics, and an
    account-level API surface that is *refused* for accounts a policy governs. So when a mechanism
    assumption turns out to be wrong, do not budget for a corrected parameter — **budget for the
    possibility that the thing the plan described does not exist**, and that what replaces it changes who
    runs the act, from where, and what else must be true first.

    **And the second half, which is about this repository rather than about AWS.** The Macie instance was
    found, understood and written down — correctly, and dated — in **Stage 11's Status row**. That is
    where it was discovered, so that is where it went. Stage 5's step 13 then carried the same wrong
    assumption for three more days, because nothing routes a reader from "I am executing Stage 5" to "a
    sibling stage learned something about the *class* of service you are about to configure". `CLAUDE.md`'s
    routing table sends you to **the stage you are executing** and to the decisions it consumes; it cannot
    send you to a paragraph in a stage you are not reading. **A finding about the stage's own subject
    belongs in the stage. A finding about a *class* of thing — a service family, a provider behaviour, a
    console pattern — belongs somewhere cross-cutting**, here or in `docs/AWS_STATE.md`'s expectations,
    *and* in the stage. Duplicating it is not the waste; the waste is the third stage rediscovering it.

    **The discriminator, while writing any correction down:** ask whether the sentence you just wrote
    would be useful to someone configuring a *different service*. If yes, the stage file is the wrong
    only-home for it.
37. **A sentence written in the perfect tense from an intention is, from that moment on, indistinguishable
    from a record — and all three of this project's have been authored in the commit that was about to
    make the reading available.**

    *Promoted to a lesson 2026-08-21, on the third occurrence, by the trigger the second one declared
    ("two instances is a pattern but not yet a lesson; a third in a different shape makes it one").*

    | # | The sentence | Written | Falsified | By what |
    |---|---|---|---|---|
    | 1 | a `CLAUDE.md` bullet describing the VPN host's state | Stage 4 | same day | reading the host |
    | 2 | *"step 0 is now runnable"*, Stage 6's Status row, commit `5df5a83` | 2026-08-21 | hours later | running step 0 |
    | 3 | *"**Pulled forward and applied before this stage:** `production/registry/` … and `production/pki/`"* | 2026-08-16 | **five days and two full stage reviews later** | auditing the prerequisite before executing it |

    **All three were written by the same hand, in the same motion, and none of them was a lie**: each was
    a true statement of what was about to be done, typed into a document, and then the doing either did
    not happen or came back with a different answer. The commit that carries the sentence is systematically
    the commit *before* the evidence exists. That is the shape to recognise — not carelessness, but the
    ordinary sequence of writing the plan and then going to execute it.

    **The third is the expensive one, and what made it survive is worth more than what made it wrong.**
    A prerequisite in another account, owned by a stage that had not started, asserted once in one
    Prerequisites row. Nothing could catch it: `check-plan-refs.py` validates identifiers, links and
    sizes; `slices.py` validates the declared slice table against the tree and would not look for a folder
    nobody declared; `./aws/studio.py` never asks; `./aws/supplychain.py` reads ECR and the CA but gates
    its whole note→fail flip on a host two stages away, so it reports green over the absence. **A false
    claim about state degrades gracefully: reading it produces no error, only the belief that something
    was done.** Its only symptom was that the *other* files disagreed — the owning stage said "runs
    before Stage 6" in the future tense, a `.tf` comment scheduled the slice at Stage 7, and the decision's
    own navigation row never listed Stage 6 at all. Four statements, three tenses, no gate between them.

    **The tell, and it is cheap enough to use every time.** This repository dates and grades its claims —
    *SATISFIED 2026-08-19*, *4d AND 4e are DELIVERED (2026-08-20)*, *measured*, *0 FAILED*. So the question
    to ask of any perfect-tense clause is not "is this true?", which invites a re-derivation, but: **why
    does this one clause carry no date, no measurement and no delivery verdict, when the clauses beside it
    in the same row carry all three?** In case 3 that asymmetry was visible from the day it was written.

    **Two practices, both nearly free:**

    - **Write intentions in the future tense and let the past tense be earned by a reading.** *"runs
      before Stage 6"* and *"applied 2026-08-16, measured"* are both fine; *"applied before this stage"*
      with no date is the form that cannot be told apart from either.
    - **Where prose cannot be checked, move the obligation into a structure that can.** The repair here
      was not better wording: it was a row in the pass table, a row in the build table, a sentence in the
      ordering paragraph, and a `layers.py` rank — four places an executor actually reads, against one
      row nobody executes from. **Prose is where an intention and a reading part company**, so the fix is
      to stop asking prose to carry a dependency at all.

    **The scope test, so this does not become paranoia about every past-tense verb:** the risk is
    concentrated in claims about work **outside the file's own stage or account**, because those are
    exactly the claims no gate reads and no owner re-reads. A stage saying what it itself did is checked
    by the next person executing it; a stage saying what *another* stage already did is checked by nobody.

38. **An identifier read out of prose is a claim, not a reading — and it travels further than the sentence
   that carried it.** Stage 6 step 1.3's table named the RAM permission the account association would
   attach: `AWSRAMPermissionDataZoneDefault`, *"never `AWSRAMPermissionDataZonePortalReadWrite`"*. Both
   names came from a documentation page's body text, read carefully and quoted accurately. **Neither
   exists.** `ram list-permissions --resource-type datazone:Domain` publishes six permissions and no name
   resembling either; what the console attaches is
   `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`. The *decision* the sentence expressed —
   no data-portal access — was right, available, and taken. Only the proper nouns were fiction.
   **The damage is not the wrong name, it is where the wrong name ends up.** By the time this was
   measured, `AWSRAMPermissionDataZoneDefault` had reached `docs/SMUS.md` twice and — worse — a comment in
   `terraform-modules/sagemaker-prereqs/blueprints.tf`, where it was doing real work: it was the stated
   *reason* the blueprint resources live in the member account's slice. A name is the most portable thing
   in a document. It gets quoted without its hedge, it survives every re-read because it looks like a
   fact rather than an inference, and it ends up load-bearing in a file nobody would think to re-check
   against an API.
   **This is not Lesson 16, and not Lesson 23.** Lesson 16 is about a console wizard being under-specified
   — fields the documentation does not name. This is the opposite: the documentation named something
   confidently and the API disagrees. Lesson 23 says bind to *contents* rather than to a name, which is
   about drift over time; this name never had a referent at all.
   **The discriminator is mechanical and costs one command.** Every class of identifier this project
   quotes has a cheap enumeration behind it — `ram list-permissions`, `aws iam list-policies --scope AWS`,
   a service's `list_*.html` action table, a registry's tag list. **If a plan sentence names an
   AWS-published identifier, enumerate the namespace before the sentence is written**, and if the name
   cannot be enumerated yet, say *"the console's no-portal option, name unread"* rather than inventing
   the precision. **The tell in review**: a proper noun with no measurement date beside it, in a file
   whose neighbours all carry one — the same shape Lesson 37 describes for verbs, applied to nouns.

   **AMENDED 2026-08-23 — the more dangerous variant is a MECHANISM read out of prose and written down as
   a measurement.** While extending the DNS Firewall allow-list on 2026-08-22, the question *does
   `*.name` reach a nested subdomain* was settled from a documentation summary and then recorded — in a
   module comment, a stage step, `REFERENCES.md` and a log entry — with the words *"measured rather than
   assumed"*. The claim happened to be **true**, which is what made it costly: it read as a closed
   question, so the next reader had no reason to ask what else governs a match, and the thing that
   actually governed it (the whole resolution chain is evaluated, so a listed name whose CNAME target is
   unlisted is blocked) went unexamined for a day while the fix it produced did not work. An identifier
   read out of prose at least stays a name; a *rule* read out of prose becomes the recorded explanation
   for behaviour nobody has watched. **The tell is the word, not the content:** "measured" is reserved
   for something this project ran, and a doc reading that says so is worse than an admitted guess,
   because a guess invites the measurement and a false measurement forbids it.

39. **What a console wizard fills and the authoring API does not require is still required — and the
   validator is the deploy and the teardown, so an incomplete object pins its dependents in both
   directions.** Stage 6's blueprint configurations were created through
   `PutEnvironmentBlueprintConfiguration`, which accepted objects missing three things the Enable-Tooling
   wizard always fills: the manage-access role, the projects-bucket `S3Location`, the `KmsKeyArn`. Nothing
   failed at Put time. Each absence surfaced only when a project tried to **deploy** an environment — and,
   worse, when a stuck project tried to **delete** one: teardown validates the same fields, so a project
   born under an incomplete configuration could neither finish nor be removed until the configuration was
   completed. Five portal attempts paid for the ladder one rung at a time (2026-08-22).
   **This is Lesson 16 inverted, and the inversion is the content.** Lesson 16's failure mode is a human
   at a wizard answering fields the plan never named — the wizard as the under-specified surface. Here no
   wizard was used at all: the API was the lax surface and **the wizard was the de facto completeness
   specification** — the checklist of what the service will eventually demand. When automating an act a
   console wizard also performs, enumerate the wizard's fields and treat every one as required, whatever
   the API's schema says.
   **The second face, from the same sitting: the strict validator arrives exactly one act late.**
   `CreateProjectProfile` validated nothing against the blueprint templates — a locked
   `lifecycleManagement = "true"` sailed through where the template's enum is `ENABLED`/`DISABLED` — and
   the error arrived from CloudFormation at the first deploy; then `UpdateProjectProfile` validated what
   Create had not (required template parameters with no default). An authoring API that accepts an object
   proves only that the object parses; **the act that has to build or redeclare it is the real validator**
   (Lesson 32's "the side that has to build it is the one that was right", as a lifecycle rule), and the
   templates were downloadable all along (Lesson 38's discriminator: check locked values against the
   template, never against prose). **The cost profile is what earns the number**: validation deferred past
   the authoring act lands on a *destructive or irreversible* act, so the defect is discovered exactly
   where it is most expensive to hold — a system that cannot deploy AND cannot tear down.

40. **The door a call takes is a fact of resolution and routing — the service's endpoint roster
   predicts nothing, and an endpoint's private zone answers for its whole subtree.** One sitting
   measured three doors and a no-door, all from one laptop on the tunnel (2026-08-23/24). `sts` left
   through the **interface** endpoint — private DNS had hijacked its name, so a deny keyed on gateway
   endpoint ids denied a call that was *on* the VPN. `s3control` left through the S3 **gateway** — it has
   no interface endpoint here, which a derivation turned into "so it rides the IGW", and CloudTrail
   refuted: a gateway route matches a **prefix list**, `s3-control.<region>` resolves inside `pl-s3`'s
   ranges, and "has no interface endpoint" says nothing about the IGW. And
   `agent.datazone.<region>.api.aws` left through **nothing**: the `datazone` endpoint's private hosted
   zone is **authoritative for the entire subtree** of the name it serves, holds only the apex, and
   answers NXDOMAIN for every subdomain that exists only in public DNS — no fallback, for every client
   of the VPC resolver, the full-tunnel laptop included.
   **The roster is a list of what AWS sells; resolution is what this VPC does — and only the second is a
   fact here.** Both are measurable for a cent: `dig` from inside, `vpcEndpointId` in CloudTrail. The
   subtree half is the sharp edge: `PrivateDnsEnabled` reads as *"this name now resolves privately"* and
   means *"this subtree now resolves ONLY here"* — the blast radius is every name under the service
   name, including ones the vendor's own front-ends need (the SMUS portal's `agent.datazone…`,
   documented public-internet-required, went NXDOMAIN and broke the portal ON the VPN). No allow-list
   sees it: the DNS Firewall filters queries, and these queries were *answered* — authoritatively, with
   nothing. **Distinct from Lesson 3**, which is about policy conditions anchored on `[E]` endpoint ids;
   this is the *path itself* being mispredicted from the roster. The design-B corollary: a design that
   multiplies interface endpoints multiplies authoritative private zones, each shadowing a subtree — a
   cost no endpoint price list carries.

41. **A vendor "required" travels without its premise — and the page that says required can carry, lower
   down, the table that contradicts it for your design.** `datazone` entered both Interactive endpoint
   lists on one comment: *"the SMUS network-isolation page marks it REQUIRED under VpcOnly, so an app
   cannot reach the domain without it."* Three errors in one sentence, all checkable from the page
   itself (2026-08-24). The premise is swapped — the page never says `VpcOnly`; its required table is
   scoped by the page's **own** isolation definition, *"access to the public internet is denied from the
   Amazon VPC"*, which is design B. The consequence is refuted by the page (*"network calls … route over
   the public internet when that network path is available"* — design A has that path, with
   `datazone.<region>.api.aws` allow-listed), by this estate's own history (**six of the fifteen
   "required" endpoints have never existed here** and the create path closed end to end), and by the
   page's own troubleshooting table (*"Private with NAT + Private with NAT: Works as expected. No action
   needed"*). And the same page carries a **third table** two prior readings never recorded — *Public
   internet access*: the portal's client assets, its client APIs (`agent.datazone.<region>.api.aws`
   among them) and the IdC sign-in endpoints **require the public internet** — so one page instructs the
   endpoint and requires a name that endpoint's private zone shadows. Where the tables collide, **the
   browser-facing one wins**: a portal is a web client, and no interface endpoint serves a web client's
   edge.
   **"Required" is always required-under-a-premise, and the premise is what falls off in transit** — the
   word survives the copy, the condition does not: Lesson 38's failure for names, applied to a
   requirement's scope. The comment even declared itself — *"the ONLY entry added from that page on
   faith"* — and the self-award of an exception is not a discharge: **an entry marked "on faith" is a
   scheduled defect**, and of the whole list it was the one that broke. The repair for the class: when
   copying a "required" row, copy the sentence that scopes the table — and read the whole page, because
   the contradicting table sat three scrolls down the same URL this repository had already cited twice.

42. **A permission failure is a response; a network failure is the absence of one — and CloudTrail
   separates "denied" from "never arrived".** The on-VPN portal break arrived with a plausible cause
   attached: the same week had re-keyed `DenyControlPlaneOffVpn`, so the deny was the suspect. The
   symptom had already ruled it out. An IAM deny is an **answer** — HTTP 403 with a body, a console
   naming the policy family, a CloudTrail event carrying `errorCode` — because the request reached the
   service and was evaluated. The browser's *"Failed to fetch"* is the opposite shape: `fetch()`
   rejecting before any HTTP exists (DNS, TCP, TLS, CORS), which no policy can produce. And the
   discriminator costs one query: CloudTrail held **45 events from the home address and zero from the
   tunnel** — same portal, same minutes. Zero events is not a deny; a deny leaves an event. The
   suspected policy was never evaluated, because nothing arrived to be evaluated.
   **Classify the failure by what came back — a body, a refusal, or silence — before opening any policy
   document**, and let CloudTrail's presence/absence split the last two. The suspect here also failed
   the *sign* test: the re-keying was **permissive** for the suspected path, so even its direction was
   wrong. This is Lesson 24's channel discipline pointed at a different pair — not benign-vs-serious
   wordings of one denial, but denial-vs-no-arrival, which no wording can distinguish because one of the
   two has no words.

43. **A browser is a term in the reach question, and its policy is one no AWS instrument can read — so
   every gate in the estate stays green through a total outage.** Removing the `datazone` endpoint
   discharged the NXDOMAIN shadowing of 2026-08-24, and the portal on the tunnel then failed with the
   **identical words**: `TypeError: Failed to fetch`, on the catalog tab and on the JupyterLab space. The
   surviving endpoints' private zones were answering *correctly* — the whole `*.studio.<region>.sagemaker.aws`
   subtree, `glue`, `lakeformation`, `athena`, all to `10.20.x.x`, which is the design working as
   intended. But the portal is a **public** origin, and a browser gates a public page's request to a
   private address behind a permission (Chrome's **Local Network Access**); ungranted, `fetch()` rejects
   before any HTTP exists. `curl` from the same laptop, the same minute, reached every one of those
   addresses — it implements no such policy. **Everything this repository owns read clean throughout:**
   `DN-1` 43/43, the DNS Firewall allowing, CloudTrail silent, `dig` answering, `terraform plan` empty.
   The only instrument that could see it was a person clicking a permission.
   **CloudTrail could still attribute it afterwards, and that is the reusable move**: the calls that
   *succeeded* after the grant name what was failing before it — the catalog tab resolved to Glue at the
   `glue` endpoint, the JupyterLab launch to the SageMaker API at `sagemaker.api`, both arriving from the
   VPN host's **private** address — while the ~25 minutes of the outage held **zero arrivals**. The trail
   cannot see a browser-side refusal, but the *shape* of the recovery identifies it: read the first
   successful minute to learn what the silent minutes were trying to do.
   **Lesson 28 said reach is an intersection; the intersection does not stop at AWS.** When a control
   plane's client is a browser, its terms join the product — origin classification, CORS, private-network
   gating, mixed content, cookie partitioning — and they share a shape: they are properties of the
   *requesting document's* context, so they are invisible to the account, invariant under IAM, and
   untestable by any harness that speaks HTTP without being a browser. Two corollaries, both structural.
   **A full-tunnel client resolving through a VPC that holds interface endpoints has been moved into
   those endpoints' address space without anyone deciding to** — every public web console for those
   services inherits the gate, as a side effect of a DNS setting made for the compute plane. And the
   fixable case was the exception: `datazone` could be deleted, `sagemaker.studio` cannot, so **the class
   whose first instance was repaired by removing an endpoint is in general repairable only by moving the
   client off the resolver** (open question 23). A per-origin browser grant is the interim, and it is not
   infrastructure: no gate asserts it, no state file holds it, and it dies with a browser profile.

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
