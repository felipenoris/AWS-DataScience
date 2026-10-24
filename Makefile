# The checks (Stage 2 step 9) and the D11 lifecycle targets.
#
# `pre-commit` and `make check` call the same scripts in scripts/, and the CI runs both on every pull
# request (.github/workflows/offline-gates.yml, Stage 8 step 6.2), so the pipeline is a caller, not a
# rewrite.
#
# Every script is Python run through uv: its shebang `#!/usr/bin/env -S uv run --quiet` resolves the
# project in pyproject.toml and the interpreter in .python-version. uv on PATH is the one prerequisite;
# every target is a direct call to a script that also runs standalone.
#
# `up`, `down`, `hub-up`, `hub-down` and `status` are D11's lifecycle tooling: destroy the [E] slices
# between sessions, stop the [D] hosts, never touch a [P] slice. They delegate to ./scripts/slices.py,
# which owns the layer table and the refusals of step 8.3. `help` and the ENV guard read the env list
# from `./scripts/slices.py envs`, the table `up` and `down` validate ENV against.
#
#   make check       step 9's offline checks - what a commit must pass
#   make check-ou    step 9.3 - needs a live SSO session as the infrastructure user on Identity
#   make check-docs  the plan's reference check on its own; `check` runs it too
#   make check-all   check and check-ou
#
# `check` never runs 9.3 and says so; `check-ou` exits 2 without a session rather than passing, so an
# unreachable organization is not reported as a clean one (Lesson 13). check-plan-refs.py joined this
# list on 2026-09-19, once it was green: it was red on prose that predates Stage 2 (dated
# measurements phrased as account counts) and on the untracked copies of this repository under
# `.terraform/` and `.claude/`, which it no longer reads. `check-docs` stays as a name so the prose
# check can be run alone. It reads the whole repository's prose rather than the tree a commit
# touches, so it is the one entry here whose cost does not scale with the size of the commit.
#
# The `check` list, each offline and failing on one mistake: check-tf-conventions (9.1),
# check-iam-wildcards (9.2), check-bootstrap-parity (3.5: the five bootstrap slices are one slice
# copied), check-copies (Stage 8 3.0 and 4.1: files copied across slices), render-workflow.py --check
# (Stage 10 decision 6: the render's table knows every value of the template's workflows), slices.py
# check (8.1), check-tfvars-shape, check-index (9.4), check-network-doc, check-plan-refs (the plan's
# relative links, stable IDs and the two size budgets),
# check-identifiers (no account id or e-mail in a tracked file), check-provider-locks (6.3: three
# platforms in every committed lock file), check-gitlab-ci (no job named after a GitLab CI global
# keyword, no `needs:` naming a job its pipeline lacks, no script item `bash -n` refuses) and
# check-sg-descriptions (no security group or rule description EC2 refuses at apply).

SHELL := /bin/bash

# make takes an unknown variable in silence, and every flag here is upper case: `auto=1` applies with
# no -auto-approve and `runners=0` raises the runner anyway (both seen 2026-10-12). The lower-case
# spellings of the flags are refused before any target runs.
ifneq ($(strip $(auto)$(build)$(dry)$(env)$(groups)$(only)$(profile)$(runners)),)
$(error the flags are upper case - AUTO, BUILD, DRY, ENV, GROUPS, ONLY, PROFILE, RUNNERS; a lower-case one would be ignored)
endif
.PHONY: help check check-ou check-docs check-all clean up down hub-up hub-down gitlab-up gitlab-down status slices guard-env

