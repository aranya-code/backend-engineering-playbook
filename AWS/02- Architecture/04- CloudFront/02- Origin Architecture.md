# 02- Origin Architecture

## Overview

A CloudFront origin is the backend location from which CloudFront retrieves content when the requested object is not already available in the edge cache.

An origin can be:

- An Amazon S3 bucket
- An Application Load Balancer
- An API Gateway endpoint
- An EC2-based application
- A Kubernetes ingress endpoint
- A custom HTTP server
- Another AWS service or externally hosted HTTP service

The important architectural distinction is:

> **CloudFront is the edge delivery layer; the origin is the authoritative source of the content or response.**

A production architecture should therefore treat origin selection, connectivity, authentication, failover, caching, and origin protection as explicit design decisions.

```text
                         Internet
                            │
                            │ HTTPS
                            ▼
                    ┌───────────────┐
                    │   CloudFront  │
                    │ Edge Network  │
                    └───────┬───────┘
                            │
                     Cache lookup
                       /       \
                     HIT       MISS
                      │          │
                      ▼          ▼
                   Response    Origin
                                  │
                       ┌──────────┼──────────┐
                       ▼          ▼          ▼
                      S3         ALB      Custom HTTP
                                  │
                                  ▼
                            Django/FastAPI
```

Origin architecture directly affects:

- Latency
- Availability
- Security
- Cache efficiency
- Scalability
- Cost
- Failure behavior
- Deployment strategy
- Disaster recovery

## What an Origin Is

An origin is the backend endpoint that CloudFront contacts when it needs to retrieve an object or generate a response.

For a static website:

```text
Browser
   │
   ▼
CloudFront
   │
   ▼
S3
```

For a backend API:

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
```

CloudFront does not normally replace the application or storage system. It sits in front of them and determines whether a request can be served from the edge or must be sent to the origin.

## Why Origins Exist

The origin remains the source of truth.

CloudFront provides:

- Edge caching
- Global request routing
- TLS termination
- Request filtering
- Compression and content optimization
- Origin shielding and request consolidation capabilities
- Integration with security controls

The origin provides the actual application or data.

This separation allows the architecture to scale independently:

```text
                  CloudFront
                      │
          ┌───────────┼───────────┐
          │           │           │
        Edge 1      Edge 2      Edge N
          │           │           │
          └───────────┼───────────┘
                      │
                    Origin
                      │
             ┌────────┼────────┐
             ▼        ▼        ▼
            App      DB      Cache
```

## Origin Types

| Origin Type | Typical Use | Main Strength | Main Concern |
|---|---|---|---|
| S3 | Static assets, media, downloads | Highly scalable object storage | Object semantics differ from HTTP applications |
| ALB | Django/FastAPI APIs | Integrates naturally with application infrastructure | Origin capacity still matters |
| API Gateway | Managed APIs | AWS-native API features | Cost and architectural complexity |
| EC2 | Custom applications | Flexible | Operational overhead |
| Kubernetes Ingress | Containerized services | Fits Kubernetes architecture | More moving parts |
| Custom HTTP origin | External services | Flexible | Internet connectivity and origin protection |

## S3 Origins

Amazon S3 is a natural CloudFront origin for static content.

Typical workloads include:

- JavaScript bundles
- CSS
- Images
- Fonts
- Videos
- Static websites
- Software downloads
- Public or private media

Architecture:

```text
User
 │
 ▼
CloudFront
 │
 ├── Cache HIT ───────► Response
 │
 └── Cache MISS
          │
          ▼
         S3
          │
          ▼
      Object Data
```

### Why Use S3

S3 provides durable object storage without requiring application servers to manage files.

CloudFront then moves frequently requested objects closer to viewers.

This is particularly effective for immutable assets:

```text
/static/app.8f3a91.js
/static/styles.2b4c11.css
/images/logo.v4.webp
```

The combination of immutable object naming and long TTLs can produce very high cache efficiency.

### S3 Origin Security

For private S3 content, keep the bucket private and grant CloudFront the required access using Origin Access Control where applicable.

Avoid:

```text
Internet ─────► Public S3
      │
      └───────► CloudFront
```

Prefer:

```text
Internet
   │
   ▼
CloudFront
   │
   │ controlled access
   ▼
Private S3
```

The security boundary should be explicit rather than relying on the obscurity of the S3 URL.

## Custom Origins

A custom origin is an HTTP endpoint that CloudFront can contact.

Common examples:

```text
CloudFront
   │
   ▼
Application Load Balancer
   │
   ▼
