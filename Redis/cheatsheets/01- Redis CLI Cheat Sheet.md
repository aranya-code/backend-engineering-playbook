# Redis CLI Cheat Sheet

## Overview

The Redis Command Line Interface (`redis-cli`) is the primary tool for interacting with a Redis server. Whether you're debugging production issues, testing new commands, monitoring performance, or administering a Redis Cluster, `redis-cli` is an essential skill for every backend engineer.

This cheat sheet provides a quick reference to the most commonly used Redis CLI commands, organized by category. It is intended as a day-to-day reference rather than a detailed tutorial.

---

# Connect to Redis

## Local Connection

```bash
redis-cli
```

---

## Connect to a Remote Server

```bash
redis-cli -h <host> -p <port>
```

Example

```bash
redis-cli -h 10.0.0.15 -p 6379
```

---

## Connect with Authentication

```bash
redis-cli -h <host> -p <port> -a <password>
```

Example

```bash
redis-cli -h redis.example.com -p 6379 -a MySecretPassword
```

---

## Connect Using TLS

```bash
redis-cli \
  --tls \
  -h redis.example.com \
  -p 6380
```

---

## Connect to a Redis Cluster

```bash
redis-cli -c
```

Cluster mode automatically follows `MOVED` and `ASK` redirections.

---

# Server Information

## General Information

```bash
INFO
```

---

## Memory Information

```bash
INFO MEMORY
```

---

## CPU Statistics

```bash
INFO CPU
```

---

## Persistence Status

```bash
INFO PERSISTENCE
```

---

## Replication Status

```bash
INFO REPLICATION
```

---

## Server Statistics

```bash
INFO STATS
```

---

## Clients

```bash
INFO CLIENTS
```

---

## Configuration

```bash
CONFIG GET *
```

Retrieve a specific configuration

```bash
CONFIG GET maxmemory
```

---

## Modify Configuration

```bash
CONFIG SET maxmemory 4gb
```

---

# Database Operations

## Select Database

```bash
SELECT 0
```

---

## List Database Statistics

```bash
INFO KEYSPACE
```

---

## Flush Current Database

```bash
FLUSHDB
```

---

## Flush All Databases

```bash
FLUSHALL
```

⚠ Never execute `FLUSHALL` on a production server unless absolutely certain.

---

# Key Operations

## Create Key

```bash
SET user:1 "Alice"
```

---

## Retrieve Key

```bash
GET user:1
```

---

## Delete Key

```bash
DEL user:1
```

---

## Check Key Exists

```bash
EXISTS user:1
```

---

## Rename Key

```bash
RENAME old_key new_key
```

---

## Determine Key Type

```bash
TYPE user:1
```

---

## Set Expiration

```bash
EXPIRE user:1 300
```

---

## View TTL

```bash
TTL user:1
```

---

## Remove Expiration

```bash
PERSIST user:1
```

---

## View Remaining Expiration (Milliseconds)

```bash
PTTL user:1
```

---

# String Commands

## Set Value

```bash
SET counter 100
```

---

## Increment

```bash
INCR counter
```

---

## Increment by Value

```bash
INCRBY counter 10
```

---

## Decrement

```bash
DECR counter
```

---

## Append

```bash
APPEND greeting " World"
```

---

# Hash Commands

## Create Field

```bash
HSET user:1 name Alice
```

---

## Retrieve Field

```bash
HGET user:1 name
```

---

## Retrieve Entire Hash

```bash
HGETALL user:1
```

---

## Delete Field

```bash
HDEL user:1 age
```

---

## List Fields

```bash
HKEYS user:1
```

---

# List Commands

## Push Left

```bash
LPUSH tasks "Task A"
```

---

## Push Right

```bash
RPUSH tasks "Task B"
```

---

## Pop Left

```bash
LPOP tasks
```

---

## Pop Right

```bash
RPOP tasks
```

---

## View Elements

```bash
LRANGE tasks 0 -1
```

---

# Set Commands

## Add Member

```bash
SADD users Alice
```

---

## Remove Member

```bash
SREM users Alice
```

---

## Check Membership

```bash
SISMEMBER users Alice
```

---

## List Members

```bash
SMEMBERS users
```

---

# Sorted Set Commands

## Add Score

```bash
ZADD leaderboard 100 Alice
```

---

## Retrieve Ranking

```bash
ZRANGE leaderboard 0 -1 WITHSCORES
```

---

## Reverse Ranking

```bash
ZREVRANGE leaderboard 0 9 WITHSCORES
```

---

## Increment Score

```bash
ZINCRBY leaderboard 50 Alice
```

---

# Stream Commands

## Add Entry

```bash
XADD orders * customer Alice amount 100
```

---

## Read Stream

```bash
XREAD STREAMS orders 0
```

---

## Create Consumer Group

```bash
XGROUP CREATE orders workers 0
```

---

## Read from Consumer Group

```bash
XREADGROUP GROUP workers worker1 STREAMS orders >
```

---

