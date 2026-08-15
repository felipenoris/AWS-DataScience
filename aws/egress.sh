#!/usr/bin/env bash
#
# egress.sh - the [E] networking half, per account, side by side: interface endpoints (with
# their AZ count and private-DNS flag), NAT gateways and elastic IPs, every endpoint POLICY
# read against step 9 (the org condition and the AWS-owned-bucket allow-list), the
# service-per-account matrix step 8's lists produce, the hourly burn those resources cost
# RIGHT NOW, and the region's endpoint service-name catalog.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/egress.sh                        # every awsds-* profile
#             ./aws/egress.sh awsds-infra-prod       # only the ones named
#             ./aws/egress.sh -                      # CloudShell, ambient credentials
#   writes:   aws/output/egress.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeVpcEndpoints, DescribeVpcEndpointServices, DescribeNatGateways,
#             DescribeAddresses, DescribeSubnets, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The subject is a
# PER-ACCOUNT fact whose meaning is the comparison BETWEEN accounts: step 8's endpoint list
# is deliberately different per account role, so "is the set right" is only readable with
# the columns side by side - an endpoint present in five accounts and missing in the sixth
# is either the sixth account's gap or the five accounts' waste, and both are the point.
# Section 1 prints the caller ARN of every profile, which is what the one-profile rule
# exists to make visible.
#
# WHAT IT IS FOR, AT THE TWO ENDS OF A SESSION.
#
#   AT make up: did egress/ produce the right set - the per-role lists of step 8, one AZ
#   per endpoint (D9), private DNS on (8.5), and a policy on every endpoint that names the
#   organization (9.1) plus the AWS-owned-bucket allow (9.3). Each is a check that FAILS,
#   not a listing to eyeball - and 9's failure mode in real life is a package manager that
#   HANGS, which no error message will ever attribute to an endpoint policy.
#
#   AT make down - AND WHENEVER IN DOUBT: section 6 is the burn meter. A forgotten egress/
#   costs ~USD 4.08/day and, by decision D12, NO BUDGET ALERT EXISTS to catch it; this
#   section is the manual instrument that risk gets. Zero everywhere is the correct
#   between-sessions answer (D11).
#
# ONE MORE PREFLIGHT IT CARRIES, before anything is paid for: section 7 lists the region's
# endpoint service names - which answers stage verification (i) (is SageMaker Studio's
# endpoint `aws.sagemaker.<region>.studio` rather than `com.amazonaws.*`?), confirms the
# CodeArtifact pair exists in this region (Lesson 6 found it absent in sa-east-1), and
# records which services support an endpoint POLICY at all, which is what keeps check EG-1
# from failing a service that cannot comply.
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - Staging is UNVENDED and has no profile; every Sandbox beyond the first likewise
#     (Stage 14). Absence from this report is silence, not evidence.
#   - Whether the allow-list of 9.3 is COMPLETE is behavioural: `dnf makecache` from a
#     probe instance with no NAT route is the honest test, and it is the stage's, not this
#     script's. This file proves the statement is PRESENT, never that it is sufficient.
#   - INTERFACE ENDPOINT IDS ARE [E] AND MAY BE NAMED BY NOTHING (Lesson 3, step 8.6):
#     they are new on every make up. The IDs a policy may anchor on are the gateway
#     endpoints in networking.sh section 5.

set -uo pipefail

PROFILE_PREFIX="awsds-"
REGION="us-west-2"
SSO_SESSION="awsds"

# Hourly rates, from the Stage 3 cost table (measured for docs/PRICING.md, not reasoned - Lesson
# 6; re-measure THERE if these look stale). The NAT figure includes its public IPv4.
RATE_IFEP="0.010"
RATE_NAT="0.050"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../CLAUDE.md" ]; then
  cd "$SCRIPT_DIR/.."
  OUT_DIR="aws/output"
else
  cd "$SCRIPT_DIR"
  OUT_DIR="."
fi
OUT="$OUT_DIR/egress.txt"
mkdir -p "$OUT_DIR"

export AWS_PAGER=""

