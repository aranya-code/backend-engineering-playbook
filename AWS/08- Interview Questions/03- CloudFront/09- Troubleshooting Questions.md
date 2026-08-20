# 09- Troubleshooting Questions

## Overview

CloudFront troubleshooting requires reasoning across the complete request path rather than treating the CDN as an isolated component.

A production request may traverse:

```text
Client
  │
  ▼
DNS
  │
  ▼
CloudFront
  │
  ├── Cache hit ───────────────► Client
  │
  └── Cache miss
          │
          ▼
       AWS WAF
          │
          ▼
       Origin
          │
          ▼
   ALB / Nginx / Ingress
          │
          ▼
    Django / FastAPI
          │
       ┌──┴──┐
       ▼     ▼
    Redis PostgreSQL
```

A strong troubleshooting answer identifies **where the request fails**, **what changed**, **whether the problem is global or scoped**, and **which metric or log can prove the hypothesis**.

The most useful troubleshooting dimensions are:

| Dimension | Questions |
|---|---|
| DNS | Is the request reaching CloudFront? |
| TLS | Is the certificate and HTTPS configuration correct? |
| Behavior | Which CloudFront behavior matches the request? |
| Cache | Was the request a hit, miss, or stale/error response? |
| Request policy | Which headers, cookies, and query strings reach the origin? |
| Security | Is WAF or another restriction blocking the request? |
| Origin | Is the origin healthy and reachable? |
| Application | Is Django/FastAPI returning the expected response? |
| Dependencies | Are Redis, PostgreSQL, Kafka, or external APIs healthy? |
| Deployment | Did a recent release or configuration change introduce the problem? |

---

## Core Troubleshooting Method

Use a layered approach instead of changing multiple settings simultaneously.

```mermaid
flowchart TD
    Start["User reports failure"] --> Scope["Determine scope and blast radius"]
    Scope --> DNS["Check DNS and TLS"]
    DNS --> CF["Check CloudFront behavior"]
    CF --> Cache["Check cache behavior"]
    Cache --> Security["Check WAF and access controls"]
    Security --> Origin["Check origin health"]
    Origin --> App["Check application"]
    App --> Dependencies["Check Redis, PostgreSQL, external services"]
    Dependencies --> Change["Check recent deployments/configuration"]
    Change --> Mitigate["Apply safest mitigation"]
    Mitigate --> Verify["Verify recovery"]
    Verify --> Prevent["Document root cause and prevention"]
```

### Recommended Investigation Order

1. Establish the exact failing URL, method, status code, and time window.
2. Determine whether the issue affects all users or a subset.
3. Determine whether the issue is global or geographic.
4. Identify the CloudFront behavior matching the request.
5. Determine whether the request is cached.
6. Check `4xx` and `5xx` metrics.
7. Check origin request volume and latency.
8. Check WAF and security controls.
9. Check origin infrastructure.
10. Check application and dependency health.
11. Compare the current state with recent changes.
12. Apply the smallest safe remediation.
13. Verify recovery from an external client.
14. Preserve evidence for root-cause analysis.

---

## Troubleshooting CloudFront `4xx` Errors

A `4xx` response indicates that the request was rejected or could not be fulfilled from the perspective of the client-facing HTTP flow, but the exact cause depends on where the response originated.

Useful questions include:

- Is CloudFront generating the response?
- Is WAF generating the response?
- Is the origin generating the response?
- Is the response cached?
- Is authentication involved?
- Is the request reaching the expected behavior?

Do not assume every CloudFront `4xx` is caused by CloudFront itself.

---

## Troubleshooting `403 Forbidden`

### Question

CloudFront returns `403 Forbidden`. How do you troubleshoot it?

### Answer

Start by identifying which layer generated the `403`.

Potential sources include:

- CloudFront configuration.
- AWS WAF.
- S3 permissions.
- Origin authorization.
- Signed URL/cookie validation.
- Application authentication.
- Geographic restrictions.
- Viewer restrictions.
- Incorrect behavior configuration.

Use this decision path:

```text
403
 │
 ├── WAF?
 │     └── Check blocked request/rule
 │
 ├── S3?
 │     └── Check bucket/object access
 │
 ├── Signed access?
 │     └── Check signature/policy/expiry
 │
 ├── CloudFront behavior?
 │     └── Check allowed methods/restrictions
 │
 └── Application?
       └── Check authentication/authorization
```

### Production Approach

Compare a working request with a failing request:

| Attribute | Working | Failing |
|---|---|---|
| URL | Same/different | Same/different |
| HTTP method | GET/POST/etc. | GET/POST/etc. |
| Region | Region A | Region B |
| Headers | Relevant headers | Relevant headers |
| Cookies | Present/absent | Present/absent |
| Authentication | Valid | Invalid/expired |
| WAF decision | Allowed | Blocked |
| Cache behavior | Hit/miss | Hit/miss |

---

## Troubleshooting `404 Not Found`

### Question

CloudFront returns `404`, but the object exists at the origin.

### Answer

Investigate:

