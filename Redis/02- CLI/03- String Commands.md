# String Commands

## Overview

Strings are the **most fundamental and widely used data type in Redis**. Despite the name, a Redis String is **not limited to text**. It can store plain text, integers, floating-point numbers, JSON strings, serialized objects, binary data, images, compressed payloads, and more.

Every Redis key ultimately points to a value, and in nearly every application, the majority of keys are Strings.

Strings power many common backend features, including:

- Application caching
- User sessions
- Authentication tokens
- API responses
- Feature flags
- Counters
- Rate limiting
- Configuration storage
- Distributed locks
- Temporary data

This chapter covers the most commonly used Redis String commands, explains their behavior, time complexity, production use cases, and best practices.

---

# Understanding Redis Strings

A Redis String is simply:

```
Key
 │
 ▼
Value
```

Example:

```
user:1001

↓

"John Doe"
```

Unlike traditional programming languages, Redis Strings can store values up to **512 MB**.

---

# Common String Commands

| Command | Description |
|----------|-------------|
| SET | Store a value |
| GET | Retrieve a value |
| MSET | Store multiple values |
| MGET | Retrieve multiple values |
| APPEND | Append data |
| STRLEN | Get string length |
| GETRANGE | Read part of a string |
| SETRANGE | Replace part of a string |
| GETSET | Replace and return old value |
| INCR | Increment integer |
| INCRBY | Increment by value |
| DECR | Decrement integer |
| DECRBY | Decrement by value |
| INCRBYFLOAT | Increment floating-point number |
| SETEX | Set value with expiration |
| PSETEX | Set value with millisecond expiration |
| SETNX | Set only if key does not exist |

---

# SET

Stores a value.

Syntax

```redis
SET key value
```

Example

```redis
SET username "john"
```

Output

```
OK
```

Complexity

```
O(1)
```

Production Uses

- Cache data
- Sessions
- Tokens
- Configuration
- Temporary storage

---

# GET

Retrieves a value.

Syntax

```redis
GET key
```

Example

```redis
GET username
```

Output

```
"john"
```

If the key doesn't exist:

```
(nil)
```

Complexity

```
O(1)
```

---

# MSET

Stores multiple values atomically.

Syntax

```redis
MSET key1 value1 key2 value2 ...
```

Example

```redis
MSET

user:1 John

user:2 Alice

user:3 Bob
```

Benefits

- Single network round trip
- Atomic execution
- Better performance

---

# MGET

Reads multiple keys.

Example

```redis
MGET

user:1

user:2

user:3
```

Output

```
1) "John"

2) "Alice"

3) "Bob"
```

Excellent for reducing network latency.

---

# APPEND

Appends text.

Example

```redis
SET greeting "Hello"

APPEND greeting " World"
```

Result

```
Hello World
```

Useful for

- Logs
- Text accumulation
- Audit records

---

# STRLEN

Returns string length.

Example

```redis
STRLEN greeting
```

Output

```
11
```

Useful for

- Validation
- Size monitoring
- Content verification

---

# GETRANGE

Reads part of a string.

Example

```redis
GETRANGE greeting 0 4
```

Output

```
Hello
```

Useful when dealing with large values.

---

# SETRANGE

Replaces a portion of a string.

Example

```redis
SETRANGE greeting 6 Redis
```

Result

```
Hello Redis
```

---

# GETSET

Returns the old value and replaces it.

Example

```redis
GETSET version "v2"
```

Output

```
"v1"
```

Useful for

- Configuration updates
- Token rotation
- State transitions

---

# INCR

Increments an integer.

Example

```redis
SET visits 10

INCR visits
```

Result

```
11
```

Complexity

```
O(1)
```

Production Uses

- Page views
- Login counts
- API usage
- Statistics

---

# INCRBY

Increment by a custom amount.

Example

```redis
INCRBY balance 500
```

---

# DECR

Decrements by one.

Example

```redis
DECR inventory
```

Useful for

- Inventory
- Remaining attempts
- Queue size

---

# DECRBY

Decrease by a specified amount.

Example

```redis
DECRBY stock 25
```

---

# INCRBYFLOAT

Works with floating-point values.

Example

```redis
INCRBYFLOAT price 2.75
```

Useful for

