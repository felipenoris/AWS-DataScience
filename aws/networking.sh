#!/usr/bin/env bash
#
# networking.sh - the [P] networking half, per account, side by side: VPCs (default ones
# flagged), DNS attributes, subnets anchored on zone IDs, route tables and routes, internet
# gateways, the S3/DynamoDB GATEWAY endpoints (the INT-05 anchor), VPC peerings seen from
# both sides, the private hosted zones with their associations and pending authorizations,
# flow logs, NACLs and security groups. The preflight for Stage 3, and the standing
# regression after each of its passes.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/networking.sh                        # every awsds-* profile
#             ./aws/networking.sh awsds-infra-prod       # only the ones named
#             ./aws/networking.sh -                      # CloudShell, ambient credentials
#   writes:   aws/output/networking.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeVpcs, DescribeVpcAttribute, DescribeSubnets, DescribeRouteTables,
#             DescribeInternetGateways, DescribeVpcEndpoints, DescribeVpcPeeringConnections,
#             DescribeFlowLogs, DescribeNetworkAcls, DescribeSecurityGroups,
#             route53:ListHostedZones, GetHostedZone, ListVPCAssociationAuthorizations,
#             logs:DescribeLogGroups, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The subject is a
# PER-ACCOUNT fact whose meaning is the comparison BETWEEN accounts: a CIDR overlap is a
# relation between two VPCs in two accounts, a peering has a requester and an accepter on
# opposite sides of a boundary, and a cross-account zone association exists precisely
# because one account owns the zone and another owns the VPC. A single-profile version
# would answer nothing. Same shape as AZs.sh and tf-backends.sh, and it pays the rule back
# the same way - section 1 prints the caller ARN of every profile.
#
# WHAT IT IS FOR, IN TWO PHASES.
#
#   BEFORE Stage 3: "what networking already exists". Nothing in the plan has measured
#   whether the vended accounts carry a DEFAULT VPC (172.31.0.0/16, public subnets, an IGW
#   already attached) - and the stage never says what happens to one. Principle 4 says
#   private by default; D22 says Data Governance gets no VPC at all. Whether either
#   sentence is TRUE TODAY is what section 2 answers.
#
#   AFTER each Stage 3 pass: the readings that would otherwise be one console tab per
#   account - validation 2 (no route into 10.40.0.0/16), step 6.5 (10.90.0.0/24 in no
#   route table), step 4.4 (the four zone associations), step 5 (a flow log per VPC),
#   step 4.1 (both DNS attributes on). Each is a check that FAILS, not a listing to eyeball.
#
# THE [P]-STABILITY DELIVERABLE IS A DIFF OF TWO RUNS OF THIS FILE. Stage 3's lifecycle
# deliverable wants every foundation/ ID byte-identical across a make down / make up.
# Run this, copy aws/output/networking.txt aside, cycle, run again, diff: the only lines
# that may change are the timestamp and the [E] resources this file deliberately omits.
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - Staging is UNVENDED (held on the account cap) and has no profile: the deliverable
#     "describe-vpc-peering-connections in Staging returns empty" cannot run from here
#     until the vend. Absence from this report is silence, not evidence.
#   - Management, Log Archive and Audit hold no CLI profile by design; their default VPCs
#     (if any) are unmeasured here. None of them is meant to hold a Stage 3 VPC.
#   - This is a CONTROL-PLANE reading. The stage's behavioural proofs - dnf through the
#     gateway endpoint, NXDOMAIN from Staging, the probe reaching GitLab's port - need the
#     throwaway probe instances the stage describes; a describe call proves none of them
#     (read the configuration when the question is configuration, keep probes for
#     behaviour - Lesson 20).

set -uo pipefail

PROFILE_PREFIX="awsds-"
REGION="us-west-2"
SSO_SESSION="awsds"

# The two profiles step 4.4's association checks resolve against. Profile names are the
# convention aws/INDEX.md documents; if one is renamed, the check reports "cannot resolve"
# rather than failing wrongly.
SBX_PROFILE="awsds-infra-sandbox-1"
DEV_PROFILE="awsds-infra-dev"
DATA_PROFILE="awsds-infra-data"
CANARY_PROFILE="awsds-policy-canary"

# The two ranges the route checks are about (Stage 3 validation 2 and step 6.5).
STAGING_CIDR="10.40.0.0/16"
WIREGUARD_CIDR="10.90.0.0/24"

# The range Control Tower's ACCOUNT FACTORY VPC occupies (measured 2026-08-15: every vended
# account carries one - IsDefault=False, three private subnets named aws-controltower-*, no
# IGW, a flow log at 90 days). The project's own address plan is 10.0.0.0/8-based (step
# 1.2), so a VPC in this range is a vend artifact, never one of ours.
AF_CIDR="172.31.0.0/16"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../CLAUDE.md" ]; then
  cd "$SCRIPT_DIR/.."
  OUT_DIR="aws/output"
else
  cd "$SCRIPT_DIR"
  OUT_DIR="."
fi
OUT="$OUT_DIR/networking.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/networking.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

