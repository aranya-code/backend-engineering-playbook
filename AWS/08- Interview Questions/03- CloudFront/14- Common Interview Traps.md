# 14- Common Interview Traps

## Overview

CloudFront interviews frequently test distinctions between concepts that appear similar but operate at different layers. The most common mistakes come from treating CloudFront as simply a cache, assuming every request is cacheable, or overlooking the interaction between cache keys, authorization, origins, and application behavior.

A strong interview answer should distinguish **delivery**, **caching**, **routing**, **security**, and **application responsibilities**. The goal is not to memorize service definitions but to understand the consequences of configuration decisions.

## CloudFront Is Not Just a Cache

### Trap: "CloudFront is a caching service."

This is incomplete.

CloudFront is a CDN and edge delivery service that can:

- Cache HTTP responses
- Deliver content from edge locations
- Terminate TLS
- Route requests to origins
- Integrate with AWS WAF
- Enforce geographic restrictions
- Protect private content
- Execute edge logic
- Support origin failover
- Apply request and response policies

A better interview answer is:

> CloudFront is AWS's global content delivery layer. Caching is one of its primary capabilities, but it also provides edge routing, security integration, TLS termination, and edge request processing.

### Trap: "CloudFront always makes the application faster."

Not necessarily.

CloudFront primarily improves performance when requests can be served efficiently at the edge.

If every request is forwarded to the origin, CloudFront may add another network hop without providing substantial caching benefit.

---

## CloudFront vs Other AWS Services

### Trap: CloudFront and ALB are interchangeable.

They are not.

| CloudFront | Application Load Balancer |
|---|---|
| Global edge delivery | Regional load balancing |
| CDN | Load balancer |
| Can cache responses | Does not provide CDN caching |
| Viewer-facing | Usually origin-facing |
| Edge TLS termination | Regional TLS termination |
| Can integrate with WAF | Can integrate with WAF |
| Routes to origins | Routes to application targets |

A common architecture is:

```text
Client
  ↓
CloudFront
  ↓
AWS WAF
  ↓
ALB
  ↓
Application
```

### Trap: CloudFront replaces Route 53.

No.

Route 53 primarily provides DNS and routing capabilities.

CloudFront provides content delivery.

They commonly work together:

```text
User
  ↓
Route 53
  ↓
CloudFront
  ↓
Origin
```

### Trap: CloudFront replaces Redis.

No.

Their caching layers operate at different levels.

| CloudFront | Redis |
|---|---|
| Edge HTTP caching | Application data caching |
| Global distribution | Usually region/application-local |
| Caches HTTP representations | Caches data/state |
| Reduces origin traffic | Reduces application/database work |

### Trap: CloudFront replaces API Gateway.

No.

CloudFront is primarily a CDN and edge delivery layer. API Gateway provides API gateway capabilities such as API-oriented routing, throttling, authorization integrations, and API lifecycle controls.

They can also be used together.

---

## Cache Key Traps

### Trap: "The cache key is just the URL."

Not always.

The cache key can incorporate configured request attributes such as:

- Path
- Query strings
- Headers
- Cookies

The important engineering question is:

> Which request attributes actually change the response?

Only those dimensions should generally distinguish cached representations.

### Trap: Include every query string in the cache key.

This can cause cache fragmentation.

For example:

```text
/product/123?utm_source=google
/product/123?utm_source=email
/product/123?utm_source=linkedin
```

If `utm_source` does not affect the response, treating it as a cache-key dimension creates unnecessary cache entries.

### Trap: Exclude every query string.

This can be equally dangerous.

Suppose:

```text
/search?q=python
/search?q=django
```

The query parameter changes the response. If it is excluded from the cache identity, one result could incorrectly be served for another request.

### Trap: Headers are always safe to ignore.

No.

If a header changes the response representation, excluding it from the cache key can produce incorrect responses.

If it is required by the origin but does **not** change the response, forwarding it without making it part of the cache key can improve cache reuse.

### Trap: Cookies should always be included.

No.

Cookies can have extremely high cardinality and often contain user-specific state.

