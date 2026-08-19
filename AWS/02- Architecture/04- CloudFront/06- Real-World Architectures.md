# 06- Real-World Architectures

## Overview

CloudFront is most valuable when it is treated as an architectural layer rather than simply a CDN for static files.

In production systems, CloudFront commonly sits at the edge of an architecture containing object storage, load balancers, API services, serverless workloads, Kubernetes clusters, and multi-region origins. The correct design depends on the traffic type, caching requirements, security model, origin characteristics, and availability objectives.

A typical production architecture looks like:

```text
                         Internet Users
                              │
                              ▼
                         CloudFront
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
              S3 Assets     ALB API     Media Origin
                              │
                              ▼
                       Django / FastAPI
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
             PostgreSQL     Redis       Kafka
```

The important architectural principle is to avoid forcing every request through the same origin or caching strategy.

Static assets, public APIs, authenticated APIs, uploads, downloads, and dynamic application pages usually have different performance and security characteristics.

## Architectural Design Principles

A production CloudFront architecture should answer several questions before implementation:

| Question | Architectural Concern |
|---|---|
| What traffic is being served? | Static, dynamic, API, media, downloads |
| Can the response be cached? | Cache policy and TTL |
| Is authentication required? | Headers, cookies, authorization |
| What is the origin? | S3, ALB, EC2, API Gateway, custom HTTP origin |
| Does the origin need protection? | Origin access and network controls |
| Is the content mutable? | Cache invalidation or versioning |
| What happens during origin failure? | Failover strategy |
| Is traffic global? | Edge distribution and regional placement |
| What are the latency requirements? | Caching and origin proximity |
| What are the security requirements? | TLS, WAF, origin protection |
| What is the availability target? | Multi-AZ, multi-region, failover |
| How is the system observed? | CloudFront, origin, and application metrics |

A good design starts with traffic classification rather than CloudFront configuration.

## Static Website Architecture

One of the simplest CloudFront architectures is a static website backed by Amazon S3.

```mermaid
flowchart LR
    User[Browser] --> CF[CloudFront]
    CF --> S3[S3 Bucket]
    S3 --> Assets[HTML / CSS / JS / Images]
```

The browser requests:

```text
https://example.com/
```

CloudFront serves the object from an edge location when it is cached. On a cache miss, CloudFront retrieves the object from the S3 origin.

### Typical Content

This architecture is suitable for:

- React applications.
- Vue applications.
- Angular applications.
- Documentation sites.
- Static marketing pages.
- Static generated websites.
- JavaScript bundles.
- CSS.
- Images.

### Production Architecture

```text
                    Route 53
                        │
                        ▼
                   CloudFront
                        │
                        ▼
                    S3 Bucket
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
            HTML       JS/CSS     Images
```

For production workloads, the S3 bucket should not need to be publicly readable simply because CloudFront serves it.

Use CloudFront-origin access controls so that CloudFront can retrieve objects while direct public access to the bucket is restricted.

### Cache Strategy

Static assets should generally be aggressively cached.

A deployment might generate:

```text
app.8d7c1a.js
styles.1b93f4.css
logo.91ac23.svg
```

These filenames are immutable from the application's perspective.

The HTML document can have a shorter TTL because it references the latest asset versions.

```text
/index.html
    ↓
shorter cache lifetime

/assets/app.8d7c1a.js
    ↓
long cache lifetime
```

This minimizes invalidation requirements.

## SPA Architecture

Single-page applications introduce an additional routing concern.

Consider:

```text
https://example.com/
https://example.com/dashboard
https://example.com/settings
```

The browser expects the application to handle routes such as:

```text
/dashboard
/settings
```

but those paths may not correspond to physical objects in S3.

A typical architecture uses the application's entry document:

```text
/dashboard
     │
     ▼
CloudFront
     │
     ▼
index.html
     │
     ▼
React Router / Vue Router
```

The application then performs client-side routing.

### Production Consideration

Do not blindly configure every 4xx response to return `index.html`.

That can hide genuine missing-resource errors.

A better architecture distinguishes:

- SPA application routes.
- Static assets.
- API paths.
- Actual missing objects.

The routing behavior should be deliberate rather than using a global catch-all rule.

## Static Assets + Backend API

A common Django or FastAPI architecture separates frontend assets from API traffic.

