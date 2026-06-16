{{ config(severity='warn') }}
-- Every listing must have at least 1 item for sale
SELECT *
FROM {{ ref('stg_listings') }}
WHERE quantity <= 0