ERRORS="$TMP/errors.txt"
CALLERS="$TMP/callers.tsv"    # PROFILE <tab> ACCOUNT <tab> ARN
VPCS="$TMP/vpcs.tsv"          # PROFILE <tab> VPC <tab> CIDR <tab> DEFAULT <tab> DNSSUP <tab> DNSHOST
ROUTES="$TMP/routes.tsv"      # PROFILE <tab> RTB <tab> VPC <tab> DEST <tab> TARGET <tab> STATE
GWEPS="$TMP/gweps.tsv"        # PROFILE <tab> VPCE <tab> SERVICE <tab> VPC
PEERS="$TMP/peers.tsv"        # PROFILE <tab> PCX <tab> STATUS <tab> REQ_VPC <tab> REQ_CIDR <tab> ACC_VPC <tab> ACC_CIDR
ZONES="$TMP/zones.tsv"        # PROFILE <tab> ZONE_ID <tab> ZONE_NAME
ZONEVPCS="$TMP/zonevpcs.tsv"  # PROFILE <tab> ZONE_NAME <tab> VPC <tab> REGION
FLOWS="$TMP/flows.tsv"        # PROFILE <tab> VPC (has a flow log)
CHECKS="$TMP/checks.tsv"      # RESULT <tab> ID <tab> WHAT <tab> DETAIL
: >"$ERRORS"; : >"$CALLERS"; : >"$VPCS"; : >"$ROUTES"; : >"$GWEPS"; : >"$PEERS"
: >"$ZONES"; : >"$ZONEVPCS"; : >"$FLOWS"; : >"$CHECKS"

# ------------------------------------------------------------------------------ helpers

note() { printf '%s\n' "$*" >&2; }

h1() {
  printf '\n\n################################################################################\n'
  printf '# %s\n' "$*"
  printf '################################################################################\n\n'
}
h2() { printf '\n--- %s ---\n\n' "$*"; }

aws_() { # aws_ <profile> <aws args...>
  local p="$1"; shift
  if [ "$p" = "-" ] || [ "$p" = "none" ]; then
    command aws --region "$REGION" "$@" </dev/null
  else
    command aws --profile "$p" --region "$REGION" "$@" </dev/null
  fi
}

RUN_OUT=""; RUN_STATUS=0; RUN_ERR=""
run() { # run <profile> <aws args...>  - logs nothing; the caller decides what an error means
  local p="$1"; shift
  RUN_OUT=$(aws_ "$p" "$@" 2>"$TMP/stderr")
  RUN_STATUS=$?
  RUN_ERR=$(cat "$TMP/stderr")
  [ "$RUN_STATUS" -eq 0 ] || RUN_OUT=""
}
logerr() { printf '[%s] aws %s\n    %s\n' "$1" "$2" \
             "$(printf '%s' "$3" | head -n 2 | tr '\n' ' ')" >>"$ERRORS"; }

show() { # show <profile> <aws args...>
  local p="$1"; shift
  printf '$ aws --profile %s %s\n\n' "$p" "$*"
  local out status
  out=$(aws_ "$p" "$@" 2>&1)
  status=$?
  if [ "$status" -ne 0 ]; then
    printf '%s\n\n!! COMMAND FAILED (exit %s)\n\n' "$out" "$status"
    logerr "$p" "$*" "$out"
    return "$status"
  fi
  if [ -n "$out" ]; then printf '%s\n' "$out"; else printf '(empty result - the call succeeded and returned nothing)\n'; fi
  printf '\n'
}

tabulate() { column -t -s $'\t'; }
check() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >>"$CHECKS"; }

# Does IPv4 CIDR $1 overlap IPv4 CIDR $2? Prints "yes" if so. Non-IPv4 inputs print nothing.
cidr_overlap() {
  case "$1" in [0-9]*.*/*) ;; *) return ;; esac
  case "$2" in [0-9]*.*/*) ;; *) return ;; esac
  awk -v a="$1" -v b="$2" '
    function ip2n(ip, o) { split(ip, o, "."); return ((o[1]*256+o[2])*256+o[3])*256+o[4] }
    function base(c, q, n, s) { split(c, q, "/"); n = ip2n(q[1]); s = 2^(32-q[2]); return n - (n % s) }
    function last(c, q) { split(c, q, "/"); return base(c) + 2^(32-q[2]) - 1 }
    BEGIN { if (base(a) <= last(b) && base(b) <= last(a)) print "yes" }'
}

# ------------------------------------------------------------ which profiles to measure

if [ "$#" -gt 0 ]; then
  PROFILES=$(printf '%s\n' "$@")
  PROFILE_SOURCE="named on the command line"
else
  PROFILES=$(command aws configure list-profiles 2>/dev/null | grep "^$PROFILE_PREFIX" | sort)
  PROFILE_SOURCE="every '$PROFILE_PREFIX*' profile in ~/.aws/config"
fi

if [ -z "$PROFILES" ]; then
  note "no profiles to measure ($PROFILE_SOURCE matched nothing)"
  exit 1
fi

# ---------------------------------------------------------------------------- preflight

note "region: $REGION"
LIVE="$TMP/live.txt"; : >"$LIVE"
while IFS= read -r p; do
  [ -n "$p" ] || continue
  if out=$(aws_ "$p" sts get-caller-identity --query '[Account,Arn]' --output text 2>&1); then
    acct=$(printf '%s' "$out" | awk '{print $1}')
    arn=$(printf '%s' "$out" | awk '{print $2}')
    printf '%s\t%s\t%s\n' "$p" "$acct" "$arn" >>"$CALLERS"
    printf '%s\n' "$p" >>"$LIVE"
    note "  $p  OK"
  else
    printf '%s\t-\t(failed)\n' "$p" >>"$CALLERS"
    logerr "$p" "sts get-caller-identity" "$out"
    note "  $p  FAILED"
  fi
done <<PROFILES
$PROFILES
PROFILES

if [ ! -s "$LIVE" ]; then
  note ""
  note "no profile authenticated. log in first:"
  note "  aws sso login --sso-session $SSO_SESSION"
  note ""
  note "the previous $OUT, if any, is left untouched."
  exit 1
fi

