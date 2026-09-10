# Route 53 Resolver DNS Firewall - design A's control, and what makes "limited internet"
# different from "internet" (Stage 6 step 4.1, D5(A), architecture.md 4.3).
#
# A private subnet used to have a default route to a NAT gateway, and a NAT is not a filter:
# anything in the subnet can reach any address on the internet. The endpoint policies do not see
# that traffic (it is not going to an endpoint), the bucket policies do not see it (it is not
# going to S3), and the flow logs record it after the fact. DNS Firewall acts before the
# connection: a name that does not resolve is a host nobody reaches.
#
# Name filtering is bypassable by raw IP (step 6.1). A process that already knows an address
# never asks the resolver, so design A's exfiltration story is "inconvenient" and design B's is
# "there is no path" - the difference D5 exists to price.
#
# Cost: ~USD 0.03/month for the domain lists plus USD 0.60 per million queries (measured,
# docs/PRICING.md 7). It is in this module rather than in foundation/ because it only means
# anything while there is a default route, and that route is [E].
#
# The query log is [E] with the rest of the slice: `make down` destroys the log group and the
# blocked-lookup evidence with it. Read 4.3's findings during the session, not after it.

locals {
  # The firewall is on where the caller says so, and nowhere else. This condition once carried a
  # second clause, `&& var.egress_mode == "A"`, so one condition served two intents (Lesson 51):
  # *the firewall only matters where a default route exists* and *the firewall is on*. The first
  # is false under design B - the firewall's job stopped being *filter the internet* the moment
  # the internet became the proxy's allow-list. What it does here is close the recursive resolver
  # as an exfiltration channel, and that channel exists with or without a default route (6c step
  # 5.1; step 5.7 is what says the firewall must stay).
  dns_firewall_enabled = var.dns_firewall

  # An empty allow-list is a valid configuration and this module's default, so the allow half
  # is gated on the list having content rather than on the firewall being on. With no names, no
  # ALLOW rule is created at all and the catch-all below is the only rule in the group: every
  # lookup in the VPC returns NXDOMAIN, so a caller who forgets the list gets a closed door.
  # Built this way rather than by passing `domains = []`, because a domain list with no entries
  # is not something to rely on the API accepting.
  dns_firewall_allow_enabled = local.dns_firewall_enabled && length(var.dns_firewall_allow_domains) > 0
}

