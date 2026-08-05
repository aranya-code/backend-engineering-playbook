# Overview

High memory usage occurs when Nginx consumes excessive RAM while processing client requests.

Unlike CPU utilization, memory usage generally increases due to buffering, caching, large client requests, long-lived connections, or excessive concurrent traffic.

Although Nginx is known for its low memory footprint, improper configuration or unusually heavy workloads can significantly increase memory consumption.

In production environments, high memory usage may eventually lead to:

- Out of Memory (OOM) kills
- Container restarts
- Kubernetes Pod eviction
- Increased response times
- System instability

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

- Serving large file uploads
- Reverse proxy buffering large responses
- Thousands of concurrent connections
- Large request headers
- Proxy caching large files
- Memory limits are too low
- Containers have limited RAM

---

# Affected Components

- Worker Processes
- Proxy Buffers
- FastCGI Buffers
- Client Buffers
- Proxy Cache
- Linux Memory
- Docker
- Kubernetes

---

# Symptoms

## Slow Website

- Increased response time
- Random failures
- Requests hanging

---

## Linux

```bash
free -h
```

Example

```text
Mem:

15G used

800M free
```

---

## Process Usage

```bash
ps aux --sort=-%mem | head
```

Example

```text
nginx

18.4% MEM
```

---

## Docker

```bash
docker stats
```

Example

```text
MEM USAGE

2.4GB / 3GB
```

---

## Kubernetes

```bash
kubectl top pods
```

Example

```text
nginx-ingress

950Mi
```

---

# Quick Diagnosis

## Check Memory

```bash
free -h
```

---

## Monitor Processes

```bash
top
```

or

```bash
htop
```

---

## View Nginx Processes

```bash
ps aux | grep nginx
```

---

## Check Docker Resources

```bash
docker stats
```

---

## Check Kubernetes Resource Usage

```bash
kubectl top pods
```

---

## View System Logs

```bash
dmesg | grep -i oom
```

---

# Decision Tree

```text
              High Memory Usage
                     │
                     ▼
            Is Nginx Using RAM?
             │               │
            No              Yes
             │               │
             ▼               ▼
      Check Backend      Large Traffic?
                               │
                     ┌─────────┴──────────┐
                     │                    │
                    Yes                  No
                     │                    │
                     ▼                    ▼
          Check Buffers          Check Cache
          Check Uploads          Check Workers
                     │
                     ▼
             Optimize Settings
                     │
                     ▼
              Monitor Again
```

---

# Why This Happens

Memory is consumed by several Nginx components:

```text
Client Request

↓

Worker Process

↓

Client Buffers

↓

Proxy Buffers

↓

FastCGI Buffers

↓

Cache

↓

Response
```

Large requests or many concurrent clients increase memory consumption.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Large uploads | Client request buffering |
| Large downloads | Proxy response buffering |
| Proxy cache | Cached responses consume RAM |
| Too many workers | Increased memory allocation |
| High concurrency | Thousands of active connections |
| Large headers | Large client header buffers |
| Memory leak in backend | Backend application consuming RAM |

---

# Error Message Decoder

## Out of Memory

```text
Killed process nginx
```

### Meaning

The Linux OOM Killer terminated Nginx due to insufficient memory.

### Solution

Reduce memory usage or increase available RAM.

---

## Cannot Allocate Memory

```text
Cannot allocate memory
```

### Meaning

The operating system cannot allocate additional memory.

### Solution

Review memory usage across the system.

---

## Container OOMKilled

```text
OOMKilled
```

### Meaning

Docker or Kubernetes terminated the container because it exceeded its memory limit.

### Solution

Increase container memory limits or optimize memory usage.

---

# Step-by-Step Troubleshooting

## Step 1 — Check System Memory

```bash
free -h
```

Review:

- Used memory
- Free memory
- Available memory

---

## Step 2 — Identify High Memory Processes

```bash
ps aux --sort=-%mem | head
```

Determine whether Nginx is the primary consumer.

---

## Step 3 — Check Active Connections

```bash
ss -ant
```

A large number of active connections may increase memory usage.

---

## Step 4 — Review Buffer Configuration

Example

```nginx
client_body_buffer_size 16k;

proxy_buffer_size 16k;

proxy_buffers 8 16k;
```

Avoid unnecessarily large buffer values.

---

## Step 5 — Review Cache Configuration

Example

```nginx
proxy_cache_path /var/cache/nginx
```

Ensure cache storage is appropriately configured.

---

## Step 6 — Review Upload Limits

Example

```nginx
client_max_body_size 100M;
```

Large upload limits increase memory requirements during request processing.

---

## Step 7 — Validate Configuration

```bash
sudo nginx -t
```

---

## Step 8 — Reload Nginx

```bash
sudo systemctl reload nginx
```

---

# Best Practices

- Configure reasonable buffer sizes.
- Store cache on disk instead of memory when appropriate.
- Limit maximum upload size.
- Monitor memory continuously.
- Configure container memory limits carefully.
- Tune worker processes according to available RAM.

---

# Real Production Scenario

## Problem

A file-sharing application began crashing every afternoon.

Kubernetes continuously restarted the Nginx Pod.

---

## Investigation

Running

```bash
kubectl describe pod
```

showed:

```text
Reason:

OOMKilled
```

Large file uploads combined with oversized proxy buffers caused the Pod to exceed its 1 GB memory limit.

---

## Resolution

Buffer sizes were reduced:

```nginx
proxy_buffer_size 16k;

proxy_buffers 8 16k;
```

The Pod memory limit was increased to 2 GB.

After redeployment, memory usage stabilized below 700 MB.

---

# Verification Checklist

After fixing the issue:

- ✅ Memory usage remains stable
- ✅ No OOMKilled events
- ✅ Buffer sizes are optimized
- ✅ Uploads complete successfully
- ✅ Cache operates normally
- ✅ Website responds without failures

---

# Common Mistakes

❌ Configuring excessively large buffers

❌ Ignoring container memory limits

❌ Allowing unlimited upload sizes

❌ Assuming more worker processes always improve performance

❌ Ignoring OOMKilled events

❌ Monitoring only CPU usage

---

# Prevention Tips

- Monitor RAM usage continuously.
- Set appropriate Docker and Kubernetes memory limits.
- Optimize proxy and FastCGI buffers.
- Review upload limits regularly.
- Configure alerts for memory usage.
- Test memory utilization under production load.

---

# Production Notes

High memory usage is often the result of **configuration choices combined with production traffic patterns**.

Investigate in this order:

1. System memory usage
2. Container memory limits
3. Number of concurrent connections
4. Buffer configuration
5. Proxy caching
6. Upload sizes
7. Backend application memory usage

Avoid increasing server memory before determining whether Nginx configuration can be optimized.

---