- Origin path.
- CloudFront behavior.
- URL path.
- S3 object key.
- Application routing.
- Host header behavior.
- Query strings.
- Cached error responses.
- Wrong origin association.

A common diagnostic mistake is checking only whether the object exists in S3 or the application.

The more important question is:

> Is CloudFront requesting the same resource from the same origin that you tested directly?

---

## Troubleshooting `400 Bad Request`

A `400` can originate from:

- CloudFront.
- WAF.
- ALB.
- Nginx.
- Django/FastAPI.
- Application validation.

Check:

- Request syntax.
- Headers.
- URL encoding.
- Query strings.
- HTTP method.
- Request body.
- Host header.
- Maximum request constraints.
- Application validation.

For APIs, reproduce the request with a controlled HTTP client rather than relying only on browser behavior.

```bash
curl -i \
  -X GET \
  'https://api.example.com/v1/users?page=1'
```

---

## Troubleshooting `405 Method Not Allowed`

### Question

GET works through CloudFront but POST returns `405`. What do you inspect?

### Answer

Check the allowed HTTP methods configured for the relevant CloudFront behavior.

Then verify the entire path:

```text
Client
  │
  ▼
CloudFront behavior
  │
  ▼
Allowed method?
  │
  ▼
Origin
  │
  ▼
Application routing
```

The application itself may also return `405`, so identify which layer generated the response.

---

## Troubleshooting CloudFront `5xx` Errors

`5xx` errors require determining whether the failure is:

- CloudFront-side.
- Origin connectivity.
- Origin infrastructure.
- Application.
- Dependency-related.

A useful correlation model is:

```text
CloudFront 5xx ↑
       │
       ├── Origin request volume ↑
       │
       ├── Origin latency ↑
       │
       ├── ALB 5xx ↑
       │
       ├── Application exceptions ↑
       │
       └── Database/Redis failures ↑
```

If several downstream signals move at the same time, the origin path becomes a strong candidate.

---

## Troubleshooting `502 Bad Gateway`

### Question

CloudFront returns `502`. What do you investigate?

### Answer

A `502` can indicate that CloudFront could not obtain a valid response from the origin.

Investigate:

- Origin availability.
- TLS configuration between CloudFront and origin.
- Origin protocol policy.
- Certificate validity.
- Origin hostname.
- DNS resolution.
- Application response.
- ALB/Nginx behavior.
- Origin timeout or connection failures.

For an ALB-backed application:

```text
CloudFront
    │
    ▼
ALB
    │
    ▼
Target group
    │
    ▼
Application
```

Check each layer rather than assuming the ALB is the problem.

---

## Troubleshooting `503 Service Unavailable`

A `503` commonly indicates an overloaded or unavailable backend, although the exact source must be established.

Check:

- Origin health.
- ALB target health.
- Application capacity.
- Kubernetes pod availability.
- Auto Scaling behavior.
- Connection pools.
- Database availability.
- Redis availability.
- Deployment state.

For Kubernetes:

```text
CloudFront
    │
    ▼
Load Balancer
    │
    ▼
Ingress
    │
    ▼
Service
    │
    ▼
Pods
```

A healthy CloudFront distribution does not imply healthy Kubernetes workloads.

---

## Troubleshooting `504 Gateway Timeout`

### Question

CloudFront returns `504 Gateway Timeout`. What is your approach?

### Answer

Start by determining where time is being consumed.

```text
CloudFront
    │
    ▼
Origin connection
    │
    ▼
ALB / Nginx
    │
    ▼
Django / FastAPI
    │
    ├── Redis
    ├── PostgreSQL
    └── External APIs
```

Investigate:

- Origin response latency.
- Application execution time.
- Database query latency.
- External API latency.
- Connection pool exhaustion.
- Worker saturation.
- Nginx/ALB timeouts.
- CloudFront origin timeout configuration.

Do not simply increase timeouts.

A timeout increase can hide an overloaded backend and increase resource consumption.

---

## Troubleshooting High Latency

### Question

CloudFront requests are slow. How do you determine whether CloudFront or the origin is responsible?

### Answer

Separate the request path into measurable segments.

```text
Viewer → CloudFront → Origin → Application → Dependencies
```

Compare:

| Signal | Interpretation |
|---|---|
| Edge latency high, origin stable | Investigate edge/network/client path |
| Cache hits fast, misses slow | Investigate origin |
| Origin latency high | Investigate backend |
| Database latency high | Investigate PostgreSQL |
| Redis latency high | Investigate Redis |
| Only one region affected | Investigate geographic/network scope |
| All regions affected | Investigate global configuration/origin |

The goal is to identify where latency is introduced rather than treating total request latency as one metric.

---

## Troubleshooting Low Cache Hit Ratio

### Question

CloudFront cache hit ratio drops from 95% to 40%. What do you check?

### Answer

Investigate changes to the cache key and cacheability.

Check:

- Query strings.
- Cookies.
- Headers.
- Cache policy.
- TTL.
- Origin response headers.
- New endpoints.
- Invalidation activity.
- URL changes.
- Deployment changes.

A useful model is:

