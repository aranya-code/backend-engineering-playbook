# 07- Architecture Decision Matrix

## Overview

A CloudFront architecture should be selected based on workload characteristics rather than by applying the same CDN pattern to every application.

The central architectural decision is not simply whether to use CloudFront. It is how CloudFront should interact with the application's origins, caching model, security controls, availability strategy, and deployment process.

A production decision typically evaluates:

- Content type.
- Cacheability.
- Request personalization.
- Origin type.
- Origin availability requirements.
- Geographic traffic distribution.
- Security requirements.
- Performance targets.
- Cost constraints.
- Operational complexity.
- Disaster recovery requirements.

The same CloudFront distribution can support multiple behaviors and origins, but combining too many responsibilities without clear boundaries can make cache behavior, security, and troubleshooting difficult.

## Decision Framework

A practical decision process is:

```mermaid
flowchart TD
    Start[Workload] --> Content{What is being served?}

    Content -->|Static assets| Static[S3 + CloudFront]
    Content -->|Media / downloads| Media[S3 + CloudFront]
    Content -->|Dynamic API| API{Is response safely cacheable?}
    Content -->|Dynamic web app| Web[CloudFront + ALB]

    API -->|Yes| Cached[Controlled API caching]
    API -->|No| Dynamic[CloudFront + ALB without caching]

    Web --> HA{Availability requirement}
    Dynamic --> HA
    Cached --> HA

    HA -->|Single region| Regional[Multi-AZ regional origin]
    HA -->|Multi-region| MultiRegion[Multi-region architecture]

    MultiRegion --> Failover{Failover requirement}
    Failover -->|Origin failover| OriginFailover[CloudFront origin failover]
    Failover -->|Global traffic steering| GlobalRouting[Global routing architecture]
```

The objective is to choose the simplest architecture that satisfies the actual requirements.

## Architecture Decision Dimensions

| Dimension | Low Complexity | Higher Complexity |
|---|---|---|
| Content | Static | Personalized dynamic |
| Origin | Single origin | Multiple origins |
| Availability | Single region | Multi-region |
| Caching | Long-lived immutable assets | Personalized API responses |
| Security | Public content | Private authenticated content |
| Traffic | Regional | Global |
| Deployment | Manual | Automated CI/CD |
| Recovery | Basic | Formal RTO/RPO |
| Operations | Simple | Multi-layer observability |

Complexity should be introduced only when it solves a concrete requirement.

## Static Content Decision

### Recommended Architecture

```text
Client
  │
  ▼
CloudFront
  │
  ▼
S3
```

Use this architecture for:

- JavaScript bundles.
- CSS.
- Images.
- Static HTML.
- Documentation.
- Public assets.

### Why

S3 provides durable object storage while CloudFront provides edge delivery and caching.

The application servers do not need to participate in every static-content request.

### Decision Matrix

| Requirement | Recommendation |
|---|---|
| Mostly immutable assets | CloudFront + S3 |
| Global users | CloudFront |
| High cacheability | Long TTL |
| Frequent asset changes | Versioned filenames |
| Private assets | CloudFront + private S3 |
| Simple static website | CloudFront + S3 |

## Static Asset Versioning Decision

For assets such as:

```text
app.js
styles.css
```

prefer:

```text
app.8d7c1a.js
styles.1b93f4.css
```

This allows aggressive caching without requiring frequent invalidation.

A typical deployment becomes:

```text
Build
  │
  ▼
Generate hashed assets
  │
  ▼
Upload to S3
  │
  ▼
Publish new HTML
  │
  ▼
CloudFront serves new asset references
```

### Decision

| Requirement | Preferred Approach |
|---|---|
| Immutable assets | Filename versioning |
| Frequently changing HTML | Shorter HTML TTL |
| Emergency content removal | Invalidation |
| Large asset fleet | Versioning over repeated invalidations |

Invalidation remains useful, but it should not be the primary deployment mechanism for every static resource.

## Dynamic API Decision

Dynamic APIs require a different evaluation.

Consider:

```text
GET /api/products
GET /api/profile
GET /api/orders
```

These endpoints do not necessarily have the same caching requirements.

| API Type | Typical CloudFront Strategy |
|---|---|
| Public catalog | Controlled caching |
| Public documentation API | Controlled caching |
| Personalized profile | Usually no caching |
| Orders | Usually no caching |
| Payments | No caching |
| Admin API | Usually no caching |
| Public configuration | Potentially cacheable |

The primary question is:

> Can the response safely be reused for another request?

If the answer is no, do not cache the response merely to improve performance.

## API Cache Decision Matrix

