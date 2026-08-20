# 03- Caching and Policy Questions

## Overview

CloudFront caching and policy configuration is one of the most important areas for backend-focused CloudFront interviews. A strong answer must go beyond defining a cache policy and explain how request attributes, cache keys, TTLs, origin forwarding, and response headers interact.

The central engineering problem is:

> How do you maximize cache reuse without serving stale, incorrect, or user-specific content to the wrong client?

A useful mental model is:

```text
Viewer Request
      │
      ▼
CloudFront Behavior
      │
      ├── Cache Policy
      │      └── Determines cache key
      │
      ├── Origin Request Policy
      │      └── Determines additional origin-bound request data
      │
      ▼
Cache Lookup
      │
      ├── HIT ───────────────► Response
      │
      └── MISS
             │
             ▼
           Origin
             │
             ▼
       Origin Response
             │
             ├── Cacheable ──► Store
             │
             └── Not cacheable
             │
             ▼
           Viewer
```

The most important distinction is between **what makes two requests different for caching** and **what information the origin needs to process the request**.

---

## Cache Fundamentals

### What is CloudFront caching?

**Answer:**

CloudFront caching stores eligible origin responses at CloudFront edge locations so subsequent requests can be served without contacting the origin.

For a cache hit:

```text
Client
  │
  ▼
CloudFront Edge
  │
  └── Cached Object
        │
        ▼
      Client
```

For a cache miss:

```text
Client
  │
  ▼
CloudFront Edge
  │
  ▼
Origin
  │
  ▼
CloudFront
  │
  ├── Cache response if eligible
  │
  ▼
Client
```

Caching reduces:

- Origin request volume.
- Application CPU usage.
- Database pressure.
- Network traffic to the origin.
- Response latency for cacheable content.

---

### What is a cache hit?

**Answer:**

A cache hit occurs when CloudFront finds a valid cached object for the request's cache key and can serve it without retrieving the object from the origin.

A high cache hit ratio generally indicates that requests are effectively reusing cached objects.

However, a high hit ratio is useful only when the cached representation is correct.

---

### What is a cache miss?

**Answer:**

A cache miss means CloudFront does not have a usable cached object corresponding to the request.

The origin may then be contacted to retrieve the response.

A miss is not an error. It is a normal part of cache operation, particularly:

- During initial traffic.
- After content expiration.
- After cache invalidation.
- When requests contain many cache-key variations.
- When content is intentionally not cached.

---

### What is cache hit ratio?

**Answer:**

Cache hit ratio represents how effectively CloudFront satisfies requests from its cache rather than retrieving objects from the origin.

Conceptually:

```text
Cache Hit Ratio =
Cache Hits / (Cache Hits + Cache Misses)
```

A low cache hit ratio can indicate:

- Poor cache-key design.
- Excessive query-string variation.
- Excessive cookie variation.
- Excessive header variation.
- Short TTLs.
- Dynamic content.
- Frequent invalidations.

A high cache hit ratio is not automatically good. If the cache key is too broad, unrelated requests may incorrectly share a cached response.

---

## Cache Keys

### What is a CloudFront cache key?

**Answer:**

A cache key identifies the request variation for which CloudFront stores and retrieves a cached response.

Conceptually:

```text
Cache Key =
Path
+
Selected Query Strings
+
Selected Headers
+
Selected Cookies
```

The exact components depend on the configured cache policy.

For example:

```text
/products/100
```

might produce one cache entry.

If the response varies by:

```text
?currency=USD
```

and the query string is part of the cache key:

```text
/products/100?currency=USD
/products/100?currency=EUR
```

represent different cached variants.

---

### Why is cache-key design important?

**Answer:**

Because the cache key controls both **correctness** and **cache efficiency**.

If the key omits a request attribute that changes the response:

```text
Different representations
        ↓
Same cache key
        ↓
Incorrect cache sharing
```