TMP=$(mktemp -d "${TMPDIR:-/tmp}/egress.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

ERRORS="$TMP/errors.txt"
CALLERS="$TMP/callers.tsv"    # PROFILE <tab> ACCOUNT <tab> ARN
IFEPS="$TMP/ifeps.tsv"        # PROFILE <tab> VPCE <tab> SERVICE <tab> STATE <tab> NSUBNETS <tab> AZ_IDS <tab> PRIVDNS
NATS="$TMP/nats.tsv"          # PROFILE <tab> NAT <tab> STATE <tab> SUBNET
EPPOL="$TMP/eppol.tsv"        # PROFILE <tab> VPCE <tab> SERVICE <tab> TYPE <tab> VPC <tab> ORGKEYS yes/no
CATALOG="$TMP/catalog.tsv"    # SERVICE <tab> TYPE <tab> POLICY_SUPPORTED <tab> PRIVATE_DNS_NAME
CHECKS="$TMP/checks.tsv"      # RESULT <tab> ID <tab> WHAT <tab> DETAIL
: >"$ERRORS"; : >"$CALLERS"; : >"$IFEPS"; : >"$NATS"; : >"$EPPOL"; : >"$CATALOG"; : >"$CHECKS"

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

# com.amazonaws.us-west-2.ecr.api -> ecr.api ; aws.sagemaker.us-west-2.studio -> aws.sagemaker.studio
short_svc() { printf '%s' "$1" | sed "s/\.$REGION//; s/^com\.amazonaws\.//"; }

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

  # subnet -> AZ-id map, so each endpoint row can say WHICH datacenter it is in (D9).
  run "$p" ec2 describe-subnets --query 'Subnets[].[SubnetId,AvailabilityZoneId]' --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "ec2 describe-subnets" "$RUN_ERR"
    : >"$TMP/subnets-$p.tsv"
  else
    printf '%s\n' "$RUN_OUT" | sed '/^$/d' >"$TMP/subnets-$p.tsv"
  fi

  # vpc -> CIDR map, so an endpoint inside the Account Factory VPC (172.31.0.0/16, the
  # vend artifact networking.sh's NT-1 flags) is judged as an artifact, not as Stage 3's.
  run "$p" ec2 describe-vpcs --query 'Vpcs[].[VpcId,CidrBlock]' --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "ec2 describe-vpcs" "$RUN_ERR"
    : >"$TMP/vpcs-$p.tsv"
  else
    printf '%s\n' "$RUN_OUT" | sed '/^$/d' >"$TMP/vpcs-$p.tsv"
  fi

  # every endpoint, both types; policies are fetched per endpoint so a JSON body cannot
  # break the TSV.
  run "$p" ec2 describe-vpc-endpoints \
      --query 'VpcEndpoints[].[VpcEndpointId,ServiceName,VpcEndpointType,State,PrivateDnsEnabled,VpcId,join(`,`,SubnetIds)]' \
      --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "ec2 describe-vpc-endpoints" "$RUN_ERR"
    continue
  fi
  printf '%s\n' "$RUN_OUT" | sed '/^$/d' | while IFS=$'\t' read -r ep svc type state privdns vpc subnets; do
    [ -n "${ep:-}" ] || continue
    if [ "$type" = "Interface" ]; then
      nsub=0; azids=""
      if [ -n "$subnets" ] && [ "$subnets" != "None" ]; then
        nsub=$(printf '%s' "$subnets" | tr ',' '\n' | grep -c .)
        azids=$(printf '%s' "$subnets" | tr ',' '\n' | while IFS= read -r s; do
                  awk -F'\t' -v s="$s" '$1==s {print $2}' "$TMP/subnets-$p.tsv"
                done | sort -u | paste -sd, -)
      fi
      printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$p" "$ep" "$svc" "$state" "$nsub" "${azids:--}" "$privdns" >>"$IFEPS"
    fi

    run "$p" ec2 describe-vpc-endpoints --vpc-endpoint-ids "$ep" \
        --query 'VpcEndpoints[0].PolicyDocument' --output text
    if [ "$RUN_STATUS" -ne 0 ]; then
      logerr "$p" "ec2 describe-vpc-endpoints --vpc-endpoint-ids $ep (policy)" "$RUN_ERR"
      continue
    fi
    printf '%s\n' "$RUN_OUT" >"$TMP/pol-$p-$ep.json"
    if grep -Eq 'aws:(Principal|Resource)OrgID' "$TMP/pol-$p-$ep.json"; then orgkeys="yes"; else orgkeys="no"; fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$p" "$ep" "$svc" "$type" "$vpc" "$orgkeys" >>"$EPPOL"
  done

  # NAT gateways - the other metered item, and the design-A switch made flesh.
  run "$p" ec2 describe-nat-gateways \
      --query 'NatGateways[].[NatGatewayId,State,SubnetId]' --output text
  if [ "$RUN_STATUS" -ne 0 ]; then
    logerr "$p" "ec2 describe-nat-gateways" "$RUN_ERR"
  else
    printf '%s\n' "$RUN_OUT" | sed '/^$/d' | while IFS=$'\t' read -r nat state subnet; do
      [ -n "${nat:-}" ] || continue
      printf '%s\t%s\t%s\t%s\n' "$p" "$nat" "$state" "$subnet" >>"$NATS"
    done
  fi
done <"$LIVE"

# The service-name catalog is regional, not per-account: one call, from the first live
# profile, answers for everyone.
CATALOG_PROFILE=$(head -n 1 "$LIVE")
note "reading the endpoint service catalog ($CATALOG_PROFILE) ..."
run "$CATALOG_PROFILE" ec2 describe-vpc-endpoint-services \
    --query 'ServiceDetails[].[ServiceName,ServiceType[0].ServiceType,VpcEndpointPolicySupported,PrivateDnsName || `-`]' \
    --output text
if [ "$RUN_STATUS" -ne 0 ]; then
  logerr "$CATALOG_PROFILE" "ec2 describe-vpc-endpoint-services" "$RUN_ERR"
else
  printf '%s\n' "$RUN_OUT" | sed '/^$/d' | sort >"$CATALOG"
fi

# Does this service support an endpoint policy? Empty answer means "not in the catalog",
# which EG-1 treats as supported rather than silently skipping (fail-open to visibility).
pol_supported() { awk -F'\t' -v s="$1" '$1==s {print $3; exit}' "$CATALOG"; }

# ------------------------------------------------------------------------------- checks

# Is this endpoint's VPC the Account Factory vend artifact (172.31.0.0/16)? Those VPCs
# and their endpoints predate Stage 3, are flagged by networking.sh NT-1, and must not
# read as Stage 3's own step 9 failing.
af_endpoint() { # af_endpoint <profile> <vpc-id>  -> prints yes if the VPC is in 172.31/16
  awk -F'\t' -v v="$2" '$1==v && $2 ~ /^172\.31\./ {print "yes"; exit}' "$TMP/vpcs-$1.tsv" 2>/dev/null
}

# EG-1: every endpoint whose service supports a policy carries one naming the organization
# (9.1) - binding to the CONDITION KEYS, not to a Sid, because the statement's name is the
# author's and the condition is the control (Lesson 23).
while IFS=$'\t' read -r p ep svc type vpc orgkeys; do
  [ -n "${p:-}" ] || continue
  if [ -n "$(af_endpoint "$p" "$vpc")" ]; then
    check note "EG-1" "org condition on $ep ($(short_svc "$svc"), $p)" \
      "policy is ${orgkeys}-org - but this endpoint sits in the Account Factory VPC ($vpc), a vend artifact that predates Stage 3 (networking.sh NT-1). Its fate is that VPC's delete-or-keep decision, not a step 9 failure."
    continue
  fi
  sup=$(pol_supported "$svc")
  if [ "$sup" = "False" ]; then
    check note "EG-1" "org condition on $ep ($(short_svc "$svc"), $p)" \
      "this service does not support endpoint policies (catalog, section 7) - the default full-access document cannot be replaced, so the perimeter for it rests on the other two axes."
  elif [ "$orgkeys" = "yes" ]; then
    check pass "EG-1" "org condition on $ep ($(short_svc "$svc"), $p)" "aws:PrincipalOrgID/aws:ResourceOrgID present"
  else
    check fail "EG-1" "org condition on $ep ($(short_svc "$svc"), $p)" \
      "policy names NEITHER aws:PrincipalOrgID NOR aws:ResourceOrgID - without it this endpoint is a private, unlogged path to ANY ${type} destination on the internet (step 9.1)."
  fi
done <"$EPPOL"

# EG-2: one AZ per interface endpoint (D9) - two subnets doubles the largest hourly item.
while IFS=$'\t' read -r p ep svc state nsub azids privdns; do
  [ -n "${p:-}" ] || continue
  if [ "$nsub" -le 1 ]; then
    check pass "EG-2" "single AZ on $ep ($(short_svc "$svc"), $p)" "subnets=$nsub az=$azids"
  else
    check fail "EG-2" "single AZ on $ep ($(short_svc "$svc"), $p)" \
      "$nsub subnets ($azids) - D9 says one AZ per endpoint; the second doubles the hourly cost and a resource in the other AZ still resolves and reaches it."
  fi
done <"$IFEPS"

# EG-3: private DNS on every interface endpoint (8.5) - without it the SDK keeps resolving
# the public name and the endpoint sits unused.
while IFS=$'\t' read -r p ep svc state nsub azids privdns; do
  [ -n "${p:-}" ] || continue
  if [ "$privdns" = "True" ]; then
    check pass "EG-3" "private DNS on $ep ($(short_svc "$svc"), $p)" "enabled"
  else
    check fail "EG-3" "private DNS on $ep ($(short_svc "$svc"), $p)" \
      "PrivateDnsEnabled=$privdns - step 8.5 wants it on (which itself needs step 4.1's VPC attributes); off, clients resolve the public name and the endpoint answers nothing."
  fi
done <"$IFEPS"

# EG-4: the S3 GATEWAY policy carries the AWS-owned-bucket allow (9.3). PRESENCE only -
# whether the list is COMPLETE is the stage's dnf probe, not a grep. Account Factory
# endpoints are EG-1's note, not this check's subject.
while IFS=$'\t' read -r p ep svc type vpc orgkeys; do
  [ -n "${p:-}" ] || continue
  [ "$type" = "Gateway" ] || continue
  case "$svc" in *".s3") ;; *) continue ;; esac
  [ -n "$(af_endpoint "$p" "$vpc")" ] && continue
  pol="$TMP/pol-$p-$ep.json"
  [ -s "$pol" ] || continue
  hits=""
  grep -q 'al2023-repos' "$pol" && hits="${hits}al2023 "
  grep -Eqi 'sagemaker' "$pol" && hits="${hits}sagemaker "
  grep -Eqi '(amazon-ssm|aws-ssm|ssm-agent)' "$pol" && hits="${hits}ssm "
  grep -Eqi 'amazoncloudwatch-agent' "$pol" && hits="${hits}cloudwatch-agent "
  if printf '%s' "$hits" | grep -q 'al2023'; then
    check pass "EG-4" "AWS-owned bucket allow on $ep ($p)" \
      "statement present; bucket classes matched: ${hits}(completeness is the stage's dnf probe, not this grep)"
  else
    check fail "EG-4" "AWS-owned bucket allow on $ep ($p)" \
      "no al2023-repos allow in the S3 gateway policy - aws:ResourceOrgID denies AWS's own buckets, so dnf and every package install HANGS rather than erroring (step 9.3, 9.4). Classes matched so far: ${hits:-none}"
  fi
