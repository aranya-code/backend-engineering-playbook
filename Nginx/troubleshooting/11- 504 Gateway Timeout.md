# Overview

A **504 Gateway Timeout** error occurs when **Nginx successfully connects to the upstream server but does not receive a response within the configured timeout period**.

Unlike a **502 Bad Gateway**, where the backend is unreachable, a **504 Gateway Timeout** means the backend is reachable but is responding too slowly.

This is one of the most common production issues in high-traffic applications and usually indicates backend performance problems rather than an Nginx configuration issue.

---

# Impact

| Impact | Level |
|---------|-------|
| Service Availability | 🔴 Critical |
| Performance | 🔴 Critical |
| Security | 🟢 None |
| Production Risk | 🔴 Critical |

---

# When You'll See This

This issue commonly occurs when:

- Long-running database queries
- Backend application is overloaded
- Slow external API calls
- CPU or memory exhaustion
- Backend deadlocks
- Incorrect timeout configuration
- Large file uploads or downloads
- Network latency

---

# Affected Components

- Reverse Proxy
- Backend Application
- Database
- Redis
- External APIs
- Load Balancer
- Network

---

# Symptoms

## Browser

```text
504 Gateway Timeout
```

---

## Access Log

```text
GET /api/orders HTTP/1.1

504
```

---

## Error Log

```text
upstream timed out (110: Connection timed out)

while reading response header from upstream
```

---

Another Example

```text
upstream timed out

while connecting to upstream
```

---

Application

```text
Request still processing...
```

---

# Quick Diagnosis

## Check Nginx Error Log

```bash
sudo tail -100 /var/log/nginx/error.log
```

---

## Test Backend Response Time

```bash
curl -w "@curl-format.txt" http://127.0.0.1:8000
```

or

```bash
time curl http://127.0.0.1:8000
```

---

## Check Backend Logs

Docker

```bash
docker logs backend
```

Linux

```bash
journalctl -u gunicorn
```

---

## Check Database

```bash
systemctl status postgresql
```

---

## Monitor Resources

```bash
top
```

```bash
htop
```

```bash
free -h
```

---

# Decision Tree

```text
             504 Gateway Timeout
                     │
                     ▼
         Can Nginx reach backend?
             │              │
            No             Yes
             │              │
             ▼              ▼
         Check 502      Is Backend Slow?
                             │
                   ┌─────────┴─────────┐
                   │                   │
                  No                  Yes
                   │                   │
                   ▼                   ▼
            Check Network       Check Application
                                Check Database
                                Check External APIs
                                       │
                                       ▼
                             Increase Timeout?
                                       │
                                       ▼
                              Optimize Backend
```

---

# Why This Happens

The request flow:

```text
Browser

↓

Nginx

↓

Backend

↓

Waiting...

↓

Timeout Exceeded

↓

504 Gateway Timeout
```

Nginx waits for the backend to respond.

If the backend exceeds the configured timeout values, Nginx closes the connection and returns a **504 Gateway Timeout**.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Slow database query | Database response takes too long |
| Heavy application processing | CPU-intensive request |
| External API delay | Third-party service is slow |
| Backend overload | Worker threads are busy |
| Network latency | Slow communication between services |
| Timeout too low | Nginx timeout values are insufficient |
| Resource exhaustion | CPU, RAM, or Disk bottleneck |

---

# Error Message Decoder

## Upstream Timed Out

```text
upstream timed out (110: Connection timed out)
```

### Meaning

The backend did not respond before the timeout expired.

### Solution

Investigate backend performance.

---

## Reading Response Header Timeout

```text
while reading response header from upstream
```

### Meaning

The backend accepted the connection but took too long to generate the response.

### Solution

Check:

- Database queries
- Application logs
- External API calls

---

# Step-by-Step Troubleshooting

## Step 1 — Verify Backend Response

```bash
time curl http://127.0.0.1:8000
```

Measure how long the backend takes to respond.

---

## Step 2 — Review Backend Logs

Docker

```bash
docker logs backend
```

Linux

```bash
journalctl -u gunicorn
```

Look for:

- Slow requests
- Exceptions
- Deadlocks
- Database timeouts

---

## Step 3 — Monitor System Resources

```bash
top
```

Check:

- CPU usage
- Memory usage
- Load Average

---

## Step 4 — Check Database Performance

Example

```sql
EXPLAIN ANALYZE
SELECT *
FROM orders;
```

Look for:

- Slow queries
- Missing indexes
- Table scans

---

## Step 5 — Review Nginx Timeout Configuration

Example

```nginx
proxy_connect_timeout 60s;

proxy_send_timeout 60s;

proxy_read_timeout 60s;
```

Increase only if the application legitimately requires more processing time.

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

- Optimize backend code before increasing timeouts.
- Monitor slow database queries.
- Cache frequently requested data.
- Use asynchronous processing for long-running tasks.
- Configure application health checks.
- Monitor request latency.

---

# Real Production Scenario

## Problem

A reporting API began returning:

```text
504 Gateway Timeout
```

during business hours.

---

## Investigation

The Nginx configuration was correct.

Backend logs showed a SQL query taking:

```text
72 seconds
```

The query performed a full table scan on a table containing over 15 million rows.

---

## Resolution

A missing database index was added.

Query execution time dropped from:

```text
72 seconds
```

to

```text
180 milliseconds
```

No timeout configuration changes were required.

---

# Verification Checklist

After fixing the issue:

- ✅ Backend responds within acceptable time
- ✅ Database queries are optimized
- ✅ No slow external API dependencies
- ✅ Resource usage is healthy
- ✅ Timeout values are appropriate
- ✅ Website returns HTTP 200

---

# Common Mistakes

❌ Increasing `proxy_read_timeout` without finding the root cause

❌ Ignoring slow SQL queries

❌ Blaming Nginx instead of the backend

❌ Not monitoring application response times

❌ Running CPU-intensive work synchronously

---

# Prevention Tips

- Monitor API response times.
- Use database indexes.
- Cache expensive operations.
- Offload long-running tasks to background workers (e.g., Celery).
- Set up alerts for slow requests.
- Continuously review application performance metrics.

---

# Production Notes

A **504 Gateway Timeout** is almost always a **performance problem**, not an Nginx problem.

In production, investigate in this order:

1. Backend response time
2. Database performance
3. External API latency
4. CPU and memory usage
5. Network latency
6. Nginx timeout configuration

Only increase timeout values **after** confirming that the application's response time cannot reasonably be optimized.

---

