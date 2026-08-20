# 13- Rapid-Fire Questions

## Overview

Rapid-fire CloudFront interviews test whether you can recall core concepts accurately and distinguish closely related AWS features without overexplaining.

The expected answer format is usually:

> **Definition → Key distinction → Production implication**

The questions below focus on high-frequency CloudFront concepts, terminology, configuration decisions, and common interview traps.

## Core Concepts

### What is Amazon CloudFront?

CloudFront is AWS's content delivery network (CDN). It distributes HTTP/HTTPS content through a globally distributed edge network, reducing latency for users and reducing traffic reaching origins.

### Why use CloudFront?

Primary reasons include:

- Lower latency through edge delivery
- Reduced origin load
- Global content distribution
- HTTP caching
- TLS termination
- Integration with AWS WAF
- Private content delivery
- Edge request processing
- Origin failover

### What is an edge location?

An edge location is a CloudFront point of presence where CloudFront can receive requests and serve cached content close to users.

### What is an origin?

An origin is the backend source from which CloudFront retrieves content when it cannot satisfy a request from its cache.

Examples include:

- S3
- Application Load Balancer
- EC2-based application
- API endpoint
- Custom HTTP server

### What is a CloudFront distribution?

A distribution is the CloudFront configuration that defines how requests are handled, including:

- Origins
- Behaviors
- Cache policies
- Origin request policies
- TLS configuration
- Viewer protocol behavior
- Security configuration

### What is a cache behavior?

A cache behavior defines how CloudFront handles requests matching a specific path pattern.

For example:

```text
/images/*
/api/*
/static/*
```

Different behaviors can use different origins, cache policies, and request handling rules.

---

## Request Flow

### What happens when a user requests an object through CloudFront?

Conceptually:

```text
Client
  ↓
CloudFront Edge
  ↓
Cache Lookup
  ↓
Hit ───────────────→ Response
  │
  └── Miss
       ↓
     Origin
       ↓
     Response
       ↓
   Edge Cache
       ↓
     Client
```

### What is a cache hit?

A cache hit occurs when CloudFront can serve the requested object from its cache without retrieving it from the origin.

### What is a cache miss?

A cache miss occurs when CloudFront cannot satisfy the request from the relevant cache and must retrieve the content from the origin.

### Does every request go to the origin?

No. Cacheable requests can be served directly from CloudFront.

Dynamic or non-cacheable requests may still reach the origin.

### Does CloudFront cache every response?

No. Whether a response is cached depends on CloudFront configuration and HTTP caching behavior.

---

## Caching

### What is a cache key?

The cache key identifies a cached representation.

It is derived from the request attributes configured to distinguish one response from another.

Typical dimensions can include:

- Path
- Query strings
- Headers
- Cookies

### Why is the cache key important?

Because it affects both:

- Cache efficiency
- Response correctness

If too many irrelevant attributes are included, the cache becomes fragmented.

If a response-changing attribute is excluded, users may receive an incorrect cached response.

### What is cache-key explosion?

Cache-key explosion occurs when too many request variations create separate cache entries.

For example:

```text
/product?id=123&utm_source=google
/product?id=123&utm_source=email
/product?id=123&utm_source=linkedin
```

If `utm_source` does not change the response, including it unnecessarily fragments the cache.

### What is cache invalidation?

Cache invalidation removes cached objects before their normal expiration.

It is useful when content must be replaced immediately.

### Should you invalidate all files after every deployment?

Usually no.

Prefer versioned or content-hashed assets:

```text
app.8f31c.js
app.2a91d.css
```

Long-lived immutable assets can then remain cached safely.

### What is TTL?

TTL determines how long a cached object remains fresh before CloudFront needs to consider retrieving or revalidating it according to the configured caching behavior.

### What is the difference between minimum, default, and maximum TTL?

They establish boundaries for how long CloudFront can cache objects under the relevant cache policy.

The exact behavior also depends on the origin's caching headers and CloudFront policy configuration.

### What happens if TTL is too short?

You may get:

- More origin requests
- Lower cache hit ratio
- Higher origin load
- Higher latency
- Potentially higher cost

### What happens if TTL is too long?

You may serve stale content longer than the business permits.

### Is a high cache hit ratio always good?

No.

A high hit ratio is valuable only if the cached responses are correct and sufficiently fresh.

---

## Cache Policies

### What is a CloudFront cache policy?

A cache policy controls which request attributes participate in the cache key and establishes caching-related settings such as TTL boundaries.

### What is an origin request policy?

