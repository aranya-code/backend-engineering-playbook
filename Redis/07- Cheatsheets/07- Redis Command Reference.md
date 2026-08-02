# Redis Command Reference

## Overview

This command reference is a quick lookup guide for the most commonly used Redis commands. Commands are grouped by category with their syntax, purpose, time complexity, and practical use cases.

> **Note:** Time complexities shown are for the typical case. Actual performance depends on dataset size and access patterns.

---

# Server Commands

| Command | Purpose | Complexity |
|----------|---------|------------|
| `PING` | Test server connectivity | O(1) |
| `INFO` | Server statistics | O(1) |
| `DBSIZE` | Number of keys in current database | O(1) |
| `TIME` | Current server time | O(1) |
| `LASTSAVE` | Last successful RDB save | O(1) |
| `BGSAVE` | Background snapshot | O(1) |
| `BGREWRITEAOF` | Rewrite AOF file | O(1) |
| `SHUTDOWN` | Stop Redis server | O(1) |

---

# Connection Commands

| Command | Purpose |
|----------|---------|
| `AUTH` | Authenticate client |
| `SELECT` | Select logical database |
| `CLIENT LIST` | List connected clients |
| `CLIENT SETNAME` | Assign client name |
| `CLIENT KILL` | Disconnect client |

---

# Key Commands

| Command | Purpose | Complexity |
|----------|---------|------------|
| `SET` | Create or update key | O(1) |
| `GET` | Retrieve value | O(1) |
| `DEL` | Delete key | O(1) |
| `EXISTS` | Check key existence | O(1) |
| `TYPE` | Get key type | O(1) |
| `RENAME` | Rename key | O(1) |
| `COPY` | Copy key | O(1) |
| `MOVE` | Move key to another database | O(1) |
| `TTL` | Remaining lifetime | O(1) |
| `PTTL` | Remaining lifetime (ms) | O(1) |
| `EXPIRE` | Set expiration | O(1) |
| `PEXPIRE` | Set expiration (ms) | O(1) |
| `PERSIST` | Remove expiration | O(1) |

---

# String Commands

| Command | Purpose | Complexity |
|----------|---------|------------|
| `SET` | Store value | O(1) |
| `GET` | Read value | O(1) |
| `GETSET` | Get old value and set new | O(1) |
| `MSET` | Set multiple keys | O(N) |
| `MGET` | Read multiple keys | O(N) |
| `APPEND` | Append text | O(1) |
| `INCR` | Increment integer | O(1) |
| `INCRBY` | Increment by amount | O(1) |
| `DECR` | Decrement integer | O(1) |
| `STRLEN` | Value length | O(1) |

---

# Hash Commands

| Command | Purpose | Complexity |
|----------|---------|------------|
| `HSET` | Set field | O(1) |
| `HGET` | Read field | O(1) |
| `HMGET` | Read multiple fields | O(N) |
| `HGETALL` | Read all fields | O(N) |
| `HDEL` | Delete field | O(1) |
| `HEXISTS` | Check field | O(1) |
| `HKEYS` | List fields | O(N) |
| `HVALS` | List values | O(N) |
| `HLEN` | Number of fields | O(1) |

---

# List Commands

| Command | Purpose | Complexity |
|----------|---------|------------|
| `LPUSH` | Insert left | O(1) |
| `RPUSH` | Insert right | O(1) |
| `LPOP` | Remove left | O(1) |
| `RPOP` | Remove right | O(1) |
| `BLPOP` | Blocking left pop | O(1) |
| `BRPOP` | Blocking right pop | O(1) |
| `LRANGE` | Retrieve range | O(S+N) |
| `LLEN` | List length | O(1) |
| `LINDEX` | Get by index | O(N) |

---

# Set Commands

| Command | Purpose | Complexity |
|----------|---------|------------|
| `SADD` | Add member | O(1) |
| `SREM` | Remove member | O(1) |
| `SMEMBERS` | List members | O(N) |
| `SCARD` | Member count | O(1) |
| `SISMEMBER` | Membership test | O(1) |
| `SUNION` | Union | O(N) |
| `SINTER` | Intersection | O(N×M) |
| `SDIFF` | Difference | O(N) |

---

# Sorted Set Commands

| Command | Purpose | Complexity |
|----------|---------|------------|
| `ZADD` | Add member with score | O(log N) |
| `ZRANGE` | Ascending range | O(log N + M) |
| `ZREVRANGE` | Descending range | O(log N + M) |
| `ZRANK` | Ascending rank | O(log N) |
| `ZREVRANK` | Descending rank | O(log N) |
| `ZSCORE` | Member score | O(1) |
| `ZINCRBY` | Increase score | O(log N) |
| `ZREM` | Remove member | O(log N) |
| `ZCARD` | Member count | O(1) |

---

# Stream Commands

| Command | Purpose |
|----------|---------|
| `XADD` | Add message |
| `XRANGE` | Read range |
| `XREAD` | Read stream |
| `XGROUP CREATE` | Create consumer group |
| `XREADGROUP` | Read from consumer group |
| `XACK` | Acknowledge message |
| `XPENDING` | View pending messages |
| `XDEL` | Delete message |

