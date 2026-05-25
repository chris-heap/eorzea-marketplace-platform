import logging
import orjson
from confluent_kafka import Producer

logger = logging.getLogger(__name__)


class KafkaPublisher:
    def __init__(self, broker_address: str):
        self.producer = Producer({
            "bootstrap.servers": broker_address,
            "queue.buffering.max.messages": 100000,
        })
        logger.info("Kafka producer initialized (broker=%s)", broker_address)

    def _delivery_report(self, err, msg):
        if err is not None:
            logger.error("Kafka delivery failed: %s", err)

    def publish(self, topic: str, message: dict, key: str | None = None):
        self.producer.produce(
            topic=topic,
            value=orjson.dumps(message),
            key=key.encode() if key else None,
            callback=self._delivery_report,
        )
        self.producer.poll(0)

    def close(self):
        self.producer.flush()