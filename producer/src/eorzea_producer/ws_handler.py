import asyncio
import logging
import bson
from websockets.asyncio.client import connect
from eorzea_producer.kafka_producer import KafkaPublisher

logger = logging.getLogger(__name__)

WS_URL = "wss://universalis.app/api/ws"

TOPIC_MAP = {
    "listings/add": "raw.listings_add",
    "sales/add": "raw.sales_add",
}


async def _subscribe(ws):
    for channel in TOPIC_MAP:
        await ws.send(bson.encode({"event": "subscribe", "channel": channel}))
    logger.info("Subscribed to channels: %s", list(TOPIC_MAP.keys()))


async def run(publisher: KafkaPublisher):
    async with connect(WS_URL) as ws:
        logger.info("Connected to %s", WS_URL)
        await _subscribe(ws)

        async for message in ws:
            data = bson.decode(message)
            channel = data.get("event")
            topic = TOPIC_MAP.get(channel)

            if topic is None:
                logger.debug("Unrecognized channel, skipping: %s", channel)
                continue

            logger.debug("Received event on %s", channel)
            publisher.publish(topic, data)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    pub = KafkaPublisher(broker_address="localhost:9092")
    try:
        asyncio.run(run(pub))
    finally:
        pub.close()
