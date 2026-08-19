# 01- CloudFront Architecture

## Overview

Amazon CloudFront is a globally distributed content delivery and edge computing service that sits between clients and application or storage origins. A production CloudFront architecture separates the concerns of **global request delivery**, **caching**, **origin protection**, **TLS termination**, **security controls**, and **application processing**.

The central architectural model is:

```text
                         Internet
                            │
                            ▼
                    ┌───────────────┐
                    │    Clients    │
                    │ Browsers/APIs │
                    └───────┬───────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     CloudFront      │
                 │                     │
                 │ Distribution        │
                 │ TLS / HTTP          │
                 │ Cache Behaviors     │
                 │ Cache Policies      │
                 │ Edge Processing     │
                 └──────────┬──────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
              Cache Hit             Cache Miss
                 │                     │
                 ▼                     ▼
             Response               Origin
                                       │
                         ┌─────────────┼─────────────┐
                         │             │             │
                         ▼             ▼             ▼
                        S3            ALB       Other Origin
                                      │
                                      ▼
                              Django / FastAPI
                                      │
                         ┌────────────┼────────────┐
                         │            │            │
                         ▼            ▼            ▼
                    PostgreSQL      Redis        Kafka
```

The important architectural boundary is that CloudFront does **not** replace the application backend. It provides a globally distributed delivery and request-processing layer in front of the origin.

## Why CloudFront Architecture Matters

Without a CDN, clients typically communicate directly with an origin:

```text
Client
   │
   │ Long-distance network request
   ▼
Origin
   │
   ▼
Application
```

A globally distributed application may have users hundreds or thousands of kilometers away from the origin. Every request must travel to that origin unless another caching layer exists.

CloudFront introduces an edge layer:

```text
Client
   │
   ▼
Nearest suitable CloudFront edge
   │
   ├── Cached response ──► Client
   │
   └── Origin request ───► Origin
```

This can provide:

- Lower latency for cacheable content.
- Reduced origin traffic.
- Better handling of traffic spikes.
- Distributed TLS termination.
- Centralized edge security controls.
- Path-based routing.
- Integration with AWS origins and custom HTTP origins.
- A foundation for edge request processing.

The architectural goal is not simply to put CloudFront in front of everything. The goal is to decide **which requests should be handled at the edge and which must reach the origin**.

## High-Level Architecture

A typical production architecture can be divided into several layers.

```text
┌───────────────────────────────────────────────────────────┐
│                         Clients                           │
│                 Browsers / Mobile / APIs                 │
└────────────────────────────┬──────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────┐
│                       CloudFront                          │
│                                                           │
│  TLS ── WAF ── Distribution ── Cache Behaviors            │
│                                                           │
│  Cache Policies ── Origin Request Policies                 │
└────────────────────────────┬──────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
        Static Origin                Dynamic Origin
              │                             │
              ▼                             ▼
        Amazon S3                    Load Balancer
                                            │
                                            ▼
                                    Backend Application
                                            │
                               ┌────────────┼────────────┐
                               ▼            ▼            ▼
                           PostgreSQL     Redis        Kafka
```

This architecture is common for applications that combine:

- Static frontend assets.
- Public APIs.
- Dynamic application responses.
- Media.
- Authentication.
- Backend services.

## Core Architectural Components

| Component | Responsibility |
|---|---|
| Viewer | Sends HTTP/HTTPS requests |
| CloudFront Distribution | Defines the CDN configuration boundary |
| Edge Location | Handles viewer traffic close to users |
| Cache | Stores eligible responses at CloudFront |
| Cache Behavior | Determines how requests matching a path are processed |
| Cache Policy | Determines cache-key and caching behavior |
| Origin Request Policy | Controls what request information is forwarded to the origin |
| Origin | Source of content when CloudFront cannot serve it from cache |
| Origin Group | Provides origin failover behavior |
| AWS WAF | Provides web application firewall controls |
| TLS Certificate | Provides HTTPS for the viewer-facing endpoint |
| Origin Access Control | Restricts supported AWS origins to authorized CloudFront access |
| Response Headers Policy | Adds or controls HTTP response headers |

## Viewer Layer

The viewer is any client communicating with CloudFront.

Typical viewers include:

- Web browsers.
- Mobile applications.
- JavaScript applications.
- REST API clients.
- IoT clients.
- Internal services using HTTP.
- Automated clients.

