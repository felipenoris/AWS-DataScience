# Stage 2 step 9 - the checks that keep the conventions honest.
#
# THERE IS NO CI, and that is why this file exists. GitLab arrives at Stage 7 and
# .gitlab-ci.yml at Stage 8, so until then the two enforcement surfaces are `pre-commit`
# (installed per clone) and this `make check`. Both call the SAME scripts in scripts/, so
# Stage 8 steps 5 and 6 move them into a pipeline by adding a .gitlab-ci.yml line rather than
# by rewriting them.
#
# THE SCRIPTS ARE PYTHON, RUN THROUGH uv (2026-08-15). Each one carries the shebang
# `#!/usr/bin/env -S uv run --quiet`, so calling `./scripts/<name>.py` resolves the project
# in pyproject.toml, pins the interpreter to .python-version and installs the shared
# packages - no activation step, no system Python involved. The one prerequisite this
# Makefile has is uv on PATH. `make` itself is a convenience, not a second prerequisite:
# every target is a direct call to scripts that run standalone, and pre-commit invokes the
# same scripts without it - this file exists to name the bundles, not to build anything.
#
# `up`, `down` AND `status` ARRIVED WITH STEP 8 (2026-08-16), and they are D11's teardown and
# rebuild tooling: destroy the [E] slices between sessions, stop the [D] ones, never touch a
# [P] one. All three delegate to ./scripts/slices.py, which owns the layer table and the four
# refusals of 8.3 - this file adds one of those refusals a second time, deliberately:
# `make down` with no ENV must FAIL rather than mean "everything", and that is the one whose
# failure mode is expensive enough to guard twice.
#
# NEITHER `help` NOR THE ENV GUARD SPELLS THE ENV LIST OUT (2026-08-23). Both call
# `./scripts/slices.py envs`, which reads the same table `up` and `down` validate ENV against,
# so the three cannot disagree: an account folder added to layers.py appears in all of them, and
# one removed disappears from all of them. A list typed into this file instead would be a second
# copy of the account map in the one file no check reads (Lesson 33), and it would go stale in
# the direction that looks fine - `make help` offering an ENV that up and down reject.
#
# THE HELP IS SPLIT INTO READ AND WRITE, AND CARRIES THE THREE LAYERS (2026-09-07, asked by the
# user). READ is every target that changes nothing in AWS - `status` runs a local `terraform
# init` and then only reads (EC2 power states, `terraform show`), `clean` deletes local
# artifacts - so a session may run one at any time. WRITE is `up`, `down`, `hub-up` and
# `hub-down`: the four that apply, destroy, start, stop or delete, and the four the apply rule
# in CLAUDE.md fences - never without an explicit authorization. DRY=1 is what turns a WRITE
# target into a READ one. The LAYERS section is this file's own business - what each target
# does to a slice wearing each letter; its one-line names match layers.py's LAYER_NAMES, and
# the reasoning stays in conventions.md 5.1, which the help points at rather than copies.
#
# EVERY SLICE ON DISK WAS [P] WHEN THESE TARGETS WERE WRITTEN, so `make up` and `make down`
# were honest no-ops. They were written before the first [E] slice (Stage 3's egress/) rather
# than after it, which is step 8.6's own argument applied to the whole target. SINCE STAGE 3
# THEY ACT FOR REAL: six [E] slices are destroyed and rebuilt, and Stage 4's [D] WireGuard host
# is stopped and started.
#
# THE CHECK LIST GREW ONE ENTRY AT STEP 3 (2026-08-15): check-bootstrap-parity.py. The five
# bootstrap slices are one slice copied five times, by decision (step 2.3 - a module would need
# a git tag that cannot exist yet), and a copy that stops being one announces nothing. It is in
# `check` rather than in a target of its own because it is offline, fast, and it fails on
# exactly the mistake this stage makes possible.
#
#   make check       step 9's checks that need no AWS session - what a commit must pass
#   make check-ou    step 9.3 - needs a live SSO session as the infrastructure user
#   make check-docs  the plan's own reference check, which predates this stage
#   make check-all   all three
#
# WHY THE SESSION SPLIT IS A TARGET AND NOT A FLAG. A check that quietly skips itself when it
# cannot reach AWS reports the same "clean" on a healthy organization and on an unreachable
# one (Lesson 13). So `check` never runs 9.3 and says so; `check-ou` runs it and exits 2 when
# it has no session, rather than passing.
#
# WHY check-plan-refs.py IS A TARGET OF ITS OWN AND NOT PART OF `check`. It asks a different
# question - are the plan's cross-references still resolvable - and it is RED today, on prose
# that predates this stage: three stage files record dated measurements phrased as "all six
# accounts with a profile", and the check cannot tell a historical measurement from a count
# that goes stale. Folding a known-red check into the commit gate trains people to ignore the
# gate, which costs more than the drift it would catch. Keep it named, keep it runnable, and
# fix it as its own piece of work.
#
# AND IT GREW A SECOND ENTRY ON 2026-08-17: check-identifiers.py. It belongs in the commit gate
# for the same three reasons check-bootstrap-parity.py does - offline, fast, and it fails on
# exactly one mistake - but the mistake is a different KIND: not drift between two files, a
# real AWS account id or a personal e-mail address reaching git, which is undone by a rewrite
# of history rather than by an edit. Unlike check-plan-refs.py it is GREEN on the tree it was
# written against, and it was written the same day the redaction it enforces was made.
#
# A THIRD ENTRY LANDED 2026-08-21, from the Stage 6 plan review: check-provider-locks.py. It
# belongs here for the same three reasons - offline, fast, one mistake - and the mistake had
# ALREADY HAPPENED in three slices: Stage 2 step 6.3 requires three platforms in every
# committed lock file and nothing had ever read one. Under this repository's mandated
# TF_PLUGIN_CACHE_DIR a missing platform fails `init` outright on a Linux runner; without the
# cache it silently rewrites a committed file. It landed in the SAME commit as the fix, because
# the note above about check-plan-refs.py applies in reverse: a gate that is red the day it
# arrives trains people to ignore the gate.

