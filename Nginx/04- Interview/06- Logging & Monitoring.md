# Overview

Logging and monitoring are essential for operating Nginx in production. While configuration determines how Nginx behaves, logs and monitoring reveal how it is actually performing under real-world traffic.

Nginx generates detailed logs for every request and error, making them invaluable for troubleshooting, performance tuning, security analysis, and capacity planning.

This chapter explains how Nginx logs requests, how to customize logging, and how to monitor the health and performance of an Nginx server.

---

# Why Logging Matters

Logs help answer questions such as:

- Is the server receiving requests?
- Why did a request fail?
- Which client generated an error?
- Which endpoints receive the most traffic?
- How long do requests take?
- Are users receiving 404 or 500 errors?
- Is the server under attack?

Without proper logging, diagnosing production issues becomes extremely difficult.

---

# Types of Logs

Nginx primarily generates two types of logs.

## Access Log

Records every successful and unsuccessful HTTP request.

Example:

```text
192.168.1.25 - - [15/Jul/2026:10:35:22 +0000] "GET /api/products HTTP/1.1" 200 1532 "-" "Mozilla/5.0"
```

Information includes:

- Client IP
- Timestamp
- HTTP Method
- Requested URL
- HTTP Version
- Status Code
- Response Size
- User Agent

---

## Error Log

Records errors, warnings, and diagnostic information.

Example:

```text
2026/07/15 10:36:18 [error] 1523#1523: *45 connect() failed (111: Connection refused)
```

Common events include:

- Configuration errors
- Backend failures
- Permission issues
- SSL errors
- Startup failures

---

# Default Log Locations

Common Linux locations:

```text
Access Log

/var/log/nginx/access.log
```

```text
Error Log

/var/log/nginx/error.log
```

The actual location depends on the operating system and distribution.

---

# Configuring Access Logs

Example:

```nginx
access_log /var/log/nginx/access.log;
```

To disable logging for a specific location:

```nginx
location /health {

    access_log off;

}
```

This is useful for high-frequency endpoints such as health checks.

---

# Configuring Error Logs

Example:

```nginx
error_log /var/log/nginx/error.log;
```

The error log can be configured globally or per server block.

---

# Error Log Levels

Nginx supports multiple logging levels.

```text
debug

info

notice

warn

error

crit

alert

emerg
```

Example:

```nginx
error_log /var/log/nginx/error.log warn;
```

Choosing an appropriate log level helps balance useful diagnostics with log volume.

---

# Custom Log Formats

Nginx allows custom access log formats using the `log_format` directive.

Example:

```nginx
log_format main
'$remote_addr - $remote_user [$time_local] '
'"$request" $status $body_bytes_sent '
'"$http_referer" "$http_user_agent"';
```

Enable the format:

```nginx
access_log /var/log/nginx/access.log main;
```

Custom log formats allow organizations to capture only the information they require.

---

# Common Log Variables

Frequently used variables include:

| Variable | Description |
|----------|-------------|
| `$remote_addr` | Client IP address |
| `$host` | Requested host |
| `$request` | Complete HTTP request |
| `$request_uri` | Requested URI |
| `$status` | HTTP status code |
| `$body_bytes_sent` | Response size |
| `$request_time` | Request processing time |
| `$http_user_agent` | Client browser |
| `$http_referer` | Referring page |

These variables can be combined to create detailed log formats.

---

# Request Lifecycle and Logging

A simplified request flow:

```text
Client
    │
    ▼
Nginx
    │
    ▼
Process Request
    │
    ▼
Generate Response
    │
    ▼
Write Access Log
```

If an error occurs:

```text
Client
    │
    ▼
Nginx
    │
    ▼
Processing Error
    │
    ▼
Write Error Log
```

---

# Monitoring Important Metrics

Production environments should continuously monitor:

- Active connections
- Requests per second
- Response time
- Error rate
- CPU utilization
- Memory usage
- Disk usage
- Network throughput
- SSL certificate expiration

Monitoring helps identify performance issues before they impact users.

---

# Nginx Status Module

The `stub_status` module provides basic runtime statistics.

Example:

```nginx
location /nginx_status {

    stub_status;

}
```

Example output:

```text
Active connections: 291

server accepts handled requests

 5234 5234 8421

Reading: 2 Writing: 4 Waiting: 285
```

Useful metrics include:

- Active connections
- Accepted connections
- Total requests
- Reading connections
- Writing connections
- Idle connections

---

# Log Rotation

Log files continuously grow in production.

A typical maintenance process is:

```text
Write Logs
     │
     ▼
Rotate Logs
     │
     ▼
Compress Old Logs
     │
     ▼
Archive or Delete
```

Log rotation prevents disks from filling up and keeps log files manageable.

---

# Monitoring Workflow

```text
Incoming Requests
        │
        ▼
Collect Logs
        │
        ▼
Analyze Metrics
        │
        ▼
Detect Problems
        │
        ▼
Investigate Root Cause
        │
        ▼
Apply Fix
```

Continuous monitoring enables faster incident detection and resolution.

---

# Real-World Example

A production API begins returning intermittent **502 Bad Gateway** errors.

Investigation process:

1. Check the error log for backend connection failures.
2. Review the access log for affected endpoints.
3. Examine request timestamps and response times.
4. Verify backend service availability.
5. Monitor CPU and memory usage.
6. Reload or restart services if necessary.

The logs reveal repeated connection failures between Nginx and the backend service, allowing engineers to identify and resolve the issue quickly.

---

# Best Practices

- Enable both access and error logging in production.
- Use appropriate error log levels.
- Create custom log formats when additional information is required.
- Rotate logs regularly.
- Exclude noisy endpoints such as health checks from access logs when appropriate.
- Monitor request latency and error rates.
- Review logs proactively instead of waiting for incidents.
- Protect log files because they may contain sensitive information.

---

# Key Takeaways

- Nginx generates access logs for requests and error logs for failures.
- Proper logging is essential for troubleshooting, auditing, and performance analysis.
- Custom log formats allow organizations to capture relevant request information.
- The `stub_status` module provides basic runtime metrics.
- Continuous monitoring helps detect issues before they become production incidents.
- Well-managed logs are a critical part of operating reliable and secure Nginx deployments.