| Property | Cache-Friendly | Cache-Unfriendly |
|---|---|---|
| Public | Yes | No |
| Personalized | No | Yes |
| Read-heavy | Yes | No |
| Frequently mutated | No | Yes |
| Same response for many users | Yes | No |
| Sensitive data | Usually no | Yes |
| Deterministic response | Yes | No |
| Short freshness requirement | Potentially | Often no |

A cacheable API might look like:

```text
GET /api/products/123
```

whereas:

```text
GET /api/account/orders
Authorization: Bearer ...
```

usually requires much more careful handling.

## CloudFront + ALB Decision

A common backend architecture is:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
ALB
   │
   ▼
Django / FastAPI
```

Use this pattern when the application benefits from:

- Global edge connectivity.
- Edge caching.
- WAF integration.
- TLS termination at the edge.
- Reduced origin bandwidth.
- A unified public endpoint.

The ALB remains responsible for regional load balancing.

CloudFront does not replace the ALB's role inside the regional application architecture.

## CloudFront + Nginx + Application

A more layered deployment may look like:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
ALB
   │
   ▼
Nginx
   │
   ▼
Gunicorn / Uvicorn
   │
   ▼
Django / FastAPI
```

This can be valid, but every layer should have a reason to exist.

For example:

| Layer | Responsibility |
|---|---|
| CloudFront | Global edge |
| ALB | Regional load balancing |
| Nginx | Reverse proxy / HTTP handling |
| Gunicorn | Django process management |
| Uvicorn | ASGI serving |
| Django/FastAPI | Application logic |

Do not introduce Nginx merely because CloudFront exists.

## S3 vs Application Origin

A frequent architectural decision is whether content should come from S3 or the application.

| Content | Preferred Origin |
|---|---|
| Static JavaScript | S3 |
| CSS | S3 |
| Public images | S3 |
| User-uploaded media | S3 |
| Large downloads | S3 |
| Business API | ALB / application |
| Authentication | Application |
| Transaction processing | Application |
| Database-backed dynamic page | Application |

The application should generally own business logic while S3 owns object storage.

## Private Content Decision

Private files require a separate security decision.

A common pattern is:

```text
User
  │
  ▼
Django / FastAPI
  │
  │ authorize
  ▼
Signed CloudFront URL
  │
  ▼
CloudFront
  │
  ▼
Private S3
```

Use this architecture when:

- Files are user-specific.
- Downloads require authorization.
- Large files should not traverse application servers.
- The S3 bucket should remain private.

The application performs authorization before granting access.

CloudFront then performs efficient delivery.

## Media and Download Decision Matrix

| Workload | Recommended Architecture |
|---|---|
| Public images | S3 + CloudFront |
| Private documents | Private S3 + controlled CloudFront access |
| Large reports | S3 + CloudFront |
| User uploads | S3 |
| Video segments | S3 + CloudFront |
| Dynamically generated report | Worker → S3 → CloudFront |
| Small JSON API response | Application origin |

For large files, avoid designs such as:

```text
Client → Django → Generate → Stream 500 MB
```

Prefer:

```text
Client → API → Create Job
                 │
                 ▼
              Worker
                 │
                 ▼
                S3
                 │
                 ▼
             CloudFront
```

## Multi-Origin Decision

Use multiple origins when different request classes require different infrastructure.

Example:

```text
CloudFront
   │
   ├── /static/*   → S3
   ├── /media/*    → S3
   ├── /api/*      → ALB
   └── /downloads/* → S3
```

This is generally preferable to routing every request through a single application origin.

### Decision Matrix

| Requirement | Single Origin | Multiple Origins |
|---|---:|---:|
| Small application | Preferred | Usually unnecessary |
| Static + API | Possible | Preferred |
| Media + API | Possible | Preferred |
| Multiple backend platforms | Difficult | Preferred |
| Different cache policies | Limited | Preferred |
| Independent origin scaling | Limited | Preferred |

Multiple origins introduce additional routing and operational complexity, so they should be justified by workload separation.

## Origin Groups and Failover

Origin groups are appropriate when an origin-level failure should cause CloudFront to try another origin.

```text
CloudFront
     │
     ▼
Primary Origin
     │
     ├── Success → Client
     │
     └── Failure
            │
            ▼
      Secondary Origin
            │
            ▼
          Client
```

Use this when:

- A secondary origin is genuinely available.
- The secondary contains equivalent content or functionality.
- Failover behavior is tested.
- The application can operate correctly against the secondary.

Do not configure a secondary origin merely to satisfy an availability checklist.

A secondary origin that is stale, untested, or missing dependencies does not provide meaningful resilience.

