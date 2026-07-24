# Persistence (RDB vs AOF)

## Overview

Redis is primarily an **in-memory database**, meaning that all data is stored in RAM for extremely fast read and write operations. While this design provides exceptional performance, it introduces an important challenge:

**What happens if the Redis server crashes or restarts?**

Without persistence, every key stored in Redis would be lost after a restart.

To solve this problem, Redis provides **Persistence**, which allows data to survive process restarts, machine reboots, and unexpected failures.

Redis supports two primary persistence mechanisms:

- **RDB (Redis Database Snapshot)**
- **AOF (Append Only File)**

These mechanisms have different performance characteristics, recovery times, storage requirements, and durability guarantees. Understanding when to use each one is essential for designing production-grade Redis deployments.

---

# Why Persistence Matters

Consider a typical backend application.

```
Application

↓

Redis

↓

User Sessions

Shopping Cart

Cache

Leaderboard
```

Now imagine the Redis server crashes.

```
Redis Crash

↓

Memory Cleared

↓

All Data Lost
```

Without persistence, every key disappears.

For some workloads, this is acceptable.

For others, it can be catastrophic.

---

# What is Persistence?

Persistence is the process of storing Redis data on disk so it can be restored after a restart.

```
Redis Memory

↓

Persistence Engine

↓

Disk Storage
```

When Redis starts again:

```
Disk

↓

Load Data

↓

Memory Restored
```

Applications continue operating with previously stored data.

---

# Types of Persistence

Redis provides two persistence mechanisms.

```
Redis

│

├── RDB Snapshot

│

└── AOF Log
```

They can also be combined.

---

# RDB (Redis Database Snapshot)

RDB creates a **point-in-time snapshot** of the entire Redis dataset.

Conceptually:

```
Memory

↓

Take Snapshot

↓

Save File

↓

dump.rdb
```

Instead of recording every operation, Redis periodically saves the entire dataset.

---

# How RDB Works

Imagine Redis contains:

```
Users

Products

Orders

Sessions
```

At a configured interval:

```
Take Snapshot

↓

Write Everything

↓

Disk
```

If Redis crashes later, the most recent snapshot is loaded.

---

# RDB Timeline

```
10:00

↓

Snapshot Created

↓

10:05

↓

Data Updated

↓

10:10

↓

Crash
```

Recovery restores the database to:

```
10:00 State
```

Changes between 10:00 and 10:10 are lost.

---

# Advantages of RDB

RDB offers several benefits.

- Very fast recovery
- Compact storage
- Efficient backups
- Low runtime overhead
- Suitable for disaster recovery
- Easy to copy between servers

---

# Disadvantages of RDB

Some limitations include:

- Possible data loss between snapshots
- Not ideal for financial transactions
- Snapshot generation consumes resources
- Recovery is limited to the latest snapshot

---

# Common RDB Use Cases

RDB works well for:

- Cache recovery
- Daily backups
- Analytics
- Reporting systems
- Product catalogs
- Development environments

---

# AOF (Append Only File)

AOF takes a different approach.

Instead of saving snapshots, Redis records **every write operation**.

```
Application

↓

SET User

↓

Append

↓

appendonly.aof
```

Each write command is stored in sequence.

---

# How AOF Works

Suppose the following operations occur:

```
SET user Alice

↓

SET city Kolkata

↓

INCR visits

↓

DEL session
```

AOF records:

```
Command 1

↓

Command 2

↓

Command 3

↓

Command 4
```

Recovery simply replays every command.

---

# AOF Timeline

```
10:00

↓

SET User

↓

10:01

↓

SET City

↓

10:02

↓

INCR Counter

↓

Crash
```

Redis replays:

```
SET User

↓

SET City

↓

INCR Counter
```

The database returns to its most recent state.

---

# Advantages of AOF

AOF provides:

- Better durability
- Minimal data loss
- Detailed operation history
- Better crash recovery
- Configurable synchronization frequency

---

# Disadvantages of AOF

Potential drawbacks include:

- Larger disk files
- Slower recovery
- Higher write overhead
- Requires periodic log rewriting

---

# AOF Rewrite

Over time, AOF grows continuously.

Example:

```
Counter

↓

Increment

↓

1000 Times
```

Instead of replaying 1000 increments:

```
SET Counter 1000
```

Redis periodically rewrites the log into a smaller equivalent file.

```
Old Log

↓

Rewrite

↓

Compact Log
```

This reduces disk usage and speeds recovery.

---

# RDB vs AOF

