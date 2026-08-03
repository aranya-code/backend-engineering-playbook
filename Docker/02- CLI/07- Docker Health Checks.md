# Docker Health Checks

## Overview
Docker Health Checks provide a native way to monitor the status of an application running inside a container. Instead of relying solely on the container process state (e.g., PID 1 is running), health checks verify if the application is actually ready to handle requests or perform its duties. This is critical for orchestrators and load balancers to route traffic correctly and recover from stalled applications.

## Common Commands

| Command | Description |
|---|---|
| `docker run -d --health-cmd="curl -f http://localhost \|\| exit 1" nginx` | Run a container with an inline health check command |
| `docker run --no-healthcheck nginx` | Disable any configured health checks for the container |
| `docker ps` | View container status, including health check state (`healthy`, `unhealthy`, `starting`) |
| `docker inspect <container_id>` | View full container metadata, including health check configuration and history |
| `docker inspect --format='{{json .State.Health}}' <container_id>` | Extract only the JSON health status and logs |

## Command Breakdown

When configuring a health check via CLI flags, the following options are available:
*   `--health-cmd`: The command to run inside the container to check health (must return exit code `0` for success, or `1` for failure).
*   `--health-interval`: The time between running the check (e.g., `30s`, `1m`).
*   `--health-timeout`: The maximum time to wait for a single check to complete before considering it failed (e.g., `5s`).
*   `--health-retries`: The number of consecutive failures needed to mark the container as `unhealthy` (e.g., `3`).
*   `--health-start-period`: Initialization time during which failures are not counted towards the maximum retries (e.g., `10s`). Useful for slow-starting apps.

## Practical Examples

### Using a Dockerfile

Add the `HEALTHCHECK` instruction to your Dockerfile to bake the configuration into the image:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
  CMD curl -f http://localhost/health || exit 1
```

### Compose File Health Check

```yaml
version: '3.8'
services:
  web:
    image: nginx
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

### Inspecting Health Status

Run a container and observe its health:

```bash
docker run -d --name web_app --health-cmd="curl -f http://localhost || exit 1" nginx
```

Check the status immediately (likely `starting`):
```bash
docker ps
```
```text
CONTAINER ID   IMAGE     COMMAND                  CREATED         STATUS                            PORTS      NAMES
abcdef123456   nginx     "/docker-entrypoint.…"   2 seconds ago   Up 1 second (health: starting)    80/tcp     web_app
```

Check the structured health output:
```bash
docker inspect --format='{{json .State.Health}}' web_app
```
```text
{"Status":"healthy","FailingStreak":0,"Log":[{"Start":"2023-10-27T10:00:00.000Z","End":"2023-10-27T10:00:00.100Z","ExitCode":0,"Output":"..."}]}
```

### Non-HTTP Health Checks

For a Postgres database:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 10s
  timeout: 5s
  retries: 5
```

## Real-World Use Cases
*   **Orchestrator Restarts:** Swarm and other orchestrators can automatically restart containers that transition to the `unhealthy` state.
*   **Load Balancer Integration:** Ensuring that a reverse proxy or load balancer only routes traffic to containers marked as `healthy`.
*   **Dependency Checks:** Using tools like Docker Compose `depends_on` with `condition: service_healthy` to delay the startup of a service until its database or required API is ready.

## Common Mistakes
*   **Missing Dependencies:** Using `curl` or `wget` in a health check, but deploying a minimal image (like `alpine` or `scratch`) that doesn't have these tools installed.
*   **Too-Short Intervals:** Setting a very aggressive interval (e.g., `1s`) which can overload the application or the host machine with constant health check requests.
*   **Ignoring Start Period:** Omitting `--health-start-period` for applications that take a long time to boot (like a large Java app). It will be marked unhealthy and potentially killed before it finishes starting.

## Best Practices
*   **Dedicated Health Endpoints:** Implement a lightweight `/health` or `/live` endpoint in your application specifically designed for health checks. It should verify database connections and critical dependencies without executing heavy logic.
*   **Use Built-in Tools:** Prefer built-in database readiness tools (like `pg_isready` or `mysqladmin ping`) over trying to run generic network queries for specialized services.

## Interview Tips
*   **What exit codes does a health check script use?** It uses `0` for success and `1` for failure. Docker also reserves `2` but its behavior is currently undefined.
*   **Difference between liveness and readiness?** While Docker's native healthcheck broadly covers both, liveness indicates if an app needs restarting, and readiness indicates if it's ready to receive traffic.

## Related Topics
- [Docker Compose](06-%20Docker%20Compose.md)
- [Images and Containers](02-%20Images%20and%20Containers.md)
- [Docker Swarm](09-%20Docker%20Swarm.md)

## Key Takeaways
*   Health checks ensure your application is actually functioning, not just that the process is running.
*   They can be defined in a Dockerfile, via the CLI, or in a Compose file.
*   Containers undergo a state transition: `starting` -> `healthy` (or `unhealthy`).
*   Properly tuning interval, timeout, retries, and start period is essential for reliable orchestration.
