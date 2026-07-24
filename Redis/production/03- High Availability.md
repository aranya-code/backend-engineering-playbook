# High Availability

## Overview

Redis is often a critical component of modern backend systems.

It powers:

- API caching
- User sessions
- Rate limiting
- Distributed locks
- Leaderboards
- Pub/Sub
- Celery queues
- Feature flags

If Redis becomes unavailable, large portions of an application may stop functioning.

High Availability (HA) ensures that Redis remains operational even when servers, disks, networks, or entire machines fail.

This chapter explores the architectures, technologies, and best practices used to build highly available Redis deployments.

---

# What is High Availability?

High Availability (HA) is the ability of a system to continue operating despite failures.

Instead of

```
Redis

↓

Crash

↓

Application Down
```

HA provides

```
Redis

↓

Crash

↓

Automatic Recovery

↓

Application Continues
```

---

# Why High Availability Matters

Suppose Redis stores sessions.

```
Users

↓

Login

↓

Redis
```

Redis crashes.

```
Redis Down

↓

Sessions Lost

↓

Users Logged Out
```

Business impact

- Poor user experience
- Revenue loss
- Increased support requests

---

# Availability Targets

Availability is usually expressed as uptime.

| Availability | Downtime Per Year |
|--------------|------------------:|
| 99% | ~3.65 Days |
| 99.9% | ~8.8 Hours |
| 99.99% | ~52 Minutes |
| 99.999% | ~5 Minutes |

Enterprise systems commonly target

```
99.99%

or

99.999%
```

---

# Single Redis Deployment

```
Application

      │

      ▼

    Redis
```

Problem

```
Redis Failure

↓

Application Failure
```

Single-node deployments are not highly available.

---

# Primary-Replica Architecture

```
           Application

                 │

                 ▼

            Primary Redis

                 │

      ┌──────────┴──────────┐

      ▼                     ▼

 Replica 1             Replica 2
```

The primary handles writes.

Replicas continuously synchronize.

---

# Replication Workflow

```
SET user:1

↓

Primary

↓

Replica 1

↓

Replica 2
```

Applications always write to the primary.

---

# Failure Scenario

```
Primary

↓

Crash
```

Replicas still contain recent data.

Without automatic failover

```
Manual Promotion

↓

Application Restart
```

Recovery is slow.

---

# Redis Sentinel

Redis Sentinel solves automatic failover.

Architecture

```
             Sentinel

      ┌────────┼────────┐

      ▼        ▼        ▼

 Sentinel  Sentinel  Sentinel

        │

        ▼

    Primary Redis

        │

    Replica Redis
```

Sentinel continuously monitors Redis.

---

# Why Multiple Sentinels?

Using only one Sentinel introduces another single point of failure.

Recommended

```
Sentinel 1

Sentinel 2

Sentinel 3
```

Majority voting determines failures.

---

# Automatic Failover

Suppose

```
Primary

↓

Crash
```

Sentinel detects

↓

Promotes

↓

Replica

↓

New Primary

↓

Applications Reconnect

Downtime is minimized.

---

# Sentinel Workflow

```
Application

↓

Sentinel

↓

Current Primary

↓

Redis
```

Applications never hardcode the Redis server.

---

# Redis Cluster High Availability

Redis Cluster combines

- Sharding
- Replication
- Automatic failover

```
            Cluster

   ┌────────┼────────┐

   ▼        ▼        ▼

Primary1 Primary2 Primary3

   │         │         │

Replica1 Replica2 Replica3
```

Each primary has a replica.

---

# Cluster Failover

```
Primary 2

↓

Failure

↓

Replica 2

↓

Promoted

↓

Cluster Updated
```

Applications continue operating.

---

# Split-Brain Protection

Network failures can divide infrastructure.

```
Network Partition

↓

Primary A

Primary B
```

Without coordination

Both may accept writes.

Sentinel prevents this through quorum voting.

---

# Quorum

Example

```
3 Sentinels
```

At least

```
2

↓

Agree

↓

Failover
```

This prevents accidental promotions.

---

# Read Availability

Applications may continue reading during failures.

```
Application

│

├── Reads

│

▼

Replicas

│

└── Writes

↓

Primary
```

Read traffic remains available even if one replica fails.

---

# Multi-Replica Deployment

```
Primary

│

├── Replica 1

├── Replica 2

└── Replica 3
```

Advantages

- Better redundancy
- Read scaling
- Faster recovery

---

# Multi-Data Center Architecture

```
           Region A

              │

        Primary Redis

              │

────────Replication────────

              │

              ▼

           Region B

         Replica Redis
```

Provides disaster recovery.

---

# Multi-Region Architecture

```
US

↓

Redis Cluster
```

```
Europe

↓

Redis Cluster
```

```
Asia

↓

Redis Cluster
```

Applications connect to the nearest region.

---

# Failure Detection

Sentinel periodically sends

```
PING
```

If Redis stops responding

↓

Marked

```
Subjectively Down
```

Multiple Sentinels agree before

```
Objectively Down
```

Then failover begins.

---

# Application Recovery

