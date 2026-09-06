# NO_PROXY, GENERATED FROM THIS VPC'S OWN ENDPOINT LIST (6c step 5.6, 2026-09-06).
#
# WHY IT IS NOT A BLANKET `.us-west-2.amazonaws.com`, which is what every tutorial writes. That
# suffix tells a client "reach every AWS service directly". Under design B there is no default
# route, so a service WITHOUT an endpoint then has no path at all: the call leaves the SDK, finds
# no route, and ends as a socket timeout with no message - a network failure is the ABSENCE of a
# response, which is the failure mode Lesson 42 separates from a denial. Generated per VPC, the
# same call instead reaches the proxy and comes back as a **403 naming the host**, which is a
# finding a person can act on. The list is therefore exactly as long as the endpoint list, and it
# shrinks and grows with it in the same apply.
#
# WHY THE NAME IS READ FROM AWS AND NOT BUILT FROM THE TOKEN. `local.service_names` builds
# `com.amazonaws.<region>.<token>`, and it is tempting to build the DNS name the same way. It does
# not work, and the measurement on 2026-09-06 says by how much: of 29 services this estate can
# declare, **8 have a private DNS name no rule derives from the token** -
#
#   ecr.api                          -> api.ecr.<region>.amazonaws.com          (reversed)
#   ecr.dkr                          -> *.dkr.ecr.<region>.amazonaws.com        (reversed, wildcard)
#   sagemaker.api / sagemaker.runtime -> api. / runtime.sagemaker.<region>...    (reversed)
#   sagemaker.studio                 -> *.studio.<region>.sagemaker.aws         (a different TLD)
#   emr-dashboard                    -> *.emrappui-prod.<region>.amazonaws.com  (an unrelated name)
#   emr-serverless-services.sessions -> *.s.emr-serverless-services...          (`sessions` -> `s`)
#   elasticmapreduce-services        -> *.elasticmapreduce-services...          (wildcard)
#
# A hand-written list would have been wrong for ECR - the most-used path in the estate - and wrong
# silently, because a bypass entry that matches nothing simply sends the call to the proxy. So the
# name comes from `describe-vpc-endpoint-services` through a data source: a plan-time READING, one
# per declared service, free and requiring no endpoint to exist yet (Lesson 38 - an identifier read
# out of prose is a claim, not a reading).
data "aws_vpc_endpoint_service" "this" {
  for_each = local.service_names

  service_name = each.value
}

locals {
  # THE ONE TRANSFORMATION, AND IT IS A DELETION: `*.` comes off the front. NO_PROXY wildcards are
  # documented (GitLab, for the runner and for repository mirroring) to work only as SUFFIXES -
  # never as prefixes, never as a CIDR block - so `*.dkr.ecr...` written literally matches nothing
  # in any client that matters. `trimprefix` rather than `replace` on purpose: it touches only a
  # LEADING `*.`, so a name that carried the sequence elsewhere would survive intact.
  #
  # BARE, NOT DOT-PREFIXED, and the two cases below differ for a reason rather than by accident.
  # An AWS service endpoint IS the host you talk to (`sts.<region>.amazonaws.com`), so a leading
  # dot would make the exact name miss under the clients that read a dot as "subdomains only"
  # (Go's httpproxy is one). CPython, botocore and curl all match a bare entry against the host
  # AND its subdomains, so bare is the form that covers both shapes with one entry.
  no_proxy_endpoint_entries = [
    for s, svc in data.aws_vpc_endpoint_service.this :
    trimprefix(svc.private_dns_name, "*.")
    if svc.private_dns_name != ""
  ]

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
  no_proxy_fixed = [
    "s3.${data.aws_region.current.region}.amazonaws.com",
    "dynamodb.${data.aws_region.current.region}.amazonaws.com",
    "169.254.169.254",
    "169.254.170.2",
    "localhost",
    "127.0.0.1",
    ".awsds.internal",
    ".awsds-pages.internal",
  ]

  no_proxy_entries = sort(distinct(concat(local.no_proxy_fixed, local.no_proxy_endpoint_entries)))
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
