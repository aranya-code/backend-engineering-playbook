# Overview

Logging is one of the most important features of Nginx.

Whenever a client sends a request or an error occurs, Nginx records this information in log files.

Logs help administrators and developers to:

- Monitor traffic
- Troubleshoot issues
- Detect attacks
- Analyze performance
- Audit user activity
- Debug application problems

Without proper logging, diagnosing production issues becomes extremely difficult.

---

# Types of Logs

Nginx primarily maintains two types of logs.

- Access Log
- Error Log

```text
                Nginx

          ┌───────────────┐

          ▼               ▼

    Access Log      Error Log
```

---

# Access Log

The Access Log records every HTTP request processed by Nginx.

Example:

```text
192.168.1.25 - - [16/Jul/2026:18:30:15 +0530] "GET /products HTTP/1.1" 200 5423
```

Each entry contains information about a completed request.

---

# What Does Access Log Record?

Typical information includes:

- Client IP
- Request Method
- Requested URL
- HTTP Version
- Response Status Code
- Response Size
- Request Time
- User Agent
- Referrer

---

# Error Log

The Error Log records problems encountered by Nginx.

Examples include:

- Missing files
- Permission issues
- Invalid configuration
- Backend failures
- SSL errors
- Timeouts

Example:

```text
2026/07/16 18:42:10 [error] 1452#1452:
connect() failed (111: Connection refused)
while connecting to upstream
```

---

# Default Log Locations

Most Linux distributions store logs in:

```text
/var/log/nginx/access.log

/var/log/nginx/error.log
```

Depending on the operating system or installation method, these locations may vary.

---

# Configuring Access Log

Syntax:

```nginx
access_log path format;
```

Example:

```nginx
access_log /var/log/nginx/access.log;
```

---

# Configuring Error Log

Syntax:

```nginx
error_log path level;
```

Example:

```nginx
error_log /var/log/nginx/error.log warn;
```

---

# Error Log Levels

Nginx supports multiple log levels.

| Level | Description |
|---------|-------------|
| debug | Detailed debugging information |
| info | Informational messages |
| notice | Normal but significant events |
| warn | Warnings |
| error | Errors |
| crit | Critical errors |
| alert | Immediate action required |
| emerg | System unusable |

Example:

```nginx
error_log /var/log/nginx/error.log error;
```

Only errors and more severe events are recorded.

---

# Log Format

Nginx allows custom log formats.

Syntax:

```nginx
log_format name 'format';
```

Example:

```nginx
log_format main
'$remote_addr - $host [$time_local] '
'"$request" $status $body_bytes_sent';
```

Then:

```nginx
access_log /var/log/nginx/access.log main;
```

---

# Common Variables Used in Logs

| Variable | Description |
|----------|-------------|
| `$remote_addr` | Client IP Address |
| `$host` | Requested Host |
| `$request` | Complete Request Line |
| `$status` | HTTP Status Code |
| `$body_bytes_sent` | Response Size |
| `$request_time` | Request Processing Time |
| `$http_user_agent` | Browser Information |
| `$http_referer` | Referring URL |

Example:

```nginx
log_format main
'$remote_addr $request $status $request_time';
```

---

# Example Access Log Entry

```text
192.168.1.10 GET /products HTTP/1.1 200 0.142
```

Meaning:

| Value | Description |
|--------|-------------|
| 192.168.1.10 | Client IP |
| GET | HTTP Method |
| /products | Requested URL |
| HTTP/1.1 | Protocol |
| 200 | Response Status |
| 0.142 | Processing Time (seconds) |

---

# Logging Reverse Proxy Requests

When Nginx acts as a reverse proxy, logs become even more valuable.

Architecture:

```text
Browser

↓

Nginx

↓

FastAPI

↓

Database
```

If the backend returns:

```
502 Bad Gateway
```

The Error Log helps identify whether:

- Backend is down
- Network problem
- Timeout occurred
- Connection refused

---

# Logging Request Time

One of the most useful variables is:

```nginx
$request_time
```

Example:

```text
GET /products

↓

0.875 seconds
```

This helps identify slow requests.

---

# Logging Upstream Response Time

When using a reverse proxy:

```nginx
$upstream_response_time
```

Example:

```text
0.624
```

This represents the time taken by the backend server to generate the response.

Useful for identifying slow application servers.

---

# Logging Cache Status

If Proxy Cache is enabled:

```nginx
add_header X-Cache $upstream_cache_status;
```

Possible values:

```
HIT
```

```
MISS
```

```
BYPASS
```

You can also include this information in custom logs.

---

# JSON Log Format

Modern monitoring tools often prefer JSON logs.

Example:

```nginx
log_format json escape=json
'{
    "ip":"$remote_addr",
    "host":"$host",
    "request":"$request",
    "status":"$status",
    "time":"$request_time"
}';
```

Advantages:

- Easy to parse
- Compatible with ELK Stack
- Compatible with Splunk
- Compatible with Grafana Loki

---

# Disabling Logging

Sometimes logging is unnecessary.

Example:

```nginx
location /health {

    access_log off;

}
```

Useful for:

- Health checks
- Monitoring endpoints
- Frequently accessed static resources

---

# Log Rotation

Log files continuously grow.

Instead of deleting them manually, Linux systems typically use **logrotate**.

Benefits:

- Prevents disk exhaustion
- Compresses old logs
- Automatically creates new log files

Typical flow:

```text
access.log

↓

Rotate

↓

access.log.1

↓

Compressed Archive
```

---

# Real-World Example

Production architecture:

```text
Internet

↓

Nginx

↓

Access Log

↓

Error Log

↓

Django

↓

PostgreSQL
```

Suppose users report:

```
502 Bad Gateway
```

Investigation:

1. Check `error.log`
2. Verify backend availability
3. Review upstream errors
4. Check response times

Logs often provide the fastest path to identifying the root cause.

---

# Best Practices

- Always enable Access Logs in production unless there is a specific reason not to.
- Use Error Logs with an appropriate log level.
- Create custom log formats for monitoring.
- Monitor request and upstream response times.
- Rotate logs regularly using logrotate or a centralized logging solution.
- Forward logs to centralized systems such as ELK, Loki, or Splunk in distributed environments.

---

# Common Mistakes

## Disabling Logs Completely

Without logs, diagnosing production issues becomes extremely difficult.

Disable logging only for endpoints where it provides little value.

---

## Logging Sensitive Information

Avoid logging:

- Passwords
- Authentication tokens
- Session IDs
- Credit card numbers
- Personally identifiable information (PII)

Sensitive information should never appear in production logs.

---

## Ignoring Large Log Files

If logs are not rotated, they may consume all available disk space and impact server stability.

---

# Interview Notes

### Beginner Questions

- What are the two main Nginx log files?
- What is the purpose of the Access Log?
- What is the purpose of the Error Log?
- Where are logs typically stored?

---

### Intermediate Questions

- What is a custom log format?
- How do you log request processing time?
- What is `$upstream_response_time`?
- Why are JSON logs commonly used?
- Why is log rotation important?

---

# Key Takeaways

- Nginx maintains two primary logs: **Access Log** and **Error Log**.
- Access Logs record every client request, while Error Logs record server and application issues.
- Custom log formats allow detailed monitoring using built-in variables.
- Variables such as `$request_time` and `$upstream_response_time` are valuable for performance analysis.
- Proper logging and log rotation are essential for troubleshooting, monitoring, and maintaining production systems.