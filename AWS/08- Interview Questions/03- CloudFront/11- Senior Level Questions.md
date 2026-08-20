# 11- Senior Level Questions

## Overview

Senior-level CloudFront interviews focus on architectural reasoning rather than feature memorization. The interviewer is typically evaluating whether you can design an edge delivery strategy that balances **latency, cache efficiency, security, availability, origin protection, operational complexity, and cost**.

A strong answer should connect CloudFront to the surrounding architecture:

- DNS and traffic routing
- HTTP caching semantics
- API authentication and authorization
- Origin scalability
- AWS WAF
- Multi-region deployments
- Observability
- CI/CD
- Cost management
- Failure recovery

At this level, the important question is not simply:

> Can CloudFront cache this?

It is:

> What should happen at the edge, what should happen at the origin, and why?

---

## How to Approach Senior-Level CloudFront Questions

A senior-level answer should generally follow this reasoning sequence:

1. Identify the traffic characteristics.
2. Determine whether the content is public, private, personalized, or immutable.
3. Define the cache key.
4. Define freshness and invalidation requirements.
5. Protect the origin from direct access.
6. Define failure and failover behavior.
7. Define observability and operational controls.
8. Evaluate performance and cost trade-offs.
9. Explain what should remain at the application or data layer.

This demonstrates architectural thinking instead of simply listing CloudFront features.

---

## Question 1: How would you decide whether an API endpoint should be cached by CloudFront?

### Answer

Start by determining whether the response is:

- Public or user-specific
- Deterministic or highly variable
- Safe to serve slightly stale
- Expensive to generate
- Frequently requested
- Sensitive to authorization context

A public product catalog is usually a strong candidate:

```http
GET /api/products
```

A user-specific endpoint generally should not use shared CDN caching:

```http
GET /api/users/me
GET /api/orders
GET /api/cart
```

| Endpoint | Cache Suitability | Reason |
|---|---|---|
| Product catalog | High | Public and read-heavy |
| Product images | Very high | Usually immutable |
| Search results | Medium | Depends on query cardinality |
| User profile | Low | Personalized |
| Shopping cart | None | User-specific mutable state |
| Checkout | None | Sensitive transactional state |
| Health endpoint | Usually none | Little caching value |

The most important senior-level concern is **cache correctness**.

The cache policy must be designed together with:

- Cache key
- Authorization behavior
- Cookies
- Query strings
- Response headers
- TTL
- Invalidation strategy

A high cache hit ratio is meaningless if the CDN is serving the wrong representation.

---

## Question 2: How would you prevent CloudFront from serving stale business-critical data?

### Answer

Do not solve every freshness requirement through invalidations.

Use a combination of:

- Appropriate TTLs
- `Cache-Control`
- `s-maxage`
- Versioned resources
- Explicit invalidation for exceptional cases
- Application-level cache invalidation where necessary

For example:

```http
Cache-Control: public, max-age=60, s-maxage=300
```

This allows browser and shared-cache freshness policies to differ.

For immutable assets:

```http
Cache-Control: public, max-age=31536000, immutable
```

The correct TTL should come from the **business tolerance for staleness**.

An application icon can remain cached for a year. Inventory information may only tolerate seconds of staleness.

Therefore, TTL should be treated as a business and architectural decision rather than an arbitrary infrastructure setting.

---

## Question 3: How would you design CloudFront for a globally distributed API?

### Answer

Use CloudFront as the global HTTP entry point and route requests toward regional application infrastructure.

```mermaid
flowchart TD
    Client((Global Clients))
    R53[Route 53]
    CF[CloudFront]
    WAF[AWS WAF]

    Client --> R53
    R53 --> CF
    CF --> WAF

    WAF --> US[US Origin]
    WAF --> EU[EU Origin]
    WAF --> APAC[APAC Origin]

    US --> USA[API Cluster]
    EU --> EUA[API Cluster]
    APAC --> APA[API Cluster]
```

The exact origin-selection strategy depends on the application's requirements.

A globally distributed CloudFront deployment does **not** automatically make the application globally consistent.

