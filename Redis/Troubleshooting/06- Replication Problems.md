# Replication Problems

## Overview

Redis replication enables one or more replica nodes to maintain copies of a primary node, providing:

- High Availability
- Read Scaling
- Disaster Recovery
- Backup Support
- Reduced Load on Primary

Although replication is asynchronous and generally reliable, production deployments may encounter replication failures that lead to stale data, increased replication lag, failover issues, or complete replica disconnection.

Common symptoms include:

```text
MASTER <-> REPLICA sync failed
```

```text
Connection with master lost
```

```text
Replication timeout
```

```text
Replica is stale
```

```text
LOADING Redis is loading the dataset
```

---

# How Replication Works

```
                Write Requests
                      │
                      ▼
              +----------------+
              |    Primary     |
              +----------------+
                  │        │
      Replication │        │ Replication
                  ▼        ▼
          +-----------+ +-----------+
          | Replica 1 | | Replica 2 |
          +-----------+ +-----------+
```

Only the primary accepts writes.

Replicas receive updates asynchronously.

---

# Replication Workflow

```
Replica Starts

      │

      ▼

Connect to Primary

      │

      ▼

Authentication

      │

      ▼

Initial Synchronization

      │

      ▼

Receive Replication Stream

      │

      ▼

Stay Synchronized
```

---

# Common Replication Problems

| Problem | Symptoms |
|----------|----------|
| Replica disconnected | Reads fail or become stale |
| Replication lag | Old data returned |
| Authentication failure | Replica never syncs |
| Full resynchronization | High CPU and network usage |
| Network interruption | Frequent reconnects |
| Disk bottleneck | Slow synchronization |
| Memory pressure | Replica instability |

---

# Step 1 — Verify Replication Status

Run

```bash
redis-cli INFO replication
```

Example

```text
role:master

connected_slaves:2
```

Replica

```text
role:slave

master_link_status:up
```

The most important fields are:

- role
- master_link_status
- master_last_io_seconds_ago
- slave_repl_offset
- master_repl_offset

---

# Healthy Replication

```
Primary

↓

Replication Stream

↓

Replica

↓

master_link_status = up
```

Healthy replicas continuously receive updates.

---

# Detecting Replica Disconnects

Example

```text
master_link_status:down
```

Possible causes

- Network failure
- Primary unavailable
- Authentication error
- Firewall
- Incorrect configuration

---

# Replication Lag

Architecture

```
Application

↓

Replica

↓

Old Data
```

Lag causes replicas to return stale information.

Check

```bash
INFO replication
```

Look for

```text
master_last_io_seconds_ago
```

Lower values indicate healthy communication.

---

# Replication Offset

Redis tracks synchronization progress.

```
Primary Offset

↓

Replica Offset
```

Example

```text
master_repl_offset

slave_repl_offset
```

Offsets should remain close.

Large differences indicate lag.

---

# Full Synchronization

Sometimes Redis performs a complete synchronization.

```
Replica

↓

SYNC

↓

RDB Snapshot

↓

Transfer

↓

Load

↓

Replication Stream
```

Full synchronization is expensive.

---

# Partial Synchronization

Preferred workflow

```
Connection Lost

↓

Reconnect

↓

Continue Stream
```

Redis uses replication backlog to avoid unnecessary full synchronization.

---

# Replication Backlog

Check

```bash
CONFIG GET repl-backlog-size
```

Example

```conf
repl-backlog-size 256mb
```

A backlog that is too small increases the frequency of full synchronizations.

---

# Authentication Problems

Primary

```conf
requirepass StrongPassword
```

Replica

```conf
masterauth StrongPassword
```

Passwords must match.

Incorrect authentication results in synchronization failures.

---

# Network Problems

```
Primary

↓

Firewall

↓

Replica
```

Verify connectivity

```bash
ping primary-server
```

Test Redis port

```bash
nc -zv primary-server 6379
```

---

# Firewall Issues

Verify

- Security Groups
- Network ACLs
- Firewalls
- Kubernetes Network Policies

Replication requires continuous connectivity.

---

# DNS Problems

Replica

```
primary.internal
```

↓

Incorrect DNS

↓

Cannot connect

Verify

```bash
nslookup primary.internal
```

---

# High CPU

Busy primary

↓

Replication delayed

Monitor

```bash
INFO cpu
```

Also inspect

```bash
top
```

