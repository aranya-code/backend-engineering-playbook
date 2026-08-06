# Replication Problems

## Overview

Replication is one of Kafka's most important reliability features. Every partition can have multiple replicas distributed across different brokers, ensuring that data remains available even if a broker fails.

When replication becomes unhealthy, Kafka may experience:

- Data loss risk
- Reduced fault tolerance
- Increased latency
- Under Replicated Partitions (URP)
- Frequent leader elections
- Unavailable partitions

Replication issues should always be treated as high-priority production incidents because they directly impact cluster reliability.

---

# How Replication Works

Example:

```text
            Partition 0

          Leader (Broker 1)

           /            \

Follower (Broker 2)   Follower (Broker 3)
```

The leader accepts all writes.

Followers continuously copy data from the leader.

---

# Replication Workflow

```text
Producer

↓

Leader Replica

↓

Follower Replica

↓

Follower Replica

↓

Acknowledgement
```

Followers must remain synchronized with the leader.

---

# Common Replication Problems

Production clusters commonly experience:

- Under Replicated Partitions
- Out-of-Sync Replicas
- Replica fetch delays
- Leader election failures
- Replica stuck
- Slow replication
- Offline replicas
- Replica imbalance
- Insufficient ISR
- Replication throttling

---

# Under Replicated Partitions (URP)

### Symptoms

```text
Leader

↓

Follower

↓

Offline
```

Kafka reports:

```text
Under Replicated Partitions
```

---

### Causes

- Slow broker
- Network latency
- Disk bottleneck
- Broker crash

---

### Solution

Investigate:

- Broker health
- Disk I/O
- Network
- CPU utilization

---

# Out-of-Sync Replica

Example:

```text
Leader

Offset 1200

↓

Follower

Offset 1175
```

The follower has fallen behind.

---

### Causes

- Slow replication
- Network congestion
- Disk latency

---

### Solution

Restore broker performance so followers can catch up.

---

# Shrinking ISR

ISR:

```text
Leader

↓

Follower

↓

Follower
```

After problems:

```text
Leader

↓

Follower
```

ISR size decreases.

---

### Effects

- Lower fault tolerance
- Potential write failures
- Higher risk during broker failure

---

### Solution

Determine why replicas left the ISR and restore synchronization.

---

# Leader Election Problems

Symptoms:

```text
Leader Failure

↓

Election

↓

Delay
```

Frequent leader elections reduce cluster stability.

---

### Causes

- Broker crashes
- Network partition
- Resource exhaustion

---

### Solution

Stabilize brokers before investigating Kafka configuration.

---

# Offline Replicas

Example:

```text
Leader

↓

Follower

↓

Offline
```

Replication cannot complete.

---

### Causes

- Broker stopped
- Disk failure
- Hardware issues

---

### Solution

Restore the failed broker or replace it.

---

# Slow Replica Fetching

Followers continuously fetch data.

```text
Leader

↓

Follower Fetch

↓

Delayed
```

---

### Causes

- Slow disk
- Busy broker
- Network bottleneck

---

### Solution

Monitor:

- Replica fetch latency
- Disk throughput
- Network utilization

---

# Replica Imbalance

Example:

```text
Broker 1

80 Replicas

Broker 2

15 Replicas

Broker 3

10 Replicas
```

One broker performs most of the replication work.

---

### Solution

Rebalance partitions across brokers.

---

# Insufficient ISR

Configuration:

```properties
min.insync.replicas=2
```

Current ISR:

```text
Leader Only
```

Producer:

```properties
acks=all
```

Result:

```text
Write Rejected
```

Kafka refuses writes to protect durability.

---

### Solution

Restore ISR before accepting writes.

---

# Replication Throttling

Sometimes replication is intentionally throttled during:

- Broker migration
- Partition reassignment
- Cluster balancing

Improper throttling may slow recovery.

---

### Solution

Review replication throttle configuration.

---

# Network Problems

Symptoms:

```text
Follower

↓

Slow Network

↓

Replication Delayed
```

