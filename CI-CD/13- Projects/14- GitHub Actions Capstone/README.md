# 14 - GitHub Actions Capstone

A complete reference project combining the major GitHub Actions concepts from
the previous labs.

## Features

- FastAPI application
- pytest
- PostgreSQL and Redis integration test services
- Matrix tests
- Reusable workflow
- Local composite action
- Docker image build
- GHCR publication
- GitHub Environments
- OIDC-ready AWS deployment stage
- Concurrency
- Immutable SHA image identity
- Manual rollback workflow
- Security-focused permissions

## Local run

```bash
docker compose up --build
```

## Project progression

This capstone is intentionally a compact production-style skeleton. Replace
the deployment placeholders with your AWS/ECS/EKS/EC2 infrastructure when
connecting it to a real environment.
