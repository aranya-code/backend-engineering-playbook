# 02- Global Infrastructure and Components

## Overview

Amazon CloudFront is a globally distributed content delivery network (CDN) that places application content closer to viewers. Its architecture is built around a distributed edge network, regional infrastructure, origins, and a control plane that manages distribution configuration.

For backend engineers, understanding CloudFront's global infrastructure is important because it explains:

- Where viewer requests are processed.
- Why latency decreases when content is cached near users.
- How CloudFront communicates with origins.
- Why cache behavior differs from origin infrastructure.
- How CloudFront scales globally without requiring application servers in every location.
- Where security, routing, caching, and edge processing occur.

A simplified architecture is:

```text
                         Global Users
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
        Edge Location    Edge Location    Edge Location
             │                │                │
             └────────────────┼────────────────┘
                              │
                              ▼
                     CloudFront Network
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
             S3 Origin                Application Origin
                                         │
                                         ▼
                                    ALB / Nginx
                                         │
                                         ▼
                                  Django / FastAPI
```

The key architectural principle is that **viewer-facing infrastructure is globally distributed while application origins can remain concentrated in one or a small number of AWS Regions**.

## CloudFront Global Architecture

CloudFront separates global content delivery from origin infrastructure.

A typical deployment looks like:

```text
                     Internet
                         │
             ┌───────────┼───────────┐
             │           │           │
             ▼           ▼           ▼
          Viewer A    Viewer B    Viewer C
             │           │           │
             ▼           ▼           ▼
          CloudFront  CloudFront  CloudFront
          Edge        Edge        Edge
             │           │           │
             └───────────┼───────────┘
                         │
                         ▼
                   Origin Region
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
             S3                    ALB
                                    │
                                    ▼
                              Application
```

The edge network handles requests close to viewers, while the origin remains responsible for generating or storing the authoritative content.

This separation allows an application to serve globally distributed users without deploying a complete application stack in every geographic market.

## Edge Locations

An edge location is a CloudFront point of presence where CloudFront can process viewer requests and cache content.

Conceptually:

```text
Viewer in India
      │
      ▼
Nearby CloudFront Edge
      │
      ▼
Cached Content
```

If the requested object is cached at that edge, CloudFront can return it without contacting the origin.

For a cache miss:

```text
Viewer
  │
  ▼
Edge Location
  │
  ▼
CloudFront Origin Path
  │
  ▼
Origin
```

Edge locations are therefore the first major infrastructure layer encountered by viewers.

## Why Edge Locations Exist

The fundamental problem CloudFront solves is network distance.

Without a CDN:

```text
Viewer in Asia
      │
      │ Long network path
      ▼
Application in US Region
```

With CloudFront:

```text
Viewer in Asia
      │
      ▼
Nearby Edge Location
      │
      ├── Cache Hit → Response
      │
      └── Cache Miss → Origin
```

For cacheable content, most of the request can terminate at the edge.

This can reduce:

- Network latency
- Origin traffic
- Application CPU usage
- Database load
- Origin bandwidth
- Regional infrastructure pressure

## Points of Presence

CloudFront's global network consists of distributed points of presence that allow viewer requests to enter AWS's edge infrastructure close to the user.

A useful mental model is:

```text
                     CloudFront
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
      PoP A             PoP B             PoP C
        │                 │                 │
     Users             Users             Users
```

The exact physical routing and internal network topology are AWS-managed implementation details.

From an application architecture perspective, the important distinction is:

```text
Viewer-facing edge infrastructure
            vs.
Regional origin infrastructure
```

## CloudFront Regional Infrastructure

CloudFront is not limited to the individual edge location where a viewer request initially arrives.

CloudFront uses a globally distributed architecture with additional regional infrastructure between edge locations and origins.

A simplified conceptual model is:

```text
Viewer
  │
  ▼
Edge Location
  │
  ▼
Regional CloudFront Infrastructure
  │
  ▼
Origin
```

This allows CloudFront to optimize communication between the global edge network and origins.

The exact internal routing is managed by AWS and should not be treated as a fixed application-visible topology.

