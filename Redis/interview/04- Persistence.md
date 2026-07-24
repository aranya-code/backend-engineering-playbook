# Persistence Interview Questions

## Overview

Redis is primarily an **in-memory database**, but production systems often require data to survive crashes, restarts, deployments, or server failures.

This is where **Redis Persistence** becomes important.

Senior backend interviews frequently ask questions such as:

- Does Redis lose data?
- How does Redis persist data?
- What is RDB?
- What is AOF?
- Which persistence mechanism should be used?
- What are the trade-offs?
- How does Redis recover after a crash?

This chapter covers Redis persistence from beginner to senior backend interview level.

---

# Q1. What is Redis Persistence?

### Answer

Persistence is the mechanism that allows Redis to save in-memory data onto disk so that it can recover the data after a restart or crash.

Without persistence:

```
Application

↓

Redis

↓

Server Crash

↓

All Data Lost
```

With persistence:

```
Application

↓

Redis

↓

Disk

↓

Restart

↓

Data Restored
```

---

# Q2. Why does Redis need persistence?

### Answer

Redis stores data primarily in RAM.

RAM is volatile memory.

If the server crashes or power is lost, everything stored only in memory disappears.

Persistence protects against:

- Server crashes
- Power failures
- Process termination
- Machine reboot
- Deployment restart

---

# Q3. What persistence options does Redis provide?

### Answer

Redis supports two persistence mechanisms.

| Persistence | Description |
|-------------|-------------|
| RDB | Point-in-time snapshots |
| AOF | Append every write operation |

Both can also be enabled together.

---

# Q4. What is RDB?

### Answer

RDB (Redis Database) periodically creates a snapshot of the dataset and saves it to disk.

Example

```
10:00

↓

Snapshot

↓

dump.rdb
```

If Redis crashes at 10:04,

the server restores the 10:00 snapshot.

---

# Q5. How does RDB work?

### Answer

Redis forks a child process.

The child writes the dataset to disk while the parent continues serving requests.

```
Redis

│

├── Parent

│      │

│      └── Handles Clients

│

└── Child

       │

       └── Writes dump.rdb
```

---

# Q6. What are the advantages of RDB?

### Answer

Advantages

- Fast restart
- Compact file
- Good for backups
- Low runtime overhead
- Easy disaster recovery

---

# Q7. What are the disadvantages of RDB?

### Answer

If Redis crashes before the next snapshot,

recent writes are lost.

Example

```
Snapshot

↓

10:00

Crash

↓

10:09

Data Lost

↓

9 Minutes
```

---

# Q8. What is AOF?

### Answer

AOF stands for

```
Append Only File
```

Instead of saving snapshots,

Redis logs every write command.

Example

```
SET user John

SET age 30

DEL token
```

These commands are replayed during restart.

---

# Q9. How does AOF recovery work?

### Answer

When Redis starts,

it reads every command from the AOF file and rebuilds the dataset.

```
AOF File

↓

Replay Commands

↓

Memory Restored
```

---

# Q10. What are the advantages of AOF?

### Answer

- Better durability
- Smaller data loss window
- Human-readable commands
- Flexible fsync configuration

---

# Q11. What are the disadvantages of AOF?

### Answer

- Larger files
- Slower restart
- More disk writes
- Higher storage usage

---

# Q12. What is fsync?

### Answer

`fsync` determines when Redis flushes AOF data from the operating system buffer to disk.

Options

| Option | Description |
|---------|-------------|
| always | Every command |
| everysec | Every second |
| no | Operating system decides |

---

# Q13. Which fsync policy is most commonly used?

### Answer

```
appendfsync everysec
```

Reason

- Good durability
- High performance
- Maximum one second of data loss

---

# Q14. What is AOF Rewrite?

### Answer

Over time,

the AOF file becomes large.

Instead of storing

```
SET count 1

SET count 2

SET count 3

SET count 4
```

Redis rewrites it as

```
SET count 4
```

The rewritten file is much smaller.

---

# Q15. Why is AOF Rewrite important?

### Answer

Benefits

- Smaller files
- Faster restart
- Reduced storage usage
- Improved performance

---

# Q16. Does AOF block Redis?

### Answer

No.

Redis performs AOF Rewrite in a background child process.

The parent process continues serving client requests.

---

# Q17. What is Copy-on-Write?

### Answer

Redis uses Copy-on-Write during background persistence.

```
Fork

↓

Child Reads Memory

↓

Parent Continues Writing

↓

Modified Pages Copied
```

Only changed memory pages are duplicated.

---

# Q18. Why is Copy-on-Write efficient?

### Answer

Without Copy-on-Write,

