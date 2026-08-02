# Replication & High Availability Interview Questions

## Overview

As applications grow, a single Redis server becomes a bottleneck and a single point of failure.

Redis provides several mechanisms to improve:

- Availability
- Fault tolerance
- Scalability
- Disaster recovery

Senior backend interviews commonly focus on:

- Replication
- High Availability (HA)
- Redis Sentinel
- Automatic Failover
- Read Scaling
- Split Brain
- Replication Lag
- Production Architecture

This chapter covers the most commonly asked interview questions on Redis Replication and High Availability.

---

# Q1. What is Redis Replication?

### Answer

Redis Replication is the process of copying data from one Redis server (Primary) to one or more Redis servers (Replicas).

Architecture

```
            Clients

               │

               ▼

        Primary Redis

        /     |      \

       ▼      ▼       ▼

 Replica1 Replica2 Replica3
```

The primary handles writes, while replicas receive copies of the data.

---

# Q2. Why is Replication needed?

### Answer

Replication provides several benefits.

- High Availability
- Read Scaling
- Backup
- Disaster Recovery
- Fault Tolerance

Without replication

```
Primary Crash

↓

Application Down
```

With replication

```
Primary Crash

↓

Replica Promoted

↓

Application Continues
```

---

# Q3. What is the difference between Primary and Replica?

### Answer

| Primary | Replica |
|----------|----------|
| Accepts reads | Accepts reads |
| Accepts writes | Read-only by default |
| Source of truth | Copy of Primary |
| Replicates data | Receives replication |

---

# Q4. How does Redis Replication work?

### Answer

Replication is asynchronous.

Workflow

```
Client

↓

Primary

↓

Write

↓

Replication Stream

↓

Replica
```

The primary acknowledges the write before replicas receive it.

---

# Q5. Is Redis Replication synchronous?

### Answer

No.

Redis replication is asynchronous.

Advantages

- Fast writes
- Low latency

Disadvantages

- Small chance of data loss during failover

---

# Q6. What happens when a new Replica joins?

### Answer

Redis performs a Full Synchronization.

Steps

1. Replica connects.
2. Primary creates an RDB snapshot.
3. Snapshot is transferred.
4. Buffered writes are replayed.
5. Replica becomes synchronized.

Architecture

```
Primary

↓

Create RDB

↓

Transfer Snapshot

↓

Replay Changes

↓

Replica Ready
```

---

# Q7. What is Partial Synchronization?

### Answer

If a replica disconnects briefly, Redis does not always need a full synchronization.

Instead

```
Replica Reconnects

↓

Requests Missing Commands

↓

Primary Sends Incremental Updates
```

This saves bandwidth and recovery time.

---

# Q8. What is Replication Backlog?

### Answer

Redis maintains an in-memory backlog buffer containing recent write operations.

Replicas use this backlog to catch up after temporary network failures.

---

# Q9. What is Replication Lag?

### Answer

Replication lag is the delay between:

```
Primary Write

↓

Replica Receives Update
```

Causes

- Network latency
- Heavy workload
- Slow disks
- CPU bottlenecks

---

# Q10. Why is Replication Lag important?

### Answer

Applications reading from replicas may receive stale data.

Example

```
Primary

Balance = 500

↓

Replica

Balance = 450
```

The replica has not yet received the latest update.

---

# Q11. What is Read Scaling?

### Answer

Instead of serving all reads from one server,

applications distribute reads across replicas.

```
Writes

↓

Primary

Reads

↓

Replica 1

Replica 2

Replica 3
```

Benefits

- Higher throughput
- Lower latency
- Better scalability

---

# Q12. Should writes go to Replicas?

### Answer

No.

Replicas are read-only by default.

All writes should go to the primary.

---

# Q13. What happens if the Primary crashes?

### Answer

Without High Availability

```
Primary Down

↓

Application Failure
```

With Sentinel

```
Primary Down

↓

Replica Promoted

↓

Application Continues
```

---

# Q14. What is Redis Sentinel?

### Answer

Redis Sentinel is Redis's High Availability solution.

Responsibilities

- Monitor Redis servers
- Detect failures
- Elect new Primary
- Perform automatic failover
- Notify applications

---

# Q15. How many Sentinel nodes are recommended?

### Answer

At least

```
3
```

Preferably

```
3

5

or

7
```

Using an odd number avoids election ties.

---

# Q16. What is Automatic Failover?

### Answer

Automatic failover promotes a replica to become the new primary.

Workflow

```
Primary Fails

↓

Sentinel Detects Failure

↓

Leader Election

↓

Replica Promoted

↓

Clients Redirected
```

---

# Q17. How does Sentinel detect failures?

### Answer

Sentinel periodically sends

```
PING
```

commands.

If multiple Sentinel nodes agree that the primary is unavailable,

failover begins.

---

# Q18. What is Quorum?

### Answer

Quorum is the minimum number of Sentinel nodes that must agree before declaring the primary unavailable.

