# 02- Core CloudFront Questions

## Overview

This document covers core AWS CloudFront interview questions expected from backend engineers who understand the fundamentals and need to explain CloudFront from an engineering perspective.

The focus is on the internal request path, distributions, origins, behaviors, caching, cache keys, policies, TLS, DNS, invalidation, security, observability, and integration with backend systems such as Django, FastAPI, ALB, Nginx, S3, and AWS WAF.

A strong interview answer should connect CloudFront configuration to system behavior:

```text
Viewer
  │
  │ HTTPS
  ▼
CloudFront Edge
  │
  ├── Cache HIT ───────────────► Viewer
  │
  └── Cache MISS
          │
          ▼
        Origin
          │
          ▼
       Response
          │
          ▼
      CloudFront
          │
          ▼
        Viewer
```

The important engineering question is not simply "What is CloudFront?" but:

> What happens to a request after it reaches CloudFront, what determines whether it can be cached, and when does the origin become involved?

---

## CloudFront Architecture

### What is Amazon CloudFront?

**Answer:**

Amazon CloudFront is AWS's globally distributed content delivery network and edge service.

It receives viewer HTTP/HTTPS requests at CloudFront edge locations and can either:

- Serve a response from cache.
- Forward the request to an origin.
- Apply configured request-processing and security controls.
- Return the origin response to the viewer.
- Cache the response when the request and response are eligible.

CloudFront can front:

- S3 buckets.
- Application Load Balancers.
- EC2 applications.
- API endpoints.
- Nginx servers.
- Django applications.
- FastAPI applications.
- Other HTTP origins.

A production backend architecture might look like:

```text
                         ┌───────────────┐
                         │   Route 53    │
                         └───────┬───────┘
                                 │
                                 ▼
Users ─────────────────────► CloudFront
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
                 S3 Origin    ALB Origin   API Origin
                                  │
                                  ▼
                               Nginx
                                  │
                                  ▼
                         Django / FastAPI
                                  │
                         ┌────────┴────────┐
                         ▼                 ▼
                       Redis          PostgreSQL
```

---

### Why would you put CloudFront in front of a backend application?

**Answer:**

CloudFront can provide an edge delivery layer between clients and the backend.

The major benefits are:

- Reduced latency for cacheable content.
- Reduced origin traffic.
- Global content distribution.
- TLS termination.
- Integration with AWS WAF.
- Controlled access to private content.
- Centralized edge routing and caching behavior.

However, CloudFront does not automatically improve every request.

If an API request must always execute application logic:

```text
User
  ↓
CloudFront
  ↓
ALB
  ↓
Django
  ↓
PostgreSQL
```

CloudFront still introduces an additional network layer but cannot eliminate backend processing time.

---

### What is an edge location?

**Answer:**

An edge location is a CloudFront point of presence where CloudFront receives viewer requests and can serve cached content.

The purpose is to move content delivery closer to users.

For example:

```text
User in India
      │
      ▼
Nearby CloudFront Edge
      │
      ├── Cache HIT → User
      │
      └── Cache MISS → Origin
```

The edge location is not the source of truth for the application. The origin remains the authoritative source when CloudFront needs to retrieve content.

---

### What is an origin?

**Answer:**

An origin is the backend source from which CloudFront retrieves content.

Common origins include:

| Origin | Typical use |
|---|---|
| S3 | Static files, media, downloads |
| ALB | Web applications and APIs |
| EC2 | Custom applications |
| API endpoint | API delivery |
| Nginx | HTTP application gateway |
| External HTTP server | Non-AWS backend |

For example:

```text
CloudFront
    │
    ▼
ALB
    │
    ▼
Django / FastAPI
```

---

### What is a CloudFront distribution?

**Answer:**

A CloudFront distribution is the primary configuration object that defines how CloudFront handles viewer requests and communicates with origins.

A distribution can define:

- Origins.
- Default cache behavior.
- Additional cache behaviors.
- Cache policies.
- Origin request policies.
- Viewer protocol policy.
- TLS configuration.
- WAF association.
- Logging.
- Geographic restrictions.
- Error responses.
- Access controls.

Conceptually:

