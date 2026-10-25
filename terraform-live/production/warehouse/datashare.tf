# The governed schema's datashare toward the lake's catalog (Stage 9 step 9.5, decision 5's shape
# (ii), decision 14): the producer's half, the authorization of the lake's Data Catalog as a consumer.
#
# The datashare itself, `trades_lf` in `governed`, is SQL run as the namespace's admin through the Data
# API (9.5 step 1: CREATE DATASHARE, ADD SCHEMA, INCLUDENEW, GRANT USAGE ... VIA DATA CATALOG), so no
# state holds it and this resource names it by ARN, which carries the namespace id. The consumer's
# half (the association, the registration, the federated database) is data-governance/data/'s. The
# consumer identifier is `DataCatalog/<the lake's account>`, the id read from production/data/'s state
# and never pasted (Lesson 14). Writes stay off, and `allow_writes` is left undeclared: the provider
# reads the attribute back as unset, so a declared `false` plans a replacement of the authorization
# (read 2026-10-25); a federated database takes no write anyway.
#
# The provider keeps this resource only while the identifier is listed `AUTHORIZED` on the share
# (9.5's first mismatch): a producer-side revoke (verification xxiv) makes the next plan re-create it,
# which is the reading, not a defect.

locals {
  trades_lf_datashare_arn = "arn:aws:redshift:${var.region}:${data.aws_caller_identity.current.account_id}:datashare:${aws_redshiftserverless_namespace.this.namespace_id}/trades_lf"
}

resource "aws_redshift_data_share_authorization" "trades_lf_to_lake" {
  data_share_arn      = local.trades_lf_datashare_arn
  consumer_identifier = "DataCatalog/${data.terraform_remote_state.data.outputs.lake_catalog_id}"
}

# The adoption of the authorization of 2026-10-25 01:52 UTC, made by hand (Stage 9's log). The import
# block reads the share's ARN from the account's own list rather than from the namespace resource, so
# its id is known at plan time; the block and the data source go in the commit after the apply.
data "aws_redshift_data_shares" "this" {}

import {
  to = aws_redshift_data_share_authorization.trades_lf_to_lake
  id = "${one([for s in data.aws_redshift_data_shares.this.data_shares : s.data_share_arn if endswith(s.data_share_arn, "/trades_lf")])},DataCatalog/${data.terraform_remote_state.data.outputs.lake_catalog_id}"
}