- Financial calculations
- Analytics
- Measurements

---

# SETEX

Stores a value with an expiration time.

Syntax

```redis
SETEX key seconds value
```

Example

```redis
SETEX

session:100

3600

token
```

Automatically expires after one hour.

Common Uses

- Sessions
- OTPs
- Cache entries
- Temporary data

---

# PSETEX

Millisecond version of SETEX.

Example

```redis
PSETEX

job

5000

processing
```

Expires after 5 seconds.

---

# SETNX

Set only if the key does not already exist.

Example

```redis
SETNX lock:user:10 locked
```

Output

```
(integer) 1
```

If the key exists:

```
(integer) 0
```

Common Uses

- Distributed locking
- Resource allocation
- One-time initialization

---

# Atomic Operations

Redis guarantees that every command executes atomically.

```
Client A

↓

INCR Counter

↓

Redis

↓

Counter Updated

↓

Client B Waits
```

No partial updates occur.

---

# Backend Architecture Example

```
                 Client
                    │
                    ▼
              User Service
                    │
                    ▼
              Redis Strings
      ┌──────────┼──────────┐
      │          │          │
      ▼          ▼          ▼
 Sessions   API Cache   Counters
```

Strings are often the default choice for simple key-value storage.

---

# Common Production Use Cases

### Session Storage

```
session:abc123

↓

User Information
```

---

### Authentication Tokens

```
token:xyz

↓

JWT Metadata
```

---

### API Response Cache

```
cache:products

↓

Serialized JSON
```

---

### Rate Limiting

```
user:100:requests

↓

125
```

Updated using `INCR`.

---

### Feature Flags

```
feature:new-dashboard

↓

enabled
```

---

### Distributed Locks

```
lock:payment

↓

locked
```

Created using `SETNX`.

---

# Common Mistakes

## Using Strings for Structured Objects

Bad

```
User Object

↓

Huge String
```

Better

```
Redis Hash
```

---

## Forgetting Expiration

Temporary data should expire automatically.

Prefer

```
SETEX
```

instead of

```
SET
```

for cache entries.

---

## Multiple Network Calls

Avoid

```
GET

GET

GET
```

Prefer

```
MGET
```

---

## Manual Counters

Avoid

```
GET

Increment in Application

SET
```

Use

```
INCR
```

instead.

---

# Best Practices

- Use meaningful key names.
- Prefer MGET/MSET for batch operations.
- Use SETEX for cache entries.
- Use INCR for counters.
- Use SETNX for distributed locking.
- Avoid storing extremely large strings.
- Monitor memory consumption.

---

# Performance Considerations

| Operation | Complexity |
|-----------|------------|
| SET | O(1) |
| GET | O(1) |
| INCR | O(1) |
| DECR | O(1) |
| STRLEN | O(1) |
| APPEND | O(1) (amortized) |
| GETRANGE | O(N) |
| SETRANGE | O(N) |
| MGET | O(N) |
| MSET | O(N) |

---

# Production Considerations

For production Redis deployments:

- Keep values reasonably small.
- Compress very large payloads if appropriate.
- Avoid storing entire database records as giant strings.
- Apply expiration to cache data.
- Use atomic increment commands instead of application-side calculations.
- Monitor hot keys and oversized values.
- Use pipelining for bulk String operations to reduce network overhead.

---

# Summary

Redis Strings are the foundation of most Redis deployments and provide an extremely fast, versatile key-value storage mechanism. From caching API responses and managing user sessions to implementing counters, rate limiters, and distributed locks, String commands are used extensively in modern backend systems. By leveraging atomic operations, expiration mechanisms, and batch commands like MGET and MSET, developers can build scalable, efficient, and highly performant applications.

---

# Key Takeaways

- Strings are the most commonly used Redis data type.
- A Redis String can store text, numbers, binary data, and serialized objects up to 512 MB.
- `SET` and `GET` are the primary commands for storing and retrieving values.
- Use `MGET` and `MSET` to reduce network round trips.
- Use `INCR`, `DECR`, and related commands for atomic counters.
- Apply expiration using `SETEX` for temporary data such as caches and sessions.
- Use `SETNX` to implement simple distributed locking patterns.
- Choose Strings for simple key-value storage, but use more suitable data structures like Hashes for complex objects.