The architecture must separately address:

- Database replication
- Session management
- Distributed locking
- Event propagation
- Data residency
- Write consistency
- Regional failure
- RPO
- RTO

CloudFront solves the edge delivery problem. It does not solve distributed data consistency.

---

## Question 4: How would you prevent users from bypassing CloudFront and accessing the origin directly?

### Answer

The origin should not become a second public entry point.

For S3 origins, use **Origin Access Control (OAC)** and keep the bucket private.

For custom origins, use appropriate controls such as:

- Origin authentication
- Security groups where applicable
- Private networking patterns
- AWS WAF
- Application-level authorization
- Origin-specific access controls

The desired architecture is:

```text
Internet
   |
   v
CloudFront
   |
   v
Protected Origin
```

Not:

```text
Internet
   | \
   |  \
   v   v
CloudFront  Origin
```

The second design creates an origin-bypass path.

A senior engineer should always ask:

> Can an attacker reach the origin without passing through the intended security controls?

---

## Question 5: What is the difference between CloudFront caching and Redis caching?

### Answer

They operate at different architectural layers.

| CloudFront | Redis |
|---|---|
| Edge/distributed cache | Application/data cache |
| Outside the application | Inside application architecture |
| HTTP responses and assets | Objects, queries, computed values |
| Reduces network distance | Reduces application/database work |
| Shared when safely cacheable | Usually application-controlled |

Typical architecture:

```mermaid
flowchart LR
    User((User))
    CF[CloudFront]
    API[Django / FastAPI]
    Redis[(Redis)]
    DB[(PostgreSQL)]

    User --> CF
    CF --> API
    API --> Redis
    Redis --> DB
```

A request can benefit from both layers:

```text
Client
  ↓
CloudFront
  ↓
Application
  ↓
Redis
  ↓
PostgreSQL
```

CloudFront should therefore not be treated as a replacement for Redis.

---

## Question 6: How would you troubleshoot a low CloudFront cache hit ratio?

### Answer

Start with the cache key.

Potential causes include:

- Excessive query-string variation
- Unnecessary cookies
- Unnecessary headers
- Authorization-dependent responses
- Low TTLs
- Dynamic content
- Frequently changing URLs
- Incorrect cache policies
- Incorrect application cache-control headers

For example:

```text
/products?utm_source=google
/products?utm_source=email
/products?utm_source=facebook
```

If `utm_source` does not change the response, including it in the cache key creates unnecessary cache fragmentation.

### Investigation Flow

```text
Low cache hit ratio
       |
       v
Inspect cache policy
       |
       v
Inspect cache key
       |
       v
Check query strings
       |
       v
Check cookies and headers
       |
       v
Check TTL
       |
       v
Check application Cache-Control
```

Increasing TTL is not automatically the correct solution.

A poor cache key can make even a very long TTL ineffective.

---

## Question 7: What is cache key fragmentation and why does it matter?

### Answer

Cache fragmentation occurs when requests for logically identical content produce different cache keys.

For example:

```text
/products?utm_source=google
/products?utm_source=email
/products?utm_source=facebook
```

If all three requests return the same representation, creating three cache entries is unnecessary.

### Consequences

- Lower cache hit ratio
- More origin requests
- Higher latency
- Higher origin cost
- More cache storage consumption

The cache key should contain only request attributes that actually affect the response.

Conceptually:

```text
Cache key =
    Path
    + Required query parameters
    + Required headers
    + Required cookies
```

Do not add request dimensions merely because they are available.

---

## Question 8: How would you handle authenticated APIs through CloudFront?

### Answer

Authentication and caching must be designed together.

For highly personalized endpoints:

```text
Client
  ↓
CloudFront
  ↓
WAF
  ↓
Origin
```

The origin performs application authentication and authorization.

For specialized use cases, edge logic can reject or transform certain requests before they reach the origin.

However, forwarding an `Authorization` header does **not** automatically make a response safe to cache.

The cache policy must reflect the authorization and personalization model.

For sensitive user-specific responses, the safest design is often to avoid shared caching entirely.

---