## Regional Edge Caches

Regional edge caches provide an additional caching layer between CloudFront edge locations and origins.

Conceptually:

```text
                    Origin
                       ▲
                       │
                Regional Edge Cache
                       ▲
                       │
                 Edge Location
                       ▲
                       │
                    Viewer
```

This creates a hierarchy of caching.

A request can potentially find content at a nearby edge location without going farther into the CloudFront network.

If it is not available there, CloudFront can use its regional infrastructure before contacting the origin.

The purpose is to reduce repeated origin retrievals for content that is requested across multiple edge locations within a broader geographic region.

## Edge Cache vs Regional Edge Cache

| Layer | Primary purpose |
|---|---|
| Edge cache | Serve content close to the viewer |
| Regional edge cache | Provide an additional shared caching layer closer to origins |
| Origin | Authoritative content source |

A simplified hierarchy is:

```text
Viewer
  │
  ▼
Edge Cache
  │
  │ Miss
  ▼
Regional Edge Cache
  │
  │ Miss
  ▼
Origin
```

The exact behavior depends on the CloudFront configuration and AWS-managed infrastructure.

The important architectural idea is that **CloudFront can use multiple caching layers before a request reaches the origin**.

## Cache Hierarchy

The caching architecture can be visualized as:

```mermaid
flowchart TD
    V[Viewer] --> E[CloudFront Edge Cache]
    E -->|Hit| R1[Return Response]
    E -->|Miss| REC[Regional Edge Cache]

    REC -->|Hit| R2[Return Response]
    REC -->|Miss| O[Origin]

    O --> REC
    REC --> E
    E --> R1
```

This hierarchy allows frequently accessed objects to remain distributed across CloudFront's network.

The architectural benefit is that an origin does not necessarily need to serve every cache miss at every individual edge location independently.

## Origin Infrastructure

An origin is the authoritative source from which CloudFront obtains content.

Common origins include:

- Amazon S3
- Application Load Balancer
- Amazon API Gateway
- EC2-based applications
- Custom HTTP servers
- Other HTTP endpoints

For example:

```text
CloudFront
    │
    ├── Static Content
    │       │
    │       ▼
    │      S3
    │
    └── Dynamic Content
            │
            ▼
           ALB
            │
            ▼
        Django / FastAPI
```

CloudFront does not replace the origin.

It reduces the amount of traffic that must reach it.

## S3 as an Origin

S3 is a common CloudFront origin for static content.

Typical content includes:

```text
/static/app.js
/static/styles.css
/images/logo.png
/videos/intro.mp4
/fonts/inter.woff2
```

Architecture:

```text
Viewer
  │
  ▼
CloudFront
  │
  ▼
S3
```

This architecture is particularly effective because static content can often be cached for long periods.

For content-hashed assets:

```text
app.7f31c2.js
styles.91a82d.css
```

long cache lifetimes can be used safely because a new deployment produces a new object name.

## Application Load Balancer as an Origin

CloudFront can sit in front of an Application Load Balancer.

```text
Viewer
  │
  ▼
CloudFront
  │
  ▼
ALB
  │
  ├── Application Server
  ├── Application Server
  └── Application Server
```

This is a common architecture for Django and FastAPI systems.

The ALB handles regional load balancing while CloudFront provides global edge delivery.

## CloudFront and Nginx

Nginx can exist behind CloudFront and an ALB:

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

The responsibilities differ:

| Component | Responsibility |
|---|---|
| CloudFront | Global edge delivery and caching |
| ALB | Regional load balancing |
| Nginx | Reverse proxying and application traffic management |
| Django/FastAPI | Business logic |
| Redis | Application-level caching |
| PostgreSQL | Persistent storage |

Each layer should have a clear architectural purpose.

## CloudFront and API Workloads

CloudFront can also front REST APIs.

For example:

```text
https://api.example.com/users
```

can follow:

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
  ▼
