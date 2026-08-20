# 15- Real-World Troubleshooting Scenarios

## Overview

CloudFront incidents are rarely isolated CloudFront problems. In production, CloudFront sits between clients and backend infrastructure, so a visible edge error can originate from cache configuration, AWS WAF, TLS, an origin load balancer, Nginx, Django, FastAPI, Kubernetes, databases, or external dependencies.

The most effective troubleshooting approach is to reconstruct the request path and identify the first layer where observed behavior diverges from expected behavior.

```mermaid
flowchart LR
    C[Client] --> CF[CloudFront]
    CF --> WAF[AWS WAF]
    WAF --> Cache{Cache Decision}
    Cache -->|Hit| R[Cached Response]
    Cache -->|Miss| O[Origin]
    O --> LB[ALB / Load Balancer]
    LB --> NG[Nginx / Ingress]
    NG --> APP[Django / FastAPI]
    APP --> DB[(PostgreSQL)]
    APP --> REDIS[(Redis)]
    APP --> EXT[External APIs]
```

A useful incident model is:

```text
Client symptom
      ↓
HTTP status / latency
      ↓
CloudFront behavior
      ↓
WAF decision
      ↓
Cache hit or miss
      ↓
Origin request
      ↓
Load balancer / Nginx
      ↓
Application
      ↓
Dependencies
      ↓
Root cause
```

The objective is not to prove that CloudFront is involved. It is to determine **where the failure actually occurs**.

## Troubleshooting Principles

### Start With an Exact Request

Avoid investigating vague reports such as:

```text
"The website is slow."
"The API is returning errors."
"CloudFront is broken."
```

Capture a representative request:

```text
Timestamp: 2026-08-20T14:32:15Z
Method: GET
Host: cdn.example.com
Path: /api/orders
Query: page=2
Status: 504
Client: 203.0.113.10
```

Then reproduce it independently:

```bash
curl -v \
  --connect-timeout 10 \
  --max-time 30 \
  "https://cdn.example.com/api/orders?page=2"
```

### Separate Edge Failures From Origin Failures

The first major distinction is:

```text
Did CloudFront fail before contacting the origin?

OR

Did the origin fail after CloudFront forwarded the request?
```

This distinction prevents large amounts of wasted investigation.

### Correlate Time

Every investigation should establish a narrow incident window.

For example:

```text
14:00 - normal
14:03 - deployment
14:05 - cache hit ratio drops
14:07 - origin CPU increases
14:09 - 5xx increases
14:12 - rollback
14:15 - recovery
```

Temporal correlation is not proof of causation, but it is valuable evidence.

## Scenario: CloudFront Returns 404 for an Existing API Endpoint

### Symptoms

A backend endpoint works directly:

```bash
curl -i https://api-origin.example.com/api/orders
```

but fails through CloudFront:

```bash
curl -i https://api.example.com/api/orders
```

The CloudFront response is:

```text
HTTP/2 404
```

### Expected Architecture

```text
Client
  │
  ▼
CloudFront
  │
  ├── /static/* → S3
  │
  └── /api/* → ALB → Django
```

### Investigation

First inspect the distribution configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.DefaultCacheBehavior,
    .DistributionConfig.CacheBehaviors'
