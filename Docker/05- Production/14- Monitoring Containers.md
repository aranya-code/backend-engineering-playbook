# Monitoring Containers

## Overview

Deploying containers into production is only the beginning. To ensure applications remain healthy, responsive, and reliable, they must be continuously monitored.

Monitoring provides visibility into the health, performance, and resource utilization of containers and helps identify problems before they impact users.

A good monitoring strategy answers questions such as:

- Is the application running?
- Is it responding quickly?
- Is CPU usage too high?
- Is memory usage increasing?
- Are containers restarting?
- Are users experiencing errors?

---

# Why Monitoring Matters

Without monitoring:

```text
Application Problem

↓

Users Experience Errors

↓

Team Learns Too Late
```

With monitoring:

```text
Application Problem

↓

Monitoring Detects Issue

↓

Alert Generated

↓

Problem Investigated

↓

Issue Resolved
```

---

# What Should Be Monitored?

A production Docker environment should monitor:

- Container health
- CPU usage
- Memory usage
- Disk usage
- Network traffic
- Restart count
- Application response time
- Error rate
- Database performance
- Queue length
- Log volume

---

# Monitoring Architecture

```text
Application

↓

Docker

↓

Metrics

↓

Monitoring System

↓

Dashboard

↓

Alerts
```

---

# Infrastructure Monitoring

Infrastructure monitoring focuses on the Docker host.

Monitor:

- CPU utilization
- Memory usage
- Disk utilization
- Network throughput
- Available storage
- Host uptime

---

# Container Monitoring

Container monitoring focuses on each running container.

```text
Container

↓

CPU

Memory

Network

Disk

Restart Count

Health
```

---

# Application Monitoring

Application monitoring measures application behavior.

Examples:

- Requests per second
- Response time
- Error rate
- Active users
- API latency
- Background jobs
- Cache hit ratio

---

# Health Monitoring

Applications should expose a health endpoint.

```text
GET /health
```

Example response

```json
{
    "status": "healthy"
}
```

Monitoring systems periodically verify the endpoint.

---

# Resource Monitoring

Monitor resource consumption continuously.

```text
CPU

↓

Memory

↓

Disk

↓

Network
```

Unexpected spikes often indicate performance issues.

---

# Docker Stats

Docker provides live container statistics.

```bash
docker stats
```

Example

```text
CONTAINER      CPU %      MEM USAGE

api            12%        185 MB

redis          3%         40 MB

postgres       18%        520 MB
```

Useful during troubleshooting and capacity planning.

---

# Inspect Running Containers

```bash
docker ps
```

Inspect a specific container.

```bash
docker inspect container_name
```

View logs.

```bash
docker logs container_name
```

---

# Restart Monitoring

Monitor restart counts.

```text
Application

↓

Crash

↓

Restart

↓

Restart Count Increases
```

Frequent restarts usually indicate:

- Application bugs
- Missing dependencies
- Resource exhaustion
- Configuration problems

---

# CPU Monitoring

```text
CPU Usage

↓

Normal

↓

Spike

↓

Investigation
```

Possible causes:

- Infinite loops
- Heavy computation
- Traffic spikes
- Inefficient queries

---

# Memory Monitoring

```text
Memory Usage

↓

Gradually Increases

↓

Memory Leak

↓

OOM Kill
```

Memory trends are often more important than instantaneous usage.

---

# Disk Monitoring

Monitor:

- Free disk space
- Docker image storage
- Volume usage
- Log growth

Example

```text
Logs

↓

Grow

↓

Disk Full

↓

Container Failure
```

---

# Network Monitoring

Track:

- Incoming traffic
- Outgoing traffic
- Request rate
- Network errors
- Connection failures

Network monitoring helps identify connectivity and routing issues.

---

# Response Time Monitoring

```text
User Request

↓

Application

↓

Response Time

↓

Dashboard
```

Monitor:

- Average response time
- 95th percentile (P95)
- 99th percentile (P99)

These metrics provide a better picture than averages alone.

---

# Error Monitoring

Track:

- HTTP 4xx responses
- HTTP 5xx responses
- Exceptions
- Database failures
- Queue failures

Example

```text
500 Internal Server Error

↓

Alert

↓

Investigation
```

---

# Monitoring Workflow

```text
Application

↓

Metrics

↓

Dashboard

↓

Alert

↓

Engineer

↓

Resolution
```

---

# Monitoring Stack

A common monitoring stack consists of:

```text
Application

↓

Prometheus

↓

Grafana

↓

Dashboard
```

Other popular monitoring platforms include:

- Datadog
- New Relic
- Dynatrace
- Amazon CloudWatch
- Azure Monitor
- Google Cloud Monitoring

---

# Alerts

Monitoring should generate alerts for important events.

Examples:

- High CPU usage
- High memory usage
- Container stopped
- Health check failure
- High response time
- Excessive restart count

Example

```text
Health Check Failed

↓

Alert

↓

Engineer Notified
```

---

# Capacity Planning

Monitoring helps determine when additional resources are required.

```text
CPU Usage

↓

Increasing

↓

Scale Application

↓

Performance Restored
```

Capacity planning prevents future outages.

---

# Dashboards

A production dashboard typically displays:

- Container status
- CPU usage
- Memory usage
- Disk utilization
- Network traffic
- Error rate
- Response time
- Active requests
- Restart count

Dashboards provide a quick overview of system health.

---

# Monitoring Lifecycle

```text
Application

↓

Collect Metrics

↓

Store Metrics

↓

Visualize

↓

Alert

↓

Investigate

↓

Resolve
```

---

# Common Mistakes

## Monitoring Only the Host

Healthy servers do not necessarily mean healthy applications.

Monitor both infrastructure and applications.

---

## No Alerts

Collecting metrics without alerts delays incident response.

---

## Ignoring Trends

Historical data often reveals issues before failures occur.

Monitor trends rather than isolated values.

---

## Monitoring Too Many Metrics

Focus on meaningful metrics.

Collecting unnecessary data increases storage costs and complexity.

---

## Never Reviewing Dashboards

Monitoring only provides value when dashboards and alerts are actively used.

---

# Production Checklist

Before deployment:

- Health endpoint implemented
- Resource monitoring enabled
- CPU usage monitored
- Memory usage monitored
- Disk usage monitored
- Network traffic monitored
- Error rates monitored
- Restart counts monitored
- Alerts configured
- Dashboard available
- Monitoring tested

---

# Best Practices

- Monitor both infrastructure and applications.
- Implement health checks for every service.
- Configure alerts for critical failures.
- Track trends over time rather than isolated measurements.
- Monitor resource utilization continuously.
- Review dashboards regularly.
- Keep monitoring lightweight and focused on actionable metrics.
- Use monitoring data for capacity planning and performance optimization.

---

# Key Takeaways

- Monitoring provides continuous visibility into the health and performance of containerized applications.
- Effective monitoring combines infrastructure metrics, container metrics, application metrics, and health checks.
- Alerts enable rapid response to production issues before users are significantly affected.
- Historical metrics support capacity planning, performance tuning, and troubleshooting.
- Monitoring, together with logging and health checks, forms the foundation of a reliable and observable production Docker environment.