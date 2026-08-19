# 03- Distributions and Cache Behaviors

## Overview

A CloudFront distribution is the configuration boundary that defines how CloudFront receives viewer requests, selects an origin, determines caching behavior, applies security controls, and returns responses.

Cache behaviors provide path-based rules inside a distribution. They allow different classes of traffic to use different origins, cache policies, HTTP methods, TTLs, request forwarding rules, and edge processing.

A production CloudFront architecture commonly looks like:

```text
                         Internet
                            │
                            ▼
                    CloudFront Distribution
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
        /static/*       /images/*       /api/*
              │             │             │
              ▼             ▼             ▼
             S3            S3            ALB
                                          │
                                          ▼
                                   Django / FastAPI
```

The important architectural distinction is:

```text
Distribution
    └── defines the global delivery configuration

Cache Behavior
    └── defines how a matching class of requests is handled
```

Understanding this distinction is essential for designing predictable cache policies and preventing accidental caching, origin overload, security vulnerabilities, and unnecessary latency.

## CloudFront Distribution

A CloudFront distribution represents a complete CloudFront delivery configuration.

It defines how CloudFront should process requests for one or more domain names.

A distribution can contain:

- One or more origins
- A default cache behavior
- Additional cache behaviors
- Viewer protocol policies
- Allowed HTTP methods
- Cache policies
- Origin request policies
- Response headers policies
- TLS configuration
- Compression settings
- WAF association
- Logging configuration
- Custom error responses
- Geographic restrictions
- Edge processing configuration

Conceptually:

```text
CloudFront Distribution
│
├── Domain / Alternate Domain Names
│
├── TLS Certificate
│
├── Origins
│   ├── S3
│   └── ALB
│
├── Default Cache Behavior
│
├── Ordered Cache Behaviors
│   ├── /static/*
│   ├── /images/*
│   └── /api/*
│
├── Security
│   └── AWS WAF
│
└── Edge Processing
    ├── CloudFront Functions
    └── Lambda@Edge
```

The distribution is therefore the top-level object through which CloudFront's global infrastructure is configured for an application.

## Why Distributions Exist

Without a distribution-level configuration, CloudFront would have no rules describing:

- Which origin should receive a request.
- Which content can be cached.
- Which HTTP methods are permitted.
- Which request components affect caching.
- Which protocol viewers must use.
- Which security controls apply.

The distribution provides a consistent global policy.

Instead of configuring individual edge locations manually:

```text
Edge A → Configuration
Edge B → Configuration
Edge C → Configuration
...
```

you configure the distribution:

```text
CloudFront Distribution
        │
        ▼
Globally propagated configuration
```

AWS manages the distribution of the configuration across CloudFront's infrastructure.

## Origins

An origin is the source from which CloudFront retrieves content when it cannot satisfy a request from its cache.

Typical origins include:

| Origin | Typical workload |
|---|---|
| S3 | Static assets and object storage |
| ALB | Dynamic applications |
| API Gateway | API workloads |
| EC2 / HTTP server | Custom applications |
| Kubernetes ingress/load balancer | Containerized applications |
| Custom HTTP endpoint | External or specialized origin |

A single distribution can have multiple origins.

For example:

```text
CloudFront Distribution
│
├── S3 Origin
│   └── Static assets
│
└── ALB Origin
    └── Application APIs
```

This is one of the primary reasons cache behaviors exist.

## Multiple Origins

Consider a web application with:

```text
/static/app.js
/images/logo.png
/api/users
/api/orders
```

A sensible architecture might be:

```text
                    CloudFront
                        │
          ┌─────────────┴─────────────┐
          │                           │
       Static                       API
          │                           │
          ▼                           ▼
         S3                           ALB
                                      │
                                      ▼
                                Django / FastAPI
```

The CloudFront distribution can route these requests differently using cache behaviors.

## Default Cache Behavior

Every CloudFront distribution has a default cache behavior.

The default behavior acts as the fallback rule for requests that do not match a more specific cache behavior.

For example:

```text
Request                         Matching behavior

/static/app.js                  /static/*
/images/logo.png                /images/*
/api/users                      /api/*
/health                         Default behavior
```