done <"$EPPOL"

# EG-5 (never a failure): the burn meter.
TOTAL_IFEP=$(awk -F'\t' '$4=="available"' "$IFEPS" | wc -l | tr -d ' ')
TOTAL_NAT=$(awk -F'\t' '$3=="available" || $3=="pending"' "$NATS" | wc -l | tr -d ' ')
TOTAL_HOURLY=$(awk -v e="$TOTAL_IFEP" -v n="$TOTAL_NAT" -v re="$RATE_IFEP" -v rn="$RATE_NAT" \
                 'BEGIN { printf "%.3f", e*re + n*rn }')
if [ "$TOTAL_IFEP" -eq 0 ] && [ "$TOTAL_NAT" -eq 0 ]; then
  check note "EG-5" "metered egress alive" \
    "none - the correct between-sessions state (D11), and the expected one before Stage 3 pass 3."
else
  check note "EG-5" "metered egress alive" \
    "$TOTAL_IFEP interface endpoint(s) + $TOTAL_NAT NAT(s) = ~USD $TOTAL_HOURLY/h ($(awk -v h="$TOTAL_HOURLY" 'BEGIN { printf "%.2f", h*24 }')/day). If no session is running, this is the forgotten-egress risk - no budget alert exists to catch it (D12)."
fi

