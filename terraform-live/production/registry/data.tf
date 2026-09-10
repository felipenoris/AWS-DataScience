# What this slice reads and does not own.
#
# Three identity reads keep an account id out of a tracked file: this account, for the key policy's
# own delegation statement, and the two consumers, for every grant below. The partition is read for
# the same reason a region literal is forbidden - an ARN built from `aws:` by hand is a portability
# assumption nobody chose.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_caller_identity" "sandbox" {
  provider = aws.sandbox
}

data "aws_caller_identity" "staging" {
  provider = aws.staging
}
