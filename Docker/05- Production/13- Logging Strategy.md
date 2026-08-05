# Logging Strategy

## Overview

Logs are one of the most important sources of information when operating applications in production. They help developers understand application behavior, diagnose failures, investigate security incidents, and monitor system health.

In containerized environments, logging becomes even more important because containers are designed to be ephemeral. When a container is removed, any logs stored only inside the container are lost.

A good logging strategy ensures that logs are collected, centralized, searchable, and retained for future analysis.

---

# Why Logging Matters

Without logging:

```text
Application Error

↓

Application Stops

↓

No Information

↓

Difficult Troubleshooting
```

With logging:

```text
Application Error

↓

Log Generated

↓

Log Collection

↓

Investigation

↓

Problem Resolved
```

---

# What Should Be Logged?

Applications should log important operational events.

Examples include:

- Application startup
- Application shutdown
- Incoming requests
- Errors
- Exceptions
- Authentication attempts
- Database failures
- External API failures
- Background jobs
- Health check failures

---

# Logging Workflow

```text
Application

↓

stdout / stderr

↓

Docker

↓

Log Driver

↓

Log Storage

↓

Monitoring Dashboard
```

---

# Standard Output Logging

Containers should write logs to:

```text
stdout

stderr
```

Avoid writing logs only to files inside containers.

Docker automatically captures standard output streams.

---

# Docker Logging

Example

```bash
docker logs container_name
```

View logs in real time

```bash
docker logs -f container_name
```

View the last 100 lines

```bash
docker logs --tail 100 container_name
```

---

# Logging Levels

Applications should use consistent logging levels.

| Level | Purpose |
|--------|----------|
| DEBUG | Detailed debugging information |
| INFO | Normal application events |
| WARNING | Unexpected but recoverable situations |
| ERROR | Failed operations |
| CRITICAL | Serious failures requiring immediate attention |

---

# Example Python Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

logger.info("Application started")

logger.warning("Cache miss")

logger.error("Database connection failed")
```

---

# Structured Logging

Instead of

```text
User login failed
```

Prefer structured logs.

Example

```json
{
    "timestamp": "2026-08-05T10:15:22Z",
    "level": "ERROR",
    "service": "backend-api",
    "endpoint": "/login",
    "status": 401,
    "message": "Authentication failed"
}
```

Benefits

- Easier searching
- Better filtering
- Machine readable
- Compatible with log aggregation tools

---

# Logging Architecture

```text
Application

↓

Docker

↓

Log Driver

↓

Centralized Logging

↓

Dashboard
```

---

# Docker Log Drivers

Docker supports multiple log drivers.

| Driver | Description |
|---------|-------------|
| json-file | Default Docker log driver |
| local | Optimized local storage |
| journald | Linux system journal |
| syslog | System logging server |
| fluentd | Fluentd collector |
| gelf | Graylog Extended Log Format |
| awslogs | Amazon CloudWatch Logs |

---

# Configure Log Rotation

Without log rotation:

```text
Logs

↓

Grow Forever

↓

Disk Full

↓

Application Problems
```

Example

```yaml
logging:

  driver: json-file

  options:

    max-size: "10m"

    max-file: "5"
```

Benefits

- Prevents disk exhaustion
- Limits storage usage
- Improves stability

---

# Logging in Docker Compose

Example

```yaml
services:

  api:

    logging:

      driver: json-file

      options:

        max-size: "20m"

        max-file: "10"
```

---

# Centralized Logging

Production systems usually collect logs in one place.

```text
Application

↓

Docker

↓

Log Collector

↓

Central Log Server

↓

Dashboard
```

Common platforms include:

- Elasticsearch
- OpenSearch
- Loki
- Splunk
- Graylog
- Amazon CloudWatch Logs

---

# Request Logging

Log important request information.

Example

```text
Timestamp

Client IP

HTTP Method

URL

Response Status

Response Time
```

Avoid logging sensitive request data.

---

# Error Logging

Log:

- Stack traces
- Error messages
- Exception type
- Request ID
- Timestamp

Example

```text
ERROR

Database connection timeout

Request ID: 7d93fa82
```

---

# Correlation IDs

Distributed systems often attach a request identifier.

```text
Request

↓

Correlation ID

↓

Service A

↓

Service B

↓

Database
```

This makes it easier to trace a request across multiple services.

---

# Sensitive Data

Never log:

- Passwords
- API keys
- JWT tokens
- Credit card numbers
- Personal identification numbers
- Private keys

Bad

```text
User password: mypassword123
```

Good

```text
Authentication failed for user alice@example.com
```

---

# Log Retention

Logs should not be kept forever.

Typical retention periods

| Environment | Example |
|-------------|---------|
| Development | Few days |
| Testing | Few weeks |
| Production | Several months (based on business or regulatory requirements) |

Retention policies should follow organizational and legal requirements.

---

# Monitoring Logs

Monitor for:

- Frequent exceptions
- Restart loops
- Failed health checks
- Authentication failures
- High response times
- Unexpected traffic spikes

Monitoring turns logs into actionable insights.

---

# Logging Lifecycle

```text
Application Event

↓

Log Generated

↓

Docker

↓

Log Storage

↓

Analysis

↓

Alert

↓

Resolution
```

---

# Common Mistakes

## Logging Inside Containers

Logs stored only inside containers disappear when containers are removed.

---

## Logging Sensitive Data

Sensitive information should never appear in logs.

---

## No Log Rotation

Large log files eventually consume all available disk space.

---

## Excessive DEBUG Logging

Verbose logging in production increases storage costs and makes important events harder to find.

Use INFO or WARNING as the default production log level.

---

## Ignoring Error Logs

Error logs should be reviewed regularly.

Repeated errors often indicate deeper application issues.

---

# Production Checklist

Before deployment:

- Logging enabled
- stdout/stderr used
- Log rotation configured
- Structured logging implemented
- Sensitive information excluded
- Error logging verified
- Request logging configured
- Log retention policy defined
- Centralized logging configured
- Monitoring alerts enabled

---

# Best Practices

- Write application logs to stdout and stderr.
- Use structured logging whenever possible.
- Configure log rotation to prevent disk exhaustion.
- Include timestamps, log levels, and request identifiers.
- Never log secrets or personally sensitive information.
- Centralize logs for easier monitoring and troubleshooting.
- Review logs regularly for operational and security issues.
- Keep logging levels appropriate for each environment.

---

# Key Takeaways

- Logging is essential for troubleshooting, monitoring, and maintaining production applications.
- Containers should write logs to stdout and stderr so Docker can collect them automatically.
- Structured logging improves searchability and integration with monitoring platforms.
- Log rotation and centralized log collection are critical for long-running production systems.
- A well-designed logging strategy improves observability while protecting sensitive information and controlling storage usage.