# ------------------------------------------------------------------- measure each account

while IFS= read -r p; do
  [ -n "$p" ] || continue
  note "measuring $p ..."

  # VPCs, then the two DNS attributes each - DescribeVpcs does not return them.
  run "$p" ec2 describe-vpcs --query 'Vpcs[].[VpcId,CidrBlock,IsDefault,State]' --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "ec2 describe-vpcs" "$RUN_ERR"
    continue
  fi
  printf '%s\n' "$RUN_OUT" | sed '/^$/d' | while IFS=$'\t' read -r vpc cidr isdef state; do
    [ -n "${vpc:-}" ] || continue
    run "$p" ec2 describe-vpc-attribute --vpc-id "$vpc" --attribute enableDnsSupport \
        --query 'EnableDnsSupport.Value' --output text
    dnssup="${RUN_OUT:-?}"
    [ "$RUN_STATUS" -eq 0 ] || logerr "$p" "ec2 describe-vpc-attribute enableDnsSupport $vpc" "$RUN_ERR"
    run "$p" ec2 describe-vpc-attribute --vpc-id "$vpc" --attribute enableDnsHostnames \
        --query 'EnableDnsHostnames.Value' --output text
    dnshost="${RUN_OUT:-?}"
    [ "$RUN_STATUS" -eq 0 ] || logerr "$p" "ec2 describe-vpc-attribute enableDnsHostnames $vpc" "$RUN_ERR"
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$p" "$vpc" "$cidr" "$isdef" "$dnssup" "$dnshost" >>"$VPCS"
  done

  # Routes, one call per route table so the TSV stays flat.
  run "$p" ec2 describe-route-tables --query 'RouteTables[].[RouteTableId,VpcId]' --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "ec2 describe-route-tables" "$RUN_ERR"
  else
    printf '%s\n' "$RUN_OUT" | sed '/^$/d' | while IFS=$'\t' read -r rtb vpc; do
      [ -n "${rtb:-}" ] || continue
      run "$p" ec2 describe-route-tables --route-table-ids "$rtb" \
          --query 'RouteTables[0].Routes[].[DestinationCidrBlock || DestinationIpv6CidrBlock || DestinationPrefixListId || `-`, GatewayId || NatGatewayId || VpcPeeringConnectionId || TransitGatewayId || EgressOnlyInternetGatewayId || NetworkInterfaceId || InstanceId || `-`, State || `-`]' \
          --output text
      if [ "$RUN_STATUS" -ne 0 ]; then
        logerr "$p" "ec2 describe-route-tables --route-table-ids $rtb" "$RUN_ERR"
        continue
      fi
      printf '%s\n' "$RUN_OUT" | sed '/^$/d' | while IFS=$'\t' read -r dest target state; do
        [ -n "${dest:-}" ] || continue
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$p" "$rtb" "$vpc" "$dest" "$target" "$state" >>"$ROUTES"
      done
    done
  fi

  # Gateway endpoints - the [P] anchor INT-05 conditions on.
  run "$p" ec2 describe-vpc-endpoints --filters Name=vpc-endpoint-type,Values=Gateway \
      --query 'VpcEndpoints[].[VpcEndpointId,ServiceName,VpcId]' --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "ec2 describe-vpc-endpoints (gateway)" "$RUN_ERR"
  else
    printf '%s\n' "$RUN_OUT" | sed '/^$/d' | while IFS=$'\t' read -r ep svc vpc; do
      [ -n "${ep:-}" ] || continue
      printf '%s\t%s\t%s\t%s\n' "$p" "$ep" "$svc" "$vpc" >>"$GWEPS"
    done
  fi

  # Peerings - the API answers from both sides, so the same pcx-* appears under both profiles.
  run "$p" ec2 describe-vpc-peering-connections \
      --query 'VpcPeeringConnections[].[VpcPeeringConnectionId,Status.Code,RequesterVpcInfo.VpcId,RequesterVpcInfo.CidrBlock || `-`,AccepterVpcInfo.VpcId,AccepterVpcInfo.CidrBlock || `-`]' \
      --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "ec2 describe-vpc-peering-connections" "$RUN_ERR"
  else
    printf '%s\n' "$RUN_OUT" | sed '/^$/d' | while IFS=$'\t' read -r pcx status rvpc rcidr avpc acidr; do
      [ -n "${pcx:-}" ] || continue
      printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$p" "$pcx" "$status" "$rvpc" "$rcidr" "$avpc" "$acidr" >>"$PEERS"
    done
  fi

  # Private hosted zones this account owns, their associated VPCs, pending authorizations.
  run "$p" route53 list-hosted-zones --query 'HostedZones[?Config.PrivateZone].[Id,Name]' --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "route53 list-hosted-zones" "$RUN_ERR"
  else
    printf '%s\n' "$RUN_OUT" | sed '/^$/d' | while IFS=$'\t' read -r zid zname; do
      [ -n "${zid:-}" ] || continue
      zid="${zid##*/}"; zname="${zname%.}"
      printf '%s\t%s\t%s\n' "$p" "$zid" "$zname" >>"$ZONES"
      run "$p" route53 get-hosted-zone --id "$zid" --query 'VPCs[].[VPCId,VPCRegion]' --output text
      if [ "$RUN_STATUS" -ne 0 ]; then
        logerr "$p" "route53 get-hosted-zone $zid" "$RUN_ERR"
      else
        printf '%s\n' "$RUN_OUT" | sed '/^$/d' | while IFS=$'\t' read -r zvpc zreg; do
          [ -n "${zvpc:-}" ] || continue
          printf '%s\t%s\t%s\t%s\n' "$p" "$zname" "$zvpc" "$zreg" >>"$ZONEVPCS"
        done
      fi
    done
  fi

  # Flow logs - which VPCs have one.
  run "$p" ec2 describe-flow-logs --query 'FlowLogs[].[ResourceId]' --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "ec2 describe-flow-logs" "$RUN_ERR"
  else
    printf '%s\n' "$RUN_OUT" | tr '\t' '\n' | sed '/^$/d' | sort -u | while IFS= read -r rid; do
      printf '%s\t%s\n' "$p" "$rid" >>"$FLOWS"
    done
  fi