## Single-Region vs Multi-Region

### Single Region

```text
CloudFront
    │
    ▼
ALB
    │
    ▼
Multi-AZ Application
```

This is usually the preferred starting point.

Use it when:

- Regional failure is outside the availability target.
- The application's RTO/RPO does not justify multi-region complexity.
- Database architecture is regional.
- Operational simplicity is important.

### Multi-Region

```text
                 CloudFront
                 /        \
                ▼          ▼
           Region A      Region B
              │             │
             ALB           ALB
              │             │
             App           App
```

Use multi-region when requirements justify:

- Regional disaster recovery.
- Lower latency for globally distributed users.
- Regional isolation.
- Business continuity requirements.

The application and data layers must also support the model.

## Multi-Region Decision Matrix

| Requirement | Single Region | Multi-Region |
|---|---:|---:|
| Regional users | Preferred | Usually unnecessary |
| Global users | Possible | Potentially beneficial |
| Strict regional DR | Limited | Preferred |
| Low operational complexity | Preferred | No |
| Low RTO for regional failure | Limited | Preferred |
| Strong cross-region consistency | Simpler | More difficult |
| Cost sensitivity | Preferred | Higher |
| Database complexity tolerance | Lower | Higher |

Multi-region should be an explicit architectural decision, not a default assumption.

## Multi-Region Data Considerations

CloudFront can distribute requests globally, but it does not solve data consistency.

For example:

```text
Region A
  │
  └── PostgreSQL A

Region B
  │
  └── PostgreSQL B
```

The architecture must answer:

- Which region accepts writes?
- Is replication synchronous or asynchronous?
- What happens during network partition?
- What is the acceptable data-loss window?
- How does failover happen?
- How are conflicting writes handled?
- How are background jobs coordinated?

A multi-region application without a defined data strategy is incomplete.

## Availability Decision Matrix

| Requirement | Architecture |
|---|---|
| Basic availability | Single-region CloudFront + ALB |
| AZ failure tolerance | Multi-AZ application |
| Origin failure | Origin group |
| Regional disaster recovery | Multi-region origins |
| Global active-active | Multi-region application + data strategy |
| Static-content resilience | Replicated object storage |
| Large-file delivery | S3 + CloudFront |

The required availability target should drive the architecture.

## Security Decision Matrix

| Requirement | Recommended Control |
|---|---|
| HTTPS | CloudFront viewer TLS |
| Web attack filtering | AWS WAF |
| Private S3 | CloudFront origin access control |
| Authentication | Application / identity layer |
| Authorization | Application |
| DDoS protection | AWS edge protections + WAF where appropriate |
| Origin bypass prevention | Origin access restrictions |
| Sensitive API responses | Avoid unsafe caching |

A key architectural rule is:

```text
CDN security
    ≠
Application authorization
```

CloudFront can protect the edge, but it should not become the sole authority for business permissions.

## Cache Policy Decision Matrix

| Workload | TTL Strategy | Cache Key Complexity |
|---|---|---|
| Hashed JS/CSS | Long | Low |
| Public images | Long | Low |
| Public API | Moderate | Moderate |
| Personalized API | Usually disabled | High |
| Frequently changing content | Short | Moderate |
| Sensitive transactional API | Disabled | Avoided |

The cache key should contain the minimum request attributes required to produce a correct response.

Overly broad cache keys can cause data leakage.

Overly broad variation can destroy the cache hit ratio.

## Cache Key Trade-Off

Consider an endpoint:

```text
GET /api/products
```

If the response varies only by:

```text
Accept-Language
```

then the cache key may need language variation.

If it varies by:

```text
User ID
Tenant ID
Authorization
Locale
Feature flags
```

the cache key becomes significantly more complex.

At some point, the correct architectural decision may be:

```text
Do not cache this endpoint.
```

This is often better than creating a fragile cache model.

## Deployment Decision Matrix

CloudFront architecture should also account for deployments.

### Immutable Assets

```text
Build
  │
  ▼
app.8d7c1a.js
  │
  ▼
S3
  │
  ▼
CloudFront
```

Preferred for:

- Frontend bundles.
- CSS.
- Static images.
- Versioned application resources.

### Mutable Content

For mutable content where immediate replacement is required:

```text
Deploy
  │
  ▼
Update object
  │
  ▼
Invalidate affected paths
```

Use invalidation selectively.

A high volume of invalidations can indicate that asset versioning should be improved.

## Architecture Selection by Workload

