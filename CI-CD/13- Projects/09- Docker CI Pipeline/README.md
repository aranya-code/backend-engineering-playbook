# 09 - Docker CI Pipeline

Builds a real Docker image after Python tests pass.

## Run

```bash
docker build -t github-actions-lab .
docker run --rm -p 8000:8000 github-actions-lab
```

## CI focus

- Docker Buildx
- Build cache
- Dependency between jobs
- Container image build