## Question 9: How would you design CloudFront for zero-downtime deployments?

### Answer

Separate immutable assets from mutable entry documents.

Instead of:

```text
/static/app.js
```

use versioned assets:

```text
/static/app.a81c92.js
/static/app.b31f10.js
```

A new deployment produces a new URL.

```mermaid
flowchart LR
    Build[CI/CD Build]
    Assets[Versioned Assets]
    HTML[HTML]
    S3[S3]
    CF[CloudFront]

    Build --> Assets
    Build --> HTML

    Assets --> S3
    HTML --> S3

    S3 --> CF
```

### Deployment Strategy

1. Build the application.
2. Generate versioned assets.
3. Upload assets.
4. Deploy the new HTML.
5. Invalidate only objects that require immediate replacement.
6. Monitor errors and cache behavior.

This reduces dependence on broad invalidations and prevents clients from receiving HTML that references unavailable assets.

---

## Question 10: When would you use CloudFront Functions versus Lambda@Edge?

### Answer

Use CloudFront Functions for lightweight edge processing where the logic is simple and latency-sensitive.

Typical use cases include:

- URL normalization
- Redirects
- Header manipulation
- Lightweight request processing

Use Lambda@Edge when the workload requires capabilities beyond the lightweight CloudFront Functions execution model.

| Area | CloudFront Functions | Lambda@Edge |
|---|---|---|
| Lightweight edge logic | Excellent | Good |
| Simple redirects | Excellent | Good |
| Header manipulation | Excellent | Good |
| Complex processing | More limited | Better suited |
| Operational complexity | Lower | Higher |
| Typical use | Simple edge behavior | More advanced edge processing |

Do not move business logic to the edge merely because it is technically possible.

Edge logic increases:

- Deployment complexity
- Debugging complexity
- Distributed-state concerns
- Operational complexity

Move logic to the edge when the latency or architectural benefit justifies that complexity.

---

## Question 11: How would you design CloudFront for a multi-region active-active application?

### Answer

CloudFront can provide the global HTTP entry point, but the application must independently support multi-region operation.

```mermaid
flowchart TD
    User((Global Users))
    CF[CloudFront]

    CF --> US[US Region]
    CF --> EU[EU Region]

    US --> USAPI[Application]
    EU --> EUAPI[Application]

    US --> USDB[(Regional Database)]
    EU --> EUDB[(Regional Database)]

    USDB <-->|Replication / Data Sync| EUDB
```

Before implementing active-active architecture, answer:

- Where is authoritative data stored?
- Can multiple regions accept writes?
- What happens during network partition?
- How are sessions managed?
- How are events replicated?
- What consistency model is acceptable?
- What are the RPO and RTO requirements?
- Are there data residency constraints?

CloudFront does not solve these problems.

---

## Question 12: How would you handle cache invalidation at scale?

### Answer

Prefer **versioned URLs** for immutable resources.

Instead of:

```text
/app.js
```

use:

```text
/app.4f8a21.js
```

A later deployment produces:

```text
/app.8b912f.js
```

The new object gets a new cache key, so there is no need to invalidate the old asset globally.

Use invalidations for:

- Emergency corrections
- HTML documents
- Incorrectly cached responses
- Exceptional content replacement

Avoid invalidating every static asset after every deployment.

This makes deployment slower, creates unnecessary operational work, and undermines the value of long-lived caching.

---

## Question 13: How would you diagnose high origin load even though CloudFront is enabled?

### Answer

CloudFront being present does not guarantee effective caching.

Investigate:

1. Cache hit ratio
2. Cache key fragmentation
3. TTL configuration
4. Request methods
5. `Cache-Control` headers
6. Query-string policies
7. Cookie forwarding
8. Authorization behavior
9. Traffic distribution
10. Origin response characteristics

For example:

```text
10 million requests
9 million origin requests
1 million cache hits
```

CloudFront is technically operating, but origin offload is poor.

The important question is:

> Why are requests not reusable?

Do not stop at:

> CloudFront is configured.

---

## Question 14: How would you design CloudFront for a high-volume e-commerce platform?

