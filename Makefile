# Stage 2 step 9 - the checks that keep the conventions honest.
#
# THERE IS NO CI, and that is why this file exists. GitLab arrives at Stage 7 and
# .gitlab-ci.yml at Stage 8, so until then the two enforcement surfaces are `pre-commit`
# (installed per clone) and this `make check`. Both call the SAME scripts in scripts/, so
# Stage 8 steps 5 and 6 move them into a pipeline by adding a .gitlab-ci.yml line rather than
# by rewriting them.
#
# WHAT IS NOT HERE YET: `up`, `down` and `status` - the teardown/rebuild tooling of D11.
# That is step 8, and it adds targets to this file rather than a second one.
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
# WHY check-plan-refs.sh IS A TARGET OF ITS OWN AND NOT PART OF `check`. It asks a different
# question - are the plan's cross-references still resolvable - and it is RED today, on prose
# that predates this stage: three stage files record dated measurements phrased as "all six
# accounts with a profile", and the check cannot tell a historical measurement from a count
# that goes stale. Folding a known-red check into the commit gate trains people to ignore the
# gate, which costs more than the drift it would catch. Keep it named, keep it runnable, and
# fix it as its own piece of work.

SHELL := /bin/bash
.PHONY: help check check-ou check-docs check-all

help:
	@printf 'targets:\n'
	@printf '  check       step 9 offline - conventions, wildcard ARNs, the policy index\n'
	@printf '  check-ou    step 9.3 - OU coverage, needs an SSO session (Identity)\n'
	@printf '  check-docs  the plan reference check (known red, see the note in this file)\n'
	@printf '  check-all   all of the above\n'

# Each script runs even when an earlier one failed - a check suite that stops at the first red
# hides the other two, and the reason to run them together is to see all of it at once.
check:
	@fail=0; \
	for c in "./scripts/check-tf-conventions.sh" \
	         "./scripts/check-iam-wildcards.sh" \
	         "./terraform-live/identity/org-policies/check-index.sh"; do \
	  printf '\n\033[1m--- %s\033[0m\n' "$$c"; \
	  $$c || fail=1; \
	done; \
	printf '\n--- not run here: ./scripts/check-ou-coverage.sh (step 9.3, needs an SSO\n'; \
	printf '    session as the infrastructure user on Identity) -> make check-ou\n'; \
	if [ $$fail -eq 0 ]; then printf '\n\033[1mcheck: OK\033[0m\n'; else printf '\n\033[1mcheck: FAILED\033[0m\n'; fi; \
	exit $$fail

check-ou:
	@./scripts/check-ou-coverage.sh

check-docs:
	@./scripts/check-plan-refs.sh

check-all:
	@fail=0; \
	$(MAKE) --no-print-directory check     || fail=1; \
	printf '\n\033[1m--- make check-ou\033[0m\n'; \
	$(MAKE) --no-print-directory check-ou  || fail=1; \
	printf '\n\033[1m--- make check-docs\033[0m\n'; \
	$(MAKE) --no-print-directory check-docs || fail=1; \
	exit $$fail