The default behavior should be designed deliberately because unmatched requests will use it.

A common production pattern is:

```text
Default
    → dynamic application

/static/*
    → S3

/images/*
    → S3

/api/*
    → application origin
```

This ensures that unexpected paths do not accidentally inherit a static-content caching policy.

## Cache Behaviors

A cache behavior defines how CloudFront handles requests matching a specific path pattern.

For example:

```text
/static/*
```

can have a different configuration from:

```text
/api/*
```

A cache behavior can control:

- Origin
- Cache policy
- Origin request policy
- Allowed methods
- Viewer protocol policy
- Compression
- Response headers
- Edge functions
- TTL behavior

Conceptually:

```text
Request
   │
   ▼
Path Matching
   │
   ├── /static/* → Static Cache Behavior
   │
   ├── /images/* → Image Cache Behavior
   │
   ├── /api/*    → API Cache Behavior
   │
   └── default   → Default Cache Behavior
```

## Why Cache Behaviors Matter

Different resources have fundamentally different caching requirements.

For example:

```text
JavaScript bundle
    → Highly cacheable

Product image
    → Highly cacheable

Public product API
    → Potentially cacheable

Authenticated user profile
    → Usually user-specific

POST /orders
    → Not a normal cacheable content request
```

Trying to use one cache policy for every request usually creates either:

- Poor cache performance, or
- Incorrect caching.

Cache behaviors allow the architecture to express these differences explicitly.

## Path Pattern Matching

A cache behavior is selected based on the request path.

Examples:

```text
/static/*
/images/*
/api/*
```

A simplified routing model is:

```mermaid
flowchart TD
    A[Viewer Request] --> B{Path Pattern Match}

    B -->|/static/*| C[Static Behavior]
    B -->|/images/*| D[Image Behavior]
    B -->|/api/*| E[API Behavior]
    B -->|No Match| F[Default Behavior]

    C --> G[S3 Origin]
    D --> G
    E --> H[Application Origin]
    F --> H
```

The path pattern controls which behavior is selected, but it does not by itself determine whether the response will be cached.

Caching depends on the behavior's cache configuration and the request/response characteristics.

## Ordered Cache Behaviors

When multiple path patterns could potentially match a request, CloudFront evaluates cache behaviors according to their configured ordering.

Specific patterns should be placed before broader patterns.

For example:

```text
/api/private/*
/api/*
```

A request for:

```text
/api/private/profile
```

should match the more specific private behavior rather than the generic API behavior.

A useful design principle is:

```text
Specific rule
    ↓
Generic rule
    ↓
Default rule
```

This prevents broad rules from unintentionally capturing traffic that requires special handling.

## Cache Behavior Design Example

Consider:

```text
example.com/
│
├── /static/*
├── /images/*
├── /api/public/*
├── /api/private/*
└── /*
```

A production-oriented design could be:

| Path | Origin | Caching |
|---|---|---|
| `/static/*` | S3 | Long TTL |
| `/images/*` | S3 | Long TTL |
| `/api/public/*` | ALB | Controlled caching |
| `/api/private/*` | ALB | Disabled or highly restricted |
| `/*` | ALB | Application-specific |

This keeps caching decisions aligned with workload characteristics.

## Cache Policy

A cache policy defines how CloudFront determines whether two requests can share the same cached response.

This is one of the most important concepts in CloudFront.

A simplified cache key can be thought of as:

```text
Cache Key =
    HTTP Method
    + Host
    + Path
    + Selected Query Parameters
    + Selected Headers
    + Selected Cookies
```

The exact cache key is determined by the CloudFront configuration.

For example:

```text
GET /products/42?currency=USD
```

might produce a different cache key from:

```text
GET /products/42?currency=INR
```

if `currency` is included in the cache key.

## Why Cache Keys Matter

The cache key determines cache sharing.

Consider:

```text
GET /products/42?currency=USD
GET /products/42?currency=INR
```

If currency affects the response but is excluded from the cache key, CloudFront could treat the requests as equivalent.

That can result in incorrect responses.

If too many request attributes are included:

```text
User-Agent
Cookie
Authorization
Tracking IDs
Random query parameters
```