An origin request policy controls which request information CloudFront forwards to the origin without necessarily making those attributes part of the cache key.

### Why are cache policy and origin request policy different?

Because:

```text
Cache Key
    ≠
Everything Sent to Origin
```

A request attribute may be required by the origin without needing to create a separate cached representation.

### Why is this distinction important?

Suppose an origin needs a header for processing, but the response is identical regardless of that header.

Including the header in the cache key would unnecessarily fragment the cache.

---

## Headers, Cookies, and Query Strings

### Should all query strings be included in the cache key?

No.

Include only query parameters that change the response representation.

### Should all headers be included in the cache key?

No.

Only headers that affect the cached response should normally distinguish cache entries.

### Should all cookies be included?

No.

Cookies can create extremely high cache cardinality and may contain user-specific state.

### Why can cookies be dangerous for CDN caching?

Consider:

```text
Cookie: session_id=user-123
```

If user identity becomes part of the cache identity, every user may create a separate representation.

Worse, incorrect cache configuration can create a security boundary violation.

### What is the safest approach for personalized content?

Often, do not use shared CDN caching for the personalized response.

Instead:

```text
Shared content → CloudFront
Personalized content → Application
```

---

## Static and Dynamic Content

### What content is a good CloudFront caching candidate?

Examples include:

- JavaScript
- CSS
- Images
- Fonts
- Videos
- Public documents
- Public product catalogs
- Public reference data

### What content should generally not be shared through a CDN cache?

Examples include:

- Payment operations
- Shopping carts
- User-specific account data
- Authentication responses
- Highly personalized responses
- Sensitive administrative responses

The exact decision depends on response semantics and authorization requirements.

### Can APIs be cached by CloudFront?

Yes.

CloudFront can cache HTTP API responses when the API's responses are safe to share and the cache policy is designed correctly.

---

## Origins

### What origins can CloudFront use?

Common origins include:

- Amazon S3
- Application Load Balancer
- EC2
- API services
- Custom HTTP servers

### Can CloudFront have multiple origins?

Yes.

Different cache behaviors can route requests to different origins.

### Why use multiple origins?

For example:

```text
/static/* → S3
/images/* → S3
/api/*    → ALB
/download/* → Private origin
```

This allows different traffic classes to have different architectures.

### What is origin failover?

Origin failover allows CloudFront to use an alternate origin when the configured failure conditions are met for the primary origin.

### Does origin failover automatically solve disaster recovery?

No.

The secondary origin must actually be capable of serving the workload.

You still need:

- Data replication
- Application recovery
- Capacity
- Configuration synchronization
- Deployment synchronization
- Tested failover procedures

---

## S3 Integration

### Should an S3 bucket behind CloudFront be public?

For protected production architectures, preferably no.

Use CloudFront with Origin Access Control so the S3 bucket can remain private.

### What is Origin Access Control?

Origin Access Control (OAC) allows CloudFront to securely access an S3 origin without requiring the bucket to be publicly accessible.

### Why is OAC preferred over a public bucket?

It provides a cleaner architecture:

```text
Internet
   ↓
CloudFront
   ↓
Private S3
```

rather than:

```text
Internet
   ↓
Public S3
```

### Can CloudFront serve private S3 objects?

Yes.

CloudFront can control access while the S3 bucket remains private.

---

## Security

### How does CloudFront improve security?

CloudFront can provide:

- TLS termination
- AWS WAF integration
- DDoS protection through AWS edge infrastructure
- Private origin access patterns
- Signed URLs
- Signed cookies
- Security headers through response headers policies
- Edge request processing

### Does CloudFront replace AWS WAF?

No.

CloudFront and WAF solve different problems.

```text
CloudFront → Delivery / caching
WAF        → HTTP request filtering
```

They are commonly deployed together.

### What is AWS WAF's role with CloudFront?

WAF can inspect HTTP requests and apply rules such as:

- IP filtering
- Rate-based controls
- Managed rule groups
- Request pattern matching
- Geographic restrictions

### How do you prevent origin bypass?

Ensure the architecture does not expose an unrestricted alternative origin path.

For S3, use OAC.

For custom origins, apply appropriate origin access controls and network/security restrictions.

### What is a signed URL?

A signed URL grants temporary access to a specific CloudFront resource based on a trusted signature.

### What is a signed cookie?

A signed cookie provides authorization for accessing one or more protected resources without placing authorization parameters into every URL.

### Signed URL vs signed cookie?