---

### Diagnosis

Check:

- Latency
- Packet loss
- Bandwidth

---

### Solution

Resolve network issues before modifying Kafka configuration.

---

# Disk Bottlenecks

Replication requires sequential disk writes.

Slow storage causes:

```text
Leader

↓

Follower

↓

Lag
```

---

### Solution

Use SSD or NVMe storage for production clusters.

---

# High Broker CPU

Heavy CPU utilization may delay replication.

Symptoms:

```text
CPU

95%
```

Followers cannot keep pace.

---

### Solution

Reduce load or add additional brokers.

---

# Broker Failure

Suppose:

```text
Broker 2

↓

Crash
```

Remaining replicas continue serving traffic.

However:

```text
Replication Factor Reduced
```

The failed broker should be restored quickly.

---

# Monitoring Replication

Monitor:

- Under Replicated Partitions
- ISR Count
- Replica Fetch Latency
- Offline Replicas
- Leader Elections
- Broker Availability

Replication metrics should always appear on production dashboards.

---

# Useful Metrics

Important metrics include:

- UnderReplicatedPartitions
- IsrShrinksPerSec
- IsrExpandsPerSec
- OfflinePartitionsCount
- LeaderElectionRate
- ReplicaFetcherManager Metrics

Unexpected changes require investigation.

---

# Monitoring Stack

```text
Kafka

↓

JMX Exporter

↓

Prometheus

↓

Grafana

↓

Alertmanager
```

Critical replication metrics should trigger alerts immediately.

---

# Troubleshooting Workflow

```text
Replication Problem

↓

Check Broker Health

↓

Check Network

↓

Check Disk

↓

Check ISR

↓

Check Leader

↓

Identify Root Cause

↓

Restore Replicas

↓

Verify Cluster Health
```

---

# Quick Diagnosis Table

| Problem | Possible Cause | Recommended Action |
|----------|----------------|--------------------|
| Under Replicated Partitions | Slow broker | Check broker health |
| Offline Replica | Broker failure | Restore broker |
| Shrinking ISR | Network or disk issue | Restore replica synchronization |
| Frequent Leader Elections | Broker instability | Investigate infrastructure |
| Slow Replication | Disk bottleneck | Improve storage performance |
| Replica Imbalance | Uneven partition distribution | Rebalance partitions |

---

# Best Practices

- Use a Replication Factor of at least three for critical topics.
- Monitor ISR continuously.
- Alert immediately on Under Replicated Partitions.
- Keep brokers healthy before performing maintenance.
- Use SSD or NVMe storage.
- Distribute replicas evenly across brokers.
- Monitor network latency between brokers.
- Perform regular health checks on replication metrics.
- Replace failed brokers promptly.
- Test replication recovery procedures periodically.

---

# Common Mistakes

- Ignoring Under Replicated Partitions.
- Assuming replication is a backup.
- Running with Replication Factor = 1.
- Ignoring shrinking ISR.
- Performing maintenance on unhealthy clusters.
- Using slow disks in production.
- Allowing brokers to remain offline for extended periods.
- Ignoring frequent leader elections.

---

# Summary

Replication is the foundation of Kafka's fault tolerance and high availability. Healthy replication ensures that data remains durable and accessible even during broker failures. Problems such as Under Replicated Partitions, shrinking ISR, offline replicas, and slow replication should be investigated immediately to prevent data loss and service disruption. Continuous monitoring, proactive infrastructure maintenance, and balanced cluster design are essential for maintaining reliable replication in production Kafka environments.

---

# Key Takeaways

- Replication protects Kafka against broker failures.
- Under Replicated Partitions are one of the most important production health indicators.
- Monitor ISR, replica fetch latency, and leader elections continuously.
- Disk, network, and broker health directly affect replication performance.
- A Replication Factor of three is recommended for production workloads.
- Replication improves availability but is not a substitute for backups.
- Resolve replication issues before performing maintenance or upgrades.
- Healthy replication is essential for maintaining Kafka's durability and fault tolerance.