```text
More cache-key variation
        ↓
More cache objects
        ↓
Fewer cache hits
        ↓
More origin requests
        ↓
Higher origin load
```

---

## Troubleshooting Cache-Key Fragmentation

### Question

Why would adding a cookie to the cache key cause a sudden performance regression?

### Answer

Because requests that previously shared a cache entry may now generate independent cache entries.

For example:

```text
/product/123 + cookie=A
/product/123 + cookie=B
/product/123 + cookie=C
```

can create multiple cache variants.

If the cookie does not change the representation, it should generally not be part of the cache key.

---

## Troubleshooting Incorrect Cached Content

### Question

Users receive the wrong content from CloudFront. What is the most important thing to investigate?

### Answer

Investigate whether the cache key contains every request attribute that changes the response.

Suppose:

```text
Header: X-Language
```

changes the response:

```text
X-Language: en → English content
X-Language: fr → French content
```

If CloudFront does not distinguish these requests correctly, one representation may be served to another request.

The general rule is:

> Every request attribute that changes the representation must be reflected appropriately in the caching design.

---

## Troubleshooting Stale Content

### Question

The origin has new content, but CloudFront still serves the old version.

### Answer

Check:

- Object TTL.
- `Cache-Control`.
- `Expires`.
- Cache policy.
- Whether the request is a cache hit.
- Whether invalidation occurred.
- Whether the URL itself changed.

For static assets, prefer content hashing:

```text
app.abc123.js
app.def456.js
```

rather than repeatedly invalidating:

```text
app.js
```

---

## Troubleshooting Cached Errors

### Question

The origin is fixed, but CloudFront continues returning `404` or `5xx`.

### Answer

The error response may itself be cached.

Investigate:

- Error caching settings.
- Error response TTL.
- Cache status.
- Invalidation.
- Whether the origin is actually healthy now.

The important distinction is:

```text
Origin recovered
        ≠
Existing cached error immediately disappeared
```

---

## Troubleshooting API Responses Cached Accidentally

### Question

A Django endpoint returns user-specific information, but CloudFront is caching it. What should you do?

### Answer

Treat this as a potential security incident.

Immediate actions should include:

1. Stop inappropriate shared caching.
2. Determine whether sensitive responses were exposed.
3. Invalidate affected objects where necessary.
4. Inspect logs to determine exposure.
5. Review cache policies.
6. Review application cache headers.
7. Correct the endpoint's caching design.
8. Add safeguards to prevent recurrence.

Authentication does not automatically make a response safe to share through a CDN cache.

---

## Troubleshooting Signed URL `403`

### Question

A signed URL is valid according to your application, but CloudFront returns `403`.

### Answer

Check:

- Expiration.
- Resource path.
- Signature.
- Key configuration.
- Trusted key group/public key configuration.
- Policy conditions.
- Distribution configuration.
- URL modification by clients or intermediaries.
- System clock differences where relevant.

A common mistake is verifying only that the backend generated a signature and not verifying that the exact requested resource matches the signed resource.

---

## Troubleshooting Signed Cookie Failures

Check:

- Cookie names.
- Cookie values.
- Expiration.
- Policy.
- Resource restrictions.
- Trusted key configuration.
- Domain/path behavior.
- Client cookie handling.

For multiple private resources:

```text
Authentication
      │
      ▼
Signed cookie
      │
      ▼
CloudFront
      │
      ├── /video/1.mp4
      ├── /video/2.mp4
      └── /video/3.mp4
```

---

## Troubleshooting S3 Origin `403`

### Question

CloudFront returns `403` for an S3-backed object.

### Answer

Check:

- S3 bucket policy.
- Origin Access Control.
- Object ownership.
- Object existence.
- CloudFront origin configuration.
- Bucket region.
- Distribution behavior.
- Requested object path.

Do not solve an origin-access problem by making the entire bucket public unless that is an explicitly justified architecture.

A safer production pattern is:

```text
Internet
   │
   ▼
CloudFront
   │
   ▼
Controlled S3 access
   │
   ▼
Private bucket
```

---

## Troubleshooting Multiple Origins

### Question

Some API requests are unexpectedly reaching the S3 origin.

### Answer

Check CloudFront behavior matching.

For example:

```text
/api/*    → ALB
/static/* → S3
/*        → S3
```

A request to `/api/users` should match `/api/*`.

Verify:

- Path patterns.
- Behavior ordering.
- Origin association.
- Default behavior.
- Recent configuration changes.

---

## Troubleshooting Origin Path Problems

### Question

CloudFront requests the wrong S3 key even though the URL looks correct.

### Answer

Inspect the configured origin path.

For example:

```text
CloudFront URL:
https://cdn.example.com/images/logo.png

Origin:
S3 bucket

Origin path:
/production
```

The resulting object lookup may effectively target:

```text
/production/images/logo.png
```

If the actual object is elsewhere, CloudFront may return `404`.

Always compare the external URL with the effective origin path.

---

## Troubleshooting CORS Through CloudFront

### Question

CORS works against the origin but fails through CloudFront.

### Answer

Inspect:

