package com.eorzea.model

case class SaleRow(
                    item: Int,
                    world: Int,
                    hq: Boolean,
                    pricePerUnit: Long,
                    quantity: Int,
                    timestamp: Long,
                    total: Long,
                    buyerName: Option[String],
                    onMannequin: Boolean
                  )