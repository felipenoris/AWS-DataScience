# NO_PROXY, generated from this VPC's own endpoint list (6c step 5.6).
#
# Not a blanket `.us-west-2.amazonaws.com`. That suffix tells a client to reach every AWS service
# directly, and under design B there is no default route, so a service without an endpoint has no
# path at all: the call leaves the SDK, finds no route, and ends as a socket timeout with no message
# (Lesson 42 - a network failure is the absence of a response). Generated per VPC, the same call
# reaches the proxy and comes back as a 403 naming the host, which a person can act on.
#
# The names come from the ENDPOINT, not from the service, because the two readings differ:
#
#   data.aws_vpc_endpoint_service.private_dns_name   one name - the service's canonical spelling
#   aws_vpc_endpoint.dns_entry[*].dns_name           every name the endpoint answers for
#
# Measured in Sandbox 2026-09-09: 16 of 18 interface endpoints answer for at least one name the
# service reading does not carry.
#
#   datazone          datazone.<region>.amazonaws.com     + datazone.<region>.api.aws
#   logs              logs.<region>.amazonaws.com         + logs.<region>.api.aws
#                                                         + streaming-logs.<region>.amazonaws.com
#                                                         + streaming-logs.<region>.api.aws
#   ecr.dkr           *.dkr.ecr.<region>.amazonaws.com    + dkr-ecr.<region>.on.aws   (and wildcard)
#   sagemaker.studio  *.studio.<region>.sagemaker.aws     + studio.sagemaker.<region>.app.aws (idem)
#   twelve more       <service>.<region>.amazonaws.com    + an `.api.aws` twin
#
# A name missing from this list goes to Squid, and the plane's allow-list decides what happens:
#
#   `.api.aws`, `.app.aws`, `.on.aws`   on no compute plane  -> 403, visible, naming the host
#   `.amazonaws.com`                    is on the plane      -> 200. The call leaves through the
#                                       hub's IGW as a PUBLIC call and arrives carrying neither
#                                       aws:SourceVpc nor aws:SourceVpce
#
# So the loud case was luck of the domain family. `streaming-logs.<region>.amazonaws.com` is the
# second row: a different label under a family this list already carries, which no suffix rule covers
# and no 403 would report. The symptom that found the defect was the first row - 11 refusals of
# `datazone.<region>.api.aws` in the proxy log, for a service holding an interface endpoint in that
# very VPC, which broke DataZone inside a Studio space (2026-09-08).
#
# `dns_entry` is an attribute of a resource this module creates, so its value is known only after
# apply. Nothing consumes it during an apply - the three egress slices publish it as an output, read
# by hand and by production/buildbox's user-data through terraform_remote_state - so the cost is a
# first plan printing (known after apply).
#
# The service reading survives for one job: the DNS Firewall coverage guard below has to fail at PLAN
# time, and `dns_entry` cannot do that on a VPC whose endpoints do not exist yet. Measured
# (staging/egress, torn down, 2026-09-09): with the guard reading `dns_entry` alone, `terraform plan`
# on an empty state printed `20 to add` and `no_proxy = (known after apply)` and raised nothing - the
# condition was unknown, so Terraform deferred it to apply (Lesson 39: the strict validator arrives
# one act late). One plan-time call per declared service, free, requiring no endpoint to exist.
data "aws_vpc_endpoint_service" "this" {
  for_each = local.service_names

  service_name = each.value
}