- `Origin` header.
- `OPTIONS` requests.
- Allowed methods.
- Allowed headers.
- `Access-Control-Allow-Origin`.
- Response headers policy.
- Cache behavior.
- Origin request policy.

A common issue is caching a response whose CORS representation varies by origin without designing the cache behavior accordingly.

---

## Troubleshooting OPTIONS Requests

### Question

POST requests fail in browsers but work through `curl`. What should you investigate?

### Answer

The browser may issue an `OPTIONS` preflight request before the actual POST.

Check:

```text
Browser
  │
  ▼
OPTIONS
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

Verify:

- `OPTIONS` is allowed.
- Required headers are forwarded.
- CORS response headers are returned.
- WAF is not blocking the request.
- The response is appropriate for the browser's origin.

---

## Troubleshooting WAF Blocks

### Question

CloudFront returns `403` after a WAF rule was deployed.

### Answer

Correlate:

```text
WAF rule deployment
       +
403 increase
       +
Blocked request count
```

Inspect:

- Rule ID.
- Rule priority.
- Managed rule groups.
- Match conditions.
- Affected paths.
- Geographic scope.
- False positives.

Prefer the narrowest correction that restores legitimate traffic without removing necessary protection.

---

## Troubleshooting Bot Traffic

### Question

Origin traffic increases because automated clients repeatedly request an uncached endpoint.

### Answer

Investigate:

- Request rate.
- Client patterns.
- Geographic distribution.
- WAF signals.
- User-agent patterns where useful.
- Cacheability.
- Authentication.
- Application rate limiting.

A layered approach may be:

```text
CloudFront
    │
    ▼
WAF
    │
    ▼
Application rate limiting
    │
    ▼
Origin
```

CloudFront caching can reduce load only when the responses are safely cacheable.

---

## Troubleshooting Direct Origin Access

### Question

Users can access the ALB directly even though CloudFront is intended to be the public entry point.

### Answer

This creates an origin-bypass path.

The direct origin may bypass:

- CloudFront caching.
- WAF attached to CloudFront.
- Viewer restrictions.
- Edge-level controls.
- Centralized traffic management.

Investigate origin security groups, load balancer exposure, network architecture, and the mechanism used to restrict origin access.

---

## Troubleshooting DNS

### Question

The CloudFront distribution is healthy, but users cannot reach the application.

### Answer

Check DNS independently.

Verify:

```text
Domain
  │
  ▼
Authoritative DNS
  │
  ▼
CloudFront distribution
```

Check:

- DNS record.
- Record type.
- Alias configuration.
- TTL.
- Authoritative nameservers.
- DNS propagation.
- Alternate domain configuration.

Do not use CloudFront metrics as proof that DNS is functioning correctly.

---

## Troubleshooting TLS and Certificate Errors

### Question

Users receive certificate errors after configuring a CloudFront custom domain.

### Answer

Check:

- ACM certificate.
- Certificate domain names.
- Certificate status.
- CloudFront association.
- Alternate domain name.
- DNS record.
- TLS configuration.

The public hostname must match the certificate presented to viewers.

---

## Troubleshooting HTTP to HTTPS Redirects

### Question

Users are redirected unexpectedly or receive HTTP responses when HTTPS is required.

### Answer

Inspect:

- Viewer protocol policy.
- Redirect configuration.
- Application redirects.
- Nginx behavior.
- Forwarded protocol headers.

A common architecture is:

```text
HTTP
 │
 ▼
CloudFront
 │
 ▼
HTTPS redirect
 │
 ▼
HTTPS
```

If multiple layers perform redirects, you can accidentally create redirect loops.

---

## Troubleshooting Redirect Loops

### Question

CloudFront and Django are producing an HTTPS redirect loop.

### Answer

This often happens when the application does not correctly understand the original viewer protocol.

For example:

```text
Browser
  │ HTTPS
  ▼
CloudFront
  │
  ▼
Origin
  │
  └── Application believes request is HTTP
             │
             ▼
        Redirect to HTTPS
             │
             ▼
        CloudFront
             │
             ▼
           Origin
```

Inspect forwarded protocol information and application proxy configuration.

For Django, ensure the application's HTTPS/proxy configuration matches the actual deployment topology.

---

## Troubleshooting Host Header Problems

### Question

Django generates URLs using the internal ALB hostname.

### Answer

Investigate:

- Host header forwarding.
- Origin request policy.
- Nginx proxy configuration.
- Django host configuration.
- URL-generation logic.
- Forwarded headers.

The application should distinguish between the public viewer-facing hostname and internal origin addressing where necessary.

---

## Troubleshooting Cache Policy Changes

### Question

Performance regressed immediately after a cache policy change.

### Answer

Compare:

```text
Before policy
      vs.
After policy
```

Look for changes to:

- TTL.
- Query strings.
- Cookies.
- Headers.
- Cacheability.
- Compression behavior.
- Error caching.

The most useful evidence is usually the change history plus cache-hit and origin-request metrics.

---

## Troubleshooting Origin Request Policy

### Question

The origin says a required header is missing, but the client definitely sent it.

### Answer

The header may not be forwarded by the CloudFront origin request configuration.

Trace:

```text
Client
  │
  ├── Required header
  ▼
