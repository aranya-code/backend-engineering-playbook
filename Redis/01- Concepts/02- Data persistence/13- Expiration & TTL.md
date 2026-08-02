# Expiration & TTL

## Overview

Caching is one of Redis's primary use cases, and an effective cache requires data to expire automatically. Keeping stale or obsolete data indefinitely wastes memory, increases operational costs, and can lead to applications serving outdated information.

Redis provides built-in support for **Expiration** and **Time-To-Live (TTL)**, allowing keys to be automatically removed after a specified duration. Instead of applications manually tracking when cached data becomes invalid, Redis handles the lifecycle of cached objects efficiently.

TTL is one of Redis's most widely used features in production systems. It is used for session management, API caching, authentication tokens, rate limiting, temporary data storage, distributed locks, and many other backend use cases.

---

# What is TTL?

TTL stands for **Time-To-Live**.

It represents the amount of time a key should remain in Redis before it is automatically deleted.

Conceptually:

```
Cache User Profile

↓

TTL = 1 Hour

↓

1 Hour Passes

↓

Redis Deletes Key
```

No application cleanup is required.

---

# Why is TTL Important?

Consider an application caching product information.

```
Database

↓

Product

↓

Redis Cache
```

If the product price changes in the database:

```
Database

↓

₹1,500
```

but Redis still stores:

```
₹1,200
```

Users receive outdated information.

TTL ensures cached data eventually expires so that fresh data can be retrieved.

---

# How Expiration Works

A key can have an expiration time.

```
Key

↓

user:101

↓

Expires In

↓

30 Minutes
```

After thirty minutes:

```
Redis

↓

Automatically Removes Key
```

The application does not need background cleanup jobs.

---

# Key Lifecycle

A typical lifecycle looks like this.

```
Create Key

↓

Assign TTL

↓

Application Reads Key

↓

TTL Counts Down

↓

TTL Reaches Zero

↓

Key Deleted
```

The deletion happens automatically.

---

# Permanent Keys

Not every key requires expiration.

Example:

```
Country Codes

↓

IN

US

UK

JP
```

This data rarely changes.

Such keys are usually stored permanently.

---

# Temporary Keys

Temporary information benefits greatly from TTL.

Examples:

```
OTP

↓

5 Minutes
```

```
Password Reset Token

↓

15 Minutes
```

```
Email Verification Link

↓

24 Hours
```

Redis automatically removes expired values.

---

# Session Management

One of the most common production use cases.

```
User Login

↓

Create Session

↓

TTL = 30 Minutes

↓

User Active

↓

TTL Refreshed

↓

User Logs Out

↓

Session Removed
```

Inactive sessions disappear automatically.

---

# Authentication Tokens

Authentication systems commonly use TTL.

```
JWT Refresh Token

↓

7 Days
```

```
Access Token

↓

15 Minutes
```

Expired credentials become unusable without manual intervention.

---

# API Response Caching

Backend services often cache API responses.

```
Client

↓

API

↓

Redis

↓

TTL = 5 Minutes
```

Popular endpoints avoid unnecessary database queries while ensuring responses remain reasonably fresh.

---

# Database Query Caching

Frequently executed queries are ideal candidates for TTL.

```
Application

↓

Redis Cache

↓

Database
```

If data exists:

```
Return Cached Data
```

Otherwise:

```
Query Database

↓

Store in Redis

↓

Assign TTL
```

---

# Shopping Cart

Temporary shopping carts commonly use expiration.

```
Cart

↓

Created

↓

TTL = 24 Hours
```

If the customer never completes checkout:

```
Cart

↓

Automatically Deleted
```

Memory is reclaimed without scheduled cleanup.

---

# One-Time Password (OTP)

Security-sensitive applications rely heavily on expiration.

```
Generate OTP

↓

Store

↓

TTL = 5 Minutes

↓

Validate

↓

Delete
```

Expired OTPs cannot be reused.

---

# Rate Limiting

TTL plays an important role in rate limiting.

```
User

↓

Request Counter

↓

TTL = 1 Minute
```

When the TTL expires:

```
Counter Reset
```

This enables rolling rate-limit windows.

---

# Distributed Locks

Distributed locks should never exist forever.

```
Acquire Lock

↓

TTL = 30 Seconds
```

If the application crashes:

```
TTL Expires

↓

Lock Removed
```

This prevents permanent deadlocks.

---

