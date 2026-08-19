# What the module reads about the account it is being applied into. Both are ARN parts; every
# identifier that crosses an account line arrives as a VARIABLE instead, resolved live by the
# caller's aliased provider (aws/INDEX.md rule 1).

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}
