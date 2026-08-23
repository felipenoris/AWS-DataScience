variable "env" {
  description = "The <env> NAME TOKEN (docs/plan/conventions.md) - builds every name here. Not the Environment tag, which the caller's provider default_tags applies."
  type        = string
  nullable    = false
}

variable "vpc_id" {
  description = "The foundation/ VPC - read by the caller through terraform_remote_state, never pasted (Lesson 3)."
  type        = string
  nullable    = false
}

variable "egress_mode" {
  description = "Step 10's switch, PER ACCOUNT (10.3): 'A' builds the NAT and the private tier's default route; 'B' builds neither - no default route at all until Stages 6-7 build B's package path. Default A (Stage 3 decision 4); choosing A as the default is not choosing A as the outcome - D5's comparison happens at Stage 6."
  type        = string
  default     = "A"

  validation {
    condition     = contains(["A", "B"], var.egress_mode)
    error_message = "egress_mode is 'A' (NAT) or 'B' (no default route) - D5's two designs, nothing else."
  }
}

variable "nat_public_subnet_id" {
  description = "The ONE public subnet the NAT lands in (step 7.1) - the caller picks the first authored zone. The documented one-per-AZ switch: make this a map like private_route_table_ids and give aws_route.private_default a per-zone NAT - foundation's route tables are already per AZ so it is a route change, not a re-plumbing."
  type        = string
  nullable    = false
}

variable "private_route_table_ids" {
  description = "foundation/'s private route tables, BY ZONE ID - under design A every one of them gets the default route toward the one NAT (steps 2.2, 7, 10). Read through terraform_remote_state."
  type        = map(string)
  nullable    = false
}

variable "endpoint_subnet_id" {
  description = "The ONE subnet every interface endpoint lands in - single AZ (D9, step 8.5): two AZs doubles the largest hourly line item, and a resource in the other AZ still resolves and reaches it. The caller picks the private subnet of the first authored zone."
  type        = string
  nullable    = false
}

variable "endpoint_security_group_id" {
  description = "foundation/'s endpoint SG (step 2.4) - TCP/443 from the VPC CIDR, attached to every interface endpoint here."
  type        = string
  nullable    = false
}

variable "core_services" {
  description = "Step 8.2's common core, in every account: identity, logging, keys, images, and the data-plane three - under design B a missing athena/glue means no query executes at all (D13). lakeformation is the least certain entry and is included at a cent an hour rather than discovered at Stage 6; verification (ii) decides whether it stays. Overridden never - the per-role differences go in extra_services."
  type        = list(string)
  default     = ["sts", "logs", "kms", "ecr.api", "ecr.dkr", "athena", "glue", "lakeformation"]
}

variable "extra_services" {
  description = "The per-account-role adds of step 8.3 - authored in each caller, because the list being DIFFERENT per role is the point: one list everywhere was wrong in both directions. Short service tokens ('sagemaker.api'); the region prefix is built here. Every entry is ~USD 0.010/h for the whole session."
  type        = list(string)
  default     = []
}

# ------------------------------------------------ design A's control (Stage 6 step 4.1)

variable "dns_firewall" {
  description = "Attach the Route 53 Resolver DNS Firewall to this VPC - design A's allow-list. false everywhere it does not apply: the deployment targets have no interactive user to constrain, and under egress_mode = B there is no default route for a name to be useful on (dns-firewall.tf enforces the second half itself, so a caller cannot half-enable it)."
  type        = bool
  default     = false
}

variable "firewall_domain_redirection_action" {
  description = "How the ALLOW rule treats a CNAME/DNAME chain. INSPECT_REDIRECTION_DOMAIN (the API default, and this module's) evaluates EVERY domain in the chain, so a hop that is not listed blocks the lookup. TRUST_REDIRECTION_DOMAIN evaluates the QUERIED name only and trusts the chain beneath it. Declared by the caller, like the list it governs."
  type        = string
  default     = "INSPECT_REDIRECTION_DOMAIN"

  # THE DEFAULT IS THE STRICTER READING, AND THAT IS THE POLICY - the same argument the empty
  # allow-list above is built on. A caller who never thought about this field gets the
  # behaviour where nothing resolves unless the whole chain was reasoned about; a caller who
  # wants the chain trusted has to say so, in its own slice, where the reach of that account
  # is decided. It is deliberately NOT the setting this estate's two Interactive slices use.
  #
  # WHY IT IS A VARIABLE AT ALL, since one value looks obviously better: the two are not
  # ranked, they answer different questions. INSPECT asks "does every name this lookup
  # touches belong to a set I enumerated" - the right question for a slice reaching a small
  # number of first-party hosts, and the only one that survives a listed name whose owner is
  # compromised. TRUST asks "did my tool ask for a name I approve of", which is what an
  # allow-list of hostnames means to the person writing it, and the only workable question
  # once artifact hosts are involved (see the list's comment). An account gets to answer the
  # one that matches what it reaches.
  #
  # AND THE FIELD IS PER RULE, not per rule group: dns-firewall.tf puts it on the ALLOW rule
  # only. The catch-all `*` matches at the first domain of every query and never has a chain
  # left to inspect, so there is nothing there for this to mean.
  validation {
    condition     = contains(["INSPECT_REDIRECTION_DOMAIN", "TRUST_REDIRECTION_DOMAIN"], var.firewall_domain_redirection_action)
    error_message = "firewall_domain_redirection_action is INSPECT_REDIRECTION_DOMAIN or TRUST_REDIRECTION_DOMAIN - the two values the Route 53 Resolver API defines, nothing else."
  }
}