SHELL := /bin/bash
.PHONY: help check check-ou check-docs check-all clean up down hub-up hub-down status slices guard-env

help:
	@printf 'make - the checks, and the D11 lifecycle. READ targets change nothing in AWS;\n'
	@printf 'WRITE targets do: terraform apply/destroy, EC2 start/stop, SageMaker DeleteApp.\n'
	@printf '\n'
	@printf '\033[1mREAD\033[0m - safe at any time; offline unless a session is named\n'
	@printf '  help        this text\n'
	@printf '  check       Stage 2 step 9, offline - what a commit must pass: conventions,\n'
	@printf '              wildcard ARNs, bootstrap parity, slice layers, tfvars shapes, the\n'
	@printf '              policy index, the network doc, account ids and e-mails, provider locks\n'
	@printf '  check-ou    step 9.3, OU coverage - reads the Organization. Needs an SSO session\n'
	@printf '              as the infrastructure user on Identity: exits 2 without one, never passes\n'
	@printf '  check-docs  the plan reference check (known red - see the note in this file)\n'
	@printf '  check-all   the three above\n'
	@printf '  slices      the D11 layer table, offline - which slice is [P], [D] or [E]\n'
	@printf '  status      what is up and the hourly burn (static rates, docs/PRICING.md 3).\n'
	@printf '              Reads the [D] power states from EC2 and each [E] state file after a\n'
	@printf '              local terraform init - a session per account read; a slice it cannot\n'
	@printf '              read is UNREADABLE and the total is then a floor, not a measurement\n'
	@printf '  clean       LOCAL delete only: aws/output, .venv, .ruff_cache, every .terraform/.\n'
	@printf '              Never secrets/, never anything in AWS\n'
	@printf '\n'
	@printf '\033[1mWRITE\033[0m - changes AWS; run one only when it was asked for by name\n'
	@printf '  up   ENV=x  START the [D] hosts of one account folder, then terraform APPLY its\n'
	@printf '              [E] slices in dependency order. Refuses while a hub host is stopped\n'
	@printf '  down ENV=x  DELETE the running Studio apps, terraform DESTROY the [E] slices in\n'
	@printf '              reverse order, then STOP the [D] hosts. Spaces and their volumes stay\n'
	@printf '  hub-up      START the two hub hosts and nothing else - no apply, no endpoint\n'
	@printf '  hub-down    STOP them - nothing is destroyed: the addresses, the host key and\n'
	@printf '              the security groups are [P] anchors and survive the stop\n'
	@printf '\n'
	@printf '  flags of the WRITE targets:\n'
	@printf '    DRY=1       print every command the target would run, and run NONE - the\n'
	@printf '                read-only preview of a write, and how its plan is read\n'
	@printf '    AUTO=1      -auto-approve: apply and destroy stop asking for a yes. The EC2\n'
	@printf '                start/stop and DeleteApp never ask, with or without it\n'
	@printf '    ENV=x       up and down: one account folder from the list at the end. Never\n'
	@printf '                optional - `make down` with no ENV fails, it never means all\n'
	@printf '    GROUPS=a,b  up only - optional endpoint families for THIS apply (see GROUPS)\n'
	@printf '\n'
	@printf '\033[1mLAYERS\033[0m - what [P], [D] and [E] mean, and what each target does to a slice\n'
	@printf 'wearing one (D11; the definitions and the reasoning: docs/plan/conventions.md 5.1)\n'
	@printf '  The rule is PAY NOTHING WHILE IDLE, not destroy everything. Every slice under\n'
	@printf '  terraform-live/ carries one letter in scripts/tfhygiene/layers.py, the one table\n'
	@printf '  up, down and status read. `make slices` prints it; `make check` fails on a slice\n'
	@printf '  with no row, because down would skip in silence what it never heard of.\n'
	@printf '\n'
	@printf '  [P] PERSISTENT  created once, never destroyed: free or nearly free at rest, or\n'
	@printf '                  too slow to rebuild - accounts, SSO, the org policies, the state\n'
	@printf '                  buckets, the VPCs themselves, zones, roles, keys, data buckets,\n'
	@printf '                  ECR, the SMUS domain. No target here touches one: a [P] slice is\n'
	@printf '                  changed by hand, with terraform in its own folder. It also holds\n'
	@printf '                  what a [D] stop must not release - the Elastic IPs, the host key\n'
	@printf '                  secret and the security groups are production/networking anchors\n'
	@printf '  [D] DORMANT     kept, powered off between sessions: STOP and START, never\n'
	@printf '                  destroy. Stateful hosts whose rebuild is riskier than the idle\n'
	@printf '                  cost - the WireGuard host and the Squid proxy today, GitLab at\n'
	@printf '                  Stage 7. up = ec2 start-instances, down = ec2 stop-instances, by\n'
	@printf '                  Name tag; no apply or destroy reaches one from here. status reads\n'
	@printf '                  the POWER STATE from EC2, not the state file. A stopped host still\n'
	@printf '                  bills its EBS volume and its [P] Elastic IP, monthly - the hourly\n'
	@printf '                  total is silent about them by construction\n'
	@printf '  [E] EPHEMERAL   destroyed at the end of a session, rebuilt from code in minutes:\n'
	@printf '                  everything metered by the HOUR - the interface endpoints (egress/,\n'
	@printf '                  workloads-egress/), the probes, the buildbox, and the running\n'
	@printf '                  Studio apps (not terraform: a DeleteApp hook). up = terraform\n'
	@printf '                  apply, down = terraform destroy in reverse order. Every id changes\n'
	@printf '                  on every up, so nothing may name one. A build alone is\n'
	@printf '                  scripts/buildbox.py - one slice, its two prerequisites checked\n'
	@printf '\n'
	@printf '  Two refusals cut across the letters: bootstrap/ is unreachable from either\n'
	@printf '  target (it holds its own state), and production/pki/ is never destroyed\n'
	@printf '  whatever its row says (D36). A layer is a cost judgement and can move (5.1 rule\n'
	@printf '  7): demote a [D] that proves cheap to rebuild, promote an [E] that proves slow.\n'
	@printf '\n'
	@printf '\033[1mTHE HUB\033[0m - one way in, one way out, in the Production account (D38; 6c 7.1/7.2)\n'
	@printf '  The WireGuard host and the Squid proxy are [D] hosts every OTHER account depends\n'
	@printf '  on. `make hub-up` starts the pair without raising Production endpoints or GitLab.\n'
	@printf '  A spoke `make up` REFUSES while either is stopped, naming it: a stopped hub is a\n'
	@printf '  blackhole rather than an error - the apply would succeed and every symptom\n'
	@printf '  afterwards would be a timeout. No session on Production WAIVES the check rather\n'
	@printf '  than failing it, and says so - the two nothings are told apart.\n'
	@printf '\n'
	@printf '\033[1mGROUPS\033[0m - optional interface endpoints, per apply (6c step 5.3)\n'
	@printf '  Both optional blueprint families stay ENABLED in the portal; what this flag\n'
	@printf '  decides is whether their endpoints EXIST. Under design B there is no default\n'
	@printf '  route anywhere, so a blueprint whose endpoints are missing does not fall back\n'
	@printf '  to a slower path - it has no path at all, and fails on first use.\n'
	@printf '\n'
	@printf '  values (closed list - an unknown name is a plan error, never a silent no-op):\n'
	@printf '    bedrock   4 endpoints, ~0.040 USD/h - the six AmazonBedrock* blueprints\n'
	@printf '    emr       7 endpoints, ~0.070 USD/h - EmrServerless\n'
	@printf '    mwaa      RESERVED AND EMPTY - names nothing. D7 settled MWAA Serverless only\n'
	@printf '              (2026-09-05); no Sandbox endpoint for it has been measured as needed,\n'
	@printf '              and 6d step 4 is the first authoring run that could\n'
	@printf '\n'
	@printf '  DEFAULT IS NONE. `make up ENV=sandbox` creates no optional endpoint - a family\n'
	@printf '  nobody uses that day costs nothing. There is no way to leave one on by accident:\n'
	@printf '  the flag lives in the environment, not in a file, so it lasts exactly one apply.\n'
	@printf '\n'
	@printf '    make up ENV=sandbox GROUPS=bedrock\n'
	@printf '    make up ENV=sandbox GROUPS=bedrock,emr\n'
	@printf '\n'
	@printf '  Running `make up` again WITHOUT the flag destroys the optional endpoints - that\n'
	@printf '  is the flag working, not drift. Endpoint ids change on every up either way\n'
	@printf '  (they are [E]), so nothing may name one.\n'
	@printf '  Wired in sandbox/egress only: the blueprints it serves are SMUS blueprints and\n'
	@printf '  the SMUS surface lives in that account alone.\n'
	@printf '\n'
	@./scripts/slices.py envs

