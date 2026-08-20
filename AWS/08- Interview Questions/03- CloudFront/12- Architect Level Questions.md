# 12- Architect Level Questions

## Overview

Architect-level CloudFront interviews evaluate whether you can design the edge layer as part of a larger distributed system rather than treat CloudFront as an isolated CDN.

The focus shifts from individual features to architectural decisions:

- Where should traffic terminate?
- Which responses should be cached?
- What belongs in the cache key?
- How should private and public traffic be separated?
- How should origins scale and fail over?
- How should CloudFront integrate with WAF, Route 53, ALB, S3, API services, and multi-region infrastructure?
- How should deployments interact with long-lived cached objects?
- How should edge behavior affect consistency, security, observability, and cost?
- Which responsibilities belong at the edge versus the application, cache, database, or messaging layers?

A strong architect-level answer should identify requirements first and then derive the CloudFront architecture from them.

---

## Architect-Level Reasoning Model

A useful framework for CloudFront architecture decisions is:

```text
Traffic
   ↓
Content Classification
   ↓
Cacheability
   ↓
Cache Key
   ↓
Freshness
   ↓
Security
   ↓
Origin Architecture
   ↓
Failure Model
   ↓
Observability
   ↓
Cost
```

For each decision, explicitly discuss the trade-off between:

| Dimension | Architectural Question |
|---|---|
| Latency | Can the response be served at the edge? |
| Correctness | Can stale data be tolerated? |
| Security | Can the response be shared safely? |
| Scalability | How much origin traffic can be eliminated? |
| Availability | What happens if the origin fails? |
| Cost | What is the cost of edge delivery versus origin compute? |
| Operations | Can the team safely operate the configuration? |
| Compliance | Can the content be cached and geographically distributed? |

---

## Question 1: Design a Global Architecture Using CloudFront for a High-Traffic Platform

### Answer

Start by separating edge delivery from application processing.

```mermaid
flowchart TD
    Client((Global Clients))
    DNS[Route 53]
    CF[CloudFront]
    WAF[AWS WAF]

    CF --> WAF

    WAF --> US[US Region]
    WAF --> EU[EU Region]
    WAF --> APAC[APAC Region]

    US --> USLB[Load Balancer]
    EU --> EULB[Load Balancer]
    APAC --> APACLB[Load Balancer]

    USLB --> USAPI[Application]
    EULB --> EUAPI[Application]
    APACLB --> APACAPI[Application]

    Client --> DNS
    DNS --> CF
```

The architecture must then answer several independent questions:

- How is the closest or healthiest origin selected?
- Are all regions active?
- Are writes regional or global?
- How is session state handled?
- How is data replicated?
- What happens during a regional outage?
- What is the acceptable RPO and RTO?
- Which resources can be cached globally?

CloudFront solves the global HTTP delivery layer. It does not automatically solve global application state or database consistency.

---

## Question 2: How Would You Design CloudFront for Active-Active Multi-Region Infrastructure?

### Answer

CloudFront can provide the global edge layer, but active-active architecture requires regional application and data independence.

```mermaid
flowchart TD
    Client((Client))
    CF[CloudFront]

    Client --> CF

    CF --> US[US Region]
    CF --> EU[EU Region]

    US --> USA[Application]
    EU --> EUA[Application]

    USA --> USDB[(US Data)]
    EUA --> EUDB[(EU Data)]

    USDB <-->|Replication| EUDB
```

Before choosing active-active, establish:

- Write ownership
- Replication model
- Conflict resolution
- Session strategy
- Event replication
- Data residency
- Regional failure behavior

Active-active is not automatically better than active-passive. It increases operational and consistency complexity.

Use active-active when the availability, latency, or capacity requirements justify that complexity.

---

## Question 3: How Would You Design CloudFront for an Application With Public and Private Traffic?

### Answer

Separate the traffic classes logically.

```mermaid
flowchart TD
    Client((Client))
    CF[CloudFront]

    Client --> CF

    CF --> Public[Public Content]
    CF --> Private[Private Content]
    CF --> API[Dynamic API]

    Public --> S3[(S3)]
    Private --> PrivateOrigin[Protected Origin]
    API --> App[Django / FastAPI]
```

### Public Content

Examples:

- JavaScript
- CSS
- Images
- Product catalogs
- Documentation

These can often have aggressive caching.

### Private Content

Examples:

- User documents
- Account information
- Personalized recommendations
- Subscription information

These require strict access control and carefully designed cache behavior.

The architectural rule is:

> Never allow personalization or authorization context to accidentally become a shared cache representation.

---

## Question 4: How Would You Design a CloudFront Cache Strategy for a Large API?

