# Docker Compose Issues

## Overview

Docker Compose simplifies the deployment and management of multi-container applications by defining services, networks, and volumes in a single `compose.yaml` (or `docker-compose.yml`) file. While Compose greatly improves development workflows, configuration mistakes, dependency issues, networking problems, and volume misconfigurations can prevent applications from starting correctly.

This guide covers the most common Docker Compose issues, explains how to diagnose them, and provides practical solutions and best practices.

---

## Common Docker Compose Issues

| Issue | Severity |
|--------|----------|
| compose.yaml not found | High |
| Invalid Compose file | High |
| Service fails to start | High |
| Dependency service unavailable | High |
| Port conflicts | Medium |
| Environment variables not loaded | Medium |
| Volume mount issues | Medium |
| Network communication failures | High |
| Build failures | Medium |
| Orphan containers | Low |

---

# Issue 1: compose.yaml Not Found

## Symptoms

```text
no configuration file provided
```

or

```text
Can't find a suitable configuration file
```

---

## Possible Causes

- Running the command from the wrong directory.
- Incorrect filename.
- Configuration file deleted.

---

## How to Diagnose

Check current directory:

```bash
pwd
```

List files:

```bash
ls
```

---

## Solutions

Run Compose from the project root.

Specify the file manually:

```bash
docker compose -f compose.yaml up
```

---

## Prevention

- Keep the Compose file in the project root.
- Use standard filenames.

---

# Issue 2: Invalid Compose File

## Symptoms

```text
services must be a mapping
```

or

```text
yaml: line 15: mapping values are not allowed
```

---

## Possible Causes

- YAML indentation errors.
- Invalid syntax.
- Unsupported configuration.

---

## How to Diagnose

Validate configuration:

```bash
docker compose config
```

---

## Solutions

Fix YAML indentation.

Validate after every change.

---

## Prevention

- Use spaces instead of tabs.
- Use a YAML-aware editor.

---

# Issue 3: Service Fails to Start

## Symptoms

One or more services stop immediately.

---

## Possible Causes

- Application crash.
- Missing dependencies.
- Invalid configuration.

---

## How to Diagnose

View running services:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs
```

---

## Solutions

Inspect logs.

Correct application configuration.

Rebuild the service:

```bash
docker compose up --build
```

---

## Prevention

Test each container independently before combining them in Compose.

---

# Issue 4: Dependency Service Unavailable

## Symptoms

Application cannot connect to database or Redis.

Example:

```text
Connection refused
```

---

## Possible Causes

- Database not fully initialized.
- Incorrect service name.
- Wrong port.

---

## How to Diagnose

List running services:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs database
```

---

## Solutions

Use service names instead of localhost.

Add health checks.

Implement retry logic in the application.

---

## Prevention

Do not rely solely on `depends_on`.

Use health checks for service readiness.

---

# Issue 5: Port Already Allocated

## Symptoms

```text
Bind for 0.0.0.0:5432 failed
```

---

## Possible Causes

- Another service uses the port.
- Local application occupies the port.

---

## How to Diagnose

List containers:

```bash
docker ps
```

Check local ports:

Linux

```bash
sudo lsof -i :5432
```

Windows

```powershell
netstat -ano
```

---

## Solutions

Stop the conflicting service.

Publish another host port.

Example:

```yaml
ports:
  - "5433:5432"
```

---

## Prevention

Maintain a documented port allocation strategy.

---

# Issue 6: Environment Variables Not Loaded

## Symptoms

Application reports missing configuration.

---

## Possible Causes

- Missing `.env`.
- Incorrect variable names.
- Wrong Compose syntax.

---

## How to Diagnose

Validate configuration:

```bash
docker compose config
```

Inspect environment variables:

```bash
docker compose exec app env
```

---

## Solutions

Verify `.env` exists.

Use:

```yaml
env_file:
  - .env
```

or

```yaml
environment:
  DATABASE_URL: postgres://...
```

---

## Prevention

Keep environment variable names consistent across environments.

---

# Issue 7: Volume Mount Issues

## Symptoms

Application files or database data disappear.

---

## Possible Causes

- Wrong mount path.
- Incorrect permissions.
- Empty host directory.

---

## How to Diagnose

Inspect container:

```bash
docker inspect container_name
```

Inspect volumes:

```bash
docker volume ls
```

---

## Solutions

Correct mount paths.

Adjust permissions.

Use named volumes for persistent data.

---

## Prevention

Prefer named volumes for production workloads.

---

# Issue 8: Network Communication Failure

## Symptoms

Services cannot communicate.

Example:

```text
Name or service not known
```

---

## Possible Causes

- Wrong hostname.
- Containers on different networks.
- DNS issue.

---

## How to Diagnose

Inspect network:

```bash
docker network inspect project_default
```

---

## Solutions

Use service names.

Ensure all services share the same network.

---

## Prevention

Allow Compose to manage networking automatically.

---

# Issue 9: Build Failures

## Symptoms

Compose build fails.

---

## Possible Causes

- Dockerfile error.
- Missing dependencies.
- Invalid build context.

---

## How to Diagnose

Build manually:

```bash
docker compose build
```

---

## Solutions

Correct Dockerfile.

Verify build context.

Use:

```bash
docker compose build --no-cache
```

---

## Prevention

Keep Dockerfiles small and deterministic.

---

# Issue 10: Orphan Containers

## Symptoms

```text
Found orphan containers
```

---

## Possible Causes

- Service renamed.
- Old Compose project.
- Stale containers.

---

## How to Diagnose

List containers:

```bash
docker ps -a
```

---

## Solutions

Remove orphan containers:

```bash
docker compose down --remove-orphans
```

---

## Prevention

Clean old Compose projects regularly.

---

# Diagnostic Commands Cheat Sheet

| Purpose | Command |
|---------|---------|
| Validate Compose file | `docker compose config` |
| Start services | `docker compose up` |
| Start in background | `docker compose up -d` |
| Stop services | `docker compose down` |
| View logs | `docker compose logs` |
| List services | `docker compose ps` |
| Build images | `docker compose build` |
| Rebuild without cache | `docker compose build --no-cache` |
| Execute shell | `docker compose exec <service> sh` |
| Remove orphan containers | `docker compose down --remove-orphans` |

---

# Best Practices

- Validate the Compose file before deployment using `docker compose config`.
- Use service names instead of IP addresses for inter-service communication.
- Prefer named volumes for persistent data.
- Add health checks for databases and dependent services.
- Store sensitive configuration in environment variables.
- Keep Compose files modular and readable.
- Remove orphan containers regularly.
- Use version control for Compose configurations.

---

# Related Topics

- Docker Compose
- Docker Networking
- Docker Volumes
- Container Startup Failures
- Image Build Failures
- Docker CLI
- Docker Containers

---

## Key Takeaways

- Most Docker Compose issues arise from configuration errors, dependency timing, networking, or storage misconfigurations.
- `docker compose config`, `docker compose logs`, and `docker compose ps` are the primary tools for troubleshooting Compose applications.
- Use service names for networking, named volumes for persistence, and health checks for reliable startup sequencing.
- Keep Compose files simple, validated, and version-controlled to reduce deployment problems.
- Regular maintenance of Compose projects, including removing orphan containers and validating configuration, improves reliability and simplifies debugging.