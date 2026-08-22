# ecr-repo - one ECR repository with the three settings Stage 7 step 5.1 makes non-negotiable,
# plus the lifecycle policy that keeps stored bytes from growing without bound.
#
# THE THREE SETTINGS, AND WHY EACH IS A MODULE PROPERTY RATHER THAN A CALLER'S CHOICE:
#
#   IMMUTABLE tags        Stage 8's promotion gate says "tags are immutable" and the whole
#                         approved-digest chain stands on it. A mutable tag means the digest a
#                         steward approved and the digest a project pulls can differ with
#                         nothing to read afterwards. Not a variable: a caller that wanted it
#                         off would be reopening Stage 8's design, not configuring a module.
#   scan on push (basic)  free, and it is what Stage 8's gate reads through
#                         DescribeImageScanFindings. Enhanced scanning is Stage 7 decision 2,
#                         measured and deferred to Stage 11 (principle 9) - a different
#                         service (Inspector), not a flag here.
#   KMS encryption        the slice's own CMK. AES256 is the default and would be free; the
#                         key exists so that "who may pull an image" and "who may decrypt it"
#                         are two grants that have to agree (Lesson 28), which is what makes
#                         the consumer list below a control rather than a courtesy.
#
# WHAT THIS MODULE DOES NOT DO: pull-through cache rules (Stage 7 step 5.2, 5.b - they are
# registry-scoped, not repository-scoped) and the registry-level permission policy the cached
# repositories need. Both are the caller's, and neither exists before Stage 7.

resource "aws_ecr_repository" "this" {
  name = var.name

  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = var.kms_key_arn
  }

  tags = {
    Name = var.name
  }
}

# ------------------------------------------------------------------- the lifecycle policy
#
# TWO RULES, AND THE ORDER MATTERS: ECR evaluates by rulePriority ascending and an image is
# acted on by the FIRST rule that matches, so the untagged rule has to come first or the
# tagged-count rule would never see the images it is meant to ignore.
#
# `tagPatternList` with a single "*" is the documented way to say "any tagged image" without
# enumerating prefixes; `tagStatus = "any"` would also catch untagged ones and make rule 1
# unreachable.
#
# REVISION TRIGGER - RULE 2 COUNTS EVERY FLAVOUR TOGETHER, AND THAT BECOMES WRONG THE DAY A
# SECOND ONE EXISTS (recorded 2026-08-22, when Stage 6 step 5.0 settled the image tag
# convention `<flavour>-v<semver>` - one copy in docs/SMUS.md, "Custom images (BYOI)").
# `imageCountMoreThan` over `["*"]` keeps the most recent N across ALL tags, so once
# `gpu-v…` images share a repository with `default-v…`, a burst of pushes on one flavour
# expires the other's images - which nothing else would have touched and which cost far
# more to rebuild. The fix is one rule PER FLAVOUR, and it is cheap precisely because the
# flavour is the tag's PREFIX: `tagPrefixList = ["gpu-"]` selects it without a wildcard.
# This comment is the trigger's only home - the module has no README, and a note written
# only in the stage that noticed it never reaches the hand that adds the second flavour.

resource "aws_ecr_lifecycle_policy" "this" {
  repository = aws_ecr_repository.this.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Untagged images are superseded layers or a failed push - stored bytes nothing references."
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = var.untagged_expiry_days
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Keep the most recent tagged images; older ones are reproducible from their Dockerfile and their git tag."
        selection = {
          tagStatus      = "tagged"
          tagPatternList = ["*"]
          countType      = "imageCountMoreThan"
          countNumber    = var.tagged_image_count
        }
        action = { type = "expire" }
      },
    ]
  })
}

# ------------------------------------------------------------- the cross-account pull grant
#
# ONE STATEMENT, READ-ONLY, ENUMERATED. The four actions are exactly what `docker pull` needs
# against a repository; `ecr:GetAuthorizationToken` is deliberately absent because it is
# REGISTRY-scoped and cannot be granted by a repository policy at all - the consumer's own IAM
# carries it (docs/plan/conventions.md 6 says so in as many words).
#
# THE COUNT GUARD: an empty list means no cross-account reader, and the policy resource is not
# created at all. Writing a policy with an empty Principal list would be a document that denies
# by having no allow - the same thing, spelled in a way a reader has to think about.

resource "aws_ecr_repository_policy" "pull" {
  count = length(var.pull_principal_arns) > 0 ? 1 : 0

  repository = aws_ecr_repository.this.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowConsumerAccountsToPull"
        Effect    = "Allow"
        Principal = { AWS = var.pull_principal_arns }
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:DescribeImages",
        ]
      },
    ]
  })
}
