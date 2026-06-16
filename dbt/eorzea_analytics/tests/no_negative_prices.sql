{{ config(severity='warn') }}
-- Prices should never be negative on the market board
SELECT *
FROM {{ ref('stg_listings') }}
WHERE price_per_unit < 0
