import com.eorzea.hudi.HudiTables
import com.eorzea.model.{ListingsEvent, SalesEvent}
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.scala.DefaultScalaModule
import org.apache.flink.api.common.eventtime.WatermarkStrategy
import org.apache.flink.api.common.functions.FlatMapFunction
import org.apache.flink.api.common.serialization.SimpleStringSchema
import org.apache.flink.api.common.typeinfo.{TypeInformation, Types}
import org.apache.flink.api.java.typeutils.RowTypeInfo
import org.apache.flink.connector.kafka.source.KafkaSource
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer
import org.apache.flink.streaming.api.datastream.DataStream
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment
import org.apache.flink.table.api.bridge.java.StreamTableEnvironment
import org.apache.flink.types.Row
import org.apache.flink.util.Collector
import org.slf4j.LoggerFactory

object MarketIngestion {

  private val logger = LoggerFactory.getLogger(getClass)
  private val mapper: ObjectMapper = {
    val m = new ObjectMapper()
    m.registerModule(DefaultScalaModule)
    m
  }

  private val listingRowType = new RowTypeInfo(
    Array[TypeInformation[_]](Types.INT, Types.INT, Types.LONG, Types.LONG, Types.INT, Types.BOOLEAN, Types.BOOLEAN, Types.STRING, Types.STRING, Types.LONG, Types.LONG),
    Array("item", "world", "lastReviewTime", "pricePerUnit", "quantity", "hq", "isCrafted", "retainerName", "listingID", "total", "tax")
  )

  private val saleRowType = new RowTypeInfo(
    Array[TypeInformation[_]](Types.INT, Types.INT, Types.BOOLEAN, Types.LONG, Types.INT, Types.LONG, Types.LONG, Types.STRING, Types.BOOLEAN),
    Array("item", "world", "hq", "pricePerUnit", "quantity", "timestamp", "total", "buyerName", "onMannequin")
  )

  def main(args: Array[String]): Unit = {
    val env = StreamExecutionEnvironment.getExecutionEnvironment
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

    val listingsStream: DataStream[String] = env.fromSource(listingsSource, WatermarkStrategy.noWatermarks(), "Listings Source")

    val listingRowStream: DataStream[Row] = listingsStream.flatMap(
      new FlatMapFunction[String, Row] {
        override def flatMap(json: String, out: Collector[Row]): Unit = {
          val event = mapper.readValue(json, classOf[ListingsEvent])
          logger.debug("Parsed {} listings for item {} on world {}", event.listings.size: java.lang.Integer, event.item: java.lang.Integer, event.world: java.lang.Integer)
          event.listings.foreach(listing => {
            val row = Row.of(
              event.item: java.lang.Integer,
              event.world: java.lang.Integer,
              listing.lastReviewTime: java.lang.Long,
              listing.pricePerUnit: java.lang.Long,
              listing.quantity: java.lang.Integer,
              listing.hq: java.lang.Boolean,
              listing.isCrafted: java.lang.Boolean,
              listing.retainerName,
              listing.listingID,
              listing.total: java.lang.Long,
              listing.tax: java.lang.Long
            )
            out.collect(row)
          })
        }
      }, listingRowType
    )

    val salesStream: DataStream[String] = env.fromSource(salesSource, WatermarkStrategy.noWatermarks(), "Sales Source")

    val saleRowStream: DataStream[Row] = salesStream.flatMap(
      new FlatMapFunction[String, Row] {
        override def flatMap(json: String, out: Collector[Row]): Unit = {
          val event = mapper.readValue(json, classOf[SalesEvent])
          logger.debug("Parsed {} sales for item {} on world {}", event.sales.size: java.lang.Integer, event.item: java.lang.Integer, event.world: java.lang.Integer)
          event.sales.foreach(sale => {
            val row = Row.of(
              event.item: java.lang.Integer,
              event.world: java.lang.Integer,
              sale.hq: java.lang.Boolean,
              sale.pricePerUnit: java.lang.Long,
              sale.quantity: java.lang.Integer,
              sale.timestamp: java.lang.Long,
              sale.total: java.lang.Long,
              sale.buyerName.orNull,
              sale.onMannequin: java.lang.Boolean
            )
            out.collect(row)
          })
        }
      }, saleRowType
    )

    val listingTable = tableEnv.fromDataStream(listingRowStream)
    val saleTable = tableEnv.fromDataStream(saleRowStream)

    tableEnv.executeSql(HudiTables.listingsDDL)
    tableEnv.executeSql(HudiTables.salesDDL)
    logger.info("Hudi tables registered")

    val statementSet = tableEnv.createStatementSet()
    statementSet.addInsert("hudi_listings", listingTable)
    statementSet.addInsert("hudi_sales", saleTable)
    statementSet.execute()
  }

}
