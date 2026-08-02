# API Caching

## Overview

API Caching is a feature of Amazon API Gateway that stores backend responses in memory so that repeated requests can be served directly from the cache instead of invoking the backend service.

Caching significantly reduces:

- Response latency
- Backend load
- Lambda invocations
- Database queries
- Infrastructure costs

API Gateway caching is especially useful for APIs that return frequently requested data that does not change often.

Examples include:

- Product catalogs
- Weather information
- Currency exchange rates
- Configuration data
- Public reference data

---

# Why API Caching?

Consider a Product API.

```text
Client

↓

API Gateway

↓

Lambda

↓

DynamoDB
```

If 10,000 users request the same product:

```text
10,000 Requests

↓

10,000 Lambda Invocations

↓

10,000 Database Reads
```

This is expensive and unnecessary.

With caching:

```text
10,000 Requests

↓

API Gateway Cache

↓

1 Backend Request
```

Most requests are served directly from memory.

---

# Architecture

```text
             Client

                │

                ▼

        Amazon API Gateway

                │

        API Cache Lookup

                │

     ┌──────────┴──────────┐

     ▼                     ▼

 Cache Hit           Cache Miss

     │                     │

     ▼                     ▼

 Cached Data        Backend Service

                           │

                           ▼

                    Store in Cache
```

---

# How API Caching Works

First request:

```text
Client

↓

API Gateway

↓

Backend

↓

Response

↓

Store in Cache
```

Subsequent requests:

```text
Client

↓

API Gateway

↓

Cache

↓

Response
```

The backend is skipped entirely.

---

# Cache Hit

A **Cache Hit** occurs when API Gateway finds the requested response in cache.

```text
Request

↓

Cache

↓

Found

↓

Immediate Response
```

Advantages:

- Very low latency
- No backend invocation
- Lower AWS cost

---

# Cache Miss

A **Cache Miss** occurs when the response is not found in cache.

```text
Request

↓

Cache

↓

Not Found

↓

Backend

↓

Store Response

↓

Return Response
```

Future requests become cache hits.

---

# Cache Lifecycle

```text
First Request

↓

Cache Miss

↓

Backend

↓

Store Response

↓

Cache Hit

↓

Cache Expiration

↓

Cache Miss Again
```

---

# Cache TTL (Time To Live)

Every cached response has a **TTL**.

Example:

```text
TTL

300 Seconds
```

After five minutes:

```text
Cache Entry

↓

Expires

↓

Removed

↓

Next Request

↓

Backend
```

---

# Cache Capacity

API Gateway uses a dedicated cache cluster.

Available cache sizes include:

```text
0.5 GB

1.6 GB

6.1 GB

13.5 GB

28.4 GB

58.2 GB

118 GB
```

Larger caches:

- Store more responses
- Reduce cache misses
- Increase cost

Choose the smallest size that meets performance requirements.

---

# Stage-Level Caching

Caching is enabled per stage.

Example:

```text
Development

↓

Caching Disabled

----------------------

Production

↓

Caching Enabled
```

Production environments typically benefit the most from caching.

---

# Method-Level Caching

Individual methods can override stage settings.

Example:

```text
GET /products

↓

Caching Enabled

---------------------

POST /orders

↓

Caching Disabled
```

Read-heavy APIs are ideal candidates for caching.

---

# Cache Key

API Gateway identifies cached responses using a **cache key**.

The cache key is typically based on:

- Request path
- Query parameters
- Headers (optional)

Example:

```text
/products?id=100
```

Different query parameters generate different cache entries.

---

# Example

Request:

```http
GET /products?id=101
```

Cache Entry:

```text
Key

/products?id=101

↓

Cached Response
```

Request:

```http
GET /products?id=102
```

Creates a separate cache entry.

---

# What Should Be Cached?

Good candidates:

- Product Catalog
- News Headlines
- Weather Data
- Exchange Rates
- Configuration Data
- Public Reference APIs

---

# What Should NOT Be Cached?

Avoid caching:

- Login APIs
- Payment APIs
- Order Creation
- User Profiles
- Frequently Updated Data
- Sensitive Information

These APIs require fresh data.

---

# API Caching vs CloudFront Caching

| API Gateway Cache | CloudFront Cache |
|-------------------|------------------|
| Inside API Gateway | Edge Locations |
| Dynamic API Responses | Static & Dynamic Content |
| Per Stage | Global CDN |
| Backend Optimization | Network Optimization |

They solve different performance problems.

---

# API Caching vs Redis

| API Gateway Cache | Redis |
|-------------------|-------|
| Managed by API Gateway | Separate Service |
| Caches API Responses | General-Purpose Cache |
| No Application Code | Requires Integration |
| Limited Configuration | Highly Flexible |

Redis is typically used by backend applications, while API Gateway caching operates before requests reach the backend.

---

# Benefits

## Reduced Latency

Responses are served directly from memory.

---

## Lower Backend Load

Lambda functions and databases receive fewer requests.

---

## Lower Cost

Reduced:

- Lambda Invocations
- DynamoDB Reads
- EC2 CPU Usage

---

## Improved Scalability

Backends can handle significantly more users.

---

# Limitations

API Gateway caching:

- Is available only for **REST APIs**
- Increases API Gateway cost
- Requires proper cache invalidation strategy
- Should not be used for rapidly changing data

HTTP APIs currently do not support API Gateway caching.

---

# Monitoring Cache Performance

Useful CloudWatch metrics:

- CacheHitCount
- CacheMissCount
- Latency
- IntegrationLatency

A healthy cache should have a high cache hit ratio.

---

# Real-World Example

An e-commerce application.

```text
Customers

↓

API Gateway

↓

Cache

↓

Product Lambda

↓

DynamoDB
```

Popular product pages are served directly from cache, dramatically reducing backend traffic during sales events.

---

# Best Practices

- Cache only GET requests whenever possible.
- Do not cache sensitive or personalized responses.
- Choose an appropriate TTL based on data freshness.
- Monitor CacheHitCount and CacheMissCount regularly.
- Enable caching only where it provides measurable benefits.
- Use cache invalidation after important data updates.
- Combine API Gateway caching with CloudFront for optimal performance.

---

# Common Interview Questions

### What is API Gateway Caching?

API Gateway Caching stores API responses in an in-memory cache so repeated requests can be served without invoking backend services.

---

### What is the difference between a Cache Hit and a Cache Miss?

A **Cache Hit** occurs when the requested response is found in cache.

A **Cache Miss** occurs when API Gateway must invoke the backend because the response is not cached.

---

### Can POST requests be cached?

Although caching can technically be configured in some scenarios, it is generally recommended to cache only **GET** requests because POST operations usually modify data.

---

### Is API Gateway Caching available for HTTP APIs?

No.

API Gateway caching is currently supported only for **REST APIs**.

---

### What CloudWatch metrics are used to monitor caching?

Common metrics include:

- CacheHitCount
- CacheMissCount
- Latency
- IntegrationLatency

---

# Key Takeaways

- API Gateway Caching stores API responses in memory to reduce backend invocations and improve response times.
- Cache Hits provide low-latency responses, while Cache Misses invoke backend services and populate the cache.
- Caching is configured at the stage level and can be overridden at the method level.
- API Gateway caching is best suited for read-heavy APIs with relatively stable data.
- Proper TTL configuration, monitoring, and cache invalidation are essential for maintaining both performance and data freshness.