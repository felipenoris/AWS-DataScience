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

  # THE TRAILING DOT IS THE API'S, AND PUTTING IT BACK HERE IS WHAT MAKES THE PLAN CONVERGE
  # (measured 2026-08-22 on sandbox/egress, provider 6.60.0). Route 53 Resolver canonicalises
  # every entry to the fully-qualified form on the way in: `list-firewall-domains` answers
  # "pypi.org.", "*.amazonaws.com." and - for the catch-all - "*.". The provider stores that
  # answer in state verbatim and compares it to the config as plain strings, so an undotted
  # config never matches its own refreshed state: `Plan: 0 to add, 2 to change` on a re-plan
  # taken immediately after a clean apply, forever, issuing an UpdateFirewallDomains that
  # changes nothing.
  #
  # THAT IS NOT COSMETIC HERE. This repository's closing check for every change is "re-plan
  # reads No changes" (the runbook, Recipe A step 7) - a perpetual diff does not just fail
  # that check, it removes the instrument, because a reader watching all 38 names churn
  # cannot tell a real edit from the noise.
  #
  # THE FIX IS ON US, NOT ON THE PROVIDER: hashicorp/terraform-provider-aws#23543 is the same
  # finding, opened 2022 and closed 2025 as not planned (REFERENCES.md). The one useful
  # comment on it is the reason this normalises rather than stripping - stripping the dot on
  # READ would flip the diff onto anyone who writes fully-qualified names, so the canonical
  # form is the one to converge on.
  #
  # WHY THIS IS AN EXPRESSION AND NOT 38 DOTS IN variables.tf (Lesson 14): a dot that must be
  # typed by hand in N places will be missing from one of them, and the entry it is missing
  # from is a name that silently churns. Written once here, the rule reaches every entry -
  # including whatever a later sitting adds, in either form.
  dns_firewall_allow_domains = [for d in var.dns_firewall_allow_domains : endswith(d, ".") ? d : "${d}."]
  dns_firewall_block_domains = [for d in ["*"] : endswith(d, ".") ? d : "${d}."]
}

# The allow-list. A domain list entry matches the name EXACTLY; `*.name` matches its
# subdomains - so nearly everything below is written twice, and an entry appearing only once
# is a bug rather than a shorthand.
#
# THE WILDCARD COVERS DEPTH, AND THAT HALF IS MEASURED RATHER THAN ASSUMED (re-read
# 2026-08-22, REFERENCES.md): `*.name` matches EVERY nesting level beneath it -
# `*.julialang.org` matches `us-west.pkg.julialang.org` - and never the apex, which is why the
# bare name sits beside it. The `*` must replace a whole leftmost label: `*prod.example.com`
# is rejected. What a wildcard does NOT cross is a sibling registrable domain, and the list
# in variables.tf carries the case that caught it.
resource "aws_route53_resolver_firewall_domain_list" "allow" {
  count = local.dns_firewall_enabled ? 1 : 0

  name    = "awsds-${var.env}-egress-allow"
  domains = local.dns_firewall_allow_domains

  tags = { Name = "awsds-${var.env}-egress-allow" }
}

# The catch-all. `*` matches every name, which is what turns the rule group into a
# default-deny instead of a list of blocked sites (Lesson 5: an allow-list that is not the
# LAST word is a suggestion). It is authored `*` and SENT `*.` - the locals block above.
#
# THIS IS THE ONE ENTRY WHOSE CANONICAL FORM THE API MODEL DOES NOT VOUCH FOR, and the
# asymmetry is worth stating rather than discovering. `FirewallDomainName` carries a regex
# (botocore, route53resolver 2018-04-01) whose wildcard branch is `\*(\.label)+(\.)?` - it
# requires at least one label after the asterisk, so it admits `*.pypi.org.` and admits
# NEITHER `*` nor `*.`. The bare `*` has nevertheless been deployed and read back since
# Stage 3, which means the SERVER is more permissive than its own model and the model
# therefore settles nothing here in either direction. What is measured is that the API
# EMITS `*.`; what is inferred is that it accepts it.
#
# WHERE THAT INFERENCE GETS TESTED is the next `make up`, not the next plan: while the list
# already exists carrying `*.`, a converged plan sends nothing at all, so the create path
# stays unexercised until the slice is rebuilt. If `*.` were refused there, this resource
# fails and the failure is loud - but read the association below before assuming it is also
# safe.
resource "aws_route53_resolver_firewall_domain_list" "everything" {
  count = local.dns_firewall_enabled ? 1 : 0

  name    = "awsds-${var.env}-egress-everything"
  domains = local.dns_firewall_block_domains

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
resource "aws_route53_resolver_firewall_rule" "allow" {
  count = local.dns_firewall_enabled ? 1 : 0

  name                    = "allow-listed-names"
  action                  = "ALLOW"
  firewall_domain_list_id = aws_route53_resolver_firewall_domain_list.allow[0].id
  firewall_rule_group_id  = aws_route53_resolver_firewall_rule_group.this[0].id
  priority                = 100
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

# THE ASSOCIATION IS WHAT ARMS THE GROUP, AND IT IS ORDERED AFTER BOTH RULES ON PURPOSE.
# Nothing in the attributes below refers to a rule, so the graph is free to build this while
# a rule is still failing - and a rule group carrying the ALLOW rule alone is not a weaker
# default-deny, it is NO default-deny: a name matching no rule resolves normally. That is the
# fail-OPEN direction, reached by a partial apply, which is precisely the shape Lesson 5
# warns about and the shape nothing here would announce. `depends_on` costs one graph edge
# and makes the same partial apply fail CLOSED instead - the association simply does not
# appear, and `./aws/egress.py` and a re-plan both say so.
#
# The ALLOW rule is in the list for the same reason read the other way: associating before it
# exists blocks every name on the allow-list for as long as the gap lasts. Transient, and the
# safe direction, but there is no reason to author it.
resource "aws_route53_resolver_firewall_rule_group_association" "this" {
  count = local.dns_firewall_enabled ? 1 : 0

  name                   = "awsds-${var.env}-egress"
  firewall_rule_group_id = aws_route53_resolver_firewall_rule_group.this[0].id
  vpc_id                 = var.vpc_id
  priority               = 101

  depends_on = [
    aws_route53_resolver_firewall_rule.allow,
    aws_route53_resolver_firewall_rule.block_everything_else,
  ]

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