The viewer normally connects to a CloudFront distribution hostname or a custom application domain configured to route to CloudFront.

```text
Browser
   │
   │ HTTPS
   ▼
app.example.com
   │
   ▼
CloudFront
```

The viewer does not normally need to know where the origin is located.

This abstraction is valuable because the origin can change without requiring clients to change their URL.

## DNS and CloudFront

A production application commonly uses a custom domain:

```text
www.example.com
```

DNS directs the domain toward CloudFront.

Conceptually:

```text
www.example.com
       │
       ▼
     DNS
       │
       ▼
CloudFront Distribution
       │
       ▼
     Origin
```

The CloudFront distribution then handles the HTTP request.

The important distinction is:

- **DNS chooses where the hostname resolves.**
- **CloudFront determines how the HTTP request is processed after reaching the CDN.**

DNS does not perform cache-key evaluation, cache lookup, origin routing, or HTTP response caching.

## Edge Locations

CloudFront uses a globally distributed network of edge locations.

The purpose of an edge location is to process viewer traffic closer to the viewer than a centralized application origin may be.

A simplified model is:

```text
                         Origin
                           │
                           │
                ┌──────────┴──────────┐
                │                     │
          CloudFront Network    CloudFront Network
                │                     │
        ┌───────┼────────┐    ┌───────┼────────┐
        ▼       ▼        ▼    ▼       ▼        ▼
      Edge    Edge     Edge  Edge    Edge     Edge
        │       │        │    │       │        │
       User    User     User User    User     User
```

The exact request path and cache placement are controlled by CloudFront's distributed infrastructure. Engineers should therefore reason in terms of **viewer edge → CloudFront cache → origin**, rather than assuming that every viewer request travels directly to the origin region.

## Regional Edge Caches

CloudFront also uses larger regional caching layers in its architecture.

The simplified hierarchy is:

```text
Viewer
   │
   ▼
Edge Location
   │
   ├── Object available
   │       │
   │       ▼
   │    Response
   │
   └── Object unavailable
           │
           ▼
    Regional cache layer
           │
           ├── Object available
           │
           └── Origin request
```

The purpose of regional caching is to reduce repeated origin fetches when an object is not available at a particular edge location.

The exact internal routing is managed by CloudFront and should not be treated as a fixed topology that application code can control.

## Distribution

A CloudFront distribution is the primary configuration object that defines how CloudFront serves content.

A distribution associates:

- Viewer configuration.
- Origins.
- Cache behaviors.
- Cache policies.
- Origin request policies.
- TLS configuration.
- Response headers policies.
- Logging configuration.
- Security integrations.
- Routing behavior.

Conceptually:

```text
Distribution
│
├── Viewer Configuration
│
├── TLS Certificate
│
├── Default Cache Behavior
│
├── Additional Cache Behaviors
│
├── Origins
│   ├── S3
│   ├── ALB
│   └── Custom HTTP Origin
│
├── Cache Policies
├── Origin Request Policies
├── Response Headers Policies
└── Security / Logging Configuration
```

A distribution is therefore much more than a cache.

It defines the behavior of the entire CloudFront-facing application surface.

## Origins

An origin is the source from which CloudFront retrieves content when it cannot satisfy a request from its cache.

Common origin types include:

- Amazon S3.
- Application Load Balancer.
- Network Load Balancer where supported through appropriate origin configuration.
- API endpoints.
- EC2-hosted applications.
- Custom HTTP servers.
- Other AWS services exposed through supported origin configurations.

A common architecture is:

```text
CloudFront
   │
   ├── /static/*
   │       │
   │       ▼
   │      S3
   │
   └── /api/*
           │
           ▼
          ALB
           │
           ▼
      Django / FastAPI
```

This allows one distribution to serve multiple classes of workloads.

## Multiple Origins

A distribution can define multiple origins.

For example:

| Request Path | Origin | Typical Workload |
|---|---|---|
| `/static/*` | S3 | CSS, JavaScript, fonts |
| `/media/*` | S3 | User media |
| `/api/*` | ALB | REST API |
| `/images/*` | Image service | Dynamic images |

The cache behavior determines which origin handles a matching request.

## Cache Behaviors

Cache behaviors provide path-based request handling.

For example:

```text
Default: /*
    │
    └── Application Origin

/static/*
    │
    └── S3 Origin

/media/*
    │
    └── S3 Origin

/api/*
    │
    └── Application Origin
```

A cache behavior can define:

