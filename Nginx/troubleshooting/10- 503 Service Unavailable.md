# Overview

The **503 Service Unavailable** error indicates that **Nginx is currently unable to process the request because the requested service is temporarily unavailable**.

Unlike **502 Bad Gateway**, where Nginx cannot communicate with the backend, a **503** generally means that the backend service is **temporarily unavailable**, overloaded, under maintenance, or all upstream servers have been marked unavailable.

This error is usually temporary and often disappears once the backend recovers.

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

- Application is under maintenance
- Backend server is overloaded
- All upstream servers are unavailable
- Health checks mark servers as unhealthy
- Kubernetes Pods are restarting
- Auto Scaling is still provisioning instances
- Maximum connections have been reached

---

# Affected Components

- Reverse Proxy
- Upstream Servers
- Load Balancer
- Backend Applications
- Docker
- Kubernetes
- Health Checks

---

# Symptoms

## Browser

```text
503 Service Unavailable
```

---

## Access Log

```text
GET /api/orders HTTP/1.1

503
```

---

## Error Log

```text
no live upstreams while connecting to upstream
```

---

Another example

```text
upstream server temporarily disabled
```

---

Kubernetes

```text
Pod Not Ready
```

---

Docker

```text
Container Restarting
```

---

# Quick Diagnosis

## Validate Configuration

```bash
sudo nginx -t
```

---

## Check Nginx Logs

```bash
sudo tail -50 /var/log/nginx/error.log
```

---

## Check Backend Health

```bash
curl http://127.0.0.1:8000/health
```

---

## Check Running Services

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

kubectl get svc

kubectl describe pod <pod-name>
```

---

# Decision Tree

```text
              503 Service Unavailable
                       │
                       ▼
            Is Backend Running?
                │           │
               No          Yes
                │           │
                ▼           ▼
         Start Backend   Backend Healthy?
                              │
                  ┌───────────┴────────────┐
                  │                        │
                 No                       Yes
                  │                        │
                  ▼                        ▼
          Check Logs             Check Upstream Pool
          Check Database         Check Health Checks
                  │
                  ▼
           Restore Service
                  │
                  ▼
            Reload Nginx
```

---

# Why This Happens

A **503** usually indicates that the backend is **temporarily unavailable**, even though Nginx itself is working correctly.

Typical request flow:

```text
Browser

↓

Nginx

↓

Load Balancer

↓

Backend Unavailable

↓

503 Service Unavailable
```

Unlike a **502**, Nginx can still reach the upstream infrastructure, but no healthy backend is available to process the request.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Backend maintenance | Application intentionally offline |
| All upstreams unavailable | No healthy backend servers |
| Health check failure | Servers marked unhealthy |
| Application overload | Maximum workers reached |
| Resource exhaustion | CPU or memory exhausted |
| Kubernetes rollout | Pods temporarily unavailable |
| Auto Scaling delay | New instances still starting |

---

# Error Message Decoder

## No Live Upstreams

```text
no live upstreams
```

### Meaning

All configured backend servers are unavailable.

### Solution

Verify that at least one backend server is healthy.

---

## Upstream Temporarily Disabled

```text
upstream server temporarily disabled
```

### Meaning

Nginx has temporarily removed the backend because repeated requests failed.

### Solution

Check application logs and health checks.

---

## Service Unavailable

```text
503 Service Temporarily Unavailable
```

### Meaning

The backend is overloaded or in maintenance mode.

### Solution

Wait for the backend to recover or scale additional instances.

---

# Step-by-Step Troubleshooting

## Step 1 — Check Backend Health

```bash
curl http://127.0.0.1:8000/health
```

Expected

```text
200 OK
```

---

## Step 2 — Verify Upstream Servers

Example

```nginx
upstream backend {

    server app1:8000;

    server app2:8000;

}
```

Ensure at least one server is running.

---

## Step 3 — Check Backend Services

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

## Step 4 — Review Backend Logs

Docker

```bash
docker logs backend
```

Linux

```bash
journalctl -u gunicorn
```

Look for:

- Crashes
- Memory errors
- Worker exhaustion
- Database failures

---

## Step 5 — Check System Resources

```bash
top
```

```bash
free -h
```

```bash
df -h
```

Verify:

- CPU
- Memory
- Disk space

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

- Configure application health checks.
- Use multiple backend servers.
- Enable automatic service restarts.
- Monitor CPU and memory usage.
- Configure load balancing.
- Use Kubernetes readiness probes.

---

# Real Production Scenario

## Problem

A Kubernetes deployment started rolling out a new version.

Users immediately received:

```text
503 Service Unavailable
```

---

## Investigation

Checking Pods:

```bash
kubectl get pods
```

showed that all old Pods had terminated while the new Pods were still starting.

The Service temporarily had no healthy endpoints.

---

## Resolution

The deployment strategy was changed to:

```text
RollingUpdate
```

with:

- maxUnavailable = 0
- maxSurge = 1

Subsequent deployments completed without downtime.

---

# Verification Checklist

After fixing the issue:

- ✅ Backend is healthy
- ✅ At least one upstream server is available
- ✅ Health checks pass
- ✅ Resource usage is normal
- ✅ Website returns HTTP 200
- ✅ Error log contains no upstream failures

---

# Common Mistakes

❌ Restarting Nginx before checking backend health

❌ Deploying all backend instances simultaneously

❌ Missing health check endpoints

❌ Running a single backend instance in production

❌ Ignoring CPU and memory usage

❌ Not configuring readiness probes in Kubernetes

---

# Prevention Tips

- Use rolling deployments.
- Configure health checks.
- Enable automatic recovery.
- Monitor backend availability.
- Use multiple application instances.
- Configure alerts for unhealthy upstreams.

---

# Production Notes

A **503 Service Unavailable** is usually an **availability problem**, not a configuration problem.

In production, investigate in this order:

1. Health checks
2. Backend availability
3. Load balancer
4. Resource utilization
5. Kubernetes/Docker status
6. Application logs
7. Nginx logs

Proper monitoring and rolling deployments significantly reduce the likelihood of 503 errors during production releases.

---
