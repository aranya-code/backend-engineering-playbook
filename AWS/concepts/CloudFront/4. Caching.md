# AWS CloudFront - Section 04: Caching

# What is Caching?

Caching is the process of storing copies of frequently requested content closer to users so that future requests can be served faster.

Instead of contacting the origin for every request:

```text
User
  |
Origin
```

CloudFront stores content at Edge Locations:

```text
User
  |
Edge Location
```

This significantly reduces latency and origin traffic.

---

# Why Caching Matters

Without caching:

```text
100,000 Users
      |
      v
    Origin
```

Every request reaches the backend.

Problems:

- High latency
- Increased infrastructure cost
- Higher origin load
- Reduced scalability

---

With caching:

```text
100,000 Users
      |
      v
CloudFront Cache
      |
      v
Origin (few requests)
```

Benefits:

- Faster delivery
- Lower costs
- Reduced backend load
- Better user experience

---

# CloudFront Caching Workflow

Request Flow:

```text
User
  |
Edge Location
  |
Object Available?
  |
  +--> Yes --> Return Object
  |
  +--> No --> Origin
```

CloudFront first checks cache before contacting the origin.

---

# Cache Hit

## Definition

A Cache Hit occurs when the requested object is already available in the Edge Location cache.

---

## Flow

```text
User
  |
Edge Location
  |
Object Found
  |
Response Returned
```

Origin is NOT contacted.

---

## Example

User requests:

```text
/logo.png
```

Object already exists in cache.

CloudFront immediately serves:

```text
/logo.png
```

from the nearest Edge Location.

---

## Benefits

### Lower Latency

Content served closer to users.

---

### Reduced Origin Load

No backend request required.

---

### Lower AWS Costs

Fewer origin requests.

---

### Better Scalability

Supports millions of requests.

---

# Cache Miss

## Definition

A Cache Miss occurs when the requested object does not exist in cache.

---

## Flow

```text
User
  |
Edge Location
  |
Object Missing
  |
Regional Edge Cache
  |
Origin
```

---

## Detailed Process

Step 1:

User requests:

```text
/logo.png
```

---

Step 2:

Edge Location checks cache.

Object not found.

---

Step 3:

Regional Edge Cache checked.

Object not found.

---

Step 4:

Request sent to origin.

---

Step 5:

Origin returns object.

---

Step 6:

CloudFront stores object in cache.

---

Step 7:

Response returned.

---

# Cache Hit vs Cache Miss

| Feature | Cache Hit | Cache Miss |
|----------|------------|------------|
| Origin Contacted | No | Yes |
| Latency | Low | Higher |
| Cost | Lower | Higher |
| Performance | Better | Slower |

---

# What Gets Cached?

Common examples:

```text
Images
CSS
JavaScript
Fonts
Videos
PDF Files
```

Examples:

```text
logo.png
app.js
style.css
training.mp4
```

---

# Dynamic Content Caching

CloudFront can cache dynamic content.

Examples:

```text
API Responses
Generated Pages
Product Catalogs
```

Caching strategy must be carefully designed.

---

# Time To Live (TTL)

## What is TTL?

TTL (Time To Live) determines how long CloudFront keeps an object in cache.

Example:

```text
TTL = 3600
```

Object remains cached for:

```text
1 Hour
```

---

# TTL Types

CloudFront supports:

```text
Minimum TTL
Default TTL
Maximum TTL
```

---

## Minimum TTL

Smallest caching duration CloudFront allows.

Example:

```text
300 Seconds
```

CloudFront will cache for at least:

```text
5 Minutes
```

---

## Default TTL

Used when origin does not provide caching headers.

Example:

```text
86400 Seconds
```

CloudFront caches content for:

```text
24 Hours
```

---

## Maximum TTL

Maximum duration CloudFront can cache content.

Example:

```text
31536000 Seconds
```

CloudFront can cache content for:

```text
1 Year
```

---

# TTL Example

Suppose:

```text
logo.png
```

TTL:

```text
86400 Seconds
```

Timeline:

```text
9 AM
 |
Object Cached
 |
Next 24 Hours
 |
Served From Cache
 |
9 AM Next Day
 |
Revalidation
```

---

# Cache Expiration

When TTL expires:

```text
Object Not Immediately Deleted
```

CloudFront checks the origin.

If content changed:

```text
Cache Updated
```

If unchanged:

```text
Cache Retained
```

---

# Cache Control Headers

Origins can control CloudFront caching.

Common Headers:

```text
Cache-Control
Expires
ETag
Last-Modified
```

---

# Cache-Control Header

Example:

```http
Cache-Control: max-age=3600
```

Meaning:

```text
Cache for 1 Hour
```

---

# Expires Header

Example:

```http
Expires: Fri, 01 Jan 2027 00:00:00 GMT
```

Defines expiration date.

---

