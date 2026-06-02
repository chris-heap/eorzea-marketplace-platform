SELECT
    item AS item_id,
    world AS world_id,
    dt AS listed_date,
    listingID AS listing_id,
    pricePerUnit AS price_per_unit,
    quantity,
    total,
    tax,
    hq AS is_hq,
    isCrafted AS is_crafted,
    retainerName AS retainer_name,
    lastReviewTime AS last_review_time
FROM {{ source('raw', 'market_listings') }}
