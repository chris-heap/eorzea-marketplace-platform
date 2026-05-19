# Producer

Universalis API (WebSocket + REST) → Kafka producer.

**Language:** Python  
**Dependencies:** confluent-kafka, websockets, httpx, pydantic, structlog  
**Package manager:** Poetry

## Topics
- `market.listings.raw` — live listing events
- `market.sales.raw` — completed sale events
