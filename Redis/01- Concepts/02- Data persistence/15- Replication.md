# Replication

## Overview

Redis Replication is a mechanism that allows one Redis server (called the **Primary**) to automatically copy its data to one or more **Replicas** (formerly known as Slaves). Replication is fundamental to building highly available, fault-tolerant, and scalable Redis deployments.

Instead of directing every read and write request to a single Redis instance, applications can distribute read traffic across multiple replicas while keeping all writes on the primary server. This improves application performance, reduces load on the primary, and provides redundancy in case of server failures.

Replication is the foundation upon which **Redis Sentinel** and **Redis Cluster** are built.

---

# Why Replication?

Consider a backend application using a single Redis server.

```
                 +----------------+
                 |  Application   |
                 +--------+-------+
                          |
                          |
                    +-----v------+
                    |   Redis    |
                    +------------+
```

Everything works well until one of the following occurs:

- Redis crashes
- Hardware failure
- Maintenance restart
- High read traffic
- Network outage

Now the application loses access to Redis.

Replication solves this problem.

---

# What is Replication?

Replication creates one or more copies of the primary Redis database.

```
                 +----------------+
                 |    Primary     |
                 +-------+--------+
                         |
          +--------------+--------------+
          |                             |
+---------v---------+         +---------v---------+
|     Replica 1     |         |     Replica 2     |
+-------------------+         +-------------------+
```

Every write sent to the primary is automatically propagated to the replicas.

---

# Primary and Replica

Redis replication follows a **Primary-Replica** architecture.

## Primary

Responsible for:

- Accepting write operations
- Processing updates
- Replicating changes

```
Application

↓

Primary

↓

Write Data
```

---

## Replica

Responsible for:

- Receiving replicated data
- Serving read requests
- Providing backup

```
Replica

↓

Read Requests
```

Replicas do not normally accept writes.

---

# Replication Flow

Whenever data changes:

```
Application

↓

Primary

↓

Replication

↓

Replica A

↓

Replica B

↓

Replica C
```

All replicas eventually receive the same updates.

---

# How Replication Works

Suppose the application writes:

```
SET user:101 Alice
```

The flow becomes:

```
Application

↓

Primary

↓

Store in Memory

↓

Send Update

↓

Replica 1

↓

Replica 2
```

Every replica stores the same value.

---

# Initial Synchronization

When a new replica joins:

```
Replica Starts

↓

Connect to Primary

↓

Request Full Sync

↓

Receive Complete Dataset

↓

Become Synchronized
```

This process is called **Full Synchronization**.

---

# Full Synchronization

During the first synchronization:

```
Primary Memory

↓

Generate Snapshot (RDB)

↓

Transfer Snapshot

↓

Replica Loads Snapshot

↓

Ready
```

Once complete, normal replication begins.

---

# Partial Synchronization

Suppose a replica temporarily disconnects.

```
Primary

↓

Writes Continue

↓

Replica Offline
```

When the replica reconnects:

```
Reconnect

↓

Receive Missing Updates

↓

Continue Replication
```

Redis attempts **Partial Synchronization**, avoiding a complete data transfer.

This greatly improves recovery speed.

---

# Replication Backlog

Redis maintains a small in-memory backlog.

```
Primary

↓

Replication Backlog

↓

Recent Commands
```

If a replica reconnects quickly:

```
Read Missing Commands

↓

Catch Up
```

No full synchronization is required.

---

# Asynchronous Replication

Redis replication is **asynchronous**.

```
Application

↓

Primary

↓

Reply Success

↓

Replicas Updated Later
```

The primary does not wait for replicas before responding.

This provides excellent performance.

---

# Eventual Consistency

Because replication is asynchronous:

```
Primary

↓

Updated Immediately
```

Replica:

```
Updated

↓

Milliseconds Later
```

For a brief period, replicas may contain slightly older data.

This model is known as **Eventual Consistency**.

---

# Read Scaling

One of the biggest advantages of replication is distributing read traffic.

Without replication:

```
1000 Reads

↓

Primary
```

With replication:

```
Primary

↓

Replica A

↓

Replica B

↓

Replica C
```

Applications distribute reads across replicas.

Benefits include:

- Lower latency
- Better scalability
- Reduced primary load

---

# High Availability

Replication improves availability.

```
Primary Failure

↓

Replica Exists

↓

Promote Replica

↓

Continue Service
```

