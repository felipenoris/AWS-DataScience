# The instance role - Session Manager and nothing else, plus one log group.
#
# THERE IS NO PORT 22 ANYWHERE IN THIS DESIGN (step 3), so this role is the shell: the AL2023
# AMI ships the SSM agent, and with AmazonSSMManagedInstanceCore it registers itself and
# `aws ssm start-session` works over the agent's OUTBOUND connection - no inbound rule, no
# key pair, no bastion. Verification (iii) asks whether that holds with NO ssm* interface
# endpoint anywhere in the account, which is the state this account is in: egress/ is [E] and
# may be down, so the agent's path is the public subnet's internet gateway.
#
# THE BOUNDARY IS null AND IT IS A DECISION, not an omission - the iam-role module makes it
# unforgettable by requiring the argument (Stage 2 step 7). This is an EC2 service role
# authored by the identity that authors boundaries, the same case Stage 3's flow-log role
# recorded (Lesson 18): no non-administrator can create or influence it, and the boundary
# object itself does not exist yet (Stage 2 decision 4).

module "role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "awsds-${var.env}-vpn"
  description = "WireGuard host - Session Manager access and its own handshake log group (Stage 4)"

  permissions_boundary = null

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowEc2Service"
        Effect    = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonSSMManagedInstanceCore",
  ]

  inline_policies = {
    # THE CLOUDWATCH AGENT, SCOPED TO ONE LOG GROUP - the same shape Stage 3's flow-log role
    # used, and for the same reason: CloudWatchAgentServerPolicy is the documented answer and
    # it carries cloudwatch:PutMetricData on * plus ssm:GetParameter on a whole prefix, none
    # of which this agent needs. It ships one file to one group (step 7.2).
    #
    # logs:CreateLogGroup IS DELIBERATELY ABSENT. Terraform owns that group because Terraform
    # owns its retention (observability.tf); an agent allowed to create it would recreate it
    # WITHOUT retention after a manual delete, and an unbounded log group is a bill nobody
    # reads. The agent finds the group already there and only opens a stream in it.
    "ship-handshake-log" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid    = "WriteHandshakeLogStreams"
          Effect = "Allow"
          Action = [
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:DescribeLogStreams",
          ]
          Resource = "${aws_cloudwatch_log_group.handshakes.arn}:*"
        }
      ]
    })

    # THE BOOT FETCH, SCOPED TO ONE ARN (step 2.2a; decision 4, third review). One action on
    # one secret: the containment lives ON the secret - its resource policy denies
    # GetSecretValue to every principal in the account except this role and
    # InfrastructureAccess - and this allow is one of that deny's two carve-outs. No kms:
    # permission is needed: the secret rides the aws/secretsmanager managed key, which
    # authorizes through the service for exactly the principals IAM and the resource policy
    # admit.
    "fetch-host-key" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid      = "FetchHostKeyAtFirstBoot"
          Effect   = "Allow"
          Action   = "secretsmanager:GetSecretValue"
          Resource = var.host_key_secret_arn
        }
      ]
    })
  }
}

resource "aws_iam_instance_profile" "this" {
  name = "awsds-${var.env}-vpn"
  role = module.role.role_name
}