the cache can become highly fragmented.

The result is:

```text
More unique cache keys
        ↓
Fewer cache hits
        ↓
More origin requests
        ↓
Higher cost and latency
```

Cache-key design is therefore both a correctness and performance concern.

## Cache Policy vs Origin Request Policy

These policies serve different purposes.

| Policy | Purpose |
|---|---|
| Cache policy | Determines what contributes to the cache key and TTL settings |
| Origin request policy | Determines what CloudFront sends to the origin |

A value may need to reach the origin without being part of the cache key.

For example:

```text
Request
  │
  ├── Cache key inputs
  │
  └── Origin request inputs
```

This distinction prevents a common mistake: forwarding every request attribute to the origin and accidentally fragmenting the cache.

## Cache Policy Example

Suppose:

```text
GET /products/42?currency=USD
```

and the response depends on `currency`.

A cache policy might include:

```text
Query string:
    currency
```

but exclude unrelated parameters such as:

```text
utm_source
utm_campaign
tracking_id
```

This allows:

```text
/products/42?currency=USD&utm_source=google
/products/42?currency=USD&utm_source=email
```

to potentially share the same cache object if the tracking parameters do not affect the response.

## TTL Configuration

TTL determines how long CloudFront can retain an object before it needs to revalidate or retrieve a newer version according to the configured caching model.

Important concepts include:

- Minimum TTL
- Default TTL
- Maximum TTL
- Origin cache-control headers

For static assets, long TTLs are common.

For dynamic APIs, TTLs are usually shorter or caching may be disabled.

Example:

| Workload | Typical strategy |
|---|---|
| Hashed JS/CSS | Long TTL |
| Images | Long or moderate TTL |
| Public API | Short/moderate TTL |
| Personalized API | Usually no shared caching |
| Sensitive data | Avoid shared caching |

TTL values should follow application consistency requirements rather than arbitrary numbers.

## Cache-Control Headers

The origin can communicate caching requirements through HTTP response headers.

For example:

```http
Cache-Control: public, max-age=3600
```

For immutable assets:

```http
Cache-Control: public, max-age=31536000, immutable
```

For sensitive or non-cacheable content:

```http
Cache-Control: private, no-store
```

The final caching behavior depends on the CloudFront cache policy and the origin response headers.

Backend engineers should therefore treat cache headers as part of the API and application contract.

## Static Asset Strategy

Static assets are often the easiest CloudFront workload to cache.

A strong production pattern is content-addressed filenames:

```text
app.91c3e7.js
styles.44a9b1.css
logo.82d31f.svg
```

The deployment process generates a new filename when content changes.

Then CloudFront can safely cache aggressively:

```text
Cache-Control:
    public
    max-age=31536000
    immutable
```

The architecture becomes:

```text
Browser
   │
   ▼
CloudFront
   │
   ▼
S3
```

Because changed content gets a new URL, long TTLs do not prevent users from receiving updated assets.

## Dynamic API Caching

API caching requires much more careful design.

Consider:

```http
GET /api/products/42
```

If the response is identical for all users, CloudFront may be able to cache it.

But:

```http
GET /api/me
Authorization: Bearer ...
```

is personalized.

A shared cache could become a serious security vulnerability if the response is cached and then served to another user.

A production rule is:

> Never allow shared caching unless you can prove that the response is safe to share across the requests represented by the cache key.

## HTTP Methods

Cache behaviors also control allowed HTTP methods.

Typical API behavior:

```text
GET
HEAD
OPTIONS
POST
PUT
PATCH
DELETE
```

Static content usually requires fewer methods:

```text
GET
HEAD
```

Restricting methods where possible reduces attack surface and avoids unnecessary origin traffic.

For example:

```text
/static/*
    GET
    HEAD

/api/*
    GET
    HEAD
    OPTIONS
    POST
    PUT
    PATCH
    DELETE
```

The exact set should reflect application requirements.

## Viewer Protocol Policy

CloudFront can enforce how viewers communicate with the distribution.

Common approaches include:

```text
HTTP
  ↓
Redirect
  ↓
HTTPS
```

or:

```text
HTTPS only
```

