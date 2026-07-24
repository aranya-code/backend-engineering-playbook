# Rate Limiting with Redis

## Overview

**Rate Limiting** is a technique used to control **how many requests a client can make within a specific time window**.

Without rate limiting, a malicious or poorly designed client can:

- Overload APIs
- Exhaust backend resources
- Cause database spikes
- Trigger denial-of-service (DoS) attacks
- Increase infrastructure costs

Redis is one of the most popular technologies for implementing rate limiting because it provides:

- Extremely fast read/write operations
- Atomic operations
- Automatic expiration (TTL)
- Distributed access
- High scalability

Today, almost every API Gateway, authentication service, payment platform, and SaaS application implements some form of Redis-based rate limiting.

---

# Why Rate Limiting Matters

Consider a public login API.

Without rate limiting:

```
Attacker

↓

1,000,000 Login Requests

↓

Application

↓

Database

↓

Authentication Service
```

Every request is processed.

---

With rate limiting:

```
Attacker

↓

Redis Rate Limiter

↓

100 Requests Allowed

↓

999,900 Rejected
```

The backend remains protected.

---

# Common Use Cases

Rate limiting is commonly used for:

- Login APIs
- OTP generation
- Password reset
- Public REST APIs
- GraphQL APIs
- Payment APIs
- Search APIs
- File uploads
- Email sending
- SMS verification
- AI inference APIs
- Third-party integrations

---

# What Can Be Limited?

Rate limiting can be applied based on:

- IP Address
- User ID
- API Key
- Access Token
- Organization
- Device ID
- Geographic Region
- Endpoint
- Tenant

Example:

```
Rate Limit

↓

User ID

↓

100 Requests / Minute
```

---

# Basic Redis Counter

The simplest implementation uses:

```
INCR

+

EXPIRE
```

Flow:

```
Client

↓

Redis

↓

INCR

↓

Count

↓

Allowed?
```

---

# Redis Commands

```
INCR api:user:123
```

Returns

```
1

2

3

4
```

Set expiration

```
EXPIRE api:user:123 60
```

Counter automatically resets after one minute.

---

# Fixed Window Algorithm

The simplest algorithm.

Example:

```
100 Requests

↓

1 Minute
```

Timeline

```
12:00

↓

Counter = 100

↓

12:01

↓

Counter Reset
```

---

## Architecture

```
Client

↓

Redis Counter

↓

Count < Limit?

├── Yes

│      ↓

│ Allow

│

└── No

↓

Reject
```

---

## Python Example

```python
import redis

r = redis.Redis()

LIMIT = 100
WINDOW = 60

key = "rate:user:123"

count = r.incr(key)

if count == 1:
    r.expire(key, WINDOW)

if count > LIMIT:
    raise Exception("Rate limit exceeded")
```

---

## Advantages

- Very simple
- Fast
- Easy to implement

---

## Disadvantages

Boundary problem.

Example:

```
12:00:59

100 Requests

12:01:00

100 Requests
```

User effectively sends

```
200 Requests

↓

2 Seconds
```

---

# Sliding Window Log

Instead of one counter, store timestamps.

```
Request

↓

Timestamp

↓

Redis Sorted Set
```

Old timestamps removed continuously.

---

## Architecture

```
Client

↓

Redis ZSET

↓

Remove Old Entries

↓

Count

↓

Allow?
```

---

## Redis Commands

```
ZADD

ZREMRANGEBYSCORE

ZCARD
```

---

## Workflow

```
Current Time

↓

Remove Old Requests

↓

Count Remaining

↓

Below Limit?

↓

Allow
```

Much more accurate.

---

# Sliding Window Counter

Hybrid approach.

Uses multiple small windows.

```
Minute

↓

10 Buckets

↓

Average Requests
```

Better accuracy than Fixed Window with lower memory usage than Sliding Log.

---

# Token Bucket Algorithm

One of the most widely used algorithms.

Imagine a bucket containing tokens.

```
Bucket

↓

100 Tokens
```

Every request consumes one token.

```
Request

↓

Token Available?

↓

Yes

↓

Process
```

No token?

```
Reject
```

---

## Bucket Refill

```
Bucket

↓

+10 Tokens / Second
```

Users can make bursts of requests while maintaining a long-term rate limit.

---

## Example

Bucket

```
Capacity

100 Tokens
```

Refill

```
10 Tokens

↓

Every Second
```

Traffic

```
Burst

↓

Allowed

↓

Eventually Limited
```

---

# Leaky Bucket Algorithm

Imagine a leaking bucket.

```
Incoming Requests

↓

Bucket

↓

Constant Leak

↓

Backend
```

Requests leave at a constant rate.

---

## Example

```
1000 Requests

↓

Bucket

↓

50 Requests / Second
```

Backend receives a smooth traffic flow.

---

# Fixed Window vs Sliding Window vs Token Bucket

| Algorithm | Burst Handling | Accuracy | Complexity |
|------------|---------------|-----------|------------|
| Fixed Window | Poor | Low | Low |
| Sliding Window | Excellent | High | Medium |
| Token Bucket | Excellent | High | Medium |
| Leaky Bucket | Smooth Traffic | High | Medium |

---

# Distributed Rate Limiting

Suppose multiple application servers exist.

```
Load Balancer

↓

App 1

App 2

App 3
```

Without Redis

Each server maintains its own counter.

User bypasses limits by switching servers.

---

Using Redis

```
App 1

↓

Redis

↑

App 2

↑

App 3
```

One shared counter.

Rate limits remain consistent.

---

# Redis Cluster

Large systems use

```
API Gateway

↓

Redis Cluster

↓

Shared Counters
```

Supports millions of users.

---

# API Gateway Architecture