# The allow-list. The names are not here and not in variables.tf: the default is empty and every
# caller declares its own set. What each entry has to satisfy is below, because it is the part
# that cannot be inferred from a hostname.
#
# How an entry is matched. A domain list entry matches the name exactly; `*.name` matches every
# nesting level beneath it (`*.example.com` matches `a.b.example.com`) and never the apex, so a
# wildcard entry and its bare name are two different entries. The `*` must replace a whole
# leftmost label: `*prod.example.com` is rejected. A wildcard never crosses into a sibling
# registrable domain.
#
# DNS Firewall evaluates the whole resolution chain, not the queried name (measured 2026-08-23,
# Stage 6 step 4.3). If a listed name is a CNAME to a target that is not also listed, the lookup
# is blocked - and the log reports the block against the original name with the catch-all list
# id, which reads exactly like "that name was not on the allow-list" and is not. The proof is a
# pair measured under the same wildcard shape: `blobs.duckdb.org` (A records) resolved while
# `index.crates.io` (CNAME to Fastly) did not.
#
# The consequence was read for a day as design A's ceiling: every package ecosystem serves its
# artifacts from a shared CDN, so an allow-list could carry every index and still have no
# download path, and the only apparent repair was to allow `*.fastly.net`, `*.cloudfront.net`,
# `*.cdn.cloudflare.net` and friends - self-service namespaces anyone can publish into, so
# allowing them ends this control.
#
# That ceiling was the default, not the mechanism. `firewall_domain_redirection_action` on the
# ALLOW rule below is a per-rule setting with two values, and this module had never set it, so
# it took the API default:
#
#   INSPECT_REDIRECTION_DOMAIN   the default - evaluate every domain in the chain
#   TRUST_REDIRECTION_DOMAIN     evaluate the first domain only, trust the rest of the chain
#
# It is an input, and the module's default stays INSPECT: the caller decides, in the slice where
# that account's reach is decided, exactly as it decides the list itself. What the second value
# buys is what an allow-list of hostnames means to the person writing it:
# `julialang-s3.julialang.org` is listed, its CNAME into Fastly is not, and does not need to be.
# Everything below describes the TRUST reading, because that is what both Interactive slices
# pass; under the default the whole-chain rule above still governs.
#
# TRUST is not "allowing the CDN": it holds inside one query transaction. A process that queries
# the redirection target itself - `dualstack.j2.shared.global.fastly.net` - is evaluated as an
# independent query with no trust carried over, matches nothing on the allow-list, falls to the
# catch-all below and is blocked. So the estate gains the artifact hosts without gaining the
# namespace they sit in.
#
# What a caller trades for it: the control then rests entirely on who owns the listed name. If
# the authoritative side of a listed name is hostile or compromised, it can point the chain
# anywhere and the firewall will follow. That was already true of an A record - a listed name
# could always answer with any address - so the delta is narrow, but it is a delta.
#
# What this does not repair: the two bypasses of a name-based control are untouched. A process
# that already knows an address never asks the resolver, and a process that asks a resolver other
# than the VPC's - `1.1.1.1:53` over the NAT, or DoH on 443 - is not inspected here at all,
# because this firewall only sees what the VPC resolver answers. Both need an L7 control
# (SNI/Host) to close, which is Network Firewall or a proxy, and neither is built. Design A
# remains a control against accident.
#
# The list rule for a caller that passes TRUST: list the name your tools query, and never a
# redirection target. A hop on such a list is not merely redundant - it is a widening, because it
# is what makes the CDN name resolvable on its own. A caller left on the default keeps the older
# rule, where every hop has to be listed and the whole chain is the unit.
resource "aws_route53_resolver_firewall_domain_list" "allow" {
  count = local.dns_firewall_allow_enabled ? 1 : 0

  name    = "${local.name_prefix}-egress-allow"
  domains = var.dns_firewall_allow_domains

  tags = { Name = "${local.name_prefix}-egress-allow" }

  # Every interface endpoint this VPC pays for must be resolvable in it (6c step 5.7). The list
  # is computed in no-proxy.tf from the same reading NO_PROXY is built from, and the argument is
  # there: a shrinking allow-list is how a paid endpoint becomes an NXDOMAIN, and NXDOMAIN reads
  # as a network fault rather than as a policy decision.
  #
  # Two preconditions, because the two readings answer at different times and only one can be
  # trusted to answer early. `declared` reads the service's canonical name from a data source and
  # therefore fails in the plan of a VPC that does not exist yet; `served` reads every name the
  # endpoints answer for and is (known after apply) until they do. Keeping only the second would
  # put the whole guard behind an apply on every new spoke (Lesson 39, measured on staging/egress
  # 2026-09-09). Each message names its reading, so a failure says which half found it and
  # whether a plan or an apply was the earliest it could have been found.
  lifecycle {
    precondition {
      condition     = length(local.dns_firewall_uncovered["declared"]) == 0
      error_message = "dns_firewall_allow_domains does not cover ${join(", ", local.dns_firewall_uncovered["declared"])} - this VPC DECLARES an interface endpoint whose canonical private DNS name the firewall would block. Add the family, or drop the endpoint. (declared reading: the service's own name, checked at plan time.)"
    }

    precondition {
      condition     = length(local.dns_firewall_uncovered["served"]) == 0
      error_message = "dns_firewall_allow_domains does not cover ${join(", ", local.dns_firewall_uncovered["served"])} - an interface endpoint in this VPC ANSWERS for that name and the firewall would block it. Add the family, or drop the endpoint. (served reading: aws_vpc_endpoint.dns_entry, so this one can only be checked once the endpoints exist.)"
    }
  }
}

# The catch-all. `*` matches every name, which is what turns the rule group into a default-deny
# instead of a list of blocked sites (Lesson 5: an allow-list that is not the last word is a
# suggestion).
#
# `"*."` rather than `"*"`: the trailing dot is the whole of `EXC-04`'s repair (6c step 5.7,
# 2026-09-06). Route 53 Resolver canonicalises every domain-list entry as an FQDN -
# `list-firewall-domains` returns `pypi.org.`, `*.amazonaws.com.` and, for this list, `*.` -
# while this module wrote them without one. The provider was comparing two spellings of the same
# list, re-issued `UpdateFirewallDomains` on every apply, and the diff never converged:
# `terraform plan` read `0 to add, 2 to change` immediately after a successful apply of the same
# code, forever. That cost this repository's closing check for every change - *"re-plan reads `No
# changes`"* - on the two slices that carry a firewall.
#
# Measured on a live Sandbox list before the fix was written: with the caller's ten entries
# dotted and this one still bare, the plan went from `2 to change` to `1 to change` - the allow
# list settled and this one did not.
resource "aws_route53_resolver_firewall_domain_list" "everything" {
  count = local.dns_firewall_enabled ? 1 : 0

  name    = "${local.name_prefix}-egress-everything"
  domains = ["*."]

  tags = { Name = "${local.name_prefix}-egress-everything" }
}