done <"$LIVE"

# ------------------------------------------------------------------------------- checks

NONDEF=$(awk -F'\t' '$4=="False"' "$VPCS" | wc -l | tr -d ' ')

# NT-1: VPCs nobody in this project created - the field Stage 3 never named (Lesson 16,
# Lesson 17). Three shapes: a true DEFAULT VPC (public subnets, an IGW); the ACCOUNT
# FACTORY VPC every vend leaves behind (172.31.0.0/16, private-only); and a project-range
# VPC in an account where a decision says there must be none.
while IFS=$'\t' read -r p vpc cidr isdef dnssup dnshost; do
  [ -n "${p:-}" ] || continue
  extra=""
  [ "$p" = "$DATA_PROFILE" ] && extra=" In THIS account the sentence is stronger: D22 says Data Governance gets no VPC at all - today that sentence is an intention, not a state (Lesson 5)."
  [ "$p" = "$CANARY_PROFILE" ] && extra=" In THIS account the sentence is stronger: the canary is deliberately empty (D29)."
  if [ "$isdef" = "True" ]; then
    check note "NT-1" "default VPC in $p" \
      "$vpc ($cidr) - public subnets and an attached IGW nobody chose (principle 4: private by default). Stage 3 never says what happens to it; decide delete-or-keep during the stage and record it in the log.$extra"
  elif [ -n "$(cidr_overlap "$cidr" "$AF_CIDR")" ]; then
    check note "NT-1" "Account Factory VPC in $p" \
      "$vpc ($cidr) - the vend artifact Control Tower leaves in every account (Lesson 17: a service that sets itself up creates resources nobody chose). Stage 3 never mentions it: decide delete-or-keep during the stage, and note that the Account Factory NETWORK CONFIGURATION decides whether the next vend (Staging, every Stage 14 Sandbox) arrives with one.$extra"
  else
    case "$p" in
      "$DATA_PROFILE")   check fail "NT-1" "project-range VPC in $p" \
        "$vpc ($cidr) - D22 says Data Governance gets no VPC at all. An intention is not a control (Lesson 5); this is the measurement." ;;
      "$CANARY_PROFILE") check fail "NT-1" "project-range VPC in $p" \
        "$vpc ($cidr) - the canary is deliberately empty (D29). A leftover here usually means an interrupted battery: read the log before deleting anything." ;;
    esac
  fi
done <"$VPCS"

# NT-2: both DNS attributes on every non-default VPC (step 4.1) - endpoint private DNS and
# everything in step 4 silently fails without them, and aws_vpc defaults hostnames to false.
while IFS=$'\t' read -r p vpc cidr isdef dnssup dnshost; do
  [ -n "${p:-}" ] || continue
  [ "$isdef" = "False" ] || continue
  if [ "$dnssup" = "True" ] && [ "$dnshost" = "True" ]; then
    check pass "NT-2" "DNS attributes on $vpc ($p)" "enableDnsSupport=True enableDnsHostnames=True"
  else
    check fail "NT-2" "DNS attributes on $vpc ($p)" \
      "enableDnsSupport=$dnssup enableDnsHostnames=$dnshost - step 4.1 needs BOTH; private DNS on every interface endpoint and every zone of step 4 resolves nothing without them."
  fi
done <"$VPCS"

# NT-3: no non-local route whose destination overlaps 10.40.0.0/16 (validation 2). The
# local route of a future Staging VPC is excluded on purpose: the validation's intent is
# "no PEERING path into Staging" (D20), not "Staging may not route to itself".
NT3=0
while IFS=$'\t' read -r p rtb vpc dest target state; do
  [ -n "${p:-}" ] || continue
  [ "$target" = "local" ] && continue
  if [ -n "$(cidr_overlap "$dest" "$STAGING_CIDR")" ]; then
    check fail "NT-3" "route into the Staging range" \
      "$p $rtb: $dest -> $target ($state) overlaps $STAGING_CIDR - Staging is deliberately unpeered (D20, step 6.6)."
    NT3=$((NT3 + 1))
  fi
done <"$ROUTES"
if [ "$NT3" -eq 0 ] && [ -s "$ROUTES" ]; then
  check pass "NT-3" "no non-local route overlaps $STAGING_CIDR" \
    "$(wc -l <"$ROUTES" | tr -d ' ') routes read across $(cut -f1 "$ROUTES" | sort -u | wc -l | tr -d ' ') account(s)"
fi

# NT-4: 10.90.0.0/24 in no route table anywhere (step 6.5) - peering does no edge-to-edge
# routing, so a route to the WireGuard client range is a route that can never work, and its
# presence means somebody is about to lose an evening to it.
NT4=0
while IFS=$'\t' read -r p rtb vpc dest target state; do
  [ -n "${p:-}" ] || continue
  if [ -n "$(cidr_overlap "$dest" "$WIREGUARD_CIDR")" ]; then
    check fail "NT-4" "route touching the WireGuard client range" \
      "$p $rtb: $dest -> $target ($state) overlaps $WIREGUARD_CIDR - that range is SNATed by the WireGuard instance and appears in no route table by design (step 6.5)."
    NT4=$((NT4 + 1))
  fi
