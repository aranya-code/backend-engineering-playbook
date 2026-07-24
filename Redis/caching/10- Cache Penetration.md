# Cache Penetration

## Overview

**Cache Penetration** occurs when an application repeatedly requests **data that does not exist** in either Redis or the database.

Since the requested data is never found, Redis cannot cache a valid value, causing **every request to bypass the cache and hit the database**.

Unlike Cache Stampede or Cache Avalanche, where cached data expires, Cache Penetration involves **invalid or non-existent data**.

If attackers intentionally generate large numbers of requests for non-existent keys, the database can become overloaded, resulting in a Denial-of-Service (DoS) attack.

---

# What Causes Cache Penetration?

Suppose a user requests:

```
GET /products/999999999
```

Product **999999999** does not exist.

Application flow:

```
Client

↓

Redis

↓

Miss

↓

Database

↓

Not Found

↓

Response
```

Nothing is cached.

The next request repeats the same process.

---

# Normal Cache Flow

```
Client

↓

Redis

↓

Hit

↓

Response
```

Database is bypassed.

---

# Cache Penetration Flow

```
Client

↓

Redis

↓

Miss

↓

Database

↓

Not Found

↓

Response
```

Every request reaches the database.

---

# Multiple Requests

Imagine 10,000 requests for invalid IDs.

```
10,000 Requests

↓

Redis Miss

↓

10,000 Database Queries

↓

No Records Found
```

Redis provides no benefit.

---

# Real Production Example

Suppose an e-commerce platform contains products:

```
1

2

3

...

100000
```

An attacker sends requests for:

```
999999999

999999998

999999997
```

Every request:

```
Redis

↓

Miss

↓

Database

↓

Not Found
```

Database CPU increases rapidly.

---

# Why It Is Dangerous

Cache penetration can cause:

- Database overload
- High CPU usage
- Connection pool exhaustion
- Increased latency
- Slow API responses
- DoS attacks
- Increased cloud costs

---

# Detecting Cache Penetration

Monitor:

Redis

```
Miss Ratio

↓

High
```

Database

```
SELECT

↓

Returns Zero Rows

↓

Very High
```

Application

```
404 Responses

↓

Sudden Increase
```

Large numbers of "Not Found" queries are a warning sign.

---

# Solution 1 — Cache Null Values

The simplest solution.

Instead of

```
Database

↓

Not Found

↓

Nothing Cached
```

Cache

```
NULL

↓

TTL = 60 Seconds
```

Future requests

```
Redis

↓

NULL

↓

Return Immediately
```

No database query.

---

# Python Example

```python
def get_product(product_id):

    key = f"product:{product_id}"

    value = redis.get(key)

    if value is not None:

        if value == "NULL":
            return None

        return deserialize(value)

    product = database.get(product_id)

    if product is None:

        redis.set(
            key,
            "NULL",
            ex=60
        )

        return None

    redis.set(
        key,
        serialize(product),
        ex=3600
    )

    return product
```

---

# Advantages of Null Caching

```
First Request

↓

Database

↓

NULL Cached

↓

Future Requests

↓

Redis
```

Database load drops dramatically.

---

# Disadvantages

If a product is later created

```
NULL Cached

↓

Product Added

↓

Old NULL Remains
```

Choose short TTLs.

Typically

```
30–120 Seconds
```

---

# Solution 2 — Bloom Filter

A Bloom Filter is a probabilistic data structure that determines whether an object **might exist**.

```
Client

↓

Bloom Filter

↓

Possible?

├── No

│      ↓

│ Reject Request

│

└── Yes

↓

Redis
```

Database traffic is greatly reduced.

---

# Bloom Filter Architecture

```
Client

↓

Bloom Filter

↓

Redis

↓

Database
```

Invalid requests never reach Redis.

---

# Bloom Filter Example

Suppose database IDs

```
100

101

102

103
```

Bloom Filter knows these IDs.

Request

```
999999
```

Bloom Filter

```
Definitely Not Present

↓

Reject
```

Database is never queried.

---

# Bloom Filter Characteristics

| Feature | Value |
|----------|-------|
| False Negatives | Never |
| False Positives | Possible |
| Memory Usage | Very Low |
| Lookup Speed | O(1) |

False positives are acceptable because Redis still performs the lookup.

---

# Solution 3 — Request Validation

Validate requests before querying Redis.

Example

Instead of

```
Product ID

-100
```

Reject immediately.

```
400 Bad Request
```

Similarly

```
Product ID

abc123
```

Reject before database access.

---

# Example Validation

```python
if product_id <= 0:
    raise HTTPException(
        status_code=400
    )
```

Simple validation prevents unnecessary work.

---

# Solution 4 — Rate Limiting

Suppose one client requests

```
10000 Invalid IDs
```

Rate limiter

```
100 Requests/Minute

↓

Blocked
```

Useful against malicious traffic.

---

# Solution 5 — Web Application Firewall (WAF)

```
Internet

↓

WAF

↓

Application
```

Suspicious traffic is blocked before reaching Redis.

---

# Solution 6 — Authentication

Anonymous users often generate abuse.

```
Login

↓

Access API
```

