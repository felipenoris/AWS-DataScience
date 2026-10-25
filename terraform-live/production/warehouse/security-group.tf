# The workgroup's security group (Stage 5b step 1.4, Stage 9 step 9.1). It lives in this slice and
# not in the compute slice: a security group is free, it is referenced by the workgroup rather than
# the reverse, and re-creating it on every `make up` would churn an object whose id the [P] side may
# one day want to name. The workgroup reads its id from this slice's state.
#
# What it decides is which in-VPC client may open a connection, nothing more. The workgroup lands in
# VPC-Workloads' private tier, which has no default route and no NAT anywhere (D38), so the warehouse
# has no internet either way, and whether it can be reached from outside is answered by the topology.
# The 5439 data path needs no interface endpoint (5b 1.10): the workgroup's own host resolves to its
# ENIs in this VPC. An interface endpoint for `redshift-serverless` is a door for the API alone, and
# the deploy runner's door is the Data API from VPC-SharedServices, which does not peer with
# VPC-Workloads (step 9.4).
resource "aws_security_group" "warehouse" {
  # checkov:skip=CKV2_AWS_5:attached by production/warehouse-compute/, the [E] slice that owns the workgroup. The group is [P] because it is free and is referenced by the workgroup rather than the reverse, so it is unattached by design for the hours the compute is down
  name        = local.name
  description = "Redshift Serverless workgroup ${local.name} (Stage 9 step 9.1). Ingress 5439/tcp from the job security group awsds-${var.env}-jobs only; no egress. No apostrophe here: EC2 refuses one in a group description (measured 2026-09-20)."
  vpc_id      = local.vpc_id

  tags = { Name = local.name }
}

# One rule, from the job security group, group to group: every pipeline-submitted Glue and SageMaker
# job carries awsds-prod-jobs (Stage 9 decision 12 (a)), the governed schema's load job among them
# (step 9.4), and the two private subnets also hold the MWAA Serverless workers (Stage 10), whose group
# this rule does not name. Never a CIDR, which would admit every ENI in the tier (Lesson 29); and the
# referenced group is [P] in production/sagemaker/, so no teardown breaks the reference.
resource "aws_vpc_security_group_ingress_rule" "jobs_5439" {
  security_group_id            = aws_security_group.warehouse.id
  referenced_security_group_id = local.job_security_group_id
  from_port                    = 5439
  to_port                      = 5439
  ip_protocol                  = "tcp"
  # `to` rather than an arrow: EC2 refuses a rule description containing `>`, at apply (measured
  # 2026-09-21). scripts/check-sg-descriptions.py reads the permitted set.
  description = "The job security group to Redshift 5439 (Stage 9 step 9.1)"
}

# The same path's other half, on the job group: production/sagemaker/ gives that group egress to the
# interface endpoints and the S3 gateway alone, so the load job's JDBC connection needs this rule to
# leave it (refused as "Connect timed out" on 2026-10-25, the rule absent). Written beside the ingress it
# pairs with, so the slice that brings the warehouse brings both halves.
resource "aws_vpc_security_group_egress_rule" "jobs_to_warehouse_5439" {
  security_group_id            = local.job_security_group_id
  referenced_security_group_id = aws_security_group.warehouse.id
  from_port                    = 5439
  to_port                      = 5439
  ip_protocol                  = "tcp"
  description                  = "The job security group to Redshift 5439 (Stage 9 step 9.4)"
}

# No egress rule, and the absence is deliberate. A Redshift Serverless workgroup's ENIs answer
# queries; nothing in this design has the warehouse originate a connection. COPY and UNLOAD would,
# and step 9.2 gives the namespace role no lake reach, so the day one is granted is the day an egress
# rule is written with a named destination, the S3 gateway endpoint's prefix list, never 0.0.0.0/0.
