# Health Checks

## Overview

A container that is running is not necessarily a healthy container.

Docker considers a container "running" as long as its main process is alive. However, the application inside the container may have crashed, become unresponsive, lost database connectivity, or entered a deadlock while the container itself continues running.

Health checks allow Docker to verify whether an application is actually functioning correctly.

---

# Why Health Checks Matter

Without health checks:

```text
Container Running

↓

Application Frozen

↓

Users Receive Errors
```

Docker has no way of detecting the failure.

With health checks:

```text
Container Running

↓

Health Check

↓

Application Unhealthy

↓

Restart / Alert
```

Health checks improve reliability by detecting failures early.

---

# Running vs Healthy

A running container is not always healthy.

| Container State | Meaning |
|-----------------|---------|
| Running | Process is alive |
| Healthy | Application is responding correctly |
| Unhealthy | Application failed health checks |
| Exited | Container has stopped |

---

# How Health Checks Work

```text
Docker

↓

Execute Health Check

↓

Application

↓

Healthy?

↓

Yes

↓

Healthy Container
```

If the check repeatedly fails:

```text
Docker

↓

Health Check Failed

↓

Container Marked Unhealthy
```

---

# Typical Health Endpoint

Most web applications expose:

```text
GET /health
```

Example response

```json
{
    "status": "healthy"
}
```

The endpoint should be lightweight and return quickly.

---

# Dockerfile Health Check

Docker supports health checks directly.

```dockerfile
HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=20s \
    --retries=3 \
CMD curl --fail http://localhost:8000/health || exit 1
```

Explanation

| Option | Purpose |
|---------|----------|
| interval | Time between checks |
| timeout | Maximum time allowed |
| start-period | Grace period after startup |
| retries | Consecutive failures before unhealthy |

---

# Docker Compose Health Check

Example

```yaml
services:

  app:

    image: myapp:1.0.0

    healthcheck:

      test:
        [
          "CMD",
          "curl",
          "-f",
          "http://localhost:8000/health"
        ]

      interval: 30s

      timeout: 5s

      retries: 3

      start_period: 20s
```

---

# Health Check Workflow

```text
Container Starts

↓

Wait Start Period

↓

Health Check

↓

Healthy?

↓

Yes

↓

Running
```

If not:

```text
Health Check

↓

Failed

↓

Retry

↓

Failed

↓

Retry

↓

Unhealthy
```

---

# Health Check Timing

Example

```text
Container Starts

↓

20 Seconds

↓

Check #1

↓

30 Seconds

↓

Check #2

↓

30 Seconds

↓

Check #3
```

Docker repeats checks according to the configured interval.

---

# Database Health Checks

PostgreSQL

```yaml
healthcheck:

  test:
    [
      "CMD-SHELL",
      "pg_isready -U postgres"
    ]
```

Redis

```yaml
healthcheck:

  test:
    [
      "CMD",
      "redis-cli",
      "ping"
    ]
```

Expected response

```text
PONG
```

---

# Service Startup Order

Health checks can control startup dependencies.

```text
Database

↓

Healthy

↓

Application Starts

↓

Healthy

↓

Nginx Starts
```

This avoids applications attempting to connect to services that are not yet ready.

---

# Using depends_on

Example

```yaml
depends_on:

  db:

    condition: service_healthy
```

The application waits until the database reports a healthy status.

---

# Good Health Checks

A good health check should:

- Execute quickly
- Require minimal resources
- Verify core functionality
- Return simple responses
- Avoid expensive operations

---

# Poor Health Checks

Avoid:

- Long database queries
- External API calls
- Large file processing
- Complex business logic
- Heavy computations

Health checks should complete in milliseconds whenever possible.

---

# Liveness vs Readiness

Although Docker provides a single health check mechanism, many orchestration platforms distinguish between two concepts.

| Check | Purpose |
|--------|----------|
| Liveness | Is the application still running? |
| Readiness | Can the application receive traffic? |

Understanding this distinction becomes important when using platforms such as Kubernetes.

---

# Inspecting Health Status

View container status

```bash
docker ps
```

Inspect health information

```bash
docker inspect container_name
```

Example

```text
Health

↓

Status

↓

healthy
```

---

# Viewing Health Logs

Inspect detailed results

```bash
docker inspect container_name
```

Docker stores:

- Exit code
- Output
- Execution time
- Previous checks

These logs are useful for troubleshooting.

---

# Common Mistakes

## No Health Checks

Without health checks Docker cannot detect application failures.

---

## Slow Health Endpoints

Health endpoints should not perform expensive work.

Bad

```text
Generate Report

↓

Health Check
```

Good

```text
Return Status

↓

200 OK
```

---

## Calling External Services

Health checks should avoid dependencies on external APIs whenever possible.

Otherwise temporary network issues may incorrectly mark the container as unhealthy.

---

## Long Timeouts

Very long timeouts delay failure detection.

Keep timeout values reasonable.

---

## Using Root URLs

Prefer

```text
/health
```

instead of

```text
/
```

The root endpoint may perform additional work that is unnecessary for health verification.

---

# Production Checklist

Before deployment:

- Health endpoint implemented
- Docker health check configured
- Startup grace period defined
- Retry count configured
- Timeout configured
- Health checks execute quickly
- Database dependencies considered
- Health status verified

---

# Best Practices

- Implement a dedicated `/health` endpoint.
- Keep health checks lightweight.
- Configure reasonable intervals and timeouts.
- Use health checks with `depends_on` for service startup.
- Verify essential application functionality only.
- Monitor unhealthy containers.
- Avoid external network dependencies during health checks.
- Test health checks as part of deployment verification.

---

# Key Takeaways

- A running container is not always a healthy container.
- Health checks allow Docker to detect application failures that process monitoring alone cannot identify.
- Lightweight health endpoints improve reliability and support automated recovery.
- Properly configured health checks help coordinate service startup and simplify production troubleshooting.
- Health checks are a fundamental component of resilient Docker deployments and form the basis for more advanced orchestration platforms.