For production applications, HTTPS should generally be enforced.

A typical architecture is:

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

Using HTTPS between CloudFront and the origin is also recommended for sensitive production traffic.

## Compression

CloudFront can compress eligible responses to reduce transfer size.

This is especially useful for:

- JavaScript
- CSS
- JSON
- HTML
- Text-based assets

Conceptually:

```text
Origin
  │
  ▼
CloudFront
  │
  ├── Brotli / gzip as appropriate
  │
  ▼
Viewer
```

Compression can reduce bandwidth and improve transfer performance.

However, cache behavior and content negotiation must be designed consistently so that compressed and uncompressed representations do not create unexpected caching behavior.

## Response Headers Policies

Response headers can be managed through CloudFront policies rather than duplicating configuration across application servers.

Typical concerns include:

- Security headers
- CORS headers
- Content type behavior
- Browser caching directives

For example:

```text
CloudFront
    │
    ▼
Response Headers Policy
    │
    ▼
Viewer
```

This can simplify security and HTTP response management for static and edge-delivered content.

## CORS and Cache Behaviors

CORS becomes important when a frontend application is served from one origin while APIs are served from another.

Example:

```text
https://app.example.com
        │
        ▼
https://api.example.com
```

CloudFront can participate in handling:

```http
Origin: https://app.example.com
```

and:

```http
Access-Control-Allow-Origin: https://app.example.com
```

CORS configuration should be consistent with cache-key behavior.

If the response varies based on the request `Origin`, the caching strategy must account for that variation.

## Authentication and Authorization

CloudFront can sit in front of authenticated applications, but authentication does not automatically make responses safe to cache.

For example:

```text
GET /api/profile
Authorization: Bearer token-A
```

and:

```text
GET /api/profile
Authorization: Bearer token-B
```

must not accidentally share a cached response.

For user-specific endpoints, a safer design is often:

```text
CloudFront
    │
    ▼
Application
    │
    ▼
Authentication
    │
    ▼
User-specific response
```

with shared caching disabled unless a carefully designed cache-key strategy proves it safe.

## Origin Selection

Cache behaviors can associate different request paths with different origins.

For example:

```text
/static/*
    → S3

/images/*
    → S3

/api/*
    → ALB
```

This lets one CloudFront distribution act as a unified public entry point.

A typical web architecture becomes:

```mermaid
flowchart LR
    U[Viewer] --> CF[CloudFront Distribution]

    CF -->|/static/*| S3[S3 Origin]
    CF -->|/images/*| S3

    CF -->|/api/*| ALB[Application Load Balancer]

    ALB --> APP[Django / FastAPI]
    APP --> REDIS[Redis]
    APP --> DB[PostgreSQL]
```

## Origin Groups and Failover

CloudFront can be configured with origin failover for supported request scenarios.

Conceptually:

```text
                  CloudFront
                       │
                       ▼
                 Primary Origin
                       │
                 Failure / Error
                       │
                       ▼
                Secondary Origin
```

This can improve resilience when the primary origin becomes unavailable.

However, origin failover is not equivalent to complete multi-region disaster recovery.

You still need to consider:

- Data replication
- Database failover
- Application deployment
- Session state
- Configuration
- Secrets
- Dependency availability

CloudFront can participate in a failover architecture but cannot independently make an application multi-region.

## Cache Invalidation

When cached content must be removed before its TTL expires, CloudFront supports invalidation.

For example:

```text
/*
```

can invalidate cached objects across the distribution.

More targeted invalidation is generally preferable:

```text
/static/app.js
/images/logo.png
```

However, frequent broad invalidations can indicate a weak cache strategy.

A better production pattern for static assets is usually:

```text
Old:
app.js

New:
app.7f31c2.js
```

rather than:

```text
app.js
    ↓
Deploy
    ↓
Invalidate /*
```

Content-addressed assets reduce the need for expensive or operationally disruptive invalidations.

## Cache Invalidation vs Versioned Assets

| Strategy | Advantages | Limitations |
|---|---|---|
| Invalidation | Immediate removal of cached content | Operational overhead |
| Versioned filenames | Excellent long-term caching | Requires asset versioning |
| Short TTL | Simple consistency model | More origin requests |
| Long TTL + versioning | High cache efficiency | Requires disciplined deployment |