### Answer

Separate public catalog traffic from personalized transactional traffic.

```mermaid
flowchart TD
    User((Customer))
    CF[CloudFront]

    User --> CF

    CF --> Catalog[Product Catalog]
    CF --> Images[S3 Product Images]
    CF --> Cart[Cart API]
    CF --> Checkout[Checkout API]

    Cart --> Redis[(Redis)]
    Checkout --> DB[(PostgreSQL)]
```

| Traffic | Strategy |
|---|---|
| Product images | Aggressive caching |
| Product catalog | Moderate caching |
| Recommendations | Carefully designed |
| Cart | No shared caching |
| Checkout | No caching |
| Payment | No caching |

The boundary should be based on **data ownership, personalization, and business semantics**, not simply URL structure.

---

## Question 15: How would you use CloudFront to protect a backend during a traffic spike?

### Answer

Use caching and edge security to prevent unnecessary requests from reaching the origin.

```text
Traffic Spike
     |
     v
CloudFront
     |
     +---- Cache Hit ----> Client
     |
     +---- Cache Miss ---> WAF ---> Origin
```

For dynamic traffic, combine CloudFront with:

- AWS WAF
- Rate limiting
- Origin autoscaling
- Load balancing
- Application-level protection
- Database protection

CloudFront can significantly reduce origin pressure when requests are cacheable.

However:

> CloudFront does not make an unscalable dynamic backend scalable by itself.

If every request is a cache miss, the backend still receives the traffic.

---

## Question 16: How would you protect against cache poisoning?

### Answer

Cache poisoning occurs when an attacker influences a cached representation so that subsequent users receive an unintended response.

Potential causes include:

- Untrusted headers
- Host manipulation
- Query-string ambiguity
- Incorrect cache-key configuration
- Application behavior that varies based on an attribute excluded from the cache key

### Prevention

Ensure every request attribute that affects the response is correctly represented in the cache key.

Also:

- Validate host headers
- Normalize URLs
- Validate forwarded headers
- Avoid caching inappropriate error responses
- Review origin behavior
- Keep cache policies intentionally scoped

A cache is part of the application's security boundary.

Incorrect cache-key design can become a data-exposure vulnerability.

---

## Question 17: How would you design secure private media delivery?

### Answer

Use CloudFront with a private origin and signed access.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant CloudFront
    participant Storage

    Client->>API: Authenticate
    API->>API: Authorize resource
    API-->>Client: Signed URL

    Client->>CloudFront: Request signed resource
    CloudFront->>Storage: Fetch if needed
    Storage-->>CloudFront: Private object
    CloudFront-->>Client: Resource
```

The architecture provides:

- Private origin access
- Expiring resource access
- Application-controlled authorization
- Global delivery
- Reduced origin traffic

A signed URL controls access to a resource. It does not replace application authentication and authorization.

---

## Question 18: How would you monitor CloudFront in production?

### Answer

Monitor both **edge behavior** and **origin behavior**.

| Metric | Why It Matters |
|---|---|
| Cache hit ratio | Measures cache effectiveness |
| Requests | Traffic volume |
| Bytes downloaded | Bandwidth usage |
| Origin latency | Backend performance |
| 4xx errors | Client or security issues |
| 5xx errors | Origin or service issues |
| Error rate | Availability |
| Data transfer | Cost and capacity |

Correlate CloudFront metrics with:

- AWS WAF
- ALB
- Django/FastAPI metrics
- Redis
- PostgreSQL
- Kubernetes
- Application logs

Example investigation:

```text
CloudFront 5xx ↑
      |
      v
ALB 5xx ↑ ?
      |
      +-- Yes --> Application / infrastructure investigation
      |
      +-- No --> CloudFront / origin configuration investigation
