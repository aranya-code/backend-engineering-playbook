# Redis CLI Cheat Sheet

## Overview

This cheat sheet provides a quick reference for the most commonly used Redis CLI commands. It is intended for day-to-day development, debugging, production support, and interview preparation.

Use this guide when you need to quickly remember command syntax without reading the detailed documentation.

---

# Redis CLI Basics

| Command | Description |
|----------|-------------|
| `redis-cli` | Start Redis CLI |
| `redis-cli -h host -p port` | Connect to remote Redis |
| `redis-cli -a password` | Authenticate |
| `redis-cli --tls` | Connect using TLS |
| `QUIT` | Exit CLI |
| `HELP` | Show help |
| `PING` | Check server availability |

---

# Key Commands

| Command | Description |
|----------|-------------|
| `EXISTS key` | Check if key exists |
| `DEL key` | Delete key |
| `UNLINK key` | Asynchronous delete |
| `TYPE key` | Get data type |
| `RENAME old new` | Rename key |
| `COPY source destination` | Copy key |
| `MOVE key db` | Move to another database |
| `TTL key` | Remaining expiration time |
| `PTTL key` | Remaining expiration in milliseconds |
| `PERSIST key` | Remove expiration |
| `SCAN 0` | Incrementally scan keys |
| `MEMORY USAGE key` | Memory used by key |

---

# String Commands

| Command | Description |
|----------|-------------|
| `SET key value` | Store value |
| `GET key` | Retrieve value |
| `MSET` | Store multiple values |
| `MGET` | Retrieve multiple values |
| `APPEND` | Append string |
| `STRLEN` | String length |
| `GETRANGE` | Retrieve substring |
| `SETRANGE` | Replace substring |
| `INCR` | Increment integer |
| `INCRBY` | Increment by value |
| `DECR` | Decrement integer |
| `DECRBY` | Decrement by value |
| `INCRBYFLOAT` | Increment float |
| `SETEX` | Set with expiration |
| `SETNX` | Set if absent |

---

# List Commands

| Command | Description |
|----------|-------------|
| `LPUSH` | Push left |
| `RPUSH` | Push right |
| `LPOP` | Pop left |
| `RPOP` | Pop right |
| `LLEN` | List size |
| `LRANGE` | Retrieve range |
| `LINDEX` | Retrieve element |
| `LSET` | Update element |
| `LINSERT` | Insert element |
| `LREM` | Remove elements |
| `LTRIM` | Trim list |
| `LMOVE` | Move between lists |
| `BLPOP` | Blocking left pop |
| `BRPOP` | Blocking right pop |
| `BLMOVE` | Blocking move |

---

# Set Commands

| Command | Description |
|----------|-------------|
| `SADD` | Add member |
| `SREM` | Remove member |
| `SMEMBERS` | List members |
| `SCARD` | Count members |
| `SISMEMBER` | Membership check |
| `SPOP` | Remove random member |
| `SRANDMEMBER` | Random member |
| `SMOVE` | Move member |
| `SUNION` | Union |
| `SINTER` | Intersection |
| `SDIFF` | Difference |
| `SSCAN` | Scan members |

---

# Sorted Set Commands

| Command | Description |
|----------|-------------|
| `ZADD` | Add member |
| `ZRANGE` | Ascending range |
| `ZREVRANGE` | Descending range |
| `ZRANK` | Rank |
| `ZREVRANK` | Reverse rank |
| `ZSCORE` | Get score |
| `ZINCRBY` | Increase score |
| `ZCOUNT` | Count by score |
| `ZRANGEBYSCORE` | Score range |
| `ZREM` | Remove member |
| `ZPOPMIN` | Remove lowest score |
| `ZPOPMAX` | Remove highest score |
| `ZSCAN` | Scan sorted set |

---

# Hash Commands

| Command | Description |
|----------|-------------|
| `HSET` | Set field |
| `HGET` | Get field |
| `HMGET` | Multiple fields |
| `HGETALL` | Entire hash |
| `HEXISTS` | Field exists |
| `HDEL` | Delete field |
| `HLEN` | Field count |
| `HKEYS` | Field names |
| `HVALS` | Values |
| `HINCRBY` | Increment integer |
| `HINCRBYFLOAT` | Increment float |
| `HSETNX` | Set if absent |
| `HSCAN` | Scan hash |

---

# Stream Commands

| Command | Description |
|----------|-------------|
| `XADD` | Add event |
| `XRANGE` | Read events |
| `XREVRANGE` | Reverse read |
| `XLEN` | Stream size |
| `XREAD` | Read stream |
| `XGROUP CREATE` | Create consumer group |
| `XREADGROUP` | Read as consumer |
| `XACK` | Acknowledge |
| `XPENDING` | Pending messages |
| `XCLAIM` | Claim message |
| `XTRIM` | Trim stream |
| `XINFO` | Stream information |

---

# Transaction Commands

