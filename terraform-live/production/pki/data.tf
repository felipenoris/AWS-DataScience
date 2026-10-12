# What this slice reads and does not own: the identity reads every statement here is built from,
# and foundation/'s state for the bucket the certificates are published into (step 2.3) and the key
# that encrypts the copies there. Same-account, so no profile - a profile literal in a .tf file is
# forbidden (Lesson 14).

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}