| Workload | Recommended Starting Architecture |
|---|---|
| Static website | CloudFront + S3 |
| React SPA | CloudFront + S3 |
| Django web application | CloudFront + ALB |
| FastAPI REST API | CloudFront + ALB |
| Static + API application | CloudFront + S3 + ALB |
| Private media | CloudFront + private S3 |
| Large downloads | CloudFront + S3 |
| Global API | CloudFront + multi-region origins if justified |
| Kubernetes application | CloudFront + ALB + Kubernetes |
| Multi-region DR | CloudFront + regional origins |
| Highly personalized API | CloudFront for edge/security, generally no response caching |

## Decision Matrix: CloudFront vs Direct Origin

| Requirement | Direct Origin | CloudFront |
|---|---:|---:|
| Global users | Weak | Strong |
| Static caching | Limited | Strong |
| Edge delivery | No | Yes |
| Custom TLS edge | Limited | Strong |
| WAF integration | Possible elsewhere | Strong |
| Origin bandwidth reduction | No | Potentially significant |
| Very low traffic | Simpler | Additional layer |
| Highly personalized traffic | Simpler | Still useful for edge/security |
| Global media | Weak | Strong |

CloudFront is not automatically required for every internal or low-volume application.

For a private internal service with controlled network access and limited geographic distribution, direct access through an appropriate internal architecture may be simpler.

## Decision Matrix: S3 vs ALB vs Application

| Requirement | S3 | ALB + Application |
|---|---:|---:|
| Static files | Excellent | Poor fit |
| Large objects | Excellent | Poor fit |
| Object durability | Excellent | Not its responsibility |
| Business logic | No | Excellent |
| Authentication | Limited | Excellent |
| Database queries | No | Excellent |
| Transaction processing | No | Excellent |
| API responses | Limited | Excellent |

The architectural boundary should remain clear:

```text
Object storage
    ↓
S3

Business behavior
    ↓
Application
```

## Performance Decision Matrix

| Optimization | Best Use |
|---|---|
| Edge caching | Reusable content |
| Compression | Textual assets and responses |
| Asset versioning | Immutable deployments |
| Origin separation | Different traffic classes |
| S3 for media | Large-object delivery |
| API caching | Public read-heavy APIs |
| Regional origins | Global application traffic |

Performance improvements should be measured against:

- Viewer latency.
- Cache hit ratio.
- Origin latency.
- Origin request volume.
- Application CPU.
- Application memory.
- Database load.
- Network transfer.

A faster edge response is not useful if the cache strategy introduces stale or incorrect data.

## Reliability Decision Matrix

| Failure | Possible Mitigation |
|---|---|
| Edge issue | CloudFront's distributed infrastructure |
| Origin instance failure | ALB + multiple instances |
| AZ failure | Multi-AZ deployment |
| Primary origin failure | Origin group |
| Regional failure | Multi-region architecture |
| Object availability issue | Replication / resilient storage |
| Application dependency failure | Dependency-specific fallback |
| Database failure | Database HA/DR architecture |

Reliability must be considered as an end-to-end property.

```text
CloudFront
   ↓
ALB
   ↓
Application
   ↓
Redis / PostgreSQL / Kafka
   ↓
External dependencies
```

The weakest critical dependency can determine practical availability.

## Cost Decision Matrix

| Workload | Cost Consideration |
|---|---|
| Highly cacheable static content | CloudFront can reduce origin traffic |
| Low-cacheability API | Benefits may be primarily security/edge-related |
| Large media | CDN can reduce repeated origin transfers |
| Multi-region | Higher infrastructure and data-transfer cost |
| Multiple distributions | More operational complexity |
| Frequent invalidation | Review deployment/versioning strategy |

Do not optimize CloudFront cost independently of origin cost.

The relevant metric is often total system cost:

```text
CloudFront
+ S3
+ ALB
+ Compute
+ Database
+ Network transfer
+ Operations
```

## Operational Complexity Matrix

| Architecture | Complexity | Typical Use |
|---|---|---|
| CloudFront + S3 | Low | Static applications |
| CloudFront + ALB | Moderate | Backend applications |
| CloudFront + S3 + ALB | Moderate | Full-stack applications |
| Multi-origin | Moderate | Mixed workloads |
| Origin failover | High | DR requirements |
| Multi-region | High | Regional resilience |
| Multi-region active-active | Very High | Mission-critical global workloads |

The most senior architectural decision is often knowing when **not** to add another layer.

## Common Decision Mistakes

### Choosing Multi-Region Too Early

Multi-region introduces:

- More infrastructure.
- More deployments.
- More monitoring.
- More networking.
- More failure modes.
- More database complexity.

Start with the simplest architecture that satisfies the availability target.

### Caching Because It Is Technically Possible

Caching a response does not make it correct.

First determine:

```text
Can the response be reused safely?
```

Then determine:

```text
How long can it remain fresh?
```

### Treating All APIs Identically

A public catalog API and a payment API should not automatically share the same cache policy.

### Using Application Servers for Object Delivery

Large static files and media can unnecessarily consume application resources.

Prefer object storage and CDN delivery where appropriate.

### Creating Multiple Origins Without Clear Boundaries

More origins increase configuration complexity.

Each origin should have a clear responsibility.

### Assuming CloudFront Provides Complete Disaster Recovery

CloudFront can provide an edge layer and origin failover mechanisms, but application state, databases, queues, and external dependencies still require independent recovery strategies.

### Ignoring Direct Origin Access

If an origin remains publicly reachable, users may bypass CloudFront.

Evaluate whether that bypass is acceptable.

## Architecture Review Checklist

### Workload

- [ ] Traffic classes have been identified.
- [ ] Static, dynamic, media, and API workloads are separated where appropriate.
- [ ] Cacheability has been explicitly evaluated.
- [ ] Personalized responses are protected from unsafe caching.

### Origins

- [ ] Every origin has a defined responsibility.
- [ ] S3 is used for suitable object-storage workloads.
- [ ] ALB/application origins are used for business logic.
- [ ] Origin health is measurable.
- [ ] Direct origin access is intentionally controlled.

### Caching

- [ ] Cache policies match response semantics.
- [ ] Cache keys include all required variation.
- [ ] Sensitive responses are not accidentally cached.
- [ ] Static assets use versioned filenames where practical.
- [ ] TTLs match freshness requirements.

### Availability

- [ ] Availability requirements are documented.
- [ ] Multi-AZ deployment is used where required.
- [ ] Origin failover is tested if configured.
- [ ] Multi-region architecture is justified by an explicit requirement.
- [ ] RTO and RPO are documented.
- [ ] Database recovery is part of the design.

### Security

- [ ] HTTPS is enforced.
- [ ] WAF requirements are evaluated.
- [ ] Private S3 origins use appropriate access controls.
- [ ] Authentication remains separate from CDN caching.
- [ ] Authorization remains enforced by the application.
- [ ] Origin bypass paths are controlled.

### Performance

- [ ] Cache hit ratio is measured.
- [ ] Origin latency is monitored.
- [ ] Static assets are aggressively cacheable where safe.
- [ ] Large-object delivery does not unnecessarily traverse application servers.
- [ ] Global latency requirements are documented.

### Operations

- [ ] CloudFront metrics are monitored.
- [ ] Origin metrics are monitored.
- [ ] Application metrics are correlated with edge behavior.
- [ ] Deployment and invalidation procedures are documented.
- [ ] Failover procedures are tested.
- [ ] Cost is monitored at the architecture level.

## Interview Traps

### Should every application use CloudFront?

No. The architecture should justify the CDN based on global delivery, caching, security, performance, or other requirements.

### Is CloudFront primarily a static-file service?

No. It can serve static content and front dynamic applications and APIs.

### Does CloudFront automatically make an application multi-region?

No. Multi-region availability requires regional application infrastructure and an appropriate data strategy.

### Should authenticated APIs always bypass CloudFront?

Not necessarily. CloudFront can still provide useful edge and security capabilities, but response caching for personalized data requires careful design.

### Is a cache hit always better than a cache miss?

Only if the cached response is correct and sufficiently fresh.

### Does using multiple origins automatically improve availability?

No. Multiple origins help only when the secondary origin is operationally ready and the failover mechanism is correctly configured and tested.

### Should every static deployment invalidate `/*`?

Usually not. Immutable asset versioning is generally a better strategy for frequently deployed frontend assets.

### Can CloudFront replace an ALB?

Not as a general rule. CloudFront provides edge delivery while the ALB provides regional load balancing and application-origin integration.

## Key Takeaways

- **Choose CloudFront architecture from workload characteristics:** content type, cacheability, personalization, origin requirements, security, and availability should drive the design.
- **Prefer the simplest architecture that satisfies the requirement:** CloudFront + S3 is often sufficient for static content, while dynamic applications commonly use CloudFront + ALB.
- **Treat caching as a correctness decision:** cache keys, TTLs, authentication, personalization, and data sensitivity must be evaluated before enabling API caching.
- **Multi-region and origin failover solve specific availability problems but add significant operational and data complexity:** they should be justified by explicit RTO, RPO, latency, or business-continuity requirements.
- **Evaluate CloudFront as part of the entire system:** performance, security, reliability, observability, and cost must be assessed across CloudFront, origins, databases, queues, storage, and application infrastructure.