# Cache Invalidation

TTL is one strategy for cache invalidation.

```
Database Updated

↓

Cache Expires

↓

Fresh Data Loaded
```

Applications often combine TTL with explicit cache invalidation for better consistency.

---

# Absolute vs Sliding Expiration

## Absolute Expiration

The expiration time never changes.

```
Created

↓

Expires After

↓

30 Minutes
```

Even if users access the key repeatedly, it expires at the original time.

---

## Sliding Expiration

The expiration timer resets whenever the key is accessed.

```
User Activity

↓

Refresh TTL

↓

Continue Session
```

This is commonly used for login sessions.

---

# Expiration Accuracy

Redis expiration is highly accurate but not necessarily instantaneous.

Internally Redis removes expired keys using two mechanisms.

## Passive Expiration

```
Application Reads Key

↓

Redis Checks TTL

↓

Expired?

↓

Delete Key
```

Expired keys disappear when accessed.

---

## Active Expiration

Redis periodically scans keys with expiration times.

```
Background Process

↓

Find Expired Keys

↓

Delete Them
```

This prevents memory from filling with expired data.

---

# Memory Benefits

Without expiration:

```
Millions of Old Keys

↓

Memory Growth

↓

Poor Performance
```

With TTL:

```
Expired Keys

↓

Automatically Removed

↓

Memory Recovered
```

Automatic expiration is one reason Redis performs well as a cache.

---

# Choosing Appropriate TTL Values

Different workloads require different expiration periods.

| Data Type | Typical TTL |
|------------|-------------|
| OTP | 2–10 Minutes |
| Session | 15–60 Minutes |
| API Cache | 1–10 Minutes |
| Product Cache | 15–60 Minutes |
| Dashboard Cache | 30 Seconds–5 Minutes |
| Refresh Token | Several Days |
| Temporary Upload | Few Hours |

The ideal TTL depends on business requirements rather than technical constraints alone.

---

# Common Production Use Cases

Expiration and TTL are commonly used for:

- User sessions
- Authentication tokens
- API response caching
- Database query caching
- Shopping carts
- Password reset links
- OTP verification
- Rate limiting
- Distributed locks
- Temporary file metadata

---

# Common Mistakes

## Setting Extremely Long TTLs

```
TTL

↓

365 Days
```

Cached data becomes stale and consumes unnecessary memory.

---

## Setting Extremely Short TTLs

```
TTL

↓

2 Seconds
```

The cache becomes ineffective because entries expire before they can be reused.

---

## Forgetting Expiration

```
Temporary Data

↓

No TTL
```

Eventually Redis fills with obsolete keys.

---

## Using Identical TTLs

If millions of keys expire simultaneously:

```
Millions of Keys

↓

Same Expiration Time

↓

Massive Database Requests
```

This phenomenon is known as a **cache avalanche**.

Production systems often introduce slight randomness into TTL values to spread expirations over time.

---

# Best Practices

- Always assign TTL to temporary data.
- Choose TTL based on data freshness requirements.
- Refresh TTL only when business logic requires it.
- Use shorter TTLs for frequently changing information.
- Add randomized expiration to avoid cache avalanches.
- Monitor memory usage and expired key statistics.
- Remove keys explicitly when immediate invalidation is required.

---

# Production Considerations

When designing Redis caches:

- Separate permanent data from temporary data.
- Monitor cache hit and miss ratios.
- Combine TTL with cache invalidation strategies.
- Avoid synchronized expirations across millions of keys.
- Design applications to gracefully handle cache misses.
- Periodically review TTL values as application usage evolves.

---

# Summary

Expiration and TTL are fundamental Redis features that automate the lifecycle of cached and temporary data. By allowing Redis to remove obsolete keys automatically, applications become simpler, more memory efficient, and less prone to serving stale information. Properly selecting TTL values is essential for achieving an effective balance between cache performance, memory utilization, and data freshness in production systems.

---

# Key Takeaways

- TTL (Time-To-Live) determines how long a key remains in Redis.
- Expired keys are automatically removed without application intervention.
- TTL is widely used for sessions, tokens, caching, OTPs, and distributed locks.
- Redis uses both passive and active expiration mechanisms.
- Choosing appropriate TTL values is critical for cache efficiency.
- Randomizing expiration times helps prevent cache avalanches.
- Expiration is one of the core features that makes Redis an effective production-grade caching solution.