| Feature | RDB | AOF |
|----------|-----|------|
| Storage Method | Snapshot | Command Log |
| Recovery Speed | Fast | Slower |
| File Size | Smaller | Larger |
| Data Loss | Possible | Minimal |
| Backup | Excellent | Good |
| Durability | Moderate | High |
| Runtime Overhead | Lower | Higher |

---

# Recovery Process

## RDB Recovery

```
Load Snapshot

↓

Restore Memory

↓

Ready
```

Recovery is fast because Redis loads one file.

---

## AOF Recovery

```
Read Log

↓

Replay Commands

↓

Restore Memory

↓

Ready
```

Recovery may take longer for very large logs.

---

# Combining RDB and AOF

Redis supports using both persistence mechanisms simultaneously.

```
Redis

↓

RDB Snapshot

+

AOF Log
```

Benefits:

- Fast backups
- Better durability
- Flexible disaster recovery

Many production systems enable both.

---

# When to Use RDB

Choose RDB when:

- Recovery speed is important.
- Small file size matters.
- Data loss of a few minutes is acceptable.
- Redis is primarily used as a cache.
- Periodic backups are sufficient.

---

# When to Use AOF

Choose AOF when:

- Data durability is critical.
- Minimal data loss is required.
- User-generated data is stored.
- Financial transactions are involved.
- Auditability is important.

---

# Persistence in Production

Different workloads require different strategies.

## Cache Server

```
Redis

↓

Cache

↓

RDB

or

No Persistence
```

If the cache is lost, it can be rebuilt.

---

## Session Store

```
Redis

↓

Sessions

↓

AOF
```

User sessions should survive restarts.

---

## Leaderboard

```
Game Scores

↓

Redis

↓

RDB + AOF
```

Player progress should not disappear.

---

## Financial Applications

```
Transactions

↓

Redis

↓

AOF
```

Durability is significantly more important than recovery speed.

---

# Common Production Architectures

## Cache Only

```
Application

↓

Redis

↓

Database
```

Redis acts as a temporary cache.

Persistence may even be disabled.

---

## Durable Redis

```
Application

↓

Redis

↓

AOF

↓

Disk
```

Suitable for user-generated data.

---

## High Availability

```
Application

↓

Redis Primary

↓

Replica

↓

RDB

↓

AOF
```

Combining replication with persistence provides maximum reliability.

---

# Common Mistakes

## Assuming Redis Never Loses Data

Redis stores data in memory.

Without persistence:

```
Restart

↓

Everything Lost
```

---

## Using Only RDB for Critical Data

```
Snapshot

↓

Crash Before Next Snapshot

↓

Recent Updates Lost
```

---

## Ignoring AOF Rewrite

Large AOF files can:

- Slow startup
- Consume excessive storage
- Increase recovery time

---

## Treating Redis as a Relational Database

Persistence improves durability, but Redis should not automatically replace a transactional database.

Choose the appropriate storage technology based on business requirements.

---

# Best Practices

- Use RDB for backups and fast recovery.
- Use AOF when durability is important.
- Enable both RDB and AOF for production systems handling valuable data.
- Regularly verify backup integrity.
- Monitor persistence latency.
- Keep persistence files on reliable storage.
- Test disaster recovery procedures periodically.

---

# Production Considerations

Before enabling persistence, consider:

- Recovery time objectives (RTO)
- Acceptable data loss (RPO)
- Available disk space
- Write throughput
- Startup time
- Backup strategy
- Replication topology

Persistence should be selected based on business requirements rather than default configuration.

---

# Summary

Persistence enables Redis to retain data across restarts and failures by writing in-memory data to disk. Redis provides two complementary persistence mechanisms: **RDB**, which periodically captures snapshots of the dataset, and **AOF**, which records every write operation for greater durability. RDB offers faster recovery and smaller files, while AOF minimizes data loss at the cost of additional storage and write overhead. Many production environments combine both approaches to balance performance, reliability, and disaster recovery.

---

# Key Takeaways

- Redis is an in-memory database; persistence protects data from being lost after restarts.
- **RDB** stores periodic snapshots and provides fast recovery with compact files.
- **AOF** records every write operation and offers stronger durability.
- RDB may lose recent updates between snapshots, while AOF minimizes data loss.
- AOF rewrite keeps append-only logs compact and improves recovery performance.
- Production deployments often enable both RDB and AOF for balanced reliability.
- The choice between RDB and AOF should be based on recovery objectives, durability requirements, and workload characteristics.