### Answer

Do not begin by enabling caching globally.

Classify endpoints.

| API Type | Typical Strategy |
|---|---|
| Public reference data | Long or moderate TTL |
| Public catalog | Moderate TTL |
| Search | Carefully controlled |
| Personalized GET | Usually no shared caching |
| User profile | Usually no shared caching |
| Cart | No shared caching |
| Payment | No caching |
| Authentication | No caching |

For each cacheable endpoint define:

```text
Cache Policy
    ↓
Cache Key
    ↓
TTL
    ↓
Freshness Strategy
    ↓
Invalidation Strategy
```

The architectural objective is not maximum cache hit ratio.

It is:

> Maximum safe origin offload while preserving correctness.

---

## Question 5: How Would You Design the Cache Key for a Multi-Tenant SaaS Platform?

### Answer

The cache key must include every tenant dimension that changes the response.

Suppose:

```http
GET /api/reports
X-Tenant-ID: tenant-a
```

and:

```http
GET /api/reports
X-Tenant-ID: tenant-b
```

return different data.

The tenant identity cannot be ignored when shared caching is used.

Conceptually:

```text
Cache Key =
    Path
    + Tenant Identity
    + Relevant Query Parameters
    + Relevant Headers
```

However, tenant-specific caching can dramatically increase cache cardinality.

For a highly multi-tenant system, an architect should evaluate whether:

- Shared edge caching is actually valuable
- The application cache should handle the data
- The API should return tenant-independent content
- A tenant-specific namespace is required

Security correctness takes precedence over cache efficiency.

---

## Question 6: How Would You Prevent Cache-Key Explosion?

### Answer

Cache-key explosion occurs when too many request dimensions produce distinct cache entries.

For example:

```text
/user-content?country=IN&language=en&device=mobile&theme=dark
/user-content?country=IN&language=en&device=desktop&theme=dark
/user-content?country=US&language=en&device=mobile&theme=light
```

If every attribute enters the cache key, the number of possible representations grows rapidly.

Evaluate each dimension:

| Dimension | Include in Cache Key? |
|---|---|
| Language | Only if representation changes |
| Country | Only if content changes |
| Device | Only if representation changes |
| Tracking parameters | Usually no |
| Authorization | Only with an explicitly safe design |
| Tenant | Required if content differs |
| Feature flags | Usually problematic for shared caching |

Prefer architectural separation of shared and personalized content rather than creating enormous cache keys.

---

## Question 7: How Would You Design CloudFront for a Global E-Commerce Platform?

### Answer

Separate highly cacheable catalog traffic from transactional traffic.

```mermaid
flowchart TD
    User((Customer))
    CF[CloudFront]

    User --> CF

    CF --> Images[Product Images]
    CF --> Catalog[Product Catalog]
    CF --> Search[Search]
    CF --> Cart[Cart]
    CF --> Checkout[Checkout]

    Images --> S3[(S3)]
    Catalog --> CatalogOrigin[Catalog Origin]
    Search --> SearchAPI[Search Service]
    Cart --> CartAPI[Cart Service]
    Checkout --> CheckoutAPI[Checkout Service]

    CartAPI --> Redis[(Redis)]
    CheckoutAPI --> DB[(PostgreSQL)]
```

### Architectural Classification

- Product images: aggressively cacheable
- Product metadata: cacheable depending on freshness
- Search results: carefully designed
- Cart: private and dynamic
- Checkout: never shared
- Payment: never cached

This architecture protects transactional systems from unnecessary public read traffic.

---

## Question 8: How Would You Design CloudFront for a Media Platform?

### Answer

Separate the media delivery plane from the application control plane.

```mermaid
flowchart TD
    User((Viewer))
    CF[CloudFront]

    User --> CF

    CF --> Media[S3 / Media Origin]

    User --> API[Playback API]
    API --> Auth[Authentication]
    API --> Metadata[(Metadata Store)]
```

CloudFront is particularly valuable for high-bandwidth, globally distributed content.

The architecture should separately handle:

- Authentication
- Entitlement
- Content authorization
- Media storage
- Content lifecycle
- Expiring access
- Regional restrictions

Signed URLs or signed cookies can control access to protected media.

The authorization system should remain the source of truth for entitlement.

---

## Question 9: How Would You Architect Private Content Delivery Through CloudFront?

### Answer

Use private origins and controlled authorization.

```mermaid
sequenceDiagram
    participant User
    participant API
    participant CloudFront
    participant Origin

    User->>API: Authenticate
    API->>API: Authorize resource
    API-->>User: Signed access

    User->>CloudFront: Request private resource
    CloudFront->>CloudFront: Validate access
    CloudFront->>Origin: Fetch if needed
    Origin-->>CloudFront: Resource
    CloudFront-->>User: Resource
```

