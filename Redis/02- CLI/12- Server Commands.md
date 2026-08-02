# Server Commands

## Overview

Redis Server commands provide information about the Redis instance itself rather than the data it stores. They are primarily used for administration, monitoring, diagnostics, maintenance, and troubleshooting.

Backend engineers, DevOps engineers, and SREs frequently use these commands to:

- Monitor server health
- Analyze memory usage
- Diagnose performance issues
- View connected clients
- Monitor replication
- Trigger persistence
- Shutdown servers safely
- Inspect runtime configuration
- Debug production incidents

Unlike data structure commands, Server commands interact with the Redis server process and should be used carefully in production environments.

---

# Server Administration Overview

```
                Administrator

                     │

                     ▼

              Redis Server

        ┌────────┬─────────┬─────────┐

        ▼        ▼         ▼

    Memory    Clients   Replication

        ▼        ▼         ▼

      Monitor  Diagnose  Maintain
```

---

# Common Server Commands

| Command | Description |
|----------|-------------|
| PING | Check server availability |
| INFO | Server statistics |
| CLIENT LIST | Connected clients |
| CLIENT KILL | Disconnect client |
| DBSIZE | Number of keys |
| MEMORY STATS | Memory statistics |
| MEMORY USAGE | Memory used by key |
| SLOWLOG | Slow command log |
| LATENCY | Latency monitoring |
| MONITOR | Live command stream |
| SAVE | Synchronous snapshot |
| BGSAVE | Background snapshot |
| LASTSAVE | Last successful save |
| FLUSHDB | Delete current database |
| FLUSHALL | Delete all databases |
| SHUTDOWN | Stop Redis server |
| TIME | Server time |

---

# PING

Tests whether Redis is reachable.

Syntax

```redis
PING
```

Output

```
PONG
```

Useful for:

- Health checks
- Load balancers
- Kubernetes probes
- Monitoring systems

---

# INFO

Displays detailed server statistics.

Syntax

```redis
INFO
```

Example Output

```
Server

Clients

Memory

Persistence

Replication

CPU

Stats

Keyspace
```

Example

```redis
INFO MEMORY
```

Shows only memory-related information.

Useful sections include:

- Server
- Clients
- Memory
- Persistence
- Replication
- CPU
- Stats
- Cluster
- Keyspace

---

# INFO Memory

```
INFO MEMORY
```

Example Output

```
used_memory

used_memory_peak

used_memory_dataset

maxmemory
```

Useful for:

- Capacity planning
- Memory optimization
- Cache tuning

---

# INFO Replication

```
INFO REPLICATION
```

Example

```
Role

Master

Connected Slaves

Replication Offset
```

Useful for replication troubleshooting.

---

# CLIENT LIST

Shows all connected clients.

Example

```redis
CLIENT LIST
```

Output

```
id=15

addr=10.0.0.15

age=600

idle=5

db=0
```

Useful during production debugging.

---

# CLIENT KILL

Terminates client connections.

Example

```redis
CLIENT KILL 10.0.0.15:50000
```

Useful for:

- Stuck clients
- Idle connections
- Testing

Use cautiously.

---

# DBSIZE

Returns the number of keys in the current database.

Example

```redis
DBSIZE
```

Output

```
(integer) 125000
```

Useful for:

- Capacity monitoring
- Migration validation
- Database statistics

---

# MEMORY STATS

Displays Redis memory statistics.

Example

```redis
MEMORY STATS
```

Provides:

- Fragmentation
- Peak memory
- Allocator statistics
- Overhead

---

# MEMORY USAGE

Returns memory consumed by a key.

Example

```redis
MEMORY USAGE user:1001
```

Output

```
(integer) 256
```

Useful for identifying expensive keys.

---

# SLOWLOG

Displays slow commands.

Example

```redis
SLOWLOG GET 10
```

Output

```
Command

Execution Time

Timestamp
```

Useful for:

- Performance tuning
- Detecting expensive operations
- Production debugging

---

# LATENCY

Monitors server latency.

Example

```redis
LATENCY LATEST
```

Shows latency spikes.

Useful for:

- Performance monitoring
- Capacity planning

---

# MONITOR

Streams every command executed.

Example

```redis
MONITOR
```

Output

```
SET user:1

GET user:1

DEL user:1

INCR counter
```

Every command executed by every client appears.

---

# Warning About MONITOR

```
Application

↓

Thousands of Commands

↓

MONITOR

↓

Large Performance Impact
```

Never leave MONITOR running on busy production systems.

---

# SAVE

Creates an RDB snapshot synchronously.

Example

```redis
SAVE
```

The server blocks until persistence completes.

Generally avoided in production.

---

# BGSAVE

Creates an RDB snapshot in the background.

Example

```redis
BGSAVE
```

Preferred over SAVE.

```
Redis

↓

Fork Process

↓

Background Save

↓

Continue Serving Clients
```

---

# LASTSAVE

Returns the Unix timestamp of the last successful snapshot.

Example

```redis
LASTSAVE
```

Useful for backup verification.

---

# FLUSHDB

Deletes every key in the current database.

Example

```redis
FLUSHDB
```

Architecture

```
Database

↓

All Keys Deleted
```

Use carefully.

---

# FLUSHALL

Deletes every key in every Redis database.

Example

```redis
FLUSHALL
```