resource "aws_route53_resolver_firewall_rule_group" "this" {
  count = local.dns_firewall_enabled ? 1 : 0

  name = "${local.name_prefix}-egress"

  tags = { Name = "${local.name_prefix}-egress" }
}

# Priority is evaluation order, ascending: the allow-list is consulted first and the catch-all
# only sees what it did not match. Reverse them and every lookup is blocked, including the ones
# on the list.
#
# With no names this rule does not exist and the group holds the catch-all alone - the
# closed-door default described on `dns_firewall_allow_enabled` above.
resource "aws_route53_resolver_firewall_rule" "allow" {
  count = local.dns_firewall_allow_enabled ? 1 : 0

  name                    = "allow-listed-names"
  action                  = "ALLOW"
  firewall_domain_list_id = aws_route53_resolver_firewall_domain_list.allow[0].id
  firewall_rule_group_id  = aws_route53_resolver_firewall_rule_group.this[0].id
  priority                = 100

  # The header's argument, in one field, and the value is the caller's (variables.tf). The
  # module defaults to INSPECT_REDIRECTION_DOMAIN, the API's own default and the stricter
  # reading; both Interactive slices pass TRUST_REDIRECTION_DOMAIN. It goes on this rule and not
  # on the catch-all below: `*` matches at the first domain of every query, so the block rule
  # never has a chain left to inspect, and giving it a redirection setting would describe a path
  # evaluation cannot take.
  firewall_domain_redirection_action = var.firewall_domain_redirection_action
}

# NXDOMAIN rather than NODATA, for the failure mode a person sees: a blocked package install
# should look like "no such host", which every tool reports clearly, rather than like an empty
# answer, which several retry against for a minute first.
resource "aws_route53_resolver_firewall_rule" "block_everything_else" {
  count = local.dns_firewall_enabled ? 1 : 0

  name                    = "block-everything-else"
  action                  = "BLOCK"
  block_response          = "NXDOMAIN"
  firewall_domain_list_id = aws_route53_resolver_firewall_domain_list.everything[0].id
  firewall_rule_group_id  = aws_route53_resolver_firewall_rule_group.this[0].id
  priority                = 200
}

resource "aws_route53_resolver_firewall_rule_group_association" "this" {
  count = local.dns_firewall_enabled ? 1 : 0

  name                   = "${local.name_prefix}-egress"
  firewall_rule_group_id = aws_route53_resolver_firewall_rule_group.this[0].id
  vpc_id                 = var.vpc_id
  priority               = 101

  tags = { Name = "${local.name_prefix}-egress" }
}

# ----------------------------------------------------------------- the block, made readable
#
# A block nobody can see is indistinguishable from a network fault (Lesson 13): the person whose
# `pip install` failed needs to tell "the firewall refused this name" from "the NAT is down".
# Resolver query logging is what writes the rule action beside the name.

resource "aws_cloudwatch_log_group" "dns_firewall" {
  # checkov:skip=CKV_AWS_158:default (AWS-managed) encryption - the same call Stage 3 made for the flow logs; this group holds DNS names, and it is [E]
  # checkov:skip=CKV_AWS_338:retention is 30 days, matching Stage 3 decision 3 - a session debugging log, not an audit trail, and the group is [E] anyway
  count = local.dns_firewall_enabled ? 1 : 0

  name              = "/awsds/${var.env}/dns-firewall"
  retention_in_days = 30
}

resource "aws_route53_resolver_query_log_config" "this" {
  count = local.dns_firewall_enabled ? 1 : 0

  name            = "${local.name_prefix}-egress"
  destination_arn = aws_cloudwatch_log_group.dns_firewall[0].arn

  tags = { Name = "${local.name_prefix}-egress" }
}

resource "aws_route53_resolver_query_log_config_association" "this" {
  count = local.dns_firewall_enabled ? 1 : 0

  resolver_query_log_config_id = aws_route53_resolver_query_log_config.this[0].id
  resource_id                  = var.vpc_id
}