CloudFront
  │
  ├── Forwarded?
  ▼
Origin
```

Verify whether the relevant header is:

- Part of the cache key.
- Forwarded to the origin.
- Removed or transformed.
- Required only for origin processing.

A header does not automatically need to be part of the cache key merely because it must reach the origin.

---

## Troubleshooting Query String Behavior

### Question

The origin receives different query parameters than the client sent.

### Answer

Inspect the CloudFront cache and origin request configuration.

Determine:

- Which query strings participate in the cache key.
- Which query strings are forwarded to the origin.
- Whether irrelevant tracking parameters are being forwarded.
- Whether required parameters are omitted.

This distinction matters:

```text
Cache key behavior
        ≠
Origin forwarding behavior
```

A parameter can be forwarded without necessarily being a cache-key dimension, provided doing so is correct for the response semantics.

---

## Troubleshooting Cookies

### Question

Your application requires a cookie, but the origin does not receive it.

### Answer

Check the origin request policy and cookie forwarding configuration.

If the cookie changes the response, also determine whether it needs to participate in the cache key.

Avoid blindly forwarding every cookie because this can:

- Increase request size.
- Reduce cache efficiency.
- Increase origin complexity.
- Create unnecessary cache variants.

---

## Troubleshooting Large Request Bodies

### Question

A large POST request fails through CloudFront but works directly against the origin.

### Answer

Investigate request-size and request-processing constraints across the entire path.

Check:

- CloudFront behavior.
- HTTP method.
- CloudFront request limits.
- WAF constraints.
- ALB limits.
- Nginx configuration.
- Application server limits.
- Django upload settings.

Do not assume that because the origin accepts the request directly, every intermediary will accept it.

---

## Troubleshooting File Downloads

### Question

Large files download correctly from S3 but fail through CloudFront.

### Answer

Investigate:

- Object existence.
- Cache behavior.
- Origin permissions.
- Range-request behavior.
- Content headers.
- Origin timeout.
- Object size.
- Client/network behavior.

Test with a direct HTTP client:

```bash
curl -I 'https://cdn.example.com/files/archive.zip'
```

Then compare the response headers and status with the origin response.

---

## Troubleshooting Compression

### Question

CloudFront is serving large text responses and bandwidth usage is unexpectedly high.

### Answer

Investigate:

- Compression support.
- Response `Content-Encoding`.
- Cache behavior.
- Origin response headers.
- Content type.
- Object size.

Compression is most useful for compressible content such as:

- HTML.
- CSS.
- JavaScript.
- JSON.
- XML.

It generally provides little benefit for already-compressed formats such as many JPEG, PNG, ZIP, and video formats.

---

## Troubleshooting Origin Saturation

### Question

CloudFront traffic is stable, but the origin CPU and database load suddenly increase.

### Answer

Check whether the CloudFront cache hit ratio has degraded.

```text
CloudFront traffic stable
        │
        ▼
Cache hit ratio ↓
        │
        ▼
Origin requests ↑
        │
        ▼
CPU/database load ↑
```

Also investigate application deployments that may have changed:

- Cache headers.
- URL generation.
- API behavior.
- Query parameters.
- Response size.
- Endpoint routing.

---

## Troubleshooting Redis and CloudFront Together

### Question

CloudFront cache misses increase and Redis latency also increases. What do you investigate?

### Answer

Determine whether increased origin traffic is cascading into application-level caching.

```text
CloudFront cache miss ↑
        │
        ▼
Django/FastAPI requests ↑
        │
        ▼
Redis operations ↑
        │
        ▼
Redis saturation
        │
        ▼
Application latency ↑
```

Do not treat Redis saturation as an isolated event if it correlates with a CloudFront configuration change.

---

## Troubleshooting PostgreSQL Saturation

### Question

PostgreSQL connections are exhausted after a CloudFront deployment.

### Answer

Investigate whether CloudFront is sending more requests to the origin than expected.

Check:

- Cache-hit ratio.
- Origin request volume.
- Application request rate.
- Queries per request.
- Connection pool size.
- Database connection count.
- Recent application changes.

The correct fix may be restoring cache efficiency rather than increasing PostgreSQL connection limits.

---

## Troubleshooting Kubernetes Origin Failures

### Question

CloudFront returns intermittent `503` responses and the application runs on Kubernetes.

### Answer

Trace:

```text
CloudFront
    │
    ▼
Load Balancer
    │
    ▼
Ingress
    │
    ▼
Service
    │
    ▼
