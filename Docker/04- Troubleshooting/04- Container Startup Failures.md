# Container Startup Failures

## Overview

A Docker container may fail to start for various reasons, including incorrect commands, missing dependencies, configuration errors, insufficient permissions, unavailable ports, or application crashes. Startup failures are among the most common Docker issues encountered during development and production deployments.

This guide explains how to identify, diagnose, and resolve common container startup failures using Docker's built-in debugging tools and best practices.

---

## Common Container Startup Issues

| Issue | Severity |
|--------|----------|
| Container exits immediately | High |
| Crash loop (Restarting) | High |
| Executable not found | High |
| Application startup failure | High |
| Environment variables missing | Medium |
| Port binding failure | High |
| Volume mount failure | Medium |
| Permission denied | High |
| Health check failures | Medium |
| Resource limitations | Medium |

---

# Issue 1: Container Exits Immediately

## Symptoms

```bash
docker ps
```

No running containers are displayed.

However,

```bash
docker ps -a
```

shows:

```text
Exited (1)
Exited (127)
Exited (137)
Exited (139)
```

---

## Possible Causes

- Main application crashed.
- Invalid startup command.
- Missing executable.
- Configuration errors.
- Required files missing.

---

## How to Diagnose

List all containers:

```bash
docker ps -a
```

Inspect logs:

```bash
docker logs <container_name>
```

Inspect configuration:

```bash
docker inspect <container_name>
```

---

## Solutions

Fix application errors.

Verify the startup command.

Ensure all required files are copied into the image.

Rebuild the image if necessary.

---

## Prevention

- Test the application locally before containerizing.
- Keep startup scripts simple.
- Validate application configuration.

---

# Issue 2: Container Keeps Restarting

## Symptoms

```text
STATUS: Restarting (1)
```

---

## Possible Causes

- Application crashes repeatedly.
- Incorrect restart policy.
- Missing dependencies.
- Health check failures.

---

## How to Diagnose

Check restart count:

```bash
docker inspect <container_name>
```

View logs:

```bash
docker logs <container_name>
```

---

## Solutions

Fix the application error.

Disable automatic restart temporarily:

```bash
docker update --restart=no <container_name>
```

Restart manually after fixing the issue.

---

## Prevention

- Test startup scripts.
- Configure meaningful health checks.
- Avoid infinite restart loops.

---

# Issue 3: Executable Not Found

## Symptoms

```text
exec: "python": executable file not found
```

or

```text
no such file or directory
```

---

## Possible Causes

- Incorrect ENTRYPOINT.
- Incorrect CMD.
- Executable missing.
- Wrong file path.

---

## How to Diagnose

Inspect Dockerfile.

Run an interactive shell:

```bash
docker run -it --entrypoint sh <image_name>
```

Locate executable:

```bash
which python
```

---

## Solutions

Correct the executable path.

Verify installation during image build.

Update CMD or ENTRYPOINT.

---

## Prevention

- Use absolute paths where appropriate.
- Verify executables after installation.

---

# Issue 4: Application Startup Failure

## Symptoms

Container starts but immediately exits.

Application logs show exceptions.

---

## Possible Causes

- Database unavailable.
- Missing configuration.
- Dependency failures.
- Syntax or runtime errors.

---

## How to Diagnose

View logs:

```bash
docker logs <container_name>
```

Run interactively:

```bash
docker exec -it <container_name> sh
```

---

## Solutions

Resolve application errors.

Verify external dependencies.

Ensure required services are available.

---

## Prevention

- Validate configuration before deployment.
- Implement application health checks.

---

# Issue 5: Missing Environment Variables

## Symptoms

Application reports:

```text
Environment variable not found
```

---

## Possible Causes

- Missing `.env` file.
- Incorrect Compose configuration.
- Typographical errors.

---

## How to Diagnose

Inspect environment variables:

```bash
docker inspect <container_name>
```

or

```bash
docker exec <container_name> env
```

---