| Requirement | Signed URL | Signed Cookie |
|---|---|---|
| Single resource | Strong fit | Possible |
| Multiple resources | Less convenient | Strong fit |
| Private media | Strong fit | Strong fit |
| Per-download authorization | Strong fit | Less convenient |
| URL remains clean | No | Yes |

---

## HTTPS and TLS

### Can CloudFront serve HTTPS?

Yes.

CloudFront supports HTTPS for viewer connections.

### Can CloudFront communicate with the origin over HTTPS?

Yes.

For production systems, HTTPS should generally be used for sensitive traffic between CloudFront and the origin as well.

### Why terminate TLS at CloudFront?

TLS termination at the edge provides:

- Global TLS handling
- Reduced origin TLS workload
- Consistent viewer security
- Centralized certificate configuration

---

## Edge Computing

### What is edge computing in CloudFront?

Edge computing executes selected request or response logic closer to users.

CloudFront supports edge execution through mechanisms such as:

- CloudFront Functions
- Lambda@Edge

### When should logic run at the edge?

Good examples include:

- Redirects
- URL normalization
- Header manipulation
- Lightweight request transformations
- Simple routing decisions

### When should logic remain at the origin?

Keep logic at the application layer when it requires:

- Database state
- Transactions
- Complex authorization
- Long-running computation
- Distributed coordination
- Complex business rules

### CloudFront Functions vs Lambda@Edge?

CloudFront Functions are intended for lightweight, high-scale edge logic.

Lambda@Edge is appropriate when more advanced execution capabilities are required.

The key interview point is:

> Choose based on execution requirements, not simply on which service has more features.

---

## Backend Architecture

### Where does CloudFront sit in a typical Django architecture?

```text
Client
  ↓
CloudFront
  ↓
WAF
  ↓
ALB
  ↓
Django
  ↓
Redis
  ↓
PostgreSQL
```

CloudFront handles the edge delivery layer.

Django remains responsible for business logic.

### Where does CloudFront sit in a FastAPI architecture?

A similar architecture applies:

```text
Client
  ↓
CloudFront
  ↓
WAF
  ↓
ALB
  ↓
FastAPI
  ↓
Redis / PostgreSQL
```

### Is CloudFront a replacement for Redis?

No.

CloudFront caches HTTP representations at the edge.

Redis is generally an application-level data cache.

### Is CloudFront an API gateway?

Not in the same sense as an API gateway responsible for API-specific routing, lifecycle management, authentication integration, and API management.

CloudFront is primarily the edge delivery and HTTP distribution layer.

---

## Performance

### How does CloudFront reduce latency?

By serving cached content from edge locations closer to clients instead of requiring every request to travel to the origin.

### What is origin offload?

Origin offload is the reduction in origin traffic caused by serving requests from CloudFront caches.

Conceptually:

```text
Total Requests
     ↓
CloudFront
     ├── Cache Hits → Edge
     └── Cache Misses → Origin
```

### What causes a low cache hit ratio?

Common causes include:

- Very short TTLs
- Excessive cache-key dimensions
- High-cardinality query strings
- User-specific cookies
- Personalized content
- Frequent invalidation
- Poor cache policy design

### How do you improve cache efficiency?

Evaluate:

- Cache-key dimensions
- TTLs
- Asset versioning
- Query parameters
- Headers
- Cookies
- Response sizes
- Content classification

Do not blindly increase TTL.

---

## Monitoring

### What should you monitor for CloudFront?

Important signals include:

- Requests
- Bytes transferred
- Error rates
- Cache behavior
- Origin request volume
- Latency
- HTTP status codes
- 4xx responses
- 5xx responses

### Why monitor origin request volume?

Because a CDN can appear healthy while the origin is overloaded.

A sudden increase in origin requests may indicate:

- Cache fragmentation
- Expired content
- Cache policy changes
- Cache bypass
- Traffic spikes
- Deployment mistakes

### What does a CloudFront 4xx indicate?

A 4xx generally indicates a client/request/access-related failure, but the exact cause depends on the status code.

Examples include:

- 403
- 404
- 400

### What does a CloudFront 5xx indicate?

A 5xx generally indicates a server-side failure somewhere in the request path, potentially involving the origin.

Investigate both CloudFront and origin logs.

---

## Troubleshooting

### CloudFront returns 403. What do you check?

Check:

1. CloudFront behavior.
2. Origin permissions.
3. S3 bucket policy if applicable.
4. OAC configuration.
5. WAF rules.
6. Signed URL/cookie validation.
7. Object existence.
8. Host/header behavior.
9. Origin access restrictions.

### CloudFront returns 404 but the object exists in S3. What do you check?