# --------------------------------------------------------------------------- the report

main() {

printf '================================================================================\n'
printf 'Egress - the [E] networking half, per account, side by side\n'
printf '================================================================================\n'
printf 'generated : %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'profiles  : %s\n' "$PROFILE_SOURCE"
printf 'region    : %s\n' "$REGION"
printf 'produced  : aws/egress.sh   (index: aws/INDEX.md)\n'
printf '\n'
printf 'SECTIONS\n'
printf '  1. Which accounts were measured, and as whom\n'
printf '  2. Interface endpoints, per account\n'
printf '  3. NAT gateways and elastic IPs\n'
printf '  4. Endpoint policies - the trusted-networks axis (step 9)\n'
printf '  5. The endpoint matrix - service x account (step 8)\n'
printf '  6. The burn meter - what metered egress costs right now (the D12 instrument)\n'
printf '  7. The service-name catalog - verification (i), policy support\n'
printf '  8. CHECKS\n'
printf '  9. The accounts nothing here is measuring\n'
printf '  10. Calls that failed\n'
printf '\n'
printf 'HOW TO READ THIS FILE\n'
printf '  - EVERYTHING HERE IS [E]: new IDs on every make up, and nothing may anchor on\n'
printf '    them (Lesson 3, step 8.6). The [P] IDs a policy may name are networking.sh\n'
printf '    section 5. An EMPTY report between sessions is the system working (D11).\n'
printf '  - THE CHECKS PROVE PRESENCE, NOT SUFFICIENCY. EG-4 sees that the 9.3 allow-list\n'
printf '    EXISTS; only the stage`s no-NAT dnf probe shows it is COMPLETE. Both halves\n'
printf '    matter and neither substitutes (deliverables, Lesson 13).\n'
printf '  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT - section 9, Staging above all.\n'
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
h1 "2. Interface endpoints, per account"

if [ -s "$IFEPS" ]; then
  {
    printf 'PROFILE\tENDPOINT\tSERVICE\tSTATE\tSUBNETS\tAZ IDS\tPRIV DNS\n'
    sort "$IFEPS" | while IFS=$'\t' read -r p ep svc state nsub azids privdns; do
      printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$p" "$ep" "$(short_svc "$svc")" "$state" "$nsub" "$azids" "$privdns"
    done
  } | tabulate
  printf '\n'
  printf 'SUBNETS should read 1 everywhere (D9, check EG-2) and the AZ IDS column says which\n'
  printf 'datacenter; PRIV DNS should read True (8.5, check EG-3).\n'
else
  printf 'NONE IN ANY MEASURED ACCOUNT - the correct answer between sessions (D11) and\n'
  printf 'before Stage 3 pass 3. The report is then worth its sections 6 and 7.\n'
fi

# ======================================================================================
h1 "3. NAT gateways and elastic IPs"

printf 'A NAT exists only under design A (step 7.2) and only while egress/ is up. The\n'
printf 'elastic-address listing is informational: Stage 4 parks the WireGuard EIP as [P],\n'
printf 'and an address associated with nothing still bills.\n\n'

if [ -s "$NATS" ]; then
  {
    printf 'PROFILE\tNAT\tSTATE\tSUBNET\n'
    sort "$NATS"
  } | tabulate
else
  printf '(no NAT gateway in any measured account)\n'
fi

printf '\nElastic addresses:\n\n'
while IFS= read -r p; do
  [ -n "$p" ] || continue
  h2 "$p"
  show "$p" ec2 describe-addresses \
      --query 'Addresses[].[AllocationId,PublicIp,AssociationId || `(NOT ASSOCIATED - still billing)`]' \
      --output table
done <"$LIVE"

# ======================================================================================
h1 "4. Endpoint policies - the trusted-networks axis (step 9)"

printf 'One row per endpoint, BOTH types: does its policy name the organization? Check EG-1\n'
printf 'reads this table. The S3 GATEWAY policy - the single most consequential policy in\n'
printf 'the stage (step 3.4) - is printed in full below it, because its allow-list is the\n'
printf 'statement most likely to be trimmed by somebody tidying up (step 9.5).\n\n'

if [ -s "$EPPOL" ]; then
  {
    printf 'PROFILE\tENDPOINT\tSERVICE\tTYPE\tVPC\tORG CONDITION\n'
    sort "$EPPOL" | while IFS=$'\t' read -r p ep svc type vpc orgkeys; do
      printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$p" "$ep" "$(short_svc "$svc")" "$type" "$vpc" "$orgkeys"
    done
  } | tabulate
  printf '\nThe S3 gateway endpoint policies, in full:\n'
  while IFS=$'\t' read -r p ep svc type vpc orgkeys; do
    [ -n "${p:-}" ] || continue
    [ "$type" = "Gateway" ] || continue
    case "$svc" in *".s3") ;; *) continue ;; esac
    h2 "$ep ($p)"
    if [ -s "$TMP/pol-$p-$ep.json" ]; then cat "$TMP/pol-$p-$ep.json"; printf '\n'; else printf '(policy not readable - see section 10)\n'; fi
  done <"$EPPOL"
