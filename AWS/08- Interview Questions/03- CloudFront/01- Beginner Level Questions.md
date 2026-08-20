# 01- Beginner Level Questions

## Overview

This document contains beginner-level AWS CloudFront interview questions and answers for backend engineers.

The questions focus on the foundational concepts required to explain CloudFront confidently in an interview: CDN architecture, distributions, origins, edge locations, caching, cache hits and misses, TTLs, invalidations, HTTPS, DNS, CloudFront behaviors, static versus dynamic content, and basic troubleshooting.

The expected interview approach is not to memorize definitions. A strong answer should explain **what CloudFront does, why it exists, how a request flows through it, and what changes when caching or the origin is involved**.

---

## Core CloudFront Questions

### What is Amazon CloudFront?

**Answer:**

Amazon CloudFront is AWS's content delivery network (CDN). It distributes content through a globally distributed network of edge locations so that users can retrieve content from a location geographically closer to them.

CloudFront can deliver:

- Static files such as images, JavaScript, CSS, and videos.
- Dynamic HTTP/HTTPS responses.
- API responses.
- Application content.
- Private content protected using signed URLs or signed cookies.

A simplified request path is:

```text
User
  │
  ▼
CloudFront Edge Location
  │
  ├── Cache HIT ────────► User
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
         User
```

---

### Why do we use CloudFront?

**Answer:**

The primary reasons are:

- Reduce latency by serving content closer to users.
- Cache frequently requested content.
- Reduce load on backend origins.
- Improve application scalability.
- Provide HTTPS termination at the edge.
- Integrate with AWS WAF and other security controls.
- Improve global content delivery.
- Support private and controlled content delivery.

For example, if a Django application runs in an AWS Region in Mumbai and users access it from Europe, serving cacheable static content through CloudFront can avoid repeatedly transferring that content from the origin region.

---

### What is a CDN?

**Answer:**

A Content Delivery Network is a distributed network of servers that caches and delivers content from locations closer to end users.

Instead of every request traveling to one centralized origin:

```text
Users
  │
  ├──────────────► Origin
  ├──────────────► Origin
  ├──────────────► Origin
  └──────────────► Origin
```

a CDN allows cacheable content to be served from edge locations:

```text
                 ┌──► Edge ──► Users
                 │
Origin ◄─────────┼──► Edge ──► Users
                 │
                 └──► Edge ──► Users
```

This reduces repeated origin traffic and can improve latency.

---

### What is an edge location?

**Answer:**

An edge location is a CloudFront point of presence where CloudFront can receive viewer requests and, where applicable, serve cached content.

The user is generally routed to an appropriate CloudFront edge location based on AWS's network routing mechanisms.

The important distinction is:

> An edge location is not the same thing as the origin.

The edge handles viewer-side delivery, while the origin is where CloudFront retrieves content when it cannot satisfy the request from its cache.

---

### What is a CloudFront distribution?

**Answer:**

A CloudFront distribution is the configuration object that defines how CloudFront delivers content.

A distribution specifies things such as:

- Origins.
- Cache behaviors.
- Viewer protocol policy.
- Cache policies.
- Origin request policies.
- TLS configuration.
- Logging.
- WAF association.
- Geographic restrictions.
- Error handling.

Conceptually:

```text
CloudFront Distribution
│
├── Origins
├── Cache Behaviors
├── Cache Policies
├── Origin Request Policies
├── TLS Configuration
├── WAF Association
└── Logging
```

---

### What is an origin in CloudFront?

**Answer:**

An origin is the backend location from which CloudFront retrieves content when it does not have a valid cached response.

Common origins include:

- Amazon S3.
- Application Load Balancer.
- API Gateway.
- EC2-based applications.
- Custom HTTP servers.
- Other HTTP endpoints.