help:
	@printf 'make - the checks, and the D11 lifecycle. READ targets change nothing in AWS;\n'
	@printf 'WRITE targets do: terraform apply/destroy, EC2 start/stop, SageMaker DeleteApp.\n'
	@printf '\n'
	@printf '\033[1mREAD\033[0m - safe at any time; offline unless a session is named\n'
	@printf '  help        this text\n'
	@printf '  check       Stage 2 step 9, offline - what a commit must pass: conventions,\n'
	@printf '              wildcard ARNs, bootstrap parity, copied files, the workflow render,\n'
	@printf '              slice layers, tfvars shapes, the policy index, the network doc,\n'
	@printf '              the plan references, account ids and e-mails, provider locks, the\n'
	@printf '              GitLab CI files, security group descriptions\n'
	@printf '  check-ou    step 9.3, OU coverage - reads the Organization. Needs an SSO session\n'
	@printf '              as the infrastructure user on Identity: exits 2 without one, never passes\n'
	@printf '  check-docs  the plan reference check on its own; check runs it too\n'
	@printf '  check-all   check and check-ou\n'
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
	@printf '              [E] slices in dependency order. Refuses while a hub host is stopped.\n'
	@printf '              ENV=production leaves the hub pair to hub-up (Stage 7 step 1.6)\n'
	@printf '  down ENV=x  DELETE the running Studio apps, terraform DESTROY the [E] slices in\n'
	@printf '              reverse order, then STOP the [D] hosts. Spaces and their volumes stay\n'
	@printf '  hub-up      START the two hub hosts and nothing else - no apply, no endpoint\n'
	@printf '  hub-down    STOP them - nothing is destroyed: the addresses, the host key and\n'
	@printf '              the security groups are [P] anchors and survive the stop\n'
	@printf '  gitlab-up   START GitLab and APPLY production/egress and production/runners - a\n'
	@printf '              GitLab session, leaving the hub to hub-up (Stage 7 step 1.6): the\n'
	@printf '              deploy and test runners always, the build runner with BUILD=1\n'
	@printf '  gitlab-down DESTROY the runners and the SharedServices endpoints, STOP GitLab; the\n'
	@printf '              hub keeps running for every other session\n'
	@printf '\n'
	@printf '  flags of the WRITE targets:\n'
	@printf '    DRY=1       print every command the target would run, and run none\n'
	@printf '    AUTO=1      -auto-approve: apply and destroy stop asking for a yes. The EC2\n'
	@printf '                start/stop and DeleteApp never ask, with or without it\n'
	@printf '    ENV=x       up and down: one account folder from the list at the end. Never\n'
	@printf '                optional - `make down` with no ENV fails, it never means all\n'
	@printf '    GROUPS=a,b  up only - optional endpoint families for THIS apply (see GROUPS)\n'
	@printf '    ONLY=a,b    up and down - these slices of ENV and no other (Stage 8 step 4.4)\n'
	@printf '    PROFILE=p   up and down - every command runs as profile p instead of the\n'
	@printf '                account default: the deploy runner names its deploy role. A deploy\n'
	@printf '                role applies no sandbox slice (refusal 8, Stage 8 step 2.4)\n'
	@printf '    RUNNERS=0   gitlab-up only - GitLab and the endpoints, production/runners left\n'
	@printf '                unapplied: neither the deploy nor the test runner rises (0.0376\n'
	@printf '                USD/h), one raised earlier keeps running, gitlab-down destroys it\n'
	@printf '    BUILD=1     gitlab-up only - the build runner too (m8i.xlarge, 0.2117 USD/h),\n'
	@printf '                the one runner that takes untagged jobs on a protected ref: image\n'
	@printf '                builds and app-etl tag pipelines. Like GROUPS it lasts one apply: a\n'
	@printf '                gitlab-up without it destroys a build runner raised earlier, and so\n'
	@printf '                does `make up ENV=production`, which applies production/runners too\n'
	@printf '\n'
	@printf '\033[1mLAYERS\033[0m - what [P], [D] and [E] mean, and what each target does to a slice\n'
	@printf 'wearing one (D11; the definitions and the reasoning: docs/plan/conventions.md 5.1)\n'
	@printf '  The rule is pay nothing while idle, not destroy everything. Every slice under\n'
	@printf '  terraform-live/ carries one letter in scripts/tfhygiene/layers.py, the one table\n'
	@printf '  up, down and status read. `make slices` prints it; `make check` fails on a slice\n'
	@printf '  with no row, because down would skip in silence what it never heard of.\n'
	@printf '\n'
	@printf '  [P] PERSISTENT  created once, never destroyed: free or nearly free at rest, or\n'
	@printf '                  too slow to rebuild - accounts, SSO, the org policies, the state\n'
	@printf '                  buckets, the VPCs, zones, roles, keys, data buckets, ECR, the SMUS\n'
	@printf '                  domain. No target here touches one: a [P] slice is changed by hand,\n'
	@printf '                  with terraform in its own folder. It also holds what a [D] stop must\n'
	@printf '                  not release: the Elastic IPs, the host key secret and the security\n'
	@printf '                  groups are production/networking anchors\n'
	@printf '  [D] DORMANT     kept, powered off between sessions: STOP and START, never destroy.\n'
	@printf '                  Stateful hosts whose rebuild is riskier than the idle cost - the\n'
	@printf '                  WireGuard host and the Squid proxy, and GitLab since Stage 7.\n'
	@printf '                  up = ec2 start-instances, down = ec2 stop-instances, by Name tag.\n'
	@printf '                  status reads the power state from EC2, not the state file. A\n'
	@printf '                  stopped host still bills its EBS volume and its [P] Elastic IP,\n'
	@printf '                  monthly; the hourly total is silent about them\n'
	@printf '  [E] EPHEMERAL   destroyed at the end of a session, rebuilt from code in minutes:\n'
	@printf '                  everything metered by the hour - the interface endpoints (egress/,\n'
	@printf '                  workloads-egress/), the probes, the build runner, and the running\n'
	@printf '                  Studio apps (not terraform: a DeleteApp hook). up = terraform apply,\n'
	@printf '                  down = terraform destroy in reverse order. Every id changes on every\n'
	@printf '                  up, so nothing may name one\n'
	@printf '\n'
	@printf '  Two refusals cut across the letters: bootstrap/ is unreachable from either\n'
	@printf '  target (it holds its own state), and production/pki/ is never destroyed\n'
	@printf '  whatever its row says (D36). A layer is a cost judgement and can move (5.1 rule\n'
	@printf '  7): demote a [D] that proves cheap to rebuild, promote an [E] that proves slow.\n'
	@printf '\n'
	@printf '\033[1mTHE HUB\033[0m - the way into the private network and the way out, in Production (D38; 6c 7.1/7.2)\n'
	@printf '  The WireGuard host and the Squid proxy are [D] hosts every other account depends\n'
	@printf '  on. `make hub-up` starts the pair without raising Production endpoints or GitLab,\n'
	@printf '  and `make up`/`make down ENV=production` never touch the pair (Stage 7 step 1.6):\n'
	@printf '  a Production session that stopped the proxy would blackhole every peer. Every\n'
	@printf '  `make up` refuses while the proxy is stopped, naming it: with a stopped hub the\n'
	@printf '  apply would succeed and every symptom afterwards would be a timeout. With no\n'
	@printf '  session on Production the check is waived, and says so.\n'
	@printf '\n'
	@printf '\033[1mGROUPS\033[0m - optional interface endpoints, per apply (6c step 5.3)\n'
	@printf '  Both optional blueprint families stay enabled in the portal; the flag decides\n'
	@printf '  whether their endpoints exist. There is no default route anywhere (design B), so a\n'
	@printf '  blueprint whose endpoints are missing has no path at all and fails on first use.\n'
	@printf '\n'
	@printf '  values (closed list - an unknown name is a plan error, never a silent no-op):\n'
	@printf '    bedrock-base   2 endpoints, ~0.020 USD/h - `bedrock` and `bedrock-runtime`, the\n'
	@printf '                   control plane and the invocation path. Stage 6e s assistant in a\n'
	@printf '                   space needs both, so a session that runs it names this group\n'
	@printf '    bedrock-agent  2 endpoints, ~0.020 USD/h - the agent pair, for the\n'
	@printf '                   AmazonBedrock* blueprints; it needs bedrock-base beside it\n'
	@printf '    emr            7 endpoints, ~0.070 USD/h - EmrServerless\n'
	@printf '    mlflow         1 endpoint, ~0.010 USD/h - the MLflow App s tracking API, for\n'
	@printf '                   MLflowApp (Stage 17); a space logging a run names it\n'
	@printf '    redshift       1 endpoint, ~0.010 USD/h - redshift-serverless, the warehouse API\n'
	@printf '                   door (5b 1.10); a session that queries the warehouse names it\n'
	@printf '    mwaa           reserved and empty - names nothing. D7 settled MWAA Serverless only;\n'
	@printf '                   no Sandbox endpoint for it has been measured as needed\n'
	@printf '\n'
	@printf '  The default is none: `make up ENV=sandbox` creates no optional endpoint. The flag\n'
	@printf '  lives in the environment, not in a file, so it lasts exactly one apply, and a\n'
	@printf '  `make up` without it destroys the optional endpoints.\n'
	@printf '\n'
	@printf '    make up ENV=sandbox GROUPS=bedrock-base\n'
	@printf '    make up ENV=sandbox GROUPS=bedrock-base,bedrock-agent,emr\n'
	@printf '\n'
	@printf '  Wired in sandbox/egress, for the SMUS blueprints, and in production/workloads-egress,\n'
	@printf '  where a job inside VPC-Workloads calls the warehouse API (redshift, Stage 9 9.1).\n'
	@printf '  There it rides on ONLY=, or the apply takes every Production [E] slice:\n'
	@printf '\n'
	@printf '    make up ENV=production ONLY=workloads-egress GROUPS=redshift\n'
	@printf '\n'
	@./scripts/slices.py envs

