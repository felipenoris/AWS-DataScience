# NO_PROXY, GENERATED FROM THIS VPC'S OWN ENDPOINT LIST (6c step 5.6, 2026-09-06).
#
# WHY IT IS NOT A BLANKET `.us-west-2.amazonaws.com`, which is what every tutorial writes. That
# suffix tells a client "reach every AWS service directly". Under design B there is no default
# route, so a service WITHOUT an endpoint then has no path at all: the call leaves the SDK, finds
# no route, and ends as a socket timeout with no message - a network failure is the ABSENCE of a
# response, which is the failure mode Lesson 42 separates from a denial. Generated per VPC, the
# same call instead reaches the proxy and comes back as a **403 naming the host**, which is a
# finding a person can act on. The list therefore holds every name this VPC's own endpoints answer
# for - LONGER than the endpoint list, since 2026-09-09 - and it shrinks and grows with them in the
# same apply.
#
# WHY THE NAMES ARE READ FROM THE ENDPOINT AND NOT FROM THE SERVICE (rewritten 2026-09-09, 6d step
# 8.8). Two readings answer "what does this endpoint respond to", and they do not return the same
# thing:
#
#   data.aws_vpc_endpoint_service.private_dns_name   ONE name - the service's canonical spelling
#   aws_vpc_endpoint.dns_entry[*].dns_name           EVERY name the endpoint actually answers for
#
# This module used the first from 6c step 5.6 until now, so the bypass list carried exactly one name
# per endpoint while the resolver served several. Measured in Sandbox 2026-09-09: 16 of 18 interface
# endpoints answer for at least one name the generated list did not carry.
#
#   datazone          datazone.<region>.amazonaws.com     + datazone.<region>.api.aws
#   logs              logs.<region>.amazonaws.com         + logs.<region>.api.aws
#                                                         + streaming-logs.<region>.amazonaws.com
#                                                         + streaming-logs.<region>.api.aws
#   ecr.dkr           *.dkr.ecr.<region>.amazonaws.com    + dkr-ecr.<region>.on.aws   (and wildcard)
#   sagemaker.studio  *.studio.<region>.sagemaker.aws     + studio.sagemaker.<region>.app.aws (idem)
#   twelve more       <service>.<region>.amazonaws.com    + an `.api.aws` twin
#
# WHAT A MISSING ENTRY COSTS, AND THE LOUD CASE WAS LUCK OF THE DOMAIN FAMILY. A name absent from
# this list goes to Squid, and what happens there is decided by the plane's allow-list, never by
# anything in this file:
#
#   `.api.aws`, `.app.aws`, `.on.aws`   on no compute plane  -> 403. Visible, and it names the host.
#   `.amazonaws.com`                    IS on the plane      -> 200. The call leaves through the
#                                       hub's IGW as a PUBLIC call and arrives carrying neither
#                                       aws:SourceVpc nor aws:SourceVpce.
#
# `streaming-logs.<region>.amazonaws.com` is the second row and it is not hypothetical: a different
# LABEL under a family this list already carries, so no suffix rule covers it and no 403 would ever
# have reported it. That is the same fail-open the gateway pair below is written against, one level
# down - not a service left out, but a NAME of a service that was put in.
#
# The symptom that found the defect was the first row: `datazone.<region>.api.aws` refused 11 times
# in the proxy's log, for a service holding an interface endpoint in that very VPC, which broke
# DataZone inside a Studio space (2026-09-08). A hand-patch adding that one name to the space's
# `http.noProxy` removed exactly that refusal and left the other five - the cause reproduced rather
# than the symptom relieved.
#
# THIRD INSTANCE OF ONE CAUSE, which is why the repair is a different READING and not another entry.
# The fixed half below already carries two hand-patches of this shape: the gateway pair, which has no
# private DNS at all, and the `dualstack` spellings, added after a build host failed its first boot.
# The pattern is Lesson 40's neighbour - THE ROSTER YIELDS FEWER NAMES THAN THE RESOLVER SERVES - and
# reading the endpoint is what stops it recurring, because a name AWS adds to an endpoint that
# already exists now arrives on the next apply instead of on the next outage.
#
# WHAT THE CHANGE COSTS. `dns_entry` is an attribute of a resource this module creates, so the value
# is known only after apply where the data source was a plan-time reading requiring no endpoint to
# exist. Nothing consumes it DURING an apply - the three egress slices publish it as an output, read
# by hand and by production/buildbox's user-data through terraform_remote_state - so the whole cost
# is that a first plan prints (known after apply). The data source is gone: keeping it beside this
# would be two readings of one fact, which is Lesson 33 in a file that already argues against it.
locals {
  # EVERY NAME, MINUS THE ENDPOINT-SPECIFIC ONES. `dns_entry` carries two kinds of name and only one
  # of them is a service name (measured 2026-09-09, sagemaker.studio, eight entries):
  #
  #   vpce-0ade...-k08f855k.studio.<region>.vpce.sagemaker.aws              the ENDPOINT, regional
  #   vpce-0ade...-k08f855k-us-west-2b.studio.<region>.vpce.sagemaker.aws   the ENDPOINT, zonal
  #   studio.<region>.sagemaker.aws                                         what a client dials
  #
  # The first kind is excluded for two reasons, and the second is the one that matters here. Nothing
  # in this estate dials it - `private_dns_enabled` is true on every endpoint this module creates, so
  # clients use the service name - and it embeds the endpoint ID, which is `[E]`. Including it would
  # make NO_PROXY change on every up/down cycle, and "the [P] outputs are byte-identical on the
  # second `up`" is the property D11's proof rests on.
  #
  # FILTERED ON THE `vpce-` PREFIX RATHER THAN ON A `.vpce.amazonaws.com` SUFFIX, and the difference
  # is measured rather than stylistic: sagemaker.studio's endpoint-specific names end in
  # `.vpce.sagemaker.aws`, so a suffix filter would have let four of them through.
  endpoint_dns_names = distinct(flatten([
    for k, ep in aws_vpc_endpoint.interface : [
      for entry in ep.dns_entry : entry.dns_name
      if !startswith(entry.dns_name, "vpce-")
    ]
  ]))

  # THE ONE TRANSFORMATION, AND IT IS NOW A FORK RATHER THAN A DELETION. `*.` cannot survive into
  # NO_PROXY - entries there match as SUFFIXES ONLY, never as prefixes and never as a CIDR block, so
  # `*.dkr.ecr...` written literally matches nothing in any client that matters, and this file's own
  # precondition refuses it.
  #
  # BOTH SPELLINGS FOR A WILDCARD NAME (decided 2026-09-09, 6d step 8.8), because the clients
  # disagree exactly here and no single form is right under all of them:
  #
  #   requests / botocore      hostname.endswith(entry)              bare covers the subtree AND the
  #                                                                  apex; dot-prefixed, subtree only
  #   CPython urllib           strips a leading dot, (.+\.)?name$     either form covers both
  #   curl                     skips a leading dot, exact-or-suffix   either form covers both
  #   a strict suffix matcher  the mirror image of the first row
  #
  # So the bare form is the one that can miss a subdomain and the dot form is the one that can miss
  # the apex, and which failure you get depends on the client rather than on the name. Carrying both
  # is correct under every matcher above and costs one array entry per wildcard name - four in
  # Sandbox. It is the choice 6d step 8.4 made for the two internal zones, for the same reason;
  # Lesson 53 is why it is not settled by transcribing one syntax into the other.
  #
  # `trimprefix` rather than `replace` on purpose: it touches only a LEADING `*`, so a name that
  # carried the sequence elsewhere would survive intact.
  no_proxy_endpoint_entries = distinct(flatten([
    for name in local.endpoint_dns_names :
    startswith(name, "*.")
    ? [trimprefix(name, "*."), trimprefix(name, "*")]
    : [name]
  ]))

  # THE FIXED HALF - six entries no endpoint list can produce, and the first two are the ones that
  # would hurt.
  #
  # S3 AND DYNAMODB ARE HERE BECAUSE A GATEWAY ENDPOINT HAS NO PRIVATE DNS AT ALL. Measured
  # 2026-09-06: `com.amazonaws.<region>.s3` returns a `PrivateDnsName` for its **Interface** shape
  # and `None` for its **Gateway** shape, because a gateway works by ROUTING - the public name
  # resolves to a public address and a prefix-list route carries it to the endpoint - and never by
  # resolution. So the loop above cannot emit them, and leaving them out is not a missing
  # convenience: an S3 call would then go to Squid, leave through the hub's IGW as a PUBLIC call,
  # and arrive at S3 carrying neither `aws:SourceVpc` nor `aws:SourceVpce`. Every bucket policy and
  # every gateway-endpoint allow-list in this estate is keyed on exactly those two. The data
  # perimeter would fail open, quietly, for the one service that carries the data.
  #
  # The link-local pair is the instance metadata service and the ECS/Fargate task-role credential
  # endpoint: a proxied call to either is a credential lookup sent to a host that is not the
  # instance. `localhost`/`127.0.0.1` are the same argument for anything a container talks to
  # in-process.
  #
  # The two internal zones are named in full because they are SIBLINGS, not parent and child:
  # `awsds.internal` does not cover `awsds-pages.internal` (a different label, not a subdomain),
  # and a suffix that covered both would have to be `.internal`. The old family - `sandbox.internal`,
  # `prod.internal`, `pages.internal` - is deliberately absent; 6c step 2.6 retires it, and an entry
  # here would be the thing that kept it alive.
  # AND THE DUALSTACK SPELLINGS, ADDED 2026-09-06 AFTER A BUILD HOST FAILED ITS FIRST BOOT ON
  # EXACTLY THIS. `s3.dualstack.<region>.amazonaws.com` is a DIFFERENT NAME, not a label under the
  # one above: `al2023-repos-<region>-xxxx.s3.dualstack.<region>.amazonaws.com` does not end in
  # `.s3.<region>.amazonaws.com`, so a bypass list carrying only the first form sends the AL2023
  # repositories at the proxy - which refuses them with a 403, because a build host's plane
  # deliberately excludes `.amazonaws.com`. `dnf` then reports `Failed to download metadata`, which
  # reads as a broken mirror. Measured on the host: the dualstack name returns 200 direct (16.15.35.255,
  # through the gateway) and 000 through the proxy.
  #
  # THE GATEWAY CARRIES IT, which is what makes the bypass correct rather than merely quieter: a
  # prefix-list route is keyed on the ADDRESS, and both spellings resolve into S3's IPv4 ranges. The
  # dualstack name also has AAAA records; nothing in this estate has IPv6, so the client picks IPv4
  # and the route applies.
  no_proxy_fixed = [
    "s3.${data.aws_region.current.region}.amazonaws.com",
    "s3.dualstack.${data.aws_region.current.region}.amazonaws.com",
    "dynamodb.${data.aws_region.current.region}.amazonaws.com",
    "dynamodb.dualstack.${data.aws_region.current.region}.amazonaws.com",
    "169.254.169.254",
    "169.254.170.2",
    "localhost",
    "127.0.0.1",
    ".awsds.internal",
    ".awsds-pages.internal",
  ]

  no_proxy_entries = sort(distinct(concat(local.no_proxy_fixed, local.no_proxy_endpoint_entries)))

  # ------------------------------------------------- the same reading, put to a second question
  #
  # THE NAMES AS AWS GIVES THEM, wildcard and all - `no_proxy_endpoint_entries` above has already
  # forked each wildcard into NO_PROXY's two spellings, and the DNS Firewall's syntax is neither of
  # them. Kept as its own local rather than re-derived from that one, so neither question can quietly
  # answer with the other's spelling (Lesson 53: two systems expressing one intent in the same-looking
  # syntax are not translatable by transcription, and they agree on the easy cases). The two questions
  # share the READING and never the spelling, which is the only arrangement in which they cannot drift.
  #
  # IT READS `endpoint_dns_names` SINCE 2026-09-09, AND THAT IS THE OTHER HALF OF 8.8's DEFECT rather
  # than tidiness. This check and NO_PROXY are one intent asked twice - *is every name this VPC pays
  # for usable in it* - so leaving the check on the service's single canonical name would have left
  # the blind spot in the guard after removing it from the output, which is the worse of the two
  # places to keep it (Lesson 51). What it found the moment it was widened, in both firewalled VPCs:
  # `studio.sagemaker.<region>.app.aws` and `dkr-ecr.<region>.on.aws` - two endpoints this VPC pays
  # for hourly, answering on families the allow-list did not carry, hence NXDOMAIN. Both families
  # were added the same day by the user's decision; the argument is verbatim the one that put
  # `sagemaker.aws` there, and the two calling slices carry it.
  # WHICH OF THIS VPC'S ENDPOINTS THE DNS FIREWALL WOULD MAKE UNREACHABLE (6c step 5.7).
  #
  # THE FAILURE THIS EXISTS TO CATCH, because 5.7 is the step that creates the opportunity: the
  # allow-list shrinks from sixty-odd names to four families, and an interface endpoint whose
  # private DNS name falls outside those families is then paid for hourly and **cannot be
  # resolved** - the catch-all returns NXDOMAIN and the tool reports "no such host", which reads
  # as a network fault rather than as a policy decision. It is not hypothetical: `sagemaker.studio`
  # answers on `*.studio.<region>.sagemaker.aws`, a TLD neither `*.amazonaws.com` nor `*.api.aws`
  # covers, so the obvious short list orphans an endpoint in both Interactive slices.
  #
  # MATCHING IS THE FIREWALL'S, NOT NO_PROXY'S: an entry matches a name EXACTLY, and `*.x` matches
  # every nesting level beneath `x` and never `x` itself. A service whose own name is wildcarded
  # (`*.dkr.ecr...`) is only genuinely covered by a WILDCARD entry - an exact entry would match the
  # base and none of the names actually queried - so that case is required to find one.
  # THE TRAILING DOT IS STRIPPED ON THE ALLOW-LIST SIDE, AND FORGETTING IT MADE THIS PRECONDITION
  # FIRE ON A CORRECT LIST (v0.10.1, 2026-09-06). `EXC-04`'s repair one file over writes every entry
  # as an FQDN - `amazonaws.com.` - because that is how Route 53 canonicalises them; the names this
  # compares them against come from `describe-vpc-endpoint-services`, which returns them WITHOUT
  # one. Two controls landed in the same sitting and the second read the first's output as a
  # mismatch, naming ten endpoints as uncovered when all ten were covered. Normalised here rather
  # than by dropping the dots, because the dots are what makes the plan converge at all.
  dns_firewall_allow_normalised = [for e in var.dns_firewall_allow_domains : trimsuffix(e, ".")]

  dns_firewall_uncovered = [
    for raw in local.endpoint_dns_names : raw
    if !anytrue([
      for e in local.dns_firewall_allow_normalised :
      startswith(e, "*.")
      ? (trimprefix(raw, "*.") == trimprefix(e, "*.") || endswith(trimprefix(raw, "*."), ".${trimprefix(e, "*.")}"))
      : (!startswith(raw, "*.") && raw == e)
    ])
  ]
}