Including session-related cookies in a shared cache key can destroy cache efficiency.

More seriously, incorrectly caching personalized responses can create a data-isolation vulnerability.

---

## Cache Policy vs Origin Request Policy

### Trap: "The cache policy controls everything CloudFront sends to the origin."

Not exactly.

The two policies have different responsibilities.

| Policy | Primary Responsibility |
|---|---|
| Cache policy | Determines cache key and caching-related settings |
| Origin request policy | Determines additional request information forwarded to the origin |

The important distinction is:

```text
Request attributes used for cache identity
                ≠
All request attributes forwarded to origin
```

### Example

Suppose the origin needs:

```text
Authorization
X-Tenant-ID
```

but the response is intentionally not shared between users or tenants.

You must design the caching and forwarding behavior based on whether those values affect the representation and whether shared caching is safe.

Never assume that forwarding a header automatically makes the response safe to cache.

---

## TTL Traps

### Trap: "Longer TTL is always better."

Long TTLs can improve:

- Cache hit ratio
- Origin offload
- Latency
- Cost efficiency

But they can also increase staleness.

The correct TTL depends on the content's freshness requirements.

### Trap: "Short TTL means the object is never cached."

No.

A short TTL can still provide substantial caching.

For example:

```text
TTL = 60 seconds
```

can eliminate a large amount of repeated origin traffic when thousands of users request the same resource within that window.

### Trap: "TTL is controlled only by the origin."

Not necessarily.

CloudFront cache policies establish TTL boundaries and caching behavior, while origin response headers can influence freshness within those configured constraints.

### Trap: "TTL determines whether a response is safe to cache."

No.

TTL controls freshness duration. It does not determine whether a response should logically be shared between users.

**Cacheability and freshness are different concerns.**

---

## Cache Invalidation Traps

### Trap: "Invalidation deletes the object."

No.

Invalidation removes the cached representation from CloudFront caches. It does not delete the object from the origin.

```text
CloudFront cache
      ↓
  Invalidated

S3 / Application origin
      ↓
  Object remains
```

### Trap: "Invalidate everything after every deployment."

This can work operationally but is usually a poor long-term deployment strategy for static assets.

Prefer immutable versioned assets:

```text
app.91d31f.js
styles.7a83c2.css
```

Then a new deployment creates new URLs.

### Trap: "You never need invalidation if you use versioning."

Not necessarily.

HTML documents, configuration resources, redirects, or other mutable objects may still require controlled invalidation depending on the deployment strategy.

---

## Personalized Content Traps

### Trap: "CloudFront can cache authenticated responses, so caching user-specific APIs is fine."

Technically possible does not mean architecturally safe.

Consider:

```text
GET /profile
Authorization: user-A
```

If the response is personalized, a shared cache must not serve it to user B.

For many personalized APIs, the safer approach is:

```text
Static/public representation → CloudFront cache
Personalized response       → Application
```

### Trap: "Authorization headers automatically prevent cache sharing."

Do not rely on that assumption.

Caching behavior must be explicitly designed and verified.

Authorization is a security boundary; cache-key configuration must not accidentally collapse requests from different principals into one cached representation.

---

## S3 Security Traps

### Trap: "S3 must be public for CloudFront to access it."

No.

A production architecture can keep the bucket private and use CloudFront Origin Access Control.

```text
Internet
   ↓
CloudFront
   ↓
OAC
   ↓
Private S3 bucket
```

### Trap: "If the S3 bucket is private, CloudFront automatically has access."

No.

CloudFront must be correctly authorized through the origin access configuration and S3 bucket policy.

### Trap: "OAC and public S3 access are equivalent."

They represent different security architectures.

Prefer private S3 origins with explicit CloudFront access where appropriate.

---

## Origin Access Traps

### Trap: "CloudFront protects the origin automatically."

Not necessarily.

If an ALB or custom origin is publicly reachable, users may be able to bypass CloudFront and access the origin directly.

A secure architecture should consider:

- Origin exposure
- Security groups
- WAF placement
- Application-level authorization
- Custom origin controls
- Host/header validation where appropriate