---

# Pub/Sub Commands

| Command | Purpose |
|----------|---------|
| `PUBLISH` | Publish message |
| `SUBSCRIBE` | Subscribe to channel |
| `PSUBSCRIBE` | Pattern subscription |
| `UNSUBSCRIBE` | Remove subscription |
| `PUBSUB CHANNELS` | List channels |

---

# Transaction Commands

| Command | Purpose |
|----------|---------|
| `MULTI` | Begin transaction |
| `EXEC` | Execute transaction |
| `DISCARD` | Cancel transaction |
| `WATCH` | Watch keys |
| `UNWATCH` | Remove watched keys |

---

# Lua Scripting

| Command | Purpose |
|----------|---------|
| `EVAL` | Execute Lua script |
| `EVALSHA` | Execute cached script |
| `SCRIPT LOAD` | Cache script |
| `SCRIPT EXISTS` | Check cached script |
| `SCRIPT FLUSH` | Remove cached scripts |

---

# Cluster Commands

| Command | Purpose |
|----------|---------|
| `CLUSTER INFO` | Cluster status |
| `CLUSTER NODES` | Node information |
| `CLUSTER SLOTS` | Slot mapping |
| `CLUSTER KEYSLOT` | Hash slot for key |
| `CLUSTER MEET` | Add node |
| `CLUSTER FORGET` | Remove node |

---

# Replication Commands

| Command | Purpose |
|----------|---------|
| `INFO REPLICATION` | Replication status |
| `REPLICAOF` | Configure replica |
| `ROLE` | Display node role |

---

# Memory Commands

| Command | Purpose |
|----------|---------|
| `INFO MEMORY` | Memory statistics |
| `MEMORY USAGE` | Memory used by key |
| `MEMORY STATS` | Detailed memory metrics |
| `MEMORY DOCTOR` | Memory analysis |

---

# Monitoring Commands

| Command | Purpose |
|----------|---------|
| `SLOWLOG GET` | View slow commands |
| `SLOWLOG RESET` | Clear slow log |
| `LATENCY DOCTOR` | Latency diagnosis |
| `MONITOR` | View all executed commands |
| `INFO STATS` | Runtime statistics |

---

# Scan Commands

| Command | Purpose | Production Safe |
|----------|---------|-----------------|
| `SCAN` | Iterate keys | ✅ |
| `HSCAN` | Iterate hash fields | ✅ |
| `SSCAN` | Iterate set members | ✅ |
| `ZSCAN` | Iterate sorted set | ✅ |
| `KEYS` | Return all matching keys | ❌ |

---

# ACL Commands

| Command | Purpose |
|----------|---------|
| `ACL LIST` | List users |
| `ACL SETUSER` | Create or modify user |
| `ACL DELUSER` | Delete user |
| `ACL WHOAMI` | Current authenticated user |

---

# Administrative Commands

| Command | Use With Caution |
|----------|------------------|
| `FLUSHDB` | Deletes current database |
| `FLUSHALL` | Deletes all databases |
| `CONFIG GET` | Read configuration |
| `CONFIG SET` | Modify configuration |
| `SAVE` | Blocking snapshot |
| `SHUTDOWN` | Stops Redis |

---

# Production-Safe Command Checklist

✅ Safe for regular production use:

- `GET`
- `SET`
- `HGET`
- `HSET`
- `INFO`
- `SCAN`
- `TTL`
- `EXPIRE`
- `SLOWLOG GET`
- `LATENCY DOCTOR`
- `CLIENT LIST`

⚠ Use carefully:

- `MONITOR`
- `CONFIG SET`
- `SAVE`

❌ Avoid during normal production operations:

- `KEYS *`
- `FLUSHDB`
- `FLUSHALL`
- `DEBUG`

---

# Most Common Commands by Use Case

| Task | Commands |
|------|----------|
| Caching | `SET`, `GET`, `EXPIRE`, `TTL` |
| Sessions | `SET`, `GET`, `EXPIRE` |
| Counters | `INCR`, `DECR`, `INCRBY` |
| User Profiles | `HSET`, `HGET`, `HGETALL` |
| Queues | `LPUSH`, `RPOP`, `BLPOP` |
| Leaderboards | `ZADD`, `ZRANGE`, `ZREVRANGE` |
| Messaging | `PUBLISH`, `SUBSCRIBE` |
| Event Processing | `XADD`, `XREADGROUP`, `XACK` |
| Monitoring | `INFO`, `SLOWLOG GET`, `LATENCY DOCTOR` |

---

# Interview Quick Revision

For senior backend interviews, you should be able to explain:

- Which Redis command is appropriate for each data structure.
- The time complexity of common commands.
- Why `SCAN` is preferred over `KEYS`.
- How transactions (`MULTI`/`EXEC`) differ from SQL transactions.
- When to use Streams instead of Lists or Pub/Sub.
- Which commands are unsafe on production systems and why.
- How monitoring commands (`INFO`, `SLOWLOG`, `LATENCY`) help diagnose performance issues.