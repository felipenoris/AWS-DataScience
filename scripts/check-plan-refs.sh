#!/usr/bin/env bash
# Verify the plan's stable identifiers and relative links still resolve.
# Run from anywhere:  ./scripts/check-plan-refs.sh
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0
say() { printf '%s\n' "$*"; }
bad() { fail=1; printf '  FAIL  %s\n' "$*"; }

say "== broken relative links =="
n=0
while IFS='|' read -r src tgt; do
  [ -z "${src:-}" ] && continue
  if [ ! -e "$(dirname "$src")/$tgt" ]; then bad "$src -> $tgt"; else n=$((n+1)); fi
done < <(grep -roE '\]\([^)#[:space:]]+\.md' --include='*.md' . \
         | grep -v '/\.git/' | sed 's/:\](/|/')
say "  $n links resolve"

say "== D-references with no decision file =="
for d in $(grep -rhoE '\bD[0-9]{1,2}\b' --include='*.md' . | sort -u); do
  num=$((10#${d#D}))
  [ "$num" -ge 1 ] && [ "$num" -le 99 ] || continue
  compgen -G "plan/decisions/D$(printf '%02d' "$num")-*.md" >/dev/null \
    || bad "$d referenced, but no plan/decisions/D$(printf '%02d' "$num")-*.md"
done

say "== INT-references with no row in plan/integrations.md =="
for i in $(grep -rhoE '\bINT-[0-9]{2}\b' --include='*.md' . | sort -u); do
  grep -q "\*\*$i\*\*" plan/integrations.md || bad "$i referenced, no row in plan/integrations.md"
done

# Every prose file the plan owns. The root docs were outside this net until 2026-08-08,
# which is exactly where the stale references had survived.
PROSE=(GENERAL_PLAN.md CLAUDE.md README.md ACCOUNTS_AND_USERS.md GLOSSARY.md PRICING.md)
while IFS= read -r f; do PROSE+=("$f"); done < <(find plan -name '*.md' | sort)

say "== stale section/row references (use a stable ID instead) =="
# Backticked and double-quoted spans are stripped first: those are mentions of the
# old notation (in history, in the glossary), not uses of it.
hits=$(perl -ne 's/`[^`]*`//g; s/"[^"]*"//g; print "$ARGV:$.: $_" if /§4\.4|\brows? \d+/' \
       "${PROSE[@]}" || true)
if [ -n "$hits" ]; then printf '%s\n' "$hits"; bad "replace the hits above with INT-nn"; else say "  none"; fi

say "== pointers into GENERAL_PLAN.md for content that moved into plan/ =="
# GENERAL_PLAN.md is the core: principles, the account map, the two indexes. A decision,
# a stage body or a numbered section is NOT in it, so a reference of that shape is stale.
hits=$(grep -nE '`?GENERAL_PLAN\.md`?[[:space:]]+(§|D[0-9]|Stage |row |item )' "${PROSE[@]}" || true)
if [ -n "$hits" ]; then printf '%s\n' "$hits"; bad "point at plan/decisions/, plan/stages/ or the plan/ file that holds it"; else say "  none"; fi

say "== hard-coded account counts (they go stale when an account is added) =="
# A *quota* is a measured external fact and keeps its number; a count of *our* accounts is
# derived from the account map and goes stale the day the map changes. Only the second is flagged.
hits=$(grep -niE '\b(ten|nine|eight|seven|six|five|four|three)[[:space:]]+(accounts|governed accounts|member accounts|state buckets)\b|\b(1[0-9]|[3-9])[[:space:]]+(accounts|governed accounts)\b' "${PROSE[@]}" \
       | grep -viE 'quota|limit|Service Quotas' || true)
if [ -n "$hits" ]; then printf '%s\n' "$hits"; bad "write 'the accounts' / 'every governed account' instead"; else say "  none"; fi

say "== size budget (the whole point of the split) =="
for f in CLAUDE.md GENERAL_PLAN.md; do
  b=$(wc -c < "$f" | tr -d ' ')
  say "  $f: $b bytes"
  [ "$b" -lt 20000 ] || bad "$f over 20 KB - move narrative into plan/"
done

[ "$fail" -eq 0 ] && say "OK" || say "FAILED"
exit "$fail"