For example:

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
S3 Bucket
```

---

### What is the difference between an origin and an edge location?

| Origin | Edge Location |
|---|---|
| Source of content | Viewer-facing delivery location |
| Usually contains the application or data | Usually serves cached content |
| Can be S3, ALB, EC2, etc. | Managed by CloudFront |
| Receives cache-miss requests | Receives viewer requests |
| Usually fewer locations | Globally distributed |

A useful interview statement is:

> CloudFront sits between the viewer and the origin. Edge locations handle viewer traffic, while origins provide content when CloudFront cannot serve the request from cache.

---

## Caching Questions

### What is caching in CloudFront?

**Answer:**

Caching means CloudFront stores eligible origin responses at its edge locations for a configured period.

For a cacheable request:

```text
First Request
User → CloudFront → Origin
                  ↓
              Response
                  ↓
              CloudFront
                  ↓
                User

Subsequent Request
User → CloudFront → Cached Response → User
```

The second request can avoid contacting the origin.

---

### What is a cache hit?

**Answer:**

A cache hit occurs when CloudFront can satisfy a viewer request using an object already stored in the CloudFront cache.

```text
User
  │
  ▼
CloudFront
  │
  ▼
Cache HIT
  │
  ▼
Response
```

Benefits include:

- Lower latency.
- Reduced origin traffic.
- Better origin scalability.
- Potentially lower infrastructure cost.

---

### What is a cache miss?

**Answer:**

A cache miss occurs when CloudFront cannot serve the requested object from the applicable cache.

CloudFront then needs to obtain the object from the configured origin.

```text
User
  │
  ▼
CloudFront
  │
  ▼
Cache MISS
  │
  ▼
Origin
  │
  ▼
Response
```

CloudFront may then cache the response according to the applicable caching rules.

---

### What is cache hit ratio?

**Answer:**

Cache hit ratio represents how effectively CloudFront serves requests from cache instead of contacting the origin.

A simplified conceptual calculation is:

```text
Cache Hit Ratio =
Cache Hits / Total Cacheable Requests
```

A higher value often means less origin traffic, but a high cache hit ratio is not automatically the goal for every application.

Dynamic and personalized content may legitimately have low cacheability.

---

### Why should we not blindly maximize cache hit ratio?

**Answer:**

Because caching is a correctness decision as well as a performance decision.

For example, consider:

```text
GET /api/profile
```

If the response contains user-specific information, caching the response incorrectly could expose one user's data to another user.

Therefore:

```text
High Cache Hit Ratio
        ≠
Correct Application
```

Cacheability must be designed around the semantics of the response.

---

### What is TTL in CloudFront?

**Answer:**

TTL, or Time To Live, controls how long a cached object can remain fresh according to the applicable CloudFront caching configuration and origin cache-control directives.

Important TTL concepts include:

- Minimum TTL.
- Maximum TTL.
- Default TTL.

The exact effective behavior depends on the configured cache policy and the response's caching headers.

A common production strategy is:

```text
Immutable static assets → Long TTL
Frequently changing content → Shorter TTL
Personalized responses → Usually bypass or carefully control caching
```

---

### What happens when an object expires from CloudFront cache?

**Answer:**

Once the cached object is no longer considered fresh according to the configured caching rules, CloudFront may need to revalidate or retrieve the object from the origin.

The exact behavior depends on HTTP caching semantics and CloudFront configuration.

The important point is:

> TTL expiration does not mean that every request always results in a complete origin download. HTTP caching and revalidation behavior can affect what happens next.

---

### What is a cache key?

**Answer:**

A cache key determines which requests are considered equivalent for caching purposes.

Depending on the CloudFront cache policy, dimensions can include information such as:

- URL path.
- Query strings.
- Headers.
- Cookies.

For example, if the cache key varies by a query parameter:

```text
/products?id=100
/products?id=200
```

these can represent different cached objects.

Poor cache-key design can create excessive cache fragmentation.

---

### Why is cache-key design important?

**Answer:**

Because unnecessary cache-key dimensions can reduce cache efficiency.

For example, if a cache varies on an irrelevant header:

```text
X-Request-ID
```

then otherwise identical requests can become separate cache entries.

That creates:

```text
More cache keys
      ↓
