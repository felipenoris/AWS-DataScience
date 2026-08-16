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
# WHAT IS NOT HERE YET: `up`, `down` and `status` - the teardown/rebuild tooling of D11.
# That is step 8, and it adds targets to this file rather than a second one.
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

SHELL := /bin/bash
.PHONY: help check check-ou check-docs check-all clean

help:
	@printf 'targets:\n'
	@printf '  check       step 9 offline - conventions, wildcard ARNs, bootstrap parity, the policy index\n'
	@printf '  check-ou    step 9.3 - OU coverage, needs an SSO session (Identity)\n'
	@printf '  check-docs  the plan reference check (known red, see the note in this file)\n'
	@printf '  check-all   all of the above\n'
	@printf '  clean       remove the volatile artifacts (aws/output, .venv, caches) - never secrets/\n'

# Each script runs even when an earlier one failed - a check suite that stops at the first red
# hides the other two, and the reason to run them together is to see all of it at once.
check:
	@fail=0; \
	for c in "./scripts/check-tf-conventions.py" \
	         "./scripts/check-iam-wildcards.py" \
	         "./scripts/check-bootstrap-parity.py" \
	         "./terraform-live/identity/org-policies/check-index.py"; do \
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