- Origin.
- Allowed HTTP methods.
- Viewer protocol policy.
- Cache policy.
- Origin request policy.
- Response headers policy.
- Compression behavior.
- Whether requests are cached.
- Additional request-processing settings.

Path matching therefore becomes an architectural routing mechanism.

## Default Cache Behavior

Every distribution has a default cache behavior.

It generally acts as the fallback when no more specific path pattern matches.

For example:

```text
/static/*
    → S3

/api/*
    → ALB

/*
    → ALB
```

A request for:

```text
/api/orders
```

matches `/api/*`.

A request for:

```text
/admin/dashboard
```

may fall through to `/*`.

The default behavior should be designed deliberately because it becomes the catch-all path for requests not matched by more specific behaviors.

## Path Matching

CloudFront evaluates cache behaviors according to path patterns.

A useful conceptual model is:

```text
Request
   │
   ▼
Path Pattern Matching
   │
   ├── /static/*
   │
   ├── /media/*
   │
   ├── /api/*
   │
   └── /*
```

The most specific matching behavior should be designed carefully.

A common production mistake is assuming that a broad default behavior will automatically have the desired security or caching settings for every application path.

Sensitive routes should receive explicit configuration when their requirements differ.

## Cache Policy

The cache policy controls the cache key and related caching behavior.

A simplified cache key can be represented as:

```text
Cache Key =
    Scheme/Host context
    +
    Path
    +
    Selected Query Strings
    +
    Selected Headers
    +
    Selected Cookies
```

The exact behavior depends on the CloudFront policy configuration.

The most important engineering concept is:

> If two requests produce different representations, they must not incorrectly share the same cached object.

For example:

```text
/products?category=books
```

and:

```text
/products?category=electronics
```

must not share a cached response if `category` changes the representation.

## Cache-Key Cardinality

Cache-key cardinality is a major production concern.

Suppose an endpoint receives:

```text
/api/products
```

and the cache key includes:

```text
Authorization
Cookie
User-Agent
X-Request-ID
X-Device-ID
```

The number of unique cache keys can grow rapidly.

Conceptually:

```text
Low Cardinality
      │
      ▼
High Cache Reuse
      │
      ▼
High Hit Ratio


High Cardinality
      │
      ▼
Low Cache Reuse
      │
      ▼
Low Hit Ratio
```

A request attribute should participate in caching only when it meaningfully affects the representation or required behavior.

## Origin Request Policy

The cache key and origin request are separate concepts.

An origin request policy controls which viewer request information is forwarded to the origin.

This distinction matters.

A request may contain:

```text
GET /products?category=books
Authorization: ...
Cookie: ...
User-Agent: ...
```

CloudFront may:

- Use only `category` as part of the cache key.
- Forward additional information to the origin.
- Avoid including certain information in the cache key.

This allows caching and origin communication to be designed independently.

## Cache Policy vs Origin Request Policy

| Concern | Cache Policy | Origin Request Policy |
|---|---|---|
| Cache key | Yes | No |
| Determines cache differentiation | Yes | No |
| Controls selected query strings | Yes | Can forward them |
| Controls selected headers | Yes | Can forward them |
| Controls selected cookies | Yes | Can forward them |
| Determines what reaches origin | Indirectly | Yes |
| Main purpose | Cache correctness and reuse | Origin request construction |

This distinction is frequently tested in interviews and is important when debugging unexpected cache behavior.

## Static Content Architecture

A highly cacheable static workload commonly uses:

```text
                 Browser
                    │
                    ▼
               CloudFront
                    │
                    ▼
                  S3
```

A production frontend may look like:

```text
CloudFront
│
├── index.html
├── app.8f91c2.js
├── app.71a8d4.css
├── vendor.29ab31.js
└── fonts/*
```

Static assets can use long TTLs when they are immutable.

The application can generate content-hashed filenames during CI/CD:

```text
app.js
    ↓
Build
    ↓
app.8f91c2.js
```

A future deployment generates:

```text
app.a721bd.js
```

The old and new assets can coexist safely.

## Dynamic API Architecture

Dynamic APIs usually require more careful caching.

A common architecture is:

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
Django / FastAPI
   │
   ├── PostgreSQL
   ├── Redis
   └── Microservices
