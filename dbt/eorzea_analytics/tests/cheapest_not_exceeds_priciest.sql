-- The cheapest cross-world price should never exceed the priciest
SELECT *
FROM {{ ref('mart_cross_world_arbitrage') }}
WHERE cheapest_price > priciest_price