Django / FastAPI
```

or:

```text
CloudFront
   │
   ▼
Kubernetes Ingress
   │
   ▼
Service
   │
   ▼
Pods
```

Custom origins are appropriate when the content must be generated dynamically or when the backend is not stored in S3.

## CloudFront in Front of Django or FastAPI

A common production architecture is:

```text
                       Internet
                          │
                          ▼
                    CloudFront
                          │
                          ▼
                         ALB
                          │
                 ┌────────┴────────┐
                 ▼                 ▼
             Django API        FastAPI API
                 │                 │
                 └────────┬────────┘
                          ▼
                     PostgreSQL
```

CloudFront can provide:

- TLS termination
- Edge caching for cacheable endpoints
- WAF integration
- Geographic edge delivery
- Request routing
- Compression
- Security headers
- Origin load reduction

The application still handles:

- Authentication
- Authorization
- Business rules
- Database operations
- Transaction management
- Application validation

## Origin Domain Name

An origin configuration contains a domain name representing where CloudFront should send requests.

Examples:

```text
my-bucket.s3.amazonaws.com
```

```text
my-production-alb-123456789.region.elb.amazonaws.com
```

```text
api.internal.example.com
```

The origin hostname is an infrastructure detail. The public hostname should generally remain the application's CloudFront-backed domain:

```text
https://api.example.com
```

rather than exposing infrastructure-specific hostnames to clients.

## Origin Path

CloudFront can prepend a path to requests sent to an origin.

For example, if the origin path is:

```text
/api
```

and the viewer requests:

```text
/users
```

the origin request can be constructed around:

```text
/api/users
```

This can be useful when the origin hosts the application under a specific path.

However, origin path configuration should be kept simple. Complex path rewriting can make debugging difficult and should generally be handled deliberately through CloudFront behaviors, application routing, or an appropriate proxy layer.

## Origin Protocol Policy

CloudFront must determine how it communicates with the origin.

Typical choices are:

| Policy | Viewer → CloudFront | CloudFront → Origin | Use |
|---|---|---|---|
| HTTP only | HTTPS | HTTP | Generally unsuitable for sensitive production traffic |
| HTTPS only | HTTPS | HTTPS | Strong default for sensitive systems |
| Match viewer | HTTPS | Depends on viewer protocol | Useful when origin behavior intentionally follows viewer protocol |

For sensitive production systems, HTTPS between CloudFront and the origin is generally preferred.

```text
Client
  │ HTTPS
  ▼
CloudFront
  │ HTTPS
  ▼
Origin
```

Encrypting only the viewer connection does not automatically secure the origin leg.

## Origin Host Header

The HTTP `Host` header requires careful consideration when CloudFront communicates with a custom origin.

A backend may use the hostname to:

- Select a virtual host
- Generate absolute URLs
- Perform tenant routing
- Validate allowed hosts
- Select application configuration

For example, Django may use allowed-host configuration to reject unexpected hostnames.

```python
ALLOWED_HOSTS = [
    "api.example.com",
]
```

CloudFront's origin configuration and request policy should therefore be designed so that the origin receives the hostname expected by the application.

Incorrect host handling can cause:

- HTTP 400 responses
- Incorrect virtual-host routing
- Broken redirects
- Security validation failures
- Incorrect generated URLs

## Origin Request Flow

For a cache miss, the request path can be understood as:

```text
Viewer
  │
  │ GET /products/42
  ▼
CloudFront Edge
  │
  ├── Determine behavior
  ├── Construct cache key
  ├── Check cache
  │
  └── MISS
       │
       ├── Apply origin request policy
       ├── Select origin
       ├── Construct origin request
       └── Send request
              │
              ▼
            Origin
              │
              ▼
         Generate response
              │
              ▼
         CloudFront Edge
              │
              ├── Cache response if allowed
              │
              ▼
            Viewer
```

Understanding this lifecycle is essential when debugging CloudFront behavior.

## Multiple Origins

A distribution can contain multiple origins.

For example:

```text
                    CloudFront
                        │
              ┌─────────┼─────────┐
              │         │         │
              ▼         ▼         ▼
             S3        ALB       API
           Assets      API       Service
