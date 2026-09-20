# The workgroup's security group (Stage 5b step 1.4). It lives in THIS slice and not in the compute
# slice on purpose: a security group is free, it is referenced by the workgroup rather than the
# reverse, and re-creating it on every `make up` would churn an object whose id the [P] side may
# one day want to name. The workgroup reads its id from this slice's state.
#
# WHAT IT IS ABOUT IS WHICH IN-VPC CLIENT MAY OPEN A CONNECTION, nothing more. The workgroup lands
# in a private tier with no default route and no NAT anywhere (D38), so the warehouse has no
# internet either way and the question "can it be reached from outside" is answered by the topology
# rather than by this group.
#
# THE 5439 DATA PATH NEEDS NO ENDPOINT, and that is the reading 5b 1.10 wrote down: the workgroup's
# own host resolves to its ENIs in this VPC, so what admits a space is this group. An interface
# endpoint for `redshift-serverless` is a door for the API - GetCredentials and the two reads - and
# a different subtree of DNS entirely.
resource "aws_security_group" "warehouse" {
  # checkov:skip=CKV2_AWS_5:attached by sandbox/warehouse-compute/, the [E] slice that owns the workgroup. The group is [P] because it is free, it is referenced by the workgroup rather than the reverse, and re-creating it on every `make up` would churn an object a policy may one day name - so it is unattached by design for the hours the compute is down
  name        = local.name
  description = "Redshift Serverless workgroup ${local.name} (Stage 5b step 1.4). Ingress 5439/tcp from the app ENIs of admitted SMUS projects only; no egress. No apostrophe here: EC2 refuses one in a group description (measured 2026-09-20)."
  vpc_id      = data.terraform_remote_state.foundation.outputs.vpc_id

  tags = { Name = local.name }
}

# One rule per admitted project, from the project's OWN security group - not a CIDR, and not the
# whole private tier. A CIDR rule would admit every ENI in two /18s, which includes every other
# project's apps and every future workload: the group-to-group form is what makes the door as narrow
# as the tag (Lesson 29 - a selector written over an attribute inherits everything wearing it).
#
# With `projects` empty, this creates nothing, and a workgroup with no ingress rule is a warehouse
# nothing in the VPC can open a connection to. That is the state pass 1 applies in, and it is what
# makes 6h verification (vi)'s "before" a measurement.
resource "aws_vpc_security_group_ingress_rule" "project_5439" {
  for_each = var.projects

  security_group_id            = aws_security_group.warehouse.id
  referenced_security_group_id = data.aws_security_group.project[each.key].id
  from_port                    = 5439
  to_port                      = 5439
  ip_protocol                  = "tcp"
  description                  = "SMUS project ${each.key} app ENIs -> Redshift 5439 (Stage 6h step 3.3)"
}

# NO EGRESS RULE, and the absence is deliberate rather than forgotten. A Redshift Serverless
# workgroup's ENIs answer queries; nothing in this design has the warehouse originate a connection.
# COPY and UNLOAD would, and 5b decision 5 gave the namespace role no lake reach at all, so the day
# one is granted is the day an egress rule is written with a named destination - the S3 gateway
# endpoint's prefix list - rather than `0.0.0.0/0` inherited from a default group.