Check:

- Requested path
- Object key
- Origin path configuration
- Cache behavior
- S3 object permissions
- Whether the object was recently created
- Cached error responses

### CloudFront is serving stale content. What do you check?

Check:

- TTL configuration
- Cache policy
- Origin `Cache-Control` headers
- Invalidation status
- Whether the requested URL is versioned
- Whether multiple cache behaviors are involved

### The origin is overloaded despite CloudFront. What do you investigate?

Check:

```text
Cache Hit Ratio
       ↓
Cache Key
       ↓
Query Strings
       ↓
Headers
       ↓
Cookies
       ↓
TTL
       ↓
Origin Request Rate
```

Do not immediately scale the origin before identifying why requests are missing the cache.

---

## Cost and Scalability

### How does CloudFront help reduce infrastructure cost?

By reducing:

- Origin compute requirements
- Origin bandwidth
- Database traffic caused by repeated reads
- Application processing for cacheable responses

### Can CloudFront increase costs?

Yes.

Costs can come from:

- Data transfer
- Requests
- Invalidations depending on usage
- Edge execution
- Other associated services

The correct optimization target is total system cost, not only the CDN bill.

### Can CloudFront handle traffic spikes?

Yes, particularly when the traffic is cacheable.

A cacheable spike may look like:

```text
100x Client Traffic
       ↓
CloudFront
       ↓
High Edge Cache Hit Rate
       ↓
Small Origin Increase
```

Dynamic traffic is different because cache misses still reach the origin.

---

## Architecture

### How would you design CloudFront for a high-traffic website?

A common architecture is:

```text
Users
  ↓
Route 53
  ↓
CloudFront
  ↓
AWS WAF
  ↓
ALB
  ↓
Application
  ├── Redis
  └── PostgreSQL
```

Static assets can use S3:

```text
CloudFront
   ├── /static/* → S3
   └── /api/*    → ALB
```

### How would you design CloudFront for a multi-region application?

Use CloudFront as the global edge layer and route traffic to resilient regional origins.

The application and data layers still require:

- Regional capacity
- Data replication
- Failover strategy
- Consistency model
- RPO
- RTO

### Does CloudFront provide database failover?

No.

CloudFront operates at the HTTP delivery layer.

Database failover must be designed separately.

---

## Interview Traps

### Is CloudFront the same as an ALB?

No.

| CloudFront | ALB |
|---|---|
| Global edge distribution | Regional load balancing |
| CDN caching | Request routing |
| Edge delivery | Application load distribution |
| Viewer-facing | Origin-facing |
| Can cache content | Does not function as a CDN |

### Is CloudFront the same as Route 53?

No.

Route 53 provides DNS and related routing capabilities.

CloudFront provides content delivery.

### Is CloudFront the same as S3?

No.

S3 provides object storage.

CloudFront distributes content from origins, including S3.

### Does CloudFront cache POST requests by default?

CloudFront's standard caching model is primarily centered around cacheable HTTP methods such as `GET` and `HEAD`.

Do not assume that all HTTP methods are cached.

### Can CloudFront cache authenticated requests?

Potentially, but this requires extremely careful cache-policy and authorization design.

For user-specific responses, shared caching is often inappropriate.

### Does a cache miss mean CloudFront is broken?

No.

A cache miss is normal behavior. The question is whether the miss rate is expected for the workload.

### Does invalidation delete the object from S3?

No.

Invalidation affects CloudFront's cached copy, not the origin object's existence.

### Does increasing TTL always improve performance?

Not necessarily.

It can improve cache efficiency but increase staleness.

---

## Quick Comparison

| Service | Primary Responsibility |
|---|---|
| CloudFront | Global content delivery and edge caching |
| Route 53 | DNS and routing |
| S3 | Object storage |
| ALB | Regional HTTP load balancing |
| WAF | Web request filtering |
| Redis | Application data caching |
| API Gateway | API management and gateway functionality |
| Lambda@Edge | Advanced edge execution |
| CloudFront Functions | Lightweight edge execution |

---

## One-Line Interview Answers