Applications should reconnect automatically.

```
Redis Failure

↓

Reconnect

↓

Retry

↓

Continue
```

Avoid requiring manual restarts.

---

# Connection Pool Recovery

Connection pools should detect failures.

```
Old Connection

↓

Closed

↓

New Connection

↓

Continue
```

Modern Redis clients handle this automatically.

---

# Retry Strategy

Temporary failures occur.

```
Application

↓

Redis Timeout

↓

Retry

↓

Success
```

Use exponential backoff.

Avoid infinite retries.

---

# Graceful Degradation

Redis should not always cause total application failure.

Example

```
Redis Down

↓

Cache Miss

↓

Database

↓

Return Response
```

Application remains functional.

---

# High Availability for Celery

```
Celery

↓

Redis Broker

↓

Sentinel

↓

Primary

↓

Replica
```

Workers reconnect after failover.

Queued jobs remain available when persistence is enabled.

---

# High Availability for Sessions

```
Application

↓

Redis

↓

Replication

↓

Automatic Failover
```

Users remain logged in during failures.

---

# High Availability for Rate Limiting

```
API

↓

Redis

↓

Failure

↓

Fallback Strategy
```

Possible fallback

- Conservative limits
- Local in-memory cache
- Temporary bypass (depending on business risk)

---

# Monitoring High Availability

Monitor

- Replication lag
- Replica status
- Failover events
- Sentinel health
- Connected clients
- Latency
- Memory usage
- Network partitions

---

# Testing Failover

Production teams should regularly perform failover drills.

Example

```
Stop Primary

↓

Sentinel Detects

↓

Replica Promoted

↓

Application Continues
```

Testing validates operational readiness.

---

# Recovery Time Objective (RTO)

RTO

```
Failure

↓

Recovery
```

Measures

```
How quickly service returns.
```

Lower is better.

---

# Recovery Point Objective (RPO)

RPO

```
Failure

↓

Data Loss
```

Measures

```
How much data can be lost.
```

Smaller values require stronger persistence.

---

# Disaster Recovery

Suppose an entire data center fails.

```
Region Failure

↓

Secondary Region

↓

Traffic Redirected

↓

Applications Continue
```

Requires advance planning and testing.

---

# Common High Availability Architectures

### Small Production

```
Application

↓

Primary

↓

Replica

↓

Sentinel
```

---

### Enterprise

```
Applications

↓

Load Balancer

↓

Redis Cluster

↓

Replicas

↓

Sentinel
```

---

### Cloud Native

```
Kubernetes

↓

Redis Cluster

↓

Persistent Volumes

↓

Monitoring

↓

Automatic Recovery
```

---

# Common Mistakes

## Single Redis Server

One server

↓

One failure

↓

Entire application affected.

---

## No Replication

Hardware failure

↓

Complete outage.

---

## Only One Sentinel

Sentinel itself becomes the single point of failure.

Deploy at least three Sentinels.

---

## Ignoring Replication Lag

Replicas may be slightly behind.

Avoid sending critical reads to lagging replicas.

---

## Never Testing Failover

Automatic failover should be verified regularly.

---

## No Persistence

Failover without persistence may still lose recent data.

---

# Best Practices

- Deploy Redis with at least one replica in production.
- Use Redis Sentinel for automatic failover.
- Use Redis Cluster for both high availability and horizontal scaling.
- Configure applications to reconnect automatically after failover.
- Continuously monitor replication lag and Sentinel health.
- Combine high availability with persistence and backups.
- Perform scheduled failover testing.
- Document recovery procedures for operational teams.

---

# Performance Considerations

| Technique | Benefit |
|-----------|----------|
| Replication | Better availability |
| Sentinel | Automatic failover |
| Cluster | Availability + scaling |
| Connection Pool Recovery | Faster reconnection |
| Graceful Degradation | Improved resilience |
| Multi-Region | Disaster recovery |

---

# Production Considerations

For production deployments:

- Deploy Redis across multiple availability zones whenever possible.
- Place Sentinel instances on separate hosts to avoid correlated failures.
- Configure application retry logic with exponential backoff and reasonable timeouts.
- Test automatic failover during maintenance windows before relying on it in production.
- Monitor replication lag to prevent stale reads.
- Combine replication, persistence, backups, and disaster recovery planning into a unified availability strategy.

---

# Summary

High Availability ensures Redis remains operational despite hardware failures, software crashes, or network disruptions. By combining replication, Redis Sentinel, Redis Cluster, automatic failover, monitoring, and well-designed recovery procedures, organizations can build resilient Redis infrastructures capable of supporting mission-critical applications with minimal downtime.

---

# Key Takeaways

- High Availability minimizes downtime and service disruption.
- Primary-replica deployments provide redundancy and read scalability.
- Redis Sentinel automates failure detection and failover.
- Redis Cluster combines high availability with horizontal scaling.
- Deploy at least three Sentinel instances to establish quorum.
- Applications should reconnect automatically after Redis failover.
- Regularly test failover and disaster recovery procedures.
- Combine high availability with persistence, backups, and monitoring for enterprise-grade reliability.