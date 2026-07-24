# Redis Coding & Practical Questions

## Overview

Coding interviews are becoming increasingly common for Senior Backend Developers. Rather than asking theoretical questions, interviewers may ask you to implement Redis-based solutions or design production-ready features.

These questions test your ability to:

- Choose the right Redis data structure
- Write efficient Redis commands
- Avoid race conditions
- Design scalable solutions
- Understand atomic operations
- Optimize performance
- Handle distributed systems challenges

Unlike LeetCode-style algorithm questions, Redis coding interviews focus on solving **real backend engineering problems**.

---

# Q1. Design a Rate Limiter using Redis.

### Problem

Allow a user to make at most **100 requests per minute**.

### Expected Approach

Use

```
INCR

+

EXPIRE
```

Workflow

```
Request

↓

INCR user:101

↓

Counter

↓

>100 ?

↓

Reject

↓

Else

↓

Continue
```

Example

```bash
INCR rate_limit:user:101

EXPIRE rate_limit:user:101 60
```

---

## Follow-up

How would you avoid race conditions?

Answer

Use

```
MULTI

EXEC
```

or a Lua script.

---

# Q2. Implement a Login Failure Counter.

### Problem

Lock an account after five failed login attempts within ten minutes.

### Redis Design

```
login_fail:user:101
```

Commands

```bash
INCR login_fail:user:101

EXPIRE login_fail:user:101 600
```

If

```
Counter >= 5
```

↓

Lock account.

---

# Q3. Design an OTP Verification System.

### Requirements

- OTP expires in five minutes.
- One-time use.
- Prevent replay attacks.

Redis

```
SET otp:user:101 835921 EX 300
```

Verification

```
Compare

↓

DELETE Key

↓

Success
```

---

# Q4. Implement a Shopping Cart.

### Suitable Data Structure

```
Hash
```

Example

```
cart:user:101

↓

Product

↓

Quantity
```

Commands

```bash
HSET cart:user:101 product_1001 2

HSET cart:user:101 product_1002 5
```

---

# Q5. Design a Leaderboard.

### Suitable Data Structure

```
Sorted Set
```

Commands

```bash
ZADD leaderboard 1500 Alice

ZADD leaderboard 1750 Bob
```

Retrieve Top 10

```bash
ZREVRANGE leaderboard 0 9 WITHSCORES
```

---

# Q6. Design an Online Users Tracker.

### Suitable Data Structure

```
Set
```

Commands

```bash
SADD online_users user101

SREM online_users user101
```

Check

```bash
SISMEMBER online_users user101
```

---

# Q7. Design a Recent Activity Feed.

### Suitable Data Structure

```
List
```

Workflow

```
New Activity

↓

LPUSH

↓

Latest Feed
```

Commands

```bash
LPUSH feed:user:101 "Order Created"

LTRIM feed:user:101 0 99
```

Keep only the latest 100 activities.

---

# Q8. Design a Notification Queue.

### Suitable Data Structure

```
Streams
```

Producer

```bash
XADD notifications * user 101 type email
```

Consumer

```bash
XREADGROUP
```

Advantages

- Persistence
- Consumer Groups
- Retry support

---

# Q9. Implement Distributed Locking.

### Command

```bash
SET payment_lock value NX EX 30
```

Meaning

```
SET

↓

Only if Not Exists

↓

Expires in 30 Seconds
```

Only one worker acquires the lock.

---

# Q10. How would you safely release the lock?

### Wrong

```bash
DEL payment_lock
```

Problem

Another client may already own the lock.

Correct approach

Use a Lua script that checks the lock value before deleting it.

---

# Q11. Design a Sliding Window Rate Limiter.

### Suitable Data Structure

```
Sorted Set
```

Workflow

```
Current Timestamp

↓

Remove Old Entries

↓

Count Remaining

↓

Add Current Request
```

Commands

```
ZADD

ZREMRANGEBYSCORE

ZCOUNT
```

Provides more accurate rate limiting than a fixed window.

---

# Q12. Design a Cache for Product Details.

Workflow

```
GET Product

↓

Redis

↓

Miss

↓

Database

↓

Redis

↓

Response
```

Pattern

```
Cache Aside
```

---

# Q13. Store User Preferences.

### Suitable Data Structure

```
Hash
```

Example

```bash
HSET prefs:user:101

theme dark

language en

timezone UTC
```

---

# Q14. Count Unique Visitors.

### Suitable Data Structure

```
HyperLogLog
```

Commands

```bash
PFADD visitors user1

PFADD visitors user2

PFCOUNT visitors
```

Advantages

- Very small memory footprint
- Approximate counting

---

# Q15. Track Daily Page Views.

### Suitable Structure

```
String Counter
```

Commands

```bash
INCR pageviews:home:2026-01-15
```

---

# Q16. Design a Feature Flag System.

### Storage

```
Hash
```

Example

```
feature_flags

↓

new_checkout=true

dark_mode=false
```

Application

↓

Read Redis

↓

Enable Feature

---

# Q17. Store Product Inventory.

### Suitable Data Structure

```
Hash
```

Example

```bash
HSET inventory

product101 25

product102 50
```

Atomic update

```bash
HINCRBY inventory product101 -1
```

---

