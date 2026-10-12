# cache.tf - the pull-through cache (Stage 7 step 5.2, the 5.b half).
#
# Under design B a public image reaches a private build in one of two ways: through the proxy, on the
# `open` build plane (measured at 6c 5.8), or through these rules, which have ECR fetch the upstream
# itself and keep a scanned copy. The cache is for what a build should not fetch twice or should
# find scanned, not for reach - every build host can pull a public image through the proxy.
#
# Three credential-free upstreams. Docker Hub is absent: it needs an `ecr-pullthroughcache/...`
# Secrets Manager secret (ECR's documented prefix, an exception to the awsds- convention) and is
# added the day a build needs an image that lives nowhere else.
#
# The documented traps, each with its control here:
#
#   immutability must not reach the cache repositories   an immutable tag blocks the cache's own
#                                                        update, so the creation templates below say
#                                                        MUTABLE where every repository this slice
#                                                        authors says IMMUTABLE (ecr-repo module)
#   the first pull "may require a route to the internet"  the reading is the deliverable (5.2,
#                                                        verification vii): the upstreams need no
#                                                        credential and their pulls are initiated
#                                                        by AWS addresses, so the requirement may
#                                                        not bite. If it does, the fallbacks are
#                                                        ranked in the stage file, a NAT gateway
#                                                        last
#   the cached repositories are created by ECR           so a consumer grant rides on the
#                                                        registry-level permission policy, never on
#                                                        a per-repository one. No cross-account
#                                                        consumer exists today: the runner pulls in
#                                                        the registry's own account, by its identity
#                                                        policy (6.1), so no registry policy is
#                                                        written yet
#
# The puller needs `ecr:BatchImportUpstreamImage` on the cache prefix, and `ecr:CreateRepository`
# for a repository that does not exist yet - runners/ grants both, scoped to the three prefixes.

locals {
  cache_upstreams = {
    "ecr-public" = "public.ecr.aws"
    "k8s"        = "registry.k8s.io"
    "quay"       = "quay.io"
  }
}

resource "aws_ecr_pull_through_cache_rule" "this" {
  for_each = local.cache_upstreams

  ecr_repository_prefix = each.key
  upstream_registry_url = each.value
}

# One creation template per prefix: ECR creates `<prefix>/<upstream path>` on the first pull and
# applies this. MUTABLE tags (the trap above), the module's two-rule lifecycle so a cache never
# grows without bound, and no repository policy. AES256 rather than the slice's key, deliberately:
# a cached image is a public upstream's bytes, so "who may pull" and "who may decrypt" are not two
# questions here (the argument that gives every repository this slice authors the CMK), and a CMK
# in a creation template needs a custom role ECR assumes to create the repository - a second
# principal for no confidentiality.
resource "aws_ecr_repository_creation_template" "cache" {
  for_each = local.cache_upstreams

  prefix      = each.key
  description = "Pull-through cache of ${each.value} - created by ECR on first pull (Stage 7 step 5.2)"
  applied_for = ["PULL_THROUGH_CACHE"]

  image_tag_mutability = "MUTABLE"

  encryption_configuration {
    encryption_type = "AES256"
  }

  lifecycle_policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Untagged cached layers nothing references."
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 14
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Keep the most recent cached tags; an expired one is fetched again on the next pull."
        selection = {
          tagStatus      = "tagged"
          tagPatternList = ["*"]
          countType      = "imageCountMoreThan"
          countNumber    = 30
        }
        action = { type = "expire" }
      },
    ]
  })

  resource_tags = {
    Project     = var.project
    Environment = var.environment_tag
    ManagedBy   = "terraform"
    Owner       = var.owner
    CostCenter  = "stage-07"
  }
}
