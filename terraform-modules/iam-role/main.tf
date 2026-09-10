# iam-role - a role whose permissions boundary is a required argument with no default (Stage 2
# step 7), so a role without one is a caller that wrote `permissions_boundary = null` and meant
# it. The IAM convention (docs/plan/conventions.md) is enforced by the type checker rather than
# by review. The first legitimate null is Stage 3's flow-log delivery role, created by the
# identity that authors boundaries and unconstrained by them either way (Lesson 18).

resource "aws_iam_role" "this" {
  name                 = var.name
  description          = var.description
  assume_role_policy   = var.assume_role_policy
  permissions_boundary = var.permissions_boundary

  tags = {
    Name = var.name
  }
}

resource "aws_iam_role_policy" "inline" {
  for_each = var.inline_policies

  name   = each.key
  role   = aws_iam_role.this.id
  policy = each.value
}

resource "aws_iam_role_policy_attachment" "managed" {
  for_each = toset(var.managed_policy_arns)

  role       = aws_iam_role.this.name
  policy_arn = each.value
}