```text
Distribution
│
├── Origins
│
├── Default Behavior
│
├── Additional Behaviors
│
├── Cache Policies
│
├── Origin Request Policies
│
├── TLS
│
├── WAF
│
└── Logging
```

---

## Request Lifecycle

### Explain the CloudFront request lifecycle.

**Answer:**

A simplified lifecycle is:

1. The client resolves the application domain through DNS.
2. The client connects to a CloudFront edge location.
3. CloudFront evaluates the request and selects the appropriate behavior.
4. CloudFront determines the applicable cache key and checks its cache.
5. If the response is available and valid, CloudFront serves it.
6. If the request requires origin access, CloudFront forwards it to the selected origin.
7. The origin returns a response.
8. CloudFront returns the response to the viewer.
9. If applicable, CloudFront stores the response in cache.

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant O as Origin

    C->>CF: HTTPS Request
    CF->>CF: Select behavior
    CF->>CF: Evaluate cache key
    CF->>CF: Check cache

    alt Cache Hit
        CF-->>C: Cached Response
    else Cache Miss
        CF->>O: Origin Request
        O-->>CF: Origin Response
        CF->>CF: Cache if eligible
        CF-->>C: Response
    end
```

---

### What determines whether CloudFront serves a cached response?

**Answer:**

CloudFront considers the applicable cache behavior and caching configuration.

Important factors include:

- Cache key.
- HTTP method.
- Cache policy.
- TTL configuration.
- Request attributes included in the cache key.
- Response caching directives.
- Whether the object is currently available and valid in cache.
- Whether the request is explicitly configured to bypass caching.

The key distinction is:

```text
Same cache key
      +
Cacheable response
      +
Fresh cache entry
      ↓
Potential cache hit
```

---

### Does every request go to the origin?

**Answer:**

No.

A cache hit can be served directly from the CloudFront edge.

```text
Cache HIT:

Client → CloudFront → Client
```

A cache miss or non-cacheable request may require origin communication:

```text
Cache MISS:

Client → CloudFront → Origin
                    ↓
                 Response
                    ↓
                CloudFront
                    ↓
                  Client
```

---

## Caching

### What is a cache hit?

**Answer:**

A cache hit occurs when CloudFront can satisfy a request using a valid cached object associated with the applicable cache key.

Benefits include:

- Lower origin traffic.
- Lower application load.
- Lower latency for cacheable content.
- Better scalability.
- Potentially lower infrastructure cost.

---

### What is a cache miss?

**Answer:**

A cache miss occurs when CloudFront does not have a usable cached response for the request.

CloudFront then needs to obtain the required content from the origin, subject to the configured request and caching behavior.

A cache miss is not necessarily an error.

It simply means:

> The edge could not satisfy the request from its cache.

---

### What is a cache key?

**Answer:**

The cache key determines which viewer requests are treated as equivalent for caching.

Depending on configuration, request characteristics such as the following can affect caching:

- URL path.
- Query strings.
- Headers.
- Cookies.

For example:

```text
/products?id=100
/products?id=200
```

may represent different cache entries if the relevant query string is included in the cache key.

The cache key should contain only information that changes the representation being returned.

---

### Why is cache-key design important?

**Answer:**

Because an unnecessarily large cache key can fragment the cache.

Suppose an API response does not depend on:

```text
X-Request-ID
```

but the header is included in the cache key.

Then:

```text
Request A → X-Request-ID=abc
Request B → X-Request-ID=xyz
Request C → X-Request-ID=pqr
```

can produce separate cache entries for logically identical responses.

This leads to:

```text
More cache variants
      ↓
Lower cache hit ratio
      ↓
More origin requests
      ↓
