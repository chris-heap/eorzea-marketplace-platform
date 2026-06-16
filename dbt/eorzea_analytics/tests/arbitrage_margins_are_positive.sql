-- Arbitrage opportunities should have positive profit margins
SELECT *
FROM {{ ref('mart_cross_world_arbitrage') }}
WHERE profit_margin_pct < 0
