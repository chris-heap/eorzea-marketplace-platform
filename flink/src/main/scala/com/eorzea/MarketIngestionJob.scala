package com.eorzea

import com.eorzea.hudi.HudiTables
import com.eorzea.model.{ListingsEvent, SalesEvent}
import com.fasterxml.jackson.databind.{DeserializationFeature, ObjectMapper}
import com.fasterxml.jackson.module.scala.DefaultScalaModule
import org.apache.flink.api.common.eventtime.WatermarkStrategy
import org.apache.flink.api.common.serialization.SimpleStringSchema
import org.apache.flink.connector.kafka.source.KafkaSource
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer
import org.apache.flink.streaming.api.scala._
import org.apache.flink.table.api.bridge.scala.StreamTableEnvironment
import org.apache.flink.types.Row
import org.slf4j.LoggerFactory
import java.time.{Instant, ZoneOffset}

object MarketIngestion {

  private val logger = LoggerFactory.getLogger(getClass)
  private val mapper: ObjectMapper = {
    val m = new ObjectMapper()
    m.registerModule(DefaultScalaModule)
    m.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
    m
  }

  def main(args: Array[String]): Unit = {
    val env = StreamExecutionEnvironment.getExecutionEnvironment
    env.enableCheckpointing(60000)

    val tableEnv = StreamTableEnvironment.create(env)
    val bootstrapServers = sys.env.getOrElse("KAFKA_BOOTSTRAP_SERVERS", "broker:29092")
    logger.info("Starting Market Ingestion job, bootstrap servers: {}", bootstrapServers)

    val listingsSource = KafkaSource.builder[String]()
      .setBootstrapServers(bootstrapServers)
      .setTopics("raw.listings_add")
      .setGroupId("flink-listings-ingestion")
      .setStartingOffsets(OffsetsInitializer.latest())
      .setValueOnlyDeserializer(new SimpleStringSchema())
      .build()

    val salesSource = KafkaSource.builder[String]()
      .setBootstrapServers(bootstrapServers)
      .setTopics("raw.sales_add")
      .setGroupId("flink-sales-ingestion")
      .setStartingOffsets(OffsetsInitializer.latest())
      .setValueOnlyDeserializer(new SimpleStringSchema())
      .build()

    val listingsStream = env.fromSource(listingsSource, WatermarkStrategy.noWatermarks(), "Listings Source")
    val salesStream = env.fromSource(salesSource, WatermarkStrategy.noWatermarks(), "Sales Source")

    val listingRows = listingsStream.flatMap { json =>
      val event = mapper.readValue(json, classOf[ListingsEvent])
      logger.debug("Parsed {} listings for item {} on world {}", event.listings.size: java.lang.Integer, event.item: java.lang.Integer, event.world: java.lang.Integer)
      event.listings.map { listing =>
        val dt = Instant.ofEpochSecond(listing.lastReviewTime)
          .atZone(ZoneOffset.UTC).toLocalDate.toString
        (event.item, listing.lastReviewTime, listing.pricePerUnit,
         listing.quantity, listing.hq, listing.isCrafted, listing.retainerName,
         listing.listingID, listing.total, listing.tax, event.world, dt)
      }
    }

    val saleRows = salesStream.flatMap { json =>
      val event = mapper.readValue(json, classOf[SalesEvent])
      logger.debug("Parsed {} sales for item {} on world {}", event.sales.size: java.lang.Integer, event.item: java.lang.Integer, event.world: java.lang.Integer)
      event.sales.map { sale =>
        val dt = Instant.ofEpochSecond(sale.timestamp)
          .atZone(ZoneOffset.UTC).toLocalDate.toString
        (event.item, sale.hq, sale.pricePerUnit,
         sale.quantity, sale.timestamp, sale.total,
         sale.buyerName.orNull, sale.onMannequin, event.world, dt)
      }
    }

    val listingTable = tableEnv.fromDataStream(listingRows)
      .as("item", "lastReviewTime", "pricePerUnit", "quantity",
          "hq", "isCrafted", "retainerName", "listingID", "total", "tax",
          "world", "dt")

    val saleTable = tableEnv.fromDataStream(saleRows)
      .as("item", "hq", "pricePerUnit", "quantity",
          "ts", "total", "buyerName", "onMannequin",
          "world", "dt")

    tableEnv.executeSql(HudiTables.listingsDDL)
    tableEnv.executeSql(HudiTables.salesDDL)
    logger.info("Hudi tables registered")

    val statementSet = tableEnv.createStatementSet()
    statementSet.addInsert("hudi_listings", listingTable)
    statementSet.addInsert("hudi_sales", saleTable)
    statementSet.execute()
  }
}
