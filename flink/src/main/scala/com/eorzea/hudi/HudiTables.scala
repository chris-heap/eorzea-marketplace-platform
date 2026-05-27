package com.eorzea.hudi

object HudiTables {

  val listingsDDL: String =
    """
      |CREATE TABLE hudi_listings (
      |  item INT,
      |  lastReviewTime BIGINT,
      |  pricePerUnit BIGINT,
      |  quantity INT,
      |  hq BOOLEAN,
      |  isCrafted BOOLEAN,
      |  retainerName STRING,
      |  listingID STRING,
      |  total BIGINT,
      |  tax BIGINT,
      |  world INT,
      |  dt STRING
      |) PARTITIONED BY (world, dt) WITH (
      |  'connector' = 'hudi',
      |  'path' = 's3a://eorzea-lake/raw/market_listings',
      |  'table.type' = 'MERGE_ON_READ',
      |  'write.precombine.field' = 'lastReviewTime',
      |  'hoodie.datasource.write.recordkey.field' = 'listingID',
      |  'compaction.async.enabled' = 'true',
      |  'compaction.delta_commits' = '5'
      |)
      |""".stripMargin

  val salesDDL: String =
    """
      |CREATE TABLE hudi_sales (
      |  item INT,
      |  hq BOOLEAN,
      |  pricePerUnit BIGINT,
      |  quantity INT,
      |  ts BIGINT,
      |  total BIGINT,
      |  buyerName STRING,
      |  onMannequin BOOLEAN,
      |  world INT,
      |  dt STRING
      |) PARTITIONED BY (world, dt) WITH (
      |  'connector' = 'hudi',
      |  'path' = 's3a://eorzea-lake/raw/sale_history',
      |  'table.type' = 'MERGE_ON_READ',
      |  'write.precombine.field' = 'ts',
      |  'hoodie.datasource.write.recordkey.field' = 'item,world,ts',
      |  'compaction.async.enabled' = 'true',
      |  'compaction.delta_commits' = '5'
      |)
      |""".stripMargin
}