If the key includes unnecessary attributes:

```text
Same representation
        ↓
Different cache keys
        ↓
Cache fragmentation
        ↓
Lower hit ratio
```

Therefore, the correct cache key contains the minimum set of request attributes required to distinguish different representations.

---

### Give an example of a dangerous cache key.

**Answer:**

Suppose:

```http
GET /api/profile
Authorization: Bearer user-A-token
```

returns User A's profile.

If the authorization context affects the response but is not properly handled by the caching design, CloudFront could potentially reuse a cached response across requests that should receive different representations.

This is why personalized API responses should generally not be blindly placed into a shared CDN cache.

The design must explicitly account for:

- Authentication.
- Authorization.
- User identity.
- Cache-key semantics.
- Response sharing.
- Data sensitivity.

---

### Give an example of an unnecessarily large cache key.

**Answer:**

Suppose a response depends only on:

```text
/products/100
```

but the cache key also varies on:

```text
X-Request-ID
User-Agent
Session Cookie
Tracking Cookie
```

Then requests that are semantically identical can generate many cache variants.

```text
Request A → variant A
Request B → variant B
Request C → variant C
...
```

This reduces cache reuse and increases origin traffic.

---

## Cache Policy

### What is a CloudFront cache policy?

**Answer:**

A cache policy controls CloudFront caching behavior, including:

- TTL configuration.
- Which query strings are included in the cache key.
- Which headers are included in the cache key.
- Which cookies are included in the cache key.

The key question is:

> What request attributes determine whether two requests can safely share the same cached response?

---

### Why were cache policies introduced?

**Answer:**

Cache policies provide a reusable, explicit way to define caching behavior rather than relying on scattered configuration decisions.

They make caching behavior easier to:

- Standardize.
- Review.
- Reuse.
- Audit.
- Deploy through infrastructure as code.
- Reason about during incidents.

---

### What should you consider when creating a cache policy?

**Answer:**

Start with response semantics rather than infrastructure preferences.

Determine:

1. Is the response publicly shareable?
2. Which request attributes change the representation?
3. How fresh must the response be?
4. Can stale data be tolerated?
5. Is authentication involved?
6. Is personalization involved?
7. Does the origin require additional request information?

Then design the cache policy around those requirements.

---

### What is the difference between including a query string in the cache key and forwarding it to the origin?

**Answer:**

These are separate concerns.

Including a query string in the cache key means:

> This query-string value makes cached responses different.

Forwarding a query string means:

> The origin should receive this query-string value.

A query string may be needed by the origin without necessarily needing to create a unique cache variant, although doing that safely requires knowing that the value does not change the response.

---

### Should all query strings be included in the cache key?

**Answer:**

No.

Only query strings that affect the representation should normally participate in the cache key.

For example:

```text
/products?category=books
```

may need `category` in the cache key if it changes the response.

But:

```text
/products?utm_source=campaign
```

may not change the response at all.

Including tracking parameters unnecessarily can fragment the cache.

A better strategy is to distinguish:

```text
Representation-affecting parameters
```

from:

```text
Non-functional tracking parameters
```

---

### What happens if you exclude a representation-changing query parameter?

**Answer:**

Requests with different intended representations can map to the same cache key.

For example:

```text
/products?currency=USD
/products?currency=EUR
```

If `currency` changes the returned representation but is excluded from the cache key, CloudFront may treat the requests as equivalent.

This can result in incorrect content being served.

The rule is:

> If a request attribute changes the representation, it must be accounted for in the caching design.

---

## Origin Request Policy

### What is an origin request policy?

**Answer:**

An origin request policy determines additional request information that CloudFront forwards to the origin.

It is intentionally separate from the cache policy.

The distinction can be represented as:

```text
Cache Policy
     │
     └── What makes cache entries different?

Origin Request Policy
     │
     └── What additional information does the origin receive?
```