For S3-backed content, use Origin Access Control rather than exposing the bucket publicly.

For private custom origins, protect the origin so users cannot bypass the intended access path.

The architect should explicitly identify:

- Authentication
- Authorization
- Resource ownership
- Expiration
- Revocation requirements
- Origin protection
- Cache behavior

---

## Question 10: How Would You Design CloudFront for a Django or FastAPI Backend?

### Answer

A common architecture is:

```mermaid
flowchart LR
    Client((Client))
    CF[CloudFront]
    WAF[AWS WAF]
    ALB[ALB]
    API[Django / FastAPI]
    Redis[(Redis)]
    DB[(PostgreSQL)]

    Client --> CF
    CF --> WAF
    WAF --> ALB
    ALB --> API

    API --> Redis
    API --> DB
```

Responsibilities should remain separated:

| Layer | Responsibility |
|---|---|
| CloudFront | Global HTTP delivery and caching |
| WAF | Edge security controls |
| ALB | Origin load balancing |
| Django/FastAPI | Business logic |
| Redis | Application-level cache |
| PostgreSQL | Durable state |

An architect should avoid putting business rules into edge functions unless there is a clear architectural reason.

---

## Question 11: When Should Logic Run at the Edge Instead of the Origin?

### Answer

Edge execution is appropriate when:

- The logic is lightweight
- The decision can be made without origin state
- Latency benefits are meaningful
- The logic applies globally
- The operational complexity is justified

Examples include:

- Redirects
- URL normalization
- Header transformations
- Lightweight request routing
- Simple edge decisions

Origin execution is preferable when logic requires:

- Database state
- Complex authorization
- Transactions
- Distributed coordination
- Long-running computation
- Complex business rules

A useful rule is:

> Move logic to the edge when the latency benefit outweighs the additional distributed-system complexity.

---

## Question 12: CloudFront Functions or Lambda@Edge?

### Answer

Choose based on execution requirements rather than preference.

| Requirement | CloudFront Functions | Lambda@Edge |
|---|---|---|
| Simple request transformation | Strong fit | Possible |
| Lightweight redirects | Strong fit | Possible |
| Header manipulation | Strong fit | Possible |
| More complex edge processing | More limited | Better fit |
| Minimal operational complexity | Better | More complex |
| Advanced execution requirements | Limited | Better suited |

The edge should remain intentionally small.

Every additional edge behavior increases the number of locations where engineers must understand, deploy, test, observe, and troubleshoot application behavior.

---

## Question 13: How Would You Protect a CloudFront Origin From Direct Internet Access?

### Answer

The architecture should have a single intended ingress path.

```text
Internet
   |
   v
CloudFront
   |
   v
Protected Origin
```

Avoid:

```text
Internet
   | \
   |  \
   v   v
CloudFront  Origin
```

For S3:

- Keep the bucket private.
- Use Origin Access Control.
- Restrict bucket policy access appropriately.

For custom origins:

- Restrict direct access where the architecture permits.
- Use origin authentication where appropriate.
- Use security controls around the origin.
- Avoid exposing an alternate public endpoint unnecessarily.

The architect should explicitly test whether the origin hostname can be discovered and reached independently.

---

## Question 14: How Would You Design Origin Failover?

### Answer

Define a primary and secondary failure strategy.

```mermaid
flowchart LR
    Client((Client))
    CF[CloudFront]

    CF --> Primary[Primary Origin]
    CF --> Secondary[Secondary Origin]

    Primary --> Health{Healthy?}

    Health -->|Yes| Response[Response]
    Health -->|No| Secondary
```

But failover is only useful if the secondary origin can serve the required content.

Evaluate:

- Data synchronization
- Configuration synchronization
- Deployment synchronization
- Capacity
- TLS configuration
- Authentication
- Cache compatibility
- Regional availability

A secondary origin that is operationally untested is not a reliable disaster-recovery mechanism.

---

## Question 15: How Would You Design CloudFront for a Regional Disaster?

### Answer

Separate edge availability from application recovery.

```mermaid
flowchart TD
    Client((Global Client))
    CF[CloudFront]

    CF --> Primary[Primary Region]
    CF --> DR[DR Region]

    Primary --> App1[Application]
    DR --> App2[Application]

    App1 --> DB1[(Primary Data)]
    App2 --> DB2[(Replicated Data)]
```

Define:

- RTO
- RPO
- Failover trigger
- Data replication mechanism
- Application capacity
- DNS and routing behavior
- Origin configuration
- Operational runbook

