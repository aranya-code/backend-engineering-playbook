# 08- Low Cache Hit Ratio

## Overview

A low CloudFront cache hit ratio means a large proportion of requests are being forwarded to the origin instead of being served from CloudFront edge caches.

For cacheable workloads, this can increase:

- Origin request volume
- Application CPU utilization
- Database load
- Network transfer
- Response latency
- Infrastructure cost
- Risk of origin overload during traffic spikes

The important distinction is that **a low cache hit ratio is not automatically a problem**. Highly dynamic, authenticated, or personalized APIs may intentionally have little or no caching. The correct target depends on the workload and response correctness requirements.

A useful production investigation starts with:

```text
Is this response supposed to be cached?
                │
        ┌───────┴────────┐
        │                │
       YES               NO
        │                │
        ▼                ▼
Why is it missing?    Is origin capacity
                      sufficient?
```

For a cacheable object, the objective is to maximize useful cache reuse without serving stale or incorrect data.

## What the Cache Hit Ratio Represents

Conceptually:

```text
Cache Hit Ratio =
    Cache Hits
    ----------------------------
    Cache Hits + Cache Misses
```

Example:

```text
Requests       = 1,000,000
Cache Hits     =   900,000
Cache Misses   =   100,000

Hit Ratio      = 90%
```

A 90% hit ratio means approximately 90% of requests were satisfied by cached content, while approximately 10% required an origin request.

CloudFront metrics should be interpreted in context. A distribution serving mostly dynamic API requests can legitimately have a low hit ratio, while a static asset distribution should generally have much stronger cache reuse.

## Why Cache Hit Ratio Matters

Consider an application receiving 100,000 requests:

```text
Scenario A

100,000 requests
     │
     ├── 95,000 CloudFront hits
     │
     └──  5,000 origin requests
```

The origin processes only a small fraction of the total traffic.

Now compare:

```text
Scenario B

100,000 requests
     │
     ├── 40,000 CloudFront hits
     │
     └── 60,000 origin requests
```

The application and its dependencies now process 12 times as many origin requests.

This can create a cascading effect:

```text
Low cache hit ratio
        ↓
More origin requests
        ↓
Higher application load
        ↓
More database queries
        ↓
Higher latency
        ↓
More timeouts
        ↓
Potential retries
        ↓
Further origin load
```

Caching is therefore not only a latency optimization. It can also be a **capacity and reliability mechanism**.

## Appropriate Cacheable Workloads

CloudFront caching is generally most valuable for content that can safely be reused across requests.

Typical examples include:

| Workload | Typical caching suitability |
|---|---|
| JavaScript | Excellent |
| CSS | Excellent |
| Images | Excellent |
| Fonts | Excellent |
| Versioned static assets | Excellent |
| Public documentation | High |
| Public API responses | Potentially high |
| Product catalog data | Potentially high |
| Personalized API responses | Usually low |
| Authenticated user profile | Usually low |
| Payment status | Usually not appropriate |
| Private financial data | Usually not appropriate |
| Real-time data | Usually low |

The key criterion is not whether something is an API or a static file. The key question is:

> Can the same response safely be served to multiple requests for the configured freshness period?

## Request Lifecycle

For a cache hit:

```mermaid
sequenceDiagram
    participant Client
    participant CF as CloudFront Edge
    participant Cache as Edge Cache

    Client->>CF: GET /static/app.js
    CF->>Cache: Lookup cache key
    Cache-->>CF: Cached object
    CF-->>Client: HTTP 200
```

For a cache miss:

```mermaid
sequenceDiagram
    participant Client
    participant CF as CloudFront
    participant Cache as Edge Cache
    participant Origin

    Client->>CF: GET /static/app.js
    CF->>Cache: Lookup cache key
    Cache-->>CF: MISS
    CF->>Origin: Fetch object
    Origin-->>CF: HTTP response
    CF->>Cache: Store eligible response
    CF-->>Client: HTTP response
```