This separation allows the origin to receive information without automatically making every piece of that information part of the cache key.

---

### Why is separating cache keys from origin forwarding useful?

**Answer:**

Because the origin may need request information that does not necessarily change the response.

For example, an origin may need a header for operational or routing purposes while the returned representation remains identical.

Separating the two concerns prevents unnecessary cache fragmentation.

However, this must be used carefully.

If an origin input changes the response but is excluded from the cache key, caching can become incorrect.

---

### Give a practical example.

**Answer:**

Suppose an application receives:

```http
GET /products/100
X-Client-Version: 5
```

If the application uses the header only for logging and the response is identical regardless of its value:

```text
X-Client-Version
     │
     ├── Forward to origin
     │
     └── Not necessarily part of cache key
```

But if:

```text
X-Client-Version: 5
```

causes the backend to return a different representation from:

```text
X-Client-Version: 6
```

then the cache design must distinguish those variants.

---

## Cache Policy vs Origin Request Policy

### What is the difference between the two?

| Concern | Cache Policy | Origin Request Policy |
|---|---|---|
| Controls cache key | Yes | No |
| Controls TTL | Yes | No |
| Controls query-string cache variation | Yes | No |
| Controls header cache variation | Yes | No |
| Controls cookie cache variation | Yes | No |
| Controls additional origin forwarding | No | Yes |
| Primary concern | Cache correctness and reuse | Origin request requirements |

A useful interview phrase is:

> The cache policy determines how CloudFront identifies cached representations; the origin request policy determines additional request data sent to the origin.

---

## TTL

### What is TTL?

**Answer:**

TTL controls how long an object can remain fresh in CloudFront's cache according to the configured caching behavior.

TTL configuration commonly involves:

- Minimum TTL.
- Default TTL.
- Maximum TTL.

Origin response headers such as `Cache-Control` can also influence caching behavior according to the configured policy.

---

### How should TTL be chosen?

**Answer:**

TTL should be based on how frequently content changes and how much staleness the application can tolerate.

Example strategy:

| Content | Example strategy |
|---|---|
| Content-hashed JS/CSS | Very long TTL |
| Versioned images | Long TTL |
| Public product catalog | Moderate TTL |
| Frequently changing public API | Short TTL |
| User-specific API | Usually no shared caching |
| Security-sensitive state | Avoid shared caching unless explicitly designed |

The key principle is:

> TTL is a business and correctness decision as much as a performance decision.

---

### Why are content-hashed assets ideal for long TTLs?

**Answer:**

Because a content-hashed filename changes when the content changes.

For example:

```text
app.a83f92.js
```

can safely have a long cache lifetime.

When the application changes:

```text
app.b72e31.js
```

becomes a new cache key.

This avoids depending on aggressive invalidation for normal deployments.

---

### What is the difference between TTL expiration and invalidation?

**Answer:**

TTL expiration allows cached content to become stale according to normal cache lifetime rules.

Invalidation explicitly requests removal of selected objects before normal expiration.

```text
TTL:
Object → remains cached → expires naturally

Invalidation:
Object → explicit invalidation → removed before normal expiration
```

Invalidation is useful for exceptional situations, but versioned assets are usually a better long-term deployment strategy.

---

## HTTP Cache-Control

### How does `Cache-Control` affect CloudFront caching?

**Answer:**

The origin can communicate caching instructions using HTTP response headers such as:

```http
Cache-Control: public, max-age=3600
```

CloudFront's configured cache policy determines how these origin caching directives interact with CloudFront's TTL behavior.

A backend should therefore treat caching as a cross-layer concern:

```text
Application
    │
    └── Cache-Control
           │
           ▼
       CloudFront
           │
           └── Cache Policy + TTL configuration
```

---

### What is the difference between `public` and `private`?

**Answer:**

Conceptually:

```http
Cache-Control: public
```

indicates that a response can be stored by shared caches when other caching requirements permit it.

