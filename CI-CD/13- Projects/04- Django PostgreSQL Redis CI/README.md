# 04 - Django PostgreSQL Redis CI

Integration-test lab using GitHub Actions service containers for PostgreSQL and Redis.

## Local run

```bash
docker compose up -d
pip install -r requirements.txt
pytest -q -m integration
```

## CI focus

- Service containers
- PostgreSQL health checks
- Redis integration
- Environment variables
- Integration tests
