# Hash Commands

## Overview

Redis Hashes are one of the most frequently used data structures in production applications. A Hash stores data as **field-value pairs**, making it ideal for representing structured objects such as users, products, orders, sessions, and configuration settings.

Instead of storing an entire object as a serialized JSON string, Hashes allow individual fields to be read and updated independently.

For example:

```
User

↓

+----------------------+
| id        : 1001     |
| name      : John     |
| email     : john@... |
| city      : London   |
| age       : 30       |
+----------------------+
```

Hashes are extremely memory efficient and support constant-time operations for most commands.

Typical production use cases include:

- User profiles
- Product catalogs
- Customer records
- Shopping carts
- Application configuration
- Session metadata
- Feature flags
- IoT device state
- Game player profiles
- Account information

---

# Understanding Redis Hashes

Unlike Strings, a Hash stores multiple fields inside a single key.

```
user:1001

│

├── name     → John

├── email    → john@example.com

├── city     → London

└── age      → 30
```

This closely resembles:

- Python Dictionary
- Java HashMap
- JavaScript Object
- JSON Object

---

# Common Hash Commands

| Command | Description |
|----------|-------------|
| HSET | Set field values |
| HGET | Retrieve a field |
| HMSET* | Set multiple fields (deprecated) |
| HMGET | Retrieve multiple fields |
| HGETALL | Retrieve entire hash |
| HDEL | Delete fields |
| HEXISTS | Check field existence |
| HLEN | Number of fields |
| HKEYS | Retrieve field names |
| HVALS | Retrieve values |
| HINCRBY | Increment integer field |
| HINCRBYFLOAT | Increment floating value |
| HSETNX | Set field only if absent |
| HSCAN | Incremental iteration |

> **Note:** `HMSET` is deprecated. Use `HSET` with multiple field-value pairs instead.

---

# HSET

Stores one or more field-value pairs.

Syntax

```redis
HSET key field value
```

Example

```redis
HSET user:1001

name John

age 30

city London
```

Output

```
(integer) 3
```

Complexity

```
O(1)
```

Per field.

---

# HGET

Returns a field value.

Example

```redis
HGET user:1001 name
```

Output

```
John
```

Complexity

```
O(1)
```

---

# HSET (Multiple Fields)

Modern Redis allows multiple fields.

```redis
HSET product:100

name Laptop

price 75000

stock 50

brand Lenovo
```

Much better than multiple HSET commands.

---

# HMGET

Retrieves multiple fields.

Example

```redis
HMGET

user:1001

name

city

age
```

Output

```
John

London

30
```

Useful for reducing network round trips.

---

# HGETALL

Returns the entire object.

Example

```redis
HGETALL user:1001
```

Output

```
name

John

city

London

age

30
```

Complexity

```
O(N)
```

Where N is the number of fields.

---

# HEXISTS

Checks whether a field exists.

Example

```redis
HEXISTS

user:1001

email
```

Output

```
(integer) 1
```

Useful for:

- Validation
- Conditional updates
- Configuration checks

---

# HDEL

Deletes one or more fields.

Example

```redis
HDEL

user:1001

city
```

Output

```
(integer) 1
```

---

# HLEN

Returns the number of fields.

Example

```redis
HLEN user:1001
```

Output

```
(integer) 5
```

Useful for:

- Validation
- Analytics
- Monitoring

---

# HKEYS

Returns all field names.

Example

```redis
HKEYS user:1001
```

Output

```
name

email

city

age
```

---

# HVALS

Returns all values.

Example

```redis
HVALS user:1001
```

Output

```
John

john@example.com

London

30
```

---

# HINCRBY

Atomically increments an integer field.

Example

```redis
HINCRBY

user:1001

login_count

1
```

Current

```
login_count

15
```

After

```
16
```

Useful for:

- Login count
- Product views
- API usage
- Statistics

---

# HINCRBYFLOAT

Increments floating-point fields.

Example

```redis
HINCRBYFLOAT

product:100

rating

0.5
```

Useful for:

- Ratings
- Financial data
- Measurements

---

# HSETNX

Sets a field only if it does not exist.

Example

```redis
HSETNX

config

environment

production
```

Useful for:

- Initialization
- Defaults
- Configuration

---

# HSCAN

Incrementally scans a hash.

Example

```redis
HSCAN user:1001 0
```

Recommended for:

- Very large hashes
- Production systems

Avoid loading extremely large hashes using HGETALL.

