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

say "== stale section/row references (use a stable ID instead) =="
# Backticked and double-quoted spans are stripped first: those are mentions of the
# old notation (in history, in the glossary), not uses of it.
hits=$(perl -ne 's/`[^`]*`//g; s/"[^"]*"//g; print "$ARGV:$.: $_" if /§4\.4|\brows? \d+/' \
       GENERAL_PLAN.md CLAUDE.md $(find plan -name '*.md') || true)
if [ -n "$hits" ]; then printf '%s\n' "$hits"; bad "replace the hits above with INT-nn"; else say "  none"; fi

say "== size budget (the whole point of the split) =="
for f in CLAUDE.md GENERAL_PLAN.md; do
  b=$(wc -c < "$f" | tr -d ' ')
  say "  $f: $b bytes"
  [ "$b" -lt 20000 ] || bad "$f over 20 KB - move narrative into plan/"
done

[ "$fail" -eq 0 ] && say "OK" || say "FAILED"
exit "$fail"