CloudFront can participate in the failover path, but the application and data layers determine whether recovery is actually possible.

---

## Question 16: How Would You Handle Cache Invalidation During Emergency Deployment?

### Answer

First determine whether invalidation is actually required.

For immutable assets:

```text
/app.123abc.js
```

deploy:

```text
/app.456def.js
```

No broad invalidation is necessary.

For mutable entry points such as:

```text
/index.html
```

an explicit invalidation may be appropriate.

### Preferred Strategy

```text
Immutable Assets
    ↓
Content Hashing
    ↓
Long TTL
    ↓
No Routine Invalidation
```

Use invalidation primarily for resources whose URL cannot be versioned or where immediate replacement is required.

---

## Question 17: How Would You Design CloudFront for a Zero-Downtime CI/CD Pipeline?

### Answer

Use immutable deployment artifacts wherever possible.

```mermaid
flowchart LR
    Git[Git Repository]
    CI[CI/CD]
    Build[Build]
    Assets[Versioned Assets]
    Origin[Origin Storage]
    CF[CloudFront]

    Git --> CI
    CI --> Build
    Build --> Assets
    Assets --> Origin
    Origin --> CF
```

The deployment sequence should avoid a state where new HTML references assets that have not reached the origin.

A safe pattern is:

1. Build artifacts.
2. Upload new versioned assets.
3. Verify assets.
4. Deploy the new HTML/application version.
5. Invalidate only mutable resources where required.
6. Monitor errors and origin load.

---

## Question 18: How Would You Design CloudFront Cache Policies for a SaaS Platform?

### Answer

Create policies based on resource semantics rather than applying one global policy.

For example:

```text
Public static assets
    → Long TTL

Public reference API
    → Moderate TTL

Tenant-specific API
    → Tenant-aware strategy or no shared caching

User-specific API
    → No shared caching

Administrative API
    → No caching
```

The architect should identify the representation boundary before defining the cache key.

The critical question is:

> Can two users safely receive the same cached representation?

If the answer is no, shared caching must be avoided or explicitly partitioned.

---

## Question 19: How Would You Design CloudFront for a Multi-Tenant API?

### Answer

First determine whether responses are:

- Globally shared
- Tenant-specific
- User-specific

If the response differs by tenant:

```text
Tenant A → Response A
Tenant B → Response B
```

the tenant boundary must be reflected in the caching architecture.

However, putting tenant IDs into the cache key can create a large number of objects.

For high-cardinality SaaS systems, consider:

- Caching shared metadata at CloudFront
- Keeping tenant-specific data at the application layer
- Using Redis for tenant-scoped application caching
- Avoiding CDN caching for highly personalized endpoints

The CDN should not be forced to solve an application-state problem.

---

## Question 20: How Would You Prevent Cache Poisoning in a Large Architecture?

### Answer

Cache poisoning occurs when an attacker causes an unintended representation to become associated with a cache key.

Review every request attribute that can influence the origin response.

Potential dimensions include:

- Host
- Query strings
- Headers
- Cookies
- Authorization
- URL normalization
- Redirect behavior

The architectural principle is:

```text
Response variation
       ↓
Must be represented in
       ↓
Cache identity
```

Also validate and normalize untrusted input before it influences routing or response generation.

A cache configuration should be reviewed as part of the security architecture, not only as a performance configuration.

---

## Question 21: How Would You Diagnose an Origin That Is Still Overloaded Despite CloudFront?

### Answer

Start from the request path.

```text
Client
  ↓
CloudFront
  ↓
Cache Decision
  ↓
Origin
```

Measure:

- Cache hit ratio
- Cache miss volume
- Request rate
- TTL
- Cache-key cardinality
- Query-string variation
- Cookie variation
- Header variation
- Authorization behavior
- Origin response latency

A common failure pattern is:

```text
High Traffic
    ↓
CloudFront
    ↓
Almost Everything Is a Cache Miss
    ↓
Origin Saturation
```

Increasing origin capacity may hide the problem temporarily.

First determine why the CDN cannot reuse responses.

---

## Question 22: How Would You Design CloudFront for API Traffic With Highly Variable Query Parameters?

### Answer

Do not automatically include every query parameter in the cache key.

Suppose:

```text
/search?q=python&page=1&utm_source=google
/search?q=python&page=1&utm_source=email
```

If `utm_source` does not change the result, it should not create separate cache entries.

A better cache identity may be:

```text
/search?q=python&page=1
```

The architect should explicitly classify query parameters as:

| Parameter Type | Cache Key |
|---|---|
| Changes response | Include |
| Tracking only | Usually exclude |
| Security-sensitive | Analyze carefully |
| Pagination | Include |
| Sorting | Include if response changes |
| Feature flag | Include only if representation genuinely differs |

