# Eorzea Market Anomaly Detection Platform

Real-time market data pipeline and anomaly detection system built on FFXIV Market Board data from the [Universalis API](https://universalis.app).

## Architecture

```
Universalis WebSocket / REST API
          │
     ┌────▼────┐
     │ producer │  Python — Kafka producer
     └────┬────┘
          │
     ┌────▼────┐
     │  Kafka   │  Event streaming
     └────┬────┘
          │
     ┌────▼────┐
     │  Flink   │  Scala — streaming transforms → Hudi on S3
     └────┬────┘
          │
     ┌────▼─────────┐
     │ Hudi on S3    │  Raw lakehouse layer (MinIO locally)
     └────┬─────────┘
          │
     ┌────▼────┐
     │ Airflow  │  Batch orchestration
     │  + dbt   │  raw → staging → mart
     └────┬────┘
          │
     ┌────▼─────────┐
     │ ML Pipeline   │  PyTorch autoencoder + MLflow
     └────┬─────────┘
          │
     ┌────▼────┐
     │   API   │  FastAPI — serve anomaly scores
     └────────┘
```

## Repo Structure

```
├── producer/          # Universalis → Kafka producer (Python)
├── flink/             # Kafka → Hudi stream processor (Scala)
├── dbt/               # raw → staging → mart transformations (SQL)
├── airflow/           # Batch orchestration DAGs (Python)
├── ml/                # PyTorch autoencoder + MLflow (Python)
├── api/               # FastAPI anomaly serving (Python)
├── infra/
│   ├── docker/        # Dockerfiles per service
│   ├── compose/       # Docker Compose for local dev
│   ├── k8s/           # Kubernetes manifests (base + overlays)
│   └── terraform/     # AWS + Snowflake IaC
├── scripts/           # Utility scripts
└── docs/              # Architecture docs + ADRs
```

## Phases

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Local Foundation — Kafka, Flink, MinIO, Hudi | 🔲 |
| 2 | Batch Pipeline — Airflow, dbt, DuckDB | 🔲 |
| 3 | Snowflake Integration | 🔲 |
| 4 | ML Pipeline — PyTorch, MLflow | 🔲 |
| 5 | Serving — FastAPI | 🔲 |
| 6 | Kubernetes | 🔲 |
| 7 | Terraform + Cloud | 🔲 |
| 8 | Polish + Monitoring | 🔲 |

## Quick Start

```bash
# Copy env config
cp .env.example .env

# Start local infra (Kafka, Flink, MinIO)
docker compose -f infra/compose/docker-compose.yml up -d

# Start the producer (once infra is healthy)
cd producer && poetry install && poetry run eorzea-producer
```

## Tech Stack

Kafka · Flink (Scala) · Apache Hudi · S3/MinIO · Airflow · dbt · Snowflake · DuckDB · PyTorch · MLflow · FastAPI · Docker · Kubernetes · Terraform