# Pub/Sub Commands

## Subscribe

```bash
SUBSCRIBE notifications
```

---

## Publish

```bash
PUBLISH notifications "Hello"
```

---

## Pattern Subscription

```bash
PSUBSCRIBE user.*
```

---

# Transactions

## Start Transaction

```bash
MULTI
```

---

## Queue Commands

```bash
SET counter 1

INCR counter
```

---

## Execute

```bash
EXEC
```

---

## Cancel Transaction

```bash
DISCARD
```

---

# Lua Scripting

Execute Script

```bash
EVAL "return redis.call('PING')" 0
```

---

# Persistence

## Manual Snapshot

```bash
BGSAVE
```

---

## Rewrite AOF

```bash
BGREWRITEAOF
```

---

## Last Save Time

```bash
LASTSAVE
```

---

# Monitoring

## Monitor Every Command

```bash
MONITOR
```

⚠ Extremely expensive. Avoid using on busy production systems.

---

## Slow Log

Retrieve Entries

```bash
SLOWLOG GET
```

---

Reset

```bash
SLOWLOG RESET
```

---

## Latency

```bash
LATENCY DOCTOR
```

---

## Memory Usage

```bash
MEMORY STATS
```

---

## Memory Usage of a Key

```bash
MEMORY USAGE user:1
```

---

## Memory Advisor

```bash
MEMORY DOCTOR
```

---

# Cluster Commands

## Cluster Information

```bash
CLUSTER INFO
```

---

## Cluster Nodes

```bash
CLUSTER NODES
```

---

## Cluster Slots

```bash
CLUSTER SLOTS
```

---

# Scan Commands

## Iterate Keys

```bash
SCAN 0
```

---

## Match Pattern

```bash
SCAN 0 MATCH user:*
```

---

## Count Hint

```bash
SCAN 0 COUNT 500
```

---

⚠ Prefer `SCAN` over `KEYS` in production.

---

# Client Management

List Clients

```bash
CLIENT LIST
```

---

Kill Client

```bash
CLIENT KILL <ip:port>
```

---

Client Name

```bash
CLIENT SETNAME backend-api
```

---

# Benchmarking

Simple Benchmark

```bash
redis-benchmark
```

---

100,000 Requests

```bash
redis-benchmark -n 100000
```

---

Concurrent Clients

```bash
redis-benchmark -c 100
```

---

Pipeline Benchmark

```bash
redis-benchmark -P 16
```

---

# Authentication

Authenticate

```bash
AUTH mypassword
```

---

ACL User

```bash
ACL LIST
```

---

Current User

```bash
ACL WHOAMI
```

---

# Shutdown

Graceful Shutdown

```bash
SHUTDOWN SAVE
```

---

Shutdown Without Saving

```bash
SHUTDOWN NOSAVE
```

---

# Production Debugging Workflow

```text
Server Slow
    │
    ▼
INFO
    │
    ▼
INFO MEMORY
    │
    ▼
SLOWLOG GET
    │
    ▼
LATENCY DOCTOR
    │
    ▼
CLIENT LIST
    │
    ▼
SCAN
    │
    ▼
Investigate Hot Keys
```

---

# Commands to Avoid in Production

| Command | Reason |
|----------|--------|
| `KEYS *` | Blocks Redis while scanning all keys |
| `FLUSHALL` | Deletes every database |
| `FLUSHDB` | Deletes the selected database |
| `MONITOR` | Very expensive on busy servers |
| `DEBUG` | Administrative/debug use only |

---

# Most Frequently Used Commands

| Purpose | Command |
|----------|---------|
| Connect | `redis-cli` |
| Server Info | `INFO` |
| Memory | `INFO MEMORY` |
| Set | `SET` |
| Get | `GET` |
| Delete | `DEL` |
| Expire | `EXPIRE` |
| TTL | `TTL` |
| Scan | `SCAN` |
| Transactions | `MULTI / EXEC` |
| Slow Log | `SLOWLOG GET` |
| Monitor | `MONITOR` |
| Benchmark | `redis-benchmark` |
| Cluster | `CLUSTER INFO` |

---

# Interview Tips

Senior interviewers often expect you to know:

- Why `SCAN` is preferred over `KEYS`
- When to use `MONITOR` and why it's risky
- How to inspect memory usage
- How to diagnose slow commands
- How to connect to a Redis Cluster
- Common troubleshooting commands (`INFO`, `SLOWLOG`, `LATENCY`, `MEMORY`)
- The difference between client-side and server-side diagnostics

---

# Quick Production Checklist

Before making changes to a production Redis instance:

- Verify you are connected to the correct server.
- Check replication status with `INFO REPLICATION`.
- Review memory usage with `INFO MEMORY`.
- Inspect the Slow Log before assuming Redis is the bottleneck.
- Prefer `SCAN` instead of `KEYS`.
- Never run destructive commands (`FLUSHALL`, `FLUSHDB`) without explicit approval.
- Benchmark changes in a staging environment before production deployment.