output "no_proxy_entries" {
  description = "This VPC's NO_PROXY as a list - one entry per interface endpoint plus the fixed eight. Consumed by whatever configures a client in THIS VPC (the buildbox's docker daemon and SSM agent, a runner, a Studio app image configuration), through terraform_remote_state so the list cannot be transcribed (Lesson 3)."
  value       = local.no_proxy_entries
}

output "no_proxy" {
  description = "The same list comma-joined - the literal value of the NO_PROXY / no_proxy environment variable."
  value       = join(",", local.no_proxy_entries)

  # THREE ASSERTIONS FOR THE THREE WAYS THIS VARIABLE FAILS SILENTLY. None of them errors at the
  # client: a malformed entry simply never matches, the call goes to the proxy, and the symptom
  # surfaces as a 403 for a service that should never have been proxied - or, for S3, as a data
  # perimeter that stopped applying. Checked here, where the list is built, rather than in a script
  # that would have to be run.
  precondition {
    condition     = length([for e in local.no_proxy_entries : e if strcontains(e, "*")]) == 0
    error_message = "NO_PROXY carries a wildcard: entries match as suffixes only, so a `*` matches nothing. Strip it."
  }

  precondition {
    condition     = length([for e in local.no_proxy_entries : e if strcontains(e, "/")]) == 0
    error_message = "NO_PROXY carries a CIDR block. Clients do not evaluate CIDR in this variable; express intranet reach as name suffixes and list any literal address literally."
  }

  precondition {
    condition     = length([for e in local.no_proxy_entries : e if strcontains(e, ":")]) == 0
    error_message = "NO_PROXY carries a port. GitLab documents a port in this variable as breaking DNS resolution for repository mirroring; entries are hosts, never host:port."
  }
}
