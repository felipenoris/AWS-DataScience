# The governed warehouse's share into this catalog (Stage 9 step 9.5, decision 5's shape (ii),
# decision 14): Production's datashare `trades_lf` associated with this account's Data Catalog and
# mapped to the federated database `governed_trades`, which the lake's TBAC grants reach as they reach
# `curated` (Sandbox's account read it through its tag grants alone, 9.7). The producer's half, the
# authorization, is production/warehouse/datashare.tf.
#
# Two of this account's three objects are Terraform's: the association and the database. The
# registration of the datashare's ARN with Lake Formation is not: aws_lakeformation_resource has no
# importer (its source at provider v6.60.0 declares none), deregistering is denied by the Data OU SCP,
# and a second registration of the same ARN is a conflict, so the registration of 2026-10-25 01:52 UTC,
# with no role, stays by hand. The two LF-Tag assignments (`layer=curated` on the database,
# `classification=internal` on the table `trades.trades_notional`) stay by hand for the same reason:
# aws_lakeformation_resource_lf_tags documents no import. Both are README rows and ./aws/datalake.py's.
#
# The datashare's ARN carries Production's namespace id, which no state here holds, so the data source
# lists the shares this account sees and the share is the one ending in its name. The list reads null,
# not empty, when this account sees no share, so after a producer-side revoke every plan of this slice
# fails at the `for` below until the share is granted and authorized again (verification xxiv,
# 2026-10-26). The database's
# `create_table_default_permission` is omitted: the account's default list is empty (Recipe D), and the
# API refuses a description beside a federation source (read 2026-10-25).

data "aws_redshift_data_shares" "visible" {}

locals {
  trades_lf_datashare_arn = one([
    for share in data.aws_redshift_data_shares.visible.data_shares : share.data_share_arn
    if endswith(share.data_share_arn, "/trades_lf")
  ])
  catalog_arn = "arn:${data.aws_partition.current.partition}:glue:${var.region}:${data.aws_caller_identity.current.account_id}:catalog"
}

resource "aws_redshift_data_share_consumer_association" "trades_lf" {
  data_share_arn = local.trades_lf_datashare_arn
  consumer_arn   = local.catalog_arn
}

resource "aws_glue_catalog_database" "governed_trades" {
  name = "governed_trades"

  federated_database {
    connection_name = "aws:redshift"
    identifier      = local.trades_lf_datashare_arn
  }

  depends_on = [aws_lakeformation_data_lake_settings.this, aws_redshift_data_share_consumer_association.trades_lf]
}

# Both adopted into this state on 2026-10-25 from the objects made by hand (Stage 9 9.5, the log); the
# provider's five default tags landed on the database at the adoption.
