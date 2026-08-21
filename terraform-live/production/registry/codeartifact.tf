# CODEARTIFACT (Stage 7 step 5.3, the 5.a half) - the package path design B reads from when
# there is no NAT at all (D5(B), INT-02's consumer half, proven at Stage 6 pass 4).
#
# ONE DOMAIN, TWO REPOSITORIES, ONE EXTERNAL CONNECTION EACH. A CodeArtifact repository may
# carry at most one external connection, which is why `pypi` and `crates` are two repositories
# rather than one with two upstreams.
#
#   pypi     public:pypi        - Python, the ecosystem every notebook uses
#   crates   public:crates-io   - Cargo, GA 2024-06 (open question 5's note, confirmed)
#
# JULIA AND R ARE DELIBERATELY UNCOVERED. CodeArtifact has no external connection for either,
# so under design B they arrive baked into the dev-env image (docs/plan/architecture.md 4.3) -
# which is a constraint on the image, not a gap in this slice, and Stage 6's comparison prices
# it.
#
# THE FIRST FETCH OF ANY PACKAGE REACHES THE PUBLIC INTERNET FROM CODEARTIFACT'S SIDE, not
# from the consumer's - that is the whole point of the design: Production's NAT is not
# involved either, because the external connection is the service's own egress. What the
# consumer needs is the interface endpoints (Stage 3 step 8.4) and the grants below.

resource "aws_codeartifact_domain" "packages" {
  domain         = "awsds-${var.env}-packages"
  encryption_key = module.registry_key.key_arn
}

resource "aws_codeartifact_repository" "pypi" {
  domain      = aws_codeartifact_domain.packages.domain
  repository  = "pypi"
  description = "PyPI through CodeArtifact - the design B package path for Python."

  external_connections {
    external_connection_name = "public:pypi"
  }
}

resource "aws_codeartifact_repository" "crates" {
  domain      = aws_codeartifact_domain.packages.domain
  repository  = "crates"
  description = "crates.io through CodeArtifact - Cargo, GA 2024-06 (open question 5)."

  external_connections {
    external_connection_name = "public:crates-io"
  }
}

# ------------------------------------------------------- the consumer-facing policies (5.4)
#
# TWO LAYERS, AND BOTH ARE NEEDED - this is Lesson 28 in CodeArtifact's own shape:
#
#   the DOMAIN policy       who may mint an authorization token and resolve a repository
#                           endpoint. Without it a consumer cannot authenticate at all.
#   the REPOSITORY policy   who may actually read packages out of one. Without it a consumer
#                           authenticates and then reads nothing.
#
# READ ONLY, IN BOTH. Nothing outside this account publishes a package: the promotion chain
# publishes from a pipeline in Production (Stage 8), and an Interactive account that could
# push into the shared repository would be a supply-chain write from the least-governed side
# of the estate.

resource "aws_codeartifact_domain_permissions_policy" "packages" {
  domain = aws_codeartifact_domain.packages.domain

  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowConsumerAccountsToAuthenticate"
        Effect    = "Allow"
        Principal = { AWS = local.consumer_account_arns }
        Action = [
          "codeartifact:GetAuthorizationToken",
          "codeartifact:GetRepositoryEndpoint",
          "codeartifact:ListRepositoriesInDomain",
        ]
        Resource = "*"
      },
    ]
  })
}

resource "aws_codeartifact_repository_permissions_policy" "pypi" {
  domain     = aws_codeartifact_domain.packages.domain
  repository = aws_codeartifact_repository.pypi.repository

  policy_document = local.codeartifact_read_policy
}

resource "aws_codeartifact_repository_permissions_policy" "crates" {
  domain     = aws_codeartifact_domain.packages.domain
  repository = aws_codeartifact_repository.crates.repository

  policy_document = local.codeartifact_read_policy
}
