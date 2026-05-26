package com.eorzea.hudi

object HudiTables {

  val listingsDDL: String =
    """
      |CREATE TABLE hudi_listings (
      |  item INT,
      |  world INT,
      |  lastReviewTime BIGINT,
      |  pricePerUnit BIGINT,
      |  quantity INT,
      |  hq BOOLEAN,
      |  isCrafted BOOLEAN,
      |  retainerName STRING,
      |  listingID STRING,
      |  total BIGINT,
      |  tax BIGINT
      |) WITH (
      |  'connector' = 'hudi',
      |  'path' = 's3a://eorzea-lake/raw/market_listings',
      |  'table.type' = 'MERGE_ON_READ',
      |  'write.precombine.field' = 'lastReviewTime',
      |  'hoodie.datasource.write.recordkey.field' = 'listingID'
      |)
      |""".stripMargin

  val salesDDL: String =
    """
      |CREATE TABLE hudi_sales (
      |  item INT,
      |  world INT,
      |  hq BOOLEAN,
      |  pricePerUnit BIGINT,
      |  quantity INT,
      |  `timestamp` BIGINT,
      |  total BIGINT,
      |  buyerName STRING,
      |  onMannequin BOOLEAN
      |) WITH (
      |  'connector' = 'hudi',
      |  'path' = 's3a://eorzea-lake/raw/sale_history',
      |  'table.type' = 'MERGE_ON_READ',
      |  'write.precombine.field' = 'timestamp',
      |  'hoodie.datasource.write.recordkey.field' = 'item,world,timestamp'
      |)
      |""".stripMargin
}
