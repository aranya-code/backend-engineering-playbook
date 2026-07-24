# Sentinel & Failover Issues

## Overview

Redis Sentinel provides **High Availability (HA)** by monitoring Redis instances, detecting failures, and automatically promoting a replica when the primary becomes unavailable.

Without Sentinel, a primary node failure requires manual intervention. With Sentinel, failover can occur automatically, minimizing downtime.

However, Sentinel itself can encounter operational issues that prevent successful failover or cause unnecessary failovers.

Common symptoms include:

```text
No failover occurred
```

```text
Master is down after election
```

```text
Sentinel cannot reach master
```

```text
Replica was never promoted
```

```text
Frequent failovers
```

This chapter explains how to troubleshoot Redis Sentinel and failover problems in production.

---

# Redis Sentinel Architecture

```
                   Clients
                      │
                      ▼
             +-----------------+
             |    Sentinel     |
             +-----------------+
              ▲      ▲      ▲
              │      │      │
     Monitoring Monitoring Monitoring
              │      │      │
              ▼      ▼      ▼
        +-------------------------+
        |       Primary           |
        +-------------------------+
             │             │
      Replication     Replication
             ▼             ▼
      +-----------+   +-----------+
      | Replica 1 |   | Replica 2 |
      +-----------+   +-----------+
```

Sentinel continuously monitors every Redis node.

---

# How Sentinel Works

```
Monitor Primary

        │

        ▼

Primary Failure?

        │

 ┌──────┴──────┐

 │             │

No            Yes

 │             │

Continue     Start Election

                │

                ▼

      Promote Best Replica

                │

                ▼

 Notify Clients

                │

                ▼

 Resume Operations
```

---

# Common Sentinel Problems

| Problem | Symptoms |
|----------|----------|
| Sentinel cannot reach primary | No monitoring |
| No quorum | Failover never starts |
| Replica not promoted | Primary remains unavailable |
| Split brain | Multiple primaries |
| Frequent failovers | Cluster instability |
| DNS issues | Sentinel loses connectivity |
| Firewall | Sentinel cannot communicate |

---

# Step 1 — Verify Sentinel Status

Run

```bash
redis-cli -p 26379 INFO Sentinel
```

Example

```text
sentinel_masters:1

sentinel_tilt:0
```

---

# Step 2 — View Monitored Masters

```bash
SENTINEL masters
```

Example

```text
name

redis-master

status

ok
```

---

# Step 3 — View Replicas

```bash
SENTINEL replicas redis-master
```

Verify

- Replica status
- IP address
- Port
- Replication lag

---

# Step 4 — View Other Sentinels

```bash
SENTINEL sentinels redis-master
```

Verify

- Reachability
- IP addresses
- Ports

---

# Quorum

Sentinel requires a majority vote.

Example

```
5 Sentinels

↓

Need 3 Votes

↓

Failover Starts
```

Without quorum

```
Primary Down

↓

No Election

↓

No Promotion
```

---

# Quorum Configuration

Example

```conf
sentinel monitor redis-master 10.0.0.10 6379 3
```

The last number

```
3
```

represents the quorum.

---

# Subjectively Down (SDOWN)

```
Sentinel

↓

Cannot Reach Primary

↓

SDOWN
```

Only one Sentinel believes the primary is unavailable.

---

# Objectively Down (ODOWN)

```
Multiple Sentinels

↓

Agree Primary Failed

↓

ODOWN

↓

Election Begins
```

ODOWN triggers failover.

---

# Election Process

```
Sentinels

↓

Leader Election

↓

Winning Sentinel

↓

Replica Promotion

↓

Cluster Updated
```

Only one Sentinel coordinates failover.

---

# Replica Promotion

```
Replica

↓

STOP Replication

↓

Become Primary

↓

Accept Writes
```

Remaining replicas begin replicating from the new primary.

---

# Verify Failover

Run

```bash
INFO replication
```

Expected

```text
role:master
```

Former primary

```text
role:slave
```

after recovery.

---

# Replica Selection

Sentinel prefers replicas with

- Lowest lag
- Highest replication offset
- Stable connectivity
- High priority

Priority

```conf
replica-priority 100
```

Lower numbers have higher priority.

---

# Split Brain

Incorrect scenario

```
Network Partition

        │

 ┌──────┴──────┐

 │             │

Primary A   Promoted Replica

 │             │

Both Accept Writes
```

Result

```
Data Inconsistency
```

Prevent split-brain through proper quorum and network design.

---

# Frequent Failovers

Causes

- Packet loss
- High latency
- CPU starvation
- Network instability
- Incorrect timeout values

Repeated failovers reduce application availability.

---

