# Expiration & TTL Commands

## Overview

Expiration is one of Redis' most powerful features. It allows keys to be automatically removed after a specified amount of time without requiring application intervention.

Instead of manually cleaning up stale data, Redis automatically deletes expired keys in the background, making it ideal for temporary data such as sessions, caches, authentication tokens, rate limiting counters, OTPs, and distributed locks.

Expiration is a core building block for high-performance backend systems and is heavily used in production architectures.

Typical production use cases include:

- Session management
- API rate limiting
- Login attempts
- One-Time Passwords (OTP)
- Password reset links
- Temporary caches
- Distributed locks
- Temporary feature flags
- Shopping cart expiration
- Temporary reservations

---

# How Key Expiration Works

```
Application

↓

SET user:token

↓

Expiration = 30 minutes

↓

Redis

↓

Automatically Deletes Key
```

No cleanup job is required.

---

# Active vs Passive Expiration

Redis removes expired keys using two mechanisms.

## Passive Expiration

A key is checked when it is accessed.

```
Client

↓

GET key

↓

Expired?

↓

Delete

↓

Return NULL
```

---

## Active Expiration

Redis periodically scans keys with expiration times.

```
Background Thread

↓

Sample Expiring Keys

↓

Delete Expired Keys

↓

Repeat
```

This prevents expired keys from accumulating.

---

# Common Expiration Commands

| Command | Description |
|----------|-------------|
| EXPIRE | Set expiration (seconds) |
| PEXPIRE | Set expiration (milliseconds) |
| EXPIREAT | Expire at Unix timestamp |
| PEXPIREAT | Millisecond timestamp expiration |
| TTL | Remaining lifetime (seconds) |
| PTTL | Remaining lifetime (milliseconds) |
| PERSIST | Remove expiration |
| EXPIRETIME | Expiration timestamp |
| PEXPIRETIME | Millisecond expiration timestamp |

---

# EXPIRE

Adds an expiration to an existing key.

Syntax

```redis
EXPIRE key seconds
```

Example

```redis
SET session:1001 active

EXPIRE session:1001 1800
```

Output

```
(integer) 1
```

The key expires after 30 minutes.

---

# SET with EX

A common pattern combines value creation and expiration.

Example

```redis
SET otp:1001 452861 EX 300
```

Redis performs both operations atomically.

Useful for:

- OTPs
- Sessions
- Temporary tokens

---

# SET with PX

Expiration in milliseconds.

Example

```redis
SET lock:payment locked PX 5000
```

Expires after 5 seconds.

Useful for distributed locking.

---

# TTL

Returns remaining lifetime.

Example

```redis
TTL session:1001
```

Output

```
(integer) 1425
```

Meaning:

```
23 minutes 45 seconds remaining
```

---

# TTL Return Values

| Value | Meaning |
|--------|---------|
| Positive | Seconds remaining |
| -1 | No expiration |
| -2 | Key does not exist |

Example

```redis
TTL user:100
```

Output

```
-1
```

No expiration exists.

---

# PTTL

Returns remaining lifetime in milliseconds.

Example

```redis
PTTL lock:100
```

Output

```
4875
```

Useful for precise timing.

---

# EXPIREAT

Expires a key at a specific Unix timestamp.

Example

```redis
EXPIREAT report:100 1700000000
```

Useful for:

- Scheduled cleanup
- Calendar events
- Time-based workflows

---

# PEXPIREAT

Millisecond precision expiration.

Example

```redis
PEXPIREAT report:100 1700000000000
```

---

# PERSIST

Removes expiration from a key.

Example

```redis
PERSIST session:1001
```

Output

```
(integer) 1
```

The key becomes permanent.

---

# EXPIRETIME

Returns the expiration timestamp.

Example

```redis
EXPIRETIME session:1001
```

Output

```
1700005400
```

Useful for monitoring.

---

# PEXPIRETIME

Returns the expiration timestamp in milliseconds.

Example

```redis
PEXPIRETIME session:1001
```

---

# Session Management Example

```
User Login

↓

SET session:abc123

↓

EXPIRE 30 Minutes

↓

Redis

↓

Auto Delete
```

A classic Redis use case.

---

# OTP Example

```
Generate OTP

↓

SET otp:100

↓

EX 300

↓

Valid For 5 Minutes

↓

Automatically Deleted
```

No cleanup process required.

---

# Password Reset Token

```
Generate Token

↓

Redis

↓

Expire After 15 Minutes

↓

User Uses Link

↓

Deleted Automatically
```

---

# Shopping Cart

```
Customer Cart

↓

Redis

↓

Expire After 24 Hours

↓

Inactive Cart Removed
```

---

# Temporary Cache

