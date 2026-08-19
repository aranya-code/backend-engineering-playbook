# 03- Multi-Origin Architecture

## Overview

A multi-origin CloudFront architecture uses multiple origins within a single distribution to serve different workloads, environments, content types, or failure domains.

The primary reason to introduce multiple origins is to avoid forcing fundamentally different workloads through the same backend path.

A typical production architecture separates static content from dynamic application traffic:

```text
                           Internet
                              │
                              ▼
                         CloudFront
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
           /static/*       /media/*         /api/*
              │               │                │
              ▼               ▼                ▼
              S3              S3               ALB
                                               │
                                               ▼
                                        Django / FastAPI
                                               │
                              ┌────────────────┼───────────────┐
                              ▼                ▼               ▼
                         PostgreSQL          Redis           Kafka
```

Multi-origin design is primarily an **origin routing problem**. CloudFront determines which origin receives a request through cache behavior configuration, while each origin remains responsible for its own application or storage concerns.

The important architectural distinction is:

> Multiple origins provide routing and isolation; they do not automatically provide high availability or disaster recovery.

## Why Multiple Origins Exist

A single application may contain several types of traffic with very different characteristics.

For example:

| Workload | Characteristics | Suitable Origin |
|---|---|---|
| JavaScript/CSS | Immutable, highly cacheable | S3 |
| Images | Object storage, cacheable | S3 |
| Public API | Dynamic, potentially cacheable | ALB |
| Private API | User-specific | ALB |
| Downloads | Large objects | S3 |
| Application pages | Dynamic | ALB |
| Legacy service | Existing HTTP endpoint | Custom origin |

Putting everything behind one application origin creates unnecessary coupling.

```text
CloudFront
    │
    ▼
Application
    │
    ├── Static files
    ├── Media
    ├── APIs
    └── Dynamic pages
```

A multi-origin architecture separates these concerns:

```text
CloudFront
    │
    ├── Static ──► S3
    │
    ├── Media ───► S3
    │
    └── Dynamic ─► ALB ──► Application
```

This allows each backend component to scale and evolve independently.

## Core Architecture

A CloudFront distribution can contain multiple origins, while cache behaviors determine which origin handles a matching request.

```mermaid
flowchart TD
    Client[Client] --> CF[CloudFront Distribution]

    CF --> StaticBehavior["/static/*"]
    CF --> MediaBehavior["/media/*"]
    CF --> APIBehavior["/api/*"]
    CF --> DefaultBehavior["Default /*"]

    StaticBehavior --> S3Static[S3 Static Bucket]
    MediaBehavior --> S3Media[S3 Media Bucket]
    APIBehavior --> ALB[Application Load Balancer]
    DefaultBehavior --> ALB

    ALB --> App[Django / FastAPI]
```

The important relationship is:

```text
Request Path
     ↓
Cache Behavior
     ↓
Origin Selection
     ↓
Origin Request
```

Origins themselves do not decide which request they receive. The CloudFront distribution configuration does.

## Origin Routing Model

Consider these URLs:

```text
https://app.example.com/static/app.js
https://app.example.com/media/logo.png
https://app.example.com/api/orders
https://app.example.com/dashboard
```

A distribution could define:

| Path Pattern | Origin |
|---|---|
| `/static/*` | S3 |
| `/media/*` | S3 |
| `/api/*` | ALB |
| `/*` | ALB |

The default behavior is important because any request not matching a more specific pattern falls through to it.

For example:

```text
/static/app.js
      │
      ▼
/static/*
      │
      ▼
S3

/api/orders
      │
      ▼
/api/*
      │
      ▼
ALB

/dashboard
      │
      ▼
/*
      │
      ▼
ALB
```

## Path Pattern Specificity

When multiple behaviors could conceptually match a request, behavior ordering and path-pattern specificity matter.

A common design is:

```text
/images/*
/static/*
/api/*
/*
```

The catch-all behavior should generally represent the default application route rather than accidentally intercepting traffic intended for another origin.

A common mistake is creating a new origin without creating the corresponding cache behavior.

For example:

```text
New Origin:
S3

Existing Behaviors:
/*
```

does not automatically cause requests to use the new S3 origin.

The cache behavior must explicitly reference the origin.

## Static and Dynamic Origin Separation

One of the most common multi-origin patterns is:

