package com.eorzea.model

case class Listing(
                    lastReviewTime: Long,
                    pricePerUnit: Long,
                    quantity: Int,
                    hq: Boolean,
                    isCrafted: Boolean,
                    retainerName: String,
                    listingID: String,
                    total: Long,
                    tax: Long,
                    worldName: Option[String],
                    worldID: Option[Int],
                    creatorName: Option[String],
                    creatorID: Option[String],
                    sellerID: Option[String],
                    retainerID: Option[String],
                    retainerCity: Option[Int],
                    stainID: Option[Int],
                  )

case class ListingsEvent(
                          item: Int,
                          world: Int,
                          listings: List[Listing]
                        )