This promotion is usually handled by **Redis Sentinel**.

---

# Backup Strategy

Replicas can also be used for backups.

```
Primary

↓

Replica

↓

Generate Backup
```

This prevents backup operations from affecting production traffic.

---

# Disaster Recovery

Replication enables disaster recovery.

```
Primary

↓

Data Center A

↓

Replica

↓

Data Center B
```

If one data center becomes unavailable, data still exists elsewhere.

---

# Replication Lag

Replication is not instantaneous.

```
Primary

↓

100 Updates

↓

Replica

↓

98 Updates
```

The difference is called **Replication Lag**.

Small lag is normal.

Large lag indicates problems such as:

- Network latency
- Heavy load
- Slow disks
- Insufficient CPU

Monitoring replication lag is important.

---

# Common Production Architectures

## Single Replica

```
            Primary
               |
           Replica
```

Simple redundancy.

---

## Multiple Replicas

```
              Primary
        /         |         \
 Replica A   Replica B   Replica C
```

Improved read scalability.

---

## Cross-Region Replication

```
Region A

↓

Primary

↓

Internet

↓

Replica

↓

Region B
```

Useful for disaster recovery.

---

# Replication vs Backup

| Feature | Replication | Backup |
|----------|-------------|---------|
| Real-Time | Yes | No |
| Automatic | Yes | Usually Scheduled |
| Disaster Recovery | Yes | Yes |
| Historical Recovery | No | Yes |
| Protects Against Accidental Deletes | No | Yes |

Replication is **not** a replacement for backups.

If a key is accidentally deleted:

```
Primary

↓

Delete Key

↓

Replica

↓

Delete Key
```

The deletion is replicated immediately.

---

# Replication vs Redis Cluster

| Feature | Replication | Cluster |
|----------|-------------|----------|
| Purpose | High Availability | Horizontal Scaling |
| Data | Complete Copy | Partitioned |
| Read Scaling | Yes | Yes |
| Write Scaling | No | Yes |
| Automatic Sharding | No | Yes |

Replication duplicates data.

Clusters distribute data.

---

# Common Production Use Cases

Redis Replication is widely used for:

- High availability
- Read scaling
- Disaster recovery
- Backup generation
- Analytics replicas
- Reporting systems
- Cross-region deployments
- Session storage
- Cache redundancy
- Production failover

---

# Common Mistakes

## Assuming Replication is a Backup

Replication copies everything.

Including:

- Accidental deletes
- Corrupted data
- Incorrect updates

Always maintain backups separately.

---

## Sending Writes to Replicas

```
Application

↓

Replica

↓

Write Request

↓

Rejected
```

Writes should always go to the primary unless explicitly configured otherwise.

---

## Ignoring Replication Lag

Applications requiring strong consistency should not immediately read from replicas after writing.

---

## Too Many Replicas

Each additional replica increases network traffic.

Plan replication topology carefully.

---

# Best Practices

- Use replication for read-heavy workloads.
- Monitor replication lag continuously.
- Combine replication with Redis Sentinel for automatic failover.
- Use replicas for reporting and analytics.
- Keep replicas in different availability zones when possible.
- Maintain independent backups in addition to replication.
- Test failover procedures regularly.

---

# Production Considerations

Before implementing replication, consider:

- Expected read-to-write ratio
- Network latency
- Number of replicas
- Disaster recovery requirements
- Cross-region deployment needs
- Failover strategy
- Backup policies

Replication should be part of a broader high-availability architecture rather than the only resilience mechanism.

---

# Summary

Redis Replication enables one primary Redis server to automatically synchronize its data with one or more replicas. It improves scalability by distributing read traffic, increases availability through redundancy, and serves as the foundation for high-availability solutions such as Redis Sentinel. Because replication is asynchronous, replicas are eventually consistent with the primary, making it important to understand replication lag and design applications accordingly. While replication enhances reliability, it should always be complemented with proper backup strategies for complete data protection.

---

# Key Takeaways

- Redis Replication copies data from a primary server to one or more replicas.
- Replicas are primarily used for read scaling and high availability.
- Initial synchronization transfers the entire dataset, while partial synchronization sends only missed updates.
- Replication is asynchronous, resulting in eventual consistency.
- Replication improves resilience but does not replace backups.
- Redis Sentinel relies on replication to perform automatic failover.
- Monitoring replication lag is essential for maintaining production performance and reliability.