PostgreSQL
```

However, API traffic requires more careful cache design than static content.

Public, cacheable API responses may benefit from CloudFront caching.

Authenticated or personalized responses often require different behavior.

For example:

```text
GET /api/products/42
```

may be cacheable.

While:

```text
GET /api/me
Authorization: Bearer <token>
```

is generally user-specific and requires careful handling.

## CloudFront and Microservices

CloudFront can serve as the public edge layer in front of a microservices platform.

For example:

```text
                         CloudFront
                              │
                              ▼
                         ALB / API Layer
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
       User Service      Order Service     Product Service
            │                 │                 │
            ▼                 ▼                 ▼
         Redis             Kafka           PostgreSQL
```

CloudFront handles external HTTP delivery.

Internal service communication can use:

- REST
- gRPC
- Kafka
- Other internal messaging mechanisms

CloudFront should not be considered an internal service-to-service communication mechanism.

## CloudFront and Kubernetes

CloudFront can front Kubernetes workloads.

A common architecture is:

```text
User
  │
  ▼
CloudFront
  │
  ▼
Application Load Balancer
  │
  ▼
Kubernetes Ingress
  │
  ▼
Kubernetes Service
  │
  ▼
Pods
```

Responsibilities remain separated:

```text
CloudFront
    → Global delivery

ALB / Ingress
    → Regional traffic routing

Kubernetes
    → Workload orchestration

Application
    → Business logic