else
  printf '(no endpoint in any measured account - expected before Stage 3 step 3)\n'
fi

# ======================================================================================
h1 "5. The endpoint matrix - service x account (step 8)"

printf 'Step 8`s list is deliberately per account role - the common core of 8.2 plus the\n'
printf 'per-role adds of 8.3 - and it is a MODULE VARIABLE, so this matrix is read against\n'
printf 'the stage file rather than against a copy here (a list maintained in two places is\n'
printf 'Lesson 14). A row present where the plan says absent is an hourly charge nobody\n'
printf 'chose; a row absent where the plan says present is, under design B, a data plane\n'
printf 'that cannot execute a single query (8.2).\n\n'

if [ -s "$IFEPS" ]; then
  SVCS=$(cut -f3 "$IFEPS" | sort -u)
  {
    printf 'SERVICE'
    while IFS= read -r p; do [ -n "$p" ] && printf '\t%s' "$p"; done <"$LIVE"
    printf '\n'
    while IFS= read -r s; do
      [ -n "$s" ] || continue
      printf '%s' "$(short_svc "$s")"
      while IFS= read -r p; do
        [ -n "$p" ] || continue
        if awk -F'\t' -v p="$p" -v s="$s" '$1==p && $3==s {found=1} END {exit !found}' "$IFEPS"; then
          printf '\tx'
        else
          printf '\t-'
        fi
      done <"$LIVE"
      printf '\n'
    done <<SVCS
$SVCS
SVCS
  } | tabulate