```
Database Query

↓

Redis Cache

↓

TTL 600 Seconds

↓

Cache Refresh
```

Improves performance while preventing stale data.

---

# Rate Limiting

```
User Request

↓

INCR api:user

↓

EXPIRE 60

↓

Requests Reset Every Minute
```

Very common in API gateways.

---

# Distributed Lock

```
Worker

↓

SET lock

↓

PX 5000

↓

Critical Section

↓

Delete Lock
```

Expiration prevents deadlocks.

---

# Feature Flags

```
Temporary Feature

↓

Redis

↓

TTL

↓

Automatically Disabled
```

Useful during A/B testing.

---

# Cache Expiration Strategies

## Absolute Expiration

```
Created

↓

10 Minutes

↓

Deleted
```

Simple and predictable.

---

## Sliding Expiration

```
Access

↓

Reset TTL

↓

Access Again

↓

Reset TTL
```

Common for user sessions.

---

# Updating TTL

Example

```redis
EXPIRE session:1001 1800
```

Calling EXPIRE again replaces the previous expiration.

---

# Removing Expiration

```
Before

↓

TTL = 600

↓

PERSIST

↓

Permanent Key
```

---

# Checking Key Lifetime

```
Application

↓

TTL

↓

Remaining Time

↓

Display or Refresh
```

---

# Common Production Use Cases

Expiration is commonly used for:

- Session storage
- OTP management
- Authentication tokens
- Password reset links
- Shopping carts
- API rate limiting
- Temporary caches
- Distributed locks
- Temporary reservations
- Login throttling

---

# Common Mistakes

## Forgetting Expiration

```
Temporary Data

↓

Never Deleted

↓

Memory Growth
```

Always expire temporary keys.

---

## Separate SET and EXPIRE

Avoid

```redis
SET token abc123

EXPIRE token 300
```

Instead use

```redis
SET token abc123 EX 300
```

This is atomic.

---

## Using Extremely Long TTLs

Avoid keeping cache entries for days unless necessary.

Stale cache leads to incorrect application behavior.

---

## Expiring Permanent Data

Not every key should expire.

Examples of permanent data:

- User profiles
- Product metadata
- Configuration

---

# Best Practices

- Use `SET EX` whenever possible.
- Keep TTL values consistent.
- Expire every temporary object.
- Use milliseconds only when required.
- Monitor memory usage.
- Refresh session TTL on user activity if implementing sliding sessions.
- Avoid unnecessary long-lived cache entries.
- Document TTL policies.

---

# Performance Considerations

| Command | Complexity |
|----------|------------|
| EXPIRE | O(1) |
| PEXPIRE | O(1) |
| TTL | O(1) |
| PTTL | O(1) |
| PERSIST | O(1) |
| EXPIREAT | O(1) |
| PEXPIREAT | O(1) |
| EXPIRETIME | O(1) |
| PEXPIRETIME | O(1) |

Expiration operations are extremely lightweight.

---

# Production Considerations

For production deployments:

- Always define expiration policies for temporary data.
- Use `SET EX` or `SET PX` instead of separate `SET` and `EXPIRE` commands.
- Monitor the ratio of expiring keys to total memory usage.
- Avoid synchronized expirations on millions of keys, as this can create traffic spikes (known as a cache stampede). Introduce randomized TTLs where appropriate.
- Use sliding expiration carefully for user sessions to avoid unnecessary write amplification.
- Combine expiration with eviction policies to improve cache efficiency.

---

# Expiration Workflow

```
                 Application
                      │
                      ▼
        SET session:123 EX 1800
                      │
                      ▼
                 Redis Stores Key
                      │
              TTL Countdown Begins
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
   Key Accessed               TTL Reaches Zero
        │                           │
        ▼                           ▼
  Return Value              Redis Deletes Key
```

---

# Summary

Redis expiration commands provide an efficient mechanism for managing temporary data by automatically removing keys after a specified lifetime. Whether used for session management, OTP validation, distributed locking, or API rate limiting, expiration eliminates the need for manual cleanup while helping control memory usage. By leveraging commands such as `EXPIRE`, `TTL`, `PERSIST`, and `SET EX`, backend engineers can build scalable, reliable, and self-maintaining systems with minimal operational overhead.

---

# Key Takeaways

- `EXPIRE` and `PEXPIRE` assign a lifetime to existing keys.
- `SET EX` and `SET PX` atomically create keys with expiration.
- `TTL` and `PTTL` report the remaining lifetime.
- `PERSIST` removes expiration and makes a key permanent.
- Redis automatically removes expired keys using active and passive expiration.
- Use expiration for sessions, caches, OTPs, locks, and rate limiting.
- Randomize cache TTLs to reduce cache stampedes in high-traffic systems.
- Define clear expiration policies for all temporary data.
```