Pods
```

Inspect:

- Pod readiness.
- Pod restarts.
- Service endpoints.
- Ingress logs.
- Load balancer target health.
- CPU/memory pressure.
- Horizontal Pod Autoscaler behavior.
- Deployment rollout state.

Intermittent failures often indicate partial capacity loss rather than a complete outage.

---

## Troubleshooting Nginx Origin

### Question

CloudFront returns `502`, and Nginx is the origin-facing proxy.

### Answer

Inspect:

- Nginx error logs.
- Upstream connectivity.
- Upstream timeout.
- Upstream connection limits.
- Worker capacity.
- Header configuration.
- Request buffering.
- Application server health.

A useful path is:

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

Determine the first layer that reports failure.

---

## Troubleshooting Application-Level `500`

### Question

CloudFront returns `500`. Django logs show exceptions. What should you do?

### Answer

The CloudFront layer may simply be exposing an application-origin failure.

Investigate:

- Application exception.
- Deployment.
- Database state.
- Redis.
- External APIs.
- Environment variables.
- Feature flags.
- Recent migrations.

Do not keep changing CloudFront settings when the origin clearly produces the failure.

---

## Troubleshooting Recent Deployments

### Question

A CloudFront problem started immediately after a deployment. How much weight should you give that correlation?

### Answer

A strong temporal correlation is valuable evidence, but it is not proof.

Compare:

```text
Deployment time
      │
      ├── CloudFront configuration
      ├── Application release
      ├── WAF changes
      ├── DNS changes
      └── Infrastructure changes
```

Then identify which measurable behavior changed immediately afterward.

---

## Troubleshooting Configuration Drift

### Question

The CloudFront console differs from your infrastructure-as-code repository. Why is this dangerous?

### Answer

The production state is no longer reproducible.

Potential consequences include:

- Unexpected future deployments.
- Difficult rollback.
- Hidden security changes.
- Configuration loss.
- Environment inconsistency.

Treat the infrastructure repository as the controlled source of truth and investigate why manual changes occurred.

---

## Troubleshooting After a Configuration Rollback

### Question

You rolled back CloudFront configuration, but the problem persists.

### Answer

Possible explanations include:

- Cached responses.
- Configuration propagation delay.
- More than one configuration change.
- Origin-side changes.
- DNS caching.
- WAF configuration.
- Application deployment.
- Client-side caching.

Verify each layer independently rather than assuming rollback immediately restores every stateful component.

---

## Troubleshooting Geographic Problems

### Question

Only users in one country experience CloudFront failures.

### Answer

Investigate:

- Geographic restrictions.
- WAF geographic rules.
- IP reputation.
- Regional networking.
- Origin behavior.
- DNS resolution.
- Specific edge locations.
- ISP-level behavior.

Compare working and failing requests while controlling for:

```text
URL
HTTP method
headers
cookies
client network
geographic location
```

---

## Troubleshooting One Endpoint Only

### Question

Only `/api/search` is slow, while every other API endpoint is healthy.

### Answer

Do not treat this as a general CloudFront outage.

Investigate the endpoint-specific behavior:

- Matching CloudFront behavior.
- Cache policy.
- Query-string variation.
- Origin request volume.
- Application processing.
- Database query performance.
- External search services.
- Response size.

For search APIs, high query-string cardinality can naturally produce poor cache reuse.

---

## Troubleshooting One User Only

### Question

Only one user reports stale or incorrect content.

### Answer

Investigate request-specific dimensions:

- Cookies.
- Authorization.
- Cache key.
- Browser cache.
- Request headers.
- Geographic edge.
- User-specific URL parameters.

This is often a cache-key or client-state problem rather than a global CloudFront problem.

---

## Troubleshooting Intermittent Errors

### Question

One out of every 100 requests fails.

### Answer

Intermittent failures require correlation rather than a single reproduction.

Investigate:

- Origin instance health.
- Load balancer target distribution.
- Kubernetes pods.
- Connection pools.
- WAF behavior.
- Edge behavior.
- Regional scope.
- Request characteristics.

For example:

```text
99% success
1% failure
      │
      ▼
Does failure correlate with:
      ├── Specific origin instance?
      ├── Specific region?
      ├── Specific endpoint?
      ├── Specific request type?
      └── Specific deployment version?
```

Partial failures are often caused by partial infrastructure health.

---

## Troubleshooting Cache Invalidation

### Question

You invalidated `/app.js`, but users still see the old application.

### Answer

Check:

- Whether the correct path was invalidated.
- Whether other dependent assets remain cached.
- Browser cache.
- Service workers.
- HTML documents referencing old assets.
- Multiple asset paths.
- Whether the deployment actually uploaded the new object.

Invalidating one object does not invalidate every object that may reference it.

---

## Troubleshooting Service Worker Caching

### Question

CloudFront has been invalidated, but users still receive old frontend code.

### Answer

CloudFront may not be the only cache.

The request path can include:

```text
Browser
   │
   ▼
Service Worker
   │
   ▼
CloudFront
   │
   ▼
