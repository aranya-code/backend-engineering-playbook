# Overview

One of the most common causes of **502 Bad Gateway** errors in Dockerized deployments is **incorrect container networking**.

Unlike applications running directly on the host machine, Docker containers communicate through **Docker networks**. If Nginx cannot reach the backend container, it cannot forward client requests and returns an error.

Common networking issues include:

- Containers on different Docker networks
- Incorrect container names
- Using `localhost` incorrectly
- Backend container not running
- Incorrect exposed ports
- DNS resolution failures
- Missing Docker Compose network configuration

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🔴 Critical |
| Performance | 🟢 None |
| Security | 🟢 None |
| Production Risk | 🔴 Critical |

---

# When You'll See This

This issue commonly occurs when:

- Deploying Nginx with Docker Compose
- Migrating applications into containers
- Creating multiple Docker networks
- Changing service names
- Updating Compose files
- Running backend services on different hosts

---

# Affected Components

- Docker Engine
- Docker Network
- Docker Compose
- Reverse Proxy
- DNS Resolution
- Backend Containers

---

# Symptoms

## Browser

```text
502 Bad Gateway
```

---

## Nginx Error Log

```text
connect() failed (111: Connection refused)
```

---

Another Example

```text
host not found in upstream
```

---

Docker Logs

```text
Container exited
```

---

Docker Compose

```text
Error response from daemon:
network not found
```

---

# Quick Diagnosis

## List Running Containers

```bash
docker ps
```

---

## View Docker Networks

```bash
docker network ls
```

---

## Inspect Network

```bash
docker network inspect bridge
```

or

```bash
docker network inspect my-network
```

---

## Test Backend

```bash
docker exec -it nginx sh
```

Then:

```bash
curl http://backend:8000
```

---

## Check Docker Compose

```bash
docker compose ps
```

---

# Decision Tree

```text
             502 Bad Gateway
                    │
                    ▼
         Is Backend Container Running?
              │               │
             No              Yes
              │               │
              ▼               ▼
      Start Container     Same Network?
                               │
                     ┌─────────┴─────────┐
                     │                   │
                    No                  Yes
                     │                   │
                     ▼                   ▼
            Connect Network       Test DNS
                                      │
                             ┌────────┴────────┐
                             │                 │
                            Fail             Success
                             │                 │
                             ▼                 ▼
                     Check Service Name   Check Port
```

---

# Why This Happens

Containers communicate using Docker networking.

Typical architecture:

```text
Internet

↓

Nginx Container

↓

Docker Network

↓

Backend Container

↓

Database
```

If either container is disconnected from the network, communication fails.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Backend container stopped | Service unavailable |
| Different Docker networks | Containers cannot communicate |
| Wrong hostname | Incorrect service/container name |
| Using localhost | Localhost refers to the current container |
| Wrong port | Backend listening on another port |
| Missing network | Docker Compose network missing |
| Firewall | Port communication blocked |

---

# Error Message Decoder

## Connection Refused

```text
connect() failed (111: Connection refused)
```

### Meaning

Nginx reached the destination host, but no application is listening.

### Solution

Verify that the backend container is running.

---

## Host Not Found

```text
host not found in upstream
```

### Meaning

Docker DNS cannot resolve the backend hostname.

### Solution

Verify the service name in `docker-compose.yml`.

---

## Network Not Found

```text
network not found
```

### Meaning

The configured Docker network does not exist.

### Solution

Recreate the Docker network.

---

# Step-by-Step Troubleshooting

## Step 1 — Verify Running Containers

```bash
docker ps
```

Expected

```text
nginx

backend

mysql
```

---

## Step 2 — Verify Networks

```bash
docker network ls
```

Example

```text
bridge

backend-network
```

---

## Step 3 — Inspect Network

```bash
docker network inspect backend-network
```

Verify both containers appear in the network.

---

## Step 4 — Test DNS Resolution

```bash
docker exec -it nginx sh
```

Then

```bash
ping backend
```

or

```bash
curl http://backend:8000
```

---

## Step 5 — Verify proxy_pass

Incorrect

```nginx
proxy_pass http://localhost:8000;
```

Inside Docker, `localhost` refers to the Nginx container itself.

Correct

```nginx
proxy_pass http://backend:8000;
```

where `backend` is the Docker Compose service name.

---

## Step 6 — Verify Docker Compose

Example

```yaml
services:

  nginx:

  backend:

networks:

  app-network:
```

Both services must belong to the same network.

---

## Step 7 — Restart Containers

```bash
docker compose down

docker compose up -d
```

---

# Best Practices

- Use Docker Compose service names instead of IP addresses.
- Never use `localhost` for inter-container communication.
- Use custom Docker networks.
- Keep Nginx and backend services on the same network.
- Use health checks for backend containers.
- Avoid hardcoding container IP addresses.

---

# Real Production Scenario

## Problem

After deploying a Django application with Docker Compose, users received:

```text
502 Bad Gateway
```

---

## Investigation

Nginx configuration contained:

```nginx
proxy_pass http://localhost:8000;
```

Inside the Nginx container, `localhost` referred to the Nginx container itself—not the Django container.

---

## Resolution

The configuration was updated:

```nginx
proxy_pass http://backend:8000;
```

where `backend` matched the Docker Compose service name.

After restarting the containers:

```bash
docker compose up -d
```

the application became accessible.

---

# Verification Checklist

After fixing the issue:

- ✅ Backend container is running
- ✅ Containers share the same Docker network
- ✅ Service names resolve correctly
- ✅ `proxy_pass` uses the correct hostname
- ✅ Backend responds successfully
- ✅ Nginx returns HTTP 200

---

# Common Mistakes

❌ Using `localhost` inside Docker

❌ Using container IP addresses

❌ Forgetting to attach services to the same network

❌ Incorrect service names in `proxy_pass`

❌ Exposing the wrong container port

❌ Ignoring Docker DNS

---

# Prevention Tips

- Always use Docker Compose service names.
- Create dedicated application networks.
- Add health checks for every backend service.
- Validate networking before deploying.
- Test connectivity using `docker exec`.

---

# Production Notes

More than **80% of Docker-related Nginx issues are caused by networking misconfigurations**.

When troubleshooting Docker deployments, investigate in this order:

1. Is the backend container running?
2. Are both containers on the same network?
3. Can Nginx resolve the backend hostname?
4. Is the backend listening on the expected port?
5. Is `proxy_pass` using the Docker service name?
6. Are health checks passing?

Avoid using fixed IP addresses in Docker. Docker's built-in DNS and service discovery are more reliable and easier to maintain.

---

