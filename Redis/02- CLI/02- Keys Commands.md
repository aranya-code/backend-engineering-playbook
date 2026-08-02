# Keys Commands

## Overview

Every piece of data stored in Redis is identified by a **key**. Regardless of the underlying data type—String, Hash, List, Set, Sorted Set, Stream, or Module—the first step in interacting with Redis is identifying the correct key.

Redis provides a rich collection of key management commands that allow developers and administrators to:

- Discover existing keys
- Check key existence
- Rename keys
- Delete data
- Move keys between databases
- Inspect metadata
- Copy keys
- Analyze memory usage
- Iterate efficiently through large datasets

Understanding these commands is critical because poor key management can significantly impact application performance and even bring production Redis servers to a halt.

This chapter explores the most important key-related commands, their use cases, performance implications, and production best practices.

---

# Key Naming Convention

A well-designed naming strategy improves maintainability and debugging.

Recommended format:

```
<Application>:<Module>:<Entity>:<Identifier>
```

Examples:

```
user:1001

user:1001:profile

session:9fd8ab2

cart:501

cache:products

order:1500

inventory:item:120
```

Good naming conventions help:

- Avoid collisions
- Simplify debugging
- Group related data
- Support efficient scanning

---

# EXISTS

Checks whether one or more keys exist.

Syntax

```redis
EXISTS key
```

Example

```redis
SET user:1 "John"

EXISTS user:1
```

Output

```
(integer) 1
```

If the key does not exist:

```
(integer) 0
```

Multiple keys:

```redis
EXISTS user:1 user:2 user:3
```

Returns the number of existing keys.

### Complexity

```
O(N)
```

Where N is the number of keys supplied.

### Common Use Cases

- Validate cache entries
- Session validation
- Feature flag existence
- Conditional logic

---

# DEL

Deletes one or more keys immediately.

Syntax

```redis
DEL key
```

Example

```redis
DEL user:1
```

Output

```
(integer) 1
```

Multiple keys:

```redis
DEL user:1 user:2 session:1
```

### Complexity

```
O(N)
```

Large objects may take longer to delete.

### Production Note

Deleting extremely large keys may briefly block Redis.

---

# UNLINK

Deletes keys asynchronously.

Syntax

```redis
UNLINK key
```

Example

```redis
UNLINK cache:homepage
```

Unlike DEL, memory cleanup occurs in the background.

```
Client

↓

UNLINK

↓

Redis

↓

Background Memory Cleanup
```

### Advantages

- Non-blocking
- Better for production
- Safer for large objects

### Recommended

Prefer `UNLINK` when deleting:

- Large Lists
- Large Sets
- Large Hashes
- Large Sorted Sets

---

# TYPE

Returns the Redis data type.

Syntax

```redis
TYPE key
```

Example

```redis
TYPE user:1
```

Output

```
string
```

Possible values:

- string
- list
- set
- zset
- hash
- stream
- none

Useful during debugging.

---

# RENAME

Renames a key.

Syntax

```redis
RENAME oldKey newKey
```

Example

```redis
RENAME user:1 customer:1
```

If the destination exists, it is overwritten.

---

# RENAMENX

Rename only if destination does not exist.

Syntax

```redis
RENAMENX oldKey newKey
```

Example

```redis
RENAMENX user:1 customer:1
```

Output

```
(integer) 1
```

If destination already exists:

```
(integer) 0
```

Useful when avoiding accidental overwrites.

---

# COPY

Creates a duplicate of a key.

Syntax

```redis
COPY source destination
```

Example

```redis
COPY user:1 backup:user:1
```

Useful for:

- Temporary backups
- Testing
- Data migration

---

# MOVE

Moves a key to another logical database.

Syntax

```redis
MOVE key database
```

Example

```redis
MOVE user:1 2
```

Returns:

```
(integer) 1
```

Limitations:

- Not supported in Redis Cluster
- Rarely used in production

---

# RANDOMKEY

Returns a random key.

Syntax

```redis
RANDOMKEY
```

Example

```
"user:245"
```

Useful mainly for:

- Testing
- Demonstrations

Not recommended for production logic.

---

# TOUCH

Updates a key's idle time without modifying its value.

Syntax

```redis
TOUCH key
```

Useful for:

- LRU policies
- Cache simulations
- Monitoring

---

# KEYS

Returns keys matching a pattern.

Syntax

```redis
KEYS pattern
```

Example

```redis
KEYS user:*
```

Output

```
user:1
user:2
user:3
```

Patterns:

```
*

?

[]

prefix*

user:*

session:*

cache:*
```

