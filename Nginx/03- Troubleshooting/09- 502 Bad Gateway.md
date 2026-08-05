# Overview

The **502 Bad Gateway** error indicates that **Nginx successfully received the client's request but failed to receive a valid response from the upstream server**.

Unlike a **500 Internal Server Error**, which usually originates from the backend application, a **502 Bad Gateway** typically indicates that Nginx **could not communicate successfully with the backend service**.

This is one of the most common production issues encountered when deploying applications behind Nginx.

Typical backend servers include:

- Gunicorn
- Uvicorn
- Node.js
- PHP-FPM
- Apache
- Tomcat

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🔴 Critical |
| Performance | 🔴 High |
| Security | 🟢 None |
| Production Risk | 🔴 Critical |

---

# When You'll See This

This issue commonly occurs when:

- Backend application is stopped
- Gunicorn/Uvicorn crashed
- Docker container is unhealthy
- Kubernetes Pod is restarting
- Incorrect `proxy_pass`
- Wrong upstream port
- Firewall blocks communication
- DNS resolution fails
- Socket file missing

---

# Affected Components

- Reverse Proxy
- Upstream Servers
- Gunicorn
- Uvicorn
- Docker
- Kubernetes
- Networking
- DNS

---

# Symptoms

## Browser

```text
502 Bad Gateway
```

---

## Access Log

```text
GET /api/users HTTP/1.1

502
```

---

## Error Log

```text
connect() failed (111: Connection refused)

while connecting to upstream
```

---

Another example

```text
no live upstreams while connecting to upstream
```

---

Docker

```text
Container Exited
```

---

Kubernetes

```text
CrashLoopBackOff
```

---

# Quick Diagnosis

## Check Nginx Configuration

```bash
sudo nginx -t
```

---

## Check Backend

```bash
curl http://127.0.0.1:8000
```

---

## Check Nginx Error Log

```bash
sudo tail -50 /var/log/nginx/error.log
```

---

## Check Gunicorn

```bash
systemctl status gunicorn
```

---

## Docker

```bash
docker ps

docker logs backend
```

---

## Kubernetes

```bash
kubectl get pods

kubectl logs <pod-name>
```

---

# Decision Tree

```text
                  502 Bad Gateway
                         │
                         ▼
                 Is Backend Running?
                 │                 │
                No                Yes
                 │                 │
                 ▼                 ▼
        Start Backend      Can Nginx Connect?
                                     │
                        ┌────────────┴────────────┐
                        │                         │
                       No                        Yes
                        │                         │
                        ▼                         ▼
             Check proxy_pass             Check Backend Logs
             Check Firewall               Check Application
             Check Docker Network         Check Database
                        │
                        ▼
                 Test Connection
                        │
                        ▼
                  Reload Nginx
```

---

# Why This Happens

Nginx acts as a reverse proxy.

Request flow:

```text
Browser

↓

Nginx

↓

Backend

↓

Response
```

If the backend:

- crashes
- refuses the connection
- becomes unreachable
- returns an invalid response

Nginx cannot forward the request and returns:

```text
502 Bad Gateway
```

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Backend stopped | Application server is not running |
| Wrong proxy_pass | Incorrect hostname or port |
| Firewall | Backend port blocked |
| Docker networking | Containers not on same network |
| Kubernetes Service | Service not pointing to Pods |
| Unix socket missing | Gunicorn socket deleted |
| DNS failure | Upstream hostname cannot be resolved |

---

# Error Message Decoder

## Connection Refused

```text
connect() failed (111: Connection refused)
```

### Meaning

The backend is not accepting connections.

### Solution

Start the backend service.

---

## No Live Upstreams

```text
no live upstreams
```

### Meaning

All upstream servers are unavailable.

### Solution

Verify every backend server is healthy.

---

## Host Not Found

```text
host not found in upstream
```

### Meaning

Nginx cannot resolve the backend hostname.

### Solution

Verify:

- DNS
- Docker service name
- Kubernetes Service

---

## Connection Timed Out

```text
upstream timed out
```

### Meaning

Backend is too slow.

### Solution

Investigate backend performance.

---

# Step-by-Step Troubleshooting

## Step 1 — Verify Backend

```bash
curl http://127.0.0.1:8000
```

Expected

```text
200 OK
```

If the request fails, the backend is unavailable.

---

## Step 2 — Check proxy_pass

Example

```nginx
location / {

    proxy_pass http://127.0.0.1:8000;

}
```

Verify:

- Hostname
- Port
- Protocol

---

## Step 3 — Verify Backend Process

Linux

```bash
systemctl status gunicorn
```

Docker

```bash
docker ps
```

Kubernetes

```bash
kubectl get pods
```

---

## Step 4 — Verify Network

Docker

```bash
docker network inspect bridge
```

Kubernetes

```bash
kubectl get svc
```

Linux

```bash
ping backend

telnet backend 8000
```

---

## Step 5 — Review Logs

Nginx

```bash
tail -100 /var/log/nginx/error.log
```

Backend

```bash
docker logs backend
```

or

```bash
journalctl -u gunicorn
```

---

## Step 6 — Validate Configuration

```bash
sudo nginx -t
```

---

## Step 7 — Reload Nginx

```bash
sudo systemctl reload nginx
```

---

# Best Practices

- Always use health checks.
- Monitor backend services.
- Use load balancing for redundancy.
- Avoid hardcoding IP addresses.
- Use service names in Docker and Kubernetes.
- Configure automatic service restarts.

---

# Real Production Scenario

## Problem

Users suddenly reported:

```text
502 Bad Gateway
```

---

## Investigation

Nginx was healthy.

Running:

```bash
systemctl status gunicorn
```

returned:

```text
inactive (dead)
```

Gunicorn crashed after a failed deployment.

---

## Resolution

Restarted Gunicorn.

```bash
systemctl restart gunicorn
```

Validated backend.

```bash
curl http://127.0.0.1:8000
```

Reloaded Nginx.

Website immediately recovered.

---

# Verification Checklist

After fixing the issue:

- ✅ Backend service is running
- ✅ Nginx can connect to backend
- ✅ `proxy_pass` is correct
- ✅ Error log is clean
- ✅ Website returns HTTP 200
- ✅ Health checks succeed

---

# Common Mistakes

❌ Restarting Nginx without checking the backend

❌ Using `localhost` inside Docker containers

❌ Wrong container name in `proxy_pass`

❌ Incorrect Gunicorn socket path

❌ Forgetting to expose the backend port

❌ Ignoring firewall rules

---

# Prevention Tips

- Configure health checks.
- Use automatic service restart policies.
- Monitor backend availability.
- Test deployments before switching traffic.
- Keep Nginx and backend logs centralized.

---

# Production Notes

A **502 Bad Gateway** is **rarely caused by Nginx itself**.

In most production systems, investigate in this order:

1. Backend service
2. Application logs
3. Network connectivity
4. Docker/Kubernetes networking
5. Reverse proxy configuration
6. Nginx logs

Following this sequence significantly reduces troubleshooting time during production incidents.

---