```mermaid
flowchart TD
    User[Browser] --> CF[CloudFront]

    CF -->|/static/*| S3[S3 Static Assets]
    CF -->|/media/*| Media[S3 Media]
    CF -->|/api/*| ALB[Application Load Balancer]

    ALB --> App[Django / FastAPI]
    App --> DB[(PostgreSQL)]
    App --> Redis[(Redis)]
```

This architecture has several advantages:

- Static content is served from the edge.
- API traffic reaches the application only when necessary.
- Application servers do not need to serve large static files.
- S3 provides durable object storage.
- CloudFront provides a unified domain.

Example:

```text
https://example.com/static/app.js
https://example.com/media/avatar.jpg
https://example.com/api/users
```

Different cache behaviors can route these paths differently.

| Path | Origin | Typical Caching |
|---|---|---|
| `/static/*` | S3 | Aggressive |
| `/media/*` | S3 | Depends on content |
| `/api/*` | ALB | Usually disabled or tightly controlled |
| `/health/*` | ALB | Usually no caching |

## Django Architecture

A production Django deployment can use CloudFront as the public edge layer.

```text
                        Internet
                           │
                           ▼
                       CloudFront
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
             S3           ALB        S3 Media
           Static          │
                           ▼
                       Nginx / App
                           │
                     Django / DRF
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        PostgreSQL       Redis         Celery
```

Nginx may still be useful behind the load balancer for:

- Reverse proxying.
- Connection handling.
- Request buffering.
- Static handling where appropriate.
- Application server integration.

CloudFront and Nginx solve different problems.

```text
CloudFront
    ↓
Global edge delivery

Nginx
    ↓
Regional reverse proxy
```

Using both is not inherently redundant.

## FastAPI Architecture

A similar design works with FastAPI.

```text
Client
  │
  ▼
CloudFront
  │
  ▼
ALB
  │
  ▼
FastAPI
  │
  ├── PostgreSQL
  ├── Redis
  └── Kafka / Celery
```

FastAPI remains responsible for application behavior.

CloudFront handles edge-level concerns such as:

- TLS termination.
- Caching.
- Compression.
- Edge delivery.
- Request routing.
- Security integration.

## Public API Architecture

CloudFront can front REST APIs when the application benefits from a global edge endpoint.

```mermaid
flowchart LR
    Client[Client] --> CF[CloudFront]
    CF --> ALB[ALB]
    ALB --> API[Django / FastAPI]
    API --> DB[(PostgreSQL)]
```

For a public read-heavy API:

```text
GET /api/products
```

some responses may be cacheable.

For authenticated user-specific APIs:

```text
GET /api/profile
Authorization: Bearer ...
```

caching must be designed carefully.

### Public Read API

A public product catalog may be cacheable:

```text
GET /api/products/123
```

If product information changes infrequently, a controlled TTL can reduce origin load.

```text
Client
  │
  ▼
CloudFront
  │
  ├── Cache HIT → Response
  │
  └── Cache MISS → API → PostgreSQL
```

### Authenticated API

User-specific data generally requires much more careful cache-key design.

```text
GET /api/orders
Authorization: Bearer <token>
```

Caching the response without correctly varying the cache key can expose one user's data to another user.

For sensitive authenticated endpoints, the safest default is often to disable caching unless there is a clearly justified cache design.

## API Caching Architecture

Caching an API should be based on the semantics of the response.

| Endpoint | Typical Strategy |
|---|---|
| `/products` | Potentially cacheable |
| `/products/{id}` | Potentially cacheable |
| `/news` | Short TTL |
| `/profile` | Usually no cache |
| `/orders` | Usually no cache |
| `/payments` | No cache |
| `/admin/*` | Usually no cache |
| `/health` | No cache |

The key question is:

> Can this response safely be reused for another request?

If the answer is uncertain, do not cache it.

## Media Delivery Architecture

Applications that serve large files should generally avoid routing the file body through application servers.

Instead:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
S3
  │
  ▼
Large Object
```

Examples include:

- Videos.
- Images.
- PDFs.
- Software packages.
- Reports.
- Data exports.

The backend can authorize access and return a signed URL or equivalent controlled access mechanism.

```text
Client
  │
  ▼
Django / FastAPI
  │
  │ authorization
  ▼
Signed CloudFront URL
  │
  ▼
CloudFront
  │
  ▼