---

# Why KEYS is Dangerous

Although simple, KEYS performs a complete scan of the database.

```
Entire Database

↓

KEYS *

↓

Returns Every Key
```

Complexity:

```
O(N)
```

If Redis contains:

- 10 million keys
- 100 million keys

KEYS scans every one of them.

During this scan, Redis blocks other requests because Redis processes commands in a single thread.

This can increase latency dramatically.

### Never Use KEYS in Production

Except for:

- Tiny datasets
- Development
- Local debugging

---

# SCAN

SCAN is the production-safe alternative to KEYS.

Syntax

```redis
SCAN cursor
```

Example

```redis
SCAN 0
```

Output

```
1) "42"
2) 1) "user:1"
   2) "user:2"
```

The cursor is then reused.

```
SCAN 42

↓

Next Batch

↓

SCAN 88

↓

Next Batch

↓

Cursor = 0

↓

Finished
```

---

# SCAN Options

Pattern matching:

```redis
SCAN 0 MATCH user:*
```

Limit batch size:

```redis
SCAN 0 COUNT 100
```

Combine:

```redis
SCAN 0 MATCH session:* COUNT 500
```

---

# KEYS vs SCAN

| Feature | KEYS | SCAN |
|----------|------|------|
| Blocking | Yes | No |
| Production Safe | No | Yes |
| Incremental | No | Yes |
| Large Databases | Poor | Excellent |
| Performance | Poor | Excellent |

Production systems should almost always use **SCAN**.

---

# OBJECT

Provides metadata about a key.

Examples:

```redis
OBJECT ENCODING user:1
```

```redis
OBJECT REFCOUNT user:1
```

```redis
OBJECT IDLETIME user:1
```

Useful for:

- Debugging
- Performance tuning
- Memory optimization

---

# MEMORY USAGE

Shows approximate memory consumed by a key.

Syntax

```redis
MEMORY USAGE user:1
```

Output

```
(integer) 128
```

Useful when:

- Investigating memory issues
- Finding oversized keys
- Capacity planning

---

# Typical Backend Workflow

```
Application

↓

SET Data

↓

EXISTS

↓

TYPE

↓

MEMORY USAGE

↓

SCAN

↓

DELETE Old Data
```

---

# Common Production Use Cases

Key commands are used for:

- Cache management
- Session cleanup
- User profile storage
- Job queues
- Inventory systems
- Shopping carts
- API rate limiting
- Feature flags
- Distributed locking
- Data migration

---

# Common Mistakes

## Using KEYS in Production

Never execute:

```redis
KEYS *
```

On a Redis instance containing millions of keys.

---

## Poor Naming Convention

Bad:

```
123

abc

data1
```

Good:

```
user:100

cart:500

order:250

session:a8df92
```

---

## Deleting Large Keys with DEL

Deleting huge collections may temporarily block Redis.

Prefer:

```redis
UNLINK
```

---

## Forgetting to Check Key Type

Running List commands on a Hash results in errors.

Always verify:

```redis
TYPE key
```

---

# Best Practices

- Design consistent key naming conventions.
- Prefer SCAN over KEYS.
- Use EXISTS before expensive operations when appropriate.
- Use UNLINK for deleting large datasets.
- Monitor memory usage regularly.
- Group related keys using prefixes.
- Avoid exposing internal naming conventions to external clients.
- Periodically scan for orphaned or unused keys.

---

# Production Considerations

Large production Redis clusters may contain hundreds of millions of keys.

Efficient key management is therefore essential.

Production recommendations:

- Never use `KEYS *`
- Prefer incremental scanning
- Monitor oversized keys
- Use structured prefixes
- Document naming standards
- Regularly audit keyspace growth

---

# Summary

Key management commands form the foundation of every Redis application. From discovering and deleting keys to inspecting metadata and scanning massive datasets safely, these commands are indispensable for development and operations. While commands like `KEYS` are useful for learning, production systems should rely on scalable alternatives such as `SCAN` and `UNLINK`. By following proper naming conventions and operational best practices, backend engineers can build Redis deployments that remain efficient, maintainable, and performant even at scale.

---

# Key Takeaways

- Every Redis object is accessed through a key.
- Use structured naming conventions for maintainability.
- `EXISTS`, `TYPE`, and `MEMORY USAGE` are valuable debugging tools.
- Prefer `UNLINK` over `DEL` for large objects.
- Never use `KEYS` on large production databases.
- Use `SCAN` for safe, incremental key iteration.
- Monitor keyspace growth and memory usage as part of regular operations.