# Down-After Timeout

Example

```conf
sentinel down-after-milliseconds redis-master 5000
```

Too low

↓

False failovers

Too high

↓

Slow recovery

---

# Failover Timeout

Example

```conf
sentinel failover-timeout redis-master 60000
```

Controls failover coordination timing.

---

# Parallel Synchronization

Example

```conf
sentinel parallel-syncs redis-master 1
```

Determines how many replicas synchronize simultaneously.

---

# Authentication Problems

Primary

```conf
requirepass StrongPassword
```

Sentinel

```conf
sentinel auth-pass redis-master StrongPassword
```

Passwords must match.

---

# Firewall Issues

Required communication

```
Sentinel

↓

26379
```

Redis

```
6379
```

Verify both ports are accessible.

---

# DNS Problems

Sentinel depends on stable host resolution.

Verify

```bash
nslookup redis-master
```

---

# Docker Deployment

Architecture

```
Sentinel Container

↓

Docker Network

↓

Redis Containers
```

Avoid using container IPs directly.

Prefer service names.

---

# Kubernetes Deployment

```
Sentinel Pods

↓

Headless Service

↓

Redis Pods
```

Verify

```bash
kubectl get pods
```

Inspect

```bash
kubectl logs redis-sentinel
```

---

# AWS Considerations

AWS ElastiCache manages failover automatically.

Redis Sentinel is generally unnecessary when using ElastiCache with Multi-AZ enabled.

Monitor

- Failover events
- Node replacement
- Replication lag

---

# Useful Commands

Primary information

```bash
INFO replication
```

Masters

```bash
SENTINEL masters
```

Replicas

```bash
SENTINEL replicas redis-master
```

Sentinels

```bash
SENTINEL sentinels redis-master
```

Health

```bash
PING
```

---

# Diagnostic Workflow

```
Failover Failed

        │

        ▼

Primary Reachable?

        │

 ┌──────┴───────┐

 │              │

Yes            No

 │              │

Network     Check Quorum

                │

                ▼

        Election Started?

                │

 ┌──────────────┴─────────────┐

 │                            │

No                           Yes

 │                            │

Configuration          Replica Promotion

 │                            │

 ▼                            ▼

Fix Config             Verify New Primary
```

---

# Common Mistakes

## Only One Sentinel

One Sentinel cannot provide reliable automatic failover.

Deploy at least three Sentinels.

---

## Incorrect Quorum

Setting quorum higher than the available Sentinels prevents failover.

---

## Replica Too Far Behind

Sentinel may avoid promoting replicas with excessive lag.

Monitor replication continuously.

---

## Firewall Blocking Sentinel

Sentinels must communicate with each other and Redis.

Verify firewall rules.

---

## Manual Failover During Election

Avoid manual promotion while Sentinel is already coordinating failover.

---

# Best Practices

- Deploy an odd number of Sentinel instances (3 or 5).
- Place Sentinels on different hosts or availability zones.
- Monitor quorum and election status.
- Keep replica lag low.
- Test failover regularly in staging.
- Synchronize authentication credentials.
- Monitor Sentinel logs continuously.
- Document failover procedures.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Quorum | Use an odd number of Sentinels |
| Replica Lag | Keep as low as possible |
| Network | Low latency between Sentinels |
| Timeouts | Tune carefully |
| Monitoring | Alert on failover events |
| Authentication | Keep credentials synchronized |

---

# Production Considerations

For production deployments:

- Deploy at least three Sentinel nodes across separate failure domains.
- Continuously monitor Sentinel health, quorum, and election events.
- Regularly perform controlled failover drills.
- Keep network latency low between Sentinels and Redis nodes.
- Maintain consistent authentication and configuration across all nodes.
- Integrate Sentinel logs with centralized monitoring and alerting systems.
- Document recovery procedures for failed or partial failovers.

---

# Summary

Redis Sentinel provides automated high availability by monitoring primary nodes, detecting failures, electing a leader, and promoting replicas. Most Sentinel issues stem from networking problems, quorum misconfiguration, authentication failures, or excessive replication lag. A well-designed Sentinel deployment with proper monitoring and regular failover testing ensures reliable automatic recovery during production incidents.

---

# Key Takeaways

- Sentinel automates Redis failover and high availability.
- Maintain an odd number of Sentinel nodes to ensure quorum.
- Monitor replication lag, election events, and failover status.
- Configure `down-after-milliseconds` and `failover-timeout` carefully.
- Keep authentication and networking consistent across all nodes.
- Test failover procedures regularly before production incidents.
- Prevent split-brain through proper quorum configuration and network design.
- Integrate Sentinel monitoring into your production observability platform.