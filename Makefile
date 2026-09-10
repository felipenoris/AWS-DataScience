# The checks (Stage 2 step 9) and the D11 lifecycle targets.
#
# There is no CI until Stage 7 (GitLab) and Stage 8 (.gitlab-ci.yml). `pre-commit` and `make check`
# call the same scripts in scripts/, so the pipeline will add a caller, not a rewrite.
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
#   make check-docs  the plan's reference check, known red (see below)
#   make check-all   all three
#
# `check` never runs 9.3 and says so; `check-ou` exits 2 without a session rather than passing, so an
# unreachable organization is not reported as a clean one (Lesson 13). check-plan-refs.py is a target
# of its own because it is red on prose that predates Stage 2 (dated measurements phrased as account
# counts), and a known-red check inside the commit gate trains people to ignore the gate.
#
# The `check` list, each offline and failing on one mistake: check-tf-conventions (9.1),
# check-iam-wildcards (9.2), check-bootstrap-parity (3.5: the five bootstrap slices are one slice
# copied), slices.py check (8.1), check-tfvars-shape, check-index (9.4), check-network-doc,
# check-identifiers (no account id or e-mail in a tracked file) and check-provider-locks (6.3: three
# platforms in every committed lock file).

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
	@printf '    DRY=1       print every command the target would run, and run none\n'
	@printf '    AUTO=1      -auto-approve: apply and destroy stop asking for a yes. The EC2\n'
	@printf '                start/stop and DeleteApp never ask, with or without it\n'
	@printf '    ENV=x       up and down: one account folder from the list at the end. Never\n'
	@printf '                optional - `make down` with no ENV fails, it never means all\n'
	@printf '    GROUPS=a,b  up only - optional endpoint families for THIS apply (see GROUPS)\n'
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
	@printf '                  WireGuard host and the Squid proxy today, GitLab at Stage 7.\n'
	@printf '                  up = ec2 start-instances, down = ec2 stop-instances, by Name tag.\n'
	@printf '                  status reads the power state from EC2, not the state file. A\n'
	@printf '                  stopped host still bills its EBS volume and its [P] Elastic IP,\n'
	@printf '                  monthly; the hourly total is silent about them\n'
	@printf '  [E] EPHEMERAL   destroyed at the end of a session, rebuilt from code in minutes:\n'
	@printf '                  everything metered by the hour - the interface endpoints (egress/,\n'
	@printf '                  workloads-egress/), the probes, the buildbox, and the running Studio\n'
	@printf '                  apps (not terraform: a DeleteApp hook). up = terraform apply, down =\n'
	@printf '                  terraform destroy in reverse order. Every id changes on every up, so\n'
	@printf '                  nothing may name one. A build alone is scripts/buildbox.py\n'
	@printf '\n'
	@printf '  Two refusals cut across the letters: bootstrap/ is unreachable from either\n'
	@printf '  target (it holds its own state), and production/pki/ is never destroyed\n'
	@printf '  whatever its row says (D36). A layer is a cost judgement and can move (5.1 rule\n'
	@printf '  7): demote a [D] that proves cheap to rebuild, promote an [E] that proves slow.\n'
	@printf '\n'
	@printf '\033[1mTHE HUB\033[0m - one way in, one way out, in the Production account (D38; 6c 7.1/7.2)\n'
	@printf '  The WireGuard host and the Squid proxy are [D] hosts every other account depends\n'
	@printf '  on. `make hub-up` starts the pair without raising Production endpoints or GitLab.\n'
	@printf '  A spoke `make up` refuses while either is stopped, naming it: with a stopped hub\n'
	@printf '  the apply would succeed and every symptom afterwards would be a timeout. With no\n'
	@printf '  session on Production the check is waived, and says so.\n'
	@printf '\n'
	@printf '\033[1mGROUPS\033[0m - optional interface endpoints, per apply (6c step 5.3)\n'
	@printf '  Both optional blueprint families stay enabled in the portal; the flag decides\n'
	@printf '  whether their endpoints exist. There is no default route anywhere (design B), so a\n'
	@printf '  blueprint whose endpoints are missing has no path at all and fails on first use.\n'
	@printf '\n'
	@printf '  values (closed list - an unknown name is a plan error, never a silent no-op):\n'
	@printf '    bedrock   4 endpoints, ~0.040 USD/h - the six AmazonBedrock* blueprints\n'
	@printf '    emr       7 endpoints, ~0.070 USD/h - EmrServerless\n'
	@printf '    mwaa      reserved and empty - names nothing. D7 settled MWAA Serverless only;\n'
	@printf '              no Sandbox endpoint for it has been measured as needed\n'
	@printf '\n'
	@printf '  The default is none: `make up ENV=sandbox` creates no optional endpoint. The flag\n'
	@printf '  lives in the environment, not in a file, so it lasts exactly one apply, and a\n'
	@printf '  `make up` without it destroys the optional endpoints.\n'
	@printf '\n'
	@printf '    make up ENV=sandbox GROUPS=bedrock\n'
	@printf '    make up ENV=sandbox GROUPS=bedrock,emr\n'
	@printf '\n'
	@printf '  Wired in sandbox/egress only: the blueprints it serves are SMUS blueprints and\n'
	@printf '  the SMUS surface lives in that account alone.\n'
	@printf '\n'
	@./scripts/slices.py envs

# Each script runs even when an earlier one failed, so one run shows every red.
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

# The hub (6c step 7.1): D38 gives the estate one way in (the WireGuard host) and one way out (the
# Squid proxy), both [D] hosts in Production. Every other account's session depends on them, and
# `make up ENV=production` would also raise that account's [E] endpoint slices and probes, so the two
# hosts get a lifecycle of their own. No ENV argument: there is exactly one hub.
hub-up:
	@./scripts/slices.py up --env production --only vpn,proxy $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,)

# `hub-down` stops, never destroys: [D] is a stop/start contract (D11), so the Elastic IPs, the host
# key and both security groups survive. It is the last thing to run in a session and the easiest to
# forget, which is why `make status` prices the two hosts.
hub-down:
	@./scripts/slices.py down --env production --only vpn,proxy $(if $(AUTO),--auto-approve,) $(if $(DRY),--dry-run,)

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
	printf '\n\033[1m--- make check-docs\033[0m\n'; \
	$(MAKE) --no-print-directory check-docs || fail=1; \
	exit $$fail