# Each script runs even when an earlier one failed, so one run shows every red.
check:
	@fail=0; \
	for c in "./scripts/check-tf-conventions.py" \
	         "./scripts/check-iam-wildcards.py" \
	         "./scripts/check-bootstrap-parity.py" \
	         "./scripts/check-copies.py" \
	         "./scripts/render-workflow.py --check" \
	         "./scripts/slices.py check" \
	         "./scripts/check-tfvars-shape.py" \
	         "./scripts/check-index.py" \
	         "./scripts/check-network-doc.py" \
	         "./scripts/check-plan-refs.py" \
	         "./scripts/check-identifiers.py" \
	         "./scripts/check-provider-locks.py" \
	         "./scripts/check-gitlab-ci.py" \
	         "./scripts/check-sg-descriptions.py" \
	         "./scripts/check-gitlab-pins.py"; do \
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
# Refusal 2 of 8.3: `make down` with no ENV fails, it never means everything. argparse enforces it
# inside slices.py; this guard catches it one layer earlier, naming the target the user typed.
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

# GROUPS becomes TF_VAR_optional_service_groups here, not in the script, because it is a Terraform
# input rather than a slice-lifecycle concept: slices.py passes the whole environment through to
# every `terraform` it runs. Unset means empty (the variable's own `[]`), the zero-cost case. The
# expansion is printed before the apply so the operator sees the JSON list Terraform receives.
#
# ONLY and PROFILE are Stage 8 step 4.4's, for the deploy runner (step 3.1): ONLY narrows ENV to the
# slices named, PROFILE replaces the account's default profile, and both pass through to slices.py.
up:
	@$(MAKE) --no-print-directory guard-env TARGET=up
	@if [ -n "$(GROUPS)" ]; then \
	  groups="[$$(printf '%s' '$(GROUPS)' | sed 's/[^,][^,]*/"&"/g')]"; \
	  printf '\033[1moptional endpoint groups\033[0m: %s\n' "$$groups"; \
	  TF_VAR_optional_service_groups="$$groups" ./scripts/slices.py up --env $(ENV) $(if $(ONLY),--only $(ONLY),) $(if $(PROFILE),--profile $(PROFILE),) $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,); \
	else \
	  ./scripts/slices.py up --env $(ENV) $(if $(ONLY),--only $(ONLY),) $(if $(PROFILE),--profile $(PROFILE),) $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,); \
	fi

