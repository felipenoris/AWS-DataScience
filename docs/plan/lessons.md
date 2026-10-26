# Lessons carried forward

These are findings from the planning period that re-reading the plan will not give back. Add to this
list only what would otherwise be relearned the hard way.

Read it before planning, reviewing, or settling a decision. `CLAUDE.md` carries the titles so a lesson
can be recognised without opening this file; the reasoning that makes each one usable is here.

---

1. **A copy of governed data landing somewhere less governed is not a hole to be closed.** It is a
   property of every SageMaker installation, not something D18 introduced. The control is the data
   perimeter (`docs/plan/architecture.md` §4.2), which stops the copy leaving the organization;
   preventing the copy was never the control. The first answer given on this treated it as a newly
   opened gap.
2. **A stand-in that shares an account with the thing it de-risks proves nothing about permissions.** A
   `staging` Glue namespace *inside* Production was once invented to substitute for a Staging account: it
   shared an IAM surface and a blast radius with its own subject, so it could catch a schema error and
   never a permission error — which is the failure class a cross-account promotion actually produces.
   That is why D20 exists.
3. **When a decision moves a resource across an account boundary, re-check every condition that
   referenced it — especially conditions pointing at ephemeral things.** This nearly shipped: Stage 5a
   pinned the Data Governance bucket policies to the consumers' `aws:SourceVpce`, but interface endpoints
   are `[E]` (new IDs on every `make up`) and since D22 live in a *different* account, so nothing would
   ever repair them. Anchor on the `[P]` S3 **gateway** endpoint, or on `aws:SourceVpc`.

    Its quieter half, measured 2026-09-06 and written out as Lesson 48: the resource
    need not move at all — its **name** moving is enough, when another account resolves it by
    tag, alias or path rather than by id. Stage 6c step 1.1 re-labelled a VPC, every id was
    unchanged, its gate passed, and two other accounts broke until somebody ran a plan in one
    of them.

4. **State that lives only inside an `[E]` resource is this design's recurring failure mode**
   (`docs/plan/conventions.md` §5.1 rule 2). Three hits already — EFS, the Studio domain, MWAA's
   metadata database — and it will recur for every stateful service considered for the `make up`/`make
   down` cadence. Check it before adopting one.
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
   written into `docs/plan/institutional-delta.md` as "what an institution would do, notational here" a
   few hours earlier, and that was wrong: with one persona, a single human writes a job that reads
   restricted data, approves its release and approves its access to that data. Three acts, one
   signature. Never assign one person to both groups. The related trap: the governance manager must not
   have blanket read on the data they gate — an approver who can already read everything is not
   exercising a control.
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
   1d's deliverable (Stage 1b's, when it was written) proposed `aws ram get-resource-share-associations`
   as the proof that organization-wide sharing was enabled; with no share yet created it returns an
   empty list in both cases. This is the detection-side twin of Lesson 5: an intention is not a control,
   and a command that cannot fail is not a check. Before writing a deliverable, ask what its output
   looks like when the thing is *broken*.
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
   This one was caught by execution rather than by review. Stage 1a step 4 read "create the accounts
   through Account Factory, using the e-mails in `secrets/emails.md`" — complete-sounding, and wrong: the
   wizard asks for a **second** address under **Access configuration**, and AWS's wording for it is that
   the user *"will have administrative access to the account you're provisioning"*. The plan named one
   e-mail and the form has two, so the obvious answer — reuse the account's own address — would have made
   a root e-mail a federated administrator on every vended account, two steps before the same stage
   removes root credentials centrally. D32 settles the value. The general form: for every manual step,
   write down every required field and the value it takes, not only the fields the plan already has an
   opinion about. The unnamed ones do not stay unanswered; they get answered by whoever is executing, at
   the moment they least want to be designing identity. The tell is a step whose verb is "create X
   **using** Y" — `using` almost always hides a form.
17. **A service that "sets itself up" creates principals nobody chose — enumerate them before the next
   step depends on one.** Lesson 16 is about fields a wizard *asks* about; this is the class it does not
   cover, because the wizard never asks. Enabling Control Tower created an Identity Center user,
   `AWS Control Tower Admin`, holding administrative access to the Management account under the root
   account's e-mail address — the collision D32 refuses for vended accounts, arrived at from the other
   side, and it surfaced only because an invitation e-mail landed in an inbox. Its twin finding is the
   opposite shape: the root user, which had done every step so far, cannot use Account Factory at all
   (documented), so a step written as "create the accounts through Account Factory" was not executable by
   the identity that was executing the stage. The general form: after enabling any service that provisions
   identity or federation, list the principals that now exist and ask of each one *which of this plan's
   personas is it* — the honest answer is often "none, and it is an administrator". And for any manual
   step, say which identity performs it, not only what it does; "whoever has the console" is not an
   identity, and the console the previous step accepted is not evidence about the next one. D33 settles
   both halves.
   The expensive part is downstream. Stage 1a step 3 described what Control Tower creates on the *account*
   axis — the Organization, Log Archive, Audit, CloudTrail, Config — and said nothing on the *identity*
   axis. So two later steps were written against a state that was never going to hold: 1b step 2 said
   "create the users and the groups" and 1b step 3 said "create permission sets: `AdministratorAccess`, …"
   in a directory that already contains Control Tower's groups and a permission set named
   `AWSAdministratorAccess` — four characters away, also granting administrator, and an assignment against
   the wrong one still works, so nothing would have reported it. A missing enumeration does not stay
   local: it becomes a wrong assumption in every step that reads the same resource later. When a step ends
   with "X now exists", enumerate what X *contains*, on every axis, not only the one the step was about.
18. **A policy never constrains the principal that authors it.** Lesson 11 says that changing *who
   authors* an IAM policy invalidates every claim made about that policy; this is the same fact from the
   other side, and it holds permanently rather than being triggered by a change. Every control in this
   design — the two approvers' denials, the derived zone's CMK, the OU policy sets, the permissions
   boundaries — is written by the infrastructure user and applied under its credentials. "Can a data
   scientist read the derived zone?" has an answer; the same question about the identity that owns the key
   policy does not, and it went unasked until someone read `docs/ORGANIZATION.md` and noticed that the
   persona with the thinnest description was the one holding administrator everywhere. The general form:
   for each control, name the principal that authors it, exclude that principal from the claim, and ask
   what is *left* holding it. The answer is almost always detective — a log that principal cannot edit, an
   alarm on the membership that would grant the reach, an object lock its own administrator cannot lift —
   so enumerate those three rather than attempt a preventive control the author would simply rewrite. The
   tell is a separation-of-duties table whose rows are all *approvers*: the builder is missing because the
   table was written about approval and the builder does not approve. The related tell, cheaper to spot:
   the persona with the shortest section in the document is usually the one with the widest reach, because
   reach that nobody had to argue for is reach nobody wrote down.
19. **A blocking input has to be re-checked against the requirement it actually serves, not against the
   mechanism that was chosen for it.** D15 needed *a certificate a client would trust*. The mechanism
   chosen was *a public domain*, and from then on the plan tracked the mechanism: "the domain name" sat
   for weeks as the one input needed from the user, blocking Stage 7, listed in `CLAUDE.md`, in
   `open-questions.md` and in two stage files. It survived because it was never re-derived — nobody asked
   again what the certificate was *for*, and the answer, once asked, was "three clients we build
   ourselves", which needs no public trust chain at all. The trigger that exposed it was unrelated:
   `CLAUDE.md` gained a line saying GitLab is intranet-only, and the mechanism's premise went with it. The
   general form: when a requirement is restated — especially when it is *narrowed* — walk the decisions
   downstream of it and ask which of them were solving the old, wider version. The second half deserves
   the same attention: deferring the mechanism improved the design rather than merely postponing it,
   because a public certificate publishes its names to Certificate Transparency logs. A prerequisite that
   has quietly become optional is usually also carrying a cost nobody has priced, since nothing was
   forcing anyone to look at it.

20. **When several policies deny the same call, only one of them is proven — the others are attached, not
   exercised.** Stage 1c step 7.6 parked all four per-OU documents on `Policy Test` at once and ran the
   battery there. Every probe was denied and every denial named a policy id in the API error itself, so the
   run looked complete. It was not: `awsds-org-scp-ou-interactive`'s two actions are also denied by the
   `Workloads` document and matched by the `Identity` document's `sagemaker:Create*`, and AWS names one
   matching policy — so that document decided nothing, and a document that never decides is a document
   whose condition, `Sid` and action spelling have never been evaluated. The tell is cheap and worth
   looking for by name: a candidate that appears in *no* probe's attribution column. The fix is not more
   probes but the right target — moved to `Interactive`, where nothing else denies `CreateNotebookInstance`,
   it was proven in one call. The general form: overlapping denies compose into a *result* that is
   indistinguishable from any one of them working, which is Lesson 13's shape moved from the verification
   into the policy set, and the same argument applies to a deny you inherit from the root while testing an
   OU-level candidate. The composed run was still worth running: the *must still succeed* half only gets
   stricter under composition, and the denial message naming the policy id is what let the gap be spotted
   at all rather than assumed away.
   A second instance arrived at 7.7, where the attribution answered a question nobody had asked.
   `Sandboxes` was given its own enabled control, and the probe run
   in `awsds-infra-sandbox-1` came back denied — naming `Interactive`'s policy, not the new one. The
   question under test was *is this nested OU a registered target*, and what the probe measured was
   *coverage*, which inheritance had already guaranteed and which would have looked identical had the
   enablement silently failed. A probe cannot distinguish a control you just added from a deny you
   already had; the OU's attached-policy list is what answered it. Read the *configuration* when the
   question is about configuration, and keep probes for behaviour.

21. **"The service validates before authorizing" is a property of the *action*, not of the service — so a
   validation error on the first try is a reason to retry with a real id, not a result.** Stage 1c had
   already met the wall twice and generalised it one step too far: `ec2:ModifySnapshotAttribute` and
   `datazone:CreateDomain` both rejected invented inputs before authorization, so the amendment of 7.5a was
   written expecting the same of every EC2 and RDS probe. In one run, in one account, three different
   answers came back: `ec2:ExportImage` and `ec2:CreateInstanceExportTask` authorized against a malformed
   AMI id and returned the deny; `ec2:CreateStoreImageTask` rejected that same id shape and only reached
   authorization once a real public AMI was passed; `ec2:StartInstances` never reached it at any id
   length. `ec2:CreateFleet` had been predicted untestable for want of a launch template and was denied
   anyway, because `--dry-run` authorizes before resolving the template. The cost of the wrong default is
   asymmetric: recording *untested* too early leaves a statement that is in fact exercised carried in the
   notes as unproven, and the next reader either re-tests it or, worse, trusts the note and treats a live
   control as a gap. The general form: a negative result from a probe is only a result once the probe has
   been given inputs that exist — the public AMI from SSM, a subnet from `describe-subnets`, the account's
   own id in an ARN — and "the API validates first" is a claim about one API call, to be re-established
   each time rather than inherited from the last one.

22. **A control whose principal the harness cannot produce is verified by *reading* the deployed document,
   not by attempting the call — and a green battery is silent about that whole class.** Stage 1c step 7.7
   enabled `AWS-GR_RESTRICT_ROOT_USER` on `Policy Test` without `ExemptAssumeRoot`, which denies
   `sts:AssumeRoot` into every account beneath it — 1a step 6's only member-account recovery path, since
   6.4 had established that no member account holds root credentials at all. The battery ran 61 of 61 as
   expected in the same sitting and could not have found it: every principal this project can obtain is
   an Identity Center role, and the statement's condition is `ArnLike aws:PrincipalArn = arn:*:iam::*:root`,
   which no such role matches. The defect was found by reading `p-kve97k0o`. The discriminator, to apply
   while *writing* a verification rather than after: can this harness produce a principal that satisfies
   the condition? If not, the plan must state what to read and which string proves it, never what to
   attempt. Three statements in this project are already in that class — the root control
   (`aws:AssumedRoot`), the positive half of D27's catalog-maintenance carve-out (needs Stage 5a's role to
   exist), and the positive half of the `aws:PrincipalIsAWSService` guard (needs a service principal) —
   and the counter-example proves the discriminator does work: decision 7's BPA carve-out names
   `InfrastructureAccess`, a principal that *does* exist, and was measured in both directions.
   This is worse than Lesson 21 rather than a variant of it: a probe given a bad id at least
   reports `UNTESTED`, which is visible. A probe that structurally cannot exist reports nothing at all, and
   nothing reads as *fine* — the absence is indistinguishable from the case being covered. So the battery
   needs a companion list of what it cannot see, which is why
   [`docs/plan/runbooks/scp-battery.md`](runbooks/scp-battery.md) now carries one. The omission cost almost
   nothing only because of an unrelated earlier decision — with
   no root credentials anywhere, the unexempted control denied exactly and only the thing it was meant to
   exempt. That alignment was luck, not design, and will not repeat.
23. **When a managed service creates artifacts on your behalf, the container is its implementation detail —
   bind to contents, never to the id or to the job the artifact was created for.** Control Tower emits each
   enabled control as an ordinary SCP, which is what made verification (vii) readable at all. But its
   *packing* is per enablement and is not consistent: in one console session, on the same day, the two
   root-user controls were folded into the original guardrail document on `Policy Test`, `Workloads`
   and `Interactive`, and into the `CT.MULTISERVICE.PV.1` document on `Identity` (`p-fw2pctqw`) and
   `Data` (`p-pk85fvr1`). Nothing distinguished those two OUs; the same clicks produced two shapes. The
   damage is not to the controls — they all work — but to every record that named a document by its
   job: the log had those two ids written down as "the Region policy" for those OUs, and that sentence
   became half-false the moment a second control was enabled. The general form: an artifact created for
   you has an identity the service owns, may re-use, and may repack; its id, name and reason for existing
   are all outside your control, and only its *contents* are what you asserted. Read the `Sid` list.
   The tell is prose that refers to a managed document by the job it was created for rather than by
   what is in it — and the same caution applies to anything else a service names for you, from
   `AWSReservedSSO_*` role suffixes to service-linked roles.
24. **A harness authenticates through the mechanism it is measuring, so the one result it cannot report is
   a failure of that mechanism — and the defence built for the benign version of that failure is what
   hides the serious one.** On 2026-08-14 `awsds-org-rcp-perimeter` was attached to the root with an STS
   statement naming `sts:AssumeRoleWithSAML` and `sts:TagSession`. Those are the only two actions the
   trust policy of an `AWSReservedSSO_*` role permits, so the deny did not restrict a perimeter — it made
   every permission-set role in every member account unreachable, from the CLI and the access portal
   alike. The battery contained six probes written for exactly this (`rcp floor: credentials still
   vend in …`), and not one of them could run: `ensure_session` tested credentials with a bare exit-code
   check and aborted the run as a *dead SSO session*, which is the hardening added after two mid-battery
   token expiries. The earlier lesson's fix produced this lesson's blindness, and it did so silently,
   because at the exit code an expired token and a denied sign-in are the same event. The discriminator,
   to apply while writing a verification rather than after: what does the harness itself need in order
   to report at all — credentials, a network path, a role — and can the change under test reach it? If it
   can, the verification cannot live inside that path. Here the outside instruments were the two that do
   not depend on it: Management, which RCPs do not affect by construction, and reading the trust
   policy of the role. A second trap sits behind the first and makes a bad attach look
   fine: a vended role credential lives four hours in `~/.aws/cli/cache`, so nothing fails at attach
   time — the probes run against a session minted before the policy existed and pass. Anything touching
   the sign-in path has to be tested against a *fresh* vend, which means invalidating that cache first.
   Against Lesson 22, its neighbour and not its twin: there the harness cannot *produce* the
   principal a control names, and the silence is a row that was never written; here the harness cannot
   *survive* the control, and the silence is an abort that confidently names the wrong cause — the worse
   of the two, because it comes with an explanation. The script now reads the error wording, stops only
   on an expiry, and records anything else as a floor breach with every probe behind it marked untested;
   the general form applies to any test rig that signs in through the system it is testing.

   **The wording fork above is necessary and not sufficient; the missing half is where to look, not how
   to read.** The fix this lesson produced classifies by error text: expiry stops the run, anything else
   is recorded as a floor breach. On 2026-08-20 `aws sso login` reported success and every `awsds-*`
   profile failed with `ForbiddenException … GetRoleCredentials … No access` — the exact wording of
   2026-08-14, and this time nothing was wrong with the organization: the browser had silently
   re-approved a live portal session belonging to a *different* human, and the token cache is keyed by
   **sso-session name, never by user**, so the wrong identity's token had come to occupy the right
   identity's slot. One wording, two causes, and they demand opposite handling — record the most serious
   finding the harness can produce, or stop and record nothing. A second text rule would repeat this
   lesson in reverse: any pattern narrow enough to recognise the operator's mistake also matches the
   real breach, because the two produce the same sentence *by construction* — the ceiling denies the
   sign-in flow, and a sign-in flow with no assignment behind it is refused by the same call for the same
   reason shape. So the discriminator cannot be a better reading of the answer; it has to be a different
   question, put to a system whose path does not traverse the mechanism under measurement. Here that is
   Identity Center's own listing of what the token is assigned (`sso:ListAccountRoles` against the cached
   token): it never reaches STS, so no SCP and no RCP can shape it. Assigned but refused is the ceiling
   and the finding stands; not assigned is an operator's click and nothing about the estate. The third
   state is what makes it safe to use: "could not tell" must keep the finding, because a hidden breach
   costs an incident and a spurious one costs an investigation. The parent lesson's instruments were
   chosen the same way, for being *outside* the path (Management, which RCPs cannot reach; the role's
   trust policy, which is a read of configuration rather than an exercise of it). The rule generalises
   past sign-in: **whenever a negative result has more than one origin, the separating evidence must come
   from a channel the tested mechanism cannot influence.** A corollary: an
   operator-side mistake can present as an estate-wide finding, so before a harness writes down a breach
   in *every* account at once, ask what single local thing could produce that same uniformity.

   A second instance the same day did not fit the sentence above. Pass 4e denied
   `athena:StartQueryExecution` and probed it. The refusal has exactly one origin — the SCP — so
   "more than one origin" does not describe it; what it has is no attribution in its own text: Athena
   answers with a bare *"You are not authorized to perform: … on the resource"*, naming no policy and no
   id. The battery's `classify()` has read wording since Stage 1c and files a policy-less `AccessDenied`
   as `DENY-NOT-SCP`, *"an IAM/permission-set deny, not the ceiling"* — sound reasoning, wrong here, and
   unfixable by any pattern, because the service never emits the string the pattern would need. Every
   probe written before this one happened to hit a service that names the document, so the assumption was
   invisible for eleven weeks. The remedy was the same one, reached faster for having been written down:
   attribution by a **contrast probe** — the same call, same principal type, same region, one session,
   from an account in an OU the amendment does not reach; it passed authorization, so the two refusals
   can only be the ceiling. The rule is about locus, not ambiguity: *when a result cannot be
   attributed from its own text — because the text is ambiguous or because it is silent — the attribution
   must come from a channel the tested mechanism cannot influence.* Two consequences worth acting on. A
   probe's expected wording is an assumption about the service, not about the control, worth stating
   when writing the probe, because it is the kind that holds for years and then does not. And do not
   fix this by loosening the classifier: teaching it to read a policy-less deny as the ceiling would
   misread every genuine IAM deny in the battery, so those two rows are left reporting `note` rather than
   `ok`, permanently and on purpose, with the contrast probe beside them carrying the meaning.

   A third occurrence — Stage 6's trust defect, 2026-08-22 — extends the progression one step: ambiguous
   text → silent text → absent event. Both SMUS service-role trusts pinned the member account where the
   documented guard wants the domain account, so the service could never assume them — and the observation
   channel itself was empty: a cross-account service `AssumeRole` denial leaves no CloudTrail event in
   the target account. There was no wording to read, no exit code to misread, nothing. The outside
   channel that carried the attribution was the documentation — the published trust contract for
   `AmazonSageMakerProvisioning-<domainAccountId>` names `aws:SourceAccount = the domain account` — read
   against the deployed trust, Lesson 22's remedy arriving through Lesson 24's rule. When the failing
   principal is another account's service, plan the attribution as a reading from the start, because the
   trail on your side will structurally never carry the denial.

   The same shape without a harness in it, and the instrument was a log (2026-08-23). Stage 6
   step 4.3's session found the SMUS notebook unable to resolve `files.pythonhosted.org` while
   `pythonhosted.org` answered. The Resolver query log was read for attribution and reported, for every
   failing name, `BLOCK` against the queried name with the catch-all list id — which reads, exactly
   and only, as *"that name is not on the allow-list"*. It was not: the name was on the list, and what
   the catch-all had matched was a CNAME target one hop further down, a name the log never prints. The
   log also populates no `firewall_rule_action` on an ALLOW, so the allowed names looked un-evaluated
   too — two ambiguities in one field, pointing the same wrong way. A correct hypothesis was abandoned
   on the strength of that reading, which is this lesson's cost measured on its own terms. The
   discriminator was again not a better reading but a different question: a paired probe under an
   identical rule shape, run from a second host in the same VPC — `blobs.duckdb.org` (A records) against
   `index.crates.io` (CNAME to a CDN), both under a wildcard of the same depth. Same rule, opposite
   outcomes, one variable. The general form for any log: a field naming the object you asked about is
   not evidence about the object that matched, and when a system resolves through a chain, indirection,
   or redirect, the log will name the entry point every time.