```

For public, cacheable responses:

```text
GET /public/catalog
```

CloudFront may reduce origin traffic.

For personalized responses:

```text
GET /account/profile
Authorization: Bearer ...
```

caching requires significantly more care because the response may be specific to the authenticated user.

The architectural question is not:

> "Is this a GET request?"

It is:

> "Can the representation safely be reused by another request?"

## API Caching Decision Model

A useful decision process is:

```text
                Is response cacheable?
                         │
             ┌───────────┴───────────┐
             │                       │
            No                      Yes
             │                       │
             ▼                       ▼
        Forward to origin      What changes response?
                                     │
                                     ▼
                              Build cache policy
                                     │
                                     ▼
                              Validate cache key
```

Consider:

- Authentication.
- User identity.
- Tenant identity.
- Query parameters.
- Headers.
- Cookies.
- Locale.
- Content negotiation.
- Authorization.
- Response freshness.
- Data sensitivity.

## Security Architecture

CloudFront can form part of the public security boundary.

A common architecture is:

```text
                    Internet
                       │
                       ▼
                 CloudFront
                       │
                 ┌─────┴─────┐
                 │           │
                WAF         TLS
                 │           │
                 └─────┬─────┘
                       │
                       ▼
                 Application
                       │
                       ▼
                  Data Layer
```

Security responsibilities should be separated.

| Layer | Responsibility |
|---|---|
| CloudFront | Global HTTP delivery and edge configuration |
| AWS WAF | Web application filtering |
| Origin Access Control | Restrict supported AWS origins |
| ALB / Origin | Application ingress |
| Application | Authentication and authorization |
| Database | Data access controls |

CloudFront does not replace application authorization.

A request reaching Django or FastAPI still requires normal authentication and authorization checks when the endpoint requires them.

## Protecting the Origin

If CloudFront is intended to be the public entry point, direct origin access should be evaluated carefully.

A weak architecture may look like:

```text
Internet ───────────────► CloudFront ─────► Origin
    │
    └────────────────────────────────────► Origin
```

Clients can bypass CloudFront.

A stronger architecture aims for:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Protected Origin
```

For supported AWS origins, mechanisms such as CloudFront Origin Access Control can help ensure that access is performed through authorized CloudFront requests rather than unrestricted public access.

## TLS Architecture

HTTPS should generally be used for viewer connections.

```text
Client
  │
  │ HTTPS
  ▼
CloudFront
  │
  │ HTTPS
  ▼
Origin
```

TLS configuration has two separate architectural concerns:

1. Viewer-to-CloudFront encryption.
2. CloudFront-to-origin encryption.

Securing only the viewer connection does not automatically mean the complete path is encrypted.

Production systems should evaluate both legs independently.

## WAF Integration

AWS WAF can be integrated with CloudFront to filter malicious or unwanted requests at the edge.

```text
Client
   │
   ▼
CloudFront
   │
   ▼
AWS WAF
   │
   ├── Block
   │
   └── Allow
          │
          ▼
        Origin
```

This can reduce malicious traffic reaching the application infrastructure.

Typical controls include:

- IP filtering.
- Rate-based rules.
- Managed rule groups.
- Geographic restrictions where appropriate.
- Application-specific request filtering.

WAF should complement, not replace, application-level security.

## Origin Groups and Failover

CloudFront can use origin groups to support origin failover.

Conceptually:

```text
                 CloudFront
                     │
                     ▼
                Primary Origin
                     │
              ┌──────┴──────┐
              │             │
           Healthy        Failure
              │             │
              ▼             ▼
           Response    Secondary Origin
```

This is useful when the workload has a meaningful fallback origin.

However, origin failover does not automatically provide complete application disaster recovery.

For example:

```text
CloudFront
   │
   ▼
Secondary Origin
   │
   ▼
Same unavailable database
```

does not solve the underlying data-layer failure.

High availability must therefore be designed across the complete dependency graph.

## Multi-Region Architecture

For workloads requiring regional resilience, CloudFront can sit above multiple origin locations.

A conceptual architecture is:

```text
                         CloudFront
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
              Region A                Region B
                 │                       │
                 ▼                       ▼
              ALB/App                 ALB/App
                 │                       │
                 ▼                       ▼
              Data A                  Data B
```

The routing strategy must account for:

- Application state.
- Database replication.
- Session management.
- Write consistency.
- Failover detection.
- DNS.
- Deployment synchronization.
- Cache consistency.

CloudFront alone does not solve multi-region state management.

## Edge Processing

CloudFront can perform certain request and response processing at the edge.

