FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src/ src/

RUN pip install websockets orjson httpx pymongo confluent-kafka

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "eorzea_producer.ws_handler"]