For frontend assets, long TTL + versioned filenames is generally a strong production pattern.

## Cache Hit Ratio

Cache hit ratio measures how effectively CloudFront serves requests from cache rather than contacting the origin.

Conceptually:

```text
Cache Hit Ratio
=
Cache Hits
--------------
Total Requests
```

For example:

```text
1,000,000 requests
900,000 cache hits

Hit Ratio = 90%
```

The exact metric interpretation should follow CloudFront's monitoring definitions.

A low cache hit ratio can result from:

- Highly dynamic content
- Poor cache-key design
- Excessive query-string variation
- Cookies in cache keys
- Request headers causing fragmentation
- Short TTLs
- Frequent invalidation
- Low object reuse

## Cache Fragmentation

Cache fragmentation occurs when many requests generate distinct cache keys for content that could otherwise be shared.

Example:

```text
/products/42?utm_source=google
/products/42?utm_source=email
/products/42?utm_source=linkedin
```

If every tracking parameter becomes part of the cache key:

```text
3 requests
3 cache objects
```

Instead of:

```text
3 requests
1 cache object
```

At scale, fragmentation can significantly increase origin traffic.

## Query String Strategy

Query strings require deliberate design.

Suppose:

```text
/products/42?currency=USD
```

affects the response, while:

```text
/products/42?utm_source=google
```

does not.

The cache policy should distinguish between them.

Conceptually:

```text
Include:
    currency

Exclude:
    utm_source
    utm_campaign
    tracking_id
```

The objective is:

```text
Cache key
    ↓
Contains response-affecting inputs
    ↓
Excludes irrelevant variability
```

## Cookies and Caching

Cookies can be dangerous for shared caching.

For example:

```http
Cookie: sessionid=abc123
```

may identify a specific user.

If the response depends on that cookie, blindly sharing the response through CloudFront can expose user-specific data.

A safer design is often:

```text
Authenticated request
    ↓
CloudFront
    ↓
Origin
    ↓
User-specific response
```

with appropriate caching restrictions.

Only include cookies in cache behavior when there is a concrete requirement and the resulting cache key is understood.

## Headers and Cache Keys

The same principle applies to request headers.

Potentially response-affecting headers include:

```text
Accept
Accept-Language
Origin
Authorization
Custom tenant headers
```

Including every header is usually a poor strategy.

It creates:

```text
High cache-key cardinality
        ↓
Low cache hit ratio
```

Instead, identify the minimal set of headers that actually changes the response.

## Multi-Tenant APIs

Multi-tenant applications require special attention.

Suppose:

```http
GET /api/orders
X-Tenant-ID: tenant-a
```

and:

```http
GET /api/orders
X-Tenant-ID: tenant-b
```

return different data.

If tenant identity affects the response, it must be accounted for in the caching architecture.

A cache design that treats both requests as identical could expose data across tenants.

For sensitive multi-tenant APIs, disabling shared caching is often simpler and safer unless there is a carefully reviewed cache-key strategy.

## Cache Behaviors and Django

A Django application might use:

```text
CloudFront
    │
    ├── /static/*
    │       ↓
    │      S3
    │
    └── /api/*
            ↓
           ALB
            ↓
          Nginx
            ↓
         Gunicorn
            ↓
          Django
```

Django should remain responsible for:

- Authentication
- Authorization
- Business logic
- Database operations
- Transaction management

CloudFront should primarily handle:

- Global delivery
- Caching
- TLS
- Edge security
- Request routing
- Static asset delivery

## Cache Behaviors and FastAPI

A FastAPI deployment can use a similar architecture:

```text
CloudFront
    │
    ├── /assets/*
    │       ↓
    │      S3
    │
    └── /api/*
            ↓
           ALB
            ↓
       Uvicorn / Gunicorn
            ↓
          FastAPI
```

FastAPI remains responsible for application semantics.

CloudFront should not become the place where complex business decisions are implemented.

## Cache Behaviors and Nginx

Nginx can still perform application-layer reverse proxying behind CloudFront.

