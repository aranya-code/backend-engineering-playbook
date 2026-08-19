# 04- Request Lifecycle

## Overview

A CloudFront request lifecycle describes how a viewer request is processed from the moment it reaches CloudFront until the response is returned to the viewer.

The lifecycle is not simply:

```text
Viewer → CloudFront → Origin
```

CloudFront makes several decisions in between:

```text
Viewer Request
      │
      ▼
CloudFront Edge
      │
      ├── Viewer request processing
      │
      ├── Cache behavior selection
      │
      ├── Cache policy evaluation
      │
      ├── Cache key construction
      │
      ├── Cache lookup
      │
      ├── Cache Hit ───────────────► Viewer
      │
      └── Cache Miss
              │
              ▼
        Origin Request
              │
              ▼
            Origin
              │
              ▼
        Origin Response
              │
              ├── Cache if eligible
              │
              ▼
            Viewer
```

Understanding this lifecycle is essential when CloudFront sits in front of a backend such as Django, FastAPI, Nginx, an Application Load Balancer, or an S3 bucket.

A CloudFront cache hit can bypass the entire backend stack. A cache miss can traverse the complete application path:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Django / FastAPI
    ↓
Redis
    ↓
PostgreSQL
```

This makes CloudFront configuration directly relevant to application latency, origin capacity, database load, security, and infrastructure cost.

## End-to-End Lifecycle

The complete conceptual lifecycle is:

```mermaid
sequenceDiagram
    participant V as Viewer
    participant CF as CloudFront
    participant EC as Edge Cache
    participant O as Origin
    participant A as Application

    V->>CF: HTTPS Request
    CF->>CF: Select distribution
    CF->>CF: Select cache behavior
    CF->>CF: Apply viewer-request processing
    CF->>CF: Construct cache key
    CF->>EC: Cache lookup

    alt Cache Hit
        EC-->>CF: Cached response
        CF-->>V: HTTP response
    else Cache Miss
        CF->>CF: Build origin request
        CF->>O: Origin request
        O->>A: Application request
        A-->>O: HTTP response
        O-->>CF: Origin response
        CF->>CF: Evaluate caching
        CF->>EC: Store eligible response
        CF-->>V: HTTP response
    end
```

The exact internal implementation contains additional AWS-managed infrastructure and processing, but this model provides the correct engineering mental model.

## Viewer Request

The lifecycle starts when a client sends an HTTP or HTTPS request to a hostname associated with the CloudFront distribution.

For example:

```http
GET /api/products/42?currency=USD HTTP/1.1
Host: api.example.com
Accept: application/json
Authorization: Bearer <token>
```

The client might be:

- A browser
- A mobile application
- A backend service
- A CLI client
- An IoT device

DNS directs the hostname to CloudFront infrastructure rather than directly to the application origin.

Conceptually:

```text
Client
  │
  │ DNS
  ▼
CloudFront
  │
  ▼
Edge Infrastructure
```

The viewer does not decide which CloudFront edge processes the request. CloudFront routes the request through its globally distributed infrastructure.

## TLS Processing

For HTTPS traffic, CloudFront establishes the viewer-side TLS connection.

The architecture becomes:

```text
Viewer
   │
   │ HTTPS
   ▼
CloudFront
   │
   │ HTTPS / HTTP
   ▼
Origin
```

Production systems should generally enforce HTTPS.

A cache behavior can use:

| Viewer protocol policy | Behavior |
|---|---|
| `allow-all` | Accept HTTP and HTTPS |
| `redirect-to-https` | Redirect HTTP clients to HTTPS |
| `https-only` | Reject HTTP requests |

A common production configuration is:

```text
HTTP request
     │
     ▼
CloudFront
     │
     └── Redirect
             │
             ▼
        HTTPS request
```

TLS between CloudFront and the origin should also normally be used for sensitive or production traffic.

## Viewer Request Processing

CloudFront can execute edge logic during request processing.

Common technologies include:

- CloudFront Functions
- Lambda@Edge

Typical use cases include:

- URL normalization
- Lightweight redirects
- Request transformations
- Header manipulation
- Simple routing decisions
- Edge authentication or authorization logic where appropriate

For example:

```text
Viewer
  │
  ▼