done <"$ROUTES"
if [ "$NT4" -eq 0 ] && [ -s "$ROUTES" ]; then
  check pass "NT-4" "no route overlaps $WIREGUARD_CIDR" "same read as NT-3"
fi

# NT-5: pairwise CIDR overlap among project VPCs, across every measured account (1.2:
# ranges are non-overlapping even between accounts that will never peer). Default and
# Account Factory VPCs are excluded - they are ALL 172.31.0.0/16, they never peer, and
# fifteen overlap rows with one root cause would bury a real one; their fate is NT-1's
# question, and they are counted once below.
awk -F'\t' '$4=="False" && $3 !~ /^172\.31\./ {print $1"\t"$2"\t"$3}' "$VPCS" >"$TMP/nondef.tsv"
N_AF=$(awk -F'\t' '$3 ~ /^172\.31\./' "$VPCS" | wc -l | tr -d ' ')
[ "$N_AF" -gt 0 ] && check note "NT-5" "VPCs excluded from the overlap check" \
  "$N_AF in the 172.31.0.0/16 range (default or Account Factory) - all mutually overlapping by construction, never peered, and covered by NT-1 instead."
if [ -s "$TMP/nondef.tsv" ]; then
  awk -F'\t' '
    function ip2n(ip, o) { split(ip, o, "."); return ((o[1]*256+o[2])*256+o[3])*256+o[4] }
    function base(c, q, n, s) { split(c, q, "/"); n = ip2n(q[1]); s = 2^(32-q[2]); return n - (n % s) }
    function last(c, q) { split(c, q, "/"); return base(c) + 2^(32-q[2]) - 1 }
    { P[NR]=$1; V[NR]=$2; C[NR]=$3 }
    END {
      for (i = 1; i <= NR; i++) for (j = i + 1; j <= NR; j++) {
        # the same VPC seen through two profiles that reach the same account is one VPC,
        # not an overlap
        if (V[i] == V[j]) continue
        if (base(C[i]) <= last(C[j]) && base(C[j]) <= last(C[i]))
          printf "%s %s (%s) overlaps %s %s (%s)\n", P[i], V[i], C[i], P[j], V[j], C[j]
      }
    }' "$TMP/nondef.tsv" >"$TMP/overlaps.txt"
  if [ -s "$TMP/overlaps.txt" ]; then
    while IFS= read -r line; do
      check fail "NT-5" "VPC CIDR overlap" \
        "$line - a CIDR chosen to overlap cannot be revisited without rebuilding the VPC (step 1.2)."
    done <"$TMP/overlaps.txt"
  else
    check pass "NT-5" "no CIDR overlap among non-default VPCs" "$NONDEF VPC(s) compared pairwise"
  fi
fi

# NT-6: no peering touches the Staging range from either side (D20, step 6.6). The loop
# body runs in a subshell (pipe), so the verdict is counted from CHECKS afterwards.
sort -u "$PEERS" | while IFS=$'\t' read -r p pcx status rvpc rcidr avpc acidr; do
  [ -n "${p:-}" ] || continue
  for c in "$rcidr" "$acidr"; do
    if [ -n "$(cidr_overlap "$c" "$STAGING_CIDR")" ]; then
      check fail "NT-6" "peering touching the Staging range" \
        "$pcx ($status, seen from $p): $rvpc $rcidr <-> $avpc $acidr - there is no peering to Staging, by decision (D20)."
    fi
  done
done
if [ -s "$PEERS" ] && [ "$(awk -F'\t' '$1=="fail" && $2=="NT-6"' "$CHECKS" | wc -l | tr -d ' ')" -eq 0 ]; then
  check pass "NT-6" "no peering touches $STAGING_CIDR" \
    "$(cut -f2 "$PEERS" | sort -u | wc -l | tr -d ' ') distinct peering(s) read"
fi

# NT-7: every non-default VPC has a flow log (step 5 is in the same slice as step 1, so a
# project VPC without one is a slice that half-applied).
while IFS=$'\t' read -r p vpc cidr isdef dnssup dnshost; do
  [ -n "${p:-}" ] || continue
  [ "$isdef" = "False" ] || continue
  if grep -q "^$p	$vpc$" "$FLOWS"; then
    check pass "NT-7" "flow log on $vpc ($p)" "present"
  else
    check fail "NT-7" "flow log on $vpc ($p)" \
      "none - step 5 puts one per VPC in the same foundation/ slice, so a VPC without one is a half-applied slice, and under design B the flow log is how a dropped packet is seen at all."
  fi
done <"$VPCS"

# NT-8: the four cross-account zone associations of step 4.4, resolved against the single
# non-default VPC of the Sandbox and Development profiles. If an account has zero or more
# than one non-default VPC the check says "cannot resolve" rather than guessing.
for zone in prod.internal pages.internal; do
  if ! grep -q "	$zone$" "$ZONES"; then
    check note "NT-8" "zone $zone" "not created yet - expected before Stage 3 step 4."
    continue
  fi
  for tp in "$SBX_PROFILE" "$DEV_PROFILE"; do
    tv=$(awk -F'\t' -v p="$tp" '$1==p && $4=="False" {n++; last=$2} END {if (n==1) print last}' "$VPCS")
    if [ -z "$tv" ]; then
      check note "NT-8" "$zone associated with the $tp VPC" \
        "cannot resolve: $tp has zero or several non-default VPCs, or was not measured."
    elif awk -F'\t' -v z="$zone" -v v="$tv" '$2==z && $3==v {found=1} END {exit !found}' "$ZONEVPCS"; then
      check pass "NT-8" "$zone associated with the $tp VPC" "$tv (step 4.4)"
    else
      check fail "NT-8" "$zone associated with the $tp VPC" \
        "$tv is NOT in the zone's association list - the query for gitlab.$zone from that VPC returns NXDOMAIN, and over the VPN that is 'GitLab is down' (step 4.4)."
    fi
  done