Origin
```

Inspect browser caching and service-worker behavior before concluding that CloudFront invalidation failed.

---

## Troubleshooting Monitoring Gaps

### Question

You know users are experiencing failures, but CloudFront metrics look normal. What is missing?

### Answer

Infrastructure metrics are not enough.

Combine:

```text
CloudFront metrics
+
WAF metrics
+
ALB metrics
+
Application metrics
+
Database metrics
+
Business metrics
```

For APIs, useful application metrics include:

- Request rate.
- P50/P95/P99 latency.
- Error rate.
- Endpoint-level latency.
- Dependency latency.
- Queue depth.
- Database query latency.

---

## Troubleshooting Without Logs

### Question

You have no CloudFront logs available. How do you investigate?

### Answer

Use the strongest remaining signals:

- CloudFront metrics.
- WAF metrics.
- ALB logs.
- Application logs.
- Database metrics.
- Deployment history.
- CloudTrail configuration history.
- Reproduction requests.

Then enable appropriate logging as a corrective action.

Logs should not be enabled indiscriminately without considering storage, retention, privacy, and cost.

---

## Troubleshooting With Logs

### Question

What information do you want from CloudFront logs during an incident?

### Answer

Useful fields depend on the logging mechanism, but the goal is to establish:

- Request path.
- Method.
- Status.
- Timestamp.
- Edge/location information where available.
- Cache behavior.
- Request characteristics.
- Origin response characteristics.
- Viewer information where appropriate.

Use logs for detailed investigation and metrics for rapid detection and trend analysis.

---

## Troubleshooting Cost Spikes

### Question

CloudFront costs suddenly increase. Is high traffic the only explanation?

### Answer

No.

Investigate:

- Request volume.
- Bytes transferred.
- Geographic distribution.
- Large objects.
- Cache efficiency.
- Bot traffic.
- New endpoints.
- Logging.
- Edge compute usage.
- Configuration changes.

A cost spike may result from a workload change, an inefficient cache design, or unexpected traffic.

---

## Troubleshooting Unexpected Origin Traffic

### Question

CloudFront request volume is stable but origin request volume doubles.

### Answer

This is a strong indication that cache efficiency has degraded.

Investigate:

```text
CloudFront requests
       │
       ▼
Cache hit ratio
       │
       ▼
Origin requests
```

Then compare:

- Cache policy.
- Cache key.
- TTL.
- Query strings.
- Cookies.
- Headers.
- Invalidation events.
- Deployment changes.

---

## Troubleshooting a Cache Miss Storm

### Question

A popular object suddenly experiences a huge number of origin requests. What could cause this?

### Answer

Possible causes include:

- Object expiration.
- Invalidation.
- Cache eviction.
- Configuration changes.
- Cache-key variation.
- New URL variants.
- Deployment changes.

The resulting pattern can be:

```text
Popular object expires
        │
        ▼
Many edge requests miss
        │
        ▼
Origin receives burst
        │
        ▼
Origin load increases
```

For highly popular content, origin capacity and caching strategy should be designed with this behavior in mind.

---

## Troubleshooting Deployment-Induced Cache Misses

### Question

Every deployment causes origin traffic to spike. Why?

### Answer

Possible reasons include:

- Global invalidations.
- Changed asset URLs.
- Short TTLs.
- Changed cache policies.
- Application responses becoming uncacheable.

Content-hashed assets can reduce unnecessary invalidation of static resources.

---

## Troubleshooting CloudFront During an Incident

### Question

What should you avoid doing during a production CloudFront incident?

### Answer

Avoid:

- Making multiple unrelated changes simultaneously.
- Disabling security controls globally without evidence.
- Making the origin public as a quick fix.
- Increasing every timeout blindly.
- Purging the entire cache without understanding impact.
- Changing cache keys without understanding response semantics.
- Scaling the database before identifying the traffic cause.
- Making manual console changes without recording them.
- Declaring recovery before verifying externally.

Incident changes should be minimal, reversible, and evidence-driven.

---

## Production Troubleshooting Checklist

Use this checklist during a CloudFront incident:

### Request

- [ ] Exact URL identified.
- [ ] HTTP method identified.
- [ ] Status code identified.
- [ ] Timestamp recorded.
- [ ] Reproduction established.
- [ ] Affected geography identified.

### CloudFront

- [ ] Distribution identified.
- [ ] Matching behavior identified.
- [ ] Cache status investigated.
- [ ] Cache policy reviewed.
- [ ] Origin request policy reviewed.
- [ ] Response headers policy reviewed.
- [ ] HTTP methods verified.
- [ ] Recent configuration changes checked.

### Security

- [ ] WAF metrics checked.
- [ ] WAF rule matches checked.
- [ ] Signed URL/cookie configuration checked.
- [ ] Geographic restrictions checked.
- [ ] Origin access controls checked.

### Origin

- [ ] Origin health checked.
- [ ] ALB/load balancer checked.
- [ ] Nginx/Ingress checked.
- [ ] Application instances/pods checked.
- [ ] Origin latency checked.
- [ ] Origin error rate checked.

### Dependencies

- [ ] Redis checked.
- [ ] PostgreSQL checked.
- [ ] External APIs checked.
- [ ] Kafka/Celery dependencies checked where applicable.

### Operations

- [ ] Recent deployments checked.
- [ ] Infrastructure changes checked.
- [ ] DNS changes checked.
- [ ] Rollback option identified.
- [ ] Recovery verified.
- [ ] Root cause documented.
- [ ] Preventive action identified.

---

## Common Troubleshooting Mistakes

| Mistake | Why it is dangerous | Better approach |
|---|---|---|
| Blaming CloudFront immediately | The origin may be failing | Trace the full request path |
| Changing many settings at once | Root cause becomes harder to identify | Make controlled changes |
| Purging the entire cache | Can create unnecessary origin load | Invalidate narrowly |
| Making S3 public | Bypasses intended access control | Fix origin access configuration |
| Disabling WAF globally | Removes security protection | Correct the specific false positive |
| Increasing timeouts blindly | Masks backend saturation | Find the slow dependency |
| Ignoring cache keys | Can cause incorrect content | Validate representation dimensions |
| Ignoring origin metrics | CDN symptoms can hide backend causes | Correlate edge and origin metrics |
| Assuming `200` means success | Business failures can return `200` | Monitor application/business metrics |
| Ignoring browser/service-worker caches | CloudFront may not be responsible | Inspect every caching layer |

---

## Senior-Level Troubleshooting Framework

For senior backend interviews, structure your answer around five questions:

### Where does the request fail?

```text
DNS
→ TLS
→ CloudFront
→ WAF
→ Origin
→ Application
→ Dependencies
```

### Is the failure deterministic?

Determine whether:

- Every request fails.
- Some requests fail.
- Only one endpoint fails.
- Only one region fails.
- Only one user fails.

### What changed?

Look for:

- Application deployment.
- CloudFront configuration.
- WAF changes.
- DNS changes.
- Infrastructure changes.
- Dependency failures.

### What evidence supports the hypothesis?

Use:

- Metrics.
- Logs.
- Traces.
- Configuration diffs.
- Deployment history.
- Reproduction tests.

### What is the safest remediation?

Prefer:

```text
Minimal
+
Reversible
+
Evidence-driven
+
Low-blast-radius
```

---

## Useful Diagnostic Commands

### Test HTTP Response

```bash
curl -I 'https://cdn.example.com/static/app.js'
```

### Follow Redirects

```bash
curl -IL 'https://cdn.example.com/api/health'
```

### Inspect Full Response

```bash
curl -v 'https://cdn.example.com/api/health'
```

### Test a Specific Method

```bash
curl -i \
  -X OPTIONS \
  -H 'Origin: https://app.example.com' \
  -H 'Access-Control-Request-Method: POST' \
  'https://api.example.com/v1/orders'