S3
```

The application does not have to stream the entire file.

This reduces:

- Application bandwidth.
- CPU usage.
- Connection pressure.
- Container resource consumption.

## Secure Private Media Architecture

Private media requires an authorization boundary.

```mermaid
sequenceDiagram
    participant User
    participant API as Django / FastAPI
    participant CF as CloudFront
    participant S3

    User->>API: Request private document
    API->>API: Authorize user
    API-->>User: Signed URL
    User->>CF: GET signed URL
    CF->>S3: Authorized object request
    S3-->>CF: Object
    CF-->>User: File
```

This pattern is useful for:

- User documents.
- Private reports.
- Subscription content.
- Protected media.

The application should not make the entire bucket publicly accessible simply because CloudFront needs to retrieve objects.

## Image Delivery Architecture

Image-heavy applications benefit significantly from edge delivery.

```text
Browser
   │
   ▼
CloudFront
   │
   ▼
S3
   │
   ├── original/
   ├── thumbnails/
   └── optimized/
```

For large applications, image processing may happen asynchronously:

```text
Upload
  │
  ▼
S3
  │
  ▼
Event
  │
  ▼
Lambda / Celery / Worker
  │
  ▼
Optimized Images
  │
  ▼
CloudFront
```

The backend does not need to resize images synchronously during every user request.

## Video Delivery Architecture

Video workloads are especially suitable for CDN architectures because the content is large and frequently reused.

A simplified design is:

```text
                    CloudFront
                        │
                        ▼
                  S3 / Media Origin
                        │
                        ▼
                 Video Segments
```

For adaptive streaming:

```text
video.m3u8
    │
    ├── segment-001
    ├── segment-002
    ├── segment-003
    └── segment-004
```

CloudFront caches frequently requested segments close to viewers.

For very large video platforms, the architecture may additionally include:

- Transcoding.
- Multiple resolutions.
- Segment generation.
- Metadata services.
- Access control.
- Signed URLs or cookies.
- Content protection.

## Download Architecture

Large report or export downloads should not unnecessarily traverse the API layer.

A better pattern is:

```text
User
  │
  ▼
API
  │
  ├── Create export job
  │
  ▼
Celery / Worker
  │
  ▼
S3
  │
  ▼
Signed CloudFront URL
  │
  ▼
User
```

The API handles orchestration.

The object store handles durable file storage.

CloudFront handles delivery.

This is significantly more scalable than:

```text
User
  │
  ▼
Django
  │
  ▼
Generate 500 MB file
  │
  ▼
Stream through application
```

## Microservices Architecture

CloudFront can sit in front of a microservice platform, but it should not be confused with an internal service-to-service communication layer.

```text
                         CloudFront
                              │
                         API Gateway /
                              ALB
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                 Users     Orders    Products
                  API        API       API
                    │         │         │
                    └─────────┼─────────┘
                              ▼
                       Internal Services
```

CloudFront is primarily concerned with the external request path.

Internal services may communicate using:

- HTTP/REST.
- gRPC.
- Kafka.
- Other internal protocols.

A common architecture is therefore:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Public API
   │
   ├── REST
   ├── gRPC
   └── Kafka
```

CloudFront does not replace gRPC or Kafka.

## Kubernetes Architecture

CloudFront can front an application deployed on Kubernetes.

A typical architecture might be:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
AWS Load Balancer
   │
   ▼
Kubernetes Ingress
   │
   ├── Service A
   ├── Service B
   └── Service C
        │
        ▼
      Pods
```

For example:

```text
CloudFront
    ↓
ALB
    ↓
Ingress
    ↓
FastAPI Service
    ↓
