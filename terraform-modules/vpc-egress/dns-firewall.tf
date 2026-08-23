# ROUTE 53 RESOLVER DNS FIREWALL - design A's control, and the thing that makes "limited
# internet" different from "internet" (Stage 6 step 4.1, D5(A), architecture.md 4.3).
#
# WHAT IT IS FOR. Under egress_mode = "A" a private subnet has a default route to a NAT
# gateway, and a NAT is not a filter: anything in the subnet can reach any address on the
# internet. The endpoint policies do not see that traffic (it is not going to an endpoint),
# the bucket policies do not see it (it is not going to S3), and the flow logs record it after
# the fact. DNS Firewall is the one cheap lever that acts BEFORE the connection: a name that
# does not resolve is a host nobody reaches.
#
# WHAT IT IS NOT, AND THIS BELONGS IN THE COMPARISON RATHER THAN IN A FOOTNOTE (step 6.1):
# name filtering is bypassable by RAW IP. A process that already knows an address never asks
# the resolver. So design A's exfiltration story is "inconvenient", and design B's is "there
# is no path" - which is the actual difference D5 exists to price.
#
# COST: ~USD 0.03/month for the domain lists plus USD 0.60 per million queries (measured,
# docs/PRICING.md 7). Cents. It is in this module rather than in foundation/ because it only
# means anything while there IS a default route, and that route is [E].
#
# THE QUERY LOG IS [E] WITH THE REST OF THE SLICE, which has one consequence worth stating:
# `make down` destroys the log group and the blocked-lookup evidence with it. Read 4.3's
# findings during the session, not after it.

locals {
  dns_firewall_enabled = var.dns_firewall && var.egress_mode == "A"

  # AN EMPTY ALLOW-LIST IS A VALID AND MEANINGFUL CONFIGURATION - it is this module's
  # DEFAULT since v0.3.0 - so the allow half is gated on the list having content rather
  # than on the firewall being on. With no names, no ALLOW rule is created at all and the
  # catch-all below is the only rule in the group: every lookup in the VPC returns
  # NXDOMAIN. That is the intended default (a caller who forgets the list gets a closed
  # door, not an open one), and it is built this way rather than by passing `domains = []`
  # because a domain list with no entries is not something to rely on the API accepting.
  dns_firewall_allow_enabled = local.dns_firewall_enabled && length(var.dns_firewall_allow_domains) > 0
}

# The allow-list. THE NAMES ARE NOT HERE AND ARE NOT IN variables.tf EITHER (v0.3.0): the
# default is EMPTY and every caller declares its own set. What each entry has to satisfy is
# below, because it is the part that cannot be inferred from a hostname.
#
# HOW AN ENTRY IS MATCHED. A domain list entry matches the name EXACTLY; `*.name` matches
# every nesting level beneath it (`*.example.com` matches `a.b.example.com`) and never the
# apex, so a wildcard entry and its bare name are two different entries. The `*` must replace
# a whole leftmost label: `*prod.example.com` is rejected. A wildcard never crosses into a
# sibling registrable domain.
#
# THE RULE THAT USED TO GOVERN WHAT BELONGS ON A LIST, MEASURED 2026-08-23 (Stage 6 step
# 4.3): DNS FIREWALL EVALUATES THE WHOLE RESOLUTION CHAIN, NOT THE QUERIED NAME. If a listed
# name is a CNAME to a target that is not also listed, the lookup is blocked - and the log
# reports the block against the ORIGINAL name with the catch-all list id, which reads exactly
# like "that name was not on the allow-list" and is not. The proof is a pair measured under
# the same wildcard shape: `blobs.duckdb.org` (A records) resolved while `index.crates.io`
# (CNAME to Fastly) did not.
#
# THE CONSEQUENCE WAS NOT SMALL, and for one day it was read as design A's ceiling: every
# package ecosystem serves its ARTIFACTS from a shared CDN, so an allow-list could carry
# every index and still have no download path, and the only apparent repair was to allow
# `*.fastly.net`, `*.cloudfront.net`, `*.cdn.cloudflare.net` and friends - self-service
# namespaces anyone can publish into, so allowing them ends this control.
#
# THAT CEILING WAS THE DEFAULT, NOT THE MECHANISM (v0.4.0). `firewall_domain_redirection_action`
# on the ALLOW rule below is a per-rule setting with two values, and this module had never set
# it, so it took the API default:
#
#   INSPECT_REDIRECTION_DOMAIN   the default - evaluate EVERY domain in the chain
#   TRUST_REDIRECTION_DOMAIN     evaluate the FIRST domain only, trust the rest of the chain
#
# SINCE v0.4.0 IT IS AN INPUT, and the module's default stays INSPECT - the caller decides,
# in the slice where that account's reach is decided, exactly as it decides the list itself.
# What the second value buys is what an allow-list of hostnames means to the person writing
# it: `julialang-s3.julialang.org` is listed, its CNAME into Fastly is not, and does not need
# to be. Everything below describes the TRUST reading, because that is what both Interactive
# slices pass; under the default nothing changed and the paragraph above is still the rule.
#
# AND IT IS NOT "ALLOWING THE CDN", which is the reading to check before trusting this: the
# trust holds inside ONE query transaction. A process that queries the redirection target
# ITSELF - `dualstack.j2.shared.global.fastly.net` - is evaluated as an independent query with
# no trust carried over, matches nothing on the allow-list, falls to the catch-all below and
# is BLOCKED. So the estate gains the artifact hosts without gaining the namespace they sit
# in, which is the whole reason widening the list was never an acceptable repair.
#
# WHAT A CALLER TRADES FOR IT, stated because it is the real cost and it is not zero: the
# control now rests entirely on WHO OWNS THE LISTED NAME. If the authoritative side of a
# listed name is hostile or compromised, it can point the chain anywhere and the firewall
# will follow. That was already true of an A record - a listed name could always answer with
# any address - so the delta is narrower than it first reads, but it is a delta.
#
# WHAT THIS DOES NOT REPAIR, so it is not mistaken for a perimeter: the two bypasses of a
# name-based control are untouched. A process that already knows an ADDRESS never asks the
# resolver, and a process that asks a resolver OTHER than the VPC's - `1.1.1.1:53` over the
# NAT, or DoH on 443 - is not inspected here at all, because this firewall only sees what
# the VPC resolver answers. Both need an L7 control (SNI/Host) to close, which is Network
# Firewall or a proxy, and neither is built. Design A remains a control against ACCIDENT.
#
# THE LIST RULE THAT FOLLOWS FROM ALL OF THIS, for a caller that passes TRUST, and it is
# shorter than the one it replaces: list THE NAME YOUR TOOLS QUERY, and never a redirection
# target. A hop on such a list is not merely redundant - it is a widening, because it is what
# makes the CDN name resolvable on its own. A caller left on the default keeps the old rule,
# where every hop has to be listed and the whole chain is the unit.
resource "aws_route53_resolver_firewall_domain_list" "allow" {
  count = local.dns_firewall_allow_enabled ? 1 : 0

  name    = "awsds-${var.env}-egress-allow"
  domains = var.dns_firewall_allow_domains

  tags = { Name = "awsds-${var.env}-egress-allow" }
}