```

The objective is not merely to monitor CloudFront but to understand the **end-to-end request path**.

---

## Question 19: How would you reduce CloudFront costs without damaging performance?

### Answer

Cost optimization should reduce unnecessary bytes, origin requests, and infrastructure work without degrading user experience.

Use:

- Compression
- Efficient image formats
- Long-lived caching for immutable assets
- Versioned URLs
- Appropriate cache policies
- Reduced cache-key fragmentation
- Efficient origin responses
- Appropriate CloudFront pricing configuration

Think about total system cost:

```text
Total Delivery Cost
=
CloudFront Request Cost
+
Data Transfer
+
Origin Requests
+
Origin Compute
+
Storage
```

A CDN configuration that increases cache hits may reduce backend compute and database load enough to reduce total infrastructure cost.

---

## Question 20: How would you design CloudFront for a globally distributed video platform?

### Answer

Separate media delivery from the control-plane API.

```mermaid
flowchart TD
    Viewer((Viewer))

    Viewer --> CF[CloudFront]

    CF --> Video[S3 / Media Origin]

    Viewer --> API[Playback API]

    API --> Auth[Authentication]
    API --> DB[(Metadata DB)]
```

Video traffic is typically:

- High bandwidth
- Read-heavy
- Globally distributed
- Highly cacheable

The playback API is generally:

- Dynamic
- Authentication-sensitive
- User-specific

Separating the two prevents media delivery from being tightly coupled to API processing.

---

## Question 21: What happens if the CloudFront origin becomes unavailable?

### Answer

The behavior depends on the origin and configuration.

For critical architectures, define explicit failure behavior.

```mermaid
flowchart LR
    Client((Client))
    CF[CloudFront]

    CF --> Primary[Primary Origin]
    CF --> Secondary[Secondary Origin]

    Primary --> Health{Available?}

    Health -->|Yes| Response[Response]
    Health -->|No| Secondary
```

Possible strategies include:

- Origin groups
- Multi-region infrastructure
- Application load balancing
- Independent storage replicas

Failover only works if the secondary origin is actually capable of serving the requested resource.

A standby endpoint with unsynchronized data is not a real disaster-recovery strategy.

---

## Question 22: How would you design CloudFront around a Django application?

### Answer

A common production architecture is:

```mermaid
flowchart LR
    User((Client))
    CF[CloudFront]
    WAF[AWS WAF]
    ALB[Application Load Balancer]
    Django[Django]
    Redis[(Redis)]
    PG[(PostgreSQL)]

    User --> CF
    CF --> WAF
    WAF --> ALB
    ALB --> Django

    Django --> Redis
    Django --> PG
```

Responsibilities should remain clearly separated:

| Component | Responsibility |
|---|---|
| CloudFront | Edge delivery |
| WAF | Request filtering |
| ALB | Load balancing |
| Django | Business logic |
| Redis | Application cache |
| PostgreSQL | Persistence |

CloudFront should not become the place where Django business rules are implemented.

---

## Question 23: How would you design CloudFront around a FastAPI microservice architecture?

### Answer

Use CloudFront as the external HTTP boundary while keeping service-to-service communication inside the application architecture.

```mermaid
flowchart TD
    Client((Client))
    CF[CloudFront]
    Gateway[API Gateway / ALB]
    API[FastAPI Layer]

    Client --> CF
    CF --> Gateway
    Gateway --> API

    API --> UserService[User Service]
    API --> OrderService[Order Service]
    API --> ProductService[Product Service]
```

Internal communication may use:

- REST
- gRPC
- Kafka
- Other internal messaging mechanisms

CloudFront should remain focused on internet-facing delivery and edge behavior.

---

## Question 24: Should every API response be cached if it is a GET request?

### Answer

No.

HTTP method alone does not determine whether shared CDN caching is safe.

A GET request can still be:

- User-specific
- Authorization-dependent
- Financially sensitive
- Highly dynamic
- Non-deterministic

For example:

```http
GET /api/account/balance
Authorization: Bearer <token>
```

Caching this response incorrectly could expose one user's balance to another user.

### Interview Trap

Incorrect answer:

> GET requests are cacheable, so CloudFront should cache all GET requests.

Better answer:

> GET is generally cacheable by HTTP semantics, but shared CDN caching depends on response semantics, authorization, cache-key design, and freshness requirements.

---

## Question 25: How would you handle personalization with CloudFront?

### Answer

Avoid turning every user attribute into a cache-key dimension.

Suppose a response changes based on:

```text
user_id
country
language
device
subscription
feature_flag
```

Including all of these dimensions can create enormous cache fragmentation.

A better architecture may separate shared content from personalized data:

```text
CloudFront
    |
    +-- Shared public content
    |
    +-- Personalized API
