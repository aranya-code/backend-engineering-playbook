# 08- Scenario Based Questions

## Overview

Scenario-based CloudFront interviews test whether you can reason about CDN behavior rather than simply recall definitions. The interviewer is usually evaluating how you investigate failures, design caching behavior, protect origins, control costs, and make production trade-offs.

A strong answer should follow a consistent engineering pattern:

```text
Understand the symptom
        ↓
Establish the blast radius
        ↓
Check CloudFront behavior
        ↓
Check origin behavior
        ↓
Correlate metrics and logs
        ↓
Identify the likely root cause
        ↓
Apply the least risky remediation
        ↓
Verify recovery
        ↓
Prevent recurrence
```

The scenarios below focus on realistic backend and system-design situations involving CloudFront, Django, FastAPI, REST APIs, ALB, Nginx, Redis, PostgreSQL, AWS WAF, CI/CD, and production operations.

---

## How to Approach Scenario Questions

When given a production incident, avoid immediately jumping to a configuration change.

A senior-level response should establish:

| Question | Why it matters |
|---|---|
| What changed? | Recent deployments often explain regressions |
| Who is affected? | Determines blast radius |
| Is the issue global or regional? | Helps isolate edge/origin problems |
| Is it cached or dynamic traffic? | Determines the likely request path |
| Are errors increasing? | Separates performance from availability problems |
| Is origin traffic increasing? | Identifies cache degradation |
| Is origin latency increasing? | Helps distinguish CDN from backend problems |
| Is the problem reproducible? | Helps validate hypotheses |
| Can the change be rolled back? | Determines safest mitigation |
| How will recovery be verified? | Prevents premature incident closure |

---

## Scenario: CloudFront `5xx` Errors Suddenly Increase

### Question

Your production API is behind CloudFront. Suddenly the CloudFront `5xx` rate increases from near zero to 8%. What do you investigate?

### Strong Answer

First, I would establish whether the increase is sustained and determine its scope.

I would check:

1. CloudFront `5xx` rate.
2. Affected paths and behaviors.
3. Origin latency.
4. Origin request volume.
5. ALB or Nginx health.
6. Django/FastAPI application errors.
7. Database and Redis health.
8. Recent application deployments.
9. Recent CloudFront configuration changes.
10. WAF or security-rule changes.

The request path is:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
ALB / Nginx
  │
  ▼
Django / FastAPI
  │
  ├── Redis
  │
  └── PostgreSQL
```

I would correlate the timestamps across these layers.

For example:

```text
CloudFront 5xx ↑
      │
      ├── ALB 5xx ↑
      │
      └── Application exceptions ↑
```

This strongly suggests an origin-side problem.

If CloudFront errors increase but the origin shows no corresponding failures, I would investigate CloudFront configuration, connectivity, edge behavior, and request-processing logic.

### Interview Trap

Do not say:

> "CloudFront is down."

A CloudFront `5xx` does not automatically mean CloudFront itself is the root cause.

---

## Scenario: Cache Hit Ratio Drops After Deployment

### Question

Your CloudFront cache hit ratio was 94%. Immediately after a deployment, it falls to 58%. Origin traffic increases significantly. What could have happened?

### Strong Answer

I would investigate changes affecting the cache key and cacheability.

Potential causes include:

- Cache policy changes.
- Additional query-string parameters.
- New cookies included in the cache key.
- Additional headers included in the cache key.
- Lower TTLs.
- Changed `Cache-Control` behavior.
- New uncached API paths.
- Cache invalidations.
- Application changes generating unique URLs.

The key relationship is:

```text
Cache hit ratio ↓
        │
        ▼
Origin requests ↑
        │
        ▼
Application load ↑
        │
        ▼
Database load ↑
```

I would compare the CloudFront configuration before and after deployment and inspect representative requests.

### Senior-Level Observation

A cache-hit-ratio problem is not necessarily a CloudFront-only problem. It can become an origin-capacity problem.

---

## Scenario: Origin Is Overloaded but CloudFront Is Healthy

### Question

CloudFront itself looks healthy, but your Django application is receiving unexpectedly high traffic and PostgreSQL is approaching saturation. What do you investigate?

### Strong Answer

I would determine whether traffic that should be cached is reaching the origin.

I would compare:

```text
CloudFront requests
        +
Cache hit ratio
        +
Origin requests
        +
Django request rate
```

If:

```text
CloudFront requests = 1,000,000/min
Origin requests     = 800,000/min
```

then CloudFront is not absorbing enough traffic for that workload.

I would investigate:

- Cache policies.
- Cache keys.
- TTLs.
- `Cache-Control` headers.
- Query-string variation.
- Cookies.
- Request headers.
- Whether the endpoint is intentionally dynamic.

I would not blindly increase database capacity before understanding why origin traffic increased.

---

## Scenario: API Responses Are Being Served Stale

### Question

Users report that your API sometimes returns stale data through CloudFront. How would you investigate?

### Strong Answer

I would first determine whether the endpoint is intended to be cached.

Then I would inspect:

- CloudFront cache policy.
- TTL settings.
- Origin `Cache-Control` headers.
- `Expires` behavior.
- Cache key configuration.
- Invalidation behavior.
- Whether the application is returning cacheable responses unintentionally.

For data that changes frequently, I would prefer explicit cache semantics rather than relying on broad default behavior.

For example:

```http
Cache-Control: no-store
```

may be appropriate for sensitive or highly dynamic responses.

For content that can tolerate controlled staleness:

```http
Cache-Control: public, max-age=60
```

may be appropriate depending on the application semantics.

### Interview Trap

Do not treat invalidation as the universal solution.

If the application continuously generates incorrect cache behavior, repeatedly invalidating objects is operationally fragile.

---

## Scenario: Users See Another User's Data

### Question

A REST API behind CloudFront is accidentally returning one user's personalized response to another user. What is your immediate concern?

### Strong Answer

This is a critical security incident.

The first concern is whether personalized responses are being cached and reused across users.

I would immediately:

1. Stop or disable caching for the affected personalized endpoint.
2. Prevent further exposure.
3. Investigate whether sensitive responses are currently cached.
4. Invalidate affected objects if appropriate.
5. Determine the exposure window.
6. Identify affected users and data.
7. Review CloudFront cache policy and cache-key configuration.
8. Review origin response headers.
9. Investigate access logs and application logs.
10. Follow the organization's security incident process.

The architectural principle is:

```text
Personalized response
        │
        ▼