Higher origin load
```

A senior-level answer should connect cache-key design directly to origin scalability.

---

### What is TTL?

**Answer:**

TTL, or Time To Live, determines how long a cached object can remain fresh under the applicable CloudFront caching configuration.

CloudFront caching configuration commonly involves:

- Minimum TTL.
- Default TTL.
- Maximum TTL.

The effective behavior also depends on the cache policy and origin response cache-control metadata.

Typical strategies are:

| Content | Typical caching strategy |
|---|---|
| Content-hashed JS/CSS | Long TTL |
| Versioned images | Long TTL |
| Public API response | Carefully controlled TTL |
| Frequently changing content | Shorter TTL |
| Personalized response | Usually no shared caching |

---

### Why can a high cache hit ratio be dangerous?

**Answer:**

Because caching the wrong response can create a correctness or security problem.

For example:

```text
GET /api/account
```

may return:

```json
{
  "user_id": 1001,
  "balance": 5000
}
```

If this response is incorrectly shared through a cache key that does not distinguish users, another user could receive the wrong response.

Therefore:

> Cacheability must be based on response semantics, not simply on whether caching improves performance.

---

### Should APIs be cached?

**Answer:**

Some APIs can be cached, but not all APIs should be.

Good candidates can include:

- Public catalog data.
- Public documentation.
- Public configuration.
- Public product information.
- Read-heavy data with controlled freshness.

Riskier candidates include:

- User profiles.
- Account information.
- Authorization-dependent responses.
- Payment information.
- Frequently changing state.

Before caching an API response, determine:

1. Whether multiple users can safely share the response.
2. What request attributes affect the representation.
3. How stale the data can safely be.
4. What happens when data changes.
5. Whether authorization information must influence the result.

---

## Cache Policies and Request Policies

### What is a CloudFront cache policy?

**Answer:**

A cache policy defines caching behavior and cache-key configuration.

It determines important aspects such as:

- TTL values.
- Which query strings participate in the cache key.
- Which headers participate in the cache key.
- Which cookies participate in the cache key.

The central question is:

> Which request attributes determine whether two requests should receive the same cached response?

---

### What is an origin request policy?

**Answer:**

An origin request policy controls additional request information that CloudFront forwards to the origin.

It is important to distinguish it from the cache policy.

```text
Cache Policy
    │
    └── What makes two requests different for caching?

Origin Request Policy
    │
    └── What additional request data should the origin receive?