```http
Cache-Control: private
```

indicates that the response is intended for a private cache and should not be stored by shared caches.

This distinction is especially important for APIs containing user-specific data.

---

### Why is `Cache-Control: no-store` important for sensitive responses?

**Answer:**

`no-store` indicates that the response should not be stored by caches.

It is useful for responses containing highly sensitive or non-cacheable information.

Examples can include:

- Payment details.
- Authentication responses.
- Highly sensitive account data.

The correct caching strategy should be determined by application semantics rather than by assuming all API responses should be cacheable.

---

## Cookies

### How do cookies affect CloudFront caching?

**Answer:**

Cookies can affect cache variation when configured as part of the cache key.

This is particularly important because applications frequently use cookies for:

- Sessions.
- Authentication.
- Personalization.
- Feature flags.
- Tracking.

If every cookie is included in the cache key, cache fragmentation can become severe.

---

### Why is forwarding session cookies dangerous?

**Answer:**

A session cookie commonly identifies a specific user.

If a response is cached and the cache strategy does not correctly isolate user-specific representations, a shared cache can create a serious security vulnerability.

For example:

```text
User A
  │
  ├── Session A
  ▼
CloudFront
  │
  ▼
Cached User A response
```

If User B can later retrieve that cached response through the same cache key, private information can leak.

The safest approach is generally to avoid shared caching for personalized responses unless the cache isolation model is explicitly designed and verified.

---

## Headers

### Should all headers be included in the cache key?

**Answer:**

No.

Only headers that affect the returned representation should normally participate in the cache key.

Potentially dangerous examples of unnecessary variation include:

- `User-Agent`.
- Request IDs.
- Tracing headers.
- Observability headers.
- Random correlation values.

If these do not affect the response, they should not fragment the cache.

---

### What about the `Authorization` header?

**Answer:**

`Authorization` requires careful handling.

If the response depends on authenticated identity or authorization state, blindly caching the response as a shared object can be unsafe.

For example:

```http
Authorization: Bearer token-A
```

and:

```http
Authorization: Bearer token-B
```

may produce completely different responses.

A common production strategy is to avoid shared caching for personalized authenticated endpoints unless there is a well-defined and tested cache isolation model.

---

## Cacheable vs Non-Cacheable APIs

### Which API endpoints are good CloudFront caching candidates?

**Answer:**

Good candidates generally have these properties:

- Responses are publicly shareable.
- Data changes relatively infrequently.
- The same representation can be safely served to many clients.
- Stale data has an acceptable bounded impact.
- Cache invalidation or TTL behavior is understood.

Examples:

```text
GET /products
GET /categories
GET /public/config
GET /documentation
```

Potentially poor candidates:

```text
GET /me
GET /account
GET /orders
GET /payment-status
```

because responses are often user-specific or highly dynamic.

---

### Can a GET request still be unsafe to cache?

**Answer:**

Yes.

HTTP method alone does not determine whether a response is safe to share through a CDN.

For example:

```text
GET /account
```

is a GET request but may return highly personalized data.

The correct question is:

> Can this response safely be reused by another request with the same cache key?

---

## Query String Questions

### Why can query strings cause cache fragmentation?

**Answer:**

Consider:

```text
/products?utm_source=google
/products?utm_source=facebook
/products?utm_source=email
```

If `utm_source` is part of the cache key but does not affect the response, CloudFront can create separate cache variants.

This reduces reuse:

```text
One logical representation
        │
        ├── Cache A
        ├── Cache B
        ├── Cache C
        └── Cache D
```

The cache policy should avoid unnecessary variation.

---

### How should you handle tracking parameters?

**Answer:**

Determine whether the tracking parameter changes the representation.

If it does not:

```text
utm_source
utm_medium
utm_campaign
```

should generally not create independent cache variants.

However, request forwarding and cache-key configuration should be evaluated separately based on origin requirements.

---