---

# Memory Pressure

Check

```bash
INFO memory
```

High eviction rates or memory exhaustion can negatively affect replication.

---

# Disk Bottlenecks

During synchronization

```
Primary

↓

BGSAVE

↓

Disk

↓

Replica
```

Slow storage delays snapshot generation.

Monitor

```bash
iostat
```

---

# Replica Read Only

Verify

```bash
CONFIG GET replica-read-only
```

Expected

```text
yes
```

Replicas should generally remain read-only.

---

# Split Brain

Incorrect architecture

```
Primary A

      ▲

      │

Primary B
```

Two writable primaries create inconsistent datasets.

Avoid manual promotion without coordination.

---

# Docker Replication

Example

```
Primary Container

↓

Docker Network

↓

Replica Container
```

Verify

```bash
docker network inspect bridge
```

---

# Kubernetes Replication

```
Redis Primary Pod

↓

Headless Service

↓

Replica Pods
```

Check

```bash
kubectl get pods
```

Describe

```bash
kubectl describe pod redis-replica
```

Logs

```bash
kubectl logs redis-replica
```

---

# AWS ElastiCache

Monitor CloudWatch

- ReplicationLag
- NetworkBytesIn
- NetworkBytesOut
- EngineCPUUtilization

Configure alerts for increasing lag.

---

# Useful Commands

Replication information

```bash
INFO replication
```

Client information

```bash
CLIENT LIST
```

Server status

```bash
INFO server
```

Statistics

```bash
INFO stats
```

---

# Diagnostic Workflow

```
Replication Issue

        │

        ▼

INFO replication

        │

        ▼

Link Status Up?

        │

 ┌──────┴───────┐

 │              │

No             Yes

 │              │

Network      Check Lag

 │              │

 ▼              ▼

Authentication Offsets

 │              │

 ▼              ▼

Firewall    CPU/Memory

 │              │

 ▼              ▼

Resolve      Monitor
```

---

# Common Mistakes

## Small Replication Backlog

Small backlogs increase full synchronization frequency.

Increase the backlog for busy production systems.

---

## Cross-Region Replication

High network latency naturally increases replication lag.

Deploy replicas close to the primary when low-latency reads are required.

---

## Ignoring Replica Lag

Applications may serve outdated information.

Monitor lag continuously.

---

## Manual Promotion

Improper failover can produce split-brain scenarios.

Always use Sentinel or Cluster for automatic failover.

---

## Sharing Infrastructure

Running the primary and replicas on the same host reduces fault tolerance.

Deploy across different availability zones when possible.

---

# Best Practices

- Monitor replication lag continuously.
- Configure an adequate replication backlog.
- Use reliable, low-latency networking.
- Keep replicas read-only.
- Place replicas in different availability zones.
- Monitor synchronization frequency.
- Secure replication traffic with authentication.
- Test failover procedures regularly.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Network | Minimize latency between primary and replicas |
| Backlog | Increase for busy workloads |
| Disk | Use SSDs for snapshot generation |
| CPU | Monitor during synchronization |
| Authentication | Keep credentials synchronized |
| Monitoring | Alert on replication lag |

---

# Production Considerations

For production deployments:

- Monitor `master_link_status` and `ReplicationLag` continuously.
- Configure alerts for disconnected replicas and repeated full synchronizations.
- Size the replication backlog based on write throughput.
- Separate primary and replicas across hosts or availability zones.
- Test replica recovery and failover procedures regularly.
- Avoid serving strongly consistent reads from replicas when replication lag is unacceptable.
- Document replication topology and recovery procedures.

---

# Summary

Redis replication is fundamental to high availability and read scalability, but it introduces operational challenges such as lag, synchronization failures, and network-related issues. By monitoring replication health, maintaining proper backlog sizing, ensuring reliable connectivity, and regularly testing failover scenarios, engineers can keep replication stable and resilient in production.

---

# Key Takeaways

- Verify replication health using `INFO replication`.
- Monitor `master_link_status`, replication offsets, and lag continuously.
- Use an appropriately sized replication backlog to minimize full synchronizations.
- Keep authentication, networking, and firewall rules consistent across nodes.
- Deploy replicas across different hosts or availability zones.
- Avoid split-brain scenarios by using Redis Sentinel or Redis Cluster for failover.
- Continuously test replication recovery and failover procedures before production incidents.