# The catch-all. `*` matches every name, which is what turns the rule group into a
# default-deny instead of a list of blocked sites (Lesson 5: an allow-list that is not the
# LAST word is a suggestion).
resource "aws_route53_resolver_firewall_domain_list" "everything" {
  count = local.dns_firewall_enabled ? 1 : 0

  name    = "awsds-${var.env}-egress-everything"
  domains = ["*"]

  tags = { Name = "awsds-${var.env}-egress-everything" }
}

resource "aws_route53_resolver_firewall_rule_group" "this" {
  count = local.dns_firewall_enabled ? 1 : 0

  name = "awsds-${var.env}-egress"

  tags = { Name = "awsds-${var.env}-egress" }
}

# PRIORITY IS EVALUATION ORDER, ASCENDING, AND THE TWO NUMBERS ARE THE WHOLE DESIGN: the
# allow-list is consulted first and the catch-all only sees what it did not match. Reverse
# them and every lookup is blocked, including the ones on the list.
#
# WITH NO NAMES THIS RULE DOES NOT EXIST and the group holds the catch-all alone - the
# closed-door default described on `dns_firewall_allow_enabled` above.
resource "aws_route53_resolver_firewall_rule" "allow" {
  count = local.dns_firewall_allow_enabled ? 1 : 0

  name                    = "allow-listed-names"
  action                  = "ALLOW"
  firewall_domain_list_id = aws_route53_resolver_firewall_domain_list.allow[0].id
  firewall_rule_group_id  = aws_route53_resolver_firewall_rule_group.this[0].id
  priority                = 100

  # v0.4.0 - the header's argument, in one field, and the VALUE IS THE CALLER'S (variables.tf).
  # The module defaults to INSPECT_REDIRECTION_DOMAIN, which is the API's own default and the
  # stricter reading; both Interactive slices pass TRUST_REDIRECTION_DOMAIN. It goes on THIS
  # rule and not on the catch-all below, and the asymmetry is not an oversight: `*` matches at
  # the first domain of every query, so the block rule never has a chain left to inspect, and
  # giving it a redirection setting would describe a path evaluation cannot take.
  firewall_domain_redirection_action = var.firewall_domain_redirection_action
}

# NXDOMAIN rather than NODATA, and the choice is about the failure MODE a person sees: a
# blocked package install should look like "no such host", which every tool reports clearly,
# rather than like an empty answer, which several retry against for a minute first.
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

  name                   = "awsds-${var.env}-egress"
  firewall_rule_group_id = aws_route53_resolver_firewall_rule_group.this[0].id
  vpc_id                 = var.vpc_id
  priority               = 101

  tags = { Name = "awsds-${var.env}-egress" }
}

# ----------------------------------------------------------------- the block, made readable
#
# A BLOCK NOBODY CAN SEE IS INDISTINGUISHABLE FROM A NETWORK FAULT (Lesson 13 applied to an
# operator rather than to a check): the person whose `pip install` failed needs to be able to
# tell "the firewall refused this name" from "the NAT is down". Resolver query logging is what
# writes the rule action beside the name.

resource "aws_cloudwatch_log_group" "dns_firewall" {
  # checkov:skip=CKV_AWS_158:default (AWS-managed) encryption - the same call Stage 3 made for the flow logs; this group holds DNS names, and it is [E]
  # checkov:skip=CKV_AWS_338:retention is 30 days, matching Stage 3 decision 3 - a session debugging log, not an audit trail, and the group is [E] anyway
  count = local.dns_firewall_enabled ? 1 : 0

  name              = "/awsds/${var.env}/dns-firewall"
  retention_in_days = 30
}

resource "aws_route53_resolver_query_log_config" "this" {
  count = local.dns_firewall_enabled ? 1 : 0

  name            = "awsds-${var.env}-egress"
  destination_arn = aws_cloudwatch_log_group.dns_firewall[0].arn

  tags = { Name = "awsds-${var.env}-egress" }
}

resource "aws_route53_resolver_query_log_config_association" "this" {
  count = local.dns_firewall_enabled ? 1 : 0

  resolver_query_log_config_id = aws_route53_resolver_query_log_config.this[0].id
  resource_id                  = var.vpc_id
}
