{{ config(severity='warn') }}
-- Sale total should equal price_per_unit * quantity (within rounding tolerance)
SELECT *
FROM {{ ref('stg_sales') }}
WHERE ABS(total - (price_per_unit * quantity)) > 1