down:
	@$(MAKE) --no-print-directory guard-env TARGET=down
	@./scripts/slices.py down --env $(ENV) $(if $(ONLY),--only $(ONLY),) $(if $(PROFILE),--profile $(PROFILE),) $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,)

# The hub (6c step 7.1): D38 gives the estate one way into the private network (the WireGuard host)
# and one way out (the Squid proxy), both [D] hosts in Production. Every other account's session
# depends on them, and `make up ENV=production` would also raise that account's [E] endpoint slices
# and probes, so the two hosts get a lifecycle of their own. No ENV argument: there is exactly one hub.
hub-up:
	@./scripts/slices.py up --env production --only vpn,proxy $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,)

# `hub-down` stops, never destroys: [D] is a stop/start contract (D11), so the Elastic IPs, the host
# key and both security groups survive. It is the last thing to run in a session and the easiest to
# forget, which is why `make status` prices the two hosts.
hub-down:
	@./scripts/slices.py down --env production --only vpn,proxy $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,)

# GitLab's session (Stage 7 step 1.6): the [D] host started, VPC-SharedServices' endpoints and the
# runners applied, and the hub left to `hub-up`. `make up ENV=production` would do the same
# and also raise `workloads-egress/` and `probes/`, which a GitLab session never needs.
#
# RUNNERS=0 leaves the runners out: a session that runs no pipeline, or one before a runner's
# token is in its container (runbook K). Any other value but 1 is refused, so a typo never raises
# hosts unasked. `$(comma)` keeps the separator out of `$(if)`'s own arguments.
#
# BUILD=1 adds the build runner (Stage 7 decision 5) by becoming TF_VAR_build_runner, the way GROUPS
# becomes TF_VAR_optional_service_groups in `up`. Unset or 0 is false, the variable's default, so a
# session with no image build and no protected pipeline bills 0.0376 USD/h of runners, not 0.2493.
# It lasts one apply: a `make gitlab-up` without it destroys a build runner an earlier one raised.
# With RUNNERS=0 it is refused, since it acts on the slice RUNNERS=0 leaves out.
comma := ,

