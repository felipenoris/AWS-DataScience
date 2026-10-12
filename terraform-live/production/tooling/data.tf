# What this slice reads and does not own: three remote states and one AMI parameter. Every read is
# same-account, so none carries a profile - a profile literal in a .tf file is forbidden (Lesson 14).
#
# Not read: egress/. It is [E], and a destroyed slice's outputs fail the plan by name - which is
# the reason the bypass list is a dated literal in variables.tf rather than egress/'s output (1.3).

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

# foundation/: the VPC, the private subnet, the two zones, GitLab's [P] anchors (1.1).
data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

# networking/: the WireGuard host's security group, which 1.2's HTTPS rule names. A same-account,
# cross-VPC group reference over the peering - the host masquerades every tunnel packet that is not
# bound for the proxy (6c pass 8, 6g), so a laptop reaches this host as the WireGuard host's
# address, and the group is the source that names it.
data "terraform_remote_state" "networking" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/networking/terraform.tfstate"
    region = var.region
  }
}

# pki/: the leaf keys' secret ARNs and the published certificates' parameters (steps 2.3, 2.4).
data "terraform_remote_state" "pki" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/pki/terraform.tfstate"
    region = var.region
  }
}

# The AMI: Amazon Linux 2023 arm64 - the Omnibus package has shipped an arm64 build for AL2023 since
# GitLab 16.3.0 (docs/REFERENCES.md), and a t4g is a fifth cheaper than the t3 of the same memory
# (D8). Resolved from the public parameter and then HELD (main.tf, ignore_changes): an SSM-resolved
# AMI replaced a [D] host on its next apply at 6g, and a replaced GitLab moves its address and
# empties its root volume. The data volume would survive it; the first boot would not re-run.
data "aws_ssm_parameter" "al2023_arm64" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}