---

## Question 23: How Would You Design CloudFront for Personalized Content?

### Answer

Avoid attempting to cache the entire personalized response.

Instead, separate shared and personalized content.

```mermaid
flowchart TD
    Client((Client))
    CF[CloudFront]

    Client --> CF

    CF --> Shared[Shared Content]
    CF --> Personalized[Personalized API]

    Shared --> Cache[(Edge Cache)]
    Personalized --> API[Django / FastAPI]

    API --> Redis[(Redis)]
    API --> DB[(PostgreSQL)]
```

For example:

```text
Product description → CloudFront
Product image → CloudFront
User recommendation → Application
Shopping cart → Application
```

This maximizes edge reuse without compromising user isolation.

---

## Question 24: How Would You Architect CloudFront With Redis?

### Answer

Treat them as separate caching layers.

```mermaid
flowchart LR
    Client((Client))
    CF[CloudFront]
    API[Application]
    Redis[(Redis)]
    DB[(PostgreSQL)]

    Client --> CF
    CF --> API
    API --> Redis
    Redis --> DB
```

CloudFront answers:

> Can this HTTP representation be reused close to the user?

Redis answers:

> Can the application avoid recomputing or rereading this data?

The two layers may cache different representations with different TTLs.

For example:

```text
CloudFront:
    /api/products → 60 seconds

Redis:
    product:123 → 5 minutes
```

Do not create redundant caching without understanding why each layer exists.

---

## Question 25: How Would You Design CloudFront for a Kubernetes-Based Backend?

### Answer

CloudFront can sit at the external edge while Kubernetes handles application orchestration.

```mermaid
flowchart TD
    Client((Client))
    CF[CloudFront]
    WAF[AWS WAF]
    LB[Load Balancer]
    K8s[Kubernetes]
    Pods[Application Pods]

    Client --> CF
    CF --> WAF
    WAF --> LB
    LB --> K8s
    K8s --> Pods
```

CloudFront should not be responsible for Kubernetes service discovery or internal pod routing.

The responsibilities remain:

- CloudFront: edge delivery
- WAF: security filtering
- Load balancer: origin traffic distribution
- Kubernetes: workload orchestration
- Application: business logic

---

## Question 26: How Would You Design CloudFront for a Microservices Architecture?

### Answer

Do not automatically expose every microservice directly through CloudFront.

A common architecture is:

```mermaid
flowchart TD
    Client((Client))
    CF[CloudFront]
    Gateway[API Gateway / ALB]

    Client --> CF
    CF --> Gateway

    Gateway --> User[User Service]
    Gateway --> Order[Order Service]
    Gateway --> Product[Product Service]
    Gateway --> Payment[Payment Service]
```

CloudFront provides the internet-facing edge layer.

The gateway provides application-level routing.

Internal services communicate through appropriate internal protocols such as REST, gRPC, or asynchronous messaging.

This keeps edge configuration from becoming a service registry.

---

## Question 27: How Would You Design CloudFront for a High-Availability API?

### Answer

The architecture should have independent failure domains.

```mermaid
flowchart TD
    Client((Client))
    CF[CloudFront]
    WAF[AWS WAF]

    Client --> CF
    CF --> WAF

    WAF --> RegionA[Region A]
    WAF --> RegionB[Region B]

    RegionA --> AppA[Application]
    RegionB --> AppB[Application]

    AppA --> DataA[(Data)]
    AppB --> DataB[(Data)]
```

Evaluate availability at every layer:

- CloudFront
- DNS
- WAF
- Load balancer
- Application
- Cache
- Database
- Messaging
- Storage

A highly available CDN does not compensate for a single-region database failure.

---

## Question 28: How Would You Design CloudFront for an API With Strict Freshness Requirements?

### Answer

If stale data is unacceptable, shared caching may provide limited value.

Consider:

- Very short TTLs
- Revalidation
- Conditional requests
- Application-level caching
- Event-driven cache invalidation
- No CDN caching for highly sensitive data

For example:

```text
Stock price
    ↓
Freshness requirement: seconds
    ↓
Very short TTL / no shared cache
```

versus:

```text
Country metadata
    ↓
Freshness requirement: months
    ↓
Long-lived CDN cache
```

Caching strategy should follow correctness requirements, not theoretical cacheability.

---

## Question 29: How Would You Architect CloudFront for a Large Static Website?

### Answer

A common architecture is:

```mermaid
flowchart LR
    User((Global User))
    DNS[Route 53]
    CF[CloudFront]
    S3[S3 Private Bucket]

    User --> DNS
    DNS --> CF
    CF --> S3
```

