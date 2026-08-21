# What this slice reads and does not own.
#
# THREE IDENTITY READS, EACH KEEPING AN ACCOUNT ID OUT OF A TRACKED FILE: this account (for
# the key policy's own delegation statement) and the two consumers (for every grant below).
# The partition is read for the same reason a region literal is forbidden - an ARN built from
# `aws:` by hand is a portability assumption nobody chose.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_caller_identity" "sandbox" {
  provider = aws.sandbox
}

data "aws_caller_identity" "development" {
  provider = aws.development
}
