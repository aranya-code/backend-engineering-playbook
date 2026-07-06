# Docker Troubleshooting

A collection of real-world Docker issues and their solutions — covering networking, static files, container lifecycle, Compose configuration, and Swarm orchestration.

---

## 📚 Issues & Solutions

| # | Issue | Category | Root Cause |
|---|-------|----------|------------|
| 01 | [Container Cannot Connect to Host PostgreSQL](./01-%20Container%20Cannot%20Connect%20to%20Host%20PostgreSQL.md) | Networking | Container can't reach a database running on the host machine |
| 02 | [DRF Admin CSS Missing in Docker](./02-%20DRF%20Admin%20CSS%20Missing%20in%20Docker.md) | Static Files | Django doesn't serve static files in containerized/production environments |
| 03 | [Container Exits Immediately After `docker run`](./03-%20Container%20Exits%20Immediately%20After%20Docker%20Run.md) | Container Lifecycle | No foreground process to keep the container alive |
| 04 | [`volumes must be a mapping` Error in Compose](./04-%20Compose%20Volumes%20Must%20Be%20a%20Mapping%20Error.md) | Compose Config | YAML list syntax (`-`) used instead of mapping for top-level volumes |
| 05 | [Swarm Overlay Network Initialization Failure](./05-%20Swarm%20Overlay%20Network%20Initialization%20Failure.md) | Swarm Networking | Overlay network sandbox fails to initialize for a service |

---

## Quick Reference

### 01 — Container Cannot Connect to Host PostgreSQL

**Problem:** A containerized app (e.g., Django) can't reach a PostgreSQL database running on the host machine.

**Solutions:**
- **Option A** — Use Docker's special DNS name `host.docker.internal` as the database host.
- **Option B** — Containerize the database itself with a `docker-compose.yml` service and `depends_on`.

```yaml
# Option B — Containerized PostgreSQL
services:
  web:
    build: .
    depends_on:
      - db
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=my_database_name
```

---

### 02 — DRF / Admin CSS Missing in Docker

**Problem:** Django Rest Framework's browsable API and Django Admin lose all CSS styling when containerized — pages render as plain, unstyled HTML.

**Root Cause:** Django's `runserver` serves static files automatically in local development, but drops this behavior inside containers or when `DEBUG=False`.

**Fix (Development):**
```dockerfile
CMD python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000
```

---

### 03 — Container Exits Immediately After `docker run -d`

**Problem:** Running `docker run -d --name ubuntu ubuntu:14.04` starts and immediately exits.

**Root Cause:** Docker containers only stay alive while a foreground process is running. The base Ubuntu image has no default foreground process.

**Solutions:**
```bash
# Interactive mode
docker run -it --name ubuntu ubuntu:14.04 /bin/bash

# Detached with a persistent process
docker run -dit --name ubuntu ubuntu:14.04 bash
```

---

### 04 — `volumes must be a mapping` Error

**Problem:** `docker compose up` fails with `volumes must be a mapping`.

**Root Cause:** Top-level `volumes` defined with YAML list syntax (`-`) instead of mapping syntax.

```diff
 volumes:
-  - drupal-modules:
-  - drupal-profiles:
+  drupal-modules:
+  drupal-profiles:
```

---

### 05 — Swarm Overlay Network Initialization Failure

**Problem:** A Docker Swarm service fails because the overlay network sandbox can't initialize, even though the network exists.

**Solution:** Remove the failed service → Remove the overlay network → Recreate → Verify → Redeploy the service.

---

## Categories at a Glance

| Category | Issues | Description |
|----------|--------|-------------|
| 🌐 **Networking** | 01, 05 | Container-to-host connectivity, Swarm overlay networks |
| 📦 **Container Lifecycle** | 03 | Container startup, foreground processes |
| 🎨 **Static Files** | 02 | Django/DRF static file serving in containers |
| ⚙️ **Compose Configuration** | 04 | YAML syntax, volume definitions |

---

## Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [Docker](../README.md) |

---

> **Part of the [Backend Engineering Playbook](../../) — a structured learning resource for backend engineers.**
