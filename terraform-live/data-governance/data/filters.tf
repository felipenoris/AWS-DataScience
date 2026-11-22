# Stage 11 pass 1, steps 2.1a and 2.1b - the data cells filters and their cross-account grants.
#
# A data cells filter is a named object on one table: a column list and a PartiQL row expression,
# granted with SELECT alone, because filters apply to reads only. These filters are the explicit
# restricted grant of docs/GOVERNANCE.md "Grants", narrowed: the default share in shares.tf carries
# `classification IN (public, internal)`, so `counterparty` reaches a consumer only through a grant
# made in two hops. This account grants SELECT through the filter to the consumer account with the
# grant option, and that account's data lake administrator regrants it to one local principal
# (terraform-modules/consumer-data, `data_cells_filter_grants`).
#
# One mechanism per dimension: what the LF-Tag ontology expresses (counterparty is restricted) stays
# on the tag-scoped grants of shares.tf; a filter carries only what the ontology cannot, a column
# subset or a row predicate within one table.
#
# Constraints from AWS's data filtering limitations page (read 2026-10-18, docs/REFERENCES.md):
#   - a column filter granted with the grant option takes an include list, never an exclude list,
#     so every filter here names its columns, and a column added to the table joins none of them;
#   - an all-rows grant prevails over every row filter the same principal holds, so a row filter
#     narrows nothing for a principal that also holds an unfiltered SELECT on the table;
#   - when a row filter is granted to an account and regranted inside it, the principal's predicate
#     is the intersection of the account's and any predicate granted to the principal directly.
#
# Nothing is created while `filter_shares` is empty: which principal in a consumer account reads a
# filter is the user's choice, recorded in the Stage 11 log on 2026-10-18, and a filter that no grant
# names is an object nobody reads.

locals {
  sample_trades_columns = ["trade_id", "trade_date", "instrument", "quantity", "price", "counterparty"]

  # The filters, by name. The name is a contract with ./aws/dlp.py DP-2: awsds-flt-<table>-<what>.
  data_cells_filters = {
    # Column restriction: the restricted column with the trade's identity and date, without its
    # quantity and price. All rows.
    "awsds-flt-sample_trades-counterparty" = {
      database_name = aws_glue_catalog_database.curated.name
      table_name    = aws_glue_catalog_table.sample_trades.name
      column_names  = ["trade_id", "trade_date", "instrument", "counterparty"]
      row_filter    = null
    }

    # Row restriction: every column, the restricted one included, for trade ids up to 6. The
    # predicate is on trade_id because PartiQL row filters take STRING, the integer and floating-point
    # types, DECIMAL, BOOLEAN and STRUCT, and not DATE (AWS's PartiQL support page). The same page
    # says a row filter on a table that contains an unsupported type is an error, and this table
    # carries `trade_date date`: the first apply decides which reading holds. The 12 rows' ids are
    # recorded nowhere, so 2.3 compares the filtered count with an unfiltered count of the same
    # predicate, and a count of 0 or 12 means the predicate is chosen again.
    "awsds-flt-sample_trades-trade-id-le-6" = {
      database_name = aws_glue_catalog_database.curated.name
      table_name    = aws_glue_catalog_table.sample_trades.name
      column_names  = local.sample_trades_columns
      row_filter    = "trade_id <= 6"
    }
  }

  # Step 2.1b: the filters each consumer account receives, keyed like local.consumer_accounts.
  # Empty until the user names the reading principal in that account.
  filter_shares = {}

  filter_grants = merge([
    for consumer, names in local.filter_shares : {
      for name in names : "${consumer}/${name}" => { consumer = consumer, filter = name }
    }
  ]...)

  filters_in_use = toset([for g in values(local.filter_grants) : g.filter])
}

resource "aws_lakeformation_data_cells_filter" "this" {
  for_each = { for name, f in local.data_cells_filters : name => f if contains(local.filters_in_use, name) }

  table_data {
    table_catalog_id = data.aws_caller_identity.current.account_id
    database_name    = each.value.database_name
    table_name       = each.value.table_name
    name             = each.key
    column_names     = each.value.column_names

    row_filter {
      filter_expression = each.value.row_filter

      dynamic "all_rows_wildcard" {
        for_each = each.value.row_filter == null ? [1] : []
        content {}
      }
    }
  }
}

# The first hop. The grant option is what lets the consumer's administrator pass the filter on; it
# reaches principals in that account only, never another account (shares.tf's note).
resource "aws_lakeformation_permissions" "filter_share" {
  for_each = local.filter_grants

  principal                     = local.consumer_accounts[each.value.consumer]
  permissions                   = ["SELECT"]
  permissions_with_grant_option = ["SELECT"]

  data_cells_filter {
    table_catalog_id = data.aws_caller_identity.current.account_id
    database_name    = aws_lakeformation_data_cells_filter.this[each.value.filter].table_data[0].database_name
    table_name       = aws_lakeformation_data_cells_filter.this[each.value.filter].table_data[0].table_name
    name             = aws_lakeformation_data_cells_filter.this[each.value.filter].table_data[0].name
  }
}