```text
                     CloudFront
                         │
              ┌──────────┴──────────┐
              │                     │
          Static Traffic        Dynamic Traffic
              │                     │
              ▼                     ▼
             S3                    ALB
                                    │
                                    ▼
                              Application
```

Static content benefits from:

- Long cache lifetimes.
- Immutable filenames.
- Object storage.
- High cache-hit ratios.
- Low origin compute requirements.

Dynamic traffic generally requires:

- Authentication.
- Application execution.
- Database access.
- Request-specific logic.
- Shorter cache lifetimes or no shared caching.

Keeping them separate avoids mixing fundamentally different caching and scaling strategies.

## Multiple S3 Origins

Multiple S3 origins can be useful when different buckets have different ownership, lifecycle, security, or deployment responsibilities.

For example:

```text
CloudFront
│
├── /static/* ──► frontend-assets bucket
│
├── /media/*  ──► user-media bucket
│
└── /downloads/* ──► downloads bucket
```

This can provide stronger separation between:

- Build artifacts.
- User-generated content.
- Public media.
- Downloadable assets.

It also allows different bucket policies and lifecycle rules.

However, do not create separate buckets merely because separate origins are technically possible. The separation should represent a meaningful operational or security boundary.

## Static Asset Origin

A frontend deployment might produce:

```text
dist/
├── index.html
├── assets/
│   ├── app.91ac2.js
│   ├── app.72f3a1.css
│   └── vendor.33f12d.js
└── images/
    └── logo.png
```

A production architecture can use:

```text
CloudFront
    │
    └── /assets/* ──► S3
```

Content-hashed assets can receive long cache lifetimes because a new deployment produces new URLs.

For example:

```text
app.91ac2.js
app.7f3c9e.js
```

The old and new files can coexist while clients gradually move to the new version.

## Dynamic Application Origin

The application origin usually sits behind a load balancer.

```text
CloudFront
    │
    ▼
ALB
    │
    ├── Application Instance
    ├── Application Instance
    └── Application Instance
```

For Django:

```text
CloudFront
    │
    ▼
ALB
    │
    ▼
Gunicorn
    │
    ▼
Django
```

For FastAPI:

```text
CloudFront
    │
    ▼
ALB
    │
    ▼
Uvicorn
    │
    ▼
FastAPI
```

CloudFront handles edge delivery while the application remains responsible for business logic.

## API and Static Content on One Domain

A multi-origin architecture is especially useful when the application should expose everything through one hostname.

For example:

```text
app.example.com
```

can serve:

```text
/static/*   → S3
/media/*    → S3
/api/*      → ALB
/*          → ALB
```

This avoids requiring separate public hostnames such as:

```text
cdn.example.com
api.example.com
media.example.com
```

when a single-domain architecture is preferable.

It can also simplify:

- CORS configuration.
- Frontend deployment.
- Browser requests.
- Cookie scope.
- TLS management.

## Multiple Application Origins

Multiple origins do not have to represent different technologies.

They can represent different application deployments.

For example:

```text
CloudFront
    │
    ├── /api/v1/* ──► API v1 ALB
    │
    ├── /api/v2/* ──► API v2 ALB
    │
    └── /legacy/* ──► Legacy ALB
```

This can be useful during migrations.

A controlled migration might look like:

```text
Old API
   │
   ├── Existing clients
   │
   └── /api/v1/*

New API
   │
   └── /api/v2/*
```

The routing boundary is explicit and can remain stable while backend implementations evolve.

## Blue/Green Architecture

Multiple origins can also participate in deployment architectures.

For example:

```text
CloudFront
   │
   ├── Production Behavior ──► Blue Environment
   │
   └── Migration Path ───────► Green Environment
```

However, CloudFront path-based routing is not a complete blue/green traffic-management solution.

For controlled percentage-based traffic shifting, dedicated deployment and routing mechanisms may be more appropriate.

CloudFront should not be treated as a replacement for a complete progressive delivery system.

## Multi-Region Origins

Multiple origins can represent separate regional application deployments.

```text
                       CloudFront
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
          Region A                  Region B
              │                         │
             ALB                       ALB
              │                         │
              ▼                         ▼
          Application               Application
```

This architecture can improve regional resilience, but it introduces substantial distributed-systems complexity.

You must consider:

- Database replication.
- Write ownership.
- Session state.
- Redis state.
- File storage.
- Background jobs.
- Kafka consumers.
- Idempotency.
- Data consistency.
- Cross-region latency.