This can be useful for:

- Request normalization.
- Header manipulation.
- Redirects.
- Lightweight routing logic.
- Authentication-related edge decisions where appropriate.
- Personalization or transformation scenarios that fit the supported edge execution model.

Edge logic should remain intentionally small.

Avoid moving complex business logic to the edge when it introduces:

- Difficult deployments.
- Complex debugging.
- Distributed state requirements.
- Tight coupling to edge execution.
- Significant operational complexity.

A good architectural principle is:

> Keep business-critical state and complex domain logic in the application layer unless there is a strong reason to execute it at the edge.

## Request Flow

The complete high-level request flow is:

```mermaid
sequenceDiagram
    participant Client
    participant DNS
    participant CF as CloudFront
    participant Cache as Edge Cache
    participant WAF as AWS WAF
    participant Origin
    participant App as Django/FastAPI

    Client->>DNS: Resolve application hostname
    DNS-->>Client: CloudFront endpoint
    Client->>CF: HTTPS request
    CF->>WAF: Evaluate request
    WAF-->>CF: Allow
    CF->>Cache: Evaluate cache key

    alt Cache Hit
        Cache-->>CF: Cached response
        CF-->>Client: Response
    else Cache Miss
        CF->>Origin: Origin request
        Origin->>App: Application request
        App-->>Origin: Application response
        Origin-->>CF: Origin response
        CF->>Cache: Store eligible response
        CF-->>Client: Response
    end
```

This lifecycle should be understood before troubleshooting any CloudFront performance or correctness issue.

## CloudFront With Nginx

CloudFront and Nginx can coexist.

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
Nginx
   │
   ▼
Django / FastAPI
```

The responsibilities are different:

| Component | Typical Responsibility |
|---|---|
| CloudFront | Global delivery and CDN caching |
| ALB | Load balancing and application ingress |
| Nginx | Reverse proxy, local routing, request handling |
| Django/FastAPI | Application and domain logic |
| Redis | Application caching / shared state |
| PostgreSQL | Persistent relational data |

Do not introduce Nginx simply because CloudFront exists. Each layer should have a clear responsibility.

## CloudFront With Kubernetes

CloudFront can also sit in front of Kubernetes-hosted workloads.

A conceptual architecture is:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Load Balancer
  │
  ▼
Kubernetes Ingress
  │
  ▼
Service
  │
  ▼
Django / FastAPI Pods
```

The CDN should primarily handle delivery concerns while Kubernetes handles:

- Workload scheduling.
- Pod lifecycle.
- Service discovery.
- Horizontal scaling.
- Application deployment.

CloudFront does not replace Kubernetes ingress or service networking.

## Cache Invalidation Architecture

When mutable content changes, invalidation can be used:

```text
Deployment
    │
    ▼
Publish new content
    │
    ▼
Create CloudFront invalidation
    │
    ▼
Cached object becomes invalid
    │
    ▼
Subsequent request fetches new content
```

For static immutable assets, versioning is generally preferable:

```text
app.js
  │
  ▼
app.a12f90.js
```

instead of repeatedly invalidating:

```text
/*
```

The architecture should distinguish between:

- **Mutable content requiring invalidation.**
- **Immutable content requiring versioned URLs.**

## Deployment Architecture

A cache-safe frontend deployment can follow:

```text
                Build
                  │
                  ▼
         Generate hashed assets
                  │
                  ▼
        Upload new static assets
                  │
                  ▼
      Publish/update HTML references
                  │
                  ▼
        Invalidate mutable HTML
                  │
                  ▼
              Release
```

The order matters.

If HTML references an asset that has not yet been uploaded, clients can receive a broken reference.

A safer strategy is:

```text
New Assets
    ↓
Available at Origin
    ↓
HTML references new Assets
    ↓
HTML becomes active
```

## Observability Architecture

CloudFront should be observable independently from the origin.

```text
                         Client
                           │
                           ▼
                      CloudFront
                           │
                 ┌─────────┴─────────┐
                 │                   │
             CDN Metrics          Logs
                 │                   │
                 ▼                   ▼
          Monitoring System     Log Analysis
                 │
                 ▼
             Alerting
```

Important operational signals include:

- Request volume.
- Cache hit ratio.
- Cache misses.
- 4xx responses.
- 5xx responses.
- Origin response latency.
- Data transfer.
- Distribution-level errors.
- Requests by path.
- Geographic request patterns.