Use:

- Private S3 bucket
- Origin Access Control
- CloudFront TLS
- Compression
- Long TTLs for immutable assets
- Versioned asset names
- Appropriate invalidation strategy

For a static site, the objective is to make the origin almost irrelevant during normal operation.

---

## Question 30: How Would You Design CloudFront for a Large File Download Platform?

### Answer

Large downloadable objects should generally be stored in durable object storage and distributed through CloudFront.

```mermaid
flowchart LR
    User((User))
    CF[CloudFront]
    S3[(S3)]

    User --> CF
    CF --> S3
```

For private files, use controlled access mechanisms.

Architectural concerns include:

- Range requests
- Download authorization
- Expiration
- Object lifecycle
- Bandwidth cost
- Abuse prevention
- Origin protection

The application should authorize the download without becoming the data-transfer bottleneck.

---

## Question 31: How Would You Handle a CloudFront Configuration Change Safely?

### Answer

Treat CloudFront configuration as production infrastructure.

Use:

- Infrastructure as Code
- Code review
- CI/CD
- Environment separation
- Automated validation
- Controlled rollout
- Monitoring

A conceptual workflow:

```mermaid
flowchart LR
    Change[Configuration Change]
    PR[Code Review]
    CI[CI Validation]
    Deploy[Deployment]
    Monitor[Monitoring]
    Rollback[Rollback]

    Change --> PR
    PR --> CI
    CI --> Deploy
    Deploy --> Monitor
    Monitor --> Rollback
```

Avoid making undocumented production changes through the console.

The exact operational workflow can vary, but the configuration should remain reproducible.

---

## Question 32: How Would You Integrate CloudFront With CI/CD?

### Answer

Store CloudFront configuration in version-controlled infrastructure code.

The deployment pipeline should control:

- Distribution configuration
- Cache policies
- Origin configuration
- Response headers policies
- Edge functions
- WAF associations
- Invalidation where required

The pipeline should distinguish between:

```text
Infrastructure deployment
```

and:

```text
Application deployment
```

This allows teams to reason about changes independently and roll them back safely.

---

## Question 33: How Would You Design CloudFront for a System With Strict Compliance Requirements?

### Answer

First determine whether the data is permitted to be cached and geographically distributed.

Questions include:

- Is the data sensitive?
- Is personal information involved?
- Are there geographic restrictions?
- Can the representation be stored at edge locations?
- Does the application need regional processing?
- Are logs subject to retention requirements?

For sensitive content, avoiding shared caching may be the correct architectural decision.

Compliance requirements should influence:

- Cacheability
- Origin selection
- Logging
- Data retention
- Encryption
- Access control
- Geographic architecture

---

## Question 34: How Would You Design CloudFront for Disaster Recovery?

### Answer

CloudFront should be part of the recovery architecture rather than the entire strategy.

```text
Global Client
      |
      v
CloudFront
      |
      +---- Primary Region
      |
      +---- Recovery Region
```

Define:

- RPO
- RTO
- Origin failover
- Data replication
- Application recovery
- Configuration recovery
- Deployment recovery
- Operational ownership

The architect should verify that every dependency can recover within the required RTO.

---

## Question 35: How Would You Design CloudFront for Cost Optimization at Very High Scale?

### Answer

Start with traffic economics.

```text
Total Requests
      |
      +--> Cache Hits
      |
      +--> Cache Misses
              |
              +--> Origin Compute
              +--> Database
```

Optimize:

- Cache hit ratio
- Cache-key cardinality
- Response size
- Compression
- Image optimization
- Origin request volume
- Asset TTL
- Data transfer

A useful architectural metric is:

```text
Origin Offload Ratio
=
1 - (Origin Requests / Total Requests)
```

Do not optimize only the CloudFront bill.

The correct objective is:

> Minimize total system cost while preserving required latency, availability, and correctness.

---

## Question 36: How Would You Design CloudFront for a Traffic Spike of 100x Normal Volume?

### Answer

First classify the traffic.

If it is cacheable:

```text
100x Traffic
    ↓
CloudFront
    ↓
Most requests served from edge
    ↓
Limited origin traffic
```

If it is dynamic:

```text
100x Traffic
    ↓
CloudFront
    ↓
100x Origin Requests
    ↓
Origin Saturation
```

For dynamic traffic, combine:

- CloudFront
- WAF
- Rate limiting
- Autoscaling
- Load balancing
- Redis
- Database protection
- Queueing where appropriate

The architect must determine whether the system can absorb the expected cache-miss rate.

---

## Question 37: How Would You Design CloudFront to Protect a Database During a Read Spike?

### Answer