For example:

```text
Viewer
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
```

Avoid duplicating the same responsibility across CloudFront and Nginx without a clear reason.

For example:

```text
CloudFront:
    HTTPS redirect

Nginx:
    HTTPS redirect
```

may be redundant if CloudFront already enforces the desired viewer protocol policy.

Each layer should have a clearly defined responsibility.

## CloudFront and API Gateway

CloudFront can also be placed in front of API Gateway where the architecture benefits from CloudFront capabilities.

The important point is that multiple AWS services can participate in the request path:

```text
Viewer
  ↓
CloudFront
  ↓
API Gateway
  ↓
Lambda / Backend
```

The decision should be based on requirements such as:

- Caching
- WAF
- Global delivery
- API management
- Authentication
- Routing
- Observability
- Cost

Do not introduce CloudFront merely because an API uses AWS.

## Distribution Configuration as Code

Production CloudFront configurations should generally be managed through infrastructure as code.

Common approaches include:

- AWS CloudFormation
- AWS CDK
- Terraform

The objective is to make distribution configuration:

- Version-controlled
- Reviewable
- Reproducible
- Auditable
- Deployable through CI/CD

A simplified Terraform-style configuration might look like:

```hcl
resource "aws_cloudfront_distribution" "app" {
  enabled = true

  origin {
    domain_name = aws_lb.app.dns_name
    origin_id   = "app-alb"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"

      origin_ssl_protocols = [
        "TLSv1.2"
      ]
    }
  }

  default_cache_behavior {
    target_origin_id       = "app-alb"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = [
      "GET",
      "HEAD",
      "OPTIONS",
      "POST",
      "PUT",
      "PATCH",
      "DELETE"
    ]

    cached_methods = [
      "GET",
      "HEAD"
    ]
  }
}
```

The exact configuration should be adapted to the application's requirements and current provider schema.

## Deployment Considerations

CloudFront configuration changes are distributed globally and should therefore be treated as production infrastructure changes.

A robust CI/CD flow is:

```text
Git Commit
    │
    ▼
Validation
    │
    ▼
Infrastructure Plan
    │
    ▼
Review
    │
    ▼
Apply
    │
    ▼
CloudFront Configuration Update
    │
    ▼
Global Propagation
    │
    ▼
Validation
```

Changes to:

- Cache policies
- Cache behaviors
- Origins
- TLS
- WAF
- Response headers
- Edge functions

should be reviewed carefully because a configuration mistake can affect global traffic.

## Monitoring and Observability

CloudFront monitoring should cover both delivery and origin behavior.

Important signals include:

| Metric / Signal | Engineering question |
|---|---|
| Requests | How much traffic is arriving? |
| Cache hit ratio | Is caching effective? |
| Origin requests | How much traffic reaches the backend? |
| 4xx responses | Are clients or configurations causing errors? |
| 5xx responses | Is the origin failing? |
| Origin latency | Is the backend slow? |
| Bytes transferred | What is the delivery volume? |
| WAF activity | Is malicious traffic being blocked? |

A useful operational relationship is:

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
Database / Redis Load ↑
        │
        ▼
Latency / Error Rate ↑
```

CloudFront metrics should therefore be correlated with application metrics.

## Security Considerations

Cache behavior configuration can directly affect application security.

### Never Cache Sensitive Responses Accidentally

Avoid shared caching for responses containing:

- User-specific information
- Authentication state
- Private account data
- Tenant-specific information
- Authorization-sensitive content

### Restrict HTTP Methods

Allow only the methods required by each behavior.

### Protect the Origin

Where appropriate, prevent direct public access to origins so that clients cannot bypass CloudFront security controls.

### Use HTTPS

Use HTTPS for viewer traffic and preferably for CloudFront-to-origin communication.

### Review Cache Keys

Ensure sensitive or response-affecting request attributes are handled correctly.

### Use WAF

For public applications, evaluate AWS WAF rules for:

- Common web attacks
- Rate limiting
- IP restrictions
- Managed rule groups
- Application-specific abuse patterns

## Scalability Considerations

CloudFront can dramatically improve effective system scalability when the workload is cacheable.

A simplified model:

```text
10 million viewer requests
          │
          ▼
      CloudFront
          │
    ┌─────┴─────┐
    │           │
  Hits        Misses
    │           │
    │           ▼
    │         Origin
    │           │
    │           ▼
    │       Application
    │
    ▼
 Viewers