```

### Inspect DNS

```bash
dig api.example.com
```

### Inspect TLS

```bash
openssl s_client \
  -connect api.example.com:443 \
  -servername api.example.com
```

These commands help establish observable behavior from outside the system. They should be combined with AWS metrics and application logs rather than used as the sole diagnostic mechanism.

---

## Interview Scenario: Complete CloudFront Incident

### Question

Your production API uses:

```text
Client
  ↓
CloudFront
  ↓
WAF
  ↓
ALB
  ↓
Django
  ↓
Redis
  ↓
PostgreSQL
```

After a CloudFront configuration deployment:

- `5xx` increases.
- Cache hit ratio falls from 92% to 35%.
- Origin requests triple.
- PostgreSQL connections reach their limit.
- Some users receive `504`.

How do you troubleshoot it?

### Strong Answer

The metrics strongly suggest a causal chain:

```text
CloudFront configuration change
            │
            ▼
Cache efficiency degraded
            │
            ▼
Origin requests increased
            │
            ▼
Django traffic increased
            │
            ▼
Redis/PostgreSQL load increased
            │
            ▼
PostgreSQL connections exhausted
            │
            ▼
Application latency increased
            │
            ▼
CloudFront 504 increased
```

I would:

1. Stop additional deployments.
2. Confirm the timing correlation.
3. Compare the current CloudFront configuration with the previous version.
4. Identify changes to cache policy, cache key, TTL, cookies, headers, or query strings.
5. Confirm origin traffic increased because of cache misses.
6. Roll back the CloudFront change if evidence supports it.
7. Monitor cache-hit ratio and origin request volume.
8. Verify PostgreSQL connection pressure falls.
9. Confirm `504` rates return to baseline.
10. Verify application behavior externally.
11. Preserve the configuration diff and metrics.
12. Perform root-cause analysis.
13. Add configuration validation or monitoring to detect similar regressions.

The important interview insight is that the `504` is likely the **final symptom in a cascading failure**, not necessarily the original problem.

---

## Key Takeaways

- **Troubleshoot CloudFront layer by layer: DNS, TLS, CloudFront behavior, cache, WAF, origin, application, and dependencies.**
- **Correlate cache-hit ratio, origin request volume, latency, and error metrics to distinguish CDN problems from origin saturation.**
- **Treat cached content, cache keys, headers, cookies, query strings, and TTLs as first-class troubleshooting concerns because they directly affect correctness and origin load.**
- **Production incident changes should be minimal, reversible, and evidence-driven; avoid broad cache purges, security disablement, and blind timeout or capacity increases.**
- **A senior troubleshooting answer identifies the causal chain, validates it with measurable evidence, restores service safely, and includes a preventive action rather than stopping at the immediate symptom.**