Prevent unnecessary requests from reaching the database.

```mermaid
flowchart TD
    User((Users))
    CF[CloudFront]
    API[Application]
    Redis[(Redis)]
    DB[(PostgreSQL)]

    User --> CF
    CF --> API
    API --> Redis
    Redis --> DB
```

Use multiple layers:

1. CloudFront for globally reusable HTTP responses.
2. Redis for application-level data reuse.
3. Application optimization for expensive computations.
4. Database indexing and query optimization.
5. Read replicas where appropriate.

CloudFront should reduce traffic before it becomes an application problem.

---

## Question 38: How Would You Design CloudFront for a Read-Heavy Microservice?

### Answer

A read-heavy service is a strong candidate for CDN caching if its responses are safe to share.

```text
Client
  ↓
CloudFront
  ↓
Read API
  ↓
Redis
  ↓
Database
```

The hierarchy provides progressive offloading:

```text
Edge Cache
    ↓
Application Cache
    ↓
Database
```

The architect should define TTLs independently at each layer.

Avoid synchronized expiration of every cache layer if it could cause a thundering herd against the database.

---

## Question 39: How Would You Handle Cache Stampede at Scale?

### Answer

Cache stampede occurs when many requests simultaneously miss or expire the same object.

For example:

```text
10:00:00
     ↓
Popular object expires
     ↓
Thousands of requests miss
     ↓
Thousands hit origin
```

Mitigation strategies include:

- Appropriate TTL design
- Staggered expiration
- Application-level request coalescing
- Redis locking where appropriate
- Background refresh
- Origin capacity planning
- Avoiding synchronized cache invalidation

The key architectural goal is to prevent a cache expiration event from becoming an origin outage.

---

## Question 40: How Would You Design CloudFront for a Multi-Layer Caching Architecture?

### Answer

Explicitly define the responsibility of each cache.

```mermaid
flowchart LR
    Client((Client))
    CF[CloudFront]
    API[Django / FastAPI]
    Redis[(Redis)]
    DB[(PostgreSQL)]

    Client --> CF
    CF --> API
    API --> Redis
    Redis --> DB
```

| Layer | Cached Representation |
|---|---|
| Browser | Client-side representation |
| CloudFront | HTTP response |
| Redis | Application data |
| Database | Durable state / query results where applicable |

Do not duplicate the same object at every layer without understanding invalidation.

The hardest part of multi-layer caching is often not reading from cache.

It is keeping all layers acceptably fresh.

---

## Question 41: How Would You Design Cache Invalidation for a Distributed System?

### Answer

Prefer immutable resources where possible.

For mutable resources, establish a clear invalidation ownership model.

```mermaid
flowchart TD
    Change[Data Change]
    Event[Domain Event]
    AppCache[Application Cache]
    CDN[CDN Invalidation]
    Origin[Origin]

    Change --> Event
    Event --> AppCache
    Event --> CDN
    Event --> Origin
```

However, not every database update should trigger a CDN invalidation.

For highly dynamic data, short TTLs may be simpler and more reliable than trying to synchronously invalidate globally distributed objects.

The architect should choose between:

- TTL-based freshness
- Event-driven invalidation
- Versioned resources
- Explicit invalidation

based on business requirements.

---

## Question 42: How Would You Handle CloudFront During a Major Security Incident?

### Answer

Use CloudFront and WAF as protective layers rather than relying solely on application defenses.

```text
Internet
   |
   v
CloudFront
   |
   v
AWS WAF
   |
   v
Origin
```

Incident response should include:

1. Identify attack patterns.
2. Inspect CloudFront traffic.
3. Inspect WAF activity.
4. Identify affected paths.
5. Rate-limit or block malicious traffic.
6. Protect expensive origin endpoints.
7. Monitor origin saturation.
8. Preserve logs.
9. Validate mitigation.
10. Remove temporary controls after the incident.

Do not blindly disable caching during an attack. Existing cached content may reduce origin exposure.

---

## Question 43: How Would You Decide What Belongs at CloudFront Versus the Application?

### Answer

Use the following decision model:

| Requirement | Edge | Application |
|---|---:|---:|
| URL redirect | Yes | Sometimes |
| Header transformation | Yes | Sometimes |
| Static delivery | Yes | No |
| Public response caching | Yes | Sometimes |
| Database lookup | No | Yes |
| Transaction | No | Yes |
| Complex authorization | Usually no | Yes |
| Payment processing | No | Yes |
| Business rules | Usually no | Yes |
| Lightweight request routing | Yes | Sometimes |

The edge should contain only logic that benefits materially from edge execution.

Distributed execution is not free from an operational perspective.

---

