WITH price_bounds AS (
    SELECT
        item_id,
        is_hq,
        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY price_per_unit) AS p05,
        PERCENTILE_CONT(0.85) WITHIN GROUP (ORDER BY price_per_unit) AS p85
    FROM {{ ref('stg_listings') }}
    GROUP BY item_id, is_hq
    HAVING COUNT(*) >= 10
),

filtered_listings AS (
    SELECT
        l.item_id,
        l.world_id,
        l.is_hq,
        l.price_per_unit
    FROM {{ ref('stg_listings') }} l
    JOIN price_bounds b ON l.item_id = b.item_id AND l.is_hq = b.is_hq
    WHERE l.price_per_unit BETWEEN b.p05 AND b.p85
),

world_prices AS (
    SELECT
        item_id,
        world_id,
        is_hq,
        MIN(price_per_unit) AS min_price
    FROM filtered_listings
    GROUP BY item_id, world_id, is_hq
)

SELECT
    wp.item_id,
    n.item_name,
    wp.world_id,
    wn.world_name,
    wp.is_hq,
    wp.min_price,
    MIN(wp.min_price) OVER (PARTITION BY wp.item_id, wp.is_hq) AS cheapest_price,
    MAX(wp.min_price) OVER (PARTITION BY wp.item_id, wp.is_hq) AS priciest_price,
    ROUND(
        (MAX(wp.min_price) OVER (PARTITION BY wp.item_id, wp.is_hq) - MIN(wp.min_price) OVER (PARTITION BY wp.item_id, wp.is_hq))
        / MIN(wp.min_price) OVER (PARTITION BY wp.item_id, wp.is_hq) * 100, 2
    ) AS profit_margin_pct
FROM world_prices wp
LEFT JOIN {{ ref('item_names') }} n ON wp.item_id = n.item_id
LEFT JOIN {{ ref('world_names') }} wn ON wp.world_id = wn.world_id
WHERE wp.min_price > 0
ORDER BY profit_margin_pct DESC