# Each script runs even when an earlier one failed - a check suite that stops at the first red
# hides the other two, and the reason to run them together is to see all of it at once.
check:
	@fail=0; \
	for c in "./scripts/check-tf-conventions.py" \
	         "./scripts/check-iam-wildcards.py" \
	         "./scripts/check-bootstrap-parity.py" \
	         "./scripts/slices.py check" \
	         "./scripts/check-tfvars-shape.py" \
	         "./scripts/check-index.py" \
	         "./scripts/check-network-doc.py" \
	         "./scripts/check-identifiers.py" \
	         "./scripts/check-provider-locks.py"; do \
	  printf '\n\033[1m--- %s\033[0m\n' "$$c"; \
	  $$c || fail=1; \
	done; \
	printf '\n--- not run here: ./scripts/check-ou-coverage.py (step 9.3, needs an SSO\n'; \
	printf '    session as the infrastructure user on Identity) -> make check-ou\n'; \
	if [ $$fail -eq 0 ]; then printf '\n\033[1mcheck: OK\033[0m\n'; else printf '\n\033[1mcheck: FAILED\033[0m\n'; fi; \
	exit $$fail

check-ou:
	@./scripts/check-ou-coverage.py

check-docs:
	@./scripts/check-plan-refs.py

# ---------------------------------------------------------------- D11 lifecycle (step 8)
#
# REFUSAL 2 OF 8.3, AND IT IS HERE *AS WELL AS* IN slices.py ON PURPOSE. `make down` with no
# ENV must fail, never default to everything - the one refusal whose failure mode is
# "destroyed the wrong account". argparse enforces it inside the script; this guard catches it
# one layer earlier, with a message about the target the user actually typed. Two independent
# guards for one rule is not duplication when the rule is this one.
guard-env:
	@if [ -z "$(ENV)" ]; then \
	  printf '\033[1mENV is required\033[0m - `make down` never means "everything" (step 8.3 refusal 2).\n'; \
	  printf 'usage: make %s ENV=<account-folder>\n' "$(TARGET)"; \
	  printf '\n'; ./scripts/slices.py envs 2>/dev/null \
	    || printf 'the ENV list is unavailable - `./scripts/slices.py envs` failed\n'; \
	  exit 2; \
	fi