```

The client can combine globally cacheable content with user-specific responses.

This is often more scalable than trying to make every personalized response edge-cacheable.

---

## Question 26: How would you approach CloudFront during a security incident?

### Answer

Treat CloudFront as one layer in the incident-response architecture.

```text
Attack
  |
  v
CloudFront
  |
  +--> WAF filtering
  |
  +--> Rate limiting
  |
  v
Origin
```

During an incident:

1. Identify affected paths.
2. Inspect CloudFront and WAF metrics.
3. Determine whether the traffic is cacheable or dynamic.
4. Apply appropriate WAF controls.
5. Protect expensive origin endpoints.
6. Preserve logs for investigation.
7. Monitor origin health.
8. Remove temporary mitigations after the incident is resolved.

Do not automatically disable caching during an attack.

Caching may be one of the mechanisms protecting the origin.

---

## Question 27: How would you handle an API that has both public and private responses?

### Answer

Separate cache behavior whenever possible.

For example:

```text
GET /products
```

may be public.

But:

```text
GET /products/recommendations
```

may depend on the authenticated user.

Use distinct paths, policies, or architectural boundaries so that public and private responses cannot accidentally share the same cache representation.

The principle is:

> Design APIs so that cacheability is explicit.

This is often safer than relying on complicated cache-key behavior for heavily personalized endpoints.

---

## Question 28: How would you optimize CloudFront for a high-volume Python backend?

### Answer

The primary objective is to reduce expensive origin work.

```text
Client
  |
  v
CloudFront
  |
  +-- Cache Hit --> Client
  |
  +-- Cache Miss
       |
       v
Django / FastAPI
       |
       +--> Redis
       |
       +--> PostgreSQL
```

### Optimization Order

1. Cache static assets aggressively.
2. Cache safe public API responses.
3. Reduce cache-key fragmentation.
4. Compress responses.
5. Optimize origin latency.
6. Use Redis for application-level caching.
7. Scale application workers.
8. Protect PostgreSQL from unnecessary reads.

CloudFront optimization and Python application optimization should be treated as one end-to-end performance problem.

---

## Question 29: How would you migrate an existing application to CloudFront with minimal risk?

### Answer

Do not immediately place all traffic behind CloudFront.

Use a staged migration.

```mermaid
flowchart LR
    Existing[Existing Origin]
    CF[CloudFront]
    Test[Test Traffic]
    Prod[Production Traffic]

    Existing --> CF
    CF --> Test
    CF --> Prod
```

### Migration Steps

1. Inventory static and dynamic traffic.
2. Identify cacheable resources.
3. Create the CloudFront distribution.
4. Configure origins and policies.
5. Test in a non-production environment.
6. Validate headers and cache behavior.
7. Validate authentication flows.
8. Test invalidation behavior.
9. Monitor origin load.
10. Gradually migrate production traffic.

Validate:

- Cache correctness
- Authorization
- Cookies
- Redirects
- CORS
- Compression
- TLS
- Origin behavior
- Error handling

---

## Question 30: How would you explain CloudFront's role in a senior system design interview?

### Answer

A strong answer is:

> CloudFront is the edge delivery layer of the architecture. I use it to terminate global HTTP traffic close to users, cache safe and reusable responses, reduce origin load, integrate edge security controls, and improve global latency. I do not treat it as a replacement for application caching, database caching, service discovery, or multi-region architecture. The important design work is defining cache boundaries, cache keys, TTLs, origin protection, failure behavior, and observability.

A representative architecture is:

```mermaid
flowchart TD
    User((Global Clients))
    DNS[Route 53]
    CF[CloudFront]
    WAF[AWS WAF]
    Origin[Application Origin]
    Redis[(Redis)]
    DB[(PostgreSQL)]
    Events[(Kafka)]

    User --> DNS
    DNS --> CF
    CF --> WAF
    WAF --> Origin

    Origin --> Redis
    Origin --> DB
    Origin --> Events