```
Internet

↓

Load Balancer

↓

API Gateway

↓

Redis Rate Limiter

↓

Backend Services
```

Rate limiting occurs before business logic executes.

---

# Login Protection

```
User

↓

Login API

↓

Redis

↓

5 Attempts

↓

Blocked
```

Helps prevent brute-force attacks.

---

# OTP Protection

```
Phone Number

↓

Redis

↓

3 OTPs / Hour
```

Prevents abuse.

---

# Password Reset

```
Email

↓

Redis

↓

5 Requests / Day
```

Stops spam.

---

# AI API Example

```
API Key

↓

Redis

↓

1000 Requests / Day
```

Common in LLM APIs.

---

# Multi-Tenant SaaS

```
Tenant A

↓

1000 Requests/Minute

Tenant B

↓

100 Requests/Minute
```

Each tenant has independent limits.

---

# Redis Lua Script

Instead of:

```
INCR

↓

EXPIRE
```

Two separate commands.

Use Lua.

```
Lua Script

↓

Atomic

↓

Counter

↓

Expiration
```

No race conditions.

---

## Example

```lua
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

return current
```

Lua ensures both operations execute atomically.

---

# HTTP Response

Typical response

```
HTTP 429

Too Many Requests
```

Useful headers

```
Retry-After

X-RateLimit-Limit

X-RateLimit-Remaining

X-RateLimit-Reset
```

---

# Monitoring

Monitor

- Requests per user
- Blocked requests
- Redis latency
- Redis memory
- Hot keys
- Top IP addresses
- API Gateway metrics

---

# Common Production Use Cases

Redis-based rate limiting is widely used for:

- Authentication services
- API gateways
- Payment systems
- AI platforms
- SMS providers
- Email providers
- Banking APIs
- GraphQL APIs
- SaaS platforms
- Public REST APIs

---

# Common Mistakes

## Limiting Only by IP

```
Corporate Network

↓

1000 Users

↓

One IP
```

Legitimate users may be blocked.

Combine IP with user ID or API key where possible.

---

## No Expiration

```
Counter

↓

Never Reset
```

Users become permanently blocked.

Always set a TTL.

---

## Separate INCR and EXPIRE Without Atomicity

If the application crashes between:

```
INCR

↓

Crash

↓

EXPIRE Never Executed
```

The key never expires.

Use Lua scripts or Redis transactions.

---

## Using Fixed Window for Critical APIs

Fixed Window allows traffic spikes at window boundaries.

Use Sliding Window or Token Bucket for production APIs requiring smoother enforcement.

---

## Ignoring HTTP 429

Always return meaningful responses with retry information.

---

# Best Practices

- Use **Token Bucket** or **Sliding Window** for production APIs.
- Store counters in Redis rather than application memory.
- Execute counter updates atomically using Lua scripts.
- Apply limits as early as possible, preferably at the API Gateway.
- Different endpoints should have different rate limits based on business requirements.
- Include informative HTTP headers so clients can implement backoff.
- Monitor blocked requests and adjust limits using real traffic patterns.
- Combine rate limiting with authentication, WAFs, and circuit breakers for layered protection.

---

# Performance Considerations

| Algorithm | Memory Usage | CPU | Burst Support | Recommended |
|------------|-------------|-----|---------------|-------------|
| Fixed Window | Very Low | Very Low | Poor | Small APIs |
| Sliding Window Counter | Low | Low | Good | Most APIs |
| Sliding Window Log | High | Medium | Excellent | High-Accuracy APIs |
| Token Bucket | Low | Low | Excellent | Large Production Systems |
| Leaky Bucket | Medium | Medium | Excellent | Traffic Shaping |

---

# Production Considerations

For production deployments:

- Use Redis Cluster for distributed rate limiting across multiple application instances.
- Prefer Lua scripts to ensure atomic counter updates.
- Separate rate limits by endpoint, user role, API key, or tenant.
- Monitor hot keys caused by extremely active users or shared API keys.
- Integrate rate limiting into API gateways (Nginx, Kong, Envoy, or custom middleware).
- Support graceful degradation by returning HTTP 429 with retry guidance instead of generic errors.
- Load test rate-limiting behavior under burst traffic to validate both correctness and performance.

---

# Decision Guide

| Scenario | Recommended Algorithm |
|----------|------------------------|
| Login API | Token Bucket |
| Public REST API | Sliding Window Counter |
| Payment API | Token Bucket |
| AI/LLM API | Token Bucket |
| OTP Service | Fixed Window |
| SMS Service | Fixed Window |
| GraphQL API | Sliding Window |
| API Gateway | Token Bucket |
| Banking API | Sliding Window |
| Multi-Tenant SaaS | Token Bucket + Per-Tenant Limits |

---

# Summary

Rate limiting is a critical mechanism for protecting APIs and backend services from abuse, accidental overload, and denial-of-service attacks. Redis is an excellent choice for implementing distributed rate limiting because of its high performance, atomic operations, and built-in expiration capabilities. While Fixed Window algorithms are simple to implement, production systems often prefer Sliding Window or Token Bucket approaches for smoother traffic control and better user experience. Combining Redis-based rate limiting with API gateways, authentication, monitoring, and security controls creates a robust and scalable defense for modern distributed applications.

---

# Key Takeaways

- Rate limiting controls how many requests a client can make within a defined time period.
- Redis is widely used for distributed rate limiting due to its speed and atomic operations.
- Fixed Window is simple but suffers from boundary issues.
- Sliding Window provides more accurate request tracking.
- Token Bucket is the preferred algorithm for many production systems because it supports controlled bursts.
- Use Lua scripts to perform `INCR` and `EXPIRE` atomically.
- Return HTTP **429 Too Many Requests** along with retry headers.
- Apply rate limiting at the API Gateway and monitor traffic continuously for optimal protection.