The objective is to ensure that the intended security controls cannot simply be bypassed by calling the origin directly.

---

## Signed URL vs Signed Cookie Traps

### Trap: "Signed URLs and signed cookies are basically the same."

Both provide controlled access to private CloudFront content, but their use cases differ.

| Signed URL | Signed Cookie |
|---|---|
| Good for individual resources | Good for multiple resources |
| Authorization appears in URL | Authorization stored in cookie |
| Useful for downloads | Useful for sessions/content collections |
| Easy to generate per resource | Convenient for accessing multiple protected files |

### Trap: "Signed URLs authenticate users."

Not necessarily.

A signed URL primarily proves that the request has a valid CloudFront authorization signature according to the configured trust model.

Your application may still need its own authentication and authorization system.

---

## HTTP Method Traps

### Trap: "CloudFront caches every HTTP method."

No.

CloudFront's caching model primarily targets cacheable methods such as `GET` and `HEAD`.

Do not assume that:

```text
POST
PUT
PATCH
DELETE
```

behave like ordinary cacheable `GET` requests.

### Trap: "POST requests never pass through CloudFront."

They can pass through CloudFront to an origin, but that does not mean they are cached.

This distinction is important:

```text
Request routing
      ≠
Response caching
```

---

## API Caching Traps

### Trap: "APIs should never be cached."

Too broad.

Public or safely shareable API responses can be excellent CDN candidates.

Examples:

```text
GET /products
GET /catalog
GET /countries
GET /public-config
```

The important question is whether the response can safely be shared among clients.

### Trap: "Every GET API can be cached."

Also wrong.

A `GET` can still return personalized or sensitive data:

```text
GET /account/profile
GET /orders
GET /notifications
```

HTTP method alone does not determine whether shared caching is safe.

---

## Origin Failover Traps

### Trap: "CloudFront origin failover gives automatic disaster recovery."

Not by itself.

A failover architecture requires:

- Healthy secondary origin
- Synchronized application configuration
- Available data
- Appropriate routing
- Capacity
- Tested recovery procedures

CloudFront can switch traffic; it cannot magically recreate your application state.

### Trap: "A secondary origin is enough for database recovery."

No.

If both application origins depend on a failed database, switching application origins does not solve the underlying failure.

---

## Edge Computing Traps

### Trap: "CloudFront Functions and Lambda@Edge are the same."

No.

They target different execution requirements.

| CloudFront Functions | Lambda@Edge |
|---|---|
| Lightweight edge logic | More capable edge execution |
| Very high-scale request processing | Advanced request/response processing |
| Simple transformations | More complex workloads |
| Lower execution complexity | Broader execution capabilities |

Always verify the current AWS service limits and supported event behavior when designing production systems.

### Trap: "Move business logic to the edge for lower latency."

Only when the logic is genuinely suitable for edge execution.

Do not move logic requiring:

- Database transactions
- Complex distributed state
- Long-running computation
- Strong consistency
- Complex business workflows

to the edge simply because it is closer to the user.

---

## WAF Traps

### Trap: "CloudFront is a firewall."

No.

CloudFront provides delivery and edge capabilities.

AWS WAF provides web request inspection and filtering.

```text
CloudFront
    ↓
AWS WAF
    ↓
Origin
```

### Trap: "WAF prevents all attacks."

No security service eliminates every attack class.

WAF is particularly useful for HTTP-layer threats and policy enforcement, but applications still require:

- Authentication
- Authorization
- Input validation
- Secure coding
- Rate limiting where appropriate
- Dependency management
- Secrets management

---

## HTTPS Traps

### Trap: "HTTPS between the browser and CloudFront is enough."

For sensitive applications, also consider the CloudFront-to-origin connection.

A typical secure architecture is:

```text
Client
  │ HTTPS
  ▼
CloudFront
  │ HTTPS
  ▼
Origin
```

Encrypting only the viewer connection leaves the origin connection as a separate security decision.

### Trap: "CloudFront SSL means the application no longer needs TLS."