done
if grep -q "	sandbox.internal$" "$ZONES"; then
  check pass "NT-8" "zone sandbox.internal exists" "associated at creation, no handshake needed (step 4.4)"
else
  check note "NT-8" "zone sandbox.internal" "not created yet - expected before Stage 3 step 4."
fi

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'Networking - the [P] foundation half, per account, side by side\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profiles  : %s\n' "$PROFILE_SOURCE"
printf 'region    : %s\n' "$REGION"
printf 'produced  : aws/networking.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Which accounts were measured, and as whom\n'
printf '  2. VPCs, and the two DNS attributes of each\n'
printf '  3. Subnets - anchored on the ZONE ID column\n'
printf '  4. Route tables, routes, internet gateways\n'
printf '  5. Gateway endpoints - the [P] anchor (INT-05)\n'
printf '  6. VPC peerings, seen from both sides\n'
printf '  7. Private hosted zones, associations, pending authorizations\n'
printf '  8. Flow logs, and their retention\n'
printf '  9. NACLs and security groups\n'
printf '  10. CHECKS\n'
printf '  11. The accounts nothing here is measuring\n'
printf '  12. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - "NO VPC" IS THE EXPECTED ANSWER UNTIL STAGE 3 PASS 1 HAS RUN - except that a\n'
printf '    DEFAULT VPC may be sitting there already, which is exactly what section 2 and\n'
printf '    check NT-1 exist to expose. Nothing in the plan has decided its fate.\n'
printf '  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT. Section 11 names the ones nothing\n'
printf '    reached - Staging above all, which is UNVENDED and therefore silent.\n'
printf '  - THIS IS A CONTROL-PLANE READING. The behavioural proofs of the stage (dnf\n'
printf '    through the endpoint, NXDOMAIN, the probe reaching GitLab) need the throwaway\n'
printf '    probe instances the stage describes; no describe call substitutes for them.\n'
printf '  - THE [P]-STABILITY DELIVERABLE IS A DIFF OF TWO RUNS: copy this file aside,\n'
printf '    make down + make up, re-run, diff. Only the timestamp may change.\n'
printf '\n'
printf 'THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.\n'
printf 'Do not copy one into a tracked file.\n'

# ======================================================================================
h1 "1. Which accounts were measured, and as whom"

printf 'A profile is an (account, permission set) pair; every awsds-* profile here resolves\n'
printf 'to the infrastructure user. A `(failed)` row is a profile that did not authenticate,\n'
printf 'never a compliant one.\n\n'

{
  printf 'PROFILE\tACCOUNT\tCALLER ARN\n'
  cat "$CALLERS"
} | tabulate

# ======================================================================================
h1 "2. VPCs, and the two DNS attributes of each"

if [ -s "$VPCS" ]; then
  {
    printf 'PROFILE\tVPC\tCIDR\tDEFAULT\tdnsSupport\tdnsHostnames\n'
    sort "$VPCS"
  } | tabulate
  printf '\n'
  printf 'The DEFAULT column is the Stage 3 preflight: a True row is a VPC nobody in this\n'
  printf 'project created - public subnets, an attached IGW - and the stage never says what\n'
  printf 'happens to it (check NT-1). The two DNS columns are step 4.1: aws_vpc defaults\n'
  printf 'dnsHostnames to FALSE, and everything in step 4 needs both True.\n'
else
  printf 'NO VPC IN ANY MEASURED ACCOUNT - including no default VPC.\n'
fi

printf '\nSecondary CIDR associations, where any exist:\n\n'
while IFS= read -r p; do
  [ -n "$p" ] || continue
  h2 "$p"
  show "$p" ec2 describe-vpcs \
      --query 'Vpcs[?length(CidrBlockAssociationSet) > `1`].[VpcId, join(`,`, CidrBlockAssociationSet[].CidrBlock)]' \
      --output table
done <"$LIVE"

# ======================================================================================
h1 "3. Subnets - anchored on the ZONE ID column"

printf 'Subnets anchor on zone IDs, never on list position (step 1.5, settled by 1b step 6).\n'
printf 'The AZ NAME column is a per-account label; the ZONE ID names the datacenter. Compare\n'
printf 'this section against aws/output/AZs.txt when a peering seems slow: two peered subnets\n'
printf 'whose zone IDs differ pay USD 0.01/GB each way with no error anywhere.\n\n'

while IFS= read -r p; do
  [ -n "$p" ] || continue
  h2 "$p"
  show "$p" ec2 describe-subnets \
      --query 'sort_by(Subnets,&SubnetId)[].[SubnetId,VpcId,CidrBlock,AvailabilityZone,AvailabilityZoneId,MapPublicIpOnLaunch,Tags[?Key==`Name`].Value|[0]]' \
      --output table
done <"$LIVE"

# ======================================================================================
h1 "4. Route tables, routes, internet gateways"

printf 'The rows checks NT-3 and NT-4 read. A route whose TARGET is "local" is the VPC\n'
printf 'routing to itself and is excluded from NT-3 on purpose. The private tier should show\n'
printf 'a 0.0.0.0/0 route ONLY under design A and only while egress/ is up (step 2.2); the\n'
printf 'isolated tier should never show one - that is what makes it isolated.\n\n'