Pods
```

Kubernetes handles:

- Pod scheduling.
- Service discovery.
- Rolling deployments.
- Horizontal scaling.
- Container orchestration.

CloudFront handles:

- Global edge delivery.
- Caching.
- Viewer TLS.
- Edge routing.

Each layer should retain a clear responsibility.

## Multi-Origin Architecture

A single CloudFront distribution can support different origins.

For example:

```text
CloudFront
   │
   ├── /static/* → S3
   ├── /media/*  → S3
   ├── /api/*    → ALB
   └── /download/* → S3
```

This is often preferable to creating separate public domains for every backend component.

The client sees:

```text
https://example.com
```

while CloudFront determines where each request should go.

## Multi-Region API Architecture

For applications requiring regional resilience:

```mermaid
flowchart TD
    Users[Global Users] --> CF[CloudFront]

    CF --> RegionA[Region A]
    CF --> RegionB[Region B]

    RegionA --> ALBA[ALB]
    RegionA --> AppA[Django / FastAPI]

    RegionB --> ALBB[ALB]
    RegionB --> AppB[Django / FastAPI]

    AppA --> DBA[(Database A)]
    AppB --> DBB[(Database B)]

    DBA <-. Replication .-> DBB
```

CloudFront provides the global edge endpoint.

The regional infrastructure provides application availability.

The database layer determines much of the actual consistency and recovery behavior.

## Origin Groups for Failover

A primary/secondary architecture can use CloudFront origin groups.

```text
CloudFront
    │
    ▼
Primary Origin
    │
    ├── Healthy → Response
    │
    └── Failure
          │
          ▼
      Secondary Origin
```

This is useful for origin-level failover.

However, failover should be based on realistic application health rather than merely assuming that network connectivity means the application is healthy.

The origin should expose health behavior that reflects meaningful availability.

## Multi-Region Static Content

Static content can use replicated S3 storage.

```text
                 CloudFront
                  /      \
                 /        \
              S3 A       S3 B
                │          │
                └── Replication ──┘
```

The exact implementation depends on the required recovery model.

For many applications, static assets are easier to make highly available than transactional data because objects are naturally addressable and can often be replicated asynchronously.

## SaaS Multi-Tenant Architecture

CloudFront can be useful for SaaS platforms serving many customers.

```text
Tenant A ─┐
Tenant B ─┼──► CloudFront ──► Application
Tenant C ─┘
```

Tenant identification may be based on:

- Hostname.
- Path.
- Headers.
- Authentication context.

Example:

```text
tenant-a.example.com
tenant-b.example.com
tenant-c.example.com
```

The application still performs tenant authorization.

CloudFront should not be treated as the primary authorization boundary for tenant isolation.

## Tenant-Aware Caching

Multi-tenant systems require special care with cache keys.

Consider:

```text
GET /api/dashboard
```

If the response depends on:

```text
Tenant ID
User ID
Authorization
```

a generic cache key can be unsafe.

For example:

```text
Cache key:
GET /api/dashboard
```

may cause responses to be incorrectly reused.

The architecture must ensure that any cached representation is scoped to all relevant dimensions.

For highly personalized SaaS APIs, disabling caching is often safer than constructing an unnecessarily complex cache key.

## Security Architecture

A production architecture should establish clear security boundaries.

```text
Internet
   │
   ▼
CloudFront
   │
   ├── TLS
   ├── WAF
   ├── Rate controls
   └── Edge policies
   │
   ▼
Origin
   │
   └── Application security
```

Security responsibilities should be layered.

| Layer | Typical Responsibility |
|---|---|
| CloudFront | TLS, edge delivery, caching |
| AWS WAF | Request filtering |
| ALB | Regional traffic distribution |
| Application | Authentication and authorization |
| Database | Data access control |
| S3 | Object permissions |
| IAM | AWS resource permissions |

Do not move business authorization into CDN configuration simply because CloudFront can inspect request attributes.

## WAF-Protected API

A common public architecture is:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
AWS WAF
  │
  ▼
ALB
  │
  ▼
Django / FastAPI
```

WAF can help reduce unwanted traffic before it reaches the application.

Application authorization is still required:

```text
WAF
  ≠
Authentication
  ≠
Authorization
```

These controls solve different problems.

## Origin Protection

A common production mistake is exposing every origin publicly without considering bypass paths.

For example:

```text
Internet
   ├────────────► CloudFront
   │
   └────────────► ALB directly
```

If clients can bypass CloudFront, they may bypass some edge-layer controls and caching behavior.

The architecture should intentionally define whether direct origin access is permitted.

## Observability Architecture

CloudFront should be observed together with the origin.

```text
                 CloudFront Metrics
                        │
                        ▼
                 Origin Metrics
                        │
                        ▼
              Application Metrics
                        │
                        ▼
               Database Metrics
```

Useful signals include:

- Requests.
- Cache hit ratio.
- Latency.
- 4xx responses.
- 5xx responses.
- Origin response time.
- WAF blocks.
- Regional traffic distribution.
- Origin health.
- Application saturation.

A high CloudFront 5xx rate is not sufficient to identify the root cause.

The operational chain should be traceable:

```text
CloudFront
   ↓
ALB
   ↓
Application
   ↓
Database
```

## Cost-Aware Architecture

CloudFront can reduce origin bandwidth and compute usage, but it is not automatically cheaper for every workload.

Consider:

```text
High cacheability
     ↓
High cache hit ratio
     ↓
Lower origin traffic
```

versus:

```text
Highly personalized requests
     ↓
Low cache hit ratio
     ↓
Most requests reach origin
```

For APIs with almost no reusable content, CloudFront may primarily provide edge networking and security benefits rather than significant origin offloading.

Cost analysis should include:

- Data transfer.
- Requests.
- Cache behavior.
- Origin bandwidth.
- S3 access.
- Application compute.
- Cross-region traffic.

## Architecture Selection Matrix

| Architecture | Best Fit | Main Benefit | Main Risk |
|---|---|---|---|
| CloudFront + S3 | Static content | Low origin load | Cache invalidation |
| CloudFront + ALB | Web/API workloads | Global edge + regional app | Dynamic origin load |
| CloudFront + S3 + ALB | Full-stack apps | Separates static/dynamic traffic | More configuration |
| CloudFront + Private S3 | Protected media | Strong object access control | Access design complexity |
| CloudFront + Multi-Region ALB | Global APIs | Regional resilience | Data consistency |
| CloudFront + Kubernetes | Container platforms | Edge + orchestration | Layer complexity |
| CloudFront + Origin Failover | DR | Origin resilience | Secondary readiness |
| CloudFront + Media Origin | Video/media | Large-scale delivery | Storage/encoding complexity |

## Production Architecture Example

A mature backend platform may combine several patterns:

```mermaid
flowchart TD
    Users[Global Users] --> CF[CloudFront]
    CF --> WAF[AWS WAF]

    WAF -->|/static/*| S3Static[S3 Static Assets]
    WAF -->|/media/*| S3Media[S3 Media]
    WAF -->|/api/*| ALB[Regional / Multi-Region ALB]

    ALB --> App[Django / FastAPI]
    App --> DB[(PostgreSQL)]
    App --> Redis[(Redis)]
    App --> Queue[Kafka / Celery]

    Queue --> Workers[Workers]
    Workers --> DB
    Workers --> S3Media
```

This design separates responsibilities:

- CloudFront provides edge delivery.
- WAF provides request filtering.
- S3 provides object storage.
- ALB provides regional traffic distribution.
- Django/FastAPI provides business logic.
- PostgreSQL provides transactional state.
- Redis provides caching or ephemeral shared state.
- Kafka/Celery provides asynchronous processing.

## Example Request Flows

### Static Asset

```text
Browser
  ↓
CloudFront
  ↓
Cache HIT
  ↓
Browser
```

No application server is involved.

### API Cache Miss

```text
Browser
  ↓
CloudFront
  ↓
ALB
  ↓
Django / FastAPI
  ↓
PostgreSQL
  ↓
Response
  ↓
CloudFront
  ↓
Browser
```

### Private Download

```text
Browser
  ↓
API
  ↓
Authorization
  ↓
Signed URL
  ↓
CloudFront
  ↓
S3
  ↓
Browser
```

### Origin Failure

```text
Browser
  ↓
CloudFront
  ↓
Primary Origin
  ↓
Failure
  ↓
Secondary Origin
  ↓
Response
```

Each flow has different reliability, security, and caching implications.

## Common Production Mistakes

### Sending Everything Through the Application

Serving static files and large downloads through Django or FastAPI increases application resource consumption.

**Better approach:** Use S3 and CloudFront for appropriate object delivery.

### Caching Personalized API Responses

A response containing user-specific data can become a security issue if the cache key is not correctly scoped.

**Better approach:** Disable caching or explicitly design the cache key around every relevant request dimension.

### Making S3 Public Because CloudFront Needs Access

CloudFront does not require the bucket to be publicly accessible.

**Better approach:** Use CloudFront-specific origin access controls.

### Treating CloudFront as an API Gateway

CloudFront provides edge delivery and routing capabilities but is not a replacement for an API gateway's full application/API management responsibilities.

### Using One Cache Policy Everywhere

Static files and authenticated APIs have different requirements.

**Better approach:** Define cache behavior according to URL path and request semantics.

### Ignoring Origin Bypass

If users can access the origin directly, they may bypass edge-layer controls.

**Better approach:** Intentionally design origin access and protection.

### Overusing Cache Invalidation

Frequent invalidation can indicate poor asset-versioning design.

**Better approach:** Use versioned asset names for immutable resources and reserve invalidation for content that genuinely requires it.

### Assuming Multi-Region Means Highly Available

Two regions do not automatically solve:

- Database failures.
- Authentication failures.
- Queue failures.
- Configuration drift.
- External service failures.
- Data consistency.

**Better approach:** Design the complete dependency graph.

### Adding CloudFront Without Measuring Cacheability

A workload with almost entirely unique, personalized requests may gain limited caching benefits.

**Better approach:** Analyze request reuse and origin load before selecting the caching strategy.

## Architecture Review Checklist

### Traffic

- [ ] Static and dynamic traffic are separated.
- [ ] API cacheability is explicitly defined.
- [ ] Personalized responses are protected from unsafe caching.
- [ ] Large downloads bypass application servers where appropriate.
- [ ] Media delivery is handled independently from transactional APIs.

### Origins

- [ ] Every CloudFront behavior has an intentional origin.
- [ ] Origins are protected appropriately.
- [ ] Origin health is observable.
- [ ] Origin failover is tested if configured.
- [ ] Direct origin access is intentionally controlled.

### Application

- [ ] Django/FastAPI instances are as stateless as practical.
- [ ] Local filesystem state is not used for critical shared data.
- [ ] Authentication works through the CloudFront path.
- [ ] Application authorization remains enforced at the application layer.

### Caching

- [ ] Cache policies match content semantics.
- [ ] Cache keys include all required dimensions.
- [ ] Static assets use versioned filenames where practical.
- [ ] Dynamic APIs are not cached by default without a clear justification.
- [ ] TTLs reflect content freshness requirements.

### Reliability

- [ ] Application workloads are multi-AZ where required.
- [ ] Multi-region architecture is used where justified.
- [ ] Origin failover has been tested.
- [ ] Database recovery is defined.
- [ ] Background processing recovery is defined.
- [ ] RTO and RPO are documented.

### Security

- [ ] HTTPS is enforced.
- [ ] WAF is configured where appropriate.
- [ ] S3 origins are not unnecessarily public.
- [ ] Authentication and authorization are separate from CDN behavior.
- [ ] Origin bypass paths are controlled.

### Operations

- [ ] CloudFront metrics are monitored.
- [ ] Origin metrics are monitored.
- [ ] Application metrics are correlated with edge metrics.
- [ ] Cache hit ratio is tracked where relevant.
- [ ] Deployment changes are observable.
- [ ] Failover and failback procedures are documented.

## Interview Traps

### Is CloudFront only for static files?

No. It can front dynamic web applications and APIs as well, although dynamic workloads require careful caching and security design.

### Should every API response be cached?

No. Cacheability depends on whether the response can safely be reused.

### Can CloudFront replace Nginx?

Not directly. CloudFront operates at the global edge while Nginx commonly operates as a regional reverse proxy or application gateway.

### Can CloudFront replace an API gateway?

Not universally. CloudFront and API gateways address overlapping but different architectural concerns.

### Why use CloudFront in front of an ALB?

Possible reasons include:

- Global edge delivery.
- Caching.
- TLS termination at the edge.
- WAF integration.
- Reduced origin traffic.
- Improved delivery latency for cacheable content.

### Why put S3 behind CloudFront?

To provide edge caching, HTTPS/custom domains, controlled origin access, and efficient global content delivery.

### Does CloudFront make the database highly available?

No. Database availability and replication must be designed independently.

### Is a high cache hit ratio always the goal?

No. The goal is correct behavior with efficient origin utilization. Caching sensitive or rapidly changing data incorrectly is worse than having a low cache hit ratio.

## Key Takeaways

- **CloudFront should be designed around traffic types:** static assets, APIs, media, downloads, and personalized content generally require different origins and cache policies.
- **A strong production architecture separates responsibilities:** CloudFront handles edge delivery, S3 handles objects, ALB handles regional traffic, and Django/FastAPI handles business logic.
- **Caching is an architectural decision, not a default optimization:** cache keys, TTLs, authentication, content mutability, and data sensitivity must all be considered together.
- **CloudFront can support highly available and multi-region systems, but it does not create resilience by itself:** databases, queues, authentication, storage, and external dependencies must also be designed for failure.
- **The best CloudFront architecture minimizes unnecessary origin work while preserving correctness and security:** immutable assets, private object delivery, carefully scoped API caching, origin protection, and end-to-end observability are core production practices.