The application architecture still needs to define how traffic is protected between internal components and origins.

CloudFront's viewer TLS configuration does not automatically secure every downstream connection.

---

## Error Handling Traps

### Trap: "A CloudFront 403 always means S3 permissions are wrong."

No.

A 403 can originate from multiple layers.

Investigate:

- CloudFront configuration
- WAF
- Signed URL/cookie validation
- Origin permissions
- S3 bucket policy
- Application authorization
- Geographic restrictions

### Trap: "A CloudFront 5xx always means CloudFront is down."

No.

A 5xx can indicate problems involving the origin or the request path.

Investigate:

```text
Client
  ↓
CloudFront
  ↓
WAF
  ↓
Origin
  ↓
Application
  ↓
Database / dependencies
```

---

## Monitoring Traps

### Trap: "CloudFront is healthy because requests are returning 200."

Not enough.

You should also examine:

- Cache hit ratio
- Origin request volume
- 4xx rate
- 5xx rate
- Latency
- Bytes transferred
- Origin health
- WAF activity
- Application metrics

A CDN can return successful responses while origin load is unexpectedly high.

### Trap: "High cache hit ratio always means a good architecture."

No.

A high cache hit ratio can coexist with incorrect caching.

For example, if personalized responses are incorrectly shared, a high hit ratio would be a serious security problem.

The priority is:

```text
Correctness
    ↓
Security
    ↓
Freshness
    ↓
Performance
```

---

## Cost Traps

### Trap: "CloudFront always reduces AWS cost."

Not necessarily.

CloudFront introduces its own costs while potentially reducing:

- Origin bandwidth
- Compute
- Application processing
- Database reads

Evaluate the complete architecture rather than one service's bill.

### Trap: "Higher cache hit ratio automatically means lower total cost."

Usually beneficial, but not sufficient as a standalone metric.

Consider:

- Request volume
- Object size
- Origin processing
- Data transfer
- Invalidation usage
- Edge execution
- Application/database costs

---

## Cache-Control Traps

### Trap: "Cache-Control: no-cache means do not cache."

This is a common HTTP terminology trap.

`no-cache` generally means the cached response must be revalidated before reuse. It does not simply mean "never store this response."

`no-store` is the stronger directive for instructing caches not to store the response.

Interview answers should distinguish:

```text
no-cache
    → revalidation semantics

no-store
    → do not store
```

The exact CloudFront behavior still depends on the configured cache policy and caching rules.

### Trap: "max-age=0 means the object cannot be cached."

Not necessarily.

It indicates that the response is immediately stale from an HTTP freshness perspective and may require revalidation.

---

## Cache Stampede Traps

### Trap: "A CDN eliminates cache stampedes."

No.

A large number of requests arriving when an object expires can still create origin pressure depending on workload and caching behavior.

A production design should consider:

- TTL strategy
- Request collapsing behavior
- Origin capacity
- Application caching
- Prewarming where appropriate
- Grace/stale-serving strategies where supported

The important interview point is that a CDN reduces origin traffic but does not eliminate every cache-coordination problem.

---

## Deployment Traps

### Trap: "Invalidate everything after deployment."

Avoid making global invalidation the default deployment mechanism.

For immutable assets:

```text
Before:
app.js

After:
app.91d31f.js
```

The HTML can reference the new asset while old assets remain safely cached.

This improves:

- Cache efficiency
- Deployment safety
- Rollback capability
- Origin offload

### Trap: "Versioning means old content can never be served."

Not necessarily.

If HTML or manifests are stale, clients may continue requesting old asset URLs.

Deployment design must consider the entire dependency chain:

```text
HTML
  ↓
Asset references
  ↓
CloudFront cache
  ↓
Origin
```

---

## Cache Invalidation and Deployment Safety

### Trap: "Invalidation is always the fastest fix."

It may be the operationally fastest fix, but repeated broad invalidations can indicate poor cache strategy.

Prefer:

1. Immutable assets for static resources.
2. Targeted invalidation for mutable resources.
3. Appropriate TTLs.
4. Explicit deployment sequencing.