## Cache Invalidation

### When should you invalidate CloudFront objects?

**Answer:**

Use invalidation when cached content must be removed before its normal expiration.

Examples:

- Emergency content correction.
- Security-sensitive content removal.
- Incorrect deployment.
- Mutable object naming.

Avoid making invalidation the primary deployment mechanism for every release.

---

### Why is this deployment strategy problematic?

```text
Deploy
  ↓
Invalidate /*
  ↓
Wait for cache repopulation
  ↓
Repeat every deployment
```

**Answer:**

Broad invalidations can:

- Create unnecessary cache churn.
- Reduce cache efficiency.
- Increase origin traffic.
- Increase operational dependency on invalidation completion.
- Make deployments less predictable.

Prefer immutable asset versioning where possible.

---

## Cache Behavior

### What is a cache behavior?

**Answer:**

A cache behavior defines how CloudFront handles requests matching a particular path pattern.

For example:

```text
/static/* → S3 + long TTL
/media/*  → S3 + controlled TTL
/api/*    → ALB + dynamic policy
```

Different workloads should generally have different caching rules.

---

### Which behavior is used when multiple patterns match?

**Answer:**

CloudFront evaluates path patterns according to its behavior matching rules, with more specific matching behavior taking precedence over the default behavior.

The exact path configuration should therefore be reviewed when troubleshooting an unexpected origin or cache policy.

A common production mistake is assuming a request uses a policy that actually belongs to another behavior.

---

## Policy Design Examples

### Design a policy for immutable static assets.

**Answer:**

For content-hashed assets:

```text
/static/app.a83f92.js
/static/styles.29bc41.css
```

a strong design is:

```text
Cache key:
  Path
  ↓
Long TTL
  ↓
No unnecessary query/header/cookie variation
```

Because the filename changes when the content changes, a long cache lifetime can be used safely.

---

### Design a policy for a public product API.

**Answer:**

Suppose:

```http
GET /api/products/100
```

returns the same representation to all users for a bounded period.

A possible design is:

```text
Cache key:
  Path
  + currency if representation changes

TTL:
  Short/medium depending on freshness requirements

Cookies:
  Excluded if irrelevant

Authentication:
  Not used for the response

Tracking parameters:
  Excluded if irrelevant
```

The correct TTL depends on how stale the product data can safely become.

---

### Design a policy for a personalized API.

**Answer:**

For:

```http
GET /api/me
```

where the response depends on the authenticated user, the default production approach should be to avoid shared CloudFront caching unless a strong cache isolation design exists.

The application should remain responsible for authentication and authorization.

---

## Policy Troubleshooting

### CloudFront cache hit ratio suddenly dropped. What do you check?

**Answer:**

Use a structured investigation:

```text
Cache Hit Ratio ↓
       │
       ├── Recent deployment?
       │
       ├── Cache policy changed?
       │
       ├── Query-string variation increased?
       │
       ├── Cookie variation increased?
       │
       ├── Header variation increased?
       │
       ├── TTL changed?
       │
       ├── Invalidation performed?
       │
       └── Traffic pattern changed?
```

Then compare CloudFront metrics with request logs and deployment history.

---

### CloudFront is returning stale data. What do you investigate?

**Answer:**

Check:

- CloudFront cache policy.
- Minimum/default/maximum TTL configuration.
- Origin `Cache-Control` behavior.
- Object versioning.
- Recent invalidations.
- Whether the request is reaching the expected behavior.
- Whether the origin itself is returning stale data.

The critical distinction is:

```text
CloudFront stale
        vs
Origin stale
```

Do not invalidate CloudFront until you know which layer is producing stale data.

---

### CloudFront cache hit ratio is low even though content should be cacheable. Why?

**Answer:**

Potential causes include:

- Cache key contains unnecessary query strings.
- Cookies create many variants.
- Headers create unnecessary variants.
- TTL is too short.
- URLs are not normalized.
- Cache behavior is incorrect.
- Objects are frequently invalidated.
- Requests are actually dynamic.
- Traffic is distributed across many low-frequency objects.

The correct response is not automatically "increase TTL."

First determine why requests are producing different cache keys.

---

## Security Questions

### What is the biggest caching security mistake?

**Answer:**

Treating personalized content as safely shareable.

For example:

```text
GET /api/account
```

returns:

```json
{
  "email": "user@example.com",
  "balance": 5000
}
```

If this response is cached under a key shared by multiple users, the CDN can become a data-leak mechanism.

The safe design is to make the cache semantics match the authorization semantics.

---

### Can WAF replace cache policy security?

**Answer:**

No.

WAF can block malicious or unwanted requests, but it does not determine whether a cached response is safe to share.

These are separate concerns:

```text
WAF
 ↓
Is this request allowed?

Cache Policy
 ↓
Can this response be reused for this cache key?
```

Both need to be correct.

---

## Performance Questions

### How do cache policies affect backend scalability?

**Answer:**

Cache policies directly influence how many requests reach the origin.

Consider:

```text
1,000,000 viewer requests
        │
        ▼
CloudFront
        │
        ├── 950,000 cache hits
        │
        └── 50,000 origin requests
```

The backend only handles approximately the origin-bound portion of the traffic.

A poorly designed cache key might instead produce:

```text
1,000,000 viewer requests
        │
        ▼
CloudFront
        │
        └── 700,000 origin requests
```

The application, database, and downstream services then experience substantially higher load.

---

### Can increasing TTL always improve performance?

**Answer:**

No.

Increasing TTL can improve cache reuse but can also increase data staleness.

The trade-off is:

```text
Long TTL
  ↓
Better cache reuse
  ↓
Lower origin load
  ↓
Potentially staler data
```

The correct TTL depends on business freshness requirements.

---

## Advanced Interview Questions

### Why should cache-key design be treated as part of API design?

**Answer:**

Because API response semantics determine whether requests can safely share cached representations.

Suppose:

```text
GET /products?currency=USD
```

and:

```text
GET /products?currency=EUR
```

produce different representations.

Then the API contract itself defines a cache variation.

Therefore:

```text
API semantics
     ↓
Response variation
     ↓
Cache-key requirements
     ↓
CloudFront policy
```

CDN configuration should not be designed independently from API behavior.

---

### What is cache fragmentation?

**Answer:**

Cache fragmentation occurs when many cache entries represent essentially the same underlying response because the cache key contains unnecessary variation.

Example:

```text
/product/100
```

with multiple irrelevant query strings:

```text
/product/100?utm_source=a
/product/100?utm_source=b
/product/100?utm_source=c
```

If all become independent cache keys, the effective cache reuse decreases.

---

### What is cache poisoning?

**Answer:**

Cache poisoning occurs when an attacker causes a cache to store a response that can later be served to other requests incorrectly.

The risk is particularly serious when:

- Untrusted request attributes influence the origin response.
- Those attributes are not correctly represented in the cache key.
- The response is cacheable.
- The poisoned response is subsequently shared.

A robust design must ensure that every request attribute capable of changing a cacheable representation is appropriately handled.

---

### Why is forwarding a header not equivalent to including it in the cache key?

**Answer:**

Because forwarding answers:

> Should the origin receive this value?

Cache-key inclusion answers:

> Should different values create different cached objects?

For example:

```text
Header forwarded
       │
       ├── Origin needs it
       │
       └── Response does not vary by it
```

may be valid.

But if the response changes according to that header:

```text
Header value changes response
       ↓
Header must be accounted for
       ↓
Cache correctness must be preserved
```

This distinction is a frequent CloudFront interview topic.

---

## Scenario-Based Questions

### A product API returns stale data for 10 minutes after deployment. What is your approach?

**Answer:**