# Q18. Prevent Duplicate Job Execution.

### Workflow

```
Worker

↓

SET NX EX

↓

Success?

↓

Execute Job
```

If the key already exists,

another worker is processing the job.

---

# Q19. Implement Session Storage.

Example

```bash
SET session:abc123

user101

EX 1800
```

Thirty-minute session expiration.

---

# Q20. Cache Expensive Reports.

Workflow

```
Generate Report

↓

Redis

↓

TTL

↓

Future Requests

↓

Cache Hit
```

Typical TTL

```
15 Minutes

30 Minutes

1 Hour
```

depending on freshness requirements.

---

# Q21. Design a Chat Application.

Redis Components

- Streams
- Pub/Sub
- Lists

Architecture

```
User

↓

Application

↓

Redis Streams

↓

Consumers
```

---

# Q22. Store User Search History.

### Suitable Data Structure

```
List
```

Commands

```bash
LPUSH search:user:101 "redis"

LPUSH search:user:101 "django"

LTRIM search:user:101 0 19
```

Keep latest twenty searches.

---

# Q23. Prevent Duplicate API Requests.

Workflow

```
Request ID

↓

SET NX

↓

Already Exists?

↓

Reject Duplicate
```

Useful for payment APIs.

---

# Q24. Cache Aggregated Dashboard Statistics.

Store

```
dashboard

↓

Total Orders

↓

Revenue

↓

Users

↓

Today's Sales
```

Refresh periodically using background workers.

---

# Q25. Design an Idempotency Key Mechanism.

Workflow

```
Client

↓

Idempotency-Key

↓

Redis

↓

Exists?

↓

Return Previous Response

↓

Else

↓

Process Request
```

Useful for

- Payments
- Order creation
- Financial APIs

---

# Q26. Design a Real-Time Counter.

Commands

```bash
INCR

DECR

INCRBY
```

Examples

- Likes
- Downloads
- Active users
- Inventory

---

# Q27. Design a Daily Active Users Counter.

Suitable Structure

```
Set
```

Commands

```bash
SADD dau:2026-01-15 user101

SCARD dau:2026-01-15
```

---

# Q28. How would you benchmark your solution?

Use

```bash
redis-benchmark
```

Measure

- Throughput
- Latency
- Memory
- CPU
- Network

Test under realistic production workloads.

---

# Q29. What mistakes do candidates commonly make?

Common mistakes

- Wrong data structure
- Missing TTL
- No atomicity
- Ignoring concurrency
- Large values
- Blocking commands
- No expiration strategy

---

# Q30. What do interviewers expect in Redis coding rounds?

Interviewers expect you to

- Choose the correct data structure.
- Explain time complexity.
- Discuss scalability.
- Handle race conditions.
- Consider failure scenarios.
- Think about production deployment.

Writing perfect syntax is less important than designing a robust solution.

---

# Rapid Fire Questions

| Problem | Best Redis Feature |
|----------|-------------------|
| Rate Limiter | INCR + EXPIRE |
| Leaderboard | Sorted Set |
| Shopping Cart | Hash |
| Recent Feed | List |
| Online Users | Set |
| Unique Visitors | HyperLogLog |
| Job Queue | Streams |
| Distributed Lock | SET NX EX |

---

# Senior Interview Tips

When solving Redis coding problems, always explain:

1. **Why you chose a particular data structure.**
2. **The time complexity of the operations.**
3. **How the solution behaves under concurrent requests.**
4. **How it scales across multiple application servers.**
5. **How you would monitor it in production.**

For example, don't just say:

> "I'd use a Hash."

Instead explain:

> "A Hash is appropriate because it stores related fields efficiently, supports O(1) lookups for individual fields, reduces memory compared to storing separate keys, and allows atomic field updates using commands like `HINCRBY`."

---

# Common Mistakes

## Choosing the Wrong Data Structure

Using Lists for leaderboards or Strings for complex objects often leads to inefficient designs.

---

## Forgetting Expiration

Temporary data such as OTPs, sessions, and rate-limit counters should almost always have a TTL.

---

## Ignoring Atomicity

Operations involving multiple steps may require transactions or Lua scripts to avoid race conditions.

---

## Overengineering

Not every solution needs Streams or Redis Cluster. Choose the simplest design that satisfies the requirements.

---

# Best Practices

- Match the Redis data structure to the problem domain.
- Prefer atomic commands whenever possible.
- Set TTLs for temporary data.
- Design keys with consistent namespaces.
- Consider concurrency and distributed deployments.
- Validate solutions under production-like load with benchmarking.
- Keep business-critical data in a durable database, using Redis as an accelerator rather than the sole source of truth.

---

# Summary

Redis coding interviews focus on practical backend engineering rather than algorithm puzzles. Success depends on selecting the right data structures, understanding command behavior, designing for concurrency, and explaining production trade-offs. Strong candidates think beyond implementation details and consider scalability, observability, and resilience.

---

# Key Takeaways

- Redis coding problems are centered on real backend use cases.
- Choosing the correct data structure is often more important than writing complex code.
- Atomic operations and TTLs are fundamental building blocks.
- Design solutions with concurrency, scalability, and failure scenarios in mind.
- Always explain trade-offs, complexity, and operational considerations during interviews.