# Overview

The **Too Many Open Files** error occurs when Nginx reaches the maximum number of file descriptors allowed by the operating system.

Every active client connection, log file, SSL certificate, socket, cache file, and backend connection consumes one or more **file descriptors (FDs)**.

When the limit is reached:

- New client connections are rejected.
- Static files cannot be opened.
- Upstream connections fail.
- Nginx may stop serving requests.

This issue is common on **high-traffic production servers** that have not been tuned for large numbers of concurrent connections.

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

- Handling thousands of concurrent users
- File descriptor limits are too low
- Worker connections are configured too high
- Large numbers of keepalive connections
- Reverse proxy to many backend servers
- Heavy logging activity

---

# Affected Components

- Worker Processes
- Worker Connections
- Linux File Descriptors
- Reverse Proxy
- Access Logs
- Error Logs
- Upstream Connections

---

# Symptoms

## Browser

```text
502 Bad Gateway
```

or

```text
503 Service Unavailable
```

---

## Error Log

```text
accept4() failed (24: Too many open files)
```

---

Another Example

```text
open() failed (24: Too many open files)
```

---

System Log

```text
EMFILE
```

---

Linux

```bash
ulimit -n
```

Example

```text
1024
```

---

# Quick Diagnosis

## Check File Descriptor Limit

```bash
ulimit -n
```

---

## View Nginx Worker Limits

```bash
cat /proc/$(pidof nginx | awk '{print $1}')/limits
```

---

## Count Open Files

```bash
lsof -p $(pidof nginx | awk '{print $1}') | wc -l
```

---

## Check Active Connections

```bash
ss -ant
```

---

## View System Limits

```bash
cat /etc/security/limits.conf
```

---

# Decision Tree

```text
          Too Many Open Files
                  │
                  ▼
         Check ulimit -n
                  │
        ┌─────────┴─────────┐
        │                   │
      Low Limit       Limit OK
        │                   │
        ▼                   ▼
 Increase Limit      Too Many Connections?
                             │
                   ┌─────────┴──────────┐
                   │                    │
                  Yes                  No
                   │                    │
                   ▼                    ▼
       Tune Workers & Keepalive   Check File Leaks
                   │
                   ▼
             Reload Nginx
```

---

# Why This Happens

Each request consumes file descriptors.

Typical flow:

```text
Client

↓

TCP Socket

↓

Nginx Worker

↓

Access Log

↓

Backend Socket

↓

Static File

↓

Response
```

When the number of open descriptors exceeds the operating system limit, new files or sockets cannot be opened.

---

# Common Causes

| Cause | Description |
|--------|-------------|
| Low ulimit | Operating system limit too small |
| High traffic | Thousands of concurrent connections |
| Large keepalive pool | Connections remain open |
| Worker connections | Configured higher than system limits |
| File leak | Processes fail to close descriptors |
| Heavy logging | Many log files open simultaneously |

---

# Error Message Decoder

## Too Many Open Files

```text
Too many open files
```

### Meaning

The process has exhausted its available file descriptors.

### Solution

Increase the file descriptor limit and review connection usage.

---

## accept4() Failed

```text
accept4() failed (24)
```

### Meaning

Nginx cannot accept new client connections.

### Solution

Increase `worker_rlimit_nofile` and the OS file descriptor limit.

---

## EMFILE

```text
EMFILE
```

### Meaning

The process has reached the maximum number of open files.

### Solution

Increase the process limit and identify excessive descriptor usage.

---

# Step-by-Step Troubleshooting

## Step 1 — Check Current Limit

```bash
ulimit -n
```

Typical production systems often use values such as:

```text
65535
```

instead of the default:

```text
1024
```

---

## Step 2 — Count Open Descriptors

```bash
lsof -p $(pidof nginx | awk '{print $1}') | wc -l
```

If this value is close to the configured limit, Nginx is exhausting available descriptors.

---

## Step 3 — Review Worker Configuration

Example

```nginx
worker_processes auto;

worker_rlimit_nofile 65535;
```

---

## Step 4 — Review Worker Connections

Example

```nginx
events {

    worker_connections 4096;

}
```

Remember:

```text
Maximum Connections

≈

worker_processes × worker_connections
```

Ensure the operating system supports the calculated maximum.

---

## Step 5 — Update Linux Limits

Example

```text
/etc/security/limits.conf
```

```
www-data soft nofile 65535

www-data hard nofile 65535
```

---

## Step 6 — Restart Nginx

```bash
sudo systemctl restart nginx
```

Verify the new limits.

---

# Best Practices

- Increase file descriptor limits for production servers.
- Configure `worker_rlimit_nofile`.
- Monitor open file descriptors.
- Tune `worker_connections` appropriately.
- Close unnecessary long-lived connections.
- Rotate log files regularly.

---

# Real Production Scenario

## Problem

A high-traffic API began rejecting new client connections during peak hours.

Users intermittently received:

```text
503 Service Unavailable
```

---

## Investigation

Running:

```bash
ulimit -n
```

returned:

```text
1024
```

while:

```bash
lsof -p $(pidof nginx | awk '{print $1}') | wc -l
```

showed over **1,000 open file descriptors**.

Nginx had exhausted the operating system limit.

---

## Resolution

The Linux file descriptor limit was increased to:

```text
65535
```

The Nginx configuration was updated:

```nginx
worker_rlimit_nofile 65535;
```

After restarting the service, the server handled peak traffic without connection failures.

---

# Verification Checklist

After fixing the issue:

- ✅ File descriptor limit increased
- ✅ `worker_rlimit_nofile` configured
- ✅ Worker connections are appropriate
- ✅ Open file descriptors remain below the limit
- ✅ No `EMFILE` errors
- ✅ Website handles expected traffic

---

# Common Mistakes

❌ Increasing `worker_connections` without increasing OS limits

❌ Leaving the default `ulimit` value

❌ Ignoring long-lived keepalive connections

❌ Forgetting to restart the service after changing limits

❌ Monitoring CPU but not file descriptor usage

---

# Prevention Tips

- Configure high file descriptor limits on production servers.
- Monitor open file descriptors with Prometheus or similar tools.
- Review connection counts regularly.
- Tune keepalive settings appropriately.
- Load test before production deployment.

---

# Production Notes

File descriptor exhaustion is a common issue on high-traffic servers.

Investigate in this order:

1. Operating system `ulimit`
2. Open file descriptor count
3. `worker_rlimit_nofile`
4. `worker_connections`
5. Keepalive configuration
6. Backend connection pooling
7. Traffic patterns

A properly tuned Linux system should rarely encounter this issue under normal production workloads.

---
