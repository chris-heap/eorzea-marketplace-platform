SELECT
    s.item_id,
    n.item_name,
    s.world_id,
    w.world_name,
    s.is_hq,
    s.sale_date,
    AVG(s.price_per_unit) AS avg_price,
    COUNT(*) AS sale_count,
    SUM(s.quantity) AS total_volume
FROM {{ ref('stg_sales') }} s
LEFT JOIN {{ ref('item_names') }} n ON s.item_id = n.item_id
LEFT JOIN {{ ref('world_names') }} w ON s.world_id = w.world_id
GROUP BY s.item_id, n.item_name, s.world_id, w.world_name, s.is_hq, s.sale_date
ORDER BY sale_date DESC