Example

```
5 Sentinels

↓

Need 3 Votes

↓

Failover
```

---

# Q19. What is Split Brain?

### Answer

Split Brain occurs when two servers believe they are both the primary.

Example

```
Network Partition

↓

Primary A

Primary B

↓

Data Divergence
```

Split Brain can cause inconsistent data.

---

# Q20. How does Sentinel reduce Split Brain?

### Answer

Sentinel uses:

- Majority voting
- Leader election
- Quorum
- Automatic reconfiguration

These reduce—but do not completely eliminate—the risk.

---

# Q21. What is a Replica Promotion?

### Answer

When the primary fails,

one replica becomes the new primary.

Selection factors include

- Replication offset
- Network health
- Priority
- Availability

---

# Q22. Can Replicas have their own Replicas?

### Answer

Yes.

Redis supports cascading replication.

```
Primary

↓

Replica A

↓

Replica B
```

Useful in large deployments.

---

# Q23. Can replication improve write performance?

### Answer

No.

Writes still go to the primary.

Replication mainly improves:

- Availability
- Read scalability

---

# Q24. What is the difference between Replication and Backup?

### Answer

| Replication | Backup |
|-------------|---------|
| Live copy | Point-in-time copy |
| High Availability | Disaster Recovery |
| Near real-time | Historical recovery |
| Same data | Older snapshot |

Replication is **not** a replacement for backups.

---

# Q25. Can a deleted key be recovered from a Replica?

### Answer

No.

Deletion is replicated.

Example

```
DEL user:100

↓

Primary

↓

Replica

↓

Deleted Everywhere
```

---

# Q26. What happens if the network disconnects a Replica?

### Answer

The replica continues serving reads.

When connectivity returns,

it synchronizes using:

- Partial synchronization
- Full synchronization (if necessary)

---

# Q27. What monitoring metrics are important?

### Answer

Monitor

- Replication lag
- Connected replicas
- Network latency
- Failover count
- Memory usage
- Disk usage
- Synchronization status

---

# Q28. What is a typical production Redis HA architecture?

### Answer

```
                 Clients

                    │

                    ▼

              Redis Sentinel

          ┌────────┼────────┐

          ▼        ▼        ▼

      Sentinel  Sentinel  Sentinel

                    │

                    ▼

             Primary Redis

             /          \

            ▼            ▼

       Replica       Replica
```

---

# Q29. What are common interview mistakes?

### Answer

Candidates often

- Think replication is synchronous.
- Assume replicas accept writes.
- Confuse Sentinel with Cluster.
- Believe replication replaces backups.
- Ignore replication lag.

---

# Q30. When should Replication be used?

### Answer

Replication should be used when applications require

- High Availability
- Read scaling
- Disaster recovery
- Reduced downtime
- Fault tolerance

Nearly every production Redis deployment uses replication.

---

# Rapid Fire Questions

| Question | Answer |
|----------|--------|
| Accept writes? | Primary |
| Accept reads? | Primary & Replica |
| Replication type? | Asynchronous |
| Automatic failover? | Sentinel |
| Detect failures? | Sentinel |
| Read scaling? | Replicas |
| Full sync uses? | RDB Snapshot |
| Incremental sync? | Partial Synchronization |

---

# Senior Interview Tips

Interviewers often ask:

> A user updates their profile, but immediately reading from a replica returns the old value. Why?

A strong answer should mention

- Asynchronous replication
- Replication lag
- Eventual consistency
- Read-after-write consistency
- Reading from the primary for critical operations

These concepts are expected at the senior backend level.

---

# Common Mistakes

## Assuming Replication Is Synchronous

Redis replication is asynchronous by default.

---

## Treating Replicas as Backup Servers

Replication copies mistakes as well.

Backups are still required.

---

## Confusing Sentinel with Cluster

Sentinel provides High Availability.

Redis Cluster provides Horizontal Scaling.

---

## Ignoring Replication Lag

Applications with strict consistency requirements must account for stale reads.

---

# Best Practices

- Deploy at least three Sentinel nodes.
- Use replicas for read-heavy workloads.
- Monitor replication lag continuously.
- Maintain regular backups in addition to replication.
- Test failover procedures before production.
- Read from the primary when strong consistency is required.

---

# Summary

Redis Replication improves availability and scalability by maintaining one or more replicas of a primary server. Combined with Redis Sentinel, it enables automatic failover and minimizes downtime. Senior backend engineers should understand replication workflows, failover mechanisms, replication lag, and the trade-offs between consistency and performance when designing production systems.

---

# Key Takeaways

- Redis replication is asynchronous.
- The primary handles writes, while replicas primarily serve reads.
- Replication improves availability and read scalability.
- Redis Sentinel provides monitoring, leader election, and automatic failover.
- Replication lag can result in stale reads.
- Replication is not a substitute for backups.
- Production deployments should combine replication, Sentinel, persistence, and backups for a resilient Redis architecture.