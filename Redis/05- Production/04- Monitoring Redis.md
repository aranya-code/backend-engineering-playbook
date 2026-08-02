# Monitoring Redis

## Overview

Deploying Redis into production is only the beginning. A production Redis deployment must be continuously monitored to detect performance degradation, memory exhaustion, replication issues, network problems, and client bottlenecks before they impact users.

Monitoring Redis enables engineers to:

- Detect failures early
- Prevent outages
- Improve performance
- Capacity plan
- Identify bottlenecks
- Troubleshoot latency
- Maintain Service Level Objectives (SLOs)

A production Redis deployment should never be treated as a "set it and forget it" component.

---

# Why Monitoring Matters

Without monitoring

```
Redis

↓

Memory Full

↓

Evictions

↓

Slow APIs

↓

Users Complain
```

With monitoring

```
Redis

↓

Memory Increasing

↓

Alert Triggered

↓

Scale Redis

↓

Users Never Notice
```

Monitoring allows proactive operations instead of reactive firefighting.

---

# Monitoring Architecture

```
                Redis

                  │

         INFO / Metrics

                  │

                  ▼

            Prometheus

                  │

                  ▼

              Grafana

                  │

                  ▼

         Email / Slack / PagerDuty
```

---

# What Should Be Monitored?

A production Redis deployment should monitor:

- Availability
- Latency
- Memory
- CPU
- Network
- Clients
- Persistence
- Replication
- Cluster health
- Slow commands
- Cache efficiency

---

# Availability Monitoring

The simplest health check is

```bash
redis-cli PING
```

Expected

```
PONG
```

Applications should also perform periodic health checks.

---

# Memory Monitoring

Redis is an in-memory database.

Memory exhaustion is one of the most common production problems.

Useful command

```bash
INFO MEMORY
```

Example output

```
used_memory

used_memory_peak

maxmemory

mem_fragmentation_ratio
```

---

# Memory Usage Workflow

```
Redis

↓

Memory Usage

↓

80%

↓

Warning

↓

90%

↓

Critical Alert
```

Never wait until memory reaches 100%.

---

# CPU Monitoring

Although Redis is efficient, CPU can become saturated due to:

- Large Lua scripts
- Heavy pipelines
- Large key scans
- Compression
- Serialization

Monitor

```
CPU %

System CPU

User CPU
```

---

# Network Monitoring

Redis performance depends heavily on network latency.

Monitor

- Bandwidth
- Packet loss
- Latency
- Network errors

Architecture

```
Application

↓

Network

↓

Redis
```

Network delays often appear as Redis latency.

---

# Client Monitoring

Useful command

```bash
CLIENT LIST
```

Monitor

- Connected clients
- Blocked clients
- Idle clients
- Maximum connections

Example

```
Connected Clients

↓

100

↓

500

↓

5000

↓

Investigate
```

---

# Cache Hit Ratio

One of the most important production metrics.

Formula

```
Cache Hits

-------------------

Hits + Misses
```

Example

```
95%
```

Excellent.

```
50%
```

Needs investigation.

---

# Cache Workflow

```
Request

↓

Redis

↓

Hit?

├── Yes

│

▼

Fast Response

│

└── No

↓

Database
```

Low hit ratios increase database load.

---

# Latency Monitoring

Redis is expected to respond within milliseconds.

Monitor

- Average latency
- P95 latency
- P99 latency
- Maximum latency

Example

```
Average

1 ms
```

```
P99

8 ms
```

Sudden increases indicate problems.

---

# Slow Log

Redis records slow operations.

Command

```bash
SLOWLOG GET
```

Example

```
Command

↓

Execution Time

↓

Arguments
```

Useful for identifying expensive commands.

---

# Slow Log Workflow

```
Command

↓

Slow?

↓

Logged

↓

Engineer Reviews
```

---

# Monitoring Persistence

Command

```bash
INFO Persistence
```

Monitor

- Last successful save
- AOF rewrite
- Background save status
- Save failures

---

# Replication Monitoring

Command

```bash
INFO Replication
```

Important metrics

- Role
- Connected replicas
- Replication lag
- Synchronization state

Architecture

```
Primary

↓

Replica

↓

Replica
```

Replication lag should remain low.

---

# Cluster Monitoring

Monitor

- Node status
- Slot allocation
- Failover events
- Cluster state

Useful command

```bash
CLUSTER INFO
```

---

# Eviction Monitoring

Redis begins evicting keys when memory is exhausted.

Monitor

```
Evicted Keys
```

Large increases often indicate

- Incorrect TTL
- Insufficient memory
- Poor cache strategy

---

# Expiration Monitoring

Track

```
Expired Keys
```

Unexpected spikes may indicate

- Incorrect TTL values
- Application bugs

---

