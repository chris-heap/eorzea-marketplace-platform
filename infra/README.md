# Infra

All infrastructure configuration.

```
infra/
├── docker/        # Dockerfiles per service
├── compose/       # Docker Compose for local dev
├── k8s/           # Kubernetes manifests
│   ├── base/
│   └── overlays/
│       ├── dev/
│       └── prod/
└── terraform/     # AWS + Snowflake IaC
    ├── modules/
    └── environments/
```