```

This demonstrates that CloudFront is being considered as one component of a larger distributed system.

---

## Advanced Trade-Offs

Senior engineers should explicitly discuss trade-offs instead of presenting CloudFront as universally beneficial.

| Decision | Benefit | Trade-Off |
|---|---|---|
| Long TTL | Excellent cache performance | Potential staleness |
| Short TTL | Better freshness | More origin traffic |
| Large cache key | Correct response variations | Cache fragmentation |
| Small cache key | Higher hit ratio | Potential incorrect responses |
| Edge logic | Lower latency | More distributed complexity |
| Aggressive caching | Lower origin load | Harder freshness management |
| Multi-region origins | Better resilience | Data consistency complexity |
| Signed URLs | Controlled access | Additional authorization complexity |
| Origin failover | Higher availability | More infrastructure |
| Public API caching | Lower latency | Requires careful security analysis |

The right choice depends on the application's correctness and availability requirements.

---

## Senior-Level Interview Traps

### "CloudFront makes everything faster"

Not necessarily.

If the content is dynamic and uncached, the request still reaches the origin.

### "A high cache hit ratio is always good"

Not if stale or incorrect content is being served.

Correctness comes before cache efficiency.

### "CloudFront replaces Redis"

It does not.

They operate at different architectural layers.

### "CloudFront provides multi-region database failover"

It does not.

CloudFront can provide HTTP-level origin routing and failover, but database availability and consistency require separate architecture.

### "Private content cannot be cached"

Private content can be safely delivered through CloudFront when access control and cache behavior are correctly designed, including mechanisms such as signed URLs or signed cookies.

### "Long TTL is always better"

Only when the content can safely remain fresh for that duration.

---

## Senior-Level Design Checklist

When designing CloudFront for a production system, evaluate:

| Area | Questions |
|---|---|
| Traffic | What percentage is static, cacheable, or dynamic? |
| Cache | What can safely be cached? |
| Cache Key | Which request attributes change the response? |
| Freshness | How stale can the content safely become? |
| Security | Can users bypass CloudFront? |
| Authentication | Are private responses safely isolated? |
| Origin | Can the backend handle cache misses? |
| Scaling | What happens during traffic spikes? |
| Availability | What happens when the origin fails? |
| Cost | How much traffic and data transfer are involved? |
| Observability | Can edge and origin failures be correlated? |
| Deployment | How are cached resources versioned and invalidated? |
| Compliance | Does data residency affect routing or caching? |
| Operations | Can the team safely modify policies under pressure? |

---

## Architecture Review Questions

Before approving a CloudFront architecture, ask:

1. What percentage of traffic is cacheable?
2. What exactly is the cache key?
3. Can a private response ever become a shared cache object?
4. What is the acceptable staleness window?
5. What happens when the origin is unavailable?
6. Can the origin be accessed directly?
7. What protects expensive API endpoints?
8. How are cache invalidations handled?
9. How does deployment interact with cached content?
10. What metrics prove that CloudFront is providing value?
11. What happens when the cache hit ratio drops?
12. How does the architecture behave during a regional outage?
13. What data cannot legally or safely be cached?
14. Which logic belongs at the edge versus the application?
15. What operational complexity does CloudFront introduce?

## Key Takeaways

- **Senior CloudFront design is primarily about cache boundaries, correctness, security, and origin protection rather than simply enabling CDN caching.**
- **A cache key must contain every request attribute that changes the representation while excluding irrelevant dimensions that create fragmentation.**
- **CloudFront complements Redis, application caches, load balancers, Kubernetes, and multi-region infrastructure; it does not replace them.**
- **Global delivery does not automatically create a globally consistent or highly available application—the origin, data layer, and failure model must be designed independently.**
- **Strong senior-level answers explicitly discuss trade-offs between latency, freshness, security, availability, operational complexity, and cost.**