gitlab-up:
	@case "$(RUNNERS)" in ""|0|1) ;; *) printf 'RUNNERS must be 0 or 1 (unset means 1), not "%s"\n' "$(RUNNERS)"; exit 2;; esac
	@case "$(BUILD)" in ""|0|1) ;; *) printf 'BUILD must be 0 or 1 (unset means 0), not "%s"\n' "$(BUILD)"; exit 2;; esac
	@if [ "$(RUNNERS)" = 0 ] && [ "$(BUILD)" = 1 ]; then printf 'BUILD=1 acts on production/runners/, which RUNNERS=0 leaves out\n'; exit 2; fi
	@$(if $(filter 0,$(RUNNERS)),true,printf '\033[1mbuild runner\033[0m: %s\n' '$(if $(filter 1,$(BUILD)),yes - BUILD=1,no - BUILD=1 raises it)')
	@TF_VAR_build_runner=$(if $(filter 1,$(BUILD)),true,false) ./scripts/slices.py up --env production --only tooling,egress$(if $(filter 0,$(RUNNERS)),,$(comma)runners) $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,)

# The reverse order is the script's: the runners and the endpoints are destroyed, then GitLab is
# stopped. Nothing here touches the hub, so every other session's proxy and tunnel stay up.
# RUNNERS and BUILD are ignored: destroying an absent runner is a no-op, and a forgotten one is this
# stage's likeliest leak.
gitlab-down:
	@./scripts/slices.py down --env production --only tooling,egress,runners $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,)

status:
	@./scripts/slices.py status $(if $(ENV),--env $(ENV),)

# Only machine-generated artifacts, named: the snapshots (any aws/ script regenerates its own), uv's
# environment (the next script run rebuilds it) and the linter/provider caches. Never `git clean
# -fdX` here: secrets/ is gitignored too and would go with it; the find prunes it explicitly.
clean:
	rm -rf aws/output .venv .ruff_cache
	find . \( -name secrets -o -name .git \) -prune -o \
	  -type d \( -name __pycache__ -o -name .terraform \) -prune -exec rm -rf {} +

check-all:
	@fail=0; \
	$(MAKE) --no-print-directory check     || fail=1; \
	printf '\n\033[1m--- make check-ou\033[0m\n'; \
	$(MAKE) --no-print-directory check-ou  || fail=1; \
	exit $$fail
