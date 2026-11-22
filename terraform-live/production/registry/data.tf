# What this slice reads and does not own.
#
# Two identity reads keep an account id out of a tracked file: this account, for the key policy's
# own delegation statement, and the consumers, for every grant below: Sandbox for both maps since
# Stage 7 decision 7, Staging for the application images since Stage 8 step 3.0. The partition is read for the same reason a region literal is forbidden - an ARN
# built from `aws:` by hand is a portability assumption nobody chose.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_caller_identity" "sandbox" {
  provider = aws.sandbox
}

data "aws_caller_identity" "staging" {
  provider = aws.staging
}
