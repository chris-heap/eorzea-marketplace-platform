package com.eorzea.model

case class Sale(
                 hq: Boolean,
                 pricePerUnit: Long,
                 quantity: Int,
                 timestamp: Long,
                 total: Long,
                 buyerName: Option[String],
                 worldName: Option[String],
                 worldID: Option[Int],
                 onMannequin: Boolean,
               )
case class SalesEvent(
                       item: Int,
                       world: Int,
                       sales: List[Sale]
                     )