A low hit ratio means the second path is occurring more frequently than expected.

## First Question: Should This Content Be Cached?

Before changing CloudFront configuration, classify the response.

### Good Candidate

```text
GET /static/app.7f91c2.js
```

The filename contains a content/version identifier. Once published, the object can often be cached for a long period.

### Poor Candidate

```text
GET /api/users/me
```

The response depends on the authenticated user and generally should not be shared through a normal public cache.

### Potentially Cacheable

```text
GET /api/products?category=books
```

If the response is public and acceptable to serve for a defined freshness period, CloudFront caching may be appropriate.

The architecture must explicitly define the freshness and correctness requirements.

## Inspect the Distribution Configuration

Retrieve the distribution:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

Retrieve its configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID"
```

Inspect:

- Cache behaviors
- Path patterns
- Cache policies
- Origin request policies
- Origin configuration
- Viewer protocol policy
- Allowed methods
- Compression
- TTL configuration
- Query-string behavior
- Cookie behavior
- Header behavior

A common production mistake is changing the origin when the actual problem is an overly fragmented cache key.

## Cache Policy and Cache Key

The cache key determines which requests are considered equivalent for caching.

Conceptually:

```text
Cache Key =
    URL path
  + selected query strings
  + selected headers
  + selected cookies
```

For example, if the cache key contains:

```text
/path
?user_id
?timestamp
Accept-Language
Cookie
```

then two requests for the same logical resource may produce different cache keys.

That reduces cache reuse.

The correct cache key should contain only request attributes that can change the response.

## Cache Key Fragmentation

Suppose the application exposes:

```text
GET /products/100
```

If the cache policy unnecessarily includes a user identifier:

```text
/products/100?user_id=101
/products/100?user_id=102
/products/100?user_id=103
```

CloudFront can treat these as separate cache entries even if the response is identical.

Instead, if the response does not depend on `user_id`, the cache key should not vary by it.

### Common Sources of Fragmentation

- Unnecessary query strings
- Tracking parameters
- Cookies
- Authorization-related headers
- `Accept-Language`
- Device-specific headers
- Arbitrary custom headers
- Per-user identifiers
- Timestamps
- Random request parameters

The solution is not to remove every variation blindly. Remove only dimensions that do not affect response correctness.

## Query String Parameters

Tracking parameters are a common source of cache fragmentation.

For example:

```text
https://cdn.example.com/app.js?utm_source=google
https://cdn.example.com/app.js?utm_source=email
https://cdn.example.com/app.js?utm_source=campaign
```

If the application returns exactly the same object regardless of `utm_source`, including it in the cache key creates unnecessary variants.

A good cache design separates:

```text
Parameters that affect content
```

from:

```text
Parameters used only for analytics
```

The former may need to participate in caching decisions. The latter generally should not.

## Cookies

Cookies can dramatically reduce cache reuse.

For example:

```text
Cookie: sessionid=abc123
```

If the cache policy varies by a session cookie, every user can effectively receive a separate cache variant.

This may be correct for personalized content but is usually undesirable for public assets.

Avoid forwarding or varying on cookies unless they are actually required by the origin behavior.

## Headers

Headers can also fragment the cache.

Examples include:

```text
Accept-Language
User-Agent
Authorization
X-Custom-Header
```

Only vary on headers that materially change the response.

A senior-level cache review asks:

> Does this request attribute affect the representation returned by the origin?

If the answer is no, it is a candidate for removal from the cache key.

## Authorization and Personalized Responses

Authentication is one of the most important cache-boundary considerations.

For example:

```text
GET /api/profile
Authorization: Bearer USER_A
```

must not accidentally become a cacheable response that is returned to:

```text
Authorization: Bearer USER_B
```

For authenticated or personalized content, caching must be designed around explicit authorization and privacy requirements.

In many architectures, authenticated APIs are deliberately configured to bypass CloudFront caching while static and public content remains highly cacheable.

## Cache-Control Headers

The origin can communicate caching behavior through HTTP cache headers.

Example:

```http
Cache-Control: public, max-age=86400
```

For immutable versioned assets:

```http
Cache-Control: public, max-age=31536000, immutable
```

For content that should not be stored:

```http
Cache-Control: no-store
```

For content requiring revalidation:

```http
Cache-Control: no-cache
```

These directives have different semantics and should not be treated as interchangeable.

### `no-cache` vs `no-store`

`no-cache` does **not** mean "never store."

It means cached content must be revalidated before reuse according to HTTP caching semantics.

`no-store` instructs caches not to store the response.

This distinction is important when diagnosing unexpectedly low cache reuse.

## TTL Configuration

A short TTL causes objects to become stale quickly and require additional origin validation or retrieval.

For example:

```text
TTL = 60 seconds
```

may be appropriate for rapidly changing public data.

But for a versioned static asset:

```text
/app.7f91c2.js
```

a much longer TTL is often preferable.

A useful pattern is:

```text
Immutable filename
        ↓
