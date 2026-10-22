# Stage 9 decision 12 (a), taken 2026-10-22 - the network every pipeline-submitted job in this account
# runs in: one security group and one Glue network connection, both [P], in VPC-Workloads's private tier.
# The application slice declares its Glue job on glue_connection_name and Stage 10's render gives a
# processing job's VpcConfig this group, so neither is re-created at each deploy; the warehouse's 5439
# rule (step 9.1) names the group, a reference an [E] group would break at every teardown.
#
# A Glue job with this connection runs in the VPC: its S3 calls arrive through the gateway endpoint
# the lake and the outputs bucket trust, and its API calls through the interface endpoints of the
# egress slice, `lakeformation` among them for the credentials it vends.

data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/workloads/terraform.tfstate"
    region = var.region
  }
}

# The S3 gateway endpoint's routes carry AWS's managed prefix list, so the egress rule below names the
# list, never a CIDR.
data "aws_ec2_managed_prefix_list" "s3" {
  name = "com.amazonaws.${var.region}.s3"
}

# Single-AZ selections land in the first authored zone (D9): a Glue connection names one subnet.
data "aws_subnet" "jobs" {
  id = data.terraform_remote_state.vpc.outputs.private_subnet_ids[var.zone_ids[0]]
}

resource "aws_security_group" "jobs" {
  # checkov:skip=CKV2_AWS_5:attached by the jobs themselves, through the Glue connection below and a processing job's VpcConfig; no job runs at rest
  name        = "awsds-${var.env}-jobs"
  description = "Pipeline-submitted Glue and SageMaker jobs (Stage 9 decision 12). Glue workers reach each other; every other call goes to the interface endpoints or the S3 gateway endpoint of this VPC."
  vpc_id      = data.terraform_remote_state.vpc.outputs.vpc_id

  tags = { Name = "awsds-${var.env}-jobs" }
}

# AWS Glue's documented requirement for a connection's group: a self-referencing rule for every TCP
# port, so the driver and the executors reach each other.
resource "aws_vpc_security_group_ingress_rule" "jobs_from_jobs" {
  # checkov:skip=CKV_AWS_24:the source is this group itself (referenced_security_group_id), never a CIDR; the check reads the port range without its source
  # checkov:skip=CKV_AWS_25:idem
  # checkov:skip=CKV_AWS_260:idem
  security_group_id            = aws_security_group.jobs.id
  referenced_security_group_id = aws_security_group.jobs.id
  ip_protocol                  = "tcp"
  from_port                    = 0
  to_port                      = 65535
  description                  = "Glue workers from each other (required of a Glue connection)"
}

resource "aws_vpc_security_group_egress_rule" "jobs_to_jobs" {
  security_group_id            = aws_security_group.jobs.id
  referenced_security_group_id = aws_security_group.jobs.id
  ip_protocol                  = "tcp"
  from_port                    = 0
  to_port                      = 65535
  description                  = "Glue workers to each other (required of a Glue connection)"
}

resource "aws_vpc_security_group_egress_rule" "jobs_to_endpoints" {
  security_group_id            = aws_security_group.jobs.id
  referenced_security_group_id = data.terraform_remote_state.vpc.outputs.endpoints_security_group_id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
  description                  = "AWS APIs through the interface endpoints of this VPC"
}

resource "aws_vpc_security_group_egress_rule" "jobs_to_s3" {
  security_group_id = aws_security_group.jobs.id
  prefix_list_id    = data.aws_ec2_managed_prefix_list.s3.id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  description       = "S3 through the gateway endpoint"
}

resource "aws_glue_connection" "jobs" {
  name            = "awsds-${var.env}-jobs"
  description     = "The network a pipeline-submitted Glue job runs in (Stage 9 decision 12)"
  connection_type = "NETWORK"

  physical_connection_requirements {
    availability_zone      = data.aws_subnet.jobs.availability_zone
    security_group_id_list = [aws_security_group.jobs.id]
    subnet_id              = data.aws_subnet.jobs.id
  }
}