| Command | Description |
|----------|-------------|
| `MULTI` | Begin transaction |
| `EXEC` | Execute transaction |
| `DISCARD` | Cancel transaction |
| `WATCH` | Optimistic locking |
| `UNWATCH` | Stop watching |

---

# Pub/Sub Commands

| Command | Description |
|----------|-------------|
| `PUBLISH` | Publish message |
| `SUBSCRIBE` | Subscribe channel |
| `PSUBSCRIBE` | Pattern subscribe |
| `UNSUBSCRIBE` | Unsubscribe |
| `PUNSUBSCRIBE` | Pattern unsubscribe |
| `PUBSUB CHANNELS` | Active channels |
| `PUBSUB NUMSUB` | Subscriber count |
| `PUBSUB NUMPAT` | Pattern subscriptions |

---

# Expiration Commands

| Command | Description |
|----------|-------------|
| `EXPIRE` | Expire in seconds |
| `PEXPIRE` | Expire in milliseconds |
| `EXPIREAT` | Unix timestamp expiration |
| `PEXPIREAT` | Millisecond timestamp |
| `TTL` | Remaining seconds |
| `PTTL` | Remaining milliseconds |
| `PERSIST` | Remove expiration |
| `EXPIRETIME` | Expiration timestamp |
| `PEXPIRETIME` | Millisecond timestamp |

---

# Server Commands

| Command | Description |
|----------|-------------|
| `PING` | Health check |
| `INFO` | Server information |
| `CLIENT LIST` | Connected clients |
| `CLIENT KILL` | Disconnect client |
| `DBSIZE` | Number of keys |
| `MEMORY STATS` | Memory statistics |
| `MEMORY USAGE key` | Memory used by key |
| `SLOWLOG GET` | Slow queries |
| `LATENCY LATEST` | Latency events |
| `MONITOR` | Live commands |
| `BGSAVE` | Background snapshot |
| `LASTSAVE` | Last snapshot |
| `TIME` | Server time |

---

# Configuration Commands

| Command | Description |
|----------|-------------|
| `CONFIG GET` | Read configuration |
| `CONFIG SET` | Change configuration |
| `CONFIG RESETSTAT` | Reset statistics |
| `CONFIG REWRITE` | Persist configuration |
| `ACL LIST` | List users |
| `ACL SETUSER` | Create/update user |
| `ACL DELUSER` | Delete user |
| `ACL WHOAMI` | Current user |

---

# Dangerous Commands

| Command | Why Dangerous |
|----------|---------------|
| `KEYS *` | Blocks Redis on large datasets |
| `FLUSHDB` | Deletes current database |
| `FLUSHALL` | Deletes all databases |
| `SAVE` | Blocks Redis during snapshot |
| `MONITOR` | High overhead on busy servers |
| `DEBUG` | Administrative/debug only |

---

# Production Best Practices

✅ Prefer `SCAN` over `KEYS`

✅ Prefer `UNLINK` over `DEL` for large keys

✅ Use `SET key value EX seconds` instead of separate `SET` + `EXPIRE`

✅ Store IDs instead of large objects

✅ Use `BGSAVE` instead of `SAVE`

✅ Review `SLOWLOG` regularly

✅ Monitor `INFO MEMORY`

✅ Use ACLs instead of a shared password

✅ Configure `maxmemory` and an appropriate eviction policy

✅ Use Consumer Groups with Streams for reliable processing

---

# Complexity Cheat Sheet

| Operation | Complexity |
|-----------|------------|
| GET | O(1) |
| SET | O(1) |
| HGET | O(1) |
| HSET | O(1) |
| SADD | O(1) |
| SISMEMBER | O(1) |
| SCARD | O(1) |
| ZADD | O(log N) |
| ZRANGE | O(log N + M) |
| XADD | O(log N) |
| MULTI | O(1) |
| EXEC | O(N) |
| EXPIRE | O(1) |
| TTL | O(1) |
| INFO | O(1) |
| CONFIG SET | O(1) |

---

# Interview Quick Revision

## Data Structures

- String → Simple values, counters, cache
- List → Queues, stacks
- Set → Unique collections
- Sorted Set → Rankings, leaderboards
- Hash → Objects, user profiles
- Stream → Event processing

---

## Persistence

- RDB → Fast snapshots
- AOF → Better durability
- RDB + AOF → Production recommendation

---

## Replication

- Primary → Read/Write
- Replica → Read-only
- Sentinel → High availability
- Cluster → Horizontal scaling

---

## Performance Rules

- Avoid `KEYS`
- Prefer `SCAN`
- Keep values small
- Use pipelining
- Monitor memory
- Set TTL for temporary data
- Use Lua scripts for complex atomic logic
- Monitor slow queries

---

# Summary

This cheat sheet consolidates the most frequently used Redis CLI commands into a single reference for development, production support, and interviews. While it is not a replacement for the detailed chapters, it serves as a practical quick-reference guide that backend engineers can keep open during daily work or technical interviews.