else
  printf '(nothing to tabulate)\n'
fi

# ======================================================================================
h1 "6. The burn meter - what metered egress costs right now"

printf 'THE ONE SECTION TO READ AT THE END OF A SESSION. A forgotten egress/ costs ~USD\n'
printf '4.08/day at the Sandbox list, and BY DECISION no budget alert exists to catch it\n'
printf '(D12) - this reading is the instrument that risk gets. Rates: interface endpoint\n'
printf 'USD %s/h, NAT (with its IPv4) USD %s/h; data-processing charges are on top and\n' "$RATE_IFEP" "$RATE_NAT"
printf 'not visible here.\n\n'

{
  printf 'PROFILE\tIF ENDPOINTS\tNATs\tUSD/HOUR\n'
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    ne=$(awk -F'\t' -v p="$p" '$1==p && $4=="available"' "$IFEPS" | wc -l | tr -d ' ')
    nn=$(awk -F'\t' -v p="$p" '$1==p && ($3=="available" || $3=="pending")' "$NATS" | wc -l | tr -d ' ')
    printf '%s\t%s\t%s\t%s\n' "$p" "$ne" "$nn" \
      "$(awk -v e="$ne" -v n="$nn" -v re="$RATE_IFEP" -v rn="$RATE_NAT" 'BEGIN { printf "%.3f", e*re + n*rn }')"
  done <"$LIVE"
  printf 'TOTAL\t%s\t%s\t%s\n' "$TOTAL_IFEP" "$TOTAL_NAT" "$TOTAL_HOURLY"
} | tabulate

printf '\nZero everywhere is the correct between-sessions answer (D11), not an absence of\n'
printf 'evidence - and the Sandbox row multiplies per business unit (D35).\n'

# ======================================================================================
h1 "7. The service-name catalog - verification (i), policy support"