---

# User Profile Example

```
user:1001

│

├── name

├── email

├── phone

├── city

└── country
```

Retrieve one field

```
HGET

↓

Email
```

Update one field

```
HSET

↓

City
```

No need to overwrite the entire object.

---

# Product Catalog Example

```
product:501

↓

Name

Price

Category

Stock

Brand

Rating
```

Inventory update

```
HINCRBY

↓

Stock
```

---

# Shopping Cart Example

```
cart:100

↓

Product 1

↓

Quantity

↓

Product 2

↓

Quantity
```

Hashes efficiently maintain item quantities.

---

# Session Storage

```
session:abc123

↓

User ID

Login Time

Role

Device

IP Address
```

---

# Configuration Management

```
application:config

↓

Environment

↓

Timeout

↓

Retries

↓

Log Level
```

Each setting can be updated independently.

---

# IoT Device State

```
device:001

↓

Temperature

Humidity

Battery

Signal Strength
```

Sensor readings can be updated individually.

---

# Common Production Use Cases

Hashes are commonly used for:

- User profiles
- Product metadata
- Customer records
- Sessions
- Shopping carts
- Feature flags
- Device metadata
- Application settings
- CRM systems
- Game player information

---

# Common Mistakes

## Using Strings for Structured Objects

Bad

```
User

↓

JSON String
```

Updating one field requires rewriting the entire value.

Better

```
Redis Hash
```

---

## Loading Huge Hashes

Avoid

```redis
HGETALL
```

on hashes containing thousands of fields.

Instead:

- HMGET
- HSCAN

---

## Too Many Tiny Hashes

Each Redis key has metadata overhead.

Sometimes grouping related data improves efficiency.

---

## Forgetting Atomic Operations

Avoid

```
Read

↓

Increment in Application

↓

Write
```

Instead use

```
HINCRBY
```

---

# Best Practices

- Use Hashes for structured objects.
- Store only related fields.
- Keep field names consistent.
- Use HMGET instead of HGETALL whenever possible.
- Use HSCAN for very large hashes.
- Increment counters using HINCRBY.
- Store IDs instead of nested objects.
- Document hash schemas.

---

# Performance Considerations

| Command | Complexity |
|----------|------------|
| HSET | O(1) |
| HGET | O(1) |
| HEXISTS | O(1) |
| HDEL | O(1) |
| HLEN | O(1) |
| HINCRBY | O(1) |
| HINCRBYFLOAT | O(1) |
| HSETNX | O(1) |
| HMGET | O(N) |
| HKEYS | O(N) |
| HVALS | O(N) |
| HGETALL | O(N) |
| HSCAN | O(1) per iteration |

---

# Hashes vs Strings

| Feature | String | Hash |
|---------|--------|------|
| Single Value | ✅ | ❌ |
| Multiple Fields | ❌ | ✅ |
| Partial Updates | ❌ | ✅ |
| Memory Efficient | Good | Excellent |
| Structured Data | Poor | Excellent |
| Counters | ✅ | ✅ |

---

# Production Considerations

For production deployments:

- Use Hashes instead of JSON strings when frequent field updates are required.
- Avoid extremely large hashes containing thousands of fields.
- Retrieve only required fields instead of using `HGETALL`.
- Monitor memory usage for high-cardinality hashes.
- Use `HSCAN` for administrative tasks involving large hashes.
- Combine Hashes with Sorted Sets or Sets for indexing and search.

---

# Summary

Redis Hashes provide an efficient and scalable way to store structured objects as field-value pairs. They enable applications to update individual attributes without rewriting entire objects, reducing bandwidth and improving performance. With commands like `HSET`, `HGET`, `HMGET`, and `HINCRBY`, Hashes are a natural choice for representing users, products, sessions, configurations, and many other business entities. Their memory efficiency and constant-time operations make them one of the most heavily used Redis data structures in production systems.

---

# Key Takeaways

- Redis Hashes store structured data as **field-value pairs**.
- Use `HSET` and `HGET` for storing and retrieving fields.
- Prefer `HMGET` over `HGETALL` when only specific fields are needed.
- `HINCRBY` and `HINCRBYFLOAT` provide atomic updates for numeric fields.
- Use `HSCAN` to iterate over very large hashes safely.
- Hashes are ideal for user profiles, product catalogs, sessions, and application configuration.
- Store related fields together and avoid excessively large hashes for optimal performance.
```