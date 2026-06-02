SELECT
    item AS item_id,
    world AS world_id,
    dt AS sale_date,
    ts AS sale_timestamp,
    pricePerUnit AS price_per_unit,
    quantity,
    total,
    hq AS is_hq,
    buyerName AS buyer_name,
    onMannequin AS is_mannequin
FROM {{ source('raw', 'sale_history') }}