## Solutions

Pass variables correctly:

```bash
docker run -e DATABASE_URL=...
```

or

```yaml
environment:
  DATABASE_URL: ...
```

---

## Prevention

- Store configuration in environment variables.
- Validate required variables during startup.

---

# Issue 6: Port Already Allocated

## Symptoms

```text
Bind for 0.0.0.0:8000 failed
```

---

## Possible Causes

- Another container is using the port.
- Local application occupies the port.

---

## How to Diagnose

List running containers:

```bash
docker ps
```

Check port usage:

Linux

```bash
sudo lsof -i :8000
```

Windows

```powershell
netstat -ano
```

---

## Solutions

Stop the conflicting container.

Change the published port:

```bash
docker run -p 8080:8000
```

---

## Prevention

Maintain a documented port allocation strategy.

---

# Issue 7: Volume Mount Failure

## Symptoms

Application cannot access expected files.

---

## Possible Causes

- Incorrect mount path.
- Missing host directory.
- Permission issues.

---

## How to Diagnose

Inspect mounts:

```bash
docker inspect <container_name>
```

Verify directory exists.

---

## Solutions

Correct mount paths.

Create missing directories.

Adjust permissions.

---

## Prevention

Always verify volume paths before deployment.

---

# Issue 8: Permission Denied

## Symptoms

```text
Permission denied
```

---

## Possible Causes

- Incorrect ownership.
- Read-only filesystem.
- Non-executable startup script.

---

## How to Diagnose

Inspect permissions:

```bash
ls -l
```

---

## Solutions

Grant execute permission:

```bash
chmod +x start.sh
```

Set correct ownership.

---

## Prevention

Avoid running containers as root unless necessary.

---

# Issue 9: Health Check Failures

## Symptoms

```text
STATUS: unhealthy
```

---

## Possible Causes

- Incorrect health check.
- Slow application startup.
- Wrong endpoint.

---

## How to Diagnose

Inspect health status:

```bash
docker inspect <container_name>
```

---

## Solutions

Increase startup timeout.

Correct health check endpoint.

Verify application readiness.

---

## Prevention

Design realistic health checks.

---

# Issue 10: Resource Limits

## Symptoms

Container stops unexpectedly.

Exit code:

```text
137
```

---

## Possible Causes

- Out of memory.
- CPU limits exceeded.

---

## How to Diagnose

Monitor resources:

```bash
docker stats
```

Inspect exit code:

```bash
docker inspect <container_name>
```

---

## Solutions

Increase memory allocation.

Optimize application.

Configure resource limits appropriately.

---

## Prevention

Monitor resource usage continuously.

Use production-appropriate limits.

---

# Diagnostic Commands Cheat Sheet

| Purpose | Command |
|---------|---------|
| List running containers | `docker ps` |
| List all containers | `docker ps -a` |
| View logs | `docker logs <container>` |
| Inspect configuration | `docker inspect <container>` |
| Execute shell | `docker exec -it <container> sh` |
| Monitor resources | `docker stats` |
| View processes | `docker top <container>` |
| View filesystem changes | `docker diff <container>` |

---

# Best Practices

- Keep startup commands simple.
- Test images before deployment.
- Validate all environment variables.
- Implement meaningful health checks.
- Monitor logs during deployment.
- Avoid hardcoded configuration.
- Use restart policies carefully.
- Regularly inspect running containers.

---

# Related Topics

- Docker Containers
- Docker Images
- Docker Compose
- Docker Volumes
- Docker Networking
- Docker Logs
- Docker Health Checks

---

## Key Takeaways

- Most startup failures are caused by incorrect startup commands, missing dependencies, configuration errors, or permission issues.
- `docker logs` and `docker inspect` are the primary tools for diagnosing startup problems.
- Health checks, proper environment variable management, and careful resource allocation improve container reliability.
- Testing container startup locally before deployment helps prevent production issues.
- Following Docker best practices significantly reduces container startup failures.