```
Redis

↓

Database 0

Database 1

Database 2

↓

Everything Deleted
```

Extremely dangerous.

---

# SHUTDOWN

Gracefully stops Redis.

Example

```redis
SHUTDOWN
```

Redis performs:

- Persistence (if configured)
- Client disconnection
- Clean shutdown

---

# TIME

Returns the current Redis server time.

Example

```redis
TIME
```

Output

```
Unix Timestamp

Microseconds
```

Useful for:

- Distributed timing
- Diagnostics
- Synchronization

---

# Monitoring Architecture

```
                Monitoring

                     │

                     ▼

                INFO MEMORY

                INFO CPU

              INFO REPLICATION

                     │

                     ▼

               Alert Dashboard
```

---

# Production Health Check

```
Application

↓

PING

↓

INFO

↓

Healthy?

↓

Continue
```

---

# Slow Query Investigation

```
Application Slow

↓

SLOWLOG

↓

Identify Command

↓

Optimize
```

---

# Memory Investigation

```
High Memory Usage

↓

INFO MEMORY

↓

MEMORY STATS

↓

MEMORY USAGE

↓

Identify Large Keys
```

---

# Client Investigation

```
Too Many Connections

↓

CLIENT LIST

↓

Identify Idle Clients

↓

CLIENT KILL
```

---

# Backup Workflow

```
Administrator

↓

BGSAVE

↓

Snapshot

↓

Verify LASTSAVE
```

---

# Common Production Use Cases

Server commands are commonly used for:

- Health monitoring
- Capacity planning
- Backup verification
- Performance tuning
- Memory analysis
- Replication monitoring
- Troubleshooting
- Incident response
- Operations dashboards
- Production diagnostics

---

# Common Mistakes

## Running MONITOR in Production

MONITOR captures every command.

On busy servers:

```
Millions of Commands

↓

MONITOR

↓

Performance Degradation
```

Use only during troubleshooting.

---

## Using SAVE Instead of BGSAVE

SAVE blocks Redis.

Prefer:

```
BGSAVE
```

---

## Executing FLUSHALL Accidentally

Never execute

```redis
FLUSHALL
```

without understanding the consequences.

Production data will be deleted.

---

## Ignoring SLOWLOG

Slow commands indicate:

- Poor key design
- Inefficient queries
- Large datasets
- Missing optimization

Review SLOWLOG regularly.

---

# Best Practices

- Use `PING` for health checks.
- Monitor `INFO` metrics continuously.
- Prefer `BGSAVE` over `SAVE`.
- Use `MEMORY USAGE` to identify oversized keys.
- Review `SLOWLOG` during performance tuning.
- Avoid `MONITOR` except during short debugging sessions.
- Restrict administrative commands using Redis ACLs.
- Disable dangerous commands such as `FLUSHALL` in production if possible.

---

# Performance Considerations

| Command | Complexity |
|----------|------------|
| PING | O(1) |
| INFO | O(1) |
| DBSIZE | O(1) |
| MEMORY USAGE | O(1) |
| MEMORY STATS | O(1) |
| CLIENT LIST | O(N) |
| CLIENT KILL | O(1) |
| SLOWLOG | O(N) |
| MONITOR | Continuous |
| SAVE | Blocking |
| BGSAVE | Background |
| LASTSAVE | O(1) |
| FLUSHDB | O(N) |
| FLUSHALL | O(N) |
| TIME | O(1) |

*N = number of keys or clients, depending on the command.*

---

# Production Considerations

For production deployments:

- Integrate `INFO` metrics with monitoring systems such as Prometheus and Grafana.
- Regularly inspect `SLOWLOG` to identify inefficient operations.
- Schedule `BGSAVE` during periods of lower activity if manual snapshots are required.
- Restrict or rename dangerous commands (`FLUSHALL`, `FLUSHDB`, `SHUTDOWN`) using Redis configuration or ACLs.
- Monitor memory fragmentation and client connection counts.
- Avoid long-running `MONITOR` sessions on high-traffic servers.
- Implement alerts for replication failures, high memory usage, and latency spikes.

---

# Server Commands vs Configuration Commands

| Server Commands | Configuration Commands |
|-----------------|------------------------|
| Monitor server health | Change Redis settings |
| Analyze memory | Modify runtime configuration |
| Diagnose performance | Tune server behavior |
| Inspect clients | Update limits and policies |
| Manage persistence | Persist configuration changes |

---

# Summary

Redis Server commands provide the operational visibility required to run Redis reliably in production. They allow administrators to monitor health, inspect memory, analyze client activity, troubleshoot slow operations, and manage persistence. Commands such as `INFO`, `PING`, `SLOWLOG`, `BGSAVE`, and `MEMORY STATS` are indispensable for maintaining high availability and diagnosing production issues. Care should be taken when using destructive commands like `FLUSHALL` or resource-intensive commands like `MONITOR`.

---

# Key Takeaways

- `PING` verifies server availability.
- `INFO` is the primary command for monitoring Redis health and performance.
- `CLIENT LIST` and `CLIENT KILL` help manage client connections.
- `SLOWLOG` identifies expensive operations that impact performance.
- `MEMORY STATS` and `MEMORY USAGE` assist in memory optimization.
- Prefer `BGSAVE` over `SAVE` for creating snapshots.
- Use `MONITOR` only for short-term debugging.
- Protect dangerous administrative commands using ACLs and operational controls.