```

Different cache behaviors can route different paths to different origins.

Example:

| Path | Origin |
|---|---|
| `/static/*` | S3 |
| `/media/*` | S3 |
| `/api/*` | ALB |
| `/graphql` | API service |
| `/health` | ALB |

This allows one CloudFront distribution to front an entire application platform.

## Path-Based Origin Routing

A common architecture is:

```text
                    CloudFront
                        │
          ┌─────────────┼──────────────┐
          │             │              │
          ▼             ▼              ▼
      /static/*      /media/*       /api/*
          │             │              │
          ▼             ▼              ▼
         S3            S3             ALB
                                      │
                                      ▼
                                Django/FastAPI
```

This pattern is useful when static and dynamic workloads have fundamentally different characteristics.

Static content can have long TTLs:

```text
/static/app.123abc.js
```

while APIs may have:

```text
Cache-Control: no-store
```

or short TTLs.

## Origin Groups

CloudFront can associate origins into an origin group for failover.

A simplified architecture is:

```text
CloudFront
     │
     ▼
Primary Origin
     │
     │ failure
     ▼
Secondary Origin
```

For example:

```text
Primary:   ALB in Region A
Secondary: ALB in Region B
```

Origin groups are useful when continuity is more important than always serving from the primary origin.

The failover policy must be designed carefully because failover is based on configured origin failure criteria, not arbitrary application business logic.

## Origin Failover

A typical flow is:

```text
Viewer
  │
  ▼
CloudFront
  │
  ▼
Primary Origin
  │
  ├── Success ─────► Response
  │
  └── Configured failure
          │
          ▼
     Secondary Origin
          │
          ▼
       Response
```

Failover is not a substitute for proper application high availability.

If the primary application is returning a valid HTTP response with incorrect business data, CloudFront may not consider that a transport/origin failure.

Therefore:

> **Failover mechanisms must be designed around the actual failure modes the system needs to tolerate.**

## Origin Shielding

CloudFront can use an Origin Shield layer to consolidate requests before they reach the origin.

Conceptually:

```text
Users
 │
 ├── Edge A ──┐
 ├── Edge B ──┼──► Origin Shield ───► Origin
 ├── Edge C ──┤
 └── Edge D ──┘
```

This can reduce the number of requests reaching the origin, particularly when many edge locations experience cache misses for the same objects.

Origin Shield can be useful for:

- Large traffic volumes
- Expensive origins
- Content with cacheable responses
- Globally distributed traffic
- Reducing origin request concentration

It is not universally necessary. Additional architecture should have a measurable benefit.

## Origin Shield vs Redis

Origin Shield and Redis solve different problems.

| Technology | Primary Purpose |
|---|---|
| CloudFront | Global HTTP edge caching |
| Origin Shield | Consolidating CloudFront cache misses toward an origin |
| Redis | Application-level data caching |
| PostgreSQL | Durable relational data |

For example:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Origin Shield
  │
  ▼
FastAPI
  │
  ▼
Redis
  │
  ▼
PostgreSQL
```

Each layer operates at a different level.

CloudFront should not be treated as a replacement for application caching, and Redis should not be treated as a replacement for CDN caching.

## Origin Protection

Origin protection is critical when CloudFront is intended to be the public entry point.

A weak architecture is:

```text
Internet
  │
  ├────────► CloudFront ─────► ALB
  │
  └────────► ALB directly
```

This allows an attacker to bypass CloudFront controls.

A stronger design intentionally restricts the origin path:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Protected Origin
```

Origin protection should consider:

- Direct origin reachability
- Security groups
- Network architecture
- Application-level validation
- Origin authentication
- DNS exposure
- WAF placement
- Rate limiting

Do not rely solely on an obscure origin hostname.

## Origin Authentication

Some origins require CloudFront to authenticate when retrieving content.

For S3, Origin Access Control is a key mechanism.

For custom origins, authentication may be implemented through:

- Custom headers
- Application-level authentication
- Mutual TLS where supported by the architecture
- Network-level controls
- Private connectivity patterns

Custom headers can be useful but should not be treated as a strong secret merely because the browser does not see them.

If an origin can be directly reached by attackers, any header-based protection must be evaluated carefully.

## Origin Response Handling

CloudFront receives the origin response and determines whether it can:

- Return it directly
- Cache it
- Apply configured response behavior
- Route the request through additional processing

The origin response should therefore contain appropriate HTTP caching semantics.

For example:

```http
Cache-Control: public, max-age=31536000, immutable
```

is appropriate for a versioned static asset.

Whereas:

```http
Cache-Control: private, no-store
```

is appropriate for sensitive personalized data.

CloudFront configuration should complement application cache headers rather than blindly overriding them.

## Origin Timeout and Latency

Origin latency directly affects cache misses.

A request can be modeled as:

```text
Viewer
  │
  ▼
CloudFront
  │
  ├── Cache HIT
  │      └── Low latency
  │
  └── Cache MISS
         │
         ▼
       Origin
         │
         ├── Network latency
         ├── Application processing
         ├── Redis access
         └── Database access
```

For APIs:

```text
CloudFront
    │
    ▼
ALB
    │
    ▼
Django
    │
    ├── Redis
    │
    └── PostgreSQL
```

A slow database query can therefore appear to the client as a CloudFront origin latency problem.

When troubleshooting, decompose the latency rather than assuming CloudFront itself is slow.

## Origin Capacity Planning

CloudFront reduces origin load only when responses are cacheable and requests actually achieve cache hits.

For an API with:

```text
10,000 requests/second
```

a cache hit ratio of:

```text
95%
```

could dramatically reduce origin traffic for cacheable requests.

But if the endpoint is personalized and effectively uncacheable:

```text
10,000 requests/second
        │
        ▼
CloudFront
        │
        ▼
~10,000 origin requests/second
```

CloudFront still provides edge routing and security capabilities, but it does not eliminate application capacity requirements.

Capacity planning should therefore consider:

- Cache hit ratio
- Request distribution
- Origin latency
- Peak traffic
- Burst traffic
- Cache TTL
- Error rates
- Database capacity
- Redis capacity
- Connection pools

## Origin Connection Management

CloudFront maintains connections to origins rather than requiring every viewer connection to create an independent backend connection.

This can reduce connection overhead between globally distributed viewers and the origin.

The architecture effectively separates:

```text
Millions of viewer connections
          │
          ▼
      CloudFront
          │
          ▼
Fewer origin-side connections
          │
          ▼
        ALB
```

However, the backend still needs appropriate:

- Connection pool sizing
- Worker configuration
- Load-balancer capacity
- Database connection management
- Timeout configuration

CloudFront does not eliminate backend resource constraints.

## Origin Architecture for Microservices

CloudFront generally should not become a replacement for an internal service mesh or API gateway.

A common architecture is:

```text
                       Internet
                           │
                           ▼
                      CloudFront
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
                 /api/*       /static/*
                    │             │
                    ▼             ▼
                   ALB            S3
                    │
                    ▼
             API Gateway / Ingress
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       Service A Service B Service C
```

CloudFront handles global edge concerns.

Internal routing remains responsible for service-to-service communication.

For example:

- REST between public API services
- gRPC between internal services
- Kafka for asynchronous events
- Redis for caching
- PostgreSQL for relational persistence

## CloudFront and Nginx

Nginx can still be useful behind CloudFront.

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

Nginx may provide:

- Local reverse proxying
- Request buffering
- Internal routing
- Static file handling
- Application server integration

However, avoid duplicating functionality without a clear reason.

For example, if CloudFront already handles global caching, adding multiple independent caching layers can make invalidation and debugging significantly harder.

## Origin Architecture for Kubernetes

A Kubernetes-backed architecture can look like:

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
   ▼
Service
   │
   ▼
Pods
```

The responsibilities should remain clear:

| Layer | Responsibility |
|---|---|
| CloudFront | Global edge delivery |
| WAF | Edge HTTP security |
| Load Balancer | AWS ingress and traffic distribution |
| Kubernetes Ingress | Cluster-level routing |
| Service | Stable pod endpoint |
| Pods | Application execution |

Avoid placing every routing concern into CloudFront merely because it supports path-based behaviors.

## Origin Health and Monitoring

Origin architecture must be observable.

Important metrics include:

- Origin latency
- Origin response count
- Origin 4xx responses
- Origin 5xx responses
- Cache hit ratio
- Requests per second
- Data transfer
- Error rate
- Failover events
- Origin connection behavior

A useful debugging chain is:

```text
Client
  │
  ▼
CloudFront
  │
  ├── Cache metrics
  │
  ▼
Origin
  │
  ├── ALB metrics
  │
  ▼
Application
  │
  ├── Django/FastAPI metrics
  │
  ▼
Dependencies
  │
  ├── Redis
  └── PostgreSQL
```

This makes it possible to distinguish:

```text
CloudFront issue
```

from:

```text
Origin issue
```

from:

```text
Application issue
```

from:

```text
Database issue
```

## Security Considerations

Origin architecture should enforce defense in depth.

Important controls include:

- HTTPS between CloudFront and the origin where appropriate.
- Private S3 buckets.
- Origin Access Control for S3.
- Restricted origin network access.
- AWS WAF at the CloudFront layer.
- Application authentication and authorization.
- Least-privilege IAM.
- Secure origin credentials.
- No unnecessary public origin endpoints.
- Controlled request headers.
- Careful cache-key design.

The origin should not assume that every request came through a trusted browser.

## Reliability Considerations

A single origin may become a single point of failure.

For example:

```text
CloudFront
    │
    ▼
Single ALB
    │
    ▼
Single Region
```

The ALB itself can be highly available within a region, but regional failure remains a separate concern.

For stronger resilience:

```text
                     CloudFront
                         │
                 ┌───────┴───────┐
                 ▼               ▼
             Region A         Region B
                 │               │
                ALB             ALB
                 │               │
              Service         Service
```

Multi-region architecture should only be introduced when the business availability requirement justifies the additional operational complexity.

## Cost Considerations

Origin architecture affects cost through:

- CloudFront data transfer
- Origin requests
- S3 requests
- ALB usage
- Application compute
- Data transfer between services
- Database usage
- Cross-region traffic

Higher cache hit ratios can reduce origin request volume and backend compute.

However, adding layers such as:

```text
CloudFront
   │
Origin Shield
   │
ALB
   │
Nginx
   │
Application
```

should be justified by measurable operational or performance benefits.

Architecture should optimize the complete system rather than one metric.

## Common Mistakes

### Treating Every Origin as Equivalent

S3, ALB, and custom HTTP origins have different operational and security characteristics.

**Better approach:** Design origin configuration around the workload.

### Making the Origin Public Without Considering Bypass

A publicly reachable ALB can allow users to bypass CloudFront.

**Better approach:** Treat origin reachability as an explicit security decision.

### Using CloudFront as an Internal Service Router

CloudFront is primarily an edge delivery layer.

**Better approach:** Use appropriate internal routing, service discovery, API gateways, ingress controllers, or service meshes for internal communication.

### Assuming CloudFront Eliminates Origin Scaling

Uncacheable dynamic requests still reach the origin.

**Better approach:** Capacity-plan the origin based on the expected cache miss rate.

### Overusing Multiple Origins

Multiple origins introduce routing complexity.

**Better approach:** Add an origin only when there is a clear separation of workload, security boundary, availability requirement, or deployment concern.

### Ignoring Host Header Behavior

The application may reject or misinterpret the origin request.

**Better approach:** Explicitly validate hostname and routing behavior during integration testing.

### Using Failover Without Testing Failure Conditions

A configured secondary origin does not guarantee that failover will behave as expected.

**Better approach:** Test the actual origin failure conditions in a controlled environment.

## Production Decision Matrix

| Requirement | Recommended Origin Pattern |
|---|---|
| Static assets | S3 |
| Private static assets | Private S3 + OAC |
| Django/FastAPI API | ALB or appropriate HTTP origin |
| Kubernetes backend | Load Balancer / Ingress |
| Multiple workload types | Multiple CloudFront origins + behaviors |
| Regional resilience | Origin groups or multi-region architecture where justified |
| Expensive global origin | Consider Origin Shield |
| High-volume immutable assets | S3 + long cache TTLs |
| Personalized API | Dynamic application origin with conservative caching |
| Internal microservices | Do not expose each service directly through CloudFront |

## Production Design Checklist

Before deploying a CloudFront origin architecture, verify:

- [ ] The origin type matches the workload.
- [ ] Origin connectivity uses the required protocol.
- [ ] Origin access is intentionally controlled.
- [ ] S3 origins are private where appropriate.
- [ ] OAC is configured for private S3 access where applicable.
- [ ] Direct origin bypass has been considered.
- [ ] Cache behaviors map to the correct origins.
- [ ] Origin request policies forward only required values.
- [ ] Cache policies do not create security or correctness issues.
- [ ] Origin timeouts match application behavior.
- [ ] Origin capacity is sufficient for cache misses.
- [ ] Origin monitoring is configured.
- [ ] Failure behavior has been tested.
- [ ] Multi-region architecture is used only when justified.
- [ ] Deployment configuration is managed through infrastructure as code where practical.

## Key Takeaways

- **The origin is the authoritative backend behind CloudFront:** choose S3, ALB, Kubernetes ingress, or another HTTP origin based on the workload rather than treating them interchangeably.
- **Origin architecture determines security and reliability:** protect the origin from unintended direct access and explicitly design failover and multi-region behavior where required.
- **CloudFront reduces origin load primarily through caching:** uncacheable or personalized requests still require backend capacity.
- **Keep responsibilities separated:** CloudFront handles edge delivery, while ALB, Kubernetes, Django/FastAPI, Redis, PostgreSQL, and internal service infrastructure handle their respective layers.
- **Design for observability and failure:** origin latency, errors, cache misses, failover behavior, and backend dependencies must be monitored as one request path.