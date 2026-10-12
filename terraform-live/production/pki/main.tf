# production/pki/ - the internal CA (Stage 7 step 2, D15 phase 1, D36): one root, two leaves.
#
# ACM cannot issue for a `.internal` name and Private CA is over the D12 ceiling, so the trust chain
# is this slice's. The root's private key lives in this state file and nowhere else; it is never an
# output (D36 section 2: the key policy on the state's own CMK is the control, and the state key is
# the second one production/bootstrap/ holds). The leaves' private keys are outputs of the tls
# provider too, but they leave this slice only through Secrets Manager (publish.tf), read by the
# GitLab host's role at boot - never through user data, which anyone holding
# ec2:DescribeInstanceAttribute reads.
#
# No revocation path exists (D36): no CRL, no OCSP. A compromised leaf is replaced by tainting its
# key here and re-issuing; a compromised root is a rebuild of every client surface (INT-19). What
# watches the root is detective and listed in D36 section 5, and the first of its items is the
# fingerprint recorded in docs/log/log-stage-07-gitlab-runners-ecr.md at this slice's first apply.
#
# The leaves and the names they serve (D15 as amended 2026-09-05):
#
#   gitlab   gitlab.awsds.internal           GitLab's nginx (tooling/, step 1.3)
#   pages    *.awsds-pages.internal          GitLab Pages' nginx, a wildcard on its own apex (D36:
#            + awsds-pages.internal          user-published content never shares a registrable
#                                            parent with the platform's names)
#
# proxy.awsds.internal gets no leaf: Squid listens on plain 3128 (6c 4.8) and nothing would
# validate it. A third leaf is issued the day the proxy gains a TLS listener, and not before.
#
# Lifetimes: the root ten years, the leaves 375 days with `early_renewal_hours` of 30 days, so a
# plan run inside the last month of a leaf's life proposes its replacement - the re-issue is an
# apply here plus the host-side refresh in runbooks/gitlab.md, and ./aws/supplychain.py SC-8 reads
# the runway from the published certificate.

# ---------------------------------------------------------------------------------- the root

resource "tls_private_key" "root" {
  algorithm   = "ECDSA"
  ecdsa_curve = "P384"
}

resource "tls_self_signed_cert" "root" {
  private_key_pem = tls_private_key.root.private_key_pem

  subject {
    common_name  = "awsds internal root CA"
    organization = "AWS-DataScience"
  }

  is_ca_certificate     = true
  validity_period_hours = var.root_validity_hours
  early_renewal_hours   = 0

  allowed_uses = [
    "cert_signing",
    "crl_signing",
    "digital_signature",
  ]
}

# -------------------------------------------------------------------------------- the leaves
#
# One map, two leaves, so the request, the signature, the parameter, the object and the secret are
# written once and the two names cannot be configured differently by accident (Lesson 33).

locals {
  leaves = {
    gitlab = {
      common_name = "gitlab.awsds.internal"
      dns_names   = ["gitlab.awsds.internal"]
      file_stem   = "gitlab.awsds.internal"
    }
    pages = {
      common_name = "*.awsds-pages.internal"
      dns_names   = ["*.awsds-pages.internal", "awsds-pages.internal"]
      file_stem   = "awsds-pages.internal"
    }
  }
}

resource "tls_private_key" "leaf" {
  for_each = local.leaves

  algorithm   = "ECDSA"
  ecdsa_curve = "P256"
}

resource "tls_cert_request" "leaf" {
  for_each = local.leaves

  private_key_pem = tls_private_key.leaf[each.key].private_key_pem
  dns_names       = each.value.dns_names

  subject {
    common_name  = each.value.common_name
    organization = "AWS-DataScience"
  }
}

resource "tls_locally_signed_cert" "leaf" {
  for_each = local.leaves

  cert_request_pem   = tls_cert_request.leaf[each.key].cert_request_pem
  ca_private_key_pem = tls_private_key.root.private_key_pem
  ca_cert_pem        = tls_self_signed_cert.root.cert_pem

  validity_period_hours = var.leaf_validity_hours
  early_renewal_hours   = 720

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]
}
