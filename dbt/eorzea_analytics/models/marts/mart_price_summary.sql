SELECT
    l.item_id,
    n.item_name,
    l.world_id,
    w.world_name,
    l.is_hq,
    COUNT(*) AS listing_count,
    AVG(l.price_per_unit) AS avg_price,
    MIN(l.price_per_unit) AS min_price,
    MAX(l.price_per_unit) AS max_price,
    SUM(l.quantity) AS total_quantity
FROM {{ ref('stg_listings') }} l
LEFT JOIN {{ ref('item_names') }} n ON l.item_id = n.item_id
LEFT JOIN {{ ref('world_names') }} w ON l.world_id = w.world_id
GROUP BY l.item_id, n.item_name, l.world_id, w.world_name, l.is_hq