25. **A borrowed session outlives the command that needed it, and every later error then describes the
   wrong account.** Stage 1d step 9 had to write past `CTS3PV8`, which exempts `AWSControlTowerExecution`
   alone, so the credentials were assumed from Management and exported into the shell. The write was not
   made in that sitting. In the next one, three commands ran as that role without anybody choosing it:
   `list-accounts` was denied — correctly, since it is a management-account API and the caller was now in
   Log Archive — and because the `&&` chain stopped there, the account variable stayed empty and the
   following command built `arn:aws:iam:::role/AWSControlTowerExecution`, producing a second
   `AccessDenied` about the role failing to assume *itself*. Two authorization errors, neither of them
   an authorization problem, and both naming an account the operator had not selected. The general form
   has two halves and they compound. First: an exported credential is ambient state with no visible
   marker — the prompt, the console tab and the CLI profile all still say what they said before, so the
   only instrument is `get-caller-identity`, and `unset` of the three variables is the *pair* of assuming
   them, not an optional tidy-up. Second: a `&&` chain that carries an empty value forward converts a
   missing input into an authorization failure, which is strictly worse than crashing, because the error
   text is plausible and sends the reader to the policy instead of to the variable. Resolution steps abort
   on empty; borrowed sessions are unset in the same block that used them. Against Lesson 24, its
   neighbour: there the harness could not survive the control it measured; here the operator could not
   *see* the identity they were using, and the wrong identity was one they had legitimately created.

   The same blindness has a second entrance: granularity, not duration (2026-08-17, caught by the
   user in review while preparing Stage 4 step 8.3's control-plane pair). Above, a credential
   *outlives* the command that needed it. Here the operator performs the switch and the switch does not
   happen: the AWS CLI caches an SSO token under the `sso-session` name, so profiles sharing a session
   share one identity, however many different people those profiles were written for. Switching
   `AWS_PROFILE` changes the account and the role being *requested* and changes nothing about *who is
   asking*. It does not vend the wrong credential — `sso:GetRoleCredentials` is refused, because the
   token's user holds no such assignment — but it is refused by the portal at vending time, a third
   failure mode dressed as the two the reading was built to tell apart (Lesson 13's shape, arriving
   through the harness rather than through the check). The rule that prevents it is one `sso-session` per
   person, which [`aws/AWS-CLI.md`](../../aws/AWS-CLI.md) already stated and which this drafted config had
   quietly broken by giving four different persona users one shared session. The general form: ambient
   identity is invisible in exactly the places that look authoritative — here the profile name, there the
   shell prompt — so the discriminator is the same in both, `get-caller-identity` and the assumed-role
   ARN it prints, read *before* the call that matters and not after it fails. The corollary for anything
   shared by name: ask what the cache is keyed on, not what the flag you typed is named.

26. **An "already exists" error is the cheapest authorization probe there is — and it proves nothing until
   an unprivileged principal has been shown to get a different one.** Stage 2 step 5.0 had to establish
   that the organization delegation reached its `Resource` list's target entries, and could not: the write
   it had already run, `UpdatePolicy`, authorizes against the *policy* ARN alone, and the stage's only
   other contact with attachments is an import, which calls nothing. The move was to attach a policy that
   was already attached — `DuplicatePolicyAttachmentException` if authorization passed, `AccessDenied` if
   it did not, and no possible mutation either way, because the end state is the state that already held.
   The general form: any create/attach/put with an idempotency conflict can be aimed at an existing object
   and read as an authorization test, which is how a preventive grant gets measured without exercising it
   for real. The half that is easy to skip is what makes it a measurement. The reading holds only if
   IAM authorization runs *before* the service's own conflict check, and that ordering is a property of the
   action, not of AWS (Lesson 21, from the other side) — if it were reversed, a principal with no permission
   at all would receive the same conflict, and the probe would return the same answer on success and failure
   (Lesson 13). So the probe is a pair: the call from the principal under test, and the same call from
   one known to hold nothing. Here the canary returned `AccessDeniedException`, which is what converted the
   two conflicts into evidence. The shape has a boundary: an entry with no existing object to aim at —
   `account/…/*`, since nothing in this design is
   attached to an account — cannot be probed inertly at all, and stays a reading. That is the honest
   outcome, not a reason to create an object so the probe becomes available.

27. **A declarative plan is silent about the values the provider owns — so the setting that has to be
   right *before anything else exists* is precisely the one Terraform will not promise.** Stage 5a step
   5.2 rests entirely on D13: the lake's databases must be born without the `IAM_ALLOWED_PRINCIPALS`
   default grants, because those act at creation time and clearing them afterwards does not reach a
   database that already exists. That obligation is an *emptying*, and
   `aws_lakeformation_data_lake_settings` offers no way to write it. Three forms were tried against the
   pinned provider and none of them states it: omitting both blocks plans as `after_unknown: true`,
   which is Terraform declaring *no intention*; `create_database_default_permissions = []` is refused,
   because they are blocks and not arguments; a `{}` block would declare one entry with computed
   fields, which is not zero. So the security property the stage exists to establish could not be
   expressed at all, and the plan rendered identically in the case where the apply would clear the
   defaults and the case where it would leave them standing. That is Lesson 13's shape moved into the
   plan itself: the artifact you read *before* acting cannot distinguish the two outcomes, which is
   worse than a verification that cannot, because the plan is what authorises the apply.
   The discriminator is one command on a plan you already have, and the obvious route does not work:
   `terraform providers schema -json` marks `computed` on attributes and never on `block_types`, so
   the schema cannot answer it for blocks. The plan can:

   ```bash
   terraform show -json <plan>.tfplan | jq '.resource_changes[] | select(.address=="<addr>") | .change.after_unknown'
   ```

   Anything coming back `true` is decided by the provider, not by your configuration. Ask it on a
   create-or-update plan — on a `no-op` everything is known from state and the answer is `{}`. If the
   cleared state of one of those is load-bearing, the apply must be split so the result can be read
   before anything depends on it, which is why [Recipe D](runbooks/terraform-changes.md) now exists.
   The class is recognisable in advance. The exposed resources are the account-level settings singletons
   — the ones that create nothing and overwrite
   server-side state that AWS, not you, initialised: `aws_lakeformation_data_lake_settings` here, and by
   the same shape `aws_s3_account_public_access_block`, `aws_ebs_encryption_by_default`, and most things
   named `*_default_*`. They have no create, only a put, so whatever you omit either keeps what was
   there before you existed or does not, and only the provider's implementation says which.
   The good outcome is a measurement of one provider version, not a property of Terraform.
   Omission turned out to clear (`DbDefaults: []`, then verified per database: no `IAMAllowedPrincipals`
   grant anywhere). That was obtained by looking, the plan still does not state it, and the next
   provider version can change it in silence with nothing failing — so the read-back is kept rather than
   the split being collapsed. Against Lesson 5, its nearest neighbour: there a property was written
   down and no policy line enforced it; here the property could not be *written down at all*, and the
   tell is a `plan` that renders the same text whether the intention will hold or not, rather than a
   stated intention missing its enforcing line.

28. **When a service keeps its own permission layer above IAM, a principal's reach is the
   *intersection* — and this repository's layout puts the two halves in different slices, so a slice
   is never the unit that answers "what can this persona do".** Stage 5a pass 2 made the governance
   manager's first grants. `identity/sso/policies-approvers.tf` carries a statement called
   `AdministerLakeFormation` (`AddLFTagsToResource`, `GrantPermissions`, `CreateLFTag`), which reads
   like the complete answer to what the persona may do, and on its own grants nothing. Lake
   Formation authorizes separately: the IAM action permits the API call, an LF permission
   (`ASSOCIATE` on the tag) decides whether the call succeeds. The two live in different accounts,
   different slices and different stages, while the natural unit to open is a slice. The failure
   shape is what makes it expensive: before pass 2 that file read exactly as it reads now and the
   persona could not tag a single dataset, and with Lake Formation enforcing, a missing grant makes
   `glue:GetDatabases` return an empty list, not an error. The wrong conclusion is drawn from a file
   that is accurate, and the symptom is an absence (Lesson 13's shape, through a service's own
   result-filtering). The reverse direction has no symptom at all: revoke the LF grant and the IAM
   policy still describes the capability. Lake Formation over IAM is one instance; a KMS key policy,
   an S3 bucket policy, a Glue or RAM resource policy are the same shape. Any claim about what a
   principal can do names both halves or is not a claim. The discriminator: for each capability, can
   you point at the two grants? If you can point at one, the other exists somewhere and you have not
   read it. Against Lesson 20: there several policies deny the same call and only one is proven,
   redundancy making a result ambiguous; here the two grants are each necessary, and reading one
   makes an absence invisible. The mitigation: a comment at each end pointing at the other
   ([`policies-approvers.tf`](../../terraform-live/identity/sso/policies-approvers.tf),
   [`data/README.md`](../../terraform-live/data-governance/data/README.md) §"A permission here is
   the intersection of two systems").

   Amended 2026-08-19 (Stage 5a pass 4c), because the lesson listed "an S3 bucket policy" and still
   did not fire. The intersection has a second trigger, which is not a service: the account
   boundary. Cross-account access requires an allow in the resource policy of the account that owns
   the object and an allow in the identity policy of the account that owns the principal. No second
   permission layer is involved; it is one IAM, whose evaluation rule changes from OR to AND at the
   boundary. S3 has no layer above IAM, so the case does not look like Lake Formation, and
   same-account intuition is wrong here: within one account a bucket policy naming a role is
   sufficient. The drop-box `PutObject` had lived since pass 1 with only its resource half, three
   correct statements naming the persona roles, and the stage file recorded that the missing
   identity half was *"correct rather than missing"*. The failure would have surfaced at the first
   attempt as an `AccessDenied` whose error names the half that is right. The discriminator: before
   claiming any permission works, ask whose account owns the object and whose owns the principal; if
   two accounts, "can you point at both grants?" is the evaluation rule. In review, a resource
   policy that names a foreign principal is by itself always incomplete, in every service, so it
   marks either an identity-side statement somewhere or a dead permission.

   Amended again 2026-08-20 (Stage 5a pass 4d, when the drop-box `PutObject` ran), because "the two
   halves" is the wrong arity on an encrypted write path: there are three. The write succeeded only
   because the identity half (`WriteIngestionDropBox`), the resource half
   (`AllowInteractiveWriterPutOnly`) and the lake CMK's key policy meeting `UseLakeDataKeyViaS3` all
   agreed at once: three policies in two accounts, one call. The third term is present on every
   write to a bucket with SSE-KMS default encryption, because S3 calls `kms:GenerateDataKey` with
   the caller's credentials. The first two halves announce themselves on failure; the key term
   surfaces as a KMS error about an action nobody wrote in the policy they are debugging, the shape
   the Athena `INSERT` failure took the day before (Lesson 34). On success the key term is the only
   visible one: the `PutObject` response echoes `SSEKMSKeyId`, naming the key and its owning
   account, while nothing in the response mentions the bucket policy or the identity policy. The
   third discriminator: is the target encrypted, and with whose key? A key in another account is a
   third grant on the same call. A successful encrypted write is read for its `SSEKMSKeyId` rather
   than its exit code, because that field is a positive proof of a grant that no failure elsewhere
   would have attributed correctly.

29. **An attribute assigned to describe a thing becomes a selector the moment somebody writes a rule
   over it — and the rule inherits every resource that wears the attribute for an unrelated
   reason.** Stage 5a pass 3 was one expression away from sharing the drop-box. The classification
   ontology gives `classification=internal` to the drop-box database for a considered reason:
   arrivals are user-supplied, and the fail-open default says an unclassified arrival is ordinary
   working data rather than invisible. The default consumer share was then written as
   `classification ∈ {public, internal}`, a sensitivity predicate, and sensitivity is not the
   question a share asks. A share asks whether people may read this, and the drop-box's answer is
   no: it is the letterbox whose contract is write, never read back. Two correct decisions, one
   accidental intersection. It was caught at the apply, by reading the expression against the
   catalog as actually tagged rather than against the model. A tag ontology read as prose looks like
   a taxonomy; read as a selector it is a set of `WHERE` clauses, and a value chosen for meaning A
   silently qualifies for rule B. Before writing any grant, SCP condition, ABAC rule or
   bucket-policy tag match, enumerate what currently carries each value and ask whether every one of
   them belongs in the result; only the inventory will tell you. The gate belongs on the axis that
   expresses the intent: the fix was not to re-tag the drop-box but to add the dimension the rule
   was about (`layer`), leaving each attribute saying the one thing it was chosen to say. The rows
   would not in fact have leaked, because the unregistered location blocks the read, and that is the
   argument to distrust (Lesson 5 in reverse): an unintended grant is a defect whether or not a
   later control happens to cover it, because nobody chose the coverage.

30. **A tool's failure is not a property of the world — and if it gets written down as one, the
   record carries the tool's limit forever.** Stage 5a pass 2 could not fetch AWS's Lake Formation
   pages: they are JavaScript-rendered and the plain fetcher returned no body. The handling was
   right in every visible way: the missing information was not asserted from memory, the gap was
   recorded, the question deferred to the stage that could measure it. But the caveat in
   `REFERENCES.md` said the pages "did not return a body to an automated fetch", which reads as
   *these pages cannot be read*, when the true statement was *this fetcher cannot read these pages*.
   One session later a rendering browser opened all of them in a minute, and the deferred question,
   whether the governance-manager persona can grant as well as tag, was answered by a sentence in a
   page nobody had failed to read, only failed to try. Before recording an unknown, name the
   instrument that failed and ask what a different instrument would see. An unread source is a gap
   in the record, not a fact about the source. The same shape sits behind an `aws` call that fails
   on the wrong profile, a plan that "cannot express" something the API supports, and a check that
   returns empty: each says something about the reach of the instrument first, and the world second.

   A second occurrence (2026-08-22) moved the limit inside the API's own contract. `US-8` read
   permission boundaries through `iam list-roles`, and `ListRoles` omits `PermissionsBoundary` by
   documented contract (`GetRole`-only, with `Tags` and `RoleLastUsed`), so the reading was a
   constant `null` for every role that had one. The check reported the estate's first real project
   role as unbounded while `get-role` showed the boundary in place. Reading everything the response
   returned is not enough; the field contract has to be read, because the drop happens at the API's
   end, not in the collection code (Lesson 31's "what did the collection drop?" one layer deeper).
   The defect survived from birth because no object existed that could falsify the check (Lesson
   13's shape stretched over time).

31. **A check inherits the scope of the account it was written in, and keeps reporting `pass` about
   that one while the design spreads past it.** `DL-6` decides whether Lake Formation's
   create-defaults still grant `IAM_ALLOWED_PRINCIPALS`, the reading D13 rests on. It was written at
   Stage 5a pass 1, when Data Governance was the only account with a `DataLakeSettings`, so it read
   `DATA_PROFILE`. By pass 4 two more accounts had one, both in the failing state, and the check was
   green. It answered its question correctly about a population that had stopped being the whole
   population. This is not Lesson 13, whose check cannot tell success from failure; this one
   discriminates perfectly and is pointed at the wrong set, which looks like evidence where Lesson
   13's failure looks empty and invites suspicion. A check's scope is part of its claim, so write
   the scope into the line it prints: `DL-6 (awsds-infra-dev)` can be falsified by counting
   accounts, `DL-6` cannot. The trigger to re-read every check is a topology change, not a code
   change: the day a second account gains a resource that only one had, every instrument that reads
   that resource is scoped until proven otherwise. Pass 3 wrote the debt down; it still shipped one
   session of a green check over two failing accounts, which argues for extending the instrument in
   the same sitting as the resource.

   The same mechanism also arrives as a false `FAIL` (2026-08-21, Stage 6 step 1.3). `US-2` asks
   whether a DataZone domain exists outside Data Governance. It counted the rows `datazone
   list-domains` returned in each account and treated any non-zero as *"a domain was created here"*,
   true in a world where nothing is shared. The account association shares one domain into the
   member accounts, so on the day the association succeeded the check went red in both, about a
   domain that had never moved. Two things generalise. The tell is cheaper than counting accounts:
   the failure arrived from the act that was supposed to work, so a check that goes red at the
   moment a step succeeds is audited before the estate is. And the fix is a discarded field, not
   scope: the collection built `(id, name, version, status)` and threw away the ARN, the one
   attribute carrying the owner. A check that infers a property it could have read (ownership from
   who is asking, instead of from what the API returned) is the shape to look for. Ask of any
   list-shaped check: what did the collection drop, and does the verdict depend on it?

32. **Two spellings of the same object survive indefinitely while nothing has to build it — and the
   side that has to build it is the one that was right.** For weeks the plan said both "scratch +
   derived-zone **buckets**" (`architecture.md`, `conventions.md` §6, the Stage 5a table) and
   "scratch and derived **prefixes**" (D13, `identity/sso/`'s owed-grants note, Stage 1b, the
   permission set's own description). Both entered in the same commit, so it was one object with two
   vocabularies, and neither spelling failed anything because no code had yet had to pick. The
   disagreement surfaced at the authoring, as a cost question: a second bucket needs either a third
   CMK the cost model does not carry or a key shared for no reason. The tie-break: follow the
   citation. All three "bucket" lines credited D19, which never mentions `scratch`; the origin is
   D13, *"non-registered prefixes (scratch, artifacts, model outputs) keep ordinary IAM access"*,
   where `scratch` names a class of thing beside `artifacts` and `model outputs`, not a resource.
   When two files disagree about what something is, the one closer to the mechanism wins: the IAM
   side had to name a resource in a policy, the topology side only had to draw a box. The cheap
   check is the citation itself: a claim that cites a decision which does not contain it is the
   copy, not the original.

33. **One intent enforced in two places diverges — and sharing the *values* while duplicating the
   *structure* is what makes it look like it cannot.** "Reachable only over the VPN" is written
   twice in this estate: `DenyOutsideTrustedNetworks` in the lake's bucket policy, and
   `DenyControlPlaneOffVpn` in the six persona permission sets. The resource half carries three
   branches (`aws:SourceVpce`, `aws:SourceIp`, `aws:PrincipalAccount`), because traffic can arrive
   by more than one path; the identity half carries one, `aws:SourceIp`. Stage 5a pass 4d measured
   the difference: tunnel traffic to S3 leaves through the `[P]` gateway endpoint carrying the
   WireGuard host's private address (`10.20.160.254`) and an endpoint id, while Glue and Athena
   leave by the internet gateway wearing the Elastic IP, so the identity half denies every direct S3
   call a persona makes from inside the perimeter, including fetching the person's own query result.
   The resource half was written against the measured topology; the identity half against the
   intended one. The trap is partial de-duplication: both halves read the Elastic IP from the same
   `[P]` state and neither pastes it, so the design looks like it has one source of truth. It has
   one source for the values and two hand-written copies of the branch structure, and the structure
   is where they disagree. Nothing compares them: `terraform plan` sees two unrelated documents, and
   each half is plausible on reading. When one sentence is enforced at two layers, ask whether the
   shape is derived or retyped; a shared variable inside two hand-written conditions is the most
   convincing disguise for a divergence. It survived because a deny is only debugged by the traffic
   it wrongly blocks: the bucket policy sits on the hot path, so an over-broad branch there breaks a
   legitimate read on day one; the identity deny fires only when someone is off-VPN, a case nobody
   exercises deliberately, so no apply, review or plan could surface it, and only a behavioural
   proof from a real session did. A control that is correct in the common case and wrong in the rare
   one reports healthy for as long as nobody tries the rare one. Two smaller shapes fell out of the
   finding. A guard can foresee the right symptom for the wrong cause: `permission-sets.tf` carried
   a `precondition` whose message predicts "deny every call from every network for all six
   personas", written against the address list arriving malformed, and nothing in it considers a
   well-formed list whose key is irrelevant on the path the traffic takes. And the proposed fix was
   aimed at the wrong list, the consumers' endpoints rather than the VPN home's, because
   `consumer_vpce_ids` is built along "who consumes the lake" and was being asked "what is on the
   network path"; the two intersect today by coincidence, since the single VPN home is also a
   consumer (Lessons 10 and 29 together).
   Closed 2026-08-20: the fix is applied and proven, and the proof shape is the reusable part. The
   third condition (`StringNotEqualsIfExists aws:SourceVpce` over the VPN home's gateway endpoints)
   went in, and the evidence was taken three ways. (a) The same call before and after: `s3api
   list-buckets`, the call whose CloudTrail record diagnosed the defect, moved from *explicit deny
   in an identity-based policy* to the implicit deny, one variable changed. (b) A contrast pair: one
   action (`GetBucketLocation`), two buckets, one session; the granted bucket succeeds, the lake
   bucket implicit-denies, which separates *"the network is blocked"* from *"this bucket is not
   granted"*, two hypotheses that had produced identical output under the over-broad deny. (c) Both
   provisioned roles, not the document: the defect belonged to a shared fragment, so the fix is
   proven only where the fragment lands, in the two accounts that failed identically. A deny
   debugged only by the traffic it wrongly blocks is also closed only that way; the apply proves the
   document changed and nothing more, so the fix and its behavioural proof belong in the same
   sitting. And while an unrelated explicit deny is in the path, every implicit deny behind it is
   unmeasurable, so a fix like this one restores the evidentiary value of every negative control
   downstream (here, D13's whole mechanism).

34. **A deferred obligation recorded only at the deferring end is a promise the receiving stage
   never gets — and a decision scheduled around an unexercised capability inherits a premise nobody
   measured.** The lake's registration role shipped read-only at Stage 5a pass 1, its comment
   deferring the write half to "Stage 9, which amends this policy (its step 2)", and Stage 9's file
   never carried that amendment. Meanwhile Stage 5a's own file scheduled a one-way-door decision,
   *load sample rows through Athena before 4.3's amendment closes that door*, on the belief that the
   in-account write path was open. Three files, three spellings of one capability: the plan said
   *open*, the code said *deferred*, the receiving stage said nothing, and all survived because
   nothing had exercised the path. This is Lesson 20's mirror: an unexercised allow-path is as
   unmeasured as an unexercised deny, and it fails the first time someone needs it rather than the
   first time someone attacks it. The first governed write attempted (2026-08-19) measured all three
   files at once: denied, the vended session naming `kms:GenerateDataKey`, and the mechanism side
   was the true one again (Lesson 32). The user's against-recommendation choice to load rows
   surfaced it in the cheapest configuration, one account, one role, one key, instead of inside
   Stage 9's cross-account job, where the share, the job role and two keys would all have been
   suspects. Two discriminators. When a comment defers work to a later stage, open that stage's file
   and write the obligation there in the same sitting (Lesson 4's state-in-one-place, for plans; the
   check is Lesson 32's citation test in reverse, follow the promise to its addressee). And before
   scheduling anything "before the door closes", try the door: both options of the sample-row
   decision described a door that was not there.

35. **Adopting an object into infrastructure-as-code silently invalidates every *procedure* written
   about it — and the adoption touches none of the files that carry those procedures.** Stage 2 step
   5.5 imported the ten Organizations policy documents into Terraform. Nothing about that commit
   reached `POLICIES.md` or the battery runbook, because adoption changes code and state, not prose
   about the object, so both files went on saying that an amendment is `update-policy` in place.
   Four days before pass 4e, that instruction was copied out of them into a stage file as the plan
   for the next act, wrong by a whole stage. Against Lesson 11: there a change of authorship
   invalidates claims, and the remedy is to re-read the decisions whose enforcement depends on it;
   here it invalidates instructions, and the remedy is to grep every prose file for a mutating
   command naming the object and correct it in the adoption's own sitting. A procedure has no
   revision trigger and no gate; `check-index.py` reads the documents' `Sid`s and would not have
   noticed, and neither would a plan.

   The failure shape earns the number. A stale procedure that errors is self-correcting; this one
   succeeds: `update-policy` would have returned cleanly, the document would have attached, every
   gate would have stayed green. The damage was one layer down: the tracked JSONs carry
   `<PLACEHOLDER>` tokens substituted at render time, and `awsds-org-scp-ou-data.json` carries
   `<ACCOUNT_ID_DATA>` inside the D27 crawler carve-out, so the hand-uploaded document would have
   held an `ArnNotEquals` comparing against the literal string `<ACCOUNT_ID_DATA>`: a carve-out
   matching no principal, no error at upload or evaluation, a control turned decoration (Lesson 5,
   by accident). Two guards exist against exactly that, `render.py`'s survivor check and
   `policies.tf`'s precondition, and the abandoned path uses neither: the guards were built into the
   sanctioned route, so leaving the route leaves the guards, and nothing announces it. While reading
   any procedure, ask whether it names a command that mutates a real object, and whether that object
   is still changed the way the text says; if the text predates the tree that now owns the object,
   assume it is stale until checked.

36. **"Auto-enable" is a word each service defines for itself — and a cross-service finding written
    down in the stage that hit it stays in that stage.** Found 2026-08-20, checking Stage 5a step 13
    against the service before running it: the third time this plan made the same assumption about a
    different service, and the second time it had already been corrected in writing.

    Three security services share a management shape: delegate administration to Audit, then turn
    the thing on for the whole organization. The semantics underneath are not shared, and this
    project has measured three answers:

    | Service | What "auto-enable" actually covers | Where it was learned |
    |---|---|---|
    | GuardDuty | `ALL` — existing accounts included | Stage 4, recorded; Stage 15 step 2 inherits it |
    | Macie | **new accounts only**; existing ones added one at a time by the administrator | Stage 11, corrected 2026-08-17 |
    | Security Hub CSPM | **new accounts only, current Region only** — so on an organization whose accounts all already exist, it covers **none of them** | Stage 5a step 13, corrected 2026-08-20 |

    The plan wrote *"auto-enable for existing and future accounts"* into Stage 5a because the shape
    was familiar from GuardDuty; nothing about the sentence looked like a guess, because the
    sentence next door had been true.

    The repair was not a different setting. For Macie the fix was "then add the existing accounts
    too": same feature, more work. For Security Hub the fix is a different feature, central
    configuration, with its own prerequisite (a home Region / finding aggregator), its own API
    family, its own console workflow, its own drift semantics, and an account-level API surface that
    is refused for accounts a policy governs. When a mechanism assumption turns out wrong, budget
    for the possibility that the thing the plan described does not exist, and that its replacement
    changes who runs the act, from where, and what else must be true first.

    The second half is about this repository. The Macie instance was found, understood and written
    down, dated, in Stage 11's Status row, because that is where it was discovered. Stage 5a's step
    13 then carried the same wrong assumption for three more days, because nothing routes a reader
    from "I am executing Stage 5a" to a paragraph in a sibling stage: `CLAUDE.md`'s routing table
    sends you to the stage you are executing and to the decisions it consumes. A finding about the
    stage's own subject belongs in the stage. A finding about a class of thing (a service family, a
    provider behaviour, a console pattern) belongs somewhere cross-cutting, here or in
    `docs/AWS_STATE.md`'s expectations, and in the stage; the waste is the third stage rediscovering
    it. While writing any correction down, ask whether the sentence would be useful to someone
    configuring a different service. If yes, the stage file is the wrong only-home for it.
37. **A sentence written in the perfect tense from an intention is, from that moment on,
    indistinguishable from a record — and all three of this project's have been authored in the
    commit that was about to make the reading available.** Promoted to a lesson on the third
    occurrence (2026-08-21), by the rule the second one declared: two instances are a pattern, a
    third in a different shape is a lesson.

    | # | The sentence | Written | Falsified | By what |
    |---|---|---|---|---|
    | 1 | a `CLAUDE.md` bullet describing the VPN host's state | Stage 4 | same day | reading the host |
    | 2 | *"step 0 is now runnable"*, Stage 6's Status row, commit `5df5a83` | 2026-08-21 | hours later | running step 0 |
    | 3 | *"**Pulled forward and applied before this stage:** `production/registry/` … and `production/pki/`"* | 2026-08-16 | five days and two full stage reviews later | auditing the prerequisite before executing it |

    All three were written by the same hand, in the same motion, and none was a lie: each was a true
    statement of what was about to be done, typed into a document, and then the doing either did not
    happen or came back with a different answer. The commit that carries the sentence is
    systematically the commit before the evidence exists: the ordinary sequence of writing the plan
    and then executing it.

    The third is the expensive one. A prerequisite in another account, owned by a stage that had not
    started, asserted once in one Prerequisites row. Nothing could catch it: `check-plan-refs.py`
    validates identifiers, links and sizes; `slices.py` validates the declared slice table against
    the tree and would not look for a folder nobody declared; `./aws/studio.py` never asks;
    `./aws/supplychain.py` reads ECR and the CA but gates its note→fail flip on a host two stages
    away, so it reports green over the absence. A false claim about state degrades gracefully:
    reading it produces no error, only the belief that something was done. Its only symptom was that
    the other files disagreed: the owning stage said "runs before Stage 6" in the future tense, a
    `.tf` comment scheduled the slice at Stage 7, and the decision's navigation row never listed
    Stage 6. Four statements, three tenses, no gate between them.

    The tell is cheap. This repository dates and grades its claims (*SATISFIED 2026-08-19*, *4d AND
    4e are DELIVERED (2026-08-20)*, *measured*, *0 FAILED*), so the question to ask of any
    perfect-tense clause is not "is this true?", which invites a re-derivation, but why this clause
    carries no date, no measurement and no delivery verdict when the clauses beside it in the same
    row carry all three. In case 3 that asymmetry was visible from the day it was written.

    Two practices, both nearly free:

    - Write intentions in the future tense and let the past tense be earned by a reading. *"runs
      before Stage 6"* and *"applied 2026-08-16, measured"* are both fine; *"applied before this
      stage"* with no date cannot be told apart from either.
    - Where prose cannot be checked, move the obligation into a structure that can. The repair here
      was a row in the pass table, a row in the build table, a sentence in the ordering paragraph,
      and a `layers.py` rank: four places an executor reads, against one row nobody executes from.
      Prose is where an intention and a reading part company, so stop asking prose to carry a
      dependency.

    The scope test: the risk is concentrated in claims about work outside the file's own stage or
    account, because those are the claims no gate reads and no owner re-reads. A stage saying what
    it itself did is checked by the next person executing it; a stage saying what another stage
    already did is checked by nobody.

38. **An identifier read out of prose is a claim, not a reading — and it travels further than the
   sentence that carried it.** Stage 6 step 1.3's table named the RAM permission the account
   association would attach: `AWSRAMPermissionDataZoneDefault`, *"never
   `AWSRAMPermissionDataZonePortalReadWrite`"*. Both names came from a documentation page's body
   text, read carefully and quoted accurately. Neither exists. `ram list-permissions --resource-type
   datazone:Domain` publishes six permissions and no name resembling either; what the console
   attaches is `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`. The decision the
   sentence expressed, no data-portal access, was right, available, and taken; only the proper nouns
   were fiction. The damage is where the wrong name ends up: by the time this was measured,
   `AWSRAMPermissionDataZoneDefault` had reached `docs/SMUS.md` twice and a comment in
   `terraform-modules/sagemaker-prereqs/blueprints.tf`, where it was the stated reason the blueprint
   resources live in the member account's slice. A name is the most portable thing in a document: it
   gets quoted without its hedge, survives every re-read because it looks like a fact, and ends up
   load-bearing in a file nobody re-checks against an API. This is not Lesson 16 (a wizard
   under-specified, fields the documentation does not name): here the documentation named something
   confidently and the API disagrees. Nor Lesson 23 (bind to contents rather than a name, about
   drift over time): this name never had a referent. The discriminator costs one command: every
   class of identifier this project quotes has an enumeration behind it (`ram list-permissions`,
   `aws iam list-policies --scope AWS`, a service's `list_*.html` action table, a registry's tag
   list). If a plan sentence names an AWS-published identifier, enumerate the namespace before the
   sentence is written; if the name cannot be enumerated yet, say *"the console's no-portal option,
   name unread"* rather than inventing the precision. The tell in review: a proper noun with no
   measurement date beside it, in a file whose neighbours all carry one (Lesson 37's shape, for
   nouns).

   Amended 2026-08-23: the more dangerous variant is a mechanism read out of prose and written down
   as a measurement. While extending the DNS Firewall allow-list on 2026-08-22, the question *does
   `*.name` reach a nested subdomain* was settled from a documentation summary and then recorded, in
   a module comment, a stage step, `REFERENCES.md` and a log entry, with the words *"measured rather
   than assumed"*. The claim happened to be true, which made it costly: it read as a closed
   question, so the next reader had no reason to ask what else governs a match, and the thing that
   governed it (the whole resolution chain is evaluated, so a listed name whose CNAME target is
   unlisted is blocked) went unexamined for a day while the fix it produced did not work. An
   identifier read out of prose stays a name; a rule read out of prose becomes the recorded
   explanation for behaviour nobody has watched. The tell is the word: "measured" is reserved for
   something this project ran, and a doc reading that says so is worse than an admitted guess,
   because a guess invites the measurement and a false measurement forbids it.

39. **What a console wizard fills and the authoring API does not require is still required — and the
   validator is the deploy and the teardown, so an incomplete object pins its dependents in both
   directions.** Stage 6's blueprint configurations were created through
   `PutEnvironmentBlueprintConfiguration`, which accepted objects missing three things the
   Enable-Tooling wizard always fills: the manage-access role, the projects-bucket `S3Location`, the
   `KmsKeyArn`. Nothing failed at Put time. Each absence surfaced only when a project tried to
   deploy an environment, and when a stuck project tried to delete one: teardown validates the same
   fields, so a project born under an incomplete configuration could neither finish nor be removed
   until the configuration was completed. Five portal attempts paid for the ladder one rung at a
   time (2026-08-22). This is Lesson 16 inverted: there a human at a wizard answers fields the plan
   never named; here no wizard was used, the API was the lax surface and the wizard was the de facto
   completeness specification. When automating an act a console wizard also performs, enumerate the
   wizard's fields and treat every one as required, whatever the API's schema says. The second face,
   from the same sitting: the strict validator arrives one act late. `CreateProjectProfile`
   validated nothing against the blueprint templates (a locked `lifecycleManagement = "true"` sailed
   through where the template's enum is `ENABLED`/`DISABLED`) and the error arrived from
   CloudFormation at the first deploy; then `UpdateProjectProfile` validated what Create had not
   (required template parameters with no default). An authoring API that accepts an object proves
   only that it parses; the act that has to build or redeclare it is the real validator (Lesson 32
   as a lifecycle rule), and the templates were downloadable all along (Lesson 38: check locked
   values against the template, never against prose). Validation deferred past the authoring act
   lands on a destructive or irreversible act, so the defect is discovered where it is most
   expensive to hold: a system that cannot deploy and cannot tear down.

40. **The door a call takes is a fact of resolution and routing — the service's endpoint roster
   predicts nothing, and an endpoint's private zone answers for its whole subtree.** One sitting
   measured three doors and a no-door, from one laptop on the tunnel (2026-08-23/24). `sts` left
   through the interface endpoint: private DNS had hijacked its name, so a deny keyed on gateway
   endpoint ids denied a call that was on the VPN. `s3control` left through the S3 gateway: it has
   no interface endpoint here, which a derivation turned into "so it rides the IGW", and CloudTrail
   refuted; a gateway route matches a prefix list, `s3-control.<region>` resolves inside `pl-s3`'s
   ranges, and "has no interface endpoint" says nothing about the IGW.
   `agent.datazone.<region>.api.aws` left through nothing: the `datazone` endpoint's private hosted
   zone is authoritative for the entire subtree of the name it serves, holds only the apex, and
   answers NXDOMAIN for every subdomain that exists only in public DNS, with no fallback, for every
   client of the VPC resolver, the full-tunnel laptop included. The roster is a list of what AWS
   sells; resolution is what this VPC does, and only the second is a fact here. Both are measurable
   for a cent: `dig` from inside, `vpcEndpointId` in CloudTrail. The subtree half is the sharp edge:
   `PrivateDnsEnabled` reads as "this name now resolves privately" and means "this subtree now
   resolves only here"; the blast radius is every name under the service name, including ones the
   vendor's own front-ends need (the SMUS portal's `agent.datazone…`, documented
   public-internet-required, went NXDOMAIN and broke the portal on the VPN). No allow-list sees it:
   the DNS Firewall filters queries, and these queries were answered, authoritatively, with nothing.
   Distinct from Lesson 3, which is about policy conditions anchored on `[E]` endpoint ids; this is
   the path itself mispredicted from the roster. The design-B corollary: a design that multiplies
   interface endpoints multiplies authoritative private zones, each shadowing a subtree, a cost no
   endpoint price list carries.

41. **A vendor "required" travels without its premise — and the page that says required can carry,
   lower down, the table that contradicts it for your design.** `datazone` entered both Interactive
   endpoint lists on one comment: *"the SMUS network-isolation page marks it REQUIRED under VpcOnly,
   so an app cannot reach the domain without it."* Three errors in one sentence, all checkable from
   the page (2026-08-24). The premise is swapped: the page never says `VpcOnly`; its required table
   is scoped by the page's own isolation definition, *"access to the public internet is denied from
   the Amazon VPC"*, which is design B. The consequence is refuted by the page (*"network calls …
   route over the public internet when that network path is available"*; design A has that path,
   with `datazone.<region>.api.aws` allow-listed), by this estate's history (six of the fifteen
   "required" endpoints have never existed here and the create path closed end to end), and by the
   page's own troubleshooting table (*"Private with NAT + Private with NAT: Works as expected. No
   action needed"*). The same page carries a third table two prior readings never recorded, *Public
   internet access*: the portal's client assets, its client APIs (`agent.datazone.<region>.api.aws`
   among them) and the IdC sign-in endpoints require the public internet, so one page instructs the
   endpoint and requires a name that endpoint's private zone shadows. Where the tables collide, the
   browser-facing one wins: a portal is a web client, and no interface endpoint serves a web
   client's edge. "Required" is always required-under-a-premise, and the premise is what falls off
   in transit (Lesson 38's failure for names, applied to a requirement's scope). The comment even
   declared itself, *"the ONLY entry added from that page on faith"*, and the self-award of an
   exception is not a discharge: an entry marked "on faith" is a scheduled defect, and of the whole
   list it was the one that broke. When copying a "required" row, copy the sentence that scopes the
   table, and read the whole page; the contradicting table sat three scrolls down a URL this
   repository had already cited twice.
   Second instance, 2026-09-05 (the 6b-6d review), and it nearly bought a NAT gateway. The MWAA
   Serverless networking page states that a workflow's subnets *"must have a route table to a NAT
   device (gateway or instance)"*; read alone, that makes orchestration D38's first named exception
   and puts a ~USD 36.50/month standing line into a USD 50 estate. The premise is the section
   heading: that list scopes *"Public routing over the internet"*, and the next section, *"Private
   routing without internet access"*, requires the opposite, *"must not have a route table to a NAT
   device … nor an internet gateway"*, with three interface endpoints and a self-referencing
   security group instead. When a vendor page offers two topologies, the requirements list you hit
   first belongs to whichever one it is under; the tell is a "required" whose premise names a
   network shape nobody checked against ours.

42. **A permission failure is a response; a network failure is the absence of one — and CloudTrail
   separates "denied" from "never arrived".** The on-VPN portal break arrived with a plausible
   cause: the same week had re-keyed `DenyControlPlaneOffVpn`, so the deny was the suspect. The
   symptom had already ruled it out. An IAM deny is an answer (HTTP 403 with a body, a console
   naming the policy family, a CloudTrail event carrying `errorCode`), because the request reached
   the service and was evaluated. The browser's *"Failed to fetch"* is the opposite shape: `fetch()`
   rejecting before any HTTP exists (DNS, TCP, TLS, CORS), which no policy can produce. The
   discriminator costs one query: CloudTrail held 45 events from the home address and zero from the
   tunnel, same portal, same minutes. Zero events is not a deny; a deny leaves an event. The
   suspected policy was never evaluated, because nothing arrived. Classify the failure by what came
   back (a body, a refusal, or silence) before opening any policy document, and let CloudTrail's
   presence or absence split the last two. The suspect also failed the sign test: the re-keying was
   permissive for the suspected path. This is Lesson 24's channel discipline pointed at a different
   pair: not benign-vs-serious wordings of one denial, but denial-vs-no-arrival, which no wording
   can distinguish because one of the two has no words.

43. **A browser is a term in the reach question, and its policy is one no AWS instrument can read —
   so every gate in the estate stays green through a total outage.** Removing the `datazone`
   endpoint discharged the NXDOMAIN shadowing of 2026-08-24, and the portal on the tunnel then
   failed with the identical words, `TypeError: Failed to fetch`, on the catalog tab and on the
   JupyterLab space. The surviving endpoints' private zones were answering correctly (the whole
   `*.studio.<region>.sagemaker.aws` subtree, `glue`, `lakeformation`, `athena`, all to
   `10.20.x.x`), the design working as intended. But the portal is a public origin, and a browser
   gates a public page's request to a private address behind a permission (Chrome's **Local Network
   Access**); ungranted, `fetch()` rejects before any HTTP exists. `curl` from the same laptop, the
   same minute, reached every one of those addresses; it implements no such policy. Everything this
   repository owns read clean throughout: `DN-1` 43/43, the DNS Firewall allowing, CloudTrail
   silent, `dig` answering, `terraform plan` empty. The only instrument that could see it was a
   person clicking a permission. CloudTrail could still attribute it afterwards, and that is the
   reusable move: the calls that succeeded after the grant name what was failing before it. The
   catalog tab resolved to Glue at the `glue` endpoint, the JupyterLab launch to the SageMaker API
   at `sagemaker.api`, both arriving from the VPN host's private address, while the ~25 minutes of
   the outage held zero arrivals. The trail cannot see a browser-side refusal, but the shape of the
   recovery identifies it: read the first successful minute to learn what the silent minutes were
   trying to do. Lesson 28 said reach is an intersection; the intersection does not stop at AWS.
   When a control plane's client is a browser, its terms join the product (origin classification,
   CORS, private-network gating, mixed content, cookie partitioning), and they share a shape: they
   are properties of the requesting document's context, so they are invisible to the account,
   invariant under IAM, and untestable by any harness that speaks HTTP without being a browser. Two
   structural corollaries. A full-tunnel client resolving through a VPC that holds interface
   endpoints has been moved into those endpoints' address space without anyone deciding to: every
   public web console for those services inherits the gate, as a side effect of a DNS setting made
   for the compute plane. And the fixable case was the exception: `datazone` could be deleted,
   `sagemaker.studio` cannot, so the class is in general repairable only by moving the client off
   the resolver (open question 23). A per-origin browser grant is the interim, and it is not
   infrastructure: no gate asserts it, no state file holds it, and it dies with a browser profile.

44. **What peering shares is an address, never a path — and a topology drawn as boxes and lines
    hides exactly that.** (2026-09-05, while the single-egress hub was being designed.) The request
    was ordinary and, drawn on a whiteboard, correct: one internet gateway in a hub VPC, one NAT
    gateway behind it, every other VPC reaching the internet through it. AWS forbids all three legs
    of that sentence: a peered VPC cannot use its neighbour's internet gateway, NAT device or
    gateway endpoint, peering is not transitive, and a peering route may carry only the peer's CIDR,
    so the drawing describes a path that silently blackholes rather than erroring. A connectivity
    primitive advertises what it joins, not what it forwards, and every "shared" gateway behind it
    is an assumption nobody wrote down. The tell is a design in which one VPC's resource appears in
    another VPC's route table as a destination of last resort: `0.0.0.0/0` toward a peering, a
    shared NAT, a gateway endpoint "for the estate". What survives the constraint is anything with
    an address (an instance, an interface endpoint, a load balancer), which is why the single egress
    became an explicit proxy and every spoke lost its default route. Two second-order effects to
    expect: the constraint enforces an isolation rule for free (two VPCs with no direct peering have
    no path, whatever the hub does), and it moves the whole filtering problem up a layer, where a
    proxy that will `CONNECT` to a private address is a bridge between the VPCs the topology was
    keeping apart. The repository already held the rule: Stage 3 step 6.5 wrote it down on
    2026-08-16 and `NT-4` measures it. It was known, tested, and still designed around, because it
    lives in a stage file nobody re-opens while drawing a new topology.

45. **A default that reaches the internet is a dependency nobody declared — and removing the route
    is what turns it from invisible into fatal.** (2026-09-05, reviewing Stages 7-15 against the
    single-egress design.) Three of one stage's six documentation corrections were the same shape.
    GitLab Omnibus enables Let's Encrypt automatically whenever `external_url` is HTTPS, and retries
    it on every `reconfigure`; on a `.internal` name behind a proxy that is a failing reconfigure,
    for ever, and the failure names ACME rather than the design. ECR's pull-through cache documents
    that the first pull *"may require a route to the internet"*, and offers as remedy a public
    subnet with an internet gateway, the thing the design removed. A `PythonOperator` in a workflow
    whose workers AWS documents as having *"no route table to a NAT device… nor an internet
    gateway"* has no path to PyPI. A managed component's convenience defaults were written for an
    estate with egress, so each is a latent outbound call, and a design that removes the route
    converts a silent success into an unexplained failure. It surfaces late: the proxied estate
    works for everything anyone thinks to test, and the defaults fire on the paths nobody drives by
    hand (a renewal, a first pull, a cold start). Three habits, only the third cheap: read a
    product's defaults page, not only its configuration page, before putting it behind a proxy; make
    the refusal legible on purpose (an explicit proxy answers 403 naming the host, which is a
    finding, where a missing route answers with a timeout, which is not: Lesson 42); and prefer a
    lint over a runtime discovery wherever the dependency is expressible in the artifact, which is
    why the workflow lint rejects an operator rather than the network rejecting a packet.

46. **A command whose output you redirect or pipe hands you the exit code of the pipe, not of the
    command — and the next step then runs on a failure you never saw.** Three times in one session
    (2026-09-06, Stage 6b/6c): a `git commit … | grep` swallowed a hook failure and the `git tag`
    that followed landed on the wrong commit, burning a published tag that a runbook forbids moving;
    a pair of `terraform apply … >/dev/null 2>&1` left two hosted zones silently uncreated,
    discovered only because a later listing was short; a `git commit && echo pushed` reported
    success while the commit had been rejected. The carelessness is about the shell, not the
    command: `cmd | grep` exits with `grep`'s status, `cmd >/dev/null 2>&1` throws away the sentence
    that says what happened, and `&&` then chains off a truth that is not the one you meant. Never
    chain a consequential act (`tag`, `push`, a second `apply`) onto a command whose output you
    filtered: run it, read it, then act. Where a loop must summarise many commands, have it print
    the exit code beside each line rather than the output it matched. The expensive half is that the
    failure is discovered later, attributed to something else, after the intermediate state has been
    published.

47. **A process waiting on stdin looks exactly like a slow one, and the lock it holds makes the
    symptom appear somewhere else entirely.** A `terraform plan` was backgrounded with one generated
    variable missing; with no terminal to prompt at, it waited eleven minutes holding the S3 state
    lock, and every reading of the problem came from other commands, in other slices, failing with
    `Error acquiring the state lock` and naming a lock id, a host and a timestamp that explained
    nothing. The diagnosis ran backwards: find the lock, find the process, discover it is blocked
    rather than slow, then find the missing input. `-input=false` is the whole fix; it converts an
    unanswerable prompt into an immediate, self-describing error, and it belongs on every
    non-interactive plan and apply, not just the backgrounded ones. Any tool that can ask a question
    must be told it may not, before it is run somewhere it cannot be answered. Cheaper still: when a
    lock error names a timestamp, look for a live process before force-unlocking, because an
    orphaned lock and a running command have identical error text and opposite correct actions
    (Lesson 13, at the level of an operator).

48. **A name that another account resolves by is a cross-account contract, and no id-shaped gate can
    see it move.** Stage 6c step 1.1 re-labelled a VPC's `Name` tag; its gate was *"any id in the
    replacement list stops the step"*, every id was unchanged, and the step passed. Two other
    accounts looked that VPC up by tag (`data "aws_vpc"` with a `tag:Name` filter), and from that
    apply until somebody happened to run a plan in one of them, both were broken with `no matching
    EC2 VPC found`. The failure surfaced through an unrelated command in a different account, hours
    later. Lesson 3 says a resource moved across a boundary invalidates every condition that
    referenced it; this is its quieter half, a resource that did not move at all, whose name did,
    with the citation living somewhere the change's own review never opens. The trigger is a rename
    of anything selected by tag, name, alias or path rather than by id. Before applying one, grep
    the whole tree for the old string, and treat every hit in another account's slice as part of the
    same commit.

49. **A comment saying a knob is never turned is a claim about the callers that existed when it was
    written.** `vpc-egress`'s `core_services` reads *"Overridden never — the per-role differences go
    in `extra_services`"*, and it was right: every caller served a VPC people work in, where those
    eight endpoints are what a notebook cannot function without under design B. Then a VPC arrived
    with no workload at all, and obeying the comment would have billed 0.080/h of interface
    endpoints for a network nothing runs in. The comment did not become wrong; its premise stopped
    applying, the same shape as a vendor "required" travelling without its premise (Lesson 41) and a
    rejected-on-cost option going stale (Lesson 7). An absolute in a module reads as a constraint
    and is only a default with an argument behind it, so the argument is the thing to re-read; when
    it does not apply, override it with the exception written where the override is, not where the
    comment is. A module that meant it would have made the value a `local`.

50. **A check written to a stage's final expectation is red for every pass until that stage ends —
    and a check that is red for four passes is a check nobody reads on the fifth.** Four instances
    in two days (2026-09-05/06): `deploytargets.py`'s `DT-8` compared a Staging mirror against the
    lake and reported `DIVERGES` because Stage 9 has not built the mirror; it had never been green,
    only skipped, and the moment a profile made it runnable it went red and would have stayed so
    through four stages. Stage 6c's `1.5` would fail on three internet-gateway routes that pass 5
    removes; its `NT-12` would fail on a zone family step 2.6 retires; its `NT-11` would fail
    between the two steps that create a peering and route it. A stage is a sequence, so "the
    expectation" is a moving target, and a check asserts a single value. Three ways out, in order of
    preference: give the check a discriminator that separates *"not built yet"* from *"built wrong"*
    (`deploytargets.py`'s `built` flag is the pattern; the signal is usually the presence of any
    object the later stage creates); write the check at the pass that makes it true, which costs
    only the discipline to leave a gap in the plan; or name the intermediate state as a dated,
    expected exception that a named step removes. The fourth option, what happens by default, is
    never acceptable: ship it red and rely on a human to remember why. *"The thing is missing"* and
    *"the thing is wrong"* are opposite findings, and a check that gives them one verdict has
    stopped being a check (Lesson 13, over time rather than over outcomes).

51. **Two intents sharing one list stay identical until the day they must differ — and then a change
    made for one silently makes it for the other.** Lesson 33's mirror, and the more dangerous half:
    33 warns that one intent enforced in two places diverges; this is two intents enforced in one
    place, which never diverges and cannot express a difference the design later requires, so the
    first change that needs one takes it from both. Stage 6c step 3.1 retired a peering, and the
    same `local.peer_vpc_ids` that named who a VPC peers with also named whose VPC its DNS zones are
    associated into. Those were the same set for three stages. Left conflated, the retirement plan
    would have destroyed a zone association nobody was thinking about, inside a plan whose headline
    was peerings, and it would have read as correct in review because every line in it was about a
    peering. The tell is a list whose name answers one question while a second reader asks it
    another (`peer_vpc_ids` consumed by a `zone_peer` local). The test: name each consumer and ask
    whether a row could ever be true for one and false for the other. If yes, the list is two lists
    whether or not it has diverged yet; *"a DNS association is not a path"* is the sentence that
    made this one obvious. Second instance, 2026-10-12: `production/registry/`'s output
    `ecr_repository_arns` fed both the build runner's push statement and Sandbox's SageMaker image
    role. Stage 7 step 5.b added `awsds-prod-ecr-app-etl` for the runner, and the next plan of
    `sandbox/dev-env/` proposed granting the image role read on it; the role now names its two
    repositories by key.

52. **A wait whose only exit is success waits forever once the thing it waits on is gone — and its
    silence is indistinguishable from patience.** Stage 6c step 4.8 polled two `until` loops for a
    cloud-init line on instance `i-0b04…`; the next step `-replace`d that instance, and both loops
    went on asking a terminated host for its console output every 15 and 20 seconds, indefinitely.
    They were found by the user noticing, not by anything in the repository, for the second time in
    one session, after the 3h33m `terraform plan` of Lesson 47. Same symptom, unrelated causes: one
    was blocked on stdin, this one was polling a corpse, and from outside both look like work in
    progress. The defect is the loop's shape: an `until <success>; do sleep; done` has no branch for
    the world changing underneath it, so every failure mode collapses into "not yet". The `Monitor`
    tool documents the same trap for event filters (*"if this process crashed right now, would my
    filter emit anything?"*), and an `until` loop is that question with the answer fixed at no. Give
    every wait a second exit (a deadline, or a check that the subject still exists) and prefer a
    condition on something that outlives the step: `terraform output -raw instance_id` re-read each
    round, never an id pasted at the top. The estate-level guard this argues for does not exist:
    nothing looks for a `terraform` process older than an hour, a `.tflock` with no live owner, or a
    poll loop outliving its subject, and two incidents in one session is the evidence for it.

53. **Two systems that express the same intent in the same-looking syntax are not translatable by
    transcription — and the failure is a refusal that reads exactly like a missing entry.** Stage 6c
    step 4.9 moved an allow-list from Route 53 DNS Firewall to Squid. Both take domain names; both
    use a leading token for "and subdomains"; the meanings do not line up. In DNS Firewall
    `example.com` is the apex only and `*.example.com` is subdomains and not the apex, so covering a
    name needs both. In Squid `example.com` is that exact host and `.example.com` is the domain and
    every subdomain, so `.example.com` alone is the whole answer, and listing both is fatal.
    Transcribing the asterisks would have produced entries matching nothing; transcribing the pairs
    took the proxy's first boot down to an empty allow-list. The two syntaxes agree on the easy
    cases (a bare hostname works in both), so a spot check of five entries passes and the sixth
    differs. Translate by asking what each side means by "covered", entry by entry, and put a gate
    on the collision the target rejects; a list that came from another system carries its grammar
    in, and every future addition copied from that side carries it in again.

54. **A program that has never been run is a claim, and `validate`, `render` and `run` are three
    different verdicts — passing the first two says nothing about the third.** Stage 6c pass 4 wrote
    a module, two slices and three templates. `terraform validate`, `tflint`, `checkov` and a
    careful re-read were green on every one, and seven defects were still there. Three fell out when
    the templates were rendered: `+` is arithmetic and not concatenation in HCL; `%{` is
    `templatefile`'s directive marker and collides with Squid's own `strftime` escape, and then with
    the comment written to explain the first collision; a "revert" path deleted the new file while
    the old one was already overwritten. Four more needed the thing to run on a host: an allow-list
    that would not parse, an error the script swallowed, a State Manager association that raced
    `dnf`, and an instance size that fit the steady state and not the build. None is exotic; they
    are the ordinary distance between "the syntax is well-formed", "the output is what I meant" and
    "the world accepts it". Render every template with real values before applying (a throwaway
    `templatefile` in a scratch directory costs one minute), and treat the first successful boot,
    not the first successful apply, as the moment a `[D]` slice is evidence rather than intent.

    Stage 6e, 2026-09-12, adds the case where `validate` is not silent but affirmative. `vpc-egress`
    v0.12.0 to v0.14.0 built each endpoint's policy with
    `scope == null ? st : merge(st, { Action = scope })`, whose branches disagree on the type of one
    attribute - `"*"` against a list of strings. `terraform validate` answered `Success!` in the
    module directory and again in `sandbox/egress` fully initialised at the tag, because a
    statement's type stays dynamic while the keys of a `for` over a computed map are unknown. They
    are known at plan, and the same directory then produced the error once per endpoint on the first
    `make up`. Neither `make check` nor the commit hooks read a plan, so three module versions
    reached origin and a caller was committed against them with no gate that could have seen it. A
    module change is exercised by planning a caller against the local path (`terraform-changes.md`
    Recipe B step 1), never by validating it.

    Stage 6i, 2026-10-11, adds a procedure documented for an environment it had never run in. The
    runbook's J1 told the reader to run `package-uv-job.py` from a clone "in a space, where uv and the
    project's storage are both at hand", and every measurement behind it was the laptop's. The first run
    in a space stopped before the script's first line, on the repository's `.python-version`
    (Lesson 65), and past that the space had no CPython 3.13 that uv could find. A sentence naming an
    environment is a claim about that environment until a run there makes it a reading.

    Stage 8, 2026-10-15, adds a job that cannot run before the release it gates. `awsds/dev-env`'s
    `release-gate` runs only on a protected tag, after a steward starts it by hand. GitLab's CI Lint, the
    offline check and every branch pipeline were green, and the job's first run was the release
    `default-v0.7.0`, after a 16-minute build: bash stopped on an apostrophe inside
    `${BASE_DIGEST:-...}`, and the registration behind it was skipped. The fix needed a new tag and a new
    build. A lint reads the YAML and no shell, so `check-gitlab-ci.py` now reads every script item with
    `bash -n`; a job that only a release can start is read offline, or its first run is the release.
    The same release met a configuration proven by the wrong reader. The deploy runner's boot checked
    its own AWS profile with the AWS CLI, which ignores a `credential_source` that has no `role_arn`,
    while the registration reads it through Terraform, which refuses that shape. A run of Terraform on
    the laptop found it before the gate. A file read by two clients is proven only for the client that
    read it.

55. **A refusal the sender cannot see is indistinguishable from silence — and the refusal is real.**
    [Lesson 42](#) separates a permission failure, which is a response, from a network failure,
    which is the absence of one. This is its mirror and the harder case: there is a response, and
    the sender discards it by policy, so it observes absence anyway. Stage 6c step 6.1, 2026-09-07.
    The VPN host's `FORWARD` chain rejects every tunnel packet not bound for RFC1918 with
    `icmp-admin-prohibited`, and this repository's runbook predicted the client would see *"a fast
    refusal, not a timeout"*. The client saw `curl: (28) Connection timed out after 15006 ms`. Both
    are true: measured the same hour, the reject rule had fired 8453 times. The mechanism this
    lesson first named, *macOS ignores an ICMP unreachable arriving mid-`connect()`*, was wrong;
    step 6.4 measured the real one the same day. The host rate-limits its ICMP errors per
    destination (`icmp_ratelimit`), and a laptop whose background applications are refused several
    times a second starves the bucket: of 27681 rejected packets the host had spoken 4366 and
    silenced 23318 (`OutRateLimitHost`), so a given SYN gets its ICMP or does not by the luck of a
    token, and when one arrives macOS honours it at once (`curl: (7) … after 194 ms`). The sender
    still cannot tell a starved refusal from a black hole. What generalises is where the evidence
    lives: not in the client's error, which has nothing to read, but in the counter on the refusing
    side, and a packet count is also what separates *the rule is present* from *the rule is hit*.
    When a control is expected to answer rather than drop, write the verification against the
    enforcing end, and treat any prediction about what the sender will observe as a claim about
    someone else's stack, which this project measures rather than reasons about.

    Stage 6i decision 7, 2026-10-11, is the same shape one layer up. A workflow with a `Code` object
    failed before its first task with "Execution environment preparation failed due to an internal
    server error", which names no control, no principal and no bucket. The refusal was real, and it
    lived on the refusing side: the VPC's S3 gateway endpoint denied `airflow-serverless.amazonaws.com`'s
    `GetObject` of the service's code snapshot, and only a trail of network activity events recorded it
    (`VpceAccessDenied`), naming the bucket, the principal and the policy type. The sender's error had
    nothing to read; the enforcing end's log was the reading.

56. **A configuration line that names a capability the surrounding configuration does not have is
    inert, and it reads exactly like a working control.** Stage 6c, 2026-09-07. Every client config
    in this estate carried `AllowedIPs = 0.0.0.0/0, ::/0` from the first day, and three documents
    (the runbook, the stage file, the objectives' reading) described IPv6 as *"deliberately
    black-holed"* on the strength of it. It was not routed anywhere: `wg-quick` installs routes only
    for the address families the interface has an address in, and the `[Interface] Address` line was
    IPv4-only. So `::/0` selected nothing, no IPv6 entered the tunnel, and every IPv6-capable
    application on the device went out of its own uplink, outside the tunnel, the proxy and the
    access log. Nine established connections were doing it, including the one carrying the session
    that found it, and the discovery came from the user noticing that a chat kept working while
    nothing else did. The tell is a directive that depends on a second setting to mean anything,
    where the second setting lives in a different part of the same file, or a different file, and
    has a permissive default. `AllowedIPs` needs `Address`; a Squid `http_access allow src dst`
    needs the `dst` acl to exist; a masquerade rule needs a route to send it traffic (Lesson 28's
    shape one layer down). Verify a routing directive by reading the routing table, never the config
    that was supposed to produce it: `netstat -rn -f inet6` answered in one line what three
    documents had asserted for three weeks.

57. **A paraphrase in a plan becomes the specification, and it is the plan's own words that make it
    look authoritative.** Stage 6c step 4.9 wrote *"the tunnel range carries the institutional web
    filter — what a person on a company laptop may reach"*, and told the executor to seed it from a
    vendor's table. `objectives.md` says the opposite in two places: the client's internet is
    monitored, and *"the restriction is on the SageMaker-managed compute, never on the user's
    (client's) machine"*. Because the proxy's configuration is default-deny, *"filter"* was
    implemented as an allow-list, and the client's internet ended up stricter than the compute's,
    the requirement inverted. Nobody noticed until a browser tried it: the AWS console opened and
    nothing else did. `CLAUDE.md` already carried the rule that would have prevented it (the
    objectives are *"the specification a stage is measured against, so it is summarised nowhere"*),
    and the summary was written anyway, in the file an executor opens. An institutional web filter
    is a deny-list over an open default; the paraphrase dropped the shape and kept the word. Before
    implementing a step that restates a requirement, open the requirement. The tell is a step that
    explains why rather than only what: an explanation is a paraphrase, and a paraphrase of a
    specification is a fork of it. A vendor's sentence forks the same way. ECR's page says the
    creation role *"must be provided when using repository tags and/or KMS in the template"*;
    `registry/cache.tf` carried it as *"a CMK in a creation template needs a custom role"*, kept the
    tags, and every first pull through the cache read `not found` (Stage 7, 2026-10-12).

58. **Data and code can share a delivery path and still have different costs, and the one that
    reports success is the cheap one.** Stage 6c, 2026-09-07. The proxy's allow-lists are `[P]` data
    in an SSM parameter, re-rendered onto the host by a State Manager association every half hour, a
    design bought so that a list edit needs no host replacement. A change of shape to those lists
    needed a change to the renderer, and the renderer is a script written by user data: `[D]` state
    on the disk. The parameter was updated, the association was triggered by hand, and it reported
    `Success`, for running the old script perfectly. The new plane did not appear, and the only
    evidence was the old `jq` expression still on the host. A reload path covers the artefacts it
    was built for and nothing else, and its success is a statement about the mechanism, not the
    outcome. Name the two classes where the mechanism is documented (this reaches the host in thirty
    minutes; that one needs a new host), because the failure is silent in the most convincing way
    available: a green status.

59. **Changing where a value is read from can change when it is knowable — and every guard that
    reads it moves with it, silently.** Stage 6d step 8.8, 2026-09-09. The `NO_PROXY` generator was
    repaired by reading `aws_vpc_endpoint.dns_entry` (every name an endpoint answers for) instead of
    `data.aws_vpc_endpoint_service.private_dns_name` (the service's one canonical name). Correct on
    the question it was asked, with a second effect nobody was asked about: a data source is known
    at plan time and a resource attribute is not. The DNS Firewall coverage precondition, one file
    away and reading the same local, stopped being evaluatable at plan on any VPC whose endpoints
    did not exist yet. Terraform did not complain; it deferred the condition to apply and printed a
    clean plan. Measured on a torn-down slice: `20 to add`, `no_proxy = (known after apply)`, and
    nothing raised, where the same code with a missing family used to fail before a single resource
    was touched. The repair had produced Lesson 39, the strict validator arriving one act late, in a
    step written to remove a different defect. A reading has two properties, its content and its
    timing, and a change of source usually changes both. The fix kept both readings: the narrow,
    early one beside the complete, late one, as two conditions naming their own reading, so a
    failure says which half found it and whether a plan could have found it at all. Before swapping
    the source of a value, list what else reads it and ask when each needs an answer.

60. **A full-replace update API turns every field you did not pass into a deletion — and the
    object's creator may have injected state that no field of that API can restore.** Stage 6d,
    2026-09-10. `mwaa-serverless update-workflow` was called with three of its eight fields, to
    change one line of a workflow's definition. It dropped the `NetworkConfiguration`, the two
    subnets and the security group that had put the workers in the private tier since the workflow
    was made, and replaced the logging configuration with a service default, orphaning a log group.
    Both were recoverable by re-passing them; a third loss was not. The workflow had been created by
    the portal, which injects the domain and project into the worker's environment, and the API
    update severed that: the next run died on `Project ID not found in environment`, with no field
    in `update-workflow` to put it back. It had to be re-expressed inside the definition. The tell
    was an absence, and it needed a negative control: the task failed in seven seconds with no event
    in CloudTrail at all, where the same failure a fortnight earlier appears twice, and the trail
    was proven current by finding the operator's own calls in the same window. A failure that
    reaches no API is a failure before the API, which is where a dropped network configuration
    lives. Two habits: read the whole input skeleton before calling any `update-*` and pass every
    field the object currently has (`--generate-cli-skeleton` beside a `get-*` is the diff); and
    treat an object authored by a console or a portal as jointly owned, since the API is not the
    same surface, and the part you cannot see is the part it will not give back.

---

## Lesson 61 — a procedure that depends on a file it did not create runs only for its author

**What happened.** Twice on 2026-09-10/11, a hand-over named a file in `$HOME/tmp` that an earlier
sitting had produced: first the domain settings kept as a rollback, then a detach file generated in the
assistant's own session. Both commands were correct and neither was runnable — the first because a
rollback is only true while nobody else has written, the second because the file was simply gone by the
time it was needed.

**Why it is a class rather than a slip.** A procedure is written by somebody who has the file in front
of them, and the missing step is invisible from there: the author's own shell is the hidden input. The
failure lands on the next person, or on the same person a week later, and it lands at the moment the
procedure is being trusted.

**The rule.** A procedure names a file outside the repository only when the procedure itself creates it,
in a step the reader can see. The generating command and the consuming command travel together. A file
kept from an earlier step is a rollback for that sitting and an input to nothing.

**Where it bites hardest**: a full-replace API, where the stale file is not merely unavailable but
*wrong* — it overwrites the present with a picture of the past, and no error names the fields it
dropped (Lesson 60's neighbour).

## Lesson 62 — an absence is evidence only when the instrument would have shown the presence

**What happened.** Twice on 2026-09-11, inside one hour, a conclusion rested on silence and the silence
was the instrument's rather than the world's. First `ls ~/.vscode-server/bin` returned nothing and was
read as *no Microsoft server in the space*: the current layout is `~/.vscode-server/cli/servers/Stable-<commit>/`
and six node processes were running out of it. Then eight hours of the proxy's access log carried no
Microsoft hostname, read as *the server never came through the proxy* — the log lags its own events by
minutes, the window's last line was 16:00:20Z, and the three `403`s on `update.code.visualstudio.com`
were stamped 16:02:19Z onward. Both reversed on the next query, and both had already been written down.

**Why it is a class rather than a slip.** The rule for one half of this was already in the repository:
[`log-debugging.md`](runbooks/log-debugging.md) §7.4, *absence is a verdict only with a positive
control*, written for a quiet client. It was not applied, because neither reading looked like a log
reading in need of a control — one was an `ls`, the other a query that had worked all day. An instrument
answers *nothing matched in what I hold*, and its two ways of holding nothing are **coverage** (the wrong
path, the wrong group, the wrong field) and **currency** (the right place, too early). The second was new
here: a positive control taken from an earlier minute says nothing about the minute in question.

**The rule.** Before a conclusion rests on an absence, state which instrument would have shown the
presence and check both of its halves: a positive control in the same channel — a name known to be there,
a path known to exist — and, for anything time-bounded, the newest entry's timestamp read against the
event being asked about. `filter-log-events` never answers *it did not happen*. §7.4 covers the quiet
client; this adds the quiet clock, and extends both beyond logs to every probe, since a stale path
answers exactly like an empty world.

**Where it bites hardest**: when the absence is the *pleasant* answer. Both readings closed a question at
no cost and demanded no decision, which is why neither was challenged — the same evidence closed
decision due 5 twice, once wrongly. Lesson 13 is its sibling (a verification empty on both outcomes),
Lesson 42 its network form (denied is a response, never-arrived is an absence) and Lesson 30 the
reminder that a tool's failure is not a property of the world.

## Lesson 63 — a default is read once, when the consumer is created, and the copy outlives it

**What happened.** The `default-v0.3.0` → `v0.4.0` bump followed [`dev-env.md`](runbooks/dev-env.md) §B
to the letter: apps deleted, the domain detached, the apply read `1 to add, 1 to destroy`, the new
version's digest checked against the one pushed, the domain re-attached on both app types, re-plan
`No changes`. Every reading the chain asks for was green. Then a reading nobody had asked for:
`remote-editor-claude` still named `image-version/awsds-sandbox-dev-env/3` in its **own**
`SpaceSettings.DefaultResourceSpec`, and version 3 had just been destroyed — the resource is force-new
on `base_image`. The domain's `DefaultUserSettings` had been correct throughout and reached nothing
that already existed.

**Why it is a class rather than a slip.** A *default* looks like a live indirection and is usually a
**copy taken at creation**. The word invites the reading that consumers follow it; what they follow is
the value it held on the day they were made. The chain was written from the domain's side, where the
whole story is visible and complete, so nothing in it pointed outward at the consumers — and the
consumers are the half that grows. Every bump after this one strands one more space than the last.

**The rule.** When a bump changes something a consumer could have copied, enumerate the consumers and
read the field back from each; do not infer their state from the object that supplied it. Ask, of any
value named *default*, when it is read — at use or at creation — because that decides whether changing
it is one write or N. Where the platform offers a **mutable alias** beside an immutable id, the alias
is what survives a bump: the space next to the stranded one was fine because it names AWS's image by
`SageMakerImageVersionAlias: "4.3"` rather than by a version ARN.

**What makes it expensive.** The stranded copy is invisible from the side you are working on and the
whole procedure reports success — this is Lesson 35's shape (adopting an object invalidates procedures
and touches none of the files carrying them) meeting Lesson 33's (one intent in two places). The repair
is also where Lesson 60 would bite: the consumer's block carries fields the runbook never mentions —
`RemoteAccess`, storage, a project's S3 connection — and whether `update-space` clears what a request
omits is **not measured**. So the repair is a transformation of the live read, never a template: it is
correct whether the API replaces or merges, and a template is correct only if it merges.

**The failure is a start that does not happen.** Measured the same evening: the stranded space's app
failed to start against the destroyed version, with no fallback to the domain default. The user
repaired it in the portal and it came up with those three fields intact.

## Lesson 64 — a comment inside a rendered template is a host replacement in waiting

**What happened.** Stage 6g decision 1 took the proxy off its `[P]` Elastic IP: two arguments changed in
`production/proxy/main.tf` and nothing else. The plan read `1 to add, 2 to change, 2 to destroy` — the
host was going to be **replaced**, and neither reason was the address. The SSM-resolved `ami` had moved,
and `user_data` differed from what the running host carried because a **comment** inside
`user-data.sh.tftpl` had been edited in `c70e73e` and never applied: nothing had touched the slice since.
With `user_data_replace_on_change = true`, every byte of that file is the host's identity. The same
afternoon it happened again in the other direction — the first-render comment was corrected *after* the
apply, so the host now carries text the repository has replaced, and the next apply of that slice rebuilds
it. Not the next `make hub-up`: that starts a `[D]` host and never applies its slice, which is why the
debt sat through a full stop and start on 2026-09-18 without being paid.

**Why it is a class rather than a slip.** A comment in a `.tf` file is free: the plan never sees it. A
comment in a file that is *rendered into an argument* is content — `templatefile` hashes it, and a
force-new argument turns prose into a rebuild. The two files sit side by side in the same slice and read
the same way in review; what separates them is which side of the rendering boundary they are on, which
no diff shows. The cost is also displaced: the person who improves the wording pays nothing, and the plan
that proposes the replacement is read by whoever next applies the slice for an unrelated reason, against
their own change.

**The rule.** Treat every file rendered into a resource argument as deployable code: `templatefile`
inputs, `user_data`, cloud-init, a rendered proxy or agent configuration. Editing one for prose is a
decision about a replacement, so either accept it and write it where the next operator reads it, or leave
the text alone. And when a plan proposes a replacement, **attribute each forcing argument before
applying** — the reason may predate the change in front of you by several commits.

**What makes it expensive.** The repository cannot answer the attribution question, because the drift is
between the tree and AWS: `describe-instance-attribute --attribute userData` reads what the host actually
carries and settles whose edit is pending. Here the replacement was harmless — the proxy is stateless,
rebuilt from this template at every boot, and its address is no longer `[P]`. On a host that keeps
anything, this is Lesson 4's shape arriving through a comment.

## Lesson 65 — a repository-wide pin is a claim about the machine it was written on, and every script inside it carries it

**What happened.** Stage 6i step 3.6, 2026-10-11. `package-uv-job.py` declares `requires-python >=3.11`
in its inline metadata and runs under the shebang `uv run --script`. In a space it stopped before its
first line: "No interpreter found for Python 3.14". The 3.14 was the repository's `.python-version`,
written for the tooling project at the root, and uv reads that file from the script's folder upwards,
wherever the command is typed, so running from another folder failed the same way. The house image sets
`UV_PYTHON_DOWNLOADS=never` by decision, so the space could not fetch 3.14, and the only interpreters on
uv's search path were the distribution's 3.12. Past that pin, the project's own `.python-version` (3.13)
stopped the inner `uv export --locked` the same way, in a simulation of the space.

**Why it is a class rather than a slip.** A tool's configuration file is found by location, never by
intent: `.python-version`, `.terraform-version`, `.tool-versions`, a tool table in `pyproject.toml`. A
pin written for one environment binds every environment the repository is carried to (a space, a CI
runner, CloudShell), and the machine that wrote it always satisfies it, so no local run can show the
failure. When the failure arrives it reads as the target environment's defect, "no interpreter found",
and the remedy it suggests, allowing downloads, undoes a decision the target environment made on
purpose.

**The rule.** A script meant to run in more than one environment states its own requirement where the
tool honours it over the repository's (here `--python >=3.11` in the shebang), and names the interpreter
it needs where the environment has one the tool cannot find (`UV_PYTHON` to the house environment's
interpreter). Before a document says a procedure runs in an environment, it is run there once
(Lesson 54).

**What makes it expensive.** Nothing in the repository looks wrong: the pin is right for the laptop, the
script's metadata is right for the script, and the image's setting is right for the image. The failure
lives in their combination, in the one environment none of the three was tried in, and the first person
to meet it is the reader the document was written for.

## Lesson 66 — a control on a request's parameters binds whoever makes the request, never the role the request passes

**What happened.** Stage 9 step 3.5, written 2026-09-05, moved `DenySageMakerJobsOffVpc` and its siblings
from the persona permission sets onto the job-execution roles, as a permissions boundary, so that "a job
this role can run" would always carry a `VpcConfig`. Read against the executed stages on 2026-10-11, the
measurements said otherwise. 6d's notebook task was refused with *"explicit deny in a permissions
boundary"* naming the **calling** session's boundary, and 6i's processing job was accepted on the caller's
policies. `sagemaker:VpcSubnets`, `sagemaker:NetworkIsolation` and the rest describe the `Create*Job`
request, and IAM evaluates a request against the principal that sends it; the job's role is a parameter of
that request, passed and never the sender. In Production the sender is a workflow's execution role or a
deploy role, so a boundary on `awsds-prod-job-exec` would have bound nothing, and the failure would have
been silent: the job runs, off the VPC.

**Why it is a class rather than a slip.** Every API that launches work under another identity has this
shape: `iam:PassRole` designs, a Glue job's role, an ECS task role, a Step Functions state machine's role.
The control that limits *how* the work is launched sits on the launcher; the control on the passed role
limits only what the work does once it runs. And the account where such a plan is first measured is often
the one where the two identities coincide, as Sandbox's project role is both the caller and the job's role,
so the measurement agrees with the wrong design.

**The rule.** Put a control on a request's contents where the request is made: on every principal that can
make it, or above all of them, in an SCP. Before reading a measurement as confirming such a control, name
the caller and the passed role separately, and check whether they were the same principal when it was
taken.

**What makes it expensive.** The mistaken control reads as stricter than the right one, since it sits on the
role closest to the data, and nothing refuses: the job that should have been denied simply runs.

## Lesson 67 — whoever can make a machine run code holds the machine's role

**What happened.** Stage 7's runbook created the build runner as a GitLab **instance runner**. The runner's
instance role pushes to the three image repositories, and any job on the host reads that role's
credentials through the metadata service, at the hop limit a containerised push needs. With sign-up open,
any account that could reach GitLab could register itself, create a project, run a job on the instance
runner and push an image into `awsds-prod-ecr-dev-env`, around the protected tag `*-v*` that Stage 8's
release gate rests on. Caught on 2026-10-12, before the runner existed: it became a **protected project
runner** of `awsds/app-etl`, linked to `awsds/dev-env` and locked to those two projects.

**Why it is a class rather than a slip.** A machine credential is held by every piece of code the machine
will run, so its real principal set is decided by whatever schedules work onto the machine. For a runner
that is GitLab: the runner's scope (instance, group, project), whether it is protected, who can push a
protected ref in the projects it serves, and who can create projects there. None of those settings is IAM,
and none appears in a policy, an access analysis or a plan. The same shape holds for Stage 8's deploy
runner and its three deploy roles, for a SageMaker space and its project role, and for an MWAA worker.

**The rule.** For every host that carries a role, write down who can make it run code, and treat that set
as the role's principals. A gate in the scheduler (a protected tag, a protected branch) controls the role
only if no unprotected path reaches the same host.

**What makes it expensive.** The gate keeps working: the tag stays protected and its settings page reads
correctly, while the credential it was meant to guard is reachable around it, and nothing refuses.

## Lesson 68 — an `[E]` host's first boot runs every session, so what it reads unpinned is a release and what it reads without waiting is a race

**What happened.** Stage 8, 2026-10-16, `production/runners/`: three defects in one day, all in the first
boot of hosts that `make gitlab-up` creates and `make gitlab-down` destroys. The test runner, created in
the same apply as its role and instance profile, read the CA root 28 s later and met `NoCredentials`;
its boot stopped there, the apply had already reported success, and runner #4 never registered, which
its serial console showed that evening. The deploy runner installed `gitlab-runner` 19.4.1 on
2026-10-13 and 19.5.0 on 2026-10-16 from an unchanged line, against a 19.4.2 server. And an Amazon
Linux release moved the AMI parameter at 20:01 UTC, so the next plan, written to replace one runner,
replaced three.

**Why it is a class rather than a slip.** A `[P]` or `[D]` host boots once per build: the person building
it meets its races, and its versions are fixed on the day it was built and then held (`production/tooling/`
installed CE 19.4.2 on 2026-10-12 and holds its AMI and user data with `ignore_changes`). The hold keeps
the host, never the template: the next first boot is a rebuild, and for GitLab the rebuild is the restore,
which GitLab refuses unless it installs the backup's release (Stage 7 decision 10, read 2026-10-16 while
CE 19.5.0 was the newest). D11 makes an
`[E]` host's first boot a recurring event, and each session's boot meets a new package index, a new
image and a new IAM timing with the same template. A boot that passed once is one sample. Its reads
come in three kinds, each failing its own way: a dependency it must wait for (its own role, the GitLab
it registers with) loses a race some sessions; a version it installs (a package's newest) moves with no
diff in the repository; and an input the plan resolves (the AMI parameter) turns every plan of the
slice into a release.

**The rule.** For each read in an `[E]` host's boot, name its kind. Wait for a dependency with a
deadline that fails loudly, the host's own identity included. Pin a version the host's behaviour
depends on, with the coupling it must keep written beside the pin (here, the server's major.minor; for
GitLab itself, the release its backups were made by).
Hold an input that only ages, so it is read when the host is created and never by an unrelated plan.

**What makes it expensive.** The apply's verdict is about the instance, not its boot: `Apply complete`
and a running host that bills while registered as nothing. Each failure is also intermittent or
silent: the race loses some sessions, the version drifts with no commit, and the replacement arrives
inside a plan written for something else.

## Lesson 69 — two stages' unapplied changes to one slice become one apply the moment both are on main

**What happened.** 2026-10-18, `sandbox/sagemaker/`. Stage 17's pass 1 put `MLflowApp` into
`sagemaker-prereqs-v0.5.0` and waited on its 1.1, a portal reading the user takes before the blueprint
exists. Stage 11's `TM-21` put the project key's organization condition into `v0.6.0`, built on `v0.5.0`,
and its threat-model row said it applies "unless Stage 17's step 1.3 applies first". Both PRs merged; the
caller pins `v0.6.0` and takes the module's default roster, so the slice's only possible plan is `2 to add,
1 to change`, and the security fix waits on a portal reading of another stage.

**Why it is a class rather than a slip.** A tag is cut from the commit before it, so a later version carries
every earlier one; each stage's text describes its own half and stays true on its branch. The coupling
appears only on main, where nothing reads the two stages together.

**The rule.** Before tagging a module whose previous version is unapplied in a caller, read who waits on that
version and say it in both stages: the apply is shared, and so is the condition each one waits on. Where the
two must land apart, cut the second change from the version that is applied, not from the newest tag.

**What makes it expensive.** The plan is the only reader that shows it, and nobody plans a slice whose change
is waiting.

## Lesson 70 — a refusal attributed to the identity's class was a membership, and memberships change in a portal nobody watches

**What happened.** `datazone list-connections` refused `InfrastructureAccess` three times (2026-09-21 to
2026-10-10), and 6h recorded it as a property of the identity: the infrastructure user is not a project
member, so `WH-9` became a permanent note and `EXC-17` an object no instrument reads. On 2026-10-15 a
portal act added a group profile whose role is Sandbox's `InfrastructureAccess` as a contributor of both
projects, and on 2026-10-18 the same call answered from Sandbox's profile and stayed refused from Data
Governance's.

**Why it is a class rather than a slip.** A service with its own permission layer decides on state it holds
(Lesson 28's second grant), and that state is edited in a console, by a person, with no plan and no diff. A
refusal read as "what this identity is" outlives the state that produced it.

**The rule.** Record such a refusal with the state it depends on ("not a member of the project, read
<date>"), and give the note a revision trigger the instrument can read, here the projects' memberships.

**What makes it expensive.** The change is silent in both directions: nothing announces the new access, and a
permanent note stops anyone from re-trying the call that would show it.

## Lesson 71 — a lint that prints `ok` for a clause its invocation leaves unchecked reads as a pass on every clause

**What happened.** Stage 8, 2026-10-18. Step 5.6 lists eight clauses for the D28 workflow lint, and
`app-etl`'s CI runs it as `lint .`, which prints `ok: 6 arquivo(s)` or one line per refusal. Reading the
tool at `3c1708e` found clauses that this invocation leaves unchecked and says nothing about: (d) and
(h)'s comparison with the release's manifest have no rule at all, and (e)'s repository, (f)'s instance
type and (f)'s volume key need `--image-repository`, `--instance-type` and `--promoted`, of which the
pipeline passes none and the last refuses a folder. A `dev-env` image by digest and a job with no volume
key both read `ok`. The clauses were written from the design (Lesson 57's neighbour); the pipeline's line
was written from the tool's default.

**Why it is a class rather than a slip.** A gate's verdict is one word for every clause, and a clause a
mode skips does not print "skipped": `ok` means nothing was refused and reads as nothing is wrong, which is
Lesson 13 inside one command. The clause list and the pipeline's line are two documents about one
behaviour, and no step reads them together; the options that switch a clause on are what the pipeline's
author did not think to add.

**The rule.** For each clause of a gate, name the invocation that switches it on, and read the pipeline's
command line against that table: a clause the line leaves off is written in the plan as a gap, with its
owner. Prove each clause with a deliberate violation run through the pipeline's own invocation, never
through the most thorough one (Stage 8 verification xiv says which option each row needed).

**What makes it expensive.** The gate stays green while the thing it was written to refuse goes through,
and the first reader to notice is a person looking at a rendered file.

## Lesson 72 — an action left out of the policy you write is not denied to a principal that carries policies you do not write

**What happened.** Stage 6h, 2026-09-21 to 2026-10-18. Step 2.2 wrote the project role's warehouse
policy without the `redshift-data:` family, and the stage recorded the consequence as a fact: *"the JDBC
path is open and the Data API path is not granted"*. Verification i left the boundary's answer for the
family unread, and decision 8 argued the wide tag on the strength of layer 2. The policy simulator, run
on 2026-10-18 for 5.3, read the project role `allowed` for `redshift-data:ExecuteStatement` on the tagged
workgroup: AWS's `SageMakerStudioProjectUserRolePolicy` v75, which the blueprint attaches to every project
role, grants the family and `GetCredentials` on a workgroup tagged with the caller's project,
`GetCredentials` on any workgroup through `sqlworkbench` or the Data API, and both on any workgroup
carrying `for-use-with-all-datazone-projects=true`. The omission had closed nothing for a month.

**Why it is a class rather than a slip.** An omission is a control only on a principal whose every policy
the author writes. The project role carries five AWS-managed documents and one of this repository's (open
question 22), so what it may do is their union, and a family left out of the one is granted or not by the
five. Lesson 11 one layer down: the author of the *other* policies decides. And Lesson 20's mirror: the
allow nobody here wrote is attached and exercised, while the deny nobody wrote is imagined.

**The rule.** A claim that a principal lacks an action is made about the principal, never about one
policy on it: simulate the principal with the action and the resource's tags in the context, or read every
policy it carries. Where a service mints the role, the repository's policy is the declared duplicate of
what the service's text grants, kept because that text moves, and the stage says which door each grant
answers for; in 6h the access role, which carries no AWS policy, is the one principal the repository's
policy alone admits.

**What makes it expensive.** The design was argued on a gate that did not exist, the instrument that reads
the layer (`WH-11`) reads the repository's policy only, and the finding arrived as a by-product of another
measurement.

## Lesson 73 — a selector that takes the last match is a claim that there is one, and the change that adds the second is never read against it

**What happened.** Stage 8, 2026-10-24. `app-etl`'s `test-deploy` followed its run with `get-workflow-run`,
taking the workflow's ARN from the CLI's log with `sed … | tail -1` on *"ARN:"*, written when the manifest
held one workflow. v0.4.0 added `app-etl-train`, created in the same deploy after `app-etl`, so the last
*"ARN:"* line became the train workflow's while the run was app-etl's. The deploy and the run passed; the
job failed 16 minutes in on *"Workflow run not found"*, and the tag `v0.4.0` was spent, since a retry runs
the tag's YAML. The release that added the second workflow was written, linted and unit-tested, and none of
that reads the job's selector.

**Why it is a class rather than a slip.** "The last line", "the first element", `[0]`, `tail -1` and
`head -1` answer correctly for every input their author ran, and the inputs grow through a change made
elsewhere: a manifest's list, an account's resources, a log's verbosity. The change is reviewed against its
own files; the selector lives in a job, a script or a query, often in another repository, and fails only
when it runs, after everything before it passed. Lesson 49 is the same claim held by a comment.

**The rule.** Select by identity, never by position: the name the run line carries, the key an object is
created under, a filter on the attribute that tells the items apart. Where a position is the only handle,
assert the count first and fail naming it. When a change adds a second instance of something (a workflow,
a chain, a bucket, a target), search its consumers for positional selectors over that thing before the
tag.

**What makes it expensive.** It fails at the last step of a long job, after the work it was meant to check
succeeded, on an identifier that names something that exists; on a tag pipeline the fix costs a new tag.

## Lesson 74 — a placeholder that reads correctly after decoding can be inert to a service that substitutes it textually, and the plan that fixes it calls the change whitespace

**What happened.** Stage 10, 2026-10-25. The orchestration module wrote each schedule's target input with
`jsonencode({ chain = …, scheduledTime = "<aws.scheduler.scheduled-time>" })`. `jsonencode` writes `<` and
`>` as `\u003c` and `\u003e`, and EventBridge Scheduler substitutes a context attribute only where the input
carries it literally, so Production's first scheduled executions received the placeholder unsubstituted.
Every reader decoded the JSON first: the HCL, `describe-execution`'s input as a parser reads it, the plan.
The fix's plan rendered the change as `jsonencode( # whitespace changes`.

**Why it is a class rather than a slip.** A service that substitutes placeholders matches bytes: the
Scheduler's `<aws.scheduler.*>` attributes, an EventBridge input transformer's `<path>` names. Every tool
between the author and the service decodes before it shows anything, so an encoder that escapes the
placeholder's delimiters makes it inert while every view reads it as intended. Lesson 56's inert line,
produced by an encoder instead of a missing capability.

**The rule.** Write a value a service substitutes into as a literal template with only the parts that need
encoding encoded (here the chain's key); read back the stored raw string from the service's own API at the
first apply; and read a plan's "whitespace changes" on a JSON string as a byte change.

**What makes it expensive.** It is silent until something consumes the value. No chain forwarded the date, so
the defect cost nothing yet; the first chain that reads it would receive a literal where a timestamp was
expected, at a scheduled run in Production.

## Lesson 75 — a permission the creator holds without a grant moves with whoever creates the object, and a decision that moves the teardown to another identity owes it the grant nobody had to write

**What happened.** Stage 8's decision 27 (2026-10-24) moved Staging's teardown from the pipeline's deploy role
to the user's `make down`. The application slice's table in `app_outputs` is created by the deploy role at
the leg, and Lake Formation gives a table's creator its permissions and nobody else: the account's
administrator, who created the database, holds no `DROP` on a table another principal created in it. The
first such down, 2026-10-25, was refused *"Required Drop on trades_notional"*; the user unblocked it with a
grant by name, which left with the table, and `app_outputs` gained a wildcard grant to the infrastructure
identity. The decision, its plans and its applies were read against IAM, the deploy roles' grants narrowed
and the user's permission set, and the creator's half was written in neither.

**Why it is a class rather than a slip.** Creator-held permissions exist in more than one system here: Lake
Formation's creator permissions on databases and tables, and Redshift's ownership, under which only an
object's owner or a superuser drops it. A decision that changes who creates or who destroys an object changes
who holds that half, and no policy diff shows it, because the permission was never written.

**The rule.** When a decision moves an act (create, alter, destroy) to another identity, list the objects the
act touches and, per object, what its creator holds without a grant; write the new identity's grant in the
same change, and run the act once as the new identity before relying on it.

**What makes it expensive.** It surfaces at the teardown, the step nobody rehearses, after the work succeeded,
and the hand grant that unblocks it leaves with its object and teaches the next release nothing.

## Lesson 76 — a toolchain upgrade on one writer locks out every older reader of the states it writes, and the readers that cannot move on the spot move first

**What happened.** The laptop moved from Terraform 1.15.8 to 1.16.6 on 2026-10-25 (the bump taken 2026-10-22
for CVE-2026-78669), while the deploy image the pipeline's jobs run in carries 1.15.8 until its next release, a
GitLab act. Terraform refuses a state snapshot written by a newer version, *"state snapshot was created by
Terraform vX, which is newer than current vY"*, in a plan, in a `terraform_remote_state` read and in `terraform
output` alike. Every state the pipeline reads or applies was still 1.15.8's that day, because the sitting's
three applies ran before the install; the first laptop apply or `make up` of such a slice after it would have
put the state out of the image's reach: `staging-check` on `staging/egress`, `production-deploy` on
`production/workloads-egress`, and the application and orchestration slices' `terraform_remote_state` reads of
`data/`, `sagemaker/`, `foundation/` and `workloads/` in both targets.

**Why it is a class rather than a slip.** A version is a property of every state a binary writes, not of the
machine alone (Lesson 65's mirror): the laptop and the image are two writers and two readers of the same
states, and upgrading one changes what the other can read without touching a file either of them reads.
Nothing in the plan, the diff or the apply names the second reader; the refusal arrives in a pipeline job,
days later, as the failure of a slice nobody changed.

**The rule.** When two toolchains read the same states, the readers that cannot be upgraded on the spot (an
image, a runner) move first, or every writer that moved stays off the states they share until they do. Here:
the deploy image is rebuilt before any laptop apply or `make up` of a slice the pipeline reads or applies
([`runbooks/promotion.md`](runbooks/promotion.md) §N.1 step 2); the hub and GitLab slices, which no pipeline
reads, are free.

**What makes it expensive.** The lockout is invisible until the pipeline runs, and the way back is a
downgrade of the laptop or an image rebuild in the middle of a release.

## Lesson 77 — a gate that reads a feed gives a dated verdict: the lock that passed on the day it was cut fails on the day it is tagged, and the tag is spent either way

**What happened.** `awsds/dev-env`'s lock was cut on 2026-10-16 and passed `pip-audit` at `default-v0.8.0`'s
release that day. The recipe then changed in one literal, and on 2026-10-25 the same lock met 73 blocking
findings at the gate, in 11 packages, three pipelines (#89 to #91) failing on the tag `default-v0.9.0`, which
the convention spends on first landing: pillow's 41 alone were published against 12.3.0 once 13.0.0 shipped
on 2026-10-16, setuptools' fix 84.1.0 on 2026-10-19. Nine packages moved by a targeted `uv lock
--upgrade-package`; pillow and setuptools could not, their fixed versions forbidden by autogluon 1.6.1's upper
bounds, and entered the accepted list by name (42 entries, `gates-v0.5.0`).

**Why it is a class rather than a slip.** The gate's input is two things, the lock and OSV's records of the
day, and only the first is in the commit. A green pipeline is a reading of the feed at that hour, not a
property of the lock; a tag cut from the same commit days later reads a different feed, and the failure lands
on the one object the project cannot reuse. Lesson 54's three verdicts gain an axis: *when*.

**The rule.** A gate that reads a moving feed is run on the laptop the day of the tag, before the tag, with
the gate's own flags (the dev-env README's *Before a build*); the tag is cut on a green reading, the lock
moved package by package past what moved, and what a dependency's upper bound forbids is accepted by name,
dated and attributed. A bare `--upgrade` is not the move: on 2026-10-25 it resolved an older autogluon and
failed building `configspace`.

## Lesson 78 — a stand-in for a refused call answers what the real call answers to the identity it imitates, read from the path that already works, never from what the first caller tolerates

**What happened.** On 2026-10-26 the CI/CD CLI's `dev` deploy from a space stopped at `ListDomains`, which
DataZone refuses to a project's role (Stage 10 2.1). The command replaced the CLI's lookup,
`get_domain_id_by_name`, with a stand-in whose first answer was `None`, on the premise that the deploy role's
own call in Sandbox returns an empty list, the domain living in Data Governance. The project step, the
lookup's first caller, accepts `None` and goes on; the deploy copied the application's files under the
project's `shared/` and two operator zips under `shared/operatorFiles/`, then stopped in `workflow.create`,
the second caller, which resolves the project's role through the same lookup: *"Domain 'awsds-studio' not
found in region us-west-2"*. The premise was contradicted by a record already in hand: the pipeline's
`test-deploy` creates its workflows through that second caller as the deploy role, so the role's call
returns the domain. The stand-in answering with the manifest's domain id passed both callers, and the deploy
and its run succeeded.

**Why it is a class rather than a slip.** A stand-in replaces a function for every caller, and the caller
that runs first is the one that tests the guess; a tolerant caller passes a wrong answer through, and the
failure arrives at a later caller, after side effects. The guess was about a value nobody read: what the real
call returns to the identity the stand-in imitates. That value was knowable without a call, from a run of the
same code path that had already succeeded.

**The rule.** Before writing a stand-in, list every caller of the function it replaces and read what the real
call returns, to the identity being imitated, from a run that went through all of them; return that. A
stand-in that satisfies only the caller that failed is a second defect, and its first symptom names a later
caller, never the stand-in.

**What makes it expensive.** Each wrong answer costs a deploy and leaves its partial write behind: the copied
files a later deploy syncs over, and operator zips nothing prunes.

## What AWS does that its documentation does not say

The lessons above are habits; the entries here are facts about the platform that cost a measurement
to learn. Each says what was measured, when, and where the reading lives: a behaviour recorded
without its evidence is indistinguishable from a belief (Lesson 37).

An entry belongs here only if the documentation does not state the behaviour, or states it somewhere
the person who needed it would not have been reading. A documented gotcha that was merely forgotten
belongs in the file that owns it (`conventions.md`, a runbook, a stage). Two candidates were
excluded by that rule: `iam list-roles` omitting `PermissionsBoundary` (documented contract) and
ECR's `tagPatternList` accepting wildcards (the page says so; the wrong claim was ours).

The signatures these findings leave in a stage log: an error message naming the wrong cause, a call
answering differently before and after another act, a field that writes and never reads, a bill
starting at a state nobody named. Each entry carries the stage that found it.

### Elastic IP transfers

- **The allocation id does not survive a transfer** (measured 2026-09-06, 6c step 4.5):
  `eipalloc-04397bfae0295333d` in the source became `eipalloc-07edec7a52dc0820a` in the destination.
  AWS documents it neither way. The address is preserved and the id is not, so an allocation id is a
  per-account fact about an address, and anything that pinned the old id points at nothing. This is
  why `[P]` ids are read through remote state instead of pasted, and why an `import` block's id is
  read after the accept. Reading: `log-stage-06c-networking-hub.md`, the 4.3-4.6 entry.
- **Two of the four documented refusals fire at accept time, in the destination account.**
  `enable-address-transfer` succeeds on an address that is still associated, and on a destination at
  its Elastic IP quota; the failure arrives at `accept-address-transfer` as
  `InvalidTransfer.AddressAssociated` / `AddressLimitExceeded`, with the transfer already pending
  and a seven-day clock running that AWS notifies nobody about. The eligibility reading is therefore
  taken across both accounts before the first write, which is what `./aws/eip-transfer.py` does.

### Systems Manager

- **`ApplyOnlyAtCronInterval` is rejected on `rate()` schedules**: `InvalidSchedule:
  ApplyOnlyAtCronInterval is not supported for Rate Schedule associations` (measured 2026-09-06, 6c
  step 4.8). The flag is the only thing that stops a State Manager association firing at creation
  time, so an association that must not race a first boot has to be `cron(...)`.
- **A State Manager association fires seconds after `RunInstances`** when that flag is absent, while
  the user data is still in `dnf install`. On a fresh host the immediate run is a guaranteed `exit
  127`, and it leaves a `Failed` association on a working host.
- **The SSM agent reports `Online` before the user data has finished**: the agent ships in the AMI
  and registers early. Agent registration is not a readiness signal; a check that treats it as one
  reads a half-built host as built (measured twice on 2026-09-06, on both hub hosts).
- **Parameter Store reserves every name beginning with `aws` or `ssm`, case-insensitively.**
  `PutParameter` answers `AccessDeniedException: No access to reserved parameter name`, a message
  that reads like a policy problem and is a naming one. Measured at Stage 2's Validation,
  2026-08-16; the rule and this project's `/datascience/<env>/…` names live in `conventions.md`. The
  undocumented half is the error text.
- **A public AMI parameter answers only its current value** (measured 2026-10-16 as
  `InfrastructureAccess` in Production, Stage 8 decision 25). On
  `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64`, `GetParameterHistory` is
  refused with `AccessDeniedException: Cannot access/update data for the restricted parameter`, and
  `GetParameter` with a version selector answers `ParameterVersionNotFound` for every version, the
  current one (194) included. A pin by parameter version is therefore unavailable, and which image the
  parameter named at a past moment is read from `describe-images` (owner `amazon`, name and
  `CreationDate`), never from Parameter Store. Neither the EC2 page that recommends the parameter nor
  Parameter Store's page on public parameters says so (both read the same day).

### ECR, S3 and the NAT

- **An ECR image pull is two paths, and the heavy one is free.** `ecr.api` and `ecr.dkr` carry the
  authentication and the manifest, kilobytes; the image layers are fetched from S3, which in this
  estate means the `[P]` gateway endpoint: no hourly charge and no per-GB charge. The two interface
  endpoints are billed for almost no traffic. This is also why AWS requires an S3 gateway endpoint
  beside the two ECR ones: without it the auth succeeds and the download hangs. Written down
  2026-09-06 after a user question found it recorded nowhere in this repository.
- **A NAT never carried S3 or DynamoDB traffic here, even under design A**: a prefix-list route is
  more specific than `0.0.0.0/0`, so the gateway endpoint always won (`docs/NETWORK.md`, measured in
  Stage 3). Removing the NAT therefore did not make that traffic cheaper; it was never paying.
  Design B saves on the traffic that did use the NAT, internet downloads at 0.045/GB of processing,
  which now cross an EC2 proxy with no per-GB charge.

### WireGuard and the client platforms

**`AllowedIPs` is inert for an address family the interface has no address in** (measured
2026-09-07, macOS, App Store client). `wg-quick` installs routes only for the families present on
`[Interface] Address`, so `AllowedIPs = 0.0.0.0/0, ::/0` beside an IPv4-only address installs no
IPv6 route; the config parses, the tunnel comes up and `wg show` reports nothing unusual. The
reading is `netstat -rn -f inet6`: the tunnel interface is not among the default routes. WireGuard's
documentation does not say the two lines are coupled. Where: `docs/plan/runbooks/vpn.md` §C6.

**macOS keeps the physical default route as an interface-scoped entry while a tunnel is primary**
(same reading). `netstat -rn` shows two defaults; the physical one carries the `I` flag, and traffic
already associated with that interface keeps using it. A socket established before the tunnel came
up survives it, so "the tunnel is up" does not mean everything goes through the tunnel: a new
connection to the same host fails while the old one works.

**macOS does not consult the system proxy while a NetworkExtension tunnel is primary** (measured
2026-09-07). `networksetup -getsecurewebproxy "Wi-Fi"` reports the proxy configured and enabled;
`scutil --proxy`, which is what applications read, returns an empty dictionary. Safari, Chrome by
default and every native application reading the system configuration behave as if no proxy existed.
Per-application configuration works (Chrome's `--proxy-server` flag, Firefox's own settings,
`https_proxy` for shell tools). With the tunnel down the same setting is consulted again, points at
a host only the tunnel can reach, and breaks the `aws` CLI, which falls back to the system
configuration: an empty `https_proxy` does not override it and `NO_PROXY='*'` does. Tracked as
[issue #67](https://github.com/felipenoris/AWS-DataScience/issues/67).

**Linux rate-limits the ICMP errors a `REJECT` rule promises, per destination, and the rule's own
counter does not say so** (measured 2026-09-07, 6c step 6.4). `iptables -L FORWARD -v` counted 27681
rejected packets; `/proc/net/snmp`'s `Icmp` line said 4366 `OutDestUnreachs` and 23318
`OutRateLimitHost`, under `net.ipv4.icmp_ratelimit = 1000` (ms, per destination) and `icmp_ratemask
= 6168` (destination-unreachable included). A client whose background traffic is refused a few times
a second sees a timeout for the packet it is watching, and a fast refusal when a token happens to be
free; both were measured with the same command, minutes apart. The `REJECT` counter proves the rule
is hit; only the `Icmp` line says whether the refusal was spoken. `./aws/vpn.py --on-host` reads
both. Where: `docs/plan/runbooks/vpn.md` §S2, `docs/NETWORK.md` §7.

**The App Store WireGuard client applies a `DNS` line to every query, whatever `AllowedIPs` says**
(read from its source on 2026-09-08, `matchDomains = [""]` in `PacketTunnelSettingsGenerator.swift`,
and measured the same night, 6c step 8.3). Under a split `AllowedIPs` the tunnel's resolver is still
`scutil --dns`'s resolver #1, with no domain restriction and ordered ahead of the physical
interface's; `/etc/resolv.conf` names it, and `dig` resolves a private name through it. A split
tunnel does not give the laptop its own DNS back: every name crosses the tunnel, only the traffic
does not. The `wg-quick` path does the same by writing the server on every network service. Where:
`docs/plan/runbooks/vpn.md` §C7.

**The same client installs an interface-scoped default route on the tunnel in both families, even
when `AllowedIPs` names no default** (measured 2026-09-08, 6c step 8.3). `netstat -rn` shows a
`default … utun4` carrying the `I` flag beside the physical `default … en0` without it, and the
scoped entry is inert for any socket not bound to the tunnel. The reading that separates the two
profiles is the flag, not the presence of the line: under the monitored profile the tunnel's default
has no `I` and is primary. A step written as *"no default via the tunnel"* was one flag short; the
host's `REJECT` counter, flat across a burst, proved the route inert. Observed the same night by the
user: the app's tunnel is a Network Extension that `wg show` does not list, so the app's window is
check 1's reading.

**A host with no IPv6 route answers a tunnelled IPv6 packet with ICMPv6 *no route* before the
`FORWARD` chain sees it** (same reading). The `ip6tables` `REJECT` written on 2026-09-07 to make the
refusal counted stood at 0 while `Icmp6OutDestUnreachs` read 191: the refusal is real and counted in
`/proc/net/snmp6`, and the rule is a backstop that has never fired. The routing table is the control
(Lesson 56). Where: `runbooks/vpn.md` §C6.

**`aws sso logout` invalidates every cached session's token, and a browser sign-out of the access
portal invalidates none** (measured 2026-09-07/08). The infrastructure token died at
`GetRoleCredentials … 401` right after the user's `aws sso logout`, while the CLI kept answering for
profiles whose role credentials were already cached locally; Terraform, which exchanges the token
itself, noticed first. The same night the Data Scientist's token survived the user signing out of
the portal in the browser and signing in again as the infrastructure user. Two people's sessions
coexist on one laptop as long as nobody types `aws sso logout`, and the browser's portal session
decides whose token a login mints (the `ForbiddenException` at `GetRoleCredentials`). Where:
`aws/AWS-CLI.md`.

### Route 53

- **DNS Firewall needs both `example.com` and `*.example.com` to cover a domain and its
  subdomains**: neither form implies the other. Harmless there, and fatal when the same list is
  transcribed into a system whose wildcard already covers the apex (Lesson 53).
- **The VPC resolver at `.2` answers only requests sourced from within the VPC's own address
  range**, so a forwarded packet carrying a tunnel address is not answered. This is why 6c step 4.7
  exempts the hub's public subnets from the masquerade and never the VPC CIDR: the tidier rule takes
  the tunnel's DNS down, with a symptom pointing anywhere but at a masquerade rule.

### Control Tower and Organizations

- **A Control Tower *Update account* renders `Display Name` and `Account Email` read-only**, so an
  account renamed out of band can never be made to match its provisioned product: permanent
  divergence, not drift (measured in Stage 6b). The same update re-asserts D32's direct
  `AWSAdministratorAccess` assignment, so its absence on other accounts is not a control.
- **A cached SSO token is keyed by the `sso-session` name, never by the user**, so signing in as a
  second identity silently reuses the first one's token. The remedy is `aws sso logout` plus a
  portal sign-out; the failure mode is a command that succeeds as the wrong person (`aws/INDEX.md`).
- **An `AWSReservedSSO_*` trust policy permits only `sts:AssumeRoleWithSAML` and `sts:TagSession`**,
  so an RCP denying those actions locks every SSO user out of every member account. Measured at
  Stage 1c step 7.8; AWS's own `CT.STS.PV.1` carries the exclusion note, which is why no `sts:`
  action is added to that document without reading it first.
- **`describe-effective-policy` answers `{}` rather than raising when the policy type is `ENABLED`
  and nothing is attached** (measured at Stage 1c). A reader expects
  `EffectivePolicyNotFoundException`, and it does not arrive, so *"no policy in force"* and *"an
  empty policy in force"* are one reading. Any check written against this call needs a second
  signal.
- **An out-of-band account rename propagates with no observable delay** (measured at Stage 6b step
  3.2, which had flagged the timing as undocumented): the console act and the `organizations
  list-accounts` read agreed in the same sitting. Recorded as a measured absence, so that nobody
  builds a wait into a procedure that does not need one.
- **`iam simulate-principal-policy` reads the Control Tower Region ceiling as an explicit deny for every
  regional action unless the context names `aws:RequestedRegion`** (measured at Stage 11 pass 0,
  2026-10-18). Without the key, `sns:Publish` and `glue:GetDatabases` from a Sandbox project role return
  `explicitDeny` with `AllowedByOrganizations: false`, and `MissingContextValues` stays empty, since it
  lists the identity policies' keys and not the SCPs'. With `--context-entries
  ContextKeyName=aws:RequestedRegion,ContextKeyValues=us-west-2,ContextKeyType=string` the same calls read
  the identity layer. Stage 6e 3.1a recorded the first shape as the organization verdict being unusable
  from a member account. Where: `log-stage-11`, 2026-10-18. Two more readings of the same day: while the
  organization denies, the result names no identity statement, so the identity layer under an SCP deny is
  read by forcing the SCP's carve-out into the context; and the SCP evaluation reads `aws:PrincipalArn`
  as the role's own ARN when the context gives none, a key the simulator's page does not list among
  those it populates. Where: `log-stage-06h`, 2026-10-18. Read again on 2026-10-25 in Production, where
  `redshift-data:ExecuteStatement` and `sagemaker:DescribeModelPackage`, both working calls, read
  `explicitDeny` until the context named the Region (`log-stage-09`). The perimeter SCP's
  `DenyS3ObjectWriteOutsideOrganization` reads the same way while the context lacks `aws:ResourceOrgID`,
  its `StringNotEqualsIfExists` matching the absent key: Staging's deploy role read `explicitDeny` on
  `s3:PutObject` to its own orchestration state, which it writes at every leg, and with the organization's
  id in the context `allowed` there and `implicitDeny` on the egress state (`log-stage-08`, 2026-10-25).
- **`sso-admin list-account-assignments-for-principal` answers from the Identity Center delegated
  administrator**, where its API reference says the action *"must be called from the management
  account"* (measured 2026-10-18 as `InfrastructureAccess` in Identity, Stage 14: the shared
  data-scientist group's three assignments). One call per principal replaces the walk over every
  permission set and account that `./aws/list-identities.py` makes, and `./aws/vending.py` `VN-6`
  rests on it: the day the page is enforced, that check fails on a refused call, never on an empty
  list. Where: `log-stage-14-sandbox-vending.md`, 2026-10-18.

### Lake Formation and SageMaker Unified Studio

- **`UpdateDomain` does not clear a list you leave out; it clears one you send empty** (measured
  2026-09-11, 6d step 2's first version bump). The API is treated as a full replace of
  `DefaultUserSettings` — and a block sent without `JupyterLabAppSettings.CustomImages` left both
  attachments exactly as they were, so "omitted" read as "unchanged" rather than as "deleted". The
  vendor says the form in the detach page and nowhere near the attach page: *"you will need to leave
  `CustomImages` blank, such that `"CustomImages": []`"*. What survives of Lesson 60 here is the
  discipline, not the mechanism: send the block back as read, and clear a list explicitly. Where:
  `runbooks/dev-env.md` §C6 and §X step 1.

- **SMUS appoints itself a Lake Formation administrator** when the first project is created: two
  service roles nobody chose, in an account whose `admins` list a later
  `aws_lakeformation_data_lake_settings` would silently reset. Found 2026-08-26 by an unrelated
  plan, not by a gate: `DL-5` measures `parameters`, not `admins`.
- **`CROSS_ACCOUNT_VERSION: 4` and `SET_CONTEXT: TRUE` are already set in accounts nobody
  configured**, consumers included, and `aws_lakeformation_data_lake_settings` replaces the whole
  `Parameters` structure in any account that gains the resource.
- **`EnvironmentRolePermissionBoundary` is write-only on a blueprint configuration**: the schema
  accepts it and no read returns it (Stage 6a, 2026-08-22). Boundary drift can never appear in a
  `terraform plan`; the only door is `iam get-role` per role, since `list-roles` omits
  `PermissionsBoundary` by documented contract. A control that cannot be read back needs a sentinel,
  which is `US-8`. Read again 2026-10-19 (Stage 18 2.5): DataZone's own `get-` and
  `list-environment-blueprint-configurations` return `environmentRolePermissionBoundary`, in Sandbox
  and in Staging; Cloud Control's `get-resource`, the read `awscc` makes, omits it. So drift still
  never appears in a plan, the configuration's value is a DataZone read away, and a role's own
  boundary is still `get-role`'s.
- **An associated DataZone domain lists from every member account, with an ARN naming the owning
  account.** A check that counts domains per account therefore reports the association working as a
  finding. Measured when `./aws/studio.py` failed because the step succeeded (Lesson 31).
- **`list-environment-blueprint-configurations` cannot succeed from a member account until the
  association exists**; after it, the same call returns `{"items": []}`. The empty list is the
  success signal, indistinguishable from an absence to anything that only checks the contents.
- **A blueprint configuration is applied from the member account**, an existing one is immutable
  through `awscc`, and an incomplete one pins its projects in both directions: they can neither
  deploy nor be torn down. None of the three is on the authoring API's page; each cost a sitting.
- **An IAM role in a DataZone domain is two principals, and a policy grant takes the group.** Its ARN
  resolves as a user identifier to one session's user profile, and as a group identifier to the
  role's `IAM_ROLE_SESSION_GROUP` profile, which every session belongs to. `CreatePolicyGrant` with
  the ARN as a user is refused, *"Group profile already exists for the given User profile"*, though
  the service model's pattern admits it; the grant goes to the group by its profile id, which Cloud
  Control's `GetResource` for `AWS::DataZone::GroupProfile` resolves from `<domain>|<role ARN>`
  (Stage 18 2.7, 2026-10-19).
- **The `Workflows` blueprint has three states and the bill starts at the third.** Enabling it
  provides the CloudFormation template; the fee-bearing MWAA environment is born when a project
  first uses the blueprint. Neither *"enabled"* nor *"a project exists"* means billing.
- **A `VpcOnly` space started with no interface endpoints does not fail; it hangs, with a working
  terminal** (measured 2026-09-07, 6c step 6.2, the first space under design B). JupyterLab loaded,
  the terminal answered, the banner *"IDE configuration in progress"* never cleared and a Python
  kernel never returned: the app's DataZone and SageMaker calls had no route and no endpoint, so
  they got silence rather than a denial (Lesson 42), and nothing in the UI said network. The
  vendor's pages list the endpoints as required and say nothing about what their absence looks like.
  `make up ENV=sandbox` plus a stop/start of the space cleared it. The discriminator from inside the
  space is `getent hosts sts.us-west-2.amazonaws.com` (`10.20.x.x` with the endpoints, public
  without) and `curl` to the same name (`302` against a timeout). Where: `docs/SMUS.md` §`VpcOnly`,
  the client runbook §1, the 6c log.
- **An app image configuration's environment caps each value at 256 characters, and no BYOI page says
  so** (measured 2026-09-10, 6d step 2.2). `CreateAppImageConfig` refused this estate's six proxy
  variables with `ValidationException … Member must have length less than or equal to 256`; the cap is
  in the `ContainerConfig` API reference (25 entries, 256 per key and per value) and nowhere on the
  pages that recommend `ContainerEnvironmentVariables` as the way to configure a custom image. A
  generated `NO_PROXY` — 50 endpoint names, 1,442 characters — does not fit, so the documented
  mechanism cannot deliver the estate's own proxy contract. Where: `runbooks/dev-env.md` §E, and 6d
  decision due 8.
- **`CreateImageVersion` uses the image's `RoleArn` to read the repository, and resolves the tag to a
  digest once** (measured 2026-09-10, 6d step 2.1). The role is documented as *"a role that enables
  SageMaker to perform tasks on your behalf"* with a console hint to attach `AmazonSageMakerFullAccess`,
  and what it actually does is `BatchGetImage` + `GetDownloadUrlForLayer` in the **registry account** —
  visible in that account's CloudTrail as `userIdentity.type AWSAccount`, principal `<role-id>:SageMaker`,
  from an AWS-internal address. Four ECR read actions are enough. The version's `ContainerImage` then
  names a `sha256:` digest, so a registered version is pinned to bytes rather than to a tag, and
  re-tagging upstream would not move it. Where: `runbooks/dev-env.md` §C5.
- **A space's `~/shared/` writes a zero-byte folder marker for every directory** (measured 2026-10-11,
  Stage 6i step 3.6). A `cp -r` of a 176-file folder left 192 objects, 16 of them `…/` keys, and a
  `mkdir` leaves `inbox/`, which a sensor's `inbox/*` matches before any file lands. A processing input
  downloads such a prefix without complaint. Where: `runbooks/serverless-workflows.md` §A and §J1.
- **The portal's session ended twice right after another Identity Center user's CLI login** (seen
  2026-10-11, Stage 6i). Each time the user had just signed in to the CLI as the infrastructure user while
  Chrome held the Data Scientist User's portal session, and the next portal act landed on the sign-in
  page. The shared browser is the inferred cause, not an isolated one. Where: `aws/AWS-CLI.md`, "Signing
  in".
- **A project update in the portal reconciles the environment's stack, and the stack writes only what
  its template changed** (measured 2026-10-18, 6d step 2.4). An `UpdateProject` with
  `projectProfileVersion: latest` and the parameters unchanged, made by a person in the portal, was
  followed 28 s later by an `UpdateStack` by the provisioning role. The new template added
  `elasticmapreduce.amazonaws.com` to the project role's trust policy, the one IAM write besides a
  `TagRole` of a value the role already carried; the SageMaker domain resource read `UPDATE_COMPLETE`
  with no `UPDATE_IN_PROGRESS` and no `UpdateDomain`, so an attachment made by hand outside the template
  survives a reconciliation that leaves the domain's properties alone. Where: 6d step 2.4, INT-15,
  INT-17.
- **A Redshift connection made in the portal carries `lineageSync` enabled, and the form shows no
  toggle** (read 2026-10-18, Stage 6h). The same-account form of 2026-09-21 offered no lineage field;
  `get-connection` on the connection it wrote reads `lineageSync.enabled: true` on
  `cron(43 3 * * ? *)` with a lineage job of its own, which ran daily from 2026-10-11 and failed eight
  times. A run that succeeds is a scheduled query on the warehouse's meter. Where: `log-stage-06h`,
  2026-10-18, and `./aws/warehouse.py` `WH-9`.
- **A `DataLake` environment that fails keeps the Glue database its add-on created, and deleting the
  environment keeps it too** (read 2026-10-20 in both trails, 6f decision due 6). The template,
  `DataLakeDefault-prod-20250618`, declares the `AWS::Glue::Database` with `DeletionPolicy: Retain`: at
  the failure DataZone deletes the stack and no `DeleteDatabase` follows, and a later
  `DeleteEnvironment` deletes the stack again and calls none either (Staging's
  `glue_db_c2ej62w956q2a8`, Sandbox's `mydatabase`). An `ACTIVE` environment's deletion follows the same
  template and left its database too (Staging's `glue_db_d6ogysnx78dguo`, 2026-10-22, Stage 18 8.1). The portal's *Create database*
  deleted its database after one such failure (`test`, 2026-10-15, as the project role) and not after
  the other. Lake Formation leaves the database out of a non-administrator's `get-databases`, so the
  listing reads it as gone; `get-database` by name answers *"Insufficient Lake Formation
  permission(s): Required Describe"* while it exists and `EntityNotFoundException` once it does not.
  Where: `log-stage-06f-data-governance.md`, the entry of 2026-10-20.
- **`GetDataLakeSettings` returns the administrators in no fixed order** (read 2026-10-20 in Sandbox).
  Three consecutive reads gave two orders of the same three principals, and the trail holds no
  `PutDataLakeSettings` since 2026-10-15, so a change of order is no write. A reading compares the set.
  Where: `log-stage-06f-data-governance.md`, the entries of 2026-10-20.
- **The portal's MLflow entries look their blueprint up in the domain account, so a domain whose
  configurations live in associated accounts greys them out whatever the profile carries** (read
  2026-10-19, Stage 17 1.5). *Create MLflow App* and *Create MLflow Tracking Server* resolve the
  blueprint's id by name from `ListEnvironmentBlueprintConfigurations`, called with the domain id alone
  as the domain execution role. DataZone answers with the domain account's configurations, none here
  (D22), the page's query fails with *"No environment blueprint configurations found"*, and the
  tooltip says *"The MLflowApp blueprint is not enabled for this project"*. Neither the profile,
  *Update project* (`UPDATE_NOT_AVAILABLE`) nor the project's age plays a part. A `CreateEnvironment`
  with the profile's configuration id, made through the API by a project contributor, creates the app
  the entry would have. Where: `log-stage-17-sandbox-machine-learning.md`, the 1.5 entries of
  2026-10-19.
- **The portal's Generative AI menu opens only with all seven Bedrock blueprints in the profile**
  (read 2026-10-19, Stage 17 1.5). Its module maps the profile's configurations to `ChatApp`,
  `Evaluation`, `FlowApp`, `Function`, `Guardrail`, `KnowledgeBase` and `Prompt`, and answers the
  Playground and *AI apps* with *"This tool is not available for this project"* when one is missing,
  so a profile carrying six, the knowledge base left out on cost, opens none of them. Where: the same
  entries.
- **An associated account's Bedrock models tab enables no model until the domain holds a project named
  `GenerativeAIModelGovernanceProject`, and only the domain account's setup creates one** (read
  2026-10-19, Stage 17 decision 13). In `Sandbox Account 1` the *Amazon Bedrock models* tab greys out
  *Manage* with *"Model governance project does not exist"* (measured 19:51 UTC). The console's code
  creates the project, on a profile *Generative AI model governance* with no environment configuration,
  only in the domain account's setup, the run that also configures the Bedrock blueprints and `Tooling`
  in the domain account, where D22 configures none; an associated account's *Set up generative AI*
  creates neither. The console finds the project through `ListProjects`, by id or by that name: one written by
  Terraform, with the account's `InfrastructureAccess` session group as a contributor, opened *Manage*
  (20:33), and the Submit created the models' environments and assets in it (20:52). AWS's page says the
  service creates the project, owned by whoever configures Bedrock for the domain, and that an associated
  account's identity must join it; it says neither which setup creates it nor what an associated account
  sees without it. Where: `log-stage-17-sandbox-machine-learning.md`, decision 13's entries of
  2026-10-19, and `terraform-live/data-governance/governance/model-governance.tf`.
- **The Bedrock models tab adopts a provisioning role by a name no AWS page gives** (read 2026-10-19,
  Stage 17 decision 13). Its Submit takes the account's role whose name contains
  `AmazonSageMakerBedrockModelManagementRole-<domain account id>`, else the role chosen in the setup
  wizard, and creates one at `/service-role/` with AWS's policy only when neither exists, all before it
  reads the role chosen per model (the console's code). A model's *Manage roles* dialog preselects that
  name as an existing role whether or not one exists (measured 19:52 UTC, with none). The role
  `sandbox/model-access/` writes under that name, at `/` under the project boundary with a policy of its
  own, served the Submit, which created no principal (20:52). The consumption dialog preselects
  `AmazonSageMakerBedrockModelConsumptionRole-<hash>` the same way, a role that did not exist. AWS's role
  page calls the role `AmazonDataZoneBedrockModelManagementRole` and its post of 2025-07-09
  `AmazonSageMakerBedrockModelManagementRole`; both say only that the service creates a role or takes a
  custom one. Where: the same entries, and `terraform-live/sandbox/model-access/`.
- **A `DataLake` environment needs `AmazonDataZoneGlueManageAccessRolePolicy` on the manage-access role**
  (measured 2026-10-20, Stage 18 7.2). The add-on has the manage-access role call
  `lakeformation:CreateLakeFormationOptIn` on the new database, which
  `AmazonDataZoneSageMakerManageAccessRolePolicy` v4 does not carry and the Glue policy v18 does; with the
  SageMaker policy alone the environment fails and its stack rolls back, which is why every Sandbox
  `DataLake` environment has been `CREATE_FAILED` since 2026-09-13. The Glue policy's ARN carries the
  `service-role/` path, which the SageMaker one does not. The module attaches it since
  `sagemaker-prereqs-v0.8.0` (PR #207), and Staging's `staging/studio/manage-access.tf` until that slice
  leaves v0.6.0. Where: `log-stage-18-staging-deployment-project.md`, the 7.2 entries of 2026-10-20.
- **A V2 domain refuses the three catalog designations the DataZone API lists** (measured 2026-10-20,
  Stage 18 6.1). `create-project-membership` with `PROJECT_CATALOG_VIEWER`, `PROJECT_CATALOG_CONSUMER`
  or `PROJECT_CATALOG_STEWARD` answers `ValidationException` *"Project member with designation <it>
  cannot be added to project in V2 domain"*, and `PROJECT_CONTRIBUTOR` is admitted. The CLI's model
  (`datazone/2018-05-10`) lists all five, while SageMaker Unified Studio's user guide names two project
  roles, Contributor and Owner, both working on the project's credentials: no designation gives a
  person a view with no write. Where: the
  Stage 18 log, 2026-10-20.

- **`glue get-table` answers a missing table as it answers a hidden one** (measured 2026-10-22 in Staging,
  Stage 18 7.2). To a principal holding no Lake Formation grant, `trades` and a made-up name both
  answered *"Insufficient Lake Formation permission(s): Required Describe"*, where `get-database`
  answers `EntityNotFoundException` for a database that does not exist; a table's existence is read in
  CloudTrail's `CreateTable` or by a principal holding `DESCRIBE`. Where: `log-stage-18`'s 7.2 entry.
- **DataZone sets `aws:SourceIdentity` on the project-role sessions it opens for a member or as
  `SYSTEM`, and on none it opens to fulfil a subscription** (measured 2026-10-21 and 2026-10-22, Stage 18
  6.2 and 7.2). A person's, an IAM principal's and a data source's `SYSTEM` sessions carried the
  caller's profile id or `SYSTEM`; the workers' (MWAA Serverless, Glue, SageMaker) and the
  `AWSDataZone-Subscriptions` sessions carried none, so a deny conditioned on the key binds the first
  and spares the second, the fulfilment's `glue:PutResourcePolicy` included. Where: `log-stage-18`'s
  6.2, 4.3 and 7.2 entries.
- **A subscription's fulfilment shares the producer's whole catalog** (measured 2026-10-22, Stage 18
  7.2). With Staging's `CROSS_ACCOUNT_VERSION` at 1, the grant DataZone wrote carried
  `CROSS_ACCOUNT_VERSION` 5 in its own parameters; the RAM share it created named Staging's `catalog`,
  `database/*` and `table/*/*` with the three ReadWrite Glue permissions, and three statements went into
  Staging's Data Catalog resource policy naming the consumer account. Lake Formation's `SELECT` under
  the subscribing project's context is what scopes the read, and the revocation removed all of it.
  Where: `log-stage-18`'s 7.2 and C1 entries.
- **Deleting a `Tooling` environment leaves its log group** (measured 2026-10-22, Stage 18 8.1): the
  stack reached `DELETE_COMPLETE` and `datazone-<project>-dev`, at 731 days, stayed.
- **SMUS's Query editor creates the project space's JupyterLab app on opening, beside its own `sqlworkbench`
  session, and the app sits in `PendingCheckout`, a state `DeleteApp` cannot take to `Deleting`** (measured
  2026-10-26, 01:26 to 01:37 UTC, the Stage 9 session's warehouse sitting). The query ran without the app;
  `make down ENV=sandbox` minutes later met the app in `PendingCheckout` (`ValidationException`) and the
  Studio-apps hook stopped the down twice, until the user closed the editor, the portal stopped polling at
  01:36:20 and `DeleteApp` went through at 01:37:03. Where: `log-stage-09-deployment-targets.md`, 2026-10-26.

### MWAA, provisioned

- **`airflow:CreateEnvironment` authorizes before it validates the network configuration** (measured
  2026-10-18, Stage 10 4.3). A call naming two subnets of Production, a security group, a role and a
  bucket that do not exist read the root baseline's `DenyProvisionedMwaa` with the policy id, so the deny
  is attributable without a valid environment. Where: the Stage 10 log.

### MWAA Serverless

- **`list-workflow-runs` returns `RunType` null for every run, and `get-workflow-run` carries it**
  (measured 2026-10-10, on Sandbox's two portal-authored workflows). The service model declares
  `RunType` (`ON_DEMAND` | `SCHEDULED`) in `WorkflowRunSummary`; all six listed runs read `null`, and
  each read `ON_DEMAND` one at a time. A check that takes the type from the list sees no `SCHEDULED` run
  whether one fired or not, and that is Stage 10 verification (v)'s evidence. Where:
  `aws/orchestration.py` section 7, `log-stage-06d`'s sixteenth sitting.
- **A worker fetches its `Code` snapshot as the service principal, through the customer's S3 gateway
  endpoint** (measured 2026-10-11, Stage 6i decision 7). At each save the service copies the code object
  to `mwaa-serverless-code-files-<AWS-owned account>-<region>-prod`, keyed by account, workflow, version
  and the upload's key. Each task's environment preparation then has `airflow-serverless.amazonaws.com`
  `GetObject` it through the workers' VPC, so the gateway endpoint's policy must admit a bucket the
  customer neither owns nor names. A refusal surfaces only as "Execution environment preparation failed
  due to an internal server error". The guide names neither the bucket nor the path. Where:
  `runbooks/serverless-workflows.md` §O and §C, `log-stage-06i`'s 4.2a entries.
- **Every save takes a new code snapshot, and the portal uploads the code again at every save**
  (measured 2026-10-11, Stage 6i verification vii). A description-only edit made a new workflow version
  and moved `CodeSnapshottedAt` with the code unchanged, and a refused save uploaded the file all the
  same. Where: `runbooks/serverless-workflows.md` §C5.
- **The portal's save sends a code location the editor pre-fills, and an import cannot replace a saved
  workflow** (measured 2026-10-10/11, Stage 6i). A new workflow's *Settings → Storage* carries
  `dev/operatorFiles/<workflow>.zip`, a processing-only workflow's included; saved with no file there,
  the service answers `ValidationException: Code not found in specified S3 location`. An import into a
  saved workflow's editor makes a new workflow under the bare name, whose save is refused with
  `ConflictException`. Where: `runbooks/serverless-workflows.md` §A.
- **A Bash task's script is rendered as a Jinja template, and its `PYTHONPATH` carries the code folder**
  (measured 2026-10-11, Stage 6i pass 5). `bash_command: reach_pypi.sh` ran as `bash <tmp>.sh`, the
  archive's file rendered into a temporary file; an inline command needs no archive; `PYTHONPATH` starts
  with `/usr/local/airflow/dags`. Where: `runbooks/serverless-workflows.md` §C4.
- **The worker's resolver reports a DNS Firewall block as errno 16** (measured 2026-10-11, Stage 6i
  step 5.0). `pypi.org` answered `NXDOMAIN` with `firewall_rule_action` `BLOCK`, and Python read
  `OSError(16, 'Device or resource busy')`, pip `[Errno 16]`, rather than a name error. A worker failing at
  resolution with "Device or resource busy" is a blocked name. Where: `runbooks/serverless-workflows.md` §O.
- **A run's state lags its task instances, and the workflow's log group exists from its first save**
  (measured 2026-10-11, Stage 6i step 3.8). `get-workflow-run` read `QUEUED` until 23:06:16Z while the
  sensor had finished at 23:05:23Z, and `/aws/mwaa-serverless/<domain>-<project>/<workflow>` existed,
  empty and with no retention, before any run. Where: `runbooks/serverless-workflows.md` §V and §O.

### The SageMaker Unified Studio CI/CD CLI

- **`deploy` reads a manifest's local content from the manifest's folder, whatever
  `--bundle-archive-path` names** (measured 2026-10-19, Stage 18 4.2, `aws-smus-cicd-cli` 1.0.9). A
  `content.storage` item that names no connection is copied from the folder the manifest sits in; run
  from a checkout with a release's bundle, the deploy wrote the checkout's files and none of the
  bundle's. A promotion that deploys a stored bundle extracts it and puts the stage's manifest beside
  it. Where: `log-stage-18`'s 4.2 entries.
- **`workflow.create` and the operator-code lookup scan the project's whole shared root, whatever
  `targetDirectory` says** (measured 2026-10-19, Stage 18 5.2, the same version). The scan's prefixes
  come from `target_directory`, a name the manifest's `StorageConfig` does not carry, so they fall back
  to the root, and the first file in S3's listing order wins each workflow name or DAG id. An
  application whose workflow reused `app-etl`'s name and DAG id read and rewrote `app-etl`'s YAML, was
  created from `app-etl`'s definition, and its `destroy` plan then held `app-etl`'s Glue job, since
  `destroy` reads the Glue jobs from the workflow's definition as the service holds it. Where:
  `log-stage-18`'s pass 5 entry.

### CloudTrail

- **CloudTrail Lake refuses a new customer, and the network activity guide still offers it** (measured
  2026-10-11, Stage 6i step 4.2a). `CreateEventDataStore` answered `InvalidParameterException: CloudTrail
  Lake is no longer accepting new customers. Existing customers can continue to use their event data
  stores.` An account that never created a store is a new customer. The guide's network activity page
  and the 2024 announcement both offer an event data store beside a trail. Where: `log-stage-06i`'s
  4.2a entry, `PRICING.md`.
- **Network activity events cover an S3 gateway endpoint, under a prefix of their own** (measured
  2026-10-11, Stage 6i step 4.2a). A trail's files arrive under `AWSLogs/<account>/CloudTrail-NetworkActivity/`,
  beside `CloudTrail/`. A refusal by the gateway endpoint's policy reads `errorCode` `VpceAccessDenied`,
  names the bucket for a path-style request as for a virtual-hosted one, and shows another owner's
  account as `HIDDEN_DUE_TO_SECURITY_REASONS`. The announcement names S3 and never says "gateway".
  Where: `log-stage-06i`'s 4.2a reading.

- **A role's own account records a caller from another account with no ARN, and an absent field fails
  EventBridge's `anything-but`** (measured 2026-10-13, Stage 8 step 4.6). Staging's copy of the deploy
  runner's `AssumeRole` reads `userIdentity.type` `AWSAccount`, a `principalId` of `<role unique
  id>:<session name>`, the caller's `accountId` and a `sharedEventID`, and no `arn`; an SSO session's reads
  `AssumedRole`, still with no `arn`. `TestEventPattern`
  answered `false` for a pattern exempting the runner by `userIdentity.arn` on that record with another
  account's role in it, so the rule could never fire on a caller from outside. The operators page says
  `anything-but` matches *"anything except what's specified"* and speaks of absence only under `exists`.
  The role's account does deliver that copy to its event bus: a misuse from Production fired Staging's
  rule (verification xvi). A refused cross-account `AssumeRole` is recorded in the caller's account only,
  with `requestParameters` null and the role named in `errorMessage` alone. Where: `log-stage-08`'s
  2026-10-13 entries, `deploy-role-v0.2.0`.
- **An `AssumeRole` event names its role by ARN, so a `ResourceName` lookup by the role's name finds
  none of them** (measured 2026-10-21 in Production). By ARN the lookup answered the same event ids as
  the `EventName=AssumeRole` history, 80,211 events since 2026-08-09: `awsds-deploy-prod` 12, Staging's
  `awsds-deploy-staging` 12, `awsds-prod-proxy` 476, and the Config service-linked role 627 on
  2026-10-19. By name it answered no `AssumeRole`. The user guide's only `ResourceName` example is a role
  name. Where: `aws/deploytargets.py` §8 and `aws/cicd.py` `CI-8`, both by ARN.

### SageMaker processing jobs

- **A processing job reads `Completed` minutes after it ends, and the operator bills the wait**
  (measured 2026-10-11, Stage 6i step 3.8). `ProcessingEndTime` was 23:16:26Z, the outputs had landed at
  23:16:21Z, and `describe-processing-job` still read `InProgress` at 23:18:33Z and `Completed` at
  23:18:54Z. `SageMakerProcessingOperator` waits on that status, so its task held a worker 791 s for a
  one-second command: about 3 minutes of provisioning before `ProcessingStartTime`, 7 of image pull, and
  this tail. Where: `runbooks/serverless-workflows.md` §J.
- **An extension module imports from a processing input** (measured 2026-10-11, Stage 6i verification
  xvi). `msgspec`'s `_core.cpython-313-x86_64-linux-gnu.so` loaded from `/opt/ml/processing/code`, which
  SageMaker had downloaded from S3 with the prefix's folder markers. No page says whether the input
  volume admits executable mappings. Where: `runbooks/serverless-workflows.md` §J1.
- **`iam simulate-custom-policy` ignores `sagemaker:VolumeKmsKey` and `sagemaker:OutputKmsKey` when the
  resource is a job's ARN** (measured 2026-10-18, 6d step 1.3). A `Deny` on `Null` of either key matched
  a `CreateProcessingJob` or `CreateTrainingJob` that supplied the key against `processing-job/…` or
  `training-job/…`, and did not match against `*`; `sagemaker:VpcSubnets` was read both ways. The real
  call reads the key: 6i's four jobs carried `VolumeKmsKeyId` past the boundary's copy of the same deny.
  A simulation of a job's settings runs with the default resource `*`. Where: 6d step 1.3. Read again
  2026-10-24 for `CreateTransformJob` against `transform-job/…`, in `simulate-principal-policy` through the
  live `Workloads` document too (`log-stage-10`, 2026-10-24).

- **`CreateProcessingJob` checks the instance quota after authorization and before the role** (measured
  2026-10-17 and read in CloudTrail on 2026-10-18, Stage 9). In Production, where the processing quotas of
  `ml.m5.large` and `ml.m5.2xlarge` read 0, six calls naming a role that does not exist answered
  `ResourceLimitExceeded`, never `ValidationException`; after the `Workloads` document's apply the same
  calls answered the SCP's deny. So a quota of 0 hides the validation a probe relies on, and reads as
  authorized. Where: the Stage 9 log, `aws/probes/probes.py` `_JOB_AUTHORIZED`.

### Athena

- **`DeleteWorkGroup` counts query history as contents, and no API deletes a query execution.** A
  workgroup with zero named queries and zero prepared statements still refuses to delete while old
  executions remain, and those age out on Athena's own 45-day clock. The only door is
  `RecursiveDeleteOption`. The Terraform corollary: that door is a configuration argument
  (`force_destroy`) and a destroy runs from the attributes in state, so the flag has to be set in
  the configuration before the resource is removed from it. Deleting the block and the flag in one
  version leaves the destroy unarmed, which surfaces only at destroy time.

### EC2

- **A Data Lifecycle Manager policy description admits `[0-9A-Za-z _-]` and nothing else** (measured
  2026-10-12, Stage 7 step 1.2): an apostrophe or a parenthesis fails the plan with `invalid value for
  description`, naming the CLI reference rather than the character. The Terraform provider validates it
  at plan time, which is the cheap place to meet it. Where: `terraform-live/production/tooling/main.tf`.
- **`associate_public_ip_address` read-back fights an `aws_eip_association` forever.** With an
  Elastic IP attached, the refresh reports the attribute from the instance's current public address,
  so the next plan wants to destroy and recreate the instance on a ForceNew diff that nothing
  changed. Measured on the first VPN apply, 2026-08-17; the fix is `ignore_changes` on the
  read-back, while the argument stays load-bearing at launch.
- **Changing `instance_type` is a stop/modify/start, and user data does not re-run on it**, so a
  size change made because the build ran out of memory leaves the bigger host unbuilt. Only a
  replacement re-runs a first boot.
- **A cross-Region inference profile is authorized once per destination Region, and `aws:RequestedRegion`
  in that evaluation is the destination, not the caller's** (measured 2026-09-12, Stage 6e step 6). A
  call made with `--region us-west-2` and logged by CloudTrail with `awsRegion: us-west-2` was denied
  against `arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-5` by Control Tower's
  `CT.MULTISERVICE.PV.1`, whose only condition is `aws:RequestedRegion != us-west-2`. No vendor page
  connects the two, and the consequence is that **a Region ceiling refuses every cross-Region profile in
  the organization** until the invoke actions are exempted. Where: `claude-code-sagemaker.md` M5.
- **`InvokeModel` refuses an application inference profile id that does not exist before it
  authorizes** (measured 2026-10-19, Stage 17 decision 11). As `InfrastructureAccess` in
  `Sandbox Account 1`, with `DenyBedrockInvocationOutsideTheScopedModels` naming no
  `application-inference-profile`, the call answered `ValidationException`, *"The provided model
  identifier is invalid"* (21:33 UTC), and the battery's row had read that call as `ALLOWED`,
  `reached-authorization`. A profile the console minted was refused by that statement at 21:13,
  `InvokeModelWithResponseStream` as the playground's consumption role (7.3's first chat). The API
  reference and the troubleshooting page name both errors and neither the message nor the order. A probe
  of a statement on application inference profiles therefore needs an id the service minted (Lesson 21),
  and the battery carries no such row. Where: `log-stage-17-sandbox-machine-learning.md`, decision 11's
  entries of 2026-10-19, and the note on decision 11 in `aws/probes/probes.py`.
- **Bedrock's data retention mode is per account AND per Region** (measured 2026-09-12). The account read
  `none` in `us-west-2` and `inherit` in the two Regions its own profiles route to; `get-account-data-retention`
  answers independently in each. A mode declared once is a claim about one Region, and whether cross-Region
  inference obeys the source Region's mode or the destination's is in no API and on no page. Where:
  `claude-code-sagemaker.md` M1, `AWS_STATE.md` `EXC-07`.
- **The Bedrock use-case form does not enable a model; the agreement does** (measured 2026-09-12). With
  the form submitted and readable in all three Regions, `create-foundation-model-agreement` against an
  offer token was still required per model — the act the console calls *Enable specific models*.
  `agreementAvailability.status: NOT_AVAILABLE` means **no agreement has been created**, not *no
  agreement is needed*, and reading it the second way is what hid the omission through three separate
  readings. The agreement is account-wide: created in one Region it reads `AVAILABLE` in the others
  before the creating Region leaves `PENDING`. Amazon's own models need none. Where:
  `claude-code-sagemaker.md` M4.
- **A Bedrock model can be gated commercially with every readable instrument reporting it available**
  (measured 2026-09-12). `anthropic.claude-sonnet-5`: agreement `AVAILABLE`, `authorizationStatus
  AUTHORIZED`, `entitlementAvailability AVAILABLE`, `regionAvailability AVAILABLE`, `modelLifecycle
  ACTIVE`, form present — and `AccessDeniedException … not available for this account … contact AWS
  Sales` for every principal including `AdministratorAccess`, while the previous generation answered.
  **The invocation is the only instrument that answers whether a model can be used**, which is
  Lesson 13 at account scale. Where: `AWS_STATE.md` `EXC-08`.
- **A streaming Bedrock invocation writes two CloudTrail events; a non-streaming one writes one**
  (measured 2026-09-12). `InvokeModelWithResponseStream` records one event carrying
  `requestParameters.modelId` and a sibling carrying `requestParameters: {}` — 9 and 9 in one hour —
  while `InvokeModel` records a single event, 4 with a `modelId` and none without in the same hour.
  Counting events doubles a streaming client's calls; **counting events that name a `modelId` and
  carry no `errorCode` counts each invocation once**, and it equals CloudWatch's per-model
  `Invocations` exactly (22/20/3 over one evening). `responseElements` is `null` on both, which is the
  attribution-without-content property Stage 6e 4.6 claims, measured. **A denied call reaches
  CloudTrail with no `modelId` at all**, so refusals cannot be attributed to a model there — and they
  do not reconcile with CloudWatch either: one hour held 18 `AccessDenied` events against 6
  `InvocationClientErrors`, a metric AWS publishes only without a `ModelId`.
- **CloudWatch carries a cross-region profile's tokens in the source Region, with invocation
  logging off** (measured 2026-09-12). `AWS/Bedrock` publishes `Invocations` and four token counts per
  `ModelId` — the `us.` profile id — in `us-west-2`, whichever Region processed the prompt; the
  dimensionless series equals the per-model sum for all four token metrics. The Control Tower Region
  ceiling refuses `cloudwatch:ListMetrics` in `us-east-1` and `us-east-2`, so nothing else could have
  been read. And `ListMetrics` names only series with data in the last two weeks. Where:
  `aws/bedrock-usage.py`.
- **`ListInferenceProfiles` with no `typeEquals` returns the system-defined profiles alone** (measured
  2026-10-19). In `Sandbox Account 1`, which held two application inference profiles, the call with
  no type returned 96 profiles, every one `SYSTEM_DEFINED`, and `--type-equals APPLICATION` returned
  the two. The API reference names both values and no default. Where:
  `aws/awslib/inferenceprofiles.py` asks for each type by name, for `aws/bedrock-usage.py` to rate a
  series published under an application profile's id, for `aws/bedrock.py` section 5 to list both
  types and for `aws/bedrock-scope.py`'s `BS-2` to read the declared `us.` profiles, which are
  `SYSTEM_DEFINED`.
- **A Control Tower control is written from `Management` and read from anywhere** (measured
  2026-09-12). `controltower:` answers only in the management account — a member account is told to
  create a landing zone first — but the control writes an ordinary SCP, and
  `organizations describe-policy` returns its document from a delegated-admin account. So a console
  act on a control has a **mechanical verification**: the `NotAction` count, 86 in the
  `CT.MULTISERVICE.PV.1` template and 92 after six additions. This matters because the obvious
  verification is the opposite of an instrument — re-attempting the denied call returns the same
  refusal whether the form failed to propagate or something else in the chain is missing (Lesson 24).
  Where: `claude-code-sagemaker.md` M5.
- **A SageMaker space keeps its own copy of the custom image version number**, in
  `SpaceSettings.<app>AppSettings.DefaultResourceSpec`, written when the space is created — and it
  **overrides the domain's `DefaultUserSettings`**. Measured 2026-09-12: with version 4 attached to the
  domain, an existing space still named version 3, which the same apply had destroyed
  (`aws_sagemaker_image_version` is force-new on `base_image`). AWS's own images are referenced by a
  mutable **alias** instead, which survives a bump. **An app started against the destroyed version
  fails to start** rather than falling back (measured the same evening). Where: `dev-env.md` §B,
  *Moving a space*, `AWS_STATE.md` `EXC-09`, Lesson 63.
- **`describe-app` still returns the `ResourceSpec` of an app that has been deleted** (measured
  2026-09-12), so the image a removed space ran can be attributed after the fact. A space deleted
  within the hour read `sagemaker-distribution-cpu`, alias `4.3`, with `Status: Deleted` — the
  evidence that it had been created on AWS's image rather than this estate's, which is what its
  missing proxy variables had looked like a defect of. Where: `dev-env.md` §C7.
- **`UpdateDomain` changes `CustomImages` with apps running, whatever the vendor's page says**
  (measured 2026-10-15 on a probe image, Stage 8 decision 7). The detach page reads *"Before you can
  update the custom images, you must delete all of the applications in your domain"*, and four
  `update-domain` calls changing the list were accepted with apps `InService`, one removing an entry
  while two apps ran on that image. Each read back identical, and the running apps were untouched.
  Where: `dev-env.md` §C6.
- **A `CustomImage` with no `ImageVersionNumber` offers every version of the image** (measured
  2026-10-15). The portal's picker listed each version, newest first, as `<display name> v<n>`,
  including one created after the attach and one no space named, and the portal's `CreateSpace` pinned
  the chosen version's ARN into the new space. The API reference says only that the field is optional.
  Where: `dev-env.md` §C6 and §B.
- **`VendorGuidance ARCHIVED` hides nothing from the portal, and an archived version still starts**
  (measured 2026-10-15). With a version `TO_BE_ARCHIVED` and then `ARCHIVED`, the picker kept offering
  it under the same label, `list-image-versions` kept listing it, and a space pinned to it started and
  pulled it by digest. Deleting it is what took it out of the picker. Where: `dev-env.md` §B, *The
  retirement*.
- **A custom image's alias works in a space's spec, and the portal reads it as the SageMaker
  Distribution's** (measured 2026-10-15). `update-space` accepted `SageMakerImageVersionAlias` with the
  version ARN cleared by `"None"`; the app resolved the alias at each start and followed it to another
  version; and the portal then bannered the space as running an *outdated SageMaker Distribution image*.
  The same `update-space`, sent the whole live block, left `SpaceManagedResources: ENABLED` out of the
  read afterwards. Where: `dev-env.md` §B, *Moving a space*.
- **Opening a project's *Spaces* page in the portal starts its default space** (read 2026-10-15).
  CloudTrail recorded a `CreateApp` on the default space, by the project role in the data scientist's
  portal session and on AWS's distribution by alias, as the page loaded, and the app ran until its idle
  shutdown. Where: `dev-env.md` §C7.
- **`PutAccountDataRetention` publishes `bedrock:DataRetentionMode` at request time** (measured
  2026-09-12 in `Policy Canary`), so a `StringNotEquals` deny on it is a mode ceiling and not a
  blanket deny on the action. **A condition key being in a service's catalogue and a key being
  published by a given action are two claims**, and `accessanalyzer validate-policy` answers only the
  first: it accepts a statement conditioned on a catalogued key whatever action it is written against.
  The second is a call, and the vendor documents neither. The mode enum is also four values —
  `default`, `none`, `provider_data_share`, `inherit` — where this plan had discussed two. Where:
  `claude-code-sagemaker.md` M3.
- **A schedule-only State Manager association does not fire when an instance starts** (measured
  2026-09-19 on the proxy host). The association is `cron(0/30 * * * ? *)` and its
  `LastExecutionDate` was **20:00:40Z**; `make hub-up` started the host at **20:04:55Z**; at 20:25Z
  the host was still serving the `squid.conf` of its previous session - 25 entries against the
  parameter's 32, missing both of that day's applies, one of which had been written while the host
  was stopped. The next scheduled run at **20:30:53Z** reported `Success` with **empty stdout**, and
  `PX-3` read 32 against 32 immediately after. What it means here: **starting the hub does not put
  the committed policy in force**, and for up to one cron interval the proxy enforces the previous
  session's allow-list. A parameter written while the host is stopped is not rendered by the start
  either, so the lag is not bounded by how old the edit is. Where: `NETWORK.md` the proxy's filters,
  `log-stage-06d` the fifteenth sitting.

- **The database identity of a SMUS Redshift connection is the ACCESS ROLE, not the project role and
  not the person** (measured 2026-10-10, from the account's own trail). `redshift-serverless:GetCredentials`
  is called by the assumed access role; the project role's own calls are `ListWorkgroups`, which fills
  the compute dropdown, and the `sts:AssumeRole` that gets there. So the `RedshiftDbUser` tag belongs on
  the access role, layer 2's reach has to be attached to **both** roles for different reasons, and
  *whose identity reaches the database* is a third answer again after Stage 6d step 7's `StartSession`.
  **Creating the connection mints no database session**: the compute reads `Available` with `pg_user`
  unchanged, because a database user is created when credentials are used rather than when they are
  minted. Where: `log-stage-06h` (2026-10-10).

- **The Redshift Serverless audit export carries nothing while a workgroup exists** (measured
  2026-10-17 over the groups' 30-day retention). Configuration is not the explanation: the namespace
  exports all three groups, unchanged since its creation. After the first day no record of any kind
  arrived during any of seven workgroup lifetimes, and the namespace's own `rdsdb` sessions arrive in a
  `default` stream, about 29,000 a day, only while no workgroup exists, from about a day after a delete
  until two minutes after the next create. The one window of user activity is the admin's Data API
  sessions of 2026-09-21, 23 minutes long: 36 of the 268 Data API calls CloudTrail holds for those two
  days, and no session through any other door.
  **The reading of 2026-10-10 was a sampler's** (inference): 155 records at a ~2h25m cadence fit one
  record per 1 MB `FilterLogEvents` page over the 444,502 records the group held, so the *heartbeat* was
  the pager's, and the *stop* at 03:09:06 was that day's first create silencing the stream. **The
  reading to carry**: before an absence or a cadence in a log group is evidence, count it with an
  aggregate (Logs Insights `stats count(*) by bin(1h)`), not by paging events (Lesson 62's wrong path).
  Stage 11 must not rest a DLP feed on these groups. Where: `log-stage-06h` (2026-10-10, 2026-10-17), `log-stage-05b`, Stage 11.

- **A Redshift schema shared by a role shares nothing IN it, and `pg_default_acl` cannot tell you**
  (measured 2026-10-10, on the first table a project ever wrote). A role holding
  `USAGE, CREATE ON SCHEMA` lets every admitted project create its own tables and carries **nothing at
  table level**: the new table's `relacl` was **null**, so a second project granted the same role would
  have had `CREATE` and read **none** of the first's data — not reduced access, none. The fix is
  `ALTER DEFAULT PRIVILEGES`, set **per creating user**, so a shared schema owes one statement per
  admitted project (Lesson 14) plus one `GRANT` per table that already exists.
  **And the verification is not where PostgreSQL keeps it**: `pg_default_acl` returns zero rows after a
  successful `ALTER DEFAULT PRIVILEGES`, and the privilege lives in **`svv_default_privileges`** alone —
  the mirror of the schema trap, where `nspacl` is the authority and the `SVV_` view shows only RBAC.
  A statement that reports `FINISHED` and a catalog that reports nothing is Lesson 54's shape, and the
  cheap resolution is to look for the platform's own view before believing either.
  Where: `log-stage-06h` (2026-10-10), `runbooks/redshift-connection.md` §T, `WH-14`.

- **Two sessions on the same role carry different session tags, and the session NAME is the only
  thing that tells them apart** (measured 2026-10-10, after reading one for the other). SMUS assumes
  one project role from two places: the portal's session, named `<Identity Center user id>@<environment
  id>`, carries `RedshiftDbUser` **and `RedshiftDbRoles`**; the space's session, named `SageMaker`,
  carries `RedshiftDbUser` and **not** `RedshiftDbRoles`. Both appear in one `lookup-events` output,
  identical but for `roleSessionName` and the tag list — and a capability read off the wrong one becomes
  a mechanism you then cannot make work, with nothing broken to find. **`transitiveTagKeys` was `None`
  on both**, so no tag survives a further chain. Read `roleSessionName` before attributing a session
  tag, and treat "the role carries X" and "this session carries X" as different claims — a role tag is
  overridden by a session tag of the same key, so the role's value can be live and irrelevant at once.
  Where: `log-stage-06h` (2026-10-10), 6h decision 8a.

- **Two doors into one database resolve to two DIFFERENT database users, one per project and one per
  person** (measured 2026-10-10). The same warehouse, the same schema, the same project: through the
  portal's Data page the grantee is `IAMR:<the project role's name>`, set by the access role's
  `RedshiftDbUser` tag; through JupyterLab, where the project role reaches `5439` directly, Redshift
  **auto-creates `IAMR:user-<Identity Center user id>@<project id>` holding nothing**. So a `GRANT`
  written for one door leaves the other with a session that authenticates and can read nothing — and
  this grantee **cannot be pre-made**, because it does not exist until that person first connects.
  Asking "is the database user per project or per person" has no answer: it is a property of the path,
  not of the design. **The per-person `GRANT` is the trap** — it is the identity seam, one statement per
  person per schema; the mechanism that fits is `RedshiftDbRoles` on the role the user signs in with,
  which maps roles at first sign-in. Where: `log-stage-06h` (2026-10-10),
  `runbooks/redshift-connection.md` §T, `docs/AWS_STATE.md`'s Redshift register.

- **`RedshiftDbUser` decides the database user, and Redshift prefixes its VALUE with `IAMR:`**
  (measured 2026-10-10). The tag on the access role carried the project role's *name*, and the session
  ran as `IAMR:<that name>` — 142 queries attributed to it. The discriminator is that an ignored tag
  would have produced `IAMR:<the access role's own name>`, and it did not. So the documented
  `IAMR:<role>` spelling applies to the **tag value**, which is not a role at all, and a grant written
  for the unprefixed value reaches nobody. Where: `log-stage-06h` (2026-10-10),
  `runbooks/redshift-connection.md` §P.

- **A CloudTrail `eventName` is not the IAM action that event authorizes, and a policy written from
  the event name grants nothing** (measured 2026-10-10, and it cost an apply cycle). The portal's
  refusals logged events `GetResources` and `ExecuteQuery`; the denial **message** on those same events
  named the action being checked, and it was `sqlworkbench:CreateConnection` — with
  `sqlworkbench:DriverExecute` behind a second `GetResources`. One event authorizes a differently-named
  action, and several events authorize the same one. A policy granting `sqlworkbench:GetResources`
  changed nothing and the next refusal was identical to the first, which is the dangerous part: the
  symptom does not say the grant missed.
  **Read `errorMessage`, not `eventName`** — `is not authorized to perform: <action>` is the only
  authoritative statement of what to grant, and it also distinguishes the policy type
  (*"no identity-based policy allows"* against an explicit deny). Two services in this same window gave
  neither: Glue answered `An unknown error occurred` for `GetCatalogs`, and Lake Formation answered
  *"Insufficient Lake Formation permission(s): Required Describe on raw"* — **not an IAM failure at
  all**, so the action was inferred from the event name there, by necessity rather than by choice.
  The corollary for managed policies: `AmazonRedshiftQueryEditorV2NoSharing` v9 **does** carry both
  real actions (`DriverExecute` unconditionally, `CreateConnection` under
  `aws:RequestTag/sqlworkbench-resource-owner`), and the earlier reading that it did not was this same
  confusion written down as a fact about AWS. Where: `log-stage-06h` (2026-10-10),
  `sandbox/warehouse/iam.tf`, `runbooks/log-debugging.md`.

- **A refused `sts:AssumeRole` records no `roleArn` in CloudTrail** (measured 2026-10-10). Both denials
  carry `requestParameters.roleArn` absent and no `externalId`, while the successes in the same window
  carry the target in full. The trail says *denied*, not *denied for what*, so the role that was actually
  requested comes from the caller's own error text — read it before attributing a refusal from the trail
  alone. Where: `log-stage-06h` (2026-10-10), `runbooks/log-debugging.md`.

- **`cloudtrail lookup-events` can answer "no events" for events it holds** (measured 2026-10-10). A
  lookup by `EventName=GetResources` returned nothing; a lookup by
  `EventSource=sqlworkbench.amazonaws.com` two minutes later returned six `GetResources` events in the
  same window. Indexing lag or an index that does not carry them — either way, **an absence from a
  lookup run shortly after the fact is not evidence of absence** (Lesson 62). Sweep by source before
  concluding that a call was never made. Where: `log-stage-06h` (2026-10-10).

- **The SageMaker Unified Studio portal requires an access role on a SAME-ACCOUNT Redshift
  connection, and both AWS's procedure and the field's own help say it does not** (measured
  2026-09-21, by the user, in the form). *"Gaining access to Amazon Redshift resources"* splits in
  two: the same-account procedure is three steps and names no role — the admin tags the workgroup and
  its namespace and *"then must send you a username and password for a database user"* — while the
  access role, its trust policy and the `RedshiftDbUser` tag live entirely under *"resources in a
  different account"*. The form's help says *"Access role ARN is optional. Required when connecting to
  resources in a different AWS account."* The form then refuses to submit without it, same account,
  same VPC, while marking **`AWS Secret` optional** beside it. Lesson 41 with the polarity reversed: a
  vendor **optional** the implementation makes mandatory, so the premise that travelled was the wrong
  one in both directions. Where: `log-stage-06h` (2026-09-21), `sandbox/warehouse/iam.tf`.

- **"IAM credentials" is not a credential type in the DataZone API at all** (read 2026-09-21 from
  `aws datazone create-connection`'s own model). `redshiftProperties.credentials` is a tagged union
  with exactly two variants, `secretArn` and `usernamePassword`. The portal's third option is
  `awsLocation.accessRole` plus the role's `RedshiftDbUser` tag, which *"determines the federated
  database user"* — a shape that carries **no standing credential**, which is why the requirement above
  turned out to be the better outcome and why the purpose-made secret held in reserve was never built.
  Two things the pages do not say: whether `RedshiftDbUser` is used verbatim or prefixed the way an
  IAM-derived user is spelled (`IAMR:<role>`), and — from the serverless side — that
  **a database user is created on first sign-in**, so the grant can be pre-made or not at all.
  `RedshiftDbRoles` maps roles at that first sign-in, and *"in a case where you pass a role name that
  doesn't exist in the database, it's ignored"*: a silent nothing, which is why it was refused.
  Where: `log-stage-06h` (2026-09-21).

- **DataZone refuses connection operations to an identity that is not a project member, in its own
  authorization layer rather than in IAM** (measured 2026-09-21). `datazone list-connections` as the
  account's `InfrastructureAccess` role: *"User is not permitted to perform operation:
  ListConnections"* — no IAM policy is involved and none can fix it. So the account's administrator
  cannot read, let alone create, a project's connections; the act belongs to a project member in the
  portal. Lesson 28's intersection, with the second permission system being the product's own.
  Where: `log-stage-06h` (2026-09-21).

- **A failed `CreateNamespace` rolls the namespace back and leaves its managed secret behind**
  (measured 2026-09-20). Redshift Serverless creates the admin credential in Secrets Manager, then
  the namespace; when the namespace creation failed on an inaccessible KMS key, the namespace was
  rolled back and the secret was not. It survives as `redshift!<namespace>-<username>`,
  `OwningService: redshift`, rotation enabled, tagged with a **namespace ARN that no longer
  resolves** — and the next attempt fails with a *different* message, *"Unable to create secret for
  the dbInstance because a secret with a matching name exists"*, which reads like a name collision
  rather than the residue of the previous attempt. The name is derived from the namespace **and the
  admin username**, so changing either gets past it and leaves the orphan. Where: `AWS_STATE.md`
  `EXC-12`, `log-stage-05b` the first sitting.

- **Redshift Serverless rotated a managed admin secret with no workgroup** (measured 2026-10-20, Stage
  5b). AWS's page *Managing Amazon Redshift admin passwords using AWS Secrets Manager* says such a
  rotation fails and is never retried. Sandbox's first scheduled rotation ran on 2026-10-20 with no
  workgroup since 2026-10-16: Redshift's service-linked role wrote and promoted the new version, and
  `CompleteRotation` reported `Succeeded`. Whether the database followed is unread; the next
  `./aws/warehouse.py --sql` authenticates with the rotated secret. Where: `AWS_STATE.md` `EXC-13`,
  `log-stage-05b` (2026-10-20).

- **A Redshift Serverless workgroup's endpoint host survives a delete and re-create; its id does
  not** (measured 2026-09-20). Destroy and re-create under the same name and
  `endpoint.address` is byte-identical — it is derived from the name, the account and the Region —
  while `workgroupId` changes (`75b926c8-…` → `4b0577a2-…`), the usage limit's id changes, and the
  workgroup's VPC endpoint and both its ENIs are replaced with new private addresses. **The ARN
  carries the id**, so any IAM or SCP statement scoped to a workgroup's exact ARN stops matching
  after the first teardown, silently, presenting as a principal whose queries stopped
  authenticating with no diff anywhere. Two ENIs also linger in `available` state for under two
  minutes after the destroy, still referencing the security group, which would fail a teardown of
  the slice that owns it inside that window. Where: `log-stage-05b` 1.9, and the comments on
  `sandbox/warehouse/iam.tf` and `DenyRedshiftCostGuardTamperingExceptInfrastructure`.

- **A breached `deactivate` usage limit does not show in the workgroup's status, and refuses only
  the compute** (measured 2026-09-20). With the limit breached, `get-workgroup` still reads
  `status: AVAILABLE` and nothing in the workgroup's record mentions it; `UsageLimitAvailable`
  reports a stale figure against the previous amount; and the client sees six words with no policy,
  no limit id and no amount: `ERROR: Query reached usage limit`. **Leader-node queries keep
  answering** — `select 1`, `select count(*) from pg_attribute`, `svv_all_schemas` — while a
  `CREATE TABLE` is refused, so *"connect and `select 1`"* passes on a warehouse that cannot run a
  real query. **Recovery is immediate on raising the amount**, with no wait for the period to roll
  over, which no vendor page states. Also: a second `deactivate` limit is refused outright (*"Only
  one DISABLE usage limit allowed per feature"*) and a second, looser `log` limit is **permitted**,
  which is the hole `WH-3` exists for. Where: `log-stage-05b` pass 3.

- **A Redshift Serverless workgroup reads back with six `config_parameter` entries nobody set, and
  the Terraform provider plans to remove them forever** (measured 2026-09-20). `config_parameter` is
  a set the provider owns whole: a workgroup created with three parameters returns nine, because the
  service fills `auto_mv`, `datestyle`, `enable_case_sensitive_identifier`, `query_group`,
  `search_path` and `use_fips_ssl`, and every subsequent plan is `1 to change` that never converges.
  The fix is to declare them at their read-back values, which also discloses what a query actually
  runs under — including that **`auto_mv` is on by default**, so the service builds and refreshes
  materialized views on a 1.44 USD/hour meter unasked. Where: `log-stage-05b` pass 3,
  `sandbox/warehouse-compute/main.tf`.

- **`SVV_SCHEMA_QUOTA_STATE` is refused to a superuser on Redshift Serverless** (measured
  2026-09-20). Both it and `STV_SCHEMA_QUOTA_STATE` answer `permission denied for relation` for the
  namespace admin, who reads `usesuper = true` in `pg_user`, and no other catalog view carries a
  schema's quota — `svv_redshift_schemas.schema_option` is empty for a schema that has one. So a
  quota is **authored and proven by breach, never read back**: the check named for it in Stage 5b's
  deliverables can only ever be a note. The breach itself is legible and carries three facts: the
  refusal is **at commit**, the usage **exceeds the quota inside the transaction** before the abort
  (2458 MB against a 2048 MB quota), and 1,024,000 incompressible 1 KB rows read as 2458 MB — a
  quota bounds **disk blocks, not logical bytes**. The floor and ceiling are also undocumented:
  *"Schema quota must be between 2048 and 524288000 MB"*. Where: `log-stage-06h`,
  `runbooks/redshift-connection.md` §S.

- **`CREATE SCHEMA … AUTHORIZATION` takes a database user, not a role** (measured 2026-09-20).
  Redshift has RBAC roles and they cannot own a schema: given a role the statement answers
  `ERROR: user "<name>" does not exist`, which reads as a missing object rather than a wrong kind of
  object. A shared schema therefore has a **non-login user** as owner and its grants on a **role**,
  which is the shape that keeps a schema × project relation many-to-many. Where: `log-stage-06h`
  1.3, `runbooks/redshift-connection.md` §S.

- **`AmazonDataZoneProject` is a single-valued tag key, so a Redshift compute admits one SageMaker
  project** (read 2026-09-20). AWS's instruction is to add *"1 of the following tags"* to the
  workgroup **and its namespace**: either `AmazonDataZoneProject={{projectID}}`, which names one
  project, or `for-use-with-all-datazone-projects=true`, which names every project in the account.
  There is no per-project list, because a tag key holds one value — on both objects. A plan that
  says *"one tag per admitted project"* is therefore not implementable, and a second map entry would
  silently overwrite the first project's tag and break its connection with nothing in the plan
  output to say which project lost access. Where: `log-stage-06h`,
  `terraform-live/sandbox/warehouse/variables.tf`'s `projects` validation.

- **`db_name` on a Redshift Serverless namespace adds a database, it does not replace `dev`**
  (measured 2026-09-20). A namespace created with `db_name = "warehouse"` carries **both**
  `warehouse` and `dev` as local databases, and both are born with `USAGE, CREATE` to the group
  `PUBLIC` on their `public` schema. So the `REVOKE` that closes that hole is owed **per database**,
  and a check that looks for "exactly one class container" has to know about two inert ones. Also in
  the same namespace: `awsdatacatalog` exists but **cannot be connected to at all** —
  *"FATAL: Cannot connect to shared database … use cross-database query notation"* — which is a
  stronger form of the documented read-only direction. Where: `log-stage-05b` 1.6 and 2.4.

- **The Redshift Data API reaches a private workgroup from outside every VPC** (measured
  2026-09-20). `redshift-data execute-statement --workgroup-name … --secret-arn …` runs SQL on a
  workgroup that is `publiclyAccessible: false`, in a private subnet with no default route, from a
  laptop with no VPN — because the Data API is an AWS endpoint and not a database connection. No
  security group sees it and the 5439 door is irrelevant to it. Convenient (it is how this
  repository's instruments read `SVV_*`) and load-bearing: a principal holding
  `redshift-data:ExecuteStatement` has a query path from anywhere, which is why `identity/sso`
  denies the family rather than merely not granting it. It is also **asynchronous with no waiter**,
  so a poll without a delay reports an empty result for a warehouse that is answering. Where:
  `log-stage-06h`, `runbooks/redshift-connection.md` §V.

- **An EC2 security group description refuses an apostrophe, and a RULE description refuses `>`**
  (measured 2026-09-20 and 2026-09-21). One character set governs both:
  `a-zA-Z0-9. _-:/()#,@[]+=&;{}!$*` — it includes `#`, `$`, `!`, `=` and `+`, and excludes `'` and
  `>`, so the ASCII arrow `->` that reads naturally in a rule description is refused while `to`
  passes. The wording differs by object (`Invalid security group description` against `Invalid rule
  description`) and both arrive **at apply**, after every other resource in the plan has been
  created and with `validate`, `fmt` and `tflint` all green. `validate` holds the set only on an
  inline `ingress`/`egress` block and on `aws_security_group_rule` (hashicorp/aws 6.68.0, measured
  2026-10-14); `./scripts/check-sg-descriptions.py` holds every description's literal text to it,
  in `make check` and the commit gate. Where: `log-stage-05b` 1.8, `log-stage-06h` 2.3,
  `log-stage-08` 2.4.

- **The Redshift Data API does not cancel a statement when its client stops polling, and
  `max_query_execution_time` did not stop it either** (measured 2026-09-20, and it cost 9.44 USD). A
  `count(*)` over a triple cross join was submitted through `redshift-data execute-statement`; the
  client gave up polling after 242 s and exited; **the statement ran for 23,601 seconds — 6 h 33 min —
  at base capacity**, and `ComputeSeconds` reported a flat 7,230 RPU-seconds per 30-minute interval
  throughout, which is 4.017 RPU sustained. The workgroup's `max_query_execution_time` was **1800**,
  **Why it did not bite is unresolved, and the obvious
  explanation lost its support within the hour.** The first hypothesis was the superuser queue —
  `pg_user` reports `usesuper = true` for the namespace admin, and Redshift exempts that queue from WLM
  and QMR. But AWS's serverless query-queues page says *"Query monitoring rules (QMR) apply only at the
  Redshift Serverless workgroup level, **affecting all queries run in this workgroup uniformly**"*, and
  its example exempts an admin by giving them a **queue with no rules** — implying that without queues
  (none here; enabling them is permanent) the rule reaches everyone. So the live candidates are the
  exemption *after all*, or that **`max_query_execution_time` as a standalone `config_parameter` is not
  enforced at all** and a per-query ceiling exists only through `wlm_json_configuration` — Lesson 56 in
  its purest form. A third: the statement read only catalog tables, which AWS runs *"exclusively on the
  leader node"*, so it may sit outside what both guards govern. **The test that separates the three** is
  a long query over a user table, as a non-superuser and as the admin. Until then the parameter is
  **possibly inert**. The unit is not in doubt: **seconds**, from the 86,399-second service maximum and
  the QMR examples' own wording; `statement_timeout` is the millisecond parameter and is
  not in the Serverless list. What stopped it:
  `pg_terminate_backend(<session_id>)`, then destroying the workgroup. The `serverless-compute` usage
  limit did not: the statement kept running through the two minutes 5.1 held it breached, while that
  breach refused every query needing the compute. Where:
  `log-stage-05b` the third amendment and the entry of 2026-10-18, and the comments on
  `sandbox/warehouse-compute/main.tf`'s `max_query_execution_time` and `layers.py`'s `usd_per_hour`.

- **A CloudWatch aggregate answers a question about its window, not about now — and the CLI makes the
  aggregate easier to ask for than the current value** (three times in one stage, 2026-09-20). The same
  session read `ComputeSeconds` as **405**, then **4,743**, then **94,767** RPU-seconds for one
  workgroup, and `DataStorage` as **1,596 MB** when the namespace held **130** — the storage figure was
  `max(Datapoints[].Maximum)` over a 24-hour window, six hours after a `DROP` had freed the space, and
  it was written into a plan as an owed `VACUUM`. `--statistics Sum` and `--statistics Maximum` with a
  wide `--start-time` are the shortest commands to type and the easiest to misread; the habit that
  catches all three is **plot the series before quoting a number from it**. Two consequences that cost
  real money and real work here: a cost figure taken while a query is still running is a partial sum,
  and a storage figure taken over a day is a peak. Where: `log-stage-05b`, the three amendments to 5.3
  and the fourth on the storage.

- **`DROP` frees Redshift Managed Storage at once; the `VACUUM` caveat is about `DELETE`** (measured
  2026-09-20). *"A DELETE statement deletes data from a table and disk space is freed up only when
  `VACUUM` runs"* is about **rows** removed from a table that still exists. `DROP SCHEMA … CASCADE` over
  a 1.5 GB table took `DataStorage` from **1,596 MB to 129 MB in the next 30-minute datapoint**, with no
  `VACUUM` anywhere. Reading the caveat as covering both is how a session ends up planning to raise an
  `[E]` compute at 1.44 USD/hour to reclaim zero bytes. Where: `log-stage-05b`, the fourth amendment,
  and `runbooks/redshift-connection.md` §S.

- **`ComputeSeconds` lands per half-hour interval, so a Redshift cost read right after an expensive
  query under-reads it** (measured 2026-09-20). The same metric answered **405**, then **4,743**, then
  **94,767** RPU-seconds for the same workgroup within a few hours — the first two while a query was
  still running, and each was written into four tracked files as *the measured cost*. Cost Explorer
  cannot be used as the cross-check on the same day: it returned 0 for every service with **zero
  groups** for that date, while a negative control three days earlier returned real figures, so its
  zero means *no data yet* and nothing else. Two rules, and neither is about Redshift: **a meter that
  is still accruing has not answered**, and *"I stopped watching"* is not *"it stopped"*. Where:
  `docs/PRICING.md` §5, `log-stage-05b`'s three amendments to 5.3.

### CloudWatch and Service Quotas

- **SageMaker's running apps and jobs are counted in `AWS/Usage`, not in an `AWS/SageMaker` namespace**
  (measured 2026-10-18, Stage 12 step 1.1). `ResourceCount` with `Service=SageMaker` carries one metric
  per app or job type, `studio/JupyterLab-ml.t3.medium` or `processing-job/ml.t3.medium`, with data while
  one runs; Service Quotas names it as the quota's usage metric, and `SERVICE_QUOTA()` divides it by the
  applied value. A reading that looked for a SageMaker namespace recorded "no running-app metric exists"
  (`EXC-10`, 2026-09-12), Lesson 62's wrong path. Where: `log-stage-12-observability-finops.md`, the
  2026-10-18 entry.
- **A read of a log group under a customer key records a refused `Decrypt` by the reader and returns the
  events anyway** (measured 2026-10-26, Stage 9 3.1 and Stage 10 1.3). The infrastructure user, whom
  Production's data key admits through no `logs` path, read a job stream with `get-log-events`: the trail
  holds its `Decrypt` `invokedBy logs.amazonaws.com`, no encryption context, `AccessDenied`, and in the same
  second a `Decrypt` by `fas.s3.amazonaws.com` under CloudWatch Logs' chunk store's `aws:s3:arn`, which
  succeeded, and the events came back. The training operator's six refusals per run have the first shape
  while its task log carries the training job's lines, and `awsds-prod-debug`'s read in a window the same
  afternoon showed the same pair. A refusal of this shape is not a refused read. Where:
  `log-stage-10-orchestration-promotion.md` and `log-stage-09-deployment-targets.md`, 2026-10-26.

### Lake Formation

- **A cross-account full-table-access vend reads the table owner's `AllowFullTableExternalDataAccess`,
  and the refusal names no account** (measured 2026-10-23, Stage 9 2.4). A Glue 6.0 Spark job in
  Production, the engine's own flag `true`, was refused at its first Iceberg write on a shared `curated`
  table with *"Insufficient Lake Formation permissions. Verify the data lake settings for account"*, the
  sentence ending there; the same job committed 99 s after the lake's flag went on. AWS's page names the
  flag as the mode's first step and says nothing about which account's. The vend is logged as
  `GetDataAccess` in two legs, the driver's own call and Glue's on its behalf, and only the second
  reaches the owner's trail, as a shared event; `GetTemporaryGlueTableCredentials` never appears as an
  event name. Where: `log-stage-09-deployment-targets.md`, the 2026-10-23 entries; Stage 9 decision 13.

- **A Lake Formation refusal reaches CloudTrail without the permission it lacked** (measured 2026-10-25,
  Staging's `make down`). The client read *"Insufficient Lake Formation permission(s): Required Drop on
  trades_notional"*, while the trail's two `DeleteTable` events read `AccessDenied`, *"An unknown error
  occurred"*. Which grant is missing comes from the client's output or from `list-permissions`, never from
  the trail. Where: `log-stage-09-deployment-targets.md`, 2026-10-25.

- **`lakeformation list-permissions` filtered by principal returns nothing on a resource another account's
  catalog holds** (measured 2026-10-25 in Sandbox, on Data Governance's `governed_trades`). For the project's
  access role, whose grant serves every read of the governed table, and for the project role alike, the
  principal-filtered listing of the database and of the table came back empty; listed by resource alone, the
  same calls returned both roles' `DESCRIBE` and `SELECT`, the latter as `TableWithColumns`. A read-back after a
  grant or a revoke on a shared resource lists by resource. Where: `log-stage-09-deployment-targets.md`,
  2026-10-25.

### MWAA Serverless

- **A worker encrypts every XCom a task pushes with its own `kms:GenerateDataKey` on the workflow's key,
  after the task's work is done** (measured 2026-10-23, Stage 8 3.8's by-hand leg in Staging). The data
  key admitted the execution role's `Decrypt` with the workflow's ARN as encryption context, the call
  Stage 18 had read, and the first chain failed at its first task: `GlueJobOperator` started the Glue
  job, the job ran to `SUCCEEDED` in 98 s, and the task ended `FAILED` on *"Failed to encrypt XCom
  value"*, the `GenerateDataKey` refused *"because no resource-based policy allows"*; the three tasks
  behind it `UPSTREAM_FAILED`. A key policy read against the service's documented calls misses the
  XCom backend's, and a run on a key the role already held `kms:*` on (Stage 18's project key) could
  not show it. The role's own policy mirrored the key's, `Decrypt` alone, so the second run moved the
  wording from *"no resource-based policy allows"* to *"no identity-based policy allows"*: one intent
  in two documents (Lesson 33), each needing the action. Where: `log-stage-10-orchestration-promotion.md`,
  the 2026-10-23 entries; `staging/data/main.tf`'s `AllowTheWorkflowRolesForTheirWorkflows` and the
  orchestration module's `UseTheKeyForItsWorkflow`.

- **MWAA Serverless calls `iam:CreateServiceLinkedRole` in the saver's session on a workflow created
  through Cloud Control, with its service-linked role already in the account** (read 2026-10-24 in
  Staging's trail of 2026-10-23). At Stage 8 3.8's apply the call came at 22:47:51, invoked by
  `airflow-serverless.amazonaws.com`, answered `InvalidInputException`, and the creation went on; Stage
  18's later CLI creations of 2026-10-19 made no such call. Under a role without the grant the call is
  refused before IAM reads whether the role exists, and how the service takes that refusal is
  unmeasured, so a grant written "until the role exists" is written for both accounts. Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-24; Staging's `deploy-role.tf` and Production's
  `deploy-anchors.tf`, `CreateTheWorkflowServiceLinkedRole`.

- **MWAA Serverless authorizes the tags a `CreateWorkflow` carries as `airflow-serverless:TagResource` on
  `workflow/*`, and no trail shows that check** (measured 2026-10-24, pipeline #68 in Staging). A
  workflow's ARN ends in a suffix the service generates (`awsds-staging-wf-app-etl-hHNGu2YFTv`), so
  `TagResource` granted on the name pattern `workflow/awsds-<env>-wf-*` misses the creation: Cloud
  Control's handler failed with `UnauthorizedTaggingOperation`, *"not authorized to perform:
  airflow-serverless:TagResource on resource: …workflow/*"*. The check runs inside `CreateWorkflow` and
  leaves no CloudTrail event of its own, so a trail replayed through the policy simulator cannot show
  it, and a by-hand apply under a broad permission set passes it unseen. The service's condition keys
  are `aws:RequestTag/*`, `aws:ResourceTag/*` and `aws:TagKeys`; held to `aws:RequestTag/Name`, the
  retried apply created the workflow in 5 s. Where: `log-stage-10-orchestration-promotion.md`,
  2026-10-24; both `foundation/apply-orchestration.tf`, `TagTheWorkflowsAtCreation`.

- **The MWAA Serverless worker renders an XCom into a template as the JSON of its value** (measured
  2026-10-25, `v0.4.1`'s train chain in Staging). `{{ ti.xcom_pull(task_ids='train')['Training'] }}` failed
  with *"'str object' has no attribute 'Training'"*: the training operator's dict reached Jinja as text, and
  `report.json`, written from `{{ ti.xcom_pull(task_ids='summarize') }}`, holds the JSON text of the report's
  string. A template indexes nothing; the callable decodes. Where: `log-stage-10-orchestration-promotion.md`,
  2026-10-24; `examples/app-etl/code/app_etl_tasks.py`, `training_job_name`.

- **A workflow created without `NetworkConfiguration` runs its worker in the service's own network, and a
  borrowed execution role fails it at environment preparation with a log line that names no refusal**
  (measured 2026-10-26, Stage 10 1.2 in Staging). The worker's first calls came from `10.1.11.134` with
  `vpcEndpointId` `airflow-serverless.amazonaws.com` (`exec-env/AWS_ECS_FARGATE`), outside every endpoint of
  the estate, where a configured run's workers call from `10.50.x` through `vpce-…`. Its `kms:Decrypt` was
  refused because the role's statement binds the key to its own workflow's ARN through
  `kms:EncryptionContext:aws:airflow-serverless:workflow-arn`, and the task log said only *"Execution
  environment preparation failed due to an internal server error."*; the trail carried the `AccessDenied`.
  Where: `log-stage-10-orchestration-promotion.md`, 2026-10-26.

### Redshift

- **The Data API authorizes following, reading and cancelling a statement on no resource** (measured
  2026-10-25, `production-warehouse-ddl`). `DescribeStatement`, `GetStatementResult` and `CancelStatement`
  granted on `workgroup/*` matched nothing, *"no identity-based policy allows"*, while `ExecuteStatement`
  on the same ARN passed; the three take `"*"` and the condition key
  `redshift-data:statement-owner-iam-userid`. The CLI on the deploy runner keeps one role session across a
  job, so `aws:userid` matches between the two calls. Where: `log-stage-09-deployment-targets.md`,
  2026-10-25; `production/foundation/deploy-anchors.tf`, `FollowItsOwnStatements`.

- **A Redshift consumer of a Lake Formation-managed datashare calls Glue and Lake Formation as the
  session's IAM principal, needs `TEMP` on the session's database, and reads with the producer's workgroup
  gone** (measured 2026-10-25, Stage 9 9.7). A SageMaker project's portal session assumes its access role,
  whose `RedshiftDbUser` tag names the database user `IAMR:datazone_usr_role_…`: the refusal named the
  access role (`glue:GetTable`), so the catalog read and the Lake Formation grant belong to the access role,
  never to the role the user is named after. A password user is refused, *"Current user is not
  authenticated with IAM credentials"*; the share's table is an external table, and the query needs
  `TEMP` on the database the session is in, *"permission denied to create temporary tables"*; and a
  Serverless producer whose workgroup was destroyed keeps serving the share from its namespace. The
  consumer account's Lake Formation administrator reads under the account's grant with no grant of its own.
  Where: `log-stage-09-deployment-targets.md`, 2026-10-25; `sandbox/warehouse/iam.tf`,
  `ReadTheGovernedShareCatalog`.

### Glue

- **A Glue database with a `FederatedDatabase` refuses a `Description`**: *"Description and federation
  source cannot exist together in a database!"* (measured 2026-10-25, Data Governance's `governed_trades`).
  Where: `log-stage-09-deployment-targets.md`, 2026-10-25.

### EventBridge Scheduler

- **EventBridge Scheduler does not substitute a context attribute whose angle brackets arrive JSON-escaped**
  (measured 2026-10-25, Production's first scheduled execution, Stage 10 6.1). The orchestration module
  writes the target's input with Terraform's `jsonencode`, which escapes `<` and `>`: the schedule stored
  `{"chain":"app-etl","scheduledTime":"\u003caws.scheduler.scheduled-time\u003e"}` and the execution
  received the same text, which a JSON parser reads back as the unsubstituted
  `<aws.scheduler.scheduled-time>`. With the brackets literal in the stored input (`orchestration-v0.2.1`),
  the firing of 2026-10-26 00:42 UTC received `"scheduledTime":"2026-10-26T00:42:00Z"`. Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-25 and 2026-10-26; `terraform-modules/orchestration/chains.tf`,
  the schedule's `input`.

### SageMaker models

- **`CreateModel` from a model package describes the package as the model's execution role, and goes on when
  refused** (measured 2026-10-25, Stage 10 5.4 in Production). At 01:29:33 the deploy role's `CreateModel` on
  `awsds-prod-model-app-etl/1` was followed by a `DescribeModelPackage` as `awsds-prod-job-exec`, session
  `sagemaker-inference`, refused *"is not authorized to perform: sagemaker:DescribeModelPackage"*; the model
  was created and the batch transform completed. A trail reader meets an `AccessDenied` on a run that
  succeeded. Where: `log-stage-10-orchestration-promotion.md`, 2026-10-25.


### SageMaker Unified Studio spaces

- **A space's home `.gitconfig` names the CodeCommit credential helper for every host** (measured 2026-10-26,
  Stage 7 xi). `credential.helper !aws codecommit credential-helper --ignore-host-check $@` with
  `credential.usehttppath true` sits in `/home/sagemaker-user/.gitconfig`: a clone of any HTTPS remote sends
  that helper's credential, GitLab answers *"HTTP Basic: Access denied"*, and git never prompts for a token.
  `-c credential.helper=` resets the list for one command. Where: `log-stage-07-gitlab-runners-ecr.md`,
  2026-10-26.
- **The SageMaker Distribution's own `aws-smus-cicd-cli` comes first on a space's `PATH`** (measured
  2026-10-26, Stage 10 2.1). In a house-image space, `type -a` reads `/opt/conda/bin/aws-smus-cicd-cli`,
  1.0.8, ahead of the house environment's 1.0.9; the 1.0.8 refuses a manifest whose `content.workflows[]`
  carries `code`. Where: `log-stage-10-orchestration-promotion.md`, 2026-10-26.
- **A space's `PATH` is the base environment's activation, not the image's `ENV`** (read 2026-10-26 in the
  SageMaker Distribution 4.5.2's start scripts and libmamba's activation, not measured in a space).
  `entrypoint-sagemaker-ui-jupyter-server`, `start-sagemaker-ui-jupyter-server` and the Code Editor's pair
  each run `micromamba activate base` before their server, and libmamba puts the environment's `bin` first
  on activation and on reactivation removes it from wherever it was and puts it first again; the server's
  terminal (`shell_command: ["/bin/bash"]`) inherits that `PATH`. A directory an image places ahead of
  `/opt/conda/bin` reaches only what runs without the activation: a descendant's Dockerfile `RUN`, which
  `_dockerfile_shell.sh` runs unactivated, and a job's `ContainerEntrypoint`. The base environment's
  `etc/conda/activate.d/*.sh` run after the activation exports `PATH`. Where: `log-stage-08-cicd-pipelines.md`,
  2026-10-26.
- **`list-apps` reports an app's first creation, not its latest start** (measured 2026-10-26). Both `default`
  spaces' apps read `CreationTime` 2026-10-25 05:40 UTC while CloudTrail's `CreateApp` started them at 04:45
  and 05:31 UTC on 2026-10-26: an app's age is read from `CreateApp`. Where: the same log.
- **An open portal page starts its project's space app again after `make down` deleted it** (measured
  2026-10-26). The Studio-apps hook deleted both projects' apps at 06:10 UTC; the persona's open portal tabs
  created them again at 06:13 (`CreateApp`, a browser `userAgent`, each project's role), and `DeleteApp`
  refused the one still starting eight times from 06:21:58 to 06:25:04, *"State transition from
  [PendingCheckout] to [Deleting] is not allowed."*, until it went through at 06:26:12 with every tab closed.
  The Query editor's case is the entry under Lake Formation and SageMaker Unified Studio above. Where:
  `log-stage-07-gitlab-runners-ecr.md`, 2026-10-26.

### DataZone and the CI/CD CLI

- **DataZone refuses `ListDomains` to a project's role that IAM allows** (measured 2026-10-26, Stage 10 2.1).
  The role's managed policy grants `datazone:List*` on `*` and nothing denies it, yet the call reads *"User is
  not permitted to perform operation: ListDomains"*, CloudTrail `AccessDenied` with no `errorMessage`. The
  CI/CD CLI 1.0.9 makes the call on every deploy with bootstrap actions, the manifest's domain id unused, so a
  deploy from a space stops there; reported upstream as [issue 413](https://github.com/aws/CICD-for-SageMakerUnifiedStudio/issues/413). Where:
  `log-stage-10-orchestration-promotion.md`, 2026-10-26.

### MWAA Serverless

- **The API has no `.amazonaws.com` name, and botocore reports a proxy's refusal as a connection failure**
  (measured 2026-10-26, Stage 10 2.1). `airflow-serverless.<region>.api.aws` is the endpoint service's only
  private name and the only public one that resolves; a compute plane that refuses `.api.aws` at its proxy
  leaves an interface endpoint as the one path. The proxy's `403` to `CONNECT` reached the CLI as *"Failed to
  connect to proxy URL"*; the proxy log names the host. Where: the same log.

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