slices:
	@./scripts/slices.py list $(ENV)

# GROUPS -> TF_VAR_optional_service_groups, and the conversion is here rather than in the script
# because it is a Terraform input, not a slice-lifecycle concept: `slices.py` passes the whole
# environment through to every `terraform` it runs (it merges env_extra into os.environ), so the
# variable simply arrives. UNSET IS THE DEFAULT AND IT MEANS EMPTY - Terraform falls back to the
# variable's own `[]`, which is what makes "no groups named" the zero-cost case.
#
# THE ECHO IS NOT DECORATION. A flag that silently changes what an apply builds is the thing this
# repository keeps writing lessons about, so the expansion is printed before the apply runs and
# the operator sees the JSON list Terraform will receive.
up:
	@$(MAKE) --no-print-directory guard-env TARGET=up
	@if [ -n "$(GROUPS)" ]; then \
	  groups="[$$(printf '%s' '$(GROUPS)' | sed 's/[^,][^,]*/"&"/g')]"; \
	  printf '\033[1moptional endpoint groups\033[0m: %s\n' "$$groups"; \
	  TF_VAR_optional_service_groups="$$groups" ./scripts/slices.py up --env $(ENV) $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,); \
	else \
	  ./scripts/slices.py up --env $(ENV) $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,); \
	fi