CloudFront only solves the edge-routing portion.

## Origin Groups

Origin groups are different from simply having multiple unrelated origins.

An origin group defines a primary and secondary origin for failover behavior.

```text
                   CloudFront
                       │
                       ▼
                Primary Origin
                       │
             ┌─────────┴─────────┐
             │                   │
          Healthy              Failure
             │                   │
             ▼                   ▼
          Response         Secondary Origin
```

For example:

```text
Primary:
ALB - us-east-1

Secondary:
ALB - eu-west-1
```

This should only be used when the secondary origin can actually serve the request correctly.

## Multi-Origin vs Origin Failover

These concepts should not be confused.

| Architecture | Purpose |
|---|---|
| Multiple origins | Serve different workloads |
| Path-based behaviors | Route different paths |
| Origin group | Fail over between origins |
| Multi-region origins | Geographic or regional resilience |
| Static + dynamic origins | Workload separation |

For example:

```text
/static/* → S3
/api/*    → ALB
```

is multi-origin routing.

Whereas:

```text
/api/*
   │
   ├── Primary ALB
   └── Secondary ALB
```

is origin failover.

## Multi-Origin Request Lifecycle

A request flows through the distribution before reaching an origin.

```mermaid
sequenceDiagram
    participant Client
    participant CF as CloudFront
    participant Cache as Edge Cache
    participant Origin as Selected Origin
    participant App as Application

    Client->>CF: GET /api/orders
    CF->>CF: Match cache behavior
    CF->>CF: Evaluate cache key
    CF->>Cache: Lookup object

    alt Cache hit
        Cache-->>CF: Cached response
        CF-->>Client: Response
    else Cache miss
        CF->>Origin: Forward origin request
        Origin->>App: Process request
        App-->>Origin: HTTP response
        Origin-->>CF: HTTP response
        CF->>Cache: Store if cacheable
        CF-->>Client: Response
    end
```

The important architectural point is that origin selection happens before the origin request is sent.

## Origin Request Policy in Multi-Origin Systems

Different origins often require different request data.

For example:

```text
/static/* → S3
```

may not require application authentication headers.

But:

```text
/api/* → ALB
```

may require:

```text
Authorization
Cookie
X-Tenant-ID
```

Therefore, different behaviors should generally use policies appropriate to their workloads.

Avoid a single "forward everything" policy across the entire distribution.

## Cache Policy Design

Different origins frequently require different cache strategies.

| Behavior | Typical Cache Strategy |
|---|---|
| `/static/*` | Long-lived |
| `/images/*` | Long-lived |
| `/api/public/*` | Carefully cacheable |
| `/api/private/*` | Usually uncached |
| `/*` | Application-specific |

The correct question is not:

> "Can CloudFront cache this?"

The better question is:

> "Is this response safe and correct to share across requests?"

That distinction is particularly important for APIs.

## Personalized Content Across Origins

Suppose:

```text
/api/profile
```

returns data based on the authenticated user.

The application origin may receive:

```text
Authorization: Bearer <token>
```

If the response is cached incorrectly:

```text
User A
  │
  ▼
CloudFront
  │
  ▼
Cached User A Response
  │
  ▼
User B
```

User B could receive User A's data.

For private endpoints, prefer a configuration that avoids unintended shared caching.

## Tenant-Aware Multi-Origin Systems

Multi-tenant applications introduce another isolation boundary.

Suppose:

```text
GET /api/catalog
X-Tenant-ID: tenant-a
```

and:

```text
GET /api/catalog
X-Tenant-ID: tenant-b
```

Both requests reach:

```text
/api/* → ALB
```

but the response differs by tenant.

The cache design must ensure that responses cannot cross tenant boundaries.

This is a correctness and security requirement, not merely a performance optimization.

## Origin Path Considerations

Different origins may expose different internal path structures.

For example:

```text
/static/* → S3 bucket
/api/*    → application
```

The viewer URL:

```text
/api/orders
```

may map directly to:

```text
/api/orders
```

at the origin.

Another application could require:

```text
/v1/api/orders
```

Origin path configuration can help when a consistent viewer-facing URL needs to map to a different origin-side path.

Be careful not to duplicate path prefixes in both CloudFront and application routing.

## Headers and Hostnames

Different origins can require different host-related behavior.