| Question | Rapid Answer |
|---|---|
| What is CloudFront? | AWS's globally distributed CDN for HTTP/HTTPS content delivery. |
| What is an origin? | The backend source from which CloudFront retrieves content. |
| What is an edge location? | A CloudFront location where requests are received and cached content can be served. |
| What is a cache hit? | The requested representation is served from the CloudFront cache. |
| What is a cache miss? | CloudFront must retrieve the representation from the origin. |
| What is a cache key? | The identity used to distinguish cached request representations. |
| What is TTL? | The freshness duration applied to cached content. |
| What is invalidation? | A mechanism for removing cached objects before normal expiration. |
| What is OAC? | A mechanism for allowing CloudFront to securely access private S3 origins. |
| What is a signed URL? | A temporary signed authorization mechanism for a CloudFront resource. |
| What is a signed cookie? | A temporary authorization mechanism suitable for accessing multiple protected resources. |
| CloudFront vs Redis? | CloudFront caches HTTP responses at the edge; Redis caches application data. |
| CloudFront vs ALB? | CloudFront is a global CDN; ALB is a regional load balancer. |
| CloudFront vs Route 53? | CloudFront delivers content; Route 53 provides DNS and routing. |
| What is origin failover? | Routing to an alternate origin when configured failure conditions occur. |
| What is edge computing? | Executing selected request/response logic near users. |
| What causes cache fragmentation? | Too many unnecessary cache-key variations. |
| What causes stale content? | TTL, origin caching headers, or invalidation/versioning strategy. |
| Can CloudFront cache APIs? | Yes, when responses are safe to share and caching is correctly configured. |
| Should personalized APIs be cached? | Usually not through shared CDN caching unless the cache is explicitly partitioned and proven safe. |
| How do you protect S3 behind CloudFront? | Keep the bucket private and use Origin Access Control. |
| How do you reduce origin load? | Increase safe cache reuse and reduce unnecessary cache misses. |
| Does CloudFront replace WAF? | No; WAF provides request filtering while CloudFront provides content delivery. |
| Does CloudFront replace an API gateway? | No; their responsibilities overlap only partially. |
| Does CloudFront provide database HA? | No; database availability is a separate architectural concern. |
| Is a high cache hit ratio enough? | No; correctness and freshness matter as well. |

## Rapid-Fire Production Scenarios

### Users are receiving another user's data. What is your first suspicion?

Inspect the cache policy and cache key.

A user-specific response may have been incorrectly cached and shared.

### Origin traffic suddenly increases after a CloudFront deployment. What is your first suspicion?

Check whether the cache policy or cache key changed and caused cache fragmentation or cache bypass.

### Static assets are still slow globally. What do you check?

Check:

- CloudFront usage
- Cache behavior
- TTL
- Cache hit ratio
- Asset size
- Compression
- Origin latency
- Cache-control headers

### A private S3 object returns `403` through CloudFront. What do you check first?

Check OAC and the S3 bucket policy, then inspect CloudFront behavior and object permissions.

### A new deployment is serving old JavaScript.

Check whether the asset URL is immutable/versioned and whether the HTML or relevant cache object requires invalidation.

### A CDN cache hit ratio dropped after adding a header.

Check whether the header was unnecessarily added to the cache key.

### An API endpoint is consuming excessive database capacity.

Determine whether the endpoint is cacheable and whether CloudFront or Redis can safely reduce repeated reads.

### A region fails.

CloudFront can route to an alternate origin only if the architecture has been explicitly designed for failover and the alternate origin is healthy and data-compatible.

### A security attack targets `/login`.

Use CloudFront and WAF as the edge protection layer and investigate rate-based controls, managed rules, and origin load.

### A deployment requires immediate content replacement.

Determine whether versioned assets can solve the problem. If not, use targeted invalidation rather than broad invalidation where possible.

## Interview Answer Pattern

For almost any CloudFront architecture question, structure the answer around five points:

1. **Traffic classification** — identify static, dynamic, public, private, and personalized traffic.
2. **Cache strategy** — define cacheability, cache key, TTL, and invalidation.
3. **Origin architecture** — explain S3, ALB, application services, and failover.
4. **Security and reliability** — discuss WAF, OAC, origin protection, authorization, and recovery.
5. **Operational trade-offs** — discuss latency, cache hit ratio, origin load, monitoring, cost, and correctness.

This structure keeps rapid answers technically precise while demonstrating architectural reasoning.

## Key Takeaways

- **CloudFront is primarily a global HTTP delivery and caching layer; distinguish it clearly from Route 53, ALB, S3, Redis, WAF, and API Gateway.**
- **Cache-key design is both a performance concern and a security boundary; incorrect configuration can cause fragmentation or data leakage.**
- **Use CloudFront aggressively for safe, reusable content, but treat personalized and transactional responses as separate workloads.**
- **Strong CloudFront answers connect caching to origin protection, security, observability, availability, and total system cost.**
- **For rapid-fire interviews, answer with the core definition first, then give the key distinction or production implication.**