# Docker Health Checks

---

### Runs a container with a Health Check.

```bash
docker run -d --health-cmd="curl -f http://localhost || exit 1" nginx
```

### Shows container health status.

```bash
docker ps
```

### Displays detailed health information.

```bash
docker inspect <container_id>
```

### Displays only the health output.

```bash
docker inspect --format='{{json .State.Health}}' <container_id>
```

### Defines a Dockerfile health check.

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost || exit 1
```

### Disables health checks.

```bash
docker run --no-healthcheck nginx
```