```

CloudFront does not replace Kubernetes networking or service discovery.

## CloudFront Distribution

A distribution is the primary CloudFront configuration boundary.

It defines how CloudFront handles:

- Origins
- Cache behaviors
- Domain names
- TLS
- Cache policies
- Origin request policies
- Response headers
- WAF integration
- Edge processing
- Logging

A simplified distribution structure is:

```text
CloudFront Distribution
│
├── Origins
│   ├── S3
│   └── ALB
│
├── Default Cache Behavior
│
├── Additional Cache Behaviors
│   ├── /static/*
│   ├── /images/*
│   └── /api/*
│
├── Security
│   ├── TLS
│   └── WAF
│
└── Edge Processing
    ├── CloudFront Functions
    └── Lambda@Edge
```

The distribution is therefore the configuration layer that connects CloudFront's global infrastructure to application-specific routing and caching behavior.

## Cache Behaviors

Cache behaviors determine how CloudFront handles specific URL path patterns.

For example:

```text
/static/*
    → S3
    → Long TTL

/images/*
    → S3
    → Long TTL

/api/*
    → ALB
    → Controlled caching

/*
    → ALB
    → Default behavior
```

This allows a single public domain to expose multiple workloads.

For example:

```text
https://example.com/static/app.js
https://example.com/images/logo.png
https://example.com/api/products
```

can all be handled by one distribution while using different infrastructure.

## Global vs Regional Responsibilities

One of the most important CloudFront architectural concepts is understanding what is global and what remains regional.

| Responsibility | Typical scope |
|---|---|
| Viewer edge delivery | Global |
| CloudFront distribution configuration | Global |
| Edge caching | Global/distributed |
| WAF associated with CloudFront | Global scope |
| S3 bucket | AWS Region |
| ALB | AWS Region |
| EC2 | AWS Region |
| RDS | AWS Region |
| Django/FastAPI application | AWS Region(s) |
| PostgreSQL | AWS Region(s) |
| Redis | AWS Region(s) |

The CDN can be global even when the backend remains regional.

## Global Delivery With a Regional Backend

Consider an application deployed only in `us-east-1`.

Without CloudFront:

```text
India User
    │
    └──────────────► US Application
```

With CloudFront:

```text
India User
    │
    ▼
CloudFront Edge
    │
    ├── Cache Hit → Response
    │
    └── Cache Miss
             │
             ▼
        US Application
```

CloudFront reduces the latency for cacheable content because the response can terminate at the edge.

However, a cache miss still requires communication with the regional origin.

This distinction is critical when evaluating application latency.

## Origin Shield

Origin Shield provides an additional centralized caching layer intended to reduce repeated requests reaching an origin.

A simplified architecture is:

```text
Multiple CloudFront Edges
        │
        ▼
    Origin Shield
        │
        ▼
      Origin
```

Without such a centralized layer, multiple edge locations may independently require content from the origin.

With Origin Shield:

```text
Edge A ──┐
Edge B ──┼──► Origin Shield ──► Origin
Edge C ──┘
```

This can be useful when:

- The origin is expensive.
- Content is requested from many geographic locations.
- Origin request consolidation provides operational value.
- The application experiences high cache-miss volume.

Origin Shield should be evaluated based on workload characteristics rather than enabled automatically.

## Origin Shield vs Regional Edge Cache

These concepts are related but serve different architectural purposes.

| Component | Primary role |
|---|---|
| Edge cache | Serve content close to viewers |
| Regional edge cache | Intermediate CloudFront caching layer |
| Origin Shield | Additional centralized caching layer for origin protection |

A simplified model is:

```text
Viewer
  │
  ▼
Edge
  │
  ▼
Regional CloudFront Infrastructure
  │
  ▼
Origin Shield
  │
  ▼
Origin
```

The exact internal path is AWS-managed and can vary by CloudFront behavior.

## Global Network Routing

CloudFront determines an appropriate edge location for viewer traffic using AWS-managed network routing.

The application does not need to manually select an edge location.

Conceptually:

```text
Viewer
  │
  ▼
DNS / Network Routing
  │
  ▼
Appropriate CloudFront Edge
```

This means application developers generally reason about:

```text
CloudFront Distribution
```

rather than:

```text
Individual Edge Server
```

AWS manages the physical distribution and routing of the edge network.

## TLS at the Edge

HTTPS normally terminates at CloudFront for viewer connections.

```text
Viewer
  │
  │ HTTPS
  ▼
CloudFront
  │
  │ HTTP or HTTPS
  ▼
Origin
```

For production systems, HTTPS should generally be used on both sides:

```text
Viewer
  │
  │ HTTPS
  ▼
CloudFront
  │
  │ HTTPS
  ▼
Origin
```

This protects data across both network segments.

The viewer-facing TLS certificate and origin-facing TLS configuration are separate concerns.

## AWS WAF at the Edge

AWS WAF can be associated with CloudFront to inspect viewer requests before they reach the origin.

```text
Viewer
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

This allows unwanted requests to be rejected before they consume regional application resources.

Typical controls include:

- IP restrictions
- Rate-based rules
- Managed rule groups
- SQL injection protection
- Cross-site scripting protection
- Application-specific filtering

## Edge Processing

CloudFront supports edge processing through services such as:

- CloudFront Functions
- Lambda@Edge

A simplified architecture is:

```text
Viewer
  │
  ▼
CloudFront
  │
  ▼
Edge Function
  │
  ▼
Cache / Origin
```

Good use cases include:

- URL normalization
- Redirects
- Header transformations
- Lightweight request manipulation

Business-critical application logic generally belongs in Django, FastAPI, or another backend service.

## CloudFront Functions

CloudFront Functions are designed for lightweight JavaScript-based edge processing.

They are useful when logic needs to execute at the edge with low overhead.

Examples include:

```text
HTTP → HTTPS redirect
URL normalization
Simple header manipulation
Simple URL rewriting
```

A useful design rule is:

```text
Simple delivery transformation
        ↓
CloudFront Functions
```

rather than:

```text
Business workflow
        ↓
CloudFront Functions
```

## Lambda@Edge

Lambda@Edge provides more advanced edge execution capabilities than CloudFront Functions.

It can be useful when request or response processing requires capabilities beyond lightweight edge transformations.

The architectural trade-off is increased complexity.

Before moving logic to Lambda@Edge, evaluate whether the same requirement can be implemented more simply:

```text
CloudFront configuration
        ↓
CloudFront Function
        ↓
Application
```

Avoid creating distributed business logic that becomes difficult to test, deploy, and troubleshoot.

## Request Flow Through the Global Infrastructure

A simplified global request path is:

```mermaid
sequenceDiagram
    participant U as Viewer
    participant E as CloudFront Edge
    participant R as Regional Edge Infrastructure
    participant O as Origin
    participant A as Application

    U->>E: HTTPS Request
    E->>E: Select Distribution
    E->>E: Select Cache Behavior
    E->>E: Cache Lookup

    alt Cache Hit
        E-->>U: Cached Response
    else Cache Miss
        E->>R: Retrieve Through CloudFront Network
        R->>O: Origin Request
        O->>A: Application Request
        A-->>O: Response
        O-->>R: Origin Response
        R-->>E: Response
        E-->>U: Response
    end
```

This is a conceptual architecture diagram. AWS manages the actual internal network path.

## Data Flow

A useful way to understand CloudFront is to separate the data flow into three paths.

### Viewer-to-Edge

```text
Viewer
  │
  ▼
CloudFront Edge
```

This is the global delivery path.

### Edge-to-Origin

```text
CloudFront Edge
  │
  ▼
CloudFront Regional Infrastructure
  │
  ▼
Origin
```

This is used when CloudFront requires content from the origin.

### Origin-to-Viewer

```text
Origin
  │
  ▼
CloudFront
  │
  ▼
Edge
  │
  ▼
Viewer
```

The response can then be cached for future requests when appropriate.

## CloudFront and Backend Scalability

CloudFront can significantly reduce origin load when content is cacheable.

Consider:

```text
1,000,000 Viewer Requests
            │
            ▼
        CloudFront
            │
      ┌─────┴─────┐
      │           │
  900,000 Hits 100,000 Misses
      │           │
      │           ▼
      │         Origin
      │           │
      │           ▼
      │       Application
      │           │
      │           ▼
      │       PostgreSQL
      │
      ▼
    Viewers
```

The numbers are illustrative.

The architectural principle is:

```text
More cache hits
      ↓
Fewer origin requests
      ↓
Less backend work
      ↓
Greater effective scalability
```

CloudFront therefore acts as an origin-load reduction layer.

## CloudFront Does Not Eliminate Backend Scaling

Dynamic traffic still reaches the origin.

For example:

```text
POST /api/orders
PATCH /api/orders/42
GET /api/me
```

may require application processing.

The backend must therefore still be designed for:

- Cache misses
- Dynamic traffic
- Authentication
- Database load
- Traffic spikes
- Dependency failures
- Deployment events

A CDN should reduce origin load, not become the justification for under-sizing the backend.

## CloudFront and Redis

CloudFront and Redis operate at different caching layers.

```text
                     CloudFront
                         │
                  ┌──────┴──────┐
                  │             │
              Cache Hit      Cache Miss
                                │
                                ▼
                           Application
                                │
                                ▼
                              Redis
                                │
                         ┌──────┴──────┐
                         │             │
                       Hit           Miss
                         │             │
                         ▼             ▼
                      Return      PostgreSQL
```

CloudFront caches HTTP responses at the edge.

Redis typically caches application data, computed values, sessions, or other backend state.

Using both can be highly effective because they reduce different categories of work.

## CloudFront and Kafka

Kafka is an internal event-streaming system and should not be confused with CloudFront.

For example:

```text
Viewer
  │
  ▼
CloudFront
  │
  ▼
API
  │
  ▼
Kafka
  │
  ├── Order Service
  ├── Notification Service
  └── Analytics Service
```

The responsibilities are different:

```text
CloudFront
    → Internet-facing content delivery

Kafka
    → Internal asynchronous event streaming
```

CloudFront does not replace Kafka for asynchronous backend communication.

## High Availability

CloudFront provides a globally distributed edge layer, but the origin can still become a single point of failure.

For example:

```text
CloudFront
    │
    ▼
Single Region
    │
    ▼
Single Origin
```

If that origin becomes unavailable, cache misses and dynamic requests can fail.

A more resilient architecture can use multiple origin paths or regional failover strategies:

```text
                    CloudFront
                         │
                 ┌───────┴───────┐
                 ▼               ▼
             Region A         Region B
                 │               │
                 ▼               ▼
                ALB             ALB
                 │               │
                 ▼               ▼
             Application     Application
```

True multi-region resilience also requires consideration of:

- Database replication
- Data consistency
- Application state
- Secrets
- External dependencies
- DNS
- Deployment consistency

CloudFront alone does not provide complete disaster recovery.

## Disaster Recovery Considerations

For a regional origin failure, a production architecture should define:

```text
Detection
   │
   ▼
Failover Decision
   │
   ▼
Secondary Origin
   │
   ▼
Application Recovery
```

However, static and dynamic content have different recovery characteristics.

Static content stored in S3 can often be replicated or restored independently from application infrastructure.

Dynamic applications require recovery of:

- Compute
- Database
- Cache
- Secrets
- Networking
- Application configuration

CloudFront is only one component of the recovery architecture.

## Security Architecture

CloudFront can act as the first security boundary for Internet traffic.

```text
Internet
   │
   ▼
CloudFront
   │
   ├── TLS
   ├── WAF
   ├── Rate Controls
   └── Cache Controls
          │
          ▼
        Origin
```

Security considerations include:

- HTTPS enforcement
- AWS WAF
- Origin access controls
- Private content controls
- Signed URLs
- Signed cookies
- Restricted HTTP methods
- Careful cache-key design
- Origin protection

A strong design attempts to ensure that users cannot bypass CloudFront and directly access an origin when the origin is intended to be protected by the edge layer.

## Cost Considerations

CloudFront introduces CDN costs, but effective caching can reduce costs elsewhere.

A simplified cost model is:

```text
Total System Cost
=
CloudFront
+
Origin Compute
+
Origin Data Transfer
+
Database
+
Caching
+
Monitoring
```

Effective caching can reduce:

- Origin bandwidth
- Application compute
- Database queries
- Scaling requirements

Poor caching can have the opposite effect:

```text
Cache Fragmentation
       │
       ▼
Low Cache Hit Ratio
       │
       ▼
High Origin Traffic
       │
       ▼
Higher Backend Cost
```

Cost optimization should therefore consider the entire architecture rather than CloudFront charges in isolation.

## Monitoring the Global Infrastructure

CloudFront should be monitored at both the edge and origin layers.

Important signals include:

| Signal | What it indicates |
|---|---|
| Request count | Overall traffic |
| Cache hit ratio | Cache effectiveness |
| Origin request count | Backend traffic |
| 4xx errors | Client/configuration/security problems |
| 5xx errors | Origin or infrastructure failures |
| Origin latency | Backend response performance |
| Bytes downloaded | Delivery volume |
| WAF blocks | Rejected malicious or unwanted traffic |

A useful incident chain is:

```text
Cache Hit Ratio ↓
        │
        ▼
Origin Requests ↑
        │
        ▼
Application Load ↑
        │
        ▼
Database Load ↑
        │
        ▼
Latency ↑
```

Monitoring CloudFront without monitoring the origin provides only half the picture.

## Common Mistakes

### Treating CloudFront as a Single Server

CloudFront is a distributed global service.

Do not reason about it as though every request reaches one centralized server.

### Assuming Every Edge Has the Same Cached Content

Cache state is distributed.

An object may exist at one edge while another edge needs to retrieve it.

The global CDN should therefore be understood as a distributed caching system rather than one shared in-memory cache.

### Confusing CloudFront With the Origin

CloudFront is the delivery layer.

S3, ALB, EC2, Kubernetes, Django, and FastAPI remain origins or origin-side components.

### Deploying the Entire Backend Globally

CloudFront does not require the backend to exist in every geographic location.

A regional backend can serve a global user base, particularly when cacheable content is involved.

### Assuming CloudFront Makes Dynamic Requests Local

A cache miss for a dynamic API still travels to the origin.

```text
User in India
     │
     ▼
India Edge
     │
     ▼
US Origin
```

The edge does not magically relocate the application.

### Ignoring Regional Origin Failure

A globally distributed CDN does not make a single-region backend globally redundant.

### Putting Business Logic at the Edge

Edge execution is powerful but can make systems harder to reason about.

Keep core application logic in the backend unless edge execution provides a clear benefit.

## Production Pitfalls

### Poor Cache Design

A global edge network cannot compensate for a cache policy that produces almost no cache hits.

### Origin Bottlenecks

If cache misses are expensive, the origin may still become the primary bottleneck.

### Incorrect Security Assumptions

CloudFront does not automatically make private application data safe to cache.

### Excessive Edge Logic

Complex edge functions can become difficult to test, deploy, and debug.

### Direct Origin Exposure

If clients can bypass CloudFront and reach the origin directly, some edge-layer protections may be bypassed.

### Ignoring Deployment Consistency

CloudFront configuration, origin infrastructure, application versions, and static assets must remain compatible during deployments.

## Interview Traps

### Are CloudFront edge locations AWS Regions?

No. Edge locations are part of CloudFront's distributed edge network and should not be treated as equivalent to standard AWS Regions.

### Does CloudFront deploy your application globally?

No. CloudFront distributes content and processes requests at the edge. Your application origin can remain in one or more AWS Regions.

### What happens when content is not at the edge?

CloudFront can retrieve it through its distributed network from the configured origin and then serve the response to the viewer. The response may be cached according to the applicable configuration.

### What is the purpose of regional edge caches?

They provide an additional caching layer within CloudFront's global infrastructure, helping reduce repeated retrievals from origins.

### What is Origin Shield?

Origin Shield provides an additional centralized caching layer that can consolidate requests before they reach the origin.

### Does CloudFront replace an ALB?

No. CloudFront is a global edge delivery layer, while an ALB provides regional load balancing.

### Does CloudFront replace Kubernetes?

No. Kubernetes manages application workloads; CloudFront handles global HTTP delivery and edge caching.

### Does CloudFront replace Redis?

No. CloudFront caches HTTP responses at the edge, while Redis typically provides application-level caching.

### Can CloudFront front a Django application?

Yes. A common architecture is:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Gunicorn
    ↓
Django
```

### Can CloudFront front FastAPI?

Yes. A common architecture is:

```text
CloudFront
    ↓
ALB
    ↓
Uvicorn / Gunicorn
    ↓
FastAPI
```

### Does a global CloudFront distribution make the database global?

No. The database remains regional unless a separate multi-region database architecture is implemented.

## Production Best Practices

- Treat CloudFront as the global delivery layer, not as the application itself.
- Design origins independently from edge infrastructure.
- Keep static and dynamic workloads separated through cache behaviors.
- Use S3 for appropriate static/object workloads.
- Use ALB or another appropriate HTTP origin for dynamic applications.
- Keep business logic inside the backend application.
- Use edge functions only when edge execution provides a clear architectural benefit.
- Understand the distinction between edge locations, regional edge infrastructure, and origins.
- Use Origin Shield when origin-request consolidation provides measurable value.
- Protect origins from unintended direct Internet access where appropriate.
- Enforce HTTPS for production workloads.
- Associate AWS WAF where appropriate.
- Monitor cache hit ratio and origin request volume together.
- Design backend capacity for cache misses and dynamic requests.
- Plan multi-region origin architecture separately from CloudFront configuration.
- Use infrastructure as code for repeatable distribution configuration.
- Test global delivery behavior from multiple geographic locations.
- Test origin failures and recovery paths.
- Document which responsibilities belong to CloudFront, ALB, Nginx, the application, Redis, and the database.

## Key Takeaways

- **CloudFront separates global delivery from regional origins:** Viewers interact with a distributed edge network while application infrastructure can remain concentrated in one or more AWS Regions.
- **Edge locations and regional caching reduce origin pressure:** CloudFront can serve cached content close to viewers and use additional CloudFront caching layers before contacting the origin.
- **CloudFront does not relocate the backend:** Cache misses and dynamic requests still depend on the regional origin, so backend scalability and availability remain essential.
- **Each infrastructure layer has a distinct responsibility:** CloudFront handles edge delivery, ALB handles regional load balancing, Nginx handles reverse proxying, Django/FastAPI handles business logic, and Redis/PostgreSQL handle application data workloads.
- **Global CDN availability is not complete disaster recovery:** A resilient architecture still requires deliberate origin, database, application, networking, and multi-region recovery strategies.