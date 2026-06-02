WITH hq_prices AS (
    SELECT
        item_id,
        world_id,
        COUNT(*) AS listing_count,
        AVG(price_per_unit) AS avg_price,
        MIN(price_per_unit) AS min_price,
        SUM(quantity) AS total_quantity
    FROM {{ ref('stg_listings') }}
    WHERE is_hq = true
    GROUP BY item_id, world_id
),

nq_prices AS (
    SELECT
        item_id,
        world_id,
        COUNT(*) AS listing_count,
        AVG(price_per_unit) AS avg_price,
        MIN(price_per_unit) AS min_price,
        SUM(quantity) AS total_quantity
    FROM {{ ref('stg_listings') }}
    WHERE is_hq = false
    GROUP BY item_id, world_id
)

SELECT
    h.item_id,
    i.item_name,
    h.world_id,
    w.world_name,
    h.avg_price AS hq_avg_price,
    nq.avg_price AS nq_avg_price,
    h.listing_count AS hq_listings,
    nq.listing_count AS nq_listings,
    ROUND((h.avg_price - nq.avg_price) / nq.avg_price * 100, 2) AS hq_premium_pct
FROM hq_prices h
JOIN nq_prices nq ON h.item_id = nq.item_id AND h.world_id = nq.world_id
LEFT JOIN {{ ref('item_names') }} i ON h.item_id = i.item_id
LEFT JOIN {{ ref('world_names') }} w ON h.world_id = w.world_id
WHERE nq.avg_price > 0
ORDER BY hq_premium_pct DESC