For example:

```text
CloudFront
    │
    ├── S3
    │
    └── ALB
```

The application origin may depend on the correct `Host` behavior for routing or TLS.

When debugging multi-origin problems, verify:

- Viewer hostname.
- CloudFront distribution.
- Selected cache behavior.
- Origin hostname.
- Origin request host/header behavior.
- TLS certificate expectations.

## Security Boundaries

Multi-origin architectures can create useful security boundaries.

For example:

```text
CloudFront
│
├── Public Static Assets
│       │
│       ▼
│      S3
│
└── Authenticated API
        │
        ▼
       ALB
        │
        ▼
    Application
```

The static origin can have a different access model from the application origin.

This allows security controls to be designed around workload characteristics rather than applying one generic policy everywhere.

## S3 Origin Security

For private S3 content, use CloudFront Origin Access Control where appropriate.

The intended access path becomes:

```text
Viewer
  │
  ▼
CloudFront
  │
  ▼
Private S3
```

rather than exposing the bucket directly.

Different S3 origins can have different bucket policies when their responsibilities differ.

For example:

```text
static-assets
    → public CDN content

user-media
    → authenticated application-controlled content
```

The security model should reflect the sensitivity of each dataset.

## Protecting Application Origins

If CloudFront is intended to be the public entry point, direct access to the application origin should be carefully controlled.

For example:

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
Application
```

should not silently become:

```text
Internet
    ├──► CloudFront
    │
    └──► ALB directly
