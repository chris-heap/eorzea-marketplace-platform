# Flink

Kafka → Hudi streaming processor.

**Language:** Scala 2.12  
**Build:** sbt + sbt-assembly  
**Runtime:** Flink 1.18

## Tables Written
- `raw.market_listings` — partitioned by (world_name, dt)
- `raw.sale_history` — partitioned by (world_name, dt)