The distinction between CloudFront errors and origin errors is particularly important.

## Troubleshooting Model

When a request behaves unexpectedly, analyze it in layers.

```text
Client
  │
  ▼
DNS
  │
  ▼
CloudFront
  │
  ├── Viewer configuration
  ├── Cache behavior
  ├── Cache policy
  ├── Cache key
  ├── WAF
  └── Cached object
  │
  ▼
Origin
  │
  ├── Load balancer
  ├── Nginx
  ├── Application
  ├── Redis
  └── Database
```

Useful questions include:

1. Did DNS resolve correctly?
2. Did the request reach CloudFront?
3. Which cache behavior matched?
4. Was the request a cache hit or miss?
5. What cache key was effectively used?
6. Was the request blocked by WAF?
7. Did CloudFront contact the origin?
8. What did the origin return?
9. Was the response eligible for caching?
10. Did the browser cache an older response?

## Scalability

CloudFront can absorb substantial amounts of cacheable traffic before requests reach the application.

For example:

```text
Without effective CDN caching:

1,000,000 requests
        │
        ▼
      ALB
        │
        ▼
  Application
        │
        ▼
    Database
```

With effective caching:

```text
1,000,000 requests
        │
        ▼
    CloudFront
        │
        ├── 900,000 cache hits
        │          │
        │          ▼
        │       Viewers
        │
        └── 100,000 origin requests
                    │
                    ▼
                  ALB
                    │
                    ▼
               Application
```

The numbers are illustrative, but the architectural principle is important: **cache effectiveness determines how much traffic the origin actually needs to process**.

## Reliability

CloudFront can improve the resilience of cacheable workloads by reducing dependency on the origin for every request.

However:

```text
CloudFront
   ↓
Origin
   ↓
Application
   ↓
Database
```

is still a dependency chain.

A senior-level architecture review should evaluate failure modes at each layer:

| Layer | Example Failure |
|---|---|
| DNS | Incorrect DNS configuration |
| CloudFront | Distribution/configuration issue |
| WAF | Incorrect blocking rule |
| Cache | Incorrect cache policy |
| Origin | Origin unavailable |
| ALB | Load balancing failure |
| Application | Deployment or runtime failure |
| Redis | Cache/state failure |
| PostgreSQL | Database failure |

## Disaster Recovery

CloudFront should be considered as one component of a broader disaster recovery design.

For a static application:

```text
CloudFront
   │
   ▼
S3
```

may provide a relatively simple architecture.

For a dynamic application:

```text
CloudFront
   │
   ▼
Regional Application
   │
   ▼
Regional Database
```

requires significantly more planning.

A multi-region design may need:

- Multiple application regions.
- Data replication.
- Origin failover.
- Automated health detection.
- Deployment synchronization.
- Session strategy.
- Recovery procedures.
- Infrastructure as code.
- Tested failover processes.

## Cost Considerations

CloudFront can reduce origin costs by serving cached content without contacting the backend.

However, total cost should consider:

- CloudFront request volume.
- Data transfer.
- Origin requests.
- ALB usage.
- Compute consumption.
- Database load.
- WAF usage.
- Logging.
- Invalidation patterns.
- Multi-region infrastructure.

A useful architectural metric is:

```text
Origin Cost
     ↓
depends partly on
     ↓
Origin Request Volume
     ↓
affected by
     ↓
CloudFront Cache Hit Ratio
```

Optimizing cache behavior can therefore have both performance and cost implications.

## Common Architectural Mistakes

### Treating CloudFront as a Replacement for the Backend

CloudFront is not a replacement for Django, FastAPI, Kubernetes, PostgreSQL, or other application components.

It is a delivery and edge-processing layer.

### Caching Personalized Responses

A response containing user-specific information can become a security issue if cached incorrectly.

Always understand whether:

```text
Response(User A) == Response(User B)
```

before enabling shared caching.

### Forwarding Everything to the Origin

Forwarding every header, cookie, and query string can dramatically increase cache-key diversity and reduce cache efficiency.

Only forward information that the origin actually needs.

### Using Long TTLs for Mutable URLs

This can create stale content that remains difficult to replace operationally.

Prefer:

```text
asset.<hash>.js
```

for immutable assets.

### Using Invalidation as the Default Deployment Mechanism

Invalidation is useful, but relying on large invalidations for every release can create unnecessary operational complexity.

Version immutable assets instead.