if [ -s "$ROUTES" ]; then
  {
    printf 'PROFILE\tROUTE TABLE\tVPC\tDESTINATION\tTARGET\tSTATE\n'
    sort "$ROUTES"
  } | tabulate
else
  printf '(no route table in any measured account)\n'
fi

printf '\nInternet gateways:\n\n'
while IFS= read -r p; do
  [ -n "$p" ] || continue
  h2 "$p"
  show "$p" ec2 describe-internet-gateways \
      --query 'InternetGateways[].[InternetGatewayId, Attachments[0].VpcId]' --output table
done <"$LIVE"

# ======================================================================================
h1 "5. Gateway endpoints - the [P] anchor (INT-05)"

printf 'THESE IDS ARE WHAT STAGE 5 MAY CONDITION ON, AND THE ONLY ENDPOINT IDS THAT MAY BE\n'
printf 'NAMED IN ANY POLICY (Lesson 3, step 3.3): they are [P], survive every make down, and\n'
printf 'live in the same slice as the VPC. The interface endpoints of egress.sh get new IDs\n'
printf 'on every make up and may anchor nothing. If a row here CHANGES across a make down /\n'
printf 'make up cycle, that is the INT-05 failure mode arriving early - stop and look.\n\n'

if [ -s "$GWEPS" ]; then
  {
    printf 'PROFILE\tENDPOINT\tSERVICE\tVPC\n'
    sort "$GWEPS"
  } | tabulate
else
  printf '(none in any measured account - expected before Stage 3 step 3)\n'
fi

# ======================================================================================
h1 "6. VPC peerings, seen from both sides"

printf 'The API answers from both sides, so one healthy peering between two measured\n'
printf 'accounts appears TWICE below - same pcx-* id, two PROFILE rows. A peering that\n'
printf 'appears under only one measured side is worth a second look. Expected once pass 2\n'
printf 'is done: exactly two distinct ids - Sandbox<->Production and Development<->Production\n'
printf '(INT-09) - and nothing touching 10.40.0.0/16 (NT-6, D20).\n\n'

if [ -s "$PEERS" ]; then
  {
    printf 'PROFILE\tPCX\tSTATUS\tREQ VPC\tREQ CIDR\tACC VPC\tACC CIDR\n'
    sort "$PEERS"
  } | tabulate
else
  printf '(no peering in any measured account - expected before Stage 3 pass 2)\n'
fi

# ======================================================================================
h1 "7. Private hosted zones, associations, pending authorizations"

printf 'Step 4.2 creates THREE zones and deliberately not one per account: sandbox.internal\n'
printf '(Sandbox), prod.internal and pages.internal (Production). Development and Staging\n'
printf 'get none. The association table is step 4.4: prod.internal and pages.internal must\n'
printf 'each reach the Sandbox AND Development VPCs, or gitlab.prod.internal is NXDOMAIN\n'
printf 'over the VPN. Check NT-8 resolves it mechanically.\n\n'

if [ -s "$ZONES" ]; then
  {
    printf 'OWNER PROFILE\tZONE ID\tZONE\n'
    sort "$ZONES"
  } | tabulate
  printf '\nAssociated VPCs per zone (owner-side view). The account owning each VPC is\n'
  printf 'resolved against section 2 where possible:\n\n'
  {
    printf 'OWNER\tZONE\tVPC\tREGION\tVPC BELONGS TO\n'
    sort -u "$ZONEVPCS" | while IFS=$'\t' read -r zp zn zv zr; do
      [ -n "${zp:-}" ] || continue
      owner=$(awk -F'\t' -v v="$zv" '$2==v {print $1; exit}' "$VPCS")
      printf '%s\t%s\t%s\t%s\t%s\n' "$zp" "$zn" "$zv" "$zr" "${owner:-(not measured here)}"
    done
  } | tabulate
else
  printf '(no private hosted zone in any measured account - expected before Stage 3 step 4)\n'
fi

printf '\nPending association authorizations, per zone (the 4.5 ordering trap: re-creating\n'
printf 'an association after a VPC rebuild needs a fresh authorization; a pending row here\n'
printf 'is a handshake whose second half has not run):\n\n'
if [ -s "$ZONES" ]; then
  while IFS=$'\t' read -r zp zid zname; do
    [ -n "${zp:-}" ] || continue
    h2 "$zname ($zp)"
    show "$zp" route53 list-vpc-association-authorizations --hosted-zone-id "$zid" \
        --query 'VPCs[].[VPCId,VPCRegion]' --output table
  done <"$ZONES"
else
  printf '(no zone to ask about)\n'
fi

# ======================================================================================
h1 "8. Flow logs, and their retention"

while IFS= read -r p; do
  [ -n "$p" ] || continue
  h2 "$p"
  show "$p" ec2 describe-flow-logs \
      --query 'FlowLogs[].[FlowLogId,ResourceId,TrafficType,LogDestinationType,LogGroupName,DeliverLogsStatus]' \
      --output table
  run "$p" ec2 describe-flow-logs --query 'FlowLogs[].LogGroupName' --output text
  printf '%s\n' "$RUN_OUT" | tr '\t' '\n' | sed '/^$/d; /^None$/d' | sort -u | while IFS= read -r lg; do
    run "$p" logs describe-log-groups --log-group-name-prefix "$lg" \
        --query 'logGroups[?logGroupName==`'"$lg"'`].retentionInDays | [0]' --output text
    printf 'log group %s: retention %s\n' "$lg" "${RUN_OUT:-?}"
    printf '\n'
  done
done <"$LIVE"

