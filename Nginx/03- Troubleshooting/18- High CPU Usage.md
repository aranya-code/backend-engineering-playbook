# Overview

High CPU usage occurs when one or more Nginx worker processes consume excessive processor resources, resulting in slow response times, increased latency, and, in severe cases, service degradation.

Although Nginx is designed to be lightweight and highly efficient, poor application design, excessive traffic, inefficient configuration, or malicious requests can cause CPU utilization to spike.

In many production environments, high CPU usage is not caused by Nginx itself but by the workload it is processing.

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🔴 Critical |
| Performance | 🔴 Critical |
| Security | 🟡 Medium |
| Production Risk | 🔴 Critical |

---

# When You'll See This

This issue commonly occurs when:

- Traffic suddenly increases
- DDoS or bot traffic
- Expensive regular expressions
- Excessive logging
- Backend application responds slowly
- Large file serving
- Compression enabled on large files
- Infinite redirect loops

---

# Affected Components

- Worker Processes
- Worker Connections
- Reverse Proxy
- Load Balancer
- CPU
- Compression
- Logging

---

# Symptoms

## Website Performance

- Slow page loads
- Increased response time
- Requests timing out

---

## CPU Usage

```bash
top
```

Example

```text
CPU: 98%
```

---

## Process List

```bash
ps -eo pid,ppid,cmd,%cpu --sort=-%cpu
```

Example

```text
nginx: worker process      99.5%
```

---

## Docker

```bash
docker stats
```

Example

```text
CPU %

98%
```

---

## Kubernetes

```bash
kubectl top pods
```

Example

```text
nginx-ingress

950m CPU
```

---

# Quick Diagnosis

## Check CPU Usage

```bash
top
```

---

## Interactive Process Monitor

```bash
htop
```

---

## Check Worker Processes

```bash
ps -ef | grep nginx
```

---

## View Active Connections

```bash
ss -ant
```

---

## Monitor Requests

```bash
tail -f /var/log/nginx/access.log
```

---

## View Error Log

```bash
tail -50 /var/log/nginx/error.log
```

---

# Decision Tree

```text
               High CPU Usage
                     │
                     ▼
            Check CPU Processes
                     │
                     ▼
             Is Nginx Using CPU?
              │              │
             No             Yes
              │              │
              ▼              ▼
      Check Backend      High Traffic?
                              │
                    ┌─────────┴──────────┐
                    │                    │
                   Yes                  No
                    │                    │
                    ▼                    ▼
          Investigate Traffic      Review Configuration
          Check Bots              Check Compression
          Rate Limiting           Check Regex
                    │
                    ▼
             Optimize Nginx
```

---

# Why This Happens

Typical request flow:

```text
Internet

↓

Nginx

↓

Worker Process

↓

Application

↓

Response
```

CPU usage increases when workers spend excessive time processing requests rather than forwarding them efficiently.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| High traffic | Large number of concurrent requests |
| DDoS attack | Excessive malicious requests |
| Gzip compression | CPU-intensive compression |
| Regex locations | Expensive regular expression matching |
| Large log files | Heavy synchronous logging |
| Redirect loops | Endless request processing |
| Slow backend | Workers remain busy waiting |

---

# Error Message Decoder

## Worker Process at 100%

```text
nginx: worker process
```

### Meaning

One or more worker processes are fully utilizing CPU resources.

### Solution

Identify whether the traffic is legitimate or caused by inefficient configuration.

---

## Worker Connections Exhausted

```text
worker_connections are not enough
```

### Meaning

Workers are overloaded handling concurrent connections.

### Solution

Increase:

```nginx
worker_connections
```

after evaluating system limits.

---

# Step-by-Step Troubleshooting

## Step 1 — Identify High CPU Process

```bash
top
```

Verify whether Nginx is consuming CPU.

---

## Step 2 — Check Active Requests

```bash
ss -ant
```

Review the number of active client connections.

---

## Step 3 — Inspect Access Logs

```bash
tail -f /var/log/nginx/access.log
```

Look for:

- Repeated requests
- Bot traffic
- Suspicious IP addresses
- Infinite redirects

---

## Step 4 — Check Compression

Example

```nginx
gzip on;
```

If serving already compressed files (ZIP, MP4, JPEG), disable unnecessary compression.

---

## Step 5 — Review Location Rules

Avoid expensive regex patterns.

Instead of:

```nginx
location ~* \.(jpg|png|gif)$
```

prefer efficient prefix matching where possible.

---

## Step 6 — Enable Caching

Example

```nginx
proxy_cache my_cache;
```

Caching reduces backend requests and CPU utilization.

---

## Step 7 — Reload Configuration

```bash
sudo nginx -t

sudo systemctl reload nginx
```

---

# Best Practices

- Enable caching for static content.
- Use CDN for static assets.
- Configure rate limiting.
- Compress only appropriate content types.
- Optimize regular expressions.
- Monitor CPU usage continuously.

---

# Real Production Scenario

## Problem

An e-commerce website became extremely slow during a seasonal sale.

CPU utilization reached:

```text
100%
```

All Nginx worker processes were fully utilized.

---

## Investigation

Access logs showed thousands of requests from a single IP range scraping product pages.

No rate limiting was configured.

---

## Resolution

Rate limiting was enabled.

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

limit_req zone=api burst=20;
```

Bot traffic was reduced significantly.

CPU usage dropped from:

```text
100%
```

to

```text
22%
```

without increasing server resources.

---

# Verification Checklist

After fixing the issue:

- ✅ CPU utilization is within normal limits
- ✅ Worker processes are healthy
- ✅ Requests complete successfully
- ✅ No excessive bot traffic
- ✅ Access logs appear normal
- ✅ Website response times improve

---

# Common Mistakes

❌ Increasing server size before identifying the cause

❌ Enabling Gzip for every file type

❌ Ignoring bot traffic

❌ Using expensive regex location blocks

❌ Not enabling caching

❌ Ignoring access log analysis

---

# Prevention Tips

- Monitor CPU utilization continuously.
- Enable rate limiting.
- Use caching whenever possible.
- Deploy a CDN for static assets.
- Configure alerts for sustained high CPU usage.
- Review access logs regularly.

---

# Production Notes

High CPU usage is **often a symptom rather than the root cause**.

Investigate in this order:

1. Traffic volume
2. Bot or DDoS activity
3. Access logs
4. Backend response time
5. Compression settings
6. Regular expression locations
7. Caching configuration
8. Worker process configuration

Scaling the server should be the **last** step after identifying and addressing the underlying issue.

---