the entire dataset would need to be copied.

Instead,

only modified memory pages are duplicated,

saving memory and CPU.

---

# Q19. Can RDB and AOF be enabled together?

### Answer

Yes.

This is common in production.

Benefits

- Fast backup (RDB)
- Better durability (AOF)

---

# Q20. Which file does Redis use during recovery if both exist?

### Answer

Redis prefers

```
AOF
```

because it usually contains more recent data.

---

# Q21. Which persistence method is faster?

### Answer

| Operation | Winner |
|-----------|--------|
| Restart | RDB |
| Backup | RDB |
| Durability | AOF |
| Recovery Accuracy | AOF |

---

# Q22. Which persistence method is recommended?

### Answer

Production recommendation

```
RDB

+

AOF
```

This provides both fast recovery and strong durability.

---

# Q23. Does Redis guarantee zero data loss?

### Answer

No.

The amount of potential data loss depends on

- Snapshot interval
- fsync policy
- Disk failures

---

# Q24. What happens if Redis crashes before the next snapshot?

### Answer

All writes after the last snapshot are lost.

Example

```
Snapshot

↓

10:00

Crash

↓

10:15

Lost

↓

15 Minutes
```

---

# Q25. Can Redis be used without persistence?

### Answer

Yes.

Many caching-only deployments disable persistence completely.

Example

- API Cache
- CDN Cache
- Temporary Sessions

---

# Q26. When should persistence be disabled?

### Answer

Persistence can be disabled when

- Redis is only a cache
- Data can be regenerated
- Performance is the highest priority

---

# Q27. How do you back up Redis?

### Answer

Common methods

- Copy RDB file
- Copy AOF file
- Cloud storage
- Scheduled backups
- Replica backups

---

# Q28. What is the production backup strategy?

### Answer

Typical production setup

```
Redis

↓

RDB Snapshot

↓

Cloud Storage

↓

Retention Policy

↓

Disaster Recovery
```

---

# Q29. How would you recover from complete server failure?

### Answer

Steps

1. Provision a new server.
2. Install Redis.
3. Restore the latest RDB or AOF.
4. Start Redis.
5. Verify data integrity.
6. Redirect application traffic.

---

# Q30. What are common persistence interview mistakes?

### Answer

Candidates often

- Think Redis automatically persists data.
- Confuse RDB with AOF.
- Ignore data loss windows.
- Forget Copy-on-Write.
- Recommend only one persistence method without justification.

---

# Rapid Fire Questions

| Question | Answer |
|----------|--------|
| Snapshot persistence? | RDB |
| Command log persistence? | AOF |
| Better durability? | AOF |
| Faster restart? | RDB |
| Most common fsync? | everysec |
| Rewrite large AOF? | AOF Rewrite |
| Memory optimization during persistence? | Copy-on-Write |
| Use both in production? | Yes |

---

# Senior Interview Tips

Interviewers often ask:

> If your Redis server crashes immediately after a customer places an order, how much data could be lost?

A strong answer should discuss

- RDB snapshot interval
- AOF fsync policy
- Replication
- Backup strategy
- Business tolerance for data loss

This demonstrates an understanding of durability trade-offs rather than simply naming persistence mechanisms.

---

# Common Mistakes

## Assuming Redis Always Persists Data

Persistence is configurable and can be disabled.

---

## Choosing Only RDB

RDB is efficient but may lose recent writes.

---

## Choosing Only AOF

AOF offers better durability but increases disk usage and restart time.

---

## Ignoring Backup Strategy

Persistence is not a replacement for backups.

Regular backups are still essential.

---

# Best Practices

- Enable both RDB and AOF for production systems that require durability.
- Use `appendfsync everysec` for a good balance of performance and reliability.
- Schedule regular off-site backups of persistence files.
- Monitor AOF rewrite frequency and disk usage.
- Test recovery procedures regularly to ensure backups are usable.

---

# Summary

Redis persistence enables an in-memory database to survive restarts and failures by writing data to disk. RDB provides efficient point-in-time snapshots, while AOF offers greater durability by recording every write operation. Understanding the trade-offs between performance, durability, storage, and recovery time is essential for designing reliable production systems and succeeding in senior backend interviews.

---

# Key Takeaways

- Redis supports two persistence mechanisms: RDB and AOF.
- RDB creates periodic snapshots and offers fast recovery.
- AOF logs write operations and provides stronger durability.
- Copy-on-Write enables efficient background persistence.
- AOF Rewrite reduces file size without losing the final state.
- Most production deployments enable both RDB and AOF.
- Strong interview answers explain not only how persistence works, but also when and why to choose each strategy.