### Trap: "Changing the origin automatically refreshes every cached object."

No.

Existing cached objects can continue being served until they expire or are invalidated according to the configuration.

---

## DNS and CloudFront Traps

### Trap: "CloudFront replaces DNS."

No.

A typical architecture is:

```text
api.example.com
       ↓
     DNS
       ↓
CloudFront distribution
       ↓
     Origin
```

DNS directs clients to the CloudFront distribution; CloudFront handles the HTTP delivery path.

### Trap: "CloudFront can be reached only through Route 53."

No.

CloudFront can be associated with custom domains using DNS records, including DNS providers other than Route 53.

---

## Origin Path Traps

### Trap: "The CloudFront URL path always maps directly to the origin path."

Not necessarily.

CloudFront behaviors and origin path configuration can alter how the request is forwarded.

For example:

```text
Viewer:
https://cdn.example.com/assets/app.js

Origin:
https://origin.example.com/static/assets/app.js
```

If an object returns 404 unexpectedly, inspect the effective origin path and behavior configuration.

---

## Query String Traps

### Trap: "Query strings are never cached."

Incorrect.

CloudFront can cache requests differentiated by query strings when the cache policy is configured accordingly.

The real question is:

> Which query strings affect the representation?

### Trap: "Query strings always need to be forwarded."

Not necessarily.

If the origin does not need a query parameter, forwarding it may be unnecessary.

If the query parameter affects the origin response, the architecture must ensure that caching and forwarding preserve correctness.

---

## Header Traps

### Trap: "Forwarding a header means it must be in the cache key."

No.

A header may need to reach the origin without distinguishing cached representations.

This is exactly why cache policies and origin request policies are separate concepts.

### Trap: "The Authorization header should always be part of the cache key."

Not automatically.

If responses are personalized, shared caching may be inappropriate altogether.

The correct decision depends on whether the response can safely be shared and how authorization affects representation.

---

## Geographic Restriction Traps

### Trap: "CloudFront geographic restrictions are equivalent to application authorization."

No.

Geographic restrictions are an edge-level access control mechanism.

They should not replace application-level authorization.

```text
CloudFront geographic control
            +
Application authorization
```

can provide defense in depth.

---

## Availability Traps

### Trap: "CloudFront makes the entire system highly available."

No.

CloudFront can improve edge availability and origin offload, but system availability depends on the entire dependency chain.

For example:

```text
CloudFront
   ↓
ALB
   ↓
Django
   ↓
Redis
   ↓
PostgreSQL
```

If PostgreSQL is unavailable and the application cannot operate without it, CloudFront does not make the application available.

### Trap: "Caching means the application can survive any origin failure."

No.

Only content already safely cached can potentially continue being served independently of the origin.

Dynamic requests still depend on the origin.

---

## Security Boundary Traps

### Trap: "CloudFront is the authorization layer."

Usually not.

CloudFront can enforce access mechanisms such as:

- Signed URLs
- Signed cookies
- Geographic restrictions
- WAF rules

But application authorization remains responsible for determining whether a user is allowed to perform business operations.

### Trap: "If content is behind CloudFront, it is private."

Not automatically.

Privacy depends on:

- Origin exposure
- CloudFront configuration
- Access controls
- Signed access mechanisms
- Application authorization
- Bucket policies
- WAF and network controls

---

## Common Interview Misstatements

| Incorrect Statement | Better Statement |
|---|---|
| CloudFront is just a cache | CloudFront is a CDN with caching, routing, security, and edge capabilities |
| CloudFront replaces ALB | CloudFront is global edge delivery; ALB provides regional load balancing |
| CloudFront replaces Redis | CloudFront caches HTTP responses; Redis caches application data |
| All GET requests should be cached | Only safely shareable responses should be shared through CDN caching |
| Longer TTL is always better | TTL is a freshness/performance trade-off |
| Invalidation deletes the origin object | Invalidation removes cached copies |
| Private S3 requires a public bucket | CloudFront can securely access private S3 using OAC |
| Authorization prevents cache sharing automatically | Cache behavior must explicitly preserve authorization boundaries |
| WAF is the CDN | WAF filters requests; CloudFront delivers content |
| CloudFront provides database HA | Database availability is a separate architecture concern |
| High cache hit ratio means the system is correct | Correctness and security come before cache efficiency |
| POST requests cannot pass through CloudFront | They can be forwarded, but caching is a separate concern |
| CloudFront automatically protects every origin | Origin bypass must be explicitly addressed |
| CloudFront eliminates origin failures | It reduces origin dependency for cacheable content but does not eliminate it |
| CloudFront is an API gateway | CloudFront is primarily a CDN and edge delivery layer |