```

unless direct ALB access is intentionally part of the architecture.

CloudFront, WAF, rate limiting, logging, and other edge controls can otherwise be bypassed.

## Origin Failure Domains

Multiple origins can reduce coupling, but they can also introduce additional failure modes.

Consider:

```text
CloudFront
│
├── S3
│
├── ALB A
│
└── ALB B
```

Potential failures include:

- Incorrect behavior routing.
- S3 access denial.
- ALB failure.
- Application failure.
- DNS issues.
- TLS issues.
- Origin timeout.
- Incorrect path mapping.
- Policy misconfiguration.

More origins therefore mean more configuration and more possible failure paths.

## High Availability

A multi-origin architecture should distinguish between **workload separation** and **availability**.

This:

```text
/static/* → S3
/api/*    → ALB
```

does not automatically make the API highly available.

For high availability, the application origin itself should have appropriate redundancy:

```text
CloudFront
    │
    ▼
ALB
    │
    ├── Instance A
    ├── Instance B
    └── Instance C
```

For regional resilience:

```text
CloudFront
   │
   ├── Region A
   │
   └── Region B
```

but the underlying data architecture must also support the failure model.

## Disaster Recovery

Multi-origin architecture should be evaluated as part of the complete disaster-recovery design.

A common misconception is:

```text
Two origins = Disaster Recovery
```

This is incorrect.

If both application origins depend on:

```text
Single PostgreSQL Database
```

then the database remains a shared failure domain.

A real DR design must consider:

```text
Application
Database
Storage
Messaging
Cache
Secrets
Configuration
DNS
Deployment
Observability
```

## Performance Considerations

Multi-origin routing can improve performance when it places content closer to the appropriate delivery mechanism.

For static assets:

```text
Client
  │
  ▼
CloudFront
  │
  └── Cache Hit
```

The origin may not be contacted at all.

For dynamic APIs:

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
Application
```

The origin latency becomes part of the request latency on cache misses or uncacheable requests.

Separating static traffic therefore reduces application-origin load.

## Origin Capacity Planning

Capacity planning should account for the traffic each origin actually receives.

Suppose:

```text
Total requests: 100 million/month

Static:
80 million

Dynamic:
20 million
```

If static requests are served primarily from CloudFront cache, the application origin may see significantly less traffic than the total request count.

This can substantially reduce:

- Application CPU.
- Database queries.
- Network bandwidth.
- Load balancer traffic.
- Infrastructure cost.

## Cache Invalidation in Multi-Origin Systems

Invalidation behavior depends on the cached objects associated with the distribution.

Suppose:

```text
/static/* → S3
/api/*    → ALB
```

Invalidating:

```text
/static/*
```

does not mean the application API cache is automatically invalidated.

Each workload should have an explicit cache lifecycle.

For static assets, versioned filenames are generally preferable to frequent broad invalidations.

For APIs, cache invalidation requires careful modeling of data freshness.

## Deployment Architecture

A common deployment flow is:

```text
CI/CD
  │
  ├── Build frontend
  │
  ├── Upload assets → S3
  │
  ├── Deploy backend → Application
  │
  └── Update CloudFront configuration if required
```

For immutable assets:

```text
app.<hash>.js
app.<hash>.css
```

the deployment can publish new objects without replacing existing versions immediately.

This reduces cache invalidation pressure.

## Infrastructure as Code

Multi-origin CloudFront distributions should generally be managed through infrastructure as code.

The exact implementation depends on the chosen AWS IaC tool, but the configuration should represent:

- Distribution.
- Origins.
- Origin groups where applicable.
- Cache behaviors.
- Cache policies.
- Origin request policies.
- TLS configuration.
- WAF association.
- Logging configuration.
- Access controls.

The goal is reproducibility and controlled change management.

A manual console-only architecture becomes difficult to audit as the number of origins grows.

## Monitoring Multi-Origin Architectures

Monitoring should be origin-aware.

A useful operational view is:

```text
CloudFront
   │
   ├── S3 Static
   │      ├── Errors
   │      └── Latency
   │
   └── ALB API
          ├── Errors
          ├── Latency
          └── Saturation
```

Track at minimum:

| Layer | Important Signals |
|---|---|
| CloudFront | Requests, cache hit ratio, 4xx, 5xx |
| S3 | Requests, errors, access failures |
| ALB | Target health, latency, HTTP errors |
| Application | Request latency, exceptions, saturation |
| Database | Connections, latency, locks |
| Redis | Memory, latency, hit ratio |
| Kafka | Consumer lag and throughput |

## Troubleshooting Multi-Origin Routing

When a request reaches the wrong backend, troubleshoot in this order:

```text
Request URL
    │
    ▼
CloudFront Distribution
    │
    ▼
Cache Behavior
    │
    ▼
Origin Selection
    │
    ▼
Origin Path
    │
    ▼
Origin Request
    │
    ▼
Backend
```

For example, if:

```text
/static/app.js
```

unexpectedly reaches Django instead of S3, verify:

1. The request matches the expected `/static/*` behavior.
2. The behavior references the S3 origin.
3. The S3 origin is correctly configured.
4. The object exists at the expected path.
5. The request is not being served from an unexpected cached response.

## Common Mistakes

### Adding an Origin Without a Cache Behavior

An origin is not automatically used.

**Avoid it:** Explicitly associate the relevant cache behavior with the intended origin.

### Using the Default Behavior for Everything

A catch-all behavior can accidentally send static requests to the application.

**Avoid it:** Create explicit behaviors for meaningful workload boundaries.

### Forwarding Everything to Every Origin

Different origins have different requirements.

**Avoid it:** Use origin request policies appropriate to each behavior.

### Caching Authenticated API Responses

This can expose private data.

**Avoid it:** Treat personalization and tenant isolation as cache-correctness requirements.

### Using Multiple Origins Without Clear Ownership

Every origin should have an operational owner and a defined responsibility.

**Avoid it:** Create an origin only when it represents a meaningful architectural boundary.

### Assuming Multi-Origin Means Multi-Region DR

Two origins can still share the same database or dependency.

**Avoid it:** Model the complete dependency graph for the desired recovery scenario.

### Overusing Path-Based Routing

Routing every microservice through a unique CloudFront behavior can create excessive configuration complexity.

**Avoid it:** Use CloudFront as a public delivery and routing layer, not as a substitute for internal service discovery.

### Ignoring Direct Origin Access

A public ALB or S3 bucket may allow users to bypass CloudFront.

**Avoid it:** Define and enforce the intended origin access model.

## Production Design Guidelines

A practical multi-origin design should follow these principles:

### Separate Workloads

Use separate origins when workloads have materially different:

- Scaling requirements.
- Caching behavior.
- Security requirements.
- Deployment lifecycles.
- Ownership.

### Prefer Stable Routing Boundaries

Use clear patterns such as:

```text
/static/*
/media/*
/api/*
```

rather than complicated overlapping path structures.

### Keep the Default Behavior Intentional

The default behavior should have an explicit purpose.

Usually:

```text
/*
```

routes to the primary application origin.

### Design Cache and Origin Policies Together

For every behavior, answer:

- What is the cache key?
- What reaches the origin?
- Is the response shared?
- Which headers are required?
- Which cookies are required?
- Which query strings matter?

### Protect Every Origin According to Its Role

S3 and application origins have different security mechanisms and threat models.

### Test Routing Explicitly

Test:

```text
/static/*
/media/*
/api/*
/unknown-path
```

and verify that each request reaches the intended backend.

### Test Failure Modes

If using multiple origins for resilience, test:

- Primary origin failure.
- Secondary origin failure.
- Partial application failure.
- Dependency failure.
- Incorrect health conditions.
- Regional failure.

A failover design that has never been exercised is an assumption, not a proven recovery mechanism.

## Architecture Decision Matrix

| Requirement | Recommended Pattern |
|---|---|
| Static assets | S3 origin |
| Dynamic backend | ALB/custom HTTP origin |
| Static + dynamic application | Multiple origins |
| API version migration | Path-based application origins |
| Regional resilience | Multi-region origins |
| Origin failover | Origin group |
| Private S3 delivery | CloudFront + Origin Access Control |
| Different security policies | Separate origins/behaviors |
| Large immutable assets | S3 + long-lived caching |
| Personalized API | Application origin with careful/no shared caching |

## Interview Traps

### Can CloudFront Have Multiple Origins?

Yes. A distribution can define multiple origins and use cache behaviors to route requests to them.

### Does CloudFront Automatically Load Balance Between Origins?

No. Multiple origins are not automatically treated as a load-balanced pool. Origin groups provide a specific failover mechanism, while ordinary multi-origin routing typically selects an origin through cache behavior configuration.

### Can One Path Use Different Origins?

A given cache behavior maps to an origin. If different routing decisions are required, the path structure and behaviors must be designed accordingly.

### Is Multi-Origin the Same as Multi-Region?

No.

Multi-origin means multiple configured content sources. Those origins may be:

- Two S3 buckets.
- S3 and ALB.
- Two application endpoints.
- Two regional deployments.

Multi-region is specifically about geographic deployment across regions.

### Does Origin Failover Guarantee Zero Downtime?

No.

Failover depends on:

- Failure detection.
- Configured failover behavior.
- Secondary origin health.
- Data availability.
- Application compatibility.
- Dependency availability.

### Should Every Microservice Have Its Own CloudFront Origin?

Usually no.

CloudFront is generally a public edge delivery layer. Internal microservice communication should normally use internal networking and service-to-service mechanisms rather than exposing every service directly through CloudFront.

## Production Checklist

- [ ] Each origin has a clearly defined responsibility.
- [ ] Each origin has an explicit operational owner.
- [ ] Static and dynamic workloads are separated where appropriate.
- [ ] Every required origin has a corresponding cache behavior.
- [ ] Path patterns are explicit and non-overlapping where practical.
- [ ] The default behavior is intentional.
- [ ] Cache policies are workload-specific.
- [ ] Origin request policies forward only required data.
- [ ] Personalized responses are not unintentionally shared.
- [ ] Tenant boundaries are preserved.
- [ ] S3 origins use appropriate access controls.
- [ ] Application origins are protected against unintended direct access.
- [ ] HTTPS is used for sensitive origin communication.
- [ ] Origin health is monitored independently.
- [ ] Origin capacity is sized for cache misses and uncacheable traffic.
- [ ] Failover has been tested if configured.
- [ ] Multi-region dependencies are understood.
- [ ] Cache invalidation is part of the deployment strategy.
- [ ] Infrastructure is managed through version-controlled configuration.
- [ ] Routing behavior is tested in CI/CD or controlled integration environments.
- [ ] Operational dashboards distinguish failures by origin.

## Key Takeaways

- **Multi-origin CloudFront architectures separate workloads:** static assets, media, APIs, and application traffic can use origins optimized for their specific requirements.
- **Cache behaviors determine origin routing:** adding an origin alone does not route traffic to it; the appropriate behavior must explicitly reference that origin.
- **Multiple origins are not automatically high availability:** resilience requires explicit failover or multi-region architecture plus independently resilient data and application dependencies.
- **Caching must be designed per workload:** authenticated, personalized, and tenant-specific responses require particular care to prevent incorrect or unsafe cache sharing.
- **Complexity should justify every additional origin:** use multiple origins when they provide meaningful isolation, scalability, security, deployment, or resilience benefits rather than simply because CloudFront supports them.