locals {
  # Every name, minus the endpoint-specific ones. `dns_entry` carries two kinds of name and only one
  # of them is a service name (measured 2026-09-09, sagemaker.studio, eight entries):
  #
  #   vpce-0ade...-k08f855k.studio.<region>.vpce.sagemaker.aws              the endpoint, regional
  #   vpce-0ade...-k08f855k-us-west-2b.studio.<region>.vpce.sagemaker.aws   the endpoint, zonal
  #   studio.<region>.sagemaker.aws                                         what a client dials
  #
  # Nothing in this estate dials the first kind (`private_dns_enabled` is true on every endpoint this
  # module creates, so clients use the service name), and it embeds the endpoint id, which is `[E]`.
  # Including it would make NO_PROXY change on every up/down cycle, and D11's proof rests on the [P]
  # outputs being byte-identical on the second `up`.
  #
  # Filtered on the `vpce-` prefix, not on a `.vpce.amazonaws.com` suffix: sagemaker.studio's
  # endpoint-specific names end in `.vpce.sagemaker.aws`, so a suffix filter would let four through.
  endpoint_dns_names = distinct(flatten([
    for k, ep in aws_vpc_endpoint.interface : [
      for entry in ep.dns_entry : entry.dns_name
      if !startswith(entry.dns_name, "vpce-")
    ]
  ]))

  # The declared half, for the guard alone and never for NO_PROXY: one name per service, where the
  # resolver serves several.
  declared_private_dns_names = [
    for s, svc in data.aws_vpc_endpoint_service.this :
    svc.private_dns_name
    if svc.private_dns_name != ""
  ]

  # A wildcard name is forked into both spellings, never deleted. `*.` cannot survive into NO_PROXY -
  # entries there match as suffixes only, so `*.dkr.ecr...` written literally matches nothing, and
  # this file's own precondition refuses it. Both spellings, because the clients disagree here and no
  # single form is right under all of them (6d step 8.8):
  #
  #   requests / botocore      hostname.endswith(entry)              bare covers the subtree AND the
  #                                                                  apex; dot-prefixed, subtree only
  #   CPython urllib           strips a leading dot, (.+\.)?name$     either form covers both
  #   curl                     skips a leading dot, exact-or-suffix   either form covers both
  #   a strict suffix matcher  the mirror image of the first row
  #
  # The bare form can miss a subdomain, the dot form can miss the apex, and which failure you get
  # depends on the client. Carrying both is correct under every matcher and costs one array entry per
  # wildcard name, four in Sandbox - the choice 6d step 8.4 made for the two internal zones (Lesson
  # 53: one syntax is not settled by transcribing the other). `trimprefix` rather than `replace`
  # touches only a leading `*`, so a name carrying the sequence elsewhere survives intact.
  no_proxy_endpoint_entries = distinct(flatten([
    for name in local.endpoint_dns_names :
    startswith(name, "*.")
    ? [trimprefix(name, "*."), trimprefix(name, "*")]
    : [name]
  ]))

  # The fixed half - entries no endpoint list can produce.
  #
  # S3 and DynamoDB are here because a gateway endpoint has no private DNS at all. Measured
  # 2026-09-06: `com.amazonaws.<region>.s3` returns a `PrivateDnsName` for its Interface shape and
  # `None` for its Gateway shape, because a gateway works by routing (the public name resolves to a
  # public address and a prefix-list route carries it to the endpoint), never by resolution. So the
  # loop above cannot emit them, and without them an S3 call goes to Squid, leaves through the hub's
  # IGW as a public call, and arrives at S3 carrying neither `aws:SourceVpc` nor `aws:SourceVpce` -
  # the two keys every bucket policy and gateway-endpoint allow-list here is written on. The data
  # perimeter would fail open, quietly, for the one service that carries the data.
  #
  # The link-local pair is the instance metadata service and the ECS/Fargate task-role credential
  # endpoint: a proxied call to either is a credential lookup sent to a host that is not the
  # instance. `localhost`/`127.0.0.1` are the same argument for anything a container talks to
  # in-process.
  #
  # The two internal zones are named in full because they are siblings, not parent and child:
  # `awsds.internal` does not cover `awsds-pages.internal` (a different label, not a subdomain), and
  # a suffix covering both would have to be `.internal`. The old family - `sandbox.internal`,
  # `prod.internal`, `pages.internal` - is absent: 6c step 2.6 retires it, and an entry here would
  # keep it alive.
  #
  # The dualstack spellings are different names, not labels under the ones above:
  # `al2023-repos-<region>-xxxx.s3.dualstack.<region>.amazonaws.com` does not end in
  # `.s3.<region>.amazonaws.com`, so a list carrying only the first form sends the AL2023
  # repositories at the proxy, which refuses them with a 403 because a build host's plane excludes
  # `.amazonaws.com`; `dnf` then reports `Failed to download metadata`, which reads as a broken
  # mirror. Measured on the host that failed its first boot on this (2026-09-06): the dualstack name
  # returns 200 direct (16.15.35.255, through the gateway) and 000 through the proxy. The gateway
  # carries it, which is what makes the bypass correct rather than merely quieter: a prefix-list
  # route is keyed on the address, and both spellings resolve into S3's IPv4 ranges. The dualstack
  # name also has AAAA records; nothing here has IPv6, so the client picks IPv4 and the route applies.
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
  # Which of this VPC's endpoints the DNS Firewall would make unreachable (6c step 5.7). That step
  # shrinks the allow-list from sixty-odd names to four families, and an interface endpoint whose
  # private DNS name falls outside them is then paid for hourly and cannot be resolved: the catch-all
  # returns NXDOMAIN and the tool reports "no such host", which reads as a network fault rather than
  # a policy decision. `sagemaker.studio` answers on `*.studio.<region>.sagemaker.aws`, a TLD neither
  # `*.amazonaws.com` nor `*.api.aws` covers, so the obvious short list orphans an endpoint in both
  # Interactive slices.
  #
  # The names are used here as AWS gives them, wildcard and all, kept as their own local rather than
  # re-derived from `no_proxy_endpoint_entries`, which has already forked each wildcard into
  # NO_PROXY's two spellings. The two questions share the reading and never the spelling, the only
  # arrangement in which they cannot drift (Lesson 53).
  #
  # This check and NO_PROXY are one intent asked twice - is every name this VPC pays for usable in it
  # - so the check reads `endpoint_dns_names` too; leaving it on the service's single canonical name
  # would keep the blind spot in the guard after removing it from the output (Lesson 51). Widening it
  # found, in both firewalled VPCs, `studio.sagemaker.<region>.app.aws` and `dkr-ecr.<region>.on.aws`:
  # two endpoints paid for hourly, answering on families the allow-list did not carry, hence NXDOMAIN.
  # Both families were added the same day by the user's decision, and the two calling slices carry
  # the argument.
  #
  # Matching here is the firewall's, not NO_PROXY's: an entry matches a name exactly, and `*.x`
  # matches every nesting level beneath `x` and never `x` itself. A service whose own name is
  # wildcarded (`*.dkr.ecr...`) is genuinely covered only by a wildcard entry, since an exact entry
  # would match the base and none of the names actually queried.
  #
  # The trailing dot is stripped on the allow-list side: `EXC-04`'s repair one file over writes every
  # entry as an FQDN, `amazonaws.com.`, because that is how Route 53 canonicalises them, while
  # `describe-vpc-endpoint-services` returns names without one. Without this the precondition fired on
  # a correct list, naming ten covered endpoints as uncovered (v0.10.1, 2026-09-06). Normalised here
  # rather than by dropping the dots, which are what makes the plan converge.
  dns_firewall_allow_normalised = [for e in var.dns_firewall_allow_domains : trimsuffix(e, ".")]

  # The coverage matcher, run over two readings of one question. They differ in WHEN they can answer,
  # never in what they ask:
  #
  #   declared   the service's canonical name, from the data source. One per declared service, known
  #              at plan time whether or not the endpoint exists. Narrower, and always early.
  #   served     every name the endpoint answers for, from `dns_entry`. Known at plan on a VPC that
  #              is already up; (known after apply) on one being raised. Complete, and sometimes late.
  #
  # Neither replaces the other: dropping `declared` puts the whole guard behind an apply on every new
  # VPC, dropping `served` puts the blind spot back. They are two preconditions on the resource below,
  # each naming its own reading, so a failure says which half found it. The comparison is written once
  # and mapped over both lists rather than copied (Lesson 33, and Lesson 51 for the half that bites).
  dns_firewall_uncovered = {
    for reading, names in {
      declared = local.declared_private_dns_names
      served   = local.endpoint_dns_names
      } : reading => [
      for raw in names : raw
      if !anytrue([
        for e in local.dns_firewall_allow_normalised :
        startswith(e, "*.")
        ? (trimprefix(raw, "*.") == trimprefix(e, "*.") || endswith(trimprefix(raw, "*."), ".${trimprefix(e, "*.")}"))
        : (!startswith(raw, "*.") && raw == e)
      ])
    ]
  }
}

output "no_proxy_entries" {
  description = "This VPC's NO_PROXY as a list: every name its interface endpoints answer for, plus the fixed entries. Consumed by whatever configures a client in this VPC (the buildbox's docker daemon and SSM agent, a runner, a Studio app image configuration), through terraform_remote_state so the list cannot be transcribed (Lesson 3)."
  value       = local.no_proxy_entries
}

output "no_proxy" {
  description = "The same list comma-joined - the literal value of the NO_PROXY / no_proxy environment variable."
  value       = join(",", local.no_proxy_entries)

  # The ways this variable fails silently. None errors at the client: a malformed entry never
  # matches, the call goes to the proxy, and the symptom surfaces as a 403 for a service that should
  # never have been proxied - or, for S3, as a data perimeter that stopped applying. Checked here,
  # where the list is built, rather than in a script somebody would have to run.
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