down:
	@$(MAKE) --no-print-directory guard-env TARGET=down
	@./scripts/slices.py down --env $(ENV) $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,)

# THE HUB, AND WHY IT HAS TARGETS OF ITS OWN (6c step 7.1). D38 gives the estate ONE way in (the
# WireGuard host) and ONE way out (the Squid proxy), both [D] hosts in the Production account. Every
# other account's session depends on them, and `make up ENV=production` would also raise that
# account's [E] endpoint slices and its probes - money for a Sandbox session that needs none of it.
# So the two hosts get a lifecycle that is not any one env's.
#
# NO ENV, NO GUARD, ON PURPOSE: there is exactly one hub, so an ENV argument here would be a
# parameter with one legal value - the shape that invites a second one nobody meant.
hub-up:
	@./scripts/slices.py up --env production --only vpn,proxy $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,)

# `hub-down` STOPS, IT NEVER DESTROYS - [D] is a stop/start contract (D11), so the Elastic IPs, the
# host key and both security groups survive. It is also the last thing to run in a session and the
# easiest to forget while a spoke is still up, which is why `make status` prices the two hosts.
hub-down:
	@./scripts/slices.py down --env production --only vpn,proxy $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,)

status:
	@./scripts/slices.py status $(if $(ENV),--env $(ENV),)

# WHAT clean REMOVES, BY NAME. Only machine-generated artifacts: the snapshots (any aws/
# script regenerates its own), uv's environment (the next script invocation rebuilds it,
# see the note above) and the linter/provider caches. NEVER `git clean -fdX` here: secrets/
# is gitignored too, and a clean that trusts .gitignore deletes it - so this target names
# what it removes, and the find prunes secrets/ explicitly all the same.
clean:
	rm -rf aws/output .venv .ruff_cache
	find . \( -name secrets -o -name .git \) -prune -o \
	  -type d \( -name __pycache__ -o -name .terraform \) -prune -exec rm -rf {} +

check-all:
	@fail=0; \
	$(MAKE) --no-print-directory check     || fail=1; \
	printf '\n\033[1m--- make check-ou\033[0m\n'; \
	$(MAKE) --no-print-directory check-ou  || fail=1; \
	printf '\n\033[1m--- make check-docs\033[0m\n'; \
	$(MAKE) --no-print-directory check-docs || fail=1; \
	exit $$fail