More cache fragmentation
      ↓
Fewer cache hits
      ↓
More origin requests
```

A good cache key contains only request attributes that genuinely affect the representation being cached.

---

## Origin Questions

### Can CloudFront have multiple origins?

**Answer:**

Yes.

A distribution can have multiple origins, and cache behaviors can route requests to different origins.

For example:

```text
CloudFront
│
├── /static/*  ──────► S3
│
├── /api/*     ──────► ALB
│
└── /media/*   ──────► S3
```

This is useful when different types of content are served by different backend systems.

---

### Can CloudFront serve an API?

**Answer:**

Yes.

CloudFront can sit in front of APIs and HTTP applications.

For example:

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

However, API caching must be designed carefully.

Many APIs contain personalized or rapidly changing data and therefore should not simply be cached by default.

---

### Can CloudFront serve dynamic content?

**Answer:**

Yes.

CloudFront can proxy dynamic requests to an origin even when the response is not cached.

For example:

```text
POST /orders
GET /account
POST /payments
```

These requests can still travel through CloudFront even when caching is not appropriate.

CloudFront therefore is not limited to static content.

---

### What is a custom origin?

**Answer:**

A custom origin is an HTTP server that CloudFront accesses using supported HTTP/HTTPS origin configuration.

Examples include:

- Application Load Balancer.
- EC2-hosted web server.
- Nginx.
- External HTTP application.

For a backend architecture:

```text
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

---

### Can S3 be used as a CloudFront origin?

**Answer:**

Yes.

S3 is a common CloudFront origin for:

- Static websites.
- JavaScript bundles.
- CSS.
- Images.
- Downloads.
- Media files.

For private S3 content, CloudFront can be configured using modern origin access controls so that users do not need direct public access to the bucket.

---

## CloudFront Behaviors

### What is a CloudFront cache behavior?

**Answer:**

A cache behavior defines how CloudFront handles requests matching a specific path pattern.

For example:

```text
/static/* → S3
/api/*    → ALB
/images/* → S3
```

A behavior can control settings such as:

- Target origin.
- Allowed HTTP methods.
- Viewer protocol policy.
- Cache policy.
- Origin request policy.
- Compression-related behavior.
- Trusted key groups for signed URLs/cookies.

---

### Why are cache behaviors useful?

**Answer:**

They allow different parts of an application to have different delivery rules.

For example:

```text
/static/*

Long-lived caching
S3 origin
GET/HEAD
```

while:

```text
/api/*

Dynamic behavior
ALB origin
API-specific caching policy
```

This is much safer than applying one caching strategy to an entire application.

---

### What happens if a request does not match a more specific path pattern?

**Answer:**

CloudFront uses the applicable default behavior.

Therefore, the default behavior should be intentionally configured because requests that do not match other behaviors will use it.

A common mistake is to configure special paths correctly but leave the default behavior overly permissive or incorrectly cached.

---

## HTTP and HTTPS Questions

### Can CloudFront handle HTTPS?

**Answer:**

Yes.

CloudFront can terminate TLS for viewer connections using an associated certificate.

The typical flow is:

```text
Client
  │
  │ HTTPS
  ▼
CloudFront
  │
  │ HTTP/HTTPS depending on origin configuration
  ▼
Origin
```

The viewer-facing TLS configuration and the CloudFront-to-origin connection are separate concerns.

---

### What is a viewer protocol policy?

**Answer:**

A viewer protocol policy controls how CloudFront handles HTTP and HTTPS requests from viewers.

Common strategies include:

- Allow HTTP and HTTPS.
- Redirect HTTP to HTTPS.
- Require HTTPS.

For production applications, HTTPS is normally preferred to protect data in transit.

---

### Is CloudFront-to-origin traffic automatically HTTPS?

**Answer:**

Not necessarily.

Viewer-to-CloudFront HTTPS and CloudFront-to-origin HTTPS are separate connections.

For example:

```text
Viewer
  │ HTTPS
  ▼
CloudFront
  │ HTTP
  ▼
Origin
```

is technically different from:

```text
Viewer
  │ HTTPS
  ▼
CloudFront
  │ HTTPS
  ▼
Origin
```

For sensitive production applications, HTTPS should generally be used for the origin connection as well.

---

### What happens if the CloudFront TLS certificate is incorrect?

**Answer:**

The viewer can receive TLS or certificate-related errors.

Common causes include:

- Certificate does not cover the requested domain.
- Incorrect certificate association.
- DNS does not point to the expected distribution.
- Incorrect alternate domain configuration.
- Certificate configuration problems.

During troubleshooting, verify the complete chain:

```text
Domain
  ↓
DNS
  ↓
CloudFront Alternate Domain Name
  ↓
CloudFront Certificate
  ↓
TLS Handshake
```

---

## DNS Questions

### Does CloudFront replace Route 53?

**Answer:**

No.

They perform different roles.

| Service | Primary responsibility |
|---|---|
| Route 53 | DNS |
| CloudFront | CDN and edge delivery |

A common architecture is:

```text
example.com
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

---

### How does a custom domain point to CloudFront?

**Answer:**

DNS is configured so that the application's domain resolves to the CloudFront distribution.

For AWS-hosted DNS, Route 53 can use an alias record pointing to the CloudFront distribution.

The exact DNS configuration depends on the domain and hosting architecture.

---

## Invalidation Questions

### What is a CloudFront invalidation?

**Answer:**

An invalidation requests that cached objects be removed from CloudFront caches before their normal expiration.

For example:

```text
/images/logo.png
```

or broader paths such as:

```text
/static/*
```

can be invalidated when necessary.

---

### Why would we use an invalidation?

**Answer:**

An invalidation is useful when cached content must be removed before its normal TTL expires.

Typical cases include:

- Emergency content replacement.
- Incorrectly cached content.
- Deployment of mutable assets.
- Security-related content removal.

However, invalidation should not be the default deployment strategy for every static asset.

---

### What is a better strategy than invalidating every static asset after deployment?

**Answer:**

Use immutable asset versioning.

For example:

```text
app.4f8c2a.js
app.91d7ab.css
```

Instead of:

```text
app.js
app.css
```

When the content changes, the filename changes.

This allows long-lived caching without requiring broad invalidations.

---

## Security Questions

### What is AWS WAF and how does it relate to CloudFront?

**Answer:**

AWS WAF is a web application firewall that can inspect HTTP/HTTPS requests and apply rules to allow, block, count, or otherwise handle requests.

A common architecture is:

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

WAF can help protect applications against common web threats and unwanted traffic patterns.

---

### Can CloudFront restrict access to content?

**Answer:**

Yes.

Depending on the use case, CloudFront supports mechanisms such as:

- Signed URLs.
- Signed cookies.
- Geographic restrictions.
- WAF rules.
- Origin access controls for private S3 content.

The correct mechanism depends on whether the requirement is user authorization, geographic restriction, content protection, or origin protection.

---

### What are signed URLs?

**Answer:**

A signed URL is a URL containing a cryptographic signature that allows CloudFront to verify that the requester has been authorized to access a protected resource.

They are useful for controlled access to individual resources.

For example:

```text
https://cdn.example.com/video/private.mp4
    ?Expires=...
    &Signature=...
    &Key-Pair-Id=...
```

The exact generated parameters depend on the signing mechanism.

---

### What are signed cookies?

**Answer:**

Signed cookies allow CloudFront to authorize access to multiple resources without requiring a separate signed URL for every object.

They are useful when a user needs access to a group of protected files.

For example:

```text
User authenticates
       │
       ▼
Backend issues CloudFront signed cookies
       │
       ▼
User requests multiple protected resources
       │
       ▼
CloudFront validates cookies
```

---

## Basic Troubleshooting Questions

### A user receives a 403 from CloudFront. What would you check?

**Answer:**

Do not assume CloudFront itself is the source of the 403.

Check:

1. Whether the request is being blocked by AWS WAF.
2. Whether the CloudFront behavior allows the HTTP method.
3. Whether the requested resource exists.
4. Whether origin access controls are configured correctly.
5. Whether signed URL or signed cookie requirements are satisfied.
6. Whether geographic restrictions apply.
7. Whether the origin itself returned the 403.
8. CloudFront logs and relevant origin logs.

The key interview point is:

> A CloudFront 403 is a symptom. Determine whether the response originated at the edge or from the origin.

---

### A user receives a 404 through CloudFront. What could cause it?

**Answer:**

Possible causes include:

- The object does not exist in the origin.
- The application route does not exist.
- The CloudFront behavior routes the request to the wrong origin.
- The origin path is incorrect.
- The cached response is stale.
- The application generated the 404.

Trace the request:

```text
Viewer
  ↓
CloudFront Behavior
  ↓
Selected Origin
  ↓
Origin Path / Application Route
  ↓
404 Source
```

---

### CloudFront is returning 502. What could be wrong?

**Answer:**

Potential causes include:

- Origin connectivity problems.
- TLS problems between CloudFront and the origin.
- Invalid origin response.
- Backend availability issues.
- Load balancer problems.
- Incorrect origin configuration.

The correct troubleshooting approach is to inspect CloudFront telemetry and then investigate the origin independently.

---

### CloudFront is returning 504. What does that suggest?

**Answer:**

A 504 generally indicates that CloudFront did not receive an appropriate response from the origin within the expected time.

Potential causes include:

- Slow application code.
- Database latency.
- Origin overload.
- Network problems.
- Backend dependency failures.
- Incorrect timeout assumptions.

For a Django or FastAPI application, investigate the complete backend request path:

```text
CloudFront
    ↓
ALB
    ↓
Nginx
    ↓
Application
    ↓
Redis / PostgreSQL / External API
```

---

### Users report that an updated image is not visible. What would you check?

**Answer:**

First determine whether the old image is being served from cache.

Then check:

- Object TTL.
- Cache behavior.
- Cache headers.
- Whether the object was invalidated.
- Whether the URL changed.
- Whether the browser itself has cached the old object.

For static deployments, immutable filenames are generally preferable:

```text
logo-v1.png
logo-v2.png
```

or content-hashed assets.

---

## Basic Architecture Questions

### How does CloudFront reduce origin load?

**Answer:**

CloudFront caches eligible responses at edge locations.

If multiple users request the same cacheable resource:

```text
                 ┌── User A
                 │
CloudFront Cache ├── User B
                 │
                 └── User C
                       │
                       ▼
                 Single origin retrieval
```

the origin may not need to process every viewer request.

This can reduce:

- Application requests.
- CPU usage.
- Database queries.
- Network traffic.
- Infrastructure scaling pressure.

---

### Does every CloudFront request reach the origin?

**Answer:**

No.

A cache hit can be served directly from CloudFront.

Only requests that cannot be satisfied from cache, or requests that are intentionally dynamic/non-cacheable, need to reach the origin.

---

### Does CloudFront cache POST requests?

**Answer:**

CloudFront's normal caching model is primarily centered around cacheable HTTP methods such as `GET` and `HEAD`. Other methods can be forwarded to the origin when allowed by the cache behavior.

A typical API architecture therefore treats:

```text
GET  → potentially cacheable
POST → dynamic
PUT  → dynamic
PATCH → dynamic
DELETE → dynamic
```

as different categories.

The exact behavior is determined by the distribution configuration and cache behavior.

---

### Can CloudFront be used with Django?

**Answer:**

Yes.

A common architecture is:

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
Django
   │
   ├── Redis
   └── PostgreSQL
```

CloudFront can be particularly useful for:

- Static assets.
- Media files.
- Public content.
- Selected API responses.
- Global application delivery.

Django should still remain responsible for application-level authorization and business logic.

---

### Can CloudFront be used with FastAPI?

**Answer:**

Yes.

For example:

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
```

CloudFront can provide edge delivery and TLS while FastAPI handles application logic.

---

## Configuration Questions

### What is a cache policy?

**Answer:**

A CloudFront cache policy defines how CloudFront determines what can be cached and what request information contributes to the cache key.

It controls important caching dimensions such as:

- TTL settings.
- Query strings included in the cache key.
- Headers included in the cache key.
- Cookies included in the cache key.

A carefully designed cache policy is important for both performance and correctness.

---

### What is an origin request policy?

**Answer:**

An origin request policy controls what additional request information CloudFront forwards to the origin without necessarily making that information part of the cache key.

This distinction is important.

```text
Cache Policy
     │
     └── What differentiates cached responses?

Origin Request Policy
     │
     └── What information does the origin receive?
```

A senior engineer should understand that **cache-key requirements and origin-forwarding requirements are not the same thing**.

---

### Why should we avoid forwarding every header, cookie, and query parameter?

**Answer:**

Because it can create unnecessary cache fragmentation.

For example:

```text
Request A
Cookie = abc

Request B
Cookie = xyz

Request C
Cookie = pqr
```

If the cookie becomes part of the cache key, each request may map to a different cache entry.

This can reduce cache efficiency and increase origin traffic.

Only request attributes that materially affect the response should influence caching.

---

## Operational Questions

### How do you monitor CloudFront?

**Answer:**

Use a combination of:

- CloudFront metrics.
- CloudWatch.
- Standard access logs.
- Real-time logs where appropriate.
- AWS WAF metrics and logs.
- Origin metrics.
- ALB metrics.
- Application logs.

A production monitoring model should correlate edge and backend telemetry.

```text
CloudFront
    │
    ├── Metrics
    ├── Logs
    └── WAF
          │
          ▼
       Origin
          │
          ├── ALB
          ├── Nginx
          ├── Django/FastAPI
          ├── Redis
          └── PostgreSQL
```

---

### What metrics are useful for CloudFront?

**Answer:**

Important operational metrics include:

- Request count.
- Bytes downloaded.
- Error rates.
- Cache-related metrics.
- Origin-related metrics.
- Latency-related measurements.

The exact metrics used should depend on the application's traffic pattern and operational objectives.

A good monitoring strategy focuses on detecting:

```text
Traffic anomalies
Error anomalies
Latency anomalies
Cache anomalies
Origin overload
Security anomalies
```

---

### What logs can CloudFront provide?

**Answer:**

CloudFront supports logging mechanisms that provide request-level visibility.

Standard access logs are useful for historical analysis, while real-time logging can provide much faster visibility for operational investigation.

Logs can help investigate:

- Request paths.
- Status codes.
- Cache behavior.
- Viewer information.
- Request patterns.
- Error patterns.

Logging should be enabled and retained according to operational and compliance requirements.

---

## Beginner Interview Traps

### Is CloudFront just an S3 caching service?

**Answer:**

No.

S3 is one possible origin.

CloudFront can sit in front of many HTTP-based origins and can also deliver dynamic application traffic.

A better answer is:

> CloudFront is a CDN and edge delivery service. S3 is a common origin, but CloudFront can also front load balancers, EC2 applications, APIs, and other HTTP origins.

---

### Is CloudFront the same as a load balancer?

**Answer:**

No.

A load balancer primarily distributes traffic among backend targets.

CloudFront primarily provides global edge delivery, caching, request handling, and integration with edge security controls.

They are often used together:

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
Application Instances
```

---

### Does CloudFront always make an application faster?

**Answer:**

No.

CloudFront can improve performance, particularly for cacheable content and geographically distributed users, but poor configuration can limit or even undermine the benefit.

For dynamic requests that must reach the origin, latency still depends heavily on:

- Network path.
- Origin location.
- Application processing.
- Database latency.
- Downstream dependencies.

---

### Does adding CloudFront automatically cache every API response?

**Answer:**

No.

Caching depends on CloudFront configuration, HTTP semantics, request methods, cache policy, response headers, and other conditions.

Dynamic or personalized APIs should not be assumed to be cacheable.

---

### If CloudFront has a cache hit, does the application receive the request?

**Answer:**

For a normal cache hit, CloudFront can serve the cached response without making the request to the origin.

Therefore:

```text
Cache HIT
User → CloudFront → User
```

instead of:

```text
Cache MISS
User → CloudFront → Origin → CloudFront → User
```

This distinction is fundamental to understanding CloudFront's performance benefits.

---

## Scenario-Based Beginner Questions

### You have a React frontend stored in S3. Why would you put CloudFront in front of it?

**Answer:**

CloudFront can provide:

- Global edge delivery.
- HTTPS.
- Caching.
- Lower latency for geographically distributed users.
- Integration with AWS security controls.
- Reduced repeated requests to S3.

A typical architecture is:

```text
Browser
   │
   ▼
CloudFront
   │
   ▼
S3
```

---

### Your API runs in one AWS Region but users are global. Should every API response be cached?

**Answer:**

No.

First classify the API responses.

Public, stable responses may be candidates for caching.

Personalized or frequently changing responses may need to bypass caching or use carefully designed caching policies.

The important question is:

> Does the same request representation safely apply to multiple users for the cache lifetime?

---

### Your origin receives too many requests after deploying CloudFront. What could be wrong?

**Answer:**

Possible causes include:

- Low cache hit ratio.
- Incorrect cache policy.
- Excessive cache-key variation.
- Short TTLs.
- Dynamic requests being sent through the same behavior.
- Cache invalidation strategy.
- Query strings or cookies unnecessarily fragmenting the cache.

The first step is to inspect cache behavior and metrics rather than immediately increasing origin capacity.

---

### Your CloudFront distribution works, but the application is still slow. What would you investigate?

**Answer:**

Determine whether the slow requests are cache hits or origin requests.

Then investigate:

```text
CloudFront
   ↓
Cache behavior
   ↓
Origin latency
   ↓
ALB
   ↓
Application
   ↓
Database / Redis / External dependencies
```

If most requests are dynamic and must reach the origin, CloudFront cannot eliminate application processing latency.

---

### A deployment changed JavaScript but users still receive the previous version. What is a common solution?

**Answer:**

Use versioned or content-hashed asset filenames.

For example:

```text
app.abc123.js
```

instead of:

```text
app.js
```

This allows the new version to use a different cache key.

An invalidation can be used when necessary, but immutable asset naming is generally a more scalable deployment pattern for static assets.

---

## Quick Comparison

| Concept | Meaning |
|---|---|
| CDN | Distributed content delivery system |
| CloudFront | AWS CDN and edge delivery service |
| Distribution | Main CloudFront configuration object |
| Origin | Backend source of content |
| Edge location | CloudFront viewer-facing location |
| Cache hit | Response served from CloudFront cache |
| Cache miss | CloudFront must obtain content from origin |
| TTL | Controls cache freshness lifetime |
| Cache key | Determines which requests map to the same cached response |
| Cache policy | Defines caching and cache-key behavior |
| Origin request policy | Defines additional request data sent to the origin |
| Invalidation | Requests removal of cached objects before normal expiration |
| WAF | Web application firewall used to inspect and control requests |
| Signed URL | Cryptographically protected access to a resource |
| Signed cookie | Cryptographically protected access to multiple resources |

---

## Key Takeaways

- **CloudFront is a CDN and edge delivery layer, not simply an S3 cache or load balancer.**
- **The most important request-flow distinction is cache hit versus cache miss:** hits can be served at the edge, while misses require origin interaction.
- **Caching is a correctness decision as well as a performance optimization:** never cache personalized or sensitive responses without deliberately designing the cache behavior.
- **CloudFront commonly works together with Route 53, WAF, ALB, Nginx, Django, FastAPI, S3, Redis, and PostgreSQL rather than replacing those components.**
- **For troubleshooting questions, follow the request path from viewer to CloudFront to origin instead of assuming every CloudFront error is caused by CloudFront.**