Long cache lifetime
        ↓
New deployment creates new filename
```

This avoids relying on frequent invalidations for every deployment.

## Versioned Static Assets

Content-addressed or versioned assets are one of the strongest CloudFront caching patterns.

Example:

```text
app.20260820.js
app.20260821.js
```

or:

```text
app.7f91c2.js
app.a821de.css
```

Deployment:

```text
Version N
  ↓
app.7f91c2.js

Version N+1
  ↓
app.83af12.js
```

The old object can remain cached while new clients request the new object.

This reduces the need for aggressive invalidation.

## Cache Invalidation and Hit Ratio

Frequent invalidations can reduce cache effectiveness.

For example:

```text
Deploy
  ↓
Invalidate /*
  ↓
All objects removed
  ↓
Traffic generates cache misses
  ↓
Origin receives large request spike
```

This can create a cache stampede-like load pattern after deployment.

Prefer versioned assets when possible.

Use invalidation for content that genuinely requires immediate removal or replacement.

## Cache Invalidation Commands

Create an invalidation:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/index.html"
```

Multiple paths:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/index.html" "/config.json"
```

Wildcard invalidation:

```bash
aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/static/*"
```

Avoid using:

```text
/*
```

as a routine deployment strategy unless there is a specific operational reason.

## Minimum TTL and Cacheability

A low minimum TTL can limit effective caching for objects that could otherwise be reused.

Review:

- Minimum TTL
- Default TTL
- Maximum TTL
- Origin `Cache-Control`
- Cache policy behavior

The effective caching behavior depends on the interaction between CloudFront configuration and origin response headers.

Do not optimize TTL values independently of the application's freshness requirements.

## Origin Response Headers

Inspect what the origin is actually returning:

```bash
curl -sS -D - \
  -o /dev/null \
  https://origin.example.com/static/app.js
```

Look for:

```http
Cache-Control: ...
ETag: ...
Last-Modified: ...
Expires: ...
Age: ...
```

If the origin consistently returns restrictive caching directives, changing unrelated CloudFront settings may not solve the underlying issue.

## Error Responses

Repeated origin errors can also produce unexpected cache behavior.

Examples:

```text
200 → cacheable
404 → potentially cacheable according to configuration
500 → potentially handled according to error caching configuration
```

Error caching should be reviewed carefully.

An incorrectly cached error can cause valid content to remain unavailable after the underlying problem has been fixed.

## Cacheable API Design

Public APIs can sometimes benefit from CloudFront caching.

Example:

```text
GET /api/products/100
```

If the product response is public and can tolerate a short freshness window:

```http
Cache-Control: public, max-age=60
```

This can reduce origin load.

The tradeoff is consistency:

```text
Database updated
       ↓
Origin returns new value
       ↓
CloudFront may still serve old cached value
```

The business requirement must determine whether that staleness is acceptable.

## Dynamic API Caching

Dynamic APIs require careful cache design.

Consider:

```text
GET /api/catalog?category=books&page=1
```

Potential cache key:

```text
/path + category + page
```

Avoid unnecessarily adding:

```text
session cookie
user ID
tracking parameters
unrelated headers
```

If the response is public and deterministic for the selected parameters, this can produce substantial cache reuse.

## Cache Hit Ratio by Path

A global hit ratio can hide problematic behaviors.

For example:

```text
/static/*      99%
/images/*      98%
/api/catalog   92%
/api/profile    0%
```

The global number may be misleading because different paths have different caching requirements.

Investigate cache performance by:

- Path
- Distribution behavior
- Region
- Object type
- Query pattern
- Response status
- Application workload

## Cache Hit Ratio by Geography

A global cache hit ratio can also hide geographic differences.

For example:

```text
North America    96%
Europe           94%
Asia             70%
South America    92%
```

Possible causes include:

- Different traffic patterns
- Different object popularity
- Recently deployed content
- Regional traffic volume
- Low request volume for specific objects
- Cache warming behavior

Do not assume geographic variation automatically indicates a CloudFront failure.

## Cache Warming

A newly deployed object starts without a populated cache at an edge location.

```text
Deployment
    ↓
New object
    ↓
First request
    ↓
Cache MISS
    ↓
Origin fetch
    ↓
Object cached
    ↓
Subsequent requests → HIT
```

Low-volume objects may continue to experience misses because there are not enough requests to justify keeping them resident at every edge location.

This is not necessarily a problem.

The important metric is whether cache misses are generating unacceptable origin load or latency.

## Cache Eviction

A cached object is not guaranteed to remain in an edge cache forever.

CloudFront may remove objects from cache based on caching behavior and edge-cache resource management.

Therefore:

> A long TTL does not mean an object will physically remain in every edge cache for the entire TTL.

Longer TTLs primarily allow an object to remain valid for longer when it is cached.

## Request Frequency and Object Popularity

A high hit ratio depends partly on traffic distribution.

Consider:

```text
1,000,000 requests
    │
    ├── 900,000 → app.js
    └── 100,000 → 100,000 unique objects
```

`app.js` can have excellent cache reuse while the long tail of unique objects naturally produces many misses.

Do not judge cache effectiveness without understanding object popularity.

## Large Number of Unique URLs

An application that generates unique URLs for logically identical content can destroy cache reuse.

Example:

```text
/image?request_id=10001
/image?request_id=10002
/image?request_id=10003
```

If `request_id` does not affect the image, these URLs are unnecessarily unique from a caching perspective.

Normalize URL design where possible.

## Trailing Slashes and URL Variants

Different URL representations can create separate cache entries:

```text
/products
/products/
```

Similarly:

```text
/image.jpg
/image.jpg?x=1
```

may represent different cache keys.

Applications should establish consistent URL conventions.

## Compression and Cache Reuse

Compression can improve transfer performance, but cache behavior must remain correct.

For example:

```text
Client A → accepts gzip
Client B → accepts gzip
Client C → accepts brotli
```

The caching system must correctly account for content negotiation where it affects the representation.

Do not introduce unnecessary variation in cache keys merely because multiple clients send different headers.

## Backend Architecture Example

A typical production architecture may look like:

```mermaid
flowchart LR
    Client --> CF[CloudFront]
    CF -->|Cache HIT| Client
    CF -->|Cache MISS| ALB[Application Load Balancer]
    ALB --> Nginx[Nginx]
    Nginx --> App[Django / FastAPI]
    App --> Redis[Redis]
    App --> DB[(PostgreSQL)]
```

The desired behavior for static content is:

```text
Client
  ↓
CloudFront
  ↓
HIT
  ↓
Client
```

The desired behavior for dynamic personalized APIs may be:

```text
Client
  ↓
CloudFront
  ↓
Origin
  ↓
Application
```

Caching should be applied selectively rather than uniformly.

## Monitoring

Monitor cache performance alongside origin health.

Useful signals include:

| Signal | Why it matters |
|---|---|
| Cache hit ratio | Measures cache reuse |
| Origin request count | Shows pressure reaching origin |
| Origin latency | Shows cost of misses |
| CloudFront error rate | Detects delivery failures |
| Request count | Provides traffic context |
| Bytes transferred | Helps evaluate bandwidth |
| Cacheable response ratio | Distinguishes intentional misses |
| Application latency | Shows downstream impact |
| Database load | Detects indirect cache impact |

A useful relationship is:

```text
Cache Hit Ratio ↓
        │
        ▼
Origin Requests ↑
        │
        ▼
Application Load ↑
        │
        ▼
Database Load ↑
        │
        ▼
Latency ↑
```

## Operational Troubleshooting Workflow

### Establish the Baseline

Determine:

- Current cache hit ratio
- Current origin request count
- Current origin latency
- Current traffic volume
- Affected paths
- Affected regions
- Time when the change started

### Identify Affected Behaviors

Inspect CloudFront distribution behavior configuration:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID"
```

Determine which path patterns are affected.

### Inspect Response Headers

```bash
curl -sS -D - \
  -o /dev/null \
  https://cdn.example.com/static/app.js
```

Check:

```text
Cache-Control
ETag
Last-Modified
Age
X-Cache
```

### Compare Equivalent Requests

Test requests that should logically map to the same object:

```text
/static/app.js
/static/app.js?utm_source=email
/static/app.js?utm_source=google
```

If they produce separate cache variants, investigate the cache policy.

### Inspect Query Parameters

Determine which query strings actually affect the response.

### Inspect Cookies and Headers

Identify whether unnecessary cookies or headers are participating in cache variation.

### Review TTLs

Check:

- Minimum TTL
- Default TTL
- Maximum TTL
- Origin cache-control headers

### Review Recent Changes

Look for:

- CloudFront policy changes
- Application deployments
- Cache policy changes
- Origin header changes
- URL changes
- Cookie changes
- Query-string changes
- Invalidation changes

### Measure Origin Impact

Determine whether the low hit ratio is causing:

- Higher CPU
- Higher database utilization
- Higher latency
- More connection contention
- Increased cost

### Validate the Fix

After changing the cache configuration, measure:

```text
Before:
Hit ratio      = 62%
Origin requests = 380k/min
P95 latency    = 900 ms

After:
Hit ratio      = 94%
Origin requests = 60k/min
P95 latency    = 240 ms
```

A successful optimization should improve both cache behavior and the downstream system where cache reduction was expected to matter.

## Common Production Pitfalls

### Treating Every Low Hit Ratio as a Bug

Authenticated APIs may intentionally have a low hit ratio.

**Avoid it:** define expected caching behavior per workload.

### Caching Personalized Responses

This can create severe security and privacy problems.

**Avoid it:** never allow shared caching unless the response is safe to reuse across the intended audience.

### Including Every Query Parameter

This fragments the cache.

**Avoid it:** include only response-affecting parameters in the cache key.

### Forwarding All Cookies

Session cookies can effectively create per-user cache variants.

**Avoid it:** forward cookies only when required.

### Forwarding All Headers

Unnecessary header variation can reduce cache reuse.

**Avoid it:** vary on headers only when they affect the representation.

### Using Very Short TTLs Everywhere

Short TTLs increase origin traffic.

**Avoid it:** choose TTLs according to freshness requirements.

### Invalidating Everything After Every Deployment

Global invalidations can cause large waves of cache misses.

**Avoid it:** use versioned assets and targeted invalidations.

### Ignoring Origin Cache-Control

The origin may explicitly communicate restrictive caching behavior.

**Avoid it:** inspect actual response headers before changing CloudFront configuration.

### Optimizing Hit Ratio Without Considering Correctness

A 99% hit ratio is not useful if clients receive stale or incorrect data.

**Avoid it:** optimize for **correct cache reuse**, not the highest possible percentage.

### Looking Only at Global Metrics

A global hit ratio can hide one problematic path.

**Avoid it:** segment metrics by behavior, path, workload, and geography where possible.

## Security Considerations

Cache configuration is part of the application's security boundary.

Pay particular attention to:

- Authorization headers
- Session cookies
- Personalized responses
- Private user data
- Signed URLs
- Signed cookies
- Origin access controls
- Sensitive API responses

A cache misconfiguration can turn a performance optimization into a data-isolation vulnerability.

Before caching an API response, verify:

```text
Is the response public?
        │
        ├── NO → Do not use shared caching without
        │         an explicit secure design.
        │
        └── YES
             │
             ▼
Does the response vary by request attributes?
             │
             ├── YES → Include required attributes
             │         in the cache key.
             │
             └── NO → Shared caching may be appropriate.
```

## Scalability Considerations

A healthy cache absorbs repeated requests before they reach the origin.

```text
10,000 requests
      │
      ▼
CloudFront
      │
      ├── 9,500 HIT ──────► Clients
      │
      └──   500 MISS
              │
              ▼
            Origin
```

This protects:

- Application workers
- Database connections
- Database CPU
- Redis
- External APIs
- Network capacity

As traffic grows, cache efficiency becomes increasingly important for workloads that are naturally cacheable.

## Reliability Considerations

Caching can reduce the blast radius of an origin degradation for content that is already cached.

For example:

```text
Origin degraded
     │
     ├── Cached objects → Continue serving when eligible
     │
     └── Cache misses   → Depend on origin health
```

Caching is not a substitute for highly available origins, but it can reduce origin dependency for suitable workloads.

Design TTL and stale-content behavior according to business requirements rather than treating caching solely as a performance feature.

## Cost Considerations

A low cache hit ratio can increase:

- Origin compute consumption
- Database workload
- Load-balancer usage
- Network transfer
- External service calls

Improving cache reuse can therefore reduce infrastructure costs.

However, cache optimization should not be driven by cost alone. A cache policy that introduces stale or incorrect responses can create significantly greater operational and business costs.

## Interview Perspective

A strong answer to:

> "CloudFront cache hit ratio dropped from 95% to 50%. How would you investigate?"

should proceed systematically:

1. Determine which workloads are expected to be cacheable.
2. Identify when the hit ratio changed.
3. Identify affected cache behaviors and paths.
4. Inspect cache policies.
5. Inspect query-string configuration.
6. Inspect cookie configuration.
7. Inspect header variation.
8. Inspect origin `Cache-Control` headers.
9. Check TTL changes.
10. Check recent deployments and invalidations.
11. Compare equivalent requests and cache keys.
12. Measure resulting origin request volume.
13. Determine whether origin latency or capacity is being affected.
14. Validate the fix with hit ratio, origin load, latency, and correctness metrics.

The senior-level insight is:

> **Do not optimize the cache hit ratio in isolation. Optimize cache reuse while preserving response correctness and the application's freshness requirements.**

## Key Takeaways

- **A low cache hit ratio is not inherently bad:** first determine whether the affected workload is actually intended to be cached.
- **Cache-key design is critical:** unnecessary query strings, cookies, headers, and user-specific attributes can fragment the cache and increase origin traffic.
- **Use appropriate TTLs and versioned assets:** long-lived immutable assets reduce origin load and minimize the need for broad invalidations.
- **Correctness and security come first:** never trade response correctness, freshness, or user isolation for a higher cache hit ratio.
- **Measure downstream impact:** correlate cache hit ratio with origin requests, application latency, database load, and infrastructure cost to determine whether optimization is actually valuable.