variable "dns_firewall_allow_domains" {
  description = "The allow-list, declared BY THE CALLER. Empty by default, and an empty list means the firewall creates no ALLOW rule at all - every lookup in the VPC returns NXDOMAIN. Since v0.4.0 the ALLOW rule trusts the redirection chain, so an entry is THE NAME A TOOL QUERIES and never a CNAME target - listing a hop is a widening, not a safety net."
  type        = list(string)

  # EMPTY BY DESIGN, AND THE DEFAULT IS THE POLICY (v0.3.0, 2026-08-23). Until v0.2.1 this
  # variable carried the estate's actual allow-list, on a "one copy so two callers cannot
  # drift" argument. That argument was worth less than it looked: the list is not a property
  # of the MECHANISM, it is a property of what a particular account is allowed to reach, and
  # keeping it here meant a module tag bump to change one account's reach and a silent
  # inheritance for any caller that never thought about it. The trade is deliberate and is
  # not free - two Interactive slices now each carry a list and CAN diverge, and nothing
  # mechanical compares them. That is the cost side, recorded so it is not discovered.
  #
  # WHAT A CALLER MUST SATISFY BEFORE ADDING A NAME - the reason this comment is here rather
  # than beside each list: dns-firewall.tf's header carries the mechanism. Since v0.4.0 the
  # ALLOW rule is set to TRUST_REDIRECTION_DOMAIN, so the firewall inspects THE NAME THAT WAS
  # QUERIED and trusts whatever chain it resolves through. The rule that follows is one line:
  #
  #     LIST THE NAME YOUR TOOLS ASK FOR. NEVER LIST A REDIRECTION TARGET.
  #
  # A hop on this list is not harmless redundancy. The trust is scoped to a single query
  # transaction, so a redirection target is unreachable on its own - unless somebody lists
  # it, which is exactly what makes `dualstack.j2.shared.global.fastly.net` resolvable for
  # anything that cares to ask. Every hop removed from a list is a narrowing.
  #
  # WHAT TO CHECK BEFORE ADDING A NAME, NOW THAT THE CHAIN NO LONGER DECIDES: only that the
  # name answers at all, and that you meant to reach its owner.
  #
  #     dig +noall +answer <name>     # +short hides the record TYPE, and the type is the answer
  #
  # A CNAME row is no longer a disqualification - it is information about who you are trusting.
  # The three shapes this comment used to sort names into (flat / same-namespace CNAME /
  # CNAME into a shared CDN) all resolve now, and only the third is worth a second thought:
  # `fastly.net`, `cloudfront.net`, `cdn.cloudflare.net`, `fastlydns.net` and
  # `awsglobalaccelerator.com` are multi-tenant, so the bytes come from a host shared with
  # everyone. That is an argument about WHO SERVES the artifact, not about whether the name
  # can be listed, and it is D5's argument (step 6.1) rather than this variable's.
  #
  # WHAT THE LIST NO LONGER PROTECTS AGAINST, so nobody re-derives it from the code: the
  # control now rests on the OWNER of each listed name keeping its DNS honest. That was
  # always true of an A record and is now true of the whole chain. And it never covered the
  # two bypasses - a raw address asks no resolver, and a query sent to `1.1.1.1` or over DoH
  # is not answered by the VPC resolver, so this firewall never sees it. Closing those needs
  # an SNI/Host control (Network Firewall, or a proxy); neither is built.
  #
  # HISTORY, kept because a reader will meet it in the stage log and in EXC-05: until v0.4.0
  # this module took the API default, INSPECT_REDIRECTION_DOMAIN, and every hop had to be
  # listed. Under that default eight of the nine external names the two Interactive slices
  # carried resolved only because their authoritative side FLATTENS the CDN behind an A record
  # served under the queried name (measured 2026-08-23: `dig`, `whois` on the answer address,
  # response headers) - a switch a third party could turn off without announcing it. That
  # dependency is what v0.4.0 removes. ./aws/dns-allowlist.py still re-resolves both lists,
  # and DN-2 now asks the question this rule made important: is anything on a list a hop.
  default = []
}