printf 'Read-only answers to questions the stage would otherwise pay to discover:\n'
printf '  - verification (i): the SageMaker Studio endpoint`s service name - the rows below\n'
printf '    matching "studio" settle whether it is aws.sagemaker.%s.studio.\n' "$REGION"
printf '  - the CodeArtifact pair exists in this region at all (8.4; Lesson 6 caught it\n'
printf '    absent in sa-east-1 - measured, not assumed).\n'
printf '  - POLICY column False = the service cannot carry an endpoint policy, which is why\n'
printf '    EG-1 reports it as a note rather than a failure.\n\n'

if [ -s "$CATALOG" ]; then
  printf 'The rows the stage names (steps 8.2-8.4, 8.7), plus s3/dynamodb:\n\n'
  {
    printf 'SERVICE\tTYPE\tPOLICY\tPRIVATE DNS NAME\n'
    grep -Ei '(sagemaker|codeartifact|datazone|athena|glue|lakeformation|elasticfilesystem|ecr|kms|logs|sts|states|scheduler|ssm|secretsmanager|monitoring|s3|dynamodb)' \
      "$CATALOG"
  } | tabulate
  printf '\nEvery row matching "studio", whatever its prefix (verification (i)):\n\n'
  grep -i 'studio' "$CATALOG" | tabulate
  [ -z "$(grep -i 'studio' "$CATALOG")" ] && printf '(none - the studio endpoint does not exist in this region under any name)\n'
  printf '\nThe full catalog holds %s services; regenerate to re-read it.\n' \
    "$(wc -l <"$CATALOG" | tr -d ' ')"
else
  printf '(the catalog call failed - see section 10)\n'
fi

# ======================================================================================
h1 "8. CHECKS"

if [ ! -s "$IFEPS" ] && [ ! -s "$EPPOL" ]; then
  printf 'NO ENDPOINT WAS MEASURED, so EG-1 through EG-4 are vacuous rather than passing\n'
  printf '(Lesson 13). Between sessions and before Stage 3 pass 3 that is the expected\n'
  printf 'state; EG-5 below is the reading that still means something.\n\n'
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
printf '  EG-1  every endpoint policy names the organization (step 9.1); services that\n'
printf '        cannot carry a policy are notes, per the catalog\n'
printf '  EG-2  one AZ per interface endpoint (D9)\n'
printf '  EG-3  private DNS enabled per interface endpoint (step 8.5)\n'
printf '  EG-4  the S3 gateway policy carries the al2023 allow (step 9.3) - presence only\n'
printf '  EG-5  the burn meter (always a note, never a failure)\n'

# ======================================================================================
h1 "9. The accounts nothing here is measuring"

printf 'Read this BEFORE reading section 8 as a pass.\n\n'
printf '  - `Staging` has no profile because the account is UNVENDED, held on the account\n'
printf '    cap (Stage 1a). Its endpoint list (8.3: no sagemaker.studio, NO lakeformation)\n'
printf '    is unmeasurable until the vend.\n'
printf '  - Management, Log Archive and Audit hold NO CLI profile, by design (D33/D34),\n'
printf '    and none of them gets an egress/ slice.\n'
printf '  - Every Sandbox beyond the first has no profile until Stage 14 vends it (D35).\n'
printf '  - Data Governance IS measured and should show NOTHING here: no VPC (D22), so no\n'
printf '    endpoint and no NAT - its consumers bring their own endpoints.\n'

# ======================================================================================
h1 "10. Calls that failed"

if [ -s "$ERRORS" ]; then
  printf 'Each entry is a call whose output is missing above. An empty block anywhere else\n'
  printf 'in this file means the call succeeded and returned nothing.\n\n'
  cat "$ERRORS"
else
  printf 'None. Every call returned successfully.\n'
fi

printf '\nRegenerate with:  ./aws/egress.sh\n'

}

# ---------------------------------------------------------------------------------- run

main >"$OUT"

NFAIL=$(awk -F'\t' '$1=="fail"' "$CHECKS" | wc -l | tr -d ' ')
note ""
if [ -s "$ERRORS" ]; then
  note "wrote $OUT (some calls FAILED - see section 10)"
  exit 1
fi
if [ "$NFAIL" -gt 0 ]; then
  note "wrote $OUT ($NFAIL CHECK(S) FAILED - see section 8)"
  exit 2
fi
note "wrote $OUT (all checks passed - and read EG-5, the burn meter)"
exit 0
