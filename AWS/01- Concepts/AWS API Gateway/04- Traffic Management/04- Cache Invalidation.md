# Cache Invalidation

## Overview

Caching improves API performance by serving responses directly from memory. However, cached data eventually becomes **stale** when the underlying backend data changes.

**Cache Invalidation** is the process of removing or refreshing cached responses so that clients receive the most recent data.

Without proper cache invalidation:

- Users may see outdated information.
- APIs may return incorrect business data.
- Inventory counts may be inaccurate.
- Prices may not reflect recent updates.
- Configuration changes may not take effect immediately.

A well-designed caching strategy always includes a cache invalidation strategy.

---

# Why Cache Invalidation?

Suppose a Product API caches product information.

```text
Client

↓

API Gateway Cache

↓

Product

↓

₹999
```

Later, an administrator updates the product price.

```text
Admin

↓

Database

↓

₹1199
```

If the cache is not invalidated:

```text
Client

↓

Cache

↓

₹999
```

The customer receives outdated data.

---

# Architecture

```text
             Client

                │

                ▼

        Amazon API Gateway

                │

          API Cache

        ┌───────┴────────┐

        ▼                ▼

 Cached Response   Backend Service

        ▲                │

        └────────────────┘

         Cache Refresh
```

The cache should always reflect the latest backend data.

---

# Cache Lifecycle

```text
First Request

↓

Backend

↓

Store Response

↓

Serve Cached Response

↓

Backend Data Changes

↓

Invalidate Cache

↓

Next Request

↓

Fresh Backend Response
```

---

# Cache Expiration (TTL)

The simplest invalidation mechanism is **Time To Live (TTL).**

Example:

```text
TTL

300 Seconds
```

Flow:

```text
Request

↓

Cache

↓

5 Minutes

↓

Expired

↓

Backend

↓

New Cache Entry
```

TTL is automatic but may not always provide sufficiently fresh data.

---

# Manual Cache Flush

API Gateway allows the entire stage cache to be flushed manually.

```text
Administrator

↓

Flush Cache

↓

All Cached Responses Removed

↓

Next Requests

↓

Backend
```

This is useful after:

- Major deployments
- Bulk data imports
- Configuration changes

---

# Automatic Cache Refresh

After cache expiration:

```text
Cache Miss

↓

Backend

↓

Updated Response

↓

Store in Cache
```

No manual intervention is required.

---

# Example

Initial request:

```text
GET /products/100
```

Response:

```json
{
    "price": 999
}
```

Stored in cache.

Later:

```text
Database

↓

Price Updated

↓

1199
```

After cache invalidation:

```json
{
    "price": 1199
}
```

---

# When Should Cache Be Invalidated?

Cache should be refreshed after:

- Product updates
- Inventory changes
- Price changes
- User role changes
- Configuration updates
- Content publishing
- Feature flag updates

---

# Cache Invalidation Strategies

Several strategies are commonly used.

---

## 1. Time-Based Expiration

The cache automatically expires after a configured TTL.

```text
Store

↓

Wait

↓

Expire

↓

Reload
```

Advantages:

- Simple
- Automatic
- No application logic

Disadvantages:

- Stale data exists until TTL expires.

---

## 2. Manual Cache Flush

Administrator clears the cache.

```text
Deploy

↓

Flush Cache

↓

Fresh Data
```

Useful for deployments.

---

## 3. Event-Driven Invalidation

Backend updates trigger cache invalidation.

```text
Database Update

↓

Event

↓

Invalidate Cache

↓

Fresh Response
```

This provides the freshest data.

---

## 4. Short TTL Strategy

Instead of explicit invalidation:

```text
TTL

30 Seconds
```

Data remains relatively fresh without manual intervention.

---

# Cache Warming

Sometimes caches are populated before users arrive.

```text
Deployment

↓

Warm Cache

↓

Popular APIs Cached

↓

Users

↓

Fast Responses
```

This avoids the "cold cache" problem.

---

# Cold Cache

Immediately after deployment:

```text
Request

↓

Cache Miss

↓

Backend
```

The first users experience slightly higher latency.

Afterward:

```text
Cache Hit

↓

Fast Response
```

---

# Cache Stampede

Suppose a popular cache entry expires.

```text
10,000 Users

↓

Cache Miss

↓

10,000 Backend Requests
```

Backend load spikes dramatically.

Mitigation strategies include:

- Staggered TTLs
- Cache warming
- Backend caching
- Distributed caches

---

# Cache Invalidation vs Cache Expiration

| Cache Expiration | Cache Invalidation |
|------------------|-------------------|
| Automatic | Manual or Event-Driven |
| Based on TTL | Triggered by data changes |
| Simple | More Accurate |
| May Serve Stale Data | Fresh Data Immediately |

---

# API Gateway Cache vs Backend Cache

| API Gateway Cache | Backend Cache |
|-------------------|---------------|
| Before Backend | Inside Application |
| Response Cache | Object/Data Cache |
| Managed by API Gateway | Managed by Application |
| Limited Configuration | Highly Flexible |

Many production systems use both.

---

# Real-World Example

An e-commerce platform.

```text
Customer

↓

API Gateway Cache

↓

Product API

↓

Amazon DynamoDB
```

When a product price changes:

```text
Admin

↓

Update Product

↓

Flush Cache

↓

Customers

↓

Updated Price
```

Customers always receive current pricing.

---

# Best Practices

- Choose TTL values based on how frequently data changes.
- Cache only data that changes infrequently.
- Flush caches after major deployments when necessary.
- Use event-driven invalidation for critical business data.
- Monitor cache hit ratios using CloudWatch.
- Avoid very long TTLs for frequently updated resources.
- Consider cache warming for high-traffic APIs.

---

# Common Interview Questions

### What is cache invalidation?

Cache invalidation is the process of removing or refreshing cached responses so clients receive the latest backend data.

---

### Why is cache invalidation important?

Without cache invalidation, users may receive stale or outdated information even after the backend has been updated.

---

### What is the simplest cache invalidation strategy?

Using **Time To Live (TTL)**, where cached entries automatically expire after a configured duration.

---

### What happens after a cache flush?

All cached entries are removed. The next request results in a cache miss, causing API Gateway to retrieve fresh data from the backend.

---

### What is a cache stampede?

A cache stampede occurs when many requests simultaneously experience a cache miss after an entry expires, causing a sudden surge of backend requests.

---

# Key Takeaways

- Cache invalidation ensures API Gateway serves fresh data after backend updates.
- TTL provides automatic expiration, while manual and event-driven invalidation offer more immediate refreshes.
- Cache warming improves performance after deployments by pre-populating frequently accessed responses.
- Poor cache invalidation strategies can result in stale data or backend overload.
- Choosing the right invalidation strategy balances performance, cost, and data freshness.