```

A request attribute can be needed by the origin without necessarily needing to create a separate cache entry.

---

### Why should we avoid forwarding every cookie and header?

**Answer:**

Because unnecessary request variation can:

- Reduce cache efficiency.
- Increase origin traffic.
- Increase application load.
- Complicate debugging.
- Create accidental caching behavior.

For example:

```text
Cookie: session_id=...
```

is usually highly user-specific.

Blindly including session cookies in shared cache behavior can destroy cache efficiency and may introduce serious security risks if caching is incorrectly configured.

---

## CloudFront Behaviors

### What is a cache behavior?

**Answer:**

A cache behavior defines how CloudFront handles requests matching a path pattern.

For example:

```text
/static/* → S3
/media/*  → S3
/api/*    → ALB
```

A behavior can specify:

- Origin.
- Cache policy.
- Origin request policy.
- Allowed methods.
- Viewer protocol policy.
- Security-related settings.
- Other request-processing configuration.

---

### Why use multiple cache behaviors?

**Answer:**

Because different parts of an application have different caching requirements.

For example:

```text
/static/*
    │
    ├── S3
    ├── Long TTL
    └── GET/HEAD

/api/*
    │
    ├── ALB
    ├── API-specific policy
    └── Dynamic behavior
```

This prevents static content and dynamic application traffic from being forced into the same caching strategy.

---

### What is the default cache behavior?

**Answer:**

The default behavior handles requests that do not match a more specific path pattern.

This makes the default behavior particularly important.

A common production approach is:

```text
Specific behaviors
    ↓
Highly intentional rules

Default behavior
    ↓
Safe fallback
```

Do not assume that every request will match a custom behavior.

---

## Origins and Routing

### Can one CloudFront distribution have multiple origins?

**Answer:**

Yes.

For example:

```text
CloudFront
│
├── /static/* → S3
├── /media/*  → S3
└── /api/*    → ALB
```

This allows one public domain to front multiple backend systems.

---

### How does CloudFront decide which origin to use?

**Answer:**

CloudFront first determines which cache behavior applies to the request.

That behavior specifies the target origin.

Conceptually:

```text
Request
   │
   ▼
Path Matching
   │
   ├── /static/* → S3
   ├── /media/*  → S3
   └── /api/*    → ALB
```

Therefore, path-pattern design is an important part of CloudFront architecture.

---

### Can CloudFront sit in front of an ALB?

**Answer:**

Yes.

This is a common production architecture:

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

CloudFront handles edge delivery and caching, while the ALB handles application traffic distribution among backend targets.

---

### Is CloudFront a replacement for an ALB?

**Answer:**

No.

They solve different problems.

| CloudFront | ALB |
|---|---|
| CDN and edge delivery | Load balancing |
| Global edge presence | Regional load balancing |
| Caching | Routes to targets |
| Edge request processing | Target health and distribution |
| Viewer TLS | Backend traffic distribution |
| Can reduce origin traffic | Connects clients to application targets |

They are commonly deployed together.

---

## CloudFront and S3

### Why is CloudFront commonly used with S3?

**Answer:**

S3 is an excellent origin for static objects, while CloudFront provides global edge delivery.

Typical architecture:

```text
Browser
   │
   ▼
CloudFront
   │
   ▼
S3
```

This is useful for:

- Frontend bundles.
- Images.
- Videos.
- Downloads.
- Static documentation.
- Media files.

---

### Should an S3 bucket behind CloudFront be publicly accessible?

**Answer:**

Not necessarily.

For private content, the preferred architecture is to restrict direct S3 access and allow CloudFront to retrieve objects through an appropriate origin access mechanism.

The goal is:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Private S3
```

rather than:

```text
Internet
   ├──► CloudFront
   └──► Public S3
```

This ensures CloudFront remains the intended delivery path.

---

## HTTPS and TLS

### Can CloudFront terminate HTTPS?

**Answer:**

Yes.

The viewer can establish an HTTPS connection with CloudFront.

```text
Browser
   │
   │ HTTPS
   ▼
CloudFront
```

CloudFront uses a TLS certificate associated with the distribution and requested hostname.

---

### Is viewer-to-CloudFront HTTPS the same as CloudFront-to-origin HTTPS?

**Answer:**

No.

They are separate connections.

```text
Browser
   │
   │ HTTPS
   ▼
CloudFront
   │
   │ HTTPS
   ▼
Origin
```

is different from:

```text
Browser
   │
   │ HTTPS
   ▼
CloudFront
   │
   │ HTTP
   ▼
Origin
```

For sensitive production systems, encrypting traffic on both legs is generally preferable.

---

### What can cause a CloudFront certificate error?

**Answer:**

Common causes include:

- Certificate does not cover the requested hostname.
- Incorrect certificate associated with the distribution.
- Incorrect alternate domain configuration.
- DNS points to an unexpected endpoint.
- TLS configuration mismatch.

A useful troubleshooting chain is:

```text
DNS
 ↓
CloudFront hostname
 ↓
Alternate domain name
 ↓
Certificate
 ↓
TLS handshake
```

---

## DNS

### What is the relationship between Route 53 and CloudFront?

**Answer:**

Route 53 provides DNS functionality, while CloudFront provides CDN and edge delivery.

They can be combined:

```text
Client
  │
  ▼
Route 53
  │
  ▼
CloudFront
  │
  ▼
Origin
```

Route 53 answers:

> Where should this hostname resolve?

CloudFront answers:

> How should HTTP/HTTPS traffic be delivered at the edge?

---

### Can CloudFront use a custom domain?

**Answer:**

Yes.

A CloudFront distribution can be associated with an alternate domain name, and DNS can point the application hostname to the distribution.

For example:

```text
api.example.com
      │
      ▼
CloudFront
      │
      ▼
ALB
```

The TLS certificate must also cover the hostname.

---

## Invalidation

### What is CloudFront invalidation?

**Answer:**

An invalidation requests removal of specified objects from CloudFront caches before their normal expiration.

For example:

```text
/static/app.js
```

or a broader path:

```text
/static/*
```

can be invalidated.

---

### When should you use invalidation?

**Answer:**

Invalidation is useful when cached content must be removed before normal expiration.

Examples include:

- Emergency correction.
- Incorrectly cached object.
- Emergency security-related removal.
- Deployment involving mutable object names.

However, frequent broad invalidation is usually a sign that the asset versioning strategy needs improvement.

---

### What is a better strategy for static assets?

**Answer:**

Use immutable, versioned, or content-hashed filenames.

Instead of:

```text
app.js
```

use:

```text
app.83f4d9.js
```

When the content changes, the filename changes.

The deployment becomes:

```text
Old:
app.83f4d9.js

New:
app.12a7c3.js
```

The new URL naturally maps to a different cache key.

This supports long TTLs and reduces the need for broad invalidations.

---

## Security

### How does AWS WAF work with CloudFront?

**Answer:**

AWS WAF can be associated with CloudFront to inspect viewer requests and apply web security rules.

A simplified architecture is:

```text
User
  │
  ▼
CloudFront
  │
  ▼
AWS WAF
  │
  ▼
Origin
```

WAF can help enforce rules involving:

- IP addresses.
- Request patterns.
- Rate-based controls.
- Managed rule groups.
- Application-specific security requirements.

---

### Does CloudFront replace application authentication?

**Answer:**

No.

CloudFront can provide edge-level access controls, but application authentication and authorization remain application concerns in many architectures.

For example:

```text
CloudFront
    │
    ├── WAF
    │
    ▼
Django / FastAPI
    │
    └── Application Authorization
```

The backend should still validate whether the authenticated user is allowed to perform the requested operation.

---

### What are signed URLs?

**Answer:**

Signed URLs provide controlled access to protected CloudFront resources using a cryptographic signature.

They are useful when access needs to be granted to a specific resource for a controlled period.

Typical use cases include:

- Private downloads.
- Paid content.
- Temporary media access.

---

### What are signed cookies?

**Answer:**

Signed cookies allow access control across multiple protected CloudFront objects.

They are useful when a client needs access to a collection of resources rather than one specific object.

For example:

```text
Authenticated User
       │
       ▼
Backend
       │
       ▼
Signed CloudFront Cookies
       │
       ▼
Multiple protected resources
```

---

## CloudFront and Backend Applications

### How would you use CloudFront with Django?

**Answer:**

A typical architecture is:

```text
                     Internet
                         │
                         ▼
                    CloudFront
                         │
              ┌──────────┴──────────┐
              │                     │
         /static/*              /api/*
              │                     │
              ▼                     ▼
             S3                    ALB
                                    │
                                  Nginx
                                    │
                                  Django
                                    │
                           ┌────────┴────────┐
                           ▼                 ▼
                         Redis          PostgreSQL
```

Static content benefits heavily from caching.

API behavior should be configured independently because many API responses are dynamic or user-specific.

---

### How would you use CloudFront with FastAPI?

**Answer:**

A typical architecture is:

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
Nginx
  │
  ▼
Uvicorn / FastAPI
  │
  ├── Redis
  └── PostgreSQL
```

CloudFront provides the edge layer, while FastAPI remains responsible for application processing.

---

### Should CloudFront cache authentication-dependent API responses?

**Answer:**

Not by default.

Authentication-dependent responses require careful analysis of whether the response can safely be shared.

For example:

```text
GET /api/me
```

usually returns user-specific data.

Blindly caching it can create a data-isolation vulnerability.

The cache strategy must account for:

- Authentication context.
- Authorization.
- Cache-key design.
- Response semantics.
- Data freshness.
- Whether responses are shareable.

---

## HTTP Methods

### Which HTTP methods are typically cacheable?

**Answer:**

CloudFront caching is primarily associated with safe, read-oriented methods such as:

```text
GET
HEAD
```

Other methods such as:

```text
POST
PUT
PATCH
DELETE
```

are generally handled as origin requests rather than normal shared cached objects.

For APIs, this aligns naturally with common REST semantics:

```text
GET    → potentially cacheable
POST   → state change
PUT    → state change
PATCH  → state change
DELETE → state change
```

Caching should still be explicitly designed rather than assumed.

---

### Why should POST requests normally not be cached?

**Answer:**

POST commonly represents an operation that changes application state or depends on request-specific data.

For example:

```http
POST /payments
```

should not return a shared cached response to unrelated users.

This is one reason CDN caching strategies need to respect HTTP semantics and application behavior.

---

## Monitoring and Troubleshooting

### How do you monitor CloudFront in production?

**Answer:**

Use multiple telemetry sources:

- CloudFront metrics.
- CloudWatch.
- Standard access logs.
- Real-time logs where needed.
- AWS WAF telemetry.
- ALB metrics.
- Application logs.
- Database and cache metrics.

The objective is to correlate edge behavior with origin behavior.

```text
CloudFront Metrics
       │
       ▼
CloudFront Logs
       │
       ▼
ALB Metrics
       │
       ▼
Application Logs
       │
       ├── Redis
       └── PostgreSQL
```

---

### How would you investigate a CloudFront 403?

**Answer:**

Do not immediately assume that CloudFront generated the 403.

Check:

1. AWS WAF rules.
2. CloudFront behavior.
3. Allowed HTTP methods.
4. Signed URL or signed cookie requirements.
5. Geographic restrictions.
6. S3 origin access configuration.
7. Origin response.
8. CloudFront logs.
9. Origin logs.

The key diagnostic question is:

> Did the edge reject the request, or did the origin return the 403?

---

### How would you investigate a CloudFront 502?

**Answer:**

A 502 can indicate an origin communication or origin response problem.

Investigate:

```text
CloudFront
   ↓
Origin connection
   ↓
ALB / Nginx
   ↓
Application
```

Check:

- Origin availability.
- TLS configuration.
- DNS and networking.
- ALB health.
- Application health.
- Origin response validity.
- Recent infrastructure changes.

---

### How would you investigate a CloudFront 504?

**Answer:**

A 504 should lead you toward latency and origin responsiveness.

Investigate:

```text
CloudFront
    ↓
Origin
    ↓
ALB
    ↓
Nginx
    ↓
Django/FastAPI
    ↓
Redis/PostgreSQL/External APIs
```

Look for:

- Slow application code.
- Database queries.
- Lock contention.
- External API latency.
- Origin overload.
- Network problems.
- Dependency failures.

---

## Performance

### How does CloudFront improve application scalability?

**Answer:**

CloudFront can absorb repeated requests for cacheable content at the edge.

Without effective caching:

```text
100,000 requests
       │
       ▼
Application
```

With effective caching:

```text
100,000 viewer requests
       │
       ▼
CloudFront
       │
       ├── Most requests → Cache
       │
       └── Small portion → Origin
```

This reduces the number of requests reaching:

- ALB.
- Nginx.
- Django/FastAPI.
- Redis.
- PostgreSQL.

The scalability benefit is therefore often indirect but significant.

---

### What causes poor CloudFront cache performance?

**Answer:**

Common causes include:

- Overly short TTLs.
- Excessive query-string variation.
- Excessive cookie variation.
- Unnecessary header variation.
- Dynamic content being treated as cacheable.
- Incorrect cache policies.
- Poor URL design.
- Frequent invalidations.

A useful diagnostic chain is:

```text
Low Cache Hit Ratio
       ↓
Inspect Cache Key
       ↓
Inspect Request Variations
       ↓
Inspect TTL
       ↓
Inspect Cache Policy
       ↓
Inspect Application Semantics
```

---

## Production Design Questions

### How would you design CloudFront for a high-traffic API?

**Answer:**

Start by separating traffic according to caching and operational requirements.

For example:

```text
                    CloudFront
                        │
            ┌───────────┴───────────┐
            │                       │
        /static/*                /api/*
            │                       │
            ▼                       ▼
           S3                      ALB
                                    │
                              Application Tier
                                    │
                           ┌────────┴────────┐
                           ▼                 ▼
                         Redis          PostgreSQL
```

Then:

- Use long TTLs for immutable assets.
- Carefully design API cache policies.
- Avoid caching personalized responses.
- Use WAF for edge protection.
- Monitor cache efficiency.
- Monitor origin latency.
- Use appropriate autoscaling behind the ALB.
- Maintain observability across the entire request path.

---

### How would you design CloudFront for a global static website?

**Answer:**

A simple architecture is:

```text
Users
  │
  ▼
Route 53
  │
  ▼
CloudFront
  │
  ▼
S3
```

Use:

- HTTPS.
- Private S3 access through CloudFront.
- Long TTLs for immutable assets.
- Versioned filenames.
- Appropriate error handling.
- Monitoring and logging.
- WAF where the application's threat model requires it.

---

### How would you design CloudFront for both static and dynamic traffic?

**Answer:**

Separate traffic using cache behaviors.

```text
CloudFront
│
├── /static/* ──► S3
│                  │
│                  └── Long TTL
│
├── /media/* ───► S3
│                  │
│                  └── Controlled caching
│
└── /api/* ─────► ALB
                   │
                   ▼
                Backend
```

This allows each workload to have an independent caching strategy.

---

## Common Interview Traps

### Is CloudFront a load balancer?

**Answer:**

No.

CloudFront is primarily a CDN and edge delivery service.

An ALB is a regional application load balancer.

They can complement each other:

```text
CloudFront
    ↓
ALB
    ↓
Application Targets
```

---

### Is CloudFront only for static content?

**Answer:**

No.

CloudFront can deliver both static and dynamic HTTP/HTTPS content.

The difference is that dynamic requests may still need to reach the origin.

---

### Does CloudFront automatically cache everything?

**Answer:**

No.

Caching depends on the request, behavior, cache policy, HTTP semantics, TTL, cache key, and response characteristics.

---

### Does CloudFront replace S3?

**Answer:**

No.

S3 stores objects.

CloudFront distributes content at the edge.

A common relationship is:

```text
CloudFront → S3
```

where S3 is the origin.

---

### Does CloudFront replace Route 53?

**Answer:**

No.

Route 53 provides DNS capabilities.

CloudFront provides content delivery and edge processing.

They commonly work together.

---

### Does CloudFront replace WAF?

**Answer:**

No.

CloudFront is the edge delivery layer.

AWS WAF provides web request inspection and filtering.

They can be integrated:

```text
Viewer
  ↓
CloudFront
  ↓
AWS WAF
  ↓
Origin
```

---

### Does a CloudFront cache hit mean the origin is healthy?

**Answer:**

No.

A cache hit can continue serving content even when the origin is currently unavailable.

This is one reason cache state and origin health must be monitored separately.

---

### Can CloudFront hide an origin completely?

**Answer:**

It can be part of an architecture designed so that viewers access the application through CloudFront rather than directly accessing the origin.

However, origin protection requires proper configuration.

For example, an application should not rely solely on the assumption that users cannot discover an origin hostname.

Use appropriate:

- Security groups.
- Origin access controls.
- WAF.
- Authentication.
- Network controls.
- Application-level authorization.

---

## Quick Comparison

| Component | Primary responsibility |
|---|---|
| CloudFront | CDN and edge delivery |
| Route 53 | DNS |
| S3 | Object storage |
| ALB | Regional application load balancing |
| AWS WAF | Web request filtering |
| Nginx | HTTP reverse proxy |
| Django | Backend application framework |
| FastAPI | API/application framework |
| Redis | In-memory data store/cache |
| PostgreSQL | Relational database |

---

## Interview Answer Framework

When asked an unfamiliar CloudFront question, structure the answer around the request lifecycle:

```text
Viewer
  ↓
DNS
  ↓
CloudFront Edge
  ↓
Behavior
  ↓
Cache Key / Cache Policy
  ↓
Cache HIT?
  ├── Yes → Response
  │
  └── No
       ↓
     Origin
       ↓
     Response
       ↓
     Cache if eligible
       ↓
     Viewer
```

Then discuss the relevant operational dimension:

| Question type | Focus |
|---|---|
| Performance | Cache hit ratio, TTL, cache key |
| Security | WAF, HTTPS, private origins, authorization |
| Scalability | Origin load reduction |
| Availability | Edge delivery, origin resilience |
| Troubleshooting | Logs, metrics, request path |
| API design | Cacheability and personalization |
| Static content | S3, immutable assets, long TTL |
| Routing | Behaviors and origins |
| TLS | Viewer and origin connections |
| Cost | Origin traffic, transfer, logging, invalidations |

The strongest answers connect **CloudFront configuration → request behavior → system impact** rather than stopping at service definitions.

## Key Takeaways

- **CloudFront is an edge delivery layer whose behavior is determined by distributions, behaviors, origins, cache policies, and request policies.**
- **Cache-key design is one of the most important CloudFront engineering decisions because it directly affects correctness, cache efficiency, and origin load.**
- **CloudFront, ALB, Route 53, S3, WAF, and application frameworks solve different problems and are commonly combined rather than treated as replacements for one another.**
- **Production troubleshooting should trace the complete request path from DNS and CloudFront through the selected origin and backend dependencies.**
- **A senior-level CloudFront answer connects configuration choices to latency, scalability, security, reliability, and operational consequences.**