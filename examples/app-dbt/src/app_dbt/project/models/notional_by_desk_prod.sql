-- The notional each desk traded in Production, read through trades_notional, the resource link the
-- project's subscription to the listing trades-notional writes in the product database. Athena resolves
-- the link to Production's table, and Lake Formation vends the read under the subscription's grant. No
-- deployment project holds the link, so no release carries this model. An Iceberg table dropped by an
-- Athena statement, as notional_by_desk.
{{ config(materialized='table', table_type='iceberg', native_drop=true) }}

select
    desk,
    round(sum(notional), 2) as notional
from {{ source('app_dbt', 'trades_notional') }}
group by desk
