-- HQ premium calculation requires both HQ and NQ prices to be positive
SELECT *
FROM {{ ref('mart_hq_premium') }}
WHERE hq_avg_price <= 0 OR nq_avg_price <= 0