# ETag Header

Used for validation.

Example:

```http
ETag: "abc123"
```

CloudFront can verify whether content changed.

---

# Last-Modified Header

Example:

```http
Last-Modified:
Mon, 01 Jan 2026 10:00:00 GMT
```

Allows CloudFront to determine if updates occurred.

---

# Cache Invalidation

## What is Cache Invalidation?

Removing objects from cache before TTL expires.

---

## Why Needed?

Suppose:

```text
logo.png
```

was updated.

CloudFront still serves old version.

Need:

```text
Cache Invalidation
```

---

# Example

Invalidate:

```text
/logo.png
```

or

```text
/images/*
```

CloudFront removes cached objects.

Next request fetches updated content.

---

# Common Invalidation Patterns

Single Object:

```text
/logo.png
```

---

Entire Folder:

```text
/images/*
```

---

Entire Distribution:

```text
/*
```

Use carefully.

---

# Invalidation Cost Considerations

Frequent invalidations:

```text
Increase Costs
```

Better approach:

```text
Versioning
```

---

# Versioning Strategy

Instead of:

```text
logo.png
```

Use:

```text
logo-v2.png
```

Benefits:

- No invalidation required
- Better cache efficiency

---

# Cache Hit Ratio

## What is Cache Hit Ratio?

Percentage of requests served from cache.

Formula:

```text
(Cache Hits / Total Requests)
× 100
```

---

# Example

Requests:

```text
1000
```

Cache Hits:

```text
850
```

Calculation:

```text
(850 / 1000) × 100
```

Result:

```text
85%
```

---

# Why Cache Hit Ratio Matters

Higher ratio means:

- Better performance
- Lower latency
- Lower origin traffic
- Reduced costs

---

# Good Cache Hit Ratios

| Ratio | Evaluation |
|---------|-----------|
| Below 50% | Poor |
| 50% - 70% | Average |
| 70% - 90% | Good |
| Above 90% | Excellent |

---

# How to Improve Cache Hit Ratio

## Increase TTL

Longer caching period.

---

## Reduce Cache Key Complexity

Avoid unnecessary:

```text
Headers
Cookies
Query Strings
```

---

## Cache Static Assets Aggressively

Examples:

```text
Images
Fonts
CSS
JavaScript
```

---

## Use Versioning

Instead of frequent invalidations.

---

# Real-World Example

E-Commerce Website

Resources:

```text
logo.png
style.css
product.jpg
```

Traffic:

```text
500,000 Requests/Day
```

Without caching:

```text
500,000 Origin Requests
```

With caching:

```text
10,000 Origin Requests
490,000 Cache Hits
```

Benefits:

- Lower cost
- Better performance

---

# Common Caching Mistakes

## Very Low TTL

Example:

```text
TTL = 30 Seconds
```

Result:

- More cache misses
- More origin traffic

---

## Frequent Invalidations

Causes:

- Higher costs
- Reduced efficiency

---

## Caching Sensitive Data

Avoid caching:

```text
User Sessions
Private Information
Authentication Tokens
```

---

## Poor Cache Key Design

Including:

```text
User-Agent
Random Cookies
```

can dramatically reduce cache hit ratio.

---

# Troubleshooting Caching Issues

## Users Seeing Old Content

Possible Causes:

- TTL not expired
- Missing invalidation
- Browser cache

---

## Low Cache Hit Ratio

Possible Causes:

- Short TTL
- Large cache key
- Too many query strings

---

## High Origin Traffic

Possible Causes:

- Frequent cache misses
- Dynamic content
- Poor caching strategy

---

# Interview Questions

## Q1. What is a Cache Hit?

A request served directly from CloudFront cache without contacting the origin.

---

## Q2. What is a Cache Miss?

A request where CloudFront retrieves content from the origin because it is not available in cache.

---

## Q3. What is TTL?

Time To Live defines how long CloudFront stores an object in cache.

---

## Q4. Why is Cache Hit Ratio important?

It directly affects:

- Performance
- Cost
- Scalability
- Origin Load

---

## Q5. How do you improve Cache Hit Ratio?

- Increase TTL
- Optimize cache keys
- Reduce cookies
- Reduce headers
- Cache static content

---

## Q6. What is Cache Invalidation?

The process of removing cached objects before TTL expiration.

---

## Q7. Which is better: Invalidation or Versioning?

Versioning is generally preferred because it improves cache efficiency and reduces invalidation costs.

---

# Summary

Key Takeaways:

- CloudFront caches content at Edge Locations.
- Cache Hits improve performance and reduce cost.
- Cache Misses retrieve content from origins.
- TTL controls cache duration.
- Cache Invalidation removes stale content.
- Versioning is often better than invalidation.
- Cache Hit Ratio is a critical performance metric.
- Efficient caching directly impacts user experience, scalability, and AWS costs.

