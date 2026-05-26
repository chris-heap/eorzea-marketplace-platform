package com.eorzea.model

case class ListingRow(
                       item: Int,
                       world: Int,
                       lastReviewTime: Long,
                       pricePerUnit: Long,
                       quantity: Int,
                       hq: Boolean,
                       isCrafted: Boolean,
                       retainerName: String,
                       listingID: String,
                       total: Long,
                       tax: Long
                     )