```

Check whether:

```text
/api/orders
```

actually matches the intended `/api/*` behavior.

A common failure is that the API request falls through to the default behavior and reaches an origin that does not contain the requested resource.

### Root Cause

For example:

```text
/api/* → ALB
default → S3
```

but the `/api/*` behavior was removed or incorrectly configured.

CloudFront therefore sends:

```text
/api/orders
    ↓
S3 origin
    ↓
404
```

### Corrective Action

Restore the intended path behavior and verify that:

- The path pattern is correct.
- The API origin is correct.
- The behavior is deployed.
- Allowed methods are correct.
- Cache policy is appropriate for the API.

### Production Lesson

A successful origin request does not prove that CloudFront is routing the request to that origin.

Always verify the **cache behavior that actually matches the request**.

## Scenario: CloudFront Returns 403 but the Origin Works

### Symptoms

The origin works:

```bash
curl -i https://origin.example.com/private/report.pdf
```

but CloudFront returns:

```text
HTTP/2 403
```

### Investigation

Check whether AWS WAF is associated with the distribution:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.WebACLId'
```

If a Web ACL is attached, inspect WAF logs.

Look for:

- `BLOCK`
- `terminatingRuleId`
- Client IP
- URI
- Rule group
- Managed rule matches

### Likely Root Causes

| Cause | Diagnostic signal |
|---|---|
| Managed WAF rule | Specific managed rule matched |
| IP restriction | Client IP appears in block rule |
| Rate-based rule | Requests spike from client/IP |
| Geo restriction | Request originates from restricted location |
| Signed access failure | Authorization mechanism rejects request |
| Origin-generated 403 | WAF allows request and origin returns 403 |

### Root Cause

Suppose WAF logs show:

```text
action=BLOCK
terminatingRuleId=AWSManagedRulesCommonRuleSet
uri=/private/report.pdf
```

The request never reached the origin.

### Corrective Action

Do not immediately disable the entire WAF.

Instead:

1. Identify the exact rule.
2. Determine why the request matched.
3. Validate whether the request is legitimate.
4. Add a narrowly scoped exception if required.
5. Test the exception.
6. Monitor for unintended bypasses.

### Production Lesson

A `403` does not automatically mean the application rejected the request.

The request may have been stopped at the edge.

## Scenario: CloudFront Returns 502 After an Origin Deployment

### Symptoms

A deployment completes successfully, but CloudFront starts returning:

```text
HTTP/2 502
```

The origin is an ALB pointing to a containerized FastAPI service.

### Request Path

```text
CloudFront
    ↓
ALB
    ↓
Kubernetes Service
    ↓
Pod
    ↓
FastAPI
```

### Investigation

Check CloudFront origin configuration:

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.Origins.Items'
```

Then check ALB target health:

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN"
```

For Kubernetes:

```bash
kubectl get pods -n production
kubectl get endpoints -n production
```

Inspect application logs:

```bash
kubectl logs \
  deployment/orders-api \
  -n production \
  --tail=200
```

### Potential Causes

- Application is listening on the wrong port.
- Container port changed.
- Health check path changed.
- Security group changed.
- Origin protocol is incorrect.
- Nginx or ingress configuration changed.
- TLS configuration is invalid.
- Application crashes immediately after startup.

### Example Failure

The application now listens on:

```text
8000
```

but the ALB target configuration expects:

```text
8080
```

The deployment itself is successful, but traffic cannot reach the application correctly.

### Production Lesson

Deployment success means the deployment system completed its operation. It does **not** prove that the application is reachable through the complete production request path.

## Scenario: CloudFront Returns 503 During a Traffic Spike

### Symptoms

Traffic increases significantly:

```text
Requests: 20k/min → 80k/min
```

CloudFront starts returning:

```text
HTTP/2 503
```

### Investigation

Compare:

```text
CloudFront requests
Origin requests
Cache hit ratio
ALB request count
Target health
Application CPU
Application memory
Database connections
```

A useful pattern might be:

```text
CloudFront requests       ↑
Cache hit ratio           ↓
Origin requests           ↑↑
Application CPU           ↑↑
Database connections      ↑
5xx                       ↑
```

### Likely Cause

A cache policy change caused previously cacheable responses to become dynamic.

Instead of:

```text
80,000 requests
↓
72,000 cache hits
↓
8,000 origin requests
```

the system now produces:

```text
80,000 requests
↓
60,000 origin requests
```

The backend becomes overloaded.

### Corrective Actions

Depending on the workload:

- Restore appropriate cache behavior.
- Remove irrelevant cache-key dimensions.
- Scale the application.
- Increase database capacity only if the database is actually the bottleneck.
- Protect the origin with rate limiting.
- Review origin request policy.
- Roll back the problematic configuration.

### Production Lesson

CloudFront can reduce origin load dramatically, but a poorly designed cache policy can remove that protection.

Caching is an **origin-capacity control mechanism**, not merely a latency optimization.

## Scenario: High Latency Appears After a Cache Policy Change

### Symptoms

Before the change:

```text
p95 latency: 180 ms
cache hit ratio: 94%
```

After the change:

```text
p95 latency: 1.4 s
cache hit ratio: 58%
```

### Investigation

Compare cache behavior before and after the deployment.

Check:

- Cache policy
- Query-string configuration
- Header forwarding
- Cookie behavior
- Origin request policy

### Example

The application receives:

```text
GET /products/123?utm_source=google
GET /products/123?utm_source=email
GET /products/123?utm_source=campaign
```

If every irrelevant query parameter participates in the cache key, CloudFront may create multiple cache entries for the same logical resource.

### Better Design

If tracking parameters do not change the response:

```text
utm_source
utm_medium
utm_campaign
```

should generally not cause separate cached objects.

The exact implementation depends on the selected CloudFront cache policy and application semantics.

### Production Lesson

A cache-key design should represent **content identity**, not every piece of request metadata.

## Scenario: CloudFront Returns 504 for a Slow API

### Symptoms

The endpoint works directly but CloudFront returns:

```text
HTTP/2 504
```

The application occasionally takes several seconds to respond.

### Investigation

Measure the endpoint directly:

```bash
curl -sS -o /dev/null \
  -w 'status=%{http_code} total=%{time_total}s\n' \
  "https://origin.example.com/api/report"
```

Then compare with CloudFront:

```bash
curl -sS -o /dev/null \
  -w 'status=%{http_code} total=%{time_total}s\n' \
  "https://api.example.com/api/report"
```

Inspect:

- CloudFront latency
- ALB latency
- Application latency
- Database latency
- External API latency

### Example

```text
CloudFront
  ↓
ALB
  ↓
FastAPI
  ↓
PostgreSQL
  ↓
Large unindexed query
```

PostgreSQL takes several seconds to complete.

### Root Cause

The problem is not necessarily that CloudFront has an incorrect timeout.

The actual issue may be an inefficient database operation.

### Corrective Actions

Investigate:

- Query plans
- Missing indexes
- N+1 queries
- Connection pool exhaustion
- External API calls
- Application-level serialization
- Excessive response payloads

### Production Lesson

Increasing a timeout can hide a performance problem while increasing resource consumption and user-visible latency.

Fix the slow dependency first.

## Scenario: Signed URLs Work Directly but Return 403 Through CloudFront

### Symptoms

A signed URL is generated by the backend:

```text
https://cdn.example.com/video.mp4?...signature...
```

but CloudFront returns:

```text
403 Forbidden
```

### Investigation

Validate:

- Key pair configuration
- Public key
- Signature
- Expiration
- Resource path
- Policy
- Distribution association
- System clock
- URL encoding

A useful first test is to generate a fresh URL with a short expiration and test immediately.

### Common Failure

The backend signs:

```text
https://cdn.example.com/video.mp4
```

but the client requests:

```text
https://cdn.example.com/video.mp4?download=true
```

Depending on the policy and signing mechanism, the request may no longer match the expected resource or policy.

### Another Failure

The backend server clock is incorrect.

The generated expiration time may already be outside the expected validity window.

### Production Lesson

Signed URL troubleshooting is fundamentally a **cryptographic validation and request-policy matching problem**.

Do not debug it by repeatedly changing cache settings.

## Scenario: Signed Cookies Work for One File but Not Another

### Symptoms

A user receives signed cookies and can access:

```text
/video/course-1/intro.mp4
```

but receives `403` for:

```text
/video/course-2/lesson-1.mp4
```

### Investigation

Check the signed-cookie policy's resource scope.

For a custom policy, verify that the resource pattern covers the intended objects.

Conceptually:

```text
Allowed:
https://cdn.example.com/video/course-1/*

Requested:
https://cdn.example.com/video/course-2/*
```

If the policy only covers course 1, CloudFront correctly rejects course 2.

### Production Lesson

Authentication and authorization scope must be explicit.

A successful signed-cookie request proves only that **that particular resource matched the policy**.

## Scenario: TLS Error After Certificate Rotation

### Symptoms

Users report:

```text
SSL certificate problem
ERR_CERTIFICATE
TLS handshake failure
```

### Investigation

Check the distribution certificate configuration:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.DistributionConfig.ViewerCertificate'
```

Verify:

- Certificate ARN
- Certificate status
- Domain names
- Distribution aliases
- Certificate region requirements
- Deployment status

For CloudFront viewer certificates, the ACM certificate must satisfy CloudFront's regional requirements.

### External Validation

Use OpenSSL to inspect the presented certificate:

```bash
openssl s_client \
  -connect cdn.example.com:443 \
  -servername cdn.example.com \
  </dev/null
```

Inspect:

```text
subject
issuer
expiration
SAN
certificate chain
```

### Production Lesson

Certificate deployment is a distributed configuration change. A certificate existing in ACM does not necessarily mean CloudFront is actively serving it.

## Scenario: CloudFront Suddenly Serves Old Application Content

### Symptoms

A deployment succeeds:

```text
Version: v2
```

but users still receive:

```text
Version: v1
```

### Investigation

Check whether the object is cached.

```bash
curl -sSI \
  "https://cdn.example.com/assets/app.js"
```

Inspect headers such as:

```text
Age
X-Cache
```

### Root Cause

The object remains valid in CloudFront cache according to its cache-control policy.

### Corrective Strategies

For versioned static assets, prefer immutable filenames:

```text
app.8f31c2.js
```

instead of:

```text
app.js
```

A new deployment produces:

```text
app.9a12ef.js
```

This avoids relying on frequent invalidations.

### Production Lesson

Content versioning is usually a better long-term cache-invalidation strategy than repeatedly purging the same static object.

## Scenario: CloudFront Is Sending Unexpected Traffic to the Origin

### Symptoms

Origin request volume suddenly increases:

```text
Origin traffic: 5k/min → 40k/min
```

but total client traffic remains roughly unchanged.

### Investigation

Compare:

```text
Requests
CacheHitRate
BytesDownloaded
OriginLatency
```

Then inspect cache behavior.

Potential causes:

- Cache policy changed.
- TTL reduced.
- Cache key became too granular.
- Query strings started varying the cache key.
- Cookies entered the cache key.
- Authorization behavior changed.
- Objects became uncacheable.

### Example

Before:

```text
Cache key:
path
```

After:

```text
Cache key:
path + query string + cookie + header
```

The number of unique cache keys can increase dramatically.

### Production Lesson

Cache efficiency is a systems property.

A small cache-policy change can produce a large increase in:

- Origin CPU
- Database load
- Network traffic
- Application cost
- Latency
- Error rate

## Scenario: WAF Blocks Legitimate API Clients

### Symptoms

A mobile client starts receiving:

```text
403
```

The same endpoint works from a browser.

### Investigation

Compare the requests:

```text
Browser
  → User-Agent A
  → headers A
  → request accepted

Mobile
  → User-Agent B
  → headers B
  → request blocked
```

Inspect WAF logs for the mobile request.

Look for:

- Managed rule matches
- Request labels
- IP reputation rules
- Bot-control behavior
- Rate-based rules

### Corrective Action

Do not disable the managed rule globally.

Instead:

1. Identify the exact match.
2. Confirm the request is legitimate.
3. Determine whether the rule is producing a false positive.
4. Add the narrowest practical exception.
5. Test the exception against malicious patterns.
6. Monitor the rule after deployment.

### Production Lesson

Security exceptions should be narrowly scoped.

A global WAF bypass can turn a troubleshooting fix into a security incident.

## Scenario: CloudFront Works, but Only Some Regions Fail

### Symptoms

Users in one geographic region receive:

```text
403
```

or:

```text
5xx
```

while users elsewhere work normally.

### Investigation

Compare:

- CloudFront edge location
- WAF behavior
- Origin health
- DNS
- Geo restrictions
- Network path
- ISP-specific behavior

Check whether geographic restrictions are configured.

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.Restrictions'
```

### Possible Causes

- CloudFront geographic restriction
- WAF geographic rule
- Origin firewall policy
- Regional DNS issue
- Network connectivity issue
- ISP-specific path issue
- Regional dependency failure

### Production Lesson

A globally distributed edge network can hide regionalized failures.

Always compare working and failing locations rather than analyzing only one request.

## Scenario: Only POST Requests Fail

### Symptoms

```text
GET /api/orders       → 200
POST /api/orders      → 403
```

### Investigation

Inspect allowed methods for the cache behavior.

```bash
aws cloudfront get-distribution-config \
  --id "$DISTRIBUTION_ID" |
jq '.DistributionConfig.DefaultCacheBehavior.AllowedMethods'
```

If the behavior only permits:

```text
GET
HEAD
```

CloudFront will not handle POST as expected.

### Additional Checks

For API behaviors, verify:

- Allowed methods
- Cache policy
- Origin request policy
- Authorization headers
- CORS
- WAF rules
- CSRF behavior if applicable
- Origin routing

### Production Lesson

Static-content behaviors and API behaviors should usually have different CloudFront configurations.

Do not apply one generic cache behavior to unrelated workloads.

## Scenario: Authorization Header Reaches the Origin Incorrectly

### Symptoms

Authenticated requests work inconsistently.

Anonymous requests are cached correctly, but authenticated requests receive unexpected responses.

### Investigation

Check whether authorization information participates in the cache behavior and whether it is forwarded to the origin as required.

The critical distinction is:

```text
Cache key
```

versus:

```text
Origin request
```

A value may need to reach the origin without necessarily being appropriate as a cache-key dimension.

### Risk

If personalized content is cached without correct cache-key isolation, one user's response can potentially be served to another user.

### Production Lesson

For authenticated APIs, cache configuration must be designed together with the application's authorization model.

Never assume that forwarding an authentication header automatically makes caching safe.

## Scenario: CloudFront and Nginx Show Different Status Codes

### Symptoms

CloudFront reports:

```text
502
```

but Nginx access logs show:

```text
200
```

### Investigation

Determine whether the Nginx log entry corresponds to the same request.

Compare:

- Timestamp
- URI
- Method
- Client/request ID
- Origin connection
- Response headers

Possible explanations include:

- The requests are not the same.
- CloudFront generated the error before the origin response was received.
- A connection failed after the origin produced a response.
- Nginx returned a response that CloudFront could not process as expected.
- Another upstream component generated the final error.

### Production Lesson

Never correlate logs based solely on approximate timestamps when request identifiers or more precise request attributes are available.

## Scenario: Kubernetes Pods Are Healthy but CloudFront Returns 503

### Symptoms

Kubernetes reports:

```bash
kubectl get pods -n production
```

and all pods are:

```text
Running
```

Yet CloudFront returns:

```text
503
```

### Investigation

`Running` does not mean `Ready`.

Check:

```bash
kubectl get pods -n production
kubectl get endpoints -n production
kubectl describe deployment orders-api -n production
```

Then inspect:

```bash
kubectl get svc -n production
```

and the load balancer target health.

### Possible Failure

Pods may be running but failing readiness probes.

Therefore:

```text
Pods Running
        ↓
Pods Not Ready
        ↓
No usable endpoints
        ↓
Load balancer failure
        ↓
CloudFront 503
```

### Production Lesson

For Kubernetes-backed origins, inspect the entire readiness chain:

```text
Pod
→ Readiness
→ Endpoint
→ Service
→ Ingress / ALB
→ CloudFront
```

## Scenario: Redis Failure Causes CloudFront 5xx

### Symptoms

CloudFront starts returning `5xx` shortly after Redis becomes unavailable.

### Request Path

```text
CloudFront
  ↓
FastAPI
  ↓
Redis
  ↓
Failure
```

### Investigation

Check application logs and Redis metrics.

For Redis connectivity:

```bash
redis-cli -h "$REDIS_HOST" ping
```

Expected:

```text
PONG
```

Inspect application behavior when Redis is unavailable.

### Architectural Question

Determine whether Redis is:

- A mandatory dependency
- A cache that can be bypassed
- A session store
- A rate limiter
- A distributed lock
- A critical state store

If Redis is only a cache, the application may be able to fall back to PostgreSQL.

If Redis stores session state, failure may have a much larger impact.

### Production Lesson

CloudFront cannot compensate for an origin architecture that turns a non-critical dependency into a mandatory single point of failure.

## Scenario: PostgreSQL Saturation Appears as a CloudFront Problem

### Symptoms

CloudFront returns:

```text
504
```

Application CPU is moderate, but PostgreSQL connections are exhausted.

### Investigation

Inspect:

- Database connections
- Query latency
- Lock contention
- Connection pool utilization
- Slow queries
- CPU
- I/O

The request path may be:

```text
CloudFront
  ↓
ALB
  ↓
Django
  ↓
PostgreSQL
  ↓
Connection pool exhausted
  ↓
Request timeout
  ↓
CloudFront 504
```

### Corrective Action

Investigate the database bottleneck.

Potential fixes include:

- Query optimization
- Indexing
- Connection-pool tuning
- Read replicas
- Caching
- Request-level batching
- Removing unnecessary database calls

Do not blindly increase CloudFront timeout values.

### Production Lesson

Edge-layer symptoms frequently expose deeper backend capacity problems.

## Scenario: CloudFront Cache Hit Ratio Collapses After a Deployment

### Symptoms

Before deployment:

```text
Cache hit ratio: 95%
```

After deployment:

```text
Cache hit ratio: 45%
```

### Investigation

Compare:

- Cache policy
- Response `Cache-Control`
- Query strings
- Cookies
- Headers
- Response status
- Object TTL
- Content types

### Application-Level Cause

The application may have changed:

```http
Cache-Control: public, max-age=3600
```

to:

```http
Cache-Control: private, no-cache
```

CloudFront can therefore behave very differently even though the distribution configuration did not change.

### Production Lesson

Caching is an end-to-end behavior.

CloudFront configuration and origin response headers must be considered together.

## Scenario: Error Appears Only After Invalidation

### Symptoms

Before invalidation:

```text
200
```

After invalidation:

```text
500
```

### Investigation

This can indicate that the cached response had been masking an origin problem.

Before invalidation:

```text
Client
  ↓
CloudFront
  ↓
Cached 200
```

After invalidation:

```text
Client
  ↓
CloudFront
  ↓
Origin
  ↓
500
```

### Root Cause

The origin was unhealthy, but clients did not observe it while the cached object remained valid.

### Production Lesson

An invalidation can expose an existing origin failure. It does not necessarily create the failure.

## Scenario: Origin Overload During a Cache Flush

### Symptoms

A large invalidation is issued and origin traffic spikes immediately.

### Request Path

```text
Many cached objects removed
          ↓
Cache misses increase
          ↓
Origin requests increase
          ↓
Application load increases
          ↓
Database load increases
          ↓
Latency / 5xx increase
```

### Mitigation

Before large cache changes:

- Verify origin capacity.
- Check autoscaling configuration.
- Consider deployment strategy.
- Monitor origin latency.
- Monitor database capacity.
- Avoid unnecessary invalidations.
- Prefer versioned assets where possible.

### Production Lesson

Cache invalidation is an operational event that can create a cache-miss storm.

## Scenario: CloudFront Configuration Change Is Not Visible Immediately

### Symptoms

A configuration change was submitted, but some users still see old behavior.

### Investigation

Check distribution status:

```bash
aws cloudfront get-distribution \
  --id "$DISTRIBUTION_ID" \
  --query 'Distribution.Status'
```

A distribution configuration change must finish deployment before the new behavior is consistently available.

### Production Practice

CI/CD should not treat configuration submission as equivalent to completed deployment.

A robust pipeline should:

```text
Apply configuration
      ↓
Wait for deployment
      ↓
Run smoke tests
      ↓
Validate production endpoint
      ↓
Complete release
```

## Scenario: Origin Works Directly but CloudFront Fails TLS Validation

### Symptoms

Direct origin requests succeed, but CloudFront reports an origin communication failure.

### Investigation

Check:

- Origin protocol policy
- Origin hostname
- Origin certificate
- Certificate SAN
- Certificate expiration
- TLS compatibility
- Origin listener

For an HTTPS origin:

```bash
openssl s_client \
  -connect origin.example.com:443 \
  -servername origin.example.com \
  </dev/null
```

The hostname used by CloudFront must be compatible with the certificate presented by the origin.

### Production Lesson

There are two distinct TLS relationships:

```text
Client
  │ TLS
  ▼
CloudFront
  │ TLS
  ▼
HTTPS Origin
```

A valid viewer certificate does not guarantee that CloudFront can establish a valid TLS connection to the origin.

## Scenario: CloudFront Is Healthy but the Application Is Down

### Symptoms

CloudFront itself appears operational, but all requests fail.

### Investigation

Bypass CloudFront where safe and test the origin directly.

```bash
curl -i \
  "https://origin.example.com/health"
```

If the origin is unhealthy:

```text
CloudFront
  ↓
Healthy edge
  ↓
Unhealthy origin
```

CloudFront is functioning correctly but cannot produce a successful application response.

### Production Lesson

"CloudFront is up" and "the application is available" are different health conditions.

## Scenario: Only One Cache Behavior Is Broken

### Symptoms

```text
/static/app.js     → 200
/images/logo.png   → 200
/api/orders        → 502
```

### Investigation

Compare the behaviors individually.

```text
/static/*
    → S3

/images/*
    → S3

/api/*
    → ALB
```

The API behavior may have:

- Wrong origin
- Incorrect origin protocol
- Incorrect allowed methods
- Wrong cache policy
- Incorrect origin request policy
- Missing authorization forwarding

### Production Lesson

CloudFront distributions are often collections of independent request-routing rules.

Troubleshoot the **specific behavior**, not just the distribution globally.

## Scenario: Monitoring Shows a 5xx Spike but Users Report No Impact

### Symptoms

A CloudWatch alarm fires:

```text
CloudFront 5xx ↑
```

but application dashboards appear normal.

### Investigation

Determine:

- Which status codes increased?
- Which paths are affected?
- Which edge locations are affected?
- Are bots generating the traffic?
- Are requests invalid?
- Is the error rate based on a very small request volume?

For example:

```text
Normal traffic: 10 million requests
Affected endpoint: 100 requests
Errors: 80
```

The endpoint has an 80% error rate, but overall user impact may be small.

### Production Lesson

Error percentages must be interpreted together with request volume and business impact.

## Scenario: A Single Client Experiences Repeated 403 Responses

### Symptoms

Most users work normally, but one client receives:

```text
403
```

### Investigation

Compare:

- IP
- User-Agent
- Cookies
- Authorization
- Signed URL
- Request rate
- Geographic location

Potential causes include:

- WAF rate-based rule
- Expired signed URL
- Invalid signed cookie
- Client clock issue
- IP restriction
- Bot-control rule

### Production Lesson

Do not widen access controls globally to fix a client-specific failure.

Determine which request attribute causes the difference.

## Scenario: CloudFront Returns Different Content for Different Users

### Symptoms

User A receives:

```text
Hello, Alice
```

User B receives:

```text
Hello, Alice
```

when User B should receive personalized content.

### Root Cause

A personalized response was cached without sufficient cache-key isolation.

### Dangerous Architecture

```text
GET /profile
        ↓
CloudFront
        ↓
Cache key = /profile
        ↓
Cached response for Alice
        ↓
Returned to Bob
```

### Correct Design

Personalized content generally requires one of:

- No caching
- Appropriate cache-key variation
- Application-side personalization after cached content retrieval
- Separate static and dynamic resources

### Security Impact

This is not merely a caching inefficiency.

It can become a cross-user data exposure vulnerability.

### Production Lesson

Never cache authenticated or personalized content until the cache semantics have been explicitly reviewed.

## Scenario: CloudFront API Requests Are Cached Unexpectedly

### Symptoms

A REST API changes data, but clients continue receiving old responses.

### Investigation

Check:

```http
Cache-Control
ETag
Age
X-Cache
```

Then inspect the API cache behavior.

### Likely Cause

An API endpoint was accidentally configured as cacheable.

### Recommended Architecture

For highly dynamic APIs:

```text
/api/*
    ↓
CloudFront
    ↓
ALB
    ↓
Django / FastAPI
```

with cache behavior designed explicitly for API semantics.

For cacheable GET APIs:

```text
GET /catalog
    ↓
CloudFront cache
    ↓
Origin only on misses
```

but mutation requests should be handled according to the configured allowed methods and application semantics.

### Production Lesson

Do not enable API caching simply because CloudFront makes it easy. Cache only when response consistency and authorization semantics are well understood.

## Scenario: Nginx Reports 499 but CloudFront Reports 5xx

### Symptoms

Origin logs contain client-aborted request indicators such as:

```text
499
```

while CloudFront metrics show elevated errors.

### Investigation

Determine whether:

- The origin is slow.
- The client disconnected.
- CloudFront timed out.
- Nginx timed out upstream.
- The application is overloaded.

Compare:

```text
request_time
upstream_response_time
CloudFront latency
```

### Production Lesson

Different layers can legitimately report different statuses for the same request lifecycle.

Always identify which component generated each status.

## Scenario: Deployment Introduces a Cache Poisoning Risk

### Symptoms

After a deployment, unexpected content appears for requests that should be equivalent.

### Investigation

Check whether the application response depends on headers or cookies that are not represented correctly in the cache configuration.

For example:

```text
Response depends on:
X-Tenant-ID
```

but:

```text
Cache key:
path only
```

Multiple tenants may therefore share the same cached representation.

### Corrective Action

Review:

- Cache key
- Origin request policy
- Response semantics
- Tenant isolation
- Authentication
- Cacheability

### Production Lesson

Multi-tenant systems require explicit cache-isolation design.

Caching a response without including the tenant dimension can become a data-isolation failure.

## Scenario: Diagnostic Data Is Insufficient During an Incident

### Symptoms

The team knows:

```text
CloudFront returned 504
```

but cannot determine:

- Which origin was used
- Whether WAF allowed it
- Whether the request reached Nginx
- How long the application took
- Which database query was slow

### Root Cause

The platform lacks sufficient correlation and observability.

### Remediation

Implement:

```text
CloudFront logs
+
WAF logs
+
ALB metrics
+
Nginx access logs
+
Structured application logs
+
Database metrics
+
Distributed tracing
```

where appropriate.

### Production Lesson

Observability should be designed before the incident.

A troubleshooting workflow that depends on logs nobody enabled during system design is not a reliable production workflow.

## Incident Response Framework

For repeated CloudFront incidents, use a standard framework.

### Detect

Identify:

- Error rate
- Latency
- Traffic anomaly
- Cache anomaly
- WAF anomaly

### Localize

Determine:

```text
Edge
→ WAF
→ Cache
→ Origin
→ Application
→ Dependency
```

### Correlate

Compare:

- Metrics
- Logs
- Traces
- Deployments
- Configuration changes

### Mitigate

Prefer the smallest safe action:

- Roll back configuration
- Restore healthy origin
- Disable problematic rule
- Scale capacity
- Correct routing
- Restore cache policy

### Validate

Repeat the original failing request:

```bash
curl -v \
  "https://cdn.example.com/api/orders"
```

Then validate:

- Status
- Latency
- Headers
- Origin metrics
- Error rate

### Document

Record:

```text
Impact
Timeline
Detection
Root cause
Evidence
Mitigation
Permanent fix
Follow-up actions
```

## Incident Evidence Matrix

A useful incident record can be structured as follows:

| Evidence | Observation | Interpretation |
|---|---|---|
| Client response | `504` | Request exceeded an upstream timeout |
| `X-Cache` | `Error from cloudfront` | CloudFront generated/returned an error response |
| Origin latency | `5.2s` | Origin is significantly slow |
| PostgreSQL latency | `4.8s` | Database likely contributes most latency |
| Deployment | 10 minutes earlier | Possible regression |
| Cache hit ratio | Stable | Cache policy probably not primary cause |

The interpretation should always be treated as a hypothesis until validated.

## Production Troubleshooting Decision Tree

```mermaid
flowchart TD
    A[CloudFront Incident] --> B{HTTP Error?}

    B -->|403| C[Check WAF / Signed Access / Restrictions]
    B -->|404| D[Check Behavior / Origin / Resource]
    B -->|502| E[Check Origin Connectivity / TLS / ALB]
    B -->|503| F[Check Origin Health / Capacity]
    B -->|504| G[Check Origin Latency / Dependencies]
    B -->|200 but Slow| H[Check Cache / Edge / Origin Latency]
    B -->|Unexpected Content| I[Check Cache Key / TTL / Authorization]

    C --> J[Correlate Logs]
    D --> J
    E --> J
    F --> J
    G --> J
    H --> J
    I --> J

    J --> K[Review Recent Changes]
    K --> L[Mitigate]
    L --> M[Validate]
```

## Senior-Level Failure Analysis

A mature investigation distinguishes between:

### Symptom

```text
CloudFront returned 504.
```

### Immediate Cause

```text
Origin did not respond within the expected time.
```

### Contributing Cause

```text
Database query latency increased.
```

### Root Cause

```text
A deployment introduced an inefficient query that caused
database saturation under production traffic.
```

### Corrective Action

```text
Rollback deployment, optimize query, add regression test,
and introduce database latency alerting.
```

This hierarchy prevents superficial incident reports.

## Common Troubleshooting Mistakes

| Mistake | Why it is dangerous | Better approach |
|---|---|---|
| Blame CloudFront immediately | Edge errors can represent origin failures | Trace the complete request path |
| Disable WAF to fix 403 | Creates unnecessary security exposure | Identify the exact rule |
| Increase timeout for every 504 | Masks backend bottlenecks | Diagnose origin latency |
| Invalidate everything | Can create origin overload | Invalidate selectively |
| Disable caching for everything | Increases origin traffic and latency | Design cache behavior intentionally |
| Ignore cache keys | Can cause stale or cross-user content | Review cache semantics |
| Trust pod `Running` status | Pod may not be ready | Check readiness and endpoints |
| Ignore recent deployments | Misses likely regressions | Build a timeline |
| Debug only from one region | Misses regional failures | Compare working/failing regions |
| Log every request field | Can expose sensitive data | Apply structured redaction |

## Interview-Level Questions

### Why can CloudFront return a 504 when the origin is technically healthy?

Because "healthy" is not equivalent to "responding within the required time for this request." An origin can pass health checks while individual requests become slow because of database contention, dependency latency, connection-pool exhaustion, CPU saturation, or expensive application logic.

### Why can an invalidation increase origin load?

Invalidation removes cached objects. Subsequent requests become cache misses and must be fulfilled by the origin, potentially producing a cache-miss storm.

### Why is a CloudFront 403 not necessarily a CloudFront configuration problem?

The response may be generated by AWS WAF, signed URL/cookie validation, geographic restrictions, or the origin itself. The first step is to identify which layer rejected the request.

### Why can a cache-policy change cause a backend outage?

If the change reduces cache effectiveness, more requests reach the origin. That additional traffic can exhaust application, database, or network capacity and produce cascading failures.

### Why can a cached response create a security vulnerability?

If the cache key does not isolate responses that vary by user, tenant, authorization, or another security-sensitive dimension, one requester's response can potentially be served to another requester.

### Why should you not immediately increase CloudFront timeouts during a 504 incident?

Because the timeout may be exposing an underlying origin bottleneck. Increasing it can increase resource occupancy and allow more slow requests to accumulate, making the backend less stable.

## Production Runbook

A concise production runbook should follow this sequence:

1. Capture the exact failing request and timestamp.
2. Reproduce using `curl`.
3. Record status, timing, and response headers.
4. Identify the CloudFront distribution and matching behavior.
5. Determine whether the response was a cache hit or miss.
6. Check AWS WAF when access-control behavior is involved.
7. Verify the configured origin.
8. Determine whether the request reached the origin.
9. Inspect ALB, Nginx, ingress, and application logs.
10. Check PostgreSQL, Redis, external APIs, and other dependencies.
11. Compare CloudFront and origin metrics.
12. Review recent CloudFront, WAF, infrastructure, and application changes.
13. Form a root-cause hypothesis supported by evidence.
14. Apply the smallest safe mitigation.
15. Re-run the original request.
16. Verify that both user-visible behavior and backend metrics have recovered.
17. Record the root cause and permanent corrective actions.

## Key Takeaways

- **Treat CloudFront errors as request-path symptoms:** the actual failure may exist in WAF, cache behavior, origin infrastructure, application code, or backend dependencies.
- **Correlate evidence across layers:** CloudFront headers, WAF logs, ALB metrics, Nginx logs, application telemetry, and database metrics should tell one consistent request story.
- **Cache configuration is an architectural concern:** cache-key, TTL, invalidation, and authorization mistakes can create latency, origin overload, stale content, or security vulnerabilities.
- **Fix root causes rather than masking symptoms:** increasing timeouts, disabling WAF, or bypassing caching can make an incident worse if the underlying bottleneck remains.
- **Production troubleshooting should be repeatable:** use exact requests, narrow time windows, recent-change analysis, evidence-based hypotheses, controlled mitigation, and post-fix validation.