### Assuming CloudFront Solves Application Availability

CloudFront cannot compensate for an unavailable database or broken application deployment.

Availability must be designed end-to-end.

### Adding Too Many Infrastructure Layers

A system such as:

```text
CloudFront
  ↓
WAF
  ↓
ALB
  ↓
Nginx
  ↓
Kubernetes Ingress
  ↓
Service
  ↓
Application
```

may be valid, but every layer should have a clear responsibility.

Additional layers increase:

- Operational complexity.
- Debugging effort.
- Configuration surface.
- Latency.
- Failure modes.

## Production Best Practices

### Design Cacheability Before Configuration

Determine which resources are:

- Public.
- Private.
- Immutable.
- Mutable.
- Personalized.
- Authorization-dependent.

Then design cache policies around those semantics.

### Minimize Cache-Key Dimensions

Include only attributes that actually change the response.

### Prefer Immutable Static Assets

Use content hashes for frontend and static resources.

### Separate Static and Dynamic Origins

A common architecture is:

```text
/static/* → S3
/media/*  → S3
/api/*    → Application Origin
/*        → Application Origin
```

### Protect Origins

Avoid unnecessarily exposing origins directly to the public Internet.

### Monitor Cache Efficiency

Track cache hit ratio and origin request volume together.

### Test Cache Behavior

Validate:

- Cache hits.
- Cache misses.
- Query-string behavior.
- Header behavior.
- Cookie behavior.
- Authentication.
- Error responses.
- Invalidations.
- Rollbacks.

### Treat Configuration as Code

For production environments, CloudFront configuration should preferably be managed through infrastructure-as-code and reviewed through CI/CD.

This makes changes:

- Repeatable.
- Auditable.
- Reviewable.
- Reversible.

## Interview Traps

### Is CloudFront Only for Static Content?

No. It can also front dynamic HTTP applications and APIs, but dynamic caching requires careful cache-key and authorization design.

### Does CloudFront Replace an ALB?

Not necessarily. They solve different problems.

```text
CloudFront
    ↓
ALB
    ↓
Application
```

is a common architecture.

### Does a Cache Hit Reach Django?

Normally, a successful cache hit can be served without sending the request to the origin.

### Does Increasing TTL Always Improve Performance?

Not necessarily. Higher TTL improves cache persistence but can increase staleness.

### Does Forwarding More Information Improve Correctness?

Not automatically. Forwarding unnecessary information can increase cache fragmentation and reduce efficiency.

### Does CloudFront Make a Single-Region Application Multi-Region?

No. CloudFront provides global edge delivery, but application state and origin architecture remain separate concerns.

## Architecture Decision Checklist

Before deploying CloudFront for a production application, verify:

- [ ] The viewer-facing domain is correctly configured.
- [ ] HTTPS is enabled.
- [ ] Viewer and origin TLS requirements are understood.
- [ ] Origins are explicitly defined.
- [ ] Cache behaviors are intentionally designed.
- [ ] The default cache behavior is safe.
- [ ] Cache policies match application semantics.
- [ ] Origin request policies forward only required data.
- [ ] Personalized responses are not accidentally shared.
- [ ] Static assets use versioned URLs where appropriate.
- [ ] Mutable content has an invalidation strategy.
- [ ] Origin access is appropriately restricted.
- [ ] WAF requirements have been evaluated.
- [ ] Cache hit ratio is monitored.
- [ ] Origin errors are observable.
- [ ] Deployment ordering is cache-safe.
- [ ] Rollback behavior has been tested.
- [ ] Infrastructure configuration is version-controlled.
- [ ] Failure scenarios have been considered.
- [ ] Cost impact has been evaluated.

## Key Takeaways

- **CloudFront is an architectural layer between clients and origins:** It provides global delivery, caching, routing, TLS, and edge capabilities without replacing the backend application.
- **Distributions, origins, cache behaviors, and policies define the request path:** Understanding these relationships is essential for designing predictable production systems.
- **Caching is a correctness problem as well as a performance problem:** Cache keys must account for every request attribute that changes the response, especially authentication and personalization.
- **CloudFront improves scalability only when the architecture uses it effectively:** High cache reuse reduces origin traffic, while excessive cache-key cardinality can eliminate much of the benefit.
- **Production CloudFront design must be end-to-end:** Security, origin protection, observability, deployment strategy, availability, disaster recovery, and cost all need to be considered alongside caching.