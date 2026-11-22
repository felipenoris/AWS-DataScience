-- An Iceberg table Athena creates under the product database's location. native_drop: the adapter
-- drops a table by an Athena statement and skips its own S3 deletion before a create, so the caller
-- never touches the table's files.
{{ config(materialized='table', table_type='iceberg', native_drop=true) }}

select
    desk,
    round(sum(price * quantity), 2) as notional
from {{ source('app_dbt', 'trades') }}
group by desk