First determine whether the stale response is coming from CloudFront or the origin.

Then inspect:

1. Cache behavior.
2. Cache policy.
3. TTL configuration.
4. Origin response headers.
5. Deployment timing.
6. Object invalidation history.
7. CloudFront logs.
8. Origin logs.

If the endpoint is expected to change immediately, consider whether:

- The TTL is too long.
- Versioned URLs should be used.
- The endpoint should not be cached.
- Explicit invalidation is appropriate.

---

### A cache policy includes all cookies and cache hit ratio is poor. What would you do?

**Answer:**

Identify which cookies actually affect the response.

Then:

```text
All Cookies
     ↓
Determine response-affecting cookies
     ↓
Remove irrelevant cookies from cache variation
     ↓
Re-evaluate cache hit ratio
```

If the response is personalized, avoid forcing it into shared caching merely to improve the metric.

Correctness takes precedence over cache efficiency.

---

### A team wants to include every header in the cache key "to be safe." What do you say?

**Answer:**

This is usually the wrong abstraction.

Including every header can destroy cache reuse because many headers are request-specific but do not affect the representation.

Instead:

1. Identify which headers change the response.
2. Include only necessary response-varying attributes in the cache key.
3. Forward additional origin-required headers separately when appropriate.
4. Verify behavior with representative traffic.

The goal is not maximum variation. It is **minimum sufficient variation**.

---

## Quick Policy Comparison

| Requirement | Cache Policy | Origin Request Policy |
|---|---:|---:|
| Define TTL | Yes | No |
| Define cache-key query strings | Yes | No |
| Define cache-key headers | Yes | No |
| Define cache-key cookies | Yes | No |
| Forward additional query strings | No | Yes |
| Forward additional headers | No | Yes |
| Forward additional cookies | No | Yes |
| Optimize cache reuse | Yes | Indirectly |
| Control origin request context | No | Yes |

---

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Include every query string | "More information is safer" | Include only response-affecting values |
| Include every header | Avoid thinking about semantics | Identify representation-changing headers |
| Cache personalized APIs | Focus on performance | Determine whether responses are safely shareable |
| Forward every cookie | Convenience | Forward only what the origin requires |
| Use very short TTLs everywhere | Fear of stale data | Define freshness requirements explicitly |
| Use very long TTLs everywhere | Maximize cache hits | Match TTL to data volatility |
| Invalidate `/*` after every deployment | Mutable asset names | Use versioned/static hashed assets |
| Confuse forwarding with cache variation | Policies seem similar | Separate cache-key and origin requirements |
| Optimize hit ratio blindly | Treat metric as the goal | Optimize correctness and origin efficiency together |

---

## Interview Traps

### "Higher cache hit ratio is always better."

**Incorrect.**

A high hit ratio with an incorrect cache key can serve incorrect or sensitive content.

### "All GET requests should be cached."

**Incorrect.**

GET is read-oriented, but the response may still be personalized or sensitive.

### "Forwarding a header means it becomes part of the cache key."

**Incorrect.**

Origin forwarding and cache-key variation are separate configuration concerns.

### "A long TTL is always the fastest configuration."

**Incomplete.**

A long TTL can improve cache reuse but may violate freshness requirements.

### "Invalidation is the standard way to deploy static assets."

**Incomplete.**

Immutable, versioned assets are generally a better foundation for long-lived caching.

## Key Takeaways

- **A cache policy defines the cache key and TTL behavior; an origin request policy controls additional request data sent to the origin.**
- **The cache key must contain every request attribute that changes the representation, but should exclude irrelevant variation to prevent cache fragmentation.**
- **Personalized or authorization-dependent responses should not be blindly placed into a shared CloudFront cache.**
- **TTL, `Cache-Control`, invalidation, and asset versioning must be designed together around application freshness requirements.**
- **The strongest CloudFront caching design minimizes cache-key variation while preserving response correctness and security.**