# Keyspace Monitoring

Useful command

```bash
INFO Keyspace
```

Shows

- Number of keys
- Expiration statistics
- Database usage

---

# Command Statistics

Useful command

```bash
INFO Commandstats
```

Example

```
GET

SET

DEL

HGET

HSET
```

Helps identify workload patterns.

---

# Redis INFO Command

General command

```bash
INFO
```

Provides

- Server information
- Clients
- Memory
- CPU
- Persistence
- Replication
- Statistics
- Keyspace

---

# Redis Insight

Redis Insight provides a graphical interface.

Features

- Memory visualization
- Key browser
- Slow log
- CLI
- Performance dashboard
- Command statistics

Architecture

```
Redis

↓

Redis Insight

↓

Dashboard
```

---

# Prometheus Integration

Prometheus periodically collects metrics.

```
Redis

↓

Exporter

↓

Prometheus

↓

Grafana
```

Typically uses

```
redis_exporter
```

---

# Grafana Dashboard

Typical dashboard includes

- Memory usage
- CPU usage
- Cache hit ratio
- Network traffic
- Replication lag
- Slow commands
- Connected clients
- Latency

---

# Alerting

Alerts should notify engineers before outages.

Examples

```
Memory > 80%
```

```
Replication Lag > 5 Seconds
```

```
Cache Hit Ratio < 85%
```

```
Connected Clients > 5000
```

```
Redis Down
```

---

# Alert Workflow

```
Redis

↓

Metric Threshold

↓

Alert

↓

On-call Engineer

↓

Investigation

↓

Resolution
```

---

# Capacity Monitoring

Track growth trends.

Monitor

- Dataset size
- Memory growth
- Connection growth
- Request rate
- Disk usage
- CPU utilization

Capacity planning prevents emergency scaling.

---

# Monitoring in Kubernetes

```
Redis Pod

↓

Prometheus

↓

Grafana

↓

Alerts
```

Additional metrics

- Pod restarts
- Container memory
- Container CPU
- PVC usage

---

# Monitoring in AWS

For Amazon ElastiCache

Monitor

- CPU utilization
- Engine CPU
- Free memory
- Cache hits
- Cache misses
- Evictions
- Network throughput

CloudWatch provides these metrics.

---

# Common Monitoring Mistakes

## Monitoring Only CPU

Redis failures are often caused by memory, not CPU.

---

## Ignoring Cache Hit Ratio

High latency may simply be poor cache efficiency.

---

## Never Reviewing Slow Log

Expensive commands remain unnoticed.

---

## No Alerts

Monitoring without alerts provides little operational value.

---

## Alert Fatigue

Avoid excessive alerts.

Instead

```
Actionable Alerts

↓

Investigation

↓

Resolution
```

---

# Best Practices

- Monitor Redis continuously in production.
- Alert on memory, latency, replication, and availability.
- Review slow logs regularly.
- Track cache hit ratio as a primary performance metric.
- Monitor replication lag in high availability deployments.
- Build Grafana dashboards for operational visibility.
- Perform capacity planning using historical trends.
- Test monitoring and alerting during incident simulations.

---

# Performance Considerations

| Metric | Why It Matters |
|----------|----------------|
| Memory Usage | Prevents evictions |
| Cache Hit Ratio | Measures cache efficiency |
| Latency | User experience |
| Connected Clients | Connection health |
| Slow Log | Finds expensive commands |
| Replication Lag | High availability |
| CPU | Processing bottlenecks |
| Network | Communication delays |

---

# Production Considerations

For production deployments:

- Standardize dashboards across all Redis environments.
- Define SLOs and alert thresholds before incidents occur.
- Export metrics to centralized monitoring systems such as Prometheus.
- Correlate Redis metrics with application, database, and infrastructure metrics.
- Periodically review alert thresholds as workloads evolve.
- Monitor trends over time rather than relying solely on current values.

---

# Summary

Monitoring is a critical part of operating Redis in production. By tracking availability, memory, latency, replication, cache efficiency, and client behavior, engineers can detect issues before they affect users. A mature monitoring stack built around Redis metrics, Prometheus, Grafana, and proactive alerting enables reliable, scalable, and highly available Redis deployments.

---

# Key Takeaways

- Continuous monitoring is essential for production Redis deployments.
- Monitor memory, latency, cache hit ratio, replication, and client connections.
- Use `INFO`, `SLOWLOG`, `CLIENT LIST`, and `CLUSTER INFO` for operational insights.
- Integrate Redis with Prometheus and Grafana for centralized observability.
- Configure actionable alerts to detect issues before users are impacted.
- Review historical trends to support capacity planning.
- Monitor both Redis metrics and the surrounding infrastructure.
- Treat monitoring as an ongoing operational practice rather than a one-time setup.