```

The origin should be sized for the miss traffic and dynamic traffic, not simply the total viewer request count.

However, cacheability must be validated rather than assumed.

## Reliability Considerations

A reliable CloudFront architecture should consider:

- Multiple origins where appropriate
- Origin failover
- Health monitoring
- Application capacity
- Database availability
- Cache correctness
- Deployment compatibility
- Origin protection
- Recovery procedures

CloudFront improves the availability of the delivery layer, but the complete system remains dependent on the origin for cache misses and dynamic traffic.

## Cost Considerations

CloudFront cost should be evaluated alongside origin cost.

High cache hit ratios can reduce:

- Origin compute
- Origin data transfer
- Database queries
- Application scaling requirements

Poor cache behavior can produce:

```text
Low cache hit ratio
        ↓
More origin requests
        ↓
More compute
        ↓
More database activity
        ↓
Higher cost
```

Cache design is therefore an architectural cost optimization mechanism, not just a performance optimization.

## Common Mistakes

### Using One Cache Policy Everywhere

Static assets, public APIs, and authenticated APIs rarely have identical caching requirements.

Use cache behaviors to separate workloads.

### Caching Personalized Responses

This is one of the most serious CloudFront configuration mistakes.

A response containing user-specific data must not become a shared cache object accidentally.

### Including Too Many Query Parameters

Unnecessary query parameters can fragment the cache.

### Forwarding Every Header

Forwarding excessive headers can increase cache-key cardinality or unnecessary origin traffic.

### Using Very Short TTLs Everywhere

Short TTLs improve freshness but can destroy the benefits of a CDN.

Use content versioning when possible.

### Invalidating Everything After Every Deployment

Frequent:

```text
/*
```

invalidations often indicate that asset versioning or cache design could be improved.

### Making the Default Behavior Too Permissive

The default behavior catches unmatched paths.

A poorly designed default can unintentionally allow methods, caching, or origins that should not apply to unknown paths.

### Ignoring Behavior Ordering

Specific paths should be evaluated before broader patterns.

### Assuming Cache Hit Means Origin-Free Forever

Cached objects expire, can be evicted, and may require revalidation or retrieval.

The origin still needs to handle misses.

## Production Pitfalls

### Cache-Key Explosion

A cache key containing many high-cardinality values can turn an apparently cacheable API into an origin-heavy workload.

### Authorization Headers

Authenticated requests require careful treatment because user identity can affect response content.

### Multi-Tenant Data

Tenant identifiers must never be accidentally omitted from a cache design when they affect response content.

### CORS Variation

If responses differ based on the `Origin` header, caching must account for that variation.

### Deployment Race Conditions

A new frontend deployment may reference assets that are not yet available at the origin or may interact with cached HTML referencing old/new asset versions.

### Inconsistent Cache Headers

If application code, Nginx, S3 metadata, and CloudFront policies all attempt to control caching independently, debugging becomes difficult.

Define a clear ownership model.

## Practical Architecture

A production web application might use:

```mermaid
flowchart TD
    U[Internet Users] --> CF[CloudFront Distribution]

    CF -->|/static/*| S3[S3 Static Assets]
    CF -->|/images/*| S3

    CF -->|/api/public/*| ALB[Application Load Balancer]
    CF -->|/api/private/*| ALB
    CF -->|/*| ALB

    ALB --> NGINX[Nginx]
    NGINX --> APP[Django / FastAPI]

    APP --> REDIS[Redis]
    APP --> DB[PostgreSQL]
    APP --> KAFKA[Kafka]
```

The cache strategy could be:

```text
/static/*
    Long TTL
    S3
    GET / HEAD

/images/*
    Long TTL
    S3
    GET / HEAD

/api/public/*
    Controlled caching
    ALB

/api/private/*
    No shared caching
    ALB

/*
    Application default
```

This design separates static delivery from dynamic application processing while preserving a single public entry point.

## Request Processing Model

A useful mental model for every CloudFront request is:

```text
Viewer Request
      │
      ▼
Distribution
      │
      ▼
Cache Behavior Selection
      │
      ▼
Request Policy Evaluation
      │
      ▼
Cache Key Evaluation
      │
      ▼
Cache Lookup
      │
      ├── Hit ───────► Response
      │
      └── Miss
             │
             ▼
           Origin
             │
             ▼
       Origin Response
             │
             ▼
        Cache Decision
             │
             ▼
          Viewer
```

The exact processing sequence contains additional CloudFront-specific details, but this model is sufficient for architectural reasoning.

## Interview Traps

### Is a distribution the same thing as an edge location?

No.

A distribution is the logical configuration boundary. Edge locations are physical/network infrastructure used to serve requests.

### Can one distribution have multiple origins?

Yes.

A distribution can route different request paths to different origins through cache behaviors.

### Can one distribution have multiple cache behaviors?

Yes.

This is a core CloudFront design mechanism.

### Does every cache behavior have its own distribution?

No.

Multiple cache behaviors exist inside a single distribution.

### Does `/api/*` automatically mean "do not cache"?

No.

The path pattern selects a behavior. The behavior's cache policy determines caching behavior.

### Does a cache policy determine what is sent to the origin?

Not by itself.

Cache policies primarily define caching and cache-key behavior. Origin request policies control additional request information sent to the origin.

### Why not include every query parameter in the cache key?

Because irrelevant query parameters create cache fragmentation and reduce cache hit ratio.

### Why is caching authenticated data dangerous?

Because a shared cached response could be served to another user if the cache key does not correctly represent the response's user-specific dimensions.

### Why use versioned static assets?

They allow long TTLs while ensuring that changed content receives a new URL.

### Can CloudFront replace an ALB?

No.

CloudFront is a global edge delivery service; ALB is a regional load balancer.

### Can CloudFront replace Redis?

No.

CloudFront caches HTTP responses at the edge; Redis generally provides application-level data caching.

## Production Best Practices

- Treat the distribution as the global configuration boundary.
- Keep cache behaviors narrowly scoped to clear workload categories.
- Use specific path patterns before broad patterns.
- Design the default behavior deliberately.
- Separate static and dynamic traffic.
- Use S3 for appropriate static assets.
- Use long TTLs for immutable, versioned assets.
- Keep authenticated and personalized responses out of shared caches unless the cache-key design has been explicitly reviewed.
- Include only response-affecting values in the cache key.
- Avoid forwarding unnecessary headers, cookies, and query parameters.
- Distinguish cache policy configuration from origin request policy configuration.
- Restrict HTTP methods to those actually required.
- Enforce HTTPS for production viewer traffic.
- Prefer HTTPS between CloudFront and origins.
- Protect origins from direct access where appropriate.
- Use AWS WAF for Internet-facing applications where appropriate.
- Use infrastructure as code for distribution configuration.
- Monitor cache hit ratio together with origin request volume and application latency.
- Prefer versioned assets over frequent broad invalidations.
- Test cache behavior changes before global production rollout.
- Treat CloudFront configuration changes as production infrastructure changes.
- Keep business logic in Django, FastAPI, or the appropriate backend rather than distributing complex logic unnecessarily to the edge.

## Key Takeaways

- **A CloudFront distribution is the global configuration boundary:** It connects domains, origins, cache behaviors, security controls, TLS, and edge processing into one delivery architecture.
- **Cache behaviors provide workload-specific routing and caching:** Path patterns can route static assets, public APIs, private APIs, and other workloads to different origins and policies.
- **Cache-key design determines both correctness and performance:** Include response-affecting inputs, exclude irrelevant variability, and never allow personalized responses to become unsafe shared cache objects.
- **Static and dynamic content require different strategies:** Versioned static assets can use aggressive caching, while authenticated and personalized APIs generally require restricted or disabled shared caching.
- **CloudFront reduces origin load but does not replace the backend:** ALB, Nginx, Django/FastAPI, Redis, PostgreSQL, and other backend components remain responsible for regional application processing and data workloads.