# Docker Health Checks

## Definition
Docker Health Check is a mechanism that determines whether an application inside a container is actually functioning correctly, not just running.

## Why Health Checks?

Problem:
A container process may be running while the application is broken.

Health checks verify:
- Web server responds
- Database accepts connections
- API endpoints work
- Application dependencies are healthy

## Container States

```text
starting
healthy
unhealthy
```

## How It Works

Docker executes a command inside the container.

Expected:
```text
Exit Code 0 = Healthy
Exit Code 1 = Unhealthy
```

Example:

```bash
curl -f http://localhost || exit 1
```

## Dockerfile Example

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost || exit 1
```

## Docker Run Example

```bash
docker run   --health-cmd="curl -f localhost:9200/_cluster/health || false"   --health-interval=5s   --health-retries=3   --health-timeout=2s   --health-start-period=15s   elasticsearch:2
```

## Parameters

| Parameter | Purpose |
|------------|----------|
| --health-cmd | Command to execute |
| --health-interval | Time between checks |
| --health-timeout | Check timeout |
| --health-retries | Failures before unhealthy |
| --health-start-period | Grace period during startup |

## Compose Example

```yaml
services:
  web:
    image: nginx
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 5s
      retries: 3
```

## Check Health Status

```bash
docker ps
```

Detailed:

```bash
docker inspect <container_id>
```

## Best Practices
- Check application functionality, not just process existence.
- Use lightweight commands.
- Allow startup grace periods.
- Combine with monitoring solutions.

## Interview Notes
Q: Difference between running and healthy?
A:
Running means process exists.
Healthy means application is responding correctly.

Q: Does Health Check replace monitoring tools?
A:
No. It is a container-level health mechanism, not a full monitoring solution.