Must not be shared through an inappropriate cache key
```

### Senior-Level Point

Authentication alone does not make a response safe to cache.

The caching layer must understand whether the response is reusable across requests.

---

## Scenario: CloudFront Works for Static Files but API Calls Fail

### Question

Your static JavaScript and CSS assets work through CloudFront, but `/api/*` requests return `403`. What do you investigate?

### Strong Answer

I would inspect CloudFront behaviors and path-based routing.

For example:

```text
/*       → S3
/api/*   → ALB
```

If `/api/*` is not configured correctly, CloudFront may send API requests to the wrong origin or apply the wrong policy.

I would inspect:

- Path pattern.
- Origin association.
- Allowed HTTP methods.
- Viewer protocol policy.
- Cache policy.
- Origin request policy.
- Authentication headers.
- WAF rules.
- Query strings.
- Cookies.
- Authorization headers.

The first question is:

> Which CloudFront behavior is actually matching `/api/...`?

---

## Scenario: POST Requests Return Errors

### Question

GET requests work through CloudFront, but POST requests to your API fail. What would you check?

### Strong Answer

I would check whether the CloudFront behavior allows the required HTTP methods.

For APIs, CloudFront must be configured appropriately for methods such as:

```text
GET
HEAD
OPTIONS
POST
PUT
PATCH
DELETE
```

depending on the API.

I would also inspect:

- Origin request configuration.
- CORS behavior.
- Authentication headers.
- CSRF requirements where applicable.
- Cache behavior.
- Preflight `OPTIONS` requests.

A common mistake is assuming that because GET works, the entire API behavior is correctly configured.

---

## Scenario: CORS Works Directly but Fails Through CloudFront

### Question

Your API works when accessed directly through the ALB, but browser requests through CloudFront fail with CORS errors. What could be wrong?

### Strong Answer

I would compare the request and response behavior through both paths.

I would inspect:

- `Origin` request header.
- `Access-Control-Allow-Origin`.
- `Access-Control-Allow-Methods`.
- `Access-Control-Allow-Headers`.
- `OPTIONS` handling.
- CloudFront cache policy.
- Origin request policy.
- Response headers policy.

A particularly important issue is caching a response whose CORS headers vary by request origin without accounting for that variation correctly.

The flow should be:

```text
Browser
   │
   ├── OPTIONS
   │
   ▼
CloudFront
   │
   ▼
Origin
   │
   ▼
CORS response
```

I would test both the preflight and actual request independently.

---

## Scenario: CloudFront Returns `403` for a Public Object

### Question

An S3 object is publicly expected to be available through CloudFront, but CloudFront returns `403`. What do you investigate?

### Strong Answer

I would not immediately make the S3 bucket public.

I would verify:

- CloudFront origin configuration.
- S3 bucket policy.
- Origin Access Control configuration.
- Object existence.
- Object ownership.
- CloudFront distribution behavior.
- Path mapping.
- Viewer restrictions.
- WAF rules.
- Signed URL/cookie requirements.

For a production architecture, the preferred design is generally to keep the S3 bucket private and allow CloudFront controlled access through the appropriate origin access mechanism.

---

## Scenario: CloudFront Returns `404`, but the Origin Returns `200`

### Question

The origin returns `200` when you access it directly, but CloudFront returns `404`. What could cause this?

### Strong Answer

I would investigate differences between the direct origin request and the CloudFront request.

Possible causes include:

- Incorrect path pattern.
- Origin path configuration.
- Host header behavior.
- Query-string handling.
- Object key transformation.
- Wrong origin.
- Cached `404`.
- Redirect behavior.
- Application routing differences.

I would inspect the exact URL and determine which CloudFront behavior handles it.

A cached error can also create confusion because fixing the origin does not necessarily mean an already-cached error disappears immediately.

---

## Scenario: A Cached `404` Persists After Fixing the Origin

### Question

You fix a missing resource at the origin, but CloudFront continues returning `404`. Why?

### Strong Answer

The original `404` may have been cached.

The request lifecycle can be:

```text
Request
  │
  ▼
CloudFront
  │
  ├── Cached 404 → Return 404
  │
  └── Cache miss → Origin
```

I would inspect the relevant error-caching behavior and invalidate the affected object if required.

The longer-term solution is to design appropriate caching behavior for error responses rather than repeatedly relying on manual invalidation.

---

## Scenario: Latency Increases but Error Rate Is Normal

### Question

CloudFront error rates remain normal, but users report increased latency. What do you investigate?

### Strong Answer

I would determine whether the latency increase affects:

- Cache hits.
- Cache misses.
- Specific regions.
- Specific paths.
- Static assets.
- Dynamic APIs.

Then I would compare:

```text
CloudFront latency
+
Origin latency
+
Application latency
```

If cache hits are slow while origin latency is stable, I would investigate edge behavior or network characteristics.

If cache misses are slow and origin latency increased, the backend is more likely responsible.

I would also inspect:

- Payload size.
- Compression.
- TLS behavior.
- Geographic distribution.
- Origin performance.
- Recent configuration changes.

---

## Scenario: Only One Region Has High Latency

### Question

Users in one geographic region report significantly higher CloudFront latency while other regions are normal. What would you do?

### Strong Answer

I would determine whether the issue is:

- Regional edge performance.
- Origin connectivity.
- Geographic routing.
- A regional backend problem.
- ISP/network-specific behavior.
- A specific CloudFront behavior or asset.

I would compare metrics by geographic dimension where available and correlate them with origin behavior.

I would avoid assuming that a regional latency problem means the origin is globally unhealthy.

---

## Scenario: Traffic Suddenly Increases 20x

### Question

A CloudFront distribution normally receives 50,000 requests/minute but suddenly receives 1 million requests/minute. What do you do?

### Strong Answer

First, determine whether the spike is expected.

Possible causes include:

- Marketing campaign.
- Product launch.
- Bot traffic.
- DDoS activity.
- Client retry storm.
- Application bug.
- Monitoring or automation bug.

I would check:

- Request patterns.
- URLs.
- User agents where available.
- Geographic distribution.
- WAF signals.
- Error rates.
- Cache hit ratio.
- Origin request volume.

If the traffic is malicious or abusive, I would consider appropriate AWS WAF controls and other mitigation mechanisms.

If the traffic is legitimate and cacheable, CloudFront should ideally absorb a large portion of it without overwhelming the origin.

---

## Scenario: Traffic Increases but Origin Load Does Not

### Question

CloudFront traffic increases 10x, but origin traffic remains almost unchanged. Is this necessarily a problem?

### Strong Answer

No.

This can actually indicate healthy caching.

For example:

```text
CloudFront requests:
100k/min → 1M/min

Origin requests:
20k/min → 25k/min
```

If cache behavior remains healthy, CloudFront is absorbing the majority of the traffic.

This is an example where monitoring both edge traffic and origin traffic provides much more useful information than monitoring either metric independently.

---

## Scenario: Traffic Increases and Origin Load Also Increases 10x

### Question

CloudFront traffic increases 10x and origin traffic also increases 10x. What does that suggest?

### Strong Answer

It suggests that CloudFront is not absorbing the additional traffic effectively.

I would investigate:

- Cacheability.
- Cache hit ratio.
- Cache key fragmentation.
- TTLs.
- Query strings.
- Cookies.
- Headers.
- New dynamic endpoints.
- Cache policy changes.

If the traffic is expected to be cacheable, this may indicate a CDN configuration regression.

---

## Scenario: CloudFront Cost Suddenly Increases

### Question

Your CloudFront bill increases significantly. How would you investigate?

### Strong Answer

I would break the cost increase into traffic and configuration drivers.

I would investigate:

- Request volume.
- Bytes transferred.
- Geographic traffic distribution.
- Large objects.
- Cache hit ratio.
- Origin traffic.
- New application features.
- Unexpected traffic spikes.
- Bot traffic.
- Log delivery.
- Edge functions.
- Recent configuration changes.

A common chain is:

```text
Cache efficiency ↓
       │
       ▼
Origin requests ↑
       │
       ├── Backend cost ↑
       │
       └── Data transfer / request-related cost ↑
```

I would use AWS billing data alongside CloudFront operational metrics rather than trying to infer the entire bill from one CloudFront metric.

---

## Scenario: Users Receive Old JavaScript After Deployment

### Question

You deploy a new frontend version, but some users continue receiving the old JavaScript bundle through CloudFront. How would you solve it?

### Strong Answer

The preferred solution is generally versioned or fingerprinted assets.

For example:

```text
app.8f91c2.js
app.31a7de.js
```

Instead of:

```text
app.js
```

With immutable, content-hashed assets, new deployments create new object names.

This avoids relying heavily on global cache invalidations.

For urgent changes, invalidation can be used as an operational mechanism.

### Senior-Level Point

Cache invalidation is useful, but **cache-busting through versioned asset names is usually a more scalable application design**.

---

## Scenario: You Need Immediate Global Content Removal

### Question

A sensitive object was accidentally published and is currently cached by CloudFront. What do you do?

### Strong Answer

This is both an operational and potentially security-sensitive incident.

I would:

1. Remove or restrict the object at the origin.
2. Prevent further access.
3. Invalidate the affected CloudFront path where appropriate.
4. Confirm the object is no longer served.
5. Review logs and access patterns.
6. Determine whether sensitive data was exposed.
7. Follow the organization's security incident process.
8. Identify why the object became accessible.
9. Correct the underlying access-control problem.

The important distinction is:

```text
Origin deletion
≠
Immediate cache removal
```

Cached content has its own lifecycle.

---

## Scenario: CloudFront Distribution Has Multiple Origins

### Question

You have:

```text
/static/* → S3
/api/*    → ALB
/images/* → S3
```

Requests to `/api/users` are reaching S3. What would you investigate?

### Strong Answer

I would inspect CloudFront behavior matching.

The expected routing is:

```mermaid
flowchart LR
    Request["/api/users"] --> CF[CloudFront]
    CF --> API["/api/* behavior"]
    API --> ALB[ALB]

    Request2["/static/app.js"] --> CF
    CF --> Static["/static/* behavior"]
    Static --> S3[S3]
```

I would check:

- Path patterns.
- Behavior ordering.
- Origin association.
- Default behavior.
- Recent configuration deployment.

The key concept is that CloudFront selects a cache behavior based on the request path, and the selected behavior determines the relevant origin and policies.

---

## Scenario: API Works Directly but Not Through Custom Domain

### Question

Your API works through the ALB DNS name but fails through `api.example.com`, which points to CloudFront. What do you investigate?

### Strong Answer

I would compare the two request paths.

I would inspect:

- Route 53 record.
- CloudFront alternate domain name.
- TLS certificate.
- Viewer protocol policy.
- Origin configuration.
- Host header behavior.
- API path behavior.
- WAF rules.
- Allowed methods.
- Authentication headers.
- CORS.

The architecture should be understood as:

```text
api.example.com
       │
       ▼
Route 53
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

A working origin URL does not prove that the CloudFront configuration is correct.

---

## Scenario: HTTPS Works but HTTP Behavior Is Unexpected

### Question

You want all HTTP requests redirected to HTTPS. What should you configure?

### Strong Answer

Use an appropriate viewer protocol policy that redirects HTTP requests to HTTPS.

The intended flow is:

```text
HTTP request
    │
    ▼
CloudFront
    │
    ▼
HTTPS redirect
    │
    ▼
HTTPS request
```

I would verify the behavior from an external client rather than assuming the configuration propagated correctly.

---

## Scenario: Users Upload Large Files Through CloudFront

### Question

Your application allows users to upload large files. Should every upload necessarily go through Django?

### Strong Answer

Not necessarily.

For large objects, a better architecture is often:

```text
Client
   │
   ▼
Application
   │
   ├── Generate authorized upload mechanism
   │
   ▼
S3
```

The application handles authorization and metadata while S3 handles object storage.

CloudFront is primarily relevant to delivery of content rather than automatically being the correct path for every upload workload.

The architectural decision should consider:

- Object size.
- Upload protocol.
- Authentication.
- Security.
- Network cost.
- Backend resource consumption.
- Resumability.
- Client requirements.

---

## Scenario: Private Video Content Must Be Delivered

### Question

You need to serve private video files only to authenticated customers. How would you design the delivery path?

### Strong Answer

A common architecture is:

```text
Authenticated Application
        │
        ▼
Authorization
        │
        ▼
Signed URL / Signed Cookie
        │
        ▼
CloudFront
        │
        ▼
Private S3
```

The application decides whether the user is authorized.

CloudFront then enforces the signed access mechanism.

I would also ensure that the underlying S3 content is not independently exposed.

---

## Scenario: Signed URLs Are Generated but Users Still Get `403`

### Question

Your backend generates CloudFront signed URLs, but clients receive `403`. What do you investigate?

### Strong Answer

I would verify:

- Key configuration.
- Public key/trusted key group configuration.
- URL signature.
- Expiration time.
- Resource path.
- Policy conditions.
- Distribution configuration.
- Client clock issues where relevant.
- Whether the URL is being modified by another component.
- Whether the requested object matches the signed resource.

I would also verify that the signed URL is being generated for the exact CloudFront resource being requested.

---

## Scenario: You Need Access to an Entire Private Content Collection

### Question

You have thousands of private files and want to grant temporary access to an entire content collection. Would you prefer signed URLs or signed cookies?

### Strong Answer

Signed cookies can be more appropriate when a client needs access to multiple restricted resources without requiring a separate signed URL for each object.

For example:

```text
User authenticates
      │
      ▼
Application
      │
      ▼
Signed cookie
      │
      ▼
CloudFront
      │
      ├── video/1.mp4
      ├── video/2.mp4
      ├── video/3.mp4
      └── video/4.mp4
```

Signed URLs are often convenient for individual resources.

The correct choice depends on access patterns and authorization requirements.

---

## Scenario: CloudFront Is Caching Personalized API Responses

### Question

Your application uses JWT authentication. Can you safely cache the API response because the user is authenticated?

### Strong Answer

No.

Authentication and cacheability are separate concerns.

A response such as:

```http
Authorization: Bearer <token>
```

may be personalized.

If the cache key does not correctly distinguish users, CloudFront could serve one user's response to another user.

For highly personalized APIs, I would normally avoid shared caching unless the caching model is deliberately designed and verified.

---

## Scenario: CloudFront Is Behind Nginx

### Question

Your architecture is:

```text
Client → CloudFront → Nginx → Django
```

Where should you investigate if API latency increases?

### Strong Answer

I would measure each layer independently.

```text
CloudFront latency
      ↓
Nginx latency
      ↓
Django latency
      ↓
Database/Redis latency
```

Nginx may contribute to:

- Connection handling.
- TLS termination depending on architecture.
- Request buffering.
- Proxy configuration.
- Timeouts.
- Header handling.

The important point is to avoid attributing all latency to CloudFront merely because CloudFront is the public entry point.

---

## Scenario: CloudFront Returns a Cached Response After Origin Is Down

### Question

Your origin becomes unavailable, but some users continue receiving successful responses. How is that possible?

### Strong Answer

Those responses may be served from CloudFront edge caches without contacting the unavailable origin.

Conceptually:

```text
Request
  │
  ▼
CloudFront
  │
  ├── Cache hit → Response
  │
  └── Cache miss → Origin unavailable
```

This is one of the major reliability benefits of caching.

However, this should not be confused with a general-purpose application failover strategy.

---

## Scenario: Origin Becomes Unhealthy

### Question

Your primary origin becomes unavailable. How would you design CloudFront for resilience?

### Strong Answer

I would consider an architecture with multiple origins and an appropriate origin-failover strategy.

For example:

```mermaid
flowchart LR
    Client[Client] --> CF[CloudFront]
    CF --> Primary[Primary Origin]
    CF --> Secondary[Secondary Origin]

    Primary --> Health{Healthy?}
    Health -->|Yes| Response[Response]
    Health -->|No| Secondary
```

The exact failover mechanism depends on the protocol, cache behavior, origin type, and failure conditions.

I would also ensure the secondary origin is genuinely capable of serving production traffic.

---

## Scenario: Origin Failover Does Not Fix the Incident

### Question

You configured a secondary origin, but users still experience failures during primary-origin outages. What would you investigate?

### Strong Answer

I would verify:

- Whether the request method is eligible for failover.
- Which HTTP errors trigger failover.
- Whether the secondary origin is healthy.
- Whether DNS or networking is involved.
- Whether the failure occurs before CloudFront can determine origin failure.
- Whether cached error responses are involved.
- Whether the secondary has equivalent application data.
- Whether authentication and headers work with both origins.

A failover architecture is only useful if the secondary path is independently functional.

---

## Scenario: CloudFront and Django Return Different Host Behavior

### Question

Your Django application generates redirects to the internal ALB hostname instead of the public CloudFront hostname. What might be wrong?

### Strong Answer

I would inspect forwarded host and protocol information.

The application may need to correctly understand:

```text
Original request:
https://api.example.com

CloudFront:
      ↓

Origin:
http://internal-alb.example
```

If the application constructs URLs based on the origin host rather than the viewer-facing host, redirects may expose internal infrastructure.

I would review:

- Forwarded headers.
- Host handling.
- Django proxy/HTTPS configuration.
- CloudFront origin request policy.
- Nginx configuration.
- Application URL generation.

---

## Scenario: Cache Hit Ratio Is Low for an API

### Question

An API has a 20% cache hit ratio. Is that automatically a configuration failure?

### Strong Answer

No.

The correct answer depends on the endpoint.

For:

```text
GET /products
```

a higher cache hit ratio may be desirable if the data tolerates caching.

For:

```text
GET /account/profile
```

a low or zero shared-cache hit ratio may be completely appropriate because the response is personalized.

The correct question is:

> Is the cache behavior aligned with the semantics of the resource?

---

## Scenario: You Need to Cache a Product API

### Question

You have:

```http
GET /products/123
```

The response changes only occasionally. How would you approach caching?

### Strong Answer

I would first determine:

- Acceptable staleness.
- Update frequency.
- Whether the response is public.
- Cache key dimensions.
- TTL.
- Invalidation requirements.

A reasonable model could be:

```text
Client
  │
  ▼
CloudFront
  │
  ├── Cache hit → Product response
  │
  └── Cache miss → API
                       │
                       ▼
                   PostgreSQL
```

For updates, the system could use either controlled invalidation or versioned resources depending on the data model.

---

## Scenario: Product Price Changes but Cached Price Remains Old

### Question

A product price changes in PostgreSQL, but CloudFront continues returning the old price. What should you do?

### Strong Answer

First, determine the application's freshness requirement.

If the endpoint is allowed to be eventually consistent, a short TTL may be acceptable.

If price freshness must be immediate, I would design an explicit cache invalidation or cache-bypass strategy.

The important architectural decision is:

```text
Database update
      │
      ▼
Cache consistency strategy
      │
      ├── TTL-based
      ├── Explicit invalidation
      └── Versioned resource
```

Do not use a CDN cache for data requiring stronger consistency without explicitly designing for that requirement.

---

## Scenario: CloudFront Is Increasing Database Load

### Question

Your database suddenly receives more queries even though application traffic has not changed. CloudFront is also showing a cache-hit-ratio decrease. What is your hypothesis?

### Strong Answer

My first hypothesis would be that cache efficiency has degraded.

The likely chain is:

```text
CloudFront cache hit ratio ↓
        │
        ▼
Origin requests ↑
        │
        ▼
Django/FastAPI requests ↑
        │
        ▼
Database queries ↑
```

I would investigate CloudFront policy and cache-key changes before changing database capacity.

---

## Scenario: CloudFront Is Serving Different Content Based on Headers

### Question

Your application returns different representations based on a request header. What should you consider before caching the response?

### Strong Answer

The header may need to be considered in the cache key or request behavior if different header values produce materially different responses.

Otherwise:

```text
Request A → Response A
Request B → Response B

If cache key ignores the differentiating header:

Request B → cached Response A
```

This can cause correctness or security problems.

The principle is:

> Every request attribute that changes the representation must be accounted for in the caching design.

Only include dimensions that genuinely affect the representation, because excessive cache-key variation can destroy cache efficiency.

---

## Scenario: Query Strings Destroy Cache Efficiency

### Question

Your endpoint is:

```text
/products?page=1
/products?page=2
/products?page=3
```

Cache performance is poor. What do you investigate?

### Strong Answer

I would inspect how query strings participate in the cache key.

Some query parameters may meaningfully change the response, while others may be tracking parameters such as:

```text
utm_source
utm_campaign
```

If irrelevant parameters fragment the cache, requests that should share cached content may become separate cache entries.

The solution is to design the cache policy around the parameters that actually affect the response.

---

## Scenario: Cache Key Contains Too Many Dimensions

### Question

An engineer configured cookies, headers, and many query parameters in the cache key "to be safe." What is the problem?

### Strong Answer

The cache may become highly fragmented.

For example:

```text
Same object
   │
   ├── Cookie A
   ├── Cookie B
   ├── Header X
   ├── Header Y
   └── Query parameter Z
```

can produce many independent cache entries.

This reduces cache efficiency and increases origin traffic.

The better approach is:

> Include only request attributes that materially change the response.

---

## Scenario: AWS WAF Blocks Legitimate Users

### Question

Users suddenly receive `403` responses after adding a WAF rule. What do you investigate?

### Strong Answer

I would correlate:

```text
Deployment/change timestamp
        +
WAF blocked requests
        +
CloudFront 403 responses
```

Then I would inspect:

- WAF rule.
- Rule priority.
- Managed rule groups.
- Request characteristics.
- False positives.
- Affected paths.
- Geographic scope.
- Client behavior.

I would avoid simply disabling all security controls.

Instead, I would identify the rule causing the false positive and apply the narrowest safe correction.

---

## Scenario: Bot Traffic Causes Origin Load

### Question

A large number of automated clients repeatedly hit an uncached API endpoint. The origin is becoming overloaded. What controls could you consider?

### Strong Answer

I would consider layered controls:

```text
Internet
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

Potential controls include:

- WAF rate-based rules.
- Bot-management capabilities where appropriate.
- Authentication.
- API-level rate limiting.
- Caching where semantically safe.
- Origin capacity protection.

The correct layer depends on the type of abuse and the required enforcement semantics.

---

## Scenario: CloudFront Is Serving an Old Error After Recovery

### Question

The backend has recovered, but CloudFront continues returning an error for a resource. What might explain this?

### Strong Answer

The error response itself may have been cached.

I would check:

- Error caching behavior.
- Cache status.
- TTL.
- Whether the response is still present in the edge cache.
- Whether invalidation is appropriate.

The incident illustrates why error caching deserves operational attention just like successful-response caching.

---

## Scenario: Deployment Causes a Global Regression

### Question

A CloudFront configuration deployment causes problems globally. What is your immediate response?

### Strong Answer

I would prioritize restoring service over performing a perfect root-cause analysis during the initial incident.

The sequence would be:

```text
Detect
  ↓
Assess blast radius
  ↓
Stop further change
  ↓
Rollback / mitigate
  ↓
Verify recovery
  ↓
Investigate root cause
  ↓
Prevent recurrence
```

I would preserve evidence such as:

- Configuration version.
- Deployment timestamp.
- CloudWatch metrics.
- Logs.
- CloudTrail events.
- CI/CD records.

---

## Scenario: CloudFront Configuration Is Managed Through CI/CD

### Question

How would you safely deploy CloudFront configuration changes?

### Strong Answer

I would treat CloudFront configuration as infrastructure code.

A production pipeline could include:

```text
Pull Request
    │
    ▼
Validation
    │
    ▼
Plan / Diff
    │
    ▼
Review
    │
    ▼
Deployment
    │
    ▼
Monitoring
    │
    ▼
Rollback if required
```

Important practices include:

- Peer review.
- Environment separation.
- Configuration validation.
- Controlled rollout.
- Monitoring after deployment.
- Versioned infrastructure.
- Documented rollback procedures.

---

## Scenario: You Need to Reduce Origin Load Without Changing the Application

### Question

Your Django application is overloaded, but application changes cannot be deployed immediately. What CloudFront-level actions could help?

### Strong Answer

If the traffic is cacheable, I would investigate whether CloudFront can absorb more requests through:

- Appropriate cache policies.
- Suitable TTLs.
- Correct cache keys.
- Removing unnecessary cache-key variation.
- Caching static or semi-static resources.
- Avoiding unnecessary invalidations.

However, I would not cache personalized or security-sensitive responses simply to reduce load.

The correct optimization must preserve application semantics.

---

## Scenario: You Need Global Low-Latency Delivery for Static Assets

### Question

Your application serves large JavaScript, CSS, image, and video assets from S3. How would CloudFront help?

### Strong Answer

The architecture would be:

```text
Client
   │
   ▼
CloudFront
   │
   ├── Edge cache hit → Asset
   │
   └── Cache miss
          │
          ▼
         S3
```

CloudFront moves frequently accessed objects closer to viewers through edge caching.

I would also use:

- Long-lived caching for immutable assets.
- Content-hashed filenames.
- Compression where applicable.
- Appropriate object metadata.
- Private S3 access controlled through CloudFront.

---

## Scenario: CloudFront Is Not Reducing Backend Traffic

### Question

You introduced CloudFront but backend traffic barely changed. What would you investigate?

### Strong Answer

I would ask whether the workload is actually cacheable.

Then inspect:

- Cache-Control headers.
- TTL.
- Cache policy.
- Cache key.
- Query strings.
- Cookies.
- Headers.
- HTTP methods.
- Request path.
- Cache invalidations.

If every request has a unique cache key, CloudFront may effectively behave as a pass-through layer for that workload.

---

## Scenario: Dynamic API Uses Redis and CloudFront

### Question

Your architecture is:

```text
CloudFront → Django → Redis → PostgreSQL
```

Why might you use both CloudFront and Redis?

### Strong Answer

They solve different caching problems.

```text
CloudFront
    │
    └── Edge/network-level response caching

Django
    │
    └── Application-level caching

Redis
    │
    └── Backend data/result caching
```

CloudFront can prevent requests from reaching the application at all.

Redis is useful after a request reaches the application.

Therefore:

```text
CloudFront cache hit
    → Django and Redis are bypassed

CloudFront miss
    → Django may use Redis

Redis miss
    → Application may query PostgreSQL
```

This creates multiple caching layers with different responsibilities.

---

## Scenario: CloudFront Cache Hit Is High but Application Is Still Slow

### Question

CloudFront has a high cache-hit ratio, but users still report slow API responses. What could be happening?

### Strong Answer

I would verify whether the slow requests are actually cache hits.

A high aggregate cache-hit ratio can hide a problematic subset of requests.

For example:

```text
95% cached
5% uncached

But the 5% may contain:
- checkout
- login
- search
- account
```

Those endpoints may be responsible for most user-visible latency.

I would segment metrics by:

- Path.
- Behavior.
- Status.
- Request type.
- Cache status where available.

---

## Scenario: A New API Endpoint Is Accidentally Cached

### Question

A developer deploys `/api/orders` and later discovers that responses are being cached. What should happen?

### Strong Answer

First determine whether the endpoint is safe to cache.

For order data, responses are usually user-specific and potentially sensitive.

I would:

1. Disable inappropriate shared caching.
2. Verify response behavior.
3. Invalidate affected cached objects if necessary.
4. Check whether sensitive data was exposed.
5. Review cache policies and application headers.
6. Add automated configuration tests or deployment checks.

The deeper lesson is that caching should be an explicit architectural decision, not an accidental side effect.

---

## Scenario: CloudFront Distribution Has Hundreds of Behaviors

### Question

A CloudFront distribution has become difficult to manage because it contains hundreds of cache behaviors. How would you improve the design?

### Strong Answer

I would first determine whether the behaviors represent genuine differences in:

- Origin.
- Authentication.
- HTTP methods.
- Cache policy.
- Origin request policy.
- Security requirements.

If multiple behaviors exist only because of historical configuration, I would consolidate them where semantics permit.

I would also establish:

- Naming conventions.
- Infrastructure-as-code.
- Configuration ownership.
- Documentation.
- Review requirements.

Complexity itself becomes an operational risk.

---

## Scenario: CloudFront Configuration Works in Staging but Fails in Production

### Question

The same application works through CloudFront in staging but fails in production. What would you compare?

### Strong Answer

I would compare infrastructure rather than assuming the application is identical.

Important differences may include:

- Origins.
- DNS.
- Certificates.
- WAF.
- Cache policies.
- Origin request policies.
- S3 permissions.
- Environment variables.
- Allowed methods.
- Viewer protocol policy.
- Security controls.
- Edge functions.
- Network access.

I would generate a configuration diff rather than manually comparing dozens of settings.

---

## Scenario: CloudFront and Kubernetes

### Question

Your backend runs on Kubernetes behind an ingress controller. Where does CloudFront fit?

### Strong Answer

A common architecture is:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Load Balancer
   │
   ▼
Ingress
   │
   ▼
Kubernetes Service
   │
   ▼
Pods
```

CloudFront provides global edge delivery and caching.

Kubernetes handles application scheduling, service discovery, scaling, and workload management.

The systems solve different problems and should not be treated as interchangeable.

---

## Scenario: Kubernetes Scales but CloudFront Cache Is Broken

### Question

Your Kubernetes cluster automatically scales when traffic increases, but CloudFront cache efficiency drops significantly. Is autoscaling enough?

### Strong Answer

No.

Autoscaling addresses increased application capacity, but it does not solve inefficient caching.

If a cache-policy regression causes:

```text
Origin requests ↑
```

Kubernetes may simply respond by:

```text
Pods ↑
CPU ↑
Database load ↑
Cost ↑
```

The correct solution may be to restore the intended cache behavior rather than continuously scaling the origin.

---

## Scenario: CloudFront Is Used for a gRPC Service

### Question

Can CloudFront be placed in front of a gRPC workload?

### Strong Answer

The answer depends on the specific CloudFront and gRPC requirements, supported protocol behavior, and architecture.

I would not assume that a CDN designed around HTTP content delivery should automatically be used for arbitrary gRPC service-to-service traffic.

For internal microservice communication, direct service-to-service networking or an architecture specifically designed for gRPC is often more appropriate.

The interview answer should focus on protocol compatibility and workload characteristics rather than saying "CloudFront is always suitable" or "CloudFront is never suitable."

---

## Scenario: You Need to Debug a CloudFront Incident Quickly

### Question

You have five minutes to investigate a production CloudFront incident. What do you check first?

### Strong Answer

I would prioritize high-signal information:

```text
1. What changed?
2. Error rate
3. Request volume
4. Cache behavior
5. Origin request volume
6. Origin latency
7. Origin health
8. Recent deployments/configuration changes
```

Then I would determine:

```text
Is the problem:
    │
    ├── Client/request related?
    ├── Edge/cache related?
    ├── Security/WAF related?
    ├── Origin related?
    └── Application/dependency related?
```

This prevents random configuration changes during an incident.

---

## Scenario: CloudFront Is Healthy but Users Still Cannot Access the Application

### Question

All CloudFront metrics look normal, but users report that the application is unavailable. What would you check?

### Strong Answer

CloudFront metrics may remain healthy if the failure occurs outside the signals being examined.

I would check:

- DNS.
- TLS/certificate problems.
- Browser-side failures.
- WAF.
- Origin behavior.
- Application errors.
- Authentication.
- CORS.
- Specific paths.
- Geographic scope.

I would also reproduce the request externally.

The key lesson is:

> A green CloudFront dashboard does not prove that the entire application is healthy.

---

## Scenario: Users in One Country Receive `403`

### Question

Users in one geographic region receive `403` while other users work normally. What could cause this?

### Strong Answer

Potential causes include:

- WAF geographic rules.
- CloudFront geographic restrictions.
- Application authorization.
- IP reputation controls.
- Bot rules.
- Regional infrastructure behavior.

I would compare:

```text
Working request
vs.
Failing request
```

and inspect the security and routing layers.

---

## Scenario: CloudFront Behaves Differently After DNS Migration

### Question

You migrated a domain from another CDN to CloudFront. Some users still reach the old CDN. Why?

### Strong Answer

DNS propagation and resolver caching can cause clients to continue using previously resolved addresses.

I would verify:

- DNS records.
- TTL.
- Authoritative DNS configuration.
- CloudFront alternate domain configuration.
- TLS certificate.
- Resolver behavior.
- Client/network caches.

I would not assume that changing the authoritative record means every client immediately uses the new destination.

---

## Scenario: CloudFront Origin Is Private

### Question

Why would you keep the origin private instead of allowing users to access it directly?

### Strong Answer

The goal is to make CloudFront the controlled public entry point.

For example:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Private / restricted origin
```

This reduces the ability for clients to bypass:

- CDN controls.
- WAF.
- Authentication mechanisms.
- Edge policies.
- Centralized traffic controls.

The origin should be protected according to its architecture rather than assuming CloudFront alone provides security.

---

## Scenario: Users Bypass CloudFront

### Question

You discover users can access the ALB directly instead of going through CloudFront. What is the concern?

### Strong Answer

The origin can become an alternate public entry point.

That can allow users to bypass:

- CloudFront caching.
- WAF controls attached to the CloudFront path.
- Viewer restrictions.
- Edge-level policies.
- Some traffic-management controls.

I would restrict origin access appropriately and verify that legitimate origin-to-CloudFront traffic still works.

---

## Scenario: CloudFront Configuration Change Causes Cache Fragmentation

### Question

A developer adds a cookie to the cache key. Cache hit ratio drops dramatically. Why?

### Strong Answer

The cookie creates additional cache-key variants.

For example:

```text
/product/123 + user=A
/product/123 + user=B
/product/123 + user=C
```

can become separate cached objects.

If the cookie does not actually change the representation, including it in the cache key is unnecessary and harmful.

The correct design is to include only dimensions that affect the response.

---

## Scenario: You Need to Protect a High-Traffic API

### Question

How would you combine CloudFront and WAF for a public API?

### Strong Answer

A common architecture is:

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

CloudFront handles edge delivery and caching where appropriate.

WAF handles web-layer filtering and request controls.

The application still owns business-level authorization.

I would not assume WAF replaces application authentication and authorization.

---

## Scenario: API Requires Authentication but Public Assets Do Not

### Question

How would you design CloudFront behaviors for:

```text
/static/*
/api/*
```

### Strong Answer

I would generally separate the behaviors because they have different semantics.

```text
/static/*
    → S3
    → aggressive caching
    → immutable assets where possible

/api/*
    → ALB
    → controlled caching
    → authentication-aware request handling
```

This allows the static and dynamic workloads to have independent policies.

---

## Scenario: CloudFront Is Serving a Large File Slowly

### Question

A large video or software package downloads slowly for users. What do you investigate?

### Strong Answer

I would inspect:

- Object size.
- Cache status.
- Edge location.
- Origin response time.
- Origin bandwidth.
- Compression suitability.
- Range-request behavior.
- Client/network conditions.
- Cache availability.

I would determine whether the object is already cached at the relevant edge or repeatedly fetched from the origin.

---

## Scenario: CloudFront Cache Is Frequently Invalidated

### Question

Your deployment pipeline invalidates thousands of CloudFront objects every time the application deploys. Is that ideal?

### Strong Answer

Not necessarily.

For static assets, content-hashed filenames are generally preferable:

```text
app.<hash>.js
style.<hash>.css
```

Then old and new assets can coexist safely.

Invalidation remains useful for:

- Urgent corrections.
- Small numbers of mutable objects.
- Exceptional operational situations.

A deployment process that depends heavily on invalidation may indicate that asset versioning or cache strategy could be improved.

---

## Scenario: Origin Latency Increases Only on Cache Misses

### Question

CloudFront cache hits are fast, but cache misses are increasingly slow. What does that suggest?

### Strong Answer

It points toward the origin path.

I would investigate:

- ALB latency.
- Nginx.
- Django/FastAPI.
- Redis.
- PostgreSQL.
- External APIs.
- Connection pools.
- CPU and memory.
- Database locks.

The key distinction is:

```text
Cache hit
  → Edge only

Cache miss
  → Edge + origin path
```

If only cache misses degrade, the origin path becomes the primary investigation target.

---

## Scenario: CloudFront Has High Availability but Origin Has One Instance

### Question

Does putting an application behind CloudFront make the application highly available?

### Strong Answer

No.

CloudFront can provide highly distributed edge infrastructure, but if every cache miss depends on one application instance, the origin remains a single point of failure.

A production architecture should consider:

```text
CloudFront
    │
    ▼
Load Balancer
    │
    ├── App 1
    ├── App 2
    └── App 3
```

High availability must be designed across the entire request path.

---

## Scenario: Disaster Recovery for a CloudFront-Backed Application

### Question

How would you approach disaster recovery for an application using CloudFront and S3?

### Strong Answer

I would consider the complete dependency chain:

```text
CloudFront
   │
   ├── S3 content
   │
   └── Application origin
          │
          ├── Database
          └── Other dependencies
```

Important considerations include:

- S3 data durability and recovery strategy.
- Application deployment reproducibility.
- Infrastructure-as-code.
- Origin failover where appropriate.
- Database backups.
- Recovery procedures.
- DNS and certificate dependencies.
- CloudFront configuration recovery.

CloudFront configuration should not exist only as undocumented console state.

---

## Scenario: CloudFront Configuration Is Lost

### Question

A production CloudFront distribution needs to be recreated. How would you ensure this is possible?

### Strong Answer

Manage configuration through infrastructure-as-code and version control.

The repository should capture relevant:

- Distribution configuration.
- Origins.
- Behaviors.
- Cache policies.
- Origin request policies.
- Response headers policies.
- Security integrations.
- Certificates and related references.
- Edge functions.
- DNS relationships.

The principle is:

> Production infrastructure should be reproducible rather than dependent on manual console configuration.

---

## Scenario: CloudFront Monitoring Shows a Sudden Traffic Drop

### Question

Traffic falls from 500,000 requests/minute to 20,000 requests/minute. What do you investigate?

### Strong Answer

I would first determine whether the traffic drop represents:

- A genuine user decline.
- DNS failure.
- Client-side failure.
- Routing failure.
- Application deployment issue.
- CloudFront distribution problem.
- Monitoring/data issue.

I would correlate with:

```text
DNS
+
CloudFront
+
ALB
+
Application
+
Business metrics
```

If CloudFront traffic drops and business traffic also drops, the issue may be upstream of CloudFront.

If CloudFront traffic drops but application traffic behaves differently, I would investigate routing and measurement.

---

## Scenario: Error Rate Is High but Users Report No Problem

### Question

CloudFront reports a high `4xx` rate, but customers appear unaffected. How do you investigate?

### Strong Answer

I would segment the errors.

A high `4xx` rate may come from:

- Bots.
- Invalid URLs.
- Health checks.
- Automated scanners.
- Deprecated endpoints.
- Expected authorization failures.

The metric needs context.

I would investigate:

- Which paths generate the errors.
- Which status codes dominate.
- Request sources.
- Traffic volume.
- User impact.

Not every high `4xx` rate represents a customer-facing outage.

---

## Scenario: CloudFront Error Rate Is Low but Business Transactions Fail

### Question

CloudFront shows almost no errors, but checkout failures have increased significantly. Why can this happen?

### Strong Answer

CloudFront monitors HTTP delivery behavior, but business success is a higher-level application concept.

A request can return:

```http
HTTP 200 OK
```

while the application returns:

```json
{
  "success": false,
  "error": "payment_failed"
}
```

Therefore, CloudFront monitoring must be combined with:

- Application metrics.
- Business metrics.
- Payment-service metrics.
- Database metrics.
- Distributed tracing where available.

Infrastructure health does not automatically equal business health.

---

## Scenario: CloudFront Is Used for a REST API

### Question

What would determine whether a REST API should be cached through CloudFront?

### Strong Answer

I would evaluate:

- Whether the response is public.
- Whether it is deterministic.
- Whether stale data is acceptable.
- How frequently it changes.
- Whether it contains personalized information.
- Whether authentication affects the response.
- Whether query parameters change the response.
- Whether cache invalidation is manageable.

A public product catalog may be a strong caching candidate.

A user's account balance generally is not.

---

## Scenario: CloudFront and Celery

### Question

Your Django application uses Celery for asynchronous processing. Does CloudFront help with Celery workload performance?

### Strong Answer

Not directly.

CloudFront primarily affects HTTP content delivery.

Celery handles asynchronous backend work:

```text
Client
  │
  ▼
CloudFront
  │
  ▼
Django
  │
  └── Celery → Worker → Broker / Backend
```

CloudFront may reduce synchronous HTTP traffic reaching Django, but it does not directly accelerate Celery workers.

---

## Scenario: CloudFront and Kafka

### Question

Your backend uses Kafka for event processing. Does CloudFront replace Kafka for high-volume traffic?

### Strong Answer

No.

They solve completely different problems.

```text
CloudFront
→ HTTP content delivery and edge caching

Kafka
→ Distributed event streaming and asynchronous communication
```

A system can use both:

```text
Client
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
   ▼
Consumers
```

CloudFront handles the synchronous delivery edge; Kafka handles event-driven backend processing.

---

## Scenario: You Need to Prove CloudFront Improved Performance

### Question

How would you measure whether introducing CloudFront actually improved your system?

### Strong Answer

I would establish a baseline before deployment and compare:

- User-facing latency.
- Origin request volume.
- Cache hit ratio.
- Origin latency.
- Error rate.
- Data transfer.
- Backend CPU.
- Database load.
- Cost.

For example:

```text
Before:
Origin requests = 1M/min
P95 latency     = 700 ms

After:
Origin requests = 150k/min
P95 latency     = 280 ms
```

The important point is to measure both CDN metrics and downstream system effects.

---

## Scenario: CloudFront Is Introduced but Performance Gets Worse

### Question

After introducing CloudFront, latency increases instead of decreasing. What could be wrong?

### Strong Answer

I would not assume that adding a CDN automatically improves every workload.

Potential causes include:

- Poor cacheability.
- Cache misses.
- Incorrect origin configuration.
- Extra redirects.
- Incorrect TLS behavior.
- Cache-key fragmentation.
- Large uncached responses.
- Geographic routing characteristics.
- Additional request-processing logic.

I would compare the old and new request paths and determine exactly where latency was introduced.

---

## Scenario: You Need Zero-Downtime CloudFront Configuration Changes

### Question

How would you reduce risk when changing CloudFront configuration in production?

### Strong Answer

I would:

- Use infrastructure-as-code.
- Review configuration diffs.
- Separate changes into small units.
- Validate configuration before deployment.
- Deploy during an appropriate change window.
- Monitor key metrics immediately afterward.
- Maintain a tested rollback process.
- Avoid combining unrelated cache, origin, and security changes into one deployment.

The objective is to reduce the blast radius of each change.

---

## Scenario: Interviewer Asks for a Complete Incident Response

### Question

"CloudFront is returning intermittent `5xx` errors, origin CPU is high, database connections are exhausted, and the issue started after a deployment. Walk me through your response."

### Strong Answer

I would reason through the incident as a chain rather than treating each symptom independently.

```text
Deployment
    │
    ▼
CloudFront behavior change?
    │
    ▼
Cache hit ratio ↓
    │
    ▼
Origin traffic ↑
    │
    ▼
Application CPU ↑
    │
    ▼
Database connections exhausted
    │
    ▼
Application latency ↑
    │
    ▼
CloudFront 5xx ↑
```

My response would be:

1. Declare or escalate the incident according to the operational process.
2. Stop additional deployments.
3. Confirm the timing correlation.
4. Compare CloudFront metrics before and after deployment.
5. Check cache-hit ratio and origin request volume.
6. Determine whether the CloudFront configuration changed.
7. Check application and database saturation.
8. Roll back the suspected configuration if safe.
9. Verify cache behavior and origin load recover.
10. Confirm error rates return to baseline.
11. Preserve logs and configuration history.
12. Perform root-cause analysis afterward.
13. Add validation or monitoring to prevent recurrence.

This demonstrates a senior engineering mindset because the objective is not merely to identify the error; it is to restore service safely and prevent recurrence.

---

## Scenario: Design a Production CloudFront Architecture

### Question

Design CloudFront for a production Django application with static assets, REST APIs, private media, Redis, and PostgreSQL.

### Strong Answer

A reasonable architecture is:

```mermaid
flowchart TD
    User[Users] --> CF[CloudFront]
    CF --> Static["Static Assets"]
    CF --> API["API Behavior"]
    CF --> Media["Private Media"]

    Static --> S3Static[S3 Static Assets]
    API --> ALB[Application Load Balancer]
    Media --> S3Media[Private S3 Media]

    ALB --> Django[Django Application]
    Django --> Redis[Redis]
    Django --> PostgreSQL[PostgreSQL]

    CF --> WAF[AWS WAF]
```

Recommended separation:

| Workload | Recommended approach |
|---|---|
| Static assets | Aggressive caching |
| Immutable JS/CSS | Long TTL + content hashing |
| Public media | Cache according to freshness requirements |
| Private media | Signed URLs/cookies |
| Personalized APIs | Usually avoid shared caching |
| Public read APIs | Cache selectively |
| Write APIs | Forward to origin without inappropriate caching |
| Sensitive responses | Avoid shared caching |

The architecture should be driven by resource semantics rather than trying to maximize the cache-hit ratio at all costs.

---

## Scenario: Explain the Most Dangerous CloudFront Mistakes

### Question

What CloudFront mistakes are most dangerous in production?

### Strong Answer

The highest-risk mistakes include:

| Mistake | Risk |
|---|---|
| Caching personalized responses | Data leakage |
| Exposing the origin directly | Security/control bypass |
| Incorrect cache key | Incorrect content delivery |
| Excessive cache-key dimensions | Poor cache efficiency |
| Incorrect HTTP method policy | API failures |
| Incorrect origin routing | Requests sent to wrong backend |
| Poor error caching configuration | Persistent failures |
| No monitoring | Slow incident detection |
| No infrastructure-as-code | Difficult recovery |
| Treating CloudFront as an HA solution for the whole stack | Hidden origin SPOFs |
| Overusing invalidations | Operational inefficiency |
| Ignoring WAF integration | Increased exposure to abusive traffic |

---

## Scenario: Senior-Level CloudFront Design Question

### Question

"How would you decide whether to cache an API endpoint?"

### Strong Answer

I would evaluate the endpoint across several dimensions:

```text
Is the response public?
        │
        ├── No → Usually avoid shared caching
        │
        └── Yes
             │
             ▼
Does the response tolerate staleness?
             │
             ├── No → Avoid or tightly control caching
             │
             └── Yes
                  │
                  ▼
What request attributes change the response?
                  │
                  ▼
Design cache key
                  │
                  ▼
Choose TTL
                  │
                  ▼
Design invalidation/update strategy
                  │
                  ▼
Monitor cache and origin behavior
```

The key design principle is:

> Cacheability is a property of the resource and its consistency requirements, not simply a property of the HTTP method.

---

## Scenario: Interviewer Challenges Your Cache Strategy

### Question

"Why not just set a very long TTL to maximize CloudFront performance?"

### Strong Answer

Because maximum caching is not the same as correct caching.

A long TTL can produce:

- Stale data.
- Difficult invalidation.
- Incorrect application behavior.
- Security issues for improperly cached personalized responses.

For immutable assets, a very long TTL can be excellent.

For frequently changing API data, it may be inappropriate.

The correct TTL is determined by:

```text
Freshness requirement
+
Update frequency
+
Invalidation strategy
+
Data sensitivity
+
Performance requirements
```

---

## Scenario: Interviewer Asks What You Would Monitor First

### Question

"If you could monitor only five CloudFront signals, which would you choose?"

### Strong Answer

For a typical production workload, I would start with:

1. Request volume.
2. `4xx` error rate.
3. `5xx` error rate.
4. Cache behavior.
5. Origin latency.

I would then correlate those with origin request volume and backend metrics.

The exact priority can change depending on whether the workload is static, dynamic, API-heavy, media-heavy, or security-sensitive.

---

## Scenario: Interviewer Asks for Your CloudFront Troubleshooting Framework

### Question

"What is your general approach when CloudFront is behaving unexpectedly?"

### Strong Answer

I use a layered troubleshooting model:

```text
DNS
 │
 ▼
Viewer / TLS
 │
 ▼
CloudFront behavior
 │
 ▼
Cache policy
 │
 ▼
Origin request policy
 │
 ▼
WAF / security
 │
 ▼
Origin
 │
 ▼
Application
 │
 ▼
Dependencies
```

At each layer I ask:

- Is the request reaching this layer?
- What configuration controls the request here?
- What metric proves its behavior?
- What log proves its behavior?
- What changed recently?
- Is the issue global or scoped?
- Can the problem be reproduced?
- What is the safest remediation?

This framework is more valuable in an interview than memorizing isolated CloudFront commands.

---

## Common Interview Traps

### "High cache hit ratio means the system is healthy."

Not necessarily.

The cached content could be incorrect, stale, or insecure.

### "CloudFront handles high availability."

Only partially.

The origin and its dependencies still require independent HA design.

### "Authenticated requests cannot be cached."

Authentication does not automatically determine cacheability. The critical question is whether the response is safely shareable.

### "Invalidation solves stale data."

Invalidation can remove cached objects, but it does not replace a correct cache-consistency strategy.

### "A CloudFront `5xx` means CloudFront is broken."

The error may originate from the origin or another part of the request path.

### "More cache-key fields are safer."

Excessive cache-key dimensions can destroy cache efficiency and may create unnecessary origin load.

### "A CDN should always reduce latency."

A CDN helps workloads that benefit from edge delivery and caching. It is not automatically faster for every request.

### "A green CloudFront dashboard means the application is healthy."

Business logic, authentication, databases, external services, and application-level failures can still be broken.

---

## Production Decision Matrix

| Situation | Typical CloudFront approach |
|---|---|
| Immutable static assets | Aggressive caching |
| Public images | Cache according to freshness |
| Public product catalog | Controlled caching |
| Personalized account API | Avoid shared caching |
| Authentication endpoint | Usually origin-driven |
| Write-heavy API | Avoid inappropriate caching |
| Private downloads | Signed URL/cookie |
| Large media delivery | Edge caching |
| Frequently changing data | Short TTL or explicit invalidation |
| Sensitive data | Conservative caching |
| High bot traffic | CloudFront + WAF + application controls |
| Multi-origin application | Path-based behaviors |
| High origin load | Investigate cache efficiency first |

---

## Production Scenario Checklist

When answering any CloudFront scenario, consider:

- [ ] Request path.
- [ ] Viewer protocol.
- [ ] CloudFront behavior.
- [ ] Origin selection.
- [ ] Cache policy.
- [ ] Origin request policy.
- [ ] Response headers policy.
- [ ] HTTP methods.
- [ ] Query strings.
- [ ] Cookies.
- [ ] Headers.
- [ ] Authentication.
- [ ] WAF.
- [ ] Cache hit behavior.
- [ ] Origin request volume.
- [ ] Origin latency.
- [ ] `4xx` and `5xx` rates.
- [ ] Recent deployments.
- [ ] Recent CloudFront configuration changes.
- [ ] Origin health.
- [ ] Application health.
- [ ] Database and Redis health.
- [ ] Access or real-time logs.
- [ ] Security implications.
- [ ] Cost implications.
- [ ] Rollback strategy.
- [ ] Long-term prevention.

## Key Takeaways

- **Approach CloudFront scenarios systematically: establish the symptom and blast radius, inspect edge behavior, correlate origin metrics, identify the root cause, remediate safely, and verify recovery.**
- **Most CloudFront production problems are easier to diagnose by correlating cache behavior, origin request volume, latency, errors, deployments, and downstream backend health rather than examining one metric in isolation.**
- **Caching is an architectural decision involving correctness, freshness, security, and cache-key design; maximizing cache-hit ratio is not the objective by itself.**
- **CloudFront improves edge delivery and can reduce origin load, but it does not automatically make the entire backend highly available or secure; origins, applications, databases, WAF, and authentication still require independent design.**
- **Senior-level CloudFront answers focus on trade-offs, blast radius, observability, rollback, security, and prevention rather than simply naming a configuration setting.**