## Senior-Level Trap Questions

### "How would you safely cache an authenticated API?"

Do not immediately answer with "include the Authorization header."

First determine whether the response is shared or personalized.

For personalized responses, prefer not to use shared CDN caching unless there is a carefully designed and tested cache partitioning strategy.

Then evaluate:

- Authorization model
- Cache key
- Cookies
- Headers
- Query strings
- TTL
- `Cache-Control`
- Data sensitivity
- Failure behavior

### "How would you maximize CloudFront cache hit ratio?"

Do not simply increase TTL.

A strong answer includes:

- Remove irrelevant cache-key dimensions.
- Avoid unnecessary cookies in the cache key.
- Avoid unnecessary headers in the cache key.
- Remove irrelevant query parameters.
- Use immutable asset versioning.
- Choose TTLs based on freshness requirements.
- Avoid unnecessary invalidations.
- Separate personalized and public traffic.

### "CloudFront cache hit ratio is high, but users report incorrect data. What happened?"

Investigate cache correctness before performance.

Likely areas include:

- Incorrect cache key
- Missing tenant/user dimension
- Incorrect cookie handling
- Missing header dimension
- Personalized response being shared
- Incorrect origin response caching semantics

### "How would you design CloudFront for a global Django application?"

A reasonable starting architecture is:

```text
                    Users
                      │
                  Route 53
                      │
                  CloudFront
                      │
                  AWS WAF
                      │
             ┌────────┴────────┐
             │                 │
          Static             Dynamic
             │                 │
             ▼                 ▼
             S3               ALB
                               │
                            Django
                          /         \
                      Redis       PostgreSQL
```

Then discuss:

- Cache strategy
- Regional application capacity
- Database architecture
- Origin protection
- TLS
- Monitoring
- Failover
- Deployment
- RPO/RTO

### "The origin is overloaded even though CloudFront is enabled. Why?"

CloudFront being present does not guarantee effective caching.

Investigate:

1. Cache hit ratio.
2. Cache key cardinality.
3. Query strings.
4. Headers.
5. Cookies.
6. TTLs.
7. Cache bypass behavior.
8. Dynamic traffic percentage.
9. Object sizes.
10. Recent configuration changes.

## Interview Answering Strategy

When an interviewer presents a CloudFront trap question, avoid immediately naming a configuration option.

Use this reasoning sequence:

```text
What kind of request?
        ↓
Is the response shareable?
        ↓
What changes the representation?
        ↓
What belongs in the cache key?
        ↓
What must reach the origin?
        ↓
What is the security boundary?
        ↓
What is the freshness requirement?
        ↓
What happens during failure?
```

This approach demonstrates architectural understanding rather than memorized AWS terminology.

## Key Takeaways

- **CloudFront is not merely a cache; understand its role as the global edge delivery layer and distinguish it from ALB, Route 53, S3, Redis, WAF, and API Gateway.**
- **Cache-key mistakes are both performance and security problems; incorrect keys can cause cache fragmentation or cross-user data exposure.**
- **Never assume that GET, Authorization, cookies, query strings, or TTL alone determine whether content is safe to cache. Evaluate response shareability and representation semantics.**
- **CloudFront improves origin offload and edge availability but does not automatically provide application, database, or disaster-recovery guarantees.**
- **In interviews, explain the reasoning behind a CloudFront configuration decision: correctness and security first, then freshness, performance, availability, and cost.**