printf 'Retention is the term that accumulates (step 5.1 says 7 days, explicit and short);\n'
printf '"None" means NEVER EXPIRE, which is the one value that cannot be intended here.\n'

# ======================================================================================
h1 "9. NACLs and security groups"

printf 'NACLs stay at the default allow, by decision (step 2.3): a False row in the DEFAULT\n'
printf 'column below is a stateless deny somebody added, and the fastest way to break a path\n'
printf 'nobody can then debug.\n\n'
while IFS= read -r p; do
  [ -n "$p" ] || continue
  h2 "$p"
  show "$p" ec2 describe-network-acls \
      --query 'NetworkAcls[].[NetworkAclId,VpcId,IsDefault,length(Entries)]' --output table
done <"$LIVE"

printf '\nSecurity groups, and the subset with an ingress rule open to the world. Wide-open\n'
printf 'ingress is a LISTING here, not a failure: from Stage 4 on, exactly one such rule is\n'
printf 'expected - UDP 51820 on the WireGuard host SG - and anything beyond it is what this\n'
printf 'block exists to make visible (step 6.4: never 0.0.0.0/0 on a peering path).\n\n'
while IFS= read -r p; do
  [ -n "$p" ] || continue
  h2 "$p"
  show "$p" ec2 describe-security-groups \
      --query 'SecurityGroups[].[GroupId,GroupName,VpcId]' --output table
  printf 'open to 0.0.0.0/0 or ::/0 (ingress):\n\n'
  show "$p" ec2 describe-security-groups \
      --query 'SecurityGroups[?IpPermissions[?IpRanges[?CidrIp==`0.0.0.0/0`] || Ipv6Ranges[?CidrIpv6==`::/0`]]].[GroupId,GroupName,VpcId]' \
      --output table
done <"$LIVE"

# ======================================================================================
h1 "10. CHECKS"

if [ "$NONDEF" -eq 0 ]; then
  printf 'NO NON-DEFAULT VPC WAS MEASURED, so most checks below are vacuous rather than\n'
  printf 'passing (Lesson 13). Before Stage 3 pass 1 that is the expected state, and the\n'
  printf 'value of this run is section 2 (are there default VPCs?) and section 11.\n\n'
fi

{
  printf 'RESULT\tID\tWHAT\tDETAIL\n'
  awk -F'\t' '$1=="fail"' "$CHECKS"
  awk -F'\t' '$1=="note"' "$CHECKS"
  awk -F'\t' '$1=="pass"' "$CHECKS"
} | tabulate

NFAIL=$(awk -F'\t' '$1=="fail"' "$CHECKS" | wc -l | tr -d ' ')
printf '\n%s check(s) FAILED.\n' "$NFAIL"
printf '\nWhat the checks are, and where each comes from:\n'
printf '  NT-1  default and Account Factory VPCs flagged (Lessons 16, 17); a\n'
printf '        project-range VPC in Data Governance (D22) or the canary (D29) FAILs\n'
printf '  NT-2  both DNS attributes on every non-default VPC (step 4.1)\n'
printf '  NT-3  no non-local route overlapping 10.40.0.0/16 (validation 2, D20)\n'
printf '  NT-4  no route overlapping 10.90.0.0/24 anywhere (step 6.5)\n'
printf '  NT-5  no CIDR overlap among project VPCs, across accounts (step 1.2);\n'
printf '        172.31.0.0/16 vend artifacts counted once, not pairwise\n'
printf '  NT-6  no peering touching the Staging range (D20, step 6.6)\n'
printf '  NT-7  a flow log on every non-default VPC (step 5)\n'
printf '  NT-8  the four cross-account zone associations of step 4.4\n'

# ======================================================================================
h1 "11. The accounts nothing here is measuring"

printf 'Read this BEFORE reading section 10 as a pass.\n\n'
printf '  - `Staging` has no profile because the account is UNVENDED, held on the account\n'
printf '    cap (Stage 1a). Two Stage 3 deliverables are therefore not runnable from here\n'
printf '    until the vend: its VPC, and the proof that its peering list is EMPTY. NT-3 and\n'
printf '    NT-6 cover the other half - that no measured account routes toward it.\n'
printf '  - Management, Log Archive and Audit hold NO CLI profile, by design (D33/D34).\n'
printf '    None of them gets a Stage 3 VPC; whether they hold a DEFAULT VPC is unmeasured\n'
printf '    here and readable only from CloudShell (`./aws/networking.sh -`).\n'
printf '  - Every Sandbox beyond the first has no profile until Stage 14 vends it (D35).\n'
printf '  - Data Governance IS measured and should show no VPC at all (D22) - the one\n'
printf '    account where an empty section 2 is the passing answer.\n'

# ======================================================================================
h1 "12. Calls that failed"

if [ -s "$ERRORS" ]; then
  printf 'Each entry is a call whose output is missing above. An empty block anywhere else\n'
  printf 'in this file means the call succeeded and returned nothing.\n\n'
  cat "$ERRORS"
else
  printf 'None. Every call returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/networking.sh\n'

}

# ---------------------------------------------------------------------------------- run

main >"$OUT"

NFAIL=$(awk -F'\t' '$1=="fail"' "$CHECKS" | wc -l | tr -d ' ')
note ""
if [ -s "$ERRORS" ]; then
  note "wrote $OUT (some calls FAILED - see section 12)"
  exit 1
fi
if [ "$NFAIL" -gt 0 ]; then
  note "wrote $OUT ($NFAIL CHECK(S) FAILED - see section 10)"
  exit 2
fi
note "wrote $OUT (all checks passed)"
exit 0