Authenticated APIs reduce penetration attacks.

---

# Solution 7 — API Gateway Validation

```
Client

↓

API Gateway

↓

Redis

↓

Database
```

Gateway validates:

- ID format
- Request size
- Authentication
- Rate limits

before forwarding requests.

---

# Real-World Example

## Product API

Without protection

```
Redis

↓

Miss

↓

Database

↓

No Product
```

Repeated forever.

---

With NULL cache

```
Redis

↓

NULL

↓

Immediate Response
```

Database avoided.

---

# Banking Example

```
Account Number

↓

Bloom Filter

↓

Invalid

↓

Reject
```

Database remains protected.

---

# Gaming Platform

```
Player ID

↓

Validation

↓

Redis

↓

Database
```

Only valid IDs proceed.

---

# Large Social Network

```
User ID

↓

Bloom Filter

↓

Redis

↓

Database
```

Millions of invalid requests are filtered.

---

# Cache Penetration vs Cache Stampede

| Feature | Cache Penetration | Cache Stampede |
|----------|------------------|----------------|
| Cause | Invalid Keys | Expired Hot Key |
| Database Queries | Continuous | Temporary Spike |
| Redis Contains Data | No | Previously Yes |
| Prevention | Bloom Filter | Distributed Lock |

---

# Cache Penetration vs Cache Avalanche

| Feature | Cache Penetration | Cache Avalanche |
|----------|------------------|-----------------|
| Keys | Invalid | Valid |
| Cache State | Never Cached | Expired |
| Database Load | Continuous | Sudden Spike |
| Cause | Missing Data | Mass Expiration |

---

# Common Production Use Cases

Protection against cache penetration is important for:

- Public REST APIs
- GraphQL APIs
- Product catalogs
- User profile services
- Banking systems
- Gaming platforms
- Authentication services
- Social media platforms
- Search services

---

# Common Mistakes

## Not Caching Null Values

```
Missing Product

↓

Database

↓

Again

↓

Database

↓

Again
```

Repeated database hits.

---

## Long NULL TTL

```
NULL

↓

Product Added

↓

Still Cached
```

Use short expiration.

---

## No Input Validation

```
Negative IDs

↓

Database
```

Reject invalid requests immediately.

---

## Ignoring Attack Patterns

Monitor:

- 404 responses
- Invalid IDs
- Miss ratio
- Request rate

---

# Best Practices

- Cache NULL responses with a short TTL (30–120 seconds).
- Use Bloom Filters for very large datasets.
- Validate all request parameters before querying Redis.
- Apply rate limiting to public APIs.
- Use API gateways or WAFs to block suspicious traffic.
- Monitor high cache miss ratios and repeated "not found" queries.
- Combine multiple protection techniques rather than relying on a single solution.

---

# Performance Considerations

| Technique | Database Load | Memory Usage | Complexity |
|------------|---------------|--------------|------------|
| NULL Cache | Very Low | Low | Low |
| Bloom Filter | Extremely Low | Very Low | Medium |
| Validation | Low | None | Very Low |
| Rate Limiting | Low | None | Medium |
| WAF | Low | None | Medium |

---

# Production Considerations

For production deployments:

- Enable NULL caching for frequently requested missing objects, but keep TTLs short.
- Use RedisBloom (or another Bloom Filter implementation) for systems with millions of keys.
- Log and analyze repeated requests for invalid IDs—they may indicate abuse or attacks.
- Place request validation as early as possible, preferably at the API gateway.
- Monitor metrics such as cache miss ratio, database queries returning zero rows, and HTTP 404 rates.
- Combine Bloom Filters with rate limiting for public-facing APIs exposed to the internet.
- Regularly rebuild Bloom Filters if the underlying dataset changes significantly.

---

# Decision Guide

| Scenario | Recommended Solution |
|----------|----------------------|
| Product Catalog | NULL Cache + Bloom Filter |
| Banking API | Bloom Filter + Validation |
| Public REST API | Rate Limiting + WAF |
| Authentication Service | Validation + Rate Limiting |
| Gaming Platform | NULL Cache |
| Social Media | Bloom Filter |
| Search API | Bloom Filter + NULL Cache |
| Internal API | Validation |

---

# Summary

Cache Penetration occurs when requests repeatedly target data that does not exist, forcing every request to bypass Redis and query the database. Unlike cache stampedes or avalanches, the cache is never populated because the requested data is invalid or missing. Effective mitigation strategies include caching NULL values, using Bloom Filters, validating input, applying rate limiting, and filtering malicious traffic at the API gateway or WAF. Combining these techniques protects backend databases and ensures Redis remains an effective caching layer.

---

# Key Takeaways

- Cache Penetration is caused by repeated requests for non-existent data.
- Every request bypasses Redis and reaches the database unless mitigated.
- Caching NULL values is the simplest protection technique.
- Bloom Filters efficiently reject requests for keys that definitely do not exist.
- Validate request parameters before accessing Redis or the database.
- Rate limiting and WAFs help defend against malicious penetration attacks.
- Monitor cache misses, 404 responses, and zero-row database queries.
- Layer multiple protection mechanisms for production-grade systems.