## Question 44: How Would You Explain CloudFront's Role in a System Design Interview?

### Answer

A strong architect-level explanation is:

> CloudFront is the globally distributed edge layer responsible for delivering HTTP content close to users, reducing origin traffic through safe caching, enforcing edge-level security controls, and providing a scalable ingress point for internet-facing applications. I would design cache policies around response semantics, explicitly define the cache key and freshness requirements, protect the origin from bypass traffic, and separate public cacheable content from personalized or transactional workloads. CloudFront can participate in multi-region failover, but application state, database consistency, and disaster recovery must be designed independently.

This answer demonstrates architectural understanding rather than feature memorization.

---

## Architecture Decision Matrix

| Requirement | Recommended Direction |
|---|---|
| Global static assets | CloudFront + private S3 origin |
| Public read-heavy API | CloudFront with carefully scoped caching |
| Personalized API | Usually bypass shared CDN cache |
| Private media | CloudFront + signed access |
| Multi-region API | CloudFront + independently resilient regional origins |
| High-volume images | CloudFront + object storage |
| Transactional API | No shared response caching |
| Edge redirects | CloudFront Functions where appropriate |
| Complex edge processing | Lambda@Edge where justified |
| Application data caching | Redis |
| Durable state | PostgreSQL / appropriate datastore |
| Internal service communication | REST / gRPC / messaging |
| Origin protection | OAC, network controls, authentication, WAF |

---

## Architect-Level CloudFront Review Checklist

Before approving a production CloudFront architecture, verify:

### Traffic

- What percentage of traffic is static?
- What percentage is cacheable?
- What percentage is personalized?
- What is the expected peak traffic?

### Cache

- What is the cache key?
- Which headers are included?
- Which query parameters are included?
- Which cookies are included?
- What is the TTL?
- What is the freshness requirement?
- What is the invalidation strategy?

### Security

- Can the origin be accessed directly?
- Can private responses become shared cache entries?
- Is origin access controlled?
- Is WAF integrated where appropriate?
- Are signed URLs or cookies required?

### Reliability

- What happens when the origin fails?
- Is there an alternate origin?
- Is the application multi-region?
- What are the RPO and RTO?
- Has failover been tested?

### Performance

- What is the expected cache hit ratio?
- Is the cache key unnecessarily fragmented?
- Are responses compressed?
- Are assets versioned?
- Is the origin protected from cache stampedes?

### Cost

- What is the expected data transfer?
- What is the origin request volume?
- How much compute is saved by caching?
- Are large responses optimized?
- Is unnecessary invalidation being avoided?

### Operations

- Is CloudFront managed through Infrastructure as Code?
- Are changes code-reviewed?
- Is configuration deployed through CI/CD?
- Are CloudFront, WAF, ALB, and application metrics correlated?
- Is there a documented rollback strategy?

---

## Common Architect-Level Mistakes

### Treating CloudFront as a Universal Cache

Not every response is safe to share.

**Avoid it:** classify resources according to their semantics and personalization requirements.

### Designing for Cache Hit Ratio Alone

A high hit ratio can still represent incorrect or stale data.

**Avoid it:** optimize for safe origin offload while preserving correctness.

### Ignoring Origin Bypass

A CDN cannot protect an origin that remains directly accessible.

**Avoid it:** explicitly design and test the origin access path.

### Putting Business Logic at the Edge

Edge execution can make simple logic faster but can also distribute application complexity.

**Avoid it:** keep edge logic small and deterministic.

### Using Multi-Region Without a Data Strategy

Two regions do not automatically provide a consistent application.

**Avoid it:** define data ownership, replication, consistency, RPO, and RTO.

### Invalidating Everything After Every Deployment

Broad invalidations are often unnecessary for immutable assets.

**Avoid it:** use content-addressed or versioned asset names.

### Treating CloudFront and Redis as the Same Cache

They solve different problems.

**Avoid it:** define the representation and responsibility of each caching layer.

---

## Key Takeaways

- **CloudFront architecture should be derived from traffic semantics, cacheability, security, freshness, origin behavior, and failure requirements—not from CDN features alone.**
- **The cache key is a correctness boundary: every response-changing dimension must be represented, while irrelevant dimensions should be excluded to prevent fragmentation.**
- **CloudFront can provide global delivery and participate in origin failover, but multi-region application state, database consistency, disaster recovery, and RPO/RTO require independent architectural design.**
- **Edge execution should remain intentionally small; business logic, transactions, complex authorization, and stateful processing generally belong at the application layer.**
- **An architect-level design must optimize the entire system—latency, origin offload, availability, security, operational complexity, and total cost—not CloudFront metrics in isolation.**