CloudFront Function
  │
  ├── Normalize URL
  ├── Add / modify header
  └── Continue request
```

Edge functions should not become a replacement for the backend application.

A useful separation is:

```text
CloudFront
    │
    └── Lightweight edge processing
              │
              ▼
        Application
              │
              └── Business logic
```

Complex business rules, database operations, and long-running processing belong in the application layer.

## Cache Behavior Selection

CloudFront distributions contain cache behaviors that determine how requests are processed.

Example:

```text
/static/*
/images/*
/api/*
*
```

A request such as:

```text
/static/app.js
```

should use the `/static/*` behavior.

A request such as:

```text
/api/products/42
```

should use the `/api/*` behavior.

If no more specific behavior matches, the default behavior applies.

```mermaid
flowchart TD
    A[Viewer Request] --> B{Path Pattern}

    B -->|/static/*| C[Static Cache Behavior]
    B -->|/images/*| D[Image Cache Behavior]
    B -->|/api/*| E[API Cache Behavior]
    B -->|No Specific Match| F[Default Cache Behavior]

    C --> G[S3 Origin]
    D --> G
    E --> H[Application Origin]
    F --> H
```

Behavior selection is important because different workloads require different caching, forwarding, security, and origin settings.

## Cache Behavior Example

A production application might use:

| Request path | Cache behavior | Origin | Typical strategy |
|---|---|---|---|
| `/static/*` | Static | S3 | Long-lived cache |
| `/images/*` | Images | S3 | Long-lived cache |
| `/api/public/*` | Public API | ALB | Controlled caching |
| `/api/private/*` | Private API | ALB | Usually no shared caching |
| `*` | Default | ALB | Explicitly configured |

The behavior determines which policies and origin configuration apply to the request.

## Cache Policy Evaluation

CloudFront uses a cache policy to determine how the cache key is constructed and how cached objects are retained.

Relevant dimensions can include:

- Query strings
- Headers
- Cookies
- Minimum TTL
- Default TTL
- Maximum TTL
- Compression-related behavior

A simplified cache key can be represented as:

```text
Cache Key
    =
Path
+
Configured Query Strings
+
Configured Headers
+
Configured Cookies
```

Only the configured request attributes contribute to cache-key variation.

For example, suppose:

```text
/products/42?currency=USD
/products/42?currency=INR
```

produce different responses.

Then `currency` needs to participate in the caching strategy.

Conversely:

```text
/products/42?utm_source=google
/products/42?utm_source=email
```

might return identical application content.

Including `utm_source` in the cache key would unnecessarily fragment the cache.

## Cache Key Correctness

Cache-key design is both a performance and correctness concern.

Suppose a backend returns different responses based on:

```http
X-Tenant-ID: tenant-a
```

and:

```http
X-Tenant-ID: tenant-b
```

If tenant identity affects the response, the caching strategy must prevent the wrong tenant from receiving another tenant's cached representation.

The general rule is:

> Every request attribute that changes a shared cached response must be represented in the cache strategy, or the response must not be shared through the cache.

At the same time, unnecessary cache-key dimensions reduce cache efficiency.

```text
Too few dimensions
        ↓
Incorrect sharing risk

Too many dimensions
        ↓
Cache fragmentation

Correct dimensions
        ↓
Safe + efficient caching
```

## Origin Request Policy

Cache policy and origin request policy solve different problems.

A useful mental model is:

```text
Cache Policy
    │
    └── What differentiates cached objects?

Origin Request Policy
    │
    └── What additional information does the origin need?
```

For example:

```text
Cache key:
    /products/42

Origin request:
    /products/42
    X-Tenant-ID: tenant-a
    Accept-Language: en-US
```

The origin may need information that should not necessarily create additional cached variants.

This separation allows backend engineers to send required request information to Django or FastAPI without unnecessarily destroying cache reuse.

## Cache Lookup

After the applicable behavior and cache key are determined, CloudFront checks its cache.

There are two primary outcomes:

```text
Cache Lookup
     │
     ├── Hit
     │
     └── Miss
```

The difference between these paths is fundamental.

## Cache Hit

A cache hit occurs when CloudFront can satisfy the request using an existing cached object associated with the request's cache key.

```text
Viewer
  │
  ▼
CloudFront
  │
  ▼
Edge Cache
  │
  └── HIT
       │
       ▼
    Response
       │
       ▼
     Viewer
```

The origin does not need to process the request.

For static assets, this is the ideal path.

```text
GET /static/app.91c3e7.js

Viewer
  ↓
CloudFront
  ↓
Cache Hit
  ↓
Viewer
```

The request can therefore avoid:

- ALB
- Nginx
- Application servers
- Redis
- PostgreSQL

## Cache Miss

A cache miss occurs when CloudFront cannot satisfy the request from its cache.

The request then proceeds toward the origin.

```text
Viewer
  │
  ▼
CloudFront
  │
  ▼
Cache
  │
  └── MISS
       │
       ▼
     Origin
```

For an API:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Django / FastAPI
```

The origin response can subsequently be cached if the response and cache configuration allow it.

## Request Collapsing

A popular object can generate many simultaneous cache misses.

Without request collapsing, a conceptual model would be:

```text
Request A ──► Origin
Request B ──► Origin
Request C ──► Origin
Request D ──► Origin
```

CloudFront can collapse simultaneous requests for the same cache key so that one request retrieves the object while other requests wait for the result.

```text
Request A ──┐
Request B ──┤
Request C ──┤
Request D ──┘
       │
       ▼
  CloudFront
       │
       ▼
 One origin request
       │
       ▼
    Origin
       │
       ▼
 Cached response
   /  /  \  \
  A  B    C  D
```

This is especially useful during traffic spikes involving popular objects.

Request collapsing depends on requests sharing the same cache key. Excessive cache-key variation can therefore prevent requests from benefiting from the same cache object.

## Origin Request Construction

On a cache miss, CloudFront constructs a request for the configured origin.

The origin request is not necessarily an exact copy of the viewer request.

Conceptually:

```text
Viewer Request
    │
    ├── Path
    ├── Query strings
    ├── Headers
    ├── Cookies
    └── Body
          │
          ▼
      CloudFront
          │
          ├── Cache Policy
          ├── Origin Request Policy
          └── Edge Processing
          │
          ▼
      Origin Request
```

This distinction is important when debugging applications that appear to receive incomplete or unexpected request information.

## Origin Selection

The selected cache behavior determines the origin configuration used for the request.

Typical origins include:

- Amazon S3
- Application Load Balancer
- API Gateway
- EC2-based applications
- Custom HTTP servers

For example:

```text
/static/*
    ↓
S3

/api/*
    ↓
ALB
```

This allows one CloudFront distribution to front multiple backend systems.

## S3 Origin Request

A static asset might follow:

```text
Viewer
   │
   ▼
CloudFront
   │
   ├── Hit → Viewer
   │
   └── Miss
         │
         ▼
        S3
         │
         ▼
     CloudFront
         │
         ▼
       Viewer
```

For example:

```text
/static/app.91c3e7.js
```

could map to an object such as:

```text
s3://frontend-assets/static/app.91c3e7.js
```

Once cached, subsequent requests can be served from CloudFront without contacting S3.

## ALB Origin Request

A dynamic API might follow:

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
   │
   ▼
Django / FastAPI
```

For example:

```http
GET /api/products/42
```

can eventually execute application code.

The latency of the complete request is therefore affected by every layer after the CloudFront cache miss.

## Application Processing

Once the request reaches Django or FastAPI, normal backend processing occurs.

For Django:

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
    ↓
Redis
    ↓
PostgreSQL
```

For FastAPI:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Uvicorn / Gunicorn
    ↓
FastAPI
    ↓
Redis
    ↓
PostgreSQL
```

The application can perform:

- Authentication
- Authorization
- Validation
- Business logic
- Redis lookups
- PostgreSQL queries
- Kafka publishing
- Celery task scheduling

CloudFront does not replace these responsibilities.

## Application-Level Caching

CloudFront and Redis operate at different layers.

```text
CloudFront
    ↓
HTTP response cache
    ↓
Global edge delivery

Redis
    ↓
Application data cache
    ↓
Backend data access
```

A request might therefore follow:

```text
Viewer
  ↓
CloudFront
  ↓
Cache Miss
  ↓
Django
  ↓
Redis
  ↓
PostgreSQL
```

A CloudFront hit can bypass Django entirely.

A CloudFront miss can still benefit from Redis after reaching Django.

These caching layers are complementary rather than interchangeable.

## Origin Response

The origin returns an HTTP response.

Example:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: public, max-age=60

{
  "id": 42,
  "name": "Keyboard"
}
```

CloudFront evaluates the response and determines whether it can be stored according to the configured caching rules.

Conceptually:

```text
Origin Response
      │
      ▼
CloudFront
      │
      ├── Cacheable
      │      │
      │      ▼
      │   Edge Cache
      │
      └── Not cacheable
             │
             ▼
          Viewer
```

The exact result depends on the cache policy, origin response headers, HTTP method, and other CloudFront configuration.

## TTL and Freshness

TTL controls how long an object can remain fresh in CloudFront's cache.

An origin might return:

```http
Cache-Control: public, max-age=3600
```

or:

```http
Cache-Control: public, s-maxage=3600
```

CloudFront cache policies also define minimum, default, and maximum TTL behavior.

For immutable assets, a common production pattern is:

```http
Cache-Control: public, max-age=31536000, immutable
```

with content-addressed filenames:

```text
app.91c3e7.js
app.4d21af.css
```

The filename changes whenever the content changes.

This allows long-lived caching without relying on immediate cache invalidation.

## Minimum TTL Consideration

Minimum TTL deserves particular attention for API workloads.

A non-zero minimum TTL can cause CloudFront to cache an object for at least that duration even when the origin attempts to prevent caching with directives such as:

```http
Cache-Control: no-cache
Cache-Control: no-store
Cache-Control: private
```

Therefore, if the origin must retain control over whether a response can be cached, configure the cache policy accordingly.

For sensitive dynamic APIs, blindly applying a long minimum TTL is a serious production mistake.

## Personalized Responses

Consider:

```http
GET /api/me
Authorization: Bearer token-A
```

The response may be:

```json
{
  "user_id": 1001,
  "email": "user@example.com"
}
```

Another user sends:

```http
GET /api/me
Authorization: Bearer token-B
```

and receives a different response.

This is fundamentally different from a public object such as:

```text
/static/logo.png
```

A shared cache must not accidentally serve one user's representation to another user.

A safe architecture is often:

```text
Viewer
   ↓
CloudFront
   ↓
ALB
   ↓
Application
   ↓
Authentication
   ↓
Authorization
   ↓
User-specific response
```

Shared caching of personalized responses should only be used when cache-key isolation and application semantics have been deliberately designed.

## Public API Responses

Some APIs can safely be cached.

For example:

```http
GET /api/catalog/products/42
```

may return the same representation to all users.

A possible architecture is:

```text
Viewer
  ↓
CloudFront
  ↓
Cache Hit → Response

Cache Miss
  ↓
ALB
  ↓
Django / FastAPI
  ↓
PostgreSQL
```

For read-heavy data that changes infrequently, this can significantly reduce origin load.

The fact that an endpoint uses `GET` does not automatically make it safe to cache. Cacheability is an application semantic decision.

## Query String Handling

Consider:

```text
/products/42?currency=USD
/products/42?currency=INR
```

If the response changes based on `currency`, it should participate in the cache strategy.

Now consider:

```text
/products/42?utm_source=google
/products/42?utm_source=email
```

If these parameters do not change the response, including them in the cache key unnecessarily creates separate cache variants.

The desired model is:

```text
Response-affecting parameter
        │
        ▼
Cache variation

Tracking / irrelevant parameter
        │
        ▼
Avoid cache variation
```

This is one of the most important techniques for improving cache efficiency.

## Header Handling

Headers can also affect response semantics.

For example:

```http
Accept-Language: en-US
```

might produce an English representation while:

```http
Accept-Language: fr-FR
```

might produce a French representation.

If a header changes the response, the caching architecture must account for that variation.

However, forwarding arbitrary headers is generally undesirable because it increases cache cardinality and can increase origin traffic.

A better approach is:

```text
Identify response-affecting headers
            ↓
Include only required headers
            ↓
Keep cache cardinality controlled
```

## Cookie Handling

Cookies can contain:

- Session identifiers
- Authentication information
- Feature flags
- User preferences
- Tracking information

For example:

```http
Cookie: sessionid=abc123
```

If the response varies by session, blindly sharing the response through CloudFront is unsafe.

Personalized session-based pages are therefore commonly configured with caching disabled or carefully isolated.

## Response Headers

CloudFront can return origin response headers and can also apply response headers policies.

Response headers are useful for concerns such as:

- CORS
- Security headers
- Browser caching
- Cross-origin behavior

A production architecture should establish ownership clearly:

```text
Application
    │
    └── Business-specific headers

CloudFront
    │
    └── Edge / delivery-level headers
```

Avoid having CloudFront, Nginx, and Django independently manipulate the same security-sensitive headers without an explicit policy.

## Error Responses

The origin can return:

```text
400
401
403
404
429
500
502
503
504
```

The first debugging question should be:

> Did CloudFront generate the response, or did the origin generate it?

For example:

```text
Viewer
  ↓
CloudFront
  ↓
403
```

may indicate an edge-level configuration or access issue.

While:

```text
Viewer
  ↓
CloudFront
  ↓
Origin
  ↓
Application
  ↓
403
```

may represent an application authorization decision.

This distinction significantly reduces debugging time.

## Origin Failover

CloudFront can use origin groups for configured failover scenarios.

Conceptually:

```text
CloudFront
    │
    ▼
Primary Origin
    │
    ├── Success
    │      ↓
    │    Viewer
    │
    └── Configured failure
             │
             ▼
       Secondary Origin
             │
             ▼
           Viewer
```

Origin failover improves resilience but does not constitute complete disaster recovery.

A production multi-region architecture still requires consideration of:

- Database replication
- Application deployment
- Secrets
- Configuration
- Stateful services
- Data consistency
- Regional dependencies

## Origin Shield

Origin Shield introduces an additional centralized caching layer between CloudFront edge locations and the origin.

```text
Viewers
   │
   ▼
CloudFront Edge
   │
   ▼
Origin Shield
   │
   ▼
Origin
```

This can reduce the number of requests reaching an origin and can improve cache aggregation for globally distributed traffic.

It is most useful when origin requests are relatively expensive and centralized caching provides measurable benefit.

## Cache Hit Ratio

Cache hit ratio is a key CloudFront performance metric.

A simplified formula is:

```text
Cache Hit Ratio
=
Cache Hits / Total Requests
```

For example:

```text
10,000,000 viewer requests

8,500,000 cache hits
1,500,000 requests requiring origin processing
```

The origin therefore does not necessarily need to handle all 10 million viewer requests.

A low hit ratio can indicate:

- Excessive cache-key variation
- Short TTLs
- Incorrect cache behavior configuration
- Highly dynamic content
- Uncacheable responses
- Unnecessary query-string variation

## Cache Miss Amplification

Poor cache-key design can create a chain reaction:

```text
High cache-key cardinality
        ↓
Low cache hit ratio
        ↓
More origin requests
        ↓
Higher application CPU
        ↓
More Redis requests
        ↓
More PostgreSQL queries
        ↓
Higher latency
        ↓
Higher infrastructure cost
```

This is why CloudFront configuration should be treated as part of backend performance engineering.

## Static Asset Lifecycle

Static assets are usually the simplest CloudFront workload.

```text
GET /static/app.91c3e7.js
        │
        ▼
CloudFront
        │
        ├── Cache Hit
        │      │
        │      ▼
        │    Viewer
        │
        └── Cache Miss
               │
               ▼
              S3
               │
               ▼
          CloudFront
               │
               ▼
             Viewer
```

A subsequent request can be served entirely from CloudFront.

Immutable, versioned assets are excellent candidates for long TTLs.

## API Lifecycle with Django

A production API request can follow:

```mermaid
sequenceDiagram
    participant C as Client
    participant CF as CloudFront
    participant ALB as ALB
    participant N as Nginx
    participant D as Django
    participant R as Redis
    participant DB as PostgreSQL

    C->>CF: GET /api/products/42
    CF->>CF: Select cache behavior
    CF->>CF: Construct cache key
    CF->>CF: Cache lookup

    alt Cache Hit
        CF-->>C: Cached JSON
    else Cache Miss
        CF->>ALB: Origin request
        ALB->>N: HTTP request
        N->>D: Proxy request
        D->>R: Lookup product

        alt Redis Hit
            R-->>D: Product
        else Redis Miss
            D->>DB: Query product
            DB-->>D: Product
            D->>R: Cache product
        end

        D-->>N: JSON response
        N-->>ALB: HTTP response
        ALB-->>CF: Origin response
        CF-->>C: HTTP response
    end
```

This demonstrates two separate caching layers:

```text
CloudFront cache
    ↓
HTTP response

Redis cache
    ↓
Application data
```

A CloudFront hit bypasses Redis and PostgreSQL completely.

## API Lifecycle with FastAPI

The same architecture can be implemented with FastAPI:

```text
Client
  ↓
CloudFront
  ↓
ALB
  ↓
Nginx
  ↓
Uvicorn / Gunicorn
  ↓
FastAPI
  ├── Redis
  └── PostgreSQL
```

The CloudFront layer should remain focused on HTTP delivery and caching.

FastAPI remains responsible for:

- Request validation
- Authentication
- Authorization
- Business logic
- Data access

## CloudFront and gRPC

CloudFront supports gRPC traffic, but gRPC requests are not cached.

The architecture can therefore look like:

```text
gRPC Client
    │
    ▼
CloudFront
    │
    ▼
gRPC Origin
```

This is fundamentally different from a cacheable static HTTP object because there is no reusable CloudFront cache object representing a gRPC response.

## CloudFront and Kafka

Kafka operates at a different architectural layer.

A backend request might perform:

```text
Viewer
  ↓
CloudFront
  ↓
API
  ↓
Django / FastAPI
  ├── PostgreSQL
  └── Kafka
        ↓
     Consumers
```

CloudFront handles HTTP delivery and caching.

Kafka handles asynchronous event streaming.

Neither replaces the other.

## Monitoring the Lifecycle

CloudFront should be monitored together with the origin and backend services.

| Layer | Useful signals |
|---|---|
| Viewer | Latency, HTTP errors |
| CloudFront | Requests, cache hits, cache misses, 4xx, 5xx |
| Origin | Request count, latency, 4xx, 5xx |
| ALB | Target response time, target errors |
| Nginx | Access logs, error logs, upstream latency |
| Django / FastAPI | Request latency, throughput, errors |
| Redis | Hit ratio, latency, memory |
| PostgreSQL | Query latency, connections, CPU |
| Kafka | Throughput, consumer lag |

A useful incident-debugging path is:

```text
Viewer latency increased
        │
        ▼
CloudFront metrics
        │
        ├── Cache hit ratio decreased
        │       │
        │       ▼
        │   Origin traffic increased
        │
        └── Cache hit ratio unchanged
                │
                ▼
          Investigate origin latency
                │
                ▼
        ALB / Nginx / Application
                │
                ▼
           Redis / Database
```

## Logging and Correlation

A request should be traceable across the infrastructure stack where practical.

A useful model is:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Application
    ↓
Database / Redis
```

During an incident, correlate:

- Timestamp
- Request path
- HTTP method
- Status code
- CloudFront result
- Origin status
- Application request ID
- Backend latency

CloudFront logging can help distinguish cache behavior and edge outcomes from origin behavior.

The important operational principle is:

> Do not diagnose a CloudFront incident using application logs alone.

A cache hit might never appear in the application logs.

## Performance Analysis

A request's latency can be conceptualized as:

```text
Viewer → CloudFront
        +
CloudFront processing
        +
Cache lookup
        +
Origin network latency
        +
Application processing
        +
Database / downstream latency
```

For a cache hit:

```text
Viewer
  ↓
CloudFront
  ↓
Response
```

For a cache miss:

```text
Viewer
  ↓
CloudFront
  ↓
Origin
  ↓
Application
  ↓
Database
  ↓
Application
  ↓
Origin
  ↓
CloudFront
  ↓
Viewer
```

The performance difference can be significant.

## Security Considerations

The request lifecycle must preserve security boundaries.

### Enforce HTTPS

Production public traffic should generally use HTTPS.

### Protect the Origin

Where appropriate, configure the origin so clients cannot simply bypass CloudFront and directly access the backend.

### Preserve Authorization

CloudFront should not be treated as a replacement for application-level authorization.

Django and FastAPI should still enforce:

```text
Authentication
      ↓
Authorization
      ↓
Business operation
```

### Protect Personalized Responses

Never allow one user's response to become another user's shared cache response.

### Preserve Tenant Isolation

If the response depends on tenant identity, the caching strategy must preserve tenant boundaries.

### Minimize Forwarded Data

Forward only the headers, cookies, and query strings that the origin actually needs.

## Scalability Considerations

CloudFront allows cacheable traffic to be handled at the edge rather than by the origin.

```text
Viewer Traffic
      │
      ▼
 CloudFront
      │
      ├───────────────┐
      │               │
 Cache Hits       Cache Misses
      │               │
      ▼               ▼
    Edge             Origin
                      │
                      ▼
                 Application
                      │
                 ┌────┴────┐
                 ▼         ▼
               Redis   PostgreSQL
```

The origin should therefore be capacity-planned primarily around:

- Cache misses
- Dynamic requests
- Personalized requests
- Writes
- Uncacheable responses
- Revalidations

CloudFront reduces origin pressure but does not eliminate backend scaling requirements.

## Reliability Considerations

CloudFront is a highly distributed delivery layer, but application availability remains an end-to-end property.

A production system may still require:

- Multi-AZ application infrastructure
- Load balancing
- Database failover
- Redis resilience
- Origin failover
- Multi-region deployment where required
- Automated rollback
- Monitoring and alerting

A highly available CDN cannot compensate for an unavailable database.

## Cost Considerations

A higher cache hit ratio can reduce downstream infrastructure consumption:

```text
More cache hits
      ↓
Fewer origin requests
      ↓
Less application compute
      ↓
Fewer database queries
      ↓
Potentially lower total system cost
```

However, CloudFront itself has request and data-transfer costs.

Cost optimization should therefore consider:

```text
CloudFront
+
ALB
+
Compute
+
Database
+
Redis
+
Data Transfer
```

Do not optimize CloudFront caching solely around hit ratio. Correctness, freshness, security, and total cost all matter.

## Common Mistakes

### Assuming Every Request Reaches the Origin

A cache hit can terminate the request at CloudFront.

This explains why CloudFront request counts can be significantly higher than application request counts.

### Treating CloudFront as a Simple Reverse Proxy

CloudFront performs cache behavior selection, cache-key evaluation, caching, edge processing, and origin routing.

### Assuming Every GET Request Is Cacheable

A `GET` request can still return private or personalized information.

### Ignoring Cache-Key Design

An incorrect cache key can cause either:

```text
Unsafe response sharing
```

or:

```text
Excessive cache fragmentation
```

### Forwarding Every Header

Forwarding unnecessary headers increases request variation and can reduce cache efficiency.

### Forwarding Every Query String

Tracking parameters and other irrelevant query strings can create unnecessary cache variants.

### Using Long TTLs for Mutable Content

Long TTLs are appropriate for immutable versioned assets, not arbitrary dynamic content.

### Using a Long Minimum TTL for Private APIs

This can cause responses to remain cached longer than the origin intended.

### Assuming Origin Request Policy Controls the Cache Key

It does not.

The cache policy determines cache-key behavior.

### Ignoring Cache Behavior Ordering

An incorrect path pattern or behavior ordering can cause requests to use the wrong configuration.

### Debugging Only Django or FastAPI

A request may never reach the application.

Always determine whether the problem is at:

```text
Viewer
CloudFront
Origin
ALB
Nginx
Application
Redis
PostgreSQL
```

## Production Best Practices

- Design cache behaviors around distinct workload types.
- Make the default cache behavior explicit and deliberate.
- Keep cache-key variation to the minimum required for correctness.
- Exclude irrelevant query strings, headers, and cookies from cache-key variation.
- Use origin request policies when the origin needs additional request information without requiring additional cache variants.
- Use long-lived caching for immutable, versioned static assets.
- Be conservative when caching authenticated or personalized responses.
- Use zero minimum TTL where the origin must retain control over cache-prevention directives.
- Monitor cache hit ratio together with origin latency.
- Correlate CloudFront metrics with ALB, Nginx, and application logs.
- Protect origins from direct access where the architecture permits it.
- Enforce HTTPS for production traffic.
- Use infrastructure as code for CloudFront configuration.
- Test cache behavior changes using realistic query strings, headers, cookies, and authentication scenarios.
- Use request collapsing and Origin Shield when they provide measurable origin-load benefits.
- Treat CloudFront configuration changes as application-impacting infrastructure changes.
- Keep authorization and business logic in the backend application.
- Use immutable asset naming for aggressive static caching.
- Validate caching behavior before deploying configuration changes to production.

## Interview Traps

### What happens during a CloudFront cache hit?

CloudFront can return the cached response without contacting the origin.

### What happens during a cache miss?

CloudFront creates an origin request, retrieves the response, evaluates whether it can be cached, and returns the response to the viewer.

### Does CloudFront forward the complete viewer request to the origin?

No. The origin request is constructed according to the configured policies and request-processing configuration.

### What is the difference between cache policy and origin request policy?

The cache policy determines cache-key inputs and TTL behavior. The origin request policy controls additional request information sent to the origin.

### Why is cache-key cardinality important?

A large number of unique cache-key combinations creates many cache variants, reducing cache reuse and increasing origin traffic.

### Can CloudFront cache authenticated requests?

Caching authenticated or personalized responses requires careful cache-key and application design. It should not be enabled simply because the request is technically cacheable at the HTTP level.

### Can CloudFront cache gRPC responses?

No. CloudFront can support gRPC traffic, but gRPC responses are not cached.

### Does CloudFront replace Redis?

No.

CloudFront caches HTTP responses at the edge. Redis is typically used for application-level data caching.

### Does CloudFront replace an ALB?

No.

CloudFront provides global edge delivery and caching. An ALB distributes requests across application targets within the configured AWS environment.

## Production Architecture

A typical backend architecture can look like:

```mermaid
flowchart TD
    V[Users / Clients] --> CF[CloudFront]

    CF -->|Cache Hit| V
    CF -->|Cache Miss| ALB[Application Load Balancer]

    CF -->|Static Asset Miss| S3[S3]

    ALB --> N[Nginx]
    N --> APP[Django / FastAPI]

    APP --> R[Redis]
    APP --> DB[PostgreSQL]
    APP --> K[Kafka]

    subgraph Edge Layer
        CF
    end

    subgraph Application Layer
        ALB
        N
        APP
        R
        DB
        K
    end

    subgraph Static Storage
        S3
    end
```

Different request types then follow different paths.

### Static Asset

```text
Viewer
  ↓
CloudFront
  ↓
S3 on cache miss
```

### Public Cacheable API

```text
Viewer
  ↓
CloudFront
  ↓
Origin on cache miss
```

### Private API

```text
Viewer
  ↓
CloudFront
  ↓
ALB
  ↓
Nginx
  ↓
Django / FastAPI
```

### Application Data

```text
Django / FastAPI
  ↓
Redis
  ↓
PostgreSQL
```

## End-to-End Mental Model

When debugging or designing a CloudFront request, reason through the lifecycle in this order:

```text
1. Which CloudFront distribution received the request?
2. Which cache behavior matched?
3. Which cache policy is attached?
4. What cache-key dimensions are used?
5. Was the request a cache hit or miss?
6. If it was a miss, what request was sent to the origin?
7. Which origin received the request?
8. Did the origin return success or an error?
9. Was the response eligible for caching?
10. What response did CloudFront return to the viewer?
```

This sequence provides a reliable debugging framework because it separates edge behavior from origin behavior.

## Key Takeaways

- **A cache hit can bypass the entire backend:** CloudFront can return an edge-cached response without contacting ALB, Nginx, Django, FastAPI, Redis, or PostgreSQL.
- **A cache miss continues through the origin stack:** The request can travel from CloudFront through the load balancer, reverse proxy, application, cache, and database before the response returns to the viewer.
- **Cache-key design determines both correctness and performance:** Missing response-affecting dimensions can create unsafe sharing, while unnecessary dimensions cause cache fragmentation.
- **CloudFront and Redis solve different caching problems:** CloudFront caches HTTP responses at the edge, while Redis typically caches application data closer to the backend.
- **Production CloudFront design requires deliberate caching:** Static immutable assets are strong candidates for long TTLs, while authenticated, personalized, and tenant-specific responses require careful cache isolation.